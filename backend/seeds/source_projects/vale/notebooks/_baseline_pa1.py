"""Runner Fase 4A — splits walk-forward + auditoria de buffer + baselines PA-1.

Saídas
------
- ``reports/eda_results/fase4a_splits.json`` — metadados dos folds.
- ``reports/eda_results/fase4a_buffer_audit.json`` — auditoria de overlap (Q1).
- ``reports/eda_results/fase4a_baselines.json`` — pacote D012 de baselines.

Reprodução
----------
    python notebooks/_baseline_pa1.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.paths import PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import SEED, set_global_seed
from src.eval.splits import (
    apply_censura_filter,
    audit_buffer_overlap,
    make_walk_forward_folds,
)
from src.eval.metrics import metric_pack

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
EDA_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS = (1, 2, 4, 6, 8, 12)
N_FOLDS = 4
BUFFER_H = 4
N_POS_THRESHOLD = 50  # fold com menos positivos é marcado como unstable


def load_dataset_v2() -> pd.DataFrame:
    files = sorted(PROCESSED_DIR.glob("features_2025-*.parquet"))
    if len(files) != 6:
        raise FileNotFoundError(
            f"Esperado 6 parquets em {PROCESSED_DIR}, encontrados {len(files)}"
        )
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["t_window"] = pd.to_datetime(df["t_window"])
    df = df.sort_values("t_window").reset_index(drop=True)
    return df


def baseline_heuristic_scores(
    df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """B1 — 'qualquer Crítico nas últimas 4h'.

    Retorna (assume_zero, strict, mask_strict) onde:
    - assume_zero: NaN → 0 (lógica operacional, comparável ao ML).
    - strict:    score em janelas com ``tem_telemetria=1`` (NaN propagado).
    - mask_strict: bool — janelas elegíveis para a versão estrita.
    """
    n_crit = df["n_crit_4h"]
    score_assume = (n_crit.fillna(0) > 0).astype(np.float64).to_numpy()
    has_tel = (df["tem_telemetria"] == 1).to_numpy()
    score_strict = np.where(has_tel, (n_crit.fillna(0) > 0).astype(float), np.nan)
    return score_assume, score_strict, has_tel


def baseline_dummy_scores(y_train: np.ndarray, n_val: int) -> np.ndarray:
    dummy = DummyClassifier(strategy="stratified", random_state=SEED)
    dummy.fit(np.zeros((len(y_train), 1)), y_train)
    proba = dummy.predict_proba(np.zeros((n_val, 1)))
    # Coluna 1 = classe positiva
    if proba.shape[1] == 2:
        return proba[:, 1]
    return np.full(n_val, float(y_train.mean()))


def evaluate_fold_horizon(
    df_train: pd.DataFrame,
    df_val: pd.DataFrame,
    horizon_h: int,
) -> dict:
    target_col = f"y_dontgo_{horizon_h}h"
    y_train = df_train[target_col].to_numpy()
    y_val = df_val[target_col].to_numpy()

    s_assume, s_strict, has_tel = baseline_heuristic_scores(df_val)

    pack_assume = metric_pack(y_val, s_assume)

    pack_strict = metric_pack(y_val[has_tel], s_strict[has_tel])
    pack_strict["n_excluded_no_telemetria"] = int((~has_tel).sum())

    s_dummy = baseline_dummy_scores(y_train, len(df_val))
    pack_dummy = metric_pack(y_val, s_dummy)

    n_pos = int(y_val.sum())
    return {
        "n_val": int(len(df_val)),
        "n_pos_val": n_pos,
        "prevalence_val": float(y_val.mean()) if len(y_val) > 0 else float("nan"),
        "unstable": int(n_pos < N_POS_THRESHOLD),
        "baseline1_assume_zero": pack_assume,
        "baseline1_strict_tem_telemetria": pack_strict,
        "baseline2_dummy_stratified": pack_dummy,
    }


def aggregate_metrics(per_fold: list[dict]) -> dict:
    """Agrega métricas com 2 visões (Q2): apenas estáveis vs todos."""
    keys = ["auc_pr", "lift", "auc_roc", "brier", "ece", "recall_at_p50"]
    baselines = [
        "baseline1_assume_zero",
        "baseline1_strict_tem_telemetria",
        "baseline2_dummy_stratified",
    ]

    def _agg(folds_subset: list[dict], baseline: str) -> dict:
        out: dict = {}
        for k in keys:
            vals = [
                f[baseline].get(k, float("nan"))
                for f in folds_subset
                if baseline in f
            ]
            vals = [
                v
                for v in vals
                if isinstance(v, (int, float)) and not np.isnan(v)
            ]
            if len(vals) == 0:
                out[k] = {"mean": float("nan"), "std": float("nan"), "n": 0}
            else:
                out[k] = {
                    "mean": float(np.mean(vals)),
                    "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                    "n": len(vals),
                }
        return out

    stable = [f for f in per_fold if f["unstable"] == 0]
    out: dict = {}
    for b in baselines:
        out[b] = {
            "n_folds_total": len(per_fold),
            "n_folds_stable_used": len(stable),
            "metrics_aggregate_stable_only": _agg(stable, b),
            "metrics_aggregate_all_folds": _agg(per_fold, b),
        }
    return out


def main() -> None:
    print("=" * 72)
    print("Fase 4A — Splits walk-forward + Baselines PA-1")
    print("=" * 72)

    info = set_global_seed()
    print(f"Seed: {info['seed']} | torch: {info.get('torch')}")

    print("\n[1/5] Carregando dataset v2...")
    df = load_dataset_v2()
    oem_counts = df["OEM"].value_counts().to_dict()
    print(f"  Total: {len(df):,} janelas / {len(df.columns)} colunas")
    print(f"  Por OEM: {oem_counts}")

    print("\n[2/5] Filtrando OEM=Caterpillar (D027) + lookback_completo=1 (D032)...")
    df_cat = df[df["OEM"] == "Caterpillar"].copy()
    df_cat = apply_censura_filter(df_cat, horizon_h=12, kind="train").reset_index(
        drop=True
    )
    print(f"  Após filtros: {len(df_cat):,} janelas")
    print(
        f"  Prevalência por horizonte: "
        + ", ".join(
            f"H{H}h={float(df_cat[f'y_dontgo_{H}h'].mean()):.4f}" for H in HORIZONS
        )
    )

    print(f"\n[3/5] Construindo {N_FOLDS} folds walk-forward (buffer={BUFFER_H}h)...")
    folds = make_walk_forward_folds(df_cat, n_folds=N_FOLDS, buffer_h=BUFFER_H)
    folds_meta = [
        {k: v for k, v in f.items() if k not in ("train_idx", "val_idx")}
        for f in folds
    ]
    for f in folds:
        print(
            f"  Fold {f['fold']}: train={f['train_months']} (n={f['n_train']:,}) "
            f"| val={f['val_month']} (n={f['n_val']:,}) "
            f"| prev_train_h12={f['prevalence_train_h12']:.4f} "
            f"prev_val_h12={f['prevalence_val_h12']:.4f}"
        )
    splits_path = EDA_DIR / "fase4a_splits.json"
    splits_path.write_text(
        json.dumps(
            {
                "config": {
                    "n_folds": N_FOLDS,
                    "buffer_h": BUFFER_H,
                    "oem_filter": "Caterpillar",
                    "censura_train": "lookback_completo=1 (D032)",
                },
                "n_total_after_filters": int(len(df_cat)),
                "folds": folds_meta,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"  → {splits_path.relative_to(PROJECT_ROOT)}")

    print("\n[4/5] Auditoria de buffer overlap (Q1)...")
    audit = audit_buffer_overlap(folds, df_cat)
    audit_path = EDA_DIR / "fase4a_buffer_audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "config": {
                    "buffer_h": BUFFER_H,
                    "lookback_h_max": 12,
                    "horizons": list(HORIZONS),
                    "criterio_revisao": "pct_overlap_A > 1% sugere D011-v2 com buffer=12h",
                },
                "audit": audit,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    max_pct_A = max(
        m["pct_overlap"] for m in audit["measurement_A_val_lookback_overlap"]
    )
    max_pct_B = max(m["pct_leak"] for m in audit["measurement_B_train_label_leak"])
    print(f"  → {audit_path.relative_to(PROJECT_ROOT)}")
    print(f"  Max pct_overlap (A — val lookback recobre treino): {max_pct_A:.2f}%")
    print(f"  Max pct_leak    (B — label do treino vaza no val): {max_pct_B:.2f}%")

    print(f"\n[5/5] Avaliando {len(HORIZONS)} horizontes × {N_FOLDS} folds...")
    results: dict = {
        "config": {
            "oem_filter": "Caterpillar",
            "n_folds": N_FOLDS,
            "buffer_h": BUFFER_H,
            "seed": SEED,
            "n_pos_threshold": N_POS_THRESHOLD,
            "horizons": list(HORIZONS),
        },
        "horizons": {},
    }
    for H in HORIZONS:
        per_fold: list[dict] = []
        for fold in folds:
            df_train = df_cat.iloc[fold["train_idx"]]
            df_val_raw = df_cat.iloc[fold["val_idx"]]
            df_val = apply_censura_filter(df_val_raw, horizon_h=H, kind="eval")
            res = evaluate_fold_horizon(df_train, df_val, H)
            res["fold"] = fold["fold"]
            res["val_month"] = fold["val_month"]
            res["n_val_after_censura"] = int(len(df_val))
            res["n_val_dropped_label_censura"] = int(len(df_val_raw) - len(df_val))
            per_fold.append(res)
            flag = " [UNSTABLE]" if res["unstable"] else ""
            print(
                f"  H{H}h F{fold['fold']}: n_val={len(df_val):>6,} "
                f"n_pos={res['n_pos_val']:>4} prev={res['prevalence_val']:.4f}{flag}"
            )
        results["horizons"][f"h{H}"] = {
            "per_fold": per_fold,
            "aggregate": aggregate_metrics(per_fold),
        }

    out_path = EDA_DIR / "fase4a_baselines.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n  → {out_path.relative_to(PROJECT_ROOT)}")

    print("\n" + "=" * 72)
    print("Resumo (assume_zero, agregado APENAS folds estáveis):")
    print("=" * 72)
    print(
        f"{'H':>3} | {'AUC-PR (mean ± std)':>24} | {'Lift (mean)':>12} | "
        f"{'Recall@P=0.5':>14} | folds"
    )
    print("-" * 72)
    for H in HORIZONS:
        agg = results["horizons"][f"h{H}"]["aggregate"]["baseline1_assume_zero"][
            "metrics_aggregate_stable_only"
        ]
        n_used = results["horizons"][f"h{H}"]["aggregate"]["baseline1_assume_zero"][
            "n_folds_stable_used"
        ]
        ap = agg["auc_pr"]
        lf = agg["lift"]
        rec = agg["recall_at_p50"]
        print(
            f"{H:>3}h | {ap['mean']:>10.4f} ± {ap['std']:>8.4f} | "
            f"{lf['mean']:>12.2f} | {rec['mean']:>14.4f} | {n_used}"
        )
    print("\nFase 4A concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
