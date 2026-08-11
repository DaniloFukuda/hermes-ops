from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import git
from hermes_ops.skills import load_skill
from hermes_ops.skills.models import SkillDefinition, SkillRisk, SkillStatus


REQUIRED_SECTIONS = (
    "Objetivo",
    "Entradas",
    "Pré-condições",
    "Procedimento",
    "Saídas",
    "Falhas",
    "Restrições",
    "Evidências",
    "Pós-condições",
)


def _body(*, procedure: str = "Texto passivo.") -> str:
    contents = {
        section: procedure if section == "Procedimento" else f"Texto de {section}."
        for section in REQUIRED_SECTIONS
    }
    return "\n# Example Skill\n\n" + "\n\n".join(
        f"## {section}\n\n{contents[section]}" for section in REQUIRED_SECTIONS
    ) + "\n"


def _write_skill(
    project: Path,
    skill_id: str,
    *,
    version: str = "1",
    requires: tuple[str, ...] = (),
    allows_write: str = "false",
    body: str | None = None,
) -> Path:
    directory = project / "skills" / skill_id
    directory.mkdir(parents=True, exist_ok=True)
    requires_lines = ["requires: []"] if not requires else [
        "requires:",
        *(f"  - {item}" for item in requires),
    ]
    metadata = [
        "schema_version: 1",
        f"id: {skill_id}",
        f"version: {version}",
        "status: active",
        f"description: Contract for {skill_id}",
        "risk: low",
        *requires_lines,
        f"allows_write: {allows_write}",
    ]
    path = directory / "SKILL.md"
    document = "---\n" + "\n".join(metadata) + "\n---\n" + (
        _body() if body is None else body
    )
    path.write_bytes(document.encode("utf-8"))
    return path


def _registry_api():
    module = importlib.import_module("hermes_ops.skills")
    missing = [
        name
        for name in ("discover_skills", "SkillRegistry")
        if not hasattr(module, name)
    ]
    if missing:
        pytest.fail(
            "HERMES-0004 production API is not implemented: missing "
            + ", ".join(missing),
            pytrace=False,
        )
    return module


def _discover(project: Path):
    return _registry_api().discover_skills(project)


def _error_code(exc: BaseException) -> str | None:
    return getattr(exc, "code", None)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }


def _definition(skill_id: str, path: Path) -> SkillDefinition:
    return SkillDefinition(
        schema_version=1,
        id=skill_id,
        version=1,
        status=SkillStatus.ACTIVE,
        description=f"Definition for {skill_id}",
        risk=SkillRisk.LOW,
        requires=(),
        allows_write=False,
        path=path,
        body=_body(),
    )


def _make_symlink(link: Path, target: Path, *, directory: bool) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlink fixture is unavailable: {exc}")


def _make_junction(link: Path, target: Path) -> None:
    if sys.platform != "win32":
        pytest.skip("Directory junction fixture is Windows-specific")
    completed = subprocess.run(
        ("cmd", "/c", "mklink", "/J", str(link), str(target)),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        pytest.skip("Directory junction fixture is unavailable")


def test_discovery_uses_only_explicit_project_root(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-01"""
    selected = tmp_path / "selected"
    _write_skill(selected, "selected-skill")
    _write_skill(tmp_path, "parent-skill")
    _write_skill(tmp_path / "sibling", "sibling-skill")

    registry = _discover(selected)

    assert tuple(skill.id for skill in registry.skills) == ("selected-skill",)


def test_empty_skills_directory_returns_empty_registry(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-02"""
    (tmp_path / "skills").mkdir()
    registry = _discover(tmp_path)
    assert registry.skills == ()
    assert isinstance(registry.skills, tuple)


def test_missing_skills_directory_is_explicit_error(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-03"""
    before = _snapshot(tmp_path)
    with pytest.raises(Exception) as caught:
        _discover(tmp_path)
    assert _error_code(caught.value) == "SKILL_ROOT_NOT_FOUND"
    assert _snapshot(tmp_path) == before


def test_discovery_uses_real_load_skill(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-04"""
    path = _write_skill(tmp_path, "real-loader")
    registry = _discover(tmp_path)
    assert registry.get_by_id("real-loader") == load_skill(path)
    assert isinstance(registry.skills[0], SkillDefinition)


def test_equivalent_trees_with_different_creation_order_match(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-05"""
    first = tmp_path / "first"
    second = tmp_path / "second"
    for skill_id in ("skill-c", "skill-a", "skill-b"):
        _write_skill(first, skill_id)
    for skill_id in ("skill-b", "skill-a", "skill-c"):
        _write_skill(second, skill_id)

    first_ids = tuple(skill.id for skill in _discover(first).skills)
    second_ids = tuple(skill.id for skill in _discover(second).skills)

    assert first_ids == second_ids == ("skill-a", "skill-b", "skill-c")


def test_get_by_id_returns_exact_skill(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-06"""
    _write_skill(tmp_path, "exact-skill")
    registry = _discover(tmp_path)
    assert registry.get_by_id("exact-skill") is registry.skills[0]


def test_get_by_id_returns_none_for_unknown_id(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-07"""
    _write_skill(tmp_path, "known-skill")
    registry = _discover(tmp_path)
    before = registry.skills
    assert registry.get_by_id("unknown-skill") is None
    assert registry.skills is before


def test_loose_file_aborts_discovery(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-08"""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "loose.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(Exception) as caught:
        _discover(tmp_path)
    assert _error_code(caught.value) == "SKILL_CANDIDATE_INVALID"


def test_candidate_without_contract_aborts_discovery(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-09"""
    (tmp_path / "skills" / "missing-contract").mkdir(parents=True)
    with pytest.raises(Exception) as caught:
        _discover(tmp_path)
    assert _error_code(caught.value) == "SKILL_CANDIDATE_MISSING_CONTRACT"


@pytest.mark.parametrize("name", [".hidden", "Upper", "trailing-"])
def test_hidden_or_invalid_candidate_name_is_blocked(
    tmp_path: Path, name: str
) -> None:
    """Spec: HERMES-0004 / AC-10"""
    (tmp_path / "skills" / name).mkdir(parents=True)
    with pytest.raises(Exception) as caught:
        _discover(tmp_path)
    assert _error_code(caught.value) == "SKILL_CANDIDATE_INVALID"


def test_discovery_never_recurses_for_contracts(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-11"""
    nested_project = tmp_path / "nested-fixture"
    nested = nested_project / "skills" / "outer-skill" / "inner-skill"
    nested.mkdir(parents=True)
    source = _write_skill(tmp_path / "source", "inner-skill")
    (nested / "SKILL.md").write_bytes(source.read_bytes())
    with pytest.raises(Exception) as caught:
        _discover(nested_project)
    assert _error_code(caught.value) == "SKILL_CANDIDATE_MISSING_CONTRACT"


def test_later_invalid_skill_exposes_no_partial_registry(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-12"""
    _write_skill(tmp_path, "a-valid")
    _write_skill(tmp_path, "z-invalid", version="0")
    result = object()
    with pytest.raises(Exception) as caught:
        result = _discover(tmp_path)
    assert _error_code(caught.value) == "SKILL_INVALID_VERSION"
    assert result.__class__ is object
    assert not hasattr(caught.value, "registry")
    assert not hasattr(caught.value, "skills")


def test_registry_constructor_rejects_duplicate_id(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-13"""
    registry_type = _registry_api().SkillRegistry
    first = _definition("duplicate-id", tmp_path / "first/SKILL.md")
    second = _definition("duplicate-id", tmp_path / "second/SKILL.md")
    with pytest.raises(Exception) as caught:
        registry_type((first, second))
    assert _error_code(caught.value) == "SKILL_REGISTRY_DUPLICATE_ID"


@pytest.mark.parametrize(
    ("fixture_type", "level"),
    [
        ("symlink", "project_root"),
        ("symlink", "skills_root"),
        ("symlink", "candidate"),
        ("symlink", "skill_file"),
        ("junction", "project_root"),
        ("junction", "skills_root"),
        ("junction", "candidate"),
    ],
)
def test_indirect_protected_paths_are_blocked(
    tmp_path: Path, fixture_type: str, level: str
) -> None:
    """Spec: HERMES-0004 / AC-14"""
    real = tmp_path / "real"
    _write_skill(real, "example-skill")
    link = tmp_path / "declared"

    if level == "project_root":
        target, indirect, project = real, link, link
    elif level == "skills_root":
        project = tmp_path / "declared-project"
        project.mkdir()
        target, indirect = real / "skills", project / "skills"
    elif level == "candidate":
        project = tmp_path / "declared-project"
        (project / "skills").mkdir(parents=True)
        target = real / "skills" / "example-skill"
        indirect = project / "skills" / "example-skill"
    else:
        if fixture_type != "symlink":
            pytest.skip("File junctions are not applicable")
        project = tmp_path / "declared-project"
        candidate = project / "skills" / "example-skill"
        candidate.mkdir(parents=True)
        target = real / "skills" / "example-skill" / "SKILL.md"
        indirect = candidate / "SKILL.md"

    if fixture_type == "junction":
        _make_junction(indirect, target)
    else:
        _make_symlink(indirect, target, directory=level != "skill_file")

    with pytest.raises(Exception) as caught:
        _discover(project)
    assert _error_code(caught.value) == "SKILL_DISCOVERY_INDIRECT_PATH"


def test_indirect_project_root_ancestor_is_blocked(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-15"""
    real_anchor = tmp_path / "real-anchor"
    project = real_anchor / "project"
    _write_skill(project, "example-skill")
    indirect_anchor = tmp_path / "indirect-anchor"
    _make_symlink(indirect_anchor, real_anchor, directory=True)
    declared_project = indirect_anchor / "project"
    with pytest.raises(Exception) as caught:
        _discover(declared_project)
    assert _error_code(caught.value) == "SKILL_DISCOVERY_INDIRECT_PATH"


def test_inspection_failure_is_controlled(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-16"""
    if os.name == "nt":
        pytest.skip("Portable permission-denied directory fixture is unavailable")
    skills = tmp_path / "skills"
    skills.mkdir()
    skills.chmod(0)
    try:
        with pytest.raises(Exception) as caught:
            _discover(tmp_path)
        assert _error_code(caught.value) == "SKILL_DISCOVERY_READ_FAILED"
    finally:
        skills.chmod(0o700)


def test_registry_is_immutable(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-17"""
    _write_skill(tmp_path, "immutable-skill")
    registry = _discover(tmp_path)
    assert isinstance(registry.skills, tuple)
    assert isinstance(registry.skills[0], SkillDefinition)
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        registry.skills += (_definition("other", tmp_path / "other"),)


def test_discovery_never_executes_content(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-18"""
    marker = tmp_path / "must-not-exist"
    payload = f'Path({str(marker)!r}).write_text("executed")'
    _write_skill(tmp_path, "passive-skill", body=_body(procedure=payload))
    _discover(tmp_path)
    assert not marker.exists()


def test_requires_remains_inert(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-19"""
    dependency = "hermes_dependency_that_must_not_be_imported"
    _write_skill(tmp_path, "requires-skill", requires=(dependency,))
    registry = _discover(tmp_path)
    assert registry.skills[0].requires == (dependency,)
    assert dependency not in sys.modules


def test_allows_write_remains_declarative(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-20"""
    before = _snapshot(tmp_path)
    _write_skill(tmp_path, "write-declaration", allows_write="true")
    before_discovery = _snapshot(tmp_path)
    registry = _discover(tmp_path)
    assert registry.skills[0].allows_write is True
    assert _snapshot(tmp_path) == before_discovery
    assert before == {}


def test_discovery_does_not_modify_files(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-21"""
    _write_skill(tmp_path, "read-only-skill")
    other = tmp_path / "unrelated.bin"
    other.write_bytes(b"unchanged\x00bytes")
    before = _snapshot(tmp_path)
    _discover(tmp_path)
    assert _snapshot(tmp_path) == before


def test_discovery_does_not_modify_git(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-22"""
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "-b", "main")
    git(repository, "config", "user.name", "Hermes Registry Test")
    git(repository, "config", "user.email", "registry@invalid.local")
    _write_skill(repository, "git-state-skill")
    git(repository, "add", "skills/git-state-skill/SKILL.md")
    git(repository, "commit", "-m", "fixture")
    head = git(repository, "rev-parse", "HEAD").stdout
    status = git(repository, "status", "--porcelain=v1", "-z").stdout
    config = (repository / ".git" / "config").read_bytes()
    _discover(repository)
    assert git(repository, "rev-parse", "HEAD").stdout == head
    assert git(repository, "status", "--porcelain=v1", "-z").stdout == status
    assert (repository / ".git" / "config").read_bytes() == config


def test_public_api_has_no_generic_runner_execute_skill_or_pipeline(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-23"""
    api = _registry_api()
    forbidden = {"runner", "pipeline", "execute_skill"}
    assert forbidden.isdisjoint(set(dir(api)))
    from hermes_ops.cli import build_parser
    assert "skills" not in build_parser().format_help().lower()


def test_registry_has_no_operational_dependencies() -> None:
    """Spec: HERMES-0004 / AC-24"""
    api = _registry_api()
    source = (Path(api.__file__).parent / "registry.py").read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "os.system",
        "shell=True",
        "importlib",
        "__import__",
        "eval(",
        "exec(",
    )
    assert all(token not in source for token in forbidden)


def test_skill_contract_public_api_remains_compatible(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-25"""
    path = _write_skill(tmp_path, "compatible-skill")
    before = load_skill(path)
    registry = _discover(tmp_path)
    assert registry.get_by_id("compatible-skill") == before
    assert isinstance(before, SkillDefinition)


def test_candidate_contents_are_not_recursively_inspected(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-26"""
    _write_skill(tmp_path, "outer-skill")
    nested = tmp_path / "skills" / "outer-skill" / "nested"
    nested.mkdir()
    (nested / "SKILL.md").write_text("invalid and inert", encoding="utf-8")
    registry = _discover(tmp_path)
    assert tuple(skill.id for skill in registry.skills) == ("outer-skill",)


def test_controlled_reverse_enumeration_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0004 / AC-27"""
    normal = tmp_path / "normal"
    reverse = tmp_path / "reverse"
    for skill_id in ("skill-a", "skill-b", "skill-c"):
        _write_skill(normal, skill_id)
    for skill_id in ("skill-c", "skill-b", "skill-a"):
        _write_skill(reverse, skill_id)
    normal_ids = tuple(skill.id for skill in _discover(normal).skills)
    reverse_ids = tuple(skill.id for skill in _discover(reverse).skills)
    assert normal_ids == reverse_ids == ("skill-a", "skill-b", "skill-c")


def test_explicit_discover_skills_api_remains_compatible(tmp_path: Path) -> None:
    """Spec: HERMES-0007 / AC-19"""
    _write_skill(tmp_path, "explicit-skill")
    registry = _discover(tmp_path)
    assert tuple(skill.id for skill in registry.skills) == ("explicit-skill",)
