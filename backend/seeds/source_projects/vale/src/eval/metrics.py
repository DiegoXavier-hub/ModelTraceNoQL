"""Pacote completo de métricas D012 para PA-1.

Métricas implementadas
----------------------
- ``prevalence`` — taxa empírica de positivos.
- ``auc_pr`` — Area Under the Precision-Recall Curve (primária, D002).
- ``lift = AUC-PR / prevalence`` — normaliza drift entre folds (H010).
- ``auc_roc`` — comparabilidade externa.
- ``brier`` — calibração (MSE entre prob e {0,1}).
- ``ece`` — Expected Calibration Error (Guo et al. 2017) em bins equi-largos.
- ``recall_at_precision`` — recall máximo onde precision ≥ alvo (D003).
- ``lead_time_quantiles`` — P25/P50/P75 de lead time entre TPs.

Robustez
--------
Folds degenerados (0 ou 100% de positivos) retornam ``NaN``, sem exceção,
mantendo o pipeline reprodutível.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import numpy.typing as npt
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
    roc_auc_score,
)


def _is_degenerate(y_true: np.ndarray) -> bool:
    """True se y_true tem só uma classe (ranking não definido)."""
    n_pos = int(y_true.sum())
    n = len(y_true)
    return n_pos == 0 or n_pos == n


def prevalence(y_true: npt.ArrayLike) -> float:
    y = np.asarray(y_true)
    return float(y.mean()) if len(y) > 0 else float("nan")


def auc_pr(y_true: npt.ArrayLike, y_score: npt.ArrayLike) -> float:
    y, s = np.asarray(y_true), np.asarray(y_score)
    if _is_degenerate(y):
        return float("nan")
    return float(average_precision_score(y, s))


def lift(y_true: npt.ArrayLike, y_score: npt.ArrayLike) -> float:
    p = prevalence(y_true)
    a = auc_pr(y_true, y_score)
    if not np.isfinite(p) or p == 0 or not np.isfinite(a):
        return float("nan")
    return float(a / p)


def auc_roc(y_true: npt.ArrayLike, y_score: npt.ArrayLike) -> float:
    y, s = np.asarray(y_true), np.asarray(y_score)
    if _is_degenerate(y):
        return float("nan")
    return float(roc_auc_score(y, s))


def brier(y_true: npt.ArrayLike, y_score: npt.ArrayLike) -> float:
    y, s = np.asarray(y_true, dtype=float), np.asarray(y_score, dtype=float)
    if len(y) == 0:
        return float("nan")
    return float(brier_score_loss(y, s))


def ece(
    y_true: npt.ArrayLike, y_score: npt.ArrayLike, n_bins: int = 10
) -> float:
    """Expected Calibration Error em bins equi-largos."""
    y = np.asarray(y_true, dtype=float)
    s = np.asarray(y_score, dtype=float)
    if len(y) == 0:
        return float("nan")
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(s, bins) - 1, 0, n_bins - 1)
    n = len(y)
    total = 0.0
    for b in range(n_bins):
        mask = idx == b
        nb = int(mask.sum())
        if nb == 0:
            continue
        acc_b = float(y[mask].mean())
        conf_b = float(s[mask].mean())
        total += (nb / n) * abs(acc_b - conf_b)
    return float(total)


def recall_at_precision(
    y_true: npt.ArrayLike,
    y_score: npt.ArrayLike,
    target_precision: float = 0.5,
) -> float:
    """Recall máximo onde precision ≥ alvo. NaN se inalcançável."""
    y, s = np.asarray(y_true), np.asarray(y_score)
    if _is_degenerate(y):
        return float("nan")
    precs, recs, _ = precision_recall_curve(y, s)
    mask = precs >= target_precision
    if not mask.any():
        return float("nan")
    return float(recs[mask].max())


def lead_time_quantiles(
    lead_min: npt.ArrayLike,
    qs: Sequence[float] = (0.25, 0.5, 0.75),
) -> dict[str, float]:
    """Quantis de lead time (em minutos) entre TPs."""
    arr = np.asarray(lead_min, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return {f"p{int(q * 100)}": float("nan") for q in qs}
    return {f"p{int(q * 100)}": float(np.percentile(arr, q * 100)) for q in qs}


def metric_pack(
    y_true: npt.ArrayLike,
    y_score: npt.ArrayLike,
    *,
    lead_min_tp: npt.ArrayLike | None = None,
    target_precision: float = 0.5,
    n_bins_ece: int = 10,
) -> dict:
    """Pacote D012 completo (wrapper de conveniência)."""
    y = np.asarray(y_true)
    s = np.asarray(y_score)
    n = int(len(y))
    n_pos = int(y.sum()) if n > 0 else 0
    pack: dict = {
        "n": n,
        "n_pos": n_pos,
        "prevalence": prevalence(y),
        "auc_pr": auc_pr(y, s),
        "lift": lift(y, s),
        "auc_roc": auc_roc(y, s),
        "brier": brier(y, s),
        "ece": ece(y, s, n_bins=n_bins_ece),
        f"recall_at_p{int(target_precision * 100)}": recall_at_precision(
            y, s, target_precision=target_precision
        ),
    }
    if lead_min_tp is not None:
        pack["lead_time"] = lead_time_quantiles(lead_min_tp)
    return pack


__all__ = [
    "prevalence",
    "auc_pr",
    "lift",
    "auc_roc",
    "brier",
    "ece",
    "recall_at_precision",
    "lead_time_quantiles",
    "metric_pack",
]
