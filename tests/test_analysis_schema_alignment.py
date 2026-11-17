from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from hermes_ops.analysis.builder import canonical_json
from hermes_ops.analysis.loader import load_evidence_pack, parse_evidence_pack
from hermes_ops.core.errors import AnalysisError
from tests.analysis_helpers import make_pack


def _serialized_pack(root: Path, *, scope: tuple[str, ...]) -> tuple[Path, dict[str, object]]:
    serialized = json.dumps(
        asdict(replace(make_pack(root / "project"), structural_scope=scope)),
        ensure_ascii=False,
    )
    document = json.loads(serialized)
    path = root / "pack.json"
    path.write_text(serialized, encoding="utf-8")
    return path, document


def test_current_pack_with_structural_scope_loads_and_preserves_value(tmp_path: Path) -> None:
    """Spec: HERMES-0016 / AC-01, AC-02, AC-06"""
    path, _ = _serialized_pack(tmp_path, scope=("src/core", "tests/core"))

    loaded = load_evidence_pack(path)

    assert loaded.structural_scope == ("src/core", "tests/core")


def test_loading_structural_scope_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0016 / AC-03"""
    path, _ = _serialized_pack(tmp_path, scope=("tests/core", "src/core"))

    first = load_evidence_pack(path)
    second = load_evidence_pack(path)

    assert first == second
    assert canonical_json(first) == canonical_json(second)
    assert first.structural_scope == ("tests/core", "src/core")


def test_unknown_root_field_remains_rejected(tmp_path: Path) -> None:
    """Spec: HERMES-0016 / AC-04"""
    _, document = _serialized_pack(tmp_path, scope=())
    document["unexpected_field"] = "must fail"

    with pytest.raises(AnalysisError) as caught:
        parse_evidence_pack(document)

    assert caught.value.code == "ANALYSIS_PACK_INVALID"


def test_legacy_pack_without_structural_scope_uses_model_default(tmp_path: Path) -> None:
    """Spec: HERMES-0016 / AC-05"""
    _, document = _serialized_pack(tmp_path, scope=("src/core",))
    del document["structural_scope"]

    loaded = parse_evidence_pack(document)

    assert loaded.structural_scope == ()
