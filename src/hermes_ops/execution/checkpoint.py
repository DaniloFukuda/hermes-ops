from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import re
from typing import Generic, Iterable, TypeVar

from hermes_ops.core.presentation import PublicSanitizer
from hermes_ops.execution.context import ExecutionContext


SCHEMA_VERSION = 1
MAX_ITEMS = 50
MAX_TEXT_LENGTH = 240

_SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*:\s*bearer\s+\S+"),
    re.compile(r"(?i)\b(?:token|password|passwd|senha|secret|private[_ -]?key)"
               r"[\w -]*\s*[:=]\s*\S+"),
    re.compile(r"(?i)\b(?:token|secret|private_key|senha)_[A-Z0-9_]+\b"),
    re.compile(r"(?i)(?:^|[\\/])\.env(?:\.[^\\/\s]+)?(?:$|[\\/\s])"),
)


class CheckpointReason(str, Enum):
    BUDGET_THRESHOLD = "budget_threshold"
    CHECKPOINT_REQUIRED = "checkpoint_required"
    MANUAL = "manual"
    ERROR = "error"
    HANDOFF = "handoff"


@dataclass(frozen=True, slots=True)
class BudgetCheckpointSnapshot:
    max_units: int
    used_units: int
    remaining: int
    validation_reserve: int
    closure_reserve: int
    warning_threshold: int
    checkpoint_threshold: int


@dataclass(frozen=True, slots=True)
class RepositoryCheckpointState:
    repository_root: str | None = None
    branch: str | None = None
    head: str | None = None
    working_tree_summary: str | None = None


@dataclass(frozen=True, slots=True)
class InspectedResource:
    kind: str
    target: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutedAction:
    kind: str
    target: str
    result: str
    units_consumed: int


@dataclass(frozen=True, slots=True)
class CheckpointTestResult:
    target: str
    status: str
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    exit_code: int | None = None
    message: str | None = None


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class BoundedItems(Generic[T]):
    items: tuple[T, ...] = ()
    omitted_count: int = 0


@dataclass(frozen=True, slots=True)
class ExecutionCheckpoint:
    schema_version: int
    reason: CheckpointReason
    objective: str = field(repr=False)
    phase: str = field(repr=False)
    budget_snapshot: BudgetCheckpointSnapshot
    repository_state: RepositoryCheckpointState | None = field(repr=False)
    modified_files: BoundedItems[str] = field(repr=False)
    inspected_resources: BoundedItems[InspectedResource] = field(repr=False)
    executed_actions: BoundedItems[ExecutedAction] = field(repr=False)
    test_results: BoundedItems[CheckpointTestResult] = field(repr=False)
    known_failures: BoundedItems[str] = field(repr=False)
    remaining_items: BoundedItems[str] = field(repr=False)
    recommended_next_action: str = field(repr=False)

    def to_dict(self) -> dict[str, object]:
        repository = self.repository_state
        return {
            "budget_snapshot": _budget_dict(self.budget_snapshot),
            "executed_actions": _bounded_dict(
                self.executed_actions, _action_dict
            ),
            "inspected_resources": _bounded_dict(
                self.inspected_resources, _resource_dict
            ),
            "known_failures": _bounded_dict(self.known_failures, str),
            "modified_files": _bounded_dict(self.modified_files, str),
            "objective": self.objective,
            "phase": self.phase,
            "reason": self.reason.value,
            "recommended_next_action": self.recommended_next_action,
            "remaining_items": _bounded_dict(self.remaining_items, str),
            "repository_state": _repository_dict(repository) if repository else None,
            "schema_version": self.schema_version,
            "test_results": _bounded_dict(self.test_results, _test_result_dict),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    def to_markdown(self) -> str:
        budget = self.budget_snapshot
        lines = [
            "# Execution checkpoint",
            "",
            f"- Objective: {self.objective}",
            f"- Reason: {self.reason.value}",
            f"- Phase: {self.phase}",
            f"- Budget: {budget.used_units}/{budget.max_units} used; "
            f"{budget.remaining} remaining",
        ]
        if self.repository_state is not None:
            lines.extend(
                (
                    f"- Branch: {self.repository_state.branch or 'unknown'}",
                    f"- HEAD: {self.repository_state.head or 'unknown'}",
                    f"- Working tree: "
                    f"{self.repository_state.working_tree_summary or 'unknown'}",
                )
            )
        _markdown_section(lines, "Modified files", self.modified_files, str)
        _markdown_section(
            lines,
            "Inspected resources",
            self.inspected_resources,
            lambda item: f"{item.kind}: {item.target}"
            + (f" ({item.detail})" if item.detail else ""),
        )
        _markdown_section(
            lines,
            "Executed actions",
            self.executed_actions,
            lambda item: f"{item.kind}: {item.target} — {item.result} "
            f"({item.units_consumed} units)",
        )
        _markdown_section(
            lines,
            "Tests",
            self.test_results,
            lambda item: f"{item.target}: {item.status} "
            f"(passed={item.passed}, failed={item.failed}, skipped={item.skipped}, "
            f"exit_code={item.exit_code if item.exit_code is not None else 'unknown'})",
        )
        _markdown_section(lines, "Known failures", self.known_failures, str)
        _markdown_section(lines, "Remaining work", self.remaining_items, str)
        lines.extend(("", "## Recommended next action", "", self.recommended_next_action))
        return "\n".join(lines) + "\n"


def create_execution_checkpoint(
    execution_context: ExecutionContext,
    *,
    reason: CheckpointReason,
    objective: str = "",
    phase: str = "",
    repository_state: RepositoryCheckpointState | None = None,
    modified_files: Iterable[str] = (),
    inspected_resources: Iterable[InspectedResource] = (),
    executed_actions: Iterable[ExecutedAction] = (),
    test_results: Iterable[CheckpointTestResult] = (),
    known_failures: Iterable[str] = (),
    remaining_items: Iterable[str] = (),
    recommended_next_action: str = "",
) -> ExecutionCheckpoint:
    if type(execution_context) is not ExecutionContext:
        raise TypeError("execution_context must be an ExecutionContext")
    if type(reason) is not CheckpointReason:
        raise TypeError("reason must be a CheckpointReason")
    root = repository_state.repository_root if repository_state else None
    sanitizer = PublicSanitizer(project_root=root, home=None, temp=None)
    clean = lambda value: _sanitize_text(value, sanitizer)
    budget = execution_context.budget
    return ExecutionCheckpoint(
        schema_version=SCHEMA_VERSION,
        reason=reason,
        objective=clean(objective),
        phase=clean(phase),
        budget_snapshot=BudgetCheckpointSnapshot(
            max_units=budget.max_units,
            used_units=budget.used_units,
            remaining=budget.remaining,
            validation_reserve=budget.validation_reserve,
            closure_reserve=budget.closure_reserve,
            warning_threshold=budget.warning_threshold,
            checkpoint_threshold=budget.checkpoint_threshold,
        ),
        repository_state=_clean_repository(repository_state, clean),
        modified_files=_bounded(modified_files, clean),
        inspected_resources=_bounded(
            inspected_resources,
            lambda item: InspectedResource(
                clean(item.kind), clean(item.target),
                clean(item.detail) if item.detail is not None else None,
            ),
        ),
        executed_actions=_bounded(
            executed_actions,
            lambda item: ExecutedAction(
                clean(item.kind), clean(item.target), clean(item.result),
                _nonnegative_int(item.units_consumed, "units_consumed"),
            ),
        ),
        test_results=_bounded(
            test_results,
            lambda item: CheckpointTestResult(
                clean(item.target), clean(item.status),
                _nonnegative_int(item.passed, "passed"),
                _nonnegative_int(item.failed, "failed"),
                _nonnegative_int(item.skipped, "skipped"),
                item.exit_code if item.exit_code is None else _integer(item.exit_code, "exit_code"),
                clean(item.message) if item.message is not None else None,
            ),
        ),
        known_failures=_bounded(known_failures, clean),
        remaining_items=_bounded(remaining_items, clean),
        recommended_next_action=clean(recommended_next_action),
    )


def _sanitize_text(value: object, sanitizer: PublicSanitizer) -> str:
    if type(value) is not str:
        raise TypeError("checkpoint text values must be strings")
    result = sanitizer.sanitize_text(value).replace("\r", " ").replace("\n", " ")
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub("<REDACTED>", result)
    if len(result) > MAX_TEXT_LENGTH:
        suffix = "…<truncated>"
        result = result[: MAX_TEXT_LENGTH - len(suffix)] + suffix
    return result


def _bounded(values: Iterable[T], transform) -> BoundedItems:
    kept = []
    omitted_count = 0
    for item in values:
        if len(kept) < MAX_ITEMS:
            kept.append(transform(item))
        else:
            omitted_count += 1
    return BoundedItems(tuple(kept), omitted_count)


def _clean_repository(state, clean):
    if state is None:
        return None
    if type(state) is not RepositoryCheckpointState:
        raise TypeError("repository_state must be a RepositoryCheckpointState or None")
    return RepositoryCheckpointState(
        clean(state.repository_root) if state.repository_root is not None else None,
        clean(state.branch) if state.branch is not None else None,
        clean(state.head) if state.head is not None else None,
        clean(state.working_tree_summary)
        if state.working_tree_summary is not None else None,
    )


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    result = _integer(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _bounded_dict(value: BoundedItems, transform) -> dict[str, object]:
    return {
        "items": [transform(item) for item in value.items],
        "omitted_count": value.omitted_count,
    }


def _budget_dict(value: BudgetCheckpointSnapshot) -> dict[str, int]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def _repository_dict(value: RepositoryCheckpointState) -> dict[str, str | None]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def _resource_dict(value: InspectedResource) -> dict[str, object]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def _action_dict(value: ExecutedAction) -> dict[str, object]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def _test_result_dict(value: CheckpointTestResult) -> dict[str, object]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def _markdown_section(lines, title, values, render) -> None:
    lines.extend(("", f"## {title}", ""))
    lines.extend(f"- {render(item)}" for item in values.items)
    if not values.items:
        lines.append("- None")
    if values.omitted_count:
        lines.append(f"- … {values.omitted_count} additional items omitted")
