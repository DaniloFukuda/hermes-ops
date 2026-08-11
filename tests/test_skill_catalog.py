from __future__ import annotations

from importlib import metadata
from pathlib import Path, PurePosixPath

import pytest

from hermes_ops.core.errors import SkillCatalogError
from hermes_ops.skills.catalog import resolve_own_skill_catalog
from hermes_ops.skills.registry import discover_skills


class _DistributionFixture:
    def __init__(
        self,
        *,
        files: tuple[PurePosixPath, ...] = (),
        located: Path | None = None,
        direct_url: str | None = None,
    ) -> None:
        self.files = files
        self._located = located
        self._direct_url = direct_url

    def read_text(self, filename: str) -> str | None:
        assert filename == "direct_url.json"
        return self._direct_url

    def locate_file(self, path: PurePosixPath) -> Path:
        assert self._located is not None
        return self._located


def test_catalog_resolution_is_anchored_to_installed_hermes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0007 / AC-04"""
    decoy = tmp_path / "decoy"
    (decoy / "skills").mkdir(parents=True)
    monkeypatch.chdir(decoy)

    root = resolve_own_skill_catalog()

    assert root != decoy
    assert (root / "skills/git-preflight/SKILL.md").is_file()


def test_catalog_resolution_never_searches_cwd_parents_or_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0007 / AC-05"""
    for name in ("cwd", "parent", "target", "sibling", "home", "path"):
        (tmp_path / name / "skills/git-preflight").mkdir(parents=True)
        (tmp_path / name / "skills/git-preflight/SKILL.md").write_text(
            "malicious",
            encoding="utf-8",
        )
    monkeypatch.chdir(tmp_path / "cwd")

    root = resolve_own_skill_catalog()

    assert root == Path(__file__).resolve().parents[1]


def test_catalog_is_discovered_with_existing_strict_contract() -> None:
    """Spec: HERMES-0007 / AC-06"""
    registry = discover_skills(resolve_own_skill_catalog())
    skill = registry.get_by_id("git-preflight")
    assert skill is not None
    assert tuple(item.id for item in registry.skills) == ("code-audit", "git-preflight", "mission-audit")
    assert skill.requires == ("git",)
    assert skill.allows_write is False


@pytest.mark.parametrize("case", ["missing", "duplicate", "invalid-resource"])
def test_missing_or_invalid_own_catalog_fails_closed(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0007 / AC-10"""
    anchor = PurePosixPath(
        "../../../hermes_ops_skill_catalog/skills/git-preflight/SKILL.md"
    )
    if case == "missing":
        fixture = _DistributionFixture()
        expected = "SKILL_CATALOG_NOT_FOUND"
    elif case == "duplicate":
        fixture = _DistributionFixture(files=(anchor, anchor))
        expected = "SKILL_CATALOG_INVALID"
    else:
        fixture = _DistributionFixture(files=(anchor,), located=tmp_path / "missing")
        expected = "SKILL_CATALOG_INVALID"
    monkeypatch.setattr(metadata, "distribution", lambda name: fixture)

    with pytest.raises(SkillCatalogError) as caught:
        resolve_own_skill_catalog()

    assert caught.value.code == expected


def test_invalid_catalog_candidate_aborts_atomically(tmp_path: Path) -> None:
    """Spec: HERMES-0007 / AC-11"""
    source = Path(__file__).resolve().parents[1] / "skills/git-preflight/SKILL.md"
    valid = tmp_path / "skills/git-preflight/SKILL.md"
    valid.parent.mkdir(parents=True)
    valid.write_bytes(source.read_bytes())
    (tmp_path / "skills/z-invalid").mkdir()

    result = object()
    with pytest.raises(Exception) as caught:
        result = discover_skills(tmp_path)

    assert getattr(caught.value, "code", None) == "SKILL_CANDIDATE_MISSING_CONTRACT"
    assert result.__class__ is object


def test_packaged_catalog_contains_exact_git_preflight_contract() -> None:
    """Spec: HERMES-0007 / AC-23"""
    canonical = Path(__file__).resolve().parents[1] / "skills/git-preflight/SKILL.md"
    resolved = resolve_own_skill_catalog() / "skills/git-preflight/SKILL.md"
    assert resolved.samefile(canonical)
    assert resolved.read_bytes() == canonical.read_bytes()


def test_installed_catalog_resolution_does_not_depend_on_one_skill_anchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0008 / AC-41"""
    prefix = PurePosixPath("../../../hermes_ops_skill_catalog/skills")
    entries = (
        prefix / "code-audit/SKILL.md",
        prefix / "git-preflight/SKILL.md",
    )
    installed = tmp_path / "hermes_ops_skill_catalog/skills/code-audit/SKILL.md"
    installed.parent.mkdir(parents=True)
    installed.write_text("anchor", encoding="utf-8")
    fixture = _DistributionFixture(files=entries, located=installed)
    monkeypatch.setattr(metadata, "distribution", lambda name: fixture)

    assert resolve_own_skill_catalog() == tmp_path / "hermes_ops_skill_catalog"
