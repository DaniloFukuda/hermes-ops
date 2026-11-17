"""Pure construction and parsing of canonical structural source locators."""

from __future__ import annotations

import ast
from typing import Any

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.controlled_reader import valid_relative_path
from hermes_ops.skills.finding_models import EvidenceRef


def _invalid(message: str) -> None:
    raise SkillExecutionError("FINDING_NORMALIZATION_INVALID", message)


def source_locator(relative_path: str, node: ast.AST) -> str:
    """Create a deterministic relative-path and source-line locator."""
    if type(relative_path) is not str or not valid_relative_path(relative_path):
        _invalid("Evidence reference path must be safely relative")
    line: Any = getattr(node, "lineno", None)
    if type(line) is not int or line < 1:
        _invalid("Evidence reference lines are invalid")
    return f"{relative_path}:{line}"


def parse_source_locator(value: Any) -> EvidenceRef:
    """Parse the canonical locator contract used by structural findings."""
    if type(value) is not str:
        _invalid("Execution path evidence reference must be text")
    try:
        path, raw_line = value.rsplit(":", 1)
        line = int(raw_line)
    except (ValueError, AttributeError) as exc:
        raise SkillExecutionError(
            "FINDING_NORMALIZATION_INVALID",
            "Execution path evidence reference is invalid",
        ) from exc
    return EvidenceRef(path, line, line)
