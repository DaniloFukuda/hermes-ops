from __future__ import annotations

import json
from pathlib import Path

from hermes_ops.skills import SkillPolicy, SkillRisk, SkillRunInputs, run_skill
from hermes_ops.skills.execution_path_review import review_execution_path
from hermes_ops.skills.execution_path_models import ExecutionPathClassification
from hermes_ops.cli import main


def _write(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _classification(root: Path, producer: str, consumer: str, **kwargs: object):
    return review_execution_path(root, producer, consumer, **kwargs)


def test_generic_path_domain_mismatch_is_confirmed(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-01, AC-07"""
    _write(tmp_path, "flow.py", '''
from pathlib import Path
MANAGED = Path("managed")
def accept(candidate):
    return candidate
def consume(candidate):
    if not candidate.is_relative_to(MANAGED):
        raise ValueError("outside")
def execute(candidate):
    consume(accept(candidate))
''')
    report = _classification(tmp_path, "accept", "consume")
    assert report.classification is ExecutionPathClassification.CONFIRMED_MISMATCH
    finding = report.findings[0]
    assert finding.producer_symbol == "accept"
    assert finding.consumer_symbol == "consume"
    assert finding.produced_value
    assert finding.required_precondition
    assert finding.executable_path == ("accept", "consume")
    assert finding.mismatch_description and finding.reachable_scenario
    assert finding.severity.value == "high"
    assert len(finding.evidence_references) >= 3


def test_compatible_managed_root_boundaries_have_no_mismatch(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-02"""
    _write(tmp_path, "flow.py", '''
from pathlib import Path
MANAGED = Path("managed")
def build(name):
    return MANAGED / name
def consume(candidate):
    if not candidate.is_relative_to(MANAGED):
        raise ValueError("outside")
def execute(name):
    consume(build(name))
''')
    report = _classification(tmp_path, "build", "consume")
    assert report.classification is ExecutionPathClassification.NO_MISMATCH
    assert report.findings == ()


def test_state_mismatch_is_confirmed(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-03"""
    _write(tmp_path, "flow.py", '''
def prepare():
    return "prepared"
def publish(state):
    if state != "confirmed":
        raise ValueError("wrong state")
def execute():
    publish(prepare())
''')
    report = _classification(tmp_path, "prepare", "publish")
    assert report.classification is ExecutionPathClassification.CONFIRMED_MISMATCH


def test_guarded_transition_is_compatible(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-04"""
    _write(tmp_path, "flow.py", '''
def prepare():
    return "prepared"
def confirm(state):
    if state != "prepared":
        raise ValueError("wrong state")
    return "confirmed"
def publish(state):
    if state != "confirmed":
        raise ValueError("wrong state")
def execute():
    publish(confirm(prepare()))
''')
    report = _classification(tmp_path, "prepare", "publish")
    assert report.classification is ExecutionPathClassification.NO_MISMATCH
    assert report.executable_path == ("prepare", "confirm", "publish")


def test_consumer_without_comparable_contract_is_path_only(tmp_path: Path) -> None:
    """Spec: HERMES-0023 / AC-01, AC-11"""
    _write(tmp_path, "flow.py", '''
def produce(value): return value
def consume(value): external_check(value)
def execute(value): consume(produce(value))
''')
    report = _classification(tmp_path, "produce", "consume")
    assert report.classification is ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT
    assert report.limitations == ("NO_COMPARABLE_CONSUMER_CONTRACT",)
    assert report.findings == ()


def test_similar_names_without_executable_path_are_not_confirmed(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-06"""
    _write(tmp_path, "flow.py", '''
def produce_path(value): return value
def consume_path(value):
    if value != "safe": raise ValueError("unsafe")
def unrelated():
    produce_path("unsafe")
    consume_path("safe")
''')
    report = _classification(tmp_path, "produce_path", "consume_path")
    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE


def test_persisted_path_benchmark_uses_generic_analysis(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-08"""
    _write(tmp_path, "benchmark.py", '''
from pathlib import Path
CONFIGURED_AREA = Path("uploads")
class Record: pass
def remember(document, caller_path):
    document.location = caller_path
    return document.location
def attach(path):
    if not path.is_relative_to(CONFIGURED_AREA):
        raise ValueError("unmanaged")
def synchronize(document, selected):
    attach(remember(document, selected))
''')
    report = _classification(tmp_path, "remember", "attach")
    assert report.classification is ExecutionPathClassification.CONFIRMED_MISMATCH
    assert report.findings[0].produced_value == "caller-controlled value"


def test_structural_scope_prevents_outside_file_from_influencing_result(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-09"""
    _write(tmp_path, "allowed/flow.py", '''
def produce(): return "prepared"
def consume(state): external_check(state)
def execute(): consume(produce())
''')
    outside = tmp_path / "outside/flow.py"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"\0must-not-be-read")
    report = _classification(
        tmp_path, "produce", "consume", include_paths=("allowed",)
    )
    assert report.classification is ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT
    assert report.structural_scope == ("allowed",)


def test_result_is_deterministic_and_immutable(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-11"""
    _write(tmp_path, "flow.py", '''
def source(): return "a"
def sink(value):
    if value != "b": raise ValueError("bad")
def execute(): sink(source())
''')
    first = _classification(tmp_path, "source", "sink")
    second = _classification(tmp_path, "source", "sink")
    assert first == second
    try:
        first.classification = ExecutionPathClassification.NO_MISMATCH
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("report must be immutable")


def test_registered_skill_runs_through_closed_executor(tmp_path: Path) -> None:
    """Spec: HERMES-0015 / AC-10"""
    _write(tmp_path, "flow.py", '''
def source(): return "a"
def sink(value):
    if value != "b": raise ValueError("bad")
def execute(): sink(source())
''')
    policy = SkillPolicy(
        max_risk=SkillRisk.LOW,
        allow_write=False,
        available_requires=frozenset(),
    )
    result = run_skill(
        tmp_path,
        "execution-path-review",
        policy,
        inputs=SkillRunInputs(producer_symbol="source", consumer_symbol="sink"),
    )
    assert result.skill_id == "execution-path-review"
    assert result.evidence[0].code == "CONFIRMED_MISMATCH"
    assert not tuple(tmp_path.glob("**/__pycache__"))


def test_execution_path_review_cli_serializes_structured_finding(
    tmp_path: Path, capsys: object
) -> None:
    """Spec: HERMES-0015 / AC-07, AC-10"""
    _write(tmp_path, "flow.py", '''
def source(): return "a"
def sink(value):
    if value != "b": raise ValueError("bad")
def execute(): sink(source())
''')
    exit_code = main([
        "skill", "run", "execution-path-review", "--project", str(tmp_path),
        "--producer", "source", "--consumer", "sink", "--format", "json",
    ])
    payload = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert exit_code == 3
    assert payload["skill_id"] == "execution-path-review"
    details = payload["evidence"][0]["details"]
    assert details["classification"] == "CONFIRMED_MISMATCH"
    assert details["findings"][0]["executable_path"] == ["source", "sink"]
