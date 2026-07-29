from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from hermes_ops.core.errors import PathResolutionError


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
