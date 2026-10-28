from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_ops.core.presentation import PublicSanitizer
from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills import SkillExecutionResult, SkillPolicy, SkillRisk, SkillRunInputs, run_skill
from hermes_ops.git import GitInspector
from hermes_ops.memory.models import DisclosureLevel, MemoryCurrentContext, RepositoryIdentity
from hermes_ops.memory.store import MemoryService
from hermes_ops.orchestration import (
    MemoryAssistedAuditRequest,
    MemoryAssistedAuditResult,
    MemoryMode,
    memory_assisted_audit_json,
    run_memory_assisted_audit,
)
from hermes_ops.skills.audit_round import AuditRoundStatus, CodeAuditRequest


PILOT_POLICY = SkillPolicy(
    max_risk=SkillRisk.LOW,
    allow_write=False,
    available_requires=frozenset({"git"}),
)


def build_cli_current_context(
    target_project: str,
    repository_identity: RepositoryIdentity,
    structural_scope: tuple[str, ...],
) -> MemoryCurrentContext:
    """Build optional local provenance without reading target source content."""
    git_state = GitInspector().inspect(Path(target_project))
    return MemoryCurrentContext(
        repository_id=repository_identity.repository_id,
        current_revision=(git_state.head if git_state.has_commits and not git_state.error else None),
        current_structural_scope=structural_scope,
    )


def _structured_details(value: Any) -> Any:
    if isinstance(value, tuple):
        if value and all(
            isinstance(item, tuple)
            and len(item) == 2
            and isinstance(item[0], str)
            for item in value
        ):
            return {item[0]: _structured_details(item[1]) for item in value}
        return [_structured_details(item) for item in value]
    return value


def run_skill_command(
    target_project: str,
    skill_id: str,
    mission: str | None = None,
    include_paths: tuple[str, ...] | list[str] | None = None,
    producer_symbol: str | None = None,
    consumer_symbol: str | None = None,
) -> SkillExecutionResult:
    inputs = SkillRunInputs(
        mission,
        include_paths=tuple(include_paths) if include_paths else (),
        producer_symbol=producer_symbol,
        consumer_symbol=consumer_symbol,
    )
    return run_skill(target_project, skill_id, PILOT_POLICY, inputs=inputs)


def run_memory_assisted_skill_command(
    target_project: str,
    mission: str | None,
    include_paths: tuple[str, ...] | list[str] | None,
    memory_mode: str,
    memory_store: str | None,
    repository_id: str | None,
    memory_disclosure: str = "header",
) -> MemoryAssistedAuditResult:
    if not mission or not mission.strip():
        raise SkillExecutionError("SKILL_EXECUTION_INVALID", "Memory-assisted audit requires --mission")
    modes = {
        "off": MemoryMode.DISABLED,
        "read": MemoryMode.READ_ONLY,
        "read-write": MemoryMode.READ_WRITE,
    }
    mode = modes[memory_mode]
    disclosures = {
        "header": DisclosureLevel.HEADER,
        "structured": DisclosureLevel.STRUCTURED,
        "canonical": DisclosureLevel.CANONICAL,
        "revalidation-hint": DisclosureLevel.REVALIDATION_HINT,
    }
    if mode is not MemoryMode.DISABLED and not memory_store:
        raise SkillExecutionError("SKILL_EXECUTION_INVALID", "Active Memory mode requires --memory-store")
    if mode is not MemoryMode.DISABLED and not repository_id:
        raise SkillExecutionError("SKILL_EXECUTION_INVALID", "Active Memory mode requires --repository-id")
    identity = RepositoryIdentity.explicit(repository_id or "local-project")
    current_context = None
    if mode is not MemoryMode.DISABLED:
        current_context = build_cli_current_context(
            target_project, identity,
            tuple(include_paths) if include_paths else (),
        )
    request = MemoryAssistedAuditRequest(
        mission=mission,
        target=target_project,
        repository_identity=identity,
        current_context=current_context,
        authoritative_structural_scope=tuple(include_paths) if include_paths else (),
        audit_requests=(CodeAuditRequest(),),
        memory_mode=mode,
        memory_disclosure_level=disclosures[memory_disclosure],
        allow_post_audit_write=mode is MemoryMode.READ_WRITE,
    )
    if mode is MemoryMode.DISABLED:
        return run_memory_assisted_audit(request)
    with MemoryService.open(memory_store, read_only=mode is MemoryMode.READ_ONLY) as service:
        return run_memory_assisted_audit(request, service)


def memory_assisted_result_json(
    result: MemoryAssistedAuditResult, sanitizer: PublicSanitizer,
) -> str:
    return json.dumps(
        sanitizer.sanitize(json.loads(memory_assisted_audit_json(result))),
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )


def memory_assisted_result_text(
    result: MemoryAssistedAuditResult, sanitizer: PublicSanitizer,
) -> str:
    context = result.historical_context
    reasons = context.candidate_reason_codes or {}
    candidates = tuple(
        f"candidate={item.observation_id} freshness={item.freshness_state.value} "
        f"privacy={item.privacy_state.value} "
        f"canonical={'AVAILABLE' if item.canonical_available else 'BLOCKED'} "
        f"score={item.retrieval_score} reasons={','.join(reasons.get(item.observation_id, ()))}"
        for item in context.candidates
    )
    metrics = context.operational_metrics
    metric_lines = () if metrics is None else (
        f"disclosure={context.effective_disclosure.value}",
        f"metrics=retrieval_requested={str(metrics.retrieval_requested).lower()},"
        f"candidates_returned={metrics.candidates_returned},hints_returned={metrics.hints_returned},"
        f"writeback_attempted={str(metrics.writeback_attempted).lower()},"
        f"observations_written={metrics.observations_written},"
        f"diagnostics={metrics.memory_diagnostics_count}",
        f"timing_ms=retrieval:{metrics.retrieval_duration_ms:.3f},"
        f"disclosure:{metrics.disclosure_duration_ms:.3f},writeback:{metrics.writeback_duration_ms:.3f}",
    )
    return "\n".join((
        "HISTORICAL MEMORY",
        f"candidates={len(result.historical_context.candidates)}",
        f"diagnostics={','.join(result.historical_context.memory_diagnostics)}",
        *metric_lines,
        *candidates,
        "CURRENT AUDIT RESULT",
        f"status={result.fresh_audit.status.value}",
        f"findings={len(result.fresh_audit.ranked_findings.ordered_findings)}",
        f"limitations={len(result.fresh_audit.limitations)}",
    ))


def skill_result_payload(
    result: SkillExecutionResult,
    sanitizer: PublicSanitizer,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "skill_id": result.skill_id,
        "status": result.status.value,
        "exit_code": result.exit_code,
        "evidence": [
            {
                "name": item.name,
                "status": item.status.value,
                "message": item.message,
                "details": (
                    _structured_details(item.details)
                    if result.skill_id in {"code-audit", "mission-audit", "execution-path-review"}
                    else item.details
                ),
                "code": item.code,
            }
            for item in result.evidence
        ],
    }
    return sanitizer.sanitize(payload)


def skill_result_json(result: SkillExecutionResult, sanitizer: PublicSanitizer) -> str:
    return json.dumps(
        skill_result_payload(result, sanitizer),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def skill_result_text(result: SkillExecutionResult, sanitizer: PublicSanitizer) -> str:
    if result.skill_id == "code-audit":
        return _code_audit_result_text(result, sanitizer)
    if result.skill_id == "mission-audit":
        return _mission_audit_result_text(result, sanitizer)
    lines = [f"skill_id={result.skill_id}", f"status={result.status.value}"]
    lines.extend(
        f"{item.status.value:<9} {item.name}: {sanitizer.sanitize_text(item.message)}"
        for item in result.evidence
    )
    lines.append(f"exit_code={result.exit_code}")
    return "\n".join(lines)


def _mission_audit_result_text(result: SkillExecutionResult, sanitizer: PublicSanitizer) -> str:
    pack = _structured_details(result.evidence[0].details)
    lines = [f"skill_id={result.skill_id}", f"status={result.status.value}"]
    if isinstance(pack, dict):
        completeness = pack.get("completeness", {})
        lines.extend((f"mission={sanitizer.sanitize_text(str(pack.get('mission', '')))}", f"target={pack.get('target')}", f"completeness={completeness.get('status') if isinstance(completeness, dict) else 'unknown'}"))
        for item in pack.get("files", []):
            if isinstance(item, dict): lines.append(f"file={sanitizer.sanitize_text(str(item.get('path')))} score={item.get('score')}")
        lines.append("note=Evidence identifies traceable locations; it does not assert defects or correctness.")
    lines.append(f"exit_code={result.exit_code}")
    return "\n".join(lines)


def _code_audit_result_text(
    result: SkillExecutionResult,
    sanitizer: PublicSanitizer,
) -> str:
    lines = [f"skill_id={result.skill_id}", f"status={result.status.value}"]
    summary = _structured_details(result.evidence[0].details)
    if isinstance(summary, dict):
        lines.extend(
            (
                f"scanned_directories={summary['directories']}",
                f"scanned_files={summary['files']}",
                f"scanned_bytes={summary['bytes_read']}",
                f"findings={sum(summary[key] for key in ('findings_info', 'findings_low', 'findings_medium', 'findings_high', 'findings_critical'))}",
            )
        )
    for evidence in result.evidence[1:]:
        finding = _structured_details(evidence.details)
        if not isinstance(finding, dict):
            continue
        region = finding["region"]
        start = f"{region['start_line']}:{region['start_column']}"
        end = f"{region['end_line']}:{region['end_column']}"
        lines.extend(
            (
                "",
                f"[{str(finding['severity']).upper()}] {finding['rule_id']} {finding['classification']}",
                f"file={sanitizer.sanitize_text(str(finding['file']))}",
                f"region={start}-{end}",
                f"evidence={sanitizer.sanitize_text(str(finding['evidence']))}",
                f"observation={sanitizer.sanitize_text(str(finding['observation']))}",
                f"justification={sanitizer.sanitize_text(str(finding['justification']))}",
                f"suggestion={sanitizer.sanitize_text(str(finding['suggestion']))}",
            )
        )
    lines.append(f"exit_code={result.exit_code}")
    return "\n".join(lines)
