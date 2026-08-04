from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from hermes_ops.core.errors import SpecParsingError


@dataclass(frozen=True, slots=True)
class HybridParseResult:
    """Result of parsing a hybrid TOML + Markdown document.

    Attributes:
        toml_data: The parsed TOML front matter as a dictionary.
        markdown_body: The Markdown content after the second delimiter.
    """

    toml_data: dict[str, object]
    markdown_body: str


DELIMITER_LF = "+++\n"
DELIMITER_CRLF = "+++\r\n"


def _split_hybrid_content(content: str) -> tuple[str, str] | None:
    """Split hybrid content into TOML text and Markdown body.

    Handles both LF and CRLF delimiters.

    Args:
        content: The full document content.

    Returns:
        Tuple of (toml_text, markdown_body) if valid format, None otherwise.
    """
    # Check for LF delimiter first
    if content.startswith(DELIMITER_LF):
        first_delim_len = len(DELIMITER_LF)
        second_delim = DELIMITER_LF
    elif content.startswith(DELIMITER_CRLF):
        first_delim_len = len(DELIMITER_CRLF)
        second_delim = DELIMITER_CRLF
    else:
        return None

    # Find second delimiter
    second_delim_pos = content.find(second_delim, first_delim_len)
    if second_delim_pos == -1:
        return None

    # Extract TOML text (between delimiters)
    toml_text = content[first_delim_len:second_delim_pos]

    # Extract Markdown body (after second delimiter)
    markdown_body = content[second_delim_pos + len(second_delim):]

    return toml_text, markdown_body


def parse_hybrid_text(content: str) -> HybridParseResult:
    """Parse a hybrid TOML + Markdown document from text.

    The document must start with '+++\\n' or '+++\\r\\n' delimiter, followed by TOML front matter,
    then a second matching delimiter, and finally the Markdown body.

    Args:
        content: The full document content as a string.

    Returns:
        HybridParseResult with parsed TOML data and Markdown body.

    Raises:
        SpecParsingError: If the format is invalid (missing delimiters, invalid TOML).
    """
    split_result = _split_hybrid_content(content)
    if split_result is None:
        raise SpecParsingError(
            "Document does not conform to hybrid format: missing opening or closing '+++' delimiter",
            code="invalid_hybrid_format",
        )

    toml_text, markdown_body = split_result

    try:
        toml_data = tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError as e:
        raise SpecParsingError(
            f"Invalid TOML in front matter: {e}",
            code="invalid_hybrid_format",
        ) from None

    return HybridParseResult(toml_data=toml_data, markdown_body=markdown_body)


def parse_hybrid_file(path: Path) -> HybridParseResult:
    """Parse a hybrid TOML + Markdown document from a file.

    Args:
        path: Path to the specification file.

    Returns:
        HybridParseResult with parsed TOML data and Markdown body.

    Raises:
        SpecParsingError: If the format is invalid (missing delimiters, invalid TOML).
        OSError: If the file cannot be read.
    """
    content = path.read_text(encoding="utf-8")
    return parse_hybrid_text(content)