from __future__ import annotations

from pathlib import Path

from hermes_ops.commands.doctor import run_doctor
from hermes_ops.commands.worktree import run_worktree
from hermes_ops.core.configuration import load_project_config
from hermes_ops.core.errors import ConfigurationError, PathResolutionError
from hermes_ops.core.paths import resolve_directory
from hermes_ops.core.results import CheckResult, Report, Status


def run_preflight(project: str | Path) -> Report:
    doctor = run_doctor(project)
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
            }
            else item
            for item in git_results
        ]
    elif worktree.exit_code:
        git_results = [
            CheckResult(item.name, Status.WARNING, item.message, item.details, item.code)
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
