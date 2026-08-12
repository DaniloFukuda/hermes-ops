import pytest
from hermes_ops.analysis.adapter import RawAnalysisResponse
from hermes_ops.analysis.builder import build_analysis_request
from hermes_ops.analysis.validator import validate_analysis_response
from hermes_ops.core.errors import AnalysisError
from tests.analysis_helpers import QUESTION, make_pack

def _request(tmp_path): return build_analysis_request(make_pack(tmp_path),QUESTION,20000)[0]
def _raw(request,classification="plausible",evidence=None,contrary=None,statement="This may be possible."):
    return RawAnalysisResponse({"schema_version":1,"claims":[{"id":"C1","statement":statement,"classification":classification,"evidence_ids":evidence or [],"contrary_evidence_ids":contrary or [],"rationale":"bounded","limitations":[]}],"overall_classification":classification,"limitations":list(request.analysis_pack.source_limitations+request.analysis_pack.reduction_limitations)})
def test_every_claim_references_existing_evidence_ids(tmp_path):
    request=_request(tmp_path); rid=dict(request.analysis_pack.regions[0])["id"]; assert validate_analysis_response(_raw(request,evidence=[rid]),request).claims[0].evidence_ids==(rid,)
def test_claim_classification_is_closed(tmp_path):
    request=_request(tmp_path); raw=_raw(request); raw.value["claims"][0]["classification"]="certain"
    with pytest.raises(AnalysisError): validate_analysis_response(raw,request)
def test_unsupported_conclusive_claim_is_rejected(tmp_path):
    request=_request(tmp_path)
    with pytest.raises(AnalysisError): validate_analysis_response(_raw(request,"supported",[],[],"It is confirmed."),request)
def test_contrary_evidence_and_limitations_are_preserved(tmp_path):
    request=_request(tmp_path); rid=dict(request.analysis_pack.regions[0])["id"]; result=validate_analysis_response(_raw(request,"contradicted",[rid],[rid],"The claim is contradicted."),request); assert result.claims[0].contrary_evidence_ids==(rid,)
def test_unknown_evidence_reference_rejects_entire_response(tmp_path):
    request=_request(tmp_path)
    with pytest.raises(AnalysisError): validate_analysis_response(_raw(request,evidence=["R9999"]),request)
