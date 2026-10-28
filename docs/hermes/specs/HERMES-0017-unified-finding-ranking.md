---
spec_id: HERMES-0017
title: Unified Finding Contract e Deterministic Finding Ranking
version: 1
status: Implementado
date: 2026-08-20
depends_on:
  - HERMES-0015
---

# HERMES-0017 — Unified Finding Contract e Deterministic Finding Ranking

## 1. Contexto

`code-audit` e `execution-path-review` já produzem findings imutáveis, porém
com contratos locais. Não existe representação mínima comum nem ordenação
comparativa independente da ordem de entrada.

## 2. Problema Confirmado

`CodeAuditFinding` e `ExecutionPathFinding` compartilham severidade, resumo e
evidências, mas classificações e payloads têm semânticas próprias. O contrato
comum atual, `SkillExecutionResult`, transporta qualquer evidência e não
distingue findings acionáveis de summaries ou resultados insuficientes.

## 3. Explicação em Linguagem Natural

Cada auditor continuará falando sua própria linguagem. Um normalizer fechado
traduzirá apenas os sinais comparáveis para um envelope pequeno; o conteúdo
original ficará preservado e opaco. Um ranker puro ordenará esses envelopes por
uma regra lexicográfica documentada, sem pesos, IA ou nova leitura do projeto.

## 4. Comportamento Atual

`code-audit` ordena findings por localização. `execution-path-review` produz no
máximo seu conjunto local. Nenhum componente reúne ou prioriza findings entre
auditores.

## 5. Comportamento Desejado

Findings acionáveis das duas skills podem ser normalizados, reunidos e
ordenados por reachability, força de evidência, severidade, skill e identidade.
O relatório expõe `top_finding` ou `None` e a sequência completa determinística.

## 6. Fora do Escopo

- Novos auditores, skill pública, CLI ou executor novo.
- LLM judge, fix automático, pesos ou score numérico.
- Impacto financeiro, blast radius ou taxonomia de impacto.
- Deduplicação semântica e inferência de produção.
- Alteração de classifications, heurísticas ou leitura das skills existentes.
- Transformar mission-audit ou `AnalysisClaim` automaticamente em finding.

## 7. Invariantes e Regras de Segurança

- Modelos imutáveis e serialização canônica.
- Somente paths relativos seguros em `EvidenceRef`.
- Normalizers fechados; valores locais desconhecidos falham fechados.
- `domain_payload` é congelado e nunca participa da chave de ranking.
- Ranking não lê filesystem, repositório, AST, rede ou ambiente.
- `UNKNOWN` significa ausência de prova de reachability; `NOT_REACHABLE` não existe.
- Entrada permutada produz relatório idêntico.

## 8. Entradas e Saídas

Entradas: `CodeAuditFinding`, `ExecutionPathReport` e/ou envelopes já
normalizados. Saída: `RankedFindingReport` com `top_finding` e
`ordered_findings`. Resultados não acionáveis normalizam para sequência vazia.

## 9. Pseudocódigo Independente de Linguagem

```text
PARA cada finding de uma skill conhecida:
    VALIDAR o contrato local exato
    TRADUZIR severity e força da evidência pela tabela fechada
    CONFIRMAR reachability somente quando o contrato local traz a prova exigida
    CONVERTER localizações em referências relativas canônicas
    GERAR identidade com digest de campos estáveis, sem relógio ou aleatoriedade
    PRESERVAR o payload original congelado

REMOVER duplicatas exatamente idênticas; BLOQUEAR colisões de identidade
ORDENAR por reachability, evidência, severity, source_skill e finding_id
RETORNAR primeiro item como top_finding; sem itens, RETORNAR None
```

## 10. Fluxo Principal

1. Normalizar separadamente cada tipo de finding.
2. Excluir `NO_MISMATCH` e `INSUFFICIENT_EVIDENCE`.
3. Validar unicidade dos IDs.
4. Ordenar com chave fechada.
5. Construir relatório imutável e serializá-lo canonicamente.

## 11. Casos de Erro e Limites

| Situação | Resultado |
|---|---|
| Tipo/classification/severity desconhecido | `FINDING_NORMALIZATION_INVALID` |
| Path absoluto, traversal ou locator inválido | `FINDING_NORMALIZATION_INVALID` |
| Mesmo ID para envelopes diferentes | `FINDING_ID_COLLISION` |
| Nenhum finding acionável | relatório vazio, sem erro |

## 12. Critérios de Aceitação

- **AC-01:** code-audit `OBSERVED` normaliza para evidência `CONFIRMED`.
- **AC-02:** code-audit `HYPOTHESIS` normaliza para `PARTIAL`.
- **AC-03:** mismatch confirmado com prova de caminho recebe reachability confirmada.
- **AC-04:** mismatch potencial recebe `PARTIAL` e reachability `UNKNOWN`.
- **AC-05:** `NO_MISMATCH` não gera envelope.
- **AC-06:** `INSUFFICIENT_EVIDENCE` não gera envelope.
- **AC-07:** severity desconhecida falha fechada.
- **AC-08:** classification desconhecida falha fechada.
- **AC-09:** finding ID é estável e independente da ordem.
- **AC-10:** mesma entrada produz JSON idêntico.
- **AC-11:** ranking segue reachability, evidência e severity nessa ordem.
- **AC-12:** source e ID resolvem empates deterministicamente.
- **AC-13:** permutações produzem o mesmo relatório.
- **AC-14:** ranker não usa payload local.
- **AC-15:** EvidenceRef insegura é rejeitada.
- **AC-16:** ranking não realiza leitura adicional.
- **AC-17:** relatório vazio possui `top_finding=None`.
- **AC-18:** contratos e semântica das skills existentes permanecem iguais.

## 13. Plano de Testes

`tests/test_finding_ranking.py` cobre AC-01 a AC-17 com normalização, matriz de
ranking, permutações, serialização, paths e ausência de I/O. As regressões de
`code-audit` e `execution-path-review` cobrem AC-18.

## 14. Arquivos Provavelmente Afetados

- `src/hermes_ops/skills/finding_models.py`
- `src/hermes_ops/skills/finding_ranking.py`
- `src/hermes_ops/skills/__init__.py`
- `tests/test_finding_ranking.py`
- `docs/hermes/specs/HERMES-0017-unified-finding-ranking.md`

Catálogo, executor e CLI não devem mudar: esta capacidade é composição pura.

## 15. Riscos Conhecidos

O ID é estável para a identidade canônica documentada, mas não representa causa
raiz. Reachability permanece `UNKNOWN` para code-audit e findings potenciais.
O ranking v1 expressa prioridade por sinais comprovados, não impacto total em
produção.

## Evidências da Implementação

| Evidência | Resultado |
|---|---|
| Primeiro RED | `ModuleNotFoundError: hermes_ops.skills.finding_models` |
| RED de ordenação total de EvidenceRef | `TypeError` entre `None` e inteiro |
| RED de export do shared kernel | `AttributeError: RankableFinding` |
| Testes focados | `20 passed` |
| Regressões adjacentes | `223 passed, 1 skipped` |
| Suíte completa | `630 passed, 2 skipped` |
| `git diff --check` | sem erros |
| Plataforma | Windows, Python 3.13.13 |
