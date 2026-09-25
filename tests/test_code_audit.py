from __future__ import annotations

from dataclasses import FrozenInstanceError
import builtins
import json
import os
from pathlib import Path
import socket
import subprocess

import pytest

from conftest import git
from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills import (
    CodeAuditClassification,
    CodeAuditFinding,
    CodeAuditRegion,
    CodeAuditSeverity,
    SkillExecutionStatus,
    SkillPolicy,
    SkillRisk,
    run_skill,
)
from hermes_ops.skills import code_audit
from hermes_ops.skills.code_audit import run_code_audit


def _write(root: Path, relative: str, content: str | bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def _findings(result):
    return result.evidence[1:]


def _details(evidence) -> dict[str, object]:
    return dict(evidence.details)


def _error_code(caught: pytest.ExceptionInfo[SkillExecutionError]) -> str:
    return caught.value.code


def _policy() -> SkillPolicy:
    return SkillPolicy(SkillRisk.LOW, False, frozenset({"git"}))


def test_code_audit_manifest_is_passive_read_only_and_requires_no_runtime_capability() -> None:
    """Spec: HERMES-0008 / AC-01"""
    from hermes_ops.skills import discover_skills

    skill = discover_skills(Path(__file__).resolve().parents[1]).get_by_id("code-audit")
    assert skill is not None
    assert (skill.risk, skill.requires, skill.allows_write) == (SkillRisk.LOW, (), False)


def test_code_audit_is_dispatched_only_by_its_exact_identifier(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-02"""
    assert run_skill(tmp_path, "code-audit", _policy()).skill_id == "code-audit"
    with pytest.raises(Exception) as caught:
        run_skill(tmp_path, "Code-Audit", _policy())
    assert getattr(caught.value, "code", None) == "SKILL_PLAN_REQUEST_INVALID"


def test_scanner_reads_only_explicitly_allowed_code_extensions(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-03"""
    for index, extension in enumerate(sorted(code_audit.ALLOWED_EXTENSIONS)):
        _write(tmp_path, f"source{index}{extension}", "value = 1\n")
    _write(tmp_path, "ignored.txt", "eval(user_input)\n")
    result = run_code_audit(tmp_path)
    assert dict(result.evidence[0].details)["files"] == 8
    assert not _findings(result)


def test_scanner_orders_paths_and_findings_deterministically(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-04"""
    _write(tmp_path, "z.py", "verify=False\n")
    _write(tmp_path, "a.py", "eval(value)\n")
    first = run_code_audit(tmp_path)
    second = run_code_audit(tmp_path)
    assert first == second
    assert [dict(item.details)["file"] for item in _findings(first)] == ["a.py", "z.py"]


def test_scanner_prunes_only_the_documented_excluded_directories(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-05"""
    for name in code_audit.EXCLUDED_DIRECTORIES:
        _write(tmp_path, f"{name}/ignored.py", "eval(value)\n")
    _write(tmp_path, "custom/source.py", "verify=False\n")
    result = run_code_audit(tmp_path)
    assert [dict(item.details)["file"] for item in _findings(result)] == ["custom/source.py"]


def test_file_count_limit_blocks_without_partial_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-06"""
    monkeypatch.setattr(code_audit, "MAX_FILES", 1)
    _write(tmp_path, "a.py", "value=1")
    _write(tmp_path, "b.py", "value=2")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_FILE_LIMIT_EXCEEDED"
    assert not hasattr(caught.value, "evidence")


def test_individual_file_size_limit_blocks_without_partial_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-07"""
    monkeypatch.setattr(code_audit, "MAX_FILE_BYTES", 3)
    _write(tmp_path, "large.py", b"1234")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_FILE_SIZE_EXCEEDED"


def test_total_byte_limit_blocks_without_partial_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-08"""
    monkeypatch.setattr(code_audit, "MAX_TOTAL_BYTES", 3)
    _write(tmp_path, "a.py", b"12")
    _write(tmp_path, "b.py", b"34")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_TOTAL_SIZE_EXCEEDED"


def test_directory_count_and_depth_limits_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-09"""
    monkeypatch.setattr(code_audit, "MAX_DIRECTORIES", 1)
    (tmp_path / "child").mkdir()
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_DIRECTORY_LIMIT_EXCEEDED"

    monkeypatch.setattr(code_audit, "MAX_DIRECTORIES", 10)
    monkeypatch.setattr(code_audit, "MAX_DEPTH", 0)
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_DEPTH_LIMIT_EXCEEDED"


def test_all_reported_paths_are_relative_normalized_and_contained(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-10"""
    _write(tmp_path, "src/nested/risk.ts", "const client = { rejectUnauthorized: false };\n")
    result = run_code_audit(tmp_path)
    path = dict(_findings(result)[0].details)["file"]
    assert path == "src/nested/risk.ts"
    assert str(tmp_path) not in repr(result)


def test_indirect_target_root_is_rejected(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-11"""
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(link)
    assert _error_code(caught) == "CODE_AUDIT_TARGET_INDIRECT"


def test_descendant_symlink_or_reparse_point_blocks_the_scan(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-12"""
    outside = tmp_path.parent / f"{tmp_path.name}-outside.py"
    outside.write_text("eval(value)", encoding="utf-8")
    link = tmp_path / "linked.py"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        outside.unlink(missing_ok=True)
        pytest.skip(f"file symlink unavailable: {exc}")
    try:
        with pytest.raises(SkillExecutionError) as caught:
            run_code_audit(tmp_path)
        assert _error_code(caught) == "CODE_AUDIT_UNSAFE_PATH"
    finally:
        outside.unlink(missing_ok=True)


def test_binary_candidate_blocks_without_exposing_content(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-13"""
    secret = b"secret-sentinel\x00tail"
    _write(tmp_path, "binary.py", secret)
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_BINARY_FILE"
    assert "secret-sentinel" not in str(caught.value)


def test_non_utf8_candidate_blocks_without_partial_result(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-14"""
    _write(tmp_path, "invalid.py", b"\xff\xfe")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_INVALID_ENCODING"

    _write(tmp_path, "invalid.py", b"value=1\xef\xbb\xbf\n")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_INVALID_ENCODING"


def test_unreadable_or_concurrently_changed_candidate_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-15"""
    candidate = _write(tmp_path, "source.py", "value=1")
    real_open = os.open

    def guarded(path, flags, *args, **kwargs):
        if Path(path) == candidate:
            raise PermissionError("denied")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", guarded)
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_READ_FAILED"


def test_audit_never_imports_parses_by_execution_or_calls_project_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-16"""
    marker = tmp_path / "marker"
    _write(tmp_path, "payload.py", f"Path({str(marker)!r}).write_text('executed')\n")
    original_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "payload":
            raise AssertionError("target import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    run_code_audit(tmp_path)
    assert not marker.exists()


def test_audit_uses_no_subprocess_shell_or_git_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-17"""
    _write(tmp_path, "source.py", "value=1")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("process"))
    run_code_audit(tmp_path)


def test_audit_opens_no_path_for_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-18"""
    _write(tmp_path, "source.py", "value=1")
    real_open = os.open

    def guarded(path, flags, *args, **kwargs):
        assert flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND) == 0
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", guarded)
    run_code_audit(tmp_path)


def test_audit_attempts_no_network_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-19"""
    _write(tmp_path, "source.ts", "const value = 1")
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network"))
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: pytest.fail("network"))
    run_code_audit(tmp_path)


def test_git_state_is_identical_before_and_after_audit(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-20"""
    _write(tmp_path, "source.py", "verify=False\n")
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Code Audit Test")
    git(tmp_path, "config", "user.email", "audit@invalid.local")
    git(tmp_path, "add", "source.py")
    git(tmp_path, "commit", "-m", "fixture")

    def snapshot() -> tuple[str, str, str, str]:
        return (
            git(tmp_path, "rev-parse", "HEAD").stdout,
            git(tmp_path, "status", "--porcelain=v1").stdout,
            git(tmp_path, "diff", "--cached", "--name-status").stdout,
            git(tmp_path, "show-ref").stdout,
        )

    before = snapshot()
    run_code_audit(tmp_path)
    assert snapshot() == before


def test_finding_model_is_immutable_and_rejects_invalid_values() -> None:
    """Spec: HERMES-0008 / AC-21"""
    region = CodeAuditRegion(1, 1, 1, 2)
    finding = CodeAuditFinding(
        "CA001", CodeAuditSeverity.HIGH, CodeAuditClassification.HYPOTHESIS,
        "source.py", region, "eval(x)", "Call observed.", "It may be risky.", "Remove it.",
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        finding.file = "other.py"
    with pytest.raises(SkillExecutionError):
        CodeAuditRegion(0, 1)
    with pytest.raises(SkillExecutionError):
        code_audit.CodeAuditSummary(
            -1, 0, 0, 0, 0, 0, 0, 0,
            ("CA001", "CA002", "CA003", "CA004", "CA005"), 1,
            tuple(sorted(code_audit.ALLOWED_EXTENSIONS)), 32, 5000, 1000,
            524288, 20971520, 200,
        )


def test_every_finding_has_required_evidence_and_remediation_fields(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-22"""
    _write(tmp_path, "source.py", "eval(value)\n")
    details = _details(_findings(run_code_audit(tmp_path))[0])
    assert all(details[name] for name in (
        "severity", "classification", "file", "region", "evidence",
        "observation", "justification", "suggestion",
    ))


def test_finding_distinguishes_observation_from_hypothesis(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-23"""
    _write(tmp_path, "source.py", "eval(value)\nverify=False\n")
    classifications = [dict(item.details)["classification"] for item in _findings(run_code_audit(tmp_path))]
    assert classifications == ["hypothesis", "observed"]


def test_no_finding_is_emitted_without_a_local_rule_trigger(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-24"""
    _write(tmp_path, "security.py", "def validate(value):\n    return bool(value)\n")
    assert not _findings(run_code_audit(tmp_path))


def test_evidence_is_bounded_sanitized_and_secret_values_are_redacted(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-25"""
    sentinel = "super-secret-sentinel"
    _write(tmp_path, "source.py", f'api_token = "{sentinel}"\n')
    result = run_code_audit(tmp_path)
    finding = dict(_findings(result)[0].details)
    assert sentinel not in repr(result)
    assert "<redacted>" in finding["evidence"]
    assert len(finding["evidence"]) <= code_audit.MAX_EVIDENCE_CHARS


def test_closed_initial_rule_set_emits_expected_findings(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-26"""
    _write(tmp_path, "rules.py", "\n".join((
        "eval(value)",
        "os.system(command)",
        "verify=False",
        'api_token = "value"',
        "security_token = random.random()",
    )))
    findings = _findings(run_code_audit(tmp_path))
    assert [item.code for item in findings] == ["CA001", "CA002", "CA003", "CA004", "CA005"]

    _write(tmp_path, "tls.ts", 'NODE_TLS_REJECT_UNAUTHORIZED="0"\n')
    assert any(item.code == "CA003" for item in _findings(run_code_audit(tmp_path)))


def test_comments_examples_and_ordinary_strings_do_not_create_findings(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-27"""
    _write(tmp_path, "source.py", """\
# eval(value)
example = "verify=False"
documentation = '''os.system(command)'''
""")
    _write(tmp_path, "source.ts", "// eval(value)\nconst example = 'rejectUnauthorized: false';\n/* execSync(command) */\n")
    assert not _findings(run_code_audit(tmp_path))


def test_clean_fixture_returns_passed_without_invented_findings(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-28"""
    _write(tmp_path, "source.py", "def add(a, b):\n    return a + b\n")
    result = run_code_audit(tmp_path)
    assert (result.status, result.exit_code, len(_findings(result))) == (SkillExecutionStatus.PASSED, 0, 0)


def test_finding_limit_blocks_instead_of_truncating_silently(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0008 / AC-29"""
    monkeypatch.setattr(code_audit, "MAX_FINDINGS", 1)
    _write(tmp_path, "source.py", "eval(first)\neval(second)\n")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_FINDING_LIMIT_EXCEEDED"


def test_structural_failure_returns_no_partial_findings(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-30"""
    _write(tmp_path, "a.py", "eval(value)\n")
    _write(tmp_path, "z.py", b"\x00binary")
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(tmp_path)
    assert _error_code(caught) == "CODE_AUDIT_BINARY_FILE"
    assert not hasattr(caught.value, "result") and not hasattr(caught.value, "findings")


def test_code_audit_ignores_target_skills_and_preserves_exact_lookup(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-36"""
    _write(tmp_path, "skills/code-audit/SKILL.md", "malicious handler")
    result = run_skill(tmp_path, "code-audit", _policy())
    assert result.status is SkillExecutionStatus.PASSED


def test_git_preflight_contract_is_unchanged_after_code_audit(committed_git_repo: Path) -> None:
    """Spec: HERMES-0008 / AC-37"""
    result = run_skill(committed_git_repo, "git-preflight", _policy())
    assert result.skill_id == "git-preflight" and result.exit_code == 0


def test_code_audit_rejects_linked_worktree_without_mutation(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-38"""
    repository = tmp_path / "repository"
    worktree = tmp_path / "linked"
    repository.mkdir()
    _write(repository, "source.py", "value=1\n")
    git(repository, "init", "-b", "main")
    git(repository, "config", "user.name", "Code Audit Test")
    git(repository, "config", "user.email", "audit@invalid.local")
    git(repository, "add", "source.py")
    git(repository, "commit", "-m", "fixture")
    git(repository, "worktree", "add", "-b", "audit-linked", str(worktree))
    head = git(worktree, "rev-parse", "HEAD").stdout
    status = git(worktree, "status", "--porcelain=v1").stdout
    with pytest.raises(SkillExecutionError) as caught:
        run_code_audit(worktree)
    assert _error_code(caught) == "CODE_AUDIT_TARGET_INDIRECT"
    assert git(worktree, "rev-parse", "HEAD").stdout == head
    assert git(worktree, "status", "--porcelain=v1").stdout == status
