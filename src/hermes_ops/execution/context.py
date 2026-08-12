from __future__ import annotations

from dataclasses import dataclass, field

from hermes_ops.execution.budget import (
    BudgetDecision,
    ExecutionBudget,
    ExecutionCategory,
)


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    budget: ExecutionBudget = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.budget) is not ExecutionBudget:
            raise TypeError("budget must be an ExecutionBudget")

    def can_start(
        self,
        category: ExecutionCategory,
        units: int = 1,
    ) -> BudgetDecision:
        return self.budget.can_start(category, units)

    def consume(
        self,
        category: ExecutionCategory,
        units: int = 1,
    ) -> ExecutionContext:
        return ExecutionContext(self.budget.consume(category, units))
