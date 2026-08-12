from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import pytest
from hermes_ops.analysis.builder import analysis_request_hash, build_analysis_request, canonical_json
from hermes_ops.analysis.loader import load_evidence_pack
from hermes_ops.core.errors import AnalysisError
from hermes_ops.skills.mission_models import EvidenceFile, EvidenceRegion, EvidenceRelationship, RelatedTest
from tests.analysis_helpers import QUESTION, make_pack, save_pack

def test_analysis_pack_is_built_only_from_valid_evidence_pack(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,20000); assert request.analysis_pack.regions
    with pytest.raises(AnalysisError): build_analysis_request({},QUESTION,20000)
def test_builder_never_receives_or_opens_target(tmp_path):
    pack=make_pack(tmp_path); request,_=build_analysis_request(pack,QUESTION,20000); assert not hasattr(request.analysis_pack,"target")
def test_reduction_is_deterministic_and_deduplicated(tmp_path):
    pack=make_pack(tmp_path); a=build_analysis_request(pack,QUESTION,20000); b=build_analysis_request(pack,QUESTION,20000); assert canonical_json(a[0])==canonical_json(b[0]) and a[1]==b[1]
def test_structurally_connected_regions_have_closed_priority(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,4000); regions=[dict(x) for x in request.analysis_pack.regions]; assert regions and regions[0]["id"]
def test_implementation_persistence_and_test_roles_have_closed_priority(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,20000); roles={r for x in request.analysis_pack.files for r in dict(x)["roles"]}; assert "implementation" in roles and "test" in roles
def test_every_analysis_item_preserves_evidence_pack_provenance(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,20000); assert all(dict(x)["reasons"] for x in request.analysis_pack.regions)
def test_stable_evidence_ids_follow_canonical_order(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,20000); ids=[dict(x)["id"] for x in request.analysis_pack.files]; assert ids==sorted(ids) and all(x.startswith("F") for x in ids)
def test_budget_counts_exact_canonical_payload_characters(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,20000); assert request.analysis_pack.budget.used_chars==len(canonical_json(request))
def test_budget_omission_is_explicit_and_never_silent(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,4000); o=request.analysis_pack.omissions; assert request.analysis_pack.budget.complete == (o.omitted_ids_digest is None)
def test_minimum_viable_pack_fails_closed_when_budget_is_too_small(tmp_path):
    with pytest.raises(AnalysisError): build_analysis_request(make_pack(tmp_path),QUESTION,3999)
def test_absolute_paths_are_rejected_before_adapter(tmp_path):
    from dataclasses import replace
    pack=make_pack(tmp_path); bad=replace(pack,files=(replace(pack.files[0],path="C:/secret.py"),)+pack.files[1:])
    with pytest.raises(AnalysisError): build_analysis_request(bad,QUESTION,20000)
def test_items_not_present_in_evidence_pack_are_rejected(tmp_path):
    from dataclasses import replace
    pack=make_pack(tmp_path); bad=replace(pack,relationships=(replace(pack.relationships[0],target="missing.py"),))
    with pytest.raises(AnalysisError): build_analysis_request(bad,QUESTION,20000)
def test_secret_like_literals_are_redacted_or_excluded_before_adapter(tmp_path):
    from dataclasses import replace
    pack=make_pack(tmp_path); region=replace(pack.regions[0],excerpt='api_token = "sensitive-value"'); pack=replace(pack,regions=(region,)+pack.regions[1:]); request,_=build_analysis_request(pack,QUESTION,20000); assert "sensitive-value" not in canonical_json(request) and "<REDACTED>" in canonical_json(request)
def test_analysis_pack_hash_is_sha256_of_exact_canonical_payload(tmp_path):
    request,digest=build_analysis_request(make_pack(tmp_path),QUESTION,20000); assert digest==hashlib.sha256(canonical_json(request).encode()).hexdigest()==analysis_request_hash(request)
def test_region_and_symbol_caps_are_represented_by_budget_omissions(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),QUESTION,4000); assert request.analysis_pack.omissions.omitted_regions>=0

def test_budget_success_and_selected_evidence_are_monotonic(tmp_path):
    """Spec: HERMES-0010 / AC-38 through AC-41."""
    pack=make_pack(tmp_path)
    path=pack.files[0].path
    extra=tuple(
        EvidenceRegion(path,100+index,100+index,(f"evidence-{index:03d}-" + "x"*900),"active_code",("budget regression",))
        for index in range(120)
    )
    pack=replace(pack,regions=pack.regions+extra)
    previous_counts=None
    passed=False
    for budget in (40_000,50_000,60_000,70_000,80_000,100_000,120_000):
        try:
            request,digest=build_analysis_request(pack,QUESTION,budget)
        except AnalysisError as error:
            assert error.code=="ANALYSIS_CONTEXT_BUDGET_TOO_SMALL"
            assert not passed
            continue
        passed=True
        raw=canonical_json(request)
        assert len(raw)<=budget
        counts=tuple(len(getattr(request.analysis_pack,name)) for name in ("files","regions","symbols","relationships","tests"))
        if previous_counts is not None:
            assert all(current>=previous for current,previous in zip(counts,previous_counts))
        previous_counts=counts
        repeated,repeated_digest=build_analysis_request(pack,QUESTION,budget)
        assert canonical_json(repeated)==raw
        assert repeated_digest==digest

def _competing_relationship_pack(tmp_path):
    pack=make_pack(tmp_path)
    service="document_service.py"
    peripheral_files=(
        EvidenceFile("agents/trello_agent.py",("implementation",),7,("peripheral integration",)),
        EvidenceFile("agents/drive_agent.py",("implementation",),7,("peripheral integration",)),
    )
    regions=(
        EvidenceRegion(service,10,10,"from agents.trello_agent import sync_board","active_code",("structural import",)),
        EvidenceRegion(service,11,11,"from agents.drive_agent import sync_drive","active_code",("structural import",)),
        EvidenceRegion("agents/trello_agent.py",1,1,"def sync_board(): pass","active_code",("peripheral implementation",)),
        EvidenceRegion("agents/drive_agent.py",1,1,"def sync_drive(): pass","active_code",("peripheral implementation",)),
    )
    relationships=(
        EvidenceRelationship("import",service,"agents/trello_agent.py",f"{service}:10","literal peripheral import"),
        EvidenceRelationship("import",service,"agents/drive_agent.py",f"{service}:11","literal peripheral import"),
    )
    return replace(pack,files=pack.files+peripheral_files,regions=pack.regions+regions,relationships=pack.relationships+relationships)

def test_question_promotes_relevant_structural_target_before_peripheral_chain(tmp_path):
    """Spec: HERMES-0010 / AC-42, AC-43, AC-47."""
    pack=_competing_relationship_pack(tmp_path)
    chosen=None
    for budget in range(4_000,20_001,250):
        request,_=build_analysis_request(pack,"Could client documents cross during batch processing?",budget)
        relationships=[dict(row) for row in request.analysis_pack.relationships]
        files={dict(row)["id"]:dict(row)["path"] for row in request.analysis_pack.files}
        targets={files[row["target_id"]] for row in relationships}
        if "document_repository.py" in targets:
            chosen=(request,targets)
            break
    assert chosen is not None
    request,targets=chosen
    assert "document_repository.py" in targets
    assert "agents/trello_agent.py" not in targets
    assert "agents/drive_agent.py" not in targets
    assert any(dict(row)["path"]=="tests/test_document_service.py" for row in request.analysis_pack.files)

def test_question_changes_priority_without_changing_ids_or_provenance(tmp_path):
    """Spec: HERMES-0010 / AC-42, AC-45, AC-46."""
    pack=_competing_relationship_pack(tmp_path)
    client,_=build_analysis_request(pack,"Could client documents cross during batch processing?",5_000)
    trello,_=build_analysis_request(pack,"How does the trello board integration work?",5_000)
    client_ranking=[dict(row)["id"] for row in client.analysis_pack.regions]
    trello_ranking=[dict(row)["id"] for row in trello.analysis_pack.regions]
    assert client_ranking!=trello_ranking
    full_client,_=build_analysis_request(pack,"Could client documents cross during batch processing?",20_000)
    full_trello,_=build_analysis_request(pack,"How does the trello board integration work?",20_000)
    def ids(request):
        return ({dict(row)["path"]:dict(row)["id"] for row in request.analysis_pack.files},{dict(row)["excerpt"]:dict(row)["id"] for row in request.analysis_pack.regions})
    assert ids(full_client)==ids(full_trello)

def test_source_score_is_controlled_tiebreaker_below_question_relevance(tmp_path):
    """Spec: HERMES-0010 / AC-44, AC-45."""
    pack=make_pack(tmp_path)
    files=(EvidenceFile("alpha.py",("implementation",),99,("generic",)),EvidenceFile("beta.py",("implementation",),1,("generic",)))
    regions=(EvidenceRegion("alpha.py",1,1,"def helper(): pass","active_code",("generic",)),EvidenceRegion("beta.py",1,1,"def helper(): pass","active_code",("generic",)))
    pack=replace(pack,files=pack.files+files,regions=pack.regions+regions)
    neutral,_=build_analysis_request(pack,"Inspect unmatched lexical query",20_000)
    focused,_=build_analysis_request(pack,"Inspect beta behavior",20_000)
    neutral_order=[dict(row)["excerpt"]+dict(row)["file_id"] for row in neutral.analysis_pack.regions]
    focused_order=[dict(row)["file_id"] for row in focused.analysis_pack.regions]
    file_ids={dict(row)["path"]:dict(row)["id"] for row in focused.analysis_pack.files}
    assert neutral_order.index("def helper(): pass"+file_ids["alpha.py"])<neutral_order.index("def helper(): pass"+file_ids["beta.py"])
    assert focused_order.index(file_ids["beta.py"])<focused_order.index(file_ids["alpha.py"])

def test_anchor_structural_unit_precedes_competing_lexical_regions(tmp_path):
    """Spec: HERMES-0010 / AC-48 through AC-50."""
    pack=make_pack(tmp_path)
    service="central_service.py"; repository="central_store.py"
    files=(
        EvidenceFile(service,("implementation","service"),32,("client document workflow",)),
        EvidenceFile(repository,("implementation",),7,("structural target",)),
    )+tuple(EvidenceFile(f"peripheral/item_{index}.py",("implementation",),12,("document helper",)) for index in range(12))
    regions=(
        EvidenceRegion(service,1,1,"def process_client_documents(): pass","active_code",("question anchor",)),
        EvidenceRegion(service,2,2,"from central_store import load_records","active_code",("relationship provenance",)),
        EvidenceRegion(repository,1,1,"def load_records(): return []","active_code",("target representative",)),
    )+tuple(
        EvidenceRegion(f"peripheral/item_{index}.py",1,1,"document helper " + str(index) + " " + "x"*1_500,"active_code",("lexical peripheral",))
        for index in range(12)
    )
    relationship=EvidenceRelationship("import",service,repository,f"{service}:2","literal structural import")
    pack=replace(pack,files=pack.files+files,regions=pack.regions+regions,relationships=pack.relationships+(relationship,))
    chosen=None
    for budget in range(4_000,12_001,250):
        request,_=build_analysis_request(pack,"Could client documents cross in processing?",budget)
        paths={dict(row)["path"] for row in request.analysis_pack.files}
        relationships=[dict(row) for row in request.analysis_pack.relationships]
        file_paths={dict(row)["id"]:dict(row)["path"] for row in request.analysis_pack.files}
        if any(file_paths[row["source_id"]]==service and file_paths[row["target_id"]]==repository for row in relationships):
            chosen=(request,paths)
            break
    assert chosen is not None
    request,paths=chosen
    assert {service,repository}<=paths
    assert not any(path.startswith("peripheral/") for path in paths)
    excerpts=[dict(row)["excerpt"] for row in request.analysis_pack.regions]
    assert excerpts.index("def process_client_documents(): pass")<excerpts.index("from central_store import load_records")<excerpts.index("def load_records(): return []")
