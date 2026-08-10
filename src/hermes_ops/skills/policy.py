from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hermes_ops.core.errors import SkillPolicyError
from hermes_ops.skills.models import SkillDefinition, SkillRisk, SkillStatus
from hermes_ops.skills.registry import SkillRegistry
from hermes_ops.skills.validator import ID_PATTERN


_RISK_LEVEL = {
    SkillRisk.LOW: 0,
    SkillRisk.MEDIUM: 1,
    SkillRisk.HIGH: 2,
}


def _fail(code: str, message: str) -> None:
    raise SkillPolicyError(code, message)


@dataclass(frozen=True, slots=True)
class SkillPolicy:
    max_risk: SkillRisk
    allow_write: bool
    available_requires: frozenset[str]

    def __post_init__(self) -> None:
        if type(self.max_risk) is not SkillRisk:
            _fail("SKILL_POLICY_INVALID", "Policy max_risk must be a SkillRisk")
        if type(self.allow_write) is not bool:
            _fail("SKILL_POLICY_INVALID", "Policy allow_write must be a boolean")
        if type(self.available_requires) is not frozenset:
            _fail(
                "SKILL_POLICY_INVALID",
                "Policy available_requires must be a frozenset",
            )
        for requirement in self.available_requires:
            if (
                type(requirement) is not str
                or not requirement
                or not requirement.strip()
                or requirement != requirement.strip()
            ):
                _fail(
                    "SKILL_POLICY_INVALID",
                    "Policy requirements must be non-empty strings without outer whitespace",
                )


def _evaluate_skill(skill: SkillDefinition, policy: SkillPolicy) -> None:
    if skill.status is not SkillStatus.ACTIVE:
        _fail(
            "SKILL_POLICY_STATUS_NOT_ACTIVE",
            f"Skill '{skill.id}' is not active",
        )
    if _RISK_LEVEL[skill.risk] > _RISK_LEVEL[policy.max_risk]:
        _fail(
            "SKILL_POLICY_RISK_EXCEEDED",
            f"Skill '{skill.id}' exceeds the allowed risk",
        )
    if skill.allows_write is True and policy.allow_write is False:
        _fail(
            "SKILL_POLICY_WRITE_NOT_ALLOWED",
            f"Skill '{skill.id}' declares write access that policy does not allow",
        )
    for requirement in skill.requires:
        if requirement not in policy.available_requires:
            _fail(
                "SKILL_POLICY_REQUIREMENT_UNAVAILABLE",
                f"Skill '{skill.id}' requires unavailable requirement '{requirement}'",
            )


@dataclass(frozen=True, slots=True)
class SkillPlan:
    skills: tuple[SkillDefinition, ...]
    policy: SkillPolicy

    def __post_init__(self) -> None:
        if type(self.skills) is not tuple or not self.skills:
            _fail("SKILL_PLAN_INVALID", "Plan skills must be a non-empty tuple")
        if any(not isinstance(skill, SkillDefinition) for skill in self.skills):
            _fail(
                "SKILL_PLAN_INVALID",
                "Plan skills must contain only SkillDefinition values",
            )
        identifiers = tuple(skill.id for skill in self.skills)
        if len(set(identifiers)) != len(identifiers):
            _fail("SKILL_PLAN_INVALID", "Plan skills contain duplicate identifiers")
        if type(self.policy) is not SkillPolicy:
            _fail("SKILL_PLAN_INVALID", "Plan policy must be a SkillPolicy")
        for skill in self.skills:
            _evaluate_skill(skill, self.policy)


def plan_skills(
    registry: Any,
    requested_ids: Any,
    policy: Any,
) -> SkillPlan:
    if not isinstance(registry, SkillRegistry):
        _fail("SKILL_PLAN_INVALID", "Registry must be a SkillRegistry")
    if type(policy) is not SkillPolicy:
        _fail("SKILL_POLICY_INVALID", "Policy must be a SkillPolicy")
    if type(requested_ids) is not tuple or any(
        type(skill_id) is not str for skill_id in requested_ids
    ):
        _fail("SKILL_PLAN_REQUEST_INVALID", "Requested IDs must be a tuple of strings")
    if not requested_ids:
        _fail("SKILL_PLAN_EMPTY_REQUEST", "At least one skill must be requested")
    if any(ID_PATTERN.fullmatch(skill_id) is None for skill_id in requested_ids):
        _fail(
            "SKILL_PLAN_REQUEST_INVALID",
            "Every requested ID must use the skill identifier grammar",
        )
    if len(set(requested_ids)) != len(requested_ids):
        _fail(
            "SKILL_PLAN_DUPLICATE_REQUEST",
            "Requested IDs contain a duplicate identifier",
        )

    resolved: list[SkillDefinition] = []
    for skill_id in requested_ids:
        skill = registry.get_by_id(skill_id)
        if skill is None:
            _fail(
                "SKILL_PLAN_SKILL_NOT_FOUND",
                f"Requested skill '{skill_id}' was not found",
            )
        resolved.append(skill)

    for skill in resolved:
        _evaluate_skill(skill, policy)
    return SkillPlan(tuple(resolved), policy)
