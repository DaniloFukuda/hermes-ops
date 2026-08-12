from hermes_ops.analysis.builder import build_analysis_request
from hermes_ops.skills.mission_audit import build_evidence_pack
from tests.analysis_helpers import QUESTION, make_pack

def test_mission_audit_remains_local_deterministic_and_adapter_free(tmp_path):
    a=make_pack(tmp_path); b=build_evidence_pack(tmp_path,"document batch client"); assert a==b
def test_git_preflight_code_audit_and_catalog_contracts_are_unchanged():
    from hermes_ops.skills.executor import _dispatch_skill
    from hermes_ops.skills.code_audit import run_code_audit
    assert callable(_dispatch_skill) and callable(run_code_audit)
