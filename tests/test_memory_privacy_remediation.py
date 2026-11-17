"""Privacy contract tests for HERMES-0030 native-payload remediation."""

from pathlib import Path

import pytest

from hermes_ops.memory import (
    DisclosureLevel, MemoryError, MemoryRetrievalRequest, MemoryStore,
    observation_from_rankable_finding, sanitize_memory_payload,
)
from hermes_ops.memory.core import canonical_digest
from hermes_ops.skills.finding_models import (
    CommonSeverity, EvidenceRef, EvidenceStrength, ProductionReachability,
    RankableFinding,
)


SOURCE_LINE = "return eval(payload)"
MULTILINE = "def dangerous(payload):\n    return eval(payload)\n"


def _finding(payload: object = None) -> RankableFinding:
    return RankableFinding(
        1,
        "finding:privacy",
        "code-audit",
        MULTILINE,
        CommonSeverity.HIGH,
        EvidenceStrength.PARTIAL,
        ProductionReachability.UNKNOWN,
        (EvidenceRef("repo.py", 2, 2, 12, 16),),
        payload if payload is not None else {"evidence": SOURCE_LINE, "secret": "value"},
    )


def _observation(payload: object = None):
    return observation_from_rankable_finding(
        _finding(payload),
        repository_id="privacy-repo",
        canonical_request={"auditor_id": "code-audit"},
        source_revision="revision-1",
        snapshot_digest="sha256:snapshot",
        structural_scope=("repo.py",),
        auditor_version=1,
        normalizer_version=1,
        limitations=(),
        finding_kind="code-audit",
        symbols=(),
    )


def test_confirmed_payload_is_closed_structural_metadata() -> None:
    """Spec: HERMES-0030 privacy / requirements 1-8, 13."""
    observation = _observation()
    encoded = observation.canonical_json()
    assert SOURCE_LINE not in encoded and MULTILINE not in encoded
    assert observation.native_payload == {
        "evidence_refs": [{
            "path": "repo.py", "start_line": 2, "end_line": 2,
            "start_column": 12, "end_column": 16,
        }],
        "evidence_strength": "PARTIAL",
        "finding_id": "finding:privacy",
        "finding_kind": "code-audit",
        "production_reachability": "UNKNOWN",
        "severity": "high",
        "source_skill": "code-audit",
    }
    assert observation.original_finding_id == "finding:privacy"
    assert observation.source_auditor == "code-audit"
    assert observation.historical_severity == "high"
    assert observation.historical_reachability == "UNKNOWN"
    assert observation.finding_kind == "code-audit"
    assert observation.evidence_refs == (EvidenceRef("repo.py", 2, 2, 12, 16),)
    assert observation.payload_digest == canonical_digest(observation.native_payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"relative_paths": (r"C:\\private\\source.py",)},
        {"password": "secret"},
        {"severity": object()},
        {"metadata": {"source": SOURCE_LINE}},
        {"finding_kind": SOURCE_LINE},
    ],
)
def test_closed_sanitizer_rejects_unsafe_or_unknown_payload(payload: object) -> None:
    """Spec: HERMES-0030 privacy / requirements 9-12."""
    with pytest.raises(MemoryError) as error:
        sanitize_memory_payload(payload)
    assert error.value.code == "MEMORY_RECORD_UNSAFE"


def test_sanitized_identity_is_deterministic_and_ignores_unsafe_native_payload() -> None:
    """Spec: HERMES-0030 privacy / requirements 14, 16."""
    first = _observation({"evidence": SOURCE_LINE})
    second = _observation({"source_block": MULTILINE})
    assert first.native_payload == second.native_payload
    assert first.payload_digest == second.payload_digest
    assert first.observation_id == second.observation_id
    assert first.lineage_id == second.lineage_id
    assert first.canonical_json() == second.canonical_json()


def test_duplicate_sanitized_observation_is_idempotent(tmp_path: Path) -> None:
    """Spec: HERMES-0030 privacy / requirement 15."""
    observation = _observation()
    with MemoryStore(tmp_path / "memory.db") as store:
        assert store.write(observation) is True
        assert store.write(observation) is False
        assert len(store.lineage_events(observation.lineage_id, "privacy-repo")) == 1


def test_all_progressive_disclosures_exclude_source(tmp_path: Path) -> None:
    """Spec: HERMES-0030 privacy / requirements 17-20."""
    observation = _observation()
    with MemoryStore(tmp_path / "memory.db") as store:
        assert store.write(observation)
        candidate = store.retrieve(MemoryRetrievalRequest(
            repository_id="privacy-repo", observation_id=observation.observation_id,
        ))[0]
        values = (
            candidate,
            store.expand(observation.observation_id, "privacy-repo", DisclosureLevel.STRUCTURED),
            store.expand(observation.observation_id, "privacy-repo", DisclosureLevel.CANONICAL),
            store.expand(observation.observation_id, "privacy-repo", DisclosureLevel.REVALIDATION_HINT),
        )
        encoded = tuple(
            item.canonical_json() if hasattr(item, "canonical_json") else repr(item)
            for item in values
        )
    assert all(SOURCE_LINE not in item and MULTILINE not in item for item in encoded)


def test_new_payload_keeps_retrieval_dimensions(tmp_path: Path) -> None:
    """Spec: HERMES-0030 privacy / confirmed write-back regression."""
    observation = _observation()
    with MemoryStore(tmp_path / "memory.db") as store:
        assert store.write(observation)
        for request in (
            MemoryRetrievalRequest(repository_id="privacy-repo", finding_kinds=("code-audit",)),
            MemoryRetrievalRequest(repository_id="privacy-repo", relative_paths=("repo.py",)),
            MemoryRetrievalRequest(repository_id="privacy-repo", auditor_kinds=("code-audit",)),
        ):
            assert store.retrieve(request)[0].observation_id == observation.observation_id
