# Hermes Skills

Este diretório contém os contratos operacionais das skills do Hermes.

Uma skill descreve uma capacidade operacional, suas entradas, limites,
evidências e pós-condições. O arquivo SKILL.md não concede permissões nem
acesso direto ao sistema. As capacidades continuam sob controle do núcleo
do Hermes.

## Layout canônico

Cada skill deve existir no formato:

skills/<skill-id>/SKILL.md

O nome do diretório deve ser igual ao campo `id` declarado no front matter.

## Contrato v1

Todo SKILL.md deve começar com o front matter textual delimitado por `---`
contendo:

- `schema_version`
- `id`
- `version`
- `status`
- `description`
- `risk`
- `requires`
- `allows_write`

### schema_version

Versão do formato do contrato.

Para este contrato:

schema_version: 1

### id

Identificador estável da skill.

Regras:

- minúsculas;
- números são permitidos;
- palavras podem ser separadas por hífen;
- deve ser igual ao nome do diretório.

Exemplo:

git-preflight

### version

Versão inteira positiva da própria skill.

Exemplo:

version: 1

### status

Valores permitidos:

- `draft`
- `active`
- `deprecated`

### description

Descrição curta da responsabilidade da skill.

### risk

Valores permitidos:

- `low`
- `medium`
- `high`

### requires

Lista de capacidades ou dependências declaradas pela skill.

Uma skill sem dependências deve usar:

requires: []

### allows_write

Valor booleano que declara se a skill pode solicitar alterações persistentes.

Valores:

- `true`
- `false`

Este campo é declarativo. Ele não concede capacidade de escrita.

## Seções obrigatórias

Após o front matter, todo SKILL.md deve possuir as seguintes seções:

1. Objetivo
2. Entradas
3. Pré-condições
4. Procedimento
5. Saídas
6. Falhas
7. Restrições
8. Evidências
9. Pós-condições

## Princípios de segurança

1. Um SKILL.md descreve intenção; não concede poder.
2. O núcleo do Hermes controla filesystem, Git, processos e demais capacidades.
3. Skills de leitura não podem alterar arquivos de código ou estado Git.
4. Uma skill deve declarar explicitamente qualquer necessidade de escrita.
5. Falhas devem ser explícitas e auditáveis.
6. A execução deve produzir evidências suficientes para auditoria.
7. Nenhuma skill pode ampliar seu próprio escopo durante a execução.
8. Dependências entre skills devem ser declaradas.
9. A ausência de permissão deve resultar em bloqueio, não em fallback inseguro.
10. O contrato deve ser validado antes de qualquer futura execução.

## Estado atual

O contrato v1 e seu carregamento passivo estão implementados conforme a
HERMES-0003. O pacote `hermes_ops.skills` fornece `load_skill` para carregar e
validar explicitamente um `SKILL.md`, além dos tipos imutáveis
`SkillDefinition`, `SkillStatus` e `SkillRisk`.

O carregamento apenas lê e valida o contrato; ele não executa a skill.
`requires` e `allows_write` continuam declarativos e não instalam dependências
nem concedem capacidades.

O pacote também fornece `SkillRegistry` e `discover_skills(project_root)`. O
discovery considera somente `<project_root>/skills`, reutiliza `load_skill` e
produz um resultado imutável, determinístico e fail-closed. A HERMES-0004,
ainda com Status Aprovado, é a especificação normativa dessa funcionalidade;
a implementação correspondente está presente no código atual e aguarda
fechamento documental.

Continuam inexistentes runner, `run_skill`, `execute_skill`, execução de
`SKILL.md`, pipeline ou CLI operacional de skills, resolução operacional de
`requires`, autorização por `allows_write`, instalação ou download de skills
e plugins.
