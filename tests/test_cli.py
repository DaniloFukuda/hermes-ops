from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import git
from conftest import VALID_CONFIG
from hermes_ops.cli import main


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "doctor" in capsys.readouterr().out


def test_invalid_command_has_no_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["unknown"])
    assert exc.value.code == 2
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize("command", ["doctor", "worktree", "preflight"])
def test_json_output_is_valid(
    command: str,
    empty_git_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main([command, "--project", str(empty_git_repo), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == command
    assert payload["exit_code"] == code


def test_text_is_default(
    empty_git_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["doctor", "--project", str(empty_git_repo)])
    output = capsys.readouterr().out
    assert "exit_code=" in output
    assert not output.lstrip().startswith("{")


def test_module_runs_from_outside_project(empty_git_repo: Path, tmp_path: Path) -> None:
    git(empty_git_repo, "add", ".hermes/project.toml")
    git(empty_git_repo, "config", "user.name", "Hermes Ops Test")
    git(empty_git_repo, "config", "user.email", "test@invalid.local")
    git(empty_git_repo, "commit", "-m", "configuration")
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "hermes_ops",
            "preflight",
            "--project",
            str(empty_git_repo),
            "--format",
            "json",
        ),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["command"] == "preflight"
    assert "Traceback" not in completed.stderr


def test_missing_path_exit_code_and_no_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        ["doctor", "--project", str(tmp_path / "missing"), "--format", "json"]
    )
    output = capsys.readouterr()
    assert code == 3
    assert json.loads(output.out)["exit_code"] == 3
    assert "Traceback" not in output.err


def test_subdirectory_is_blocked_in_text_and_json(
    empty_git_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    nested = empty_git_repo / "nested"
    nested.mkdir()
    text_code = main(["doctor", "--project", str(nested), "--format", "text"])
    text = capsys.readouterr()
    assert text_code == 3
    assert "BLOQUEADO" in text.out
    assert "Traceback" not in text.err

    json_code = main(["doctor", "--project", str(nested), "--format", "json"])
    output = capsys.readouterr()
    assert json_code == 3
    assert json.loads(output.out)["exit_code"] == 3
    assert "Traceback" not in output.err


def test_invalid_minimum_python_returns_configuration_exit_code(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_dir = tmp_path / ".hermes"
    config_dir.mkdir()
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (config_dir / "project.toml").write_text(
        VALID_CONFIG.replace(
            'minimum_python = "3.11"', 'minimum_python = "banana"'
        ),
        encoding="utf-8",
    )
    code = main(["doctor", "--project", str(tmp_path), "--format", "json"])
    output = capsys.readouterr()
    assert code == 2
    assert json.loads(output.out)["exit_code"] == 2
    assert "Traceback" not in output.err
