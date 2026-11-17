---
title: State Guard Effect Coverage
status: Implementado
---

# HERMES-0025 — State Guard Effect Coverage

## 1. Contexto

As lentes atuais comprovam dataflow Python, garantias locais de producer e
contratos de persistência. Nenhuma responde diretamente se um literal de estado
declarado consegue atravessar guards suportados e alcançar uma chamada esperada.

## 2. Problema confirmado

Um guard pode excluir um estado que, pelo contrato explícito do request, deveria
alcançar um efeito. A presença textual do efeito não prova reachability e a
ausência de evidência não autoriza finding.

## 3. Explicação em linguagem natural

O solicitante informa a operação, a origem estrutural do estado, um valor
literal e uma chamada esperada. A lente percorre apenas controle de fluxo Python
simples. Se provar um caminho até a chamada, há alinhamento. Se provar que todos
os caminhos terminam antes dela, há mismatch. Construções desconhecidas falham
fechado.

## 4. Comportamento atual

`execution-path-review` compara producer e consumer. `persistence-contract-review`
interpreta contratos SQL. Nenhuma dessas responsabilidades inclui cobertura de
um literal concreto por guards até uma chamada.

## 5. Comportamento desejado

Criar a lens independente `state-guard-effect-review`, com core puro sobre
`SourceDocument`, wrapper read-only, normalizer próprio e auditor próprio na
Audit Round. Ela não interpreta nomes de negócio, SQL ou o corpo do callee.

## 6. Fora do escopo

- descoberta automática de estados ou intenção de negócio;
- symbolic execution geral ou prova runtime;
- SQL, mutation facts e outcomes da persistence lens;
- propagação interprocedural do state binding;
- `and`, `or`, loops, `try`, `match`, callbacks e dispatch dinâmico;
- nova skill pública ou CLI.

## 7. Invariantes e regras de segurança

1. Estado, binding e effect vêm somente do request.
2. Somente `str`, `int`, `bool` e `None` são literais válidos; bool não é int.
3. Finding exige cobertura completa sem path desconhecido.
4. Um path aceito basta para alinhamento, pois a pergunta é existencial.
5. Ausência do effect produz evidência insuficiente, nunca mismatch.
6. Snapshot, scope, locators e ordenação seguem os contratos existentes.
7. A lens não recebe facts, reports, findings, classifications ou reachability
   de outra lens.
8. Código e fixtures de produção permanecem independentes de consumidores.

## 8. Entradas e saídas

`StateBindingRequest` contém `source_parameter` e `field` opcional.
`StateGuardEffectReviewRequest` contém operation, binding, input literal,
expected call effect e structural scope. O report frozen contém classification,
reachability, facts de path, findings, evidências, limitations e scope.

Classifications usam os valores existentes: `CONFIRMED_CONTRACT_MISMATCH`,
`POTENTIAL_CONTRACT_MISMATCH`, `CONTRACT_STRUCTURALLY_ALIGNED` e
`INSUFFICIENT_EVIDENCE`. A v1 reserva potential.

## 9. Pseudocódigo independente de linguagem

```text
validar o request sem interpretar seus nomes
resolver exatamente uma definição da operação
resolver o parâmetro e o field opcional
localizar chamadas estruturais do effect no corpo
se operação, binding ou effect não forem resolvíveis:
    retornar evidência insuficiente

criar a geração inicial do binding
percorrer os statements e branches em ordem
para cada guard atômico suportado sobre a geração ativa:
    avaliar o literal e seguir o branch factível
para guard independente:
    manter ambos os branches estruturalmente possíveis
para construção relevante não suportada:
    marcar o path como desconhecido
para return ou raise:
    marcar o path como rejeitado
para chamada do effect:
    marcar o path como aceito

se algum path foi aceito:
    retornar alinhado
senão, se todos os paths foram rejeitados:
    retornar mismatch confirmado com um finding
senão:
    retornar evidência insuficiente sem finding
```

## 10. Fluxo principal

Request → snapshot controlado → definição única → binding/generations → walker
intraprocedural → estados ACCEPTED/REJECTED/UNKNOWN → agregação → normalização.

## 11. Guards, paths, effects e diagnostics

São suportados `==`, `!=`, `in` e `not in` contra literal ou set/tuple/list
inteiramente literal; aliases diretos; `return`, `raise`, `else` e nested `if`
dentro do subset. Reassignment, transform ou mutation relevante invalidam a
geração. O effect v1 é chamada direta cujo nome terminal coincide exatamente
com o símbolo declarado; a expressão completa fica na evidência.

Diagnostics fechados incluem: `STATE_OPERATION_NOT_UNIQUE`,
`STATE_SOURCE_PARAMETER_NOT_FOUND`, `STATE_BINDING_NOT_DISCOVERABLE`,
`STATE_BINDING_REDEFINED`, `STATE_BINDING_TRANSFORMED`,
`STATE_GUARD_COLLECTION_DYNAMIC`, `STATE_GUARD_HELPER_OPAQUE`,
`STATE_GUARD_BOOLEAN_COMPOSITION_UNSUPPORTED`,
`STATE_CONTROL_FLOW_UNSUPPORTED`, `EXPECTED_EFFECT_CALL_DYNAMIC`,
`EXPECTED_EFFECT_NOT_FOUND`, `NO_ANALYZABLE_STATE_PATH` e
`STATE_PATH_PARTIALLY_UNKNOWN`.

## 12. Finding, reachability e integrações

Somente mismatch confirmado cria `STATE_EFFECT_COVERAGE_MISMATCH`, severity
medium e evidence strength confirmed. Aligned e insufficient não são rankable.
Reachability é CONFIRMED para path estrutural integral até effect ou terminal e
UNKNOWN em qualquer lacuna relevante.

O normalizer HERMES-0017 é explícito. A HERMES-0018 ganha um quarto auditor com
ID próprio, mesmo snapshot, input frozen, isolamento de falha e normalização
posterior a todos os outcomes. A HERMES-0024 permanece semanticamente isolada.

## 13. Critérios de aceitação

- **AC-01:** membership literal aceito produz aligned.
- **AC-02:** membership literal rejeitado produz mismatch confirmado.
- **AC-03:** equality aceita e rejeita corretamente.
- **AC-04:** inequality aceita e rejeita corretamente.
- **AC-05:** set, tuple e list inteiramente literais são suportados.
- **AC-06:** str, int, bool e None preservam tipo; bool não colapsa em int.
- **AC-07:** parâmetro direto é resolvido.
- **AC-08:** field por subscript literal é resolvido.
- **AC-09:** field por `.get()` literal é resolvido.
- **AC-10:** alias direto preserva identidade e geração.
- **AC-11:** reassignment invalida o guard anterior.
- **AC-12:** transformação invalida o guard anterior.
- **AC-13:** guard sobre binding diferente não gera prova.
- **AC-14:** coleção dinâmica retorna insufficient sem finding.
- **AC-15:** helper predicate opaco retorna insufficient sem finding.
- **AC-16:** composição booleana relevante retorna insufficient.
- **AC-17:** nested if dentro do subset é avaliado.
- **AC-18:** alternate path aceito produz aligned.
- **AC-19:** rejected mais unknown produz insufficient.
- **AC-20:** accepted mais unknown produz aligned.
- **AC-21:** múltiplos rejected produzem um único finding.
- **AC-22:** effect ausente produz insufficient.
- **AC-23:** effect após terminal inevitável produz mismatch.
- **AC-24:** chamada dinâmica produz insufficient.
- **AC-25:** loop, try e match relevantes falham fechado.
- **AC-26:** output, evidências, finding ID e JSON são determinísticos.
- **AC-27:** definição ausente ou duplicada da operação produz insufficient.
- **AC-28:** source parameter ausente produz diagnostic controlado.
- **AC-29:** aligned e insufficient não são rankable.
- **AC-30:** quarto auditor compartilha um único snapshot e isola falhas.
- **AC-31:** a lens não consome tipos ou outcomes da persistence lens.
- **AC-32:** benchmark buggy produz mismatch e finding esperados.
- **AC-33:** benchmark fixed produz aligned e zero findings.
- **AC-34:** AC-32 e AC-33 usam exatamente o mesmo request.
- **AC-35:** produção não contém regra, nome ou revisão específica do projeto consumidor.

## 14. Plano de testes e arquivos afetados

Primeiro executar fixtures neutras em `tests/test_state_guard_effect_review.py`.
Depois cobrir normalização e Audit Round, regressões HERMES-0017–0024 e, por
último, controles históricos read-only com `git show`, sem checkout.

Arquivos previstos: esta spec; models e review próprios; finding ranking; Audit
Round; exports necessários; testes da lens, ranking e rodada.

## 15. Riscos conhecidos

Os maiores riscos são tratar UNKNOWN como rejeição, aceitar aliases ou
collections dinâmicas, confundir presença textual com reachability, misturar
bool/int, acoplar a persistence lens e deixar nomes do benchmark influenciarem
produção.

## Evidências de implementação

- Primeiro RED: os módulos da lens não existiam; depois, AC-01/AC-02 ficaram
  verdes com models e core próprios.
- AC-24 RED: callback relevante retornava `EXPECTED_EFFECT_NOT_FOUND`; após a
  implementação genérica, callback, call expression e mapping dispatch retornam
  `EXPECTED_EFFECT_CALL_DYNAMIC`.
- Core, ranking e Audit Round: 88 passed.
- Regressões execution-path e persistence: 75 passed.
- Regressões amplas de reader, mission audit, Analysis Pack, execução, CLI e Git:
  246 passed, 1 skipped.
- Benchmark histórico read-only: o mesmo request serializado produziu mismatch
  confirmado/finding no buggy e aligned/zero findings no fixed. Uma fixture
  neutra para call effect no RHS foi criada antes da ampliação genérica exigida.
- Full suite: 754 passed, 11 skipped, 0 failed em 66,95 segundos.
- Build: `hermes_ops-0.1.0.tar.gz` e
  `hermes_ops-0.1.0-py3-none-any.whl` construídos com sucesso, incluindo os dois
  módulos da lens.
- Produção verificada sem nomes, estados, revisões ou regras específicas do
  benchmark e sem dependência da persistence lens.
