# HERMES-XXXX — Título

## Status

Rascunho | Aprovado | Em implementação | Implementado | Substituído

## Resumo para o Responsável pelo Projeto

*Duas a três frases explicando o que muda, por que importa e qual o impacto
visível. Linguagem não técnica.*

## Contexto

*Descreva a situação que motivou a mudança. Referencie issues, discussões ou
observações concretas.*

## Problema Confirmado

*Declaração objetiva do que está errado, inconsistente ou ausente. Baseada em
código, testes ou comportamento observado — não em suposição.*

## Comportamento Atual

*O que acontece hoje. Cite caminhos de código, mensagens de erro, códigos de
saída, estados retornados.*

## Comportamento Desejado

*O que deve acontecer após a mudança. Descreva entradas, saídas, mensagens,
status e efeitos colaterais esperados.*

## Fora do Escopo

*Liste explicitamente o que NÃO será alterado nesta especificação. Evita
*scope creep*.*

## Entradas

*Parâmetros, configurações, variáveis de ambiente, arquivos lidos, estado
prévio necessário.*

## Saídas

*Valores retornados, arquivos escritos, mensagens emitidas, códigos de saída,
estados alterados.*

## Invariantes e Regras de Segurança

*Regras que **nunca** podem ser violadas, mesmo em casos de erro. Exemplos:*

- *Configuração insegura sempre bloqueia antes de executar Git.*
- *Nenhum segredo aparece em saída pública.*
- *Caminhos absolutos nunca vazam em JSON.*

## Pseudocódigo

*Lógica independente da linguagem, legível por quem não programa em Python.
Explique decisões, não traduza linhas.*

```text
SE condição de segurança:
    BLOQUEAR
    NÃO executar operação perigosa

SE configuração.opcional E erro operacional:
    REGISTRAR aviso
    CONTINUAR sem falhar

SE condição crítica:
    FALHAR com código específico
```

## Fluxo Principal

*Passo a passo do caminho feliz. Use numeração ou marcadores.*

1. Validar entrada X.
2. Ler configuração Y.
3. Se Z, aplicar regra W.
4. Retornar resultado.

## Casos de Erro e Limites

*Tabela ou lista de situações de falha, entrada inválida, estado ausente,
recurso indisponível, timeout, permissão negada, etc. Para cada um: o que
acontece, código de erro, mensagem.*

| Situação | Comportamento | Código | Mensagem |
|----------|---------------|--------|----------|
| ...      | ...           | ...    | ...      |

## Critérios de Aceitação

Use identificadores: **AC-01**, **AC-02**, **AC-03**...

- **AC-01**: Descrição verificável.
- **AC-02**: Descrição verificável.
- **AC-03**: Descrição verificável.

## Plano de Testes

| Critério | Tipo de Teste | Arquivo | Nome do Teste | O que o Teste Comprova |
|----------|---------------|---------|---------------|------------------------|
| AC-01    | Unitário      | tests/test_xxx.py | test_xxx_ac01 | ... |
| AC-02    | Integração    | tests/test_xxx.py | test_xxx_ac02 | ... |
| AC-03    | Segurança     | tests/test_xxx.py | test_xxx_ac03_blocked / test_xxx_ac03_allowed | ... |

*Para correções de segurança, inclua obrigatoriamente:*
- *Teste de comportamento permitido*
- *Teste de comportamento bloqueado*
- *Teste de não regressão*

## Arquivos Provavelmente Afetados

- `src/hermes_ops/...`
- `tests/test_...py`
- `docs/...` (se houver)

## Decisões Tomadas

| Data | Decisão | Justificativa | Alternativa Descartada |
|------|---------|---------------|------------------------|
| ...  | ...     | ...           | ...                    |

## Alternativas Descartadas

*Descreva brevemente opções consideradas e por que não foram adotadas.*

## Riscos Restantes

*O que pode dar errado, o que não foi coberto, dependências externas,
limitações conhecidas.*

## Evidências da Implementação

| Campo | Valor |
|-------|-------|
| Commit | `hash` |
| Testes direcionados | `comando` → `resultado` |
| Suíte completa | `comando` → `resultado` |
| compileall | `comando` → `resultado` |
| Empacotamento | `comando` → `resultado` |
| git diff --check | `resultado` |
| Plataformas validadas | `SO / Python version` |
| Limitações do ambiente | `ex.: symlinks indisponíveis no Windows CI` |

## Histórico de Alterações

| Data | Autor | Alteração | Referência |
|------|-------|-----------|------------|
| ...  | ...   | ...       | ...        |