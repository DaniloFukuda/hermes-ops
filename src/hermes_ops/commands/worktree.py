from __future__ import annotations

from pathlib import Path

from hermes_ops.core.configuration import (
    CONFIG_RELATIVE_PATH,
    load_project_config,
    project_config_path,
)
from hermes_ops.core.errors import (
    ConfigurationError,
    ConfigurationMissingError,
    PathResolutionError,
)
from hermes_ops.core.paths import resolve_directory
from hermes_ops.core.results import CheckResult, Report, Status
from hermes_ops.git.inspector import GitInspector


def run_worktree(project: str | Path) -> Report:
    try:
        supplied = resolve_directory(project)
    except PathResolutionError as exc:
        return Report.from_results(
            "worktree",
            [CheckResult("path", Status.BLOCKED, str(exc), code="path_invalid")],
        )
    root = supplied
    try:
        project_config_path(root)
    except ConfigurationMissingError:
        return Report.from_results(
            "worktree",
            [
                CheckResult(
                    "root",
                    Status.BLOCKED,
                    "The supplied directory is not a declared project root",
                    {"root": root},
                    "root_configuration_missing",
                )
            ],
        )
    except ConfigurationError as exc:
        return Report.from_results(
            "worktree",
            [
                CheckResult(
                    "configuration",
                    Status.BLOCKED,
                    str(exc),
                    {"root": root},
                    "config_unsafe_path",
                )
            ],
        )

    try:
        config = load_project_config(root)
    except ConfigurationError as exc:
        return Report.from_results(
            "worktree",
            [
                CheckResult(
                    "configuration",
                    Status.BLOCKED,
                    str(exc),
                    {"path": root / CONFIG_RELATIVE_PATH},
                    "config_schema",
                )
            ],
        )
    marker_states = [path.exists() for path in config.root_marker_paths]
    if not any(marker_states):
        return Report.from_results(
            "worktree",
            [
                CheckResult(
                    "root_markers",
                    Status.BLOCKED,
                    "None of the configured root markers exists",
                    {
                        "policy": "at_least_one",
                        "markers": config.root_marker_paths,
                    },
                    "root_markers_missing",
                )
            ],
        )
    protected = config.git.protected_branches

    state = GitInspector().inspect(root)
    if not state.available:
        return Report.from_results(
            "worktree",
            [
                CheckResult(
                    "git",
                    Status.ERROR,
                    state.error or "Git is unavailable",
                    code=state.error_code or "git_unavailable",
                )
            ],
        )
    if state.error:
        git_status = (
            Status.BLOCKED
            if state.error_code
            in {
                "git_root_mismatch",
                "git_indirect_repository_unsupported",
                "git_unsafe_local_config",
            }
            else Status.ERROR
        )
        return Report.from_results(
            "worktree",
            [
                CheckResult(
                    "git",
                    git_status,
                    state.error,
                    code=state.error_code or "git_operational_error",
                )
            ],
        )
    if not state.is_repository:
        return Report.from_results(
            "worktree",
            [
                CheckResult(
                    "git",
                    Status.BLOCKED,
                    "The project is not a Git repository",
                    code="git_repository_missing",
                )
            ],
        )
    is_protected = state.branch in protected if state.branch else False
    status = Status.WARNING if is_protected else Status.OK
    message = (
        f"Protected branch: {state.branch}"
        if is_protected
        else ("Detached HEAD" if state.detached else f"Branch: {state.branch}")
    )
    changes = state.changes
    details = {
        "root": state.root,
        "branch": state.branch,
        "head": state.head,
        "has_commits": state.has_commits,
        "detached": state.detached,
        "protected_branch": is_protected,
        "clean": state.clean,
        "modified": changes.modified,
        "added": changes.added,
        "removed": changes.removed,
        "untracked": changes.untracked,
        "conflicts": changes.conflicts,
    }
    return Report.from_results(
        "worktree",
        [
            CheckResult("git", status, message, details, "protected_branch" if is_protected else "ok"),
            CheckResult(
                "working_tree",
                Status.OK if state.clean else Status.WARNING,
                "Working tree is clean" if state.clean else "Working tree has changes",
                details,
                "ok" if state.clean else "worktree_dirty",
            ),
        ],
    )
