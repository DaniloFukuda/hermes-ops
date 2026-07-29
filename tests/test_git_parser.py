import pytest

from hermes_ops.git.parser import parse_porcelain_v1_z


def test_parse_all_change_categories_with_unicode_and_spaces() -> None:
    output = (
        " M modified file.txt\0"
        "A  adicionado-ação.txt\0"
        " D removed.txt\0"
        "?? untracked file.txt\0"
        "UU conflict.txt\0"
    )
    changes = parse_porcelain_v1_z(output)
    assert changes.modified == ("modified file.txt",)
    assert changes.added == ("adicionado-ação.txt",)
    assert changes.removed == ("removed.txt",)
    assert changes.untracked == ("untracked file.txt",)
    assert changes.conflicts == ("conflict.txt",)


def test_empty_output_is_clean() -> None:
    assert parse_porcelain_v1_z("").clean


def test_rename_consumes_source_record() -> None:
    changes = parse_porcelain_v1_z("R  new name.txt\0old name.txt\0")
    assert changes.modified == ("new name.txt",)


def test_malformed_record_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_porcelain_v1_z("bad\0")

