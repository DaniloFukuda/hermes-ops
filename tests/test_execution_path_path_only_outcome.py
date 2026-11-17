from pathlib import Path

from hermes_ops.skills.execution_path_models import ExecutionPathClassification
from hermes_ops.skills.controlled_reader import SourceDocument
from hermes_ops.skills.execution_path_review import (
    _definitions, _parse_documents, _producer_evidence, review_execution_path,
)


def test_unique_path_without_comparable_contract_has_path_only_outcome(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / AC-01 to AC-05, AC-09, AC-10, AC-23"""
    (tmp_path / "flow.py").write_text('''
def create_session(source):
    cursor = store(source)
    return int(cursor.lastrowid)
def update_session(session_id, value):
    write_update(session_id, value)
def orchestrate(source, value):
    session_id = create_session(source)
    update_session(session_id, value)
    return session_id
''', encoding="utf-8")
    report = review_execution_path(tmp_path, "create_session", "update_session")
    assert report.classification is ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT
    assert report.executable_path == ("create_session", "orchestrate", "update_session")
    assert report.findings == ()
    assert len(report.evidence_references) >= 2


def _write_and_review(tmp_path: Path, source: str):
    (tmp_path / "flow.py").write_text(source, encoding="utf-8")
    return review_execution_path(tmp_path, "create_session", "update_session")


def test_multiple_call_origins_are_preserved_without_domain(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / AC-06 to AC-10"""
    source = '''
def create_session(flag):
    if flag:
        return int(existing["id"])
    return int(cursor.lastrowid)
def update_session(session_id):
    use(session_id)
def orchestrate(flag):
    session_id = create_session(flag)
    update_session(session_id)
'''
    report = _write_and_review(tmp_path, source)
    document = SourceDocument("flow.py", source, len(source.encode()))
    definition = _definitions(_parse_documents((document,)))["create_session"][0]
    evidence = _producer_evidence(definition)
    assert report.classification is ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT
    assert evidence.domain is None and evidence.origin is not None
    assert evidence.origin.kind == "variants"
    assert evidence.origin.variant_expressions == (
        "int(cursor.lastrowid)", "int(existing['id'])",
    )
    assert len(evidence.origin.variant_evidence_refs) == 2


def test_consumer_truthy_with_unknown_producer_stays_insufficient(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / AC-13"""
    report = _write_and_review(tmp_path, '''
def create_session(source): return int(make_id(source))
def update_session(session_id):
    if not session_id: raise ValueError("missing")
def orchestrate(source):
    session_id = create_session(source)
    update_session(session_id)
''')
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert report.limitations == ("PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN",)


def test_opaque_consumer_guard_is_not_treated_as_no_contract(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / opaque precondition boundary"""
    report = _write_and_review(tmp_path, '''
def create_session(source): return int(make_id(source))
def update_session(session_id):
    if not custom_validator(session_id): raise ValueError("invalid")
def orchestrate(source): update_session(create_session(source))
''')
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert "CONSUMER_PRECONDITION_NOT_DISCOVERABLE" in report.limitations


def test_sql_use_does_not_become_python_precondition(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / AC-11, AC-12"""
    report = _write_and_review(tmp_path, '''
def create_session(source): return int(make_id(source))
def update_session(session_id, value):
    conn.execute("UPDATE sessions SET value=? WHERE id=?", (value, session_id))
def orchestrate(source, value):
    session_id = create_session(source)
    update_session(session_id, value)
''')
    assert report.classification is ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT
    assert "NO_COMPARABLE_CONSUMER_CONTRACT" in report.limitations


def test_path_only_result_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / AC-22"""
    source = '''
def create_session(source): return make_id(source)
def update_session(session_id): use(session_id)
def orchestrate(source): update_session(create_session(source))
'''
    assert _write_and_review(tmp_path, source) == _write_and_review(tmp_path, source)
