"""Driver Fase 5C — Tradução técnica → impacto operacional (CM 5.3 / 6.1).

1. Deriva ``d_avg`` (mediana empírica de duração de parada não-programada).
2. Computa superfície de sensibilidade ``(ΔP × ρ)`` para H ∈ {2, 4, 8} h.
3. Recomenda ponto operacional baseado em ``(lift × recall × lead_p50)`` e em
   horas evitadas absolutas.
4. Persiste figura ``fig17_sensitivity_surface.png`` (heatmap H=4h, anotando
   célula recomendada) e ``reports/eda_results/fase5c_business_impact.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.business_impact import (
    derive_d_avg,
    recommended_operating_point,
    sensitivity_surface,
)
from src.utils.paths import (
    FIGURES_DIR,
    PREDICTIONS_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
)
from src.utils.seeds import SEED, set_global_seed

EDA_DIR = REPORTS_DIR / "eda_results"
HORIZONS_TO_REPORT = (2, 4, 8, 12)
DELTAS = (30.0, 60.0, 120.0, 240.0)
RHOS = (0.5, 0.7, 0.9)


def _read_horizon_lead_times(H: int) -> np.ndarray:
    df = pd.read_parquet(PREDICTIONS_DIR / f"lead_times_jun_h{H}.parquet")
    return df.loc[df["status"] == "TP", "lead_time_min"].to_numpy(dtype=float)


def _read_canonical_metrics() -> dict:
    fase4b = json.loads(
        (EDA_DIR / "fase4b_pa1_lightgbm.json").read_text(encoding="utf-8")
    )
    fase5b = json.loads(
        (EDA_DIR / "fase5b_error_analysis.json").read_text(encoding="utf-8")
    )
    fase5_pre2 = json.loads(
        (EDA_DIR / "fase5_pre2_lead_times.json").read_text(encoding="utf-8")
    )
    return {"fase4b": fase4b, "fase5b": fase5b, "fase5_pre2": fase5_pre2}


def plot_sensitivity_heatmap(
    surface: dict, H: int, d_avg_h: float, recommended: dict, out_path: Path
) -> None:
    deltas = surface["deltas"]
    rhos = surface["rhos"]
    matrix = np.zeros((len(deltas), len(rhos)))
    for cell in surface["cells"]:
        i = deltas.index(cell["delta_p_min"])
        j = rhos.index(cell["rho"])
        matrix[i, j] = cell["hours_saved_per_month"]

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(rhos)))
    ax.set_xticklabels([f"ρ={r:.1f}" for r in rhos])
    ax.set_yticks(range(len(deltas)))
    ax.set_yticklabels([f"ΔP={int(d)} min" for d in deltas])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            v = matrix[i, j]
            color = "white" if v > matrix.max() * 0.5 else "black"
            ax.text(j, i, f"{v:,.0f} h", ha="center", va="center", color=color, fontsize=10)
    plt.colorbar(im, ax=ax, label="Horas evitadas / mês")
    ax.set_title(
        f"Fase 5C — Superfície (ΔP × ρ) | H={H}h | d_avg={d_avg_h:.2f}h\n"
        f"Recomendado: H={recommended.get('horizon_h')}h, "
        f"ΔP={int(recommended.get('delta_p_min', 0))}min, ρ={recommended.get('rho', 0):.1f}"
        f" → {recommended.get('hours_saved_per_month', 0):.0f}h/mês"
    )
    plt.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def main() -> None:
    print("=" * 72)
    print("Fase 5C — Tradução técnica → impacto operacional (CM 5.3 / 6.1)")
    print("=" * 72)
    set_global_seed()
    print(f"Seed: {SEED}")

    # 1) d_avg empírico — três estimativas (cru, op, físico-reconstruído)
    print("\n[1/4] Derivando d_avg de apontamentos (Classe ∈ {Parado, Manutenção})...")
    d = derive_d_avg(min_op_min=30.0, gap_max_min=5.0)
    print(
        f"  Global  : n={d.n_ciclos:,}  P25={d.p25_min:.1f}  P50={d.p50_min:.1f}min ({d.d_avg_h:.2f}h)  P75={d.p75_min:.1f}"
    )
    print(
        f"  Op (≥30): n={d.n_ciclos_op:,}  P25={d.p25_op_min:.1f}  P50={d.p50_op_min:.1f}min ({d.d_avg_h_op:.2f}h)  P75={d.p75_op_min:.1f}"
        f"  | share_exato_60min={d.pct_share_60min_op:.1%} (cap do sistema)"
    )
    print(
        f"  Físico  : n={d.n_paradas_fisicas:,}  P25={d.p25_phys_min:.1f}  P50={d.p50_phys_min:.1f}min ({d.d_avg_h_phys:.2f}h)  P75={d.p75_phys_min:.1f} (D040, gap≤{d.gap_max_min:.0f}min)"
    )
    print(
        "  → usando d_avg_h_phys (D040: paradas físicas reconstruídas — número honesto)"
    )

    # 2) Superfícies por horizonte
    print("\n[2/4] Computando superfícies (ΔP × ρ) por horizonte...")
    surface_per_h: dict[int, dict] = {}
    surface_per_h_op: dict[int, dict] = {}
    surface_per_h_global: dict[int, dict] = {}
    metrics_per_h: dict[int, dict] = {}
    canonical = _read_canonical_metrics()

    for H in HORIZONS_TO_REPORT:
        lt = _read_horizon_lead_times(H)
        # Default: d_avg_h_phys (D040 — reconstruído fisicamente)
        surf = sensitivity_surface(lt, deltas=DELTAS, rhos=RHOS, d_avg_h=d.d_avg_h_phys)
        surface_per_h[H] = surf
        # Variantes (registradas no JSON para honestidade epistêmica):
        surface_per_h_op[H] = sensitivity_surface(
            lt, deltas=DELTAS, rhos=RHOS, d_avg_h=d.d_avg_h_op
        )
        surface_per_h_global[H] = sensitivity_surface(
            lt, deltas=DELTAS, rhos=RHOS, d_avg_h=d.d_avg_h
        )
        # Score de recomendação alternativo (lift × recall × lead_p50_h)
        h_key = f"h{H}"
        ref = canonical["fase4b"]["horizons"][h_key]["holdout_jun"]["metrics"]
        pre2 = canonical["fase5_pre2"]["horizons"][h_key]
        lead_p50 = pre2["lead_time_per_incident_min"]["p50"]
        recall_inc = pre2["recall_per_incident"]
        score = ref["lift"] * recall_inc * (lead_p50 / 60.0)
        metrics_per_h[H] = {
            "lift_jun": ref["lift"],
            "recall_per_incident": recall_inc,
            "lead_p50_min": lead_p50,
            "score_lift_x_recall_x_leadh": score,
            "n_TPs_per_incident": pre2["n_TP_per_incident"],
        }
        print(
            f"  H{H:>2}h: n_TP={len(lt)} lead_p50={lead_p50:.1f}min"
            f" | score={score:.2f}"
            f" | célula (ΔP=60, ρ=0.7) → {surf['cells'][1*3 + 1]['hours_saved_per_month']:.0f}h/mês"
        )

    # 3) Recomendação
    print("\n[3/4] Recomendação operacional...")
    rec = recommended_operating_point(surface_per_h, DELTAS, RHOS)
    print(
        f"  MAX horas evitadas: H={rec['horizon_h']}h, ΔP={int(rec['delta_p_min'])}min,"
        f" ρ={rec['rho']:.1f} → {rec['hours_saved_per_month']:.0f}h/mês"
        f" ({rec['n_TPs_aproveitaveis']} TPs aproveitáveis de {rec['n_TPs_total']})"
    )

    # Recomendação alternativa: maior score técnico (lift x recall x lead_h)
    best_score_h = max(metrics_per_h.keys(), key=lambda h: metrics_per_h[h]["score_lift_x_recall_x_leadh"])
    print(
        f"  Maior score técnico (lift × recall × lead_h): H={best_score_h}h"
        f" (score={metrics_per_h[best_score_h]['score_lift_x_recall_x_leadh']:.2f})"
    )

    # 4) Figura + JSON
    print("\n[4/4] Persistindo figura + JSON canônico...")
    plot_sensitivity_heatmap(
        surface_per_h[4], H=4, d_avg_h=d.d_avg_h_phys, recommended=rec,
        out_path=FIGURES_DIR / "fig17_sensitivity_surface.png"
    )
    # extra: heatmap H=12h
    plot_sensitivity_heatmap(
        surface_per_h[12], H=12, d_avg_h=d.d_avg_h_phys, recommended=rec,
        out_path=FIGURES_DIR / "fig17b_sensitivity_surface_h12.png"
    )
    # extra 2: heatmap H=8h (sweet spot operacional)
    plot_sensitivity_heatmap(
        surface_per_h[8], H=8, d_avg_h=d.d_avg_h_phys, recommended=rec,
        out_path=FIGURES_DIR / "fig17c_sensitivity_surface_h8.png"
    )

    summary = {
        "config": {
            "seed": SEED,
            "horizons_evaluated": list(HORIZONS_TO_REPORT),
            "deltas_min": list(DELTAS),
            "rhos": list(RHOS),
        },
        "d_avg": {
            "global": {
                "p25_min": d.p25_min,
                "p50_min": d.p50_min,
                "p75_min": d.p75_min,
                "n_ciclos": d.n_ciclos,
                "d_avg_h": d.d_avg_h,
            },
            "operacional": {
                "min_op_min": d.min_op_min,
                "p25_op_min": d.p25_op_min,
                "p50_op_min": d.p50_op_min,
                "p75_op_min": d.p75_op_min,
                "n_ciclos_op": d.n_ciclos_op,
                "share_exact_60min_op": d.pct_share_60min_op,
                "d_avg_h_op": d.d_avg_h_op,
                "decision_ref": "D039",
            },
            "fisico_reconstruido": {
                "gap_max_min": d.gap_max_min,
                "p25_phys_min": d.p25_phys_min,
                "p50_phys_min": d.p50_phys_min,
                "p75_phys_min": d.p75_phys_min,
                "n_paradas_fisicas": d.n_paradas_fisicas,
                "d_avg_h_phys": d.d_avg_h_phys,
                "decision_ref": "D040",
            },
            "classes_filtradas": list(d.classes_filtradas),
            "d_avg_h_used_in_surface": d.d_avg_h_phys,
            "default_decision_ref": "D040",
        },
        "metrics_per_h": metrics_per_h,
        "surface_per_h_fisico_default": {
            f"h{H}": surface_per_h[H] for H in HORIZONS_TO_REPORT
        },
        "surface_per_h_operacional_d039": {
            f"h{H}": surface_per_h_op[H] for H in HORIZONS_TO_REPORT
        },
        "surface_per_h_global_reference": {
            f"h{H}": surface_per_h_global[H] for H in HORIZONS_TO_REPORT
        },
        "recommended_operating_point": rec,
        "best_technical_score_horizon": int(best_score_h),
    }
    out_json = EDA_DIR / "fase5c_business_impact.json"
    out_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"  → {out_json.relative_to(PROJECT_ROOT)}")
    print(f"  → reports/figures/fig17_sensitivity_surface.png")
    print(f"  → reports/figures/fig17b_sensitivity_surface_h12.png")
    print("\n✅ Fase 5C concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
