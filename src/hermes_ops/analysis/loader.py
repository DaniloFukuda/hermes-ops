from __future__ import annotations

from dataclasses import MISSING, fields
import json
import os
from pathlib import Path
import stat
from typing import Any

from hermes_ops.core.errors import AnalysisError
from hermes_ops.skills.mission_models import EvidenceFile, EvidenceRegion, EvidenceRelationship, EvidenceSymbol, MissionCompleteness, MissionEvidencePack, OmissionRecord, RelatedTest, SelectionTerm

MAX_PACK_BYTES = 2 * 1024 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _fail(code: str, message: str) -> None:
    raise AnalysisError(code, message)


def _tuple_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or any(type(item) is not str for item in value): _fail("ANALYSIS_PACK_INVALID", "Expected a string array")
    return tuple(value)


def _root_contract(value: Any) -> dict[str, Any]:
    model_fields = fields(MissionEvidencePack)
    allowed = {field.name for field in model_fields}
    required = {
        field.name
        for field in model_fields
        if field.default is MISSING and field.default_factory is MISSING
    }
    if (
        not isinstance(value, dict)
        or not required.issubset(value)
        or not set(value).issubset(allowed)
    ):
        _fail("ANALYSIS_PACK_INVALID", "Evidence Pack schema is invalid")
    return value


def _parse_omission_provenance(root: dict[str, Any], schema_version: int,
                               regions: tuple[EvidenceRegion, ...],
                               structural_scope: tuple[str, ...]) -> tuple[OmissionRecord, ...]:
    if schema_version == 1:
        if "omission_provenance" in root:
            _fail("ANALYSIS_PACK_INVALID", "Schema v1 cannot carry omission provenance")
        return ()
    if "omission_provenance" not in root or not isinstance(root["omission_provenance"], (list, tuple)):
        _fail("ANALYSIS_PACK_INVALID", "Schema v2 requires omission provenance")
    if len(root["omission_provenance"]) > 300:
        _fail("ANALYSIS_PACK_TOO_LARGE", "Omission provenance exceeds the bounded record limit")
    selected = {(region.path, region.start_line, region.end_line): region for region in regions}

    def in_scope(path: str) -> bool:
        if not structural_scope:
            return True
        return any(path == scope or path.startswith(scope.rstrip("/") + "/") for scope in structural_scope)

    def ordered_strings(value: Any, label: str) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or any(type(item) is not str for item in value):
            _fail("ANALYSIS_PACK_INVALID", f"Omission provenance {label} are invalid")
        values = tuple(value)
        if values != tuple(sorted(set(values))):
            _fail("ANALYSIS_PACK_INVALID", f"Omission provenance {label} are not canonical")
        return values

    records: list[OmissionRecord] = []
    allowed_classifications = {
        "critical_evidence_omitted", "necessary_evidence_omitted", "redundant_evidence_omitted",
    }
    allowed_kinds = {"active_code", "comment", "docstring"}
    for raw in root["omission_provenance"]:
        if not isinstance(raw, dict):
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance record must be an object")
        required = {
            "omission_id", "omitted_region", "equivalent_region", "content_kind",
            "reasons", "associated_terms", "classification", "cap", "justification",
        }
        if set(raw) != required:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance record fields are invalid")

        def region(value: Any, *, optional: bool = False) -> dict[str, object] | None:
            if value is None and optional:
                return None
            if not isinstance(value, dict) or set(value) != {"path", "start_line", "end_line"}:
                _fail("ANALYSIS_PACK_INVALID", "Omission provenance region is invalid")
            if (type(value["path"]) is not str or not value["path"]
                    or type(value["start_line"]) is not int or type(value["end_line"]) is not int
                    or value["start_line"] < 1 or value["start_line"] > value["end_line"]):
                _fail("ANALYSIS_PACK_INVALID", "Omission provenance region values are invalid")
            return {
                "path": value["path"],
                "start_line": value["start_line"],
                "end_line": value["end_line"],
            }

        omitted = region(raw["omitted_region"])
        equivalent = region(raw["equivalent_region"], optional=True)
        omitted_dict = omitted or {}
        expected_id = f"{omitted_dict['path']}:{omitted_dict['start_line']}:{omitted_dict['end_line']}"
        if type(raw["omission_id"]) is not str or raw["omission_id"] != expected_id:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance identity is invalid")
        if not in_scope(omitted_dict["path"]):
            _fail("ANALYSIS_PACK_INVALID", "Omitted region is outside structural scope")
        if raw["content_kind"] not in allowed_kinds or raw["classification"] not in allowed_classifications:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance classification is invalid")
        reasons = ordered_strings(raw["reasons"], "reasons")
        associated_terms = ordered_strings(raw["associated_terms"], "associated terms")
        if type(raw["cap"]) is not str or not raw["cap"] or type(raw["justification"]) is not str or not raw["justification"]:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance explanation is invalid")
        omitted_key = (omitted_dict["path"], omitted_dict["start_line"], omitted_dict["end_line"])
        if omitted_key in selected:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance region is not omitted")
        equivalent_dict = equivalent
        if raw["classification"] == "redundant_evidence_omitted":
            if equivalent_dict is None:
                _fail("ANALYSIS_PACK_INVALID", "Redundant omission lacks a selected equivalent region")
            equivalent_key = (
                equivalent_dict["path"], equivalent_dict["start_line"], equivalent_dict["end_line"],
            )
            selected_region = selected.get(equivalent_key)
            if (selected_region is None or equivalent_key[:3] == omitted_key
                    or equivalent_dict["path"] != omitted_dict["path"]
                    or not in_scope(equivalent_dict["path"])
                    or selected_region.content_kind != raw["content_kind"]
                    or tuple(sorted(set(selected_region.reasons))) != reasons):
                _fail("ANALYSIS_PACK_INVALID", "Redundant omission lacks a complete selected equivalent")
        records.append(OmissionRecord(
            raw["omission_id"], omitted or {}, equivalent,
            raw["content_kind"], reasons, associated_terms,
            raw["classification"], raw["cap"], raw["justification"],
        ))
    if len({item.omission_id for item in records}) != len(records):
        _fail("ANALYSIS_PACK_INVALID", "Omission provenance contains duplicate identities")
    canonical = sorted(records, key=lambda item: (
        dict(item.omitted_region)["path"], dict(item.omitted_region)["start_line"],
        dict(item.omitted_region)["end_line"], item.classification,
    ))
    return tuple(canonical)


def validate_omission_provenance(
    records: Any,
    selected_regions: Any,
    *,
    completeness_status: str,
    incompleteness_codes: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
    file_paths: dict[str, str] | None = None,
) -> None:
    """Validate v2 omission proof at every consumer boundary."""
    if not isinstance(records, (list, tuple)):
        _fail("ANALYSIS_PACK_INVALID", "Omission provenance must be a sequence")
    file_paths = file_paths or {}

    def values(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, OmissionRecord):
            return {
                "omission_id": value.omission_id,
                "omitted_region": value.omitted_region,
                "equivalent_region": value.equivalent_region,
                "content_kind": value.content_kind,
                "reasons": value.reasons,
                "associated_terms": value.associated_terms,
                "classification": value.classification,
                "cap": value.cap,
                "justification": value.justification,
            }
        if isinstance(value, tuple):
            try:
                return dict(value)
            except (TypeError, ValueError):
                pass
        _fail("ANALYSIS_PACK_INVALID", "Omission provenance record is invalid")

    def region(value: Any, *, optional: bool = False) -> dict[str, Any] | None:
        if value is None and optional:
            return None
        if not isinstance(value, dict) or set(value) != {"path", "start_line", "end_line"}:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance region is invalid")
        if (type(value["path"]) is not str or not value["path"]
                or type(value["start_line"]) is not int or type(value["end_line"]) is not int
                or value["start_line"] < 1 or value["start_line"] > value["end_line"]):
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance region values are invalid")
        return dict(value)

    def strings(value: Any, label: str) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or any(type(item) is not str for item in value):
            _fail("ANALYSIS_PACK_INVALID", f"Omission provenance {label} are invalid")
        result = tuple(value)
        if result != tuple(sorted(set(result))):
            _fail("ANALYSIS_PACK_INVALID", f"Omission provenance {label} are not canonical")
        return result

    selected: dict[tuple[str, int, int], dict[str, Any]] = {}
    for raw_region in selected_regions:
        row = values(raw_region) if not isinstance(raw_region, EvidenceRegion) else {
            "path": raw_region.path,
            "start_line": raw_region.start_line,
            "end_line": raw_region.end_line,
            "content_kind": raw_region.content_kind,
            "reasons": raw_region.reasons,
        }
        if "path" not in row and row.get("file_id") in file_paths:
            row["path"] = file_paths[row["file_id"]]
        if {"path", "start_line", "end_line"}.issubset(row):
            selected[(row["path"], row["start_line"], row["end_line"])] = row

    if "CAP_OMISSION" in set(incompleteness_codes) | set(limitations) and not records:
        _fail("ANALYSIS_PACK_INVALID", "CAP_OMISSION requires complete omission provenance")

    required = {
        "omission_id", "omitted_region", "equivalent_region", "content_kind",
        "reasons", "associated_terms", "classification", "cap", "justification",
    }
    allowed_classifications = {
        "critical_evidence_omitted", "necessary_evidence_omitted", "redundant_evidence_omitted",
    }
    for raw_record in records:
        record = values(raw_record)
        if set(record) != required:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance record fields are invalid")
        omitted = region(record["omitted_region"])
        equivalent = region(record["equivalent_region"], optional=True)
        assert omitted is not None
        expected_id = f"{omitted['path']}:{omitted['start_line']}:{omitted['end_line']}"
        if type(record["omission_id"]) is not str or record["omission_id"] != expected_id:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance identity is invalid")
        if record["content_kind"] not in {"active_code", "comment", "docstring"}:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance content kind is invalid")
        if record["classification"] not in allowed_classifications:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance classification is invalid")
        reasons = strings(record["reasons"], "reasons")
        associated_terms = strings(record["associated_terms"], "associated terms")
        derived_terms = tuple(sorted({
            item.removeprefix("term:") for item in reasons if item.startswith("term:")
        }))
        if associated_terms != derived_terms:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance terms do not match reasons")
        if type(record["cap"]) is not str or not record["cap"] or type(record["justification"]) is not str or not record["justification"]:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance explanation is invalid")
        omitted_key = (omitted["path"], omitted["start_line"], omitted["end_line"])
        if omitted_key in selected:
            _fail("ANALYSIS_PACK_INVALID", "Omission provenance region is not omitted")
        if record["classification"] == "redundant_evidence_omitted":
            if record["content_kind"] not in {"comment", "docstring"} or equivalent is None:
                _fail("ANALYSIS_PACK_INVALID", "Only comment/docstring evidence can be redundant")
            equivalent_key = (equivalent["path"], equivalent["start_line"], equivalent["end_line"])
            selected_region = selected.get(equivalent_key)
            if (selected_region is None or equivalent_key == omitted_key
                    or equivalent["path"] != omitted["path"]
                    or selected_region.get("content_kind") != record["content_kind"]
                    or tuple(sorted(set(selected_region.get("reasons", ())))) != reasons):
                _fail("ANALYSIS_PACK_INVALID", "Redundant omission lacks a complete selected equivalent")
        elif completeness_status == "sufficient":
            _fail("ANALYSIS_PACK_INVALID", "Sufficient pack contains nonredundant omission")

    if completeness_status == "sufficient" and any(
        values(record)["classification"] != "redundant_evidence_omitted" for record in records
    ):
        _fail("ANALYSIS_PACK_INVALID", "Sufficient pack contains unproved omission")


def parse_evidence_pack(value: Any) -> MissionEvidencePack:
    root=_root_contract(value)
    try:
        terms=tuple(SelectionTerm(x["term"],x["source"],_tuple_strings(x["derived_from"]),x["matched_count"]) for x in root["selection_terms"])
        files=tuple(EvidenceFile(x["path"],_tuple_strings(x["roles"]),x["score"],_tuple_strings(x["reasons"])) for x in root["files"])
        regions=tuple(EvidenceRegion(x["path"],x["start_line"],x["end_line"],x["excerpt"],x["content_kind"],_tuple_strings(x["reasons"])) for x in root["regions"])
        symbols=tuple(EvidenceSymbol(x["name"],x["kind"],x["path"],x["region"],_tuple_strings(x["reasons"])) for x in root["symbols"])
        relationships=tuple(EvidenceRelationship(x["kind"],x["source"],x["target"],x["evidence_region"],x["reason"],x.get("supporting_relationship")) for x in root["relationships"])
        tests=tuple(RelatedTest(x["path"],_tuple_strings(x["related_to"]),_tuple_strings(x["reasons"])) for x in root["related_tests"])
        c=root["completeness"]
        completeness=MissionCompleteness(c["status"],_tuple_strings(c["matched_terms"]),_tuple_strings(c["unmatched_terms"]),c["has_active_implementation"],c["has_traceable_relationship"],c["has_related_test"],tuple((str(k),int(v)) for k,v in c["counts"].items()) if isinstance(c["counts"],dict) else tuple((str(k),int(v)) for k,v in c["counts"]),_tuple_strings(c["incompleteness_codes"]))
        structural_scope = (
            _tuple_strings(root["structural_scope"])
            if "structural_scope" in root
            else ()
        )
        omission_provenance = _parse_omission_provenance(
            root, root["schema_version"], regions, structural_scope,
        )
        pack = MissionEvidencePack(root["schema_version"],root["mission"],root["target"],terms,files,regions,symbols,relationships,tests,_tuple_strings(root["unresolved_questions"]),completeness,_tuple_strings(root["limitations"]),structural_scope,omission_provenance)
        validate_omission_provenance(
            omission_provenance,
            regions,
            completeness_status=completeness.status,
            incompleteness_codes=completeness.incompleteness_codes,
            limitations=pack.limitations,
        )
        return pack
    except AnalysisError: raise
    except (KeyError, TypeError, ValueError) as exc: raise AnalysisError("ANALYSIS_PACK_INVALID","Evidence Pack values are invalid") from exc


def load_evidence_pack(path: str | Path) -> MissionEvidencePack:
    try: source=Path(path)
    except (TypeError,ValueError,OSError) as exc: raise AnalysisError("ANALYSIS_PACK_INVALID","Evidence Pack path is invalid") from exc
    try: metadata=os.lstat(source)
    except OSError as exc: raise AnalysisError("ANALYSIS_PACK_INVALID","Evidence Pack cannot be inspected") from exc
    if stat.S_ISLNK(metadata.st_mode) or getattr(metadata,"st_file_attributes",0)&_REPARSE or not stat.S_ISREG(metadata.st_mode): _fail("ANALYSIS_PACK_INVALID","Evidence Pack must be a direct regular file")
    if metadata.st_size>MAX_PACK_BYTES: _fail("ANALYSIS_PACK_TOO_LARGE","Evidence Pack exceeds 2 MiB")
    flags=os.O_RDONLY|getattr(os,"O_BINARY",0)|getattr(os,"O_NOFOLLOW",0); descriptor=None
    try:
        descriptor=os.open(source,flags); data=os.read(descriptor,MAX_PACK_BYTES+1)
    except OSError as exc: raise AnalysisError("ANALYSIS_PACK_INVALID","Evidence Pack could not be read") from exc
    finally:
        if descriptor is not None: os.close(descriptor)
    if len(data)>MAX_PACK_BYTES: _fail("ANALYSIS_PACK_TOO_LARGE","Evidence Pack exceeds 2 MiB")
    try: decoded=json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc: raise AnalysisError("ANALYSIS_PACK_INVALID","Evidence Pack is not valid UTF-8 JSON") from exc
    return parse_evidence_pack(decoded)
