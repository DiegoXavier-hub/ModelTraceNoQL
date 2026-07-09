"""Runner Fase 4E — PA-3 anomalia LeTourneau (Isolation Forest + Autoencoder LSTM).

Para LeTourneau (D027): 32 incidentes em ~291k janelas.
Treina IF e LSTM AE em janeiro (sem labels) e avalia capture rate em fev-jun.

Saídas
------
- ``outputs/models/iforest_lt.joblib``
- ``outputs/models/ae_lstm_lt.pt``
- ``reports/eda_results/fase4e_pa3_anomaly.json``
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

warnings.filterwarnings("ignore")

from src.utils.paths import PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import SEED, set_global_seed
from src.eval.splits import apply_censura_filter
from src.models.pa3_isolation_forest import (
    anomaly_scores,
    capture_at_topn,
    fit_isolation_forest,
)
from src.models.pa3_autoencoder_lstm import (
    SEQ_LEN,
    _sample_sequences,
    fit_autoencoder,
    reconstruction_score,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = REPORTS_DIR / "eda_results"
MODELS_DIR = PROJECT_ROOT / "outputs" / "models"

# Caps para velocidade
MAX_AE_TRAIN_SEQS = 50000
MAX_AE_EVAL_SEQS = 100000


def load_dataset_v2_lt() -> pd.DataFrame:
    files = sorted(PROCESSED_DIR.glob("features_2025-*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["t_window"] = pd.to_datetime(df["t_window"])
    df = df[df["OEM"] == "LeTourneau"].copy()
    df = apply_censura_filter(df, horizon_h=12, kind="train").reset_index(drop=True)
    return df


def main() -> None:
    print("=" * 72)
    print("Fase 4E — PA-3 Anomalia LeTourneau (IF + LSTM AE)")
    print("=" * 72)
    set_global_seed()

    df_lt = load_dataset_v2_lt()
    n_total = len(df_lt)
    n_pos_total = int(df_lt["y_dontgo_12h"].sum())
    print(f"\nLeTourneau: {n_total:,} janelas | {n_pos_total} positivos (y_dontgo_12h)")

    # Split temporal: train=jan, eval=fev-jun (incidentes "futuros")
    df_train = df_lt[df_lt["mes_str"] == "2025-01"].reset_index(drop=True)
    df_eval = df_lt[df_lt["mes_str"] != "2025-01"].reset_index(drop=True)
    print(
        f"Train (jan): {len(df_train):,} | Eval (fev-jun): {len(df_eval):,} "
        f"| n_pos eval: {int(df_eval['y_dontgo_12h'].sum())}"
    )

    results: dict = {
        "config": {
            "n_total_lt": n_total,
            "n_pos_total_lt": n_pos_total,
            "split_train": "2025-01",
            "split_eval": "2025-02..06",
            "seed": SEED,
        },
        "isolation_forest": {},
        "autoencoder_lstm": {},
    }

    # ---- Isolation Forest ----
    print("\n[1/2] Isolation Forest...")
    t0 = time.time()
    iso, cols = fit_isolation_forest(df_train, n_estimators=200, contamination="auto")
    elapsed = time.time() - t0
    scores_eval = anomaly_scores(iso, df_eval, cols)
    capture = capture_at_topn(scores_eval, df_eval["y_dontgo_12h"].to_numpy())
    print(f"  treinado em {elapsed:.0f}s | features: {len(cols)}")
    for k, v in capture.items():
        print(
            f"  {k:>10}: capturados {v['captured']}/{v['total']} ({v['pct_captured']:.1f}%) "
            f"| precision={v['precision']:.4f}%"
        )
    joblib.dump({"model": iso, "feature_cols": cols}, MODELS_DIR / "iforest_lt.joblib")
    results["isolation_forest"] = {
        "elapsed_s_train": round(elapsed, 1),
        "n_train": int(len(df_train)),
        "n_eval": int(len(df_eval)),
        "n_pos_eval": int(df_eval["y_dontgo_12h"].sum()),
        "n_features": int(len(cols)),
        "capture": capture,
    }

    # ---- Autoencoder LSTM ----
    print("\n[2/2] Autoencoder LSTM...")
    feature_cols = [c for c in df_lt.columns if c.startswith("n_")]
    print(f"  Construindo sequências de {SEQ_LEN} janelas (3h)...")
    seqs_tr, _, _ = _sample_sequences(
        df_train, feature_cols, seq_len=SEQ_LEN, max_seqs=MAX_AE_TRAIN_SEQS
    )
    seqs_eval, anchors_eval, pos_anchors_eval = _sample_sequences(
        df_eval, feature_cols, seq_len=SEQ_LEN, max_seqs=MAX_AE_EVAL_SEQS
    )
    print(f"  train_seqs: {seqs_tr.shape} | eval_seqs: {seqs_eval.shape}")
    if len(seqs_tr) < 100 or len(seqs_eval) < 100:
        print("  [WARN] sequências insuficientes; pulando AE.")
        results["autoencoder_lstm"] = {"skipped": True, "reason": "few sequences"}
    else:
        # Normalização leve (z-score por feature, com clip)
        mu = seqs_tr.reshape(-1, seqs_tr.shape[2]).mean(axis=0)
        sd = seqs_tr.reshape(-1, seqs_tr.shape[2]).std(axis=0) + 1e-6
        seqs_tr_n = ((seqs_tr - mu) / sd).clip(-5, 5).astype(np.float32)
        seqs_eval_n = ((seqs_eval - mu) / sd).clip(-5, 5).astype(np.float32)

        t0 = time.time()
        model = fit_autoencoder(seqs_tr_n, n_epochs=8, batch_size=128, lr=1e-3)
        ae_t = time.time() - t0
        scores_ae = reconstruction_score(model, seqs_eval_n, batch_size=256)
        capture_ae = capture_at_topn(scores_ae, pos_anchors_eval)
        print(
            f"  treinado em {ae_t:.0f}s | "
            f"loss final epoch: {model._train_loss_history[-1]:.6f}"
        )
        for k, v in capture_ae.items():
            print(
                f"  {k:>10}: capturados {v['captured']}/{v['total']} "
                f"({v['pct_captured']:.1f}%) | precision={v['precision']:.4f}%"
            )

        # Salvar modelo torch
        import torch as _t

        _t.save(
            {
                "state_dict": model.state_dict(),
                "n_features": int(seqs_tr.shape[2]),
                "mu": mu.tolist(),
                "sd": sd.tolist(),
                "feature_cols": feature_cols,
            },
            MODELS_DIR / "ae_lstm_lt.pt",
        )
        results["autoencoder_lstm"] = {
            "elapsed_s_train": round(ae_t, 1),
            "n_train_seqs": int(len(seqs_tr_n)),
            "n_eval_seqs": int(len(seqs_eval_n)),
            "n_pos_eval_seqs": int(pos_anchors_eval.sum()),
            "n_features": int(seqs_tr.shape[2]),
            "loss_history": [round(x, 6) for x in model._train_loss_history],
            "capture": capture_ae,
        }

    out_path = EDA_DIR / "fase4e_pa3_anomaly.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n→ {out_path.relative_to(PROJECT_ROOT)}")
    print("\nFase 4E concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
