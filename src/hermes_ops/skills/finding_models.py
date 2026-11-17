from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.controlled_reader import valid_relative_path
from hermes_ops.skills.execution_models import FrozenValue, _freeze


_IDENTIFIER = re.compile(r"[a-z0-9](?:[a-z0-9._:-]*[a-z0-9])?\Z")


def _invalid(message: str) -> None:
    raise SkillExecutionError("FINDING_NORMALIZATION_INVALID", message)


class CommonSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceStrength(str, Enum):
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"


class ProductionReachability(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    path: str
    start_line: int
    end_line: int
    start_column: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        if type(self.path) is not str or not valid_relative_path(self.path):
            _invalid("Evidence reference path must be safely relative")
        if (
            type(self.start_line) is not int
            or type(self.end_line) is not int
            or self.start_line < 1
            or self.end_line < self.start_line
        ):
            _invalid("Evidence reference lines are invalid")
        if (self.start_column is None) != (self.end_column is None):
            _invalid("Evidence reference columns are incomplete")
        if self.start_column is not None and (
            type(self.start_column) is not int
            or type(self.end_column) is not int
            or self.start_column < 1
            or self.end_column < self.start_column
        ):
            _invalid("Evidence reference columns are invalid")


def evidence_ref_key(reference: EvidenceRef) -> tuple[str, int, int, int, int]:
    return (
        reference.path,
        reference.start_line,
        reference.end_line,
        reference.start_column if reference.start_column is not None else -1,
        reference.end_column if reference.end_column is not None else -1,
    )


@dataclass(frozen=True, slots=True)
class RankableFinding:
    schema_version: int
    finding_id: str
    source_skill: str
    summary: str
    severity: CommonSeverity
    evidence_strength: EvidenceStrength
    production_reachability: ProductionReachability
    evidence_refs: tuple[EvidenceRef, ...]
    domain_payload: FrozenValue

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            _invalid("Rankable finding schema version is invalid")
        if type(self.finding_id) is not str or _IDENTIFIER.fullmatch(self.finding_id) is None:
            _invalid("Rankable finding id is invalid")
        if type(self.source_skill) is not str or _IDENTIFIER.fullmatch(self.source_skill) is None:
            _invalid("Rankable finding source skill is invalid")
        if type(self.summary) is not str or not self.summary.strip():
            _invalid("Rankable finding summary is invalid")
        if type(self.severity) is not CommonSeverity:
            _invalid("Rankable finding severity is invalid")
        if type(self.evidence_strength) is not EvidenceStrength:
            _invalid("Rankable finding evidence strength is invalid")
        if type(self.production_reachability) is not ProductionReachability:
            _invalid("Rankable finding reachability is invalid")
        if (
            type(self.evidence_refs) is not tuple
            or not self.evidence_refs
            or any(type(item) is not EvidenceRef for item in self.evidence_refs)
        ):
            _invalid("Rankable finding evidence references are invalid")
        ordered = tuple(sorted(set(self.evidence_refs), key=evidence_ref_key))
        object.__setattr__(self, "evidence_refs", ordered)
        object.__setattr__(self, "domain_payload", _freeze(self.domain_payload))


@dataclass(frozen=True, slots=True)
class RankedFindingReport:
    schema_version: int
    top_finding: RankableFinding | None
    ordered_findings: tuple[RankableFinding, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            _invalid("Ranked finding report schema version is invalid")
        if type(self.ordered_findings) is not tuple or any(
            type(item) is not RankableFinding for item in self.ordered_findings
        ):
            _invalid("Ranked finding report items are invalid")
        expected = self.ordered_findings[0] if self.ordered_findings else None
        if self.top_finding != expected:
            _invalid("Ranked finding report top finding is inconsistent")
