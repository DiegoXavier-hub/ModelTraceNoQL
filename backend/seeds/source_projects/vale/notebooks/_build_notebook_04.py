"""Gera o notebook canonico 04_modeling.ipynb consolidando a Fase 4.

Este notebook nao re-treina nada — apenas carrega artefatos persistidos
em outputs/models/ e reports/eda_results/ para narrativa.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_PATH = ROOT / "notebooks" / "04_modeling.ipynb"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def code(src: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": src.splitlines(keepends=True),
    }


cells: list[dict] = [
    md(
        "# Notebook 04 — Modelagem (Fase 4 / CM 4.1, 4.2, 4.3)\n\n"
        "**Princípio governante**: ROBUSTEZ > custo computacional.\n\n"
        "Este notebook consolida os artefatos da Fase 4 sem retreinar — todos os "
        "modelos foram serializados pelos runners em `notebooks/_run_*.py` e estão "
        "em `outputs/models/`; resultados em `reports/eda_results/fase4*.json`.\n\n"
        "## Estrutura\n\n"
        "1. Setup + carga\n"
        "2. Splits walk-forward (4A) + auditoria de buffer\n"
        "3. Baselines PA-1 (4A)\n"
        "4. PA-1 LightGBM (4B)\n"
        "5. Comparativo XGB/CatBoost (4C)\n"
        "6. PA-2 sobrevivência (4D)\n"
        "7. PA-3 anomalia LeTourneau (4E)\n"
        "8. Calibração (4F)\n"
        "9. SHAP (4G)\n"
        "10. Drift (4H)\n"
        "11. Resumo final\n"
    ),
    md("## 1. Setup + carga"),
    code(
        "import json, sys\n"
        "from pathlib import Path\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "from IPython.display import Image, display\n\n"
        "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
        "sys.path.insert(0, str(ROOT))\n"
        "EDA = ROOT / 'reports' / 'eda_results'\n"
        "FIG = ROOT / 'reports' / 'figures'\n"
        "MODELS = ROOT / 'outputs' / 'models'\n"
        "print('ROOT:', ROOT)\n"
    ),
    md("## 2. Splits walk-forward (4A) + auditoria de buffer\n\n"
       "Quatro folds expansivos jan→fev, jan-fev→mar, jan-mar→abr, jan-abr→mai. "
       "Junho é holdout intocado. Buffer 4h aplicado ao treino (D011)."),
    code(
        "splits = json.loads((EDA / 'fase4a_splits.json').read_text(encoding='utf-8'))\n"
        "audit = json.loads((EDA / 'fase4a_buffer_audit.json').read_text(encoding='utf-8'))\n"
        "print('Folds:')\n"
        "for f in splits['folds']:\n"
        "    print(f'  Fold {f[\"fold\"]}: train={f[\"train_months\"]} (n={f[\"n_train\"]:,}) | val={f[\"val_month\"]} (n={f[\"n_val\"]:,}) | prev_val_h12={f[\"prevalence_val_h12\"]:.4f}')\n"
        "print('\\nBuffer audit (medição A — val lookback recobre treino):')\n"
        "for m in audit['audit']['measurement_A_val_lookback_overlap']:\n"
        "    print(f'  Fold {m[\"fold\"]}: pct_overlap={m[\"pct_overlap\"]:.2f}% (max_overlap_min={m[\"max_overlap_minutes\"]:.1f})')\n"
    ),
    md("## 3. Baselines PA-1 (4A)\n\n"
       "B1 heurística \"qualquer Crítico nas últimas 4h\" + B2 DummyClassifier estratificado. "
       "Lift do baseline 1.13-1.42×. Recall@P=0.5 = 0 em todos horizontes."),
    code(
        "baselines = json.loads((EDA / 'fase4a_baselines.json').read_text(encoding='utf-8'))\n"
        "print('Resumo baseline 1 (assume_zero), agregado folds estáveis:')\n"
        "print(f'{\"H\":>4} | {\"AUC-PR\":>14} | {\"Lift\":>8} | {\"R@P=0.5\":>10}')\n"
        "for H in (1, 2, 4, 6, 8, 12):\n"
        "    a = baselines['horizons'][f'h{H}']['aggregate']['baseline1_assume_zero']['metrics_aggregate_stable_only']\n"
        "    rec = a['recall_at_p50']['mean']\n"
        "    if isinstance(rec, float) and np.isnan(rec): rec = 0.0\n"
        "    print(f'{H:>3}h | {a[\"auc_pr\"][\"mean\"]:>5.3f} ± {a[\"auc_pr\"][\"std\"]:.3f} | {a[\"lift\"][\"mean\"]:>8.2f} | {rec:>10.4f}')\n"
    ),
    md("## 4. PA-1 LightGBM (4B)\n\n"
       "150 trials Optuna por horizonte (D044). 24 modelos walk-forward + 6 holdout junho. "
       "Lift calibrado junho 6.71× a 2.11× (decai com horizonte = prevalência cresce)."),
    code(
        "lgbm = json.loads((EDA / 'fase4b_pa1_lightgbm.json').read_text(encoding='utf-8'))\n"
        "print(f'{\"H\":>4} | {\"WF AUC-PR\":>14} | {\"WF Lift\":>10} | {\"JUN AUC-PR\":>12} | {\"JUN Lift\":>10} | {\"JUN R@P50\":>10} | {\"JUN ECE\":>10}')\n"
        "for H in (1, 2, 4, 6, 8, 12):\n"
        "    r = lgbm['horizons'][f'h{H}']\n"
        "    wf = r['aggregate_walk_forward']\n"
        "    j = r['holdout_jun']['metrics']\n"
        "    rec = j['recall_at_p50']\n"
        "    if isinstance(rec, float) and np.isnan(rec): rec = 0.0\n"
        "    print(f'{H:>3}h | {wf[\"auc_pr\"][\"mean\"]:>5.3f} ± {wf[\"auc_pr\"][\"std\"]:.3f} | {wf[\"lift\"][\"mean\"]:>10.2f} | {j[\"auc_pr\"]:>12.4f} | {j[\"lift\"]:>10.2f} | {rec:>10.4f} | {j[\"ece\"]:>10.4f}')\n"
    ),
    code(
        "feat_imp = json.loads((EDA / 'fase4b_feature_importance.json').read_text(encoding='utf-8'))\n"
        "for H in (1, 4, 12):\n"
        "    print(f'\\nTop-10 features por gain — H={H}h (modelo holdout junho):')\n"
        "    for x in feat_imp[f'h{H}'][:10]:\n"
        "        print(f'  {x[\"feature\"]:>40}  gain={x[\"gain\"]:>14,.1f}')\n"
    ),
    md("## 5. Comparativo XGB/CatBoost (4C)\n\n"
       "Sem novo tuning — best_params do LightGBM traduzidos para os outros frameworks. "
       "XGB +0.5% a +12.4% sobre LGBM. CatBoost −1.6% a −8.6%. LightGBM mantido como primário."),
    code(
        "comp = json.loads((EDA / 'fase4c_pa1_comparativo.json').read_text(encoding='utf-8'))\n"
        "print(f'{\"H\":>4} | {\"LGBM JUN\":>10} | {\"XGB JUN\":>10} | {\"CB JUN\":>10}')\n"
        "for H in (1, 2, 4, 6, 8, 12):\n"
        "    lg = lgbm['horizons'][f'h{H}']['holdout_jun']['metrics']['auc_pr']\n"
        "    xg = comp['horizons'][f'h{H}']['xgboost']['holdout_jun']['metrics']['auc_pr']\n"
        "    cb = comp['horizons'][f'h{H}']['catboost']['holdout_jun']['metrics']['auc_pr']\n"
        "    print(f'{H:>3}h | {lg:>10.4f} | {xg:>10.4f} | {cb:>10.4f}')\n"
    ),
    md("## 6. PA-2 sobrevivência (4D)\n\n"
       "Cox PH + Weibull AFT (D017). Cox PH falhou Schoenfeld em folds 1 e 4 — "
       "C-index < 0.5 = inversão de ranking. Weibull AFT estável (0.62 em junho). "
       "**D035 — Weibull AFT como primário PA-2**."),
    code(
        "surv = json.loads((EDA / 'fase4d_pa2_survival.json').read_text(encoding='utf-8'))\n"
        "print('C-index por fold:')\n"
        "for f in surv['folds']:\n"
        "    aft = f['weibull_aft']['c_index_val']\n"
        "    print(f'  Fold {f[\"fold\"]} (val={f[\"val_month\"]}): Cox PH={f[\"cox_ph\"][\"c_index_val\"]} | Weibull AFT={aft}')\n"
        "print(f'\\nHoldout junho:')\n"
        "print(f'  Cox PH C-index = {surv[\"holdout_jun\"][\"cox_ph\"][\"c_index\"]} | IBS_avg = {surv[\"holdout_jun\"][\"cox_ph\"][\"ibs\"][\"ibs_avg\"]:.4f}')\n"
        "print(f'  Weibull AFT C-index = {surv[\"holdout_jun\"][\"weibull_aft\"][\"c_index\"]}')\n"
    ),
    md("## 7. PA-3 anomalia LeTourneau (4E)\n\n"
       "Isolation Forest + Autoencoder LSTM. Top-10% capture: IF=6.0%, LSTM=4.4%. "
       "**D036 — PA-3 declarado exploratório** (alvo 50% não atingido). "
       "Recomendação: tela de monitoramento, não gatilho."),
    code(
        "pa3 = json.loads((EDA / 'fase4e_pa3_anomaly.json').read_text(encoding='utf-8'))\n"
        "print('Isolation Forest:')\n"
        "for k, v in pa3['isolation_forest']['capture'].items():\n"
        "    print(f'  {k}: {v[\"captured\"]}/{v[\"total\"]} ({v[\"pct_captured\"]:.1f}%) | precision={v[\"precision\"]:.4f}%')\n"
        "if 'capture' in pa3.get('autoencoder_lstm', {}):\n"
        "    print('\\nAutoencoder LSTM:')\n"
        "    for k, v in pa3['autoencoder_lstm']['capture'].items():\n"
        "        print(f'  {k}: {v[\"captured\"]}/{v[\"total\"]} ({v[\"pct_captured\"]:.1f}%) | precision={v[\"precision\"]:.4f}%')\n"
    ),
    md("## 8. Calibração (4F)\n\n"
       "Platt + Isotonic ajustados em fold4 val (mai). ECE pós-calibração ≤ 0.026 em "
       "**TODOS** os 6 horizontes (alvo era ≤ 0.05). **D037 — política mista**: "
       "Isotonic em H ≤ 4h, Platt em H ≥ 6h."),
    code(
        "cal = json.loads((EDA / 'fase4f_calibration.json').read_text(encoding='utf-8'))\n"
        "print(f'{\"H\":>4} | {\"escolhido\":>10} | {\"Brier pré\":>10} | {\"Brier pós\":>10} | {\"ECE pré\":>10} | {\"ECE pós\":>10}')\n"
        "for H in (1, 2, 4, 6, 8, 12):\n"
        "    h = cal['horizons'][f'h{H}']\n"
        "    chosen = h['chosen_method']\n"
        "    pre, post = h['metrics_pre'], h[f'metrics_post_{chosen}']\n"
        "    print(f'{H:>3}h | {chosen:>10} | {pre[\"brier\"]:>10.4f} | {post[\"brier\"]:>10.4f} | {pre[\"ece\"]:>10.4f} | {post[\"ece\"]:>10.4f}')\n"
        "display(Image(filename=str(FIG / 'fig14_calibration_curves.png')))\n"
    ),
    md("## 9. SHAP (4G)\n\n"
       "Top features alinhadas com H002 (sequência), H009 (família funcional), "
       "H011 (acumulação não-crítica). Engine_Coolant é dominante em H ≥ 4h, "
       "consistente com o exemplo Don't Go original (5 disparos em 6 min)."),
    code(
        "shap_data = json.loads((EDA / 'fase4g_shap.json').read_text(encoding='utf-8'))\n"
        "for H in (1, 4, 12):\n"
        "    print(f'\\nTop-10 SHAP — H={H}h:')\n"
        "    for x in shap_data['horizons'][f'h{H}']['top_15_by_mean_abs_shap'][:10]:\n"
        "        print(f'  {x[\"feature\"]:>40}  mean|shap|={x[\"mean_abs_shap\"]:>8.4f}')\n"
    ),
    code(
        "for H in (1, 4, 12):\n"
        "    print(f'SHAP summary — H={H}h:')\n"
        "    display(Image(filename=str(FIG / f'fig15_shap_summary_h{H}.png')))\n"
        "print('\\nWaterfall em 5 casos representativos (H=4h):')\n"
        "display(Image(filename=str(FIG / 'fig16_shap_waterfall_5incidentes.png')))\n"
    ),
    md("## 10. Drift PSI/KS (4H)\n\n"
       "PSI mean fold4→jun = 0.05; PSI top-10 = 0.16 < 0.25 (D034 normaliza H010). "
       "Insight: prevalência caiu 72.5% (H010), mas distribuições de features são estáveis. "
       "Sugere mudança operacional, não degradação física do equipamento."),
    code(
        "drift = json.loads((EDA / 'fase4h_drift.json').read_text(encoding='utf-8'))\n"
        "print('PSI por fold (treino → val):')\n"
        "for f in (1, 2, 3, 4):\n"
        "    d = drift['folds'][f'fold{f}']\n"
        "    print(f'  Fold {f} (val={d[\"val_month\"]}): PSI mean={d[\"psi_mean\"]:.4f} | top10={d[\"psi_top10_mean\"]:.4f} | n_severo={d[\"n_severo\"]}')\n"
        "j = drift['fold4_to_jun']\n"
        "print(f'\\nFold4 → JUN: PSI mean={j[\"psi_mean\"]:.4f} | top10={j[\"psi_top10_mean\"]:.4f} | n_severo={j[\"n_severo\"]}')\n"
        "display(Image(filename=str(FIG / 'fig18_psi_heatmap.png')))\n"
    ),
    md("## 11. Resumo final — Fase 4 fechada\n\n"
       "| Critério do plano | Status |\n"
       "|---|---|\n"
       "| Auditoria 0-4 passa 100% (`_audit_fases_0_a_4.py`) | ✅ 51/51 |\n"
       "| PA-1 lift ≥ 5× em ≥ 4 horizontes | ⚠️ Em junho só H1, H2; em walk-forward 5/6 |\n"
       "| PA-1 Recall@P=0.5 ≥ 0.3 em ≥ 3 horizontes | ⚠️ Em junho só H12h; em walk-forward 5/6 |\n"
       "| PA-1 ECE ≤ 0.05 pós-calibração | ✅ Todos ≤ 0.026 |\n"
       "| PA-2 C-index ≥ 0.70 em junho | ❌ Weibull 0.62 (limitação) |\n"
       "| PA-3 top-10% captura ≥ 50% | ❌ 6% (PA-3 exploratório, D036) |\n"
       "| SHAP coerente H002/H009/H011 | ✅ |\n"
       "| Drift PSI < 0.25 fold4→jun | ✅ 0.16 |\n\n"
       "**6 decisões D033-D038** registradas em `docs/decisions.md`. "
       "**Checkpoint completo** em `MEMORY.md §13`. "
       "**Próxima fase**: 5 (Evaluation) — análise de erros + tradução técnica → impacto operacional."
       ),
]


nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.13.7",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT_PATH.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Notebook gerado: {OUT_PATH.relative_to(ROOT)} ({len(cells)} cells)")
