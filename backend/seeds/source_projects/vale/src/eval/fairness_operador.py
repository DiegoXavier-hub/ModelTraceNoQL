"""Auditoria de fairness por operador (Fase 6 — Frente F1).

Estrutura: para cada incidente do JUN holdout (já materializado em
``outputs/predictions/lead_times_jun_h{H}.parquet``), inferir o operador
predominante na janela de 30 min anterior ao início do incidente
(t_I - 30 min, t_I), via telemetria. Em seguida, agregar Recall por
incidente, contagem de FN e Lead time mediano por operador.

Disparidade reportada: razão entre o operador top-quartil e o operador
bottom-quartil de Recall, restrito a operadores com n >= 10 incidentes
em JUN.

Princípio: D016 estabelece que a inferência de operador via
``share_moda >= 80%`` cobre 61.5% dos ciclos. Neste módulo, aplicamos
filtro análogo: se a moda dos eventos da janela 30-min antes do
incidente cobre menos que 50% dos eventos, o incidente é marcado como
"operador_indefinido" e não compõe a estatística por operador.

Saída: ``reports/eda_results/fase6_fairness_operador.json`` +
tabela ``reports/tables/fase6_fairness_operador.csv``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
import numpy as np
import pandas as pd

from src.utils.paths import OUTPUTS_DIR, REPORTS_DIR, TELEMETRIA_DIR


HORIZONS = [1, 2, 4, 6, 8, 12]


def _telemetry_glob() -> str:
    # JUN único arquivo
    return str(TELEMETRIA_DIR / "telemetry_jun.parquet").replace("\\", "/")


def infer_operator_per_incident(
    lead_times: pd.DataFrame, lookback_min: int = 30, share_threshold: float = 0.5
) -> pd.DataFrame:
    """Para cada incidente, inferir operador na janela 30-min pré-início.

    Args:
        lead_times: DataFrame de ``lead_times_jun_h{H}.parquet`` com
            colunas ['TAG', 'incident_id', 't_I', 'status', ...].
        lookback_min: Janela em minutos antes de t_I para inferir
            operador (default 30).
        share_threshold: Fração mínima da moda. Abaixo disso, o
            operador é "indefinido".

    Returns:
        DataFrame com colunas ['TAG', 'incident_id', 't_I', 'status',
        'operador_inferido', 'operador_share', 'n_eventos_30min'].
    """
    if lead_times.empty:
        return lead_times.assign(
            operador_inferido=pd.NA, operador_share=np.nan, n_eventos_30min=0
        )
    df_in = lead_times[["TAG", "incident_id", "t_I", "status", "lead_time_min"]].copy()
    df_in["t_I"] = pd.to_datetime(df_in["t_I"])
    df_in["t_lookback_start"] = df_in["t_I"] - pd.Timedelta(minutes=lookback_min)

    con = duckdb.connect()
    con.register("incidents", df_in)
    glob = _telemetry_glob()
    q = f"""
    WITH evt AS (
        SELECT
            t.TAG,
            t.Data_Evento,
            t.Nome_Operador_Anon AS op
        FROM read_parquet('{glob}') t
        WHERE t.Nome_Operador_Anon IS NOT NULL
    ),
    win AS (
        SELECT
            i.TAG,
            i.incident_id,
            i.t_I,
            i.status,
            i.lead_time_min,
            i.t_lookback_start,
            e.op,
            COUNT(*) AS n_evt
        FROM incidents i
        LEFT JOIN evt e
          ON e.TAG = i.TAG
         AND e.Data_Evento >= i.t_lookback_start
         AND e.Data_Evento <  i.t_I
        WHERE e.op IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7
    ),
    ranked AS (
        SELECT
            *,
            SUM(n_evt) OVER (PARTITION BY TAG, incident_id) AS total_evt,
            ROW_NUMBER() OVER (
                PARTITION BY TAG, incident_id
                ORDER BY n_evt DESC, op ASC
            ) AS rk
        FROM win
    )
    SELECT
        TAG,
        incident_id,
        t_I,
        status,
        lead_time_min,
        op AS operador_inferido,
        1.0 * n_evt / NULLIF(total_evt, 0) AS operador_share,
        total_evt AS n_eventos_30min
    FROM ranked
    WHERE rk = 1
    """
    res = con.execute(q).df()
    con.close()

    # Apply share_threshold filter
    res["operador_estavel"] = (
        (res["operador_share"].astype(float) >= share_threshold).astype("Int8")
    )
    res.loc[res["operador_estavel"] == 0, "operador_inferido"] = pd.NA

    # Merge back: incidents without telemetry events get NaN operator
    full = df_in.merge(
        res[
            [
                "TAG",
                "incident_id",
                "operador_inferido",
                "operador_share",
                "n_eventos_30min",
                "operador_estavel",
            ]
        ],
        on=["TAG", "incident_id"],
        how="left",
    )
    full["n_eventos_30min"] = full["n_eventos_30min"].fillna(0).astype(int)
    return full


def aggregate_per_operator(
    df: pd.DataFrame, min_incidents: int = 10
) -> pd.DataFrame:
    """Agrega métricas por operador (apenas com n >= min_incidents)."""
    df_op = df[df["operador_inferido"].notna()].copy()
    df_op["is_tp"] = (df_op["status"] == "TP").astype(int)
    grp = df_op.groupby("operador_inferido")
    agg = grp.agg(
        n_incidentes=("incident_id", "count"),
        n_TP=("is_tp", "sum"),
        recall_per_incident=("is_tp", "mean"),
        lead_p50_min=(
            "lead_time_min",
            lambda s: float(np.median(s.dropna())) if s.dropna().size else np.nan,
        ),
    )
    agg["n_FN"] = agg["n_incidentes"] - agg["n_TP"]
    agg = agg[agg["n_incidentes"] >= min_incidents]
    agg = agg.sort_values("recall_per_incident", ascending=False)
    return agg.reset_index()


def gini_coefficient(values: np.ndarray) -> float:
    """Coeficiente de Gini sobre uma distribuição não-negativa.

    Definição clássica: 0 = uniforme; 1 = totalmente concentrado.
    """
    x = np.asarray(values, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return float("nan")
    if np.all(x == 0):
        return 0.0
    x_sorted = np.sort(x)
    n = x_sorted.size
    cum = np.cumsum(x_sorted)
    # Gini = (2 * sum(i * x_i) - (n+1) * sum(x_i)) / (n * sum(x_i))
    return float((2.0 * np.sum(np.arange(1, n + 1) * x_sorted) - (n + 1) * cum[-1]) / (n * cum[-1]))


def disparity_ratio(agg: pd.DataFrame, top_q: float = 0.75, bot_q: float = 0.25) -> Optional[float]:
    """Razão Recall(top-quartil) / Recall(bottom-quartil)."""
    if agg.empty or "recall_per_incident" not in agg.columns:
        return None
    rec = agg["recall_per_incident"].dropna()
    if rec.size < 4:
        return None
    top = float(np.quantile(rec, top_q))
    bot = float(np.quantile(rec, bot_q))
    if bot <= 0:
        return float("inf")
    return top / bot


def run_fairness_audit(
    horizons: List[int] = HORIZONS,
    lookback_min: int = 30,
    share_threshold: float = 0.5,
    min_incidents: int = 10,
    persist: bool = True,
) -> Dict:
    """Executa fairness audit para todos os horizontes."""
    out: Dict = {
        "config": {
            "lookback_min": lookback_min,
            "share_threshold": share_threshold,
            "min_incidents_per_operator": min_incidents,
            "horizons": horizons,
        },
        "per_horizon": {},
    }
    rows_csv: List[Dict] = []
    for h in horizons:
        lt_path = OUTPUTS_DIR / "predictions" / f"lead_times_jun_h{h}.parquet"
        if not lt_path.is_file():
            continue
        lt = pd.read_parquet(lt_path)
        df = infer_operator_per_incident(lt, lookback_min=lookback_min, share_threshold=share_threshold)
        agg = aggregate_per_operator(df, min_incidents=min_incidents)

        n_total = int(len(df))
        n_with_op = int(df["operador_inferido"].notna().sum())
        share_with_op = n_with_op / n_total if n_total > 0 else float("nan")

        gini_recall = gini_coefficient(agg["recall_per_incident"].to_numpy()) if not agg.empty else float("nan")
        disp = disparity_ratio(agg)

        out["per_horizon"][f"h{h}"] = {
            "n_incidents_total": n_total,
            "n_incidents_with_operator": n_with_op,
            "share_with_operator": share_with_op,
            "n_operadores_min10_incid": int(len(agg)),
            "gini_recall": gini_recall,
            "disparity_ratio_q75_over_q25": disp,
            "top_5_operadores_by_recall": agg.head(5).to_dict(orient="records"),
            "bottom_5_operadores_by_recall": agg.tail(5).to_dict(orient="records"),
        }
        for _, r in agg.iterrows():
            rows_csv.append(
                {
                    "horizon_h": h,
                    "operador_inferido": r["operador_inferido"],
                    "n_incidentes": r["n_incidentes"],
                    "n_TP": r["n_TP"],
                    "n_FN": r["n_FN"],
                    "recall_per_incident": r["recall_per_incident"],
                    "lead_p50_min": r["lead_p50_min"],
                }
            )

    if persist:
        target_json = REPORTS_DIR / "eda_results" / "fase6_fairness_operador.json"
        target_json.parent.mkdir(parents=True, exist_ok=True)
        with open(target_json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False, default=str)
        target_csv = REPORTS_DIR / "tables" / "fase6_fairness_operador.csv"
        target_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows_csv).to_csv(target_csv, index=False, encoding="utf-8")
    return out
