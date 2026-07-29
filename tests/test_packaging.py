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
