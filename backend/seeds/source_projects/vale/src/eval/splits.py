"""Splits temporais walk-forward (D011) e filtros de censura (D032).

Funções públicas
----------------
- ``make_walk_forward_folds(df, n_folds, buffer_h)``: 4 folds expansivos jan→mai.
- ``make_holdout(df, holdout_month)``: junho como teste intocado.
- ``apply_censura_filter(df, horizon_h, kind)``: aplica D032 derivando
  ``label_completa_<H>h`` on-the-fly para H ∈ {1, 2, 4, 6, 8}.
- ``audit_buffer_overlap(folds, df, lookback_h_max, horizons)``: mede overlap
  treino↔val em duas óticas (val-lookback × train-label-leak).

Convenção de buffer
-------------------
O buffer é aplicado ao **treino**: janelas com ``t_window > val_period_start
- buffer_h`` são removidas do treino. Junho NUNCA entra em treino, validação
ou tuning — fica disponível apenas via ``make_holdout()``.

Censura (D032)
--------------
``label_completa_12h`` está materializada no parquet. Para H < 12h, derivamos
on-the-fly usando o limite ``2025-07-01 00:00`` (fim observável da telemetria
de junho). Janelas com ``t_window + H > 2025-07-01 00:00`` têm label
incompleto e são excluídas da avaliação no horizonte H.
"""
from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

DATASET_END_TS = pd.Timestamp("2025-07-01 00:00")
TRAIN_MONTHS_DEFAULT = ("2025-01", "2025-02", "2025-03", "2025-04", "2025-05")
HOLDOUT_MONTH_DEFAULT = "2025-06"


def make_walk_forward_folds(
    df: pd.DataFrame,
    n_folds: int = 4,
    buffer_h: int = 4,
    time_col: str = "t_window",
    month_col: str = "mes_str",
    label_col_for_pos: str = "y_dontgo_12h",
) -> list[dict]:
    """Constrói folds walk-forward expansivos (D011).

    Parameters
    ----------
    df : DataFrame previamente filtrado por OEM (D027) e ``lookback_completo=1``.
        DEVE ter o índice posicional contínuo (``reset_index(drop=True)``).
    n_folds : 4 por padrão (D011 fechada).
    buffer_h : horas de gap entre fim do treino e início da validação.
    time_col : coluna de timestamp.
    month_col : coluna ``mes_str`` (formato ``YYYY-MM``).
    label_col_for_pos : coluna usada para reportar prevalência de positivos
        (referência para inspeção; reportamos apenas, não filtramos).

    Returns
    -------
    Lista de dicts. Cada dict descreve um fold com ``train_idx``/``val_idx``
    como ``np.ndarray`` de inteiros (índices posicionais de ``df``).
    """
    months = list(TRAIN_MONTHS_DEFAULT)
    if n_folds < 1 or n_folds > 4:
        raise ValueError(f"n_folds deve estar em [1, 4], recebido {n_folds}")

    if month_col not in df.columns:
        raise ValueError(f"df precisa da coluna {month_col!r}")

    folds: list[dict] = []
    pos_idx = np.arange(len(df))

    for f in range(n_folds):
        train_months = months[: f + 1]
        val_month = months[f + 1]

        val_period_start = pd.Timestamp(f"{val_month}-01")
        train_cutoff = val_period_start - pd.Timedelta(hours=buffer_h)

        in_train_months = df[month_col].isin(train_months).to_numpy()
        in_val_month = (df[month_col] == val_month).to_numpy()

        respects_buffer = (df[time_col] <= train_cutoff).to_numpy()

        train_mask = in_train_months & respects_buffer
        val_mask = in_val_month

        train_idx = pos_idx[train_mask]
        val_idx = pos_idx[val_mask]

        folds.append(
            {
                "fold": f + 1,
                "train_months": train_months,
                "val_month": val_month,
                "val_period_start": str(val_period_start),
                "train_cutoff": str(train_cutoff),
                "buffer_h_applied": buffer_h,
                "n_train": int(len(train_idx)),
                "n_val": int(len(val_idx)),
                "n_pos_train_h12": int(df.iloc[train_idx][label_col_for_pos].sum()),
                "n_pos_val_h12": int(df.iloc[val_idx][label_col_for_pos].sum()),
                "prevalence_train_h12": float(
                    df.iloc[train_idx][label_col_for_pos].mean()
                )
                if len(train_idx) > 0
                else float("nan"),
                "prevalence_val_h12": float(
                    df.iloc[val_idx][label_col_for_pos].mean()
                )
                if len(val_idx) > 0
                else float("nan"),
                "train_idx": train_idx,
                "val_idx": val_idx,
            }
        )
    return folds


def make_holdout(
    df: pd.DataFrame,
    holdout_month: str = HOLDOUT_MONTH_DEFAULT,
    month_col: str = "mes_str",
) -> pd.DataFrame:
    """Retorna o teste intocado (junho por padrão). Use UMA vez por modelo final."""
    return df[df[month_col] == holdout_month].copy()


def apply_censura_filter(
    df: pd.DataFrame,
    horizon_h: int,
    kind: Literal["train", "eval"],
    time_col: str = "t_window",
    dataset_end: pd.Timestamp = DATASET_END_TS,
) -> pd.DataFrame:
    """Aplica filtros de censura D032.

    - ``kind='train'``: requer ``lookback_completo=1``.
    - ``kind='eval'``: requer ``lookback_completo=1`` AND ``label_completa_<H>h=1``.

    A flag ``label_completa_<H>h`` para H<12h é derivada via
    ``t_window + INTERVAL H HOUR <= dataset_end``.
    """
    if "lookback_completo" not in df.columns:
        raise ValueError("df precisa de 'lookback_completo' (D032).")

    mask = df["lookback_completo"] == 1

    if kind == "eval":
        cutoff = dataset_end - pd.Timedelta(hours=horizon_h)
        mask &= df[time_col] <= cutoff
    elif kind != "train":
        raise ValueError(f"kind deve ser 'train' ou 'eval', recebido {kind!r}")

    return df.loc[mask].copy()


def audit_buffer_overlap(
    folds: list[dict],
    df: pd.DataFrame,
    lookback_h_max: int = 12,
    horizons: tuple[int, ...] = (1, 2, 4, 6, 8, 12),
    time_col: str = "t_window",
) -> dict:
    """Audita overlap treino↔val em duas óticas complementares.

    A) **Val-lookback overlap**: janelas de validação cuja janela de
       lookback (até ``lookback_h_max`` h) recobre o período de treino.
       Diagnóstico do risco "features de val dependem de eventos do treino".
    B) **Train-label leak**: janelas de treino cujo horizonte de label H
       cai no período de validação (``t_train + H > val_start``). Diagnóstico
       "label do treino é contaminado por evento do val".

    Critério (Q1 do C1): se ``pct_overlap`` de A > 1% em qualquer fold,
    propor revisão de D011 (buffer = 12h em vez de 4h).
    """
    out: dict = {
        "measurement_A_val_lookback_overlap": [],
        "measurement_B_train_label_leak": [],
    }
    for fold in folds:
        train_t = df.iloc[fold["train_idx"]][time_col]
        val_t = df.iloc[fold["val_idx"]][time_col]
        if len(train_t) == 0 or len(val_t) == 0:
            continue

        train_end = train_t.max()
        val_start = val_t.min()
        buffer_actual_h = (val_start - train_end).total_seconds() / 3600.0

        # A) lookback de val recobre treino
        cutoff_A = train_end + pd.Timedelta(hours=lookback_h_max)
        overlap_A = val_t <= cutoff_A
        n_overlap = int(overlap_A.sum())
        n_val = int(len(val_t))
        max_overlap_minutes = 0.0
        if n_overlap > 0:
            min_t_val = val_t.min()
            lookback_start = min_t_val - pd.Timedelta(hours=lookback_h_max)
            max_overlap_minutes = max(
                0.0, (train_end - lookback_start).total_seconds() / 60.0
            )

        out["measurement_A_val_lookback_overlap"].append(
            {
                "fold": fold["fold"],
                "train_end": str(train_end),
                "val_start": str(val_start),
                "buffer_actual_h": round(buffer_actual_h, 4),
                "lookback_h": lookback_h_max,
                "n_val_windows": n_val,
                "n_overlap_windows": n_overlap,
                "pct_overlap": round(100.0 * n_overlap / n_val, 4)
                if n_val > 0
                else 0.0,
                "max_overlap_minutes": round(max_overlap_minutes, 1),
            }
        )

        # B) label do treino vaza no val (por horizonte)
        for H in horizons:
            cutoff_B = val_start - pd.Timedelta(hours=H)
            leak_B = train_t > cutoff_B
            n_leak = int(leak_B.sum())
            n_train = int(len(train_t))
            out["measurement_B_train_label_leak"].append(
                {
                    "fold": fold["fold"],
                    "horizon_h": H,
                    "cutoff_for_no_leak": str(cutoff_B),
                    "n_train_windows": n_train,
                    "n_leak_windows": n_leak,
                    "pct_leak": round(100.0 * n_leak / n_train, 4)
                    if n_train > 0
                    else 0.0,
                }
            )
    return out


__all__ = [
    "make_walk_forward_folds",
    "make_holdout",
    "apply_censura_filter",
    "audit_buffer_overlap",
    "DATASET_END_TS",
    "TRAIN_MONTHS_DEFAULT",
    "HOLDOUT_MONTH_DEFAULT",
]
