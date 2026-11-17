---
id: HERMES-0033
title: Legacy Memory Privacy and Compatibility
status: Implementado
---

# HERMES-0033 — Legacy Memory Privacy and Compatibility

## 1. Context and confirmed problem

Pre-HERMES-0030 observations may contain source or secrets in `native_payload`.
Normal store opening is compatible, but CANONICAL expansion currently returns
such records without a privacy gate.

## 2. Plain-language explanation

Old history remains append-only, but unsafe or uncertain detail is never shown.
Safe metadata can still identify a candidate and guide a mandatory fresh audit.
An explicit local API may create a new safe observation without rewriting the
old one.

## 3. Desired behavior

Classify records structurally, allow safe HEADER/STRUCTURED, block unsafe or
unknown CANONICAL, produce safe hints only, quarantine without deletion, and
offer deterministic append-only migration preserving compatible lineage.

## 4. Out of scope

No auditor/lens/ranking/telemetry/cloud/cross-repository feature, automatic
scan, deletion, background migration, finding reinterpretation, or CLI admin
command.

## 5. Legacy definition and states

Classification never uses time or mtime. `CURRENT_SAFE` exactly matches a
complete modern HERMES-0030 structural payload for its Memory kind.
`LEGACY_SAFE_VERIFIED` passes the current closed sanitizer but lacks that exact
modern shape. Unknown fields yield `LEGACY_UNVERIFIED`. Proven source/code,
secret-like keys/values, absolute paths, or integrity failure yield
`LEGACY_UNSAFE`. Explicitly blocked originals project as `QUARANTINED`; safe
migration outputs project as `MIGRATED_SAFE` when linked by migration event.

## 6. Safe-read and quarantine policy

HEADER and STRUCTURED are derived only from validated top-level metadata.
CANONICAL is allowed for current, verified-safe, and migrated-safe records.
It fails closed for unverified, unsafe, or quarantined records with an explicit
Memory diagnostic and never returns raw payload. HINT is returned only when its
request and structural metadata pass the privacy gate. Quarantine never deletes
or overwrites the stored canonical row.

## 7. Migration semantics

Migration is an explicit API call for one repository/observation. It drops all
unsafe payload material, reconstructs only the closed structural subset from
validated top-level metadata, creates a deterministic new observation, requires
the same derived lineage, writes append-only, records a dedicated privacy
migration event, and leaves the source untouched. Repetition returns the same
result without duplicate semantic writes/events. If request or structural
identity is unsafe or insufficient, migration fails with
`MEMORY_LEGACY_MIGRATION_UNSAFE`.

## 8. Invariants and security

Memory is context, fresh audit remains authoritative, unknown is not safe, no
silent rewrite occurs, privacy failure is optional to core audit, ranking is
unchanged, privacy and freshness are independent, no target is executed, and
no raw payload appears in diagnostics/events.

## 9. Inputs and outputs

Public local APIs inspect or migrate one observation using explicit store,
repository ID, and observation ID. Candidate presentation adds privacy state
and effective canonical availability. No SQLite schema migration is required.

## 10. Pseudocode

```text
inspect one canonical row without exposing it
verify identity and known schema
scan recursively for secret keys, absolute paths, and source-like text
try the closed current payload sanitizer
classify exact modern shape as current; safe non-modern shape as legacy verified
classify unknown shape as unverified; proven prohibited content as unsafe

for safe disclosure, derive only allowed projection
for blocked canonical, emit diagnostic and return no raw payload

on explicit migration, validate request and structural identity
build safe payload only from top-level structural metadata
create deterministic observation; require compatible lineage
append new row and privacy migration event; preserve old row
```

## 11. Error cases

Unknown schema, corrupt identity, unsafe request, missing structural identity,
repository mismatch, and unsafe canonical all fail closed per record. Store
opening and fresh audit continue. No implicit migration occurs.

## 12. Acceptance criteria

- **AC-01:** Six closed privacy states classify deterministically.
- **AC-02:** Current-safe IDs/digests/disclosure remain unchanged.
- **AC-03:** Unsafe source, secret, and absolute path are blocked; unknown is
  unverified and blocked; verified-safe legacy remains readable.
- **AC-04:** HEADER/STRUCTURED and eligible HINT never echo prohibited data.
- **AC-05:** Retrieval IDs/scores/order and freshness remain unchanged while UX
  adds privacy state and canonical availability.
- **AC-06:** Explicit migration creates one new safe ID with same lineage,
  preserves original, records traceable event, and is idempotent.
- **AC-07:** Impossible migration fails closed and quarantines without deletion.
- **AC-08:** Store open never scans/migrates; one bad record does not break audit.
- **AC-09:** Fresh audit is byte-identical with or without legacy history.
- **AC-10:** No frozen core, retrieval ranking, or SQLite schema change.

## 13. Test plan

Use hermetic current/legacy safe/source/secret/path/unknown fixtures. First RED
proves raw CANONICAL exposure; second proves migration API absence. Cover the 35
required cases through dedicated and existing Memory/orchestration/privacy
tests, dogfood inspection/migration/reopen, full regression, build, and scans.

## 14. Likely affected files

Memory models/core/store public API, orchestration presentation, dedicated
tests, exports, and this specification.

## 15. Known risks

Over-broad source detection may block a safe legacy record; fail-closed is the
chosen privacy tradeoff. Migration must never derive semantics from unsafe text.

## 16. Validation evidence

- RED: unsafe legacy CANONICAL remained readable and the explicit migration API
  was absent: `2 failed` in `0.30s`.
- GREEN privacy/UX set: `21 passed` in `2.08s`.
- Focused HERMES-0033 plus HERMES-0028–0032 Memory, lifecycle, retrieval,
  orchestration, and privacy: `110 passed` in `8.20s`.
- Final focused presentation/privacy regression after UX completion: `52
  passed` in `3.98s`.
- Full suite collected `899` tests: `888 passed`, `11` expected skips, zero
  failed in `80.50s`.
- Wheel and sdist build succeeded with Memory/orchestration included.

## 17. Migration and compatibility evidence

Hermetic fixtures prove CURRENT_SAFE, LEGACY_SAFE_VERIFIED,
LEGACY_UNVERIFIED, and LEGACY_UNSAFE for source, secret, and host path.
HEADER/STRUCTURED remain safe; unsafe/unknown CANONICAL is blocked; safe HINT
requires a fresh audit. Explicit migration preserves the source row, creates a
different deterministic safe observation with the same lineage, records
`PRIVACY_MIGRATED:HERMES-0033-v1` and `QUARANTINED`, blocks the old canonical,
allows the new canonical, and is idempotent. Unsafe canonical requests refuse
migration with `MEMORY_LEGACY_MIGRATION_UNSAFE`.

No automatic store scan, overwrite, deletion, ranking adjustment, or SQLite
schema migration was added. Privacy state and freshness remain independent
candidate metadata. Existing HERMES-0028 test data that represented a current
record was aligned from arbitrary `summary` payload to the modern structural
contract; unknown-field blocking remains independently tested.

## 18. Freeze readiness

`MEMORY_V1_READY_FOR_FREEZE`. Legacy privacy classification, disclosure block,
quarantine, explicit append-only migration, event policy version, idempotency,
and failure optionality are now closed. The remaining pre-limit
`candidates_considered` metric is LOW observability debt and does not justify
holding the semantic/privacy freeze.
