from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.core.results import Status


FrozenValue = None | str | int | float | bool | tuple["FrozenValue", ...]


def _invalid(message: str) -> None:
    raise SkillExecutionError("SKILL_EXECUTION_INVALID", message)


def _canonical(value: FrozenValue) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _freeze(value: Any) -> FrozenValue:
    if value is None or type(value) in {str, int, float, bool}:
        return value
    if isinstance(value, Enum):
        return _freeze(value.value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Mapping):
        normalized: dict[str, FrozenValue] = {}
        for key, item in value.items():
            text_key = str(key)
            if text_key in normalized:
                _invalid("Execution detail mapping keys collide after normalization")
            normalized[text_key] = _freeze(item)
        return tuple((key, normalized[key]) for key in sorted(normalized))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        frozen = tuple(_freeze(item) for item in value)
        return tuple(sorted(frozen, key=_canonical))
    if is_dataclass(value) and not isinstance(value, type):
        return tuple((field.name, _freeze(getattr(value, field.name))) for field in fields(value))
    _invalid(f"Unsupported execution detail type: {type(value).__name__}")


class SkillExecutionStatus(str, Enum):
    PASSED = "passed"
    COMPLETED_WITH_FINDINGS = "completed_with_findings"
    COMPLETED_WITH_INSUFFICIENT_EVIDENCE = "completed_with_insufficient_evidence"


@dataclass(frozen=True, slots=True)
class SkillRunInputs:
    mission: str | None = None

    def __post_init__(self) -> None:
        if self.mission is not None and type(self.mission) is not str:
            _invalid("Mission input must be a string")


@dataclass(frozen=True, slots=True)
class SkillExecutionEvidence:
    name: str
    status: Status
    message: str
    details: FrozenValue
    code: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            _invalid("Execution evidence name must be a non-empty string")
        if type(self.status) is not Status:
            _invalid("Execution evidence status must be a Status")
        if type(self.message) is not str or type(self.code) is not str:
            _invalid("Execution evidence text fields must be strings")
        object.__setattr__(self, "details", _freeze(self.details))


@dataclass(frozen=True, slots=True)
class SkillExecutionResult:
    skill_id: str
    status: SkillExecutionStatus
    exit_code: int
    evidence: tuple[SkillExecutionEvidence, ...]

    def __post_init__(self) -> None:
        if type(self.skill_id) is not str or not self.skill_id:
            _invalid("Execution result skill id must be a non-empty string")
        if type(self.status) is not SkillExecutionStatus:
            _invalid("Execution result status is invalid")
        if type(self.exit_code) is not int:
            _invalid("Execution result exit code must be an integer")
        if type(self.evidence) is not tuple or any(
            type(item) is not SkillExecutionEvidence for item in self.evidence
        ):
            _invalid("Execution result evidence must be an evidence tuple")
