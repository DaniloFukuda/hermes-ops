---
spec_id: HERMES-0014
title: Structural Scope do Mission Audit
version: 1
status: draft
author: Danilo Fukuda
date: 2026-08-16
depends_on:
  - HERMES-0009
  - HERMES-0010
---

# HERMES-0014 — Structural Scope do Mission Audit

## 1. Contexto

O `mission-audit` (introduzido em HERMES-0009) coleta evidências locais dirigidas por uma `--mission` explícita. Atualmente, o escopo de descoberta é **todo o TARGET** (todos os arquivos permitidos sob o diretório do projeto). Não existe mecanismo para restringir a superfície de investigação sem alterar a semântica da missão.

## 2. Problema Confirmado

Usuários precisam delimitar **ONDE** a auditoria pode operar, separadamente de **O QUE** investigar:

- `--mission` = "auditar validação de entrada" (semântica)
- Structural scope = "somente `src/auth/` e `tests/auth/`" (superfície permitida)

Sem essa separação, a missão carrega ambiguidade semântica e o discovery varre superfície desnecessária, consumindo orçamento e diluindo relevância.

## 3. Explicação em Linguagem Natural

Adicionar uma opção CLI repetível `--include-path` ao comando `skill run mission-audit`. Cada valor é um caminho relativo ao TARGET. Quando nenhum `--include-path` é fornecido, o comportamento permanece **exatamente** o atual. Quando há pelo menos um `--include-path`, o discovery, a seleção e a evidence operam **somente** sobre arquivos dentro das superfícies autorizadas.

- Diretório incluído → autoriza recursivamente todos os descendentes.
- Arquivo incluído → autoriza somente aquele arquivo.
- Paths absolutos, `../`, ou fora do TARGET → rejeitados na validação.
- Duplicatas → normalizadas deterministicamente.
- Paths inexistentes → comportamento explícito (rejeitado com erro claro).

## 4. Comportamento Atual

- `skill run mission-audit --project <TARGET> --mission "..."` descobre **todos** arquivos permitidos no TARGET.
- `read_source_documents()` faz walk completo respeitando `ALLOWED_EXTENSIONS`, `EXCLUDED_DIRECTORIES`, limites de profundidade/arquivos/bytes.
- `build_evidence_pack()` recebe todo o inventário e seleciona/pontua baseado nos termos da missão.
- Nenhum filtro de superfície existe.

## 5. Comportamento Desejado

```
skill run mission-audit \
  --project /caminho/projeto \
  --mission "validar entrada" \
  --include-path src/auth \
  --include-path tests/auth
```

- Discovery lê inventário completo mas **filtra** antes da seleção.
- Somente arquivos sob `src/auth/**` e `tests/auth/**` participam de scoring, regiões, símbolos, relacionamentos, testes.
- `--mission` continua significando **O QUE** buscar (termos, relevância).
- `--include-path` determina **ONDE** buscar (superfície permitida).
- Sem `--include-path` → comportamento idêntico ao atual (compatibilidade total).

## 6. Fora do Escopo

- `--exclude-path` (negação) — não na primeira versão.
- Glob patterns (`**/*.py`) — apenas paths literais relativos.
- Escopo por camada arquitetural (ex: "apenas services") — não na primeira versão.
- Integração com `evidence analyze` — o evidence pack já carrega o scope usado.
- Persistência de scope em configuração — apenas CLI.
- Modificação de `code-audit` — skill separada.

## 7. Invariantes e Regras de Segurança

| Regra | Descrição |
|-------|-----------|
| **I-01** | Paths absolutos são rejeitados na validação CLI. |
| **I-02** | Qualquer componente `..` no path é rejeitado. |
| **I-03** | Path resolvido fora do TARGET é rejeitado. |
| **I-04** | `valid_relative_path()` (já existente em `controlled_reader.py`) é a autoridade única de validação. |
| **I-05** | Duplicatas (mesmo path, path pai/filho redundante) são normalizadas: mantém o mais específico, ordena lexicograficamente. |
| **I-06** | Path inexistente no filesystem → erro explícito `STRUCTURAL_SCOPE_PATH_NOT_FOUND`. |
| **I-07** | Sem `--include-path` → **zero** alteração no fluxo legado (compatibilidade binária de comportamento). |
| **I-08** | Com `--include-path` → discovery **não produz** arquivo fora da superfície. |
| **I-09** | Selection **não reintroduz** arquivo fora da superfície. |
| **I-10** | Evidence pack **não contém** arquivo fora da superfície. |
| **I-11** | Resultados permanecem determinísticos (mesma entrada = mesmo pack). |
| **I-12** | `--mission` mantém semântica atual (termos, stopwords, normalização). |

## 8. Entradas e Saídas

### Entradas (CLI)
```
--include-path <relpath>   (repetível, opcional)
--mission <string>         (existente, obrigatório para mission-audit)
--project <path>           (existente, obrigatório)
--format text|json         (existente)
```

### Saídas
- `MissionEvidencePack` com campo opcional `structural_scope: tuple[str, ...]` (paths normalizados usados).
- Mesmo `schema_version: 1`, mesmo `target: "<PROJECT_ROOT>"`.
- Exit codes inalterados: `0` (sufficient), `3` (insufficient), `2` (invalid input), `4` (external failure).

## 9. Pseudocode Independente de Linguagem

```
FUNCTION normalize_structural_scope(raw_paths: list[str], target_root: Path) -> tuple[str, ...]:
    IF raw_paths is empty:
        RETURN empty_tuple

    normalized = []
    FOR each raw_path in raw_paths:
        # Validação de segurança
        IF is_absolute(raw_path) OR has_parent_traversal(raw_path):
            RAISE "STRUCTURAL_SCOPE_INVALID_PATH"

        candidate = target_root / raw_path
        IF NOT candidate.is_relative_to(target_root):
            RAISE "STRUCTURAL_SCOPE_ESCAPES_TARGET"

        IF NOT candidate.exists():
            RAISE "STRUCTURAL_SCOPE_PATH_NOT_FOUND"

        normalized.append(raw_path.replace("\\", "/"))

    # Deduplicação: remover paths que são prefixo de outro (pai redundante)
    # Ex: ["src/auth", "src/auth/login.py"] → mantém ambos (arquivo + dir são distintos)
    # Ex: ["src/auth", "src/auth/"] → normaliza para "src/auth"
    unique = deduplicate_preserving_file_and_dir(normalized)

    RETURN tuple(sorted(unique))


FUNCTION is_within_scope(relative_path: str, scope: tuple[str, ...]) -> bool:
    IF scope is empty:
        RETURN True  # legacy behavior: everything allowed

    FOR each scope_path in scope:
        IF scope_path ends with "/" OR is_directory(scope_path):
            IF relative_path == scope_path OR relative_path.starts_with(scope_path + "/"):
                RETURN True
        ELSE:  # arquivo explícito
            IF relative_path == scope_path:
                RETURN True
    RETURN False
```

## 10. Fluxo Principal (CORRIGIDO PARA TRUE SCOPED DISCOVERY)

1. **CLI parsing** (`cli.py:build_parser`): adicionar `--include-path` (action='append', default=[])
2. **CLI exec** (`cli.py:_run_skill_cli`): passar `include_paths` para `SkillRunInputs`
3. **Skill dispatch** (`commands/skill.py:run_skill_command`): propagar no `SkillRunInputs`
4. **Mission audit handler** (`skills/mission_audit.py:run_mission_audit`): receber `include_paths`
5. **Normalização** (novo helper em `mission_audit.py`): `normalize_structural_scope(include_paths, target)` → valida + normaliza contra TARGET
6. **Scoped Discovery** (`controlled_reader.py:read_source_documents`): **recebe `allowed_paths=scope`**, restringe candidates **ANTES** da leitura de conteúdo
   - `_inventory()` poda traversal de diretórios inteiramente fora do scope
   - `_read()` **nunca chamado** para arquivos fora do scope
7. **Seleção/Evidence** (`build_evidence_pack`): recebe inventário **já scoped**, processa normalmente
8. **Pack final**: incluir `structural_scope` no `MissionEvidencePack`

**Ponto exato onde arquivo deixa de ser elegível:** Em `controlled_reader.py:_inventory()`, durante enumeração, **antes** de criar `_Candidate` e **muito antes** de `_read()` ser invocado.

## 11. Casos de Erro e Fronteiras

| Código | Causa | Exit Code |
|--------|-------|-----------|
| `STRUCTURAL_SCOPE_INVALID_PATH` | Path absoluto, `..`, chars controle, vazio | 2 |
| `STRUCTURAL_SCOPE_ESCAPES_TARGET` | Path resolve fora do TARGET | 2 |
| `STRUCTURAL_SCOPE_PATH_NOT_FOUND` | Path não existe no filesystem | 2 |
| `MISSION_TERM_LIMIT_EXCEEDED` | Inalterado (herdado) | 2 |

## 12. Critérios de Aceitação (AC)

| AC | Descrição | Teste |
|----|-----------|-------|
| **AC-01** | `--include-path` aceita múltiplos valores (repetível) | CLI parsing test |
| **AC-02** | Cada valor é path relativo ao TARGET (não absoluto) | Security test |
| **AC-03** | Path absoluto → erro `STRUCTURAL_SCOPE_INVALID_PATH` | Security test |
| **AC-04** | Path com `../` → erro `STRUCTURAL_SCOPE_INVALID_PATH` | Security test |
| **AC-05** | Path fora do TARGET → erro `STRUCTURAL_SCOPE_ESCAPES_TARGET` | Security test |
| **AC-06** | Path inexistente → erro `STRUCTURAL_SCOPE_PATH_NOT_FOUND` | Security test |
| **AC-07** | Diretório incluído autoriza descendentes recursivamente | Functional test |
| **AC-08** | Arquivo incluído autoriza somente aquele arquivo | Functional test |
| **AC-09** | Sem `--include-path` → comportamento idêntico ao legado | Regression test |
| **AC-10** | Com `--include-path` → discovery **não lê** arquivo fora da superfície | **True scoped discovery test** |
| **AC-11** | Diretório fora do scope não contribui documentos (pruning de traversal) | **Directory pruning test** |
| **AC-12** | Selection não reintroduz arquivo fora da superfície | Functional test |
| **AC-13** | Evidence pack não contém arquivo fora da superfície | Functional test |
| **AC-14** | Duplicatas normalizadas deterministicamente (ordem lexicográfica) | Determinism test |
| **AC-15** | `--mission` mantém semântica atual (termos, scoring) | Regression test |
| **AC-16** | Results determinísticos: mesma entrada = mesmo pack | Determinism test |
| **AC-17** | `structural_scope` incluído no evidence pack (quando usado) | Model test |

## 13. Plano de Testes

### Segurança (bloqueio)
- `test_include_path_rejects_absolute`
- `test_include_path_rejects_parent_traversal`
- `test_include_path_rejects_escape_target`
- `test_include_path_rejects_nonexistent`
- `test_include_path_rejects_empty_string`

### True Scoped Discovery (NOVO — core da decisão arquitetural)
- `test_scoped_discovery_does_not_read_outside_file` — arquivo fora do scope NÃO tem `_read()` chamado
- `test_scoped_discovery_prunes_outside_directory` — diretório fora do scope não enumera filhos
- `test_scoped_discovery_allows_explicit_file_only` — arquivo explícito incluído, irmãos não
- `test_scoped_discovery_allows_directory_recursive` — diretório incluído autoriza descendentes
- `test_scoped_discovery_mixed_file_and_dir` — combina arquivo + diretório

### Compatibilidade Legada (regressão)
- `test_legacy_without_include_path_unchanged` — todos os testes existentes passam sem alteração
- `test_mission_semantics_preserved` — termos, scoring, stopwords inalterados

### Determinismo
- `test_include_path_deterministic_order` — duplicatas, ordem de entrada não afetam saída
- `test_same_scope_same_mission_same_pack` — pack idêntico em execuções repetidas

### Modelo
- `test_evidence_pack_includes_structural_scope` — campo presente quando usado

## 14. Arquivos Provavelmente Afetados

| Arquivo | Tipo de Mudança |
|---------|-----------------|
| `src/hermes_ops/cli.py` | Adicionar arg `--include-path` em `build_parser()` |
| `src/hermes_ops/cli.py` | Passar `include_paths` em `_run_skill_cli()` |
| `src/hermes_ops/commands/skill.py` | `SkillRunInputs` aceitar `include_paths` |
| `src/hermes_ops/skills/__init__.py` | `run_skill()` propagar para handler |
| `src/hermes_ops/skills/mission_audit.py` | `run_mission_audit()` receber + normalizar + propagar scope |
| `src/hermes_ops/skills/mission_audit.py` | `normalize_structural_scope()` novo helper |
| `src/hermes_ops/skills/mission_audit.py` | `build_evidence_pack()` **remover** filtro pós-discovery, usar inventário já scoped |
| `src/hermes_ops/skills/mission_models.py` | `MissionEvidencePack` adicionar campo `structural_scope` |
| `src/hermes_ops/skills/controlled_reader.py` | `read_source_documents()` aceitar `allowed_paths` opcional |
| `src/hermes_ops/skills/controlled_reader.py` | `_inventory()` receber `allowed_paths` e podar traversal + filtrar candidates antes de `_read()` |
| `src/hermes_ops/skills/controlled_reader.py` | Reutilizar `valid_relative_path()` para consistência |
| `tests/test_mission_audit.py` | Novos testes AC-01 a AC-17 (incluindo true scoped discovery + directory pruning) |
| `tests/test_mission_audit_security.py` | Novos testes de segurança (se arquivo existir) |

## 15. Riscos Conhecidos

| Risco | Mitigação |
|-------|-----------|
| Filtro em `_inventory()` pode ter edge cases com paths pai/filho | Testes exaustivos de combinações; `PurePosixPath` para comparação canônica; `is_within_scope()` centralizada |
| `MissionEvidencePack` schema_version continua 1 com campo novo | Campo opcional com default `()`; validação `__post_init__` tolera ausência |
| Testes existentes podem falhar se dependem de contagem total de arquivos | Verificar que testes legados não assumem contagem absoluta de discovery |
| Directory pruning: path que é prefixo de scope_path mas não exatamente scope_path | Lógica: se path é pai de algum scope_path, deve continuar traversal (ex: scope=`src/auth`, path=`src` → continua) |
| Performance: verificação `is_within_scope` para cada entry | Cache de scope_paths normalizados; early return para scope vazio (legacy) |
| Scope normalizado vs path do filesystem (case sensitivity Windows) | Usar `PurePosixPath` para comparação; filesystem Windows é case-insensitive mas paths no inventory já são `.as_posix()` |
