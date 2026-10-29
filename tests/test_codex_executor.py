"""Contract tests for the Codex executor boundary.

These tests never execute codex.cmd. They validate request gating and the
normalized process-result mapping used before a future provider enablement.
"""

from dataclasses import replace
import inspect
from pathlib import Path

import pytest

from hermes_ops.core.processes import BudgetedProcessResult, ProcessResult
from hermes_ops.execution import ExecutionBudget, ExecutionContext
from hermes_ops.executors import CodexExecutionRequest, CodexExecutionResult, CodexExecutor
import hermes_ops.executors.codex as codex_module


def _context() -> ExecutionContext:
    return ExecutionContext(
        ExecutionBudget(
            max_units=10,
            used_units=0,
            validation_reserve=2,
            closure_reserve=2,
            warning_threshold=3,
            checkpoint_threshold=5,
        )
    )


def _request(tmp_path: Path, **changes: object) -> CodexExecutionRequest:
    request = CodexExecutionRequest(
        prompt="Inspect only the supplied analysis request",
        project_path=Path("legacy-target-placeholder"),
        timeout_seconds=42,
        execution_context=_context(),
        working_directory=tmp_path,
        executable_path=tmp_path / "codex.cmd",
        env={"CODEX_TEST_MODE": "1"},
    )
    return replace(request, **changes)


def test_request_requires_explicit_execution_context(tmp_path: Path) -> None:
    request = _request(tmp_path, execution_context=None)

    result = CodexExecutor().execute(request)

    assert result.success is False
    assert result.error_code == "CODEX_BUDGET_CONTEXT_REQUIRED"


def test_project_path_is_not_used_as_implicit_cwd(tmp_path: Path) -> None:
    request = _request(tmp_path, working_directory=None)

    result = CodexExecutor().execute(request)

    assert result.success is False
    assert result.error_code == "CODEX_CWD_INVALID"


def test_executable_requires_explicit_absolute_codex_path(tmp_path: Path) -> None:
    request = _request(tmp_path, executable_path=Path("codex.cmd"))

    result = CodexExecutor().execute(request)

    assert result.success is False
    assert result.error_code == "CODEX_EXECUTABLE_UNAUTHORIZED"


def test_environment_requires_string_allowlisted_values(tmp_path: Path) -> None:
    request = _request(tmp_path, env={"CODEX_TEST_MODE": 1})  # type: ignore[dict-item]

    result = CodexExecutor().execute(request)

    assert result.success is False
    assert result.error_code == "CODEX_ENV_INVALID"


def test_non_read_only_sandbox_is_rejected_at_request_boundary(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="sandbox_mode must be 'read-only'"):
        _request(tmp_path, sandbox_mode="workspace-write")


def test_process_boundary_receives_limits_without_real_codex(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_process(*args: object, **kwargs: object) -> BudgetedProcessResult:
        captured.update(kwargs)
        return BudgetedProcessResult(
            ProcessResult("neutral", 0, "{}", "", True, False),
            _context(),
        )

    monkeypatch.setattr(codex_module, "run_process_with_context", fake_process)

    result = CodexExecutor().execute(_request(tmp_path))

    assert result.success is True
    assert captured["input_bytes"] == b"Inspect only the supplied analysis request"
    assert captured["env"] == {"CODEX_TEST_MODE": "1"}
    assert captured["max_stdout_bytes"] == _request(tmp_path).max_stdout_bytes
    assert captured["max_stderr_bytes"] == _request(tmp_path).max_stderr_bytes
    assert captured["cwd"] == tmp_path.resolve()


def test_output_limit_exceeded_is_a_controlled_codex_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def limited_process(*args: object, **kwargs: object) -> BudgetedProcessResult:
        return BudgetedProcessResult(
            ProcessResult(
                "neutral",
                0,
                "",
                "",
                True,
                False,
                "Process output exceeded configured byte limit",
                "output_limit_exceeded",
                True,
                False,
            ),
            _context(),
        )

    monkeypatch.setattr(codex_module, "run_process_with_context", limited_process)

    result = CodexExecutor().execute(_request(tmp_path))

    assert result.success is False
    assert result.error_code == "CODEX_OUTPUT_LIMIT_EXCEEDED"
    assert result.stdout == ""
    assert result.stderr == ""
    assert "output" in (result.error or "")


def test_process_boundary_path_is_explicit_and_prompt_uses_stdin() -> None:
    source = inspect.getsource(codex_module)

    assert "subprocess.run" not in source
    assert "run_process_with_context" in source
    assert "input_bytes" in source
    assert "--sandbox" in source
    assert "request.sandbox_mode" in source
    assert "shell=False" not in source


def test_nonzero_process_result_is_normalized() -> None:
    result = codex_module._result_from_process_result(
        ProcessResult("neutral", 7, "partial", "diagnostic", True, False),
        duration_seconds=1.25,
    )

    assert result == CodexExecutionResult(
        exit_code=7,
        stdout="partial",
        stderr="diagnostic",
        duration_seconds=1.25,
        success=False,
        error_code="CODEX_PROCESS_NONZERO_EXIT",
        error="Codex process returned a non-zero exit code",
    )


def test_timeout_process_result_is_normalized() -> None:
    result = codex_module._result_from_process_result(
        ProcessResult(
            "neutral",
            None,
            "partial",
            "diagnostic",
            True,
            True,
            "Process exceeded timeout",
            "timeout",
        ),
        duration_seconds=2.0,
    )

    assert result.success is False
    assert result.error_code == "CODEX_TIMEOUT"
    assert result.stdout == "partial"
    assert result.stderr == "diagnostic"
    assert result.duration_seconds == 2.0


def test_stdout_and_stderr_are_taken_from_normalized_process_result() -> None:
    result = codex_module._result_from_process_result(
        ProcessResult("neutral", 0, "stdout", "stderr", True, False),
        duration_seconds=0.5,
    )

    assert result.success is True
    assert result.stdout == "stdout"
    assert result.stderr == "stderr"
    assert result.error_code is None


def test_executor_never_executes_real_codex(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_process(*args: object, **kwargs: object) -> BudgetedProcessResult:
        return BudgetedProcessResult(
            ProcessResult("neutral", 0, "{}", "", True, False),
            _context(),
        )

    monkeypatch.setattr(codex_module, "run_process_with_context", fake_process)
    result = CodexExecutor().execute(_request(tmp_path))

    assert result.success is True
