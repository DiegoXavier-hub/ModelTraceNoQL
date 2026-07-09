# Auditoria metodológica da Fase 2

> **Data**: 2026-04-30
> **Escopo**: revisão crítica completa da Fase 2 (Data Understanding / EDA)
> contra o plano em `MEMORY.md §8`, contra os princípios D000–D017, e
> contra padrões de rigor estatístico para um TCC ABNT.
> **Princípio governante**: ROBUSTEZ > custo computacional.
>
> Esta auditoria foi solicitada pelo autor após a Fase 2 ter sido marcada
> como "fechada". O objetivo é falsificar conclusões antes de avançar para
> a Fase 3. Achados aqui resultaram em correções de código, atualização de
> hipóteses (H001, H010, H013, H015), refinamento de duas decisões (D016,
> D018) e uma nova decisão (D022).

---

## 1. Sumário executivo

A Fase 2 foi auditada em **13 frentes** (5 verificações de bugs/integridade
+ 8 verificações de omissões e validações populacionais). Resultados:

- **Nenhuma conclusão da Fase 2 foi invalidada**.
- **2 bugs latentes foram encontrados e corrigidos** (não estavam ativos
  por coincidência da implementação do duckdb e por uma propriedade
  emergente do dataset).
- **Uma conclusão foi refinada com magnitude maior do que a reportada**:
  H010 (drift) era −49%, é na verdade **−72,5%** quando normalizado por
  volume de telemetria.
- **Quatro análises críticas que estavam faltando** foram executadas:
  NIVEL CMA, taxa H001 por mês, distribuição de IDs por alarme, testes
  chi-square formais para H003.
- **Um falso alarme foi corrigido**: gaps de 95-112 dias entre apontamentos
  e telemetria que apareceram em amostra de 2.000 ciclos não se
  confirmaram em população total (apenas 1 TAG com gap > 7 dias).
- **3 problemas de qualidade técnica** foram corrigidos: encoding cp1252
  dos JSONs, ausência de kernelspec no notebook, SQL com ANY_VALUE não
  determinístico.

A Fase 2 está **mais sólida** após a auditoria. Nenhum impedimento para
abrir a Fase 3.

---

## 2. Metodologia da auditoria

A auditoria seguiu cinco trilhas:

1. **Verificação de bugs latentes**: revisar todo o SQL gerado pelos
   runners contra o que o padrão SQL garante (sem depender de detalhes de
   implementação).
2. **Validação de magnitude**: re-executar análises substantivas com
   normalizações alternativas e na população total quando fizemos amostra.
3. **Cobertura do plano**: comparar o que foi entregue contra a lista
   detalhada do plano em `MEMORY.md §8` (sub-fases 2A-2F).
4. **Teste estatístico formal**: traduzir hipóteses descritivas em testes
   com p-value (chi-square, Cramer's V).
5. **Qualidade técnica**: encoding, metadata, reprodutibilidade.

Ferramenta: `notebooks/_audit_fase2.py` (273 linhas) que produz
`reports/eda_results/audit_fase2.json`.

---

## 3. Achados — bugs latentes (2)

### Achado A1 — `ANY_VALUE(Alarme)` em incidentes (Fase 2C)

**Onde**: `notebooks/_eda_runner_2c.py`, agregação de incidentes pelo
`incident_id`.

**O bug**: a SQL fazia

```sql
SELECT TAG, ..., incident_id,
       ANY_VALUE(Alarme) AS alarme_inicio,
       ANY_VALUE(Criticidade) AS crit_inicio
FROM grouped GROUP BY ALL
```

`ANY_VALUE` retorna *qualquer* valor da partição — no padrão SQL não há
garantia de qual. A intenção era pegar o **alarme do evento de início** do
incidente.

**Verificação**: para os 2.171 incidentes com >1 evento (43,2% do total),
contei quantos casos `ANY_VALUE != alarme_correto_start`. Resultado: **0
casos**. O duckdb retorna o primeiro evento por coincidência da
implementação atual (preserva ordem de inserção em pipelines com window
functions upstream).

**Status**: bug **latente** mas não ativo no dataset/versão atual. Ainda
assim:
- Substituí por `MIN(CASE WHEN is_incident_start=1 THEN col END)` —
  semanticamente correto e portável.
- Conclusões da Fase 2C (top 15 alarmes que iniciam incidentes; 52%
  Não Crítico) **não mudam**.

### Achado A2 — Denominador errado em `share_moda` (D016, Fase 2E)

**Onde**: `notebooks/_eda_runner_2e.py`, teste de inferência do operador.

**O bug**: a SQL calculava `share = mode_count / sum_of_mode_counts`, mas
`sum_of_mode_counts` era `COUNT(*) OVER ()` filtrado por
`Nome_Operador_Anon IS NOT NULL`. Ou seja, o denominador era o total de
eventos com operador, não o total do ciclo. Pela definição em D016 ("share
≥ 80% **dos eventos do ciclo**"), o denominador correto deveria incluir
eventos com operador NULL.

**Verificação**: re-executei com denominador correto. Resultado idêntico:
99,67% ≥ 80%. Por quê? Descoberta: **`Nome_Operador_Anon` é universalmente
preenchido nos eventos que existem no parquet** — não há eventos com
operador NULL nesse dataset. Assim, o conjunto `eventos com operador` é
igual ao `total do ciclo` quando há telemetria.

**Status**: bug **latente** mas não ativo.
- Corrigi o SQL.
- D016 não muda (D021 ratifica 80%).
- **Nova hipótese H017**: operador é universalmente reportado quando há
  telemetria — útil para a Fase 3, simplifica feature engineering.

---

## 4. Achados — refinamentos de magnitude (3)

### Achado B1 — H010 era −49%, é **−72,5%**

**Original**: reportei "redução de 49% entre o pico de fev e o vale de mai"
usando contagens absolutas mensais.

**Problema**: a telemetria cresce 45% jan→jun (5,4M → 7,9M eventos).
Usar contagem bruta ignora esse crescimento e **subestima** a queda
relativa de risco.

**Corrigido**: normalizar por incidentes por milhão de eventos:

| Mês | n_evt | n_inc | inc/M evt |
|---|---:|---:|---:|
| 2025-01 | 5.400.002 | 975 | 180,6 |
| 2025-02 | 5.709.935 | 1.303 | **228,2** ← peak |
| 2025-03 | 5.688.538 | 1.154 | 202,9 |
| 2025-04 | 6.475.045 | 616 | 95,1 |
| 2025-05 | 6.036.291 | 484 | 80,2 |
| 2025-06 | 7.854.243 | 493 | **62,8** ← vale |

**Redução real peak → vale: −72,5%** (não −49%).

**Implicação**: o concept drift entre 1º e 2º trimestre é ~1,5× mais
severo do que reportei. O TCC vai usar este número.

### Achado B2 — H001 esconde drift severo entre meses

**Original**: H001 confirmada com taxa global de 0,054%.

**Faltava**: taxa por mês.

| Mês | Eventos | Don't Go | Taxa |
|---|---:|---:|---:|
| jan | 5.400.002 | 2.581 | **0,048%** |
| fev | 5.709.935 | 4.493 | **0,079%** ← max |
| mar | 5.688.538 | 4.223 | 0,074% |
| abr | 6.475.045 | 2.159 | 0,033% |
| mai | 6.036.291 | 1.280 | **0,021%** ← min |
| jun | 7.854.243 | 5.226 | 0,067% |

**Razão max/min = 3,71×.** Todos os meses < 0,1% (H001 confirmada),
**mas folds do walk-forward terão prevalências muito diferentes**.
Justifica D012 (Lift = AUC-PR / prevalência) como métrica primária — sem
normalização, comparar AUC-PR entre folds é enganoso.

> **Nota interessante**: jun saltou para 0,067% após o vale de 0,021% em
> mai — possivelmente sazonalidade operacional (chuvas em Itabira em jun?
> Mudanças de programação?). Justifica investigação adicional na Fase 3.

### Achado B3 — H015 era "~2× IDs por nome", é **distribuição com cauda longa**

**Original**: reportei `n_alarme=712, n_alarme_id=1.324` e concluí "~2×
IDs por nome".

**Problema**: o ratio uniforme implícito é incorreto.

**Real**:
- 80,2% (571 alarmes) com **1 único Id_Alarme**
- 19,8% (141 alarmes) com >1 ID
- Cauda longa: alarmes com **49 e 50 IDs distintos**

**Implicação**: o problema de "mesmo nome, IDs diferentes" só afeta 20%
dos alarmes (concentrados nos 141 mais "compartilhados entre OEMs").
Para 80% dos alarmes, a chave de junção `Alarme` ou `Id_Alarme` é
equivalente. Os 141 com cauda longa são exatamente os candidatos a
"famílias funcionais" de H009.

---

## 5. Achados — análises faltantes (4)

### Achado C1 — NIVEL CMA não foi reportado

**Plano (MEMORY.md §8)** especificava: "distribuição por TIPO/NIVEL/Tag/
Frota/mês". Eu reportei TIPO (Caminhão/Escavadeira), Tag, Frota, mês — mas
**não NIVEL** (Muito Alto / Alto, do catálogo CMA).

**Confusão semântica**: na Fase 2C eu reportei `Criticidade` (Crítico /
Não Crítico / Informacional, da telemetria) e chamei isso de "criticidade
do alarme inicial". Não é a mesma coisa que NIVEL CMA.

**Auditoria**: JOIN dos 5.025 incidentes com `cma[EVENTO,NIVEL]`:

| NIVEL CMA | n incidentes | % |
|---|---:|---:|
| Muito Alto | 4.059 | 80,8% |
| Alto | 966 | 19,2% |

Cross com Criticidade:
- Regras "Muito Alto" são iniciadas por: 2.209 Critico + 1.850 Não Crítico
- Regras "Alto" são iniciadas por: 225 Critico + **741 Não Crítico**

**Confirma o mecanismo de H011**: a regra CMA "Muito Alto" pode ser
disparada por acúmulo de alarmes Não Críticos — não exige um Crítico
inicial. Especialmente para regras "Alto" (77% iniciadas por Não
Crítico).

LeTourneau só tem incidentes Muito Alto (32 de 32) — reforça H016.

### Achado C2 — Chi-square formal de H003 (faltava)

**H003** declara "diferença significativa" mas eu só reportei razões
descritivas.

**Auditoria**:
- Turno × Is_Dont_Go: chi² = 99,7, **p = 1,7 × 10⁻²³**, dof=1
- DOW × Is_Dont_Go: chi² = 743,3, **p = 2,7 × 10⁻¹⁵⁷**, dof=6

Ambos rejeitam independência com força extrema. **H003 confirmada
formalmente**, não só descritivamente.

### Achado C3 — Cramer's V categóricas vs Is_Dont_Go (faltava)

**Auditoria**: força de associação entre cada categórica e o alvo:

| Variável | Cramer's V | Categorias |
|---|---:|---:|
| Criticidade | **0,271** | 5 |
| Classe | 0,190 | 3 |
| TAG | 0,136 | 35 |
| Tag_Frota | 0,077 | 5 |
| Tipo | 0,074 | 2 |

**Criticidade é o categórico mais informativo, mas longe de ser smoking
gun**. V=0,27 é "moderado". Confirma que sinal preditivo virá de
combinações temporais, não de um único campo.

### Achado C4 — H013 só estava em amostra; falta população

**Original**: "19,1% dos ciclos `Operando` sem telemetria" baseado em 471
ciclos amostrais.

**Auditoria populacional** (182.527 ciclos `Operando` totais):
- 32.154 com 0 eventos = **17,6% real**
- CI 95% da amostra (n=471, p=19,1%): [15,6%, 22,6%] — **capturou** 17,6%

**H013 confirmada na população** com magnitude ligeiramente menor que a
amostra (viés aleatório).

---

## 6. Achados — falsos alarmes corrigidos (1)

### Achado D1 — Gaps de 95-112 dias entre apontamentos e telemetria

**Original**: reportei que CA65916 e CA65793 tinham gaps massivos entre o
primeiro apontamento e o primeiro evento de telemetria, sugerindo
problema de timezone ou pipeline.

**Auditoria populacional**: dos 35 TAGs, **só CA65916 tem gap > 7 dias**
(gap = −24 dias, telemetria começa antes dos apontamentos).

**Conclusão**: o achado original veio de viés amostral — a amostra de
2.000 ciclos do `_eda_runner_2e.py` não pegou apontamentos antigos dos
TAGs CA65916 e CA65793, fazendo `MIN(primeiro_apt)` da amostra refletir
ciclos tardios. Em população, os apontamentos antigos estão lá.

**Lição**: validações de pareamento entre fontes devem rodar sobre
população total, não amostra.

---

## 7. Achados — qualidade técnica (4)

### Achado E1 — Encoding cp1252 nos JSONs

3 dos 5 JSONs (`fase2c_results.json`, `fase2d_results.json`,
`fase2e_results.json`) foram escritos sem `encoding='utf-8'` explícito —
no Windows, isso usa cp1252. Strings como "Não Crítico" geraram bytes
inválidos para UTF-8.

**Fix**: adicionei `encoding='utf-8'` em todos os 4 runners + builder.
Re-executei. Todos UTF-8 válido agora.

### Achado E2 — Notebook sem `kernelspec`

Notebook gerado sem metadata de kernel. Ao abrir no Jupyter, o usuário
era forçado a selecionar kernel manualmente.

**Fix**: builder agora adiciona `kernelspec` (python3) e `language_info`
(python 3.13.7).

### Achado E3 — Notebook nunca foi executado

8 cells de código sem `outputs`. Reprodutibilidade depende de o usuário
rodar tudo manualmente.

**Status**: encaminhado mas opcional — figuras já existem em
`reports/figures/`, então o notebook funciona como visualização (load via
`Image()` puxa do disco).

### Achado E4 — `n_alarme` discrepância entre Fase 2B (712) e Fase 2D (710)

**Causa**: 2D filtra `WHERE Alarme IS NOT NULL` antes de `set()`. Nos
712 da 2B, 2 são strings com whitespace marginal que `.str.strip()`
colapsou em outros nomes na 2D.

**Status**: cosmético, não material. Documentado.

---

## 8. Propriedades emergentes do dataset descobertas

A auditoria expôs três propriedades não-triviais:

1. **`Nome_Operador_Anon` é universalmente preenchido** quando há
   telemetria (zero eventos com NULL nesse campo). Significa que "ciclo
   sem operador" e "ciclo sem telemetria" são equivalentes — não
   independentes.
2. **Os 167 Don't Gos com `Classe=NULL` são exclusivamente LeTourneau**.
   Todas as 4 frotas 793-D usam `Activate` para 100% dos seus Don't Gos.
   Reforça H016 (modelo separado).
3. **`Valor` tem zero falhas de conversão** (vírgula→ponto + try_cast em
   37M linhas). O pipeline da Vale exporta `Valor` apenas como inteiro,
   decimal com vírgula, ou literal `NULL`. Sem casos exóticos.

---

## 9. Mudanças aplicadas

### Código

- [`notebooks/_eda_runner_2c.py`](../notebooks/_eda_runner_2c.py): SQL `ANY_VALUE` substituído por `MIN(CASE)`.
- [`notebooks/_eda_runner_2e.py`](../notebooks/_eda_runner_2e.py): denominador `share_moda` corrigido para total do ciclo.
- Todos os 4 `_eda_runner*.py`: `encoding='utf-8'` explícito nos `write_text`.
- [`notebooks/_build_notebook.py`](../notebooks/_build_notebook.py): kernelspec + language_info adicionados.

### Documentação

- `docs/audit_fase2.md` (este arquivo).
- `docs/hypotheses.md` (atualizações de H001, H010, H013, H015 + nova H017).
- `docs/decisions.md` (nova D022 sobre LeTourneau Classe NULL; revisão de D016 e D018).
- `MEMORY.md` (checkpoint da auditoria adicionado).
- Notebook regerado com seção 2I "Auditoria pós-EDA".

### Artefatos novos

- `reports/eda_results/audit_fase2.json` (resultados quantitativos da auditoria).

---

## 10. Pendências aceitas (não fixadas nesta auditoria)

1. **Notebook não auto-executado**: rodar `jupyter nbconvert --execute` é
   opcional. Figuras estão em disco e se carregam via `Image()`.
2. **PYTHONHASHSEED warn na seeds.py**: aviso esperado; setar no env do
   sistema antes de iniciar Python é responsabilidade do operador.
3. **Lint de markdown** nos arquivos `MEMORY.md`, `decisions.md`,
   `hypotheses.md` (warnings MD022, MD031, MD040, MD060): pré-existentes,
   não bloqueantes para banca; cosmético.
4. **`pmdarima`**: não instalado (substituído por `prophet`). D017 prevê
   `Cox PH + Weibull AFT` (lifelines) como rota principal; ARIMA não é
   essencial.

---

## 11. Veredito final

A Fase 2 estava **boa em conteúdo, mas tinha 2 bugs latentes, 4 análises
faltantes, 1 falso alarme, e 4 problemas de qualidade técnica**. Após a
auditoria:

- **Conclusões substantivas mantidas**, com **uma magnitude refinada para
  pior** (H010: −49% → −72,5%) e **três análises adicionadas** que
  reforçam a tese.
- **Bugs latentes neutralizados** mesmo sem terem afetado o dataset.
- **Reprodutibilidade restaurada** (UTF-8, kernelspec, SQL portátil).
- **Uma nova hipótese (H017)** sobre propriedade emergente do dataset.
- **Uma nova decisão (D022)** registrando LeTourneau Classe NULL.

A Fase 2 está **pronta para virar Capítulo 4 (Resultados parciais —
Compreensão dos Dados)** do TCC, e a Fase 3 pode abrir sem revisitar EDA.
