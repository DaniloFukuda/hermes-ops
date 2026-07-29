from __future__ import annotations

from dataclasses import dataclass
import platform
import re
import sys


@dataclass(frozen=True, slots=True)
class PlatformInfo:
    operating_system: str
    release: str
    python_version: str
    python_executable: str


def current_platform() -> PlatformInfo:
    return PlatformInfo(
        operating_system=platform.system(),
        release=platform.release(),
        python_version=platform.python_version(),
        python_executable=sys.executable,
    )


_SIMPLE_VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?\Z")


def parse_version(value: str) -> tuple[int, ...]:
    if not isinstance(value, str):
        raise ValueError(f"Invalid version: {value}")
    match = _SIMPLE_VERSION.fullmatch(value)
    if match is None:
        raise ValueError(f"Invalid version: {value}")
    return tuple(int(part) for part in match.groups() if part is not None)


def python_is_compatible(current: str, minimum: str) -> bool:
    current_parts = parse_version(current)
    minimum_parts = parse_version(minimum)
    width = max(len(current_parts), len(minimum_parts))
    return current_parts + (0,) * (width - len(current_parts)) >= minimum_parts + (0,) * (
        width - len(minimum_parts)
    )
