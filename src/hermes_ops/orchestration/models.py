from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from hermes_ops.skills.audit_round import AuditRequest, AuditRoundResult
from hermes_ops.memory.models import (
    DisclosureLevel,
    FreshnessState,
    MemoryCandidate,
    MemoryCurrentContext,
    MemoryRevalidationHint,
    RepositoryIdentity,
)


class MemoryMode(str, Enum):
    DISABLED = "DISABLED"
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"


@dataclass(frozen=True, slots=True)
class MemoryAssistedAuditRequest:
    mission: str
    target: str | Path
    repository_identity: RepositoryIdentity
    current_context: MemoryCurrentContext | None
    authoritative_structural_scope: tuple[str, ...]
    audit_requests: tuple[AuditRequest, ...]
    memory_mode: MemoryMode = MemoryMode.DISABLED
    memory_candidate_limit: int = 20
    memory_disclosure_level: DisclosureLevel = DisclosureLevel.HEADER
    allow_memory_scope_suggestions: bool = False
    allow_post_audit_write: bool = False
    allow_operational_limitation_write: bool = False

    def __post_init__(self) -> None:
        if type(self.mission) is not str or not self.mission.strip():
            raise ValueError("Mission must be a non-empty string")
        if not isinstance(self.target, (str, Path)):
            raise ValueError("Audit target must be a string or Path")
        if type(self.repository_identity) is not RepositoryIdentity:
            raise ValueError("Repository identity is required")
        if self.current_context is not None and type(self.current_context) is not MemoryCurrentContext:
            raise ValueError("Current context must be MemoryCurrentContext or None")
        if self.current_context is not None and self.current_context.repository_id != self.repository_identity.repository_id:
            raise ValueError("Current context repository mismatch")
        if type(self.authoritative_structural_scope) is not tuple or any(type(p) is not str for p in self.authoritative_structural_scope):
            raise ValueError("Authoritative structural scope must be a tuple of strings")
        if type(self.audit_requests) is not tuple or not self.audit_requests:
            raise ValueError("At least one audit request is required")
        if type(self.memory_mode) is not MemoryMode:
            raise ValueError("Invalid memory mode")
        if type(self.memory_candidate_limit) is not int or not 1 <= self.memory_candidate_limit <= 100:
            raise ValueError("Memory candidate limit must be between 1 and 100")
        if type(self.memory_disclosure_level) is not DisclosureLevel:
            raise ValueError("Invalid disclosure level")


@dataclass(frozen=True, slots=True)
class MemoryAssistedAuditPlan:
    mission: str
    repository_identity: RepositoryIdentity
    current_context: MemoryCurrentContext | None
    authoritative_structural_scope: tuple[str, ...]
    historical_candidates: tuple[MemoryCandidate, ...]
    revalidation_hints: tuple[MemoryRevalidationHint, ...]
    suggested_auditors: tuple[str, ...]
    suggested_symbols: tuple[str, ...]
    suggested_paths: tuple[str, ...]
    audit_requests: tuple[AuditRequest, ...]
    requires_fresh_audit: bool = True

    def __post_init__(self) -> None:
        if type(self.mission) is not str or not self.mission.strip():
            raise ValueError("Mission must be a non-empty string")
        if type(self.repository_identity) is not RepositoryIdentity:
            raise ValueError("Repository identity is required")
        if type(self.authoritative_structural_scope) is not tuple:
            raise ValueError("Authoritative structural scope must be a tuple")
        if type(self.historical_candidates) is not tuple:
            raise ValueError("Historical candidates must be a tuple")
        if type(self.revalidation_hints) is not tuple:
            raise ValueError("Revalidation hints must be a tuple")
        if type(self.suggested_auditors) is not tuple:
            raise ValueError("Suggested auditors must be a tuple")
        if type(self.suggested_symbols) is not tuple:
            raise ValueError("Suggested symbols must be a tuple")
        if type(self.suggested_paths) is not tuple:
            raise ValueError("Suggested paths must be a tuple")
        if type(self.audit_requests) is not tuple:
            raise ValueError("Audit requests must be a tuple")


@dataclass(frozen=True, slots=True)
class MemoryWritebackResult:
    attempted: bool
    written_observations: tuple[str, ...]
    skipped_observations: tuple[tuple[str, str], ...]
    write_diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MemoryOperationalMetrics:
    retrieval_requested: bool
    candidates_returned: int
    hints_returned: int
    disclosure_level: DisclosureLevel
    writeback_attempted: bool
    observations_written: int
    memory_diagnostics_count: int
    retrieval_duration_ms: float
    disclosure_duration_ms: float
    writeback_duration_ms: float


@dataclass(frozen=True, slots=True)
class MemoryAssistedAuditResult:
    historical_context: "HistoricalContext"
    audit_plan: MemoryAssistedAuditPlan
    fresh_audit: AuditRoundResult
    memory_writeback: MemoryWritebackResult

    def __post_init__(self) -> None:
        if type(self.historical_context) is not HistoricalContext:
            raise ValueError("Historical context is required")
        if type(self.audit_plan) is not MemoryAssistedAuditPlan:
            raise ValueError("Audit plan is required")
        if type(self.fresh_audit) is not AuditRoundResult:
            raise ValueError("Fresh audit result is required")
        if type(self.memory_writeback) is not MemoryWritebackResult:
            raise ValueError("Memory writeback result is required")


@dataclass(frozen=True, slots=True)
class HistoricalContext:
    memory_diagnostics: tuple[str, ...]
    candidates: tuple[MemoryCandidate, ...]
    selected_candidates: tuple[MemoryCandidate, ...]
    revalidation_hints: tuple[MemoryRevalidationHint, ...]
    freshness_summary: dict[FreshnessState, int]
    suggested_symbols: tuple[str, ...]
    suggested_paths: tuple[str, ...]
    suggested_auditors: tuple[str, ...]
    memory_provenance: str
    comparison: dict[str, tuple[str, ...]]
    pre_audit_current_context: MemoryCurrentContext | None = None
    post_audit_current_context: MemoryCurrentContext | None = None
    candidate_reason_codes: dict[str, tuple[str, ...]] | None = None
    effective_disclosure: DisclosureLevel = DisclosureLevel.HEADER
    operational_metrics: MemoryOperationalMetrics | None = None
    candidate_disclosures: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        if type(self.memory_diagnostics) is not tuple:
            raise ValueError("Memory diagnostics must be a tuple")
        if type(self.candidates) is not tuple:
            raise ValueError("Candidates must be a tuple")
        if type(self.selected_candidates) is not tuple:
            raise ValueError("Selected candidates must be a tuple")
        if type(self.revalidation_hints) is not tuple:
            raise ValueError("Revalidation hints must be a tuple")
        if type(self.freshness_summary) is not dict:
            raise ValueError("Freshness summary must be a dict")
        if type(self.suggested_symbols) is not tuple:
            raise ValueError("Suggested symbols must be a tuple")
        if type(self.suggested_paths) is not tuple:
            raise ValueError("Suggested paths must be a tuple")
        if type(self.suggested_auditors) is not tuple:
            raise ValueError("Suggested auditors must be a tuple")
        if type(self.memory_provenance) is not str:
            raise ValueError("Memory provenance must be a string")
        if type(self.comparison) is not dict:
            raise ValueError("Historical comparison must be a dict")
        for context in (self.pre_audit_current_context, self.post_audit_current_context):
            if context is not None and type(context) is not MemoryCurrentContext:
                raise ValueError("Historical provenance context is invalid")
        if self.candidate_reason_codes is not None and type(self.candidate_reason_codes) is not dict:
            raise ValueError("Candidate reason codes must be a dict")
        if type(self.effective_disclosure) is not DisclosureLevel:
            raise ValueError("Effective disclosure is invalid")
        if self.operational_metrics is not None and type(self.operational_metrics) is not MemoryOperationalMetrics:
            raise ValueError("Operational metrics are invalid")
        if type(self.candidate_disclosures) is not tuple:
            raise ValueError("Candidate disclosures must be a tuple")
