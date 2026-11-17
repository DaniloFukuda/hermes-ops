from pathlib import Path
import sys

import pytest

from hermes_ops.core.processes import run_process


def run_python(tmp_path: Path, code: str, *args: str):
    return run_process(
        (sys.executable, "-c", code, *args),
        cwd=tmp_path,
        timeout=5,
    )


def test_success_and_explicit_cwd(tmp_path: Path) -> None:
    result = run_python(tmp_path, "import os; print(os.getcwd())")
    assert result.succeeded
    assert Path(result.stdout.strip()) == tmp_path
    assert result.cwd == str(tmp_path.resolve())


def test_nonzero_and_separate_streams(tmp_path: Path) -> None:
    result = run_python(
        tmp_path,
        "import sys; print('out'); print('err', file=sys.stderr); raise SystemExit(7)",
    )
    assert result.returncode == 7
    assert result.stdout.strip() == "out"
    assert result.stderr.strip() == "err"


def test_missing_executable(tmp_path: Path) -> None:
    result = run_process(
        ("executable-that-does-not-exist-hermes-ops",),
        cwd=tmp_path,
        timeout=1,
    )
    assert not result.started
    assert result.error


def test_timeout(tmp_path: Path) -> None:
    result = run_process(
        (sys.executable, "-c", "import time; time.sleep(2)"),
        cwd=tmp_path,
        timeout=0.05,
    )
    assert result.started
    assert result.timed_out


def test_unicode_and_argument_with_spaces(tmp_path: Path) -> None:
    result = run_python(tmp_path, "import sys; print(sys.argv[1])", "olá mundo")
    assert result.stdout.strip() == "olá mundo"


def test_shell_is_explicitly_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured = {}

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""
        return Completed()

    monkeypatch.setattr("hermes_ops.core.processes.subprocess.run", fake_run)
    run_process(("tool",), cwd=tmp_path, timeout=1)
    assert captured["shell"] is False


def test_string_command_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_process("echo unsafe", cwd=tmp_path, timeout=1)  # type: ignore[arg-type]


def test_missing_cwd_returns_controlled_result(tmp_path: Path) -> None:
    result = run_process(
        (sys.executable, "--version"),
        cwd=tmp_path / "missing",
        timeout=1,
    )
    assert not result.started
    assert result.error_code == "cwd_not_found"
    assert result.error == "Working directory does not exist"


def test_file_cwd_returns_controlled_result(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("", encoding="utf-8")
    result = run_process(
        (sys.executable, "--version"),
        cwd=file_path,
        timeout=1,
    )
    assert not result.started
    assert result.error_code == "cwd_not_directory"


def test_empty_stdin_bytes_are_forwarded_as_eof(tmp_path: Path) -> None:
    result = run_process(
        (sys.executable, "-c", "import sys; print(len(sys.stdin.buffer.read()))"),
        cwd=tmp_path,
        timeout=5,
        input_bytes=b"",
    )
    assert result.succeeded
    assert result.stdout.strip() == "0"


def test_stdin_bytes_with_unicode_content_are_forwarded(tmp_path: Path) -> None:
    result = run_process(
        (
            sys.executable,
            "-c",
            "import sys; print(sys.stdin.buffer.read().decode('utf-8'))",
        ),
        cwd=tmp_path,
        timeout=5,
        input_bytes="entrada olá".encode("utf-8"),
    )
    assert result.succeeded
    assert result.stdout.strip() == "entrada olá"


def test_explicit_environment_is_forwarded_without_mutating_input(tmp_path: Path) -> None:
    environment = {"HERMES_PROCESS_TEST_VALUE": "provided"}
    result = run_process(
        (
            sys.executable,
            "-c",
            "import os; print(os.environ['HERMES_PROCESS_TEST_VALUE'])",
        ),
        cwd=tmp_path,
        timeout=5,
        env=environment,
    )
    assert result.succeeded
    assert result.stdout.strip() == "provided"
    assert environment == {"HERMES_PROCESS_TEST_VALUE": "provided"}


def test_invalid_input_bytes_and_environment_types_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="input_bytes"):
        run_process(
            (sys.executable, "--version"),
            cwd=tmp_path,
            timeout=1,
            input_bytes="not bytes",  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="env"):
        run_process(
            (sys.executable, "--version"),
            cwd=tmp_path,
            timeout=1,
            env={"HERMES_PROCESS_TEST_VALUE": 1},  # type: ignore[dict-item]
        )


def test_input_and_environment_values_are_not_exposed_in_start_error(tmp_path: Path) -> None:
    result = run_process(
        ("missing-hermes-executable",),
        cwd=tmp_path,
        timeout=1,
        input_bytes=b"secret-input",
        env={"HERMES_SECRET": "secret-value"},
    )
    assert not result.started
    assert "secret-input" not in (result.error or "")
    assert "secret-value" not in (result.error or "")


def test_stdout_below_and_at_limit_are_complete(tmp_path: Path) -> None:
    code = "import sys; sys.stdout.buffer.write(b'abc')"
    for limit in (3, 4):
        result = run_process(
            (sys.executable, "-c", code),
            cwd=tmp_path,
            timeout=5,
            max_stdout_bytes=limit,
        )
        assert result.succeeded
        assert result.stdout == "abc"
        assert result.stdout_limit_exceeded is False


def test_stdout_above_limit_fails_closed_without_partial_output(tmp_path: Path) -> None:
    result = run_process(
        (sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'secret-output')"),
        cwd=tmp_path,
        timeout=5,
        max_stdout_bytes=6,
    )
    assert result.started
    assert result.succeeded is False
    assert result.error_code == "output_limit_exceeded"
    assert result.stdout_limit_exceeded is True
    assert result.stderr_limit_exceeded is False
    assert result.stdout == ""
    assert "secret-output" not in (result.error or "")


def test_stderr_above_limit_is_identified_independently(tmp_path: Path) -> None:
    result = run_process(
        (
            sys.executable,
            "-c",
            "import sys; sys.stderr.buffer.write(b'diagnostic-output')",
        ),
        cwd=tmp_path,
        timeout=5,
        max_stderr_bytes=5,
    )
    assert result.error_code == "output_limit_exceeded"
    assert result.stdout_limit_exceeded is False
    assert result.stderr_limit_exceeded is True
    assert result.stdout == ""
    assert result.stderr == ""


def test_both_output_limits_are_identified(tmp_path: Path) -> None:
    result = run_process(
        (
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(b'out'); sys.stderr.buffer.write(b'err')",
        ),
        cwd=tmp_path,
        timeout=5,
        max_stdout_bytes=2,
        max_stderr_bytes=2,
    )
    assert result.error_code == "output_limit_exceeded"
    assert result.stdout_limit_exceeded is True
    assert result.stderr_limit_exceeded is True


def test_multibyte_output_limit_is_measured_in_bytes(tmp_path: Path) -> None:
    result = run_process(
        (
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write('á'.encode('utf-8'))",
        ),
        cwd=tmp_path,
        timeout=5,
        max_stdout_bytes=1,
    )
    assert result.error_code == "output_limit_exceeded"
    assert result.stdout_limit_exceeded is True


def test_output_limit_validation_rejects_non_positive_and_bool(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_stdout_bytes"):
        run_process((sys.executable, "--version"), cwd=tmp_path, timeout=1, max_stdout_bytes=0)
    with pytest.raises(TypeError, match="max_stderr_bytes"):
        run_process((sys.executable, "--version"), cwd=tmp_path, timeout=1, max_stderr_bytes=True)  # type: ignore[arg-type]
