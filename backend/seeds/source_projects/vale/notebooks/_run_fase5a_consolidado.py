"""Driver Fase 5A — Avaliação consolidada (CM 5.1).

Entregáveis:
- ``reports/tables/fase5a_pa1_consolidado.csv`` — tabela única (4 modelos × 6 H).
- ``reports/figures/fig09_pr_curves.png`` — PR curves (LightGBM calibrado, JUN).
- ``reports/figures/fig10_roc_curves.png`` — ROC curves idem.
- ``reports/figures/fig11_confusion_matrix_h4.png`` — H=4h @P=0.5 e @P=0.3.
- ``reports/figures/fig11b_confusion_matrix_h12.png`` — H=12h idem.
- ``reports/eda_results/fase5a_consolidado.json`` — sumário canônico.

Fontes de dados
---------------
- LightGBM (raw)         : fase4b_pa1_lightgbm.json (WF + holdout_jun)
- XGBoost                : fase4c_pa1_comparativo.json (WF + holdout_jun)
- CatBoost               : fase4c_pa1_comparativo.json (WF + holdout_jun)
- LightGBM (calibrado)   : preds_jun_h{H}.parquet (recomputa métricas em JUN)

Em walk-forward, "LightGBM calibrado" usa as mesmas métricas técnicas do
LightGBM raw (calibração só altera Brier/ECE; AUC-PR/Lift/AUC-ROC/Recall@P
se mantêm pois calibração é monotônica). Marcamos isso explicitamente na
tabela e na coluna `notes`.
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
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.lead_time import pick_threshold_at_precision
from src.eval.metrics import (
    auc_pr,
    auc_roc,
    brier,
    ece,
    lift as lift_metric,
    prevalence,
    recall_at_precision,
)
from src.utils.paths import (
    FIGURES_DIR,
    PREDICTIONS_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
    TABLES_DIR,
)
from src.utils.seeds import SEED, set_global_seed

EDA_DIR = REPORTS_DIR / "eda_results"
HORIZONS = (1, 2, 4, 6, 8, 12)
TARGET_PRECISION = 0.5
TARGET_PRECISION_RECALL_FAV = 0.3  # ponto operacional alternativo


def _fmt_meanstd(d: dict, key: str, decimals: int = 4) -> str:
    if key not in d or "mean" not in d[key]:
        return "—"
    m = d[key]["mean"]
    s = d[key].get("std", 0.0)
    if not np.isfinite(m):
        return "—"
    return f"{m:.{decimals}f} ± {s:.{decimals}f}"


def _safe(d: dict, key: str, decimals: int = 4) -> str:
    v = d.get(key)
    if v is None or not np.isfinite(v):
        return "—"
    return f"{v:.{decimals}f}"


def _agg_to_dict(agg: dict) -> dict[str, float]:
    """Extrai apenas .mean dos pacotes WF para uso direto em rows."""
    return {k: v.get("mean", float("nan")) for k, v in agg.items()}


def build_consolidated_rows(
    fase4b: dict, fase4c: dict, calib_jun_metrics: dict
) -> list[dict]:
    rows: list[dict] = []
    for H in HORIZONS:
        h_key = f"h{H}"
        lgb_h = fase4b["horizons"][h_key]
        xgb_h = fase4c["horizons"][h_key]["xgboost"]
        cat_h = fase4c["horizons"][h_key]["catboost"]
        cal_jun = calib_jun_metrics[h_key]

        prev_jun = lgb_h["holdout_jun"]["metrics"]["prevalence"]

        # LightGBM (raw)
        rows.append(
            _model_row(
                "LightGBM",
                H,
                prev_jun=prev_jun,
                wf_agg=lgb_h["aggregate_walk_forward"],
                jun_metrics=lgb_h["holdout_jun"]["metrics"],
                jun_n=lgb_h["holdout_jun"]["n"],
                jun_n_pos=lgb_h["holdout_jun"]["n_pos"],
                notes="primário (D033/D034)",
            )
        )
        # XGBoost
        rows.append(
            _model_row(
                "XGBoost",
                H,
                prev_jun=prev_jun,
                wf_agg=xgb_h["aggregate_walk_forward"],
                jun_metrics=xgb_h["holdout_jun"]["metrics"],
                jun_n=xgb_h["holdout_jun"]["n"],
                jun_n_pos=xgb_h["holdout_jun"]["n_pos"],
                notes="comparativo Fase 4C",
            )
        )
        # CatBoost
        rows.append(
            _model_row(
                "CatBoost",
                H,
                prev_jun=prev_jun,
                wf_agg=cat_h["aggregate_walk_forward"],
                jun_metrics=cat_h["holdout_jun"]["metrics"],
                jun_n=cat_h["holdout_jun"]["n"],
                jun_n_pos=cat_h["holdout_jun"]["n_pos"],
                notes="comparativo Fase 4C",
            )
        )
        # LightGBM calibrado — JUN recomputado dos parquets PRE-1
        # WF: AUC-PR/Lift/AUC-ROC/Recall idênticos ao LGB raw (calibração monotônica);
        # Brier/ECE indisponíveis pré-calibração WF (calibrador é treinado em fold4-val).
        wf_lgb = lgb_h["aggregate_walk_forward"]
        rows.append(
            _model_row(
                "LightGBM (calibrado)",
                H,
                prev_jun=prev_jun,
                wf_agg=wf_lgb,
                jun_metrics=cal_jun,
                jun_n=cal_jun["n"],
                jun_n_pos=cal_jun["n_pos"],
                notes=f"calibrador {cal_jun['chosen_method']} (D037)",
                wf_calib_note=True,
            )
        )
    return rows


def _model_row(
    model: str,
    H: int,
    *,
    prev_jun: float,
    wf_agg: dict,
    jun_metrics: dict,
    jun_n: int,
    jun_n_pos: int,
    notes: str,
    wf_calib_note: bool = False,
) -> dict:
    return {
        "model": model,
        "horizon_h": H,
        "WF_AUC_PR": _fmt_meanstd(wf_agg, "auc_pr"),
        "WF_Lift": _fmt_meanstd(wf_agg, "lift", decimals=2),
        "WF_AUC_ROC": _fmt_meanstd(wf_agg, "auc_roc"),
        "WF_Brier": "(cal pós em JUN)" if wf_calib_note else _fmt_meanstd(wf_agg, "brier"),
        "WF_ECE": "(cal pós em JUN)" if wf_calib_note else _fmt_meanstd(wf_agg, "ece"),
        "WF_RecallAtP50": _fmt_meanstd(wf_agg, "recall_at_p50", decimals=3),
        "JUN_n": jun_n,
        "JUN_n_pos": jun_n_pos,
        "JUN_prevalence": f"{prev_jun:.4f}",
        "JUN_AUC_PR": _safe(jun_metrics, "auc_pr"),
        "JUN_Lift": _safe(jun_metrics, "lift", decimals=2),
        "JUN_AUC_ROC": _safe(jun_metrics, "auc_roc"),
        "JUN_Brier": _safe(jun_metrics, "brier"),
        "JUN_ECE": _safe(jun_metrics, "ece"),
        "JUN_RecallAtP50": _safe(jun_metrics, "recall_at_p50", decimals=3),
        "notes": notes,
    }


def compute_calibrated_jun_metrics() -> dict:
    """Recomputa métricas D012 em JUN sobre score_cal (do PRE-1)."""
    out: dict = {}
    for H in HORIZONS:
        df = pd.read_parquet(PREDICTIONS_DIR / f"preds_jun_h{H}.parquet")
        y = df["y_true"].to_numpy()
        s_cal = df["score_cal"].to_numpy()
        out[f"h{H}"] = {
            "n": int(len(df)),
            "n_pos": int(y.sum()),
            "prevalence": prevalence(y),
            "auc_pr": auc_pr(y, s_cal),
            "lift": lift_metric(y, s_cal),
            "auc_roc": auc_roc(y, s_cal),
            "brier": brier(y, s_cal),
            "ece": ece(y, s_cal),
            "recall_at_p50": recall_at_precision(y, s_cal, 0.5),
            "chosen_method": _read_calibrator_method(H),
        }
    return out


def _read_calibrator_method(H: int) -> str:
    fase4f = json.loads(
        (EDA_DIR / "fase4f_calibration.json").read_text(encoding="utf-8")
    )
    return fase4f["horizons"][f"h{H}"]["chosen_method"]


def plot_pr_roc_grid(predictions: dict[int, pd.DataFrame], out_path: Path, kind: str) -> None:
    """Plot 2x3 grid de PR ou ROC curves."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()
    for i, H in enumerate(HORIZONS):
        df = predictions[H]
        y = df["y_true"].to_numpy()
        s = df["score_cal"].to_numpy()
        prev = float(y.mean())
        ax = axes[i]
        if kind == "pr":
            precs, recs, _ = precision_recall_curve(y, s)
            ax.plot(recs, precs, color="tab:blue", linewidth=1.6)
            ax.axhline(prev, linestyle="--", linewidth=0.8, color="gray", label=f"prev={prev:.3f}")
            ax.set_xlabel("Recall")
            ax.set_ylabel("Precision")
            ax.set_title(
                f"H={H}h | AUC-PR={auc_pr(y, s):.3f} (lift={lift_metric(y, s):.2f}×)"
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, max(1.0, precs.max() * 1.05))
            ax.legend(loc="upper right", fontsize=8)
        elif kind == "roc":
            fpr, tpr, _ = roc_curve(y, s)
            ax.plot(fpr, tpr, color="tab:orange", linewidth=1.6)
            ax.plot([0, 1], [0, 1], "k--", linewidth=0.6)
            ax.set_xlabel("FPR")
            ax.set_ylabel("TPR")
            ax.set_title(f"H={H}h | AUC-ROC={auc_roc(y, s):.3f}")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        ax.grid(alpha=0.3)
    title = "Fase 5A — PR curves (JUN, score_cal)" if kind == "pr" else "Fase 5A — ROC curves (JUN, score_cal)"
    fig.suptitle(title, fontsize=14)
    plt.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_confusion_matrix(
    df_preds: pd.DataFrame,
    H: int,
    out_path: Path,
) -> dict:
    """Confusion matrix @P=0.5 (canônico) e @P=0.3 (recall-favoring)."""
    y = df_preds["y_true"].to_numpy()
    s = df_preds["score_cal"].to_numpy()
    th_p50, p_at_50, r_at_50 = pick_threshold_at_precision(y, s, 0.5)
    th_p30, p_at_30, r_at_30 = pick_threshold_at_precision(y, s, 0.3)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    summary = {}
    for ax, label, th, p_at, r_at in [
        (axes[0], "P≥0.5", th_p50, p_at_50, r_at_50),
        (axes[1], "P≥0.3", th_p30, p_at_30, r_at_30),
    ]:
        if not np.isfinite(th):
            ax.text(0.5, 0.5, f"{label}: inalcançável", ha="center", va="center")
            ax.set_axis_off()
            summary[label] = {
                "threshold": float("nan"),
                "precision_at": float("nan"),
                "recall_at": float("nan"),
                "TN": 0, "FP": 0, "FN": 0, "TP": 0,
            }
            continue
        y_pred = (s >= th).astype(int)
        cm = confusion_matrix(y, y_pred, labels=[0, 1])
        ConfusionMatrixDisplay(cm, display_labels=["Negativo", "Don't Go"]).plot(
            ax=ax, colorbar=False, cmap="Blues", values_format="d"
        )
        ax.set_title(
            f"H={H}h | τ={th:.3f} ({label}) | P={p_at:.3f}, R={r_at:.3f}"
        )
        tn, fp, fn, tp = cm.ravel()
        summary[label] = {
            "threshold": float(th),
            "precision_at": float(p_at),
            "recall_at": float(r_at),
            "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
        }
    plt.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return summary


def main() -> None:
    print("=" * 72)
    print("Fase 5A — Avaliação consolidada (CM 5.1)")
    print("=" * 72)
    set_global_seed()
    print(f"Seed: {SEED}")

    fase4b = json.loads(
        (EDA_DIR / "fase4b_pa1_lightgbm.json").read_text(encoding="utf-8")
    )
    fase4c = json.loads(
        (EDA_DIR / "fase4c_pa1_comparativo.json").read_text(encoding="utf-8")
    )

    print("\n[1/4] Recomputando métricas de score_cal em JUN...")
    cal_jun = compute_calibrated_jun_metrics()
    for H in HORIZONS:
        m = cal_jun[f"h{H}"]
        print(
            f"  H{H:>2}h cal: AUC-PR={m['auc_pr']:.4f} Lift={m['lift']:.2f}"
            f" Brier={m['brier']:.4f} ECE={m['ece']:.4f} R@P50={m['recall_at_p50']:.3f}"
            f" ({m['chosen_method']})"
        )

    print("\n[2/4] Construindo tabela consolidada...")
    rows = build_consolidated_rows(fase4b, fase4c, cal_jun)
    df_table = pd.DataFrame(rows)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = TABLES_DIR / "fase5a_pa1_consolidado.csv"
    df_table.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"  Tabela: {csv_path.relative_to(PROJECT_ROOT)} ({len(df_table)} linhas)")

    print("\n[3/4] Gerando figuras (PR / ROC / matriz de confusão)...")
    predictions = {
        H: pd.read_parquet(PREDICTIONS_DIR / f"preds_jun_h{H}.parquet")
        for H in HORIZONS
    }
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot_pr_roc_grid(predictions, FIGURES_DIR / "fig09_pr_curves.png", kind="pr")
    plot_pr_roc_grid(predictions, FIGURES_DIR / "fig10_roc_curves.png", kind="roc")
    cm_h4 = plot_confusion_matrix(
        predictions[4], 4, FIGURES_DIR / "fig11_confusion_matrix_h4.png"
    )
    cm_h12 = plot_confusion_matrix(
        predictions[12], 12, FIGURES_DIR / "fig11b_confusion_matrix_h12.png"
    )

    print("\n[4/4] Persistindo JSON canônico...")
    summary = {
        "config": {"seed": SEED, "horizons": list(HORIZONS)},
        "models_compared": ["LightGBM", "XGBoost", "CatBoost", "LightGBM (calibrado)"],
        "calibrated_jun_metrics": cal_jun,
        "confusion_matrix_h4": cm_h4,
        "confusion_matrix_h12": cm_h12,
        "n_rows_table": int(len(df_table)),
        "table_csv": str(csv_path.relative_to(PROJECT_ROOT)),
    }
    out_json = EDA_DIR / "fase5a_consolidado.json"
    out_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"  JSON: {out_json.relative_to(PROJECT_ROOT)}")

    # Recap textual da tabela
    print("\nResumo da tabela consolidada (JUN holdout):")
    print(
        f"{'Modelo':<22} | {'H':>3} | {'AUC-PR':>8} | {'Lift':>5} | {'R@P50':>6} | {'Brier':>7}"
    )
    print("-" * 70)
    for r in rows:
        print(
            f"{r['model']:<22} | {r['horizon_h']:>2}h | "
            f"{r['JUN_AUC_PR']:>8} | {r['JUN_Lift']:>5} | "
            f"{r['JUN_RecallAtP50']:>6} | {r['JUN_Brier']:>7}"
        )
    print("\n✅ Fase 5A concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
