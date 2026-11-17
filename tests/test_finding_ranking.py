from __future__ import annotations

from itertools import permutations
import json
from pathlib import Path

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.code_audit import (
    CodeAuditClassification,
    CodeAuditFinding,
    CodeAuditRegion,
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
)
from hermes_ops.skills.finding_ranking import (
    normalize_code_audit_finding,
    normalize_execution_path_report,
    normalize_persistence_contract_report,
    normalize_state_guard_effect_report,
    rank_findings,
    ranked_finding_json,
)
from hermes_ops.skills.persistence_contract_models import (
    PersistenceContractClassification,
    PersistenceContractDialect,
    PersistenceContractFinding,
    PersistenceContractFindingKind,
    PersistenceContractReachability,
    PersistenceContractReport,
    PersistenceContractSeverity,
)
from hermes_ops.skills.state_guard_effect_models import (
    StateBindingRequest,
    StateGuardEffectClassification,
    StateGuardEffectFinding,
    StateGuardEffectFindingKind,
    StateGuardEffectReachability,
    StateGuardEffectReport,
    StateGuardEffectSeverity,
)


def _code_finding(
    classification: CodeAuditClassification = CodeAuditClassification.OBSERVED,
    severity: CodeAuditSeverity = CodeAuditSeverity.HIGH,
    *,
    suggestion: str = "Use a safe alternative.",
) -> CodeAuditFinding:
    return CodeAuditFinding(
        "CA003",
        severity,
        classification,
        "src/service.py",
        CodeAuditRegion(7, 7, 3, 15),
        "verify=False",
        "TLS verification is disabled.",
        "The connection accepts untrusted certificates.",
        suggestion,
    )


def _execution_report(
    classification: ExecutionPathClassification,
) -> ExecutionPathReport:
    findings = ()
    path = ()
    references = ()
    if classification in {
        ExecutionPathClassification.CONFIRMED_MISMATCH,
        ExecutionPathClassification.POTENTIAL_MISMATCH,
    }:
        path = ("produce", "consume")
        references = ("src/flow.py:2", "src/flow.py:8", "src/flow.py:5")
        findings = (
            ExecutionPathFinding(
                "produce",
                "caller-controlled value",
                "consume",
                "value must be managed",
                path,
                "Produced value does not guarantee the consumer contract.",
                "A reachable call passes the value to consume.",
                ExecutionPathSeverity.HIGH,
                references,
            ),
        )
    return ExecutionPathReport(
        1,
        classification,
        "produce",
        "consume",
        path,
        findings,
        references,
        (),
        (),
    )


def _rankable(
    finding_id: str,
    *,
    source: str = "test-auditor",
    severity: CommonSeverity = CommonSeverity.MEDIUM,
    strength: EvidenceStrength = EvidenceStrength.PARTIAL,
    reachability: ProductionReachability = ProductionReachability.UNKNOWN,
    payload: object = "opaque",
) -> RankableFinding:
    return RankableFinding(
        1,
        finding_id,
        source,
        "A deterministic test finding.",
        severity,
        strength,
        reachability,
        (EvidenceRef("src/example.py", 1, 1),),
        payload,
    )


def test_code_audit_observed_normalizes_as_confirmed() -> None:
    """Spec: HERMES-0017 / AC-01"""
    finding = normalize_code_audit_finding(_code_finding())
    assert finding.source_skill == "code-audit"
    assert finding.severity is CommonSeverity.HIGH
    assert finding.evidence_strength is EvidenceStrength.CONFIRMED
    assert finding.production_reachability is ProductionReachability.UNKNOWN
    assert finding.evidence_refs == (EvidenceRef("src/service.py", 7, 7, 3, 15),)


def test_code_audit_hypothesis_normalizes_as_partial() -> None:
    """Spec: HERMES-0017 / AC-02"""
    finding = normalize_code_audit_finding(
        _code_finding(CodeAuditClassification.HYPOTHESIS)
    )
    assert finding.evidence_strength is EvidenceStrength.PARTIAL


def test_execution_confirmed_mismatch_has_confirmed_path() -> None:
    """Spec: HERMES-0017 / AC-03"""
    finding = normalize_execution_path_report(
        _execution_report(ExecutionPathClassification.CONFIRMED_MISMATCH)
    )[0]
    assert finding.evidence_strength is EvidenceStrength.CONFIRMED
    assert finding.production_reachability is ProductionReachability.CONFIRMED


def test_execution_potential_is_partial_with_unknown_reachability() -> None:
    """Spec: HERMES-0017 / AC-04"""
    finding = normalize_execution_path_report(
        _execution_report(ExecutionPathClassification.POTENTIAL_MISMATCH)
    )[0]
    assert finding.evidence_strength is EvidenceStrength.PARTIAL
    assert finding.production_reachability is ProductionReachability.UNKNOWN


@pytest.mark.parametrize(
    "classification",
    [
        ExecutionPathClassification.NO_MISMATCH,
        ExecutionPathClassification.INSUFFICIENT_EVIDENCE,
        ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT,
    ],
)
def test_non_actionable_execution_results_are_not_rankable(
    classification: ExecutionPathClassification,
) -> None:
    """Spec: HERMES-0017 / AC-05, AC-06, AC-17; HERMES-0023 / AC-18."""
    normalized = normalize_execution_path_report(_execution_report(classification))
    report = rank_findings(normalized)
    assert normalized == ()
    assert report.top_finding is None
    assert report.ordered_findings == ()


def test_unknown_severity_fails_closed() -> None:
    """Spec: HERMES-0017 / AC-07"""
    finding = _code_finding()
    object.__setattr__(finding, "severity", "urgent")
    with pytest.raises(SkillExecutionError) as caught:
        normalize_code_audit_finding(finding)
    assert caught.value.code == "FINDING_NORMALIZATION_INVALID"


def test_unknown_classification_fails_closed() -> None:
    """Spec: HERMES-0017 / AC-08"""
    report = _execution_report(ExecutionPathClassification.CONFIRMED_MISMATCH)
    object.__setattr__(report, "classification", "LIKELY")
    with pytest.raises(SkillExecutionError) as caught:
        normalize_execution_path_report(report)
    assert caught.value.code == "FINDING_NORMALIZATION_INVALID"


def test_finding_id_and_serialization_are_deterministic() -> None:
    """Spec: HERMES-0017 / AC-09, AC-10"""
    first = normalize_code_audit_finding(_code_finding())
    second = normalize_code_audit_finding(_code_finding())
    assert first.finding_id == second.finding_id
    assert ranked_finding_json(rank_findings((first,))) == ranked_finding_json(
        rank_findings((second,))
    )


def test_ranking_uses_reachability_before_severity() -> None:
    """Spec: HERMES-0017 / AC-11"""
    critical_unknown = _rankable(
        "critical-unknown",
        severity=CommonSeverity.CRITICAL,
        strength=EvidenceStrength.CONFIRMED,
    )
    high_reachable = _rankable(
        "high-reachable",
        severity=CommonSeverity.HIGH,
        strength=EvidenceStrength.CONFIRMED,
        reachability=ProductionReachability.CONFIRMED,
    )
    assert rank_findings((critical_unknown, high_reachable)).top_finding == high_reachable


def test_ranking_matrix_orders_strength_severity_source_and_id() -> None:
    """Spec: HERMES-0017 / AC-11, AC-12"""
    values = (
        _rankable("b", source="z", severity=CommonSeverity.MEDIUM),
        _rankable("a", source="z", severity=CommonSeverity.MEDIUM),
        _rankable("z", source="a", severity=CommonSeverity.MEDIUM),
        _rankable("partial", severity=CommonSeverity.HIGH),
        _rankable(
            "confirmed-medium",
            severity=CommonSeverity.MEDIUM,
            strength=EvidenceStrength.CONFIRMED,
        ),
        _rankable(
            "confirmed-high",
            severity=CommonSeverity.HIGH,
            strength=EvidenceStrength.CONFIRMED,
        ),
    )
    ordered = rank_findings(values).ordered_findings
    assert tuple(item.finding_id for item in ordered) == (
        "confirmed-high",
        "confirmed-medium",
        "partial",
        "z",
        "a",
        "b",
    )


def test_all_input_permutations_produce_identical_report() -> None:
    """Spec: HERMES-0017 / AC-13"""
    values = (
        _rankable("c"),
        _rankable("a", strength=EvidenceStrength.CONFIRMED),
        _rankable("b", reachability=ProductionReachability.CONFIRMED),
    )
    serialized = {
        ranked_finding_json(rank_findings(tuple(items)))
        for items in permutations(values)
    }
    assert len(serialized) == 1


def test_domain_payload_is_opaque_to_ranking() -> None:
    """Spec: HERMES-0017 / AC-14"""
    anchor = _rankable("anchor", strength=EvidenceStrength.CONFIRMED)
    first = _rankable("same", payload={"producer": "alpha", "suggestion": "one"})
    second = _rankable("same", payload={"producer": "omega", "suggestion": "two"})
    assert tuple(item.finding_id for item in rank_findings((anchor, first)).ordered_findings) == tuple(
        item.finding_id for item in rank_findings((anchor, second)).ordered_findings
    )


@pytest.mark.parametrize("path", ["C:/secret.py", "/etc/passwd", "../escape.py"])
def test_evidence_ref_rejects_unsafe_path(path: str) -> None:
    """Spec: HERMES-0017 / AC-15"""
    with pytest.raises(SkillExecutionError) as caught:
        EvidenceRef(path, 1, 1)
    assert caught.value.code == "FINDING_NORMALIZATION_INVALID"


def test_evidence_refs_with_optional_columns_have_canonical_order() -> None:
    """Spec: HERMES-0017 / AC-10, AC-15"""
    finding = RankableFinding(
        1,
        "mixed-references",
        "test-auditor",
        "References have a total deterministic order.",
        CommonSeverity.LOW,
        EvidenceStrength.PARTIAL,
        ProductionReachability.UNKNOWN,
        (
            EvidenceRef("src/example.py", 1, 1, 3, 5),
            EvidenceRef("src/example.py", 1, 1),
        ),
        "opaque",
    )
    assert finding.evidence_refs == (
        EvidenceRef("src/example.py", 1, 1),
        EvidenceRef("src/example.py", 1, 1, 3, 5),
    )


def test_normalization_and_ranking_do_not_read_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0017 / AC-16"""
    from hermes_ops.skills import controlled_reader

    monkeypatch.setattr(
        controlled_reader,
        "read_source_documents",
        lambda *args, **kwargs: pytest.fail("ranking attempted source reading"),
    )
    finding = normalize_code_audit_finding(_code_finding())
    assert rank_findings((finding,)).top_finding == finding


def test_ranked_json_is_valid_and_payload_is_frozen() -> None:
    """Spec: HERMES-0017 / AC-10, AC-14"""
    payload = {"nested": [1, 2]}
    finding = _rankable("frozen", payload=payload)
    payload["nested"].append(3)
    serialized = ranked_finding_json(rank_findings((finding,)))
    assert json.loads(serialized)["ordered_findings"][0]["domain_payload"] == {
        "nested": [1, 2]
    }


def test_shared_contract_is_exported_without_registering_a_skill() -> None:
    """Spec: HERMES-0017 / AC-18"""
    from hermes_ops import skills

    assert skills.RankableFinding is RankableFinding
    assert skills.rank_findings is rank_findings


def _persistence_report(classification: PersistenceContractClassification) -> PersistenceContractReport:
    findings = () if classification in {
        PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED,
        PersistenceContractClassification.INSUFFICIENT_EVIDENCE,
    } else (PersistenceContractFinding(
        PersistenceContractFindingKind.TARGET_TABLE_MISMATCH,
        "Observed table differs from the target.", PersistenceContractSeverity.MEDIUM,
        ("src/store.py:7",), "records", "id", "archive", "id",
    ),)
    return PersistenceContractReport(
        1, classification, "create", "consume", PersistenceContractDialect.SQLITE_DBAPI,
        "records", "id", ("create", "execute", "consume"),
        PersistenceContractReachability.CONFIRMED, (), (), (), (), findings,
        ("src/store.py:7",), ("TRANSACTION_SEMANTICS_UNKNOWN",), (),
    )


def test_persistence_normalizer_maps_strength_severity_and_reachability() -> None:
    """Spec: HERMES-0021 / AC-26"""
    confirmed = normalize_persistence_contract_report(
        _persistence_report(PersistenceContractClassification.CONFIRMED_CONTRACT_MISMATCH)
    )[0]
    partial = normalize_persistence_contract_report(
        _persistence_report(PersistenceContractClassification.POTENTIAL_CONTRACT_MISMATCH)
    )[0]
    assert confirmed.source_skill == "persistence-contract-review"
    assert confirmed.evidence_strength is EvidenceStrength.CONFIRMED
    assert confirmed.severity is CommonSeverity.MEDIUM
    assert confirmed.production_reachability is ProductionReachability.CONFIRMED
    assert partial.evidence_strength is EvidenceStrength.PARTIAL
    assert partial.severity is CommonSeverity.LOW


@pytest.mark.parametrize("classification", [
    PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED,
    PersistenceContractClassification.INSUFFICIENT_EVIDENCE,
])
def test_non_actionable_persistence_reports_are_not_rankable(classification) -> None:
    """Spec: HERMES-0021 / AC-26"""
    assert normalize_persistence_contract_report(_persistence_report(classification)) == ()


def _state_report(
    classification: StateGuardEffectClassification,
    literal: object = "waiting",
) -> StateGuardEffectReport:
    findings = () if classification in {
        StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED,
        StateGuardEffectClassification.INSUFFICIENT_EVIDENCE,
    } else (
        StateGuardEffectFinding(
            StateGuardEffectFindingKind.STATE_EFFECT_COVERAGE_MISMATCH,
            "confirm",
            StateBindingRequest("state"),
            literal,
            "cancel",
            "The declared state is blocked.",
            StateGuardEffectSeverity.MEDIUM,
            ("src/flow.py:2", "src/flow.py:3"),
        ),
    )
    return StateGuardEffectReport(
        1,
        classification,
        "confirm",
        StateBindingRequest("state"),
        literal,
        "cancel",
        StateGuardEffectReachability.CONFIRMED,
        None,
        (),
        findings,
        ("src/flow.py:2", "src/flow.py:3"),
        (),
        (),
    )


def test_state_guard_effect_confirmed_normalization_is_deterministic() -> None:
    """Spec: HERMES-0025 / AC-26, AC-29."""
    reports = [
        normalize_state_guard_effect_report(
            _state_report(StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH)
        )
        for _ in range(2)
    ]
    assert reports[0] == reports[1]
    finding = reports[0][0]
    assert finding.source_skill == "state-guard-effect-review"
    assert finding.evidence_strength is EvidenceStrength.CONFIRMED
    assert finding.severity is CommonSeverity.MEDIUM
    assert finding.production_reachability is ProductionReachability.CONFIRMED
    assert finding.finding_id.startswith("sha256:")
    assert ranked_finding_json(rank_findings(reports[0])) == ranked_finding_json(rank_findings(reports[1]))


@pytest.mark.parametrize(
    "classification",
    [
        StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED,
        StateGuardEffectClassification.INSUFFICIENT_EVIDENCE,
    ],
)
def test_non_actionable_state_reports_are_not_rankable(classification) -> None:
    """Spec: HERMES-0025 / AC-29."""
    assert normalize_state_guard_effect_report(_state_report(classification)) == ()


def test_state_finding_identity_preserves_literal_type() -> None:
    """Spec: HERMES-0025 / AC-06, AC-26."""
    true_finding = normalize_state_guard_effect_report(
        _state_report(StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH, True)
    )[0]
    one_finding = normalize_state_guard_effect_report(
        _state_report(StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH, 1)
    )[0]
    assert true_finding.finding_id != one_finding.finding_id
