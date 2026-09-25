from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from hermes_ops.analysis.models import AnalysisRequest


@dataclass(frozen=True, slots=True)
class RawAnalysisResponse:
    value: Any


class AnalyzerAdapter(Protocol):
    def id(self) -> str: ...
    def analyze(self, request: AnalysisRequest) -> RawAnalysisResponse: ...
