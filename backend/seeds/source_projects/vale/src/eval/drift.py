"""Análise de drift PSI / KS (Fase 4H).

PSI (Population Stability Index)
--------------------------------
Para cada feature numérica, distribui em 10 quantis do conjunto de
referência (treino) e calcula:

    PSI = sum_b (p_test[b] - p_ref[b]) * log(p_test[b] / p_ref[b])

Interpretação:
- PSI < 0.1   : estável
- 0.1-0.25    : atenção
- PSI >= 0.25 : drift severo

KS test
-------
Kolmogorov-Smirnov entre amostras de treino e teste — devolve estatística
e p-valor.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def _bucketize(values: np.ndarray, edges: np.ndarray) -> np.ndarray:
    return np.clip(np.searchsorted(edges, values, side="right") - 1, 0, len(edges) - 2)


def population_stability_index(
    ref: pd.Series, test: pd.Series, n_bins: int = 10, eps: float = 1e-6
) -> float:
    ref = pd.to_numeric(ref, errors="coerce").dropna().to_numpy()
    test = pd.to_numeric(test, errors="coerce").dropna().to_numpy()
    if len(ref) < 10 or len(test) < 10:
        return float("nan")
    # Bordas em quantis do treino
    qs = np.linspace(0, 1, n_bins + 1)
    edges = np.unique(np.quantile(ref, qs))
    if len(edges) < 3:
        return 0.0
    ref_bin = _bucketize(ref, edges)
    test_bin = _bucketize(test, edges)
    n_b = len(edges) - 1
    p_ref = (np.bincount(ref_bin, minlength=n_b) + eps) / (len(ref) + eps * n_b)
    p_test = (np.bincount(test_bin, minlength=n_b) + eps) / (len(test) + eps * n_b)
    return float(np.sum((p_test - p_ref) * np.log(p_test / p_ref)))


def ks_test(ref: pd.Series, test: pd.Series) -> dict[str, float]:
    ref = pd.to_numeric(ref, errors="coerce").dropna().to_numpy()
    test = pd.to_numeric(test, errors="coerce").dropna().to_numpy()
    if len(ref) < 10 or len(test) < 10:
        return {"statistic": float("nan"), "p_value": float("nan")}
    res = ks_2samp(ref, test)
    return {"statistic": float(res.statistic), "p_value": float(res.pvalue)}


def drift_report(
    ref_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
    n_bins: int = 10,
) -> pd.DataFrame:
    rows = []
    for c in feature_cols:
        if c not in ref_df.columns or c not in test_df.columns:
            continue
        psi = population_stability_index(ref_df[c], test_df[c], n_bins=n_bins)
        ks = ks_test(ref_df[c], test_df[c])
        rows.append(
            {
                "feature": c,
                "psi": round(psi, 5),
                "ks_stat": round(ks["statistic"], 5),
                "ks_p": round(ks["p_value"], 6),
                "category": _psi_category(psi),
            }
        )
    return pd.DataFrame(rows).sort_values("psi", ascending=False).reset_index(drop=True)


def _psi_category(psi: float) -> str:
    if not np.isfinite(psi):
        return "indef"
    if psi < 0.1:
        return "estavel"
    if psi < 0.25:
        return "atencao"
    return "severo"


__all__ = [
    "population_stability_index",
    "ks_test",
    "drift_report",
]
