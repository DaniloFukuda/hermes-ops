---
schema_version: 1
id: git-preflight
version: 1
status: active
description: Valida o estado do Git e do repositório antes de operações do Hermes.
risk: low
requires:
  - git
allows_write: false
---

# Git Preflight

## Objetivo

Verificar se o ambiente Git e o estado do repositório são compatíveis com
a operação pretendida antes que o Hermes realize alterações.

A skill é somente de inspeção e não pode modificar arquivos, referências,
configurações ou o estado do repositório.

## Entradas

- `repository_path`: caminho do repositório que será inspecionado.
- contexto de configuração do Hermes aplicável ao repositório.

## Pré-condições

- O caminho informado deve poder ser inspecionado.
- A política de Git opcional do Hermes deve ser respeitada.
- A configuração aplicável ao repositório deve ser resolvida pelo núcleo,
  e não pela própria skill.

## Procedimento

1. Verificar se o caminho informado existe.
2. Verificar se o executável Git está disponível.
3. Determinar se o caminho pertence a um repositório Git.
4. Respeitar a política configurada para Git obrigatório ou opcional.
5. Identificar a branch atual quando disponível.
6. Identificar o commit HEAD quando disponível.
7. Inspecionar o estado da working tree.
8. Identificar arquivos modificados, adicionados, removidos ou não rastreados.
9. Produzir avisos para condições permitidas que mereçam atenção.
10. Produzir evidências da inspeção sem alterar o repositório.

## Saídas

A execução futura desta skill deverá produzir um resultado estruturado contendo,
no mínimo:

- status;
- caminho do repositório;
- disponibilidade do Git;
- identificação de repositório Git;
- branch atual, quando aplicável;
- commit HEAD, quando aplicável;
- estado limpo ou sujo da working tree;
- avisos;
- falhas;
- evidências.

## Falhas

Falhas previstas devem possuir códigos estáveis.

Códigos iniciais:

- `SKILL_PATH_NOT_FOUND`
- `SKILL_GIT_NOT_AVAILABLE`
- `SKILL_REPOSITORY_INVALID`
- `SKILL_GIT_REQUIRED`
- `SKILL_GIT_INSPECTION_FAILED`

A indisponibilidade do Git não deve ser tratada automaticamente como falha fatal
quando a política ativa permitir operação sem Git.

## Restrições

Esta skill não pode:

- criar ou alterar arquivos;
- executar `git add`;
- executar `git commit`;
- executar `git push`;
- executar `git pull`;
- executar `git fetch`;
- executar `git checkout`;
- executar `git switch`;
- executar `git reset`;
- executar `git clean`;
- alterar configuração Git;
- criar, excluir ou mover branches;
- criar ou remover tags;
- alterar o index;
- alterar o HEAD;
- executar comandos Git com efeitos persistentes.

A skill também não pode transformar avisos em permissões implícitas para
operações posteriores.

## Evidências

Quando aplicável, a execução futura deverá registrar evidências equivalentes a:

- caminho efetivamente inspecionado;
- disponibilidade e versão do Git;
- raiz do repositório;
- branch atual;
- commit HEAD;
- resumo da working tree;
- política de Git aplicada;
- avisos e falhas encontrados.

Evidências devem ser obtidas por operações somente de leitura.

## Pós-condições

Ao finalizar:

- nenhum arquivo deve ter sido alterado pela skill;
- o index Git deve permanecer inalterado;
- HEAD e referências Git devem permanecer inalterados;
- configurações Git devem permanecer inalteradas;
- deve existir resultado explícito da inspeção;
- qualquer condição impeditiva deve estar registrada antes de uma operação
  posterior do Hermes.