# HERMES-0001 — Git Opcional e Configuração Worktree

## Status

Implementado

**Integração:**
- Commit original da implementação: `25cfc73`
- Commit de integração na main: `327b667`
- PR: #1
- Data da integração: 2026-07-30
- 8 checks de CI aprovados

## Resumo para o Responsável pelo Projeto

Esta especificação resolve uma inconsistência: quando o projeto declara `git.required = false`, falhas operacionais do Git (como Git não instalado, repositório inexistente, permissão negada) ainda faziam o `preflight` falhar com código de saída diferente de zero. Agora essas falhas viram **AVISO**, permitindo que o fluxo continue. Contudo, **configuração Git insegura** (includes externos, filtros, indireções) continua **BLOQUEANTE** mesmo com Git opcional, pois representa risco de segurança. Além disso, o arquivo `.git/config.worktree` (usado quando `extensions.worktreeConfig = true`) é validado **antes** de qualquer consulta Git, aplicando as mesmas regras de bloqueio.

## Contexto

O `hermes-ops` suporta a configuração `git.required` no arquivo `.hermes/project.toml`:

```toml
[git]
required = true   # ou false
protected_branches = ["main", "release"]
require_clean_worktree = true
```

Quando `required = false`, a intenção é que a ausência ou falha do Git **não** impeça o uso das outras ferramentas (doctor, worktree, preflight). No entanto, a implementação anterior tratava várias falhas Git como erros bloqueantes independentemente dessa configuração, tornando `git.required = false` ineficaz na prática.

Paralelamente, o Git suporta `extensions.worktreeConfig` que, quando habilitado, faz o Git ler configuração adicional de `.git/config.worktree`. Esse arquivo pode conter as mesmas diretivas perigosas (`include.path`, `includeIf`, `filter`) que já são bloqueadas em `.git/config`. A validação precisa acontecer **antes** de invocar o Git, pois o próprio Git carregaria essas configurações perigosas.

## Problema Confirmado

1. **Git opcional ineficaz**: Com `git.required = false`, erros como `git_unavailable`, `git_repository_missing`, `git_operational_error`, `git_permission_denied`, `git_dubious_ownership`, `git_unexpected_output` ainda resultavam em `exit_code != 0` no `preflight`.

2. **Inconsistência entre comandos**: `doctor` e `worktree` tinham lógicas diferentes para rebaixar erros a avisos quando Git era opcional.

3. **Configuração worktree não validada**: O arquivo `.git/config.worktree` não era inspecionado, permitindo que includes e filtros perigosos fossem carregados pelo Git quando `extensions.worktreeConfig = true`.

## Comportamento Atual (Antes da Correção)

| Cenário | `git.required = true` | `git.required = false` |
|---------|----------------------|------------------------|
| Git não instalado | ERRO/BLOQUEADO | ERRO (incorreto) |
| Não é repositório Git | BLOQUEADO | ERRO (incorreto) |
| Erro operacional (permissão, etc.) | ERRO | ERRO (incorreto) |
| Raiz Git difere do projeto | BLOQUEADO | BLOQUEADO (correto) |
| `.git` indireto (symlink/junction) | BLOQUEADO | BLOQUEADO (correto) |
| `include.path` em `.git/config` | BLOQUEADO | BLOQUEADO (correto) |
| `include.path` em `.git/config.worktree` | **Não validado** | **Não validado** |
| `filter` em `.git/config.worktree` | **Não validado** | **Não validado** |

## Comportamento Desejado (Após a Correção)

| Cenário | `git.required = true` | `git.required = false` |
|---------|----------------------|------------------------|
| Git não instalado | ERRO | **AVISO** |
| Não é repositório Git | BLOQUEADO | **AVISO** |
| Erro operacional (permissão, etc.) | ERRO | **AVISO** |
| Raiz Git difere do projeto | BLOQUEADO | BLOQUEADO |
| `.git` indireto (symlink/junction) | BLOQUEADO | BLOQUEADO |
| `include.path` / `includeIf` / `filter` em `.git/config` | BLOQUEADO | BLOQUEADO |
| `include.path` / `includeIf` / `filter` em `.git/config.worktree` (se `extensions.worktreeConfig = true`) | BLOQUEADO | BLOQUEADO |
| Configuração worktree segura | OK | OK |

**Regra geral**: falhas **exclusivamente operacionais do Git** viram AVISO quando `git.required = false`. Falhas de **segurança ou integridade estrutural** (raiz, indireção, configuração perigosa) **nunca** são rebaixadas.

## Fora do Escopo

- Alteração no formato de `.hermes/project.toml`.
- Novos códigos de erro além dos já existentes.
- Mudança no comportamento de `protected_branches` ou `require_clean_worktree`.
- Suporte a submodules, worktrees vinculados ou repositórios bare.
- Validação de configuração global/sistema do Git (já neutralizada pelo ambiente seguro).

## Entradas

- Caminho do projeto (`--project` ou diretório atual).
- Arquivo `.hermes/project.toml` com campo `git.required` (boolean, default `true`).
- Repositório Git (ou ausência dele) no caminho do projeto.
- Arquivos `.git/config` e `.git/config.worktree` (se existirem).
- Variáveis de ambiente `GIT_*` (neutralizadas pelo ambiente seguro).

## Saídas

- `GitState` com campos:
  - `available` (bool): Git executável encontrado.
  - `is_repository` (bool): É repositório Git válido.
  - `root`, `branch`, `head`, `has_commits`, `detached`.
  - `changes` (WorktreeChanges): modified, added, removed, untracked, conflicts.
  - `error` (str | None): Mensagem de erro legível.
  - `error_code` (str | None): Código de erro padronizado.
- `Report` dos comandos `doctor`, `worktree`, `preflight` com:
  - `CheckResult` por verificação (status: OK, AVISO, ERRO, BLOQUEADO).
  - `exit_code` agregado (0 = sucesso, 1 = aviso, 2 = erro, 3 = bloqueado, 4 = configuração).

## Invariantes e Regras de Segurança

1. **Nenhuma consulta Git é executada antes de validar `.git/config` e `.git/config.worktree`** (quando aplicável).
2. **`include.path`, `includeIf`, `filter`** em configuração local ou worktree **sempre bloqueiam** (código `git_unsafe_local_config`).
3. **Indireção de `.git`** (arquivo `gitdir:`, symlink, junction) **sempre bloqueia** (código `git_indirect_repository_unsupported`).
4. **`core.fsmonitor` e `core.autocrlf`** são forçados via `-c` em toda invocação Git.
5. **Ambiente Git seguro**: `GIT_CONFIG_GLOBAL=os.devnull`, `GIT_CONFIG_SYSTEM=os.devnull`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_OPTIONAL_LOCKS=0`, `GIT_TERMINAL_PROMPT=0`, `LC_ALL=C`, `LANG=C`; variáveis `GIT_*` herdadas são removidas.
6. **Raiz do projeto declarada** deve coincidir com `git rev-parse --show-toplevel`; mismatch bloqueia sempre.
7. **Inspecção é imutável**: não altera estado do working tree, não cria locks, não executa hooks.

## Pseudocódigo

```text
CONSTANTES:
    OPTIONAL_GIT_WARNING_CODES = {
        "git_unavailable",
        "git_repository_missing",
        "git_operational_error",
        "git_permission_denied",
        "git_dubious_ownership",
        "git_unexpected_output"
    }

    NEVER_DOWNGRADE_CODES = {
        "git_root_mismatch",
        "git_indirect_repository_unsupported",
        "git_unsafe_local_config",
        "git_declared_root_invalid"
    }

FUNÇÃO inspect(project_path):
    # 1. Resolver raiz declarada
    declared_root = RESOLVER(project_path, estrito=true)
    SE falhou:
        RETORNAR GitState(available=true, is_repository=false,
                          error="raiz declarada inválida",
                          error_code="git_declared_root_invalid")

    # 2. Verificar .git (arquivo ou indireção)
    git_entry = declared_root / ".git"
    SE git_entry É_ARQUIVO OU É_INDIRETO:
        RETORNAR GitState(available=true, is_repository=true,
                          error="repositório indireto não suportado",
                          error_code="git_indirect_repository_unsupported")

    # 3. VALIDAR CONFIGURAÇÃO LOCAL ANTES DE QUALQUER COMANDO GIT
    unsafe = _unsafe_local_config(declared_root)
    SE unsafe NÃO É NULO:
        RETORNAR unsafe  # BLOQUEIA: include, includeIf, filter, indireção

    # 4. Probe: está dentro de worktree?
    probe = RUN_GIT(declared_root, "rev-parse", "--is-inside-work-tree")
    SE probe NÃO INICIOU:
        RETORNAR GitState(available=false, is_repository=false,
                          error=probe.error, error_code="git_unavailable")
    SE probe.returncode != 0:
        RETORNAR _classify_probe_failure(probe)
    SE probe.stdout != "true":
        RETORNAR GitState(available=true, is_repository=false,
                          error="raiz Git difere da declarada",
                          error_code="git_root_mismatch")

    # 5. Obter raiz real do Git
    root_result = RUN_GIT(declared_root, "rev-parse", "--show-toplevel")
    SE root_result FALHOU:
        RETORNAR GitState(..., error_code="git_operational_error")
    git_root = RESOLVER(root_result.stdout)
    SE git_root != declared_root:
        RETORNAR GitState(..., root=git_root,
                          error="raiz Git difere da declarada",
                          error_code="git_root_mismatch")

    # 6. Coletar estado (HEAD, branch, status)
    head_result = RUN_GIT(declared_root, "rev-parse", "--verify", "HEAD")
    has_commits = head_result.succeeded
    head = head_result.stdout SE has_commits SENÃO NULO

    branch_result = RUN_GIT(declared_root, "symbolic-ref", "--quiet", "--short", "HEAD")
    branch = branch_result.stdout SE branch_result.succeeded SENÃO NULO
    detached = has_commits E branch É NULO

    status_result = RUN_GIT(declared_root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    SE status_result FALHOU:
        RETORNAR GitState(..., error_code="git_operational_error")
    changes = PARSE_PORCELAIN_V1_Z(status_result.stdout)

    RETORNAR GitState(available=true, is_repository=true, root=declared_root,
                      branch=branch, head=head, has_commits=has_commits,
                      detached=detached, changes=changes)

FUNÇÃO _unsafe_local_config(root):
    # Lê .git/config
    config_path = DIRECT_PROJECT_PATH(root, ".git/config")
    SE config_path NÃO EXISTE:
        RETORNAR NULO
    text = LER_ARQUIVO_SEGURO(config_path)
    unsafe = _unsafe_config_text(text)
    SE unsafe: RETORNAR unsafe

    # Verifica se worktreeConfig está habilitado
    SE NÃO _worktree_config_enabled(text):
        RETORNAR NULO

    # Lê .git/config.worktree APÓS confirmar que a opção está ligada
    worktree_path = DIRECT_PROJECT_PATH(root, ".git/config.worktree")
    SE worktree_path NÃO EXISTE:
        RETORNAR NULO
    worktree_text = LER_ARQUIVO_SEGURO(worktree_path)
    RETORNAR _unsafe_config_text(worktree_text)

FUNÇÃO _unsafe_config_text(text):
    sections = EXTRAIR_SEÇÕES(text)  # regex: ^\s*\[\s*([A-Za-z][A-Za-z0-9.-]*)
    SE "include" EM sections OU "includeif" EM sections:
        RETORNAR GitState(..., error="config inclui configuração externa",
                          error_code="git_unsafe_local_config")
    SE "filter" EM sections:
        RETORNAR GitState(..., error="config define filtros de conteúdo externos",
                          error_code="git_unsafe_local_config")
    RETORNAR NULO

FUNÇÃO _worktree_config_enabled(text):
    PARA cada linha EM text:
        SE linha INICIA_SEÇÃO:
            section = NOME_SEÇÃO.lowercase()
        SE section == "extensions" E linha CONTÉM "worktreeconfig = true":
            RETORNAR VERDADEIRO
    RETORNAR FALSO

FUNÇÃO classificar_status_para_comando(state, config):
    SE state.error É NULO:
        SE state.is_repository: STATUS = OK
        SENÃO: STATUS = BLOQUEADO SE config.git.required SENÃO AVISO
    SENÃO:  # há erro
        SE NÃO config.git.required E state.error_code EM OPTIONAL_GIT_WARNING_CODES:
            STATUS = AVISO
        SENÃO SE state.error_code EM NEVER_DOWNGRADE_CODES:
            STATUS = BLOQUEADO
        SENÃO:
            STATUS = ERRO
    RETORNAR STATUS
```

## Fluxo Principal

1. **Entrada**: caminho do projeto.
2. **Resolver raiz declarada** (estrita, sem descobrir pais).
3. **Verificar `.git`**: se for arquivo `gitdir:` ou indireção (symlink/junction) → **BLOQUEAR**.
4. **Ler `.git/config`** de forma segura (caminho direto, sem seguir indireções).
5. **Escanear seções** por `include`, `includeIf`, `filter` → **BLOQUEAR** se encontrado.
6. **Verificar `extensions.worktreeConfig`** no texto do `.git/config`.
7. **Se habilitado**: ler `.git/config.worktree` (mesma validação de segurança) → **BLOQUEAR** se inseguro.
8. **Só então**: executar `git rev-parse --is-inside-work-tree` com ambiente seguro.
9. **Se probe falha**: classificar erro (não repositório, permissão, etc.).
10. **Obter raiz real** via `git rev-parse --show-toplevel`; comparar com declarada → **BLOQUEAR** se diferente.
11. **Coletar HEAD, branch, status** (porcelain v1, NUL-delimitado, UTF-8).
12. **Retornar `GitState`** completo.
13. **Comandos públicos** (`doctor`, `worktree`, `preflight`) usam `classificar_status_para_comando` respeitando `git.required`.

## Casos de Erro e Limites

| Situação | Comportamento | Código de Erro | Rebaixável com `git.required=false`? |
|----------|---------------|----------------|--------------------------------------|
| Git não instalado / não no PATH | AVISO/ERRO | `git_unavailable` | **Sim** |
| Diretório não é repo Git | AVISO/BLOQUEADO | `git_repository_missing` | **Sim** |
| Erro operacional genérico (exit 128) | AVISO/ERRO | `git_operational_error` | **Sim** |
| Permissão negada (arquivos/objetos) | AVISO/ERRO | `git_permission_denied` | **Sim** |
| Propriedade duvidosa (dubious ownership) | AVISO/ERRO | `git_dubious_ownership` | **Sim** |
| Saída inesperada do Git (parse falhou) | AVISO/ERRO | `git_unexpected_output` | **Sim** |
| Raiz Git ≠ raiz declarada | **BLOQUEADO** | `git_root_mismatch` | **Não** |
| `.git` é arquivo `gitdir:` | **BLOQUEADO** | `git_indirect_repository_unsupported` | **Não** |
| `.git` é symlink/junction | **BLOQUEADO** | `git_indirect_repository_unsupported` | **Não** |
| `.git/config` tem `include.path` | **BLOQUEADO** | `git_unsafe_local_config` | **Não** |
| `.git/config` tem `includeIf` | **BLOQUEADO** | `git_unsafe_local_config` | **Não** |
| `.git/config` tem `filter` | **BLOQUEADO** | `git_unsafe_local_config` | **Não** |
| `extensions.worktreeConfig=true` e `.git/config.worktree` tem include/filter | **BLOQUEADO** | `git_unsafe_local_config` | **Não** |
| `.git/config.worktree` usa indireção | **BLOQUEADO** | `git_unsafe_local_config` | **Não** |
| Raiz declarada não resolvível | **BLOQUEADO** | `git_declared_root_invalid` | **Não** |

## Critérios de Aceitação

- **AC-01**: Com `git.required = false`, `git_unavailable` resulta em **AVISO** (status `AVISO`, exit_code 0 ou 1) em `doctor`, `worktree` e `preflight`.
- **AC-02**: Com `git.required = false`, `git_repository_missing` resulta em **AVISO** nos três comandos.
- **AC-03**: Com `git.required = false`, erros operacionais (`git_operational_error`, `git_permission_denied`, `git_dubious_ownership`, `git_unexpected_output`) resultam em **AVISO** nos três comandos.
- **AC-04**: Com `git.required = true`, os mesmos códigos acima resultam em **ERRO** ou **BLOQUEADO** (conforme código).
- **AC-05**: `git_root_mismatch` **sempre** resulta em **BLOQUEADO**, independente de `git.required`.
- **AC-06**: `git_indirect_repository_unsupported` **sempre** resulta em **BLOQUEADO**.
- **AC-07**: `git_unsafe_local_config` (include, includeIf, filter em `.git/config`) **sempre** resulta em **BLOQUEADO**.
- **AC-08**: Quando `extensions.worktreeConfig = true`, `.git/config.worktree` é validado **antes** de qualquer comando Git; include/includeIf/filter nele **sempre** resulta em **BLOQUEADO**.
- **AC-09**: Configuração worktree segura (`[core] autocrlf = false`) **não** gera falso positivo; inspeção prossegue normalmente.
- **AC-10**: Filtros `clean`/`process` definidos em `.git/config` e referenciados em `.gitattributes` **não são executados** durante inspeção; inspeção detecta a configuração e bloqueia com `git_unsafe_local_config`.
- **AC-11**: Quando `git.required = false` e ocorre **exclusivamente** um dos estados opcionais do Git (`git_unavailable`, `git_repository_missing`, `git_operational_error`, `git_permission_denied`, `git_dubious_ownership`, `git_unexpected_output`) — sem qualquer outra falha independente —, `doctor`, `worktree` e `preflight` devem permanecer não bloqueantes e o resultado agregado deve possuir `exit_code = 0`. Outras falhas independentes (ex.: configuração de projeto inválida, marcadores de raiz ausentes) podem produzir código de saída diferente de zero, mas a falha opcional do Git isoladamente nunca causa isso.

## Plano de Testes

| Critério | Tipo de Teste | Arquivo | Nome do Teste | O que o Teste Comprova |
|----------|---------------|---------|---------------|------------------------|
| AC-01 | Unitário (mock) | tests/test_preflight.py | test_optional_unavailable_git_is_warning_for_all_commands | Git indisponível vira AVISO em doctor/worktree/preflight quando required=false |
| AC-02 | Integração | tests/test_preflight.py | test_optional_git_outside_repository_is_warning | Fora de repo Git vira AVISO nos três comandos quando required=false |
| AC-03 | Unitário (mock) | tests/test_preflight.py | test_optional_git_doctor_error_does_not_leave_preflight_at_exit_one | Erro opcional no doctor não faz preflight falhar |
| AC-04 | Unitário (mock) | tests/test_preflight.py | test_required_unavailable_git_remains_blocking | Com required=true, erros continuam bloqueantes |
| AC-05 | Integração | tests/test_git_security.py | test_root_mismatch_stops_before_status | Root mismatch bloqueia antes de rodar status |
| AC-05 | Integração | tests/test_git_security.py | test_external_core_worktree_is_blocked | core.worktree externo causa root mismatch |
| AC-06 | Integração | tests/test_git_security.py | test_git_file_redirected_to_external_repository_is_blocked | .git arquivo gitdir: bloqueado |
| AC-06 | Integração | tests/test_git_security.py | test_git_directory_junction_or_symlink_is_blocked | Symlink/junction em .git bloqueado |
| AC-07 | Integração | tests/test_git_security.py | test_local_config_include_is_not_loaded | include.path em .git/config bloqueado |
| AC-08 | Integração | tests/test_git_security.py | test_worktree_config_include_path_is_not_loaded | include.path em config.worktree bloqueado (antes de rodar Git) |
| AC-08 | Integração | tests/test_git_security.py | test_worktree_config_include_if_is_not_loaded | includeIf em config.worktree bloqueado |
| AC-08 | Integração | tests/test_git_security.py | test_worktree_config_filter_is_not_loaded | filter em config.worktree bloqueado |
| AC-08 | Integração (segurança) | tests/test_git_security.py | test_clean_and_process_filters_are_not_executed | Filtros clean/process não executados; config detectada e bloqueada |
| AC-09 | Integração | tests/test_git_security.py | test_safe_worktree_config_has_no_false_positive | Config worktree segura passa sem erro |
| AC-10 | Integração (segurança) | tests/test_git_security.py | test_clean_and_process_filters_are_not_executed | Filtros não executados; inspeção bloqueia por config insegura |
|| AC-11 | Integração | tests/test_preflight.py | test_optional_git_doctor_error_does_not_leave_preflight_at_exit_one | Preflight exit_code 0 quando falha opcional do Git é a única ocorrência |

## Arquivos Provavelmente Afetados

- `src/hermes_ops/git/inspector.py` — lógica central de inspeção, validação de config, constante `OPTIONAL_GIT_WARNING_CODES`.
- `src/hermes_ops/commands/doctor.py` — uso da constante para classificar status.
- `src/hermes_ops/commands/worktree.py` — uso da constante; ajuste em Git indisponível e repo missing.
- `src/hermes_ops/commands/preflight.py` — uso da constante para rebaixar resultados do worktree.
- `tests/test_git_security.py` — testes de validação de config worktree, bloqueio antes de Git, segurança de filtros.
- `tests/test_preflight.py` — testes de comportamento opcional vs obrigatório, exit_code do preflight.

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| 2026-07-30 | `OPTIONAL_GIT_WARNING_CODES` como frozenset no módulo inspector | Centraliza a definição; evita divergência entre comandos | Duplicar o conjunto em cada comando |
| 2026-07-30 | Classificação centralizada em `OPTIONAL_GIT_WARNING_CODES` importada por `doctor.py`, `worktree.py` e `preflight.py` | Evita conjuntos literais contraditórios entre comandos; a constante única é a fonte da verdade; evidência: inspeção do código do commit 25cfc73; não há teste automatizado específico para essa decisão estrutural — os testes comportamentais dos AC-01 a AC-11 validam os efeitos públicos dessa decisão | Definir o conjunto separadamente em cada comando |
| 2026-07-30 | Validar `.git/config.worktree` apenas se `extensions.worktreeConfig=true` | O Git só lê esse arquivo quando a opção está ligada; validar sempre seria falso positivo | Validar sempre que o arquivo existisse |
| 2026-07-30 | Bloquear `includeIf` (case-insensitive) além de `include` | `includeIf` é seção válida do Git para includes condicionais | Ignorar `includeIf` |
| 2026-07-30 | `_worktree_config_enabled` lê texto bruto do `.git/config` (não via Git) | Precisa saber se a opção está ligada **antes** de rodar Git; usar `git config` criaria dependência circular | Usar `git config --get extensions.worktreeConfig` |
| 2026-07-30 | `git_repository_missing` entra em `OPTIONAL_GIT_WARNING_CODES` | Estar fora de repo é falha operacional Git, não de segurança | Manter apenas `git_unavailable` como opcional |
| 2026-07-30 | `preflight` rebaixar resultados do `worktree` pós-fato | `preflight` compõe `doctor` + `worktree`; não re-inspeciona Git | Re-inspecionar Git no preflight |

## Alternativas Descartadas

1. **Validar config.worktree via `git config --file`**: Exigiria Git funcionando; violaria a regra "validar antes de rodar Git".
2. **Não validar config.worktree**: Deixaria vetor de ataque aberto quando `extensions.worktreeConfig=true`.
3. **Rebaixar todos os erros Git quando `required=false`**: Incluiria `git_root_mismatch` e `git_unsafe_local_config`, o que comprometeria integridade e segurança.
4. **Criar nova constante por comando**: Aumentaria superfície de divergência; constante única é fonte da verdade.
5. **Usar `git config --includes` para detectar includes**: Executaria o Git; perigoso se o include apontar para script malicioso.

## Riscos Restantes

- **Regex de seções** pode não capturar casos exóticos (ex.: `[include "foo"]` com aspas). O padrão atual `^\s*\[\s*([A-Za-z][A-Za-z0-9.-]*)` cobre o formato canônico do Git.
- **Symlinks/junctions no Windows** podem não ser criados em CI; teste `test_git_directory_junction_or_symlink_is_blocked` pode ser skipped.
- **Variáveis de ambiente `GIT_*`** herdadas são removidas, mas se o processo pai definir `GIT_CONFIG_GLOBAL` após nossa limpeza, não há proteção (não aplicável: ambiente é construído fresco a cada chamada).
- **Encoding de arquivos de config**: usa `utf-8` com `errors="replace"`; bytes inválidos são substituídos, o que pode mascarar seções malformadas. Aceitável pois Git também tolera.

## Evidências da Implementação

| Campo | Valor |
|-------|-------|
| Commit original | `25cfc737285d1f84e14c5f961494771ab659cf7b` |
| Commit de integração na main | `327b667` |
| PR | #1 |
| Data da integração | 2026-07-30 |
| Checks de CI | 8 aprovados |
| Testes direcionados | `pytest tests/test_git_security.py tests/test_preflight.py -v` → 30 passed |
| Suíte completa | `pytest` → 113 passed, 2 skipped (symlinks Windows), 3 errors (packaging - módulo `build` não instalado, não relacionado) |
| compileall | `python -m compileall src/hermes_ops` → OK (sem erros de sintaxe) |
| Empacotamento | `python -m build` → OK (wheel + sdist criados localmente) |
| git diff --check | Sem avisos |
| Plataformas validadas | Windows 10 (Python 3.13.13, venv `C:\Users\Danilo\Projeto\hermes-ops\.venv\Scripts\python.exe`) |
| Limitações do ambiente | Symlinks indisponíveis no Windows CI padrão; 2 testes skipped (`test_configuration_file_symlink_is_rejected`, `test_external_symlink_is_rejected`) |

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| 2026-07-30 | Danilo Fukuda | Criação da especificação baseada no commit 25cfc73 | Commit 25cfc73 |
| 2026-07-30 | Danilo Fukuda | Adição de AC-12 (constante compartilhada) e evidências de validação | Análise do diff |
| 2026-07-30 | Danilo Fukuda | Atualização de status para **Implementado** com registro de integração (PR #1, commit 327b667, 8 checks CI) | Integração na main |

---

**Substituída por:** (não aplicável — primeira especificação)
**Motivo:** N/A