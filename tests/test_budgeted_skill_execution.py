from __future__ import annotations

from pathlib import Path

import pytest
import subprocess

from conftest import VALID_CONFIG, git
from hermes_ops.core.errors import (
    CheckpointRequired,
    ExecutionBudgetExceeded,
    ExecutionBudgetReserved,
)
from hermes_ops.core.processes import BudgetedProcessResult, ProcessResult
from hermes_ops.execution import ExecutionBudget, ExecutionCategory, ExecutionContext
from hermes_ops.skills import (
    BudgetedSkillExecutionResult,
    SkillPolicy,
    SkillRisk,
    run_skill,
    run_skill_with_context,
)
import hermes_ops.git.inspector as inspector_module


def context(*, used: int = 0) -> ExecutionContext:
    return ExecutionContext(
        ExecutionBudget(10, used, 2, 2, 3, 5)
    )


def policy() -> SkillPolicy:
    return SkillPolicy(SkillRisk.LOW, False, frozenset({"git"}))


def project(tmp_path: Path) -> Path:
    config = tmp_path / ".hermes/project.toml"
    config.parent.mkdir(parents=True)
    config.write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='fixture'\nversion='1'\n",
        encoding="utf-8",
    )
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Hermes Budget Test")
    git(tmp_path, "config", "user.email", "budget@invalid.local")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture")
    return tmp_path


def test_legacy_and_budgeted_git_preflight_are_functionally_equivalent(
    tmp_path: Path,
) -> None:
    """Spec: HERMES-0011 / AC-50, AC-51."""
    target = project(tmp_path)

    legacy = run_skill(target, "git-preflight", policy())
    budgeted = run_skill_with_context(
        target,
        "git-preflight",
        policy(),
        execution_context=context(),
        category=ExecutionCategory.VALIDATION,
    )

    assert type(legacy) is type(budgeted.skill_result)
    assert legacy == budgeted.skill_result
    assert budgeted.execution_context.budget.used_units == 1


def test_context_after_returns_to_public_budgeted_api(tmp_path: Path) -> None:
    """Spec: HERMES-0011 / AC-51, AC-52."""
    target = project(tmp_path)
    before = context()

    result = run_skill_with_context(
        target,
        "git-preflight",
        policy(),
        execution_context=before,
        category=ExecutionCategory.VALIDATION,
    )

    assert type(result) is BudgetedSkillExecutionResult
    assert result.execution_context is not before
    assert before.budget.used_units == 0
    assert result.execution_context.budget.used_units == 1


def test_warning_executes_and_returns_advanced_context(tmp_path: Path) -> None:
    """Spec: HERMES-0011 / AC-53."""
    target = project(tmp_path)

    result = run_skill_with_context(
        target,
        "git-preflight",
        policy(),
        execution_context=context(used=2),
        category=ExecutionCategory.VALIDATION,
    )

    assert result.skill_result.exit_code == 0
    assert result.execution_context.budget.used_units == 3


@pytest.mark.parametrize(
    ("used", "category", "error"),
    [
        (5, ExecutionCategory.EXPLORATION, CheckpointRequired),
        (8, ExecutionCategory.VALIDATION, ExecutionBudgetReserved),
        (10, ExecutionCategory.VALIDATION, ExecutionBudgetExceeded),
    ],
)
def test_budget_refusals_block_before_any_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    used: int,
    category: ExecutionCategory,
    error: type[Exception],
) -> None:
    """Spec: HERMES-0011 / AC-54, AC-55, AC-56."""
    target = project(tmp_path)

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("subprocess started")

    monkeypatch.setattr("hermes_ops.core.processes.run_process", forbidden)

    with pytest.raises(error):
        run_skill_with_context(
            target,
            "git-preflight",
            policy(),
            execution_context=context(used=used),
            category=category,
        )


def test_failed_probe_keeps_consumption_and_is_not_masked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-57."""
    target = project(tmp_path)
    failed = ProcessResult(
        str(target),
        7,
        "",
        "probe failed",
        True,
        False,
    )

    def failed_probe(
        args: object,
        **kwargs: object,
    ) -> BudgetedProcessResult:
        before = kwargs["execution_context"]
        after = before.consume(ExecutionCategory.VALIDATION)
        return BudgetedProcessResult(failed, after)

    monkeypatch.setattr(inspector_module, "run_process_with_context", failed_probe)

    result = run_skill_with_context(
        target,
        "git-preflight",
        policy(),
        execution_context=context(),
        category=ExecutionCategory.VALIDATION,
    )

    assert result.execution_context.budget.used_units == 1
    assert result.skill_result.exit_code == 1
    assert any(item.message == "probe failed" for item in result.skill_result.evidence)


def test_only_git_preflight_has_budgeted_handler(
    tmp_path: Path,
) -> None:
    """Spec: HERMES-0011 / AC-58."""
    target = project(tmp_path)

    with pytest.raises(Exception) as captured:
        run_skill_with_context(
            target,
            "code-audit",
            policy(),
            execution_context=context(),
            category=ExecutionCategory.VALIDATION,
        )

    assert getattr(captured.value, "code", None) == "SKILL_EXECUTION_NOT_SUPPORTED"


def test_legacy_run_skill_never_uses_budgeted_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-50, AC-58."""
    target = project(tmp_path)

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("budget-aware probe used by legacy path")

    monkeypatch.setattr(inspector_module.GitInspector, "probe_with_context", forbidden)

    assert run_skill(target, "git-preflight", policy()).exit_code == 0


def test_budgeted_path_does_not_add_duplicate_probe_or_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-59."""
    target = project(tmp_path)
    real_run = subprocess.run
    commands: list[tuple[str, ...]] = []

    def counted_run(args: object, **kwargs: object) -> object:
        normalized = tuple(str(item) for item in args)  # type: ignore[union-attr]
        commands.append(normalized)
        return real_run(args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr("hermes_ops.core.processes.subprocess.run", counted_run)

    run_skill(target, "git-preflight", policy())
    legacy = tuple(commands)
    commands.clear()

    run_skill_with_context(
        target,
        "git-preflight",
        policy(),
        execution_context=context(),
        category=ExecutionCategory.VALIDATION,
    )
    budgeted = tuple(commands)

    probe = ("rev-parse", "--is-inside-work-tree")
    legacy_probes = sum(command[-2:] == probe for command in legacy)
    budgeted_probes = sum(command[-2:] == probe for command in budgeted)
    assert legacy_probes == budgeted_probes
    assert len(legacy) == len(budgeted)


def test_inspector_variants_each_execute_selected_probe_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0011 / AC-59, AC-60."""
    target = project(tmp_path)
    real_run = subprocess.run
    commands: list[tuple[str, ...]] = []

    def counted_run(args: object, **kwargs: object) -> object:
        commands.append(tuple(str(item) for item in args))  # type: ignore[union-attr]
        return real_run(args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr("hermes_ops.core.processes.subprocess.run", counted_run)
    inspector = inspector_module.GitInspector()
    inspector.inspect(target)
    legacy = tuple(commands)
    commands.clear()

    result = inspector.inspect_with_context(
        target,
        context(),
        ExecutionCategory.VALIDATION,
    )
    budgeted = tuple(commands)
    probe = ("rev-parse", "--is-inside-work-tree")

    assert sum(command[-2:] == probe for command in legacy) == 1
    assert sum(command[-2:] == probe for command in budgeted) == 1
    assert len(legacy) == len(budgeted)
    assert result.execution_context.budget.used_units == 1
