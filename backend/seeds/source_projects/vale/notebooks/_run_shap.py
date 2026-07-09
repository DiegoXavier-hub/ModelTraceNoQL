"""Runner Fase 4G — SHAP global + waterfall em incidentes representativos.

Saídas
------
- ``reports/figures/fig15_shap_summary_h{1,4,12}.png`` (3 figuras)
- ``reports/figures/fig16_shap_waterfall_5incidentes.png``
- ``reports/eda_results/fase4g_shap.json`` — top-15 features por horizonte.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.paths import PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import SEED, set_global_seed
from src.eval.splits import apply_censura_filter
from src.models.pa1_lightgbm import build_feature_matrix

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
FIG_DIR = REPORTS_DIR / "figures"
MODELS_DIR = PROJECT_ROOT / "outputs" / "models"


def load_dataset_v2_jun() -> pd.DataFrame:
    files = sorted(PROCESSED_DIR.glob("features_2025-*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["t_window"] = pd.to_datetime(df["t_window"])
    df = df[(df["mes_str"] == "2025-06") & (df["OEM"] == "Caterpillar")].copy()
    return df.reset_index(drop=True)


def main() -> None:
    print("=" * 72)
    print("Fase 4G — SHAP (global + waterfall)")
    print("=" * 72)
    set_global_seed()

    df_jun = load_dataset_v2_jun()
    print(f"Junho CAT: {len(df_jun):,} janelas")

    summary_horizons = (1, 4, 12)
    results: dict = {"horizons": {}, "waterfall_5_cases": []}

    # Sample para acelerar SHAP global (suficiente para summary)
    SAMPLE_N = 5000
    rng = np.random.default_rng(SEED)

    for H in summary_horizons:
        h_key = f"h{H}"
        booster = lgb.Booster(
            model_file=str(MODELS_DIR / f"lgbm_h{H}_holdout_jun.txt")
        )
        df_eval = apply_censura_filter(df_jun, horizon_h=H, kind="eval")
        X, y, _ = build_feature_matrix(df_eval, H)

        if len(X) > SAMPLE_N:
            sample_idx = rng.choice(len(X), SAMPLE_N, replace=False)
            X_s = X.iloc[sample_idx]
        else:
            X_s = X

        explainer = shap.TreeExplainer(booster)
        shap_values = explainer.shap_values(X_s)
        # LightGBM binary: shape (n, n_features) ou list [class0, class1]
        if isinstance(shap_values, list):
            sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            sv = shap_values

        # Top-15 por |SHAP|
        mean_abs = np.abs(sv).mean(axis=0)
        feature_names = X_s.columns.tolist()
        order = np.argsort(mean_abs)[::-1]
        top = [
            {
                "feature": feature_names[idx],
                "mean_abs_shap": float(mean_abs[idx]),
            }
            for idx in order[:15]
        ]

        # Plot summary
        fig = plt.figure(figsize=(10, 8))
        shap.summary_plot(
            sv,
            X_s,
            feature_names=feature_names,
            max_display=15,
            show=False,
            plot_size=(10, 8),
        )
        plt.title(f"SHAP summary — horizonte {H}h (junho/2025)", fontsize=12)
        plt.tight_layout()
        fig_path = FIG_DIR / f"fig15_shap_summary_h{H}.png"
        plt.savefig(fig_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"  H{H}h: top-1={top[0]['feature']} top-2={top[1]['feature']} top-3={top[2]['feature']}")
        print(f"    → {fig_path.name}")

        results["horizons"][h_key] = {
            "n_evaluated": int(len(X_s)),
            "top_15_by_mean_abs_shap": top,
        }

    # Waterfall em 5 casos (H=4h por defeito — sweet spot operacional)
    print("\nWaterfall em 5 incidentes (H=4h)...")
    H = 4
    booster = lgb.Booster(model_file=str(MODELS_DIR / f"lgbm_h{H}_holdout_jun.txt"))
    df_eval = apply_censura_filter(df_jun, horizon_h=H, kind="eval")
    X_jun, y_jun, _ = build_feature_matrix(df_eval, H)
    proba = booster.predict(X_jun)

    # 5 casos: 2 TP curto (alta prob, y=1, lead curto); 1 TP longo; 1 FN; 1 FP
    df_eval2 = df_eval.copy()
    df_eval2["proba"] = proba
    df_eval2["y"] = y_jun.values
    df_eval2["lead"] = df_eval2["target_lead_time_min"]

    cases: list[tuple[str, int]] = []
    # TP curto: y=1 e lead pequeno e proba alta
    tp_short = df_eval2[
        (df_eval2["y"] == 1) & (df_eval2["lead"] < 60) & (df_eval2["proba"] > 0.5)
    ]
    if len(tp_short) > 0:
        cases.append(("TP_curto_<60min", int(tp_short["proba"].idxmax())))

    # TP longo: y=1 e lead grande e proba alta
    tp_long = df_eval2[
        (df_eval2["y"] == 1) & (df_eval2["lead"] >= 180) & (df_eval2["proba"] > 0.4)
    ]
    if len(tp_long) > 0:
        cases.append(("TP_longo_>=3h", int(tp_long["proba"].idxmax())))

    # FN: y=1 e proba baixa
    fn = df_eval2[(df_eval2["y"] == 1) & (df_eval2["proba"] < 0.1)]
    if len(fn) > 0:
        cases.append(("FN_baixa_proba", int(fn["proba"].idxmin())))

    # FP: y=0 e proba alta
    fp = df_eval2[(df_eval2["y"] == 0) & (df_eval2["proba"] > 0.7)]
    if len(fp) > 0:
        cases.append(("FP_alta_proba", int(fp["proba"].idxmax())))

    # Caso aleatório com proba mediana (~prevalência)
    mid = df_eval2[(df_eval2["proba"] > 0.1) & (df_eval2["proba"] < 0.3)]
    if len(mid) > 0:
        cases.append(("Borderline_~prev", int(mid.sample(1, random_state=SEED).index[0])))

    if cases:
        explainer = shap.TreeExplainer(booster)
        # Compute SHAP only for selected cases
        rows = X_jun.loc[[idx for _, idx in cases]]
        sv = explainer.shap_values(rows)
        if isinstance(sv, list):
            sv = sv[1] if len(sv) > 1 else sv[0]
        ev = explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            ev = float(ev[1] if len(np.atleast_1d(ev)) > 1 else ev[0])
        else:
            ev = float(ev)

        n_cases = len(cases)
        fig, axes = plt.subplots(n_cases, 1, figsize=(10, 4 * n_cases))
        if n_cases == 1:
            axes = [axes]
        for ax_i, ((label, idx), ax) in enumerate(zip(cases, axes)):
            row = rows.iloc[ax_i]
            sv_row = sv[ax_i]
            order_local = np.argsort(np.abs(sv_row))[::-1][:10]
            feat_names = [str(rows.columns[j]) for j in order_local]
            vals = sv_row[order_local]
            ax.barh(range(len(vals)), vals, color=["tab:red" if v > 0 else "tab:blue" for v in vals])
            ax.set_yticks(range(len(vals)))
            ax.set_yticklabels(feat_names, fontsize=8)
            ax.invert_yaxis()
            ax.axvline(0, color="k", linewidth=0.5)
            real_proba = float(df_eval2.loc[idx, "proba"])
            real_y = int(df_eval2.loc[idx, "y"])
            real_lead = df_eval2.loc[idx, "lead"]
            ax.set_title(
                f"{label}: proba={real_proba:.3f} y={real_y} lead={real_lead}",
                fontsize=10,
            )
            ax.set_xlabel("SHAP value")

            results["waterfall_5_cases"].append(
                {
                    "label": label,
                    "row_idx": idx,
                    "proba": real_proba,
                    "y_true": real_y,
                    "lead_time_min": float(real_lead) if not pd.isna(real_lead) else None,
                    "top_10_shap": [
                        {"feature": feat_names[k], "shap": float(vals[k])}
                        for k in range(len(vals))
                    ],
                }
            )
        plt.suptitle("Fase 4G — SHAP local em 5 casos representativos (H=4h, junho)", fontsize=12)
        plt.tight_layout()
        fig_path = FIG_DIR / "fig16_shap_waterfall_5incidentes.png"
        plt.savefig(fig_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"  → {fig_path.name}")

    out_path = EDA_DIR / "fase4g_shap.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n→ {out_path.relative_to(PROJECT_ROOT)}")
    print("\nFase 4G concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
