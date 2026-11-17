"""Contract tests for HERMES-0033 legacy privacy and compatibility."""
from pathlib import Path
from dataclasses import replace
import pytest

from hermes_ops.memory.core import create_observation, inspect_observation_privacy
from hermes_ops.memory.models import DisclosureLevel, LegacyPrivacyState, LineageEventKind, MemoryError, MemoryKind
from hermes_ops.memory.store import MemoryService, migrate_memory_observation_privacy


def legacy(payload, *, repository_id="legacy-repo"):
    return create_observation(
        repository_id=repository_id, source_revision="old", snapshot_digest="old-digest",
        structural_scope=("source.py",), canonical_request={"auditor": "code-audit"},
        source_auditor="code-audit", auditor_version=1, normalizer_version=1,
        outcome_status="COMPLETED_WITH_FINDINGS", original_finding_id="CA001:source.py:1:1",
        finding_kind="CA001", historical_severity="HIGH", historical_reachability="DIRECT",
        native_payload=payload, memory_kind=MemoryKind.CONFIRMED_FINDING,
        symbols=(), relative_paths=("source.py",), retrieval_terms=("CA001",),
    )


def test_unsafe_legacy_canonical_is_blocked(tmp_path: Path) -> None:
    """Spec: HERMES-0033 / AC-03 (first RED)."""
    observation = legacy({"evidence": "return eval(payload)"})
    with MemoryService.open(tmp_path / "memory.sqlite3") as service:
        assert service.store is not None and service.store.write(observation)
        with pytest.raises(MemoryError) as error:
            service.store.expand(observation.observation_id, "legacy-repo", DisclosureLevel.CANONICAL)
    assert error.value.code == "MEMORY_LEGACY_CANONICAL_BLOCKED"


def test_explicit_migration_api_exists() -> None:
    """Spec: HERMES-0033 / AC-06 (second RED)."""
    import hermes_ops.memory as memory
    assert hasattr(memory, "migrate_memory_observation_privacy")


@pytest.mark.parametrize(("payload", "expected"), [
    ({"finding_kind": "CA001"}, LegacyPrivacyState.LEGACY_SAFE_VERIFIED),
    ({"mystery": "opaque"}, LegacyPrivacyState.LEGACY_UNVERIFIED),
    ({"password": "fixture-value"}, LegacyPrivacyState.LEGACY_UNSAFE),
    ({"relative_paths": ["C:\\Users\\Example\\source.py"]}, LegacyPrivacyState.LEGACY_UNSAFE),
])
def test_legacy_privacy_classification_is_closed_and_deterministic(payload, expected) -> None:
    """Spec: HERMES-0033 / AC-01, AC-03."""
    try:
        observation = legacy(payload)
    except MemoryError:
        observation = replace(legacy({"finding_kind": "CA001"}), native_payload=payload)
    assert inspect_observation_privacy(observation) is expected
    assert inspect_observation_privacy(observation) is expected


def test_current_complete_shape_and_safe_legacy_disclosures(tmp_path: Path) -> None:
    """Spec: HERMES-0033 / AC-02 through AC-04."""
    current = legacy({
        "source_skill": "code-audit", "finding_id": "CA001:source.py:1:1",
        "finding_kind": "CA001", "severity": "HIGH", "evidence_strength": "DIRECT",
        "production_reachability": "DIRECT", "evidence_refs": [],
    })
    safe = legacy({"finding_kind": "CA001"}, repository_id="safe-repo")
    assert inspect_observation_privacy(current) is LegacyPrivacyState.CURRENT_SAFE
    with MemoryService.open(tmp_path / "memory.sqlite3") as service:
        assert service.store is not None
        assert service.store.write(current) and service.store.write(safe)
        assert service.store.expand(safe.observation_id, "safe-repo", DisclosureLevel.CANONICAL) == safe


def test_unsafe_header_structured_safe_and_hint_requires_fresh(tmp_path: Path) -> None:
    """Spec: HERMES-0033 / AC-03, AC-04."""
    source = legacy({"evidence": "return eval(payload)"})
    with MemoryService.open(tmp_path / "memory.sqlite3") as service:
        assert service.store is not None and service.store.write(source)
        header = service.store.expand(source.observation_id, "legacy-repo", DisclosureLevel.HEADER)
        structured = service.store.expand(source.observation_id, "legacy-repo", DisclosureLevel.STRUCTURED)
        hint = service.store.expand(source.observation_id, "legacy-repo", DisclosureLevel.REVALIDATION_HINT)
    combined = repr((header, structured, hint))
    assert "eval(payload)" not in combined
    assert header.privacy_state is LegacyPrivacyState.LEGACY_UNSAFE
    assert header.canonical_available is False and hint.requires_fresh_audit is True


def test_explicit_append_only_migration_preserves_lineage_and_is_idempotent(tmp_path: Path) -> None:
    """Spec: HERMES-0033 / AC-06."""
    source = legacy({"evidence": "return eval(payload)"})
    with MemoryService.open(tmp_path / "memory.sqlite3") as service:
        assert service.store is not None and service.store.write(source)
        first = migrate_memory_observation_privacy(service.store, source.observation_id, "legacy-repo")
        second = migrate_memory_observation_privacy(service.store, source.observation_id, "legacy-repo")
        migrated = service.store.expand(first.migrated_observation_id, "legacy-repo", DisclosureLevel.CANONICAL)
        events = service.store.lineage_events(source.lineage_id, "legacy-repo")
        with pytest.raises(MemoryError):
            service.store.expand(source.observation_id, "legacy-repo", DisclosureLevel.CANONICAL)
    assert first.created is True and second.created is False
    assert first.migrated_observation_id == second.migrated_observation_id != source.observation_id
    assert first.lineage_id == source.lineage_id == migrated.lineage_id
    assert "eval(payload)" not in migrated.canonical_json()
    assert sum(event.kind is LineageEventKind.PRIVACY_MIGRATED for event in events) == 1
    assert sum(event.kind is LineageEventKind.QUARANTINED for event in events) == 1


def test_migration_refuses_unsafe_request_and_preserves_original(tmp_path: Path) -> None:
    """Spec: HERMES-0033 / AC-07."""
    source = legacy({"mystery": "opaque"})
    source = create_observation(**{
        "repository_id": source.repository_id, "source_revision": source.source_revision,
        "snapshot_digest": source.snapshot_digest, "structural_scope": source.structural_scope,
        "canonical_request": {"example": "return eval(payload)"},
        "source_auditor": source.source_auditor, "auditor_version": source.auditor_version,
        "normalizer_version": source.normalizer_version, "outcome_status": source.outcome_status,
        "original_finding_id": source.original_finding_id, "finding_kind": source.finding_kind,
        "historical_severity": source.historical_severity,
        "historical_reachability": source.historical_reachability,
        "native_payload": source.native_payload, "memory_kind": source.memory_kind,
        "symbols": source.symbols, "relative_paths": source.relative_paths,
        "retrieval_terms": source.retrieval_terms,
    })
    with MemoryService.open(tmp_path / "memory.sqlite3") as service:
        assert service.store is not None and service.store.write(source)
        with pytest.raises(MemoryError) as error:
            migrate_memory_observation_privacy(service.store, source.observation_id, "legacy-repo")
        assert service.store._load(source.observation_id, "legacy-repo").observation_id == source.observation_id
    assert error.value.code == "MEMORY_LEGACY_MIGRATION_UNSAFE"
