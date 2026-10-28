"""Contract tests for the HERMES-0026 source evidence primitive."""

import ast
from pathlib import Path

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills.finding_models import EvidenceRef
from hermes_ops.skills.source_evidence import parse_source_locator, source_locator


def _node(line: int = 7) -> ast.AST:
    node = ast.parse("call()")
    node.body[0].lineno = line
    return node.body[0]


def test_source_locator_is_relative_nested_and_deterministic() -> None:
    """Spec: HERMES-0026 / AC-07, AC-08."""
    assert source_locator("src/nested/example.py", _node()) == "src/nested/example.py:7"
    assert source_locator("src/nested/example.py", _node()) == "src/nested/example.py:7"


@pytest.mark.parametrize("path", ["C:/host/secret.py", "/host/secret.py", "../secret.py"])
def test_source_locator_rejects_unsafe_paths(path: str) -> None:
    """Spec: HERMES-0026 / AC-08."""
    with pytest.raises(SkillExecutionError) as caught:
        source_locator(path, _node())
    assert caught.value.code == "FINDING_NORMALIZATION_INVALID"


@pytest.mark.parametrize("line", [0, -1, True])
def test_source_locator_rejects_invalid_line(line: int) -> None:
    """Spec: HERMES-0026 / AC-07."""
    with pytest.raises(SkillExecutionError) as caught:
        source_locator("src/example.py", _node(line))
    assert caught.value.code == "FINDING_NORMALIZATION_INVALID"


def test_parse_source_locator_preserves_evidence_contract() -> None:
    """Spec: HERMES-0026 / AC-07, AC-08."""
    assert parse_source_locator("src/nested/example.py:19") == EvidenceRef(
        "src/nested/example.py", 19, 19
    )


@pytest.mark.parametrize(
    "locator", ["missing-line", "src/example.py:not-a-line", "C:/host.py:2", "src/a.py:0"]
)
def test_parse_source_locator_fails_closed(locator: str) -> None:
    """Spec: HERMES-0026 / AC-07, AC-08."""
    with pytest.raises(SkillExecutionError) as caught:
        parse_source_locator(locator)
    assert caught.value.code == "FINDING_NORMALIZATION_INVALID"


def test_structural_helpers_have_no_consumer_hardcode() -> None:
    """Spec: HERMES-0026 / AC-25."""
    forbidden = (
        "lucre",
        "awaiting_client_type",
        "cancel_batch",
        "whatsapp",
        "trello",
        "c:\\users\\danilo",
    )
    root = Path(__file__).parents[1] / "src" / "hermes_ops" / "skills"
    text = "\n".join(
        (root / name).read_text(encoding="utf-8").lower()
        for name in ("structural_ast.py", "source_evidence.py")
    )
    assert not any(value in text for value in forbidden)
