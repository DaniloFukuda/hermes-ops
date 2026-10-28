"""Contract tests for the HERMES-0026 structural AST primitive."""

import ast

import pytest

from hermes_ops.skills.structural_ast import terminal_symbol


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("consumer", "consumer"),
        ("adapter.bind", "bind"),
        ("repository.bind_existing", "bind_existing"),
        ("module.service.call", "call"),
    ],
)
def test_terminal_symbol_returns_only_static_terminal_name(
    expression: str, expected: str
) -> None:
    """Spec: HERMES-0026 / AC-01, AC-02."""
    node = ast.parse(expression, mode="eval").body

    assert terminal_symbol(node) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "callbacks[name]",
        "factory()",
        "lambda: None",
        "choose(left, right)",
    ],
)
def test_terminal_symbol_fails_closed_for_dynamic_callable(expression: str) -> None:
    """Spec: HERMES-0026 / AC-03."""
    node = ast.parse(expression, mode="eval").body

    assert terminal_symbol(node) is None
