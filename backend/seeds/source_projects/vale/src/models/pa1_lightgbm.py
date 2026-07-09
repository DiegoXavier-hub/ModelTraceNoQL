"""PA-1 LightGBM por horizonte com tuning Optuna.

Pipeline (D001 v2 + D004 + D015 + D011)
---------------------------------------
1. ``build_feature_matrix`` — separa X / y, descarta colunas-alvo e metadados.
2. ``tune_lgbm_for_horizon`` — Optuna 150 trials sobre fold 1 (val=fev).
3. ``train_final_per_fold`` — retreina nos 4 folds com ``best_params`` +
   ``early_stopping``.
4. ``predict_calibratable`` — score de probabilidade ``predict_proba``-like.

Princípios
----------
- ``scale_pos_weight = neg/pos`` por fold (D015 — sem SMOTE).
- Categóricas declaradas via ``categorical_feature``.
- Sem ``target_lead_time_min`` em X (D030).
- ``early_stopping_rounds=30`` para evitar overfit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from src.utils.seeds import SEED

# Categóricas após filtro CAT (Tipo_canonico, OEM, Porte são constantes).
CAT_COLS = ["Tag_Frota", "bucket_hora", "turno"]

# Metadados / chaves / alvos a EXCLUIR de X.
EXCLUDE_FROM_X = {
    "TAG",
    "t_window",
    "mes_str",
    "OEM",
    "Tipo_canonico",
    "Porte",
    "Capacidade_t",
    "target_lead_time_min",
    "label_completa_12h",
}
TARGET_PREFIX = "y_dontgo_"

LGBM_FIXED_PARAMS = {
    "objective": "binary",
    "metric": "average_precision",
    "boosting_type": "gbdt",
    "verbose": -1,
    "n_jobs": -1,
    "random_state": SEED,
}


def build_feature_matrix(
    df: pd.DataFrame, horizon_h: int
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Separa X, y e lista de categóricas para um horizonte."""
    target_col = f"{TARGET_PREFIX}{horizon_h}h"
    y = df[target_col].astype(int)
    drop = EXCLUDE_FROM_X | {
        c for c in df.columns if c.startswith(TARGET_PREFIX)
    }
    feature_cols = [c for c in df.columns if c not in drop]
    X = df[feature_cols].copy()
    for c in CAT_COLS:
        if c in X.columns:
            X[c] = X[c].astype("category")
    cats_present = [c for c in CAT_COLS if c in X.columns]
    return X, y, cats_present


def _scale_pos_weight(y: pd.Series) -> float:
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0:
        return 1.0
    return float(n_neg / n_pos)


def tune_lgbm_for_horizon(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    cat_features: list[str],
    n_trials: int = 150,
    timeout_s: int | None = None,
    seed: int = SEED,
) -> tuple[dict[str, Any], float]:
    """Tuning Bayesiano via Optuna TPE.

    Retorna (best_params, best_value) onde best_value é AUC-PR no val.
    """
    spw = _scale_pos_weight(y_train)

    def objective(trial: optuna.Trial) -> float:
        params: dict[str, Any] = {
            **LGBM_FIXED_PARAMS,
            "num_leaves": trial.suggest_int("num_leaves", 15, 255),
            "learning_rate": trial.suggest_float(
                "learning_rate", 0.01, 0.2, log=True
            ),
            "max_depth": trial.suggest_categorical(
                "max_depth", [-1, 4, 6, 8, 12]
            ),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 200),
            "feature_fraction": trial.suggest_float(
                "feature_fraction", 0.5, 1.0
            ),
            "bagging_fraction": trial.suggest_float(
                "bagging_fraction", 0.5, 1.0
            ),
            "bagging_freq": trial.suggest_categorical(
                "bagging_freq", [0, 5, 10]
            ),
            "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
            "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
            "scale_pos_weight": spw,
            "n_estimators": 500,
        }
        model = lgb.LGBMClassifier(**params)
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            eval_metric="average_precision",
            categorical_feature=cat_features,
            callbacks=[lgb.early_stopping(30, verbose=False)],
        )
        proba = model.predict_proba(X_val)[:, 1]
        from src.eval.metrics import auc_pr

        return auc_pr(y_val, proba)

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=n_trials, timeout=timeout_s, show_progress_bar=False)
    return dict(study.best_params), float(study.best_value)


def train_final_per_fold(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    best_params: dict[str, Any],
    cat_features: list[str],
) -> lgb.LGBMClassifier:
    """Treina modelo final num fold com best_params + early stopping."""
    spw = _scale_pos_weight(y_train)
    params = {
        **LGBM_FIXED_PARAMS,
        **best_params,
        "scale_pos_weight": spw,
        "n_estimators": 1000,
    }
    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="average_precision",
        categorical_feature=cat_features,
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )
    return model


def save_lgbm(model: lgb.LGBMClassifier, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(path))


def feature_importance_gain(
    model: lgb.LGBMClassifier, top: int = 15
) -> pd.DataFrame:
    """Top-N features por gain."""
    booster = model.booster_
    df = pd.DataFrame(
        {
            "feature": booster.feature_name(),
            "gain": booster.feature_importance(importance_type="gain"),
        }
    ).sort_values("gain", ascending=False)
    return df.head(top).reset_index(drop=True)


__all__ = [
    "CAT_COLS",
    "EXCLUDE_FROM_X",
    "TARGET_PREFIX",
    "build_feature_matrix",
    "tune_lgbm_for_horizon",
    "train_final_per_fold",
    "save_lgbm",
    "feature_importance_gain",
]
