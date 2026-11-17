+++
schema_version = 1
id = "HERMES-0034"
title = "Limite controlado do adapter analisador Codex CLI"
status = "Rascunho"
owners = ["Danilo"]
created = "2026-10-29"
updated = "2026-10-29"
supersedes = []
related = ["HERMES-0007", "HERMES-0010", "HERMES-0011", "HERMES-0016"]

[[acceptance_criteria]]
id = "AC-01"
test = "tests/test_codex_boundary.py::test_codex_capability_requires_explicit_configuration"
[[acceptance_criteria]]
id = "AC-02"
test = "tests/test_codex_boundary.py::test_missing_codex_configuration_fails_closed"
[[acceptance_criteria]]
id = "AC-03"
test = "tests/test_codex_boundary.py::test_supported_codex_version_is_validated"
[[acceptance_criteria]]
id = "AC-04"
test = "tests/test_codex_boundary.py::test_unsupported_codex_version_is_rejected"
[[acceptance_criteria]]
id = "AC-05"
test = "tests/test_codex_process_boundary.py::test_executor_uses_core_process_boundary"
[[acceptance_criteria]]
id = "AC-06"
test = "tests/test_codex_process_boundary.py::test_executor_has_no_direct_subprocess_run"
[[acceptance_criteria]]
id = "AC-07"
test = "tests/test_processes.py::test_stdin_bytes_are_forwarded_without_breaking_legacy_callers"
[[acceptance_criteria]]
id = "AC-08"
test = "tests/test_codex_boundary.py::test_executable_resolution_never_falls_back_to_arbitrary_path"
[[acceptance_criteria]]
id = "AC-09"
test = "tests/test_codex_boundary.py::test_codex_runs_in_neutral_isolated_cwd"
[[acceptance_criteria]]
id = "AC-10"
test = "tests/test_codex_boundary.py::test_target_path_is_not_used_as_codex_cwd"
[[acceptance_criteria]]
id = "AC-11"
test = "tests/test_codex_boundary.py::test_environment_is_allowlisted"
[[acceptance_criteria]]
id = "AC-12"
test = "tests/test_codex_boundary.py::test_credentials_never_enter_prompt_or_public_output"
[[acceptance_criteria]]
id = "AC-13"
test = "tests/test_codex_boundary.py::test_real_home_and_uncontrolled_config_are_blocked_by_default"
[[acceptance_criteria]]
id = "AC-14"
test = "tests/test_codex_boundary.py::test_read_only_sandbox_is_required_but_not_treated_as_complete_isolation"
[[acceptance_criteria]]
id = "AC-15"
test = "tests/test_codex_boundary.py::test_network_policy_is_explicit_and_fail_closed"
[[acceptance_criteria]]
id = "AC-16"
test = "tests/test_codex_process_boundary.py::test_timeout_returns_normalized_failure"
[[acceptance_criteria]]
id = "AC-17"
test = "tests/test_codex_process_boundary.py::test_timeout_terminates_process_tree_on_windows"
[[acceptance_criteria]]
id = "AC-18"
test = "tests/test_codex_output.py::test_stdout_and_stderr_limits_are_enforced"
[[acceptance_criteria]]
id = "AC-19"
test = "tests/test_codex_output.py::test_output_uses_deterministic_utf8_decoding"
[[acceptance_criteria]]
id = "AC-20"
test = "tests/test_codex_output.py::test_stderr_is_bounded_and_sanitized"
[[acceptance_criteria]]
id = "AC-21"
test = "tests/test_codex_output.py::test_nonzero_exit_is_a_controlled_failure"
[[acceptance_criteria]]
id = "AC-22"
test = "tests/test_codex_output.py::test_invalid_json_fails_closed"
[[acceptance_criteria]]
id = "AC-23"
test = "tests/test_codex_output.py::test_invalid_non_object_or_oversized_json_fails_closed"
[[acceptance_criteria]]
id = "AC-24"
test = "tests/test_codex_prompt.py::test_evidence_pack_is_marked_as_untrusted_data"
[[acceptance_criteria]]
id = "AC-25"
test = "tests/test_codex_prompt.py::test_prompt_injection_fixture_cannot_expand_authority"
[[acceptance_criteria]]
id = "AC-26"
test = "tests/test_codex_budget.py::test_codex_attempt_consumes_execution_context_before_process"
[[acceptance_criteria]]
id = "AC-27"
test = "tests/test_codex_budget.py::test_budget_failure_prevents_codex_process"
[[acceptance_criteria]]
id = "AC-28"
test = "tests/test_codex_cli.py::test_adapter_is_not_publicly_available_without_approved_capability"
[[acceptance_criteria]]
id = "AC-29"
test = "tests/test_codex_cli.py::test_dry_run_never_resolves_or_calls_codex"
[[acceptance_criteria]]
id = "AC-30"
test = "tests/test_codex_packaging.py::test_wheel_and_sdist_contain_only_approved_codex_surface"
[[acceptance_criteria]]
id = "AC-31"
test = "tests/test_codex_packaging.py::test_wheel_and_sdist_contain_no_secrets_or_runtime_artifacts"
[[acceptance_criteria]]
id = "AC-32"
test = "manual:external_network_boundary_parent_child_matrix"
justification = "Requer política Windows externa e probe autorizada; não é implementado nesta spec Draft."
[[acceptance_criteria]]
id = "AC-33"
test = "manual:external_network_boundary_provider_only_allowlist"
justification = "Requer validação de provider/broker e endpoints autorizados."
[[acceptance_criteria]]
id = "AC-34"
test = "manual:external_network_boundary_arbitrary_child_denial"
justification = "A matriz deve cobrir filhos arbitrários sem lista fixa de tools."
[[acceptance_criteria]]
id = "AC-35"
test = "manual:external_network_boundary_direct_connection_denial"
justification = "Proxy sem bloqueio de socket direto não satisfaz o contrato."
[[acceptance_criteria]]
id = "AC-36"
test = "manual:external_network_boundary_dns_ipv4_ipv6_matrix"
justification = "DNS, IPv4, IPv6, DoH e DoT exigem probe específica."
[[acceptance_criteria]]
id = "AC-37"
test = "manual:external_network_boundary_fail_closed_and_rollback"
justification = "Falha de filtro, broker ou política deve bloquear e permitir rollback determinístico."
[[acceptance_criteria]]
id = "AC-38"
test = "manual:external_network_boundary_identity_scope"
justification = "Requer comprovação de identidade de processo, executável e usuário dedicado."
[[acceptance_criteria]]
id = "AC-39"
test = "manual:external_network_boundary_admin_surface"
justification = "Privilégio administrativo, serviço e eventual driver precisam ser confirmados."
[[acceptance_criteria]]
id = "AC-40"
test = "manual:external_network_boundary_crash_behavior"
justification = "Crash do Hermes/Codex não pode reabrir a rede."
[[acceptance_criteria]]
id = "AC-41"
test = "manual:external_network_boundary_auditability"
justification = "Logs de allow/block e IDs de regras devem ser verificáveis sem secrets."
[[acceptance_criteria]]
id = "AC-42"
test = "manual:external_network_boundary_machine_impact"
justification = "A probe deve provar que aplicações normais do usuário não são bloqueadas."
[[acceptance_criteria]]
id = "AC-43"
test = "manual:external_network_boundary_candidate_architecture_review"
justification = "A combinação preferencial continua candidata até a prova Windows isolada."
+++

# HERMES-0034 — Limite controlado do adapter analisador Codex CLI

## Status

`Rascunho`.

Esta especificação autoriza o desenho de uma integração concreta e opcional com
Codex CLI, mas não autoriza ainda sua execução real, seu staging, seu commit ou
sua ativação como provider padrão.

## Resumo para o Responsável pelo Projeto

O Hermes poderá usar o Codex CLI como um analisador opcional de um `AnalysisRequest`
já preparado localmente. O Codex não poderá receber o projeto-alvo, procurar
arquivos por conta própria, herdar credenciais sem controle ou executar fora da
fronteira central de processos. A integração somente poderá ser habilitada após
validar a capacidade, a versão, o ambiente e todas as regras de segurança.

## Contexto

A HERMES-0010 define o contrato genérico e vendor-neutral de análise de um
Evidence Pack. Ela separa a coleta local da análise opcional, exige um
`AnalyzerAdapter` injetado, mantém ausência de provider por padrão e declara que
transporte, timeout, retry e credenciais pertencem a uma borda concreta futura.

A auditoria T2 encontrou uma implementação Codex fora do Git que introduz:

- `CodexAnalyzerAdapter`;
- `CodexExecutor`;
- seleção pública de `--adapter codex-cli`;
- execução direta de `subprocess.run`;
- uso do CWD da aplicação como CWD do processo externo;
- herança implícita do ambiente do processo;
- timeout e saída sem o contrato central de processos.

O repositório exige que subprocessos passem por `hermes_ops.core.processes`.
HERMES-0011 também define a execução externa como uma ação que deve poder ser
orçada, interrompida e representada por falha controlada.

## Problema Confirmado

A implementação concreta existente não possui autorização normativa suficiente e
não respeita o process boundary oficial. Em particular, `executors/codex.py`
chama `subprocess.run` diretamente, enquanto o contrato do repositório exige a
fronteira central.

Além disso, a implementação atual não prova que `--sandbox read-only` bloqueia
rede, tools, leitura do CWD, HOME, configuração ou caches. Uma instrução no prompt
não é um controle de segurança equivalente a uma restrição técnica do processo.

## Comportamento Atual

O comportamento observado fora do Git é:

1. A CLI aceita `evidence analyze --adapter codex-cli`.
2. O comando lê e valida o Evidence Pack e constrói um `AnalysisRequest`.
3. Em `dry-run`, nenhum adapter é chamado.
4. Fora de `dry-run`, `Path.cwd()` é entregue como diretório de trabalho do
   `CodexAnalyzerAdapter`.
5. O adapter cria um prompt com instruções Hermes e o JSON canônico do request.
6. O executor chama:

   ```text
   codex.cmd exec --sandbox read-only -
   ```

   com o prompt em stdin.
7. stdout é tratado como texto e interpretado como JSON.
8. A resposta é entregue ao validator de Analysis Response.
9. Timeout, falha de inicialização e encoding não possuem o mesmo contrato
   controlado de `core.processes`.

Esse comportamento é apenas uma descrição da implementação encontrada. Não é
comportamento aprovado nem autorização para commit.

## Comportamento Desejado

A integração deverá obedecer simultaneamente às regras abaixo:

- `codex-cli` será um adapter concreto opcional;
- nenhum provider será ativado por padrão;
- ausência ou inconsistência de configuração falhará fechado;
- a versão do Codex será validada contra uma faixa explicitamente suportada;
- o executável será resolvido por política explícita, nunca por confiança cega
  em qualquer item do `PATH`;
- todo processo passará por `hermes_ops.core.processes`;
- nenhum executor/provider chamará `subprocess.run` diretamente;
- o stdin será encaminhado pela API central, sem quebrar callers existentes;
- o target e qualquer repositório real nunca serão usados como CWD do Codex;
- o processo usará um CWD neutro e isolado;
- o ambiente será construído por allowlist;
- secrets não entrarão no prompt, logs, stdout, stderr, Evidence Pack ou
  mensagens públicas;
- `read-only` será obrigatório, mas não será tratado como prova suficiente de
  isolamento;
- a política de rede, HOME, configuração, caches e tools será explícita;
- timeout, encerramento da árvore de processos, stdout, stderr e encoding terão
  contratos determinísticos;
- a tentativa consumirá `ExecutionContext`/budget antes do efeito externo;
- `dry-run` nunca resolverá nem chamará o provider;
- a saída só será aceita após parsing e validação local completos.

## Fora do Escopo

- API direta OpenAI ou de qualquer outro provider;
- automação de login;
- descoberta automática de provider;
- provider padrão;
- execução de tools pelo modelo;
- escrita no target ou no repositório analisado;
- acesso livre ao filesystem do target;
- memória de conversa ou histórico persistente do provider;
- upload automático do Evidence Pack integral;
- alteração semântica do `AnalysisRequest` genérico da HERMES-0010;
- alteração do fluxo de coleta `mission-audit`;
- commit da implementação Codex atualmente fora do Git;
- validação real contra API ou serviço externo nesta etapa Draft.

## Entradas

A futura borda receberá somente os seguintes tipos de entrada:

### Capability configuration

Configuração fornecida pela aplicação hospedeira, validada antes da execução:

- capability explicitamente habilitada;
- adapter id exato `codex-cli`;
- executável autorizado e sua origem;
- faixa de versão suportada;
- política de rede;
- política de HOME/config/cache;
- allowlist de variáveis de ambiente;
- timeout e limites de stdout/stderr;
- custo de execução no budget;
- política de sandbox e tools.

A configuração não poderá conter segredo em campos públicos serializados, logs,
Evidence Pack ou AnalysisRequest.

A F3 implementa somente a modelagem e validação local desta capability. A
verificação runtime da versão do Codex, autenticação, HOME/config/cache, rede e
tools continuam bloqueantes e não são executadas nesta fase. A capability padrão
é deliberadamente não configurada; o adapter falha fechado sem uma capability
aprovada.

### Estado de implementação da F3

O `CodexAnalyzerAdapter` recebe `AnalysisRequest` como payload semântico e uma
`CodexCapability` separada como configuração operacional. Ele copia somente os
campos explicitamente validados para `CodexExecutionRequest`, sem derivar CWD de
`Path.cwd()` ou ambiente de `os.environ`. O adapter ainda não é conectado à CLI
pública nem a `commands/evidence.py`.

### Estado de implementação da F4

A F4 adiciona `CodexCapabilityConfig` e um resolver explícito que não consulta
`Path.cwd()`, `os.environ`, PATH ou HOME real. O resolver só produz
`CodexCapability` quando executável, diretórios, limites, contexto, autenticação,
versão atestada, allowlist de ambiente e políticas de rede/tools passam todos os
gates. Caso contrário retorna gaps estruturados sem valores sensíveis.

A verificação runtime da versão, autenticação efetiva, isolamento técnico de
HOME/config/cache, enforcement de rede e enforcement de tools permanecem gaps;
nenhuma probe externa é executada nesta fase.

### Veredito runtime F5 — Windows / Codex CLI 0.147.0

As probes F5 observaram o binário nativo autorizado:

```text
<CODEX_EXECUTABLE_PATH>
```

Os shims npm `codex` e `codex.cmd` não foram autorizados para execução pelo
Hermes Ops. A versão observada foi:

```text
codex-cli 0.147.0
```

A interface local comprovadamente expõe `exec`, stdin, JSON, sandbox, approval,
CWD, permission profile, `CODEX_HOME` e `--ignore-user-config`. Isso prova
compatibilidade de interface, não certificação de segurança.

A probe do permission profile `:read-only` comprovou, no scratch isolado:

```text
READ_PERMISSION=PROVEN
WRITE_DENIAL=PROVEN
READ_ONLY_FILESYSTEM_ENFORCEMENT=PROVEN
```

A probe de rede usou baseline TCP para `example.com:80` e a mesma operação com
`--sandbox-state-disable-network`:

```text
BASELINE_NETWORK_AVAILABLE=PROVEN
NETWORK_INTERFACE_ACCEPTED=true
SANDBOX_NETWORK_DENIAL=FAILED
network_policy_verified=false
```

A operação continuou conectando mesmo com a opção de disable-network. Portanto,
`provider-only` não significa `unrestricted network` e não pode ser marcado como
política verificada. O contrato exige provar que o Codex acessa somente o
provider necessário e que comandos/tools filhos não recebem rede irrestrita; o
segundo requisito falhou na F5-G.

A relocation de `CODEX_HOME` foi observada para as probes locais. Configuração e
cache foram apenas parcialmente observados; autenticação permanece não provada.
Tools, process tree e enforcement de rede continuam não comprovados ou falhos.

O veredito normativo da versão é:

```text
runtime_version_observed = "0.147.0"
runtime_version_interface_compatible = true
runtime_version_security_certified = false
version_validated = false
capability_ready = false
classification = "observed_but_not_certified"
```

Nenhuma faixa normativa de versões, como `>=0.147.0`, é definida por esta
alteração. `0.147.0` permanece candidata observada, não versão suportada
certificada.

Próximas alternativas ainda abertas:

- testar uma versão mais nova em isolamento separado;
- implementar um boundary externo de rede;
- tomar uma nova decisão humana explícita para relaxar HERMES-0034.

A terceira alternativa não está autorizada nesta fase.

### Veredito comparativo F5-J — Codex CLI 0.165.0 isolada

A runtime isolada `codex-cli 0.165.0` foi observada no binário nativo do
pacote instalado separadamente, sem alterar a instalação global `0.147.0`.

Os fatos comparáveis foram:

| Runtime | Baseline de rede | `--sandbox-state-disable-network` | Veredito |
|---|---|---|---|
| `0.147.0` | `CONNECTED` | `CONNECTED` | `SANDBOX_NETWORK_DENIAL=FAILED` |
| `0.165.0` | `CONNECTED` | `CONNECTED` | `SANDBOX_NETWORK_DENIAL=FAILED` |

Para ambas as runtimes:

```text
BASELINE_NETWORK_AVAILABLE=PROVEN
NETWORK_INTERFACE_ACCEPTED=true
network_policy_verified=false
```

A mudança de `0.147.0` para `0.165.0` não resolveu o network enforcement
Windows pela rota testada. A hipótese de que uma atualização de versão isolada
resolveria esse boundary fica rejeitada:

```text
NETWORK_ENFORCEMENT_VERSION_HYPOTHESIS=REJECTED
```

O filesystem read-only permanece comprovado nas duas runtimes:

```text
0.147.0: READ_ONLY_FILESYSTEM_ENFORCEMENT=PROVEN
0.165.0: READ_ONLY_FILESYSTEM_ENFORCEMENT=PROVEN
```

Portanto, o sandbox filesystem funciona nas duas versões testadas, mas o deny de
network não.

Os gates da capability permanecem:

```text
network_policy_verified=false
tools_policy_verified=false
version_validated=false
capability_ready=false
```

Nenhuma das versões está security-certified para uso real do adapter sob o
contrato atual.

A próxima direção preferencial é:

```text
EXTERNAL_NETWORK_BOUNDARY_REQUIRED_FOR_EVALUATION=true
```

Isso é uma direção de investigação, não autorização de implementação. Não
relaxa a exigência de que `provider-only` limite a rede ao provider necessário e
não concede rede irrestrita a comandos ou tools filhos.

### AnalysisRequest

O adapter receberá o `AnalysisRequest` imutável da HERMES-0010. Não receberá:

- target;
- project root;
- callback de leitura;
- `Path` para source code;
- credencial em texto;
- ambiente arbitrário;
- ferramenta ou comando escolhido pelo modelo.

### Execução central

A camada central receberá:

- sequência de argumentos já autorizada;
- CWD neutro validado;
- timeout positivo;
- stdin em bytes ou texto explicitamente codificado;
- ambiente allowlisted;
- limites de saída;
- contexto de execução e categoria orçada.

## Saídas

O executor produzirá um resultado controlado contendo, no mínimo:

- código de saída ou ausência de início;
- stdout limitado;
- stderr limitado e sanitizado;
- duração monotônica;
- estado de sucesso;
- estado de timeout;
- código de falha fechado;
- indicação de truncamento, se aplicável.

O adapter produzirá `RawAnalysisResponse` somente quando:

- o processo terminou com sucesso;
- stdout respeitou limites e encoding;
- stdout contém um objeto JSON;
- o objeto passou pela validação local da HERMES-0010.

Falha, timeout, saída inválida, saída excessiva ou violação de capability não
produzem resultado parcial.

## Invariantes e Regras de Segurança

### Autorização e default

1. `codex-cli` nunca é default.
2. Opt-in exige capability explicitamente aprovada e configurada.
3. Capability ausente, incompleta, ambígua ou incompatível falha fechado.
4. O adapter genérico da HERMES-0010 continua vendor-neutral.
5. A CLI não poderá aceitar um provider concreto antes da capability ser
   aprovada pela aplicação hospedeira.

### Versão e executável

6. A versão do Codex será obtida e validada pela fronteira central.
7. Versões fora da faixa suportada bloquearão antes do prompt.
8. O executável será um caminho ou resolução explicitamente autorizada.
9. Um `codex.cmd` arbitrário encontrado no `PATH` não será suficiente.
10. O caminho do executável não será aceito de Evidence Pack, prompt ou target.

### Process boundary

11. Todo processo externo passará por `hermes_ops.core.processes`.
12. Nenhum `subprocess.run` aparecerá em executor, adapter ou command provider.
13. `shell=False` será obrigatório.
14. A extensão de stdin manterá compatibilidade com callers que não fornecem
    stdin.
15. Falhas de cwd, executável, permissão, timeout e inicialização serão
    convertidas para o contrato central.

### CWD e filesystem

16. O target nunca será CWD do Codex.
17. O CWD será neutro, isolado e fora do target.
18. O CWD deverá ser validado antes da execução.
19. Um CWD ausente, indireto, não-diretório ou não-isolado bloqueará.
20. O prompt será a única fonte de conteúdo de análise autorizada.
21. O processo não poderá descobrir ou reler o target por caminho, CWD ou
    ferramenta.

### Ambiente, autenticação e secrets

22. O ambiente completo do processo pai nunca será herdado implicitamente.
23. Variáveis de ambiente usarão allowlist explícita.
24. Credenciais serão fornecidas somente pelo mecanismo de autenticação aprovado
    para o provider e nunca serão copiadas para `AnalysisRequest`.
25. Segredos não aparecerão em prompt, stdout, stderr, logs, exceções,
    `AnalysisResult`, Evidence Pack ou mensagens públicas.
26. HOME real, arquivos de configuração e caches reais serão bloqueados por
    padrão ou substituídos por localização isolada explicitamente aprovada.

### Sandbox, rede e tools

27. `read-only` será requisito obrigatório.
28. `read-only` não será considerado prova de ausência de rede, tools, leitura do
    CWD, HOME, configuração ou cache.
29. A política de rede será explícita e validada antes da execução.
30. Somente a rede necessária para inferência/autenticação, quando formalmente
    permitida, poderá ser usada.
31. Rede ampla, endpoints desconhecidos e fallback de rede bloquearão.
32. Tools não autorizadas serão bloqueadas tecnicamente, não apenas por texto
    no prompt.

### External Network Boundary

A sandbox interna do Codex não satisfaz, sozinha, `network_policy_verified` no
Windows observado. A capability só poderá ser liberada quando existir um
boundary externo que cumpra o contrato provider-only:

- o parent Codex acessa somente o provider ou broker autorizado;
- processos/tools filhos têm rede negada por default;
- a decisão considera identidade do processo, executável, usuário/contexto
  dedicado e identidade da conexão outbound;
- filhos arbitrários como `python.exe`, `powershell.exe`, `cmd.exe`, `curl.exe`
  e executáveis desconhecidos ou renomeados não recebem rede por default;
- uma lista fixa de nomes de tools não é suficiente;
- conexão TCP/UDP direta de filhos permanece bloqueada;
- proxy por variável de ambiente, sem bloqueio de socket direto, não satisfaz o
  contrato;
- quando houver proxy/broker, o parent poderá acessá-lo, mas filhos não terão
  acesso livre ao broker nem fallback direto;
- allowlist do provider deve cobrir DNS, IPv4 e IPv6; DoH/DoT e qualquer outra
  resolução devem possuir política explícita para impedir leakage;
- falha de firewall/WFP, broker, DNS policy, filtro incompleto, regra ambígua,
  bypass de proxy ou mismatch de executável/versão bloqueia a capability.

A arquitetura candidata preferencial é:

```text
dedicated identity/context
    + WFP/ALE ou Windows Firewall escopado
    + proxy/broker obrigatório
    + direct-connect deny
```

A instalação deve usar IDs determinísticos de filtros/regras, rollback específico
sem reset global de firewall e comportamento fail-closed após crash do Hermes,
Codex ou broker. Privilégios administrativos e eventual serviço privilegiado
podem ser necessários; driver customizado não deve ser exigido sem prova de
necessidade.

A existência de uma interface de rede ou de um parâmetro de sandbox não prova o
enforcement. A HERMES-0034 exige uma probe futura com baseline sem policy,
parent autorizado, filho bloqueado, bypass direto bloqueado, broker/provider
permitido, IPv4, IPv6, DNS, crash e rollback. Até essa prova, classificar:

```text
EXTERNAL_NETWORK_BOUNDARY=CANDIDATE_ARCHITECTURE
network_policy_verified=false
capability_ready=false
```

A F6-A concluiu `INSUFFICIENT_EVIDENCE`; nenhuma implementação Windows é
autorizada por esta seção.

### Timeout e árvore de processos

33. Timeout positivo será obrigatório.
34. Timeout será normalizado como erro de domínio do adapter.
35. O processo principal e os filhos iniciados por ele deverão ser encerrados
    conforme política compatível com Windows.
36. Após timeout, nenhum resultado parcial será aceito.
37. Falha no encerramento da árvore será observável e bloqueará o resultado.

### Output e parsing

38. stdout e stderr terão limites de bytes explícitos.

    A baseline inicial da capability usa `max_stdout_bytes = 1_048_576`
    (1 MiB) e `max_stderr_bytes = 262_144` (256 KiB). O limite é medido
    sobre bytes capturados antes do decoding. Saída exatamente no limite é
    aceita; saída acima do limite falha fechado, limpa as streams públicas e
    marca independentemente `stdout_limit_exceeded` e
    `stderr_limit_exceeded`.

39. stdout será decodificado com encoding determinístico, preferencialmente
    UTF-8 estrito para JSON.
40. Bytes inválidos bloquearão a resposta; fallback de locale não poderá alterar
    silenciosamente o JSON analisado.
41. stderr será limitado, sanitizado e nunca retornará secrets.
42. Exit code diferente de zero será falha controlada.
43. JSON inválido, não-objeto, incompleto ou acima do limite falhará fechado.
44. A resposta só será aceita após a validação completa da HERMES-0010.

### Prompt e evidência

45. O Evidence Pack e seus excerpts serão rotulados como dados não confiáveis.
46. Instruções encontradas em excerpts nunca ganharão autoridade.
47. A proteção contra prompt injection será complementar, nunca substituta dos
    controles de CWD, tools, rede, env e sandbox.
48. O prompt não poderá pedir ao provider para ler arquivos, escolher comandos,
    buscar contexto externo ou executar ferramentas.

### Budget

49. Cada tentativa Codex consumirá `ExecutionContext` antes do subprocesso.
50. A decisão deverá usar categoria explícita e custo explícito.
51. Budget insuficiente bloqueará antes do processo.
52. Timeout, falha, exit code não-zero e executável ausente não desfazem o
    consumo da tentativa.
53. O custo não será inferido de tokens reais do provider.

### Packaging

54. Wheel e sdist conterão somente a superfície Codex aprovada pela spec.
55. Nenhum segredo, cache, banco, log, arquivo temporário ou artefato local será
    empacotado.
56. O packaging será validado fora do checkout e em ambiente isolado.

## Pseudocódigo

### Habilitar a capability

```text
FUNÇÃO VALIDAR_CAPABILITY(configuração):
    SE adapter_id != "codex-cli":
        REJEITAR com CODEX_ADAPTER_UNAVAILABLE

    VALIDAR que a capability foi explicitamente aprovada
    VALIDAR executável autorizado
    VALIDAR versão suportada
    VALIDAR política de rede, tools, HOME e cache
    VALIDAR allowlist de ambiente
    VALIDAR timeout, limites de stdout/stderr e custo positivo

    SE qualquer validação falhar:
        NÃO iniciar processo
        RETORNAR erro fechado

    RETORNAR capability imutável
```

### Executar a análise

```text
FUNÇÃO ANALISAR_COM_CODEX(analysis_request, capability, execution_context):
    VALIDAR capability
    VALIDAR tipo e schema de analysis_request

    decisão = execution_context.can_start(VALIDATION, capability.cost)
    SE decisão for impeditiva:
        RETORNAR CODEX_BUDGET_BLOCKED

    contexto_seguinte = execution_context.consume(VALIDATION, capability.cost)

    prompt = SERIALIZAR_REQUEST_COM_DELIMITADORES(analysis_request)
    MARCAR excerpts como dados não confiáveis
    NÃO incluir credenciais nem paths do target

    cwd = CRIAR_OU_OBTER_CWD_NEUTRO_ISOLADO()
    SE cwd não for isolado ou não for diretório regular:
        RETORNAR CODEX_CWD_INVALID

    env = CONSTRUIR_ENV_ALLOWLIST(capability)
    args = RESOLVER_EXECUTÁVEL_E_ARGUMENTOS_AUTORIZADOS(capability)

    resultado = core.processes.run_process(
        args,
        cwd=cwd,
        timeout=capability.timeout,
        input_bytes=UTF8(prompt),
        env=env,
        output_limits=capability.output_limits,
    )

    SE resultado indicar timeout:
        ENCERRAR E VALIDAR A ÁRVORE DE PROCESSOS
        RETORNAR CODEX_TIMEOUT

    SE resultado indicar falha de inicialização ou exit code não-zero:
        RETORNAR CODEX_PROCESS_FAILED

    SE stdout excedeu limite ou não é UTF-8 válido:
        RETORNAR CODEX_OUTPUT_INVALID

    resposta = PARSEAR_JSON(stdout)
    VALIDAR que resposta é objeto
    VALIDAR resposta com validator da HERMES-0010

    SE qualquer validação falhar:
        RETORNAR CODEX_RESPONSE_INVALID

    RETORNAR resposta validada e contexto_seguinte
```

## Fluxo Principal

1. A aplicação hospedeira solicita a capability `codex-cli` por opt-in explícito.
2. A configuração é validada sem ler ou imprimir secrets.
3. O executável e sua versão são validados.
4. A política de rede, tools, HOME, configuração, cache e ambiente é fixada.
5. O Evidence Pack é carregado e reduzido localmente pela HERMES-0010.
6. O `AnalysisRequest` é validado antes de qualquer processo externo.
7. O budget é consultado e consumido antes da tentativa.
8. O prompt é criado a partir somente do request validado.
9. O processo é executado pela fronteira central, em CWD neutro.
10. Timeout, árvore de processos, stdout e stderr são tratados pelo contrato.
11. A resposta é parseada e validada localmente.
12. Somente a resposta validada é exposta como resultado.
13. Falha em qualquer gate impede resultado parcial ou fallback para o pack
    integral.

## Casos de Erro e Limites

| Situação | Comportamento | Código |
|---|---|---|
| Capability ausente | Bloqueia sem iniciar provider | `CODEX_ADAPTER_UNAVAILABLE` |
| Provider diferente de `codex-cli` | Rejeita | `CODEX_ADAPTER_UNSUPPORTED` |
| Configuração incompleta | Falha fechado | `CODEX_CONFIGURATION_INVALID` |
| Versão fora da faixa | Bloqueia | `CODEX_VERSION_UNSUPPORTED` |
| Executável não autorizado | Bloqueia | `CODEX_EXECUTABLE_UNAUTHORIZED` |
| Executável ausente | Resultado controlado | `CODEX_EXECUTABLE_NOT_FOUND` |
| CWD não isolado | Bloqueia | `CODEX_CWD_INVALID` |
| Ambiente fora da allowlist | Bloqueia | `CODEX_ENV_INVALID` |
| Rede fora da política | Bloqueia | `CODEX_NETWORK_POLICY_INVALID` |
| Tools não controláveis | Bloqueia | `CODEX_TOOLS_UNCONTROLLED` |
| Budget insuficiente | Não inicia processo | `CODEX_BUDGET_BLOCKED` |
| Timeout | Encerra árvore e falha | `CODEX_TIMEOUT` |
| Árvore não encerrada | Falha sem resultado | `CODEX_PROCESS_TREE_UNCONTROLLED` |
| Exit code diferente de zero | Falha controlada | `CODEX_PROCESS_FAILED` |
| stdout acima do limite | Falha fechado | `CODEX_OUTPUT_LIMIT_EXCEEDED` |
| stderr acima do limite | Falha fechado | `CODEX_OUTPUT_LIMIT_EXCEEDED` |
| Encoding inválido | Falha fechado | `CODEX_OUTPUT_ENCODING_INVALID` |
| JSON inválido | Falha fechado | `CODEX_RESPONSE_INVALID` |
| JSON não-objeto | Falha fechado | `CODEX_RESPONSE_INVALID` |
| Claim inválida | Validator rejeita resposta inteira | `ANALYSIS_RESPONSE_INVALID` |
| Secret detectado em output | Redige e falha fechado | `CODEX_SENSITIVE_OUTPUT` |

Nenhum caso de erro poderá fazer fallback para execução livre, leitura do target,
provider alternativo ou envio do Evidence Pack integral.

## Critérios de Aceitação

- **AC-01:** `codex-cli` é reconhecido somente como capability explicitamente
  aprovada.
- **AC-02:** ausência de configuração falha fechado e não inicia processo.
- **AC-03:** provider nunca é default.
- **AC-04:** versão fora da faixa aprovada é rejeitada.
- **AC-05:** resolução arbitrária de `codex.cmd` pelo PATH é rejeitada.
- **AC-06:** todo processo é iniciado por `hermes_ops.core.processes`.
- **AC-07:** nenhum executor/provider contém chamada direta a `subprocess.run`.
- **AC-08:** stdin pode ser encaminhado pela API central sem quebrar callers
  existentes.
- **AC-09:** o target nunca é usado como CWD.
- **AC-10:** CWD neutro e isolado é obrigatório.
- **AC-11:** ambiente é allowlisted e não herda o ambiente completo.
- **AC-12:** credenciais nunca aparecem no request, prompt, logs ou output.
- **AC-13:** HOME, config e cache reais são bloqueados ou isolados conforme
  capability aprovada.
- **AC-14:** `read-only` é obrigatório, mas gates independentes de rede, tools,
  CWD, HOME e cache também são aplicados.
- **AC-15:** política de rede ausente ou ambígua bloqueia.
- **AC-16:** timeout é obrigatório e retorna erro normalizado.
- **AC-17:** timeout encerra e verifica a árvore de processos no Windows.
- **AC-18:** stdout e stderr possuem limites de bytes.
- **AC-19:** decoding de stdout é determinístico.
- **AC-20:** stderr é limitado e sanitizado.
- **AC-21:** exit code não-zero não produz resultado parcial.
- **AC-22:** JSON inválido, não-objeto ou excedente falha fechado.
- **AC-23:** prompt injection em fixture não aumenta a autoridade do modelo.
- **AC-24:** Evidence Pack permanece dado não confiável, não instrução.
- **AC-25:** budget é consultado e consumido antes do processo.
- **AC-26:** bloqueio de budget impede qualquer processo externo.
- **AC-27:** dry-run nunca resolve, instancia ou chama Codex.
- **AC-28:** `--adapter codex-cli` só aparece quando a capability está aprovada.
- **AC-29:** packaging inclui somente módulos autorizados e nenhum artefato
  runtime.
- **AC-30:** wheel e sdist reproduzem a superfície aprovada em ambiente isolado.
- **AC-31:** resposta Codex só é exposta após a validação HERMES-0010.
- **AC-32:** a capability exige um boundary externo de rede provider-only e não
  libera o Codex com a sandbox interna isoladamente.
- **AC-33:** o parent pode acessar somente provider/broker autorizado; filhos
  permanecem deny-by-default.
- **AC-34:** filhos arbitrários não recebem rede por listas parciais de nomes.
- **AC-35:** conexão direta de filhos é bloqueada; proxy por env sozinho é
  insuficiente.
- **AC-36:** DNS, IPv4, IPv6, DoH e DoT possuem política explícita sem leakage.
- **AC-37:** falha de filtro, broker, DNS, regra ambígua ou bypass bloqueia e
  permite rollback determinístico.
- **AC-38:** a política diferencia identidade de processo, executável, usuário e
  conexão outbound.
- **AC-39:** privilégios administrativos e componentes Windows necessários são
  explicitamente documentados antes da implementação.
- **AC-40:** crash do Hermes, Codex ou broker não reabre a rede.
- **AC-41:** filtros/regras possuem IDs e evidência auditável sem secrets.
- **AC-42:** a probe cobre baseline, parent, filho, bypass, broker/provider,
  IPv4, IPv6, DNS, crash e rollback.
- **AC-43:** a arquitetura permanece `CANDIDATE_ARCHITECTURE` até prova Windows
  isolada; não é classificada como `PROVEN` ou `FEASIBLE` nesta fase.

## Plano de Testes

### Testes unitários do boundary central

- stdin bytes/texto com caller legado sem stdin;
- shell false;
- cwd inválido, ausente, arquivo e caminho indireto;
- timeout e saída controlada;
- stdout/stderr separados e limitados;
- encoding UTF-8 inválido;
- erro de executável e permissão.

### Testes do executor

- spy em `hermes_ops.core.processes.run_process` confirma delegação;
- scanner/AST falha se `subprocess.run` aparecer em executor/provider;
- argumentos exatos e executável autorizado;
- env allowlist;
- cwd neutro;
- timeout e encerramento da árvore no Windows;
- exit code, stderr e output excessivo.

### Testes de segurança

- prompt injection em excerpt não concede tool, rede ou filesystem;
- path do target não aparece como cwd;
- secrets não aparecem no prompt, logs ou output;
- HOME/config/cache reais não são usados sem capability explícita;
- ausência de capability e configuração parcial falham fechado;
- política de rede ausente ou fora da allowlist bloqueia.

### Testes de adapter e resposta

- request somente `AnalysisRequest`;
- dry-run sem resolução de adapter;
- JSON válido e validado;
- JSON inválido, não-objeto e acima do limite;
- claims com ID inexistente;
- classificação não suportada;
- limitações e evidências contrárias preservadas.

### Testes de CLI

- provider não aparece sem capability aprovada;
- `--adapter codex-cli` exige configuração completa;
- ausência de adapter continua `ANALYSIS_ADAPTER_UNAVAILABLE`;
- flags de target continuam proibidas na etapa de análise;
- saída pública não expõe paths absolutos, secrets ou stderr bruto.

### Testes de packaging

- wheel/sdist incluem a superfície aprovada;
- nenhum secret, cache, banco, log ou artefato temporário entra no pacote;
- instalação isolada resolve somente o catálogo e módulos autorizados;
- provider não é ativado por import ou instalação.

Cada teste de segurança deverá conter comportamento permitido, comportamento
bloqueado e regressão correspondente.

## Arquivos Provavelmente Afetados

- `docs/hermes/specs/HERMES-0034-codex-cli-analyzer-boundary.md`
- `src/hermes_ops/core/processes.py`
- `src/hermes_ops/core/errors.py`
- `src/hermes_ops/executors/codex.py`
- `src/hermes_ops/executors/models.py`
- `src/hermes_ops/analysis/codex_adapter.py`
- `src/hermes_ops/commands/evidence.py`
- `src/hermes_ops/cli.py`
- `tests/test_processes.py`
- `tests/test_budgeted_process.py`
- `tests/test_codex_process_boundary.py`
- `tests/test_codex_boundary.py`
- `tests/test_codex_output.py`
- `tests/test_codex_prompt.py`
- `tests/test_codex_budget.py`
- `tests/test_codex_cli.py`
- `tests/test_codex_packaging.py`
- `pyproject.toml` ou `MANIFEST.in`, somente se o packaging exigir ajuste

A implementação atual Codex não será automaticamente incorporada ao futuro
commit. Ela deverá ser reavaliada contra esta spec após a correção arquitetural.

## Decisões Tomadas

| Decisão | Justificativa | Alternativa descartada |
|---|---|---|
| Criar spec dedicada em vez de alterar HERMES-0010 | HERMES-0010 é deliberadamente vendor-neutral e não autoriza provider concreto | Reescrever a 0010 para absorver detalhes Codex |
| Codex é opt-in e nunca default | Evita mudança silenciosa de transporte, custo e superfície de dados | Seleção automática por disponibilidade no PATH |
| Todo processo passa por `core.processes` | É o boundary oficial do repositório e concentra timeout/cwd/encoding/erros | `subprocess.run` local em executor |
| stdin entra pela API central | O provider precisa receber prompt sem quebrar callers legados | Capturar stdin diretamente no executor |
| target nunca é cwd | O AnalysisRequest é a única entrada autorizada da análise | Reutilizar `Path.cwd()` ou project root |
| `read-only` não basta | Sandbox textual não prova rede, tools, HOME, cache ou leitura do cwd | Tratar `--sandbox read-only` como isolamento completo |
| Budget é obrigatório | Codex é efeito externo custoso e deve obedecer HERMES-0011 | Executar fora de `ExecutionContext` |
| Falha é fechada | Provider não pode compensar falta de evidência com leitura adicional | Fallback para pack integral ou target |

## Alternativas Descartadas

### Provider default quando `codex.cmd` existe

Rejeitada: disponibilidade no PATH não é autorização, versão nem configuração
segura.

### Passar o target como CWD em modo read-only

Rejeitada: read-only não prova ausência de leitura, tools ou rede; também viola o
isolamento definido pela HERMES-0010.

### Confiar somente em instruções do prompt

Rejeitada: texto não é uma boundary de segurança. O processo precisa de gates
técnicos de CWD, env, tools, rede e sandbox.

### Chamar `subprocess.run` diretamente no executor

Rejeitada: viola `AGENTS.md`, HERMES-0007 e HERMES-0011.

### Herdar o ambiente completo

Rejeitada: pode transportar credenciais, configuração e endpoints não
autorizados.

### Fazer fallback para outro provider

Rejeitada: esconderia ausência de capability e quebraria rastreabilidade.

## Riscos Restantes

1. A semântica exata de `codex.cmd --sandbox read-only` ainda precisa ser
   confirmada para a faixa de versões aprovada.
2. A política de rede pode exigir configuração do host e não ser expressável
   apenas por argumentos do Codex.
3. Encerramento de árvore de processos precisa de validação específica do
   Windows.
4. A autenticação concreta ainda não foi definida.
5. Limites de output podem precisar de suporte novo em `core.processes`.
6. A capacidade de manter o provider fora do target depende de CWD, HOME,
   config, cache e tools serem isolados conjuntamente.
7. Nenhuma implementação ou teste desta spec foi executado; o status continua
   `Rascunho`.

## Evidências da Implementação

Esta seção registra somente a base factual usada para desenhar a spec; não é
certificação de implementação.

| Evidência | Resultado |
|---|---|
| HERMES-0010 | Draft, provider-neutral, sem autorização de chamada real |
| HERMES-0007 | subprocessos devem passar pela fronteira central |
| HERMES-0011 | `core.processes.run_process` é a única borda de subprocesso de produção |
| T2 read-only | executor Codex atual usa `subprocess.run` diretamente |
| T2 read-only | executor atual passa CWD e ambiente de forma não isolada |
| HEAD | `4fda64b86d6a90d13d4ba1923cb51fbc60f54e2c` |
| Estado Git | implementação Codex permanece unstaged/untracked |

Não há commit de implementação, teste de integração real ou validação de
provider nesta spec Draft.

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|---|---|---|---|
| 2026-10-29 | Hermes | Criação da proposta Draft para formalizar a capability Codex CLI | Auditoria T2 read-only |
