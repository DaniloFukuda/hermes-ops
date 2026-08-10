from __future__ import annotations

from pathlib import Path
from typing import Any

from hermes_ops.core.errors import SkillContractError
from hermes_ops.skills.models import SkillDefinition
from hermes_ops.skills.validator import (
    parse_contract_v1,
    split_front_matter,
    validate_metadata,
    validate_required_sections,
)


def load_skill(path: Any) -> SkillDefinition:
    source = Path(path)
    try:
        is_file = source.is_file()
    except OSError as exc:
        raise SkillContractError(
            "SKILL_FILE_READ_FAILED",
            "The explicit SKILL.md path could not be inspected",
        ) from exc
    if not is_file:
        raise SkillContractError(
            "SKILL_FILE_NOT_FOUND",
            "The explicit SKILL.md path does not name a regular file",
        )

    try:
        text = source.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SkillContractError(
            "SKILL_INVALID_ENCODING",
            "SKILL.md is not valid UTF-8",
        ) from exc
    except OSError as exc:
        raise SkillContractError(
            "SKILL_FILE_READ_FAILED",
            "SKILL.md could not be read",
        ) from exc

    metadata_text, body = split_front_matter(text)
    parsed = parse_contract_v1(metadata_text)
    metadata = validate_metadata(parsed, source.parent.name)
    validate_required_sections(body)

    return SkillDefinition(
        schema_version=metadata.schema_version,
        id=metadata.id,
        version=metadata.version,
        status=metadata.status,
        description=metadata.description,
        risk=metadata.risk,
        requires=metadata.requires,
        allows_write=metadata.allows_write,
        path=source,
        body=body,
    )
