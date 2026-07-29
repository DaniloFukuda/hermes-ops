from pathlib import Path

import pytest

from hermes_ops.core.errors import PathResolutionError
from hermes_ops.core.paths import project_relative_path, resolve_directory


def test_missing_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(PathResolutionError):
        resolve_directory(tmp_path / "missing")


def test_file_is_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("", encoding="utf-8")
    with pytest.raises(PathResolutionError):
        resolve_directory(file_path)


@pytest.mark.parametrize("name", ["path with spaces", "projeto-ação"])
def test_space_and_unicode_paths(tmp_path: Path, name: str) -> None:
    target = tmp_path / name
    target.mkdir()
    assert resolve_directory(target) == target.resolve()


def test_relative_path_uses_explicit_base(tmp_path: Path) -> None:
    target = tmp_path / "nested"
    target.mkdir()
    assert resolve_directory("nested", base=tmp_path) == target.resolve()


def test_valid_contained_project_path(tmp_path: Path) -> None:
    assert project_relative_path(tmp_path, "path with spaces/ação") == (
        tmp_path / "path with spaces/ação"
    ).resolve()


@pytest.mark.parametrize(
    "value",
    ["../outside", "../../file", "C:\\outside\\python.exe", "/outside/python"],
)
def test_project_path_escape_is_rejected(tmp_path: Path, value: str) -> None:
    with pytest.raises(PathResolutionError):
        project_relative_path(tmp_path, value)


def test_nonexistent_but_contained_path_is_allowed(tmp_path: Path) -> None:
    result = project_relative_path(tmp_path, "missing/python")
    assert result == (tmp_path / "missing/python").resolve()


def test_external_symlink_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are not available")
    with pytest.raises(PathResolutionError):
        project_relative_path(root, "link/python")
