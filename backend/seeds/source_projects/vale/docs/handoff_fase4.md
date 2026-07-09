# Continuação do projeto Vale — Fase 4 (Modeling / CM 4.1, 4.2, 4.3)

Estou continuando um projeto que já tem **Fases 0, 1, 2 e 3 fechadas + auditadas**. Você está entrando frio, então leia os artefatos existentes ANTES de qualquer ação.

## 1. Diretório de trabalho

**Path absoluto** (Windows, contém espaços e acento — em comandos bash sempre cite com aspas duplas):

```text
c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale
```

## 2. Ordem de leitura obrigatória (não pule)

Leia, nesta ordem:

1. `MEMORY.md` (raiz) — caderno de bordo. Tem o protocolo de handoff, princípio governante, mapeamento CRISP-DM↔ABNT, inventário de dados, e checkpoints das Fases 1, 2, 3 + auditorias. **§12 contém a tabela canônica do dataset v2 (321.500 janelas).**
2. **`docs/plano_fase4.md`** — **O PLANO DETALHADO QUE VOCÊ VAI EXECUTAR** (~440 linhas, 9 sub-fases 4A→4I, cronograma, critérios de sucesso, pontos de pausa, apêndices técnicos). Este é o seu documento-mestre.
3. `docs/decisions.md` — **33 decisões formais (D001-D032 + D020 v2)**. Todas fechadas. Não as redebata sem motivo forte. Especialmente importantes para Fase 4: D001 v2 (6 horizontes), D002 (AUC-PR), D003 (Recall@P=0,5 + Lead time), D004 (PA-1/PA-2/PA-3), D008 (15 min), D010 (blackout 5 min), D011 (walk-forward 4 folds + jun intocado + buffer 4h), D012 (pacote completo de métricas), D014 (calibração Platt + Isotonic), D015 (sem SMOTE), D017 (Cox PH + Weibull AFT), D027 (CAT segregado da LeTourneau), D030 (lead_time é alvo, não feature).
4. `docs/hypotheses.md` — **17 hipóteses (H001-H017)**. H002, H009, H011, H014 estão marcadas OPERACIONALIZADA — viraram features no dataset; serão **testadas** na Fase 4 via SHAP e feature importance.
5. `docs/features.md` — **catálogo do schema do dataset v2** (89 colunas: 9 ID/temp + 66 contagens + 6 labels + 1 alvo lead + 8 derivadas/flags). Leia inteiro antes de carregar parquets.
6. `docs/audit_fase3a.md` — relatório do diagnóstico pré-limpeza da Fase 3.
7. `PENDENCIAS.md` — status atual das pendências (todas fechadas em 2026-05-03).
8. `reports/eda_results/audit_fases_0_3.json` — resultados da auditoria automatizada (33/33 PASSA / 0 FALHA).
9. `reports/eda_results/fase3c_build_report.json` — números canônicos do dataset v2.

Confirme em uma linha que leu tudo antes de avançar.

## 3. Status atual do projeto

- **Fase 0 (setup)** ✅ — `requirements.txt` fixado; `lightgbm`, `xgboost`, `catboost`, `lifelines`, `prophet`, `torch`, `shap`, `optuna` instalados.
- **Fase 1 (Business Understanding)** ✅ — CM 1.1 e CM 1.2 v2 fechados; 17 decisões D001-D017 + 17 hipóteses H001-H017 (na origem).
- **Fase 2 (Data Understanding / EDA)** ✅ — 5 JSONs canônicos em `reports/eda_results/`, 12 figuras, notebook `02_data_understanding_eda.ipynb` com 28 cells executadas, auditoria pós-fase aplicada.
- **Fase 3 (Data Preparation)** ✅ — **dataset v2 corrigido** após auditoria de PENDENCIAS (2026-05-03):
  - 321.500 janelas em 6 parquets `data/processed/features_2025-{01..06}.parquet`.
  - 89 colunas (66 features de contagem + 6 labels + 1 alvo lead + 16 metadados).
  - **APENAS ciclos `Operando`** (D029) — cobertura 99,3%.
  - **`target_lead_time_min` clipado a 12h** (D030) — alvo auxiliar PA-2, **NUNCA usar como feature**.
  - **Contagens NaN quando `tem_telemetria=0`** (D020 v2) — preserva semântica.
  - **P99 de outlier calibrado externamente** (D031) sobre jan+fev em `outlier_p99_thresholds.parquet`.
  - **Flags de censura nas bordas** (D032): `lookback_completo` + `label_completa_12h`.
- **Auditoria Fases 0-3** ✅ — 33/33 PASSA, 0 issues semânticos.
- **TCC compilável** em `docs/article_dontgo/TCC_DontGo.tex` (61 páginas / 915,8 KB), com Cap. 1, 2, 3 (com Fase 3) e Cap. 4 parte 1 (Fase 2) escritos.

## 4. Princípio governante (não negociável)

> **ROBUSTEZ > custo computacional.** Sempre escolher o método mais rigoroso, mesmo que mais lento.

## 5. Achados-chave das Fases 0-3 que IMPACTAM A FASE 4

### Volume e estratificação

- **CAT 793-D**: 30 TAGs / 9% volume / **4.993 incidentes** (99,4%) / taxa 0,603% por evento. Vai para **PA-1 (supervisionado) + PA-2 (sobrevivência)**.
- **LeTourneau L 1850**: 5 TAGs / 91% volume / **32 incidentes** (0,6%) / taxa 0,000493% por evento. **Razão CAT/LT = 1.224×.** Vai para **PA-3 (anomalia não supervisionada)** — D027.
- Após filtro CAT no dataset v2: ~30k janelas (não 321.500 — atenção!).

### Drift temporal severo (H010 refinada)

- Prevalência de incidentes Don't Go cai **−72,5%** entre fevereiro (peak) e junho (vale), normalizado por volume de telemetria.
- Razão max/min da taxa por evento entre meses = **3,71×**.
- **Implicação**: `lift = AUC-PR / prevalência` (D012) é a métrica que normaliza isso. Comparar AUC-PR absoluto entre folds é enganoso.
- **Implicação para validação walk-forward**: junho (teste intocado) tem **prevalência muito menor** que fevereiro/março — modelos treinados em folds antigos podem mostrar quedas de AUC-PR absoluto que NÃO refletem degradação real.

### Sinal preditivo já evidente (Fase 3B)

- **`is_valor_outlier_p99` tem lift 87,9×** sobre prevalência global de Don't Go (auditoria empírica). Marca apenas 0,04% das linhas mas 4,75% delas são positivas.
- **52% dos incidentes começam com alarme `Não Crítico`** (H011 — Don't Go é por acumulação, não severidade isolada). Features `n_naocrit_<W>h` são candidatas naturais a importância alta no SHAP.
- **Engine_Coolant é família dominante**: 42% dos 5.025 incidentes começam com alarme dessa família (top driver).

### Validação CMA (D006 ratificada)

- 100% dos 967 positivos amostrados batem com regras `(Alto + Muito Alto)` do catálogo CMA.
- Ground truth confiável — não há ruído na flag `Is_Dont_Go`.

### Pipeline OEM divergente (D022)

- LeTourneau usa `Classe=NULL` em 100% dos seus 167 Don't Gos.
- CAT usa `Classe=Activate` em 100%.
- O modelo CAT pode usar `Classe` como feature; o pipeline LT (PA-3) precisa lidar com NULL como categoria estrutural.

## 6. Próxima tarefa: Fase 4 — Modeling

**Documento-mestre**: `docs/plano_fase4.md` (já existe, 440 linhas).

Estrutura resumida:

| # | Sub-fase | Tempo | Critério de pausa |
|---|---|---:|---|
| 4A | Splits walk-forward + 2 baselines | 3h | C1 |
| 4B | PA-1 LightGBM com Optuna 50 trials × 6 horizontes | 10h | C2 |
| 4C | Comparativo XGBoost / CatBoost | 3h | — |
| 4D | PA-2 sobrevivência (Cox PH + Weibull AFT) | 3h | C3 |
| 4E | PA-3 anomalia (Isolation Forest + LSTM AE) sobre LeTourneau | 5h | C4 |
| 4F | Calibração Platt × Isotonic | 2h | C5 |
| 4G | SHAP global + waterfall em 5 incidentes | 3h | C6 |
| 4H | Drift PSI / KS entre folds | 2h | — |
| 4I | Notebook 04 + Cap. 4 parte 2 + MEMORY §13 + recompilar PDF | 4h | C7 |

**Total estimado**: ~35h de implementação.

Os critérios de sucesso quantitativos, riscos identificados, e estrutura de diretórios prevista estão **todos no plano**. Não recriar.

## 7. Volume de dados (cuidado com RAM)

- **Dataset v2 completo**: 321.500 linhas × 89 cols ≈ 220 MB em RAM se carregado tudo. OK pandas direto.
- **Após filtro `OEM='Caterpillar'` (D027)**: ~30k linhas. Trivial.
- **Após filtro `OEM='LeTourneau'` (D027)** para PA-3: ~291k linhas. Para Autoencoder LSTM com sequências de 12 janelas, montar batch sob demanda — não materializar tensor completo.
- **Telemetria bruta** (37 M eventos / 28 GB se em pandas): NÃO carregar. Toda análise sobre o dataset v2 já agregado dispensa isso.

## 8. Estrutura de código existente (NÃO recriar)

```text
Vale/
├── requirements.txt                                    [pacotes fixados]
├── src/
│   ├── utils/
│   │   ├── paths.py                                    [PROJECT_ROOT, DATA_DIR, etc]
│   │   └── seeds.py                                    [SEED=42, set_global_seed()]
│   ├── data/
│   │   ├── loaders.py                                  [duckdb lazy + apontamentos pandas]
│   │   ├── mappings.py                                 [Tag_Frota → Porte/OEM/Tipo]
│   │   ├── cleaning.py                                 [clean_telemetria + clean_apontamentos]
│   │   ├── incidents.py                                [apply_incidents_d009 — canônica]
│   │   └── coverage.py                                 [compute_telemetry_coverage]
│   └── features/
│       ├── families.py                                 [14 famílias funcionais + Other, FAMILIES_SQL_CASE]
│       ├── builders.py                                 [v2 — gera features para um mês]
│       └── outlier_calibration.py                      [P99 calibrado externamente]
├── data/processed/
│   ├── features_2025-{01..06}.parquet                  [DATASET v2 — 321.500 janelas]
│   ├── outlier_p99_thresholds.parquet                  [529 limiares P99 fixos]
│   └── coverage_populacional.parquet
├── notebooks/
│   ├── 02_data_understanding_eda.ipynb                 [Fase 2 final]
│   ├── 03_data_preparation.ipynb                       [Fase 3 final v2]
│   ├── _audit_fases_0_a_3.py                           [auditoria automatizada — extender para Fase 4]
│   └── _audit_fase3*.py + _build_features_dataset.py + outros runners offline
├── reports/
│   ├── figures/fig01..fig08*.png                       [12+ figuras das Fases 2-3]
│   └── eda_results/fase{2b,2c,2d,2e,3a,3b,3c,3d,3e,audit_fase2}*.json
└── docs/
    ├── plano_fase4.md                                  [SEU DOCUMENTO-MESTRE]
    ├── decisions.md                                    [D001-D032 + D020 v2, em ordem]
    ├── hypotheses.md                                   [H001-H017]
    ├── features.md                                     [catálogo do schema do dataset]
    ├── audit_fase3a.md                                 [diagnóstico pré-limpeza]
    └── article_dontgo/TCC_DontGo.{tex,pdf,bib}         [TCC, 61 páginas]
```

**Crie em**:
- `src/eval/{splits.py, metrics.py, drift.py}` (Fase 4A, 4H).
- `src/models/{pa1_lightgbm.py, pa1_xgb.py, pa1_catboost.py, pa2_survival.py, pa3_isolation_forest.py, pa3_autoencoder_lstm.py, calibration.py}` (Fases 4B-4F).
- `outputs/models/` (modelos serializados).
- `notebooks/_audit_fases_0_a_4.py` (auditoria estendida).
- `notebooks/04_modeling.ipynb` (notebook canônico final).

## 9. Cuidados específicos / armadilhas conhecidas

- **`target_lead_time_min` é alvo, NUNCA feature** (D030). Sempre fazer `X = df.drop(columns=[c for c in df.columns if c.startswith('y_dontgo_') or c == 'target_lead_time_min'])` ou listar features explicitamente.
- **`tem_telemetria=0` ⇒ contagens são `NaN`** (D020 v2). LightGBM e XGBoost lidam nativamente; sklearn pode precisar `SimpleImputer` ou aceitar via `enable_categorical`.
- **Filtro de censura D032**:
  - Treino requer `lookback_completo=1`.
  - Avaliação no horizonte H requer `label_completa_<H>h=1` (atualmente só `label_completa_12h` está materializada — para horizontes < 12h derive uma flag análoga: `t_window <= '2025-06-30 24:00' - INTERVAL <H> HOUR`).
- **Walk-forward expansivo (D011)**: cada fold treina em jan-`<m>` e valida em `<m+1>`. O fold 4 treina em jan-mai e valida em mai... espera, releia D011:
  - Fold 1: treino jan, val fev (buffer 4h).
  - Fold 2: treino jan+fev, val mar.
  - Fold 3: treino jan+fev+mar, val abr.
  - Fold 4: treino jan+fev+mar+abr, val mai.
  - Teste intocado: jun (modelo deployable).
- **Buffer 4h entre treino e validação**: na verdade, dado que o lookback maior é 12h, o buffer mais conservador seria 12h. Mas D011 fixa 4h. Se Fase 4A descobrir overlap problemático, **propor revisão de D011 com justificativa empírica**, não silenciosamente mudar.
- **Optuna**: rodar 50 trials apenas no fold 1 (não em todos os 4). Reaproveitar `best_params` para retreinar nos demais folds com `early_stopping`. Isso reduz custo de ~200 trials para 50.
- **DuckDB SQL com `SELECT *`**: erro interno em sub-queries aninhadas com `Valor_num` (DOUBLE) e `Valor` (VARCHAR). Workaround: `CREATE OR REPLACE VIEW tel_view AS <query>` e usar a view. Já documentado em `_audit_fase3d.py` e `_audit_fase3e.py`.
- **Encoding console Windows é cp1252**; sempre passe `encoding="utf-8"` em `write_text`/`read_text` para arquivos persistidos. Para imprimir Unicode no terminal: `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`.
- **PYTHONHASHSEED warn na seeds.py** é cosmético — não bloqueia.
- **Categóricas LightGBM**: `Tag_Frota`, `OEM`, `Tipo_canonico`, `bucket_hora`, `turno`, `Porte` devem entrar como `categorical_feature=[...]`. CatBoost: usar `cat_features=[...]`. XGBoost ≥ 2.0: `enable_categorical=True`.
- **`scale_pos_weight` por fold**: calcular `neg/pos` no fold de treino, não global. Prevalências variam de 2,6% a 7,7% por mês.
- **Junho NUNCA em treino/tuning/validação interna**. É *holdout* final.

## 10. O que NÃO refazer

- ❌ Reabrir CM 1.1, CM 1.2, CM 2.x, CM 3.x — todas fechadas e auditadas.
- ❌ Reabrir EDA — todos os números canônicos estão em `reports/eda_results/`.
- ❌ Re-discutir definição de incidente — D009 + D018 fechadas (tol 30 min).
- ❌ Re-discutir validação — D011 inalterada (walk-forward 4 folds + buffer 4h + jun intocado).
- ❌ Re-discutir métricas — D012 inalterada (pacote completo).
- ❌ Re-discutir leakage — D010 (blackout 5 min) + D031 (P99 calibrado externamente) + D032 (censura) já fechadas.
- ❌ Re-discutir múltiplos horizontes — D001 v2 fechada (6 horizontes paralelos).
- ❌ Re-discutir calibração — D014 fechada (Platt + Isotonic).
- ❌ Re-discutir SMOTE — D015 fechada (proibido em séries temporais).
- ❌ Re-discutir sobrevivência — D017 fechada (Cox PH + Schoenfeld + Weibull AFT).
- ❌ Re-discutir estratégia OEM — D027 fechada (CAT supervisionado segregado / LT anomalia).
- ❌ Re-materializar dataset v2 — `data/processed/features_*.parquet` está canônico após auditoria 2026-05-03.
- ❌ Recalibrar P99 — `outlier_p99_thresholds.parquet` é fixo (D031).
- ❌ Tocar em `D:\TCC - versão final\article\` (TCC anterior do autor sobre Evasão Acadêmica — projeto separado).

## 11. Estilo de trabalho exigido

> **PASSO A PASSO, PARTE POR PARTE.** Nunca despeje tudo de uma vez.

- Antes de criar qualquer arquivo, **proponha em texto** o que vai fazer e **aguarde OK**.
- Após cada sub-fase (4A → 4I), **pause no checkpoint correspondente (C1-C7)** e reporte os achados.
- Atualize `MEMORY.md`, `docs/decisions.md`, `docs/hypotheses.md` conforme avança.
- Use `TodoWrite` para tracking quando a sub-fase tiver 3+ passos.
- **O artigo TCC (`docs/article_dontgo/cap4_resultados.tex` parte 2 + `cap5_discussao.tex`) deve ser escrito ao decorrer da fase**, não no fim. Não acumule a redação para o último dia.

## 12. Entregáveis esperados ao fim da Fase 4

Conforme `docs/plano_fase4.md` Apêndice B:

- `src/eval/{splits.py, metrics.py, drift.py}`
- `src/models/{pa1_lightgbm, pa1_xgb, pa1_catboost, pa2_survival, pa3_isolation_forest, pa3_autoencoder_lstm, calibration}.py`
- `outputs/models/` com 24 modelos LightGBM (6 horizontes × 4 folds) + 6 modelos calibrados + 4 Cox PH + 4 Weibull AFT + 1 Isolation Forest + 1 Autoencoder LSTM
- `outputs/models/lgbm_best_params.json`
- 7 JSONs em `reports/eda_results/fase4{a,b,c,d,e,f,h}_*.json`
- 10 figuras `fig09..fig18*.png`
- `notebooks/04_modeling.ipynb` (canônico, 30+ cells executadas)
- `notebooks/_audit_fases_0_a_4.py` (auditoria estendida, deve passar 100%)
- `docs/article_dontgo/cap4_resultados.tex` parte 2 acrescida (~150 linhas adicionais)
- `MEMORY.md §13` (checkpoint completo da Fase 4 + handoff para Fase 5)
- `docs/decisions.md` com D033+ se houver decisões novas
- `PENDENCIAS.md` atualizada
- PDF recompilado (estimado 75-80 páginas)

## 13. Critérios de sucesso (resumo do plano)

A Fase 4 é declarada **fechada** quando:

1. Auditoria automatizada estendida (`_audit_fases_0_a_4.py`) passa 100%.
2. **PA-1 LightGBM**: lift ≥ 5× sobre prevalência em ≥ 4 horizontes; Recall@P=0,5 ≥ 0,3 em ≥ 3 horizontes; ECE pós-calibração ≤ 0,05.
3. **PA-2**: C-index ≥ 0,70 em junho.
4. **PA-3**: top-10% scores captura ≥ 50% dos 32 incidentes LeTourneau.
5. **SHAP** mostra top-5 features coerentes com hipóteses H002 (sequência), H009 (família), H011 (acumulação não-crítica).
6. **Drift**: PSI médio < 0,25 entre fold 4 → junho nas top-10 features OU registro formal da limitação no Cap. 5.
7. **Artigo**: Cap. 4 parte 2 escrita; PDF recompila sem erros.
8. **MEMORY §13** completo com handoff para Fase 5.

## 14. Pedido inicial

Confirme em uma linha que leu os documentos da seção 2 (especialmente `docs/plano_fase4.md` integralmente) e que entendeu o estado atual.

Em seguida, me diga **o que pretende fazer primeiro na Fase 4A** (splits walk-forward + baselines + pacote D012 de métricas), com os 3 entregáveis primários:

1. `src/eval/splits.py` — funções `make_walk_forward_folds(df, n_folds=4, buffer_h=4)` e `apply_censura_filter(df, horizon_h)`.
2. `src/eval/metrics.py` — pacote D012 (`auc_pr`, `lift`, `auc_roc`, `brier`, `ece`, `recall_at_precision`, `lead_time_p50`).
3. `notebooks/_baseline_pa1.py` — runner que produz `reports/eda_results/fase4a_baselines.json` com baseline 1 (regra heurística "qualquer Crítico nas últimas 4h") e baseline 2 (DummyClassifier estratificado), reportando o pacote D012 em cada um dos 6 horizontes × 4 folds.

Aguarde meu OK antes de criar arquivos. **Pause no checkpoint C1** (após 4A) antes de tocar em LightGBM/Optuna.
