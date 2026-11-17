# Hermes Core Baseline 0015–0026

## Identificação do freeze

- **Baseline name:** `HERMES_CORE_BASELINE_0015_0026`
- **Status:** `FROZEN_BASELINE_WITH_NON_BLOCKING_DEBT`
- **Verdict de readiness:** `HERMES_CORE_READY_WITH_NON_BLOCKING_DEBT`
- **Freeze date:** 2026-08-23
- **Branch:** `feature/execution-path-review-20260820`
- **HEAD:** `08ad7bf919bdfc889d3be81c6ce3095029f33ee8`
- **Scope:** arquitetura e contratos do core entregues por HERMES-0015–0026.

Este registro congela a baseline semântica validada. Freeze significa que uma
mudança na surface exige nova spec e compatibility analysis; não significa
imutabilidade eterna nem impede evoluções internas semanticamente neutras.

## Baseline scope

- **HERMES-0015 — Execution Path Review v1:** compara producer e consumer por
  um caminho executável e evidência estrutural dirigida.
- **HERMES-0016 — Analysis Schema Alignment:** alinha o schema do
  `MissionEvidencePack` com o loader sem relaxar validação estrita.
- **HERMES-0017 — Unified Finding Ranking:** preserva reports nativos, normaliza
  findings acionáveis e os ordena deterministicamente.
- **HERMES-0018 — Independent Audit Round:** executa auditors independentes
  sobre um snapshot único, com isolamento e ranking agregado único.
- **HERMES-0019 — Explicit Python Dataflow Resolution:** acompanha dataflow
  Python explicitamente demonstrado e respeita fronteiras externas.
- **HERMES-0020 — Producer Guarantee Semantics:** separa origem sintática de
  domínio demonstrável e preserva falha fechada.
- **HERMES-0021 — Persistence Contract Review v1:** analisa intents estruturais
  de write, identidade e read sob contrato SQL dirigido.
- **HERMES-0022 — Guard-Derived Producer Guarantees:** deriva guarantees apenas
  de guards atômicos e success paths comprovados.
- **HERMES-0023 — Path-Only Outcome Refinement:** distingue path provado sem
  contrato comparável, sem fabricar mismatch ou finding.
- **HERMES-0024 — Persistence Mutation Effect Contracts:** compara mutations
  SQL alcançáveis com table, key e state explicitamente declarados.
- **HERMES-0025 — State Guard Effect Coverage:** verifica se um literal de state
  atravessa guards suportados até o effect esperado.
- **HERMES-0026 — Minimal Structural Kernel Consolidation:** consolida somente
  terminal symbol e source locator e torna o benchmark histórico hermético.

As specs permanecem a fonte normativa detalhada; este documento não as
substitui nem reinterpreta.

## Frozen invariants

1. **Controlled reading:** source entra por leitura controlada, sem execução do
   target.
2. **Structural scope fechado:** somente o root e paths explicitamente
   autorizados participam da análise; não há descoberta de pais ou siblings.
3. **Fail-closed behavior:** ambiguidade, construção dinâmica ou evidência
   incompleta não é promovida a confirmação.
4. **Evidence refs determinísticas e sanitizadas:** locators públicos usam paths
   relativos seguros e linhas válidas.
5. **Finding IDs determinísticos:** identidade canônica, não ordem incidental,
   determina o ID.
6. **Independência semântica nativa:** cada auditor decide em seu próprio
   modelo, classification e report.
7. **Zero semantic fact sharing:** auditors não recebem facts ou conclusões uns
   dos outros.
8. **Single snapshot em Audit Round:** todos os auditors da rodada recebem a
   mesma fotografia controlada.
9. **Failure isolation:** falha de um auditor não fabrica finding nem invalida
   outcomes nativos dos demais.
10. **Normalize after native outcomes:** normalização ocorre somente depois de
    todos os outcomes nativos.
11. **Rank once:** o conjunto normalizado é ordenado uma única vez por rodada.
12. **Sem finding artificial:** aligned, insufficient e path-only não geram
    finding acionável sintético.
13. **Kernel estrutural sem domínio:** terminal symbol e source locator não
    carregam semântica de auditor ou consumidor.
14. **Benchmark histórico hermético:** a prova automatizada necessária usa
    sources controlados, o mesmo request e nenhuma dependência de checkout
    consumidor ou Git externo.
15. **Deterministic serialization:** mesmos inputs canônicos produzem o mesmo
    JSON independentemente da ordem admissível de requests/evidências.

Estas invariants são parte normativa do freeze.

## Frozen semantic surfaces

As seguintes surfaces estão congeladas semanticamente:

- semântica das classifications existentes;
- contrato `EvidenceRef`;
- envelope `RankableFinding`;
- semântica de identidade de `finding_id`;
- ranking key, ordering e tie-breaks;
- invariants de orquestração da Audit Round;
- comportamento de structural scope e controlled reading;
- comportamento fail-closed;
- formato canônico `relative/path.py:<line>` do source locator;
- `terminal_symbol`: `Name.id`, terminal `Attribute.attr` e `None` para callable
  não estaticamente suportada;
- schemas públicos estabilizados de requests e results.

Qualquer delta nessas surfaces exige spec e compatibility analysis. O freeze
não transforma helpers module-local em API pública nem amplia exports.

## Flexible internals

Continuam flexíveis, desde que não alterem a semantic surface congelada sem
spec:

- layout interno de helpers;
- implementação dos walkers;
- performance e caching interno;
- novos auditors e seus novos native reports;
- novos contracts introduzidos por novas specs;
- corpus histórico adicional;
- diagnostics mais ricos que preservem classifications e contratos;
- futuras camadas construídas acima do core.

Mudanças internas comprovadamente sem semantic delta não reabrem o freeze.

## Non-blocking debt register

Nenhum debt HIGH integra este registro.

### MEDIUM — Execution-path complexity hotspot

- **Descrição:** a resolução execution-path concentra dataflow, guards,
  forwarding e caracterização de evidência em um módulo interno extenso.
- **Consequência:** eleva custo de revisão e risco de regressão em futuras
  extensões semânticas.
- **Timing recomendado:** antes de ampliar substancialmente o subset Python;
  qualquer consolidação deve provar semantic delta zero.
- **Freeze blocker:** NO.

### LOW — Duplicação analyzer-local não compartilhável hoje

- **Descrição:** permanecem decisões e pequenas representações parecidas cujo
  significado depende do auditor. HERMES-0026 consolidou somente as duas
  equivalências comprovadas.
- **Consequência:** alguma manutenção paralela continua necessária.
- **Timing recomendado:** reavaliar apenas quando testes demonstrarem uma nova
  equivalência estrita; não introduzir common walker ou common facts.
- **Freeze blocker:** NO.

### LOW — Public API asymmetry

- **Descrição:** capacidades internas e integrações da Audit Round não possuem
  necessariamente wrappers/exports públicos simétricos.
- **Consequência:** consumidores futuros podem precisar de uma camada de
  integração explícita, em vez de assumir uma API uniforme inexistente.
- **Timing recomendado:** tratar somente quando um use case público concreto
  exigir contrato próprio.
- **Freeze blocker:** NO.

### LOW — Historical corpus ainda pequeno

- **Descrição:** os benchmarks históricos automatizados cobrem poucos pares
  buggy/fixed, embora preservem causalidade e hermeticidade.
- **Consequência:** a variedade empírica de regressões reais ainda é limitada.
- **Timing recomendado:** adicionar casos quando novos incidentes forem
  validados, sempre com request cego idêntico e sources mínimos honestos.
- **Freeze blocker:** NO.

## Post-freeze change policy

Qualquer mudança que altere classification semantics, finding identity,
ranking semantics, evidence locator, structural scope, fail-closed behavior,
Audit Round ordering, auditor isolation ou schema público de request/result
exige obrigatoriamente:

1. nova spec versionada;
2. characterization automatizada da semântica anterior;
3. rationale da mudança;
4. declaração explícita de compatibilidade ou breaking change;
5. regressões proporcionais ao contrato afetado;
6. evidência concreta de validação.

Snapshots esperados não podem ser simplesmente atualizados para ocultar delta.
Mudanças internas sem semantic delta podem prosseguir sem reabrir o freeze,
observadas as regras gerais de especificação do repositório.

## Next-layer boundary

Futuras camadas devem consumir o core por cima, sem modificar sua epistemologia:

```text
historical context
    -> candidate selection
    -> fresh audit
    -> fresh evidence refs
    -> conclusion
```

Uma camada de memória/retrieval pode armazenar histórico, recuperar contexto,
sugerir arquivos, símbolos, missões e candidatos e ordenar investigações. Ela
não pode:

- tornar memória evidência final;
- confirmar finding apenas por histórico;
- sobrescrever outcome nativo de auditor;
- compartilhar fact sem nova validação;
- bypassar controlled reading ou structural scope.

Toda conclusão permanece fundada em auditoria nova e evidence refs novas.

## Memory roadmap marker

A próxima categoria arquitetural aprovada é **MEMORY / RETRIEVAL LAYER**,
posicionada depois deste core freeze e antes de evoluções mais autônomas. Seu
vocabulário inicial inclui persistent memory, retrieval, compression e
progressive disclosure.

Princípio normativo: `MEMORY_IS_CONTEXT_NOT_EVIDENCE`.

Este marker não cria HERMES-0028, implementation mandate, modelo público ou
capability.

## No-new-lens policy

Este freeze não autoriza nova lens. Capabilities experimentais continuam
exigindo spec, benchmarks justos, controles positivos/negativos e evidência
concreta. Discoveries anteriores são evidence de roadmap, não mandato de
implementação.

## Evidence summary

HERMES-0026 registrou:

- focused: 188 passed;
- regression: 396 passed, 9 skipped;
- full: 778 passed, 11 skipped, 0 failed;
- wheel e sdist com os módulos do baseline;
- invariants before/after byte-for-byte;
- finding IDs estáveis;
- benchmark histórico hermético;
- kernel estrutural compartilhado consolidado sem domain semantics.

A Core Freeze Readiness Review registrou todos os gates sem `FAIL` e a decisão
`CORE_READY_WITH_NON_BLOCKING_DEBT`, consolidada neste registro pelo verdict
`HERMES_CORE_READY_WITH_NON_BLOCKING_DEBT`.

Nenhum teste foi reexecutado e nenhum build foi produzido por HERMES-0027; esta
missão referencia exclusivamente a evidência já registrada por HERMES-0026 e
pela review de readiness.
