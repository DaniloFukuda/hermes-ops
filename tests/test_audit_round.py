"""Contract tests for HERMES-0018 independent audit rounds."""

from dataclasses import FrozenInstanceError
from itertools import permutations
import json
from pathlib import Path

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills import audit_round
from hermes_ops.skills.audit_round import (
    AuditRoundRequest, AuditRoundStatus, AuditorOutcomeStatus, CodeAuditRequest,
    ExecutionPathAuditRequest, PersistenceContractAuditRequest,
    PersistenceMutationAuditRequest, audit_round_json, run_audit_round,
    StateGuardEffectAuditRequest,
)
from hermes_ops.skills.code_audit import audit_code_documents, run_code_audit
from hermes_ops.skills import controlled_reader
from hermes_ops.skills.controlled_reader import (
    SourceDocument, SourceLimits, _snapshot_digest, read_scoped_source_snapshot,
)
from hermes_ops.skills.execution_path_review import review_execution_path, review_execution_path_documents
from hermes_ops.skills.execution_models import _freeze
from hermes_ops.skills.persistence_contract_models import PersistenceContractDialect
from hermes_ops.skills.state_guard_effect_models import StateBindingRequest


FLOW = '''
def prepare():
    return "prepared"
def publish(state):
    if state != "confirmed":
        raise ValueError("wrong")
def execute():
    publish(prepare())
'''

MUTATION_FLOW = FLOW + '''
def handle_cancel(entity):
    cancel_entity(entity["id"])
def cancel_entity(entity_id):
    conn.execute("UPDATE sessions SET status='failed' WHERE id=?", (entity_id,))
'''

FOUR_AUDITOR_FLOW = MUTATION_FLOW + '''
def confirm(state):
    if state != "ready":
        return False
    cancel()
'''


def _write(root: Path, relative: str, source: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source) if isinstance(source, bytes) else path.write_text(source, encoding="utf-8")


def _request(root: Path, *, reverse: bool = False) -> AuditRoundRequest:
    requests = (CodeAuditRequest(), ExecutionPathAuditRequest("prepare", "publish"))
    return AuditRoundRequest(root, tuple(reversed(requests)) if reverse else requests)


def test_single_snapshot_is_shared_by_new_frozen_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0018 / AC-01, AC-02, AC-03, AC-19."""
    _write(tmp_path, "flow.py", FLOW)
    reads, snapshots = [], []
    original_read, original_code, original_path = controlled_reader.read_source_documents, audit_round._run_code, audit_round._run_execution_path

    def read(*args: object, **kwargs: object):
        reads.append(1)
        return original_read(*args, **kwargs)

    def code(value):
        snapshots.append(value.snapshot)
        with pytest.raises(FrozenInstanceError):
            value.snapshot.digest = "changed"  # type: ignore[misc]
        return original_code(value)

    def path(value):
        snapshots.append(value.snapshot)
        for forbidden in ("previous_result", "previous_findings", "outcomes", "ranked_findings", "claims", "analysis", "execution_context"):
            assert not hasattr(value, forbidden)
        return original_path(value)

    monkeypatch.setattr(controlled_reader, "read_source_documents", read)
    monkeypatch.setattr(audit_round, "_run_code", code)
    monkeypatch.setattr(audit_round, "_run_execution_path", path)
    result = run_audit_round(_request(tmp_path))
    assert len(reads) == 1
    assert snapshots[0] is snapshots[1]
    assert snapshots[0].digest == result.snapshot_provenance.digest


def test_mutation_mode_shares_one_snapshot_across_three_auditors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0024 / AC-20, AC-21, AC-22."""
    _write(tmp_path, "flow.py", MUTATION_FLOW)
    reads, snapshots = [], []
    original_read = controlled_reader.read_source_documents
    original_code = audit_round._run_code
    original_path = audit_round._run_execution_path
    original_persistence = audit_round._run_persistence_contract

    def read(*args: object, **kwargs: object):
        reads.append(1)
        return original_read(*args, **kwargs)

    def capture(runner):
        def wrapped(value):
            snapshots.append(value.snapshot)
            return runner(value)
        return wrapped

    monkeypatch.setattr(controlled_reader, "read_source_documents", read)
    monkeypatch.setattr(audit_round, "_run_code", capture(original_code))
    monkeypatch.setattr(audit_round, "_run_execution_path", capture(original_path))
    monkeypatch.setattr(audit_round, "_run_persistence_contract", capture(original_persistence))
    request = AuditRoundRequest(tmp_path, (
        CodeAuditRequest(),
        ExecutionPathAuditRequest("prepare", "publish"),
        PersistenceMutationAuditRequest(
            "handle_cancel", PersistenceContractDialect.SQLITE_DBAPI,
            "sessions", "id", "status", "failed",
        ),
    ))
    result = run_audit_round(request)
    assert len(reads) == 1
    assert len(snapshots) == 3 and all(item is snapshots[0] for item in snapshots)
    assert result.status is AuditRoundStatus.COMPLETED
    assert result.auditor_outcomes[2].status is AuditorOutcomeStatus.COMPLETED_NO_FINDINGS


def _four_auditor_request(root: Path, *, reverse: bool = False) -> AuditRoundRequest:
    requests = (
        CodeAuditRequest(),
        ExecutionPathAuditRequest("prepare", "publish"),
        PersistenceMutationAuditRequest(
            "handle_cancel", PersistenceContractDialect.SQLITE_DBAPI,
            "sessions", "id", "status", "failed",
        ),
        StateGuardEffectAuditRequest(
            "confirm", StateBindingRequest("state"), "waiting", "cancel"
        ),
    )
    return AuditRoundRequest(root, tuple(reversed(requests)) if reverse else requests)


def test_four_auditors_share_snapshot_and_normalize_after_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0025 / AC-30, AC-31."""
    _write(tmp_path, "flow.py", FOUR_AUDITOR_FLOW)
    snapshots, events, reads = [], [], []
    original_read = controlled_reader.read_source_documents

    def read(*args, **kwargs):
        reads.append(1)
        return original_read(*args, **kwargs)

    monkeypatch.setattr(controlled_reader, "read_source_documents", read)
    runners = (
        "_run_code", "_run_execution_path", "_run_persistence_contract",
        "_run_state_guard_effect",
    )
    for name in runners:
        original = getattr(audit_round, name)

        def capture(value, *, _name=name, _original=original):
            events.append(f"run:{_name}")
            snapshots.append(value.snapshot)
            if _name == "_run_state_guard_effect":
                assert set(value.__dataclass_fields__) == {"snapshot", "request"}
                for forbidden in (
                    "persistence_report", "mutation_intents", "findings",
                    "reachability", "outcomes", "ranked_findings",
                ):
                    assert not hasattr(value, forbidden)
            return _original(value)

        monkeypatch.setattr(audit_round, name, capture)

    original_execution_normalizer = audit_round.normalize_execution_path_report
    original_state_normalizer = audit_round.normalize_state_guard_effect_report
    original_rank = audit_round.rank_findings

    def normalize_execution(value):
        events.append("normalize:execution")
        return original_execution_normalizer(value)

    def normalize_state(value):
        events.append("normalize:state")
        return original_state_normalizer(value)

    rank_calls = []

    def rank(values):
        events.append("rank")
        rank_calls.append(values)
        return original_rank(values)

    monkeypatch.setattr(audit_round, "normalize_execution_path_report", normalize_execution)
    monkeypatch.setattr(audit_round, "normalize_state_guard_effect_report", normalize_state)
    monkeypatch.setattr(audit_round, "rank_findings", rank)

    result = run_audit_round(_four_auditor_request(tmp_path))

    assert len(reads) == 1
    assert len(snapshots) == 4 and all(item is snapshots[0] for item in snapshots)
    first_normalize = min(index for index, event in enumerate(events) if event.startswith("normalize:"))
    assert all(event.startswith("run:") for event in events[:first_normalize])
    assert len(rank_calls) == 1 and events[-1] == "rank"
    assert len(result.auditor_outcomes) == 4
    assert result.snapshot_provenance is not None


def test_four_auditor_request_order_does_not_change_json(tmp_path: Path) -> None:
    """Spec: HERMES-0025 / AC-26, AC-30."""
    _write(tmp_path, "flow.py", FOUR_AUDITOR_FLOW)
    results = [
        audit_round_json(run_audit_round(_four_auditor_request(tmp_path, reverse=reverse)))
        for reverse in (False, True)
    ]
    assert results[0] == results[1]


def test_state_auditor_failure_is_isolated_without_synthetic_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0025 / AC-30, AC-31."""
    _write(tmp_path, "flow.py", FOUR_AUDITOR_FLOW)

    def fail(_value):
        raise SkillExecutionError("STATE_TEST_FAILURE", "isolated")

    monkeypatch.setattr(audit_round, "_run_state_guard_effect", fail)
    result = run_audit_round(_four_auditor_request(tmp_path))
    outcomes = {item.auditor_id: item for item in result.auditor_outcomes}
    assert outcomes["state-guard-effect-review"].status is AuditorOutcomeStatus.FAILED
    assert outcomes["code-audit"].status is not AuditorOutcomeStatus.FAILED
    assert outcomes["execution-path-review"].status is not AuditorOutcomeStatus.FAILED
    assert outcomes["persistence-contract-review"].status is not AuditorOutcomeStatus.FAILED
    assert all(
        finding.source_skill != "state-guard-effect-review"
        for finding in result.ranked_findings.ordered_findings
    )
    assert result.status is AuditRoundStatus.COMPLETED_WITH_LIMITATIONS


def test_mutation_failure_is_isolated_without_synthetic_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0024 / AC-23."""
    _write(tmp_path, "flow.py", MUTATION_FLOW)

    def fail(_value):
        raise SkillExecutionError("MUTATION_TEST_FAILURE", "isolated")

    monkeypatch.setattr(audit_round, "_run_persistence_contract", fail)
    result = run_audit_round(AuditRoundRequest(tmp_path, (
        CodeAuditRequest(),
        ExecutionPathAuditRequest("prepare", "publish"),
        PersistenceMutationAuditRequest(
            "handle_cancel", PersistenceContractDialect.SQLITE_DBAPI,
            "sessions", "id", "status", "failed",
        ),
    )))
    assert result.status is AuditRoundStatus.COMPLETED_WITH_LIMITATIONS
    assert result.auditor_outcomes[0].status is not AuditorOutcomeStatus.FAILED
    assert result.auditor_outcomes[1].status is not AuditorOutcomeStatus.FAILED
    assert result.auditor_outcomes[2].status is AuditorOutcomeStatus.FAILED
    assert all(
        item.source_skill != "persistence-contract-review"
        for item in result.ranked_findings.ordered_findings
    )


def test_requests_are_canonical_and_invalid_catalog_entries_fail_closed(tmp_path: Path) -> None:
    """Spec: HERMES-0018 / AC-04, AC-05, AC-06."""
    _write(tmp_path, "flow.py", FLOW)
    first, second = run_audit_round(_request(tmp_path)), run_audit_round(_request(tmp_path, reverse=True))
    assert first == second
    assert audit_round_json(first) == audit_round_json(second)
    assert tuple(item.auditor_id for item in first.auditor_outcomes) == ("code-audit", "execution-path-review")
    with pytest.raises(SkillExecutionError) as duplicate:
        AuditRoundRequest(tmp_path, (CodeAuditRequest(), CodeAuditRequest()))
    assert duplicate.value.code == "AUDIT_ROUND_DUPLICATE_AUDITOR"
    with pytest.raises(SkillExecutionError) as unknown:
        AuditRoundRequest(tmp_path, (object(),))  # type: ignore[arg-type]
    assert unknown.value.code == "AUDIT_ROUND_UNKNOWN_AUDITOR"


@pytest.mark.parametrize("failed", ["code", "path"])
def test_auditor_failure_is_isolated_without_synthetic_finding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed: str) -> None:
    """Spec: HERMES-0018 / AC-07, AC-08, AC-14."""
    _write(tmp_path, "flow.py", FLOW + "\nverify = False\n")
    calls = []
    original_code, original_path = audit_round._run_code, audit_round._run_execution_path

    def code(value):
        calls.append("code")
        if failed == "code": raise RuntimeError("incidental absolute C:\\secret")
        return original_code(value)

    def path(value):
        calls.append("path")
        if failed == "path": raise RuntimeError("incidental absolute C:\\secret")
        return original_path(value)

    monkeypatch.setattr(audit_round, "_run_code", code)
    monkeypatch.setattr(audit_round, "_run_execution_path", path)
    result = run_audit_round(_request(tmp_path))
    outcomes = {item.auditor_id: item for item in result.auditor_outcomes}
    failed_id = "code-audit" if failed == "code" else "execution-path-review"
    assert calls == ["code", "path"]
    assert result.status is AuditRoundStatus.COMPLETED_WITH_LIMITATIONS
    assert outcomes[failed_id].status is AuditorOutcomeStatus.FAILED
    assert "C:\\" not in audit_round_json(result)
    assert all(item.source_skill != failed_id for item in result.ranked_findings.ordered_findings)
    assert result.ranked_findings.ordered_findings


def test_insufficient_no_findings_and_findings_remain_distinct(tmp_path: Path) -> None:
    """Spec: HERMES-0018 / AC-09, AC-13."""
    _write(tmp_path, "clean.py", "def produce(value): return value\ndef consume(value): external(value)\n")
    result = run_audit_round(AuditRoundRequest(tmp_path, (CodeAuditRequest(), ExecutionPathAuditRequest("produce", "consume"))))
    outcomes = {item.auditor_id: item for item in result.auditor_outcomes}
    assert outcomes["code-audit"].status is AuditorOutcomeStatus.COMPLETED_NO_FINDINGS
    assert outcomes["code-audit"].limitations == ()
    assert outcomes["execution-path-review"].status is AuditorOutcomeStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE
    assert result.status is AuditRoundStatus.COMPLETED_WITH_LIMITATIONS
    assert result.ranked_findings.ordered_findings == ()


def test_path_only_is_completed_without_findings_or_round_degradation(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / AC-19, AC-20."""
    _write(
        tmp_path,
        "flow.py",
        "def produce(): return opaque()\n"
        "def consume(value): use(value)\n"
        "def execute(): consume(produce())\n",
    )
    result = run_audit_round(
        AuditRoundRequest(tmp_path, (ExecutionPathAuditRequest("produce", "consume"),))
    )
    outcome = result.auditor_outcomes[0]
    assert outcome.status is AuditorOutcomeStatus.COMPLETED_NO_FINDINGS
    assert result.status is AuditRoundStatus.COMPLETED
    assert result.ranked_findings.ordered_findings == ()


def test_snapshot_failure_starts_no_auditor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0018 / AC-10, AC-20."""
    calls = []
    monkeypatch.setattr(audit_round, "_run_code", lambda value: calls.append("code"))
    monkeypatch.setattr(audit_round, "_run_execution_path", lambda value: calls.append("path"))
    result = run_audit_round(_request(tmp_path / "missing"))
    assert result.status is AuditRoundStatus.FAILED
    assert result.snapshot_provenance is None and result.auditor_outcomes == () and calls == []
    assert "C:\\" not in audit_round_json(result)


def test_normalization_waits_for_all_runs_and_ranker_runs_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0018 / AC-11, AC-12."""
    _write(tmp_path, "flow.py", FLOW + "\nverify = False\n")
    events = []
    originals = {"code": audit_round._run_code, "path": audit_round._run_execution_path, "normalize_code": audit_round.normalize_code_audit_finding, "normalize_path": audit_round.normalize_execution_path_report, "rank": audit_round.rank_findings}

    def wrap(name):
        def invoke(*args, **kwargs):
            events.append(name)
            return originals[name](*args, **kwargs)
        return invoke

    for name, attribute in (("code", "_run_code"), ("path", "_run_execution_path"), ("normalize_code", "normalize_code_audit_finding"), ("normalize_path", "normalize_execution_path_report"), ("rank", "rank_findings")):
        monkeypatch.setattr(audit_round, attribute, wrap(name))
    run_audit_round(_request(tmp_path))
    assert max(events.index("code"), events.index("path")) < min(events.index("normalize_code"), events.index("normalize_path"))
    assert events.count("rank") == 1 and events[-1] == "rank"


def test_snapshot_resists_physical_drift_between_auditors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0018 / AC-15."""
    _write(tmp_path, "flow.py", FLOW)
    seen = []
    original_code, original_path = audit_round._run_code, audit_round._run_execution_path

    def code(value):
        seen.append((value.snapshot.digest, value.snapshot.documents[0].text))
        _write(tmp_path, "flow.py", "def replaced(): return True\n")
        return original_code(value)

    def path(value):
        seen.append((value.snapshot.digest, value.snapshot.documents[0].text))
        return original_path(value)

    monkeypatch.setattr(audit_round, "_run_code", code)
    monkeypatch.setattr(audit_round, "_run_execution_path", path)
    result = run_audit_round(_request(tmp_path))
    assert seen[0] == seen[1]
    assert result.auditor_outcomes[1].status is AuditorOutcomeStatus.COMPLETED_WITH_FINDINGS


def test_structural_scope_prunes_invalid_file_before_read(tmp_path: Path) -> None:
    """Spec: HERMES-0018 / AC-16."""
    _write(tmp_path, "allowed/flow.py", FLOW)
    _write(tmp_path, "outside/broken.py", b"\x00not-source")
    result = run_audit_round(AuditRoundRequest(tmp_path, (CodeAuditRequest(), ExecutionPathAuditRequest("prepare", "publish")), ("allowed",)))
    assert result.status is AuditRoundStatus.COMPLETED
    assert result.snapshot_provenance.structural_scope == ("allowed",)
    assert all(ref.path.startswith("allowed/") for finding in result.ranked_findings.ordered_findings for ref in finding.evidence_refs)


def test_snapshot_and_round_are_deterministic_and_sanitized(tmp_path: Path) -> None:
    """Spec: HERMES-0018 / AC-04, AC-17, AC-20."""
    _write(tmp_path, "z.py", "verify = False\n")
    _write(tmp_path, "a.py", FLOW)
    snapshots = [read_scoped_source_snapshot(tmp_path) for _ in range(2)]
    results = [run_audit_round(_request(tmp_path, reverse=bool(index))) for index in range(2)]
    assert snapshots[0].digest == snapshots[1].digest and results[0] == results[1]
    payload = audit_round_json(results[0])
    assert payload == audit_round_json(results[1]) and str(tmp_path) not in payload
    assert "timestamp" not in payload and "duration" not in payload and "pid" not in payload
    json.loads(payload)


def test_snapshot_digest_ignores_document_input_order() -> None:
    """Spec: HERMES-0018 / AC-17."""
    documents = (
        SourceDocument("z.py", "z = 1\n", 6),
        SourceDocument("a.py", "a = 1\n", 6),
    )
    limits = SourceLimits(32, 5_000, 1_000, 512 * 1024, 20 * 1024 * 1024)
    assert _snapshot_digest(("src",), documents, limits) == _snapshot_digest(
        ("src",), tuple(reversed(documents)), limits
    )


def test_invalid_execution_symbols_fail_before_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0018 / AC-06, AC-19."""
    calls = []
    monkeypatch.setattr(audit_round, "read_scoped_source_snapshot", lambda *args, **kwargs: calls.append(1))
    with pytest.raises(SkillExecutionError) as caught:
        ExecutionPathAuditRequest("invalid.name", "publish")
    assert caught.value.code == "AUDIT_ROUND_INVALID_REQUEST" and calls == []


def test_public_wrappers_equal_pure_cores_on_same_sources(tmp_path: Path) -> None:
    """Spec: HERMES-0018 / AC-18."""
    _write(tmp_path, "flow.py", FLOW + "\nverify = False\n")
    snapshot = read_scoped_source_snapshot(tmp_path)
    wrapper_code, core_code = run_code_audit(tmp_path), audit_code_documents(snapshot.documents, snapshot.directories)
    assert wrapper_code.evidence[0].details == _freeze(core_code.summary)
    assert len(wrapper_code.evidence) - 1 == len(core_code.findings)
    wrapper_path = review_execution_path(tmp_path, "prepare", "publish")
    core_path = review_execution_path_documents(snapshot.documents, "prepare", "publish", structural_scope=snapshot.structural_scope)
    assert wrapper_path == core_path


def test_persistence_is_an_independent_third_auditor_on_the_same_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0021 / AC-25, AC-27"""
    source = '''
def create(conn):
    cursor = conn.execute("INSERT INTO archive (state) VALUES (?)", ("ready",))
    record_id = cursor.lastrowid
    return record_id
def consume(conn, record_id):
    row = conn.execute("SELECT state FROM records WHERE id = ?", (record_id,)).fetchone()
    return row
'''
    _write(tmp_path, "store.py", source)
    reads, snapshots = [], []
    original_read = audit_round.read_scoped_source_snapshot
    original_persistence = audit_round._run_persistence_contract

    def read(*args, **kwargs):
        reads.append(1)
        return original_read(*args, **kwargs)

    def persistence(value):
        snapshots.append(value.snapshot)
        return original_persistence(value)

    monkeypatch.setattr(audit_round, "read_scoped_source_snapshot", read)
    monkeypatch.setattr(audit_round, "_run_persistence_contract", persistence)
    result = run_audit_round(AuditRoundRequest(tmp_path, (
        CodeAuditRequest(), ExecutionPathAuditRequest("create", "consume"),
        PersistenceContractAuditRequest(
            "create", "consume", PersistenceContractDialect.SQLITE_DBAPI, "records", "id",
        ),
    )))
    assert len(reads) == 1 and snapshots[0].digest == result.snapshot_provenance.digest
    assert tuple(item.auditor_id for item in result.auditor_outcomes) == (
        "code-audit", "execution-path-review", "persistence-contract-review",
    )
    assert any(
        item.source_skill == "persistence-contract-review"
        for item in result.ranked_findings.ordered_findings
    )


def test_three_auditor_order_is_canonical_and_persistence_failure_is_isolated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0021 / AC-27"""
    _write(tmp_path, "flow.py", FLOW)
    requests = (
        CodeAuditRequest(), ExecutionPathAuditRequest("prepare", "publish"),
        PersistenceContractAuditRequest(
            "prepare", "publish", PersistenceContractDialect.SQLITE_DBAPI, "records", "id",
        ),
    )
    payloads = {
        audit_round_json(run_audit_round(AuditRoundRequest(tmp_path, tuple(order))))
        for order in permutations(requests)
    }
    assert len(payloads) == 1

    monkeypatch.setattr(
        audit_round, "_run_persistence_contract",
        lambda value: (_ for _ in ()).throw(RuntimeError("persistence failed")),
    )
    result = run_audit_round(AuditRoundRequest(tmp_path, requests))
    outcomes = {item.auditor_id: item for item in result.auditor_outcomes}
    assert result.status is AuditRoundStatus.COMPLETED_WITH_LIMITATIONS
    assert outcomes["persistence-contract-review"].status is AuditorOutcomeStatus.FAILED
    assert outcomes["code-audit"].status is not AuditorOutcomeStatus.FAILED
    assert outcomes["execution-path-review"].status is not AuditorOutcomeStatus.FAILED
    assert all(
        item.source_skill != "persistence-contract-review"
        for item in result.ranked_findings.ordered_findings
    )
