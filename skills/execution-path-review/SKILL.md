---
schema_version: 1
id: execution-path-review
version: 1
status: active
description: Revisa compatibilidade entre produtor e consumidor em um caminho executável, com evidência local e somente leitura.
risk: low
requires: []
allows_write: false
---

# Execution Path Review

## Objetivo

Comparar a garantia produzida por uma fronteira com a pré-condição aplicada por
um consumidor alcançável em código Python autorizado.

## Entradas

Raiz exata, símbolos simples de produtor e consumidor, missão opcional e escopo
estrutural opcional.

## Pré-condições

O alvo, os símbolos e o escopo devem satisfazer os contratos fechados do
Hermes; produtor e consumidor precisam ter definição única para análise plena.

## Procedimento

Ler fontes pelo leitor controlado, localizar definições e um caminho executável
explícito, resumir domínios suportados pela v1 e classificá-los conservadoramente.

## Saídas

Relatório imutável com classificação, caminho, limitações e achados rastreáveis.

## Falhas

Entradas inválidas, paths inseguros, limites de leitura e sintaxe Python
inválida falham fechados. Evidência incompleta gera classificação conservadora.

## Restrições

Não executa ou importa código do alvo, não usa Git, rede ou subprocessos e não
escreve arquivos. Nomes isolados nunca confirmam incompatibilidade.

## Evidências

Achados referenciam linhas relativas do produtor, da propagação e da guarda do
consumidor, além de descrever domínio, requisito e cenário alcançável.

## Pós-condições

O alvo permanece inalterado e nenhuma incompatibilidade é confirmada sem todos
os elos executáveis exigidos.
