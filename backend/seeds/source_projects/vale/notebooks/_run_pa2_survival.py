"""Runner Fase 4D — PA-2 sobrevivência (Cox PH + Weibull AFT) por fold.

Saídas
------
- ``outputs/models/cox_ph_fold{F}.joblib`` (4 modelos)
- ``outputs/models/weibull_aft_fold{F}.joblib`` (4 modelos)
- ``reports/eda_results/fase4d_pa2_survival.json``
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from src.utils.paths import PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import SEED, set_global_seed
from src.eval.splits import (
    apply_censura_filter,
    make_walk_forward_folds,
)
from src.models.pa2_survival import (
    build_survival_frame,
    cox_concordance_at_t,
    fit_cox,
    fit_weibull,
    integrated_brier_score,
    schoenfeld_summary,
    weibull_concordance,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
MODELS_DIR = PROJECT_ROOT / "outputs" / "models"
N_FOLDS = 4
BUFFER_H = 4

# Subamostragem para acelerar (CoxPH é O(n²) na amostra de treino).
MAX_TRAIN_SAMPLE = 30000
MAX_VAL_SAMPLE = 15000


def load_dataset_v2() -> pd.DataFrame:
    files = sorted(PROCESSED_DIR.glob("features_2025-*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["t_window"] = pd.to_datetime(df["t_window"])
    return df.sort_values("t_window").reset_index(drop=True)


def _subsample(df: pd.DataFrame, max_n: int, seed: int) -> pd.DataFrame:
    if len(df) <= max_n:
        return df
    return df.sample(n=max_n, random_state=seed).reset_index(drop=True)


def main() -> None:
    print("=" * 72)
    print("Fase 4D — PA-2 sobrevivência (Cox PH + Weibull AFT)")
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

    results: dict = {
        "config": {
            "n_folds": N_FOLDS,
            "buffer_h": BUFFER_H,
            "seed": SEED,
            "max_train_sample": MAX_TRAIN_SAMPLE,
            "max_val_sample": MAX_VAL_SAMPLE,
            "ibs_horizons_min": [60, 120, 240, 480, 720],
        },
        "folds": [],
        "holdout_jun": {},
    }

    for fold in folds:
        f = fold["fold"]
        print(f"\n[Fold {f}] train={fold['train_months']} val={fold['val_month']}")
        df_tr_full = df_cat.iloc[fold["train_idx"]].reset_index(drop=True)
        df_va_full = df_cat.iloc[fold["val_idx"]].reset_index(drop=True)
        df_tr = _subsample(df_tr_full, MAX_TRAIN_SAMPLE, SEED)
        df_va = _subsample(df_va_full, MAX_VAL_SAMPLE, SEED)

        Xt, Tt, Et, used = build_survival_frame(df_tr)
        Xv, Tv, Ev, _ = build_survival_frame(df_va, feature_cols=None)
        Xv = Xv.reindex(columns=Xt.columns, fill_value=0.0)

        print(f"  shape train: {Xt.shape}, val: {Xv.shape}")
        print(
            f"  events train: {int(Et.sum())} ({Et.mean() * 100:.1f}%) "
            f"| val: {int(Ev.sum())} ({Ev.mean() * 100:.1f}%)"
        )

        # Cox PH
        t0 = time.time()
        cph = fit_cox(Xt, Tt, Et, penalizer=0.05)
        cox_t = time.time() - t0
        c_train = cox_concordance_at_t(cph, Xt, Tt, Et)
        c_val = cox_concordance_at_t(cph, Xv, Tv, Ev)
        n_sub = min(5000, len(Xt))
        idx_sub = Xt.sample(n_sub, random_state=SEED).index
        sch = schoenfeld_summary(
            cph, Xt.loc[idx_sub], Tt.loc[idx_sub], Et.loc[idx_sub]
        )
        ibs = integrated_brier_score(cph, Xv, Tv, Ev)
        print(
            f"  CoxPH C-index train={c_train:.4f} val={c_val:.4f} "
            f"| Schoenfeld viol={sch.get('violation_ratio', 'NA')} "
            f"| IBS_avg={ibs['ibs_avg']:.4f} | {cox_t:.0f}s"
        )

        # Weibull AFT
        t0 = time.time()
        try:
            aft = fit_weibull(Xt, Tt, Et, penalizer=0.05)
            aft_t = time.time() - t0
            c_aft_val = weibull_concordance(aft, Xv, Tv, Ev)
            print(f"  Weibull AFT C-index val={c_aft_val:.4f} | {aft_t:.0f}s")
            joblib.dump(aft, MODELS_DIR / f"weibull_aft_fold{f}.joblib")
        except Exception as e:
            c_aft_val = float("nan")
            aft_t = 0.0
            print(f"  Weibull AFT falhou: {e}")

        joblib.dump(cph, MODELS_DIR / f"cox_ph_fold{f}.joblib")

        results["folds"].append(
            {
                "fold": f,
                "val_month": fold["val_month"],
                "n_train_subsample": int(len(Xt)),
                "n_val_subsample": int(len(Xv)),
                "n_features_after_onehot": int(Xt.shape[1]),
                "cox_ph": {
                    "c_index_train": round(c_train, 4),
                    "c_index_val": round(c_val, 4),
                    "schoenfeld": sch,
                    "ibs": ibs,
                    "elapsed_s": round(cox_t, 1),
                },
                "weibull_aft": {
                    "c_index_val": round(c_aft_val, 4)
                    if not np.isnan(c_aft_val)
                    else None,
                    "elapsed_s": round(aft_t, 1),
                },
            }
        )

    # Holdout junho
    print("\n[HOLDOUT JUN] treino jan-mai → eval jun")
    cutoff_train = pd.Timestamp("2025-06-01") - pd.Timedelta(hours=BUFFER_H)
    df_alltrain = df_cat[df_cat["t_window"] <= cutoff_train].reset_index(drop=True)
    df_alltrain = _subsample(df_alltrain, MAX_TRAIN_SAMPLE, SEED)
    df_jun = _subsample(holdout, MAX_VAL_SAMPLE, SEED)

    Xt, Tt, Et, _ = build_survival_frame(df_alltrain)
    Xv, Tv, Ev, _ = build_survival_frame(df_jun)
    Xv = Xv.reindex(columns=Xt.columns, fill_value=0.0)

    cph_full = fit_cox(Xt, Tt, Et, penalizer=0.05)
    c_jun_cox = cox_concordance_at_t(cph_full, Xv, Tv, Ev)
    ibs_jun = integrated_brier_score(cph_full, Xv, Tv, Ev)
    try:
        aft_full = fit_weibull(Xt, Tt, Et, penalizer=0.05)
        c_jun_aft = weibull_concordance(aft_full, Xv, Tv, Ev)
        joblib.dump(aft_full, MODELS_DIR / "weibull_aft_holdout_jun.joblib")
    except Exception as e:
        c_jun_aft = float("nan")
        print(f"  Weibull jun falhou: {e}")

    joblib.dump(cph_full, MODELS_DIR / "cox_ph_holdout_jun.joblib")

    print(f"  Cox PH jun C-index={c_jun_cox:.4f} | IBS_avg={ibs_jun['ibs_avg']:.4f}")
    if not np.isnan(c_jun_aft):
        print(f"  Weibull jun C-index={c_jun_aft:.4f}")

    results["holdout_jun"] = {
        "n_train_subsample": int(len(Xt)),
        "n_val_subsample": int(len(Xv)),
        "cox_ph": {"c_index": round(c_jun_cox, 4), "ibs": ibs_jun},
        "weibull_aft": {
            "c_index": round(c_jun_aft, 4) if not np.isnan(c_jun_aft) else None
        },
    }

    out_path = EDA_DIR / "fase4d_pa2_survival.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n→ {out_path.relative_to(PROJECT_ROOT)}")
    print("\nFase 4D concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
