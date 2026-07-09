"""Tradução técnica → impacto operacional (Fase 5C / CM 6.1).

Operacionaliza a métrica de negócio definida em ``MEMORY §0``:

> Superfície de sensibilidade ``(ΔP, ρ)`` → horas de parada evitadas por mês,
> onde ``ΔP`` é o lead time mínimo aproveitável (min) e ``ρ`` é a fração de
> redução obtida ao mover de parada não-programada para programada.
>
> Apenas TPs com ``lead_time_min ≥ ΔP`` contam como evitados.

Componentes
-----------
- ``derive_d_avg``: P25/P50/P75 da duração média de parada não-programada
  empírica, lendo ``desenvolver_apontamentos.parquet`` filtrado por ``Classe ∈
  {Parado, Manutenção}``.
- ``avoidable_hours_per_month``: para um vetor de lead times per-incidente
  e parâmetros ``(ΔP, ρ, d_avg)``, retorna horas evitadas em junho.
- ``sensitivity_surface``: matriz 4×3 (``ΔP × ρ``) para um horizonte.

Premissas (registradas como D039 em ``decisions.md``)
-----------------------------------------------------
- ``d_avg`` é a *mediana* da distribuição empírica em ``Classe ∈ {Parado,
  Manutenção}`` filtrado por ``dur_min > 0``.
- O período de junho tem 30 dias → multiplicação direta para "horas/mês".
- ``ΔP`` é aplicado como filtro mínimo: TPs com ``lead_time_min < ΔP`` são
  tratados como não-aproveitáveis (operação não tem tempo de reagir).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.utils.paths import APONTAMENTOS_PARQUET

CLASSES_PARADA: tuple[str, ...] = ("Parado", "Manutenção", "Manutencao")


@dataclass(frozen=True)
class DAvgEstimate:
    """Estimativa de ``d_avg`` (duração média de parada não-programada).

    Reporta TRÊS estimativas:

    - ``p50_min``: mediana de TODOS os ciclos crus (``Classe ∈ {Parado,
      Manutenção}`` ∧ ``dur_min > 0``) — inclui micro-paradas operacionais
      (fuel-up, descanso). Referência ampla.
    - ``p50_op_min``: mediana de ciclos com ``dur_min ≥ min_op_min`` (default
      30 min). Filtro de "operacionalmente significativa" — D039.
    - ``p50_phys_min``: mediana de **paradas físicas reconstruídas** (D040)
      agrupando registros consecutivos do mesmo ``Tag`` em ``Classe ∈
      classes`` separados por ``≤ gap_max_min``. Esta é a estimativa
      honesta — o sistema de apontamentos segmenta paradas longas em blocos
      de 60 min.

    Default em 5C: usa ``d_avg_h_phys`` (P50 reconstruído, D040).
    """

    p25_min: float
    p50_min: float
    p75_min: float
    n_ciclos: int
    p25_op_min: float
    p50_op_min: float
    p75_op_min: float
    n_ciclos_op: int
    min_op_min: float
    p25_phys_min: float
    p50_phys_min: float
    p75_phys_min: float
    n_paradas_fisicas: int
    gap_max_min: float
    pct_share_60min_op: float
    classes_filtradas: tuple[str, ...]

    @property
    def d_avg_h(self) -> float:
        """Mediana global em horas (referência ampla)."""
        return self.p50_min / 60.0

    @property
    def d_avg_h_op(self) -> float:
        """Mediana operacional (≥ ``min_op_min``) em horas."""
        return self.p50_op_min / 60.0

    @property
    def d_avg_h_phys(self) -> float:
        """Mediana de paradas físicas reconstruídas (D040) — DEFAULT em 5C."""
        return self.p50_phys_min / 60.0


def reconstruct_physical_stops(
    df: pd.DataFrame,
    *,
    classes: tuple[str, ...] = CLASSES_PARADA,
    gap_max_min: float = 5.0,
) -> pd.DataFrame:
    """D040: agrupa registros consecutivos do mesmo ``Tag`` em paradas físicas.

    Critério: dois registros são da MESMA parada física se
    ``Classe ∈ classes`` em ambos AND ``Inicio_seguinte − Fim_anterior ≤
    gap_max_min`` minutos.

    Retorna DataFrame com 1 linha por parada física, colunas:
    ``[Tag, Frota, classe_inicio, n_blocos, inicio_fisico, fim_fisico,
       dur_fisica_min]``.
    """
    work = df.copy()
    work["Inicio"] = pd.to_datetime(work["Inicio"])
    work["Fim"] = pd.to_datetime(work["Fim"])
    work["dur_min"] = (work["Fim"] - work["Inicio"]).dt.total_seconds() / 60.0
    work = work[work["Classe"].isin(classes) & (work["dur_min"] > 0)].copy()
    work = work.sort_values(["Tag", "Inicio"]).reset_index(drop=True)

    prev_tag = work["Tag"].shift()
    prev_fim = work["Fim"].shift()
    gap_min = (work["Inicio"] - prev_fim).dt.total_seconds() / 60.0
    new_stop = (work["Tag"] != prev_tag) | (gap_min > gap_max_min)
    work["stop_id"] = new_stop.cumsum().astype(int)

    grp = work.groupby(["Tag", "stop_id"], dropna=False, sort=False)
    out = grp.agg(
        Frota=("Frota", "first"),
        classe_inicio=("Classe", "first"),
        n_blocos=("Classe", "size"),
        inicio_fisico=("Inicio", "min"),
        fim_fisico=("Fim", "max"),
    ).reset_index()
    out["dur_fisica_min"] = (
        out["fim_fisico"] - out["inicio_fisico"]
    ).dt.total_seconds() / 60.0
    return out


def derive_d_avg(
    *,
    parquet_path: str | None = None,
    classes: tuple[str, ...] = CLASSES_PARADA,
    min_op_min: float = 30.0,
    gap_max_min: float = 5.0,
) -> DAvgEstimate:
    """Lê o parquet de apontamentos e retorna as três estimativas.

    Aplica defesa em profundidade contra inconsistências (D025): exige
    ``dur_min > 0``.

    Parameters
    ----------
    min_op_min : D039 — só paradas ≥ esse limiar contam para "operacional".
    gap_max_min : D040 — gap máximo (min) entre registros consecutivos para
        considerá-los a mesma parada física.
    """
    path = parquet_path or str(APONTAMENTOS_PARQUET)
    df = pd.read_parquet(path)
    df["Inicio"] = pd.to_datetime(df["Inicio"])
    df["Fim"] = pd.to_datetime(df["Fim"])
    df["dur_min"] = (df["Fim"] - df["Inicio"]).dt.total_seconds() / 60.0
    mask = df["Classe"].isin(classes) & (df["dur_min"] > 0)
    durs = df.loc[mask, "dur_min"].to_numpy(dtype=float)
    if len(durs) == 0:
        raise ValueError("Nenhum ciclo correspondente para derivar d_avg.")

    mask_op = mask & (df["dur_min"] >= min_op_min)
    durs_op = df.loc[mask_op, "dur_min"].to_numpy(dtype=float)
    if len(durs_op) == 0:
        raise ValueError(
            f"Nenhum ciclo com dur >= {min_op_min} min para d_avg operacional."
        )
    pct_share_60min_op = float((durs_op == 60.0).mean()) if len(durs_op) else 0.0

    # D040: paradas físicas reconstruídas, filtradas por duração operacional
    paradas = reconstruct_physical_stops(df, classes=classes, gap_max_min=gap_max_min)
    durs_phys_all = paradas["dur_fisica_min"].to_numpy(dtype=float)
    durs_phys_all = durs_phys_all[durs_phys_all > 0]
    durs_phys = durs_phys_all[durs_phys_all >= min_op_min]  # mesmo filtro op
    if len(durs_phys) == 0:
        raise ValueError(
            "Reconstrução D040 retornou zero paradas físicas operacionais."
        )

    return DAvgEstimate(
        p25_min=float(np.percentile(durs, 25)),
        p50_min=float(np.percentile(durs, 50)),
        p75_min=float(np.percentile(durs, 75)),
        n_ciclos=int(mask.sum()),
        p25_op_min=float(np.percentile(durs_op, 25)),
        p50_op_min=float(np.percentile(durs_op, 50)),
        p75_op_min=float(np.percentile(durs_op, 75)),
        n_ciclos_op=int(mask_op.sum()),
        min_op_min=float(min_op_min),
        p25_phys_min=float(np.percentile(durs_phys, 25)),
        p50_phys_min=float(np.percentile(durs_phys, 50)),
        p75_phys_min=float(np.percentile(durs_phys, 75)),
        n_paradas_fisicas=int(len(durs_phys)),
        gap_max_min=float(gap_max_min),
        pct_share_60min_op=pct_share_60min_op,
        classes_filtradas=classes,
    )


def avoidable_hours_per_month(
    lead_times_min: np.ndarray,
    delta_p_min: float,
    rho: float,
    d_avg_h: float,
) -> dict[str, float]:
    """Retorna horas evitadas por mês para parâmetros (ΔP, ρ, d_avg).

    ``count_TPs`` = ``len(lead_times[lead_times >= delta_p_min])``.
    ``hours_saved = count_TPs × ρ × d_avg_h``.
    """
    arr = np.asarray(lead_times_min, dtype=float)
    arr = arr[~np.isnan(arr)]
    n_aproveitaveis = int((arr >= delta_p_min).sum())
    horas = float(n_aproveitaveis * rho * d_avg_h)
    return {
        "delta_p_min": float(delta_p_min),
        "rho": float(rho),
        "d_avg_h": float(d_avg_h),
        "n_TPs_aproveitaveis": n_aproveitaveis,
        "n_TPs_total": int(len(arr)),
        "hours_saved_per_month": horas,
    }


def sensitivity_surface(
    lead_times_min: np.ndarray,
    *,
    deltas: tuple[float, ...] = (30, 60, 120, 240),
    rhos: tuple[float, ...] = (0.5, 0.7, 0.9),
    d_avg_h: float,
) -> dict[str, list[dict[str, float]]]:
    """Matriz |ΔP| × |ρ| de horas evitadas/mês."""
    rows: list[dict[str, float]] = []
    for dp in deltas:
        for r in rhos:
            rows.append(avoidable_hours_per_month(lead_times_min, dp, r, d_avg_h))
    return {"cells": rows, "deltas": list(deltas), "rhos": list(rhos)}


def recommended_operating_point(
    surface_per_h: dict[int, dict],
    deltas: tuple[float, ...] = (30, 60, 120, 240),
    rhos: tuple[float, ...] = (0.5, 0.7, 0.9),
) -> dict:
    """Recomenda (H, ΔP, ρ) com maior horas/mês entre os horizontes ofertados.

    Ranking: maior ``hours_saved_per_month`` entre todas as células.
    """
    best = None
    for H, surf in surface_per_h.items():
        for cell in surf["cells"]:
            score = cell["hours_saved_per_month"]
            if best is None or score > best["hours_saved_per_month"]:
                best = {**cell, "horizon_h": H}
    return best or {}


__all__ = [
    "CLASSES_PARADA",
    "DAvgEstimate",
    "avoidable_hours_per_month",
    "derive_d_avg",
    "recommended_operating_point",
    "reconstruct_physical_stops",
    "sensitivity_surface",
]
