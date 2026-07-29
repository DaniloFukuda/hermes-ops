from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat

from hermes_ops.core.errors import PathResolutionError


def is_indirect_path(path: Path) -> bool:
    """Return whether one filesystem entry is a symlink or reparse point."""

    try:
        metadata = os.lstat(path)
    except OSError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(metadata.st_mode) or bool(attributes & reparse_flag)


def direct_project_path(root: Path, relative: str | Path) -> Path:
    """Resolve a project path only after proving every entry is direct."""

    resolved_root = root.resolve(strict=True)
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise PathResolutionError("Project path must be relative and contained")
    candidate = resolved_root
    for part in relative_path.parts:
        candidate = candidate / part
        if is_indirect_path(candidate):
            raise PathResolutionError(
                f"Project path uses an indirect filesystem entry: {relative}"
            )
    return candidate


def resolve_directory(value: str | Path, *, base: Path | None = None) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = (base if base is not None else Path.cwd()) / candidate
    try:
        candidate = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PathResolutionError(f"Project path does not exist: {candidate}") from exc
    if not candidate.is_dir():
        raise PathResolutionError(f"Project path is not a directory: {candidate}")
    return candidate


def project_relative_path(root: Path, value: str | Path) -> Path:
    text = str(value)
    windows = PureWindowsPath(text)
    posix = PurePosixPath(text)
    if not text.strip():
        raise PathResolutionError("Configured project path must not be empty")
    if windows.is_absolute() or windows.drive or posix.is_absolute():
        raise PathResolutionError(
            f"Configured project path must be relative: {text}"
        )
    if ".." in windows.parts or ".." in posix.parts:
        raise PathResolutionError(
            f"Configured project path must not traverse parents: {text}"
        )

    resolved_root = root.resolve(strict=True)
    candidate = (resolved_root / Path(text)).resolve(strict=False)
    if not candidate.is_relative_to(resolved_root):
        raise PathResolutionError(
            f"Configured project path escapes the project root: {text}"
        )
    return candidate
