from __future__ import annotations

from pathlib import Path
from typing import Any

from hermes_ops.commands.preflight import run_preflight
from hermes_ops.core.errors import PathResolutionError, SkillExecutionError
from hermes_ops.core.paths import resolve_directory
from hermes_ops.core.results import Report
from hermes_ops.skills.catalog import resolve_own_skill_catalog
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


def _run_git_preflight(target_project: str | Path) -> SkillExecutionResult:
    report = run_preflight(target_project)
    if type(report) is not Report:
        _invalid("The git-preflight handler did not return a Report")
    return _build_execution_result("git-preflight", report)


def _dispatch_skill(plan: SkillPlan, target_project: str | Path) -> SkillExecutionResult:
    if type(plan) is not SkillPlan or len(plan.skills) != 1:
        _invalid("Execution requires an approved unitary SkillPlan")
    if plan.skills[0].id == "git-preflight":
        return _run_git_preflight(target_project)
    raise SkillExecutionError(
        "SKILL_EXECUTION_NOT_SUPPORTED",
        f"Skill '{plan.skills[0].id}' has no execution handler",
    )


def _run_skill_with_catalog(
    project_root: Any,
    skill_id: Any,
    policy: Any,
    catalog_root: Path,
) -> SkillExecutionResult:
    if project_root is None or type(skill_id) is not str or type(policy) is not SkillPolicy:
        _invalid("Execution requires an explicit project root, skill id, and SkillPolicy")
    try:
        target_project = resolve_directory(project_root)
    except PathResolutionError as exc:
        raise SkillExecutionError(
            "SKILL_TARGET_INVALID",
            "The explicit target project is not a valid directory",
        ) from exc
    registry = discover_skills(catalog_root)
    plan = plan_skills(registry, (skill_id,), policy)
    return _dispatch_skill(plan, target_project)


def run_skill(
    project_root: Any,
    skill_id: Any,
    policy: Any,
) -> SkillExecutionResult:
    if project_root is None or type(skill_id) is not str or type(policy) is not SkillPolicy:
        _invalid("Execution requires an explicit project root, skill id, and SkillPolicy")
    try:
        target_project = resolve_directory(project_root)
    except PathResolutionError as exc:
        raise SkillExecutionError(
            "SKILL_TARGET_INVALID",
            "The explicit target project is not a valid directory",
        ) from exc
    catalog_root = resolve_own_skill_catalog()
    return _run_skill_with_catalog(target_project, skill_id, policy, catalog_root)
