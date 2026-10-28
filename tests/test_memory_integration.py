"""Integration, dogfood, and frozen-core controls for HERMES-0028."""

from dataclasses import replace
from pathlib import Path
import sqlite3

from hermes_ops.memory import (
    DisclosureLevel,
    MemoryCandidate,
    MemoryKind,
    MemoryRetrievalRequest,
    MemoryService,
    MemoryStore,
    create_observation,
)
from hermes_ops.skills.finding_models import (
    CommonSeverity,
    EvidenceRef,
    EvidenceStrength,
    ProductionReachability,
    RankableFinding,
)
from hermes_ops.skills.finding_ranking import rank_findings, ranked_finding_json


def _observation(
    kind: MemoryKind,
    finding_kind: str,
    *,
    revision: str = "buggy",
    auditor: str = "persistence-contract-review",
):
    return create_observation(
        repository_id="repo:historical-fixture",
        source_revision=revision,
        snapshot_digest=f"sha256:{revision}",
        structural_scope=("services/operation.py",),
        canonical_request={"operation_symbol": "process", "target_table": "records"},
        source_auditor=auditor,
        auditor_version=1,
        normalizer_version=1,
        outcome_status="COMPLETED_WITH_FINDINGS" if kind is MemoryKind.CONFIRMED_FINDING else "COMPLETED_NO_FINDINGS",
        native_classification="CONFIRMED_CONTRACT_MISMATCH" if kind is MemoryKind.CONFIRMED_FINDING else "CONTRACT_STRUCTURALLY_ALIGNED",
        limitations=(),
        original_finding_id="sha256:historical" if kind is MemoryKind.CONFIRMED_FINDING else None,
        finding_kind=finding_kind,
        historical_severity="medium" if kind is MemoryKind.CONFIRMED_FINDING else None,
        historical_reachability="CONFIRMED",
        evidence_refs=(EvidenceRef("services/operation.py", 5, 5),),
        native_payload={"contract": finding_kind},
        memory_kind=kind,
        symbols=("process",),
        relative_paths=("services/operation.py",),
        retrieval_terms=("persistence", "state", finding_kind.lower()),
    )


def test_local_python_has_fts5_or_store_reports_fallback() -> None:
    """Spec: HERMES-0028 / AC-10, AC-11."""
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE VIRTUAL TABLE capability_check USING fts5(value)")
        available = True
    except sqlite3.Error:
        available = False
    finally:
        connection.close()
    service = MemoryService.open(":memory:")
    assert service.store is not None
    assert service.store.fts_available is available


def test_wrong_store_and_state_effect_dogfoods_are_retrievable(tmp_path: Path) -> None:
    """Spec: HERMES-0028 / AC-37, AC-38."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    wrong_store = _observation(MemoryKind.CONFIRMED_FINDING, "TARGET_TABLE_MISMATCH")
    state_effect = _observation(
        MemoryKind.CONFIRMED_FINDING,
        "STATE_EFFECT_COVERAGE_MISMATCH",
        auditor="state-guard-effect-review",
    )
    store.write(wrong_store)
    store.write(state_effect)
    assert store.retrieve(MemoryRetrievalRequest(
        "repo:historical-fixture", finding_kinds=("TARGET_TABLE_MISMATCH",)
    ))[0].observation_id == wrong_store.observation_id
    assert store.retrieve(MemoryRetrievalRequest(
        "repo:historical-fixture", finding_kinds=("STATE_EFFECT_COVERAGE_MISMATCH",)
    ))[0].observation_id == state_effect.observation_id
    store.close()


def test_aligned_revalidation_shares_lineage_and_cannot_suppress_fresh_result(tmp_path: Path) -> None:
    """Spec: HERMES-0028 / AC-20, AC-39."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    buggy = _observation(MemoryKind.CONFIRMED_FINDING, "TARGET_TABLE_MISMATCH")
    fixed = _observation(
        MemoryKind.ALIGNED_REVALIDATION, "TARGET_TABLE_MISMATCH", revision="fixed"
    )
    assert buggy.lineage_id == fixed.lineage_id
    store.write(buggy)
    store.write(fixed, revalidation=True)
    candidates = store.retrieve(MemoryRetrievalRequest(
        "repo:historical-fixture", lineage_id=buggy.lineage_id
    ))
    assert {item.observation_id for item in candidates} == {
        buggy.observation_id, fixed.observation_id,
    }
    fresh_core_finding = RankableFinding(
        1, "fresh-current", "persistence-contract-review", "Fresh mismatch.",
        CommonSeverity.MEDIUM, EvidenceStrength.CONFIRMED,
        ProductionReachability.CONFIRMED, (EvidenceRef("services/operation.py", 9, 9),),
        "fresh",
    )
    assert rank_findings((fresh_core_finding,)).top_finding == fresh_core_finding
    store.close()


def test_path_only_dogfood_requires_structural_value(tmp_path: Path) -> None:
    """Spec: HERMES-0028 / AC-27, AC-36."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    path_only = _observation(MemoryKind.PATH_ONLY_OBSERVATION, "PATH_ONLY")
    store.write(path_only)
    candidate = store.retrieve(MemoryRetrievalRequest(
        "repo:historical-fixture", symbols=("process",)
    ))[0]
    hint = store.expand(candidate.observation_id, candidate.repository_id, DisclosureLevel.REVALIDATION_HINT)
    assert hint.requires_fresh_audit is True
    assert type(candidate) is MemoryCandidate
    assert not isinstance(candidate, RankableFinding)
    store.close()


def test_memory_presence_does_not_change_core_ranking_json(tmp_path: Path) -> None:
    """Spec: HERMES-0028 / AC-13, AC-19, AC-22, AC-24."""
    finding = RankableFinding(
        1, "core-invariant", "execution-path-review", "Core remains authoritative.",
        CommonSeverity.LOW, EvidenceStrength.PARTIAL,
        ProductionReachability.UNKNOWN, (EvidenceRef("src/flow.py", 1, 1),), "core",
    )
    before = ranked_finding_json(rank_findings((finding,)))
    with MemoryStore(tmp_path / "memory.sqlite3") as store:
        store.write(_observation(MemoryKind.CONFIRMED_FINDING, "HISTORICAL"))
    after = ranked_finding_json(rank_findings((finding,)))
    assert before == after


def test_corrupt_store_falls_back_without_core_exception(tmp_path: Path) -> None:
    """Spec: HERMES-0028 / AC-21, AC-29."""
    path = tmp_path / "memory.sqlite3"
    path.write_bytes(b"not sqlite")
    service = MemoryService.open(path)
    assert service.store is None
    assert service.retrieve(MemoryRetrievalRequest("repo:alpha")) == ()
    assert service.diagnostics == ("MEMORY_STORE_CORRUPT",)


def test_hundreds_of_observations_retrieve_deterministically(tmp_path: Path) -> None:
    """Spec: HERMES-0028 / AC-12, AC-31."""
    store = MemoryStore(tmp_path / "memory.sqlite3")
    for index in range(120):
        item = create_observation(
            repository_id="repo:scale", source_revision=f"rev-{index}",
            snapshot_digest=f"sha256:s{index}", structural_scope=("src/flow.py",),
            canonical_request={"symbol": f"symbol_{index}"}, source_auditor="code-audit",
            auditor_version=1, normalizer_version=1,
            outcome_status="COMPLETED_WITH_FINDINGS", native_classification="OBSERVED",
            limitations=(), original_finding_id=f"finding-{index}", finding_kind="RULE",
            historical_severity="low", historical_reachability="UNKNOWN",
            evidence_refs=(EvidenceRef("src/flow.py", index + 1, index + 1),),
            native_payload={"index": index}, memory_kind=MemoryKind.CONFIRMED_FINDING,
            symbols=(f"symbol_{index}",), relative_paths=("src/flow.py",),
            retrieval_terms=("rule",),
        )
        store.write(item)
    request = MemoryRetrievalRequest("repo:scale", relative_paths=("src/flow.py",), max_candidates=100)
    first = store.retrieve(request)
    second = store.retrieve(request)
    assert first == second and len(first) == 100
    store.close()


def test_memory_production_has_no_consumer_hardcode_or_private_auditor_imports() -> None:
    """Spec: HERMES-0028 / AC-23, AC-35."""
    root = Path(__file__).parents[1] / "src" / "hermes_ops" / "memory"
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in root.glob("*.py"))
    forbidden = (
        "lucre", "olt", "kumon", "trello", "whatsapp", "awaiting_client_type",
        "c:\\users\\", "_originfact", "_domainfact", "mutationintentfact",
    )
    assert not any(item in text for item in forbidden)
