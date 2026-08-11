from __future__ import annotations

import json
from typing import Any

from hermes_ops.core.presentation import PublicSanitizer
from hermes_ops.skills import SkillExecutionResult, SkillPolicy, SkillRisk, SkillRunInputs, run_skill


PILOT_POLICY = SkillPolicy(
    max_risk=SkillRisk.LOW,
    allow_write=False,
    available_requires=frozenset({"git"}),
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


def run_skill_command(target_project: str, skill_id: str, mission: str | None = None) -> SkillExecutionResult:
    return run_skill(target_project, skill_id, PILOT_POLICY, inputs=SkillRunInputs(mission))


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
                    if result.skill_id in {"code-audit", "mission-audit"}
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
