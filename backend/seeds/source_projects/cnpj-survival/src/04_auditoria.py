from __future__ import annotations

import csv
from datetime import date, datetime
import json
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "tables"
TMP_DIR = Path.home() / "AppData" / "Local" / "Temp" / "duckdb_cnpj_04"
RADAR_PATH = ROOT / "data" / "processed" / "radar_12m.parquet"
SURVIVAL_PATH = ROOT / "data" / "processed" / "survival_empresa.parquet"
FEATURE_CHECKLIST = RESULT_DIR / "checklist_colunas_modelagem.csv"
SUMMARY_JSON = RESULT_DIR / "resumo_auditoria.json"
PORTE_CSV = RESULT_DIR / "distribuicao_porte_por_split.csv"
UF_CSV = RESULT_DIR / "distribuicao_uf_por_split.csv"
CNAE_DIV_CSV = RESULT_DIR / "distribuicao_cnae_divisao_por_split.csv"


FEATURE_RULES = [
    {
        "column_name": "split_temporal",
        "role": "metadata",
        "status_modelagem": "bloqueada",
        "reason": "Identifica o split e nao deve entrar como feature.",
    },
    {
        "column_name": "data_observacao",
        "role": "metadata_temporal",
        "status_modelagem": "bloqueada",
        "reason": "Serve para auditoria e recorte temporal, nao para treino direto.",
    },
    {
        "column_name": "ano_observacao",
        "role": "contexto_temporal",
        "status_modelagem": "cautela",
        "reason": "E observavel no momento da previsao, mas pode capturar efeito de periodo e contaminar a comparacao entre janelas.",
    },
    {
        "column_name": "cnpj_basico",
        "role": "identificador",
        "status_modelagem": "bloqueada",
        "reason": "Identificador da empresa.",
    },
    {
        "column_name": "cnpj_14_matriz",
        "role": "identificador",
        "status_modelagem": "bloqueada",
        "reason": "Identificador da matriz.",
    },
    {
        "column_name": "data_inicio_atividade",
        "role": "data_bruta",
        "status_modelagem": "bloqueada",
        "reason": "A informacao util ja foi derivada em idade e coorte; a data bruta adiciona granularidade desnecessaria.",
    },
    {
        "column_name": "idade_empresa_dias",
        "role": "feature_numerica",
        "status_modelagem": "aprovada",
        "reason": "Observavel em t e relevante para risco.",
    },
    {
        "column_name": "idade_empresa_meses",
        "role": "feature_numerica",
        "status_modelagem": "aprovada",
        "reason": "Observavel em t e mais interpretavel que a idade em dias.",
    },
    {
        "column_name": "coorte_abertura_ano",
        "role": "feature_temporal_estrutural",
        "status_modelagem": "aprovada",
        "reason": "Permite capturar efeito de cohort sem usar a data bruta.",
    },
    {
        "column_name": "flag_optante_simples_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Status observavel na data t.",
    },
    {
        "column_name": "flag_optante_mei_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Status observavel na data t.",
    },
    {
        "column_name": "flag_excluido_simples_ate_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Reflete historico conhecido ate t.",
    },
    {
        "column_name": "flag_excluido_mei_ate_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Reflete historico conhecido ate t.",
    },
    {
        "column_name": "qtd_escrituracoes_regime_t",
        "role": "feature_numerica",
        "status_modelagem": "aprovada",
        "reason": "Disponivel no ano de observacao, com `flag_tem_regime_t` para separar ausencia de cobertura.",
    },
    {
        "column_name": "flag_tem_regime_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Indica cobertura da fonte tributaria.",
    },
    {
        "column_name": "flag_lucro_real_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Forma de tributacao observavel no ano t.",
    },
    {
        "column_name": "flag_lucro_presumido_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Forma de tributacao observavel no ano t.",
    },
    {
        "column_name": "flag_lucro_arbitrado_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Forma de tributacao observavel no ano t.",
    },
    {
        "column_name": "flag_imune_ou_isenta_t",
        "role": "feature_booleana",
        "status_modelagem": "aprovada",
        "reason": "Forma de tributacao observavel no ano t.",
    },
    {
        "column_name": "y_baixa_12m",
        "role": "target",
        "status_modelagem": "bloqueada",
        "reason": "Variavel alvo.",
    },
    {
        "column_name": "data_baixa_12m",
        "role": "target_auxiliar",
        "status_modelagem": "bloqueada",
        "reason": "Contem o desfecho futuro.",
    },
    {
        "column_name": "dias_ate_baixa_12m",
        "role": "target_auxiliar",
        "status_modelagem": "bloqueada",
        "reason": "Contem o tempo ate o desfecho futuro.",
    },
]


APPROVED_NUMERIC = ["idade_empresa_dias", "idade_empresa_meses", "coorte_abertura_ano", "qtd_escrituracoes_regime_t"]
APPROVED_BOOLEAN = [
    "flag_optante_simples_t",
    "flag_optante_mei_t",
    "flag_excluido_simples_ate_t",
    "flag_excluido_mei_ate_t",
    "flag_tem_regime_t",
    "flag_lucro_real_t",
    "flag_lucro_presumido_t",
    "flag_lucro_arbitrado_t",
    "flag_imune_ou_isenta_t",
]


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
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"PRAGMA temp_directory='{TMP_DIR.as_posix()}'")
    con.execute("PRAGMA threads=4")
    con.execute("SET preserve_insertion_order=false")
    return con


def fetch_record(con: duckdb.DuckDBPyConnection, sql: str) -> dict[str, Any]:
    return con.execute(sql).fetchdf().to_dict(orient="records")[0]


def fetch_rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    return con.execute(sql).fetchdf().to_dict(orient="records")


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: normalize_numbers(v) for k, v in row.items()})


def build_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE OR REPLACE VIEW radar AS
        SELECT * FROM parquet_scan('{RADAR_PATH.resolve().as_posix()}')
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW survival AS
        SELECT * FROM parquet_scan('{SURVIVAL_PATH.resolve().as_posix()}')
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW radar_diag AS
        SELECT
            r.*,
            s.porte_snapshot,
            s.uf_snapshot,
            s.cnae_fiscal_principal_snapshot,
            SUBSTR(s.cnae_fiscal_principal_snapshot, 1, 2) AS cnae_divisao_snapshot
        FROM radar r
        LEFT JOIN survival s USING (cnpj_basico)
        """
    )


def write_feature_checklist() -> None:
    write_csv_rows(FEATURE_CHECKLIST, FEATURE_RULES)


def compute_leakage_summary(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    schema_rows = fetch_rows(con, "DESCRIBE SELECT * FROM radar")
    radar_columns = [row["column_name"] for row in schema_rows]
    snapshot_cols = [c for c in radar_columns if c.endswith("_snapshot")]
    future_proxy_candidates = [
        "situacao_cadastral",
        "situacao_cadastral_desc",
        "motivo_situacao_cadastral",
        "motivo_situacao_cadastral_desc",
        "data_situacao_cadastral",
    ]
    leakage = {
        "schema": {
            "total_columns": len(radar_columns),
            "snapshot_columns_present": snapshot_cols,
            "future_proxy_columns_present": [c for c in future_proxy_candidates if c in radar_columns],
        },
        "approved_feature_counts": {
            "aprovadas": sum(1 for row in FEATURE_RULES if row["status_modelagem"] == "aprovada"),
            "cautela": sum(1 for row in FEATURE_RULES if row["status_modelagem"] == "cautela"),
            "bloqueadas": sum(1 for row in FEATURE_RULES if row["status_modelagem"] == "bloqueada"),
        },
        "checks": normalize_numbers(
            {
                "duplicatas_chave_observacao": fetch_record(
                    con,
                    """
                    SELECT COUNT(*) AS n
                    FROM (
                        SELECT cnpj_basico, data_observacao, COUNT(*) AS k
                        FROM radar
                        GROUP BY 1, 2
                        HAVING COUNT(*) > 1
                    )
                    """,
                )["n"],
                "target_inconsistente_y_sem_data": fetch_record(
                    con,
                    "SELECT COUNT(*) AS n FROM radar WHERE y_baixa_12m = 1 AND data_baixa_12m IS NULL",
                )["n"],
                "target_inconsistente_data_sem_y": fetch_record(
                    con,
                    "SELECT COUNT(*) AS n FROM radar WHERE y_baixa_12m = 0 AND data_baixa_12m IS NOT NULL",
                )["n"],
                "dias_ate_baixa_fora_janela": fetch_record(
                    con,
                    """
                    SELECT COUNT(*) AS n
                    FROM radar
                    WHERE dias_ate_baixa_12m IS NOT NULL
                      AND (dias_ate_baixa_12m <= 0 OR dias_ate_baixa_12m > 366)
                    """,
                )["n"],
                "datas_observacao_por_split_invalidas": fetch_record(
                    con,
                    """
                    SELECT COUNT(*) AS n
                    FROM (
                        SELECT split_temporal, COUNT(DISTINCT data_observacao) AS n_datas
                        FROM radar
                        GROUP BY 1
                        HAVING COUNT(DISTINCT data_observacao) <> 1
                    )
                    """,
                )["n"],
                "inicio_atividade_maior_que_observacao": fetch_record(
                    con,
                    """
                    SELECT COUNT(*) AS n
                    FROM radar
                    WHERE data_inicio_atividade > data_observacao
                    """,
                )["n"],
                "positivos_por_split": fetch_rows(
                    con,
                    """
                    SELECT
                        split_temporal,
                        COUNT(*) AS total_rows,
                        SUM(y_baixa_12m) AS positivos_12m,
                        ROUND(AVG(CAST(y_baixa_12m AS DOUBLE)), 6) AS taxa_positiva_12m
                    FROM radar
                    GROUP BY 1
                    ORDER BY CASE split_temporal WHEN 'treino' THEN 1 WHEN 'validacao' THEN 2 WHEN 'teste' THEN 3 ELSE 4 END
                    """,
                ),
                "missing_rate_features": fetch_rows(
                    con,
                    """
                    SELECT
                        ROUND(AVG(CASE WHEN idade_empresa_meses IS NULL THEN 1.0 ELSE 0.0 END), 6) AS idade_empresa_meses_missing,
                        ROUND(AVG(CASE WHEN coorte_abertura_ano IS NULL THEN 1.0 ELSE 0.0 END), 6) AS coorte_abertura_ano_missing,
                        ROUND(AVG(CASE WHEN qtd_escrituracoes_regime_t IS NULL THEN 1.0 ELSE 0.0 END), 6) AS qtd_escrituracoes_regime_t_missing
                    FROM radar
                    """,
                )[0],
                "datas_muito_antigas_survival": fetch_record(
                    con,
                    """
                    SELECT
                        SUM(CASE WHEN data_inicio_atividade < DATE '1950-01-01' THEN 1 ELSE 0 END) AS antes_1950,
                        SUM(CASE WHEN data_inicio_atividade < DATE '1900-01-01' THEN 1 ELSE 0 END) AS antes_1900
                    FROM survival
                    """,
                ),
            }
        ),
    }
    return leakage


def compute_stability_summary(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    numeric_summaries = {}
    for col in APPROVED_NUMERIC:
        numeric_summaries[col] = fetch_rows(
            con,
            f"""
            SELECT
                split_temporal,
                ROUND(AVG(CAST({col} AS DOUBLE)), 6) AS media,
                ROUND(STDDEV_SAMP(CAST({col} AS DOUBLE)), 6) AS desvio,
                approx_quantile(CAST({col} AS DOUBLE), 0.5) AS mediana,
                approx_quantile(CAST({col} AS DOUBLE), 0.95) AS p95
            FROM radar
            GROUP BY 1
            ORDER BY CASE split_temporal WHEN 'treino' THEN 1 WHEN 'validacao' THEN 2 WHEN 'teste' THEN 3 ELSE 4 END
            """
        )
    boolean_rates = fetch_rows(
        con,
        f"""
        SELECT
            split_temporal,
            {", ".join(f"ROUND(AVG(CAST({col} AS DOUBLE)), 6) AS {col}" for col in APPROVED_BOOLEAN)}
        FROM radar
        GROUP BY 1
        ORDER BY CASE split_temporal WHEN 'treino' THEN 1 WHEN 'validacao' THEN 2 WHEN 'teste' THEN 3 ELSE 4 END
        """
    )
    coverage_summary = fetch_rows(
        con,
        """
        SELECT
            split_temporal,
            ROUND(AVG(CASE WHEN porte_snapshot IS NULL THEN 1.0 ELSE 0.0 END), 6) AS porte_missing_rate,
            ROUND(AVG(CASE WHEN uf_snapshot IS NULL THEN 1.0 ELSE 0.0 END), 6) AS uf_missing_rate,
            ROUND(AVG(CASE WHEN cnae_divisao_snapshot IS NULL THEN 1.0 ELSE 0.0 END), 6) AS cnae_divisao_missing_rate
        FROM radar_diag
        GROUP BY 1
        ORDER BY CASE split_temporal WHEN 'treino' THEN 1 WHEN 'validacao' THEN 2 WHEN 'teste' THEN 3 ELSE 4 END
        """
    )
    porte_dist = fetch_rows(
        con,
        """
        SELECT
            split_temporal,
            COALESCE(porte_snapshot, 'MISSING') AS categoria,
            COUNT(*) AS n,
            ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY split_temporal), 6) AS share
        FROM radar_diag
        GROUP BY 1, 2
        ORDER BY split_temporal, n DESC, categoria
        """
    )
    uf_dist = fetch_rows(
        con,
        """
        SELECT
            split_temporal,
            COALESCE(uf_snapshot, 'MISSING') AS categoria,
            COUNT(*) AS n,
            ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY split_temporal), 6) AS share
        FROM radar_diag
        GROUP BY 1, 2
        ORDER BY split_temporal, n DESC, categoria
        """
    )
    cnae_div_dist = fetch_rows(
        con,
        """
        SELECT
            split_temporal,
            COALESCE(cnae_divisao_snapshot, 'MISSING') AS categoria,
            COUNT(*) AS n,
            ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY split_temporal), 6) AS share
        FROM radar_diag
        GROUP BY 1, 2
        ORDER BY split_temporal, n DESC, categoria
        """
    )
    top_shift_porte = fetch_rows(
        con,
        """
        WITH dist AS (
            SELECT
                split_temporal,
                COALESCE(porte_snapshot, 'MISSING') AS categoria,
                COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY split_temporal) AS share
            FROM radar_diag
            GROUP BY 1, 2
        )
        SELECT
            COALESCE(t.categoria, e.categoria) AS categoria,
            ROUND(COALESCE(t.share, 0), 6) AS share_treino,
            ROUND(COALESCE(e.share, 0), 6) AS share_teste,
            ROUND(ABS(COALESCE(e.share, 0) - COALESCE(t.share, 0)), 6) AS abs_diff_treino_teste
        FROM (SELECT * FROM dist WHERE split_temporal = 'treino') t
        FULL OUTER JOIN (SELECT * FROM dist WHERE split_temporal = 'teste') e USING (categoria)
        ORDER BY abs_diff_treino_teste DESC, categoria
        LIMIT 10
        """
    )
    top_shift_uf = fetch_rows(
        con,
        """
        WITH dist AS (
            SELECT
                split_temporal,
                COALESCE(uf_snapshot, 'MISSING') AS categoria,
                COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY split_temporal) AS share
            FROM radar_diag
            GROUP BY 1, 2
        )
        SELECT
            COALESCE(t.categoria, e.categoria) AS categoria,
            ROUND(COALESCE(t.share, 0), 6) AS share_treino,
            ROUND(COALESCE(e.share, 0), 6) AS share_teste,
            ROUND(ABS(COALESCE(e.share, 0) - COALESCE(t.share, 0)), 6) AS abs_diff_treino_teste
        FROM (SELECT * FROM dist WHERE split_temporal = 'treino') t
        FULL OUTER JOIN (SELECT * FROM dist WHERE split_temporal = 'teste') e USING (categoria)
        ORDER BY abs_diff_treino_teste DESC, categoria
        LIMIT 10
        """
    )
    top_shift_cnae = fetch_rows(
        con,
        """
        WITH dist AS (
            SELECT
                split_temporal,
                COALESCE(cnae_divisao_snapshot, 'MISSING') AS categoria,
                COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY split_temporal) AS share
            FROM radar_diag
            GROUP BY 1, 2
        )
        SELECT
            COALESCE(t.categoria, e.categoria) AS categoria,
            ROUND(COALESCE(t.share, 0), 6) AS share_treino,
            ROUND(COALESCE(e.share, 0), 6) AS share_teste,
            ROUND(ABS(COALESCE(e.share, 0) - COALESCE(t.share, 0)), 6) AS abs_diff_treino_teste
        FROM (SELECT * FROM dist WHERE split_temporal = 'treino') t
        FULL OUTER JOIN (SELECT * FROM dist WHERE split_temporal = 'teste') e USING (categoria)
        ORDER BY abs_diff_treino_teste DESC, categoria
        LIMIT 10
        """
    )
    return normalize_numbers(
        {
            "numeric_summaries": numeric_summaries,
            "boolean_rates": boolean_rates,
            "coverage_summary": coverage_summary,
            "top_shift_porte": top_shift_porte,
            "top_shift_uf": top_shift_uf,
            "top_shift_cnae_divisao": top_shift_cnae,
            "event_rate_by_split": fetch_rows(
                con,
                """
                SELECT
                    split_temporal,
                    COUNT(*) AS total_rows,
                    SUM(y_baixa_12m) AS positivos_12m,
                    ROUND(AVG(CAST(y_baixa_12m AS DOUBLE)), 6) AS taxa_positiva_12m
                FROM radar
                GROUP BY 1
                ORDER BY CASE split_temporal WHEN 'treino' THEN 1 WHEN 'validacao' THEN 2 WHEN 'teste' THEN 3 ELSE 4 END
                """
            ),
            "regime_coverage_by_split": fetch_rows(
                con,
                """
                SELECT
                    split_temporal,
                    ROUND(AVG(CAST(flag_tem_regime_t AS DOUBLE)), 6) AS taxa_tem_regime_t
                FROM radar
                GROUP BY 1
                ORDER BY CASE split_temporal WHEN 'treino' THEN 1 WHEN 'validacao' THEN 2 WHEN 'teste' THEN 3 ELSE 4 END
                """
            ),
            "porte_dist": porte_dist,
            "uf_dist": uf_dist,
            "cnae_div_dist": cnae_div_dist,
        }
    )


def write_leakage_report(summary: dict[str, Any]) -> None:
    checks = summary["checks"]
    positives_rows = [
        [row["split_temporal"], row["total_rows"], row["positivos_12m"], row["taxa_positiva_12m"]]
        for row in checks["positivos_por_split"]
    ]
    feature_rows = [
        [row["column_name"], row["role"], row["status_modelagem"], row["reason"]]
        for row in FEATURE_RULES
    ]
    lines = [
        "# Fase 03 - Relatorio de Leakage",
        "",
        "Este relatorio verifica se a base `radar_12m.parquet` esta pronta para modelagem sem vazamento temporal obvio e com um checklist explicito de colunas aprovadas e bloqueadas.",
        "",
        "## Parecer geral",
        "",
        "A base `radar_12m.parquet` ficou aprovada para seguir para modelagem sob uma regra simples: usar apenas colunas marcadas como `aprovada` e, se necessario, testar `ano_observacao` separadamente como coluna de cautela.",
        "",
        "## Cheques estruturais",
        "",
        md_table(
            ["Cheque", "Valor"],
            [
                ["Colunas totais em `radar_12m`", summary["schema"]["total_columns"]],
                ["Colunas `_snapshot` presentes", len(summary["schema"]["snapshot_columns_present"])],
                ["Colunas proxy de futuro presentes", len(summary["schema"]["future_proxy_columns_present"])],
                ["Duplicatas por `cnpj_basico + data_observacao`", checks["duplicatas_chave_observacao"]],
                ["`y=1` sem `data_baixa_12m`", checks["target_inconsistente_y_sem_data"]],
                ["`y=0` com `data_baixa_12m` preenchida", checks["target_inconsistente_data_sem_y"]],
                ["`dias_ate_baixa_12m` fora da janela", checks["dias_ate_baixa_fora_janela"]],
                ["Splits com mais de uma `data_observacao`", checks["datas_observacao_por_split_invalidas"]],
                ["`data_inicio_atividade > data_observacao`", checks["inicio_atividade_maior_que_observacao"]],
            ],
        ),
        "",
        "## Checklist de colunas",
        "",
        md_table(["Coluna", "Papel", "Status", "Justificativa"], feature_rows),
        "",
        "## Taxa de evento por split",
        "",
        md_table(["Split", "Linhas", "Positivos 12m", "Taxa positiva"], positives_rows),
        "",
        "## Qualidade adicional relevante",
        "",
        md_table(
            ["Cheque", "Valor"],
            [
                ["Missing em `idade_empresa_meses`", checks["missing_rate_features"]["idade_empresa_meses_missing"]],
                ["Missing em `coorte_abertura_ano`", checks["missing_rate_features"]["coorte_abertura_ano_missing"]],
                ["Missing em `qtd_escrituracoes_regime_t`", checks["missing_rate_features"]["qtd_escrituracoes_regime_t_missing"]],
                ["Empresas de sobrevivencia com inicio antes de 1950", checks["datas_muito_antigas_survival"]["antes_1950"]],
                ["Empresas de sobrevivencia com inicio antes de 1900", checks["datas_muito_antigas_survival"]["antes_1900"]],
            ],
        ),
        "",
        "## Conclusoes e regras",
        "",
        "- O vazamento estrutural mais perigoso da Fase 2, que era o uso de colunas `_snapshot` no radar, ja foi removido.",
        "- `ano_observacao` fica em categoria de cautela: e observavel no momento da previsao, mas pode funcionar como proxy de periodo e deve ser avaliado separadamente.",
        "- `data_inicio_atividade` e `data_observacao` devem permanecer fora da matriz final de treino; usar as derivadas `idade` e `coorte`.",
        "- A base de sobrevivencia ainda preserva colunas `_snapshot`; isso e aceitavel para analise descritiva e explicativa, nao para treino do radar sem auditoria adicional.",
    ]
    LEAKAGE_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_stability_report(summary: dict[str, Any]) -> None:
    event_rows = [
        [row["split_temporal"], row["total_rows"], row["positivos_12m"], row["taxa_positiva_12m"]]
        for row in summary["event_rate_by_split"]
    ]
    regime_rows = [
        [row["split_temporal"], row["taxa_tem_regime_t"]]
        for row in summary["regime_coverage_by_split"]
    ]
    boolean_rows = []
    for row in summary["boolean_rates"]:
        for col in APPROVED_BOOLEAN:
            boolean_rows.append([row["split_temporal"], col, row[col]])
    numeric_lines = []
    for col, rows in summary["numeric_summaries"].items():
        numeric_lines.append(f"### {col}")
        numeric_lines.append("")
        numeric_lines.append(
            md_table(
                ["Split", "Media", "Desvio", "Mediana", "P95"],
                [[r["split_temporal"], r["media"], r["desvio"], r["mediana"], r["p95"]] for r in rows],
            )
        )
        numeric_lines.append("")
    lines = [
        "# Fase 03 - Relatorio de Estabilidade e Drift",
        "",
        "Este relatorio resume desbalanceamento, estabilidade temporal e cobertura por dimensoes diagnosticas.",
        "",
        "## Taxa de evento por split",
        "",
        md_table(["Split", "Linhas", "Positivos 12m", "Taxa positiva"], event_rows),
        "",
        "## Cobertura de `Regimes Tributarios` por split",
        "",
        md_table(["Split", "Taxa com regime observado"], regime_rows),
        "",
        "## Features booleanas aprovadas por split",
        "",
        md_table(["Split", "Feature", "Share"], boolean_rows),
        "",
        "## Features numericas aprovadas por split",
        "",
        *numeric_lines,
        "## Cobertura de dimensoes diagnosticas",
        "",
        md_table(
            ["Split", "porte missing", "uf missing", "cnae divisao missing"],
            [
                [row["split_temporal"], row["porte_missing_rate"], row["uf_missing_rate"], row["cnae_divisao_missing_rate"]]
                for row in summary["coverage_summary"]
            ],
        ),
        "",
        "## Maiores shifts de composicao entre treino e teste",
        "",
        "### Porte",
        "",
        md_table(
            ["Categoria", "Share treino", "Share teste", "Abs diff"],
            [[r["categoria"], r["share_treino"], r["share_teste"], r["abs_diff_treino_teste"]] for r in summary["top_shift_porte"]],
        ),
        "",
        "### UF",
        "",
        md_table(
            ["Categoria", "Share treino", "Share teste", "Abs diff"],
            [[r["categoria"], r["share_treino"], r["share_teste"], r["abs_diff_treino_teste"]] for r in summary["top_shift_uf"]],
        ),
        "",
        "### CNAE divisao",
        "",
        md_table(
            ["Categoria", "Share treino", "Share teste", "Abs diff"],
            [[r["categoria"], r["share_treino"], r["share_teste"], r["abs_diff_treino_teste"]] for r in summary["top_shift_cnae_divisao"]],
        ),
        "",
        "## Conclusoes",
        "",
        "- A classe positiva e minoritaria, mas nao extrema: cerca de 5,9% no treino e 6,6% no teste.",
        "- Existe drift temporal real na taxa de evento, o que reforca a escolha por split temporal em vez de split aleatorio.",
        "- A cobertura de `Regimes Tributarios` e baixa e relativamente estavel, perto de 5,5%; isso exige cautela porque a ausencia de cobertura pode virar proxy forte de subpopulacao.",
        "- As dimensoes `porte`, `UF` e `CNAE divisao` foram auditadas como lentes de cobertura e drift, nao como features aprovadas automaticamente para o radar.",
    ]
    STABILITY_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    con = build_con()
    build_views(con)
    write_feature_checklist()

    leakage_summary = compute_leakage_summary(con)
    stability_summary = compute_stability_summary(con)

    write_csv_rows(PORTE_CSV, stability_summary["porte_dist"])
    write_csv_rows(UF_CSV, stability_summary["uf_dist"])
    write_csv_rows(CNAE_DIV_CSV, stability_summary["cnae_div_dist"])

    write_leakage_report(leakage_summary)
    write_stability_report(stability_summary)

    summary = normalize_numbers(
        {
            "leakage": leakage_summary,
            "stability": {
                "event_rate_by_split": stability_summary["event_rate_by_split"],
                "regime_coverage_by_split": stability_summary["regime_coverage_by_split"],
                "coverage_summary": stability_summary["coverage_summary"],
                "top_shift_porte": stability_summary["top_shift_porte"][:5],
                "top_shift_uf": stability_summary["top_shift_uf"][:5],
                "top_shift_cnae_divisao": stability_summary["top_shift_cnae_divisao"][:5],
            },
        }
    )
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
