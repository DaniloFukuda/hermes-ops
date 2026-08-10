from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import git
from conftest import VALID_CONFIG
from hermes_ops.cli import main


def _skill_cli_project(tmp_path: Path, *, other_skill: bool = False) -> Path:
    config = tmp_path / ".hermes/project.toml"
    config.parent.mkdir(parents=True)
    config.write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='cli-fixture'\nversion='1'\n",
        encoding="utf-8",
    )
    source = Path(__file__).resolve().parents[1] / "skills/git-preflight/SKILL.md"
    contract = source.read_text(encoding="utf-8")
    target = tmp_path / "skills/git-preflight/SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text(contract, encoding="utf-8")
    if other_skill:
        other = tmp_path / "skills/other-skill/SKILL.md"
        other.parent.mkdir(parents=True)
        other.write_text(
            contract.replace("id: git-preflight", "id: other-skill", 1),
            encoding="utf-8",
        )
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Hermes Skill CLI Test")
    git(tmp_path, "config", "user.email", "skill-cli@invalid.local")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture")
    return tmp_path


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


def test_skill_run_git_preflight_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-27"""
    project = _skill_cli_project(tmp_path)
    code = main(["skill", "run", "git-preflight", "--project", str(project), "--format", "text"])
    output = capsys.readouterr()
    assert code == 0
    assert "git-preflight" in output.out and "exit_code=0" in output.out
    assert "Traceback" not in output.err


@pytest.mark.parametrize("flag", ["--command", "--shell", "--handler", "--module", "--script", "--python"])
def test_skill_run_rejects_operational_flags(flag: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-28"""
    project = _skill_cli_project(tmp_path)
    with pytest.raises(SystemExit) as caught:
        main(["skill", "run", "git-preflight", "--project", str(project), flag, "payload"])
    assert caught.value.code == 2
    error = capsys.readouterr().err
    assert "unrecognized arguments" in error
    assert flag in error
    assert "Traceback" not in error


def test_skill_run_output_is_sanitized(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-29"""
    project = _skill_cli_project(tmp_path)
    main(["skill", "run", "git-preflight", "--project", str(project), "--format", "json"])
    output = capsys.readouterr().out
    assert str(project) not in output
    assert "<PROJECT_ROOT>" in output


def test_cli_uses_explicit_least_privilege_policy(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-34"""
    project = _skill_cli_project(tmp_path)
    code = main(["skill", "run", "git-preflight", "--project", str(project), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == payload["exit_code"] == 0
    assert payload["skill_id"] == "git-preflight"


def test_skill_run_semantic_errors_map_to_normative_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-46"""
    project = _skill_cli_project(tmp_path, other_skill=True)
    unsupported = main(["skill", "run", "other-skill", "--project", str(project), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert unsupported == 3
    assert payload["error"]["code"] == "SKILL_EXECUTION_NOT_SUPPORTED"
    assert payload["exit_code"] == 3


def test_generic_valid_id_reaches_closed_dispatch_through_run_skill(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-50"""
    project = _skill_cli_project(tmp_path, other_skill=True)
    code = main(["skill", "run", "other-skill", "--project", str(project), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 3
    assert payload["error"]["code"] == "SKILL_EXECUTION_NOT_SUPPORTED"


def test_real_repository_dogfooding_exercises_full_skill_pipeline(capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-51"""
    root = Path(__file__).resolve().parents[1]
    code = main(["skill", "run", "git-preflight", "--project", str(root), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == payload["exit_code"]
    assert payload["skill_id"] == "git-preflight"
    assert payload["evidence"]
