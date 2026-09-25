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
