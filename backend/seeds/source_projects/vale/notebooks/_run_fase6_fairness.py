"""Driver Fase 6 / Frente F1 — Auditoria de fairness por operador (D016).

Executa ``src.eval.fairness_operador.run_fairness_audit`` sobre todos
os horizontes e persiste em
``reports/eda_results/fase6_fairness_operador.json`` +
``reports/tables/fase6_fairness_operador.csv``.

Princípio: D016 estabelece que share_moda >= 80% cobre 61.5% dos
ciclos. Para o presente fairness audit, usamos limiar mais permissivo
(50%) e janela de 30 min antes do início do incidente para inferência
do operador, dado que o número absoluto de incidentes em JUN é
limitado (491 em H=12h) e queremos reter o máximo possível.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.eval.fairness_operador import run_fairness_audit  # noqa: E402


def main() -> None:
    print("[fase6_fairness] running fairness audit per operator...")
    res = run_fairness_audit(
        lookback_min=30, share_threshold=0.5, min_incidents=10, persist=True
    )
    print("[fase6_fairness] persisted -> reports/eda_results/fase6_fairness_operador.json")
    print("[fase6_fairness] table -> reports/tables/fase6_fairness_operador.csv")
    print()
    print("Resumo por horizonte:")
    for h_key, payload in res["per_horizon"].items():
        print(
            f"  {h_key}: incidentes={payload['n_incidents_total']}, "
            f"com operador={payload['n_incidents_with_operator']} "
            f"({payload['share_with_operator']:.1%}), "
            f"operadores >=10 incid.={payload['n_operadores_min10_incid']}, "
            f"Gini(Recall)={payload['gini_recall']:.3f}, "
            f"Disp(Q75/Q25)={payload['disparity_ratio_q75_over_q25']}"
        )


if __name__ == "__main__":
    main()
