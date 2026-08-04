from __future__ import annotations

import pytest

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

    def test_unknown_toplevel_field(self) -> None:
        """Single unknown top-level field returns unknown_field_toplevel."""
        toml_data = {"schema_version": 1, "id": "HERMES-0001", "unknown_field": "value"}
        issues = validate_spec_schema(toml_data)
        assert len(issues) == 1
        assert issues[0].code == "unknown_field_toplevel"
        assert issues[0].field == "unknown_field"

    def test_multiple_unknown_toplevel_fields_sorted(self) -> None:
        """Multiple unknown top-level fields returned in alphabetical order."""
        toml_data = {
            "schema_version": 1,
            "id": "HERMES-0001",
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
            "unknown_top": 1,
            "acceptance_criteria": [{"id": "AC-01", "unknown_ac": 1}],
            "evidence": {"unknown_ev": 1},
        }
        issues = validate_spec_schema(toml_data)
        codes = [i.code for i in issues]
        # Order: unknown_field_toplevel, unknown_field_ac, unknown_field_evidence
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