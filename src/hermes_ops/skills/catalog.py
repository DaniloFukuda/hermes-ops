from __future__ import annotations

from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import stat
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from hermes_ops.core.errors import SkillCatalogError


_DISTRIBUTION_NAME = "hermes-ops"
_CATALOG_PARTS = ("hermes_ops_skill_catalog", "skills")
_CATALOG_MARKER_PARTS = _CATALOG_PARTS


def _fail(code: str, message: str) -> None:
    raise SkillCatalogError(code, message)


def _require_directory(path: Path, *, editable: bool) -> None:
    description = "editable Hermes" if editable else "installed Hermes"
    try:
        information = os.lstat(path)
    except FileNotFoundError as exc:
        raise SkillCatalogError(
            "SKILL_CATALOG_NOT_FOUND",
            f"The {description} distribution does not provide a skill catalog",
        ) from exc
    except OSError as exc:
        raise SkillCatalogError(
            "SKILL_CATALOG_INVALID",
            f"The {description} skill catalog could not be inspected",
        ) from exc
    if not stat.S_ISDIR(information.st_mode):
        _fail(
            "SKILL_CATALOG_INVALID",
            f"The {description} skill catalog is not a directory resource",
        )


def _editable_catalog_root(distribution: metadata.Distribution) -> Path | None:
    try:
        raw = distribution.read_text("direct_url.json")
        document = json.loads(raw) if raw is not None else None
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
        raise SkillCatalogError(
            "SKILL_CATALOG_INVALID",
            "The installed Hermes distribution metadata is invalid",
        ) from exc
    if document is None:
        return None
    if not isinstance(document, dict):
        _fail(
            "SKILL_CATALOG_INVALID",
            "The installed Hermes distribution metadata is invalid",
        )
    directory_info = document.get("dir_info")
    if not isinstance(directory_info, dict) or directory_info.get("editable") is not True:
        return None
    source_url = document.get("url")
    if type(source_url) is not str:
        _fail(
            "SKILL_CATALOG_INVALID",
            "The editable Hermes distribution does not declare its source root",
        )
    parsed = urlparse(source_url)
    if parsed.scheme != "file" or parsed.params or parsed.query or parsed.fragment:
        _fail(
            "SKILL_CATALOG_INVALID",
            "The editable Hermes distribution source root is not a local file resource",
        )
    source_root = Path(url2pathname(unquote(parsed.path)))
    if parsed.netloc:
        source_root = Path(f"//{parsed.netloc}{url2pathname(unquote(parsed.path))}")
    return source_root


def resolve_own_skill_catalog() -> Path:
    """Return the sole catalog root recorded by the installed distribution."""

    try:
        distribution = metadata.distribution(_DISTRIBUTION_NAME)
        files = distribution.files
    except (metadata.PackageNotFoundError, OSError, ValueError) as exc:
        raise SkillCatalogError(
            "SKILL_CATALOG_NOT_FOUND",
            "The installed Hermes distribution does not provide a skill catalog",
        ) from exc

    editable_root = _editable_catalog_root(distribution)
    if editable_root is not None:
        catalog_root = editable_root
        _require_directory(catalog_root / "skills", editable=True)
        return catalog_root

    if files is None:
        _fail(
            "SKILL_CATALOG_NOT_FOUND",
            "The installed Hermes distribution does not record a skill catalog",
        )

    catalog_entries = tuple(
        (entry, PurePosixPath(str(entry).replace("\\", "/")).parts)
        for entry in files
        if _CATALOG_MARKER_PARTS
        == PurePosixPath(str(entry).replace("\\", "/")).parts[-4:-2]
        and PurePosixPath(str(entry).replace("\\", "/")).parts[-1:] == ("SKILL.md",)
    )
    roots = {
        parts[:-4]
        for _, parts in catalog_entries
    }
    recorded_paths = tuple(str(entry) for entry, _ in catalog_entries)
    if (
        not catalog_entries
        or len(roots) != 1
        or len(set(recorded_paths)) != len(recorded_paths)
    ):
        _fail(
            "SKILL_CATALOG_NOT_FOUND" if not catalog_entries else "SKILL_CATALOG_INVALID",
            "The installed Hermes distribution must contain exactly one skill catalog",
        )

    try:
        anchor = Path(distribution.locate_file(catalog_entries[0][0]))
        catalog_root = anchor.parents[2]
        anchor_is_file = anchor.is_file()
        catalog_is_directory = catalog_root.is_dir()
    except (IndexError, OSError, RuntimeError, TypeError, ValueError) as exc:
        raise SkillCatalogError(
            "SKILL_CATALOG_INVALID",
            "The installed Hermes skill catalog could not be inspected",
        ) from exc

    if not anchor_is_file or not catalog_is_directory:
        _fail(
            "SKILL_CATALOG_INVALID",
            "The installed Hermes skill catalog is not a valid directory resource",
        )
    return catalog_root
