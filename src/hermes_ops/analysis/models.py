from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

FrozenObject = tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class ContextBudget:
    limit_chars: int
    used_chars: int
    remaining_chars: int
    canonical_utf8_bytes: int
    complete: bool


@dataclass(frozen=True, slots=True)
class OmissionSummary:
    omitted_files: int = 0
    omitted_regions: int = 0
    omitted_symbols: int = 0
    omitted_relationships: int = 0
    omitted_tests: int = 0
    omitted_ids_digest: str | None = None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AnalysisPack:
    schema_version: int
    source_schema_version: int
    source_hash: str
    mission: str
    question: str
    source_completeness: Literal["sufficient", "insufficient"]
    files: tuple[FrozenObject, ...]
    regions: tuple[FrozenObject, ...]
    symbols: tuple[FrozenObject, ...]
    relationships: tuple[FrozenObject, ...]
    tests: tuple[FrozenObject, ...]
    source_limitations: tuple[str, ...]
    reduction_limitations: tuple[str, ...]
    omissions: OmissionSummary
    budget: ContextBudget


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    schema_version: int
    instructions: tuple[str, ...]
    analysis_pack: AnalysisPack


@dataclass(frozen=True, slots=True)
class AnalysisClaim:
    id: str
    statement: str
    classification: Literal["supported", "plausible", "insufficient", "contradicted"]
    evidence_ids: tuple[str, ...]
    contrary_evidence_ids: tuple[str, ...]
    rationale: str
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    schema_version: int
    analysis_pack_hash: str
    question: str
    claims: tuple[AnalysisClaim, ...]
    overall_classification: Literal["supported", "plausible", "insufficient", "contradicted"]
    limitations: tuple[str, ...]
    omitted_evidence_summary: OmissionSummary
