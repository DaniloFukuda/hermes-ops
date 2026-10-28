"""Small, pure AST primitives shared by structural analyzers."""

from __future__ import annotations

import ast


def terminal_symbol(node: ast.AST) -> str | None:
    """Return the terminal syntactic symbol of a statically named callable."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
