+++
id = "HERMES-0008"
title = "Code audit read-only com evidências"
status = "Implementado"
owners = ["Danilo"]
created = "2026-08-11"
updated = "2026-08-11"
supersedes = []
related = ["HERMES-0004", "HERMES-0005", "HERMES-0006", "HERMES-0007"]

[[acceptance_criteria]]
id = "AC-01"
test = "tests/test_code_audit.py::test_code_audit_manifest_is_passive_read_only_and_requires_no_runtime_capability"

[[acceptance_criteria]]
id = "AC-02"
test = "tests/test_code_audit.py::test_code_audit_is_dispatched_only_by_its_exact_identifier"

[[acceptance_criteria]]
id = "AC-03"
test = "tests/test_code_audit.py::test_scanner_reads_only_explicitly_allowed_code_extensions"

[[acceptance_criteria]]
id = "AC-04"
test = "tests/test_code_audit.py::test_scanner_orders_paths_and_findings_deterministically"

[[acceptance_criteria]]
id = "AC-05"
test = "tests/test_code_audit.py::test_scanner_prunes_only_the_documented_excluded_directories"

[[acceptance_criteria]]
id = "AC-06"
test = "tests/test_code_audit.py::test_file_count_limit_blocks_without_partial_result"

[[acceptance_criteria]]
id = "AC-07"
test = "tests/test_code_audit.py::test_individual_file_size_limit_blocks_without_partial_result"

[[acceptance_criteria]]
id = "AC-08"
test = "tests/test_code_audit.py::test_total_byte_limit_blocks_without_partial_result"

[[acceptance_criteria]]
id = "AC-09"
test = "tests/test_code_audit.py::test_directory_count_and_depth_limits_block"

[[acceptance_criteria]]
id = "AC-10"
test = "tests/test_code_audit.py::test_all_reported_paths_are_relative_normalized_and_contained"

[[acceptance_criteria]]
id = "AC-11"
test = "tests/test_code_audit.py::test_indirect_target_root_is_rejected"

[[acceptance_criteria]]
id = "AC-12"
test = "tests/test_code_audit.py::test_descendant_symlink_or_reparse_point_blocks_the_scan"

[[acceptance_criteria]]
id = "AC-13"
test = "tests/test_code_audit.py::test_binary_candidate_blocks_without_exposing_content"

[[acceptance_criteria]]
id = "AC-14"
test = "tests/test_code_audit.py::test_non_utf8_candidate_blocks_without_partial_result"

[[acceptance_criteria]]
id = "AC-15"
test = "tests/test_code_audit.py::test_unreadable_or_concurrently_changed_candidate_blocks"

[[acceptance_criteria]]
id = "AC-16"
test = "tests/test_code_audit.py::test_audit_never_imports_parses_by_execution_or_calls_project_code"

[[acceptance_criteria]]
id = "AC-17"
test = "tests/test_code_audit.py::test_audit_uses_no_subprocess_shell_or_git_command"

[[acceptance_criteria]]
id = "AC-18"
test = "tests/test_code_audit.py::test_audit_opens_no_path_for_writing"

[[acceptance_criteria]]
id = "AC-19"
test = "tests/test_code_audit.py::test_audit_attempts_no_network_access"

[[acceptance_criteria]]
id = "AC-20"
test = "tests/test_code_audit.py::test_git_state_is_identical_before_and_after_audit"

[[acceptance_criteria]]
id = "AC-21"
test = "tests/test_code_audit.py::test_finding_model_is_immutable_and_rejects_invalid_values"

[[acceptance_criteria]]
id = "AC-22"
test = "tests/test_code_audit.py::test_every_finding_has_required_evidence_and_remediation_fields"

[[acceptance_criteria]]
id = "AC-23"
test = "tests/test_code_audit.py::test_finding_distinguishes_observation_from_hypothesis"

[[acceptance_criteria]]
id = "AC-24"
test = "tests/test_code_audit.py::test_no_finding_is_emitted_without_a_local_rule_trigger"

[[acceptance_criteria]]
id = "AC-25"
test = "tests/test_code_audit.py::test_evidence_is_bounded_sanitized_and_secret_values_are_redacted"

[[acceptance_criteria]]
id = "AC-26"
test = "tests/test_code_audit.py::test_closed_initial_rule_set_emits_expected_findings"

[[acceptance_criteria]]
id = "AC-27"
test = "tests/test_code_audit.py::test_comments_examples_and_ordinary_strings_do_not_create_findings"

[[acceptance_criteria]]
id = "AC-28"
test = "tests/test_code_audit.py::test_clean_fixture_returns_passed_without_invented_findings"

[[acceptance_criteria]]
id = "AC-29"
test = "tests/test_code_audit.py::test_finding_limit_blocks_instead_of_truncating_silently"

[[acceptance_criteria]]
id = "AC-30"
test = "tests/test_code_audit.py::test_structural_failure_returns_no_partial_findings"

[[acceptance_criteria]]
id = "AC-31"
test = "tests/test_cli.py::test_skill_run_code_audit_text_contract"

[[acceptance_criteria]]
id = "AC-32"
test = "tests/test_cli.py::test_skill_run_code_audit_json_contract"

[[acceptance_criteria]]
id = "AC-33"
test = "tests/test_cli.py::test_code_audit_adds_no_public_operational_option"

[[acceptance_criteria]]
id = "AC-34"
test = "tests/test_cli.py::test_code_audit_cli_never_exposes_absolute_or_unsafe_paths"

[[acceptance_criteria]]
id = "AC-35"
test = "tests/test_cli.py::test_code_audit_exit_status_distinguishes_clean_findings_and_failure"

[[acceptance_criteria]]
id = "AC-36"
test = "tests/test_code_audit.py::test_code_audit_ignores_target_skills_and_preserves_exact_lookup"

[[acceptance_criteria]]
id = "AC-37"
test = "tests/test_code_audit.py::test_git_preflight_contract_is_unchanged_after_code_audit"

[[acceptance_criteria]]
id = "AC-38"
test = "tests/test_code_audit.py::test_code_audit_rejects_linked_worktree_without_mutation"

[[acceptance_criteria]]
id = "AC-39"
test = "tests/test_packaging.py::test_wheel_contains_complete_canonical_code_audit_skill"

[[acceptance_criteria]]
id = "AC-40"
test = "tests/test_packaging.py::test_sdist_contains_complete_canonical_code_audit_skill"

[[acceptance_criteria]]
id = "AC-41"
test = "tests/test_skill_catalog.py::test_installed_catalog_resolution_does_not_depend_on_one_skill_anchor"

[[acceptance_criteria]]
id = "AC-42"
justification = "Aceitação real executada externamente após a suíte; o teste automatizado portátil não pode depender de um clone de consumidor."
+++

# HERMES-0008 - Code audit read-only com evidências

## Status

Implementado e validado em 2026-08-11.

## Resumo para o Responsável

O Hermes já consegue carregar uma skill de seu catálogo próprio e executá-la
contra um projeto-alvo externo. A próxima capacidade proposta é `code-audit`:
uma auditoria estática, delimitada, determinística e estritamente somente
leitura sobre arquivos de código do `TARGET`.

A interface pública permanece simples:

```powershell
python -m hermes_ops skill run code-audit `
  --project "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" `
  --format text
```

`--project` continua significando exclusivamente o projeto-alvo. A definição
passiva da skill vem do catálogo canônico instalado do Hermes, conforme a
HERMES-0007. O alvo não precisa e não deve fornecer uma pasta `skills/`.

O primeiro escopo não pretende ser um analisador semântico completo nem usar
um modelo de linguagem. Ele aplica um conjunto pequeno e fechado de regras
estáticas sobre texto de código permitido. Cada achado precisa apontar uma
evidência local verificável. Quando o contexto não permite uma conclusão, o
resultado é explicitamente marcado como hipótese. A ausência de gatilho não
autoriza inventar um problema.

Os limites iniciais são fixos e fazem parte do contrato. Ultrapassá-los,
encontrar uma indirection insegura, não conseguir ler integralmente um arquivo
candidato ou observar uma mudança concorrente bloqueia a auditoria inteira.
Não há resultado parcial apresentado como auditoria completa.

## 1. Contexto

As HERMES-0004, HERMES-0005 e HERMES-0006 introduziram, respectivamente:

1. descoberta estrita e atômica de skills passivas;
2. policy e planejamento explícitos, sem execução implícita;
3. execução literal e fechada de `git-preflight`, com evidências imutáveis.

A HERMES-0007 separou o catálogo próprio do Hermes do projeto-alvo. Hoje o
fluxo público resolve o catálogo instalado, faz lookup exato do `skill_id` e
passa o `TARGET` validado ao handler conhecido pelo dispatcher.

A arquitetura atual também impõe três limites relevantes para esta proposta:

- o dispatcher conhece somente `git-preflight` e rejeita qualquer outro ID;
- `SkillExecutionResult` e `SkillExecutionEvidence` são modelos genéricos e
  não representam, por si sós, arquivo, região, severidade e hipótese;
- o empacotamento e uma âncora da resolução do catálogo estão materialmente
  ligados ao diretório de `git-preflight`.

Portanto, adicionar `code-audit` exige uma segunda entrada passiva no catálogo,
um segundo handler literal, modelos próprios de auditoria e empacotamento que
prove a presença integral das duas skills. Isso deve ocorrer sem transformar
Markdown em código, sem descoberta dinâmica de handlers e sem ampliar o
significado de `--project`.

## 2. Problema Confirmado

O Hermes ainda não possui uma operação que percorra código-fonte de um alvo
externo e produza achados técnicos estruturados com evidência, mantendo um
contrato verificável de não mutação.

Fazer essa leitura sem um contrato explícito criaria riscos importantes:

- escapar do alvo por symlink, junction, mount point ou outro reparse point;
- consumir árvores ou arquivos sem limite;
- ler conteúdo binário, secreto ou não relacionado ao escopo;
- executar importações, hooks, compiladores, linters ou shell do projeto;
- apresentar inferências como fatos;
- omitir silenciosamente partes que não puderam ser auditadas;
- expor paths absolutos ou valores sensíveis na saída;
- alterar o Git ou o filesystem durante uma operação declarada read-only.

## 3. Explicação em Linguagem Simples

O Hermes caminhará somente dentro da pasta indicada por `--project`. Ele
considerará apenas extensões de código conhecidas, ignorará diretórios
documentados como dependências ou artefatos e parará se a árvore ultrapassar
limites de segurança.

Antes de abrir qualquer arquivo candidato, o Hermes confirma que o caminho é
um arquivo regular e não é um atalho ou redirecionamento. O arquivo é lido uma
única vez, com teto de bytes e UTF-8 estrito. O Hermes não importa o módulo,
não chama ferramentas do projeto e não executa nenhum trecho encontrado.

Regras estáticas fechadas procuram sinais específicos. Um achado contém o
caminho relativo, a região, um trecho curto, a explicação do risco e uma
sugestão. O trecho comprova o que foi observado; a classificação informa se a
conclusão é um fato local ou uma hipótese que precisa de validação humana.

Se uma parte que deveria ser auditada não puder ser verificada com segurança,
o Hermes falha fechado. Ele não diz que a auditoria passou sobre um conjunto
incompleto.

## 4. Comportamento Atual

O comando público existente é:

```text
python -m hermes_ops skill run <skill_id> --project <TARGET> --format text|json
```

No estado anterior a esta especificação:

1. `--project` é resolvido como o alvo exato;
2. o catálogo canônico é resolvido a partir da instalação/root do Hermes;
3. `discover_skills(root)` permanece disponível para descoberta explícita;
4. o registry faz lookup exato e atômico;
5. a policy bloqueia escrita e capacidades não permitidas;
6. o dispatcher possui somente o handler literal de `git-preflight`;
7. qualquer outro ID válido, incluindo `code-audit`, é não suportado;
8. wheel e sdist transportam somente a skill canônica existente.

Não há hoje scanner de código, regra de auditoria nem modelo de achado.

## 5. Comportamento Desejado

### 5.1 Interface pública

A invocação será exatamente:

```text
python -m hermes_ops skill run code-audit --project <TARGET> --format text|json
```

Não será criado `--skills-root`, `--include`, `--exclude`, `--rule`,
`--max-size`, `--mission` ou outro parâmetro operacional nesta versão.

`--project` representa exclusivamente o diretório-alvo. O catálogo pertence ao
Hermes. `TARGET/skills`, se existir, não participa da resolução e não pode
sobrescrever `code-audit`.

### 5.2 Definição passiva da skill

O catálogo canônico terá uma entrada direta:

```text
skills/
  code-audit/
    SKILL.md
```

O manifesto seguirá o mesmo contrato passivo já validado pelo loader:

```toml
id = "code-audit"
version = 1
status = "active"
risk = "low"
requires = []
allows_write = false
```

`requires` é vazio porque a leitura usa somente APIs locais da biblioteca
padrão. A skill não requer Git para funcionar e seu handler não executa Git.
O snapshot Git do dogfooding é uma verificação externa ao handler.

O Markdown descreve a operação, mas não escolhe nem carrega código. O
dispatcher terá um ramo literal `code-audit -> handler conhecido`. IDs
desconhecidos continuam bloqueados.

### 5.3 Resultado da execução

Uma execução completa possui um dos resultados:

| Situação | `status` | `exit_code` | Significado |
|---|---|---:|---|
| varredura completa, zero achados | `passed` | `0` | nenhum gatilho das regras iniciais foi observado |
| varredura completa, um ou mais achados | `completed_with_findings` | `3` | auditoria terminou e exige revisão |
| alvo, catálogo, path, limite ou leitura inválidos | erro fechado | `3` | auditoria não foi concluída |

O código `0` não significa ausência universal de vulnerabilidades. Significa
apenas que a varredura cobriu integralmente seu escopo e não encontrou gatilhos
do conjunto fechado desta versão.

Achados não são falhas internas, mas usam `exit_code=3` para que automações não
os ignorem acidentalmente. Erros fechados não retornam achados parciais.

### 5.4 Determinismo

Com os mesmos bytes, metadata estável, plataforma e versão do Hermes, a ordem
e o conteúdo lógico da saída devem ser os mesmos.

Arquivos serão ordenados pelo path relativo normalizado em POSIX, com ordenação
ordinal. Achados serão ordenados por:

1. path relativo;
2. linha inicial;
3. coluna inicial;
4. `rule_id`;
5. índice estável dentro da regra.

Timestamps, duração, paths absolutos e dados aleatórios não fazem parte do
resultado público.

## 6. Fora do Escopo

Esta versão não inclui:

- execução, importação, build ou teste do projeto-alvo;
- AST completa para todas as linguagens;
- ferramentas externas como linters, compiladores ou scanners;
- shell, PowerShell, `cmd`, subprocessos ou comandos Git pelo handler;
- rede, APIs remotas, LLMs, RAG ou consulta de vulnerabilidades;
- leitura de histórico Git, branches, commits ou conteúdo remoto;
- correção automática ou edição sugerida aplicada ao disco;
- configuração de regras ou limites pelo projeto consumidor;
- leitura de `.env`, credenciais, certificados, bancos ou arquivos de dados;
- auditoria de dependências por lockfiles ou manifests;
- garantia de ausência de vulnerabilidades;
- conhecimento específico de Lucre Agro, WhatsApp ou outro consumidor;
- seleção de arquivos por linguagem natural ou uma opção `--mission`;
- plugins, handlers declarados no Markdown ou imports dinâmicos;
- mudança no contrato de `git-preflight`;
- commit, push, checkout, switch, reset, stage ou alteração de branch.

A missão de dogfooding sobre o lote documental do WhatsApp orienta a revisão
humana do resultado real; ela não adiciona regras específicas de cliente ao
produto genérico.

## 7. Invariantes e Regras de Segurança

### 7.1 Origem da skill e despacho

- A skill vem somente do catálogo canônico do Hermes.
- Não existe busca em CWD, `TARGET`, ancestrais, siblings, home ou `PATH`.
- O lookup de `code-audit` é exato.
- `TARGET/skills/code-audit` é conteúdo comum do alvo e não é catálogo.
- Catálogo ausente, ambíguo, inseguro ou inválido bloqueia antes do handler.
- O dispatcher é uma tabela literal fechada mantida no código confiável.
- O conteúdo de `SKILL.md` nunca é executado.

### 7.2 Somente leitura

- O handler abre arquivos somente em modo binário de leitura.
- O handler não cria arquivos temporários, caches, logs ou relatórios no alvo.
- O handler não altera atime de forma prometida: a leitura pode atualizar
  metadados de acesso conforme o filesystem. O contrato de não mutação cobre
  conteúdo, nomes, árvore e estado Git controlado; atime é um risco conhecido.
- Nenhum path é aberto com intenção de escrita, append, criação ou exclusão.
- Nenhum código do alvo é importado, avaliado, compilado ou chamado.
- Nenhum subprocesso, shell, comando Git ou acesso de rede é permitido.
- HEAD, refs, index/staging, branch e working tree devem permanecer idênticos.

### 7.3 Fail closed

O processo inteiro bloqueia, sem achados parciais, quando:

- o alvo não existe, não é diretório ou é indireto;
- qualquer ancestral entre a âncora validada e o alvo é indireto;
- uma entrada encontrada na árvore é symlink ou reparse point;
- um path resolve ou aponta para fora do alvo;
- não é possível classificar com segurança uma entrada;
- um arquivo candidato não é regular;
- um limite de diretórios, profundidade, arquivos, bytes ou achados é excedido;
- um candidato é grande demais, binário, não UTF-8 ou ilegível;
- o arquivo muda entre as verificações de identidade;
- uma regra ou modelo tenta produzir valor fora do contrato;
- ocorre erro inesperado durante enumeração, leitura ou análise.

Diretórios excluídos ainda são classificados por `lstat` antes de serem
podados. Portanto, um diretório excluído que seja symlink/reparse point também
bloqueia; ele não é seguido.

### 7.4 Ausência de promessas indevidas

- Um achado precisa de gatilho local e evidência reproduzível.
- A ausência de achado não é uma certificação de segurança.
- Não são emitidos achados baseados apenas em ausência presumida de validação,
  nome de arquivo, nome de projeto ou contexto de negócio inferido.
- Comentários, exemplos documentais e texto comum dentro de strings não podem
  ser apresentados como chamadas executáveis.
- Se o reconhecedor não consegue distinguir código de comentário/string com
  confiança, ele não emite o achado.
- Hipóteses usam linguagem condicional e pedem confirmação humana.
- Valores que se pareçam com segredos nunca aparecem integralmente na saída.

## 8. Contrato de Entrada

### 8.1 Entrada pública

| Campo | Tipo | Obrigatório | Regra |
|---|---|---:|---|
| `skill_id` | texto | sim | deve ser exatamente `code-audit` |
| `--project` | path | sim | raiz exata, existente, direta e local do alvo |
| `--format` | enum | não | `text` por padrão; também aceita `json` |

Não há entrada vinda do conteúdo executável do projeto. Configurações do alvo
não podem ampliar extensões, limites ou regras.

### 8.2 Extensões permitidas

O conjunto inicial, exato e case-sensitive é:

```text
.py
.pyi
.js
.jsx
.mjs
.cjs
.ts
.tsx
```

Uma extensão em maiúsculas ou não listada não é candidata. Esta decisão evita
tratar arquivos de dados, ambiente, chaves e formatos desconhecidos como
código. Ampliar a lista exige atualizar esta especificação e seus testes.

### 8.3 Diretórios excluídos

Em qualquer nível, os nomes diretos abaixo são podados depois da classificação
segura da entrada:

```text
.git
.hg
.svn
.venv
venv
node_modules
vendor
dist
build
coverage
__pycache__
.mypy_cache
.pytest_cache
.tox
.nox
```

A exclusão evita dependências vendorizadas, metadata de VCS, caches e produtos
gerados. Outros diretórios não são excluídos por heurística.

### 8.4 Limites fixos de leitura

| Limite | Valor inicial | Comportamento ao exceder |
|---|---:|---|
| profundidade, com `TARGET` em nível 0 | 32 | bloqueia |
| diretórios classificados | 5.000 | bloqueia |
| arquivos candidatos | 1.000 | bloqueia |
| bytes por arquivo candidato | 524.288 (512 KiB) | bloqueia |
| bytes totais de candidatos | 20.971.520 (20 MiB) | bloqueia |
| achados | 200 | bloqueia |
| linhas de evidência por achado | 8 | nunca excede |
| caracteres de evidência por achado | 1.200 | nunca excede |

Os limites são constantes do Hermes nesta versão e não podem ser relaxados
pelo alvo. Quantidades são verificadas antes de apresentar resultado. Um teto
de achados não causa truncamento silencioso: o resultado inteiro bloqueia.

## 9. Política de Paths

### 9.1 Raiz exata

O argumento recebido é a raiz exata. O scanner não procura repositórios,
configs ou diretórios pais. A validação conserva separadamente:

- o path fornecido/âncora, para inspecionar cada componente sem seguir
  redirecionamentos;
- o path absoluto canônico, apenas para comparações de contenção.

A raiz ou um ancestral inspecionado com symlink, junction, mount point inseguro
ou outro reparse point bloqueia. A implementação não deve tornar o path seguro
por primeiro chamar `resolve()` e esquecer como ele foi alcançado.

### 9.2 Descendentes

Cada entrada é examinada com metadata que não segue links. Antes de listar um
diretório ou abrir um arquivo:

1. confirmar que a entrada continua diretamente dentro do alvo;
2. rejeitar symlink;
3. no Windows, rejeitar qualquer reparse point;
4. aceitar somente diretório regular ou arquivo regular conforme o estágio;
5. manter o path relativo derivado da árvore já validada.

Não se usa glob recursivo que possa atravessar indirections. Não se segue
atalho nem para um destino interno.

### 9.3 Paths na saída

Somente paths relativos ao alvo aparecem em achados e erros públicos. Eles são
normalizados com `/`, não começam com `/`, não contêm drive, `..`, componentes
vazios ou caracteres de controle.

O sanitizador centralizado da CLI continua sendo a última barreira. O modelo
de auditoria deve rejeitar um path inválido antes da formatação.

### 9.4 Linked Git worktrees

Um linked worktree costuma representar `.git` como arquivo apontando para
metadata externa. `code-audit` não precisa de Git e não lê esse arquivo, mas a
execução pública deve preservar o contrato conservador existente: um alvo
identificado como layout Git indireto é bloqueado antes da leitura do código.

O teste prova bloqueio sem alteração de HEAD, refs, staging ou working tree.
Esta especificação não relaxa a decisão existente sobre worktrees.

## 10. Tratamento de Arquivos Binários, Grandes e Instáveis

### 10.1 Arquivos não candidatos

Arquivos com extensão não permitida são classificados com segurança e
ignorados sem leitura de conteúdo. Eles não contam no limite de candidatos ou
bytes. Uma indirection continua bloqueando mesmo que seu nome não seja
candidato.

### 10.2 Arquivos grandes

Um arquivo candidato cujo tamanho informado exceda 512 KiB bloqueia antes da
leitura. Se ele crescer durante a leitura, no máximo 512 KiB + 1 byte pode ser
lido para detectar o excesso; em seguida a auditoria bloqueia.

O tamanho real lido, e não apenas o tamanho inicial, participa do limite total.

### 10.3 Arquivos binários e encoding

Um candidato é binário quando contém byte NUL na amostra limitada inicial.
Ele bloqueia sem incluir bytes na mensagem de erro.

Texto deve ser UTF-8 estrito. Um BOM UTF-8 é aceito somente no início do
arquivo e removido para a análise. Sequência inválida bloqueia. Não há fallback
para encoding do sistema, detecção probabilística ou substituição de bytes.

### 10.4 Mudança concorrente

O scanner captura antes e depois da leitura, quando fornecidos pela plataforma:

- tipo;
- device e inode/file ID;
- tamanho;
- `mtime_ns`;
- `ctime_ns`.

Mudança de identidade ou metadata bloqueia. O arquivo é lido de forma limitada
e integral em memória somente dentro dos tetos definidos. Esta proteção reduz
TOCTOU, mas não promete detectar uma troca que preserve toda metadata; isso é
registrado como risco restante.

### 10.5 Erros de leitura

Permissão negada, sharing violation, arquivo removido, tipo especial, I/O
parcial ou qualquer exceção impede resultado completo. O erro público contém
somente código estável e path relativo seguro, nunca conteúdo do arquivo.

## 11. Modelo de Achados

### 11.1 Modelo imutável

Um achado é um valor imutável com os campos:

| Campo | Tipo | Contrato |
|---|---|---|
| `rule_id` | texto | ID estável do conjunto fechado |
| `severity` | enum | `info`, `low`, `medium`, `high`, `critical` |
| `classification` | enum | `observed` ou `hypothesis` |
| `file` | path relativo | POSIX, contido e sanitizado |
| `region` | região | linha inicial/final; colunas opcionais, base 1 |
| `evidence` | texto | trecho local curto, limitado e redigido |
| `observation` | texto | fato estritamente sustentado pela evidência |
| `justification` | texto | por que o fato pode representar risco |
| `suggestion` | texto | próxima ação segura, sem aplicá-la |

`region.start_line <= region.end_line`. Quando há colunas, elas também são
base 1 e ordenadas. O modelo rejeita enum inválido, path absoluto, região
inconsistente, texto vazio e evidência acima dos limites.

### 11.2 Fato observado e hipótese

`observed` é permitido somente quando a propriedade de risco está explícita
nos próprios bytes, por exemplo uma configuração literal que desabilita
verificação TLS.

`hypothesis` indica que o token existe, mas exploração, origem do dado ou
contexto de segurança precisam de confirmação. A observação permanece factual;
a justificativa usa termos como “pode” e descreve o dado faltante.

O modelo não possui classificação implícita. O formatador exibe esse campo em
texto e JSON.

### 11.3 Evidência e redação

Evidência:

- é derivada exclusivamente do arquivo e região reportados;
- contém no máximo 8 linhas e 1.200 caracteres;
- normaliza quebras de linha para `\n`;
- remove caracteres de controle não imprimíveis;
- não contém path absoluto;
- substitui o valor de possível segredo por `<redacted>`;
- mantém nome da variável e contexto mínimo necessário para justificar o
  gatilho;
- nunca inclui o arquivo completo.

Se a redação impedir comprovar o gatilho, o achado não é emitido. Segurança de
dado prevalece sobre volume de evidência.

### 11.4 Conjunto inicial fechado de regras

| ID | Gatilho conservador | Severidade | Classificação padrão |
|---|---|---|---|
| `CA001` | chamada de avaliação dinâmica (`eval`, `exec` ou construtor `Function`) em código ativo | high | hypothesis |
| `CA002` | chamada explícita de shell (`os.system`, subprocesso com `shell=True`, `child_process.exec` ou `execSync`) em código ativo | high | hypothesis |
| `CA003` | literal que desabilita validação TLS (`verify=False`, `rejectUnauthorized: false` ou equivalente fechado) | high | observed |
| `CA004` | literal não vazio atribuído a identificador sensível (`secret`, `token`, `password`, `api_key` ou `access_key`) | high | hypothesis |
| `CA005` | gerador não criptográfico usado na mesma expressão para identificador de segurança (`token`, `otp`, `nonce`, `secret`) | medium | hypothesis |

“Código ativo” significa que o reconhecedor conservador determinou que o
gatilho não está em comentário, docstring, string comum, fixture textual ou
exemplo documental. O reconhecedor pode deixar de emitir quando houver
ambiguidade; ele não pode promover texto ambíguo a fato.

As regras são implementadas como funções confiáveis literais. Não são regexes
fornecidas pelo projeto e não vêm de `SKILL.md`. Cada regra tem testes positivos,
negativos, de comentário/string, redação e limite.

O conjunto é deliberadamente pequeno. Uma nova regra, nova extensão ou nova
linguagem altera o contrato e exige revisão da especificação.

### 11.5 Resumo

Além dos achados, a evidência de execução contém um resumo imutável:

- quantidade de diretórios classificados;
- quantidade de arquivos candidatos lidos;
- bytes lidos;
- quantidade de achados por severidade;
- IDs e versão do conjunto de regras;
- limites efetivamente usados.

O resumo não lista arquivos ignorados e não expõe paths absolutos. Em erro
fechado, nenhum resumo de sucesso ou achado parcial é emitido.

## 12. Contrato de Saída

### 12.1 Texto

O formato textual mantém o envelope público de skills e acrescenta, por ramo
literal de `code-audit`, blocos determinísticos:

```text
Skill: code-audit
Status: completed_with_findings
Exit code: 3
Scanned files: 12
Scanned bytes: 34821
Findings: 1

[HIGH] CA003 observed
File: src/http/client.ts
Region: 42:5-42:30
Evidence: rejectUnauthorized: false
Justification: A validação TLS está explicitamente desabilitada.
Suggestion: Remover a desativação e usar uma cadeia de confiança válida.
```

Este exemplo demonstra forma, não afirma que o alvo real contém esse código.

### 12.2 JSON

O JSON preserva o envelope de `SkillExecutionResult`. A evidência
`code_audit_summary` contém o resumo e cada evidência `code_audit_finding`
contém todos os campos do modelo de achado. Arrays mantêm a ordem determinística.

Não se adicionam objetos arbitrários ou tipos não serializáveis ao envelope.
Nenhum campo contém path absoluto, traceback, representação de exceção ou
valor secreto.

### 12.3 Compatibilidade do modelo de execução

`SkillExecutionResult` não será alterado de forma incompatível. Os modelos
específicos de auditoria são convertidos para `SkillExecutionEvidence` no
boundary do handler. O formatador textual possui um ramo literal para
`code-audit`; outras skills conservam sua saída atual.

## 13. Pseudocódigo Independente de Linguagem

### 13.1 Resolução e despacho

```text
AO RECEBER "skill run code-audit --project TARGET":
    validar TARGET como diretório exato e direto
    SE TARGET for inválido:
        bloquear com erro estável

    localizar exclusivamente o catálogo instalado do Hermes
    validar o catálogo inteiro de forma atômica
    procurar exatamente "code-audit"
    aplicar policy explícita de baixo risco e sem escrita

    SE catálogo, skill ou policy forem inválidos:
        bloquear antes de ler código do TARGET

    escolher o handler literal conhecido de code-audit
    NÃO interpretar o Markdown como programa
    NÃO procurar outro handler ou catálogo
```

### 13.2 Construção segura do inventário

```text
VALIDAR_RAIZ(TARGET):
    inspecionar a forma como cada componente do path é alcançado
    rejeitar link, junction ou reparse point
    confirmar que TARGET é diretório regular existente
    definir TARGET como nível zero e limite absoluto de contenção

INVENTARIAR_DIRETORIO(DIRETORIO, NIVEL):
    SE NIVEL exceder 32:
        bloquear auditoria inteira

    contar o diretório
    SE a contagem exceder 5.000:
        bloquear auditoria inteira

    listar somente entradas diretas e ordenar pelo nome ordinal

    PARA CADA ENTRADA:
        obter metadata sem seguir links
        confirmar contenção dentro de TARGET

        SE for link ou reparse point:
            bloquear auditoria inteira

        SE for diretório:
            SE nome estiver na lista fechada de exclusões:
                não entrar
            SENÃO:
                inventariar recursivamente no próximo nível

        SENÃO SE for arquivo regular:
            SE extensão exata estiver na allowlist:
                adicionar como candidato
                SE candidatos excederem 1.000:
                    bloquear auditoria inteira

        SENÃO:
            bloquear porque o tipo não é seguro

    ao final, ordenar candidatos pelo path relativo normalizado
```

### 13.3 Leitura limitada

```text
PARA CADA ARQUIVO CANDIDATO:
    capturar identidade e metadata antes da leitura

    SE tamanho declarado exceder 512 KiB:
        bloquear auditoria inteira

    abrir somente para leitura binária, sem seguir indirection
    ler no máximo 512 KiB mais um byte

    SE houver byte excedente:
        bloquear auditoria inteira

    capturar identidade e metadata novamente
    SE arquivo mudou ou deixou de ser regular:
        bloquear auditoria inteira

    somar bytes realmente lidos
    SE total exceder 20 MiB:
        bloquear auditoria inteira

    SE houver byte NUL:
        bloquear sem expor conteúdo

    decodificar como UTF-8 estrito, aceitando BOM apenas no início
    SE decodificação falhar:
        bloquear sem resultado parcial
```

### 13.4 Análise e achados

```text
PARA CADA ARQUIVO DECODIFICADO NA ORDEM:
    identificar regiões de código com reconhecedor conservador da extensão

    PARA CADA REGRA DA LISTA FECHADA, EM ORDEM:
        procurar somente em regiões confirmadas como código ativo

        PARA CADA GATILHO CONFIRMADO:
            construir região exata e evidência local limitada
            redigir qualquer valor possivelmente secreto
            escrever observação que a evidência prova
            classificar como observado ou hipótese explicitamente
            anexar justificativa e sugestão fixas da regra
            validar o modelo imutável

            SE achados excederem 200:
                bloquear em vez de truncar

ordenar todos os achados pelo contrato determinístico

SE não houver achado:
    retornar passed e exit_code 0
SENÃO:
    retornar completed_with_findings e exit_code 3
```

### 13.5 Falha fechada

```text
SE qualquer etapa falhar:
    descartar inventário, resumo e achados parciais
    mapear a causa para código público estável
    sanitizar qualquer path ou detalhe
    retornar exit_code 3
    NÃO tentar fallback
    NÃO modificar TARGET
```

## 14. Fluxo Principal

1. A CLI valida sintaxe e formato.
2. O executor valida o projeto-alvo antes da execução.
3. O catálogo próprio é resolvido sem participação do alvo.
4. Registry, loader, planner e policy validam `code-audit` exatamente.
5. O dispatcher seleciona somente o handler literal de `code-audit`.
6. O handler valida a raiz sem apagar evidência de indirection.
7. A árvore é inventariada com `lstat`, contenção, exclusões e limites.
8. Candidatos são ordenados e lidos de forma binária e limitada.
9. Binary, encoding, tamanho, identidade e mudanças concorrentes são validados.
10. O conjunto fechado de regras analisa somente regiões reconhecidas como
    código ativo.
11. Modelos imutáveis validam e ordenam os achados.
12. O resultado genérico recebe resumo e achados estruturados.
13. A CLI formata texto ou JSON pelo sanitizador central.
14. Nenhuma etapa escreve, executa subprocesso ou acessa rede.

## 15. Casos de Erro e Limites

| Condição | Código estável proposto | Resultado |
|---|---|---|
| target ausente ou não diretório | erro existente de project root | bloqueia, 3 |
| target/ancestral indireto | `CODE_AUDIT_TARGET_INDIRECT` | bloqueia, 3 |
| linked worktree indireto | erro de segurança existente ou equivalente estável | bloqueia, 3 |
| catálogo canônico ausente/inseguro | erro existente de catálogo | bloqueia, 3 |
| `code-audit` ausente | `SKILL_NOT_FOUND` | bloqueia, 3 |
| skill/policy incompatível | erro existente de policy | bloqueia, 3 |
| entrada symlink/reparse | `CODE_AUDIT_UNSAFE_PATH` | bloqueia, 3 |
| escape de contenção | `CODE_AUDIT_PATH_ESCAPE` | bloqueia, 3 |
| tipo especial | `CODE_AUDIT_UNSAFE_FILE_TYPE` | bloqueia, 3 |
| profundidade excedida | `CODE_AUDIT_DEPTH_LIMIT_EXCEEDED` | bloqueia, 3 |
| diretórios excedidos | `CODE_AUDIT_DIRECTORY_LIMIT_EXCEEDED` | bloqueia, 3 |
| candidatos excedidos | `CODE_AUDIT_FILE_LIMIT_EXCEEDED` | bloqueia, 3 |
| arquivo acima de 512 KiB | `CODE_AUDIT_FILE_SIZE_EXCEEDED` | bloqueia, 3 |
| total acima de 20 MiB | `CODE_AUDIT_TOTAL_SIZE_EXCEEDED` | bloqueia, 3 |
| binário com extensão permitida | `CODE_AUDIT_BINARY_FILE` | bloqueia, 3 |
| UTF-8 inválido | `CODE_AUDIT_INVALID_ENCODING` | bloqueia, 3 |
| leitura negada/incompleta | `CODE_AUDIT_READ_FAILED` | bloqueia, 3 |
| arquivo mudou | `CODE_AUDIT_FILE_CHANGED` | bloqueia, 3 |
| mais de 200 achados | `CODE_AUDIT_FINDING_LIMIT_EXCEEDED` | bloqueia, 3 |
| modelo de achado inválido | `CODE_AUDIT_INVALID_FINDING` | bloqueia, 3 |
| formato CLI inválido | erro existente de CLI | bloqueia, 2 |

Mensagens públicas não incluem conteúdo do arquivo, path absoluto ou texto cru
da exceção. Erros preexistentes conservam seus códigos quando já representam a
mesma condição.

## 16. Critérios de Aceitação

### Contrato e arquitetura

- **AC-01:** o catálogo contém `code-audit` passiva, `active`, `risk=low`,
  `requires=[]` e `allows_write=false`.
- **AC-02:** somente o ID exato `code-audit` alcança seu handler literal; IDs
  próximos ou desconhecidos bloqueiam.
- **AC-03:** somente as oito extensões permitidas são abertas para conteúdo.
- **AC-04:** inventário e achados são determinísticos pelo contrato de ordem.
- **AC-05:** somente os nomes documentados de diretórios são podados; não há
  heurística silenciosa adicional.

### Limites e paths

- **AC-06:** o 1.001º candidato bloqueia sem resultado parcial.
- **AC-07:** candidato acima de 512 KiB ou que cresça além disso bloqueia.
- **AC-08:** total acima de 20 MiB bloqueia sem leitura ilimitada.
- **AC-09:** mais de 5.000 diretórios ou profundidade maior que 32 bloqueia.
- **AC-10:** todo path público é relativo, POSIX, contido e validado.
- **AC-11:** target ou ancestral indireto bloqueia antes da varredura.
- **AC-12:** symlink, junction ou reparse point descendente bloqueia e nunca é
  seguido, inclusive sob nome excluído.
- **AC-13:** arquivo binário com extensão permitida bloqueia sem vazar bytes.
- **AC-14:** arquivo candidato não UTF-8 bloqueia sem fallback de encoding.
- **AC-15:** arquivo ilegível, removido, trocado ou alterado durante a leitura
  bloqueia sem achados parciais.

### Não execução e não mutação

- **AC-16:** nenhum módulo, script, hook, configuração executável ou código do
  alvo é importado ou executado.
- **AC-17:** o handler não chama subprocesso, shell, Git ou ferramenta externa.
- **AC-18:** nenhum path é aberto para escrita e nenhum arquivo é criado,
  alterado, renomeado ou removido.
- **AC-19:** nenhuma tentativa de rede ocorre.
- **AC-20:** HEAD, working tree, staging e refs são byte a byte/logicamente
  idênticos antes e depois em repositório temporário controlado.

### Achados

- **AC-21:** achado, região e resumo são imutáveis e rejeitam estado inválido.
- **AC-22:** cada achado contém severidade, arquivo, região, evidência,
  observação, justificativa e sugestão não vazios.
- **AC-23:** cada achado declara `observed` ou `hypothesis`; a saída mostra a
  classificação sem inferi-la por texto livre.
- **AC-24:** nenhum achado existe sem um gatilho local de uma regra fechada.
- **AC-25:** evidência respeita 8 linhas/1.200 caracteres, caracteres seguros e
  redação de valores possivelmente secretos.
- **AC-26:** as cinco regras iniciais detectam seus casos positivos mínimos com
  severidade, classificação, região e mensagem esperadas.
- **AC-27:** comentários, docstrings, exemplos e strings comuns equivalentes aos
  gatilhos não produzem achado.
- **AC-28:** fixture limpa termina `passed`, código 0 e zero achados; o Hermes
  não cria um achado para preencher o relatório.
- **AC-29:** o 201º achado bloqueia; não há truncamento apresentado como sucesso.
- **AC-30:** qualquer erro estrutural descarta todos os achados já calculados.

### CLI, compatibilidade e packaging

- **AC-31:** a CLI textual exibe resumo e todos os campos de cada achado em
  ordem determinística.
- **AC-32:** a CLI JSON preserva o envelope existente e serializa resumo e
  achados completos em tipos JSON estáveis.
- **AC-33:** a CLI não ganha opção operacional nova nesta versão.
- **AC-34:** texto e JSON não expõem path absoluto, traceback, controle ou valor
  secreto.
- **AC-35:** clean retorna `passed/0`, achados retornam
  `completed_with_findings/3` e falha fechada retorna erro/3.
- **AC-36:** `TARGET/skills` não participa da resolução nem causa shadowing; o
  lookup continua exato no catálogo próprio.
- **AC-37:** todos os contratos e testes de `git-preflight` permanecem
  inalterados e passando.
- **AC-38:** linked worktree é bloqueado conforme o contrato conservador
  existente, sem mutação Git.
- **AC-39:** wheel contém o `SKILL.md` completo de `code-audit` no catálogo
  canônico e a instalação isolada consegue resolvê-lo.
- **AC-40:** sdist contém o mesmo artefato e um wheel reconstruído do sdist
  conserva o catálogo.
- **AC-41:** a resolução do catálogo instalado valida a estrutura canônica sem
  depender da existência de uma skill específica como única âncora.

### Dogfooding real

- **AC-42:** no clone independente
  `C:\Users\Danilo\Projeto\lucreagro-hermes-clone`, que não precisa conter
  `skills/`, o Hermes executa `code-audit` sobre o escopo permitido e produz
  somente achados sustentados por evidência. A revisão da missão destaca os
  achados realmente relacionados ao fluxo de lote documental do WhatsApp, se
  houver gatilhos no escopo. Não existe quota mínima de achados. Antes e depois,
  HEAD, working tree, staging e refs são idênticos. Um resultado sem achados é
  aceitável somente como “nenhum gatilho das regras desta versão”, nunca como
  certificação de segurança.

Cada AC possui teste automatizado planejado no front matter. O componente de
“risco realmente relacionado à missão” em AC-42 também exige revisão humana da
evidência, pois relevância de negócio não deve ser inferida por uma regra
específica de consumidor.

## 17. Plano de Testes

### 17.1 Testes unitários

Arquivo principal proposto: `tests/test_code_audit.py`.

1. Validar manifesto e compatibilidade com policy (`AC-01`).
2. Criar árvores temporárias com cada extensão permitida e extensões vizinhas;
   espionar aberturas para provar o conjunto exato (`AC-03`).
3. Embaralhar ordem de criação de arquivos/diretórios e comparar resultados
   completos (`AC-04`).
4. Cobrir cada exclusão e um diretório não listado (`AC-05`).
5. Testar cada valor exatamente no limite e um acima (`AC-06` a `AC-09`,
   `AC-29`). Fixtures usam monkeypatch de constantes quando necessário para
   permanecer rápidas sem mudar a semântica do boundary.
6. Criar symlinks e, no Windows, junctions/reparse points em raiz, ancestral,
   diretório excluído e arquivo candidato (`AC-10` a `AC-12`). Testes são
   pulados apenas quando a plataforma não permite criar a forma, com motivo
   explícito; pelo menos a lógica de flags é testada em todas as plataformas.
7. Cobrir NUL, UTF-8 inválido, BOM válido, arquivo crescente, troca de inode e
   falha de permissão (`AC-13` a `AC-15`).
8. Monkeypatchar importação dinâmica, execução de código, subprocessos, socket
   e primitivas de escrita para falhar se chamados (`AC-16` a `AC-19`).
9. Validar imutabilidade, enums, paths e regiões do modelo (`AC-21`, `AC-22`).
10. Cobrir fato e hipótese explicitamente (`AC-23`).
11. Executar cada regra contra caso positivo, caso negativo, comentário,
    docstring/string, falso positivo próximo e variantes de whitespace
    documentadas (`AC-24`, `AC-26`, `AC-27`).
12. Usar um literal de segredo sentinela e provar que ele não aparece em
    nenhuma representação, enquanto o gatilho continua verificável (`AC-25`).
13. Auditar fixture limpa e provar zero achados (`AC-28`).
14. Injetar falha após achados provisórios e provar descarte atômico (`AC-30`).

### 17.2 Testes de integração de skills

Arquivos propostos: `tests/test_skill_execution.py` e
`tests/test_skill_catalog.py`.

1. Resolver catálogo próprio, planejar e despachar `code-audit` exato
   (`AC-02`).
2. Colocar uma skill conflitante em `TARGET/skills/code-audit` e provar que ela
   é ignorada sem sequer ser carregada (`AC-36`).
3. Invalidar qualquer entrada do catálogo canônico e provar descoberta atômica
   antes do handler.
4. Rodar regressão completa de `git-preflight`, incluindo read-only e estados
   Git (`AC-37`).
5. Criar linked worktree temporário conforme o contrato Git existente, provar
   bloqueio prévio e snapshots idênticos (`AC-38`).
6. Provar que a resolução canônica reconhece catálogo completo sem âncora
   exclusiva em `git-preflight` ou `code-audit` (`AC-41`).

### 17.3 Testes CLI

Arquivo proposto: `tests/test_cli.py`.

1. `--format text` limpo e com achados (`AC-31`, `AC-35`).
2. `--format json` limpo, com achados e erro (`AC-32`, `AC-35`).
3. Parser continua expondo somente `skill_id`, `--project` e `--format` para
   `skill run`; flags não previstas falham (`AC-33`).
4. Paths absolutos, controles, traceback e segredo sentinela não aparecem em
   stdout/stderr (`AC-34`).
5. Target ausente, catálogo inválido, skill inexistente, limite excedido e
   arquivo inseguro retornam código 3 sem traceback.

### 17.4 Testes de packaging

Arquivo proposto: `tests/test_packaging.py`.

1. Construir wheel e listar seu conteúdo sem depender da árvore fonte.
2. Instalar wheel em ambiente isolado, mudar CWD para diretório sem `skills/` e
   executar `code-audit` contra fixture externa (`AC-39`).
3. Construir sdist, provar presença do manifesto canônico de `code-audit`,
   reconstruir wheel dele e repetir a execução isolada (`AC-40`).
4. Provar que catálogo inválido ou incompleto no artefato bloqueia sem fallback.

### 17.5 Teste de não mutação Git

Em repositório temporário, antes e depois da auditoria, capturar externamente:

```text
git rev-parse HEAD
git status --porcelain=v1
git diff --cached --name-status
git show-ref
```

Comparar os quatro valores exatamente. O teste também registra conteúdo e
metadata relevante da árvore para provar que o handler não escreveu (`AC-20`).
Os comandos de snapshot são infraestrutura de teste; não são chamados pelo
handler.

### 17.6 Dogfooding real contra Lucre Agro

Pré-condições:

- alvo exato:
  `C:\Users\Danilo\Projeto\lucreagro-hermes-clone`;
- o clone não será limpo, alterado ou preparado para fazer o teste passar;
- a presença de `skills/` no clone não é exigida e não participa do catálogo;
- a implementação e toda a suíte automatizada já passaram;
- snapshots são executados externamente ao processo de `code-audit`.

Captura anterior:

```powershell
git -C "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" rev-parse HEAD
git -C "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" status --porcelain=v1
git -C "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" diff --cached --name-status
git -C "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" show-ref
```

Execução:

```powershell
.venv\Scripts\python.exe -m hermes_ops skill run code-audit `
  --project "C:\Users\Danilo\Projeto\lucreagro-hermes-clone" `
  --format text
```

Captura posterior: repetir os quatro comandos, sem qualquer comando de
limpeza, checkout, reset, stage ou correção.

Validação:

1. a auditoria cobre todos os candidatos dentro dos limites ou falha fechado;
2. `passed/0` é válido se não houver gatilhos;
3. `completed_with_findings/3` é válido se houver achados;
4. cada achado é conferido no arquivo e região indicados;
5. o relatório da missão separa achados pertinentes ao lote documental do
   WhatsApp de achados gerais, sem mudar as regras do produto;
6. nenhuma hipótese é reescrita como fato;
7. HEAD anterior = HEAD posterior;
8. working tree anterior = working tree posterior;
9. staging anterior = staging posterior;
10. refs anteriores = refs posteriores.

O dogfooding só pode ser registrado como evidência de implementação depois de
existir código. Ele não será executado na fase atual de especificação.

## 18. Arquivos Provavelmente Afetados na Implementação Futura

Esta lista é indicativa e não autoriza alterações nesta fase:

```text
skills/code-audit/SKILL.md
src/hermes_ops/skills/code_audit.py
src/hermes_ops/skills/execution.py
src/hermes_ops/skills/executor.py
src/hermes_ops/skills/catalog.py
src/hermes_ops/commands/skill.py
src/hermes_ops/core/errors.py
pyproject.toml
MANIFEST.in
tests/test_code_audit.py
tests/test_code_audit_dogfood.py
tests/test_skill_execution.py
tests/test_skill_catalog.py
tests/test_cli.py
tests/test_packaging.py
docs/hermes/specs/HERMES-0008-code-audit-read-only.md
```

O desenho deve preferir um módulo dedicado de auditoria e evitar concentrar
scanner, regras e formatação no dispatcher.

## 19. Decisões Tomadas

### D-01 - Reutilizar a interface pública existente

`skill run code-audit --project TARGET --format ...` é suficiente. Não haverá
flag de catálogo nem opções operacionais no primeiro escopo.

### D-02 - Catálogo próprio e despacho literal

`code-audit` é uma skill passiva do Hermes e seu handler é escolhido por ID
literal no código confiável. Não será criado mecanismo genérico de plugins.

### D-03 - Nenhuma capacidade runtime declarada

O manifesto usa `requires=[]`. O scanner depende somente de leitura local pela
biblioteca padrão. Git não é requisito de execução.

### D-04 - Conjunto pequeno e fechado de linguagens

O primeiro escopo cobre Python, JavaScript e TypeScript pelas oito extensões
listadas. Cobertura ampla porém superficial seria menos verificável.

### D-05 - Limites fixos no Hermes

Limites não são configuráveis pelo alvo. Isso impede que um arquivo do projeto
relaxe a barreira que deveria protegê-lo.

### D-06 - Incompletude bloqueia

Arquivo candidato grande, binário, ilegível ou instável bloqueia. O Hermes não
omite silenciosamente uma parte esperada e chama o restante de auditoria
completa.

### D-07 - Rejeitar toda indirection encontrada

Symlinks e reparse points não são seguidos, mesmo quando apontam para dentro ou
usam nome excluído. Esta regra é simples, auditável e fail closed.

### D-08 - Regras determinísticas, não IA

A primeira versão usa cinco regras estáticas fechadas. Ela não acessa rede nem
depende de modelo probabilístico. Novas regras exigem mudança explícita.

### D-09 - Evidência mínima e redação de segredo

Trechos são curtos e valores sensíveis são substituídos. Um relatório técnico
não justifica republicar credenciais encontradas.

### D-10 - Achado é resultado operacional que exige atenção

Zero achados retorna 0. Um ou mais achados retornam 3 com
`completed_with_findings`. Isso mantém automações conservadoras.

### D-11 - Sem quota de achados no dogfooding

Exigir quantidade mínima incentivaria falsos positivos. O teste real valida
evidência e não volume. Relevância para o fluxo documental é revisão humana,
não lógica específica da Lucre Agro.

### D-12 - Modelo genérico de execução permanece compatível

Modelos específicos são adaptados para evidências existentes. A apresentação
textual recebe somente um ramo literal, sem quebrar `git-preflight`.

## 20. Alternativas Consideradas e Descartadas

### A-01 - Executar linters e scanners instalados no alvo

Descartada porque executaria processos e possivelmente plugins/configurações do
projeto, ampliando rede, mutação e supply chain.

### A-02 - Importar módulos Python ou carregar JavaScript

Descartada porque importação é execução de código arbitrário.

### A-03 - Usar LLM remoto para interpretar todos os arquivos

Descartada no primeiro escopo por rede, privacidade, não determinismo e risco de
achados sem evidência reproduzível.

### A-04 - Permitir configuração no projeto-alvo

Descartada porque conteúdo não confiável poderia ampliar paths, extensões,
limites ou regras.

### A-05 - Seguir symlinks que parecem permanecer dentro do alvo

Descartada por TOCTOU, diferenças de plataforma e complexidade de provar
contenção durante toda a leitura.

### A-06 - Ignorar silenciosamente arquivos grandes, binários ou ilegíveis

Descartada porque produziria um sucesso sobre escopo incompleto.

### A-07 - Ler todos os formatos de texto

Descartada para evitar `.env`, dumps, dados e arquivos sem semântica de código
no escopo inicial.

### A-08 - Criar opções `--include`, `--exclude` e `--max-size`

Descartada para manter a interface simples e a segurança não relaxável nesta
versão.

### A-09 - Regras específicas de WhatsApp ou Lucre Agro

Descartada porque `hermes-ops` é genérico e independente de consumidores.

### A-10 - Retornar código 0 mesmo com achados

Descartada porque consumidores automatizados poderiam confundir “execução
concluída” com “nenhuma ação necessária”.

### A-11 - Adicionar `findings` diretamente ao resultado genérico

Descartada nesta versão para não quebrar o contrato estabelecido pela
HERMES-0006. A adaptação via evidências é suficiente.

## 21. Riscos Conhecidos e Mitigações

### R-01 - Falsos positivos lexicais

Mesmo com reconhecimento conservador, contexto semântico pode faltar.
Mitigação: evidência local, classificação de hipótese, testes negativos e
linguagem condicional.

### R-02 - Falsos negativos

Cinco regras e três famílias de linguagem não cobrem toda vulnerabilidade.
Mitigação: comunicar escopo e nunca tratar `passed` como certificação.

### R-03 - TOCTOU sofisticado

Um ator pode tentar trocar conteúdo preservando metadata. Mitigação: handle
limitado, checagens antes/depois, contenção e bloqueio; documentar que a
proteção não é garantia contra filesystem hostil com privilégios superiores.

### R-04 - Reparse points variam por plataforma

Flags e APIs diferem entre Windows e POSIX. Mitigação: helpers centralizados,
testes específicos por plataforma e bloqueio quando a classificação é incerta.

### R-05 - Atualização de atime

Leitura pode atualizar timestamp de acesso apesar de não escrever conteúdo.
Mitigação: explicitar a limitação; não tentar restaurar atime, pois isso seria
mutação.

### R-06 - Evidência conter dado sensível não reconhecido

Redação por identificador não captura todo segredo. Mitigação: trechos mínimos,
limite estrito, sanitização e regras conservadoras. Revisar política antes da
implementação.

### R-07 - Regex ou reconhecedor com custo patológico

Conteúdo controlado pode causar consumo excessivo. Mitigação: padrões lineares
ou limitados, arquivos/bytes fixos e testes adversariais; evitar regex com
backtracking não limitado.

### R-08 - Catálogo empacotado incompleto

Adicionar uma segunda skill pode expor dependência indevida da âncora atual em
`git-preflight`. Mitigação: testar wheel, sdist, instalação isolada e resolução
da raiz do catálogo como estrutura, não por skill única.

### R-09 - Código minificado ou gerado bloqueiar a auditoria

Um arquivo permitido maior que 512 KiB fora dos diretórios excluídos bloqueia.
Mitigação: erro explícito; uma política futura de exclusão requer nova decisão,
nunca fallback silencioso.

### R-10 - Código válido em extensão não coberta

Ele será ignorado e o resumo pode parecer abrangente demais. Mitigação: saída
declara extensões/versão das regras e documentação define exatamente o escopo.

### R-11 - `exit_code=3` para achados e erros

O mesmo código exige que automações leiam `status`/erro para distinguir os
casos. Mitigação: contrato explícito e testes de texto/JSON. Um código dedicado
futuro exigiria decisão compatível de CLI.

## 22. Evidências Necessárias para Mudar o Status para Implementado

O status somente poderá mudar de `Rascunho` para `Implementado` quando houver:

1. referência do commit ou diff de implementação, sem exigir commit local;
2. testes direcionados passando para scanner, regras, executor, CLI e packaging;
3. suíte completa `.venv\Scripts\python.exe -m pytest` passando;
4. build de wheel e sdist passando;
5. instalação isolada dos artefatos provando o catálogo;
6. `git diff --check` sem erros;
7. dogfooding real documentado com comando, status e exit code;
8. HEAD antes/depois;
9. working tree antes/depois;
10. staging antes/depois;
11. refs antes/depois;
12. revisão humana de cada achado relacionado à missão, sem quota inventada;
13. confirmação de que nenhuma limpeza ou alteração foi feita no clone;
14. confirmação de que `git-preflight` permaneceu compatível.

As evidências concretas desta implementação estão registradas na seção 23.

## 23. Evidências da Implementação

### Implementação e testes

| Verificação | Evidência |
|---|---|
| Testes direcionados finais | 86 passed, 3 skipped, 0 failed |
| Suíte completa final | 452 collected; 441 passed, 11 skipped, 0 failed |
| `compileall` | exit code 0 |
| Build wheel e sdist | exit code 0; ambos os artefatos construídos |
| Packaging isolado | wheel instalado e `code-audit` executada fora da árvore fonte; wheel reconstruído do sdist |
| Catálogo instalado | `code-audit` e `git-preflight` presentes e resolvidos sem âncora exclusiva em uma skill |
| Regressão `git-preflight` | suíte completa passando |

Os skips foram ambientais ou deliberados: criação de symlinks sem privilégio
no Windows, fixtures portáteis de permission-denied indisponíveis e o teste
externo antigo da HERMES-0007 reservado para execução explícita. Junctions e o
linked worktree aplicáveis foram exercitados.

### Dogfooding real da Lucre Agro

Alvo:

```text
C:\Users\Danilo\Projeto\lucreagro-hermes-clone
```

O alvo não continha `skills/`. Resultado:

```text
status=completed_with_findings
exit_code=3
scanned_directories=11
scanned_files=95
scanned_bytes=1308117
findings=14
```

Todos os 14 achados foram `CA004/high/hypothesis`. A revisão humana confirmou
que o relatório não declarou nenhum deles como fato: quatro evidências usam
nomes explícitos `FAKE_TOKEN`/`FAKE_APP_SECRET`, oito apontam para paths de
credenciais em testes, uma aponta para `private_token` em teste de logging e
uma para `APP_SECRET` em teste de assinatura. Não houve achado `observed` nem
risco real confirmado pelas cinco regras. Os achados relacionados ao fluxo de
WhatsApp permanecem hipóteses de fixtures de teste, corretamente redigidas,
para revisão do responsável.

Estado Git externo:

| Estado | Antes | Depois | Preservado |
|---|---|---|---|
| HEAD | `2d1402764b379bf742c78819eff122cc657d86c5` | `2d1402764b379bf742c78819eff122cc657d86c5` | sim |
| working tree | vazia; SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | idêntica | sim |
| staging | vazio; SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | idêntico | sim |
| refs | 40; SHA-256 `fbcb522489a8c38e233bce51ef3a4d5955346d172a973e115b50d2d865d17620` | 40; mesmo SHA-256 | sim |

O clone não foi limpo, preparado ou modificado para o teste.

## 24. Histórico

| Data | Mudança |
|---|---|
| 2026-08-11 | Rascunho inicial da HERMES-0008 para revisão antes de implementação. |
| 2026-08-11 | Implementação concluída; 42 ACs validados por testes automatizados ou dogfooding real, packaging e snapshots Git preservados. |
