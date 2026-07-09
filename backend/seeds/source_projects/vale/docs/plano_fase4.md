# Plano de Execução da Fase 4 — Modelagem (CRISP-DM Modeling)

> **Versão**: v1 — 2026-05-03
> **Princípio governante**: ROBUSTEZ > custo computacional.
> **Pré-requisitos**: Fases 0-3 concluídas e auditadas (33/33 PASSA, 0 issues semânticos), dataset v2 materializado em `data/processed/features_2025-{01..06}.parquet` (321.500 janelas / 89 colunas), decisões D001-D032 + D020 v2 formalizadas.

---

## 1. Resumo executivo

A Fase 4 produz **três modelos preditivos paralelos e complementares** sobre o dataset corrigido v2, ancorados nas decisões metodológicas formalizadas:

- **PA-1 (Supervisionado, decisão D004)** — classificador binário para cada um dos 6 horizontes paralelos (D001 v2), treinado **exclusivamente sobre o subconjunto Caterpillar** (D027) com walk-forward de 4 folds + junho intocado (D011).
- **PA-2 (Sobrevivência, decisão D017)** — Cox PH com teste de Schoenfeld + fallback Weibull AFT, usando `target_lead_time_min` (D030) como alvo. Mede `tempo até próximo Don't Go`.
- **PA-3 (Anomalia, decisão D027)** — Isolation Forest e Autoencoder LSTM **sobre LeTourneau apenas** (32 incidentes em 33,9 M eventos — supervisionado seria sub-amostrado).

Resultados são consolidados em **calibração (D014)**, **explicações SHAP** e **análise de drift entre folds** antes de virarem texto do Cap. 4 (segunda parte) do TCC.

**Volume estimado de modelos treinados**: 24 (PA-1: 6 horizontes × 4 folds) + 6 (PA-1 finais com junho como teste) + 6 (PA-2: 6 horizontes Cox PH) + 2 (PA-3: IF + LSTM) = **~38 artefatos modelos**.

**Tempo estimado de execução**: 22-25 horas de implementação + tuning (não wall-clock — assume desenvolvimento sequencial).

---

## 2. Princípios governantes recapitulados

| Princípio | Fonte | Como impacta a Fase 4 |
|---|---|---|
| ROBUSTEZ > custo | D000 | Optuna até 50 trials por horizonte; preferir Cox PH com Schoenfeld a regressão simples; preferir Autoencoder LSTM a vizinhança trivial |
| 6 horizontes paralelos | D001 v2 | 6 modelos PA-1 + 6 modelos PA-2 (não 1 modelo único) |
| AUC-PR primária | D002 | Ranking entre modelos pela AUC-PR; `lift = AUC-PR / prevalência` para comparação entre folds |
| Walk-forward 4 folds + jun intocado + buffer 4h | D011 | Junho **JAMAIS** entra em treino, validação ou tuning — só na avaliação final do modelo deployable |
| Pacote completo de métricas | D012 | AUC-PR, Lift, AUC-ROC, Brier, ECE, Recall@P=0,5, Lead time mediano em TPs |
| Sem SMOTE | D015 | `scale_pos_weight` (LightGBM) ou `class_weight='balanced'` (sklearn) — nunca oversampling temporal |
| Calibração D014 | D014 | Platt + Isotonic comparados por Brier/ECE no fold de validação |
| Apenas CAT no PA-1 | D027 | `df = df[df['OEM'] == 'Caterpillar']` antes de qualquer split |
| Apenas LeTourneau no PA-3 | D027 | `df_lt = df[df['OEM'] == 'LeTourneau']` para anomalia |
| `target_lead_time_min` é alvo, não feature | D030 | NUNCA aparece em `X` |
| Filtros de censura | D032 | `lookback_completo=1` para treino; `label_completa_Hh=1` para avaliação no horizonte H |

---

## 3. Sub-fases — 4A → 4I

### Fase 4A — Splits temporais e baselines

**Objetivo**: construir a infraestrutura de splits walk-forward (D011) e estabelecer o piso de qualidade contra o qual todos os modelos devem ser comparados.

**Inputs**:
- `data/processed/features_2025-{01..06}.parquet` (321.500 janelas)
- `data/processed/outlier_p99_thresholds.parquet`

**Processo**:

1. **Carga e filtro CAT** (D027):
   - Concatenar 6 parquets em um DataFrame único.
   - Filtrar `OEM == 'Caterpillar'`.
   - Esperado: ~30k janelas (CAT é 30 TAGs / 9% volume mas concentrado).

2. **Construção dos folds** (D011) — walk-forward expansivo:
   - **Fold 1**: treino jan; valida fev (buffer 4h entre treino e val).
   - **Fold 2**: treino jan+fev; valida mar.
   - **Fold 3**: treino jan+fev+mar; valida abr.
   - **Fold 4**: treino jan-abr; valida mai.
   - **Teste final intocado**: jun (NUNCA usado em tuning).
   - Buffer de 4 horas entre fim do treino e início da validação para impedir overlap de janelas via lookback de 12h.

3. **Filtros de censura** (D032):
   - Nos splits de **treino**: `lookback_completo=1` obrigatório.
   - Nos splits de **validação/teste**: `lookback_completo=1` E `label_completa_<H>h=1` (depende do horizonte).

4. **Baseline 1 — regra heurística** (consistente com a hipótese H011):
   - "Existe ao menos 1 evento Crítico nas últimas 4 h?" → predição binária (sem probabilidade).
   - Para o horizonte H, prediz `y_<H>h=1` se `n_crit_4h > 0`.
   - Calcula Recall, Precisão, F1, Brier (com prob=0/1 dummy).

5. **Baseline 2 — DummyClassifier estratificado** (sklearn):
   - `DummyClassifier(strategy='stratified', random_state=42)`.
   - Reproduz prevalência. Útil como piso absoluto de AUC-PR ≈ prevalência (lift = 1).

6. **Reporte** por horizonte × fold para ambos os baselines.

**Decisões a tomar nesta sub-fase**:
- Confirmar se buffer de 4h é suficiente (ou se 12h seria mais conservador, igualando o lookback máximo).
- Definir critério de "fold inválido": se o fold de validação tem 0 positivos, descartar ou registrar.

**Entregáveis**:
- `src/eval/splits.py` — funções `make_walk_forward_folds(df, n_folds=4, buffer_h=4)` e `apply_censura_filter(df, horizon_h)`.
- `src/eval/metrics.py` — pacote D012 (`auc_pr`, `lift`, `auc_roc`, `brier`, `ece`, `recall_at_precision`, `lead_time_p50`).
- `notebooks/_baseline_pa1.py` — runner que produz `reports/eda_results/fase4a_baselines.json`.

**Métricas de sucesso desta sub-fase**:
- Splits totalizam ~30k janelas CAT distribuídas em 4 folds de tamanhos crescentes.
- Cada fold tem ≥ 50 positivos no horizonte de 12h (caso contrário avaliação é instável).
- Baseline 1 atinge Recall ≥ 0,3 em pelo menos 2 horizontes (sanity check: a regra heurística captura algo).
- Baseline 2 fica em AUC-PR ≈ prevalência.

**Tempo estimado**: ~3 horas (implementação cuidadosa dos splits + métricas).

---

### Fase 4B — PA-1 LightGBM por horizonte (núcleo supervisionado)

**Objetivo**: produzir o classificador supervisionado primário para cada um dos 6 horizontes, com tuning Bayesiano via Optuna.

**Inputs**: Fase 4A finalizada.

**Processo**:

1. **Pipeline base LightGBM** (sem tuning):
   - `LGBMClassifier` com hiperparâmetros default + `scale_pos_weight = neg/pos` calculado por fold.
   - Features: 66 colunas `n_*` (sem `target_lead_time_min`, sem `y_dontgo_*`, sem `mes_str`).
   - Categóricas (`Tag_Frota`, `OEM`, `Tipo_canonico`, `bucket_hora`, `turno`, `Porte`) declaradas via `categorical_feature`.
   - `tem_telemetria` e flags de censura entram como features (são informativas).
   - Treino com `early_stopping_rounds=30` no fold validador.

2. **Tuning Optuna** — 50 trials por horizonte sobre o **fold 1 apenas** (fev como validação):
   - Espaço de busca:
     - `num_leaves` ∈ [15, 255]
     - `learning_rate` ∈ [0.01, 0.2] log-uniform
     - `max_depth` ∈ {-1, 4, 6, 8, 12}
     - `min_data_in_leaf` ∈ [10, 200]
     - `feature_fraction` ∈ [0.5, 1.0]
     - `bagging_fraction` ∈ [0.5, 1.0]
     - `bagging_freq` ∈ {0, 5, 10}
     - `lambda_l1` ∈ [0, 10] log-uniform
     - `lambda_l2` ∈ [0, 10] log-uniform
   - Objetivo: maximizar **AUC-PR** no fold validador.
   - **TPESampler** com `seed=42`.

3. **Treino final em cada fold**:
   - Usar `best_params` do Optuna (do fold 1) para retreinar nos 4 folds com `early_stopping`.
   - Salvar 24 modelos (`outputs/models/lgbm_h{1,2,4,6,8,12}_fold{1,2,3,4}.txt`).

4. **Avaliação no teste intocado (junho)**:
   - Usar o modelo treinado no fold 4 (treino = jan-mai).
   - Aplicar em junho com `label_completa_<H>h=1`.
   - Reportar pacote D012 + lead time bucketed (TP em [0-1h], [1-4h], [4-12h]).

5. **Análise de feature importance**:
   - `gain` (LightGBM nativo) — top-15 por horizonte.

**Decisões a tomar**:
- Se algum horizonte ficar com AUC-PR < lift 2× sobre baseline, registrar como "sinal fraco neste horizonte" antes de partir para XGB/CB.
- Se o fold 1 não convergir (early_stopping antes de 50 iterações), aumentar `n_estimators` máximo no Optuna.

**Entregáveis**:
- `src/models/pa1_lightgbm.py` — funções `tune_lgbm`, `train_final`, `evaluate_horizon`.
- `outputs/models/lgbm_*.txt` — 24 modelos serializados.
- `outputs/models/lgbm_best_params.json` — hyperparâmetros Optuna.
- `reports/eda_results/fase4b_pa1_lightgbm.json` — métricas D012 por horizonte × fold + teste em junho.
- `reports/figures/fig09_pr_curves_lgbm.png` — curvas PR por horizonte.
- `reports/figures/fig10_feature_importance_lgbm.png` — top-15 por horizonte.

**Métricas de sucesso**:
- Lift ≥ 5× sobre prevalência em pelo menos 4 dos 6 horizontes.
- Recall@P=0,5 ≥ 0,3 em pelo menos 3 horizontes (curtos).
- Lead time mediano dos TPs ≥ 30 min (modelo é útil operacionalmente — não apenas reativo).
- Em junho (teste): Brier ≤ 0,15 antes de calibração.

**Tempo estimado**: ~10 horas (Optuna 50 trials × 6 horizontes ≈ 5h + treino final 4 folds × 6h ≈ 2h + avaliação + figuras).

---

### Fase 4C — PA-1 comparação com XGBoost e CatBoost

**Objetivo**: confirmar (ou contestar) a escolha de LightGBM como modelo primário.

**Inputs**: Fase 4B finalizada (best_params do LightGBM como referência).

**Processo**:

1. **XGBoost** (`XGBClassifier`):
   - Hiperparâmetros traduzidos do LightGBM (mesmo `learning_rate`, `max_depth`, `min_child_weight` ≈ `min_data_in_leaf`).
   - **Sem novo tuning** — usar a mesma "vizinhança hp" do LightGBM por simetria.
   - Categóricas: `enable_categorical=True` (XGBoost 2.0+).

2. **CatBoost** (`CatBoostClassifier`):
   - Hiperparâmetros similares + `cat_features` declaradas.
   - **Sem novo tuning** — usar defaults razoáveis para classificação binária desbalanceada.

3. **Comparação por AUC-PR / Lift / Brier** em cada horizonte × fold.

**Decisões**:
- Se XGB ou CB superar LightGBM por > 5% relativo em AUC-PR no teste de junho, considerar swap.
- Caso contrário, manter LightGBM e relatar XGB/CB como "comparação de robustez" (texto do TCC).

**Entregáveis**:
- `src/models/pa1_xgb.py`, `src/models/pa1_catboost.py`.
- `reports/eda_results/fase4c_pa1_comparativo.json`.
- `reports/figures/fig11_pa1_comparativo.png` — AUC-PR de LGBM/XGB/CB por horizonte.

**Métricas de sucesso**:
- Diferença máxima de AUC-PR entre os 3 modelos < 10% — confirma estabilidade.
- Pelo menos 2 dos 3 algoritmos concordam no top-5 features (estabilidade interpretativa).

**Tempo estimado**: ~3 horas.

---

### Fase 4D — PA-2 Sobrevivência (Cox PH + Weibull AFT)

**Objetivo**: estimar o **tempo até o próximo Don't Go** com modelos de sobrevivência (D017).

**Inputs**:
- Dataset CAT (mesmo da Fase 4B).
- `target_lead_time_min` como alvo (D030) — clipado a 720 min.

**Processo**:

1. **Preparar dataset de sobrevivência**:
   - `T = target_lead_time_min` quando preenchido; caso contrário **censura**.
   - `E = 1` se `target_lead_time_min` preenchido (incidente observado em até 12h); `E = 0` se censura.
   - Features: subconjunto das 66 contagens + categóricas (mesmo X do PA-1).

2. **Cox Proportional Hazards** (`lifelines.CoxPHFitter`):
   - Treinar nos folds 1-4 (walk-forward).
   - **Teste de Schoenfeld** para verificar suposição PH em cada feature.
   - Se 3+ features falham Schoenfeld → fallback Weibull AFT.
   - Reportar `concordance_index` (C-index) e `IBS` (Integrated Brier Score) em horizontes {1, 2, 4, 8, 12} h.

3. **Weibull AFT** (`lifelines.WeibullAFTFitter`) como fallback:
   - Mesmo X.
   - C-index + IBS.

4. **Comparação Cox PH vs Weibull AFT** em cada fold + junho.

**Decisões**:
- Se C-index de ambos < 0,65 em junho → registrar como "PA-2 inconclusivo" (não bloqueia o trabalho — PA-1 e PA-3 ainda valem).

**Entregáveis**:
- `src/models/pa2_survival.py`.
- `outputs/models/cox_ph_fold{1..4}.pkl`, `weibull_aft_fold{1..4}.pkl`.
- `reports/eda_results/fase4d_pa2_survival.json` — C-index, IBS, p-valores Schoenfeld.
- `reports/figures/fig12_survival_curves.png` — curvas de sobrevivência por TAG representativo.

**Métricas de sucesso**:
- C-index ≥ 0,70 em pelo menos um modelo (Cox ou Weibull) em junho.
- p-valor Schoenfeld global > 0,05 (Cox PH) OU log-likelihood ratio > critical (Weibull).

**Tempo estimado**: ~3 horas.

---

### Fase 4E — PA-3 Anomalia (LeTourneau)

**Objetivo**: detectar pré-condições de Don't Go na frota LeTourneau via aprendizado **não supervisionado** — única lente viável dadas as 32 ocorrências em 33,9 M eventos.

**Inputs**:
- Dataset filtrado `OEM == 'LeTourneau'`.
- 32 incidentes conhecidos como "validação positiva" (não usados em treino).

**Processo**:

1. **Isolation Forest** (`sklearn.ensemble.IsolationForest`):
   - `n_estimators=200`, `contamination='auto'`, `random_state=42`.
   - Treinar em janelas LeTourneau **sem** olhar `y_dontgo_*`.
   - Score `decision_function` (quanto menor, mais anômalo).
   - Avaliar: % dos 32 incidentes com score no top-N% (N ∈ {1, 5, 10, 25}%).

2. **Autoencoder LSTM** (PyTorch):
   - Input: sequência das últimas 12 janelas de 15 min (3h de história) por (TAG, t).
   - Arquitetura: LSTM encoder → bottleneck (8 dim) → LSTM decoder → reconstrução.
   - Loss: MSE de reconstrução.
   - Score = erro de reconstrução. Quanto maior, mais anômalo.
   - Mesma avaliação top-N%.

3. **Comparação IF vs LSTM**:
   - Métrica primária: **% dos 32 incidentes capturados em top-10% scores**.
   - Métrica secundária: precisão no top-1% (taxa de TP em alarmes muito raros).

**Decisões**:
- Se top-10% capturar < 50% dos incidentes → registrar como sinal fraco; PA-3 vira "exploratório" no texto.
- Se LSTM superar IF por > 20% relativo no top-10% → declarar LSTM como modelo primário PA-3.

**Entregáveis**:
- `src/models/pa3_isolation_forest.py`, `src/models/pa3_autoencoder_lstm.py`.
- `outputs/models/iforest_lt.pkl`, `outputs/models/ae_lstm_lt.pt`.
- `reports/eda_results/fase4e_pa3_anomaly.json`.
- `reports/figures/fig13_anomaly_capture_curve.png` — curva % capturado vs % alarmes.

**Métricas de sucesso**:
- Top-10% scores captura ≥ 50% dos 32 incidentes (≥ 16 / 32).
- Top-1% scores tem ≥ 5 incidentes (precisão informativa em volume tratável).

**Tempo estimado**: ~5 horas (LSTM exige cuidado).

---

### Fase 4F — Calibração (D014)

**Objetivo**: garantir que `model.predict_proba` produz probabilidades **operacionalmente confiáveis** (Brier baixo, ECE baixo).

**Inputs**: melhor PA-1 da Fase 4B/4C.

**Processo**:

1. **CalibratedClassifierCV** (sklearn) — duas variantes:
   - `method='sigmoid'` (Platt scaling).
   - `method='isotonic'` (regressão isotônica).
   - **Calibração no fold de validação** (jamais no teste de junho).

2. **Comparação Brier / ECE pre × pós-calibração** em junho.

3. **Decisão final**: escolher o método com menor Brier em junho. Se isotônica e Platt empatarem em Brier mas isotônica tiver melhor ECE, escolher isotônica.

**Entregáveis**:
- `src/models/calibration.py`.
- `outputs/models/lgbm_calibrated_h{1,2,4,6,8,12}.pkl`.
- `reports/eda_results/fase4f_calibration.json`.
- `reports/figures/fig14_calibration_curves.png` — reliability diagrams pre/pós.

**Métricas de sucesso**:
- ECE pós-calibração ≤ 0,05 em pelo menos 4 horizontes.
- Brier pós ≤ Brier pré em todos os horizontes (calibração não pode piorar).

**Tempo estimado**: ~2 horas.

---

### Fase 4G — Explicações SHAP

**Objetivo**: interpretar os modelos PA-1 com `shap.TreeExplainer` para responder "por que o modelo previu Don't Go neste instante?".

**Inputs**: modelos finais PA-1 calibrados (Fase 4F).

**Processo**:

1. **Global**: `shap.summary_plot` para cada horizonte (top-15 features por |SHAP|).

2. **Local**: `shap.waterfall_plot` em **5 incidentes representativos**, escolhidos:
   - 1 TP em horizonte de 1h (acerto curto).
   - 1 TP em horizonte de 12h (acerto longo).
   - 1 FN em horizonte de 1h (modelo "perdeu").
   - 1 FP em horizonte de 4h (alarme falso).
   - 1 TP da LeTourneau (sob anomalia, contexto diferente).

3. **Dependência**: `shap.dependence_plot` para top-3 features de cada horizonte (ex.: `n_naocrit_4h` vs taxa de Don't Go).

**Decisões**:
- Se SHAP destaca features de censura (`lookback_completo`) entre top-5, isso é red flag — pode indicar que o modelo está apenas aprendendo "estou perto da borda do dataset". Investigar e remover do treino se confirmado.

**Entregáveis**:
- `notebooks/_make_shap_plots.py`.
- `reports/figures/fig15_shap_summary_h{1,4,12}.png`.
- `reports/figures/fig16_shap_waterfall_5incidentes.png`.
- `reports/figures/fig17_shap_dependence_top3.png`.

**Métricas de sucesso**:
- Top-5 features SHAP coerentes com hipóteses H002 (sequência), H009 (família), H011 (acumulação não-crítica).

**Tempo estimado**: ~3 horas.

---

### Fase 4H — Análise de drift entre folds

**Objetivo**: quantificar o drift de distribuições entre treinos e testes — antecipa problemas operacionais em deploy.

**Inputs**: folds da Fase 4A.

**Processo**:

1. **PSI (Population Stability Index)** entre treino-fold e validação-fold para cada feature numérica:
   - `PSI < 0,1` → estável.
   - `0,1 ≤ PSI < 0,25` → atenção.
   - `PSI ≥ 0,25` → drift severo.

2. **KS test (Kolmogorov-Smirnov)** entre folds para top-20 features mais importantes (SHAP).

3. **Análise de correlação drift × degradação**:
   - Para cada fold, calcular `delta_AUC-PR = AUC-PR(treino) - AUC-PR(val)`.
   - Correlacionar com PSI médio das features importantes.

**Entregáveis**:
- `src/eval/drift.py`.
- `reports/eda_results/fase4h_drift.json`.
- `reports/figures/fig18_psi_heatmap.png`.

**Métricas de sucesso**:
- Fold 4 → junho: PSI médio < 0,25 nas top-10 features (drift "tolerável").
- Se PSI médio ≥ 0,25 → registrar formalmente no Cap. 5 (Discussão) como limitação.

**Tempo estimado**: ~2 horas.

---

### Fase 4I — Notebook canônico + redação Cap. 4 parte 2

**Objetivo**: consolidar tudo em artefatos de entrega.

**Inputs**: todas as Fases 4A-4H finalizadas.

**Processo**:

1. **`notebooks/04_modeling.ipynb`** — narrativa completa:
   - Setup + carga.
   - Splits e baselines (Fase 4A).
   - PA-1 LightGBM com tuning + métricas (4B).
   - Comparação com XGB/CB (4C).
   - PA-2 sobrevivência (4D).
   - PA-3 anomalia LeTourneau (4E).
   - Calibração (4F).
   - SHAP (4G).
   - Drift (4H).

2. **`docs/article_dontgo/cap4_resultados.tex` parte 2** — escrever:
   - § Splits temporais e metodologia de avaliação.
   - § Resultados PA-1 (LightGBM com tabela 6 horizontes × 4 folds × pacote D012).
   - § Comparação com XGBoost/CatBoost.
   - § Resultados PA-2 (Cox PH + Weibull AFT).
   - § Resultados PA-3 (Isolation Forest + Autoencoder LSTM).
   - § Calibração de probabilidades.
   - § Interpretação via SHAP.
   - § Análise de drift e limitações.

3. **Atualizar `MEMORY.md §13`** — checkpoint da Fase 4 + handoff para Fase 5 (Avaliação) / Fase 6 (Implantação).

**Entregáveis**:
- `notebooks/04_modeling.ipynb` — 30+ cells executáveis.
- `cap4_resultados.tex` parte 2 — adicionar ~150 linhas.
- `MEMORY.md §13` — checkpoint completo.
- PDF recompilado (estimado 75-80 páginas).

**Tempo estimado**: ~4 horas.

---

## 4. Cronograma agregado

| Sub-fase | Tempo estimado | Dependências |
|---|---:|---|
| 4A — Splits + baselines | 3h | Fase 3 v2 |
| 4B — PA-1 LightGBM | 10h | 4A |
| 4C — Comparação XGB/CB | 3h | 4B |
| 4D — PA-2 sobrevivência | 3h | 4A |
| 4E — PA-3 anomalia | 5h | 4A (subset LT) |
| 4F — Calibração | 2h | 4B (modelo final) |
| 4G — SHAP | 3h | 4F |
| 4H — Drift | 2h | 4B |
| 4I — Notebook + artigo | 4h | 4A-4H |
| **Total** | **35h** | |

> O total é ligeiramente acima dos "22-25h" do resumo inicial — ajustado considerando overhead de figuras, debugging do tuning Optuna e redação cuidadosa do artigo.

**Caminho crítico**: 4A → 4B → 4F → 4G → 4I (24h sequenciais).

**Paralelização possível**: 4D, 4E, 4H podem rodar em paralelo a 4C/4F após 4A/4B prontos.

---

## 5. Critérios de sucesso global

A Fase 4 é declarada **fechada** quando:

1. Todos os 33+ checks da auditoria automatizada (extensão de `_audit_fases_0_a_3.py`) passam.
2. **PA-1 LightGBM**: lift ≥ 5× sobre prevalência em ≥ 4 horizontes; Recall@P=0,5 ≥ 0,3 em ≥ 3 horizontes; ECE pós-calibração ≤ 0,05.
3. **PA-2**: C-index ≥ 0,70 em junho.
4. **PA-3**: top-10% scores captura ≥ 50% dos 32 incidentes LeTourneau.
5. **SHAP**: top-3 features de cada horizonte têm sentido físico/operacional alinhado com H002/H009/H011 (interpretação humana).
6. **Drift**: PSI médio < 0,25 entre fold 4 → junho nas top-10 features OU registro formal da limitação no Cap. 5.
7. **Artigo**: Cap. 4 parte 2 escrita; PDF recompila sem erros.
8. **MEMORY.md §13** completo com handoff para Fase 5.

---

## 6. Riscos identificados

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Optuna 50 trials × 6 horizontes excede tempo razoável (>10h CPU) | Média | Reduzir para 30 trials no fold 1 + reaproveitar best_params com leve perturbação por horizonte |
| Fold 4 → junho mostra drift severo (PSI > 0,25) | Alta (já confirmado H010 −72,5%) | Reportar transparentemente; lift normaliza por prevalência local |
| LeTourneau PA-3: 32 incidentes podem ser insuficientes mesmo para top-N% | Média | Reportar com IC 95% via bootstrap dos 32 incidentes |
| Cox PH falha Schoenfeld em > 50% das features | Média | Fallback Weibull AFT já planejado (D017) |
| LightGBM categóricas não convergem com `Tag_Frota` (4 categorias CAT) | Baixa | One-hot fallback como contingência |
| SHAP de modelo grande (66 features) gera figuras ilegíveis | Baixa | Limitar a top-15 features no `summary_plot` |
| Disco/memória limitados ao salvar 24+ modelos | Baixa | LightGBM `.txt` é leve (~MB cada) |

---

## 7. Pontos de pausa para aprovação

Conforme estilo de trabalho exigido (passo-a-passo), cada checkpoint pausa para confirmação:

| Checkpoint | Pausa após | Decisão a confirmar |
|---|---|---|
| C1 | 4A (baselines reportados) | Critério de "modelo pior que baseline = problema sério" está calibrado? |
| C2 | 4B (PA-1 com tuning) | Seguir com XGB/CB ou LightGBM já basta? |
| C3 | 4D (PA-2) | Cox PH ou Weibull como modelo primário PA-2? |
| C4 | 4E (PA-3) | Isolation Forest, LSTM ou ambos como modelo primário PA-3? |
| C5 | 4F (calibração) | Platt ou Isotonic? |
| C6 | 4G (SHAP) | Top-5 features fazem sentido operacional? |
| C7 | 4I (artigo) | Cap. 4 parte 2 está pronta para banca? |

---

## 8. Apêndices técnicos

### A. Esquema de seeds para reprodutibilidade

```python
from src.utils.seeds import set_global_seed
set_global_seed()  # SEED=42 em random/numpy/torch/lightgbm/xgboost/catboost
# Optuna:
study = optuna.create_study(direction='maximize',
                            sampler=optuna.samplers.TPESampler(seed=42))
```

### B. Estrutura de diretórios prevista após Fase 4

```text
Vale/
├── src/
│   ├── eval/
│   │   ├── splits.py           [novo - 4A]
│   │   ├── metrics.py          [novo - 4A]
│   │   └── drift.py            [novo - 4H]
│   └── models/
│       ├── pa1_lightgbm.py     [novo - 4B]
│       ├── pa1_xgb.py          [novo - 4C]
│       ├── pa1_catboost.py     [novo - 4C]
│       ├── pa2_survival.py     [novo - 4D]
│       ├── pa3_isolation_forest.py  [novo - 4E]
│       ├── pa3_autoencoder_lstm.py  [novo - 4E]
│       └── calibration.py      [novo - 4F]
├── outputs/
│   └── models/                 [novo]
│       ├── lgbm_h{1,2,4,6,8,12}_fold{1,2,3,4}.txt   [24 modelos]
│       ├── lgbm_calibrated_h{1,2,4,6,8,12}.pkl      [6 modelos]
│       ├── lgbm_best_params.json
│       ├── cox_ph_fold{1..4}.pkl
│       ├── weibull_aft_fold{1..4}.pkl
│       ├── iforest_lt.pkl
│       └── ae_lstm_lt.pt
├── reports/
│   ├── figures/
│   │   ├── fig09_pr_curves_lgbm.png             [4B]
│   │   ├── fig10_feature_importance_lgbm.png    [4B]
│   │   ├── fig11_pa1_comparativo.png            [4C]
│   │   ├── fig12_survival_curves.png            [4D]
│   │   ├── fig13_anomaly_capture_curve.png      [4E]
│   │   ├── fig14_calibration_curves.png         [4F]
│   │   ├── fig15_shap_summary_h{1,4,12}.png     [4G]
│   │   ├── fig16_shap_waterfall_5incidentes.png [4G]
│   │   ├── fig17_shap_dependence_top3.png       [4G]
│   │   └── fig18_psi_heatmap.png                [4H]
│   └── eda_results/
│       ├── fase4a_baselines.json
│       ├── fase4b_pa1_lightgbm.json
│       ├── fase4c_pa1_comparativo.json
│       ├── fase4d_pa2_survival.json
│       ├── fase4e_pa3_anomaly.json
│       ├── fase4f_calibration.json
│       └── fase4h_drift.json
├── notebooks/
│   ├── _baseline_pa1.py
│   ├── _make_shap_plots.py
│   └── 04_modeling.ipynb       [final canônico]
└── docs/
    ├── decisions.md             [adicionar D033+ se houver]
    └── article_dontgo/
        └── cap4_resultados.tex  [parte 2 acrescida]
```

### C. Bibliotecas e versões a usar (já em `requirements.txt`)

- `lightgbm` (PA-1)
- `xgboost` (PA-1 comparativo)
- `catboost` (PA-1 comparativo)
- `lifelines >= 0.30.3` (PA-2 — Cox PH, Weibull AFT, Schoenfeld)
- `scikit-learn` (DummyClassifier, IsolationForest, CalibratedClassifierCV)
- `torch` (PA-3 LSTM)
- `optuna` (tuning)
- `shap` (interpretação)
- `prophet 1.3.0` (auxiliar opcional para análise de drift sazonal)

### D. Comandos úteis durante a Fase 4

```bash
# Reprodução completa da Fase 4
python -m src.eval.splits --check
python notebooks/_baseline_pa1.py
python -m src.models.pa1_lightgbm --tune --train --evaluate
python -m src.models.pa1_xgb --train --evaluate
python -m src.models.pa1_catboost --train --evaluate
python -m src.models.pa2_survival --train --evaluate
python -m src.models.pa3_isolation_forest --train --evaluate
python -m src.models.pa3_autoencoder_lstm --train --evaluate
python -m src.models.calibration --apply
python notebooks/_make_shap_plots.py
python -m src.eval.drift --report

# Auditoria final da Fase 4 (extensão de _audit_fases_0_a_3.py)
python notebooks/_audit_fases_0_a_4.py
```

---

## 9. O que NÃO entra na Fase 4

Para evitar escopo expandido (D000):

- ❌ **Fine-tuning manual** após Optuna — confiar no resultado bayesiano.
- ❌ **Stacking ou ensembling** entre PA-1/PA-2/PA-3 — fica para Fase 5 (Avaliação) se houver tempo.
- ❌ **Treino contínuo / online learning** — fora do escopo.
- ❌ **Replay temporal** (refit a cada novo dia) — fora do escopo.
- ❌ **Otimização de inferência** (latência, memória) — Fase 6 (Implantação).
- ❌ **GUI ou dashboard** — fora do escopo.

---

## 10. Próximo passo concreto

Aguardar OK do usuário para iniciar **Fase 4A** (splits + baselines). Eu pretendo:

1. Criar `src/eval/splits.py` com `make_walk_forward_folds` e `apply_censura_filter`.
2. Criar `src/eval/metrics.py` com o pacote D012.
3. Rodar `notebooks/_baseline_pa1.py` que produz `fase4a_baselines.json`.
4. Reportar resultados e pausar no checkpoint C1 antes de seguir para 4B.

Aguardando autorização.
