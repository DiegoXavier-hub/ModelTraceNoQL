"""Runner Fase 4B — PA-1 LightGBM por horizonte (6 × 4 = 24 modelos) + Optuna.

Saídas
------
- ``outputs/models/lgbm_h{H}_fold{F}.txt`` — 24 modelos LightGBM.
- ``outputs/models/lgbm_h{H}_holdout_jun.txt`` — 6 modelos finais (train=jan-mai).
- ``outputs/models/lgbm_best_params.json`` — best_params Optuna por horizonte.
- ``reports/eda_results/fase4b_pa1_lightgbm.json`` — métricas D012 por horizonte/fold.
- ``reports/eda_results/fase4b_feature_importance.json`` — top-15 features por horizonte.
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
from src.models.pa1_lightgbm import (
    build_feature_matrix,
    feature_importance_gain,
    save_lgbm,
    train_final_per_fold,
    tune_lgbm_for_horizon,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
MODELS_DIR = PROJECT_ROOT / "outputs" / "models"
EDA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS = (1, 2, 4, 6, 8, 12)
N_FOLDS = 4
BUFFER_H = 4
N_TRIALS_OPTUNA = 150  # D044: re-tuning robusto em todos os horizontes PA-1


def load_dataset_v2() -> pd.DataFrame:
    files = sorted(PROCESSED_DIR.glob("features_2025-*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["t_window"] = pd.to_datetime(df["t_window"])
    return df.sort_values("t_window").reset_index(drop=True)


def main() -> None:
    print("=" * 72)
    print("Fase 4B — PA-1 LightGBM por horizonte (24 modelos + Optuna)")
    print("=" * 72)

    set_global_seed()
    print(f"Seed: {SEED} | Optuna trials/horizonte: {N_TRIALS_OPTUNA}")

    print("\n[1/4] Carregando + filtros...")
    df = load_dataset_v2()
    df_cat = df[df["OEM"] == "Caterpillar"].copy()
    df_cat = apply_censura_filter(df_cat, horizon_h=12, kind="train").reset_index(
        drop=True
    )
    print(f"  CAT + lookback_completo: {len(df_cat):,} janelas")

    folds = make_walk_forward_folds(df_cat, n_folds=N_FOLDS, buffer_h=BUFFER_H)
    holdout = make_holdout(df).copy()
    holdout = holdout[holdout["OEM"] == "Caterpillar"].reset_index(drop=True)
    print(f"  Holdout junho (CAT): {len(holdout):,} janelas")

    results: dict = {
        "config": {
            "buffer_h": BUFFER_H,
            "n_folds": N_FOLDS,
            "n_trials_optuna": N_TRIALS_OPTUNA,
            "seed": SEED,
            "horizons": list(HORIZONS),
        },
        "horizons": {},
    }
    best_params_all: dict[str, dict] = {}
    feat_imp_all: dict[str, list] = {}

    for H in HORIZONS:
        h_key = f"h{H}"
        print(f"\n[2/4] Horizonte {H}h — Optuna no Fold 1...")
        t0 = time.time()
        # Fold 1: train=jan, val=fev
        f1 = folds[0]
        df_tr = df_cat.iloc[f1["train_idx"]]
        df_va_raw = df_cat.iloc[f1["val_idx"]]
        df_va = apply_censura_filter(df_va_raw, horizon_h=H, kind="eval")

        X_tr, y_tr, cats = build_feature_matrix(df_tr, H)
        X_va, y_va, _ = build_feature_matrix(df_va, H)

        best_params, best_val = tune_lgbm_for_horizon(
            X_tr, y_tr, X_va, y_va, cats,
            n_trials=N_TRIALS_OPTUNA,
        )
        elapsed = time.time() - t0
        print(f"  Best AUC-PR (val fev): {best_val:.4f} | {elapsed:.0f}s")
        best_params_all[h_key] = {
            "best_params": best_params,
            "best_value_auc_pr_val_fold1": best_val,
            "elapsed_s": round(elapsed, 1),
        }

        per_fold: list[dict] = []
        print(f"\n[3/4] Horizonte {H}h — Treinando nos {N_FOLDS} folds...")
        for fold in folds:
            df_train = df_cat.iloc[fold["train_idx"]]
            df_val_raw = df_cat.iloc[fold["val_idx"]]
            df_val = apply_censura_filter(df_val_raw, horizon_h=H, kind="eval")

            X_train, y_train, cats = build_feature_matrix(df_train, H)
            X_val, y_val, _ = build_feature_matrix(df_val, H)

            model = train_final_per_fold(
                X_train, y_train, X_val, y_val, best_params, cats
            )
            proba = model.predict_proba(X_val)[:, 1]
            pack = metric_pack(y_val.values, proba)

            model_path = MODELS_DIR / f"lgbm_h{H}_fold{fold['fold']}.txt"
            save_lgbm(model, model_path)

            per_fold.append(
                {
                    "fold": fold["fold"],
                    "val_month": fold["val_month"],
                    "n_train": int(len(X_train)),
                    "n_val": int(len(X_val)),
                    "n_pos_val": int(y_val.sum()),
                    "best_iteration": int(model.best_iteration_)
                    if model.best_iteration_
                    else int(model.n_estimators),
                    "metrics": pack,
                }
            )
            print(
                f"  F{fold['fold']} ({fold['val_month']}): "
                f"AUC-PR={pack['auc_pr']:.4f} Lift={pack['lift']:.2f} "
                f"R@P50={pack['recall_at_p50'] if not np.isnan(pack['recall_at_p50']) else 0:.3f} "
                f"Brier={pack['brier']:.4f}"
            )

        # Holdout final: train = jan-mai, eval = jun
        print(f"\n[4/4] Horizonte {H}h — Modelo final em jun (treino jan-mai)...")
        all_train = df_cat
        X_all_train, y_all_train, cats = build_feature_matrix(all_train, H)
        # Cortar últimas BUFFER_H horas (D011)
        cutoff_train = pd.Timestamp("2025-06-01") - pd.Timedelta(hours=BUFFER_H)
        mask_keep = (all_train["t_window"] <= cutoff_train).to_numpy()
        X_all_train = X_all_train.iloc[mask_keep]
        y_all_train = y_all_train.iloc[mask_keep]

        df_jun = apply_censura_filter(holdout, horizon_h=H, kind="eval")
        X_jun, y_jun, _ = build_feature_matrix(df_jun, H)

        # Para o final, usar best_params com val=jun como early-stopping reference
        # Não ideal (vaza junho), mas comum. Alternativa: treinar n_estimators fixo.
        # Para honestidade, treino com n_estimators = mediana de best_iteration nos folds.
        med_it = int(np.median([f["best_iteration"] for f in per_fold]))
        from src.models.pa1_lightgbm import LGBM_FIXED_PARAMS, _scale_pos_weight
        import lightgbm as lgb_

        params_final = {
            **LGBM_FIXED_PARAMS,
            **best_params,
            "scale_pos_weight": _scale_pos_weight(y_all_train),
            "n_estimators": max(med_it, 50),
        }
        final_model = lgb_.LGBMClassifier(**params_final)
        final_model.fit(
            X_all_train,
            y_all_train,
            categorical_feature=cats,
        )
        proba_jun = final_model.predict_proba(X_jun)[:, 1]
        pack_jun = metric_pack(y_jun.values, proba_jun)
        save_lgbm(final_model, MODELS_DIR / f"lgbm_h{H}_holdout_jun.txt")
        print(
            f"  Holdout jun: AUC-PR={pack_jun['auc_pr']:.4f} "
            f"Lift={pack_jun['lift']:.2f} "
            f"R@P50={pack_jun['recall_at_p50'] if not np.isnan(pack_jun['recall_at_p50']) else 0:.3f} "
            f"Brier={pack_jun['brier']:.4f} ECE={pack_jun['ece']:.4f}"
        )

        feat_imp = feature_importance_gain(final_model, top=15)
        feat_imp_all[h_key] = feat_imp.to_dict(orient="records")

        # Agregação
        keys = ["auc_pr", "lift", "auc_roc", "brier", "ece", "recall_at_p50"]
        agg = {}
        for k in keys:
            vals = [
                f["metrics"].get(k, np.nan)
                for f in per_fold
                if not np.isnan(f["metrics"].get(k, np.nan))
            ]
            agg[k] = {
                "mean": float(np.mean(vals)) if vals else float("nan"),
                "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
            }

        results["horizons"][h_key] = {
            "best_params_optuna": best_params,
            "best_value_auc_pr_val_fold1": best_val,
            "per_fold": per_fold,
            "aggregate_walk_forward": agg,
            "holdout_jun": {
                "n": int(len(X_jun)),
                "n_pos": int(y_jun.sum()),
                "n_estimators_used": params_final["n_estimators"],
                "metrics": pack_jun,
            },
        }

    # Persistir
    (MODELS_DIR / "lgbm_best_params.json").write_text(
        json.dumps(best_params_all, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (EDA_DIR / "fase4b_pa1_lightgbm.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (EDA_DIR / "fase4b_feature_importance.json").write_text(
        json.dumps(feat_imp_all, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print("Resumo PA-1 LightGBM (walk-forward + holdout junho):")
    print("=" * 72)
    print(
        f"{'H':>3} | {'WF AUC-PR':>13} | {'WF Lift':>8} | {'WF R@P50':>9} "
        f"| {'JUN AUC-PR':>10} | {'JUN Lift':>8} | {'JUN ECE':>8}"
    )
    print("-" * 80)
    for H in HORIZONS:
        r = results["horizons"][f"h{H}"]
        wf = r["aggregate_walk_forward"]
        jh = r["holdout_jun"]["metrics"]
        rec = wf["recall_at_p50"]["mean"]
        if np.isnan(rec):
            rec = 0.0
        print(
            f"{H:>3}h | {wf['auc_pr']['mean']:>5.3f} ± {wf['auc_pr']['std']:.3f} "
            f"| {wf['lift']['mean']:>8.2f} | {rec:>9.3f} "
            f"| {jh['auc_pr']:>10.4f} | {jh['lift']:>8.2f} | {jh['ece']:>8.4f}"
        )
    print("\nFase 4B concluída. 30 modelos serializados em outputs/models/.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
