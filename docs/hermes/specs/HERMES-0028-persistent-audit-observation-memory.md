---
spec_id: HERMES-0028
title: Persistent Audit Observation Memory and Deterministic Retrieval Foundation
version: 1
status: Implementado
date: 2026-08-23
depends_on: [HERMES-0017, HERMES-0018, HERMES-0026, HERMES-0027]
---

# HERMES-0028 — Persistent Audit Observation Memory and Deterministic Retrieval Foundation

## 1. Objective

Criar uma Memory / Retrieval Layer V1 local, offline, opcional e isolada para
persistir observations históricas elegíveis, recuperá-las deterministicamente
e oferecer contexto progressivo para uma auditoria nova.

## 2. Architectural boundary

```text
fresh AuditRoundResult / auditor outcome
  -> eligibility + privacy gate
  -> canonical observation
  -> repository-isolated SQLite store
  -> structured indexes + optional FTS5
  -> ranked historical candidates
  -> progressive disclosure / revalidation hint
  -> fresh audit remains authoritative
```

A implementação reside em `hermes_ops.memory`, acima do core congelado. Não
altera Audit Round, auditors, finding ranking, classifications, evidence refs,
finding IDs, structural scope ou fail-closed behavior.

## 3. MEMORY_IS_CONTEXT_NOT_EVIDENCE

Memória sugere auditor, request, symbols, paths e scope. Ela nunca cria finding
atual, nunca fornece strength/reachability atuais e nunca substitui controlled
reading ou fresh auditor outcome. Nenhum memory fact entra em auditor.

## 4. Canonical record model

`AuditMemoryObservation` é frozen e contém schema version, observation/lineage
IDs, repository ID, revision/snapshot, scope, request digest/payload, auditor e
versions, outcome/classification, limitations, finding metadata histórica,
evidence refs, payload/digest, kind, symbols, paths e termos sanitizados.

Canonical observations são separados de tabelas derivadas, FTS e presentations.
Summary nunca participa da identidade canônica.

## 5. Repository identity

`RepositoryIdentity` exige `repository_id` explícito ou o deriva
deterministicamente de logical name + origin fingerprint fornecidos. Nome de
pasta e path absoluto nunca bastam. O ID participa de records e queries; V1
proíbe retrieval cross-repository.

## 6. Observation identity

`observation_id` é SHA-256 de schema, repository, revision/snapshot, scope,
request digest, auditor/version, kind/finding identity e payload digest. Não
usa UUID, row ID, timestamp ou path absoluto. Revisão, repository, request,
auditor ou payload distintos produzem observation distinta.

## 7. Lineage identity

`lineage_id` é SHA-256 de repository, auditor, request semantic identity,
kind/finding kind e paths/symbols estáveis; não inclui revision. Sem identidade
causal suficiente, a lineage fica observation-specific, sem heurística por nome.

Eventos frozen append-only: `OBSERVED`, `RECONFIRMED`, `NOT_REPRODUCED`,
`SUPERSEDED` e `SCHEMA_MIGRATED`.

## 8. Persistence backend

SQLite standard library em path fornecido pelo caller. Canonical observation,
evento e índices obrigatórios são gravados atomicamente. FTS5 indexa somente
texto estrutural derivado; se indisponível, exact retrieval continua e a
limitation `MEMORY_FTS_UNAVAILABLE` é exposta.

## 9. Migrations

`memory_meta` registra schema 1. O protocolo transacional suporta criação
`0 -> 1`, repeated open idempotente e rejeita versão futura sem downgrade ou
reinterpretação silenciosa.

## 10. Write eligibility

Always: confirmed rankable finding e benchmark validado. Conditional: path-only
com path/evidence; aligned apenas como revalidation/benchmark; limitation apenas
com opt-in recorrente/operacional. Failed, malformed, empty/no-op ou unsafe não
são elegíveis. Recorrência não é inferida.

## 11. Privacy and sanitization

Canonical store rejeita paths absolutos Windows/POSIX, raw source declarado,
secret/token fields e objetos arbitrários. Prefere relative paths, symbols,
`EvidenceRef`, digests e enums. Limites: 64 symbols, 64 paths, 256 terms, 256
evidence refs, request 64 KiB, payload 256 KiB, query 64 terms e 100 candidates.

## 12. Retrieval query

`MemoryRetrievalRequest` frozen exige repository ID e aceita observation/lineage
IDs, symbols, relative paths, auditors, finding kinds, mission terms,
`max_candidates`, freshness e disclosure. Valores são limitados e sanitizados.

## 13. Exact retrieval

Suporta observation ID, lineage ID, symbol, relative path, auditor, finding kind
e combinações. Toda query inclui repository ID e retorna ordering determinístico.

## 14. Lexical retrieval

FTS5 cobre termos da missão, summary algorítmico, finding kind, symbols, paths e
limitations. Raw source não é indexado; nenhuma LLM é usada. Fallback sem FTS
preserva exact retrieval.

## 15. Retrieval ranking

`HISTORICAL_RETRIEVAL_RELEVANCE` é separado de prioridade atual. Sinais, em
ordem: ID/lineage exato, symbol, path, auditor/finding kind, lexical overlap,
freshness e revalidation. `observation_id` é tie-break. Severity histórica não
domina e nunca altera `CommonSeverity`, strength, reachability ou finding ID.

## 16. Freshness model

Estados: `CURRENTLY_UNVERIFIED`, `SAME_SNAPSHOT_CANDIDATE`, `STALE_CANDIDATE`,
`REVALIDATED`, `SUPERSEDED`, `NOT_REPRODUCED`, `INCOMPATIBLE_SCHEMA`. Relações:
`SAME_REVISION`, `SAME_SNAPSHOT`, `DIFFERENT_REVISION`, `UNKNOWN`. Freshness é
metadata histórica, nunca EvidenceStrength.

## 17. Progressive disclosure

`HEADER` traz metadata mínima e evidence count; `STRUCTURED` acrescenta
classification, limitations, request identity e locators; `CANONICAL` retorna a
observation completa; `REVALIDATION_HINT` sugere auditor/request/scope com
`requires_fresh_audit=True`. Toda presentation aponta ao canonical record e
payload digest.

## 18. Failure and optionality

Modos: disabled, unavailable, read-only e writable. Diagnósticos próprios:
`MEMORY_STORE_UNAVAILABLE`, `MEMORY_STORE_CORRUPT`, `MEMORY_SCHEMA_UNSUPPORTED`,
`MEMORY_FTS_UNAVAILABLE`, `MEMORY_RECORD_UNSAFE`,
`MEMORY_RECORD_INTEGRITY_ERROR`, `MEMORY_REPOSITORY_MISMATCH`. Nenhum vira core
finding. Falha/desabilitação de memory nunca quebra ou muda core audit.

## 19. Schema versioning

`MemorySchemaVersion.V1` é explícita em records/store. Readers falham fechado
para versão desconhecida. Migrations são explícitas, transacionais e
determinísticas; índices podem ser reconstruídos do canonical store.

## 20. Non-goals

Embeddings, vector DB, cloud sync, cross-user/repository retrieval, daemon,
compaction destrutiva, deletion API, source archive, DLP complexo, LLM,
knowledge graph, autonomous scope narrowing/fixing, semantic fact sharing,
execução de target e qualquer mudança no core congelado.

Canonical observations não expiram automaticamente; duplicates exatos são
deduplicados e presentations/índices são reconstruíveis. Retention/deletion
governada permanece debt futuro.

## 21. Acceptance criteria

- **AC-01:** memory schema version é explícita.
- **AC-02:** repository isolation é obrigatória.
- **AC-03:** absolute paths não entram no canonical store.
- **AC-04:** observation ID é determinístico.
- **AC-05:** lineage é separada da observation identity.
- **AC-06:** observations são append-only/idempotentes.
- **AC-07:** integrity conflict falha fechado.
- **AC-08:** SQLite migration é transacional.
- **AC-09:** exact retrieval funciona offline.
- **AC-10:** lexical retrieval usa FTS5 quando disponível.
- **AC-11:** ausência de FTS5 não quebra exact retrieval nem core.
- **AC-12:** retrieval ranking é determinístico.
- **AC-13:** severity histórica não vira current priority.
- **AC-14:** header não carrega payload completo.
- **AC-15:** structured disclosure aponta para canonical.
- **AC-16:** canonical disclosure preserva provenance.
- **AC-17:** presentation nunca substitui canonical.
- **AC-18:** fresh revalidation é obrigatória para conclusão atual.
- **AC-19:** memory não cria finding atual.
- **AC-20:** aligned histórico não suprime fresh finding.
- **AC-21:** memory failure não quebra core.
- **AC-22:** memory disabled preserva core behavior.
- **AC-23:** não há semantic fact sharing.
- **AC-24:** `audit_round.py` permanece semanticamente intocado.
- **AC-25:** confirmed finding é elegível.
- **AC-26:** failed audit não vira semantic memory.
- **AC-27:** path-only exige path/evidence útil.
- **AC-28:** limitation exige opt-in operacional.
- **AC-29:** unknown schema falha fechado.
- **AC-30:** indexes são reconstruíveis do canonical store.
- **AC-31:** candidate ordering usa tie-break determinístico.
- **AC-32:** repository mismatch rejeita retrieval.
- **AC-33:** request canonicalization é determinística.
- **AC-34:** store funciona sem rede.
- **AC-35:** target consumidor nunca é importado/executado.
- **AC-36:** candidate/hint não cria conclusão.
- **AC-37:** wrong-store histórico é recuperável por estrutura.
- **AC-38:** state-effect histórico é recuperável.
- **AC-39:** fixed/aligned revalidation compartilha lineage quando aplicável.
- **AC-40:** full regression do core permanece verde.

## 22. Evidence

- TDD RED inicial: coleta falhou com `ModuleNotFoundError` para
  `hermes_ops.memory` antes da implementação.
- Iteração models/identity/privacy/store: 16 passed e três contratos RED;
  depois de type-preserving assertion, opt-in limitation fixture e exact
  retrieval via índices derivados, 19 passed.
- Generic + integration/dogfoods finais: 27 passed. Incluem IDs, lineage,
  privacy, migrations, append-only/idempotency/integrity, exact/lexical,
  repository isolation, disclosure, freshness/events, optionality/corruption,
  rebuild, 120 observations, FTS5 runtime, dogfoods e core invariant.
- FTS5: disponível no `sqlite3` do runtime local; fallback controlado permanece
  implementado e testado por contrato.
- Focados memory + ranking + Audit Round + execution + persistence + state +
  controlled reading: 222 passed, 2 skipped em 4,96 s. Skips conhecidos de
  symlink no Windows.
- Regressões amplas de mission/Analysis Pack/skills/CLI/Git/serialization e
  packaging: 365 passed, 7 skipped em 78,64 s. Skips conhecidos de
  symlink/permissão e dogfooding externo opt-in.
- Full suite: 805 passed, 11 skipped, 0 failed em 86,82 s; 27 testes a mais que
  o baseline HERMES-0026 e nenhum skip novo.
- Dogfoods herméticos: wrong-store, state-effect, fixed/aligned revalidation e
  path-only foram persistidos/recuperados; hints exigem fresh audit e nenhum
  candidate é `RankableFinding` atual.
- Core invariant: JSON de ranking permaneceu byte-for-byte idêntico com memory
  ausente e store presente mas fora do core. `audit_round.py` não foi alterado.
- Build: wheel e sdist construídos com sucesso. Ambos contêm exatamente uma
  cópia de `hermes_ops.memory.__init__`, `core`, `models` e `store`.
- Anti-hardcode e arquitetura: `ANTI_HARDCODE_OK` e
  `NO_PRIVATE_AUDITOR_COUPLING_OK`.
