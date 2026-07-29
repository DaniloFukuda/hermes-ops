from pathlib import Path

from conftest import git
from hermes_ops.commands.doctor import run_doctor
from hermes_ops.commands.preflight import run_preflight
from hermes_ops.commands.worktree import run_worktree


def test_doctor_missing_path_is_blocked(tmp_path: Path) -> None:
    report = run_doctor(tmp_path / "missing")
    assert report.exit_code == 3


def test_subdirectory_does_not_select_ancestor(empty_git_repo: Path) -> None:
    nested = empty_git_repo / "nested"
    nested.mkdir()
    report = run_doctor(nested)
    assert report.exit_code == 3
    assert report.results[-1].code == "root_configuration_missing"
    assert report.results[-1].details["root"] == nested.resolve()


def test_root_requires_at_least_one_configured_marker(configured_project: Path) -> None:
    report = run_doctor(configured_project)
    assert report.exit_code == 3
    assert any(item.code == "root_markers_missing" for item in report.results)


def test_doctor_valid_project(empty_git_repo: Path) -> None:
    report = run_doctor(empty_git_repo)
    assert report.exit_code == 0
    assert any(item.name == "configuration" for item in report.results)


def test_worktree_empty_repository(empty_git_repo: Path) -> None:
    report = run_worktree(empty_git_repo)
    details = report.results[0].details
    assert details["has_commits"] is False
    assert details["head"] is None


def test_protected_branch_is_warning_not_failure(empty_git_repo: Path) -> None:
    report = run_worktree(empty_git_repo)
    assert report.results[0].code == "protected_branch"
    assert report.exit_code == 0


def test_preflight_blocks_dirty_tree(committed_git_repo: Path) -> None:
    (committed_git_repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    report = run_preflight(committed_git_repo)
    assert report.exit_code == 3
    assert any(item.code == "worktree_required_clean" for item in report.results)


def test_preflight_clean_tree_passes_after_tracking_config(
    committed_git_repo: Path,
) -> None:
    report = run_preflight(committed_git_repo)
    assert report.exit_code == 0
