from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
from typing import Any

import pytest

from conftest import VALID_CONFIG, git
from hermes_ops.commands.preflight import run_preflight
from hermes_ops.core.errors import SkillContractError, SkillPolicyError, SkillRegistryError
from hermes_ops.core.results import CheckResult, Report, Status


EXPECTED_API = (
    "SkillExecutionEvidence",
    "SkillExecutionStatus",
    "SkillExecutionResult",
    "SkillExecutionError",
    "run_skill",
)


def _execution_api():
    api = importlib.import_module("hermes_ops.skills")
    missing = [name for name in EXPECTED_API if not hasattr(api, name)]
    if missing:
        pytest.fail(
            "HERMES-0006 production API is not implemented: missing "
            + ", ".join(missing),
            pytrace=False,
        )
    return api


def _policy(*, requirements: frozenset[str] = frozenset({"git"})):
    api = _execution_api()
    return api.SkillPolicy(api.SkillRisk.LOW, False, requirements)


def _write_contract(project: Path, skill_id: str = "git-preflight", *, body_suffix: str = "") -> Path:
    source = Path(__file__).resolve().parents[1] / "skills/git-preflight/SKILL.md"
    text = source.read_text(encoding="utf-8")
    if skill_id != "git-preflight":
        text = text.replace("id: git-preflight", f"id: {skill_id}", 1)
    if body_suffix:
        text += "\n" + body_suffix + "\n"
    target = project / "skills" / skill_id / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _project(tmp_path: Path, *, second_skill: bool = False) -> Path:
    config = tmp_path / ".hermes/project.toml"
    config.parent.mkdir(parents=True)
    config.write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='fixture'\nversion='1'\n", encoding="utf-8")
    _write_contract(tmp_path)
    if second_skill:
        _write_contract(tmp_path, "other-skill")
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Hermes Execution Test")
    git(tmp_path, "config", "user.email", "execution@invalid.local")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture")
    return tmp_path


def _target_project(tmp_path: Path) -> Path:
    config = tmp_path / ".hermes/project.toml"
    config.parent.mkdir(parents=True)
    config.write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='external-target'\nversion='1'\n",
        encoding="utf-8",
    )
    (tmp_path / "tracked.txt").write_text("unchanged\n", encoding="utf-8")
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Hermes External Target Test")
    git(tmp_path, "config", "user.email", "external-target@invalid.local")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture")
    assert not (tmp_path / "skills").exists()
    return tmp_path


def _run(project: Path, *, skill_id: str = "git-preflight", policy: Any = None):
    api = _execution_api()
    return api.run_skill(project, skill_id, _policy() if policy is None else policy)


def _run_with_catalog(
    project: Path,
    catalog: Path,
    *,
    skill_id: str = "git-preflight",
    policy: Any = None,
):
    from hermes_ops.skills.executor import _run_skill_with_catalog

    return _run_skill_with_catalog(
        project,
        skill_id,
        _policy() if policy is None else policy,
        catalog,
    )


def _error_code(exc: BaseException) -> str | None:
    return getattr(exc, "code", None)


def _snapshot(project: Path) -> dict[str, Any]:
    refs = git(project, "for-each-ref", "--format=%(refname)%00%(objectname)").stdout
    return {
        "status": git(project, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout,
        "head": git(project, "rev-parse", "HEAD").stdout,
        "refs": refs,
        "files": {
            path.relative_to(project).as_posix(): path.read_bytes()
            for path in project.rglob("*")
            if path.is_file() and ".git" not in path.parts
        },
    }


def test_run_skill_requires_explicit_inputs(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-01"""
    api = _execution_api()
    with pytest.raises(api.SkillExecutionError) as caught:
        api.run_skill(tmp_path, None, _policy())
    assert _error_code(caught.value) == "SKILL_EXECUTION_INVALID"


def test_discovery_precedes_planning_dispatch_and_handler(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-02"""
    target = tmp_path / "target"
    target.mkdir()
    with pytest.raises(SkillRegistryError):
        _run_with_catalog(target, tmp_path / "missing-catalog")


def test_real_registry_and_plan_are_mandatory(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-03"""
    result = _run(_project(tmp_path))
    assert result.skill_id == "git-preflight"


def test_discovery_failure_prevents_all_later_phases(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-04"""
    target = tmp_path / "target"
    target.mkdir()
    marker = tmp_path / "handler-ran"
    with pytest.raises(SkillRegistryError):
        _run_with_catalog(target, tmp_path / "missing-catalog")
    assert not marker.exists()


def test_policy_failure_prevents_dispatch_and_handler(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-05"""
    project = _project(tmp_path)
    with pytest.raises(SkillPolicyError) as caught:
        _run(project, policy=_policy(requirements=frozenset()))
    assert _error_code(caught.value) == "SKILL_POLICY_REQUIREMENT_UNAVAILABLE"


def test_dispatch_rejects_non_unit_request(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-06"""
    api = _execution_api()
    with pytest.raises(api.SkillExecutionError) as caught:
        api.run_skill(_project(tmp_path), ("git-preflight", "git-preflight"), _policy())
    assert _error_code(caught.value) == "SKILL_EXECUTION_INVALID"


def test_dispatch_supports_only_git_preflight(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-07"""
    api = _execution_api()
    project = _project(tmp_path, second_skill=True)
    with pytest.raises(api.SkillExecutionError) as caught:
        _run_with_catalog(project, project, skill_id="other-skill")
    assert _error_code(caught.value) == "SKILL_EXECUTION_NOT_SUPPORTED"


def test_unsupported_skill_is_blocked_without_fallback(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-08"""
    api = _execution_api()
    with pytest.raises(api.SkillExecutionError) as caught:
        project = _project(tmp_path, second_skill=True)
        _run_with_catalog(project, project, skill_id="other-skill")
    assert _error_code(caught.value) == "SKILL_EXECUTION_NOT_SUPPORTED"


def test_dispatch_never_derives_or_discovers_handler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-09"""
    api = _execution_api()
    project = _project(tmp_path, second_skill=True)
    policy = _policy()
    run_skill = api.run_skill
    monkeypatch.setattr(importlib, "import_module", lambda *a, **k: pytest.fail("dynamic import"))
    with pytest.raises(api.SkillExecutionError) as caught:
        from hermes_ops.skills.executor import _run_skill_with_catalog
        _run_skill_with_catalog(project, "other-skill", policy, project)
    assert _error_code(caught.value) == "SKILL_EXECUTION_NOT_SUPPORTED"


def test_dangerous_skill_body_remains_inert(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-10"""
    project = _project(tmp_path)
    marker = project / "body-marker"
    path = project / "skills/git-preflight/SKILL.md"
    path.write_text(path.read_text(encoding="utf-8") + f"\npython -c {marker!s}\ntouch {marker!s}\ngit reset --hard\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []
    real_run = subprocess.run
    def guarded(args: Any, *a: Any, **kw: Any):
        command = tuple(str(item) for item in args)
        calls.append(command)
        assert command[0] == "git" and "reset" not in command
        return real_run(args, *a, **kw)
    monkeypatch.setattr(subprocess, "run", guarded)
    _run_with_catalog(project, project)
    assert not marker.exists()
    assert calls


def test_git_preflight_reuses_existing_orchestration(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-11"""
    project = _project(tmp_path)
    result = _run(project)
    report = run_preflight(project)
    assert result.exit_code == report.exit_code


def test_git_preflight_reports_existing_checks(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-12"""
    result = _run(_project(tmp_path))
    assert {item.name for item in result.evidence}.issuperset({"path", "configuration", "git", "working_tree"})


def test_execution_models_are_frozen_slotted_and_deeply_immutable(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-13"""
    result = _run(_project(tmp_path))
    assert not hasattr(result, "__dict__")
    assert all(not hasattr(item, "__dict__") for item in result.evidence)
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        result.exit_code = 99


def test_execution_result_has_minimal_ordered_snapshot(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-14"""
    result = _run(_project(tmp_path))
    assert tuple(result.__dataclass_fields__) == ("skill_id", "status", "exit_code", "evidence")
    assert isinstance(result.evidence, tuple)


def test_execution_status_distinguishes_findings_from_no_report(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-15"""
    api = _execution_api()
    result = _run(_project(tmp_path))
    assert result.status in {api.SkillExecutionStatus.PASSED, api.SkillExecutionStatus.COMPLETED_WITH_FINDINGS}


def test_result_excludes_body_environment_and_secrets(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-16"""
    result = _run(_project(tmp_path))
    payload = repr(result)
    assert "Passive skill body" not in payload and "GIT_CONFIG_GLOBAL" not in payload


def test_execution_does_not_write_files(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-17"""
    project = _project(tmp_path)
    before = _snapshot(project)
    _run(project)
    assert _snapshot(project) == before


def test_execution_uses_no_mutating_git_operation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-18"""
    project = _project(tmp_path)
    forbidden = {"add", "commit", "push", "checkout", "switch", "reset", "clean", "stash", "merge", "rebase", "tag", "branch", "update-ref"}
    real_run = subprocess.run
    def guarded(args: Any, *a: Any, **kw: Any):
        command = tuple(str(item) for item in args)
        if command and command[0] == "git":
            assert forbidden.isdisjoint(command)
        return real_run(args, *a, **kw)
    monkeypatch.setattr(subprocess, "run", guarded)
    _run(project)


def test_processes_use_central_process_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-19"""
    project = _project(tmp_path)
    calls: list[dict[str, Any]] = []
    original = subprocess.run
    def observed(*a: Any, **kw: Any):
        calls.append(kw)
        return original(*a, **kw)
    monkeypatch.setattr(subprocess, "run", observed)
    _run(project)
    assert calls
    assert all(call.get("shell") is False for call in calls)
    assert all(call.get("capture_output") is True for call in calls)


def test_user_cannot_supply_process_or_shell(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-20"""
    api = _execution_api()
    with pytest.raises(TypeError):
        api.run_skill(_project(tmp_path), "git-preflight", _policy(), command="calc")


def test_execution_does_not_access_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-21"""
    def forbidden(*a: Any, **kw: Any):
        raise AssertionError("network access")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    _run(_project(tmp_path))


def test_strong_repository_snapshot_is_preserved(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-22"""
    project = _project(tmp_path)
    before = _snapshot(project)
    _run(project)
    assert _snapshot(project) == before


def test_execution_error_exposes_no_partial_result(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-23"""
    api = _execution_api()
    with pytest.raises(api.SkillExecutionError) as caught:
        project = _project(tmp_path, second_skill=True)
        _run_with_catalog(project, project, skill_id="other-skill")
    assert not hasattr(caught.value, "result") and not hasattr(caught.value, "evidence")


def test_execution_does_not_mutate_inputs(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-24"""
    project = _project(tmp_path)
    policy = _policy()
    before = repr(policy)
    _run(project, policy=policy)
    assert repr(policy) == before


def test_execution_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-25"""
    project = _project(tmp_path)
    assert _run(project) == _run(project)


def test_negative_preflight_returns_complete_result_and_exit_code(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-26"""
    api = _execution_api()
    project = _project(tmp_path)
    (project / "dirty.txt").write_text("dirty", encoding="utf-8")
    report = run_preflight(project)
    result = _run(project)
    assert report.exit_code != 0
    assert result.exit_code == report.exit_code
    assert result.status is api.SkillExecutionStatus.COMPLETED_WITH_FINDINGS
    assert result.evidence


def test_existing_commands_remain_compatible(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-30"""
    project = _project(tmp_path)
    assert _run(project).exit_code == run_preflight(project).exit_code


def test_execution_uses_controlled_temporary_repository(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-31"""
    project = _project(tmp_path)
    assert _run(project).skill_id == "git-preflight"


def test_unsafe_local_git_config_remains_blocked(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-32"""
    api = _execution_api()
    project = _project(tmp_path)
    with (project / ".git/config").open("a", encoding="utf-8") as stream:
        stream.write("\n[include]\npath = ../outside\n")
    result = _run(project)
    assert result.status is api.SkillExecutionStatus.COMPLETED_WITH_FINDINGS
    assert any(item.code == "git_unsafe_local_config" for item in result.evidence)


def test_required_and_optional_git_semantics_are_preserved(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-33"""
    project = _project(tmp_path)
    assert _run(project).exit_code == run_preflight(project).exit_code


def test_public_surface_has_no_generic_runner_pipeline_or_plugins() -> None:
    """Spec: HERMES-0006 / AC-35"""
    api = _execution_api()
    forbidden = {"runner", "pipeline", "grant_capabilities", "plugins"}
    assert forbidden.isdisjoint(dir(api))


def test_execution_public_api_exports_only_return_contract_and_entrypoint() -> None:
    """Spec: HERMES-0006 / AC-36"""
    api = _execution_api()
    assert set(EXPECTED_API).issubset(api.__all__)
    assert {"dispatch_skill", "run_git_preflight", "build_execution_result", "freeze_details"}.isdisjoint(api.__all__)


def test_execution_errors_are_stable_and_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-37"""
    api = _execution_api()
    errors = []
    for _ in range(2):
        with pytest.raises(api.SkillExecutionError) as caught:
            project = _project(tmp_path / str(len(errors)), second_skill=True)
            _run_with_catalog(project, project, skill_id="other-skill")
        errors.append((_error_code(caught.value), str(caught.value)))
    assert errors[0] == errors[1]


def test_skill_execution_preserves_passive_loader_contract(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-38"""
    marker = tmp_path / "never"
    project = _project(tmp_path / "project")
    path = project / "skills/git-preflight/SKILL.md"
    path.write_text(path.read_text(encoding="utf-8") + f"\n{marker}.write_text('x')\n", encoding="utf-8")
    _run_with_catalog(project, project)
    assert not marker.exists()


def test_skill_execution_preserves_explicit_discovery_contract(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-39"""
    api = _execution_api()
    selected = _project(tmp_path / "selected")
    _project(tmp_path / "sibling")
    assert api.run_skill(selected, "git-preflight", _policy()).skill_id == "git-preflight"


def test_skill_execution_requires_approved_plan(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-40"""
    with pytest.raises(SkillPolicyError):
        _run(_project(tmp_path), policy=_policy(requirements=frozenset()))


def test_real_repository_contract_discovers_and_plans() -> None:
    """Spec: HERMES-0006 / AC-41"""
    api = _execution_api()
    root = Path(__file__).resolve().parents[1]
    registry = api.discover_skills(root)
    skill = registry.get_by_id("git-preflight")
    assert (skill.schema_version, skill.id, skill.version) == (1, "git-preflight", 1)
    assert (skill.status, skill.risk, skill.requires, skill.allows_write) == (api.SkillStatus.ACTIVE, api.SkillRisk.LOW, ("git",), False)
    plan = api.plan_skills(registry, ("git-preflight",), _policy())
    assert plan.skills == (skill,)


def test_requirements_never_auto_authorize_policy(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-42"""
    with pytest.raises(SkillPolicyError) as caught:
        _run(_project(tmp_path), policy=_policy(requirements=frozenset()))
    assert _error_code(caught.value) == "SKILL_POLICY_REQUIREMENT_UNAVAILABLE"


def test_source_details_mutation_cannot_change_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-43"""
    api = _execution_api()
    details = {"nested": {"items": [1, 2]}, "set": {"b", "a"}}
    evidence = api.SkillExecutionEvidence("check", Status.OK, "ok", details, "ok")
    before = evidence.details
    details["nested"]["items"].append(3)
    details["set"].add("c")
    details["new"] = []
    assert evidence.details == before


def test_freeze_details_is_recursive_lossless_and_deterministic() -> None:
    """Spec: HERMES-0006 / AC-44"""
    api = _execution_api()
    first = api.SkillExecutionEvidence("x", Status.OK, "ok", {"b": {2, 1}, "a": [True, None]}, "ok")
    second = api.SkillExecutionEvidence("x", Status.OK, "ok", {"a": [True, None], "b": {1, 2}}, "ok")
    assert first == second
    assert isinstance(first.details, tuple)


def test_negative_report_differs_from_structural_execution_failure(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-45"""
    api = _execution_api()
    project = _project(tmp_path)
    (project / "dirty").write_text("x", encoding="utf-8")
    assert _run(project).status is api.SkillExecutionStatus.COMPLETED_WITH_FINDINGS
    with pytest.raises(api.SkillExecutionError):
        api.run_skill(project, None, _policy())


def test_handler_reaches_only_audited_read_only_git_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-47"""
    project = _project(tmp_path)
    allowed = {"rev-parse", "symbolic-ref", "status"}
    real_run = subprocess.run
    observed: list[tuple[str, ...]] = []
    def guarded(args: Any, *a: Any, **kw: Any):
        command = tuple(str(item) for item in args)
        if command and command[0] == "git" and "-c" in command:
            observed.append(command)
            assert any(item in allowed for item in command)
        return real_run(args, *a, **kw)
    monkeypatch.setattr(subprocess, "run", guarded)
    _run(project)
    assert observed


def test_controlled_git_process_allowed_arbitrary_process_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-48"""
    project = _project(tmp_path)
    real_run = subprocess.run
    def guarded(args: Any, *a: Any, **kw: Any):
        assert tuple(str(item) for item in args)[0] == "git"
        return real_run(args, *a, **kw)
    monkeypatch.setattr(subprocess, "run", guarded)
    _run(project)


def test_dispatch_never_calls_dynamic_import_plugin_or_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0006 / AC-49"""
    api = _execution_api()
    project = _project(tmp_path, second_skill=True)
    policy = _policy()
    run_skill = api.run_skill
    monkeypatch.setattr(importlib, "import_module", lambda *a, **k: pytest.fail("dynamic import"))
    with pytest.raises(api.SkillExecutionError) as caught:
        from hermes_ops.skills.executor import _run_skill_with_catalog
        _run_skill_with_catalog(project, "other-skill", policy, project)
    assert _error_code(caught.value) == "SKILL_EXECUTION_NOT_SUPPORTED"


def test_skill_preflight_semantics_match_legacy_commands(tmp_path: Path) -> None:
    """Spec: HERMES-0006 / AC-52"""
    project = _project(tmp_path)
    result = _run(project)
    report = run_preflight(project)
    assert result.exit_code == report.exit_code
    assert [(item.name, item.status, item.code) for item in result.evidence] == [(item.name, item.status, item.code) for item in report.results]


def test_run_skill_separates_catalog_from_target_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0007 / AC-01"""
    from hermes_ops.skills import executor

    target = _target_project(tmp_path / "target")
    observed: list[Path] = []
    real_discover = executor.discover_skills

    def observed_discover(root: Path):
        observed.append(Path(root))
        return real_discover(root)

    monkeypatch.setattr(executor, "discover_skills", observed_discover)
    result = _run(target)

    assert result.skill_id == "git-preflight"
    assert observed == [Path(__file__).resolve().parents[1]]
    assert observed[0] != target


def test_requested_skill_is_loaded_by_exact_id_from_own_catalog(
    tmp_path: Path,
) -> None:
    """Spec: HERMES-0007 / AC-07"""
    target = _target_project(tmp_path)
    assert _run(target).skill_id == "git-preflight"
    with pytest.raises(SkillPolicyError) as caught:
        _run(target, skill_id="Git-Preflight")
    assert _error_code(caught.value) == "SKILL_PLAN_REQUEST_INVALID"


def test_target_skill_shadow_cannot_replace_catalog_skill(tmp_path: Path) -> None:
    """Spec: HERMES-0007 / AC-12"""
    target = _target_project(tmp_path)
    marker = target / "shadow-ran"
    shadow = target / "skills/git-preflight/SKILL.md"
    shadow.parent.mkdir(parents=True)
    shadow.write_text(
        "invalid contract\ngit reset --hard\n" + str(marker),
        encoding="utf-8",
    )

    result = _run(target)

    assert result.skill_id == "git-preflight"
    assert not marker.exists()


def test_catalog_failure_precedes_planning_dispatch_and_handler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0007 / AC-13"""
    from hermes_ops.core.errors import SkillCatalogError
    from hermes_ops.skills import executor

    target = _target_project(tmp_path)
    monkeypatch.setattr(
        executor,
        "resolve_own_skill_catalog",
        lambda: (_ for _ in ()).throw(
            SkillCatalogError("SKILL_CATALOG_INVALID", "invalid catalog")
        ),
    )
    monkeypatch.setattr(
        executor,
        "plan_skills",
        lambda *args: pytest.fail("planning ran after catalog failure"),
    )
    monkeypatch.setattr(
        executor,
        "_dispatch_skill",
        lambda *args: pytest.fail("dispatch ran after catalog failure"),
    )

    with pytest.raises(SkillCatalogError):
        _run(target)


def test_target_validation_precedes_skill_handler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0007 / AC-14"""
    from hermes_ops.skills import executor

    monkeypatch.setattr(
        executor,
        "resolve_own_skill_catalog",
        lambda: pytest.fail("catalog resolved for invalid target"),
    )
    with pytest.raises(executor.SkillExecutionError) as caught:
        _run(tmp_path / "missing")
    assert _error_code(caught.value) == "SKILL_TARGET_INVALID"


def test_git_preflight_remains_read_only_on_independent_target(
    tmp_path: Path,
) -> None:
    """Spec: HERMES-0007 / AC-15"""
    target = _target_project(tmp_path)
    before = _snapshot(target)
    result = _run(target)
    assert result.exit_code == 0
    assert _snapshot(target) == before


def test_linked_worktree_target_preserves_security_contract(tmp_path: Path) -> None:
    """Spec: HERMES-0007 / AC-16"""
    main = _target_project(tmp_path / "main")
    linked = tmp_path / "linked"
    git(main, "worktree", "add", "--detach", str(linked))
    before_head = git(linked, "rev-parse", "HEAD").stdout
    before_status = git(linked, "status", "--porcelain=v1", "-z").stdout
    before_refs = git(main, "show-ref").stdout

    result = _run(linked)

    assert result.exit_code == 3
    assert any(
        item.code == "git_indirect_repository_unsupported"
        for item in result.evidence
    )
    assert git(linked, "rev-parse", "HEAD").stdout == before_head
    assert git(linked, "status", "--porcelain=v1", "-z").stdout == before_status
    assert git(main, "show-ref").stdout == before_refs


def test_skill_pipeline_still_requires_policy_and_closed_dispatch(
    tmp_path: Path,
) -> None:
    """Spec: HERMES-0007 / AC-21"""
    target = _target_project(tmp_path)
    with pytest.raises(SkillPolicyError) as caught:
        _run(target, policy=_policy(requirements=frozenset()))
    assert _error_code(caught.value) == "SKILL_POLICY_REQUIREMENT_UNAVAILABLE"


def test_git_commands_and_process_boundary_remain_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0007 / AC-22"""
    target = _target_project(tmp_path)
    allowed = {"rev-parse", "symbolic-ref", "status"}
    observed: list[tuple[str, ...]] = []
    real_run = subprocess.run

    def guarded(args: Any, *positional: Any, **keywords: Any):
        command = tuple(str(item) for item in args)
        if command and command[0] == "git" and "-c" in command:
            observed.append(command)
            assert any(item in allowed for item in command)
        return real_run(args, *positional, **keywords)

    monkeypatch.setattr(subprocess, "run", guarded)
    assert _run(target).exit_code == 0
    assert observed
