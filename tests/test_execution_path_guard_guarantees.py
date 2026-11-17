from __future__ import annotations

from pathlib import Path

from hermes_ops.skills.execution_path_models import ExecutionPathClassification
from hermes_ops.skills.execution_path_review import review_execution_path


def _write(root: Path, source: str) -> None:
    (root / "flow.py").write_text(source, encoding="utf-8")


def test_truthiness_guard_establishes_success_path_guarantee(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-01, AC-02, AC-06, AC-24"""
    _write(tmp_path, '''
def producer(value):
    if not value:
        return {"success": False}
    return {"success": True, "value": value}

def consumer(value):
    if not value:
        raise ValueError("missing")

def execute(runtime_value):
    result = producer(runtime_value)
    consumer(result["value"])
''')
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.NO_MISMATCH
    assert report.limitations == ()


def _review(tmp_path: Path, producer_body: str, consumer_guard: str = "if not value: raise ValueError('missing')"):
    _write(tmp_path, f'''
def producer(value):
{producer_body}
def consumer(value):
    {consumer_guard}
def execute(runtime_value):
    result = producer(runtime_value)
    consumer(result["value"])
''')
    return review_execution_path(tmp_path, "producer", "consumer")


def test_equality_guard_matches_and_mismatches_literal_requirements(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-03 to AC-05"""
    matching = _review(
        tmp_path,
        "    if value != 'confirmed':\n        return {'success': False}\n    return {'success': True, 'value': value}\n",
        "if value != 'confirmed': raise ValueError('wrong')",
    )
    assert matching.classification is ExecutionPathClassification.NO_MISMATCH
    mismatching = _review(
        tmp_path,
        "    if value != 'prepared':\n        return {'success': False}\n    return {'success': True, 'value': value}\n",
        "if value != 'confirmed': raise ValueError('wrong')",
    )
    assert mismatching.classification is ExecutionPathClassification.CONFIRMED_MISMATCH
    assert len(mismatching.findings[0].evidence_references) >= 4


def test_simple_alias_preserves_guarded_generation(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-08"""
    report = _review(tmp_path, "    if not value:\n        return {'success': False}\n    final_value = value\n    return {'success': True, 'value': final_value}\n")
    assert report.classification is ExecutionPathClassification.NO_MISMATCH


def test_redefinition_and_transform_invalidate_old_guard(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-09, AC-10, AC-18"""
    redefined = _review(tmp_path, "    if not value:\n        return {'success': False}\n    value = other()\n    return {'success': True, 'value': value}\n")
    transformed = _review(tmp_path, "    if not value:\n        return {'success': False}\n    normalized = value.strip()\n    return {'success': True, 'value': normalized}\n")
    assert redefined.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert transformed.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE


def test_guarded_str_strip_result_has_its_own_truthy_generation(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-01, AC-10"""
    report = _review(tmp_path, "    normalized = str(value).strip()\n    if not normalized:\n        return {'success': False}\n    return {'success': True, 'value': normalized}\n")
    assert report.classification is ExecutionPathClassification.NO_MISMATCH


def test_guard_on_other_binding_does_not_constrain_returned_value(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-11, AC-18"""
    _write(tmp_path, '''
def producer(value, other):
    if not other:
        return {"success": False}
    return {"success": True, "value": value}
def consumer(value):
    if not value: raise ValueError("missing")
def execute(runtime_value, runtime_other):
    consumer(producer(runtime_value, runtime_other)["value"])
''')
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE


def test_opaque_predicate_is_diagnostic_only(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-12, AC-13"""
    report = _review(tmp_path, "    if not custom_validator(value):\n        return {'success': False}\n    return {'success': True, 'value': value}\n")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.limitations == ("PRODUCER_GUARD_FACT_DISCOVERED_NOT_COMPARABLE",)


def test_truthy_guarantee_cannot_satisfy_literal_requirement(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / comparison matrix"""
    report = _review(
        tmp_path,
        "    if not value:\n        return {'success': False}\n    return {'success': True, 'value': value}\n",
        "if value != 'confirmed': raise ValueError('wrong')",
    )
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.limitations == ("PRODUCER_GUARANTEE_NOT_COMPARABLE",)


def test_multiple_atomic_guards_can_share_one_generation(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-01, AC-03"""
    report = _review(
        tmp_path,
        "    if not value:\n        return {'success': False}\n    if value != 'confirmed':\n        return {'success': False}\n    return {'success': True, 'value': value}\n",
        "if value != 'confirmed': raise ValueError('wrong')",
    )
    assert report.classification is ExecutionPathClassification.NO_MISMATCH


def test_success_return_that_avoids_guard_prevents_common_guarantee(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-07, AC-14, AC-15"""
    _write(tmp_path, '''
def producer(value, choice):
    if choice:
        return {"success": True, "value": value}
    if not value:
        return {"success": False}
    return {"success": True, "value": value}
def consumer(value):
    if not value: raise ValueError("missing")
def execute(runtime_value, choice):
    consumer(producer(runtime_value, choice)["value"])
''')
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE


def test_nested_guard_loop_and_guard_after_return_fail_closed(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-16, AC-17"""
    bodies = (
        "    if flag():\n        if not value:\n            return {'success': False}\n    return {'success': True, 'value': value}\n",
        "    for item in items():\n        pass\n    if not value:\n        return {'success': False}\n    return {'success': True, 'value': value}\n",
        "    if branch():\n        return {'success': True, 'value': value}\n    if not value:\n        return {'success': False}\n    return {'success': True, 'value': value}\n",
    )
    for body in bodies:
        assert _review(tmp_path, body).classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE


def test_guard_analysis_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0022 / AC-23"""
    body = "    if not value:\n        return {'success': False}\n    return {'success': True, 'value': value}\n"
    assert _review(tmp_path, body) == _review(tmp_path, body)
