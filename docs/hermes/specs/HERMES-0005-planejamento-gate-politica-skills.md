+++
schema_version = 1
id = "HERMES-0005"
status = "Implementado"
[[acceptance_criteria]]
id = "AC-01"
test_file = "tests/test_skill_policy.py"
test_function = "test_skill_policy_is_immutable_and_strict"
[[acceptance_criteria]]
id = "AC-02"
test_file = "tests/test_skill_policy.py"
test_function = "test_skill_plan_is_immutable"
[[acceptance_criteria]]
id = "AC-03"
test_file = "tests/test_skill_policy.py"
test_function = "test_empty_request_is_rejected"
[[acceptance_criteria]]
id = "AC-04"
test_file = "tests/test_skill_policy.py"
test_function = "test_single_active_skill_is_planned"
[[acceptance_criteria]]
id = "AC-05"
test_file = "tests/test_skill_policy.py"
test_function = "test_multiple_eligible_skills_form_complete_plan"
[[acceptance_criteria]]
id = "AC-06"
test_file = "tests/test_skill_policy.py"
test_function = "test_plan_preserves_requested_order"
[[acceptance_criteria]]
id = "AC-07"
test_file = "tests/test_skill_policy.py"
test_function = "test_unknown_skill_id_is_rejected"
[[acceptance_criteria]]
id = "AC-08"
test_file = "tests/test_skill_policy.py"
test_function = "test_duplicate_requested_id_is_rejected"
[[acceptance_criteria]]
id = "AC-09"
test_file = "tests/test_skill_policy.py"
test_function = "test_draft_skill_is_rejected"
[[acceptance_criteria]]
id = "AC-10"
test_file = "tests/test_skill_policy.py"
test_function = "test_deprecated_skill_is_rejected"
[[acceptance_criteria]]
id = "AC-11"
test_file = "tests/test_skill_policy.py"
test_function = "test_low_risk_allowed_by_low_policy"
[[acceptance_criteria]]
id = "AC-12"
test_file = "tests/test_skill_policy.py"
test_function = "test_medium_risk_blocked_by_low_policy"
[[acceptance_criteria]]
id = "AC-13"
test_file = "tests/test_skill_policy.py"
test_function = "test_medium_risk_allowed_by_medium_policy"
[[acceptance_criteria]]
id = "AC-14"
test_file = "tests/test_skill_policy.py"
test_function = "test_high_risk_blocked_by_medium_policy"
[[acceptance_criteria]]
id = "AC-15"
test_file = "tests/test_skill_policy.py"
test_function = "test_high_risk_allowed_by_high_policy"
[[acceptance_criteria]]
id = "AC-16"
test_file = "tests/test_skill_policy.py"
test_function = "test_read_only_declaration_allowed_when_policy_disallows_write"
[[acceptance_criteria]]
id = "AC-17"
test_file = "tests/test_skill_policy.py"
test_function = "test_write_declaration_blocked_when_policy_disallows_write"
[[acceptance_criteria]]
id = "AC-18"
test_file = "tests/test_skill_policy.py"
test_function = "test_write_declaration_can_be_planned_without_writing"
[[acceptance_criteria]]
id = "AC-19"
test_file = "tests/test_skill_policy.py"
test_function = "test_empty_requires_is_allowed"
[[acceptance_criteria]]
id = "AC-20"
test_file = "tests/test_skill_policy.py"
test_function = "test_all_requirements_available"
[[acceptance_criteria]]
id = "AC-21"
test_file = "tests/test_skill_policy.py"
test_function = "test_unavailable_requirement_is_rejected"
[[acceptance_criteria]]
id = "AC-22"
test_file = "tests/test_skill_policy.py"
test_function = "test_first_missing_requirement_follows_declared_order"
[[acceptance_criteria]]
id = "AC-23"
test_file = "tests/test_skill_policy.py"
test_function = "test_policy_failure_is_atomic"
[[acceptance_criteria]]
id = "AC-24"
test_file = "tests/test_skill_policy.py"
test_function = "test_error_exposes_no_partial_plan"
[[acceptance_criteria]]
id = "AC-25"
test_file = "tests/test_skill_policy.py"
test_function = "test_planning_never_executes_skill_content"
[[acceptance_criteria]]
id = "AC-26"
test_file = "tests/test_skill_policy.py"
test_function = "test_planning_does_not_write_files"
[[acceptance_criteria]]
id = "AC-27"
test_file = "tests/test_skill_policy.py"
test_function = "test_planning_does_not_modify_git"
[[acceptance_criteria]]
id = "AC-28"
test_file = "tests/test_skill_policy.py"
test_function = "test_policy_layer_does_not_create_processes"
[[acceptance_criteria]]
id = "AC-29"
test_file = "tests/test_skill_policy.py"
test_function = "test_requirements_are_not_imported_or_executed"
[[acceptance_criteria]]
id = "AC-30"
test_file = "tests/test_skill_policy.py"
test_function = "test_plan_skills_does_not_use_discovery_filesystem_or_loader"
[[acceptance_criteria]]
id = "AC-31"
test_file = "tests/test_skill_policy.py"
test_function = "test_planning_integrates_with_real_skill_registry"
[[acceptance_criteria]]
id = "AC-32"
test_file = "tests/test_skill_policy.py"
test_function = "test_public_api_has_no_generic_runner_execute_skill_or_pipeline"
[[acceptance_criteria]]
id = "AC-33"
test_file = "tests/test_skill_policy.py"
test_function = "test_invalid_skill_policy_values_are_rejected"
[[acceptance_criteria]]
id = "AC-34"
test_file = "tests/test_skill_policy.py"
test_function = "test_invalid_registry_is_rejected"
[[acceptance_criteria]]
id = "AC-35"
test_file = "tests/test_skill_policy.py"
test_function = "test_invalid_requested_ids_structure_is_rejected"
[[acceptance_criteria]]
id = "AC-36"
test_file = "tests/test_skill_policy.py"
test_function = "test_requested_id_must_match_contract_grammar"
[[acceptance_criteria]]
id = "AC-37"
test_file = "tests/test_skill_policy.py"
test_function = "test_direct_plan_rejects_invalid_container_empty_and_policy"
[[acceptance_criteria]]
id = "AC-38"
test_file = "tests/test_skill_policy.py"
test_function = "test_direct_plan_rejects_non_skill_definition"
[[acceptance_criteria]]
id = "AC-39"
test_file = "tests/test_skill_policy.py"
test_function = "test_direct_plan_rejects_duplicate_ids_and_preserves_valid_order"
[[acceptance_criteria]]
id = "AC-40"
test_file = "tests/test_skill_policy.py"
test_function = "test_missing_id_precedes_policy_failure"
[[acceptance_criteria]]
id = "AC-41"
test_file = "tests/test_skill_policy.py"
test_function = "test_intra_skill_error_precedence"
[[acceptance_criteria]]
id = "AC-42"
test_file = "tests/test_skill_policy.py"
test_function = "test_cross_phase_error_precedence"
[[acceptance_criteria]]
id = "AC-43"
test_file = "tests/test_skill_policy.py"
test_function = "test_planning_is_deterministic"
+++

# HERMES-0005 — Planejamento e Gate de Política de Skills

## Status

Implementado

## Resumo para o Responsável pelo Projeto

O Hermes já consegue carregar, validar e descobrir contratos de skills. Esta
especificação propõe a próxima camada: receber uma lista explícita de skills e
uma política explícita, verificar se todas são elegíveis e produzir um plano
imutável.

O plano é somente uma decisão de política. Ele não executa skills, não concede
permissões e não substitui os controles que um futuro runner precisará aplicar.

## Contexto

A HERMES-0003 implementou `SkillDefinition`, os enums `SkillStatus` e
`SkillRisk` e o carregamento passivo por `load_skill`. A HERMES-0004 implementou
`SkillRegistry`, `discover_skills(project_root)` e consulta exata por ID. Essas
camadas respondem, respectivamente, se um contrato individual é válido e quais
skills válidas existem na raiz explícita de um projeto.

Nenhuma delas responde se uma combinação solicitada de skills é elegível sob
uma política concreta. Em particular, encontrar uma skill no registry não é
autorizá-la, e os campos `risk`, `requires` e `allows_write` continuam sendo
declarações do contrato.

## Problema Confirmado

Sem uma fronteira única de planejamento, futuros consumidores poderiam tratar
`SkillRegistry.get_by_id()` como autorização, comparar riscos de formas
divergentes, ignorar requirements ausentes, deduplicar solicitações
silenciosamente ou produzir planos parciais.

Também existe o risco de interpretar `allows_write: true` como concessão de
escrita. Esse campo somente informa que a skill declara possível necessidade
de escrita; a autorização operacional continuará fora do contrato da skill e
fora desta fase.

## Comportamento Atual

- `load_skill(path)` lê e valida um `SKILL.md` explícito sem executá-lo.
- `discover_skills(project_root)` constrói um registry imutável e fail-closed.
- `SkillRegistry.get_by_id(skill_id)` retorna uma definição ou `None`.
- `requires` e `allows_write` são dados declarativos e inertes.
- Não existem `SkillPolicy`, `SkillPlan` ou `plan_skills`.
- Não existe runner, execução, pipeline ou CLI operacional de skills.

## Comportamento Desejado

A API pública mínima proposta mantém os nomes coerentes com os tipos e funções
já existentes:

```text
SkillPolicy
SkillPlan
plan_skills(registry, requested_ids, policy) -> SkillPlan
```

`SkillPolicy` é externa a `SkillDefinition` e obrigatória em toda chamada de
planejamento. Não há política implícita nem default permissivo.

Estrutura proposta:

```text
SkillPolicy:
    max_risk: SkillRisk
    allow_write: bool
    available_requires: frozenset[str]

SkillPlan:
    skills: tuple[SkillDefinition, ...]
    policy: SkillPolicy
```

Ambos seguem o padrão existente de `dataclass(frozen=True, slots=True)`.
`SkillPlan.skills` preserva a ordem da solicitação, não a ordem canônica do
registry. Manter a política imutável no plano registra sob qual gate a decisão
foi produzida, mas não transforma o plano em autorização operacional.

### Validação de `SkillPolicy`

O construtor público é defensivo:

- `max_risk` deve ser uma instância de `SkillRisk`; strings como `"low"` não
  sofrem coerção;
- `allow_write` deve ter tipo exato `bool`; inteiros não são aceitos;
- `available_requires` deve ter tipo exato `frozenset`;
- cada item deve ter tipo exato `str`, ser não vazio, não conter somente
  whitespace e já estar sem whitespace externo;
- nenhum item é normalizado, importado, executado ou procurado no sistema;
- duplicidade não pode ser fornecida na representação exigida. A API não aceita
  lista ou outra coleção que pudesse ser deduplicada silenciosamente.

Qualquer violação produz `SKILL_POLICY_INVALID`. `plan_skills` também rejeita
objetos que não sejam `SkillPolicy`, sem construir política implícita.

Exemplos normativos: `frozenset({"git"})` é válido;
`frozenset({"GIT"})` também é válido como token distinto; `frozenset({" Git "})`,
`frozenset({""})` e `frozenset({"   "})` são inválidos. Não se aplica `strip`
nem normalização de caixa.

### Ordem de Risco

A ordem normativa é:

```text
low < medium < high
```

Uma skill é elegível somente quando `skill.risk <= policy.max_risk`. A
comparação usa um mapeamento interno explícito entre membros de `SkillRisk` e
níveis, sem depender da ordem textual ou da declaração do enum.

### Status Elegível

Somente `SkillStatus.ACTIVE` é elegível. `DRAFT` e `DEPRECATED` produzem
`SKILL_POLICY_STATUS_NOT_ACTIVE`. A política não possui override de status.

### Declaração de Escrita

Uma skill com `allows_write == false` não depende de `policy.allow_write`. Uma
skill com `allows_write == true` somente entra no plano quando
`policy.allow_write == true`; caso contrário ocorre
`SKILL_POLICY_WRITE_NOT_ALLOWED`.

Essa aprovação vale apenas para construir o plano. Ela não concede escrita. Um
futuro executor continuará obrigado a possuir e verificar capacidades reais
separadas.

### Requirements Declarativos

Para cada skill deve valer:

```text
set(skill.requires) ⊆ policy.available_requires
```

A comparação é exata e não normaliza caixa, hífens ou espaços. Requirements
continuam sendo strings inertes: não há import, instalação, busca de executável
ou qualquer tentativa de satisfazê-los.

Se houver ausências, o erro `SKILL_POLICY_REQUIREMENT_UNAVAILABLE` informa
somente o primeiro requirement ausente na ordem declarada em
`SkillDefinition.requires`. Isso oferece informação mínima e determinística.

### Solicitação de IDs

`requested_ids` deve ser uma tupla de strings que obedeçam exatamente à mesma
gramática de ID da HERMES-0003:

```text
[a-z0-9](?:[a-z0-9-]*[a-z0-9])?
```

Cada ID começa e termina com letra minúscula ASCII ou número e contém somente
letras minúsculas ASCII, números e hífen. String vazia, whitespace, underscore,
barra, ponto, caixa alta, hífen inicial ou final e whitespace externo são
inválidos. A validação usa os caracteres recebidos: não aplica `strip`,
`lowercase`, normalização ou coerção. Exigir tupla evita consumir iteradores
com comportamento externo e torna a ordem da entrada explícita.

São exemplos inválidos: `""`, `"   "`, `" git-preflight"`,
`"git-preflight "`, `"Git-Preflight"`, `"git_preflight"`, `"git preflight"`,
`"-git"`, `"git-"`, `"../git"` e `"skills/git"`. Todos produzem
`SKILL_PLAN_REQUEST_INVALID`, nunca `SKILL_PLAN_SKILL_NOT_FOUND`.
`"missing-skill"`, por outro lado, é sintaticamente válido e produz
`SKILL_PLAN_SKILL_NOT_FOUND` quando estiver ausente do registry.

- tupla vazia produz `SKILL_PLAN_EMPTY_REQUEST`;
- tipo de coleção, item não string ou item fora da gramática produz
  `SKILL_PLAN_REQUEST_INVALID`;
- a primeira repetição na ordem solicitada produz
  `SKILL_PLAN_DUPLICATE_REQUEST`;
- somente um ID sintaticamente válido que não exista no registry produz
  `SKILL_PLAN_SKILL_NOT_FOUND`;
- nenhum ID é normalizado ou deduplicado;
- uma solicitação válida preserva exatamente sua ordem no plano.

Exemplo normativo:

```text
registry.skills: ("a", "b", "c")
requested_ids:   ("c", "a")
SkillPlan.skills:("c", "a")
```

O plano nunca é reordenado por ID.

### Construção Defensiva de `SkillPlan`

O construtor público de `SkillPlan` rejeita com `SKILL_PLAN_INVALID`: `skills`
que não seja tupla; tupla vazia; item que não seja `SkillDefinition`; IDs
duplicados; ou `policy` que não seja `SkillPolicy`. Ele preserva a ordem da
tupla recebida.

Depois da validação estrutural, o construtor chama a mesma regra conceitual
`evaluate_skill_policy` usada por `plan_skills`, na ordem da tupla. Não existe
uma segunda implementação semântica do gate. Violações de status, risco,
escrita ou requirements preservam seu código específico.

O construtor direto não possui registry nem `requested_ids`; portanto não
valida existência original dos IDs nem a origem ou intenção da ordem recebida.
Ele valida somente estrutura, unicidade e elegibilidade das definições.

`plan_skills` continua sendo a fronteira que resolve IDs pelo registry. Somente
depois de resolver e validar toda a solicitação ele chama o construtor de
`SkillPlan`.

## Fora do Escopo

- runner ou `run_skill`;
- execução de skills ou de conteúdo de `SKILL.md`;
- CLI operacional de skills;
- pipeline ou orquestração;
- implementação ou concessão de capabilities;
- subprocessos, shell ou processos reais;
- escrita real em filesystem ou Git;
- discovery de filesystem;
- chamadas a `load_skill` ou parsing de contratos;
- instalação, import ou resolução operacional de requirements;
- plugins ou carregamento dinâmico;
- acesso a rede;
- autorização humana ou prompts de confirmação;
- rollback, sandbox ou logs de execução;
- mudança em HERMES-0003 ou HERMES-0004.

## Entradas

- `registry`: uma instância de `SkillRegistry` já construída;
- `requested_ids`: uma tupla ordenada e não vazia de IDs exatos;
- `policy`: uma instância explícita e válida de `SkillPolicy`.

Não há entrada de caminho, arquivo, variável de ambiente ou configuração
implícita.

## Saídas

Em caso válido, `plan_skills` retorna um `SkillPlan` completo e imutável, com as
skills na ordem solicitada e a política usada na decisão.

Em qualquer falha, levanta `SkillPolicyError` com código estável e mensagem
controlada. Não retorna plano parcial nem anexa skills aprovadas ao erro.

## Invariantes e Regras de Segurança

1. Existência no registry não equivale a autorização.
2. `SkillPolicy` é externa a `SkillDefinition` e sempre obrigatória.
3. `SkillPlan` é decisão de política, não execução ou autorização suficiente.
4. Somente skills `active` são elegíveis.
5. A ordem de risco é explicitamente `low < medium < high`.
6. `allows_write` nunca concede escrita.
7. `requires` nunca importa, instala, executa ou procura dependências.
8. Planejamento recebe um registry pronto e não acessa filesystem.
9. Planejamento nunca chama `discover_skills` nem `load_skill`.
10. Nenhuma etapa executa shell, subprocesso, plugin ou acesso a rede.
11. Nenhuma etapa escreve arquivos, altera Git ou modifica ambiente.
12. Uma falha aborta todo o planejamento sem resultado parcial.
13. A ordem do plano é a ordem da solicitação.
14. A mesma entrada produz o mesmo plano ou o mesmo primeiro erro.
15. Policy, plano e coleções públicas são imutáveis.
16. Mensagens de erro não contêm caminhos locais.
17. Não existe fallback, coerção ou deduplicação silenciosa.
18. A implementação usa Python 3.11 e somente a biblioteca padrão.
19. HERMES-0003 e HERMES-0004 permanecem compatíveis e inalteradas.
20. `plan_skills` exige uma instância real de `SkillRegistry`; objetos
    duck-typed e coleções não são aceitos.
21. A gramática dos IDs solicitados é exatamente a da HERMES-0003.

## Pseudocódigo

O pseudocódigo descreve as decisões sem fixar detalhes de Python.

### `validate_policy(policy)`

```text
FUNÇÃO validate_policy(policy):
    VALIDAR que policy é SkillPolicy
    VALIDAR que max_risk é SkillRisk, sem coerção
    VALIDAR que allow_write é booleano estrito
    VALIDAR que available_requires é frozenset
    PARA cada item em ordem lexical apenas para validação determinística:
        VALIDAR que é string não vazia e sem espaços externos
    SE qualquer validação falhar:
        FALHAR com SKILL_POLICY_INVALID
    RETORNAR policy sem modificação
```

### `validate_requested_ids(requested_ids)`

```text
FUNÇÃO validate_requested_ids(requested_ids):
    SE requested_ids não for tupla:
        FALHAR com SKILL_PLAN_REQUEST_INVALID
    SE requested_ids estiver vazia:
        FALHAR com SKILL_PLAN_EMPTY_REQUEST

    PARA cada id na ordem recebida:
        SE id não for string:
            FALHAR com SKILL_PLAN_REQUEST_INVALID
        SE id não corresponder exatamente à gramática de ID da HERMES-0003:
            FALHAR com SKILL_PLAN_REQUEST_INVALID

    vistos = conjunto temporário
    PARA cada id na ordem recebida:
        SE id já estiver em vistos:
            FALHAR com SKILL_PLAN_DUPLICATE_REQUEST
        ADICIONAR id a vistos
    RETORNAR a mesma sequência ordenada
```

### `validate_requirements(skill, policy)`

```text
FUNÇÃO validate_requirements(skill, policy):
    PARA cada requirement na ordem declarada pela skill:
        SE requirement não estiver em policy.available_requires:
            FALHAR com SKILL_POLICY_REQUIREMENT_UNAVAILABLE
                informando somente o requirement ausente
    RETORNAR sucesso
```

### `evaluate_skill_policy(skill, policy)`

```text
FUNÇÃO evaluate_skill_policy(skill, policy):
    SE skill.status não for active:
        FALHAR com SKILL_POLICY_STATUS_NOT_ACTIVE
    MAPEAR low, medium e high para níveis explícitos 0, 1 e 2
    SE nível de skill.risk exceder nível de policy.max_risk:
        FALHAR com SKILL_POLICY_RISK_EXCEEDED
    SE skill.allows_write for verdadeiro E policy.allow_write for falso:
        FALHAR com SKILL_POLICY_WRITE_NOT_ALLOWED
    CHAMAR validate_requirements(skill, policy)
    RETORNAR sucesso sem executar a skill
```

### `build_skill_plan(skills, policy)`

```text
FUNÇÃO build_skill_plan(skills, policy):
    SE skills não for tupla OU estiver vazia:
        FALHAR com SKILL_PLAN_INVALID
    SE policy não for SkillPolicy:
        FALHAR com SKILL_PLAN_INVALID
    SE algum item não for SkillDefinition OU IDs se repetirem:
        FALHAR com SKILL_PLAN_INVALID
    PARA cada skill na ordem da tupla:
        CHAMAR a mesma evaluate_skill_policy(skill, policy)
    SOMENTE após sucesso total:
        CONSTRUIR SkillPlan imutável contendo skills e policy
    RETORNAR plano completo
```

### `plan_skills(registry, requested_ids, policy)`

```text
FUNÇÃO plan_skills(registry, requested_ids, policy):
    SE registry não for uma instância real de SkillRegistry:
        FALHAR com SKILL_PLAN_INVALID
    policy_validada = validate_policy(policy)
    ids_validados = validate_requested_ids(requested_ids)

    definições = coleção temporária não publicada
    PARA cada id em ids_validados, na ordem solicitada:
        definição = registry.get_by_id(id)
        SE definição não existir:
            FALHAR com SKILL_PLAN_SKILL_NOT_FOUND
        ADICIONAR definição à coleção temporária

    PARA cada definição temporária, na ordem solicitada:
        CHAMAR evaluate_skill_policy(definição, policy_validada)

    RETORNAR build_skill_plan(tuple(definições), policy_validada)
```

Nenhuma função acima executa uma skill ou acessa seu arquivo de origem.

A precedência acima é normativa. Todos os IDs são resolvidos antes de qualquer
gate por skill. Assim, para `("skill-a", "missing-skill")`, quando `skill-a`
excede o risco mas `missing-skill` é um ID válido ausente, o resultado é
`SKILL_PLAN_SKILL_NOT_FOUND`. Dentro de uma mesma skill, status vence risco,
risco vence escrita, escrita vence requirements e requirements ausentes vencem
na ordem declarada.

## Fluxo Principal

1. Validar que registry é uma instância real de `SkillRegistry`.
2. Validar tipos e invariantes da policy.
3. Validar que `requested_ids` é tupla e que seus itens são strings.
4. Rejeitar solicitação vazia.
5. Validar a sintaxe de cada ID pela gramática da HERMES-0003.
6. Detectar duplicidades na ordem solicitada.
7. Resolver todos os IDs pelo registry antes de avaliar policy por skill.
8. Para cada skill na ordem solicitada, verificar status, risco, escrita e
   requirements, exatamente nessa ordem.
9. Abortar integralmente na primeira falha determinística.
10. Construir o plano imutável somente após sucesso total.
11. Retornar o plano sem executar qualquer operação da skill.

## Casos de Erro e Limites

Uma única classe pública `SkillPolicyError`, derivada de `HermesOpsError` e com
atributo `code`, cobre a fronteira de policy e planejamento.

| Situação | Código | Semântica |
|----------|--------|-----------|
| Policy ou campo da policy inválido | `SKILL_POLICY_INVALID` | Falha antes de avaliar skills |
| Registry não é `SkillRegistry` real | `SKILL_PLAN_INVALID` | Sem coerção de tuple, list, dict, `None` ou objeto duck-typed |
| Construção direta de plano com estrutura inválida | `SKILL_PLAN_INVALID` | `skills` não tupla, tupla vazia, item inválido, ID repetido ou policy de tipo errado; mensagem distingue a causa |
| Solicitação não é tupla ou contém item não string | `SKILL_PLAN_REQUEST_INVALID` | Sem coerção |
| ID solicitado não segue exatamente a gramática da HERMES-0003 | `SKILL_PLAN_REQUEST_INVALID` | Sem strip, lowercase ou normalização |
| Solicitação vazia | `SKILL_PLAN_EMPTY_REQUEST` | Plano vazio não é produzido |
| Primeiro ID repetido | `SKILL_PLAN_DUPLICATE_REQUEST` | Sem deduplicação |
| Primeiro ID sintaticamente válido e inexistente | `SKILL_PLAN_SKILL_NOT_FOUND` | Consulta exata após validar todo o request |
| Status diferente de active | `SKILL_POLICY_STATUS_NOT_ACTIVE` | Sem override |
| Risco excede `max_risk` | `SKILL_POLICY_RISK_EXCEEDED` | Ordem explícita de risco |
| Declaração de escrita bloqueada | `SKILL_POLICY_WRITE_NOT_ALLOWED` | Não concede nem tenta escrita |
| Primeiro requirement ausente | `SKILL_POLICY_REQUIREMENT_UNAVAILABLE` | Ordem declarada, informação mínima |

Mensagens são estáveis e controladas, podem incluir somente ID ou requirement
necessário ao diagnóstico e nunca incluem caminhos locais. Erros não carregam
registry, plano ou coleção parcial.

Se vários problemas existirem, a precedência observável é exatamente: registry;
policy; tipo e estrutura de `requested_ids`; request vazio; sintaxe dos IDs;
duplicidade; resolução de todos os IDs; depois, para cada skill na ordem
solicitada, status, risco, escrita e requirements; por fim, construção do plano.

Exemplos normativos de precedência:

1. Se uma skill anterior excede o risco, mas um ID posterior válido não existe,
   vence `SKILL_PLAN_SKILL_NOT_FOUND`, pois todos os IDs são resolvidos antes do
   gate por skill.
2. Se uma skill é deprecated, high, declara escrita e possui requirement
   ausente, vence `SKILL_POLICY_STATUS_NOT_ACTIVE`.
3. Se uma skill active é high, declara escrita e possui requirement ausente sob
   policy medium sem escrita, vence `SKILL_POLICY_RISK_EXCEEDED`.
4. Se risco e status são permitidos, mas escrita e requirement são bloqueados,
   vence `SKILL_POLICY_WRITE_NOT_ALLOWED`.
5. Entre vários requirements ausentes, vence o primeiro na ordem declarada e o
   código é `SKILL_POLICY_REQUIREMENT_UNAVAILABLE`.

## Critérios de Aceitação

- **AC-01**: `SkillPolicy` é imutável, usa `frozen` e `slots`, exige
  `SkillRisk`, booleano estrito e `frozenset[str]` válido sem coerção.
- **AC-02**: `SkillPlan` é imutável, armazena skills em tupla e preserva a
  policy usada na decisão.
- **AC-03**: Solicitação vazia falha com `SKILL_PLAN_EMPTY_REQUEST`.
- **AC-04**: Uma única skill active que satisfaz a policy produz plano válido.
- **AC-05**: Múltiplas skills elegíveis produzem um único plano completo.
- **AC-06**: `SkillPlan.skills` preserva exatamente a ordem solicitada.
- **AC-07**: ID desconhecido falha com `SKILL_PLAN_SKILL_NOT_FOUND`.
- **AC-08**: ID duplicado falha com `SKILL_PLAN_DUPLICATE_REQUEST`, sem
  deduplicação silenciosa.
- **AC-09**: Skill draft falha com `SKILL_POLICY_STATUS_NOT_ACTIVE`.
- **AC-10**: Skill deprecated falha com `SKILL_POLICY_STATUS_NOT_ACTIVE`.
- **AC-11**: Risco low é permitido sob `max_risk=low`.
- **AC-12**: Risco medium é bloqueado sob `max_risk=low` com
  `SKILL_POLICY_RISK_EXCEEDED`.
- **AC-13**: Risco medium é permitido sob `max_risk=medium`.
- **AC-14**: Risco high é bloqueado sob `max_risk=medium` com
  `SKILL_POLICY_RISK_EXCEEDED`.
- **AC-15**: Risco high é permitido sob `max_risk=high`.
- **AC-16**: Skill com `allows_write=false` pode ser planejada com
  `policy.allow_write=false`, observadas as demais regras.
- **AC-17**: Skill com `allows_write=true` é bloqueada por policy false com
  `SKILL_POLICY_WRITE_NOT_ALLOWED`.
- **AC-18**: Skill com `allows_write=true` pode entrar no plano sob policy true,
  sem que isso conceda ou realize escrita.
- **AC-19**: Skill sem requirements pode ser planejada com conjunto disponível
  vazio.
- **AC-20**: Skill cujos requirements estão todos disponíveis é aceita por
  comparação exata.
- **AC-21**: Requirement ausente falha com
  `SKILL_POLICY_REQUIREMENT_UNAVAILABLE`.
- **AC-22**: Com múltiplos requirements ausentes, o erro informa somente o
  primeiro na ordem declarada.
- **AC-23**: Falha em qualquer skill aborta atomicamente toda a solicitação.
- **AC-24**: Erros não retornam nem expõem `SkillPlan` ou coleção parcial.
- **AC-25**: Planejamento nunca executa conteúdo ou comportamento de skill.
- **AC-26**: Planejamento não escreve arquivos nem concede escrita.
- **AC-27**: Planejamento não modifica Git.
- **AC-28**: Implementação não usa shell, subprocesso ou criação de processo.
- **AC-29**: Requirements não são importados, executados, instalados ou
  resolvidos operacionalmente.
- **AC-30**: `plan_skills` não acessa filesystem, não faz discovery e não chama
  `load_skill`.
- **AC-31**: Integração usa `SkillRegistry` real e consulta por `get_by_id`.
- **AC-32**: A camada de policy/planning não executa skills e `plan_skills`
  permanece puramente declarativo. A HERMES-0006 supersede somente a proibição
  phase-scoped de uma API `run_skill` e da CLI piloto `skill run`; permanecem
  proibidos runner genérico, `execute_skill`, pipeline e execução dinâmica, e
  nenhum `SkillPlan` executa por si próprio.
- **AC-33**: `SkillPolicy` rejeita tipos ou valores inválidos, incluindo
  coleções diferentes de `frozenset`, itens vazios, whitespace-only ou com
  whitespace externo, com `SKILL_POLICY_INVALID` e sem normalização.
- **AC-34**: Registry que não seja instância real de `SkillRegistry` é rejeitado
  por `plan_skills` com `SKILL_PLAN_INVALID`, sem coerção ou duck typing.
- **AC-35**: `requested_ids` que não seja tupla ou contenha item não string é
  rejeitado com `SKILL_PLAN_REQUEST_INVALID`.
- **AC-36**: Cada ID solicitado deve seguir exatamente a gramática da
  HERMES-0003; vazio, whitespace-only, whitespace externo, caixa alta,
  underscore, espaço, barra, ponto ou hífen inicial/final produzem
  `SKILL_PLAN_REQUEST_INVALID`, nunca `SKILL_PLAN_SKILL_NOT_FOUND`.
- **AC-37**: Construção direta rejeita com `SKILL_PLAN_INVALID` skills que não
  sejam tupla, tupla vazia ou policy que não seja `SkillPolicy`.
- **AC-38**: Construção direta rejeita com `SKILL_PLAN_INVALID` qualquer item
  que não seja `SkillDefinition`.
- **AC-39**: Construção direta rejeita com `SKILL_PLAN_INVALID` IDs duplicados e
  preserva a ordem da tupla quando válida.
- **AC-40**: Um ID válido inexistente vence falha de policy de skill anterior,
  pois todos os IDs são resolvidos antes da avaliação das skills.
- **AC-41**: Na mesma skill, a precedência observável é status sobre risco,
  escrita e requirements; risco sobre escrita e requirements; escrita sobre
  requirements. Cada combinação produz o código vencedor normativo.
- **AC-42**: Entre fases, registry inválido vence policy inválida; policy
  inválida vence request inválido; e sintaxe inválida em qualquer ID vence
  duplicidade, conforme a ordem normativa completa.
- **AC-43**: Mesmos registry, IDs e policy produzem deterministicamente o mesmo
  plano ou o mesmo primeiro erro.

## Plano de Testes

Os testes futuros ficarão em `tests/test_skill_policy.py`. Usarão
`SkillDefinition`, `SkillPolicy`, `SkillPlan` e `SkillRegistry` artificiais e
imutáveis, evitando filesystem salvo se uma integração futura realmente o
exigir. Pelo menos um teste usa o `SkillRegistry` público real.

| Critério | Tipo | Arquivo | Teste planejado | Evidência |
|----------|------|---------|------------------|-----------|
| AC-01 | Unitário | `tests/test_skill_policy.py` | `test_skill_policy_is_immutable_and_strict` | Policy e frozenset rejeitam mutação e coerção |
| AC-02 | Unitário | `tests/test_skill_policy.py` | `test_skill_plan_is_immutable` | Plano e tupla rejeitam mutação |
| AC-03 | Unitário | `tests/test_skill_policy.py` | `test_empty_request_is_rejected` | Solicitação vazia tem código estável |
| AC-04 | Unitário | `tests/test_skill_policy.py` | `test_single_active_skill_is_planned` | Fluxo mínimo permitido |
| AC-05 | Unitário | `tests/test_skill_policy.py` | `test_multiple_eligible_skills_form_complete_plan` | Plano contém todas as solicitadas |
| AC-06 | Unitário | `tests/test_skill_policy.py` | `test_plan_preserves_requested_order` | Ordem do request difere do registry |
| AC-07 | Unitário | `tests/test_skill_policy.py` | `test_unknown_skill_id_is_rejected` | Lookup ausente falha |
| AC-08 | Unitário | `tests/test_skill_policy.py` | `test_duplicate_requested_id_is_rejected` | Sem deduplicação |
| AC-09 | Unitário | `tests/test_skill_policy.py` | `test_draft_skill_is_rejected` | Draft não elegível |
| AC-10 | Unitário | `tests/test_skill_policy.py` | `test_deprecated_skill_is_rejected` | Deprecated não elegível |
| AC-11 | Unitário | `tests/test_skill_policy.py` | `test_low_risk_allowed_by_low_policy` | Limite inclusivo low |
| AC-12 | Unitário | `tests/test_skill_policy.py` | `test_medium_risk_blocked_by_low_policy` | Excesso medium/low |
| AC-13 | Unitário | `tests/test_skill_policy.py` | `test_medium_risk_allowed_by_medium_policy` | Limite inclusivo medium |
| AC-14 | Unitário | `tests/test_skill_policy.py` | `test_high_risk_blocked_by_medium_policy` | Excesso high/medium |
| AC-15 | Unitário | `tests/test_skill_policy.py` | `test_high_risk_allowed_by_high_policy` | Limite inclusivo high |
| AC-16 | Unitário | `tests/test_skill_policy.py` | `test_read_only_declaration_allowed_when_policy_disallows_write` | False não exige capacidade |
| AC-17 | Segurança | `tests/test_skill_policy.py` | `test_write_declaration_blocked_when_policy_disallows_write` | Bloqueio declarativo |
| AC-18 | Segurança | `tests/test_skill_policy.py` | `test_write_declaration_can_be_planned_without_writing` | Policy permite plano, não escrita |
| AC-19 | Unitário | `tests/test_skill_policy.py` | `test_empty_requires_is_allowed` | Vazio é subconjunto |
| AC-20 | Unitário | `tests/test_skill_policy.py` | `test_all_requirements_available` | Subconjunto completo |
| AC-21 | Unitário | `tests/test_skill_policy.py` | `test_unavailable_requirement_is_rejected` | Requirement ausente |
| AC-22 | Unitário | `tests/test_skill_policy.py` | `test_first_missing_requirement_follows_declared_order` | Erro mínimo determinístico |
| AC-23 | Segurança | `tests/test_skill_policy.py` | `test_policy_failure_is_atomic` | Skill anterior não vira plano parcial |
| AC-24 | Segurança | `tests/test_skill_policy.py` | `test_error_exposes_no_partial_plan` | Erro sem plano ou skills parciais |
| AC-25 | Segurança | `tests/test_skill_policy.py` | `test_planning_never_executes_skill_content` | Skill sentinela falha se comportamento for invocado; marcador permanece ausente |
| AC-26 | Segurança | `tests/test_skill_policy.py` | `test_planning_does_not_write_files` | Snapshot em `tmp_path` permanece igual e fronteiras de escrita falham se chamadas |
| AC-27 | Segurança | `tests/test_skill_policy.py` | `test_planning_does_not_modify_git` | Snapshot Git permanece igual e helper Git falha se chamado |
| AC-28 | Segurança observável | `tests/test_skill_policy.py` | `test_policy_layer_does_not_create_processes` | `subprocess.run` e `Popen` falham se chamados; planejamento válido termina sem chamada |
| AC-29 | Segurança | `tests/test_skill_policy.py` | `test_requirements_are_not_imported_or_executed` | Requirement sentinela não aparece em módulos e imports perigosos falham se chamados |
| AC-30 | Segurança observável | `tests/test_skill_policy.py` | `test_plan_skills_does_not_use_discovery_filesystem_or_loader` | `discover_skills`, `load_skill` e fronteiras de filesystem falham se chamados |
| AC-31 | Integração | `tests/test_skill_policy.py` | `test_planning_integrates_with_real_skill_registry` | Registry público real |
| AC-32 | API pública | `tests/test_skill_policy.py` | `test_public_api_has_no_generic_runner_execute_skill_or_pipeline` | Planning permanece inerte apesar da fronteira piloto posterior; sem runner genérico, `execute_skill` ou pipeline |
| AC-33 | Unitário parametrizado | `tests/test_skill_policy.py` | `test_invalid_skill_policy_values_are_rejected` | Tipos, coleções, vazio, whitespace-only e whitespace externo falham sem conversão |
| AC-34 | Unitário parametrizado | `tests/test_skill_policy.py` | `test_invalid_registry_is_rejected` | Tuple, list, dict, `None` e objeto duck-typed produzem `SKILL_PLAN_INVALID` |
| AC-35 | Unitário parametrizado | `tests/test_skill_policy.py` | `test_invalid_requested_ids_structure_is_rejected` | Coleção não tuple e item não string produzem `SKILL_PLAN_REQUEST_INVALID` |
| AC-36 | Unitário parametrizado | `tests/test_skill_policy.py` | `test_requested_id_must_match_contract_grammar` | Todos os exemplos lexicais inválidos falham antes do lookup |
| AC-37 | Unitário parametrizado | `tests/test_skill_policy.py` | `test_direct_plan_rejects_invalid_container_empty_and_policy` | Não tuple, vazio e policy de tipo errado produzem `SKILL_PLAN_INVALID` |
| AC-38 | Unitário | `tests/test_skill_policy.py` | `test_direct_plan_rejects_non_skill_definition` | Item inválido produz `SKILL_PLAN_INVALID` |
| AC-39 | Unitário | `tests/test_skill_policy.py` | `test_direct_plan_rejects_duplicate_ids_and_preserves_valid_order` | Duplicidade falha e tupla válida mantém ordem |
| AC-40 | Precedência | `tests/test_skill_policy.py` | `test_missing_id_precedes_policy_failure` | Lookup completo vence risco bloqueado em skill anterior |
| AC-41 | Precedência parametrizada | `tests/test_skill_policy.py` | `test_intra_skill_error_precedence` | Status vence demais; risco vence write/requires; write vence requires |
| AC-42 | Precedência parametrizada | `tests/test_skill_policy.py` | `test_cross_phase_error_precedence` | Registry vence policy; policy vence request; sintaxe vence duplicidade |
| AC-43 | Unitário | `tests/test_skill_policy.py` | `test_planning_is_deterministic` | Repetições produzem resultado ou erro idêntico |

Os testes de segurança devem incluir comportamento permitido, bloqueado e de
regressão. Helpers devem construir modelos diretamente; não devem duplicar o
parser nem usar monkeypatch amplo de internals da policy. Provas de ausência de
efeito usam marcadores, snapshots, sentinelas ou monkeypatch somente nas
fronteiras públicas/perigosas que jamais deveriam ser chamadas; inspeção
textual da implementação não é prova principal.

## Arquivos Provavelmente Afetados

- `src/hermes_ops/skills/policy.py` — policy, plano e planejamento puro;
- `src/hermes_ops/skills/__init__.py` — exportação da API mínima;
- `src/hermes_ops/core/errors.py` — `SkillPolicyError`;
- `tests/test_skill_policy.py` — testes unitários, segurança e integração.

Não se prevê alteração em loader, validator, registry, CLI, skills existentes,
HERMES-0003 ou HERMES-0004.

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| 2026-08-10 | API pública `SkillPolicy`, `SkillPlan` e `plan_skills` | Segue o padrão de modelos imutáveis e funções públicas pequenas | Planner mutável ou registry com autorização embutida |
| 2026-08-10 | Policy obrigatória e externa à skill | Declaração da skill não pode conceder capacidade | Defaults permissivos ou policy em `SkillDefinition` |
| 2026-08-10 | `available_requires` exige `frozenset[str]` estrito | Evita mutação, coerção e deduplicação silenciosa | Aceitar iterável e converter |
| 2026-08-10 | `requested_ids` exige tupla ordenada não vazia | Preserva intenção e evita consumo de iteradores externos | Aceitar qualquer iterável ou plano vazio |
| 2026-08-10 | IDs solicitados reutilizam exatamente a gramática da HERMES-0003 | Distingue request inválido de ID válido ausente sem normalização | Tratar toda string como lookup |
| 2026-08-10 | Registry inválido e estrutura inválida de plano usam `SKILL_PLAN_INVALID` com causas distintas | Mantém conjunto pequeno de códigos e exige tipos públicos reais | Duck typing ou código adicional sem ganho semântico |
| 2026-08-10 | Plano preserva ordem solicitada | Ordem representa intenção do chamador | Reordenar pelo registry |
| 2026-08-10 | Primeiro requirement ausente em ordem declarada | Diagnóstico mínimo e determinístico | Retornar conjunto completo sem ordem |
| 2026-08-10 | `SkillPlan` inclui a policy e valida construção direta | Plano registra o gate e não pode ser criado invalidamente pela API comum | Plano contendo apenas IDs ou construtor permissivo |
| 2026-08-10 | Uma classe `SkillPolicyError` com dez códigos | Mantém fronteira pequena e coerente com erros existentes | Subclasse para cada falha |
| 2026-08-10 | Precedência policy → request → lookup → status → risk → write → requires | Estabiliza a primeira falha observável | Ordem dependente da implementação |

## Alternativas Descartadas

1. **Autorizar diretamente no registry:** mistura existência com decisão de
   política e enfraquece a separação de responsabilidades.
2. **Usar `allows_write` como permissão:** transforma declaração do contrato em
   capability, contrariando HERMES-0003.
3. **Resolver requirements automaticamente:** exigiria import, processo,
   filesystem ou rede e ampliaria a superfície de segurança.
4. **Retornar plano parcial:** permitiria consumo acidental de subconjunto não
   solicitado e esconderia falhas de policy.
5. **Ordenar plano por ID:** perderia a ordem intencional da solicitação.
6. **Criar runner nesta fase:** planejamento não possui controles suficientes
   para execução segura.

## Riscos Restantes

- Um plano válido pode ser interpretado incorretamente por consumidor futuro
  como autorização operacional; documentação e tipos deixam a limitação
  explícita, mas o futuro runner precisará impor gates próprios.
- Strings de requirements não têm catálogo semântico nesta fase; igualdade
  exata evita ambiguidade operacional, mas erros de digitação serão apenas
  reportados como indisponibilidade.
- `get_by_id` é linear, porém suficiente para o tamanho esperado dos registries
  e já pertence ao contrato da HERMES-0004.
- Revalidar policy no plano duplica verificações simples; a defesa do construtor
  público é priorizada sobre micro-otimização.
- A API e os códigos permanecem sujeitos a auditoria antes da aprovação.

## Evidências da Implementação

A implementação preservou o contrato aprovado e foi concluída no commit
`738bc971fb3ed6802a5c5eb53958aa1f526f0216`. A aprovação anterior da própria
especificação está registrada no commit
`44edb726b6db9d1b0fb4b823f13064c88c141f5b`.

As validações comprovaram `SkillPolicy` e `SkillPlan` imutáveis, tipos estritos,
gramática aprovada para `requested_ids`, precedência normativa e lookup total
antes do gate de policy. A ordem interna observada é
`status -> risk -> write -> requires`. Atomicidade, determinismo e integração
com `SkillRegistry` real passaram.

A auditoria de segurança confirmou ausência de dependências externas, runner,
execução de skill, escrita operacional, Git mutável, subprocessos e chamadas a
`load_skill` ou `discover_skills`. Requirements permanecem declarativos e
inertes, sem mutação de `SkillRegistry` ou `SkillDefinition`.

| Campo | Valor |
|-------|-------|
| Commit da implementação | `738bc971fb3ed6802a5c5eb53958aa1f526f0216` |
| Estado da integração | Concluído na branch `feature/skills-contract`; ainda não integrado |
| Arquivos alterados | `src/hermes_ops/core/errors.py`, `src/hermes_ops/skills/__init__.py`, `src/hermes_ops/skills/policy.py`, `tests/test_skill_policy.py` |
| Testes direcionados | `pytest tests/test_skill_policy.py -q` -> 78 passed, 0 failed, 0 errors; regressão de skills -> 200 passed, 6 skipped |
| Suíte completa | `pytest -q` -> 321 collected, 313 passed, 8 skipped, 0 failed, 0 errors |
| Validação de sintaxe ou compileall | `python -m compileall -q src` -> PASS |
| Empacotamento | Não aplicável — nenhuma configuração de distribuição ou dependência foi alterada |
| git diff --check | PASS, sem avisos |
| Plataformas e versões validadas | Microsoft Windows NT 10.0.19045.0, Python 3.13.13 |
| CI | Não aplicável — implementação concluída em branch local ainda não integrada |
| Limitações do ambiente | Oito skips ambientais conhecidos na suíte completa: symlinks e fixture portátil de permission denied indisponíveis; nenhum warning novo |
| Auditoria final | PASS: contrato, precedência, atomicidade, determinismo, integração e segurança aprovados |

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| 2026-08-10 | Codex | Criação inicial da HERMES-0005 em status Rascunho, definindo policy externa, planejamento atômico e ausência de execução | Solicitação de especificação SKILL-4 |
| 2026-08-10 | Codex | Fechamento da gramática de request, registry inválido, precedência observável, construção direta e provas de ausência de efeitos | Correção após auditoria da HERMES-0005 |
| 2026-08-10 | Codex | Promoção para Aprovado e registro de justification documental temporária nos 43 ACs, antes da implementação e criação dos testes | Auditoria final concluída sem bloqueantes ou ambiguidades materiais |
| 2026-08-10 | Codex | Promoção para Implementado, substituição das 43 justifications temporárias por vínculos reais de teste e registro das evidências finais | Implementação `738bc971fb3ed6802a5c5eb53958aa1f526f0216`; aprovação `44edb726b6db9d1b0fb4b823f13064c88c141f5b` |
| 2026-08-10 | Codex | Reconciliação de AC-32 com a HERMES-0006: a fronteira posterior `run_skill`/`skill run` é permitida sem atribuir execução ao planning | `plan_skills` e `SkillPlan` permanecem declarativos; runner genérico, `execute_skill`, pipeline e execução dinâmica seguem proibidos |
