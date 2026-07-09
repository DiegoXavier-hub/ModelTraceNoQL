"""Driver Fase 5 / PRE-1 — Regerar predições do JUN holdout.

Para cada horizonte H ∈ {1, 2, 4, 6, 8, 12}:
- Carrega features de junho (CAT + censura).
- Aplica booster `lgbm_h{H}_holdout_jun.txt`.
- Calibra com método registrado em D037 (joblib `chosen_method`).
- Persiste parquet em `outputs/predictions/preds_jun_h{H}.parquet`.

Sanity checks contra `fase4b_pa1_lightgbm.json` e `fase4f_calibration.json`.
Saída JSON: `reports/eda_results/fase5_pre1_predictions.json`.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.predictions import load_holdout_cat, predict_holdout_jun
from src.utils.paths import PROJECT_ROOT, REPORTS_DIR
from src.utils.seeds import SEED, set_global_seed

EDA_DIR = REPORTS_DIR / "eda_results"
HORIZONS = (1, 2, 4, 6, 8, 12)
TOL_AUC_PR = 1e-6
TOL_BRIER = 1e-6


def _load_canonical() -> tuple[dict, dict]:
    fase4b = json.loads((EDA_DIR / "fase4b_pa1_lightgbm.json").read_text(encoding="utf-8"))
    fase4f = json.loads((EDA_DIR / "fase4f_calibration.json").read_text(encoding="utf-8"))
    return fase4b, fase4f


def main() -> None:
    print("=" * 72)
    print("Fase 5 / PRE-1 — Regerar predições do JUN holdout")
    print("=" * 72)
    set_global_seed()
    print(f"Seed: {SEED}")

    fase4b, fase4f = _load_canonical()

    print("\n[1/2] Carregando JUN parquet (CAT + ordenação)...")
    df_jun_cat = load_holdout_cat()
    print(f"  Linhas (CAT, antes de censura): {len(df_jun_cat):,}")

    results: dict = {
        "config": {
            "seed": SEED,
            "horizons": list(HORIZONS),
            "n_jun_cat_pre_filter": int(len(df_jun_cat)),
        },
        "horizons": {},
        "global": {"all_pass": True, "failures": []},
    }

    print("\n[2/2] Predições por horizonte...")
    for H in HORIZONS:
        h_key = f"h{H}"
        t0 = time.time()
        art = predict_holdout_jun(H, df_jun_cat=df_jun_cat)
        dt = time.time() - t0

        ref_b = fase4b["horizons"][h_key]["holdout_jun"]
        ref_f = fase4f["horizons"][h_key]
        canonical_method_post = "metrics_post_" + ref_f["chosen_method"]
        ref_brier_cal = ref_f[canonical_method_post]["brier"]
        ref_n = ref_b["n"]
        ref_n_pos = ref_b["n_pos"]
        ref_auc_pr = ref_b["metrics"]["auc_pr"]
        ref_chosen = ref_f["chosen_method"]

        check_n = art.n_rows == ref_n
        check_n_pos = art.n_pos == ref_n_pos
        check_method = art.chosen_method == ref_chosen
        check_auc_pr = abs(art.auc_pr_raw - ref_auc_pr) < TOL_AUC_PR
        check_brier = abs(art.brier_cal - ref_brier_cal) < TOL_BRIER

        all_ok = check_n and check_n_pos and check_method and check_auc_pr and check_brier

        results["horizons"][h_key] = {
            "parquet": str(art.parquet_path.relative_to(PROJECT_ROOT)),
            "n_rows": art.n_rows,
            "n_pos": art.n_pos,
            "chosen_method": art.chosen_method,
            "elapsed_s": round(dt, 2),
            "metrics_recomputed": {
                "auc_pr_raw": art.auc_pr_raw,
                "brier_cal": art.brier_cal,
            },
            "metrics_canonical": {
                "auc_pr_raw": ref_auc_pr,
                "brier_cal": ref_brier_cal,
                "n": ref_n,
                "n_pos": ref_n_pos,
                "chosen_method": ref_chosen,
            },
            "checks": {
                "n_match": check_n,
                "n_pos_match": check_n_pos,
                "method_match": check_method,
                "auc_pr_within_tol": check_auc_pr,
                "brier_cal_within_tol": check_brier,
                "all_pass": all_ok,
            },
        }
        if not all_ok:
            results["global"]["all_pass"] = False
            results["global"]["failures"].append(h_key)
        flag = "OK" if all_ok else "FAIL"
        print(
            f"  H{H:>2}h: n={art.n_rows:,}/{ref_n:,} pos={art.n_pos}/{ref_n_pos}"
            f" method={art.chosen_method} auc_pr_raw={art.auc_pr_raw:.6f}"
            f" brier_cal={art.brier_cal:.6f} ({flag}) [{dt:.1f}s]"
        )

    out_path = EDA_DIR / "fase5_pre1_predictions.json"
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n→ {out_path.relative_to(PROJECT_ROOT)}")
    if results["global"]["all_pass"]:
        print("\n✅ PRE-1 OK — predições recompõem AUC-PR/Brier canônicos em todos os 6 horizontes.")
    else:
        print(f"\n❌ PRE-1 FALHOU em: {results['global']['failures']}")
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
