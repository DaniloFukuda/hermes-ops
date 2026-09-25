from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
from typing import Any

from hermes_ops.core.errors import SkillExecutionError

ALLOWED_EXTENSIONS = frozenset({".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"})
EXCLUDED_DIRECTORIES = frozenset({".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor", "dist", "build", "coverage", "__pycache__", ".mypy_cache", ".pytest_cache", ".tox", ".nox"})
MAX_DEPTH = 32
MAX_DIRECTORIES = 5_000
MAX_FILES = 1_000
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 20 * 1024 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@dataclass(frozen=True, slots=True)
class SourceDocument:
    path: str
    text: str
    bytes_read: int


@dataclass(frozen=True, slots=True)
class SourceInventory:
    root: Path
    directories: int
    documents: tuple[SourceDocument, ...]


@dataclass(frozen=True, slots=True)
class _Candidate:
    path: Path
    relative: str
    metadata: os.stat_result


def _fail(code: str, message: str) -> None:
    raise SkillExecutionError(code, message)


def valid_relative_path(value: str) -> bool:
    posix, windows = PurePosixPath(value), PureWindowsPath(value)
    return bool(value and value == value.replace("\\", "/") and not posix.is_absolute() and not windows.is_absolute() and not windows.drive and ".." not in posix.parts and all(p not in {"", "."} for p in posix.parts) and _CONTROL.search(value) is None)


def _metadata(path: Path, code: str = "CODE_AUDIT_READ_FAILED") -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        raise SkillExecutionError(code, "A controlled-reader path could not be inspected") from exc


def _reject(metadata: os.stat_result, code: str = "CODE_AUDIT_UNSAFE_PATH") -> None:
    if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & _REPARSE:
        _fail(code, "Controlled reading does not follow filesystem indirections")


def validate_target(value: str | Path) -> Path:
    try:
        target = Path(value).expanduser()
    except (TypeError, ValueError, OSError) as exc:
        raise SkillExecutionError("CODE_AUDIT_TARGET_INDIRECT", "The audit target is invalid") from exc
    target = target if target.is_absolute() else Path.cwd() / target
    current = Path(target.anchor)
    metadata = _metadata(current, "CODE_AUDIT_TARGET_INDIRECT")
    _reject(metadata, "CODE_AUDIT_TARGET_INDIRECT")
    for part in target.parts[1:]:
        current /= part
        metadata = _metadata(current, "CODE_AUDIT_TARGET_INDIRECT")
        _reject(metadata, "CODE_AUDIT_TARGET_INDIRECT")
    if not stat.S_ISDIR(metadata.st_mode):
        _fail("CODE_AUDIT_TARGET_INDIRECT", "The audit target is not a direct directory")
    canonical = target.resolve(strict=True)
    try:
        git_metadata = os.lstat(target / ".git")
    except FileNotFoundError:
        git_metadata = None
    except OSError as exc:
        raise SkillExecutionError("CODE_AUDIT_READ_FAILED", "The target Git layout could not be inspected") from exc
    if git_metadata is not None and stat.S_ISREG(git_metadata.st_mode):
        _fail("CODE_AUDIT_TARGET_INDIRECT", "Indirect Git worktree layouts are not supported")
    return canonical


def _relative(root: Path, path: Path) -> str:
    try:
        value = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise SkillExecutionError("CODE_AUDIT_PATH_ESCAPE", "An audit path escapes the target") from exc
    if not valid_relative_path(value):
        _fail("CODE_AUDIT_PATH_ESCAPE", "An audit path is not safely contained")
    return value


def _inventory(root: Path, *, max_depth: int, max_directories: int, max_files: int, max_file_bytes: int, max_total_bytes: int) -> tuple[tuple[_Candidate, ...], int]:
    directories, candidates, stack = 1, [], [(root, 0)]
    while stack:
        directory, depth = stack.pop()
        if depth > max_depth:
            _fail("CODE_AUDIT_DEPTH_LIMIT_EXCEEDED", "Audit depth limit exceeded")
        try:
            entries = tuple(sorted(directory.iterdir(), key=lambda p: p.name))
        except OSError as exc:
            raise SkillExecutionError("CODE_AUDIT_READ_FAILED", "An audit directory could not be enumerated") from exc
        children = []
        for entry in entries:
            relative = _relative(root, entry)
            metadata = _metadata(entry)
            _reject(metadata)
            if stat.S_ISDIR(metadata.st_mode):
                directories += 1
                if directories > max_directories:
                    _fail("CODE_AUDIT_DIRECTORY_LIMIT_EXCEEDED", "Audit directory limit exceeded")
                if entry.name not in EXCLUDED_DIRECTORIES:
                    if depth + 1 > max_depth:
                        _fail("CODE_AUDIT_DEPTH_LIMIT_EXCEEDED", "Audit depth limit exceeded")
                    children.append((entry, depth + 1))
            elif stat.S_ISREG(metadata.st_mode):
                if entry.suffix in ALLOWED_EXTENSIONS:
                    if metadata.st_size > max_file_bytes:
                        _fail("CODE_AUDIT_FILE_SIZE_EXCEEDED", "An audit file exceeds its size limit")
                    candidates.append(_Candidate(entry, relative, metadata))
                    if len(candidates) > max_files:
                        _fail("CODE_AUDIT_FILE_LIMIT_EXCEEDED", "Audit file limit exceeded")
            else:
                _fail("CODE_AUDIT_UNSAFE_FILE_TYPE", "Audit encountered an unsafe file type")
        stack.extend(reversed(children))
    candidates.sort(key=lambda c: c.relative)
    if sum(c.metadata.st_size for c in candidates) > max_total_bytes:
        _fail("CODE_AUDIT_TOTAL_SIZE_EXCEEDED", "Audit total size limit exceeded")
    return tuple(candidates), directories


def _identity(m: os.stat_result) -> tuple[int, ...]:
    return (m.st_mode, m.st_dev, m.st_ino, m.st_size, m.st_mtime_ns, m.st_ctime_ns)


def _cross(m: os.stat_result) -> tuple[int, ...]:
    return (m.st_mode, m.st_dev, m.st_ino, m.st_size, m.st_mtime_ns)


def _read(candidate: _Candidate, max_file_bytes: int) -> SourceDocument:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = None
    try:
        descriptor = os.open(candidate.path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _cross(opened) != _cross(candidate.metadata):
            _fail("CODE_AUDIT_FILE_CHANGED", "An audit file changed before reading")
        chunks, remaining = [], max_file_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk); remaining -= len(chunk)
        after_handle, after_path = os.fstat(descriptor), os.lstat(candidate.path)
    except SkillExecutionError:
        raise
    except OSError as exc:
        raise SkillExecutionError("CODE_AUDIT_READ_FAILED", "An audit file could not be read") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    data = b"".join(chunks)
    if len(data) > max_file_bytes:
        _fail("CODE_AUDIT_FILE_SIZE_EXCEEDED", "An audit file exceeds its size limit")
    if _identity(after_handle) != _identity(opened) or _identity(after_path) != _identity(candidate.metadata) or _cross(after_path) != _cross(opened):
        _fail("CODE_AUDIT_FILE_CHANGED", "An audit file changed while being read")
    if b"\0" in data:
        _fail("CODE_AUDIT_BINARY_FILE", "An audit candidate is binary")
    bom = b"\xef\xbb\xbf"
    if data.find(bom, 1) >= 0:
        _fail("CODE_AUDIT_INVALID_ENCODING", "A UTF-8 BOM is only valid at the file start")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SkillExecutionError("CODE_AUDIT_INVALID_ENCODING", "An audit candidate is not valid UTF-8") from exc
    return SourceDocument(candidate.relative, text, len(data))


def read_source_documents(value: Any, *, max_depth: int = MAX_DEPTH, max_directories: int = MAX_DIRECTORIES, max_files: int = MAX_FILES, max_file_bytes: int = MAX_FILE_BYTES, max_total_bytes: int = MAX_TOTAL_BYTES) -> SourceInventory:
    root = validate_target(value)
    candidates, directories = _inventory(root, max_depth=max_depth, max_directories=max_directories, max_files=max_files, max_file_bytes=max_file_bytes, max_total_bytes=max_total_bytes)
    documents = tuple(_read(candidate, max_file_bytes) for candidate in candidates)
    if sum(document.bytes_read for document in documents) > max_total_bytes:
        _fail("CODE_AUDIT_TOTAL_SIZE_EXCEEDED", "Audit total size limit exceeded")
    return SourceInventory(root, directories, documents)
