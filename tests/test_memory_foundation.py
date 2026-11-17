"""Generic contract matrix for HERMES-0028 Memory V1."""

from dataclasses import replace
import sqlite3

import pytest

from hermes_ops.skills.finding_models import (
    CommonSeverity,
    EvidenceRef,
    EvidenceStrength,
    ProductionReachability,
    RankableFinding,
)
from hermes_ops.memory import (
    AuditMemoryObservation,
    DisclosureLevel,
    FreshnessState,
    LineageEventKind,
    MemoryError,
    MemoryKind,
    MemoryRetrievalRequest,
    MemorySchemaVersion,
    MemoryService,
    MemoryStore,
    RepositoryIdentity,
    canonical_request_payload,
    create_observation,
    is_memory_eligible,
    observation_from_rankable_finding,
)


def _finding(identifier: str = "sha256:abc") -> RankableFinding:
    return RankableFinding(
        1,
        identifier,
        "execution-path-review",
        "A historical mismatch was confirmed.",
        CommonSeverity.HIGH,
        EvidenceStrength.CONFIRMED,
        ProductionReachability.CONFIRMED,
        (EvidenceRef("src/flow.py", 7, 7),),
        (("finding_kind", "CONTRACT_MISMATCH"),),
    )


def _observation(**changes) -> AuditMemoryObservation:
    values = dict(
        repository_id="repo:alpha",
        source_revision="rev-1",
        snapshot_digest="sha256:snapshot",
        structural_scope=("src/flow.py",),
        canonical_request={"producer_symbol": "prepare", "consumer_symbol": "publish"},
        source_auditor="execution-path-review",
        auditor_version=1,
        normalizer_version=1,
        outcome_status="COMPLETED_WITH_FINDINGS",
        native_classification="CONFIRMED_MISMATCH",
        limitations=(),
        original_finding_id="sha256:abc",
        finding_kind="CONTRACT_MISMATCH",
        historical_severity="high",
        historical_reachability="CONFIRMED",
        evidence_refs=(EvidenceRef("src/flow.py", 7, 7),),
        native_payload={
            "source_skill": "execution-path-review",
            "finding_id": "sha256:abc",
            "finding_kind": "CONTRACT_MISMATCH",
            "severity": "high",
            "evidence_strength": "CONFIRMED",
            "production_reachability": "CONFIRMED",
            "evidence_refs": (EvidenceRef("src/flow.py", 7, 7),),
        },
        memory_kind=MemoryKind.CONFIRMED_FINDING,
        symbols=("prepare", "publish"),
        relative_paths=("src/flow.py",),
        retrieval_terms=("historical", "mismatch"),
    )
    values.update(changes)
    return create_observation(**values)


def test_repository_identity_is_explicit_or_deterministic() -> None:
    """Spec: HERMES-0028 / AC-02."""
    assert RepositoryIdentity.explicit("repo:alpha").repository_id == "repo:alpha"
    first = RepositoryIdentity.derive("project", "origin-fingerprint")
    second = RepositoryIdentity.derive("project", "origin-fingerprint")
    assert first == second
    assert first.repository_id.startswith("sha256:")


def test_request_canonicalization_is_order_independent_and_type_preserving() -> None:
    """Spec: HERMES-0028 / AC-33."""
    first, first_digest = canonical_request_payload({"b": True, "a": 1})
    second, second_digest = canonical_request_payload({"a": 1, "b": True})
    integer, integer_digest = canonical_request_payload({"b": 1, "a": 1})
    assert first == second and first_digest == second_digest
    assert first_digest != integer_digest
    assert type(first["b"]) is bool and type(integer["b"]) is int


@pytest.mark.parametrize(
    "canonical_value",
    [
        {"path": "C:/Users/example/secret.py"},
        {"path": "/etc/passwd"},
        {"raw_source": "print('content')"},
        {"api_token": "secret"},
        {"value": object()},
    ],
)
def test_privacy_gate_rejects_unsafe_canonical_request(canonical_value: object) -> None:
    """Spec: HERMES-0028 / AC-03."""
    with pytest.raises(MemoryError) as caught:
        canonical_request_payload(canonical_value)
    assert caught.value.code == "MEMORY_RECORD_UNSAFE"


def test_observation_and_lineage_identity_contract() -> None:
    """Spec: HERMES-0028 / AC-04, AC-05."""
    first = _observation()
    same = _observation()
    revised = _observation(source_revision="rev-2")
    other_repo = _observation(repository_id="repo:beta")
    changed_payload = _observation(native_payload={"summary": "different"})
    assert first == same
    assert first.observation_id != revised.observation_id
    assert first.lineage_id == revised.lineage_id
    assert first.observation_id != other_repo.observation_id
    assert first.lineage_id != other_repo.lineage_id
    assert first.observation_id != changed_payload.observation_id


def test_confirmed_finding_adapter_and_eligibility() -> None:
    """Spec: HERMES-0028 / AC-25, AC-26."""
    observation = observation_from_rankable_finding(
        _finding(),
        repository_id="repo:alpha",
        source_revision="rev-1",
        snapshot_digest="sha256:snapshot",
        structural_scope=("src/flow.py",),
        canonical_request={"producer_symbol": "prepare"},
        auditor_version=1,
        normalizer_version=1,
        finding_kind="CONTRACT_MISMATCH",
        symbols=("prepare",),
    )
    assert observation.memory_kind is MemoryKind.CONFIRMED_FINDING
    assert is_memory_eligible(observation)
    failed = _observation(outcome_status="FAILED")
    assert not is_memory_eligible(failed)


def test_conditional_write_eligibility() -> None:
    """Spec: HERMES-0028 / AC-27, AC-28."""
    path_only = _observation(
        memory_kind=MemoryKind.PATH_ONLY_OBSERVATION,
        original_finding_id=None,
        evidence_refs=(),
        relative_paths=(),
    )
    limitation = _observation(
        memory_kind=MemoryKind.OPERATIONAL_LIMITATION,
        limitations=("NO_EXECUTABLE_PATH",),
    )
    aligned = _observation(memory_kind=MemoryKind.ALIGNED_REVALIDATION)
    assert not is_memory_eligible(path_only)
    assert is_memory_eligible(replace(path_only, relative_paths=("src/flow.py",)))
    assert not is_memory_eligible(limitation)
    assert is_memory_eligible(limitation, operational_opt_in=True)
    assert not is_memory_eligible(aligned)
    assert is_memory_eligible(aligned, revalidation=True)


def test_store_migration_idempotency_and_future_schema(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-01, AC-08, AC-29."""
    path = tmp_path / "memory.sqlite3"
    MemoryStore(path).close()
    MemoryStore(path).close()
    connection = sqlite3.connect(path)
    connection.execute("UPDATE memory_meta SET value = '99' WHERE key = 'schema_version'")
    connection.commit()
    connection.close()
    with pytest.raises(MemoryError) as caught:
        MemoryStore(path)
    assert caught.value.code == "MEMORY_SCHEMA_UNSUPPORTED"


def test_append_only_idempotency_and_integrity(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-06, AC-07."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    observation = _observation()
    assert store.write(observation)
    assert not store.write(observation)
    with pytest.raises(MemoryError) as fabricated:
        store.write(replace(observation, native_payload={"summary": "fabricated"}))
    assert fabricated.value.code == "MEMORY_RECORD_INTEGRITY_ERROR"
    store._connection.execute(
        "UPDATE memory_observations SET canonical_json = '{}' WHERE observation_id = ?",
        (observation.observation_id,),
    )
    store._connection.commit()
    with pytest.raises(MemoryError) as caught:
        store.write(observation)
    assert caught.value.code == "MEMORY_RECORD_INTEGRITY_ERROR"
    store.close()


def test_exact_retrieval_and_repository_isolation(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-09, AC-31, AC-32."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    alpha = _observation()
    beta = _observation(repository_id="repo:beta")
    store.write(alpha)
    store.write(beta)
    request = MemoryRetrievalRequest(
        "repo:alpha", symbols=("prepare",), relative_paths=("src/flow.py",)
    )
    results = store.retrieve(request)
    assert tuple(item.observation_id for item in results) == (alpha.observation_id,)
    mismatch = MemoryRetrievalRequest(
        "repo:beta", observation_id=alpha.observation_id
    )
    with pytest.raises(MemoryError) as caught:
        store.retrieve(mismatch)
    assert caught.value.code == "MEMORY_REPOSITORY_MISMATCH"
    store.close()


def test_lexical_retrieval_or_controlled_fallback(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-10, AC-11."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    observation = _observation()
    store.write(observation)
    request = MemoryRetrievalRequest("repo:alpha", mission_terms=("mismatch",))
    results = store.retrieve(request)
    if store.fts_available:
        assert results and results[0].observation_id == observation.observation_id
    else:
        assert results == ()
        assert "MEMORY_FTS_UNAVAILABLE" in store.diagnostics
    store.close()


def test_progressive_disclosure_and_hint(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-14–AC-19."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    observation = _observation()
    store.write(observation)
    header = store.expand(observation.observation_id, "repo:alpha", DisclosureLevel.HEADER)
    structured = store.expand(
        observation.observation_id, "repo:alpha", DisclosureLevel.STRUCTURED
    )
    canonical = store.expand(
        observation.observation_id, "repo:alpha", DisclosureLevel.CANONICAL
    )
    hint = store.expand(
        observation.observation_id, "repo:alpha", DisclosureLevel.REVALIDATION_HINT
    )
    assert not hasattr(header, "native_payload")
    assert structured.canonical_pointer == observation.observation_id
    assert canonical == observation
    assert hint.requires_fresh_audit is True
    assert not hasattr(hint, "current_classification")
    store.close()


def test_freshness_and_lineage_events_are_append_only(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-05, AC-18."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    observation = _observation()
    store.write(observation)
    store.append_lineage_event(
        observation.lineage_id,
        observation.repository_id,
        observation.observation_id,
        LineageEventKind.RECONFIRMED,
    )
    events = store.lineage_events(observation.lineage_id, observation.repository_id)
    assert tuple(item.kind for item in events) == (
        LineageEventKind.OBSERVED,
        LineageEventKind.RECONFIRMED,
    )
    current = store.retrieve(MemoryRetrievalRequest("repo:alpha"))[0]
    assert current.freshness_state is FreshnessState.REVALIDATED
    store.close()


def test_disabled_and_unavailable_memory_are_controlled(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-21, AC-22."""
    disabled = MemoryService.disabled()
    assert disabled.retrieve(MemoryRetrievalRequest("repo:alpha")) == ()
    assert disabled.diagnostics == ()
    unavailable = MemoryService.open(tmp_path / "missing" / "memory.sqlite3")
    assert unavailable.retrieve(MemoryRetrievalRequest("repo:alpha")) == ()
    assert "MEMORY_STORE_UNAVAILABLE" in unavailable.diagnostics


def test_schema_enum_and_deterministic_json() -> None:
    """Spec: HERMES-0028 / AC-01, AC-04."""
    assert MemorySchemaVersion.V1.value == 1
    assert _observation().canonical_json() == _observation().canonical_json()


def test_indexes_can_be_rebuilt(tmp_path) -> None:
    """Spec: HERMES-0028 / AC-30."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    observation = _observation()
    store.write(observation)
    store._connection.execute("DELETE FROM memory_symbols")
    store._connection.commit()
    assert store.retrieve(MemoryRetrievalRequest("repo:alpha", symbols=("prepare",))) == ()
    store.rebuild_indexes()
    assert store.retrieve(MemoryRetrievalRequest("repo:alpha", symbols=("prepare",)))
    store.close()
