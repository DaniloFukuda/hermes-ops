from __future__ import annotations

from pathlib import Path
import socket
import sys

import pytest

from hermes_ops.core.errors import (
    CheckpointRequired,
    ExecutionBudgetExceeded,
    ExecutionBudgetReserved,
)
from hermes_ops.core.processes import (
    BudgetedProcessResult,
    ProcessResult,
    run_process,
    run_process_with_context,
)
from hermes_ops.execution import (
    BudgetDecision,
    ExecutionBudget,
    ExecutionCategory,
    ExecutionContext,
)


def context(*, used: int = 0) -> ExecutionContext:
    return ExecutionContext(
        ExecutionBudget(
            max_units=10,
            used_units=used,
            validation_reserve=2,
            closure_reserve=2,
            warning_threshold=3,
            checkpoint_threshold=5,
        )
    )


def process_result(*, returncode: int = 0) -> ProcessResult:
    return ProcessResult("cwd", returncode, "out", "err", True, False)


def install_process_spy(
    monkeypatch: pytest.MonkeyPatch,
    returned: ProcessResult,
) -> list[tuple[object, ...]]:
    calls: list[tuple[object, ...]] = []

    def fake_run_process(
        args: object,
        *,
        cwd: Path,
        timeout: float,
        env: object = None,
    ) -> ProcessResult:
        calls.append((args, cwd, timeout, env))
        return returned

    monkeypatch.setattr("hermes_ops.core.processes.run_process", fake_run_process)
    return calls


def test_allowed_consumes_before_one_process_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-43."""
    events: list[str] = []
    original_consume = ExecutionContext.consume
    expected_process = process_result()

    def observed_consume(
        value: ExecutionContext,
        category: ExecutionCategory,
        units: int = 1,
    ) -> ExecutionContext:
        events.append("consume")
        return original_consume(value, category, units)

    def observed_process(*args: object, **kwargs: object) -> ProcessResult:
        events.append("process")
        return expected_process

    monkeypatch.setattr(ExecutionContext, "consume", observed_consume)
    monkeypatch.setattr("hermes_ops.core.processes.run_process", observed_process)
    before = context()

    result = run_process_with_context(
        ("tool",),
        cwd=Path("work"),
        timeout=1,
        execution_context=before,
        category=ExecutionCategory.CLOSURE,
    )

    assert events == ["consume", "process"]
    assert result == BudgetedProcessResult(expected_process, result.execution_context)
    assert result.execution_context.budget.used_units == 1
    assert before.budget.used_units == 0


def test_warning_consumes_and_executes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0011 / AC-44."""
    expected = process_result()
    calls = install_process_spy(monkeypatch, expected)
    before = context(used=2)

    assert before.can_start(ExecutionCategory.VALIDATION) is BudgetDecision.WARNING
    result = run_process_with_context(
        ("tool",),
        cwd=Path("work"),
        timeout=1,
        execution_context=before,
        category=ExecutionCategory.VALIDATION,
    )

    assert len(calls) == 1
    assert result.process_result is expected
    assert result.execution_context.budget.used_units == 3


def test_checkpoint_required_blocks_before_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-45."""
    calls = install_process_spy(monkeypatch, process_result())
    before = context(used=5)

    with pytest.raises(CheckpointRequired) as captured:
        run_process_with_context(
            ("tool",),
            cwd=Path("work"),
            timeout=1,
            execution_context=before,
            category=ExecutionCategory.EXPLORATION,
        )

    assert captured.value.code == "EXECUTION_CHECKPOINT_REQUIRED"
    assert calls == []
    assert before.budget.used_units == 5


def test_reserved_blocks_before_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0011 / AC-46."""
    calls = install_process_spy(monkeypatch, process_result())
    before = context(used=6)

    with pytest.raises(ExecutionBudgetReserved):
        run_process_with_context(
            ("tool",),
            cwd=Path("work"),
            timeout=1,
            execution_context=before,
            category=ExecutionCategory.IMPLEMENTATION,
        )

    assert calls == []
    assert before.budget.used_units == 6


def test_exhausted_blocks_before_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0011 / AC-47."""
    calls = install_process_spy(monkeypatch, process_result())
    before = context(used=9)

    with pytest.raises(ExecutionBudgetExceeded):
        run_process_with_context(
            ("tool",),
            cwd=Path("work"),
            timeout=1,
            execution_context=before,
            category=ExecutionCategory.CLOSURE,
            units=2,
        )

    assert calls == []
    assert before.budget.used_units == 9


def test_units_and_explicit_category_are_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-48."""
    calls = install_process_spy(monkeypatch, process_result())
    observed: list[tuple[ExecutionCategory, int]] = []
    original_can_start = ExecutionContext.can_start

    def observed_can_start(
        value: ExecutionContext,
        category: ExecutionCategory,
        units: int = 1,
    ) -> BudgetDecision:
        observed.append((category, units))
        return original_can_start(value, category, units)

    monkeypatch.setattr(ExecutionContext, "can_start", observed_can_start)

    result = run_process_with_context(
        ("tool",),
        cwd=Path("work"),
        timeout=1,
        execution_context=context(),
        category=ExecutionCategory.IMPLEMENTATION,
        units=2,
    )

    assert observed == [(ExecutionCategory.IMPLEMENTATION, 2)]
    assert result.execution_context.budget.used_units == 2
    assert len(calls) == 1


def test_success_preserves_legacy_result_inside_budgeted_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-43, AC-50."""
    expected = process_result()
    install_process_spy(monkeypatch, expected)

    result = run_process_with_context(
        ("tool",),
        cwd=Path("work"),
        timeout=1,
        execution_context=context(),
        category=ExecutionCategory.CLOSURE,
    )

    assert result.process_result is expected
    assert result.process_result.succeeded


def test_failed_process_keeps_consumed_context_and_failure_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-49."""
    failed = process_result(returncode=7)
    calls = install_process_spy(monkeypatch, failed)

    result = run_process_with_context(
        ("tool",),
        cwd=Path("work"),
        timeout=1,
        execution_context=context(),
        category=ExecutionCategory.CLOSURE,
    )

    assert len(calls) == 1
    assert result.process_result is failed
    assert not result.process_result.succeeded
    assert result.process_result.returncode == 7
    assert result.execution_context.budget.used_units == 1


def test_legacy_run_process_contract_is_unchanged(tmp_path: Path) -> None:
    """Spec: HERMES-0011 / AC-50."""
    result = run_process(
        (sys.executable, "-c", "print('legacy')"),
        cwd=tmp_path,
        timeout=5,
    )

    assert type(result) is ProcessResult
    assert result.succeeded
    assert result.stdout.strip() == "legacy"


def test_wrapper_adds_no_network_or_filesystem_before_legacy_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-43, AC-45."""
    def forbidden_network(*args: object, **kwargs: object) -> object:
        raise AssertionError("network access")

    monkeypatch.setattr(socket, "socket", forbidden_network)
    calls = install_process_spy(monkeypatch, process_result())

    run_process_with_context(
        ("tool",),
        cwd=Path("unresolved-and-unread"),
        timeout=1,
        execution_context=context(),
        category=ExecutionCategory.CLOSURE,
    )

    assert len(calls) == 1
    assert calls[0][1] == Path("unresolved-and-unread")
