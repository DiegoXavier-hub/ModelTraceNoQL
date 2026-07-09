"""Auditoria adicional Fase 5 — verificações cruzadas finais.

Roda DEPOIS de _audit_fases_0_a_5.py. Foca em:
- Cap 5: bibliografia, estrutura de seções, números coerentes com JSONs.
- Boosters: reprodutibilidade bit-a-bit das predições salvas.
- Calibradores: método em D037 igual ao salvo no joblib.
- PDF: integridade (páginas, refs, citations).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval.predictions import load_holdout_cat
from src.eval.splits import apply_censura_filter
from src.models.pa1_lightgbm import build_feature_matrix

results: dict = {"checks": [], "totals": {"n_pass": 0, "n_fail": 0}}


def check(label: str, ok: bool, detail: str = "") -> None:
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {label}: {detail}")
    results["checks"].append({"label": label, "ok": ok, "detail": detail})
    results["totals"]["n_pass" if ok else "n_fail"] += 1


print("=" * 70)
print("Auditoria Adicional Fase 5 — verificações cruzadas")
print("=" * 70)

# 1) Boosters reproduzem score_raw bit-a-bit
print("\n[1] Boosters reproduzem score_raw bit-a-bit:")
df_root = load_holdout_cat()
all_ok = True
for H in (1, 2, 4, 6, 8, 12):
    df_eval = apply_censura_filter(df_root, H, "eval")
    X, _, _ = build_feature_matrix(df_eval, H)
    booster = lgb.Booster(
        model_file=str(ROOT / f"outputs/models/lgbm_h{H}_holdout_jun.txt")
    )
    raw = np.clip(np.asarray(booster.predict(X)), 1e-6, 1 - 1e-6)
    saved = pd.read_parquet(
        ROOT / f"outputs/predictions/preds_jun_h{H}.parquet"
    )["score_raw"].to_numpy()
    delta = float(np.abs(raw - saved).max())
    ok = delta < 1e-12
    check(f"H={H}h booster reproduz", ok, f"delta_max={delta:.2e}")
    all_ok &= ok

# 2) Calibradores method == D037 esperado
print("\n[2] Calibradores method == D037:")
f4f = json.loads(
    (ROOT / "reports/eda_results/fase4f_calibration.json").read_text(encoding="utf-8")
)
for H in (1, 2, 4, 6, 8, 12):
    cal = joblib.load(ROOT / f"outputs/models/lgbm_calibrated_h{H}.joblib")
    expected = f4f["horizons"][f"h{H}"]["chosen_method"]
    ok = (cal["chosen_method"] == expected
          and "isotonic" in cal and "platt" in cal)
    check(f"H={H}h calibrador", ok,
          f"method={cal['chosen_method']}/D037={expected} both_present={('isotonic' in cal) and ('platt' in cal)}")

# 3) Recompute AUC-PR/Brier vs PRE-1 reported numbers
print("\n[3] AUC-PR raw e Brier cal recomputados batem com PRE-1:")
from sklearn.metrics import average_precision_score, brier_score_loss

f4b = json.loads((ROOT / "reports/eda_results/fase4b_pa1_lightgbm.json").read_text(encoding="utf-8"))
for H in (1, 2, 4, 6, 8, 12):
    df = pd.read_parquet(ROOT / f"outputs/predictions/preds_jun_h{H}.parquet")
    ap = average_precision_score(df["y_true"], df["score_raw"])
    bs = brier_score_loss(df["y_true"], df["score_cal"])
    ref_ap = f4b["horizons"][f"h{H}"]["holdout_jun"]["metrics"]["auc_pr"]
    method = f4f["horizons"][f"h{H}"]["chosen_method"]
    ref_bs = f4f["horizons"][f"h{H}"][f"metrics_post_{method}"]["brier"]
    ok = abs(ap - ref_ap) < 1e-9 and abs(bs - ref_bs) < 1e-9
    check(f"H={H}h métricas",
          ok, f"AUC-PR Δ={abs(ap-ref_ap):.2e} Brier Δ={abs(bs-ref_bs):.2e}")

# 4) Per-incident lead time: lead_p50 < H*60, recall crescente
print("\n[4] Per-incident lead time consistente:")
p2 = json.loads((ROOT / "reports/eda_results/fase5_pre2_lead_times.json").read_text(encoding="utf-8"))
horizons = (1, 2, 4, 6, 8, 12)
recalls = [p2["horizons"][f"h{H}"]["recall_per_incident"] for H in horizons]
leads = [p2["horizons"][f"h{H}"]["lead_time_per_incident_min"]["p50"] for H in horizons]
n_inc_ok = all(p2["horizons"][f"h{H}"]["n_incidentes_avaliados"] == p2["config"]["n_incidentes_jun_cat"] for H in horizons)
recall_mono = all(a <= b + 1e-9 for a, b in zip(recalls, recalls[1:]))
lead_below_cap = all(l < H * 60 for l, H in zip(leads, horizons))
check("# incidentes igual em todos os H", n_inc_ok,
      f"n_inc={p2['config']['n_incidentes_jun_cat']}")
check("recall_per_incident monotonic crescente", recall_mono,
      f"recalls={[round(r,3) for r in recalls]}")
check("lead_time_p50 < H*60 sempre", lead_below_cap,
      f"leads/lim_teor={[(round(l,1), H*60) for l, H in zip(leads, horizons)]}")

# 5) 5C surface 12 cells per H
print("\n[5] 5C superfície 12 células × H:")
f5c = json.loads((ROOT / "reports/eda_results/fase5c_business_impact.json").read_text(encoding="utf-8"))
for H in (2, 4, 8, 12):
    cells = f5c["surface_per_h_fisico_default"][f"h{H}"]["cells"]
    deltas = sorted({c["delta_p_min"] for c in cells})
    rhos = sorted({c["rho"] for c in cells})
    ok = (len(cells) == 12 and deltas == [30.0, 60.0, 120.0, 240.0]
          and rhos == [0.5, 0.7, 0.9])
    check(f"H={H}h surface 12 células", ok,
          f"n={len(cells)} deltas={deltas} rhos={rhos}")

# 6) Recommended op point é o máximo da superfície
print("\n[6] Ponto operacional recomendado é o máximo:")
rec = f5c["recommended_operating_point"]
all_cells = []
for H_str in f5c["surface_per_h_fisico_default"]:
    for c in f5c["surface_per_h_fisico_default"][H_str]["cells"]:
        all_cells.append(c["hours_saved_per_month"])
max_h = max(all_cells)
ok = abs(rec["hours_saved_per_month"] - max_h) < 0.1
check("rec é o máximo", ok, f"rec={rec['hours_saved_per_month']:.1f} max={max_h:.1f}")

# 7) Cap 5 estrutura: 5 seções
print("\n[7] Cap 5 estrutura:")
cap5 = (ROOT / "docs/article_dontgo/cap5_discussao.tex").read_text(encoding="utf-8")
sections = re.findall(r"\\section\{([^}]+)\}", cap5)
ok = len(sections) >= 5
check("≥5 seções em Cap 5", ok, f"sections={sections}")

# 8) Cap 5 cita números do JSON
print("\n[8] Cap 5 cita números coerentes com 5C JSON:")
expectations = [
    ("60{,}2 minutos", "P50 fisico"),
    ("11.047 paradas", "n_paradas físicas"),
    ("214 horas evitadas/mês", "recomendação H=12h"),
    ("81{,}3", "tabela H4 dP=30 ρ=0.5"),
    ("107{,}5", "tabela H4 dP=60 ρ=0.7"),
    ("281{,}7", "tabela H12 dP=30 ρ=0.9"),
]
for expected, label in expectations:
    ok = expected in cap5
    check(f"Cap5 menciona {label!r}", ok, f"present={ok} ({expected!r})")

# 9) Cap 5 bibliografia
print("\n[9] Cap 5 cites todas presentes na bibliografia:")
bib = (ROOT / "docs/article_dontgo/bibliografia.bib").read_text(encoding="utf-8")
pattern = r"\\(?:textcite|parencite|cite)\{([^}]+)\}"
cites = set(re.findall(pattern, cap5))
all_keys = set()
for c in cites:
    for k in c.split(","):
        all_keys.add(k.strip())
missing = [k for k in all_keys if f"{{{k}," not in bib]
ok = len(missing) == 0
check("todas as cites presentes na .bib", ok,
      f"total={len(all_keys)} miss={missing}")

# 10) PDF integridade
print("\n[10] PDF integridade:")
log = (ROOT / "docs/article_dontgo/TCC_DontGo.log").read_text(encoding="utf-8", errors="ignore")
m_pages = re.search(r"Output written on TCC_DontGo.pdf \((\d+) pages, (\d+) bytes\)", log)
m_undef = re.findall(r"LaTeX Warning: Reference `([^']+)' on page (\d+) undefined", log)
m_cit = re.findall(r"LaTeX Warning: Citation '([^']+)' on page (\d+) undefined", log)
pages = int(m_pages.group(1)) if m_pages else 0
ok = pages >= 75 and len(m_undef) == 0 and len(m_cit) == 0
check(f"PDF pages>=75 + 0 undefined refs/cites", ok,
      f"pages={pages} undef_refs={len(m_undef)} undef_cites={len(m_cit)}")

# 11) MEMORY §14 é a última seção e tem o handoff
print("\n[11] MEMORY §14 fechamento:")
mem = (ROOT / "MEMORY.md").read_text(encoding="utf-8")
section_14_present = "## 14. Checkpoint da Fase 5" in mem
handoff_present = "Plano da Fase 6" in mem
last_update = "Última atualização**: 2026-05-09" in mem
check("§14 + handoff + última atualização",
      section_14_present and handoff_present and last_update,
      f"§14={section_14_present} handoff={handoff_present} last_upd={last_update}")

# 12) Decisões D039, D040 com formato ANTES/DEPOIS/Justificativa
print("\n[12] D039/D040 formato completo:")
dec = (ROOT / "docs/decisions.md").read_text(encoding="utf-8")
for d in ("D039", "D040"):
    has_data = re.search(rf"## {d} —.*\n.*Data.*\n", dec) is not None
    has_antes = f"{d}" in dec and "ANTES" in dec.split(f"## {d} —")[1].split("##")[0]
    has_depois = "DEPOIS" in dec.split(f"## {d} —")[1].split("##")[0]
    has_just = "Justificativa" in dec.split(f"## {d} —")[1].split("##")[0]
    ok = has_antes and has_depois and has_just
    check(f"{d} tem ANTES/DEPOIS/Justificativa", ok,
          f"antes={has_antes} depois={has_depois} just={has_just}")

# Total
print()
print("=" * 70)
n_pass = results["totals"]["n_pass"]
n_fail = results["totals"]["n_fail"]
total = n_pass + n_fail
print(f"TOTAL: {n_pass} OK | {n_fail} FAIL | {total} checks adicionais")
out_path = ROOT / "reports/eda_results/audit_fase5_complete.json"
out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"-> {out_path.relative_to(ROOT)}")
sys.exit(0 if n_fail == 0 else 1)
