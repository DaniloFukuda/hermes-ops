from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from hermes_ops.core.processes import ProcessResult, run_process
from hermes_ops.git.environment import safe_git_environment
from hermes_ops.git.parser import WorktreeChanges, parse_porcelain_v1_z


Runner = Callable[..., ProcessResult]


@dataclass(frozen=True, slots=True)
class GitState:
    available: bool
    is_repository: bool
    root: str | None = None
    branch: str | None = None
    head: str | None = None
    has_commits: bool = False
    detached: bool = False
    changes: WorktreeChanges = field(default_factory=WorktreeChanges)
    error: str | None = None
    error_code: str | None = None

    @property
    def clean(self) -> bool:
        return self.changes.clean


class GitInspector:
    def __init__(
        self,
        *,
        executable: str = "git",
        timeout: float = 10,
        runner: Runner = run_process,
    ) -> None:
        self.executable = executable
        self.timeout = timeout
        self.runner = runner

    def inspect(self, project: Path) -> GitState:
        try:
            declared_root = project.resolve(strict=True)
        except (OSError, RuntimeError):
            return GitState(
                True,
                False,
                error="Declared project root could not be resolved",
                error_code="git_declared_root_invalid",
            )
        if (declared_root / ".git").is_file():
            return GitState(
                True,
                True,
                error=(
                    "Indirect .git files and linked Git worktrees are not "
                    "supported by the current safety contract"
                ),
                error_code="git_indirect_repository_unsupported",
            )
        probe = self._run(project, "rev-parse", "--is-inside-work-tree")
        if not probe.started:
            return GitState(
                False,
                False,
                error=probe.error or "Git is unavailable",
                error_code="git_unavailable",
            )
        if probe.returncode != 0:
            return self._classify_probe_failure(probe)
        if probe.stdout.strip() != "true":
            return GitState(
                True,
                False,
                error=(
                    "Git worktree differs from the declared project root "
                    "or is not an active worktree"
                ),
                error_code="git_root_mismatch",
            )

        root_result = self._run(project, "rev-parse", "--show-toplevel")
        if not root_result.succeeded:
            return GitState(
                True,
                True,
                error=self._safe_git_error(root_result, "Cannot determine Git root"),
                error_code="git_operational_error",
            )
        root_text = root_result.stdout.strip()
        try:
            git_root = Path(root_text).resolve(strict=True)
        except (OSError, RuntimeError):
            return GitState(
                True,
                True,
                error="Git returned an invalid repository root",
                error_code="git_unexpected_output",
            )
        if git_root != declared_root:
            return GitState(
                True,
                True,
                root=str(git_root),
                error="Git repository root differs from the declared project root",
                error_code="git_root_mismatch",
            )
        root = str(git_root)

        head_result = self._run(project, "rev-parse", "--verify", "HEAD")
        has_commits = head_result.succeeded
        head = head_result.stdout.strip() if has_commits else None

        branch_result = self._run(project, "symbolic-ref", "--quiet", "--short", "HEAD")
        branch = branch_result.stdout.strip() if branch_result.succeeded else None
        detached = has_commits and branch is None

        status_result = self._run(
            project,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        )
        if not status_result.succeeded:
            return GitState(
                True,
                True,
                root=root,
                branch=branch,
                head=head,
                has_commits=has_commits,
                detached=detached,
                error=status_result.stderr.strip() or "Cannot inspect working tree",
                error_code="git_operational_error",
            )
        try:
            changes = parse_porcelain_v1_z(status_result.stdout)
        except ValueError as exc:
            return GitState(
                True,
                True,
                root=root,
                branch=branch,
                head=head,
                has_commits=has_commits,
                detached=detached,
                error=str(exc),
                error_code="git_unexpected_output",
            )
        return GitState(
            True,
            True,
            root=root,
            branch=branch,
            head=head,
            has_commits=has_commits,
            detached=detached,
            changes=changes,
        )

    def _run(self, cwd: Path, *args: str) -> ProcessResult:
        return self.runner(
            (self.executable, "-c", "core.fsmonitor=false", *args),
            cwd=cwd,
            timeout=self.timeout,
            env=safe_git_environment(),
        )

    def _classify_probe_failure(self, result: ProcessResult) -> GitState:
        message = self._safe_git_error(result, "Git repository probe failed")
        lowered = message.lower()
        if "not a git repository" in lowered:
            return GitState(True, False)
        if "dubious ownership" in lowered:
            code = "git_dubious_ownership"
        elif "permission denied" in lowered or "access is denied" in lowered:
            code = "git_permission_denied"
        else:
            code = "git_operational_error"
        return GitState(True, False, error=message, error_code=code)

    @staticmethod
    def _safe_git_error(result: ProcessResult, fallback: str) -> str:
        message = result.stderr.strip()
        return message if message else fallback
