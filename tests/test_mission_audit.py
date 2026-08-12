from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from hermes_ops.cli import main
from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills import SkillPolicy, SkillRisk, SkillRunInputs, discover_skills, run_skill
from hermes_ops.skills.mission_audit import build_evidence_pack, normalize_mission


def _policy() -> SkillPolicy:
    return SkillPolicy(SkillRisk.LOW, False, frozenset({"git"}))


def _project(root: Path) -> Path:
    (root / "tests").mkdir()
    (root / "invoice_service.py").write_text("class InvoiceService:\n    def process_batch(self): pass\n", encoding="utf-8")
    (root / "tests/test_invoice_service.py").write_text("from invoice_service import InvoiceService\ndef test_process_batch(): pass\n", encoding="utf-8")
    return root


def test_mission_audit_manifest_is_passive_and_exact(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-01, AC-38"""
    skill = discover_skills(Path(__file__).parents[1]).get_by_id("mission-audit")
    assert skill and skill.requires == () and not skill.allows_write
    assert run_skill(_project(tmp_path), "mission-audit", _policy(), inputs=SkillRunInputs("invoice batch process")).skill_id == "mission-audit"


def test_mission_is_required_and_other_skills_reject_it(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-02, AC-03"""
    with pytest.raises(SkillExecutionError): run_skill(tmp_path, "mission-audit", _policy())
    with pytest.raises(SkillExecutionError): run_skill(tmp_path, "code-audit", _policy(), inputs=SkillRunInputs("audit this"))


def test_mission_normalization_is_closed_and_bounded() -> None:
    """Spec: HERMES-0009 / AC-04, AC-05"""
    mission, terms = normalize_mission("  Auditar   emissão lote  ")
    assert mission == "Auditar emissão lote"
    assert {x.term for x in terms}.issuperset({"emissão", "emissao", "lote"})
    with pytest.raises(SkillExecutionError): normalize_mission("x")
    with pytest.raises(SkillExecutionError) as caught: normalize_mission(" ".join(f"term{i}" for i in range(25)))
    assert caught.value.code == "MISSION_TERM_LIMIT_EXCEEDED"


def test_no_signals_is_explicitly_insufficient(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-06, AC-31"""
    (tmp_path / "other.py").write_text("value = 1\n", encoding="utf-8")
    result = run_skill(tmp_path, "mission-audit", _policy(), inputs=SkillRunInputs("invoice batch process"))
    assert result.exit_code == 3 and result.status.value == "completed_with_insufficient_evidence"


def test_pack_has_traceable_regions_roles_scores_and_tests(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-18 through AC-30"""
    pack = build_evidence_pack(_project(tmp_path), "invoice batch process")
    assert pack.completeness.status == "sufficient"
    assert all(f.path and f.reasons and f.score >= 0 for f in pack.files)
    assert all(r.start_line <= r.end_line and r.reasons for r in pack.regions)
    assert any(r.kind == "import" and r.evidence_region for r in pack.relationships)
    assert pack.related_tests and any("test" in f.roles for f in pack.files)
    with pytest.raises(FrozenInstanceError): pack.mission = "changed"  # type: ignore[misc]


def test_every_relationship_has_a_materialized_evidence_region(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-49, AC-50"""
    pack = build_evidence_pack(_project(tmp_path), "invoice batch process")
    for relationship in pack.relationships:
        path, line_text = relationship.evidence_region.rsplit(":", 1)
        line = int(line_text)
        assert any(region.path == path and region.start_line <= line <= region.end_line for region in pack.regions)


def test_region_limit_drops_relationship_without_provenance_and_marks_omission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spec: HERMES-0009 / AC-50, AC-52"""
    import hermes_ops.skills.mission_audit as mission_audit

    (tmp_path / "seed.py").write_text("import alpha\nimport beta\n", encoding="utf-8")
    (tmp_path / "alpha.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "beta.py").write_text("VALUE = 2\n", encoding="utf-8")
    monkeypatch.setattr(mission_audit, "MAX_REGIONS", 1)
    first = build_evidence_pack(tmp_path, "audit seed module")
    second = build_evidence_pack(tmp_path, "audit seed module")
    assert first == second
    assert len(first.relationships) == 1
    assert first.relationships[0].evidence_region == "seed.py:1"
    assert all(item.evidence_region != "seed.py:2" for item in first.relationships)
    assert "SELECTION_CAP_REACHED" in first.limitations
    assert "CAP_OMISSION" in first.completeness.incompleteness_codes


def test_mission_pack_is_consumed_directly_by_hermes_0010(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-53; HERMES-0010 direct compatibility."""
    from hermes_ops.analysis.builder import build_analysis_request

    pack = build_evidence_pack(_project(tmp_path), "invoice batch process")
    request, digest = build_analysis_request(pack, "What evidence supports the invoice batch process?", 20_000)
    assert request.analysis_pack.source_schema_version == pack.schema_version
    assert request.analysis_pack.relationships
    assert digest


def test_reader_blocks_binary_invalid_encoding_and_linked_worktree(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-07 through AC-11, AC-39, AC-47, AC-48"""
    (tmp_path / "bad.py").write_bytes(b"x\0y")
    with pytest.raises(SkillExecutionError): build_evidence_pack(tmp_path, "audit bad module")
    (tmp_path / "bad.py").unlink(); (tmp_path / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
    with pytest.raises(SkillExecutionError): build_evidence_pack(tmp_path, "audit bad module")


def test_cli_text_json_and_semantic_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Spec: HERMES-0009 / AC-40, AC-41, AC-42"""
    target = _project(tmp_path)
    assert main(["skill","run","mission-audit","--project",str(target),"--mission","invoice batch process","--format","text"]) == 0
    text = capsys.readouterr().out
    assert "status=passed" in text and str(target) not in text and "does not assert defects" in text
    assert main(["skill","run","mission-audit","--project",str(target),"--mission","invoice batch process","--format","json"]) == 0
    payload=json.loads(capsys.readouterr().out); assert payload["evidence"][0]["details"]["target"] == "<PROJECT_ROOT>"


def test_target_shadowing_does_not_change_catalog(tmp_path: Path) -> None:
    """Spec: HERMES-0009 / AC-38, AC-46"""
    target=_project(tmp_path); (target/"skills/mission-audit").mkdir(parents=True); (target/"skills/mission-audit/SKILL.md").write_text("malicious",encoding="utf-8")
    assert run_skill(target,"mission-audit",_policy(),inputs=SkillRunInputs("invoice batch process")).exit_code==0


def test_lexical_selection_expands_literal_internal_import_exactly_one_hop(tmp_path: Path) -> None:
    """Regression: structural imports are evidence even without mission terms."""
    (tmp_path / "services").mkdir(); (tmp_path / "core").mkdir()
    (tmp_path / "services/batch_service.py").write_text(
        "from core import storage_gateway as repository\n\n"
        "def process_document_batch():\n    return repository.load()\n",
        encoding="utf-8",
    )
    (tmp_path / "core/storage_gateway.py").write_text(
        "from core import database_adapter\n\ndef load():\n    return database_adapter.read()\n",
        encoding="utf-8",
    )
    (tmp_path / "core/database_adapter.py").write_text("def read():\n    return []\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "document batch process")
    paths = {item.path for item in pack.files}
    assert "services/batch_service.py" in paths
    assert "core/storage_gateway.py" in paths
    assert "core/database_adapter.py" not in paths
    relation = next(item for item in pack.relationships if item.source == "services/batch_service.py")
    assert relation.target == "core/storage_gateway.py"
    assert relation.evidence_region == "services/batch_service.py:1"
    assert any(region.path == relation.source and region.start_line == 1 and "structural import" in region.reasons[0] for region in pack.regions)
    imported = next(item for item in pack.files if item.path == relation.target)
    assert imported.reasons == ("import seed from services/batch_service.py:1",)


def test_external_import_does_not_expand_outside_target(tmp_path: Path) -> None:
    """Regression: unresolved/external imports never escape the inventory."""
    (tmp_path / "document_batch.py").write_text("import requests\ndef process_document_batch(): pass\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "document batch process")
    assert {item.path for item in pack.files} == {"document_batch.py"}
    assert not pack.relationships


def test_uncovered_central_concept_keeps_large_pack_insufficient(tmp_path: Path) -> None:
    """Regression: volume cannot replace coverage of central mission terms."""
    (tmp_path / "tests").mkdir()
    for index in range(20):
        (tmp_path / f"invoice_batch_{index}.py").write_text(f"def invoice_batch_{index}(): pass\n", encoding="utf-8")
    (tmp_path / "tests/test_invoice_batch.py").write_text("from invoice_batch_0 import invoice_batch_0\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "invoice batch settlement")
    assert pack.completeness.status == "insufficient"
    assert "settlement" in pack.completeness.unmatched_terms
    assert "UNCOVERED_CENTRAL_TERMS" in pack.completeness.incompleteness_codes
