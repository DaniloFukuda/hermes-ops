from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from pathlib import PurePosixPath, PureWindowsPath
import re
from typing import Any

from hermes_ops.skills.controlled_reader import valid_relative_path
from hermes_ops.skills.finding_models import EvidenceRef, RankableFinding

from .models import (
    AuditMemoryObservation,
    FreshnessState,
    LineageEventKind,
    LegacyPrivacyState,
    MemoryCurrentContext,
    MemoryError,
    MemoryKind,
    MemorySchemaVersion,
)


MAX_SYMBOLS = 64
MAX_PATHS = 64
MAX_TERMS = 256
MAX_EVIDENCE_REFS = 256
MAX_REQUEST_BYTES = 64 * 1024
MAX_PAYLOAD_BYTES = 256 * 1024
MAX_PAYLOAD_DEPTH = 6
MAX_PAYLOAD_ITEMS = 256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")
_UNSAFE_KEYS = re.compile(r"(?:raw[_-]?source|secret|token|password|api[_-]?key)", re.I)
_MEMORY_PAYLOAD_FIELDS = frozenset({
    "source_skill", "source_auditor", "finding_id", "finding_kind",
    "severity", "evidence_strength", "production_reachability",
    "outcome_status", "native_classification", "limitations", "symbols",
    "relative_paths", "evidence_refs",
})


def sanitize_memory_payload(value: Any, *, _depth: int = 0) -> Any:
    """Return only the closed structural payload allowed in new Memory writes."""
    if _depth > MAX_PAYLOAD_DEPTH:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload nesting is too deep")
    if type(value) is not dict:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload must be a structural mapping")
    if len(value) > MAX_PAYLOAD_ITEMS:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload has too many fields")
    result: dict[str, Any] = {}
    for key in sorted(value):
        if type(key) is not str or key not in _MEMORY_PAYLOAD_FIELDS or _UNSAFE_KEYS.search(key):
            raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload field is not allowed")
        item = value[key]
        if key == "evidence_refs":
            if type(item) is not tuple or len(item) > MAX_EVIDENCE_REFS:
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory evidence payload is invalid")
            result[key] = [
                {
                    "path": ref.path,
                    "start_line": ref.start_line,
                    "end_line": ref.end_line,
                    "start_column": ref.start_column,
                    "end_column": ref.end_column,
                }
                for ref in item
                if type(ref) is EvidenceRef
            ]
            if len(result[key]) != len(item):
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory evidence payload is invalid")
        elif type(item) is tuple:
            if len(item) > MAX_PAYLOAD_ITEMS or any(type(part) is not str for part in item):
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload sequence is invalid")
            if key == "relative_paths":
                validate_relative_paths(item)
            elif any(_SAFE_ID.fullmatch(part) is None for part in item):
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload sequence is not structural")
            result[key] = list(item)
        elif isinstance(item, Enum):
            result[key] = item.value
        elif item is None or type(item) in {str, int, bool}:
            if type(item) is str and (len(item) > 256 or _absolute(item)):
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload text is unsafe")
            if type(item) is str and _SAFE_ID.fullmatch(item) is None:
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload text is not structural")
            result[key] = item
        else:
            raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload contains a runtime object")
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory payload exceeds its limit")
    return result


def _structural_terms(*values: str | None) -> tuple[str, ...]:
    terms: list[str] = []
    for value in values:
        if not value:
            continue
        terms.extend(part for part in re.split(r"[^A-Za-z0-9_]+", value) if part)
    return tuple(sorted(set(terms)))


_MODERN_CONFIRMED_FIELDS = frozenset({
    "source_skill", "finding_id", "finding_kind", "severity",
    "evidence_strength", "production_reachability", "evidence_refs",
})
_MODERN_OUTCOME_FIELDS = frozenset({
    "source_auditor", "finding_kind", "outcome_status", "native_classification",
    "limitations", "symbols", "relative_paths", "evidence_refs",
})
_SOURCE_LIKE = re.compile(r"(?:\beval\s*\(|\bdef\s+\w+\s*\(|\breturn\s+|[;{}]\s*$)", re.I)


def _prohibited_legacy_value(value: Any, *, key: str = "") -> bool:
    if _UNSAFE_KEYS.search(key):
        return True
    if isinstance(value, dict):
        return any(type(k) is not str or _prohibited_legacy_value(v, key=k) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_prohibited_legacy_value(item, key=key) for item in value)
    if type(value) is str:
        host_path = value.startswith("/") or bool(re.match(r"^[A-Za-z]:[\\/]", value))
        return host_path or bool(_SOURCE_LIKE.search(value))
    return False


def _closed_legacy_payload(value: Any) -> bool:
    if type(value) is not dict or any(
        type(key) is not str or key not in _MEMORY_PAYLOAD_FIELDS
        for key in value
    ):
        return False
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return False
    return len(encoded.encode("utf-8")) <= MAX_PAYLOAD_BYTES


def privacy_safe_canonical_request(value: Any) -> bool:
    try:
        canonical_request_payload(value)
    except (MemoryError, TypeError, ValueError):
        return False
    return not _prohibited_legacy_value(value)


def inspect_observation_privacy(observation: AuditMemoryObservation) -> LegacyPrivacyState:
    """Classify one record without exposing or executing its payload."""
    if type(observation) is not AuditMemoryObservation:
        return LegacyPrivacyState.LEGACY_UNVERIFIED
    try:
        validate_observation_identity(observation)
    except MemoryError:
        return LegacyPrivacyState.LEGACY_UNSAFE
    payload = observation.native_payload
    if _prohibited_legacy_value(payload):
        return LegacyPrivacyState.LEGACY_UNSAFE
    if not _closed_legacy_payload(payload):
        return LegacyPrivacyState.LEGACY_UNVERIFIED
    fields = frozenset(payload)
    expected = (
        _MODERN_CONFIRMED_FIELDS
        if observation.memory_kind is MemoryKind.CONFIRMED_FINDING
        else _MODERN_OUTCOME_FIELDS
    )
    return (
        LegacyPrivacyState.CURRENT_SAFE
        if fields == expected
        else LegacyPrivacyState.LEGACY_SAFE_VERIFIED
    )


def validate_repository_id(value: str) -> None:
    if type(value) is not str or _SAFE_ID.fullmatch(value) is None:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Repository ID is invalid")


def validate_relative_paths(values: tuple[str, ...]) -> None:
    if type(values) is not tuple or len(values) > MAX_PATHS:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory paths are invalid")
    if any(type(item) is not str or not valid_relative_path(item) for item in values):
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory paths must be safely relative")


def validate_terms(values: tuple[str, ...], limit: int = MAX_TERMS) -> None:
    if type(values) is not tuple or len(values) > limit:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory terms exceed their limit")
    if any(type(item) is not str or not item.strip() or len(item) > 256 for item in values):
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory terms are invalid")


def validate_optional_provenance(value: str | None) -> None:
    if value is not None and (
        type(value) is not str or not value.strip() or len(value) > 256 or _absolute(value)
    ):
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory provenance is invalid")


def derive_memory_freshness(
    observation: AuditMemoryObservation,
    current_context: MemoryCurrentContext | None,
    lineage_projection: LineageEventKind | None,
) -> FreshnessState:
    """Derive context metadata without consulting Git, indexes, or ranking."""
    if observation.memory_schema_version is not MemorySchemaVersion.V1:
        return FreshnessState.INCOMPATIBLE_SCHEMA
    lineage_states = {
        LineageEventKind.SUPERSEDED: FreshnessState.SUPERSEDED,
        LineageEventKind.NOT_REPRODUCED: FreshnessState.NOT_REPRODUCED,
        LineageEventKind.RECONFIRMED: FreshnessState.REVALIDATED,
    }
    if lineage_projection in lineage_states:
        return lineage_states[lineage_projection]
    if current_context is None or (
        current_context.current_revision is None
        and current_context.current_snapshot_digest is None
    ):
        return FreshnessState.CURRENTLY_UNVERIFIED
    historical_snapshot = observation.snapshot_digest
    current_snapshot = current_context.current_snapshot_digest
    if historical_snapshot is not None and current_snapshot is not None:
        if historical_snapshot == current_snapshot:
            return FreshnessState.SAME_SNAPSHOT_CANDIDATE
        return FreshnessState.STALE_CANDIDATE
    if (
        observation.source_revision is not None
        and current_context.current_revision is not None
        and observation.source_revision != current_context.current_revision
    ):
        return FreshnessState.STALE_CANDIDATE
    return FreshnessState.CURRENTLY_UNVERIFIED


def _absolute(value: str) -> bool:
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute() or bool(PureWindowsPath(value).drive)


def _plain(value: Any, *, key: str | None = None) -> Any:
    if key is not None and _UNSAFE_KEYS.search(key):
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Unsafe canonical field is prohibited")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, EvidenceRef):
        return {
            "path": value.path,
            "start_line": value.start_line,
            "end_line": value.end_line,
            "start_column": value.start_column,
            "end_column": value.end_column,
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name), key=field.name) for field in fields(value)}
    if isinstance(value, dict):
        result = {}
        for item_key in sorted(value, key=lambda item: str(item)):
            if type(item_key) is not str:
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Canonical keys must be text")
            result[item_key] = _plain(value[item_key], key=item_key)
        return result
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is None or type(value) in {str, int, float, bool}:
        if type(value) is str and _absolute(value):
            raise MemoryError("MEMORY_RECORD_UNSAFE", "Absolute paths are prohibited")
        return value
    raise MemoryError("MEMORY_RECORD_UNSAFE", "Runtime object is not canonicalizable")


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(_plain(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Canonical payload is invalid") from exc


def canonical_digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()}"


def canonical_request_payload(request: Any) -> tuple[Any, str]:
    plain = _plain(request)
    encoded = json.dumps(plain, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_REQUEST_BYTES:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Canonical request exceeds its limit")
    return plain, f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def create_observation(**values: Any) -> AuditMemoryObservation:
    repository_id = values["repository_id"]
    validate_repository_id(repository_id)
    scope = tuple(sorted(set(values.get("structural_scope", ()))))
    paths = tuple(sorted(set(values.get("relative_paths", ()))))
    symbols = tuple(sorted(set(values.get("symbols", ()))))
    terms = tuple(sorted(set(values.get("retrieval_terms", ()))))
    evidence = tuple(sorted(set(values.get("evidence_refs", ())), key=lambda item: (item.path, item.start_line, item.end_line, item.start_column or -1, item.end_column or -1)))
    validate_relative_paths(scope)
    validate_relative_paths(paths)
    validate_terms(symbols, MAX_SYMBOLS)
    validate_terms(terms, MAX_TERMS)
    if len(evidence) > MAX_EVIDENCE_REFS:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Evidence references exceed their limit")
    request, request_digest = canonical_request_payload(values["canonical_request"])
    payload = _plain(values.get("native_payload"))
    payload_json = canonical_json(payload)
    if len(payload_json.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Native payload exceeds its limit")
    payload_digest = canonical_digest(payload)
    memory_kind = values["memory_kind"]
    if type(memory_kind) is not MemoryKind:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Memory kind is invalid")
    lineage_basis = (
        repository_id, values["source_auditor"], request_digest,
        values.get("finding_kind") or memory_kind.value, symbols, paths,
    )
    lineage_id = canonical_digest(lineage_basis)
    observation_basis = (
        MemorySchemaVersion.V1.value, repository_id, values.get("source_revision"),
        values.get("snapshot_digest"), scope, request_digest, values["source_auditor"],
        values["auditor_version"], memory_kind.value, values.get("original_finding_id"),
        payload_digest,
    )
    observation_id = canonical_digest(observation_basis)
    return AuditMemoryObservation(
        MemorySchemaVersion.V1, observation_id, lineage_id, repository_id,
        values.get("source_revision"), values.get("snapshot_digest"), scope,
        request_digest, request, values["source_auditor"], values["auditor_version"],
        values.get("normalizer_version"), values["outcome_status"],
        values.get("native_classification"), tuple(sorted(set(values.get("limitations", ())))),
        values.get("original_finding_id"), values.get("finding_kind"),
        values.get("historical_severity"), values.get("historical_reachability"),
        evidence, payload, payload_digest, memory_kind, symbols, paths, terms,
    )


def is_memory_eligible(
    observation: AuditMemoryObservation,
    *,
    operational_opt_in: bool = False,
    revalidation: bool = False,
) -> bool:
    if observation.outcome_status == "FAILED":
        return False
    if observation.memory_kind in {MemoryKind.CONFIRMED_FINDING, MemoryKind.HISTORICAL_BENCHMARK}:
        return True
    if observation.memory_kind is MemoryKind.PATH_ONLY_OBSERVATION:
        return bool(observation.relative_paths or observation.evidence_refs)
    if observation.memory_kind is MemoryKind.ALIGNED_REVALIDATION:
        return revalidation
    if observation.memory_kind is MemoryKind.OPERATIONAL_LIMITATION:
        return operational_opt_in and bool(observation.limitations)
    return False


def validate_observation_identity(observation: AuditMemoryObservation) -> None:
    if observation.memory_schema_version is not MemorySchemaVersion.V1:
        raise MemoryError("MEMORY_SCHEMA_UNSUPPORTED", "Observation schema is unsupported")
    expected = create_observation(
        repository_id=observation.repository_id,
        source_revision=observation.source_revision,
        snapshot_digest=observation.snapshot_digest,
        structural_scope=observation.structural_scope,
        canonical_request=observation.canonical_request,
        source_auditor=observation.source_auditor,
        auditor_version=observation.auditor_version,
        normalizer_version=observation.normalizer_version,
        outcome_status=observation.outcome_status,
        native_classification=observation.native_classification,
        limitations=observation.limitations,
        original_finding_id=observation.original_finding_id,
        finding_kind=observation.finding_kind,
        historical_severity=observation.historical_severity,
        historical_reachability=observation.historical_reachability,
        evidence_refs=observation.evidence_refs,
        native_payload=observation.native_payload,
        memory_kind=observation.memory_kind,
        symbols=observation.symbols,
        relative_paths=observation.relative_paths,
        retrieval_terms=observation.retrieval_terms,
    )
    if (
        observation.observation_id != expected.observation_id
        or observation.lineage_id != expected.lineage_id
        or observation.request_digest != expected.request_digest
        or observation.payload_digest != expected.payload_digest
    ):
        raise MemoryError(
            "MEMORY_RECORD_INTEGRITY_ERROR",
            "Observation identity does not match its canonical payload",
        )


def observation_from_rankable_finding(
    finding: RankableFinding,
    **values: Any,
) -> AuditMemoryObservation:
    if type(finding) is not RankableFinding:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Adapter requires RankableFinding")
    payload = sanitize_memory_payload({
        "source_skill": finding.source_skill,
        "finding_id": finding.finding_id,
        "finding_kind": values.get("finding_kind"),
        "severity": finding.severity,
        "evidence_strength": finding.evidence_strength,
        "production_reachability": finding.production_reachability,
        "evidence_refs": finding.evidence_refs,
    })
    return create_observation(
        repository_id=values["repository_id"],
        source_revision=values.get("source_revision"),
        snapshot_digest=values.get("snapshot_digest"),
        structural_scope=values.get("structural_scope", ()),
        canonical_request=values["canonical_request"],
        source_auditor=finding.source_skill,
        auditor_version=values["auditor_version"],
        normalizer_version=values.get("normalizer_version"),
        outcome_status="COMPLETED_WITH_FINDINGS",
        native_classification="CONFIRMED_HISTORICAL_FINDING",
        limitations=values.get("limitations", ()),
        original_finding_id=finding.finding_id,
        finding_kind=values.get("finding_kind"),
        historical_severity=finding.severity.value,
        historical_reachability=finding.production_reachability.value,
        evidence_refs=finding.evidence_refs,
        native_payload=payload,
        memory_kind=MemoryKind.CONFIRMED_FINDING,
        symbols=values.get("symbols", ()),
        relative_paths=tuple(item.path for item in finding.evidence_refs),
        retrieval_terms=_structural_terms(
            finding.source_skill, values.get("finding_kind"),
            finding.severity.value, finding.evidence_strength.value,
            finding.production_reachability.value,
        ),
    )


def observation_from_auditor_outcome(
    outcome: Any,
    *,
    memory_kind: MemoryKind,
    repository_id: str,
    canonical_request: Any,
    source_revision: str | None = None,
    snapshot_digest: str | None = None,
    structural_scope: tuple[str, ...] = (),
    finding_kind: str | None = None,
    symbols: tuple[str, ...] = (),
    relative_paths: tuple[str, ...] = (),
    evidence_refs: tuple[EvidenceRef, ...] = (),
    retrieval_terms: tuple[str, ...] = (),
) -> AuditMemoryObservation:
    from hermes_ops.skills.audit_round import AuditorOutcome

    if type(outcome) is not AuditorOutcome or outcome.native_result is None:
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Adapter requires a completed native outcome")
    native = outcome.native_result
    classification = getattr(native, "classification", None)
    classification_value = classification.value if isinstance(classification, Enum) else None
    payload = sanitize_memory_payload({
        "source_auditor": outcome.auditor_id,
        "finding_kind": finding_kind,
        "outcome_status": outcome.status.value,
        "native_classification": classification_value,
        "limitations": outcome.limitations,
        "symbols": symbols,
        "relative_paths": relative_paths,
        "evidence_refs": evidence_refs,
    })
    return create_observation(
        repository_id=repository_id,
        source_revision=source_revision,
        snapshot_digest=snapshot_digest,
        structural_scope=structural_scope,
        canonical_request=canonical_request,
        source_auditor=outcome.auditor_id,
        auditor_version=outcome.auditor_version,
        normalizer_version=outcome.normalizer_version,
        outcome_status=outcome.status.value,
        native_classification=classification_value,
        limitations=outcome.limitations,
        original_finding_id=None,
        finding_kind=finding_kind,
        historical_severity=None,
        historical_reachability=None,
        evidence_refs=evidence_refs,
        native_payload=payload,
        memory_kind=memory_kind,
        symbols=symbols,
        relative_paths=relative_paths,
        retrieval_terms=_structural_terms(
            outcome.auditor_id, finding_kind, classification_value,
            outcome.status.value, *outcome.limitations,
        ),
    )
