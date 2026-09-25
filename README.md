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

## Status

This repository contains the current 0.1.0 implementation. It is prepared as a public source copy; publication and license selection require human review.
