---
schema_version: 1
id: code-audit
version: 1
status: active
description: Audita código permitido de um projeto-alvo com evidências locais, sem executar ou modificar conteúdo.
risk: low
requires: []
allows_write: false
---

# Code Audit

## Objetivo

Examinar de forma estática, limitada e somente leitura os arquivos de código
permitidos de um projeto-alvo e produzir achados técnicos sustentados por
evidências locais.

## Entradas

- `project_path`: raiz exata do projeto-alvo.
- limites e regras fechados definidos pelo Hermes.

## Pré-condições

- O alvo deve existir e ser um diretório direto.
- O catálogo e a policy devem autorizar esta skill passiva e read-only.
- A árvore não pode conter indirections inseguras nas regiões inspecionadas.

## Procedimento

1. Validar a raiz exata sem seguir symlinks, junctions ou reparse points.
2. Inventariar deterministicamente somente a árvore contida no alvo.
3. Aplicar extensões, exclusões e limites fixos do Hermes.
4. Ler candidatos como bytes, com tamanho limitado e UTF-8 estrito.
5. Aplicar somente as cinco regras estáticas fechadas da HERMES-0008.
6. Produzir resumo e achados imutáveis em ordem determinística.
7. Falhar sem resultado parcial quando a auditoria não puder ser concluída.

## Saídas

- status e exit code da execução;
- resumo de diretórios, arquivos, bytes, regras e limites;
- achados com severidade, classificação, arquivo, região, evidência,
  observação, justificativa e sugestão.

## Falhas

Falhas de raiz, path, limite, tipo, encoding, leitura ou estabilidade possuem
códigos determinísticos e bloqueiam a auditoria inteira.

## Restrições

Esta skill não pode executar ou importar código do alvo, chamar subprocessos,
Git ou shell, acessar rede, escrever arquivos, criar temporários no alvo nem
alterar HEAD, refs, staging, working tree ou branch.

## Evidências

Cada achado aponta somente para path relativo e região contida no alvo. Trechos
são limitados, sanitizados e têm possíveis valores secretos redigidos.

## Pós-condições

- Nenhum arquivo ou estado Git foi modificado pela skill.
- A auditoria foi concluída integralmente ou falhou fechada.
- Nenhum achado foi emitido sem gatilho local suficiente.

