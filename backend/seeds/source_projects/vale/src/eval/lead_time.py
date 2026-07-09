"""Lead time empírico (Fase 5 / PRE-2).

Operacionaliza D013 (definição formal TP/FN/FP/Lead time) sobre o JUN holdout.

Duas perspectivas complementares
--------------------------------
1) **Per-window (TP por janela 15 min)**: para cada janela com ``y_true=1``,
   ``target_lead_time_min`` (já materializado no parquet, clipado em 12h)
   é o lead time. Útil para histogramas/buckets em 5B.

2) **Per-incidente (D013 formal)**: para cada incidente ``I`` em junho:
   - ``P(I)`` = predições positivas (``score_cal ≥ τ_op``) emitidas pelo
     equipamento de ``I`` em ``[t_I − H, t_I]``.
   - **TP** se ``P(I) ≠ ∅``: ``lead_time = t_I − min(t_window ∈ P(I))``.
   - **FN** se ``P(I) = ∅``.
   Esta é a unidade de avaliação correta para Recall e Lead time finais
   (1 incidente = 1 unidade, não N janelas).

Threshold operacional
---------------------
``pick_threshold_at_precision`` varre a curva PR sobre ``score_cal`` e
seleciona o **menor** threshold que entrega ``precision ≥ alvo`` (default
0,5; D003). A varredura é feita em junho e usada apenas para *tradução
operacional* (5C) — não para seleção de modelo.

Geração de incidentes
---------------------
Regenera ``is_incident_start=1`` via ``apply_incidents_d009`` sobre a
telemetria CAT de junho. Isso bate exatamente com a label do parquet
porque a lógica de label é a mesma (mesma definição D009 + tol 30 min).
"""
from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from src.data.incidents import (
    INCIDENT_TOL_MIN_DEFAULT,
    aggregate_incidents,
    apply_incidents_d009,
)
from src.data.loaders import get_connection, load_telemetria_lazy
from src.data.mappings import TAG_FROTA_TO_OEM


@dataclass(frozen=True)
class IncidentLeadTimeRow:
    """Uma linha do parquet ``lead_times_jun_h{H}.parquet``.

    ``status`` ∈ {"TP", "FN"}; ``lead_time_min`` é NaN para FN.
    """

    TAG: str
    Tag_Frota: str
    incident_id: int
    t_I: pd.Timestamp
    alarme_inicio: str
    n_positive_preds: int
    t_first_positive: pd.Timestamp | None
    lead_time_min: float
    status: str


def load_jun_incidents_cat(
    *,
    tol_min: int = INCIDENT_TOL_MIN_DEFAULT,
    con: duckdb.DuckDBPyConnection | None = None,
) -> pd.DataFrame:
    """Regenera os incidentes de junho via D009 sobre telemetria CAT.

    Retorna DataFrame com 1 linha por incidente, colunas:
    ``[TAG, Tag_Frota, Tipo, incident_id, inicio_inc, fim_inc,
       n_eventos_no_incidente, alarme_inicio, crit_inicio,
       id_crit_inicio, classe_inicio, duracao_min]``.

    Filtra por OEM=Caterpillar (D027) e ``Data_Evento`` em junho/2025.
    """
    if con is None:
        con = get_connection()

    rel = load_telemetria_lazy(con)
    cat_frotas = [k for k, v in TAG_FROTA_TO_OEM.items() if v == "Caterpillar"]
    quoted = ",".join("'" + f.replace("'", "''") + "'" for f in cat_frotas)
    rel_filtered = rel.filter(
        f"Data_Evento >= TIMESTAMP '2025-06-01 00:00:00' "
        f"AND Data_Evento < TIMESTAMP '2025-07-01 00:00:00' "
        f"AND Tag_Frota IN ({quoted})"
    )
    rel_with_start = apply_incidents_d009(rel_filtered, con=con, tol_min=tol_min)
    df = aggregate_incidents(rel_with_start, con=con)
    return df


def pick_threshold_at_precision(
    y_true: np.ndarray,
    y_score: np.ndarray,
    target_precision: float = 0.5,
) -> tuple[float, float, float]:
    """Menor threshold com ``precision ≥ alvo``.

    Retorna ``(threshold, precision_at_threshold, recall_at_threshold)``.
    Se nenhum ponto da PR-curve atinge o alvo, retorna ``(NaN, NaN, NaN)``.
    """
    y, s = np.asarray(y_true), np.asarray(y_score)
    if y.sum() == 0 or y.sum() == len(y):
        return float("nan"), float("nan"), float("nan")
    precs, recs, ths = precision_recall_curve(y, s)
    # ths tem len = len(precs) - 1 (último ponto é (recall=0, precision=1)).
    mask = precs[:-1] >= target_precision
    if not mask.any():
        return float("nan"), float("nan"), float("nan")
    idxs = np.where(mask)[0]
    # menor threshold => maior recall com a precisão ainda no alvo
    chosen = idxs[np.argmin(ths[idxs])]
    return float(ths[chosen]), float(precs[chosen]), float(recs[chosen])


def derive_per_incident_lead_times(
    preds: pd.DataFrame,
    incidents: pd.DataFrame,
    horizon_h: int,
    threshold: float,
) -> pd.DataFrame:
    """Computa lead time per-incidente para um horizonte.

    Parameters
    ----------
    preds
        Saída de PRE-1 com colunas ``[TAG, t_window, score_cal]`` (no mínimo).
    incidents
        Saída de ``load_jun_incidents_cat`` com ``[TAG, incident_id,
        inicio_inc, alarme_inicio, Tag_Frota]``.
    horizon_h
        Horizonte em horas — define a janela ``[t_I − H, t_I]``.
    threshold
        ``score_cal ≥ threshold`` é positiva.
    """
    if not np.isfinite(threshold):
        return _empty_lead_time_frame(incidents)

    p = preds[["TAG", "t_window", "score_cal"]].copy()
    p["t_window"] = pd.to_datetime(p["t_window"])
    p_pos = p[p["score_cal"] >= threshold]

    inc = incidents[
        ["TAG", "Tag_Frota", "incident_id", "inicio_inc", "alarme_inicio"]
    ].copy()
    inc["inicio_inc"] = pd.to_datetime(inc["inicio_inc"])

    win_start = inc["inicio_inc"] - pd.Timedelta(hours=horizon_h)
    inc["_win_start"] = win_start

    merged = inc.merge(p_pos, on="TAG", how="left", suffixes=("", "_pred"))
    in_window = (
        (merged["t_window"] >= merged["_win_start"])
        & (merged["t_window"] <= merged["inicio_inc"])
    )
    merged = merged.assign(_in_window=in_window.fillna(False))

    grouped = merged.groupby(["TAG", "incident_id"], dropna=False, sort=False)

    rows: list[dict] = []
    for (_tag, _iid), grp in grouped:
        first = grp.iloc[0]
        positives = grp[grp["_in_window"]]
        n_pos = int(len(positives))
        if n_pos == 0:
            rows.append(
                {
                    "TAG": first["TAG"],
                    "Tag_Frota": first["Tag_Frota"],
                    "incident_id": int(first["incident_id"]),
                    "t_I": first["inicio_inc"],
                    "alarme_inicio": first["alarme_inicio"],
                    "n_positive_preds": 0,
                    "t_first_positive": pd.NaT,
                    "lead_time_min": float("nan"),
                    "status": "FN",
                }
            )
            continue
        t_first = positives["t_window"].min()
        lead_min = (first["inicio_inc"] - t_first).total_seconds() / 60.0
        rows.append(
            {
                "TAG": first["TAG"],
                "Tag_Frota": first["Tag_Frota"],
                "incident_id": int(first["incident_id"]),
                "t_I": first["inicio_inc"],
                "alarme_inicio": first["alarme_inicio"],
                "n_positive_preds": n_pos,
                "t_first_positive": t_first,
                "lead_time_min": float(lead_min),
                "status": "TP",
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values(["TAG", "incident_id"]).reset_index(drop=True)


def _empty_lead_time_frame(incidents: pd.DataFrame) -> pd.DataFrame:
    """Frame com 1 linha FN por incidente quando o threshold é inalcançável."""
    inc = incidents[
        ["TAG", "Tag_Frota", "incident_id", "inicio_inc", "alarme_inicio"]
    ].copy()
    inc = inc.assign(
        t_I=pd.to_datetime(inc["inicio_inc"]),
        n_positive_preds=0,
        t_first_positive=pd.NaT,
        lead_time_min=float("nan"),
        status="FN",
    ).drop(columns=["inicio_inc"])
    return inc[
        [
            "TAG",
            "Tag_Frota",
            "incident_id",
            "t_I",
            "alarme_inicio",
            "n_positive_preds",
            "t_first_positive",
            "lead_time_min",
            "status",
        ]
    ].reset_index(drop=True)


def per_window_lead_time_quantiles(
    preds: pd.DataFrame,
) -> dict[str, float]:
    """Quantis P25/P50/P75 do lead time per-window (apenas TP por janela).

    Usa ``target_lead_time_min`` materializado (D030 — alvo, não feature).
    """
    mask = (preds["y_true"] == 1) & preds["target_lead_time_min"].notna()
    arr = preds.loc[mask, "target_lead_time_min"].to_numpy(dtype=float)
    if len(arr) == 0:
        return {"p25": float("nan"), "p50": float("nan"), "p75": float("nan")}
    return {
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
    }


__all__ = [
    "IncidentLeadTimeRow",
    "derive_per_incident_lead_times",
    "load_jun_incidents_cat",
    "per_window_lead_time_quantiles",
    "pick_threshold_at_precision",
]
