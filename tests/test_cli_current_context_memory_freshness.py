"""Contract tests for HERMES-0031 current provenance and freshness."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from hermes_ops.cli import main
from hermes_ops.commands.skill import build_cli_current_context, run_memory_assisted_skill_command
from hermes_ops.core.processes import run_process
from hermes_ops.git.inspector import GitState
from hermes_ops.memory.core import create_observation
from hermes_ops.memory.models import (
    DisclosureLevel, FreshnessState, MemoryCurrentContext, MemoryKind,
    MemoryRetrievalRequest, RepositoryIdentity,
)
from hermes_ops.memory.store import MemoryService
from hermes_ops.orchestration.memory_assisted_audit import refine_candidate_freshness


BUGGY = "def dangerous(payload):\n    return eval(payload)\n"
FIXED = "def dangerous(payload):\n    return payload\n"


def _cli(target: Path, store: Path, mode: str) -> list[str]:
    return [
        "skill", "run", "memory-assisted-audit",
        "--project", str(target),
        "--mission", "dynamic execution audit",
        "--repository-id", "hermes-0031-repo",
        "--memory-store", str(store),
        "--memory", mode,
        "--include-path", "source.py",
        "--format", "json",
    ]


def test_cli_read_refines_changed_snapshot_to_stale(
    tmp_path: Path, capsys,
) -> None:
    """Spec: HERMES-0031 / AC-02, AC-14 (first RED)."""
    target = tmp_path / "target"
    target.mkdir()
    source = target / "source.py"
    store = tmp_path / "memory.sqlite3"
    source.write_text(BUGGY, encoding="utf-8")
    assert main(_cli(target, store, "read-write")) == 0
    capsys.readouterr()

    source.write_text(FIXED, encoding="utf-8")
    assert main(_cli(target, store, "read")) == 0
    payload = json.loads(capsys.readouterr().out)

    candidate = payload["memory_context"]["candidates"][0]
    assert candidate["freshness_state"] == "STALE_CANDIDATE"


def test_cli_read_refines_same_snapshot_and_text_displays_it(
    tmp_path: Path, capsys,
) -> None:
    """Spec: HERMES-0031 / AC-01, AC-14."""
    target = tmp_path / "target"
    target.mkdir()
    (target / "source.py").write_text(BUGGY, encoding="utf-8")
    store = tmp_path / "memory.sqlite3"
    assert main(_cli(target, store, "read-write")) == 0
    capsys.readouterr()
    assert main(_cli(target, store, "read")) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["memory_context"]["candidates"][0]["freshness_state"] == "SAME_SNAPSHOT_CANDIDATE"

    text_args = _cli(target, store, "read")
    text_args[text_args.index("--format") + 1] = "text"
    assert main(text_args) == 0
    assert "freshness=SAME_SNAPSHOT_CANDIDATE" in capsys.readouterr().out


def _observation(*, revision: str | None, digest: str | None, scope=("source.py",)):
    return create_observation(
        repository_id="hermes-0031-repo",
        source_revision=revision,
        snapshot_digest=digest,
        structural_scope=scope,
        canonical_request={"auditor": "code-audit"},
        source_auditor="code-audit",
        auditor_version=1,
        normalizer_version=1,
        outcome_status="COMPLETED_WITH_FINDINGS",
        native_classification="CONFIRMED_HISTORICAL_FINDING",
        original_finding_id="CA001:source.py:1:1",
        finding_kind="CA001",
        native_payload={"finding_id": "CA001:source.py:1:1", "finding_kind": "CA001"},
        memory_kind=MemoryKind.CONFIRMED_FINDING,
        relative_paths=("source.py",),
        retrieval_terms=("CA001",),
    )


@pytest.mark.parametrize(
    ("historical_revision", "historical_digest", "current_revision", "current_digest", "expected"),
    [
        ("r1", "d1", "r1", "d1", FreshnessState.SAME_SNAPSHOT_CANDIDATE),
        ("r1", "d1", "r1", "d2", FreshnessState.STALE_CANDIDATE),
        ("r1", None, "r1", None, FreshnessState.CURRENTLY_UNVERIFIED),
        ("r1", None, "r2", None, FreshnessState.STALE_CANDIDATE),
        ("r1", "d1", "r2", "d1", FreshnessState.SAME_SNAPSHOT_CANDIDATE),
        (None, None, None, None, FreshnessState.CURRENTLY_UNVERIFIED),
    ],
)
def test_post_audit_projection_preserves_ranking_and_applies_decision_table(
    tmp_path: Path, historical_revision, historical_digest,
    current_revision, current_digest, expected,
) -> None:
    """Spec: HERMES-0031 / AC-01 through AC-05, AC-07, AC-09."""
    with MemoryService.open(tmp_path / "memory.sqlite3") as service:
        observation = _observation(revision=historical_revision, digest=historical_digest)
        assert service.store is not None and service.store.write(observation)
        candidates = service.retrieve(MemoryRetrievalRequest(
            repository_id="hermes-0031-repo", mission_terms=("CA001",),
        ))
        context = MemoryCurrentContext(
            "hermes-0031-repo", current_revision, current_digest, ("different.py",),
        )
        refined = refine_candidate_freshness(candidates, context, service)
    assert refined[0].freshness_state is expected
    assert replace(refined[0], freshness_state=candidates[0].freshness_state) == candidates[0]


def test_cli_context_uses_optional_local_head_and_scope(monkeypatch) -> None:
    """Spec: HERMES-0031 / AC-15."""
    calls = []

    def inspect(_self, target):
        calls.append(target)
        return GitState(True, True, head="abc123", has_commits=True)

    monkeypatch.setattr("hermes_ops.commands.skill.GitInspector.inspect", inspect)
    context = build_cli_current_context(
        "declared-target", RepositoryIdentity.explicit("logical-repo"), ("source.py",),
    )
    assert context == MemoryCurrentContext("logical-repo", "abc123", None, ("source.py",))
    assert calls == [Path("declared-target")]


def test_no_git_is_optional_and_disabled_mode_skips_git(tmp_path: Path, monkeypatch) -> None:
    """Spec: HERMES-0031 / AC-06, AC-15."""
    target = tmp_path / "target"
    target.mkdir()
    (target / "source.py").write_text(FIXED, encoding="utf-8")
    calls = []

    def inspect(_self, _target):
        calls.append("git")
        return GitState(True, False, error="not a repository", error_code="git_repository_missing")

    monkeypatch.setattr("hermes_ops.commands.skill.GitInspector.inspect", inspect)
    active = build_cli_current_context(str(target), RepositoryIdentity.explicit("repo"), ())
    assert active.current_revision is None and calls == ["git"]
    calls.clear()
    result = run_memory_assisted_skill_command(str(target), "audit", (), "off", None, None)
    assert result.historical_context.pre_audit_current_context is None
    assert calls == []


def test_repository_mismatch_still_fails_closed() -> None:
    """Spec: HERMES-0031 / AC-08."""
    with pytest.raises(Exception) as error:
        MemoryRetrievalRequest(
            repository_id="repo-a",
            current_context=MemoryCurrentContext("repo-b"),
        )
    assert getattr(error.value, "code", None) == "MEMORY_REPOSITORY_MISMATCH"


def _git(target: Path, *args: str) -> str:
    result = run_process(("git", *args), cwd=target, timeout=10)
    assert result.succeeded, result.stderr
    return result.stdout.strip()


def test_dirty_git_worktree_uses_head_only_as_metadata_and_snapshot_as_authority(
    tmp_path: Path, capsys,
) -> None:
    """Spec: HERMES-0031 / AC-05, AC-15, AC-16."""
    target = tmp_path / "target"
    target.mkdir()
    source = target / "source.py"
    source.write_text(BUGGY, encoding="utf-8")
    _git(target, "init")
    _git(target, "add", "source.py")
    _git(
        target, "-c", "user.name=Hermes Test", "-c", "user.email=test@example.invalid",
        "commit", "-m", "fixture",
    )
    head = _git(target, "rev-parse", "HEAD")
    store = tmp_path / "memory.sqlite3"

    assert main(_cli(target, store, "read-write")) == 0
    first = json.loads(capsys.readouterr().out)
    source.write_text(FIXED, encoding="utf-8")
    assert _git(target, "rev-parse", "HEAD") == head
    assert main(_cli(target, store, "read")) == 0
    dirty = json.loads(capsys.readouterr().out)

    assert first["memory_context"]["pre_audit_current_context"]["current_revision"] == head
    assert dirty["memory_context"]["pre_audit_current_context"]["current_revision"] == head
    assert dirty["memory_context"]["candidates"][0]["freshness_state"] == "STALE_CANDIDATE"
    assert (
        first["memory_context"]["post_audit_current_context"]["current_snapshot_digest"]
        != dirty["memory_context"]["post_audit_current_context"]["current_snapshot_digest"]
    )
