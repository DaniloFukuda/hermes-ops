from __future__ import annotations

import os
from typing import Mapping


def safe_git_environment(
    source: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a Git environment without inherited Git redirections.

    The caller's mapping and ``os.environ`` are never modified. Locale is
    controlled so expected Git diagnostics can be classified consistently;
    Git still emits NUL-delimited path bytes independently of message locale.
    """

    inherited = os.environ if source is None else source
    environment = {
        key: value
        for key, value in inherited.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
            "LANG": "C",
        }
    )
    return environment

