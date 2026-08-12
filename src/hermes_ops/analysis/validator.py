from __future__ import annotations

from typing import Any

from hermes_ops.analysis.adapter import RawAnalysisResponse
from hermes_ops.analysis.builder import analysis_request_hash
from hermes_ops.analysis.models import AnalysisClaim, AnalysisRequest, AnalysisResult
from hermes_ops.core.errors import AnalysisError

CLASSIFICATIONS=frozenset({"supported","plausible","insufficient","contradicted"})


def _fail(message:str)->None: raise AnalysisError("ANALYSIS_RESPONSE_INVALID",message)
def validate_analysis_response(raw:RawAnalysisResponse,request:AnalysisRequest)->AnalysisResult:
    if type(raw) is not RawAnalysisResponse or not isinstance(raw.value,dict): _fail("Adapter response must be an object")
    value=raw.value
    if set(value)!={"schema_version","claims","overall_classification","limitations"} or value["schema_version"]!=1: _fail("Response schema is invalid")
    if value["overall_classification"] not in CLASSIFICATIONS or not isinstance(value["claims"],list): _fail("Response classification is invalid")
    pack=request.analysis_pack; rows=(*pack.files,*pack.regions,*pack.symbols,*pack.relationships,*pack.tests); objects={dict(row)["id"]:dict(row) for row in rows}; claims=[]
    for item in value["claims"]:
        if not isinstance(item,dict) or set(item)!={"id","statement","classification","evidence_ids","contrary_evidence_ids","rationale","limitations"}: _fail("Claim schema is invalid")
        classification=item["classification"]
        if classification not in CLASSIFICATIONS: _fail("Claim classification is invalid")
        evidence=tuple(item["evidence_ids"]); contrary=tuple(item["contrary_evidence_ids"])
        if any(type(x) is not str or x not in objects for x in evidence+contrary): _fail("Claim references unknown evidence")
        if classification=="supported":
            active=sum(1 for x in evidence if x.startswith("R") and objects[x].get("content_kind")=="active_code")
            independent=len(set(evidence))>=2 and (active>=1 or any(x.startswith("L") for x in evidence))
            if not evidence or active<1 or not independent: _fail("Supported claim lacks direct independent evidence")
        if classification=="plausible" and not any(word in item["statement"].casefold() for word in ("possible","possibly","may","might","pode","possível")): _fail("Plausible claim must be conditional")
        if classification=="insufficient" and any(word in item["statement"].casefold() for word in ("definitely","certainly","com certeza","confirma")): _fail("Insufficient claim is conclusive")
        if classification=="contradicted" and not contrary: _fail("Contradicted claim lacks contrary evidence")
        if any(type(item[x]) is not str or not item[x] for x in ("id","statement","rationale")) or not isinstance(item["limitations"],list): _fail("Claim text is invalid")
        claims.append(AnalysisClaim(item["id"],item["statement"],classification,evidence,contrary,item["rationale"],tuple(item["limitations"])))
    limitations=tuple(value["limitations"])
    required=set(pack.source_limitations+pack.reduction_limitations)
    if not required.issubset(limitations): _fail("Response removed required limitations")
    return AnalysisResult(1,analysis_request_hash(request),pack.question,tuple(claims),value["overall_classification"],limitations,pack.omissions)
