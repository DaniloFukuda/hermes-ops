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

## Specifications, Pseudocode, and Tests

Every non-trivial functional change must have a versioned specification in:

```
docs/hermes/specs/
```

Before implementation, the specification must document:

1. Context
2. Confirmed problem
3. Plain-language explanation
4. Current behavior
5. Desired behavior
6. Out of scope items
7. Invariants and security rules
8. Inputs and outputs
9. Language-independent pseudocode
10. Main flow
11. Error cases and boundaries
12. Acceptance criteria identified as AC-01, AC-02, etc.
13. Test plan
14. Likely affected files
15. Known risks

Mandatory rules:

- Pseudocode must be understandable by the project owner, even if they don't
  know the source code.
- Pseudocode must explain decisions and flows, not translate Python line by
  line.
- The specification must separate expected behavior from implementation
  details.
- Each acceptance criterion must have an automated test or an explicit
  justification for not having one.
- When possible, new tests must reference the specification and criterion
  identifier in a docstring or comment, e.g.:

  ```
  Spec: HERMES-0002 / AC-03
  ```

- Tests must validate the specification contract, not merely mirror internal
  implementation structure.
- Code, tests, and specification must be updated together when a change
  alters public behavior.
- If code, tests, and specification diverge, the agent must stop and report
  the divergence before deciding what to change.
- Security fixes must include:
  - allowed behavior test;
  - blocked behavior test;
  - regression test.
- A specification cannot receive "Implemented" status without concrete
  validation evidence.
- Simple typographical or documentary changes may be exempt from a dedicated
  specification.
- The agent must not create a retroactive specification inventing decisions
  not supported by code, tests, or history.