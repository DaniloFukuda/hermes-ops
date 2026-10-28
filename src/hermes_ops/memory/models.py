from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any

from hermes_ops.skills.finding_models import EvidenceRef


class MemorySchemaVersion(int, Enum):
    V1 = 1


class MemoryKind(str, Enum):
    CONFIRMED_FINDING = "CONFIRMED_FINDING"
    PATH_ONLY_OBSERVATION = "PATH_ONLY_OBSERVATION"
    ALIGNED_REVALIDATION = "ALIGNED_REVALIDATION"
    OPERATIONAL_LIMITATION = "OPERATIONAL_LIMITATION"
    HISTORICAL_BENCHMARK = "HISTORICAL_BENCHMARK"


class FreshnessState(str, Enum):
    CURRENTLY_UNVERIFIED = "CURRENTLY_UNVERIFIED"
    SAME_SNAPSHOT_CANDIDATE = "SAME_SNAPSHOT_CANDIDATE"
    STALE_CANDIDATE = "STALE_CANDIDATE"
    REVALIDATED = "REVALIDATED"
    SUPERSEDED = "SUPERSEDED"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    INCOMPATIBLE_SCHEMA = "INCOMPATIBLE_SCHEMA"


class RevisionRelationship(str, Enum):
    SAME_REVISION = "SAME_REVISION"
    SAME_SNAPSHOT = "SAME_SNAPSHOT"
    DIFFERENT_REVISION = "DIFFERENT_REVISION"
    UNKNOWN = "UNKNOWN"


class LineageEventKind(str, Enum):
    OBSERVED = "OBSERVED"
    RECONFIRMED = "RECONFIRMED"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    SUPERSEDED = "SUPERSEDED"
    SCHEMA_MIGRATED = "SCHEMA_MIGRATED"
    PRIVACY_MIGRATED = "PRIVACY_MIGRATED:HERMES-0033-v1"
    QUARANTINED = "QUARANTINED"


class LegacyPrivacyState(str, Enum):
    CURRENT_SAFE = "CURRENT_SAFE"
    LEGACY_SAFE_VERIFIED = "LEGACY_SAFE_VERIFIED"
    LEGACY_UNVERIFIED = "LEGACY_UNVERIFIED"
    LEGACY_UNSAFE = "LEGACY_UNSAFE"
    MIGRATED_SAFE = "MIGRATED_SAFE"
    QUARANTINED = "QUARANTINED"


class DisclosureLevel(str, Enum):
    HEADER = "HEADER"
    STRUCTURED = "STRUCTURED"
    CANONICAL = "CANONICAL"
    REVALIDATION_HINT = "REVALIDATION_HINT"


class MemoryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class RepositoryIdentity:
    repository_id: str
    logical_name: str | None = None
    origin_fingerprint: str | None = None
    metadata_digest: str | None = None

    @classmethod
    def explicit(cls, repository_id: str) -> RepositoryIdentity:
        from .core import validate_repository_id

        validate_repository_id(repository_id)
        return cls(repository_id)

    @classmethod
    def derive(cls, logical_name: str, origin_fingerprint: str) -> RepositoryIdentity:
        from .core import canonical_digest

        if not logical_name.strip() or not origin_fingerprint.strip():
            raise MemoryError("MEMORY_RECORD_UNSAFE", "Repository identity inputs are empty")
        digest = canonical_digest((logical_name, origin_fingerprint))
        return cls(digest, logical_name, origin_fingerprint, digest)


@dataclass(frozen=True, slots=True)
class AuditMemoryObservation:
    memory_schema_version: MemorySchemaVersion
    observation_id: str
    lineage_id: str
    repository_id: str
    source_revision: str | None
    snapshot_digest: str | None
    structural_scope: tuple[str, ...]
    request_digest: str
    canonical_request: Any
    source_auditor: str
    auditor_version: int
    normalizer_version: int | None
    outcome_status: str
    native_classification: str | None
    limitations: tuple[str, ...]
    original_finding_id: str | None
    finding_kind: str | None
    historical_severity: str | None
    historical_reachability: str | None
    evidence_refs: tuple[EvidenceRef, ...]
    native_payload: Any
    payload_digest: str
    memory_kind: MemoryKind
    symbols: tuple[str, ...]
    relative_paths: tuple[str, ...]
    retrieval_terms: tuple[str, ...]

    def canonical_json(self) -> str:
        from .core import canonical_json

        return canonical_json(self)


@dataclass(frozen=True, slots=True)
class MemoryLineageEvent:
    lineage_id: str
    repository_id: str
    observation_id: str
    kind: LineageEventKind


@dataclass(frozen=True, slots=True)
class MemoryCurrentContext:
    repository_id: str
    current_revision: str | None = None
    current_snapshot_digest: str | None = None
    current_structural_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        from .core import validate_optional_provenance, validate_relative_paths, validate_repository_id

        validate_repository_id(self.repository_id)
        validate_optional_provenance(self.current_revision)
        validate_optional_provenance(self.current_snapshot_digest)
        validate_relative_paths(self.current_structural_scope)


@dataclass(frozen=True, slots=True)
class MemoryRetrievalRequest:
    repository_id: str
    observation_id: str | None = None
    lineage_id: str | None = None
    symbols: tuple[str, ...] = ()
    relative_paths: tuple[str, ...] = ()
    auditor_kinds: tuple[str, ...] = ()
    finding_kinds: tuple[str, ...] = ()
    mission_terms: tuple[str, ...] = ()
    max_candidates: int = 20
    freshness_policy: FreshnessState | None = None
    disclosure_level: DisclosureLevel = DisclosureLevel.HEADER
    current_context: MemoryCurrentContext | None = None

    def __post_init__(self) -> None:
        from .core import validate_relative_paths, validate_repository_id, validate_terms

        validate_repository_id(self.repository_id)
        validate_relative_paths(self.relative_paths)
        for values in (self.symbols, self.auditor_kinds, self.finding_kinds):
            validate_terms(values, 64)
        validate_terms(self.mission_terms, 64)
        if type(self.max_candidates) is not int or not 1 <= self.max_candidates <= 100:
            raise MemoryError("MEMORY_RECORD_UNSAFE", "Candidate limit is invalid")
        if self.current_context is not None:
            if type(self.current_context) is not MemoryCurrentContext:
                raise MemoryError("MEMORY_RECORD_UNSAFE", "Current context is invalid")
            if self.current_context.repository_id != self.repository_id:
                raise MemoryError(
                    "MEMORY_REPOSITORY_MISMATCH",
                    "Current context belongs to another repository",
                )


@dataclass(frozen=True, slots=True)
class MemoryCandidate:
    observation_id: str
    lineage_id: str
    repository_id: str
    memory_kind: MemoryKind
    source_auditor: str
    source_revision: str | None
    finding_kind: str | None
    historical_severity: str | None
    symbols: tuple[str, ...]
    paths: tuple[str, ...]
    freshness_state: FreshnessState
    evidence_count: int
    compact_summary: str
    retrieval_score: int
    canonical_available: bool
    canonical_pointer: str
    payload_digest: str
    privacy_state: LegacyPrivacyState = LegacyPrivacyState.CURRENT_SAFE
    requires_fresh_audit: bool = True


@dataclass(frozen=True, slots=True)
class PrivacyMigrationResult:
    source_observation_id: str
    migrated_observation_id: str
    lineage_id: str
    policy_version: str
    created: bool
    diagnostic: str


@dataclass(frozen=True, slots=True)
class StructuredMemoryDisclosure:
    observation_id: str
    canonical_pointer: str
    payload_digest: str
    native_classification: str | None
    limitations: tuple[str, ...]
    request_digest: str
    evidence_refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True)
class MemoryRevalidationHint:
    observation_id: str
    lineage_id: str
    historical_auditor: str
    canonical_request: Any
    suggested_symbols: tuple[str, ...]
    suggested_relative_paths: tuple[str, ...]
    suggested_structural_scope: tuple[str, ...]
    canonical_pointer: str
    payload_digest: str
    requires_fresh_audit: bool = True
