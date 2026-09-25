from __future__ import annotations

import json
import os
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


def _skill_cli_target(tmp_path: Path) -> Path:
    config = tmp_path / ".hermes/project.toml"
    config.parent.mkdir(parents=True)
    config.write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='external-cli-target'\nversion='1'\n",
        encoding="utf-8",
    )
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Hermes External CLI Test")
    git(tmp_path, "config", "user.email", "external-cli@invalid.local")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture")
    assert not (tmp_path / "skills").exists()
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
    assert payload["error"]["code"] == "SKILL_PLAN_SKILL_NOT_FOUND"
    assert payload["exit_code"] == 3


def test_generic_valid_id_reaches_closed_dispatch_through_run_skill(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-50"""
    project = _skill_cli_project(tmp_path, other_skill=True)
    code = main(["skill", "run", "other-skill", "--project", str(project), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 3
    assert payload["error"]["code"] == "SKILL_PLAN_SKILL_NOT_FOUND"


def test_real_repository_dogfooding_exercises_full_skill_pipeline(capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0006 / AC-51"""
    root = Path(__file__).resolve().parents[1]
    code = main(["skill", "run", "git-preflight", "--project", str(root), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == payload["exit_code"]
    assert payload["skill_id"] == "git-preflight"
    assert payload["evidence"]


def test_skill_run_project_option_means_target_project(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-02"""
    target = _skill_cli_target(tmp_path)
    code = main(
        ["skill", "run", "git-preflight", "--project", str(target), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == payload["exit_code"] == 0
    assert payload["skill_id"] == "git-preflight"


def test_skill_run_target_does_not_require_skills_directory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-03"""
    target = _skill_cli_target(tmp_path)
    assert not (target / "skills").exists()
    code = main(["skill", "run", "git-preflight", "--project", str(target)])
    output = capsys.readouterr()
    assert code == 0
    assert "status=passed" in output.out
    assert "exit_code=0" in output.out


def test_unknown_catalog_skill_fails_closed_with_exit_code_three(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-08"""
    target = _skill_cli_target(tmp_path)
    code = main(
        ["skill", "run", "missing-skill", "--project", str(target), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == payload["exit_code"] == 3
    assert payload["error"]["code"] == "SKILL_PLAN_SKILL_NOT_FOUND"


def test_missing_target_project_fails_closed_before_handler(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-09"""
    missing = tmp_path / "missing-target"
    code = main(
        ["skill", "run", "git-preflight", "--project", str(missing), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == payload["exit_code"] == 3
    assert payload["error"]["code"] == "SKILL_TARGET_INVALID"


def test_skill_run_external_clean_clone_dogfooding(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-17"""
    if os.environ.get("HERMES_RUN_EXTERNAL_DOGFOODING") != "1":
        pytest.skip("Real external clone dogfooding is an explicit post-suite acceptance step")
    target = Path(r"C:\example\external-clean-clone")
    assert target.is_dir()
    assert not (target / "skills").exists()
    before = (
        git(target, "rev-parse", "HEAD").stdout,
        git(target, "status", "--porcelain=v1", "-z").stdout,
        git(target, "diff", "--cached", "--name-status").stdout,
        git(target, "show-ref").stdout,
    )
    code = main(["skill", "run", "git-preflight", "--project", str(target)])
    output = capsys.readouterr().out
    after = (
        git(target, "rev-parse", "HEAD").stdout,
        git(target, "status", "--porcelain=v1", "-z").stdout,
        git(target, "diff", "--cached", "--name-status").stdout,
        git(target, "show-ref").stdout,
    )
    assert code == 0
    assert "status=passed" in output and "exit_code=0" in output
    assert after == before


def test_skill_run_output_and_errors_are_sanitized(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-18"""
    missing = tmp_path / "private-target"
    code = main(
        ["skill", "run", "git-preflight", "--project", str(missing), "--format", "json"]
    )
    output = capsys.readouterr()
    assert code == 3
    assert str(missing) not in output.out
    assert "Traceback" not in output.out + output.err


def test_existing_skill_run_invocation_remains_compatible(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-20"""
    root = Path(__file__).resolve().parents[1]
    code = main(["skill", "run", "git-preflight", "--project", str(root)])
    output = capsys.readouterr().out
    assert code in {0, 3}
    assert "skill_id=git-preflight" in output
    assert "exit_code=" in output


@pytest.mark.parametrize("flag", ["--skills-root", "--catalog", "--hermes-root"])
def test_skill_run_has_no_catalog_override_option(
    flag: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0007 / AC-25"""
    target = _skill_cli_target(tmp_path)
    with pytest.raises(SystemExit) as caught:
        main(
            [
                "skill",
                "run",
                "git-preflight",
                "--project",
                str(target),
                flag,
                "payload",
            ]
        )
    assert caught.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_skill_run_code_audit_text_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0008 / AC-31"""
    target = _skill_cli_target(tmp_path)
    (target / "risk.py").write_text("verify=False\n", encoding="utf-8")
    code = main(["skill", "run", "code-audit", "--project", str(target), "--format", "text"])
    output = capsys.readouterr().out
    assert code == 3
    for expected in (
        "status=completed_with_findings", "[HIGH] CA003 observed", "file=risk.py",
        "region=1:1-1:12", "evidence=verify=False", "observation=",
        "justification=", "suggestion=", "exit_code=3",
    ):
        assert expected in output


def test_skill_run_code_audit_json_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0008 / AC-32"""
    target = _skill_cli_target(tmp_path)
    (target / "risk.ts").write_text("eval(value);\n", encoding="utf-8")
    code = main(["skill", "run", "code-audit", "--project", str(target), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == payload["exit_code"] == 3
    assert payload["skill_id"] == "code-audit"
    finding = payload["evidence"][1]["details"]
    assert finding["rule_id"] == "CA001"
    assert set(finding).issuperset({
        "severity", "classification", "file", "region", "evidence",
        "observation", "justification", "suggestion",
    })


@pytest.mark.parametrize("flag", ["--skills-root", "--include", "--exclude", "--rule"])
def test_code_audit_adds_no_public_operational_option(
    flag: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0008 / AC-33"""
    target = _skill_cli_target(tmp_path)
    with pytest.raises(SystemExit) as caught:
        main(["skill", "run", "code-audit", "--project", str(target), flag, "value"])
    assert caught.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_code_audit_cli_never_exposes_absolute_or_unsafe_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0008 / AC-34"""
    target = _skill_cli_target(tmp_path)
    secret = "cli-secret-sentinel"
    (target / "risk.py").write_text(f'api_token = "{secret}"\n', encoding="utf-8")
    code = main(["skill", "run", "code-audit", "--project", str(target), "--format", "json"])
    output = capsys.readouterr()
    assert code == 3
    assert str(target) not in output.out + output.err
    assert secret not in output.out + output.err
    assert "Traceback" not in output.out + output.err


def test_code_audit_exit_status_distinguishes_clean_findings_and_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec: HERMES-0008 / AC-35"""
    clean = tmp_path / "clean"
    clean.mkdir()
    assert main(["skill", "run", "code-audit", "--project", str(clean)]) == 0
    assert "status=passed" in capsys.readouterr().out

    (clean / "risk.py").write_text("verify=False\n", encoding="utf-8")
    assert main(["skill", "run", "code-audit", "--project", str(clean)]) == 3
    assert "status=completed_with_findings" in capsys.readouterr().out

    missing = tmp_path / "missing"
    assert main(["skill", "run", "code-audit", "--project", str(missing)]) == 3
    assert "ERRO SKILL_TARGET_INVALID" in capsys.readouterr().err
