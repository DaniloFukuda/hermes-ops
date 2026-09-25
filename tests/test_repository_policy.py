from pathlib import Path


def test_yaml_line_endings_are_declared_as_lf() -> None:
    root = Path(__file__).resolve().parents[1]
    attributes = (root / ".gitattributes").read_text(encoding="utf-8")
    assert "*.yml text eol=lf" in attributes
    assert "*.yaml text eol=lf" in attributes
