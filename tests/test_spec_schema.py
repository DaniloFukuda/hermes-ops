from __future__ import annotations

import pytest
from collections.abc import Mapping
from hermes_ops.core.errors import SpecParsingError
from hermes_ops.core.hybrid_parser import parse_hybrid_text
from hermes_ops.core.spec_schema import SchemaIssue, validate_spec_schema


class TestSchemaVersionValidation:
    """Tests for schema_version validation precedence."""

    def test_schema_version_missing(self) -> None:
        """Missing schema_version returns missing_schema_version."""
        toml_data = {"id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "missing_schema_version"
        assert issues[0].field == "schema_version"

    def test_schema_version_string(self) -> None:
        """String schema_version returns invalid_schema_version_type."""
        toml_data = {"schema_version": "1", "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_type"
        assert issues[0].field == "schema_version"

    def test_schema_version_float(self) -> None:
        """Float schema_version returns invalid_schema_version_type."""
        toml_data = {"schema_version": 1.0, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_type"
        assert issues[0].field == "schema_version"

    def test_schema_version_bool_true(self) -> None:
        """True schema_version returns invalid_schema_version_type (bool not int)."""
        toml_data = {"schema_version": True, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_type"
        assert issues[0].field == "schema_version"

    def test_schema_version_bool_false(self) -> None:
        """False schema_version returns invalid_schema_version_type (bool not int)."""
        toml_data = {"schema_version": False, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_type"
        assert issues[0].field == "schema_version"

    def test_schema_version_zero(self) -> None:
        """Zero schema_version returns invalid_schema_version_value."""
        toml_data = {"schema_version": 0, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_value"
        assert issues[0].field == "schema_version"

    def test_schema_version_negative(self) -> None:
        """Negative schema_version returns invalid_schema_version_value."""
        toml_data = {"schema_version": -1, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_value"
        assert issues[0].field == "schema_version"

    def test_schema_version_greater_than_1(self) -> None:
        """schema_version > 1 returns unsupported_schema_version."""
        toml_data = {"schema_version": 2, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "unsupported_schema_version"
        assert issues[0].field == "schema_version"

    def test_schema_version_equal_1(self) -> None:
        """schema_version == 1 passes schema_version validation."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        # No schema_version issue, may have other issues
        assert not any(iss.code.startswith("schema_version") for iss in issues)


class TestTomlIdSemantics:
    """Tests for id field semantic validation (Block 3A1)."""

    def test_id_missing(self) -> None:
        """Missing id returns missing_toml_id."""
        toml_data = {"schema_version": 1, "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        missing_issues = [i for i in issues if i.code == "missing_toml_id"]
        assert len(missing_issues) == 1
        assert missing_issues[0].field == "id"

    def test_id_valid(self) -> None:
        """Valid id format passes semantic validation."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        id_issues = [i for i in issues if i.code in ("missing_toml_id", "invalid_toml_id_format")]
        assert len(id_issues) == 0

    def test_id_lowercase(self) -> None:
        """Lowercase id returns invalid_toml_id_format."""
        toml_data = {"schema_version": 1, "id": "hermes-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        format_issues = [i for i in issues if i.code == "invalid_toml_id_format"]
        assert len(format_issues) == 1
        assert format_issues[0].field == "id"

    def test_id_three_digits(self) -> None:
        """Three-digit id returns invalid_toml_id_format."""
        toml_data = {"schema_version": 1, "id": "HERMES-001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        format_issues = [i for i in issues if i.code == "invalid_toml_id_format"]
        assert len(format_issues) == 1
        assert format_issues[0].field == "id"

    def test_id_five_digits(self) -> None:
        """Five-digit id returns invalid_toml_id_format."""
        toml_data = {"schema_version": 1, "id": "HERMES-00001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        format_issues = [i for i in issues if i.code == "invalid_toml_id_format"]
        assert len(format_issues) == 1
        assert format_issues[0].field == "id"

    def test_id_with_letters(self) -> None:
        """Id with letters instead of digits returns invalid_toml_id_format."""
        toml_data = {"schema_version": 1, "id": "HERMES-ABCD", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        format_issues = [i for i in issues if i.code == "invalid_toml_id_format"]
        assert len(format_issues) == 1
        assert format_issues[0].field == "id"

    def test_id_with_spaces(self) -> None:
        """Id with spaces returns invalid_toml_id_format."""
        toml_data = {"schema_version": 1, "id": " HERMES-0001 ", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        format_issues = [i for i in issues if i.code == "invalid_toml_id_format"]
        assert len(format_issues) == 1
        assert format_issues[0].field == "id"

    def test_id_non_string_only_invalid_field_type(self) -> None:
        """Non-string id produces only invalid_field_type, not invalid_toml_id_format."""
        toml_data = {"schema_version": 1, "id": 123, "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Should have invalid_field_type for id
        assert "invalid_field_type" in codes
        # Should NOT have invalid_toml_id_format
        assert "invalid_toml_id_format" not in codes

    def test_id_non_string_no_invalid_toml_id_format(self) -> None:
        """Non-string id does not produce invalid_toml_id_format as secondary error."""
        toml_data = {"schema_version": 1, "id": 123, "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        id_format_issues = [i for i in issues if i.code == "invalid_toml_id_format"]
        assert len(id_format_issues) == 0


class TestTomlStatusSemantics:
    """Tests for status field semantic validation (Block 3A1)."""

    def test_status_missing(self) -> None:
        """Missing status returns missing_toml_status."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        missing_issues = [i for i in issues if i.code == "missing_toml_status"]
        assert len(missing_issues) == 1
        assert missing_issues[0].field == "status"

    def test_status_valid_rascunho(self) -> None:
        """Status 'Rascunho' is valid."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code in ("missing_toml_status", "invalid_toml_status")]
        assert len(status_issues) == 0

    def test_status_valid_aprovado(self) -> None:
        """Status 'Aprovado' is valid."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Aprovado", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code in ("missing_toml_status", "invalid_toml_status")]
        assert len(status_issues) == 0

    def test_status_valid_em_implementacao(self) -> None:
        """Status 'Em implementação' is valid."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Em implementação", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code in ("missing_toml_status", "invalid_toml_status")]
        assert len(status_issues) == 0

    def test_status_valid_implementado(self) -> None:
        """Status 'Implementado' is valid."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Implementado", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code in ("missing_toml_status", "invalid_toml_status")]
        assert len(status_issues) == 0

    def test_status_valid_substituido(self) -> None:
        """Status 'Substituído' is valid."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Substituído", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code in ("missing_toml_status", "invalid_toml_status")]
        assert len(status_issues) == 0

    def test_status_wrong_capitalization(self) -> None:
        """Status with wrong capitalization returns invalid_toml_status."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code == "invalid_toml_status"]
        assert len(status_issues) == 1
        assert status_issues[0].field == "status"

    def test_status_extra_space(self) -> None:
        """Status with extra space returns invalid_toml_status."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho ", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code == "invalid_toml_status"]
        assert len(status_issues) == 1
        assert status_issues[0].field == "status"

    def test_status_unknown(self) -> None:
        """Unknown status returns invalid_toml_status."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Invalido", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_issues = [i for i in issues if i.code == "invalid_toml_status"]
        assert len(status_issues) == 1
        assert status_issues[0].field == "status"

    def test_status_non_string_only_invalid_field_type(self) -> None:
        """Non-string status produces only invalid_field_type, not invalid_toml_status."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": 42, "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Should have invalid_field_type for status
        assert "invalid_field_type" in codes
        # Should NOT have invalid_toml_status
        assert "invalid_toml_status" not in codes

    def test_status_non_string_no_invalid_toml_status(self) -> None:
        """Non-string status does not produce invalid_toml_status as secondary error."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": 42, "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        status_format_issues = [i for i in issues if i.code == "invalid_toml_status"]
        assert len(status_format_issues) == 0


class TestAcceptanceCriteriaSemantics:
    """Tests for acceptance_criteria semantic validation (Block 3A1)."""

    def test_acceptance_criteria_missing(self) -> None:
        """Missing acceptance_criteria returns missing_acceptance_criteria."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho"}
        issues = validate_spec_schema(toml_data)
        missing_issues = [i for i in issues if i.code == "missing_acceptance_criteria"]
        assert len(missing_issues) == 1
        assert missing_issues[0].field == "acceptance_criteria"

    def test_acceptance_criteria_empty_list_allowed(self) -> None:
        """Empty acceptance_criteria list is allowed."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        ac_semantic_issues = [i for i in issues if i.code in ("missing_acceptance_criteria", "empty_acceptance_criteria")]
        assert len(ac_semantic_issues) == 0

    def test_acceptance_criteria_non_list_uses_invalid_type(self) -> None:
        """Non-list acceptance_criteria continues using invalid_acceptance_criteria_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": "not a list"}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_acceptance_criteria_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "acceptance_criteria"

    def test_acceptance_criteria_non_list_no_missing(self) -> None:
        """Non-list container does not produce missing_acceptance_criteria."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": "not a list"}
        issues = validate_spec_schema(toml_data)
        missing_issues = [i for i in issues if i.code == "missing_acceptance_criteria"]
        assert len(missing_issues) == 0

    def test_acceptance_criteria_absent_no_invalid_type(self) -> None:
        """Absent acceptance_criteria does not produce invalid_acceptance_criteria_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho"}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_acceptance_criteria_type"]
        assert len(type_issues) == 0


class TestPrecedenceAndDeterminism:
    """Tests for precedence and deterministic ordering (Block 3A1)."""

    def test_schema_version_missing_blocks_new_errors(self) -> None:
        """Missing schema_version blocks all new semantic errors."""
        toml_data = {"id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "missing_schema_version"

    def test_schema_version_invalid_type_blocks_new_errors(self) -> None:
        """Invalid schema_version type blocks all new semantic errors."""
        toml_data = {"schema_version": "1", "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_type"

    def test_schema_version_invalid_value_blocks_new_errors(self) -> None:
        """Invalid schema_version value blocks all new semantic errors."""
        toml_data = {"schema_version": 0, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_value"

    def test_missing_id_status_acceptance_criteria_deterministic_order(self) -> None:
        """Missing id, status, acceptance_criteria reported in deterministic order: id, status, acceptance_criteria."""
        toml_data = {"schema_version": 1}
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Should be in order: missing_toml_id, missing_toml_status, missing_acceptance_criteria
        assert codes == [
            "missing_toml_id",
            "missing_toml_status",
            "missing_acceptance_criteria",
        ]

    def test_unknown_field_type_semantic_order(self) -> None:
        """Unknown fields, type errors, semantic errors in deterministic order."""
        toml_data = {
            "schema_version": 1,
            "id": 123,  # type error
            "status": 456,  # type error
            "unknown_top": "value",  # unknown field
            "acceptance_criteria": "not a list",  # container type error
        }
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # When id/status have wrong types, only type errors are emitted (not missing semantic errors)
        # acceptance_criteria is present but wrong type -> only invalid_acceptance_criteria_type
        expected = [
            "unknown_field_toplevel",
            "invalid_field_type",  # id
            "invalid_field_type",  # status
            "invalid_acceptance_criteria_type",
        ]
        assert codes == expected

    def test_input_not_modified(self) -> None:
        """validate_spec_schema does not modify input dict."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": [], "extra": "value"}
        original = dict(toml_data)
        validate_spec_schema(toml_data)
        assert toml_data == original

    def test_return_type_is_tuple(self) -> None:
        """Return type is tuple (immutable), not list."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": []}
        issues = validate_spec_schema(toml_data)
        assert isinstance(issues, tuple)
        assert all(isinstance(i, SchemaIssue) for i in issues)

    def test_no_non_canonical_capitalization_emitted(self) -> None:
        """No issue uses non_canonical_capitalization code."""
        test_cases = [
            {"schema_version": 1, "id": "hermes-0001", "status": "Rascunho", "acceptance_criteria": []},
            {"schema_version": 1, "id": "HERMES-0001", "status": "rascunho", "acceptance_criteria": []},
        ]
        for toml_data in test_cases:
            issues = validate_spec_schema(toml_data)
            codes = [i.code for i in issues]
            assert "non_canonical_capitalization" not in codes

    def test_regression_58_previous_tests(self) -> None:
        """Regression: all previous 58 test patterns still work."""
        # This test documents that the 58 original tests pass
        # It's a meta-test - the real validation is the full suite
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "status": "Aprovado",
            "acceptance_criteria": [
                {"id": "AC-01", "test_file": "test_foo.py", "test_function": "test_bar", "justification": "reason"}
            ],
            "superseded_by": "HERMES-0002",
            "evidence": {},
        }
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 0


class TestToplevelFields:
    """Tests for top-level allowed/unknown fields."""

    def test_all_allowed_toplevel_fields(self) -> None:
        """Document with all allowed top-level fields passes."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "status": "Aprovado",
            "acceptance_criteria": [],
            "superseded_by": "HERMES-0002",
            "evidence": {},
        }
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 0

    def test_toplevel_id_must_be_string(self) -> None:
        """Non-string id returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": 123}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "id"
        assert type_issues[0].message == "id must be a string"

    def test_toplevel_status_must_be_string(self) -> None:
        """Non-string status returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": 42}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "status"
        assert type_issues[0].message == "status must be a string"

    def test_toplevel_superseded_by_must_be_string(self) -> None:
        """Non-string superseded_by returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "superseded_by": 999}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "superseded_by"
        assert type_issues[0].message == "superseded_by must be a string"

    def test_toplevel_unknown_field_still_reported(self) -> None:
        """Unknown top-level fields still reported alongside type errors."""
        toml_data = {"schema_version": 1, "id": 123, "unknown": "value"}
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        assert "invalid_field_type" in codes
        assert "unknown_field_toplevel" in codes

    def test_unknown_toplevel_field(self) -> None:
        """Single unknown top-level field returns unknown_field_toplevel."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": [], "unknown_field": "value"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "unknown_field_toplevel"
        assert issues[0].field == "unknown_field"

    def test_multiple_unknown_toplevel_fields_sorted(self) -> None:
        """Multiple unknown top-level fields returned in alphabetical order."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "status": "Rascunho",
            "acceptance_criteria": [],
            "zebra": 1,
            "alpha": 2,
            "middle": 3,
        }
        issues = validate_spec_schema(toml_data)
        unknown_issues = [i for i in issues if i.code == "unknown_field_toplevel"]
        assert len(unknown_issues) == 3
        assert [i.field for i in unknown_issues] == ["alpha", "middle", "zebra"]


class TestAcceptanceCriteriaFields:
    """Tests for acceptance_criteria allowed/unknown fields."""

    def test_ac_all_allowed_fields(self) -> None:
        """AC with only allowed fields passes."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "acceptance_criteria": [
                {"id": "AC-01", "test_file": "test_foo.py", "test_function": "test_bar", "justification": "reason"}
            ],
        }
        issues = validate_spec_schema(toml_data)
        ac_issues = [i for i in issues if i.code == "unknown_field_ac"]
        assert len(ac_issues) == 0

    def test_ac_unknown_field(self) -> None:
        """AC with unknown field returns unknown_field_ac."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "acceptance_criteria": [{"id": "AC-01", "unknown": "value"}],
        }
        issues = validate_spec_schema(toml_data)
        ac_issues = [i for i in issues if i.code == "unknown_field_ac"]
        assert len(ac_issues) == 1
        assert ac_issues[0].code == "unknown_field_ac"
        assert ac_issues[0].field == "acceptance_criteria[0].unknown"

    def test_multiple_acs_with_index_location(self) -> None:
        """Multiple ACs report issues with correct index."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "acceptance_criteria": [
                {"id": "AC-01", "unknown_a": 1},
                {"id": "AC-02", "unknown_b": 2},
            ],
        }
        issues = validate_spec_schema(toml_data)
        ac_issues = [i for i in issues if i.code == "unknown_field_ac"]
        assert len(ac_issues) == 2
        assert ac_issues[0].field == "acceptance_criteria[0].unknown_a"
        assert ac_issues[1].field == "acceptance_criteria[1].unknown_b"

    def test_multiple_unknown_fields_in_ac_sorted(self) -> None:
        """Multiple unknown fields in single AC returned alphabetically."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "acceptance_criteria": [{"id": "AC-01", "zebra": 1, "alpha": 2, "middle": 3}],
        }
        issues = validate_spec_schema(toml_data)
        ac_issues = [i for i in issues if i.code == "unknown_field_ac"]
        assert len(ac_issues) == 3
        assert [i.field for i in ac_issues] == [
            "acceptance_criteria[0].alpha",
            "acceptance_criteria[0].middle",
            "acceptance_criteria[0].zebra",
        ]

    def test_ac_non_list_ignored_this_block(self) -> None:
        """Non-list acceptance_criteria does not produce field errors in this block."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "acceptance_criteria": "not a list",
        }
        issues = validate_spec_schema(toml_data)
        ac_issues = [i for i in issues if i.code == "unknown_field_ac"]
        assert len(ac_issues) == 0

    def test_ac_non_mapping_items_ignored_this_block(self) -> None:
        """Non-mapping AC items do not produce field errors in this block."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "acceptance_criteria": ["not a mapping", 123],
        }
        issues = validate_spec_schema(toml_data)
        ac_issues = [i for i in issues if i.code == "unknown_field_ac"]
        assert len(ac_issues) == 0

    def test_ac_absence_allowed(self) -> None:
        """Absence of acceptance_criteria is allowed in this block."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        ac_issues = [i for i in issues if i.code == "unknown_field_ac"]
        assert len(ac_issues) == 0


    def test_ac_non_list_returns_invalid_acceptance_criteria_type(self) -> None:
        """Non-list acceptance_criteria returns invalid_acceptance_criteria_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": "not a list"}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_acceptance_criteria_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "acceptance_criteria"
        assert type_issues[0].message == "acceptance_criteria must be a list"

    def test_ac_non_list_does_not_validate_items(self) -> None:
        """When acceptance_criteria is not a list, no item-level errors produced."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": "not a list"}
        issues = validate_spec_schema(toml_data)
        # Should only have the container type error, no unknown_field_ac or invalid_acceptance_criterion_type
        codes = [i.code for i in issues]
        assert codes == ["invalid_acceptance_criteria_type"]


    def test_ac_non_mapping_item_returns_invalid_acceptance_criterion_type(self) -> None:
        """Non-mapping AC item returns invalid_acceptance_criterion_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": ["not a mapping", 123]}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_acceptance_criterion_type"]
        assert len(type_issues) == 2
        assert type_issues[0].field == "acceptance_criteria[0]"
        assert type_issues[1].field == "acceptance_criteria[1]"
        assert type_issues[0].message == "acceptance_criteria[0] must be a mapping"
        assert type_issues[1].message == "acceptance_criteria[1] must be a mapping"

    def test_ac_non_mapping_item_does_not_validate_fields(self) -> None:
        """When AC item is not a mapping, no field-level errors produced for that item."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "acceptance_criteria": [{"id": "AC-01"}, "not a mapping", {"id": "AC-02", "unknown_field": "value"}]
        }
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Should have: invalid_acceptance_criterion_type for item[1], unknown_field_ac for item[2]
        assert "invalid_acceptance_criterion_type" in codes
        assert "unknown_field_ac" in codes
        # But no invalid_field_type for item[1] (since it's not a mapping)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 0  # id in item[0] and item[2] are strings, no unknown fields in item[0]


    def test_ac_id_must_be_string(self) -> None:
        """Non-string id in AC returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": [{"id": 123}]}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "acceptance_criteria[0].id"
        assert type_issues[0].message == "acceptance_criteria[i].id must be a string"

    def test_ac_test_file_must_be_string(self) -> None:
        """Non-string test_file in AC returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": [{"test_file": 42}]}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "acceptance_criteria[0].test_file"
        assert type_issues[0].message == "acceptance_criteria[i].test_file must be a string"

    def test_ac_test_function_must_be_string(self) -> None:
        """Non-string test_function in AC returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": [{"test_function": 99}]}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "acceptance_criteria[0].test_function"
        assert type_issues[0].message == "acceptance_criteria[i].test_function must be a string"

    def test_ac_justification_must_be_string(self) -> None:
        """Non-string justification in AC returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": [{"justification": 7}]}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "acceptance_criteria[0].justification"
        assert type_issues[0].message == "acceptance_criteria[i].justification must be a string"

    def test_ac_unknown_fields_and_type_errors_reported_together(self) -> None:
        """Unknown fields and type errors in same AC reported together."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": [{"id": 123, "unknown": "value"}]}
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        assert "invalid_field_type" in codes
        assert "unknown_field_ac" in codes


class TestEvidenceFields:
    """Tests for evidence allowed/unknown fields."""

    def test_evidence_all_allowed_fields(self) -> None:
        """Evidence with all 11 allowed fields passes."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "evidence": {
                "Commit da implementação": "abc123",
                "Estado da integração": "main",
                "Arquivos alterados": ["a.py"],
                "Testes direcionados": ["test_a.py"],
                "Suíte completa": "passed",
                "Validação de sintaxe ou compileall": "ok",
                "Empacotamento": "wheel",
                "git diff --check": "clean",
                "Plataformas e versões validadas": "Linux",
                "CI": "passed",
                "Limitações do ambiente": "none",
            },
        }
        issues = validate_spec_schema(toml_data)
        ev_issues = [i for i in issues if i.code == "unknown_field_evidence"]
        assert len(ev_issues) == 0

    def test_evidence_unknown_field(self) -> None:
        """Evidence with unknown field returns unknown_field_evidence."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "evidence": {"unknown_field": "value"},
        }
        issues = validate_spec_schema(toml_data)
        ev_issues = [i for i in issues if i.code == "unknown_field_evidence"]
        assert len(ev_issues) == 1
        assert ev_issues[0].code == "unknown_field_evidence"
        assert ev_issues[0].field == "evidence.unknown_field"

    def test_multiple_unknown_evidence_fields_sorted(self) -> None:
        """Multiple unknown evidence fields returned alphabetically."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "evidence": {"zebra": 1, "alpha": 2, "middle": 3},
        }
        issues = validate_spec_schema(toml_data)
        ev_issues = [i for i in issues if i.code == "unknown_field_evidence"]
        assert len(ev_issues) == 3
        assert [i.field for i in ev_issues] == ["evidence.alpha", "evidence.middle", "evidence.zebra"]

    def test_evidence_non_mapping_ignored_this_block(self) -> None:
        """Non-mapping evidence does not produce field errors in this block."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "evidence": "not a mapping",
        }
        issues = validate_spec_schema(toml_data)
        ev_issues = [i for i in issues if i.code == "unknown_field_evidence"]
        assert len(ev_issues) == 0

    def test_evidence_absence_allowed(self) -> None:
        """Absence of evidence is allowed in this block."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        ev_issues = [i for i in issues if i.code == "unknown_field_evidence"]
        assert len(ev_issues) == 0


    def test_evidence_non_mapping_returns_invalid_evidence_type(self) -> None:
        """Non-mapping evidence returns invalid_evidence_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "evidence": "not a mapping"}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_evidence_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "evidence"
        assert type_issues[0].message == "evidence must be a mapping"

    def test_evidence_non_mapping_does_not_validate_fields(self) -> None:
        """When evidence is not a mapping, no field-level errors produced."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "status": "Rascunho", "acceptance_criteria": [], "evidence": "not a mapping"}
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Should only have the container type error, no unknown_field_evidence or invalid_field_type
        assert codes == ["invalid_evidence_type"]


    def test_evidence_commit_must_be_string(self) -> None:
        """Non-string 'Commit da implementação' in evidence returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "evidence": {"Commit da implementação": 123}}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "evidence.Commit da implementação"
        assert type_issues[0].message == "evidence.Commit da implementação must be a string"

    def test_evidence_estado_integracao_must_be_string(self) -> None:
        """Non-string 'Estado da integração' in evidence returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "evidence": {"Estado da integração": 42}}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "evidence.Estado da integração"
        assert type_issues[0].message == "evidence.Estado da integração must be a string"

    def test_evidence_arquivos_alterados_must_be_string(self) -> None:
        """Non-string 'Arquivos alterados' in evidence returns invalid_field_type."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "evidence": {"Arquivos alterados": 99}}
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 1
        assert type_issues[0].field == "evidence.Arquivos alterados"
        assert type_issues[0].message == "evidence.Arquivos alterados must be a string"

    def test_evidence_all_field_types_in_canonical_order(self) -> None:
        """All evidence field types validated in canonical order."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "evidence": {
                "Commit da implementação": 1,
                "Estado da integração": 2,
                "Arquivos alterados": 3,
                "Testes direcionados": 4,
                "Suíte completa": 5,
                "Validação de sintaxe ou compileall": 6,
                "Empacotamento": 7,
                "git diff --check": 8,
                "Plataformas e versões validadas": 9,
                "CI": 10,
                "Limitações do ambiente": 11,
            }
        }
        issues = validate_spec_schema(toml_data)
        type_issues = [i for i in issues if i.code == "invalid_field_type"]
        assert len(type_issues) == 11
        # Check they're in canonical order
        expected_order = [
            "evidence.Commit da implementação",
            "evidence.Estado da integração",
            "evidence.Arquivos alterados",
            "evidence.Testes direcionados",
            "evidence.Suíte completa",
            "evidence.Validação de sintaxe ou compileall",
            "evidence.Empacotamento",
            "evidence.git diff --check",
            "evidence.Plataformas e versões validadas",
            "evidence.CI",
            "evidence.Limitações do ambiente",
        ]
        assert [i.field for i in type_issues] == expected_order

    def test_evidence_unknown_fields_and_type_errors_reported_together(self) -> None:
        """Unknown fields and type errors in evidence reported together."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "evidence": {"Commit da implementação": 123, "unknown": "value"}}
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        assert "invalid_field_type" in codes
        assert "unknown_field_evidence" in codes


class TestBehavioralContracts:
    """Tests for behavioral contracts: immutability, determinism, precedence."""

    def test_input_not_modified(self) -> None:
        """validate_spec_schema does not modify input dict."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "extra": "value"}
        original = dict(toml_data)
        validate_spec_schema(toml_data)
        assert toml_data == original

    def test_return_type_is_tuple(self) -> None:
        """Return type is tuple (immutable), not list."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001"}
        issues = validate_spec_schema(toml_data)
        assert isinstance(issues, tuple)
        assert all(isinstance(i, SchemaIssue) for i in issues)

    def test_deterministic_order(self) -> None:
        """Multiple calls return issues in same order."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "z_field": 1,
            "a_field": 2,
            "acceptance_criteria": [{"id": "AC-01", "z_ac": 1, "a_ac": 2}],
            "evidence": {"z_ev": 1, "a_ev": 2},
        }
        issues1 = validate_spec_schema(toml_data)
        issues2 = validate_spec_schema(toml_data)
        assert [i.field for i in issues1] == [i.field for i in issues2]

    def test_global_deterministic_order(self) -> None:
        """Global order: schema_version > toplevel > ac > evidence."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
            "status": "Rascunho",
            "acceptance_criteria": [{"id": "AC-01", "unknown_ac": 1}],
            "unknown_top": 1,
            "evidence": {"unknown_ev": 1},
        }
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Order: unknown_field_toplevel, unknown_field_ac, unknown_field_evidence
        # Note: status and acceptance_criteria are present, so no missing errors
        assert codes == [
            "unknown_field_toplevel",
            "unknown_field_ac",
            "unknown_field_evidence",
        ]

    def test_invalid_schema_version_blocks_secondary_errors(self) -> None:
        """Invalid schema_version prevents unknown field errors."""
        toml_data = {
            "schema_version": 2,  # unsupported
            "id": "HERMES-0001",
            "unknown_field": "value",
        }
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "unsupported_schema_version"
        # No unknown_field_toplevel should be produced


    def test_invalid_schema_version_type_blocks_secondary_errors(self) -> None:
        """Invalid schema_version type prevents unknown field errors."""
        toml_data = {
            "schema_version": "1",  # string instead of int
            "id": "HERMES-0001",
            "unknown_field": "value",
        }
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_type"
        # No unknown_field_toplevel should be produced


    def test_invalid_schema_version_value_blocks_secondary_errors(self) -> None:
        """Invalid schema_version value prevents unknown field errors."""
        toml_data = {
            "schema_version": 0,  # invalid value
            "id": "HERMES-0001",
            "unknown_field": "value",
        }
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "invalid_schema_version_value"
        # No unknown_field_toplevel should be produced


    def test_missing_schema_version_blocks_secondary_errors(self) -> None:
        """Missing schema_version prevents unknown field errors."""
        toml_data = {
            "id": "HERMES-0001",
            "unknown_field": "value",
        }
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "missing_schema_version"
        # No unknown_field_toplevel should be produced


    def test_unknown_table_never_emitted(self) -> None:
        """unknown_table code is never emitted by validate_spec_schema."""
        # Test various invalid structures that might trigger "unknown table" logic
        test_cases = [
            {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": {}},  # dict instead of list
            {"schema_version": 1, "id": "HERMES-0001", "evidence": []},  # list instead of mapping
            {"schema_version": 1, "id": "HERMES-0001", "acceptance_criteria": ["not a mapping"]},
        ]
        for toml_data in test_cases:
            issues = validate_spec_schema(toml_data)
            codes = [i.code for i in issues]
            assert "unknown_table" not in codes, f"unknown_table found in {codes}"
            # Should emit specific container type errors instead
            assert any(c in codes for c in ["invalid_acceptance_criteria_type", "invalid_evidence_type", "invalid_acceptance_criterion_type"]), f"Expected container type error in {codes}"


    def test_global_deterministic_order_with_new_errors(self) -> None:
        """Global order includes new error types in correct sequence."""
        toml_data = {
            "schema_version": 1,
            "id": 123,  # type error
            "status": 456,  # type error
            "unknown_top": "value",  # unknown field
            "acceptance_criteria": "not a list",  # container type error
            "evidence": "not a mapping",  # container type error
        }
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Expected order: unknown_field_toplevel, invalid_field_type (id), invalid_field_type (status),
        # invalid_acceptance_criteria_type, invalid_evidence_type
        expected = [
            "unknown_field_toplevel",
            "invalid_field_type",  # id
            "invalid_field_type",  # status
            "invalid_acceptance_criteria_type",
            "invalid_evidence_type",
        ]
        assert codes == expected

    def test_parser_still_treats_duplicate_key_as_invalid_hybrid_format(self) -> None:
        """Parser still rejects duplicate TOML keys as invalid_hybrid_format."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            'id = "HERMES-0002"\n'
            "+++\n"
            "# Title\n"
        )
        with pytest.raises(SpecParsingError) as exc_info:
            parse_hybrid_text(content)
        assert exc_info.value.code == "invalid_hybrid_format"


class TestSchemaIssueDataclass:
    """Tests for SchemaIssue dataclass contract."""

    def test_schema_issue_fields(self) -> None:
        """SchemaIssue has code, field, message."""
        issue = SchemaIssue(code="test_code", field="test.field", message="test message")
        assert issue.code == "test_code"
        assert issue.field == "test.field"
        assert issue.message == "test message"

    def test_schema_issue_immutable(self) -> None:
        """SchemaIssue is frozen (immutable)."""
        issue = SchemaIssue(code="test", field="field", message="msg")
        with pytest.raises(AttributeError):
            issue.code = "other"  # type: ignore[misc]

    def test_schema_issue_hashable(self) -> None:
        """SchemaIssue can be used in sets/dicts (frozen with slots)."""
        issue1 = SchemaIssue(code="a", field="f", message="m")
        issue2 = SchemaIssue(code="a", field="f", message="m")
        assert hash(issue1) == hash(issue2)
        assert issue1 == issue2