from pathlib import Path
import json
import pytest

from hermes_ops.core.results import CheckResult, Report, Status


def test_result_json_is_stable_and_json_safe() -> None:
    report = Report.from_results(
        "doctor",
        [
            CheckResult(
                "sample",
                Status.OK,
                "Tudo certo",
                {"path": Path("a/b"), "raw": b"ol\xc3\xa1"},
                "ok",
            )
        ],
    )
    first = report.to_json()
    assert first == report.to_json()
    payload = json.loads(first)
    assert payload["results"][0]["details"] == {"path": str(Path("a/b")), "raw": "olá"}


def test_exit_code_precedence() -> None:
    results = [
        CheckResult("error", Status.ERROR, "error"),
        CheckResult("blocked", Status.BLOCKED, "blocked"),
        CheckResult("config", Status.BLOCKED, "config", code="config_schema"),
    ]
    assert Report.from_results("x", results).exit_code == 2


def test_warning_does_not_fail() -> None:
    report = Report.from_results(
        "x", [CheckResult("warning", Status.WARNING, "warning")]
    )
    assert report.exit_code == 0


def test_sets_are_normalized_deterministically() -> None:
    first = CheckResult(
        "set", Status.OK, "ok", {"values": {"z", "a", "m"}}
    ).to_dict()
    second = CheckResult(
        "set", Status.OK, "ok", {"values": {"m", "z", "a"}}
    ).to_dict()
    assert first == second
    assert first["details"]["values"] == ["a", "m", "z"]


def test_nested_details_are_recursively_normalized() -> None:
    result = CheckResult(
        "nested",
        Status.WARNING,
        "ok",
        {
            "path": Path("folder/file"),
            "nested": [{"raw": b"ol\xc3\xa1", "status": Status.BLOCKED}],
        },
    ).to_dict()
    assert result["details"] == {
        "nested": [{"raw": "olá", "status": "BLOQUEADO"}],
        "path": str(Path("folder/file")),
    }


def test_invalid_status_is_rejected() -> None:
    with pytest.raises(TypeError, match="Status"):
        CheckResult("invalid", "OK", "message")  # type: ignore[arg-type]


def test_repeated_complex_json_is_identical() -> None:
    report = Report.from_results(
        "doctor",
        [
            CheckResult(
                "stable",
                Status.OK,
                "ok",
                {"set": {3, 1, 2}, "mapping": {"z": 1, "a": 2}},
            )
        ],
    )
    assert len({report.to_json() for _ in range(20)}) == 1

