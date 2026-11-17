from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from hermes_ops.core.errors import SkillExecutionError


_IDENTIFIER = re.compile(r"[A-Za-z_]\w*\Z")


def _invalid(message: str) -> None:
    raise SkillExecutionError("PERSISTENCE_CONTRACT_INVALID_REQUEST", message)


class PersistenceContractDialect(str, Enum):
    SQLITE_DBAPI = "SQLITE_DBAPI"


class PersistenceContractClassification(str, Enum):
    CONFIRMED_CONTRACT_MISMATCH = "CONFIRMED_CONTRACT_MISMATCH"
    POTENTIAL_CONTRACT_MISMATCH = "POTENTIAL_CONTRACT_MISMATCH"
    CONTRACT_STRUCTURALLY_ALIGNED = "CONTRACT_STRUCTURALLY_ALIGNED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class PersistenceContractFindingKind(str, Enum):
    TARGET_TABLE_MISMATCH = "TARGET_TABLE_MISMATCH"
    TARGET_KEY_MISMATCH = "TARGET_KEY_MISMATCH"
    WRITE_READ_IDENTITY_MISMATCH = "WRITE_READ_IDENTITY_MISMATCH"
    STATE_INTENT_MISMATCH = "STATE_INTENT_MISMATCH"
    MUTATION_TARGET_TABLE_MISMATCH = "MUTATION_TARGET_TABLE_MISMATCH"
    MUTATION_TARGET_KEY_MISMATCH = "MUTATION_TARGET_KEY_MISMATCH"
    MUTATION_STATE_MISMATCH = "MUTATION_STATE_MISMATCH"


class PersistenceContractSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"


class PersistenceContractReachability(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PersistenceContractReviewRequest:
    producer_symbol: str
    consumer_symbol: str
    dialect: PersistenceContractDialect
    target_table: str
    identity_column: str
    expected_state: str | None = None
    structural_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("producer", self.producer_symbol),
            ("consumer", self.consumer_symbol),
            ("target table", self.target_table),
            ("identity column", self.identity_column),
        ):
            if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
                _invalid(f"Persistence contract {name} must be a simple identifier")
        if type(self.dialect) is not PersistenceContractDialect:
            _invalid("Persistence contract dialect is unsupported")
        if self.expected_state is not None and type(self.expected_state) is not str:
            _invalid("Expected state must be text when supplied")
        if type(self.structural_scope) is not tuple or any(
            type(item) is not str for item in self.structural_scope
        ):
            _invalid("Structural scope must be a tuple of paths")


@dataclass(frozen=True, slots=True)
class PersistenceMutationReviewRequest:
    operation_symbol: str
    dialect: PersistenceContractDialect
    target_table: str
    identity_column: str
    expected_state_column: str | None = None
    expected_state_value: str | None = None
    activation_guard_symbol: str | None = None
    structural_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("operation", self.operation_symbol),
            ("target table", self.target_table),
            ("identity column", self.identity_column),
        ):
            if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
                _invalid(f"Persistence mutation {name} must be a simple identifier")
        if type(self.dialect) is not PersistenceContractDialect:
            _invalid("Persistence mutation dialect is unsupported")
        if (self.expected_state_column is None) != (self.expected_state_value is None):
            _invalid("Expected state column and value must be supplied together")
        if self.expected_state_column is not None and (
            type(self.expected_state_column) is not str
            or _IDENTIFIER.fullmatch(self.expected_state_column) is None
            or type(self.expected_state_value) is not str
        ):
            _invalid("Persistence mutation expected state is invalid")
        if self.activation_guard_symbol is not None and (
            type(self.activation_guard_symbol) is not str
            or _IDENTIFIER.fullmatch(self.activation_guard_symbol) is None
        ):
            _invalid("Persistence mutation activation guard must be a simple identifier")
        if type(self.structural_scope) is not tuple or any(
            type(item) is not str for item in self.structural_scope
        ):
            _invalid("Structural scope must be a tuple of paths")


@dataclass(frozen=True, slots=True)
class WriteIntentFact:
    table: str
    columns: tuple[str, ...]
    bindings: tuple[str, ...]
    cursor_symbol: str
    evidence_reference: str


@dataclass(frozen=True, slots=True)
class IdentityBindingFact:
    cursor_symbol: str
    identity_symbol: str
    mechanism: str
    write_table: str
    evidence_reference: str


@dataclass(frozen=True, slots=True)
class ReadRequirementFact:
    table: str
    selected_columns: tuple[str, ...]
    predicate_column: str
    predicate_value_identity: str
    fetch_kind: str
    success_guard: bool
    evidence_reference: str


@dataclass(frozen=True, slots=True)
class StateTransitionIntentFact:
    table: str
    column: str
    value: str
    predicate_column: str
    predicate_value_identity: str
    evidence_reference: str


@dataclass(frozen=True, slots=True)
class MutationIntentFact:
    operation_symbol: str
    table: str
    assignments: tuple[tuple[str, str], ...]
    predicate_column: str
    predicate_value_origin: str
    call_path: tuple[str, ...]
    evidence_references: tuple[str, ...]
    literal_assignment_columns: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PersistenceContractFinding:
    kind: PersistenceContractFindingKind
    summary: str
    severity: PersistenceContractSeverity
    evidence_references: tuple[str, ...]
    target_table: str
    target_key: str
    observed_table: str | None = None
    observed_key: str | None = None


@dataclass(frozen=True, slots=True)
class PersistenceContractReport:
    schema_version: int
    classification: PersistenceContractClassification
    producer_symbol: str
    consumer_symbol: str
    dialect: PersistenceContractDialect
    target_table: str
    identity_column: str
    executable_path: tuple[str, ...]
    production_reachability: PersistenceContractReachability
    write_intents: tuple[WriteIntentFact, ...]
    identity_bindings: tuple[IdentityBindingFact, ...]
    read_requirements: tuple[ReadRequirementFact, ...]
    state_transition_intents: tuple[StateTransitionIntentFact, ...]
    findings: tuple[PersistenceContractFinding, ...]
    evidence_references: tuple[str, ...]
    limitations: tuple[str, ...]
    structural_scope: tuple[str, ...]
    mutation_intents: tuple[MutationIntentFact, ...] = ()
