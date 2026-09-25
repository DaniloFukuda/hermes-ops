+++
schema_version = 1
id = "HERMES-0004"
status = "Implementado"
[[acceptance_criteria]]
id = "AC-01"
test_file = "tests/test_skill_registry.py"
test_function = "test_discovery_uses_only_explicit_project_root"
[[acceptance_criteria]]
id = "AC-02"
test_file = "tests/test_skill_registry.py"
test_function = "test_empty_skills_directory_returns_empty_registry"
[[acceptance_criteria]]
id = "AC-03"
test_file = "tests/test_skill_registry.py"
test_function = "test_missing_skills_directory_is_explicit_error"
[[acceptance_criteria]]
id = "AC-04"
test_file = "tests/test_skill_registry.py"
test_function = "test_discovery_uses_real_load_skill"
[[acceptance_criteria]]
id = "AC-05"
test_file = "tests/test_skill_registry.py"
test_function = "test_equivalent_trees_with_different_creation_order_match"
[[acceptance_criteria]]
id = "AC-06"
test_file = "tests/test_skill_registry.py"
test_function = "test_get_by_id_returns_exact_skill"
[[acceptance_criteria]]
id = "AC-07"
test_file = "tests/test_skill_registry.py"
test_function = "test_get_by_id_returns_none_for_unknown_id"
[[acceptance_criteria]]
id = "AC-08"
test_file = "tests/test_skill_registry.py"
test_function = "test_loose_file_aborts_discovery"
[[acceptance_criteria]]
id = "AC-09"
test_file = "tests/test_skill_registry.py"
test_function = "test_candidate_without_contract_aborts_discovery"
[[acceptance_criteria]]
id = "AC-10"
test_file = "tests/test_skill_registry.py"
test_function = "test_hidden_or_invalid_candidate_name_is_blocked"
[[acceptance_criteria]]
id = "AC-11"
test_file = "tests/test_skill_registry.py"
test_function = "test_discovery_never_recurses_for_contracts"
[[acceptance_criteria]]
id = "AC-12"
test_file = "tests/test_skill_registry.py"
test_function = "test_later_invalid_skill_exposes_no_partial_registry"
[[acceptance_criteria]]
id = "AC-13"
test_file = "tests/test_skill_registry.py"
test_function = "test_registry_constructor_rejects_duplicate_id"
[[acceptance_criteria]]
id = "AC-14"
test_file = "tests/test_skill_registry.py"
test_function = "test_indirect_protected_paths_are_blocked"
[[acceptance_criteria]]
id = "AC-15"
test_file = "tests/test_skill_registry.py"
test_function = "test_indirect_project_root_ancestor_is_blocked"
[[acceptance_criteria]]
id = "AC-16"
test_file = "tests/test_skill_registry.py"
test_function = "test_inspection_failure_is_controlled"
[[acceptance_criteria]]
id = "AC-17"
test_file = "tests/test_skill_registry.py"
test_function = "test_registry_is_immutable"
[[acceptance_criteria]]
id = "AC-18"
test_file = "tests/test_skill_registry.py"
test_function = "test_discovery_never_executes_content"
[[acceptance_criteria]]
id = "AC-19"
test_file = "tests/test_skill_registry.py"
test_function = "test_requires_remains_inert"
[[acceptance_criteria]]
id = "AC-20"
test_file = "tests/test_skill_registry.py"
test_function = "test_allows_write_remains_declarative"
[[acceptance_criteria]]
id = "AC-21"
test_file = "tests/test_skill_registry.py"
test_function = "test_discovery_does_not_modify_files"
[[acceptance_criteria]]
id = "AC-22"
test_file = "tests/test_skill_registry.py"
test_function = "test_discovery_does_not_modify_git"
[[acceptance_criteria]]
id = "AC-23"
test_file = "tests/test_skill_registry.py"
test_function = "test_public_api_has_no_generic_runner_execute_skill_or_pipeline"
[[acceptance_criteria]]
id = "AC-24"
test_file = "tests/test_skill_registry.py"
test_function = "test_registry_has_no_operational_dependencies"
[[acceptance_criteria]]
id = "AC-25"
test_file = "tests/test_skill_registry.py"
test_function = "test_skill_contract_public_api_remains_compatible"
[[acceptance_criteria]]
id = "AC-26"
test_file = "tests/test_skill_registry.py"
test_function = "test_candidate_contents_are_not_recursively_inspected"
[[acceptance_criteria]]
id = "AC-27"
test_file = "tests/test_skill_registry.py"
test_function = "test_controlled_reverse_enumeration_is_deterministic"
+++

# HERMES-0004 — Registry e Discovery Controlado de Skills

## Status

Implementado

## Resumo para o Responsável pelo Projeto

O Hermes passará a localizar e consultar contratos de skills existentes
somente no diretório `skills/` do projeto informado. A descoberta continuará
sendo uma operação de leitura: ela validará todos os contratos antes de
produzir uma coleção imutável e não executará nenhuma skill.

## Contexto

A HERMES-0003 implementou o contrato versão 1, o modelo imutável
`SkillDefinition` e `load_skill(path)`. Esse loader recebe um único caminho
explícito, lê o `SKILL.md` em UTF-8, valida metadados e Markdown e não descobre
outros arquivos.

O repositório possui hoje uma skill canônica em
`skills/git-preflight/SKILL.md`. A API pública de `hermes_ops.skills` expõe o
loader e os tipos do contrato, mas não possui uma forma controlada de enumerar
as skills disponíveis nem consultá-las por identificador.

## Problema Confirmado

Consumidores futuros precisariam conhecer antecipadamente o caminho de cada
`SKILL.md` ou implementar sua própria enumeração de diretórios. Implementações
independentes poderiam divergir quanto à raiz permitida, ordem, indireções de
filesystem, candidatos inválidos e tratamento de falhas.

Sem uma única fronteira de discovery, existe risco de procurar pais, irmãos ou
caminhos externos, seguir symlinks, aceitar resultados parciais ou produzir
ordens dependentes do filesystem.

## Comportamento Atual

- `load_skill(path)` carrega somente o arquivo explícito recebido.
- `SkillDefinition` é uma dataclass imutável com `slots`.
- `requires` é uma tupla ordenada e `allows_write` é apenas declarativo.
- `SkillContractError` fornece códigos estáveis para contrato ou leitura
  inválidos.
- Não existem registry, discovery, runner, pipeline ou CLI de skills.
- `skills/README.md` documenta o layout `skills/<skill-id>/SKILL.md`, mas sua
  seção de estado ainda descreve o loader como uma fase futura. A HERMES-0003
  implementada e o código atual são a fonte de verdade sobre o loader; essa
  dívida documental não altera o contrato desta especificação e deverá ser
  corrigida em commit separado antes da implementação da HERMES-0004.

## Comportamento Desejado

A operação recebe `project_root` explicitamente e considera exclusivamente o
filho direto `<project-root>/skills`. Somente diretórios diretos de primeiro
nível são candidatos. Cada candidato precisa conter um `SKILL.md` regular e
direto, carregado pelo `load_skill` real da HERMES-0003.

O resultado somente é construído depois que todos os candidatos passam por
validação. As skills são ordenadas pelo `id` em ordem ASCII crescente,
independentemente da ordem fornecida pelo filesystem. O registry oferece a
coleção imutável e consulta exata por `id`.

Estrutura conceitual:

```text
<project-root>/skills/
    git-preflight/SKILL.md
    code-audit/SKILL.md
             |
             v
    discovery estrito e validação por load_skill
             |
             v
    SkillRegistry imutável, ordenado por id
             |
             v
    consulta exata por id, sem execução
```

### API Pública Mínima Proposta

Após analisar o padrão atual — funções públicas simples para operações e
dataclasses imutáveis para resultados — esta especificação propõe:

```text
discover_skills(project_root) -> SkillRegistry

SkillRegistry:
    skills: coleção imutável de SkillDefinition
    get_by_id(skill_id) -> SkillDefinition ou ausência
```

Os nomes `discover_skills` e `SkillRegistry` são decisões de contrato desta
especificação, sujeitos à aprovação antes da implementação. `skills` deve ser
representada por uma tupla. `get_by_id` retorna `None` quando o identificador
não existe; ausência não é erro de discovery. Não haverá método de execução,
registro mutável ou inclusão posterior.

A construção pública `SkillRegistry(skills)` recebe uma tupla de definições,
valida a unicidade dos IDs e estabelece a ordem canônica pelo ID. O mesmo
construtor é a fronteira usada por discovery. Assim, a invariante defensiva de
unicidade pode ser testada diretamente com `SkillDefinition` artificiais
válidas, sem fabricar uma colisão impossível no filesystem e sem monkeypatch
do loader.

O pacote público `hermes_ops.skills` deverá exportar somente os novos símbolos
necessários a essa API, além dos símbolos existentes. O comportamento e a
assinatura pública de `load_skill` não serão alterados.

### Estratégia de Falha

Discovery será **fail-closed e atômico**. Uma skill inválida, colisão de ID,
entrada inesperada, indireção ou falha de inspeção aborta a operação inteira.
Não serão retornadas skills válidas junto com erros e não existirá registry
parcial.

Essa escolha evita que um erro de configuração seja silenciosamente tratado
como ausência de capacidade. A alternativa de retornar válidas mais erros
estruturados foi considerada, mas adiada até existir um consumidor que precise
de diagnóstico parcial sem usar o resultado operacionalmente.

Falhas de contrato produzidas por `load_skill` permanecem
`SkillContractError`, com seu código original e sem reclassificação. Falhas da
fronteira de discovery usam um erro de domínio próprio, proposto como
`SkillRegistryError`, derivado de `HermesOpsError` e com atributo `code`.

### Raiz e Candidatos

- `project_root` deve ser informado explicitamente e representar exatamente a
  raiz a inspecionar; não há busca de pais ou irmãos.
- A validação de `project_root` começa em seu anchor ou raiz de filesystem e
  inspeciona sequencialmente todos os componentes existentes do caminho
  fornecido, antes de acessar o componente seguinte.
- Se qualquer componente ancestral existente ou o próprio `project_root` for
  uma indireção de nomes, discovery falha antes de inspecionar conteúdo abaixo
  dele.
- `skills/`, cada candidato e seu `SKILL.md` também são objetos protegidos e
  precisam ser inspecionados sem atravessar indireções de nomes.
- Symlinks e junctions são sempre indireções proibidas. No Windows, reparse
  points que representem name-surrogate ou outro redirecionamento da resolução
  de nomes também são proibidos. Nenhuma dessas indireções é seguida.
- Um reparse point que não redirecione a resolução de nomes não é rejeitado
  automaticamente apenas por possuir `FILE_ATTRIBUTE_REPARSE_POINT`. A
  implementação futura deverá distinguir com segurança o comportamento de
  indireção, usando Python 3.11 ou superior e somente a biblioteca padrão, sem
  transformar este contrato em dependência de uma API Win32 específica.
- `skills/` inexistente produz erro, pois ausência não deve mascarar projeto
  incompleto ou raiz incorreta.
- `skills/` existente e vazio produz `SkillRegistry` vazio.
- Todo item direto dentro de `skills/` deve ser um diretório candidato válido.
- Arquivo solto, diretório oculto, nome inválido ou diretório sem `SKILL.md`
  aborta discovery como configuração inválida.
- Apenas o `SKILL.md` diretamente dentro do candidato é considerado.
- Discovery nunca percorre subdiretórios. Um `SKILL.md` aninhado não satisfaz
  a ausência do contrato direto e nunca se torna candidato.
- Conteúdo adicional dentro de um candidato válido, inclusive diretórios
  comuns aninhados, não é percorrido nem interpretado por esta fase.
- Uma indireção no caminho que discovery precisa inspecionar é bloqueada antes
  de chamar `load_skill`, com `SKILL_DISCOVERY_INDIRECT_PATH`.

### Ordem e Colisões

As entradas diretas são inspecionadas primeiro em ordem determinística pelo
nome, usando comparação ordinal. Depois da validação, o registry é ordenado
pelo `SkillDefinition.id` em ordem ASCII crescente.

O contrato da HERMES-0003 exige que o ID seja igual ao diretório pai, mas o
construtor público de `SkillRegistry` ainda verifica colisões lógicas. Qualquer
segundo objeto com o mesmo `id` produz `SKILL_REGISTRY_DUPLICATE_ID` e nenhum
registry é retornado. O construtor também aplica a mesma ordenação canônica
usada por discovery.

## Fora do Escopo

- execução de skills;
- runner ou métodos equivalentes;
- pipelines e orquestração;
- resolução operacional, importação ou execução de `requires`;
- autorização ou concessão de capacidades por `allows_write`;
- CLI de skills;
- instalação, download ou atualização de skills;
- plugins ou carregamento dinâmico;
- registry remoto ou catálogo externo;
- Git remoto ou qualquer Git mutável;
- hot reload, watch ou cache persistente;
- descoberta recursiva;
- alteração do contrato v1, de `SkillDefinition` ou de `load_skill` definidos
  pela HERMES-0003;
- atualização de `skills/README.md` ou das skills existentes nesta fase.

## Entradas

- `project_root`, caminho explícito para a raiz exata do projeto.
- O diretório direto `<project-root>/skills/`.
- Zero ou mais diretórios candidatos diretos.
- Um `SKILL.md` direto por candidato.

Nenhuma variável de ambiente, configuração Git, rede ou diretório descoberto
automaticamente participa da operação.

## Saídas

Em caso válido, `discover_skills` retorna um `SkillRegistry` completo e
imutável. Sua propriedade `skills` contém uma tupla de `SkillDefinition`
ordenada por ID. `get_by_id` devolve o objeto existente de ID exato ou `None`.

Em caso inválido, a operação levanta uma falha controlada e não retorna coleção
total nem parcial. Nenhum arquivo, processo, dependência, plugin ou estado Git
é modificado.

## Invariantes e Regras de Segurança

1. `project_root` é a raiz exata recebida; discovery nunca procura pais ou
   irmãos.
2. Somente `<project-root>/skills/` pode ser enumerado.
3. Discovery não recursa e somente diretórios diretos são candidatos.
4. Todos os componentes ancestrais existentes de `project_root`, a própria
   raiz, `skills/`, candidato e `SKILL.md` são inspecionados antes de atravessar
   uma eventual indireção de nomes.
5. Symlink, junction e name-surrogate ou redirecionamento equivalente são
   bloqueados com `SKILL_DISCOVERY_INDIRECT_PATH`; um reparse point sem
   redirecionamento de nomes não é bloqueado somente pelo atributo genérico.
6. Todo candidato é carregado pelo `load_skill` público real.
7. Uma falha aborta todo o resultado; nunca há registry parcial.
8. Ordem de filesystem não influencia a saída nem a primeira falha observável.
9. IDs duplicados são rejeitados, nunca sobrescritos.
10. Conteúdo de `SKILL.md` permanece dado e nunca é executado.
11. `requires` não instala, importa ou executa nada.
12. `allows_write` não concede capacidade.
13. Registry e discovery não escrevem arquivos.
14. Registry e discovery não executam shell ou subprocessos.
15. Registry e discovery não modificam Git.
16. Registry e discovery não carregam plugins.
17. O resultado e sua coleção de skills são imutáveis.
18. Falhas não expõem caminhos locais sem passar pela sanitização central em
    qualquer futura interface pública.
19. A implementação usa Python 3.11 e somente a biblioteca padrão.
20. O contrato existente de `load_skill`, parser v1, validator,
    `SkillDefinition`, enums e `SkillContractError` da HERMES-0003 permanece
    compatível. Esta especificação estende deliberadamente a API pública com
    registry e discovery e supersede somente a restrição limitada à fase
    HERMES-0003 contra essas duas superfícies.

## Pseudocódigo

O pseudocódigo descreve decisões e resultados sem fixar detalhes de Python.

### `discover_skills(project_root)`

```text
FUNÇÃO discover_skills(raiz_do_projeto):
    VALIDAR que a raiz foi informada explicitamente
    PARTINDO do anchor de raiz_do_projeto:
        PARA cada componente existente do caminho, em sequência:
            INSPECIONAR o componente sem seguir a próxima resolução
            SE representar symlink, junction ou redirecionamento de nomes:
                FALHAR com SKILL_DISCOVERY_INDIRECT_PATH
            SOMENTE ENTÃO continuar para o próximo componente
    VALIDAR que raiz_do_projeto existe e é diretório
    DEFINIR raiz_de_skills como o filho direto "skills" da raiz recebida
    SE raiz_de_skills não existir:
        FALHAR com SKILL_ROOT_NOT_FOUND
    INSPECIONAR raiz_de_skills sem seguir indireção
    SE raiz_de_skills representar redirecionamento de nomes:
        FALHAR com SKILL_DISCOVERY_INDIRECT_PATH
    SE raiz_de_skills não for diretório:
        FALHAR com SKILL_ROOT_INVALID

    candidatos = discover_candidate_directories(raiz_de_skills)
    definições = coleção temporária não publicada
    PARA cada candidato em ordem determinística:
        definição = load_candidate(raiz_de_skills, candidato)
        ADICIONAR definição à coleção temporária

    RETORNAR build_registry(definições)
```

### `discover_candidate_directories(skills_root)`

```text
FUNÇÃO discover_candidate_directories(raiz_de_skills):
    TENTAR listar somente os filhos diretos da raiz_de_skills
    SE a listagem falhar:
        FALHAR de forma controlada com SKILL_DISCOVERY_READ_FAILED

    ORDENAR filhos por nome com comparação ordinal
    PARA cada filho:
        SE o nome não seguir a gramática de ID da HERMES-0003:
            FALHAR com SKILL_CANDIDATE_INVALID
        SE o filho representar redirecionamento de nomes:
            FALHAR com SKILL_DISCOVERY_INDIRECT_PATH
        SE o filho não for diretório regular:
            FALHAR com SKILL_CANDIDATE_INVALID
        SE não existir SKILL.md direto no filho:
            FALHAR com SKILL_CANDIDATE_MISSING_CONTRACT
        SE SKILL.md representar redirecionamento de nomes:
            FALHAR com SKILL_DISCOVERY_INDIRECT_PATH
        SE SKILL.md não for arquivo regular:
            FALHAR com SKILL_CANDIDATE_INVALID
        ADICIONAR filho como candidato
    RETORNAR candidatos ordenados
```

### `load_candidate(skills_root, candidate)`

```text
FUNÇÃO load_candidate(raiz_de_skills, candidato):
    CONSTRUIR somente o caminho direto candidato/SKILL.md
    VALIDAR novamente que candidato e arquivo permanecem contidos e diretos
    CHAMAR load_skill(caminho_do_skill_md)
    SE load_skill falhar:
        PROPAGAR a falha original sem produzir resultado parcial
    RETORNAR SkillDefinition validada
```

### `build_registry(definitions)`

```text
FUNÇÃO build_registry(definições):
    CONVERTER definições em tupla
    CONSTRUIR SkillRegistry usando a mesma fronteira pública de construção
    DURANTE a construção:
        VALIDAR que cada id aparece uma única vez
        SE houver duplicidade:
            FALHAR com SKILL_REGISTRY_DUPLICATE_ID
        ORDENAR definições pelo id ASCII crescente
        ARMAZENAR somente a tupla ordenada e imutável
    RETORNAR SkillRegistry imutável e completo
```

### `get_by_id(skill_id)`

```text
FUNÇÃO get_by_id(id_consultado):
    COMPARAR o texto recebido de forma exata, sem normalização ou coerção
    SE existir definição com esse id:
        RETORNAR a SkillDefinition correspondente
    SENÃO:
        RETORNAR ausência
```

## Fluxo Principal

1. Receber a raiz exata do projeto.
2. Inspecionar desde o anchor todos os componentes existentes da raiz, sem
   atravessar indireções de nomes.
3. Formar somente o filho direto `skills/`.
4. Listar somente suas entradas diretas em ordem determinística.
5. Validar cada entrada como candidato estrito.
6. Carregar cada `SKILL.md` por meio de `load_skill`.
7. Interromper integralmente na primeira falha determinística.
8. Verificar colisões lógicas de ID.
9. Ordenar as definições por ID.
10. Construir o registry imutável.
11. Permitir consulta exata por ID, sem executar a skill.

## Casos de Erro e Limites

| Situação | Comportamento | Código |
|----------|---------------|--------|
| `project_root` ausente, inexistente ou não diretório | Falha antes de enumerar | `SKILL_PROJECT_ROOT_INVALID` |
| Ancestral existente, `project_root`, `skills/`, candidato ou `SKILL.md` representa indireção de nomes | Falha antes de atravessar a indireção | `SKILL_DISCOVERY_INDIRECT_PATH` |
| `skills/` inexistente | Falha explícita | `SKILL_ROOT_NOT_FOUND` |
| `skills/` não diretório | Falha antes de enumerar | `SKILL_ROOT_INVALID` |
| Falha de I/O ao listar ou inspecionar | Falha controlada, sem parcial | `SKILL_DISCOVERY_READ_FAILED` |
| Diretório `skills/` vazio | Registry vazio válido | — |
| Arquivo solto ou entrada de tipo inesperado | Falha fail-closed | `SKILL_CANDIDATE_INVALID` |
| Diretório oculto ou nome fora da gramática | Falha fail-closed | `SKILL_CANDIDATE_INVALID` |
| Candidato sem `SKILL.md` direto | Falha fail-closed; não procura aninhados | `SKILL_CANDIDATE_MISSING_CONTRACT` |
| Candidato ou `SKILL.md` é symlink, junction ou name-surrogate | Falha antes do loader | `SKILL_DISCOVERY_INDIRECT_PATH` |
| `SKILL.md` inválido | Propaga `SkillContractError` e código original | Código da HERMES-0003 |
| ID lógico duplicado | Falha sem sobrescrita | `SKILL_REGISTRY_DUPLICATE_ID` |
| ID consultado inexistente | Retorna `None` | — |

A validação considera o estado observado durante a chamada. Não existe garantia
contra troca concorrente de entradas entre inspeção e leitura em filesystems
hostis; reduzir essa janela sem abrir handles específicos de plataforma fica
fora desta versão. Toda inconsistência observada ainda falha de forma fechada.

## Critérios de Aceitação

- **AC-01**: `discover_skills` recebe `project_root` explícito e não procura
  diretórios pais, irmãos ou raízes alternativas.
- **AC-02**: Um `skills/` direto, existente e vazio produz `SkillRegistry`
  imutável com coleção vazia.
- **AC-03**: Ausência de `skills/` produz `SKILL_ROOT_NOT_FOUND`, sem criar o
  diretório nem procurar fallback.
- **AC-04**: Uma skill válida é carregada pelo `load_skill` real e aparece no
  registry com todos os campos preservados.
- **AC-05**: Duas árvores logicamente equivalentes, criadas em ordens
  diferentes, produzem a mesma coleção ordenada por ID ASCII,
  independentemente da ordem entregue pelo filesystem.
- **AC-06**: `get_by_id` retorna a `SkillDefinition` do ID exato existente.
- **AC-07**: Consulta de ID inexistente retorna `None` sem alterar o registry.
- **AC-08**: Arquivo solto diretamente em `skills/` aborta discovery com
  `SKILL_CANDIDATE_INVALID`.
- **AC-09**: Diretório candidato sem `SKILL.md` direto aborta discovery com
  `SKILL_CANDIDATE_MISSING_CONTRACT`.
- **AC-10**: Diretório oculto ou nome fora da gramática de ID aborta discovery
  com `SKILL_CANDIDATE_INVALID`.
- **AC-11**: Discovery não recursa; um `SKILL.md` somente aninhado não é
  descoberto nem satisfaz o contrato direto do candidato.
- **AC-12**: Com ao menos uma skill válida anterior e uma candidata inválida
  posterior na ordem canônica, discovery preserva o `SkillContractError`
  original, não retorna `SkillRegistry` e não expõe coleção parcial pública.
- **AC-13**: A construção pública de `SkillRegistry` valida sua própria
  invariante; duas `SkillDefinition` válidas artificiais com o mesmo ID
  produzem `SKILL_REGISTRY_DUPLICATE_ID`, sem sobrescrita.
- **AC-14**: Symlink, junction ou name-surrogate disponível na plataforma é
  rejeitado com `SKILL_DISCOVERY_INDIRECT_PATH` em cada nível protegido:
  `project_root`, `skills/`, candidato e `SKILL.md` aplicável.
- **AC-15**: Uma indireção em qualquer componente ancestral existente de
  `project_root` é detectada desde o anchor e produz
  `SKILL_DISCOVERY_INDIRECT_PATH` antes que conteúdo abaixo dela seja lido.
- **AC-16**: Falha de listagem ou inspeção é controlada por
  `SKILL_DISCOVERY_READ_FAILED` e não retorna resultado parcial.
- **AC-17**: O registry e sua coleção de skills são imutáveis; a ordem não pode
  ser alterada depois da construção.
- **AC-18**: Discovery trata corpo e metadados como dados e nunca executa
  conteúdo de `SKILL.md`.
- **AC-19**: Valores de `requires` permanecem inertes e não são instalados,
  importados ou executados.
- **AC-20**: `allows_write` permanece declarativo e não autoriza escrita.
- **AC-21**: Discovery e registry não criam, alteram ou removem arquivos.
- **AC-22**: Discovery e registry não modificam index, HEAD, referências ou
  configuração Git.
- **AC-23**: Na fase HERMES-0004, a API pública mínima continha discovery e
  consulta por ID, sem execução ou CLI. A HERMES-0006 supersede somente a
  proibição absoluta de `run_skill` e da CLI piloto `skill run`; registry e
  discovery continuam passivos, e permanecem proibidos runner genérico,
  `execute_skill`, pipeline e qualquer framework de execução dinâmica.
- **AC-24**: A implementação não usa shell, subprocesso, import dinâmico,
  plugin loading ou dependência externa.
- **AC-25**: O comportamento público de `load_skill`, `SkillDefinition`,
  `SkillStatus`, `SkillRisk` e `SkillContractError` permanece compatível com a
  HERMES-0003. A extensão com `SkillRegistry` e `discover_skills` supersede
  somente a ausência de registry e discovery naquela fase.
- **AC-26**: Conteúdo adicional e diretórios comuns dentro de candidato válido
  não são percorridos, interpretados ou carregados.
- **AC-27**: Para a mesma coleção lógica e os mesmos bytes, inclusive quando
  uma seam pequena de enumeração entrega candidatos em ordem invertida,
  discovery produz a mesma sequência final por ID ou a mesma primeira falha
  observável.

## Plano de Testes

Os testes futuros ficarão em `tests/test_skill_registry.py`, seguindo o padrão
de arquivos dedicados por domínio e usando `tmp_path`. Cada teste conterá o
marcador `Spec: HERMES-0004 / AC-NN`. Testes que precisarem de Git criarão
repositórios somente em diretórios temporários.

| Critério | Tipo de Teste | Arquivo | Nome do Teste | O que o Teste Comprova |
|----------|---------------|---------|---------------|------------------------|
| AC-01 | Segurança | `tests/test_skill_registry.py` | `test_discovery_uses_only_explicit_project_root` | Não descobre pais, irmãos ou fallback |
| AC-02 | Unitário | `tests/test_skill_registry.py` | `test_empty_skills_directory_returns_empty_registry` | Diretório vazio é válido e imutável |
| AC-03 | Unitário | `tests/test_skill_registry.py` | `test_missing_skills_directory_is_explicit_error` | Ausência tem código estável e não cria diretório |
| AC-04 | Integração | `tests/test_skill_registry.py` | `test_discovery_uses_real_load_skill` | Integração preserva `SkillDefinition` real |
| AC-05 | Unitário | `tests/test_skill_registry.py` | `test_equivalent_trees_with_different_creation_order_match` | Árvores criadas em ordens diferentes resultam na mesma sequência por ID |
| AC-06 | Unitário | `tests/test_skill_registry.py` | `test_get_by_id_returns_exact_skill` | Consulta exata encontra a definição |
| AC-07 | Unitário | `tests/test_skill_registry.py` | `test_get_by_id_returns_none_for_unknown_id` | Ausência é retorno estável |
| AC-08 | Segurança | `tests/test_skill_registry.py` | `test_loose_file_aborts_discovery` | Arquivo solto é bloqueado |
| AC-09 | Unitário | `tests/test_skill_registry.py` | `test_candidate_without_contract_aborts_discovery` | Candidato precisa de contrato direto |
| AC-10 | Segurança | `tests/test_skill_registry.py` | `test_hidden_or_invalid_candidate_name_is_blocked` | Nomes inesperados não são ignorados |
| AC-11 | Segurança | `tests/test_skill_registry.py` | `test_discovery_never_recurses_for_contracts` | Contrato aninhado não é descoberto |
| AC-12 | Integração | `tests/test_skill_registry.py` | `test_later_invalid_skill_exposes_no_partial_registry` | Skill válida anterior não se torna resultado público após falha posterior |
| AC-13 | Unitário | `tests/test_skill_registry.py` | `test_registry_constructor_rejects_duplicate_id` | Construtor público defende unicidade com definições artificiais válidas |
| AC-14 | Segurança parametrizada | `tests/test_skill_registry.py` | `test_indirect_protected_paths_are_blocked` | Tipos suportados são rejeitados separadamente em cada nível protegido |
| AC-15 | Segurança | `tests/test_skill_registry.py` | `test_indirect_project_root_ancestor_is_blocked` | Validação desde o anchor bloqueia ancestral indireto antes da leitura |
| AC-16 | Unitário | `tests/test_skill_registry.py` | `test_inspection_failure_is_controlled` | Erro de I/O não vaza parcial |
| AC-17 | Unitário | `tests/test_skill_registry.py` | `test_registry_is_immutable` | Modelo e coleção rejeitam mutação |
| AC-18 | Segurança | `tests/test_skill_registry.py` | `test_discovery_never_executes_content` | Payload permanece texto |
| AC-19 | Segurança | `tests/test_skill_registry.py` | `test_requires_remains_inert` | Dependências declaradas não são carregadas |
| AC-20 | Segurança | `tests/test_skill_registry.py` | `test_allows_write_remains_declarative` | Declaração não concede escrita |
| AC-21 | Segurança | `tests/test_skill_registry.py` | `test_discovery_does_not_modify_files` | Snapshot do filesystem permanece igual |
| AC-22 | Segurança | `tests/test_skill_registry.py` | `test_discovery_does_not_modify_git` | Git permanece inalterado |
| AC-23 | Estrutural | `tests/test_skill_registry.py` | `test_public_api_has_no_generic_runner_execute_skill_or_pipeline` | A extensão piloto posterior é permitida sem runner genérico, `execute_skill` ou pipeline |
| AC-24 | Estrutural | `tests/test_skill_registry.py` | `test_registry_has_no_operational_dependencies` | Sem shell, subprocesso, import dinâmico ou plugin |
| AC-25 | Regressão | `tests/test_skill_registry.py` | `test_skill_contract_public_api_remains_compatible` | Loader, parser e modelo da HERMES-0003 não sofrem regressão; registry e discovery são a extensão aprovada |
| AC-26 | Segurança | `tests/test_skill_registry.py` | `test_candidate_contents_are_not_recursively_inspected` | Conteúdo adicional fica inerte |
| AC-27 | Unitário | `tests/test_skill_registry.py` | `test_controlled_reverse_enumeration_is_deterministic` | Seam limitada de enumeração invertida não altera resultado nem primeira falha |

Os testes de segurança devem cobrir comportamento permitido, comportamento
bloqueado e regressão: árvore direta válida permitida; indireções de nomes
bloqueadas; e API da HERMES-0003 preservada.

### Matriz Portátil de Indireções

O teste parametrizado de AC-14 deve distinguir os níveis `project_root`,
`skills/`, candidato e `SKILL.md`. O caso de `SKILL.md` usa symlink de arquivo;
os demais usam symlink de diretório. AC-15 cobre separadamente cada posição
ancestral existente entre o anchor e `project_root`.

No Windows, os casos suportados também incluem junction e outra fixture segura
de name-surrogate quando ela puder ser criada somente com recursos disponíveis
no ambiente de teste. Não se exige fabricar reparse point arbitrário que
dependa de driver, software externo ou API fora do escopo.

Um caso pode usar `pytest.skip` somente quando a plataforma ou o ambiente
realmente não puder criar aquela fixture: junction é específica do Windows e
ausência de privilégio pode impedir symlink. Cada tipo e nível é parametrizado
isoladamente; o skip de um caso não oculta nem dispensa os demais casos
suportados.

### Provas de Atomicidade, Colisão e Determinismo

- AC-12 cria uma skill válida cujo ID vem antes de uma candidata inválida,
  chama discovery, confirma a exceção original e confirma que a variável de
  resultado nunca recebeu `SkillRegistry` nem coleção parcial pública. Não se
  inspeciona a destruição de objetos temporários internos.
- AC-13 constrói duas `SkillDefinition` artificiais válidas com o mesmo ID e
  chama diretamente `SkillRegistry(skills)`, a mesma fronteira pública usada
  pelo discovery. O teste valida a invariante do registry, não parser ou
  filesystem, e não usa monkeypatch de `load_skill`.
- AC-05 cria duas árvores temporárias equivalentes com ordens de criação
  diferentes e compara as sequências públicas completas.
- AC-27 pode usar uma seam pequena e dedicada de enumeração controlada para
  fornecer os mesmos candidatos em ordem normal e invertida. Essa seam não
  substitui `pathlib` globalmente; o teste compara resultados ou erros públicos
  e não procura apenas a existência de uma chamada a `sorted`.

## Arquivos Provavelmente Afetados

- `src/hermes_ops/skills/registry.py` — implementação provável de discovery,
  registry imutável e consulta;
- `src/hermes_ops/skills/__init__.py` — exportação da API pública mínima;
- `src/hermes_ops/core/errors.py` — erro controlado da fronteira de registry;
- `tests/test_skill_registry.py` — testes unitários, integração, segurança e
  regressão.

Não se prevê alteração em `models.py`, `loader.py`, `validator.py`, CLI,
`pyproject.toml`, skills existentes ou HERMES-0003.

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| 2026-08-10 | API mínima `discover_skills(project_root) -> SkillRegistry`, construção pública que valida unicidade, tupla `skills` e `get_by_id` | Segue funções públicas simples, permite testar a invariante defensiva sem filesystem impossível e mantém resultado imutável | Registry global ou mutável; builder privado como única fronteira |
| 2026-08-10 | Discovery atômico e fail-closed | Impede uso silencioso de conjunto parcial após configuração inválida | Retornar válidas junto com erros estruturados |
| 2026-08-10 | `skills/` ausente é erro; vazio é registry vazio | Distingue raiz/projeto incompleto de uma coleção explicitamente vazia | Tratar ausência como vazio |
| 2026-08-10 | Toda entrada direta em `skills/` deve ser candidato válido | Evita ignorar typo, artefato oculto ou configuração inesperada | Ignorar arquivos e diretórios desconhecidos |
| 2026-08-10 | Inspecionar desde o anchor todos os ancestrais existentes e objetos protegidos; rejeitar symlink, junction e name-surrogate com código único | Garante que nenhuma indireção de nomes seja atravessada, inclusive antes do objeto final | Verificar apenas o nó final; seguir symlinks internos contidos |
| 2026-08-10 | Não rejeitar automaticamente reparse point sem redirecionamento de nomes | O atributo genérico também pode representar objetos que não alteram resolução de caminho | Bloquear indiscriminadamente todo `FILE_ATTRIBUTE_REPARSE_POINT` |
| 2026-08-10 | Não recursar | Mantém a fronteira em um nível e evita descoberta implícita | Procurar `SKILL.md` em profundidade arbitrária |
| 2026-08-10 | Ordenar por ID ASCII e inspecionar nomes ordinalmente | Resultado e primeira falha independem da ordem do filesystem | Preservar ordem de `iterdir` |
| 2026-08-10 | Propagar `SkillContractError` de candidatos inválidos | Preserva semântica e códigos públicos da HERMES-0003 | Encapsular toda falha como erro genérico de registry |
| 2026-08-10 | ID inexistente retorna `None` | Consulta de ausência é esperada e não invalida registry válido | Levantar exceção para lookup ausente |

## Alternativas Descartadas

1. **Retornar skills válidas e erros estruturados:** facilita diagnóstico, mas
   permite consumo acidental de resultado incompleto. Pode ser reconsiderado
   em uma API de inspeção separada.
2. **Ignorar entradas desconhecidas:** esconderia erros de configuração e
   tornaria a coleção dependente de convenções não validadas.
3. **Seguir symlinks ou name-surrogates contidos:** exige resolução e prova de
   contenção sujeitas a condições de corrida; a primeira versão bloqueia toda
   indireção de nomes, mas não rejeita atributo de reparse sem redirecionamento.
4. **Registry global ou singleton:** cria estado implícito, dificulta testes e
   contraria a raiz explícita.
5. **Lookup que normaliza caixa ou hífens:** IDs da HERMES-0003 são exatos;
   coerção poderia resolver a skill errada.
6. **Discovery recursivo:** amplia a superfície, aceita layouts não canônicos e
   pode atravessar diretórios inesperados.

## Riscos Restantes

- A inspeção por caminho possui janela entre validação e leitura; um agente
  externo com escrita concorrente pode trocar entradas nesse intervalo.
- Rejeitar qualquer entrada inesperada torna artefatos como `.DS_Store` erro
  explícito. Isso é intencional, mas exige diretório canônico disciplinado.
- Rejeitar todas as indireções de nomes pode impedir layouts legítimos baseados
  em symlink ou junction; uma versão futura poderá avaliar handles seguros por
  plataforma.
- Identificar name-surrogate de forma portátil no Windows pode exigir caminhos
  distintos conforme recursos expostos pela biblioteca padrão do Python; a
  implementação deve falhar de forma controlada se não puder classificar com
  segurança um objeto que precisa atravessar.
- `get_by_id` linear sobre uma tupla é suficiente para coleções pequenas. Uma
  estrutura auxiliar imutável pode ser avaliada sem mudar o contrato se houver
  evidência de problema de desempenho.
- Códigos e nomes públicos permanecem sujeitos à aprovação desta especificação
  antes da implementação.

## Evidências da Implementação

A implementação de registry e discovery foi concluída na branch
`feature/skills-contract`. A auditoria final confirmou segurança somente
leitura, `SkillRegistry` imutável, discovery fail-closed, atomicidade,
determinismo, integração com o `load_skill` real e proteção de ancestrais e
indireções. Não foram adicionadas dependências externas, runner, execução,
pipeline ou CLI operacional de skills; `requires` e `allows_write` permanecem
inertes.

| Campo | Valor |
|-------|-------|
| Commit da implementação | `d6164f3` |
| Estado da integração | Concluído na branch `feature/skills-contract`; ainda não integrado |
| Arquivos alterados | `src/hermes_ops/core/errors.py`, `src/hermes_ops/skills/__init__.py`, `src/hermes_ops/skills/registry.py`, `tests/test_skill_registry.py`, além da reconciliação documental em HERMES-0003/HERMES-0004 e atualização de `skills/README.md` |
| Testes direcionados | `.venv\Scripts\python.exe -m pytest tests/test_skill_registry.py` → 35 collected, 29 passed, 6 skipped, 0 failed, 0 errors, exit code 0; `.venv\Scripts\python.exe -m pytest tests/test_skills.py` → 93 collected, 93 passed, 0 failed, exit code 0 |
| Suíte completa | `.venv\Scripts\python.exe -m pytest` → 243 collected, 235 passed, 8 skipped, 0 failed, 0 errors, exit code 0 |
| Validação de sintaxe ou compileall | `.venv\Scripts\python.exe -m compileall -q src/hermes_ops` → concluído sem erros, exit code 0 |
| Empacotamento | Coberto por `tests/test_packaging.py` na suíte completa → 3 testes aprovados |
| git diff --check | PASS, sem avisos |
| Plataformas e versões validadas | Windows, Python 3.13.13 |
| CI | Não aplicável — implementação concluída em branch local, ainda sem integração ou execução de CI |
| Limitações do ambiente | 6 skips nos testes direcionados: cinco fixtures de symlink indisponíveis por privilégio no Windows e uma fixture portátil de permission-denied indisponível; junctions executadas com sucesso. Na suíte completa, 8 skips ambientais. Após `553f275`, `PytestUnhandledThreadExceptionWarning` e warnings de junction são 0 |

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| 2026-08-10 | Codex | Criação inicial da especificação em status Rascunho, com API proposta, discovery fail-closed e política estrita de caminhos | Solicitação SKILL-3 |
| 2026-08-10 | Codex | Fechamento da inspeção de ancestrais, distinção de name-surrogate, remoção do escape conceitual e fortalecimento dos testes de atomicidade, colisão e determinismo | Correção após auditoria da HERMES-0004 |
| 2026-08-10 | Codex | Promoção do status para Aprovado e registro de justificativas documentais temporárias para os 27 ACs ainda sem implementação | Auditoria final concluída sem contradições materiais |
| 2026-08-10 | Codex | Esclarecimento de que registry e discovery estendem a API e supersedem somente a restrição limitada à fase HERMES-0003, preservando loader, parser, modelo e segurança | Reconciliação HERMES-0003 / AC-30; sem alteração do comportamento do registry |
| 2026-08-10 | Codex | Promoção para Implementado, substituição das 27 justificativas temporárias por vínculos reais e registro das evidências finais de segurança e validação | Reconciliação `ad455ed`; implementação `d6164f3`; correção da fixture de junction `553f275` |
| 2026-08-10 | Codex | Reconciliação da fronteira phase-scoped de AC-23 com a HERMES-0006: `run_skill` e `skill run` passam a ser permitidos somente no piloto fechado | Registry/discovery permanecem passivos; runner genérico, `execute_skill`, pipeline e execução dinâmica continuam proibidos |
