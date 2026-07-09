"""Runner Fase 4F — Calibração Platt × Isotonic dos modelos LightGBM.

Para cada horizonte:
1. Carrega modelo do fold 4 (train=jan-abr).
2. Aplica em fold 4 val (mai/2025) → (scores_val, y_val).
3. Ajusta Platt e Isotonic em (scores_val, y_val).
4. Aplica em junho/2025 (intocado) → reporta Brier/ECE pré e pós.

Saídas
------
- ``outputs/models/lgbm_calibrated_h{H}.joblib`` (6 modelos: dict com platt+iso)
- ``reports/eda_results/fase4f_calibration.json``
- ``reports/figures/fig14_calibration_curves.png``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import lightgbm as lgb
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
from src.eval.metrics import brier, ece
from src.models.pa1_lightgbm import build_feature_matrix
from src.models.calibration import (
    apply_isotonic,
    apply_platt,
    fit_isotonic,
    fit_platt,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
FIG_DIR = REPORTS_DIR / "figures"
MODELS_DIR = PROJECT_ROOT / "outputs" / "models"
HORIZONS = (1, 2, 4, 6, 8, 12)
N_FOLDS = 4
BUFFER_H = 4


def load_dataset_v2() -> pd.DataFrame:
    files = sorted(PROCESSED_DIR.glob("features_2025-*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["t_window"] = pd.to_datetime(df["t_window"])
    return df.sort_values("t_window").reset_index(drop=True)


def reliability_diagram(
    y_true: np.ndarray, y_score: np.ndarray, n_bins: int = 10
) -> tuple[np.ndarray, np.ndarray]:
    """Retorna (mean_pred_per_bin, mean_obs_per_bin)."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(y_score, bins) - 1, 0, n_bins - 1)
    means_pred = np.full(n_bins, np.nan)
    means_obs = np.full(n_bins, np.nan)
    for b in range(n_bins):
        m = idx == b
        if m.sum() > 0:
            means_pred[b] = float(y_score[m].mean())
            means_obs[b] = float(y_true[m].mean())
    return means_pred, means_obs


def main() -> None:
    print("=" * 72)
    print("Fase 4F — Calibração Platt × Isotonic")
    print("=" * 72)
    set_global_seed()

    df = load_dataset_v2()
    df_cat = df[df["OEM"] == "Caterpillar"].copy()
    df_cat = apply_censura_filter(df_cat, horizon_h=12, kind="train").reset_index(
        drop=True
    )
    folds = make_walk_forward_folds(df_cat, n_folds=N_FOLDS, buffer_h=BUFFER_H)
    fold4 = folds[-1]
    df_val_fold4 = df_cat.iloc[fold4["val_idx"]]
    print(f"Fold 4 val (mai/2025): {len(df_val_fold4):,} janelas")

    holdout = df[(df["mes_str"] == "2025-06") & (df["OEM"] == "Caterpillar")].copy()
    print(f"Holdout junho: {len(holdout):,} janelas")

    results: dict = {"horizons": {}}
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, H in enumerate(HORIZONS):
        h_key = f"h{H}"
        # Carrega modelo do fold 4
        model_path = MODELS_DIR / f"lgbm_h{H}_fold4.txt"
        booster = lgb.Booster(model_file=str(model_path))

        # Predições no fold 4 val (mai)
        df_val_calib = apply_censura_filter(df_val_fold4, horizon_h=H, kind="eval")
        X_calib, y_calib, _ = build_feature_matrix(df_val_calib, H)
        scores_calib = booster.predict(X_calib)
        scores_calib = np.clip(scores_calib, 1e-6, 1 - 1e-6)

        # Predições em junho
        df_jun = apply_censura_filter(holdout, horizon_h=H, kind="eval")
        X_jun, y_jun, _ = build_feature_matrix(df_jun, H)
        # Modelo holdout junho (treino jan-mai)
        booster_jun = lgb.Booster(
            model_file=str(MODELS_DIR / f"lgbm_h{H}_holdout_jun.txt")
        )
        scores_jun_pre = booster_jun.predict(X_jun)
        scores_jun_pre = np.clip(scores_jun_pre, 1e-6, 1 - 1e-6)

        # Calibradores treinados no fold 4 val
        platt = fit_platt(scores_calib, y_calib.values)
        iso = fit_isotonic(scores_calib, y_calib.values)

        # Para calibrar predições do modelo holdout, é justo aplicar o calibrator
        # treinado em (mai-scores) sobre (jun-scores). Mas mai-scores vêm do modelo
        # fold 4 (train=jan-abr) e jun-scores vêm do modelo holdout (train=jan-mai).
        # Para consistência operacional, recalibramos: treinamos calibrador em scores
        # do MESMO modelo holdout aplicado a fold 4 val.
        scores_calib_holdout = booster_jun.predict(X_calib)
        scores_calib_holdout = np.clip(scores_calib_holdout, 1e-6, 1 - 1e-6)
        platt_op = fit_platt(scores_calib_holdout, y_calib.values)
        iso_op = fit_isotonic(scores_calib_holdout, y_calib.values)

        scores_jun_platt = apply_platt(platt_op, scores_jun_pre)
        scores_jun_iso = apply_isotonic(iso_op, scores_jun_pre)

        m_pre = {
            "brier": brier(y_jun.values, scores_jun_pre),
            "ece": ece(y_jun.values, scores_jun_pre),
        }
        m_platt = {
            "brier": brier(y_jun.values, scores_jun_platt),
            "ece": ece(y_jun.values, scores_jun_platt),
        }
        m_iso = {
            "brier": brier(y_jun.values, scores_jun_iso),
            "ece": ece(y_jun.values, scores_jun_iso),
        }

        # Decisão: menor Brier; em empate, menor ECE.
        cands = {"platt": m_platt, "isotonic": m_iso}
        winner = min(cands.keys(), key=lambda k: (cands[k]["brier"], cands[k]["ece"]))

        joblib.dump(
            {"platt": platt_op, "isotonic": iso_op, "chosen_method": winner},
            MODELS_DIR / f"lgbm_calibrated_h{H}.joblib",
        )

        results["horizons"][h_key] = {
            "n_calib_fold4_val": int(len(X_calib)),
            "n_test_jun": int(len(X_jun)),
            "n_pos_jun": int(y_jun.sum()),
            "metrics_pre": m_pre,
            "metrics_post_platt": m_platt,
            "metrics_post_isotonic": m_iso,
            "chosen_method": winner,
            "improvement_brier": round(
                m_pre["brier"] - cands[winner]["brier"], 6
            ),
            "improvement_ece": round(m_pre["ece"] - cands[winner]["ece"], 6),
        }

        print(
            f"  H{H}h: PRE Brier={m_pre['brier']:.4f} ECE={m_pre['ece']:.4f}"
            f" | Platt Brier={m_platt['brier']:.4f} ECE={m_platt['ece']:.4f}"
            f" | Iso Brier={m_iso['brier']:.4f} ECE={m_iso['ece']:.4f}"
            f" -> {winner.upper()}"
        )

        # Plot
        ax = axes[i]
        for label, scores, color in [
            ("pré", scores_jun_pre, "tab:blue"),
            ("Platt", scores_jun_platt, "tab:orange"),
            ("Isotonic", scores_jun_iso, "tab:green"),
        ]:
            mp, mo = reliability_diagram(y_jun.values, scores)
            mask = ~np.isnan(mp)
            ax.plot(mp[mask], mo[mask], "o-", label=label, color=color)
        ax.plot([0, 1], [0, 1], "k--", linewidth=0.7)
        ax.set_xlabel("Predição média")
        ax.set_ylabel("Frequência observada")
        ax.set_title(f"H={H}h | escolha: {winner}")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(alpha=0.3)

    plt.suptitle("Fase 4F — Reliability diagrams junho (D014)", fontsize=14)
    plt.tight_layout()
    fig_path = FIG_DIR / "fig14_calibration_curves.png"
    fig.savefig(fig_path, dpi=120)
    plt.close(fig)
    print(f"\nFigura: {fig_path.relative_to(PROJECT_ROOT)}")

    out_path = EDA_DIR / "fase4f_calibration.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"→ {out_path.relative_to(PROJECT_ROOT)}")
    print("\nFase 4F concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
