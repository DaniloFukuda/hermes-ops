from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from pathlib import Path
import sys

import pytest

from conftest import git


REQUIRED_SECTIONS = (
    "Objetivo",
    "Entradas",
    "Pré-condições",
    "Procedimento",
    "Saídas",
    "Falhas",
    "Restrições",
    "Evidências",
    "Pós-condições",
)

DEFAULT_METADATA = (
    "schema_version: 1",
    "id: example-skill",
    "version: 1",
    "status: active",
    "description: Example skill",
    "risk: low",
    "requires: []",
    "allows_write: false",
)


def _body(*, sections: tuple[str, ...] = REQUIRED_SECTIONS) -> str:
    return "\n# Example Skill\n\n" + "\n\n".join(
        f"## {section}\n\nConteúdo de {section}." for section in sections
    ) + "\n"


def _document(
    *,
    metadata: tuple[str, ...] = DEFAULT_METADATA,
    body: str | None = None,
) -> str:
    markdown = _body() if body is None else body
    return "---\n" + "\n".join(metadata) + "\n---\n" + markdown


def _replace_metadata(
    metadata: tuple[str, ...],
    key: str,
    replacement: str | tuple[str, ...] | None,
) -> tuple[str, ...]:
    prefix = f"{key}:"
    index = next(i for i, line in enumerate(metadata) if line.startswith(prefix))
    values = () if replacement is None else (
        (replacement,) if isinstance(replacement, str) else replacement
    )
    return metadata[:index] + values + metadata[index + 1 :]


def _write_skill(
    root: Path,
    *,
    skill_id: str = "example-skill",
    metadata: tuple[str, ...] | None = None,
    body: str | None = None,
    content: str | None = None,
    raw_bytes: bytes | None = None,
) -> Path:
    directory = root / "skills" / skill_id
    directory.mkdir(parents=True)
    path = directory / "SKILL.md"
    if raw_bytes is not None:
        path.write_bytes(raw_bytes)
        return path
    selected = DEFAULT_METADATA if metadata is None else metadata
    if skill_id != "example-skill" and metadata is None:
        selected = _replace_metadata(selected, "id", f"id: {skill_id}")
    path.write_text(
        _document(metadata=selected, body=body) if content is None else content,
        encoding="utf-8",
    )
    return path


def _skills_api():
    """Load only the minimal public API required by HERMES-0003."""
    try:
        return importlib.import_module("hermes_ops.skills")
    except ModuleNotFoundError as exc:
        if exc.name == "hermes_ops.skills":
            pytest.fail(
                "HERMES-0003 production API is not implemented: "
                "missing hermes_ops.skills",
                pytrace=False,
            )
        raise


def _load_skill(path: Path):
    api = _skills_api()
    assert hasattr(api, "load_skill"), "hermes_ops.skills.load_skill is required"
    return api.load_skill(path)


def _error_code(exc: BaseException) -> str | None:
    return getattr(exc, "code", None)


def _assert_error(path: Path, code: str) -> BaseException:
    with pytest.raises(Exception) as caught:
        _load_skill(path)
    assert _error_code(caught.value) == code
    return caught.value


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _snapshot_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }


def test_loads_only_explicit_path(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-01"""
    selected = _write_skill(tmp_path, skill_id="selected-skill")
    _write_skill(tmp_path, skill_id="broken-sibling", content="invalid")

    definition = _load_skill(selected)

    assert definition.id == "selected-skill"
    assert definition.path == selected


def test_loads_real_git_preflight_skill() -> None:
    """Spec: HERMES-0003 / AC-02"""
    project = Path(__file__).resolve().parents[1]
    path = project / "skills" / "git-preflight" / "SKILL.md"

    definition = _load_skill(path)

    assert definition.id == "git-preflight"
    assert definition.path == path


def test_utf8_accents_and_invalid_encoding(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-03"""
    metadata = _replace_metadata(
        DEFAULT_METADATA,
        "description",
        "description: Validação com acentuação",
    )
    valid = _write_skill(tmp_path / "valid", metadata=metadata)
    assert _load_skill(valid).description == "Validação com acentuação"

    invalid = _write_skill(tmp_path / "invalid", raw_bytes=b"\xff\xfe\x80")
    _assert_error(invalid, "SKILL_INVALID_ENCODING")


def test_front_matter_boundaries(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-04"""
    missing = _write_skill(tmp_path / "missing", content=_body())
    _assert_error(missing, "SKILL_FRONT_MATTER_MISSING")

    unclosed = _write_skill(
        tmp_path / "unclosed",
        content="---\n" + "\n".join(DEFAULT_METADATA) + "\n" + _body(),
    )
    _assert_error(unclosed, "SKILL_FRONT_MATTER_INVALID")


@pytest.mark.parametrize("field", [line.split(":", 1)[0] for line in DEFAULT_METADATA])
def test_exact_required_fields(tmp_path: Path, field: str) -> None:
    """Spec: HERMES-0003 / AC-05"""
    missing = _write_skill(
        tmp_path / "missing",
        metadata=_replace_metadata(DEFAULT_METADATA, field, None),
    )
    _assert_error(missing, "SKILL_REQUIRED_FIELD_MISSING")

    unknown = _write_skill(
        tmp_path / "unknown",
        metadata=DEFAULT_METADATA + ("unexpected: value",),
    )
    _assert_error(unknown, "SKILL_UNKNOWN_FIELD")

    duplicate_line = next(line for line in DEFAULT_METADATA if line.startswith(f"{field}:"))
    duplicate = _write_skill(
        tmp_path / "duplicate",
        metadata=DEFAULT_METADATA + (duplicate_line,),
    )
    _assert_error(duplicate, "SKILL_DUPLICATE_FIELD")


@pytest.mark.parametrize("value", ["01", "+1", "1.0", '"1"', "true", "false"])
def test_schema_version_is_exact_textual_one(tmp_path: Path, value: str) -> None:
    """Spec: HERMES-0003 / AC-06"""
    assert _load_skill(_write_skill(tmp_path / "valid")).schema_version == 1
    invalid = _write_skill(
        tmp_path / "invalid",
        metadata=_replace_metadata(DEFAULT_METADATA, "schema_version", f"schema_version: {value}"),
    )
    _assert_error(invalid, "SKILL_UNSUPPORTED_SCHEMA")


@pytest.mark.parametrize("skill_id", ["git-preflight", "a", "skill-2", "a1-b2"])
def test_id_format_and_directory_match(tmp_path: Path, skill_id: str) -> None:
    """Spec: HERMES-0003 / AC-07"""
    assert _load_skill(_write_skill(tmp_path / "valid", skill_id=skill_id)).id == skill_id

    invalid_ids = ('"git-preflight"', "Upper", "-leading", "trailing-", "with space")
    for index, invalid_id in enumerate(invalid_ids):
        metadata = _replace_metadata(DEFAULT_METADATA, "id", f"id: {invalid_id}")
        path = _write_skill(tmp_path / f"invalid-{index}", metadata=metadata)
        _assert_error(path, "SKILL_INVALID_ID")

    mismatch = _write_skill(
        tmp_path / "mismatch",
        skill_id="directory-id",
        metadata=_replace_metadata(DEFAULT_METADATA, "id", "id: other-id"),
    )
    _assert_error(mismatch, "SKILL_ID_DIRECTORY_MISMATCH")


@pytest.mark.parametrize("value", ["0", "-1", "+1", "01", "1.0", "true", "false", '"1"'])
def test_version_matches_unsigned_positive_decimal(tmp_path: Path, value: str) -> None:
    """Spec: HERMES-0003 / AC-08"""
    assert _load_skill(_write_skill(tmp_path / "valid")).version == 1
    invalid = _write_skill(
        tmp_path / "invalid",
        metadata=_replace_metadata(DEFAULT_METADATA, "version", f"version: {value}"),
    )
    _assert_error(invalid, "SKILL_INVALID_VERSION")


@pytest.mark.parametrize("status", ["draft", "active", "deprecated"])
def test_status_enum(tmp_path: Path, status: str) -> None:
    """Spec: HERMES-0003 / AC-09"""
    metadata = _replace_metadata(DEFAULT_METADATA, "status", f"status: {status}")
    assert _enum_value(_load_skill(_write_skill(tmp_path / status, metadata=metadata)).status) == status

    for index, value in enumerate(('"active"', "paused")):
        invalid = _write_skill(
            tmp_path / f"invalid-{status}-{index}",
            metadata=_replace_metadata(DEFAULT_METADATA, "status", f"status: {value}"),
        )
        _assert_error(invalid, "SKILL_INVALID_STATUS")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Example skill", "Example skill"), ("123", "123"), ("true", "true")],
)
def test_description_is_non_empty_literal_text(
    tmp_path: Path, raw: str, expected: str
) -> None:
    """Spec: HERMES-0003 / AC-10"""
    metadata = _replace_metadata(DEFAULT_METADATA, "description", f"description: {raw}")
    assert _load_skill(_write_skill(tmp_path / "valid", metadata=metadata)).description == expected

    for index, line in enumerate(("description:", "description:    ")):
        invalid = _write_skill(
            tmp_path / f"invalid-{index}",
            metadata=_replace_metadata(DEFAULT_METADATA, "description", line),
        )
        _assert_error(invalid, "SKILL_INVALID_DESCRIPTION")


@pytest.mark.parametrize("risk", ["low", "medium", "high"])
def test_risk_enum(tmp_path: Path, risk: str) -> None:
    """Spec: HERMES-0003 / AC-11"""
    metadata = _replace_metadata(DEFAULT_METADATA, "risk", f"risk: {risk}")
    assert _enum_value(_load_skill(_write_skill(tmp_path / risk, metadata=metadata)).risk) == risk

    for index, value in enumerate(('"low"', "critical")):
        invalid = _write_skill(
            tmp_path / f"invalid-{risk}-{index}",
            metadata=_replace_metadata(DEFAULT_METADATA, "risk", f"risk: {value}"),
        )
        _assert_error(invalid, "SKILL_INVALID_RISK")


def test_requires_empty_list(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-12"""
    definition = _load_skill(_write_skill(tmp_path))
    assert definition.requires == ()
    assert isinstance(definition.requires, tuple)


def test_requires_preserves_order(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-13"""
    metadata = _replace_metadata(
        DEFAULT_METADATA,
        "requires",
        ("requires:", "  - git", "  - pytest", "  - importlib"),
    )
    definition = _load_skill(_write_skill(tmp_path, metadata=metadata))
    assert definition.requires == ("git", "pytest", "importlib")


@pytest.mark.parametrize(
    "replacement",
    [
        ("requires:", "  - git", "  - git"),
        ("requires:", "  - "),
        ("requires:", " - git"),
        ("requires:", "    - git"),
        ("requires: [git]",),
        ('requires: ["git"]',),
        ("requires:", "  - nested:", "    - value"),
    ],
)
def test_requires_rejects_invalid_grammar_and_items(
    tmp_path: Path, replacement: tuple[str, ...]
) -> None:
    """Spec: HERMES-0003 / AC-14"""
    invalid = _write_skill(
        tmp_path,
        metadata=_replace_metadata(DEFAULT_METADATA, "requires", replacement),
    )
    with pytest.raises(Exception) as caught:
        _load_skill(invalid)
    assert _error_code(caught.value) in {
        "SKILL_INVALID_REQUIRES",
        "SKILL_FRONT_MATTER_INVALID",
    }


@pytest.mark.parametrize(("raw", "expected"), [("true", True), ("false", False)])
def test_allows_write_literal_booleans(
    tmp_path: Path, raw: str, expected: bool
) -> None:
    """Spec: HERMES-0003 / AC-15"""
    metadata = _replace_metadata(DEFAULT_METADATA, "allows_write", f"allows_write: {raw}")
    assert _load_skill(_write_skill(tmp_path, metadata=metadata)).allows_write is expected


@pytest.mark.parametrize(
    "value",
    ["True", "False", "TRUE", "FALSE", "yes", "no", "1", "0", '"true"', "'false'"],
)
def test_allows_write_rejects_non_booleans(tmp_path: Path, value: str) -> None:
    """Spec: HERMES-0003 / AC-16"""
    invalid = _write_skill(
        tmp_path,
        metadata=_replace_metadata(DEFAULT_METADATA, "allows_write", f"allows_write: {value}"),
    )
    _assert_error(invalid, "SKILL_INVALID_ALLOWS_WRITE")


@pytest.mark.parametrize(
    "line",
    [
        "description: |",
        "description: >",
        "description: &anchor text",
        "description: *alias",
        "description: !!str text",
        "description: {key: value}",
        "description: [one, two]",
        "<<: *defaults",
    ],
)
def test_parser_uses_closed_textual_grammar(tmp_path: Path, line: str) -> None:
    """Spec: HERMES-0003 / AC-17"""
    for index, literal in enumerate(("value # literal", '"quoted"', "first: second")):
        metadata = _replace_metadata(
            DEFAULT_METADATA,
            "description",
            f"description: {literal}",
        )
        assert _load_skill(
            _write_skill(tmp_path / f"literal-{index}", metadata=metadata)
        ).description == literal

    key = "description" if line.startswith("description:") else "description"
    replacement = line if line.startswith("description:") else (
        "description: Example skill",
        line,
    )
    invalid = _write_skill(
        tmp_path,
        metadata=_replace_metadata(DEFAULT_METADATA, key, replacement),
    )
    _assert_error(invalid, "SKILL_FRONT_MATTER_INVALID")


@pytest.mark.parametrize("missing", REQUIRED_SECTIONS)
def test_each_required_section_missing(tmp_path: Path, missing: str) -> None:
    """Spec: HERMES-0003 / AC-18"""
    sections = tuple(section for section in REQUIRED_SECTIONS if section != missing)
    invalid = _write_skill(tmp_path, body=_body(sections=sections))
    _assert_error(invalid, "SKILL_REQUIRED_SECTION_MISSING")


@pytest.mark.parametrize("case", ["duplicate", "order"])
def test_required_sections_unique_and_ordered(tmp_path: Path, case: str) -> None:
    """Spec: HERMES-0003 / AC-19"""
    sections = list(REQUIRED_SECTIONS)
    if case == "duplicate":
        sections.insert(1, REQUIRED_SECTIONS[0])
        code = "SKILL_DUPLICATE_SECTION"
    else:
        sections[0], sections[1] = sections[1], sections[0]
        code = "SKILL_SECTION_ORDER_INVALID"
    invalid = _write_skill(tmp_path, body=_body(sections=tuple(sections)))
    _assert_error(invalid, code)


@pytest.mark.parametrize(
    "replacement",
    [
        "A menção Objetivo em texto comum não é heading.",
        "### Objetivo\n\nHeading de nível incorreto.",
        "```text\n## Objetivo\n```",
    ],
)
def test_section_names_must_be_real_h2(tmp_path: Path, replacement: str) -> None:
    """Spec: HERMES-0003 / AC-20"""
    body = _body().replace("## Objetivo\n\nConteúdo de Objetivo.", replacement, 1)
    invalid = _write_skill(tmp_path, body=body)
    _assert_error(invalid, "SKILL_REQUIRED_SECTION_MISSING")


@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_markdown_body_is_preserved_in_skill_definition(
    tmp_path: Path, newline: str
) -> None:
    """Spec: HERMES-0003 / AC-21"""
    body_lf = _body().replace("Conteúdo de Objetivo.", "Ação  \ncom espaços.\n")
    body = body_lf.replace("\n", newline)
    document = _document(body=body_lf).replace("\n", newline)
    path = _write_skill(tmp_path, raw_bytes=document.encode("utf-8"))

    definition = _load_skill(path)

    assert definition.body == body
    assert not hasattr(_skills_api(), "SkillDocument")


def test_skill_definition_is_immutable(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-22"""
    metadata = _replace_metadata(
        DEFAULT_METADATA,
        "requires",
        ("requires:", "  - git", "  - pytest"),
    )
    definition = _load_skill(_write_skill(tmp_path, metadata=metadata))
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        definition.id = "changed"
    with pytest.raises((AttributeError, TypeError)):
        definition.requires += ("changed",)


def test_validation_failure_has_no_partial_result(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-23"""
    invalid = _write_skill(
        tmp_path,
        metadata=_replace_metadata(DEFAULT_METADATA, "status", "status: invalid"),
    )
    result = object()
    with pytest.raises(Exception) as caught:
        result = _load_skill(invalid)
    assert _error_code(caught.value) == "SKILL_INVALID_STATUS"
    assert result.__class__ is object


def test_loader_does_not_modify_files(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-24"""
    path = _write_skill(tmp_path)
    other = tmp_path / "unrelated.txt"
    other.write_bytes(b"unchanged\x00bytes")
    before = _snapshot_files(tmp_path)
    _load_skill(path)
    assert _snapshot_files(tmp_path) == before


def test_loader_does_not_modify_git(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-25"""
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "-b", "main")
    git(repository, "config", "user.name", "Hermes Skills Test")
    git(repository, "config", "user.email", "skills@invalid.local")
    path = _write_skill(repository)
    git(repository, "add", "skills/example-skill/SKILL.md")
    git(repository, "commit", "-m", "fixture")
    head_before = git(repository, "rev-parse", "HEAD").stdout
    status_before = git(repository, "status", "--porcelain=v1", "-z").stdout
    config_before = (repository / ".git" / "config").read_bytes()

    _load_skill(path)

    assert git(repository, "rev-parse", "HEAD").stdout == head_before
    assert git(repository, "status", "--porcelain=v1", "-z").stdout == status_before
    assert (repository / ".git" / "config").read_bytes() == config_before


def test_loader_never_executes_content(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-26"""
    marker = tmp_path / "must-not-exist"
    payload = f'Path({str(marker)!r}).write_text("executed", encoding="utf-8")'
    body = _body().replace("Conteúdo de Procedimento.", payload)
    _load_skill(_write_skill(tmp_path, body=body))
    assert not marker.exists()


def test_declarations_do_not_grant_capabilities(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-27"""
    marker = tmp_path / "capability-marker"
    dependency = "hermes_dependency_that_must_not_be_imported"
    metadata = _replace_metadata(
        DEFAULT_METADATA,
        "requires",
        ("requires:", f"  - {dependency}"),
    )
    metadata = _replace_metadata(metadata, "allows_write", "allows_write: true")
    definition = _load_skill(_write_skill(tmp_path, metadata=metadata))
    assert definition.allows_write is True
    assert dependency not in sys.modules
    assert not marker.exists()


def test_no_external_yaml_dependency() -> None:
    """Spec: HERMES-0003 / AC-28"""
    api = _skills_api()
    project = Path(__file__).resolve().parents[1]
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8").lower()
    assert "pyyaml" not in pyproject
    package = Path(api.__file__).resolve().parent
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in package.rglob("*.py")
    ).lower()
    assert "import yaml" not in source
    assert "from yaml" not in source


def test_validation_is_deterministic(tmp_path: Path) -> None:
    """Spec: HERMES-0003 / AC-29"""
    valid = _write_skill(tmp_path / "valid")
    assert _load_skill(valid) == _load_skill(valid)

    invalid = _write_skill(
        tmp_path / "invalid",
        metadata=_replace_metadata(DEFAULT_METADATA, "version", "version: 0"),
    )
    errors = []
    for _ in range(2):
        with pytest.raises(Exception) as caught:
            _load_skill(invalid)
        errors.append((_error_code(caught.value), str(caught.value)))
    assert errors[0] == errors[1]


def test_skills_api_has_no_generic_runner_execute_skill_or_pipeline() -> None:
    """Spec: HERMES-0003 / AC-30"""
    api = _skills_api()
    forbidden = {"runner", "execute_skill", "pipeline"}
    assert forbidden.isdisjoint(set(dir(api)))

    from hermes_ops.cli import build_parser

    help_text = build_parser().format_help().lower()
    assert "skills" not in help_text
