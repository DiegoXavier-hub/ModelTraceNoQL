"""Runner offline da Fase 2 — executa todas as queries da EDA, salva
figuras em reports/figures/ e dumps JSON em reports/eda_results/.

Este script e usado tanto para gerar os artefatos do TCC quanto como
fonte de verdade para o notebook 02_data_understanding_eda.ipynb (que
re-executa as mesmas chamadas).

Rodar com:
    cd "<root>"
    python notebooks/_eda_runner.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")  # backend nao-interativo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data.loaders import (
    get_connection,
    load_apontamentos,
    load_apontamentos_lazy,
    load_telemetria_lazy,
)
from src.utils.paths import (
    ALARMES_XLSX,
    DICIONARIO_XLSX,
    DONTGO_EXAMPLE_XLSX,
    FIGURES_DIR,
    REPORTS_DIR,
    TABLES_DIR,
)
from src.utils.seeds import set_global_seed

# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
set_global_seed()
RESULTS: dict = {}
RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)

con = get_connection()
rel_tel = load_telemetria_lazy(con)
TEL_SUBQUERY = "(" + rel_tel.sql_query() + ")"

print("=" * 72)
print("Fase 2 EDA runner — projeto Vale (Don't Go)")
print("=" * 72)


def section(title: str) -> None:
    print()
    print("-" * 72)
    print(title)
    print("-" * 72)


def save_fig(fig, name: str) -> Path:
    p = FIGURES_DIR / name
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  ! figure saved: {p.name}")
    return p


# ----------------------------------------------------------------------
# Fase 2B — shape, dtypes, %nulos, duplicados, distribuicao temporal
# ----------------------------------------------------------------------
section("[2B.1] Shape e schema")

apt = load_apontamentos(con)
RESULTS["apontamentos_shape"] = list(apt.shape)
RESULTS["apontamentos_dtypes"] = {c: str(t) for c, t in apt.dtypes.items()}
RESULTS["apontamentos_mem_mb"] = float(apt.memory_usage(deep=True).sum() / 1e6)
print(f"apontamentos: shape={apt.shape}  mem={RESULTS['apontamentos_mem_mb']:.1f} MB")
print(apt.dtypes)

n_tel = con.sql(f"SELECT COUNT(*) n FROM {TEL_SUBQUERY}").df().iloc[0, 0]
RESULTS["telemetria_total_rows"] = int(n_tel)
print(f"\ntelemetria: {n_tel:,} linhas (lazy)")

# Volumes mensais via group by month(Data_Evento)
section("[2B.2] Volumes mensais de telemetria")
volume_mes = con.sql(
    f"""
    SELECT date_trunc('month', Data_Evento) AS mes, COUNT(*) AS n
    FROM {TEL_SUBQUERY}
    GROUP BY ALL
    ORDER BY mes
    """
).df()
volume_mes["mes_str"] = volume_mes["mes"].dt.strftime("%Y-%m")
print(volume_mes[["mes_str", "n"]])
RESULTS["telemetria_volume_mes"] = volume_mes[["mes_str", "n"]].to_dict("records")

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(volume_mes["mes_str"], volume_mes["n"] / 1e6)
ax.set_ylabel("Eventos (milhoes)")
ax.set_xlabel("Mes")
ax.set_title("Volume mensal de eventos de telemetria")
for i, v in enumerate(volume_mes["n"]):
    ax.text(i, v / 1e6, f"{v/1e6:.2f}M", ha="center", va="bottom", fontsize=9)
save_fig(fig, "fig02_volume_telemetria_mensal.png")

# Volume mensal de apontamentos
volume_mes_apt = (
    apt.assign(mes=apt["Inicio"].dt.to_period("M").astype(str))
    .groupby("mes")
    .size()
    .reset_index(name="n")
    .sort_values("mes")
)
RESULTS["apontamentos_volume_mes"] = volume_mes_apt.to_dict("records")
print()
print("Apontamentos por mes:")
print(volume_mes_apt)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(volume_mes_apt["mes"], volume_mes_apt["n"] / 1e3, color="#666")
ax.set_ylabel("Ciclos (milhares)")
ax.set_xlabel("Mes")
ax.set_title("Volume mensal de apontamentos (ciclos de equipamento)")
for i, v in enumerate(volume_mes_apt["n"]):
    ax.text(i, v / 1e3, f"{v/1e3:.1f}k", ha="center", va="bottom", fontsize=9)
save_fig(fig, "fig02_volume_apontamentos_mensal.png")

# Periodo coberto
section("[2B.3] Periodo coberto")
periodo_tel = con.sql(
    f"SELECT MIN(Data_Evento) AS min_d, MAX(Data_Evento) AS max_d FROM {TEL_SUBQUERY}"
).df().iloc[0]
RESULTS["telemetria_periodo"] = {
    "min": str(periodo_tel["min_d"]),
    "max": str(periodo_tel["max_d"]),
}
print(f"telemetria: {periodo_tel['min_d']} -> {periodo_tel['max_d']}")

periodo_apt = {
    "min_inicio": str(apt["Inicio"].min()),
    "max_inicio": str(apt["Inicio"].max()),
    "min_fim": str(apt["Fim"].min()),
    "max_fim": str(apt["Fim"].max()),
}
RESULTS["apontamentos_periodo"] = periodo_apt
print(
    f"apontamentos Inicio: {periodo_apt['min_inicio']} -> {periodo_apt['max_inicio']}"
)
print(f"apontamentos Fim: {periodo_apt['min_fim']} -> {periodo_apt['max_fim']}")

# %nulos por coluna — telemetria (com colunas limpas)
section("[2B.4] %nulos por coluna — telemetria")
cols_check = [
    "Id_Eventos_Telemetria",
    "Data_Evento",
    "Inicio_Turno_ts",
    "Fim_Turno_ts",
    "Dia",
    "Localidade",
    "TAG",
    "Tag_Frota",
    "Tipo",
    "Nome_Operador_Anon",
    "Matricula_Operador_Hash",
    "Id_Alarme",
    "Alarme",
    "Id_Criticidade",
    "Criticidade",
    "Valor_num",
    "Valor_raw",
    "Classe",
    "Is_Dont_Go",
]
expr = ", ".join(
    [
        f"100.0 * SUM(CASE WHEN \"{c}\" IS NULL THEN 1 ELSE 0 END) / COUNT(*) AS \"{c}\""
        for c in cols_check
    ]
)
nulos = con.sql(f"SELECT {expr} FROM {TEL_SUBQUERY}").df().T
nulos.columns = ["pct_null"]
nulos = nulos.sort_values("pct_null", ascending=False)
print(nulos)
RESULTS["telemetria_pct_null"] = nulos["pct_null"].round(4).to_dict()

# nulos apontamentos
print()
print("apontamentos pct null:")
print((apt.isna().mean() * 100).round(4))
RESULTS["apontamentos_pct_null"] = (apt.isna().mean() * 100).round(4).to_dict()

# duplicados
section("[2B.5] Duplicados")
dup_apt_id = int(apt["Id"].duplicated().sum())
dup_apt_full = int(apt.duplicated().sum())
RESULTS["apontamentos_duplicados_id"] = dup_apt_id
RESULTS["apontamentos_duplicados_full"] = dup_apt_full
print(f"apontamentos: dup por Id={dup_apt_id}, dup linha completa={dup_apt_full}")

dup_tel = con.sql(
    f"SELECT COUNT(*) - COUNT(DISTINCT Id_Eventos_Telemetria) AS n_dup FROM {TEL_SUBQUERY}"
).df().iloc[0, 0]
RESULTS["telemetria_duplicados_id"] = int(dup_tel)
print(f"telemetria: dup por Id_Eventos_Telemetria={dup_tel}")

# Distribuicao temporal por dia/hora
section("[2B.6] Distribuicao temporal — eventos por dia e por hora")
por_dia = con.sql(
    f"""
    SELECT date_trunc('day', Data_Evento) AS dia, COUNT(*) AS n
    FROM {TEL_SUBQUERY}
    GROUP BY ALL
    ORDER BY dia
    """
).df()
por_hora = con.sql(
    f"""
    SELECT extract(hour FROM Data_Evento) AS hora, COUNT(*) AS n
    FROM {TEL_SUBQUERY}
    GROUP BY ALL
    ORDER BY hora
    """
).df()
RESULTS["telemetria_por_dia_count"] = len(por_dia)
RESULTS["telemetria_por_hora"] = por_hora.to_dict("records")

fig, axes = plt.subplots(2, 1, figsize=(10, 6))
axes[0].plot(por_dia["dia"], por_dia["n"] / 1e3)
axes[0].set_title("Eventos de telemetria por dia (jan-jun 2025)")
axes[0].set_ylabel("Eventos (milhares)")
axes[0].grid(alpha=0.3)
axes[1].bar(por_hora["hora"], por_hora["n"] / 1e3)
axes[1].set_title("Eventos por hora do dia (agregado)")
axes[1].set_xlabel("Hora do dia (0-23)")
axes[1].set_ylabel("Eventos (milhares)")
axes[1].set_xticks(range(0, 24))
axes[1].grid(alpha=0.3)
plt.tight_layout()
save_fig(fig, "fig02_dist_temporal_telemetria.png")

# Estatisticas descritivas — Valor_num (numerica unica)
section("[2B.7] Estatisticas descritivas Valor_num")
stats_valor = con.sql(
    f"""
    SELECT COUNT(*) AS n_total,
           COUNT(Valor_num) AS n_nao_null,
           AVG(Valor_num) AS media,
           STDDEV_SAMP(Valor_num) AS stddev,
           MIN(Valor_num) AS minv,
           quantile_cont(Valor_num, 0.25) AS p25,
           quantile_cont(Valor_num, 0.5) AS p50,
           quantile_cont(Valor_num, 0.75) AS p75,
           MAX(Valor_num) AS maxv
    FROM {TEL_SUBQUERY}
    """
).df().iloc[0]
print(stats_valor)
RESULTS["telemetria_valor_stats"] = {k: float(v) if v is not None and not pd.isna(v) else None for k, v in stats_valor.items()}

# Cardinalidades importantes
section("[2B.8] Cardinalidades")
card = con.sql(
    f"""
    SELECT
        COUNT(DISTINCT TAG) AS n_tag,
        COUNT(DISTINCT Tag_Frota) AS n_frota,
        COUNT(DISTINCT Tipo) AS n_tipo,
        COUNT(DISTINCT Localidade) AS n_localidade,
        COUNT(DISTINCT Alarme) AS n_alarme,
        COUNT(DISTINCT Id_Alarme) AS n_alarme_id,
        COUNT(DISTINCT Criticidade) AS n_criticidade,
        COUNT(DISTINCT Classe) AS n_classe,
        COUNT(DISTINCT Nome_Operador_Anon) AS n_operador
    FROM {TEL_SUBQUERY}
    """
).df().iloc[0]
print(card)
RESULTS["telemetria_cardinalidades"] = {k: int(v) for k, v in card.items()}

# ----------------------------------------------------------------------
# Salvar resultados parciais
# ----------------------------------------------------------------------
out_path = RESULTS_DIR / "fase2b_results.json"
out_path.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Fase 2B salva em {out_path}")
print("=" * 72)
