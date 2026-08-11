+++
schema_version = 1
id = "HERMES-0007"
status = "Implementado"
[[acceptance_criteria]]
id = "AC-01"
test_file = "tests/test_skill_execution.py"
test_function = "test_run_skill_separates_catalog_from_target_project"
[[acceptance_criteria]]
id = "AC-02"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_project_option_means_target_project"
[[acceptance_criteria]]
id = "AC-03"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_target_does_not_require_skills_directory"
[[acceptance_criteria]]
id = "AC-04"
test_file = "tests/test_skill_catalog.py"
test_function = "test_catalog_resolution_is_anchored_to_installed_hermes"
[[acceptance_criteria]]
id = "AC-05"
test_file = "tests/test_skill_catalog.py"
test_function = "test_catalog_resolution_never_searches_cwd_parents_or_target"
[[acceptance_criteria]]
id = "AC-06"
test_file = "tests/test_skill_catalog.py"
test_function = "test_catalog_is_discovered_with_existing_strict_contract"
[[acceptance_criteria]]
id = "AC-07"
test_file = "tests/test_skill_execution.py"
test_function = "test_requested_skill_is_loaded_by_exact_id_from_own_catalog"
[[acceptance_criteria]]
id = "AC-08"
test_file = "tests/test_cli.py"
test_function = "test_unknown_catalog_skill_fails_closed_with_exit_code_three"
[[acceptance_criteria]]
id = "AC-09"
test_file = "tests/test_cli.py"
test_function = "test_missing_target_project_fails_closed_before_handler"
[[acceptance_criteria]]
id = "AC-10"
test_file = "tests/test_skill_catalog.py"
test_function = "test_missing_or_invalid_own_catalog_fails_closed"
[[acceptance_criteria]]
id = "AC-11"
test_file = "tests/test_skill_catalog.py"
test_function = "test_invalid_catalog_candidate_aborts_atomically"
[[acceptance_criteria]]
id = "AC-12"
test_file = "tests/test_skill_execution.py"
test_function = "test_target_skill_shadow_cannot_replace_catalog_skill"
[[acceptance_criteria]]
id = "AC-13"
test_file = "tests/test_skill_execution.py"
test_function = "test_catalog_failure_precedes_planning_dispatch_and_handler"
[[acceptance_criteria]]
id = "AC-14"
test_file = "tests/test_skill_execution.py"
test_function = "test_target_validation_precedes_skill_handler"
[[acceptance_criteria]]
id = "AC-15"
test_file = "tests/test_skill_execution.py"
test_function = "test_git_preflight_remains_read_only_on_independent_target"
[[acceptance_criteria]]
id = "AC-16"
test_file = "tests/test_skill_execution.py"
test_function = "test_linked_worktree_target_preserves_security_contract"
[[acceptance_criteria]]
id = "AC-17"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_external_clean_clone_dogfooding"
[[acceptance_criteria]]
id = "AC-18"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_output_and_errors_are_sanitized"
[[acceptance_criteria]]
id = "AC-19"
test_file = "tests/test_skill_registry.py"
test_function = "test_explicit_discover_skills_api_remains_compatible"
[[acceptance_criteria]]
id = "AC-20"
test_file = "tests/test_cli.py"
test_function = "test_existing_skill_run_invocation_remains_compatible"
[[acceptance_criteria]]
id = "AC-21"
test_file = "tests/test_skill_execution.py"
test_function = "test_skill_pipeline_still_requires_policy_and_closed_dispatch"
[[acceptance_criteria]]
id = "AC-22"
test_file = "tests/test_skill_execution.py"
test_function = "test_git_commands_and_process_boundary_remain_read_only"
[[acceptance_criteria]]
id = "AC-23"
test_file = "tests/test_skill_catalog.py"
test_function = "test_packaged_catalog_contains_exact_git_preflight_contract"
[[acceptance_criteria]]
id = "AC-24"
test_file = "tests/test_packaging.py"
test_function = "test_wheel_and_sdist_include_own_skill_catalog"
[[acceptance_criteria]]
id = "AC-25"
test_file = "tests/test_cli.py"
test_function = "test_skill_run_has_no_catalog_override_option"
+++

# HERMES-0007 — Catálogo Próprio e Projeto-Alvo de Skills

## Status

Implementado

## Resumo para o Responsável pelo Projeto

O Hermes deve carregar `git-preflight` do seu próprio catálogo e executar a
inspeção sobre o projeto informado em `--project`. Assim, um repositório externo
não precisará conter `skills/`, e a interface atual continuará simples e
explícita.

A separação será fail-closed: existe uma única origem confiável de skills por
instalação, o ID solicitado é exato e qualquer falha no catálogo ou no alvo
interrompe a execução sem procurar alternativas.

## Contexto

As HERMES-0003, HERMES-0004 e HERMES-0005 introduziram, respectivamente, o
contrato passivo de uma skill, o discovery em uma raiz explícita e o gate de
política. A HERMES-0006 conectou essas camadas a um dispatcher fechado que
executa somente `git-preflight` por meio do preflight read-only existente.

O comando público implementado pela HERMES-0006 é:

```text
python -m hermes_ops skill run git-preflight --project <PROJETO>
```

No dogfooding atual, `<PROJETO>` exerce três responsabilidades diferentes:

1. fornece a raiz em que `discover_skills` procura `skills/`;
2. fornece o catálogo do qual o contrato solicitado é carregado e planejado;
3. fornece a raiz sobre a qual o handler `git-preflight` opera.

Esse desenho funciona quando o alvo é o próprio `hermes-ops`, porque sua raiz
contém `skills/git-preflight/SKILL.md`. Ele não representa a arquitetura
desejada quando o alvo é outro repositório.

Evidência de dogfooding real fornecida para esta especificação:

- contra `hermes-ops`, `git-preflight` concluiu com `status=passed` e
  `exit_code=0`;
- uma skill inexistente falhou fechada com `exit_code=3`;
- a execução preservou HEAD, working tree, staging e refs;
- contra um clone limpo da Lucre Agro, ocorreu `SKILL_ROOT_NOT_FOUND`, com a
  mensagem `The explicit project root does not contain a skills directory` e
  `exit_code=3`.

## Problema Confirmado

`run_skill(project_root, skill_id, policy)` usa hoje o mesmo `project_root` em
duas fronteiras conceitualmente independentes. Primeiro chama
`discover_skills(project_root)`; depois entrega esse mesmo valor ao dispatcher
e ao handler. `discover_skills` exige que exista o filho direto `skills/`.

Consequentemente, o alvo só pode ser inspecionado pela skill se também hospedar
o catálogo usado para autorizá-la. Isso impede o Hermes de usar sua própria
skill contra um repositório externo normal e transfere indevidamente ao alvo a
responsabilidade de fornecer código declarativo de controle do Hermes.

Não há divergência entre código, testes e HERMES-0006: o comportamento atual é
o comportamento implementado e documentado naquela fase. HERMES-0007 propõe
uma mudança pública posterior e limitada, sem reescrever retroativamente a
decisão da HERMES-0006.

## Explicação em Linguagem Simples

O local de onde vem uma ferramenta não é necessariamente o local examinado por
ela. O Hermes possui `git-preflight`; a Lucre Agro é apenas o repositório que o
Hermes deve verificar.

Depois desta mudança, `--project` responderá somente “qual projeto devo
inspecionar?”. O Hermes saberá, de forma determinística, onde está seu próprio
catálogo. Ele não tentará encontrar outra cópia em diretórios próximos e não
aceitará que o projeto-alvo substitua a skill por um arquivo de mesmo nome.

## Comportamento Atual

O fluxo atual é:

```text
--project
    +-- raiz para localizar <project>/skills/
    +-- raiz para carregar e planejar git-preflight
    +-- raiz entregue ao handler git-preflight
```

Comportamentos observáveis:

1. O alvo precisa existir e ser diretório.
2. O alvo precisa conter um filho direto `skills/` válido.
3. A skill precisa existir dentro desse diretório e passar pelo loader,
   registry e policy.
4. O dispatcher fechado chama `run_preflight` sobre a mesma raiz.
5. Ausência de `skills/` produz `SKILL_ROOT_NOT_FOUND` e exit code 3 no CLI.
6. A execução bem-sucedida continua read-only e preserva o repositório.

## Comportamento Desejado

### Interface pública

A forma preferida e normativa permanece:

```text
python -m hermes_ops skill run git-preflight --project <TARGET> [--format text|json]
```

`--project` passa a significar exclusivamente **projeto-alvo**. Não será
introduzida nesta fase uma opção pública `--skills-root`, `--catalog`,
`--hermes-root` ou equivalente.

O catálogo é um recurso próprio da instalação do Hermes. Ele deve ser
empacotado com wheel e sdist e resolvido por uma âncora pertencente ao pacote,
usando recursos da distribuição, nunca a partir de CWD, do alvo ou de busca por
ancestrais. O checkout de desenvolvimento e uma instalação construída dele
devem expor o mesmo catálogo lógico e o mesmo contrato `git-preflight`.

O diretório de autoria do repositório continua conceitualmente:

```text
hermes-ops/
  skills/
    git-preflight/
      SKILL.md
```

A implementação futura deverá declarar esse conteúdo como dado da distribuição
e garantir por teste que o artefato instalado o contém. Não haverá segunda
cópia editável mantida manualmente: se o backend de build exigir transformação
ou cópia para o artefato, ela será mecânica, verificável e terá como fonte
canônica o diretório `skills/` da raiz exata do projeto Hermes.

### Separação de responsabilidades

O fluxo normativo passa a ser:

```text
instalação do Hermes                     --project <TARGET>
        |                                        |
        v                                        v
resolver catálogo próprio               validar projeto-alvo
        |                                        |
        v                                        |
discover/load/plan skill exata                   |
        |                                        |
        +------------------+---------------------+
                           v
                    dispatcher fechado
                           |
                           v
                git-preflight read-only no TARGET
```

A API operacional deve tornar a distinção explícita internamente:

```text
run_skill(target_project, skill_id, policy) -> SkillExecutionResult
resolve_own_skill_catalog() -> raiz/recurso de catálogo validável
```

`run_skill` resolve o catálogo próprio; ele não recebe implicitamente o alvo
como catálogo. Um helper privado pode aceitar uma origem injetada apenas para
testes unitários, desde que não seja exportado nem controlável pelo CLI. A API
pública `discover_skills(explicit_root)` permanece disponível e com a semântica
da HERMES-0004 para consumidores que solicitam discovery explícito; a mudança
ocorre na composição operacional de `run_skill`.

### Ordem e atomicidade

A precedência normativa é:

1. validar forma e presença das entradas públicas;
2. validar que o projeto-alvo existe e é diretório direto aceitável;
3. resolver e validar a única origem do catálogo próprio;
4. descobrir atomicamente todos os candidatos do catálogo;
5. procurar o ID solicitado por igualdade exata;
6. planejar sob policy explícita;
7. despachar por associação literal;
8. executar o preflight read-only no alvo.

Nenhuma fase posterior ocorre quando uma fase anterior falha. Em especial, o
handler não roda diante de alvo inválido, catálogo inválido, skill ausente ou
policy bloqueada. A validação antecipada do alvo evita que erro de catálogo
mascare um `--project` inexistente; depois dela, falhas do catálogo precedem
lookup, planning e dispatch.

### Compatibilidade

- A sintaxe atual do CLI permanece válida.
- `--project` continua obrigatório e continua apontando para o repositório
  inspecionado; apenas deixa de exigir `skills/` nele.
- Um alvo que seja o próprio `hermes-ops` continua funcionando.
- Um alvo que contenha `skills/` não tem esse diretório consultado por
  `skill run`; isso impede shadowing e não constitui fallback.
- `discover_skills(root)` conserva sua semântica explícita atual.
- Registry, loader, policy, dispatcher e modelo de resultado existentes devem
  ser reutilizados, com a menor adaptação necessária para separar as raízes.
- Os exit codes públicos da HERMES-0006 permanecem: falhas semânticas
  controladas de catálogo/skill/policy usam 3; falha externa inesperada usa 4;
  resultado do preflight preserva o exit code do `Report`.

## Fora do Escopo

- Implementar qualquer código nesta tarefa documental.
- Obrigar projetos-alvo a conter `skills/`.
- Catálogo por projeto, workspace, usuário ou variável de ambiente.
- Flag pública para sobrescrever o catálogo.
- Busca em CWD, pais, irmãos, home, PATH ou múltiplas instalações.
- Merge, precedência ou fallback entre catálogos.
- Download, atualização remota, registry remoto ou rede.
- Plugins, entry points de terceiros ou import dinâmico de handlers.
- Execução de texto Markdown, scripts ou comandos declarados na skill.
- Adicionar handlers além de `git-preflight`.
- Alterar o contrato declarativo de `git-preflight`, salvo ajuste estritamente
  necessário de empacotamento sem mudança semântica.
- Git mutável, escrita no alvo, commit, push ou alteração de branch.
- Resolver identidade/versionamento de catálogos de múltiplas distribuições.
- Remover os comandos legados `doctor`, `worktree` ou `preflight`.

## Entradas

### CLI

- ID posicional exato da skill.
- `--project <TARGET>` obrigatório.
- `--format text|json`, opcional e fechado aos valores existentes.

### API operacional

- `target_project`: caminho explícito do projeto-alvo.
- `skill_id`: string que segue a gramática existente e é comparada exatamente.
- `policy`: `SkillPolicy` explícita e válida.

### Origem interna

- recurso de catálogo pertencente à distribuição instalada do Hermes;
- contratos `SKILL.md` empacotados a partir do catálogo canônico do Hermes.

Não são entradas: CWD, conteúdo de `<TARGET>/skills`, variáveis de ambiente de
catálogo, pais/irmãos do alvo, texto do body como código ou configuração Git
herdada insegura.

## Saídas

- O mesmo `SkillExecutionResult` imutável da HERMES-0006 quando há execução.
- `skill_id`, `status`, `exit_code` e evidências na mesma forma pública.
- Texto ou JSON sanitizado pelo boundary central.
- Erro controlado e determinístico quando alvo, catálogo, contrato, ID ou
  policy são inválidos.
- Nenhum arquivo escrito e nenhuma alteração em HEAD, refs, staging, working
  tree, branch ou configuração Git.

## Invariantes e Regras de Segurança

1. `--project` designa somente o alvo operacional.
2. Existe exatamente um catálogo próprio selecionado por instalação.
3. A resolução do catálogo não consulta alvo, CWD, ancestrais, siblings, home,
   PATH, rede ou configuração ambiente fornecida pelo usuário.
4. Não existe fallback se o catálogo próprio estiver ausente ou inválido.
5. O alvo nunca pode sombrear ou substituir uma skill do catálogo próprio.
6. O ID é validado e comparado exatamente, sem trim, lowercase, aliases ou
   aproximação.
7. Uma skill ausente nunca resulta na execução de outra skill.
8. Todo o catálogo é validado atomicamente pelas regras existentes antes do
   planejamento; um candidato inválido bloqueia o registry completo.
9. O projeto-alvo inexistente ou que não seja diretório bloqueia antes do
   handler.
10. Discovery precede planning; planning precede dispatch; dispatch precede
    handler.
11. A policy continua explícita, least-privilege e independente das declarações
    da skill.
12. O dispatcher continua privado, literal e fechado a `git-preflight`.
13. O body de `SKILL.md` permanece passivo e nunca é interpretado.
14. Não existem plugin discovery, import dinâmico, eval, exec, shell ou comando
    fornecido pelo usuário.
15. `git-preflight` reutiliza o preflight e o `GitInspector` auditados.
16. Todo subprocesso passa por `hermes_ops.core.processes`.
17. Comandos Git permanecem somente leitura, com argumentos controlados.
18. Locks opcionais, redirecionamentos `GIT_*`, fsmonitor, prompts e
    configuração global/sistema permanecem neutralizados.
19. Includes e filters da configuração Git local permanecem bloqueados.
20. Linked Git worktrees preservam a validação de raiz e o contrato de
    segurança existente.
21. Nunca alterar HEAD, refs, staging, working tree, branch ou configuração.
22. Nunca fazer commit, push, checkout, switch, reset, clean ou stash.
23. Falha não produz resultado parcial nem tenta outra origem.
24. Toda saída pública, inclusive paths e mensagens de catálogo, passa pelo
    sanitizador central.
25. O artefato instalado deve conter exatamente o catálogo esperado; ausência,
    duplicação ou divergência bloqueia validação/empacotamento.

## Pseudocódigo

### Resolver o catálogo próprio

```text
FUNÇÃO RESOLVER_CATÁLOGO_PRÓPRIO():
    PEDIR ao mecanismo de recursos da distribuição do Hermes
        a única localização declarada do catálogo empacotado

    SE o recurso não existir, não for acessível ou não representar diretório:
        FALHAR com erro controlado de catálogo
        NÃO procurar no diretório atual
        NÃO procurar no projeto-alvo
        NÃO procurar em pais, irmãos, home ou PATH

    VALIDAR que o recurso pertence à distribuição Hermes em uso

    RETORNAR a origem única do catálogo
```

### Executar uma skill contra um alvo

```text
FUNÇÃO EXECUTAR_SKILL(projeto_alvo, id_solicitado, política):
    VALIDAR que todas as entradas obrigatórias têm forma válida

    VALIDAR diretamente que projeto_alvo existe e é diretório
    SE não for válido:
        FALHAR fechado antes de carregar ou executar qualquer handler

    catálogo = RESOLVER_CATÁLOGO_PRÓPRIO()

    registry = DESCOBRIR_SKILLS_NO_CATÁLOGO(catálogo)
    # O discovery usa loader e validações existentes e é atômico.

    skill = PROCURAR_ID_EXATO(registry, id_solicitado)
    SE não houver correspondência exata:
        FALHAR fechado como skill inexistente
        NÃO escolher nome parecido, alias ou skill do projeto_alvo

    plano = PLANEJAR((skill), política_explícita)
    SE a política bloquear:
        FALHAR antes do dispatcher

    resultado = DESPACHAR_LITERALMENTE(plano, projeto_alvo)
    # Somente git-preflight possui handler.

    RETORNAR resultado imutável
```

### Handler git-preflight

```text
FUNÇÃO EXECUTAR_GIT_PREFLIGHT(projeto_alvo):
    CHAMAR o preflight read-only existente com projeto_alvo
    USAR somente a fronteira central de processos e consultas Git auditadas

    SE o preflight produzir Report:
        CONVERTER para o resultado imutável existente
        PRESERVAR status, evidências e exit code
        RETORNAR resultado

    SENÃO:
        FALHAR sem resultado parcial

    EM TODOS OS CASOS:
        NÃO alterar HEAD, refs, staging, working tree, branch ou configuração
```

### Empacotar o catálogo

```text
AO CONSTRUIR wheel ou sdist:
    TOMAR skills/ do root exato do hermes-ops como fonte canônica
    INCLUIR o catálogo no recurso declarado da distribuição
    NÃO coletar skills de pais, siblings ou ambiente

AO TESTAR o artefato construído:
    INSTALAR ou inspecionar o artefato em ambiente isolado
    RESOLVER o catálogo pela mesma API usada em runtime
    CONFIRMAR que git-preflight existe uma vez e seu contrato é idêntico
    SE faltar, duplicar ou divergir:
        BLOQUEAR o artefato
```

## Fluxo Principal

1. O usuário solicita `git-preflight` e informa o clone externo em
   `--project`.
2. O CLI valida o alvo explícito e cria a policy piloto least-privilege.
3. O runtime resolve o catálogo único pertencente à instalação corrente.
4. O discovery existente valida atomicamente o catálogo próprio.
5. O registry retorna somente a skill cujo ID corresponde exatamente a
   `git-preflight`.
6. O planning existente valida status, risco, escrita e requirement `git`.
7. O dispatcher literal associa o plano ao único handler permitido.
8. O handler chama o preflight existente contra o clone externo.
9. A saída é convertida, sanitizada e apresentada.
10. Snapshots antes e depois confirmam que HEAD, refs, staging e working tree
    permaneceram idênticos.

## Casos de Erro e Limites

| Situação | Comportamento | Código semântico / exit code | Limite observável |
|----------|---------------|------------------------------|-------------------|
| `--project` ausente | Argparse rejeita | contrato CLI existente | Nenhuma resolução ou execução |
| Alvo inexistente | Bloqueia antes do handler | erro controlado / 3 | Não procurar pais |
| Alvo não é diretório | Bloqueia antes do handler | erro controlado / 3 | Não inspecionar Git |
| Alvo sem `skills/` | Permitido | resultado normal | Catálogo vem do Hermes |
| Alvo contém skill homônima maliciosa | Ignorar por completo | resultado baseado no catálogo próprio | Sem shadowing |
| Recurso de catálogo ausente | Bloqueia | novo erro estável de catálogo / 3 | Sem fallback |
| Recurso de catálogo não é diretório | Bloqueia | novo erro estável de catálogo / 3 | Sem fallback |
| Catálogo inacessível | Bloqueia | erro controlado de catálogo / 3 | Sem traceback público |
| Candidato/contrato inválido no catálogo | Discovery atômico bloqueia | código existente específico / 3 | Nenhum plano parcial |
| ID inválido | Bloqueia pela gramática existente | código existente / 3 | Sem normalização |
| ID válido inexistente | Bloqueia lookup/planning | código existente / 3 | Não executar outra skill |
| Skill válida sem handler | Dispatcher fechado bloqueia | `SKILL_EXECUTION_NOT_SUPPORTED` / 3 | Nenhum fallback |
| Policy bloqueia | Planejamento bloqueia | código existente / 3 | Handler não chamado |
| Git indisponível ou alvo não é repo válido | Preflight retorna findings/erro conforme contrato existente | exit code do `Report` | Não confundir com catálogo |
| Linked worktree válido | Inspecionar segundo regras existentes | resultado normal | Preservar common dir e worktree |
| Config Git local insegura | Bloquear conforme contrato existente | resultado do preflight | Não seguir include/filter |
| Exceção inesperada | Boundary final sanitiza | `external_failure` / 4 | Sem traceback ou path bruto |
| Wheel/sdist sem catálogo | Teste de packaging bloqueia release | falha de teste/build | Não aceitar instalação incompleta |

Os nomes exatos dos novos códigos de resolução de catálogo são decisão de
implementação, mas devem pertencer à taxonomia `SKILL_CATALOG_*`, ser estáveis,
determinísticos e não colidir com `SKILL_ROOT_*`, que continua descrevendo o
discovery explícito da HERMES-0004.

## Critérios de Aceitação

- **AC-01**: A execução operacional usa origens distintas para catálogo próprio
  e projeto-alvo; o alvo nunca é passado como raiz de discovery da skill.
- **AC-02**: Na CLI, `--project` significa exclusivamente o projeto-alvo sobre
  o qual o handler opera.
- **AC-03**: Um projeto-alvo válido sem diretório `skills/` pode executar
  `git-preflight` carregada do Hermes.
- **AC-04**: O catálogo é resolvido de um único recurso pertencente à
  distribuição corrente do Hermes, independentemente do alvo e do CWD.
- **AC-05**: A resolução não busca CWD, pais, irmãos, home, PATH, alvo ou rede e
  não possui fallback silencioso.
- **AC-06**: Loader, validação, registry atômico e policy existentes continuam
  sendo usados sobre o catálogo próprio.
- **AC-07**: O ID solicitado é validado e consultado por igualdade exata; sem
  normalização, alias ou aproximação.
- **AC-08**: Skill inexistente bloqueia com erro controlado e exit code 3, sem
  execução de qualquer outra skill.
- **AC-09**: Projeto-alvo inexistente ou não diretório bloqueia com erro
  controlado antes do handler.
- **AC-10**: Catálogo ausente, inacessível ou de tipo inválido bloqueia com
  código estável `SKILL_CATALOG_*`, exit code 3 e sem fallback.
- **AC-11**: Um único candidato inválido torna o catálogo inteiro inválido e
  impede plano, dispatch, handler e resultado parcial.
- **AC-12**: Uma pasta `<TARGET>/skills` ou skill homônima no alvo nunca é lida
  por `skill run` e não pode sombrear o catálogo próprio.
- **AC-13**: Falha de resolução/discovery do catálogo impede lookup, planning,
  dispatch e handler.
- **AC-14**: A validação direta do alvo ocorre antes do catálogo; alvo inválido
  impede resolução posterior e execução.
- **AC-15**: Em repositório Git independente, `git-preflight` preserva HEAD,
  refs, staging e working tree byte a byte/porcelain conforme snapshot forte da
  HERMES-0006.
- **AC-16**: Linked Git worktrees continuam aceitos ou bloqueados exatamente
  pelo contrato existente, sem relaxar root validation, configuração segura ou
  neutralização Git.
- **AC-17**: Dogfooding executa a skill real do catálogo do Hermes contra clone
  Git independente e limpo da Lucre Agro, sem `skills/` no clone, obtendo
  `status=passed`, `exit_code=0` e preservando HEAD, working tree, staging e
  refs.
- **AC-18**: Texto e JSON, inclusive erros de catálogo e paths externos, passam
  pelo sanitizador central e não expõem traceback, segredos ou caminhos brutos.
- **AC-19**: `discover_skills(explicit_root)` mantém a API e a semântica da
  HERMES-0004; a separação ocorre na composição de execução.
- **AC-20**: A invocação existente contra o próprio Hermes continua válida sem
  novas flags obrigatórias.
- **AC-21**: Policy explícita, planning real e dispatcher literal permanecem
  obrigatórios; nenhum caminho direto para handler é criado.
- **AC-22**: Os únicos subprocessos alcançáveis continuam na fronteira central
  e na allowlist Git read-only existente; nenhuma operação mutável é adicionada.
- **AC-23**: O catálogo empacotado contém uma única skill `git-preflight`, com
  contrato semanticamente idêntico à fonte canônica `skills/git-preflight/SKILL.md`.
- **AC-24**: Wheel e sdist construídos contêm o catálogo próprio e permitem
  resolvê-lo sem depender do checkout, do CWD ou do projeto-alvo.
- **AC-25**: O CLI não oferece opção para selecionar ou sobrescrever catálogo
  nesta fase.

## Plano de Testes

Todo teste novo deve conter `Spec: HERMES-0007 / AC-NN` em docstring ou
comentário. Repositórios Git são criados somente em diretórios temporários, com
o helper seguro existente; o teste de aceitação da Lucre Agro usa um clone
independente previamente disponibilizado pelo ambiente de dogfooding e não faz
clone, fetch ou qualquer acesso remoto durante a suíte.

| AC | Tipo | Arquivo | Função planejada | Prova |
|----|------|---------|------------------|-------|
| AC-01 | Unitário | `tests/test_skill_execution.py` | `test_run_skill_separates_catalog_from_target_project` | Duas raízes conceituais e alvo fora do discovery |
| AC-02 | CLI | `tests/test_cli.py` | `test_skill_run_project_option_means_target_project` | Semântica pública de `--project` |
| AC-03 | Integração/permitido | `tests/test_cli.py` | `test_skill_run_target_does_not_require_skills_directory` | Alvo sem catálogo funciona |
| AC-04 | Unitário | `tests/test_skill_catalog.py` | `test_catalog_resolution_is_anchored_to_installed_hermes` | Âncora única da distribuição |
| AC-05 | Segurança | `tests/test_skill_catalog.py` | `test_catalog_resolution_never_searches_cwd_parents_or_target` | Sentinelas maliciosas nunca consultadas |
| AC-06 | Integração | `tests/test_skill_catalog.py` | `test_catalog_is_discovered_with_existing_strict_contract` | Loader/registry reais |
| AC-07 | Unitário | `tests/test_skill_execution.py` | `test_requested_skill_is_loaded_by_exact_id_from_own_catalog` | Lookup literal |
| AC-08 | CLI/bloqueado | `tests/test_cli.py` | `test_unknown_catalog_skill_fails_closed_with_exit_code_three` | Skill ausente, sem fallback |
| AC-09 | CLI/bloqueado | `tests/test_cli.py` | `test_missing_target_project_fails_closed_before_handler` | Alvo inexistente |
| AC-10 | Segurança parametrizada | `tests/test_skill_catalog.py` | `test_missing_or_invalid_own_catalog_fails_closed` | Ausente, arquivo e inacessível |
| AC-11 | Segurança | `tests/test_skill_catalog.py` | `test_invalid_catalog_candidate_aborts_atomically` | Registry sem parcial |
| AC-12 | Segurança | `tests/test_skill_execution.py` | `test_target_skill_shadow_cannot_replace_catalog_skill` | Shadowing bloqueado por não leitura |
| AC-13 | Unitário | `tests/test_skill_execution.py` | `test_catalog_failure_precedes_planning_dispatch_and_handler` | Precedência com sentinelas |
| AC-14 | Unitário | `tests/test_skill_execution.py` | `test_target_validation_precedes_skill_handler` | Validação do alvo primeiro |
| AC-15 | Integração/regressão | `tests/test_skill_execution.py` | `test_git_preflight_remains_read_only_on_independent_target` | Snapshot forte antes/depois |
| AC-16 | Integração/segurança | `tests/test_skill_execution.py` | `test_linked_worktree_target_preserves_security_contract` | Linked worktree e configuração comum |
| AC-17 | Aceitação/dogfooding | `tests/test_cli.py` | `test_skill_run_external_clean_clone_dogfooding` | Lucre Agro limpa, PASS e invariantes |
| AC-18 | CLI/segurança | `tests/test_cli.py` | `test_skill_run_output_and_errors_are_sanitized` | Texto e JSON seguros |
| AC-19 | Regressão | `tests/test_skill_registry.py` | `test_explicit_discover_skills_api_remains_compatible` | HERMES-0004 preservada |
| AC-20 | Regressão CLI | `tests/test_cli.py` | `test_existing_skill_run_invocation_remains_compatible` | Mesmo comando no Hermes |
| AC-21 | Regressão/segurança | `tests/test_skill_execution.py` | `test_skill_pipeline_still_requires_policy_and_closed_dispatch` | HERMES-0005/0006 preservadas |
| AC-22 | Segurança | `tests/test_skill_execution.py` | `test_git_commands_and_process_boundary_remain_read_only` | Allowlist e boundary central |
| AC-23 | Packaging/unitário | `tests/test_skill_catalog.py` | `test_packaged_catalog_contains_exact_git_preflight_contract` | Fonte e recurso idênticos |
| AC-24 | Packaging/integração | `tests/test_packaging.py` | `test_wheel_and_sdist_include_own_skill_catalog` | Artefatos autossuficientes |
| AC-25 | CLI/segurança | `tests/test_cli.py` | `test_skill_run_has_no_catalog_override_option` | Sem override público |

### Detalhes obrigatórios dos testes de segurança

- **Permitido:** alvo Git temporário válido e sem `skills/` executa
  `git-preflight` do catálogo próprio.
- **Bloqueado:** alvo inexistente, catálogo inválido, skill ausente, contrato
  inválido e tentativa de shadowing não alcançam o handler.
- **Regressão:** alvo `hermes-ops`, linked worktree, policy, dispatcher,
  sanitização, allowlist Git e `discover_skills` explícito permanecem válidos.

O snapshot forte de AC-15 e AC-17 registra antes e depois:

```text
git rev-parse --verify HEAD
git status --porcelain=v1 -z --untracked-files=all
git diff --cached --binary
lista e valores de refs relevantes
mapa de bytes dos arquivos controlados quando aplicável
branch simbólica ou estado detached
```

As consultas de prova também devem usar a infraestrutura Git segura do projeto
ou helpers de teste isolados, com configuração neutralizada. Não comparar
mtime/atime. O dogfooding da Lucre Agro é teste de aceitação condicionado à
disponibilidade local do clone independente; sua ausência pode gerar skip
justificado na suíte portátil, mas a promoção da especificação para
`Implementado` exige evidência concreta de uma execução real bem-sucedida, não
um skip.

## Arquivos Provavelmente Afetados

| Caminho | Papel futuro |
|---------|--------------|
| `src/hermes_ops/skills/catalog.py` | Resolução determinística do catálogo próprio |
| `src/hermes_ops/skills/executor.py` | Separar catálogo resolvido do projeto-alvo |
| `src/hermes_ops/skills/registry.py` | Reutilização/adaptação mínima para origem de recurso, se necessária |
| `src/hermes_ops/skills/__init__.py` | Export mínimo, somente se houver novo contrato público indispensável |
| `src/hermes_ops/core/errors.py` | Erro estável `SKILL_CATALOG_*` |
| `src/hermes_ops/commands/skill.py` | Nomeação explícita de target e composição CLI |
| `src/hermes_ops/cli.py` | Ajuda de `--project`; sem nova opção de catálogo |
| `pyproject.toml` | Inclusão declarada do catálogo nos artefatos |
| `MANIFEST.in` | Inclusão no sdist, somente se o backend exigir |
| `skills/git-preflight/SKILL.md` | Fonte canônica, sem mudança semântica prevista |
| `tests/test_skill_catalog.py` | Resolução, atomicidade, origem e packaging lógico |
| `tests/test_skill_execution.py` | Separação, ordem, segurança Git e linked worktrees |
| `tests/test_cli.py` | Contrato público, erros, dogfooding e sanitização |
| `tests/test_packaging.py` | Wheel/sdist autossuficientes |

Nenhum desses arquivos de produção é alterado durante a criação desta
especificação.

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| 2026-08-11 | Manter `skill run <id> --project <TARGET>` | A interface já expressa o alvo e não precisa expor detalhe do catálogo | Adicionar flag obrigatória de catálogo |
| 2026-08-11 | `--project` designa somente o alvo | Remove a sobrecarga observada e torna o contrato explicável | Manter raiz híbrida |
| 2026-08-11 | Resolver automaticamente um catálogo pertencente à distribuição Hermes | Permite uso instalado e impede dependência do alvo/CWD | Descoberta por proximidade |
| 2026-08-11 | Não oferecer override público de catálogo nesta fase | Evita ambiguidade, shadowing e ampliação da superfície de confiança | `--skills-root` opcional |
| 2026-08-11 | Manter `skills/` da raiz exata do Hermes como fonte canônica de autoria | Preserva o layout existente e evita duas fontes manuais | Duplicar contratos sob `src/` |
| 2026-08-11 | Empacotar o catálogo como recurso da distribuição | Wheel/sdist não podem depender do checkout | Calcular repo root em runtime |
| 2026-08-11 | Validar alvo antes de resolver catálogo | Um `--project` inexistente deve bloquear com causa direta e sem handler | Deixar preflight descobrir tarde |
| 2026-08-11 | Preservar `discover_skills(root)` explícito | HERMES-0004 continua útil e compatível; muda apenas a composição operacional | Alterar globalmente sua semântica |
| 2026-08-11 | Ignorar totalmente `<TARGET>/skills` em `skill run` | Impede shadowing e execução de contrato diferente | Merge de catálogos |
| 2026-08-11 | Exigir dogfooding externo real antes de status Implementado | A falha foi encontrada em uso real e precisa de prova equivalente | Apenas fixtures sintéticas |

## Decisões Pendentes Antes da Implementação

Não há decisão de produto pendente. A implementação ainda deverá escolher o
mecanismo exato suportado pelo backend de build atual para materializar
`skills/` como recurso da distribuição, desde que satisfaça integralmente
AC-04, AC-23 e AC-24 e não crie segunda fonte manual.

Os nomes específicos dentro da família `SKILL_CATALOG_*` serão fechados antes
do primeiro teste, mantendo um código distinto ao menos para origem ausente e
origem inválida/inacessível. Essa escolha não altera precedência, exit code ou
comportamento público definidos aqui.

## Alternativas Descartadas

1. **Continuar exigindo `<TARGET>/skills`:** mantém o bug e transfere ao alvo a
   responsabilidade pelo catálogo do Hermes.
2. **Adicionar `--skills-root` obrigatório:** resolve tecnicamente, mas torna a
   operação comum verbosa e permite apontar acidentalmente para catálogo não
   confiável.
3. **Adicionar override opcional agora:** cria duas origens públicas e exige
   regras de precedência sem necessidade demonstrada.
4. **Procurar `skills/` no CWD:** o resultado dependeria do diretório de
   invocação e permitiria shadowing.
5. **Subir pelos ancestrais até encontrar `skills/`:** viola a regra de não
   descobrir pais/siblings e pode selecionar catálogo inesperado.
6. **Preferir catálogo do alvo e usar o próprio como fallback:** permite que um
   alvo controle qual contrato é autorizado e torna falhas silenciosas.
7. **Mesclar catálogo próprio e catálogo do alvo:** introduz colisões,
   precedência e execução potencial de skill diferente da solicitada.
8. **Resolver a raiz do checkout por `__file__` e contagem de pais:** funciona
   apenas em layout de fonte e pode escapar para `site-packages` ou outro pai em
   instalações reais.
9. **Usar variável de ambiente para catálogo:** amplia entrada não confiável e
   torna a execução dependente de estado herdado.
10. **Embeddar o contrato como string Python:** duplica a fonte canônica e
    enfraquece loader/discovery reais.
11. **Pular registry/planning para handler conhecido:** corrigiria o sintoma ao
    custo de remover gates aprovados nas HERMES-0004/0005/0006.
12. **Copiar `skills/` para cada projeto consumidor:** não escala, diverge e
    impede o Hermes de governar sua própria skill.

## Riscos Restantes

- **Empacotamento incompleto:** wheel pode funcionar no checkout e falhar após
  instalação. Mitigação: AC-23/24 inspecionam ambos os artefatos fora da raiz.
- **Duplicação fonte/recurso:** uma cópia manual pode divergir. Mitigação: uma
  fonte canônica e comparação byte/semântica automatizada.
- **Recursos não materializados como `Path`:** `importlib.resources` pode
  fornecer traversable ou extração temporária. A adaptação ao discovery precisa
  manter validações de tipo, atomicidade e ausência de busca.
- **Mudança de precedência de erros:** separar raízes cria duas falhas possíveis.
  A ordem normativa desta spec deve ser coberta por sentinelas.
- **Confusão entre `SKILL_ROOT_*` e `SKILL_CATALOG_*`:** mitigada por taxonomias
  distintas e mensagens que não exponham path bruto.
- **Compatibilidade de API Python:** renomear conceitualmente `project_root` para
  `target_project` não deve quebrar chamadas posicionais existentes. Chamadas
  por keyword precisam de decisão conservadora na implementação, possivelmente
  mantendo o nome público e esclarecendo sua semântica.
- **Clone real indisponível no CI:** o teste portátil pode precisar de skip,
  mas a evidência final de dogfooding é obrigatória fora do CI.
- **Linked worktrees:** `.git` arquivo e common dir ampliam casos de path e
  configuração. A implementação não pode contornar `GitInspector`.
- **Catálogo instalado adulterado:** a validação contratual bloqueia estrutura
  inválida, mas esta fase não define assinatura criptográfica de distribuição.
- **Instalações múltiplas:** o Python seleciona uma distribuição importada; esta
  spec garante coerência com ela, não escolhe entre ambientes Python.
- **Escopo futuro de outras skills:** adicionar novo handler ou catálogo
  configurável exige especificação própria.

## Evidências da Implementação

A implementação separa o catálogo instalado do projeto-alvo, preserva as
fronteiras das HERMES-0004/0005/0006 e foi validada tanto no checkout editável
quanto em wheel instalado isoladamente. O usuário proibiu commit nesta tarefa;
por isso o estado validado é o diff local ainda não commitado.

| Campo | Valor |
|-------|-------|
| Commit | Não aplicável — o usuário determinou explicitamente que a implementação não fosse commitada |
| Estado da integração | Implementação local concluída e não commitada |
| Arquivos alterados | `MANIFEST.in`, `pyproject.toml`, `src/hermes_ops/cli.py`, `src/hermes_ops/commands/skill.py`, `src/hermes_ops/core/errors.py`, `src/hermes_ops/skills/catalog.py`, `src/hermes_ops/skills/executor.py`, `tests/test_skill_catalog.py`, `tests/test_skill_execution.py`, `tests/test_skill_registry.py`, `tests/test_cli.py`, `tests/test_packaging.py` e esta especificação |
| Testes direcionados | Matriz HERMES-0004/0005/0006/0007 → 205 passed, 7 skipped; repetição final dos módulos afetados após endurecimento de erros de catálogo → 97 passed, 1 skipped; 0 failed, 0 errors |
| Suíte completa | `.venv\Scripts\python.exe -m pytest -q` → 398 passed, 9 skipped, 0 failed, 0 errors |
| Validação de sintaxe ou compileall | `.venv\Scripts\python.exe -m compileall -q src` → PASS, exit code 0 |
| Empacotamento | `.venv\Scripts\python.exe -m build` → wheel e sdist construídos; `tests/test_packaging.py` → 4 passed, incluindo instalação isolada e catálogo idêntico |
| git diff --check | PASS, sem avisos |
| Plataformas e versões validadas | Windows 10, Python 3.13.13 |
| CI | Não aplicável — validação local solicitada; nenhuma operação remota foi autorizada |
| Limitações do ambiente | 8 skips portáteis relacionados a symlinks/permissão no Windows e 1 skip intencional do teste automatizado opt-in de dogfooding; a aceitação externa correspondente foi executada concretamente após a suíte |
| Auditoria final | PASS, 25 critérios vinculados às funções declaradas no front matter |

### Empacotamento Comprovado

- a fonte canônica permanece `skills/git-preflight/SKILL.md`;
- sdist contém exatamente essa fonte sob `skills/`;
- wheel contém uma única cópia em
  `hermes_ops_skill_catalog/skills/git-preflight/SKILL.md` como data-file;
- a instalação normal resolve o catálogo pelo arquivo registrado no manifesto
  da distribuição;
- a instalação editável resolve exclusivamente a raiz local declarada em
  `direct_url.json`, nunca CWD, TARGET, ancestrais, siblings, home ou PATH;
- o wheel instalado em venv isolado executou `git-preflight` contra um alvo sem
  `skills/` com `status=passed`.

### Dogfooding Externo Real

Projeto-alvo:

```text
C:\Users\Danilo\Projeto\lucreagro-hermes-clone
```

O clone não continha `skills/` e não foi alterado ou limpo para a execução. O
comando executado com o interpretador local foi:

```text
.venv\Scripts\python.exe -m hermes_ops skill run git-preflight \
    --project "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" \
    --format text
```

Resultado:

```text
skill_id=git-preflight
status=passed
exit_code=0
process_exit_code=0
```

Snapshot antes e depois:

| Estado | Antes | Depois | Preservado |
|--------|-------|--------|------------|
| HEAD | `2d1402764b379bf742c78819eff122cc657d86c5` | `2d1402764b379bf742c78819eff122cc657d86c5` | Sim |
| Working tree (`status --porcelain=v1`) | vazia | vazia | Sim |
| Staging (`diff --cached --name-status`) | vazio | vazio | Sim |
| Refs (`show-ref`) | 40 refs, SHA-256 `fbcb522489a8c38e233bce51ef3a4d5955346d172a973e115b50d2d865d17620` | 40 refs, mesmo SHA-256 | Sim |

As capturas externas usaram somente consultas Git read-only, com locks
opcionais, configurações global/sistema, fsmonitor, prompts e redirecionamentos
`GIT_*` neutralizados.

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| 2026-08-11 | Codex | Criação inicial da HERMES-0007 em status Rascunho, separando catálogo próprio e projeto-alvo sem nova flag pública | Dogfooding real contra Hermes e clone independente da Lucre Agro |
| 2026-08-11 | Codex | Implementação do catálogo próprio ancorado na distribuição, separação do TARGET, packaging wheel/sdist e matriz completa de testes | 205 testes direcionados e 398 testes na suíte completa, sem falhas |
| 2026-08-11 | Codex | Promoção para Implementado após dogfooding externo real com PASS e preservação integral do estado Git | Clone independente da Lucre Agro, HEAD `2d1402764b379bf742c78819eff122cc657d86c5` |
