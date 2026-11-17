---
spec_id: HERMES-0029
title: Deterministic Memory Freshness and Store Lifecycle Hardening
version: 1
status: Implementado
date: 2026-08-23
depends_on: [HERMES-0028]
---

# HERMES-0029 - Deterministic Memory Freshness and Store Lifecycle Hardening

## 1. Context

HERMES-0028 introduced an optional, local historical-memory layer above the
frozen Hermes core. Operational dogfood demonstrated two bounded gaps: a query
cannot compare a historical observation with caller-supplied current
provenance, and a SQLite handle can survive a failed store initialization.

## 2. Confirmed problem

A revision-A/snapshot-A observation queried while revision-B/snapshot-B is
current is reported as `CURRENTLY_UNVERIFIED`, although explicit divergence is
available to the caller. Separately, exceptions after `sqlite3.connect` do not
close the owned connection before they are propagated or converted.

## 3. Plain-language explanation

The caller may describe the current repository state without asking Hermes to
run Git. Memory then labels historical context using explicit equality only.
The label remains context, never current evidence. A store owns its connection
from the instant SQLite returns it and releases it on every failed or successful
lifecycle path.

## 4. Current behavior

- Retrieval requests contain no current provenance.
- Freshness is derived only from the latest stored lineage event.
- Equal or different snapshots/revisions cannot affect freshness.
- Initialization catches errors without closing an already-open connection.
- `close()` is not explicitly idempotent and post-close operations expose raw
  SQLite lifecycle errors.

## 5. Desired behavior

- A frozen optional `MemoryCurrentContext` remains separate from observations.
- Existing requests without it preserve HERMES-0028 behavior.
- A pure decision function derives freshness from schema, explicit lineage
  projection, historical provenance, and current provenance.
- Retrieval score, filtering, ordering, disclosure payloads, historical finding
  semantics, and all frozen-core behavior remain unchanged.
- Initialization failure closes the connection without masking the original
  diagnostic; repeated close is safe; post-close operations fail coherently.

## 6. Out of scope

Git discovery, ancestry, changed-file inference, Audit Round integration,
ranking changes, embeddings, fuzzy/semantic retrieval, graph traversal,
cross-repository retrieval, pooling, consumer-specific behavior, and changes to
the frozen core are excluded.

## 7. Invariants and security rules

`MEMORY_IS_CONTEXT_NOT_EVIDENCE`. Revision is opaque. Snapshot digest is
stronger than revision metadata. Structural-scope difference alone does not
prove staleness. Current context contains no classification, finding, severity,
reachability, or auditor outcome. Repository mismatch fails closed. No target
is imported or executed. Runtime remains standard-library-only and Python 3.11.

Freshness precedence, strongest first, is:

1. `INCOMPATIBLE_SCHEMA`;
2. explicit `SUPERSEDED`;
3. explicit `NOT_REPRODUCED`;
4. explicit `REVALIDATED`;
5. `SAME_SNAPSHOT_CANDIDATE` or `STALE_CANDIDATE` from provenance;
6. `CURRENTLY_UNVERIFIED`.

## 8. Inputs and outputs

`MemoryCurrentContext` accepts repository ID, optional current revision,
optional current snapshot digest, and an optional bounded structural scope.
`MemoryRetrievalRequest.current_context` is optional. Output candidates retain
their existing shape and score; only `freshness_state` becomes more precise.
Store initialization either returns a ready store or raises/returns an existing
controlled diagnostic with no owned live connection.

## 9. Language-independent pseudocode

```text
VALIDATE CURRENT CONTEXT
  require its repository to equal the request repository
  validate optional text and relative structural scope with existing bounds

DERIVE FRESHNESS(observation, current context, lineage projection)
  if the observation schema is unsupported, return INCOMPATIBLE_SCHEMA
  if lineage explicitly says superseded, return SUPERSEDED
  if lineage explicitly says not reproduced, return NOT_REPRODUCED
  if lineage explicitly says revalidated, return REVALIDATED
  if current revision and snapshot are both absent, return CURRENTLY_UNVERIFIED
  if both historical and current snapshots are present:
    if equal, return SAME_SNAPSHOT_CANDIDATE
    otherwise return STALE_CANDIDATE
  if both revisions are present and different, return STALE_CANDIDATE
  return CURRENTLY_UNVERIFIED

OPEN STORE
  connection starts absent and store starts not ready
  try to connect, configure, migrate, check schema, and initialize FTS
  if any step fails:
    close the connection if it was acquired
    leave the store not ready
    propagate the original Memory error, or map the existing SQLite/OS error
  mark ready only after all required initialization finishes

CLOSE STORE
  if a connection is owned, close it once and release it
  mark the store closed
  repeated close does nothing
  later operations return the existing unavailable-store error
```

## 10. Main flow

The caller constructs a repository-matched current context and attaches it to a
retrieval request. Existing exact/lexical filters select observations and the
unchanged ranking computes scores. For each candidate, the store projects the
latest explicit lineage state and calls the pure freshness function. Opening a
store transfers connection ownership immediately; readiness is published only
after initialization completes.

## 11. Decision table

| Historical | Current | Explicit lineage | Result |
|---|---|---|---|
| snapshot A | snapshot A | none | `SAME_SNAPSHOT_CANDIDATE` |
| snapshot A | snapshot B | none | `STALE_CANDIDATE` |
| revision A, no snapshots | revision B, no snapshot | none | `STALE_CANDIDATE` |
| revision A, no snapshots | revision A, no snapshot | none | `CURRENTLY_UNVERIFIED` |
| revision A, digest A | revision A, digest B | none | `STALE_CANDIDATE` |
| any | no revision or snapshot | none | `CURRENTLY_UNVERIFIED` |
| any | any | revalidated | `REVALIDATED` |
| any | any | not reproduced | `NOT_REPRODUCED` |
| any | any | superseded | `SUPERSEDED` |

When only one side has a snapshot, revision inequality may prove stale;
revision equality does not prove an equal snapshot. Scope is diagnostic only.

## 12. Error cases and boundaries

- Context/request repository mismatch: `MEMORY_REPOSITORY_MISMATCH`.
- Unsafe/unbounded provenance or scope: `MEMORY_RECORD_UNSAFE`.
- Invalid SQLite: `MEMORY_STORE_CORRUPT`, followed by immediate path reuse.
- Future schema: `MEMORY_SCHEMA_UNSUPPORTED`, followed by cleanup.
- Simulated migration or unexpected FTS initialization failure: owned handle is
  closed and the original error is preserved.
- Operation after close: `MEMORY_STORE_UNAVAILABLE`; no reconnection.
- Optional service failures remain diagnostics and never break core execution.

## 13. Acceptance criteria

- **AC-01:** Current context is optional and backward-compatible.
- **AC-02:** Current-context repository mismatch fails closed.
- **AC-03:** Equal snapshots yield `SAME_SNAPSHOT_CANDIDATE`.
- **AC-04:** Different snapshots yield `STALE_CANDIDATE`.
- **AC-05:** Different revisions without snapshots yield `STALE_CANDIDATE`.
- **AC-06:** Missing current provenance yields `CURRENTLY_UNVERIFIED`.
- **AC-07:** Equal revisions without snapshots do not imply equal snapshots.
- **AC-08:** Different digests override equal revisions.
- **AC-09:** Freshness does not alter retrieval score or order.
- **AC-10:** Freshness does not alter finding semantics or identity.
- **AC-11:** Explicit lineage revalidation produces the specified stronger state.
- **AC-12:** Freshness derivation is deterministic and side-effect free.
- **AC-13:** Every initialization failure closes an acquired connection.
- **AC-14:** Corrupt DB initialization leaves no blocking handle.
- **AC-15:** Unsupported future schema leaves no blocking handle.
- **AC-16:** Simulated migration failure leaves no blocking handle.
- **AC-17:** `close()` is idempotent and post-close operations fail coherently.
- **AC-18:** Disabled, unavailable, corrupt, and retrieval-failing MemoryService
  modes do not affect core behavior.
- **AC-19:** Exact retrieval remains unchanged.
- **AC-20:** Lexical retrieval and FTS fallback remain unchanged.
- **AC-21:** Repository isolation remains fail-closed.
- **AC-22:** Progressive disclosure remains semantically unchanged.
- **AC-23:** Revalidation hints still require a fresh audit.
- **AC-24:** The original four dogfoods retain candidate, score, and order.
- **AC-25:** A hermetic 20-30 observation corpus does not affect core behavior.
- **AC-26:** Tests never import or execute a consumer target.
- **AC-27:** `audit_round.py` remains untouched.
- **AC-28:** Production code remains consumer-agnostic.
- **AC-29:** Full frozen-core regression remains green.
- **AC-30:** Wheel and sdist contain the Memory modules.

## 14. Test plan and criterion mapping

Dedicated HERMES-0029 tests cover AC-01 through AC-18 and AC-24 through AC-25,
including a RED characterization before implementation, pure decision-table
tests, score/order comparison, Windows-compatible rename/delete/reopen checks,
and injected migration/FTS failures. Existing foundation/integration tests cover
AC-19 through AC-23. Focused core suites and the full suite cover AC-10 and
AC-26 through AC-29. Archive inspection covers AC-30. Every criterion therefore
has automated evidence; static diffs and anti-hardcode scans supplement AC-26
through AC-28.

## 15. Likely affected files

- `src/hermes_ops/memory/models.py`
- `src/hermes_ops/memory/core.py`
- `src/hermes_ops/memory/store.py`
- `src/hermes_ops/memory/__init__.py`
- `tests/test_memory_freshness_lifecycle.py`
- this specification and the specification index

## 16. Known risks

An overly optimistic equality rule could present stale history as current;
therefore revision equality alone is deliberately insufficient. Lifecycle
cleanup must not replace the original diagnostic if `close()` itself fails.
The expanded corpus may expose ranking limitations, but HERMES-0029 records
them without changing ranking.

## 17. Validation evidence

Validated on 2026-08-23:

- RED: the HERMES-0029 test module initially failed collection because the
  current-context API did not exist.
- Memory/HERMES-0029: 46 passed in 3.25 s.
- Focused Memory, finding/ranking, Audit Round, execution-path, persistence,
  and state-effect: 210 passed in 3.83 s.
- Broad non-Memory regression: 778 passed, 11 skipped, 46 deselected in
  67.88 s.
- Full suite: 824 passed, 11 skipped, 0 failed in 70.50 s. The skip count is
  unchanged from the 805/11 baseline; 19 tests were added.
- The first full-suite attempt used a temp directory below the repository and
  contaminated three no-repository fixtures through their Git parent. It
  recorded 821 passed, 11 skipped, 3 failed; the unchanged suite passed when
  rerun with the hermetic temp root outside the repository.
- Original dogfood: 4/4 Top-1, score 160 each, zero misses and zero false
  candidates above; three revision-A records changed only from unverified to
  stale and the explicitly reconfirmed revision-B record became revalidated.
- Expanded corpus: 24 observations, 10 blind symbol queries, Top-1/Top-3/Top-5
  10/10, zero misses, zero false context above, four same-snapshot and six stale
  classifications correct, repository isolation and repeated ordering true.
- Expanded retrieval elapsed time: 0.006068 s for 10 local retrievals. This is
  a sanity measurement, not an SLA.
- Expanded context proxy: HEADER 7,976 bytes, STRUCTURED 5,480 bytes, CANONICAL
  11,758 bytes; reductions versus canonical were 32.1653% and 53.3934%.
- Corrupt, future-schema, injected-migration, and unexpected-FTS initialization
  paths released their Windows file handles; rename/delete/recreate succeeded.
- Wheel and sdist built successfully and contain `memory/__init__.py`,
  `memory/core.py`, `memory/models.py`, and `memory/store.py`.
- Anti-hardcode scan found no prohibited consumer names, historical SHA,
  benchmark/state literals, or absolute user paths in production Memory code.
- Frozen Audit Round, finding/ranking, execution, persistence, and state-model
  diffs are empty. Branch/HEAD/staging safety is recorded in the final report.
