from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


class Status(str, Enum):
    OK = "OK"
    WARNING = "AVISO"
    BLOCKED = "BLOQUEADO"
    ERROR = "ERRO"


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (set, frozenset)):
        normalized = [_json_safe(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        )
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return _json_safe(asdict(value))
    if isinstance(value, BaseException):
        return str(value)
    raise TypeError(f"Unsupported result detail type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: Status
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)
    code: str = "ok"

    def __post_init__(self) -> None:
        if not isinstance(self.status, Status):
            raise TypeError("status must be an instance of Status")

    def to_dict(self, sanitizer: Any | None = None) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": _json_safe(self.details),
            "code": self.code,
        }
        if sanitizer is not None:
            return sanitizer.sanitize(payload)
        return payload


@dataclass(frozen=True, slots=True)
class Report:
    command: str
    results: tuple[CheckResult, ...]
    forced_exit_code: int | None = None

    @classmethod
    def from_results(
        cls,
        command: str,
        results: Iterable[CheckResult],
        forced_exit_code: int | None = None,
    ) -> Report:
        return cls(command, tuple(results), forced_exit_code)

    @property
    def exit_code(self) -> int:
        if self.forced_exit_code is not None:
            return self.forced_exit_code
        if any(item.code == "external_failure" for item in self.results):
            return 4
        if any(item.code.startswith("config_") and item.status is not Status.OK for item in self.results):
            return 2
        if any(item.status is Status.BLOCKED for item in self.results):
            return 3
        if any(item.status is Status.ERROR for item in self.results):
            return 1
        return 0

    def to_dict(self, sanitizer: Any | None = None) -> dict[str, Any]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "results": [item.to_dict(sanitizer) for item in self.results],
        }

    def to_json(self, sanitizer: Any | None = None) -> str:
        return json.dumps(
            self.to_dict(sanitizer),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def to_text(self, sanitizer: Any | None = None) -> str:
        lines = [
            f"{item.status.value:<9} {item.name}: "
            f"{sanitizer.sanitize_text(item.message) if sanitizer else item.message}"
            for item in self.results
        ]
        lines.append(f"exit_code={self.exit_code}")
        return "\n".join(lines)
