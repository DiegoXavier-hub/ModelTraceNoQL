"""PA-1 CatBoost — comparativo (Fase 4C).

Sem novo tuning: hiperparâmetros razoáveis para classificação binária
desbalanceada com categóricas via ``cat_features``.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from src.utils.seeds import SEED


def _scale_pos_weight(y: pd.Series) -> float:
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    return float(n_neg / n_pos) if n_pos > 0 else 1.0


def lgbm_params_to_catboost(lgbm_params: dict[str, Any]) -> dict[str, Any]:
    return {
        "loss_function": "Logloss",
        "eval_metric": "AUC:type=Ranking",
        "depth": min(
            lgbm_params.get("max_depth", 6)
            if lgbm_params.get("max_depth", 6) > 0
            else 6,
            10,
        ),
        "learning_rate": lgbm_params.get("learning_rate", 0.1),
        "l2_leaf_reg": max(lgbm_params.get("lambda_l2", 3.0), 1.0),
        "rsm": lgbm_params.get("feature_fraction", 0.8),
        "subsample": lgbm_params.get("bagging_fraction", 0.8),
        "bootstrap_type": "Bernoulli",
        "random_seed": SEED,
        "verbose": False,
        "thread_count": -1,
        "allow_writing_files": False,
    }


def _coerce_categoricals_to_str(
    df: pd.DataFrame, cat_features: list[str]
) -> pd.DataFrame:
    out = df.copy()
    for c in cat_features:
        if c in out.columns:
            out[c] = out[c].astype(str).fillna("MISSING")
    return out


def train_catboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    cat_features: list[str],
    base_params: dict[str, Any],
) -> CatBoostClassifier:
    spw = _scale_pos_weight(y_train)
    params = {**base_params, "scale_pos_weight": spw, "iterations": 1000}
    Xt = _coerce_categoricals_to_str(X_train, cat_features)
    Xv = _coerce_categoricals_to_str(X_val, cat_features)
    cats_idx = [Xt.columns.get_loc(c) for c in cat_features if c in Xt.columns]
    model = CatBoostClassifier(**params)
    model.fit(
        Xt,
        y_train,
        cat_features=cats_idx,
        eval_set=(Xv, y_val),
        early_stopping_rounds=50,
        use_best_model=True,
    )
    return model


__all__ = [
    "lgbm_params_to_catboost",
    "train_catboost",
    "_coerce_categoricals_to_str",
]
