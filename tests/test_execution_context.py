from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import socket
import subprocess
from typing import Any

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.execution import ExecutionBudget, ExecutionContext
from hermes_ops.skills.execution_models import (
    SkillExecutionResult,
    SkillExecutionStatus,
)
from hermes_ops.skills.models import SkillRisk
from hermes_ops.skills.policy import SkillPolicy
import hermes_ops.skills.executor as executor


def budget(*, used: int = 0) -> ExecutionBudget:
    return ExecutionBudget(
        max_units=10,
        used_units=used,
        validation_reserve=2,
        closure_reserve=2,
        warning_threshold=3,
        checkpoint_threshold=5,
    )


def result() -> SkillExecutionResult:
    return SkillExecutionResult(
        "git-preflight",
        SkillExecutionStatus.PASSED,
        0,
        (),
    )


def policy() -> SkillPolicy:
    return SkillPolicy(SkillRisk.LOW, False, frozenset({"git"}))


def stub_public_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    returned: SkillExecutionResult,
) -> list[ExecutionContext | None]:
    received: list[ExecutionContext | None] = []
    monkeypatch.setattr(executor, "resolve_directory", lambda value: Path("target"))
    monkeypatch.setattr(
        executor,
        "resolve_own_skill_catalog",
        lambda: Path("catalog"),
    )

    def fake_run(
        project_root: Any,
        skill_id: Any,
        supplied_policy: Any,
        catalog_root: Path,
        inputs: Any,
        *,
        execution_context: ExecutionContext | None = None,
    ) -> SkillExecutionResult:
        received.append(execution_context)
        return returned

    monkeypatch.setattr(executor, "_run_skill_with_catalog", fake_run)
    return received


def test_context_preserves_budget_identity_and_is_immutable() -> None:
    """Spec: HERMES-0011 / AC-31."""
    supplied_budget = budget()
    context = ExecutionContext(supplied_budget)

    assert context.budget is supplied_budget
    assert repr(context) == "ExecutionContext()"
    with pytest.raises(FrozenInstanceError):
        context.budget = budget(used=1)  # type: ignore[misc]


def test_context_rejects_non_budget_value() -> None:
    """Spec: HERMES-0011 / AC-32."""
    with pytest.raises(TypeError, match="budget must be an ExecutionBudget"):
        ExecutionContext(object())  # type: ignore[arg-type]


def test_run_skill_without_context_preserves_legacy_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-33."""
    expected = result()
    received = stub_public_pipeline(monkeypatch, expected)

    actual = executor.run_skill("project", "git-preflight", policy())

    assert actual is expected
    assert received == [None]


def test_run_skill_accepts_explicit_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-34."""
    expected = result()
    received = stub_public_pipeline(monkeypatch, expected)
    context = ExecutionContext(budget())

    actual = executor.run_skill(
        "project",
        "git-preflight",
        policy(),
        execution_context=context,
    )

    assert actual is expected
    assert received == [context]
    assert received[0] is context


def test_same_context_reaches_dispatch_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-34."""
    context = ExecutionContext(budget())
    expected = result()
    received: list[ExecutionContext | None] = []
    monkeypatch.setattr(executor, "resolve_directory", lambda value: Path("target"))
    monkeypatch.setattr(executor, "discover_skills", lambda root: object())
    monkeypatch.setattr(executor, "plan_skills", lambda registry, ids, value: object())

    def fake_dispatch(
        plan: Any,
        target_project: Any,
        original_target: Any,
        inputs: Any,
        *,
        execution_context: ExecutionContext | None = None,
    ) -> SkillExecutionResult:
        received.append(execution_context)
        return expected

    monkeypatch.setattr(executor, "_dispatch_skill", fake_dispatch)

    actual = executor._run_skill_with_catalog(
        "project",
        "git-preflight",
        policy(),
        Path("catalog"),
        execution_context=context,
    )

    assert actual is expected
    assert received[0] is context


def test_run_skill_does_not_consume_supplied_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-35."""
    expected = result()
    stub_public_pipeline(monkeypatch, expected)
    supplied_budget = budget(used=2)
    context = ExecutionContext(supplied_budget)

    def forbidden_consume(*args: object, **kwargs: object) -> object:
        raise AssertionError("budget.consume must not be called in HERMES-0011B")

    monkeypatch.setattr(ExecutionBudget, "consume", forbidden_consume)
    before = context.budget.used_units

    executor.run_skill(
        "project",
        "git-preflight",
        policy(),
        execution_context=context,
    )

    assert context.budget is supplied_budget
    assert context.budget.used_units == before == 2


def test_context_creation_has_no_external_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-36."""
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("external effect attempted")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)

    supplied_budget = budget()
    context = ExecutionContext(supplied_budget)

    assert context.budget is supplied_budget


def test_context_does_not_change_public_skill_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-37."""
    expected = result()
    received = stub_public_pipeline(monkeypatch, expected)

    legacy = executor.run_skill("project", "git-preflight", policy())
    contextual = executor.run_skill(
        "project",
        "git-preflight",
        policy(),
        execution_context=ExecutionContext(budget()),
    )

    assert legacy is contextual is expected
    assert legacy.__dataclass_fields__.keys() == {
        "skill_id",
        "status",
        "exit_code",
        "evidence",
    }
    assert received[0] is None
    assert type(received[1]) is ExecutionContext


def test_run_skill_rejects_invalid_context_before_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-32, AC-33."""
    monkeypatch.setattr(executor, "resolve_directory", lambda value: Path("target"))

    def forbidden_catalog() -> Path:
        raise AssertionError("catalog resolved after invalid context")

    monkeypatch.setattr(executor, "resolve_own_skill_catalog", forbidden_catalog)

    with pytest.raises(SkillExecutionError) as captured:
        executor.run_skill(
            "project",
            "git-preflight",
            policy(),
            execution_context=object(),  # type: ignore[arg-type]
        )

    assert captured.value.code == "SKILL_EXECUTION_INVALID"
