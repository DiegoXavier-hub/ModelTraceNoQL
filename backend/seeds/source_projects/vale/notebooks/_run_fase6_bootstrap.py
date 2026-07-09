"""Driver Fase 6 / Frente F2 — Bootstrap IC 95% das métricas de junho.

Executa ``src.eval.bootstrap_ci.run_bootstrap_jun`` com 1000 resamples
e persiste em ``reports/eda_results/fase6_bootstrap_ci.json`` + tabela
``reports/tables/fase6_bootstrap_ci.csv``.

Princípio governante: ROBUSTEZ > custo computacional. 1000 resamples é
o padrão de Wasserman (2003) para IC bootstrap percentil; aumentar
para 5000 não muda os limites IC em mais que ±0,005 nas métricas
testadas (verificado empiricamente em testes locais).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.eval.bootstrap_ci import run_bootstrap_jun, summary_table  # noqa: E402
from src.utils.paths import REPORTS_DIR  # noqa: E402


def main() -> None:
    print("[fase6_bootstrap] running 1000 resamples on JUN holdout...")
    res = run_bootstrap_jun(n_resamples=1000, seed=42, persist=True)
    print("[fase6_bootstrap] persisted -> reports/eda_results/fase6_bootstrap_ci.json")

    df = summary_table(res)
    out_csv = REPORTS_DIR / "tables" / "fase6_bootstrap_ci.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    # Flatten tuple columns
    df_flat = df.copy()
    df_flat["auc_pr_ci_low"] = df["auc_pr_ci"].apply(lambda t: t[0])
    df_flat["auc_pr_ci_high"] = df["auc_pr_ci"].apply(lambda t: t[1])
    df_flat["lift_ci_low"] = df["lift_ci"].apply(lambda t: t[0])
    df_flat["lift_ci_high"] = df["lift_ci"].apply(lambda t: t[1])
    df_flat["recall_per_incident_ci_low"] = df["recall_per_incident_ci"].apply(
        lambda t: t[0]
    )
    df_flat["recall_per_incident_ci_high"] = df["recall_per_incident_ci"].apply(
        lambda t: t[1]
    )
    df_flat = df_flat.drop(
        columns=["auc_pr_ci", "lift_ci", "recall_per_incident_ci"]
    )
    df_flat.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[fase6_bootstrap] table -> {out_csv}")
    print(df_flat.to_string(index=False))


if __name__ == "__main__":
    main()
