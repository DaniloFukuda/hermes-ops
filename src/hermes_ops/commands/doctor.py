from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil

from hermes_ops.core.configuration import (
    CONFIG_RELATIVE_PATH,
    ProjectConfig,
    load_project_config,
    project_config_path,
)
from hermes_ops.core.errors import (
    ConfigurationError,
    ConfigurationMissingError,
    PathResolutionError,
)
from hermes_ops.core.paths import resolve_directory
from hermes_ops.core.platform_info import current_platform, python_is_compatible
from hermes_ops.core.results import CheckResult, Report, Status
from hermes_ops.git.inspector import GitInspector, GitState, OPTIONAL_GIT_WARNING_CODES


def run_doctor(project: str | Path) -> Report:
    return _run_doctor(project, lambda root: GitInspector().inspect(root))


def _run_doctor(
    project: str | Path,
    inspect_git: Callable[[Path], GitState],
) -> Report:
    results: list[CheckResult] = []
    try:
        supplied = resolve_directory(project)
    except PathResolutionError as exc:
        return Report.from_results(
            "doctor",
            [CheckResult("path", Status.BLOCKED, str(exc), code="path_invalid")],
        )
    results.append(
        CheckResult("path", Status.OK, "Project path is accessible", {"path": supplied})
    )

    root = supplied
    try:
        config_path = project_config_path(root)
    except ConfigurationMissingError:
        return Report.from_results(
            "doctor",
            results
            + [
                CheckResult(
                        "root",
                        Status.BLOCKED,
                        "The supplied directory is not a declared project root",
                        {
                            "root": root,
                            "required_configuration": root
                            / CONFIG_RELATIVE_PATH,
                        },
                    "root_configuration_missing",
                )
            ],
        )
    except ConfigurationError as exc:
        return Report.from_results(
            "doctor",
            results
            + [
                CheckResult(
                    "configuration",
                    Status.BLOCKED,
                    str(exc),
                    {"root": root},
                    _config_code(exc),
                )
            ],
        )
    results.append(
        CheckResult("root", Status.OK, "Using the explicitly supplied project root", {"root": root})
    )

    config: ProjectConfig | None = None
    try:
        config = load_project_config(root)
    except ConfigurationError as exc:
        results.append(
            CheckResult(
                "configuration",
                Status.BLOCKED,
                str(exc),
                {"path": root / ".hermes/project.toml"},
                _config_code(exc),
            )
        )
    else:
        results.append(
            CheckResult(
                "configuration",
                Status.OK,
                "Configuration is valid",
                {"path": root / ".hermes/project.toml", "project": config.project.name},
            )
        )
        marker_states = [
            {"path": path, "exists": path.exists()}
            for path in config.root_marker_paths
        ]
        marker_valid = any(item["exists"] for item in marker_states)
        results.append(
            CheckResult(
                "root_markers",
                Status.OK if marker_valid else Status.BLOCKED,
                (
                    "At least one configured root marker exists"
                    if marker_valid
                    else "None of the configured root markers exists"
                ),
                {"policy": "at_least_one", "markers": marker_states},
                "ok" if marker_valid else "root_markers_missing",
            )
        )

    platform = current_platform()
    results.append(
        CheckResult(
            "platform",
            Status.OK,
            f"{platform.operating_system} {platform.release}",
            {
                "operating_system": platform.operating_system,
                "release": platform.release,
                "python_version": platform.python_version,
                "python_executable": platform.python_executable,
            },
        )
    )

    if config is not None:
        compatible = python_is_compatible(
            platform.python_version, config.runtime.minimum_python
        )
        results.append(
            CheckResult(
                "python",
                Status.OK if compatible else Status.BLOCKED,
                (
                    f"Python {platform.python_version} satisfies "
                    f">={config.runtime.minimum_python}"
                    if compatible
                    else (
                        f"Python {platform.python_version} does not satisfy "
                        f">={config.runtime.minimum_python}"
                    )
                ),
                {
                    "current": platform.python_version,
                    "minimum": config.runtime.minimum_python,
                },
                "ok" if compatible else "python_incompatible",
            )
        )
        candidates = [
            {"path": candidate, "exists": candidate.is_file()}
            for candidate in config.python_candidate_paths
        ]
        results.append(
            CheckResult(
                "python_candidates",
                Status.OK if any(item["exists"] for item in candidates) else Status.WARNING,
                (
                    "At least one configured Python candidate exists"
                    if any(item["exists"] for item in candidates)
                    else "No configured Python candidate exists"
                ),
                {"candidates": candidates},
                "ok" if any(item["exists"] for item in candidates) else "python_candidate_missing",
            )
        )

    git_path = shutil.which("git")
    results.append(
        CheckResult(
            "git_available",
            Status.OK if git_path else Status.WARNING,
            f"Git available at {git_path}" if git_path else "Git is unavailable",
            {"executable": git_path},
            "ok" if git_path else "git_unavailable",
        )
    )
    state = inspect_git(root)
    if state.error:
        if not config.git.required and state.error_code in OPTIONAL_GIT_WARNING_CODES:
            git_status = Status.WARNING
        else:
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
        results.append(
            CheckResult(
                "git_repository",
                git_status,
                state.error,
                {"root": state.root},
                state.error_code or "git_operational_error",
            )
        )
    else:
        results.append(
            CheckResult(
                "git_repository",
                Status.OK if state.is_repository else Status.WARNING,
                "Git repository detected" if state.is_repository else "Not a Git repository",
                {"root": state.root},
                "ok" if state.is_repository else "git_repository_missing",
            )
        )
    return Report.from_results("doctor", results)


def _config_code(exc: ConfigurationError) -> str:
    name = type(exc).__name__.lower()
    if "missing" in name:
        return "config_missing"
    if "syntax" in name:
        return "config_syntax"
    return "config_schema"
