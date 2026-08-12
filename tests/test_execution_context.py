from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import socket
import subprocess
from typing import Any

import pytest

from hermes_ops.core.errors import (
    CheckpointRequired,
    ExecutionBudgetExceeded,
    ExecutionBudgetReserved,
    SkillExecutionError,
)
from hermes_ops.execution import (
    BudgetDecision,
    ExecutionBudget,
    ExecutionCategory,
    ExecutionContext,
)
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


def test_consume_returns_new_context_and_preserves_previous_snapshot() -> None:
    """Spec: HERMES-0011 / AC-38."""
    original_budget = budget()
    context0 = ExecutionContext(original_budget)

    context1 = context0.consume(ExecutionCategory.EXPLORATION)

    assert context1 is not context0
    assert context1.budget is not context0.budget
    assert context0.budget is original_budget
    assert context0.budget.used_units == 0
    assert context1.budget.used_units == 1


def test_multiple_context_transitions_preserve_every_snapshot() -> None:
    """Spec: HERMES-0011 / AC-39."""
    context0 = ExecutionContext(budget())

    context1 = context0.consume(ExecutionCategory.IMPLEMENTATION)
    context2 = context1.consume(ExecutionCategory.VALIDATION, units=2)

    assert context0.budget.used_units == 0
    assert context1.budget.used_units == 1
    assert context2.budget.used_units == 3
    assert len({id(context0), id(context1), id(context2)}) == 3
    assert len({id(context0.budget), id(context1.budget), id(context2.budget)}) == 3


def test_context_delegates_category_units_and_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-40."""
    context = ExecutionContext(budget(used=2))
    calls: list[tuple[ExecutionCategory, int]] = []
    original_can_start = ExecutionBudget.can_start

    def observed_can_start(
        value: ExecutionBudget,
        category: ExecutionCategory,
        units: int = 1,
    ) -> BudgetDecision:
        calls.append((category, units))
        return original_can_start(value, category, units)

    monkeypatch.setattr(ExecutionBudget, "can_start", observed_can_start)

    decision = context.can_start(ExecutionCategory.VALIDATION, units=2)

    assert decision is BudgetDecision.WARNING
    assert calls == [(ExecutionCategory.VALIDATION, 2)]
    assert context.budget.used_units == 2


def test_context_consume_respects_category_and_units() -> None:
    """Spec: HERMES-0011 / AC-38, AC-40."""
    context = ExecutionContext(budget(used=6))

    updated = context.consume(ExecutionCategory.VALIDATION, units=2)

    assert context.budget.used_units == 6
    assert updated.budget.used_units == 8
    assert updated.budget.remaining == updated.budget.closure_reserve


def test_reserved_transition_propagates_error_without_changing_context() -> None:
    """Spec: HERMES-0011 / AC-41."""
    context = ExecutionContext(budget(used=6))
    original_budget = context.budget

    with pytest.raises(ExecutionBudgetReserved) as captured:
        context.consume(ExecutionCategory.EXPLORATION)

    assert captured.value.code == "EXECUTION_BUDGET_RESERVED"
    assert context.budget is original_budget
    assert context.budget.used_units == 6


def test_checkpoint_transition_propagates_reserved_error() -> None:
    """Spec: HERMES-0011 / AC-41."""
    context = ExecutionContext(budget(used=5))

    assert (
        context.can_start(ExecutionCategory.IMPLEMENTATION)
        is BudgetDecision.CHECKPOINT_REQUIRED
    )
    with pytest.raises(CheckpointRequired, match="checkpoint"):
        context.consume(ExecutionCategory.IMPLEMENTATION)
    assert context.budget.used_units == 5


def test_exhausted_transition_propagates_error_without_changing_context() -> None:
    """Spec: HERMES-0011 / AC-42."""
    context = ExecutionContext(budget(used=9))
    original_budget = context.budget

    with pytest.raises(ExecutionBudgetExceeded) as captured:
        context.consume(ExecutionCategory.CLOSURE, units=2)

    assert captured.value.code == "EXECUTION_BUDGET_EXCEEDED"
    assert context.budget is original_budget
    assert context.budget.used_units == 9


def test_context_transitions_have_no_external_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-36, AC-38."""
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("external effect attempted")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)

    context = ExecutionContext(budget())
    assert context.can_start(ExecutionCategory.CLOSURE) is BudgetDecision.ALLOWED
    assert context.consume(ExecutionCategory.CLOSURE).budget.used_units == 1
