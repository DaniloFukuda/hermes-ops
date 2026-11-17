# Hermes Ops

Hermes Ops is an execution and governance layer for AI agents.

It provides structured skill execution, mission auditing, controlled source reading, execution boundaries, evidence collection, and safety mechanisms for agentic workflows.

## Overview

Hermes Ops turns a requested operational task into a bounded skill flow. Its current implementation includes a controlled source reader, a mission-audit evidence pack, a closed skill dispatcher, policy-based skill planning, execution checkpoints, and read-only Git preflight checks.

## Core concepts

- **Skills:** catalogued operations selected through an explicit policy.
- **Mission audit:** local evidence collection for a bounded mission.
- **Controlled source reading:** deterministic, read-only source inventory with file and path safety checks.
- **Execution checkpoints:** immutable checkpoints and explicit handoff data for an execution context.
- **Execution boundaries:** closed dispatch and unitary approved skill plans.
- **Evidence:** structured results, regions, symbols, relationships, and related tests.

## Installation

Python 3.11+ is required. For development:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

On POSIX systems, use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

## Basic usage

```bash
python -m hermes_ops doctor --project PATH
python -m hermes_ops preflight --project PATH
python -m hermes_ops skill run mission-audit --project PATH --mission "inspect source evidence"
```

## Tests

```bash
.venv/Scripts/python.exe -m pytest
```

## Evidence Pack compatibility

Evidence Pack v1 remains readable for historical analysis and never infers
redundancy from cap signals. Evidence Pack v2 carries explicit
`omission_provenance`; only complete, deterministic proof for a selected
same-file comment or docstring can make a cap omission non-blocking. Unknown
versions, missing provenance, critical/necessary omissions, active-code
claims, and incomplete records fail closed.

## Memory-assisted audit

The `skill run` interface keeps historical Memory disabled by default. `--memory
read` opens a supplied SQLite store read-only; `--memory read-write` is an
explicit opt-in that requires `--memory-store` and `--repository-id` and only
writes post-audit observations to that store. The target project remains
outside the writeback boundary.

## Build and validation

```bash
.venv/Scripts/python.exe -m compileall -q src tests
.venv/Scripts/python.exe -m build
```

The runtime has no third-party dependencies. Development dependencies are
listed under `[project.optional-dependencies].dev` in `pyproject.toml`.

## Status

This repository contains the `0.2.0rc1` public release candidate. Publication
requires final human review of the integrated tree, license, documentation,
security scan, and validation artifacts.
