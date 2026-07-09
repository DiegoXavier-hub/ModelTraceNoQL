"""Fase 2C — analise da variavel alvo (Is_Dont_Go), incidentes D009.

Calcula:
- Taxa empirica global (H001).
- Gaps entre Don't Gos consecutivos do mesmo equipamento (refina D009).
- Incidentes (sequencias maximais com gap <= tolerancia).
- Distribuicao de Don't Gos e incidentes por TAG, Tag_Frota, Tipo, mes,
  Criticidade, Alarme.
- Serie temporal de incidentes (Figura 4).

Salva resultados em reports/eda_results/fase2c_results.json e figuras
em reports/figures/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data.loaders import get_connection, load_telemetria_lazy
from src.utils.paths import FIGURES_DIR, REPORTS_DIR
from src.utils.seeds import set_global_seed

set_global_seed()
RESULTS: dict = {}
RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

con = get_connection()
rel_tel = load_telemetria_lazy(con)
TEL = "(" + rel_tel.sql_query() + ")"


def section(t: str) -> None:
    print()
    print("-" * 72)
    print(t)
    print("-" * 72)


def save_fig(fig, name: str) -> Path:
    p = FIGURES_DIR / name
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  ! figure saved: {p.name}")
    return p


print("=" * 72)
print("Fase 2C — Analise da variavel alvo")
print("=" * 72)

# -------------------------------------------------------------------------
# H001 — taxa empirica de Is_Dont_Go
# -------------------------------------------------------------------------
section("[2C.1] Taxa empirica global de Is_Dont_Go (H001)")
taxa = con.sql(
    f"""
    SELECT COUNT(*) AS n_total,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS taxa
    FROM {TEL}
    """
).df().iloc[0]
RESULTS["taxa_is_dont_go"] = {
    "n_total": int(taxa["n_total"]),
    "n_dontgo": int(taxa["n_dontgo"]),
    "taxa": float(taxa["taxa"]),
    "taxa_pct": float(taxa["taxa"] * 100),
}
print(f"n_total = {int(taxa['n_total']):,}")
print(f"n_dontgo = {int(taxa['n_dontgo']):,}")
print(f"taxa = {float(taxa['taxa']):.6%}  (= {float(taxa['taxa']):.2e})")
print(
    "H001 (< 0.1%): "
    + ("CONFIRMADA" if taxa["taxa"] < 0.001 else "REFUTADA")
)

# -------------------------------------------------------------------------
# Distribuicao de gaps entre Don't Gos consecutivos do mesmo equipamento
# -------------------------------------------------------------------------
section("[2C.2] Distribuicao de gaps entre Don't Gos consecutivos por equipamento")
gaps = con.sql(
    f"""
    WITH dontgo AS (
        SELECT TAG, Data_Evento
        FROM {TEL}
        WHERE Is_Dont_Go = 1
    ),
    ord AS (
        SELECT TAG, Data_Evento,
               LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento) AS prev
        FROM dontgo
    )
    SELECT TAG, Data_Evento,
           date_diff('second', prev, Data_Evento) AS gap_s,
           date_diff('second', prev, Data_Evento) / 60.0 AS gap_min
    FROM ord
    WHERE prev IS NOT NULL
    """
).df()
print(f"pares (don't go anterior, don't go atual) do mesmo equipamento: {len(gaps):,}")
print()
print("Distribuicao do gap em minutos:")
desc = gaps["gap_min"].describe(percentiles=[0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
print(desc)
RESULTS["dontgo_gap_min_describe"] = {k: float(v) for k, v in desc.items()}

# Quantos pares teriam mesmo incidente sob diferentes tolerancias?
for tol_min in [5, 10, 15, 30, 60, 120, 240, 480, 1440]:
    pct = (gaps["gap_min"] <= tol_min).mean() * 100
    print(f"  tol={tol_min} min  -> {(gaps['gap_min']<=tol_min).sum():,} pares ({pct:.2f}%)")
    RESULTS.setdefault("frac_pares_dentro_tol", {})[str(tol_min)] = float(pct)

# Histograma do gap em escala log
fig, ax = plt.subplots(figsize=(9, 4))
gaps_pos = gaps[gaps["gap_min"] > 0]["gap_min"]
ax.hist(np.clip(gaps_pos, 1e-2, 1440 * 2), bins=80)
ax.set_xscale("log")
ax.set_xlabel("Gap entre Don't Gos consecutivos do mesmo equipamento (min, log)")
ax.set_ylabel("Frequencia")
ax.set_title("Distribuicao de gaps — refina tolerancia D009 (defaut: 30 min)")
ax.axvline(30, color="red", linestyle="--", label="D009: 30 min")
ax.legend()
ax.grid(alpha=0.3)
save_fig(fig, "fig02_gaps_dontgo_consec.png")

# -------------------------------------------------------------------------
# Identificar incidentes (D009) com tolerancia 30 min
# -------------------------------------------------------------------------
section("[2C.3] Incidentes Don't Go (D009, tol=30 min)")
TOL_MIN = 30

# Marcar inicio de incidente: gap > tolerancia OU primeiro Don't Go do equip.
incidentes_full = con.sql(
    f"""
    WITH dontgo AS (
        SELECT TAG, Tag_Frota, Tipo, Data_Evento, Alarme, Id_Criticidade, Criticidade
        FROM {TEL}
        WHERE Is_Dont_Go = 1
    ),
    ord AS (
        SELECT *,
               LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento) AS prev,
               date_diff('second', LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento), Data_Evento) AS gap_s
        FROM dontgo
    ),
    flagged AS (
        SELECT *,
               CASE WHEN prev IS NULL OR gap_s > {TOL_MIN}*60 THEN 1 ELSE 0 END AS is_incident_start
        FROM ord
    ),
    grouped AS (
        SELECT *,
               SUM(is_incident_start) OVER (PARTITION BY TAG ORDER BY Data_Evento
                                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS incident_id
        FROM flagged
    )
    -- alarme_inicio e crit_inicio usam MIN(CASE WHEN is_start=1) para
    -- garantir que o valor vem do EVENTO de inicio do incidente. Versao
    -- com ANY_VALUE funcionou por coincidencia da implementacao do duckdb,
    -- mas nao e garantida pelo padrao SQL.
    SELECT TAG, Tag_Frota, Tipo, incident_id,
           MIN(Data_Evento) AS inicio_inc,
           MAX(Data_Evento) AS fim_inc,
           COUNT(*) AS n_eventos_no_incidente,
           MIN(CASE WHEN is_incident_start=1 THEN Alarme END) AS alarme_inicio,
           MIN(CASE WHEN is_incident_start=1 THEN Criticidade END) AS crit_inicio
    FROM grouped
    GROUP BY ALL
    ORDER BY TAG, inicio_inc
    """
).df()
RESULTS["incidentes"] = {
    "n_eventos_dontgo": int(taxa["n_dontgo"]),
    "n_incidentes_30min": int(len(incidentes_full)),
    "tolerancia_min": TOL_MIN,
    "compressao": (
        float(taxa["n_dontgo"]) / max(len(incidentes_full), 1)
    ),
}
print(f"eventos Is_Dont_Go=1: {int(taxa['n_dontgo']):,}")
print(f"incidentes (tol=30 min): {len(incidentes_full):,}")
print(
    f"compressao media (eventos/incidente): "
    f"{float(taxa['n_dontgo'])/max(len(incidentes_full),1):.2f}"
)

# distribuicao do nº de eventos por incidente
desc_eventos_inc = incidentes_full["n_eventos_no_incidente"].describe(
    percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]
)
print()
print("eventos por incidente:")
print(desc_eventos_inc)
RESULTS["eventos_por_incidente_describe"] = {
    k: float(v) for k, v in desc_eventos_inc.items()
}

# duracao do incidente
incidentes_full["duracao_min"] = (
    pd.to_datetime(incidentes_full["fim_inc"])
    - pd.to_datetime(incidentes_full["inicio_inc"])
).dt.total_seconds() / 60
desc_dur = incidentes_full["duracao_min"].describe(
    percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]
)
print()
print("duracao do incidente (min):")
print(desc_dur)
RESULTS["duracao_incidente_describe"] = {k: float(v) for k, v in desc_dur.items()}

# salvar a tabela completa de incidentes
incidentes_full.to_csv(RESULTS_DIR / "incidentes_dontgo.csv", index=False)
print(f"\ntabela completa de incidentes salva: {RESULTS_DIR / 'incidentes_dontgo.csv'}")

# -------------------------------------------------------------------------
# Distribuicao de incidentes por dimensao
# -------------------------------------------------------------------------
section("[2C.4] Distribuicao de incidentes por dimensao")

por_tag = (
    incidentes_full.groupby("TAG")
    .size()
    .reset_index(name="n_incidentes")
    .sort_values("n_incidentes", ascending=False)
)
print(f"por TAG (35 equipamentos): top 10:")
print(por_tag.head(10))
RESULTS["incidentes_por_tag_top"] = por_tag.head(15).to_dict("records")

por_frota = (
    incidentes_full.groupby("Tag_Frota")
    .size()
    .reset_index(name="n_incidentes")
    .sort_values("n_incidentes", ascending=False)
)
print(f"\npor Tag_Frota:")
print(por_frota)
RESULTS["incidentes_por_frota"] = por_frota.to_dict("records")

por_tipo = (
    incidentes_full.groupby("Tipo")
    .size()
    .reset_index(name="n_incidentes")
    .sort_values("n_incidentes", ascending=False)
)
print(f"\npor Tipo:")
print(por_tipo)
RESULTS["incidentes_por_tipo"] = por_tipo.to_dict("records")

# por mes
incidentes_full["mes"] = (
    pd.to_datetime(incidentes_full["inicio_inc"]).dt.to_period("M").astype(str)
)
por_mes = (
    incidentes_full.groupby("mes")
    .size()
    .reset_index(name="n_incidentes")
    .sort_values("mes")
)
print(f"\npor mes:")
print(por_mes)
RESULTS["incidentes_por_mes"] = por_mes.to_dict("records")

# por alarme
por_alarme = (
    incidentes_full.groupby("alarme_inicio")
    .size()
    .reset_index(name="n")
    .sort_values("n", ascending=False)
)
print(f"\nalarmes mais comuns no inicio dos incidentes (top 15):")
print(por_alarme.head(15))
RESULTS["incidentes_por_alarme_top"] = por_alarme.head(20).to_dict("records")

# por criticidade
por_crit = (
    incidentes_full.groupby("crit_inicio")
    .size()
    .reset_index(name="n")
    .sort_values("n", ascending=False)
)
print(f"\npor criticidade no inicio:")
print(por_crit)
RESULTS["incidentes_por_criticidade"] = por_crit.to_dict("records")

# -------------------------------------------------------------------------
# Figuras
# -------------------------------------------------------------------------
section("[2C.5] Figuras")

# Distribuicao por TAG (top 20)
fig, ax = plt.subplots(figsize=(9, 5))
top = por_tag.head(20).iloc[::-1]
ax.barh(top["TAG"], top["n_incidentes"])
ax.set_xlabel("Numero de incidentes (jan-jun 2025)")
ax.set_title("Top 20 equipamentos por # de incidentes Don't Go")
ax.grid(alpha=0.3, axis="x")
save_fig(fig, "fig03_incidentes_por_tag.png")

# Por frota
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(por_frota["Tag_Frota"], por_frota["n_incidentes"])
ax.set_ylabel("# incidentes")
ax.set_title("Incidentes Don't Go por modelo de frota")
plt.xticks(rotation=20, ha="right")
ax.grid(alpha=0.3, axis="y")
save_fig(fig, "fig03_incidentes_por_frota.png")

# Por mes
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(por_mes["mes"], por_mes["n_incidentes"])
ax.set_ylabel("# incidentes")
ax.set_xlabel("Mes")
ax.set_title("Incidentes Don't Go por mes")
ax.grid(alpha=0.3, axis="y")
save_fig(fig, "fig03_incidentes_por_mes.png")

# Por alarme (top 15)
fig, ax = plt.subplots(figsize=(10, 6))
top_a = por_alarme.head(15).iloc[::-1]
ax.barh(top_a["alarme_inicio"], top_a["n"])
ax.set_xlabel("# incidentes")
ax.set_title("Top 15 alarmes que iniciaram incidentes Don't Go")
ax.grid(alpha=0.3, axis="x")
save_fig(fig, "fig03_incidentes_por_alarme.png")

# Serie temporal por dia de incidentes
inc_por_dia = (
    pd.to_datetime(incidentes_full["inicio_inc"]).dt.floor("D")
    .value_counts()
    .sort_index()
    .reset_index(name="n")
)
inc_por_dia.columns = ["dia", "n"]
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(inc_por_dia["dia"], inc_por_dia["n"], lw=1.2)
ax.fill_between(inc_por_dia["dia"], inc_por_dia["n"], alpha=0.3)
ax.set_title("Serie temporal de incidentes Don't Go por dia (jan-jun 2025)")
ax.set_xlabel("Data")
ax.set_ylabel("# incidentes/dia")
ax.grid(alpha=0.3)
save_fig(fig, "fig04_serie_temporal_incidentes.png")

# -------------------------------------------------------------------------
# Persistir
# -------------------------------------------------------------------------
out = RESULTS_DIR / "fase2c_results.json"
out.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Fase 2C salva em {out}")
print("=" * 72)
