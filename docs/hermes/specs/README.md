# Especificações do Hermes Ops

## Objetivo

Esta pasta contém as especificações versionadas para alterações funcionais não
triviais do `hermes-ops`. Cada especificação documenta o ciclo completo:

```
necessidade
  → especificação
  → explicação simples
  → pseudocódigo
  → critérios de aceitação
  → testes
  → implementação
  → validação
  → evidências
```

---

## Convenção de Nomes

Arquivos seguem o padrão:

```
HERMES-XXXX-descrição-curta.md
```

Onde `XXXX` é um número sequencial de 4 dígitos (0001, 0002, ...).

### Como Escolher o Próximo Número

1. Liste os arquivos existentes em `docs/hermes/specs/`.
2. Extraia o maior número usado.
3. Incremente em 1.
4. Preencha com zeros à esquerda até 4 dígitos.

Exemplo: se o último for `HERMES-0003`, o próximo será `HERMES-0004`.

---

## Estados Permitidos

| Estado | Significado |
|--------|-------------|
| **Rascunho** | Em elaboração, não aprovado para implementação. |
| **Aprovado** | Revisado e aceito; pronto para implementação. |
| **Em implementação** | Código e testes sendo escritos. |
| **Implementado** | Código, testes e especificação atualizados; validação concluída. |
| **Substituído** | Uma nova especificação substituiu esta; mantida para histórico. |

---

## Quando Criar uma Especificação

**Obrigatório para:**
- Nova funcionalidade visível ao usuário ou que altere comportamento público.
- Correção de bug que muda semântica de erro, status ou saída.
- Mudança de regra de segurança ou validação.
- Refatoração que altere contratos entre módulos.
- Qualquer alteração que exija novos testes ou mude testes existentes.

**Dispensável para:**
- Correções tipográficas ou de formatação em documentação.
- Ajustes internos sem impacto observável (ex.: renomear variável privada).
- Atualizações de dependências ou tooling sem mudança funcional.

---

## Como Vincular Critérios aos Testes

Em cada novo teste (ou teste alterado), inclua no docstring ou comentário:

```python
# Spec: HERMES-XXXX / AC-YY
```

Ou em docstring:

```python
"""
Spec: HERMES-XXXX / AC-YY
Valida que...
"""
```

Isso permite rastreabilidade bidirecional: da especificação ao teste e vice-versa.

---

## Como Atualizar uma Especificação

1. Se a especificação está em **Rascunho** ou **Aprovada** (sem implementação):
   - Edite diretamente.
   - Atualize a seção **Histórico de alterações**.

2. Se a especificação está **Em implementação** ou **Implementada**:
   - Não altere o conteúdo original que gerou a implementação.
   - Adicione uma entrada em **Histórico de alterações** descrevendo o que
     mudou, por quê, e referencie o commit.
   - Se o comportamento público mudou, crie uma nova especificação
     (`HERMES-XXXX-v2` ou novo número) e marque a anterior como
     **Substituído**.

---

## Como Registrar uma Decisão Alterada

Na seção **Decisões tomadas** ou **Histórico de alterações**, registre:

- Data.
- Autor/responsável.
- O que foi decidido.
- Por que a alternativa anterior foi descartada.
- Referência a issue, PR ou discussão (se houver).

---

## Como Marcar uma Especificação como Substituída

1. Altere o **Status** para `Substituído`.
2. Adicione no topo do arquivo:

   > **Substituída por:** `HERMES-YYYY-nova-descricao.md`
   > **Motivo:** breve explicação.

3. Na nova especificação, referencie a anterior em **Alternativas descartadas**
   ou **Histórico de alterações**.

---

## Como Registrar Evidências

Na seção **Evidências da implementação**, preencha:

| Campo | Exemplo |
|-------|---------|
| Commit | `a1b2c3d` |
| Testes direcionados | `pytest tests/test_xyz.py -v` → 12 passed |
| Suíte completa | `pytest` → 113 passed, 2 skipped |
| compileall | `python -m compileall src/hermes_ops` → OK |
| Empacotamento | `python -m build` → wheel + sdist criados |
| git diff --check | sem avisos |
| Plataformas validadas | Windows 10 (Python 3.11.15), Ubuntu 22.04 (Python 3.11.9) |
| Limitações do ambiente | Symlinks indisponíveis no Windows CI; 2 testes skipped |

---

## Como Tratar Divergências

Se em qualquer momento **código, testes e especificação divergirem**:

1. **Pare**.
2. Documente a divergência na especificação (seção **Divergências
   encontradas** ou **Histórico de alterações**).
3. Decida qual reflete a intenção correta:
   - Se a especificação está certa: corrija código e testes.
   - Se o código/testes estão certos: atualize a especificação.
   - Se houve mudança de escopo: registre como decisão alterada.
4. Só continue após alinhar os três.

---

## Princípios Fundamentais

> **A especificação não substitui os testes.**
>
> **Os testes não substituem a explicação do comportamento.**
>
> A especificação explica *o quê* e *por quê* em linguagem acessível.
> O pseudocódigo mostra *como* (lógica, não sintaxe).
> Os testes provam *que funciona* e guardam contra regressão.
> Os três devem caminhar juntos.