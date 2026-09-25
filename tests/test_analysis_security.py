from dataclasses import asdict
import json
from hermes_ops.analysis.builder import build_analysis_request
from tests.analysis_helpers import QUESTION, make_pack

def test_analysis_path_uses_no_filesystem_shell_git_or_project_code(tmp_path,monkeypatch):
    pack=make_pack(tmp_path); import subprocess
    monkeypatch.setattr(subprocess,"run",lambda *a,**k:(_ for _ in ()).throw(AssertionError("subprocess")))
    assert build_analysis_request(pack,QUESTION,20000)[0].analysis_pack.regions
def test_analysis_path_does_not_write_target_or_access_network_directly(tmp_path,monkeypatch):
    pack=make_pack(tmp_path); import socket
    monkeypatch.setattr(socket,"socket",lambda *a,**k:(_ for _ in ()).throw(AssertionError("network")))
    before={p.relative_to(tmp_path).as_posix():p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}; build_analysis_request(pack,QUESTION,20000); after={p.relative_to(tmp_path).as_posix():p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}; assert before==after
