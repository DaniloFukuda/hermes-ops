+++
schema_version = 1
id = "HERMES-0037"
title = "Omissões comprovadamente redundantes no Evidence Pack"
status = "Implementado"
owners = ["Danilo"]
created = "2026-11-17"
updated = "2026-11-17"
supersedes = []
related = ["HERMES-0036", "HERMES-0014", "HERMES-0035"]
+++

# HERMES-0037 — Omissões comprovadamente redundantes no Evidence Pack

## 1. Problema

A HERMES-0036 tornou a seleção de símbolos, testes e relacionamentos críticos
prioritária, mantendo os caps de regiões. O comportamento atual ainda trata
qualquer omissão causada por cap como bloqueante, mesmo quando a região omitida
pode ser provada equivalente a uma região selecionada.

A distinção é necessária porque:

- ignorar toda omissão mantém o auditor excessivamente restritivo;
- ignorar omissões apenas pela ausência de `critical_*` pode produzir falso
  `sufficient`;
- somente uma prova determinística de redundância pode liberar a omissão.

A HERMES-0037 complementa a HERMES-0036. Ela não altera retroativamente os
caps, o escopo estrutural ou os critérios de segurança da HERMES-0036.

## 2. Contrato atual preservado

Devem continuar invariáveis:

- `MAX_REGIONS_PER_FILE = 12`;
- `MAX_REGIONS = 300`;
- caps de arquivos, símbolos, relacionamentos, testes e JSON;
- `SELECTION_CAP_REACHED` como sinal de que candidatos foram omitidos;
- `CAP_OMISSION` como sinal de omissão causada por cap;
- `CRITICAL_EVIDENCE_OMITTED` para evidência crítica não selecionada;
- `UNCOVERED_CENTRAL_TERMS` para termos centrais sem ocorrência;
- `--include-path` como autoridade de superfície;
- seleção determinística;
- Evidence Packs legados carregáveis;
- nenhum acesso, escrita, rede, subprocesso ou execução no TARGET.

A ausência de uma razão `critical_symbol` ou `critical_test` nunca é, sozinha,
prova de redundância.

### 2.1 Versionamento da semântica

A semântica nova de omissões redundantes exige:

```text
schema_version = 2
```

Regras:

- Evidence Packs v1 continuam válidos para leitura histórica;
- v1 nunca infere redundância a partir de `CAP_OMISSION`;
- v2 exige suporte explícito de modelo, loader, builder e validator;
- consumidor que não suporte v2 deve rejeitar o pacote de forma fail-closed;
- ausência de `omission_provenance` nunca constitui prova de redundância;
- Evidence Packs v1 não podem ser usados para autorizar `sufficient` com
  `CAP_OMISSION`.

### 2.2 Precedência normativa

HERMES-0037 altera somente a interpretação de omissões comprovadamente
redundantes em Evidence Packs v2. HERMES-0036 continua sendo a referência
para caps, escopo, seleção, termos centrais e demais critérios.

`CAP_OMISSION` e `SELECTION_CAP_REACHED` continuam registrados. `sufficient`
só pode coexistir com `CAP_OMISSION` quando cada omissão individual estiver
classificada como `redundant_evidence_omitted` e possuir provenance v2 válida e
completa.

Qualquer omissão crítica, necessária, incerta, incompleta ou sem provenance
válida permanece bloqueante.

## 3. Classificação formal

### 3.1 `critical_evidence_omitted`

Uma região pertence a esta classe quando pelo menos uma condição é verdadeira:

- definição de símbolo crítico correspondente a termo central;
- definição de teste crítico correspondente a cenário requerido;
- relacionamento estrutural exigido sem região materializada;
- região ativa marcada como protegida por regra de segurança;
- região que é a única evidência de um termo central.

Efeito:

```text
CRITICAL_EVIDENCE_OMITTED = bloqueante
sufficient = false
```

### 3.2 `necessary_evidence_omitted`

Uma região pertence a esta classe quando não é crítica por classificação direta,
mas contém informação que não pode ser reconstruída a partir de evidência
selecionada, por exemplo:

- código ativo sem região equivalente selecionada;
- import que materializa relacionamento necessário;
- teste ou fixture cuja informação causal não aparece em outro trecho;
- ocorrência única de termo central;
- contexto necessário para interpretar o símbolo ou relacionamento crítico.

Efeito:

```text
NECESSARY_EVIDENCE_OMITTED = bloqueante
sufficient = false
```

### 3.3 `redundant_evidence_omitted`

Uma região somente pode pertencer a esta classe quando houver prova de todos
os itens abaixo:

1. não é símbolo crítico;
2. não é teste crítico;
3. não é relacionamento estrutural necessário;
4. não é código ativo com comportamento exclusivo;
5. não contém a única ocorrência de termo central;
6. não é necessária para interpretar uma região crítica;
7. existe região selecionada equivalente de forma determinística;
8. a equivalência é verificável por identidade estável, não por proximidade,
   score ou ausência de classificação crítica.

Para a primeira implementação, a prova mínima permitida fica restrita a uma
região `comment` ou `docstring` que satisfaça simultaneamente:

- mesmo arquivo;
- mesmo `content_kind`;
- excerpt canônico idêntico ao de uma região selecionada;
- exatamente os mesmos motivos e termos associados;
- nenhum relacionamento estrutural;
- nenhum símbolo ou teste associado;
- nenhum termo central exclusivo;
- nenhuma função de interpretação de região crítica.

Duplicatas com a mesma chave de região devem ser agregadas antes da
classificação. Código ativo, imports, fixtures e relacionamentos não podem ser
classificados como redundantes apenas por igualdade lexical.

Qualquer falha ou ausência de prova classifica a região como necessária ou
não comprovada e mantém a omissão bloqueante.

Efeito:

```text
REDUNDANT_EVIDENCE_OMITTED = não bloqueante somente quando a prova é completa
```

A omissão deve continuar registrada em `limitations` junto com
`SELECTION_CAP_REACHED`/`CAP_OMISSION`, mas não deve bloquear `sufficient` se e
somente se todas as omissões do pacote forem comprovadamente redundantes.

## 4. Prova de equivalência

### 4.1 Identidade da região

A chave primária de deduplicação permanece:

```text
(path, start_line, end_line)
```

Razões de regiões com a mesma chave devem ser unidas antes da classificação.
Uma razão crítica agregada não pode ser perdida.

### 4.2 Equivalência textual

Para comentário/docstring, a comparação deve usar uma forma canônica
não-executável, preservando o conteúdo semântico:

- mesmo arquivo;
- mesmo tipo de conteúdo (`comment` ou `docstring`);
- excerpt normalizado de forma determinística;
- mesmos motivos/termos associados;
- uma região equivalente selecionada.

Não usar somente hash de termo, score, posição próxima ou quantidade de
ocorrências.

### 4.3 Cobertura de termos

Antes de liberar uma omissão, cada termo central associado deve aparecer em uma
região selecionada equivalente ou em outra região selecionada que preserve a
mesma função de evidência.

Se houver dúvida, a classificação é:

```text
necessary_evidence_omitted
```

### 4.4 Relacionamentos

Um `EvidenceRelationship` sem `evidence_region` materializada nunca pode ser
redundante. Deve permanecer bloqueante, mesmo que o source e o target estejam
presentes no pack.

### 4.5 Provenance da omissão

A versão 2 deve conter explicitamente o campo:

```text
omission_provenance: tuple[OmissionRecord, ...]
```

O campo é obrigatório no payload v2 e pode ser vazio quando não houver
omissões. Em v1, o campo está ausente e nunca pode ser inferido.

`OmissionRecord` deve conter exatamente:

```text
omission_id: str
omitted_region: {path: str, start_line: int, end_line: int}
equivalent_region: {path: str, start_line: int, end_line: int} | null
content_kind: "active_code" | "comment" | "docstring"
reasons: tuple[str, ...]
associated_terms: tuple[str, ...]
classification: "critical_evidence_omitted" | "necessary_evidence_omitted" | "redundant_evidence_omitted"
cap: str
justification: str
```

Validações obrigatórias:

- `omission_id` deriva deterministicamente de
  `path:start_line:end_line`;
- linhas são inteiros positivos e `start_line <= end_line`;
- `equivalent_region` é obrigatório para redundância;
- a região equivalente deve estar efetivamente selecionada;
- a região equivalente deve permanecer no mesmo `structural_scope`;
- `reasons` e `associated_terms` são tuplas ordenadas e sem duplicatas;
- `classification`, `cap` e `justification` não podem estar vazios;
- registros são ordenados por path, linha inicial, linha final e classificação;
- no máximo `MAX_REGIONS` registros podem ser serializados;
- o payload completo deve respeitar `MAX_JSON_BYTES`.

Se qualquer registro necessário for truncado, inválido, incompleto ou não puder
ser serializado, a classificação é não comprovada e `sufficient = false`.



A seleção deve calcular separadamente:

```text
any_cap_omission
critical_evidence_omitted
necessary_evidence_omitted
redundant_evidence_omitted
```

A regra segura é:

```text
omitted_blocking = (
    critical_evidence_omitted
    or necessary_evidence_omitted
    or unproved_evidence_omitted
    or uncovered_central_terms
    or any_other_existing_blocking_gate
)

sufficient = existing_gates_pass and not omitted_blocking
```

`any_cap_omission` continua sendo registrado sempre que um cap descarta
candidatos. `SELECTION_CAP_REACHED` continua sendo registrado quando a seleção
perde candidatos. Esses sinais não podem ser removidos nem ignorados
silenciosamente.

A presença isolada de `CAP_OMISSION` não autoriza `sufficient`: cada região
omitida precisa de uma classificação individual. Somente quando todas as
regiões omitidas forem `redundant_evidence_omitted`, com prova completa, o cap
pode deixar de ser bloqueante. Qualquer região incompleta, desconhecida ou sem
prova mantém `sufficient = false`.

Se uma única região não puder ser classificada com prova suficiente, o pacote
permanece `insufficient`.

## 6. Compatibilidade

### 6.1 Evidence Pack

Preferir os campos existentes:

- `completeness.incompleteness_codes`;
- `limitations`.

Se for necessário registrar provenance estruturada por região, o campo
`omission_provenance` pertence ao payload v2. A implementação deve atualizar
explicitamente:

- `src/hermes_ops/skills/mission_models.py`;
- `src/hermes_ops/analysis/loader.py`;
- `src/hermes_ops/analysis/builder.py`;
- `src/hermes_ops/analysis/validator.py`;
- testes de serialização e compatibilidade.

Evidence Packs v1 permanecem carregáveis para leitura histórica, mas nunca
inferem redundância com `CAP_OMISSION`. Evidence Packs v2 exigem suporte
explícito em todos os consumidores autorizadores. Versões desconhecidas devem
ser rejeitadas fail-closed. A decisão de manter ou não `schema_version=1` para
o campo opcional foi encerrada: a semântica de redundância usa `schema_version=2`.

Consumidores devem preservar provenance e limitações ao construir pedidos de
análise. Um consumidor que não reconheça a nova provenance pode ignorar o
detalhe apenas para apresentação, mas deve permanecer fail-closed: ausência
ou provenance desconhecida nunca pode ser convertida em `sufficient`.

### 6.2 Consumidores

Consumidores que tratam `incompleteness_codes` e `limitations` como tuplas de
strings devem continuar funcionando com os novos valores:

```text
NECESSARY_EVIDENCE_OMITTED
REDUNDANT_EVIDENCE_OMITTED
```

Nenhum consumidor deve interpretar apenas a ausência de
`CRITICAL_EVIDENCE_OMITTED` como suficiência. Um pacote legado sem provenance
não contém prova de redundância e deve permanecer submetido à semântica
fail-closed vigente.
### 6.3 Escopo estrutural

A prova de redundância só pode comparar evidências dentro do mesmo
`structural_scope`. Uma região fora do escopo nunca pode servir como evidência
equivalente.

## 7. Critérios de aceitação

- **AC-01:** duplicata exata é agregada sem perder razões críticas.
- **AC-02:** comentário duplicado com excerpt e razões idênticos pode ser
  classificado como redundante.
- **AC-03:** docstring duplicada com equivalência comprovada pode ser
  classificada como redundante.
- **AC-04:** comentário com termo central exclusivo permanece necessário e
  bloqueia `sufficient`.
- **AC-05:** código ativo não crítico e exclusivo permanece necessário.
- **AC-06:** relacionamento sem região materializada permanece bloqueante.
- **AC-07:** símbolo crítico omitido permanece bloqueante.
- **AC-08:** teste crítico omitido permanece bloqueante.
- **AC-09:** cap por arquivo mantém `MAX_REGIONS_PER_FILE=12` e não permite
  falso `sufficient` por ausência de prova.
- **AC-10:** cap global mantém `MAX_REGIONS=300` e só libera omissões quando
  todas forem comprovadamente redundantes.
- **AC-11:** `UNCOVERED_CENTRAL_TERMS` continua bloqueante.
- **AC-12:** `--include-path` limita também a prova de equivalência.
- **AC-13:** mesma entrada produz mesma classificação, omissões e provenance.
- **AC-14:** Evidence Pack legado continua carregável.
- **AC-15:** `MAX_JSON_BYTES` continua fail-closed.
- **AC-16:** ausência de `critical_*` sem prova de equivalência nunca produz
  `REDUNDANT_EVIDENCE_OMITTED`.
- **AC-17:** provenance ausente, inválida ou truncada classifica a omissão como
  não comprovada e mantém `sufficient = false`.
- **AC-18:** Evidence Pack legado sem provenance nunca é interpretado como
  redundante automaticamente.
- **AC-19:** cap global com qualquer omissão não comprovada permanece
  `insufficient`, mesmo quando todas as regiões críticas foram selecionadas.
- **AC-20:** classificação de redundância e provenance são determinísticas e
  ordenadas por identidade da região.
- **AC-21:** nenhuma combinação de ausência de `CRITICAL_EVIDENCE_OMITTED`,
  `CAP_OMISSION` ou `REDUNDANT_EVIDENCE_OMITTED` pode produzir `sufficient`
  sem a prova individual completa de todas as omissões.
- **AC-22:** a semântica de redundância somente é válida em
  `schema_version=2` com `omission_provenance` presente e válida.
- **AC-23:** Evidence Pack v1 permanece carregável para leitura, mas nunca
  fornece prova de redundância para autorização.
- **AC-24:** schema version desconhecido é rejeitado fail-closed por loader e
  validator.
- **AC-25:** provenance ausente, incompleta ou truncada mantém a omissão
  bloqueante e nunca produz `sufficient`.
## 8. Testes RED necessários

Adicionar em `tests/test_mission_audit.py`:

1. comentário duplicado com cobertura equivalente;
2. docstring duplicada com cobertura equivalente;
3. comentário contendo termo central exclusivo;
4. código ativo exclusivo;
5. relacionamento sem região;
6. símbolo crítico omitido;
7. teste crítico omitido;
8. cap por arquivo com mistura de regiões críticas e redundantes;
9. cap global com mistura de regiões críticas e redundantes;
10. `--include-path` impedindo equivalência fora do escopo;
11. determinismo da classificação;
12. compatibilidade de Evidence Pack legado;
13. limite `MAX_JSON_BYTES`;
14. provenance ausente, inválida ou truncada;
15. cap global com omissão não comprovada;
16. consumer legado que ignora provenance sem produzir aprovação;
17. prevenção de falso `sufficient` quando só a ausência de critical é conhecida;
18. Evidence Pack v2 com provenance válida;
19. Evidence Pack v1 carregável sem prova de redundância;
20. schema version desconhecido rejeitado;
21. omission_provenance ausente, inválida ou truncada em v2.

Os testes devem demonstrar separadamente:

```text
redundant_evidence_omitted não bloqueante somente com prova
necessary_evidence_omitted bloqueante
critical_evidence_omitted bloqueante
```

## 9. Riscos

- Uma prova textual excessivamente permissiva pode classificar informação
  exclusiva como redundante.
- Um Evidence Pack pode crescer com provenance de omissões.
- Comparação de excerpts pode ser cara para arquivos grandes.
- Equivalência entre regiões de arquivos diferentes deve permanecer proibida na
  primeira implementação.
- Um erro de classificação pode produzir falso `sufficient`, por isso o
  default deve ser sempre necessário/bloqueante.

## 10. Questões contratuais resolvidas

- a semântica de redundância usa `schema_version=2`;
- `omission_provenance` é obrigatória em v2 e ausente em v1;
- equivalência textual inicial é limitada ao mesmo arquivo;
- imports e relacionamentos não são redundantes na primeira implementação;
- comentário explicativo é necessário salvo equivalência textual explícita;
- o limite de provenance é `MAX_REGIONS` e o limite de serialização é
  `MAX_JSON_BYTES`;
- qualquer falha de representação mantém a omissão bloqueante.

Questões de implementação restantes, como a forma concreta do dataclass
`OmissionRecord` e a atualização coordenada de loaders/consumidores, estão
tratadas no plano futuro e não alteram este contrato.

## 11. Plano futuro

1. Aprovar HERMES-0037.
2. Adicionar testes RED/guards, incluindo v1/v2, provenance e consumers.
3. Implementar `OmissionRecord` e `schema_version=2`.
4. Atualizar `mission_models.py`, loader, builder, validator e serialização.
5. Implementar prova conservadora de redundância.
6. Executar testes focados e regressões HERMES-0036.
7. Executar suíte Hermes Ops.
8. Validar determinismo, tamanho do pack e ausência de falso `sufficient`.
9. Somente depois repetir auditorias formais autorizadas.

## 12. Estado

Implementado na branch privada de origem e integrado nesta branch de release.
A validação de publicação deve repetir testes, compileall e empacotamento na
árvore integrada antes de qualquer tag ou release pública.
