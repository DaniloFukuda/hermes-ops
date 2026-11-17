"""Before/after characterization for the HERMES-0026 narrow extraction."""

import ast
from dataclasses import asdict
import json

import pytest

from hermes_ops.skills import execution_path_review, persistence_contract_review
from hermes_ops.skills import state_guard_effect_review
from hermes_ops.skills.controlled_reader import SourceDocument
from hermes_ops.skills.finding_ranking import (
    normalize_execution_path_report,
    normalize_persistence_contract_report,
    normalize_state_guard_effect_report,
    rank_findings,
    ranked_finding_json,
)
from hermes_ops.skills.persistence_contract_models import (
    PersistenceContractDialect,
    PersistenceContractReviewRequest,
)
from hermes_ops.skills.state_guard_effect_models import (
    StateBindingRequest,
    StateGuardEffectReviewRequest,
)


def _document(source: str) -> SourceDocument:
    return SourceDocument("nested/flow.py", source, len(source.encode("utf-8")))


def _legacy_terminal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _legacy_locator(path: str, node: ast.AST) -> str:
    return f"{path}:{getattr(node, 'lineno', 1)}"


def _serialized(report: object, normalized: tuple[object, ...]) -> tuple[str, str]:
    native = json.dumps(asdict(report), sort_keys=True, default=str)
    ranked = ranked_finding_json(rank_findings(normalized))
    return native, ranked


def test_execution_mismatch_is_byte_stable_against_legacy_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0026 / AC-04, AC-09, AC-12, AC-30."""
    documents = (_document('''
def producer(): return ""
def consumer(value):
    if not value: raise ValueError("missing")
def execute(): consumer(producer())
'''),)
    current = execution_path_review.review_execution_path_documents(
        documents, "producer", "consumer"
    )
    expected = _serialized(current, normalize_execution_path_report(current))

    monkeypatch.setattr(execution_path_review, "terminal_symbol", _legacy_terminal)
    monkeypatch.setattr(execution_path_review, "source_locator", _legacy_locator)
    legacy = execution_path_review.review_execution_path_documents(
        documents, "producer", "consumer"
    )

    assert _serialized(legacy, normalize_execution_path_report(legacy)) == expected


def test_persistence_mismatch_is_byte_stable_against_legacy_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0026 / AC-05, AC-10, AC-13, AC-30."""
    documents = (_document('''
def create(conn):
    cursor = conn.execute("INSERT INTO archive (state) VALUES (?)", ("ready",))
    return cursor.lastrowid
def consume(conn, item_id):
    return conn.execute("SELECT state FROM other WHERE uuid = ?", (item_id,)).fetchone()
def execute(conn):
    item_id = create(conn)
    return consume(conn, item_id)
'''),)
    request = PersistenceContractReviewRequest(
        "create", "consume", PersistenceContractDialect.SQLITE_DBAPI, "records", "id"
    )
    current = persistence_contract_review.review_persistence_contract_documents(
        documents, request
    )
    expected = _serialized(current, normalize_persistence_contract_report(current))

    monkeypatch.setattr(persistence_contract_review, "terminal_symbol", _legacy_terminal)
    monkeypatch.setattr(persistence_contract_review, "source_locator", _legacy_locator)
    legacy = persistence_contract_review.review_persistence_contract_documents(
        documents, request
    )

    assert _serialized(legacy, normalize_persistence_contract_report(legacy)) == expected


def test_state_mismatch_is_byte_stable_against_legacy_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0026 / AC-06, AC-11, AC-14, AC-30."""
    documents = (_document('''
def confirm(state):
    if state != "ready": return False
    cancel()
'''),)
    request = StateGuardEffectReviewRequest(
        "confirm", StateBindingRequest("state"), "waiting", "cancel"
    )
    current = state_guard_effect_review.review_state_guard_effect_documents(
        documents, request
    )
    expected = _serialized(current, normalize_state_guard_effect_report(current))

    monkeypatch.setattr(state_guard_effect_review, "terminal_symbol", _legacy_terminal)
    monkeypatch.setattr(state_guard_effect_review, "source_locator", _legacy_locator)
    legacy = state_guard_effect_review.review_state_guard_effect_documents(
        documents, request
    )

    assert _serialized(legacy, normalize_state_guard_effect_report(legacy)) == expected
