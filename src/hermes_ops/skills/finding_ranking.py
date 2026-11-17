from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.code_audit import (
    CodeAuditClassification,
    CodeAuditFinding,
    CodeAuditSeverity,
)
from hermes_ops.skills.execution_path_models import (
    ExecutionPathClassification,
    ExecutionPathFinding,
    ExecutionPathReport,
    ExecutionPathSeverity,
)
from hermes_ops.skills.finding_models import (
    CommonSeverity,
    EvidenceRef,
    EvidenceStrength,
    ProductionReachability,
    RankableFinding,
    RankedFindingReport,
    evidence_ref_key,
)
from hermes_ops.skills.persistence_contract_models import (
    PersistenceContractClassification,
    PersistenceContractFindingKind,
    PersistenceContractReachability,
    PersistenceContractReport,
    PersistenceContractSeverity,
)
from hermes_ops.skills.state_guard_effect_models import (
    StateGuardEffectClassification,
    StateGuardEffectFinding,
    StateGuardEffectFindingKind,
    StateGuardEffectReachability,
    StateGuardEffectReport,
    StateGuardEffectSeverity,
)
from hermes_ops.skills.source_evidence import parse_source_locator


_CODE_SEVERITY = {
    CodeAuditSeverity.INFO: CommonSeverity.INFO,
    CodeAuditSeverity.LOW: CommonSeverity.LOW,
    CodeAuditSeverity.MEDIUM: CommonSeverity.MEDIUM,
    CodeAuditSeverity.HIGH: CommonSeverity.HIGH,
    CodeAuditSeverity.CRITICAL: CommonSeverity.CRITICAL,
}
_PATH_SEVERITY = {
    ExecutionPathSeverity.MEDIUM: CommonSeverity.MEDIUM,
    ExecutionPathSeverity.HIGH: CommonSeverity.HIGH,
}
_CODE_STRENGTH = {
    CodeAuditClassification.OBSERVED: EvidenceStrength.CONFIRMED,
    CodeAuditClassification.HYPOTHESIS: EvidenceStrength.PARTIAL,
}
_PATH_STRENGTH = {
    ExecutionPathClassification.CONFIRMED_MISMATCH: EvidenceStrength.CONFIRMED,
    ExecutionPathClassification.POTENTIAL_MISMATCH: EvidenceStrength.PARTIAL,
}
_PERSISTENCE_STRENGTH = {
    PersistenceContractClassification.CONFIRMED_CONTRACT_MISMATCH: EvidenceStrength.CONFIRMED,
    PersistenceContractClassification.POTENTIAL_CONTRACT_MISMATCH: EvidenceStrength.PARTIAL,
}
_PERSISTENCE_SEVERITY = {
    PersistenceContractSeverity.LOW: CommonSeverity.LOW,
    PersistenceContractSeverity.MEDIUM: CommonSeverity.MEDIUM,
}
_STATE_STRENGTH = {
    StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH: EvidenceStrength.CONFIRMED,
    StateGuardEffectClassification.POTENTIAL_CONTRACT_MISMATCH: EvidenceStrength.PARTIAL,
}
_STATE_SEVERITY = {
    StateGuardEffectSeverity.MEDIUM: CommonSeverity.MEDIUM,
}
_REACHABILITY_ORDER = {
    ProductionReachability.CONFIRMED: 0,
    ProductionReachability.UNKNOWN: 1,
}
_STRENGTH_ORDER = {
    EvidenceStrength.CONFIRMED: 0,
    EvidenceStrength.PARTIAL: 1,
}
_SEVERITY_ORDER = {
    CommonSeverity.CRITICAL: 0,
    CommonSeverity.HIGH: 1,
    CommonSeverity.MEDIUM: 2,
    CommonSeverity.LOW: 3,
    CommonSeverity.INFO: 4,
}


def _invalid(message: str) -> None:
    raise SkillExecutionError("FINDING_NORMALIZATION_INVALID", message)


def _canonical(value: Any) -> str:
    return json.dumps(
        _plain(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        if value and all(
            isinstance(item, tuple)
            and len(item) == 2
            and isinstance(item[0], str)
            for item in value
        ):
            return {item[0]: _plain(item[1]) for item in value}
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    return value


def _finding_id(source_skill: str, identity: Any) -> str:
    digest = hashlib.sha256(_canonical((source_skill, identity)).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def normalize_code_audit_finding(finding: Any) -> RankableFinding:
    if type(finding) is not CodeAuditFinding:
        _invalid("Code audit normalizer requires a CodeAuditFinding")
    try:
        severity = _CODE_SEVERITY[finding.severity]
        strength = _CODE_STRENGTH[finding.classification]
    except (KeyError, TypeError) as exc:
        raise SkillExecutionError(
            "FINDING_NORMALIZATION_INVALID",
            "Code audit finding contains an unsupported enum value",
        ) from exc
    region = finding.region
    reference = EvidenceRef(
        finding.file,
        region.start_line,
        region.end_line,
        region.start_column,
        region.end_column,
    )
    identity = (
        finding.rule_id,
        finding.file,
        region.start_line,
        region.end_line,
        region.start_column,
        region.end_column,
    )
    return RankableFinding(
        1,
        _finding_id("code-audit", identity),
        "code-audit",
        finding.observation,
        severity,
        strength,
        ProductionReachability.UNKNOWN,
        (reference,),
        finding,
    )


def _path_reference(value: Any) -> EvidenceRef:
    return parse_source_locator(value)


def _has_confirmed_path(finding: ExecutionPathFinding) -> bool:
    return bool(
        len(finding.executable_path) >= 2
        and finding.executable_path[0] == finding.producer_symbol
        and finding.executable_path[-1] == finding.consumer_symbol
        and len(finding.evidence_references) >= 3
    )


def _normalize_execution_finding(
    finding: Any,
    classification: ExecutionPathClassification,
) -> RankableFinding:
    if type(finding) is not ExecutionPathFinding:
        _invalid("Execution path report contains an invalid finding")
    try:
        severity = _PATH_SEVERITY[finding.severity]
        strength = _PATH_STRENGTH[classification]
    except (KeyError, TypeError) as exc:
        raise SkillExecutionError(
            "FINDING_NORMALIZATION_INVALID",
            "Execution path finding contains an unsupported enum value",
        ) from exc
    references = tuple(_path_reference(item) for item in finding.evidence_references)
    reachability = (
        ProductionReachability.CONFIRMED
        if classification is ExecutionPathClassification.CONFIRMED_MISMATCH
        and _has_confirmed_path(finding)
        else ProductionReachability.UNKNOWN
    )
    identity = (
        finding.producer_symbol,
        finding.consumer_symbol,
        finding.executable_path,
        tuple(evidence_ref_key(item) for item in sorted(references, key=evidence_ref_key)),
    )
    return RankableFinding(
        1,
        _finding_id("execution-path-review", identity),
        "execution-path-review",
        finding.mismatch_description,
        severity,
        strength,
        reachability,
        references,
        finding,
    )


def normalize_execution_path_report(report: Any) -> tuple[RankableFinding, ...]:
    if type(report) is not ExecutionPathReport:
        _invalid("Execution path normalizer requires an ExecutionPathReport")
    classification = report.classification
    if classification in {
        ExecutionPathClassification.NO_MISMATCH,
        ExecutionPathClassification.INSUFFICIENT_EVIDENCE,
        ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT,
    }:
        return ()
    if classification not in _PATH_STRENGTH:
        _invalid("Execution path report classification is unsupported")
    if not report.findings:
        _invalid("Actionable execution path report has no findings")
    return tuple(
        _normalize_execution_finding(finding, classification)
        for finding in report.findings
    )


def normalize_persistence_contract_report(report: Any) -> tuple[RankableFinding, ...]:
    if type(report) is not PersistenceContractReport:
        _invalid("Persistence contract normalizer requires a PersistenceContractReport")
    if report.classification in {
        PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED,
        PersistenceContractClassification.INSUFFICIENT_EVIDENCE,
    }:
        return ()
    try:
        strength = _PERSISTENCE_STRENGTH[report.classification]
    except (KeyError, TypeError) as exc:
        raise SkillExecutionError(
            "FINDING_NORMALIZATION_INVALID",
            "Persistence contract classification is unsupported",
        ) from exc
    if not report.findings:
        _invalid("Actionable persistence contract report has no findings")
    normalized = []
    for finding in report.findings:
        try:
            _PERSISTENCE_SEVERITY[finding.severity]
        except (KeyError, TypeError) as exc:
            raise SkillExecutionError(
                "FINDING_NORMALIZATION_INVALID",
                "Persistence contract finding contains an unsupported severity",
            ) from exc
        severity = (
            CommonSeverity.LOW
            if finding.kind is PersistenceContractFindingKind.MUTATION_STATE_MISMATCH
            else CommonSeverity.MEDIUM
            if report.classification is PersistenceContractClassification.CONFIRMED_CONTRACT_MISMATCH
            else CommonSeverity.LOW
        )
        references = tuple(_path_reference(item) for item in finding.evidence_references)
        identity = (
            finding.kind,
            finding.target_table,
            finding.target_key,
            finding.observed_table,
            finding.observed_key,
            tuple(evidence_ref_key(item) for item in sorted(references, key=evidence_ref_key)),
        )
        normalized.append(RankableFinding(
            1,
            _finding_id("persistence-contract-review", identity),
            "persistence-contract-review",
            finding.summary,
            severity,
            strength,
            ProductionReachability.CONFIRMED
            if report.production_reachability is PersistenceContractReachability.CONFIRMED
            else ProductionReachability.UNKNOWN,
            references,
            finding,
        ))
    return tuple(normalized)


def normalize_state_guard_effect_report(report: Any) -> tuple[RankableFinding, ...]:
    if type(report) is not StateGuardEffectReport:
        _invalid("State guard effect normalizer requires a StateGuardEffectReport")
    if report.classification in {
        StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED,
        StateGuardEffectClassification.INSUFFICIENT_EVIDENCE,
    }:
        return ()
    try:
        strength = _STATE_STRENGTH[report.classification]
    except (KeyError, TypeError) as exc:
        raise SkillExecutionError(
            "FINDING_NORMALIZATION_INVALID",
            "State guard effect classification is unsupported",
        ) from exc
    if not report.findings:
        _invalid("Actionable state guard effect report has no findings")
    normalized = []
    for finding in report.findings:
        if type(finding) is not StateGuardEffectFinding:
            _invalid("State guard effect report contains an invalid finding")
        if finding.kind is not StateGuardEffectFindingKind.STATE_EFFECT_COVERAGE_MISMATCH:
            _invalid("State guard effect finding kind is unsupported")
        try:
            severity = _STATE_SEVERITY[finding.severity]
        except (KeyError, TypeError) as exc:
            raise SkillExecutionError(
                "FINDING_NORMALIZATION_INVALID",
                "State guard effect finding severity is unsupported",
            ) from exc
        references = tuple(_path_reference(item) for item in finding.evidence_references)
        literal_identity = (
            type(finding.input_state_literal).__name__,
            finding.input_state_literal,
        )
        identity = (
            finding.kind,
            finding.operation_symbol,
            finding.state_binding,
            literal_identity,
            finding.expected_effect_symbol,
            tuple(evidence_ref_key(item) for item in sorted(references, key=evidence_ref_key)),
        )
        normalized.append(RankableFinding(
            1,
            _finding_id("state-guard-effect-review", identity),
            "state-guard-effect-review",
            finding.summary,
            severity,
            strength,
            ProductionReachability.CONFIRMED
            if report.reachability is StateGuardEffectReachability.CONFIRMED
            else ProductionReachability.UNKNOWN,
            references,
            finding,
        ))
    return tuple(normalized)


def _ranking_key(finding: RankableFinding) -> tuple[int, int, int, str, str]:
    return (
        _REACHABILITY_ORDER[finding.production_reachability],
        _STRENGTH_ORDER[finding.evidence_strength],
        _SEVERITY_ORDER[finding.severity],
        finding.source_skill,
        finding.finding_id,
    )


def rank_findings(findings: Any) -> RankedFindingReport:
    if type(findings) is not tuple:
        _invalid("Ranking input must be a tuple of RankableFinding values")
    unique: dict[str, RankableFinding] = {}
    for finding in findings:
        if type(finding) is not RankableFinding:
            _invalid("Ranking input contains a non-rankable value")
        previous = unique.get(finding.finding_id)
        if previous is not None and previous != finding:
            raise SkillExecutionError(
                "FINDING_ID_COLLISION",
                "Different findings share the same deterministic identity",
            )
        unique[finding.finding_id] = finding
    ordered = tuple(sorted(unique.values(), key=_ranking_key))
    return RankedFindingReport(1, ordered[0] if ordered else None, ordered)


def ranked_finding_json(report: Any) -> str:
    if type(report) is not RankedFindingReport:
        _invalid("Serialization requires a RankedFindingReport")
    return _canonical(report)
