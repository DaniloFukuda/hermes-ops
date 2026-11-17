+++
schema_version = 1
id = "HERMES-0035"
title = "Limites seguros para missões textuais"
status = "Implementado"
owners = ["Danilo"]
created = "2026-10-30"
updated = "2026-10-30"
supersedes = []
related = ["HERMES-0009", "HERMES-0014"]

[[acceptance_criteria]]
id = "AC-01"
test = "tests/test_mission_audit.py::test_mission_character_limit_accepts_3000_and_rejects_3001"

[[acceptance_criteria]]
id = "AC-02"
test = "tests/test_mission_audit.py::test_mission_base_term_limit_accepts_96_and_rejects_97"

[[acceptance_criteria]]
id = "AC-03"
test = "tests/test_mission_audit.py::test_accent_aliases_do_not_consume_base_term_limit"

[[acceptance_criteria]]
id = "AC-04"
test = "tests/test_mission_audit.py::test_selection_terms_have_an_absolute_192_item_limit"

[[acceptance_criteria]]
id = "AC-05"
test = "tests/test_mission_audit.py::test_mission_limit_error_codes_remain_stable"

[[acceptance_criteria]]
id = "AC-06"
test = "tests/test_mission_audit.py::test_mission_term_limit_keeps_cli_exit_code_two"

[[acceptance_criteria]]
id = "AC-07"
test = "tests/test_mission_audit.py::test_short_mission_normalization_remains_unchanged"
+++

# HERMES-0035 - Limites seguros para missões textuais

## 1. Contexto

O comportamento implementado de `mission-audit` aceita uma missão normalizada
de até 500 caracteres e rejeita mais de 24 `selection_terms`. Aliases sem
acento são contados junto com termos escritos pelo operador. Missões legítimas
e detalhadas podem, por isso, ser recusadas antes da coleta de evidência.

A HERMES-0009 permanece `Rascunho` e não deve ser transformada
retroativamente em especificação implementada. Esta HERMES-0035 registra uma
alteração controlada do comportamento que existe no código e nos testes atuais.

## 2. Problema confirmado

O teto de 500 caracteres é insuficiente para missões que descrevem fronteiras,
invariantes e perguntas de auditoria. O teto atual de 24 mistura termos-base
com aliases gerados pelo próprio Hermes, fazendo uma palavra acentuada consumir
até duas posições. O resultado é `MISSION_TERM_LIMIT_EXCEEDED` para entradas
humanas razoáveis.

## 3. Explicação em linguagem simples

O operador poderá escrever uma missão maior, mas ainda limitada. O Hermes
contará separadamente as palavras significativas fornecidas pelo operador e os
aliases sem acento criados para comparação. Entradas excessivas continuam
falhando, sem truncamento silencioso.

## 4. Comportamento atual

- missão normalizada: de 3 a 500 caracteres;
- no máximo 24 `selection_terms`, incluindo aliases;
- excesso de tamanho: `SKILL_EXECUTION_INVALID`, exit code 2;
- excesso de termos: `MISSION_TERM_LIMIT_EXCEEDED`, exit code 2;
- nenhuma parte da missão ou dos termos é truncada.

## 5. Comportamento desejado

- missão normalizada: de 3 a 3000 caracteres;
- no máximo 96 termos-base únicos, em ordem de primeira ocorrência;
- aliases sem acento não consomem o teto de 96 termos-base;
- no máximo 192 `selection_terms` totais, incluindo aliases;
- acima de qualquer teto, falhar antes da coleta de evidência;
- preservar códigos de erro, exit codes, normalização e comportamento de
  missões que já eram aceitas.

## 6. Fora de escopo

- mudar stopwords, tokenização, stemming, tradução ou sinônimos;
- alterar ranking, completude, leitura de fontes ou tamanho do Evidence Pack;
- alterar `execution-path-review`, memória ou outros comandos;
- modificar o status, decisões ou papel histórico da HERMES-0009;
- introduzir truncamento, amostragem ou descarte de termos.

## 7. Invariantes e regras de segurança

1. NUL e caracteres de controle continuam rejeitados.
2. O tamanho é medido depois de NFKC e colapso de whitespace.
3. Termos-base são deduplicados deterministicamente.
4. Aliases são derivados somente pela remoção de acento já existente.
5. Nenhum limite pode ser contornado por aliases.
6. Excesso falha fechado e não produz Evidence Pack parcial.
7. Códigos de erro e exit codes públicos permanecem estáveis.
8. Nenhuma escrita, rede, subprocesso ou execução de código do TARGET é criada.

## 8. Entradas e saídas

Entrada: o texto de `--mission` ou o valor passado diretamente a
`normalize_mission()`/`build_evidence_pack()`.

Saída válida: missão normalizada e tupla ordenada de `SelectionTerm`.

Saída inválida: `SkillExecutionError` com `SKILL_EXECUTION_INVALID` para
tamanho, ou `MISSION_TERM_LIMIT_EXCEEDED` para qualquer teto de termos.

## 9. Pseudocódigo independente de linguagem

```text
normalizar Unicode e whitespace da missão
se tamanho não estiver entre 3 e 3000:
    falhar com SKILL_EXECUTION_INVALID

extrair tokens e remover stopwords pelas regras existentes
deduplicar somente os termos-base, preservando a primeira ocorrência
se houver mais de 96 termos-base:
    falhar com MISSION_TERM_LIMIT_EXCEEDED

para cada termo-base, em ordem:
    adicionar o termo-base uma única vez
    gerar o alias sem acento pelas regras existentes
    adicionar o alias somente se for diferente e ainda não existir

se houver mais de 192 termos totais:
    falhar com MISSION_TERM_LIMIT_EXCEEDED

retornar todos os termos; nunca truncar
```

## 10. Fluxo principal

1. Validar o tipo e caracteres da missão.
2. Normalizar NFKC e whitespace.
3. Validar o teto de 3000 caracteres.
4. Extrair e deduplicar termos-base.
5. Validar o teto de 96 termos-base.
6. Gerar e deduplicar aliases.
7. Validar o teto absoluto de 192 itens.
8. Prosseguir pelo fluxo existente do `mission-audit`.

## 11. Erros e fronteiras

| Condição | Código | Exit |
|---|---|---:|
| menos de 3 ou mais de 3000 caracteres | `SKILL_EXECUTION_INVALID` | 2 |
| mais de 96 termos-base únicos | `MISSION_TERM_LIMIT_EXCEEDED` | 2 |
| mais de 192 termos totais | `MISSION_TERM_LIMIT_EXCEEDED` | 2 |
| missão curta anteriormente válida | sem erro | inalterado |

Os tetos são inclusivos: 3000, 96 e 192 são aceitos.

## 12. Critérios de aceitação

- **AC-01:** 3000 caracteres normalizados são aceitos; 3001 são rejeitados.
- **AC-02:** 96 termos-base únicos são aceitos; 97 são rejeitados.
- **AC-03:** aliases não contam contra o teto de termos-base.
- **AC-04:** a coleção final nunca ultrapassa 192 itens e não é truncada.
- **AC-05:** tamanho e termos conservam seus códigos públicos anteriores.
- **AC-06:** excesso de termos continua produzindo exit code 2 na CLI.
- **AC-07:** missões curtas conservam texto, termos, ordem e provenance.

## 13. Plano de testes

Adicionar testes de fronteira em `tests/test_mission_audit.py`, incluindo um
isolamento do teto absoluto com o teto de termos-base controlado no teste.
Executar os testes focados de missão/CLI, a regressão de skills relacionadas e
a suíte completa.

## 14. Arquivos provavelmente afetados

- `src/hermes_ops/skills/mission_audit.py`;
- `tests/test_mission_audit.py`;
- `docs/hermes/specs/HERMES-0035-mission-input-bounds.md`.

## 15. Riscos conhecidos

- mais termos aumentam o custo de comparação sobre o inventário de fontes;
- Evidence Packs podem conter mais `selection_terms` e crescer;
- missões longas podem introduzir sinais pouco específicos e reduzir precisão;
- o teto total de 192 é atualmente redundante no caso comum, pois cada
  termo-base gera no máximo um alias, mas permanece como defesa independente;
- testes de desempenho não substituem os limites estruturais já existentes.

## 16. Evidência de validação

Validação executada em 2026-10-30:

- contrato focado de missão: `28 passed`;
- regressão relevante de CLI, execução, análise, memória e execution path:
  `129 passed, 1 skipped`;
- suíte completa: `955 passed, 11 skipped`;
- os skips são fixtures portáteis preexistentes, principalmente symlinks sem
  privilégio de criação no Windows e dogfooding externo explícito.
