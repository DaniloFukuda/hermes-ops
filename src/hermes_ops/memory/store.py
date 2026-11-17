from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sqlite3
from typing import Any

from hermes_ops.skills.finding_models import EvidenceRef

from .core import (
    create_observation, derive_memory_freshness, inspect_observation_privacy,
    is_memory_eligible, privacy_safe_canonical_request, sanitize_memory_payload,
    validate_observation_identity,
)
from .models import (
    AuditMemoryObservation,
    DisclosureLevel,
    FreshnessState,
    LineageEventKind,
    MemoryCandidate,
    LegacyPrivacyState, PrivacyMigrationResult,
    MemoryError,
    MemoryKind,
    MemoryLineageEvent,
    MemoryRetrievalRequest,
    MemoryRevalidationHint,
    MemorySchemaVersion,
    StructuredMemoryDisclosure,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS memory_observations (
 observation_id TEXT PRIMARY KEY, repository_id TEXT NOT NULL, lineage_id TEXT NOT NULL,
 canonical_json TEXT NOT NULL, payload_digest TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memory_lineage_events (
 event_order INTEGER PRIMARY KEY AUTOINCREMENT, lineage_id TEXT NOT NULL,
 repository_id TEXT NOT NULL, observation_id TEXT NOT NULL, kind TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memory_symbols (
 observation_id TEXT NOT NULL, repository_id TEXT NOT NULL, value TEXT NOT NULL,
 PRIMARY KEY (observation_id, value)
);
CREATE TABLE IF NOT EXISTS memory_paths (
 observation_id TEXT NOT NULL, repository_id TEXT NOT NULL, value TEXT NOT NULL,
 PRIMARY KEY (observation_id, value)
);
CREATE TABLE IF NOT EXISTS memory_terms (
 observation_id TEXT NOT NULL, repository_id TEXT NOT NULL, value TEXT NOT NULL,
 PRIMARY KEY (observation_id, value)
);
"""


def _evidence(value: dict[str, Any]) -> EvidenceRef:
    return EvidenceRef(
        value["path"], value["start_line"], value["end_line"],
        value.get("start_column"), value.get("end_column"),
    )


def _observation(value: str) -> AuditMemoryObservation:
    item = json.loads(value)
    return AuditMemoryObservation(
        MemorySchemaVersion(item["memory_schema_version"]), item["observation_id"],
        item["lineage_id"], item["repository_id"], item.get("source_revision"),
        item.get("snapshot_digest"), tuple(item["structural_scope"]),
        item["request_digest"], item["canonical_request"], item["source_auditor"],
        item["auditor_version"], item.get("normalizer_version"), item["outcome_status"],
        item.get("native_classification"), tuple(item["limitations"]),
        item.get("original_finding_id"), item.get("finding_kind"),
        item.get("historical_severity"), item.get("historical_reachability"),
        tuple(_evidence(ref) for ref in item["evidence_refs"]), item.get("native_payload"),
        item["payload_digest"], MemoryKind(item["memory_kind"]), tuple(item["symbols"]),
        tuple(item["relative_paths"]), tuple(item["retrieval_terms"]),
    )


class MemoryStore:
    def __init__(self, path: str | Path, *, read_only: bool = False) -> None:
        self.path = Path(path)
        self.read_only = read_only
        self.diagnostics: tuple[str, ...] = ()
        self._connection: sqlite3.Connection | None = None
        self._closed = False
        try:
            if read_only:
                self._connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
            else:
                self._connection = sqlite3.connect(self.path)
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._migrate()
            self.fts_available = self._enable_fts()
        except BaseException as exc:
            connection = self._connection
            self._connection = None
            self._closed = True
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
            if isinstance(exc, MemoryError):
                raise
            if isinstance(exc, (OSError, sqlite3.Error)):
                raise MemoryError(
                    "MEMORY_STORE_UNAVAILABLE", "Memory store could not be opened"
                ) from exc
            raise

    def _require_connection(self) -> sqlite3.Connection:
        if self._closed or self._connection is None:
            raise MemoryError("MEMORY_STORE_UNAVAILABLE", "Memory store is closed")
        return self._connection

    def _migrate(self) -> None:
        try:
            with self._connection:
                if not self.read_only:
                    self._connection.executescript(_SCHEMA)
                    self._connection.execute(
                        "INSERT OR IGNORE INTO memory_meta(key, value) VALUES ('schema_version', '1')"
                    )
                row = self._connection.execute(
                    "SELECT value FROM memory_meta WHERE key = 'schema_version'"
                ).fetchone()
                if row is None or row[0] != str(MemorySchemaVersion.V1.value):
                    raise MemoryError("MEMORY_SCHEMA_UNSUPPORTED", "Memory schema is unsupported")
        except MemoryError:
            raise
        except sqlite3.DatabaseError as exc:
            raise MemoryError("MEMORY_STORE_CORRUPT", "Memory schema is corrupt") from exc

    def _enable_fts(self) -> bool:
        try:
            if not self.read_only:
                self._connection.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(observation_id UNINDEXED, repository_id UNINDEXED, content)"
                )
                self._connection.commit()
            self._connection.execute("SELECT count(*) FROM memory_fts").fetchone()
            return True
        except sqlite3.Error:
            self.diagnostics = ("MEMORY_FTS_UNAVAILABLE",)
            return False

    def close(self) -> None:
        connection = self._connection
        self._connection = None
        self._closed = True
        if connection is not None:
            connection.close()

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def write(
        self,
        observation: AuditMemoryObservation,
        *,
        operational_opt_in: bool = False,
        revalidation: bool = False,
    ) -> bool:
        self._require_connection()
        if self.read_only:
            raise MemoryError("MEMORY_STORE_UNAVAILABLE", "Memory store is read-only")
        validate_observation_identity(observation)
        if not is_memory_eligible(
            observation, operational_opt_in=operational_opt_in, revalidation=revalidation
        ):
            return False
        encoded = observation.canonical_json()
        existing = self._connection.execute(
            "SELECT canonical_json FROM memory_observations WHERE observation_id = ?",
            (observation.observation_id,),
        ).fetchone()
        if existing is not None:
            if existing[0] != encoded:
                raise MemoryError(
                    "MEMORY_RECORD_INTEGRITY_ERROR",
                    "Observation identity conflicts with canonical payload",
                )
            return False
        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO memory_observations VALUES (?, ?, ?, ?, ?)",
                    (observation.observation_id, observation.repository_id,
                     observation.lineage_id, encoded, observation.payload_digest),
                )
                self._connection.execute(
                    "INSERT INTO memory_lineage_events(lineage_id, repository_id, observation_id, kind) VALUES (?, ?, ?, ?)",
                    (observation.lineage_id, observation.repository_id,
                     observation.observation_id, LineageEventKind.OBSERVED.value),
                )
                self._index(observation)
        except sqlite3.DatabaseError as exc:
            raise MemoryError("MEMORY_STORE_CORRUPT", "Atomic memory write failed") from exc
        return True

    def _index(self, observation: AuditMemoryObservation) -> None:
        for table, values in (
            ("memory_symbols", observation.symbols),
            ("memory_paths", observation.relative_paths),
            ("memory_terms", observation.retrieval_terms),
        ):
            self._connection.executemany(
                f"INSERT INTO {table}(observation_id, repository_id, value) VALUES (?, ?, ?)",
                ((observation.observation_id, observation.repository_id, value) for value in values),
            )
        if self.fts_available:
            content = " ".join((
                observation.finding_kind or "", *observation.symbols,
                *observation.relative_paths, *observation.limitations,
                *observation.retrieval_terms,
            ))
            self._connection.execute(
                "INSERT INTO memory_fts(observation_id, repository_id, content) VALUES (?, ?, ?)",
                (observation.observation_id, observation.repository_id, content),
            )

    def _freshness(
        self, observation: AuditMemoryObservation, request: MemoryRetrievalRequest
    ) -> FreshnessState:
        row = self._connection.execute(
            "SELECT kind FROM memory_lineage_events WHERE lineage_id = ? AND repository_id = ? AND observation_id = ? ORDER BY event_order DESC LIMIT 1",
            (observation.lineage_id, observation.repository_id, observation.observation_id),
        ).fetchone()
        projection = LineageEventKind(row[0]) if row else None
        return derive_memory_freshness(observation, request.current_context, projection)

    def _candidate(self, observation: AuditMemoryObservation, request: MemoryRetrievalRequest) -> MemoryCandidate:
        score = 0
        score += 1000 if request.observation_id == observation.observation_id else 0
        score += 800 if request.lineage_id == observation.lineage_id else 0
        score += 100 * len(set(request.symbols) & set(observation.symbols))
        score += 80 * len(set(request.relative_paths) & set(observation.relative_paths))
        score += 40 if observation.source_auditor in request.auditor_kinds else 0
        score += 40 if observation.finding_kind in request.finding_kinds else 0
        score += 10 * len(set(item.lower() for item in request.mission_terms) & set(item.lower() for item in observation.retrieval_terms))
        summary = " | ".join(item for item in (
            observation.memory_kind.value,
            observation.finding_kind or observation.native_classification or "historical observation",
            ", ".join(observation.symbols),
        ) if item)
        privacy = self.privacy_state(observation)
        return MemoryCandidate(
            observation.observation_id, observation.lineage_id, observation.repository_id,
            observation.memory_kind, observation.source_auditor, observation.source_revision,
            observation.finding_kind, observation.historical_severity, observation.symbols,
            observation.relative_paths, self._freshness(observation, request), len(observation.evidence_refs),
            summary, score,
            privacy in {LegacyPrivacyState.CURRENT_SAFE, LegacyPrivacyState.LEGACY_SAFE_VERIFIED, LegacyPrivacyState.MIGRATED_SAFE},
            observation.observation_id, observation.payload_digest, privacy, True,
        )

    def privacy_state(self, observation: AuditMemoryObservation) -> LegacyPrivacyState:
        rows = self._connection.execute(
            "SELECT kind FROM memory_lineage_events WHERE observation_id = ? ORDER BY event_order",
            (observation.observation_id,),
        ).fetchall()
        kinds = {row[0] for row in rows}
        if LineageEventKind.PRIVACY_MIGRATED.value in kinds:
            return LegacyPrivacyState.MIGRATED_SAFE
        if LineageEventKind.QUARANTINED.value in kinds:
            return LegacyPrivacyState.QUARANTINED
        return inspect_observation_privacy(observation)

    def retrieve(self, request: MemoryRetrievalRequest) -> tuple[MemoryCandidate, ...]:
        self._require_connection()
        if type(request) is not MemoryRetrievalRequest:
            raise MemoryError("MEMORY_RECORD_UNSAFE", "Retrieval request is invalid")
        if request.observation_id:
            row = self._connection.execute(
                "SELECT repository_id FROM memory_observations WHERE observation_id = ?",
                (request.observation_id,),
            ).fetchone()
            if row is not None and row[0] != request.repository_id:
                raise MemoryError("MEMORY_REPOSITORY_MISMATCH", "Observation belongs to another repository")
        query = "SELECT canonical_json FROM memory_observations WHERE repository_id = ?"
        parameters: list[Any] = [request.repository_id]
        if request.observation_id:
            query += " AND observation_id = ?"; parameters.append(request.observation_id)
        if request.lineage_id:
            query += " AND lineage_id = ?"; parameters.append(request.lineage_id)
        rows = self._connection.execute(query, parameters).fetchall()
        observations = [_observation(row[0]) for row in rows]
        if request.symbols:
            placeholders = ",".join("?" for _ in request.symbols)
            ids = {
                row[0] for row in self._connection.execute(
                    f"SELECT DISTINCT observation_id FROM memory_symbols WHERE repository_id = ? AND value IN ({placeholders})",
                    (request.repository_id, *request.symbols),
                ).fetchall()
            }
            observations = [item for item in observations if item.observation_id in ids]
        if request.relative_paths:
            placeholders = ",".join("?" for _ in request.relative_paths)
            ids = {
                row[0] for row in self._connection.execute(
                    f"SELECT DISTINCT observation_id FROM memory_paths WHERE repository_id = ? AND value IN ({placeholders})",
                    (request.repository_id, *request.relative_paths),
                ).fetchall()
            }
            observations = [item for item in observations if item.observation_id in ids]
        if request.auditor_kinds:
            observations = [item for item in observations if item.source_auditor in request.auditor_kinds]
        if request.finding_kinds:
            observations = [item for item in observations if item.finding_kind in request.finding_kinds]
        if request.mission_terms:
            if not self.fts_available:
                return ()
            fts_query = " OR ".join(f'"{item.replace(chr(34), "")}"' for item in request.mission_terms)
            ids = {
                row[0] for row in self._connection.execute(
                    "SELECT observation_id FROM memory_fts WHERE repository_id = ? AND memory_fts MATCH ?",
                    (request.repository_id, fts_query),
                ).fetchall()
            }
            observations = [item for item in observations if item.observation_id in ids]
        candidates = [self._candidate(item, request) for item in observations]
        candidates.sort(key=lambda item: (-item.retrieval_score, item.observation_id))
        return tuple(candidates[:request.max_candidates])

    def _load(self, observation_id: str, repository_id: str) -> AuditMemoryObservation:
        self._require_connection()
        row = self._connection.execute(
            "SELECT repository_id, canonical_json FROM memory_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        if row is None:
            raise MemoryError("MEMORY_STORE_UNAVAILABLE", "Observation is unavailable")
        if row[0] != repository_id:
            raise MemoryError("MEMORY_REPOSITORY_MISMATCH", "Observation belongs to another repository")
        return _observation(row[1])

    def expand(self, observation_id: str, repository_id: str, level: DisclosureLevel) -> Any:
        observation = self._load(observation_id, repository_id)
        privacy = self.privacy_state(observation)
        if level is DisclosureLevel.CANONICAL:
            if privacy not in {
                LegacyPrivacyState.CURRENT_SAFE,
                LegacyPrivacyState.LEGACY_SAFE_VERIFIED,
                LegacyPrivacyState.MIGRATED_SAFE,
            }:
                raise MemoryError("MEMORY_LEGACY_CANONICAL_BLOCKED", "Legacy canonical disclosure is blocked")
            return observation
        if level is DisclosureLevel.HEADER:
            return self._candidate(observation, MemoryRetrievalRequest(repository_id, observation_id=observation_id))
        if level is DisclosureLevel.STRUCTURED:
            return StructuredMemoryDisclosure(
                observation.observation_id, observation.observation_id,
                observation.payload_digest, observation.native_classification,
                observation.limitations, observation.request_digest, observation.evidence_refs,
            )
        if level is DisclosureLevel.REVALIDATION_HINT:
            if not privacy_safe_canonical_request(observation.canonical_request):
                raise MemoryError("MEMORY_LEGACY_HINT_BLOCKED", "Legacy revalidation request is unsafe")
            return MemoryRevalidationHint(
                observation.observation_id, observation.lineage_id, observation.source_auditor,
                observation.canonical_request, observation.symbols, observation.relative_paths,
                observation.structural_scope, observation.observation_id, observation.payload_digest,
            )
        raise MemoryError("MEMORY_RECORD_UNSAFE", "Disclosure level is invalid")

    def append_lineage_event(
        self, lineage_id: str, repository_id: str, observation_id: str,
        kind: LineageEventKind,
    ) -> None:
        self._require_connection()
        row = self._connection.execute(
            "SELECT repository_id, lineage_id FROM memory_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        if row is None or row != (repository_id, lineage_id):
            raise MemoryError("MEMORY_REPOSITORY_MISMATCH", "Lineage event provenance mismatches")
        with self._connection:
            self._connection.execute(
                "INSERT INTO memory_lineage_events(lineage_id, repository_id, observation_id, kind) VALUES (?, ?, ?, ?)",
                (lineage_id, repository_id, observation_id, kind.value),
            )

    def lineage_events(self, lineage_id: str, repository_id: str) -> tuple[MemoryLineageEvent, ...]:
        self._require_connection()
        rows = self._connection.execute(
            "SELECT observation_id, kind FROM memory_lineage_events WHERE lineage_id = ? AND repository_id = ? ORDER BY event_order",
            (lineage_id, repository_id),
        ).fetchall()
        return tuple(MemoryLineageEvent(lineage_id, repository_id, row[0], LineageEventKind(row[1])) for row in rows)

    def rebuild_indexes(self) -> None:
        self._require_connection()
        with self._connection:
            self._connection.execute("DELETE FROM memory_symbols")
            self._connection.execute("DELETE FROM memory_paths")
            self._connection.execute("DELETE FROM memory_terms")
            if self.fts_available:
                self._connection.execute("DELETE FROM memory_fts")
            rows = self._connection.execute("SELECT canonical_json FROM memory_observations").fetchall()
            for row in rows:
                self._index(_observation(row[0]))


class MemoryService:
    def __init__(self, store: MemoryStore | None, diagnostics: tuple[str, ...] = ()) -> None:
        self.store = store
        self.diagnostics = diagnostics

    @classmethod
    def disabled(cls) -> MemoryService:
        return cls(None)

    @classmethod
    def open(cls, path: str | Path, *, read_only: bool = False) -> MemoryService:
        try:
            store = MemoryStore(path, read_only=read_only)
            return cls(store, store.diagnostics)
        except MemoryError as exc:
            return cls(None, (exc.code,))

    def retrieve(self, request: MemoryRetrievalRequest) -> tuple[MemoryCandidate, ...]:
        if self.store is None:
            return ()
        try:
            return self.store.retrieve(request)
        except MemoryError as exc:
            self.diagnostics = tuple(sorted(set((*self.diagnostics, exc.code))))
            return ()

    def close(self) -> None:
        if self.store is not None:
            self.store.close()

    def __enter__(self) -> MemoryService:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def inspect_memory_observation_privacy(
    store: MemoryStore, observation_id: str, repository_id: str,
) -> LegacyPrivacyState:
    """Inspect one explicitly named observation without exposing its payload."""
    observation = store._load(observation_id, repository_id)
    return store.privacy_state(observation)


def _append_event_once(
    store: MemoryStore, observation: AuditMemoryObservation, kind: LineageEventKind,
) -> None:
    if any(
        event.observation_id == observation.observation_id and event.kind is kind
        for event in store.lineage_events(observation.lineage_id, observation.repository_id)
    ):
        return
    store.append_lineage_event(
        observation.lineage_id, observation.repository_id,
        observation.observation_id, kind,
    )


def migrate_memory_observation_privacy(
    store: MemoryStore, observation_id: str, repository_id: str,
) -> PrivacyMigrationResult:
    """Explicitly append a deterministic safe projection of one legacy record."""
    source = store._load(observation_id, repository_id)
    if not privacy_safe_canonical_request(source.canonical_request):
        _append_event_once(store, source, LineageEventKind.QUARANTINED)
        raise MemoryError("MEMORY_LEGACY_MIGRATION_UNSAFE", "Legacy request cannot be migrated safely")
    if not source.source_auditor or not source.finding_kind:
        _append_event_once(store, source, LineageEventKind.QUARANTINED)
        raise MemoryError("MEMORY_LEGACY_MIGRATION_UNSAFE", "Legacy structural identity is insufficient")
    if source.memory_kind is MemoryKind.CONFIRMED_FINDING:
        payload = sanitize_memory_payload({
            "source_skill": source.source_auditor,
            "finding_id": source.original_finding_id,
            "finding_kind": source.finding_kind,
            "severity": source.historical_severity,
            "evidence_strength": None,
            "production_reachability": source.historical_reachability,
            "evidence_refs": source.evidence_refs,
        })
    else:
        payload = sanitize_memory_payload({
            "source_auditor": source.source_auditor,
            "finding_kind": source.finding_kind,
            "outcome_status": source.outcome_status,
            "native_classification": source.native_classification,
            "limitations": source.limitations,
            "symbols": source.symbols,
            "relative_paths": source.relative_paths,
            "evidence_refs": source.evidence_refs,
        })
    migrated = create_observation(
        repository_id=source.repository_id,
        source_revision=source.source_revision,
        snapshot_digest=source.snapshot_digest,
        structural_scope=source.structural_scope,
        canonical_request=source.canonical_request,
        source_auditor=source.source_auditor,
        auditor_version=source.auditor_version,
        normalizer_version=source.normalizer_version,
        outcome_status=source.outcome_status,
        native_classification=source.native_classification,
        limitations=source.limitations,
        original_finding_id=source.original_finding_id,
        finding_kind=source.finding_kind,
        historical_severity=source.historical_severity,
        historical_reachability=source.historical_reachability,
        evidence_refs=source.evidence_refs,
        native_payload=payload,
        memory_kind=source.memory_kind,
        symbols=source.symbols,
        relative_paths=source.relative_paths,
        retrieval_terms=source.retrieval_terms,
    )
    if migrated.lineage_id != source.lineage_id or migrated.observation_id == source.observation_id:
        _append_event_once(store, source, LineageEventKind.QUARANTINED)
        raise MemoryError("MEMORY_LEGACY_MIGRATION_UNSAFE", "Safe migration identity could not be established")
    created = store.write(
        migrated,
        revalidation=migrated.memory_kind is MemoryKind.ALIGNED_REVALIDATION,
        operational_opt_in=migrated.memory_kind is MemoryKind.OPERATIONAL_LIMITATION,
    )
    _append_event_once(store, source, LineageEventKind.QUARANTINED)
    _append_event_once(store, migrated, LineageEventKind.PRIVACY_MIGRATED)
    return PrivacyMigrationResult(
        source.observation_id, migrated.observation_id, migrated.lineage_id,
        "HERMES-0033-v1", created, "MEMORY_LEGACY_MIGRATION_COMPLETE",
    )
