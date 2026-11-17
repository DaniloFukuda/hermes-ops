---
spec_id: HERMES-0019
title: Explicit Python Dataflow Resolution
version: 1
status: Implementado
date: 2026-08-20
depends_on:
  - HERMES-0015
  - HERMES-0018
---

# HERMES-0019 — Explicit Python Dataflow Resolution

## 1. Contexto

O `execution-path-review` v1 reconhece composições de chamadas aninhadas, mas
não acompanha valores por assignments locais, campos de mappings ou wrappers
explícitos. Dogfood real mostrou tanto esse padrão Python quanto uma fronteira
operacional externa entre stdout e uma nova invocação CLI.

## 2. Problema confirmado

O analisador conflaciona ausência de caminho com caminhos múltiplos sob
`EXECUTABLE_PATH_NOT_UNIQUE`. Além disso, não representa uma cadeia explícita
como producer → mapping retornado → subscript → alias → método qualificado →
forwarding posicional → consumer. A fronteira stdout → nova CLI não contém um
edge Python e não pode ser inventada.

## 3. Explicação em linguagem natural

A evolução acompanha somente valores cuja movimentação está escrita no código
Python autorizado. Cada passo precisa mostrar de onde o valor veio e para qual
parâmetro foi enviado. Um nome igual em duas funções não cria relação. Quando o
valor sai pelo terminal e volta em outro processo, o caminho termina.

## 4. Comportamento atual

O core reconhece o nome de chamadas diretas no primeiro argumento do consumer
e composições sintáticas aninhadas. Não reconhece métodos, aliases locais,
subscripts de mapping ou wrappers. Zero e muitos traces recebem o mesmo código.

## 5. Comportamento desejado

- Zero caminhos produz `NO_EXECUTABLE_PATH` e evidência insuficiente.
- Mais de um caminho produz `EXECUTABLE_PATH_NOT_UNIQUE`.
- Um caminho com edges explícitos continua a análise vigente.
- Assignments simples, mapping fields, subscripts literais, chamadas
  qualificadas inequívocas e forwarding posicional 1:1 preservam identidade.
- Guards simples de truthiness e `str(value).strip()` podem descrever
  preconditions estruturais.
- Redefinição incompatível rompe a identidade anterior.

## 6. Fora do escopo

- stdout → nova invocação CLI e qualquer fluxo entre processos;
- semântica de persistência ou SQL;
- call graph whole-program;
- taint analysis genérica;
- symbolic execution ou SSA;
- arbitrary alias analysis;
- `getattr`, monkey patching, metaclasses e imports dinâmicos;
- `dict.get`, `**kwargs` e argument reshaping genérico.

## 7. Invariantes e regras de segurança

1. O target nunca é importado nem executado.
2. O pure core recebe somente documentos já autorizados e não relê o filesystem.
3. O structural scope não é ampliado para procurar callers.
4. Cada edge depende de evidência sintática positiva; não há scores ou nomes
   parecidos.
5. Ambiguidade ou construct não suportado reduz a conclusão conservadoramente.
6. Resultados, paths, limitations e evidence refs são determinísticos.
7. HERMES-0015 e a arquitetura de snapshot único HERMES-0018 são preservados.

## 8. Entradas e saídas

As entradas públicas permanecem source documents, producer, consumer e scope.
O schema público permanece v1. A saída continua sendo `ExecutionPathReport`.
`NO_EXECUTABLE_PATH` é um novo limitation code; não é uma classificação nova.
Edges e identidades de valor são modelos internos frozen.

## 9. Pseudocódigo independente de linguagem

```text
validar as entradas e analisar somente os documentos recebidos
localizar producer e consumer de forma inequívoca

para cada função autorizada, na ordem escrita:
    acompanhar chamadas explícitas do producer
    ligar o resultado a assignments locais
    permitir extração de chave literal declarada pelo mapping retornado
    apagar uma identidade quando a variável for redefinida por outra origem
    ao encontrar uma chamada inequívoca:
        ligar argumentos reais aos parâmetros formais correspondentes
        continuar por wrappers simples
        registrar um caminho ao alcançar o consumer

remover duplicatas idênticas e ordenar os caminhos pela evidência
se nenhum caminho restar:
    retornar evidência insuficiente com NO_EXECUTABLE_PATH
se mais de um caminho restar:
    retornar evidência insuficiente com EXECUTABLE_PATH_NOT_UNIQUE
se exatamente um caminho restar:
    extrair guarantee e precondition suportadas
    continuar a comparação conservadora existente

nunca ligar uma saída impressa à entrada de outro processo
```

## 10. Fluxo principal

1. Parse e indexação determinísticos dos source documents.
2. Extração conservadora dos shapes de retorno do producer.
3. Interpretação local de assignments e calls relevantes.
4. Binding posicional entre argumento real e parâmetro formal.
5. Travessia apenas por definições qualificadas inequívocas no scope.
6. Pruning por redefinição, key diferente ou origem distinta.
7. Contagem separada de zero, um e muitos paths.
8. Aplicação das regras de guarantee/precondition existentes e novas.

## 11. Erros, limites e fronteiras

- Definição ambígua continua produzindo `SYMBOL_DEFINITION_NOT_UNIQUE`.
- Zero path produz `NO_EXECUTABLE_PATH`.
- Muitos paths produzem `EXECUTABLE_PATH_NOT_UNIQUE`.
- Mapping com returns incompatíveis não recebe shape estável.
- Key dinâmica, despacho dinâmico, redefinição ou forwarding ambíguo não cria edge.
- Truthiness representa somente controle de fluxo; não implica existência em DB.
- Print e parsing CLI são endpoints desconectados.

## 12. Critérios de aceitação

- **AC-01:** zero paths produz `NO_EXECUTABLE_PATH`.
- **AC-02:** dois ou mais paths produzem `EXECUTABLE_PATH_NOT_UNIQUE`.
- **AC-03:** um path explícito continua a análise.
- **AC-04:** alias local simples preserva identidade.
- **AC-05:** field de mapping retornado é rastreável.
- **AC-06:** subscript com key literal é rastreável.
- **AC-07:** método qualificado inequívoco é reconhecido.
- **AC-08:** forwarding posicional 1:1 preserva identidade.
- **AC-09:** truthiness com raise produz precondition.
- **AC-10:** truthiness com retorno falso descreve condição de sucesso.
- **AC-11:** `str(value).strip()` direto é reconhecido.
- **AC-12:** nomes iguais desconectados não criam path.
- **AC-13:** redefinição rompe identidade anterior.
- **AC-14:** fixture completa produz um path único.
- **AC-15:** fixture sem caller produz `NO_EXECUTABLE_PATH`.
- **AC-16:** stdout → CLI não cria path.
- **AC-17:** contratos HERMES-0015 permanecem semanticamente compatíveis.
- **AC-18:** o pure core HERMES-0018 permanece equivalente ao wrapper.
- **AC-19:** structural scope permanece fechado.
- **AC-20:** resultado permanece determinístico e read-only.

## 13. Plano de testes

`tests/test_execution_path_semantic_resolution.py` cobre AC-01 a AC-16 e AC-20
com fixtures genéricas positivas e negativas. As suítes HERMES-0015 e
HERMES-0018 cobrem AC-17 a AC-19. Cada teste novo referencia seus ACs. Depois
dos testes focados são executadas regressões das áreas afetadas e a full suite.

## 14. Arquivos provavelmente afetados

- `docs/hermes/specs/HERMES-0019-explicit-python-dataflow-resolution.md`
- `src/hermes_ops/skills/execution_path_review.py`
- `tests/test_execution_path_semantic_resolution.py`

Modelos públicos, CLI, catálogo e executor não devem mudar sem necessidade
demonstrada por teste.

## 15. Riscos conhecidos

- Resolver método apenas pelo nome pode escolher classe errada; ambiguidade deve
  falhar conservadoramente.
- Interpretar controle de fluxo parcialmente pode criar path impossível.
- Returns múltiplos podem declarar shapes incompatíveis.
- Um alias pode ser redefinido antes do uso.
- Incluir callers estruturais no path pode alterar contratos antigos; composição
  aninhada já suportada deve preservar sua representação.
- Expansão interprocedural sem limite pode criar ciclos; a travessia precisa de
  conjunto de definições ativas e profundidade finita.

## Evidências da implementação

| Evidência | Resultado |
|---|---|
| Primeiro RED, AC-01 | `NO_EXECUTABLE_PATH` ausente; zero trace ainda retornava `EXECUTABLE_PATH_NOT_UNIQUE` |
| Suíte HERMES-0019 | `9 passed` |
| HERMES-0015, audit round e finding ranking | `44 passed` |
| Skill execution, catálogo, mission audit e execution context | `101 passed` |
| Analysis Pack e Analysis CLI | `25 passed` |
| Full suite com basetemp externo ao repositório | `643 passed, 11 skipped` |
| Dogfood TEST_ONLY | path `ingest → test_only_flow → bind_existing_card → bind_existing_trello_card` resolvido |
| Dogfood operacional | `INSUFFICIENT_EVIDENCE` com `NO_EXECUTABLE_PATH`; stdout → CLI não inferido |

Os 11 skips da full suite são limitações de symlink/permissão no ambiente
Windows e um dogfood de clone externo explicitamente opt-in. Nenhum teste
falhou. Um primeiro ensaio com basetemp dentro da raiz foi descartado porque os
diretórios temporários herdavam o repositório pai e invalidavam as premissas de
testes Git; a execução válida usou basetemp fora da raiz exata.
