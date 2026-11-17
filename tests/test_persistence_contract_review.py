from __future__ import annotations

from pathlib import Path

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.controlled_reader import SourceDocument
from hermes_ops.skills.persistence_contract_models import (
    PersistenceContractClassification,
    PersistenceContractDialect,
    PersistenceContractFindingKind,
    PersistenceContractReachability,
    PersistenceContractReviewRequest,
)
from hermes_ops.skills.persistence_contract_review import review_persistence_contract_documents


def _document(source: str) -> SourceDocument:
    return SourceDocument("flow.py", source, len(source.encode("utf-8")))


def test_insert_identity_select_contract_is_structurally_aligned() -> None:
    """Spec: HERMES-0021 / AC-01 to AC-03, AC-05, AC-06, AC-08 to AC-10, AC-13"""
    source = '''
def create(conn):
    cursor = conn.execute(
        "INSERT INTO records (state) VALUES (?)",
        ("prepared",),
    )
    record_id = cursor.lastrowid
    return record_id

def consume(conn, record_id):
    row = conn.execute(
        "SELECT state FROM records WHERE id = ?",
        (record_id,),
    ).fetchone()
    if not row:
        return False
    return True

def execute(conn):
    record_id = create(conn)
    return consume(conn, record_id)
'''
    request = PersistenceContractReviewRequest(
        "create",
        "consume",
        PersistenceContractDialect.SQLITE_DBAPI,
        "records",
        "id",
    )

    report = review_persistence_contract_documents((_document(source),), request)

    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert report.write_intents[0].table == "records"
    assert report.write_intents[0].columns == ("state",)
    assert report.write_intents[0].bindings == ("'prepared'",)
    assert report.identity_bindings[0].cursor_symbol == "cursor"
    assert report.identity_bindings[0].write_table == "records"
    assert report.read_requirements[0].predicate_column == "id"
    assert report.read_requirements[0].predicate_value_identity == "record_id"
    assert report.read_requirements[0].success_guard is True
    assert report.executable_path == ("create", "execute", "consume")
    assert report.production_reachability is PersistenceContractReachability.CONFIRMED
    assert "TRANSACTION_SEMANTICS_UNKNOWN" in report.limitations


def _review(source: str, *, table: str = "records", key: str = "id", expected_state: str | None = None):
    return review_persistence_contract_documents(
        (_document(source),),
        PersistenceContractReviewRequest(
            "create", "consume", PersistenceContractDialect.SQLITE_DBAPI,
            table, key, expected_state,
        ),
    )


def test_explicit_table_and_key_mismatches_are_confirmed() -> None:
    """Spec: HERMES-0021 / AC-14, AC-15, AC-29"""
    source = '''
def create(conn):
    cursor = conn.execute("INSERT INTO archive (state) VALUES (?)", ("ready",))
    item_id = cursor.lastrowid
    return item_id
def consume(conn, item_id):
    row = conn.execute("SELECT state FROM other WHERE uuid = ?", (item_id,)).fetchone()
    return bool(row)
'''
    report = _review(source)
    assert report.classification is PersistenceContractClassification.CONFIRMED_CONTRACT_MISMATCH
    assert {item.kind for item in report.findings} == {
        PersistenceContractFindingKind.TARGET_TABLE_MISMATCH,
        PersistenceContractFindingKind.TARGET_KEY_MISMATCH,
    }


@pytest.mark.parametrize(
    ("expression", "limitation"),
    [
        ("query", "DYNAMIC_SQL_UNSUPPORTED"),
        ('f"SELECT state FROM records WHERE id = {record_id}"', "DYNAMIC_SQL_UNSUPPORTED"),
        ('"SELECT state " + "FROM records WHERE id = ?"', "DYNAMIC_SQL_UNSUPPORTED"),
        ('"SELECT state FROM records WHERE id = ? OR state = ?"', "SQL_SHAPE_UNSUPPORTED"),
    ],
)
def test_dynamic_and_complex_sql_fail_closed(expression: str, limitation: str) -> None:
    """Spec: HERMES-0021 / AC-04, AC-30"""
    prefix = "query = 'SELECT state FROM records WHERE id = ?'\n    " if expression == "query" else ""
    source = f'''
def create(conn):
    cursor = conn.execute("INSERT INTO records (state) VALUES (?)", ("ready",))
    record_id = cursor.lastrowid
    return record_id
def consume(conn, record_id):
    {prefix}row = conn.execute({expression}, (record_id,)).fetchone()
    return bool(row)
'''
    report = _review(source)
    assert report.classification is PersistenceContractClassification.INSUFFICIENT_EVIDENCE
    assert report.findings == () and limitation in report.limitations


def test_two_inserts_keep_cursor_and_identity_origins_separate() -> None:
    """Spec: HERMES-0021 / AC-05, AC-16, AC-17"""
    source = '''
def create(conn):
    first = conn.execute("INSERT INTO ignored (state) VALUES (?)", ("old",))
    ignored_id = first.lastrowid
    second = conn.execute("INSERT INTO records (state) VALUES (?)", ("ready",))
    record_id = second.lastrowid
    return record_id
def consume(conn, record_id):
    row = conn.execute("SELECT state FROM records WHERE id = ?", (record_id,)).fetchone()
    return bool(row)
'''
    report = _review(source)
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert [(item.cursor_symbol, item.write_table) for item in report.identity_bindings] == [
        ("first", "ignored"), ("second", "records")
    ]


def test_constant_read_identity_is_insufficient_not_a_confirmed_mismatch() -> None:
    """Spec: HERMES-0021 / AC-18"""
    source = '''
def create(conn):
    cursor = conn.execute("INSERT INTO records (state) VALUES (?)", ("ready",))
    record_id = cursor.lastrowid
    return record_id
def consume(conn, record_id):
    row = conn.execute("SELECT state FROM records WHERE id = ?", (7,)).fetchone()
    return bool(row)
'''
    report = _review(source)
    assert report.classification is PersistenceContractClassification.INSUFFICIENT_EVIDENCE
    assert report.findings == () and "READ_IDENTITY_ORIGIN_UNKNOWN" in report.limitations


def test_update_is_an_intent_and_expected_state_can_mismatch() -> None:
    """Spec: HERMES-0021 / AC-11, AC-12, AC-21"""
    source = '''
def create(conn):
    cursor = conn.execute("INSERT INTO records (state) VALUES (?)", ("ready",))
    record_id = cursor.lastrowid
    conn.execute("UPDATE records SET state = ? WHERE id = ?", ("failed", record_id))
    return record_id
def consume(conn, record_id):
    row = conn.execute("SELECT state FROM records WHERE id = ?", (record_id,)).fetchone()
    return bool(row)
'''
    report = _review(source, expected_state="ready")
    assert report.state_transition_intents[0].value == "'failed'"
    assert not hasattr(report, "persistence_confirmed")
    assert report.findings[0].kind is PersistenceContractFindingKind.STATE_INTENT_MISMATCH
    assert "TRANSACTION_SEMANTICS_UNKNOWN" in report.limitations


def test_no_local_caller_preserves_structural_alignment_with_unknown_reachability() -> None:
    """Spec: HERMES-0021 / AC-19, AC-20"""
    source = '''
def create(conn):
    cursor = conn.execute("INSERT INTO records (state) VALUES (?)", ("ready",))
    record_id = cursor.lastrowid
    return record_id
def consume(conn, record_id):
    row = conn.execute("SELECT state FROM records WHERE id = ?", (record_id,)).fetchone()
    return bool(row)
def cli():
    print(create(open_connection()))
'''
    report = _review(source)
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert report.executable_path == ()
    assert report.production_reachability is PersistenceContractReachability.UNKNOWN


def test_invalid_dialect_fails_at_request_boundary() -> None:
    """Spec: HERMES-0021 / AC-07"""
    with pytest.raises(SkillExecutionError) as caught:
        PersistenceContractReviewRequest("create", "consume", "postgres", "records", "id")  # type: ignore[arg-type]
    assert caught.value.code == "PERSISTENCE_CONTRACT_INVALID_REQUEST"


def test_pure_core_is_deterministic_and_does_not_read_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0021 / AC-23 to AC-25"""
    source = '''
def create(conn):
    cursor = conn.execute("INSERT INTO records (state) VALUES (?)", ("ready",))
    record_id = cursor.lastrowid
    return record_id
def consume(conn, record_id):
    return conn.execute("SELECT state FROM records WHERE id = ?", (record_id,)).fetchone()
'''
    from hermes_ops.skills import controlled_reader
    monkeypatch.setattr(controlled_reader, "read_source_documents", lambda *a, **k: pytest.fail("filesystem read"))
    first, second = _review(source), _review(source)
    assert first == second
    assert all(not reference.startswith(("/", "C:")) for reference in first.evidence_references)
