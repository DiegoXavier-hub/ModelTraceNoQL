"""Auditoria abrangente das Fases 0-4 (2026-05-04).

Estende `_audit_fases_0_a_3.py` com 18 verificacoes da Fase 4.
Saida: stdout + reports/eda_results/audit_fases_0_4.json.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

import pandas as pd

RESULTS: dict = {"checks": [], "totals": {}}
N_PASS = 0
N_FAIL = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global N_PASS, N_FAIL
    status = "PASSA" if ok else "FALHA"
    if ok:
        N_PASS += 1
    else:
        N_FAIL += 1
    print(f"  [{status}] {label}")
    if detail:
        print(f"           {detail}")
    RESULTS["checks"].append({"label": label, "ok": bool(ok), "detail": detail})


def safe_run(label: str, fn) -> None:
    try:
        ok, detail = fn()
        check(label, ok, detail)
    except Exception as e:
        tb = traceback.format_exc().splitlines()[-1]
        check(label, False, f"EXCECAO: {tb}")


# ---------- Reusa as 33 checagens da Fase 0-3 ----------
print("=" * 70)
print("Bloco 1 — Auditoria Fases 0-3 (delegada)")
print("=" * 70)
prev = json.loads(
    (PROJECT_ROOT / "reports" / "eda_results" / "audit_fases_0_3.json").read_text(
        encoding="utf-8"
    )
)
for c in prev["checks"]:
    check(c["label"], c["ok"], c["detail"])

# ---------- Fase 4 ----------
print()
print("=" * 70)
print("Bloco 2 — Auditoria Fase 4 (Modeling)")
print("=" * 70)


def c01() -> tuple[bool, str]:
    paths = [
        "src/eval/__init__.py",
        "src/eval/splits.py",
        "src/eval/metrics.py",
        "src/eval/drift.py",
        "src/models/__init__.py",
        "src/models/pa1_lightgbm.py",
        "src/models/pa1_xgb.py",
        "src/models/pa1_catboost.py",
        "src/models/pa2_survival.py",
        "src/models/pa3_isolation_forest.py",
        "src/models/pa3_autoencoder_lstm.py",
        "src/models/calibration.py",
    ]
    miss = [p for p in paths if not (PROJECT_ROOT / p).exists()]
    return len(miss) == 0, f"miss={miss}"


safe_run("Modulos da Fase 4 existem", c01)


def c02() -> tuple[bool, str]:
    from src.eval import splits, metrics, drift  # noqa: F401
    from src.models import (  # noqa: F401
        pa1_lightgbm,
        pa1_xgb,
        pa1_catboost,
        pa2_survival,
        pa3_isolation_forest,
        pa3_autoencoder_lstm,
        calibration,
    )

    return True, "imports OK"


safe_run("Imports dos 12 modulos OK", c02)


def c03() -> tuple[bool, str]:
    jsons = [
        "fase4a_splits.json",
        "fase4a_buffer_audit.json",
        "fase4a_baselines.json",
        "fase4b_pa1_lightgbm.json",
        "fase4b_feature_importance.json",
        "fase4c_pa1_comparativo.json",
        "fase4d_pa2_survival.json",
        "fase4e_pa3_anomaly.json",
        "fase4f_calibration.json",
        "fase4g_shap.json",
        "fase4h_drift.json",
    ]
    base = PROJECT_ROOT / "reports" / "eda_results"
    miss = [j for j in jsons if not (base / j).exists()]
    return len(miss) == 0, f"miss={miss}, encontrados={len(jsons) - len(miss)}/11"


safe_run("11 JSONs canonicos da Fase 4 existem", c03)


def c04() -> tuple[bool, str]:
    base = PROJECT_ROOT / "outputs" / "models"
    expected_lgbm = [f"lgbm_h{H}_fold{F}.txt" for H in (1, 2, 4, 6, 8, 12) for F in (1, 2, 3, 4)]
    expected_lgbm += [f"lgbm_h{H}_holdout_jun.txt" for H in (1, 2, 4, 6, 8, 12)]
    miss = [f for f in expected_lgbm if not (base / f).exists()]
    return len(miss) == 0, f"esperado=30, miss={miss}"


safe_run("30 modelos LightGBM serializados (24 WF + 6 holdout)", c04)


def c05() -> tuple[bool, str]:
    base = PROJECT_ROOT / "outputs" / "models"
    cox = [f"cox_ph_fold{F}.joblib" for F in (1, 2, 3, 4)]
    weib = [f"weibull_aft_fold{F}.joblib" for F in (1, 2, 3, 4)]
    miss = [f for f in cox + weib if not (base / f).exists()]
    return len(miss) == 0, f"esperado=8, miss={miss}"


safe_run("8 modelos sobrevivencia (4 Cox + 4 Weibull)", c05)


def c06() -> tuple[bool, str]:
    base = PROJECT_ROOT / "outputs" / "models"
    pa3 = [base / "iforest_lt.joblib", base / "ae_lstm_lt.pt"]
    miss = [str(p) for p in pa3 if not p.exists()]
    return len(miss) == 0, f"miss={miss}"


safe_run("PA-3 modelos serializados (IF + LSTM AE)", c06)


def c07() -> tuple[bool, str]:
    base = PROJECT_ROOT / "outputs" / "models"
    cal = [f"lgbm_calibrated_h{H}.joblib" for H in (1, 2, 4, 6, 8, 12)]
    miss = [f for f in cal if not (base / f).exists()]
    return len(miss) == 0, f"esperado=6, miss={miss}"


safe_run("6 calibradores LightGBM (Platt+Isotonic)", c07)


def c08() -> tuple[bool, str]:
    p = PROJECT_ROOT / "outputs" / "models" / "lgbm_best_params.json"
    if not p.exists():
        return False, "arquivo ausente"
    bp = json.loads(p.read_text(encoding="utf-8"))
    return len(bp) == 6, f"horizontes registrados: {list(bp.keys())}"


safe_run("lgbm_best_params.json com 6 horizontes (Optuna)", c08)


def c09() -> tuple[bool, str]:
    figs = [
        "fig14_calibration_curves.png",
        "fig15_shap_summary_h1.png",
        "fig15_shap_summary_h4.png",
        "fig15_shap_summary_h12.png",
        "fig16_shap_waterfall_5incidentes.png",
        "fig18_psi_heatmap.png",
    ]
    base = PROJECT_ROOT / "reports" / "figures"
    miss = [f for f in figs if not (base / f).exists()]
    return len(miss) == 0, f"esperado=6 figuras 4F-4H, miss={miss}"


safe_run("Figuras Fase 4 (calibracao + SHAP + drift)", c09)


def c10() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase4a_buffer_audit.json"
    a = json.loads(p.read_text(encoding="utf-8"))
    pcts = [m["pct_overlap"] for m in a["audit"]["measurement_A_val_lookback_overlap"]]
    max_pct = max(pcts)
    # D034 ratifica buffer 4h se overlap < 5% (limiar de critério revisado)
    return max_pct < 5.0, f"max_pct_overlap_A={max_pct:.2f}% (ratificado por D034)"


safe_run("Buffer 4h ratificado: overlap A < 5% (D034)", c10)


def c11() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase4b_pa1_lightgbm.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    lifts_jun = [r["horizons"][f"h{H}"]["holdout_jun"]["metrics"]["lift"] for H in (1, 2, 4, 6, 8, 12)]
    n_above_baseline = sum(1 for lf in lifts_jun if lf > 1.5)
    return n_above_baseline == 6, f"lifts_jun={[round(x, 2) for x in lifts_jun]}, n>1.5={n_above_baseline}/6"


safe_run("PA-1: lift junho > 1.5 em todos os horizontes", c11)


def c12() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase4f_calibration.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    eces = []
    for H in (1, 2, 4, 6, 8, 12):
        h = r["horizons"][f"h{H}"]
        chosen = h["chosen_method"]
        ece_post = h[f"metrics_post_{chosen}"]["ece"]
        eces.append(ece_post)
    n_below_005 = sum(1 for e in eces if e <= 0.05)
    return n_below_005 == 6, f"ece_pos={[round(x, 4) for x in eces]}, n<=0.05={n_below_005}/6"


safe_run("Calibracao: ECE pos <= 0.05 em todos os horizontes", c12)


def c13() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase4f_calibration.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    n_pos_improved = 0
    for H in (1, 2, 4, 6, 8, 12):
        h = r["horizons"][f"h{H}"]
        chosen = h["chosen_method"]
        brier_pre = h["metrics_pre"]["brier"]
        brier_post = h[f"metrics_post_{chosen}"]["brier"]
        if brier_post <= brier_pre:
            n_pos_improved += 1
    return n_pos_improved == 6, f"brier_pos<=pre em {n_pos_improved}/6 horizontes"


safe_run("Calibracao: Brier pos <= pre em todos os horizontes", c13)


def c14() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase4d_pa2_survival.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    c_cox_jun = r["holdout_jun"]["cox_ph"]["c_index"]
    c_aft_jun = r["holdout_jun"]["weibull_aft"].get("c_index")
    return c_aft_jun is not None and c_aft_jun > c_cox_jun, (
        f"Cox PH={c_cox_jun}, Weibull AFT={c_aft_jun} (D035: Weibull primario)"
    )


safe_run("PA-2: Weibull AFT supera Cox PH em junho (D035)", c14)


def c15() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase4h_drift.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    psi_top10_jun = r["fold4_to_jun"]["psi_top10_mean"]
    return psi_top10_jun < 0.25, f"PSI top10 fold4->jun = {psi_top10_jun:.4f} (< 0.25)"


safe_run("Drift: PSI top10 fold4->jun < 0.25 (D034 normaliza H010)", c15)


def c16() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase4g_shap.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    top1_h1 = r["horizons"]["h1"]["top_15_by_mean_abs_shap"][0]["feature"]
    top1_h12 = r["horizons"]["h12"]["top_15_by_mean_abs_shap"][0]["feature"]
    h002_ok = "n_crit" in top1_h1 or "n_naocrit" in top1_h1
    h009_ok = "n_fam_engine_coolant" in top1_h12 or any(
        "n_fam" in t["feature"]
        for t in r["horizons"]["h12"]["top_15_by_mean_abs_shap"][:3]
    )
    return h002_ok and h009_ok, (
        f"H1h top1={top1_h1} (H002), H12h top1={top1_h12} (H009)"
    )


safe_run("SHAP: top features coerentes com H002 e H009", c16)


def c17() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "decisions.md"
    text = p.read_text(encoding="utf-8")
    needed = ["D033", "D034", "D035", "D036", "D037", "D038"]
    miss = [d for d in needed if f"## {d} —" not in text]
    return len(miss) == 0, f"miss={miss}"


safe_run("decisions.md cobre D033-D038", c17)


def c18() -> tuple[bool, str]:
    p = PROJECT_ROOT / "MEMORY.md"
    text = p.read_text(encoding="utf-8")
    return "## 13. Checkpoint da Fase 4" in text, "secao 13 presente"


safe_run("MEMORY.md tem §13 (Checkpoint Fase 4)", c18)


# Fechamento
print()
print("=" * 70)
RESULTS["totals"] = {"n_pass": N_PASS, "n_fail": N_FAIL, "n_total": N_PASS + N_FAIL}
print(f"TOTAL: {N_PASS} PASSA | {N_FAIL} FALHA | {N_PASS + N_FAIL} checks")
out_path = PROJECT_ROOT / "reports" / "eda_results" / "audit_fases_0_4.json"
out_path.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"-> {out_path.relative_to(PROJECT_ROOT)}")
sys.exit(0 if N_FAIL == 0 else 1)
