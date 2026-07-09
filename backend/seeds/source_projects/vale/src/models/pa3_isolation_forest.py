"""PA-3 Isolation Forest sobre LeTourneau (D027).

Aprende limites de "normalidade" SEM usar ``y_dontgo_*``. Avalia retroativamente
se os 32 incidentes LeTourneau caem nos top-N% scores mais anômalos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.utils.seeds import SEED


def _features_for_anomaly(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    n_cols = [c for c in df.columns if c.startswith("n_")]
    X = df[n_cols].copy()
    X = X.fillna(0.0).astype(float)
    return X, n_cols


def fit_isolation_forest(
    df_train: pd.DataFrame,
    contamination: str | float = "auto",
    n_estimators: int = 200,
    max_samples: int | str = "auto",
    seed: int = SEED,
) -> tuple[IsolationForest, list[str]]:
    X, cols = _features_for_anomaly(df_train)
    iso = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        max_samples=max_samples,
        random_state=seed,
        n_jobs=-1,
    )
    iso.fit(X)
    return iso, cols


def anomaly_scores(iso: IsolationForest, df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    """Retorna score onde quanto MAIOR, mais anômalo (negativo de decision_function)."""
    X = df[cols].copy().fillna(0.0).astype(float)
    return -iso.decision_function(X)


def capture_at_topn(
    scores: np.ndarray,
    is_event: np.ndarray,
    pct_levels: tuple[float, ...] = (1, 5, 10, 25),
) -> dict[str, dict]:
    """% dos eventos verdadeiros capturados pelos top-N% scores."""
    n = len(scores)
    n_pos = int(is_event.sum())
    out: dict[str, dict] = {}
    if n_pos == 0:
        return {f"top_{p}pct": {"captured": 0, "total": 0, "pct": 0.0} for p in pct_levels}
    order = np.argsort(scores)[::-1]
    is_event = is_event.astype(bool)
    for p in pct_levels:
        k = max(1, int(round(n * p / 100.0)))
        top_idx = order[:k]
        captured = int(is_event[top_idx].sum())
        out[f"top_{int(p)}pct"] = {
            "k": k,
            "captured": captured,
            "total": n_pos,
            "pct_captured": round(100.0 * captured / n_pos, 2),
            "precision": round(100.0 * captured / k, 4),
        }
    return out


__all__ = [
    "fit_isolation_forest",
    "anomaly_scores",
    "capture_at_topn",
]
