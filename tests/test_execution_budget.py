from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import socket
import subprocess

import pytest

from hermes_ops.core.errors import (
    CheckpointRequired,
    ExecutionBudgetError,
    ExecutionBudgetExceeded,
    ExecutionBudgetReserved,
)
from hermes_ops.execution import (
    BudgetDecision,
    ExecutionBudget,
    ExecutionCategory,
)


def budget(*, used: int = 0) -> ExecutionBudget:
    return ExecutionBudget(
        max_units=10,
        used_units=used,
        validation_reserve=2,
        closure_reserve=2,
        warning_threshold=3,
        checkpoint_threshold=5,
    )


def test_valid_budget_starts_with_no_used_units() -> None:
    """Spec: HERMES-0011 / AC-01, AC-03."""
    value = budget()

    assert value.used_units == 0
    assert value.remaining == 10
    assert not value.should_warn()
    assert not value.should_checkpoint()
    assert not value.should_stop_exploration()


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"max_units": 0}, "max_units"),
        ({"used_units": -1}, "used_units"),
        ({"used_units": 11}, "used_units"),
        ({"validation_reserve": -1}, "validation_reserve"),
        ({"closure_reserve": 0}, "closure_reserve"),
        ({"validation_reserve": 4, "closure_reserve": 6}, "reserves"),
        ({"warning_threshold": -1}, "warning_threshold"),
        ({"warning_threshold": 5}, "warning_threshold"),
        ({"checkpoint_threshold": 7}, "checkpoint_threshold"),
        ({"max_units": True}, "max_units"),
    ],
)
def test_invalid_budget_values_are_rejected(
    changes: dict[str, int],
    message: str,
) -> None:
    """Spec: HERMES-0011 / AC-08."""
    values = {
        "max_units": 10,
        "used_units": 0,
        "validation_reserve": 2,
        "closure_reserve": 2,
        "warning_threshold": 3,
        "checkpoint_threshold": 5,
    }
    values.update(changes)

    with pytest.raises(ExecutionBudgetError, match=message) as captured:
        ExecutionBudget(**values)

    assert captured.value.code == "EXECUTION_BUDGET_INVALID"


def test_consume_records_one_atomic_action() -> None:
    """Spec: HERMES-0011 / AC-02."""
    original = budget()

    updated = original.consume(ExecutionCategory.EXPLORATION)

    assert original.used_units == 0
    assert updated.used_units == 1
    assert updated.remaining == 9


def test_consume_accumulates_explicit_positive_units() -> None:
    """Spec: HERMES-0011 / AC-02, AC-03, AC-16."""
    updated = budget().consume(ExecutionCategory.IMPLEMENTATION, 2)
    updated = updated.consume(ExecutionCategory.EXPLORATION, 1)

    assert updated.used_units == 3
    assert updated.remaining == 7


@pytest.mark.parametrize("units", [0, -1, True, 1.5])
def test_action_cost_must_be_a_positive_integer(units: object) -> None:
    """Spec: HERMES-0011 / AC-16."""
    with pytest.raises(ExecutionBudgetError) as captured:
        budget().can_start(ExecutionCategory.EXPLORATION, units)  # type: ignore[arg-type]

    assert captured.value.code == "EXECUTION_BUDGET_INVALID"


def test_warning_threshold_is_inclusive_on_resulting_snapshot() -> None:
    """Spec: HERMES-0011 / AC-15."""
    before = budget(used=2)

    assert before.can_start(ExecutionCategory.EXPLORATION) is BudgetDecision.WARNING
    after = before.consume(ExecutionCategory.EXPLORATION)
    assert after.should_warn()
    assert not after.should_checkpoint()


def test_checkpoint_threshold_stops_later_exploration() -> None:
    """Spec: HERMES-0011 / AC-05."""
    reached = budget(used=4).consume(ExecutionCategory.EXPLORATION)

    assert reached.used_units == 5
    assert reached.should_checkpoint()
    assert reached.should_stop_exploration()
    assert (
        reached.can_start(ExecutionCategory.IMPLEMENTATION)
        is BudgetDecision.CHECKPOINT_REQUIRED
    )
    with pytest.raises(CheckpointRequired, match="checkpoint"):
        reached.consume(ExecutionCategory.EXPLORATION)


def test_closure_reserve_blocks_exploration_and_allows_closure() -> None:
    """Spec: HERMES-0011 / AC-04."""
    at_limit = budget(used=6)

    assert at_limit.exploration_limit == 6
    assert at_limit.can_start(ExecutionCategory.EXPLORATION) is BudgetDecision.RESERVED
    assert at_limit.can_start(ExecutionCategory.IMPLEMENTATION) is BudgetDecision.RESERVED
    with pytest.raises(ExecutionBudgetReserved):
        at_limit.consume(ExecutionCategory.IMPLEMENTATION)
    assert at_limit.consume(ExecutionCategory.CLOSURE, 4).remaining == 0


def test_validation_can_use_validation_reserve_but_preserves_closure() -> None:
    """Spec: HERMES-0011 / AC-04, AC-27."""
    value = budget(used=6)

    value = value.consume(ExecutionCategory.VALIDATION, 2)

    assert value.used_units == 8
    assert value.remaining == value.closure_reserve
    assert value.can_start(ExecutionCategory.VALIDATION) is BudgetDecision.RESERVED


def test_closure_can_use_its_reserve() -> None:
    """Spec: HERMES-0011 / AC-04, AC-26."""
    value = budget(used=8).consume(ExecutionCategory.CLOSURE, 2)

    assert value.used_units == value.max_units
    assert value.remaining == 0


def test_absolute_limit_precedes_reserve_decision() -> None:
    """Spec: HERMES-0011 / AC-26."""
    value = budget(used=9)

    assert value.can_start(ExecutionCategory.VALIDATION, 2) is BudgetDecision.EXHAUSTED
    with pytest.raises(ExecutionBudgetExceeded) as captured:
        value.consume(ExecutionCategory.CLOSURE, 2)

    assert captured.value.code == "EXECUTION_BUDGET_EXCEEDED"
    assert value.remaining == 1


def test_budget_is_frozen_and_transitions_are_deterministic() -> None:
    """Spec: HERMES-0011 / AC-03, AC-09."""
    original = budget()

    first = original.consume(ExecutionCategory.EXPLORATION, 2)
    second = original.consume(ExecutionCategory.EXPLORATION, 2)

    assert first == second
    assert first is not second
    with pytest.raises(FrozenInstanceError):
        original.used_units = 4  # type: ignore[misc]


def test_unknown_category_is_rejected_explicitly() -> None:
    """Spec: HERMES-0011 / AC-16."""
    with pytest.raises(ExecutionBudgetError) as captured:
        budget().can_start("exploration")  # type: ignore[arg-type]

    assert captured.value.code == "EXECUTION_BUDGET_INVALID"


def test_budget_operations_have_no_external_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-10."""
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("external effect attempted")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)

    value = budget()
    assert value.can_start(ExecutionCategory.EXPLORATION) is BudgetDecision.ALLOWED
    assert value.consume(ExecutionCategory.EXPLORATION).remaining == 9


def test_budget_module_has_only_provider_neutral_imports() -> None:
    """Spec: HERMES-0011 / AC-09, AC-10."""
    source = Path("src/hermes_ops/execution/budget.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])

    assert roots <= {"__future__", "dataclasses", "enum", "hermes_ops"}
