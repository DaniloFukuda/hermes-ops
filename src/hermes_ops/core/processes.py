from __future__ import annotations

from dataclasses import dataclass
import locale
from pathlib import Path
import subprocess
from typing import Mapping, Sequence

from hermes_ops.core.errors import (
    CheckpointRequired,
    ExecutionBudgetExceeded,
    ExecutionBudgetReserved,
)
from hermes_ops.execution import (
    BudgetDecision,
    ExecutionCategory,
    ExecutionContext,
)


@dataclass(frozen=True, slots=True)
class ProcessResult:
    cwd: str
    returncode: int | None
    stdout: str
    stderr: str
    started: bool
    timed_out: bool
    error: str | None = None
    error_code: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.started and not self.timed_out and self.returncode == 0


@dataclass(frozen=True, slots=True)
class BudgetedProcessResult:
    process_result: ProcessResult
    execution_context: ExecutionContext


def run_process_with_context(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: float,
    execution_context: ExecutionContext,
    category: ExecutionCategory,
    units: int = 1,
    env: Mapping[str, str] | None = None,
) -> BudgetedProcessResult:
    if type(execution_context) is not ExecutionContext:
        raise TypeError("execution_context must be an ExecutionContext")
    decision = execution_context.can_start(category, units)
    if decision is BudgetDecision.CHECKPOINT_REQUIRED:
        raise CheckpointRequired(
            "Exploration is stopped at the checkpoint threshold"
        )
    if decision is BudgetDecision.RESERVED:
        raise ExecutionBudgetReserved(
            "Action would consume units reserved for a later category"
        )
    if decision is BudgetDecision.EXHAUSTED:
        raise ExecutionBudgetExceeded(
            "Action would exceed the absolute execution budget"
        )
    next_context = execution_context.consume(category, units)
    process_result = run_process(args, cwd=cwd, timeout=timeout, env=env)
    return BudgetedProcessResult(process_result, next_context)


def run_process(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: float,
    env: Mapping[str, str] | None = None,
) -> ProcessResult:
    if isinstance(args, (str, bytes)) or not args:
        raise ValueError("args must be a non-empty sequence of strings")
    normalized = tuple(str(arg) for arg in args)
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    requested_cwd = str(cwd)
    try:
        explicit_cwd = Path(cwd).expanduser().resolve(strict=True)
    except FileNotFoundError:
        return ProcessResult(
            requested_cwd,
            None,
            "",
            "",
            False,
            False,
            "Working directory does not exist",
            "cwd_not_found",
        )
    except PermissionError:
        return ProcessResult(
            requested_cwd,
            None,
            "",
            "",
            False,
            False,
            "Working directory is not accessible",
            "cwd_permission_denied",
        )
    except (OSError, RuntimeError):
        return ProcessResult(
            requested_cwd,
            None,
            "",
            "",
            False,
            False,
            "Working directory could not be resolved",
            "cwd_invalid",
        )
    if not explicit_cwd.is_dir():
        return ProcessResult(
            str(explicit_cwd),
            None,
            "",
            "",
            False,
            False,
            "Working directory is not a directory",
            "cwd_not_directory",
        )

    try:
        completed = subprocess.run(
            normalized,
            cwd=explicit_cwd,
            timeout=timeout,
            env=None if env is None else dict(env),
            shell=False,
            capture_output=True,
            text=False,
            check=False,
        )
    except FileNotFoundError as exc:
        return ProcessResult(
            str(explicit_cwd),
            None,
            "",
            "",
            False,
            False,
            f"Executable not found: {normalized[0]}",
            "executable_not_found",
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _timeout_text(exc.stdout)
        stderr = _timeout_text(exc.stderr)
        return ProcessResult(
            str(explicit_cwd),
            None,
            stdout,
            stderr,
            True,
            True,
            f"Process exceeded timeout of {timeout} seconds",
            "timeout",
        )
    except PermissionError:
        return ProcessResult(
            str(explicit_cwd),
            None,
            "",
            "",
            False,
            False,
            "Process could not start because access was denied",
            "process_permission_denied",
        )
    except OSError:
        return ProcessResult(
            str(explicit_cwd),
            None,
            "",
            "",
            False,
            False,
            "Process could not be started",
            "process_start_failed",
        )

    return ProcessResult(
        str(explicit_cwd),
        completed.returncode,
        _decode_output(completed.stdout),
        _decode_output(completed.stderr),
        True,
        False,
    )


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return _decode_output(value)
    return value


def _decode_output(value: str | bytes) -> str:
    if isinstance(value, str):
        return value
    try:
        return value.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return value.decode(locale.getpreferredencoding(False), errors="replace")
