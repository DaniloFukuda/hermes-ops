from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionPathClassification(str, Enum):
    CONFIRMED_MISMATCH = "CONFIRMED_MISMATCH"
    POTENTIAL_MISMATCH = "POTENTIAL_MISMATCH"
    NO_MISMATCH = "NO_MISMATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    PATH_PROVEN_NO_COMPARABLE_CONTRACT = "PATH_PROVEN_NO_COMPARABLE_CONTRACT"


class ExecutionPathSeverity(str, Enum):
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ExecutionPathFinding:
    producer_symbol: str
    produced_value: str
    consumer_symbol: str
    required_precondition: str
    executable_path: tuple[str, ...]
    mismatch_description: str
    reachable_scenario: str
    severity: ExecutionPathSeverity
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutionPathReport:
    schema_version: int
    classification: ExecutionPathClassification
    producer_symbol: str
    consumer_symbol: str
    executable_path: tuple[str, ...]
    findings: tuple[ExecutionPathFinding, ...]
    evidence_references: tuple[str, ...]
    limitations: tuple[str, ...]
    structural_scope: tuple[str, ...]
