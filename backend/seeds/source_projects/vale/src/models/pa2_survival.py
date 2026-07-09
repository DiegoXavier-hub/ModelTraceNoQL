"""PA-2 Análise de sobrevivência (D017) — Cox PH + Weibull AFT.

Frame de scoring (D017)
-----------------------
Para cada janela ``(TAG, t)`` em ciclo Operando (CAT):
- T = ``target_lead_time_min`` se preenchido (incidente em até 12h);
  caso contrário, T = 720 (clipe horizonte máximo, censura).
- E = 1 se incidente observado em (t, t+12h]; E = 0 se censura.

Modelos
-------
- ``CoxPHFitter`` (lifelines) — primário; ``proportional_hazard_test`` (Schoenfeld).
- ``WeibullAFTFitter`` (lifelines) — fallback se Schoenfeld rejeita PH.

Métricas (D017)
---------------
- C-index (concordance) — primária.
- IBS (integrated Brier score) em janelas {1, 2, 4, 8, 12}h.

Pré-processamento
-----------------
- Categóricas one-hot (lifelines não aceita categorical dtype nativo).
- Features sem variância (Tipo_canonico, OEM, Porte) descartadas.
- Tratamento de NaN: imputação por mediana (CoxPH não aceita NaN).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, WeibullAFTFitter
from lifelines.statistics import proportional_hazard_test
from lifelines.utils import concordance_index

from src.utils.seeds import SEED

LEAD_TIME_CAP = 720.0  # 12 h em minutos (D030)


def build_survival_frame(
    df: pd.DataFrame,
    feature_cols: list[str] | None = None,
    cat_cols: tuple[str, ...] = ("Tag_Frota", "bucket_hora", "turno"),
) -> tuple[pd.DataFrame, pd.Series, pd.Series, list[str]]:
    """Constrói (X, T, E, used_cols) para ajuste de Cox/Weibull.

    Retorna features one-hot, tempos T (minutos) e indicador E (1=evento, 0=censura).
    """
    df = df.copy()
    is_incident = df["target_lead_time_min"].notna() & (
        df["target_lead_time_min"] > 0
    )
    T = df["target_lead_time_min"].where(is_incident, LEAD_TIME_CAP).astype(float)
    T = np.clip(T, 1.0, LEAD_TIME_CAP)
    E = is_incident.astype(int)

    if feature_cols is None:
        # Pega 66 contagens + categóricas
        feature_cols = [c for c in df.columns if c.startswith("n_")]
    X = df[feature_cols].copy()
    # Imputação mediana para NaN (sem-telemetria)
    X = X.fillna(X.median(numeric_only=True)).fillna(0)
    # One-hot categóricas presentes
    cats_used = []
    for c in cat_cols:
        if c in df.columns:
            d = pd.get_dummies(df[c].astype(str), prefix=c, drop_first=True)
            X = pd.concat([X, d], axis=1)
            cats_used.append(c)
    # Drop colunas constantes ou quase-zero variance
    nunique = X.nunique()
    keep = nunique[nunique > 1].index.tolist()
    X = X[keep].astype(float)
    return X, T.reset_index(drop=True), E.reset_index(drop=True), keep


def fit_cox(
    X: pd.DataFrame,
    T: pd.Series,
    E: pd.Series,
    penalizer: float = 0.01,
) -> CoxPHFitter:
    df = X.copy()
    df["T"] = T.values
    df["E"] = E.values
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(df, duration_col="T", event_col="E", show_progress=False)
    return cph


def fit_weibull(
    X: pd.DataFrame,
    T: pd.Series,
    E: pd.Series,
    penalizer: float = 0.01,
) -> WeibullAFTFitter:
    df = X.copy()
    df["T"] = T.values
    df["E"] = E.values
    aft = WeibullAFTFitter(penalizer=penalizer)
    aft.fit(df, duration_col="T", event_col="E", show_progress=False)
    return aft


def schoenfeld_summary(
    cph: CoxPHFitter, X: pd.DataFrame, T: pd.Series, E: pd.Series
) -> dict[str, Any]:
    """Roda teste de Schoenfeld global e por covariável."""
    df = X.copy()
    df["T"] = T.values
    df["E"] = E.values
    try:
        results = proportional_hazard_test(cph, df, time_transform="rank")
        summary = results.summary
        n_violators = int((summary["p"] < 0.05).sum())
        return {
            "n_features_tested": int(len(summary)),
            "n_violators_p_lt_005": n_violators,
            "global_p_min": float(summary["p"].min()),
            "global_p_median": float(summary["p"].median()),
            "violation_ratio": round(n_violators / max(1, len(summary)), 4),
        }
    except Exception as e:
        return {"error": str(e)}


def cox_concordance_at_t(
    cph: CoxPHFitter, X: pd.DataFrame, T: pd.Series, E: pd.Series
) -> float:
    """C-index sobre o conjunto."""
    risk = cph.predict_partial_hazard(X).values
    return float(concordance_index(T, -risk, E))


def weibull_concordance(
    aft: WeibullAFTFitter, X: pd.DataFrame, T: pd.Series, E: pd.Series
) -> float:
    """C-index do AFT (usa expectativa como tempo predito)."""
    pred = aft.predict_expectation(X).values
    return float(concordance_index(T, pred, E))


def integrated_brier_score(
    cph: CoxPHFitter,
    X: pd.DataFrame,
    T: pd.Series,
    E: pd.Series,
    times: tuple[float, ...] = (60, 120, 240, 480, 720),
) -> dict[str, float]:
    """IBS aproximado em horizontes específicos.

    Usa Brier score por horizonte sem censura ajustada (KM weighting omitido).
    Suficiente para comparação entre folds.
    """
    out: dict[str, float] = {}
    surv = cph.predict_survival_function(X, times=list(times))
    surv_arr = surv.values  # shape (n_times, n_samples)
    for i, t in enumerate(times):
        true_event = ((T <= t) & (E == 1)).astype(int).values
        pred_event = 1.0 - surv_arr[i]
        bs = float(np.mean((pred_event - true_event) ** 2))
        out[f"brier_{int(t)}min"] = round(bs, 6)
    out["ibs_avg"] = float(np.mean(list(out.values())))
    return out


__all__ = [
    "LEAD_TIME_CAP",
    "build_survival_frame",
    "fit_cox",
    "fit_weibull",
    "schoenfeld_summary",
    "cox_concordance_at_t",
    "weibull_concordance",
    "integrated_brier_score",
]
