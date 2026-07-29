# hermes-ops

`hermes-ops` is a portable, project-independent operational preflight tool.
It inspects configuration, paths, Python, and Git state without changing the
project being inspected.

Runtime requirements:

- Python 3.11 or newer
- Git, when required by the inspected project's configuration
- no third-party runtime dependencies

The runtime supports Windows and Linux. CI is prepared for Python 3.11 and
3.13 on both systems, but it will run only after a remote repository is
created and a push is explicitly authorized.

## Install for development

Windows:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Commands

```text
python -m hermes_ops doctor --project PATH [--format text|json]
python -m hermes_ops worktree --project PATH [--format text|json]
python -m hermes_ops preflight --project PATH [--format text|json]
```

The commands are read-only. Configuration is loaded only from
`.hermes/project.toml`; environment files are never loaded.

`--project` always names the exact project root. The tool never searches
parent or sibling directories. The root is valid when its configuration is
valid and at least one configured `project.root_markers` path exists inside
that same root.

## Configuration

The complete minimum configuration is:

```toml
[project]
name = "example-project"
```

Omitted fields receive these safe defaults:

- root markers: `.git` and `pyproject.toml` (at least one must exist);
- minimum Python: `3.11`;
- Python candidates: `.venv/Scripts/python.exe` and `.venv/bin/python`;
- Git is required and the working tree must be clean;
- protected branches: `main`, `master`, and `production`;
- targeted, regression, and full test command lists are empty;
- protected patterns cover environment, database, SQLite, PEM, and key files.

Unknown sections and fields are rejected. Configured project paths must be
relative and cannot escape the declared root. The canonical template is
packaged at `src/hermes_ops/templates/project.toml`.

## Read-only policy and public output

Runtime Git commands are queries only. They run without optional locks,
without inherited `GIT_*` redirections, and with external fsmonitor disabled.
The Git root must equal the declared project root before status is inspected.
Indirect `.git` files, including linked Git worktrees, are blocked by this
first safety contract.

Public text and JSON replace the declared root with `<PROJECT_ROOT>`,
temporary directories with `<TEMP>`, and the home directory with `~`.
Relative file names inside the project remain unchanged.

## Test and build

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m build
```

Linux:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m build
```

The packaged template is available read-only through
`hermes_ops.core.configuration.read_packaged_project_template`. No command
creates configuration in consumer projects.

## Exit codes

Precedence from highest to lowest:

1. `4`: unexpected external failure
2. `2`: invalid configuration
3. `3`: blocked operation
4. `1`: check error
5. `0`: completed without errors or blocks

## Limitations

- configured consumer-project test commands are not executed;
- no deploy, database, backup, SSH, systemd, or Docker support exists;
- full secret and token sanitization is intentionally deferred;
- a Git root different from the declared project root is blocked.
- linked Git worktrees are not yet supported.
