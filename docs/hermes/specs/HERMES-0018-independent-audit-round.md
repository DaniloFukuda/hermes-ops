# HERMES-0018 — Independent Audit Round v1

Status: Implementado

## 1. Contexto

O Hermes possui auditores estáticos independentes e, por meio da HERMES-0017,
um contrato comum para normalizar e ordenar findings. Ainda não existe uma
rodada que execute mais de um auditor sobre uma única visão autorizada das
fontes.

## 2. Problema confirmado

Hoje cada skill lê o target separadamente. Se o repositório mudar entre essas
leituras, auditores da mesma rodada podem analisar conteúdos diferentes
(`snapshot drift`). Também não há contrato para isolamento de falhas,
normalização posterior a todas as execuções ou ranking agregado único.

## 3. Explicação em linguagem simples

A rodada deve fotografar os arquivos permitidos uma única vez. Cada auditor
recebe essa mesma fotografia, junto apenas com seus próprios parâmetros. Um
auditor nunca vê a conclusão do outro. Depois que todos terminarem, seus
findings são convertidos para o formato comum e ordenados uma única vez.

## 4. Comportamento atual

`code-audit` e `execution-path-review` são skills públicas unitárias. Seus
wrappers recebem um target e cada um chama o controlled reader. O executor não
compõe skills. O normalizador e o ranker HERMES-0017 são funções puras, mas não
há orquestrador que os aplique a uma rodada.

## 5. Comportamento desejado

- Validar target, structural scope e pedidos antes da leitura.
- Construir um snapshot imutável por rodada.
- Executar sequencialmente somente `code-audit` e
  `execution-path-review`, sobre documentos já lidos.
- Isolar entradas, resultados e falhas de cada auditor.
- Normalizar somente depois que todos os outcomes existirem.
- Chamar o ranker HERMES-0017 exatamente uma vez.
- Produzir resultado imutável, sanitizado e determinístico.

## 6. Fora de escopo

- Skill pública, CLI ou manifest para a rodada.
- Paralelismo, threads, processos ou asyncio.
- RepositoryMap, índice global de símbolos ou call graph global.
- `mission-audit` ou `MissionEvidencePack` como entrada da rodada.
- Novos auditores, execução do target, rede ou subprocessos.
- Blast radius, impact taxonomy, ranking por LLM, deduplicação semântica ou
  correção automática.

## 7. Invariantes e regras de segurança

1. O target informado é a raiz exata; pais e irmãos não são descobertos.
2. O controlled reader preserva as regras vigentes de path, symlink, reparse
   point, encoding, tipo e tamanho.
3. O structural scope é normalizado e aplicado antes da leitura de arquivos.
4. Todos os paths públicos são relativos e usam `/`.
5. O snapshot é frozen, canonicamente ordenado e não contém raiz absoluta,
   timestamp, duração ou PID.
6. Cada auditor recebe um input frozen novo contendo o mesmo snapshot e apenas
   seus parâmetros locais.
7. Outcomes, findings, claims, rankings e contextos acumulados nunca são
   entradas de outro auditor.
8. Falha individual não cancela o outro auditor nem cria finding sintético.
9. Falha ao construir o snapshot impede todos os auditores.
10. Nenhum componente pós-snapshot relê o filesystem.
11. A rodada é estática e read-only; não importa nem executa código do target.

## 8. Entradas e saídas

### Entrada

`AuditRoundRequest` contém schema, target explícito, structural scope e uma
tupla de pedidos fechados. `CodeAuditRequest` não possui parâmetros adicionais.
`ExecutionPathAuditRequest` contém producer e consumer não vazios.

Pedidos são validados e ordenados por `auditor_id`. Duplicatas e IDs não
registrados falham antes do snapshot.

### Snapshot

`ScopedSourceSnapshot` contém schema, scope normalizado, documentos integrais,
limites aplicados, limitações e digest SHA-256 da identidade lógica.

### Saída

`AuditRoundResult` contém schema, proveniência sanitizada do snapshot, outcomes
ordenados, relatório ranqueado, status da rodada e limitações.

Cada `AuditorOutcome` registra auditor e normalizador com suas versões, um dos
quatro estados locais, resultado nativo fechado quando disponível, error code
determinístico e limitações.

## 9. Pseudocódigo independente de linguagem

```text
receber pedido da rodada
validar todos os pedidos, rejeitando desconhecidos e duplicados
ordenar pedidos pelo identificador do auditor

tentar ler uma fotografia completa e autorizada das fontes
se a fotografia falhar:
    retornar rodada FAILED sem iniciar auditor algum

para cada pedido na ordem canônica:
    criar uma entrada local nova com a mesma fotografia
    tentar executar o auditor usando somente os documentos da fotografia
    se o auditor falhar:
        guardar outcome FAILED sanitizado e continuar
    senão:
        classificar seu outcome sem mostrar o resultado aos demais

somente depois que todos os outcomes existirem:
    normalizar os resultados que possuem findings
    juntar todos os findings normalizados
    chamar o ranker uma vez

se algum outcome falhou ou teve evidência insuficiente:
    status da rodada é COMPLETED_WITH_LIMITATIONS
senão:
    status da rodada é COMPLETED

retornar resultado imutável e deterministicamente serializável
```

## 10. Fluxo principal

1. Validação e canonicalização do request.
2. Leitura controlada única e construção do digest.
3. Execução isolada dos cores puros dos dois auditores.
4. Materialização de todos os outcomes.
5. Normalização HERMES-0017 dos outcomes com findings.
6. Ranking HERMES-0017 único.
7. Derivação do status e serialização canônica.

## 11. Erros e limites

- Pedido inválido, duplicado ou desconhecido: erro contratual antes da leitura.
- Falha estrutural de leitura: resultado `FAILED`, zero chamadas de auditor.
- Exceção individual: outcome `FAILED`, error code estável, sem traceback ou
  texto incidental.
- Evidência insuficiente permanece distinta de no findings.
- Limites compartilhados são os do controlled reader: profundidade 32, 5.000
  diretórios, 1.000 arquivos, 512 KiB por arquivo e 20 MiB no total.
- Caps analíticos continuam locais a cada auditor; não há `ExecutionContext`
  acumulado.

## 12. Critérios de aceitação

- **AC-01:** uma rodada constrói exatamente um snapshot.
- **AC-02:** os dois auditores recebem o mesmo snapshot e digest.
- **AC-03:** o segundo auditor não recebe resultado ou conclusão do primeiro.
- **AC-04:** permutar pedidos não altera outcomes, findings, ranking ou JSON.
- **AC-05:** auditor duplicado falha fechado antes da leitura.
- **AC-06:** auditor desconhecido falha fechado antes da leitura.
- **AC-07:** falha do primeiro auditor não impede o segundo.
- **AC-08:** falha do segundo preserva findings válidos do primeiro.
- **AC-09:** evidência insuficiente é distinta de no findings.
- **AC-10:** falha de snapshot impede o início de todos os auditores.
- **AC-11:** normalização começa somente após todas as execuções.
- **AC-12:** o ranker é chamado exatamente uma vez por rodada com snapshot.
- **AC-13:** no findings não cria limitation.
- **AC-14:** failed cria limitation sem finding sintético.
- **AC-15:** mutação física posterior ao snapshot não muda a visão do segundo
  auditor.
- **AC-16:** structural scope impede leitura de arquivo fora do escopo.
- **AC-17:** resultado e snapshot serializam deterministicamente.
- **AC-18:** wrappers públicos existentes permanecem semanticamente
  compatíveis com seus cores.
- **AC-19:** nenhum componente pós-snapshot relê o filesystem.
- **AC-20:** paths públicos e erros permanecem sanitizados.

## 13. Plano de testes

`tests/test_audit_round.py` cobre AC-01 a AC-17 e AC-19/20 com spies,
instrumentação de eventos, permutações, falhas e alteração da fixture. Testes
de equivalência entre wrappers e cores, somados às suítes existentes de
`code-audit` e `execution-path-review`, cobrem AC-18. As suítes do controlled
reader, HERMES-0017, mission audit, Analysis Pack, modelos e serialização são
regressões obrigatórias.

## 14. Arquivos provavelmente afetados

- `src/hermes_ops/skills/controlled_reader.py`
- `src/hermes_ops/skills/code_audit.py`
- `src/hermes_ops/skills/execution_path_review.py`
- novos modelos/orquestrador internos de audit round
- `tests/test_audit_round.py`
- esta especificação

Não são necessários CLI, catálogo público, manifest ou handler do executor.

## 15. Riscos conhecidos

- Refatorar cores pode alterar silenciosamente ordenação ou evidência antiga.
- Serializar resultados nativos heterogêneos pode introduzir campos incidentais.
- Captura excessivamente ampla de exceções pode esconder defeitos do
  orquestrador; a fronteira deve limitar-se à chamada individual do auditor.
- Um digest que use raiz física, metadata ou ordem de entrada quebraria
  portabilidade e determinismo.
- Compartilhar qualquer coleção mutável ou contexto acumulado quebraria a
  independência futura necessária para paralelismo.

## 16. Decisão arquitetural

A v1 é uma composição interna. `SkillDefinition.version` continua versionando
a skill pública; `AuditorDefinition` registra separadamente a versão do adapter
da rodada e sua relação explícita com a skill correspondente. Não há exposição
pública nova sem uma necessidade concreta posterior.

## 17. Evidência de validação

- Primeiro RED: `tests/test_audit_round.py` falhou com `ModuleNotFoundError`
  antes da criação do módulo de produção.
- Testes HERMES-0018: 13 passed.
- Regressões diretamente relacionadas: 257 passed, 1 skipped.
- Suíte integral: 643 passed, 2 skipped; corresponde ao baseline de 630
  testes mais os 13 testes da HERMES-0018.
- Wheel e sdist: construídos com sucesso.
- Cada AC-01 a AC-20 possui cobertura automatizada direta no novo arquivo ou
  regressão explícita dos contratos anteriores, conforme o plano de testes.
