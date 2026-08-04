from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from hermes_ops.core.errors import SpecParsingError
from hermes_ops.core.hybrid_parser import HybridParseResult, parse_hybrid_text, parse_hybrid_file


class TestParseHybridText:
    """Tests for parse_hybrid_text function."""

    def test_valid_document_with_lf(self) -> None:
        """Valid document with LF line endings."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            'status = "Aprovado"\n'
            "+++\n"
            "# HERMES-0001 — Título\n\n"
            "Conteúdo markdown.\n"
        )
        result = parse_hybrid_text(content)
        assert isinstance(result, HybridParseResult)
        assert result.toml_data == {
            "schema_version": 1,
            "id": "HERMES-0001",
            "status": "Aprovado",
        }
        assert result.markdown_body == "# HERMES-0001 — Título\n\nConteúdo markdown.\n"

    def test_valid_document_with_crlf(self) -> None:
        """Valid document with CRLF line endings."""
        content = (
            "+++\r\n"
            'schema_version = 1\r\n'
            'id = "HERMES-0002"\r\n'
            'status = "Rascunho"\r\n'
            "+++\r\n"
            "# HERMES-0002 — Título\r\n\r\n"
            "Conteúdo markdown.\r\n"
        )
        result = parse_hybrid_text(content)
        assert isinstance(result, HybridParseResult)
        assert result.toml_data == {
            "schema_version": 1,
            "id": "HERMES-0002",
            "status": "Rascunho",
        }
        assert result.markdown_body == "# HERMES-0002 — Título\r\n\r\nConteúdo markdown.\r\n"

    def test_missing_opening_delimiter(self) -> None:
        """Missing opening delimiter raises SpecParsingError with invalid_hybrid_format code."""
        content = (
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            "+++\n"
            "# HERMES-0001 — Título\n"
        )
        with pytest.raises(SpecParsingError) as exc_info:
            parse_hybrid_text(content)
        assert exc_info.value.code == "invalid_hybrid_format"

    def test_missing_closing_delimiter(self) -> None:
        """Missing closing delimiter raises SpecParsingError with invalid_hybrid_format code."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            "# HERMES-0001 — Título\n"
        )
        with pytest.raises(SpecParsingError) as exc_info:
            parse_hybrid_text(content)
        assert exc_info.value.code == "invalid_hybrid_format"

    def test_invalid_toml_syntax(self) -> None:
        """Invalid TOML syntax raises SpecParsingError with invalid_hybrid_format code."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            'status = "Aprovado"\n'
            "invalid toml\n"
            "+++\n"
            "# HERMES-0001 — Título\n"
        )
        with pytest.raises(SpecParsingError) as exc_info:
            parse_hybrid_text(content)
        assert exc_info.value.code == "invalid_hybrid_format"

    def test_duplicate_key_in_toml(self) -> None:
        """Duplicate key in TOML raises SpecParsingError with invalid_hybrid_format code."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            'id = "HERMES-0002"\n'
            "+++\n"
            "# HERMES-0001 — Título\n"
        )
        with pytest.raises(SpecParsingError) as exc_info:
            parse_hybrid_text(content)
        assert exc_info.value.code == "invalid_hybrid_format"

    def test_empty_markdown_body(self) -> None:
        """Empty Markdown body is accepted."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            "+++\n"
        )
        result = parse_hybrid_text(content)
        assert result.toml_data == {"schema_version": 1, "id": "HERMES-0001"}
        assert result.markdown_body == ""

    def test_markdown_body_contains_delimiter(self) -> None:
        """Subsequent '+++' in Markdown body does not affect parsing."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            "+++\n"
            "# HERMES-0001 — Título\n\n"
            "+++\n\n"
            "Outro conteúdo.\n"
        )
        result = parse_hybrid_text(content)
        assert result.toml_data == {"schema_version": 1, "id": "HERMES-0001"}
        assert result.markdown_body == "# HERMES-0001 — Título\n\n+++\n\nOutro conteúdo.\n"

    def test_utf8_in_toml_and_markdown(self) -> None:
        """UTF-8 characters in TOML and Markdown are handled correctly."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            'titulo = "Título com acentuação 🎉"\n'
            "+++\n"
            "# HERMES-0001 — Título com acentuação 🎉\n\n"
            "Conteúdo com emoji 🚀 e caracteres especiais: àáãçéêíóôõú.\n"
        )
        result = parse_hybrid_text(content)
        assert result.toml_data == {
            "schema_version": 1,
            "id": "HERMES-0001",
            "titulo": "Título com acentuação 🎉",
        }
        assert "🎉" in result.markdown_body
        assert "🚀" in result.markdown_body
        assert "àáãçéêíóôõú" in result.markdown_body

    def test_only_first_two_delimiters_used(self) -> None:
        """Only the first two delimiters are used for parsing."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            "+++\n"
            "+++\n"
            'id = "HERMES-0002"\n'
            "+++\n"
            "# HERMES-0001 — Título\n"
        )
        result = parse_hybrid_text(content)
        assert result.toml_data == {"schema_version": 1, "id": "HERMES-0001"}
        assert result.markdown_body == "+++\nid = \"HERMES-0002\"\n+++\n# HERMES-0001 — Título\n"

    def test_error_code_is_stable_invalid_hybrid_format(self) -> None:
        """Public error code is consistently invalid_hybrid_format."""
        test_cases = [
            'id = "HERMES-0001"\n+++\n# Title\n',  # missing opening
            "+++\nid = \"HERMES-0001\"\n# Title\n",  # missing closing
            "+++\ninvalid toml\n+++\n# Title\n",  # invalid TOML
            "+++\nid = 1\nid = 2\n+++\n# Title\n",  # duplicate key
        ]
        for content in test_cases:
            with pytest.raises(SpecParsingError) as exc_info:
                parse_hybrid_text(content)
            assert exc_info.value.code == "invalid_hybrid_format"

    def test_toml_decode_error_message_not_used_as_public_code(self) -> None:
        """The original TOMLDecodeError message is not used as the public error code."""
        content = (
            "+++\n"
            "invalid toml [\n"
            "+++\n"
            "# Title\n"
        )
        with pytest.raises(SpecParsingError) as exc_info:
            parse_hybrid_text(content)
        # The code should be our stable code, not the tomllib error message
        assert exc_info.value.code == "invalid_hybrid_format"
        # The message can mention the error but code is stable
        assert "invalid" in str(exc_info.value).lower() or "toml" in str(exc_info.value).lower()


class TestParseHybridFile:
    """Tests for parse_hybrid_file function."""

    def test_parse_file_success(self) -> None:
        """Parsing a valid file returns HybridParseResult."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            "+++\n"
            "# HERMES-0001 — Título\n\n"
            "Conteúdo.\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = Path(f.name)

        try:
            result = parse_hybrid_file(path)
            assert isinstance(result, HybridParseResult)
            assert result.toml_data == {"schema_version": 1, "id": "HERMES-0001"}
            assert result.markdown_body == "# HERMES-0001 — Título\n\nConteúdo.\n"
        finally:
            path.unlink(missing_ok=True)

    def test_parse_file_invalid_format(self) -> None:
        """Parsing an invalid file raises SpecParsingError."""
        content = 'id = "HERMES-0001"\n'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = Path(f.name)

        try:
            with pytest.raises(SpecParsingError) as exc_info:
                parse_hybrid_file(path)
            assert exc_info.value.code == "invalid_hybrid_format"
        finally:
            path.unlink(missing_ok=True)

    def test_parsing_does_not_modify_input_file(self) -> None:
        """Parsing does not modify the input file."""
        content = (
            "+++\n"
            'schema_version = 1\n'
            'id = "HERMES-0001"\n'
            "+++\n"
            "# HERMES-0001 — Título\n\n"
            "Conteúdo original.\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = Path(f.name)

        try:
            parse_hybrid_file(path)
            # Read file again and verify it's unchanged
            after_content = path.read_text(encoding="utf-8")
            assert after_content == content
        finally:
            path.unlink(missing_ok=True)

    def test_parse_file_raises_oserror_on_missing_file(self) -> None:
        """Parsing a non-existent file raises OSError."""
        path = Path("/nonexistent/path/spec.md")
        with pytest.raises(OSError):
            parse_hybrid_file(path)