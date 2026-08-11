+++
schema_version = 1
id = "HERMES-0009"
title = "Auditoria dirigida por missão e Evidence Pack read-only"
status = "Rascunho"
owners = ["Danilo"]
created = "2026-08-11"
updated = "2026-08-11"
supersedes = []
related = ["HERMES-0007", "HERMES-0008"]

[[acceptance_criteria]]
id = "AC-01"
test = "tests/test_mission_audit.py::test_manifest_is_passive_read_only_and_requires_no_runtime_capability"
[[acceptance_criteria]]
id = "AC-02"
test = "tests/test_mission_audit_cli.py::test_mission_audit_requires_nonempty_mission"
[[acceptance_criteria]]
id = "AC-03"
test = "tests/test_mission_audit_cli.py::test_other_skills_reject_mission_input"
[[acceptance_criteria]]
id = "AC-04"
test = "tests/test_mission_audit.py::test_mission_normalization_is_closed_and_deterministic"
[[acceptance_criteria]]
id = "AC-05"
test = "tests/test_mission_audit.py::test_portuguese_terms_are_not_translated_or_expanded_by_synonym"
[[acceptance_criteria]]
id = "AC-06"
test = "tests/test_mission_audit.py::test_mission_without_local_signals_returns_insufficient_pack"
[[acceptance_criteria]]
id = "AC-07"
test = "tests/test_controlled_reader.py::test_mission_and_code_audit_share_the_controlled_reader_contract"
[[acceptance_criteria]]
id = "AC-08"
test = "tests/test_controlled_reader.py::test_reader_preserves_h0008_extensions_exclusions_and_limits"
[[acceptance_criteria]]
id = "AC-09"
test = "tests/test_controlled_reader.py::test_every_read_and_output_path_is_contained_and_relative"
[[acceptance_criteria]]
id = "AC-10"
test = "tests/test_controlled_reader.py::test_symlink_junction_and_reparse_point_block_without_following"
[[acceptance_criteria]]
id = "AC-11"
test = "tests/test_controlled_reader.py::test_structural_traversal_and_byte_limits_fail_closed"
[[acceptance_criteria]]
id = "AC-12"
test = "tests/test_mission_audit.py::test_region_count_and_excerpt_caps_are_explicit"
[[acceptance_criteria]]
id = "AC-13"
test = "tests/test_mission_audit.py::test_symbol_index_and_pack_caps_are_explicit"
[[acceptance_criteria]]
id = "AC-14"
test = "tests/test_mission_audit.py::test_relationship_cap_marks_pack_insufficient_without_silent_omission"
[[acceptance_criteria]]
id = "AC-15"
test = "tests/test_mission_audit.py::test_related_test_cap_marks_pack_insufficient"
[[acceptance_criteria]]
id = "AC-16"
test = "tests/test_mission_audit.py::test_final_pack_size_limit_blocks_oversized_serialization"
[[acceptance_criteria]]
id = "AC-17"
test = "tests/test_mission_audit.py::test_structural_failure_exposes_no_partial_pack"
[[acceptance_criteria]]
id = "AC-18"
test = "tests/test_mission_audit_models.py::test_evidence_pack_models_are_frozen_slotted_and_validated"
[[acceptance_criteria]]
id = "AC-19"
test = "tests/test_mission_audit_models.py::test_region_contains_relative_path_lines_excerpt_and_reasons"
[[acceptance_criteria]]
id = "AC-20"
test = "tests/test_mission_audit_models.py::test_relationship_requires_closed_kind_and_traceable_evidence"
[[acceptance_criteria]]
id = "AC-21"
test = "tests/test_mission_audit_models.py::test_every_selected_object_has_a_selection_reason"
[[acceptance_criteria]]
id = "AC-22"
test = "tests/test_mission_audit.py::test_direct_mission_terms_select_filename_symbol_import_and_lexical_regions"
[[acceptance_criteria]]
id = "AC-23"
test = "tests/test_mission_audit.py::test_single_bounded_lexical_bridge_has_region_provenance"
[[acceptance_criteria]]
id = "AC-24"
test = "tests/test_mission_audit.py::test_implementation_files_are_selected_with_explained_scores"
[[acceptance_criteria]]
id = "AC-25"
test = "tests/test_mission_audit.py::test_persistence_files_are_classified_by_closed_conventions"
[[acceptance_criteria]]
id = "AC-26"
test = "tests/test_mission_audit.py::test_related_tests_are_selected_by_traceable_relations"
[[acceptance_criteria]]
id = "AC-27"
test = "tests/test_mission_audit.py::test_repository_service_test_chain_uses_only_closed_relationships"
[[acceptance_criteria]]
id = "AC-28"
test = "tests/test_mission_audit.py::test_comments_and_docstrings_are_labeled_and_never_reported_as_active_code"
[[acceptance_criteria]]
id = "AC-29"
test = "tests/test_mission_audit.py::test_same_snapshot_and_mission_produce_identical_canonical_pack"
[[acceptance_criteria]]
id = "AC-30"
test = "tests/test_mission_audit.py::test_sufficient_pack_meets_all_closed_completeness_criteria"
[[acceptance_criteria]]
id = "AC-31"
test = "tests/test_mission_audit.py::test_insufficient_pack_names_missing_criteria_terms_and_limitations"
[[acceptance_criteria]]
id = "AC-32"
test = "tests/test_mission_audit.py::test_output_makes_no_bug_vulnerability_or_correctness_conclusion"
[[acceptance_criteria]]
id = "AC-33"
test = "tests/test_mission_audit_security.py::test_target_modules_are_never_imported_or_executed"
[[acceptance_criteria]]
id = "AC-34"
test = "tests/test_mission_audit_security.py::test_no_subprocess_shell_or_git_is_called"
[[acceptance_criteria]]
id = "AC-35"
test = "tests/test_mission_audit_security.py::test_no_file_is_opened_for_write_or_created_in_target"
[[acceptance_criteria]]
id = "AC-36"
test = "tests/test_mission_audit_security.py::test_no_network_api_is_called"
[[acceptance_criteria]]
id = "AC-37"
test = "tests/test_mission_audit_security.py::test_head_worktree_staging_and_refs_are_preserved"
[[acceptance_criteria]]
id = "AC-38"
test = "tests/test_mission_audit_integration.py::test_catalog_exact_lookup_and_target_shadowing_contract"
[[acceptance_criteria]]
id = "AC-39"
test = "tests/test_mission_audit_integration.py::test_linked_worktree_is_blocked_without_mutation"
[[acceptance_criteria]]
id = "AC-40"
test = "tests/test_mission_audit_cli.py::test_text_output_is_bounded_explanatory_and_deterministic"
[[acceptance_criteria]]
id = "AC-41"
test = "tests/test_mission_audit_cli.py::test_json_output_exposes_complete_stable_evidence_pack_schema"
[[acceptance_criteria]]
id = "AC-42"
test = "tests/test_mission_audit_cli.py::test_output_sanitizes_paths_controls_and_sensitive_literals"
[[acceptance_criteria]]
id = "AC-43"
test = "tests/test_mission_audit_regression.py::test_git_preflight_and_code_audit_contracts_are_unchanged"
[[acceptance_criteria]]
id = "AC-44"
test = "tests/test_packaging.py::test_wheel_and_sdist_include_and_run_mission_audit"
[[acceptance_criteria]]
id = "AC-45"
justification = "Benchmark real pós-implementação depende do clone externo da Lucre Agro e inclui revisão humana de relevância; não é teste portátil da suíte."
[[acceptance_criteria]]
id = "AC-46"
test = "tests/test_mission_audit_integration.py::test_invalid_target_blocks_before_catalog_and_handler"
[[acceptance_criteria]]
id = "AC-47"
test = "tests/test_controlled_reader.py::test_binary_invalid_utf8_and_invalid_bom_block_atomically"
[[acceptance_criteria]]
id = "AC-48"
test = "tests/test_controlled_reader.py::test_unreadable_removed_or_changed_file_blocks_atomically"
+++

# HERMES-0009 — Auditoria dirigida por missão e Evidence Pack read-only

## Status

Rascunho para revisão. Esta especificação não autoriza implementação.

## Resumo para o Responsável pelo Projeto

O Hermes passará a aceitar uma missão textual e reunir, de forma determinística
e somente leitura, os arquivos, regiões, símbolos, relações e testes que podem
ajudar uma análise posterior. Esta fase não usa IA e não declara que existe bug,
vulnerabilidade ou correção: ela entrega um pacote rastreável de evidências e
expõe honestamente quando o material encontrado é insuficiente.

## 1. Contexto

A HERMES-0007 separou o catálogo próprio do Hermes do projeto-alvo. A
HERMES-0008 adicionou `code-audit`, um scanner estático read-only com:

- raiz exata e catálogo canônico;
- dispatcher literal;
- extensões, exclusões e limites fechados;
- contenção, proteção contra indirections e UTF-8 estrito;
- leitura por descritor com verificação de estabilidade;
- cinco regras técnicas previamente conhecidas;
- saída estruturada e sanitizada;
- dogfooding real sem mutação de HEAD, refs, staging ou working tree.

`code-audit` responde “algum dos cinco gatilhos conhecidos apareceu?”. Ele não
responde “quais partes implementam esta missão de negócio e como elas se
relacionam?”. Essa segunda pergunta exige primeiro uma camada segura de seleção
e organização de evidências.

## 2. Problema Confirmado

Não existe hoje uma operação que receba uma missão como:

```text
Investigue o fluxo de lote documental e reúna evidências sobre possível
cruzamento de documentos entre clientes.
```

e produza uma seleção explicável de implementação, persistência, símbolos,
relações e testes. O conjunto fechado de regras da HERMES-0008 não deve ser
transformado em raciocínio aberto nem ampliado com heurísticas ocultas.

Sem um contrato novo, uma futura busca por missão poderia:

- traduzir ou inventar sinônimos sem informar;
- percorrer a árvore ilimitadamente;
- seguir relações especulativas;
- tratar comentário como implementação;
- esconder por que um arquivo foi escolhido;
- omitir silenciosamente partes limitadas;
- executar parser, import, Git ou ferramenta do alvo;
- apresentar seleção fraca como conclusão técnica.

## 3. Objetivos

1. Introduzir a skill passiva `mission-audit` no catálogo próprio.
2. Acrescentar `--mission` à invocação de `skill run` sem quebrar skills atuais.
3. Reutilizar as primitivas seguras de leitura da HERMES-0008.
4. Descobrir escopo por algoritmo determinístico, fechado e auditável.
5. Correlacionar código, camadas e testes apenas com evidência rastreável.
6. Produzir um `MissionEvidencePack` imutável e próprio para consumo futuro.
7. Diferenciar pacote suficiente, pacote insuficiente e falha estrutural.
8. Preservar integralmente o alvo e seu estado Git.

## 4. Não Objetivos

Esta especificação não inclui:

- IA, LLM, embeddings, busca vetorial ou tradução automática;
- conclusão de bug, vulnerabilidade, correção ou ausência de risco;
- recomendações de mudança de código;
- regras específicas da Lucre Agro, WhatsApp ou lote documental;
- nomes de arquivos, símbolos ou defeitos conhecidos do benchmark;
- execução de `git-preflight` ou `code-audit` dentro do handler;
- subprocesso, shell, Git, rede, compilador, linter ou parser externo;
- importação ou execução de módulos do alvo;
- leitura de histórico Git;
- configuração de limites ou heurísticas pelo alvo;
- opção pública de catálogo, include, exclude, depth ou score;
- persistência do Evidence Pack em disco;
- correção ou edição automática;
- múltiplas missões em uma invocação;
- descoberta semântica entre idiomas quando não houver ponte local verificável.

## 5. Comportamento Atual

A CLI aceita:

```text
python -m hermes_ops skill run <skill_id> --project <TARGET> --format text|json
```

`run_skill` recebe alvo, ID e policy. O dispatcher conhece literalmente
`git-preflight` e `code-audit`. A CLI não possui inputs específicos por skill.

O leitor seguro está atualmente dentro do módulo de `code-audit`. Suas
primitivas de raiz, inventário, leitura, encoding e estabilidade são privadas e
não devem ser copiadas para uma segunda implementação independente.

## 6. Comportamento Desejado

### 6.1 Interface pública

```text
python -m hermes_ops skill run mission-audit \
  --project <TARGET> \
  --mission "<MISSÃO>" \
  --format text|json
```

No parser compartilhado, `--mission` é opcional porque a obrigatoriedade depende
do `skill_id`. A validação fechada posterior aplica:

- `mission-audit` exige exatamente uma missão não vazia;
- `git-preflight` e `code-audit` rejeitam `--mission` quando fornecida;
- invocações existentes sem `--mission` permanecem idênticas;
- não haverá `--term`, `--seed` ou outra opção pública nesta versão.

### 6.2 Input operacional tipado

A evolução interna proposta é um valor imutável e fechado:

```text
SkillRunInputs:
    mission: texto opcional

run_skill(target, skill_id, policy, *, inputs=SkillRunInputs())
```

Não será aceito dicionário arbitrário. O parâmetro keyword-only com default
preserva chamadas existentes. Cada handler valida e consome somente os campos
que declara; input inesperado bloqueia antes do handler.

### 6.3 Skill passiva

```toml
id = "mission-audit"
version = 1
status = "active"
risk = "low"
requires = []
allows_write = false
```

O dispatcher ganha somente o ramo literal `mission-audit`. `SKILL.md` permanece
dado passivo e não contém regras executáveis.

### 6.4 Relação com git-preflight

O desenho conceitual contém um gate de preflight, mas o handler de
`mission-audit` não chama Git e não compõe outra skill. A execução pública já
faz validação de target, catálogo, policy e dispatcher. A raiz direta e linked
worktree usam o contrato conservador da HERMES-0008.

Quando um operador desejar `git-preflight`, ele o executa como comando separado.
Os snapshots Git do dogfooding são externos ao handler. Esta decisão resolve a
tensão entre o diagrama conceitual e a proibição explícita de Git durante a
análise.

## 7. Contrato da Missão

### 7.1 Validade textual

- tipo `str` exato;
- de 3 a 500 caracteres depois de normalizar whitespace externo;
- sem NUL ou caracteres de controle;
- uma única missão;
- sem interpretação como path, regex, glob, código ou comando.

Missão ausente, vazia ou estruturalmente inválida é erro de input, exit code 2.

### 7.2 Normalização

O algoritmo:

1. aplica Unicode NFKC;
2. aplica `casefold`;
3. colapsa whitespace;
4. separa tokens Unicode alfanuméricos;
5. mantém tokens entre 3 e 48 caracteres;
6. remove uma lista fechada e versionada de stopwords portuguesas e inglesas,
   incluindo verbos de instrução como “investigue”, “audite” e “reúna”;
7. cria, para comparação, alias sem acentos com provenance `accent_alias`;
8. rejeita mais de 24 termos significativos em vez de truncar silenciosamente.

Não há stemming, tradução, sinônimo, correção ortográfica ou aproximação por
distância. Tokens e aliases são expostos em `selection_terms`.

### 7.3 Português e identificadores do código

Uma missão em português pode encontrar:

- nomes e símbolos que compartilhem literalmente tokens;
- comentários/docstrings em português, rotulados como documentação;
- identificadores próximos a esses sinais locais por uma única ponte lexical.

Ela não transforma automaticamente `cliente` em `client`, `lote` em `batch` ou
`documento` em `document`. Se o próprio projeto não fornecer uma ponte local,
o pack será `insufficient`. Honestidade é preferível a busca mágica.

Não será criada opção `--term` nesta versão. Seeds explícitos poderão ser
avaliados futuramente como contrato tipado separado, após evidência de que a
ponte local é insuficiente.

## 8. Leitor Controlado Compartilhado

A implementação futura deve extrair de `code_audit.py` um componente interno
compartilhado, por exemplo `controlled_reader.py`, preservando exatamente:

- extensões permitidas da HERMES-0008;
- diretórios excluídos;
- validação da raiz e linked worktree;
- `lstat`, contenção e rejeição de indirections;
- arquivos regulares, UTF-8 estrito e tratamento de BOM/binário;
- leitura limitada por descritor read-only;
- identidade e estabilidade antes/depois;
- ordem de paths;
- limites estruturais.

`code-audit` e `mission-audit` consomem esse mesmo boundary. A refatoração não
altera regras, resultados ou exit codes de `code-audit`.

O leitor retorna documentos imutáveis com path relativo, extensão, bytes
decodificados, linhas e regiões lexicais classificadas. Ele não produz decisões
de missão.

## 9. Algoritmo Determinístico de Scope Discovery

### 9.1 Índice fechado

Para cada documento permitido, o indexador reconhece conservadoramente:

- tokens do nome e componentes do path;
- definições de classe e função;
- identificadores em código ativo;
- imports locais lexicalmente resolvíveis;
- comentários e docstrings, em categoria separada;
- convenções de teste;
- convenções genéricas de camada.

Não há AST externa. Um reconhecedor que não consiga classificar uma construção
com segurança deixa de criar símbolo/relação e registra limitação; ele não
executa nem adivinha.

### 9.2 Convenções fechadas

Papéis de arquivo:

- `implementation`: código permitido que não é apenas teste;
- `service`: path/símbolo contém token exato `service`;
- `repository`: path/símbolo contém `repository`, `repo` ou `dao`;
- `persistence`: contém `persistence`, `storage`, `database` ou `store`;
- `test`: path `tests/` ou nome `test_*.py`, `*_test.py`, `*.test.js|ts|jsx|tsx`;
- `support`: código permitido sem outro papel fechado.

Papéis são metadados de seleção, não afirmações arquiteturais.

### 9.3 Seleção direta

Cada ocorrência de termo original/alias recebe reason e peso:

| Origem | Peso |
|---|---:|
| nome/path | 12 |
| definição de símbolo | 10 |
| import local | 8 |
| identificador de código ativo | 6 |
| comentário/docstring | 4 |
| dois termos da missão a até 12 tokens | bônus 5 |

Um arquivo-semente precisa de ao menos uma correspondência direta. O score é a
soma dos reasons únicos; repetição idêntica não infla score. Comentário e
docstring podem selecionar documentação, mas nunca são rotulados como código
ativo.

### 9.4 Ponte lexical local

Há exatamente uma rodada de expansão:

1. partir somente de regiões com correspondência direta;
2. observar identificadores de código ativo a até 12 tokens da ocorrência;
3. aceitar um identificador derivado apenas se ele for definição/import local
   ou aparecer em duas regiões diretas distintas;
4. remover keywords, stopwords e identificadores menores que 3 caracteres;
5. ordenar por número de origens decrescente e token ordinal;
6. manter no máximo 24 termos derivados;
7. registrar cada região de origem e o termo direto que causou a derivação;
8. executar uma única expansão; termos derivados não geram novos termos.

Isso permite que um comentário português próximo a `document_batch` ofereça
uma ponte verificável sem dicionário português-inglês.

### 9.5 Grafo e correlação

Relações permitidas:

| Kind | Evidência necessária |
|---|---|
| `import` | import local explícito e módulo resolvido unicamente |
| `symbol_reference` | referência ativa a símbolo com definição local única |
| `naming_convention` | nomes normalizados compatíveis pela regra documentada |
| `test_relation` | teste importa/referencia símbolo ou corresponde à convenção do módulo |
| `lexical_relation` | termo direto/derivado comum com regiões nos dois lados |
| `layer_convention` | papéis service/repository/persistence conectados por import ou símbolo |

Uma relação possui origem, destino, kind, região de evidência e reason. Símbolo
ambíguo não gera relação. `layer_convention` nunca existe sozinho: referencia a
relação import/symbol que o sustenta.

A expansão do grafo é de um único hop a partir dos arquivos-semente. Não há
travessia recursiva.

### 9.6 Seleção final

Pesos adicionais:

- import/symbol relation com semente: 7;
- test relation: 9;
- lexical relation: 4;
- layer convention sustentada: 3.

Seleção intermediária usa score decrescente e path ordinal como desempate. O
Evidence Pack final é reordenado canonicamente, não por relevância implícita.
Todo item selecionado conserva os reasons e scores que permitiram a inclusão.

## 10. Modelo Imutável do Evidence Pack

```text
MissionEvidencePack
    schema_version
    mission
    target
    selection_terms
    files
    regions
    symbols
    relationships
    related_tests
    unresolved_questions
    completeness
    limitations
```

`target` público é sempre `<PROJECT_ROOT>`. O path absoluto operacional não é
armazenado no pack.

### 10.1 SelectionTerm

- `term`;
- `source`: `mission`, `accent_alias` ou `lexical_bridge`;
- `derived_from`: locators de regiões, vazio somente para termo original;
- `matched_count`.

### 10.2 EvidenceFile

- `path` relativo POSIX;
- `roles` fechados;
- `score` inteiro;
- `reasons` não vazios.

### 10.3 EvidenceRegion

- `path` relativo;
- `start_line`, `end_line`, base 1;
- `excerpt` limitado;
- `content_kind`: `active_code`, `comment` ou `docstring`;
- `reasons` não vazios.

### 10.4 EvidenceSymbol

- `name`;
- `kind`: `class`, `function`, `method`, `variable` ou `module`;
- `path` e região;
- `reasons`.

### 10.5 EvidenceRelationship

- `kind` fechado;
- `source` e `target` como locators;
- `evidence_region`;
- `reason`;
- `supporting_relationship`, obrigatório para `layer_convention`.

### 10.6 RelatedTest

- `path`;
- `related_to` não vazio;
- `reasons` contendo ao menos `test_relation`, import, símbolo ou convenção.

### 10.7 Questões, completude e limitações

Questões não são geradas livremente. Um catálogo fechado produz perguntas
determinísticas para critérios ausentes, por exemplo:

- `NO_IMPLEMENTATION_EVIDENCE`;
- `NO_PERSISTENCE_EVIDENCE`;
- `NO_RELATED_TEST_EVIDENCE`;
- `UNMATCHED_MISSION_TERMS`;
- `AMBIGUOUS_SYMBOL_RELATION`.

`EvidenceCompleteness` contém:

- `status`: `sufficient` ou `insufficient`;
- termos diretos matched/unmatched;
- critérios booleanos;
- contagens;
- códigos de incompletude.

`limitations` contém somente código estável, mensagem fixa e contagem. Não
contém exceção, path absoluto ou conclusão aberta.

## 11. Suficiência, Status e Exit Codes

Um pack é `sufficient` somente quando todos são verdadeiros:

1. ao menos dois termos diretos distintos foram encontrados;
2. existe ao menos uma região `active_code` de implementação;
3. existe ao menos uma relação rastreável entre itens selecionados;
4. existe ao menos um teste relacionado por relação rastreável;
5. nenhum cap analítico causou omissão.

Essa suficiência mede utilidade mínima do pacote, não qualidade ou segurança do
código.

| Situação | Status | Exit |
|---|---|---:|
| pack suficiente | `passed` | 0 |
| pack completo porém insuficiente | `completed_with_insufficient_evidence` | 3 |
| input de missão inválido | erro `SKILL_EXECUTION_INVALID` | 2 |
| falha estrutural controlada | erro fechado | 3 |
| falha externa inesperada | `external_failure` | 4 |

`SkillExecutionStatus` será estendido com o novo valor, preservando os dois
valores existentes. Insuficiência retorna um pack completo com limitações;
falha estrutural não retorna pack parcial.

## 12. Limites

### 12.1 Limites estruturais herdados da HERMES-0008

| Recurso | Limite | Excesso |
|---|---:|---|
| profundidade | 32 | bloqueia |
| diretórios classificados | 5.000 | bloqueia |
| arquivos candidatos | 1.000 | bloqueia |
| arquivo candidato | 512 KiB | bloqueia |
| bytes totais | 20 MiB | bloqueia |

Binário, UTF-8 inválido, arquivo instável, tipo especial ou indirection também
bloqueiam como na HERMES-0008.

### 12.2 Limites analíticos e do pack

| Recurso | Limite |
|---|---:|
| termos diretos | 24 |
| termos de ponte lexical | 24 |
| símbolos indexados | 10.000 |
| arquivos no pack | 100 |
| regiões por arquivo | 12 |
| regiões totais | 300 |
| linhas por região | 12 |
| caracteres por excerpt | 2.000 |
| símbolos no pack | 300 |
| relações | 500 |
| testes relacionados | 100 |
| questões não resolvidas | 24 |
| limitações | 24 |
| JSON canônico do pack | 2 MiB UTF-8 |

Mais de 10.000 símbolos ou JSON acima de 2 MiB são falhas estruturais. Nos
demais caps de seleção, o Hermes aplica ranking determinístico, registra
limitação e retorna `insufficient`; não omite silenciosamente nem chama o pack
de suficiente.

## 13. Segurança

1. Catálogo somente do Hermes; lookup exato; sem shadowing.
2. `--project` é exclusivamente TARGET.
3. Raiz e descendentes seguem o boundary compartilhado da HERMES-0008.
4. Nenhum acesso fora do TARGET.
5. Nenhum symlink, junction ou reparse point inseguro é seguido.
6. Nenhum arquivo é aberto para escrita.
7. Nenhum temporário, cache ou pack é criado no TARGET.
8. Nenhum módulo do TARGET é importado ou executado.
9. Nenhum subprocesso, shell, Git ou ferramenta externa é chamado.
10. Nenhuma rede é acessada.
11. Markdown da skill e missão permanecem dados.
12. Missão não é regex, glob, path ou comando.
13. Falha estrutural descarta índice, grafo e pack provisórios.
14. Paths públicos são relativos e passam pelo sanitizador central.
15. Excerpts são limitados, sem controles e submetidos à redação de literais
    sensíveis da HERMES-0008.
16. HEAD, branch, refs, staging e working tree não mudam.
17. Não há commit, push, checkout, switch, stage, reset, clean ou stash.

## 14. Determinismo e Ordenação Canônica

Para mesma versão, missão normalizada, plataforma e bytes/metadata estáveis:

- termos: `(source_order, term, provenance)`;
- arquivos: `path` ordinal;
- regiões: `(path, start_line, end_line, content_kind, reason_id)`;
- símbolos: `(path, line, kind, name)`;
- relações: `(kind, source_locator, target_locator, evidence_locator)`;
- testes: `(path, related_to)`;
- questões e limitações: `(code, payload canônico)`.

Scores são inteiros e não usam timestamp, hash aleatório, ordem de filesystem
ou locale. JSON usa chaves ordenadas, arrays canônicos, UTF-8 e schema version.

## 15. Contrato de Saída

### 15.1 Texto

Texto mostra missão sanitizada, status de completude, contagens, termos,
arquivos, regiões, relações, testes, questões e limitações. Não usa linguagem
de diagnóstico de bug. Exemplo de frase normativa:

```text
Evidence Pack coletado para análise posterior; nenhuma conclusão de bug,
vulnerabilidade ou correção foi produzida.
```

### 15.2 JSON

O envelope existente conserva `skill_id`, `status`, `exit_code` e `evidence`.
Uma evidência `mission_evidence_pack` contém o modelo completo como objeto JSON,
não como texto serializado dentro de string.

O schema é versionado e não contém path absoluto, traceback, horário, duração ou
conteúdo integral de arquivo.

## 16. Pseudocódigo

### 16.1 Entrada e pipeline

```text
AO RECEBER skill run mission-audit --project TARGET --mission MISSÃO:
    validar sintaxe e tamanho da missão
    validar TARGET direto antes do catálogo
    resolver somente o catálogo próprio
    descobrir e validar o catálogo atomicamente
    procurar exatamente mission-audit
    planejar sob policy read-only
    despachar pelo ramo literal mission-audit
```

### 16.2 Leitura e índice

```text
documentos = LEITOR_CONTROLADO_DA_HERMES_0008(TARGET)
SE raiz, path, limite, encoding, tipo ou estabilidade falhar:
    descartar tudo
    falhar fechado sem Evidence Pack

PARA cada documento em ordem:
    classificar regiões de código, comentário e docstring
    extrair conservadoramente símbolos, imports e identificadores
    SE não for possível classificar uma construção:
        não criar relação especulativa
        registrar limitação fechada
```

### 16.3 Termos e seleção

```text
termos = NORMALIZAR_MISSÃO_SEM_TRADUZIR(MISSÃO)
selecionar ocorrências diretas e registrar reason + peso

SE houver regiões diretas:
    derivar no máximo uma rodada de ponte lexical local
    registrar cada termo derivado e regiões de origem

construir relações fechadas de import, símbolo, nome, teste e léxico
expandir somente um hop a partir das sementes
classificar papéis por convenções fechadas
```

### 16.4 Pack e suficiência

```text
ordenar candidatos por score e desempate ordinal
aplicar caps analíticos
SE algum cap omitir candidato:
    registrar limitação
    marcar insuficiente

construir modelos imutáveis
validar que todo item possui reason e evidence locator
ordenar pack canonicamente

SE critérios mínimos forem atendidos e não houver limitação:
    retornar passed / 0
SENÃO:
    gerar somente questões fechadas para critérios ausentes
    retornar completed_with_insufficient_evidence / 3

NUNCA concluir bug, vulnerabilidade ou correção
```

## 17. Fluxo Principal

1. Parser recebe `--mission` sem alterar invocações antigas.
2. Boundary valida combinação skill/input.
3. Target, catálogo, registry, policy e dispatcher são validados em ordem.
4. Leitor compartilhado cria inventário integral ou falha fechado.
5. Indexador cria tokens, símbolos, imports e regiões tipadas.
6. Termos diretos são procurados com reasons e pesos.
7. Uma ponte lexical local, se sustentada, é calculada.
8. Grafo fechado correlaciona módulos e testes em um hop.
9. Caps e suficiência são avaliados explicitamente.
10. Pack imutável é ordenado e validado.
11. CLI sanitiza e apresenta texto ou JSON.

## 18. Casos de Erro e Limites

| Condição | Código proposto | Exit |
|---|---|---:|
| missão ausente/vazia/controle/tamanho | `SKILL_EXECUTION_INVALID` | 2 |
| mais de 24 termos diretos | `MISSION_TERM_LIMIT_EXCEEDED` | 2 |
| `--mission` em outra skill | `SKILL_EXECUTION_INVALID` | 2 |
| target inválido/indireto | código compartilhado HERMES-0008 | 3 |
| linked worktree | código compartilhado HERMES-0008 | 3 |
| catálogo/skill/policy inválidos | código existente | 3 |
| path/encoding/binário/tamanho/instabilidade | código compartilhado | 3 |
| mais de 10.000 símbolos | `MISSION_SYMBOL_INDEX_LIMIT_EXCEEDED` | 3 |
| pack JSON acima de 2 MiB | `MISSION_PACK_SIZE_EXCEEDED` | 3 |
| cap analítico de seleção | pack insuficiente + limitation | 3 |
| nenhum sinal local | pack insuficiente | 3 |
| relação ambígua | não cria relação; limitation/question | conforme completude |
| falha inesperada | `external_failure` | 4 |

## 19. Critérios de Aceitação

### Interface, catálogo e leitura

- **AC-01:** manifesto passivo, active, low, sem requires e sem escrita.
- **AC-02:** `mission-audit` exige missão válida; vazio/missing retorna 2.
- **AC-03:** skills existentes rejeitam missão e mantêm sintaxe anterior.
- **AC-04:** normalização segue somente regras fechadas e é determinística.
- **AC-05:** português não é traduzido nem expandido por sinônimos ocultos.
- **AC-06:** ausência de sinais retorna pack insuficiente, sem associação inventada.
- **AC-07:** `mission-audit` e `code-audit` usam o mesmo leitor controlado.
- **AC-08:** extensões, exclusões e limites HERMES-0008 são preservados.
- **AC-09:** toda leitura e path público permanecem contidos e relativos.
- **AC-10:** symlink, junction e reparse point bloqueiam sem serem seguidos.
- **AC-11:** limites estruturais bloqueiam atomicamente.

### Limites e modelos

- **AC-12:** máximo de 12 regiões/arquivo, 12 linhas e 2.000 caracteres é aplicado.
- **AC-13:** índices/packs de símbolos respeitam 10.000/300.
- **AC-14:** mais de 500 relações causa limitação e insuficiência, sem silêncio.
- **AC-15:** mais de 100 testes relacionados causa limitação e insuficiência.
- **AC-16:** JSON acima de 2 MiB bloqueia sem pack parcial.
- **AC-17:** qualquer falha estrutural não expõe índice, grafo ou pack parcial.
- **AC-18:** todos os modelos são frozen, slotted e validam invariantes.
- **AC-19:** região contém path, linhas, excerpt, kind e reasons válidos.
- **AC-20:** relação usa kind fechado e evidência rastreável.
- **AC-21:** nenhum arquivo, região, símbolo ou teste é incluído sem reason.

### Discovery e correlação

- **AC-22:** matches em path, símbolo, import, código e documentação têm pesos exatos.
- **AC-23:** ponte lexical tem uma rodada, máximo 24 e provenance regional.
- **AC-24:** implementação é selecionada por score explicável.
- **AC-25:** persistência usa apenas convenções fechadas e não afirma arquitetura.
- **AC-26:** teste relacionado exige import, símbolo ou convenção rastreável.
- **AC-27:** cadeia repository/service/test conserva relações subjacentes.
- **AC-28:** comentário/docstring é rotulado e nunca apresentado como código ativo.
- **AC-29:** mesma missão/snapshot produz pack idêntico e canônico.
- **AC-30:** pack suficiente cumpre os cinco critérios fechados.
- **AC-31:** pack insuficiente nomeia critérios, termos e limitações ausentes.
- **AC-32:** nenhuma saída conclui bug, vulnerabilidade ou correção.

### Segurança, CLI, regressão e packaging

- **AC-33:** nenhum módulo ou código do alvo é importado/executado.
- **AC-34:** nenhum subprocesso, shell ou Git é chamado pelo pipeline.
- **AC-35:** nenhuma escrita ou temporário ocorre no TARGET.
- **AC-36:** nenhuma rede é acessada.
- **AC-37:** HEAD, working tree, staging e refs permanecem idênticos.
- **AC-38:** catálogo próprio, lookup exato e anti-shadowing são preservados.
- **AC-39:** linked worktree bloqueia sem mutação.
- **AC-40:** texto é limitado, explicativo e determinístico.
- **AC-41:** JSON possui schema completo, estável e próprio para consumo futuro.
- **AC-42:** paths, controles e literais sensíveis são sanitizados/redigidos.
- **AC-43:** `git-preflight` e `code-audit` mantêm todos os contratos.
- **AC-44:** wheel/sdist contêm a skill e funcionam em instalação isolada.
- **AC-45:** dogfooding real usa somente missão benchmark, avalia relevância e
  preserva os quatro snapshots Git.
- **AC-46:** target ausente ou não diretório bloqueia antes do catálogo e do
  handler, sem pack parcial.
- **AC-47:** binário, UTF-8 inválido e BOM fora do início bloqueiam atomicamente.
- **AC-48:** arquivo ilegível, removido ou alterado durante a leitura bloqueia
  atomicamente.

## 20. Matriz AC → Testes

| AC | Tipo | Arquivo planejado | Foco |
|---|---|---|---|
| 01 | contrato | `test_mission_audit.py` | manifesto |
| 02–03 | CLI | `test_mission_audit_cli.py` | combinação skill/input |
| 04–06 | unitário | `test_mission_audit.py` | missão e insuficiência |
| 07–11 | segurança | `test_controlled_reader.py` | reutilização, path e limites |
| 12–17 | limites | `test_mission_audit.py` | caps e atomicidade |
| 18–21 | modelos | `test_mission_audit_models.py` | imutabilidade/provenance |
| 22–32 | discovery | `test_mission_audit.py` | score, ponte, grafo, completude |
| 33–37 | segurança | `test_mission_audit_security.py` | não execução/não mutação |
| 38–39 | integração | `test_mission_audit_integration.py` | catálogo/worktree |
| 40–42 | CLI | `test_mission_audit_cli.py` | text/JSON/sanitização |
| 43 | regressão | `test_mission_audit_regression.py` | skills existentes |
| 44 | packaging | `test_packaging.py` | wheel/sdist/isolamento |
| 45 | aceitação real | execução manual registrada | Lucre Agro |
| 46 | integração | `test_mission_audit_integration.py` | target inválido/precedência |
| 47–48 | segurança | `test_controlled_reader.py` | encoding, binário e estabilidade |

Os nomes exatos de testes estão no front matter. AC-45 possui justificativa
explícita por depender de clone externo e revisão humana.

## 21. Plano de Testes

### 21.1 Unitários

- missão válida, vazia, controles, limites e normalização;
- português sem tradução e ponte lexical com provenance;
- pesos, desempates e uma única rodada de expansão;
- símbolos/imports únicos e ambíguos;
- convenções Python/JS/TS de testes e camadas;
- comentários/docstrings versus código ativo;
- modelos inválidos, mutação e ordenação;
- suficiente e insuficiente;
- caps analíticos e pack size.

### 21.2 Leitor e segurança

- allowed extensions e exclusions herdados;
- raiz, ancestrais, arquivos e diretórios indiretos;
- containment e paths normalizados;
- binário, UTF-8, BOM, arquivo grande/instável/ilegível;
- file/directory/depth/byte limits;
- monkeypatch de import, subprocess, shell, Git, socket e APIs de escrita;
- allowed, blocked e regression para cada fronteira de segurança.

### 21.3 Integração e CLI

- catálogo com três skills e discovery atômico;
- skill ausente, catálogo inválido e shadow no target;
- `--mission` obrigatória somente para `mission-audit`;
- text/JSON suficiente, insuficiente e erro;
- sanitização de missão, paths, excerpt e erros;
- linked worktree e snapshots;
- regressão integral de `git-preflight` e `code-audit`.

### 21.4 Packaging

- wheel e sdist contêm `skills/mission-audit/SKILL.md` byte a byte;
- instalação isolada em CWD sem `skills/`;
- execução contra alvo externo temporário;
- rebuild do wheel a partir do sdist;
- catálogo incompleto/ambíguo bloqueia sem fallback.

## 22. Dogfooding Real

Alvo futuro:

```text
C:\Users\Danilo\Projeto\lucreagro-hermes-clone
```

Missão exata, sem seeds nem nomes conhecidos:

```text
Investigue o fluxo de lote documental e reúna evidências sobre possível
cruzamento de documentos entre clientes.
```

Comando:

```powershell
.venv\Scripts\python.exe -m hermes_ops skill run mission-audit `
  --project "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" `
  --mission "Investigue o fluxo de lote documental e reúna evidências sobre possível cruzamento de documentos entre clientes." `
  --format json
```

Antes/depois, capturar externamente:

```text
git rev-parse HEAD
git status --porcelain=v1
git diff --cached --name-status
git show-ref
```

Rubrica humana, sem alimentar o algoritmo com nomes:

1. evidência de fluxo de lote documental;
2. implementação/service;
3. repository;
4. identificação de cliente;
5. persistência;
6. testes relacionados.

O benchmark registra quais categorias foram encontradas, relevância de cada
seleção, falsos positivos, termos/relações que causaram seleção e limitações.
Não exige declaração de bug. Para considerar a capacidade útil no benchmark,
ao menos quatro das seis categorias, incluindo implementação e testes, devem
ter evidência humana verificável. Se isso não ocorrer, o resultado esperado é
`insufficient`, nunca uma associação fabricada.

HEAD, working tree, staging e refs devem ser idênticos. O clone não será limpo,
alterado ou preparado para passar.

## 23. Compatibilidade com HERMES-0007 e HERMES-0008

- catálogo continua único, próprio e sem override público;
- TARGET nunca fornece skill ou configuração de descoberta;
- lookup permanece exato e dispatcher literal;
- `discover_skills(root)` mantém API explícita;
- interface antiga funciona sem `--mission`;
- `code-audit` mantém cinco regras, modelos, status e exit codes;
- leitor compartilhado preserva integralmente os ACs de segurança HERMES-0008;
- nenhum catálogo, leitor ou sanitizador paralelo é criado;
- wheel/sdist passam a carregar três manifests canônicos.

## 24. Arquivos Provavelmente Afetados na Implementação Futura

```text
skills/mission-audit/SKILL.md
src/hermes_ops/cli.py
src/hermes_ops/commands/skill.py
src/hermes_ops/skills/controlled_reader.py
src/hermes_ops/skills/code_audit.py
src/hermes_ops/skills/mission_audit.py
src/hermes_ops/skills/mission_models.py
src/hermes_ops/skills/execution_models.py
src/hermes_ops/skills/executor.py
src/hermes_ops/skills/__init__.py
src/hermes_ops/core/errors.py
pyproject.toml
MANIFEST.in
tests/test_controlled_reader.py
tests/test_mission_audit.py
tests/test_mission_audit_models.py
tests/test_mission_audit_security.py
tests/test_mission_audit_integration.py
tests/test_mission_audit_cli.py
tests/test_mission_audit_regression.py
tests/test_packaging.py
docs/hermes/specs/HERMES-0009-auditoria-dirigida-missao-evidence-pack-read-only.md
```

## 25. Decisões Tomadas

| ID | Decisão | Justificativa | Alternativa descartada |
|---|---|---|---|
| D-01 | `--mission` opcional no parser e condicionalmente obrigatório | preserva uma única interface de `skill run` | subcomando público por skill |
| D-02 | `SkillRunInputs` fechado e keyword-only | evita dict arbitrário e preserva chamadas | parâmetros soltos ou JSON livre |
| D-03 | sem `--term` nesta versão | interface simples; insuficiência é honesta | seeds públicos prematuros |
| D-04 | sem tradução/stemming/sinônimos | determinismo e ausência de busca mágica | dicionário oculto |
| D-05 | uma ponte lexical local | permite conexão auditável entre comentário e identificador | expansão recursiva |
| D-06 | leitor HERMES-0008 extraído e compartilhado | evita duplicação de segurança | segundo walker/reader |
| D-07 | handler não chama git-preflight/code-audit | proibição de Git/subprocesso e separação de skills | composição operacional implícita |
| D-08 | relações fechadas com provenance | impede grafo especulativo | relação por similaridade opaca |
| D-09 | suficiência mede o pack, não o código | evita “passed” significar “correto” | conclusão técnica aberta |
| D-10 | insuficiente usa novo status e exit 3 | diferencia de sucesso e de erro pelo envelope | retornar 0 ou inventar exit code |
| D-11 | caps analíticos geram limitação/insuficiência | evita omissão silenciosa | truncar como sucesso |
| D-12 | benchmark por categorias, não arquivos | impede hardcode de consumidor | golden paths da Lucre Agro |

## 26. Alternativas Descartadas

1. LLM/embedding nesta fase: não determinístico, rede e privacidade.
2. Tradução automática ou dicionário bilíngue: associação não fornecida pelo
   alvo e difícil de auditar.
3. Busca fuzzy: pode selecionar termos semanticamente não relacionados.
4. AST/parser de terceiros: dependência, plugins e execução indireta.
5. Git grep/ripgrep: subprocesso e diferença de plataforma.
6. Grafo recursivo ilimitado: explosão de escopo e relações distantes.
7. Configuração no TARGET: conteúdo não confiável alteraria a barreira.
8. Retornar apenas lista de arquivos: insuficiente para explicar regiões e
   relações.
9. Declarar bug com base na seleção: Evidence Pack não é análise conclusiva.
10. Hardcode do benchmark: invalidaria a avaliação real.

## 27. Riscos Restantes

- Missão portuguesa pode não encontrar código inglês sem comentário/ponte local.
- Regras lexicais podem perder sintaxes complexas ou gerar candidatos fracos.
- Convenções service/repository/test não provam arquitetura real.
- Um hop pode omitir dependência relevante distante; mais hops aumentariam ruído.
- Comentários desatualizados podem criar ponte enganosa, embora rotulada.
- Score fixo pode favorecer nomes sobre relações; reasons permitem auditoria.
- Limites podem tornar projetos grandes insuficientes.
- Redação lexical não garante detectar todo segredo em excerpt.
- TOCTOU hostil além das garantias da HERMES-0008 permanece possível.
- `passed/0` pode ser mal interpretado; documentação deve reiterar que significa
  somente pack suficiente.
- O benchmark da Lucre Agro exige julgamento humano de relevância.

## 28. Evidências Necessárias para Implementado

O status somente poderá mudar após:

1. todos os 47 ACs automatizados passando e AC-45 validado pelo benchmark;
2. suíte completa e regressões HERMES-0007/0008;
3. compileall;
4. wheel, sdist, rebuild e instalação isolada;
5. `git diff --check`;
6. dogfooding AC-45 com missão exata, sem seeds;
7. Evidence Pack real e rubrica humana registrados;
8. HEAD, working tree, staging e refs antes/depois;
9. confirmação de nenhum hardcode de consumidor;
10. confirmação de nenhum commit/push/stage/branch change pela execução.

Nesta fase não existe implementação nem evidência operacional.

## 29. Histórico de Alterações

| Data | Autor | Alteração | Referência |
|---|---|---|---|
| 2026-08-11 | Codex | Rascunho inicial da HERMES-0009 para revisão antes de implementação | Solicitação de auditoria dirigida por missão |
