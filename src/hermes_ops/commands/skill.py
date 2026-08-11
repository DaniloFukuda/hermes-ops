from __future__ import annotations

import json
from typing import Any

from hermes_ops.core.presentation import PublicSanitizer
from hermes_ops.skills import SkillExecutionResult, SkillPolicy, SkillRisk, run_skill


PILOT_POLICY = SkillPolicy(
    max_risk=SkillRisk.LOW,
    allow_write=False,
    available_requires=frozenset({"git"}),
)


def run_skill_command(target_project: str, skill_id: str) -> SkillExecutionResult:
    return run_skill(target_project, skill_id, PILOT_POLICY)


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
                "details": item.details,
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
    lines = [f"skill_id={result.skill_id}", f"status={result.status.value}"]
    lines.extend(
        f"{item.status.value:<9} {item.name}: {sanitizer.sanitize_text(item.message)}"
        for item in result.evidence
    )
    lines.append(f"exit_code={result.exit_code}")
    return "\n".join(lines)
