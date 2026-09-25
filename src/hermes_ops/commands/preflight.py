from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from hermes_ops.commands.doctor import _run_doctor, run_doctor
from hermes_ops.commands.worktree import run_worktree
from hermes_ops.core.configuration import load_project_config
from hermes_ops.core.errors import ConfigurationError, PathResolutionError
from hermes_ops.core.paths import resolve_directory
from hermes_ops.core.results import CheckResult, Report, Status
from hermes_ops.execution import ExecutionCategory, ExecutionContext
from hermes_ops.git.inspector import GitInspector
from hermes_ops.git.inspector import OPTIONAL_GIT_WARNING_CODES


def run_preflight(project: str | Path) -> Report:
    return _run_preflight(project, run_doctor)


@dataclass(frozen=True, slots=True)
class BudgetedPreflightResult:
    report: Report
    execution_context: ExecutionContext


def run_preflight_with_context(
    project: str | Path,
    execution_context: ExecutionContext,
    category: ExecutionCategory,
) -> BudgetedPreflightResult:
    current_context = execution_context

    def budgeted_doctor(target: str | Path) -> Report:
        nonlocal current_context

        def inspect_git(root: Path):
            nonlocal current_context
            inspection = GitInspector().inspect_with_context(
                root,
                current_context,
                category,
            )
            current_context = inspection.execution_context
            return inspection.state

        return _run_doctor(target, inspect_git)

    report = _run_preflight(project, budgeted_doctor)
    return BudgetedPreflightResult(report, current_context)


def _run_preflight(
    project: str | Path,
    doctor_runner: Callable[[str | Path], Report],
) -> Report:
    doctor = doctor_runner(project)
    results = list(doctor.results)
    if doctor.exit_code in {2, 3, 4}:
        return Report.from_results("preflight", results)

    try:
        supplied = resolve_directory(project)
        root = supplied
        config = load_project_config(root)
    except (PathResolutionError, ConfigurationError):
        return Report.from_results("preflight", results)

    worktree = run_worktree(project)
    git_results = [item for item in worktree.results if item.name in {"git", "working_tree"}]
    if config.git.required:
        git_results = [
            CheckResult(item.name, Status.BLOCKED, item.message, item.details, item.code)
            if item.code in {
                "git_unavailable",
                "git_repository_missing",
                "git_operational_error",
                "git_permission_denied",
                "git_dubious_ownership",
                "git_unexpected_output",
                "git_root_mismatch",
                "git_declared_root_invalid",
                "git_indirect_repository_unsupported",
                "git_unsafe_local_config",
            }
            else item
            for item in git_results
        ]
    elif worktree.exit_code:
        git_results = [
            CheckResult(item.name, Status.WARNING, item.message, item.details, item.code)
            if item.code in OPTIONAL_GIT_WARNING_CODES
            else item
            for item in git_results
        ]
    results.extend(git_results)

    dirty = next((item for item in git_results if item.code == "worktree_dirty"), None)
    if dirty is not None and config.git.require_clean_worktree:
        results.append(
            CheckResult(
                "clean_worktree_policy",
                Status.BLOCKED,
                "Configuration requires a clean working tree",
                dirty.details,
                "worktree_required_clean",
            )
        )
    return Report.from_results("preflight", results)
