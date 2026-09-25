from hermes_ops.analysis.builder import build_analysis_request, canonical_json
from tests.analysis_helpers import make_pack

def test_saved_evidence_pack_answers_only_from_reduced_analysis_pack(tmp_path):
    request,_=build_analysis_request(make_pack(tmp_path),"Existe evidência de possível cruzamento de documentos entre clientes?",20000); text=canonical_json(request); assert "analysis_pack" in text and "<PROJECT_ROOT>" not in text
