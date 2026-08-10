from __future__ import annotations

from pathlib import Path
from typing import Any

from hermes_ops.commands.preflight import run_preflight
from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.core.results import Report
from hermes_ops.skills.execution_models import (
    SkillExecutionEvidence,
    SkillExecutionResult,
    SkillExecutionStatus,
)
from hermes_ops.skills.policy import SkillPlan, SkillPolicy, plan_skills
from hermes_ops.skills.registry import discover_skills


def _invalid(message: str) -> None:
    raise SkillExecutionError("SKILL_EXECUTION_INVALID", message)


def _build_execution_result(skill_id: str, report: Report) -> SkillExecutionResult:
    if type(skill_id) is not str or type(report) is not Report:
        _invalid("Execution result inputs are invalid")
    evidence = tuple(
        SkillExecutionEvidence(
            item.name,
            item.status,
            item.message,
            item.details,
            item.code,
        )
        for item in report.results
    )
    exit_code = report.exit_code
    status = (
        SkillExecutionStatus.PASSED
        if exit_code == 0
        else SkillExecutionStatus.COMPLETED_WITH_FINDINGS
    )
    return SkillExecutionResult(skill_id, status, exit_code, evidence)


def _run_git_preflight(project_root: str | Path) -> SkillExecutionResult:
    report = run_preflight(project_root)
    if type(report) is not Report:
        _invalid("The git-preflight handler did not return a Report")
    return _build_execution_result("git-preflight", report)


def _dispatch_skill(plan: SkillPlan, project_root: str | Path) -> SkillExecutionResult:
    if type(plan) is not SkillPlan or len(plan.skills) != 1:
        _invalid("Execution requires an approved unitary SkillPlan")
    if plan.skills[0].id == "git-preflight":
        return _run_git_preflight(project_root)
    raise SkillExecutionError(
        "SKILL_EXECUTION_NOT_SUPPORTED",
        f"Skill '{plan.skills[0].id}' has no execution handler",
    )


def run_skill(
    project_root: Any,
    skill_id: Any,
    policy: Any,
) -> SkillExecutionResult:
    if project_root is None or type(skill_id) is not str or type(policy) is not SkillPolicy:
        _invalid("Execution requires an explicit project root, skill id, and SkillPolicy")
    registry = discover_skills(project_root)
    plan = plan_skills(registry, (skill_id,), policy)
    return _dispatch_skill(plan, project_root)
