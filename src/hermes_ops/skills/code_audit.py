from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
from typing import Any

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.core.results import Status
from hermes_ops.skills.execution_models import (
    SkillExecutionEvidence,
    SkillExecutionResult,
    SkillExecutionStatus,
)
from hermes_ops.skills.controlled_reader import read_source_documents


ALLOWED_EXTENSIONS = frozenset(
    {".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
)
EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "coverage",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".tox",
        ".nox",
    }
)
MAX_DEPTH = 32
MAX_DIRECTORIES = 5_000
MAX_FILES = 1_000
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 20 * 1024 * 1024
MAX_FINDINGS = 200
MAX_EVIDENCE_LINES = 8
MAX_EVIDENCE_CHARS = 1_200
RULESET_VERSION = 1

_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class CodeAuditSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CodeAuditClassification(str, Enum):
    OBSERVED = "observed"
    HYPOTHESIS = "hypothesis"


def _fail(code: str, message: str) -> None:
    raise SkillExecutionError(code, message)


def _valid_relative_path(value: str) -> bool:
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    return bool(
        value
        and value == value.replace("\\", "/")
        and not posix.is_absolute()
        and not windows.is_absolute()
        and not windows.drive
        and ".." not in posix.parts
        and all(part not in {"", "."} for part in posix.parts)
        and _CONTROL_CHARACTERS.search(value) is None
    )


@dataclass(frozen=True, slots=True)
class CodeAuditRegion:
    start_line: int
    end_line: int
    start_column: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        if (
            type(self.start_line) is not int
            or type(self.end_line) is not int
            or self.start_line < 1
            or self.end_line < self.start_line
        ):
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding region lines are invalid")
        columns = (self.start_column, self.end_column)
        if (columns[0] is None) != (columns[1] is None):
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding region columns are incomplete")
        if columns[0] is not None and (
            type(columns[0]) is not int
            or type(columns[1]) is not int
            or columns[0] < 1
            or columns[1] < columns[0]
        ):
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding region columns are invalid")


@dataclass(frozen=True, slots=True)
class CodeAuditFinding:
    rule_id: str
    severity: CodeAuditSeverity
    classification: CodeAuditClassification
    file: str
    region: CodeAuditRegion
    evidence: str
    observation: str
    justification: str
    suggestion: str

    def __post_init__(self) -> None:
        if type(self.rule_id) is not str or re.fullmatch(r"CA00[1-5]", self.rule_id) is None:
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding rule id is invalid")
        if type(self.severity) is not CodeAuditSeverity:
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding severity is invalid")
        if type(self.classification) is not CodeAuditClassification:
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding classification is invalid")
        if not _valid_relative_path(self.file):
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding file path is invalid")
        if type(self.region) is not CodeAuditRegion:
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding region is invalid")
        for value in (
            self.evidence,
            self.observation,
            self.justification,
            self.suggestion,
        ):
            if type(value) is not str or not value.strip():
                _fail("CODE_AUDIT_INVALID_FINDING", "Finding text is invalid")
        if len(self.evidence) > MAX_EVIDENCE_CHARS or len(self.evidence.splitlines()) > MAX_EVIDENCE_LINES:
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding evidence exceeds its limit")
        if _CONTROL_CHARACTERS.search(self.evidence):
            _fail("CODE_AUDIT_INVALID_FINDING", "Finding evidence contains unsafe controls")


@dataclass(frozen=True, slots=True)
class CodeAuditSummary:
    directories: int
    files: int
    bytes_read: int
    findings_info: int
    findings_low: int
    findings_medium: int
    findings_high: int
    findings_critical: int
    rules: tuple[str, ...]
    ruleset_version: int
    extensions: tuple[str, ...]
    max_depth: int
    max_directories: int
    max_files: int
    max_file_bytes: int
    max_total_bytes: int
    max_findings: int

    def __post_init__(self) -> None:
        numeric = (
            self.directories, self.files, self.bytes_read, self.findings_info,
            self.findings_low, self.findings_medium, self.findings_high,
            self.findings_critical, self.ruleset_version, self.max_depth,
            self.max_directories, self.max_files, self.max_file_bytes,
            self.max_total_bytes, self.max_findings,
        )
        if any(type(value) is not int or value < 0 for value in numeric):
            _fail("CODE_AUDIT_INVALID_FINDING", "Code audit summary values are invalid")
        if self.rules != ("CA001", "CA002", "CA003", "CA004", "CA005"):
            _fail("CODE_AUDIT_INVALID_FINDING", "Code audit summary rules are invalid")
        if self.extensions != tuple(sorted(ALLOWED_EXTENSIONS)):
            _fail("CODE_AUDIT_INVALID_FINDING", "Code audit summary extensions are invalid")


@dataclass(frozen=True, slots=True)
class _Candidate:
    path: Path
    relative: str
    metadata: os.stat_result


def _absolute_without_resolving(value: str | Path) -> Path:
    try:
        candidate = Path(value).expanduser()
    except (TypeError, ValueError, OSError) as exc:
        raise SkillExecutionError(
            "CODE_AUDIT_TARGET_INDIRECT", "The code audit target is invalid"
        ) from exc
    return candidate if candidate.is_absolute() else Path.cwd() / candidate


def _metadata(path: Path, code: str = "CODE_AUDIT_READ_FAILED") -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        raise SkillExecutionError(code, "A code audit path could not be inspected") from exc


def _reject_indirection(
    metadata: os.stat_result,
    code: str = "CODE_AUDIT_UNSAFE_PATH",
) -> None:
    attributes = getattr(metadata, "st_file_attributes", 0)
    if stat.S_ISLNK(metadata.st_mode) or attributes & _REPARSE_POINT_ATTRIBUTE:
        _fail(code, "Code audit does not follow filesystem indirections")


def validate_code_audit_target(value: str | Path) -> Path:
    target = _absolute_without_resolving(value)
    anchor = Path(target.anchor)
    current = anchor
    metadata = _metadata(anchor, "CODE_AUDIT_TARGET_INDIRECT")
    _reject_indirection(metadata, "CODE_AUDIT_TARGET_INDIRECT")
    for part in target.parts[1:]:
        current = current / part
        metadata = _metadata(current, "CODE_AUDIT_TARGET_INDIRECT")
        _reject_indirection(metadata, "CODE_AUDIT_TARGET_INDIRECT")
    if not stat.S_ISDIR(metadata.st_mode):
        _fail("CODE_AUDIT_TARGET_INDIRECT", "The code audit target is not a direct directory")
    try:
        canonical = target.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise SkillExecutionError(
            "CODE_AUDIT_TARGET_INDIRECT", "The code audit target could not be resolved"
        ) from exc
    git_entry = target / ".git"
    try:
        git_metadata = os.lstat(git_entry)
    except FileNotFoundError:
        git_metadata = None
    except OSError as exc:
        raise SkillExecutionError(
            "CODE_AUDIT_READ_FAILED", "The target Git layout could not be inspected"
        ) from exc
    if git_metadata is not None and stat.S_ISREG(git_metadata.st_mode):
        _fail("CODE_AUDIT_TARGET_INDIRECT", "Indirect Git worktree layouts are not supported")
    return canonical


def _relative(root: Path, path: Path) -> str:
    try:
        value = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise SkillExecutionError(
            "CODE_AUDIT_PATH_ESCAPE", "A code audit path escapes the target"
        ) from exc
    if not _valid_relative_path(value):
        _fail("CODE_AUDIT_PATH_ESCAPE", "A code audit path is not safely contained")
    return value


def _inventory(root: Path) -> tuple[tuple[_Candidate, ...], int]:
    directories = 1
    candidates: list[_Candidate] = []
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        directory, depth = stack.pop()
        if depth > MAX_DEPTH:
            _fail("CODE_AUDIT_DEPTH_LIMIT_EXCEEDED", "Code audit depth limit exceeded")
        try:
            entries = tuple(sorted(directory.iterdir(), key=lambda item: item.name))
        except OSError as exc:
            raise SkillExecutionError(
                "CODE_AUDIT_READ_FAILED", "A code audit directory could not be enumerated"
            ) from exc
        child_directories: list[tuple[Path, int]] = []
        for entry in entries:
            _relative(root, entry)
            metadata = _metadata(entry)
            _reject_indirection(metadata)
            if stat.S_ISDIR(metadata.st_mode):
                directories += 1
                if directories > MAX_DIRECTORIES:
                    _fail(
                        "CODE_AUDIT_DIRECTORY_LIMIT_EXCEEDED",
                        "Code audit directory limit exceeded",
                    )
                if entry.name not in EXCLUDED_DIRECTORIES:
                    if depth + 1 > MAX_DEPTH:
                        _fail("CODE_AUDIT_DEPTH_LIMIT_EXCEEDED", "Code audit depth limit exceeded")
                    child_directories.append((entry, depth + 1))
            elif stat.S_ISREG(metadata.st_mode):
                if entry.suffix in ALLOWED_EXTENSIONS:
                    if metadata.st_size > MAX_FILE_BYTES:
                        _fail("CODE_AUDIT_FILE_SIZE_EXCEEDED", "A code audit file exceeds its size limit")
                    candidates.append(_Candidate(entry, _relative(root, entry), metadata))
                    if len(candidates) > MAX_FILES:
                        _fail("CODE_AUDIT_FILE_LIMIT_EXCEEDED", "Code audit file limit exceeded")
            else:
                _fail("CODE_AUDIT_UNSAFE_FILE_TYPE", "Code audit encountered an unsafe file type")
        stack.extend(reversed(child_directories))
    candidates.sort(key=lambda item: item.relative)
    if sum(item.metadata.st_size for item in candidates) > MAX_TOTAL_BYTES:
        _fail("CODE_AUDIT_TOTAL_SIZE_EXCEEDED", "Code audit total size limit exceeded")
    return tuple(candidates), directories


def _identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        metadata.st_mode,
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _cross_handle_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    """Fields with matching semantics between path and handle stats."""

    return (
        metadata.st_mode,
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _read_candidate(candidate: _Candidate) -> tuple[str, int]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(candidate.path, flags)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _cross_handle_identity(opened)
            != _cross_handle_identity(candidate.metadata)
        ):
            _fail("CODE_AUDIT_FILE_CHANGED", "A code audit file changed before reading")
        chunks: list[bytes] = []
        remaining = MAX_FILE_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after_handle = os.fstat(descriptor)
        after_path = os.lstat(candidate.path)
    except SkillExecutionError:
        raise
    except OSError as exc:
        raise SkillExecutionError(
            "CODE_AUDIT_READ_FAILED", "A code audit file could not be read"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    data = b"".join(chunks)
    if len(data) > MAX_FILE_BYTES:
        _fail("CODE_AUDIT_FILE_SIZE_EXCEEDED", "A code audit file exceeds its size limit")
    if (
        _identity(after_handle) != _identity(opened)
        or _identity(after_path) != _identity(candidate.metadata)
        or _cross_handle_identity(after_path) != _cross_handle_identity(opened)
    ):
        _fail("CODE_AUDIT_FILE_CHANGED", "A code audit file changed while being read")
    if b"\x00" in data:
        _fail("CODE_AUDIT_BINARY_FILE", "A code audit candidate is binary")
    bom = b"\xef\xbb\xbf"
    if data.find(bom, 1) >= 0:
        _fail("CODE_AUDIT_INVALID_ENCODING", "A UTF-8 BOM is only valid at the file start")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SkillExecutionError(
            "CODE_AUDIT_INVALID_ENCODING", "A code audit candidate is not valid UTF-8"
        ) from exc
    return text, len(data)


def _mask_non_code(text: str, *, python: bool) -> str:
    result = list(text)
    index = 0
    state = "code"
    quote = ""
    triple = False
    while index < len(text):
        char = text[index]
        following = text[index : index + 3]
        pair = text[index : index + 2]
        if state == "code":
            if python and char == "#":
                state = "line-comment"
                result[index] = " "
            elif not python and pair == "//":
                state = "line-comment"
                result[index] = result[index + 1] = " "
                index += 1
            elif not python and pair == "/*":
                state = "block-comment"
                result[index] = result[index + 1] = " "
                index += 1
            elif char in {"'", '"'} or (not python and char == "`"):
                quote = char
                triple = python and following == char * 3
                state = "string"
                width = 3 if triple else 1
                for offset in range(width):
                    result[index + offset] = " "
                index += width - 1
        elif state == "line-comment":
            if char == "\n":
                state = "code"
            else:
                result[index] = " "
        elif state == "block-comment":
            result[index] = " "
            if pair == "*/":
                result[index + 1] = " "
                index += 1
                state = "code"
        else:
            result[index] = " "
            if char == "\\":
                if index + 1 < len(text):
                    result[index + 1] = " "
                    index += 1
            elif triple and following == quote * 3:
                for offset in range(3):
                    result[index + offset] = " "
                index += 2
                state = "code"
            elif not triple and char == quote:
                state = "code"
        index += 1
    return "".join(result)


_DYNAMIC = re.compile(r"\b(?:eval|exec)\s*\(|\bnew\s+Function\s*\(")
_SHELL = re.compile(
    r"\bos\.system\s*\(|\bchild_process\.exec\s*\(|\bexecSync\s*\(|"
    r"\bsubprocess\.[A-Za-z_][A-Za-z0-9_]*\s*\([^\n]{0,300}\bshell\s*=\s*True\b"
)
_TLS = re.compile(
    r"\bverify\s*=\s*False\b|\brejectUnauthorized\s*:\s*false\b"
)
_TLS_STRING = re.compile(r"\bNODE_TLS_REJECT_UNAUTHORIZED\s*=\s*(['\"])0\1")
_SECRET = re.compile(
    r"(?i)\b([A-Za-z_][A-Za-z0-9_]*(?:secret|token|password|api_key|access_key)[A-Za-z0-9_]*)"
    r"\s*(?::[^=\n]+)?=\s*(['\"])([^'\"\r\n]+)\2"
)
_WEAK_RANDOM = re.compile(r"\b(?:Math\.random|random\.random)\s*\(")
_SECURITY_IDENTIFIER = re.compile(r"(?i)\b(?:[A-Za-z0-9_]*(?:token|otp|nonce|secret)[A-Za-z0-9_]*)\b")


def _safe_evidence(value: str) -> str:
    cleaned = _CONTROL_CHARACTERS.sub("", value).replace("\r\n", "\n").replace("\r", "\n")
    return cleaned[:MAX_EVIDENCE_CHARS]


def _finding(
    *,
    rule_id: str,
    severity: CodeAuditSeverity,
    classification: CodeAuditClassification,
    relative: str,
    line_number: int,
    start: int,
    end: int,
    evidence: str,
    observation: str,
    justification: str,
    suggestion: str,
) -> CodeAuditFinding:
    return CodeAuditFinding(
        rule_id,
        severity,
        classification,
        relative,
        CodeAuditRegion(line_number, line_number, start + 1, max(start + 1, end)),
        _safe_evidence(evidence),
        observation,
        justification,
        suggestion,
    )


def _analyze_file(relative: str, text: str) -> tuple[CodeAuditFinding, ...]:
    python = Path(relative).suffix in {".py", ".pyi"}
    active = _mask_non_code(text, python=python)
    source_lines = text.splitlines()
    active_lines = active.splitlines()
    findings: list[CodeAuditFinding] = []
    for line_number, (source, code) in enumerate(zip(source_lines, active_lines), 1):
        for match in _DYNAMIC.finditer(code):
            findings.append(_finding(
                rule_id="CA001", severity=CodeAuditSeverity.HIGH,
                classification=CodeAuditClassification.HYPOTHESIS,
                relative=relative, line_number=line_number, start=match.start(), end=match.end(),
                evidence=source.strip(), observation="A dynamic code evaluation call is present.",
                justification="Dynamic evaluation may execute data as code if untrusted input reaches this call.",
                suggestion="Remove dynamic evaluation or constrain input with a non-executable parser.",
            ))
        for match in _SHELL.finditer(code):
            findings.append(_finding(
                rule_id="CA002", severity=CodeAuditSeverity.HIGH,
                classification=CodeAuditClassification.HYPOTHESIS,
                relative=relative, line_number=line_number, start=match.start(), end=match.end(),
                evidence=source.strip(), observation="An explicit shell execution call is present.",
                justification="Shell execution may permit command injection if arguments include untrusted data.",
                suggestion="Use a direct process API with a fixed executable and an argument vector, without shell.",
            ))
        for match in _TLS.finditer(code):
            findings.append(_finding(
                rule_id="CA003", severity=CodeAuditSeverity.HIGH,
                classification=CodeAuditClassification.OBSERVED,
                relative=relative, line_number=line_number, start=match.start(), end=match.end(),
                evidence=source.strip(), observation="TLS certificate verification is explicitly disabled.",
                justification="The literal configuration prevents normal peer certificate validation.",
                suggestion="Enable certificate verification and configure a valid trust chain.",
            ))
        for match in _TLS_STRING.finditer(source):
            operator = source.find("=", match.start(), match.end())
            if operator < 0 or code[match.start()] == " " or code[operator] == " ":
                continue
            findings.append(_finding(
                rule_id="CA003", severity=CodeAuditSeverity.HIGH,
                classification=CodeAuditClassification.OBSERVED,
                relative=relative, line_number=line_number, start=match.start(), end=match.end(),
                evidence=source.strip(), observation="TLS certificate verification is explicitly disabled.",
                justification="The literal configuration prevents normal peer certificate validation.",
                suggestion="Enable certificate verification and configure a valid trust chain.",
            ))
        for match in _SECRET.finditer(source):
            operator = source.find("=", match.start(), match.end())
            if operator < 0 or operator >= len(code) or code[match.start()] == " " or code[operator] == " ":
                continue
            redacted = source[: match.start(3)] + "<redacted>" + source[match.end(3) :]
            findings.append(_finding(
                rule_id="CA004", severity=CodeAuditSeverity.HIGH,
                classification=CodeAuditClassification.HYPOTHESIS,
                relative=relative, line_number=line_number, start=match.start(1), end=match.end(1),
                evidence=redacted.strip(), observation="A non-empty literal is assigned to a sensitive identifier.",
                justification="The literal may be a hardcoded credential; placeholders and test values require human confirmation.",
                suggestion="Load secrets from an approved secret provider and rotate any real exposed value.",
            ))
        weak = _WEAK_RANDOM.search(code)
        identifier = _SECURITY_IDENTIFIER.search(code)
        if weak is not None and identifier is not None:
            findings.append(_finding(
                rule_id="CA005", severity=CodeAuditSeverity.MEDIUM,
                classification=CodeAuditClassification.HYPOTHESIS,
                relative=relative, line_number=line_number, start=weak.start(), end=weak.end(),
                evidence=source.strip(), observation="A non-cryptographic random generator appears in an expression with a security identifier.",
                justification="Predictable randomness may weaken tokens, OTPs, nonces or secrets if this expression creates one.",
                suggestion="Confirm the data purpose and use a cryptographically secure random generator when security-sensitive.",
            ))
        if len(findings) > MAX_FINDINGS:
            _fail("CODE_AUDIT_FINDING_LIMIT_EXCEEDED", "Code audit finding limit exceeded")
    return tuple(findings)


def _summary(directories: int, files: int, bytes_read: int, findings: tuple[CodeAuditFinding, ...]) -> CodeAuditSummary:
    counts = {severity: 0 for severity in CodeAuditSeverity}
    for finding in findings:
        counts[finding.severity] += 1
    return CodeAuditSummary(
        directories, files, bytes_read,
        counts[CodeAuditSeverity.INFO], counts[CodeAuditSeverity.LOW],
        counts[CodeAuditSeverity.MEDIUM], counts[CodeAuditSeverity.HIGH],
        counts[CodeAuditSeverity.CRITICAL],
        ("CA001", "CA002", "CA003", "CA004", "CA005"), RULESET_VERSION,
        tuple(sorted(ALLOWED_EXTENSIONS)), MAX_DEPTH, MAX_DIRECTORIES, MAX_FILES,
        MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_FINDINGS,
    )


def run_code_audit(target_project: Any) -> SkillExecutionResult:
    inventory = read_source_documents(target_project, max_depth=MAX_DEPTH, max_directories=MAX_DIRECTORIES, max_files=MAX_FILES, max_file_bytes=MAX_FILE_BYTES, max_total_bytes=MAX_TOTAL_BYTES)
    findings: list[CodeAuditFinding] = []
    bytes_read = 0
    for document in inventory.documents:
        bytes_read += document.bytes_read
        if bytes_read > MAX_TOTAL_BYTES:
            _fail("CODE_AUDIT_TOTAL_SIZE_EXCEEDED", "Code audit total size limit exceeded")
        findings.extend(_analyze_file(document.path, document.text))
        if len(findings) > MAX_FINDINGS:
            _fail("CODE_AUDIT_FINDING_LIMIT_EXCEEDED", "Code audit finding limit exceeded")
    ordered = tuple(sorted(
        findings,
        key=lambda item: (
            item.file, item.region.start_line, item.region.start_column or 0, item.rule_id
        ),
    ))
    summary = _summary(inventory.directories, len(inventory.documents), bytes_read, ordered)
    evidence = [SkillExecutionEvidence(
        "code_audit_summary", Status.OK, "Code audit scan completed.", summary, "ok"
    )]
    evidence.extend(
        SkillExecutionEvidence(
            "code_audit_finding", Status.WARNING,
            f"{finding.rule_id}: {finding.observation}", finding, finding.rule_id,
        )
        for finding in ordered
    )
    status = SkillExecutionStatus.PASSED if not ordered else SkillExecutionStatus.COMPLETED_WITH_FINDINGS
    exit_code = 0 if not ordered else 3
    return SkillExecutionResult("code-audit", status, exit_code, tuple(evidence))
