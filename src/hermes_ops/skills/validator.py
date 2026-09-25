from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from hermes_ops.core.errors import SkillContractError
from hermes_ops.skills.models import SkillRisk, SkillStatus


FIELDS = (
    "schema_version",
    "id",
    "version",
    "status",
    "description",
    "risk",
    "requires",
    "allows_write",
)
FIELD_SET = frozenset(FIELDS)
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
ID_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\Z")
VERSION_PATTERN = re.compile(r"[1-9][0-9]*\Z")
FENCE_PATTERN = re.compile(r"^[ \t]*(`{3,}|~{3,})")


@dataclass(frozen=True, slots=True)
class ValidatedMetadata:
    schema_version: int
    id: str
    version: int
    status: SkillStatus
    description: str
    risk: SkillRisk
    requires: tuple[str, ...]
    allows_write: bool


def _fail(code: str, message: str) -> None:
    raise SkillContractError(code, message)


def _line_without_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\r", "\n")):
        return line[:-1]
    return line


def split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    if not lines or _line_without_ending(lines[0]) != "---":
        _fail("SKILL_FRONT_MATTER_MISSING", "SKILL.md must start with ---")

    closing_index: int | None = None
    for index in range(1, len(lines)):
        if _line_without_ending(lines[index]) == "---":
            closing_index = index
            break
    if closing_index is None:
        _fail("SKILL_FRONT_MATTER_INVALID", "Front matter is not closed")

    metadata_text = "".join(lines[1:closing_index])
    if not metadata_text.strip():
        _fail("SKILL_FRONT_MATTER_INVALID", "Front matter is empty")
    body = "".join(lines[closing_index + 1 :])
    return metadata_text, body


def _is_forbidden_scalar(value: str) -> bool:
    return value.startswith(("|", ">", "&", "*", "!", "{", "["))


def parse_contract_v1(metadata_text: str) -> dict[str, str | tuple[str, ...]]:
    lines = metadata_text.splitlines()
    parsed: dict[str, str | tuple[str, ...]] = {}
    seen: set[str] = set()
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line or line[0].isspace() or ":" not in line:
            _fail("SKILL_FRONT_MATTER_INVALID", "Unexpected metadata line")

        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if key == "<<":
            _fail("SKILL_FRONT_MATTER_INVALID", "Merge keys are not supported")
        if key not in FIELD_SET:
            _fail("SKILL_UNKNOWN_FIELD", f"Unknown skill field: {key}")
        if key in seen:
            _fail("SKILL_DUPLICATE_FIELD", f"Duplicate skill field: {key}")
        seen.add(key)

        if key != "requires":
            if _is_forbidden_scalar(value):
                _fail(
                    "SKILL_FRONT_MATTER_INVALID",
                    f"Unsupported syntax in field: {key}",
                )
            parsed[key] = value
            index += 1
            continue

        if value == "[]":
            parsed[key] = ()
            index += 1
            continue
        if value:
            _fail(
                "SKILL_FRONT_MATTER_INVALID",
                "requires must be [] or an indented block list",
            )

        index += 1
        items: list[str] = []
        while index < len(lines):
            item_line = lines[index]
            if item_line.startswith("  - "):
                item = item_line[4:].strip()
                if not item:
                    _fail("SKILL_INVALID_REQUIRES", "requires contains an empty item")
                if _is_forbidden_scalar(item):
                    _fail(
                        "SKILL_FRONT_MATTER_INVALID",
                        "Nested requires structures are not supported",
                    )
                items.append(item)
                index += 1
                continue

            if (
                item_line
                and not item_line[0].isspace()
                and ":" in item_line
                and item_line.split(":", 1)[0] in FIELD_SET
            ):
                break
            _fail("SKILL_FRONT_MATTER_INVALID", "Invalid requires list line")

        if not items:
            _fail("SKILL_INVALID_REQUIRES", "requires block list is empty")
        parsed[key] = tuple(items)

    return parsed


def validate_metadata(
    metadata: dict[str, str | tuple[str, ...]],
    directory_name: str,
) -> ValidatedMetadata:
    for field in FIELDS:
        if field not in metadata:
            _fail("SKILL_REQUIRED_FIELD_MISSING", f"Missing required field: {field}")

    schema_version = metadata["schema_version"]
    if schema_version != "1":
        _fail("SKILL_UNSUPPORTED_SCHEMA", "schema_version must be exactly 1")

    skill_id = metadata["id"]
    if not isinstance(skill_id, str) or ID_PATTERN.fullmatch(skill_id) is None:
        _fail("SKILL_INVALID_ID", "Skill id does not match the version 1 grammar")
    if skill_id != directory_name:
        _fail(
            "SKILL_ID_DIRECTORY_MISMATCH",
            "Skill id does not match its parent directory",
        )

    version = metadata["version"]
    if not isinstance(version, str) or VERSION_PATTERN.fullmatch(version) is None:
        _fail("SKILL_INVALID_VERSION", "Skill version must be a positive decimal")

    status_text = metadata["status"]
    try:
        status = SkillStatus(status_text)
    except (TypeError, ValueError):
        _fail("SKILL_INVALID_STATUS", "Skill status is invalid")

    description = metadata["description"]
    if not isinstance(description, str) or not description:
        _fail("SKILL_INVALID_DESCRIPTION", "Skill description must not be empty")

    risk_text = metadata["risk"]
    try:
        risk = SkillRisk(risk_text)
    except (TypeError, ValueError):
        _fail("SKILL_INVALID_RISK", "Skill risk is invalid")

    requires = metadata["requires"]
    if not isinstance(requires, tuple) or any(not item for item in requires):
        _fail("SKILL_INVALID_REQUIRES", "Skill requires list is invalid")
    if len(set(requires)) != len(requires):
        _fail("SKILL_INVALID_REQUIRES", "Skill requires list contains duplicates")

    allows_write_text = metadata["allows_write"]
    if allows_write_text not in {"true", "false"}:
        _fail(
            "SKILL_INVALID_ALLOWS_WRITE",
            "allows_write must be exactly true or false",
        )

    return ValidatedMetadata(
        schema_version=1,
        id=skill_id,
        version=int(version),
        status=status,
        description=description,
        risk=risk,
        requires=requires,
        allows_write=allows_write_text == "true",
    )


def validate_required_sections(body: str) -> None:
    found: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in body.splitlines():
        if fence_character is not None:
            candidate = line.strip()
            if (
                len(candidate) >= fence_length
                and set(candidate) == {fence_character}
            ):
                fence_character = None
                fence_length = 0
            continue

        fence = FENCE_PATTERN.match(line)
        if fence is not None:
            token = fence.group(1)
            if fence_character is None:
                fence_character = token[0]
                fence_length = len(token)
            continue
        if not line.startswith("## ") or line.startswith("### "):
            continue
        name = line[3:].rstrip()
        if name in REQUIRED_SECTIONS:
            found.append(name)

    for section in REQUIRED_SECTIONS:
        count = found.count(section)
        if count == 0:
            _fail(
                "SKILL_REQUIRED_SECTION_MISSING",
                f"Missing required section: {section}",
            )
        if count > 1:
            _fail(
                "SKILL_DUPLICATE_SECTION",
                f"Duplicate required section: {section}",
            )
    if tuple(found) != REQUIRED_SECTIONS:
        _fail("SKILL_SECTION_ORDER_INVALID", "Required sections are out of order")
