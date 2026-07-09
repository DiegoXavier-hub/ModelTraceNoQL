"""Runner Fase 4C — Comparativo PA-1 LightGBM × XGBoost × CatBoost.

Reusa best_params do LightGBM (Fase 4B) — nenhum novo tuning. Treina XGB
e CatBoost com hiperparâmetros equivalentes nos 4 folds + holdout junho,
reportando o pacote D012 para comparação.

Saídas
------
- ``reports/eda_results/fase4c_pa1_comparativo.json``
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.paths import PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import SEED, set_global_seed
from src.eval.splits import (
    apply_censura_filter,
    make_holdout,
    make_walk_forward_folds,
)
from src.eval.metrics import metric_pack
from src.models.pa1_lightgbm import build_feature_matrix
from src.models.pa1_xgb import lgbm_params_to_xgb, train_xgb
from src.models.pa1_catboost import (
    _coerce_categoricals_to_str,
    lgbm_params_to_catboost,
    train_catboost,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
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


def main() -> None:
    print("=" * 72)
    print("Fase 4C — Comparativo LightGBM × XGBoost × CatBoost")
    print("=" * 72)

    set_global_seed()
    print("\n[1/3] Carregando dataset + best_params LightGBM...")
    df = load_dataset_v2()
    df_cat = df[df["OEM"] == "Caterpillar"].copy()
    df_cat = apply_censura_filter(df_cat, horizon_h=12, kind="train").reset_index(
        drop=True
    )
    folds = make_walk_forward_folds(df_cat, n_folds=N_FOLDS, buffer_h=BUFFER_H)
    holdout = df[(df["mes_str"] == "2025-06") & (df["OEM"] == "Caterpillar")].copy()

    best_params_path = MODELS_DIR / "lgbm_best_params.json"
    best_params_all = json.loads(best_params_path.read_text(encoding="utf-8"))

    results: dict = {
        "config": {
            "n_folds": N_FOLDS,
            "buffer_h": BUFFER_H,
            "seed": SEED,
            "horizons": list(HORIZONS),
        },
        "horizons": {},
    }

    print(f"\n[2/3] Treinando XGB e CatBoost para {len(HORIZONS)} horizontes...")
    for H in HORIZONS:
        h_key = f"h{H}"
        lgbm_bp = best_params_all[h_key]["best_params"]
        xgb_params = lgbm_params_to_xgb(lgbm_bp)
        cb_params = lgbm_params_to_catboost(lgbm_bp)
        print(f"\n  Horizonte {H}h:")

        per_fold_xgb: list[dict] = []
        per_fold_cb: list[dict] = []
        for fold in folds:
            df_train = df_cat.iloc[fold["train_idx"]]
            df_val_raw = df_cat.iloc[fold["val_idx"]]
            df_val = apply_censura_filter(df_val_raw, horizon_h=H, kind="eval")
            X_train, y_train, cats = build_feature_matrix(df_train, H)
            X_val, y_val, _ = build_feature_matrix(df_val, H)

            # XGBoost
            t0 = time.time()
            mxgb = train_xgb(
                X_train.copy(), y_train, X_val.copy(), y_val, cats, xgb_params
            )
            p_xgb = mxgb.predict_proba(X_val)[:, 1]
            pack_x = metric_pack(y_val.values, p_xgb)
            per_fold_xgb.append(
                {
                    "fold": fold["fold"],
                    "val_month": fold["val_month"],
                    "elapsed_s": round(time.time() - t0, 1),
                    "metrics": pack_x,
                }
            )

            # CatBoost
            t0 = time.time()
            mcb = train_catboost(X_train, y_train, X_val, y_val, cats, cb_params)
            X_val_cb = _coerce_categoricals_to_str(X_val, cats)
            p_cb = mcb.predict_proba(X_val_cb)[:, 1]
            pack_c = metric_pack(y_val.values, p_cb)
            per_fold_cb.append(
                {
                    "fold": fold["fold"],
                    "val_month": fold["val_month"],
                    "elapsed_s": round(time.time() - t0, 1),
                    "metrics": pack_c,
                }
            )
            print(
                f"    F{fold['fold']}: XGB AUC-PR={pack_x['auc_pr']:.4f} "
                f"| CB AUC-PR={pack_c['auc_pr']:.4f}"
            )

        # Holdout junho — treino jan-mai (com buffer) → eval jun
        cutoff_train = pd.Timestamp("2025-06-01") - pd.Timedelta(hours=BUFFER_H)
        all_train = df_cat[df_cat["t_window"] <= cutoff_train]
        X_all, y_all, cats = build_feature_matrix(all_train, H)
        df_jun = apply_censura_filter(holdout, horizon_h=H, kind="eval")
        X_jun, y_jun, _ = build_feature_matrix(df_jun, H)

        mxgb_full = train_xgb(
            X_all.copy(), y_all, X_jun.copy(), y_jun, cats, xgb_params
        )
        p_xgb_jun = mxgb_full.predict_proba(X_jun)[:, 1]
        pack_xgb_jun = metric_pack(y_jun.values, p_xgb_jun)

        mcb_full = train_catboost(X_all, y_all, X_jun, y_jun, cats, cb_params)
        X_jun_cb = _coerce_categoricals_to_str(X_jun, cats)
        p_cb_jun = mcb_full.predict_proba(X_jun_cb)[:, 1]
        pack_cb_jun = metric_pack(y_jun.values, p_cb_jun)

        # Agregação WF
        def _agg(per_fold: list[dict]) -> dict:
            keys = ["auc_pr", "lift", "auc_roc", "brier", "ece", "recall_at_p50"]
            out = {}
            for k in keys:
                vals = [
                    f["metrics"].get(k, np.nan)
                    for f in per_fold
                    if not np.isnan(f["metrics"].get(k, np.nan))
                ]
                out[k] = {
                    "mean": float(np.mean(vals)) if vals else float("nan"),
                    "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                }
            return out

        results["horizons"][h_key] = {
            "xgboost": {
                "per_fold": per_fold_xgb,
                "aggregate_walk_forward": _agg(per_fold_xgb),
                "holdout_jun": {
                    "n": int(len(X_jun)),
                    "n_pos": int(y_jun.sum()),
                    "metrics": pack_xgb_jun,
                },
            },
            "catboost": {
                "per_fold": per_fold_cb,
                "aggregate_walk_forward": _agg(per_fold_cb),
                "holdout_jun": {
                    "n": int(len(X_jun)),
                    "n_pos": int(y_jun.sum()),
                    "metrics": pack_cb_jun,
                },
            },
        }
        print(
            f"  HOLDOUT JUN — XGB AUC-PR={pack_xgb_jun['auc_pr']:.4f} "
            f"| CB AUC-PR={pack_cb_jun['auc_pr']:.4f}"
        )

    # Comparação com LightGBM (Fase 4B)
    print("\n[3/3] Comparação com LightGBM (Fase 4B)...")
    lgbm_results_path = EDA_DIR / "fase4b_pa1_lightgbm.json"
    lgbm_results = json.loads(lgbm_results_path.read_text(encoding="utf-8"))

    print("\n" + "=" * 80)
    print("Comparativo AUC-PR holdout junho:")
    print("=" * 80)
    print(
        f"{'H':>4} | {'LGBM':>8} | {'XGB':>8} | {'CB':>8} "
        f"| {'Δ XGB-LGBM (%)':>16} | {'Δ CB-LGBM (%)':>16}"
    )
    print("-" * 80)
    for H in HORIZONS:
        h_key = f"h{H}"
        lg = lgbm_results["horizons"][h_key]["holdout_jun"]["metrics"]["auc_pr"]
        xg = results["horizons"][h_key]["xgboost"]["holdout_jun"]["metrics"]["auc_pr"]
        cb = results["horizons"][h_key]["catboost"]["holdout_jun"]["metrics"]["auc_pr"]
        d_xg = 100 * (xg - lg) / lg
        d_cb = 100 * (cb - lg) / lg
        print(
            f"{H:>3}h | {lg:>8.4f} | {xg:>8.4f} | {cb:>8.4f} "
            f"| {d_xg:>+16.2f} | {d_cb:>+16.2f}"
        )
    out_path = EDA_DIR / "fase4c_pa1_comparativo.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n→ {out_path.relative_to(PROJECT_ROOT)}")
    print("\nFase 4C concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
