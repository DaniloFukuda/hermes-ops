# Hermes Skills

Este diretório contém os contratos operacionais das skills do Hermes.

Uma skill descreve uma capacidade operacional, suas entradas, limites,
evidências e pós-condições. O arquivo SKILL.md não concede permissões nem
acesso direto ao sistema. As capacidades continuam sob controle do núcleo
do Hermes.

## Descoberta

Cada skill deve existir no formato:

skills/<skill-id>/SKILL.md

O nome do diretório deve ser igual ao campo `id` declarado no front matter.

## Contrato v1

Todo SKILL.md deve começar com front matter YAML contendo:

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

## Estado desta fase

Nesta primeira fase, SKILL.md é somente um contrato declarativo.

Ainda não existem:

- loader de skills;
- registry;
- runner;
- execução automática;
- concessão de capacidades baseada no arquivo.

Esses componentes serão adicionados em fases posteriores.