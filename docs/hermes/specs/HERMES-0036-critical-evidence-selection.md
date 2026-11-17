+++
schema_version = 1
id = "HERMES-0036"
title = "Seleção crítica de evidências do mission-audit"
status = "Implementado"
owners = ["Danilo"]
created = "2026-11-16"
updated = "2026-11-16"
supersedes = []
related = ["HERMES-0009", "HERMES-0014", "HERMES-0035"]
+++

# HERMES-0036 — Seleção crítica de evidências do mission-audit

## 1. Contexto

O `mission-audit` atualmente preserva limites seguros de arquivos, regiões,
símbolos, relacionamentos e testes, mas pode truncar regiões lexicais antes de
priorizar funções e testes críticos. Uma função localizada depois das primeiras
12 ocorrências de termos em um arquivo pode não chegar ao Evidence Pack,
mesmo quando seu nome é um termo central da missão.

Essa lacuna foi observada em auditorias com escopo estrutural: a seleção
atingiu `MAX_REGIONS=300`, enquanto regiões tardias de executor, store,
migração e testes de recovery ficaram fora do pacote selecionado.

## 2. Objetivo

Garantir que funções, símbolos, testes e regiões de relacionamento diretamente
ligados aos termos centrais recebam prioridade dentro dos limites existentes,
sem converter evidência omitida em aprovação.

## 3. Fora do escopo

- aumentar `MAX_REGIONS_PER_FILE`, `MAX_REGIONS` ou outros caps;
- remover `CAP_OMISSION` ou `SELECTION_CAP_REACHED`;
- alterar critérios oficiais de suficiência;
- adicionar stemming, tradução ou sinônimos à seleção lexical;
- executar código, provider, rede ou subprocesso do TARGET;
- alterar a semântica de `--include-path`;
- substituir a verificação externa de identidade Git do projeto auditado.

## 4. Definições

### 4.1 Candidato lexical redundante

Região produzida por ocorrência de termo em comentário, docstring, import ou
código não crítico, quando não é necessária para cobrir um símbolo, teste,
relacionamento ou termo central ainda sem evidência.

Candidatos redundantes podem ser descartados dentro dos caps sem gerar uma
falha adicional, desde que nenhuma evidência crítica seja perdida.

### 4.2 Evidência crítica necessária

Região que representa pelo menos uma destas condições:

1. definição de função ou classe cujo nome corresponde a termo central da missão;
2. definição de teste cujo nome corresponde a termo central ou cenário requerido;
3. linha de relacionamento estrutural necessária para materializar uma relação;
4. região ativa que é a única evidência selecionável de um termo central;
5. região explicitamente protegida por uma regra de segurança do Evidence Pack.

### 4.3 Relacionamento sem evidência

`EvidenceRelationship` cujo `evidence_region` não está materializado em uma
região selecionada válida. Esse relacionamento não pode ser tratado como
comprovado e deve contribuir para a insuficiência do pacote.

### 4.4 Termo central sem cobertura

Termo originado diretamente da missão, e não apenas de alias, cuja contagem
de ocorrência permanece zero na superfície autorizada. Deve continuar gerando
`UNCOVERED_CENTRAL_TERMS`.

## 5. Comportamento atual a preservar

- `MAX_REGIONS_PER_FILE = 12`;
- `MAX_REGIONS = 300`;
- caps de arquivos, símbolos, relacionamentos e testes;
- deduplicação por `(path, start_line, end_line)`;
- prioridade atual para regiões de relacionamento;
- `SELECTION_CAP_REACHED` quando candidatos são omitidos;
- `CAP_OMISSION` na completude quando qualquer cap omite evidência;
- `UNCOVERED_CENTRAL_TERMS` quando termo central não possui ocorrência;
- suficiência somente quando todos os gates atuais passam e não há omissão.

A melhoria não pode fazer um pacote com evidência crítica omitida retornar
`sufficient`.

## 6. Comportamento proposto

### 6.1 Candidate generation

Não descartar `rows[:MAX_REGIONS_PER_FILE]` antes da priorização. Gerar
candidatos bounded pelo inventário já limitado pelo `controlled_reader`,
retendo somente metadados e excerpts necessários para a etapa final.

Adicionar candidatos de símbolo/teste para definições cujo nome corresponde a
um termo central, mesmo quando a linha da definição não contém uma ocorrência
lexical independente.

### 6.2 Priority classes

A seleção deve ordenar candidatos de forma determinística nesta prioridade:

1. símbolo crítico de implementação;
2. teste crítico;
3. região de relacionamento estrutural;
4. código ativo com termo central;
5. código ativo com alias/termo derivado;
6. código ativo não crítico;
7. comentário ou docstring.

Dentro de cada classe, desempatar por relevância lexical, score da fonte,
path, linha inicial e linha final.

### 6.3 Per-file budget

Dentro de cada arquivo:

1. selecionar primeiro regiões críticas;
2. preservar relacionamento necessário;
3. preencher slots restantes com contexto relevante;
4. nunca substituir região crítica por candidato lexical redundante;
5. se regiões críticas excederem 12, preservar no máximo 12 e registrar as
   omitidas como evidência crítica não coberta.

### 6.4 Global budget

O limite global de 300 permanece inalterado. Se regiões críticas excederem o
limite global:

- selecionar de forma determinística;
- registrar todas as omissões relevantes dentro de um resumo bounded;
- manter `SELECTION_CAP_REACHED` e `CAP_OMISSION`;
- manter a completude como `insufficient`;
- nunca promover o pacote por volume parcial.

### 6.5 Omission provenance

O Evidence Pack deve registrar, dentro dos limites de tamanho já existentes,
por que uma evidência crítica não foi selecionada:

- arquivo;
- linha ou símbolo;
- classe de evidência;
- cap que causou a omissão;
- termo ou relacionamento associado.

Se o modelo receber um novo campo, ele deve ser opcional e compatível com
Evidence Packs legados. A ausência desse campo em pacotes antigos não deve
alterar o comportamento de consumo.

### 6.6 Structural scope

`--include-path` continua sendo a autoridade de superfície. A seleção crítica
não pode reintroduzir arquivos fora de `structural_scope`.

## 7. Critérios de aceitação

- **AC-01:** função crítica localizada após 12 regiões lexicais é selecionada
  quando seu nome é termo central.
- **AC-02:** teste crítico localizado após imports e fixtures é selecionado
  quando seu nome é termo central.
- **AC-03:** seleção é determinística para mesma missão, target e scope.
- **AC-04:** cada relacionamento selecionado possui região de evidência
  materializada.
- **AC-05:** candidato lexical redundante pode ser descartado sem substituir
  uma região crítica.
- **AC-06:** cap por arquivo continua sendo 12 e omissões críticas preservam
  `CAP_OMISSION`/`SELECTION_CAP_REACHED`.
- **AC-07:** cap global continua sendo 300 e não permite status `sufficient`
  quando evidência crítica foi omitida.
- **AC-08:** missão sem correspondência mantém `UNCOVERED_CENTRAL_TERMS` e
  permanece insuficiente.
- **AC-09:** `--include-path` continua impedindo arquivos fora da superfície.
- **AC-10:** chamadas legadas sem `--include-path` preservam comportamento
  compatível, salvo a nova priorização de evidência dentro dos mesmos caps.
- **AC-11:** Evidence Pack continua respeitando `MAX_JSON_BYTES` e não cria
  escrita, rede, subprocesso ou execução no TARGET.

## 8. Plano de testes

Adicionar regressões em `tests/test_mission_audit.py`:

1. `test_critical_symbol_after_twelve_regions_is_selected`;
2. `test_critical_test_after_imports_and_fixtures_is_selected`;
3. `test_critical_selection_is_deterministic`;
4. `test_critical_symbol_and_relationship_region_are_preserved`;
5. `test_redundant_candidates_do_not_replace_critical_region`;
6. `test_per_file_cap_reports_critical_omission_without_sufficiency`;
7. `test_global_region_cap_reports_critical_omission_without_sufficiency`;
8. `test_unmatched_central_term_remains_insufficient`;
9. `test_critical_selection_respects_include_path`;
10. `test_legacy_empty_scope_remains_compatible`;
11. `test_evidence_pack_size_limit_remains_fail_closed`.

O RED deve ser separado entre:

- testes críticos que falham por ausência da nova priorização;
- guards legados que continuam passando;
- falhas inesperadas de setup, que devem ser corrigidas antes de classificar
  o RED.

## 9. Impactos e riscos

### Desempenho

A coleta de candidatos pode manter mais metadados antes da seleção. O custo
continua bounded pelo inventário e pelos limites do `controlled_reader`.
A implementação deve medir tempo e memória em uma árvore representativa.

### Tamanho do Evidence Pack

O número final de regiões, símbolos, relações e testes continua limitado.
O resumo de omissões críticas também deve ser bounded. Se o JSON exceder
`MAX_JSON_BYTES`, o comando deve falhar fechado.

### Compatibilidade

- HERMES-0014 continua definindo `--include-path`;
- HERMES-0035 continua definindo limites de entrada da missão;
- HERMES-0035 não deve ser alterada retroativamente para autorizar mudança de
  ranking sem nova decisão;
- Evidence Packs legados continuam carregáveis.

### Segurança

Uma seleção mais inteligente não equivale a evidência completa. O auditor
deve continuar distinguindo:

```text
sufficient
insufficient
CAP_OMISSION
UNCOVERED_CENTRAL_TERMS
```

## 10. Arquivos provavelmente afetados

- `src/hermes_ops/skills/mission_audit.py`;
- `src/hermes_ops/skills/mission_models.py`, se o resumo de omissões for
  estruturado;
- `tests/test_mission_audit.py`;
- `docs/hermes/specs/HERMES-0036-critical-evidence-selection.md`.

## 11. Implementação e validação

A implementação foi concluída em `9a9c8d1` e integrada nesta branch de release.
A seleção de símbolos, testes e relacionamentos críticos permanece prioritária,
com caps e sinais de omissão preservados.

## 12. Evidência de validação

- testes focados: `tests/test_mission_audit.py` — 56 passed;
- suíte Hermes Ops: 983 passed, 11 skipped, 2 warnings ambientais;
- `git diff --check`: sem avisos;
- HERMES-0037 adiciona a validação fail-closed para provenance v2 e cobertura
  adversarial de omissões não comprovadas.

Os testes devem ser repetidos na árvore integrada antes da publicação final.
