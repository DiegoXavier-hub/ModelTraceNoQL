"""Driver Fase 5 / PRE-2 — Lead time empírico (per-window + per-incidente).

Para cada horizonte H ∈ {1, 2, 4, 6, 8, 12}:

1. Lê ``outputs/predictions/preds_jun_h{H}.parquet`` (PRE-1).
2. Regenera incidentes de junho via ``load_jun_incidents_cat`` (CAT).
3. Computa ``threshold_at_p50`` sobre ``score_cal`` da PR-curve em junho.
4. Computa lead time per-incidente (D013) e per-window (target_lead_time_min).
5. Persiste ``outputs/predictions/lead_times_jun_h{H}.parquet``.

Saída JSON: ``reports/eda_results/fase5_pre2_lead_times.json``.
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

from src.eval.lead_time import (
    derive_per_incident_lead_times,
    load_jun_incidents_cat,
    per_window_lead_time_quantiles,
    pick_threshold_at_precision,
)
from src.utils.paths import PREDICTIONS_DIR, PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import SEED, set_global_seed

EDA_DIR = REPORTS_DIR / "eda_results"
HORIZONS = (1, 2, 4, 6, 8, 12)


def _quantiles(arr: np.ndarray) -> dict[str, float]:
    arr = np.asarray(arr, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return {"p25": float("nan"), "p50": float("nan"), "p75": float("nan")}
    return {
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
    }


def main() -> None:
    print("=" * 72)
    print("Fase 5 / PRE-2 — Lead time empírico (per-window + per-incidente)")
    print("=" * 72)
    set_global_seed()
    print(f"Seed: {SEED}")

    print("\n[1/3] Regenerando incidentes de junho (CAT, D009 + D018)...")
    t0 = time.time()
    incidents = load_jun_incidents_cat()
    dt_inc = time.time() - t0
    print(
        f"  Incidentes JUN-CAT: {len(incidents):,}"
        f" | TAGs distintas: {incidents['TAG'].nunique()}"
        f" | duração mediana: {incidents['duracao_min'].median():.1f} min"
        f" [{dt_inc:.1f}s]"
    )

    print("\n[2/3] Lead time por horizonte...")
    results: dict = {
        "config": {
            "seed": SEED,
            "horizons": list(HORIZONS),
            "n_incidentes_jun_cat": int(len(incidents)),
            "tol_min_d018": 30,
        },
        "horizons": {},
    }

    for H in HORIZONS:
        h_key = f"h{H}"
        t1 = time.time()

        preds_path = PREDICTIONS_DIR / f"preds_jun_h{H}.parquet"
        preds = pd.read_parquet(preds_path)
        preds["t_window"] = pd.to_datetime(preds["t_window"])

        # 1) Threshold operacional (precision >= 0.5)
        th, p_at, r_at = pick_threshold_at_precision(
            preds["y_true"].to_numpy(),
            preds["score_cal"].to_numpy(),
            target_precision=0.5,
        )

        # 2) Per-incidente
        if np.isfinite(th):
            df_lt = derive_per_incident_lead_times(preds, incidents, H, th)
        else:
            df_lt = derive_per_incident_lead_times(
                preds, incidents, H, threshold=2.0  # impossível, marca tudo FN
            )

        out_path = PREDICTIONS_DIR / f"lead_times_jun_h{H}.parquet"
        df_lt.to_parquet(out_path, index=False)

        n_inc_total = int(len(df_lt))
        n_tp = int((df_lt["status"] == "TP").sum())
        n_fn = int((df_lt["status"] == "FN").sum())
        recall_inc = n_tp / n_inc_total if n_inc_total else float("nan")
        lead_quantiles_inc = _quantiles(df_lt["lead_time_min"].to_numpy())

        # 3) Per-window
        lead_quantiles_win = per_window_lead_time_quantiles(preds)

        # Bucket de lead time per-window (D013 — buckets do plano da Fase 1)
        # 0–15 min, 15–60 min, 1–4 h
        mask_tp = (preds["y_true"] == 1) & preds["target_lead_time_min"].notna()
        arr = preds.loc[mask_tp, "target_lead_time_min"].to_numpy(dtype=float)
        b_0_15 = int(((arr >= 0) & (arr < 15)).sum())
        b_15_60 = int(((arr >= 15) & (arr < 60)).sum())
        b_60_240 = int(((arr >= 60) & (arr <= 240)).sum())
        b_above_240 = int((arr > 240).sum())
        n_tp_win = int(mask_tp.sum())

        dt = time.time() - t1
        results["horizons"][h_key] = {
            "threshold_at_p50": th,
            "precision_at_chosen": p_at,
            "recall_at_chosen": r_at,
            "n_incidentes_avaliados": n_inc_total,
            "n_TP_per_incident": n_tp,
            "n_FN_per_incident": n_fn,
            "recall_per_incident": recall_inc,
            "lead_time_per_incident_min": lead_quantiles_inc,
            "n_TP_per_window": n_tp_win,
            "lead_time_per_window_min": lead_quantiles_win,
            "lead_time_buckets_per_window": {
                "0-15min": b_0_15,
                "15-60min": b_15_60,
                "1-4h": b_60_240,
                ">4h": b_above_240,
                "n_total": n_tp_win,
            },
            "parquet": str(out_path.relative_to(PROJECT_ROOT)),
            "elapsed_s": round(dt, 2),
        }

        th_repr = f"{th:.4f}" if np.isfinite(th) else "NaN"
        lt_p50 = lead_quantiles_inc["p50"]
        lt_repr = f"{lt_p50:.1f}" if np.isfinite(lt_p50) else "n/a"
        print(
            f"  H{H:>2}h: τ@P=0.5={th_repr} (P={p_at:.3f},R={r_at:.3f})"
            f" | TP/Inc={n_tp}/{n_inc_total} (recall={recall_inc:.3f})"
            f" | lead p50={lt_repr} min"
            f" | win bucket: 0-15={b_0_15} 15-60={b_15_60} 1-4h={b_60_240} >4h={b_above_240}"
            f" [{dt:.1f}s]"
        )

    out_json = EDA_DIR / "fase5_pre2_lead_times.json"
    out_json.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n[3/3] → {out_json.relative_to(PROJECT_ROOT)}")
    print("\n✅ PRE-2 OK — lead times per-window e per-incidente persistidos.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
