"""Freshness and SQLite ownership contracts for HERMES-0029."""

from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

from hermes_ops.memory import (
    FreshnessState,
    LineageEventKind,
    MemoryCurrentContext,
    MemoryError,
    MemoryKind,
    MemoryRetrievalRequest,
    MemoryService,
    MemoryStore,
    create_observation,
    derive_memory_freshness,
)
from hermes_ops.skills.finding_models import EvidenceRef


def _observation(*, revision: str = "rev-a", snapshot: str | None = "sha256:a", index: int = 0):
    return create_observation(
        repository_id="repo:freshness", source_revision=revision,
        snapshot_digest=snapshot, structural_scope=(f"src/flow_{index}.py",),
        canonical_request={"symbol": f"operation_{index}"},
        source_auditor="execution-path-review", auditor_version=1,
        normalizer_version=1, outcome_status="COMPLETED_WITH_FINDINGS",
        native_classification="CONFIRMED_CONTRACT_MISMATCH", limitations=(),
        original_finding_id=f"finding-{index}", finding_kind="CONTRACT_MISMATCH",
        historical_severity="medium", historical_reachability="CONFIRMED",
        evidence_refs=(EvidenceRef(f"src/flow_{index}.py", 1, 1),),
        native_payload={"index": index}, memory_kind=MemoryKind.CONFIRMED_FINDING,
        symbols=(f"operation_{index}",), relative_paths=(f"src/flow_{index}.py",),
        retrieval_terms=("contract", f"operation_{index}"),
    )


def _context(*, revision: str | None = "rev-b", snapshot: str | None = "sha256:b"):
    return MemoryCurrentContext("repo:freshness", revision, snapshot, ("src",))


def test_current_context_is_optional_and_repository_bound() -> None:
    """Spec: HERMES-0029 / AC-01, AC-02."""
    assert MemoryRetrievalRequest("repo:freshness").current_context is None
    with pytest.raises(MemoryError) as caught:
        MemoryRetrievalRequest(
            "repo:freshness", current_context=MemoryCurrentContext("repo:other")
        )
    assert caught.value.code == "MEMORY_REPOSITORY_MISMATCH"


@pytest.mark.parametrize(
    ("observation", "context", "expected"),
    (
        (_observation(), _context(revision="rev-z", snapshot="sha256:a"), FreshnessState.SAME_SNAPSHOT_CANDIDATE),
        (_observation(), _context(), FreshnessState.STALE_CANDIDATE),
        (_observation(snapshot=None), _context(snapshot=None), FreshnessState.STALE_CANDIDATE),
        (_observation(snapshot=None), _context(revision="rev-a", snapshot=None), FreshnessState.CURRENTLY_UNVERIFIED),
        (_observation(), _context(revision="rev-a", snapshot="sha256:b"), FreshnessState.STALE_CANDIDATE),
        (_observation(), _context(revision=None, snapshot=None), FreshnessState.CURRENTLY_UNVERIFIED),
        (_observation(), None, FreshnessState.CURRENTLY_UNVERIFIED),
    ),
)
def test_pure_freshness_decision_table(observation, context, expected) -> None:
    """Spec: HERMES-0029 / AC-03-AC-08, AC-12."""
    assert derive_memory_freshness(observation, context, None) is expected
    assert derive_memory_freshness(observation, context, None) is expected


@pytest.mark.parametrize(
    ("lineage", "expected"),
    (
        (LineageEventKind.RECONFIRMED, FreshnessState.REVALIDATED),
        (LineageEventKind.NOT_REPRODUCED, FreshnessState.NOT_REPRODUCED),
        (LineageEventKind.SUPERSEDED, FreshnessState.SUPERSEDED),
    ),
)
def test_explicit_lineage_precedes_provenance(lineage, expected) -> None:
    """Spec: HERMES-0029 / AC-11, AC-12."""
    assert derive_memory_freshness(_observation(), _context(), lineage) is expected


def test_retrieval_freshness_changes_metadata_not_score_or_order(tmp_path: Path) -> None:
    """Spec: HERMES-0029 / AC-09, AC-10, AC-19, AC-21, AC-24."""
    with MemoryStore(tmp_path / "memory.sqlite3") as store:
        for index in range(4):
            store.write(_observation(index=index))
        base = MemoryRetrievalRequest("repo:freshness", mission_terms=("contract",))
        current = replace(base, current_context=_context())
        before = store.retrieve(base)
        after = store.retrieve(current)
    assert [(x.observation_id, x.retrieval_score) for x in before] == [
        (x.observation_id, x.retrieval_score) for x in after
    ]
    assert {x.freshness_state for x in before} == {FreshnessState.CURRENTLY_UNVERIFIED}
    assert {x.freshness_state for x in after} == {FreshnessState.STALE_CANDIDATE}


def test_revalidation_is_projected_to_its_explicit_observation(tmp_path: Path) -> None:
    """Spec: HERMES-0029 / AC-11."""
    historical = _observation()
    aligned = create_observation(
        repository_id=historical.repository_id, source_revision="rev-b",
        snapshot_digest="sha256:b", structural_scope=historical.structural_scope,
        canonical_request=historical.canonical_request,
        source_auditor=historical.source_auditor, auditor_version=1,
        normalizer_version=1, outcome_status="COMPLETED_NO_FINDINGS",
        native_classification="CONTRACT_STRUCTURALLY_ALIGNED", limitations=(),
        original_finding_id=None, finding_kind=historical.finding_kind,
        historical_severity=None, historical_reachability=None,
        evidence_refs=historical.evidence_refs, native_payload={"index": 0},
        memory_kind=MemoryKind.ALIGNED_REVALIDATION, symbols=historical.symbols,
        relative_paths=historical.relative_paths, retrieval_terms=historical.retrieval_terms,
    )
    assert historical.lineage_id == aligned.lineage_id
    with MemoryStore(tmp_path / "lineage.sqlite3") as store:
        store.write(historical)
        store.write(aligned, revalidation=True)
        store.append_lineage_event(
            aligned.lineage_id, aligned.repository_id, aligned.observation_id,
            LineageEventKind.RECONFIRMED,
        )
        results = store.retrieve(MemoryRetrievalRequest(
            "repo:freshness", lineage_id=historical.lineage_id,
            current_context=_context(),
        ))
    by_id = {item.observation_id: item for item in results}
    assert by_id[historical.observation_id].freshness_state is FreshnessState.STALE_CANDIDATE
    assert by_id[aligned.observation_id].freshness_state is FreshnessState.REVALIDATED


def test_expanded_hermetic_corpus_blind_queries_and_determinism(tmp_path: Path) -> None:
    """Spec: HERMES-0029 / AC-20, AC-21, AC-25, AC-26."""
    observations = tuple(
        _observation(
            revision="rev-current" if index % 3 == 0 else f"rev-{index}",
            snapshot="sha256:current" if index % 3 == 0 else f"sha256:{index}",
            index=index,
        )
        for index in range(24)
    )
    with MemoryStore(tmp_path / "expanded.sqlite3") as store:
        for observation in observations:
            store.write(observation)
        context = MemoryCurrentContext(
            "repo:freshness", "rev-current", "sha256:current", ("src",)
        )
        requests = tuple(
            MemoryRetrievalRequest(
                "repo:freshness", symbols=(f"operation_{index}",),
                current_context=context,
            )
            for index in range(10)
        )
        first = tuple(store.retrieve(request) for request in requests)
        second = tuple(store.retrieve(request) for request in requests)
        isolated = store.retrieve(MemoryRetrievalRequest("repo:other"))
    assert first == second
    assert isolated == ()
    assert all(len(results) == 1 for results in first)
    assert all(results[0].observation_id == observations[index].observation_id
               for index, results in enumerate(first))
    assert all(results[0].retrieval_score == 100 for results in first)
    assert all(results[0].freshness_state is (
        FreshnessState.SAME_SNAPSHOT_CANDIDATE
        if index % 3 == 0 else FreshnessState.STALE_CANDIDATE
    ) for index, results in enumerate(first))


def test_original_four_dogfoods_preserve_top_one_score_and_order(tmp_path: Path) -> None:
    """Spec: HERMES-0029 / AC-09, AC-24."""
    families = (
        ("persist_record", "TARGET_TABLE_MISMATCH", "persistence-contract-review"),
        ("apply_state", "STATE_EFFECT_COVERAGE_MISMATCH", "state-guard-effect-review"),
        ("trace_flow", "PATH_ONLY", "execution-path-review"),
        ("corrected_flow", "ALIGNED", "execution-path-review"),
    )
    observations = []
    with MemoryStore(tmp_path / "original.sqlite3") as store:
        for index, (symbol, finding_kind, auditor) in enumerate(families):
            kind = (
                MemoryKind.PATH_ONLY_OBSERVATION if finding_kind == "PATH_ONLY"
                else MemoryKind.ALIGNED_REVALIDATION if finding_kind == "ALIGNED"
                else MemoryKind.CONFIRMED_FINDING
            )
            observation = create_observation(
                repository_id="repo:original-dogfood",
                source_revision="rev-b" if kind is MemoryKind.ALIGNED_REVALIDATION else "rev-a",
                snapshot_digest="sha256:b" if kind is MemoryKind.ALIGNED_REVALIDATION else "sha256:a",
                structural_scope=(f"services/{symbol}.py",),
                canonical_request={"symbol": symbol}, source_auditor=auditor,
                auditor_version=1, normalizer_version=1,
                outcome_status="COMPLETED_NO_FINDINGS" if kind is MemoryKind.ALIGNED_REVALIDATION else "COMPLETED_WITH_FINDINGS",
                native_classification="ALIGNED" if kind is MemoryKind.ALIGNED_REVALIDATION else "HISTORICAL",
                limitations=(), original_finding_id=None if kind is not MemoryKind.CONFIRMED_FINDING else f"finding-{index}",
                finding_kind=finding_kind, historical_severity="medium" if kind is MemoryKind.CONFIRMED_FINDING else None,
                historical_reachability="CONFIRMED" if kind is MemoryKind.CONFIRMED_FINDING else None,
                evidence_refs=(EvidenceRef(f"services/{symbol}.py", 1, 1),),
                native_payload={"family": index}, memory_kind=kind, symbols=(symbol,),
                relative_paths=(f"services/{symbol}.py",),
                retrieval_terms=("historical", f"scenario{index}"),
            )
            store.write(
                observation,
                revalidation=kind is MemoryKind.ALIGNED_REVALIDATION,
            )
            if kind is MemoryKind.ALIGNED_REVALIDATION:
                store.append_lineage_event(
                    observation.lineage_id, observation.repository_id,
                    observation.observation_id, LineageEventKind.RECONFIRMED,
                )
            observations.append(observation)
        store.write(create_observation(
            repository_id="repo:original-dogfood", source_revision="noise",
            snapshot_digest="sha256:noise", structural_scope=("services/noise.py",),
            canonical_request={"symbol": "noise"}, source_auditor="code-audit",
            auditor_version=1, normalizer_version=1,
            outcome_status="COMPLETED_WITH_FINDINGS", native_classification="NOISE",
            limitations=(), original_finding_id="noise", finding_kind="NOISE",
            historical_severity="low", historical_reachability="UNKNOWN",
            evidence_refs=(EvidenceRef("services/noise.py", 1, 1),),
            native_payload={"noise": True}, memory_kind=MemoryKind.CONFIRMED_FINDING,
            symbols=("noise",), relative_paths=("services/noise.py",),
            retrieval_terms=("irrelevant",),
        ))
        context = MemoryCurrentContext(
            "repo:original-dogfood", "rev-b", "sha256:b", ("services",)
        )
        results = tuple(store.retrieve(MemoryRetrievalRequest(
            "repo:original-dogfood", symbols=(symbol,), auditor_kinds=(auditor,),
            mission_terms=("historical", f"scenario{index}"), current_context=context,
        )) for index, (symbol, _kind, auditor) in enumerate(families))
    assert all(result[0].observation_id == observations[index].observation_id
               for index, result in enumerate(results))
    assert all(result[0].retrieval_score == 160 for result in results)
    assert all(len(result) == 1 for result in results)
    assert tuple(result[0].freshness_state for result in results) == (
        FreshnessState.STALE_CANDIDATE,
        FreshnessState.STALE_CANDIDATE,
        FreshnessState.STALE_CANDIDATE,
        FreshnessState.REVALIDATED,
    )


def _assert_path_reusable(path: Path) -> None:
    renamed = path.with_suffix(".reusable")
    path.replace(renamed)
    renamed.replace(path)
    path.unlink()
    path.write_bytes(b"reused")


def test_corrupt_and_future_schema_failures_release_file(tmp_path: Path) -> None:
    """Spec: HERMES-0029 / AC-13-AC-15, AC-18."""
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not sqlite")
    service = MemoryService.open(corrupt)
    assert service.store is None and service.diagnostics == ("MEMORY_STORE_CORRUPT",)
    _assert_path_reusable(corrupt)

    future = tmp_path / "future.sqlite3"
    MemoryStore(future).close()
    connection = sqlite3.connect(future)
    connection.execute("UPDATE memory_meta SET value = '99' WHERE key = 'schema_version'")
    connection.commit()
    connection.close()
    with pytest.raises(MemoryError) as caught:
        MemoryStore(future)
    assert caught.value.code == "MEMORY_SCHEMA_UNSUPPORTED"
    _assert_path_reusable(future)


def test_injected_initialization_failures_close_connection(tmp_path: Path, monkeypatch) -> None:
    """Spec: HERMES-0029 / AC-13, AC-16."""
    path = tmp_path / "injected.sqlite3"

    def fail_migration(_store) -> None:
        raise MemoryError("MEMORY_STORE_CORRUPT", "injected migration failure")

    monkeypatch.setattr(MemoryStore, "_migrate", fail_migration)
    with pytest.raises(MemoryError) as caught:
        MemoryStore(path)
    assert caught.value.code == "MEMORY_STORE_CORRUPT"
    _assert_path_reusable(path)


def test_unexpected_fts_initialization_failure_closes_connection(tmp_path: Path, monkeypatch) -> None:
    """Spec: HERMES-0029 / AC-13."""
    path = tmp_path / "fts.sqlite3"

    def fail_fts(_store) -> bool:
        raise RuntimeError("injected FTS initialization failure")

    monkeypatch.setattr(MemoryStore, "_enable_fts", fail_fts)
    with pytest.raises(RuntimeError, match="injected FTS"):
        MemoryStore(path)
    _assert_path_reusable(path)


def test_close_is_idempotent_and_closed_store_never_reopens(tmp_path: Path) -> None:
    """Spec: HERMES-0029 / AC-17."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.close()
    store.close()
    with pytest.raises(MemoryError) as caught:
        store.retrieve(MemoryRetrievalRequest("repo:freshness"))
    assert caught.value.code == "MEMORY_STORE_UNAVAILABLE"
