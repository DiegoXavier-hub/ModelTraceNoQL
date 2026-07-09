"""Bootstrap IC 95% para métricas de junho 2025 (Fase 6 — Frente F2).

Resamostra com substituição as predições do JUN holdout (1000x) e calcula
intervalos de confiança bootstrap percentil 95% para AUC-PR, Lift,
AUC-ROC, Brier, ECE, Recall@P=0.5 (por janela) e Recall por incidente
(D013).

Princípio governante: ROBUSTEZ > custo computacional. O IC 95% empírico
endereça o critério de honestidade epistêmica do Cap. 6 §6.5
(Trabalhos Futuros). Não substitui as métricas pontuais, apenas as
qualifica.

Saída: dicionário JSON-serializável com IC 95% per-horizonte, persistido
em ``reports/eda_results/fase6_bootstrap_ci.json``.

Uso típico::

    from src.eval.bootstrap_ci import run_bootstrap_jun
    res = run_bootstrap_jun(n_resamples=1000, seed=42)

Dependências internas: ``src.eval.metrics`` para as métricas D012,
``src.utils.paths`` para localização canônica.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.eval.metrics import (
    auc_pr,
    auc_roc,
    brier,
    ece,
    recall_at_precision,
)
from src.utils.paths import OUTPUTS_DIR, REPORTS_DIR
from src.utils.seeds import set_global_seed


HORIZONS = [1, 2, 4, 6, 8, 12]


def _load_preds_h(h: int) -> pd.DataFrame:
    p = OUTPUTS_DIR / "predictions" / f"preds_jun_h{h}.parquet"
    if not p.is_file():
        raise FileNotFoundError(f"Predictions parquet not found: {p}")
    return pd.read_parquet(p)


def _load_lead_times_h(h: int) -> pd.DataFrame:
    p = OUTPUTS_DIR / "predictions" / f"lead_times_jun_h{h}.parquet"
    if not p.is_file():
        raise FileNotFoundError(f"Lead-time parquet not found: {p}")
    return pd.read_parquet(p)


def _percentile_ci(values: np.ndarray, alpha: float = 0.05) -> Dict[str, float]:
    lo = float(np.percentile(values, 100.0 * alpha / 2))
    hi = float(np.percentile(values, 100.0 * (1 - alpha / 2)))
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "ci_low": lo,
        "ci_high": hi,
        "std": float(np.std(values, ddof=1)),
    }


def _bootstrap_per_window(
    df: pd.DataFrame, n_resamples: int, rng: np.random.Generator
) -> Dict[str, Dict[str, float]]:
    """Bootstrap a nível de janela (D008).

    A unidade de resamostragem é a janela individual: cada bootstrap
    sample tem o mesmo tamanho do dataset original e é construída por
    sorteio com substituição. Métricas dependentes de prevalência são
    calculadas dentro de cada amostra.
    """
    y = df["y_true"].to_numpy().astype(np.int8)
    s = df["score_cal"].to_numpy().astype(np.float64)
    n = len(y)
    aucpr_list = np.empty(n_resamples)
    lift_list = np.empty(n_resamples)
    aucroc_list = np.empty(n_resamples)
    brier_list = np.empty(n_resamples)
    ece_list = np.empty(n_resamples)
    rec_p50_list = np.empty(n_resamples)
    for b in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        yb, sb = y[idx], s[idx]
        # Skip pathological samples (no positives or no negatives)
        if yb.sum() == 0 or yb.sum() == n:
            aucpr_list[b] = np.nan
            lift_list[b] = np.nan
            aucroc_list[b] = np.nan
            brier_list[b] = brier(yb, sb)
            ece_list[b] = ece(yb, sb)
            rec_p50_list[b] = np.nan
            continue
        prev_b = float(yb.mean())
        ap = auc_pr(yb, sb)
        aucpr_list[b] = ap
        lift_list[b] = ap / prev_b if prev_b > 0 else np.nan
        aucroc_list[b] = auc_roc(yb, sb)
        brier_list[b] = brier(yb, sb)
        ece_list[b] = ece(yb, sb)
        rec_p50_list[b] = recall_at_precision(yb, sb, target_precision=0.5)
    return {
        "auc_pr": _percentile_ci(aucpr_list[~np.isnan(aucpr_list)]),
        "lift": _percentile_ci(lift_list[~np.isnan(lift_list)]),
        "auc_roc": _percentile_ci(aucroc_list[~np.isnan(aucroc_list)]),
        "brier": _percentile_ci(brier_list),
        "ece": _percentile_ci(ece_list),
        "recall_at_p50": _percentile_ci(rec_p50_list[~np.isnan(rec_p50_list)]),
    }


def _bootstrap_per_incident(
    lt: pd.DataFrame, n_resamples: int, rng: np.random.Generator
) -> Dict[str, Dict[str, float]]:
    """Bootstrap a nível de incidente para Recall por incidente (D013).

    Resamostra `incident_id` com substituição e calcula Recall e Lead
    time mediano em cada amostra.
    """
    if "status" not in lt.columns:
        return {}
    n = len(lt)
    if n == 0:
        return {}
    rec_list = np.empty(n_resamples)
    lead_p50_list = np.empty(n_resamples)
    is_tp = (lt["status"].to_numpy() == "TP").astype(np.int8)
    lead = lt["lead_time_min"].to_numpy()
    for b in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        rec_list[b] = float(is_tp[idx].mean())
        leads_b = lead[idx]
        leads_tp = leads_b[~np.isnan(leads_b)]
        lead_p50_list[b] = float(np.median(leads_tp)) if leads_tp.size else np.nan
    return {
        "recall_per_incident": _percentile_ci(rec_list),
        "lead_p50_min": _percentile_ci(lead_p50_list[~np.isnan(lead_p50_list)]),
    }


def run_bootstrap_jun(
    n_resamples: int = 1000, seed: int = 42, persist: bool = True
) -> Dict:
    """Roda bootstrap IC 95% para todos os 6 horizontes.

    Args:
        n_resamples: Número de amostras bootstrap (default 1000).
        seed: Seed global.
        persist: Se True, persiste em ``reports/eda_results/fase6_bootstrap_ci.json``.

    Returns:
        Dicionário JSON-serializável com IC 95% per-horizonte.
    """
    set_global_seed(seed)
    rng = np.random.default_rng(seed)
    out: Dict = {
        "config": {
            "seed": seed,
            "n_resamples": n_resamples,
            "horizons": HORIZONS,
            "method": "percentile_bootstrap_95ci",
        },
        "per_horizon": {},
    }
    for h in HORIZONS:
        df = _load_preds_h(h)
        lt = _load_lead_times_h(h)
        win = _bootstrap_per_window(df, n_resamples=n_resamples, rng=rng)
        inc = _bootstrap_per_incident(lt, n_resamples=n_resamples, rng=rng)
        out["per_horizon"][f"h{h}"] = {
            "n_windows": int(len(df)),
            "n_incidents": int(len(lt)),
            "prevalence": float(df["y_true"].mean()),
            "per_window": win,
            "per_incident": inc,
        }
    if persist:
        target = REPORTS_DIR / "eda_results" / "fase6_bootstrap_ci.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
    return out


def summary_table(res: Dict) -> pd.DataFrame:
    """Tabela narrativa para o Cap. 6: ponto e [low, high] por H."""
    rows: List[Dict] = []
    for h_key, payload in res["per_horizon"].items():
        h = int(h_key[1:])
        win = payload["per_window"]
        inc = payload.get("per_incident", {})
        rows.append({
            "h": h,
            "n_windows": payload["n_windows"],
            "auc_pr_mean": win["auc_pr"]["mean"],
            "auc_pr_ci": (win["auc_pr"]["ci_low"], win["auc_pr"]["ci_high"]),
            "lift_mean": win["lift"]["mean"],
            "lift_ci": (win["lift"]["ci_low"], win["lift"]["ci_high"]),
            "recall_per_incident_mean": inc.get("recall_per_incident", {}).get("mean", np.nan),
            "recall_per_incident_ci": (
                inc.get("recall_per_incident", {}).get("ci_low", np.nan),
                inc.get("recall_per_incident", {}).get("ci_high", np.nan),
            ),
        })
    return pd.DataFrame(rows)
