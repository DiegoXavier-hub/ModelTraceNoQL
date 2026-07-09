"""PA-1 XGBoost — comparativo (Fase 4C).

Sem novo tuning: traduz best_params do LightGBM para a vizinhança equivalente
de XGBoost (D004 — comparação de robustez).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb

from src.utils.seeds import SEED


def _scale_pos_weight(y: pd.Series) -> float:
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    return float(n_neg / n_pos) if n_pos > 0 else 1.0


def lgbm_params_to_xgb(lgbm_params: dict[str, Any]) -> dict[str, Any]:
    """Converte best_params do LightGBM para hiperparâmetros XGBoost análogos."""
    return {
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "max_depth": (
            lgbm_params.get("max_depth", 6)
            if lgbm_params.get("max_depth", 6) > 0
            else 6
        ),
        "learning_rate": lgbm_params.get("learning_rate", 0.1),
        "min_child_weight": lgbm_params.get("min_data_in_leaf", 20) / 5.0,
        "subsample": lgbm_params.get("bagging_fraction", 0.8),
        "colsample_bytree": lgbm_params.get("feature_fraction", 0.8),
        "reg_alpha": lgbm_params.get("lambda_l1", 0.0),
        "reg_lambda": lgbm_params.get("lambda_l2", 0.0),
        "random_state": SEED,
        "verbosity": 0,
        "n_jobs": -1,
        "enable_categorical": True,
    }


def train_xgb(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    cat_features: list[str],
    base_params: dict[str, Any],
) -> xgb.XGBClassifier:
    """Treina XGBoost com early stopping. Categóricas via dtype=category."""
    spw = _scale_pos_weight(y_train)
    params = {**base_params, "scale_pos_weight": spw, "n_estimators": 1000}
    for c in cat_features:
        if c in X_train.columns:
            X_train[c] = X_train[c].astype("category")
            X_val[c] = X_val[c].astype("category")
    model = xgb.XGBClassifier(**params, early_stopping_rounds=50)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


__all__ = ["lgbm_params_to_xgb", "train_xgb"]
