# AGENTS.md

## Scope

This repository contains the generic, project-independent `hermes-ops` tool.
Do not add assumptions or integrations specific to consumer projects.

## Safety

- Never read environment files or include secrets in command output.
- Keep Git operations in `hermes_ops.git` read-only.
- Disable optional locks, inherited `GIT_*` redirections, and external
  fsmonitor for every runtime Git command.
- Block local Git configuration includes and filter sections before running
  any Git query; neutralize global and system Git configuration.
- Run subprocesses through `hermes_ops.core.processes`.
- Use `pathlib` for filesystem paths.
- Treat `--project` as the exact root; never discover parents or siblings.
- Public CLI output must pass through the centralized path sanitizer.
- Tests that need Git must create repositories in temporary directories.
- Do not commit, push, deploy, access remote APIs, or modify global Git settings.

## Development

- Runtime code must support Python 3.11 and use only the standard library.
- Invoke the local interpreter explicitly on Windows:
  `.venv\Scripts\python.exe`.
- Run the full suite with:
  `.venv\Scripts\python.exe -m pytest`.
- Build wheel and sdist with:
  `.venv\Scripts\python.exe -m build`.
- The canonical project template lives only in
  `src/hermes_ops/templates/project.toml`.
