---
spec_id: HERMES-0022
title: Guard-Derived Producer Guarantees
version: 1
status: Implementado
date: 2026-08-20
depends_on: [HERMES-0019, HERMES-0020, HERMES-0021]
---

# HERMES-0022 — Guard-Derived Producer Guarantees

## 1. Contexto

HERMES-0019 prova propagação Python e HERMES-0020 separa origem de domínio,
mas guards do producer ainda não restringem o domínio de seus success returns.
HERMES-0021 permanece uma lente independente de persistência.

## 2. Problema confirmado

Um parâmetro permanece `unconstrained` mesmo quando um early failure return
exclui explicitamente valores incompatíveis antes do success return. Isso reduz
a capacidade semântica sem que seja necessário executar o target.

## 3. Explicação em linguagem natural

Se um guard atômico rejeita o caminho ruim, o binding não muda e o caminho bom
o retorna explicitamente, a condição inversa vale somente naquele success path.
Predicados opacos são registrados, mas nunca traduzidos como regra de negócio.

## 4. Comportamento atual

Success mappings são separados de failure mappings e literals são comparáveis.
Assignments são resolvidos por mapa atemporal. Guards do consumer são extraídos;
guards do producer não geram guarantees.

## 5. Comportamento desejado

Derivar facts internos `TRUTHY`, `EQUAL_LITERAL` e `OPAQUE_PREDICATE` por meio
de um walker sequencial pequeno, com gerações de binding, dominância linear,
alias seguro e invalidação por redefinition/transform.

## 6. Fora do escopo

Symbolic execution, solver de branches, loops, match, try complexo, membership,
negação de domínio, filesystem/persistence guarantees, SQL, cross-process,
helpers arbitrários, contratos interprocedurais e taint engine genérico.

## 7. Invariantes e segurança

1. Guard-derived guarantee não é persistence nem external protocol guarantee.
2. Somente failure mapping literal `success=False` é terminal v1.
3. Fact vale apenas para success return dominado e mesma geração.
4. Predicate opaco nunca vira `_DomainFact`.
5. Complexity desconhecida falha fechado apenas para a derivação de guards.
6. Target não é importado, executado ou ampliado para helpers.
7. IDs de geração e evidências dependem somente da estrutura AST.

## 8. Entradas e saídas

As entradas públicas permanecem source snapshot, producer e consumer. O novo
`_GuardDerivedFact` frozen contém identidade do binding, constraint, valor
canônico opcional, referências do guard/return e generation ID. A saída pública
continua `ExecutionPathReport`.

## 9. Pseudocódigo independente de linguagem

```text
inicializar uma geração para cada parâmetro
percorrer statements de cima para baixo
para assignment simples:
    alias recebe a mesma identidade
    qualquer outra expressão cria nova geração
para if atômico sem else cujo corpo é failure return:
    registrar a condição inversa para a geração atual
para success return explícito:
    resolver o field retornado até sua identidade
    anexar somente facts ativos dessa identidade
se qualquer região relevante exceder o gate:
    não derivar guarantees de guard
entre múltiplos success returns:
    manter somente constraints comuns
converter truthy/equal-literal em DomainFact
manter opaque predicate apenas como diagnóstico
```

## 10. Fluxo principal

1. HERMES-0020 seleciona success returns e mapping field.
2. O walker sequencial calcula binding generations e guards dominantes.
3. Facts são intersectados entre success returns.
4. Facts fechados enriquecem `_ProducerEvidence`.
5. A matriz existente compara producer e consumer.
6. Opaque facts geram limitation específica.

## 11. Erros, limites e fronteiras

Else relevante, nested if, loops, match, try, boolean composto, destructuring ou
mutation não suportada invalidam a derivação. Guard em outra variável, depois
do return ou antes de redefinition não se aplica. Transform cria nova geração.

## 12. Critérios de aceitação

- **AC-01:** truthiness guard produz success-path guarantee.
- **AC-02:** truthy producer e consumer produzem NO_MISMATCH.
- **AC-03:** equality guard produz literal domain.
- **AC-04:** mesmo literal produz NO_MISMATCH.
- **AC-05:** literals diferentes produzem CONFIRMED_MISMATCH.
- **AC-06:** failure return não contamina success contract.
- **AC-07:** guard precisa dominar o success return.
- **AC-08:** alias simples preserva guarantee.
- **AC-09:** redefinition invalida guarantee.
- **AC-10:** transform posterior não herda fact.
- **AC-11:** guard sobre outra variável é ignorado.
- **AC-12:** opaque predicate não vira DomainFact.
- **AC-13:** opaque predicate usa diagnóstico específico.
- **AC-14:** multiple returns usam interseção segura.
- **AC-15:** return sem dominância impede guarantee comum.
- **AC-16:** branch complexo falha fechado.
- **AC-17:** loops e match falham fechados.
- **AC-18:** generations impedem correlação por nome.
- **AC-19:** HERMES-0019 permanece compatível.
- **AC-20:** HERMES-0020 permanece compatível.
- **AC-21:** HERMES-0021 continua independente.
- **AC-22:** ausência de path local continua NO_EXECUTABLE_PATH.
- **AC-23:** fatos, evidências e resultado são determinísticos.
- **AC-24:** target nunca é executado.
- **AC-25:** Lucre batch_id não recebe guarantee inventada.

## 13. Plano de testes

Novo arquivo cobre AC-01–AC-18 e AC-22–AC-24. Suítes HERMES-0019/0020 cobrem
AC-19/20, persistence/Audit Round cobre AC-21 e dogfood Lucre read-only cobre
AC-25. Full suite e build completam a validação.

## 14. Arquivos provavelmente afetados

- esta especificação;
- `execution_path_review.py`;
- `tests/test_execution_path_guard_guarantees.py`.

## 15. Riscos conhecidos

Dominância aproximada, alias atemporal, redefinition ignorada, predicado opaco
promovido indevidamente e múltiplos returns unidos por OR são os principais
riscos. O gate conservador deve preferir evidência insuficiente.

## Evidência de implementação

| Contrato | Evidência em 2026-08-20 |
|---|---|
| RED | Fixture truthy retornou `CONFIRMED_MISMATCH` antes da implementação |
| AC-01–AC-18, AC-22–AC-24 | `test_execution_path_guard_guarantees.py`: 12 passed |
| AC-19–AC-21 | Grupo execution-path/Audit Round/persistence/ranking: 93 passed |
| Regressões mission/Analysis Pack | 42 passed |
| Full suite | 683 passed, 11 skipped, 0 failed |
| AC-25 | Dogfood Lucre: origin `cursor.lastrowid`, domain ausente e `NO_EXECUTABLE_PATH` |
| Distribuição | wheel e sdist construídos com sucesso |

Os 11 skips mantêm os limites conhecidos do ambiente Windows e o dogfood
externo opt-in. Nenhuma evidência foi obtida executando ou importando o target.
