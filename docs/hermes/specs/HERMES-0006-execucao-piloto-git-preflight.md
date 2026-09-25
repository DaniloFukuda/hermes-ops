+++
schema_version = 1
id = "HERMES-0006"
status = "Implementado"
[[acceptance_criteria]]
id = "AC-01"
test_file = "tests/test_skill_execution.py"
test_function = "test_run_skill_requires_explicit_inputs"
[[acceptance_criteria]]
id = "AC-02"
test_file = "tests/test_skill_execution.py"
test_function = "test_discovery_precedes_planning_dispatch_and_handler"
[[acceptance_criteria]]
id = "AC-03"
test_file = "tests/test_skill_execution.py"
test_function = "test_real_registry_and_plan_are_mandatory"
[[acceptance_criteria]]
id = "AC-04"
test_file = "tests/test_skill_execution.py"
test_function = "test_discovery_failure_prevents_all_later_phases"
[[acceptance_criteria]]
id = "AC-05"
test_file = "tests/test_skill_execution.py"
test_function = "test_policy_failure_prevents_dispatch_and_handler"
[[acceptance_criteria]]
id = "AC-06"
test_file = "tests/test_skill_execution.py"
test_function = "test_dispatch_rejects_non_unit_request"
[[acceptance_criteria]]
id = "AC-07"
test_file = "tests/test_skill_execution.py"
test_function = "test_dispatch_supports_only_git_preflight"
[[acceptance_criteria]]
id = "AC-08"
test_file = "tests/test_skill_execution.py"
test_function = "test_unsupported_skill_is_blocked_without_fallback"
[[acceptance_criteria]]
id = "AC-09"
test_file = "tests/test_skill_execution.py"
test_function = "test_dispatch_never_derives_or_discovers_handler"
[[acceptance_criteria]]
id = "AC-10"
test_file = "tests/test_skill_execution.py"
test_function = "test_dangerous_skill_body_remains_inert"
[[acceptance_criteria]]
id = "AC-11"
test_file = "tests/test_skill_execution.py"
test_function = "test_git_preflight_reuses_existing_orchestration"
[[acceptance_criteria]]
id = "AC-12"
test_file = "tests/test_skill_execution.py"
test_function = "test_git_preflight_reports_existing_checks"
[[acceptance_criteria]]
id = "AC-13"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_models_are_frozen_slotted_and_deeply_immutable"
[[acceptance_criteria]]
id = "AC-14"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_result_has_minimal_ordered_snapshot"
[[acceptance_criteria]]
id = "AC-15"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_status_distinguishes_findings_from_no_report"
[[acceptance_criteria]]
id = "AC-16"
test_file = "tests/test_skill_execution.py"
test_function = "test_result_excludes_body_environment_and_secrets"
[[acceptance_criteria]]
id = "AC-17"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_does_not_write_files"
[[acceptance_criteria]]
id = "AC-18"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_uses_no_mutating_git_operation"
[[acceptance_criteria]]
id = "AC-19"
test_file = "tests/test_skill_execution.py"
test_function = "test_processes_use_central_process_boundary"
[[acceptance_criteria]]
id = "AC-20"
test_file = "tests/test_skill_execution.py"
test_function = "test_user_cannot_supply_process_or_shell"
[[acceptance_criteria]]
id = "AC-21"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_does_not_access_network"
[[acceptance_criteria]]
id = "AC-22"
test_file = "tests/test_skill_execution.py"
test_function = "test_strong_repository_snapshot_is_preserved"
[[acceptance_criteria]]
id = "AC-23"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_error_exposes_no_partial_result"
[[acceptance_criteria]]
id = "AC-24"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_does_not_mutate_inputs"
[[acceptance_criteria]]
id = "AC-25"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_is_deterministic"
[[acceptance_criteria]]
id = "AC-26"
test_file = "tests/test_skill_execution.py"
test_function = "test_negative_preflight_returns_complete_result_and_exit_code"
[[acceptance_criteria]]
id = "AC-27"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_git_preflight_cli"
[[acceptance_criteria]]
id = "AC-28"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_rejects_operational_flags"
[[acceptance_criteria]]
id = "AC-29"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_output_is_sanitized"
[[acceptance_criteria]]
id = "AC-30"
test_file = "tests/test_skill_execution.py"
test_function = "test_existing_commands_remain_compatible"
[[acceptance_criteria]]
id = "AC-31"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_uses_controlled_temporary_repository"
[[acceptance_criteria]]
id = "AC-32"
test_file = "tests/test_skill_execution.py"
test_function = "test_unsafe_local_git_config_remains_blocked"
[[acceptance_criteria]]
id = "AC-33"
test_file = "tests/test_skill_execution.py"
test_function = "test_required_and_optional_git_semantics_are_preserved"
[[acceptance_criteria]]
id = "AC-34"
test_file = "tests/test_cli.py"
test_function = "test_cli_uses_explicit_least_privilege_policy"
[[acceptance_criteria]]
id = "AC-35"
test_file = "tests/test_skill_execution.py"
test_function = "test_public_surface_has_no_generic_runner_pipeline_or_plugins"
[[acceptance_criteria]]
id = "AC-36"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_public_api_exports_only_return_contract_and_entrypoint"
[[acceptance_criteria]]
id = "AC-37"
test_file = "tests/test_skill_execution.py"
test_function = "test_execution_errors_are_stable_and_deterministic"
[[acceptance_criteria]]
id = "AC-38"
test_file = "tests/test_skill_execution.py"
test_function = "test_skill_execution_preserves_passive_loader_contract"
[[acceptance_criteria]]
id = "AC-39"
test_file = "tests/test_skill_execution.py"
test_function = "test_skill_execution_preserves_explicit_discovery_contract"
[[acceptance_criteria]]
id = "AC-40"
test_file = "tests/test_skill_execution.py"
test_function = "test_skill_execution_requires_approved_plan"
[[acceptance_criteria]]
id = "AC-41"
test_file = "tests/test_skill_execution.py"
test_function = "test_real_repository_contract_discovers_and_plans"
[[acceptance_criteria]]
id = "AC-42"
test_file = "tests/test_skill_execution.py"
test_function = "test_requirements_never_auto_authorize_policy"
[[acceptance_criteria]]
id = "AC-43"
test_file = "tests/test_skill_execution.py"
test_function = "test_source_details_mutation_cannot_change_evidence"
[[acceptance_criteria]]
id = "AC-44"
test_file = "tests/test_skill_execution.py"
test_function = "test_freeze_details_is_recursive_lossless_and_deterministic"
[[acceptance_criteria]]
id = "AC-45"
test_file = "tests/test_skill_execution.py"
test_function = "test_negative_report_differs_from_structural_execution_failure"
[[acceptance_criteria]]
id = "AC-46"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_semantic_errors_map_to_normative_exit_codes"
[[acceptance_criteria]]
id = "AC-47"
test_file = "tests/test_skill_execution.py"
test_function = "test_handler_reaches_only_audited_read_only_git_commands"
[[acceptance_criteria]]
id = "AC-48"
test_file = "tests/test_skill_execution.py"
test_function = "test_controlled_git_process_allowed_arbitrary_process_blocked"
[[acceptance_criteria]]
id = "AC-49"
test_file = "tests/test_skill_execution.py"
test_function = "test_dispatch_never_calls_dynamic_import_plugin_or_fallback"
[[acceptance_criteria]]
id = "AC-50"
test_file = "tests/test_cli.py"
test_function = "test_generic_valid_id_reaches_closed_dispatch_through_run_skill"
[[acceptance_criteria]]
id = "AC-51"
test_file = "tests/test_cli.py"
test_function = "test_real_repository_dogfooding_exercises_full_skill_pipeline"
[[acceptance_criteria]]
id = "AC-52"
test_file = "tests/test_skill_execution.py"
test_function = "test_skill_preflight_semantics_match_legacy_commands"
+++

# HERMES-0006 — Execução Piloto Read-only da Skill git-preflight

## Status

Implementado

## Resumo para o Responsável pelo Projeto

Esta especificação propõe o primeiro uso operacional de uma skill real do
Hermes, limitado exclusivamente a `git-preflight` e às inspeções read-only já
existentes. O contrato `SKILL.md` continua sendo somente uma declaração: um
dispatcher fechado escolhe um handler interno conhecido, depois de discovery e
policy planning, sem executar texto, carregar plugins ou conceder poderes
genéricos.

## Contexto

HERMES-0003 implementou o contrato textual passivo e `load_skill`.
HERMES-0004 implementou discovery explícito e `SkillRegistry`. HERMES-0005
implementou `SkillPolicy`, `SkillPlan` e `plan_skills`, mas deliberadamente
não criou execução.

O repositório já possui comandos read-only maduros:

- `run_doctor(project)` valida caminho, configuração e ambiente;
- `run_worktree(project)` valida a raiz declarada, carrega configuração e usa
  `GitInspector`;
- `run_preflight(project)` compõe doctor e worktree e aplica a política Git
  configurada;
- `GitInspector.inspect(project)` usa somente consultas Git controladas,
  ambiente neutralizado, timeout e parsing de porcelain NUL-delimited;
- `Report`, `CheckResult` e `Status` já representam resultados estruturados.

A realidade verificada na criação deste rascunho é que existe uma única skill
operacional concreta em `skills/`: `skills/git-preflight/SKILL.md`. Não
existem runner, `run_skill`, `execute_skill`, pipeline ou CLI de skills.

Após a movimentação da documentação geral para `docs/hermes/skills/README.md`,
o diretório operacional `skills/` contém somente candidatos válidos. A prova
pública real `discover_skills(project_root)` constrói `SkillRegistry`, encontra
`git-preflight` e preserva a regra fail-closed da HERMES-0004, sem exceção para
README ou arquivos soltos.

O contrato real descoberto possui `schema_version=1`, `version=1`, status
`ACTIVE`, risco `LOW`, `requires=("git",)` e `allows_write=false`. Sob a policy
piloto explícita definida nesta especificação, ele é elegível e chega a um
`SkillPlan` real sem alteração do contrato.

## Problema Confirmado

As camadas atuais conseguem carregar, descobrir e autorizar o planejamento de
`git-preflight`, mas não existe uma fronteira operacional que conecte um
`SkillPlan` aprovado à lógica read-only já implementada.

Sem uma fronteira pequena e fechada, um primeiro executor poderia introduzir
interpretação de Markdown, resolução dinâmica de handlers, comandos
arbitrários, duplicação das proteções Git ou bypass de registry e policy. Isso
transformaria uma experiência de dogfooding limitada em um runner genérico
antes de existir contrato de segurança para tal responsabilidade.

Também há acoplamento de orquestração em `run_preflight` e `run_worktree`:
essas funções retornam `Report`, que é um modelo de domínio/apresentação
compartilhado pelo CLI. O núcleo Git reutilizável já está separado em
`GitInspector`; portanto o piloto pode inicialmente adaptar o `Report`
existente, sem duplicar regras. Uma extração adicional só será aceita se testes
demonstrarem necessidade concreta.

## Explicação em Linguagem Simples

O Hermes continuará sem “ler instruções” do arquivo da skill. O arquivo apenas
prova que a skill existe e declara seu contrato. Depois disso, o Hermes verifica
a política e consulta uma pequena tabela interna que conhece exatamente um
nome: `git-preflight`.

Se esse nome for aprovado, o Hermes chama a verificação read-only que já usa
hoje. Se qualquer outro nome chegar ao dispatcher, a operação para com erro.
Não existe tentativa de adivinhar módulo, função, comando ou script.

## Comportamento Atual

1. `discover_skills(project_root)` encontra contratos válidos somente na raiz
   explícita.
2. `plan_skills(registry, requested_ids, policy)` produz plano imutável ou
   falha antes de qualquer efeito operacional.
3. `run_preflight(project)` e `run_worktree(project)` produzem `Report`.
4. `GitInspector` consulta `rev-parse`, `symbolic-ref` e `status` com
   argumentos fixos e proteções de ambiente/configuração.
5. O CLI oferece `doctor`, `worktree` e `preflight`.
6. Não há execução de skills nem associação entre ID e handler.

## Comportamento Desejado

Adicionar futuramente um piloto com fluxo normativo:

```text
project_root explícito
    -> discover_skills(project_root)
    -> SkillRegistry
    -> plan_skills(registry, ("git-preflight",), policy)
    -> SkillPlan
    -> dispatcher fechado
    -> handler interno run_git_preflight
    -> SkillExecutionResult imutável
```

A API proposta é:

```text
SkillExecutionStatus
SkillExecutionEvidence
SkillExecutionResult
SkillExecutionError
run_skill(project_root, skill_id, policy) -> SkillExecutionResult
```

Os três modelos precisam ser públicos porque aparecem diretamente no contrato
do valor retornado. `SkillExecutionError` segue o padrão dos erros esperados já
exportados pelo pacote e permite preservar os dois códigos da nova fronteira.
Nenhum handler, dispatcher, builder ou função de congelamento é exportado.
Testes exercitam preferencialmente `run_skill` e os tipos públicos; testes
unitários de invariantes testam o builder por efeitos observáveis através do
entry point, sem tornar auxiliares públicos.

Os auxiliares internos propostos são:

```text
_dispatch_skill(plan, project_root) -> SkillExecutionResult
_run_git_preflight(project_root) -> SkillExecutionResult
_build_execution_result(skill_id, report) -> SkillExecutionResult
```

`run_skill` aceita um único ID textual porque multi-skill e chaining estão
fora do piloto. Ele exige uma instância explícita de `SkillPolicy`; não cria
fallback permissivo. O dispatcher exige um plano com exatamente uma skill e
compara o ID literalmente com `"git-preflight"`.

`_run_git_preflight` reutiliza `run_preflight(project_root)`. A adaptação
preserva `Report.exit_code` e converte seus resultados para evidências
imutáveis. Não replica comandos Git, classificação de erros ou política de
working tree.

### Modelo de Resultado

Os modelos públicos mínimos propostos são:

```text
SkillExecutionStatus(str, Enum):
    PASSED = "passed"
    COMPLETED_WITH_FINDINGS = "completed_with_findings"

SkillExecutionEvidence:
    name: str
    status: Status
    message: str
    details: FrozenDetails
    code: str

SkillExecutionResult:
    skill_id: str
    status: SkillExecutionStatus
    exit_code: int
    evidence: tuple[SkillExecutionEvidence, ...]
```

Os dois dataclasses usam `frozen=True, slots=True`. `SkillExecutionStatus` é
fechado: `PASSED` significa que o handler retornou `Report` com exit code zero;
`COMPLETED_WITH_FINDINGS` significa que o handler retornou `Report` completo
com exit code diferente de zero. Este segundo estado não é crash nem falha do
executor: o preflight executou corretamente e detectou uma condição negativa.

Se não for possível obter um `Report` porque a nova fronteira é estruturalmente
inválida, ocorre `SkillExecutionError`. Uma exceção inesperada não é engolida
nem convertida em resultado falso; ela alcança o boundary final do CLI como
`external_failure`. Portanto não existe status público para execução que não
aconteceu.

`CheckResult` e `Report` são frozen/slotted, mas `CheckResult.details` aceita
`Mapping[str, Any]` e pode referenciar dicts, listas ou valores aninhados
mutáveis. Por isso o resultado público nunca armazena diretamente esses
objetos. Cada check é copiado para `SkillExecutionEvidence`, e `details` passa
por congelamento recursivo antes da construção do resultado.

`FrozenDetails` é uma representação profundamente imutável e determinística:

```text
None, str, int, float e bool -> preservar valor
Enum -> preservar seu valor textual estável
Path -> converter para string; sanitizar somente na apresentação pública
bytes -> decodificar como UTF-8 com a mesma política segura de resultados
Mapping -> tuple de pares (chave string, valor congelado), ordenada pela chave
list ou tuple -> tuple de valores congelados, preservando a ordem
set ou frozenset -> tuple de valores congelados, ordenada pela serialização
dataclass suportado -> congelar recursivamente seus campos em ordem declarada
tipo não suportado -> SKILL_EXECUTION_INVALID, sem perda ou repr silencioso
```

Chaves de mappings são convertidas para string de modo coerente com
`core.results._json_safe`; colisão após conversão é inválida. A ordenação de
sets usa a mesma normalização JSON determinística já empregada pelo projeto.
Nenhum dict, list, set ou objeto mutável original sobrevive no snapshot. Alterar
`CheckResult.details` ou qualquer estrutura de origem depois da conversão não
muda a evidência pública.

O resultado não inclui o corpo do `SKILL.md`, objetos de registry, policy,
plano, comandos executados, environment ou caminhos externos desnecessários.
A apresentação pública continua obrigada a usar o sanitizador central.

### Dispatcher Fechado

A versão inicial possui uma associação literal e privada:

```text
"git-preflight" -> _run_git_preflight
```

Não há import dinâmico, convenção de nome, acesso a atributo calculado, leitura
de handler no contrato, entry point, plugin discovery ou fallback. Um plano
válido contendo outro ID falha com `SKILL_EXECUTION_NOT_SUPPORTED` antes de
qualquer handler.

### CLI de Dogfooding

A extensão futura avaliada é:

```text
python -m hermes_ops skill run git-preflight --project . --format text
```

O CLI aceita somente o ID posicional, a raiz explícita e os formatos já
suportados `text|json`. Não aceita `--command`, `--shell`, `--handler`,
`--module`, `--script` ou `--python`.

Durante o piloto, o boundary do CLI constrói uma policy explícita e
least-privilege exclusiva para o contrato conhecido:

```text
max_risk = LOW
allow_write = false
available_requires = frozenset({"git"})
```

Essa policy permite apenas o planejamento; não afirma que o executável Git está
operacional. A disponibilidade real continua sendo verificada de forma
controlada pelo handler e reportada como resultado. A API Python continua
exigindo policy do chamador.

Os três valores são constantes auditadas do boundary do piloto e são
construídos antes de `plan_skills`. É proibido ler `skill.requires` para copiar,
derivar, completar ou ampliar `available_requires`. Em particular, se uma
policy externa omitir `"git"`, o contrato real continua declarando
`requires=("git",)`, mas HERMES-0005 bloqueia o plano com
`SKILL_POLICY_REQUIREMENT_UNAVAILABLE`; a declaração nunca autoriza a si mesma.

O parser aceita qualquer ID sintaticamente válido. Ele não restringe argparse
ao literal `git-preflight`: isso permite comprovar que uma skill válida,
descoberta e planejada, mas sem handler, chega ao dispatcher e recebe
`SKILL_EXECUTION_NOT_SUPPORTED`. O CLI chama somente `run_skill`; nunca chama
dispatcher ou handler privado diretamente.

Os comandos `doctor`, `worktree` e `preflight` permanecem disponíveis e
inalterados para comparação durante o dogfooding.

## Fora do Escopo

- Runner genérico ou registro extensível de handlers.
- Capabilities genéricas ou capability grants.
- Execução de `safe-edit`, `test-runner`, `code-audit`, `diff-guard` ou
  `characterization-tests`.
- Pipeline, chaining ou execução de múltiplas skills.
- Plugins, entry points, dynamic import ou handler derivado do ID.
- Interpretação ou execução de Markdown.
- Comando, script, módulo Python ou shell fornecido pelo usuário.
- Escrita em filesystem.
- Git mutável, incluindo add, commit, push, checkout, switch, reset, clean,
  stash ou alteração de refs/configuração.
- Rede, download, instalação ou resolução de dependências.
- Sandbox, autorização humana, confirmação, rollback ou logs de execução.
- Alteração do contrato `skills/git-preflight/SKILL.md`.
- Migração ou criação de outras skills.
- Remoção dos comandos atuais.
- Refatoração ampla de `preflight`, `worktree` ou `GitInspector`.

## Entradas

### API Python

- `project_root`: raiz explícita, sem descoberta de pais ou siblings.
- `skill_id`: string exata; no piloto somente `git-preflight` é executável.
- `policy`: instância válida e explícita de `SkillPolicy`.

### CLI futura

- Subcomandos literais `skill run`.
- ID posicional.
- `--project` obrigatório.
- `--format text|json`, com comportamento coerente com o CLI existente.

O corpo do `SKILL.md` nunca é uma entrada operacional para o handler.

## Saídas

- `SkillExecutionResult` imutável.
- `skill_id` executado.
- `status` fechado distinguindo PASS de conclusão com findings.
- `exit_code` preservado do `Report` de preflight.
- `evidence` como tuple de snapshots profundamente imutáveis e estruturados.
- Texto ou JSON sanitizado no boundary de apresentação do CLI.

Nenhum arquivo, estado Git, configuração, variável de ambiente herdada ou
objeto recebido é alterado.

## Invariantes e Regras de Segurança

1. Discovery sempre precede planning.
2. Planning sempre precede dispatch.
3. Dispatch sempre precede handler.
4. Policy bloqueada impede qualquer chamada ao handler.
5. Somente `git-preflight` possui handler.
6. O dispatcher nunca deriva comportamento do corpo ou ID.
7. O `SKILL.md` permanece declarativo e inerte.
8. Nenhuma forma de eval, exec ou import dinâmico é permitida.
9. Nenhum argumento do usuário se transforma em comando.
10. Toda criação de processo Git continua passando por
    `hermes_ops.core.processes` via `GitInspector`.
11. Somente argumentos Git fixos e read-only existentes são usados.
12. Locks opcionais, redirecionamentos `GIT_*`, configuração global/sistema,
    fsmonitor e prompts continuam neutralizados.
13. Configuração local com include/includeIf/filter continua bloqueada.
14. O project root declarado deve coincidir com a raiz Git.
15. Não há escrita, rede, shell, plugins ou chaining.
16. Falha nunca produz resultado de sucesso parcial.
17. Registry, policy, plan e SkillDefinition não são mutados.
18. Evidências públicas passam pelo sanitizador central.
19. Segredos, environment e paths externos desnecessários não são expostos.
20. Os comandos existentes permanecem compatíveis.
21. `available_requires` nunca é derivado dos requirements da skill.
22. Um `Report` negativo continua sendo execução concluída, não crash.
23. Nenhum resultado é criado quando o handler não retorna `Report`.
24. Códigos semânticos permanecem distintos de exit codes numéricos.
25. Nenhuma estrutura mutável de `CheckResult.details` sobrevive no resultado.

O subprocess Git interno, controlado e read-only, é permitido somente porque já
faz parte de `run_preflight`/`GitInspector`. As operações atualmente alcançáveis
são exatamente:

```text
git rev-parse --is-inside-work-tree
git rev-parse --show-toplevel
git rev-parse --verify HEAD
git symbolic-ref --quiet --short HEAD
git status --porcelain=v1 -z --untracked-files=all
```

Essa enumeração não autoriza comandos Git adicionais. Continuam proibidos
subprocess arbitrário, executável ou argumento vindo do usuário/skill, shell e
qualquer Git mutável.

## Pseudocódigo

### run_skill

```text
FUNÇÃO run_skill(project_root, skill_id, policy):
    VALIDAR que project_root foi fornecido explicitamente
    VALIDAR que skill_id é string exata
    VALIDAR que policy é SkillPolicy válida

    registry = discover_skills(project_root)

    plan = plan_skills(
        registry,
        tuple contendo somente skill_id,
        policy,
    )

    RETORNAR dispatch_skill(plan, project_root)
```

Nenhum passo entre discovery e planning executa a skill. Nenhum passo entre
planning e dispatch escolhe handler dinamicamente.

### dispatch_skill

```text
FUNÇÃO dispatch_skill(plan, project_root):
    VALIDAR que plan é SkillPlan real
    VALIDAR que plan contém exatamente uma skill

    skill = única skill do plano

    SE skill.id for exatamente "git-preflight":
        RETORNAR run_git_preflight(project_root)

    FALHAR com SKILL_EXECUTION_NOT_SUPPORTED
    NÃO procurar módulo
    NÃO interpretar contrato
    NÃO tentar fallback
```

### run_git_preflight

```text
FUNÇÃO run_git_preflight(project_root):
    TENTAR:
        report = executar a orquestração read-only existente run_preflight(project_root)

    SE run_preflight retornar Report, mesmo com exit_code diferente de zero:
        execução ocorreu
        RETORNAR build_execution_result("git-preflight", report)

    SE a fronteira detectar falha estrutural esperada antes de obter Report:
        FALHAR com SkillExecutionError específico

    SE ocorrer exceção inesperada:
        PROPAGAR ao boundary final
        NÃO fabricar Report
        NÃO fabricar SkillExecutionResult

    NÃO construir comandos a partir do usuário
    NÃO executar o corpo da skill
    NÃO alterar arquivos ou Git
```

### build_execution_result

```text
FUNÇÃO build_execution_result(skill_id, report):
    VALIDAR skill_id e Report

    evidências = tuple vazia
    PARA CADA CheckResult na ordem original:
        detalhes = congelar recursivamente CheckResult.details
        CONSTRUIR SkillExecutionEvidence imutável
        ACRESCENTAR à nova tuple sem reter estrutura mutável original

    exit_code = exit code determinístico já calculado pelo Report

    SE exit_code for zero:
        status = PASSED
    SENÃO:
        status = COMPLETED_WITH_FINDINGS

    CONSTRUIR resultado completo uma única vez
    RETORNAR SkillExecutionResult
```

### freeze_details

```text
FUNÇÃO freeze_details(valor):
    SE valor for escalar seguro:
        RETORNAR valor
    SE valor for Enum, Path ou bytes suportado:
        NORMALIZAR conforme a política de resultados existente
    SE valor for Mapping:
        CONVERTER chaves para strings e rejeitar colisões
        CONGELAR cada valor recursivamente
        RETORNAR tuple de pares ordenada por chave
    SE valor for list ou tuple:
        RETORNAR tuple dos itens congelados na ordem original
    SE valor for set ou frozenset:
        CONGELAR itens e ordenar por serialização canônica
        RETORNAR tuple ordenada
    SE valor for dataclass suportado:
        CONGELAR campos recursivamente na ordem declarada
    SENÃO:
        FALHAR com SKILL_EXECUTION_INVALID
        NÃO descartar nem converter silenciosamente com repr
```

### Boundary do CLI

```text
AO receber "skill run git-preflight":
    VALIDAR somente project, format e ID
    CONSTRUIR policy piloto explícita e conservadora
    CHAMAR run_skill
    SANITIZAR o resultado na apresentação
    EMITIR text ou JSON determinístico
    RETORNAR o exit_code do resultado

AO receber outro ID:
    SE o ID for sintaticamente válido, executar discovery e planning
    SE houver plano válido sem handler, dispatcher falha fechado
    com SKILL_EXECUTION_NOT_SUPPORTED

AO receber erro esperado antes ou durante dispatch:
    PRESERVAR código semântico original
    MAPEAR para exit code numérico conforme tabela normativa
    NÃO reclassificar como external_failure

AO receber exceção inesperada:
    USAR boundary final existente com external_failure e exit code 4
```

## Fluxo Principal

1. Receber raiz, ID e policy explícitos.
2. Validar tipos de boundary sem coerção insegura.
3. Executar `discover_skills(project_root)`.
4. Obter `SkillRegistry` real.
5. Executar `plan_skills(registry, (skill_id,), policy)`.
6. Interromper se registry, contrato ou policy falharem.
7. Entregar somente o `SkillPlan` aprovado ao dispatcher.
8. Validar plano unitário.
9. Comparar ID literalmente com `git-preflight`.
10. Chamar o handler interno.
11. Reutilizar `run_preflight`, que compõe doctor e worktree.
12. Reutilizar `GitInspector` indiretamente para inspeção Git protegida.
13. Adaptar o `Report` para resultado imutável.
14. Sanitizar somente na apresentação.
15. Retornar exit code preservado.

## Casos de Erro e Limites

| Situação | Comportamento | Código semântico |
|----------|---------------|-----------------|
| Contrato/discovery/registry inválido | Propagar `SkillContractError` ou `SkillRegistryError` original | Código existente intacto |
| Skill sintaticamente válida não encontrada | Propagar `SkillPolicyError` do planning | `SKILL_PLAN_SKILL_NOT_FOUND` |
| Policy inválida ou gate bloqueado | Propagar `SkillPolicyError`; handler não chamado | Código existente intacto |
| Argumento da nova API ou plano recebido pelo dispatcher é estruturalmente inválido | Falhar antes do handler | `SKILL_EXECUTION_INVALID` |
| Plano contém zero ou mais de uma skill | Falhar; piloto é unitário | `SKILL_EXECUTION_INVALID` |
| Skill planejada sem handler | Falhar sem fallback | `SKILL_EXECUTION_NOT_SUPPORTED` |
| Tipo de detalhe não pode ser congelado sem perda | Falhar antes de publicar resultado | `SKILL_EXECUTION_INVALID` |
| Path/configuração inválidos detectados pelo handler | Retornar resultado completo do preflight | Código existente no evidence |
| Git indisponível ou repositório ausente | Retornar resultado conforme required/optional | Código existente no evidence |
| Config Git insegura | Retornar resultado bloqueado | `git_unsafe_local_config` |
| Root Git divergente | Retornar resultado bloqueado | `git_root_mismatch` |
| Working tree suja | Retornar warning ou bloqueio conforme configuração | Código existente no evidence |
| Exceção inesperada antes de obter `Report` | Não fabricar resultado; boundary final sem traceback | `external_failure` |

Não se cria código alternativo para cada falha interna de preflight. O piloto
preserva os resultados estáveis existentes e adiciona somente dois erros de
fronteira de execução.

### Códigos semânticos e exit codes do processo

Código semântico identifica a causa; exit code numérico é somente o resultado
externo do processo CLI. O formatter sempre preserva o código semântico
específico. Erros esperados nunca são apagados e reclassificados como
`external_failure`.

A política numérica reutiliza a convenção atual do Hermes: `0` para conclusão
sem ERROR/BLOCKED, `1` para erro operacional representado por `Status.ERROR`,
`2` para entrada/configuração inválida, `3` para bloqueio e `4` para falha
externa inesperada.

| Cenário no CLI | Resultado/diagnóstico | Exit code numérico |
|----------------|-----------------------|-------------------|
| Handler retorna `Report.exit_code == 0` | `PASSED`, evidências completas | 0 |
| Handler retorna Report negativo | `COMPLETED_WITH_FINDINGS`, código dos checks preservado | Preservar exatamente `Report.exit_code` (1, 2, 3 ou 4) |
| Argparse rejeita sintaxe, ID inválido ou flag proibida | Erro de uso; handler não chamado | 2 |
| `SKILL_EXECUTION_INVALID` em entrada/estado estrutural esperado | Código semântico preservado | 2 |
| `SkillContractError` ou `SkillRegistryError` esperado | Código original preservado; bloqueio antes do handler | 3 |
| `SKILL_PLAN_SKILL_NOT_FOUND` | Código original preservado | 3 |
| Outro `SkillPolicyError`, incluindo requirement/risk/write/status | Código original preservado | 3 |
| `SKILL_EXECUTION_NOT_SUPPORTED` após plano válido | Código preservado; handler não chamado | 3 |
| Falha operacional esperada já convertida em CheckResult pelo handler | Resultado completo | Exit code calculado pelo Report |
| Exceção inesperada antes de obter Report | `external_failure`, sem resultado falso | 4 |

O exit code `1` não é usado como tradução genérica de exceções de domínio; ele
continua representando um `Report` concluído que contém `Status.ERROR`. O exit
code `4` retornado por um Report também é preservado, embora a origem usual de
`external_failure` seja o boundary final.

## Critérios de Aceitação

- **AC-01**: `run_skill` exige project root explícito, ID e policy válida.
- **AC-02**: Discovery real ocorre antes de qualquer planning, dispatch ou handler.
- **AC-03**: `plan_skills` real recebe o registry descoberto e ocorre antes do dispatch.
- **AC-04**: Falha de registry/discovery impede planning e handler.
- **AC-05**: Falha ou bloqueio de policy impede dispatch e handler.
- **AC-06**: O piloto aceita somente planos com exatamente uma skill.
- **AC-07**: O dispatcher reconhece literalmente somente `git-preflight`.
- **AC-08**: Skill planejada sem handler falha com `SKILL_EXECUTION_NOT_SUPPORTED`.
- **AC-09**: Não existe fallback, resolução de módulo ou derivação de handler pelo ID.
- **AC-10**: Body válido contendo shell, Python textual, marcador e `git reset --hard` permanece inerte e não influencia o handler.
- **AC-11**: O handler reutiliza `run_preflight` e não duplica inspeção Git.
- **AC-12**: A execução verifica path, configuração, Git, repositório, branch e working tree conforme lógica existente.
- **AC-13**: `SkillExecutionResult` e `SkillExecutionEvidence` são dataclasses frozen/slotted e usam apenas membros profundamente imutáveis.
- **AC-14**: Resultado contém somente skill_id, status, exit_code e tuple ordenada de snapshots estruturados.
- **AC-15**: Status fechado distingue `PASSED` de `COMPLETED_WITH_FINDINGS`; ausência de Report não produz resultado.
- **AC-16**: Resultado e evidências não expõem corpo da skill, environment ou segredos.
- **AC-17**: Nenhuma escrita em arquivos ocorre no piloto.
- **AC-18**: Nenhuma operação Git mutável ocorre no piloto.
- **AC-19**: Todos os processos continuam passando pela abstração central existente.
- **AC-20**: Nenhum subprocess ou shell arbitrário pode ser fornecido pelo usuário.
- **AC-21**: Nenhum acesso de rede ocorre.
- **AC-22**: Snapshot antes/depois de porcelain NUL, HEAD, refs do fixture e bytes dos arquivos é idêntico, sem comparar mtime/atime.
- **AC-23**: Resultado não é retornado parcialmente em erro.
- **AC-24**: Registry, policy, plan e SkillDefinition permanecem imutados.
- **AC-25**: Execuções equivalentes sobre estado equivalente produzem resultado equivalente.
- **AC-26**: Report negativo produz resultado completo e preserva seu exit code no CLI, sem ser tratado como crash.
- **AC-27**: A CLI aceita `skill run git-preflight --project ... --format text|json`.
- **AC-28**: A CLI rejeita command, shell, handler, module, script e python.
- **AC-29**: Saída pública text/JSON passa pelo sanitizador central.
- **AC-30**: Comandos `doctor`, `worktree` e `preflight` permanecem compatíveis.
- **AC-31**: Testes usam repositório Git temporário e controlado.
- **AC-32**: Configuração local Git insegura continua bloqueada.
- **AC-33**: Git opcional e obrigatório preservam a semântica existente.
- **AC-34**: Policy piloto é construída no boundary antes do planning com LOW, write false e requirement literal `git`.
- **AC-35**: O piloto não cria runner genérico, pipeline, plugins ou chaining.
- **AC-36**: A API pública contém somente status, evidence, result, erro esperado e `run_skill`; auxiliares permanecem privados.
- **AC-37**: Erros de execução são instâncias de erro esperado, com código e mensagem determinísticos.
- **AC-38**: HERMES-0003 permanece compatível e o loader continua passivo.
- **AC-39**: HERMES-0004 permanece compatível e discovery continua preso à raiz explícita.
- **AC-40**: HERMES-0005 permanece compatível e nenhum handler roda sem plano aprovado.
- **AC-41**: O contrato real do repositório é descoberto, entra no registry e produz SkillPlan sob a policy piloto, sem registry artificial.
- **AC-42**: `available_requires` nunca é derivado de `skill.requires`; policy sem `git` bloqueia o contrato real.
- **AC-43**: Mutação posterior do dict/list original de details não altera `SkillExecutionEvidence` já construída.
- **AC-44**: Conversão recursiva cobre mappings, sequências, sets e valores reais com ordem determinística e sem perda silenciosa.
- **AC-45**: Preflight negativo e falha estrutural anterior ao Report seguem resultados distintos e observáveis.
- **AC-46**: Cada classe de erro semântico possui o exit code numérico normativo sem apagar seu diagnóstico.
- **AC-47**: Somente os cinco comandos Git read-only auditados podem ser alcançados pelo handler, via boundary central.
- **AC-48**: Subprocess Git interno controlado é permitido, mas processo/executável/argumento arbitrário permanece impossível.
- **AC-49**: Sentinelas observáveis provam ausência de import dinâmico, plugin discovery, handler derivado e fallback.
- **AC-50**: O CLI aceita ID genérico válido, chama somente `run_skill` e deixa unsupported ocorrer depois do plano.
- **AC-51**: Dogfooding end-to-end no layout real atravessa discovery, registry, policy, plan, dispatch, handler, resultado e formatter.
- **AC-52**: Resultado semântico relevante do comando skill permanece compatível com preflight, doctor e worktree legados.

A compatibilidade dos AC-38 a AC-40 preserva a semântica interna e passiva de
loader, registry, discovery, policy e planning. Ela não preserva como proibição
permanente as ausências próprias das fases anteriores: esta especificação
supersede de forma limitada a vedação absoluta do símbolo público `run_skill` e
da CLI operacional `skill run`, exclusivamente para o piloto read-only fechado
aqui definido. Runner genérico, `execute_skill`, pipeline, plugins e execução
dinâmica ou arbitrária continuam proibidos.

## Plano de Testes

Todos os testes futuros ficam em `tests/test_skill_execution.py`, salvo as
verificações mínimas de CLI em `tests/test_cli.py`. Cada teste deve conter o
marcador `Spec: HERMES-0006 / AC-NN`.

| AC | Tipo | Arquivo | Função futura | Prova |
|----|------|---------|---------------|-------|
| AC-01 | Unitário | tests/test_skill_execution.py | test_run_skill_requires_explicit_inputs | Entradas obrigatórias e estritas |
| AC-02 | Unitário | tests/test_skill_execution.py | test_discovery_precedes_planning_dispatch_and_handler | Ordem global |
| AC-03 | Integração | tests/test_skill_execution.py | test_real_registry_and_plan_are_mandatory | Registry e plan reais |
| AC-04 | Segurança | tests/test_skill_execution.py | test_discovery_failure_prevents_all_later_phases | Fail-closed |
| AC-05 | Segurança | tests/test_skill_execution.py | test_policy_failure_prevents_dispatch_and_handler | Gate efetivo |
| AC-06 | Unitário | tests/test_skill_execution.py | test_dispatch_rejects_non_unit_request | Piloto unitário |
| AC-07 | Unitário | tests/test_skill_execution.py | test_dispatch_supports_only_git_preflight | Dispatch literal |
| AC-08 | Segurança | tests/test_skill_execution.py | test_unsupported_skill_is_blocked_without_fallback | Erro estável |
| AC-09 | Segurança | tests/test_skill_execution.py | test_dispatch_never_derives_or_discovers_handler | Sem resolução dinâmica |
| AC-10 | Segurança | tests/test_skill_execution.py | test_dangerous_skill_body_remains_inert | Payload textual não executado |
| AC-11 | Unitário | tests/test_skill_execution.py | test_git_preflight_reuses_existing_orchestration | Sem duplicação |
| AC-12 | Integração | tests/test_skill_execution.py | test_git_preflight_reports_existing_checks | Cobertura operacional |
| AC-13 | Unitário | tests/test_skill_execution.py | test_execution_models_are_frozen_slotted_and_deeply_immutable | Modelos imutáveis |
| AC-14 | Unitário | tests/test_skill_execution.py | test_execution_result_has_minimal_ordered_snapshot | Superfície mínima |
| AC-15 | Unitário | tests/test_skill_execution.py | test_execution_status_distinguishes_findings_from_no_report | Estados fechados |
| AC-16 | Segurança | tests/test_skill_execution.py | test_result_excludes_body_environment_and_secrets | Evidência mínima |
| AC-17 | Segurança | tests/test_skill_execution.py | test_execution_does_not_write_files | Sem escrita |
| AC-18 | Segurança | tests/test_skill_execution.py | test_execution_uses_no_mutating_git_operation | Git read-only |
| AC-19 | Segurança | tests/test_skill_execution.py | test_processes_use_central_process_boundary | Boundary obrigatório |
| AC-20 | Segurança | tests/test_skill_execution.py | test_user_cannot_supply_process_or_shell | Sem processo arbitrário |
| AC-21 | Segurança | tests/test_skill_execution.py | test_execution_does_not_access_network | Sem rede |
| AC-22 | Integração | tests/test_skill_execution.py | test_strong_repository_snapshot_is_preserved | Porcelain, HEAD, refs e bytes preservados |
| AC-23 | Unitário | tests/test_skill_execution.py | test_execution_error_exposes_no_partial_result | Atomicidade |
| AC-24 | Unitário | tests/test_skill_execution.py | test_execution_does_not_mutate_inputs | Imutabilidade |
| AC-25 | Unitário | tests/test_skill_execution.py | test_execution_is_deterministic | Determinismo |
| AC-26 | Integração | tests/test_skill_execution.py | test_negative_preflight_returns_complete_result_and_exit_code | Finding não é crash |
| AC-27 | CLI | tests/test_cli.py | test_skill_run_git_preflight_cli | Integração CLI |
| AC-28 | CLI/Segurança | tests/test_cli.py | test_skill_run_rejects_operational_flags | Flags proibidas |
| AC-29 | CLI/Segurança | tests/test_cli.py | test_skill_run_output_is_sanitized | Saída pública |
| AC-30 | Regressão | tests/test_skill_execution.py | test_existing_commands_remain_compatible | Comandos existentes |
| AC-31 | Integração | tests/test_skill_execution.py | test_execution_uses_controlled_temporary_repository | Fixture real |
| AC-32 | Segurança | tests/test_skill_execution.py | test_unsafe_local_git_config_remains_blocked | Config segura |
| AC-33 | Regressão | tests/test_skill_execution.py | test_required_and_optional_git_semantics_are_preserved | Política Git |
| AC-34 | CLI/Segurança | tests/test_cli.py | test_cli_uses_explicit_least_privilege_policy | Policy piloto |
| AC-35 | Segurança | tests/test_skill_execution.py | test_public_surface_has_no_generic_runner_pipeline_or_plugins | Escopo fechado |
| AC-36 | API | tests/test_skill_execution.py | test_execution_public_api_exports_only_return_contract_and_entrypoint | Exports mínimos |
| AC-37 | Unitário | tests/test_skill_execution.py | test_execution_errors_are_stable_and_deterministic | Erros |
| AC-38 | Regressão | tests/test_skill_execution.py | test_skill_execution_preserves_passive_loader_contract | HERMES-0003 |
| AC-39 | Regressão | tests/test_skill_execution.py | test_skill_execution_preserves_explicit_discovery_contract | HERMES-0004 |
| AC-40 | Regressão | tests/test_skill_execution.py | test_skill_execution_requires_approved_plan | HERMES-0005 |
| AC-41 | Integração | tests/test_skill_execution.py | test_real_repository_contract_discovers_and_plans | Contrato real até SkillPlan |
| AC-42 | Segurança | tests/test_skill_execution.py | test_requirements_never_auto_authorize_policy | Sem autoautorização |
| AC-43 | Unitário | tests/test_skill_execution.py | test_source_details_mutation_cannot_change_evidence | Imutabilidade profunda observável |
| AC-44 | Unitário | tests/test_skill_execution.py | test_freeze_details_is_recursive_lossless_and_deterministic | Conversão completa |
| AC-45 | Unitário | tests/test_skill_execution.py | test_negative_report_differs_from_structural_execution_failure | Resultado versus erro |
| AC-46 | CLI | tests/test_cli.py | test_skill_run_semantic_errors_map_to_normative_exit_codes | Mapa completo |
| AC-47 | Segurança | tests/test_skill_execution.py | test_handler_reaches_only_audited_read_only_git_commands | Allowlist concreta |
| AC-48 | Segurança | tests/test_skill_execution.py | test_controlled_git_process_allowed_arbitrary_process_blocked | Boundary de processos |
| AC-49 | Segurança | tests/test_skill_execution.py | test_dispatch_never_calls_dynamic_import_plugin_or_fallback | Sentinelas observáveis |
| AC-50 | CLI/Segurança | tests/test_cli.py | test_generic_valid_id_reaches_closed_dispatch_through_run_skill | ID genérico, dispatch fechado |
| AC-51 | End-to-end | tests/test_cli.py | test_real_repository_dogfooding_exercises_full_skill_pipeline | Pipeline real completo |
| AC-52 | Regressão | tests/test_skill_execution.py | test_skill_preflight_semantics_match_legacy_commands | Compatibilidade semântica |

Testes de segurança devem incluir comportamento permitido, comportamento
bloqueado e regressão. A prova do AC-22 registra antes e depois: saída bruta de
`status --porcelain=v1 -z --untracked-files=all`, HEAD, refs criadas pelo
fixture e mapa caminho->bytes de todos os arquivos controlados. Ela não compara
mtime, atime ou metadados irrelevantes. Repositórios Git são criados somente em
diretórios temporários e usam o helper seguro existente.

O AC-10 usa contrato válido cujo body contém comando shell textual, nome de
arquivo marcador, `git reset --hard` e código Python textual; monkeypatches e o
snapshot provam que nada foi interpretado. AC-49 instala sentinelas nas
fronteiras de import dinâmico/plugin discovery e prova ausência de chamadas,
em vez de depender de grep do source. AC-41 usa o contrato e discovery públicos
do repositório real, nunca `load_skill` isolado ou registry artificial.

## Arquivos Provavelmente Afetados

| Caminho | Papel futuro |
|---------|--------------|
| `src/hermes_ops/skills/execution_models.py` | Modelo imutável e status de execução |
| `src/hermes_ops/skills/executor.py` | Orquestração, dispatcher literal e adapter de preflight |
| `src/hermes_ops/skills/__init__.py` | Exportar apenas resultado e entry point público |
| `src/hermes_ops/core/errors.py` | Erro esperado de execução |
| `src/hermes_ops/cli.py` | Subcomandos fechados `skill run` |
| `src/hermes_ops/commands/skill.py` | Boundary CLI e policy piloto explícita |
| `tests/test_skill_execution.py` | Matriz dedicada do piloto |
| `tests/test_cli.py` | Parsing, flags proibidas e apresentação |
| `tests/test_skills.py` | Regressão HERMES-0003, se necessário |
| `tests/test_skill_registry.py` | Regressão HERMES-0004, se necessário |
| `tests/test_skill_policy.py` | Regressão HERMES-0005, se necessário |

`preflight.py`, `worktree.py`, `git/inspector.py`, `git/environment.py`
e `git/parser.py` devem ser reutilizados sem alteração se os testes
confirmarem que o adapter é suficiente. Refatoração mínima futura só é
permitida quando necessária para separar domínio de apresentação sem mudar os
comandos existentes.

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| 2026-08-10 | Piloto executa exclusivamente `git-preflight` | É a única skill operacional concreta existente | Runner genérico |
| 2026-08-10 | Fluxo obrigatório discovery -> plan -> dispatch -> handler | Reutiliza fronteiras aprovadas e impede bypass de policy | Chamar handler diretamente |
| 2026-08-10 | Dispatcher privado e literal | Menor superfície e nenhuma resolução dinâmica | Registry extensível de handlers |
| 2026-08-10 | Handler adapta `run_preflight` | Preserva lógica e testes read-only existentes | Duplicar GitInspector/classificação |
| 2026-08-10 | Resultado próprio mínimo envolvendo evidências existentes | Marca boundary de execução sem criar segunda taxonomia de checks | Retornar Report sem skill_id |
| 2026-08-10 | Execução unitária | Evita ordem, atomicidade e chaining ainda não especificados | Aceitar SkillPlan multi-skill |
| 2026-08-10 | CLI usa policy piloto explícita e conservadora | Permite dogfooding sem configuração nova e bloqueia aumento de risco/escrita | Policy permissiva ou implícita no planner |
| 2026-08-10 | Dois códigos novos de fronteira | Diagnóstico suficiente sem duplicar erros internos | Um código por falha de preflight |

## Alternativas Descartadas

1. Interpretar o procedimento Markdown: transforma documentação em código e
   permite injeção.
2. Importar módulo com base no ID: cria plugin discovery implícito.
3. Registrar handlers por entry point: amplia superfície antes de existir
   governança de plugins.
4. Chamar `GitInspector` diretamente no handler: duplicaria configuração,
   root markers, doctor e semântica required/optional de preflight.
5. Retornar apenas booleano: perderia evidências e exit code.
6. Executar um `SkillPlan` arbitrário: introduziria pipeline e atomicidade
   operacional fora do piloto.
7. Remover comandos antigos: impediria comparação de dogfooding.
8. Adicionar capabilities genéricas primeiro: não é necessário para o piloto
   read-only fechado.
9. Permitir argumentos operacionais no CLI: converteria o piloto em executor
   arbitrário.

## Riscos Restantes

- **Confusão entre contrato e código:** mitigada pelo dispatcher literal; o
  Markdown nunca escolhe comportamento.
- **Policy piloto do CLI e disponibilidade de Git:** o token `git` autoriza
  planejamento declarativo, enquanto disponibilidade real só é conhecida pelo
  handler. A distinção deve ser documentada na ajuda.
- **Acoplamento ao `Report`:** o adapter depende do modelo atual. Se isso
  impedir resultado mínimo ou testes isolados, será necessária extração pequena
  e compatível, nunca duplicação.
- **Dupla execução de validações:** `run_preflight` chama doctor e depois
  resolve configuração novamente. O piloto prioriza reutilização; otimização
  exige medição e spec própria se mudar comportamento.
- **Paths em evidências:** `CheckResult.details` pode conter paths. A API
  interna pode preservá-los, mas toda apresentação pública precisa sanitizar.
- **Escopo do ID suportado:** uma skill futura pode ser planejável, mas não
  executável. O erro fechado precisa permanecer explícito.
- **Mudança futura de preflight:** o handler herdará mudanças do comando. Testes
  comparativos devem detectar divergência.
- **Processos Git ainda existem:** são subprocessos controlados e necessários,
  não subprocess arbitrário. A segurança depende de manter argumentos fixos,
  ambiente neutralizado, cwd explícito e timeout.
- **Exit codes:** `Report.exit_code` possui precedência própria; o piloto não
  deve reinterpretá-la.
- **Expansão acidental:** adicionar segundo handler exige nova especificação,
  análise de capabilities e testes próprios.

## Evidências da Implementação

A implementação foi concluída na branch `feature/skills-contract` após a
reconciliação contratual controlada. O commit documental desta transição é
posterior e não se confunde com os commits abaixo.

| Campo | Valor |
|-------|-------|
| Commit da reconciliação contratual | `37e54fd9d1503a27c6f54e1982ab7a67e9d50d32` — `docs(skills): reconcilia contratos e testes com execucao piloto` |
| Commit da implementação | `ecc6c4cdd3613f64ad35be8b39e3bef63f7926c6` — `feat(skills): implementa execucao piloto do git-preflight` |
| Commit do fechamento documental | `947460ad658e76b2ca8eacdb9521cd9dc4c12160` — `docs(specs): marca HERMES-0006 como implementada` |
| Estado da integração | Concluído na branch `feature/skills-contract`; ainda não integrado |
| Arquivos alterados | `src/hermes_ops/cli.py`, `src/hermes_ops/core/errors.py`, `src/hermes_ops/skills/__init__.py`, `src/hermes_ops/commands/skill.py`, `src/hermes_ops/skills/execution_models.py`, `src/hermes_ops/skills/executor.py`, `tests/test_cli.py`, `tests/test_skill_execution.py` |
| Testes direcionados | Domínio: 45 passed; CLI HERMES-0006: 12 passed, 10 deselected; regressão skills: 245 passed, 6 skipped; commands legados: 35 passed; 0 falhas e 0 erros |
| Suíte completa | `.venv\Scripts\python.exe -m pytest` → 378 collected, 370 passed, 8 skipped, 0 failed, 0 errors |
| Validação de sintaxe ou compileall | `.venv\Scripts\python.exe -m compileall -q src` → PASS, exit code 0 |
| Empacotamento | Não aplicável — a distribuição e sua configuração não foram alteradas; os testes de packaging permaneceram verdes na suíte completa |
| git diff --check | PASS, sem avisos |
| Plataformas e versões validadas | Windows 10, Python 3.13.13 |
| CI | Não aplicável — implementação e validação concluídas localmente na branch, ainda sem integração |
| Limitações do ambiente | 8 skips ambientais conhecidos na suíte completa: symlinks indisponíveis no Windows e fixture portátil de permission denied indisponível; 0 warnings novos |
| Auditoria final | PASS, sem bloqueantes |

### Pipeline Real Comprovado

O dogfooding e os testes percorreram o fluxo real, sem registry ou plano
artificial:

```text
CLI
→ run_skill
→ discover_skills
→ SkillRegistry
→ SkillPolicy
→ plan_skills
→ SkillPlan
→ dispatch fechado
→ handler git-preflight
→ run_preflight
→ SkillExecutionResult
→ formatter
```

### Segurança Comprovada

- somente `git-preflight` possui handler literal;
- não existem dynamic import, plugins, entrypoints, fallback, `eval` ou `exec`;
- o body de `SKILL.md` permanece declarativo e inerte;
- não existem escrita, Git mutável, rede ou shell arbitrário;
- subprocessos permanecem limitados ao Git read-only existente via
  `GitInspector` e à abstração central de processos;
- a policy é externa e explícita; `available_requires` não deriva de
  `skill.requires`, e requirements não se autoautorizam;
- `SkillExecutionEvidence` e `SkillExecutionResult` preservam deep
  immutability e ordenação determinística;
- runner genérico, `execute_skill` e pipeline genérico continuam inexistentes.

### Dogfooding Pré-commit

Foi executado sem mock:

```text
.venv\Scripts\python.exe -m hermes_ops skill run git-preflight --project . --format text
```

O resultado foi `completed_with_findings`, exit code 3, porque
`clean_worktree_policy` bloqueou corretamente o working tree com alterações da
própria implementação ainda não commitadas. O HEAD permaneceu
`37e54fd9d1503a27c6f54e1982ab7a67e9d50d32`; working tree e refs permaneceram
idênticas, nenhum stage ou arquivo inesperado apareceu e nenhuma mutação foi
detectada.

### Dogfooding Pós-commit

Após o commit documental `947460ad658e76b2ca8eacdb9521cd9dc4c12160`, o
mesmo comando foi executado novamente sem mock e com working tree limpa:

```text
.venv\Scripts\python.exe -m hermes_ops skill run git-preflight --project . --format text
```

O resultado foi `passed`, exit code 0, com `git-preflight` encontrado e todas
as evidências concluídas sem bloqueio. O HEAD antes e depois permaneceu
`947460ad658e76b2ca8eacdb9521cd9dc4c12160`; working tree permaneceu limpa,
refs permaneceram idênticas, staging permaneceu vazio, nenhum arquivo
inesperado apareceu e nenhuma mutação foi detectada.

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| 2026-08-10 | Codex | Criação do rascunho para execução piloto read-only e fechada de `git-preflight` | Dogfooding da única skill operacional concreta existente |
| 2026-08-10 | Codex | Promoção para Aprovado após reauditoria final dos 52 critérios, sem bloqueantes | Discovery, planning, policy externa, imutabilidade profunda, exit codes e dogfooding especificados |
| 2026-08-10 | Codex | Registro explícito da supersessão limitada das antigas ausências phase-scoped de `run_skill` e CLI de skills | Loader, registry, policy e planning permanecem compatíveis; somente o piloto read-only fechado é acrescentado |
| 2026-08-10 | Codex | Promoção para Implementado, substituição das 52 justifications temporárias por vínculos reais e registro das evidências finais | Reconciliação `37e54fd9d1503a27c6f54e1982ab7a67e9d50d32`; implementação `ecc6c4cdd3613f64ad35be8b39e3bef63f7926c6` |
| 2026-08-10 | Codex | Registro do dogfooding pós-commit com working tree limpa, status `passed`, exit code 0 e ausência de mutação | Fechamento documental `947460ad658e76b2ca8eacdb9521cd9dc4c12160` |
