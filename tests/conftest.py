from __future__ import annotations

from pathlib import Path
import subprocess

import pytest


VALID_CONFIG = """\
[project]
name = "temporary-project"
root_markers = [".git", "pyproject.toml"]

[runtime]
minimum_python = "3.11"
python_candidates = [".venv/Scripts/python.exe", ".venv/bin/python"]

[git]
required = true
protected_branches = ["main", "master", "production"]
require_clean_worktree = true

[tests]
targeted = []
regression = []
full = []

[security]
protected_files = [".env", "*.db", "*.sqlite", "*.pem", "*.key"]
"""


@pytest.fixture
def configured_project(tmp_path: Path) -> Path:
    config_dir = tmp_path / ".hermes"
    config_dir.mkdir()
    (config_dir / "project.toml").write_text(VALID_CONFIG, encoding="utf-8")
    return tmp_path


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


@pytest.fixture
def empty_git_repo(configured_project: Path) -> Path:
    git(configured_project, "init", "-b", "main")
    return configured_project


@pytest.fixture
def committed_git_repo(empty_git_repo: Path) -> Path:
    git(empty_git_repo, "config", "user.name", "Hermes Ops Test")
    git(empty_git_repo, "config", "user.email", "test@invalid.local")
    (empty_git_repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
    git(empty_git_repo, "add", "tracked.txt", ".hermes/project.toml")
    git(empty_git_repo, "commit", "-m", "initial")
    return empty_git_repo
