from dataclasses import replace
from pathlib import Path

from hermes_ops.analysis.codex_capability_resolver import (
    CodexCapabilityConfig,
    resolve_codex_capability,
)
from hermes_ops.execution import ExecutionBudget, ExecutionContext


def _context() -> ExecutionContext:
    return ExecutionContext(
        ExecutionBudget(
            max_units=10,
            used_units=0,
            validation_reserve=2,
            closure_reserve=2,
            warning_threshold=3,
            checkpoint_threshold=5,
        )
    )


def _config(tmp_path: Path, **changes: object) -> CodexCapabilityConfig:
    target = tmp_path / "target"
    repository = tmp_path / "repository"
    neutral = tmp_path / "neutral"
    home = tmp_path / "home"
    config_dir = tmp_path / "config"
    cache = tmp_path / "cache"
    for path in (target, repository, neutral, home, config_dir, cache):
        path.mkdir()
    executable = tmp_path / "codex.cmd"
    executable.write_text("synthetic", encoding="utf-8")
    values = dict(
        executable_path=executable,
        working_directory=neutral,
        target_path=target,
        repository_path=repository,
        env={"CODEX_AUTH_REF": "host-managed"},
        env_allowlist=("CODEX_AUTH_REF",),
        execution_context=_context(),
        timeout_seconds=180,
        max_stdout_bytes=1_048_576,
        max_stderr_bytes=262_144,
        authorization_approved=True,
        validated_version="0.1.0",
        supported_version_range=">=0.1,<1",
        auth_configured=True,
        home_directory=home,
        config_directory=config_dir,
        cache_directory=cache,
        network_policy="provider-only",
        network_policy_verified=True,
        tools_policy="disabled",
        tools_policy_verified=True,
    )
    values.update(changes)
    return CodexCapabilityConfig(**values)


def test_missing_config_fails_closed() -> None:
    result = resolve_codex_capability(None)
    assert result.capability is None
    assert "CAPABILITY_CONFIG_MISSING" in result.gaps


def test_executable_must_exist_be_absolute_and_authorized(tmp_path: Path) -> None:
    base = _config(tmp_path)
    missing = resolve_codex_capability(replace(base, executable_path=tmp_path / "missing.cmd"))
    assert missing.capability is None
    assert "EXECUTABLE_NOT_FOUND" in missing.gaps

    relative = resolve_codex_capability(replace(base, executable_path=Path("codex.cmd")))
    assert relative.capability is None
    assert "EXECUTABLE_NOT_ABSOLUTE" in relative.gaps

    other = tmp_path / "other.exe"
    other.write_text("synthetic", encoding="utf-8")
    unauthorized = resolve_codex_capability(replace(base, executable_path=other))
    assert unauthorized.capability is None
    assert "EXECUTABLE_NAME_UNAUTHORIZED" in unauthorized.gaps


def test_working_directory_must_be_explicit_and_outside_known_roots(tmp_path: Path) -> None:
    base = _config(tmp_path)
    invalid = resolve_codex_capability(replace(base, working_directory=tmp_path / "missing"))
    assert invalid.capability is None
    assert "WORKING_DIRECTORY_INVALID" in invalid.gaps

    inside_target = base.target_path / "neutral"
    inside_target.mkdir()
    nested = resolve_codex_capability(replace(base, working_directory=inside_target))
    assert nested.capability is None
    assert "WORKING_DIRECTORY_INSIDE_TARGET_OR_REPOSITORY" in nested.gaps


def test_environment_allowlist_rejects_unapproved_names_without_leaking_values(
    tmp_path: Path,
) -> None:
    base = _config(tmp_path, env={"SECRET_TOKEN": "do-not-print"}, env_allowlist=("SAFE",))
    result = resolve_codex_capability(base)
    text = " ".join(result.gaps + result.reasons)
    assert result.capability is None
    assert "ENV_NOT_ALLOWLISTED" in result.gaps
    assert "do-not-print" not in text


def test_home_config_cache_directories_are_required(tmp_path: Path) -> None:
    base = _config(tmp_path, cache_directory=None)
    result = resolve_codex_capability(base)
    assert result.capability is None
    assert "CACHE_DIRECTORY_INVALID" in result.gaps


def test_authentication_and_version_must_be_attested(tmp_path: Path) -> None:
    base = _config(tmp_path, auth_configured=False, validated_version=None)
    result = resolve_codex_capability(base)
    assert result.capability is None
    assert "AUTH_NOT_CONFIGURED" in result.gaps
    assert "VERSION_NOT_VALIDATED" in result.gaps


def test_network_and_tools_require_technical_attestation(tmp_path: Path) -> None:
    base = _config(tmp_path, network_policy_verified=False, tools_policy_verified=False)
    result = resolve_codex_capability(base)
    assert result.capability is None
    assert "NETWORK_POLICY_UNVERIFIED" in result.gaps
    assert "TOOLS_POLICY_UNVERIFIED" in result.gaps


def test_valid_capability_is_produced_only_when_all_gates_pass(tmp_path: Path) -> None:
    result = resolve_codex_capability(_config(tmp_path))
    assert result.ready is True
    assert result.gaps == ()
    assert result.capability is not None
    assert result.capability.working_directory == (tmp_path / "neutral").resolve()
    assert result.capability.env == {"CODEX_AUTH_REF": "host-managed"}
