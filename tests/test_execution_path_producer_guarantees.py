from __future__ import annotations

from pathlib import Path

from hermes_ops.skills.execution_path_models import ExecutionPathClassification
from hermes_ops.skills.execution_path_review import review_execution_path


def _write(root: Path, source: str) -> None:
    (root / "flow.py").write_text(source, encoding="utf-8")


def test_mapping_literal_alias_matches_consumer_requirement(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-01 to AC-03, AC-13"""
    _write(
        tmp_path,
        '''
def producer():
    state = "confirmed"
    return {"state": state}

def consumer(state):
    if state != "confirmed":
        raise ValueError("wrong state")

def execute():
    result = producer()
    consumer(result["state"])
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert report.classification is ExecutionPathClassification.NO_MISMATCH
    assert report.executable_path == ("producer", "execute", "consumer")
    assert report.limitations == ()


def test_mapping_literal_mismatch_preserves_finding(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-01, AC-03, AC-14"""
    _write(
        tmp_path,
        '''
def producer(): return {"state": "prepared"}
def consumer(state):
    if state != "confirmed": raise ValueError("wrong state")
def execute():
    result = producer()
    consumer(result["state"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.CONFIRMED_MISMATCH
    finding = report.findings[0]
    assert finding.producer_symbol == "producer"
    assert finding.consumer_symbol == "consumer"
    assert finding.executable_path == ("producer", "execute", "consumer")
    assert len(finding.evidence_references) == 3


def test_mapping_parameter_remains_caller_controlled(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-04"""
    _write(
        tmp_path,
        '''
def producer(state): return {"state": state}
def consumer(state):
    if state != "confirmed": raise ValueError("wrong state")
def execute(value):
    result = producer(value)
    consumer(result["state"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.CONFIRMED_MISMATCH
    assert "caller-controlled" in report.findings[0].produced_value


def test_opaque_helper_origin_has_distinct_diagnostic(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-05 to AC-08"""
    _write(
        tmp_path,
        '''
def producer(): return {"item_id": create_id()}
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def execute():
    result = producer()
    consumer(result["item_id"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.executable_path == ("producer", "execute", "consumer")
    assert report.limitations == ("PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN",)


def test_opaque_helper_through_local_alias_stays_opaque(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-05 to AC-08"""
    _write(
        tmp_path,
        '''
def producer():
    item_id = create_id()
    alias = item_id
    return {"item_id": alias}
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def execute(): consumer(producer()["item_id"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.limitations == ("PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN",)


def test_explicit_failure_return_does_not_contaminate_success_contract(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-09, AC-10"""
    _write(
        tmp_path,
        '''
def producer(invalid):
    if invalid:
        return {"success": False, "error": "invalid"}
    state = "confirmed"
    return {"success": True, "state": state}
def consumer(state):
    if state != "confirmed": raise ValueError("wrong state")
def execute(flag):
    result = producer(flag)
    consumer(result["state"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.NO_MISMATCH
    assert report.limitations == ()


def test_compatible_success_variants_establish_one_domain(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-09"""
    _write(
        tmp_path,
        '''
def producer(choice):
    if choice:
        return {"success": True, "state": "confirmed"}
    return {"success": True, "state": "confirmed"}
def consumer(state):
    if state != "confirmed": raise ValueError("wrong state")
def execute(choice): consumer(producer(choice)["state"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.NO_MISMATCH


def test_incompatible_success_variants_remain_insufficient(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-11"""
    _write(
        tmp_path,
        '''
def producer(choice):
    if choice:
        return {"success": True, "state": "confirmed"}
    return {"success": True, "state": "prepared"}
def consumer(state):
    if state != "confirmed": raise ValueError("wrong state")
def execute(choice): consumer(producer(choice)["state"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.limitations == ("PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN",)


def test_success_variant_without_field_has_no_guarantee(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-12"""
    _write(
        tmp_path,
        '''
def producer(choice):
    if choice:
        return {"success": True, "state": "confirmed"}
    return {"success": True}
def consumer(state):
    if state != "confirmed": raise ValueError("wrong state")
def execute(choice): consumer(producer(choice)["state"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.limitations == ("PRODUCER_GUARANTEE_NOT_DISCOVERABLE",)


def test_lastrowid_and_sql_do_not_create_persistence_domain(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-15, AC-16"""
    _write(
        tmp_path,
        '''
def producer(conn):
    cursor = conn.execute("INSERT INTO records(value) VALUES ('x')")
    item_id = cursor.lastrowid
    return {"item_id": item_id}
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def execute(conn): consumer(producer(conn)["item_id"])
''',
    )
    report = review_execution_path(tmp_path, "producer", "consumer")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.limitations == ("PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN",)


def test_producer_evidence_result_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0020 / AC-20"""
    _write(
        tmp_path,
        '''
def producer(): return {"item_id": create_id()}
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def execute(): consumer(producer()["item_id"])
''',
    )
    first = review_execution_path(tmp_path, "producer", "consumer")
    second = review_execution_path(tmp_path, "producer", "consumer")
    assert first == second
