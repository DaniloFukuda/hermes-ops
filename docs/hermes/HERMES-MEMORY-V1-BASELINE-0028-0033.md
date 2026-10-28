# Hermes Memory V1 — Frozen Baseline HERMES-0028–0033

Status: `FROZEN_BASELINE_WITH_NON_BLOCKING_DEBT`

Provenance:

- branch: `feature/execution-path-review-20260820`
- historical working-tree origin: `08ad7bf919bdfc889d3be81c6ce3095029f33ee8` (`feat(mission-audit): adiciona structural scope`), an ancestor of the current baseline;
- current reproducible parent/core baseline: `16738eb310cd8f21393a969f5715c4ee730ace19` (`feat(audit): consolidate Hermes structural audit core`);
- inputs: HERMES-0028 through HERMES-0033, all `Implementado`
- latest checkpoint: `888 passed, 11 skipped, 0 failed`
- this freeze changes documentation only

## 1. Responsibility

Memory V1 is an optional, local, repository-isolated historical context layer
above the frozen Hermes audit core. It persists structural observations,
retrieves deterministic candidates, offers progressive disclosure, classifies
freshness and privacy, produces revalidation hints, assists planning, writes
only after fresh audit, maintains append-only lineage, and treats legacy privacy
fail-closed.

It does not confirm a current finding, replace Audit Round, inject facts into
auditors, alter current finding ranking, narrow authoritative scope, execute a
target, fix code, or share auditor semantics. Historical relevance is not
current finding priority. Fresh audit remains the current authority.

## 2. Freeze input inventory

| Spec | Responsibility | Main surface | Principal invariant | Evidence/dependencies |
|---|---|---|---|---|
| HERMES-0028 | Persistent observation identity, repository-isolated retrieval and disclosure | `memory/models.py`, `core.py`, `store.py` | Memory is context, not evidence | 805 passed/11 skipped; foundation for later specs |
| HERMES-0029 | Freshness decision and lifecycle | Memory models/core/store | lineage → snapshot → revision precedence | 824/11; depends on 0028 |
| HERMES-0030 | Memory-assisted orchestration, post-audit writes, native-payload privacy | `orchestration/*`, adapters, CLI | Memory never changes fresh Audit Round | closure 846/11; privacy 857/11; depends on 0028–0029 and Audit Round |
| HERMES-0031 | Automatic current provenance and post-audit freshness refinement | CLI/orchestration | current provenance is metadata; snapshot is authoritative | 869/11; Git/no-Git/dirty-worktree dogfood |
| HERMES-0032 | Reasons, disclosure UX and local observability | CLI/orchestration presentation | observability does not change semantics | 878/11; four-disclosure dogfood |
| HERMES-0033 | Legacy classification, blocked disclosure, quarantine and migration | Memory models/core/store | unknown is not safe; no silent rewrite | 888/11; legacy migration/idempotency dogfood |

Counts are evolving-suite checkpoints, not a claim of perfectly linear test
growth.

## 3. Frozen invariants

1. `MEMORY_IS_CONTEXT_NOT_EVIDENCE`.
2. Repository isolation is mandatory and fails closed.
3. Observation IDs are deterministic.
4. Lineage identity is separate from observation identity.
5. Canonical observations and lineage are append-only.
6. Memory retrieval never changes current finding ranking.
7. Memory failure never breaks fresh audit.
8. Fresh `AuditRoundResult` is invariant across OFF, READ and READ_WRITE.
9. Memory objects never enter auditor inputs.
10. Memory never reduces authoritative structural scope.
11. Memory never substitutes auditor requests.
12. Write-back occurs only after fresh audit.
13. Revalidation always requires fresh audit.
14. Historical severity/reachability never become current facts.
15. Snapshot digest precedes revision for freshness.
16. Same snapshot is not current truth.
17. Stale candidate does not mean fixed bug.
18. Progressive disclosure points to a repository-isolated canonical record.
19. New canonical records never store raw source, snippets, secrets, host paths,
    runtime objects, or unrestricted native payloads.
20. Legacy unsafe/unverified CANONICAL is blocked.
21. Legacy migration is explicit, deterministic and append-only.
22. Canonical history is never silently rewritten.
23. Privacy and freshness are independent dimensions.
24. Retrieval ordering and observation-ID tie-break are deterministic.
25. Unknown Memory schema/version fails closed.
26. FTS is optional; exact structured retrieval remains available.
27. Disabled Memory preserves core behavior.
28. Metrics remain local and are never external telemetry.
29. Filesystem target and logical repository identity are distinct.
30. Current provenance is metadata, not semantic auditor input.

## 4. Frozen semantic surfaces

The following are frozen:

- `MemorySchemaVersion.V1` and unknown-schema failure;
- `RepositoryIdentity` semantics and repository-first isolation;
- `AuditMemoryObservation` canonical identity;
- observation-ID and lineage-ID contracts;
- `MemoryKind`, freshness states, privacy states and disclosure levels;
- lineage event meanings and append-only behavior;
- revalidation hints with `requires_fresh_audit=True`;
- retrieval weights, ordering, limit and tie-break;
- canonical write eligibility and privacy-safe payload contract;
- migration/quarantine and no-silent-rewrite semantics;
- failure optionality and diagnostic categories;
- OFF/READ/READ_WRITE semantics;
- historical/fresh namespace separation;
- `MemoryCurrentContext` and freshness precedence.

A delta requires a new spec, characterization, compatibility analysis and
regression evidence.

## 5. Flexible internals

Helpers, code layout, private serializers, internal SQL indexes, caching/query
performance, private projections, local metrics implementation, CLI formatting,
additive diagnostics, admin UX, compaction implementation and richer indexes
remain flexible when frozen behavior is preserved. Optional non-authoritative
accelerators may be added only behind the same invariants. Additional auditors
consume Memory through orchestration and require their own approved work.

## 6. Core/Memory boundary

```text
Frozen Core HERMES-0015–0027
    controlled snapshot + normalized findings + AuditRoundResult
                         ↓
Memory V1 HERMES-0028–0033
    optional historical context + append-only observations
                         ↓
Operational orchestration / CLI
    separate history presentation + mandatory fresh audit
```

Core has no semantic dependency on Memory. Audit Round is Memory-agnostic.

## 7. Frozen read path

```text
mission + current provenance + logical repository identity
 → repository-isolated deterministic retrieval
 → historical candidates with privacy/freshness metadata
 → progressive disclosure and revalidation hints
 → non-authoritative planning metadata
 → independent fresh Audit Round
```

A historical candidate is never a current result.

## 8. Frozen write path

```text
completed fresh audit
 → semantic eligibility
 → privacy-safe structural adapter/gate
 → deterministic canonical observation
 → append-only observation/lineage/index transaction
 → optional local presentation metadata
```

No Memory write occurs during auditor execution. Failed auditors do not become
semantic observations. Disclosure never governs persistence.

## 9. Freshness contract

Decision precedence is: incompatible schema; explicit superseded; explicit not
reproduced; explicit revalidated; comparable snapshot; comparable revision
difference; `CURRENTLY_UNVERIFIED`. Snapshot overrides revision. Equal revision
without comparable digest does not prove equal source. Scope difference alone
does not prove stale.

## 10. Privacy and legacy compatibility

New writes store structural references over raw content and pass the closed
payload sanitizer before digest and identity. All disclosures preserve privacy.

Legacy states are `CURRENT_SAFE`, `LEGACY_SAFE_VERIFIED`,
`LEGACY_UNVERIFIED`, `LEGACY_UNSAFE`, `MIGRATED_SAFE`, and `QUARANTINED`.
Opening a store never scans or migrates. HEADER/STRUCTURED derive safe metadata.
Unsafe, unverified or quarantined CANONICAL is blocked. A safe hint may still
guide a mandatory fresh audit.

Migration explicitly names one record, retains the old row, creates a new safe
observation, preserves compatible lineage, and appends quarantine plus a
versioned privacy-migration event. Unsafe input fails closed. Repetition is
idempotent.

## 11. Retrieval and disclosure

Retrieval is repository-first, uses exact metadata and structured indexes, may
use optional FTS, and orders by score then observation ID. Historical relevance
is separate from current ranking. Pre-limit `candidates_considered` is not a V1
semantic surface.

Frozen levels:

- `HEADER`: compact candidate;
- `STRUCTURED`: validated metadata and evidence references;
- `CANONICAL`: privacy-authorized canonical observation;
- `REVALIDATION_HINT`: safe fresh-audit inputs, always requiring fresh audit.

## 12. Orchestration, CLI, failures and observability

Modes are OFF, READ and READ_WRITE. Differences remain in `memory_context`,
`audit_plan`, `memory_writeback` and operational metadata. `fresh_audit` is
invariant.

Operational entrypoint:

```text
hermes-ops skill run memory-assisted-audit
```

Stabilized flags: `--project`, `--mission`, `--memory`, `--memory-store`,
`--repository-id`, `--include-path`, `--memory-disclosure`, and `--format`.
Memory defaults to `off`.

Memory failures are diagnostics, never `RankableFinding`, current
classification, or automatic fresh limitation. Unavailable, corrupt,
unsupported, unsafe or degraded stores do not suppress fresh audit.

Metrics stay local, do not enter identity/ranking/persistence and are not
telemetry. Variable monotonic timings stay outside deterministic JSON.

## 13. Evidence summary

| Checkpoint | Full-suite evidence |
|---|---:|
| HERMES-0028 | 805 passed, 11 skipped |
| HERMES-0029 | 824 passed, 11 skipped |
| HERMES-0030 closure | 846 passed, 11 skipped |
| HERMES-0030 privacy | 857 passed, 11 skipped |
| HERMES-0031 | 869 passed, 11 skipped |
| HERMES-0032 | 878 passed, 11 skipped |
| HERMES-0033 | 888 passed, 11 skipped, 0 failed |

Accumulated evidence covers deterministic identity/retrieval, isolation,
OFF/READ/READ_WRITE equality, optional failures, dirty-worktree freshness,
buggy/fixed/regression cycles, path-only outcomes, aligned revalidation,
disclosure, native-payload privacy RED→GREEN, source/secret/path/unknown legacy
blocking, append-only migration, lineage, idempotency and package contents.

## 14. Non-blocking debt

| Debt | Severity | Freeze blocker |
|---|---|---|
| Pre-limit `candidates_considered` metric | LOW | NO |
| Optional administrative migration CLI | LOW | NO |
| Additional auditor coverage | LOW | NO |
| HEADER size refinement | LOW | NO |

No open HIGH or MEDIUM was identified.

## 15. Post-freeze change policy

A frozen-surface change requires: new versioned spec; characterization before
implementation; rationale; compatibility statement; migration plan when stored
identity/schema changes; focused regression; full suite; and operational
dogfood where applicable. Neutral internal work preserving all invariants does
not reopen the freeze.

This freeze does not authorize a new lens or auditor. New capability remains
subject to specification, benchmark, fairness, boundedness and validation.

## 16. Operational dogfood readiness

Classification: `READY`.

All gates pass: six specs implemented; no HIGH/MEDIUM; new and legacy privacy
closed; fresh-result invariance, isolation, retrieval determinism and failure
optionality proven; latest suite has zero failures; and freeze review changes no
code.

The first Lucre Agro dogfood may proceed only as external read-only validation
of this generic tool, without consumer-specific logic in `hermes-ops`.

Role split:

- Hermes: principal executor.
- Codex: independent support/reviewer after execution.
- Codex does not provide ground truth before Hermes executes.

Initial safety: no fix, mutation, deploy, target execution, network, or consumer
integration. Evaluate detection, characterization, insufficient evidence,
Memory usefulness, freshness, ranking, false positives and misses.

## 17. Freeze gates

| Gate | Result | Evidence |
|---|---|---|
| HERMES-0028–0033 implemented | PASS | all six specs `Implementado` |
| No HIGH/MEDIUM | PASS | LOW debt only |
| New-record privacy | PASS | HERMES-0030 sanitizer/privacy suite |
| Legacy policy | PASS | HERMES-0033 block/quarantine/migration |
| Fresh-audit invariant | PASS | mode/disclosure comparisons |
| Repository isolation | PASS | store/retrieval/orchestration tests |
| Retrieval determinism | PASS | ID/score/order/tie-break tests |
| Failure optionality | PASS | unavailable/corrupt/schema/FTS/write matrix |
| Latest full suite | PASS | 888 passed, 11 skipped, 0 failed |
| No core semantic delta | PASS | documentation-only freeze review |

## 18. Final record

- freeze status: `FROZEN_BASELINE_WITH_NON_BLOCKING_DEBT`
- verdict: `HERMES_MEMORY_V1_BASELINE_FROZEN`
- readiness: `LUCRE_AGRO_OPERATIONAL_DOGFOOD_READY`
