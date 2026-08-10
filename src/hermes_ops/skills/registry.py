from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Any

from hermes_ops.core.errors import SkillRegistryError
from hermes_ops.skills.loader import load_skill
from hermes_ops.skills.models import SkillDefinition
from hermes_ops.skills.validator import ID_PATTERN


_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_NAME_SURROGATE_TAG_BIT = 0x20000000


def _fail(code: str, message: str) -> None:
    raise SkillRegistryError(code, message)


def _absolute_without_resolving(path: Path) -> Path:
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _metadata(path: Path) -> os.stat_result | None:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise SkillRegistryError(
            "SKILL_DISCOVERY_READ_FAILED",
            "A protected discovery path could not be inspected",
        ) from exc


def _is_name_indirection(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    if not attributes & _REPARSE_POINT_ATTRIBUTE:
        return False
    reparse_tag = getattr(metadata, "st_reparse_tag", None)
    if reparse_tag is None:
        _fail(
            "SKILL_DISCOVERY_READ_FAILED",
            "A protected reparse point could not be classified safely",
        )
    return bool(reparse_tag & _NAME_SURROGATE_TAG_BIT)


def _reject_indirection(metadata: os.stat_result) -> None:
    if _is_name_indirection(metadata):
        _fail(
            "SKILL_DISCOVERY_INDIRECT_PATH",
            "Skill discovery does not follow filesystem name indirections",
        )


def _inspect_existing_components(path: Path) -> os.stat_result | None:
    absolute = _absolute_without_resolving(path)
    anchor = Path(absolute.anchor)
    current = anchor
    final_metadata = _metadata(anchor)
    if final_metadata is None:
        return None
    _reject_indirection(final_metadata)

    for part in absolute.parts[1:]:
        current = current / part
        metadata = _metadata(current)
        if metadata is None:
            return None
        _reject_indirection(metadata)
        final_metadata = metadata
    return final_metadata


def _inspect_direct_child(path: Path) -> os.stat_result | None:
    metadata = _metadata(path)
    if metadata is not None:
        _reject_indirection(metadata)
    return metadata


@dataclass(frozen=True, slots=True)
class SkillRegistry:
    skills: tuple[SkillDefinition, ...]

    def __post_init__(self) -> None:
        ordered = tuple(sorted(tuple(self.skills), key=lambda skill: skill.id))
        identifiers = tuple(skill.id for skill in ordered)
        if len(set(identifiers)) != len(identifiers):
            _fail(
                "SKILL_REGISTRY_DUPLICATE_ID",
                "Skill registry contains duplicate identifiers",
            )
        object.__setattr__(self, "skills", ordered)

    def get_by_id(self, skill_id: str) -> SkillDefinition | None:
        for skill in self.skills:
            if skill.id == skill_id:
                return skill
        return None


def _candidate_directories(skills_root: Path) -> tuple[Path, ...]:
    try:
        entries = tuple(sorted(skills_root.iterdir(), key=lambda entry: entry.name))
    except OSError as exc:
        raise SkillRegistryError(
            "SKILL_DISCOVERY_READ_FAILED",
            "The skills directory could not be enumerated",
        ) from exc

    candidates: list[Path] = []
    for entry in entries:
        metadata = _inspect_direct_child(entry)
        if metadata is None:
            _fail(
                "SKILL_DISCOVERY_READ_FAILED",
                "A discovery candidate disappeared during inspection",
            )
        if ID_PATTERN.fullmatch(entry.name) is None or not stat.S_ISDIR(
            metadata.st_mode
        ):
            _fail(
                "SKILL_CANDIDATE_INVALID",
                "A direct skills entry is not a valid candidate directory",
            )

        contract = entry / "SKILL.md"
        contract_metadata = _inspect_direct_child(contract)
        if contract_metadata is None:
            _fail(
                "SKILL_CANDIDATE_MISSING_CONTRACT",
                "A skill candidate does not contain a direct SKILL.md",
            )
        if not stat.S_ISREG(contract_metadata.st_mode):
            _fail(
                "SKILL_CANDIDATE_INVALID",
                "A skill candidate contract is not a regular file",
            )
        candidates.append(entry)
    return tuple(candidates)


def discover_skills(project_root: Any) -> SkillRegistry:
    try:
        project = _absolute_without_resolving(Path(project_root))
    except (TypeError, ValueError, OSError) as exc:
        raise SkillRegistryError(
            "SKILL_PROJECT_ROOT_INVALID",
            "The explicit project root is invalid",
        ) from exc

    project_metadata = _inspect_existing_components(project)
    if project_metadata is None or not stat.S_ISDIR(project_metadata.st_mode):
        _fail(
            "SKILL_PROJECT_ROOT_INVALID",
            "The explicit project root does not name a direct directory",
        )

    skills_root = project / "skills"
    skills_metadata = _inspect_direct_child(skills_root)
    if skills_metadata is None:
        _fail(
            "SKILL_ROOT_NOT_FOUND",
            "The explicit project root does not contain a skills directory",
        )
    if not stat.S_ISDIR(skills_metadata.st_mode):
        _fail(
            "SKILL_ROOT_INVALID",
            "The direct skills entry is not a directory",
        )

    definitions = tuple(
        load_skill(candidate / "SKILL.md")
        for candidate in _candidate_directories(skills_root)
    )
    return SkillRegistry(definitions)
