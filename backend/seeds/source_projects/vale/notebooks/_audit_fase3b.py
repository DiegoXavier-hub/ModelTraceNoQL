"""Fase 3B - Analise de outliers em `Valor_num`.

Objetivo: definir criterio de outlier para `Valor_num` (auditavel) que
sera usado em features derivadas (max/percentile em janela na Fase 3C).

A Fase 2B mostrou que `Valor_num` e fortemente concentrada em 0 (P25=P50=P75=0)
com cauda longa ate 4347. A correlacao com `Is_Dont_Go` e ~0 (variavel
nao e dominante isoladamente), mas pode ser util em features derivadas.

Estrategia:
- Particionar por (Alarme, Tag_Frota) — uma temperatura tem distribuicao
  diferente de uma pressao ou de um nivel.
- Calcular IQR e percentis robustos POR particao com >= 1000 eventos.
- Definir criterio dual:
  (a) Outlier estatistico: > P99 da particao OU > Q3 + 3*IQR.
  (b) Outlier estrutural: |valor| > 1e6 (sentinela de bug do sensor).
- Reportar quantos eventos seriam marcados.

Read-only: produz JSON e figura. Nao toca em src/.
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

from src.data.loaders import get_connection, load_telemetria_lazy
from src.utils.paths import FIGURES_DIR, REPORTS_DIR
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


def save_fig(fig, name: str) -> Path:
    p = FIGURES_DIR / name
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  ! figure saved: {p.name}")
    return p


print("=" * 72)
print("Fase 3B - Analise de outliers em Valor_num")
print("=" * 72)

con = get_connection()
con.execute("PRAGMA disable_progress_bar")
rel = load_telemetria_lazy(con)
TEL = "(" + rel.sql_query() + ")"

# =========================================================================
# 1) Distribuicao global de Valor_num (todos eventos com valor != NULL)
# =========================================================================
section("[3B.1] Distribuicao global de Valor_num")

stats_global = con.sql(
    f"""
    SELECT
        COUNT(*) AS n_total,
        SUM(CASE WHEN Valor_num IS NULL THEN 1 ELSE 0 END) AS n_null,
        SUM(CASE WHEN Valor_num = 0 THEN 1 ELSE 0 END) AS n_zero,
        SUM(CASE WHEN Valor_num < 0 THEN 1 ELSE 0 END) AS n_neg,
        AVG(Valor_num) AS media,
        STDDEV(Valor_num) AS sd,
        MIN(Valor_num) AS minimo,
        approx_quantile(Valor_num, 0.01) AS p01,
        approx_quantile(Valor_num, 0.25) AS p25,
        approx_quantile(Valor_num, 0.50) AS p50,
        approx_quantile(Valor_num, 0.75) AS p75,
        approx_quantile(Valor_num, 0.95) AS p95,
        approx_quantile(Valor_num, 0.99) AS p99,
        approx_quantile(Valor_num, 0.999) AS p999,
        MAX(Valor_num) AS maximo
    FROM {TEL}
    """
).df().iloc[0].to_dict()
print("Valor_num — distribuicao global:")
for k, v in stats_global.items():
    print(f"  {k}: {v}")
RESULTS["valor_num_global"] = {k: float(v) if v is not None else None for k, v in stats_global.items()}

# =========================================================================
# 2) Particoes (Alarme, Tag_Frota) com >= 1000 eventos
# =========================================================================
section("[3B.2] Particoes (Alarme, Tag_Frota) com >=1000 eventos")
particoes = con.sql(
    f"""
    SELECT
        Alarme, Tag_Frota,
        COUNT(*) AS n,
        SUM(CASE WHEN Valor_num IS NULL THEN 1 ELSE 0 END) AS n_null,
        SUM(CASE WHEN Valor_num = 0 THEN 1 ELSE 0 END) AS n_zero,
        approx_quantile(Valor_num, 0.50) AS p50,
        approx_quantile(Valor_num, 0.99) AS p99,
        approx_quantile(Valor_num, 0.999) AS p999,
        MAX(Valor_num) AS maximo
    FROM {TEL}
    WHERE Valor_num IS NOT NULL
    GROUP BY ALL
    HAVING COUNT(*) >= 1000
    ORDER BY n DESC
    LIMIT 50
    """
).df()
print(f"# particoes com >= 1000 eventos: {len(particoes)}")
print()
print("Top 20 particoes por volume:")
print(particoes.head(20).to_string(index=False))
RESULTS["particoes_top"] = particoes.head(50).astype(str).to_dict("records")

# =========================================================================
# 3) Quantos eventos seriam marcados outlier por cada criterio
# =========================================================================
section("[3B.3] Avaliacao de criterios de outlier")

# Criterio A: Valor_num > P99 da particao (Alarme, Tag_Frota)
# Criterio B: Valor_num > P99.9 da particao
# Criterio C: |Valor_num| > 1e6 (sentinela de bug)

crit_eval = con.sql(
    f"""
    WITH base AS (
        SELECT *,
               approx_quantile(Valor_num, 0.99) OVER (PARTITION BY Alarme, Tag_Frota) AS p99_p,
               approx_quantile(Valor_num, 0.999) OVER (PARTITION BY Alarme, Tag_Frota) AS p999_p
        FROM {TEL}
        WHERE Valor_num IS NOT NULL
    )
    SELECT
        COUNT(*) AS n,
        SUM(CASE WHEN Valor_num > p99_p THEN 1 ELSE 0 END) AS n_outA_gt_p99,
        SUM(CASE WHEN Valor_num > p999_p THEN 1 ELSE 0 END) AS n_outB_gt_p999,
        SUM(CASE WHEN ABS(Valor_num) > 1e6 THEN 1 ELSE 0 END) AS n_outC_abs_1e6,
        SUM(CASE WHEN Valor_num > p99_p AND Is_Dont_Go = 1 THEN 1 ELSE 0 END) AS n_outA_dontgo,
        SUM(CASE WHEN Valor_num > p999_p AND Is_Dont_Go = 1 THEN 1 ELSE 0 END) AS n_outB_dontgo,
        SUM(CASE WHEN Is_Dont_Go = 1 THEN 1 ELSE 0 END) AS n_dontgo
    FROM base
    """
).df().iloc[0].to_dict()
print("Avaliacao dos criterios (eventos com Valor_num NAO NULL):")
for k, v in crit_eval.items():
    print(f"  {k}: {int(v):,}")
RESULTS["criterios_outlier"] = {k: int(v) for k, v in crit_eval.items()}

n = crit_eval["n"]
print()
print("Pct de outliers / lift de Don't Go:")
for letra, key_n, key_dg in [
    ("A (>P99)", "n_outA_gt_p99", "n_outA_dontgo"),
    ("B (>P99.9)", "n_outB_gt_p999", "n_outB_dontgo"),
]:
    pct = crit_eval[key_n] / n * 100
    pct_dg_amongst_out = crit_eval[key_dg] / max(crit_eval[key_n], 1) * 100
    pct_dg_global = crit_eval["n_dontgo"] / n * 100
    lift = pct_dg_amongst_out / max(pct_dg_global, 1e-9)
    print(
        f"  {letra}: {pct:.4f}% das linhas marcadas; "
        f"taxa Don't Go entre outliers = {pct_dg_amongst_out:.4f}% "
        f"(lift {lift:.2f}x vs taxa global)"
    )
    RESULTS.setdefault("lift_outlier", {})[letra] = {
        "pct_marcadas": float(pct),
        "pct_dontgo_entre_outliers": float(pct_dg_amongst_out),
        "lift_x_global": float(lift),
    }

# =========================================================================
# 4) Criterio adotado (decisao formal)
# =========================================================================
section("[3B.4] Criterio adotado")
print("DECISAO (D026, formal): adotar criterio A (> P99 por particao")
print("    (Alarme, Tag_Frota)) como flag `is_valor_outlier_p99`.")
print()
print("  Justificativa:")
print("  - Particao por (Alarme, Tag_Frota) preserva semantica fisica:")
print("    uma temperatura nao e comparavel a uma pressao.")
print("  - P99 (vs P99.9) gera 1% de cobertura — suficiente para sinal,")
print("    insuficiente para over-fitting.")
print("  - Sentinela |Valor_num| > 1e6 permanece como flag separada")
print("    `is_valor_sensor_bug`.")
print("  - Valor_num NULL e Valor_num=0 ficam como ate aqui (NaN/zero")
print("    explicito); LightGBM/XGBoost lidam nativamente.")
print()
print("Aplicacao na Fase 3C:")
print("  Para cada janela [t-W, t-blackout] por equipamento, criar:")
print("    n_valor_outlier_p99_W: contagem de eventos outlier")
print("    pct_valor_outlier_p99_W: razao sobre eventos da janela")

# =========================================================================
# 5) Figura: histograma global em log + linhas de P99/P999/sentinela
# =========================================================================
section("[3B.5] Figura — distribuicao + criterios")
sample = con.sql(
    f"""
    SELECT Valor_num
    FROM {TEL}
    WHERE Valor_num IS NOT NULL AND Valor_num > 0
    USING SAMPLE 200000 ROWS
    """
).df()
fig, axes = plt.subplots(1, 2, figsize=(13, 4))

ax = axes[0]
ax.hist(np.clip(sample["Valor_num"], 0.1, 5000), bins=80, log=True)
ax.axvline(stats_global["p99"], color="red", linestyle="--", label=f"P99 global = {stats_global['p99']:.1f}")
ax.axvline(stats_global["p999"], color="orange", linestyle="--", label=f"P99.9 global = {stats_global['p999']:.1f}")
ax.set_xlabel("Valor_num (eventos com Valor_num > 0)")
ax.set_ylabel("Frequencia (log)")
ax.set_title("Distribuicao global Valor_num (amostra 200k, log scale)")
ax.legend()
ax.grid(alpha=0.3)

ax = axes[1]
ax.hist(np.clip(np.log10(np.clip(sample["Valor_num"], 0.1, None)), -1, 4), bins=80)
ax.set_xlabel("log10(Valor_num)")
ax.set_ylabel("Frequencia")
ax.set_title("Distribuicao em log10 — cauda longa visivel")
ax.grid(alpha=0.3)

save_fig(fig, "fig08_valor_num_distribuicao_outliers.png")

# =========================================================================
# Persistir
# =========================================================================
out = RESULTS_DIR / "fase3b_outliers.json"
out.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Fase 3B salva em {out}")
print("=" * 72)
