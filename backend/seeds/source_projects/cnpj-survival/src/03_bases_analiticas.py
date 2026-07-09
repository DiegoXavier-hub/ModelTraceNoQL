from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "processed"
TMP_DIR = Path.home() / "AppData" / "Local" / "Temp" / "duckdb_cnpj_03"
SUMMARY_PATH = ROOT / "tables" / "resumo_bases_analiticas.json"
SNAPSHOT_DATE_SQL = "DATE '2026-03-15'"


def human_size(num: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1000 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1000
    return f"{num} B"


def normalize_numbers(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: normalize_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_numbers(v) for v in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def build_con() -> duckdb.DuckDBPyConnection:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"PRAGMA temp_directory='{TMP_DIR.as_posix()}'")
    con.execute("PRAGMA threads=4")
    con.execute("SET preserve_insertion_order=false")
    return con


def output_path(name: str) -> Path:
    return OUT_DIR / name


def output_scan(name: str) -> str:
    return f"parquet_scan('{output_path(name).resolve().as_posix()}')"


def build_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE OR REPLACE VIEW empresa_base AS
        SELECT * FROM {output_scan('empresa_base.parquet')}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW estabelecimento_base AS
        SELECT * FROM {output_scan('estabelecimento_base.parquet')}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW socio_base AS
        SELECT * FROM {output_scan('socio_base.parquet')}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW simples_base AS
        SELECT * FROM {output_scan('simples_base.parquet')}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW regimes_anuais_base AS
        SELECT * FROM {output_scan('regimes_anuais_base.parquet')}
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW matriz_empresa AS
        SELECT *
        FROM estabelecimento_base
        WHERE identificador_matriz_filial = '1'
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW socio_agregado AS
        SELECT
            cnpj_basico,
            COUNT(*) AS qtd_socios_total_snapshot,
            SUM(CASE WHEN identificador_socio = '1' THEN 1 ELSE 0 END) AS qtd_socios_pj_snapshot,
            SUM(CASE WHEN identificador_socio = '2' THEN 1 ELSE 0 END) AS qtd_socios_pf_snapshot,
            SUM(CASE WHEN identificador_socio = '3' THEN 1 ELSE 0 END) AS qtd_socios_estrangeiro_snapshot,
            COUNT(DISTINCT qualificacao_socio) AS qtd_qualificacoes_socio_snapshot,
            MAX(CASE WHEN pais_desc LIKE 'CODIGO_NAO_MAPEADO_%' THEN 1 ELSE 0 END) = 1 AS flag_socio_pais_nao_mapeado_snapshot
        FROM socio_base
        GROUP BY 1
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW regime_empresa_ano AS
        SELECT
            cnpj_basico,
            ano,
            SUM(COALESCE(quantidade_de_escrituracoes, 0)) AS qtd_escrituracoes_regime_ano,
            MAX(CASE WHEN forma_de_tributacao = 'LUCRO REAL' THEN 1 ELSE 0 END) = 1 AS flag_lucro_real_ano,
            MAX(CASE WHEN forma_de_tributacao = 'LUCRO PRESUMIDO' THEN 1 ELSE 0 END) = 1 AS flag_lucro_presumido_ano,
            MAX(CASE WHEN forma_de_tributacao = 'LUCRO ARBITRADO' THEN 1 ELSE 0 END) = 1 AS flag_lucro_arbitrado_ano,
            MAX(CASE WHEN forma_de_tributacao IN ('IMUNE DE IRPJ', 'ISENTO DO IRPJ') THEN 1 ELSE 0 END) = 1 AS flag_imune_ou_isenta_ano
        FROM regimes_anuais_base
        GROUP BY 1, 2
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW regime_empresa_latest AS
        WITH ranked AS (
            SELECT
                *,
                ROW_NUMBER() OVER (PARTITION BY cnpj_basico ORDER BY ano DESC) AS rn
            FROM regime_empresa_ano
        )
        SELECT
            cnpj_basico,
            ano AS ano_regime_snapshot,
            qtd_escrituracoes_regime_ano AS qtd_escrituracoes_regime_snapshot,
            flag_lucro_real_ano AS flag_lucro_real_snapshot,
            flag_lucro_presumido_ano AS flag_lucro_presumido_snapshot,
            flag_lucro_arbitrado_ano AS flag_lucro_arbitrado_snapshot,
            flag_imune_ou_isenta_ano AS flag_imune_ou_isenta_snapshot
        FROM ranked
        WHERE rn = 1
        """
    )


def copy_parquet(con: duckdb.DuckDBPyConnection, sql: str, output_name: str) -> None:
    path = output_path(output_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con.execute(
        f"""
        COPY (
            {sql}
        ) TO '{path.resolve().as_posix()}'
        (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 500000)
        """
    )


def survival_sql() -> str:
    return f"""
    SELECT
        m.cnpj_basico,
        m.cnpj_14 AS cnpj_14_matriz,
        m.data_inicio_atividade,
        CASE
            WHEN m.situacao_cadastral = '08' THEN m.data_situacao_cadastral
            ELSE {SNAPSHOT_DATE_SQL}
        END AS data_evento_ou_censura,
        CASE WHEN m.situacao_cadastral = '08' THEN 1 ELSE 0 END AS evento_baixa,
        CASE WHEN m.situacao_cadastral = '08' THEN m.data_situacao_cadastral ELSE NULL END AS data_baixa,
        {SNAPSHOT_DATE_SQL} AS data_referencia_censura,
        date_diff('day', m.data_inicio_atividade, CASE WHEN m.situacao_cadastral = '08' THEN m.data_situacao_cadastral ELSE {SNAPSHOT_DATE_SQL} END) AS tempo_em_dias,
        ROUND(date_diff('day', m.data_inicio_atividade, CASE WHEN m.situacao_cadastral = '08' THEN m.data_situacao_cadastral ELSE {SNAPSHOT_DATE_SQL} END) / 30.4375, 2) AS tempo_em_meses,
        EXTRACT(YEAR FROM m.data_inicio_atividade) AS coorte_abertura_ano,
        e.natureza_juridica AS natureza_juridica_snapshot,
        e.natureza_juridica_desc AS natureza_juridica_desc_snapshot,
        e.qualificacao_responsavel AS qualificacao_responsavel_snapshot,
        e.qualificacao_responsavel_desc AS qualificacao_responsavel_desc_snapshot,
        e.capital_social AS capital_social_snapshot,
        e.porte AS porte_snapshot,
        e.porte_desc AS porte_desc_snapshot,
        m.cnae_fiscal_principal AS cnae_fiscal_principal_snapshot,
        m.cnae_fiscal_principal_desc AS cnae_fiscal_principal_desc_snapshot,
        m.qtd_cnaes_secundarios AS qtd_cnaes_secundarios_snapshot,
        m.uf AS uf_snapshot,
        m.regiao AS regiao_snapshot,
        m.municipio AS municipio_snapshot,
        m.municipio_desc AS municipio_desc_snapshot,
        m.pais AS pais_snapshot,
        m.pais_desc AS pais_desc_snapshot,
        COALESCE(s.flag_optante_simples, FALSE) AS flag_optante_simples_snapshot,
        COALESCE(s.flag_optante_mei, FALSE) AS flag_optante_mei_snapshot,
        COALESCE(s.flag_ja_excluido_simples, FALSE) AS flag_ja_excluido_simples_snapshot,
        COALESCE(s.flag_ja_excluido_mei, FALSE) AS flag_ja_excluido_mei_snapshot,
        COALESCE(sa.qtd_socios_total_snapshot, 0) AS qtd_socios_total_snapshot,
        COALESCE(sa.qtd_socios_pj_snapshot, 0) AS qtd_socios_pj_snapshot,
        COALESCE(sa.qtd_socios_pf_snapshot, 0) AS qtd_socios_pf_snapshot,
        COALESCE(sa.qtd_socios_estrangeiro_snapshot, 0) AS qtd_socios_estrangeiro_snapshot,
        COALESCE(sa.qtd_qualificacoes_socio_snapshot, 0) AS qtd_qualificacoes_socio_snapshot,
        COALESCE(sa.flag_socio_pais_nao_mapeado_snapshot, FALSE) AS flag_socio_pais_nao_mapeado_snapshot,
        rl.ano_regime_snapshot,
        COALESCE(rl.qtd_escrituracoes_regime_snapshot, 0) AS qtd_escrituracoes_regime_snapshot,
        COALESCE(rl.flag_lucro_real_snapshot, FALSE) AS flag_lucro_real_snapshot,
        COALESCE(rl.flag_lucro_presumido_snapshot, FALSE) AS flag_lucro_presumido_snapshot,
        COALESCE(rl.flag_lucro_arbitrado_snapshot, FALSE) AS flag_lucro_arbitrado_snapshot,
        COALESCE(rl.flag_imune_ou_isenta_snapshot, FALSE) AS flag_imune_ou_isenta_snapshot
    FROM matriz_empresa m
    INNER JOIN empresa_base e ON m.cnpj_basico = e.cnpj_basico
    LEFT JOIN simples_base s ON m.cnpj_basico = s.cnpj_basico
    LEFT JOIN socio_agregado sa ON m.cnpj_basico = sa.cnpj_basico
    LEFT JOIN regime_empresa_latest rl ON m.cnpj_basico = rl.cnpj_basico
    WHERE m.data_inicio_atividade IS NOT NULL
      AND m.data_inicio_atividade <= {SNAPSHOT_DATE_SQL}
      AND NOT m.flag_cronologia_invalida
      AND (
          m.situacao_cadastral <> '08'
          OR (m.data_situacao_cadastral IS NOT NULL AND m.data_situacao_cadastral >= m.data_inicio_atividade)
      )
    """


def radar_split_sql(obs_date: str, split_name: str) -> str:
    return f"""
    SELECT
        '{split_name}' AS split_temporal,
        DATE '{obs_date}' AS data_observacao,
        EXTRACT(YEAR FROM DATE '{obs_date}') AS ano_observacao,
        m.cnpj_basico,
        m.cnpj_14 AS cnpj_14_matriz,
        m.data_inicio_atividade,
        date_diff('day', m.data_inicio_atividade, DATE '{obs_date}') AS idade_empresa_dias,
        ROUND(date_diff('day', m.data_inicio_atividade, DATE '{obs_date}') / 30.4375, 2) AS idade_empresa_meses,
        EXTRACT(YEAR FROM m.data_inicio_atividade) AS coorte_abertura_ano,
        CASE
            WHEN s.data_opcao_simples IS NOT NULL
             AND s.data_opcao_simples <= DATE '{obs_date}'
             AND (s.data_exclusao_simples IS NULL OR s.data_exclusao_simples > DATE '{obs_date}')
            THEN TRUE ELSE FALSE
        END AS flag_optante_simples_t,
        CASE
            WHEN s.data_opcao_mei IS NOT NULL
             AND s.data_opcao_mei <= DATE '{obs_date}'
             AND (s.data_exclusao_mei IS NULL OR s.data_exclusao_mei > DATE '{obs_date}')
            THEN TRUE ELSE FALSE
        END AS flag_optante_mei_t,
        CASE
            WHEN s.data_exclusao_simples IS NOT NULL AND s.data_exclusao_simples <= DATE '{obs_date}'
            THEN TRUE ELSE FALSE
        END AS flag_excluido_simples_ate_t,
        CASE
            WHEN s.data_exclusao_mei IS NOT NULL AND s.data_exclusao_mei <= DATE '{obs_date}'
            THEN TRUE ELSE FALSE
        END AS flag_excluido_mei_ate_t,
        COALESCE(ra.qtd_escrituracoes_regime_ano, 0) AS qtd_escrituracoes_regime_t,
        CASE WHEN ra.cnpj_basico IS NOT NULL THEN TRUE ELSE FALSE END AS flag_tem_regime_t,
        COALESCE(ra.flag_lucro_real_ano, FALSE) AS flag_lucro_real_t,
        COALESCE(ra.flag_lucro_presumido_ano, FALSE) AS flag_lucro_presumido_t,
        COALESCE(ra.flag_lucro_arbitrado_ano, FALSE) AS flag_lucro_arbitrado_t,
        COALESCE(ra.flag_imune_ou_isenta_ano, FALSE) AS flag_imune_ou_isenta_t,
        CASE
            WHEN m.situacao_cadastral = '08'
             AND m.data_situacao_cadastral > DATE '{obs_date}'
             AND m.data_situacao_cadastral <= DATE '{obs_date}' + INTERVAL 12 MONTH
            THEN 1 ELSE 0
        END AS y_baixa_12m,
        CASE
            WHEN m.situacao_cadastral = '08'
             AND m.data_situacao_cadastral > DATE '{obs_date}'
             AND m.data_situacao_cadastral <= DATE '{obs_date}' + INTERVAL 12 MONTH
            THEN m.data_situacao_cadastral ELSE NULL
        END AS data_baixa_12m,
        CASE
            WHEN m.situacao_cadastral = '08'
             AND m.data_situacao_cadastral > DATE '{obs_date}'
             AND m.data_situacao_cadastral <= DATE '{obs_date}' + INTERVAL 12 MONTH
            THEN date_diff('day', DATE '{obs_date}', m.data_situacao_cadastral) ELSE NULL
        END AS dias_ate_baixa_12m
    FROM matriz_empresa m
    LEFT JOIN simples_base s ON m.cnpj_basico = s.cnpj_basico
    LEFT JOIN regime_empresa_ano ra
        ON m.cnpj_basico = ra.cnpj_basico
       AND ra.ano = EXTRACT(YEAR FROM DATE '{obs_date}')
    WHERE m.data_inicio_atividade IS NOT NULL
      AND m.data_inicio_atividade <= DATE '{obs_date}'
      AND NOT m.flag_cronologia_invalida
      AND (
          m.situacao_cadastral <> '08'
          OR m.data_situacao_cadastral IS NULL
          OR m.data_situacao_cadastral > DATE '{obs_date}'
      )
      AND DATE '{obs_date}' + INTERVAL 12 MONTH <= {SNAPSHOT_DATE_SQL}
    """


def write_outputs(con: duckdb.DuckDBPyConnection) -> None:
    copy_parquet(con, survival_sql(), "survival_empresa.parquet")

    radar_sql = (
        radar_split_sql("2022-12-31", "treino")
        + "\nUNION ALL\n"
        + radar_split_sql("2023-12-31", "validacao")
        + "\nUNION ALL\n"
        + radar_split_sql("2024-12-31", "teste")
    )
    copy_parquet(con, radar_sql, "radar_12m.parquet")
    copy_parquet(con, f"SELECT * FROM {output_scan('radar_12m.parquet')} WHERE split_temporal = 'treino'", "treino_radar_12m.parquet")
    copy_parquet(con, f"SELECT * FROM {output_scan('radar_12m.parquet')} WHERE split_temporal = 'validacao'", "validacao_radar_12m.parquet")
    copy_parquet(con, f"SELECT * FROM {output_scan('radar_12m.parquet')} WHERE split_temporal = 'teste'", "teste_radar_12m.parquet")


def fetch_record(con: duckdb.DuckDBPyConnection, sql: str) -> dict[str, Any]:
    return con.execute(sql).fetchdf().to_dict(orient="records")[0]


def build_summary(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    outputs = {
        "survival_empresa": output_path("survival_empresa.parquet"),
        "radar_12m": output_path("radar_12m.parquet"),
        "treino_radar_12m": output_path("treino_radar_12m.parquet"),
        "validacao_radar_12m": output_path("validacao_radar_12m.parquet"),
        "teste_radar_12m": output_path("teste_radar_12m.parquet"),
    }
    dataset_summary: dict[str, Any] = {}
    for name, path in outputs.items():
        dataset_summary[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "size_human": human_size(path.stat().st_size),
            "rows": fetch_record(con, f"SELECT COUNT(*) AS n FROM parquet_scan('{path.resolve().as_posix()}')")["n"],
        }

    checks = {
        "survival_empresa": fetch_record(
            con,
            f"""
            SELECT
                COUNT(*) AS total_rows,
                SUM(evento_baixa) AS eventos_baixa,
                MIN(data_inicio_atividade) AS data_inicio_min,
                MAX(data_evento_ou_censura) AS data_evento_ou_censura_max,
                SUM(CASE WHEN tempo_em_dias < 0 THEN 1 ELSE 0 END) AS tempos_negativos
            FROM {output_scan('survival_empresa.parquet')}
            """,
        ),
        "radar_12m": fetch_record(
            con,
            f"""
            SELECT
                COUNT(*) AS total_rows,
                SUM(y_baixa_12m) AS positivos_12m,
                MIN(data_observacao) AS data_obs_min,
                MAX(data_observacao) AS data_obs_max
            FROM {output_scan('radar_12m.parquet')}
            """,
        ),
        "splits": con.execute(
            f"""
            SELECT
                split_temporal,
                COUNT(*) AS total_rows,
                SUM(y_baixa_12m) AS positivos_12m,
                ROUND(AVG(CAST(y_baixa_12m AS DOUBLE)), 6) AS taxa_positiva_12m
            FROM {output_scan('radar_12m.parquet')}
            GROUP BY 1
            ORDER BY CASE split_temporal WHEN 'treino' THEN 1 WHEN 'validacao' THEN 2 WHEN 'teste' THEN 3 ELSE 4 END
            """
        ).fetchdf().to_dict(orient="records"),
        "regras_exclusao": fetch_record(
            con,
            """
            WITH base AS (
                SELECT *
                FROM matriz_empresa
            )
            SELECT
                COUNT(*) AS matrizes_totais,
                SUM(CASE WHEN flag_cronologia_invalida THEN 1 ELSE 0 END) AS matrizes_excluidas_cronologia,
                SUM(CASE WHEN data_inicio_atividade IS NULL THEN 1 ELSE 0 END) AS matrizes_excluidas_sem_data_inicio,
                SUM(CASE WHEN data_inicio_atividade > DATE '2026-03-15' THEN 1 ELSE 0 END) AS matrizes_excluidas_inicio_pos_censura
            FROM base
            """,
        ),
    }
    return normalize_numbers({"datasets": dataset_summary, "checks": checks})


def write_report(summary: dict[str, Any]) -> None:
    datasets_rows = [
        [name, info["rows"], info["size_human"], info["path"]]
        for name, info in summary["datasets"].items()
    ]
    split_rows = [
        [row["split_temporal"], row["total_rows"], row["positivos_12m"], row["taxa_positiva_12m"]]
        for row in summary["checks"]["splits"]
    ]
    lines = [
        "# Fase 02 - Unidade Analitica, Sobrevivencia e Radar 12M",
        "",
        "Este documento registra a execucao das Aulas 02 a 04 da Fase 2: definicao da unidade principal no nivel da empresa, construcao da base de sobrevivencia e construcao do radar de risco em 12 meses com split temporal.",
        "",
        "## Regras metodologicas adotadas",
        "",
        "- A unidade principal do projeto foi definida no nivel da empresa, aproximada pela matriz em `Estabelecimentos`.",
        "- A base de sobrevivencia exclui casos com cronologia invalida e usa censura a direita em `2026-03-15`, data ajustada na auditoria final da fase por ser o maximo observado na propria base.",
        "- O evento principal foi definido como `situacao_cadastral = 08` com `data_situacao_cadastral` valida.",
        "- O radar 12M foi construido com tres datas de observacao absolutas: `2022-12-31`, `2023-12-31` e `2024-12-31`.",
        "- Na auditoria final da fase, as colunas `_snapshot` foram removidas de `radar_12m` para evitar leakage temporal por uso de caracteristicas observadas apenas na fotografia cadastral final.",
        "",
        "## Saidas geradas",
        "",
        md_table(["Dataset", "Linhas", "Tamanho", "Arquivo"], datasets_rows),
        "",
        "## Cheques centrais",
        "",
        md_table(
            ["Base", "Cheque", "Valor"],
            [
                ["survival_empresa", "linhas", summary["checks"]["survival_empresa"]["total_rows"]],
                ["survival_empresa", "eventos de baixa", summary["checks"]["survival_empresa"]["eventos_baixa"]],
                ["survival_empresa", "tempos negativos", summary["checks"]["survival_empresa"]["tempos_negativos"]],
                ["radar_12m", "linhas", summary["checks"]["radar_12m"]["total_rows"]],
                ["radar_12m", "positivos 12m", summary["checks"]["radar_12m"]["positivos_12m"]],
                ["matriz", "matrizes excluidas por cronologia", summary["checks"]["regras_exclusao"]["matrizes_excluidas_cronologia"]],
                ["matriz", "matrizes excluidas sem data_inicio", summary["checks"]["regras_exclusao"]["matrizes_excluidas_sem_data_inicio"]],
                ["matriz", "matrizes excluidas por inicio pos censura", summary["checks"]["regras_exclusao"]["matrizes_excluidas_inicio_pos_censura"]],
            ],
        ),
        "",
        "## Splits temporais do radar 12M",
        "",
        md_table(["Split", "Linhas", "Positivos 12m", "Taxa positiva"], split_rows),
        "",
        "## Observacao metodologica importante",
        "",
        "A base `survival_empresa` preserva colunas `_snapshot` para analise descritiva e explicativa com cautela. A base `radar_12m`, por outro lado, foi reduzida a variaveis temporalmente defensaveis (`*_t`, idade e coorte) como correcao metodologica aplicada no fechamento da fase.",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    con = build_con()
    build_views(con)
    write_outputs(con)
    summary = build_summary(con)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary)


if __name__ == "__main__":
    main()
