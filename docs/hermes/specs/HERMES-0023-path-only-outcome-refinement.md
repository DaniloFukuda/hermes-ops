---
spec_id: HERMES-0023
title: Path-Only Outcome Refinement
version: 1
status: Implementado
date: 2026-08-21
depends_on: [HERMES-0017, HERMES-0018, HERMES-0019, HERMES-0020, HERMES-0022]
---

# HERMES-0023 — Path-Only Outcome Refinement

## 1. Contexto

O dogfood projeto consumidor provou um path Python real, mas retornou evidência insuficiente
porque não havia domínio do producer nem precondition Python no consumer.

## 2. Problema confirmado

Path comprovado é hoje misturado com falha de descoberta semântica. Múltiplos
returns sem success mappings também descartam origins sintáticas observáveis.

## 3. Explicação em linguagem natural

Quando o Hermes prova quem produziu, transportou e recebeu um valor, mas não há
contratos comparáveis, deve relatar essa conectividade sem chamá-la de ausência
de mismatch e sem criar finding.

## 4. Comportamento atual

Um único trace é preservado no campo path, porém a classificação continua
`INSUFFICIENT_EVIDENCE`, os edge refs ficam vazios e a Audit Round degrada.

## 5. Comportamento desejado

Adicionar `PATH_PROVEN_NO_COMPARABLE_CONTRACT`, preservar origins variantes e
edge refs, refinar diagnostics, manter o outcome non-rankable e mapear sua
execução para completed/no-findings.

## 6. Fora do escopo

Novos domains/preconditions, SQL na execution lens, compartilhamento de facts,
cross-process, symbolic execution, ranking/severity changes e findings path-only.

## 7. Invariantes e segurança

1. Path-only requer exatamente um trace.
2. Path-only não é `NO_MISMATCH`.
3. Origin nunca é promovida a domain.
4. SQL predicate não é Python precondition.
5. Zero/múltiplos paths permanecem insufficient.
6. Persistence permanece independente.
7. Resultados e ordering são determinísticos.

## 8. Entradas e saídas

Entradas públicas não mudam. `ExecutionPathReport` ganha apenas um novo valor de
classification; executable path, diagnostics e evidence refs carregam a prova.

## 9. Pseudocódigo independente de linguagem

```text
descobrir definitions e traces
se trace count não for um: manter insufficient
extrair origins de todos os returns, mesmo sem success marker
não criar domain se variantes não possuem domínio comum
extrair consumer contract
se consumer não possui candidato a guard/precondition:
    retornar path-proven-no-comparable-contract
    anexar edge refs e diagnostics informativos
se consumer possui candidato opaco que não pode ser demonstrado:
    manter insufficient
se existe contrato em um lado mas falta no outro:
    manter insufficient
se ambos são comparáveis:
    usar a matriz semântica existente
```

## 10. Fluxo principal

Parse → definitions → único trace → producer evidence → consumer requirement →
path-only ou comparação existente → normalização vazia → Audit Round completed.

## 11. Erros, limites e fronteiras

Guard opaco continua precondition não descoberta. Sem path ou path ambíguo não
há path-only. Calls como `int(...)` são apenas origins. SQL não é interpretado.

## 12. Critérios de aceitação

- **AC-01:** path único sem contratos produz path-only.
- **AC-02:** path-only não produz finding.
- **AC-03:** path-only não é no-mismatch.
- **AC-04:** executable path é preservado.
- **AC-05:** edge evidence refs são preservadas.
- **AC-06:** multiple origins são preservadas.
- **AC-07:** `int(existing[id])` permanece call origin.
- **AC-08:** `int(cursor.lastrowid)` permanece call origin.
- **AC-09:** lastrowid não cria domain/truthiness.
- **AC-10:** lastrowid não cria persistence guarantee.
- **AC-11:** consumer sem guard recebe diagnostic próprio.
- **AC-12:** SQL predicate não vira precondition.
- **AC-13:** consumer truthy + producer unknown continua insufficient.
- **AC-14:** ambos truthy continuam no-mismatch.
- **AC-15:** literal mismatch continua confirmed.
- **AC-16:** zero paths permanece insufficient.
- **AC-17:** múltiplos paths permanecem insufficient.
- **AC-18:** path-only é non-rankable.
- **AC-19:** Audit Round usa completed/no-findings.
- **AC-20:** path-only não degrada round status.
- **AC-21:** persistence continua independente.
- **AC-22:** determinismo é preservado.
- **AC-23:** target nunca é executado.
- **AC-24:** projeto consumidor real produz path-only.

## 13. Plano de testes

Novo teste cobre path-only, variants, refs, diagnostics e negativos. Suites de
execution, ranking, Audit Round e persistence cobrem integrações e regressões.

## 14. Arquivos provavelmente afetados

Esta spec, execution path models/review, finding ranking, Audit Round e testes.

## 15. Riscos conhecidos

Classificar guard opaco como ausência de contrato, perder refs de edges, tornar
path-only rankeável ou degradar a rodada são os principais riscos.

## 16. Evidência de validação

- RED inicial: o primeiro teste falhou porque a nova enumeração ainda não existia.
- Testes focados: `101 passed`.
- Regressões relacionadas: `101 passed, 1 skipped`.
- Suíte completa: `691 passed, 11 skipped`.
- Build: wheel e sdist construídos com sucesso.
- Dogfood projeto consumidor: path-only, caminho real esperado, dois diagnostics, quatro
  evidence refs e zero findings.
- Audit Round dogfood: auditor `COMPLETED_NO_FINDINGS`, rodada `COMPLETED` e
  zero findings rankeados.
