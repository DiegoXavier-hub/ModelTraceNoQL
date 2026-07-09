"""Materializa o dataset de features para Fase 4 (Modeling).

Roda `build_features_for_month` para cada mes (jan-jun 2025) e salva os
parquets particionados em `data/processed/features_<mes>.parquet`.
Tambem produz um relatorio agregado em
`reports/eda_results/fase3c_build_report.json`.

Princípio governante: ROBUSTEZ > custo computacional.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loaders import get_connection, load_telemetria_lazy
from src.features.builders import build_features_for_month
from src.utils.paths import PROJECT_ROOT as ROOT, REPORTS_DIR
from src.utils.seeds import set_global_seed

set_global_seed()

PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MESES = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
RESULTS: dict = {"per_month": [], "totals": {}}

con = get_connection()
con.execute("PRAGMA disable_progress_bar")
rel = load_telemetria_lazy(con)

t_start = time.time()
total_windows = 0
total_y1h = 0
total_y12h = 0

print("=" * 72)
print("Fase 3C - Materializacao do dataset de features (jan-jun 2025)")
print("=" * 72)

for mes in MESES:
    print(f"\n>>> {mes} ...")
    t0 = time.time()
    df, rep = build_features_for_month(rel, mes, con=con)
    elapsed = time.time() - t0
    out_path = PROCESSED_DIR / f"features_{mes}.parquet"
    df.to_parquet(out_path, index=False)
    n_features = len(
        [c for c in df.columns if c.startswith(("n_", "y_", "lead_time"))]
    )

    rec = {
        "mes": mes,
        "n_windows": rep.n_windows,
        "n_tags": rep.n_tags,
        "n_features": n_features,
        "pct_tem_telemetria": rep.pct_tem_telemetria,
        "n_dontgo_1h": rep.n_dontgo_1h,
        "n_dontgo_12h": rep.n_dontgo_12h,
        "elapsed_s": rep.elapsed_s,
        "out_path": str(out_path),
        "size_mb": out_path.stat().st_size / 1024 / 1024,
    }
    RESULTS["per_month"].append(rec)
    total_windows += rep.n_windows
    total_y1h += rep.n_dontgo_1h
    total_y12h += rep.n_dontgo_12h

    print(rep.summary())
    print(f"    saved: {out_path} ({rec['size_mb']:.1f} MB)")

elapsed_total = time.time() - t_start
RESULTS["totals"] = {
    "n_meses": len(MESES),
    "n_windows_total": total_windows,
    "n_dontgo_1h_total": total_y1h,
    "n_dontgo_12h_total": total_y12h,
    "elapsed_total_s": elapsed_total,
}

print()
print("=" * 72)
print(f"DONE em {elapsed_total/60:.1f} min")
print(f"Total windows: {total_windows:,}")
print(f"Total y_dontgo_1h: {total_y1h:,}")
print(f"Total y_dontgo_12h: {total_y12h:,}")
print(f"Prevalencia y_1h: {total_y1h/max(total_windows,1)*100:.4f}%")
print(f"Prevalencia y_12h: {total_y12h/max(total_windows,1)*100:.4f}%")

out_json = RESULTS_DIR / "fase3c_build_report.json"
out_json.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"Report: {out_json}")
print("=" * 72)
