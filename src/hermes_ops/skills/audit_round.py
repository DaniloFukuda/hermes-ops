from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.code_audit import CodeAuditAnalysis, audit_code_documents
from hermes_ops.skills.controlled_reader import (
    ScopedSourceSnapshot,
    SourceLimits,
    read_scoped_source_snapshot,
    validate_target,
)
from hermes_ops.skills.execution_path_models import (
    ExecutionPathClassification,
    ExecutionPathReport,
)
from hermes_ops.skills.execution_path_review import review_execution_path_documents
from hermes_ops.skills.finding_models import RankedFindingReport
from hermes_ops.skills.finding_ranking import (
    normalize_code_audit_finding,
    normalize_execution_path_report,
    normalize_persistence_contract_report,
    normalize_state_guard_effect_report,
    rank_findings,
)
from hermes_ops.skills.persistence_contract_models import (
    PersistenceContractClassification,
    PersistenceContractDialect,
    PersistenceContractReport,
    PersistenceContractReviewRequest,
    PersistenceMutationReviewRequest,
)
from hermes_ops.skills.persistence_contract_review import (
    review_persistence_contract_documents,
    review_persistence_mutation_documents,
)
from hermes_ops.skills.state_guard_effect_models import (
    StateBindingRequest,
    StateGuardEffectClassification,
    StateGuardEffectReport,
    StateGuardEffectReviewRequest,
)
from hermes_ops.skills.state_guard_effect_review import review_state_guard_effect_documents
from hermes_ops.skills.mission_audit import normalize_structural_scope


ROUND_SCHEMA_VERSION = 1
AUDITOR_VERSION = 1
NORMALIZER_VERSION = 1
_SYMBOL = re.compile(r"[A-Za-z_]\w*\Z")


def _invalid(code: str, message: str) -> None:
    raise SkillExecutionError(code, message)


class AuditorInputKind(str, Enum):
    SCOPED_SOURCE_SNAPSHOT = "scoped_source_snapshot"


class AuditorOutputKind(str, Enum):
    CODE_AUDIT_ANALYSIS = "code_audit_analysis"
    EXECUTION_PATH_REPORT = "execution_path_report"
    PERSISTENCE_CONTRACT_REPORT = "persistence_contract_report"
    STATE_GUARD_EFFECT_REPORT = "state_guard_effect_report"


class AuditorOutcomeStatus(str, Enum):
    COMPLETED_NO_FINDINGS = "COMPLETED_NO_FINDINGS"
    COMPLETED_WITH_FINDINGS = "COMPLETED_WITH_FINDINGS"
    COMPLETED_WITH_INSUFFICIENT_EVIDENCE = "COMPLETED_WITH_INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"


class AuditRoundStatus(str, Enum):
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_LIMITATIONS = "COMPLETED_WITH_LIMITATIONS"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class AuditorDefinition:
    auditor_id: str
    version: int
    input_kind: AuditorInputKind
    output_kind: AuditorOutputKind
    read_only: bool
    normalizer_id: str
    normalizer_version: int


CODE_AUDITOR = AuditorDefinition(
    "code-audit", AUDITOR_VERSION, AuditorInputKind.SCOPED_SOURCE_SNAPSHOT,
    AuditorOutputKind.CODE_AUDIT_ANALYSIS, True, "code-audit-h0017", NORMALIZER_VERSION,
)
EXECUTION_PATH_AUDITOR = AuditorDefinition(
    "execution-path-review", AUDITOR_VERSION, AuditorInputKind.SCOPED_SOURCE_SNAPSHOT,
    AuditorOutputKind.EXECUTION_PATH_REPORT, True, "execution-path-h0017", NORMALIZER_VERSION,
)
PERSISTENCE_CONTRACT_AUDITOR = AuditorDefinition(
    "persistence-contract-review", AUDITOR_VERSION, AuditorInputKind.SCOPED_SOURCE_SNAPSHOT,
    AuditorOutputKind.PERSISTENCE_CONTRACT_REPORT, True, "persistence-contract-h0017", NORMALIZER_VERSION,
)
STATE_GUARD_EFFECT_AUDITOR = AuditorDefinition(
    "state-guard-effect-review", AUDITOR_VERSION,
    AuditorInputKind.SCOPED_SOURCE_SNAPSHOT,
    AuditorOutputKind.STATE_GUARD_EFFECT_REPORT,
    True,
    "state-guard-effect-h0017",
    NORMALIZER_VERSION,
)
AUDITORS = (
    CODE_AUDITOR,
    EXECUTION_PATH_AUDITOR,
    PERSISTENCE_CONTRACT_AUDITOR,
    STATE_GUARD_EFFECT_AUDITOR,
)


@dataclass(frozen=True, slots=True)
class CodeAuditRequest:
    auditor_id: str = "code-audit"

    def __post_init__(self) -> None:
        if self.auditor_id != "code-audit":
            _invalid("AUDIT_ROUND_UNKNOWN_AUDITOR", "Code audit request has an invalid auditor")


@dataclass(frozen=True, slots=True)
class ExecutionPathAuditRequest:
    producer_symbol: str
    consumer_symbol: str
    auditor_id: str = "execution-path-review"

    def __post_init__(self) -> None:
        if self.auditor_id != "execution-path-review":
            _invalid("AUDIT_ROUND_UNKNOWN_AUDITOR", "Execution path request has an invalid auditor")
        if (
            type(self.producer_symbol) is not str
            or _SYMBOL.fullmatch(self.producer_symbol) is None
            or type(self.consumer_symbol) is not str
            or _SYMBOL.fullmatch(self.consumer_symbol) is None
        ):
            _invalid("AUDIT_ROUND_INVALID_REQUEST", "Execution path symbols must be simple identifiers")


@dataclass(frozen=True, slots=True)
class PersistenceContractAuditRequest:
    producer_symbol: str
    consumer_symbol: str
    dialect: PersistenceContractDialect
    target_table: str
    identity_column: str
    expected_state: str | None = None
    auditor_id: str = "persistence-contract-review"

    def __post_init__(self) -> None:
        if self.auditor_id != "persistence-contract-review":
            _invalid("AUDIT_ROUND_UNKNOWN_AUDITOR", "Persistence contract request has an invalid auditor")
        try:
            PersistenceContractReviewRequest(
                self.producer_symbol, self.consumer_symbol, self.dialect,
                self.target_table, self.identity_column, self.expected_state,
            )
        except SkillExecutionError as error:
            _invalid("AUDIT_ROUND_INVALID_REQUEST", str(error))


@dataclass(frozen=True, slots=True)
class PersistenceMutationAuditRequest:
    operation_symbol: str
    dialect: PersistenceContractDialect
    target_table: str
    identity_column: str
    expected_state_column: str | None = None
    expected_state_value: str | None = None
    activation_guard_symbol: str | None = None
    auditor_id: str = "persistence-contract-review"

    def __post_init__(self) -> None:
        if self.auditor_id != "persistence-contract-review":
            _invalid("AUDIT_ROUND_UNKNOWN_AUDITOR", "Persistence mutation request has an invalid auditor")
        try:
            PersistenceMutationReviewRequest(
                self.operation_symbol, self.dialect, self.target_table,
                self.identity_column, self.expected_state_column,
                self.expected_state_value, self.activation_guard_symbol,
            )
        except SkillExecutionError as error:
            _invalid("AUDIT_ROUND_INVALID_REQUEST", str(error))


@dataclass(frozen=True, slots=True)
class StateGuardEffectAuditRequest:
    operation_symbol: str
    state_binding: StateBindingRequest
    input_state_literal: str | int | bool | None
    expected_effect_symbol: str
    auditor_id: str = "state-guard-effect-review"

    def __post_init__(self) -> None:
        if self.auditor_id != "state-guard-effect-review":
            _invalid("AUDIT_ROUND_UNKNOWN_AUDITOR", "State guard effect request has an invalid auditor")
        try:
            StateGuardEffectReviewRequest(
                self.operation_symbol,
                self.state_binding,
                self.input_state_literal,
                self.expected_effect_symbol,
            )
        except SkillExecutionError as error:
            _invalid("AUDIT_ROUND_INVALID_REQUEST", str(error))


AuditRequest = (
    CodeAuditRequest | ExecutionPathAuditRequest | PersistenceContractAuditRequest
    | PersistenceMutationAuditRequest | StateGuardEffectAuditRequest
)


@dataclass(frozen=True, slots=True)
class AuditRoundRequest:
    target: str | Path
    auditor_requests: tuple[AuditRequest, ...]
    structural_scope: tuple[str, ...] = ()
    schema_version: int = ROUND_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != ROUND_SCHEMA_VERSION:
            _invalid("AUDIT_ROUND_INVALID_REQUEST", "Audit round schema is unsupported")
        if not isinstance(self.target, (str, Path)):
            _invalid("AUDIT_ROUND_INVALID_REQUEST", "Audit round requires an explicit target")
        if type(self.auditor_requests) is not tuple:
            _invalid("AUDIT_ROUND_INVALID_REQUEST", "Auditor requests must be a tuple")
        allowed = (
            CodeAuditRequest, ExecutionPathAuditRequest,
            PersistenceContractAuditRequest, PersistenceMutationAuditRequest,
            StateGuardEffectAuditRequest,
        )
        if any(type(item) not in allowed for item in self.auditor_requests):
            _invalid("AUDIT_ROUND_UNKNOWN_AUDITOR", "Audit round contains an unknown auditor")
        ids = tuple(item.auditor_id for item in self.auditor_requests)
        if len(set(ids)) != len(ids):
            _invalid("AUDIT_ROUND_DUPLICATE_AUDITOR", "Audit round contains a duplicate auditor")
        if type(self.structural_scope) is not tuple or any(
            type(item) is not str for item in self.structural_scope
        ):
            _invalid("STRUCTURAL_SCOPE_INVALID_PATH", "Structural scope must be a tuple")
        object.__setattr__(self, "auditor_requests", tuple(sorted(self.auditor_requests, key=lambda item: item.auditor_id)))


@dataclass(frozen=True, slots=True)
class CodeAuditorInput:
    snapshot: ScopedSourceSnapshot


@dataclass(frozen=True, slots=True)
class ExecutionPathAuditorInput:
    snapshot: ScopedSourceSnapshot
    producer_symbol: str
    consumer_symbol: str


@dataclass(frozen=True, slots=True)
class PersistenceContractAuditorInput:
    snapshot: ScopedSourceSnapshot
    request: PersistenceContractReviewRequest | PersistenceMutationReviewRequest


@dataclass(frozen=True, slots=True)
class StateGuardEffectAuditorInput:
    snapshot: ScopedSourceSnapshot
    request: StateGuardEffectReviewRequest


NativeResult = (
    CodeAuditAnalysis | ExecutionPathReport | PersistenceContractReport
    | StateGuardEffectReport
)


@dataclass(frozen=True, slots=True)
class AuditorOutcome:
    auditor_id: str
    auditor_version: int
    normalizer_id: str
    normalizer_version: int
    status: AuditorOutcomeStatus
    native_result: NativeResult | None
    error_code: str | None
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SnapshotProvenance:
    schema_version: int
    digest: str
    structural_scope: tuple[str, ...]
    applied_limits: SourceLimits
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuditRoundResult:
    schema_version: int
    snapshot_provenance: SnapshotProvenance | None
    auditor_outcomes: tuple[AuditorOutcome, ...]
    ranked_findings: RankedFindingReport
    status: AuditRoundStatus
    limitations: tuple[str, ...]
    ranking_schema_version: int = 1


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def audit_round_json(result: AuditRoundResult) -> str:
    if type(result) is not AuditRoundResult:
        _invalid("AUDIT_ROUND_INVALID_RESULT", "Serialization requires an audit round result")
    return json.dumps(_plain(result), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _error_code(error: Exception) -> str:
    code = getattr(error, "code", None)
    return code if type(code) is str and code else "AUDITOR_EXECUTION_FAILED"


def _run_code(value: CodeAuditorInput) -> CodeAuditAnalysis:
    return audit_code_documents(value.snapshot.documents, value.snapshot.directories)


def _run_execution_path(value: ExecutionPathAuditorInput) -> ExecutionPathReport:
    return review_execution_path_documents(
        value.snapshot.documents,
        value.producer_symbol,
        value.consumer_symbol,
        structural_scope=value.snapshot.structural_scope,
    )


def _run_persistence_contract(value: PersistenceContractAuditorInput) -> PersistenceContractReport:
    if type(value.request) is PersistenceMutationReviewRequest:
        return review_persistence_mutation_documents(value.snapshot.documents, value.request)
    return review_persistence_contract_documents(value.snapshot.documents, value.request)


def _run_state_guard_effect(value: StateGuardEffectAuditorInput) -> StateGuardEffectReport:
    return review_state_guard_effect_documents(value.snapshot.documents, value.request)


def _failed_round(code: str) -> AuditRoundResult:
    return AuditRoundResult(
        ROUND_SCHEMA_VERSION, None, (), rank_findings(()), AuditRoundStatus.FAILED, (code,)
    )


def run_audit_round(request: AuditRoundRequest) -> AuditRoundResult:
    if type(request) is not AuditRoundRequest:
        _invalid("AUDIT_ROUND_INVALID_REQUEST", "Audit round request is invalid")
    try:
        root = validate_target(request.target)
        scope = normalize_structural_scope(request.structural_scope, root)
        snapshot = read_scoped_source_snapshot(request.target, structural_scope=scope)
    except Exception as error:
        return _failed_round(_error_code(error))

    outcomes: list[AuditorOutcome] = []
    for item in request.auditor_requests:
        if type(item) is CodeAuditRequest:
            definition = CODE_AUDITOR
        elif type(item) is ExecutionPathAuditRequest:
            definition = EXECUTION_PATH_AUDITOR
        elif type(item) is StateGuardEffectAuditRequest:
            definition = STATE_GUARD_EFFECT_AUDITOR
        else:
            definition = PERSISTENCE_CONTRACT_AUDITOR
        try:
            if type(item) is CodeAuditRequest:
                native: NativeResult = _run_code(CodeAuditorInput(snapshot))
                status = (
                    AuditorOutcomeStatus.COMPLETED_WITH_FINDINGS
                    if native.findings else AuditorOutcomeStatus.COMPLETED_NO_FINDINGS
                )
                limitations: tuple[str, ...] = ()
            elif type(item) is ExecutionPathAuditRequest:
                native = _run_execution_path(
                    ExecutionPathAuditorInput(snapshot, item.producer_symbol, item.consumer_symbol)
                )
                if native.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE
                elif native.findings:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_FINDINGS
                else:
                    status = AuditorOutcomeStatus.COMPLETED_NO_FINDINGS
                limitations = native.limitations
            elif type(item) is StateGuardEffectAuditRequest:
                native = _run_state_guard_effect(StateGuardEffectAuditorInput(
                    snapshot,
                    StateGuardEffectReviewRequest(
                        item.operation_symbol,
                        item.state_binding,
                        item.input_state_literal,
                        item.expected_effect_symbol,
                        snapshot.structural_scope,
                    ),
                ))
                if native.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE
                elif native.findings:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_FINDINGS
                else:
                    status = AuditorOutcomeStatus.COMPLETED_NO_FINDINGS
                limitations = native.limitations
            elif type(item) is PersistenceContractAuditRequest:
                native = _run_persistence_contract(PersistenceContractAuditorInput(
                    snapshot,
                    PersistenceContractReviewRequest(
                        item.producer_symbol, item.consumer_symbol, item.dialect,
                        item.target_table, item.identity_column, item.expected_state,
                        snapshot.structural_scope,
                    ),
                ))
                if native.classification is PersistenceContractClassification.INSUFFICIENT_EVIDENCE:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE
                elif native.findings:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_FINDINGS
                else:
                    status = AuditorOutcomeStatus.COMPLETED_NO_FINDINGS
                limitations = native.limitations
            else:
                native = _run_persistence_contract(PersistenceContractAuditorInput(
                    snapshot,
                    PersistenceMutationReviewRequest(
                        item.operation_symbol, item.dialect, item.target_table,
                        item.identity_column, item.expected_state_column,
                        item.expected_state_value, item.activation_guard_symbol,
                        snapshot.structural_scope,
                    ),
                ))
                if native.classification is PersistenceContractClassification.INSUFFICIENT_EVIDENCE:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE
                elif native.findings:
                    status = AuditorOutcomeStatus.COMPLETED_WITH_FINDINGS
                else:
                    status = AuditorOutcomeStatus.COMPLETED_NO_FINDINGS
                limitations = native.limitations
            outcome = AuditorOutcome(
                definition.auditor_id, definition.version, definition.normalizer_id,
                definition.normalizer_version, status, native, None, limitations,
            )
        except Exception as error:
            code = _error_code(error)
            outcome = AuditorOutcome(
                definition.auditor_id, definition.version, definition.normalizer_id,
                definition.normalizer_version, AuditorOutcomeStatus.FAILED, None, code, (code,),
            )
        outcomes.append(outcome)

    normalized = []
    for outcome in outcomes:
        if outcome.status is not AuditorOutcomeStatus.COMPLETED_WITH_FINDINGS:
            continue
        if type(outcome.native_result) is CodeAuditAnalysis:
            normalized.extend(
                normalize_code_audit_finding(item) for item in outcome.native_result.findings
            )
        elif type(outcome.native_result) is ExecutionPathReport:
            normalized.extend(normalize_execution_path_report(outcome.native_result))
        elif type(outcome.native_result) is PersistenceContractReport:
            normalized.extend(normalize_persistence_contract_report(outcome.native_result))
        elif type(outcome.native_result) is StateGuardEffectReport:
            normalized.extend(normalize_state_guard_effect_report(outcome.native_result))
    ranked = rank_findings(tuple(normalized))
    limited = any(
        item.status in {
            AuditorOutcomeStatus.FAILED,
            AuditorOutcomeStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE,
        }
        for item in outcomes
    )
    limitations = tuple(
        f"{item.auditor_id}:{limitation}"
        for item in outcomes
        for limitation in item.limitations
    )
    provenance = SnapshotProvenance(
        snapshot.schema_version, snapshot.digest, snapshot.structural_scope,
        snapshot.applied_limits, snapshot.limitations,
    )
    return AuditRoundResult(
        ROUND_SCHEMA_VERSION, provenance, tuple(outcomes), ranked,
        AuditRoundStatus.COMPLETED_WITH_LIMITATIONS if limited else AuditRoundStatus.COMPLETED,
        limitations,
    )
