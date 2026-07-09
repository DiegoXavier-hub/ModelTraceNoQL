"""Fase 3A.1 - Diagnostico populacional.

Quantifica os 4 problemas a tratar antes da limpeza/feature engineering:
  1. Encoding mojibake em Criticidade (e em outras colunas string).
  2. Inconsistencias temporais nos apontamentos (Inicio>Fim, duracao=0,
     duracao<0, sobreposicao entre ciclos do mesmo Tag).
  3. H013 estratificada na populacao: % de ciclos `Operando` sem telemetria
     por mes x Tag_Frota x bucket de hora (madrugada/manha/tarde/noite).
  4. Validacao do mapping `Tag_Frota -> Porte` contra `desenvolver_dontgo.xlsx`.

Read-only: escreve apenas em reports/eda_results/fase3a_diagnostico.json
e gera figura `reports/figures/fig07a_h013_por_mes_frota_hora.png`.

Princípio governante: ROBUSTEZ > custo computacional.
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

from src.data.loaders import (
    get_connection,
    load_apontamentos,
    load_telemetria_lazy,
)
from src.utils.paths import (
    APONTAMENTOS_PARQUET,
    DONTGO_EXAMPLE_XLSX,
    FIGURES_DIR,
    REPORTS_DIR,
)
from src.utils.seeds import set_global_seed

set_global_seed()

RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
RESULTS: dict = {}


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
print("Fase 3A.1 - Diagnostico populacional pre-limpeza")
print("=" * 72)

con = get_connection()
rel_tel = load_telemetria_lazy(con)
TEL = "(" + rel_tel.sql_query() + ")"

# =========================================================================
# 1) Encoding mojibake em Criticidade (e em outras colunas string)
# =========================================================================
section("[3A.1.1] Encoding mojibake em Criticidade")

VALORES_CRIT_VALIDOS = ("Critico", "Não Crítico", "Informacional", "Outros")

crit_dist = con.sql(
    f"""
    SELECT Criticidade, COUNT(*) AS n
    FROM {TEL}
    GROUP BY ALL
    ORDER BY n DESC
    """
).df()
print("Valores distintos em Criticidade (TODOS):")
print(crit_dist.to_string(index=False))
RESULTS["criticidade_distinct_full"] = crit_dist.to_dict("records")

# Identifica linhas com mojibake (qualquer valor fora dos 4 oficiais).
mojibake_mask = ~crit_dist["Criticidade"].isin(list(VALORES_CRIT_VALIDOS))
mojibake_rows = crit_dist[mojibake_mask]
RESULTS["criticidade_mojibake"] = mojibake_rows.to_dict("records")
n_mojibake = int(mojibake_rows["n"].sum()) if not mojibake_rows.empty else 0
print(f"\n>>> Linhas com Criticidade fora do dominio oficial: {n_mojibake:,}")
if n_mojibake > 0:
    print("\n  Bytes (hex) dos valores anomalos:")
    for raw in mojibake_rows["Criticidade"].tolist():
        if raw is None:
            print(f"    None: (NULL real)")
            continue
        as_bytes = raw.encode("utf-8", errors="replace")
        print(f"    {raw!r:<40s} bytes = {as_bytes.hex(' ')}")

# Caracterizar os mojibake: cruzar com Tag_Frota, mes, alarme.
if n_mojibake > 0:
    mojibake_lit = ", ".join(
        f"'{v}'" for v in mojibake_rows["Criticidade"].dropna().tolist()
    )
    mojibake_detail = con.sql(
        f"""
        SELECT
            Tag_Frota,
            strftime(Data_Evento, '%Y-%m') AS mes,
            Criticidade,
            Id_Criticidade,
            COUNT(*) AS n
        FROM {TEL}
        WHERE Criticidade IN ({mojibake_lit})
        GROUP BY ALL
        ORDER BY n DESC
        """
    ).df()
    print("\n  Estratificacao das linhas mojibake:")
    print(mojibake_detail.to_string(index=False))
    RESULTS["criticidade_mojibake_detail"] = mojibake_detail.to_dict("records")
    # Mapeamento mojibake -> Id_Criticidade (canonico) para reconstruir o
    # valor correto pela chave numerica que NAO sofre encoding.
    map_via_id = con.sql(
        f"""
        SELECT Id_Criticidade,
               Criticidade,
               COUNT(*) AS n
        FROM {TEL}
        WHERE Id_Criticidade IS NOT NULL
        GROUP BY ALL
        ORDER BY Id_Criticidade, n DESC
        """
    ).df()
    print("\n  Map Id_Criticidade -> Criticidade (TODOS os valores observados):")
    print(map_via_id.to_string(index=False))
    RESULTS["id_criticidade_to_criticidade"] = map_via_id.to_dict("records")

# =========================================================================
# 2) Inconsistencias temporais nos apontamentos
# =========================================================================
section("[3A.1.2] Inconsistencias temporais nos apontamentos")

apt = load_apontamentos(con)
apt["Inicio"] = pd.to_datetime(apt["Inicio"])
apt["Fim"] = pd.to_datetime(apt["Fim"])
apt["dur_min"] = (apt["Fim"] - apt["Inicio"]).dt.total_seconds() / 60

n = len(apt)
RESULTS["apontamentos_total"] = n
print(f"Apontamentos totais: {n:,}")

# 2.1 - Inicio > Fim
inicio_gt_fim = apt[apt["Inicio"] > apt["Fim"]]
print(f"\n2.1) Inicio > Fim: {len(inicio_gt_fim):,} ({len(inicio_gt_fim)/n*100:.4f}%)")
RESULTS["inicio_gt_fim"] = {
    "n": int(len(inicio_gt_fim)),
    "pct": float(len(inicio_gt_fim) / n * 100),
}
if len(inicio_gt_fim) > 0:
    sample = inicio_gt_fim.head(10).copy()
    print(sample[["Id", "Tag", "Inicio", "Fim", "dur_min", "Classe"]].to_string(index=False))
    RESULTS["inicio_gt_fim_sample"] = sample.head(10).astype(str).to_dict("records")

# 2.2 - duracao zero (Inicio == Fim)
dur_zero = apt[apt["dur_min"] == 0]
print(f"\n2.2) Inicio == Fim (dur=0): {len(dur_zero):,} ({len(dur_zero)/n*100:.4f}%)")
RESULTS["duracao_zero"] = {
    "n": int(len(dur_zero)),
    "pct": float(len(dur_zero) / n * 100),
}
if len(dur_zero) > 0:
    print("  Distribuicao por Classe:")
    print(dur_zero["Classe"].value_counts().to_string())
    RESULTS["duracao_zero_por_classe"] = (
        dur_zero["Classe"].value_counts().to_dict()
    )

# 2.3 - duracao negativa (Inicio > Fim)
dur_neg = apt[apt["dur_min"] < 0]
RESULTS["duracao_negativa"] = {
    "n": int(len(dur_neg)),
    "pct": float(len(dur_neg) / n * 100),
}
print(f"\n2.3) duracao < 0 min: {len(dur_neg):,} ({len(dur_neg)/n*100:.4f}%)")

# 2.4 - duracao MUITO grande (sentinela de bug do pipeline)
dur_huge = apt[apt["dur_min"] > 24 * 60 * 30]  # > 30 dias
print(f"\n2.4) duracao > 30 dias: {len(dur_huge):,}")
RESULTS["duracao_maior_30dias"] = int(len(dur_huge))

# 2.5 - sobreposicao entre ciclos do mesmo Tag
section("[3A.1.2.5] Sobreposicao entre ciclos do mesmo Tag")
apt_sorted = apt.sort_values(["Tag", "Inicio"]).reset_index(drop=True)
apt_sorted["Fim_anterior"] = apt_sorted.groupby("Tag")["Fim"].shift()
apt_sorted["Inicio_anterior"] = apt_sorted.groupby("Tag")["Inicio"].shift()
apt_sorted["Classe_anterior"] = apt_sorted.groupby("Tag")["Classe"].shift()
apt_sorted["overlap"] = (
    apt_sorted["Inicio"] < apt_sorted["Fim_anterior"]
).fillna(False)
apt_sorted["overlap_min"] = (
    apt_sorted["Fim_anterior"] - apt_sorted["Inicio"]
).dt.total_seconds() / 60
apt_sorted.loc[~apt_sorted["overlap"], "overlap_min"] = np.nan

n_overlap = int(apt_sorted["overlap"].sum())
print(f"Pares (anterior, atual) do mesmo Tag com sobreposicao: {n_overlap:,} ({n_overlap/n*100:.4f}%)")
RESULTS["overlap_total"] = {
    "n": n_overlap,
    "pct": float(n_overlap / n * 100),
}

if n_overlap > 0:
    overlap_desc = apt_sorted.loc[apt_sorted["overlap"], "overlap_min"].describe(
        percentiles=[0.5, 0.9, 0.95, 0.99]
    )
    print("\n  Distribuicao da sobreposicao em min:")
    print(overlap_desc.to_string())
    RESULTS["overlap_describe_min"] = {k: float(v) for k, v in overlap_desc.items()}

    # Cruzamento com (Classe_anterior, Classe) para descobrir padrao
    sob_por_par = (
        apt_sorted.loc[apt_sorted["overlap"]]
        .groupby(["Classe_anterior", "Classe"])
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    print("\n  Top combinacoes (Classe_anterior, Classe) sob sobreposicao:")
    print(sob_por_par.head(15).to_string(index=False))
    RESULTS["overlap_por_par_classe_top"] = sob_por_par.head(20).to_dict("records")

# =========================================================================
# 3) H013 estratificada (mes x Tag_Frota x bucket de hora) na populacao
# =========================================================================
section("[3A.1.3] H013 estratificada (Operando sem telemetria)")

# Construir tabela de ciclos Operando.
operando = apt_sorted[apt_sorted["Classe"] == "Operando"].copy()
operando["mes"] = operando["Inicio"].dt.to_period("M").astype(str)
operando["hora"] = operando["Inicio"].dt.hour
def hora_bucket(h: int) -> str:
    if 0 <= h < 6:
        return "00-06_madrugada"
    if 6 <= h < 12:
        return "06-12_manha"
    if 12 <= h < 18:
        return "12-18_tarde"
    return "18-24_noite"

operando["bucket"] = operando["hora"].map(hora_bucket)

# Para cada ciclo Operando, conta # eventos de telemetria em [Inicio, Fim]
# com mesmo TAG. Faz em duckdb com JOIN de range para evitar OOM.
# Apontamentos NAO tem Tag_Frota; derivar do mapping populacional na telemetria.
print(f"Ciclos Operando totais: {len(operando):,}")
print("Derivando mapping Tag -> Tag_Frota da telemetria populacional...")

tag_to_frota = con.sql(
    f"SELECT TAG, Tag_Frota, COUNT(*) AS n FROM {TEL} GROUP BY ALL"
).df()
# Para cada TAG, escolhe a Tag_Frota mais frequente (deve ser unica em quase todos os casos).
tag_to_frota = (
    tag_to_frota.sort_values(["TAG", "n"], ascending=[True, False])
    .groupby("TAG", as_index=False)
    .first()[["TAG", "Tag_Frota"]]
)
operando = operando.merge(tag_to_frota, left_on="Tag", right_on="TAG", how="left")
operando = operando.drop(columns=["TAG"])

print("Computando # eventos de telemetria por ciclo (JOIN de range no duckdb)...")
con.register(
    "operando_tmp",
    operando[["Id", "Tag", "Inicio", "Fim", "mes", "bucket", "Tag_Frota"]],
)

cycle_event_counts = con.sql(
    f"""
    WITH evt AS (
        SELECT TAG, Data_Evento FROM {TEL}
    )
    SELECT o.Id, o.Tag, o.Tag_Frota, o.mes, o.bucket,
           COUNT(e.Data_Evento) AS n_evt
    FROM operando_tmp o
    LEFT JOIN evt e
      ON e.TAG = o.Tag
     AND e.Data_Evento >= o.Inicio
     AND e.Data_Evento <= o.Fim
    GROUP BY ALL
    """
).df()

cycle_event_counts["zero_evt"] = (cycle_event_counts["n_evt"] == 0).astype(int)
total_op = len(cycle_event_counts)
total_zero = int(cycle_event_counts["zero_evt"].sum())
print(f"Operando total: {total_op:,}  | sem eventos: {total_zero:,} ({total_zero/total_op*100:.2f}%)")
RESULTS["h013_pop_total"] = {
    "n_ciclos_operando": total_op,
    "n_ciclos_zero_evt": total_zero,
    "pct_zero_evt": float(total_zero / total_op * 100),
}

# Estratificacao: mes x bucket
mat_mes_bucket = (
    cycle_event_counts.groupby(["mes", "bucket"])
    .agg(n_total=("Id", "count"), n_zero=("zero_evt", "sum"))
    .reset_index()
)
mat_mes_bucket["pct_zero"] = (
    mat_mes_bucket["n_zero"] / mat_mes_bucket["n_total"] * 100
)
print("\nH013 por mes x bucket:")
print(mat_mes_bucket.to_string(index=False))
RESULTS["h013_por_mes_bucket"] = mat_mes_bucket.to_dict("records")

# mes x Tag_Frota
mat_mes_frota = (
    cycle_event_counts.groupby(["mes", "Tag_Frota"])
    .agg(n_total=("Id", "count"), n_zero=("zero_evt", "sum"))
    .reset_index()
)
mat_mes_frota["pct_zero"] = (
    mat_mes_frota["n_zero"] / mat_mes_frota["n_total"] * 100
)
print("\nH013 por mes x Tag_Frota:")
print(mat_mes_frota.to_string(index=False))
RESULTS["h013_por_mes_frota"] = mat_mes_frota.to_dict("records")

# bucket x Tag_Frota
mat_bucket_frota = (
    cycle_event_counts.groupby(["bucket", "Tag_Frota"])
    .agg(n_total=("Id", "count"), n_zero=("zero_evt", "sum"))
    .reset_index()
)
mat_bucket_frota["pct_zero"] = (
    mat_bucket_frota["n_zero"] / mat_bucket_frota["n_total"] * 100
)
print("\nH013 por bucket x Tag_Frota:")
print(mat_bucket_frota.to_string(index=False))
RESULTS["h013_por_bucket_frota"] = mat_bucket_frota.to_dict("records")

# Figura: heatmap mes x bucket com % zero_evt
section("[3A.1.3.fig] Heatmap H013 por mes x bucket")
piv = mat_mes_bucket.pivot(index="bucket", columns="mes", values="pct_zero").fillna(0)
piv = piv.reindex(["00-06_madrugada", "06-12_manha", "12-18_tarde", "18-24_noite"])

fig, ax = plt.subplots(figsize=(9, 4))
im = ax.imshow(piv.values, aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(len(piv.columns)))
ax.set_xticklabels(piv.columns)
ax.set_yticks(range(len(piv.index)))
ax.set_yticklabels(piv.index)
ax.set_title(
    "H013 estratificada: % de ciclos Operando sem telemetria\n"
    f"(populacao total: {total_op:,} ciclos, taxa global {total_zero/total_op*100:.1f}%)"
)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        ax.text(j, i, f"{piv.values[i, j]:.1f}%", ha="center", va="center", fontsize=9)
plt.colorbar(im, ax=ax, label="% sem telemetria")
save_fig(fig, "fig07a_h013_por_mes_frota_hora.png")

# =========================================================================
# 4) Validacao do mapping Tag_Frota -> Porte
# =========================================================================
section("[3A.1.4] Validacao Tag_Frota -> Porte (catalogo Vale)")

# Le o exemplo Don't Go que tem coluna `Porte`.
xlsx = pd.read_excel(DONTGO_EXAMPLE_XLSX)
print(f"Colunas em desenvolver_dontgo.xlsx: {list(xlsx.columns)}")
RESULTS["dontgo_xlsx_columns"] = list(xlsx.columns)

if "Porte" in xlsx.columns and "Tag_Frota" in xlsx.columns:
    map_observed = (
        xlsx.dropna(subset=["Tag_Frota"])
        [["Tag_Frota", "Porte"]]
        .drop_duplicates()
        .sort_values(["Tag_Frota", "Porte"])
    )
    print("Pares (Tag_Frota, Porte) observados em desenvolver_dontgo.xlsx:")
    print(map_observed.to_string(index=False))
    RESULTS["porte_xlsx_observed"] = map_observed.astype(str).to_dict("records")

# Lista canonica de Tag_Frota na telemetria (5 frotas).
frotas_tel = con.sql(
    f"""
    SELECT Tag_Frota, COUNT(DISTINCT TAG) AS n_tags, COUNT(*) AS n_eventos
    FROM {TEL}
    GROUP BY ALL
    ORDER BY n_eventos DESC
    """
).df()
print("\nFrotas distintas na telemetria populacional:")
print(frotas_tel.to_string(index=False))
RESULTS["frotas_telemetria_pop"] = frotas_tel.to_dict("records")

# =========================================================================
# Persistir
# =========================================================================
out = RESULTS_DIR / "fase3a_diagnostico.json"
out.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Diagnostico Fase 3A salvo em {out}")
print("=" * 72)
