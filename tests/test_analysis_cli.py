import json
import pytest
from hermes_ops.cli import main
from tests.analysis_helpers import QUESTION, save_pack

def test_cli_analyzes_existing_pack_without_project_option(tmp_path,capsys):
    code=main(["evidence","analyze","--evidence-pack",str(save_pack(tmp_path)),"--question",QUESTION,"--context-budget-chars","20000","--dry-run","--format","json"]); assert code==0 and json.loads(capsys.readouterr().out)["dry_run"]
def test_cli_rejects_project_and_target_inputs(tmp_path):
    with pytest.raises(SystemExit): main(["evidence","analyze","--evidence-pack",str(save_pack(tmp_path)),"--question",QUESTION,"--context-budget-chars","20000","--dry-run","--project",str(tmp_path)])
def test_cli_text_and_json_are_sanitized_and_deterministic(tmp_path,capsys):
    path=save_pack(tmp_path); args=["evidence","analyze","--evidence-pack",str(path),"--question",QUESTION,"--context-budget-chars","20000","--dry-run","--format","text"]; assert main(args)==0; a=capsys.readouterr().out; assert main(args)==0; b=capsys.readouterr().out; assert a==b and str(tmp_path) not in a
def test_invalid_pack_question_or_budget_fails_closed(tmp_path,capsys):
    path=tmp_path/"bad.json"; path.write_text("{}",encoding="utf-8"); code=main(["evidence","analyze","--evidence-pack",str(path),"--question","x","--context-budget-chars","1","--dry-run"]); assert code==2 and "exit_code=2" in capsys.readouterr().err
