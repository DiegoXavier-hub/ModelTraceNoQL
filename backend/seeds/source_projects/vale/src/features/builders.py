"""Engenharia de features sequenciais por janela (Fase 3C, núcleo).

Versao 2 (2026-05-03) — corrige 6 achados metodologicos da auditoria
documentados em PENDENCIAS.md (sessao anterior). As correcoes sao:

D029 (filtro Operando)
    Janelas sao geradas apenas onde existe um ciclo de apontamento com
    `Classe='Operando'` cobrindo `t_window`. Antes a versao 1 fazia
    `TAGs CROSS JOIN time_grid`, gerando 40,5% das janelas em Parado /
    Hibernando / Manutencao / sem-apontamento. Apenas janelas em ciclo
    `Operando` correspondem ao regime onde `Don't Go` e operacionalmente
    relevante.

D030 (lead_time como alvo, nao feature)
    `lead_time_to_next_incident_min` foi renomeado, prefixado com
    `target_` e clipado ao horizonte maximo (12h) — alem disso ele NAO
    deve ser usado como entrada de classificadores (auditoria mostrou
    78,27% das linhas com lead_time preenchido alem de 12h, ou seja,
    alvo futuro vazando como feature). A coluna fica preservada como
    apoio a sobrevivencia (D017) e analise.

D020 v2 (sem_tel != zero_events)
    `tem_telemetria=0` agora indica especificamente: o ciclo Operando
    cobrindo `t_window` nao tem **nenhum evento de telemetria**.
    Quando `tem_telemetria=0`, as contagens `n_*` sao preservadas como
    `NaN`, NAO substituidas por zero — assim modelos como LightGBM e
    XGBoost lidam com missing nativamente em vez de confundir
    "sem telemetria" com "zero alarmes registrados".

D031 (P99 fixo, anti-leakage)
    O limiar P99 por (Alarme, Tag_Frota) e calibrado externamente em
    `src/features/outlier_calibration.py` sobre janeiro+fevereiro 2025
    (anterior aos folds de validacao do walk-forward) e persistido em
    `data/processed/outlier_p99_thresholds.parquet`. O builder LE este
    limiar como constante externa, sem nenhum recalculo por mes.

D032 (flag de censura temporal)
    Adiciona `lookback_completo` (1 se ha 12h de historia anterior a
    `t_window` — i.e., `t >= '2025-01-01' + 12h`) e `label_completa_12h`
    (1 se ha 12h apos `t` — i.e., `t <= '2025-06-30 12:00`). A Fase 4
    pode escolher dropar janelas com flag=0 ou tratar como missing.

Volume estimado v2: ~321.500 windows (vs 538.848 da v1; queda explicada
pelo filtro Operando).

Princípio governante: ROBUSTEZ > custo computacional.

Uso típico
----------
    from src.data.loaders import get_connection, load_telemetria_lazy
    from src.features.builders import build_features_for_month

    con = get_connection()
    rel_tel = load_telemetria_lazy(con)
    df_jan = build_features_for_month(rel_tel, "2025-01", con=con)
    df_jan.to_parquet("data/processed/features_2025-01.parquet")
"""
from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pandas as pd

from src.features.families import FAMILIES_SQL_CASE, FAMILY_NAMES
from src.features.outlier_calibration import load_p99_thresholds

# ---------------------------------------------------------------------------
# Constantes operacionais (D008, D010, D001 v2)
# ---------------------------------------------------------------------------
WINDOW_STRIDE_MIN: int = 15            # D008
BLACKOUT_MIN: int = 5                  # D010
LOOKBACK_WINDOWS_H: tuple[int, ...] = (1, 4, 12)
LABEL_HORIZONS_H: tuple[int, ...] = (1, 2, 4, 6, 8, 12)  # D001 v2

# Bordas globais do periodo de estudo (para flags de censura D032).
PERIODO_INICIO: str = "2025-01-01 00:00:00"
PERIODO_FIM: str = "2025-07-01 00:00:00"  # exclusivo


@dataclass(frozen=True)
class FeatureBuildReport:
    mes: str
    n_windows: int
    n_tags: int
    n_features_count: int
    n_labels: int
    n_categorical: int
    pct_tem_telemetria: float
    pct_lookback_completo: float
    pct_label_completa_12h: float
    n_dontgo_1h: int
    n_dontgo_12h: int
    elapsed_s: float

    def summary(self) -> str:
        return (
            f"FeatureBuildReport(mes={self.mes}, windows={self.n_windows:,}, "
            f"tags={self.n_tags}, n_features={self.n_features_count}, "
            f"n_labels={self.n_labels}, n_cat={self.n_categorical}, "
            f"tem_tel={self.pct_tem_telemetria:.1f}%, "
            f"lb_compl={self.pct_lookback_completo:.1f}%, "
            f"y_1h={self.n_dontgo_1h:,}, y_12h={self.n_dontgo_12h:,}, "
            f"t={self.elapsed_s:.1f}s)"
        )


# ---------------------------------------------------------------------------
# SQL fragments
# ---------------------------------------------------------------------------
def _family_count_sql(window_alias: str) -> str:
    parts = []
    for name in FAMILY_NAMES:
        col = f"n_fam_{name.lower()}_{window_alias}"
        parts.append(
            f"SUM(CASE WHEN family = '{name}' THEN 1 ELSE 0 END) AS {col}"
        )
    return ",\n            ".join(parts)


def _sql_for_window(
    rel_with_family_sql: str,
    incidents_sql: str,
    apt_table: str,
    p99_table: str,
    mes_start: str,
    mes_end: str,
    stride_min: int,
    blackout_min: int,
    lookback_h: tuple[int, ...],
    label_h: tuple[int, ...],
) -> str:
    """SQL completo (v2) — gera apenas janelas em ciclos Operando.

    Estrutura em CTEs:
    - `time_grid`: instantes t com stride de stride_min minutos no mes.
    - `windows`: INNER JOIN entre time_grid e apontamentos com
      Classe='Operando' (apt.Inicio <= t < apt.Fim). Substitui o
      CROSS JOIN da v1 (correcao do achado #1).
    - `tel_enriched`: telemetria + familia + flag de outlier P99 com
      limiar EXTERNO (correcao do achado #6).
    - `agg_<H>h`: agregacoes por janela de lookback. Apenas janelas com
      ao menos 1 evento sao registradas (LEFT JOIN com w por
      `tem_telemetria_aux` definido a partir do JOIN de range).
    - `labels_<H>h`: target binaria por horizonte H.
    - `lead_time`: alvo auxiliar `target_lead_time_to_next_incident_min`,
      clipado ao max(label_h) horas (correcao do achado #3).
    - SELECT final junta tudo, com `tem_telemetria` derivado a partir
      da existencia de eventos (D020 v2 — correcao do achado #2).
    """
    largest_W_h = max(lookback_h)
    largest_H_h = max(label_h)

    # 1) Lookback aggregations (tem_telemetria_aux por window).
    lookback_ctes: list[str] = []
    lookback_joins: list[str] = []
    lookback_cols: list[str] = []

    for W in lookback_h:
        alias = f"{W}h"
        fam_sql = _family_count_sql(alias)
        cte = f"""
        agg_{alias} AS (
            SELECT
                w.TAG, w.t,
                COUNT(t.Data_Evento) AS n_evt_raw_{alias},
                COUNT(t.Data_Evento) AS n_evt_{alias},
                SUM(CASE WHEN t.Id_Criticidade = 1 THEN 1 ELSE 0 END) AS n_crit_{alias},
                SUM(CASE WHEN t.Id_Criticidade = 2 THEN 1 ELSE 0 END) AS n_naocrit_{alias},
                SUM(CASE WHEN t.Id_Criticidade IN (3, 4) THEN 1 ELSE 0 END) AS n_info_{alias},
                SUM(CASE WHEN t.Classe = 'Activate' THEN 1 ELSE 0 END) AS n_classe_active_{alias},
                COUNT(DISTINCT t.Alarme) AS n_distinct_alarmes_{alias},
                SUM(CASE WHEN t.is_valor_outlier_p99 = 1 THEN 1 ELSE 0 END) AS n_outlier_p99_{alias},
                {fam_sql}
            FROM windows w
            LEFT JOIN tel_enriched t
              ON t.TAG = w.TAG
             AND t.Data_Evento >  w.t - INTERVAL '{W}' HOUR
             AND t.Data_Evento <= w.t - INTERVAL '{blackout_min}' MINUTE
            GROUP BY ALL
        )
        """
        lookback_ctes.append(cte)
        lookback_joins.append(
            f"LEFT JOIN agg_{alias} a{alias} ON a{alias}.TAG = w.TAG AND a{alias}.t = w.t"
        )
        cols = [
            f"a{alias}.n_evt_{alias}",
            f"a{alias}.n_crit_{alias}",
            f"a{alias}.n_naocrit_{alias}",
            f"a{alias}.n_info_{alias}",
            f"a{alias}.n_classe_active_{alias}",
            f"a{alias}.n_distinct_alarmes_{alias}",
            f"a{alias}.n_outlier_p99_{alias}",
        ]
        for name in FAMILY_NAMES:
            cols.append(f"a{alias}.n_fam_{name.lower()}_{alias}")
        lookback_cols.extend(cols)

    # 2) Labels: por horizonte H.
    label_ctes: list[str] = []
    label_joins: list[str] = []
    label_cols: list[str] = []
    for H in label_h:
        alias = f"{H}h"
        cte = f"""
        labels_{alias} AS (
            SELECT
                w.TAG, w.t,
                MAX(CASE WHEN i.Data_Evento >  w.t
                       AND i.Data_Evento <= w.t + INTERVAL '{H}' HOUR
                     THEN 1 ELSE 0 END) AS y_dontgo_{alias}
            FROM windows w
            LEFT JOIN incidents_pop i
              ON i.TAG = w.TAG
             AND i.Data_Evento >  w.t
             AND i.Data_Evento <= w.t + INTERVAL '{H}' HOUR
            GROUP BY ALL
        )
        """
        label_ctes.append(cte)
        label_joins.append(
            f"LEFT JOIN labels_{alias} l{alias} ON l{alias}.TAG = w.TAG AND l{alias}.t = w.t"
        )
        label_cols.append(f"COALESCE(l{alias}.y_dontgo_{alias}, 0) AS y_dontgo_{alias}")

    # 3) lead time clipado ao horizonte maximo (D030).
    lead_time_cte = f"""
        lead_time AS (
            SELECT
                w.TAG, w.t,
                MIN(date_diff('minute', w.t, i.Data_Evento)) AS raw_lead_min
            FROM windows w
            LEFT JOIN incidents_pop i
              ON i.TAG = w.TAG
             AND i.Data_Evento > w.t
             AND i.Data_Evento <= w.t + INTERVAL '{largest_H_h}' HOUR
            GROUP BY ALL
        )
    """

    sql = f"""
    WITH
    time_grid AS (
        SELECT UNNEST(generate_series(
            TIMESTAMP '{mes_start}',
            TIMESTAMP '{mes_end}' - INTERVAL '{stride_min}' MINUTE,
            INTERVAL '{stride_min}' MINUTE
        )) AS t
    ),
    -- D029: janelas SOMENTE em ciclos Operando (INNER JOIN).
    windows AS (
        SELECT
            apt.Tag AS TAG,
            apt.Tag_Frota AS Tag_Frota,
            g.t AS t
        FROM time_grid g
        INNER JOIN {apt_table} apt
          ON apt.Inicio <= g.t
         AND apt.Fim    >  g.t
         AND apt.Classe = 'Operando'
    ),
    -- D031: P99 carregado externamente (jan+fev anterior aos folds).
    tel_with_family AS (
        SELECT t.*,
               {FAMILIES_SQL_CASE} AS family
        FROM ({rel_with_family_sql}) t
    ),
    tel_enriched AS (
        SELECT
            t.*,
            CASE WHEN t.Valor_num IS NOT NULL
                  AND p.p99 IS NOT NULL
                  AND t.Valor_num > p.p99
                 THEN 1 ELSE 0 END AS is_valor_outlier_p99
        FROM tel_with_family t
        LEFT JOIN {p99_table} p
          ON p.Alarme = t.Alarme
         AND p.Tag_Frota = t.Tag_Frota
    ),
    incidents_pop AS (
        SELECT * FROM ({incidents_sql})
        WHERE is_incident_start = 1
    ),
    {','.join(lookback_ctes)}
    , {','.join(label_ctes)}
    , {lead_time_cte}
    SELECT
        w.TAG,
        w.Tag_Frota,
        w.t AS t_window,
        EXTRACT(HOUR FROM w.t) AS hora,
        EXTRACT(DOW FROM w.t) AS dow,
        EXTRACT(MONTH FROM w.t) AS mes_num,
        -- D032: flags de censura temporal.
        CASE WHEN w.t >= TIMESTAMP '{PERIODO_INICIO}' + INTERVAL '{largest_W_h}' HOUR
             THEN 1 ELSE 0 END AS lookback_completo,
        CASE WHEN w.t <= TIMESTAMP '{PERIODO_FIM}' - INTERVAL '{largest_H_h}' HOUR
             THEN 1 ELSE 0 END AS label_completa_{largest_H_h}h,
        {', '.join(lookback_cols)},
        {', '.join(label_cols)},
        -- D030: lead_time como ALVO auxiliar, clipado a {largest_H_h}h.
        lt.raw_lead_min AS target_lead_time_min
    FROM windows w
    {' '.join(lookback_joins)}
    {' '.join(label_joins)}
    LEFT JOIN lead_time lt ON lt.TAG = w.TAG AND lt.t = w.t
    """
    return sql


def _build_tel_enriched_sql(
    rel_telemetria: duckdb.DuckDBPyRelation,
) -> str:
    """SQL fragment que retorna a telemetria base (sem outlier flag).

    A flag `is_valor_outlier_p99` agora e calculada na CTE `tel_enriched`
    do `_sql_for_window`, com JOIN no limiar externo `p99_table`.
    """
    base = "(" + rel_telemetria.sql_query() + ")"
    return f"SELECT * FROM {base}"


def _build_incidents_sql(
    rel_telemetria: duckdb.DuckDBPyRelation,
    tol_min: int = 30,
) -> str:
    base = "(" + rel_telemetria.sql_query() + ")"
    tol_s = tol_min * 60
    return f"""
    WITH dontgo AS (
        SELECT TAG, Data_Evento, Is_Dont_Go
        FROM {base}
        WHERE Is_Dont_Go = 1
    ),
    ord AS (
        SELECT TAG, Data_Evento,
               LAG(Data_Evento) OVER (PARTITION BY TAG ORDER BY Data_Evento) AS prev_evt
        FROM dontgo
    )
    SELECT TAG, Data_Evento,
           CASE WHEN prev_evt IS NULL
                  OR date_diff('second', prev_evt, Data_Evento) > {tol_s}
                THEN 1 ELSE 0 END AS is_incident_start
    FROM ord
    """


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------
def build_features_for_month(
    rel_telemetria: duckdb.DuckDBPyRelation,
    mes: str,
    *,
    con: duckdb.DuckDBPyConnection,
    stride_min: int = WINDOW_STRIDE_MIN,
    blackout_min: int = BLACKOUT_MIN,
    lookback_h: tuple[int, ...] = LOOKBACK_WINDOWS_H,
    label_h: tuple[int, ...] = LABEL_HORIZONS_H,
    tol_min_incident: int = 30,
) -> tuple[pd.DataFrame, FeatureBuildReport]:
    """Constroi dataset de features (v2 corrigida) para um mes.

    Volume esperado por mes: ~50.000-60.000 janelas (apenas Operando).
    """
    import time

    from src.data.loaders import load_apontamentos
    from src.data.mappings import (
        TAG_FROTA_TO_CAPACIDADE_T,
        TAG_FROTA_TO_OEM,
        TAG_FROTA_TO_PORTE,
        TAG_FROTA_TO_TIPO,
        hora_bucket,
        turno_da_hora,
    )

    t0 = time.time()
    mes_start = f"{mes}-01 00:00:00"
    y, m = map(int, mes.split("-"))
    mes_end_str = (
        f"{y + 1}-01-01 00:00:00" if m == 12 else f"{y}-{m + 1:02d}-01 00:00:00"
    )

    # 1) Limiar P99 externo (D031).
    p99_table = load_p99_thresholds(con)

    # 2) Apontamentos completos enriquecidos com Tag_Frota.
    apt = load_apontamentos(con)
    apt["Inicio"] = pd.to_datetime(apt["Inicio"])
    apt["Fim"] = pd.to_datetime(apt["Fim"])
    # Apontamentos nao tem Tag_Frota — derivamos via mapping de TAG na
    # populacao (ja consolidado em mappings; usamos a propria telemetria).
    tag_to_frota = con.sql(
        "SELECT TAG, ANY_VALUE(Tag_Frota) AS Tag_Frota "
        + f"FROM ({rel_telemetria.sql_query()}) "
        + "GROUP BY TAG"
    ).df()
    apt = apt.merge(tag_to_frota, left_on="Tag", right_on="TAG", how="left")
    apt = apt[["Tag", "Tag_Frota", "Inicio", "Fim", "Classe"]]
    con.register("apt_for_windows", apt)

    tel_sql = _build_tel_enriched_sql(rel_telemetria)
    inc_sql = _build_incidents_sql(rel_telemetria, tol_min=tol_min_incident)

    sql = _sql_for_window(
        rel_with_family_sql=tel_sql,
        incidents_sql=inc_sql,
        apt_table="apt_for_windows",
        p99_table=p99_table,
        mes_start=mes_start,
        mes_end=mes_end_str,
        stride_min=stride_min,
        blackout_min=blackout_min,
        lookback_h=lookback_h,
        label_h=label_h,
    )

    df = con.sql(sql).df()

    largest_W = max(lookback_h)
    largest_H = max(label_h)

    # D020 v2: tem_telemetria=0 quando nao ha eventos no maior lookback;
    # contagens permanecem como NaN nessas linhas (nao zero).
    df["tem_telemetria"] = (df[f"n_evt_{largest_W}h"].fillna(0) > 0).astype("int8")

    # Variaveis temporais derivadas.
    df["bucket_hora"] = df["hora"].astype(int).map(hora_bucket)
    df["turno"] = df["hora"].astype(int).map(turno_da_hora)

    # Categoricas via mappings.
    df["Porte"] = df["Tag_Frota"].map(TAG_FROTA_TO_PORTE)
    df["OEM"] = df["Tag_Frota"].map(TAG_FROTA_TO_OEM)
    df["Tipo_canonico"] = df["Tag_Frota"].map(TAG_FROTA_TO_TIPO)
    df["Capacidade_t"] = df["Tag_Frota"].map(TAG_FROTA_TO_CAPACIDADE_T)
    df["mes_str"] = mes

    # D020 v2: N_xx ficam Int64 nullable e SAO substituidos por NaN nas
    # janelas com tem_telemetria=0. Antes da substituicao, COUNT(*) sobre
    # particoes vazias retorna 0 — semanticamente diferente de "ciclo
    # Operando sem nenhum evento de telemetria nas Wh anteriores", que
    # exige missing nativo para LightGBM/XGBoost lidarem como tal.
    int_cols_count = [c for c in df.columns if c.startswith("n_")]
    no_tel_mask = df["tem_telemetria"] == 0
    for c in int_cols_count:
        df[c] = df[c].astype("Int64")  # nullable int
        df.loc[no_tel_mask, c] = pd.NA

    # D030: target_lead_time_min e Float64 nullable (clipado a 12h+ no SQL).
    if "target_lead_time_min" in df.columns:
        df["target_lead_time_min"] = pd.to_numeric(
            df["target_lead_time_min"], errors="coerce"
        )

    # Labels y_dontgo_* sao 0/1 sem missing.
    label_cols = [c for c in df.columns if c.startswith("y_dontgo_")]
    for c in label_cols:
        df[c] = df[c].fillna(0).astype("int64")

    # Flags de censura D032: int8.
    for c in df.columns:
        if c.startswith("lookback_completo") or c.startswith("label_completa_"):
            df[c] = df[c].astype("int8")

    elapsed = time.time() - t0

    report = FeatureBuildReport(
        mes=mes,
        n_windows=len(df),
        n_tags=int(df["TAG"].nunique()),
        n_features_count=len(int_cols_count),
        n_labels=len(label_cols),
        n_categorical=sum(
            1
            for c in df.columns
            if c
            in {
                "Tag_Frota",
                "bucket_hora",
                "turno",
                "Porte",
                "OEM",
                "Tipo_canonico",
            }
        ),
        pct_tem_telemetria=float(df["tem_telemetria"].mean() * 100),
        pct_lookback_completo=float(df["lookback_completo"].mean() * 100),
        pct_label_completa_12h=float(df[f"label_completa_{largest_H}h"].mean() * 100),
        n_dontgo_1h=int(df["y_dontgo_1h"].sum()) if "y_dontgo_1h" in df.columns else 0,
        n_dontgo_12h=int(df["y_dontgo_12h"].sum()) if "y_dontgo_12h" in df.columns else 0,
        elapsed_s=elapsed,
    )

    con.unregister("apt_for_windows")
    return df, report


__all__ = [
    "WINDOW_STRIDE_MIN",
    "BLACKOUT_MIN",
    "LOOKBACK_WINDOWS_H",
    "LABEL_HORIZONS_H",
    "PERIODO_INICIO",
    "PERIODO_FIM",
    "FeatureBuildReport",
    "build_features_for_month",
]
