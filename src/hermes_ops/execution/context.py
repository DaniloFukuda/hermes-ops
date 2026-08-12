from __future__ import annotations

from dataclasses import dataclass, field

from hermes_ops.execution.budget import ExecutionBudget


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    budget: ExecutionBudget = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.budget) is not ExecutionBudget:
            raise TypeError("budget must be an ExecutionBudget")
