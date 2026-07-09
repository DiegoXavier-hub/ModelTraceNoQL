"""Auditoria abrangente das Fases 0-5 (2026-05-09).

Estende `_audit_fases_0_a_4.py` com verificações da Fase 5.
Saída: stdout + reports/eda_results/audit_fases_0_5.json.
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


# ---------- Reusa as 51 checagens das Fases 0-4 ----------
print("=" * 70)
print("Bloco 1 — Auditoria Fases 0-4 (delegada)")
print("=" * 70)
prev = json.loads(
    (PROJECT_ROOT / "reports" / "eda_results" / "audit_fases_0_4.json").read_text(
        encoding="utf-8"
    )
)
for c in prev["checks"]:
    check(c["label"], c["ok"], c["detail"])

# ---------- Fase 5 ----------
print()
print("=" * 70)
print("Bloco 2 — Auditoria Fase 5 (Evaluation)")
print("=" * 70)


def c51_modules() -> tuple[bool, str]:
    paths = [
        "src/eval/predictions.py",
        "src/eval/lead_time.py",
        "src/eval/error_analysis.py",
        "src/eval/business_impact.py",
    ]
    miss = [p for p in paths if not (PROJECT_ROOT / p).exists()]
    return len(miss) == 0, f"miss={miss}"


safe_run("Módulos da Fase 5 existem", c51_modules)


def c52_imports() -> tuple[bool, str]:
    from src.eval import (  # noqa: F401
        business_impact,
        error_analysis,
        lead_time,
        predictions,
    )
    return True, "src.eval.{predictions,lead_time,error_analysis,business_impact} OK"


safe_run("Imports dos módulos da Fase 5", c52_imports)


def c53_predictions_parquets() -> tuple[bool, str]:
    pred_dir = PROJECT_ROOT / "outputs" / "predictions"
    miss = []
    for H in (1, 2, 4, 6, 8, 12):
        pp = pred_dir / f"preds_jun_h{H}.parquet"
        lp = pred_dir / f"lead_times_jun_h{H}.parquet"
        if not pp.exists():
            miss.append(pp.name)
        if not lp.exists():
            miss.append(lp.name)
    return len(miss) == 0, f"miss={miss}"


safe_run("Predições + lead times persistidos (12 parquets)", c53_predictions_parquets)


def c54_predictions_match_canonical() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase5_pre1_predictions.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    fail = [h for h, v in r["horizons"].items() if not v["checks"]["all_pass"]]
    return len(fail) == 0, (
        f"all_pass={r['global']['all_pass']}, fail={fail}"
    )


safe_run("PRE-1: AUC-PR/Brier batem com canônicos (6/6)", c54_predictions_match_canonical)


def c55_lead_times_consistency() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase5_pre2_lead_times.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    n_inc = r["config"]["n_incidentes_jun_cat"]
    fail = []
    for H in (1, 2, 4, 6, 8, 12):
        v = r["horizons"][f"h{H}"]
        if v["n_incidentes_avaliados"] != n_inc:
            fail.append(f"h{H}: {v['n_incidentes_avaliados']} != {n_inc}")
    return len(fail) == 0, f"n_inc={n_inc}, fail={fail}"


safe_run("PRE-2: # incidentes consistente entre H (6/6)", c55_lead_times_consistency)


def c56_recall_per_incident_growth() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase5_pre2_lead_times.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    rec = [r["horizons"][f"h{H}"]["recall_per_incident"] for H in (1, 2, 4, 6, 8, 12)]
    monotonic = all(a <= b + 1e-6 for a, b in zip(rec, rec[1:]))
    h12_ok = rec[-1] >= 0.5
    return monotonic and h12_ok, f"rec={[round(x, 3) for x in rec]} monot={monotonic}, h12>=0.5={h12_ok}"


safe_run("PRE-2: recall_per_incident cresce com H e ≥0.5 em H12h", c56_recall_per_incident_growth)


def c57_5a_table() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "tables" / "fase5a_pa1_consolidado.csv"
    if not p.exists():
        return False, f"missing: {p}"
    df = pd.read_csv(p)
    n_models = df["model"].nunique()
    n_h = df["horizon_h"].nunique()
    return (n_models == 4 and n_h == 6 and len(df) == 24), (
        f"n_models={n_models} n_h={n_h} len={len(df)}"
    )


safe_run("5A: tabela consolidada 4×6=24 linhas", c57_5a_table)


def c58_5a_figures() -> tuple[bool, str]:
    fig_dir = PROJECT_ROOT / "reports" / "figures"
    needed = [
        "fig09_pr_curves.png",
        "fig10_roc_curves.png",
        "fig11_confusion_matrix_h4.png",
        "fig11b_confusion_matrix_h12.png",
    ]
    miss = [f for f in needed if not (fig_dir / f).exists()]
    return len(miss) == 0, f"miss={miss}"


safe_run("5A: figuras (fig09/fig10/fig11/fig11b) presentes", c58_5a_figures)


def c59_5b_fn_waterfalls() -> tuple[bool, str]:
    fig_dir = PROJECT_ROOT / "reports" / "figures"
    waters = list(fig_dir.glob("fig12_fn_waterfalls_*.png"))
    return len(waters) >= 5, f"n_waterfalls={len(waters)} (>=5 esperado)"


safe_run("5B: ≥5 figuras fig12_fn_waterfalls_*.png", c59_5b_fn_waterfalls)


def c60_5b_error_dist() -> tuple[bool, str]:
    fig_dir = PROJECT_ROOT / "reports" / "figures"
    needed = ["fig13_error_distribution.png", "fig13b_fn_by_dimension.png"]
    miss = [f for f in needed if not (fig_dir / f).exists()]
    return len(miss) == 0, f"miss={miss}"


safe_run("5B: figuras de distribuição de erros", c60_5b_error_dist)


def c61_5c_surface() -> tuple[bool, str]:
    fig_dir = PROJECT_ROOT / "reports" / "figures"
    needed = ["fig17_sensitivity_surface.png", "fig17b_sensitivity_surface_h12.png"]
    miss = [f for f in needed if not (fig_dir / f).exists()]
    return len(miss) == 0, f"miss={miss}"


safe_run("5C: figuras de superfície de sensibilidade", c61_5c_surface)


def c62_5c_d_avg() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase5c_business_impact.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    has_phys = "fisico_reconstruido" in r["d_avg"]
    has_op = "operacional" in r["d_avg"]
    has_global = "global" in r["d_avg"]
    used = r["d_avg"]["d_avg_h_used_in_surface"]
    used_ok = 0.5 < used < 5.0  # 30 min a 5h é faixa razoável
    return (has_phys and has_op and has_global and used_ok), (
        f"phys={has_phys}, op={has_op}, global={has_global}, used={used:.3f}h"
    )


safe_run("5C: três estimativas de d_avg + valor default razoável", c62_5c_d_avg)


def c63_5c_surface_cells() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase5c_business_impact.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    fail = []
    for H in (4, 12):
        n_cells = len(r["surface_per_h_fisico_default"][f"h{H}"]["cells"])
        if n_cells != 12:
            fail.append(f"h{H}: {n_cells} cells != 12")
    return len(fail) == 0, f"fail={fail}"


safe_run("5C: superfície com 12 células (4 ΔP × 3 ρ)", c63_5c_surface_cells)


def c64_decisions_d039_d040() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "decisions.md"
    text = p.read_text(encoding="utf-8")
    needed = ["D039", "D040"]
    miss = [d for d in needed if f"## {d} —" not in text]
    return len(miss) == 0, f"miss={miss}"


safe_run("decisions.md cobre D039 e D040", c64_decisions_d039_d040)


def c65_cap5_writed() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "article_dontgo" / "cap5_discussao.tex"
    text = p.read_text(encoding="utf-8")
    needed = [
        "\\section{Síntese dos Resultados}",
        "\\section{Limitações}",
        "\\section{Comparação com a Literatura}",
        "\\section{Tradução em Impacto Operacional}",
        "\\section{Trabalhos Futuros (preview)}",
    ]
    miss = [s for s in needed if s not in text]
    n_lines = len(text.splitlines())
    return (len(miss) == 0 and n_lines >= 100), (
        f"miss={miss}, n_lines={n_lines} (≥100 esperado)"
    )


safe_run("Cap 5 (cap5_discussao.tex) com 5 seções e ≥100 linhas", c65_cap5_writed)


def c66_memory_section_14() -> tuple[bool, str]:
    p = PROJECT_ROOT / "MEMORY.md"
    text = p.read_text(encoding="utf-8")
    return ("## 14. Checkpoint da Fase 5" in text), "seção 14 presente em MEMORY.md"


safe_run("MEMORY.md §14 (Checkpoint Fase 5) presente", c66_memory_section_14)


def c67_pendencias_atualizada() -> tuple[bool, str]:
    p = PROJECT_ROOT / "PENDENCIAS.md"
    text = p.read_text(encoding="utf-8")
    closed = "Fase 5 — Evaluation" in text and "FECHADA" in text
    return closed, f"Fase 5 marcada como fechada: {closed}"


safe_run("PENDENCIAS.md tem Fase 5 marcada como FECHADA", c67_pendencias_atualizada)


def c68_globally_missed() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase5b_error_analysis.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    n_fn = r["fn_globally_missed_incidents_n"]
    n_with_shap = len(r["fn_top10_globally_missed_with_shap"])
    return n_with_shap >= 5, f"n_fn_globais={n_fn}, com_shap={n_with_shap} (>=5 esperado)"


safe_run("5B: ≥5 incidentes FN globais com SHAP local", c68_globally_missed)


def c69_recommended_op_point() -> tuple[bool, str]:
    p = PROJECT_ROOT / "reports" / "eda_results" / "fase5c_business_impact.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    rec = r["recommended_operating_point"]
    fields = ["horizon_h", "delta_p_min", "rho", "hours_saved_per_month"]
    miss = [f for f in fields if f not in rec]
    return len(miss) == 0, f"missing fields={miss}, rec={rec}"


safe_run("5C: ponto operacional recomendado tem todos os campos", c69_recommended_op_point)


# Fechamento
print()
print("=" * 70)
RESULTS["totals"] = {"n_pass": N_PASS, "n_fail": N_FAIL, "n_total": N_PASS + N_FAIL}
print(f"TOTAL: {N_PASS} PASSA | {N_FAIL} FALHA | {N_PASS + N_FAIL} checks")
out_path = PROJECT_ROOT / "reports" / "eda_results" / "audit_fases_0_5.json"
out_path.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"-> {out_path.relative_to(PROJECT_ROOT)}")
sys.exit(0 if N_FAIL == 0 else 1)
