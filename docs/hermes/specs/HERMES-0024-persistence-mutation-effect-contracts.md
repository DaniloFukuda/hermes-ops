---
spec_id: HERMES-0024
title: Persistence Mutation Effect Contracts
version: 1
status: Implementado
date: 2026-08-21
depends_on: [HERMES-0017, HERMES-0018, HERMES-0019, HERMES-0021]
---

# HERMES-0024 — Persistence Mutation Effect Contracts

## 1. Contexto

Um defeito histórico real do Lucre cancelava uma sessão no armazenamento
legado, embora a operação pertencesse a outro contrato persistente. O fix
passou a usar a tabela, chave e transição esperadas. HERMES-0021 cobre hoje
write/identity/read, mas não um efeito UPDATE dirigido por contrato.

## 2. Problema confirmado

Uma mutation alcançável pode escrever em table/key/state incompatíveis e ainda
retornar sucesso. A lente atual não compara esse efeito com uma expectativa
explícita, mesmo quando o SQL e o call path são observáveis.

## 3. Explicação em linguagem natural

O caller informa qual operação revisar e qual efeito estrutural espera. O
Hermes acompanha somente calls Python suportadas até um UPDATE local, descreve
o intent e compara table, key e, opcionalmente, um estado literal. Intent
observado não prova commit nem persistência real.

## 4. Comportamento atual

`PersistenceContractReviewRequest` exige producer/consumer e a conclusão
principal depende de INSERT, lastrowid e SELECT. UPDATEs geram
`StateTransitionIntentFact`, mas não são revisados como operação independente.

## 5. Comportamento desejado

Adicionar request mutation frozen, fact de mutation agrupado, call path
dirigido, parser UPDATE restrito reutilizado, comparação determinística e
integração no auditor persistence existente, normalizer e Audit Round.

## 6. Fora do escopo

SQL genérico, schema/FK discovery, commit/transaction guarantee, cross-process,
efeitos de API, consistência da resposta success, identity-origin mismatch,
symbolic execution, call graph arbitrário e semântica inferida de nomes.

## 7. Invariantes e segurança

- O target nunca é importado ou executado.
- Table/key/state esperados vêm apenas do request.
- Guard opcional é selector estrutural, não semântica.
- SQL/path ambíguo falha fechado.
- Snapshot e paths públicos permanecem controlados e sanitizados.
- Mutation intent não significa persisted effect.
- Nenhum nome, table, path ou SHA de consumidor é regra de produção.

## 8. Entradas e saídas

`PersistenceMutationReviewRequest` recebe operation, dialect, target table,
identity column, state column/value opcionais em par, activation guard opcional
e structural scope. A saída reutiliza `PersistenceContractReport`, incluindo
mutation intents, path, reachability, findings, evidências e limitations.

## 9. Pseudocódigo independente de linguagem

```text
validar contrato explícito
localizar exatamente uma entry operation
se guard foi pedido, localizar seus branches na entry
acompanhar calls suportadas somente a partir desses branches
acompanhar SQL e params encaminhados sem redefinição
extrair UPDATEs suportados e agrupar efeitos canônicos
se nenhum efeito relevante for provado, retornar insufficient
comparar primeiro table; se diferente, emitir apenas wrong-table
comparar key; se diferente, emitir wrong-key
se state foi pedido, comparar o literal da coluna solicitada
se todos os paths concordam, retornar aligned ou confirmed mismatch
se paths analisáveis divergem, retornar potential
```

## 10. Fluxo principal

Request → snapshot existente → definitions → guard slice → call/dataflow
→ UPDATE intents → deduplication → comparison → normalization.

## 11. Erros, limites e fronteiras

Definition/guard/path ausente, dynamic SQL, forwarding ambíguo, structural
interpolation, API-only e state opaco retornam `INSUFFICIENT_EVIDENCE` com
limitation determinística. Paths alinhados e incompatíveis misturados retornam
`POTENTIAL_CONTRACT_MISMATCH`. Updates inalcançáveis são ignorados.

## 12. Critérios de aceitação

- **AC-01:** mutation alinhada retorna structurally aligned.
- **AC-02:** wrong table retorna confirmed mismatch.
- **AC-03:** wrong key retorna confirmed mismatch.
- **AC-04:** expected state diferente retorna confirmed mismatch.
- **AC-05:** assignments extras não impedem comparação dirigida.
- **AC-06:** state omitido não é inferido por nome.
- **AC-07:** dynamic SQL retorna insufficient.
- **AC-08:** unrelated update é ignorado.
- **AC-09:** zero paths retorna insufficient.
- **AC-10:** paths divergentes nunca retornam aligned.
- **AC-11:** aligned mais incompatible retorna potential.
- **AC-12:** nomes não possuem peso semântico.
- **AC-13:** call qualificado inequívoco é suportado.
- **AC-14:** SQL/params forwarding local é preservado.
- **AC-15:** static core seguro é aceito e core estrutural dinâmico é bloqueado.
- **AC-16:** mesma key com origem semanticamente errada não cria identity mismatch.
- **AC-17:** API-only retorna insufficient.
- **AC-18:** evidências cobrem entry, edges e SQL.
- **AC-19:** reachability confirmed exige path completo.
- **AC-20:** resultado é frozen e determinístico.
- **AC-21:** target nunca é executado.
- **AC-22:** aligned/insufficient não são rankeáveis.
- **AC-23:** Audit Round reutiliza um único snapshot e isola falhas.
- **AC-24:** mesmo request no histórico buggy confirma wrong-table.
- **AC-25:** mesmo request no histórico fixed retorna aligned.
- **AC-26:** produção não contém regra específica do benchmark.

## 13. Plano de testes

Fixtures genéricas cobrem AC-01–AC-23 e AC-26. SourceDocuments carregados por
Git read-only cobrem AC-24/25 com o mesmo request. Suites persistence, ranking,
Audit Round, execution, mission, analysis, CLI e full suite cobrem regressão.

## 14. Arquivos provavelmente afetados

Esta spec; persistence models/review; finding ranking; Audit Round; exports e
testes de mutation, persistence, ranking e Audit Round.

## 15. Riscos conhecidos

F-string estrutural ambíguo, SQL forwarded redefinido, branch selector amplo,
efeitos equivalentes duplicados e updates não relacionados podem gerar falso
positivo. Todos devem falhar fechado ou ser provados por fluxo explícito.

### Evidência de implementação

Validado em 2026-08-21: fixtures genéricas e integrações focadas verdes; suíte
completa com 707 testes aprovados e 11 pulados por limitações ambientais já
declaradas; wheel e sdist construídos; benchmark Git read-only executado com o
mesmo request, obtendo wrong-table confirmado no snapshot defeituoso e
alinhamento estrutural sem findings no snapshot corrigido. AC-24/25 permanecem
dogfood externo deliberadamente não automatizado: a política do repositório
exige que testes com Git criem repositórios temporários, portanto revisões de um
projeto consumidor não podem ser dependência da suíte Hermes.
