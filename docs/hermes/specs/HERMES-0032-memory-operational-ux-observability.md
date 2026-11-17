---
id: HERMES-0032
title: Memory Operational UX and Observability
status: Implementado
---

# HERMES-0032 — Memory Operational UX and Observability

## 1. Context

Memory V1 retrieval, freshness, privacy, orchestration, and CLI provenance are
implemented by HERMES-0028 through HERMES-0031. Selection reason codes exist
internally, but are discarded before presentation. Disclosure is not selectable
from CLI, help is incomplete, and local operational counts/timings are absent.

## 2. Confirmed problem

Operators cannot see why a candidate was selected, which disclosure is active,
or stable operation counts. They also cannot request an existing disclosure
level through the existing command. This is an observability gap, not a Memory
semantic defect.

## 3. Plain-language explanation

The system already knows why history matched and already supports four safe
levels of detail. This change carries that information to text/JSON output and
measures local orchestration work. It does not influence retrieval, findings,
freshness, writes, or lineage.

## 4. Current behavior

Selection reasons are computed then discarded. CLI always uses HEADER.
Candidate text shows ID/freshness only. Diagnostics are a compact comma list.
No local metrics model exists.

## 5. Desired behavior

- Expose deterministic, ordered, deduplicated real selection reason codes.
- Add `--memory-disclosure` mapped exactly to the four existing enum values.
- Improve concise help and text diagnostics.
- Add derived local counts and monotonic durations.
- Keep variable timings out of deterministic JSON while exposing stable counts.
- Preserve privacy and every semantic invariant.

## 6. Out of scope

No Memory/core semantic change, schema migration, new lens/auditor/ranking,
LLM, daemon, telemetry backend, network, or persistence of metrics.

## 7. Invariants and security rules

`MEMORY_IS_CONTEXT_NOT_EVIDENCE`, `OBSERVABILITY_MUST_NOT_CHANGE_SEMANTICS`,
`HISTORICAL_RELEVANCE_IS_NOT_CURRENT_FINDING_PRIORITY`, and
`NO_EXTERNAL_TELEMETRY` are mandatory. Presentation never enters IDs, scores,
freshness, write eligibility, lineage, or Audit Round. Canonical disclosure
remains subject to HERMES-0030 privacy sanitization.

## 8. Inputs and outputs

Input adds optional `--memory-disclosure` with `header`, `structured`,
`canonical`, and `revalidation-hint`; default is `header`. Memory JSON additions
are limited to candidate `reason_codes`, effective disclosure, deterministic
diagnostics presentation, and stable operational metrics. Fresh-audit JSON is
unchanged.

## 9. Language-independent pseudocode

```text
parse disclosure flag and map it to the existing Memory enum
start a local monotonic retrieval timer
retrieve candidates without changing query, limit, score, or order
select candidates and retain the real reason codes already computed
expand selected hints at the requested existing disclosure boundary
record stable counts and local elapsed durations
run the fresh audit unchanged
perform unchanged write-back while measuring local elapsed duration
return presentation metadata beside the unchanged semantic results
text output includes counts, timings, diagnostics, disclosure, freshness, score, reasons
deterministic JSON includes stable counts but excludes variable durations
never send, persist, or network any metric
```

## 10. Main flow

Reason codes originate only in `select_candidates`. Metrics wrap orchestration
boundaries. `candidates_considered` is omitted in V1 because the store does not
expose the pre-limit row count without changing retrieval. `candidates_returned`
means candidates presented after the existing retrieval/selection limit;
`hints_returned` means produced hints; `observations_written` means successful
canonical writes.

## 11. Error cases and boundaries

Invalid disclosure is rejected by argparse. Disabled/unavailable/corrupt/FTS
diagnostics remain Memory metadata, never findings. Timings may be zero and are
non-canonical. Other skills reject Memory flags. Disclosure never controls
storage. No target is executed.

## 12. Acceptance criteria

- **AC-01:** JSON/text expose real PATH, SYMBOL, AUDITOR, and LINEAGE reasons in
  deterministic deduplicated order.
- **AC-02:** CLI maps the four values exactly and defaults to HEADER.
- **AC-03:** Invalid disclosure is rejected and help accurately describes
  mission, Memory context, fresh audit, store, repository ID, and disclosure.
- **AC-04:** All freshness states and deterministic diagnostics remain visible.
- **AC-05:** Stable metrics expose requested/returned/hint/write/diagnostic counts
  and effective disclosure; local text exposes monotonic durations.
- **AC-06:** Variable timings are excluded from deterministic JSON and no metric
  is transmitted or persisted.
- **AC-07:** Candidate IDs, scores, ordering, selection limit, freshness, hints,
  repository isolation, and reason calculation are unchanged.
- **AC-08:** Fresh Audit Round is byte-identical across modes/disclosures.
- **AC-09:** Disclosure does not alter eligible observation identity/payload.
- **AC-10:** HEADER/STRUCTURED/CANONICAL/HINT preserve HERMES-0030 privacy.
- **AC-11:** Previous CLI usage remains valid and unrelated skills reject flags.
- **AC-12:** Aligned history and path-only behavior remain unchanged.
- **AC-13:** Dogfood proves UX, size proxy, freshness, revalidation, regression,
  privacy, and invariants.
- **AC-14:** Frozen core and Memory SQLite schema remain unchanged.

## 13. Test plan

Start with RED tests for JSON reasons and CLI structured disclosure. Cover the
35 required matrix items through a dedicated HERMES-0032 module plus existing
CLI, orchestration, Memory, freshness, privacy, Audit Round, and ranking tests.
Run eight-round CLI dogfood, focused/regression/full suites, build,
anti-hardcode, frozen-core, and schema checks.

## 14. Likely affected files

`src/hermes_ops/cli.py`, `src/hermes_ops/commands/skill.py`, orchestration
presentation/models, dedicated tests, and this specification.

## 15. Known risks

Reason projection could drift from selection, timings could break deterministic
JSON, disclosure could accidentally govern storage, or richer output could leak
source. Direct invariant and privacy comparisons guard each risk.

## 16. Validation evidence

- RED: JSON lacked `reason_codes` and argparse rejected structured disclosure;
  the two-test run failed twice in `0.54s`.
- Initial GREEN: HERMES-0032 plus HERMES-0030/0031 compatibility passed `37`
  tests in `3.18s`.
- Dedicated tests pass `9` test functions, including four parameterized
  disclosure/privacy cases. Focused coverage passed `188` tests with one
  expected external-clone skip in `21.42s`.
- Broad regression passed `480` tests with eight expected Windows portability
  skips in `39.14s`.
- Full suite collected `889` tests: `878 passed`, `11 skipped`, zero failed in
  `86.61s`; no skip was added.
- Wheel and sdist build succeeded and contain Memory/orchestration modules.
- No Memory SQLite schema or retrieval scoring implementation changed.

## 17. Dogfood and UX evidence

Eight real CLI rounds under the system temporary directory covered buggy
READ_WRITE/HEADER, buggy READ at all four disclosures, fixed READ, fixed
READ_WRITE/STRUCTURED, and buggy regression READ/HEADER. The relevant candidate
was Top-1 with `PATH_MATCH,AUDITOR_MATCH,LINEAGE_MATCH`. Same source was
`SAME_SNAPSHOT_CANDIDATE`; fixed source was `STALE_CANDIDATE`; aligned history
became `NOT_REPRODUCED`; regression produced a fresh finding.

Candidate-disclosure sizes were measured as bytes, not tokens: HEADER `744`,
STRUCTURED `543`, CANONICAL `1588`, and REVALIDATION_HINT `583`. Relative to
CANONICAL these reduce size by 53.1%, 65.8%, and 63.3%, respectively. Canonical
Memory output contained no source literal or host path. HINT explicitly reported
`requires_fresh_audit=true`. Stable metrics were useful in JSON; local timing
was confined to text and did not disturb deterministic JSON.

UX assessment: text `CLEAR`; JSON `CLEAR`; disclosure
`USABLE_WITH_MINOR_FRICTION` because HEADER's generic candidate projection is
larger than STRUCTURED; diagnostics `CLEAR`; freshness `CLEAR`; reason codes
`CLEAR`.

## 18. Freeze readiness

Recommendation: `MEMORY_V1_NEEDS_MORE_WORK`. Current operational behavior is
stable enough for continued use, but a documentary freeze should wait for an
explicit policy/migration for legacy pre-HERMES-0030 unsafe CANONICAL records
and a decision on whether pre-limit `candidates_considered` observability is
worth a future store API. Neither gap blocks HERMES-0032.
