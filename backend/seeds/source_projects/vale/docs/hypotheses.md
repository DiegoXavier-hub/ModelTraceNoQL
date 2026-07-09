# docs/hypotheses.md — Hipóteses levantadas durante o projeto

> Toda observação interessante na EDA vira uma **hipótese testável**. Mesmo as não confirmadas servem para interpretar o modelo depois.
>
> Formato por entrada:
> - **ID** (H001, H002, …)
> - **Hipótese** (frase declarativa, falsificável)
> - **Origem** (qual fonte/análise levantou a suspeita)
> - **Como testar** (operacionalização concreta)
> - **Status**: aberta · em_teste · confirmada · refutada · inconclusiva
> - **Resultado** (preencher após teste, com referência a notebook/seção)

---

## Hipóteses iniciais (levantadas na Fase 1 — Business Understanding) — atualizadas na Fase 2

### H001 — Forte desbalanceamento do alvo

- **Hipótese**: A taxa empírica de eventos com `Is_Dont_Go=1` é **menor que 0,1%** do total de eventos de telemetria.
- **Origem**: o arquivo `desenvolver_dontgo.xlsx` mostra apenas **1 Don't Go em 147 eventos** (~0,68%) — e essa é uma janela enriquecida, focada num caso real de Don't Go. Em telemetria normal a taxa deve ser muito menor.
- **Como testar**: contar `Is_Dont_Go.sum() / len(df)` no parquet completo de telemetria.
- **Status**: ✅ **CONFIRMADA** + **refinada na auditoria**
- **Resultado**: Fase 2C (notebook `02_data_understanding_eda.ipynb`):
  - Eventos totais: 37.164.054
  - Eventos com Is_Dont_Go=1: 19.962
  - **Taxa global: 0,054%** (5,4× abaixo do limiar de 0,1%)
  - Justifica D002 (AUC-PR primária) e D015 (sem SMOTE).
- **Refinamento da auditoria** (2026-04-30, `docs/audit_fase2.md` §4 B2): a taxa global esconde drift severo entre meses:
  - jan 0,048% · fev **0,079%** ← max · mar 0,074% · abr 0,033% · mai **0,021%** ← min · jun 0,067%
  - **Razão max/min = 3,71×** entre folds.
  - Todos os meses < 0,1% (H001 mantém-se confirmada), **mas walk-forward terá prevalências muito diferentes em cada fold** — reforça D012 (Lift = AUC-PR / prevalência) como métrica primária.

### H002 — Padrão sequencial precursor

- **Hipótese**: Pelo menos **70% dos Don't Go** são precedidos, na **última hora**, por **3 ou mais alarmes** do mesmo evento ou da mesma família funcional (motor / transmissão / hidráulico / arrefecimento).
- **Origem**: o exemplo `desenvolver_dontgo.xlsx` mostra **2 disparos de `Engine Coolant Level - Active` nos 3 minutos finais e 5 disparos nos 6 minutos finais** antes do Don't Go.
- **Como testar**: para cada incidente Don't Go, olhar a janela [t−1h, t−1s] do mesmo equipamento e contar alarmes com `Id_Criticidade ≤ 2` ou da mesma "família" (mapear textualmente).
- **Status**: 🔄 **OPERACIONALIZADA na Fase 3C** — `n_evt_1h`, `n_crit_1h`, `n_naocrit_1h`, `n_fam_<X>_1h` por janela. Teste estatístico definitivo fica para a Fase 4 (Modeling).
- **Resultado parcial**: dataset de 538.848 windows materializado em `data/processed/features_*.parquet` permite testar via odds-ratio/lift entre `y_dontgo_1h=1` e contagens de alarme por família. Fase 4 reportará.

### H003 — Concentração temporal (turnos / dias)

- **Hipótese**: A **taxa de Don't Go por hora-equipamento** difere significativamente entre turnos noturno (18:00-06:00) e diurno (06:00-18:00). Subhipótese: noturno tem taxa maior (fadiga acumulada, menor visibilidade da operação).
- **Origem**: literatura de operação 24/7; padrões de fadiga humana e térmica do equipamento.
- **Como testar**: agregar `Is_Dont_Go` por turno (definido por `Inicio_Turno`/`Fim_Turno`) e por hora do dia; teste qui-quadrado de proporção.
- **Status**: ✅ **CONFIRMADA — agora com teste estatístico formal (auditoria 2026-04-30)**
- **Resultado**: Fase 2D + auditoria (`docs/audit_fase2.md` §5 C2):
  - Turno noturno: 0,058% vs diurno 0,050% → razão **1,15×** (efeito real porém modesto).
  - Madrugada (5h) tem peak: 0,071%; mínimo às 16h (0,044%).
  - **Dia da semana é mais informativo que turno**: Segunda 0,072% vs Domingo 0,041% → razão **1,77×**.
  - **Chi-square formal (auditoria)**:
    - Turno × Is_Dont_Go: χ² = 99,7, **p = 1,7 × 10⁻²³**, dof = 1 — rejeita independência.
    - DOW × Is_Dont_Go: χ² = 743,3, **p = 2,7 × 10⁻¹⁵⁷**, dof = 6 — rejeita independência com força ainda maior.
  - **Cramer's V** (auditoria): Tipo 0,074 / Tag_Frota 0,077 / TAG 0,136 / Classe 0,190 / **Criticidade 0,271** (mais informativo).
  - O sinal temporal linear é fraco (corr ≈ 0 entre Is_Dont_Go e hora/DOW/mês), mas há diferenças categóricas mensuráveis. Feature engineering precisa capturar como **categórico** (DOW × turno), não como contínuo.

### H004 — Heterogeneidade entre frotas

- **Hipótese**: Determinadas frotas (modelos mais antigos ou tipos específicos — escavadeiras vs. caminhões) concentram **desproporcionalmente** os Don't Go (≥ 2× a taxa média da operação).
- **Origem**: heurística de engenharia: modelos antigos e equipamentos auxiliares de baixa redundância tendem a ter mais incidentes.
- **Como testar**: taxa de Don't Go por `Tag_Frota` e por `Tipo`; ranqueamento + bootstrap CI da taxa.
- **Status**: ✅ **CONFIRMADA com força**
- **Resultado**: Fase 2C/2D:
  - **Sob 2 lentes**:
    - **Por # incidentes absolutos**: 793-D 5S concentra **56%** dos 5.025 incidentes (2.821); 793-D 4S 24%; LeTourneau L 1850 apenas 0,6%.
    - **Por taxa por evento**: 793-D 4S/3S têm 0,87% e 0,82%; 793-D 5S 0,50%; 793-D 2S 0,45%; **LeTourneau L 1850 0,0005% — 1700× menor**!
  - Caminhões: 0,60% taxa por evento; Escavadeira (LeTourneau): 0,0005% (taxa 1200× menor).
  - Implica considerar **modelos separados por frota** na Fase 3 (vide H016).

### H005 — Efeito do operador

- **Hipótese**: O **operador anonimizado** tem efeito mensurável: pelo menos um decil de operadores tem taxa de Don't Go ≥ 1,5× a mediana, controlando por equipamento.
- **Origem**: literatura de mineração mostra variabilidade entre operadores.
- **Como testar**: regressão logística com efeito fixo de equipamento + termo de operador; análise de variância da taxa empírica.
- **Status**: ⏸️ **TESTÁVEL** — D016 viabilizou inferência de operador.
- **Resultado**: Fase 2E:
  - 61,5% dos ciclos têm operador inferível (telemetria reporta operador no intervalo).
  - **99,67% desses ciclos têm share da moda ≥ 80%** (D016 valida com folga).
  - Os 38,5% sem operador inferível ficarão com `operador=NULL` nas análises.
  - Teste estatístico em si fica para a Fase 4 (modelagem) sobre os 61,5% testáveis.

### H006 — Dependência de localidade

- **Hipótese**: A taxa de Don't Go varia entre localidades.
- **Origem**: variação natural entre minas (relevo, clima, manutenção local).
- **Como testar**: taxa por `Localidade` (após confirmar pluralidade na Fase 2).
- **Status**: 🛑 **INCONCLUSIVA POR CONSTRUÇÃO**
- **Resultado**: Fase 2E (T3.2 confirmada):
  - **Itabira é a única localidade nos 6 meses** (verificação formal sobre 37M eventos, ratificada mês a mês).
  - **Plano de contingência ativado**: H006 vai para "Trabalhos Futuros" do TCC sem teste empírico nesta entrega.

### H007 — Janela ótima de predição

- **Hipótese**: A janela de **4 horas** captura ≥ 80% dos Don't Go com sinal preditivo da última hora; janelas menores (1–2 h) tornam o problema "trivial demais" e janelas maiores (> 8 h) tornam o sinal **muito ruidoso**.
- **Origem**: D001 (substituída por D001 v2: múltiplos horizontes paralelos).
- **Como testar**: treinar o mesmo modelo com janelas de {1, 2, 4, 6, 8, 12} horas e comparar AUC-PR; analisar curvas de degradação.
- **Status**: ⏸️ **aberta** (será testada na Fase 4 — Modelagem).
- **Resultado**: — (Fase 4)

### H008 — Coerência da flag `Is_Dont_Go` com o catálogo CMA

- **Hipótese**: ≥ 95% dos eventos com `Is_Dont_Go=1` correspondem a um evento listado em alguma regra `(TIPO, EVENTO, NIVEL ∈ {Alto, Muito Alto})` do catálogo CMA.
- **Origem**: D006 — adotamos a flag como ground truth, mas precisamos validar.
- **Como testar**: amostragem estratificada de positivos; cruzar `Alarme` da telemetria com `EVENTO` do CMA; reportar taxa de match.
- **Status**: ✅ **CONFIRMADA com folga**
- **Resultado**: Fase 2D (cobertura CMA × inícios de incidente):
  - 19 alarmes distintos iniciam os 5.025 incidentes.
  - **Todos os 19 (100%) estão no catálogo CMA** (vs hipótese de ≥ 95%).
  - Reforça D006: usar a flag como ground truth é seguro e economicamente justo.

### H009 — Famílias funcionais como features fortes

- **Hipótese**: Agrupar os ~136 eventos OEM em **5–8 famílias funcionais** (motor, transmissão, hidráulico, arrefecimento, exaustão, freio, elétrico, outros) gera features de contagem por família que **isoladamente** atingem AUC-PR > 0,5.
- **Origem**: o catálogo CMA mostra que eventos de Muito Alto se aglomeram em poucos sistemas funcionais.
- **Como testar**: criar baseline com features de contagem por família nas últimas N horas; medir performance.
- **Status**: 🔄 **OPERACIONALIZADA na Fase 3C (D028)** — taxonomia formalizada em `src/features/families.py` com **13 famílias + Other** (vs 5-8 da hipótese original; refinada com exposição populacional).
- **Resultado parcial (Fase 3C)**: cobertura 99,64% dos eventos (Other = 0,36%, 134k eventos). 3 horizontes × 14 famílias = **42 features `n_fam_<X>_<W>h`** no dataset. AUC-PR isolada por família vai ser medida na Fase 4.
- **Nota de refinamento**: a inspeção populacional revelou famílias dominadas por **estado operacional** (`Operational_State` = 71% dos eventos, sub-família CAT+LeTourneau) que não tinha sido prevista na hipótese original. As **famílias preditivas** prováveis são: Engine_Coolant, Transmission, Brakes, Steering, Hydraulic, Exhaust_Turbo, Engine_Oil — todas alinhadas com o catálogo CMA.

---

## Hipóteses novas derivadas da EDA — Fase 2 (H010–H016)

### H010 — Drift temporal de prevalência

- **Hipótese (revisada na auditoria)**: A prevalência de incidentes Don't Go por unidade de telemetria cai significativamente entre o primeiro e o segundo trimestre. **Refinada**: a redução real é maior do que a contagem bruta sugere, porque o volume de telemetria cresce ~45% no período.
- **Origem**: Fase 2C — distribuição mensal de incidentes (contagens brutas).
- **Como testar**:
  1. **Normalizar por volume mensal de telemetria** — `incidentes / 1.000.000 eventos`.
  2. Calcular prevalência por fold do walk-forward (D011) e reportar como métrica auxiliar.
  3. Aplicar teste de drift (PSI, KS) entre janelas mensais.
  4. Investigar causas plausíveis: (a) ações operacionais reativas pós-jan/fev, (b) atualização das regras CMA, (c) sazonalidade chuvosa em Itabira.
- **Status**: ✅ **CONFIRMADA com magnitude maior (auditoria 2026-04-30)**
- **Resultado**: `docs/audit_fase2.md` §4 B1:

| Mês | n_evt | n_inc | inc/M evt |
|---|---:|---:|---:|
| jan | 5.400.002 | 975 | 180,6 |
| fev | 5.709.935 | 1.303 | **228,2** ← peak |
| mar | 5.688.538 | 1.154 | 202,9 |
| abr | 6.475.045 | 616 | 95,1 |
| mai | 6.036.291 | 484 | 80,2 |
| jun | 7.854.243 | 493 | **62,8** ← vale |

  - **Redução real peak (fev) → vale (jun): −72,5%** (não −49% como reportado originalmente).
  - O número que vai para o TCC é **−72,5%**.
- **Implicação prática**: o teste em junho (modelo "para deploy") sofre de **covariate shift** — pode pontuar pior em métricas absolutas que folds anteriores sem que o modelo esteja "ruim", apenas porque a distribuição mudou. **Lift = AUC-PR / prevalência** (D012) é a métrica que normaliza este efeito.

### H011 — Don't Go nasce por acumulação, não por severidade

- **Hipótese**: A maioria dos incidentes (≥ 50%) começa com alarme `Não Crítico`, não com alarme `Crítico` isolado. O Don't Go é um evento **emergente** de padrões de repetição.
- **Origem**: Fase 2C — distribuição de criticidade do alarme inicial dos 5.025 incidentes:
  - Crítico: 2.434 (48%)
  - Não Crítico: 2.591 (52%)
- **Como testar**:
  1. Calcular curva de probabilidade de Don't Go condicional ao número de alarmes Não Críticos do mesmo evento na última hora.
  2. Comparar AUC-PR de modelo com features de "contagem de não-críticos por evento" vs sem.
- **Status**: 🔄 **OPERACIONALIZADA na Fase 3C** — features `n_naocrit_<W>h` para W ∈ {1h, 4h, 12h} no dataset. Auditoria 3D ratificou o mecanismo: regras CMA "Alto" são iniciadas em 77% por alarmes Não Críticos.
- **Implicação aplicada**: features `n_crit_<W>h` (n=3) e `n_naocrit_<W>h` (n=3) no dataset permitem o teste estatístico definitivo na Fase 4.

### H012 — Don't Go ocorre exclusivamente em Classe=Activate

- **Hipótese**: 100% dos eventos com `Is_Dont_Go=1` têm `Classe='Activate'`. Eventos `Inactive` ou `NULL` nunca disparam Don't Go.
- **Origem**: Fase 2D:
  - Activate: 19.795 / 19.962 = **99,16%** dos Don't Gos (com 167 vindo de Classe=NULL — todos LeTourneau)
  - Inactive: **zero** dos 525.236 eventos
  - NULL: 167 (todos LeTourneau, com Classe ausente)
- **Como testar**: já testada — quase 100% confirmada.
- **Status**: ✅ **CONFIRMADA** (com nuance: 0,84% vêm de NULL na LeTourneau).
- **Implicação prática**: eventos `Inactive` podem ser excluídos do training set (~525k linhas). Eventos `NULL` precisam ser preservados (caso LeTourneau).

### H013 — Inconsistência "Operando + 0 eventos de telemetria"

- **Hipótese**: Aproximadamente 19% dos ciclos `Operando` no apontamento não têm nenhum evento de telemetria correspondente (mesmo `Tag`, mesmo intervalo `[Inicio, Fim]`).
- **Origem**: Fase 2E (pareamento amostra 1.002 ciclos):
  - Operando com 0 eventos: 19,1%
  - Hibernando: 99,3% (esperado)
  - Manutenção: 60,9% (esperado)
  - Parado: 35,6% (parcialmente esperado)
- **Como testar**: replicar pareamento na população completa estratificando por mês/frota; investigar correlação com horário (ex: telemetria offline em determinados turnos).
- **Status**: ✅ **CONFIRMADA na população total (auditoria 2026-04-30)**
- **Resultado**: `docs/audit_fase2.md` §5 C4
  - **População total: 182.527 ciclos `Operando`**
  - 32.154 com 0 eventos = **17,6%** (CI 95% da amostra: [15,6%, 22,6%] — capturou)
  - Mediana de eventos por ciclo: 11; média 187 (cauda longa).
- **Implicação**: marcar com flag `tem_telemetria=0` em vez de excluir. **Decisão D020 a aplicar** (já registrada).

### H014 — Alarmes órfãos do catálogo O&M

- **Hipótese**: Aproximadamente 25% dos nomes de alarme distintos na telemetria não estão no catálogo geral `Eventos O&M`.
- **Origem**: Fase 2D:
  - 710 alarmes distintos na telemetria
  - 533 (75,1%) com match em O&M
  - **177 (24,9%) órfãos**
- **Como testar**: cruzar os 177 órfãos com `Tag_Frota` e `Tipo` para descobrir se são predominantemente da LeTourneau ou se estão espalhados por todas as frotas.
- **Status**: 🔄 **PARCIALMENTE OPERACIONALIZADA via D027** — D027 dedica PA-3 (anomalia não supervisionada) à LeTourneau. A taxonomia D028 (`families.py`) cobre os 712 alarmes em 13 famílias + Other. **Cruzamento órfão × OEM fica como entregável da PA-3 na Fase 4**, onde o universo dos 177 órfãos será o input natural do Isolation Forest.
- **Implicação aplicada**: as features `n_fam_other_<W>h` no dataset 3C agregam exatamente os alarmes não-classificáveis pela taxonomia funcional — proxy útil para "modo de falha não-canônico".

### H015 — Múltiplos `Id_Alarme` para o mesmo nome textual

- **Hipótese (refinada na auditoria)**: A relação `Alarme → Id_Alarme` não é uniforme: a maioria dos nomes tem 1 ID, mas uma cauda longa de alarmes ("compartilhados entre OEMs") tem múltiplos IDs.
- **Origem**: Fase 2B — `n_alarme=712` vs `n_alarme_id=1324`. A simplificação "~2× IDs por nome" era enganosa.
- **Como testar**: `SELECT n_ids, COUNT(*) FROM (SELECT Alarme, COUNT(DISTINCT Id_Alarme) AS n_ids FROM tel GROUP BY Alarme) GROUP BY n_ids`.
- **Status**: ✅ **CONFIRMADA com perfil real (auditoria 2026-04-30)**
- **Resultado**: `docs/audit_fase2.md` §4 B3
  - **80,2% (571 alarmes)** têm exatamente **1** `Id_Alarme`.
  - 19,8% (141 alarmes) têm > 1 ID.
  - **Cauda longa**: alarmes individuais com 25, 27, 30, 49 e 50 IDs distintos.
- **Implicação**: chave de junção para o catálogo CMA e O&M deve ser **`Alarme` (texto)**, não `Id_Alarme` — confirma o design original. Os 141 alarmes "compartilhados" são exatamente os candidatos a "famílias funcionais" de H009.

### H016 — LeTourneau requer modelo separado

- **Hipótese**: A LeTourneau L 1850 (escavadeira) tem padrão de telemetria tão diferente das Caterpillar 793-D (caminhões) que justifica modelo separado, não apenas feature de frota como variável dummy.
- **Origem**: Fase 2D:
  - LeTourneau: 33,9 M eventos / 167 Don't Gos / 5 equipamentos / **0,0005%** taxa por evento
  - 793-D 4S: 0,85 M eventos / 7.405 Don't Gos / 9 equipamentos / **0,87%** taxa por evento
  - Razão de prevalência: **~1700×**.
- **Como testar**: na Fase 4, treinar três configurações: (a) modelo único com Frota como feature, (b) dois modelos (793-D vs LeTourneau), (c) modelo único filtrado para 793-D apenas. Comparar AUC-PR e calibração.
- **Status**: ⏸️ **aberta** (decisão de modelagem da Fase 4); reforçada pela auditoria.
- **Reforço da auditoria** (2026-04-30): cross `Tag_Frota × Classe` dos 19.962 Don't Gos confirmou que **todos os 167 NULL Classe são da LeTourneau**, e as 4 frotas 793-D usam **Activate exclusivamente**. O pipeline OEM da LeTourneau não reporta `Classe` como o pipeline CAT — divergência estrutural.
- **Reforço da auditoria** (NIVEL CMA): LeTourneau só tem incidentes "Muito Alto" (32 de 32) — distribuição de severidade também distinta.
- **Implicação**: pode ser necessário documentar isso como limitação ou como solução.

### H017 — Propriedade emergente: `Nome_Operador_Anon` é universal quando há telemetria

- **Hipótese (descoberta na auditoria 2026-04-30)**: 100% dos eventos de telemetria que existem no parquet têm `Nome_Operador_Anon` preenchido (não há eventos com NULL nesse campo).
- **Origem**: auditoria 2026-04-30 (`docs/audit_fase2.md` §3 A2). Foi descoberta acidental ao corrigir o bug latente do denominador de `share_moda` em D016 — o BUG e a versão CORRETA produziram exatamente os mesmos números.
- **Como testar**: `SELECT 100.0 * SUM(CASE WHEN Nome_Operador_Anon IS NULL THEN 1 ELSE 0 END) / COUNT(*) FROM tel`.
- **Status**: ✅ **CONFIRMADA** (verificação direta sobre 37M eventos).
- **Implicações importantes**:
  1. **"Ciclo sem operador inferível" e "ciclo sem telemetria" são equivalentes** — não fenômenos independentes. Os 38,5% sem operador inferível na amostra (D016 / Fase 2E) são exatamente os ciclos sem telemetria.
  2. **D020 (flag `tem_telemetria=0`) cobre H013 e H017 com a mesma feature** — não precisamos de duas flags separadas.
  3. Para feature engineering: se um ciclo tem qualquer evento, o operador é conhecido com certeza (sujeito a D016 = moda dominante).

---

## Convenções

- **Não apagar** uma hipótese mesmo se refutada — registrar `Status=refutada` com referência ao notebook que a refutou. Hipóteses refutadas são tão informativas quanto as confirmadas para o relatório final.
- **Citar a hipótese** no `.tex` quando interpretarmos resultados (ex: "consistente com H002, observamos que…").
- Hipóteses H010+ derivadas da EDA têm origem nos JSONs de `reports/eda_results/` — auditável.

---

## Status final pós-Fase 5 (atualizado 2026-05-09)

| ID | Status final | Onde foi testada/observada |
|---|---|---|
| H001 | ✅ Confirmada (taxa 0,054%) + drift 3,71× entre meses | Fase 2C + auditoria |
| H002 | ✅ Confirmada — `n_crit_4h` top-1 SHAP em H1h e H4h | Fase 4G + Cap.4§Resultados de Modelagem |
| H003 | ✅ Confirmada — chi² turno p=1,7e-23, DOW p=2,7e-157 | Fase 2C |
| H004 | ✅ Confirmada — 793-D 5S concentra 56% dos incidentes | Fase 2D + análise de erros 5B (43% dos FN) |
| H005 | ⏸️ Inconclusiva — operador inferido em 61,5% dos ciclos; teste estatístico fica para fairness audit (Fase 6) | D016 + audit_fase2 |
| H006 | 🛑 Inconclusiva por construção (Itabira único — D005) — vira Trabalho Futuro #1 (Cap. 5§5.5 + Cap. 6) | — |
| H007 | ✅ Resolvida — operacionalizada via 6 horizontes paralelos (D001 v2); curva risco-vs-horizonte é resultado primário do trabalho | Fase 4B + Cap. 4 |
| H008 | ✅ Confirmada — 100% match flag×CMA | Fase 2 |
| H009 | ✅ Confirmada — `n_fam_engine_coolant_*h` top-3 SHAP em todos os horizontes | Fase 4G |
| H010 | ✅ Confirmada — drift normalizado −72,5%; Lift estável (D012 robusta) | Auditoria + Fase 4H |
| H011 | ✅ Confirmada — `n_naocrit_12h` top-3 em H12h SHAP | Fase 4G |
| H012 | ✅ Confirmada — Don't Go = Activate em CAT (D022 ratifica para LT) | Fase 2 |
| H013 | ✅ Confirmada — 17,6% Operando sem telemetria (populacional) | Fase 2E + 3A |
| H014 | ⚠️ Parcial — `n_fam_other_*h` aparece mas não é top-15 SHAP; em FNs (5B) está entre top-5 famílias proximais | Fase 4G + 5B |
| H015 | ✅ Confirmada — 80% alarmes com 1 ID, cauda longa até 50 | Fase 2 |
| H016 | ✅ Ratificada — D027 segregou treino CAT (PA-1) de LT (PA-3); D036 declarou PA-3 exploratório | Fase 3E + 4E |
| H017 | ✅ Confirmada — operador universal quando há telemetria | Auditoria |

Resumo: **13 confirmadas**, **2 ratificadas**, **1 parcial (H014)**, **2 inconclusivas** (H005, H006). Nenhuma refutada.
