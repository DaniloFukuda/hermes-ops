---
spec_id: HERMES-0030
title: Memory-Assisted Audit Orchestration
version: 2
status: Implementado
date: 2026-08-24
depends_on: [HERMES-0028, HERMES-0029, HERMES-0018, HERMES-0017]
---

# HERMES-0030 — Memory-Assisted Audit Orchestration

## 1. Objective

Integrar a Memory (HERMES-0028/0029) ao fluxo operacional real do Hermes para que uma nova missão possa:

1. obter provenance atual do repositório;
2. consultar Memory V1;
3. recuperar contexto histórico relevante;
4. produzir um plano de revalidação;
5. executar auditoria FRESCA usando o core existente;
6. produzir findings/ranking exclusivamente a partir da auditoria fresca;
7. opcionalmente registrar outcomes elegíveis na Memory depois da rodada.

A Memory deve passar de subsystem manual para capability operacional do Hermes.

## 2. Architectural Boundary

```
mission
    → current provenance
    → memory retrieval
    → historical candidates
    → revalidation planning
    → authoritative audit request/scope
    → FRESH CONTROLLED AUDIT
    → fresh normalization/ranking
    → current result
    → optional post-audit memory write
```

A Memory fica ACIMA do frozen core. Não altera:
- `audit_round.py`
- `finding_ranking.py`
- `execution_path_review.py`
- `persistence_contract_review.py`
- `state_guard_effect_review.py`
- `code_audit.py`

## 3. MEMORY_IS_CONTEXT_NOT_EVIDENCE (Princípio Inviolável)

A memória **nunca** pode:
- criar finding atual;
- confirmar finding atual;
- alterar severity atual;
- alterar EvidenceStrength atual;
- alterar ProductionReachability atual;
- alterar finding_id atual;
- fornecer native facts a um auditor;
- compartilhar semantic facts entre auditors;
- evitar controlled reading;
- transformar historical alignment em suppressão de auditoria;
- restringir scope autoritativo silenciosamente.

## 4. Operational Modes

Enum frozen: `MemoryMode`

- `MEMORY_DISABLED` — Hermes funciona como antes da Memory.
- `MEMORY_READ_ONLY` — consulta histórico, mas não grava.
- `MEMORY_READ_WRITE` — consulta antes e grava observations elegíveis depois.

**Default operacional:** `MEMORY_DISABLED` (conservador para V1).

Falha de Memory em qualquer modo que permita Memory:
- fresh core deve continuar normalmente;
- diagnostics da Memory são preservados;
- current audit result não muda por causa da falha.

## 5. Request Model: `MemoryAssistedAuditRequest`

Frozen dataclass com campos mínimos:

- `mission: str`
- `repository_identity: RepositoryIdentity`
- `current_context: MemoryCurrentContext | None`
- `authoritative_structural_scope: tuple[str, ...]`
- `audit_requests: tuple[AuditRequest, ...]`
- `memory_mode: MemoryMode = MemoryMode.DISABLED`
- `memory_candidate_limit: int = 20`
- `memory_disclosure_level: DisclosureLevel = DisclosureLevel.HEADER`
- `allow_memory_scope_suggestions: bool = False`
- `allow_post_audit_write: bool = False`

**Não aceita:**
- current finding
- current classification
- current severity
- native auditor facts históricos

Compor modelos existentes quando possível (HERMES-0029 `MemoryCurrentContext`, `RepositoryIdentity`, `AuditRequest`).

## 6. Result Model: `MemoryAssistedAuditResult`

Frozen dataclass com namespaces claramente separados:

### `historical_context`
- `memory_diagnostics: tuple[str, ...]`
- `candidates: tuple[MemoryCandidate, ...]`
- `selected_candidates: tuple[MemoryCandidate, ...]`
- `revalidation_hints: tuple[MemoryRevalidationHint, ...]`
- `freshness_summary: dict[FreshnessState, int]`
- `suggested_symbols: tuple[str, ...]`
- `suggested_paths: tuple[str, ...]`
- `suggested_auditors: tuple[str, ...]`
- `memory_provenance: str`

### `fresh_audit`
- `audit_round_result: AuditRoundResult` (existente, intacto)

### `memory_writeback`
- `attempted: bool`
- `written_observations: tuple[str, ...]` (observation_ids)
- `skipped_observations: tuple[tuple[str, str], ...]` (observation_id, reason)
- `write_diagnostics: tuple[str, ...]`

**Nunca misturar historical candidate com fresh finding na mesma coleção.**

## 7. Pre-Audit Memory Retrieval

Fluxo:

```
mission + repository ID + current context + explicit structural scope
    → MemoryRetrievalRequest
```

Query usa:
- mission terms;
- symbols declarados pelos audit requests;
- paths do structural scope;
- auditor IDs;
- finding kinds quando explicitamente aplicáveis.

**Não incluir:**
- finding esperado;
- classification esperada;
- cross-repository retrieval.

## 8. Candidate Selection

**Sem LLM.** Seleção determinística preservando ordering da Memory retrieval.

Selecionar no máximo `memory_candidate_limit`.

Não alterar ranking weights da HERMES-0029.

Candidate selection produz:
- selected candidates;
- reason codes estruturais: `SYMBOL_MATCH`, `PATH_MATCH`, `AUDITOR_MATCH`, `LEXICAL_MATCH`, `LINEAGE_MATCH`;
- freshness;
- disclosure level usado.

Não transformar Top-1 em verdade.

## 9. Memory-Assisted Audit Plan

Modelo frozen: `MemoryAssistedAuditPlan`

Campos:
- `mission`
- `repository/current context`
- `authoritative_structural_scope`
- `historical_candidates`
- `revalidation_hints`
- `suggested_auditors`
- `suggested_symbols`
- `suggested_paths`
- `audit_requests`
- `requires_fresh_audit: bool = True`

**Princípio:** `suggested_scope != authoritative_scope`

Na V1:
- Memory NÃO reduz structural scope automaticamente.
- Se memory paths forem úteis: registrar como `suggested_paths`; não remover paths do request original.
- Se futura expansão de scope for permitida: somente com política explícita e nunca silenciosamente.

## 10. Revalidation Hint Usage

`MemoryRevalidationHint` pode ajudar a preparar:
- auditor apropriado;
- historical request identity;
- symbols;
- paths;
- structural scope histórico;
- lineage.

Mas **não pode** fornecer:
- historical classification como expectativa;
- current finding;
- historical EvidenceStrength como current strength;
- historical reachability como current reachability.

Fresh request deve permanecer válido por seus próprios contratos.

## 11. Fresh Audit Boundary

Boundary explícita no código:

```
historical planning terminou
-------------------------
fresh audit começou
```

A partir daqui:
- auditor recebe apenas inputs normais;
- snapshot é novo/controlado;
- evidence refs são novas;
- classifications são recalculadas;
- findings são novos;
- normalizer funciona normalmente;
- ranking HERMES-0017 funciona normalmente.

**Nenhum objeto MemoryCandidate deve atravessar para auditor input.**

Provar por testes/spies que Audit Round não recebe Memory objects.

## 12. Audit Round Integration

Preferência: chamar `run_audit_round(...)` como consumer externo.

Não alterar internals da Audit Round.

A orchestration pode:
1. preparar request;
2. chamar Audit Round;
3. receber resultado;
4. comparar historicamente depois.

## 13. Historical Comparison

Depois da fresh audit, orchestration pode produzir comparação informativa:
- `historical finding reproduced`
- `historical finding not reproduced`
- `new finding`
- `lineage candidate`
- `historical aligned vs fresh mismatch`
- `historical stale vs fresh result`

Essas comparações são presentation/context.

**Não alterar fresh result.**

## 14. Post-Audit Write Path

Somente após fresh result finalizado.

Fluxo:
```
fresh completed audit
    → memory eligibility
    → privacy gate
    → observation adapters HERMES-0028
    → canonical observation
    → append-only transaction
```

Não gravar durante auditor execution.
Não gravar failed auditor como semantic memory.
Respeitar eligibility existente.

## 15. Write-Back Policy V1

Elegíveis automaticamente, se privacy/provenance válidos:
- confirmed fresh findings;
- fresh path-only útil com evidence/path;
- explicit revalidation outcomes;
- recurring/opt-in operational limitations conforme policy existente.

Aligned:
somente como revalidation de lineage histórica ou contrato explicitamente acompanhado.

Não encher store com todos os no-findings.

## 16. Lineage Update

Quando fresh audit revalida candidate histórico:

Historical confirmed + fresh confirmed equivalent
→ nova observation + RECONFIRMED.

Historical confirmed + fresh aligned/no finding
→ nova observation apropriada + NOT_REPRODUCED.

Historical state superseded de forma demonstrável
→ SUPERSEDED quando semanticamente permitido pela policy atual.

Não inferir equivalência apenas por resumo textual.
Usar lineage existente quando identity causal for demonstrável.

## 17. Memory Failure Safety

Testes obrigatórios:
1. Memory disabled.
2. Store unavailable.
3. Store corrupt.
4. Unsupported schema.
5. FTS unavailable.
6. Write failure depois da fresh audit.

Em todos:
- fresh audit deve continuar.

Especialmente:
- write failure NÃO pode invalidar o AuditRoundResult já produzido.

## 18. Core Result Invariant

Teste central obrigatório:

```
same authoritative request
same source
same structural scope

MEMORY_DISABLED
versus
MEMORY_READ_ONLY
versus
MEMORY_READ_WRITE
```

Fresh AuditRoundResult deve ser semanticamente/byte-for-byte idêntico onde serialization determinística permitir.

Únicas diferenças permitidas:
- orchestration metadata;
- historical candidates;
- memory diagnostics;
- write-back metadata.

## 19. Aligned History Regression Test

Historical observation: aligned/revalidated.
Current source: regression reintroduz mismatch.

Esperado:
- Memory recupera aligned histórico;
- fresh audit detecta mismatch;
- fresh finding permanece rankeado;
- aligned histórico NÃO suprime nem reduz severidade.

## 20. Stale History Test

Historical confirmed: snapshot A.
Current: snapshot B.
Memory: STALE_CANDIDATE.
Fresh source: fixed/aligned.

Esperado:
- historical candidate aparece como contexto;
- fresh auditor produz aligned;
- nenhum finding atual;
- optional NOT_REPRODUCED lineage event após write-back.

## 21. Historical Confirmed Reproduced Test

Historical confirmed: snapshot A.
Current: snapshot B ou same snapshot.
Fresh source: bug ainda presente.

Esperado:
- historical candidate recuperado;
- fresh auditor independentemente produz mismatch;
- finding atual possui identidade própria;
- post-audit write pode produzir reconfirmation.

## 22. Path-Only Test

Historical: PATH_PROVEN_NO_COMPARABLE_CONTRACT.
Current: mesmo tipo de fluxo.

Esperado:
- Memory sugere path/symbols;
- fresh execution auditor roda;
- se continuar path-only: zero RankableFinding.
- Memory nunca promove path-only a actionable finding.

## 23. No-Candidate Fallback

Query sem candidate.

Esperado:
- plan histórico vazio;
- fresh audit normal;
- resultado idêntico ao MEMORY_DISABLED;
- post-write continua possível se fresh outcome elegível.

Isso é caminho normal, não erro.

## 24. Scope Safety

Testar:

Authoritative scope: `[a.py, b.py, c.py]`
Memory candidate sugere: `[a.py]`

A fresh audit continua recebendo: `[a.py, b.py, c.py]`

Nenhuma seleção histórica reduz o scope.

Se current caller explicitamente construir um scope menor antes da orchestration: isso é decisão do caller, não Memory.

## 25. Auditor Suggestion Safety

Memory pode sugerir auditor histórico.

Mas se caller já declarou auditor requests:
Memory não remove nem substitui requests.

Na V1: memory auditor suggestion = metadata apenas.
Não auto-adicionar auditor novo sem policy explícita.

## 26. CLI / User Entrypoint

Identificar o entrypoint operacional correto do Hermes.

Objetivo: o usuário deve conseguir usar Memory sem chamar manualmente módulos Python.

Projetar integração CLI mínima no comando `skill run` existente.

Possibilidades conceituais:

```
hermes-ops skill run mission-audit --project ... --mission ... --memory off|read|read-write --memory-store PATH
```

Ou flags equivalentes no comando operacional mais adequado.

NÃO criar um segundo CLI paralelo se já existe entrypoint apropriado.

Antes de alterar CLI: inspecionar contratos e testes atuais.
Manter backward compatibility.

## 27. Default Memory Mode

Decisão conservadora para V1 operacional: **default = MEMORY_DISABLED**.

Rationale: exige que o caller explicitamente habilite a Memory, garantindo que repository identity e store location sejam conhecidos/controlados.

READ_ONLY só como opt-in explícito.

Não escolher READ_WRITE como default nesta spec.

Registrar decisão e rationale na spec.

## 28. Memory Store Location

Não usar path do consumidor como identity.

Separar:
- store location
versus
- repository identity.

Escolher localização local estável compatível com Hermes, mas não inventar diretório global sem revisar convenções existentes.

Se não houver convenção clara: exigir `--memory-store PATH` ou configuração existente.

Não introduzir path absoluto de usuário em código.

## 29. Current Provenance

Orchestration deve construir/passar:
- repository identity;
- revision quando disponível;
- snapshot digest quando disponível;
- structural scope.

Não chamar rede.
Não exigir Git.

Se Git estiver disponível localmente: pode usar revisão somente através de abstraction já segura ou caller explícito.
Não transformar Git em requisito da Memory.

## 30. User-Visible Output

Relatório deve separar claramente:

```
HISTORICAL MEMORY
de
CURRENT AUDIT RESULT
```

Exemplo conceitual:

```
Historical context:
- 2 candidates
- 1 stale
- 1 revalidated
- requires fresh audit

Current audit:
- 1 confirmed finding
- fresh evidence refs ...
```

Não misturar os findings numa lista única.

## 31. JSON Contract

Serialização determinística.

Campos históricos e fresh precisam estar em namespaces distintos.

Não alterar JSON nativo da Audit Round.

Orchestration pode encapsulá-lo.

Exemplo conceitual:

```json
{
  "memory_context": ...,
  "audit_plan": ...,
  "fresh_audit": <existing AuditRoundResult serialization>,
  "memory_writeback": ...
}
```

## 32. Privacy

Reutilizar privacy gate HERMES-0028.

Não persistir:
- raw source;
- absolute paths;
- secrets;
- user machine paths;
- runtime objects.

CLI não deve imprimir native payload histórico inteiro por padrão.

Default disclosure: HEADER ou STRUCTURED.

## 33. Performance Bounds

Configurar:
- max memory candidates bounded.
- Não carregar canonical payload de todos.
- Usar progressive disclosure.
- Não fazer N fresh audits por candidate.

V1:
uma missão → um planejamento → uma fresh audit normal.

Memory não multiplica auditor runs automaticamente.

## 34. No Autonomy Creep

PROIBIDO:
- Memory escolher patch;
- Memory editar target;
- auto-fix;
- auto-commit;
- auto-expandir scope indefinidamente;
- executar target;
- chamar LLM externo;
- embeddings;
- background daemon;
- scheduled memory jobs.

Esta spec é orchestration assistida, não autonomia.

## 35. Acceptance Criteria

| ID | Criterion |
|---|---|
| **AC-01** | Memory disabled preserva fresh result. |
| **AC-02** | Memory read-only preserva fresh result. |
| **AC-03** | Memory read-write preserva fresh result. |
| **AC-04** | no candidate → fresh audit normal. |
| **AC-05** | historical confirmed não cria current finding. |
| **AC-06** | aligned histórico não suprime current mismatch. |
| **AC-07** | path-only histórico não vira finding. |
| **AC-08** | stale histórico continua exigindo fresh audit. |
| **AC-09** | revalidation hint sempre exige fresh audit. |
| **AC-10** | MemoryCandidate nunca entra em auditor input. |
| **AC-11** | Memory não reduz authoritative scope. |
| **AC-12** | Memory suggestion não remove auditor request. |
| **AC-13** | repository isolation permanece obrigatório. |
| **AC-14** | corrupt Memory não quebra fresh audit. |
| **AC-15** | unavailable Memory não quebra fresh audit. |
| **AC-16** | FTS unavailable não quebra fresh audit. |
| **AC-17** | post-write failure não invalida fresh result. |
| **AC-18** | confirmed fresh finding é elegível para write-back. |
| **AC-19** | failed auditor não vira semantic observation. |
| **AC-20** | aligned write só ocorre conforme revalidation policy. |
| **AC-21** | lineage reconfirmation é append-only. |
| **AC-22** | not-reproduced event não apaga histórico. |
| **AC-23** | orchestration JSON é determinístico. |
| **AC-24** | AuditRoundResult interno permanece inalterado. |
| **AC-25** | ranking HERMES-0017 não recebe historical severity. |
| **AC-26** | current finding IDs não dependem da Memory. |
| **AC-27** | fresh evidence refs não vêm da Memory. |
| **AC-28** | same source/request Memory ON/OFF mantém current ranking. |
| **AC-29** | store disabled não cria filesystem side effect desnecessário. |
| **AC-30** | privacy gate permanece ativo no write-back. |
| **AC-31** | candidate limit é bounded. |
| **AC-32** | progressive disclosure evita canonical eager loading. |
| **AC-33** | current context HERMES-0029 é usado em freshness. |
| **AC-34** | same-snapshot candidate continua apenas candidate. |
| **AC-35** | stale candidate não recebe evidence strength atual. |
| **AC-36** | CLI mantém backward compatibility. |
| **AC-37** | default memory mode não é READ_WRITE. |
| **AC-38** | target nunca é executado/importado pela orchestration. |
| **AC-39** | auditors permanecem semanticamente independentes. |
| **AC-40** | frozen core permanece sem semantic delta. |

## 36. TDD Order

1. Spec.
2. Orchestration frozen models (`models.py`).
3. Memory-disabled pass-through.
4. Read-only retrieval.
5. Plan/revalidation hint.
6. Fresh Audit Round invocation.
7. Core-result invariant.
8. Stale/aligned/path-only safety.
9. Failure optionality.
10. Post-audit write adapter.
11. Lineage events.
12. JSON determinism.
13. CLI integration.
14. Dogfood hermético.
15. Regression/full suite/build.

Não começar pelo CLI.

## 37. Dogfood Corpus

Usar fixtures herméticas já derivadas de:
- persistence wrong-store;
- state-effect mismatch;
- path-only;
- aligned revalidation.

Não acessar Lucre externo.

Testar missão nova com Memory pré-carregada.

Provar:
Memory encontra contexto → orchestration prepara investigation → fresh auditor conclui independentemente → write-back registra histórico novo quando permitido.

## 38. Operational Dogfood

Criar ao menos quatro cenários:
1. reproduced confirmed historical defect;
2. historical defect fixed;
3. historical aligned followed by regression;
4. historical path-only.

Para cada registrar:
- candidates;
- freshness;
- hints;
- authoritative request/scope;
- fresh result;
- memory writeback;
- lineage effect.

## 39. Memory OFF / ON Comparison

Para cada dogfood comparar:
Memory OFF versus Memory READ_ONLY

Fresh result: deve ser idêntico.

Memory READ_WRITE: fresh result também idêntico; somente store side effects mudam.

## 40. Anti-Hardcode

Produção não pode conter:
Lucre, OLT, Kumon, Trello, WhatsApp, historical SHA, benchmark ID, known historical state, absolute machine path.

Também verificar: Memory modules não importam consumer code.

## 41. Core Freeze Check

Ao final: verificar diff de:
- `audit_round.py`
- `finding_models.py`
- `finding_ranking.py`
- `execution_path*`
- `persistence_contract*`
- `state_guard_effect*`

Qualquer semantic delta inesperado: STOP.

Verdict: `HERMES_0030_BLOCKED_BY_FROZEN_CORE`

## 42. Focused Tests

Rodar:
- orchestration tests;
- memory tests;
- audit round;
- ranking;
- execution;
- persistence;
- state-effect;
- CLI relevante.

Registrar contagens.

## 43. Regression

Executar regressão ampla. Zero failed esperado.

## 44. Full Suite

Executar pytest completo.

Baseline: 824 passed, 11 skipped, 0 failed.

Registrar delta. Nenhum skip novo sem justificativa.

## 45. Build

Construir wheel + sdist. Confirmar módulos de orchestration e memory. Não publicar.

## 46. Spec Finalization

Somente depois de:
- generic TDD;
- fresh-result invariant;
- failure optionality;
- write-back safety;
- lineage;
- CLI;
- dogfood;
- regressions;
- full suite;
- build;
- anti-hardcode;
- frozen core intacto;

mudar: status: Implementado

## 47. Final Git Safety

Registrar:
- git branch --show-current
- git rev-parse HEAD
- git status --short
- git diff --check
- git diff --cached --name-only

Confirmar:
- branch igual;
- HEAD igual;
- staging vazio;
- nenhum commit;
- nenhum push;
- nenhum consumidor externo;
- nenhum target executado;
- worktree preexistente preservado.

Limpar somente temporários criados por ESTA missão quando permitido pela política.

## 48. Review Remediation Contract (Version 2)

The independent implementation review confirmed that version 1 remained
partial. Version 2 closes only those confirmed gaps and does not change the
frozen audit core.

### 48.1 Authoritative target

`MemoryAssistedAuditRequest` has an explicit `target: str | Path`. This is the
filesystem root consumed by controlled reading and Audit Round. It is never
derived from `RepositoryIdentity`, and it is never included in Memory canonical
identity. `repository_identity` remains the logical cross-run Memory identity.

### 48.2 Result and serialization

Historical comparison is retained as presentation metadata in
`HistoricalContext.comparison`. It never changes the fresh result. The official
`memory_assisted_audit_json()` serializer emits separate `memory_context`,
`audit_plan`, `fresh_audit`, and `memory_writeback` namespaces, embeds the
existing Audit Round JSON contract without changing it, and is deterministic
for identical inputs.

### 48.3 Post-audit write policy

Confirmed findings are adapted from the already-normalized and ranked fresh
result. Native path-only outcomes may be stored without creating a finding.
Aligned/no-finding outcomes are stored only when explicitly revalidating a
retrieved historical lineage. Operational limitations are stored only when the
backward-compatible `allow_operational_limitation_write` request flag is true.
Failed auditors are never semantic observations.

Lineage correlation uses the candidate lineage and canonical request identity,
symbols, paths, and auditor contract; it never uses summary text. Equivalent
confirmed observations receive `RECONFIRMED`; explicit aligned revalidation of
a confirmed lineage receives `NOT_REPRODUCED`. Both operations are append-only.

### 48.4 Failure and lifecycle contract

The orchestration snapshots Memory diagnostics after retrieval and after
write-back. A failed write is represented as attempted with a diagnostic and
does not invalidate the completed fresh result. `MemoryService` supports
explicit close/context-manager lifecycle so SQLite handles are released before
temporary directories are removed.

### 48.5 CLI contract

The existing `skill run` entrypoint accepts `--memory off|read|read-write` and
`--memory-store PATH`. The operational skill is `memory-assisted-audit`.
Default is `off`; active modes require an explicit store path. Filesystem target
and logical repository identity are separate inputs. Existing skill invocations
without Memory flags retain their prior behavior.

### 48.6 Remediation acceptance evidence required

AC-01 through AC-40 must be mapped to executable tests. Required evidence
includes a real hermetic filesystem target, byte-for-byte Audit Round JSON
equality for OFF/READ_ONLY/READ_WRITE, argument spies for the Memory boundary,
four hermetic dogfoods, complete optional-failure coverage, deterministic
orchestration JSON, CLI coverage, focused/regression/full-suite results, build
contents, anti-hardcode inspection, and a frozen-core diff check. This spec must
remain `Em implementação` until that evidence is green.

## 49. AC-01 through AC-40 Test Map

| Criterion | Executable evidence |
|---|---|
| AC-01, AC-02, AC-03 | `test_fresh_result_is_byte_identical_across_modes` |
| AC-04 | `test_no_candidate_is_normal_and_json_is_deterministic` |
| AC-05, AC-10 | `test_memory_objects_never_cross_fresh_boundary` and confirmed dogfood |
| AC-06 | `test_aligned_history_regression_does_not_suppress_finding` |
| AC-07 | `test_path_only_dogfood_stays_non_actionable_and_writes` |
| AC-08, AC-09 | `test_historical_fixed_dogfood_writes_not_reproduced` |
| AC-11, AC-12 | `test_authoritative_scope_and_requests_reach_round_unchanged` |
| AC-13 | `test_request_validation_and_defaults` plus HERMES-0028 repository-isolation tests |
| AC-14, AC-15, AC-16 | `test_memory_read_failures_preserve_fresh_audit` |
| AC-17 | `test_write_failure_is_attempted_and_fresh_result_survives` |
| AC-18 | confirmed-reproduced and path-only dogfoods |
| AC-19 | `test_failed_auditor_is_not_written` |
| AC-20 | fixed dogfood and operational-limitation opt-in test |
| AC-21, AC-22 | confirmed-reproduced and historical-fixed lineage assertions |
| AC-23 | orchestration JSON and CLI determinism tests |
| AC-24 | real-target and byte-identical invariant tests |
| AC-25, AC-26 | aligned-history regression and boundary tests |
| AC-27 | boundary spy plus fresh finding evidence assertions |
| AC-28 | all four dogfood mode comparisons |
| AC-29 | disabled-mode real-target test; no service/store is constructed |
| AC-30 | operational opt-in test plus HERMES-0028 privacy tests |
| AC-31 | request validation plus HERMES-0028 retrieval limit tests |
| AC-32 | candidate/header retrieval followed only by selected hint expansion in dogfoods |
| AC-33, AC-35 | stale confirmed dogfood with explicit current context |
| AC-34 | HERMES-0029 same-snapshot freshness lifecycle tests and boundary test |
| AC-36, AC-37 | three CLI tests covering compatibility/default/read/read-write/errors |
| AC-38 | real-target controlled Audit Round tests and controlled-reader regression suite |
| AC-39 | Memory boundary spy and existing Audit Round isolation tests |
| AC-40 | No production test mutates Git. Validation is the required read-only frozen-surface diff and full frozen-core regression suite because repository change attribution is not a runtime behavior. |

## 50. Version 2 Validation Evidence

- TDD remediation: the new real-target, lifecycle, lineage, path-only and CLI
  tests first exposed four concrete failures (missing canonical disclosure
  import, native locator conversion, limitation-kind assertion, and CLI error
  import); each was corrected before the green run.
- HERMES-0030 focused file: `22 passed` in `1.63s`.
- Focused orchestration/Memory/frozen-core/CLI regression: `338 passed,
  1 skipped` in `41.15s`.
- Full suite, with `--basetemp` under the system temporary directory and outside
  the repository: `846 passed, 11 skipped, 0 failed` in `86.64s`.
- The four hermetic dogfoods prove reproduced confirmed, fixed/not reproduced,
  aligned-history regression, and path-only behavior. Their OFF/READ_ONLY/
  READ_WRITE fresh Audit Round JSON is byte-for-byte identical.
- SQLite lifecycle test closes the service and then renames and deletes the
  database successfully on Windows.
- Wheel and sdist build succeeded and both contain all
  `hermes_ops/orchestration/*` and `hermes_ops/memory/*` modules.
- Anti-hardcode inspection found no consumer name, machine path, historical SHA
  or benchmark identifier in HERMES-0030 production code.
- No frozen-core file was edited by this remediation. The tracked
  `code_audit.py` modification was present in base provenance before work began;
  the remaining frozen surfaces retain their preexisting untracked state.

## 51. Native Payload Privacy Remediation

Operational dogfood found that orchestration-generated confirmed observations
persisted the native `CodeAuditFinding` domain payload, including its literal
`evidence` source line. This violated `STORE_STRUCTURAL_REFERENCES_OVER_RAW_CONTENT`
even though the field was not named `raw_source`.

For all new orchestration writes, Memory V1 therefore uses a closed structural
payload and never persists a complete native auditor payload. The allowed
payload is limited to auditor/finding identity, bounded enum/code metadata,
historical severity and reachability, relative evidence references, symbols,
relative paths, limitations, and classification/outcome codes. Raw summaries,
source evidence text, source lines/blocks, absolute paths, secret-like fields,
unknown nested fields, and runtime objects are prohibited.

Sanitization occurs in the Memory adapters before `payload_digest` and
`observation_id` are calculated. Consequently, those values reflect the exact
sanitized payload that is persisted. Changing an unsafe historical observation
ID is an intentional privacy correction. `lineage_id` remains stable because it
does not depend on native payload.

Existing stores are append-only compatibility data: this remediation neither
rewrites nor deletes old observations. HEADER and STRUCTURED disclosure remain
safe by construction; CANONICAL disclosure of an older unsafe record remains a
documented future migration/privacy debt. All new confirmed, path-only, aligned,
and operational-limitation writes must pass the closed sanitizer.

## 52. Native Payload Privacy Validation Evidence

- RED: `test_new_canonical_observation_never_persists_source_literal` failed
  before the remediation because CANONICAL JSON contained
  `return eval(payload)`; the isolated RED run was `1 failed` in `0.47s`.
- GREEN: the same isolated test passed in `0.30s`. Privacy plus orchestration
  coverage passed `33` tests in `1.99s`; focused Memory, orchestration, audit,
  and ranking coverage passed `128` tests in `5.49s`.
- The dedicated privacy matrix covers exact and multiline source exclusion,
  structural metadata retention, relative evidence paths, sanitizer rejection
  of absolute paths, secret-like and unknown nested fields, runtime objects,
  unsafe code-like identifiers, digest correctness, deterministic observation
  and lineage identities, idempotent duplicate writes, all four disclosure
  levels, and retrieval by finding kind, path, and auditor.
- The broader relevant regression run passed `349` tests with `1` expected
  external-clone dogfood skip in `43.68s`.
- The full suite passed `857` tests with `11` expected skips and no failures in
  `86.87s`, using a base temporary directory outside the repository.
- Seven real CLI rounds covered OFF, READ_WRITE, READ_ONLY, fixed revalidation,
  regression, and idempotent repeated write. Fresh buggy hashes were identical;
  fixed READ_ONLY and READ_WRITE hashes were identical. The resulting store had
  two observations, one lineage, and `OBSERVED`, `OBSERVED`, and
  `NOT_REPRODUCED` events. Historical aligned context did not suppress the
  reintroduced fresh finding.
- Canonical payload inspection found no exact source line, multiline source,
  `eval(payload)`, target/store absolute path, or secret marker. Structural
  finding identity, severity, reachability, auditor, evidence reference, and
  relative path remained available for retrieval and disclosure.
- Wheel and sdist builds succeeded and contain the Memory and orchestration
  packages. Production anti-hardcode inspection returned no matches.
- This remediation did not edit a frozen-core file. The tracked
  `src/hermes_ops/skills/code_audit.py` diff was present in base provenance and
  remains preserved.
