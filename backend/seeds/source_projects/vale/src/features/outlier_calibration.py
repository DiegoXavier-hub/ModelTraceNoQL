"""Calibracao externa do limiar P99 de `Valor_num` por (Alarme, Tag_Frota).

Problema corrigido (auditoria 2026-05-03):
    A versao anterior do builder calculava `approx_quantile(Valor_num, 0.99)
    OVER (PARTITION BY Alarme, Tag_Frota)` sobre toda a base disponivel
    (jan-jun 2025). Para um pipeline walk-forward (D011) onde junho e o
    teste intocado, esse calculo vaza informacao de junho no limiar usado
    nos folds de treino, contaminando a metrica final.

Correcao adotada (D031):
    O limiar P99 e calibrado **uma unica vez**, em modulo separado, sobre
    um periodo de calibracao **anterior aos folds de validacao e teste**.
    Adotamos `2025-01-01` a `2025-02-28` como periodo de calibracao
    (~22% do volume total de telemetria), suficiente para estimar P99
    estavel em 50+ particoes (Alarme, Tag_Frota), sem que junho ou os
    folds de validacao do walk-forward influenciem o limiar.

    Uma vez calibrado, o limiar e persistido em
    `data/processed/outlier_p99_thresholds.parquet` e e lido pelo builder
    como **constante externa**.

Como rodar (uma unica vez antes do build dos features):
    python -m src.features.outlier_calibration

Uso no builder:
    from src.features.outlier_calibration import load_p99_thresholds
    thr = load_p99_thresholds(con)  # registra como tabela 'p99_thresholds'
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Periodo de calibracao — fixo, anterior ao primeiro fold de walk-forward.
CALIBRATION_START: str = "2025-01-01 00:00:00"
CALIBRATION_END: str = "2025-03-01 00:00:00"  # exclusivo

THRESHOLDS_PARQUET: Path = (
    PROJECT_ROOT / "data" / "processed" / "outlier_p99_thresholds.parquet"
)


def calibrate_p99_thresholds(
    rel_telemetria: duckdb.DuckDBPyRelation,
    *,
    con: duckdb.DuckDBPyConnection,
    start: str = CALIBRATION_START,
    end: str = CALIBRATION_END,
) -> pd.DataFrame:
    """Calcula P99 por (Alarme, Tag_Frota) restrito ao periodo de calibracao.

    Args:
        rel_telemetria: relation lazy (load_telemetria_lazy).
        con: conexao duckdb.
        start: timestamp inclusivo de inicio do periodo.
        end: timestamp exclusivo de fim do periodo.

    Returns:
        DataFrame com colunas (Alarme, Tag_Frota, p99, n_obs).
    """
    base = "(" + rel_telemetria.sql_query() + ")"
    df = con.sql(
        f"""
        SELECT
            Alarme,
            Tag_Frota,
            approx_quantile(Valor_num, 0.99) AS p99,
            COUNT(Valor_num) AS n_obs
        FROM {base}
        WHERE Data_Evento >= TIMESTAMP '{start}'
          AND Data_Evento <  TIMESTAMP '{end}'
          AND Valor_num IS NOT NULL
        GROUP BY ALL
        HAVING COUNT(Valor_num) >= 30
        """
    ).df()
    return df


def save_thresholds(df: pd.DataFrame, path: Path = THRESHOLDS_PARQUET) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def load_p99_thresholds(
    con: duckdb.DuckDBPyConnection,
    *,
    path: Path = THRESHOLDS_PARQUET,
    table_name: str = "p99_thresholds",
) -> str:
    """Registra os limiares como tabela duckdb e retorna o nome.

    Returns:
        Nome da tabela registrada (default `p99_thresholds`).
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Limiares P99 nao encontrados em {path}. "
            "Rode `python -m src.features.outlier_calibration` antes do build."
        )
    df = pd.read_parquet(path)
    con.register(table_name, df)
    return table_name


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    from src.data.loaders import get_connection, load_telemetria_lazy

    con = get_connection()
    con.execute("PRAGMA disable_progress_bar")
    rel = load_telemetria_lazy(con)
    print(
        f"Calibrando P99 por (Alarme, Tag_Frota) sobre [{CALIBRATION_START}, "
        f"{CALIBRATION_END}) ..."
    )
    df = calibrate_p99_thresholds(rel, con=con)
    save_thresholds(df)
    print(f"Persistido em {THRESHOLDS_PARQUET}")
    print(f"  particoes (Alarme, Tag_Frota) com n_obs >= 30: {len(df):,}")
    print(
        f"  p99 stats: min={df['p99'].min():.3f} | "
        f"p50={df['p99'].median():.3f} | max={df['p99'].max():.3f}"
    )
