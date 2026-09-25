from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
from hermes_ops.skills.mission_audit import build_evidence_pack

QUESTION="Is there evidence of possible document crossing between clients?"

def make_pack(root:Path):
    (root/"tests").mkdir(parents=True,exist_ok=True)
    (root/"document_service.py").write_text("from document_repository import load_client\ndef process_document_batch(client_id):\n    return load_client(client_id)\n",encoding="utf-8")
    (root/"document_repository.py").write_text("def load_client(client_id):\n    return client_id\n",encoding="utf-8")
    (root/"tests/test_document_service.py").write_text("from document_service import process_document_batch\ndef test_document_batch_client(): pass\n",encoding="utf-8")
    return build_evidence_pack(root,"document batch client")

def save_pack(root:Path,pack=None)->Path:
    pack=pack or make_pack(root/"project"); path=root/"pack.json"; path.write_text(json.dumps(asdict(pack),ensure_ascii=False),encoding="utf-8"); return path
