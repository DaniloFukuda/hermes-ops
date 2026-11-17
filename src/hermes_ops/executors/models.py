"""Data models for generic Codex CLI execution."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from hermes_ops.execution import ExecutionContext


DEFAULT_CODEX_MAX_STDOUT_BYTES = 1_048_576
DEFAULT_CODEX_MAX_STDERR_BYTES = 262_144


@dataclass(frozen=True)
class CodexExecutionRequest:
    """Inputs needed to execute a prompt with Codex CLI."""

    prompt: str
    project_path: Path
    timeout_seconds: int = 300
    sandbox_mode: str = "read-only"
    execution_context: ExecutionContext | None = None
    working_directory: Path | None = None
    executable_path: Path | None = None
    env: Mapping[str, str] = field(default_factory=dict)
    max_stdout_bytes: int = DEFAULT_CODEX_MAX_STDOUT_BYTES
    max_stderr_bytes: int = DEFAULT_CODEX_MAX_STDERR_BYTES

    def __post_init__(self) -> None:
        if self.sandbox_mode != "read-only":
            raise ValueError("sandbox_mode must be 'read-only'")
        if type(self.timeout_seconds) is not int or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        for name, value in (
            ("max_stdout_bytes", self.max_stdout_bytes),
            ("max_stderr_bytes", self.max_stderr_bytes),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class CodexExecutionResult:
    """Captured outcome of a generic Codex CLI execution attempt."""

    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    success: bool
    error_code: str | None = None
    error: str | None = None
