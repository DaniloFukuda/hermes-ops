"""Generic, independent Codex CLI executor."""

from collections.abc import Mapping
from pathlib import Path
import time

from hermes_ops.core.errors import ExecutionBudgetError
from hermes_ops.core.processes import ProcessResult, run_process_with_context
from hermes_ops.execution import ExecutionCategory
from hermes_ops.executors.models import CodexExecutionRequest, CodexExecutionResult


_ALLOWED_EXECUTABLE_NAMES = frozenset({"codex", "codex.cmd", "codex.exe"})


class CodexExecutor:
    """Invoke Codex only through the central process boundary."""

    def execute(self, request: CodexExecutionRequest) -> CodexExecutionResult:
        started_at = time.perf_counter()
        validation = _validate_request(request)
        if validation[0] is not None:
            return _failure(validation[0], validation[1], started_at)

        working_directory, executable_path, environment = validation[2:]
        return _execute_via_process_boundary(
            request,
            working_directory,
            executable_path,
            environment,
            started_at,
        )


def _validate_request(
    request: CodexExecutionRequest,
) -> tuple[str | None, str | None, Path | None, Path | None, dict[str, str] | None]:
    if request.execution_context is None:
        return (
            "CODEX_BUDGET_CONTEXT_REQUIRED",
            "Codex execution requires an explicit execution context",
            None,
            None,
            None,
        )

    if request.working_directory is None:
        return (
            "CODEX_CWD_INVALID",
            "Codex execution requires a neutral working directory",
            None,
            None,
            None,
        )
    try:
        working_directory = Path(request.working_directory).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return (
            "CODEX_CWD_INVALID",
            "Codex working directory could not be resolved",
            None,
            None,
            None,
        )
    if not working_directory.is_dir():
        return (
            "CODEX_CWD_INVALID",
            "Codex working directory is not a directory",
            None,
            None,
            None,
        )

    if request.executable_path is None:
        return (
            "CODEX_EXECUTABLE_UNAUTHORIZED",
            "Codex executable must be explicitly configured",
            None,
            None,
            None,
        )
    executable_path = Path(request.executable_path).expanduser()
    if (
        not executable_path.is_absolute()
        or executable_path.name.casefold() not in _ALLOWED_EXECUTABLE_NAMES
    ):
        return (
            "CODEX_EXECUTABLE_UNAUTHORIZED",
            "Codex executable is not an authorized absolute path",
            None,
            None,
            None,
        )

    if not isinstance(request.env, Mapping):
        return (
            "CODEX_ENV_INVALID",
            "Codex environment must be an explicit mapping",
            None,
            None,
            None,
        )
    environment: dict[str, str] = {}
    for key, value in request.env.items():
        if not isinstance(key, str) or not isinstance(value, str):
            return (
                "CODEX_ENV_INVALID",
                "Codex environment keys and values must be strings",
                None,
                None,
                None,
            )
        environment[key] = value

    return None, None, working_directory, executable_path, environment


def _execute_via_process_boundary(
    request: CodexExecutionRequest,
    working_directory: Path,
    executable_path: Path,
    environment: dict[str, str],
    started_at: float,
) -> CodexExecutionResult:
    args = (
        str(executable_path),
        "exec",
        "--sandbox",
        request.sandbox_mode,
        "-",
    )
    try:
        budgeted = run_process_with_context(
            args,
            cwd=working_directory,
            timeout=float(request.timeout_seconds),
            execution_context=request.execution_context,
            category=ExecutionCategory.VALIDATION,
            input_bytes=request.prompt.encode("utf-8"),
            env=environment,
            max_stdout_bytes=request.max_stdout_bytes,
            max_stderr_bytes=request.max_stderr_bytes,
        )
    except ExecutionBudgetError as exc:
        return _failure(getattr(exc, "code", "CODEX_BUDGET_BLOCKED"), str(exc), started_at)

    return _result_from_process_result(
        budgeted.process_result,
        duration_seconds=time.perf_counter() - started_at,
    )


def _result_from_process_result(
    result: ProcessResult,
    *,
    duration_seconds: float,
) -> CodexExecutionResult:
    if result.stdout_limit_exceeded or result.stderr_limit_exceeded:
        error_code = "CODEX_OUTPUT_LIMIT_EXCEEDED"
    elif result.timed_out or result.error_code == "timeout":
        error_code = "CODEX_TIMEOUT"
    elif not result.started:
        error_code = "CODEX_PROCESS_START_FAILED"
    elif result.returncode != 0:
        error_code = "CODEX_PROCESS_NONZERO_EXIT"
    else:
        error_code = result.error_code

    error = result.error
    if error_code == "CODEX_OUTPUT_LIMIT_EXCEEDED":
        error = "Codex process output exceeded configured limits"
    elif error_code == "CODEX_PROCESS_NONZERO_EXIT":
        error = "Codex process returned a non-zero exit code"

    return CodexExecutionResult(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_seconds=duration_seconds,
        success=result.succeeded,
        error_code=error_code,
        error=error,
    )


def _failure(
    error_code: str,
    error: str,
    started_at: float,
) -> CodexExecutionResult:
    return CodexExecutionResult(
        exit_code=None,
        stdout="",
        stderr="",
        duration_seconds=time.perf_counter() - started_at,
        success=False,
        error_code=error_code,
        error=error,
    )
