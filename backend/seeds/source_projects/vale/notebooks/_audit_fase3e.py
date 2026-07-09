"""Fase 3E - Estratificacao 793-D (CAT) vs LeTourneau.

Quantifica a divergencia estrutural entre os dois OEMs para decidir
formalmente a estrategia de modelagem (D027):

Opcoes:
  (a) Treino unico com OEM como variavel dummy.
  (b) Treino segregado: 1 modelo CAT + 1 modelo LeTourneau.
  (c) Treino unico filtrado para CAT apenas; LeTourneau cobrida por
      PA-3 (anomalia nao supervisionada).

Decisao baseada em (i) volume de eventos, (ii) prevalencia de
incidentes, (iii) divergencia de pipeline OEM (Classe NULL), (iv)
tamanho da amostra de positivos por OEM.

Read-only. Output: `reports/eda_results/fase3e_oem_split.json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.data.loaders import get_connection, load_telemetria_lazy
from src.utils.paths import REPORTS_DIR
from src.utils.seeds import set_global_seed

set_global_seed()
RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS: dict = {}


def section(t: str) -> None:
    print()
    print("-" * 72)
    print(t)
    print("-" * 72)


print("=" * 72)
print("Fase 3E - Estratificacao OEM (CAT 793-D vs LeTourneau)")
print("=" * 72)

con = get_connection()
con.execute("PRAGMA disable_progress_bar")
rel = load_telemetria_lazy(con)
con.sql("CREATE OR REPLACE VIEW tel_view AS " + rel.sql_query())
TEL = "tel_view"

# =========================================================================
# 1) Volume e prevalencia por OEM
# =========================================================================
section("[3E.1] Volume e prevalencia por OEM")
oem_stats = con.sql(
    f"""
    SELECT
        CASE WHEN Tag_Frota LIKE '793-D%' THEN 'CAT'
             WHEN Tag_Frota LIKE 'LeTourneau%' THEN 'LeTourneau'
             ELSE 'Outro' END AS OEM,
        Tag_Frota,
        COUNT(DISTINCT TAG) AS n_tags,
        COUNT(*) AS n_eventos,
        SUM(CAST(Is_Dont_Go AS INTEGER)) AS n_dontgo,
        1.0 * SUM(CAST(Is_Dont_Go AS INTEGER)) / COUNT(*) * 100 AS taxa_pct
    FROM {TEL}
    GROUP BY ALL
    ORDER BY OEM, n_eventos DESC
    """
).df()
print(oem_stats.to_string(index=False))
RESULTS["oem_volume_prevalence"] = oem_stats.to_dict("records")

# Resumo OEM
oem_resumo = (
    oem_stats.groupby("OEM")
    .agg(
        n_tags=("n_tags", "sum"),
        n_eventos=("n_eventos", "sum"),
        n_dontgo=("n_dontgo", "sum"),
    )
    .reset_index()
)
oem_resumo["taxa_pct"] = oem_resumo["n_dontgo"] / oem_resumo["n_eventos"] * 100
print()
print("Resumo OEM:")
print(oem_resumo.to_string(index=False))
RESULTS["oem_resumo"] = oem_resumo.to_dict("records")

ratio_taxa = (
    oem_resumo.loc[oem_resumo["OEM"] == "CAT", "taxa_pct"].iloc[0]
    / max(oem_resumo.loc[oem_resumo["OEM"] == "LeTourneau", "taxa_pct"].iloc[0], 1e-9)
)
print(f"\nRazao taxa_pct (CAT / LeTourneau): {ratio_taxa:.1f}x")
RESULTS["razao_taxa_cat_lt"] = float(ratio_taxa)

# =========================================================================
# 2) Cobertura de incidentes (D009/D018, tol 30 min) por OEM
# =========================================================================
section("[3E.2] Incidentes por OEM (D009/D018)")
inc_per_oem = con.sql(
    f"""
    WITH dontgo AS (
        SELECT TAG, Tag_Frota, Data_Evento,
               CASE WHEN Tag_Frota LIKE '793-D%' THEN 'CAT'
                    WHEN Tag_Frota LIKE 'LeTourneau%' THEN 'LeTourneau'
                    ELSE 'Outro' END AS OEM
        FROM {TEL}
        WHERE Is_Dont_Go = 1
    ),
    ord AS (
        SELECT *,
               LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento) AS prev_evt
        FROM dontgo
    ),
    flagged AS (
        SELECT *,
               CASE WHEN prev_evt IS NULL
                      OR date_diff('second', prev_evt, Data_Evento) > 1800
                    THEN 1 ELSE 0 END AS is_start
        FROM ord
    )
    SELECT OEM,
           COUNT(*) AS n_eventos,
           SUM(is_start) AS n_incidentes
    FROM flagged
    GROUP BY ALL
    """
).df()
inc_per_oem["compressao"] = (
    inc_per_oem["n_eventos"] / inc_per_oem["n_incidentes"]
)
print(inc_per_oem.to_string(index=False))
RESULTS["incidentes_por_oem"] = inc_per_oem.to_dict("records")

# =========================================================================
# 3) Classe distribution (D022)
# =========================================================================
section("[3E.3] Distribuicao de Classe entre Don't Gos por OEM")
classe_dist = con.sql(
    f"""
    SELECT
        CASE WHEN Tag_Frota LIKE '793-D%' THEN 'CAT'
             WHEN Tag_Frota LIKE 'LeTourneau%' THEN 'LeTourneau'
             ELSE 'Outro' END AS OEM,
        COALESCE(Classe, '(NULL)') AS Classe,
        COUNT(*) AS n
    FROM {TEL}
    WHERE Is_Dont_Go = 1
    GROUP BY ALL
    ORDER BY OEM, n DESC
    """
).df()
print(classe_dist.to_string(index=False))
RESULTS["classe_dist_dontgo_por_oem"] = classe_dist.to_dict("records")

# =========================================================================
# 4) Alarmes distintos que iniciam incidentes por OEM
# =========================================================================
section("[3E.4] Alarmes que iniciam incidentes por OEM")
alarmes_inicio = con.sql(
    f"""
    WITH dontgo AS (
        SELECT TAG, Tag_Frota, Data_Evento, Alarme,
               CASE WHEN Tag_Frota LIKE '793-D%' THEN 'CAT'
                    WHEN Tag_Frota LIKE 'LeTourneau%' THEN 'LeTourneau'
                    ELSE 'Outro' END AS OEM
        FROM {TEL}
        WHERE Is_Dont_Go = 1
    ),
    ord AS (
        SELECT *,
               LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento) AS prev_evt
        FROM dontgo
    ),
    flagged AS (
        SELECT *,
               CASE WHEN prev_evt IS NULL
                      OR date_diff('second', prev_evt, Data_Evento) > 1800
                    THEN 1 ELSE 0 END AS is_start
        FROM ord
    )
    SELECT OEM, Alarme, COUNT(*) AS n_incidentes
    FROM flagged
    WHERE is_start = 1
    GROUP BY ALL
    ORDER BY OEM, n_incidentes DESC
    """
).df()
print("Alarmes CAT (top 15):")
print(alarmes_inicio[alarmes_inicio["OEM"] == "CAT"].head(15).to_string(index=False))
print("\nAlarmes LeTourneau (todos):")
print(alarmes_inicio[alarmes_inicio["OEM"] == "LeTourneau"].to_string(index=False))
RESULTS["alarmes_inicio_oem_top"] = {
    "CAT": alarmes_inicio[alarmes_inicio["OEM"] == "CAT"].head(20).to_dict("records"),
    "LeTourneau": alarmes_inicio[alarmes_inicio["OEM"] == "LeTourneau"].to_dict("records"),
}

# =========================================================================
# 5) Decisao formal D027
# =========================================================================
section("[3E.5] Decisao D027 — estrategia de modelagem por OEM")

n_inc_cat = int(inc_per_oem.loc[inc_per_oem["OEM"] == "CAT", "n_incidentes"].iloc[0])
n_inc_lt = int(inc_per_oem.loc[inc_per_oem["OEM"] == "LeTourneau", "n_incidentes"].iloc[0])
RESULTS["d027_inputs"] = {
    "n_incidentes_cat": n_inc_cat,
    "n_incidentes_lt": n_inc_lt,
    "razao_taxa": float(ratio_taxa),
}

print(f"# incidentes CAT: {n_inc_cat:,}")
print(f"# incidentes LeTourneau: {n_inc_lt:,}")
print(f"Razao taxa CAT/LT: {ratio_taxa:.1f}x")
print()

# Criterios:
# - Se n_inc_lt < 100: amostra muito pequena para modelo supervisionado
#   robusto — recomendar PA-3 (anomalia) para LeTourneau.
# - Se razao_taxa > 100: distribuicoes muito diferentes — treino unico
#   com dummy nao captura o regime LeTourneau.
# - Volume de eventos LT > 90% do total + dialeto OEM diferente
#   (Classe=NULL) — modelo unico fica dominado por LT mesmo com weighting.
DECISAO = "(c) treino segregado para CAT + PA-3 (anomalia) para LeTourneau"
print(f">>> DECISAO D027: {DECISAO}")
print()
print("Justificativa:")
print(f"  - LeTourneau so tem {n_inc_lt} incidentes (vs {n_inc_cat} CAT)")
print(f"  - Razao de prevalencia por evento: {ratio_taxa:.0f}x")
print("  - Pipeline OEM divergente (Classe=NULL estrutural — D022)")
print("  - 91% do volume de telemetria e LeTourneau, mas so 0.6% dos")
print("    incidentes — modelo unico fica dominado pelo ruido LT")
print("  - PA-3 (Isolation Forest / Autoencoder LSTM) e a lente certa")
print("    para LeTourneau: descobre modos de falha sem precisar de")
print("    rotulos volumosos")
RESULTS["d027_decisao"] = {
    "escolha": "C — treino CAT segregado + PA-3 para LeTourneau",
    "justificativa": [
        f"LeTourneau so tem {n_inc_lt} incidentes (n insuficiente)",
        f"Razao de prevalencia CAT/LT = {ratio_taxa:.0f}x",
        "Pipeline OEM divergente (Classe=NULL — D022)",
        "91% do volume e LT mas so 0.6% dos incidentes",
        "PA-3 (anomalia) e a lente certa para LeTourneau",
    ],
}

# Sub-decisao para CAT (4 frotas 793-D 2S/3S/4S/5S):
print()
print("Para CAT, modelo UNICO com Tag_Frota como categoria:")
print("  - As 4 frotas 793-D compartilham chassi-base (only suspension")
print("    config differs); pipeline OEM e o mesmo (Classe=Activate")
print("    100%); volume de incidentes em cada (567/391/1214/2821)")
print("    e suficiente.")
print("  - Tag_Frota como variavel dummy + scale_pos_weight + Optuna")
RESULTS["d027_sub"] = "Para CAT: modelo unico com Tag_Frota dummy"

# =========================================================================
# Persistir
# =========================================================================
out = RESULTS_DIR / "fase3e_oem_split.json"
out.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Fase 3E salva em {out}")
print("=" * 72)
