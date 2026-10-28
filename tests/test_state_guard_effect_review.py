"""Contract tests for HERMES-0025 state guard effect coverage."""

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.controlled_reader import SourceDocument
from hermes_ops.skills.state_guard_effect_models import (
    StateBindingRequest,
    StateGuardEffectClassification,
    StateGuardEffectReachability,
    StateGuardEffectReviewRequest,
)
from hermes_ops.skills.state_guard_effect_review import review_state_guard_effect_documents


def _document(text: str) -> SourceDocument:
    return SourceDocument("fixture.py", text, len(text.encode("utf-8")))


def _review(
    text: str,
    literal: object = "ready",
    *,
    source: str = "state",
    field: str | None = None,
    effect: str = "cancel",
):
    return review_state_guard_effect_documents(
        (_document(text),),
        StateGuardEffectReviewRequest(
            "confirm", StateBindingRequest(source, field), literal, effect
        ),
    )


def test_literal_membership_can_reach_expected_effect() -> None:
    """Spec: HERMES-0025 / AC-01, AC-07."""
    document = _document(
        '''
def confirm(state):
    if state not in {"new", "ready"}:
        return False
    cancel()
    return True
'''
    )
    request = StateGuardEffectReviewRequest(
        operation_symbol="confirm",
        state_binding=StateBindingRequest(source_parameter="state"),
        input_state_literal="ready",
        expected_effect_symbol="cancel",
    )

    report = review_state_guard_effect_documents((document,), request)

    assert report.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert report.binding_fact is not None
    assert report.binding_fact.source_parameter == "state"
    assert report.binding_fact.field is None


def test_literal_membership_can_be_proven_blocked() -> None:
    """Spec: HERMES-0025 / AC-02."""
    document = _document(
        '''
def confirm(state):
    if state not in {"new", "ready"}:
        return False
    cancel()
    return True
'''
    )
    request = StateGuardEffectReviewRequest(
        operation_symbol="confirm",
        state_binding=StateBindingRequest(source_parameter="state"),
        input_state_literal="waiting",
        expected_effect_symbol="cancel",
    )

    report = review_state_guard_effect_documents((document,), request)

    assert report.classification is StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH
    assert len(report.findings) == 1
    assert report.findings[0].kind.value == "STATE_EFFECT_COVERAGE_MISMATCH"


@pytest.mark.parametrize(
    ("operator", "literal", "classification"),
    [
        ('== "ready"', "ready", StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED),
        ('== "ready"', "waiting", StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH),
        ('!= "ready"', "ready", StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH),
        ('!= "ready"', "waiting", StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED),
    ],
)
def test_equality_and_inequality(operator, literal, classification) -> None:
    """Spec: HERMES-0025 / AC-03, AC-04."""
    report = _review(f'def confirm(state):\n    if state {operator}:\n        cancel()\n    else:\n        return False\n', literal)
    assert report.classification is classification


@pytest.mark.parametrize("collection", ['{"ready", "new"}', '("ready", "new")', '["ready", "new"]'])
def test_literal_collection_shapes(collection: str) -> None:
    """Spec: HERMES-0025 / AC-05."""
    report = _review(f'def confirm(state):\n    if state in {collection}:\n        cancel()\n')
    assert report.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED


@pytest.mark.parametrize(
    ("literal_source", "request_literal", "accepted"),
    [("None", None, True), ("True", True, True), ("1", 1, True), ("1", True, False)],
)
def test_literal_types_are_preserved(literal_source, request_literal, accepted) -> None:
    """Spec: HERMES-0025 / AC-06."""
    report = _review(
        f'def confirm(state):\n    if state == {literal_source}:\n        cancel()\n    else:\n        return False\n',
        request_literal,
    )
    expected = (
        StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED
        if accepted else StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH
    )
    assert report.classification is expected


@pytest.mark.parametrize("access", ['batch["status"]', 'batch.get("status")'])
def test_mapping_field_and_alias_are_resolved(access: str) -> None:
    """Spec: HERMES-0025 / AC-08, AC-09, AC-10."""
    report = _review(
        f'def confirm(batch):\n    status = {access}\n    current = status\n    if current != "ready":\n        return False\n    cancel()\n',
        source="batch",
        field="status",
    )
    assert report.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED


@pytest.mark.parametrize("replacement", ["other()", "normalize(state)"])
def test_redefinition_and_transform_fail_closed(replacement: str) -> None:
    """Spec: HERMES-0025 / AC-11, AC-12."""
    report = _review(
        f'def confirm(state):\n    if state != "ready":\n        return False\n    state = {replacement}\n    cancel()\n'
    )
    assert report.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE
    assert report.findings == ()


def test_wrong_binding_is_not_used_as_state_evidence() -> None:
    """Spec: HERMES-0025 / AC-13."""
    report = _review('def confirm(state, other_state):\n    if other_state != "ready":\n        return False\n    cancel()\n')
    assert report.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE
    assert "STATE_GUARD_WRONG_BINDING" in report.limitations


@pytest.mark.parametrize(
    ("body", "diagnostic"),
    [
        ('allowed = load_allowed()\n    if state not in allowed:\n        return False\n    cancel()', "STATE_GUARD_COLLECTION_DYNAMIC"),
        ('if not can_cancel(state):\n        return False\n    cancel()', "STATE_GUARD_HELPER_OPAQUE"),
        ('if state == "ready" and enabled:\n        cancel()', "STATE_GUARD_BOOLEAN_COMPOSITION_UNSUPPORTED"),
    ],
)
def test_unsupported_guards_fail_closed(body: str, diagnostic: str) -> None:
    """Spec: HERMES-0025 / AC-14–AC-16."""
    report = _review(f"def confirm(state):\n    {body}\n")
    assert report.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE
    assert diagnostic in report.limitations and report.findings == ()


def test_nested_guard_is_supported() -> None:
    """Spec: HERMES-0025 / AC-17."""
    report = _review('def confirm(state):\n    if state == "ready":\n        if state in {"ready"}:\n            cancel()\n    else:\n        return False\n')
    assert report.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED


def test_alternate_independent_path_is_existentially_aligned() -> None:
    """Spec: HERMES-0025 / AC-18."""
    report = _review('def confirm(state, mode):\n    if mode:\n        if state != "ready":\n            return False\n    else:\n        cancel()\n', "waiting")
    assert report.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED


def test_rejected_plus_unknown_is_insufficient() -> None:
    """Spec: HERMES-0025 / AC-19."""
    report = _review('def confirm(state, mode):\n    if mode:\n        if state != "ready":\n            return False\n    else:\n        while pending():\n            pass\n        cancel()\n', "waiting")
    assert report.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE


def test_accepted_plus_unknown_is_aligned() -> None:
    """Spec: HERMES-0025 / AC-20."""
    report = _review('def confirm(state, mode):\n    if mode:\n        cancel()\n    else:\n        while pending():\n            pass\n', "waiting")
    assert report.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED


def test_multiple_rejected_paths_make_one_finding() -> None:
    """Spec: HERMES-0025 / AC-21."""
    report = _review('def confirm(state, mode):\n    if mode:\n        return False\n    else:\n        raise ValueError()\n    cancel()\n')
    assert report.classification is StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH
    assert len(report.findings) == 1


def test_absent_effect_is_insufficient() -> None:
    """Spec: HERMES-0025 / AC-22."""
    report = _review('def confirm(state):\n    return False\n')
    assert report.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE
    assert "EXPECTED_EFFECT_NOT_FOUND" in report.limitations


def test_effect_after_terminal_is_confirmed_mismatch() -> None:
    """Spec: HERMES-0025 / AC-23."""
    report = _review('def confirm(state):\n    return False\n    cancel()\n')
    assert report.classification is StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH
    assert report.reachability is StateGuardEffectReachability.CONFIRMED


def test_expected_effect_can_be_the_rhs_of_an_assignment() -> None:
    """Spec: HERMES-0025 / AC-01 generic call-expression placement."""
    report = _review(
        'def confirm(state):\n'
        '    if state != "ready":\n'
        '        return False\n'
        '    result = cancel()\n'
        '    return result\n'
    )
    assert report.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED


@pytest.mark.parametrize(
    "dynamic_call",
    ["callback()", 'getattr(service, name)()', 'dispatch[key]()'],
)
def test_dynamic_call_in_effect_position_is_distinct_from_absent_effect(dynamic_call: str) -> None:
    """Spec: HERMES-0025 / AC-24."""
    report = _review(
        'def confirm(state, callback):\n'
        '    if state != "ready":\n'
        '        return False\n'
        f'    {dynamic_call}\n'
    )
    assert report.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE
    assert "EXPECTED_EFFECT_CALL_DYNAMIC" in report.limitations
    assert "EXPECTED_EFFECT_NOT_FOUND" not in report.limitations
    assert report.findings == ()


def test_production_lens_has_no_consumer_specific_rules_or_persistence_dependency() -> None:
    """Spec: HERMES-0025 / AC-31, AC-35."""
    production_files = (
        Path("src/hermes_ops/skills/state_guard_effect_models.py"),
        Path("src/hermes_ops/skills/state_guard_effect_review.py"),
    )
    forbidden = (
        "awaiting_client_type",
        "handle_confirm_cancellation",
        "cancel_batch",
        "012fd775",
        "3e13126",
        "lucreagro",
        "lucre-hist-batch-cancel-missing-state-coverage",
        "MutationIntentFact",
        "PersistenceContractReport",
        "persistence_contract_models",
        "persistence_contract_review",
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in production_files).lower()
    assert all(item.lower() not in source for item in forbidden)


@pytest.mark.parametrize("construct", ["for item in items:\n        pass", "try:\n        work()\n    except Exception:\n        pass", "match state:\n        case _:\n            pass"])
def test_unsupported_control_flow_is_insufficient(construct: str) -> None:
    """Spec: HERMES-0025 / AC-25."""
    report = _review(f"def confirm(state):\n    {construct}\n    cancel()\n")
    assert report.classification is StateGuardEffectClassification.INSUFFICIENT_EVIDENCE
    assert "STATE_CONTROL_FLOW_UNSUPPORTED" in report.limitations


def test_request_validation_is_closed_and_type_safe() -> None:
    with pytest.raises(SkillExecutionError):
        StateGuardEffectReviewRequest("bad.name", StateBindingRequest("state"), "ready", "cancel")
    with pytest.raises(SkillExecutionError):
        StateGuardEffectReviewRequest("confirm", StateBindingRequest("state"), 1.5, "cancel")


def test_report_is_deterministic() -> None:
    """Spec: HERMES-0025 / AC-26."""
    source = 'def confirm(state):\n    if state != "ready":\n        return False\n    cancel()\n'
    reports = [_review(source) for _ in range(2)]
    assert reports[0] == reports[1]
    assert json.dumps(asdict(reports[0]), sort_keys=True, default=str) == json.dumps(asdict(reports[1]), sort_keys=True, default=str)


def test_operation_and_source_must_be_resolvable() -> None:
    """Spec: HERMES-0025 / AC-27, AC-28."""
    missing = _review('def other(state):\n    cancel()\n')
    duplicate = _review('def confirm(state):\n    cancel()\ndef confirm(state):\n    cancel()\n')
    wrong_source = _review('def confirm(other):\n    cancel()\n')
    assert "STATE_OPERATION_NOT_UNIQUE" in missing.limitations
    assert "STATE_OPERATION_NOT_UNIQUE" in duplicate.limitations
    assert "STATE_SOURCE_PARAMETER_NOT_FOUND" in wrong_source.limitations
