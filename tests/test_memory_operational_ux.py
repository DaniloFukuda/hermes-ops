"""Contract tests for HERMES-0032 operational UX and observability."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes_ops.cli import build_parser, main
from hermes_ops.memory.models import DisclosureLevel
from hermes_ops.memory.store import MemoryService


SOURCE = "def dangerous(payload):\n    return eval(payload)\n"


def _args(target: Path, store: Path, mode: str, *extra: str) -> list[str]:
    return [
        "skill", "run", "memory-assisted-audit", "--project", str(target),
        "--mission", "dynamic audit", "--repository-id", "ux-repo",
        "--memory-store", str(store), "--memory", mode,
        "--include-path", "source.py", "--format", "json", *extra,
    ]


def _seed(tmp_path: Path, capsys) -> tuple[Path, Path]:
    target = tmp_path / "target"
    target.mkdir()
    (target / "source.py").write_text(SOURCE, encoding="utf-8")
    store = tmp_path / "memory.sqlite3"
    assert main(_args(target, store, "read-write")) == 0
    capsys.readouterr()
    return target, store


def test_json_candidate_exposes_real_reason_codes(tmp_path: Path, capsys) -> None:
    """Spec: HERMES-0032 / AC-01 (first RED)."""
    target, store = _seed(tmp_path, capsys)
    assert main(_args(target, store, "read")) == 0
    payload = json.loads(capsys.readouterr().out)
    candidate = payload["memory_context"]["candidates"][0]
    assert candidate["reason_codes"] == ["PATH_MATCH", "AUDITOR_MATCH", "LINEAGE_MATCH"]


def test_cli_accepts_structured_disclosure(tmp_path: Path, capsys) -> None:
    """Spec: HERMES-0032 / AC-02 (second RED)."""
    target, store = _seed(tmp_path, capsys)
    assert main(_args(target, store, "read", "--memory-disclosure", "structured")) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["memory_context"]["effective_disclosure"] == "STRUCTURED"


@pytest.mark.parametrize(
    ("cli_value", "enum_value"),
    [
        ("header", "HEADER"),
        ("structured", "STRUCTURED"),
        ("canonical", "CANONICAL"),
        ("revalidation-hint", "REVALIDATION_HINT"),
    ],
)
def test_all_disclosures_are_exact_and_privacy_safe(
    tmp_path: Path, capsys, cli_value: str, enum_value: str,
) -> None:
    """Spec: HERMES-0032 / AC-02, AC-08 through AC-10."""
    target, store = _seed(tmp_path, capsys)
    assert main(_args(target, store, "read", "--memory-disclosure", cli_value)) == 0
    raw = capsys.readouterr().out
    payload = json.loads(raw)
    assert payload["memory_context"]["effective_disclosure"] == enum_value
    assert payload["memory_context"]["candidates"][0]["reason_codes"]
    historical = json.dumps(payload["memory_context"], sort_keys=True)
    assert "return eval(payload)" not in historical
    assert "eval(payload)" not in historical
    if cli_value == "revalidation-hint":
        assert payload["memory_context"]["revalidation_hints"][0]["requires_fresh_audit"] is True


def test_default_help_invalid_and_unrelated_skill_compatibility(
    tmp_path: Path, capsys,
) -> None:
    """Spec: HERMES-0032 / AC-02, AC-03, AC-11."""
    parser = build_parser()
    parsed = parser.parse_args(["skill", "run", "memory-assisted-audit", "--project", "."])
    assert parsed.memory_disclosure == "header" and parsed.memory == "off"
    help_text = parser._subparsers._group_actions[0].choices["skill"]._subparsers._group_actions[0].choices["run"].format_help()
    normalized_help = " ".join(help_text.split())
    assert "--memory-disclosure" in help_text
    assert "always runs a fresh audit" in normalized_help
    assert "mission-audit or memory-assisted- audit" in normalized_help
    with pytest.raises(SystemExit):
        parser.parse_args([
            "skill", "run", "memory-assisted-audit", "--project", ".",
            "--memory-disclosure", "unsafe",
        ])
    target = tmp_path / "target"
    target.mkdir()
    assert main([
        "skill", "run", "code-audit", "--project", str(target),
        "--memory-disclosure", "canonical",
    ]) == 2
    assert "SKILL_EXECUTION_INVALID" in capsys.readouterr().err


def test_metrics_and_json_are_stable_while_text_has_local_timings(
    tmp_path: Path, capsys,
) -> None:
    """Spec: HERMES-0032 / AC-04 through AC-06."""
    target, store = _seed(tmp_path, capsys)
    assert main(_args(target, store, "read")) == 0
    first_raw = capsys.readouterr().out
    assert main(_args(target, store, "read")) == 0
    second_raw = capsys.readouterr().out
    assert first_raw == second_raw
    metrics = json.loads(first_raw)["memory_context"]["operational_metrics"]
    assert metrics == {
        "candidates_returned": 1,
        "disclosure_level": "HEADER",
        "hints_returned": 1,
        "memory_diagnostics_count": 0,
        "observations_written": 0,
        "retrieval_requested": True,
        "writeback_attempted": False,
    }
    text_args = _args(target, store, "read")
    text_args[text_args.index("json")] = "text"
    assert main(text_args) == 0
    text = capsys.readouterr().out
    assert "timing_ms=retrieval:" in text
    assert "score=" in text and "reasons=PATH_MATCH,AUDITOR_MATCH,LINEAGE_MATCH" in text


def test_disclosure_does_not_change_fresh_result_or_persisted_observation(
    tmp_path: Path, capsys,
) -> None:
    """Spec: HERMES-0032 / AC-08, AC-09."""
    target = tmp_path / "target"
    target.mkdir()
    (target / "source.py").write_text(SOURCE, encoding="utf-8")
    fresh_values = []
    canonical_values = []
    for disclosure in ("header", "structured", "canonical", "revalidation-hint"):
        store = tmp_path / f"{disclosure}.sqlite3"
        assert main(_args(
            target, store, "read-write", "--memory-disclosure", disclosure,
        )) == 0
        payload = json.loads(capsys.readouterr().out)
        fresh_values.append(payload["fresh_audit"])
        observation_id = payload["memory_writeback"]["written_observations"][0]
        with MemoryService.open(store, read_only=True) as service:
            assert service.store is not None
            observation = service.store.expand(observation_id, "ux-repo", DisclosureLevel.CANONICAL)
            canonical_values.append(observation.canonical_json())
    assert all(value == fresh_values[0] for value in fresh_values)
    assert all(value == canonical_values[0] for value in canonical_values)
