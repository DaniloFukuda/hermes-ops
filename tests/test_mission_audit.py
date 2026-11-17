from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, replace
import json
from pathlib import Path

import pytest

from hermes_ops.cli import main
from hermes_ops.core.errors import AnalysisError, SkillExecutionError
from hermes_ops.skills import SkillPolicy, SkillRisk, SkillRunInputs, discover_skills, run_skill
from hermes_ops.skills.mission_audit import build_evidence_pack, normalize_mission


def _policy() -> SkillPolicy:
    return SkillPolicy(SkillRisk.LOW, False, frozenset({"git"}))


def _project(root: Path) -> Path:
    (root / "tests").mkdir()
    (root / "invoice_service.py").write_text("class InvoiceService:\n    def process_batch(self): pass\n", encoding="utf-8")
    (root / "tests/test_invoice_service.py").write_text("from invoice_service import InvoiceService\ndef test_process_batch(): pass\n", encoding="utf-8")
    return root


def _v2_payload(tmp_path: Path, provenance: list[dict] | None = None) -> dict:
    payload = json.loads(json.dumps(asdict(build_evidence_pack(_project(tmp_path), "invoice batch process"))))
    payload["schema_version"] = 2
    payload["omission_provenance"] = list(provenance or [])
    if provenance:
        equivalent = provenance[0]["equivalent_region"]
        if equivalent is not None:
            payload["files"].append({
                "path": equivalent["path"], "roles": ["documentation"], "score": 0,
                "reasons": ["synthetic selected equivalent for provenance validation"],
            })
            payload["regions"].append({
                **equivalent,
                "excerpt": "# redundant_marker",
                "content_kind": provenance[0]["content_kind"],
                "reasons": list(provenance[0]["reasons"]),
            })
    return payload


def _redundant_record(path: str = "notes.py", line: int = 2) -> dict:
    return {
        "omission_id": f"{path}:{line}:{line}",
        "omitted_region": {"path": path, "start_line": line, "end_line": line},
        "equivalent_region": {"path": path, "start_line": 1, "end_line": 1},
        "content_kind": "comment",
        "reasons": ("term:redundant_marker",),
        "associated_terms": ("redundant_marker",),
        "classification": "redundant_evidence_omitted",
        "cap": "MAX_REGIONS_PER_FILE",
        "justification": "canonical duplicate comment selected at notes.py:1:1",
    }


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


def test_mission_character_limit_accepts_3000_and_rejects_3001() -> None:
    """Spec: HERMES-0035 / AC-01"""
    accepted = "a" * 3000
    mission, terms = normalize_mission(accepted)
    assert mission == accepted
    assert tuple(item.term for item in terms) == (accepted,)

    with pytest.raises(SkillExecutionError) as caught:
        normalize_mission("a" * 3001)
    assert caught.value.code == "SKILL_EXECUTION_INVALID"


def test_mission_base_term_limit_accepts_96_and_rejects_97() -> None:
    """Spec: HERMES-0035 / AC-02"""
    accepted = " ".join(f"term{index:03d}" for index in range(96))
    _, terms = normalize_mission(accepted)
    assert len(terms) == 96

    rejected = " ".join(f"term{index:03d}" for index in range(97))
    with pytest.raises(SkillExecutionError) as caught:
        normalize_mission(rejected)
    assert caught.value.code == "MISSION_TERM_LIMIT_EXCEEDED"


def test_accent_aliases_do_not_consume_base_term_limit() -> None:
    """Spec: HERMES-0035 / AC-03"""
    mission = " ".join(f"término{index:03d}" for index in range(96))
    _, terms = normalize_mission(mission)
    assert len(terms) == 192
    assert sum(item.source == "mission" for item in terms) == 96
    assert sum(item.source == "accent_alias" for item in terms) == 96


def test_selection_terms_have_an_absolute_192_item_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec: HERMES-0035 / AC-04"""
    import hermes_ops.skills.mission_audit as mission_audit

    monkeypatch.setattr(mission_audit, "MAX_BASE_TERMS", 97)
    mission = " ".join(f"término{index:03d}" for index in range(97))
    with pytest.raises(SkillExecutionError) as caught:
        normalize_mission(mission)
    assert caught.value.code == "MISSION_TERM_LIMIT_EXCEEDED"


def test_mission_limit_error_codes_remain_stable() -> None:
    """Spec: HERMES-0035 / AC-05"""
    with pytest.raises(SkillExecutionError) as length_error:
        normalize_mission("a" * 3001)
    with pytest.raises(SkillExecutionError) as term_error:
        normalize_mission(" ".join(f"term{index:03d}" for index in range(97)))
    assert length_error.value.code == "SKILL_EXECUTION_INVALID"
    assert term_error.value.code == "MISSION_TERM_LIMIT_EXCEEDED"


def test_mission_term_limit_keeps_cli_exit_code_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Spec: HERMES-0035 / AC-06"""
    mission = " ".join(f"term{index:03d}" for index in range(97))
    assert main([
        "skill", "run", "mission-audit", "--project", str(tmp_path),
        "--mission", mission,
    ]) == 2
    assert "MISSION_TERM_LIMIT_EXCEEDED" in capsys.readouterr().err


def test_short_mission_normalization_remains_unchanged() -> None:
    """Spec: HERMES-0035 / AC-07"""
    mission, terms = normalize_mission("  Auditar   emissão lote  ")
    assert mission == "Auditar emissão lote"
    assert tuple((item.term, item.source) for item in terms) == (
        ("emissão", "mission"),
        ("emissao", "accent_alias"),
        ("lote", "mission"),
    )


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


def test_evidence_pack_includes_structural_scope_field(tmp_path: Path) -> None:
    """Spec: HERMES-0014 / AC-16 - structural_scope field exists in MissionEvidencePack."""
    (tmp_path / "service.py").write_text("def process(): pass\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "process service")
    # structural_scope should exist and default to empty tuple for legacy calls
    assert hasattr(pack, "structural_scope")
    assert isinstance(pack.structural_scope, tuple)
    assert pack.structural_scope == ()


def test_mission_evidence_pack_has_structural_scope_field(tmp_path: Path) -> None:
    """Spec: HERMES-0014 / AC-16 - structural_scope field exists and defaults to empty tuple."""
    from hermes_ops.skills.mission_models import MissionEvidencePack, MissionCompleteness

    # Test default empty tuple for backward compatibility
    pack = MissionEvidencePack(
        schema_version=1,
        mission="test mission",
        target="<PROJECT_ROOT>",
        selection_terms=(),
        files=(),
        regions=(),
        symbols=(),
        relationships=(),
        related_tests=(),
        unresolved_questions=(),
        completeness=MissionCompleteness(
            status="sufficient",
            matched_terms=(),
            unmatched_terms=(),
            has_active_implementation=False,
            has_traceable_relationship=False,
            has_related_test=False,
            counts=(),
            incompleteness_codes=(),
        ),
        limitations=(),
    )
    assert hasattr(pack, "structural_scope")
    assert pack.structural_scope == ()
    assert isinstance(pack.structural_scope, tuple)

    # Test setting structural_scope with values
    pack_with_scope = MissionEvidencePack(
        schema_version=1,
        mission="test mission",
        target="<PROJECT_ROOT>",
        selection_terms=(),
        files=(),
        regions=(),
        symbols=(),
        relationships=(),
        related_tests=(),
        unresolved_questions=(),
        completeness=MissionCompleteness(
            status="sufficient",
            matched_terms=(),
            unmatched_terms=(),
            has_active_implementation=False,
            has_traceable_relationship=False,
            has_related_test=False,
            counts=(),
            incompleteness_codes=(),
        ),
        limitations=(),
        structural_scope=("src/**/*.py", "tests/**/*.py"),
    )
    assert pack_with_scope.structural_scope == ("src/**/*.py", "tests/**/*.py")

    # Test frozen immutability
    with pytest.raises(FrozenInstanceError):
        pack.structural_scope = ("new",)  # type: ignore[misc]


def test_scoped_discovery_does_not_read_outside_file(tmp_path: Path) -> None:
    """Spec: HERMES-0014 / AC-10 — arquivo fora do scope NÃO tem _read() chamado.

    Creates a structure where a file outside the scope would cause read_source_documents
    to fail if it were read (binary content). With scope restricting to allowed/,
    the forbidden file must never be passed to _read().
    """
    # Setup: allowed/selected.py (valid UTF-8) and forbidden/outside.py (binary with NUL)
    (tmp_path / "allowed").mkdir()
    (tmp_path / "forbidden").mkdir()
    (tmp_path / "allowed" / "selected.py").write_text("def process(): pass\n", encoding="utf-8")
    # This file would trigger CODE_AUDIT_BINARY_FILE if _read() is called on it
    (tmp_path / "forbidden" / "outside.py").write_bytes(b"x\x00y" * 100)

    # With scope restricting to allowed/, forbidden/outside.py must NOT be read
    pack = build_evidence_pack(tmp_path, "process", allowed_paths=("allowed",))

    # Should succeed (not fail with CODE_AUDIT_BINARY_FILE)
    assert pack.completeness.status in ("sufficient", "insufficient")
    # Only allowed/selected.py should be in evidence
    file_paths = {f.path for f in pack.files}
    assert file_paths == {"allowed/selected.py"}
    assert "forbidden/outside.py" not in file_paths


def test_scoped_discovery_prunes_outside_directory(tmp_path: Path) -> None:
    """Spec: HERMES-0014 / AC-11 — diretório fora do scope não enumera filhos.

    Creates a large directory tree outside the scope. If traversal pruning works,
    the walk should not descend into forbidden/ at all.
    """
    (tmp_path / "allowed").mkdir()
    (tmp_path / "forbidden").mkdir()
    # Create many files in forbidden/ — if traversed, would hit file limits
    for i in range(50):
        (tmp_path / "forbidden" / f"file_{i}.py").write_text(f"# file {i}\n", encoding="utf-8")
    (tmp_path / "allowed" / "main.py").write_text("def main(): pass\n", encoding="utf-8")

    # With scope = allowed/, forbidden/ should be pruned during traversal
    pack = build_evidence_pack(tmp_path, "main", allowed_paths=("allowed",))

    # Should succeed without hitting file limits
    assert pack.completeness.status in ("sufficient", "insufficient")
    file_paths = {f.path for f in pack.files}
    assert file_paths == {"allowed/main.py"}
    # No forbidden files should appear
    assert not any(p.startswith("forbidden/") for p in file_paths)


def test_scoped_discovery_allows_explicit_file_only(tmp_path: Path) -> None:
    """Spec: HERMES-0014 / AC-08 — arquivo explícito incluído, irmãos não."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "selected.py").write_text("def selected(): pass\n", encoding="utf-8")
    (tmp_path / "src" / "sibling.py").write_text("def sibling(): pass\n", encoding="utf-8")

    # Include only the specific file
    pack = build_evidence_pack(tmp_path, "selected", allowed_paths=("src/selected.py",))

    file_paths = {f.path for f in pack.files}
    assert file_paths == {"src/selected.py"}
    assert "src/sibling.py" not in file_paths


def test_scoped_discovery_allows_directory_recursive(tmp_path: Path) -> None:
    """Spec: HERMES-0014 / AC-07 — diretório incluído autoriza descendentes."""
    (tmp_path / "src" / "auth").mkdir(parents=True)
    (tmp_path / "src" / "auth" / "login.py").write_text("def login(): pass\n", encoding="utf-8")
    (tmp_path / "src" / "auth" / "session.py").write_text("def session(): pass\n", encoding="utf-8")
    (tmp_path / "src" / "other").mkdir()
    (tmp_path / "src" / "other" / "unrelated.py").write_text("def unrelated(): pass\n", encoding="utf-8")

    # Include directory — should get all descendants
    pack = build_evidence_pack(tmp_path, "auth login", allowed_paths=("src/auth",))

    file_paths = {f.path for f in pack.files}
    assert "src/auth/login.py" in file_paths
    assert "src/auth/session.py" in file_paths
    assert "src/other/unrelated.py" not in file_paths


def test_scoped_discovery_mixed_file_and_dir(tmp_path: Path) -> None:
    """Spec: HERMES-0014 / AC-08 + AC-07 — combina arquivo + diretório."""
    (tmp_path / "src" / "auth").mkdir(parents=True)
    (tmp_path / "src" / "auth" / "login.py").write_text("def login(): pass\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_login.py").write_text("def test_login(): pass\n", encoding="utf-8")
    (tmp_path / "src" / "other.py").write_text("def other(): pass\n", encoding="utf-8")

    # Include directory + explicit file
    pack = build_evidence_pack(tmp_path, "auth test", allowed_paths=("src/auth", "tests/test_login.py"))

    file_paths = {f.path for f in pack.files}
    assert "src/auth/login.py" in file_paths
    assert "tests/test_login.py" in file_paths
    assert "src/other.py" not in file_paths


def test_critical_symbol_after_twelve_regions_is_selected(tmp_path: Path) -> None:
    """HERMES-0036 / AC-01: a late critical function must outrank lexical noise."""
    lines = [f"# noise {index}" for index in range(12)]
    lines.append("def recover_critical(): pass")
    (tmp_path / "critical.py").write_text("\n".join(lines) + "\n", encoding="utf-8")

    pack = build_evidence_pack(tmp_path, "noise recover_critical")

    assert any(region.path == "critical.py" and region.start_line == 13 for region in pack.regions)


def test_critical_test_after_imports_and_fixtures_is_selected(tmp_path: Path) -> None:
    """HERMES-0036 / AC-02: a late test definition must remain visible."""
    (tmp_path / "tests").mkdir()
    lines = [f"# fixture {index}" for index in range(12)]
    lines.append("def test_recover_critical(): pass")
    (tmp_path / "tests" / "test_critical.py").write_text("\n".join(lines) + "\n", encoding="utf-8")

    pack = build_evidence_pack(tmp_path, "fixture test_recover_critical")

    assert any(
        region.path == "tests/test_critical.py" and region.start_line == 13
        for region in pack.regions
    )


def test_critical_selection_is_deterministic(tmp_path: Path) -> None:
    """HERMES-0036 / AC-03: repeated selection has identical evidence."""
    (tmp_path / "critical.py").write_text(
        "\n".join([f"# noise {index}" for index in range(12)] + ["def recover_critical(): pass"]) + "\n",
        encoding="utf-8",
    )
    first = build_evidence_pack(tmp_path, "noise recover_critical")
    second = build_evidence_pack(tmp_path, "noise recover_critical")
    assert first == second


def test_critical_symbol_and_relationship_region_are_preserved(tmp_path: Path) -> None:
    """HERMES-0036 / AC-04: structural provenance remains materialized."""
    (tmp_path / "seed.py").write_text(
        "\n".join([f"# noise {index}" for index in range(12)] + ["import critical", "def seed(): pass"]) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "critical.py").write_text("def critical(): pass\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "noise critical")
    assert pack.relationships
    for relationship in pack.relationships:
        path, line_text = relationship.evidence_region.rsplit(":", 1)
        line = int(line_text)
        assert any(region.path == path and region.start_line <= line <= region.end_line for region in pack.regions)




def test_import_context_dedup_preserves_critical_symbol_reason() -> None:
    """HERMES-0036 regression: import context cannot demote a critical region."""
    from hermes_ops.skills.mission_audit import _select_regions
    from hermes_ops.skills.mission_models import EvidenceRegion

    candidates = [
        EvidenceRegion("imported.py", line, line, "# noise", "comment", ("term:noise",))
        for line in range(1, 13)
    ]
    candidates.extend((
        EvidenceRegion(
            "imported.py", 13, 13, "def recover_critical(): pass", "active_code",
            ("critical_symbol:recover_critical",),
        ),
        EvidenceRegion(
            "imported.py", 13, 13, "def recover_critical(): pass", "active_code",
            ("one-hop import from seed.py:1",),
        ),
    ))

    selected, omitted, critical_omitted = _select_regions(candidates, [])
    critical = next(region for region in selected if region.start_line == 13)
    assert "critical_symbol:recover_critical" in critical.reasons
    assert not critical_omitted
    assert omitted


def test_redundant_candidates_do_not_replace_critical_region(tmp_path: Path) -> None:
    """HERMES-0036 / AC-05: critical evidence outranks comments/docstrings."""
    lines = [f"# noise {index}" for index in range(12)] + ["def recover_critical(): pass"]
    (tmp_path / "critical.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "noise recover_critical")
    assert any(region.start_line == 13 for region in pack.regions)


def test_per_file_cap_reports_critical_omission_without_sufficiency(tmp_path: Path) -> None:
    """HERMES-0036 / AC-06: omission remains a blocking signal."""
    import hermes_ops.skills.mission_audit as mission_audit

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(mission_audit, "MAX_REGIONS_PER_FILE", 1)
    try:
        (tmp_path / "critical.py").write_text("# noise\ndef recover_critical(): pass\n", encoding="utf-8")
        pack = build_evidence_pack(tmp_path, "noise recover_critical")
        assert pack.completeness.status == "insufficient"
        assert "CAP_OMISSION" in pack.completeness.incompleteness_codes
    finally:
        monkeypatch.undo()


def test_global_region_cap_reports_critical_omission_without_sufficiency(tmp_path: Path) -> None:
    """HERMES-0036 / AC-07: global cap cannot produce approval."""
    import hermes_ops.skills.mission_audit as mission_audit

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(mission_audit, "MAX_REGIONS", 1)
    try:
        (tmp_path / "critical.py").write_text("def recover_critical(): pass\n", encoding="utf-8")
        (tmp_path / "other.py").write_text("def other(): pass\n", encoding="utf-8")
        pack = build_evidence_pack(tmp_path, "recover_critical other")
        assert pack.completeness.status == "insufficient"
        assert "CAP_OMISSION" in pack.completeness.incompleteness_codes
    finally:
        monkeypatch.undo()


def test_unmatched_central_term_remains_insufficient(tmp_path: Path) -> None:
    """HERMES-0036 / AC-08: volume cannot replace a missing central term."""
    (tmp_path / "critical.py").write_text("def recover_critical(): pass\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "recover_critical absent_central_requirement")
    assert pack.completeness.status == "insufficient"
    assert "UNCOVERED_CENTRAL_TERMS" in pack.completeness.incompleteness_codes


def test_critical_selection_respects_include_path(tmp_path: Path) -> None:
    """HERMES-0036 / AC-09: critical selection cannot escape structural scope."""
    (tmp_path / "allowed").mkdir()
    (tmp_path / "forbidden").mkdir()
    (tmp_path / "allowed" / "critical.py").write_text("def recover_critical(): pass\n", encoding="utf-8")
    (tmp_path / "forbidden" / "critical.py").write_text("def recover_critical(): pass\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "recover_critical", allowed_paths=("allowed",))
    assert {item.path for item in pack.files} == {"allowed/critical.py"}
    assert all(region.path == "allowed/critical.py" for region in pack.regions)


def test_legacy_empty_scope_remains_compatible(tmp_path: Path) -> None:
    """HERMES-0036 / AC-10: empty scope preserves legacy discovery."""
    (tmp_path / "critical.py").write_text("def recover_critical(): pass\n", encoding="utf-8")
    pack = build_evidence_pack(tmp_path, "recover_critical")
    assert pack.structural_scope == ()
    assert "critical.py" in {item.path for item in pack.files}


def test_evidence_pack_size_limit_remains_fail_closed(tmp_path: Path) -> None:
    """HERMES-0036 / AC-11: size overflow remains an error."""
    import hermes_ops.skills.mission_audit as mission_audit

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(mission_audit, "MAX_JSON_BYTES", 1)
    try:
        (tmp_path / "critical.py").write_text("def recover_critical(): pass\n", encoding="utf-8")
        with pytest.raises(SkillExecutionError) as caught:
            build_evidence_pack(tmp_path, "recover_critical")
        assert caught.value.code == "MISSION_EVIDENCE_PACK_SIZE_EXCEEDED"
    finally:
        monkeypatch.undo()


def test_v2_pack_accepts_complete_omission_provenance(tmp_path: Path) -> None:
    """HERMES-0037 AC-22: v2 must carry validated omission provenance."""
    from hermes_ops.analysis.loader import parse_evidence_pack

    payload = _v2_payload(tmp_path, [_redundant_record()])
    try:
        parsed = parse_evidence_pack(payload)
    except Exception as exc:  # noqa: BLE001 - RED until v2 support exists
        pytest.fail(f"v2 provenance is not accepted: {type(exc).__name__}: {exc}")
    assert parsed.schema_version == 2
    assert parsed.omission_provenance[0].classification == "redundant_evidence_omitted"


def test_v2_provenance_is_sorted_deterministically(tmp_path: Path) -> None:
    """HERMES-0037 AC-13/AC-20: provenance order is stable by region identity."""
    from hermes_ops.analysis.loader import parse_evidence_pack

    payload = _v2_payload(tmp_path, [_redundant_record(line=3), _redundant_record(line=2)])
    try:
        parsed = parse_evidence_pack(payload)
    except Exception as exc:  # noqa: BLE001 - RED until v2 support exists
        pytest.fail(f"v2 provenance is not accepted: {type(exc).__name__}: {exc}")
    assert [item.omission_id for item in parsed.omission_provenance] == ["notes.py:2:2", "notes.py:3:3"]


@pytest.mark.parametrize("content_kind", ["comment", "docstring"])
def test_v2_redundant_comment_or_docstring_has_equivalent_region(tmp_path: Path, content_kind: str) -> None:
    """HERMES-0037 AC-02/AC-03: equivalence requires a selected same-file region."""
    from hermes_ops.analysis.loader import parse_evidence_pack

    record = _redundant_record()
    record["content_kind"] = content_kind
    payload = _v2_payload(tmp_path, [record])
    try:
        parsed = parse_evidence_pack(payload)
    except Exception as exc:  # noqa: BLE001 - RED until v2 support exists
        pytest.fail(f"v2 redundancy is not accepted: {type(exc).__name__}: {exc}")
    assert parsed.omission_provenance[0].equivalent_region == {
        "path": "notes.py", "start_line": 1, "end_line": 1,
    }


@pytest.mark.parametrize("classification,content_kind", [
    ("necessary_evidence_omitted", "active_code"),
    ("critical_evidence_omitted", "active_code"),
])
def test_v2_nonredundant_omission_remains_blocking(tmp_path: Path, classification: str, content_kind: str) -> None:
    """HERMES-0037 AC-04/AC-05/AC-07/AC-08: nonredundant omissions cannot authorize."""
    from hermes_ops.analysis.loader import parse_evidence_pack

    record = _redundant_record()
    record["classification"] = classification
    record["content_kind"] = content_kind
    record["equivalent_region"] = None
    payload = _v2_payload(tmp_path, [record])
    payload["completeness"]["status"] = "insufficient"
    payload["completeness"]["incompleteness_codes"].append(classification.upper())
    parsed = parse_evidence_pack(payload)
    assert parsed.completeness.status == "insufficient"
    assert parsed.omission_provenance[0].classification != "redundant_evidence_omitted"


def test_v2_missing_provenance_is_rejected_or_insufficient(tmp_path: Path) -> None:
    """HERMES-0037 AC-17/AC-25: absence of provenance cannot authorize."""

    payload = _v2_payload(tmp_path)
    payload.pop("omission_provenance")
    _assert_invalid_v2(payload)


def test_v1_pack_remains_readable_without_redundancy_inference(tmp_path: Path) -> None:
    """HERMES-0037 AC-18/AC-23: v1 remains historical and cannot prove redundancy."""
    from hermes_ops.analysis.loader import parse_evidence_pack

    payload = _v2_payload(tmp_path)
    payload["schema_version"] = 1
    payload.pop("omission_provenance")
    parsed = parse_evidence_pack(payload)
    assert parsed.schema_version == 1
    assert not hasattr(parsed, "omission_provenance")


def test_unknown_evidence_pack_version_is_rejected(tmp_path: Path) -> None:
    """HERMES-0037 AC-24: unknown versions fail closed."""

    payload = _v2_payload(tmp_path)
    payload["schema_version"] = 99
    _assert_invalid_v2(payload)


def _assert_invalid_v2(payload: dict) -> None:
    from hermes_ops.analysis.loader import parse_evidence_pack

    with pytest.raises(AnalysisError) as caught:
        parse_evidence_pack(payload)
    assert caught.value.code == "ANALYSIS_PACK_INVALID"


def test_v2_rejects_active_code_marked_as_redundant(tmp_path: Path) -> None:
    """HERMES-0037 AC-05/AC-16: active code cannot be redundant evidence."""
    record = _redundant_record()
    record["content_kind"] = "active_code"
    _assert_invalid_v2(_v2_payload(tmp_path, [record]))


def test_v2_rejects_missing_associated_terms(tmp_path: Path) -> None:
    """HERMES-0037 AC-21: provenance must preserve associated terms."""
    record = _redundant_record()
    record["associated_terms"] = ()
    _assert_invalid_v2(_v2_payload(tmp_path, [record]))


def test_v2_rejects_divergent_associated_terms(tmp_path: Path) -> None:
    """HERMES-0037 AC-20/AC-21: provenance terms cannot diverge from evidence."""
    record = _redundant_record()
    record["associated_terms"] = ("different_term",)
    _assert_invalid_v2(_v2_payload(tmp_path, [record]))


def test_v2_rejects_cap_omission_without_complete_provenance(tmp_path: Path) -> None:
    """HERMES-0037 AC-17/AC-25: CAP_OMISSION needs per-region provenance."""
    payload = _v2_payload(tmp_path)
    payload["limitations"].append("CAP_OMISSION")
    payload["completeness"]["incompleteness_codes"].append("CAP_OMISSION")
    _assert_invalid_v2(payload)


def test_v2_rejects_sufficient_with_nonredundant_provenance(tmp_path: Path) -> None:
    """HERMES-0037 AC-19/AC-21: sufficient cannot coexist with necessary omission."""
    record = _redundant_record()
    record["classification"] = "necessary_evidence_omitted"
    record["content_kind"] = "active_code"
    record["equivalent_region"] = None
    payload = _v2_payload(tmp_path, [record])
    assert payload["completeness"]["status"] == "sufficient"
    _assert_invalid_v2(payload)


def test_v2_rejects_equivalent_region_that_is_not_omitted(tmp_path: Path) -> None:
    """HERMES-0037 AC-20: omitted and equivalent identities must differ."""
    record = _redundant_record(line=1)
    record["equivalent_region"] = dict(record["omitted_region"])
    _assert_invalid_v2(_v2_payload(tmp_path, [record]))


def test_v2_validator_rejects_direct_invalid_provenance(tmp_path: Path) -> None:
    """HERMES-0037 AC-21: validator must not trust direct AnalysisPack objects."""
    from hermes_ops.analysis.adapter import RawAnalysisResponse
    from hermes_ops.analysis.builder import build_analysis_request
    from hermes_ops.analysis.validator import validate_analysis_response

    request, _ = build_analysis_request(
        build_evidence_pack(_project(tmp_path), "invoice batch process"),
        "What evidence supports the invoice batch process?",
        20_000,
    )
    selected = dict(request.analysis_pack.regions[0])
    file_path = next(
        dict(row)["path"] for row in request.analysis_pack.files
        if dict(row)["id"] == selected["file_id"]
    )
    malformed = tuple(sorted({
        "omission_id": f"{file_path}:999:999",
        "omitted_region": {"path": file_path, "start_line": 999, "end_line": 999},
        "equivalent_region": {"path": file_path, "start_line": selected["start_line"], "end_line": selected["end_line"]},
        "content_kind": "active_code",
        "reasons": selected["reasons"],
        "associated_terms": (),
        "classification": "redundant_evidence_omitted",
        "cap": "MAX_REGIONS",
        "justification": "synthetic malformed direct object",
    }.items()))
    bad_pack = replace(request.analysis_pack, omission_provenance=(malformed,))
    bad_request = replace(request, analysis_pack=bad_pack)
    raw = RawAnalysisResponse({
        "schema_version": 1,
        "claims": [],
        "overall_classification": "insufficient",
        "limitations": list(bad_pack.source_limitations),
    })
    with pytest.raises(AnalysisError) as caught:
        validate_analysis_response(raw, bad_request)
    assert caught.value.code == "ANALYSIS_RESPONSE_INVALID"
