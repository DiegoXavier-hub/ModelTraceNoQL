"""Análise de erros (Fase 5B) — distribuições de FN/FP + SHAP local.

Funções para:
- Classificar predições por (y_true, score_cal, threshold) → ``status`` ∈
  {"TP", "FP", "TN", "FN"}.
- Agregar FN/FP por TAG, Tag_Frota, hora_dia, bucket_hora e família proximal.
- Identificar incidentes "perdidos por todos os horizontes" (FN globais).
- Computar SHAP local (waterfall top-10) num conjunto de janelas.

Princípios
----------
- Threshold operacional vem do ``threshold_at_p50`` calculado em PRE-2 e
  registrado em ``fase5_pre2_lead_times.json``.
- Para "família proximal", usamos o sufixo `_4h` (família dominante na
  janela imediatamente prévia ao horizonte H=4h).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

FAMILY_4H_COLS: tuple[str, ...] = (
    "n_fam_engine_coolant_4h",
    "n_fam_engine_oil_4h",
    "n_fam_transmission_4h",
    "n_fam_hydraulic_4h",
    "n_fam_brakes_4h",
    "n_fam_steering_4h",
    "n_fam_exhaust_turbo_4h",
    "n_fam_body_load_4h",
    "n_fam_operational_state_4h",
    "n_fam_electrical_comms_4h",
    "n_fam_fuel_aftertreatment_4h",
    "n_fam_fan_drive_4h",
    "n_fam_tires_suspension_4h",
    "n_fam_air_filters_4h",
    "n_fam_other_4h",
)


@dataclass(frozen=True)
class ConfusionStatus:
    """Status de cada janela após aplicar threshold."""

    n_TP: int
    n_FP: int
    n_TN: int
    n_FN: int

    @property
    def total(self) -> int:
        return self.n_TP + self.n_FP + self.n_TN + self.n_FN


def classify_predictions(
    df: pd.DataFrame,
    threshold: float,
    score_col: str = "score_cal",
    label_col: str = "y_true",
) -> pd.DataFrame:
    """Adiciona coluna ``status`` ∈ {"TP", "FP", "TN", "FN"}.

    NaN threshold (inalcançável) → todas como TN/FN (predição sempre 0).
    """
    out = df.copy()
    if not np.isfinite(threshold):
        y_pred = np.zeros(len(out), dtype=int)
    else:
        y_pred = (out[score_col].to_numpy() >= threshold).astype(int)
    y = out[label_col].to_numpy().astype(int)
    status = np.where(
        (y == 1) & (y_pred == 1), "TP",
        np.where(
            (y == 1) & (y_pred == 0), "FN",
            np.where(
                (y == 0) & (y_pred == 1), "FP", "TN"
            ),
        ),
    )
    out["status"] = status
    return out


def confusion_status(df_classified: pd.DataFrame) -> ConfusionStatus:
    counts = df_classified["status"].value_counts()
    return ConfusionStatus(
        n_TP=int(counts.get("TP", 0)),
        n_FP=int(counts.get("FP", 0)),
        n_TN=int(counts.get("TN", 0)),
        n_FN=int(counts.get("FN", 0)),
    )


def fn_fp_by_dimension(
    df_classified: pd.DataFrame,
    df_features: pd.DataFrame,
    dimension: str,
    *,
    top_k: int | None = None,
) -> pd.DataFrame:
    """Distribuição de FN/FP/TP/TN por uma dimensão.

    df_features deve ter ``t_window`` e ``TAG`` (ou outra coluna usada como
    chave de junção) idênticos a df_classified — passamos um DataFrame único
    enriquecido na função chamadora.
    """
    join_cols = ["TAG", "t_window"]
    right_cols = list(dict.fromkeys(join_cols + [dimension]))  # dedup
    df = df_classified[join_cols + ["status"]].merge(
        df_features[right_cols], on=join_cols, how="left"
    )
    pivot = (
        df.groupby([dimension, "status"], dropna=False)
        .size()
        .unstack("status", fill_value=0)
        .reset_index()
    )
    for st in ["TP", "FP", "TN", "FN"]:
        if st not in pivot.columns:
            pivot[st] = 0
    pivot["fn_rate"] = pivot["FN"] / (pivot["TP"] + pivot["FN"]).replace(0, np.nan)
    pivot["fp_rate"] = pivot["FP"] / (pivot["FP"] + pivot["TN"]).replace(0, np.nan)
    pivot = pivot.sort_values("FN", ascending=False).reset_index(drop=True)
    if top_k is not None:
        pivot = pivot.head(top_k)
    return pivot


def proximal_family_distribution(
    df_classified: pd.DataFrame,
    df_features: pd.DataFrame,
    family_cols: Iterable[str] = FAMILY_4H_COLS,
) -> pd.DataFrame:
    """Para cada (FN, FP), qual família ``n_fam_*_4h`` é dominante na janela?

    Retorna contagem por (status, família_dominante).
    """
    join_cols = ["TAG", "t_window"]
    df = df_classified[join_cols + ["status"]].merge(
        df_features[join_cols + list(family_cols)],
        on=join_cols,
        how="left",
    )
    family_arr = df[list(family_cols)].fillna(0).to_numpy()
    if family_arr.size == 0:
        return pd.DataFrame(columns=["status", "dominant_family", "count"])
    # Caso todas zero → "none"; senão argmax
    none_mask = family_arr.sum(axis=1) == 0
    dom_idx = np.argmax(family_arr, axis=1)
    fam_names = list(family_cols)
    df["dominant_family"] = np.where(
        none_mask, "none", [fam_names[i] for i in dom_idx]
    )
    out = (
        df.groupby(["status", "dominant_family"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    return out.sort_values(["status", "count"], ascending=[True, False]).reset_index(
        drop=True
    )


def find_globally_missed_incidents(
    incidents_df: pd.DataFrame,
    lead_times_per_horizon: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    """Incidentes que NENHUM horizonte capturou (FN em todos os 6 H).

    Parameters
    ----------
    incidents_df
        Incidentes em junho (saída de ``load_jun_incidents_cat``).
    lead_times_per_horizon
        ``{H: df_lead_time}`` por horizonte (saída de PRE-2).
    """
    base = incidents_df[
        ["TAG", "incident_id", "inicio_inc", "alarme_inicio", "Tag_Frota"]
    ].copy()
    base["inicio_inc"] = pd.to_datetime(base["inicio_inc"])

    for H, df_lt in lead_times_per_horizon.items():
        col = f"status_h{H}"
        sub = df_lt[["TAG", "incident_id", "status"]].rename(columns={"status": col})
        base = base.merge(sub, on=["TAG", "incident_id"], how="left")

    status_cols = [f"status_h{H}" for H in lead_times_per_horizon.keys()]
    fn_all = (base[status_cols] == "FN").all(axis=1)
    return base.loc[fn_all].reset_index(drop=True)


__all__ = [
    "FAMILY_4H_COLS",
    "ConfusionStatus",
    "classify_predictions",
    "confusion_status",
    "find_globally_missed_incidents",
    "fn_fp_by_dimension",
    "proximal_family_distribution",
]
