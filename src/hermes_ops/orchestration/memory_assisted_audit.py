from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from enum import Enum
import json
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from hermes_ops.memory.core import (
    derive_memory_freshness,
    observation_from_auditor_outcome,
    observation_from_rankable_finding,
)
from hermes_ops.memory.models import (
    AuditMemoryObservation, DisclosureLevel, FreshnessState, LineageEventKind,
    MemoryCandidate, MemoryError, MemoryKind, MemoryRevalidationHint,
    MemoryCurrentContext, MemoryRetrievalRequest,
)
from hermes_ops.memory.store import MemoryService
from hermes_ops.orchestration.models import (
    HistoricalContext, MemoryAssistedAuditPlan, MemoryAssistedAuditRequest,
    MemoryAssistedAuditResult, MemoryMode, MemoryOperationalMetrics,
    MemoryWritebackResult,
)
from hermes_ops.skills.audit_round import (
    AuditRequest, AuditRoundRequest, AuditRoundResult, AuditorOutcome,
    AuditorOutcomeStatus, audit_round_json, run_audit_round,
)
from hermes_ops.skills.execution_path_models import ExecutionPathClassification
from hermes_ops.skills.source_evidence import parse_source_locator


class CandidateSelectionReason(str, Enum):
    SYMBOL_MATCH = "SYMBOL_MATCH"
    PATH_MATCH = "PATH_MATCH"
    AUDITOR_MATCH = "AUDITOR_MATCH"
    LEXICAL_MATCH = "LEXICAL_MATCH"
    LINEAGE_MATCH = "LINEAGE_MATCH"
    EXACT_ID = "EXACT_ID"
    EXACT_LINEAGE = "EXACT_LINEAGE"


_COMPARISON_KEYS = (
    "historical_reproduced", "historical_not_reproduced", "new_findings",
    "lineage_candidates", "aligned_vs_mismatch", "stale_vs_fresh",
)


def _empty_comparison() -> dict[str, tuple[str, ...]]:
    return {key: () for key in _COMPARISON_KEYS}


def _symbols(requests: tuple[AuditRequest, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for request in requests:
        for name in ("producer_symbol", "consumer_symbol", "operation_symbol"):
            value = getattr(request, name, None)
            if type(value) is str:
                values.append(value)
    return tuple(dict.fromkeys(values))


def build_retrieval_request(request: MemoryAssistedAuditRequest) -> MemoryRetrievalRequest:
    return MemoryRetrievalRequest(
        repository_id=request.repository_identity.repository_id,
        symbols=_symbols(request.audit_requests),
        relative_paths=request.authoritative_structural_scope,
        auditor_kinds=tuple(item.auditor_id for item in request.audit_requests),
        mission_terms=tuple(request.mission.split())[:64],
        max_candidates=request.memory_candidate_limit,
        disclosure_level=request.memory_disclosure_level,
        current_context=request.current_context,
    )


def select_candidates(
    candidates: tuple[MemoryCandidate, ...], request: MemoryAssistedAuditRequest,
) -> tuple[tuple[MemoryCandidate, ...], dict[str, tuple[CandidateSelectionReason, ...]]]:
    selected = candidates[:request.memory_candidate_limit]
    request_symbols = set(_symbols(request.audit_requests))
    request_paths = set(request.authoritative_structural_scope)
    request_auditors = {item.auditor_id for item in request.audit_requests}
    reasons: dict[str, tuple[CandidateSelectionReason, ...]] = {}
    for candidate in selected:
        values: list[CandidateSelectionReason] = []
        if request_symbols.intersection(candidate.symbols):
            values.append(CandidateSelectionReason.SYMBOL_MATCH)
        if request_paths.intersection(candidate.paths):
            values.append(CandidateSelectionReason.PATH_MATCH)
        if candidate.source_auditor in request_auditors:
            values.append(CandidateSelectionReason.AUDITOR_MATCH)
        values.append(CandidateSelectionReason.LINEAGE_MATCH)
        reasons[candidate.observation_id] = tuple(values)
    return selected, reasons


def build_revalidation_hints(
    candidates: tuple[MemoryCandidate, ...], service: MemoryService,
    request: MemoryAssistedAuditRequest,
) -> tuple[MemoryRevalidationHint, ...]:
    del request
    if service.store is None:
        return ()
    hints: list[MemoryRevalidationHint] = []
    for candidate in candidates:
        try:
            value = service.store.expand(
                candidate.observation_id, candidate.repository_id,
                DisclosureLevel.REVALIDATION_HINT,
            )
            if type(value) is MemoryRevalidationHint:
                hints.append(value)
        except MemoryError as error:
            service.diagnostics = tuple(sorted(set((*service.diagnostics, error.code))))
    return tuple(hints)


def build_candidate_disclosures(
    candidates: tuple[MemoryCandidate, ...], service: MemoryService,
    level: DisclosureLevel,
) -> tuple[Any, ...]:
    if service.store is None:
        return ()
    values: list[Any] = []
    for candidate in candidates:
        try:
            values.append(service.store.expand(
                candidate.observation_id, candidate.repository_id, level,
            ))
        except MemoryError as error:
            service.diagnostics = tuple(sorted(set((*service.diagnostics, error.code))))
    return tuple(values)


def build_audit_plan(
    request: MemoryAssistedAuditRequest, candidates: tuple[MemoryCandidate, ...],
    hints: tuple[MemoryRevalidationHint, ...],
    selection_reasons: dict[str, tuple[CandidateSelectionReason, ...]],
) -> MemoryAssistedAuditPlan:
    del selection_reasons
    auditors = {item.source_auditor for item in candidates}
    symbols = {value for item in candidates for value in item.symbols}
    paths = {value for item in candidates for value in item.paths}
    for hint in hints:
        auditors.add(hint.historical_auditor)
        symbols.update(hint.suggested_symbols)
        paths.update(hint.suggested_relative_paths)
    return MemoryAssistedAuditPlan(
        request.mission, request.repository_identity, request.current_context,
        request.authoritative_structural_scope, candidates, hints,
        tuple(sorted(auditors)), tuple(sorted(symbols)), tuple(sorted(paths)),
        request.audit_requests, True,
    )


def run_fresh_audit(request: MemoryAssistedAuditRequest) -> AuditRoundResult:
    return run_audit_round(AuditRoundRequest(
        request.target, request.audit_requests, request.authoritative_structural_scope,
    ))


def compute_historical_comparison(
    candidates: tuple[MemoryCandidate, ...], fresh_result: AuditRoundResult,
) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = {key: [] for key in _COMPARISON_KEYS}
    fresh_ids = tuple(item.finding_id for item in fresh_result.ranked_findings.ordered_findings)
    for candidate in candidates:
        if candidate.freshness_state is FreshnessState.STALE_CANDIDATE:
            values["stale_vs_fresh"].append(candidate.observation_id)
        if candidate.memory_kind is MemoryKind.ALIGNED_REVALIDATION and fresh_ids:
            values["aligned_vs_mismatch"].append(candidate.observation_id)
        if candidate.memory_kind is MemoryKind.CONFIRMED_FINDING:
            key = "historical_reproduced" if fresh_ids else "historical_not_reproduced"
            values[key].append(candidate.observation_id)
        else:
            values["lineage_candidates"].append(candidate.observation_id)
    values["new_findings"].extend(fresh_ids)
    return {key: tuple(items) for key, items in values.items()}


def _hint(candidate: MemoryCandidate, hints: tuple[MemoryRevalidationHint, ...]) -> MemoryRevalidationHint | None:
    return next((item for item in hints if item.observation_id == candidate.observation_id), None)


def _candidate_for_finding(finding: Any, candidates: tuple[MemoryCandidate, ...]) -> MemoryCandidate | None:
    finding_paths = {ref.path for ref in finding.evidence_refs}
    return next((item for item in candidates if
        item.memory_kind is MemoryKind.CONFIRMED_FINDING
        and item.source_auditor == finding.source_skill
        and (not item.paths or set(item.paths) == finding_paths)), None)


def _canonical_request(
    request: MemoryAssistedAuditRequest, outcome: AuditorOutcome,
    candidate: MemoryCandidate | None, hints: tuple[MemoryRevalidationHint, ...],
) -> Any:
    if candidate is not None:
        historical = _hint(candidate, hints)
        if historical is not None:
            return historical.canonical_request
    audit_request = next(item for item in request.audit_requests if item.auditor_id == outcome.auditor_id)
    return {field.name: getattr(audit_request, field.name) for field in fields(audit_request)}


def _store_write(
    service: MemoryService, observation: AuditMemoryObservation, *,
    revalidation: bool = False, operational_opt_in: bool = False,
) -> bool:
    if service.store is None:
        raise MemoryError("MEMORY_STORE_UNAVAILABLE", "Memory store is unavailable")
    return service.store.write(
        observation, revalidation=revalidation,
        operational_opt_in=operational_opt_in,
    )


def write_back_observations(
    request: MemoryAssistedAuditRequest, fresh_result: AuditRoundResult,
    plan: MemoryAssistedAuditPlan, candidates: tuple[MemoryCandidate, ...],
    hints: tuple[MemoryRevalidationHint, ...], service: MemoryService,
) -> MemoryWritebackResult:
    del plan
    if not request.allow_post_audit_write or request.memory_mode is not MemoryMode.READ_WRITE:
        return MemoryWritebackResult(False, (), (), ("write_back_disabled",))
    written: list[str] = []
    skipped: list[tuple[str, str]] = []
    diagnostics: list[str] = []
    outcomes = {item.auditor_id: item for item in fresh_result.auditor_outcomes}
    try:
        for finding in fresh_result.ranked_findings.ordered_findings:
            outcome = outcomes[finding.source_skill]
            candidate = _candidate_for_finding(finding, candidates)
            observation = observation_from_rankable_finding(
                finding,
                repository_id=request.repository_identity.repository_id,
                canonical_request=_canonical_request(request, outcome, candidate, hints),
                source_revision=request.current_context.current_revision if request.current_context else None,
                snapshot_digest=fresh_result.snapshot_provenance.digest if fresh_result.snapshot_provenance else None,
                structural_scope=request.authoritative_structural_scope,
                auditor_version=outcome.auditor_version,
                normalizer_version=outcome.normalizer_version,
                limitations=outcome.limitations,
                finding_kind=candidate.finding_kind if candidate else outcome.auditor_id,
                symbols=candidate.symbols if candidate else _symbols(request.audit_requests),
                retrieval_terms=(finding.summary,),
            )
            if _store_write(service, observation):
                written.append(observation.observation_id)
                if candidate is not None and observation.lineage_id == candidate.lineage_id:
                    service.store.append_lineage_event(
                        observation.lineage_id, observation.repository_id,
                        observation.observation_id, LineageEventKind.RECONFIRMED,
                    )

        for outcome in fresh_result.auditor_outcomes:
            if outcome.status is AuditorOutcomeStatus.FAILED or outcome.native_result is None:
                continue
            classification = getattr(outcome.native_result, "classification", None)
            if classification is ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT:
                refs = tuple(
                    parse_source_locator(item)
                    for item in getattr(outcome.native_result, "evidence_references", ())
                )
                paths = tuple(sorted({ref.path for ref in refs}))
                candidate = next((item for item in candidates if
                    item.source_auditor == outcome.auditor_id
                    and item.memory_kind is MemoryKind.PATH_ONLY_OBSERVATION), None)
                observation = observation_from_auditor_outcome(
                    outcome, memory_kind=MemoryKind.PATH_ONLY_OBSERVATION,
                    repository_id=request.repository_identity.repository_id,
                    canonical_request=_canonical_request(request, outcome, candidate, hints),
                    source_revision=request.current_context.current_revision if request.current_context else None,
                    snapshot_digest=fresh_result.snapshot_provenance.digest if fresh_result.snapshot_provenance else None,
                    structural_scope=request.authoritative_structural_scope,
                    finding_kind=candidate.finding_kind if candidate else outcome.auditor_id,
                    symbols=candidate.symbols if candidate else _symbols(request.audit_requests),
                    relative_paths=paths, evidence_refs=refs,
                    retrieval_terms=(outcome.auditor_id,),
                )
                if _store_write(service, observation):
                    written.append(observation.observation_id)

            confirmed = next((item for item in candidates if
                item.source_auditor == outcome.auditor_id
                and item.memory_kind is MemoryKind.CONFIRMED_FINDING), None)
            if confirmed is not None and outcome.status is AuditorOutcomeStatus.COMPLETED_NO_FINDINGS:
                observation = observation_from_auditor_outcome(
                    outcome, memory_kind=MemoryKind.ALIGNED_REVALIDATION,
                    repository_id=request.repository_identity.repository_id,
                    canonical_request=_canonical_request(request, outcome, confirmed, hints),
                    source_revision=request.current_context.current_revision if request.current_context else None,
                    snapshot_digest=fresh_result.snapshot_provenance.digest if fresh_result.snapshot_provenance else None,
                    structural_scope=request.authoritative_structural_scope,
                    finding_kind=confirmed.finding_kind, symbols=confirmed.symbols,
                    relative_paths=confirmed.paths,
                    retrieval_terms=(outcome.auditor_id,),
                )
                if observation.lineage_id == confirmed.lineage_id and _store_write(service, observation, revalidation=True):
                    written.append(observation.observation_id)
                    service.store.append_lineage_event(
                        observation.lineage_id, observation.repository_id,
                        observation.observation_id, LineageEventKind.NOT_REPRODUCED,
                    )

            if request.allow_operational_limitation_write and outcome.limitations:
                observation = observation_from_auditor_outcome(
                    outcome, memory_kind=MemoryKind.OPERATIONAL_LIMITATION,
                    repository_id=request.repository_identity.repository_id,
                    canonical_request=_canonical_request(request, outcome, None, hints),
                    source_revision=request.current_context.current_revision if request.current_context else None,
                    snapshot_digest=fresh_result.snapshot_provenance.digest if fresh_result.snapshot_provenance else None,
                    structural_scope=request.authoritative_structural_scope,
                    finding_kind=outcome.auditor_id, symbols=_symbols(request.audit_requests),
                    retrieval_terms=outcome.limitations,
                )
                if _store_write(service, observation, operational_opt_in=True):
                    written.append(observation.observation_id)
    except Exception as error:
        diagnostics.append(str(getattr(error, "code", f"writeback_failed:{type(error).__name__}")))
    return MemoryWritebackResult(True, tuple(written), tuple(skipped), tuple(diagnostics))


def _context(
    diagnostics: tuple[str, ...], candidates: tuple[MemoryCandidate, ...],
    selected: tuple[MemoryCandidate, ...], hints: tuple[MemoryRevalidationHint, ...],
    plan: MemoryAssistedAuditPlan, provenance: str,
    comparison: dict[str, tuple[str, ...]],
    pre_audit_context: MemoryCurrentContext | None,
    post_audit_context: MemoryCurrentContext | None,
    reasons: dict[str, tuple[CandidateSelectionReason, ...]],
    disclosure: DisclosureLevel,
    metrics: MemoryOperationalMetrics,
    disclosures: tuple[Any, ...],
) -> HistoricalContext:
    summary: dict[FreshnessState, int] = {}
    for candidate in candidates:
        summary[candidate.freshness_state] = summary.get(candidate.freshness_state, 0) + 1
    return HistoricalContext(
        diagnostics, candidates, selected, hints, summary, plan.suggested_symbols,
        plan.suggested_paths, plan.suggested_auditors, provenance, comparison,
        pre_audit_context, post_audit_context,
        {
            observation_id: tuple(reason.value for reason in values)
            for observation_id, values in sorted(reasons.items())
        },
        disclosure, metrics, disclosures,
    )


def _post_audit_context(
    request: MemoryAssistedAuditRequest, fresh_result: AuditRoundResult,
) -> MemoryCurrentContext | None:
    snapshot = fresh_result.snapshot_provenance
    revision = request.current_context.current_revision if request.current_context else None
    if snapshot is None and revision is None:
        return request.current_context
    return MemoryCurrentContext(
        repository_id=request.repository_identity.repository_id,
        current_revision=revision,
        current_snapshot_digest=snapshot.digest if snapshot else None,
        current_structural_scope=(
            snapshot.structural_scope if snapshot
            else request.authoritative_structural_scope
        ),
    )


def refine_candidate_freshness(
    candidates: tuple[MemoryCandidate, ...], context: MemoryCurrentContext | None,
    service: MemoryService | None,
) -> tuple[MemoryCandidate, ...]:
    """Project final freshness without changing retrieval identity or ranking."""
    if context is None or service is None or service.store is None:
        return candidates
    explicit = {
        FreshnessState.INCOMPATIBLE_SCHEMA,
        FreshnessState.SUPERSEDED,
        FreshnessState.NOT_REPRODUCED,
        FreshnessState.REVALIDATED,
    }
    refined: list[MemoryCandidate] = []
    for candidate in candidates:
        if candidate.freshness_state in explicit:
            refined.append(candidate)
            continue
        try:
            observation = service.store.expand(
                candidate.observation_id, candidate.repository_id,
                DisclosureLevel.CANONICAL,
            )
            if type(observation) is not AuditMemoryObservation:
                refined.append(candidate)
                continue
            freshness = derive_memory_freshness(observation, context, None)
            refined.append(replace(candidate, freshness_state=freshness))
        except MemoryError as error:
            service.diagnostics = tuple(sorted(set((*service.diagnostics, error.code))))
            refined.append(candidate)
    return tuple(refined)


def run_memory_assisted_audit(
    request: MemoryAssistedAuditRequest, memory_service: MemoryService | None = None,
) -> MemoryAssistedAuditResult:
    candidates: tuple[MemoryCandidate, ...] = ()
    selected: tuple[MemoryCandidate, ...] = ()
    hints: tuple[MemoryRevalidationHint, ...] = ()
    disclosures: tuple[Any, ...] = ()
    diagnostics: tuple[str, ...] = ("MEMORY_DISABLED",)
    provenance = "disabled"
    reasons: dict[str, tuple[CandidateSelectionReason, ...]] = {}
    retrieval_started = perf_counter_ns()
    retrieval_duration_ms = 0.0
    disclosure_duration_ms = 0.0
    if request.memory_mode is not MemoryMode.DISABLED:
        provenance = "memory_active"
        if memory_service is None:
            diagnostics = ("MEMORY_STORE_UNAVAILABLE",)
        else:
            candidates = memory_service.retrieve(build_retrieval_request(request))
            retrieval_duration_ms = (perf_counter_ns() - retrieval_started) / 1_000_000
            selected, reasons = select_candidates(candidates, request)
            disclosure_started = perf_counter_ns()
            hints = build_revalidation_hints(selected, memory_service, request)
            disclosures = build_candidate_disclosures(
                selected, memory_service, request.memory_disclosure_level,
            )
            disclosure_duration_ms = (perf_counter_ns() - disclosure_started) / 1_000_000
            diagnostics = memory_service.diagnostics
    plan = build_audit_plan(request, selected, hints, reasons)
    fresh_result = run_fresh_audit(request)
    post_context = _post_audit_context(request, fresh_result)
    refined_candidates = refine_candidate_freshness(candidates, post_context, memory_service)
    if memory_service is not None:
        diagnostics = tuple(sorted(set((*diagnostics, *memory_service.diagnostics))))
    refined_by_id = {item.observation_id: item for item in refined_candidates}
    refined_selected = tuple(refined_by_id[item.observation_id] for item in selected)
    comparison = compute_historical_comparison(refined_selected, fresh_result)
    writeback = MemoryWritebackResult(False, (), (), ())
    writeback_duration_ms = 0.0
    if request.memory_mode is MemoryMode.READ_WRITE and request.allow_post_audit_write:
        writeback_started = perf_counter_ns()
        if memory_service is None:
            writeback = MemoryWritebackResult(True, (), (), ("MEMORY_STORE_UNAVAILABLE",))
        else:
            writeback = write_back_observations(request, fresh_result, plan, selected, hints, memory_service)
            diagnostics = tuple(sorted(set((*memory_service.diagnostics, *writeback.write_diagnostics))))
        writeback_duration_ms = (perf_counter_ns() - writeback_started) / 1_000_000
    metrics = MemoryOperationalMetrics(
        retrieval_requested=request.memory_mode is not MemoryMode.DISABLED,
        candidates_returned=len(refined_selected),
        hints_returned=len(hints),
        disclosure_level=request.memory_disclosure_level,
        writeback_attempted=writeback.attempted,
        observations_written=len(writeback.written_observations),
        memory_diagnostics_count=len(diagnostics),
        retrieval_duration_ms=retrieval_duration_ms,
        disclosure_duration_ms=disclosure_duration_ms,
        writeback_duration_ms=writeback_duration_ms,
    )
    return MemoryAssistedAuditResult(
        _context(
            diagnostics, refined_candidates, refined_selected, hints, plan,
            provenance, comparison, request.current_context, post_context,
            reasons, request.memory_disclosure_level, metrics,
            disclosures,
        ),
        plan, fresh_result, writeback,
    )


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def memory_assisted_audit_json(result: MemoryAssistedAuditResult) -> str:
    if type(result) is not MemoryAssistedAuditResult:
        raise ValueError("Serialization requires a memory-assisted audit result")
    memory_context = _plain(result.historical_context)
    reasons = memory_context.pop("candidate_reason_codes") or {}
    for key in ("candidates", "selected_candidates"):
        for candidate in memory_context[key]:
            candidate["reason_codes"] = reasons.get(candidate["observation_id"], [])
    metrics = memory_context.get("operational_metrics")
    if metrics:
        for key in ("retrieval_duration_ms", "disclosure_duration_ms", "writeback_duration_ms"):
            metrics.pop(key, None)
    return json.dumps({
        "memory_context": memory_context,
        "audit_plan": _plain(result.audit_plan),
        "fresh_audit": json.loads(audit_round_json(result.fresh_audit)),
        "memory_writeback": _plain(result.memory_writeback),
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
