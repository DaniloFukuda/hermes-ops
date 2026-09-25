from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tarfile
import venv
import zipfile

import pytest

from conftest import git


@pytest.fixture(scope="session")
def built_artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    output = tmp_path_factory.mktemp("artifacts")
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(output),
        ),
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    wheel = next(output.glob("*.whl"))
    sdist = next(output.glob("*.tar.gz"))
    return {"wheel": wheel, "sdist": sdist}


def test_wheel_contains_runtime_template_and_no_forbidden_files(
    built_artifacts: dict[str, Path],
) -> None:
    source_root = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(built_artifacts["wheel"]) as archive:
        names = archive.namelist()
        contents = b"\n".join(archive.read(name) for name in names)
    assert "hermes_ops/__main__.py" in names
    assert "hermes_ops/templates/project.toml" in names
    assert any(name.endswith(".dist-info/METADATA") for name in names)
    assert not any(name.startswith("tests/") for name in names)
    assert not any(".venv" in name for name in names)
    assert not any("__pycache__" in name for name in names)
    assert not any(Path(name).name in {".env", ".env.local"} for name in names)
    assert str(source_root).encode("utf-8") not in contents


def test_sdist_contains_source_template_readme_and_metadata(
    built_artifacts: dict[str, Path],
) -> None:
    with tarfile.open(built_artifacts["sdist"], "r:gz") as archive:
        names = archive.getnames()
    assert any(name.endswith("/README.md") for name in names)
    assert any(
        name.endswith("/src/hermes_ops/templates/project.toml")
        for name in names
    )
    assert any(name.endswith("/pyproject.toml") for name in names)
    assert any(name.endswith("/tests/conftest.py") for name in names)
    assert not any("/.venv/" in name for name in names)
    assert not any("__pycache__" in name for name in names)


def test_wheel_installs_and_runs_all_commands_in_isolation(
    built_artifacts: dict[str, Path],
    tmp_path: Path,
) -> None:
    environment = tmp_path / "wheel-venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = (
        environment / "Scripts/python.exe"
        if sys.platform == "win32"
        else environment / "bin/python"
    )
    install = subprocess.run(
        (
            str(python),
            "-m",
            "pip",
            "install",
            "--no-deps",
            str(built_artifacts["wheel"]),
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert install.returncode == 0, install.stdout + install.stderr

    help_result = subprocess.run(
        (str(python), "-m", "hermes_ops", "--help"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert help_result.returncode == 0
    assert "doctor" in help_result.stdout

    template_result = subprocess.run(
        (
            str(python),
            "-c",
            (
                "from hermes_ops.core.configuration import "
                "read_packaged_project_template; "
                "print(read_packaged_project_template())"
            ),
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert template_result.returncode == 0
    assert '[project]' in template_result.stdout

    project = tmp_path / "demo project ação"
    config_dir = project / ".hermes"
    config_dir.mkdir(parents=True)
    (config_dir / "project.toml").write_text(
        '[project]\nname = "wheel-demo"\n',
        encoding="utf-8",
    )
    git(project, "init", "-b", "main")
    git(project, "config", "user.name", "Hermes Ops Test")
    git(project, "config", "user.email", "test@invalid.local")
    git(project, "add", ".hermes/project.toml")
    git(project, "commit", "-m", "initial")

    for command in ("doctor", "worktree", "preflight"):
        completed = subprocess.run(
            (
                str(python),
                "-m",
                "hermes_ops",
                command,
                "--project",
                str(project),
                "--format",
                "json",
            ),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["command"] == command
        assert str(project) not in completed.stdout
        assert "<PROJECT_ROOT>" in completed.stdout

    skill = subprocess.run(
        (
            str(python),
            "-m",
            "hermes_ops",
            "skill",
            "run",
            "git-preflight",
            "--project",
            str(project),
            "--format",
            "json",
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert skill.returncode == 0, skill.stdout + skill.stderr
    payload = json.loads(skill.stdout)
    assert payload["skill_id"] == "git-preflight"
    assert payload["status"] == "passed"
    assert not (project / "skills").exists()

    (project / "source.py").write_text("def safe(value):\n    return value\n", encoding="utf-8")
    audit = subprocess.run(
        (
            str(python), "-m", "hermes_ops", "skill", "run", "code-audit",
            "--project", str(project), "--format", "json",
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert audit.returncode == 0, audit.stdout + audit.stderr
    audit_payload = json.loads(audit.stdout)
    assert audit_payload["skill_id"] == "code-audit"
    assert audit_payload["status"] == "passed"
    assert not (project / "skills").exists()


def test_wheel_and_sdist_include_own_skill_catalog(
    built_artifacts: dict[str, Path],
) -> None:
    """Spec: HERMES-0007 / AC-24"""
    canonical = (
        Path(__file__).resolve().parents[1]
        / "skills/git-preflight/SKILL.md"
    ).read_bytes()
    wheel_suffix = "hermes_ops_skill_catalog/skills/git-preflight/SKILL.md"
    with zipfile.ZipFile(built_artifacts["wheel"]) as archive:
        wheel_matches = [
            name for name in archive.namelist() if name.endswith(wheel_suffix)
        ]
        assert len(wheel_matches) == 1
        assert archive.read(wheel_matches[0]) == canonical

    with tarfile.open(built_artifacts["sdist"], "r:gz") as archive:
        sdist_matches = [
            member
            for member in archive.getmembers()
            if member.name.endswith("/skills/git-preflight/SKILL.md")
        ]
        assert len(sdist_matches) == 1
        extracted = archive.extractfile(sdist_matches[0])
        assert extracted is not None
        assert extracted.read() == canonical


def test_wheel_contains_complete_canonical_code_audit_skill(
    built_artifacts: dict[str, Path],
) -> None:
    """Spec: HERMES-0008 / AC-39"""
    canonical = (Path(__file__).resolve().parents[1] / "skills/code-audit/SKILL.md").read_bytes()
    suffix = "hermes_ops_skill_catalog/skills/code-audit/SKILL.md"
    with zipfile.ZipFile(built_artifacts["wheel"]) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
        assert len(matches) == 1
        assert archive.read(matches[0]) == canonical


def test_sdist_contains_complete_canonical_code_audit_skill(
    built_artifacts: dict[str, Path],
    tmp_path: Path,
) -> None:
    """Spec: HERMES-0008 / AC-40"""
    canonical = (Path(__file__).resolve().parents[1] / "skills/code-audit/SKILL.md").read_bytes()
    with tarfile.open(built_artifacts["sdist"], "r:gz") as archive:
        matches = [
            member for member in archive.getmembers()
            if member.name.endswith("/skills/code-audit/SKILL.md")
        ]
        assert len(matches) == 1
        extracted = archive.extractfile(matches[0])
        assert extracted is not None
        assert extracted.read() == canonical

    rebuilt = tmp_path / "rebuilt"
    completed = subprocess.run(
        (
            sys.executable, "-m", "pip", "wheel", "--no-deps",
            "--no-build-isolation", "--wheel-dir", str(rebuilt),
            str(built_artifacts["sdist"]),
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    rebuilt_wheel = next(rebuilt.glob("*.whl"))
    with zipfile.ZipFile(rebuilt_wheel) as archive:
        matches = [
            name for name in archive.namelist()
            if name.endswith("hermes_ops_skill_catalog/skills/code-audit/SKILL.md")
        ]
        assert len(matches) == 1
        assert archive.read(matches[0]) == canonical


def test_wheel_and_sdist_contain_canonical_mission_audit_skill(
    built_artifacts: dict[str, Path],
) -> None:
    """Spec: HERMES-0009 / AC-44"""
    canonical = (Path(__file__).resolve().parents[1] / "skills/mission-audit/SKILL.md").read_bytes()
    suffix = "hermes_ops_skill_catalog/skills/mission-audit/SKILL.md"
    with zipfile.ZipFile(built_artifacts["wheel"]) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
        assert len(matches) == 1 and archive.read(matches[0]) == canonical
    with tarfile.open(built_artifacts["sdist"], "r:gz") as archive:
        matches = [member for member in archive.getmembers() if member.name.endswith("/skills/mission-audit/SKILL.md")]
        assert len(matches) == 1
        extracted = archive.extractfile(matches[0])
        assert extracted is not None and extracted.read() == canonical


def test_wheel_and_sdist_include_analysis_contract_without_provider(
    built_artifacts: dict[str, Path],
) -> None:
    """Spec: HERMES-0010 / AC-35"""
    expected = "hermes_ops/analysis/adapter.py"
    with zipfile.ZipFile(built_artifacts["wheel"]) as archive:
        assert any(name.endswith(expected) for name in archive.namelist())
    with tarfile.open(built_artifacts["sdist"], "r:gz") as archive:
        assert any(member.name.endswith(expected) for member in archive.getmembers())
