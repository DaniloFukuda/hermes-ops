---
spec_id: HERMES-0020
title: Producer Guarantee Semantics
version: 1
status: Implementado
date: 2026-08-20
depends_on:
  - HERMES-0015
  - HERMES-0018
  - HERMES-0019
---

# HERMES-0020 — Producer Guarantee Semantics

## 1. Contexto

A HERMES-0019 prova dataflow Python explícito por mappings, aliases e wrappers,
mas um producer cujo campo vem de chamada opaca ainda termina apenas com
`PRODUCER_GUARANTEE_NOT_DISCOVERABLE`. Origem sintática e domínio semântico
precisam ser representados separadamente.

## 2. Problema confirmado

O extractor atual retorna somente um domínio ou `None`. Assim, não distingue
return shape ausente de field conhecido cuja origem é uma chamada com domínio
desconhecido. Ele também exige um único return e não representa contratos
restritos a mappings marcados explicitamente com `"success": True`.

## 3. Explicação em linguagem natural

Saber de onde veio um valor não diz quais valores ele pode assumir. A análise
registra a origem para diagnóstico, mas só compara producer e consumer quando
há domínio demonstrado por literal, parâmetro caller-controlled ou transformação
já suportada. Uma chamada opaca e `cursor.lastrowid` continuam sem domínio.

## 4. Comportamento atual

Literais, parâmetros, aliases simples, composição de path e fields de mappings
com essas expressões produzem `_Domain`. Chamadas retornam `None`. Mais de um
`return` impede qualquer guarantee, mesmo quando failure e success mappings são
explicitamente discriminados.

## 5. Comportamento desejado

- Origin e Domain são fatos internos frozen e independentes.
- Mapping field herda ambos da expressão associada.
- Returns com `"success": True` literal formam um contrato de success path.
- Todos os success returns precisam conter o field e domínios compatíveis.
- Failure returns explícitos não contaminam o contrato de success path.
- Origem conhecida sem domínio gera diagnóstico específico e permanece
  `INSUFFICIENT_EVIDENCE`.
- Apenas Domain participa de mismatch/no-mismatch.

## 6. Fora do escopo

- interpretação SQL genérica ou INSERT → entidade existe;
- semântica de SELECT, transação, foreign key ou commit;
- `cursor.lastrowid` como guarantee de persistência;
- persistência entre processos ou chamadas;
- sistema público de contratos de helper;
- análise interprocedural whole-program;
- symbolic execution, SSA ou taint analysis genérica;
- arbitrary aliasing e dynamic dispatch.

## 7. Invariantes e regras de segurança

1. Value origin, domain, validity, persistence e business guarantee são fatos
   diferentes e nunca são promovidos implicitamente.
2. O target não é importado nem executado.
3. O pure core opera apenas sobre source documents autorizados.
4. O structural scope não é ampliado para resolver helper.
5. Limitações e evidence refs são determinísticos e relativos.
6. Ambiguidade reduz a conclusão; nunca cria confirmação.
7. HERMES-0015, HERMES-0018 e HERMES-0019 permanecem semanticamente compatíveis.

## 8. Entradas e saídas

Entradas e schema público permanecem inalterados. Internamente,
`ProducerEvidence` contém origin opcional, domain opcional e a informação de que
o field está presente em todos os success returns explícitos. Um novo limitation
code diferencia origem conhecida com domínio desconhecido.

## 9. Pseudocódigo independente de linguagem

```text
identificar o field do producer que alcança o parâmetro do consumer
enumerar todos os returns do producer

se houver mappings marcados explicitamente com success=True:
    considerar somente esses mappings como variantes de sucesso
    exigir que todos contenham o field observado
senão, se houver exatamente um return normal:
    usar esse return
senão:
    a guarantee não é demonstrável

para cada expressão produzida para o field:
    registrar sua origem sintática
    derivar domínio somente por regras fechadas já suportadas

se alguma variante não possuir field ou origem:
    reportar guarantee não descobrível
senão, se algum domínio estiver ausente ou os domínios divergirem:
    reportar origem descoberta e domínio desconhecido
senão:
    comparar o domínio comum somente com a precondition do consumer

nunca interpretar SQL, lastrowid ou nome de helper como domínio
```

## 10. Fluxo principal

1. Resolver path e mapping key pela HERMES-0019.
2. Extrair variantes de return e discriminantes explícitos.
3. Construir OriginFact e DomainFact por expressão.
4. Consolidar ProducerEvidence de todas as variantes relevantes.
5. Emitir diagnóstico específico quando apenas origin for conhecida.
6. Aplicar transforms intermediários pelo mesmo extractor de evidência.
7. Comparar somente domains compatíveis.

## 11. Erros, limites e fronteiras

- Key dinâmica, mapping expandido ou return shape desconhecido não cria field.
- Sem success return explícito, o comportamento legado de return único continua.
- Success returns incompatíveis não escolhem branch arbitrariamente.
- Success return sem field impede field presence guarantee.
- Helper opaco, atributo de resultado de chamada e SQL não produzem DomainFact.
- Guard-derived producer domain fica fora da v1 se exigir controle de fluxo novo.

## 12. Critérios de aceitação

- **AC-01:** literal direto produz DomainFact literal.
- **AC-02:** literal por alias preserva domínio.
- **AC-03:** mapping field herda domain da expressão.
- **AC-04:** parâmetro continua unconstrained.
- **AC-05:** helper opaco produz OriginFact sem DomainFact.
- **AC-06:** origin conhecida/domain desconhecido usa o novo limitation code.
- **AC-07:** origin sem domain continua insufficient.
- **AC-08:** origin nunca é promovida a mismatch/no-mismatch.
- **AC-09:** success returns compatíveis com field estabelecem guarantee.
- **AC-10:** failure returns explícitos não contaminam o success contract.
- **AC-11:** success returns incompatíveis permanecem insufficient.
- **AC-12:** success return sem field impede guarantee.
- **AC-13:** confirmed → confirmed produz `NO_MISMATCH`.
- **AC-14:** prepared → confirmed produz `CONFIRMED_MISMATCH`.
- **AC-15:** `cursor.lastrowid` não cria persistence guarantee.
- **AC-16:** SQL literal não cria DomainFact.
- **AC-17:** dataflow HERMES-0019 permanece intacto.
- **AC-18:** semântica HERMES-0015 permanece intacta.
- **AC-19:** pure core HERMES-0018 não acessa filesystem.
- **AC-20:** resultados e limitations são determinísticos.
- **AC-21:** structural scope não é ampliado para helper.
- **AC-22:** target nunca é importado ou executado.

## 13. Plano de testes

`tests/test_execution_path_producer_guarantees.py` cobre AC-01 a AC-16 e AC-20
com fixtures positivas e negativas. As suítes HERMES-0015, HERMES-0018 e
HERMES-0019 cobrem AC-17 a AC-19, AC-21 e AC-22. Após os testes focados, são
executadas regressões, full suite e dogfoods read-only.

## 14. Arquivos provavelmente afetados

- `docs/hermes/specs/HERMES-0020-producer-guarantee-semantics.md`
- `src/hermes_ops/skills/execution_path_review.py`
- `tests/test_execution_path_producer_guarantees.py`

Nenhum modelo público, CLI, catálogo ou arquivo de um projeto consumidor deve ser
alterado.

## 15. Riscos conhecidos

- `ast.walk` sem controle de fluxo pode misturar aliases de branches; o novo
  extractor deve permanecer limitado a resolução determinística.
- Múltiplos returns podem ter discriminantes ausentes ou incompatíveis.
- Field presence no success return não prova que o caller tomou esse branch.
- Tratar chamada como domain introduziria falso positivo crítico.
- Migração do extractor pode alterar benchmarks HERMES-0015 ou transforms
  intermediários; as regressões são obrigatórias.

## Evidências da implementação

| Evidência | Resultado |
|---|---|
| Primeiro RED | confirmed mapping ficou `POTENTIAL_MISMATCH` por tratar caller como transformação |
| Suíte HERMES-0020 | `11 passed` |
| HERMES-0015/0018/0019 e finding ranking | `53 passed` |
| Skill execution, catálogo, mission audit e execution context | `101 passed` |
| Analysis Pack, packaging e Analysis CLI | `25 passed` |
| Full suite com basetemp externo | `654 passed, 11 skipped` |
| Dogfood confirmed | `NO_MISMATCH`, path único, zero limitations |
| Dogfood prepared | `CONFIRMED_MISMATCH`, path único |
| Dogfood helper opaco | `INSUFFICIENT_EVIDENCE` + `PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN` |
| Dogfood projeto consumidor `batch_id` | origin opaca via `cursor.lastrowid`; domain ausente; insufficient |

Os 11 skips são os mesmos da baseline: um clone externo opt-in, uma fixture de
permission-denied não portátil no Windows e nove fixtures de symlink sem
privilégio no host. Nenhum teste falhou e nenhum skip pertence ao analyzer.
