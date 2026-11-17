from __future__ import annotations

from pathlib import Path

from hermes_ops.skills.execution_path_models import ExecutionPathClassification
from hermes_ops.skills.execution_path_review import review_execution_path


def _write(root: Path, source: str) -> None:
    (root / "flow.py").write_text(source, encoding="utf-8")


def test_zero_paths_has_distinct_limitation(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-01, AC-12, AC-15"""
    _write(
        tmp_path,
        '''
def producer():
    return {"item_id": 1}

def consumer(item_id):
    if not item_id:
        raise ValueError("missing")
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert "NO_EXECUTABLE_PATH" in report.limitations
    assert "EXECUTABLE_PATH_NOT_UNIQUE" not in report.limitations


def test_multiple_explicit_paths_remain_distinct(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-02"""
    _write(
        tmp_path,
        '''
def producer(): return "ready"
def consumer(value):
    if value != "ready": raise ValueError("bad")
def first(): consumer(producer())
def second(): consumer(producer())
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    assert "EXECUTABLE_PATH_NOT_UNIQUE" in report.limitations
    assert "NO_EXECUTABLE_PATH" not in report.limitations


def test_mapping_subscript_alias_method_and_forwarding_form_one_path(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-03 to AC-08, AC-14"""
    _write(
        tmp_path,
        '''
class Repository:
    def bind_existing(self, item_id, external_id):
        normalized = str(external_id).strip()
        if not normalized:
            raise ValueError("missing")
        record = lookup(item_id)
        if not record:
            return False
        return True

repository = Repository()

def producer():
    item_id = 7
    return {"success": True, "item_id": item_id}

class Adapter:
    def bind(self, item_id, external_id):
        return repository.bind_existing(item_id, external_id)

def execute():
    result = producer()
    alias = result
    item_id = alias["item_id"]
    return Adapter().bind(item_id, "known-id")
''',
    )

    report = review_execution_path(tmp_path, "producer", "bind_existing")

    assert "NO_EXECUTABLE_PATH" not in report.limitations
    assert "EXECUTABLE_PATH_NOT_UNIQUE" not in report.limitations
    assert report.executable_path == ("producer", "execute", "bind", "bind_existing")


def test_truthiness_and_direct_string_strip_are_preconditions(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-09, AC-11"""
    _write(
        tmp_path,
        '''
def producer(): return ""
def consumer(value):
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("missing")
def execute(): consumer(producer())
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert "CONSUMER_PRECONDITION_NOT_DISCOVERABLE" not in report.limitations
    assert report.classification is ExecutionPathClassification.CONFIRMED_MISMATCH


def test_truthiness_false_return_is_success_path_condition(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-10"""
    _write(
        tmp_path,
        '''
def producer(value): return value
def consumer(value):
    record = lookup(value)
    if not record:
        return False
    return True
def execute(value): consumer(producer(value))
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert "CONSUMER_PRECONDITION_NOT_DISCOVERABLE" not in report.limitations
    assert report.executable_path == ("producer", "consumer")


def test_redefined_alias_and_different_source_are_pruned(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-13"""
    _write(
        tmp_path,
        '''
def producer(): return {"item_id": 1}
def other(): return 999
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def execute():
    result = producer()
    item_id = result["item_id"]
    item_id = other()
    consumer(item_id)
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert "NO_EXECUTABLE_PATH" in report.limitations


def test_direct_mapping_subscript_without_alias_is_supported(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-05, AC-06"""
    _write(
        tmp_path,
        '''
def producer(): return {"item_id": 1}
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def execute():
    result = producer()
    consumer(result["item_id"])
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert report.executable_path == ("producer", "execute", "consumer")
    assert "NO_EXECUTABLE_PATH" not in report.limitations


def test_stdout_and_separate_cli_input_do_not_form_a_path(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-16"""
    _write(
        tmp_path,
        '''
def producer(): return {"item_id": 1}
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def emit():
    result = producer()
    print(result["item_id"])
def separate_command(args):
    consumer(args.item_id)
''',
    )

    report = review_execution_path(tmp_path, "producer", "consumer")

    assert "NO_EXECUTABLE_PATH" in report.limitations


def test_semantic_resolution_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0019 / AC-20"""
    _write(
        tmp_path,
        '''
def producer(): return {"item_id": 1}
def consumer(item_id):
    if not item_id: raise ValueError("missing")
def execute():
    result = producer()
    consumer(result["item_id"])
''',
    )

    first = review_execution_path(tmp_path, "producer", "consumer")
    second = review_execution_path(tmp_path, "producer", "consumer")

    assert first == second
