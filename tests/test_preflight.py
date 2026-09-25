from pathlib import Path

from conftest import git
from hermes_ops.commands.doctor import run_doctor
from hermes_ops.commands.preflight import run_preflight
from hermes_ops.commands.worktree import run_worktree
from hermes_ops.git.inspector import GitState


def _make_git_optional(root: Path) -> None:
    path = root / ".hermes/project.toml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "required = true",
            "required = false",
        ),
        encoding="utf-8",
    )


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


def test_optional_unavailable_git_is_warning_for_all_commands(
    configured_project: Path,
    monkeypatch,
) -> None:
    _make_git_optional(configured_project)
    (configured_project / "pyproject.toml").write_text("", encoding="utf-8")
    unavailable = GitState(
        False,
        False,
        error="Git is unavailable",
        error_code="git_unavailable",
    )
    monkeypatch.setattr(
        "hermes_ops.commands.doctor.GitInspector.inspect",
        lambda self, root: unavailable,
    )
    monkeypatch.setattr(
        "hermes_ops.commands.worktree.GitInspector.inspect",
        lambda self, root: unavailable,
    )

    for command in (run_doctor, run_worktree, run_preflight):
        report = command(configured_project)
        assert report.exit_code == 0
        assert any(
            item.code == "git_unavailable" and item.status.value == "AVISO"
            for item in report.results
        )


def test_optional_git_outside_repository_is_warning(
    configured_project: Path,
) -> None:
    _make_git_optional(configured_project)
    (configured_project / "pyproject.toml").write_text("", encoding="utf-8")

    for command in (run_doctor, run_worktree, run_preflight):
        report = command(configured_project)
        assert report.exit_code == 0
        assert any(
            item.code == "git_repository_missing"
            and item.status.value == "AVISO"
            for item in report.results
        )


def test_optional_git_doctor_error_does_not_leave_preflight_at_exit_one(
    configured_project: Path,
    monkeypatch,
) -> None:
    _make_git_optional(configured_project)
    (configured_project / "pyproject.toml").write_text("", encoding="utf-8")
    unavailable = GitState(
        False,
        False,
        error="Git is unavailable",
        error_code="git_unavailable",
    )
    monkeypatch.setattr(
        "hermes_ops.commands.doctor.GitInspector.inspect",
        lambda self, root: unavailable,
    )
    monkeypatch.setattr(
        "hermes_ops.commands.worktree.GitInspector.inspect",
        lambda self, root: unavailable,
    )

    report = run_preflight(configured_project)

    assert report.exit_code == 0
    assert not any(item.status.value == "ERRO" for item in report.results)


def test_required_unavailable_git_remains_blocking(
    configured_project: Path,
    monkeypatch,
) -> None:
    (configured_project / "pyproject.toml").write_text("", encoding="utf-8")
    unavailable = GitState(
        False,
        False,
        error="Git is unavailable",
        error_code="git_unavailable",
    )
    monkeypatch.setattr(
        "hermes_ops.commands.doctor.GitInspector.inspect",
        lambda self, root: unavailable,
    )
    monkeypatch.setattr(
        "hermes_ops.commands.worktree.GitInspector.inspect",
        lambda self, root: unavailable,
    )

    assert run_doctor(configured_project).exit_code != 0
    assert run_worktree(configured_project).exit_code != 0
    assert run_preflight(configured_project).exit_code == 3


def test_unsafe_git_configuration_remains_blocked_when_git_is_optional(
    empty_git_repo: Path,
) -> None:
    _make_git_optional(empty_git_repo)
    git(empty_git_repo, "config", "include.path", "../external-config")

    for command in (run_doctor, run_worktree, run_preflight):
        report = command(empty_git_repo)
        assert report.exit_code == 3
        assert any(
            item.code == "git_unsafe_local_config"
            for item in report.results
        )
