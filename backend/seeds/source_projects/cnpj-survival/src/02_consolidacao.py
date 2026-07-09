from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]
RAW_CNPJ_DIR = ROOT / "data" / "raw" / "cnpj"
RAW_REGIMES_DIR = ROOT / "data" / "raw" / "regimes_tributarios"
OUT_DIR = ROOT / "data" / "processed"
TMP_DIR = Path.home() / "AppData" / "Local" / "Temp" / "duckdb_cnpj_02"
SUMMARY_PATH = ROOT / "tables" / "resumo_consolidacao.json"
PROBLEM_EST_DIRS = {"Estabelecimentos0", "Estabelecimentos2", "Estabelecimentos5", "Estabelecimentos9"}


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
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def q_no_header(path_pattern: str, columns: dict[str, str], encoding: str = "latin-1", delim: str = ";") -> str:
    cols = ",".join(f"'{k}':'{v}'" for k, v in columns.items())
    return (
        f"read_csv('{path_pattern}', delim='{delim}', quote='\"', escape='\"', encoding='{encoding}', "
        f"header=false, columns={{{cols}}})"
    )


def q_paths(
    paths: list[str],
    columns: dict[str, str],
    encoding: str = "latin-1",
    delim: str = ";",
    header: bool = False,
    filename: bool = False,
) -> str:
    cols = ",".join(f"'{k}':'{v}'" for k, v in columns.items())
    path_sql = "[" + ", ".join(f"'{p}'" for p in paths) + "]"
    return (
        f"read_csv({path_sql}, delim='{delim}', quote='\"', escape='\"', encoding='{encoding}', "
        f"header={'true' if header else 'false'}, filename={'true' if filename else 'false'}, columns={{{cols}}})"
    )


def ensure_utf8_copy(src: Path) -> Path:
    dst = TMP_DIR / "normalized_utf8" / src.parent.name / (src.name + ".utf8.csv")
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("r", encoding="latin-1", errors="replace", newline="") as fsrc, dst.open(
        "w", encoding="utf-8", newline=""
    ) as fdst:
        for line in fsrc:
            fdst.write(line)
    return dst


def build_con() -> duckdb.DuckDBPyConnection:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"PRAGMA temp_directory='{TMP_DIR.as_posix()}'")
    con.execute("PRAGMA threads=8")
    con.execute("SET preserve_insertion_order=false")
    return con


def sql_date_yyyymmdd(col: str) -> str:
    return (
        f"CASE "
        f"WHEN TRIM(COALESCE({col}, '')) IN ('', '0', '00000000') THEN NULL "
        f"WHEN regexp_full_match(TRIM({col}), '^[0-9]{{8}}$') THEN strptime(TRIM({col}), '%Y%m%d')::DATE "
        f"ELSE NULL END"
    )


def sql_clean_text(col: str) -> str:
    return f"NULLIF(TRIM({col}), '')"


def sql_clean_code(col: str, width: int) -> str:
    return (
        f"CASE WHEN TRIM(COALESCE({col}, '')) = '' THEN NULL "
        f"ELSE lpad(TRIM({col}), {width}, '0') END"
    )


def sql_clean_cnpj(col: str) -> str:
    return f"NULLIF(regexp_replace(COALESCE({col}, ''), '[^0-9]', '', 'g'), '')"


def sql_unknown_desc(code_expr: str, desc_expr: str) -> str:
    return (
        f"CASE "
        f"WHEN {code_expr} IS NULL THEN NULL "
        f"WHEN {desc_expr} IS NOT NULL THEN {desc_expr} "
        f"ELSE 'CODIGO_NAO_MAPEADO_' || {code_expr} END"
    )


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def build_views(con: duckdb.DuckDBPyConnection) -> None:
    empresas_cols = {
        "cnpj_basico": "VARCHAR",
        "razao_social": "VARCHAR",
        "natureza_juridica": "VARCHAR",
        "qualificacao_responsavel": "VARCHAR",
        "capital_social": "VARCHAR",
        "porte": "VARCHAR",
        "ente_federativo_responsavel": "VARCHAR",
    }
    estabelecimentos_cols = {
        "cnpj_basico": "VARCHAR",
        "cnpj_ordem": "VARCHAR",
        "cnpj_dv": "VARCHAR",
        "identificador_matriz_filial": "VARCHAR",
        "nome_fantasia": "VARCHAR",
        "situacao_cadastral": "VARCHAR",
        "data_situacao_cadastral": "VARCHAR",
        "motivo_situacao_cadastral": "VARCHAR",
        "nome_cidade_exterior": "VARCHAR",
        "pais": "VARCHAR",
        "data_inicio_atividade": "VARCHAR",
        "cnae_fiscal_principal": "VARCHAR",
        "cnae_fiscal_secundaria": "VARCHAR",
        "tipo_logradouro": "VARCHAR",
        "logradouro": "VARCHAR",
        "numero": "VARCHAR",
        "complemento": "VARCHAR",
        "bairro": "VARCHAR",
        "cep": "VARCHAR",
        "uf": "VARCHAR",
        "municipio": "VARCHAR",
        "ddd_1": "VARCHAR",
        "telefone_1": "VARCHAR",
        "ddd_2": "VARCHAR",
        "telefone_2": "VARCHAR",
        "ddd_fax": "VARCHAR",
        "fax": "VARCHAR",
        "correio_eletronico": "VARCHAR",
        "situacao_especial": "VARCHAR",
        "data_situacao_especial": "VARCHAR",
    }
    socios_cols = {
        "cnpj_basico": "VARCHAR",
        "identificador_socio": "VARCHAR",
        "nome_socio": "VARCHAR",
        "cpf_cnpj_socio": "VARCHAR",
        "qualificacao_socio": "VARCHAR",
        "data_entrada_sociedade": "VARCHAR",
        "pais": "VARCHAR",
        "representante_legal": "VARCHAR",
        "nome_representante": "VARCHAR",
        "qualificacao_representante_legal": "VARCHAR",
        "faixa_etaria": "VARCHAR",
    }
    simples_cols = {
        "cnpj_basico": "VARCHAR",
        "opcao_simples": "VARCHAR",
        "data_opcao_simples": "VARCHAR",
        "data_exclusao_simples": "VARCHAR",
        "opcao_mei": "VARCHAR",
        "data_opcao_mei": "VARCHAR",
        "data_exclusao_mei": "VARCHAR",
    }
    dominio_cols = {"codigo": "VARCHAR", "descricao": "VARCHAR"}
    regimes_cols = {
        "ano": "VARCHAR",
        "cnpj": "VARCHAR",
        "cnpj_da_scp": "VARCHAR",
        "forma_de_tributacao": "VARCHAR",
        "quantidade_de_escrituracoes": "VARCHAR",
    }

    base = RAW_CNPJ_DIR.resolve().as_posix()
    con.execute(
        f"""
        CREATE OR REPLACE VIEW empresas_src AS
        SELECT * FROM {q_no_header(base + "/Empresas*/K3241*.EMPRECSV", empresas_cols)}
        """
    )

    est_root = RAW_CNPJ_DIR
    good_est_paths: list[str] = []
    normalized_est_paths: list[str] = []
    for path in sorted(est_root.glob("Estabelecimentos*/K3241*.ESTABELE")):
        if path.parent.name in PROBLEM_EST_DIRS:
            normalized_est_paths.append(ensure_utf8_copy(path).resolve().as_posix())
        else:
            good_est_paths.append(path.resolve().as_posix())
    est_sources = []
    if good_est_paths:
        est_sources.append(f"SELECT * FROM {q_paths(good_est_paths, estabelecimentos_cols, encoding='latin-1')}")
    if normalized_est_paths:
        est_sources.append(f"SELECT * FROM {q_paths(normalized_est_paths, estabelecimentos_cols, encoding='utf-8')}")
    con.execute(
        f"""
        CREATE OR REPLACE VIEW estabelecimentos_src AS
        {" UNION ALL ".join(est_sources)}
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE VIEW socios_src AS
        SELECT * FROM {q_no_header(base + "/Socios*/K3241*.SOCIOCSV", socios_cols)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW simples_src AS
        SELECT * FROM {q_no_header(base + "/Simples/F.K03200$W.SIMPLES.CSV.D60314", simples_cols)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW cnaes_dom AS
        SELECT {sql_clean_code('codigo', 7)} AS codigo, {sql_clean_text('descricao')} AS descricao
        FROM {q_no_header(base + "/Cnaes/F.K03200$Z.D60314.CNAECSV", dominio_cols)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW municipios_dom AS
        SELECT {sql_clean_code('codigo', 4)} AS codigo, {sql_clean_text('descricao')} AS descricao
        FROM {q_no_header(base + "/Municipios/F.K03200$Z.D60314.MUNICCSV", dominio_cols)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW naturezas_dom AS
        SELECT {sql_clean_code('codigo', 4)} AS codigo, {sql_clean_text('descricao')} AS descricao
        FROM {q_no_header(base + "/Naturezas/F.K03200$Z.D60314.NATJUCSV", dominio_cols)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW motivos_dom AS
        SELECT {sql_clean_code('codigo', 2)} AS codigo, {sql_clean_text('descricao')} AS descricao
        FROM {q_no_header(base + "/Motivos/F.K03200$Z.D60314.MOTICSV", dominio_cols)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW paises_dom AS
        SELECT {sql_clean_code('codigo', 3)} AS codigo, {sql_clean_text('descricao')} AS descricao
        FROM {q_no_header(base + "/Paises/F.K03200$Z.D60314.PAISCSV", dominio_cols)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW qualificacoes_dom AS
        SELECT {sql_clean_code('codigo', 2)} AS codigo, {sql_clean_text('descricao')} AS descricao
        FROM {q_no_header(base + "/Qualificacoes/F.K03200$Z.D60314.QUALSCSV", dominio_cols)}
        """
    )

    regime_paths: list[str] = []
    regime_paths.extend(sorted(path.resolve().as_posix() for path in RAW_REGIMES_DIR.glob("Lucro Presumido *.csv")))
    regime_paths.extend(
        sorted(
            path.resolve().as_posix()
            for path in [
                RAW_REGIMES_DIR / "Lucro Real.csv",
                RAW_REGIMES_DIR / "Lucro Arbitrado.csv",
                RAW_REGIMES_DIR / "Imunes e Isentas.csv",
            ]
            if path.exists()
        )
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW regimes_anuais_src AS
        SELECT * FROM {q_paths(regime_paths, regimes_cols, encoding='utf-8', delim=',', header=True, filename=True)}
        """
    )


def copy_parquet(con: duckdb.DuckDBPyConnection, sql: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    con.execute(
        f"""
        COPY (
            {sql}
        ) TO '{output_path.resolve().as_posix()}'
        (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 500000)
        """
    )


def write_outputs(con: duckdb.DuckDBPyConnection) -> None:
    empresa_sql = f"""
    SELECT
        {sql_clean_code('e.cnpj_basico', 8)} AS cnpj_basico,
        {sql_clean_text('e.razao_social')} AS razao_social,
        {sql_clean_code('e.natureza_juridica', 4)} AS natureza_juridica,
        {sql_unknown_desc(sql_clean_code('e.natureza_juridica', 4), 'n.descricao')} AS natureza_juridica_desc,
        {sql_clean_code('e.qualificacao_responsavel', 2)} AS qualificacao_responsavel,
        {sql_unknown_desc(sql_clean_code('e.qualificacao_responsavel', 2), 'q.descricao')} AS qualificacao_responsavel_desc,
        TRY_CAST(REPLACE(NULLIF(TRIM(e.capital_social), ''), ',', '.') AS DOUBLE) AS capital_social,
        {sql_clean_code('e.porte', 2)} AS porte,
        CASE
            WHEN {sql_clean_code('e.porte', 2)} = '00' THEN 'NAO INFORMADO'
            WHEN {sql_clean_code('e.porte', 2)} = '01' THEN 'MICRO EMPRESA'
            WHEN {sql_clean_code('e.porte', 2)} = '03' THEN 'EMPRESA DE PEQUENO PORTE'
            WHEN {sql_clean_code('e.porte', 2)} = '05' THEN 'DEMAIS'
            ELSE 'PORTE_NAO_MAPEADO'
        END AS porte_desc,
        {sql_clean_text('e.ente_federativo_responsavel')} AS ente_federativo_responsavel
    FROM empresas_src e
    LEFT JOIN naturezas_dom n ON {sql_clean_code('e.natureza_juridica', 4)} = n.codigo
    LEFT JOIN qualificacoes_dom q ON {sql_clean_code('e.qualificacao_responsavel', 2)} = q.codigo
    """

    estabelecimento_sql = f"""
    SELECT
        {sql_clean_code('e.cnpj_basico', 8)} AS cnpj_basico,
        {sql_clean_code('e.cnpj_ordem', 4)} AS cnpj_ordem,
        {sql_clean_code('e.cnpj_dv', 2)} AS cnpj_dv,
        {sql_clean_code('e.cnpj_basico', 8)} || {sql_clean_code('e.cnpj_ordem', 4)} || {sql_clean_code('e.cnpj_dv', 2)} AS cnpj_14,
        {sql_clean_code('e.identificador_matriz_filial', 1)} AS identificador_matriz_filial,
        CASE
            WHEN {sql_clean_code('e.identificador_matriz_filial', 1)} = '1' THEN 'MATRIZ'
            WHEN {sql_clean_code('e.identificador_matriz_filial', 1)} = '2' THEN 'FILIAL'
            ELSE 'NAO_MAPEADO'
        END AS identificador_matriz_filial_desc,
        {sql_clean_text('e.nome_fantasia')} AS nome_fantasia,
        {sql_clean_code('e.situacao_cadastral', 2)} AS situacao_cadastral,
        CASE
            WHEN {sql_clean_code('e.situacao_cadastral', 2)} = '01' THEN 'NULA'
            WHEN {sql_clean_code('e.situacao_cadastral', 2)} = '02' THEN 'ATIVA'
            WHEN {sql_clean_code('e.situacao_cadastral', 2)} = '03' THEN 'SUSPENSA'
            WHEN {sql_clean_code('e.situacao_cadastral', 2)} = '04' THEN 'INAPTA'
            WHEN {sql_clean_code('e.situacao_cadastral', 2)} = '08' THEN 'BAIXADA'
            ELSE 'NAO_MAPEADA'
        END AS situacao_cadastral_desc,
        {sql_date_yyyymmdd('e.data_situacao_cadastral')} AS data_situacao_cadastral,
        CASE WHEN TRIM(COALESCE(e.data_situacao_cadastral, '')) IN ('0', '00000000') THEN TRUE ELSE FALSE END AS flag_data_situacao_sentinela_zero,
        {sql_clean_code('e.motivo_situacao_cadastral', 2)} AS motivo_situacao_cadastral,
        {sql_unknown_desc(sql_clean_code('e.motivo_situacao_cadastral', 2), 'm.descricao')} AS motivo_situacao_cadastral_desc,
        {sql_clean_text('e.nome_cidade_exterior')} AS nome_cidade_exterior,
        {sql_clean_code('e.pais', 3)} AS pais,
        {sql_unknown_desc(sql_clean_code('e.pais', 3), 'p.descricao')} AS pais_desc,
        {sql_date_yyyymmdd('e.data_inicio_atividade')} AS data_inicio_atividade,
        {sql_clean_code('e.cnae_fiscal_principal', 7)} AS cnae_fiscal_principal,
        {sql_unknown_desc(sql_clean_code('e.cnae_fiscal_principal', 7), 'c.descricao')} AS cnae_fiscal_principal_desc,
        {sql_clean_text('e.cnae_fiscal_secundaria')} AS cnae_fiscal_secundaria,
        CASE
            WHEN TRIM(COALESCE(e.cnae_fiscal_secundaria, '')) = '' THEN 0
            ELSE LENGTH(TRIM(e.cnae_fiscal_secundaria)) - LENGTH(REPLACE(TRIM(e.cnae_fiscal_secundaria), ',', '')) + 1
        END AS qtd_cnaes_secundarios,
        {sql_clean_text('e.tipo_logradouro')} AS tipo_logradouro,
        {sql_clean_text('e.logradouro')} AS logradouro,
        {sql_clean_text('e.numero')} AS numero,
        {sql_clean_text('e.complemento')} AS complemento,
        {sql_clean_text('e.bairro')} AS bairro,
        {sql_clean_text('e.cep')} AS cep,
        {sql_clean_text('e.uf')} AS uf,
        CASE
            WHEN TRIM(COALESCE(e.uf, '')) IN ('AC','AP','AM','PA','RO','RR','TO') THEN 'NORTE'
            WHEN TRIM(COALESCE(e.uf, '')) IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE') THEN 'NORDESTE'
            WHEN TRIM(COALESCE(e.uf, '')) IN ('DF','GO','MT','MS') THEN 'CENTRO-OESTE'
            WHEN TRIM(COALESCE(e.uf, '')) IN ('ES','MG','RJ','SP') THEN 'SUDESTE'
            WHEN TRIM(COALESCE(e.uf, '')) IN ('PR','RS','SC') THEN 'SUL'
            ELSE NULL
        END AS regiao,
        {sql_clean_code('e.municipio', 4)} AS municipio,
        {sql_unknown_desc(sql_clean_code('e.municipio', 4), 'mun.descricao')} AS municipio_desc,
        {sql_clean_text('e.ddd_1')} AS ddd_1,
        {sql_clean_text('e.telefone_1')} AS telefone_1,
        {sql_clean_text('e.ddd_2')} AS ddd_2,
        {sql_clean_text('e.telefone_2')} AS telefone_2,
        {sql_clean_text('e.ddd_fax')} AS ddd_fax,
        {sql_clean_text('e.fax')} AS fax,
        {sql_clean_text('e.correio_eletronico')} AS correio_eletronico,
        {sql_clean_text('e.situacao_especial')} AS situacao_especial,
        {sql_date_yyyymmdd('e.data_situacao_especial')} AS data_situacao_especial,
        CASE
            WHEN {sql_date_yyyymmdd('e.data_inicio_atividade')} IS NOT NULL
             AND {sql_date_yyyymmdd('e.data_situacao_cadastral')} IS NOT NULL
             AND {sql_date_yyyymmdd('e.data_situacao_cadastral')} < {sql_date_yyyymmdd('e.data_inicio_atividade')}
            THEN TRUE ELSE FALSE
        END AS flag_cronologia_invalida
    FROM estabelecimentos_src e
    LEFT JOIN motivos_dom m ON {sql_clean_code('e.motivo_situacao_cadastral', 2)} = m.codigo
    LEFT JOIN paises_dom p ON {sql_clean_code('e.pais', 3)} = p.codigo
    LEFT JOIN cnaes_dom c ON {sql_clean_code('e.cnae_fiscal_principal', 7)} = c.codigo
    LEFT JOIN municipios_dom mun ON {sql_clean_code('e.municipio', 4)} = mun.codigo
    """

    socio_sql = f"""
    SELECT
        {sql_clean_code('s.cnpj_basico', 8)} AS cnpj_basico,
        {sql_clean_code('s.identificador_socio', 1)} AS identificador_socio,
        CASE
            WHEN {sql_clean_code('s.identificador_socio', 1)} = '1' THEN 'PESSOA JURIDICA'
            WHEN {sql_clean_code('s.identificador_socio', 1)} = '2' THEN 'PESSOA FISICA'
            WHEN {sql_clean_code('s.identificador_socio', 1)} = '3' THEN 'ESTRANGEIRO'
            ELSE 'NAO_MAPEADO'
        END AS identificador_socio_desc,
        {sql_clean_text('s.nome_socio')} AS nome_socio,
        {sql_clean_text('s.cpf_cnpj_socio')} AS cpf_cnpj_socio,
        {sql_clean_code('s.qualificacao_socio', 2)} AS qualificacao_socio,
        {sql_unknown_desc(sql_clean_code('s.qualificacao_socio', 2), 'q1.descricao')} AS qualificacao_socio_desc,
        {sql_date_yyyymmdd('s.data_entrada_sociedade')} AS data_entrada_sociedade,
        {sql_clean_code('s.pais', 3)} AS pais,
        {sql_unknown_desc(sql_clean_code('s.pais', 3), 'p.descricao')} AS pais_desc,
        {sql_clean_text('s.representante_legal')} AS representante_legal,
        {sql_clean_text('s.nome_representante')} AS nome_representante,
        {sql_clean_code('s.qualificacao_representante_legal', 2)} AS qualificacao_representante_legal,
        {sql_unknown_desc(sql_clean_code('s.qualificacao_representante_legal', 2), 'q2.descricao')} AS qualificacao_representante_legal_desc,
        {sql_clean_code('s.faixa_etaria', 1)} AS faixa_etaria,
        CASE
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '0' THEN 'NAO SE APLICA'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '1' THEN '0 A 12'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '2' THEN '13 A 20'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '3' THEN '21 A 30'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '4' THEN '31 A 40'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '5' THEN '41 A 50'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '6' THEN '51 A 60'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '7' THEN '61 A 70'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '8' THEN '71 A 80'
            WHEN {sql_clean_code('s.faixa_etaria', 1)} = '9' THEN 'MAIOR DE 80'
            ELSE 'NAO_MAPEADA'
        END AS faixa_etaria_desc
    FROM socios_src s
    LEFT JOIN qualificacoes_dom q1 ON {sql_clean_code('s.qualificacao_socio', 2)} = q1.codigo
    LEFT JOIN qualificacoes_dom q2 ON {sql_clean_code('s.qualificacao_representante_legal', 2)} = q2.codigo
    LEFT JOIN paises_dom p ON {sql_clean_code('s.pais', 3)} = p.codigo
    """

    simples_sql = f"""
    SELECT
        {sql_clean_code('s.cnpj_basico', 8)} AS cnpj_basico,
        {sql_clean_text('s.opcao_simples')} AS opcao_simples,
        CASE WHEN TRIM(COALESCE(s.opcao_simples, '')) = 'S' THEN TRUE ELSE FALSE END AS flag_optante_simples,
        {sql_date_yyyymmdd('s.data_opcao_simples')} AS data_opcao_simples,
        {sql_date_yyyymmdd('s.data_exclusao_simples')} AS data_exclusao_simples,
        {sql_clean_text('s.opcao_mei')} AS opcao_mei,
        CASE WHEN TRIM(COALESCE(s.opcao_mei, '')) = 'S' THEN TRUE ELSE FALSE END AS flag_optante_mei,
        {sql_date_yyyymmdd('s.data_opcao_mei')} AS data_opcao_mei,
        {sql_date_yyyymmdd('s.data_exclusao_mei')} AS data_exclusao_mei,
        CASE WHEN {sql_date_yyyymmdd('s.data_exclusao_simples')} IS NOT NULL THEN TRUE ELSE FALSE END AS flag_ja_excluido_simples,
        CASE WHEN {sql_date_yyyymmdd('s.data_exclusao_mei')} IS NOT NULL THEN TRUE ELSE FALSE END AS flag_ja_excluido_mei
    FROM simples_src s
    """

    regimes_sql = f"""
    SELECT DISTINCT
        TRY_CAST(NULLIF(TRIM(r.ano), '') AS INTEGER) AS ano,
        {sql_clean_cnpj('r.cnpj')} AS cnpj_14,
        SUBSTR({sql_clean_cnpj('r.cnpj')}, 1, 8) AS cnpj_basico,
        CASE
            WHEN {sql_clean_cnpj('r.cnpj_da_scp')} IN ('0', '00000000000000') THEN NULL
            ELSE {sql_clean_cnpj('r.cnpj_da_scp')}
        END AS cnpj_da_scp_14,
        {sql_clean_text('r.forma_de_tributacao')} AS forma_de_tributacao,
        TRY_CAST(NULLIF(TRIM(r.quantidade_de_escrituracoes), '') AS INTEGER) AS quantidade_de_escrituracoes,
        regexp_extract(r.filename, '[^/\\\\]+$') AS arquivo_origem
    FROM regimes_anuais_src r
    WHERE {sql_clean_cnpj('r.cnpj')} IS NOT NULL
    """

    copy_parquet(con, empresa_sql, OUT_DIR / "empresa_base.parquet")
    copy_parquet(con, estabelecimento_sql, OUT_DIR / "estabelecimento_base.parquet")
    copy_parquet(con, socio_sql, OUT_DIR / "socio_base.parquet")
    copy_parquet(con, simples_sql, OUT_DIR / "simples_base.parquet")
    copy_parquet(con, regimes_sql, OUT_DIR / "regimes_anuais_base.parquet")


def fetch_record(con: duckdb.DuckDBPyConnection, sql: str) -> dict[str, Any]:
    return con.execute(sql).fetchdf().to_dict(orient="records")[0]


def build_summary(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    outputs = {
        "empresa_base": OUT_DIR / "empresa_base.parquet",
        "estabelecimento_base": OUT_DIR / "estabelecimento_base.parquet",
        "socio_base": OUT_DIR / "socio_base.parquet",
        "simples_base": OUT_DIR / "simples_base.parquet",
        "regimes_anuais_base": OUT_DIR / "regimes_anuais_base.parquet",
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
        "empresa_base": fetch_record(
            con,
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT cnpj_basico) AS distinct_cnpj_basico,
                SUM(CASE WHEN natureza_juridica_desc LIKE 'CODIGO_NAO_MAPEADO_%' THEN 1 ELSE 0 END) AS natureza_nao_mapeada,
                SUM(CASE WHEN qualificacao_responsavel_desc LIKE 'CODIGO_NAO_MAPEADO_%' THEN 1 ELSE 0 END) AS qualificacao_responsavel_nao_mapeada
            FROM parquet_scan('{(OUT_DIR / "empresa_base.parquet").resolve().as_posix()}')
            """,
        ),
        "estabelecimento_base": fetch_record(
            con,
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT cnpj_14) AS distinct_cnpj_14,
                SUM(CASE WHEN flag_data_situacao_sentinela_zero THEN 1 ELSE 0 END) AS data_situacao_sentinela_zero,
                SUM(CASE WHEN flag_cronologia_invalida THEN 1 ELSE 0 END) AS cronologia_invalida,
                SUM(CASE WHEN motivo_situacao_cadastral_desc LIKE 'CODIGO_NAO_MAPEADO_%' THEN 1 ELSE 0 END) AS motivo_nao_mapeado,
                SUM(CASE WHEN pais_desc LIKE 'CODIGO_NAO_MAPEADO_%' THEN 1 ELSE 0 END) AS pais_nao_mapeado
            FROM parquet_scan('{(OUT_DIR / "estabelecimento_base.parquet").resolve().as_posix()}')
            """,
        ),
        "socio_base": fetch_record(
            con,
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT cnpj_basico) AS distinct_cnpj_basico,
                SUM(CASE WHEN pais_desc LIKE 'CODIGO_NAO_MAPEADO_%' THEN 1 ELSE 0 END) AS pais_nao_mapeado
            FROM parquet_scan('{(OUT_DIR / "socio_base.parquet").resolve().as_posix()}')
            """,
        ),
        "simples_base": fetch_record(
            con,
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT cnpj_basico) AS distinct_cnpj_basico,
                SUM(CASE WHEN flag_optante_simples THEN 1 ELSE 0 END) AS optantes_simples,
                SUM(CASE WHEN flag_optante_mei THEN 1 ELSE 0 END) AS optantes_mei
            FROM parquet_scan('{(OUT_DIR / "simples_base.parquet").resolve().as_posix()}')
            """,
        ),
        "regimes_anuais_base": fetch_record(
            con,
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT cnpj_14 || '-' || CAST(ano AS VARCHAR) || '-' || forma_de_tributacao) AS distinct_chave_regime,
                MIN(ano) AS ano_min,
                MAX(ano) AS ano_max
            FROM parquet_scan('{(OUT_DIR / "regimes_anuais_base.parquet").resolve().as_posix()}')
            """,
        ),
    }
    return normalize_numbers({"datasets": dataset_summary, "checks": checks})


def write_report(summary: dict[str, Any]) -> None:
    rows = [
        [name, info["rows"], info["size_human"], info["path"]]
        for name, info in summary["datasets"].items()
    ]
    checks = summary["checks"]
    lines = [
        "# Fase 02 - Consolidacao e Padronizacao",
        "",
        "Este documento registra a execucao da Aula 01 da Fase 2: leitura, padronizacao tipada e exportacao das bases consolidadas em parquet.",
        "",
        "## Saidas geradas",
        "",
        md_table(["Dataset", "Linhas", "Tamanho", "Arquivo"], rows),
        "",
        "## Regras aplicadas na consolidacao",
        "",
        "- As pastas extraidas do snapshot `2026-03` foram tratadas como fonte canonica.",
        "- As quatro particoes problematicas de `Estabelecimentos` continuaram com normalizacao transitoria de encoding para leitura reproduzivel.",
        "- Datas `yyyymmdd` foram convertidas para `DATE`, tratando `0` e `00000000` como ausentes.",
        "- Codigos com zeros a esquerda relevantes foram preservados como texto.",
        "- Tabelas de dominio foram usadas para gerar descricoes e manter codigos nao mapeados como categorias residuais documentadas.",
        "",
        "## Cheques rapidos apos a consolidacao",
        "",
        md_table(
            ["Dataset", "Cheque", "Valor"],
            [
                ["empresa_base", "linhas", checks["empresa_base"]["total_rows"]],
                ["empresa_base", "cnpj_basico distinto", checks["empresa_base"]["distinct_cnpj_basico"]],
                ["empresa_base", "qualificacao_responsavel nao mapeada", checks["empresa_base"]["qualificacao_responsavel_nao_mapeada"]],
                ["estabelecimento_base", "linhas", checks["estabelecimento_base"]["total_rows"]],
                ["estabelecimento_base", "cnpj_14 distinto", checks["estabelecimento_base"]["distinct_cnpj_14"]],
                ["estabelecimento_base", "sentinela zero em data_situacao", checks["estabelecimento_base"]["data_situacao_sentinela_zero"]],
                ["estabelecimento_base", "cronologia invalida", checks["estabelecimento_base"]["cronologia_invalida"]],
                ["estabelecimento_base", "motivo nao mapeado", checks["estabelecimento_base"]["motivo_nao_mapeado"]],
                ["estabelecimento_base", "pais nao mapeado", checks["estabelecimento_base"]["pais_nao_mapeado"]],
                ["socio_base", "linhas", checks["socio_base"]["total_rows"]],
                ["socio_base", "pais nao mapeado", checks["socio_base"]["pais_nao_mapeado"]],
                ["simples_base", "linhas", checks["simples_base"]["total_rows"]],
                ["regimes_anuais_base", "linhas", checks["regimes_anuais_base"]["total_rows"]],
                ["regimes_anuais_base", "ano minimo", checks["regimes_anuais_base"]["ano_min"]],
                ["regimes_anuais_base", "ano maximo", checks["regimes_anuais_base"]["ano_max"]],
            ],
        ),
        "",
        "## Proximo passo recomendado",
        "",
        "A proxima etapa da Fase 2 deve construir a unidade analitica empresarial a partir da matriz, definir evento e censura e produzir `survival_empresa.parquet`.",
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
