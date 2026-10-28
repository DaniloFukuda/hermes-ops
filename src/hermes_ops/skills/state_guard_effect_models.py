from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from hermes_ops.core.errors import SkillExecutionError


_IDENTIFIER = re.compile(r"[A-Za-z_]\w*\Z")
_MAX_FIELD_LENGTH = 200


def _invalid(message: str) -> None:
    raise SkillExecutionError("STATE_GUARD_EFFECT_INVALID_REQUEST", message)


class StateGuardEffectClassification(str, Enum):
    CONFIRMED_CONTRACT_MISMATCH = "CONFIRMED_CONTRACT_MISMATCH"
    POTENTIAL_CONTRACT_MISMATCH = "POTENTIAL_CONTRACT_MISMATCH"
    CONTRACT_STRUCTURALLY_ALIGNED = "CONTRACT_STRUCTURALLY_ALIGNED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class StateGuardEffectFindingKind(str, Enum):
    STATE_EFFECT_COVERAGE_MISMATCH = "STATE_EFFECT_COVERAGE_MISMATCH"


class StateGuardEffectSeverity(str, Enum):
    MEDIUM = "medium"


class StateGuardEffectReachability(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"


class StatePathStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class StateBindingRequest:
    source_parameter: str
    field: str | None = None

    def __post_init__(self) -> None:
        if type(self.source_parameter) is not str or _IDENTIFIER.fullmatch(self.source_parameter) is None:
            _invalid("State source parameter must be a simple identifier")
        if self.field is not None and (
            type(self.field) is not str
            or not self.field
            or len(self.field) > _MAX_FIELD_LENGTH
        ):
            _invalid("State field must be non-empty bounded text when supplied")


@dataclass(frozen=True, slots=True)
class StateGuardEffectReviewRequest:
    operation_symbol: str
    state_binding: StateBindingRequest
    input_state_literal: str | int | bool | None
    expected_effect_symbol: str
    structural_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for label, value in (
            ("operation", self.operation_symbol),
            ("expected effect", self.expected_effect_symbol),
        ):
            if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
                _invalid(f"State guard effect {label} must be a simple identifier")
        if type(self.state_binding) is not StateBindingRequest:
            _invalid("State guard effect binding is invalid")
        if type(self.input_state_literal) not in {str, int, bool, type(None)}:
            _invalid("State input must be a string, integer, boolean, or None literal")
        if type(self.structural_scope) is not tuple or any(
            type(item) is not str for item in self.structural_scope
        ):
            _invalid("Structural scope must be a tuple of paths")


@dataclass(frozen=True, slots=True)
class StateBindingFact:
    source_parameter: str
    field: str | None
    binding_identity: str
    generation_id: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StatePathFact:
    status: StatePathStatus
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StateGuardEffectFinding:
    kind: StateGuardEffectFindingKind
    operation_symbol: str
    state_binding: StateBindingRequest
    input_state_literal: str | int | bool | None
    expected_effect_symbol: str
    summary: str
    severity: StateGuardEffectSeverity
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StateGuardEffectReport:
    schema_version: int
    classification: StateGuardEffectClassification
    operation_symbol: str
    state_binding: StateBindingRequest
    input_state_literal: str | int | bool | None
    expected_effect_symbol: str
    reachability: StateGuardEffectReachability
    binding_fact: StateBindingFact | None
    paths: tuple[StatePathFact, ...]
    findings: tuple[StateGuardEffectFinding, ...]
    evidence_references: tuple[str, ...]
    limitations: tuple[str, ...]
    structural_scope: tuple[str, ...]
