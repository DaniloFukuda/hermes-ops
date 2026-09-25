from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import socket
import subprocess

import pytest

from hermes_ops.execution import (
    CheckpointReason,
    CheckpointTestResult,
    ExecutedAction,
    ExecutionBudget,
    ExecutionCheckpoint,
    ExecutionContext,
    InspectedResource,
    RepositoryCheckpointState,
    create_execution_checkpoint,
)
from hermes_ops.execution.checkpoint import MAX_ITEMS, MAX_TEXT_LENGTH, SCHEMA_VERSION


def context(*, used: int = 3) -> ExecutionContext:
    return ExecutionContext(ExecutionBudget(12, used, 2, 2, 4, 7))


def checkpoint(**overrides: object) -> ExecutionCheckpoint:
    values: dict[str, object] = {
        "reason": CheckpointReason.MANUAL,
        "objective": "Finish checkpoint domain",
        "phase": "implementation",
        "repository_state": RepositoryCheckpointState(
            r"C:\work\hermes", "feature/checkpoint", "abc123", "clean"
        ),
        "modified_files": ["src/a.py"],
        "inspected_resources": [InspectedResource("file", "src/a.py", "1-20")],
        "executed_actions": [ExecutedAction("edit", "src/a.py", "ok", 1)],
        "test_results": [CheckpointTestResult("tests/test_a.py", "passed", 2, 0, 1, 0)],
        "known_failures": ["one known failure"],
        "remaining_items": ["run full suite"],
        "recommended_next_action": "Run the focused test.",
    }
    values.update(overrides)
    return create_execution_checkpoint(context(), **values)  # type: ignore[arg-type]


def test_checkpoint_contains_required_traceable_fields() -> None:
    """Spec: HERMES-0011 / AC-19, AC-61."""
    value = checkpoint()
    assert value.objective == "Finish checkpoint domain"
    assert value.reason is CheckpointReason.MANUAL
    assert value.repository_state is not None
    assert value.recommended_next_action == "Run the focused test."


def test_checkpoint_preserves_repository_snapshot() -> None:
    """Spec: HERMES-0011 / AC-11."""
    supplied = RepositoryCheckpointState("/repo", "feature/x", "deadbeef", "M a.py")
    value = checkpoint(repository_state=supplied)
    assert value.repository_state == RepositoryCheckpointState(
        "<PROJECT_ROOT>", "feature/x", "deadbeef", "M a.py"
    )
    assert supplied.repository_root == "/repo"


def test_checkpoint_is_frozen_and_deeply_immutable() -> None:
    """Spec: HERMES-0011 / AC-06, AC-62."""
    source = ["first"]
    value = checkpoint(remaining_items=source)
    source.append("later mutation")
    assert value.remaining_items.items == ("first",)
    with pytest.raises(FrozenInstanceError):
        value.phase = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        value.remaining_items.items[0] = "changed"  # type: ignore[index]


def test_checkpoint_snapshots_budget_without_changing_context() -> None:
    """Spec: HERMES-0011 / AC-63."""
    original = context(used=5)
    value = create_execution_checkpoint(original, reason=CheckpointReason.HANDOFF)
    assert value.budget_snapshot.used_units == 5
    assert value.budget_snapshot.remaining == 7
    assert value.budget_snapshot.validation_reserve == 2
    assert original.budget.used_units == 5


def test_checkpoint_json_and_markdown_are_deterministic() -> None:
    """Spec: HERMES-0011 / AC-20, AC-64."""
    first = checkpoint()
    second = checkpoint()
    assert first.to_json() == second.to_json()
    assert first.to_markdown() == second.to_markdown()
    assert json.loads(first.to_json()) == first.to_dict()


def test_checkpoint_generation_has_no_external_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0011 / AC-21, AC-65."""
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("external effect attempted")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "iterdir", forbidden)
    value = checkpoint()
    assert value.repository_state is not None


@pytest.mark.parametrize("render", [lambda value: value.to_json(), lambda value: value.to_markdown(), repr])
def test_public_handoff_is_sanitized_bounded_and_has_no_sensitive_content(render) -> None:
    """Spec: HERMES-0011 / AC-07, AC-29, AC-66."""
    secrets = "TOKEN_TESTE_SECRETO Authorization: Bearer TEST PRIVATE_KEY_TEST senha_teste"
    value = checkpoint(
        objective=secrets,
        modified_files=[r"C:\work\hermes\.env"],
        known_failures=[f"password=bad {secrets}"],
        recommended_next_action=f"token: abc {secrets}",
    )
    output = render(value)
    for secret in ("TOKEN_TESTE_SECRETO", "Bearer TEST", "PRIVATE_KEY_TEST", "senha_teste", "password=bad", ".env"):
        assert secret not in output
    assert r"C:\work\hermes" not in output
    if render is not repr:
        assert "<REDACTED>" in output


def test_all_collections_are_limited_and_report_omissions() -> None:
    """Spec: HERMES-0011 / AC-67."""
    many = [f"item-{index}" for index in range(MAX_ITEMS + 7)]
    value = checkpoint(
        modified_files=many,
        inspected_resources=[InspectedResource("file", item) for item in many],
        executed_actions=[ExecutedAction("read", item, "ok", 1) for item in many],
        test_results=[CheckpointTestResult(item, "passed") for item in many],
        known_failures=many,
        remaining_items=many,
    )
    for collection in (
        value.modified_files, value.inspected_resources, value.executed_actions,
        value.test_results, value.known_failures, value.remaining_items,
    ):
        assert len(collection.items) == MAX_ITEMS
        assert collection.omitted_count == 7
    assert "7 additional items omitted" in value.to_markdown()


def test_individual_messages_are_limited_deterministically() -> None:
    """Spec: HERMES-0011 / AC-67."""
    value = checkpoint(known_failures=["x" * (MAX_TEXT_LENGTH + 100)])
    message = value.known_failures.items[0]
    assert len(message) == MAX_TEXT_LENGTH
    assert message.endswith("…<truncated>")


def test_repository_state_is_optional_and_unknown_is_not_collected() -> None:
    """Spec: HERMES-0011 / AC-11, AC-68."""
    value = checkpoint(repository_state=None)
    assert value.repository_state is None
    assert value.to_dict()["repository_state"] is None
    assert "Branch:" not in value.to_markdown()


def test_empty_minimum_checkpoint_and_stable_schema() -> None:
    """Spec: HERMES-0011 / AC-69."""
    value = create_execution_checkpoint(context(), reason=CheckpointReason.CHECKPOINT_REQUIRED)
    assert value.schema_version == SCHEMA_VERSION == 1
    assert value.modified_files.items == ()
    assert value.known_failures.items == ()
    assert value.recommended_next_action == ""


def test_checkpoint_with_failures_and_recommended_action() -> None:
    """Spec: HERMES-0011 / AC-70."""
    value = checkpoint(
        reason=CheckpointReason.ERROR,
        known_failures=["focused test failed"],
        recommended_next_action="Correct the focused failure before exploration.",
    )
    assert value.known_failures.items == ("focused test failed",)
    assert "Correct the focused failure" in value.to_markdown()


def test_checkpoint_reason_is_a_closed_contract() -> None:
    with pytest.raises(TypeError, match="CheckpointReason"):
        create_execution_checkpoint(context(), reason="manual")  # type: ignore[arg-type]


def test_checkpoint_rejects_invalid_summary_counts() -> None:
    with pytest.raises(ValueError, match="failed"):
        checkpoint(test_results=[CheckpointTestResult("tests", "failed", failed=-1)])
