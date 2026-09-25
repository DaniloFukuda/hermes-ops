from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ContentKind = Literal["active_code", "comment", "docstring"]
RelationshipKind = Literal["import", "symbol_reference", "naming_convention", "test_relation", "lexical_relation", "layer_convention"]


@dataclass(frozen=True, slots=True)
class SelectionTerm:
    term: str
    source: Literal["mission", "accent_alias", "lexical_bridge"]
    derived_from: tuple[str, ...] = ()
    matched_count: int = 0


@dataclass(frozen=True, slots=True)
class EvidenceFile:
    path: str
    roles: tuple[str, ...]
    score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvidenceRegion:
    path: str
    start_line: int
    end_line: int
    excerpt: str
    content_kind: ContentKind
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvidenceSymbol:
    name: str
    kind: Literal["class", "function", "method", "variable", "module"]
    path: str
    region: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    kind: RelationshipKind
    source: str
    target: str
    evidence_region: str
    reason: str
    supporting_relationship: str | None = None


@dataclass(frozen=True, slots=True)
class RelatedTest:
    path: str
    related_to: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MissionCompleteness:
    status: Literal["sufficient", "insufficient"]
    matched_terms: tuple[str, ...]
    unmatched_terms: tuple[str, ...]
    has_active_implementation: bool
    has_traceable_relationship: bool
    has_related_test: bool
    counts: tuple[tuple[str, int], ...]
    incompleteness_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MissionEvidencePack:
    schema_version: int
    mission: str
    target: str
    selection_terms: tuple[SelectionTerm, ...]
    files: tuple[EvidenceFile, ...]
    regions: tuple[EvidenceRegion, ...]
    symbols: tuple[EvidenceSymbol, ...]
    relationships: tuple[EvidenceRelationship, ...]
    related_tests: tuple[RelatedTest, ...]
    unresolved_questions: tuple[str, ...]
    completeness: MissionCompleteness
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.target != "<PROJECT_ROOT>" or not self.mission:
            raise ValueError("invalid mission evidence pack")
