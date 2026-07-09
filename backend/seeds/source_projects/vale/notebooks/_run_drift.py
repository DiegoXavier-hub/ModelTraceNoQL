"""Runner Fase 4H — análise de drift PSI/KS entre folds e fold4 → junho.

Saídas
------
- ``reports/eda_results/fase4h_drift.json``
- ``reports/figures/fig18_psi_heatmap.png``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.paths import PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import set_global_seed
from src.eval.splits import (
    apply_censura_filter,
    make_walk_forward_folds,
)
from src.eval.drift import drift_report

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
FIG_DIR = REPORTS_DIR / "figures"
N_FOLDS = 4
BUFFER_H = 4


def load_dataset_v2() -> pd.DataFrame:
    files = sorted(PROCESSED_DIR.glob("features_2025-*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["t_window"] = pd.to_datetime(df["t_window"])
    return df.sort_values("t_window").reset_index(drop=True)


def main() -> None:
    print("=" * 72)
    print("Fase 4H — Drift PSI / KS")
    print("=" * 72)
    set_global_seed()

    df = load_dataset_v2()
    df_cat = df[df["OEM"] == "Caterpillar"].copy()
    df_cat = apply_censura_filter(df_cat, horizon_h=12, kind="train").reset_index(
        drop=True
    )
    folds = make_walk_forward_folds(df_cat, n_folds=N_FOLDS, buffer_h=BUFFER_H)
    holdout = df[(df["mes_str"] == "2025-06") & (df["OEM"] == "Caterpillar")].copy()
    holdout = apply_censura_filter(holdout, horizon_h=12, kind="train").reset_index(
        drop=True
    )

    feature_cols = [c for c in df_cat.columns if c.startswith("n_")]
    print(f"\n{len(feature_cols)} features numéricas analisadas.")

    results: dict = {"folds": {}, "fold4_to_jun": {}, "summary": {}}

    # Drift treino_fold ↔ val_fold
    for fold in folds:
        f = fold["fold"]
        df_train = df_cat.iloc[fold["train_idx"]]
        df_val = df_cat.iloc[fold["val_idx"]]
        report = drift_report(df_train, df_val, feature_cols)
        psi_mean = float(report["psi"].mean())
        psi_top10_mean = float(report.head(10)["psi"].mean())
        n_severo = int((report["category"] == "severo").sum())
        results["folds"][f"fold{f}"] = {
            "val_month": fold["val_month"],
            "psi_mean": round(psi_mean, 5),
            "psi_top10_mean": round(psi_top10_mean, 5),
            "n_severo": n_severo,
            "top_15_psi": report.head(15).to_dict(orient="records"),
        }
        print(
            f"  Fold{f} (val={fold['val_month']}): PSI mean={psi_mean:.4f} "
            f"top10={psi_top10_mean:.4f} severo={n_severo}"
        )

    # Drift fold4 (treino jan-abr) ↔ holdout jun
    df_train_full = df_cat.iloc[folds[-1]["train_idx"]]
    rep_jun = drift_report(df_train_full, holdout, feature_cols)
    psi_mean_jun = float(rep_jun["psi"].mean())
    psi_top10_jun = float(rep_jun.head(10)["psi"].mean())
    n_severo_jun = int((rep_jun["category"] == "severo").sum())
    results["fold4_to_jun"] = {
        "psi_mean": round(psi_mean_jun, 5),
        "psi_top10_mean": round(psi_top10_jun, 5),
        "n_severo": n_severo_jun,
        "top_15_psi": rep_jun.head(15).to_dict(orient="records"),
    }
    print(
        f"\nFold4(treino jan-abr) → JUN: PSI mean={psi_mean_jun:.4f} "
        f"top10={psi_top10_jun:.4f} severo={n_severo_jun}"
    )

    # Summary against criterion
    crit_top10_jun = psi_top10_jun < 0.25
    results["summary"] = {
        "criterion_psi_top10_jun_lt_025": crit_top10_jun,
        "interpretation": (
            "PSI top10 < 0.25 confirma drift toleravel (alvo do plano)"
            if crit_top10_jun
            else "PSI top10 >= 0.25; documentar como limitacao no Cap. 5 (D027 + H010)"
        ),
    }
    print(f"\nCritério (PSI top10 jun < 0.25): {crit_top10_jun}")

    # Heatmap: features × folds
    top_features_overall = (
        rep_jun.head(20)["feature"].tolist()
    )  # top-20 features no drift jun
    rows = []
    for f in (1, 2, 3, 4):
        df_f = pd.DataFrame(results["folds"][f"fold{f}"]["top_15_psi"])
        for _, r in df_f.iterrows():
            if r["feature"] in top_features_overall:
                rows.append(
                    {"feature": r["feature"], "fold_or_jun": f"F{f}", "psi": r["psi"]}
                )
    for _, r in rep_jun.iterrows():
        if r["feature"] in top_features_overall:
            rows.append(
                {"feature": r["feature"], "fold_or_jun": "JUN", "psi": r["psi"]}
            )
    if rows:
        heatmap_df = pd.DataFrame(rows)
        pivot = (
            heatmap_df.pivot_table(index="feature", columns="fold_or_jun", values="psi")
            .reindex(top_features_overall)
            .fillna(0)
        )
        fig, ax = plt.subplots(figsize=(8, max(4, 0.3 * len(pivot))))
        im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=0.5)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=8)
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                v = pivot.values[i, j]
                ax.text(
                    j,
                    i,
                    f"{v:.2f}",
                    ha="center",
                    va="center",
                    color="black" if v < 0.25 else "white",
                    fontsize=7,
                )
        ax.set_title("PSI top-20 features × folds (treino vs val) e fold4 vs JUN")
        plt.colorbar(im, ax=ax, label="PSI")
        plt.tight_layout()
        fig_path = FIG_DIR / "fig18_psi_heatmap.png"
        plt.savefig(fig_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"\n→ {fig_path.relative_to(PROJECT_ROOT)}")

    out_path = EDA_DIR / "fase4h_drift.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"→ {out_path.relative_to(PROJECT_ROOT)}")
    print("\nFase 4H concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
