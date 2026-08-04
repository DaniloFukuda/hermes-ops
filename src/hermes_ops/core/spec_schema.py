from __future__ import annotations

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

# Allowed fields in evidence
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


def _validate_acceptance_criteria(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate acceptance_criteria fields if present and is list of mappings."""
    issues = []
    ac = toml_data.get("acceptance_criteria")
    if not isinstance(ac, list):
        return issues  # Not a list, defer structural validation to later block

    for idx, item in enumerate(ac):
        if not isinstance(item, dict):
            continue  # Defer structural validation to later block

        unknown_fields = sorted(set(item.keys()) - _ALLOWED_AC_FIELDS)
        for field in unknown_fields:
            issues.append(SchemaIssue(
                code="unknown_field_ac",
                field=f"acceptance_criteria[{idx}].{field}",
                message=f"Unknown field in acceptance_criteria[{idx}]: {field}",
            ))
    return issues


def _validate_evidence(toml_data: dict[str, Any]) -> list[SchemaIssue]:
    """Validate evidence fields if present and is a mapping."""
    issues = []
    evidence = toml_data.get("evidence")
    if not isinstance(evidence, dict):
        return issues  # Not a mapping, defer structural validation to later block

    unknown_fields = sorted(set(evidence.keys()) - _ALLOWED_EVIDENCE_FIELDS)
    for field in unknown_fields:
        issues.append(SchemaIssue(
            code="unknown_field_evidence",
            field=f"evidence.{field}",
            message=f"Unknown field in evidence: {field}",
        ))
    return issues


def validate_spec_schema(toml_data: dict[str, Any]) -> tuple[SchemaIssue, ...]:
    """Validate TOML data against schema_version 1 closed schema.

    Args:
        toml_data: Parsed TOML dictionary from hybrid parser.

    Returns:
        Tuple of SchemaIssue objects in deterministic order:
        1. schema_version issues (if any)
        2. Unknown top-level fields (alphabetical)
        3. acceptance_criteria issues (by item index, fields alphabetical)
        4. evidence issues (alphabetical)

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

    # 2. Top-level unknown fields (alphabetical)
    issues.extend(_validate_toplevel_fields(toml_data))

    # 3. acceptance_criteria (by index, fields alphabetical)
    issues.extend(_validate_acceptance_criteria(toml_data))

    # 4. evidence (alphabetical)
    issues.extend(_validate_evidence(toml_data))

    return tuple(issues)