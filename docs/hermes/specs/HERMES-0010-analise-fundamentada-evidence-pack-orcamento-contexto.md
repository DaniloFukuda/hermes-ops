+++
schema_version = 1
id = "HERMES-0010"
title = "Análise fundamentada de Evidence Pack com orçamento explícito de contexto"
status = "Rascunho"
owners = ["Danilo"]
created = "2026-08-11"
updated = "2026-08-11"
supersedes = []
related = ["HERMES-0007", "HERMES-0008", "HERMES-0009"]

[[acceptance_criteria]]
id = "AC-01"
test = "tests/test_analysis_pack.py::test_analysis_pack_is_built_only_from_valid_evidence_pack"
[[acceptance_criteria]]
id = "AC-02"
test = "tests/test_analysis_pack.py::test_builder_never_receives_or_opens_target"
[[acceptance_criteria]]
id = "AC-03"
test = "tests/test_analysis_pack.py::test_reduction_is_deterministic_and_deduplicated"
[[acceptance_criteria]]
id = "AC-04"
test = "tests/test_analysis_pack.py::test_structurally_connected_regions_have_closed_priority"
[[acceptance_criteria]]
id = "AC-05"
test = "tests/test_analysis_pack.py::test_implementation_persistence_and_test_roles_have_closed_priority"
[[acceptance_criteria]]
id = "AC-06"
test = "tests/test_analysis_pack.py::test_every_analysis_item_preserves_evidence_pack_provenance"
[[acceptance_criteria]]
id = "AC-07"
test = "tests/test_analysis_pack.py::test_stable_evidence_ids_follow_canonical_order"
[[acceptance_criteria]]
id = "AC-08"
test = "tests/test_analysis_pack.py::test_budget_counts_exact_canonical_payload_characters"
[[acceptance_criteria]]
id = "AC-09"
test = "tests/test_analysis_pack.py::test_budget_omission_is_explicit_and_never_silent"
[[acceptance_criteria]]
id = "AC-10"
test = "tests/test_analysis_pack.py::test_minimum_viable_pack_fails_closed_when_budget_is_too_small"
[[acceptance_criteria]]
id = "AC-11"
test = "tests/test_analysis_pack.py::test_absolute_paths_are_rejected_before_adapter"
[[acceptance_criteria]]
id = "AC-12"
test = "tests/test_analysis_pack.py::test_items_not_present_in_evidence_pack_are_rejected"
[[acceptance_criteria]]
id = "AC-13"
test = "tests/test_analysis_pack.py::test_secret_like_literals_are_redacted_or_excluded_before_adapter"
[[acceptance_criteria]]
id = "AC-14"
test = "tests/test_analysis_pack.py::test_analysis_pack_hash_is_sha256_of_exact_canonical_payload"
[[acceptance_criteria]]
id = "AC-15"
test = "tests/test_analysis_adapter.py::test_adapter_contract_is_vendor_neutral"
[[acceptance_criteria]]
id = "AC-16"
test = "tests/test_analysis_adapter.py::test_controller_calls_adapter_only_after_local_validation"
[[acceptance_criteria]]
id = "AC-17"
test = "tests/test_analysis_adapter.py::test_adapter_receives_only_analysis_request"
[[acceptance_criteria]]
id = "AC-18"
test = "tests/test_analysis_adapter.py::test_no_adapter_is_configured_by_default"
[[acceptance_criteria]]
id = "AC-19"
test = "tests/test_analysis_dry_run.py::test_dry_run_never_calls_adapter"
[[acceptance_criteria]]
id = "AC-20"
test = "tests/test_analysis_dry_run.py::test_dry_run_emits_exact_payload_that_would_be_sent"
[[acceptance_criteria]]
id = "AC-21"
test = "tests/test_analysis_dry_run.py::test_dry_run_reports_counts_characters_budget_and_hash"
[[acceptance_criteria]]
id = "AC-22"
test = "tests/test_analysis_conclusions.py::test_every_claim_references_existing_evidence_ids"
[[acceptance_criteria]]
id = "AC-23"
test = "tests/test_analysis_conclusions.py::test_claim_classification_is_closed"
[[acceptance_criteria]]
id = "AC-24"
test = "tests/test_analysis_conclusions.py::test_unsupported_conclusive_claim_is_rejected"
[[acceptance_criteria]]
id = "AC-25"
test = "tests/test_analysis_conclusions.py::test_contrary_evidence_and_limitations_are_preserved"
[[acceptance_criteria]]
id = "AC-26"
test = "tests/test_analysis_conclusions.py::test_unknown_evidence_reference_rejects_entire_response"
[[acceptance_criteria]]
id = "AC-27"
test = "tests/test_analysis_security.py::test_analysis_path_uses_no_filesystem_shell_git_or_project_code"
[[acceptance_criteria]]
id = "AC-28"
test = "tests/test_analysis_security.py::test_analysis_path_does_not_write_target_or_access_network_directly"
[[acceptance_criteria]]
id = "AC-29"
test = "tests/test_analysis_cli.py::test_cli_analyzes_existing_pack_without_project_option"
[[acceptance_criteria]]
id = "AC-30"
test = "tests/test_analysis_cli.py::test_cli_rejects_project_and_target_inputs"
[[acceptance_criteria]]
id = "AC-31"
test = "tests/test_analysis_cli.py::test_cli_text_and_json_are_sanitized_and_deterministic"
[[acceptance_criteria]]
id = "AC-32"
test = "tests/test_analysis_cli.py::test_invalid_pack_question_or_budget_fails_closed"
[[acceptance_criteria]]
id = "AC-33"
test = "tests/test_analysis_regression.py::test_mission_audit_remains_local_deterministic_and_adapter_free"
[[acceptance_criteria]]
id = "AC-34"
test = "tests/test_analysis_regression.py::test_git_preflight_code_audit_and_catalog_contracts_are_unchanged"
[[acceptance_criteria]]
id = "AC-35"
test = "tests/test_analysis_packaging.py::test_wheel_and_sdist_include_analysis_contract_without_provider"
[[acceptance_criteria]]
id = "AC-36"
test = "tests/test_analysis_benchmark.py::test_saved_evidence_pack_answers_only_from_reduced_analysis_pack"
justification = "Automatizado com fixture sintética equivalente; o Evidence Pack real da Lucre Agro não integra o repositório."
[[acceptance_criteria]]
id = "AC-37"
test = "manual:dogfooding_h0010_saved_lucre_agro_pack"
justification = "Validação manual futura com Evidence Pack previamente capturado, sem acesso ao clone ou chamada real de API."
[[acceptance_criteria]]
id = "AC-38"
test = "tests/test_analysis_pack.py::test_budget_success_and_selected_evidence_are_monotonic"
[[acceptance_criteria]]
id = "AC-39"
test = "tests/test_analysis_pack.py::test_budget_success_and_selected_evidence_are_monotonic"
[[acceptance_criteria]]
id = "AC-40"
test = "tests/test_analysis_pack.py::test_budget_success_and_selected_evidence_are_monotonic"
[[acceptance_criteria]]
id = "AC-41"
test = "tests/test_analysis_pack.py::test_budget_success_and_selected_evidence_are_monotonic"
[[acceptance_criteria]]
id = "AC-42"
test = "tests/test_analysis_pack.py::test_question_promotes_relevant_structural_target_before_peripheral_chain"
[[acceptance_criteria]]
id = "AC-43"
test = "tests/test_analysis_pack.py::test_question_promotes_relevant_structural_target_before_peripheral_chain"
[[acceptance_criteria]]
id = "AC-44"
test = "tests/test_analysis_pack.py::test_source_score_is_controlled_tiebreaker_below_question_relevance"
[[acceptance_criteria]]
id = "AC-45"
test = "tests/test_analysis_pack.py::test_source_score_is_controlled_tiebreaker_below_question_relevance"
[[acceptance_criteria]]
id = "AC-46"
test = "tests/test_analysis_pack.py::test_question_changes_priority_without_changing_ids_or_provenance"
[[acceptance_criteria]]
id = "AC-47"
test = "tests/test_analysis_pack.py::test_question_promotes_relevant_structural_target_before_peripheral_chain"
[[acceptance_criteria]]
id = "AC-48"
test = "tests/test_analysis_pack.py::test_anchor_structural_unit_precedes_competing_lexical_regions"
[[acceptance_criteria]]
id = "AC-49"
test = "tests/test_analysis_pack.py::test_anchor_structural_unit_precedes_competing_lexical_regions"
[[acceptance_criteria]]
id = "AC-50"
test = "tests/test_analysis_pack.py::test_anchor_structural_unit_precedes_competing_lexical_regions"
+++

# HERMES-0010 — Análise fundamentada de Evidence Pack com orçamento explícito de contexto

## Status

Rascunho. Esta especificação não autoriza implementação nem chamada real a
qualquer modelo ou API.

## Resumo para o Responsável pelo Projeto

A `mission-audit` continuará coletando evidências localmente, de forma
determinística e sem LLM. A nova capacidade será uma etapa posterior e
opcional: o Hermes recebe um Evidence Pack já produzido, valida esse artefato,
reduz seu conteúdo a um Analysis Pack mensurável e somente então pode entregá-lo
a um analisador por uma interface desacoplada de fornecedor.

O analisador não recebe `--project`, não conhece a localização do TARGET e não
pode reler arquivos. Toda conclusão deve apontar para IDs existentes no
Analysis Pack. O modo `dry-run` não chama modelo e mostra exatamente o pedido
canônico que seria enviado, seus totais, seu orçamento e seu hash.

## Contexto

A HERMES-0007 separou o catálogo próprio do Hermes do projeto-alvo. A
HERMES-0008 introduziu leitura estática controlada e achados locais. A
HERMES-0009 introduziu `mission-audit`, seu leitor compartilhado e o
`MissionEvidencePack`: uma representação imutável, sanitizável, limitada e
rastreável de arquivos, regiões, símbolos, relações e testes relacionados.

Na arquitetura atual, `mission-audit` ainda é deliberadamente uma coleta de
evidência, não um mecanismo de conclusão. Ela usa somente algoritmos locais,
não importa código do alvo, não executa subprocessos e não acessa rede. O
Evidence Pack usa paths relativos, `<PROJECT_ROOT>` como identidade pública do
alvo e registra completude e limitações.

O próximo passo desejado é permitir perguntas técnicas sobre esse material sem
reabrir o projeto e sem enviar todo o pack indiscriminadamente a um modelo.
Economia de contexto, inspeção anterior à chamada e vínculo obrigatório entre
conclusão e evidência são partes do contrato, não otimizações opcionais.

## Problema Confirmado

Um Evidence Pack pode ser grande demais para envio econômico e pode conter
regiões redundantes ou periféricas. Enviar o artefato integral:

1. aumenta custo e variabilidade;
2. dificulta saber exatamente o que foi autorizado;
3. pode incluir literals sensíveis presentes em evidências locais;
4. favorece conclusões sem referências verificáveis;
5. acopla a auditoria a limites e formatos de um fornecedor;
6. cria risco de o analisador tentar compensar lacunas relendo o TARGET.

O Hermes precisa continuar controlando seleção, sanitização, orçamento,
chamada e validação da resposta.

## Explicação em Linguagem Simples

O Evidence Pack é a pasta de evidências autorizadas. O Analysis Pack é um
dossiê menor preparado pelo Hermes para uma pergunta específica. O analista
só vê esse dossiê: não recebe a chave do arquivo original, não visita o projeto
e não procura informação adicional.

Antes de qualquer chamada, o usuário pode executar um ensaio seco. O Hermes
mostra o dossiê exato, quantos itens e caracteres ele contém, o que ficou de
fora e um hash que identifica aquele conteúdo. A resposta só é aceita quando
cita evidências desse mesmo dossiê.

## Comportamento Atual

- `mission-audit` recebe TARGET e missão e produz `MissionEvidencePack`.
- O pack contém provenance relativa, relações fechadas, completude e limites.
- Não existe etapa de análise por modelo.
- Não existe adapter, Analysis Pack, orçamento de contexto ou dry-run.
- Não existe chamada real ou configuração padrão de fornecedor.

## Comportamento Desejado

### Separação obrigatória em duas etapas

```text
Etapa 1 — coleta local existente
TARGET -> mission-audit local -> Evidence Pack persistível

Etapa 2 — análise opcional nova
Evidence Pack validado + pergunta + orçamento
    -> redutor local determinístico
    -> Analysis Pack sanitizado e inspecionável
    -> dry-run OU adapter controlado pelo Hermes
    -> resposta validada com referências
```

O processo da etapa 2 não recebe TARGET. A API do redutor aceita um objeto
`MissionEvidencePack`, nunca `Path`, project root, callback de leitura ou
loader. O adapter aceita somente `AnalysisRequest` imutável.

### Interface pública proposta

```text
python -m hermes_ops evidence analyze \
  --evidence-pack <PACK_JSON> \
  --question "<PERGUNTA>" \
  --context-budget-chars <N> \
  --dry-run \
  --format text|json
```

Decisões da interface:

- `--evidence-pack` é obrigatório e aponta exclusivamente para um artefato
  serializado; o controlador pode lê-lo, mas redutor e adapter não recebem o
  path.
- `--question` é obrigatório, normalizado e limitado.
- `--context-budget-chars` é obrigatório na primeira versão, evitando custo
  implícito.
- `--dry-run` impede materialmente a resolução e a chamada do adapter.
- `--project`, `--target`, `--include`, `--file` e equivalentes são proibidos.
- `mission-audit` não ganha flag de modelo e permanece inalterada.
- Uma execução sem `--dry-run` falha fechada enquanto nenhum adapter explícito
  e autorizado estiver configurado pela aplicação hospedeira. Esta
  especificação não define opção pública para credencial ou fornecedor.

### Arquitetura proposta

```text
Evidence Pack JSON
       |
       v
controller: carregar, validar schema e tamanho
       |
       v
AnalysisPackBuilder (puro, local, determinístico)
  - validar provenance
  - sanitizar/redigir
  - atribuir evidence IDs
  - ordenar, deduplicar e reduzir
  - aplicar orçamento e registrar omissões
       |
       +--> dry-run presenter (não resolve adapter)
       |
       v
AnalysisController
       |
       v
AnalyzerAdapter interface (vendor-neutral)
       |
       v
resposta não confiável
       |
       v
AnalysisResponseValidator
  - schema fechado
  - IDs existentes
  - política de conclusões
  - limitações e contradições
       |
       v
saída pública sanitizada
```

## Fora do Escopo

- Implementar código, testes ou manifests nesta tarefa.
- Fazer chamada real a API ou escolher fornecedor/modelo.
- Ler novamente a Lucre Agro ou qualquer TARGET durante análise.
- Permitir que modelo selecione arquivos, paths ou comandos.
- RAG, embeddings, banco vetorial, busca semântica ou expansão por LLM.
- Sessão conversacional com memória oculta.
- Upload automático do Evidence Pack integral.
- Estimar ou cobrar tokens segundo tokenizer proprietário.
- Corrigir código, criar patch, escrever no TARGET ou executar ferramentas.
- Substituir a coleta determinística da HERMES-0009.
- Inferir fatos ausentes para tornar uma resposta mais conclusiva.

## Entradas e Saídas

### Entradas do controlador

- `evidence_pack`: JSON correspondente exatamente ao schema aceito de
  `MissionEvidencePack`.
- `question`: string NFKC com whitespace externo colapsado, entre 10 e 1.000
  caracteres, sem NUL ou controles inseguros.
- `context_budget_chars`: inteiro explícito entre 4.000 e 200.000.
- `dry_run`: booleano.
- `format`: `text` ou `json`.

O arquivo do pack tem limite fechado de 2 MiB, consistente com HERMES-0009. O
controlador lê exatamente esse arquivo, uma vez e de forma limitada. Ele não
segue referências ou paths contidos no JSON.

### Entradas do redutor

```text
build_analysis_pack(
    evidence_pack: MissionEvidencePack,
    question: AnalysisQuestion,
    budget: ContextBudget,
) -> AnalysisRequest
```

Não são entradas permitidas: TARGET, cwd, ambiente, rede, handles, caminhos
para source code ou funções de leitura.

### Entrada do adapter

```text
AnalyzerAdapter.analyze(request: AnalysisRequest) -> RawAnalysisResponse
```

`AnalysisRequest` contém somente instruções fechadas do Hermes, pergunta e
Analysis Pack. O adapter não recebe configuração do projeto, filesystem,
ferramentas, credenciais em texto ou callbacks.

### Saída validada

```text
AnalysisResult(
    schema_version,
    analysis_pack_hash,
    question,
    claims,
    overall_classification,
    limitations,
    omitted_evidence_summary,
)
```

Falhas estruturais não produzem resultado parcial.

## Modelo do Analysis Pack

Todos os modelos são imutáveis, slotted, validados e serializáveis em JSON
canônico.

```text
AnalysisPack
  schema_version: 1
  source_schema_version: 1
  mission: string sanitizada
  question: string sanitizada
  source_completeness: sufficient | insufficient
  evidence:
    files: AnalysisFile[]
    regions: AnalysisRegion[]
    symbols: AnalysisSymbol[]
    relationships: AnalysisRelationship[]
    tests: AnalysisTest[]
  source_limitations: string[]
  reduction_limitations: string[]
  omissions: OmissionSummary
  budget: BudgetReport

AnalysisFile
  id: F0001...
  path: path relativo
  roles: enum[]
  source_score: inteiro
  reasons: string[]

AnalysisRegion
  id: R0001...
  file_id: F....
  start_line: inteiro
  end_line: inteiro
  content_kind: active_code | comment | docstring
  excerpt: string sanitizada
  reasons: string[]

AnalysisSymbol
  id: S0001...
  file_id: F....
  name: string sanitizada
  kind: enum da HERMES-0009
  region_id: R.... | null
  reasons: string[]

AnalysisRelationship
  id: L0001...
  kind: enum da HERMES-0009
  source_id: evidence ID
  target_id: evidence ID
  evidence_region_id: R....
  supporting_relationship_id: L.... | null
  reason: string

AnalysisTest
  id: T0001...
  file_id: F....
  related_to_ids: evidence ID[]
  reasons: string[]

OmissionSummary
  omitted_files: inteiro
  omitted_regions: inteiro
  omitted_symbols: inteiro
  omitted_relationships: inteiro
  omitted_tests: inteiro
  omitted_ids_digest: SHA-256 | null
  reasons: enum[]

BudgetReport
  limit_chars: inteiro
  used_chars: inteiro
  remaining_chars: inteiro
  canonical_utf8_bytes: inteiro
  complete: booleano
```

Nenhum campo contém path absoluto. `<PROJECT_ROOT>` não é necessário no
Analysis Pack; a identidade da origem é o hash do Evidence Pack validado e
não uma localização física.

## Evidence IDs e Provenance

IDs são atribuídos localmente depois da validação e antes da redução:

1. ordenar objetos pelo critério canônico da HERMES-0009;
2. deduplicar por identidade estrutural completa;
3. atribuir prefixo por tipo e ordinal de quatro dígitos;
4. preservar o ID mesmo se o item for omitido, para que o digest de omissões
   seja estável;
5. incluir no Analysis Pack somente IDs selecionados e referências cujo alvo
   também esteja incluído.

Identidades:

- arquivo: path relativo canônico;
- região: path, linhas, content kind, excerpt e reasons;
- símbolo: nome, kind, path e região;
- relação: kind, source, target, evidence region e suporte;
- teste: path, relacionados e reasons.

Colisão, referência órfã, duplicação incompatível ou path inválido bloqueia o
pack inteiro. O hash de origem e o hash final usam SHA-256 sobre JSON canônico
UTF-8, chaves ordenadas, separadores compactos e sem valores não finitos.

## Algoritmo de Redução

### Ordem de prioridade fechada

O ranking primeiro identifica uma âncora representativa por arquivo com sinais
diretos da pergunta. As âncoras são ordenadas por:

1. cobertura lexical ponderada da pergunta;
2. quantidade de termos distintos cobertos;
3. `source_score`, decrescente, como sinal controlado;
4. papel fechado;
5. preferência por código ativo;
6. ID canônico.

Imediatamente após cada âncora entram, como pequena cadeia estrutural ordenada:

1. a própria região de âncora;
2. a região de provenance de cada relationship direta originada no arquivo;
3. uma região representativa do target direto correspondente.

Relationships da âncora são ordenadas pela relevância lexical do target,
`source_score`, papel e IDs canônicos. Somente depois dessas cadeias mínimas
entram regiões lexicais adicionais das âncoras, demais regiões dos arquivos,
testes relacionados, outras provenances estruturais e evidência periférica.

Os termos da pergunta são normalizados localmente por NFKC, casefold, remoção
de acentos, separação lexical e stopwords fechadas. Eles são comparados somente
com paths, reasons, excerpts e símbolos já presentes no Evidence Pack. Não há
sinônimo, tradução, stemming, embedding ou semântica externa.

Para reduzir a dominância de termos comuns, cada termo recebe peso inteiro
determinístico igual a `quantidade_de_arquivos + 1 - frequência_em_arquivos`.
Não há corpus externo, ponto flutuante ou estado persistente.

A promoção estrutural considera somente relationships já materializadas no
pack e somente targets diretos de sources lexicalmente relevantes. Para cada
target promovido, uma única região representativa é escolhida por relevância
lexical, código ativo e ID. Não há travessia transitiva, nova descoberta ou
leitura do TARGET. IDs e provenance são atribuídos antes do ranking e não
mudam quando a pergunta muda.

Uma relação só entra como unidade atômica junto de source, target e região de
evidência. Se a unidade não couber, ela é omitida integralmente e registrada.
Não se mantém relação quebrada para economizar caracteres.

### Deduplicação

- Excerpts idênticos no mesmo arquivo e região tornam-se um item.
- Reasons são conjuntos ordenados e únicos.
- Arquivos referenciados por vários itens aparecem uma vez.
- Relações semanticamente distintas não são fundidas.
- Deduplicação nunca remove provenance; origins múltiplas são preservadas em
  lista ordenada.

### Seleção

1. Validar integralmente Evidence Pack e pergunta.
2. Rejeitar qualquer path absoluto ou referência externa.
3. Redigir conteúdo sensível por regras locais fechadas.
4. Gerar IDs e grafo local.
5. Formar unidades atômicas de contexto.
6. Ordenar unidades pela prioridade fechada.
7. Avaliar cada prefixo de unidades contra o payload canônico final, incluindo
   todas as contagens, razões e o digest das omissões do sufixo.
8. Registrar toda unidade omitida por tipo, motivo e digest de IDs.
9. Recalcular referências e validar ausência de órfãos.
10. Serializar, medir e gerar hash.

Não há seleção pelo modelo, truncamento de excerpt no meio, resumo generativo,
expansão recursiva ou leitura adicional.

## Orçamento Explícito de Contexto

O orçamento normativo é medido em caracteres Unicode do JSON canônico de
`AnalysisRequest`, incluindo instruções, pergunta, schema, evidências,
limitações e relatório de omissões. Também se informa o total de bytes UTF-8.

O limite é obrigatório e validado entre 4.000 e 200.000 caracteres. O Hermes
não promete equivalência entre caracteres e tokens de fornecedor; caracteres
são uma unidade local, estável, mensurável e independente de tokenizer.

Antes da seleção, reserva-se espaço exato para envelope, instruções, pergunta,
limitações e relatório de orçamento. Cada unidade candidata é testada por
serialização canônica do pedido resultante, não por estimativa.

Os resultados candidatos são prefixos da ordem fechada e independem do valor
do budget. O redutor escolhe o prefixo mais longo cujo request final caiba.
Assim, budget maior nunca retrocede para menos evidência nem transforma sucesso
anterior em `ANALYSIS_CONTEXT_BUDGET_TOO_SMALL`. Metadados de omissão não são
acrescentados retroativamente depois de uma decisão de inclusão.

Se nem o envelope mínimo, pergunta, limitações da origem e uma unidade de
evidência couberem, falhar com `ANALYSIS_CONTEXT_BUDGET_TOO_SMALL`. Se itens
forem omitidos, `budget.complete=false`, `reduction_limitations` inclui
`CONTEXT_BUDGET_OMISSIONS` e os totais são explícitos. Nunca cortar string,
linha, objeto ou JSON silenciosamente.

## Sanitização de Conteúdo Sensível

Antes da priorização, o builder aplica uma política local e versionada:

- reutiliza o sanitizador público para paths e controles;
- rejeita paths absolutos em qualquer forma Windows ou POSIX;
- redige valores literais ligados a identificadores fechados como password,
  secret, token, api key, access key e credential;
- preserva nome do identificador e localização, substituindo somente o valor
  por `<REDACTED>`;
- registra `SENSITIVE_LITERAL_REDACTED` nas reasons/limitations;
- exclui atomicamente uma região quando não puder garantir redação segura;
- nunca inclui variáveis de ambiente, configuração externa ou credenciais do
  adapter no request.

O hash é calculado depois da sanitização. Dry-run e chamada usam exatamente o
mesmo objeto sanitizado.

## Dry-run

`--dry-run` executa validação, sanitização, IDs, redução, orçamento,
serialização e hashing. Ele não resolve, instancia nem chama adapter.

Saída JSON contém:

```text
dry_run: true
analysis_request: objeto exato que seria enviado
analysis_pack_hash: SHA-256
counts:
  files, regions, symbols, relationships, tests
context:
  limit_chars, used_chars, remaining_chars, canonical_utf8_bytes
omissions: totais, razões e digest
adapter_called: false
```

O formato text apresenta os mesmos totais e o payload canônico completo em
bloco delimitado. O hash deve ser reproduzível a partir desse payload. Não há
campos ocultos acrescentados depois do dry-run.

## Adapter do Analisador

Interface conceitual:

```text
INTERFACE AnalyzerAdapter:
    id() -> identificador não secreto e estável
    analyze(request: AnalysisRequest) -> RawAnalysisResponse
```

O domínio não importa SDK de fornecedor. O controller recebe um adapter por
injeção interna explícita. Nenhum adapter padrão é habilitado. Credenciais,
timeouts, retry e transporte pertencem à borda concreta futura e nunca entram
no Analysis Pack.

O adapter não oferece tools ao modelo. Se um fornecedor exigir configuração
de tools, a lista deve ser vazia e validada. O Hermes controla uma única
chamada; respostas que solicitem ferramenta, continuação ou conteúdo externo
são rejeitadas.

## Política de Segurança

1. `mission-audit` permanece local, determinística e sem adapter.
2. A análise nunca recebe TARGET ou project root.
3. Builder, validator e adapter nunca abrem arquivos do projeto.
4. Somente o controlador lê o arquivo explícito do Evidence Pack, com limite.
5. Paths internos são relativos e já pertencem ao pack validado.
6. Nenhum item novo pode ser inventado pelo redutor.
7. Nenhum path absoluto chega ao AnalysisRequest.
8. Conteúdo sensível é redigido ou excluído antes do hash e da chamada.
9. Não há subprocesso, shell, Git, import de código-alvo ou execução de código.
10. O domínio não acessa rede; somente adapter futuro pode transportar o
    request autorizado, sob controle do Hermes.
11. Adapter não recebe tools, filesystem, callbacks ou credenciais em texto.
12. Nenhuma etapa escreve no TARGET.
13. Dry-run torna impossível a chamada do adapter.
14. Falhas são fechadas, atômicas e sem fallback para pack integral.
15. Toda saída pública passa pelo sanitizador central.
16. Hash, contagens e orçamento são calculados localmente.
17. Uma resposta do modelo é dado não confiável até validação integral.

## Política de Conclusões

Classificações fechadas:

- `supported`: evidência direta e rastreável sustenta a afirmação; requer ao
  menos uma região ativa e uma relação ou segunda evidência independente.
- `plausible`: evidência é consistente e rastreável, mas falta ligação direta
  suficiente; a redação deve usar linguagem condicional.
- `insufficient`: o pack não permite sustentar nem contradizer; a resposta
  deve nomear a lacuna.
- `contradicted`: evidência contrária rastreável invalida a afirmação; requer
  `contrary_evidence_ids` não vazio.

Cada claim contém:

```text
Claim
  id
  statement
  classification
  evidence_ids[]
  contrary_evidence_ids[]
  rationale
  limitations[]
```

Regras:

1. Todo ID deve existir no Analysis Pack recebido.
2. `supported` não aceita lista vazia nem apenas comentário/docstring.
3. `plausible` deve usar marcador condicional e declarar o elo ausente.
4. `insufficient` não pode afirmar presença ou ausência conclusiva.
5. `contradicted` exige evidência contrária explícita.
6. Evidência contrária encontrada não pode ser omitida da claim.
7. Limitações do source e da redução são sempre propagadas.
8. Se uma conclusão depender de item omitido, ela é inválida.
9. Referência desconhecida, classificação desconhecida ou linguagem proibida
   rejeita a resposta inteira; não há reparo silencioso.
10. `overall_classification` é a classificação mais conservadora compatível
    com todas as claims e nunca promove evidência insuficiente.

## Pseudocódigo

### Carregar e validar o Evidence Pack

```text
FUNÇÃO CARREGAR_PACK(caminho_explícito):
    VALIDAR que o argumento aponta para um único arquivo regular direto
    LER no máximo 2 MiB, uma única vez, sem seguir indirections
    DECODIFICAR UTF-8 estrito e parsear JSON fechado
    CONSTRUIR MissionEvidencePack imutável
    VALIDAR schema, paths relativos, IDs implícitos, limites e referências
    NÃO abrir nenhum path descrito dentro do pack
    RETORNAR o objeto validado, sem conservar o path de entrada
```

### Construir o Analysis Pack

```text
FUNÇÃO CONSTRUIR_ANALYSIS_PACK(pack, pergunta, orçamento):
    VALIDAR tipos; rejeitar Path, TARGET e callbacks
    VALIDAR pergunta e orçamento fechado
    VALIDAR integralmente pack antes de produzir qualquer saída

    itens = COPIAR somente objetos autorizados do pack
    itens = SANITIZAR localmente
    SE uma região não puder ser sanitizada com segurança:
        OMITIR a região atomicamente
        REGISTRAR motivo e provenance

    DEDUPLICAR por identidade estrutural
    ATRIBUIR IDs estáveis pela ordem canônica
    FORMAR unidades atômicas, preservando relações e referências
    ORDENAR pela prioridade fechada

    pedido = envelope mínimo
    PARA CADA unidade ordenada:
        candidato = pedido + unidade
        SERIALIZAR candidato canonicamente
        SE candidato couber no orçamento:
            pedido = candidato
        SENÃO:
            REGISTRAR todos os IDs da unidade como omitidos por orçamento

    VALIDAR que pedido possui ao menos uma evidência útil
    VALIDAR ausência de referências órfãs e paths absolutos
    MEDIR caracteres e bytes exatos
    hash = SHA256(JSON_CANÔNICO_UTF8(pedido))
    RETORNAR pedido imutável, relatório e hash
```

### Dry-run

```text
FUNÇÃO DRY_RUN(pack, pergunta, orçamento):
    request, relatório, hash = CONSTRUIR_ANALYSIS_PACK(...)
    NÃO resolver adapter
    NÃO acessar rede
    EMITIR request exato, contagens, orçamento, omissões e hash
    RETORNAR exit code 0 se o request for válido
```

### Chamada controlada e validação

```text
FUNÇÃO ANALISAR(pack, pergunta, orçamento, adapter_explícito):
    request = CONSTRUIR_ANALYSIS_PACK(...)
    VALIDAR que adapter está explicitamente autorizado
    raw = adapter.analyze(request)
    # O adapter recebe somente request e não recebe tools.

    resposta = VALIDAR_SCHEMA_FECHADO(raw)
    PARA CADA claim:
        VALIDAR classificação fechada
        VALIDAR que todos os IDs existem em request
        VALIDAR requisitos de suporte, contradição e linguagem
        PROPAGAR limitações sem removê-las

    SE qualquer validação falhar:
        REJEITAR resposta inteira sem resultado parcial
    RETORNAR AnalysisResult sanitizado
```

## Fluxo Principal

1. Parsear somente flags fechadas de `evidence analyze`.
2. Validar pergunta, orçamento e ausência de TARGET.
3. Ler e validar o artefato do Evidence Pack.
4. Descartar a localização física do artefato do domínio.
5. Construir Analysis Pack determinístico.
6. Em dry-run, apresentar request, métricas e hash e terminar.
7. Fora do dry-run, exigir adapter interno explícito.
8. Entregar somente AnalysisRequest ao adapter.
9. Validar atomicamente a resposta não confiável.
10. Emitir resultado sanitizado com claims, IDs, contradições e limitações.

## Erros e Limites

- `ANALYSIS_PACK_INVALID`: schema, tipo ou referência inválida.
- `ANALYSIS_PACK_TOO_LARGE`: entrada acima de 2 MiB.
- `ANALYSIS_PATH_FORBIDDEN`: path absoluto ou externo no pack.
- `ANALYSIS_QUESTION_INVALID`: pergunta ausente ou inválida.
- `ANALYSIS_BUDGET_INVALID`: limite ausente ou fora da faixa.
- `ANALYSIS_CONTEXT_BUDGET_TOO_SMALL`: envelope mínimo inviável.
- `ANALYSIS_SENSITIVE_CONTENT_UNSAFE`: sanitização não pôde preservar um
  request mínimo seguro.
- `ANALYSIS_ADAPTER_UNAVAILABLE`: execução real sem adapter autorizado.
- `ANALYSIS_ADAPTER_FAILURE`: falha controlada do transporte futuro.
- `ANALYSIS_RESPONSE_INVALID`: schema, ID, classificação ou conclusão inválida.

Erros de entrada usam exit code 2; falhas controladas estruturais, adapter
indisponível e resposta inválida usam 3; falha externa inesperada usa 4. Dry-run
válido usa 0, mesmo quando há omissões explícitas que ainda preservem o pack
mínimo.

## Critérios de Aceitação

- **AC-01:** somente `MissionEvidencePack` integralmente válido alimenta o
  builder.
- **AC-02:** builder não aceita TARGET, path ou capacidade de leitura.
- **AC-03:** mesma entrada, pergunta e orçamento produzem bytes idênticos.
- **AC-04:** regiões conectadas estruturalmente precedem regiões isoladas.
- **AC-05:** implementação, persistência/repository e testes têm prioridade
  fechada e verificável.
- **AC-06:** todo item selecionado preserva provenance da HERMES-0009.
- **AC-07:** IDs são estáveis, tipados, únicos e canonicamente ordenados.
- **AC-08:** `used_chars` corresponde exatamente ao request canônico.
- **AC-09:** toda omissão por orçamento aparece em contagem, motivo e digest.
- **AC-10:** orçamento incapaz de conter pack mínimo bloqueia sem truncamento.
- **AC-11:** qualquer path absoluto bloqueia antes do adapter.
- **AC-12:** builder nunca inclui item ausente do Evidence Pack.
- **AC-13:** literals sensíveis são redigidos ou excluídos antes do adapter.
- **AC-14:** hash é SHA-256 reproduzível do request canônico sanitizado.
- **AC-15:** interface do adapter não contém tipos ou SDK de fornecedor.
- **AC-16:** adapter só é chamado após todas as validações locais.
- **AC-17:** adapter recebe exclusivamente `AnalysisRequest`.
- **AC-18:** não há adapter, rede ou chamada real habilitados por padrão.
- **AC-19:** dry-run nunca resolve nem chama adapter.
- **AC-20:** dry-run exibe exatamente os mesmos bytes lógicos da chamada.
- **AC-21:** dry-run informa arquivos, regiões, símbolos, relações, testes,
  caracteres, bytes, orçamento, omissões e hash.
- **AC-22:** toda claim referencia IDs existentes.
- **AC-23:** classificações aceitas são somente `supported`, `plausible`,
  `insufficient` e `contradicted`.
- **AC-24:** afirmação conclusiva sem suporte mínimo é rejeitada.
- **AC-25:** limitações e evidências contrárias não podem ser removidas.
- **AC-26:** um único ID desconhecido rejeita a resposta inteira.
- **AC-27:** domínio de análise não usa filesystem, shell, Git ou execução.
- **AC-28:** domínio não escreve no TARGET nem acessa rede diretamente.
- **AC-29:** CLI analisa pack existente sem aceitar `--project`.
- **AC-30:** qualquer tentativa de fornecer TARGET é rejeitada.
- **AC-31:** text e JSON são sanitizados, limitados e determinísticos.
- **AC-32:** pack, pergunta ou orçamento inválidos falham fechados.
- **AC-33:** `mission-audit` permanece local, determinística e sem LLM.
- **AC-34:** HERMES-0007/0008 e skills existentes não mudam.
- **AC-35:** wheel/sdist incluem contrato local, sem SDK/provider adicional.
- **AC-36:** fixture de benchmark responde exclusivamente do Analysis Pack.
- **AC-37:** dogfooding futuro reutiliza pack salvo da Lucre Agro, não lê clone
  e não chama API real durante a validação desta especificação.
- **AC-38:** todo request retornado satisfaz `used_chars <= limit_chars` e seu
  JSON canônico cabe no budget.
- **AC-39:** sucesso é monotônico: após um budget passar, budgets maiores não
  falham com `ANALYSIS_CONTEXT_BUDGET_TOO_SMALL` para a mesma entrada.
- **AC-40:** contagens de evidência selecionada não diminuem com budget maior;
  unidades e excerpts permanecem atômicos.
- **AC-41:** repetição do mesmo budget produz request, digest de omissões e hash
  exatamente idênticos.
- **AC-42:** termos lexicais locais da pergunta alteram deterministicamente a
  prioridade de arquivos e regiões diretamente relacionados.
- **AC-43:** target direto de relationship originada em arquivo relevante recebe
  promoção estrutural limitada ao grafo existente.
- **AC-44:** `source_score` participa dentro da mesma camada, mas não supera
  relevância direta da pergunta ou conectividade estrutural.
- **AC-45:** ranking é determinístico e mantém monotonicidade de budget.
- **AC-46:** perguntas diferentes podem mudar a seleção, nunca os IDs ou a
  provenance originais.
- **AC-47:** cadeia service → repository → teste relevante precede relações
  periféricas concorrentes quando o budget é limitado.
- **AC-48:** a âncora relevante, provenance estrutural e representante do target
  direto formam um prefixo coerente antes de regiões lexicais periféricas.
- **AC-49:** frequência local dos termos, `source_score`, papel, código ativo e
  IDs produzem ordem determinística sem semântica externa.
- **AC-50:** prefixo que não contém source, target e provenance completos não
  emite relationship órfã.

Cada AC automatizado possui o teste indicado no front matter. AC-37 é manual
porque depende de artefato real controlado que não deve integrar o repositório.

## Plano de Testes

### Unitários — builder e modelos

- validação profunda, imutabilidade e schema fechado;
- IDs, ordenação, deduplicação e hash;
- prioridades estruturais e por papel;
- unidades atômicas de relações;
- budgets nos limites mínimo, exato e excedido;
- omissões explícitas e ausência de truncamento;
- paths absolutos, referências órfãs e itens inventados;
- sanitização/redação e exclusão segura;
- determinismo com ordem de entrada permutada.

### Unitários — conclusões

- quatro classificações permitidas;
- IDs existentes e desconhecidos;
- `supported` sem suporte direto;
- `plausible` sem linguagem condicional;
- `insufficient` conclusivo;
- `contradicted` sem contrary evidence;
- propagação de limitações e resposta atômica.

### Segurança

- monkeypatch de `open`, `Path.read_*`, subprocess, Git, imports dinâmicos e
  sockets dentro de builder/controller/validator;
- adapter espião confirma request único e ausência de tools;
- dry-run confirma zero chamadas;
- snapshots externos confirmam nenhuma escrita.

### CLI e integração

- pack válido em text e JSON;
- ausência de `--project` e rejeição de flags de TARGET;
- orçamento e pergunta inválidos;
- adapter ausente;
- sanitização de paths, controles e literals;
- request do dry-run comparado byte a byte ao request do adapter fake;
- wheel/sdist executados em ambiente isolado sem dependência de fornecedor.

### Regressões

- `mission-audit` produz o mesmo Evidence Pack sem adapter;
- `code-audit` e `git-preflight` preservam contratos;
- catálogo próprio, lookup exato e target shadowing permanecem inalterados.

## Dogfooding Futuro

Pré-condição: possuir fora do repositório um Evidence Pack já capturado e
validado da Lucre Agro. O clone não deve estar disponível ao processo de
análise, demonstrando que não houve releitura.

Pergunta:

```text
Existe evidência de possível cruzamento de documentos entre clientes no fluxo
de lote documental?
```

Procedimento:

1. Copiar somente o Evidence Pack autorizado para diretório temporário.
2. Tornar o clone da Lucre Agro inacessível ao processo ou executar em ambiente
   que não o contenha.
3. Executar dry-run com orçamento explícito.
4. Registrar payload, contagens, caracteres, bytes, omissões e hash.
5. Usar adapter fake/replay nesta fase; nenhuma API real.
6. Validar que cada afirmação cita IDs existentes e inclui limitações e
   evidências contrárias.
7. Confirmar que nenhum path absoluto ou conteúdo externo aparece.
8. Repetir e comparar bytes e hash.

Aceite futuro: a resposta usa somente o Analysis Pack, não relê a Lucre Agro,
não inventa evidência e classifica conservadoramente a pergunta conforme o
suporte disponível.

## Arquivos Provavelmente Afetados em Implementação Futura

- `src/hermes_ops/analysis/models.py`
- `src/hermes_ops/analysis/builder.py`
- `src/hermes_ops/analysis/controller.py`
- `src/hermes_ops/analysis/adapter.py`
- `src/hermes_ops/analysis/validator.py`
- `src/hermes_ops/commands/evidence.py`
- `src/hermes_ops/cli.py`
- testes nomeados no front matter
- documentação de CLI e packaging, se necessário

Não é prevista alteração do handler de `mission-audit` nem do leitor
controlado da HERMES-0009.

## Riscos Conhecidos

1. Orçamento por caracteres não equivale a tokens do fornecedor; mitigação:
   unidade local explícita e bytes também reportados.
2. Priorização pode omitir evidência decisiva; mitigação: omissões visíveis,
   digest estável e classificação conservadora.
3. Redação por padrões pode falhar para segredo incomum; mitigação: exclusão
   fail-closed quando a região for suspeita e não sanitizável.
4. Modelo pode citar IDs inexistentes; mitigação: rejeição atômica.
5. Modelo pode formular conclusão forte com evidência fraca; mitigação:
   política local de claims e classificação fechada.
6. Relação quebrada pela redução; mitigação: unidades atômicas.
7. Dry-run divergir da chamada; mitigação: mesmo objeto imutável e mesmo hash.
8. Adapter introduzir tools ou conteúdo oculto; mitigação: interface mínima,
   request único e testes de fronteira.
9. Evidence Pack malicioso tentar injeção de instrução em excerpt; mitigação:
   excerpts são rotulados como dados não confiáveis e instruções do request
   proíbem obedecer conteúdo de evidência.
10. Hash revelar igualdade de conteúdo sensível; mitigação: hash somente após
    sanitização e sem publicação automática.

## Decisões

1. Análise é etapa separada, não modo interno de `mission-audit`.
2. Entrada normativa é Evidence Pack existente; não há TARGET na etapa.
3. Analysis Pack é construído localmente antes de qualquer adapter.
4. Budget obrigatório usa caracteres canônicos, com bytes informativos.
5. IDs são atribuídos pelo Hermes e validados na resposta.
6. Relações são unidades atômicas durante redução.
7. Omissão é permitida somente quando explícita e mensurável.
8. Dry-run é caminho completo sem chamada, não uma aproximação.
9. Adapter é vendor-neutral, injetado e ausente por padrão.
10. Resposta do modelo nunca é confiável antes da validação local.
11. A classificação é fechada e conservadora.
12. Não há implementação ou chamada real nesta especificação.

## Alternativas Consideradas

### Enviar Evidence Pack integral

Rejeitada: custo não controlado, menor inspeção e maior superfície de dados.

### Permitir que o modelo releia o TARGET

Rejeitada: quebra autorização, determinismo e isolamento entre coleta e
análise.

### Incorporar LLM dentro de `mission-audit`

Rejeitada: tornaria a skill local dependente de rede e fornecedor e impediria
reutilizar um pack salvo sem reler o projeto.

### Budget em tokens do fornecedor

Adiada: acopla o domínio a tokenizer específico. Caracteres canônicos são
mensuráveis antes da escolha de adapter.

### Resumo generativo antes da análise

Rejeitada: adiciona outra camada não determinística e pode perder provenance.

### IDs fornecidos pelo modelo

Rejeitada: não são confiáveis nem estáveis. IDs pertencem ao Hermes.

### Truncar excerpts para caber

Rejeitada: altera evidência silenciosamente. A unidade entra inteira ou é
omitida com registro.

### Embeddings ou banco vetorial

Fora de escopo: introduzem índice adicional, persistência e busca semântica.

## Evidência Necessária para Mudar o Status

Esta especificação só pode receber status `Implementado` após:

1. todos os ACs automatizados passarem;
2. suíte completa, compileall, build e packaging passarem;
3. dry-run provar identidade com o request entregue ao adapter fake;
4. auditoria confirmar ausência de filesystem/TARGET no domínio de análise;
5. AC-37 ser executado com pack real salvo, sem clone acessível e sem API real;
6. resultados concretos serem registrados na especificação ou evidência de
   validação associada.
