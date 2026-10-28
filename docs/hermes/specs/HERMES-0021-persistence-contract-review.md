---
spec_id: HERMES-0021
title: Persistence Contract Review v1
version: 1
status: Implementado
date: 2026-08-20
depends_on:
  - HERMES-0017
  - HERMES-0018
  - HERMES-0020
---

# HERMES-0021 — Persistence Contract Review v1

## 1. Contexto

O execution-path-review prova propagação Python e separa origin de domain, mas
deliberadamente não interpreta persistência. O caso real contém INSERT,
`lastrowid`, propagação local e SELECT posterior. Uma lente independente pode
validar o alinhamento estrutural desses intents sem afirmar que houve commit ou
que uma row existe.

## 2. Problema confirmado

Não existe auditor que represente write intent, identity binding, read
requirement ou state-transition intent. Tratar qualquer `.execute` como SQL ou
promover `lastrowid` a persistência seria inseguro. A análise precisa ser
SQLite-specific, direcionada e fail-closed.

## 3. Explicação em linguagem natural

O usuário declara a tabela e coluna de identidade esperadas. A lente procura
somente SQL literal de formatos pequenos, liga o cursor do INSERT ao
`lastrowid`, acompanha esse valor por Python explícito e confere se o SELECT usa
a tabela e coluna declaradas. Alinhamento significa que o código pede operações
coerentes; não significa que o banco as executou ou confirmou.

## 4. Comportamento atual

Audit Round possui dois auditores independentes. HERMES-0017 normaliza findings
de code-audit e execution-path-review. Nenhum modelo representa contratos de
persistência e nenhum auditor interpreta SQL.

## 5. Comportamento desejado

- Review direcionada por producer, consumer, SQLite dialect, table e key.
- Pure core sobre source documents já autorizados.
- Recognizer fechado de INSERT, SELECT e UPDATE literais.
- Facts frozen de intent, identity, read e state transition.
- Aligned, confirmed mismatch, potential mismatch ou insufficient evidence.
- Findings somente para divergência demonstrada.
- Normalizer HERMES-0017 fechado.
- Terceiro auditor independente consumindo o mesmo snapshot uma única vez.

## 6. Fora do escopo

- persistência confirmada, commit ou transaction guarantee;
- parser SQL genérico;
- JOIN, subquery, CTE, OR, RETURNING, ON CONFLICT ou múltiplos statements;
- SQL dinâmico, f-string ou concatenação;
- schema discovery e FK reasoning;
- cross-process propagation;
- descoberta global de persistence contracts;
- generic DB-API ou target table inference;
- execução/import do target, database access ou rede.

## 7. Invariantes e regras de segurança

1. Persistence intent não é persistence guarantee.
2. Somente dialect `SQLITE_DBAPI` é aceito.
3. SQL fora da gramática falha fechado e não gera mismatch confirmado.
4. Table/key vêm do request, não de heurística.
5. Structural scope é aplicado antes da leitura e nunca ampliado para schema.
6. O pure core não acessa filesystem.
7. Auditores não consomem resultados uns dos outros.
8. Resultados, evidence refs, IDs e JSON são determinísticos.
9. Nenhum target é importado, executado ou conectado.

## 8. Entradas e saídas

`PersistenceContractReviewRequest` é frozen e contém producer, consumer,
dialect, target table, identity column, expected state opcional e structural
scope. O relatório nativo frozen contém classificação, facts, findings,
evidence refs, limitations, path e reachability local.

Facts: `WriteIntentFact`, `IdentityBindingFact`, `ReadRequirementFact` e
`StateTransitionIntentFact`. Não existe `PersistenceConfirmedFact`.

## 9. Pseudocódigo independente de linguagem

```text
validar request e usar somente documentos do snapshot
localizar producer e consumer únicos
no producer:
    reconhecer INSERT literal fechado
    ligar o cursor exatamente àquele INSERT
    ligar variável = cursor.lastrowid ao mesmo INSERT
    coletar UPDATE intents suportados
no consumer:
    reconhecer SELECT literal fechado seguido de fetchone
    ligar placeholder à identidade Python usada
    reconhecer early return quando a row não é truthy
procurar caminho Python local explícito entre producer e consumer

se SQL for dinâmico ou shape não suportado:
    retornar evidência insuficiente com limitation
se facts essenciais estiverem ausentes:
    retornar evidência insuficiente
se table ou key observadas contradisserem o target explícito:
    retornar confirmed contract mismatch com finding
se identidade consumida tiver origin explicitamente diferente:
    retornar confirmed contract mismatch
se facts estiverem alinhados:
    retornar contract structurally aligned

sempre registrar transaction semantics unknown
nunca afirmar commit, row existente ou estado persistido
```

## 10. Fluxo principal

1. Validar identificadores e dialect.
2. Parsear somente source documents fornecidos.
3. Reconhecer SQL literal integral pela gramática v1.
4. Extrair facts e bindings por função.
5. Construir dataflow local mínimo e independente.
6. Comparar facts com target explícito.
7. Produzir relatório nativo determinístico.
8. Normalizar somente findings mismatch.
9. Executar como terceiro auditor sobre o snapshot compartilhado.

## 11. Erros, limites e fronteiras

- Dialect inválido ou request malformado falha contratualmente.
- Símbolo ambíguo produz insufficient evidence.
- Query não literal produz `DYNAMIC_SQL_UNSUPPORTED`.
- SQL literal fora da gramática produz `SQL_SHAPE_UNSUPPORTED`.
- Placeholder/binding incompatível produz limitation.
- Sem caller local, reachability é unknown.
- Transaction semantics unknown não impede alignment estrutural.
- Expected state ausente impede state mismatch.

## 12. Critérios de aceitação

- **AC-01:** INSERT literal produz WriteIntentFact.
- **AC-02:** table e columns são extraídas deterministicamente.
- **AC-03:** placeholders ligam-se à tuple posicional.
- **AC-04:** SQL dinâmico falha fechado.
- **AC-05:** cursor liga-se ao INSERT específico.
- **AC-06:** `cursor.lastrowid` produz IdentityBindingFact.
- **AC-07:** dialect não suportado falha fechado.
- **AC-08:** SELECT literal produz ReadRequirementFact.
- **AC-09:** predicate column e value identity são extraídos.
- **AC-10:** fetchone + early false-return registra success guard.
- **AC-11:** UPDATE restrito produz StateTransitionIntentFact.
- **AC-12:** UPDATE intent não vira persisted guarantee.
- **AC-13:** table/key alinhadas produzem structural alignment.
- **AC-14:** table divergente produz confirmed mismatch.
- **AC-15:** key divergente produz confirmed mismatch.
- **AC-16:** origins distintas não são correlacionadas por nome.
- **AC-17:** dois INSERTs preservam cursores separados.
- **AC-18:** SELECT constante não liga generated identity.
- **AC-19:** ausência de path local mantém reachability unknown.
- **AC-20:** stdout → CLI não cria path.
- **AC-21:** transaction semantics permanecem unknown.
- **AC-22:** schema não é descoberto fora do scope.
- **AC-23:** results/evidence refs são determinísticos e sanitizados.
- **AC-24:** target nunca é importado ou executado.
- **AC-25:** pure core opera apenas sobre snapshot.
- **AC-26:** normalizer mapeia strength/severity sem inflação.
- **AC-27:** terceiro auditor é isolado e usa leitura única.
- **AC-28:** Lucre produz intents sem commit/handoff inventados.
- **AC-29:** mesmo nome não basta para correlacionar tables/origins.
- **AC-30:** SQL não suportado produz limitation, não confirmed finding.

## 13. Plano de testes

`tests/test_persistence_contract_review.py` cobre parsing, facts, alignment,
mismatches e negativos AC-01 a AC-24/29/30. Testes de ranking cobrem AC-26;
Audit Round cobre AC-25/27; dogfood read-only cobre AC-28. Regressões de
HERMES-0015–0020 e full suite são obrigatórias.

## 14. Arquivos provavelmente afetados

- esta spec;
- novos módulos de models e review;
- `finding_ranking.py`;
- `audit_round.py`;
- testes de persistence, ranking e audit round.

CLI, catálogo público e executor não precisam mudar na v1 interna.

## 15. Riscos conhecidos

- Regex permissiva pode aceitar SQL parcialmente; matching deve cobrir a string
  inteira.
- `lastrowid` pode ser ligado ao cursor errado se assignments forem ignorados.
- Mesmo nome de variável em funções diferentes não prova identidade.
- Table diferente pode ser relação legítima; mismatch exige target explícito.
- Context manager não prova commit.
- Integração do terceiro auditor pode quebrar ordenação, isolamento ou ranking
  único.

## Evidência de implementação

| Contrato | Evidência em 2026-08-20 |
|---|---|
| AC-01–AC-25, AC-29–AC-30 | `tests/test_persistence_contract_review.py`: 12 passed |
| AC-26 | `tests/test_finding_ranking.py`, incluído no grupo Audit Round/ranking: verde |
| AC-27 | `tests/test_audit_round.py`: snapshot único, permutações e falha isolada verdes |
| AC-28 | Dogfood read-only Lucre: aligned, reachability unknown, 1 write, 1 identity, 2 reads, 8 state intents |
| Regressões HERMES-0019/0020 | 31 passed |
| Full suite | 671 passed, 11 skipped, 0 failed |
| Distribuição | wheel e sdist construídos com sucesso |

Os 11 skips são os mesmos limites de ambiente: um dogfood externo opt-in, nove
fixtures de symlink indisponíveis no Windows e uma fixture portátil de permissão.
Nenhuma evidência afirma commit, existência de row ou estado persistido.
