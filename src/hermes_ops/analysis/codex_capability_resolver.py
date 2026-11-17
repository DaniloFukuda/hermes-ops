from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from hermes_ops.analysis.codex_adapter import CodexCapability
from hermes_ops.execution import ExecutionContext


_ALLOWED_EXECUTABLE_NAMES = frozenset({"codex", "codex.cmd", "codex.exe"})
_ALLOWED_NETWORK_POLICIES = frozenset({"disabled", "provider-only"})


@dataclass(frozen=True, slots=True)
class CodexCapabilityConfig:
    """Explicit host configuration; no field is derived from ambient state."""

    executable_path: Path | None = None
    working_directory: Path | None = None
    target_path: Path | None = None
    repository_path: Path | None = None
    env: Mapping[str, str] | None = None
    env_allowlist: tuple[str, ...] = ()
    execution_context: ExecutionContext | None = None
    timeout_seconds: int = 180
    max_stdout_bytes: int = 1_048_576
    max_stderr_bytes: int = 262_144
    authorization_approved: bool = False
    validated_version: str | None = None
    supported_version_range: str | None = None
    auth_configured: bool = False
    home_directory: Path | None = None
    config_directory: Path | None = None
    cache_directory: Path | None = None
    network_policy: str = "unresolved"
    network_policy_verified: bool = False
    tools_policy: str = "unresolved"
    tools_policy_verified: bool = False


@dataclass(frozen=True, slots=True)
class CodexCapabilityResolution:
    capability: CodexCapability | None
    gaps: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.capability is not None and not self.gaps


def resolve_codex_capability(
    config: CodexCapabilityConfig | None,
) -> CodexCapabilityResolution:
    if config is None:
        return CodexCapabilityResolution(
            None,
            ("CAPABILITY_CONFIG_MISSING",),
            ("Explicit Codex capability configuration is required",),
        )

    gaps: list[str] = []
    executable_path = _resolve_executable(config, gaps)
    working_directory = _resolve_directory(config.working_directory, "WORKING_DIRECTORY_INVALID", gaps)
    target_path = _resolve_directory(config.target_path, "TARGET_BOUNDARY_INVALID", gaps)
    repository_path = _resolve_directory(config.repository_path, "REPOSITORY_BOUNDARY_INVALID", gaps)

    if working_directory is not None:
        for boundary_name, boundary in (("TARGET", target_path), ("REPOSITORY", repository_path)):
            if boundary is not None and _is_within(working_directory, boundary):
                gaps.append("WORKING_DIRECTORY_INSIDE_TARGET_OR_REPOSITORY")

    environment = _resolve_environment(config, gaps)
    _validate_positive_int(config.timeout_seconds, "TIMEOUT_INVALID", gaps)
    _validate_positive_int(config.max_stdout_bytes, "STDOUT_LIMIT_INVALID", gaps)
    _validate_positive_int(config.max_stderr_bytes, "STDERR_LIMIT_INVALID", gaps)

    if type(config.execution_context) is not ExecutionContext:
        gaps.append("EXECUTION_CONTEXT_MISSING")
    if not config.authorization_approved:
        gaps.append("AUTHORIZATION_NOT_APPROVED")
    if not config.validated_version or not config.supported_version_range:
        gaps.append("VERSION_NOT_VALIDATED")
    if not config.auth_configured:
        gaps.append("AUTH_NOT_CONFIGURED")

    home = _resolve_directory(config.home_directory, "HOME_DIRECTORY_INVALID", gaps)
    config_dir = _resolve_directory(config.config_directory, "CONFIG_DIRECTORY_INVALID", gaps)
    cache = _resolve_directory(config.cache_directory, "CACHE_DIRECTORY_INVALID", gaps)
    for isolated in (home, config_dir, cache):
        if isolated is not None:
            for boundary in (target_path, repository_path):
                if boundary is not None and _is_within(isolated, boundary):
                    gaps.append("ISOLATED_DIRECTORY_INSIDE_TARGET_OR_REPOSITORY")

    if config.network_policy not in _ALLOWED_NETWORK_POLICIES:
        gaps.append("NETWORK_POLICY_UNRESOLVED")
    elif not config.network_policy_verified:
        gaps.append("NETWORK_POLICY_UNVERIFIED")
    if config.tools_policy != "disabled":
        gaps.append("TOOLS_POLICY_UNRESOLVED")
    elif not config.tools_policy_verified:
        gaps.append("TOOLS_POLICY_UNVERIFIED")

    unique_gaps = tuple(dict.fromkeys(gaps))
    if unique_gaps:
        return CodexCapabilityResolution(None, unique_gaps, unique_gaps)

    capability = CodexCapability(
        executable_path=executable_path,
        working_directory=working_directory,
        env=environment,
        execution_context=config.execution_context,
        timeout_seconds=config.timeout_seconds,
        max_stdout_bytes=config.max_stdout_bytes,
        max_stderr_bytes=config.max_stderr_bytes,
        authorization_approved=True,
        version_validated=True,
        auth_configured=True,
        home_config_isolated=True,
        network_policy=config.network_policy,
        tools_policy="disabled",
    )
    return CodexCapabilityResolution(capability, (), ("CODEX_CAPABILITY_READY",))


def _resolve_executable(config: CodexCapabilityConfig, gaps: list[str]) -> Path | None:
    path = config.executable_path
    if path is None:
        gaps.append("EXECUTABLE_NOT_CONFIGURED")
        return None
    if not isinstance(path, Path) or not path.is_absolute():
        gaps.append("EXECUTABLE_NOT_ABSOLUTE")
        return None
    if path.name.casefold() not in _ALLOWED_EXECUTABLE_NAMES:
        gaps.append("EXECUTABLE_NAME_UNAUTHORIZED")
    try:
        resolved = path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        gaps.append("EXECUTABLE_NOT_FOUND")
        return None
    if not resolved.is_file():
        gaps.append("EXECUTABLE_NOT_FILE")
        return None
    return resolved


def _resolve_directory(
    path: Path | None,
    missing_code: str,
    gaps: list[str],
) -> Path | None:
    if path is None:
        gaps.append(missing_code)
        return None
    if not isinstance(path, Path):
        gaps.append(missing_code)
        return None
    try:
        resolved = path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        gaps.append(missing_code)
        return None
    if not resolved.is_dir():
        gaps.append(missing_code)
        return None
    return resolved


def _resolve_environment(
    config: CodexCapabilityConfig,
    gaps: list[str],
) -> dict[str, str] | None:
    if not isinstance(config.env, Mapping):
        gaps.append("ENV_NOT_CONFIGURED")
        return None
    if not all(isinstance(name, str) for name in config.env_allowlist):
        gaps.append("ENV_ALLOWLIST_INVALID")
        return None
    allowlist = set(config.env_allowlist)
    environment: dict[str, str] = {}
    for name, value in config.env.items():
        if not isinstance(name, str) or not isinstance(value, str):
            gaps.append("ENV_INVALID")
            continue
        if name not in allowlist:
            gaps.append("ENV_NOT_ALLOWLISTED")
            continue
        environment[name] = value
    return environment


def _validate_positive_int(value: object, code: str, gaps: list[str]) -> None:
    if type(value) is not int or value <= 0:
        gaps.append(code)


def _is_within(path: Path, boundary: Path) -> bool:
    try:
        path.relative_to(boundary)
    except ValueError:
        return False
    return True
