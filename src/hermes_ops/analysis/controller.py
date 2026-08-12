from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from hermes_ops.analysis.adapter import AnalyzerAdapter
from hermes_ops.analysis.builder import build_analysis_request
from hermes_ops.analysis.loader import load_evidence_pack
from hermes_ops.analysis.validator import validate_analysis_response
from hermes_ops.core.errors import AnalysisError


def _plain(value:Any)->Any:
    if is_dataclass(value) and not isinstance(value,type): return {f.name:_plain(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,tuple):
        if value and all(isinstance(x,tuple) and len(x)==2 for x in value): return {k:_plain(v) for k,v in value}
        return [_plain(x) for x in value]
    return value


def analyze_evidence_pack(path:str,question:str,budget_chars:int,*,dry_run:bool,adapter:AnalyzerAdapter|None=None)->dict[str,Any]:
    pack=load_evidence_pack(path); request,digest=build_analysis_request(pack,question,budget_chars)
    if dry_run:
        analysis=request.analysis_pack
        return {"dry_run":True,"analysis_request":_plain(request),"analysis_pack_hash":digest,"counts":{"files":len(analysis.files),"regions":len(analysis.regions),"symbols":len(analysis.symbols),"relationships":len(analysis.relationships),"tests":len(analysis.tests)},"context":_plain(analysis.budget),"omissions":_plain(analysis.omissions),"adapter_called":False}
    if adapter is None: raise AnalysisError("ANALYSIS_ADAPTER_UNAVAILABLE","No analyzer adapter is configured")
    raw=adapter.analyze(request)
    return {"dry_run":False,"analysis_result":_plain(validate_analysis_response(raw,request)),"adapter_id":adapter.id()}
