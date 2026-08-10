from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SkillStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class SkillRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    schema_version: int
    id: str
    version: int
    status: SkillStatus
    description: str
    risk: SkillRisk
    requires: tuple[str, ...]
    allows_write: bool
    path: Path
    body: str
