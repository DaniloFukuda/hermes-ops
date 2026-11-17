---
title: Minimal Structural Kernel Consolidation
status: Implementado
---

# HERMES-0026 — Minimal Structural Kernel Consolidation

## 1. Contexto

A revisão arquitetural HERMES-0015–0025 encontrou duas operações puramente
estruturais repetidas entre lenses: obter o símbolo sintático terminal de uma
callable e representar uma posição de source como `caminho:linha`. O benchmark
histórico HERMES-0025 ainda depende de um checkout consumidor e de Git externo.

## 2. Problema confirmado

`execution_path_review`, `persistence_contract_review` e
`state_guard_effect_review` repetem a mesma decisão para `ast.Name` e
`ast.Attribute`. Persistence e state repetem a criação de locators; execution
faz a mesma formatação em seus pontos de evidência, e o ranker faz o parsing do
mesmo contrato. O teste histórico aponta para caminho absoluto, SHAs e um
repositório externo, portanto não é hermético.

## 3. Explicação em linguagem natural

Serão extraídas somente duas pequenas funções: uma responde qual é o último
nome escrito numa callable estática; outra monta a referência relativa de uma
linha de source. O parsing inverso só será compartilhado se preservar exatamente
a validação atual do ranker. Nenhuma delas decide o significado da chamada.
O benchmark passará a analisar dois trechos mínimos controlados, mantendo o
mesmo request e a diferença causal dos snapshots validados.

## 4. Comportamento atual

Cada analyzer tem helper local equivalente para calls. Evidence refs usam
strings `relative/path.py:<line>` e o ranker as converte em `EvidenceRef`. Os
reports, finding IDs, ordenação e JSON dependem desse formato. O benchmark
HERMES-0025 executa `git show` num caminho absoluto do projeto consumidor e pula quando o
checkout não existe.

## 5. Comportamento desejado

Criar `structural_ast.terminal_symbol` e `source_evidence.source_locator`, ambos
puros, pequenos e sem exports em `skills.__init__`. Migrar somente os usos
semanticamente idênticos. Se o parser for extraído, deve manter os mesmos erros e
o mesmo `EvidenceRef`. Tornar o benchmark autocontido e provar delta semântico
zero por caracterização e regressão.

## 6. Fora do escopo

Não criar walker, dataflow engine, symbolic executor, auditor base, fact comum,
identity ou generation engine, enum comum, normalizer ou serializer genérico,
grafo, taint, SSA, plugin framework, lens, auditor, finding, severity ou
classification. Permanecem separados `_FlowValue`, facts de producer,
identidade de persistence, `MutationIntentFact`, estados/generações da state
lens, findings/classifications nativos e semântica SQL.

## 7. Invariantes e regras de segurança

1. Outputs nativos e normalizados, limitations, evidence refs, IDs e ordering
   não mudam.
2. `terminal_symbol` não resolve definição, unicidade, forwarding, module path,
   `self`/`cls`, dispatch ou monkey patching.
3. Locators nunca introduzem caminho absoluto, cwd, timestamp ou object id.
4. Helpers não leem filesystem, importam/executam target, descobrem arquivos,
   resolvem imports nem acessam `sys.path`.
5. Structural scope e isolamento entre auditors permanecem inalterados.
6. Audit Round preserva snapshot único, uma leitura controlada, ordering,
   isolamento de falhas, normalização posterior, ranking único e JSON
   determinístico.
7. Nenhum nome, SHA, path ou regra de consumidor entra em produção.

## 8. Entradas e saídas

`terminal_symbol(node: ast.AST) -> str | None` recebe somente um AST e retorna o
`id` de `Name`, o `attr` de `Attribute`, ou `None`.

`source_locator(relative_path, node) -> str` recebe um caminho source relativo
já pertencente ao snapshot e um nó com linha válida; retorna
`relative/path.py:<line>` de modo determinístico. Um parser opcional recebe essa
string e retorna o `EvidenceRef` equivalente, mantendo falha fechada.

## 9. Pseudocódigo independente de linguagem

```text
para obter o símbolo terminal:
    se a expressão é um nome, devolver esse nome
    se a expressão é acesso a atributo, devolver apenas o atributo final
    para qualquer outra expressão, devolver ausência

para criar um locator:
    confirmar que o caminho atende ao contrato relativo existente
    obter e validar a linha inteira do nó
    juntar caminho e linha com dois-pontos

para cada analyzer aprovado:
    substituir apenas o helper local equivalente
    manter local toda decisão semântica

para o benchmark:
    criar um request uma vez
    analisar source buggy mínimo e source fixed mínimo
    confirmar request inalterado, mismatch no buggy e alinhamento no fixed
```

## 10. Fluxo principal

Testes RED das primitives → testes de caracterização → implementação pura →
migração estreita → benchmark hermético → testes focados → regressões →
full suite → build e inspeção dos artefatos.

## 11. Erros e limites

Callable por subscript, retorno de call, lambda e dispatch dinâmico retornam
`None`. Caminho absoluto, linha ausente/não inteira ou locator malformado falham
fechado. Ambiguidade, definições múltiplas, forwarding e dispatch continuam sob
as regras locais dos analyzers. Se centralizar mudar ID/JSON, exigir walker/fact
comum, ampliar scope ou tornar um auditor dependente de outro, a implementação
deve parar.

## 12. Critérios de aceitação

- **AC-01:** `terminal_symbol` retorna id para `ast.Name`.
- **AC-02:** retorna attr terminal para `ast.Attribute`.
- **AC-03:** falha fechado para callable dinâmica.
- **AC-04:** execution usa a primitive sem mudar resolução.
- **AC-05:** persistence usa a primitive sem mudar resolução.
- **AC-06:** state usa a primitive sem mudar resolução.
- **AC-07:** source locator é determinístico.
- **AC-08:** source locator não introduz path absoluto público.
- **AC-09:** evidence refs de execution permanecem equivalentes.
- **AC-10:** evidence refs de persistence permanecem equivalentes.
- **AC-11:** evidence refs de state permanecem equivalentes.
- **AC-12:** finding IDs de execution permanecem estáveis.
- **AC-13:** finding IDs de persistence permanecem estáveis.
- **AC-14:** finding IDs de state permanecem estáveis.
- **AC-15:** ranking ordenado permanece estável.
- **AC-16:** JSON da Audit Round permanece determinístico.
- **AC-17:** não surge dependência semântica entre auditors.
- **AC-18:** nenhum walker comum é introduzido.
- **AC-19:** nenhum fact comum de domain/state/persistence é introduzido.
- **AC-20:** benchmark não depende de caminho absoluto externo.
- **AC-21:** benchmark não depende de checkout projeto consumidor.
- **AC-22:** fixture buggy produz mismatch confirmado.
- **AC-23:** fixture fixed produz alinhamento estrutural.
- **AC-24:** buggy e fixed usam o mesmo request.
- **AC-25:** helpers de produção não contêm hardcode consumidor.
- **AC-26:** pure cores não passam a ler filesystem.
- **AC-27:** structural scope não é ampliado.
- **AC-28:** full regression permanece verde.
- **AC-29:** wheel e sdist contêm os novos módulos.
- **AC-30:** semantic delta dos contratos existentes é zero.

## 13. Plano de testes

AC-01–03 terão testes unitários diretos, inclusive negativos. AC-07–08 e o
parsing terão testes de path relativo/nested, linha, invalidade e determinismo.
AC-04–06, AC-09–16 e AC-30 serão cobertos pelas suites existentes mais
caracterizações de reports/JSON/IDs/ranking/Audit Round. AC-20–24 terão o teste
histórico hermético. AC-25 terá inspeção automatizada. AC-17–19 e AC-26–27
serão verificados por testes de arquitetura e inspeção do diff. AC-28 será
provado pela full suite; AC-29 pela inspeção de wheel e sdist.

## 14. Arquivos provavelmente afetados

Esta spec; `structural_ast.py`; `source_evidence.py`; os três review modules;
possivelmente `finding_ranking.py` apenas para parsing idêntico; testes unitários
das primitives, caracterização e benchmark histórico. `audit_round.py` e
`skills.__init__` não devem mudar.

## 15. Riscos conhecidos

Os riscos são aceitar callable dinâmica, alterar fallback de linha, normalizar
path além do contrato existente, mudar parsing/erro, reordenar evidências ou
identidade canônica e reduzir a fidelidade causal da fixture histórica. Qualquer
delta observado deve ser corrigido na extração, nunca absorvido por snapshots.

## Evidências finais

- TDD RED: `test_structural_ast.py` e `test_source_evidence.py` falharam na
  coleta com `ModuleNotFoundError` para os dois módulos ainda inexistentes.
- Primitives GREEN: 21 passed. Direct/qualified calls, callable dinâmica,
  paths nested/relativos, linha, parsing, paths host inseguros e anti-hardcode
  foram exercitados.
- Caracterização before/after: 3 passed. Reports nativos e JSON normalizado e
  rankeado de execution, persistence e state ficaram byte a byte idênticos aos
  helpers legados, incluindo finding IDs.
- Focados de execution, persistence, state, ranking, Audit Round, benchmark e
  primitives: 185 passed; somados aos 3 de caracterização, 188 passed.
- Benchmark hermético: o mesmo request imutável produz
  `CONFIRMED_CONTRACT_MISMATCH`/`STATE_EFFECT_COVERAGE_MISMATCH` no source buggy
  e `CONTRACT_STRUCTURALLY_ALIGNED`/zero findings no fixed, sem Git ou checkout
  consumidor.
- Regressões amplas de mission audit, Analysis Pack, skill execution, catálogo,
  CLI, controlled reading, execution context, Git safety, serialization e
  packaging: 396 passed, 9 skipped em 69,98 s. Os skips são limitações já
  conhecidas de symlink/permissão no Windows e dogfooding externo opt-in.
- Full suite: 778 passed, 11 skipped, 0 failed em 76,30 s; 24 testes a mais que
  o baseline, sem skip novo relacionado à extração.
- Build: wheel e sdist construídos com sucesso. A inspeção de ambos confirmou
  `structural_ast.py`, `source_evidence.py`, `execution_path_review.py`,
  `finding_ranking.py`, `audit_round.py`, `persistence_contract_review.py` e
  `state_guard_effect_review.py` exatamente uma vez em cada artefato.
- `audit_round.py` e `skills.__init__` não foram alterados por HERMES-0026. Os
  helpers permanecem puros, sem filesystem, target, imports ambientais, scope
  discovery, facts compartilhados ou semântica de consumidor.
