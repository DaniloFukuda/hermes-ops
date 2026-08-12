from pathlib import Path
import tarfile
import zipfile

from test_packaging import built_artifacts


def test_wheel_and_sdist_include_analysis_contract_without_provider(
    built_artifacts: dict[str, Path],
) -> None:
    """Spec: HERMES-0010 / AC-35"""
    suffix = "hermes_ops/analysis/adapter.py"
    with zipfile.ZipFile(built_artifacts["wheel"]) as archive:
        assert any(name.endswith(suffix) for name in archive.namelist())
        assert not any("openai" in name.casefold() for name in archive.namelist())
    with tarfile.open(built_artifacts["sdist"], "r:gz") as archive:
        assert any(member.name.endswith(suffix) for member in archive.getmembers())
