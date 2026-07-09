"""Driver Fase 5B — Análise de erros (CM 5.2).

Para H=4h (ponto operacional sugerido) e H=12h (mais lead time):
1. Classifica cada janela como TP/FP/TN/FN @threshold_at_p50.
2. Distribuições de FN e FP por TAG, Tag_Frota, hora_dia, bucket_hora,
   família proximal (`n_fam_*_4h`).
3. Top-10 incidentes "perdidos por todos os horizontes" → SHAP local
   (waterfall) usando o modelo H=4h.
4. Histograma de lead time per-window por bucket {0–15, 15–60, 1–4h, >4h}.

Saídas:
- ``reports/figures/fig12_fn_waterfalls_<i>.png`` × 10 (uma por incidente FN).
- ``reports/figures/fig13_error_distribution.png``.
- ``reports/figures/fig13b_fn_by_dimension.png``.
- ``reports/eda_results/fase5b_error_analysis.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.error_analysis import (
    FAMILY_4H_COLS,
    classify_predictions,
    confusion_status,
    find_globally_missed_incidents,
    fn_fp_by_dimension,
    proximal_family_distribution,
)
from src.eval.lead_time import load_jun_incidents_cat
from src.eval.predictions import load_holdout_cat
from src.eval.splits import apply_censura_filter
from src.models.pa1_lightgbm import build_feature_matrix
from src.utils.paths import (
    FIGURES_DIR,
    MODELS_DIR,
    PREDICTIONS_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
)
from src.utils.seeds import SEED, set_global_seed

EDA_DIR = REPORTS_DIR / "eda_results"
HORIZONS = (1, 2, 4, 6, 8, 12)
H_OP = 4  # horizonte operacional sugerido


def _hour_bucket_str(h: int) -> str:
    if h < 6:
        return "00-06_madrugada"
    if h < 12:
        return "06-12_manha"
    if h < 18:
        return "12-18_tarde"
    return "18-24_noite"


def _read_thresholds() -> dict[int, float]:
    with (EDA_DIR / "fase5_pre2_lead_times.json").open(encoding="utf-8") as f:
        d = json.load(f)
    return {H: d["horizons"][f"h{H}"]["threshold_at_p50"] for H in HORIZONS}


def _enriched_features_jun_h(H: int) -> pd.DataFrame:
    """JUN holdout, CAT, censura aplicada, com colunas extras p/ joins."""
    df = load_holdout_cat()
    df = apply_censura_filter(df, horizon_h=H, kind="eval").reset_index(drop=True)
    df["hora_dia"] = pd.to_datetime(df["t_window"]).dt.hour
    df["bucket_hora_str"] = df["hora_dia"].apply(_hour_bucket_str)
    return df


def main() -> None:
    print("=" * 72)
    print("Fase 5B — Análise de erros (CM 5.2)")
    print("=" * 72)
    set_global_seed()
    print(f"Seed: {SEED}")

    thresholds = _read_thresholds()
    print(f"Thresholds@P=0.5 por H: {thresholds}")

    # -------------------------------------------------------------------
    # 1) Classificar predições H=4h e H=12h
    # -------------------------------------------------------------------
    print("\n[1/4] Classificando predições (H=4h, H=12h)...")
    classified_per_h: dict[int, pd.DataFrame] = {}
    feats_per_h: dict[int, pd.DataFrame] = {}
    for H in (H_OP, 12):
        preds = pd.read_parquet(PREDICTIONS_DIR / f"preds_jun_h{H}.parquet")
        preds["t_window"] = pd.to_datetime(preds["t_window"])
        cl = classify_predictions(preds, threshold=thresholds[H])
        feats = _enriched_features_jun_h(H)
        feats["t_window"] = pd.to_datetime(feats["t_window"])
        classified_per_h[H] = cl
        feats_per_h[H] = feats

        cs = confusion_status(cl)
        print(
            f"  H{H:>2}h: TP={cs.n_TP} FP={cs.n_FP} TN={cs.n_TN} FN={cs.n_FN}"
            f" (total={cs.total}, threshold={thresholds[H]:.4f})"
        )

    # -------------------------------------------------------------------
    # 2) Distribuições por dimensão (H=4h)
    # -------------------------------------------------------------------
    print("\n[2/4] Distribuições FN/FP por dimensão (H=4h)...")
    cl_4 = classified_per_h[H_OP]
    feats_4 = feats_per_h[H_OP]

    dim_results: dict[str, pd.DataFrame] = {}
    for dim, top_k in [
        ("TAG", 10),
        ("Tag_Frota", None),
        ("hora_dia", None),
        ("bucket_hora_str", None),
    ]:
        d = fn_fp_by_dimension(cl_4, feats_4, dim, top_k=top_k)
        dim_results[dim] = d
        print(f"  {dim} (top {len(d)} por FN):")
        for r in d.head(min(5, len(d))).to_dict(orient="records"):
            print(
                f"    {r[dim]}: TP={r.get('TP', 0)} FP={r.get('FP', 0)}"
                f" FN={r.get('FN', 0)} TN={r.get('TN', 0)}"
                f" fn_rate={r.get('fn_rate', float('nan')):.3f}"
                if isinstance(r.get('fn_rate'), float) and np.isfinite(r.get('fn_rate', float('nan')))
                else f"    {r[dim]}: TP={r.get('TP', 0)} FP={r.get('FP', 0)} FN={r.get('FN', 0)} TN={r.get('TN', 0)}"
            )

    proximal = proximal_family_distribution(cl_4, feats_4, FAMILY_4H_COLS)
    print(f"  Família proximal (top FN): ")
    fn_prox = proximal[proximal["status"] == "FN"].head(5)
    for r in fn_prox.to_dict(orient="records"):
        print(f"    {r['dominant_family']}: {r['count']}")

    # -------------------------------------------------------------------
    # 3) Top-10 incidentes "perdidos por todos os horizontes" + SHAP local
    # -------------------------------------------------------------------
    print("\n[3/4] Top-10 incidentes FN globais + SHAP local (H=4h)...")
    incidents = load_jun_incidents_cat()
    lead_times_per_h: dict[int, pd.DataFrame] = {}
    for H in HORIZONS:
        lead_times_per_h[H] = pd.read_parquet(
            PREDICTIONS_DIR / f"lead_times_jun_h{H}.parquet"
        )
    fn_global = find_globally_missed_incidents(incidents, lead_times_per_h)
    print(f"  Incidentes FN em TODOS os 6 horizontes: {len(fn_global)}")

    # Para SHAP local, escolher os 10 mais relevantes (maior duracao_min ou
    # com `alarme_inicio` mais frequente — mas `duracao_min` é majoritariamente
    # 0 (eventos instantâneos). Vamos pegar os 10 primeiros por ordem cronológica.
    fn_top10 = fn_global.head(10).copy()

    # Carregar modelo H=4h e construir matriz
    booster_h4 = lgb.Booster(
        model_file=str(MODELS_DIR / f"lgbm_h{H_OP}_holdout_jun.txt")
    )
    df_eval_h4 = apply_censura_filter(load_holdout_cat(), horizon_h=H_OP, kind="eval")
    X_h4, y_h4, _ = build_feature_matrix(df_eval_h4, H_OP)
    df_eval_h4_ = df_eval_h4.reset_index(drop=True)
    df_eval_h4_["row_idx"] = np.arange(len(df_eval_h4_))

    # Para cada FN-incidente, achar a janela mais próxima do t_I (anterior),
    # com mesma TAG, e gerar SHAP local nela.
    fn_top10_records: list[dict] = []
    explainer = shap.TreeExplainer(booster_h4)
    expected_value = explainer.expected_value
    if isinstance(expected_value, (list, np.ndarray)):
        expected_value = float(np.atleast_1d(expected_value).ravel()[-1])
    else:
        expected_value = float(expected_value)

    for i, inc in fn_top10.iterrows():
        tag = inc["TAG"]
        t_I = pd.to_datetime(inc["inicio_inc"])
        win_start = t_I - pd.Timedelta(hours=H_OP)
        candidate = df_eval_h4_[
            (df_eval_h4_["TAG"] == tag)
            & (df_eval_h4_["t_window"] >= win_start)
            & (df_eval_h4_["t_window"] <= t_I)
        ]
        if candidate.empty:
            print(f"  [{i}] Sem janela CAT pré-incidente para TAG={tag} t_I={t_I}")
            continue
        # Janela mais próxima do incidente
        chosen = candidate.sort_values("t_window").iloc[-1]
        idx_local = int(chosen["row_idx"])
        row = X_h4.iloc[[idx_local]]
        sv = explainer.shap_values(row)
        sv = sv[1] if isinstance(sv, list) and len(sv) > 1 else (
            sv[0] if isinstance(sv, list) else sv
        )
        sv_arr = np.asarray(sv).reshape(-1)
        # top-10 por |SHAP|
        order = np.argsort(np.abs(sv_arr))[::-1][:10]
        feat_names = [str(row.columns[j]) for j in order]
        vals = sv_arr[order]

        proba_local = float(np.asarray(booster_h4.predict(row)).ravel()[0])
        delta_pre_inc_min = float((t_I - pd.to_datetime(chosen["t_window"])).total_seconds() / 60.0)

        # Plot waterfall
        fig, ax = plt.subplots(figsize=(9, 4.8))
        colors = ["tab:red" if v > 0 else "tab:blue" for v in vals]
        ax.barh(range(len(vals)), vals, color=colors)
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(feat_names, fontsize=8)
        ax.invert_yaxis()
        ax.axvline(0, color="k", linewidth=0.5)
        ax.set_xlabel("SHAP value")
        ax.set_title(
            f"FN #{i+1}: TAG={tag} | t_I={t_I.strftime('%Y-%m-%d %H:%M')}"
            f" | Δ={delta_pre_inc_min:.0f} min | proba(H=4h)={proba_local:.3f}",
            fontsize=10,
        )
        plt.tight_layout()
        out_fig = FIGURES_DIR / f"fig12_fn_waterfalls_{i+1:02d}.png"
        fig.savefig(out_fig, dpi=120, bbox_inches="tight")
        plt.close(fig)

        fn_top10_records.append(
            {
                "rank": int(i + 1),
                "TAG": tag,
                "Tag_Frota": inc["Tag_Frota"],
                "incident_id": int(inc["incident_id"]),
                "t_I": str(t_I),
                "alarme_inicio": inc.get("alarme_inicio"),
                "t_window_chosen": str(chosen["t_window"]),
                "delta_pre_inc_min": delta_pre_inc_min,
                "proba_h4": proba_local,
                "expected_value": expected_value,
                "top_10_shap": [
                    {"feature": feat_names[k], "shap": float(vals[k])}
                    for k in range(len(vals))
                ],
                "fig_path": str(out_fig.relative_to(PROJECT_ROOT)),
            }
        )
    print(f"  Persistidas {len(fn_top10_records)} figuras fig12_fn_waterfalls_*.png")

    # -------------------------------------------------------------------
    # 4) Histograma lead-time per-window (buckets D013) + heatmap dimensão
    # -------------------------------------------------------------------
    print("\n[4/4] Histograma lead time per-window (H=4h, H=12h)...")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    bucket_summaries: dict[int, dict] = {}
    for ax, H in zip(axes, (H_OP, 12)):
        preds = pd.read_parquet(PREDICTIONS_DIR / f"preds_jun_h{H}.parquet")
        mask_tp = (preds["y_true"] == 1) & preds["target_lead_time_min"].notna()
        arr = preds.loc[mask_tp, "target_lead_time_min"].to_numpy(dtype=float)
        bin_edges = [0, 15, 60, 240, max(720, float(arr.max() if len(arr) else 720))]
        labels = ["0-15min", "15-60min", "1-4h", ">4h"]
        counts = []
        for i in range(len(bin_edges) - 1):
            n = int(((arr >= bin_edges[i]) & (arr < bin_edges[i + 1])).sum())
            counts.append(n)
        ax.bar(labels, counts, color=["tab:red", "tab:orange", "tab:green", "tab:blue"])
        for j, v in enumerate(counts):
            ax.text(j, v + max(counts) * 0.01, str(v), ha="center", fontsize=9)
        ax.set_title(f"Lead time per-window (H={H}h, n_TP={len(arr)})")
        ax.set_ylabel("Janelas TP")
        ax.grid(alpha=0.3, axis="y")
        bucket_summaries[H] = dict(zip(labels, counts))
    plt.suptitle("Fase 5B — Distribuição de lead time per-window (TP)", fontsize=12)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig13_error_distribution.png", dpi=120)
    plt.close(fig)

    # FN by dimension figure (H=4h)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for ax, key in zip(axes.flatten(), ["TAG", "Tag_Frota", "hora_dia", "bucket_hora_str"]):
        d = dim_results[key].copy()
        if key == "hora_dia":
            d = d.sort_values(key)
        elif key == "bucket_hora_str":
            order = ["00-06_madrugada", "06-12_manha", "12-18_tarde", "18-24_noite"]
            d[key] = pd.Categorical(d[key], categories=order, ordered=True)
            d = d.sort_values(key)
        labels = d[key].astype(str).tolist()[:15]
        fn_vals = d["FN"].tolist()[:15]
        tp_vals = d["TP"].tolist()[:15]
        x = np.arange(len(labels))
        width = 0.4
        ax.bar(x - width / 2, fn_vals, width, label="FN", color="tab:red")
        ax.bar(x + width / 2, tp_vals, width, label="TP", color="tab:green")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.set_title(f"FN/TP por {key}")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, axis="y")
    plt.suptitle("Fase 5B — FN/TP por dimensão (H=4h, JUN)", fontsize=12)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "fig13b_fn_by_dimension.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    # -------------------------------------------------------------------
    # JSON canônico
    # -------------------------------------------------------------------
    summary = {
        "config": {
            "seed": SEED,
            "horizons_classified": [H_OP, 12],
            "h_operational": H_OP,
            "thresholds_at_p50": thresholds,
            "n_incidents_jun_cat": int(len(incidents)),
        },
        "confusion_per_h": {
            f"h{H}": {
                "TP": confusion_status(classified_per_h[H]).n_TP,
                "FP": confusion_status(classified_per_h[H]).n_FP,
                "TN": confusion_status(classified_per_h[H]).n_TN,
                "FN": confusion_status(classified_per_h[H]).n_FN,
            }
            for H in (H_OP, 12)
        },
        "fn_top10_by_TAG_h4": dim_results["TAG"].head(10).to_dict(orient="records"),
        "fn_by_Tag_Frota_h4": dim_results["Tag_Frota"].to_dict(orient="records"),
        "fn_by_hora_dia_h4": dim_results["hora_dia"].to_dict(orient="records"),
        "fn_by_bucket_hora_h4": dim_results["bucket_hora_str"].to_dict(orient="records"),
        "proximal_family_distribution_h4": proximal.to_dict(orient="records"),
        "fn_globally_missed_incidents_n": int(len(fn_global)),
        "fn_top10_globally_missed_with_shap": fn_top10_records,
        "lead_time_buckets_per_window": bucket_summaries,
    }
    out_json = EDA_DIR / "fase5b_error_analysis.json"
    out_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n→ {out_json.relative_to(PROJECT_ROOT)}")
    print("\n✅ Fase 5B concluída.")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
