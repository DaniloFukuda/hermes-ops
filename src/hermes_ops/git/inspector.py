from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Callable

from hermes_ops.core.processes import ProcessResult, run_process
from hermes_ops.core.paths import (
    direct_project_path,
    is_indirect_path,
)
from hermes_ops.core.errors import PathResolutionError
from hermes_ops.git.environment import safe_git_environment
from hermes_ops.git.parser import WorktreeChanges, parse_porcelain_v1_z


Runner = Callable[..., ProcessResult]

OPTIONAL_GIT_WARNING_CODES = frozenset(
    {
        "git_unavailable",
        "git_repository_missing",
        "git_operational_error",
        "git_permission_denied",
        "git_dubious_ownership",
        "git_unexpected_output",
    }
)


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
        git_entry = declared_root / ".git"
        if is_indirect_path(git_entry) or git_entry.is_file():
            return GitState(
                True,
                True,
                error=(
                    "Indirect .git files and linked Git worktrees are not "
                    "supported by the current safety contract"
                ),
                error_code="git_indirect_repository_unsupported",
            )
        unsafe_config = self._unsafe_local_config(declared_root)
        if unsafe_config is not None:
            return unsafe_config
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
            (
                self.executable,
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.autocrlf=input",
                *args,
            ),
            cwd=cwd,
            timeout=self.timeout,
            env=safe_git_environment(),
        )

    @staticmethod
    def _unsafe_local_config(root: Path) -> GitState | None:
        try:
            config_path = direct_project_path(root, ".git/config")
        except PathResolutionError:
            return GitState(
                True,
                True,
                error="Git configuration uses an indirect filesystem entry",
                error_code="git_unsafe_local_config",
            )
        if not config_path.is_file():
            return None
        try:
            text = config_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return GitState(
                True,
                True,
                error="Git configuration could not be read safely",
                error_code="git_operational_error",
            )
        unsafe = GitInspector._unsafe_config_text(text)
        if unsafe is not None:
            return unsafe
        if not GitInspector._worktree_config_enabled(text):
            return None
        try:
            worktree_config_path = direct_project_path(root, ".git/config.worktree")
        except PathResolutionError:
            return GitState(
                True,
                True,
                error="Git worktree configuration uses an indirect filesystem entry",
                error_code="git_unsafe_local_config",
            )
        if not worktree_config_path.is_file():
            return None
        try:
            worktree_text = worktree_config_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            return GitState(
                True,
                True,
                error="Git worktree configuration could not be read safely",
                error_code="git_operational_error",
            )
        return GitInspector._unsafe_config_text(worktree_text)

    @staticmethod
    def _unsafe_config_text(text: str) -> GitState | None:
        section_pattern = re.compile(
            r"^\s*\[\s*([A-Za-z][A-Za-z0-9.-]*)",
            re.MULTILINE,
        )
        sections = {
            match.group(1).casefold()
            for match in section_pattern.finditer(text)
        }
        if sections.intersection({"include", "includeif"}):
            return GitState(
                True,
                True,
                error="Git configuration includes external configuration",
                error_code="git_unsafe_local_config",
            )
        if "filter" in sections:
            return GitState(
                True,
                True,
                error="Git configuration defines external content filters",
                error_code="git_unsafe_local_config",
            )
        return None

    @staticmethod
    def _worktree_config_enabled(text: str) -> bool:
        section_pattern = re.compile(
            r"^\s*\[\s*([A-Za-z][A-Za-z0-9.-]*)",
        )
        setting_pattern = re.compile(
            r"^\s*worktreeconfig\s*=\s*(true|yes|on|1)\s*(?:[#;].*)?$",
            re.IGNORECASE,
        )
        section: str | None = None
        for line in text.splitlines():
            match = section_pattern.match(line)
            if match is not None:
                section = match.group(1).casefold()
                continue
            if section == "extensions" and setting_pattern.match(line):
                return True
        return False

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
