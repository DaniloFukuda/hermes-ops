# Changelog

## 0.2.0rc1 — Unreleased

Candidate release for public review.

### Added

- Critical evidence prioritization for mission-audit Evidence Packs (HERMES-0036).
- Evidence Pack v2 omission provenance and conservative redundant-evidence proof
  (HERMES-0037).
- Fail-closed validation for unknown, incomplete, inconsistent, or non-redundant
  omission provenance.
- Historical Evidence Pack v1 loading without redundancy inference.
- Additional execution, memory, orchestration, audit, and packaging coverage
  included in the integrated public candidate.

### Validation

- Focused mission-audit tests and the full Hermes Ops suite must be rerun in the
  integrated release worktree before publication approval.
- The release candidate does not access production or perform external sends.
