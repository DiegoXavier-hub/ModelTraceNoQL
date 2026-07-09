"""Auditoria critica da Fase 2.

Auditorias 6-12: omissoes, testes formais, populacao total.
Roda sobre os parquets reais e produz reports/eda_results/audit_fase2.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from src.data.loaders import (
    get_connection,
    load_apontamentos,
    load_telemetria_lazy,
)
from src.utils.paths import ALARMES_XLSX, REPORTS_DIR

con = get_connection()
rel = load_telemetria_lazy(con)
TEL = "(" + rel.sql_query() + ")"

R: dict = {}


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


# =====================================================================
# AUDITORIA 6: NIVEL CMA — breakdown que faltava na Fase 2C
# =====================================================================
section("AUDITORIA 6: NIVEL CMA por incidente (FALTAVA na Fase 2)")
cma = pd.read_excel(ALARMES_XLSX, sheet_name="CMA")
cma_map = cma[["EVENTO", "NIVEL"]].drop_duplicates(subset=["EVENTO"])
cma_map.columns = ["alarme", "nivel_cma"]
con.register("cma_map", cma_map)

TOL = 30
sql_inc = f"""
WITH dontgo AS (
    SELECT TAG, Tag_Frota, Tipo, Data_Evento, Alarme, Criticidade
    FROM {TEL} WHERE Is_Dont_Go = 1
),
ord AS (
    SELECT *, LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento) AS prev,
           date_diff('second', LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento), Data_Evento) AS gap_s
    FROM dontgo
),
flagged AS (
    SELECT *, CASE WHEN prev IS NULL OR gap_s > {TOL}*60 THEN 1 ELSE 0 END AS is_start
    FROM ord
),
grouped AS (
    SELECT *, SUM(is_start) OVER (PARTITION BY TAG ORDER BY Data_Evento
                                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS inc_id
    FROM flagged
),
incidentes AS (
    SELECT TAG, Tag_Frota, Tipo, inc_id,
           MIN(Data_Evento) AS inicio,
           MIN(CASE WHEN is_start=1 THEN Alarme END) AS alarme_start,
           MIN(CASE WHEN is_start=1 THEN Criticidade END) AS crit_start,
           COUNT(*) AS n
    FROM grouped GROUP BY ALL
)
SELECT i.*, m.nivel_cma
FROM incidentes i LEFT JOIN cma_map m ON m.alarme = i.alarme_start
"""
inc = con.sql(sql_inc).df()

print(f"incidentes: {len(inc)}")
dist_nivel = inc["nivel_cma"].value_counts(dropna=False).to_dict()
print(f"\nDistribuicao por NIVEL CMA:\n{dist_nivel}")
R["nivel_cma_incidentes"] = {str(k): int(v) for k, v in dist_nivel.items()}

ct_frota_nivel = pd.crosstab(inc["Tag_Frota"], inc["nivel_cma"].fillna("SEM_MATCH"))
print(f"\nCross NIVEL CMA x Frota:\n{ct_frota_nivel}")
R["nivel_cma_x_frota"] = ct_frota_nivel.to_dict()

ct_nivel_crit = pd.crosstab(
    inc["nivel_cma"].fillna("SEM_MATCH"), inc["crit_start"]
)
print(f"\nCross NIVEL CMA x Criticidade do alarme inicial:\n{ct_nivel_crit}")
R["nivel_cma_x_crit"] = ct_nivel_crit.to_dict()


# =====================================================================
# AUDITORIA 7: H010 normalizado por volume mensal de telemetria
# =====================================================================
section("AUDITORIA 7: H010 — drift normalizado por volume de telemetria")
df = con.sql(
    f"""
    WITH inc_mes AS (
        SELECT date_trunc('month', i.inicio) AS mes, COUNT(*) AS n_inc
        FROM (
            SELECT TAG, Tag_Frota, MIN(Data_Evento) AS inicio
            FROM (
                SELECT *, SUM(CASE WHEN gap_s IS NULL OR gap_s > 30*60 THEN 1 ELSE 0 END)
                           OVER (PARTITION BY TAG ORDER BY Data_Evento
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS inc_id
                FROM (
                    SELECT TAG, Tag_Frota, Data_Evento,
                           date_diff('second',
                                     LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento),
                                     Data_Evento) AS gap_s
                    FROM {TEL} WHERE Is_Dont_Go = 1
                )
            ) GROUP BY TAG, Tag_Frota, inc_id
        ) i GROUP BY ALL
    ),
    vol_mes AS (
        SELECT date_trunc('month', Data_Evento) AS mes, COUNT(*) AS n_evt
        FROM {TEL} GROUP BY ALL
    )
    SELECT v.mes, v.n_evt, COALESCE(i.n_inc, 0) AS n_inc,
           1e6 * COALESCE(i.n_inc, 0) / v.n_evt AS inc_per_milhao_evt
    FROM vol_mes v LEFT JOIN inc_mes i ON v.mes = i.mes
    ORDER BY v.mes
    """
).df()
df["mes_str"] = df["mes"].dt.strftime("%Y-%m")
print(df[["mes_str", "n_evt", "n_inc", "inc_per_milhao_evt"]])
peak = df["inc_per_milhao_evt"].max()
vale = df["inc_per_milhao_evt"].min()
print(f"\npeak inc/M evt: {peak:.1f} (mes {df.loc[df['inc_per_milhao_evt'].idxmax(),'mes_str']})")
print(f"vale inc/M evt: {vale:.1f} (mes {df.loc[df['inc_per_milhao_evt'].idxmin(),'mes_str']})")
print(f"reducao peak->vale: {(1-vale/peak)*100:.1f}%")
R["h010_normalizado"] = df[["mes_str", "n_evt", "n_inc", "inc_per_milhao_evt"]].to_dict("records")


# =====================================================================
# AUDITORIA 8: H001 — taxa por mes (drift-aware)
# =====================================================================
section("AUDITORIA 8: H001 — taxa de Is_Dont_Go por mes")
df = con.sql(
    f"""
    SELECT date_trunc('month', Data_Evento) AS mes,
           COUNT(*) AS n,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           100.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS pct
    FROM {TEL} GROUP BY ALL ORDER BY mes
    """
).df()
df["mes_str"] = df["mes"].dt.strftime("%Y-%m")
print(df[["mes_str", "n", "n_dontgo", "pct"]])
print(f"\nrange: {df['pct'].min():.4f}% — {df['pct'].max():.4f}%")
print(f"razao max/min: {df['pct'].max()/df['pct'].min():.2f}x")
R["taxa_dontgo_por_mes"] = df[["mes_str","n","n_dontgo","pct"]].to_dict("records")


# =====================================================================
# AUDITORIA 9: H015 — distribuicao Id_Alarme por nome de Alarme
# =====================================================================
section("AUDITORIA 9: H015 — # Id_Alarme por nome de Alarme")
df = con.sql(
    f"""
    WITH per_alarme AS (
        SELECT Alarme, COUNT(DISTINCT Id_Alarme) AS n_ids
        FROM {TEL} WHERE Alarme IS NOT NULL
        GROUP BY Alarme
    )
    SELECT n_ids, COUNT(*) AS n_alarmes
    FROM per_alarme GROUP BY ALL ORDER BY n_ids
    """
).df()
print(df)
n_total = int(df["n_alarmes"].sum())
n_1 = int(df.loc[df["n_ids"] == 1, "n_alarmes"].sum())
n_gt1 = int(df.loc[df["n_ids"] > 1, "n_alarmes"].sum())
print(f"\ntotal alarmes: {n_total}")
print(f"alarmes com 1 Id: {n_1} ({100*n_1/n_total:.1f}%)")
print(f"alarmes com >1 Id: {n_gt1} ({100*n_gt1/n_total:.1f}%)")
R["h015_n_ids_distrib"] = df.to_dict("records")
R["h015_pct_unicos"] = float(100 * n_1 / n_total)


# =====================================================================
# AUDITORIA 10: H003 — chi-square formal
# =====================================================================
section("AUDITORIA 10: H003 — testes chi-square")
# Turno
df = con.sql(
    f"""
    SELECT
        CASE WHEN extract(hour FROM Data_Evento) BETWEEN 6 AND 17
             THEN 'diurno' ELSE 'noturno' END AS turno,
        Is_Dont_Go, COUNT(*) AS n
    FROM {TEL} GROUP BY ALL
    """
).df()
ct = df.pivot_table(index="turno", columns="Is_Dont_Go", values="n", aggfunc="sum").fillna(0)
print(f"\nTurno x Is_Dont_Go:\n{ct}")
chi2, p, dof, _ = chi2_contingency(ct)
print(f"chi2={chi2:.2f}  p={p:.3e}  dof={dof}")
R["h003_turno_chi2"] = {"chi2": float(chi2), "p": float(p), "dof": int(dof)}

df = con.sql(
    f"""
    SELECT extract(isodow FROM Data_Evento) AS dow, Is_Dont_Go, COUNT(*) AS n
    FROM {TEL} GROUP BY ALL
    """
).df()
ct = df.pivot_table(index="dow", columns="Is_Dont_Go", values="n", aggfunc="sum").fillna(0)
print(f"\nDOW x Is_Dont_Go:\n{ct}")
chi2, p, dof, _ = chi2_contingency(ct)
print(f"chi2={chi2:.2f}  p={p:.3e}  dof={dof}")
R["h003_dow_chi2"] = {"chi2": float(chi2), "p": float(p), "dof": int(dof)}


# =====================================================================
# AUDITORIA 11: Cramer V categoricas vs Is_Dont_Go
# =====================================================================
section("AUDITORIA 11: Cramer V para categoricas")


def cramers_v(ct):
    chi2, _, _, _ = chi2_contingency(ct)
    n = ct.sum().sum()
    r, c = ct.shape
    return float(np.sqrt(chi2 / (n * (min(r, c) - 1))))


cramer = {}
for var in ["Tag_Frota", "Tipo", "Classe", "Criticidade", "TAG"]:
    df = con.sql(
        f'SELECT "{var}" AS k, Is_Dont_Go, COUNT(*) AS n FROM {TEL} GROUP BY ALL'
    ).df()
    ct = df.pivot_table(index="k", columns="Is_Dont_Go", values="n", aggfunc="sum").fillna(0)
    v = cramers_v(ct)
    cramer[var] = {"cramers_v": v, "n_categorias": int(ct.shape[0])}
    print(f"  {var:15s}  V = {v:.4f}  ({ct.shape[0]} categorias)")
R["cramers_v"] = cramer


# =====================================================================
# AUDITORIA 12: H013 — % Operando sem telemetria — POPULACAO TOTAL
# =====================================================================
section("AUDITORIA 12: H013 — Operando sem telemetria (população total)")
apt = load_apontamentos(con)
apt_op = apt[apt["Classe"] == "Operando"].copy()
print(f"total ciclos Operando: {len(apt_op):,}")
con.register("apt_op_full", apt_op[["Id", "Tag", "Inicio", "Fim"]])

df = con.sql(
    f"""
    SELECT
        COUNT(*) AS n_ciclos,
        SUM(CASE WHEN n_evt = 0 THEN 1 ELSE 0 END) AS n_zero,
        100.0 * SUM(CASE WHEN n_evt = 0 THEN 1 ELSE 0 END) / COUNT(*) AS pct_zero,
        AVG(n_evt) AS media_evt,
        quantile_cont(n_evt, 0.5) AS mediana_evt
    FROM (
        SELECT a.Id,
            (SELECT COUNT(*) FROM {TEL} t
             WHERE t.TAG = a.Tag AND t.Data_Evento >= a.Inicio AND t.Data_Evento < a.Fim) AS n_evt
        FROM apt_op_full a
    )
    """
).df()
print(df.T)
R["h013_pop_total"] = df.iloc[0].to_dict()


# =====================================================================
# AUDITORIA 13: gaps grandes Apontamentos × Telemetria
# =====================================================================
section("AUDITORIA 13: TAGs com gap apontamentos vs telemetria > 7 dias")
df = con.sql(
    f"""
    WITH first_tel AS (
        SELECT TAG, MIN(Data_Evento) AS primeiro_evt FROM {TEL} GROUP BY TAG
    ),
    apt_tag AS (
        SELECT Tag, MIN(Inicio) AS primeiro_apt, COUNT(*) AS n_apt
        FROM apt_op_full GROUP BY Tag
    )
    SELECT a.Tag, a.primeiro_apt, t.primeiro_evt,
           date_diff('day', a.primeiro_apt, t.primeiro_evt) AS gap_d,
           a.n_apt
    FROM apt_tag a JOIN first_tel t ON t.TAG = a.Tag
    WHERE ABS(date_diff('day', a.primeiro_apt, t.primeiro_evt)) > 7
    ORDER BY gap_d DESC
    """
).df()
print(df)
R["tags_gap_grande"] = df.to_dict("records")


# Persistir
out = REPORTS_DIR / "eda_results" / "audit_fase2.json"
out.write_text(
    json.dumps(R, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
)
print(f"\n>>> Auditoria salva em {out}")
