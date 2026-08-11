---
id: mission-audit
schema_version: 1
version: 1
status: active
description: Coleta evidencias locais dirigidas por uma missao explicita, sem executar ou modificar conteudo.
risk: low
allows_write: false
requires: []
---

# Mission Audit

## Objetivo

Collect a bounded, deterministic evidence pack for an explicit audit mission.

## Entradas

An exact target project root and a mission supplied by the caller.

## Pré-condições

The target and mission must satisfy the closed validation contract.

## Procedimento

Validate, read bounded source files, correlate evidence, and report completeness.

## Saídas

A read-only evidence pack with files, regions, symbols, relationships, tests,
limitations, unresolved questions, and completeness.

## Falhas

Invalid missions, unsafe paths, structural limits, and read instability fail closed.

## Restrições

The skill only reads controlled source files. It does not execute project code,
spawn processes, use Git, access the network, or write files.

## Evidências

Every selected item includes an explicit reason and traceable location.

## Pós-condições

The target remains unchanged and insufficient evidence is reported explicitly.
