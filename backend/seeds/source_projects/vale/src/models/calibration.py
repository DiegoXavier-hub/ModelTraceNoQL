"""Calibração de probabilidades (D014) — Platt scaling + Isotonic Regression.

Usa fold de validação (mai/2025) como conjunto de calibração e avalia sobre
junho/2025 (intocado). Compara Brier e ECE pré × pós para escolher o método
operacional.
"""
from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


def fit_platt(scores_val: np.ndarray, y_val: np.ndarray) -> LogisticRegression:
    """Sigmoid 1D (Platt scaling)."""
    lr = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
    lr.fit(scores_val.reshape(-1, 1), y_val)
    return lr


def apply_platt(model: LogisticRegression, scores: np.ndarray) -> np.ndarray:
    return model.predict_proba(scores.reshape(-1, 1))[:, 1]


def fit_isotonic(
    scores_val: np.ndarray, y_val: np.ndarray
) -> IsotonicRegression:
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(scores_val, y_val)
    return iso


def apply_isotonic(model: IsotonicRegression, scores: np.ndarray) -> np.ndarray:
    return model.predict(scores)


__all__ = [
    "fit_platt",
    "apply_platt",
    "fit_isotonic",
    "apply_isotonic",
]
