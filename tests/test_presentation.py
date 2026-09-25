from hermes_ops.core.presentation import PublicSanitizer


def test_windows_paths_are_sanitized_without_prefix_collision() -> None:
    sanitizer = PublicSanitizer(
        project_root=r"C:\Users\Example User\Projeto ação",
        home=r"C:\Users\Example User",
        temp=r"C:\Users\Example User\AppData\Local\Temp",
    )
    assert sanitizer.sanitize_text(
        r"C:\Users\Example User\Projeto ação\.venv\Scripts\python.exe"
    ) == r"<PROJECT_ROOT>\.venv\Scripts\python.exe"
    assert sanitizer.sanitize_text(
        r"C:\Users\Example User\Documents\file.txt"
    ) == r"~\Documents\file.txt"
    assert sanitizer.sanitize_text(
        r"C:\Users\Example User\AppData\Local\Temp\internal"
    ) == r"<TEMP>\internal"
    sibling = r"C:\Users\Example User\Projeto ação-other\file.txt"
    assert sanitizer.sanitize_text(sibling) == r"~\Projeto ação-other\file.txt"
    assert "<PROJECT_ROOT>" not in sanitizer.sanitize_text(sibling)


def test_posix_paths_spaces_and_unicode_are_sanitized() -> None:
    sanitizer = PublicSanitizer(
        project_root="/home/example/Project ação",
        home="/home/example",
        temp="/tmp",
    )
    assert (
        sanitizer.sanitize_text("/home/example/Project ação/.venv/bin/python")
        == "<PROJECT_ROOT>/.venv/bin/python"
    )
    assert sanitizer.sanitize_text("/home/example/docs/a") == "~/docs/a"
    assert sanitizer.sanitize_text("/tmp/private/a") == "<TEMP>/private/a"
    sibling = "/home/example/Project ação-other/file"
    assert sanitizer.sanitize_text(sibling) == "~/Project ação-other/file"
    assert "<PROJECT_ROOT>" not in sanitizer.sanitize_text(sibling)


def test_nested_public_details_are_sanitized() -> None:
    sanitizer = PublicSanitizer(
        project_root="/work/project",
        home="/home/example",
        temp="/tmp",
    )
    assert sanitizer.sanitize(
        {"paths": ["/work/project/a", "/home/example/b", "/tmp/c"]}
    ) == {
        "paths": ["<PROJECT_ROOT>/a", "~/b", "<TEMP>/c"]
    }
