from pathlib import Path
import pytest
from hermes_ops.analysis.adapter import AnalyzerAdapter, RawAnalysisResponse
from hermes_ops.analysis.controller import analyze_evidence_pack
from hermes_ops.analysis.loader import load_evidence_pack
from hermes_ops.analysis.builder import build_analysis_request
from hermes_ops.analysis.validator import validate_analysis_response
from hermes_ops.core.errors import AnalysisError
from tests.analysis_helpers import QUESTION, save_pack

class FakeAdapter:
    def __init__(self): self.requests=[]
    def id(self): return "fake"
    def analyze(self,request):
        self.requests.append(request); p=request.analysis_pack; ids=[dict(x)["id"] for x in p.regions[:2]]
        return RawAnalysisResponse({"schema_version":1,"claims":[{"id":"C1","statement":"There may be a documented risk.","classification":"plausible","evidence_ids":ids,"contrary_evidence_ids":[],"rationale":"Bounded evidence only.","limitations":[]}],"overall_classification":"plausible","limitations":list(p.source_limitations+p.reduction_limitations)})

def test_adapter_contract_is_vendor_neutral(): assert hasattr(AnalyzerAdapter,"analyze") and hasattr(AnalyzerAdapter,"id")
def test_controller_calls_adapter_only_after_local_validation(tmp_path):
    adapter=FakeAdapter(); result=analyze_evidence_pack(str(save_pack(tmp_path)),QUESTION,20000,dry_run=False,adapter=adapter); assert len(adapter.requests)==1 and result["adapter_id"]=="fake"
def test_adapter_receives_only_analysis_request(tmp_path):
    adapter=FakeAdapter(); analyze_evidence_pack(str(save_pack(tmp_path)),QUESTION,20000,dry_run=False,adapter=adapter); assert not hasattr(adapter.requests[0],"target")
def test_no_adapter_is_configured_by_default(tmp_path):
    with pytest.raises(AnalysisError) as caught: analyze_evidence_pack(str(save_pack(tmp_path)),QUESTION,20000,dry_run=False)
    assert caught.value.code=="ANALYSIS_ADAPTER_UNAVAILABLE"
