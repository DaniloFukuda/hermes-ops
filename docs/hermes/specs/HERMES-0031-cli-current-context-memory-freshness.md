---
id: HERMES-0031
title: CLI Current Context and Memory Freshness Provenance
status: Implementado
---

# HERMES-0031 — CLI Current Context and Memory Freshness Provenance

## 1. Context

HERMES-0029 defines deterministic Memory freshness and HERMES-0030 supplies a
Memory-assisted audit orchestration. The CLI currently sends no
`MemoryCurrentContext`, so ordinary CLI retrieval cannot distinguish a matching
snapshot from stale history.

## 2. Confirmed problem

`run_memory_assisted_skill_command` always sets `current_context=None`.
Retrieval therefore reports `CURRENTLY_UNVERIFIED` even when the single
controlled snapshot produced by the fresh Audit Round proves equal or different
content.

## 3. Plain-language explanation

Memory is historical context, not evidence. The CLI may safely attach the local
HEAD as opaque metadata. The audit then reads the target once and produces the
authoritative content digest. After that audit finishes, orchestration may
relabel presentation copies of the already-retrieved candidates. It must not
change what was retrieved, its ranking, or the fresh audit.

## 4. Current behavior

CLI requests contain no current revision or snapshot. Retrieval runs before the
fresh audit and candidates normally remain `CURRENTLY_UNVERIFIED`. Fresh
snapshot provenance is already used for write-back but not for final historical
presentation.

## 5. Desired behavior

- CLI automatically obtains local HEAD through the existing hardened, read-only
  Git inspection boundary when the declared target is the repository root.
- Git absence, an uncommitted repository, unsafe configuration, or inspection
  failure produces `current_revision=None` and never blocks the audit.
- Pre-audit retrieval uses only genuinely available provenance.
- Post-audit orchestration combines the request context with
  `AuditRoundResult.snapshot_provenance` and creates refined candidate copies.
- The final text and JSON expose refined freshness.
- Fresh snapshot provenance, never guessed pre-audit data, is authoritative for
  write-back.

## 6. Out of scope

No new auditor, retrieval ranking, embeddings, reason-code UX, disclosure
selector, cross-repository retrieval, fetch, remote ancestry, old-record
migration, Audit Round change, finding-ID change, or broader help redesign.

## 7. Invariants and security rules

- `MEMORY_IS_CONTEXT_NOT_EVIDENCE`.
- `CURRENT_CONTEXT_IS_PROVENANCE_NOT_SEMANTIC_INPUT`.
- `MEMORY_MUST_NOT_CHANGE_FRESH_AUDIT`.
- `target != repository_id`; absolute paths never become repository identity.
- Git commands are local/read-only, run through `hermes_ops.core.processes` via
  the existing hardened Git inspector, with locks, inherited `GIT_*`, config
  includes/filters, global/system config, prompts, and fsmonitor neutralized.
- No network operation is permitted.
- Snapshot digest comes only from the controlled snapshot used by Audit Round;
  path, timestamp, or a second semantic read must never synthesize it.
- Repository mismatch fails closed.
- Privacy rules from HERMES-0030 remain mandatory.

## 8. Inputs and outputs

Inputs are the existing CLI target, logical repository ID, structural scope,
Memory mode/store, mission, and audit requests. Internal provenance uses the
existing `MemoryCurrentContext`. Output namespaces remain `memory_context`,
`audit_plan`, `fresh_audit`, and `memory_writeback`; refined candidate freshness
is an additive change inside the existing historical candidate representation.

## 9. Language-independent pseudocode

```text
BUILD CLI CURRENT CONTEXT
  create context with logical repository ID and requested structural scope
  ask the hardened local Git inspector about the exact declared target root
  if a safe local committed HEAD is available, attach it as revision metadata
  otherwise leave revision absent
  never calculate a content digest here

RUN MEMORY-ASSISTED AUDIT
  retrieve historical candidates using pre-audit context
  preserve returned IDs, scores, ordering, and match reasons
  run the fresh audit exactly once with the original target, scope, and requests
  if the audit produced snapshot provenance:
    create a post-audit context using its digest and structural scope
    for each retrieved candidate:
      derive freshness with the unchanged HERMES-0029 decision table
      create a presentation copy differing only in freshness
  rebuild historical summary/comparison from those presentation copies
  write new observations using fresh digest and local revision metadata
  return the unchanged fresh audit plus refined historical presentation
```

## 10. Main flow

CLI provenance is pre-audit and optional. Retrieval occurs with that context.
Audit Round performs its existing single controlled read. Orchestration then
constructs post-audit context and immutable candidate projections. Selection is
mapped by observation ID so the selected subset retains retrieval order. Hints
and canonical observations are unchanged.

## 11. Error cases and boundaries

- Target outside Git: revision absent; snapshot still refines freshness.
- Git inspection failure: revision absent; audit proceeds.
- No snapshot provenance: revision-only HERMES-0029 rules apply.
- Same revision with different digest: stale.
- Different revision with equal digest: same snapshot.
- Different scope alone: not stale.
- Memory/store failure: optional diagnostics; fresh audit proceeds.
- Repository mismatch: validation error before retrieval.
- Disabled Memory: no Memory service/retrieval; fresh audit unchanged.

## 12. Acceptance criteria

- **AC-01:** Equal historical/current digests yield `SAME_SNAPSHOT_CANDIDATE`.
- **AC-02:** Different digests yield `STALE_CANDIDATE`.
- **AC-03:** Equal revision without comparable digests remains unverified.
- **AC-04:** Different revision without comparable digests is stale.
- **AC-05:** Digest precedence handles same-revision/different-snapshot and
  different-revision/same-snapshot correctly.
- **AC-06:** No-Git targets refine freshness using the audit snapshot.
- **AC-07:** No usable provenance remains unverified; scope alone is diagnostic.
- **AC-08:** Repository mismatch fails closed.
- **AC-09:** Refinement preserves candidate IDs, scores, ordering, reasons,
  hints, and canonical observations.
- **AC-10:** OFF, READ_ONLY, and READ_WRITE fresh results are byte-identical.
- **AC-11:** Write-back uses the fresh audit digest and local revision metadata.
- **AC-12:** READ_ONLY writes nothing; existing READ_WRITE/idempotence remains.
- **AC-13:** Aligned history never suppresses a regression and path-only remains
  non-actionable.
- **AC-14:** Text and deterministic JSON display final freshness without
  breaking top-level namespaces.
- **AC-15:** Git inspection is local, read-only, hardened, and optional.
- **AC-16:** Dirty worktree content is governed by snapshot digest, not HEAD.
- **AC-17:** Memory/store failures remain optional.
- **AC-18:** HERMES-0030 native-payload privacy and lineage stability remain.
- **AC-19:** The six-round operational dogfood proves equal, changed, fixed,
  revalidated, and regression behavior with repository isolation.
- **AC-20:** Frozen-core files receive no semantic change.

## 13. Test plan

Add a dedicated HERMES-0031 test module covering every decision-table row,
pre/post contexts, immutable refinement, ranking invariants, fresh-result
identity, write modes, CLI text/JSON, hardened Git success/failure, no-Git,
dirty worktree, privacy, store failure, aligned regression, and path-only.
Retain HERMES-0029, HERMES-0030, Audit Round, ranking, CLI, and privacy suites.
Run hermetic dogfood, focused tests, broad regression, full suite, and build.

## 14. Likely affected files

- `src/hermes_ops/commands/skill.py`
- `src/hermes_ops/orchestration/memory_assisted_audit.py`
- possibly orchestration models/exports if an explicit projection is required
- `tests/test_cli_current_context_memory_freshness.py`
- this specification and the specification index

## 15. Known risks

Post-audit projection could accidentally reorder candidates, leak into Audit
Round inputs, or make plan/context inconsistent. Git inspection could broaden
the declared root or inherit unsafe configuration. Tests therefore compare all
ranking fields, spy on the audit boundary, exercise Git optionality and dirty
content, and require frozen-core and anti-hardcode checks.

## 16. Implementation evidence

- The first valid contract RED reproduced the CLI defect exactly:
  `CURRENTLY_UNVERIFIED` instead of `STALE_CANDIDATE`, with `1 failed` in
  `0.38s`.
- CLI/orchestration GREEN plus HERMES-0030 compatibility passed `24` tests in
  `1.65s`. The dedicated HERMES-0031 module passes `12` tests, including six
  parameterized decision-table cases and a real dirty Git worktree.
- Focused HERMES-0031, orchestration, Memory, HERMES-0029, privacy, Audit Round,
  ranking, and relevant CLI coverage passed `149` tests in `7.05s`.
- Broad analysis/auditor/controlled-reader regression passed `216` tests with
  `2` expected Windows symlink skips in `13.44s`.
- Full suite collected `880` tests and completed with `869 passed`, `11`
  expected skips, and zero failures in `84.31s`; no new skip was introduced.
- Wheel and sdist build succeeded. Both artifacts contain the Memory and
  orchestration modules; nothing was published.

## 17. Operational dogfood evidence

Six real CLI rounds used one local temporary Git repository, one logical
repository ID, one SQLite store, and a dirty worktree whose HEAD remained
constant:

- Round A, buggy READ_WRITE: one fresh finding and one observation written.
- Round B, same buggy READ: `SAME_SNAPSHOT_CANDIDATE`; fresh digest equals A.
- Round C, fixed READ: `STALE_CANDIDATE`; zero fresh findings and a new digest.
- Round D, fixed READ_WRITE: stale historical finding, one aligned observation
  written, and `NOT_REPRODUCED` lineage event.
- Round E, same fixed READ: confirmed history remains stale and aligned history
  is `NOT_REPRODUCED`; fixed digest equals C/D.
- Round F, buggy regression READ: original history is
  `SAME_SNAPSHOT_CANDIDATE`, aligned history remains `NOT_REPRODUCED`, and the
  fresh finding reappears.

The store contains two observations, one lineage, and events `OBSERVED`,
`OBSERVED`, `NOT_REPRODUCED`. Repository-isolation violations are zero.
Canonical inspection found neither `return eval(payload)` nor the host path.
Candidate identity, ranking fields, ordering, hints, and canonical observations
remain unchanged by freshness projection.

## 18. Acceptance evidence map

| Criteria | Evidence |
|---|---|
| AC-01–AC-07 | HERMES-0031 decision-table, same/changed CLI, no-Git, and dirty-worktree tests |
| AC-08 | repository mismatch fail-closed test plus existing Memory isolation suite |
| AC-09 | immutable projection equality assertion and existing deterministic retrieval suite |
| AC-10 | existing OFF/READ_ONLY/READ_WRITE byte-identity test, full suite, and dogfood digests |
| AC-11–AC-13 | HERMES-0030 write-back, mode, aligned-regression, and path-only tests plus dogfood |
| AC-14 | CLI text/JSON freshness tests and deterministic serializer regression |
| AC-15–AC-16 | Git spy, no-Git test, hardened Git suites, and real dirty-worktree test |
| AC-17 | existing optional Memory read/write failure matrix |
| AC-18 | `test_memory_privacy_remediation.py` and dogfood canonical inspection |
| AC-19 | six-round operational dogfood recorded above |
| AC-20 | final frozen-surface diff attribution and full frozen-core regression |
