import hashlib
from hermes_ops.analysis.builder import canonical_json
from hermes_ops.analysis.controller import analyze_evidence_pack
from tests.analysis_helpers import QUESTION, save_pack

def test_dry_run_never_calls_adapter(tmp_path):
    class Bomb:
        def analyze(self,request): raise AssertionError("called")
        def id(self): return "bomb"
    result=analyze_evidence_pack(str(save_pack(tmp_path)),QUESTION,20000,dry_run=True,adapter=Bomb()); assert result["adapter_called"] is False
def test_dry_run_emits_exact_payload_that_would_be_sent(tmp_path):
    result=analyze_evidence_pack(str(save_pack(tmp_path)),QUESTION,20000,dry_run=True); assert result["analysis_request"]["analysis_pack"]["question"]==QUESTION
def test_dry_run_reports_counts_characters_budget_and_hash(tmp_path):
    result=analyze_evidence_pack(str(save_pack(tmp_path)),QUESTION,20000,dry_run=True); assert result["counts"]["regions"] and result["context"]["used_chars"]<=20000 and len(result["analysis_pack_hash"])==64
