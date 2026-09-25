+++
schema_version = 1
id = "HERMES-0002"
status = "Aprovado"
[[acceptance_criteria]]
id = "AC-01"
[[acceptance_criteria]]
id = "AC-02"
[[acceptance_criteria]]
id = "AC-03"
[[acceptance_criteria]]
id = "AC-04"
[[acceptance_criteria]]
id = "AC-05"
[[acceptance_criteria]]
id = "AC-06"
[[acceptance_criteria]]
id = "AC-07"
[[acceptance_criteria]]
id = "AC-08"
[[acceptance_criteria]]
id = "AC-09"
[[acceptance_criteria]]
id = "AC-10"
[[acceptance_criteria]]
id = "AC-11"
justification = "Aprovação formal — a especificação passou por auditoria estrutural e semântica completa, com pseudocódigo abrangente, 20 critérios de aceitação testáveis e independentes, e plano de testes detalhado com rastreabilidade AC↔teste. Validação manual de conformidade com TEMPLATE e AGENTS.md registrada no Histórico de Alterações."
[[acceptance_criteria]]
id = "AC-12"
[[acceptance_criteria]]
id = "AC-13"
[[acceptance_criteria]]
id = "AC-14"
[[acceptance_criteria]]
id = "AC-15"
[[acceptance_criteria]]
id = "AC-16"
[[acceptance_criteria]]
id = "AC-17"
[[acceptance_criteria]]
id = "AC-18"
[[acceptance_criteria]]
id = "AC-19"
[[acceptance_criteria]]
id = "AC-20"
+++

# HERMES-0002 — Validação Automática de Especificações (spec-check)

## Status
Rascunho | Aprovado | Em implementação | Implementado | Substituído

## Resumo para o Responsável pelo Projeto

Esta especificação introduz o comando `spec-check` para validação **somente leitura** das especificações versionadas em `docs/hermes/specs/`. O comando verifica: convenção de nomes (padrão HERMES-NNNN), presença e completude de todas as seções obrigatórias do TEMPLATE, valores válidos para Status, critérios de aceitação (AC-NN) bem formados, vínculos com testes, evidências de implementação e caminhos seguros. A saída é determinística nos formatos **texto** e **JSON**, sem traceback em nenhum cenário. O comando **não modifica** arquivos — apenas reporta conformidade e desvios.

## Contexto

O repositório `hermes-ops` adota especificações versionadas obrigatórias para alterações funcionais não triviais (conforme AGENTS.md). Hoje não existe validação automatizada: revisores precisam checar manualmente se cada especificação segue o TEMPLATE, se os ACs têm testes vinculados, se o Status está correto, se os nomes seguem HERMES-NNNN. Isso gera inconsistências, esquecimentos e retrabalho em PRs.

O comando `spec-check` será adicionado ao CLI `hermes-ops` junto a `doctor`, `worktree` e `preflight`, reutilizando a infraestrutura de `Report`, `CheckResult`, `Status`, `PublicSanitizer` e saídas texto/JSON já existentes.

## Problema Confirmado

1. **Ausência de validação automatizada**: Especificações podem ser criadas/alteradas sem seguir o TEMPLATE, com seções faltando, ACs mal formados, Status inválido, sem vínculos a testes.
2. **Nomes fora de padrão**: Arquivos podem não seguir `HERMES-NNNN-descrição.md`, dificultando rastreabilidade e ordenação.
3. **Status inconsistentes**: Valores livres em vez dos 5 estados permitidos.
4. **Critérios de aceitação sem padrão**: ACs sem numeração sequencial, sem descrição verificável, sem referência a testes.
5. **Vínculos com testes não verificados**: Não há checagem de que cada AC possui teste correspondente com marcador `Spec: HERMES-XXXX / AC-YY`.
6. **Evidências incompletas**: Seção de evidências pode estar vazia ou faltando campos obrigatórios (commit, testes, suite, compileall, build, git diff --check, plataformas).
7. **Caminhos inseguros**: Especificações podem referenciar caminhos absolutos ou fora do projeto.
8. **Saída não determinística**: Não há comando que produza relatório padronizado texto/JSON para CI.

## Comportamento Atual

- Não existe comando `spec-check`.
- Validação é 100% manual durante code review.
- Não há verificação de nomenclatura, seções, status, ACs, testes, evidências ou caminhos.
- CLI atual: `doctor`, `worktree`, `preflight` (ver `src/hermes_ops/cli.py`).
- Infraestrutura de resultados: `Report`, `CheckResult`, `Status` (OK, AVISO, BLOQUEADO, ERRO), `PublicSanitizer` (ver `src/hermes_ops/core/results.py`).

## Comportamento Desejado

Novo comando `spec-check` com:

**Entradas:**
- `--project` (obrigatório): raiz do projeto contendo `docs/hermes/specs/`.
- `--format` (opcional, default `text`): `text` ou `json`.

**Saídas (determinísticas, ordenadas):**
- Para cada arquivo `.md` em `docs/hermes/specs/` (exceto README.md, TEMPLATE.md) no **formato híbrido** (front matter TOML delimitado por `+++` + Markdown):
  - **Identificador**: o nome do arquivo é a fonte autoritativa; deve seguir `HERMES-NNNN-titulo-em-kebab-case.md` (NNNN = 4 dígitos). O front matter TOML deve conter `id = "HERMES-NNNN"` coincidente. O cabeçalho principal Markdown (`# HERMES-NNNN — Título`) deve declarar o mesmo identificador. Qualquer divergência entre as três fontes produz resultado inválido controlado. Não há fallback silencioso.
  - **Seções**: todas as 19 seções obrigatórias do TEMPLATE presentes no Markdown (Contexto, Problema Confirmado, Comportamento Atual, Comportamento Desejado, Fora do Escopo, Entradas, Saídas, Invariantes e Regras de Segurança, Pseudocódigo, Fluxo Principal, Casos de Erro e Limites, Critérios de Aceitação, Plano de Testes, Arquivos Provavelmente Afetados, Decisões Tomadas, Alternativas Descartadas, Riscos Restantes, Evidências da Implementação, Histórico de Alterações). Seções extras são permitidas. As seções "Status" e "Resumo para o Responsável pelo Projeto" são validadas separadamente.
  - **Status**: valor no TOML em {Rascunho, Aprovado, Em implementação, Implementado, Substituído}. Deve coincidir com a seção "Status" do Markdown.
  - **ACs**: cada AC declarado no TOML em `acceptance_criteria` (array de tabelas com `id`, `test_file`, `test_function`, `justification` opcional). O Markdown deve conter descrição correspondente no padrão `**AC-NN**: descrição` (NN sequencial a partir de 01).
  - **Vínculos testes**: para cada AC no TOML, `test_file` e `test_function` (quando presentes) devem existir e conter marcador `Spec: HERMES-XXXX / AC-NN`.
  - **Evidências**:
    - Se Status = **Implementado**: exige seção Evidências preenchida com os 11 campos padronizados abaixo. Cada campo deve conter valor concreto ou "Não aplicável — justificativa objetiva" quando a categoria realmente não se aplicar:
      1. **Commit da implementação** — hexadecimal entre 7 e 64 caracteres; não consulta Git nesta versão. **Sempre obrigatório (não aceita "Não aplicável")**.
      2. **Estado da integração** — ex.: "integrado na main via PR #1", "concluído na branch feature/X; ainda não integrado", "integrado na main (push direto)". **Sempre obrigatório (não aceita "Não aplicável")**.
      3. **Arquivos alterados** — lista ou descrição dos arquivos modificados. **Sempre obrigatório (não aceita "Não aplicável")**.
      4. **Testes direcionados** — comando + resultado; ou "Não aplicável — alteração exclusivamente documental".
      5. **Suíte completa** — comando + resultado; ou "Não aplicável — nenhuma alteração funcional".
      6. **Validação de sintaxe ou compileall** — comando + resultado; ou "Não aplicável — nenhum arquivo Python alterado".
      7. **Empacotamento** — comando + resultado; ou "Não aplicável — distribuição não alterada".
      8. **git diff --check** — "sem avisos" ou lista de avisos; sempre obrigatório. **Sempre obrigatório (não aceita "Não aplicável")**.
      9. **Plataformas e versões validadas** — ex.: "Windows 10 (Python 3.11.15), Ubuntu 22.04 (Python 3.11.9)". **Sempre obrigatório (não aceita "Não aplicável")**.
      10. **CI** — ex.: "8 checks aprovados no GitHub Actions"; ou "Não aplicável — integração sem CI".
      11. **Limitações do ambiente** — ex.: "Symlinks indisponíveis no Windows CI; 2 testes skipped"; "Nenhuma limitação conhecida" é valor válido. **Sempre obrigatório (não aceita "Não aplicável")**.
    - **Resumo da política de evidências**:
      - **6 campos sempre-obrigatórios** (nunca aceitam "Não aplicável"): Commit da implementação, Estado da integração, Arquivos alterados, git diff --check, Plataformas e versões validadas, Limitações do ambiente.
      - **5 campos condicionais** (aceitam "Não aplicável — justificativa objetiva" quando a categoria não se aplica): Testes direcionados, Suíte completa, Validação de sintaxe ou compileall, Empacotamento, CI.
      - Para alteração exclusivamente documental: Testes direcionados, Suíte completa, compileall e Empacotamento aceitam "Não aplicável — justificativa objetiva"; git diff --check permanece obrigatório.
      - Para integração via PR: número do PR, commit de integração, resultado CI, quantidade de checks.
      - Implementação em branch não integrada: estado deve declarar "Concluído na branch X; ainda não integrado"; PR/merge/CI usam "Não aplicável — integração ainda não realizada".
      - Integração direta na main permitida; main é branch válida; PR = "Não aplicável — integração sem PR".
      - **Estado final do working tree é recomendado, mas não requisito mínimo universal da primeira versão.**
      - Riscos restantes ficam na seção própria da especificação.
    - Se Status = **Substituído**: exige referência explícita à especificação que o substitui (campo "Substituída por" no cabeçalho ou seção "Histórico de Alterações"). Não exige evidências de implementação própria.
    - A validação da referência substituta é determinística e somente leitura.
    - **Riscos restantes** continuam registrados na seção obrigatória própria da especificação. Essa seção deve declarar os riscos conhecidos ou "Nenhum risco restante conhecido"; não precisa ser duplicada na tabela de evidências.
  - **Caminhos seguros**: somente valores formalmente definidos pelo formato como caminhos devem passar por validação de contenção e segurança (ex.: arquivo do teste, arquivo de especificação, diretório de especificações). A validação usa as proteções de caminho do núcleo `hermes-ops` (`core/paths.py`); a função concreta será definida na decisão arquitetural. Campos como `commit`, `plataformas validadas`, `resultado de teste`, `comando` e texto descritivo **não** são caminhos e não passam por validação de caminho. Referências de teste são extraídas em campos separados:
    - arquivo do teste (validado como caminho);
    - nome da função;
    - tipo do teste;
    - descrição.
  - URLs legítimas, texto explicativo e Markdown bruto **não** passam por validação de caminho.
  - `PublicSanitizer` é aplicado **somente na apresentação dos resultados** (saída texto/JSON), impedindo exposição de caminhos locais na saída pública. Sanitização de saída não substitui validação de contenção e segurança.
  - **Política de symlinks, junctions e reparse points: DECISÃO PENDENTE** para microbloco separado.
    - Mantido como decidido: caminhos formais precisam de validação segura; caminhos externos ao projeto são proibidos; sanitização de saída não substitui validação.
    - Pendente: se toda indireção será rejeitada; se indireções internas contidas poderão ser aceitas; função concreta de core/paths.py; status, código e comportamento exatos.
    - Não use indirect_path_blocked como decisão final.
  - **Ordenação**: arquivos processados em ordem alfabética (logo, numérica por NNNN).

**Resultado agregado (precedência exata de `Report.exit_code`):**

| Ordem | Condição | Exit Code |
|-------|----------|-----------|
| 1 | `forced_exit_code` definido | valor do `forced_exit_code` |
| 2 | qualquer resultado com `code == "external_failure"` | **4** |
| 3 | qualquer resultado não-OK com `code` começando com `config_` | **2** |
| 4 | qualquer resultado com `status == BLOCKED` | **3** |
| 5 | qualquer resultado com `status == ERROR` | **1** |
| 6 | apenas `WARNING` e/ou `OK` | **0** |

> **A precedência não segue o valor numérico do exit code.** `config_*` (2) prevalece sobre `BLOCKED` (3); `external_failure` (4) prevalece sobre tudo; `forced_exit_code` prevalece conforme a implementação atual.

**Exemplos de agregação:**
- `WARNING` + `OK` = **0**
- `WARNING` + `ERROR` = **1**
- `ERROR` + `BLOCKED` = **3**
- `config_*` não-OK + `ERROR` = **2**
- `config_*` não-OK + `BLOCKED` = **2**
- `external_failure` + `BLOCKED` = **4**
- `forced_exit_code` prevalece conforme a implementação atual

**Política de `justification` por status:**

O campo `justification` nos ACs do front matter TOML segue política rigorosa por status:

- **Rascunho**: `test_file` opcional; `justification` opcional; pode não possuir nenhum dos dois; não usar `justification` para indicar trabalho futuro; quando ainda não existe teste nem motivo de não aplicabilidade, omitir ambos.
- **Aprovado**: cada AC deve possuir exatamente um caminho — `test_file` ou `justification` válida.
- **Em implementação**: cada AC deve possuir exatamente um caminho — `test_file` ou `justification` válida.
- **Implementado**: cada AC deve possuir exatamente um caminho; `justification` só é permitida quando (1) teste automatizado é objetivamente não aplicável ou (2) o critério não é automatizável; `justification` deve conter: (a) razão objetiva, (b) método de validação manual ou documental, (c) referência verificável da evidência.
- **Substituído**: não exige criação de novos vínculos; vínculos históricos existentes são preservados; não exige `justification` somente por estar Substituído.

Regras transversais:
- `test_file` e `justification` são mutuamente exclusivos.
- `test_function` só pode existir junto de `test_file`.
- O mesmo `test_file` pode cobrir vários ACs.
- A mesma `test_function` pode cobrir vários ACs quando isso estiver documentado.
- Quando existe teste apontável, ele deve ser referenciado diretamente.
- "Outro AC já cobre" não substitui `test_file`.
- Ausência de CI não é `justification` de AC.

Marcadores inválidos de `justification` (rejeitados com ERROR):
- vazio; "pendente"; "a fazer"; "depois"; "futuro"; "TBD"; "em andamento"; "não executado"; "N/A"; "não aplicável" sem explicação; "desconhecido"; traço isolado ("—").

Exemplo válido para **Implementado**:
```toml
justification = "Validação manual — o critério exige inspeção visual do alinhamento no terminal. Procedimento e resultado registrados em docs/evidencias/alinhamento-terminal.md."
```

Exemplo válido para **Rascunho** sem decisão de teste:
```toml
[[acceptance_criteria]]
id = "AC-03"
```

Não usar como exemplo válido:
```toml
justification = "Teste será definido depois."
```

**Divergências TOML versus Markdown (ERROR documental, exit code isolado 1):**

As seguintes inconsistências entre o front matter TOML e o corpo Markdown são tratadas como **ERROR documental**, código público (nomes definitivos pendentes), exit code isolado **1**, sem traceback, sem uso de `BLOCKED`, sem prefixo `config_`. Quando a inconsistência impede validação do documento, o arquivo atual é pulado e a inspeção continua nos demais documentos.

1. Identificador divergente.
2. Status divergente.
3. AC presente no TOML e ausente no Markdown.
4. AC presente no Markdown e ausente no TOML.
5. AC duplicado.
6. `superseded_by` divergente.
7. Ordem dos ACs diferente entre TOML e Markdown.
8. ID ou status com capitalização não canônica.
9. Descrição humana de AC vazia.
10. Cabeçalho Markdown ausente.

Não são comparados (o texto humano da descrição do AC não é duplicado no TOML):
- Estilo, pontuação, capitalização, formatação da descrição.

**IMPORTANTE:** A política de ordem divergente entre TOML e Markdown não decide a política de gap na numeração dos ACs. Mantém-se explicitamente pendente: AC fora de sequência/gap — WARNING versus ERROR.

Exemplo de gap ainda pendente: AC-01, AC-02, AC-04.

**Schema TOML versão 1 — fechado e estrito:**

O schema versão 1 é **fechado**. São **erros documentais** (ERROR documental, exit code isolado 1, sem traceback, sem `config_`, sem `BLOCKED`, pula documento atual, continua os demais):

- Chave desconhecida no nível superior.
- Chave desconhecida em `acceptance_criteria`.
- Chave desconhecida em `evidence`.
- Tabela desconhecida.
- `schema_version` ausente.
- `schema_version` com tipo diferente de inteiro.
- `schema_version` zero ou negativo.
- `schema_version` maior que 1.
- Chave TOML duplicada.

Para `schema_version` maior que 1:
- Considerar versão não suportada.
- Não interpretar parcialmente.
- Não tentar validar apenas campos conhecidos da versão 1.
- Pular o documento atual.
- Continuar os demais documentos.
- ERROR documental; exit code isolado 1; nome do código público permanece pendente.

Não usar: WARNING para campos desconhecidos; schema aberto; schema parcialmente aberto; heurística de Levenshtein; sugestão automática de correção; processamento parcial de versão futura.

A evolução acontece por:
1. Definição explícita de nova `schema_version`.
2. Implementação do suporte correspondente.
3. Migração documentada.

**Formato texto:**
```
OK        HERMES-0001: nome válido
OK        HERMES-0001: seções obrigatórias presentes
OK        HERMES-0001: status válido (Implementado)
AVISO     HERMES-0001: AC-12 não tem teste vinculado (status não é Implementado)
ERRO      HERMES-0002: seção 'Pseudocódigo' ausente
BLOQUEADO HERMES-0003: caminho absoluto em campo formal
exit_code=3
```

**Formato JSON:** array de objetos por arquivo, cada um com array de checks (name, status, message, details, code). Mesma lógica de `Report.to_json()`.

**Sem traceback:** qualquer exceção é capturada no boundary do CLI e reportada como `external_failure` (exit_code=4), igual aos comandos existentes.

## Fora do Escopo

- **Correção automática**: o comando não reescreve, renomeia ou corrige arquivos.
- **Validação de conteúdo semântico**: não verifica se pseudocódigo está correto, se decisões fazem sentido, se riscos são reais — apenas estrutura e presença.
- **Validação cruzada entre especificações**: não checa se números NNNN são sequenciais sem gaps (apenas formato individual).
- **Integração com Git hooks**: não instala pre-commit/pre-push; o usuário decide como invocar.
- **Validação de arquivos fora de `docs/hermes/specs/`**: escopo restrito a essa pasta.
- **Novos códigos de erro**: usa os status e códigos existentes (`ok`, `config_*`, `external_failure`).

## Entradas

- Caminho do projeto (`--project`, obrigatório).
- Formato de saída (`--format`, opcional: `text` | `json`, default `text`).
- Diretório `docs/hermes/specs/` dentro do projeto (existência obrigatória).
- Arquivos `.md` dentro de `docs/hermes/specs/` (exceto `README.md`, `TEMPLATE.md`) no **formato híbrido**: front matter TOML delimitado por `+++` + Markdown. O TOML contém dados validáveis machine-readable; o Markdown contém conteúdo humano.
- Testes do projeto (para verificação de vínculos AC → teste): busca por marcadores `Spec: HERMES-XXXX / AC-NN` em `tests/**/*.py`.

## Saídas

- `Report` com:
  - `command`: `"spec-check"`
  - `results`: tupla de `CheckResult` (um por verificação por arquivo)
  - `exit_code`: 0/1/2/3/4 conforme regras acima
- STDOUT: relatório em texto ou JSON determinístico (chaves ordenadas, sets normalizados, paths sanitizados).
- STDERR: apenas `exit_code=N` no modo texto; vazio no modo JSON.

## Invariantes e Regras de Segurança

1. **Somente leitura**: o comando **nunca** escreve, renomeia, move ou apaga arquivos.
2. **Validação de caminho**: apenas valores formalmente definidos como caminhos (ex.: arquivo do teste, arquivo de especificação, diretório de especificações) passam por validação de contenção via proteções de `core/paths.py`. A função concreta será definida na decisão arquitetural.
3. **Sanitização de saída**: `PublicSanitizer` remove caminhos absolutos e `..` de **toda saída pública** (texto e JSON). Sanitização de saída não substitui validação de contenção e segurança.
4. **Sem traceback**: exceções no dispatch são capturadas no `main()` e reportadas como `external_failure` (exit_code=4).
5. **Determinismo**: ordem de processamento alfabética; JSON com `sort_keys=True`, `separators=(",", ":")`; sets ordenados lexicograficamente.
6. **Não executa testes**: apenas verifica presença de marcadores `Spec: HERMES-XXXX / AC-NN` nos arquivos de teste.
7. **Referências de teste estruturadas**: extraídas em campos separados (arquivo do teste — validado como caminho —, nome da função, tipo do teste, descrição).
8. **Evidências de Implementado**: a seção Evidências de todo Implementado deve possuir os 11 campos padronizados (Commit, Estado da integração, Arquivos alterados, Testes direcionados, Suíte completa, Validação de sintaxe/compileall, Empacotamento, git diff --check, Plataformas validadas, CI, Limitações do ambiente). **6 campos sempre-obrigatórios** (nunca aceitam "Não aplicável"): Commit da implementação, Estado da integração, Arquivos alterados, git diff --check, Plataformas e versões validadas, Limitações do ambiente. **5 campos condicionais** (aceitam "Não aplicável — justificativa objetiva" quando a categoria não se aplica): Testes direcionados, Suíte completa, Validação de sintaxe ou compileall, Empacotamento, CI. Cada campo deve conter valor concreto ou "Não aplicável — justificativa objetiva" quando a categoria não se aplicar. "Nenhuma limitação conhecida" é valor válido para Limitações do ambiente. Campo vazio ou marcador provisório ("pendente", "a fazer", "TBD", "N/A" sem justificativa, "não executado", "não aplicável" isolado) é inválido. Commit deve ser hexadecimal entre 7 e 64 caracteres; nesta versão não consulta Git. Para alteração exclusivamente documental: Testes direcionados, Suíte completa, compileall e Empacotamento aceitam "Não aplicável — justificativa objetiva"; git diff --check permanece obrigatório. Para integração via PR: número do PR, commit de integração, resultado CI, quantidade de checks. Implementação em branch não integrada: estado deve declarar "Concluído na branch X; ainda não integrado"; PR/merge/CI usam "Não aplicável — integração ainda não realizada". Integração direta na main permitida; main é branch válida; PR = "Não aplicável — integração sem PR". **Estado final do working tree é recomendado, mas não requisito mínimo universal da primeira versão.** Riscos restantes ficam na seção própria da especificação.
9. **Formato de especificação**: front matter TOML + Markdown (formato híbrido aprovado). O TOML contém dados validáveis machine-readable; o Markdown contém conteúdo humano. Delimitadores `+++` obrigatórios. Parser usa `tomllib` da stdlib Python 3.11+.
## Pseudocódigo

*Lógica independente da linguagem, legível por quem não programa em Python.
Explique decisões, não traduza linhas.*

```text
CONSTANTES:
    REQUIRED_SECTIONS = [
        "Contexto",
        "Problema Confirmado",
        "Comportamento Atual",
        "Comportamento Desejado",
        "Fora do Escopo",
        "Entradas",
        "Saídas",
        "Invariantes e Regras de Segurança",
        "Pseudocódigo",
        "Fluxo Principal",
        "Casos de Erro e Limites",
        "Critérios de Aceitação",
        "Plano de Testes",
        "Arquivos Provavelmente Afetados",
        "Decisões Tomadas",
        "Alternativas Descartadas",
        "Riscos Restantes",
        "Evidências da Implementação",
        "Histórico de Alterações"
    ]

    VALID_STATUSES = {"Rascunho", "Aprovado", "Em implementação", "Implementado", "Substituído"}

    NAME_PATTERN = regex: ^HERMES-\d{4}-.+\.md$

    AC_PATTERN = regex: ^\s*[-*]?\s*\*\*AC-(\d{2})\*\*:?\s*(.+)$

    EVIDENCE_REQUIRED_FIELDS_IMPLEMENTED = [
        "Commit da implementação",
        "Estado da integração",
        "Arquivos alterados",
        "Testes direcionados",
        "Suíte completa",
        "Validação de sintaxe ou compileall",
        "Empacotamento",
        "git diff --check",
        "Plataformas e versões validadas",
        "CI",
        "Limitações do ambiente"
    ]

    # Campos que SEMPRE exigem valor concreto (nunca aceitam "Não aplicável")
    EVIDENCE_ALWAYS_REQUIRED_FIELDS = {
        "Commit da implementação",
        "Estado da integração",
        "Arquivos alterados",
        "git diff --check",
        "Plataformas e versões validadas",
        "Limitações do ambiente"
    }

    # Campos condicionais (aceitam "Não aplicável — justificativa objetiva" quando categoria não se aplica)
    EVIDENCE_CONDITIONAL_FIELDS = {
        "Testes direcionados",
        "Suíte completa",
        "Validação de sintaxe ou compileall",
        "Empacotamento",
        "CI"
    }

    EVIDENCE_REQUIRED_FIELDS_SUPERSEDED = [
        "Substituída por"  # referência explícita à spec substituta
    ]

    MARCADORES_REJEITADOS = [
        "", "pendente", "a fazer", "depois", "desconhecido", "TBD", "futuro",
        "em andamento", "não executado", "N/A", "não aplicável", "—"
    ]

    FUNÇÃO MARCADOR_REJEITADO(valor):
        valor_lower = valor.TRIM().LOWER()
        PARA cada m EM MARCADORES_REJEITADOS:
            SE valor_lower == m:
                RETORNAR VERDADEIRO
        RETORNAR FALSO

    EXCLUDED_FILES = {"README.md", "TEMPLATE.md"}

    # Chaves permitidas no schema versão 1 (fechado)
    TOML_ALLOWED_TOPLEVEL = {"schema_version", "id", "status", "acceptance_criteria", "superseded_by", "evidence"}
    TOML_ALLOWED_AC = {"id", "test_file", "test_function", "justification"}
    TOML_ALLOWED_EVIDENCE = {
        "Commit da implementação",
        "Estado da integração",
        "Arquivos alterados",
        "Testes direcionados",
        "Suíte completa",
        "Validação de sintaxe ou compileall",
        "Empacotamento",
        "git diff --check",
        "Plataformas e versões validadas",
        "CI",
        "Limitações do ambiente"
    }
    TOML_ALLOWED_TABLES = {"acceptance_criteria", "evidence"}

    FUNÇÃO PARSE_HYBRID_FORMAT(raw_content, filename):
        """Parse do formato híbrido: front matter TOML delimitado por +++ + Markdown.

        Regras:
        - O documento DEVE começar com delimitador '+++' na primeira linha.
        - O segundo '+++' encerra o front matter TOML.
        - O conteúdo entre os dois delimitadores é analisado com tomllib.
        - O conteúdo após o segundo delimitador é o corpo Markdown.
        - Delimitador inicial ausente, delimitador final ausente, ou TOML inválido
          geram erro 'invalid_hybrid_format' (pula arquivo).
        - Delimitadores '+++' dentro do corpo Markdown NÃO reiniciam o parsing
          do front matter (apenas os dois primeiros são considerados).
        """
        SE NÃO raw_content.COMEÇA_COM("+++\n"):
            RETORNAR NULO  # sem delimitador inicial
        # Busca o segundo delimitador
        pos = raw_content.ENCONTRAR("\n+++\n", 4)  # pula o primeiro '+++\n'
        SE pos == -1:
            RETORNAR NULO  # sem delimitador final
        toml_text = raw_content[4:pos]  # conteúdo entre delimitadores
        markdown_content = raw_content[pos + 5:]  # após '\n+++\n'
        TENTAR:
            toml_data = TOMLLIB.LOADS(toml_text)
        CAPTURAR TOMLDecodeError:
            RETORNAR NULO  # TOML inválido (inclui chaves duplicadas)
        RETORNAR (toml_data, markdown_content)

    FUNÇÃO VALIDAR_SCHEMA_FECHADO(toml_data, spec_id):
        results = []
        # 1. Chaves desconhecidas no nível superior
        PARA cada key EM toml_data.CHAVES():
            SE key NÃO EM TOML_ALLOWED_TOPLEVEL:
                results.ADICIONAR(CheckResult("schema:unknown_field", ERRO,
                    "chave desconhecida no nível superior: " + key,
                    code="unknown_field_toplevel"))
        # 2. Chaves duplicadas: tomllib levanta TOMLDecodeError em duplicatas (não sobrescreve silenciosamente).
        # Falha de parsing é capturada no parse do formato híbrido (invalid_hybrid_format).
        # 3. acceptance_criteria: chaves desconhecidas em cada item
        acs = toml_data.OBTER("acceptance_criteria", LISTA VAZIA)
        PARA cada ac EM acs:
            PARA cada key EM ac.CHAVES():
                SE key NÃO EM TOML_ALLOWED_AC:
                    results.ADICIONAR(CheckResult("schema:unknown_field", ERRO,
                        "chave desconhecida em acceptance_criteria: " + key,
                        code="unknown_field_ac"))
        # 4. evidence: chaves desconhecidas
        evidence = toml_data.OBTER("evidence")
        SE evidence NÃO É NULO:
            PARA cada key EM evidence.CHAVES():
                SE key NÃO EM TOML_ALLOWED_EVIDENCE:
                    results.ADICIONAR(CheckResult("schema:unknown_field", ERRO,
                        "chave desconhecida em evidence: " + key,
                        code="unknown_field_evidence"))
        # 5. Tabelas desconhecidas (arrays de tabelas fora dos permitidos)
        # tomllib não distingue array de tabela de tabela simples facilmente.
        # Implementação prática: validar apenas acceptance_criteria e evidence como arrays.
        RETORNAR results

    FUNÇÃO VALIDAR_ACS_HYBRID(toml_acs, markdown_acs, spec_id):
        results = []
        # Mapa por ID para comparação
        toml_by_id = {ac.OBTER("id"): ac PARA ac EM toml_acs SE ac.OBTER("id") NÃO É NULO}
        md_by_id = {ac.OBTER("id"): ac PARA ac EM markdown_acs SE ac.OBTER("id") NÃO É NULO}
        toml_ids = list(toml_by_id.CHAVES())
        md_ids = list(md_by_id.CHAVES())
        # AC duplicado no TOML
        SE len(toml_ids) != len(set(toml_ids)):
            results.ADICIONAR(CheckResult("ac:duplicate", ERRO, "AC duplicado no TOML", code="ac_duplicate"))
        # AC duplicado no Markdown
        SE len(md_ids) != len(set(md_ids)):
            results.ADICIONAR(CheckResult("ac:duplicate", ERRO, "AC duplicado no Markdown", code="ac_duplicate"))
        # AC no TOML ausente no Markdown
        PARA id EM toml_ids:
            SE id NÃO EM md_ids:
                results.ADICIONAR(CheckResult("ac:missing_in_markdown", ERRO,
                    "AC " + id + " presente no TOML e ausente no Markdown",
                    code="ac_missing_in_markdown"))
        # AC no Markdown ausente no TOML
        PARA id EM md_ids:
            SE id NÃO EM toml_ids:
                results.ADICIONAR(CheckResult("ac:missing_in_toml", ERRO,
                    "AC " + id + " presente no Markdown e ausente no TOML",
                    code="ac_missing_in_toml"))
        # Ordem diferente
        SE toml_ids != md_ids:
            results.ADICIONAR(CheckResult("ac:order_mismatch", ERRO,
                "ordem dos ACs diferente entre TOML e Markdown",
                code="ac_order_mismatch"))
        # ID/status capitalização não canônica (verifica padrão AC-NN)
        PARA id EM toml_ids + md_ids:
            SE NÃO id CORRESPONDE ^AC-\\d{2}$:
                results.ADICIONAR(CheckResult("ac:capitalization", ERRO,
                    "ID com capitalização não canônica: " + id,
                    code="non_canonical_capitalization"))
        # Descrição humana vazia (apenas Markdown tem descrição)
        PARA ac EM markdown_acs:
            desc = ac.OBTER("desc", "")
            SE desc É VAZIA OU desc.TRIM() == "":
                results.ADICIONAR(CheckResult("ac:" + ac.OBTER("id"), ERRO,
                    "descrição humana de AC vazia",
                    code="ac_empty_description"))
        RETORNAR results

    FUNÇÃO MARCADOR_REJEITADO(valor):
        valor_lower = valor.TRIM().LOWER()
        REJEITADOS = ["", "pendente", "a fazer", "depois", "desconhecido", "tbd", "futuro",
                      "em andamento", "não executado", "n/a", "não aplicável", "—", "-"]
        PARA cada m EM REJEITADOS:
            SE valor_lower == m:
                RETORNAR VERDADEIRO
        RETORNAR FALSO

    FUNÇÃO JUSTIFICATION_VALIDA(justification, status):
        SE justification É NULA OU justification.TRIM() == "":
            RETORNAR FALSO
        SE MARCADOR_REJEITADO(justification):
            RETORNAR FALSO
        SE status == "Implementado":
            # Deve conter 3 elementos: razão objetiva, método, referência verificável
            # Heurística simples: contém "—" separando partes, tem referência a docs/evidencias ou arquivo
            TEM_RAZAO = justification.CONTÉM("—") OU justification.CONTÉM("-")
            TEM_REFERENCIA = justification.CONTÉM("docs/") OU justification.CONTÉM("evidencias/") OU justification.CONTÉM(".md")
            RETORNAR TEM_RAZAO E TEM_REFERENCIA
        RETORNAR VERDADEIRO  # Para outros status, justification não vazia e não rejeitada é válida

    FUNÇÃO VALIDAR_VINCULO_TESTE_HYBRID(ac_id, spec_id, test_file, test_function, justification, test_markers, toml_status):
        # Regra: test_file e justification mutuamente exclusivos
        TEM_TESTE = test_file NÃO É NULO E test_file != ""
        TEM_JUSTIFICATION = justification NÃO É NULA E justification != ""

        SE TEM_TESTE E TEM_JUSTIFICATION:
            RETORNAR CheckResult("teste:" + ac_id, ERRO,
                "test_file e justification são mutuamente exclusivos",
                code="test_justification_both")

        SE TEM_TESTE:
            SE test_function NÃO É NULO E test_function != "":
                RETORNAR CheckResult("teste:" + ac_id, ERRO,
                    "test_function só pode existir junto de test_file",
                    code="test_function_without_file")
            # Validar se teste existe nos marcadores
            key = spec_id + "/" + ac_id
            SE key EM test_markers:
                # Verificar se test_file coincide
                marker_file = test_markers[key][0].arquivo_teste
                SE test_file NÃO CORRESPONDE marker_file:
                    RETORNAR CheckResult("teste:" + ac_id, ERRO,
                        "test_file no TOML (" + test_file + ") difere do marcador (" + marker_file + ")",
                        code="test_file_mismatch")
                RETORNAR CheckResult("teste:" + ac_id, OK,
                    "vínculo em " + marker_file, code="ok")
            SENAO:
                RETORNAR CheckResult("teste:" + ac_id, ERRO,
                    "test_file declarado mas marcador não encontrado em testes",
                    code="test_file_missing")

        SE TEM_JUSTIFICATION:
            SE NÃO JUSTIFICATION_VALIDA(justification, toml_status):
                RETORNAR CheckResult("teste:" + ac_id, ERRO,
                    "justification inválida para status " + toml_status + ": " + justification,
                    code="invalid_justification")
            RETORNAR CheckResult("teste:" + ac_id, OK,
                "justification aceita: " + justification, code="ok")

        # Nenhum dos dois
        SE toml_status EM {"Aprovado", "Em implementação", "Implementado"}:
            RETORNAR CheckResult("teste:" + ac_id, ERRO,
                "AC deve ter test_file ou justification válida no status " + toml_status,
                code="missing_test_or_justification")
        # Rascunho e Substituído: permitido não ter nenhum
        RETORNAR CheckResult("teste:" + ac_id, OK,
            "sem test_file nem justification (permitido no status " + toml_status + ")", code="ok")

    FUNÇÃO main(project_path, format):
        sanitizer = PublicSanitizer.for_project(project_path)  # usado apenas na apresentação final
        specs_dir = project_path / "docs/hermes/specs"
        SE NÃO specs_dir.EXISTE():
            # Política já aprovada: ERROR, code=specs_dir_missing, exit_code=1 quando isolado
            # Não cria a pasta; encerra o comando; sem traceback; NÃO usa forced_exit_code
            results = LISTA VAZIA
            results.ADICIONAR(CheckResult("specs_dir", ERRO, "diretório docs/hermes/specs não encontrado", code="specs_dir_missing"))
            RETORNAR Report.from_results("spec-check", results)

        spec_files = LISTAR specs_dir/*.md ORDENADOS ALFABETICAMENTE
        spec_files = FILTRAR spec_files ONDE nome NÃO EM EXCLUDED_FILES

        # DECISÃO PENDENTE — tratamento de arquivos Markdown auxiliares/desconhecidos
        # em docs/hermes/specs/ que não seguem padrão HERMES-NNNN.
        # A. Arquivo que pretende ser especificação mas possui nome HERMES inválido →
        #    invalid_filename_pattern (ERROR, pula arquivo).
        # B. Arquivo Markdown auxiliar/desconhecido → DECISÃO PENDENTE: ignorar, WARNING ou ERROR.
        # README.md e TEMPLATE.md continuam explicitamente ignorados.

        all_results = LISTA VAZIA
        test_markers = EXTRAIR_MARCADORES_TESTES(project_path)  # mapa: "HERMES-XXXX/AC-NN" -> lista de marcadores com arquivo_teste, linha, funcao, tipo, descricao

        PARA cada spec_file EM spec_files:
            raw_content = LER_ARQUIVO(spec_file)

            # 0. Parse front matter TOML (formato híbrido)
            toml_data, markdown_content = PARSE_HYBRID_FORMAT(raw_content, spec_file.name)
            SE toml_data É NULO:
                result = CheckResult("formato", ERRO, "front matter TOML ausente ou delimitadores +++ inválidos", code="invalid_hybrid_format")
                all_results.ADICIONAR(result)
                CONTINUAR  # não processa este arquivo

            # 1. Identificador: extrair do nome do arquivo (fonte autoritativa)
            file_spec_id = EXTRAIR_ID_DO_NOME(spec_file.name)  # HERMES-NNNN
            SE file_spec_id É NULO:
                result = CheckResult("identificador", ERRO,
                                     "nome do arquivo não segue padrão HERMES-NNNN-titulo.md",
                                     code="invalid_filename_pattern")
                all_results.ADICIONAR(result)
                CONTINUAR  # não processa este arquivo

            # 2. Validar id no TOML
            toml_id = toml_data.OBTER("id")
            SE toml_id É NULO:
                result = CheckResult("identificador:toml", ERRO, "campo 'id' ausente no front matter TOML", code="missing_toml_id")
                all_results.ADICIONAR(result)
                CONTINUAR
            SE toml_id != file_spec_id:
                result = CheckResult("identificador", ERRO,
                                     "id no TOML (" + toml_id + ") difere do nome do arquivo (" + file_spec_id + ")",
                                     code="toml_filename_mismatch")
                all_results.ADICIONAR(result)
                CONTINUAR

            # 3. Validar cabeçalho Markdown coincide
            header_spec_id = EXTRAIR_ID_DO_CABECALHO(markdown_content)
            SE header_spec_id É NULO:
                result = CheckResult("identificador", ERRO,
                                     "cabeçalho principal ausente ou não contém HERMES-NNNN",
                                     code="missing_header_id")
                all_results.ADICIONAR(result)
                CONTINUAR
            SE header_spec_id != file_spec_id:
                result = CheckResult("identificador", ERRO,
                                     "identificador no cabeçalho (" + header_spec_id + ") difere do nome do arquivo (" + file_spec_id + ")",
                                     code="header_filename_mismatch")
                all_results.ADICIONAR(result)
                CONTINUAR

            spec_id = file_spec_id  # identificador validado e unificado

            # 4. Validar schema_version (schema versão 1 é fechado e estrito)
            schema_version = toml_data.OBTER("schema_version")
            SE schema_version É NULO:
                result = CheckResult("schema_version", ERRO, "campo 'schema_version' ausente no front matter TOML", code="missing_schema_version")
                all_results.ADICIONAR(result)
                CONTINUAR  # não processa este arquivo
            SE schema_version NÃO É INTEIRO:
                result = CheckResult("schema_version", ERRO, "schema_version deve ser inteiro", code="invalid_schema_version_type")
                all_results.ADICIONAR(result)
                CONTINUAR
            SE schema_version <= 0:
                result = CheckResult("schema_version", ERRO, "schema_version deve ser positivo", code="invalid_schema_version_value")
                all_results.ADICIONAR(result)
                CONTINUAR
            SE schema_version > 1:
                # Versão futura não suportada: não interpreta parcialmente, pula documento
                result = CheckResult("schema_version", ERRO, "schema_version '" + schema_version + "' não suportado; versão máxima 1", code="unsupported_schema_version")
                all_results.ADICIONAR(result)
                CONTINUAR  # pula este arquivo, continua os demais
            # schema_version == 1: prossegue

            # 4b. Validar schema fechado: chaves desconhecidas
            results = VALIDAR_SCHEMA_FECHADO(toml_data, spec_id)
            all_results.ESTENDER(results)
            SE EXISTE RESULTADO COM status == ERRO EM results ONDE code COMEÇA_COM "unknown_field":
                CONTINUAR  # pula este arquivo, continua os demais

            # 5. Validar nome do arquivo (padrão completo)
            result = VALIDAR_NOME_COMPLETO(spec_file.name, spec_id)
            all_results.ADICIONAR(result)

            # 6. Validar seções obrigatórias (19 do TEMPLATE) no Markdown
            results = VALIDAR_SECOES_OBRIGATORIAS(markdown_content, spec_id)
            all_results.ESTENDER(results)

            # 7. Validar Status (TOML + Markdown)
            toml_status = toml_data.OBTER("status")
            SE toml_status É NULO:
                result = CheckResult("status:toml", ERRO, "campo 'status' ausente no front matter TOML", code="missing_toml_status")
                all_results.ADICIONAR(result)
            SENÃO SE toml_status NÃO EM VALID_STATUSES:
                result = CheckResult("status:toml", ERRO, "status inválido no TOML: " + toml_status, code="invalid_toml_status")
                all_results.ADICIONAR(result)
            SENÃO:
                result = CheckResult("status:toml", OK, "status válido no TOML (" + toml_status + ")", code="ok")
                all_results.ADICIONAR(result)

            markdown_status = EXTRAIR_STATUS(markdown_content)
            SE markdown_status É NULO:
                result = CheckResult("status:markdown", ERRO, "seção 'Status' ausente no Markdown", code="missing_markdown_status")
                all_results.ADICIONAR(result)
            SENÃO SE markdown_status != toml_status:
                result = CheckResult("status", ERRO, "status no TOML (" + toml_status + ") difere do Markdown (" + markdown_status + ")", code="status_mismatch")
                all_results.ADICIONAR(result)
            SENÃO:
                result = CheckResult("status:markdown", OK, "status coincide (" + markdown_status + ")", code="ok")
                all_results.ADICIONAR(result)

            # 8. Extrair e validar ACs (TOML + Markdown)
            toml_acs = toml_data.OBTER("acceptance_criteria", LISTA VAZIA)
            markdown_acs = EXTRAIR_ACS(markdown_content, spec_id)

            results = VALIDAR_ACS_HYBRID(toml_acs, markdown_acs, spec_id)
            all_results.ESTENDER(results)

            # 9. Validar vínculos AC -> testes (usando TOML)
            PARA cada ac_toml EM toml_acs:
                ac_id = ac_toml.OBTER("id")
                SE ac_id É NULO:
                    CONTINUAR  # já reportado em VALIDAR_ACS_HYBRID
                test_file = ac_toml.OBTER("test_file")
                test_function = ac_toml.OBTER("test_function")
                justification = ac_toml.OBTER("justification")

                result = VALIDAR_VINCULO_TESTE_HYBRID(ac_id, spec_id, test_file, test_function, justification, test_markers, toml_status)
                all_results.ADICIONAR(result)

            # 10. Validar superseded_by se status = Substituído
            SE toml_status == "Substituído":
                superseded_by = toml_data.OBTER("superseded_by")
                SE superseded_by É NULO:
                    # Fallback: tentar extrair do Markdown (cabeçalho ou Histórico)
                    header = EXTRAIR_CABECALHO(markdown_content)
                    history_section = EXTRAIR_SECAO(markdown_content, "Histórico de Alterações")
                    superseded_by = EXTRAIR_SUBSTITUIDA_POR(header, history_section)

                SE superseded_by É NULO OU VAZIA:
                    results.ADICIONAR(CheckResult("evidencia:substituida_por", ERRO,
                                         "referência à especificação substituta ausente (campo 'superseded_by' no TOML ou 'Substituída por' no Markdown)",
                                         code="missing_superseded_by"))
                SENÃO:
                    SE superseded_by CORRESPONDE ^HERMES-\\d{4}-.+$:
                        results.ADICIONAR(CheckResult("evidencia:substituida_por", OK, "referência substituta presente: " + superseded_by, code="ok"))
                    SENÃO:
                        results.ADICIONAR(CheckResult("evidencia:substituida_por", ERRO,
                                             "formato de referência substituta inválido: " + superseded_by,
                                             code="invalid_superseded_by_format"))

            # 11. Validar evidências se status = Implementado
            SE toml_status == "Implementado":
                evidence_toml = toml_data.OBTER("evidence")
                SE evidence_toml É NULO:
                    results.ADICIONAR(CheckResult("evidence", ERRO, "tabela 'evidence' ausente no TOML para status Implementado", code="missing_evidence_toml"))
                SENÃO:
                    results = VALIDAR_EVIDENCIAS_IMPLEMENTADO_HYBRID(evidence_toml, markdown_content, spec_id)
                    all_results.ESTENDER(results)

            # 12. Validar campos TOML desconhecidos (DECISÃO PENDENTE: rejeitar, ignorar, WARNING)
            # TODO: implementar quando política for definida

        # 13. Validar caminhos formais (após processar todas as specs)
        results = VALIDAR_CAMINHOS_FORMAIS(project_path, spec_files, test_markers)
        all_results.ESTENDER(results)

        report = Report.from_results("spec-check", all_results)
        IMPRIMIR report.to_json(sanitizer) SE format == "json" SENÃO report.to_text(sanitizer)
        RETORNAR report.exit_code

FUNÇÃO EXTRAIR_MARCADORES_TESTES(project_path):
    markers = MAPA VAZIO
    PARA cada test_file EM project_path / "tests" RECURSIVO *.py:
        content = LER_ARQUIVO(test_file)
        PARA cada linha EM content COM NÚMERO DE LINHA:
            SE linha CONTÉM "Spec: HERMES-" E "/ AC-":
                EXTRAIR spec_id e ac_id
                markers[spec_id + "/" + ac_id].ADICIONAR({
                    "arquivo_teste": test_file,
                    "linha": linha,
                    "funcao": EXTRAIR_NOME_FUNCAO(content, linha),
                    "tipo": EXTRAIR_TIPO_TESTE(content, linha),
                    "descricao": EXTRAIR_DESCRICAO_TESTE(content, linha)
                })
    RETORNAR markers

FUNÇÃO EXTRAIR_ID_DO_NOME(filename):
    match = REGEX_MATCH(^HERMES-(\d{4})-.+\.md$, filename)
    SE match: RETORNAR "HERMES-" + match.grupo(1)
    RETORNAR NULO

FUNÇÃO EXTRAIR_ID_DO_CABECALHO(content):
    # Procura primeira linha começando com "# HERMES-NNNN"
    PARA cada linha EM content:
        SE linha CORRESPONDE ^#\s+HERMES-\d{4}:
            EXTRAIR HERMES-NNNN
            RETORNAR HERMES-NNNN
    RETORNAR NULO

FUNÇÃO VALIDAR_NOME_COMPLETO(filename, spec_id):
    SE filename CORRESPONDE NAME_PATTERN:
        RETORNAR CheckResult("identificador:nome", OK, "nome segue padrão HERMES-NNNN-titulo.md", code="ok")
    SENÃO:
        RETORNAR CheckResult("identificador:nome", ERRO, "nome não segue padrão HERMES-NNNN-titulo-em-kebab-case.md", code="invalid_filename_pattern")

FUNÇÃO VALIDAR_SECOES_OBRIGATORIAS(content, spec_id):
    results = []
    PARA cada section EM REQUIRED_SECTIONS:
        SE section NÃO ENCONTRADA EM content (heading markdown case-insensitive, níveis ## ou ###):
            results.ADICIONAR(CheckResult("secao:" + section, ERRO, "seção obrigatória ausente", code="missing_section"))
        SENÃO:
            results.ADICIONAR(CheckResult("secao:" + section, OK, "presente", code="ok"))
    # Validar também "Status" e "Resumo para o Responsável pelo Projeto" separadamente
    PARA section EM {"Status", "Resumo para o Responsável pelo Projeto"}:
        SE section NÃO ENCONTRADA EM content:
            results.ADICIONAR(CheckResult("secao:" + section, ERRO, "seção obrigatória ausente", code="missing_section"))
        SENÃO:
            results.ADICIONAR(CheckResult("secao:" + section, OK, "presente", code="ok"))
    RETORNAR results

FUNÇÃO VALIDAR_STATUS(content, spec_id):
    status = EXTRAIR_STATUS(content)  # linha após "## Status"
    SE status EM VALID_STATUSES:
        RETORNAR CheckResult("status", OK, "status válido (" + status + ")", code="ok")
    SENÃO:
        RETORNAR CheckResult("status", ERRO, "status inválido: " + status, code="invalid_status")

FUNÇÃO EXTRAIR_ACS(content, spec_id):
    acs = LISTA VAZIA
    na_secao_ac = FALSO
    PARA cada linha EM content:
        SE linha CORRESPONDE ^##\s+Critérios de Aceitação:
            na_secao_ac = VERDADEIRO
            CONTINUAR
        SE na_secao_ac E linha CORRESPONDE ^##\s+:
            BREAK  # próxima seção principal
        SE na_secao_ac:
            match = AC_PATTERN MATCH linha
            SE match:
                ac_num = match.grupo(1)  # NN
                ac_desc = match.grupo(2).strip()
                acs.ADICIONAR({"id": "AC-" + ac_num, "desc": ac_desc, "num": INT(ac_num)})
    ORDENAR acs POR num
    RETORNAR acs

FUNÇÃO VALIDAR_ACS(acs, spec_id):
    results = []
    expected_num = 1
    PARA cada ac EM acs:
        SE ac.num != expected_num:
            # DECISÃO PENDENTE — gap em numeração: WARNING vs ERROR
            # Código público: decisão pendente
            REGISTRAR_RESULTADO_CONFORME_POLITICA_PENDENTE("AC fora de sequência")
        SE ac.desc VAZIA:
            results.ADICIONAR(CheckResult("ac:" + ac.id, ERRO, "descrição vazia", code="ac_empty"))
        SENÃO:
            results.ADICIONAR(CheckResult("ac:" + ac.id, OK, "formato válido", code="ok"))
        expected_num += 1
    RETORNAR results

FUNÇÃO VALIDAR_VINCULO_TESTE(ac, spec_id, test_markers):
    key = spec_id + "/" + ac.id
    SE key EM test_markers:
        RETORNAR CheckResult("teste:" + ac.id, OK, "vínculo em " + test_markers[key][0].arquivo, code="ok")
    SENÃO:
        # DECISÃO PENDENTE — forma da justificativa explícita, política por status,
        # severidade e código público
        # Apenas detecta vínculo ausente; política de severidade será definida em microbloco próprio
        # Cada AC deve possuir teste ou justificativa permitida
        status = EXTRAIR_STATUS(content_do_spec)
        SE status == "Implementado":
            # Código público: decisão pendente
            REGISTRAR_RESULTADO_CONFORME_POLITICA_PENDENTE("AC sem teste — Implementado")
        SENÃO:
            # Código público: decisão pendente
            REGISTRAR_RESULTADO_CONFORME_POLITICA_PENDENTE("AC sem teste — status ≠ Implementado")

FUNÇÃO VALIDAR_EVIDENCIAS_IMPLEMENTADO(content, spec_id):
    results = []
    evidence_section = EXTRAIR_SECAO(content, "Evidências da Implementação")
    PARA cada field EM EVIDENCE_REQUIRED_FIELDS_IMPLEMENTED:
        SE field NÃO ENCONTRADO EM evidence_section:
            results.ADICIONAR(CheckResult("evidencia:" + field, ERRO, "campo obrigatório ausente para status Implementado", code="missing_evidence_field"))
        SENÃO:
            field_value = EXTRAIR_VALOR_CAMPO(evidence_section, field)
            SE field_value É VAZIO OU CORRESPONDE MARCADOR_REJEITADO(field_value):
                results.ADICIONAR(CheckResult("evidencia:" + field, ERRO, "campo obrigatório contém valor inválido: " + field_value, code="invalid_evidence_value"))
            SENÃO SE field_value COMEÇA_COM "Não aplicável —":
                # Verificar se a justificativa é objetiva
                justificativa = field_value[16:]  # após "Não aplicável — "
                SE justificativa É VAZIA:
                    results.ADICIONAR(CheckResult("evidencia:" + field, ERRO, "'Não aplicável' sem justificativa objetiva", code="invalid_na_justification"))
                SENÃO SE field EM EVIDENCE_ALWAYS_REQUIRED_FIELDS:
                    # Campos sempre-obrigatórios NÃO aceitam "Não aplicável"
                    results.ADICIONAR(CheckResult("evidencia:" + field, ERRO, "campo sempre-obrigatório não aceita 'Não aplicável'", code="always_required_not_na"))
                SENÃO:
                    results.ADICIONAR(CheckResult("evidencia:" + field, OK, "não aplicável — " + justificativa, code="ok"))
            SENÃO:
                # Validar formato específico por campo
                validation_result = VALIDAR_FORMATO_EVIDENCIA(field, field_value)
                SE validation_result NÃO É OK:
                    results.ADICIONAR(validation_result)
                SENÃO:
                    results.ADICIONAR(CheckResult("evidencia:" + field, OK, "preenchido", code="ok"))
    RETORNAR results

FUNÇÃO VALIDAR_FORMATO_EVIDENCIA(field, value):
    SE field == "Commit da implementação":
        SE value CORRESPONDE ^[0-9a-f]{7,64}$:
            RETORNAR CheckResult("", OK, "", code="ok")
        SENÃO:
            RETORNAR CheckResult("evidencia:Commit da implementação", ERRO, "commit deve ser hexadecimal entre 7 e 64 caracteres", code="invalid_commit_format")
    SE field == "Estado da integração":
        SE value CONTÉM "integrado" OU value CONTÉM "concluído" OU value CONTÉM "push direto":
            RETORNAR CheckResult("", OK, "", code="ok")
        SENÃO:
            RETORNAR CheckResult("evidencia:Estado da integração", AVISO, "formato não reconhecido; esperado: 'integrado na main via PR #X', 'concluído na branch X; ainda não integrado', etc.", code="integration_state_unrecognized")
    SE field == "Plataformas e versões validadas":
        SE value CONTÉM "Python":
            RETORNAR CheckResult("", OK, "", code="ok")
        SENÃO:
            RETORNAR CheckResult("evidencia:Plataformas e versões validadas", AVISO, "deve conter SO e versão Python", code="platforms_format_unrecognized")
    SE field == "Limitações do ambiente":
        SE value == "Nenhuma limitação conhecida" OU value CONTÉM "skip" OU value CONTÉM "indisponível":
            RETORNAR CheckResult("", OK, "", code="ok")
        SENÃO:
            RETORNAR CheckResult("", OK, "", code="ok")  # aceita qualquer texto não vazio
    SE field == "git diff --check":
        SE value == "sem avisos" OU value CONTÉM "aviso":
            RETORNAR CheckResult("", OK, "", code="ok")
        SENÃO:
            RETORNAR CheckResult("evidencia:git diff --check", AVISO, "formato não reconhecido", code="git_diff_check_format_unrecognized")
    SE field EM {"Testes direcionados", "Suíte completa", "Validação de sintaxe ou compileall", "Empacotamento", "CI"}:
        # Campos condicionais: aceitar "Não aplicável — justificativa" ou formato "comando → resultado"
        SE value CONTÉM "→":
            # Validar se resultado indica sucesso
            resultado_parte = value.DIVIDIR("→")[1].TRIM()
            SE resultado_parte CONTÉM "failed" OU resultado_parte CONTÉM "error" OU resultado_parte CONTÉM "Error":
                RETORNAR CheckResult("evidencia:" + field, ERRO, "resultado indica falha: " + resultado_parte, code="evidence_failed")
            SE resultado_parte CONTÉM "skipped" E NÃO value CONTÉM "Limitações":
                RETORNAR CheckResult("evidencia:" + field, AVISO, "skips detectados; registrar em Limitações do ambiente", code="evidence_skips")
            RETORNAR CheckResult("", OK, "", code="ok")
        SENÃO:
            RETORNAR CheckResult("evidencia:" + field, AVISO, "formato esperado: 'comando → resultado'", code="evidence_format_unrecognized")
    RETORNAR CheckResult("", OK, "", code="ok")

FUNÇÃO VALIDAR_EVIDENCIAS_SUBSTITUIDO(content, spec_id):
    results = []
    # Verifica referência substituta no cabeçalho ou Histórico de Alterações
    header = EXTRAIR_CABECALHO(content)
    history_section = EXTRAIR_SECAO(content, "Histórico de Alterações")
    substituida_por = EXTRAIR_SUBSTITUIDA_POR(header, history_section)
    SE substituida_por É NULO OU VAZIA:
        results.ADICIONAR(CheckResult("evidencia:substituida_por", ERRO,
                                     "referência à especificação substituta ausente (campo 'Substituída por' no cabeçalho ou Histórico de Alterações)",
                                     code="missing_superseded_by"))
    SENÃO:
        # Validar formato da referência (determinístico, somente leitura)
        SE substituida_por CORRESPONDE ^HERMES-\d{4}-.+$:
            results.ADICIONAR(CheckResult("evidencia:substituida_por", OK, "referência substituta presente: " + substituida_por, code="ok"))
        SENÃO:
            results.ADICIONAR(CheckResult("evidencia:substituida_por", ERRO,
                                         "formato de referência substituta inválido: " + substituida_por,
                                         code="invalid_superseded_by_format"))
    RETORNAR results

FUNÇÃO EXTRAIR_SUBSTITUIDA_POR(header, history_section):
    # Procura no cabeçalho: "> **Substituída por:** `HERMES-XXXX-...`"
    match = REGEX_SEARCH(Substituída por.*?`(HERMES-\d{4}-[^`]+)`, header)
    SE match: RETORNAR match.grupo(1)
    # Procura no Histórico de Alterações
    match = REGEX_SEARCH(Substituída por.*?(HERMES-\d{4}-[^\s\n]+), history_section)
    SE match: RETORNAR match.grupo(1)
    RETORNAR NULO

FUNÇÃO VALIDAR_CAMINHOS_FORMAIS(project_path, spec_files, test_markers):
    """Valida apenas campos formalmente definidos como caminhos usando core/paths.py.
    A função concreta (direct_project_path, resolve_directory, etc.) será definida
    na decisão arquitetural."""
    results = []
    # 1. Diretório de especificações
    specs_dir = project_path / "docs/hermes/specs"
    TRY:
        validated_specs_dir = VALIDAR_CAMINHO_CONTIDO(project_path, specs_dir)
        results.ADICIONAR(CheckResult("caminho:specs_dir", OK, "diretório de specs contido no projeto", code="ok"))
    CATCH PathResolutionError AS e:
        results.ADICIONAR(CheckResult("caminho:specs_dir", BLOCKED, "diretório de specs escapa do projeto: " + str(e), code="unsafe_path"))

    # 2. Cada arquivo de especificação
    PARA cada spec_file EM spec_files:
        TRY:
            validated_spec = VALIDAR_CAMINHO_CONTIDO(project_path, spec_file)
            results.ADICIONAR(CheckResult("caminho:spec_file", OK, "arquivo de spec contido no projeto", code="ok"))
        CATCH PathResolutionError AS e:
            results.ADICIONAR(CheckResult("caminho:spec_file", BLOCKED, "arquivo de spec escapa do projeto: " + str(e), code="unsafe_path"))

    # 3. Arquivos de teste referenciados nos marcadores
    PARA cada marker EM test_markers.VALORES():
        test_file = marker.arquivo_teste
        TRY:
            validated_test = VALIDAR_CAMINHO_CONTIDO(project_path, test_file)
            results.ADICIONAR(CheckResult("caminho:test_file", OK, "arquivo de teste contido no projeto", code="ok"))
        CATCH PathResolutionError AS e:
            results.ADICIONAR(CheckResult("caminho:test_file", BLOCKED, "arquivo de teste escapa do projeto: " + str(e), code="unsafe_path"))

    RETORNAR results
```

## Fluxo Principal

1. **Entrada**: `--project` (raiz do projeto), `--format` (text|json).
2. **Sanitizer**: criar `PublicSanitizer.for_project(project_path)` — **usado apenas na apresentação final dos resultados**.
3. **Localizar specs**: `project_path / "docs/hermes/specs"`; se não existe → **ERROR** `specs_dir_missing` (exit_code=1, para inspeção).
4. **Listar arquivos**: `*.md` ordenados alfabeticamente; excluir `README.md`, `TEMPLATE.md`.
5. **Extrair marcadores de testes**: varrer `tests/**/*.py` buscando `Spec: HERMES-XXXX / AC-NN`; indexar por `HERMES-XXXX/AC-NN` com campos estruturados: `arquivo_teste`, `linha`, `funcao`, `tipo`, `descricao`.
6. **Para cada arquivo de especificação** (em ordem):
   a. Ler conteúdo.
   b. Extrair `spec_id` do **nome do arquivo** (fonte autoritativa).
   c. Validar cabeçalho: deve conter mesmo `HERMES-NNNN`. Ausente ou divergente → **ERROR** (pula arquivo).
   d. Validar nome do arquivo (padrão HERMES-NNNN).
   e. Validar 19 seções obrigatórias do TEMPLATE + "Status" + "Resumo para o Responsável pelo Projeto".
   f. Validar Status (um dos 5 valores permitidos).
   g. Extrair ACs da seção "Critérios de Aceitação" (padrão `**AC-NN**: descrição`).
   h. Validar ACs: numeração sequencial 01, 02..., descrição não vazia.
   i. Para cada AC: verificar vínculo em marcadores de testes extraídos.
   j. Se Status = Implementado: validar seção Evidências com campos obrigatórios (lista a definir).
   k. Se Status = Substituído: validar referência substituta ("Substituída por" no cabeçalho ou Histórico). Não exige evidências de implementação.
   l. **Validar caminhos seguros**: apenas campos formalmente definidos como caminhos (arquivo do teste, arquivo da spec, diretório specs) via `core/paths.py`. Função concreta a definir na decisão arquitetural. **PublicSanitizer NÃO é usado para validação de caminho**.
7. **Agregar**: construir `Report` com todos os `CheckResult`.
8. **Saída**: `report.to_json(sanitizer)` ou `report.to_text(sanitizer)` no STDOUT — **aqui o PublicSanitizer é aplicado** para evitar exposição de caminhos locais.
9. **Retorno**: `report.exit_code` (precedência nativa: 0=OK/WARNING, 1=ERROR, 2=config_*, 3=BLOCKED, 4=external_failure).

## Casos de Erro e Limites

| Situação | Status | Código | Exit Code Isolado | Continua? |
|----------|--------|--------|-------------------|-----------|
| `--project` não existe / não é diretório | **DECISÃO PENDENTE** | **decisão pendente** | — | — |
| `docs/hermes/specs` não existe | ERROR | `specs_dir_missing` | 1 | **Para** |
| Nenhuma especificação real (só README/TEMPLATE) | WARNING | `no_specs_found` | 0 | Sim |
| Arquivo spec não segue `HERMES-NNNN-*.md` | ERROR | `invalid_filename_pattern` | 1 | **Pula arquivo** |
| Identificador duplicado entre specs | ERROR | `duplicate_spec_id` | 1 | Sim |
| Cabeçalho principal ausente ou sem HERMES-NNNN | ERROR | `missing_header_id` | 1 | **Pula arquivo** |
| ID no cabeçalho ≠ ID no nome do arquivo | ERROR | `header_filename_mismatch` | 1 | **Pula arquivo** |
| Seção obrigatória ausente (19 TEMPLATE + Status + Resumo) | ERROR | `missing_section` | 1 | Sim (por seção) |
| Status não está nos 5 permitidos | ERROR | `invalid_status` | 1 | Sim |
| AC duplicado | ERROR | `ac_duplicate` | 1 | Sim |
| AC fora de sequência (gap) | **DECISÃO PENDENTE** | **decisão pendente** | **decisão pendente** | Sim |
| AC com descrição vazia | ERROR | `ac_empty` | 1 | Sim |
| AC sem test_file nem justification (Aprovado, Em implementação, Implementado) | ERROR | `missing_test_or_justification` | 1 | Sim |
| Status = Implementado sem evidências mínimas | ERROR | `missing_evidence_field` | 1 | Sim |
| Status = Substituído sem referência substituta | ERROR | `missing_superseded_by` | 1 | Sim |
| Referência substituta com formato inválido | ERROR | `invalid_superseded_by_format` | 1 | Sim |
| Arquivo de teste referenciado inexistente | ERROR | `test_file_missing` | 1 | Sim |
| Função de teste referenciada inexistente | ERROR | `test_function_missing` | 1 | Sim |
| Referência de teste tenta escapar da raiz do projeto | BLOCKED | `unsafe_path` | 3 | **Para inspeção** |
| Caminho absoluto ou `..` em campo formal (arquivo spec, teste, specs_dir) | BLOCKED | `unsafe_path` | 3 | **Para inspeção** |
| Indireção insegura (symlink, junction, reparse point) em caminho formal | **DECISÃO PENDENTE** | **decisão pendente** | **decisão pendente** | **Para inspeção** |
| Erro de I/O ao ler arquivo (permissão, removido durante inspeção) | ERROR | `io_error` | 1 | **Pula arquivo** |
| Exceção interna inesperada / defeito do spec-check | — | `external_failure` | 4 | **Para execução** |
| **Schema TOML: `schema_version` ausente** | ERROR | `missing_schema_version` | 1 | **Pula arquivo** |
| **Schema TOML: `schema_version` tipo não inteiro** | ERROR | `invalid_schema_version_type` | 1 | **Pula arquivo** |
| **Schema TOML: `schema_version` zero ou negativo** | ERROR | `invalid_schema_version_value` | 1 | **Pula arquivo** |
| **Schema TOML: `schema_version` > 1** | ERROR | `unsupported_schema_version` | 1 | **Pula arquivo** |
| **Schema TOML: chave desconhecida nível superior** | ERROR | `unknown_field_toplevel` | 1 | **Pula arquivo** |
| **Schema TOML: chave desconhecida em acceptance_criteria** | ERROR | `unknown_field_ac` | 1 | **Pula arquivo** |
| **Schema TOML: chave desconhecida em evidence** | ERROR | `unknown_field_evidence` | 1 | **Pula arquivo** |
| **Schema TOML: tabela desconhecida** | ERROR | `unknown_table` | 1 | **Pula arquivo** |
| **Divergência: identificador TOML vs Markdown** | ERROR | `toml_markdown_id_mismatch` | 1 | **Pula arquivo** |
| **Divergência: status TOML vs Markdown** | ERROR | `toml_markdown_status_mismatch` | 1 | **Pula arquivo** |
| **Divergência: AC no TOML ausente no Markdown** | ERROR | `ac_missing_in_markdown` | 1 | Sim |
| **Divergência: AC no Markdown ausente no TOML** | ERROR | `ac_missing_in_toml` | 1 | Sim |
| **Divergência: AC duplicado** | ERROR | `ac_duplicate` | 1 | Sim |
| **Divergência: superseded_by divergente** | ERROR | `superseded_by_mismatch` | 1 | Sim |
| **Divergência: ordem dos ACs diferente** | ERROR | `ac_order_mismatch` | 1 | Sim |
| **Divergência: ID/status capitalização não canônica** | ERROR | `non_canonical_capitalization` | 1 | Sim |
| **Divergência: descrição humana AC vazia** | ERROR | `ac_empty_description` | 1 | Sim |
| **Divergência: cabeçalho Markdown ausente** | ERROR | `missing_header` | 1 | **Pula arquivo** |

## Critérios de Aceitação

- **AC-01**: Comando `spec-check` disponível no CLI junto a `doctor`, `worktree`, `preflight`.
- **AC-02**: Aceita `--project` (obrigatório) e `--format` (text|json, default text).
- **AC-03**: Processa apenas arquivos `.md` em `docs/hermes/specs/` (exclui README.md, TEMPLATE.md) em ordem alfabética.
- **AC-04**: Valida nome do arquivo: padrão `HERMES-NNNN-titulo-em-kebab-case.md` (NNNN = 4 dígitos). Falha → **ERROR** (exit_code=1, pula arquivo).
- **AC-05**: Valida cabeçalho principal: deve conter o mesmo `HERMES-NNNN` do nome do arquivo. Ausente ou divergente → **ERROR** (exit_code=1, pula arquivo). Sem fallback silencioso.
- **AC-06**: Valida 19 seções obrigatórias do TEMPLATE presentes + "Status" + "Resumo para o Responsável pelo Projeto". Falha → **ERROR** (exit_code=1, continua).
- **AC-07**: Valida Status: valor em {Rascunho, Aprovado, Em implementação, Implementado, Substituído}. Falha → **ERROR** (exit_code=1, continua).
- **AC-08**: Extrai ACs da seção "Critérios de Aceitação" no padrão `**AC-NN**: descrição`.
- **AC-09**: Valida ACs: numeração sequencial a partir de 01 (gap → **DECISÃO PENDENTE** — WARNING vs ERROR; status, código público e exit code: decisão pendente), descrição não vazia (vazia → **ERROR**, exit_code=1). AC duplicado → **ERROR** (exit_code=1).
- **AC-10**: Verifica vínculo AC → teste: busca marcador `Spec: HERMES-XXXX / AC-NN` em `tests/**/*.py`.
- **AC-11**: AC sem `test_file` segue a política formal de **justification por status** definida no Comportamento Desejado (seção "Política de `justification` por status"). Em resumo: **Rascunho** — `test_file` e `justification` opcionais, ambos podem estar ausentes; **Aprovado, Em implementação, Implementado** — exatamente um entre `test_file` e `justification` válida; **Substituído** — não exige novo vínculo de implementação. A validação verifica mutual exclusivity, formato da justification (3 elementos para Implementado), e existência do marcador nos testes quando `test_file` presente.
- **AC-12**: Se Status = Implementado, valida seção Evidências com os 11 campos padronizados. Cada campo deve ter valor concreto ou "Não aplicável — justificativa objetiva". Falha → **ERROR** (exit_code=1, continua). Valida: presença, não vazio, não marcador rejeitado, formato específico (commit hex 7-64, integração reconhecida, Python em plataformas, git diff --check "sem avisos" ou avisos, condicionais com "→" sem failed/error, skips justificados em Limitações). "Não aplicável" requer justificativa; "não executado" inválido; failed/errors não satisfazem Implementado.
- **AC-13**: Se Status = Substituído, valida referência explícita à especificação substituta (campo "Substituída por" no cabeçalho ou Histórico de Alterações). Não exige evidências de implementação. Falha → **ERROR** (exit_code=1, continua). Validação determinística e somente leitura.
- **AC-14**: Valida caminhos seguros: apenas valores formalmente definidos como caminhos (arquivo do teste, arquivo de especificação, diretório de especificações) passam por validação de contenção via `core/paths.py`; a função concreta será definida na decisão arquitetural. Campos como `commit`, `plataformas validadas`, `resultado de teste`, `comando` e texto descritivo **não** são caminhos. Referências de teste extraídas em campos estruturados: `arquivo_teste` (validado), `funcao`, `tipo`, `descricao`. URLs legítimas, texto explicativo e Markdown bruto **não** passam por validação de caminho. `PublicSanitizer` aplicado **somente na apresentação dos resultados** (saída texto/JSON) para evitar exposição de caminhos locais. Sanitização de saída não substitui validação de contenção. **Política de symlinks/junctions/reparse points: DECISÃO PENDENTE** para microbloco separado. O formato híbrido (front matter TOML + Markdown) é a base de validação; o Markdown ainda será inspecionado minimamente para cabeçalho principal, seções humanas obrigatórias, descrições dos ACs e validações cruzadas.
- **AC-15**: Saída texto determinística: uma linha por check (status, nome, mensagem), ordenada por arquivo e check; final `exit_code=N`.
- **AC-16**: Saída JSON determinística: `sort_keys=True`, `separators=(",", ":")`, sets ordenados, paths sanitizados.
- **AC-17**: Exit codes:
  - 0 = apenas OK e/ou WARNING (sem ERROR, BLOCKED, config_*, external_failure)
  - 1 = há ERROR (sem BLOCKED, config_*, external_failure)
  - 2 = há config_* não-OK (prevalece sobre ERROR)
  - 3 = há BLOCKED (prevalece sobre ERROR e config_*)
  - 4 = external_failure / forced_exit_code=4 (prevalece sobre tudo)
  - forced_exit_code, quando presente, mantém a precedência já implementada em `core/results.py`
- **AC-18**: Sem traceback em nenhum cenário: exceções capturadas no `main()` → `external_failure` (exit_code=4).
- **AC-19**: Comando é somente leitura: nenhum arquivo modificado, criado ou apagado.
- **AC-20**: Reutiliza infraestrutura existente: `Report`, `CheckResult`, `Status`, `PublicSanitizer`, `build_parser`.

## Plano de Testes

| Critério | Tipo de Teste | Arquivo | Nome do Teste | O que o Teste Comprova |
|----------|---------------|---------|---------------|------------------------|
| AC-01 | Integração | tests/test_cli.py | test_spec_check_command_exists | `spec-check` aparece no help e é despachado |
| AC-02 | Integração | tests/test_cli.py | test_spec_check_args | `--project` obrigatório, `--format` text\|json |
| AC-03 | Integração | tests/test_spec_check.py | test_spec_check_processes_only_md_files | Só .md em specs dir, exclui README/TEMPLATE, ordem alfabética |
| AC-04 | Unitário | tests/test_spec_check.py | test_validate_filename_pattern | Nomes válidos/inválidos → OK/ERROR |
| AC-05 | Unitário | tests/test_spec_check.py | test_validate_header_id_match | Cabeçalho coincide com nome; ausente/divergente → ERROR |
| AC-06 | Unitário | tests/test_spec_check.py | test_validate_required_sections | 19 seções + Status + Resumo checadas; ausente → ERRO por seção |
| AC-07 | Unitário | tests/test_spec_check.py | test_validate_status_values | 5 status válidos OK; inválido → ERRO |
| AC-08 | Unitário | tests/test_spec_check.py | test_extract_acs | Extrai ACs no formato **AC-NN**: desc |
| AC-09 | Unitário | tests/test_spec_check.py | test_validate_ac_sequential | Gap na numeração → **DECISÃO PENDENTE** (WARNING vs ERROR; status, código público e exit code: decisão pendente); descrição vazia → ERRO |
| AC-10 | Integração | tests/test_spec_check.py | test_validate_test_link_found | Marcador em teste → OK |
| AC-11 | Integração | tests/test_spec_check.py | test_validate_test_link_missing | Sem marcador → valida política de justification por status (Rascunho=opcional; Aprovado/Em impl/Implementado=exige um caminho; Substituído=opcional) |
| AC-12 | Unitário | tests/test_spec_check.py | test_validate_evidence_implemented | 11 campos padronizados checados; ausente/inválido/marcador rejeitado/formato inválido → **ERROR** |
| AC-13 | Unitário | tests/test_spec_check.py | test_validate_evidence_superseded | Referência substituta presente/ausente/inválida → OK/**ERROR** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_na_justification_required | "Não aplicável" sem justificativa → **ERROR** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_commit_format | commit hex 7-64 OK; inválido → **ERROR** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_integration_state | formato reconhecido OK; não reconhecido → **AVISO** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_platforms_format | contém "Python" OK; ausente → **AVISO** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_na_justification | "Não aplicável — justificativa" OK; sem justificativa → **ERROR** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_failed_result | resultado com "failed"/"error" → **ERROR** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_skips_registered | skips sem registrar em Limitações → **AVISO** |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_not_applicable_doc_only | doc-only usa "Não aplicável — justificativa" OK |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_branch_not_integrated | estado "concluído na branch X; ainda não integrado" OK |
| AC-12 | Unitário | tests/test_spec_check.py | test_evidence_main_integration | estado "integrado na main (push direto)" OK; PR "Não aplicável — integração sem PR" OK |
| AC-14 | Unitário | tests/test_spec_check.py | test_validate_formal_paths_only | Validação só em caminhos formais (spec_file, test_file, specs_dir) via core/paths.py; commit/plataforma/texto ignorados; PublicSanitizer só na saída |
| AC-15 | Integração | tests/test_spec_check.py | test_text_output_deterministic | Mesmo input → mesmo output texto ordenado |
| AC-16 | Integração | tests/test_spec_check.py | test_json_output_deterministic | Mesmo input → mesmo JSON (sort_keys, separators) |
| AC-17 | Integração | tests/test_spec_check.py | test_exit_codes | 0/1/2/3/4 conforme combinação de status |
| AC-18 | Integração | tests/test_cli.py | test_spec_check_no_traceback | Exceção no dispatch → exit_code=4, sem traceback |
| AC-19 | Integração | tests/test_spec_check.py | test_read_only_no_writes | Nenhum arquivo modificado durante execução |
| AC-20 | Unitário | tests/test_spec_check.py | test_reuses_existing_infrastructure | Usa Report, CheckResult, Status, PublicSanitizer |

**Testes planejados — Justification:**

| Cenário | O que Comprova |
|---------|----------------|
| Rascunho sem test_file e sem justification | Permitido (omissão de ambos) |
| Rascunho com test_file | Permitido |
| Rascunho com justification objetiva | Permitido |
| Rascunho com justification de adiamento inválida | ERROR (marcador rejeitado) |
| Aprovado com exatamente um caminho (test_file) | OK |
| Aprovado com exatamente um caminho (justification) | OK |
| Aprovado sem nenhum caminho | ERROR |
| Aprovado com ambos (test_file e justification) | ERROR (mutuamente exclusivos) |
| Em implementação — mesmos cenários de Aprovado | Mesma validação |
| Implementado com test_file | OK |
| Implementado com justification válida (3 elementos: razão, método, referência) | OK |
| Implementado com justification incompleta | ERROR |
| Substituído preservando vínculo histórico | Não exige justification nova |
| test_function sem test_file | ERROR |
| Cada marcador rejeitado (vazio, pendente, a fazer, depois, futuro, TBD, em andamento, não executado, N/A, não aplicável sem explicação, desconhecido, traço isolado) | ERROR |

**Testes planejados — Divergências TOML/Markdown:**

| Caso | O que Comprova |
|------|----------------|
| Identificador divergente | ERROR documental, exit code 1, pula arquivo |
| Status divergente | ERROR documental, exit code 1, pula arquivo |
| AC presente no TOML e ausente no Markdown | ERROR documental, exit code 1, continua |
| AC presente no Markdown e ausente no TOML | ERROR documental, exit code 1, continua |
| AC duplicado | ERROR documental, exit code 1, continua |
| superseded_by divergente | ERROR documental, exit code 1, continua |
| Ordem dos ACs diferente entre TOML e Markdown | ERROR documental, exit code 1, continua |
| ID ou status com capitalização não canônica | ERROR documental, exit code 1, continua |
| Descrição humana de AC vazia | ERROR documental, exit code 1, continua |
| Cabeçalho Markdown ausente | ERROR documental, exit code 1, pula arquivo |
| Confirmação: todos são ERROR documental | Status ERROR, não BLOCKED |
| Confirmação: exit code isolado 1 | exit_code=1 quando apenas esses erros |
| Confirmação: continuação dos demais documentos | Loop não para no primeiro erro |
| Ausência de prefixo config_ | Código não começa com config_ |
| Ausência de BLOCKED | Status não é BLOCKED |

**Testes planejados — Schema TOML versão 1 (fechado):**

| Caso | O que Comprova |
|------|----------------|
| Campo desconhecido no nível superior | ERROR documental |
| Campo desconhecido em acceptance_criteria | ERROR documental |
| Campo desconhecido em evidence | ERROR documental |
| Tabela desconhecida | ERROR documental |
| schema_version ausente | ERROR documental |
| schema_version com tipo diferente de inteiro | ERROR documental |
| schema_version zero | ERROR documental |
| schema_version negativo | ERROR documental |
| schema_version = 1 | OK |
| schema_version maior que 1 (ex.: 2) | ERROR documental, versão não suportada, pula documento, continua demais |
| TOML com chave duplicada | ERROR geral de parsing (invalid_hybrid_format) |
| Confirmação: versão futura não é interpretada parcialmente | Não valida campos conhecidos da v1 em doc v2 |

## Arquivos Provavelmente Afetados
|
| Caminho | Nota |
|---------|------|
| `src/hermes_ops/cli.py` | Integração provável: adicionar subparser `spec-check` e dispatch |
| `src/hermes_ops/commands/spec_check.py` | **Arquitetura provável/recomendada, sujeita à decisão arquitetural**: possível novo módulo com função principal |
| `src/hermes_ops/core/results.py` | Reutilização provável (sem alteração) |
| `src/hermes_ops/core/presentation.py` | Reutilização provável (sem alteração) |
| `tests/test_cli.py` | Testes de CLI para `spec-check` |
| `tests/test_spec_check.py` | **Arquitetura provável/recomendada, sujeita à decisão arquitetural**: possível novo arquivo com testes |
| `docs/hermes/specs/README.md` | Pode precisar atualizar seção "Quando Criar uma Especificação" |
| `docs/hermes/specs/TEMPLATE.md` | Pode precisar nota sobre validação automática |

**Nota**: Nomes de módulos, funções e assinaturas (ex.: `run_spec_check(project) -> Report`) são hipóteses de trabalho, não contrato aprovado. A arquitetura final será definida na decisão arquitetural.

## Decisões Tomadas
||
| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| 2026-07-30 | 19 seções obrigatórias (todas do TEMPLATE) | O TEMPLATE define estrutura canônica; validar todas garante consistência | Validar apenas subset "crítico" |
| 2026-07-30 | Status = Implementado exige evidências; Substituído exige referência substituta | Implementado comprova entrega; Substituído documenta sucessão sem duplicar evidências | Exigir evidências idênticas para ambos |
| 2026-07-30 | Identificador autoritativo = nome do arquivo; cabeçalho deve coincidir | Nome controla ordenação e rastreabilidade; cabeçalho valida consistência | Cabeçalho como fonte primária |
| 2026-07-30 | Busca marcadores `Spec: HERMES-XXXX / AC-NN` em todo `tests/**/*.py` | Simples, não depende de execução de testes, funciona offline | Rodar pytest e inspecionar resultados |
| 2026-07-30 | Validação de caminho: apenas campos formalmente definidos como caminhos (arquivo do teste, arquivo da spec, diretório specs) via `core/paths.py`. PublicSanitizer **apenas** na apresentação final (saída). | Separa validação de contenção/segurança de sanitização de exposição; evita falsos positivos em commit/plataforma/texto; função concreta de `core/paths.py` a definir na decisão arquitetural | Usar PublicSanitizer para validar campos como commit/plataforma; sanitizar conteúdo bruto inteiro |
| 2026-07-30 | Exit_code precedência: config_* não-OK(2) > BLOCKED(3) > ERROR(1) > WARNING/OK(0); external_failure/forced_exit_code=4 prevalece sobre tudo | Alinhado com `Report.exit_code` existente; config_* prevalece sobre BLOCKED; external_failure/forced_exit_code=4 prevalece sobre tudo | Nova precedência customizada |
| 2026-07-30 | Comando somente leitura, sem side effects | Segurança; alinhado com `doctor`/`worktree`/`preflight` | Permitir --fix para correções automáticas |
| 2026-07-30 | Especificações com status Implementado exigem evidências mínimas (11 campos padronizados, 6 sempre-obrigatórios) | Garante rastreabilidade e qualidade | Não exigir evidências |
| 2026-07-31 | Formato híbrido: front matter TOML + Markdown | TOML para dados validáveis machine-readable; Markdown para leitura humana; `tomllib` da stdlib Python 3.11+; delimitadores `+++`; sem dependências extras | Markdown puro com parsing complexo; front matter YAML (PyYAML); formato totalmente estruturado (JSON/TOML sem Markdown) |

## Decisões Pendentes Antes da Implementação
|||
| Assunto | Detalhes Pendentes |
|---------|-------------------|
| AC fora de sequência (gap) | WARNING vs ERROR; severidade; exit code; código público |
| Markdown desconhecido em `docs/hermes/specs/` | Arquivos B (auxiliares/desconhecidos): ignorar, WARNING ou ERROR |
| Política de symlinks, junctions, reparse points | Se toda indireção será rejeitada; se indireções internas contidas poderão ser aceitas; função concreta de core/paths.py; status, código e comportamento exatos |
| Arquitetura dos módulos do spec-check | Nomes definitivos de módulos, funções, assinaturas (ex.: `run_spec_check`), separação entre leitura e validação |
| Função concreta de core/paths.py | Função existente a reutilizar (direct_project_path, resolve_directory, etc.); composição; necessidade de nova função |
| Classificação de raiz inválida (--project) | Depende da política pública existente de CLI e caminhos; exit code; comportamento |
| Formato estruturado adicional para evidência manual | Estrutura padronizada além de texto livre para justification/validação manual |

**Nota**: Estas decisões NÃO estão autorizadas neste microbloco. Serão resolvidas em microblocos próprios ou na decisão arquitetural.

## Alternativas Descartadas

1. **Validar semântica do pseudocódigo**: Exigiria IA/parser complexo; fora do escopo "estrutural".
2. **Verificar sequencialidade global NNNN (sem gaps)**: Requer estado global; specs podem ser removidas; apenas formato individual.
3. **Executar testes para validar vínculos**: Lento, exige ambiente, flaky; marcador estático é suficiente.
4. **Auto-corrigir (--fix)**: Viola "somente leitura"; risco de corrupção; usuário corrige manualmente.
5. **Validar arquivos fora de `docs/hermes/specs/`**: Escopo deliberadamente restrito.
6. **Novo módulo de resultados**: Reutiliza `Report`/`CheckResult`/`Status` existentes; evita duplicação.

## Riscos Restantes

- **Falsos negativos em vínculos AC→teste**: Se teste usa formato diferente do marcador (ex.: `Spec: HERMES-0002/AC-01` sem espaços), não detecta. Mitigação: documentar formato exato no TEMPLATE.
- **Seções com headings variados**: Validação busca heading markdown case-insensitive; pode falhar se seção usa `###` em vez de `##`. Mitigação: regex flexível `^#{2,3}\s+<section>`.
- **Evidências em formato tabela vs lista**: Validação procura campo na seção; tabela markdown com `| Campo | Valor |` funciona; lista `- Campo: valor` também. Regex tolera ambos.
- **Performance em projetos com muitas specs/testes**: Leitura de todos os arquivos de teste a cada execução. Aceitável para CLI pontual; pode cachear no futuro.
- **Encoding de arquivos**: Usa UTF-8; arquivos em outro encoding podem falhar. Mitigação: `errors="replace"` na leitura.

## Evidências da Implementação
|
| Campo | Valor |
|-------|-------|
| Commit | `hash` |
| Estado da integração | `ex.: integrado na main via PR #1` |
| Arquivos alterados | `lista dos arquivos` |
| Testes direcionados | `comando` → `resultado` |
| Suíte completa | `comando` → `resultado` |
| compileall | `comando` → `resultado` |
| Empacotamento | `comando` → `resultado` |
| git diff --check | `resultado` |
| Plataformas validadas | `SO / Python version` |
| CI | `ex.: 8 checks aprovados` |
| Limitações do ambiente | `ex.: symlinks indisponíveis no Windows CI` |

## Histórico de Alterações
||
| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| 2026-07-30 | Danilo Fukuda | Criação da especificação HERMES-0002 | — |
| 2026-08-04 | Danilo Fukuda | Aprovação formal da especificação HERMES-0002 | Auditoria final concluída (0 bloqueadores) |
