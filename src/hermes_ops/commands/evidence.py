from __future__ import annotations

import json
from typing import Any

from hermes_ops.analysis.controller import analyze_evidence_pack
from hermes_ops.core.presentation import PublicSanitizer


def run_evidence_analysis(path:str,question:str,budget:int,*,dry_run:bool)->dict[str,Any]: return analyze_evidence_pack(path,question,budget,dry_run=dry_run)
def evidence_analysis_json(payload:dict[str,Any],sanitizer:PublicSanitizer)->str: return json.dumps(sanitizer.sanitize(payload),ensure_ascii=False,sort_keys=True,separators=(",",":"))
def evidence_analysis_text(payload:dict[str,Any],sanitizer:PublicSanitizer)->str:
    safe=sanitizer.sanitize(payload); lines=[f"dry_run={str(safe['dry_run']).lower()}",f"analysis_pack_hash={safe.get('analysis_pack_hash','')}"]
    if safe["dry_run"]:
        counts=safe["counts"]; context=safe["context"]
        lines.extend(f"{name}={counts[name]}" for name in ("files","regions","symbols","relationships","tests"))
        lines.extend((f"context_limit_chars={context['limit_chars']}",f"context_used_chars={context['used_chars']}",f"context_remaining_chars={context['remaining_chars']}",f"context_utf8_bytes={context['canonical_utf8_bytes']}","analysis_request="+json.dumps(safe["analysis_request"],ensure_ascii=False,sort_keys=True,separators=(",",":")),"adapter_called=false"))
    return "\n".join(lines)
