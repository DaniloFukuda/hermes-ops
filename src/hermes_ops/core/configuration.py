from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
import tomllib
from typing import Any

from hermes_ops.core.errors import (
    ConfigurationMissingError,
    ConfigurationSchemaError,
    ConfigurationSyntaxError,
    ConfigurationUnsafePathError,
    PathResolutionError,
)
from hermes_ops.core.paths import direct_project_path, project_relative_path
from hermes_ops.core.platform_info import parse_version


CONFIG_RELATIVE_PATH = Path(".hermes/project.toml")


@dataclass(frozen=True, slots=True)
class ProjectSettings:
    name: str
    root_markers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    minimum_python: str
    python_candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GitSettings:
    required: bool
    protected_branches: tuple[str, ...]
    require_clean_worktree: bool


@dataclass(frozen=True, slots=True)
class TestSettings:
    targeted: tuple[str, ...]
    regression: tuple[str, ...]
    full: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SecuritySettings:
    protected_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    root: Path
    project: ProjectSettings
    runtime: RuntimeSettings
    git: GitSettings
    tests: TestSettings
    security: SecuritySettings

    @property
    def python_candidate_paths(self) -> tuple[Path, ...]:
        return tuple(
            project_relative_path(self.root, item)
            for item in self.runtime.python_candidates
        )

    @property
    def root_marker_paths(self) -> tuple[Path, ...]:
        return tuple(
            project_relative_path(self.root, item)
            for item in self.project.root_markers
        )


_SCHEMA: dict[str, set[str]] = {
    "project": {"name", "root_markers"},
    "runtime": {"minimum_python", "python_candidates"},
    "git": {"required", "protected_branches", "require_clean_worktree"},
    "tests": {"targeted", "regression", "full"},
    "security": {"protected_files"},
}

DEFAULT_ROOT_MARKERS = (".git", "pyproject.toml")
DEFAULT_MINIMUM_PYTHON = "3.11"
DEFAULT_PYTHON_CANDIDATES = (
    ".venv/Scripts/python.exe",
    ".venv/bin/python",
)
DEFAULT_GIT_REQUIRED = True
DEFAULT_PROTECTED_BRANCHES = ("main", "master", "production")
DEFAULT_REQUIRE_CLEAN_WORKTREE = True
DEFAULT_PROTECTED_FILES = (
    ".env",
    "*.db",
    "*.sqlite",
    "*.pem",
    "*.key",
)


def load_project_config(root: Path) -> ProjectConfig:
    path = project_config_path(root)
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError, OSError) as exc:
        raise ConfigurationSyntaxError(f"Invalid TOML in {path}: {exc}") from exc
    return parse_project_config(raw, root=root)


def project_config_path(root: Path) -> Path:
    try:
        path = direct_project_path(root, CONFIG_RELATIVE_PATH)
    except PathResolutionError as exc:
        raise ConfigurationUnsafePathError(str(exc)) from exc
    if not path.is_file():
        raise ConfigurationMissingError(f"Configuration not found: {path}")
    return path


def parse_project_config(raw: Any, *, root: Path) -> ProjectConfig:
    if not isinstance(raw, dict):
        raise ConfigurationSchemaError("Configuration root must be a table")
    unknown_sections = set(raw) - set(_SCHEMA)
    if unknown_sections:
        raise ConfigurationSchemaError(
            f"Unknown section(s): {', '.join(sorted(unknown_sections))}"
        )
    if "project" not in raw:
        raise ConfigurationSchemaError(
            "Missing required section: project"
        )
    for section, table in raw.items():
        fields = _SCHEMA[section]
        if not isinstance(table, dict):
            raise ConfigurationSchemaError(f"[{section}] must be a table")
        unknown = set(table) - fields
        if unknown:
            raise ConfigurationSchemaError(
                f"Unknown field(s) in [{section}]: {', '.join(sorted(unknown))}"
            )

    project = raw["project"]
    if "name" not in project:
        raise ConfigurationSchemaError("Missing required field: project.name")
    runtime = raw.get("runtime", {})
    git = raw.get("git", {})
    tests = raw.get("tests", {})
    security = raw.get("security", {})

    minimum_python = _string(
        runtime.get("minimum_python", DEFAULT_MINIMUM_PYTHON),
        "runtime.minimum_python",
    )
    try:
        parse_version(minimum_python)
    except ValueError as exc:
        raise ConfigurationSchemaError(
            "runtime.minimum_python must be a simple version such as 3.11 or 3.11.0"
        ) from exc

    config = ProjectConfig(
        root=root.resolve(),
        project=ProjectSettings(
            _string(project["name"], "project.name"),
            _nonempty_string_tuple(
                project.get("root_markers", list(DEFAULT_ROOT_MARKERS)),
                "project.root_markers",
            ),
        ),
        runtime=RuntimeSettings(
            minimum_python,
            _nonempty_string_tuple(
                runtime.get(
                    "python_candidates", list(DEFAULT_PYTHON_CANDIDATES)
                ),
                "runtime.python_candidates",
            ),
        ),
        git=GitSettings(
            _boolean(git.get("required", DEFAULT_GIT_REQUIRED), "git.required"),
            _string_tuple(
                git.get(
                    "protected_branches", list(DEFAULT_PROTECTED_BRANCHES)
                ),
                "git.protected_branches",
            ),
            _boolean(
                git.get(
                    "require_clean_worktree",
                    DEFAULT_REQUIRE_CLEAN_WORKTREE,
                ),
                "git.require_clean_worktree",
            ),
        ),
        tests=TestSettings(
            _string_tuple(tests.get("targeted", []), "tests.targeted"),
            _string_tuple(tests.get("regression", []), "tests.regression"),
            _string_tuple(tests.get("full", []), "tests.full"),
        ),
        security=SecuritySettings(
            _string_tuple(
                security.get(
                    "protected_files", list(DEFAULT_PROTECTED_FILES)
                ),
                "security.protected_files",
            )
        ),
    )
    _validate_contained_paths(
        config.root, config.project.root_markers, "project.root_markers"
    )
    _validate_contained_paths(
        config.root, config.runtime.python_candidates, "runtime.python_candidates"
    )
    return config


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationSchemaError(f"{name} must be a non-empty string")
    return value


def _string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ConfigurationSchemaError(f"{name} must be an array of strings")
    return tuple(value)


def _nonempty_string_tuple(value: Any, name: str) -> tuple[str, ...]:
    items = _string_tuple(value, name)
    if not items:
        raise ConfigurationSchemaError(f"{name} must not be empty")
    if any(not item.strip() for item in items):
        raise ConfigurationSchemaError(
            f"{name} must contain only non-empty strings"
        )
    return items


def _boolean(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigurationSchemaError(f"{name} must be a boolean")
    return value


def _validate_contained_paths(
    root: Path,
    values: tuple[str, ...],
    name: str,
) -> None:
    for value in values:
        try:
            project_relative_path(root, value)
        except PathResolutionError as exc:
            raise ConfigurationSchemaError(f"{name}: {exc}") from exc


def read_packaged_project_template() -> str:
    return (
        resources.files("hermes_ops.templates")
        .joinpath("project.toml")
        .read_text(encoding="utf-8")
    )
