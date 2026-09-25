from pathlib import Path
import subprocess
import sys

import pytest

from conftest import VALID_CONFIG
from hermes_ops.core.configuration import load_project_config
from hermes_ops.core.configuration import (
    DEFAULT_GIT_REQUIRED,
    DEFAULT_MINIMUM_PYTHON,
    DEFAULT_PROTECTED_BRANCHES,
    DEFAULT_PROTECTED_FILES,
    DEFAULT_PYTHON_CANDIDATES,
    DEFAULT_REQUIRE_CLEAN_WORKTREE,
    DEFAULT_ROOT_MARKERS,
    read_packaged_project_template,
)
from hermes_ops.core.errors import (
    ConfigurationMissingError,
    ConfigurationSchemaError,
    ConfigurationSyntaxError,
    ConfigurationUnsafePathError,
)


def write_config(root: Path, content: str) -> None:
    directory = root / ".hermes"
    directory.mkdir()
    (directory / "project.toml").write_text(content, encoding="utf-8")


def test_missing_configuration(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationMissingError):
        load_project_config(tmp_path)


def test_empty_configuration(tmp_path: Path) -> None:
    write_config(tmp_path, "")
    with pytest.raises(ConfigurationSchemaError):
        load_project_config(tmp_path)


def test_malformed_toml(tmp_path: Path) -> None:
    write_config(tmp_path, "[project\n")
    with pytest.raises(ConfigurationSyntaxError):
        load_project_config(tmp_path)


def test_missing_required_field(tmp_path: Path) -> None:
    write_config(tmp_path, VALID_CONFIG.replace('name = "temporary-project"\n', ""))
    with pytest.raises(ConfigurationSchemaError, match="Missing required field"):
        load_project_config(tmp_path)


def test_incorrect_type(tmp_path: Path) -> None:
    write_config(tmp_path, VALID_CONFIG.replace("required = true", 'required = "yes"'))
    with pytest.raises(ConfigurationSchemaError, match="boolean"):
        load_project_config(tmp_path)


def test_unknown_field(tmp_path: Path) -> None:
    write_config(tmp_path, VALID_CONFIG.replace("[runtime]", "typo = true\n\n[runtime]"))
    with pytest.raises(ConfigurationSchemaError, match="Unknown field"):
        load_project_config(tmp_path)


def test_valid_configuration_and_relative_candidates(configured_project: Path) -> None:
    config = load_project_config(configured_project)
    assert config.project.name == "temporary-project"
    assert config.python_candidate_paths[0] == (
        configured_project / ".venv/Scripts/python.exe"
    ).resolve()


@pytest.mark.parametrize(
    "version",
    ["banana", "3", "3.x", ">=3.11", "", "-3.11"],
)
def test_invalid_minimum_python(tmp_path: Path, version: str) -> None:
    write_config(
        tmp_path,
        VALID_CONFIG.replace(
            'minimum_python = "3.11"', f'minimum_python = "{version}"'
        ),
    )
    with pytest.raises(ConfigurationSchemaError, match="runtime.minimum_python"):
        load_project_config(tmp_path)


@pytest.mark.parametrize("version", ["3.11", "3.11.0", "3.13"])
def test_valid_minimum_python(tmp_path: Path, version: str) -> None:
    write_config(
        tmp_path,
        VALID_CONFIG.replace(
            'minimum_python = "3.11"', f'minimum_python = "{version}"'
        ),
    )
    assert load_project_config(tmp_path).runtime.minimum_python == version


@pytest.mark.parametrize(
    "candidate",
    ["../outside", "../../file", "C:\\outside\\python.exe", "/outside/python"],
)
def test_invalid_python_candidate_escape(tmp_path: Path, candidate: str) -> None:
    content = VALID_CONFIG.replace(
        'python_candidates = [".venv/Scripts/python.exe", ".venv/bin/python"]',
        f'python_candidates = ["{candidate.replace(chr(92), chr(92) * 2)}"]',
    )
    write_config(tmp_path, content)
    with pytest.raises(ConfigurationSchemaError):
        load_project_config(tmp_path)


def test_env_file_is_not_a_configuration_source(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("PROJECT_NAME=must-not-load\n", encoding="utf-8")
    with pytest.raises(ConfigurationMissingError):
        load_project_config(tmp_path)


def test_minimal_configuration_receives_all_defaults(tmp_path: Path) -> None:
    write_config(tmp_path, '[project]\nname = "minimal"\n')
    config = load_project_config(tmp_path)
    assert config.project.root_markers == DEFAULT_ROOT_MARKERS
    assert config.runtime.minimum_python == DEFAULT_MINIMUM_PYTHON
    assert config.runtime.python_candidates == DEFAULT_PYTHON_CANDIDATES
    assert config.git.required is DEFAULT_GIT_REQUIRED
    assert config.git.protected_branches == DEFAULT_PROTECTED_BRANCHES
    assert config.git.require_clean_worktree is DEFAULT_REQUIRE_CLEAN_WORKTREE
    assert config.tests.targeted == ()
    assert config.tests.regression == ()
    assert config.tests.full == ()
    assert config.security.protected_files == DEFAULT_PROTECTED_FILES


def test_partial_configuration_overrides_only_declared_values(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        """\
[project]
name = "partial"

[git]
require_clean_worktree = false
""",
    )
    config = load_project_config(tmp_path)
    assert not config.git.require_clean_worktree
    assert config.git.protected_branches == DEFAULT_PROTECTED_BRANCHES
    assert config.runtime.minimum_python == DEFAULT_MINIMUM_PYTHON


def test_packaged_template_is_valid_and_compatible(tmp_path: Path) -> None:
    text = read_packaged_project_template()
    assert text.count("[project]") == 1
    write_config(tmp_path, text)
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    config = load_project_config(tmp_path)
    assert config.project.name == "example-project"


def _create_directory_indirection(link: Path, target: Path) -> None:
    if sys.platform == "win32":
        completed = subprocess.run(
            ("cmd", "/c", "mklink", "/J", str(link), str(target)),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            pytest.skip("Directory junctions are not available")
    else:
        link.symlink_to(target, target_is_directory=True)


def test_configuration_parent_junction_is_rejected_before_read(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "project.toml").write_text(
        '[project]\nname = "must-not-load"\n',
        encoding="utf-8",
    )
    _create_directory_indirection(root / ".hermes", outside)
    with pytest.raises(ConfigurationUnsafePathError):
        load_project_config(root)


def test_configuration_file_symlink_is_rejected_before_read(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside.toml"
    (root / ".hermes").mkdir(parents=True)
    outside.write_text(
        '[project]\nname = "must-not-load"\n',
        encoding="utf-8",
    )
    try:
        (root / ".hermes/project.toml").symlink_to(outside)
    except OSError:
        pytest.skip("File symlinks are not available")
    with pytest.raises(ConfigurationUnsafePathError):
        load_project_config(root)
