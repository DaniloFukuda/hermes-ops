from pathlib import Path


def test_ci_workflow_has_portability_matrix_and_required_steps() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "windows-latest" in text
    assert "ubuntu-latest" in text
    assert '"3.11"' in text
    assert '"3.13"' in text
    assert "python -m pytest" in text
    assert "python -m compileall" in text
    assert "python -m build" in text
    assert "python -m hermes_ops --help" in text
    assert "contents: read" in text
    lowered = text.lower()
    assert "pypi" not in lowered
    assert "deploy" not in lowered
    assert "publish" not in lowered

