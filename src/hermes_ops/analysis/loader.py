from __future__ import annotations

import json
import os
from pathlib import Path
import stat
from typing import Any

from hermes_ops.core.errors import AnalysisError
from hermes_ops.skills.mission_models import EvidenceFile, EvidenceRegion, EvidenceRelationship, EvidenceSymbol, MissionCompleteness, MissionEvidencePack, RelatedTest, SelectionTerm

MAX_PACK_BYTES = 2 * 1024 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _fail(code: str, message: str) -> None:
    raise AnalysisError(code, message)


def _tuple_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or any(type(item) is not str for item in value): _fail("ANALYSIS_PACK_INVALID", "Expected a string array")
    return tuple(value)


def _exact(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys: _fail("ANALYSIS_PACK_INVALID", "Evidence Pack schema is invalid")
    return value


def parse_evidence_pack(value: Any) -> MissionEvidencePack:
    root=_exact(value,{"schema_version","mission","target","selection_terms","files","regions","symbols","relationships","related_tests","unresolved_questions","completeness","limitations"})
    try:
        terms=tuple(SelectionTerm(x["term"],x["source"],_tuple_strings(x["derived_from"]),x["matched_count"]) for x in root["selection_terms"])
        files=tuple(EvidenceFile(x["path"],_tuple_strings(x["roles"]),x["score"],_tuple_strings(x["reasons"])) for x in root["files"])
        regions=tuple(EvidenceRegion(x["path"],x["start_line"],x["end_line"],x["excerpt"],x["content_kind"],_tuple_strings(x["reasons"])) for x in root["regions"])
        symbols=tuple(EvidenceSymbol(x["name"],x["kind"],x["path"],x["region"],_tuple_strings(x["reasons"])) for x in root["symbols"])
        relationships=tuple(EvidenceRelationship(x["kind"],x["source"],x["target"],x["evidence_region"],x["reason"],x.get("supporting_relationship")) for x in root["relationships"])
        tests=tuple(RelatedTest(x["path"],_tuple_strings(x["related_to"]),_tuple_strings(x["reasons"])) for x in root["related_tests"])
        c=root["completeness"]
        completeness=MissionCompleteness(c["status"],_tuple_strings(c["matched_terms"]),_tuple_strings(c["unmatched_terms"]),c["has_active_implementation"],c["has_traceable_relationship"],c["has_related_test"],tuple((str(k),int(v)) for k,v in c["counts"].items()) if isinstance(c["counts"],dict) else tuple((str(k),int(v)) for k,v in c["counts"]),_tuple_strings(c["incompleteness_codes"]))
        return MissionEvidencePack(root["schema_version"],root["mission"],root["target"],terms,files,regions,symbols,relationships,tests,_tuple_strings(root["unresolved_questions"]),completeness,_tuple_strings(root["limitations"]))
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
