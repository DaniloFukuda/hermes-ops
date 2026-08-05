from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SchemaIssue:
    """Represents a schema validation issue.

    Attributes:
        code: Stable error code identifying the issue type.
        field: Structural location of the issue (e.g., "schema_version",
            "acceptance_criteria[2].unknown_field", "evidence.field_name").
        message: Stable human-readable description.
    """
    code: str
    field: str
    message: str


# Top-level allowed fields for schema_version 1
_ALLOWED_TOPLEVEL_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "id",
    "status",
    "acceptance_criteria",
    "superseded_by",
    "evidence",
})

# Allowed fields in each acceptance_criteria item
_ALLOWED_AC_FIELDS: frozenset[str] = frozenset({
    "id",
    "test_file",
    "test_function",
    "justification",
})

# Allowed fields in evidence (canonical order for deterministic validation)
_ALLOWED_EVIDENCE_FIELDS: frozenset[str] = frozenset({
    "Commit da implementação",
    "Estado da integração",
    "Arquivos alterados",
    "Testes direcionados",
    "Suíte completa",
    "Validação de sintaxe ou compileall",
    "Empacotamento",
    "git diff --check",
    "Plataformas e versões validadas",
    "CI",
    "Limitações do ambiente",
})

# Canonical order for evidence fields (for deterministic validation order)
_EVIDENCE_FIELD_ORDER: tuple[str, ...] = (
    "Commit da implementação",
    "Estado da integração",
    "Arquivos alterados",
    "Testes direcionados",
    "Suíte completa",
    "Validação de sintaxe ou compileall",
    "Empacotamento",
    "git diff --check",
    "Plataformas e versões validadas",
    "CI",
    "Limitações do ambiente",
)

# Valid status values for schema_version 1
_VALID_STATUSES: frozenset[str] = frozenset({
    "Rascunho",
    "Aprovado",
    "Em implementação",
    "Implementado",
    "Substituído",
})

# Regex for HERMES-NNNN format (exactly 4 digits)
import re
_HERMES_ID_PATTERN = re.compile(r"HERMES-[0-9]{4}")


def _validate_schema_version(toml_data: dict[str, Any]) -> SchemaIssue | None:
    """Validate schema_version field. Returns SchemaIssue if invalid, None if valid (==1)."""
    if "schema_version" not in toml_data:
        return SchemaIssue(
            code="missing_schema_version",
            field="schema_version",
            message="schema_version is required",
        )

    value = toml_data["schema_version"]

    # bool is subclass of int in Python, must explicitly reject
    if isinstance(value, bool) or not isinstance(value, int):
        return SchemaIssue(
            code="invalid_schema_version_type",
            field="schema_version",
            message="schema_version must be an integer",
        )

    if value <= 0:
        return SchemaIssue(
            code="invalid_schema_version_value",
            field="schema_version",
            message="schema_version must be a positive integer",
        )

    if value > 1:
        return SchemaIssue(
            code="unsupported_schema_version",
            field="schema_version",
            message=f"schema_version {value} is not supported; only version 1 is supported",
        )

    # value == 1 is valid
    return None


def _validate_toplevel_fields(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate top-level fields against allowed set."""
    issues = []
    for key in sorted(toml_data.keys()):
        if key not in _ALLOWED_TOPLEVEL_FIELDS:
            issues.append(SchemaIssue(
                code="unknown_field_toplevel",
                field=key,
                message=f"Unknown top-level field: {key}",
            ))
    return issues


def _validate_toplevel_field_types(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate types of known top-level fields."""
    issues = []

    # id must be string
    if "id" in toml_data and not isinstance(toml_data["id"], str):
        issues.append(SchemaIssue(
            code="invalid_field_type",
            field="id",
            message="id must be a string",
        ))

    # status must be string
    if "status" in toml_data and not isinstance(toml_data["status"], str):
        issues.append(SchemaIssue(
            code="invalid_field_type",
            field="status",
            message="status must be a string",
        ))

    # superseded_by must be string when present
    if "superseded_by" in toml_data and not isinstance(toml_data["superseded_by"], str):
        issues.append(SchemaIssue(
            code="invalid_field_type",
            field="superseded_by",
            message="superseded_by must be a string",
        ))

    return issues


def _validate_acceptance_criteria(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate acceptance_criteria structure and field types."""
    issues = []
    ac = toml_data.get("acceptance_criteria")

    # Container type validation
    if ac is not None and not isinstance(ac, list):
        issues.append(SchemaIssue(
            code="invalid_acceptance_criteria_type",
            field="acceptance_criteria",
            message="acceptance_criteria must be a list",
        ))
        return issues  # Do not validate items when container type is invalid

    if not isinstance(ac, list):
        return issues  # Not a list (or absent), defer to later blocks

    # Validate each item
    for idx, item in enumerate(ac):
        # Item type validation
        if not isinstance(item, Mapping):
            issues.append(SchemaIssue(
                code="invalid_acceptance_criterion_type",
                field=f"acceptance_criteria[{idx}]",
                message=f"acceptance_criteria[{idx}] must be a mapping",
            ))
            continue  # Continue to next item, don't validate fields of invalid item

        # Unknown fields (alphabetical order)
        unknown_fields = sorted(set(item.keys()) - _ALLOWED_AC_FIELDS)
        for field in unknown_fields:
            issues.append(SchemaIssue(
                code="unknown_field_ac",
                field=f"acceptance_criteria[{idx}].{field}",
                message=f"Unknown field in acceptance_criteria[{idx}]: {field}",
            ))

        # Known field types (in specified order)
        if "id" in item and not isinstance(item["id"], str):
            issues.append(SchemaIssue(
                code="invalid_field_type",
                field=f"acceptance_criteria[{idx}].id",
                message="acceptance_criteria[i].id must be a string",
            ))

        if "test_file" in item and not isinstance(item["test_file"], str):
            issues.append(SchemaIssue(
                code="invalid_field_type",
                field=f"acceptance_criteria[{idx}].test_file",
                message="acceptance_criteria[i].test_file must be a string",
            ))

        if "test_function" in item and not isinstance(item["test_function"], str):
            issues.append(SchemaIssue(
                code="invalid_field_type",
                field=f"acceptance_criteria[{idx}].test_function",
                message="acceptance_criteria[i].test_function must be a string",
            ))

        if "justification" in item and not isinstance(item["justification"], str):
            issues.append(SchemaIssue(
                code="invalid_field_type",
                field=f"acceptance_criteria[{idx}].justification",
                message="acceptance_criteria[i].justification must be a string",
            ))

    return issues


def _validate_evidence(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate evidence structure and field types."""
    issues = []
    evidence = toml_data.get("evidence")

    # Container type validation
    if evidence is not None and not isinstance(evidence, Mapping):
        issues.append(SchemaIssue(
            code="invalid_evidence_type",
            field="evidence",
            message="evidence must be a mapping",
        ))
        return issues  # Do not validate fields when container type is invalid

    if not isinstance(evidence, Mapping):
        return issues  # Not a mapping (or absent), defer to later blocks

    # Unknown fields (alphabetical order)
    unknown_fields = sorted(set(evidence.keys()) - _ALLOWED_EVIDENCE_FIELDS)
    for field in unknown_fields:
        issues.append(SchemaIssue(
            code="unknown_field_evidence",
            field=f"evidence.{field}",
            message=f"Unknown field in evidence: {field}",
        ))

    # Known field types (in canonical order for determinism)
    for field_name in _EVIDENCE_FIELD_ORDER:
        if field_name in evidence and not isinstance(evidence[field_name], str):
            issues.append(SchemaIssue(
                code="invalid_field_type",
                field=f"evidence.{field_name}",
                message=f"evidence.{field_name} must be a string",
            ))

    return issues


def _validate_toml_id(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate id field semantics (HERMES-NNNN format)."""
    issues = []
    if "id" not in toml_data:
        issues.append(SchemaIssue(
            code="missing_toml_id",
            field="id",
            message="id is required",
        ))
        return issues

    value = toml_data["id"]
    if not isinstance(value, str):
        # Type error already handled in _validate_toplevel_field_types
        # Do not emit invalid_toml_id_format as secondary error
        return issues

    if not _HERMES_ID_PATTERN.fullmatch(value):
        issues.append(SchemaIssue(
            code="invalid_toml_id_format",
            field="id",
            message="id must match format HERMES-NNNN (exactly 4 digits)",
        ))

    return issues


def _validate_toml_status(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate status field semantics."""
    issues = []
    if "status" not in toml_data:
        issues.append(SchemaIssue(
            code="missing_toml_status",
            field="status",
            message="status is required",
        ))
        return issues

    value = toml_data["status"]
    if not isinstance(value, str):
        # Type error already handled in _validate_toplevel_field_types
        # Do not emit invalid_toml_status as secondary error
        return issues

    if value not in _VALID_STATUSES:
        issues.append(SchemaIssue(
            code="invalid_toml_status",
            field="status",
            message="status must be one of: Rascunho, Aprovado, Em implementação, Implementado, Substituído",
        ))

    return issues


def _validate_acceptance_criteria_semantics(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate acceptance_criteria field semantics (presence only)."""
    issues = []
    if "acceptance_criteria" not in toml_data:
        issues.append(SchemaIssue(
            code="missing_acceptance_criteria",
            field="acceptance_criteria",
            message="acceptance_criteria is required",
        ))
        return issues

    value = toml_data["acceptance_criteria"]
    if not isinstance(value, list):
        # Type error already handled in _validate_acceptance_criteria
        # Do not emit missing_acceptance_criteria as secondary error
        return issues

    # Empty list is allowed in this block
    # Non-empty list items validated in _validate_acceptance_criteria

    return issues


def validate_spec_schema(toml_data: dict[str, Any]) -> tuple[SchemaIssue, ...]:
    """Validate TOML data against schema_version 1 closed schema.

    Args:
        toml_data: Parsed TOML dictionary from hybrid parser.

    Returns:
        Tuple of SchemaIssue objects in deterministic order:
        1. schema_version issues (if any)
        2. Unknown top-level fields (alphabetical)
        3. Types of known top-level fields (id, status, superseded_by)
        4. id semantic validation (missing_toml_id, invalid_toml_id_format)
        5. status semantic validation (missing_toml_status, invalid_toml_status)
        6. acceptance_criteria:
           - container type error when applicable
           - items in original order
           - for Mapping items:
             a. unknown fields alphabetical
             b. known field types in order: id, test_file, test_function, justification
        7. acceptance_criteria semantic validation (missing_acceptance_criteria)
        8. evidence:
           - container type error when applicable
           - unknown fields alphabetical
           - known field types in canonical order

    Does not modify toml_data. Returns all detectable issues for this block.
    Does not raise exceptions for expected document errors.
    """
    issues: list[SchemaIssue] = []

    # 1. schema_version validation (precedence rules)
    sv_issue = _validate_schema_version(toml_data)
    if sv_issue is not None:
        issues.append(sv_issue)
        # When schema_version is invalid, do not apply closed-field rules
        return tuple(issues)

    # 2. Unknown top-level fields (alphabetical)
    issues.extend(_validate_toplevel_fields(toml_data))

    # 3. Types of known top-level fields (id, status, superseded_by)
    issues.extend(_validate_toplevel_field_types(toml_data))

    # 4. id semantic validation (missing_toml_id, invalid_toml_id_format)
    issues.extend(_validate_toml_id(toml_data))

    # 5. status semantic validation (missing_toml_status, invalid_toml_status)
    issues.extend(_validate_toml_status(toml_data))

    # 6. acceptance_criteria structure and field types
    issues.extend(_validate_acceptance_criteria(toml_data))

    # 7. acceptance_criteria semantic validation (missing_acceptance_criteria)
    issues.extend(_validate_acceptance_criteria_semantics(toml_data))

    # 8. evidence
    issues.extend(_validate_evidence(toml_data))

    return tuple(issues)