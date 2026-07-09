"""Fase 2D — analise de features.

Cobre:
- Taxa de Is_Dont_Go por hora do dia, dia da semana, turno (H003).
- Taxa por Frota / Tipo / Classe (H004 — ja parcialmente em 2C).
- Heatmap de correlacao entre variaveis numericas (Valor_num, Id_Criticidade,
  Is_Dont_Go).
- Cobertura: telemetria.Alarme.unique() vs Eventos O&M.Name (catalogo CMA).
- Distribuicao de criticidade na telemetria geral.
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
from src.utils.paths import ALARMES_XLSX, FIGURES_DIR, REPORTS_DIR
from src.utils.seeds import set_global_seed

set_global_seed()
RESULTS: dict = {}
RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

con = get_connection()
rel = load_telemetria_lazy(con)
TEL = "(" + rel.sql_query() + ")"


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
print("Fase 2D — Analise de features")
print("=" * 72)

# -------------------------------------------------------------------------
# Taxa de Is_Dont_Go por hora / dia da semana / turno (H003)
# -------------------------------------------------------------------------
section("[2D.1] Taxa Is_Dont_Go por hora do dia (H003)")
por_hora = con.sql(
    f"""
    SELECT extract(hour FROM Data_Evento) AS hora,
           COUNT(*) AS n_eventos,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS taxa
    FROM {TEL}
    GROUP BY ALL
    ORDER BY hora
    """
).df()
por_hora["taxa_pct"] = por_hora["taxa"] * 100
print(por_hora)
RESULTS["taxa_dontgo_por_hora"] = por_hora.to_dict("records")

# Turno: 06-18 = diurno, 18-06 = noturno
por_hora["turno"] = np.where(
    (por_hora["hora"] >= 6) & (por_hora["hora"] < 18), "diurno", "noturno"
)
agreg_turno = (
    por_hora.groupby("turno")
    .agg(n_eventos=("n_eventos", "sum"), n_dontgo=("n_dontgo", "sum"))
    .reset_index()
)
agreg_turno["taxa"] = agreg_turno["n_dontgo"] / agreg_turno["n_eventos"]
agreg_turno["taxa_pct"] = agreg_turno["taxa"] * 100
print()
print("Por turno (06-18 diurno / 18-06 noturno):")
print(agreg_turno)
RESULTS["taxa_dontgo_por_turno"] = agreg_turno.to_dict("records")

# Por dia da semana
por_dow = con.sql(
    f"""
    SELECT extract(isodow FROM Data_Evento) AS dow,
           COUNT(*) AS n_eventos,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS taxa
    FROM {TEL}
    GROUP BY ALL
    ORDER BY dow
    """
).df()
por_dow["taxa_pct"] = por_dow["taxa"] * 100
nome_dow = {1: "Seg", 2: "Ter", 3: "Qua", 4: "Qui", 5: "Sex", 6: "Sab", 7: "Dom"}
por_dow["dow_nome"] = por_dow["dow"].map(nome_dow)
print()
print("Por dia da semana:")
print(por_dow)
RESULTS["taxa_dontgo_por_dow"] = por_dow.to_dict("records")

# Figuras
fig, axes = plt.subplots(2, 1, figsize=(10, 7))
axes[0].bar(por_hora["hora"], por_hora["taxa_pct"])
axes[0].set_title("Taxa Is_Dont_Go (%) por hora do dia")
axes[0].set_xlabel("Hora")
axes[0].set_ylabel("Taxa (%)")
axes[0].set_xticks(range(24))
axes[0].grid(alpha=0.3, axis="y")
# turnos sombreados
axes[0].axvspan(0, 6, alpha=0.08, color="navy")
axes[0].axvspan(18, 24, alpha=0.08, color="navy")
axes[1].bar(por_dow["dow_nome"], por_dow["taxa_pct"])
axes[1].set_title("Taxa Is_Dont_Go (%) por dia da semana")
axes[1].set_ylabel("Taxa (%)")
axes[1].grid(alpha=0.3, axis="y")
plt.tight_layout()
save_fig(fig, "fig06_taxa_por_hora_dow.png")

# -------------------------------------------------------------------------
# Taxa por Frota / Tipo / Classe (eventos)
# -------------------------------------------------------------------------
section("[2D.2] Taxa por Frota / Tipo / Classe")
por_frota_evt = con.sql(
    f"""
    SELECT Tag_Frota,
           COUNT(*) AS n_eventos,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS taxa,
           COUNT(DISTINCT TAG) AS n_equip
    FROM {TEL}
    GROUP BY ALL
    ORDER BY taxa DESC
    """
).df()
por_frota_evt["taxa_pct"] = por_frota_evt["taxa"] * 100
print("Por frota:")
print(por_frota_evt)
RESULTS["taxa_dontgo_por_frota"] = por_frota_evt.to_dict("records")

por_tipo_evt = con.sql(
    f"""
    SELECT Tipo,
           COUNT(*) AS n_eventos,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS taxa
    FROM {TEL}
    GROUP BY ALL
    ORDER BY taxa DESC
    """
).df()
por_tipo_evt["taxa_pct"] = por_tipo_evt["taxa"] * 100
print()
print("Por tipo:")
print(por_tipo_evt)
RESULTS["taxa_dontgo_por_tipo"] = por_tipo_evt.to_dict("records")

por_classe_evt = con.sql(
    f"""
    SELECT Classe,
           COUNT(*) AS n_eventos,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS taxa
    FROM {TEL}
    GROUP BY ALL
    ORDER BY taxa DESC
    """
).df()
por_classe_evt["taxa_pct"] = por_classe_evt["taxa"] * 100
print()
print("Por classe (Activate/Inactive):")
print(por_classe_evt)
RESULTS["taxa_dontgo_por_classe"] = por_classe_evt.to_dict("records")

por_crit_evt = con.sql(
    f"""
    SELECT Id_Criticidade, Criticidade,
           COUNT(*) AS n_eventos,
           SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
           1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) AS taxa
    FROM {TEL}
    GROUP BY ALL
    ORDER BY Id_Criticidade
    """
).df()
por_crit_evt["taxa_pct"] = por_crit_evt["taxa"] * 100
print()
print("Por criticidade:")
print(por_crit_evt)
RESULTS["taxa_dontgo_por_criticidade"] = por_crit_evt.to_dict("records")

# -------------------------------------------------------------------------
# Heatmap de correlacao (numericas)
# -------------------------------------------------------------------------
section("[2D.3] Correlacao entre numericas")
# Usar amostra para nao estourar memoria
sample_n = 500_000
df_corr = con.sql(
    f"""
    SELECT Id_Criticidade, Valor_num, Is_Dont_Go,
           extract(hour FROM Data_Evento) AS hora,
           extract(isodow FROM Data_Evento) AS dow,
           extract(month FROM Data_Evento) AS mes
    FROM {TEL}
    USING SAMPLE {sample_n} ROWS (RESERVOIR, 42)
    """
).df()
print(f"amostra para correlacao: {len(df_corr):,} linhas")
corr = df_corr.corr(numeric_only=True)
print(corr.round(3))
RESULTS["correlacao_numericas"] = corr.round(4).to_dict()

fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr.columns)))
ax.set_xticklabels(corr.columns, rotation=40, ha="right")
ax.set_yticks(range(len(corr.columns)))
ax.set_yticklabels(corr.columns)
for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        v = corr.values[i, j]
        ax.text(
            j, i, f"{v:.2f}", ha="center", va="center",
            color="white" if abs(v) > 0.5 else "black", fontsize=9,
        )
ax.set_title(f"Heatmap de correlacao (Pearson) — amostra {sample_n:,} linhas")
plt.colorbar(im, ax=ax, fraction=0.04, pad=0.04)
plt.tight_layout()
save_fig(fig, "fig05_heatmap_correlacao.png")

# -------------------------------------------------------------------------
# Cobertura: Alarme da telemetria vs Eventos O&M (T3.4)
# -------------------------------------------------------------------------
section("[2D.4] Cobertura: telemetria.Alarme vs Eventos O&M.Name")
om = pd.read_excel(ALARMES_XLSX, sheet_name="Eventos O&M")
print(f"Eventos O&M: {len(om):,} linhas, cols={list(om.columns)}")

# Coluna pode ter nome diferente — descobrir
name_col = None
for c in ["Name", "Nome", "Evento", "EVENT", "Evento_Nome"]:
    if c in om.columns:
        name_col = c
        break
if name_col is None:
    name_col = om.columns[0]
print(f"Coluna de nome usada: '{name_col}'")
om_names = set(om[name_col].dropna().astype(str).str.strip())
print(f"# nomes unicos no catalogo OEM: {len(om_names):,}")

tel_names = con.sql(
    f"SELECT DISTINCT Alarme FROM {TEL} WHERE Alarme IS NOT NULL"
).df()
tel_names_set = set(tel_names["Alarme"].astype(str).str.strip())
print(f"# alarmes distintos na telemetria: {len(tel_names_set):,}")

cobertos = tel_names_set & om_names
nao_cobertos = tel_names_set - om_names
print(f"alarmes da telemetria com match em O&M: {len(cobertos):,}")
print(f"alarmes da telemetria sem match (orfaos): {len(nao_cobertos):,}")
RESULTS["cobertura_alarmes_om"] = {
    "n_om_total": len(om_names),
    "n_telemetria_distintos": len(tel_names_set),
    "n_match": len(cobertos),
    "n_orfaos_telemetria": len(nao_cobertos),
    "pct_cobertura_telemetria": (
        100 * len(cobertos) / max(len(tel_names_set), 1)
    ),
    "exemplos_orfaos": sorted(list(nao_cobertos))[:30],
}
print(f"% cobertura: {RESULTS['cobertura_alarmes_om']['pct_cobertura_telemetria']:.1f}%")

# -------------------------------------------------------------------------
# Cobertura com catalogo CMA (regras Don't Go)
# -------------------------------------------------------------------------
section("[2D.5] Cobertura: alarmes do inicio de incidente vs catalogo CMA")
cma = pd.read_excel(ALARMES_XLSX, sheet_name="CMA")
print(f"CMA: {len(cma)} regras, cols={list(cma.columns)}")

evento_col = None
for c in ["EVENTO", "Evento", "EVENT", "Name"]:
    if c in cma.columns:
        evento_col = c
        break
if evento_col is None:
    evento_col = cma.columns[1]
print(f"Coluna evento usada: '{evento_col}'")
cma_eventos = set(cma[evento_col].dropna().astype(str).str.strip())
print(f"# eventos unicos no CMA: {len(cma_eventos)}")

# Carrega incidentes ja calculados
inc_csv = RESULTS_DIR / "incidentes_dontgo.csv"
if inc_csv.exists():
    inc = pd.read_csv(inc_csv)
    inicios = set(inc["alarme_inicio"].dropna().astype(str).str.strip().unique())
    print(f"alarmes distintos no inicio dos incidentes: {len(inicios)}")
    cobertos_cma = inicios & cma_eventos
    orfaos_cma = inicios - cma_eventos
    print(f"alarmes inicio com match em CMA: {len(cobertos_cma)}")
    print(f"alarmes inicio sem match em CMA: {len(orfaos_cma)}")
    if orfaos_cma:
        print("orfaos (10 primeiros):", sorted(list(orfaos_cma))[:10])
    RESULTS["cobertura_inicios_cma"] = {
        "n_inicios_distintos": len(inicios),
        "n_cma_total": len(cma_eventos),
        "n_match": len(cobertos_cma),
        "n_orfaos": len(orfaos_cma),
        "pct_match": 100 * len(cobertos_cma) / max(len(inicios), 1),
        "orfaos_amostra": sorted(list(orfaos_cma))[:30],
    }

# -------------------------------------------------------------------------
# Distribuicao geral de criticidade
# -------------------------------------------------------------------------
section("[2D.6] Distribuicao geral de criticidade")
dist_crit = con.sql(
    f"""
    SELECT Id_Criticidade, Criticidade,
           COUNT(*) AS n,
           100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS pct
    FROM {TEL}
    GROUP BY ALL
    ORDER BY Id_Criticidade
    """
).df()
print(dist_crit)
RESULTS["distribuicao_criticidade"] = dist_crit.to_dict("records")

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(dist_crit["Criticidade"].astype(str), dist_crit["n"] / 1e6)
ax.set_title("Distribuicao geral de criticidade na telemetria (37M eventos)")
ax.set_ylabel("Eventos (milhoes)")
plt.xticks(rotation=20, ha="right")
ax.grid(alpha=0.3, axis="y")
save_fig(fig, "fig05b_distribuicao_criticidade.png")

# -------------------------------------------------------------------------
# Persistir
# -------------------------------------------------------------------------
out = RESULTS_DIR / "fase2d_results.json"
out.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Fase 2D salva em {out}")
print("=" * 72)
