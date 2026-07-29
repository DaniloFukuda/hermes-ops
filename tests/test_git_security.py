from __future__ import annotations

import os
from pathlib import Path
import stat
import sys

from conftest import VALID_CONFIG, git
from hermes_ops.core.processes import ProcessResult
from hermes_ops.git.environment import safe_git_environment
from hermes_ops.git.inspector import GitInspector


def make_repo(root: Path, *, commit: bool = True) -> Path:
    root.mkdir()
    config_dir = root / ".hermes"
    config_dir.mkdir()
    (config_dir / "project.toml").write_text(VALID_CONFIG, encoding="utf-8")
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Hermes Ops Test")
    git(root, "config", "user.email", "test@invalid.local")
    if commit:
        (root / "tracked.txt").write_text("initial\n", encoding="utf-8")
        git(root, "add", ".hermes/project.toml", "tracked.txt")
        git(root, "commit", "-m", "initial")
    return root


def snapshot_tree(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.name.endswith(".lock")
    }


def test_safe_environment_removes_all_inherited_git_variables() -> None:
    source = {
        "PATH": "kept",
        "SystemRoot": "kept",
        "GIT_DIR": "hostile",
        "git_work_tree": "hostile",
        "GIT_CONFIG_KEY_0": "hostile",
    }
    result = safe_git_environment(source)
    assert result["PATH"] == "kept"
    assert result["SystemRoot"] == "kept"
    assert result["GIT_OPTIONAL_LOCKS"] == "0"
    assert result["GIT_TERMINAL_PROMPT"] == "0"
    assert "GIT_DIR" not in result
    assert "git_work_tree" not in result
    assert "GIT_CONFIG_KEY_0" not in result
    assert source["GIT_DIR"] == "hostile"


def test_hostile_git_environment_cannot_redirect_inspection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = make_repo(tmp_path / "target")
    hostile = make_repo(tmp_path / "hostile")
    alternate_index = tmp_path / "alternate-index"
    hostile_before = snapshot_tree(hostile)
    target_head = git(target, "rev-parse", "HEAD").stdout.strip()
    values = {
        "GIT_DIR": str(hostile / ".git"),
        "GIT_WORK_TREE": str(hostile),
        "GIT_INDEX_FILE": str(alternate_index),
        "GIT_COMMON_DIR": str(hostile / ".git"),
        "GIT_OBJECT_DIRECTORY": str(hostile / ".git" / "objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(hostile / ".git" / "objects"),
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.bare",
        "GIT_CONFIG_VALUE_0": "true",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    state = GitInspector().inspect(target)

    assert state.root == str(target.resolve())
    assert state.head == target_head
    assert state.branch == "main"
    assert snapshot_tree(hostile) == hostile_before
    assert not alternate_index.exists()
    for key, value in values.items():
        assert os.environ[key] == value


def test_inspection_is_byte_for_byte_immutable(tmp_path: Path) -> None:
    target = make_repo(tmp_path / "target")
    (target / "untracked ação.txt").write_text("untracked\n", encoding="utf-8")
    status_before = git(target, "status", "--porcelain=v1", "-z").stdout
    before = snapshot_tree(target)
    state = GitInspector().inspect(target)
    status_after = git(target, "status", "--porcelain=v1", "-z").stdout
    after = snapshot_tree(target)

    assert state.is_repository
    assert before == after
    assert status_before == status_after
    assert not list((target / ".git").rglob("*.lock"))


def test_empty_repository_absence_states_remain_unchanged(tmp_path: Path) -> None:
    target = make_repo(tmp_path / "target", commit=False)
    before = snapshot_tree(target)
    state = GitInspector().inspect(target)
    assert not state.has_commits
    assert state.head is None
    assert snapshot_tree(target) == before
    assert not list((target / ".git").rglob("*.lock"))


def test_operational_git_error_is_not_not_repository(tmp_path: Path) -> None:
    def failing_runner(*args, **kwargs):
        return ProcessResult(
            str(tmp_path),
            128,
            "",
            "fatal: permission denied",
            True,
            False,
        )

    state = GitInspector(runner=failing_runner).inspect(tmp_path)
    assert not state.is_repository
    assert state.error_code == "git_permission_denied"
    assert state.error


def test_false_probe_output_is_a_root_mismatch(tmp_path: Path) -> None:
    def unexpected_runner(*args, **kwargs):
        return ProcessResult(str(tmp_path), 0, "maybe\n", "", True, False)

    state = GitInspector(runner=unexpected_runner).inspect(tmp_path)
    assert state.error_code == "git_root_mismatch"


def test_root_mismatch_stops_before_status(tmp_path: Path) -> None:
    declared = tmp_path / "declared"
    other = tmp_path / "other"
    declared.mkdir()
    other.mkdir()
    calls: list[tuple[str, ...]] = []

    def runner(args, **kwargs):
        calls.append(tuple(args))
        if "--is-inside-work-tree" in args:
            return ProcessResult(str(declared), 0, "true\n", "", True, False)
        if "--show-toplevel" in args:
            return ProcessResult(
                str(declared), 0, f"{other}\n", "", True, False
            )
        raise AssertionError("No command may run after a root mismatch")

    state = GitInspector(runner=runner).inspect(declared)
    assert state.error_code == "git_root_mismatch"
    assert len(calls) == 2
    assert not any("status" in call for call in calls)
    assert all(call[1:3] == ("-c", "core.fsmonitor=false") for call in calls)


def test_git_file_redirected_to_external_repository_is_blocked(
    tmp_path: Path,
) -> None:
    external = make_repo(tmp_path / "external")
    declared = tmp_path / "declared"
    declared.mkdir()
    (declared / ".git").write_text(
        f"gitdir: {(external / '.git').as_posix()}\n",
        encoding="utf-8",
    )
    state = GitInspector().inspect(declared)
    assert state.error_code == "git_indirect_repository_unsupported"


def test_external_core_worktree_is_blocked(tmp_path: Path) -> None:
    declared = make_repo(tmp_path / "declared")
    external = tmp_path / "external-worktree"
    external.mkdir()
    git(declared, "config", "core.worktree", str(external))
    state = GitInspector().inspect(declared)
    assert state.error_code == "git_root_mismatch"
    assert not state.clean or state.error is not None


def test_hostile_fsmonitor_is_not_executed(tmp_path: Path) -> None:
    if sys.platform == "win32":
        import pytest

        pytest.skip("Executable fsmonitor fixture is validated on Linux CI")
    target = make_repo(tmp_path / "target")
    marker = tmp_path / "fsmonitor-executed"
    hook = tmp_path / "hostile-fsmonitor.sh"
    hook.write_text(
        f"#!/bin/sh\nprintf executed > '{marker}'\n",
        encoding="utf-8",
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    git(target, "config", "core.fsmonitor", str(hook))
    state = GitInspector().inspect(target)
    assert state.is_repository
    assert not marker.exists()
