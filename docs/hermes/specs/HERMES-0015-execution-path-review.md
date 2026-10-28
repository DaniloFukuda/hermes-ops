---
spec_id: HERMES-0015
title: Execution Path Review v1
version: 1
status: Implementado
date: 2026-08-20
depends_on:
  - HERMES-0008
  - HERMES-0014
---

# HERMES-0015 — Execution Path Review v1

## 1. Contexto

As auditorias atuais localizam estrutura e evidência, mas não respondem se um
valor ou estado produzido por uma fronteira executável satisfaz a pré-condição
aplicada por um consumidor alcançável.

## 2. Problema Confirmado

Não existe skill registrada que relacione comportamento do produtor,
propagação executável e guarda do consumidor. `code-audit` aplica regras
fechadas locais e `mission-audit` coleta evidência sem afirmar compatibilidade.

## 3. Explicação em Linguagem Natural

A nova skill acompanha um valor entre duas funções indicadas. Ela só confirma
incompatibilidade quando o código mostra a origem, o caminho até o consumidor,
a exigência do consumidor e um resultado alcançável que viola essa exigência.
Lacunas reduzem a conclusão para potencial ou evidência insuficiente.

## 4. Comportamento Atual

`run_skill` possui despacho fechado para `git-preflight`, `code-audit` e
`mission-audit`. Nenhum resultado representa compatibilidade entre fronteiras.

## 5. Comportamento Desejado

`execution-path-review` recebe raiz exata, símbolo produtor, símbolo consumidor
e escopo estrutural opcional. Analisa Python sem executar o alvo e retorna um
relatório determinístico com uma das classificações `CONFIRMED_MISMATCH`,
`POTENTIAL_MISMATCH`, `NO_MISMATCH` ou `INSUFFICIENT_EVIDENCE` e zero ou mais
achados rastreáveis.

HERMES-0023 refina este contrato: quando existe exatamente um caminho provado,
mas nenhum dos lados expõe contrato comparável, o resultado específico é
`PATH_PROVEN_NO_COMPARABLE_CONTRACT`, sem achados. A ausência de requisito com
candidato de guarda opaco continua `INSUFFICIENT_EVIDENCE`.

## 6. Fora do Escopo

- Correção automática, ranking, orquestração multiagente ou quatro lentes.
- Call graph completo, inferência interprocedural geral ou execução do alvo.
- Skills futuras citadas na missão e alterações no Lucre Agro.
- Nomes, caminhos ou integrações especiais de qualquer projeto consumidor.

## 7. Invariantes e Regras de Segurança

- Somente leitura; sem import, execução, subprocesso, Git, rede ou escrita no alvo.
- A raiz informada é exata; pais e irmãos nunca são descobertos.
- O `controlled_reader` filtra o escopo antes da leitura.
- Somente código executável sustenta confirmação; nomes e comentários não bastam.
- Paths públicos são relativos e a serialização é determinística.
- Elo essencial ausente impede `CONFIRMED_MISMATCH`.

## 8. Entradas e Saídas

Entradas: `project`, `producer_symbol`, `consumer_symbol`, `include_paths` e
`mission` opcional. Os símbolos são identificadores Python simples na v1.

Saída: relatório imutável contendo classificação, símbolos, escopo, caminho
executável e achados. Cada achado contém produtor, valor/estado produzido,
consumidor, pré-condição, caminho, descrição, cenário alcançável, severidade e
referências `arquivo:linha`.

## 9. Pseudocódigo Independente de Linguagem

```text
VALIDAR raiz, símbolos e escopo
LER somente fontes autorizadas pelo leitor controlado
LOCALIZAR definições executáveis exatas do produtor e consumidor
SE uma definição ou a exigência do consumidor não estiver demonstrada:
    RETORNAR INSUFFICIENT_EVIDENCE
LOCALIZAR chamada alcançável que leve o resultado do produtor ao consumidor
SE não houver caminho executável:
    RETORNAR INSUFFICIENT_EVIDENCE sem confirmar incompatibilidade
RESUMIR a garantia produzida e a exigência consumidora
APLICAR, em ordem, transformações explícitas no caminho
SE a garantia final implica a exigência:
    RETORNAR NO_MISMATCH
SE o código demonstra um valor alcançável contrário à exigência:
    RETORNAR CONFIRMED_MISMATCH com os quatro elos de evidência
SE existe caminho e possível divergência, mas falta um elo para confirmação:
    RETORNAR POTENTIAL_MISMATCH
```

## 10. Fluxo Principal

1. Validar entradas e normalizar escopo com a arquitetura existente.
2. Ler fontes permitidas antes de qualquer análise.
3. Indexar definições Python por nome exato.
4. Extrair garantias simples de retorno/estado e guardas simples do consumidor.
5. Encontrar composição ou propagação local explícita entre chamadas.
6. Comparar domínios, montar evidência e serializar pelo resultado comum.

## 11. Casos de Erro e Limites

| Situação | Resultado |
|---|---|
| Símbolo inválido | `SKILL_EXECUTION_INVALID` |
| Path de escopo inválido | erro estrutural existente |
| Definição/guarda/caminho ausente | `INSUFFICIENT_EVIDENCE` |
| Sintaxe Python inválida em fonte autorizada | `EXECUTION_PATH_PARSE_FAILED` |
| Construção fora do subconjunto v1 | potencial ou insuficiente, nunca confirmado |

## 12. Critérios de Aceitação

- **AC-01**: domínio arbitrário contra raiz gerenciada produz mismatch.
- **AC-02**: produtor que garante a raiz exigida produz `NO_MISMATCH`.
- **AC-03**: estado `prepared` contra requisito `confirmed` produz mismatch.
- **AC-04**: transição explícita para `confirmed` produz `NO_MISMATCH`.
- **AC-05**: requisito não demonstrável com candidato de contrato opaco produz
  `INSUFFICIENT_EVIDENCE`; a ausência bilateral de contrato em caminho único é
  refinada por HERMES-0023.
- **AC-06**: nomes semelhantes sem caminho não produzem confirmação.
- **AC-07**: achado confirmado contém os quatro elos e todas as evidências públicas.
- **AC-08**: benchmark de persistência de path detecta a classe genérica sem nomes especiais.
- **AC-09**: arquivo fora do escopo não é lido nem influencia resultado.
- **AC-10**: skill é registrada e executada pelo framework existente, read-only.
- **AC-11**: resultados são imutáveis e determinísticos.
- **AC-12**: wheel e sdist contêm exatamente uma cópia byte a byte da skill
  canônica `execution-path-review`.

## 13. Plano de Testes

`tests/test_execution_path_review.py` referencia AC-01 a AC-11 em testes
funcionais, integração, escopo, regressão e determinismo. AC-09 cobre o limite
de segurança; AC-10 cobre comportamento permitido e não regressão do catálogo.

`tests/test_packaging.py` cobre AC-12 nos dois formatos de distribuição.

## 14. Arquivos Provavelmente Afetados

- `skills/execution-path-review/SKILL.md`
- `src/hermes_ops/skills/execution_path_review.py`
- `src/hermes_ops/skills/execution_path_models.py`
- `src/hermes_ops/skills/executor.py`
- `src/hermes_ops/skills/execution_models.py`
- `src/hermes_ops/skills/__init__.py`
- `src/hermes_ops/commands/skill.py`
- `src/hermes_ops/cli.py`
- `tests/test_execution_path_review.py`
- `tests/test_skill_catalog.py`
- `tests/test_packaging.py`
- `pyproject.toml`
- `MANIFEST.in`

## 15. Riscos Conhecidos

O subconjunto estático v1 é deliberadamente pequeno e pode retornar evidência
insuficiente para metaprogramação, aliases complexos, despacho dinâmico e
efeitos externos. A resposta conservadora evita transformar essas limitações
em falsos achados confirmados.

## Evidências da Implementação

| Evidência | Resultado |
|---|---|
| Testes específicos HERMES-0015 | `11 passed` |
| Integrações de catálogo, registry, executor, CLI, modelos, missão e serialização | `172 passed, 2 skipped` |
| Benchmarks genéricos e fixture inspirada no Lucre Agro | todos verdes |
| Resistência a falso positivo | `INSUFFICIENT_EVIDENCE` confirmado |
| Structural scope com arquivo binário externo | arquivo fora do escopo não lido |
| Suíte completa após HERMES-0016 | `610 passed, 2 skipped` |
| Regressão focada de packaging após AC-12 | `9 passed` |
| Wheel e sdist após AC-12 | uma cópia canônica byte a byte em cada artefato |
| Plataforma | Windows, Python 3.13.13 |
