# Antecipação de Alertas Críticos "Don't Go" em Frotas de Mineração

Projeto de Análise Avançada de Dados — Estudo Guiado.
Autor: **Diego Henrique Xavier** — UFU/FAGEN/Gestão da Informação — 2026.

## 📌 Ponto de entrada

> **Leia [`MEMORY.md`](./MEMORY.md) primeiro.** Ele é o caderno de bordo vivo do projeto:
> contém o protocolo de handoff, caminhos absolutos, roadmap completo, decisões e o
> checkpoint da última sessão.

## Status atual (2026-05-12)

| Fase | Status | Entrega |
|---|---|---|
| 0 — Setup | ✅ | Estrutura, `requirements.txt`, `src/utils/{paths,seeds}` |
| 1 — Business Understanding | ✅ v2 | `docs/business_understanding.md`, D001-D017 |
| 2 — Data Understanding (EDA) | ✅ + auditoria | 9 figuras + 5 JSONs em `reports/eda_results/` |
| 3 — Data Preparation | ✅ + auditoria | `data/processed/features_*.parquet` (321.500 janelas, 89 colunas) |
| **4 — Modeling** | **✅** | **30 LightGBM + 8 sobrevivência + 1 IF + 1 LSTM AE + 6 calibradores** |
| 5 — Evaluation | ✅ + auditoria | Análise de erros + tradução operacional |
| 6 — Conclusão | ✅ + auditoria | Cap. 5 + 6 do TCC, model card, bootstrap, fairness |

**Auditoria automatizada Fases 0-6**: `notebooks/_audit_fases_0_a_6.py` → 84/84 PASSA.
**Decisões formais**: D001-D044 em `docs/decisions.md`.
**TCC**: fonte LaTeX em `docs/article_dontgo/`, atualizado para a retunagem Optuna D044.

## Resultados-chave da Fase 4 (PA-1 LightGBM, holdout junho 2025)

| H | AUC-PR | Lift | Recall@P=0,5 | Brier (pré) | ECE pós-cal |
|---:|---:|---:|---:|---:|---:|
| 1h | 0,221 | **7,14×** | 0,118 | 0,048 | **0,010** |
| 2h | 0,284 | **5,34×** | 0,160 | 0,085 | **0,022** |
| 4h | 0,328 | 3,67× | 0,189 | 0,099 | **0,046** |
| 6h | 0,357 | 2,94× | 0,210 | 0,134 | **0,023** |
| 8h | 0,374 | 2,53× | 0,258 | 0,153 | **0,015** |
| 12h | 0,412 | 2,11× | 0,288 | 0,173 | **0,027** |

- **Optuna**: 150 trials por horizonte (D044), aplicado a todos os 6 modelos PA-1.
- **Calibração**: ECE ≤ 0,046 em **todos** os 6 horizontes pós-calibração (alvo do plano: ≥ 4 horizontes com ECE ≤ 0,05).
- **PA-2 sobrevivência (Weibull AFT)**: C-index 0,62 em junho.
- **PA-3 anomalia LeTourneau**: declarado exploratório (top-10% capture = 6%).
- **Drift PSI top-10 fold4→jun**: 0,16 (< 0,25, sem features severas).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `Base de Dados/` | Dados brutos (parquet + xlsx), regras de alarme, dicionário |
| `data/processed/` | Dataset v2 corrigido (6 parquets mensais) + limiares P99 calibrados |
| `notebooks/` | Notebooks numerados por fase CRISP-DM (02..04) + runners `_run_*.py` |
| `src/data/` | `loaders`, `mappings`, `cleaning`, `incidents`, `coverage` |
| `src/features/` | `families`, `builders`, `outlier_calibration` |
| `src/eval/` | `splits`, `metrics`, `drift` (Fase 4) |
| `src/models/` | `pa1_lightgbm`, `pa1_xgb`, `pa1_catboost`, `pa2_survival`, `pa3_isolation_forest`, `pa3_autoencoder_lstm`, `calibration` |
| `src/utils/` | `paths`, `seeds` |
| `reports/figures/` | Figuras finais para o `.tex` ABNT (~18 figuras) |
| `reports/eda_results/` | JSONs canônicos de cada sub-fase |
| `outputs/models/` | Modelos serializados (`.txt` LightGBM, `.joblib` sklearn/lifelines, `.pt` PyTorch) |
| `docs/decisions.md` | Controle de alterações ANTES → DEPOIS (D001-D044) |
| `docs/hypotheses.md` | 17 hipóteses (H001-H017) com status |
| `docs/features.md` | Catálogo do schema do dataset v2 |
| `docs/plano_fase4.md` | Plano detalhado executado |
| `docs/article_dontgo/` | TCC LaTeX/ABNT (`TCC_DontGo.tex` + capítulos + `bibliografia.bib`) |

## Como reproduzir

```bash
# 1) Calibrar limiares P99 (Fase 3 — uma vez antes do build)
python -m src.features.outlier_calibration

# 2) Materializar dataset v2 de features
python notebooks/_build_features_dataset.py

# 3) Fase 4A — splits + baselines
python notebooks/_baseline_pa1.py

# 4) Fase 4B — PA-1 LightGBM com Optuna (150 trials/horizonte; 30 modelos)
python notebooks/_run_pa1_lightgbm.py

# 5) Fase 4C — XGBoost + CatBoost comparativo
python notebooks/_run_pa1_comparativo.py

# 6) Fase 4D — PA-2 sobrevivência
python notebooks/_run_pa2_survival.py

# 7) Fase 4E — PA-3 anomalia LeTourneau
python notebooks/_run_pa3_anomaly.py

# 8) Fase 4F — calibração Platt/Isotonic
python notebooks/_run_calibration.py

# 9) Fase 4G — SHAP
python notebooks/_run_shap.py

# 10) Fase 4H — drift PSI/KS
python notebooks/_run_drift.py

# 11) Auditoria estendida (Fases 0-4)
python notebooks/_audit_fases_0_a_4.py

# 12) Recompilar TCC PDF
cd docs/article_dontgo
pdflatex TCC_DontGo.tex && biber TCC_DontGo && pdflatex TCC_DontGo.tex && pdflatex TCC_DontGo.tex
```

## Entregável final

Relatório em **LaTeX (ABNT)** publicado em `docs/article_dontgo/` (raiz `TCC_DontGo.tex`,
PDF em `TCC_DontGo.pdf`, atualmente com 68 páginas). Preâmbulo e estilo de tabelas/figuras foram
reaproveitados do TCC anterior do autor (`D:\TCC - versão final\article\TCC_Evasao.tex`),
mas o entregável atual vive integralmente neste repositório.

## Princípio governante

> **ROBUSTEZ > custo computacional.** Em todo dilema rigor-vs-velocidade, escolher rigor.
