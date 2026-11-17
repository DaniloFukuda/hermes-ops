from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.skills import controlled_reader
from hermes_ops.skills.controlled_reader import read_source_documents


def _write(root: Path, relative: str, content: str = "value = 1\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _error_code(caught: pytest.ExceptionInfo[SkillExecutionError]) -> str:
    return caught.value.code


def test_pytest_tmp_is_pruned_without_iterdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec: HERMES-0008 / AC-43"""
    artifact = tmp_path / ".pytest_tmp"
    artifact.mkdir()
    _write(tmp_path, "source.py")
    real_iterdir = Path.iterdir

    def guarded_iterdir(path: Path):
        if path == artifact:
            raise AssertionError("pruned pytest artifact was enumerated")
        return real_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)

    inventory = read_source_documents(tmp_path)

    assert [document.path for document in inventory.documents] == ["source.py"]


@pytest.mark.parametrize("name", [".pytest_verify", ".pytest_session_artifacts"])
def test_pytest_artifact_family_is_pruned(tmp_path: Path, name: str) -> None:
    """Spec: HERMES-0008 / AC-44"""
    _write(tmp_path, f"{name}/ignored.py")
    _write(tmp_path, "source.py")

    inventory = read_source_documents(tmp_path)

    assert [document.path for document in inventory.documents] == ["source.py"]


def test_version_suffixed_python_environment_is_pruned(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-45"""
    _write(tmp_path, ".venv312/Lib/site-packages/ignored.py")
    _write(tmp_path, "source.py")

    inventory = read_source_documents(tmp_path)

    assert [document.path for document in inventory.documents] == ["source.py"]


def test_unreadable_code_directory_still_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec: HERMES-0008 / AC-46"""
    code_directory = tmp_path / "application"
    code_directory.mkdir()
    _write(tmp_path, ".gitignore", "application/\n")
    real_iterdir = Path.iterdir

    def guarded_iterdir(path: Path):
        if path == code_directory:
            raise PermissionError("denied")
        return real_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)

    with pytest.raises(SkillExecutionError) as caught:
        read_source_documents(tmp_path)

    assert _error_code(caught) == "CODE_AUDIT_READ_FAILED"


def test_reparse_point_is_rejected_before_pytest_pruning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec: HERMES-0008 / AC-47, AC-51"""
    artifact = tmp_path / ".pytest_tmp"
    artifact.mkdir()
    real_lstat = os.lstat

    def guarded_lstat(path: os.PathLike[str] | str):
        if Path(path) == artifact:
            return SimpleNamespace(
                st_mode=artifact.stat().st_mode,
                st_file_attributes=controlled_reader._REPARSE,
            )
        return real_lstat(path)

    monkeypatch.setattr(os, "lstat", guarded_lstat)

    with pytest.raises(SkillExecutionError) as caught:
        read_source_documents(tmp_path)

    assert _error_code(caught) == "CODE_AUDIT_UNSAFE_PATH"
    assert ".pytest_tmp" in str(caught.value)
    assert str(tmp_path) not in str(caught.value)


def test_unsafe_path_error_names_only_sanitized_relative_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec: HERMES-0008 / AC-50"""
    offending = _write(tmp_path, "nested/offending.py")
    real_lstat = os.lstat

    def guarded_lstat(path: os.PathLike[str] | str):
        if Path(path) == offending:
            metadata = real_lstat(path)
            return SimpleNamespace(
                st_mode=metadata.st_mode,
                st_file_attributes=controlled_reader._REPARSE,
            )
        return real_lstat(path)

    monkeypatch.setattr(os, "lstat", guarded_lstat)

    with pytest.raises(SkillExecutionError) as caught:
        read_source_documents(tmp_path)

    message = str(caught.value)
    assert _error_code(caught) == "CODE_AUDIT_UNSAFE_PATH"
    assert "nested/offending.py" in message
    assert str(tmp_path) not in message


def test_pruning_preserves_deterministic_document_order(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-48"""
    _write(tmp_path, "z.py", "z = 1\n")
    _write(tmp_path, ".pytest_verify/ignored.py")
    _write(tmp_path, "a.py", "a = 1\n")

    first = read_source_documents(tmp_path)
    second = read_source_documents(tmp_path)

    assert first == second
    assert [document.path for document in first.documents] == ["a.py", "z.py"]


def test_pruning_preserves_structural_and_file_limits(tmp_path: Path) -> None:
    """Spec: HERMES-0008 / AC-49"""
    _write(tmp_path, ".pytest_verify/nested/deep/ignored.py")
    _write(tmp_path, "source.py")

    inventory = read_source_documents(
        tmp_path,
        max_directories=2,
        max_files=1,
    )
    assert [document.path for document in inventory.documents] == ["source.py"]

    _write(tmp_path, "second.py")
    with pytest.raises(SkillExecutionError) as caught:
        read_source_documents(tmp_path, max_directories=2, max_files=1)
    assert _error_code(caught) == "CODE_AUDIT_FILE_LIMIT_EXCEEDED"
