"""Contract tests for HERMES-0024 persistence mutation effects."""

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.controlled_reader import SourceDocument
from hermes_ops.skills.persistence_contract_models import (
    PersistenceContractClassification,
    PersistenceContractDialect,
    PersistenceContractFindingKind,
    PersistenceMutationReviewRequest,
)
from hermes_ops.skills.persistence_contract_review import review_persistence_mutation_documents
from hermes_ops.skills.finding_models import CommonSeverity, EvidenceStrength
from hermes_ops.skills.finding_ranking import normalize_persistence_contract_report


def test_aligned_generic_mutation_is_structurally_aligned() -> None:
    """Spec: HERMES-0024 / AC-01, AC-18, AC-19."""
    source = '''
def handle_cancel(entity):
    cancel_entity(entity["id"])

def cancel_entity(entity_id):
    conn.execute(
        "UPDATE sessions SET status='failed' WHERE id=?",
        (entity_id,),
    )
'''
    request = PersistenceMutationReviewRequest(
        "handle_cancel",
        PersistenceContractDialect.SQLITE_DBAPI,
        "sessions",
        "id",
        "status",
        "failed",
    )
    report = review_persistence_mutation_documents(
        (SourceDocument("flow.py", source, len(source.encode())),), request
    )
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert report.findings == ()
    assert report.executable_path == ("handle_cancel", "cancel_entity")
    assert report.production_reachability.value == "CONFIRMED"
    assert report.evidence_references


def test_with_block_is_traversed_without_changing_mutation_semantics() -> None:
    """Spec: HERMES-0024 / AC-07, AC-10."""
    report = _review('''
def handle_cancel(entity):
    with transaction() as conn:
        cancel_entity(conn, entity["id"])
def cancel_entity(conn, entity_id):
    conn.execute("UPDATE sessions SET status='failed' WHERE id=?", (entity_id,))
''')
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED


def test_non_mutating_helper_with_unsupported_binding_does_not_poison_proven_effect() -> None:
    """Spec: HERMES-0024 / AC-10, AC-16."""
    report = _review('''
def handle_cancel(entity):
    mutate(entity["id"])
def mutate(entity_id):
    conn.execute("UPDATE sessions SET status='failed' WHERE id=?", (entity_id,))
    render("done", unexpected=True)
def render(message):
    return message
''')
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED


def _review(source: str, **overrides: object):
    values = {
        "operation_symbol": "handle_cancel",
        "dialect": PersistenceContractDialect.SQLITE_DBAPI,
        "target_table": "sessions",
        "identity_column": "id",
        "expected_state_column": "status",
        "expected_state_value": "failed",
    }
    values.update(overrides)
    request = PersistenceMutationReviewRequest(**values)
    document = SourceDocument("flow.py", source, len(source.encode()))
    return review_persistence_mutation_documents((document,), request)


def test_wrong_table_is_confirmed_with_one_causal_finding() -> None:
    """Spec: HERMES-0024 / AC-02."""
    report = _review('''
def handle_cancel(entity, sender):
    cancel_legacy(sender)
def cancel_legacy(sender):
    conn.execute("UPDATE legacy_sessions SET status='failed' WHERE sender=?", (sender,))
''')
    assert report.classification is PersistenceContractClassification.CONFIRMED_CONTRACT_MISMATCH
    assert tuple(item.kind for item in report.findings) == (
        PersistenceContractFindingKind.MUTATION_TARGET_TABLE_MISMATCH,
    )
    normalized = normalize_persistence_contract_report(report)
    assert normalized[0].severity is CommonSeverity.MEDIUM
    assert normalized[0].evidence_strength is EvidenceStrength.CONFIRMED


def test_wrong_key_is_confirmed() -> None:
    """Spec: HERMES-0024 / AC-03."""
    report = _review('''
def handle_cancel(value): cancel_entity(value)
def cancel_entity(value):
    conn.execute("UPDATE sessions SET status='failed' WHERE external_id=?", (value,))
''')
    assert report.findings[0].kind is PersistenceContractFindingKind.MUTATION_TARGET_KEY_MISMATCH


def test_literal_state_mismatch_is_confirmed_and_extras_are_preserved() -> None:
    """Spec: HERMES-0024 / AC-04, AC-05."""
    report = _review('''
def handle_cancel(value): cancel_entity(value)
def cancel_entity(value):
    conn.execute(
        "UPDATE sessions SET updated_at=?, status='completed', reason='done' WHERE id=? AND status='open'",
        (now, value),
    )
''')
    assert report.findings[0].kind is PersistenceContractFindingKind.MUTATION_STATE_MISMATCH
    assert dict(report.mutation_intents[0].assignments)["reason"] == "done"


def test_state_is_not_inferred_from_misleading_names() -> None:
    """Spec: HERMES-0024 / AC-06, AC-12."""
    report = _review('''
def handle_cancel(value): cancel_bad(value)
def cancel_bad(value):
    conn.execute("UPDATE sessions SET status='completed' WHERE id=?", (value,))
''', expected_state_column=None, expected_state_value=None)
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED


def test_dynamic_sql_and_api_only_fail_closed() -> None:
    """Spec: HERMES-0024 / AC-07, AC-17."""
    dynamic = _review('''
def handle_cancel(value): cancel_entity(value)
def cancel_entity(value):
    query = build_query(value)
    conn.execute(query, (value,))
''')
    api = _review('''
def handle_cancel(value): external_api.cancel(value)
''')
    assert dynamic.classification is PersistenceContractClassification.INSUFFICIENT_EVIDENCE
    assert "DYNAMIC_SQL_UNSUPPORTED" in dynamic.limitations
    assert api.classification is PersistenceContractClassification.INSUFFICIENT_EVIDENCE


def test_unrelated_update_is_ignored() -> None:
    """Spec: HERMES-0024 / AC-08."""
    report = _review('''
def handle_cancel(value): external_api.cancel(value)
def unrelated(value):
    conn.execute("UPDATE legacy_sessions SET status='failed' WHERE sender=?", (value,))
''')
    assert report.classification is PersistenceContractClassification.INSUFFICIENT_EVIDENCE
    assert report.findings == () and report.mutation_intents == ()


def test_activation_guard_selects_only_its_branch() -> None:
    """Spec: HERMES-0024 / AC-08, AC-19."""
    report = _review('''
def handle_cancel(value, text):
    if other_command(text):
        mutate_wrong(value)
    if selected_command(text):
        mutate_right(value)
def mutate_wrong(value):
    conn.execute("UPDATE legacy SET status='failed' WHERE id=?", (value,))
def mutate_right(value):
    conn.execute("UPDATE sessions SET status='failed' WHERE id=?", (value,))
''', activation_guard_symbol="selected_command")
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert report.executable_path == ("handle_cancel", "mutate_right")


def test_qualified_call_and_sql_parameter_forwarding_are_supported() -> None:
    """Spec: HERMES-0024 / AC-13, AC-14."""
    report = _review('''
def handle_cancel(value): repository.cancel_entity(value)
def cancel_entity(value):
    sql = "UPDATE sessions SET status='failed', updated_at=? WHERE id=?"
    params = (now, value)
    return execute_update(sql, params)
def execute_update(sql, params):
    conn.execute(sql, params)
''')
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert report.executable_path == ("handle_cancel", "cancel_entity", "execute_update")


def test_mixed_paths_are_potential_and_equivalent_paths_are_confirmed() -> None:
    """Spec: HERMES-0024 / AC-10, AC-11."""
    mixed = _review('''
def handle_cancel(value, flag):
    if flag: mutate_right(value)
    else: mutate_wrong(value)
def mutate_right(value):
    conn.execute("UPDATE sessions SET status='failed' WHERE id=?", (value,))
def mutate_wrong(value):
    conn.execute("UPDATE legacy SET status='failed' WHERE id=?", (value,))
''')
    same_mismatch = _review('''
def handle_cancel(value, flag):
    if flag: first(value)
    else: second(value)
def first(value):
    conn.execute("UPDATE legacy SET status='failed' WHERE id=?", (value,))
def second(value):
    conn.execute("UPDATE legacy SET status='failed' WHERE id=?", (value,))
''')
    assert mixed.classification is PersistenceContractClassification.POTENTIAL_CONTRACT_MISMATCH
    assert same_mismatch.classification is PersistenceContractClassification.CONFIRMED_CONTRACT_MISMATCH


def test_same_key_with_wrong_semantic_origin_does_not_invent_identity_mismatch() -> None:
    """Spec: HERMES-0024 / AC-16."""
    report = _review('''
def handle_cancel(entity_id, sender): cancel_entity(sender)
def cancel_entity(value):
    conn.execute("UPDATE sessions SET status='failed' WHERE id=?", (value,))
''')
    assert report.classification is PersistenceContractClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert all("IDENTITY" not in item.kind.value for item in report.findings)


def test_invalid_request_fails_closed() -> None:
    """Spec: HERMES-0024 / request contract."""
    with pytest.raises(SkillExecutionError):
        PersistenceMutationReviewRequest(
            "bad.name", PersistenceContractDialect.SQLITE_DBAPI, "sessions", "id"
        )
    with pytest.raises(SkillExecutionError):
        PersistenceMutationReviewRequest(
            "operation", PersistenceContractDialect.SQLITE_DBAPI,
            "sessions", "id", "status", None,
        )
