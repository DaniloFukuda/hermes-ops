from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from hermes_ops.core.errors import (
    CheckpointRequired,
    ExecutionBudgetError,
    ExecutionBudgetExceeded,
    ExecutionBudgetReserved,
)


class ExecutionCategory(str, Enum):
    EXPLORATION = "exploration"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    CLOSURE = "closure"


class BudgetDecision(str, Enum):
    ALLOWED = "allowed"
    WARNING = "warning"
    CHECKPOINT_REQUIRED = "checkpoint_required"
    RESERVED = "reserved"
    EXHAUSTED = "exhausted"


def _invalid(message: str) -> None:
    raise ExecutionBudgetError("EXECUTION_BUDGET_INVALID", message)


def _integer(value: object, name: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        _invalid(f"{name} must be an integer greater than or equal to {minimum}")
    return value


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    max_units: int
    used_units: int
    validation_reserve: int
    closure_reserve: int
    warning_threshold: int
    checkpoint_threshold: int

    def __post_init__(self) -> None:
        max_units = _integer(self.max_units, "max_units", minimum=1)
        used_units = _integer(self.used_units, "used_units", minimum=0)
        validation_reserve = _integer(
            self.validation_reserve,
            "validation_reserve",
            minimum=0,
        )
        closure_reserve = _integer(
            self.closure_reserve,
            "closure_reserve",
            minimum=1,
        )
        warning_threshold = _integer(
            self.warning_threshold,
            "warning_threshold",
            minimum=0,
        )
        checkpoint_threshold = _integer(
            self.checkpoint_threshold,
            "checkpoint_threshold",
            minimum=1,
        )
        if used_units > max_units:
            _invalid("used_units must not exceed max_units")
        if validation_reserve + closure_reserve >= max_units:
            _invalid("execution reserves must leave unreserved units")
        if warning_threshold >= checkpoint_threshold:
            _invalid("warning_threshold must be less than checkpoint_threshold")
        exploration_limit = max_units - validation_reserve - closure_reserve
        if checkpoint_threshold > exploration_limit:
            _invalid(
                "checkpoint_threshold must not exceed the exploration limit"
            )

    @property
    def remaining(self) -> int:
        return self.max_units - self.used_units

    @property
    def exploration_limit(self) -> int:
        return self.max_units - self.validation_reserve - self.closure_reserve

    @property
    def validation_limit(self) -> int:
        return self.max_units - self.closure_reserve

    def should_warn(self) -> bool:
        return self.used_units >= self.warning_threshold

    def should_checkpoint(self) -> bool:
        return self.used_units >= self.checkpoint_threshold

    def should_stop_exploration(self) -> bool:
        return self.should_checkpoint() or self.used_units >= self.exploration_limit

    def can_start(
        self,
        category: ExecutionCategory,
        units: int = 1,
    ) -> BudgetDecision:
        if type(category) is not ExecutionCategory:
            _invalid("category must be an ExecutionCategory")
        cost = _integer(units, "units", minimum=1)
        next_used = self.used_units + cost
        if next_used > self.max_units:
            return BudgetDecision.EXHAUSTED
        if category in {
            ExecutionCategory.EXPLORATION,
            ExecutionCategory.IMPLEMENTATION,
        }:
            limit = self.exploration_limit
        elif category is ExecutionCategory.VALIDATION:
            limit = self.validation_limit
        else:
            limit = self.max_units
        if next_used > limit:
            return BudgetDecision.RESERVED
        if (
            category
            in {ExecutionCategory.EXPLORATION, ExecutionCategory.IMPLEMENTATION}
            and self.should_checkpoint()
        ):
            return BudgetDecision.CHECKPOINT_REQUIRED
        if next_used >= self.warning_threshold:
            return BudgetDecision.WARNING
        return BudgetDecision.ALLOWED

    def consume(
        self,
        category: ExecutionCategory,
        units: int = 1,
    ) -> ExecutionBudget:
        decision = self.can_start(category, units)
        if decision is BudgetDecision.EXHAUSTED:
            raise ExecutionBudgetExceeded(
                "Action would exceed the absolute execution budget"
            )
        if decision is BudgetDecision.RESERVED:
            raise ExecutionBudgetReserved(
                "Action would consume units reserved for a later category"
            )
        if decision is BudgetDecision.CHECKPOINT_REQUIRED:
            raise CheckpointRequired(
                "Exploration is stopped at the checkpoint threshold"
            )
        return replace(self, used_units=self.used_units + units)
