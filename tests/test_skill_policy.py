from __future__ import annotations

import builtins
from dataclasses import FrozenInstanceError
import importlib
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from conftest import git
from hermes_ops.skills.models import SkillDefinition, SkillRisk, SkillStatus
from hermes_ops.skills.registry import SkillRegistry


def _policy_api():
    api = importlib.import_module("hermes_ops.skills")
    required = ("SkillPlan", "SkillPolicy", "SkillPolicyError", "plan_skills")
    missing = [name for name in required if not hasattr(api, name)]
    if missing:
        pytest.fail(
            "HERMES-0005 production API is not implemented: missing "
            + ", ".join(missing),
            pytrace=False,
        )
    return api


def _definition(
    skill_id: str,
    *,
    status: SkillStatus = SkillStatus.ACTIVE,
    risk: SkillRisk = SkillRisk.LOW,
    allows_write: bool = False,
    requires: tuple[str, ...] = (),
    body: str = "Passive skill body",
) -> SkillDefinition:
    return SkillDefinition(
        schema_version=1,
        id=skill_id,
        version=1,
        status=status,
        description=f"Definition for {skill_id}",
        risk=risk,
        requires=requires,
        allows_write=allows_write,
        path=Path("skills") / skill_id / "SKILL.md",
        body=body,
    )


def _registry(*skills: SkillDefinition) -> SkillRegistry:
    return SkillRegistry(tuple(skills))


def _policy(
    *,
    max_risk: SkillRisk = SkillRisk.LOW,
    allow_write: bool = False,
    available_requires: frozenset[str] = frozenset(),
):
    return _policy_api().SkillPolicy(
        max_risk=max_risk,
        allow_write=allow_write,
        available_requires=available_requires,
    )


def _plan(
    registry: Any,
    requested_ids: Any,
    policy: Any,
):
    return _policy_api().plan_skills(registry, requested_ids, policy)


def _error_code(exc: BaseException) -> str | None:
    return getattr(exc, "code", None)


def _expect_error(code: str):
    return pytest.raises(_policy_api().SkillPolicyError, match=".+")


def _assert_code(caught: pytest.ExceptionInfo[BaseException], code: str) -> None:
    assert _error_code(caught.value) == code


def test_skill_policy_is_immutable_and_strict() -> None:
    """Spec: HERMES-0005 / AC-01"""
    policy = _policy(
        max_risk=SkillRisk.MEDIUM,
        allow_write=False,
        available_requires=frozenset({"git"}),
    )
    assert policy.max_risk is SkillRisk.MEDIUM
    assert policy.allow_write is False
    assert policy.available_requires == frozenset({"git"})
    assert isinstance(policy.available_requires, frozenset)
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        policy.allow_write = True


def test_skill_plan_is_immutable() -> None:
    """Spec: HERMES-0005 / AC-02"""
    api = _policy_api()
    skill = _definition("immutable-skill")
    policy = _policy()
    plan = api.SkillPlan((skill,), policy)
    assert plan.skills == (skill,)
    assert isinstance(plan.skills, tuple)
    assert plan.policy is policy
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        plan.skills += (_definition("other-skill"),)


def test_empty_request_is_rejected() -> None:
    """Spec: HERMES-0005 / AC-03"""
    with _expect_error("SKILL_PLAN_EMPTY_REQUEST") as caught:
        _plan(_registry(), (), _policy())
    _assert_code(caught, "SKILL_PLAN_EMPTY_REQUEST")


def test_single_active_skill_is_planned() -> None:
    """Spec: HERMES-0005 / AC-04"""
    skill = _definition("single-skill")
    policy = _policy()
    plan = _plan(_registry(skill), (skill.id,), policy)
    assert plan.skills == (skill,)
    assert plan.policy is policy


def test_multiple_eligible_skills_form_complete_plan() -> None:
    """Spec: HERMES-0005 / AC-05"""
    first = _definition("first-skill")
    second = _definition("second-skill")
    plan = _plan(_registry(first, second), (first.id, second.id), _policy())
    assert plan.skills == (first, second)


def test_plan_preserves_requested_order() -> None:
    """Spec: HERMES-0005 / AC-06"""
    a = _definition("a")
    b = _definition("b")
    c = _definition("c")
    registry = _registry(c, a, b)
    assert tuple(skill.id for skill in registry.skills) == ("a", "b", "c")
    plan = _plan(registry, ("c", "a"), _policy())
    assert tuple(skill.id for skill in plan.skills) == ("c", "a")


def test_unknown_skill_id_is_rejected() -> None:
    """Spec: HERMES-0005 / AC-07"""
    with _expect_error("SKILL_PLAN_SKILL_NOT_FOUND") as caught:
        _plan(_registry(), ("missing-skill",), _policy())
    _assert_code(caught, "SKILL_PLAN_SKILL_NOT_FOUND")


def test_duplicate_requested_id_is_rejected() -> None:
    """Spec: HERMES-0005 / AC-08"""
    skill = _definition("duplicate-skill")
    with _expect_error("SKILL_PLAN_DUPLICATE_REQUEST") as caught:
        _plan(_registry(skill), (skill.id, skill.id), _policy())
    _assert_code(caught, "SKILL_PLAN_DUPLICATE_REQUEST")


def test_draft_skill_is_rejected() -> None:
    """Spec: HERMES-0005 / AC-09"""
    skill = _definition("draft-skill", status=SkillStatus.DRAFT)
    with _expect_error("SKILL_POLICY_STATUS_NOT_ACTIVE") as caught:
        _plan(_registry(skill), (skill.id,), _policy(max_risk=SkillRisk.HIGH))
    _assert_code(caught, "SKILL_POLICY_STATUS_NOT_ACTIVE")


def test_deprecated_skill_is_rejected() -> None:
    """Spec: HERMES-0005 / AC-10"""
    skill = _definition("deprecated-skill", status=SkillStatus.DEPRECATED)
    with _expect_error("SKILL_POLICY_STATUS_NOT_ACTIVE") as caught:
        _plan(_registry(skill), (skill.id,), _policy(max_risk=SkillRisk.HIGH))
    _assert_code(caught, "SKILL_POLICY_STATUS_NOT_ACTIVE")


def test_low_risk_allowed_by_low_policy() -> None:
    """Spec: HERMES-0005 / AC-11"""
    skill = _definition("low-skill", risk=SkillRisk.LOW)
    assert _plan(_registry(skill), (skill.id,), _policy()).skills == (skill,)


def test_medium_risk_blocked_by_low_policy() -> None:
    """Spec: HERMES-0005 / AC-12"""
    skill = _definition("medium-skill", risk=SkillRisk.MEDIUM)
    with _expect_error("SKILL_POLICY_RISK_EXCEEDED") as caught:
        _plan(_registry(skill), (skill.id,), _policy(max_risk=SkillRisk.LOW))
    _assert_code(caught, "SKILL_POLICY_RISK_EXCEEDED")


def test_medium_risk_allowed_by_medium_policy() -> None:
    """Spec: HERMES-0005 / AC-13"""
    skill = _definition("medium-skill", risk=SkillRisk.MEDIUM)
    plan = _plan(
        _registry(skill),
        (skill.id,),
        _policy(max_risk=SkillRisk.MEDIUM),
    )
    assert plan.skills == (skill,)


def test_high_risk_blocked_by_medium_policy() -> None:
    """Spec: HERMES-0005 / AC-14"""
    skill = _definition("high-skill", risk=SkillRisk.HIGH)
    with _expect_error("SKILL_POLICY_RISK_EXCEEDED") as caught:
        _plan(_registry(skill), (skill.id,), _policy(max_risk=SkillRisk.MEDIUM))
    _assert_code(caught, "SKILL_POLICY_RISK_EXCEEDED")


def test_high_risk_allowed_by_high_policy() -> None:
    """Spec: HERMES-0005 / AC-15"""
    skill = _definition("high-skill", risk=SkillRisk.HIGH)
    plan = _plan(
        _registry(skill),
        (skill.id,),
        _policy(max_risk=SkillRisk.HIGH),
    )
    assert plan.skills == (skill,)


def test_read_only_declaration_allowed_when_policy_disallows_write() -> None:
    """Spec: HERMES-0005 / AC-16"""
    skill = _definition("read-only-skill", allows_write=False)
    plan = _plan(_registry(skill), (skill.id,), _policy(allow_write=False))
    assert plan.skills == (skill,)


def test_write_declaration_blocked_when_policy_disallows_write() -> None:
    """Spec: HERMES-0005 / AC-17"""
    skill = _definition("write-skill", allows_write=True)
    with _expect_error("SKILL_POLICY_WRITE_NOT_ALLOWED") as caught:
        _plan(_registry(skill), (skill.id,), _policy(allow_write=False))
    _assert_code(caught, "SKILL_POLICY_WRITE_NOT_ALLOWED")


def test_write_declaration_can_be_planned_without_writing(tmp_path: Path) -> None:
    """Spec: HERMES-0005 / AC-18"""
    marker = tmp_path / "must-not-exist"
    skill = _definition("write-skill", allows_write=True)
    plan = _plan(_registry(skill), (skill.id,), _policy(allow_write=True))
    assert plan.skills == (skill,)
    assert not marker.exists()


def test_empty_requires_is_allowed() -> None:
    """Spec: HERMES-0005 / AC-19"""
    skill = _definition("no-requires", requires=())
    plan = _plan(_registry(skill), (skill.id,), _policy())
    assert plan.skills == (skill,)


def test_all_requirements_available() -> None:
    """Spec: HERMES-0005 / AC-20"""
    skill = _definition("requires-skill", requires=("git", "pytest"))
    policy = _policy(available_requires=frozenset({"pytest", "git", "other"}))
    assert _plan(_registry(skill), (skill.id,), policy).skills == (skill,)


def test_unavailable_requirement_is_rejected() -> None:
    """Spec: HERMES-0005 / AC-21"""
    skill = _definition("requires-skill", requires=("git",))
    with _expect_error("SKILL_POLICY_REQUIREMENT_UNAVAILABLE") as caught:
        _plan(_registry(skill), (skill.id,), _policy())
    _assert_code(caught, "SKILL_POLICY_REQUIREMENT_UNAVAILABLE")
    assert "git" in str(caught.value)


def test_first_missing_requirement_follows_declared_order() -> None:
    """Spec: HERMES-0005 / AC-22"""
    skill = _definition(
        "requires-skill",
        requires=("available", "first-missing", "second-missing"),
    )
    policy = _policy(available_requires=frozenset({"available"}))
    with _expect_error("SKILL_POLICY_REQUIREMENT_UNAVAILABLE") as caught:
        _plan(_registry(skill), (skill.id,), policy)
    _assert_code(caught, "SKILL_POLICY_REQUIREMENT_UNAVAILABLE")
    assert "first-missing" in str(caught.value)
    assert "second-missing" not in str(caught.value)


def test_policy_failure_is_atomic() -> None:
    """Spec: HERMES-0005 / AC-23"""
    allowed = _definition("a-allowed")
    blocked = _definition("z-blocked", risk=SkillRisk.HIGH)
    result = object()
    with _expect_error("SKILL_POLICY_RISK_EXCEEDED") as caught:
        result = _plan(
            _registry(allowed, blocked),
            (allowed.id, blocked.id),
            _policy(max_risk=SkillRisk.LOW),
        )
    _assert_code(caught, "SKILL_POLICY_RISK_EXCEEDED")
    assert result.__class__ is object


def test_error_exposes_no_partial_plan() -> None:
    """Spec: HERMES-0005 / AC-24"""
    allowed = _definition("a-allowed")
    blocked = _definition("z-blocked", allows_write=True)
    with _expect_error("SKILL_POLICY_WRITE_NOT_ALLOWED") as caught:
        _plan(
            _registry(allowed, blocked),
            (allowed.id, blocked.id),
            _policy(allow_write=False),
        )
    _assert_code(caught, "SKILL_POLICY_WRITE_NOT_ALLOWED")
    assert not hasattr(caught.value, "plan")
    assert not hasattr(caught.value, "skills")
    assert not hasattr(caught.value, "registry")


def test_planning_never_executes_skill_content(tmp_path: Path) -> None:
    """Spec: HERMES-0005 / AC-25"""
    marker = tmp_path / "executed"
    payload = f'Path({str(marker)!r}).write_text("executed")'
    skill = _definition("passive-skill", body=payload)
    _plan(_registry(skill), (skill.id,), _policy())
    assert not marker.exists()


def test_planning_does_not_write_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec: HERMES-0005 / AC-26"""
    marker = tmp_path / "unchanged.txt"
    marker.write_bytes(b"unchanged")
    before = marker.read_bytes()
    api = _policy_api()
    skill = _definition("read-only-skill")
    policy = api.SkillPolicy(SkillRisk.LOW, False, frozenset())

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("planning attempted filesystem write")

    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "touch", forbidden)
    api.plan_skills(_registry(skill), (skill.id,), policy)
    assert marker.read_bytes() == before


def test_planning_does_not_modify_git(tmp_path: Path) -> None:
    """Spec: HERMES-0005 / AC-27"""
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "-b", "main")
    git(repository, "config", "user.name", "Hermes Policy Test")
    git(repository, "config", "user.email", "policy@invalid.local")
    tracked = repository / "tracked.txt"
    tracked.write_text("unchanged\n", encoding="utf-8")
    git(repository, "add", "tracked.txt")
    git(repository, "commit", "-m", "fixture")
    before_head = git(repository, "rev-parse", "HEAD").stdout
    before_status = git(repository, "status", "--porcelain=v1", "-z").stdout
    skill = _definition("git-safe-skill")
    _plan(_registry(skill), (skill.id,), _policy())
    assert git(repository, "rev-parse", "HEAD").stdout == before_head
    assert git(repository, "status", "--porcelain=v1", "-z").stdout == before_status
    assert tracked.read_text(encoding="utf-8") == "unchanged\n"


def test_policy_layer_does_not_create_processes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0005 / AC-28"""
    api = _policy_api()
    skill = _definition("process-free-skill")
    policy = api.SkillPolicy(SkillRisk.LOW, False, frozenset())

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("planning attempted to create a process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    plan = api.plan_skills(_registry(skill), (skill.id,), policy)
    assert plan.skills == (skill,)


def test_requirements_are_not_imported_or_executed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0005 / AC-29"""
    api = _policy_api()
    requirement = "hermes_requirement_that_must_remain_inert"
    skill = _definition("inert-requires", requires=(requirement,))
    policy = api.SkillPolicy(SkillRisk.LOW, False, frozenset({requirement}))
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object):
        if name == requirement:
            raise AssertionError("planning attempted to import a requirement")
        return original_import(name, *args, **kwargs)

    def forbidden_import_module(name: str, package: str | None = None):
        raise AssertionError(f"planning attempted dynamic import: {name}")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(importlib, "import_module", forbidden_import_module)
    plan = api.plan_skills(_registry(skill), (skill.id,), policy)
    assert plan.skills == (skill,)
    assert requirement not in sys.modules


def test_plan_skills_does_not_use_discovery_filesystem_or_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0005 / AC-30"""
    api = _policy_api()
    skill = _definition("pure-planning-skill")
    policy = api.SkillPolicy(SkillRisk.LOW, False, frozenset())

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("planning crossed into discovery, loader, or filesystem")

    monkeypatch.setattr(api, "discover_skills", forbidden)
    monkeypatch.setattr(api, "load_skill", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "iterdir", forbidden)
    plan = api.plan_skills(_registry(skill), (skill.id,), policy)
    assert plan.skills == (skill,)


def test_planning_integrates_with_real_skill_registry() -> None:
    """Spec: HERMES-0005 / AC-31"""
    selected = _definition("selected-skill")
    other = _definition("other-skill")
    registry = SkillRegistry((selected, other))
    plan = _plan(registry, (selected.id,), _policy())
    assert plan.skills == (registry.get_by_id(selected.id),)
    assert isinstance(plan.skills[0], SkillDefinition)


def test_public_api_has_no_generic_runner_execute_skill_or_pipeline() -> None:
    """Spec: HERMES-0005 / AC-32"""
    api = _policy_api()
    forbidden = {"runner", "execute_skill", "pipeline"}
    assert forbidden.isdisjoint(set(dir(api)))
    from hermes_ops.cli import build_parser

    assert "skills" not in build_parser().format_help().lower()


@pytest.mark.parametrize(
    ("max_risk", "allow_write", "available_requires"),
    [
        ("low", False, frozenset()),
        (SkillRisk.LOW, 0, frozenset()),
        (SkillRisk.LOW, 1, frozenset()),
        (SkillRisk.LOW, False, []),
        (SkillRisk.LOW, False, set()),
        (SkillRisk.LOW, False, ()),
        (SkillRisk.LOW, False, "git"),
        (SkillRisk.LOW, False, frozenset({1})),
        (SkillRisk.LOW, False, frozenset({""})),
        (SkillRisk.LOW, False, frozenset({"   "})),
        (SkillRisk.LOW, False, frozenset({" Git "})),
    ],
)
def test_invalid_skill_policy_values_are_rejected(
    max_risk: object,
    allow_write: object,
    available_requires: object,
) -> None:
    """Spec: HERMES-0005 / AC-33"""
    api = _policy_api()
    with pytest.raises(api.SkillPolicyError) as caught:
        api.SkillPolicy(max_risk, allow_write, available_requires)
    _assert_code(caught, "SKILL_POLICY_INVALID")


class _DuckRegistry:
    def get_by_id(self, skill_id: str) -> None:
        return None


@pytest.mark.parametrize("registry", [(), [], {}, None, _DuckRegistry()])
def test_invalid_registry_is_rejected(registry: object) -> None:
    """Spec: HERMES-0005 / AC-34"""
    with _expect_error("SKILL_PLAN_INVALID") as caught:
        _plan(registry, ("valid-id",), _policy())
    _assert_code(caught, "SKILL_PLAN_INVALID")


@pytest.mark.parametrize(
    "requested_ids",
    [[], {"valid-id"}, ["valid-id"], "valid-id", None, (1,)],
)
def test_invalid_requested_ids_structure_is_rejected(
    requested_ids: object,
) -> None:
    """Spec: HERMES-0005 / AC-35"""
    with _expect_error("SKILL_PLAN_REQUEST_INVALID") as caught:
        _plan(_registry(), requested_ids, _policy())
    _assert_code(caught, "SKILL_PLAN_REQUEST_INVALID")


@pytest.mark.parametrize(
    "skill_id",
    [
        "",
        "   ",
        " git-preflight",
        "git-preflight ",
        "Git-Preflight",
        "git_preflight",
        "git preflight",
        "-git",
        "git-",
        "../git",
        "skills/git",
    ],
)
def test_requested_id_must_match_contract_grammar(skill_id: str) -> None:
    """Spec: HERMES-0005 / AC-36"""
    with _expect_error("SKILL_PLAN_REQUEST_INVALID") as caught:
        _plan(_registry(), (skill_id,), _policy())
    _assert_code(caught, "SKILL_PLAN_REQUEST_INVALID")


@pytest.mark.parametrize("case", ["list", "empty", "invalid-policy"])
def test_direct_plan_rejects_invalid_container_empty_and_policy(case: str) -> None:
    """Spec: HERMES-0005 / AC-37"""
    api = _policy_api()
    skill = _definition("direct-skill")
    policy = _policy()
    skills: object = (skill,)
    if case == "list":
        skills = [skill]
    elif case == "empty":
        skills = ()
    elif case == "invalid-policy":
        policy = object()
    with pytest.raises(api.SkillPolicyError) as caught:
        api.SkillPlan(skills, policy)
    _assert_code(caught, "SKILL_PLAN_INVALID")


def test_direct_plan_rejects_non_skill_definition() -> None:
    """Spec: HERMES-0005 / AC-38"""
    api = _policy_api()
    with pytest.raises(api.SkillPolicyError) as caught:
        api.SkillPlan((object(),), _policy())
    _assert_code(caught, "SKILL_PLAN_INVALID")


def test_direct_plan_rejects_duplicate_ids_and_preserves_valid_order() -> None:
    """Spec: HERMES-0005 / AC-39"""
    api = _policy_api()
    first = _definition("duplicate-id")
    duplicate = _definition("duplicate-id", risk=SkillRisk.MEDIUM)
    with pytest.raises(api.SkillPolicyError) as caught:
        api.SkillPlan((first, duplicate), _policy(max_risk=SkillRisk.HIGH))
    _assert_code(caught, "SKILL_PLAN_INVALID")

    c = _definition("c")
    a = _definition("a")
    plan = api.SkillPlan((c, a), _policy())
    assert plan.skills == (c, a)


def test_missing_id_precedes_policy_failure() -> None:
    """Spec: HERMES-0005 / AC-40"""
    blocked = _definition("skill-a", risk=SkillRisk.HIGH)
    with _expect_error("SKILL_PLAN_SKILL_NOT_FOUND") as caught:
        _plan(
            _registry(blocked),
            (blocked.id, "missing-skill"),
            _policy(max_risk=SkillRisk.LOW),
        )
    _assert_code(caught, "SKILL_PLAN_SKILL_NOT_FOUND")


@pytest.mark.parametrize(
    ("skill", "policy", "expected_code"),
    [
        (
            _definition(
                "status-wins",
                status=SkillStatus.DEPRECATED,
                risk=SkillRisk.HIGH,
                allows_write=True,
                requires=("missing",),
            ),
            (SkillRisk.LOW, False, frozenset()),
            "SKILL_POLICY_STATUS_NOT_ACTIVE",
        ),
        (
            _definition(
                "risk-wins",
                risk=SkillRisk.HIGH,
                allows_write=True,
                requires=("missing",),
            ),
            (SkillRisk.MEDIUM, False, frozenset()),
            "SKILL_POLICY_RISK_EXCEEDED",
        ),
        (
            _definition(
                "write-wins",
                allows_write=True,
                requires=("missing",),
            ),
            (SkillRisk.LOW, False, frozenset()),
            "SKILL_POLICY_WRITE_NOT_ALLOWED",
        ),
    ],
)
def test_intra_skill_error_precedence(
    skill: SkillDefinition,
    policy: tuple[SkillRisk, bool, frozenset[str]],
    expected_code: str,
) -> None:
    """Spec: HERMES-0005 / AC-41"""
    max_risk, allow_write, available = policy
    with _expect_error(expected_code) as caught:
        _plan(
            _registry(skill),
            (skill.id,),
            _policy(
                max_risk=max_risk,
                allow_write=allow_write,
                available_requires=available,
            ),
        )
    _assert_code(caught, expected_code)


@pytest.mark.parametrize(
    "case",
    ["registry-before-policy", "policy-before-request", "syntax-before-duplicate"],
)
def test_cross_phase_error_precedence(case: str) -> None:
    """Spec: HERMES-0005 / AC-42"""
    api = _policy_api()
    registry: object = _registry()
    policy: object = _policy()
    requested: object = ("valid-id",)
    expected = ""
    if case == "registry-before-policy":
        registry = object()
        policy = object()
        requested = []
        expected = "SKILL_PLAN_INVALID"
    elif case == "policy-before-request":
        policy = object()
        requested = []
        expected = "SKILL_POLICY_INVALID"
    elif case == "syntax-before-duplicate":
        requested = ("same-id", "same-id", "INVALID")
        expected = "SKILL_PLAN_REQUEST_INVALID"
    with pytest.raises(api.SkillPolicyError) as caught:
        api.plan_skills(registry, requested, policy)
    _assert_code(caught, expected)


def test_planning_is_deterministic() -> None:
    """Spec: HERMES-0005 / AC-43"""
    first = _definition("first-skill")
    second = _definition("second-skill")
    registry = _registry(second, first)
    policy = _policy()
    plans = [
        _plan(registry, (second.id, first.id), policy),
        _plan(registry, (second.id, first.id), policy),
    ]
    assert plans[0] == plans[1]
    assert tuple(skill.id for skill in plans[0].skills) == (
        "second-skill",
        "first-skill",
    )

    messages: list[tuple[str | None, str]] = []
    for _ in range(2):
        with _expect_error("SKILL_PLAN_SKILL_NOT_FOUND") as caught:
            _plan(registry, ("missing-skill",), policy)
        messages.append((_error_code(caught.value), str(caught.value)))
    assert messages[0] == messages[1]
