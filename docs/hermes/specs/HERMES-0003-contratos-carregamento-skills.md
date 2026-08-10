+++
schema_version = 1
id = "HERMES-0003"
status = "Implementado"
[[acceptance_criteria]]
id = "AC-01"
test_file = "tests/test_skills.py"
test_function = "test_loads_only_explicit_path"
[[acceptance_criteria]]
id = "AC-02"
test_file = "tests/test_skills.py"
test_function = "test_loads_real_git_preflight_skill"
[[acceptance_criteria]]
id = "AC-03"
test_file = "tests/test_skills.py"
test_function = "test_utf8_accents_and_invalid_encoding"
[[acceptance_criteria]]
id = "AC-04"
test_file = "tests/test_skills.py"
test_function = "test_front_matter_boundaries"
[[acceptance_criteria]]
id = "AC-05"
test_file = "tests/test_skills.py"
test_function = "test_exact_required_fields"
[[acceptance_criteria]]
id = "AC-06"
test_file = "tests/test_skills.py"
test_function = "test_schema_version_is_exact_textual_one"
[[acceptance_criteria]]
id = "AC-07"
test_file = "tests/test_skills.py"
test_function = "test_id_format_and_directory_match"
[[acceptance_criteria]]
id = "AC-08"
test_file = "tests/test_skills.py"
test_function = "test_version_matches_unsigned_positive_decimal"
[[acceptance_criteria]]
id = "AC-09"
test_file = "tests/test_skills.py"
test_function = "test_status_enum"
[[acceptance_criteria]]
id = "AC-10"
test_file = "tests/test_skills.py"
test_function = "test_description_is_non_empty_literal_text"
[[acceptance_criteria]]
id = "AC-11"
test_file = "tests/test_skills.py"
test_function = "test_risk_enum"
[[acceptance_criteria]]
id = "AC-12"
test_file = "tests/test_skills.py"
test_function = "test_requires_empty_list"
[[acceptance_criteria]]
id = "AC-13"
test_file = "tests/test_skills.py"
test_function = "test_requires_preserves_order"
[[acceptance_criteria]]
id = "AC-14"
test_file = "tests/test_skills.py"
test_function = "test_requires_rejects_invalid_grammar_and_items"
[[acceptance_criteria]]
id = "AC-15"
test_file = "tests/test_skills.py"
test_function = "test_allows_write_literal_booleans"
[[acceptance_criteria]]
id = "AC-16"
test_file = "tests/test_skills.py"
test_function = "test_allows_write_rejects_non_booleans"
[[acceptance_criteria]]
id = "AC-17"
test_file = "tests/test_skills.py"
test_function = "test_parser_uses_closed_textual_grammar"
[[acceptance_criteria]]
id = "AC-18"
test_file = "tests/test_skills.py"
test_function = "test_each_required_section_missing"
[[acceptance_criteria]]
id = "AC-19"
test_file = "tests/test_skills.py"
test_function = "test_required_sections_unique_and_ordered"
[[acceptance_criteria]]
id = "AC-20"
test_file = "tests/test_skills.py"
test_function = "test_section_names_must_be_real_h2"
[[acceptance_criteria]]
id = "AC-21"
test_file = "tests/test_skills.py"
test_function = "test_markdown_body_is_preserved_in_skill_definition"
[[acceptance_criteria]]
id = "AC-22"
test_file = "tests/test_skills.py"
test_function = "test_skill_definition_is_immutable"
[[acceptance_criteria]]
id = "AC-23"
test_file = "tests/test_skills.py"
test_function = "test_validation_failure_has_no_partial_result"
[[acceptance_criteria]]
id = "AC-24"
test_file = "tests/test_skills.py"
test_function = "test_loader_does_not_modify_files"
[[acceptance_criteria]]
id = "AC-25"
test_file = "tests/test_skills.py"
test_function = "test_loader_does_not_modify_git"
[[acceptance_criteria]]
id = "AC-26"
test_file = "tests/test_skills.py"
test_function = "test_loader_never_executes_content"
[[acceptance_criteria]]
id = "AC-27"
test_file = "tests/test_skills.py"
test_function = "test_declarations_do_not_grant_capabilities"
[[acceptance_criteria]]
id = "AC-28"
test_file = "tests/test_skills.py"
test_function = "test_no_external_yaml_dependency"
[[acceptance_criteria]]
id = "AC-29"
test_file = "tests/test_skills.py"
test_function = "test_validation_is_deterministic"
[[acceptance_criteria]]
id = "AC-30"
test_file = "tests/test_skills.py"
test_function = "test_skills_api_has_no_generic_runner_execute_skill_or_pipeline"
+++

# HERMES-0003 — Contratos e Carregamento de Skills

## Status

Implementado

## Resumo para o Responsável pelo Projeto

O Hermes passará a ler um arquivo `skills/<skill-id>/SKILL.md` indicado
explicitamente e a verificar se ele obedece ao contrato versão 1. Nesta fase,
o arquivo será apenas dado: seu conteúdo não será executado, não concederá
permissões e não poderá causar escrita em arquivos ou no Git.

## Contexto

O repositório já contém o contrato documental de skills em `skills/README.md`
e uma primeira instância em `skills/git-preflight/SKILL.md`. Esse contrato
declara oito campos de metadados e nove seções Markdown obrigatórias, mas o
núcleo Python ainda não possui uma representação estruturada nem um mecanismo
oficial para carregar e validar um `SKILL.md`.

O comportamento diferente observado no Windows PowerShell 5.1 ao ler UTF-8
sem codificação explícita também exige que a codificação faça parte do
contrato, em vez de depender do padrão da plataforma.

## Problema Confirmado

Hoje, a conformidade de um `SKILL.md` depende exclusivamente de revisão manual.
O Hermes não consegue distinguir programaticamente um contrato válido de um
arquivo com metadados ambíguos, campos incorretos, identificador divergente do
diretório ou seções ausentes e fora de ordem.

Sem uma fronteira estrita de carregamento, futuros consumidores poderiam
interpretar dados inválidos de formas diferentes ou atribuir efeito operacional
a campos que são apenas declarações.

## Explicação em Linguagem Simples

Uma skill é, por enquanto, uma ficha descritiva. O loader abre a ficha pelo
caminho informado, confirma que ela está escrita em UTF-8, verifica cada campo
e cada seção exigida e, somente se tudo estiver correto, devolve uma cópia
estruturada e imutável dessas informações.

O loader não segue instruções escritas na ficha. Declarar que uma skill requer
Git ou permite solicitar escrita não instala, executa nem autoriza nada.

## Comportamento Atual

- `skills/README.md` documenta o contrato v1.
- `skills/git-preflight/SKILL.md` é um exemplo real desse contrato.
- Não existe pacote `hermes_ops.skills`.
- Não existem `SkillStatus`, `SkillRisk` ou `SkillDefinition`.
- Não existem loader ou validator de skills.
- Não existem registry, runner ou CLI de skills.

## Comportamento Desejado

Uma chamada de carregamento recebe o caminho explícito de um `SKILL.md`. O
Hermes lê o arquivo explicitamente como UTF-8, separa o front matter do corpo
Markdown, aplica apenas a gramática textual fechada do contrato v1 e valida os
metadados, a correspondência entre `id` e diretório e as nove seções H2.

Somente a validação completa produz um resultado. O modelo previsto contém os
enums `SkillStatus` e `SkillRisk` e um `SkillDefinition` imutável,
preferencialmente conforme o padrão existente:

```python
@dataclass(frozen=True, slots=True)
```

`SkillDefinition` deve conter, no mínimo:

- `schema_version`;
- `id`;
- `version`;
- `status`;
- `description`;
- `risk`;
- `requires` em representação ordenada e imutável;
- `allows_write`;
- `path`, com o caminho de origem;
- `body`, com o corpo Markdown preservado depois da linha de fechamento do
  front matter.

Nesta fase, `path` e `body` pertencem diretamente a `SkillDefinition`. Não
existe um `SkillDocument` separado.

O fluxo conceitual é:

```text
SKILL.md
  -> arquivo existe
  -> UTF-8 válido
  -> front matter presente e fechado
  -> parser v1
  -> campos exatos
  -> tipos e valores válidos
  -> id corresponde ao diretório
  -> corpo Markdown válido
  -> 9 seções únicas e ordenadas
  -> SkillDefinition imutável
```

### Contrato de Metadados v1

O front matter começa na primeira linha do documento e usa delimitadores
isolados `---`:

```text
---
<metadados>
---
```

Exatamente estes oito campos são obrigatórios e únicos:

```text
schema_version
id
version
status
description
risk
requires
allows_write
```

Campos desconhecidos, ausentes ou duplicados invalidam o documento.

#### `schema_version`

Aceita somente a representação textual exata `1`, depois de `trim`. Valores
como `01`, `+1`, `1.0`, `"1"`, `true` e qualquer outra versão ou forma são
inválidos.

#### `id`

Deve ser uma string não vazia que:

- contenha somente letras minúsculas ASCII, números e hífen;
- comece e termine com letra ou número;
- não contenha espaços ou barras;
- corresponda exatamente ao nome do diretório pai de `SKILL.md`.

O formato pode ser expresso como `[a-z0-9](?:[a-z0-9-]*[a-z0-9])?`.
Não existe quoting: `git-preflight` é válido, mas `"git-preflight"` inclui
as aspas no valor e é rejeitado pela gramática.

#### `version`

Aceita somente decimal positivo, sem sinal, no formato `[1-9][0-9]*`, depois
de `trim`. `bool` não conta como inteiro válido. `0`, `-1`, `+1`, `01`, `1.0`,
`true`, `false` e `"1"` são inválidos.

#### `status`

Aceita somente os tokens literais `draft`, `active` ou `deprecated`, depois de
`trim`. Não existe quoting; por exemplo, `active` é válido e `"active"` é
inválido.

#### `description`

É texto literal de uma única linha: todo o conteúdo depois do primeiro `:`
pertence ao valor, com espaços externos removidos. O resultado não pode ficar
vazio e não pode continuar em outra linha. O parser não infere números,
booleanos ou outros tipos para este campo. Assim, `description: 123` produz o
texto `123` e `description: true` produz o texto `true`; ambos são válidos.
Aspas não têm semântica especial e, se presentes, fazem parte do texto após
o `trim`.

#### `risk`

Aceita somente os tokens literais `low`, `medium` ou `high`, depois de `trim`.
Não existe quoting; `low` é válido e `"low"` é inválido.

#### `requires`

É uma coleção ordenada de strings. Aceita a forma vazia:

```text
requires: []
```

E a forma em lista:

```text
requires:
  - git
  - pytest
```

Na forma em lista, `requires:` deve ter valor vazio depois de `trim`. Cada linha
de item deve começar exatamente com `  - `; o restante literal da linha é o
item, depois de `trim`. Item vazio ou duplicado é inválido, e a ordem declarada
é preservada em representação imutável. Itens não possuem quoting ou escaping
especial: aspas, se presentes, pertencem ao item.

O próximo campo válido no nível superior encerra a lista. Enquanto a lista
estiver aberta, uma linha que não seja item com o prefixo exato nem próximo
campo permitido causa erro. Outra indentação, listas aninhadas, mapas,
`requires: [git]`, `requires: ["git"]` e qualquer outra forma são inválidos.

#### `allows_write`

Aceita exclusivamente os tokens literais `true` e `false`, depois de `trim`,
sem coerção. `True`, `False`, `TRUE`, `FALSE`, `yes`, `no`, `1`, `0`,
`"true"` e `'false'` são inválidos. O campo é declarativo e nunca concede
capacidade real de escrita.

### Gramática Textual Fechada do Parser v1

O parser v1 é textual, orientado a linhas, e não usa semântica YAML. Em uma
linha escalar, separa `chave: valor` no primeiro caractere `:`. A chave deve
corresponder exatamente a um dos campos permitidos; o valor restante é
submetido a `trim` e validado pela regra específica do campo.

Não existe interpretação de comentários: `#` não inicia comentário e pertence
ao valor. Aspas simples ou duplas não criam strings especiais, não existe
escaping ou coerção automática, e valores não continuam na linha seguinte. Os
tipos são determinados pelas regras de cada campo, nunca por inferência YAML.

A gramática reconhece somente:

- uma atribuição de campo escalar por linha, separada no primeiro `:`;
- `requires: []` para a coleção vazia;
- `requires:` com valor vazio, seguido de itens iniciados exatamente por
  `  - ` e encerrado pelo próximo campo válido de nível superior.

Qualquer linha inesperada causa erro, sem fallback. O parser rejeita
explicitamente:

- campos desconhecidos ou duplicados;
- mapas ou listas aninhados;
- anchors e aliases;
- tags YAML;
- merge keys;
- valores YAML multiline;
- objetos arbitrários;
- sintaxe de comentário, quoting ou escaping usada como se tivesse semântica
  YAML;
- qualquer sintaxe fora da gramática fechada acima.

Não será adicionada dependência de PyYAML. O parser não deve ampliar
silenciosamente a gramática aceita em `schema_version: 1`.

### Contrato do Corpo Markdown

O corpo deve conter exatamente uma ocorrência de cada uma destas nove seções
H2, nesta ordem:

```text
## Objetivo
## Entradas
## Pré-condições
## Procedimento
## Saídas
## Falhas
## Restrições
## Evidências
## Pós-condições
```

Uma seção obrigatória é uma linha de heading Markdown H2 real, fora de code
fence, formada por `##`, espaço e o nome canônico da seção; espaços externos
ao fim da linha podem ser ignorados. Menções em texto comum, headings de outro
nível e texto dentro de code fence não satisfazem o requisito.

Ausência, duplicidade ou ordem incorreta invalida o contrato. Outros headings
podem existir e não alteram a ordem relativa das nove seções obrigatórias.

O corpo retornado deve preservar exatamente os caracteres existentes depois da
linha que fecha o front matter, inclusive quebras de linha e Markdown; a
validação não o normaliza nem o reescreve.

## Fora do Escopo

- execução de skills;
- registry global ou descoberta automática de todas as skills;
- CLI de skills;
- pipelines;
- autorização ou concessão de capacidades;
- shell ou subprocessos;
- instalação ou download de skills;
- plugins;
- escrita em arquivos;
- escrita no Git;
- parser YAML completo;
- alteração de `skills/README.md`, `skills/git-preflight/SKILL.md` ou
  `pyproject.toml` nesta fase.

## Entradas

- Um caminho explícito para `skills/<skill-id>/SKILL.md`.
- O arquivo apontado, codificado em UTF-8.
- O nome do diretório pai, usado para conferir o campo `id`.

O loader não procura pais, irmãos ou outras skills e não descobre arquivos
automaticamente. A leitura deve ser equivalente a:

```python
path.read_text(encoding="utf-8")
```

## Saídas

Em caso válido, a saída é um `SkillDefinition` completo e imutável, com enums
para status e risco, origem, metadados validados e corpo Markdown preservado.

Em caso inválido, a saída é uma falha controlada com distinção semântica
testável. Nenhum objeto parcial é retornado, nenhum conteúdo é executado e
nenhum arquivo ou estado Git é modificado.

## Invariantes e Regras de Segurança

1. Ler `SKILL.md` nunca executa seu conteúdo.
2. Metadados são dados e Markdown é texto.
3. `allows_write` nunca concede permissão real.
4. `requires` não instala, importa nem executa nada.
5. Falha de leitura, parsing ou validação não produz objeto parcial.
6. O loader não modifica o `SKILL.md` nem qualquer outro arquivo.
7. O loader não modifica index, HEAD, referências ou configuração Git.
8. Não existe fallback permissivo.
9. O resultado válido é imutável, inclusive a coleção `requires`.
10. A validação é determinística para os mesmos bytes, caminho e contrato v1.
11. A leitura usa UTF-8 explicitamente e não depende do locale da plataforma.
12. O parser usa apenas a biblioteca padrão do Python 3.11.

## Pseudocódigo

O pseudocódigo descreve decisões e resultados, sem fixar a divisão final entre
módulos Python.

### `load_skill(path)`

```text
FUNÇÃO load_skill(caminho):
    TRATAR caminho como o arquivo explícito fornecido pelo chamador
    NÃO procurar outras skills, diretórios pais ou arquivos alternativos

    SE o arquivo não existir ou não for um arquivo regular:
        FALHAR com SKILL_FILE_NOT_FOUND

    TENTAR ler todos os caracteres com UTF-8 explícito
    SE os bytes não formarem UTF-8 válido:
        FALHAR com SKILL_INVALID_ENCODING
    SE ocorrer outra falha de leitura:
        PROPAGAR uma falha controlada de carregamento, sem resultado parcial

    (texto_de_metadados, corpo) = split_front_matter(texto)
    metadados = parse_contract_v1(texto_de_metadados)
    metadados_validados = validate_metadata(metadados, caminho.parent.name)
    validate_required_sections(corpo)

    CONSTRUIR SkillDefinition imutável com todos os dados validados,
        a origem explícita e o corpo preservado
    RETORNAR somente o objeto completo
```

### `split_front_matter(text)`

```text
FUNÇÃO split_front_matter(texto):
    DIVIDIR o texto em linhas preservando as terminações de linha

    SE a primeira linha não for exatamente o delimitador ---:
        FALHAR com SKILL_FRONT_MATTER_MISSING

    PROCURAR a próxima linha que seja exatamente o delimitador ---
    SE ela não existir:
        FALHAR com SKILL_FRONT_MATTER_INVALID
    SE não houver conteúdo de metadados entre os delimitadores:
        FALHAR com SKILL_FRONT_MATTER_INVALID

    EXTRAIR os metadados sem incluir os delimitadores
    EXTRAIR como corpo todos os caracteres após o delimitador final,
        sem normalizar quebras de linha ou conteúdo Markdown
    RETORNAR (metadados, corpo)
```

### `parse_contract_v1(metadata_text)`

```text
FUNÇÃO parse_contract_v1(texto_de_metadados):
    CRIAR resultado vazio e conjunto de campos já vistos
    PERCORRER as linhas na ordem declarada

    PARA cada linha:
        SE uma lista requires estiver aberta:
            SE a linha começar exatamente com dois espaços, hífen e espaço:
                EXTRAIR como item o restante literal depois do prefixo
                REMOVER espaços externos do item
                SE o item ficar vazio:
                    FALHAR com SKILL_INVALID_REQUIRES
                REGISTRAR o item na ordem declarada
                CONTINUAR para a próxima linha
            SE a linha declarar um próximo campo permitido no nível superior:
                ENCERRAR a lista e processar esse campo
            SENÃO:
                FALHAR com SKILL_FRONT_MATTER_INVALID

        SE a linha não contiver dois-pontos:
            FALHAR com SKILL_FRONT_MATTER_INVALID
        SEPARAR chave e valor no primeiro caractere dois-pontos
        REMOVER espaços externos do valor
        SE a chave já foi vista:
            FALHAR com SKILL_DUPLICATE_FIELD
        SE a chave não pertencer aos oito campos do contrato:
            FALHAR com SKILL_UNKNOWN_FIELD

        SE a chave for requires:
            SE o valor for exatamente []:
                REGISTRAR coleção vazia
            SENÃO SE o valor estiver vazio:
                ABRIR lista para consumir itens com prefixo exato
            SENÃO:
                FALHAR com SKILL_FRONT_MATTER_INVALID
        SENÃO:
            REGISTRAR o texto literal para validação pela regra do campo

        REGISTRAR a chave exatamente uma vez no resultado

    SE requires abriu uma lista sem qualquer item antes do fim:
        FALHAR com SKILL_INVALID_REQUIRES

    RETORNAR o conjunto estruturado de valores, ainda sem criar SkillDefinition
```

### `validate_metadata(...)`

```text
FUNÇÃO validate_metadata(metadados, nome_do_diretorio):
    PARA cada um dos oito campos obrigatórios:
        SE estiver ausente:
            FALHAR com SKILL_REQUIRED_FIELD_MISSING

    SE schema_version não for exatamente o texto 1:
        FALHAR com SKILL_UNSUPPORTED_SCHEMA

    SE id não seguir o padrão ASCII definido:
        FALHAR com SKILL_INVALID_ID
    SE id não for exatamente igual a nome_do_diretorio:
        FALHAR com SKILL_ID_DIRECTORY_MISMATCH

    SE version não corresponder a [1-9][0-9]*:
        FALHAR com SKILL_INVALID_VERSION
    SE status não for draft, active ou deprecated:
        FALHAR com SKILL_INVALID_STATUS
    SE o texto literal de description ficar vazio após trim:
        FALHAR com SKILL_INVALID_DESCRIPTION
    SE risk não for low, medium ou high:
        FALHAR com SKILL_INVALID_RISK

    SE requires contiver item vazio ou duplicado:
        FALHAR com SKILL_INVALID_REQUIRES
    CONVERTER requires para representação ordenada e imutável

    SE allows_write não for exatamente o texto true nem o texto false:
        FALHAR com SKILL_INVALID_ALLOWS_WRITE

    RETORNAR todos os metadados validados, sem executar ou autorizar nada
```

### `validate_required_sections(body)`

```text
FUNÇÃO validate_required_sections(corpo):
    DEFINIR a sequência esperada das nove seções H2
    CRIAR lista vazia de seções obrigatórias encontradas
    PERCORRER o corpo linha por linha, acompanhando abertura e fechamento
        de code fences Markdown

    PARA cada linha fora de code fence:
        SE for heading H2 real com um dos nove nomes canônicos:
            ADICIONAR o nome à lista encontrada

    PARA cada nome esperado:
        SE não aparecer na lista encontrada:
            FALHAR com SKILL_REQUIRED_SECTION_MISSING
        SE aparecer mais de uma vez:
            FALHAR com SKILL_DUPLICATE_SECTION

    SE a lista encontrada não estiver na sequência esperada:
        FALHAR com SKILL_SECTION_ORDER_INVALID

    RETORNAR sucesso sem modificar o corpo
```

## Fluxo Principal

1. Receber o caminho explícito de `SKILL.md`.
2. Confirmar que o arquivo existe e é regular.
3. Ler o arquivo com UTF-8 explícito.
4. Separar front matter fechado e corpo Markdown preservado.
5. Interpretar os metadados com a gramática textual fechada do parser v1.
6. Confirmar campos exatos, tipos e valores.
7. Comparar `id` com o nome do diretório pai.
8. Localizar headings H2 obrigatórios fora de code fences.
9. Confirmar unicidade e ordem das nove seções.
10. Construir e retornar um `SkillDefinition` imutável.

Qualquer falha interrompe o fluxo antes da construção do resultado.

## Casos de Erro e Limites

A representação concreta pode usar subclasses, um erro único com código ou uma
abordagem híbrida. As distinções abaixo são parte do contrato testável.

| Situação | Código estável | Resultado |
|----------|---------------|-----------|
| Arquivo ausente ou não regular | `SKILL_FILE_NOT_FOUND` | Falha sem descoberta alternativa |
| Bytes não formam UTF-8 válido | `SKILL_INVALID_ENCODING` | Falha sem texto parcial |
| Delimitador inicial ausente | `SKILL_FRONT_MATTER_MISSING` | Falha antes do parsing |
| Delimitador final ausente, metadados vazios ou sintaxe proibida | `SKILL_FRONT_MATTER_INVALID` | Falha sem fallback YAML |
| Campo obrigatório ausente | `SKILL_REQUIRED_FIELD_MISSING` | Falha identificando o campo |
| Campo desconhecido | `SKILL_UNKNOWN_FIELD` | Falha; schema v1 permanece fechado |
| Campo duplicado | `SKILL_DUPLICATE_FIELD` | Falha sem sobrescrever valor |
| `schema_version` diferente do token textual `1` | `SKILL_UNSUPPORTED_SCHEMA` | Falha sem interpretação parcial |
| `id` fora do padrão | `SKILL_INVALID_ID` | Falha de validação |
| `id` diferente do diretório pai | `SKILL_ID_DIRECTORY_MISMATCH` | Falha de validação |
| `version` não corresponde a `[1-9][0-9]*` | `SKILL_INVALID_VERSION` | Falha de validação |
| `status` fora do enum | `SKILL_INVALID_STATUS` | Falha de validação |
| `description` vazia após `trim` ou continuada em outra linha | `SKILL_INVALID_DESCRIPTION` | Falha de validação |
| `risk` fora do enum | `SKILL_INVALID_RISK` | Falha de validação |
| `requires` inválido, vazio em item ou duplicado | `SKILL_INVALID_REQUIRES` | Falha de validação |
| `allows_write` não é booleano literal | `SKILL_INVALID_ALLOWS_WRITE` | Falha de validação |
| Seção H2 obrigatória ausente | `SKILL_REQUIRED_SECTION_MISSING` | Falha identificando a seção |
| Seção H2 obrigatória duplicada | `SKILL_DUPLICATE_SECTION` | Falha identificando a seção |
| Seções obrigatórias fora de ordem | `SKILL_SECTION_ORDER_INVALID` | Falha de validação |

Erros de permissão ou de I/O diferentes de arquivo ausente devem continuar
controlados e não podem expor um objeto parcial. O código público específico
para essas falhas operacionais será definido junto da arquitetura de erros,
sem fundi-las semanticamente com contrato inválido.

## Critérios de Aceitação

- **AC-01**: O loader recebe somente um caminho explícito e não descobre outras skills.
- **AC-02**: `skills/git-preflight/SKILL.md` real é carregado como contrato v1 válido.
- **AC-03**: A leitura usa UTF-8 explícito e preserva acentos; bytes UTF-8 inválidos produzem `SKILL_INVALID_ENCODING`.
- **AC-04**: Front matter ausente produz `SKILL_FRONT_MATTER_MISSING`; front matter sem fechamento produz `SKILL_FRONT_MATTER_INVALID`.
- **AC-05**: Os oito campos são obrigatórios e únicos; campo ausente, desconhecido ou duplicado produz seu código estável correspondente.
- **AC-06**: Somente o token textual `1`, após `trim`, é aceito em `schema_version`; `01`, `+1`, `1.0`, `"1"`, `true` e outras formas produzem `SKILL_UNSUPPORTED_SCHEMA`.
- **AC-07**: `id` aceita somente o padrão definido e deve ser idêntico ao diretório pai; cada violação mantém seu código específico.
- **AC-08**: `version` aceita somente `[1-9][0-9]*` e rejeita `0`, negativos, sinal, zero inicial, fração, booleanos e valores entre aspas.
- **AC-09**: `status` aceita somente `draft`, `active` e `deprecated`.
- **AC-10**: `description` é texto literal de uma linha, não vazio após `trim`; descrição normal, `123` e `true` são aceitos como texto, enquanto valor vazio ou somente espaços é rejeitado.
- **AC-11**: `risk` aceita somente `low`, `medium` e `high`.
- **AC-12**: `requires: []` é válido e produz coleção ordenada imutável vazia.
- **AC-13**: Uma lista `requires` com vários itens válidos preserva a ordem.
- **AC-14**: Item vazio ou duplicado em `requires` produz `SKILL_INVALID_REQUIRES`; indentação, forma inline ou estrutura diferente da gramática fechada é rejeitada.
- **AC-15**: `allows_write: true` e `allows_write: false` são válidos e preservados como booleanos.
- **AC-16**: `allows_write` rejeita variações de caixa, `yes`, `no`, `1`, `0`, `"true"` e `'false'` com `SKILL_INVALID_ALLOWS_WRITE`.
- **AC-17**: A gramática textual orientada a linhas separa escalares no primeiro `:`, não interpreta `#`, aspas, escaping ou coerção YAML, e rejeita mapas, listas aninhadas, anchors, aliases, tags, merge keys e multiline.
- **AC-18**: Cada uma das nove seções H2 obrigatórias, quando removida isoladamente, produz `SKILL_REQUIRED_SECTION_MISSING`.
- **AC-19**: Seção obrigatória duplicada produz `SKILL_DUPLICATE_SECTION` e seções fora de ordem produzem `SKILL_SECTION_ORDER_INVALID`.
- **AC-20**: Menção do nome de seção em texto comum, heading de nível diferente ou code fence não conta como H2 obrigatório.
- **AC-21**: `SkillDefinition.body` é idêntico ao trecho original posterior ao front matter, e não existe `SkillDocument` separado.
- **AC-22**: `SkillDefinition`, seu `path`, seu `body` e sua coleção `requires` pertencem ao mesmo modelo e não podem ser mutados após a criação.
- **AC-23**: Falha em qualquer etapa não retorna `SkillDefinition` total nem parcial.
- **AC-24**: Carregamento e validação não modificam o arquivo de origem nem qualquer outro arquivo.
- **AC-25**: Carregamento e validação não modificam index, HEAD, referências ou configuração Git.
- **AC-26**: Conteúdo semelhante a instruções, comandos ou código permanece texto e nunca é executado.
- **AC-27**: `requires` não instala, importa ou executa dependências, e `allows_write` não autoriza escrita.
- **AC-28**: A implementação usa somente a biblioteca padrão e não adiciona PyYAML nem outra dependência YAML.
- **AC-29**: O mesmo arquivo, caminho e contrato v1 produzem deterministicamente o mesmo resultado ou o mesmo erro.
- **AC-30**: Na fase HERMES-0003 não eram expostos registry, discovery,
  runner, execução, pipelines ou CLI de skills. HERMES-0004/0005/0006
  supersedem somente essas ausências limitadas à fase por meio das APIs
  explicitamente especificadas. `run_skill` e a CLI piloto `skill run` são
  permitidos exclusivamente pelo contrato fechado da HERMES-0006; permanecem
  proibidos runner genérico, `execute_skill`, pipeline e qualquer execução
  genérica ou dinâmica de skills.

## Plano de Testes

Os testes futuros ficarão em `tests/test_skills.py`, usarão `tmp_path` para
contratos artificiais e incluirão um teste leve do arquivo real. Cada teste
deverá referenciar `Spec: HERMES-0003 / AC-NN` em docstring ou comentário.

| Critério | Tipo de Teste | Arquivo | Nome do Teste | O que o Teste Comprova |
|----------|---------------|---------|---------------|------------------------|
| AC-01 | Unitário | `tests/test_skills.py` | `test_loads_only_explicit_path` | Não há descoberta automática |
| AC-02 | Integração leve | `tests/test_skills.py` | `test_loads_real_git_preflight_skill` | Contrato real é válido |
| AC-03 | Unitário | `tests/test_skills.py` | `test_utf8_accents_and_invalid_encoding` | UTF-8 explícito, acentos e erro de encoding |
| AC-04 | Unitário | `tests/test_skills.py` | `test_front_matter_boundaries` | Ausência e falta de fechamento têm códigos distintos |
| AC-05 | Parametrizado | `tests/test_skills.py` | `test_exact_required_fields` | Ausência, desconhecido e duplicado são rejeitados |
| AC-06 | Parametrizado | `tests/test_skills.py` | `test_schema_version_is_exact_textual_one` | Somente `1` após trim é aceito; formas alternativas falham |
| AC-07 | Parametrizado | `tests/test_skills.py` | `test_id_format_and_directory_match` | Formato do id e correspondência ao diretório |
| AC-08 | Parametrizado | `tests/test_skills.py` | `test_version_matches_unsigned_positive_decimal` | Valida `[1-9][0-9]*` e rejeita sinais, zero inicial, bool, aspas e fração |
| AC-09 | Parametrizado | `tests/test_skills.py` | `test_status_enum` | Enum de status é fechado |
| AC-10 | Parametrizado | `tests/test_skills.py` | `test_description_is_non_empty_literal_text` | Aceita descrição normal, `123` e `true` como texto; rejeita vazio e somente espaços |
| AC-11 | Parametrizado | `tests/test_skills.py` | `test_risk_enum` | Enum de risco é fechado |
| AC-12 | Unitário | `tests/test_skills.py` | `test_requires_empty_list` | Lista vazia é válida e imutável |
| AC-13 | Unitário | `tests/test_skills.py` | `test_requires_preserves_order` | Múltiplos itens preservam ordem |
| AC-14 | Parametrizado | `tests/test_skills.py` | `test_requires_rejects_invalid_grammar_and_items` | Duplicado, vazio, indentação incorreta, inline e estruturas extras falham |
| AC-15 | Parametrizado | `tests/test_skills.py` | `test_allows_write_literal_booleans` | `true` e `false` são válidos |
| AC-16 | Parametrizado | `tests/test_skills.py` | `test_allows_write_rejects_non_booleans` | Formas não booleanas são rejeitadas |
| AC-17 | Parametrizado | `tests/test_skills.py` | `test_parser_uses_closed_textual_grammar` | Primeiro `:`, `#` literal e ausência de quoting, escaping, coerção e extensões YAML |
| AC-18 | Parametrizado | `tests/test_skills.py` | `test_each_required_section_missing` | Cada seção ausente falha isoladamente |
| AC-19 | Parametrizado | `tests/test_skills.py` | `test_required_sections_unique_and_ordered` | Duplicidade e ordem têm códigos próprios |
| AC-20 | Parametrizado | `tests/test_skills.py` | `test_section_names_must_be_real_h2` | Texto, H3 e fence não geram falso positivo |
| AC-21 | Unitário | `tests/test_skills.py` | `test_markdown_body_is_preserved_in_skill_definition` | `body` fica no modelo e preserva o trecho posterior ao front matter |
| AC-22 | Unitário | `tests/test_skills.py` | `test_skill_definition_is_immutable` | Modelo com `path`, `body` e `requires` rejeita mutação |
| AC-23 | Unitário | `tests/test_skills.py` | `test_validation_failure_has_no_partial_result` | Erro não vaza objeto parcial |
| AC-24 | Segurança | `tests/test_skills.py` | `test_loader_does_not_modify_files` | Origem e árvore permanecem inalteradas |
| AC-25 | Segurança | `tests/test_skills.py` | `test_loader_does_not_modify_git` | Estado Git permanece inalterado |
| AC-26 | Segurança | `tests/test_skills.py` | `test_loader_never_executes_content` | Comandos e código no texto não executam |
| AC-27 | Segurança | `tests/test_skills.py` | `test_declarations_do_not_grant_capabilities` | `requires` e `allows_write` não causam efeitos |
| AC-28 | Estrutural | `tests/test_skills.py` | `test_no_external_yaml_dependency` | Nenhuma dependência ou import YAML externo |
| AC-29 | Unitário | `tests/test_skills.py` | `test_validation_is_deterministic` | Repetições produzem resultado idêntico |
| AC-30 | Estrutural | `tests/test_skills.py` | `test_skills_api_has_no_generic_runner_execute_skill_or_pipeline` | Extensões posteriores explícitas são permitidas; runner genérico, `execute_skill` e pipeline permanecem ausentes |

Os testes de segurança abrangem comportamento permitido, comportamento
bloqueado e regressão: carregamento do contrato real permitido; construções
perigosas ou ambíguas bloqueadas; e conteúdo executável tratado somente como
texto, sem mutações.

## Arquivos Provavelmente Afetados

Futuramente, na implementação desta especificação:

- `src/hermes_ops/skills/__init__.py`;
- `src/hermes_ops/skills/models.py`;
- `src/hermes_ops/skills/loader.py`;
- `src/hermes_ops/skills/validator.py`;
- `tests/test_skills.py`.

Possivelmente:

- `src/hermes_ops/core/errors.py`.

Não se prevê alteração em `pyproject.toml`, pois o parser v1 deve usar somente a
biblioteca padrão.

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| 2026-08-09 | Carregar somente um caminho explícito | Mantém a fase pequena e sem descoberta implícita | Registry ou descoberta global |
| 2026-08-09 | Contrato v1 fechado com oito campos obrigatórios e únicos | Evita interpretação divergente e fallback permissivo | Campos desconhecidos tolerados |
| 2026-08-09 | Parser textual com gramática v1 fechada | O contrato determina tipos por campo e não usa inferência ou semântica YAML | Adicionar PyYAML ou reimplementar YAML completo |
| 2026-08-09 | Leitura UTF-8 explícita | Garante comportamento consistente, inclusive no Windows PowerShell 5.1 | Depender da codificação padrão da plataforma |
| 2026-08-09 | Nove headings H2 únicos e ordenados | Torna o corpo documental verificável sem interpretar sua intenção | Aceitar mera menção textual |
| 2026-08-09 | `allows_write` e `requires` são apenas declarações | O arquivo não pode conceder capacidades nem causar execução | Tratar metadados como autorização |
| 2026-08-09 | Resultado completo e imutável | Impede estado parcial ou alteração posterior do contrato validado | Modelo mutável ou retorno parcial |
| 2026-08-09 | `path` e `body` pertencem a `SkillDefinition` | Mantém origem, metadados e corpo preservado em um único resultado imutável | Criar `SkillDocument` separado nesta fase |

## Decisões Pendentes

1. Representar falhas por subclasses, erro único com código ou abordagem
   híbrida.

Essa decisão não altera os códigos semânticos, a imutabilidade observável ou
os critérios de aceitação desta especificação.

## Alternativas Descartadas

1. **Adicionar PyYAML agora:** aumenta a superfície e a dependência para um
   contrato que exige apenas uma gramática textual pequena e fechada.
2. **Implementar YAML completo internamente:** amplia o escopo e o risco sem
   necessidade funcional na versão 1.
3. **Executar a skill durante o carregamento:** mistura dados com execução e
   viola a fronteira de segurança desta fase.
4. **Tratar `allows_write` como autorização:** um campo autodeclarado não pode
   ampliar capacidades.

## Riscos Restantes

- A gramática aceita é intencionalmente incompatível com recursos avançados
  de YAML; autores precisam permanecer no formato documentado.
- Necessidades futuras podem justificar parser externo ou nova
  `schema_version`, mas não devem ampliar silenciosamente a versão 1.
- A lógica de headings precisa acompanhar code fences corretamente para não
  aceitar exemplos como se fossem seções reais.
- A arquitetura final da hierarquia de erros ainda depende da decisão
  pendente, sem alterar o comportamento público especificado.

## Evidências da Implementação

| Campo | Valor |
|-------|-------|
| Commit da implementação | `ad462f0` — `feat(skills): implementa carregamento e validacao de contratos` |
| Estado da integração | Concluído na branch `feature/skills-contract`; ainda não integrado |
| Arquivos alterados | `src/hermes_ops/core/errors.py`; `src/hermes_ops/skills/__init__.py`; `src/hermes_ops/skills/models.py`; `src/hermes_ops/skills/loader.py`; `src/hermes_ops/skills/validator.py`; `tests/test_skills.py` |
| Testes direcionados | `.venv\Scripts\python.exe -m pytest tests/test_skills.py` → 93 collected, 93 passed, 0 failed, 0 errors, exit code 0 |
| Suíte completa | `.venv\Scripts\python.exe -m pytest` → 208 collected, 206 passed, 2 skipped, 0 failed, 0 errors, exit code 0 |
| Validação de sintaxe ou compileall | Validação somente leitura com `ast.parse` nos 5 arquivos Python de produção alterados → 5 arquivos válidos, exit code 0 |
| Empacotamento | Não aplicável — a configuração de distribuição não foi alterada; a suíte completa executou os testes de packaging sem falhas |
| git diff --check | Sem avisos antes do commit de implementação |
| Plataformas e versões validadas | Windows, Python 3.13.13 |
| CI | Não aplicável — integração ainda não realizada |
| Limitações do ambiente | Symlinks de arquivo e diretório indisponíveis no ambiente Windows; 2 testes ignorados |
| Preservação LF/CRLF | AC-21 cobre LF e CRLF; prova isolada: `expected_crlf=116`, `actual_crlf=116`, `body_equal=True` |
| Auditoria final | Segurança, modelo/imutabilidade, parser v1, preservação LF/CRLF, Markdown/H2 e erros/códigos: PASS; nenhum problema bloqueante, importante ou opcional restante |
| Estado pós-commit | Working tree limpa; Hermes worktree `exit_code=0`; Hermes preflight `exit_code=0` |
| Dependências e superfícies | Nenhuma dependência externa adicionada; nenhum registry, runner ou CLI criado |
| Integridade documental | A HERMES-0003 não foi alterada durante a implementação até esta atualização documental |

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| 2026-08-09 | Danilo Fukuda | Criação inicial da especificação HERMES-0003 em status Rascunho | — |
| 2026-08-09 | Codex | Correção da estrutura Markdown e consolidação do contrato v1, pseudocódigo, erros, critérios e plano de testes | Solicitação documental |
| 2026-08-09 | Codex | Fechamento da gramática textual v1 e definição de `path` e `body` em `SkillDefinition` | Correção após auditoria |
| 2026-08-09 | Codex | Promoção do status para Aprovado após auditoria final, com `justification` documental para os ACs sem testes implementados | Auditoria final concluída sem divergências materiais |
| 2026-08-10 | Codex | Promoção do status para Implementado, substituição das justificativas temporárias por vínculos reais AC→teste e registro das evidências finais do SKILL-2 | Commit `ad462f0`; auditoria final e validações concluídas sem divergências |
| 2026-08-10 | Codex | Reconciliação do AC-30 com a extensão posterior da HERMES-0004: registry e discovery deixam de ser proibição permanente; runner, execução, pipeline e CLI operacional permanecem fora do escopo | Supersessão limitada pela HERMES-0004; sem alteração do loader, parser ou modelo |
| 2026-08-10 | Codex | Reconciliação controlada do AC-30 com a HERMES-0006: `run_skill` e a CLI piloto deixam de ser proibições absolutas, mantendo vedados runner genérico, `execute_skill`, pipeline e execução dinâmica | Supersessão limitada ao piloto read-only; loader, parser e modelo permanecem inalterados |
