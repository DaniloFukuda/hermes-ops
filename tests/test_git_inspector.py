from pathlib import Path

from conftest import git
from hermes_ops.git.inspector import GitInspector


def test_directory_without_repository(tmp_path: Path) -> None:
    state = GitInspector().inspect(tmp_path)
    assert state.available
    assert not state.is_repository


def test_git_unavailable(tmp_path: Path) -> None:
    state = GitInspector(executable="missing-git-hermes-ops").inspect(tmp_path)
    assert not state.available
    assert state.error


def test_empty_repository_has_no_head(empty_git_repo: Path) -> None:
    state = GitInspector().inspect(empty_git_repo)
    assert state.is_repository
    assert state.branch == "main"
    assert not state.has_commits
    assert state.head is None


def test_first_commit_and_clean_tree(committed_git_repo: Path) -> None:
    state = GitInspector().inspect(committed_git_repo)
    assert state.has_commits
    assert state.head
    assert state.branch == "main"
    assert state.clean


def test_detached_head(committed_git_repo: Path) -> None:
    git(committed_git_repo, "checkout", "--detach")
    state = GitInspector().inspect(committed_git_repo)
    assert state.detached
    assert state.branch is None


def test_modified_added_removed_untracked_and_unicode(
    committed_git_repo: Path,
) -> None:
    (committed_git_repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    (committed_git_repo / "added ação.txt").write_text("new\n", encoding="utf-8")
    git(committed_git_repo, "add", "added ação.txt")
    (committed_git_repo / "removed.txt").write_text("remove\n", encoding="utf-8")
    git(committed_git_repo, "add", "removed.txt")
    git(committed_git_repo, "commit", "-m", "add removable")
    (committed_git_repo / "removed.txt").unlink()
    (committed_git_repo / "untracked file.txt").write_text("new\n", encoding="utf-8")

    state = GitInspector().inspect(committed_git_repo)
    assert "tracked.txt" in state.changes.modified
    assert "added ação.txt" not in state.changes.added  # included in the second commit
    assert "removed.txt" in state.changes.removed
    assert "untracked file.txt" in state.changes.untracked
    assert not state.clean


def test_staged_added(committed_git_repo: Path) -> None:
    (committed_git_repo / "added space ação.txt").write_text("new\n", encoding="utf-8")
    git(committed_git_repo, "add", "added space ação.txt")
    assert "added space ação.txt" in GitInspector().inspect(
        committed_git_repo
    ).changes.added


def test_conflict_is_recognized(committed_git_repo: Path) -> None:
    git(committed_git_repo, "checkout", "-b", "other")
    (committed_git_repo / "tracked.txt").write_text("other\n", encoding="utf-8")
    git(committed_git_repo, "commit", "-am", "other")
    git(committed_git_repo, "checkout", "main")
    (committed_git_repo / "tracked.txt").write_text("main\n", encoding="utf-8")
    git(committed_git_repo, "commit", "-am", "main")
    git(committed_git_repo, "merge", "other", check=False)
    assert "tracked.txt" in GitInspector().inspect(
        committed_git_repo
    ).changes.conflicts


def test_inspection_does_not_change_status(committed_git_repo: Path) -> None:
    (committed_git_repo / "untracked.txt").write_text("x\n", encoding="utf-8")
    before = git(committed_git_repo, "status", "--porcelain=v1", "-z").stdout
    GitInspector().inspect(committed_git_repo)
    after = git(committed_git_repo, "status", "--porcelain=v1", "-z").stdout
    assert after == before

