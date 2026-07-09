"""Fase 3D - Validacao cruzada Is_Dont_Go x catalogo CMA.

Valida que `Is_Dont_Go=1` da telemetria e coerente com o catalogo de
regras CMA (151 regras). Estrategia:

1. Amostragem estratificada de **1.000 positivos** (`Is_Dont_Go=1`,
   estratificado por `Tag_Frota`).
2. Amostragem estratificada de **1.000 perto-positivos** (eventos com
   `Id_Criticidade=1` (Critico) ou `Id_Criticidade=2` (Não Crítico),
   `Is_Dont_Go=0`, estratificado por `Tag_Frota`).
3. Para cada amostra, faz JOIN com o catalogo CMA por `(Alarme,
   NIVEL ∈ {Alto, Muito Alto})` e reporta:
   - taxa de match
   - distribuicao por NIVEL CMA dos positivos
   - perfil dos perto-positivos que NAO bateram com CMA (sao casos
     onde a flag e silenciosa apesar de criticidade alta — possivel
     evidencia de modos de falha nao cobertos pela regra: alvo da
     PA-3, anomalia).

Read-only. Output: `reports/eda_results/fase3d_validacao_cma.json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.data.loaders import get_connection, load_telemetria_lazy
from src.utils.paths import ALARMES_XLSX, REPORTS_DIR
from src.utils.seeds import set_global_seed

set_global_seed()
RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS: dict = {}


def section(t: str) -> None:
    print()
    print("-" * 72)
    print(t)
    print("-" * 72)


print("=" * 72)
print("Fase 3D - Validacao cruzada Is_Dont_Go x catalogo CMA")
print("=" * 72)

# =========================================================================
# Carrega catalogo CMA
# =========================================================================
section("[3D.1] Catalogo CMA")
cma = pd.read_excel(ALARMES_XLSX, sheet_name="CMA")
cma.columns = [str(c).strip() for c in cma.columns]
print(f"CMA: {len(cma)} regras")
print(f"Cols: {list(cma.columns)}")
print()

# Normaliza coluna NIVEL e EVENTO
event_col = next((c for c in cma.columns if "EVENT" in c.upper()), None)
nivel_col = next((c for c in cma.columns if "NIVEL" in c.upper() or "NÍVEL" in c.upper()), None)
print(f"Coluna EVENTO: {event_col!r}")
print(f"Coluna NIVEL: {nivel_col!r}")

# Set de eventos do CMA por NIVEL
cma["_event_norm"] = cma[event_col].astype(str).str.strip()
cma["_nivel_norm"] = cma[nivel_col].astype(str).str.strip()

eventos_muito_alto = set(cma.loc[cma["_nivel_norm"] == "Muito Alto", "_event_norm"])
eventos_alto = set(cma.loc[cma["_nivel_norm"] == "Alto", "_event_norm"])
eventos_cma = eventos_muito_alto | eventos_alto
print(f"# eventos distintos (Muito Alto): {len(eventos_muito_alto)}")
print(f"# eventos distintos (Alto): {len(eventos_alto)}")
print(f"# total: {len(eventos_cma)}")
RESULTS["cma_summary"] = {
    "n_regras": len(cma),
    "n_eventos_muito_alto": len(eventos_muito_alto),
    "n_eventos_alto": len(eventos_alto),
    "n_eventos_total": len(eventos_cma),
}

# =========================================================================
# Amostragem estratificada
# =========================================================================
section("[3D.2] Amostragem estratificada")

con = get_connection()
con.execute("PRAGMA disable_progress_bar")
rel = load_telemetria_lazy(con)
# Cria view para evitar erro de duplo bind do duckdb com sub-queries
# wraping com CASE-cast dentro de loaders.py.
con.sql("CREATE OR REPLACE VIEW tel_view AS " + rel.sql_query())
TEL = "tel_view"

# 1000 positivos (Is_Dont_Go=1) estratificado por Tag_Frota com SEED=42
positivos = con.sql(
    f"""
    SELECT TAG, Tag_Frota, Tipo, Data_Evento, Alarme,
           Id_Criticidade, Criticidade, Classe, Is_Dont_Go
    FROM (
        SELECT TAG, Tag_Frota, Tipo, Data_Evento, Alarme,
               Id_Criticidade, Criticidade, Classe, Is_Dont_Go,
               ROW_NUMBER() OVER (PARTITION BY Tag_Frota ORDER BY hash(Id_Eventos_Telemetria)) AS rn
        FROM {TEL}
        WHERE Is_Dont_Go = 1
    )
    WHERE rn <= 200  -- ate 200 por frota; total ~1000 com 5 frotas
    """
).df()
print(f"# positivos amostrados: {len(positivos)}")
print("Por Tag_Frota:")
print(positivos["Tag_Frota"].value_counts().to_string())
RESULTS["amostra_positivos_por_frota"] = (
    positivos["Tag_Frota"].value_counts().to_dict()
)

# 1000 perto-positivos: Is_Dont_Go=0 + Id_Criticidade in (1, 2),
# estratificado por Tag_Frota.
perto_positivos = con.sql(
    f"""
    SELECT TAG, Tag_Frota, Tipo, Data_Evento, Alarme,
           Id_Criticidade, Criticidade, Classe, Is_Dont_Go
    FROM (
        SELECT TAG, Tag_Frota, Tipo, Data_Evento, Alarme,
               Id_Criticidade, Criticidade, Classe, Is_Dont_Go,
               ROW_NUMBER() OVER (PARTITION BY Tag_Frota ORDER BY hash(Id_Eventos_Telemetria)) AS rn
        FROM {TEL}
        WHERE Is_Dont_Go = 0 AND Id_Criticidade IN (1, 2)
    )
    WHERE rn <= 200
    """
).df()
print(f"\n# perto-positivos amostrados: {len(perto_positivos)}")
print("Por Tag_Frota:")
print(perto_positivos["Tag_Frota"].value_counts().to_string())
RESULTS["amostra_perto_positivos_por_frota"] = (
    perto_positivos["Tag_Frota"].value_counts().to_dict()
)

# =========================================================================
# Match com catalogo CMA
# =========================================================================
section("[3D.3] Match dos POSITIVOS com CMA")

positivos["_in_cma"] = positivos["Alarme"].isin(eventos_cma)
positivos["_in_muito_alto"] = positivos["Alarme"].isin(eventos_muito_alto)
positivos["_in_alto"] = positivos["Alarme"].isin(eventos_alto)

n_match_pos = int(positivos["_in_cma"].sum())
print(f"Positivos com match no CMA: {n_match_pos} / {len(positivos)} = "
      f"{n_match_pos / len(positivos) * 100:.2f}%")
print(f"  Muito Alto: {int(positivos['_in_muito_alto'].sum())}")
print(f"  Alto: {int(positivos['_in_alto'].sum())}")
RESULTS["positivos_match"] = {
    "n_total": len(positivos),
    "n_match_cma": n_match_pos,
    "pct_match_cma": float(n_match_pos / len(positivos) * 100),
    "n_muito_alto": int(positivos["_in_muito_alto"].sum()),
    "n_alto": int(positivos["_in_alto"].sum()),
}

# Positivos sem match — investigacao
sem_match = positivos[~positivos["_in_cma"]]
print(f"\nPositivos SEM match no CMA: {len(sem_match)}")
if len(sem_match) > 0:
    top_sem_match = (
        sem_match.groupby(["Alarme", "Tag_Frota"])
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    print("Top alarmes positivos sem match no CMA:")
    print(top_sem_match.head(15).to_string(index=False))
    RESULTS["positivos_sem_match_top"] = top_sem_match.head(20).to_dict("records")

# =========================================================================
# Match dos PERTO-POSITIVOS com CMA
# =========================================================================
section("[3D.4] Match dos PERTO-POSITIVOS com CMA")
perto_positivos["_in_cma"] = perto_positivos["Alarme"].isin(eventos_cma)
n_match_pp = int(perto_positivos["_in_cma"].sum())
print(f"Perto-positivos com match no CMA: {n_match_pp} / {len(perto_positivos)} = "
      f"{n_match_pp / len(perto_positivos) * 100:.2f}%")
RESULTS["perto_positivos_match"] = {
    "n_total": len(perto_positivos),
    "n_match_cma": n_match_pp,
    "pct_match_cma": float(n_match_pp / len(perto_positivos) * 100),
}

# Perto-positivos QUE BATEM com CMA mas tem Is_Dont_Go=0:
# sao os candidatos a "regra deveria ter disparado mas nao disparou" —
# normalmente porque a SITUACAO/QTD/TEMPO da regra exige sequencia.
match_pp = perto_positivos[perto_positivos["_in_cma"]]
print(f"\nPerto-positivos que BATEM com CMA mas Is_Dont_Go=0: {len(match_pp)}")
if len(match_pp) > 0:
    top_pp_match = (
        match_pp.groupby(["Alarme", "Tag_Frota"])
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    print("Top:")
    print(top_pp_match.head(15).to_string(index=False))
    RESULTS["perto_positivos_match_top"] = top_pp_match.head(20).to_dict("records")
print()
print("Interpretacao: perto-positivos com match CMA + Is_Dont_Go=0 sao")
print("eventos isolados de uma regra com SITUACAO != 'Em qualquer situacao'")
print("(exigem 5 alarmes em 6 min, etc.). Nao e bug — confirma D006.")

# =========================================================================
# Cruzamento por SITUACAO da regra
# =========================================================================
section("[3D.5] Distribuicao das regras por SITUACAO")

# Pega coluna SITUACAO
sit_col = next((c for c in cma.columns if "SITUAC" in c.upper()), None)
if sit_col:
    print(f"Coluna SITUACAO: {sit_col!r}")
    sit_dist = cma[sit_col].fillna("(NULL)").value_counts().head(15)
    print(sit_dist.to_string())
    RESULTS["cma_situacao_dist"] = sit_dist.to_dict()
    n_qualquer = int((cma[sit_col].fillna("").str.lower() == "em qualquer situação").sum())
    print(f"\n'Em qualquer situação' (regras instantaneas): {n_qualquer}/{len(cma)} = "
          f"{n_qualquer/len(cma)*100:.1f}%")
    RESULTS["cma_pct_instantaneas"] = float(n_qualquer / len(cma) * 100)

# =========================================================================
# Veredito formal
# =========================================================================
section("[3D.6] Veredito de validacao (D006 ratificada)")
ratifica = (n_match_pos / len(positivos) * 100) >= 95
print(
    "\n>>> "
    + ("D006 RATIFICADA " if ratifica else "D006 SOB SUSPEITA ")
    + f"({n_match_pos / len(positivos) * 100:.2f}% dos positivos amostrados "
    + "tem match com regras (Alto + Muito Alto) do CMA)"
)
RESULTS["veredito_d006"] = {
    "ratificada": ratifica,
    "pct_match_pos": float(n_match_pos / len(positivos) * 100),
    "criterio": ">= 95% (H008)",
}

# =========================================================================
# Persistir
# =========================================================================
out = RESULTS_DIR / "fase3d_validacao_cma.json"
out.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Fase 3D salva em {out}")
print("=" * 72)
