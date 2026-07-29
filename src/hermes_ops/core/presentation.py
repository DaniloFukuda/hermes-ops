from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import re
import tempfile
from typing import Any


@dataclass(frozen=True, slots=True)
class PublicSanitizer:
    project_root: str | Path | None = None
    home: str | Path | None = None
    temp: str | Path | None = None

    @classmethod
    def for_project(cls, project_root: str | Path | None) -> PublicSanitizer:
        return cls(
            project_root=project_root,
            home=Path.home(),
            temp=Path(tempfile.gettempdir()),
        )

    def sanitize(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.sanitize_text(value)
        if isinstance(value, dict):
            return {
                str(key): self.sanitize(item)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            }
        if isinstance(value, list):
            return [self.sanitize(item) for item in value]
        if isinstance(value, tuple):
            return [self.sanitize(item) for item in value]
        return value

    def sanitize_text(self, value: str) -> str:
        result = value
        replacements = (
            (self.project_root, "<PROJECT_ROOT>"),
            (self.temp, "<TEMP>"),
            (self.home, "~"),
        )
        for raw_base, replacement in replacements:
            if raw_base is None:
                continue
            for variant in _path_variants(str(raw_base)):
                if not variant:
                    continue
                flags = re.IGNORECASE if _looks_windows(variant) else 0
                pattern = re.compile(
                    re.escape(variant) + r"(?=$|[\\/])",
                    flags,
                )
                result = pattern.sub(
                    lambda match: replacement,
                    result,
                )
        return result


def _path_variants(value: str) -> tuple[str, ...]:
    stripped = value.rstrip("\\/")
    variants = {stripped}
    if "\\" in stripped or _looks_windows(stripped):
        variants.add(stripped.replace("\\", "/"))
        variants.add(stripped.replace("/", "\\"))
    return tuple(sorted(variants, key=len, reverse=True))


def _looks_windows(value: str) -> bool:
    return bool(PureWindowsPath(value).drive)

