---
spec_id: HERMES-0016
title: Alinhamento do schema MissionEvidencePack com analysis.loader
version: 1
status: implementado
date: 2026-08-20
depends_on:
  - HERMES-0010
  - HERMES-0014
---

# HERMES-0016 — Alinhamento do schema MissionEvidencePack com analysis.loader

## 1. Contexto

A HERMES-0014 acrescentou `structural_scope` ao `MissionEvidencePack` com
default vazio, mantendo `schema_version: 1`. A serialização por dataclass passou
a emitir o campo, mas o consumidor do Analysis Pack continuou validando a lista
raiz anterior.

## 2. Problema Confirmado

`tests.analysis_helpers.save_pack` usa `asdict`, que inclui
`structural_scope`. `analysis.loader.parse_evidence_pack` compara exatamente as
chaves recebidas com uma lista manual que não contém o campo e rejeita um pack
produzido pelo modelo atual como `ANALYSIS_PACK_INVALID`.

## 3. Explicação em Linguagem Natural

O produtor e o consumidor devem concordar sobre os campos do mesmo pacote. O
loader passará a obter do próprio modelo quais campos existem e quais possuem
default, preservando validação estrita sem aceitar propriedades arbitrárias.

## 4. Comportamento Atual

Um `MissionEvidencePack` atual serializado é rejeitado antes da reconstrução.
O loader também não repassa `structural_scope` ao construir o modelo.

## 5. Comportamento Desejado

- Pack atual com `structural_scope` é aceito e preservado integralmente.
- Pack legado sem o campo continua válido e recebe o default vazio documentado.
- Campo desconhecido continua inválido.
- Carregamentos repetidos são determinísticos.

## 6. Fora do Escopo

- Alterar semântica, código ou status da HERMES-0015.
- Mudar `schema_version`, o Analysis Pack resultante ou o structural scope.
- Relaxar validação de campos aninhados ou criar framework de schemas.

## 7. Invariantes e Regras de Segurança

- O loader lê somente arquivo regular direto dentro dos limites existentes.
- Chaves desconhecidas são rejeitadas.
- Campos obrigatórios ausentes são rejeitados.
- Campos com default no modelo podem estar ausentes e usam exatamente o default.
- Ordem e conteúdo de `structural_scope` não são transformados.
- Nenhuma rede, Git, subprocesso ou escrita externa é introduzida.

## 8. Entradas e Saídas

Entrada: JSON do `MissionEvidencePack` schema 1, com ou sem campos opcionais
declarados pelo modelo. Saída: `MissionEvidencePack` imutável reconstruído ou
`ANALYSIS_PACK_INVALID`.

## 9. Pseudocódigo Independente de Linguagem

```text
OBTER do modelo a lista de todos os campos
SE a entrada não for objeto: REJEITAR
SE existir chave que não pertence ao modelo: REJEITAR
SE faltar campo do modelo que não possui default: REJEITAR
PARA cada campo opcional ausente: USAR o default declarado pelo modelo
VALIDAR e reconstruir todos os valores existentes
PRESERVAR structural_scope na mesma ordem e sem alterar seus textos
```

## 10. Fluxo Principal

1. Derivar campos obrigatórios e opcionais de `MissionEvidencePack`.
2. Validar o conjunto de chaves recebido contra esse contrato.
3. Validar `structural_scope` como array de strings quando presente.
4. Construir o modelo com argumento nomeado e default vazio quando ausente.
5. Prosseguir para o Analysis Pack sem mudar seu comportamento.

## 11. Casos de Erro e Limites

| Situação | Resultado |
|---|---|
| Campo obrigatório ausente | `ANALYSIS_PACK_INVALID` |
| Campo desconhecido | `ANALYSIS_PACK_INVALID` |
| `structural_scope` não é array de strings | `ANALYSIS_PACK_INVALID` |
| Campo opcional ausente | default declarado pelo modelo |

## 12. Critérios de Aceitação

- **AC-01 — Contract alignment:** pack válido com `structural_scope` é aceito.
- **AC-02 — Preservation:** o valor é preservado no modelo carregado.
- **AC-03 — Determinism:** serialização e carregamento repetidos são estáveis.
- **AC-04 — Validation remains strict:** campo desconhecido é rejeitado.
- **AC-05 — Backward compatibility:** pack sem `structural_scope` é aceito com `()` conforme HERMES-0014.
- **AC-06 — Structural scope semantics:** ordem e textos não são transformados.
- **AC-07 — Existing analysis behavior:** testes existentes do Analysis Pack permanecem verdes.
- **AC-08 — No HERMES-0015 behavior change:** testes da execution-path-review permanecem verdes sem mudança semântica.

## 13. Plano de Testes

`tests/test_analysis_schema_alignment.py` cobre AC-01 a AC-06. As suítes
`test_analysis_*`, `test_mission_audit.py` e `test_execution_path_review.py`
cobrem AC-07 e AC-08, seguidas pela suíte completa.

## 14. Arquivos Provavelmente Afetados

- `src/hermes_ops/analysis/loader.py`
- `tests/test_analysis_schema_alignment.py`
- `docs/hermes/specs/HERMES-0016-analysis-schema-alignment.md`

## 15. Riscos Conhecidos

Derivar apenas o contrato raiz do dataclass reduz a duplicação que causou a
falha, mas a validação dos objetos aninhados continua manual e pode exigir uma
evolução separada se esses modelos mudarem futuramente.

## Evidências da Implementação

| Evidência | Resultado |
|---|---|
| TDD específico antes da correção | `2 failed, 2 passed` |
| Testes focados após a correção | `15 passed` |
| Regressões adjacentes | `180 passed, 1 skipped` |
| Suíte completa | `610 passed, 2 skipped` |
| `git diff --check` | sem erros |
| Plataforma | Windows, Python 3.13.13 |
