"""Contract and dogfood tests for HERMES-0030 v2."""

from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path

import pytest

from hermes_ops.cli import build_parser, main
from hermes_ops.memory.core import observation_from_auditor_outcome, observation_from_rankable_finding
from hermes_ops.memory.models import (
    AuditMemoryObservation, DisclosureLevel, FreshnessState, LineageEventKind, MemoryCandidate,
    MemoryCurrentContext, MemoryError, MemoryKind, MemoryRevalidationHint,
    RepositoryIdentity,
)
from hermes_ops.memory.store import MemoryService
from hermes_ops.orchestration import (
    MemoryAssistedAuditRequest, MemoryMode, memory_assisted_audit_json,
    run_memory_assisted_audit,
)
from hermes_ops.skills import audit_round
from hermes_ops.skills.audit_round import (
    AuditRoundRequest, AuditRoundStatus, AuditorOutcomeStatus, CodeAuditRequest,
    ExecutionPathAuditRequest, audit_round_json, run_audit_round,
)
from hermes_ops.skills.execution_path_models import ExecutionPathClassification
from hermes_ops.skills.source_evidence import parse_source_locator


BUG = '''
def prepare():
    return "prepared"
def publish(state):
    if state != "confirmed":
        raise ValueError("wrong")
def execute():
    publish(prepare())
'''

FIXED = BUG.replace('return "prepared"', 'return "confirmed"')

PATH_ONLY = '''
def create_session(source):
    cursor = store(source)
    return int(cursor.lastrowid)
def update_session(session_id, value):
    write_update(session_id, value)
def orchestrate(source, value):
    session_id = create_session(source)
    update_session(session_id, value)
'''


def _write(root: Path, source: str = BUG) -> None:
    root.mkdir(exist_ok=True)
    (root / "flow.py").write_text(source, encoding="utf-8")


def _audit_request(path_only: bool = False) -> ExecutionPathAuditRequest:
    return (
        ExecutionPathAuditRequest("create_session", "update_session")
        if path_only else ExecutionPathAuditRequest("prepare", "publish")
    )


def _request(
    target: Path,
    mode: MemoryMode = MemoryMode.DISABLED,
    *,
    path_only: bool = False,
    write: bool = False,
    scope: tuple[str, ...] = ("flow.py",),
) -> MemoryAssistedAuditRequest:
    return MemoryAssistedAuditRequest(
        mission="execution path audit",
        target=target,
        repository_identity=RepositoryIdentity.explicit("repo-logical-id"),
        current_context=MemoryCurrentContext(
            "repo-logical-id", current_revision="current-revision",
        ),
        authoritative_structural_scope=scope,
        audit_requests=(_audit_request(path_only),),
        memory_mode=mode,
        allow_post_audit_write=write,
    )


def _canonical(request: ExecutionPathAuditRequest) -> dict[str, object]:
    return {field.name: getattr(request, field.name) for field in fields(request)}


def _historical_confirmed(service: MemoryService, target: Path) -> AuditMemoryObservation:
    fresh = run_audit_round(AuditRoundRequest(target, (_audit_request(),), ("flow.py",)))
    finding = fresh.ranked_findings.ordered_findings[0]
    outcome = fresh.auditor_outcomes[0]
    observation = observation_from_rankable_finding(
        finding,
        repository_id="repo-logical-id",
        canonical_request=_canonical(_audit_request()),
        source_revision="historical-revision",
        snapshot_digest="sha256:historical",
        structural_scope=("flow.py",),
        auditor_version=outcome.auditor_version,
        normalizer_version=outcome.normalizer_version,
        limitations=outcome.limitations,
        finding_kind=outcome.auditor_id,
        symbols=("prepare", "publish"),
        retrieval_terms=("execution", "path", "audit"),
    )
    assert service.store is not None and service.store.write(observation)
    return observation


def _historical_native(
    service: MemoryService, target: Path, kind: MemoryKind, *, path_only: bool = False,
) -> AuditMemoryObservation:
    request = _audit_request(path_only)
    fresh = run_audit_round(AuditRoundRequest(target, (request,), ("flow.py",)))
    outcome = fresh.auditor_outcomes[0]
    refs = tuple(
        parse_source_locator(item)
        for item in getattr(outcome.native_result, "evidence_references", ())
    )
    observation = observation_from_auditor_outcome(
        outcome,
        memory_kind=kind,
        repository_id="repo-logical-id",
        canonical_request=_canonical(request),
        source_revision="historical-revision",
        snapshot_digest="sha256:historical",
        structural_scope=("flow.py",),
        finding_kind=outcome.auditor_id,
        symbols=(request.producer_symbol, request.consumer_symbol),
        relative_paths=("flow.py",),
        evidence_refs=refs,
        retrieval_terms=("execution", "path", "audit"),
    )
    assert service.store is not None
    assert service.store.write(
        observation,
        revalidation=kind is MemoryKind.ALIGNED_REVALIDATION,
    )
    return observation


def test_request_separates_logical_identity_from_real_target(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-01, AC-24, AC-38."""
    target = tmp_path / "target"
    _write(target)
    result = run_memory_assisted_audit(_request(target))
    assert result.fresh_audit.status is AuditRoundStatus.COMPLETED
    assert result.fresh_audit.snapshot_provenance is not None
    assert result.fresh_audit.snapshot_provenance.structural_scope == ("flow.py",)
    assert result.fresh_audit.ranked_findings.ordered_findings


def test_request_validation_and_defaults(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-31, AC-37."""
    target = tmp_path / "target"
    _write(target)
    request = _request(target)
    assert request.memory_mode is MemoryMode.DISABLED
    assert request.allow_post_audit_write is False
    with pytest.raises(ValueError):
        MemoryAssistedAuditRequest(
            "mission", object(), RepositoryIdentity.explicit("repo"), None, (),
            (_audit_request(),),
        )


def test_memory_service_releases_sqlite_handle(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / lifecycle remediation."""
    path = tmp_path / "memory.db"
    with MemoryService.open(path) as service:
        assert service.store is not None
    renamed = tmp_path / "renamed.db"
    path.rename(renamed)
    renamed.unlink()


def test_fresh_result_is_byte_identical_across_modes(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-01, AC-02, AC-03, AC-24, AC-26, AC-28."""
    target = tmp_path / "target"
    _write(target)
    with MemoryService.open(tmp_path / "memory.db") as service:
        results = (
            run_memory_assisted_audit(_request(target)),
            run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY), service),
            run_memory_assisted_audit(_request(target, MemoryMode.READ_WRITE, write=True), service),
        )
    serialized = tuple(audit_round_json(item.fresh_audit) for item in results)
    assert serialized[0] == serialized[1] == serialized[2]
    fresh = results[0].fresh_audit
    assert fresh.snapshot_provenance is not None
    assert fresh.auditor_outcomes[0].native_result is not None
    assert fresh.ranked_findings.ordered_findings[0].finding_id
    assert fresh.ranked_findings.ordered_findings[0].evidence_refs


def test_memory_objects_never_cross_fresh_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0030 / AC-05, AC-10, AC-25, AC-27, AC-39."""
    target = tmp_path / "target"
    _write(target)
    captured: list[AuditRoundRequest] = []
    original = audit_round.run_audit_round

    def spy(request: AuditRoundRequest):
        captured.append(request)
        for value in (request, *request.auditor_requests):
            assert not isinstance(value, (MemoryCandidate, MemoryRevalidationHint, AuditMemoryObservation))
        return original(request)

    monkeypatch.setattr("hermes_ops.orchestration.memory_assisted_audit.run_audit_round", spy)
    with MemoryService.open(tmp_path / "memory.db") as service:
        _historical_confirmed(service, target)
        result = run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY), service)
    assert captured and captured[0].target == target
    assert result.historical_context.candidates


def test_authoritative_scope_and_requests_reach_round_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0030 / AC-11, AC-12."""
    target = tmp_path / "target"
    target.mkdir()
    for name in ("a.py", "b.py", "c.py"):
        (target / name).write_text("def value(): return 1\n", encoding="utf-8")
    request = _request(target, MemoryMode.READ_ONLY, scope=("a.py", "b.py", "c.py"))
    captured: list[AuditRoundRequest] = []
    original = audit_round.run_audit_round

    def spy(value: AuditRoundRequest):
        captured.append(value)
        return original(value)

    monkeypatch.setattr("hermes_ops.orchestration.memory_assisted_audit.run_audit_round", spy)
    with MemoryService.open(tmp_path / "memory.db") as service:
        run_memory_assisted_audit(request, service)
    assert captured[0].structural_scope == ("a.py", "b.py", "c.py")
    assert captured[0].auditor_requests == request.audit_requests
    assert len(captured[0].auditor_requests) == 1


def test_no_candidate_is_normal_and_json_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-04, AC-23, AC-34."""
    target = tmp_path / "target"
    _write(target)
    with MemoryService.open(tmp_path / "memory.db") as service:
        result = run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY), service)
    assert result.historical_context.candidates == ()
    assert result.fresh_audit.status is AuditRoundStatus.COMPLETED
    first = memory_assisted_audit_json(result)
    assert first == memory_assisted_audit_json(result)
    payload = json.loads(first)
    assert set(payload) == {"memory_context", "audit_plan", "fresh_audit", "memory_writeback"}


def test_confirmed_reproduced_dogfood_and_reconfirmed_lineage(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-05, AC-18, AC-21, AC-28, AC-33, AC-35."""
    target = tmp_path / "target"
    _write(target)
    with MemoryService.open(tmp_path / "memory.db") as service:
        historical = _historical_confirmed(service, target)
        off = run_memory_assisted_audit(_request(target))
        read = run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY), service)
        written = run_memory_assisted_audit(_request(target, MemoryMode.READ_WRITE, write=True), service)
        assert service.store is not None
        events = service.store.lineage_events(historical.lineage_id, "repo-logical-id")
    assert read.historical_context.candidates[0].freshness_state is FreshnessState.STALE_CANDIDATE
    assert read.historical_context.revalidation_hints[0].requires_fresh_audit
    assert audit_round_json(off.fresh_audit) == audit_round_json(read.fresh_audit) == audit_round_json(written.fresh_audit)
    assert written.memory_writeback.written_observations
    assert any(item.kind is LineageEventKind.RECONFIRMED for item in events)


def test_historical_fixed_dogfood_writes_not_reproduced(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-08, AC-09, AC-20, AC-22."""
    target = tmp_path / "target"
    _write(target, BUG)
    with MemoryService.open(tmp_path / "memory.db") as service:
        historical = _historical_confirmed(service, target)
        _write(target, FIXED)
        result = run_memory_assisted_audit(_request(target, MemoryMode.READ_WRITE, write=True), service)
        assert service.store is not None
        events = service.store.lineage_events(historical.lineage_id, "repo-logical-id")
        original = service.store.expand(historical.observation_id, "repo-logical-id", DisclosureLevel.CANONICAL)
        aligned = service.store.expand(
            result.memory_writeback.written_observations[0],
            "repo-logical-id", DisclosureLevel.CANONICAL,
        )
    assert result.fresh_audit.ranked_findings.ordered_findings == ()
    assert result.memory_writeback.written_observations
    assert any(item.kind is LineageEventKind.NOT_REPRODUCED for item in events)
    assert original.observation_id == historical.observation_id
    assert "return eval(payload)" not in aligned.canonical_json()


def test_aligned_history_regression_does_not_suppress_finding(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-06, AC-25, AC-26."""
    target = tmp_path / "target"
    _write(target, FIXED)
    with MemoryService.open(tmp_path / "memory.db") as service:
        _historical_native(service, target, MemoryKind.ALIGNED_REVALIDATION)
        _write(target, BUG)
        off = run_memory_assisted_audit(_request(target))
        read = run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY), service)
    assert read.historical_context.candidates[0].memory_kind is MemoryKind.ALIGNED_REVALIDATION
    assert read.fresh_audit.ranked_findings == off.fresh_audit.ranked_findings
    assert read.fresh_audit.ranked_findings.ordered_findings[0].finding_id == off.fresh_audit.ranked_findings.ordered_findings[0].finding_id


def test_path_only_dogfood_stays_non_actionable_and_writes(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-07, AC-18, AC-28."""
    target = tmp_path / "target"
    _write(target, PATH_ONLY)
    with MemoryService.open(tmp_path / "memory.db") as service:
        _historical_native(service, target, MemoryKind.PATH_ONLY_OBSERVATION, path_only=True)
        off = run_memory_assisted_audit(_request(target, path_only=True))
        read = run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY, path_only=True), service)
        written = run_memory_assisted_audit(_request(target, MemoryMode.READ_WRITE, path_only=True, write=True), service)
        assert service.store is not None
        persisted = service.store.expand(
            written.memory_writeback.written_observations[0],
            "repo-logical-id", DisclosureLevel.CANONICAL,
        )
    outcome = written.fresh_audit.auditor_outcomes[0]
    assert outcome.native_result.classification is ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT
    assert written.fresh_audit.ranked_findings.ordered_findings == ()
    assert read.historical_context.suggested_paths == ("flow.py",)
    assert written.memory_writeback.written_observations
    assert "cursor = store(source)" not in persisted.canonical_json()
    assert audit_round_json(off.fresh_audit) == audit_round_json(read.fresh_audit) == audit_round_json(written.fresh_audit)


@pytest.mark.parametrize("failure", ["unavailable", "corrupt", "unsupported", "fts"])
def test_memory_read_failures_preserve_fresh_audit(tmp_path: Path, failure: str) -> None:
    """Spec: HERMES-0030 / AC-14, AC-15, AC-16, AC-17."""
    target = tmp_path / "target"
    _write(target)
    expected = audit_round_json(run_memory_assisted_audit(_request(target)).fresh_audit)
    path = tmp_path / f"{failure}.db"
    if failure == "corrupt":
        path.write_bytes(b"not sqlite")
        service = MemoryService.open(path)
    elif failure == "unsupported":
        with MemoryService.open(path) as seeded:
            seeded.store._connection.execute("UPDATE memory_meta SET value='999' WHERE key='schema_version'")
            seeded.store._connection.commit()
        service = MemoryService.open(path)
    elif failure == "fts":
        service = MemoryService.open(path)
        service.store.fts_available = False
        service.diagnostics = ("MEMORY_FTS_UNAVAILABLE",)
    else:
        service = MemoryService.disabled()
        service.diagnostics = ("MEMORY_STORE_UNAVAILABLE",)
    try:
        result = run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY), service)
    finally:
        service.close()
    assert audit_round_json(result.fresh_audit) == expected
    assert result.historical_context.memory_diagnostics


def test_write_failure_is_attempted_and_fresh_result_survives(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0030 / AC-17."""
    target = tmp_path / "target"
    _write(target)
    expected = audit_round_json(run_memory_assisted_audit(_request(target)).fresh_audit)
    with MemoryService.open(tmp_path / "memory.db") as service:
        def fail(*_args, **_kwargs):
            raise MemoryError("MEMORY_WRITE_TEST_FAILURE", "expected")
        monkeypatch.setattr(service.store, "write", fail)
        result = run_memory_assisted_audit(_request(target, MemoryMode.READ_WRITE, write=True), service)
    assert result.memory_writeback.attempted is True
    assert "MEMORY_WRITE_TEST_FAILURE" in result.memory_writeback.write_diagnostics
    assert audit_round_json(result.fresh_audit) == expected


def test_failed_auditor_is_not_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0030 / AC-19."""
    target = tmp_path / "target"
    _write(target)
    def fail(_value):
        raise RuntimeError("isolated")
    monkeypatch.setattr(audit_round, "_run_execution_path", fail)
    with MemoryService.open(tmp_path / "memory.db") as service:
        result = run_memory_assisted_audit(_request(target, MemoryMode.READ_WRITE, write=True), service)
    assert result.fresh_audit.auditor_outcomes[0].status is AuditorOutcomeStatus.FAILED
    assert result.memory_writeback.written_observations == ()


def test_operational_limitation_requires_explicit_opt_in(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / AC-19, AC-20, AC-30."""
    target = tmp_path / "target"
    _write(target, "def prepare(): return unknown()\ndef publish(value): use(value)\ndef execute(): publish(prepare())\n")
    base = _request(target, MemoryMode.READ_WRITE, write=True)
    with MemoryService.open(tmp_path / "memory.db") as service:
        without = run_memory_assisted_audit(base, service)
        enabled = MemoryAssistedAuditRequest(
            **{field.name: getattr(base, field.name) for field in fields(base) if field.name != "allow_operational_limitation_write"},
            allow_operational_limitation_write=True,
        )
        with_opt_in = run_memory_assisted_audit(enabled, service)
        assert service.store is not None
        without_kinds = {
            service.store.expand(item, "repo-logical-id", DisclosureLevel.CANONICAL).memory_kind
            for item in without.memory_writeback.written_observations
        }
        with_kinds = {
            service.store.expand(item, "repo-logical-id", DisclosureLevel.CANONICAL).memory_kind
            for item in with_opt_in.memory_writeback.written_observations
        }
    assert MemoryKind.OPERATIONAL_LIMITATION not in without_kinds
    assert MemoryKind.OPERATIONAL_LIMITATION in with_kinds


def test_comparison_is_retained_without_changing_fresh_result(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / historical comparison contract."""
    target = tmp_path / "target"
    _write(target)
    with MemoryService.open(tmp_path / "memory.db") as service:
        historical = _historical_confirmed(service, target)
        result = run_memory_assisted_audit(_request(target, MemoryMode.READ_ONLY), service)
    assert historical.observation_id in result.historical_context.comparison["historical_reproduced"]
    assert result.fresh_audit.ranked_findings.ordered_findings


def test_new_canonical_observation_never_persists_source_literal(tmp_path: Path) -> None:
    """Spec: HERMES-0030 / native-payload privacy remediation."""
    target = tmp_path / "target"
    _write(target, "def dangerous(payload):\n    return eval(payload)\n")
    with MemoryService.open(tmp_path / "memory.db") as service:
        request = MemoryAssistedAuditRequest(
            mission="dynamic",
            target=target,
            repository_identity=RepositoryIdentity.explicit("privacy-repo"),
            current_context=None,
            authoritative_structural_scope=("flow.py",),
            audit_requests=(CodeAuditRequest(),),
            memory_mode=MemoryMode.READ_WRITE,
            allow_post_audit_write=True,
        )
        result = run_memory_assisted_audit(request, service)
        observation_id = result.memory_writeback.written_observations[0]
        assert service.store is not None
        observation = service.store.expand(
            observation_id, "privacy-repo", DisclosureLevel.CANONICAL,
        )
        serialized = observation.canonical_json()
    assert "return eval(payload)" not in serialized
    assert "eval(payload)" not in serialized
    assert observation.evidence_refs[0].path == "flow.py"
    assert observation.original_finding_id == result.fresh_audit.ranked_findings.ordered_findings[0].finding_id


def test_cli_default_off_and_output_separation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0030 / AC-36, AC-37."""
    target = tmp_path / "target"
    _write(target)
    code = main(["skill", "run", "memory-assisted-audit", "--project", str(target), "--mission", "audit"])
    output = capsys.readouterr().out
    assert code == 0
    assert "HISTORICAL MEMORY" in output and "CURRENT AUDIT RESULT" in output
    args = build_parser().parse_args(["skill", "run", "code-audit", "--project", str(target)])
    assert args.memory == "off"


def test_cli_read_and_read_write_json_are_deterministic(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0030 / AC-23, AC-36, AC-37."""
    target = tmp_path / "target"
    _write(target)
    store = tmp_path / "memory.db"
    with MemoryService.open(store):
        pass
    common = [
        "skill", "run", "memory-assisted-audit", "--project", str(target),
        "--mission", "audit", "--repository-id", "repo-logical-id",
        "--memory-store", str(store), "--format", "json",
    ]
    assert main([*common, "--memory", "read"]) == 0
    read_payload = json.loads(capsys.readouterr().out)
    assert main([*common, "--memory", "read-write"]) == 0
    write_payload = json.loads(capsys.readouterr().out)
    assert read_payload["fresh_audit"] == write_payload["fresh_audit"]
    assert json.dumps(read_payload, sort_keys=True) == json.dumps(read_payload, sort_keys=True)


def test_cli_rejects_invalid_or_incomplete_memory_options(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0030 / AC-36, AC-37."""
    target = tmp_path / "target"
    _write(target)
    with pytest.raises(SystemExit) as error:
        main(["skill", "run", "memory-assisted-audit", "--project", str(target), "--mission", "audit", "--memory", "invalid"])
    assert error.value.code == 2
    assert main(["skill", "run", "memory-assisted-audit", "--project", str(target), "--mission", "audit", "--memory", "read"]) == 2
    assert "requires --memory-store" in capsys.readouterr().err
