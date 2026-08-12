+++
schema_version = 1
id = "HERMES-0011"
title = "Orçamento de Execução e Checkpoint Automático"
status = "Rascunho"
owners = ["Danilo"]
created = "2026-08-12"
updated = "2026-08-12"
supersedes = []
related = ["HERMES-0005", "HERMES-0006", "HERMES-0008", "HERMES-0009", "HERMES-0010"]

[[acceptance_criteria]]
id = "AC-01"
test = "tests/test_execution_budget.py::test_valid_budget_starts_with_no_used_units"
[[acceptance_criteria]]
id = "AC-02"
test = "tests/test_execution_budget.py::test_consume_records_one_atomic_action"
[[acceptance_criteria]]
id = "AC-03"
test = "tests/test_execution_budget.py::test_valid_budget_starts_with_no_used_units"
[[acceptance_criteria]]
id = "AC-04"
test = "tests/test_execution_budget.py::test_closure_reserve_blocks_exploration_and_allows_closure"
[[acceptance_criteria]]
id = "AC-05"
test = "tests/test_execution_budget.py::test_checkpoint_threshold_stops_later_exploration"
[[acceptance_criteria]]
id = "AC-06"
test = "tests/test_execution_checkpoint.py::test_checkpoint_is_frozen_and_deeply_immutable"
[[acceptance_criteria]]
id = "AC-07"
test = "tests/test_execution_checkpoint.py::test_public_handoff_is_sanitized_bounded_and_has_no_sensitive_content"
[[acceptance_criteria]]
id = "AC-08"
test = "tests/test_execution_budget.py::test_invalid_budget_values_are_rejected"
[[acceptance_criteria]]
id = "AC-09"
test = "tests/test_execution_budget.py::test_budget_module_has_only_provider_neutral_imports"
[[acceptance_criteria]]
id = "AC-10"
test = "tests/test_execution_budget.py::test_budget_operations_have_no_external_effects"
[[acceptance_criteria]]
id = "AC-11"
test = "tests/test_execution_checkpoint.py::test_checkpoint_preserves_repository_snapshot"
[[acceptance_criteria]]
id = "AC-12"
test = "tests/test_execution_actions.py::test_exact_redundant_action_is_detected_without_cache"
[[acceptance_criteria]]
id = "AC-13"
test = "tests/test_execution_regression.py::test_existing_commands_and_explicit_configs_remain_compatible"
[[acceptance_criteria]]
id = "AC-14"
test = "tests/test_execution_configuration.py::test_omitted_execution_section_uses_safe_defaults"
[[acceptance_criteria]]
id = "AC-15"
test = "tests/test_execution_budget.py::test_warning_threshold_is_inclusive_on_resulting_snapshot"
[[acceptance_criteria]]
id = "AC-16"
test = "tests/test_execution_budget.py::test_consume_accumulates_explicit_positive_units"
[[acceptance_criteria]]
id = "AC-17"
test = "tests/test_execution_actions.py::test_repetition_after_relevant_state_change_is_not_redundant"
[[acceptance_criteria]]
id = "AC-18"
test = "tests/test_execution_actions.py::test_repeated_test_without_state_change_requires_justification_or_is_blocked"
[[acceptance_criteria]]
id = "AC-19"
test = "tests/test_execution_checkpoint.py::test_checkpoint_contains_required_traceable_fields"
[[acceptance_criteria]]
id = "AC-20"
test = "tests/test_execution_checkpoint.py::test_checkpoint_json_and_markdown_are_deterministic_with_injected_clock"
[[acceptance_criteria]]
id = "AC-21"
test = "tests/test_execution_checkpoint.py::test_checkpoint_generation_runs_no_subprocess_and_writes_no_file"
[[acceptance_criteria]]
id = "AC-22"
test = "tests/test_execution_integration.py::test_skill_executor_uses_one_execution_context_across_all_phases"
[[acceptance_criteria]]
id = "AC-23"
test = "tests/test_execution_integration.py::test_process_and_controlled_read_boundaries_report_actions"
[[acceptance_criteria]]
id = "AC-24"
test = "tests/test_execution_integration.py::test_budget_failure_has_specific_domain_error_and_checkpoint"
[[acceptance_criteria]]
id = "AC-25"
test = "tests/test_execution_checkpoint.py::test_handoff_resume_preserves_history_and_recommended_next_action"
[[acceptance_criteria]]
id = "AC-26"
test = "tests/test_execution_budget.py::test_absolute_limit_precedes_reserve_decision"
[[acceptance_criteria]]
id = "AC-27"
test = "tests/test_execution_security.py::test_allowed_targeted_closure_action_runs_inside_reserve"
[[acceptance_criteria]]
id = "AC-28"
test = "tests/test_execution_security.py::test_exploratory_read_is_blocked_inside_closure_reserve"
[[acceptance_criteria]]
id = "AC-29"
test = "tests/test_execution_security.py::test_checkpoint_cannot_capture_env_credentials_or_full_file_dumps"
[[acceptance_criteria]]
id = "AC-30"
test = "tests/test_execution_regression.py::test_git_queries_keep_existing_read_only_security_contract"
[[acceptance_criteria]]
id = "AC-31"
test = "tests/test_execution_context.py::test_context_preserves_budget_identity_and_is_immutable"
[[acceptance_criteria]]
id = "AC-32"
test = "tests/test_execution_context.py::test_context_rejects_non_budget_value"
[[acceptance_criteria]]
id = "AC-33"
test = "tests/test_execution_context.py::test_run_skill_without_context_preserves_legacy_result"
[[acceptance_criteria]]
id = "AC-34"
test = "tests/test_execution_context.py::test_same_context_reaches_dispatch_boundary"
[[acceptance_criteria]]
id = "AC-35"
test = "tests/test_execution_context.py::test_run_skill_does_not_consume_supplied_budget"
[[acceptance_criteria]]
id = "AC-36"
test = "tests/test_execution_context.py::test_context_creation_has_no_external_effects"
[[acceptance_criteria]]
id = "AC-37"
test = "tests/test_execution_context.py::test_context_does_not_change_public_skill_result"
[[acceptance_criteria]]
id = "AC-38"
test = "tests/test_execution_context.py::test_consume_returns_new_context_and_preserves_previous_snapshot"
[[acceptance_criteria]]
id = "AC-39"
test = "tests/test_execution_context.py::test_multiple_context_transitions_preserve_every_snapshot"
[[acceptance_criteria]]
id = "AC-40"
test = "tests/test_execution_context.py::test_context_delegates_category_units_and_decision"
[[acceptance_criteria]]
id = "AC-41"
test = "tests/test_execution_context.py::test_reserved_transition_propagates_error_without_changing_context"
[[acceptance_criteria]]
id = "AC-42"
test = "tests/test_execution_context.py::test_exhausted_transition_propagates_error_without_changing_context"
[[acceptance_criteria]]
id = "AC-43"
test = "tests/test_budgeted_process.py::test_allowed_consumes_before_one_process_call"
[[acceptance_criteria]]
id = "AC-44"
test = "tests/test_budgeted_process.py::test_warning_consumes_and_executes"
[[acceptance_criteria]]
id = "AC-45"
test = "tests/test_budgeted_process.py::test_checkpoint_required_blocks_before_process"
[[acceptance_criteria]]
id = "AC-46"
test = "tests/test_budgeted_process.py::test_reserved_blocks_before_process"
[[acceptance_criteria]]
id = "AC-47"
test = "tests/test_budgeted_process.py::test_exhausted_blocks_before_process"
[[acceptance_criteria]]
id = "AC-48"
test = "tests/test_budgeted_process.py::test_units_and_explicit_category_are_preserved"
[[acceptance_criteria]]
id = "AC-49"
test = "tests/test_budgeted_process.py::test_failed_process_keeps_consumed_context_and_failure_result"
[[acceptance_criteria]]
id = "AC-50"
test = "tests/test_budgeted_process.py::test_legacy_run_process_contract_is_unchanged"
[[acceptance_criteria]]
id = "AC-51"
test = "tests/test_budgeted_skill_execution.py::test_legacy_and_budgeted_git_preflight_are_functionally_equivalent"
[[acceptance_criteria]]
id = "AC-52"
test = "tests/test_budgeted_skill_execution.py::test_context_after_returns_to_public_budgeted_api"
[[acceptance_criteria]]
id = "AC-53"
test = "tests/test_budgeted_skill_execution.py::test_warning_executes_and_returns_advanced_context"
[[acceptance_criteria]]
id = "AC-54"
test = "tests/test_budgeted_skill_execution.py::test_budget_refusals_block_before_any_process"
[[acceptance_criteria]]
id = "AC-55"
test = "tests/test_budgeted_skill_execution.py::test_budget_refusals_block_before_any_process"
[[acceptance_criteria]]
id = "AC-56"
test = "tests/test_budgeted_skill_execution.py::test_budget_refusals_block_before_any_process"
[[acceptance_criteria]]
id = "AC-57"
test = "tests/test_budgeted_skill_execution.py::test_failed_probe_keeps_consumption_and_is_not_masked"
[[acceptance_criteria]]
id = "AC-58"
test = "tests/test_budgeted_skill_execution.py::test_only_git_preflight_has_budgeted_handler"
[[acceptance_criteria]]
id = "AC-59"
test = "tests/test_budgeted_skill_execution.py::test_budgeted_path_does_not_add_duplicate_probe_or_process"
[[acceptance_criteria]]
id = "AC-60"
test = "tests/test_budgeted_skill_execution.py::test_inspector_variants_each_execute_selected_probe_once"
+++

# HERMES-0011 — Orçamento de Execução e Checkpoint Automático

## Status

Rascunho. O domínio puro de `ExecutionBudget` e o transporte explícito de
`ExecutionContext` estão autorizados e implementados parcialmente. Defaults,
enforcement, instrumentação, checkpoint, handoff, novas skills e integração com
contador externo continuam não autorizados por esta fase.

## Resumo para o Responsável pelo Projeto

O Hermes passará a limitar o trabalho que ele próprio inicia, reservar parte do
orçamento para validar e fechar a execução e produzir um resumo reutilizável
antes de esgotar sua capacidade lógica. Isso evita que leitura, busca e teste se
repitam indefinidamente e permite que outra execução continue sem depender de
um prompt manual extenso.

O contador 32/32 observado no dogfooding não está exposto ao `hermes-ops`.
Portanto, o mecanismo proposto é local, determinístico e independente de
provider: ele controla ações conhecidas pelo Hermes, mas não afirma conhecer ou
reproduzir o limite da infraestrutura externa.

## Contexto

Sessões reais no projeto Lucre Agro terminaram com `ResourceExhausted` depois de
releituras, repetição de testes e consultas de estado. O working tree foi
preservado, porém uma pessoa precisou reconstruir o histórico e escrever o
handoff para a sessão seguinte.

O repositório atual já possui contratos úteis: configuração TOML fechada,
modelos imutáveis, planejamento de skills, despacho fechado, sanitização de
saída, subprocessos centralizados e Git somente leitura. Também há limites de
arquivos, diretórios, profundidade e bytes nos auditores, além de orçamento de
caracteres no Analysis Pack da HERMES-0010. Nenhum deles representa o número de
ações de uma execução.

## Problema Confirmado

Não existe no código atual um objeto de sessão ou execução que acompanhe ações
entre descoberta, planejamento, handler, leituras, subprocessos, validação e
fechamento. Consequentemente, não há:

- contador lógico de ações;
- reserva de validação ou fechamento;
- limiar de aviso ou checkpoint;
- histórico estruturado de leituras e comandos;
- detecção transversal de repetição;
- checkpoint ou handoff consumível por outra execução.

O `ResourceExhausted` relatado pertence à infraestrutura que hospeda o agente.
Busca pelos conceitos `budget`, `limit`, `step`, `action`, `attempt`,
`checkpoint`, `handoff`, `session`, `tool`, `execution`, `resource` e `retry`
não encontrou contador de chamadas externas. A única borda futura de provider é
o protocolo `AnalyzerAdapter`, que recebe uma requisição e não expõe metadados
de cota.

## Explicação em Linguagem Simples

O Hermes terá uma carteira de unidades para cada execução. Antes de fazer uma
ação controlada, ele verifica se pode pagá-la sem gastar a parcela guardada para
testar o necessário, registrar o estado e encerrar. Se uma ação idêntica já foi
feita e nada relevante mudou, o Hermes a reconhece como repetição.

Quando o saldo chega ao limiar seguro, o Hermes deixa de explorar, cria uma
fotografia pequena e sanitizada do progresso e orienta a próxima execução. Essa
fotografia é construída em memória e exibida pela saída pública; criá-la não
altera o projeto.

## Auditoria da Arquitetura Atual

### Entrypoints e fluxo de execução

- `pyproject.toml` publica `hermes-ops = hermes_ops.cli:main`;
- `python -m hermes_ops` delega ao mesmo `main`;
- `cli.py` monta `argparse`, cria `PublicSanitizer`, despacha comandos e é a
  fronteira final de erros e apresentação;
- `doctor`, `worktree` e `preflight` são orquestradores síncronos que retornam
  `Report`;
- `skill run` passa por catálogo, registry, `SkillPlan`, despacho fechado e um
  handler conhecido;
- `evidence analyze` carrega e reduz um pack; em modo não `dry-run`, chama um
  `AnalyzerAdapter` explicitamente fornecido.

### Representações existentes

- `SkillDefinition`, `SkillPolicy`, `SkillPlan`, `SkillRunInputs`,
  `SkillExecutionEvidence` e `SkillExecutionResult` são dataclasses imutáveis;
- `Report` e `CheckResult` representam o resultado final de comandos legados;
- não existe `Session`, `Attempt`, `Step`, `Action` ou contexto compartilhado de
  execução;
- “execution” hoje significa uma invocação unitária de skill, não uma sessão
  com histórico e orçamento.

### Skills

`load_skill` lê um `SKILL.md` UTF-8 de caminho explícito, valida front matter e
seções e preserva o corpo como dado inerte. `discover_skills` cria registry
imutável; `plan_skills` aplica status, risco, escrita e requisitos; `executor`
aceita apenas um plano unitário e escolhe handlers por comparação fechada de
ID. O conteúdo da skill não é executado e não concede capacidades.

### Logs, erros e apresentação

Não há subsistema de logging nem journal persistente. Evidências existem apenas
nos resultados retornados durante a invocação, e a CLI imprime texto ou JSON.
Erros esperados derivam de `HermesOpsError`; famílias de skills carregam código
estável. A fronteira da CLI converte falhas inesperadas em `external_failure` e
sanitiza mensagens e payloads com `PublicSanitizer`.

### Subprocessos, leituras e pontos de parada

`core.processes.run_process` é a única borda de subprocesso de produção,
executa sem shell, com cwd e timeout explícitos. `GitInspector` a utiliza com
ambiente Git neutralizado e comandos somente leitura. Leituras de código dos
auditores passam por `controlled_reader`, mas carregamento de configuração,
skills e Evidence Packs ainda usa `pathlib` diretamente. Pontos de parada são
retornos antecipados de `Report` ou exceções de domínio; não existe pausa ou
retomada.

## Observabilidade do Limite 32/32

Classificação: **B — limite não observável**.

O runtime do `hermes-ops` não fornece `current_tool_calls`, `max_tool_calls`,
`remaining_tool_calls` nem `worker_request_limit`. O projeto usa apenas a
biblioteca padrão, não captura `ResourceExhausted` e não recebe cabeçalhos ou
telemetria de quota. `AnalyzerAdapter` também não define esse contrato.

O orçamento lógico não deve ser chamado de “chamadas restantes” e não pode
prometer evitar todo esgotamento externo. Uma integração futura só poderá
considerar contador externo após existir um contrato confiável e provider-neutral;
até lá, sinais de infraestrutura não alteram o contador local.

## Comportamento Desejado

Cada invocação orçada cria um `ExecutionContext` único. O contexto contém o
budget, o journal limitado de ações, o objetivo, a fase e um relógio injetável.
Toda ação coberta consulta o budget antes de começar e registra um resultado
pequeno depois de terminar. Ao cruzar o aviso, emite uma única evidência. Ao
cruzar o checkpoint, não inicia exploração nova. Ao entrar na reserva de
fechamento, aceita somente a allowlist de fechamento.

Se for obrigatório interromper, retorna ou associa um `ExecutionCheckpoint`
com handoff sanitizável. A criação do objeto nunca chama Git, subprocesso, rede
ou filesystem: branch, HEAD e status devem vir de estado já coletado por ações
orçadas. Caso esse estado não exista, os campos ficam explicitamente
`unknown`, sem consulta oportunista escondida.

Na fase HERMES-0011B, `ExecutionContext` contém exclusivamente um
`ExecutionBudget` fornecido explicitamente. Ele não cria ID ou timestamp, não
consome unidades e não contém journal. `None` preserva integralmente a execução
legada; um contexto fornecido é transportado até `_dispatch_skill`, onde poderá
ser usado por instrumentação futura.

## Fora do Escopo

- ler ou integrar o contador 32/32 da infraestrutura;
- estimar tokens ou custo financeiro de modelos;
- cache de conteúdo de arquivos ou resultados de testes;
- heurística semântica para decidir se duas ações “parecem” iguais;
- execução paralela ou distribuição de budget entre workers;
- persistir checkpoint dentro do projeto automaticamente;
- implementar `execution-budget`, `checkpoint-handoff` ou `spec-guardian` nesta
  rodada;
- mudar handlers, configuração ou CLI nesta rodada;
- consumir budget ou adicionar enforcement durante o transporte do contexto.

## Arquitetura Proposta

### Ponto de integração

O ponto principal é `skills.executor.run_skill`, imediatamente após validar a
raiz explícita e antes de catálogo, descoberta, planejamento e handler. Ele deve
receber opcionalmente um `ExecutionContext` e passá-lo explicitamente até o
dispatcher. Enquanto defaults não forem calibrados, `None` não cria contexto ou
budget. Não deve haver singleton nem estado global.

Para cobrir ações reais, duas bordas devem aceitar um observador/contexto:

1. `core.processes.run_process`, para comandos e testes;
2. `skills.controlled_reader` e demais loaders autorizados, para leituras e
   buscas.

Os comandos legados poderão adotar o mesmo contexto em fase compatível
posterior. Contar apenas ao redor do handler seria insuficiente, pois esconderia
as múltiplas consultas Git e leituras internas. Contar apenas na CLI também
seria insuficiente para consumidores da API Python.

### ExecutionContext — fase HERMES-0011B

Modelo `frozen` e `slots` com um único campo obrigatório, `budget`. O campo
preserva a identidade do `ExecutionBudget` recebido; nenhuma cópia ou transição
é realizada. O contexto não possui `execution_id`, pois ainda não existe uso que
justifique identidade adicional.

O caminho implementado é:

```text
run_skill
    → _run_skill_with_catalog
        → _dispatch_skill
            → handler existente sem parâmetro novo
```

O dispatcher é o limite atual de propagação e o ponto futuro de instrumentação.
Nenhum handler recebe ou consulta o contexto nesta fase.

### Transição imutável — fase HERMES-0011C

Entre as opções consideradas, adota-se o contexto imutável que retorna outro
contexto. `ExecutionContext.can_start(category, units)` delega a decisão ao
budget corrente. `ExecutionContext.consume(category, units)` chama
`budget.consume`, recebe o novo snapshot e retorna um novo `ExecutionContext`.
Não existe wrapper de resultado: a decisão já é representada por
`BudgetDecision`, e uma transição bem-sucedida precisa retornar somente o novo
contexto.

O contexto anterior e seu budget permanecem inalterados. Antes de uma
transição, a identidade pode ser preservada durante o transporte; depois dela,
um novo contexto e um novo budget são esperados. Os demais campos seriam
preservados por valor quando existirem; nesta fase, `budget` continua sendo o
único campo.

Uma borda futura deve decidir e consumir antes do efeito externo:

```text
context_before
    → decision = context_before.can_start(category, units)
    → context_after = context_before.consume(category, units)
    → executar o efeito somente após a transição bem-sucedida
    → propagar context_after
```

Se a decisão resultar em reserva, checkpoint obrigatório ou exaustão,
`consume` preserva os erros definidos por `ExecutionBudget`; nenhum efeito deve
começar e `context_before` permanece válido. A fase 0011C define somente esse
contrato e não o aplica em `run_skill`, dispatcher, handlers, processos ou
leitores.

### Primeira borda real — fase HERMES-0011D

`run_process` permanece inalterado. A nova função
`run_process_with_context` recebe `ExecutionContext`, categoria explícita e
custo, além dos argumentos legados. Ela não infere política do comando e retorna
`BudgetedProcessResult`, contendo o `ProcessResult` legado e o contexto válido
após a tentativa.

A ordem normativa é: consultar `can_start`; bloquear decisões impeditivas;
consumir e obter contexto N+1; somente então chamar `run_process`. `ALLOWED` e
`WARNING` executam. `CHECKPOINT_REQUIRED`, `RESERVED` e `EXHAUSTED` lançam seus
erros específicos antes do subprocesso e preservam o contexto N.

O budget mede a tentativa. Depois de autorizado e consumido, retorno diferente
de zero, timeout, executável ausente ou outra falha representada por
`ProcessResult` não desfaz o consumo. O resultado budget-aware sempre conserva
o contexto N+1 ao lado da falha. A fase não adota a nova borda em nenhum caller
de produção.

### Primeiro caminho de produção — fase HERMES-0011E

O único caller direto encontrado foi `GitInspector`. A primeira adoção escolhe
somente sua probe read-only `git rev-parse --is-inside-work-tree`, protegida
pelos mesmos argumentos Git, ambiente neutralizado e timeout do inspector. A
API exige categoria explícita; o uso normal e semanticamente recomendado para
essa pré-condição é `ExecutionCategory.VALIDATION`. A probe custa uma unidade
lógica. Esse custo não representa o limite externo 32/32.

O caminho é:

```text
run_skill_with_context
    → _dispatch_skill_with_context
        → _run_git_preflight_with_context
            → GitInspector.probe_with_context
                → run_process_with_context
            → handler git-preflight legado, somente após probe bem-sucedida
    → BudgetedSkillExecutionResult(skill_result, context_after)
```

`run_skill` e `GitInspector.inspect` permanecem legados. A variante
`inspect_with_context` compartilha toda a lógica de inspeção e substitui somente
a probe existente; ela não executa uma probe preliminar. No preflight completo,
a inspeção do doctor usa essa variante e a inspeção do worktree continua
legada. Assim, não há subprocesso adicional: apenas uma das probes preexistentes
é contabilizada. Os demais subprocessos continuam fora do budget nesta fase.

A API paralela evita retorno condicional e impede a perda de `context_after`.
Nenhuma outra skill possui handler budget-aware. Se a probe falhar após começar,
o consumo permanece e a falha vira evidência funcional da skill; o restante do
preflight respeita o retorno antecipado já existente.

### ExecutionBudget

Modelo imutável com transição explícita: cada `consume` devolve um novo
snapshot. Nesta primeira fase o construtor exige todos os valores; defaults
pertencem à fase posterior de configuração. Campos aprovados para o domínio:

- `max_units`;
- `used_units`;
- `validation_reserve`;
- `closure_reserve`;
- `warning_threshold`;
- `checkpoint_threshold`.

Operações propostas:

- `remaining()` calcula `max_units - used_units`;
- `can_start(category, units=1)` devolve decisão sem alterar o estado;
- `consume(category, units=1)` valida primeiro e devolve novo budget;
- `should_warn()` observa o snapshot corrente;
- `should_checkpoint()` observa o snapshot corrente;
- `should_stop_exploration()` indica bloqueio de exploração/implementação.

O modelo não conhece arquivo, subprocesso, LLM, provider ou rede. O total e os
limiares são unidades lógicas locais, não tool calls externas.

### Unidades e categorias

Na primeira versão, cada ação atômica coberta custa uma unidade por default,
embora a API pura aceite custo inteiro positivo para representar uma operação
composta já conhecida. Isso é simples, auditável e evita falsa precisão.
Categorias fechadas nesta fase:

- `EXPLORATION`: leitura, busca e descoberta de informação nova;
- `IMPLEMENTATION`: trabalho que aplica a mudança planejada;
- `VALIDATION`: teste ou validação dirigida;
- `CLOSURE`: fechamento e produção do resultado final.

Categorias operacionais mais granulares, como READ, TEST ou GIT_READ, poderão
ser metadados futuros da ação, mas não participam do cálculo desta fase.

Uma ação que combina trabalho deve ser decomposta na borda onde os efeitos são
observáveis. Pesos diferentes ficam como extensão futura, sem alterar a
assinatura da ação. Não se contam linhas, bytes, tokens nem arquivos internos de
uma única varredura como substitutos de ação; os limites existentes continuam
protegendo volume e profundidade.

### ActionRecord e deduplicação

Em fase futura, cada ação receberá categoria, assinatura canônica, fase, custo,
`state_revision`, resultado resumido e justificativa opcional. Exemplos de
assinatura:

- `read:src/hermes_ops/cli.py:1-191`;
- `test:pytest:tests/test_execution_budget.py`;
- `git-read:status:porcelain-v1`.

A assinatura usa somente paths relativos sanitizáveis e argumentos públicos
permitidos. Essa fase futura deverá guardar um conjunto limitado de assinaturas
recentes; não guardará conteúdo nem saída completa.

Mesma assinatura na mesma `state_revision` é redundante. A primeira tentativa
redundante produz warning e exige justificativa explícita para prosseguir; sem
justificativa é bloqueada. Se autorizada, consome normalmente e fica marcada
como redundante. Teste repetido sem mudança relevante segue a mesma regra.
Mudança registrada de estado incrementa `state_revision`; mera leitura, status
ou passagem do tempo não incrementa. Como o Hermes atual é read-only, a revisão
normalmente permanece estável.

### Reserva e thresholds

Devem valer as relações:

```text
0 < closure_reserve
0 <= validation_reserve
validation_reserve + closure_reserve < max_units
0 <= warning_threshold < checkpoint_threshold
checkpoint_threshold <= max_units - validation_reserve - closure_reserve
```

O teto de EXPLORATION e IMPLEMENTATION é
`max_units - validation_reserve - closure_reserve`. O teto de VALIDATION é
`max_units - closure_reserve`. CLOSURE pode usar qualquer saldo até o limite
absoluto. Logo, validação pode usar espaço ainda não reservado e sua própria
reserva, enquanto fechamento preserva acesso à reserva final.

Os predicados `should_warn` e `should_checkpoint` avaliam `used_units` do
snapshot corrente com comparação inclusiva (`>=`). Uma ação autorizada pode
levar o novo snapshot exatamente ao threshold; o próximo trabalho observa a
transição. `can_start` devolve WARNING quando a ação cabe e seu consumo alcança
o warning. Se EXPLORATION ou IMPLEMENTATION for solicitada em snapshot que já
alcançou o checkpoint, devolve CHECKPOINT_REQUIRED e não inicia. VALIDATION e
CLOSURE continuam sujeitas aos próprios tetos. A precedência de decisões é:
EXHAUSTED, RESERVED, CHECKPOINT_REQUIRED, WARNING, ALLOWED.

Nenhuma categoria pode ultrapassar `max_units`, inclusive CLOSURE. `units` deve
ser inteiro positivo e valores booleanos não são aceitos como inteiros.

Os números default não são vinculados ao 32/32. Antes da aprovação desta spec,
devem ser calibrados com traces locais de ações; o contrato de “default seguro”
é definido pelas relações acima e por sempre preservar fechamento, não por um
número mágico. Configuração explícita poderá usar `[execution]` com
`max_units`, `validation_reserve_units`, `closure_reserve_units`,
`warning_threshold` e `checkpoint_threshold`.

### ExecutionCheckpoint

Dataclass congelada, deeply immutable e serializável, contendo no mínimo:

- timestamp UTC obtido de relógio injetado;
- raiz interna exata e identidade pública sanitizada;
- branch, HEAD e status sanitizado já observados;
- objetivo e fase;
- snapshot do budget;
- arquivos modificados e arquivos inspecionados;
- comandos/testes executados e resultados resumidos;
- falhas conhecidas e itens restantes;
- próximo passo recomendado;
- motivo do checkpoint;
- assinaturas recentes a não repetir.

Não contém tokens, variáveis de ambiente, credenciais, conteúdo de `.env`,
argumentos secretos, dumps completos, stdout/stderr completos ou paths
absolutos na forma pública. Coleções têm limites explícitos e ordenação
canônica. O timestamp é o único valor temporal e é controlável em testes.

### Handoff

O checkpoint possui JSON canônico interno e renderização Markdown pública. O
JSON é o contrato de retomada; Markdown é uma visão humana do mesmo objeto, não
uma segunda fonte de verdade. A CLI os envia a stdout após `PublicSanitizer`.
Persistência em arquivo só poderá ocorrer por opção explícita futura e nunca
dentro do projeto por padrão.

Ao retomar, o Hermes valida schema/version, objetivo e identidade do projeto,
restaura apenas histórico e próxima ação, e cria novo budget. Não reutiliza
automaticamente resultados se HEAD ou estado observado forem incompatíveis.

## Entradas

- raiz exata fornecida por `--project` quando aplicável;
- objetivo textual limitado;
- configuração `[execution]` opcional;
- plano e fase atuais;
- ações reportadas pelas bordas controladas;
- checkpoint anterior opcional, explicitamente fornecido;
- relógio injetável.

## Saídas

- snapshots de `ExecutionBudget`;
- `ActionRecord` limitado por ação;
- warning estruturado ao cruzar limiar;
- erros de domínio específicos;
- `ExecutionCheckpoint` imutável;
- handoff JSON canônico e Markdown sanitizado;
- resultado normal existente quando o budget não interfere.

## Invariantes e Regras de Segurança

- O budget nunca concede capacidade de filesystem, subprocesso, Git ou rede.
- Toda ação é autorizada pela política existente antes de ser orçada.
- O checkpoint não executa coleta adicional nem modifica o working tree.
- Toda saída pública passa por `PublicSanitizer`.
- `.env`, credenciais, ambiente e dumps completos nunca entram no checkpoint.
- `--project` continua sendo a raiz exata; não há descoberta de pais ou irmãos.
- Git permanece somente leitura, com locks, redirecionamentos, includes,
  filtros e fsmonitor neutralizados conforme o contrato atual.
- Subprocessos continuam passando por `core.processes`.
- O domínio usa somente biblioteca padrão, sem rede e sem provider.
- O estado é explícito e por execução; não há singleton, global mutável ou
  compartilhamento acidental entre projetos.
- Falha ao criar handoff seguro produz erro sanitizado e nenhum artefato parcial.

## Erros Específicos

Novas classes em `core/errors.py`, derivadas de `HermesOpsError` e com código
estável:

| Situação | Classe | Código proposto | Comportamento |
|---|---|---|---|
| custo ultrapassa total | `ExecutionBudgetExceeded` | `EXECUTION_BUDGET_EXCEEDED` | bloqueia antes da ação |
| ação invade reserva da fase | `ExecutionBudgetReserved` | `EXECUTION_BUDGET_RESERVED` | bloqueia antes da ação |
| limiar exige fechamento | `CheckpointRequired` | `EXECUTION_CHECKPOINT_REQUIRED` | produz checkpoint, sem explorar |
| configuração incoerente | `ConfigurationSchemaError` | contrato existente | rejeita antes de executar |
| checkpoint inválido | `ExecutionCheckpointError` | `EXECUTION_CHECKPOINT_INVALID` | rejeita retomada integralmente |
| repetição sem justificativa | `ExecutionActionRedundant` | `EXECUTION_ACTION_REDUNDANT` | bloqueia antes da repetição |

Erros de budget devem carregar somente metadados sanitizáveis: categoria,
custo, saldo e fase. Não incluem comando bruto ou conteúdo.

## Pseudocódigo

### Iniciar uma execução

```text
RECEBER configuração opcional, objetivo e raiz exata
VALIDAR configuração e relações entre reservas e limiares
SE configuração não declarar execution:
    APLICAR defaults seguros versionados
CRIAR budget sem unidades usadas
CRIAR journal vazio e revisão de estado inicial
RETORNAR contexto explícito da execução
```

### Autorizar e registrar uma ação

```text
RECEBER categoria, assinatura sanitizável e fase
VERIFICAR primeiro se a política existente permite a capacidade

SE a assinatura já ocorreu na mesma revisão de estado:
    MARCAR como redundante
    SE não existe justificativa explícita:
        BLOQUEAR antes de repetir

CALCULAR custo pela tabela fechada de categorias
SE o custo ultrapassa o orçamento total:
    BLOQUEAR com erro de orçamento excedido
SE a ação consumiria reserva destinada a uma fase posterior:
    BLOQUEAR com erro de reserva
SE o limiar de checkpoint foi alcançado e a ação é exploratória:
    EXIGIR checkpoint em vez de iniciar a ação

CONSUMIR o custo e iniciar a ação na borda controlada
REGISTRAR somente resultado resumido, nunca dump completo
SE houve mudança autorizada e relevante de estado:
    INCREMENTAR revisão de estado
SE o warning acabou de ser cruzado:
    EMITIR warning uma única vez
RETORNAR novo contexto imutável
```

### Criar checkpoint

```text
RECEBER contexto e fatos já registrados
NÃO ler arquivo, NÃO chamar Git, NÃO iniciar subprocesso, NÃO acessar rede
ORDENAR e limitar arquivos, ações, resultados, falhas e itens restantes
REMOVER conteúdo sensível e aplicar identidade pública aos caminhos
CRIAR objeto imutável com timestamp do relógio injetado
VALIDAR que todos os campos são serializáveis e limitados
RENDERIZAR JSON canônico e Markdown a partir do mesmo objeto
RETORNAR checkpoint sem escrever no projeto
```

### Retomar de um handoff

```text
VALIDAR schema e limites do checkpoint fornecido
COMPARAR identidade do projeto e estado observado disponível
SE incompatível:
    NÃO confiar em resultados reutilizáveis
    INFORMAR divergência de estado
CRIAR novo budget seguro
IMPORTAR lista limitada do que não repetir e itens restantes
COMEÇAR pelo próximo passo recomendado, sujeito à política e ao novo budget
```

## Fluxo Principal

1. A CLI ou API resolve a raiz exata e carrega configuração.
2. O executor cria um `ExecutionContext` antes de descoberta e planejamento.
3. Cada leitura ou subprocesso coberto pede autorização ao contexto.
4. O journal recebe uma síntese determinística da ação concluída.
5. O warning sinaliza a aproximação do limiar uma única vez.
6. O checkpoint threshold encerra exploração ampla.
7. Validação dirigida usa somente sua reserva e ações previstas.
8. Fechamento usa a reserva final para gerar checkpoint/handoff e relatório.
9. A CLI sanitiza e apresenta o resultado.

## Casos de Erro e Limites

- Configuração booleana, negativa, zero indevido ou fora das relações bloqueia
  com `ConfigurationSchemaError`.
- Categoria desconhecida bloqueia antes de consumir unidade.
- Ação que custa mais que o saldo bloqueia antes de produzir efeito.
- Exploração durante reserva bloqueia mesmo que exista saldo numérico.
- Checkpoint com campo desconhecido, versão incompatível, coleção excessiva ou
  path absoluto público é rejeitado integralmente.
- Ausência de branch/HEAD/status previamente coletado gera `unknown`, não nova
  consulta Git.
- Falha da ação registra síntese da falha e consome a unidade, pois o recurso foi
  tentado; falha de autorização não consome porque a ação não começou.
- Repetição justificada ainda consome unidade e permanece auditável.
- O journal é limitado; ao alcançar o limite, preserva totais e digests em vez
  de crescer sem limite.
- `ResourceExhausted` externo continua sendo falha externa enquanto não houver
  contrato observável; se chegar à borda, o melhor checkpoint possível usa
  apenas estado já coletado.

## Critérios de Aceitação

- **AC-01:** budget default começa com `used_units=0` e configuração válida.
- **AC-02:** consumir ação atômica autorizada incrementa o uso exatamente pelo
  custo determinístico da categoria.
- **AC-03:** `remaining` é exato e snapshots anteriores não mudam.
- **AC-04:** a reserva de fechamento bloqueia exploração e permite somente a
  allowlist de fechamento.
- **AC-05:** o threshold exige checkpoint antes de invadir a reserva final.
- **AC-06:** checkpoint e coleções internas são profundamente imutáveis.
- **AC-07:** handoff público é sanitizado, limitado e não contém segredos,
  ambiente, tokens, dumps ou paths absolutos.
- **AC-08:** toda combinação inválida de parâmetros do domínio falha fechada;
  validação do TOML permanece coberta futuramente por AC-14.
- **AC-09:** domínio do budget não importa SDK nem tipo de provider.
- **AC-10:** o domínio de budget não acessa filesystem, subprocesso ou rede.
- **AC-11:** gerar checkpoint preserva exatamente o snapshot do repositório.
- **AC-12:** ação exatamente repetida na mesma revisão é detectável sem cache de
  conteúdo.
- **AC-13:** comandos e configurações existentes continuam compatíveis.
- **AC-14:** ausência de `[execution]` aplica default seguro versionado.
- **AC-15:** o warning threshold é inclusivo, observável no novo snapshot e não
  altera o estado por consulta; emissão pública única pertence à integração.
- **AC-16:** categorias e custos formam tabela fechada e determinística.
- **AC-17:** mesma ação após mudança relevante registrada não é classificada
  automaticamente como redundante.
- **AC-18:** teste repetido sem mudança exige justificativa ou é bloqueado.
- **AC-19:** checkpoint contém todos os campos mínimos rastreáveis definidos.
- **AC-20:** com relógio injetado, JSON e Markdown são determinísticos.
- **AC-21:** checkpoint não inicia subprocesso nem escreve arquivo.
- **AC-22:** descoberta, planejamento, handler, validação e fechamento usam o
  mesmo contexto explícito.
- **AC-23:** subprocessos e leitores controlados registram suas ações reais.
- **AC-24:** budget/reserva/checkpoint usam erros específicos e checkpoint
  disponível quando seguro.
- **AC-25:** retomada preserva histórico limitado, itens restantes e próximo
  passo sem assumir resultados incompatíveis.
- **AC-26:** nem ações de fechamento ultrapassam o total absoluto.
- **AC-27:** teste final dirigido autorizado pode ocorrer dentro da reserva
  apropriada.
- **AC-28:** leitura exploratória é bloqueada dentro da reserva de fechamento.
- **AC-29:** tentativa de incluir `.env`, credencial ou dump completo é
  removida ou bloqueada, com regressão contra vazamento.
- **AC-30:** consultas Git mantêm ambiente e allowlist read-only atuais.
- **AC-31:** contexto é imutável e preserva a identidade exata do budget.
- **AC-32:** valor que não seja `ExecutionBudget` é rejeitado explicitamente.
- **AC-33:** `run_skill` sem contexto preserva o caminho e resultado legados.
- **AC-34:** a mesma instância de contexto chega ao limite de dispatcher.
- **AC-35:** transportar contexto não chama `consume` nem altera `used_units`.
- **AC-36:** criar contexto não acessa filesystem, subprocesso ou rede.
- **AC-37:** contexto não adiciona campos nem altera o resultado público da
  skill.
- **AC-38:** consumo bem-sucedido retorna novo contexto e preserva integralmente
  o snapshot anterior.
- **AC-39:** múltiplas transições mantêm uma cadeia determinística de snapshots.
- **AC-40:** contexto delega categoria, unidades e decisão sem duplicar regras
  do budget.
- **AC-41:** reserva ou checkpoint bloqueado propaga `ExecutionBudgetReserved`
  e não altera o contexto anterior.
- **AC-42:** limite absoluto propaga `ExecutionBudgetExceeded` e não altera o
  contexto anterior.
- **AC-43:** decisão ALLOWED consome antes e chama o processo exatamente uma vez.
- **AC-44:** decisão WARNING também consome e executa, sem criar checkpoint.
- **AC-45:** CHECKPOINT_REQUIRED usa erro próprio e bloqueia antes do efeito.
- **AC-46:** RESERVED bloqueia antes do efeito e preserva o contexto anterior.
- **AC-47:** EXHAUSTED bloqueia antes do efeito e preserva o contexto anterior.
- **AC-48:** categoria e custo são explícitos e chegam intactos ao domínio.
- **AC-49:** falha do processo permanece visível e conserva o contexto já
  consumido.
- **AC-50:** assinatura, retorno e comportamento do `run_process` legado não
  mudam.
- **AC-51:** git-preflight legado e budget-aware produzem resultado funcional
  equivalente quando a probe é permitida.
- **AC-52:** a API externa budget-aware devolve contexto N+1 sem alterar N.
- **AC-53:** WARNING executa e devolve o contexto avançado.
- **AC-54:** CHECKPOINT_REQUIRED bloqueia antes de qualquer subprocesso.
- **AC-55:** RESERVED bloqueia antes de qualquer subprocesso.
- **AC-56:** EXHAUSTED bloqueia antes de qualquer subprocesso.
- **AC-57:** falha da probe conserva consumo e não é mascarada pelo handler
  legado.
- **AC-58:** somente git-preflight possui handler budget-aware; demais skills e
  `run_skill` permanecem legados.
- **AC-59:** o caminho budget-aware executa o mesmo número total de probes e
  subprocessos que o caminho legado equivalente.
- **AC-60:** cada variante individual do inspector executa a probe selecionada
  exatamente uma vez; somente a variante budget-aware consome uma unidade.

## Plano de Testes

| Critérios | Tipo | Arquivo futuro | Contrato comprovado |
|---|---|---|---|
| AC-01–AC-05, AC-15, AC-16, AC-26 | unitário | `tests/test_execution_budget.py` | transições, limiares, reservas e total |
| AC-06, AC-07, AC-11, AC-19–AC-21, AC-25 | unitário/segurança | `tests/test_execution_checkpoint.py` | imutabilidade, handoff e zero mutação |
| AC-08 | unitário | `tests/test_execution_budget.py` | rejeição dos parâmetros inválidos do domínio |
| AC-14 | unitário | `tests/test_execution_configuration.py` | schema, defaults e compatibilidade futuros |
| AC-12, AC-17, AC-18 | unitário | `tests/test_execution_actions.py` | assinaturas e repetição auditável |
| AC-22–AC-24 | integração | `tests/test_execution_integration.py` | contexto atravessa bordas reais |
| AC-27–AC-29 | segurança | `tests/test_execution_security.py` | permitido, bloqueado e regressão |
| AC-13, AC-30 | regressão | `tests/test_execution_regression.py` | CLI/config/skills/Git existentes |
| AC-31–AC-37 | unitário/integração | `tests/test_execution_context.py` | contexto, transporte sem consumo e compatibilidade |
| AC-38–AC-42 | unitário | `tests/test_execution_context.py` | transições imutáveis, decisões e erros preservados |
| AC-43–AC-50 | unitário/integração | `tests/test_budgeted_process.py` | autorização, consumo anterior ao efeito e compatibilidade |
| AC-51–AC-58 | integração/regressão | `tests/test_budgeted_skill_execution.py` | primeiro caminho real e retorno do contexto |
| AC-59–AC-60 | caracterização/regressão | `tests/test_budgeted_skill_execution.py` | ausência de probe e subprocesso duplicados |

Cada teste novo deve citar `Spec: HERMES-0011 / AC-XX`. AC-29 compõe a tríade
de segurança: comportamento permitido (metadados sanitizados), bloqueado
(entrada sensível) e regressão (nenhuma saída pública contém o valor). AC-27,
AC-28 e AC-30 cobrem respectivamente ação permitida, ação bloqueada e
preservação do contrato Git.

### Testes de caracterização existentes

- configuração: `tests/test_configuration.py` cobre schema fechado, defaults,
  template canônico, paths contidos e rejeição de `.env` como fonte;
- erros/CLI: `tests/test_cli.py`, `tests/test_results.py` e
  `tests/test_presentation.py` cobrem códigos, ausência de traceback e
  sanitização;
- skills: `tests/test_skills.py`, `tests/test_skill_registry.py`,
  `tests/test_skill_policy.py` e `tests/test_skill_execution.py` cobrem
  carregamento inerte, registry, plano, despacho, imutabilidade e read-only;
- orquestração/subprocessos: `tests/test_preflight.py`,
  `tests/test_processes.py`, `tests/test_git_inspector.py` e
  `tests/test_git_security.py` cobrem composição, timeout e Git seguro;
- análise: `tests/test_analysis_*.py` caracteriza orçamento de contexto e borda
  de adapter, mas não orçamento de ações.

Lacunas atuais: não há teste ou código de sessão, journal, retry, ação,
checkpoint, handoff ou repetição transversal. Não há teste de captura de
`ResourceExhausted`, coerentemente com a ausência dessa integração.

## Plano de Implementação em Pequenas Fases

1. **Domínio puro:** modelos, categorias, erros, transições e testes unitários,
   sem integrar CLI ou handlers.
2. **Configuração:** adicionar `[execution]` opcional ao schema e ao template
   canônico, escolher números default com evidência de calibração e preservar
   configs antigas.
3. **Journal e repetição:** assinaturas canônicas, `state_revision`, limites e
   testes de deduplicação sem cache.
4. **Checkpoint/handoff:** objeto imutável, JSON/Markdown, sanitização e testes
   que provem ausência de filesystem, processo e rede.
5. **Integração piloto:** um único contexto em `skill run`, começando por
   `git-preflight`, instrumentando `run_process` e leituras necessárias sem
   alterar allowlists.
6. **Expansão controlada:** code/mission audit e comandos legados, com testes de
   caracterização rodando a cada borda migrada.
7. **Skills orientativas:** somente após o núcleo impor o contrato, adicionar
   `execution-budget` e `checkpoint-handoff`, empacotamento e testes próprios.
8. **Dogfooding:** medir traces locais, revisar defaults e validar handoff em
   execução real sem depender do contador externo.

Cada fase exige atualização desta spec para status apropriado, testes
direcionados, suíte completa, `compileall`, build e evidência concreta antes de
“Implementado”.

## Skills Futuras

### `execution-budget`

Ensinará planejamento anterior à exploração, leituras dirigidas, justificativa
de repetição, preservação das reservas e checkpoint precoce. Ela orienta o
agente, mas não autoriza nem substitui o enforcement do núcleo.

### `checkpoint-handoff`

Ao ser solicitada ou exigida, orientará parar exploração, usar somente estado
já capturado, listar feito/restante, recomendar a próxima ação e não realizar
mutações adicionais.

### `spec-guardian`

Evolução posterior, fora do escopo. Deve tratar especificação aprovada como
fonte superior a teste inconsistente e emitir `SPEC_TEST_CONFLICT` ou
equivalente em vez de alterar produção apenas para deixar o teste verde.

## Arquivos Provavelmente Afetados em Implementação Futura

- `src/hermes_ops/core/execution.py` (novo domínio);
- `src/hermes_ops/core/errors.py`;
- `src/hermes_ops/core/configuration.py`;
- `src/hermes_ops/core/processes.py`;
- `src/hermes_ops/core/presentation.py`;
- `src/hermes_ops/skills/executor.py`;
- `src/hermes_ops/skills/controlled_reader.py`;
- `src/hermes_ops/cli.py`;
- `src/hermes_ops/templates/project.toml`;
- testes listados no plano;
- `skills/execution-budget/SKILL.md` e
  `skills/checkpoint-handoff/SKILL.md`, somente em fase posterior;
- `pyproject.toml`, quando as skills forem empacotadas.

## Compatibilidade

Configurações antigas sem `[execution]` permanecem válidas e recebem defaults.
Assinaturas públicas existentes continuam aceitas durante a migração; contexto
novo deve ser keyword-only ou criado internamente. Resultados normais mantêm
campos e exit codes existentes; avisos/checkpoints entram de modo versionado.
O budget de caracteres da HERMES-0010 permanece independente do budget de
ações e não deve ser renomeado ou reutilizado.

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa descartada |
|---|---|---|---|
| 2026-08-12 | Classificar 32/32 como não observável | Nenhum contrato, símbolo ou adapter fornece contador | Inferir saldo por `ResourceExhausted` |
| 2026-08-12 | Usar unidade lógica por ação atômica | Determinístico e auditável sem falsa precisão | Estimar tokens ou custo do provider |
| 2026-08-12 | Integrar no executor e nas bordas reais | Cobre API e operações internas | Contar somente comandos da CLI |
| 2026-08-12 | Estado explícito e imutável | Facilita teste, isolamento e retomada | Singleton de sessão |
| 2026-08-12 | Checkpoint usa fatos já registrados | Garante ausência de mutação/coleta escondida | Rodar Git e reler arquivos no fechamento |
| 2026-08-12 | JSON é contrato e Markdown é visão | Evita duas fontes de verdade | Handoff somente textual |
| 2026-08-12 | Repetição exata exige justificativa | Regra simples, extensível e auditável | Cache ou similaridade semântica |

## Decisões Abertas Antes da Aprovação

- valores numéricos dos defaults, após coleta de traces locais;
- tamanho máximo do journal e de cada coleção do checkpoint;
- allowlist exata de ações de validação e fechamento por comando;
- forma versionada de fornecer checkpoint anterior à API/CLI;
- se o primeiro piloto cobre apenas `skill run git-preflight` ou também
  `preflight` legado na mesma fase;
- mapeamento de novos erros para exit codes públicos sem quebrar os existentes.

## Alternativas Descartadas

### Usar o contador externo 32/32

Não existe acesso programático comprovado. Inventar integração produziria uma
garantia falsa e acoplamento a infraestrutura não representada no projeto.

### Reutilizar ContextBudget da HERMES-0010

Ele mede caracteres de um payload canônico, não ações ou fases. Misturar os
conceitos tornaria ambos menos precisos.

### Checkpoint que consulta Git no momento de fechar

Consumiria justamente as ações reservadas e poderia falhar externamente. O
checkpoint deve usar apenas dados já registrados; uma consulta final dirigida,
se necessária, é uma ação orçada anterior.

### Cache automático de leituras e testes

Exige invalidação e semântica de estado prematuras. Assinatura exata mais
`state_revision` resolve o caso confirmado com contrato simples.

### Apenas criar skills comportamentais

Orientação textual não impõe limite nas bordas de execução. As skills só fazem
sentido depois que o núcleo possui enforcement.

## Riscos Conhecidos

- Como o limite externo não é observável, o checkpoint local ainda pode chegar
  tarde se ações internas e tool calls externos não tiverem relação estável.
- Instrumentação parcial cria falsa sensação de cobertura; toda borda adotada
  deve declarar quais ações ainda não são contadas.
- Unidade uniforme pode subestimar buscas amplas e superestimar leituras
  pequenas; traces devem orientar pesos futuros.
- `state_revision` incorreta pode bloquear trabalho necessário ou liberar
  repetição; somente mutações explicitamente registradas podem alterá-la.
- Handoff pode crescer ou vazar dados se limites e sanitização não forem
  aplicados antes da serialização.
- Defaults sem calibração podem encerrar cedo demais ou tarde demais; por isso
  seus números permanecem decisão aberta enquanto a spec é Rascunho.
- Passar contexto por muitas camadas pode pressionar APIs existentes; migração
  deve ser incremental e compatível.

## Evidências da Implementação

Implementação parcial das fases 0011A (domínio puro), 0011B (transporte de
contexto), 0011C (transição imutável), 0011D (primeira borda isolada) e 0011E
(primeiro caminho de produção). O status permanece `Rascunho` porque defaults,
configuração, journal, checkpoint e adoção ampla continuam abertos.

| Campo | Valor |
|---|---|
| Testes direcionados | `.venv\\Scripts\\python.exe -m pytest tests/test_execution_budget.py -q` → `27 passed` |
| Testes ExecutionContext | `.venv\\Scripts\\python.exe -m pytest tests/test_execution_context.py -q` → `17 passed` |
| Budget + contexto | `.venv\\Scripts\\python.exe -m pytest tests/test_execution_budget.py tests/test_execution_context.py -q` → `44 passed` |
| Regressão do executor 0011C | `.venv\\Scripts\\python.exe -m pytest tests/test_skill_execution.py -q --basetemp <TEMP>` → `54 passed` |
| Borda budget-aware | `.venv\\Scripts\\python.exe -m pytest tests/test_budgeted_process.py -q --basetemp <TEMP>` → `10 passed` |
| Budget + contexto + borda | `.venv\\Scripts\\python.exe -m pytest tests/test_execution_budget.py tests/test_execution_context.py tests/test_budgeted_process.py -q --basetemp <TEMP>` → `54 passed` |
| Regressão de processes | `.venv\\Scripts\\python.exe -m pytest tests/test_processes.py -q --basetemp <TEMP>` → `9 passed` |
| Caminho git-preflight budget-aware | `.venv\\Scripts\\python.exe -m pytest tests/test_budgeted_skill_execution.py -q --basetemp <TEMP>` → `11 passed` |
| Budget e caminho completo | `.venv\\Scripts\\python.exe -m pytest tests/test_execution_budget.py tests/test_execution_context.py tests/test_budgeted_process.py tests/test_budgeted_skill_execution.py -q --basetemp <TEMP>` → `65 passed` |
| Regressões do caminho escolhido | `.venv\\Scripts\\python.exe -m pytest tests/test_git_inspector.py tests/test_preflight.py tests/test_skill_execution.py tests/test_budgeted_skill_execution.py -q --basetemp <TEMP>` → `87 passed` |
| Regressões de skills | `.venv\\Scripts\\python.exe -m pytest tests/test_skill_execution.py tests/test_skill_registry.py tests/test_skill_policy.py -q --basetemp <TEMP>` → `162 passed, 6 skipped` |
| Suíte completa | `.venv\\Scripts\\python.exe -m pytest -q --basetemp <TEMP>` → `563 passed, 11 skipped` |
| compileall | `.venv\\Scripts\\python.exe -m compileall src` → OK |
| Limitações | primeira execução completa terminou no teardown do pytest por `WinError 5`; repetição com basetemp isolado passou |

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|---|---|---|---|
| 2026-08-12 | Codex | Auditoria inicial, classificação B e proposta técnica | Dogfooding Lucre Agro |
| 2026-08-12 | Codex | Desambiguou thresholds/reservas/categorias e implementou somente o domínio puro | Fase HERMES-0011A |
| 2026-08-12 | Codex | Adicionou contexto mínimo e transporte até o dispatcher, sem consumo | Fase HERMES-0011B |
| 2026-08-12 | Codex | Formalizou transição contexto N → N+1 sem instrumentar efeitos | Fase HERMES-0011C |
| 2026-08-12 | Codex | Adicionou primeira borda budget-aware isolada sobre subprocesso | Fase HERMES-0011D |
| 2026-08-12 | Codex | Adotou uma probe Git read-only no caminho git-preflight | Fase HERMES-0011E |
| 2026-08-12 | Codex | Substituiu a probe existente sem adicionar subprocesso | Correção HERMES-0011E |
