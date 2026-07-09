"""Auditoria abrangente das Fases 0-3 (2026-05-03).

Cada bloco roda um conjunto de verificacoes empiricas independentes;
imprime PASSA / FALHA por item; agrega estatistica final. Princípio: se
nao roda, nao passa.

Saida: stdout legivel + reports/eda_results/audit_fases_0_3.json.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

import pandas as pd

RESULTS: dict = {"checks": [], "totals": {}}
N_PASS = 0
N_FAIL = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    """Registra um check."""
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


def try_check(label: str, fn) -> None:
    try:
        ok, detail = fn()
        check(label, ok, detail)
    except Exception as e:
        check(label, False, f"EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


# =========================================================================
# Fase 0 — Setup
# =========================================================================
section("Fase 0 — Setup")

def f0_files():
    must_exist = [
        "requirements.txt",
        "src/utils/paths.py",
        "src/utils/seeds.py",
        "src/data/loaders.py",
        "MEMORY.md",
    ]
    miss = [p for p in must_exist if not (PROJECT_ROOT / p).exists()]
    return (not miss, "OK" if not miss else f"missing: {miss}")
try_check("Arquivos obrigatorios da Fase 0", f0_files)


def f0_imports():
    from src.utils import paths, seeds  # noqa: F401
    from src.data import loaders  # noqa: F401
    return True, "src.utils.{paths, seeds}, src.data.loaders OK"
try_check("Imports core (paths/seeds/loaders)", f0_imports)


def f0_seeds():
    from src.utils.seeds import set_global_seed
    set_global_seed()
    import random, numpy as np
    a = random.random()
    b = float(np.random.rand())
    set_global_seed()
    a2 = random.random()
    b2 = float(np.random.rand())
    return (a == a2 and b == b2, f"random determ: {a==a2}, numpy: {b==b2}")
try_check("set_global_seed() determinismo", f0_seeds)


# =========================================================================
# Fase 1 — Business Understanding
# =========================================================================
section("Fase 1 — Business Understanding")

def f1_docs():
    must = [
        "docs/business_understanding.md",
        "docs/decisions.md",
        "docs/hypotheses.md",
        "docs/methodology_review.md",
    ]
    miss = [p for p in must if not (PROJECT_ROOT / p).exists()]
    return (not miss, "OK" if not miss else f"missing: {miss}")
try_check("Docs canonicos da Fase 1 existem", f1_docs)


def f1_decisions_count():
    txt = (PROJECT_ROOT / "docs/decisions.md").read_text(encoding="utf-8")
    # Conta D001..D032 como cabecalhos formais.
    import re
    ids = re.findall(r"^## D(\d{3})", txt, flags=re.MULTILINE)
    nums = sorted(set(int(i) for i in ids))
    expected = set(range(1, 33))  # D001..D032
    found = set(nums)
    miss = expected - found
    extras = found - expected
    ok = not miss and not extras and len(found) == 32
    detail = f"found {len(found)} (D001..D032), miss={sorted(miss)}, extras={sorted(extras)}"
    return ok, detail
try_check("decisions.md com 32 entradas (D001..D032)", f1_decisions_count)


def f1_hypotheses_count():
    txt = (PROJECT_ROOT / "docs/hypotheses.md").read_text(encoding="utf-8")
    import re
    ids = re.findall(r"### H(\d{3})", txt)
    nums = sorted(set(int(i) for i in ids))
    expected = set(range(1, 18))  # H001..H017
    found = set(nums)
    miss = expected - found
    ok = not miss and len(found) == 17
    return ok, f"found {len(found)} hipoteses, miss={sorted(miss)}"
try_check("hypotheses.md com 17 hipoteses (H001..H017)", f1_hypotheses_count)


# =========================================================================
# Fase 2 — Data Understanding (EDA)
# =========================================================================
section("Fase 2 — Data Understanding (EDA)")

def f2_jsons():
    must = [
        "reports/eda_results/fase2b_results.json",
        "reports/eda_results/fase2c_results.json",
        "reports/eda_results/fase2d_results.json",
        "reports/eda_results/fase2e_results.json",
        "reports/eda_results/audit_fase2.json",
        "reports/eda_results/incidentes_dontgo.csv",
    ]
    miss = [p for p in must if not (PROJECT_ROOT / p).exists()]
    return (not miss, "OK" if not miss else f"missing: {miss}")
try_check("JSONs canonicos da Fase 2 existem", f2_jsons)


def f2_canonical_numbers():
    fc = json.loads((PROJECT_ROOT / "reports/eda_results/fase2c_results.json").read_text(encoding="utf-8"))
    n_total = fc["taxa_is_dont_go"]["n_total"]
    n_dontgo = fc["taxa_is_dont_go"]["n_dontgo"]
    n_inc = fc["incidentes"]["n_incidentes_30min"]
    expected = {"n_total": 37164054, "n_dontgo": 19962, "n_inc": 5025}
    actual = {"n_total": int(n_total), "n_dontgo": int(n_dontgo), "n_inc": int(n_inc)}
    ok = actual == expected
    return ok, f"actual={actual} expected={expected}"
try_check("Numeros canonicos Fase 2 (n_total/n_dontgo/n_inc)", f2_canonical_numbers)


def f2_pareamento_corrigido():
    """Valida correcao de PENDENCIAS item 2 — denominador do pareamento."""
    fe = json.loads((PROJECT_ROOT / "reports/eda_results/fase2e_results.json").read_text(encoding="utf-8"))
    val = fe.get("pareamento_pct_zero_operando", -1)
    # Antes era 8.98 (errado); correto eh 19.11 (sample) com nota apontando 17.6 populacional.
    ok = abs(val - 19.108) < 0.01
    has_note = "_note_pareamento_pct_zero_operando" in fe
    return ok and has_note, f"valor={val:.3f} (esperado 19.108), note presente={has_note}"
try_check("Item 2 PENDENCIAS — denominador pareamento corrigido", f2_pareamento_corrigido)


def f2_audit_h010():
    """A auditoria mostrou redução real −72,5% (não −49%)."""
    aj = json.loads((PROJECT_ROOT / "reports/eda_results/audit_fase2.json").read_text(encoding="utf-8"))
    rows = aj["h010_normalizado"]
    peak = max(r["inc_per_milhao_evt"] for r in rows)
    vale = min(r["inc_per_milhao_evt"] for r in rows)
    drop = (peak - vale) / peak * 100
    ok = abs(drop - 72.5) < 1.0
    return ok, f"peak={peak:.2f}, vale={vale:.2f}, drop={drop:.2f}% (esperado ~72,5%)"
try_check("H010 refinada na auditoria: drift = -72.5%", f2_audit_h010)


def f2_h013_pop():
    aj = json.loads((PROJECT_ROOT / "reports/eda_results/audit_fase2.json").read_text(encoding="utf-8"))
    pct = aj["h013_pop_total"]["pct_zero"]
    ok = abs(pct - 17.616) < 0.05
    return ok, f"pct_zero_op_pop={pct:.3f}% (esperado ~17.61)"
try_check("H013 populacional: 17,61% Operando sem telemetria", f2_h013_pop)


def f2_notebook_02():
    p = PROJECT_ROOT / "notebooks/02_data_understanding_eda.ipynb"
    if not p.exists():
        return False, "ausente"
    nb = json.loads(p.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    code_cells = [c for c in cells if c.get("cell_type") == "code"]
    code_with_out = [c for c in code_cells if c.get("outputs")]
    has_kernel = "kernelspec" in nb.get("metadata", {})
    ok = len(cells) >= 25 and has_kernel and len(code_with_out) >= 5
    return ok, f"cells={len(cells)}, code_with_outputs={len(code_with_out)}, kernelspec={has_kernel}"
try_check("Notebook 02 estruturalmente valido (>=25 cells, kernelspec, outputs)", f2_notebook_02)


# =========================================================================
# Fase 3 — Data Preparation (v2 corrigida)
# =========================================================================
section("Fase 3 — Data Preparation (v2 corrigida)")

def f3_modules():
    from src.data import mappings, cleaning, incidents, coverage  # noqa: F401
    from src.features import families, builders, outlier_calibration  # noqa: F401
    return True, "src.data.{mappings, cleaning, incidents, coverage} + src.features.{families, builders, outlier_calibration} OK"
try_check("Modulos da Fase 3 importam", f3_modules)


def f3_jsons():
    must = [
        "reports/eda_results/fase3a_diagnostico.json",
        "reports/eda_results/fase3b_outliers.json",
        "reports/eda_results/fase3c_build_report.json",
        "reports/eda_results/fase3d_validacao_cma.json",
        "reports/eda_results/fase3e_oem_split.json",
    ]
    miss = [p for p in must if not (PROJECT_ROOT / p).exists()]
    return (not miss, "OK" if not miss else f"missing: {miss}")
try_check("JSONs canonicos da Fase 3 existem", f3_jsons)


def f3_decisions_d029_d032():
    txt = (PROJECT_ROOT / "docs/decisions.md").read_text(encoding="utf-8")
    must_have = [
        "D029 — Janelas geradas apenas em ciclos `Operando`",
        "D030 — `target_lead_time_min` é alvo auxiliar",
        "D020 v2",
        "D031 — Limiar P99 de outlier calibrado externamente",
        "D032 — Flags de censura temporal",
    ]
    miss = [s for s in must_have if s not in txt]
    return not miss, "OK" if not miss else f"missing: {miss}"
try_check("decisions.md cobre D029, D030, D020 v2, D031, D032", f3_decisions_d029_d032)


def f3_audit_fase3a_md():
    p = PROJECT_ROOT / "docs/audit_fase3a.md"
    return p.exists(), f"size={p.stat().st_size if p.exists() else 0} bytes"
try_check("docs/audit_fase3a.md existe", f3_audit_fase3a_md)


def f3_features_md():
    p = PROJECT_ROOT / "docs/features.md"
    if not p.exists():
        return False, "ausente"
    txt = p.read_text(encoding="utf-8")
    keys = ["D029", "D030", "D031", "D032", "tem_telemetria", "target_lead_time_min", "lookback_completo"]
    miss = [k for k in keys if k not in txt]
    return not miss, "OK" if not miss else f"missing keys: {miss}"
try_check("docs/features.md completo (D029-D032 + flags)", f3_features_md)


def f3_outlier_calibration():
    p = PROJECT_ROOT / "data/processed/outlier_p99_thresholds.parquet"
    if not p.exists():
        return False, "ausente — rode src/features/outlier_calibration.py"
    df = pd.read_parquet(p)
    required = {"Alarme", "Tag_Frota", "p99", "n_obs"}
    miss = required - set(df.columns)
    ok = not miss and len(df) >= 100
    return ok, f"n_partitions={len(df)}, cols={list(df.columns)}"
try_check("outlier_p99_thresholds.parquet (D031)", f3_outlier_calibration)


def f3_features_dataset():
    must = [f"data/processed/features_2025-{m:02d}.parquet" for m in range(1, 7)]
    miss = [p for p in must if not (PROJECT_ROOT / p).exists()]
    return (not miss, f"OK: 6 parquets" if not miss else f"missing: {miss}")
try_check("Dataset materializado (6 meses)", f3_features_dataset)


# Carrega o dataset uma vez para os testes seguintes
df_full = None
def _load_df():
    global df_full
    if df_full is None:
        parquets = sorted((PROJECT_ROOT / "data/processed").glob("features_2025-*.parquet"))
        df_full = pd.concat([pd.read_parquet(p) for p in parquets], ignore_index=True)
    return df_full


def f3_dataset_total():
    df = _load_df()
    n = len(df)
    rep = json.loads((PROJECT_ROOT / "reports/eda_results/fase3c_build_report.json").read_text(encoding="utf-8"))
    n_rep = rep["totals"]["n_windows_total"]
    ok = n == n_rep == 321500
    return ok, f"parquet={n:,}, report={n_rep:,}, esperado=321,500"
try_check("Dataset v2: 321.500 janelas (parquet vs report)", f3_dataset_total)


def f3_fix1_operando():
    """Achado #1 corrigido — todas as janelas devem cair em Operando."""
    import duckdb
    df = _load_df()
    from src.data.loaders import load_apontamentos
    apt = load_apontamentos()
    apt["Inicio"] = pd.to_datetime(apt["Inicio"])
    apt["Fim"] = pd.to_datetime(apt["Fim"])
    con = duckdb.connect()
    con.register("d", df[["TAG", "t_window"]])
    con.register("a", apt[["Tag", "Inicio", "Fim", "Classe"]])
    res = con.sql("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN a.Classe='Operando' THEN 1 ELSE 0 END) AS in_op
        FROM d LEFT JOIN a
          ON a.Tag = d.TAG AND a.Inicio <= d.t_window AND a.Fim > d.t_window
    """).df().iloc[0]
    con.close()
    pct = res["in_op"] / res["total"] * 100
    ok = pct >= 99.5
    return ok, f"in_op/total = {res['in_op']:.0f}/{res['total']:.0f} = {pct:.2f}% (esperado >=99.5%)"
try_check("Fix #1: 99,5+% das janelas em Operando", f3_fix1_operando)


def f3_fix2_nan_no_tel():
    df = _load_df()
    no_tel = df[df["tem_telemetria"] == 0]
    n_evt_cols = [c for c in df.columns if c.startswith("n_evt_") and "raw" not in c]
    if len(no_tel) == 0:
        return True, "0 janelas com tem_telemetria=0 (caso degenerado, OK)"
    rates = [no_tel[c].isna().mean() for c in n_evt_cols]
    all_nan = all(r == 1.0 for r in rates)
    return all_nan, f"n_no_tel={len(no_tel)}, todas as n_evt_* NaN={all_nan}"
try_check("Fix #2: tem_telemetria=0 -> contagens NaN", f3_fix2_nan_no_tel)


def f3_fix3_lead_time_no_leak():
    df = _load_df()
    n_lead_y0 = ((df["target_lead_time_min"].notna()) & (df["y_dontgo_12h"] == 0)).sum()
    ok = n_lead_y0 == 0
    return ok, f"target_lead com y_12h=0: {n_lead_y0} (esperado 0)"
try_check("Fix #3: target_lead_time sem leak (y_12h=0 -> NaN)", f3_fix3_lead_time_no_leak)


def f3_fix4_schema():
    df = _load_df()
    n_count = sum(1 for c in df.columns if c.startswith("n_"))
    n_y = sum(1 for c in df.columns if c.startswith("y_"))
    n_lead = sum(1 for c in df.columns if c == "target_lead_time_min")
    ok = n_count == 66 and n_y == 6 and n_lead == 1
    return ok, f"n_*={n_count} (esperado 66), y_*={n_y} (6), lead={n_lead} (1), total cols={len(df.columns)}"
try_check("Fix #4: schema explicito (66 contagens / 6 labels / 1 lead)", f3_fix4_schema)


def f3_fix5_censura_flags():
    df = _load_df()
    has_lb = "lookback_completo" in df.columns
    has_lc = "label_completa_12h" in df.columns
    n_lb = int((df.get("lookback_completo", pd.Series([1])) == 0).sum()) if has_lb else -1
    n_lc = int((df.get("label_completa_12h", pd.Series([1])) == 0).sum()) if has_lc else -1
    ok = has_lb and has_lc and n_lb > 0 and n_lc > 0
    return ok, f"lookback_completo presente={has_lb} (n_zero={n_lb}), label_completa_12h presente={has_lc} (n_zero={n_lc})"
try_check("Fix #5: flags de censura presentes e nao-vazias", f3_fix5_censura_flags)


def f3_fix6_p99_external():
    """Verifica que o builder NAO usa approx_quantile global."""
    src = (PROJECT_ROOT / "src/features/builders.py").read_text(encoding="utf-8")
    has_global = "approx_quantile(Valor_num, 0.99) OVER" in src
    has_load = "load_p99_thresholds" in src
    ok = (not has_global) and has_load
    return ok, f"approx_quantile_global={has_global} (esperado False), load_p99_thresholds={has_load} (esperado True)"
try_check("Fix #6: P99 calibrado externamente (sem approx_quantile global)", f3_fix6_p99_external)


def f3_incidents_canonical():
    """A funcao apply_incidents_d009 ainda retorna 5025 incidentes / 19962 eventos."""
    from src.data.loaders import get_connection, load_telemetria_lazy
    from src.data.incidents import apply_incidents_d009, summarize_incidents
    con = get_connection()
    con.execute("PRAGMA disable_progress_bar")
    rel = load_telemetria_lazy(con)
    rel_with_start = apply_incidents_d009(rel, con=con, tol_min=30)
    summ = summarize_incidents(rel_with_start, con=con, tol_min=30)
    ok = summ.n_eventos_dontgo == 19962 and summ.n_incidentes == 5025
    return ok, f"eventos={summ.n_eventos_dontgo} (19962), incidentes={summ.n_incidentes} (5025)"
try_check("incidents.apply_incidents_d009: 19.962 / 5.025 (Fase 2C)", f3_incidents_canonical)


def f3_families_coverage():
    """Cobertura > 99% (so 'Other' < 1%)."""
    from src.features.families import family_of, FAMILY_NAMES
    from src.data.loaders import get_connection, load_telemetria_lazy
    con = get_connection()
    con.execute("PRAGMA disable_progress_bar")
    rel = load_telemetria_lazy(con)
    df = con.sql(f"SELECT Alarme, COUNT(*) AS n FROM ({rel.sql_query()}) WHERE Alarme IS NOT NULL GROUP BY ALL").df()
    df["fam"] = df["Alarme"].map(family_of)
    n_total = int(df["n"].sum())
    n_other = int(df.loc[df["fam"] == "Other", "n"].sum())
    pct_other = n_other / n_total * 100
    ok = pct_other < 1.0 and len(FAMILY_NAMES) == 15
    return ok, f"Other={pct_other:.3f}% (esperado <1%), familias={len(FAMILY_NAMES)} (15 com Other)"
try_check("Families: cobertura >99%, taxonomia D028 (15 familias com Other)", f3_families_coverage)


# =========================================================================
# Cross-checks: artigo vs JSONs
# =========================================================================
section("Cross-checks: artigo vs JSONs/parquets")

def cx_cap3_321500():
    """Cap 3 deve mencionar 321.500 (v2), nao 538.848 (v1 descartada)."""
    txt = (PROJECT_ROOT / "docs/article_dontgo/cap3_metodologia.tex").read_text(encoding="utf-8")
    has_v2 = "321.500" in txt
    has_v1 = "538.848" in txt and "538.848" not in "Total" not in txt[:txt.find("538.848")+20] if "538.848" in txt else False
    has_v1_ref = "538.848" in txt
    ok = has_v2 and not has_v1_ref
    return ok, f"contem '321.500'={has_v2}, ainda contem '538.848' (v1)={has_v1_ref}"
try_check("Cap 3 cita totais v2 (321.500) e nao mais v1 (538.848)", cx_cap3_321500)


def cx_cap3_no_73_features():
    """Cap 3 nao deve dizer '73 componentes'."""
    txt = (PROJECT_ROOT / "docs/article_dontgo/cap3_metodologia.tex").read_text(encoding="utf-8")
    bad = "73 componentes" in txt
    has_66 = "66" in txt and "feature" in txt.lower()
    return not bad and has_66, f"'73 componentes' no texto = {bad} (esperado False), menciona 66 features = {has_66}"
try_check("Cap 3 nao menciona '73 componentes' (errado)", cx_cap3_no_73_features)


def cx_cap4_321500():
    txt = (PROJECT_ROOT / "docs/article_dontgo/cap4_resultados.tex").read_text(encoding="utf-8")
    has_v2 = "321.500" in txt
    has_v1 = "538.848" in txt
    return has_v2 and not has_v1, f"contem '321.500'={has_v2}, contem '538.848' (v1)={has_v1}"
try_check("Cap 4 cita totais v2 (321.500) e nao mais v1", cx_cap4_321500)


def cx_pdf_compiles():
    p = PROJECT_ROOT / "docs/article_dontgo/TCC_DontGo.pdf"
    if not p.exists():
        return False, "PDF nao existe"
    size = p.stat().st_size
    ok = size > 100_000  # PDF razoavel
    return ok, f"size={size/1024:.1f} KB"
try_check("TCC_DontGo.pdf existe e tem tamanho razoavel", cx_pdf_compiles)


def cx_memory_v2():
    txt = (PROJECT_ROOT / "MEMORY.md").read_text(encoding="utf-8")
    has_v2_table = "321.500" in txt and "Estatísticas do dataset materializado (v2" in txt
    has_v1_descarte = "v1 foi descartado" in txt or "v1 descartado" in txt
    return has_v2_table and has_v1_descarte, f"tabela v2={has_v2_table}, marca v1 descartada={has_v1_descarte}"
try_check("MEMORY.md §12 reflete dataset v2 com nota de descarte v1", cx_memory_v2)


# =========================================================================
# Persistir relatorio
# =========================================================================
RESULTS["totals"] = {"n_pass": N_PASS, "n_fail": N_FAIL, "n_total": N_PASS + N_FAIL}
out = PROJECT_ROOT / "reports/eda_results/audit_fases_0_3.json"
out.write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False), encoding="utf-8")

section("RESUMO")
print(f"PASSA: {N_PASS}")
print(f"FALHA: {N_FAIL}")
print(f"TOTAL: {N_PASS + N_FAIL}")
print(f"Relatorio: {out}")
sys.exit(0 if N_FAIL == 0 else 1)
