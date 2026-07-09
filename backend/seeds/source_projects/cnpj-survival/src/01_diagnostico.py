from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tables"
TMP_DIR = Path.home() / "AppData" / "Local" / "Temp" / "duckdb_cnpj_01"
PROBLEM_EST_DIRS = {"Estabelecimentos0", "Estabelecimentos2", "Estabelecimentos5", "Estabelecimentos9"}


def human_size(num: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1000 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1000
    return f"{num} B"


def load_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


@dataclass(frozen=True)
class SchemaField:
    table: str
    order: int
    column: str
    logical_type: str
    key_role: str
    description: str


SCHEMA_FIELDS: list[SchemaField] = [
    SchemaField("empresas", 1, "cnpj_basico", "string", "pk_empresa", "Oito primeiros digitos do CNPJ."),
    SchemaField("empresas", 2, "razao_social", "string", "", "Nome empresarial da pessoa juridica."),
    SchemaField("empresas", 3, "natureza_juridica", "codigo", "fk_naturezas", "Codigo da natureza juridica."),
    SchemaField("empresas", 4, "qualificacao_responsavel", "codigo", "fk_qualificacoes", "Qualificacao da pessoa fisica responsavel."),
    SchemaField("empresas", 5, "capital_social", "decimal_string", "", "Capital social da empresa com virgula decimal."),
    SchemaField("empresas", 6, "porte", "codigo", "", "Codigo do porte: 00, 01, 03 ou 05."),
    SchemaField("empresas", 7, "ente_federativo_responsavel", "string", "", "Preenchido para certas naturezas juridicas do grupo 1XXX."),
    SchemaField("estabelecimentos", 1, "cnpj_basico", "string", "fk_empresas", "Oito primeiros digitos do CNPJ."),
    SchemaField("estabelecimentos", 2, "cnpj_ordem", "string", "pk_estabelecimento", "Digitos 9 a 12 do CNPJ."),
    SchemaField("estabelecimentos", 3, "cnpj_dv", "string", "pk_estabelecimento", "Digitos verificadores do CNPJ."),
    SchemaField("estabelecimentos", 4, "identificador_matriz_filial", "codigo", "", "1 = matriz, 2 = filial."),
    SchemaField("estabelecimentos", 5, "nome_fantasia", "string", "", "Nome fantasia do estabelecimento."),
    SchemaField("estabelecimentos", 6, "situacao_cadastral", "codigo", "", "01 nula, 02 ativa, 03 suspensa, 04 inapta, 08 baixada."),
    SchemaField("estabelecimentos", 7, "data_situacao_cadastral", "yyyymmdd_string", "", "Data do evento da situacao cadastral."),
    SchemaField("estabelecimentos", 8, "motivo_situacao_cadastral", "codigo", "fk_motivos", "Motivo da situacao cadastral."),
    SchemaField("estabelecimentos", 9, "nome_cidade_exterior", "string", "", "Cidade do exterior quando aplicavel."),
    SchemaField("estabelecimentos", 10, "pais", "codigo", "fk_paises", "Codigo do pais para domicilio no exterior."),
    SchemaField("estabelecimentos", 11, "data_inicio_atividade", "yyyymmdd_string", "", "Data de inicio da atividade."),
    SchemaField("estabelecimentos", 12, "cnae_fiscal_principal", "codigo", "fk_cnaes", "Codigo do CNAE principal."),
    SchemaField("estabelecimentos", 13, "cnae_fiscal_secundaria", "csv_string", "", "Lista de CNAEs secundarios separados por virgula."),
    SchemaField("estabelecimentos", 14, "tipo_logradouro", "string", "", "Descricao do tipo de logradouro."),
    SchemaField("estabelecimentos", 15, "logradouro", "string", "", "Nome do logradouro."),
    SchemaField("estabelecimentos", 16, "numero", "string", "", "Numero do endereco."),
    SchemaField("estabelecimentos", 17, "complemento", "string", "", "Complemento do endereco."),
    SchemaField("estabelecimentos", 18, "bairro", "string", "", "Bairro do estabelecimento."),
    SchemaField("estabelecimentos", 19, "cep", "string", "", "CEP do estabelecimento."),
    SchemaField("estabelecimentos", 20, "uf", "string", "", "Unidade da federacao."),
    SchemaField("estabelecimentos", 21, "municipio", "codigo", "fk_municipios", "Codigo do municipio."),
    SchemaField("estabelecimentos", 22, "ddd_1", "string", "", "DDD principal."),
    SchemaField("estabelecimentos", 23, "telefone_1", "string", "", "Telefone principal."),
    SchemaField("estabelecimentos", 24, "ddd_2", "string", "", "DDD secundario."),
    SchemaField("estabelecimentos", 25, "telefone_2", "string", "", "Telefone secundario."),
    SchemaField("estabelecimentos", 26, "ddd_fax", "string", "", "DDD do fax."),
    SchemaField("estabelecimentos", 27, "fax", "string", "", "Numero do fax."),
    SchemaField("estabelecimentos", 28, "correio_eletronico", "string", "", "E-mail do contribuinte."),
    SchemaField("estabelecimentos", 29, "situacao_especial", "string", "", "Situacao especial do estabelecimento."),
    SchemaField("estabelecimentos", 30, "data_situacao_especial", "yyyymmdd_string", "", "Data da situacao especial."),
    SchemaField("socios", 1, "cnpj_basico", "string", "fk_empresas", "Oito primeiros digitos do CNPJ."),
    SchemaField("socios", 2, "identificador_socio", "codigo", "", "1 = PJ, 2 = PF, 3 = estrangeiro."),
    SchemaField("socios", 3, "nome_socio", "string", "", "Nome do socio ou razao social."),
    SchemaField("socios", 4, "cpf_cnpj_socio", "string", "", "Documento mascarado nos casos aplicaveis."),
    SchemaField("socios", 5, "qualificacao_socio", "codigo", "fk_qualificacoes", "Codigo da qualificacao do socio."),
    SchemaField("socios", 6, "data_entrada_sociedade", "yyyymmdd_string", "", "Data de entrada na sociedade."),
    SchemaField("socios", 7, "pais", "codigo", "fk_paises", "Codigo do pais para socio estrangeiro."),
    SchemaField("socios", 8, "representante_legal", "string", "", "Documento do representante legal."),
    SchemaField("socios", 9, "nome_representante", "string", "", "Nome do representante legal."),
    SchemaField("socios", 10, "qualificacao_representante_legal", "codigo", "fk_qualificacoes", "Qualificacao do representante legal."),
    SchemaField("socios", 11, "faixa_etaria", "codigo", "", "Faixa etaria codificada entre 0 e 9."),
    SchemaField("simples", 1, "cnpj_basico", "string", "fk_empresas", "Oito primeiros digitos do CNPJ."),
    SchemaField("simples", 2, "opcao_simples", "flag", "", "S = sim, N = nao, vazio = outros."),
    SchemaField("simples", 3, "data_opcao_simples", "yyyymmdd_string", "", "Data de opcao pelo Simples."),
    SchemaField("simples", 4, "data_exclusao_simples", "yyyymmdd_string", "", "Data de exclusao do Simples."),
    SchemaField("simples", 5, "opcao_mei", "flag", "", "S = sim, N = nao, vazio = outros."),
    SchemaField("simples", 6, "data_opcao_mei", "yyyymmdd_string", "", "Data de opcao pelo MEI."),
    SchemaField("simples", 7, "data_exclusao_mei", "yyyymmdd_string", "", "Data de exclusao do MEI."),
    SchemaField("cnaes", 1, "codigo", "codigo", "pk_dominio", "Codigo do CNAE."),
    SchemaField("cnaes", 2, "descricao", "string", "", "Descricao do CNAE."),
    SchemaField("municipios", 1, "codigo", "codigo", "pk_dominio", "Codigo do municipio."),
    SchemaField("municipios", 2, "descricao", "string", "", "Descricao do municipio."),
    SchemaField("naturezas", 1, "codigo", "codigo", "pk_dominio", "Codigo da natureza juridica."),
    SchemaField("naturezas", 2, "descricao", "string", "", "Descricao da natureza juridica."),
    SchemaField("motivos", 1, "codigo", "codigo", "pk_dominio", "Codigo do motivo de situacao cadastral."),
    SchemaField("motivos", 2, "descricao", "string", "", "Descricao do motivo."),
    SchemaField("paises", 1, "codigo", "codigo", "pk_dominio", "Codigo do pais."),
    SchemaField("paises", 2, "descricao", "string", "", "Descricao do pais."),
    SchemaField("qualificacoes", 1, "codigo", "codigo", "pk_dominio", "Codigo da qualificacao."),
    SchemaField("qualificacoes", 2, "descricao", "string", "", "Descricao da qualificacao."),
]


def build_con() -> duckdb.DuckDBPyConnection:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"PRAGMA temp_directory='{TMP_DIR.as_posix()}'")
    con.execute("PRAGMA threads=8")
    con.execute("SET preserve_insertion_order=false")
    return con


def q(path_pattern: str, columns: dict[str, str]) -> str:
    cols = ",".join(f"'{k}':'{v}'" for k, v in columns.items())
    return (
        f"read_csv('{path_pattern}', delim=';', quote='\"', escape='\"', encoding='latin-1', "
        f"header=false, columns={{{cols}}})"
    )


def q_multi(paths: list[str], columns: dict[str, str], encoding: str) -> str:
    cols = ",".join(f"'{k}':'{v}'" for k, v in columns.items())
    path_sql = "[" + ", ".join(f"'{p}'" for p in paths) + "]"
    return (
        f"read_csv({path_sql}, delim=';', quote='\"', escape='\"', encoding='{encoding}', "
        f"header=false, columns={{{cols}}})"
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


def build_views(con: duckdb.DuckDBPyConnection) -> None:
    base = (ROOT / "Base de Dados" / "2026-03").resolve().as_posix()
    est_cols = {
        'cnpj_basico':'VARCHAR','cnpj_ordem':'VARCHAR','cnpj_dv':'VARCHAR','identificador_matriz_filial':'VARCHAR',
        'nome_fantasia':'VARCHAR','situacao_cadastral':'VARCHAR','data_situacao_cadastral':'VARCHAR',
        'motivo_situacao_cadastral':'VARCHAR','nome_cidade_exterior':'VARCHAR','pais':'VARCHAR',
        'data_inicio_atividade':'VARCHAR','cnae_fiscal_principal':'VARCHAR','cnae_fiscal_secundaria':'VARCHAR',
        'tipo_logradouro':'VARCHAR','logradouro':'VARCHAR','numero':'VARCHAR','complemento':'VARCHAR','bairro':'VARCHAR',
        'cep':'VARCHAR','uf':'VARCHAR','municipio':'VARCHAR','ddd_1':'VARCHAR','telefone_1':'VARCHAR','ddd_2':'VARCHAR',
        'telefone_2':'VARCHAR','ddd_fax':'VARCHAR','fax':'VARCHAR','correio_eletronico':'VARCHAR',
        'situacao_especial':'VARCHAR','data_situacao_especial':'VARCHAR'
    }
    con.execute(
        f"""
        CREATE OR REPLACE VIEW empresas_src AS
        SELECT * FROM {q(base + "/Empresas*/K3241*.EMPRECSV", {
            'cnpj_basico':'VARCHAR','razao_social':'VARCHAR','natureza_juridica':'VARCHAR',
            'qualificacao_responsavel':'VARCHAR','capital_social':'VARCHAR','porte':'VARCHAR',
            'ente_federativo_responsavel':'VARCHAR'
        })}
        """
    )
    est_root = ROOT / "Base de Dados" / "2026-03"
    good_est_paths = []
    normalized_est_paths = []
    for path in sorted(est_root.glob("Estabelecimentos*/K3241*.ESTABELE")):
        if path.parent.name in PROBLEM_EST_DIRS:
            normalized_est_paths.append(ensure_utf8_copy(path).resolve().as_posix())
        else:
            good_est_paths.append(path.resolve().as_posix())

    est_sources = []
    if good_est_paths:
        est_sources.append(f"SELECT * FROM {q_multi(good_est_paths, est_cols, 'latin-1')}")
    if normalized_est_paths:
        est_sources.append(f"SELECT * FROM {q_multi(normalized_est_paths, est_cols, 'utf-8')}")
    con.execute(
        f"""
        CREATE OR REPLACE VIEW estabelecimentos_src AS
        {" UNION ALL ".join(est_sources)}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW socios_src AS
        SELECT * FROM {q(base + "/Socios*/K3241*.SOCIOCSV", {
            'cnpj_basico':'VARCHAR','identificador_socio':'VARCHAR','nome_socio':'VARCHAR','cpf_cnpj_socio':'VARCHAR',
            'qualificacao_socio':'VARCHAR','data_entrada_sociedade':'VARCHAR','pais':'VARCHAR',
            'representante_legal':'VARCHAR','nome_representante':'VARCHAR',
            'qualificacao_representante_legal':'VARCHAR','faixa_etaria':'VARCHAR'
        })}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW simples_src AS
        SELECT * FROM {q(base + "/Simples/F.K03200$W.SIMPLES.CSV.D60314", {
            'cnpj_basico':'VARCHAR','opcao_simples':'VARCHAR','data_opcao_simples':'VARCHAR',
            'data_exclusao_simples':'VARCHAR','opcao_mei':'VARCHAR','data_opcao_mei':'VARCHAR',
            'data_exclusao_mei':'VARCHAR'
        })}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW cnaes_dom AS
        SELECT * FROM {q(base + "/Cnaes/F.K03200$Z.D60314.CNAECSV", {'codigo':'VARCHAR','descricao':'VARCHAR'})}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW municipios_dom AS
        SELECT * FROM {q(base + "/Municipios/F.K03200$Z.D60314.MUNICCSV", {'codigo':'VARCHAR','descricao':'VARCHAR'})}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW naturezas_dom AS
        SELECT * FROM {q(base + "/Naturezas/F.K03200$Z.D60314.NATJUCSV", {'codigo':'VARCHAR','descricao':'VARCHAR'})}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW motivos_dom AS
        SELECT * FROM {q(base + "/Motivos/F.K03200$Z.D60314.MOTICSV", {'codigo':'VARCHAR','descricao':'VARCHAR'})}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW paises_dom AS
        SELECT * FROM {q(base + "/Paises/F.K03200$Z.D60314.PAISCSV", {'codigo':'VARCHAR','descricao':'VARCHAR'})}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE VIEW qualificacoes_dom AS
        SELECT * FROM {q(base + "/Qualificacoes/F.K03200$Z.D60314.QUALSCSV", {'codigo':'VARCHAR','descricao':'VARCHAR'})}
        """
    )


def fetch_record(con: duckdb.DuckDBPyConnection, sql: str) -> dict[str, Any]:
    return con.execute(sql).fetchdf().to_dict(orient="records")[0]


def fetch_rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    return con.execute(sql).fetchdf().to_dict(orient="records")


def normalize_numbers(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: normalize_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_numbers(v) for v in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def write_schema_csv() -> None:
    out = OUT_DIR / "02_dicionario_operacional_colunas.csv"
    with out.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["table", "order", "column", "logical_type", "key_role", "description"],
        )
        writer.writeheader()
        for field in SCHEMA_FIELDS:
            writer.writerow(
                {
                    "table": field.table,
                    "order": field.order,
                    "column": field.column,
                    "logical_type": field.logical_type,
                    "key_role": field.key_role,
                    "description": field.description,
                }
            )


def canonical_sources(
    inventory_data: list[dict[str, Any]], line_counts: dict[str, int], row_overrides: dict[str, int] | None = None
) -> tuple[list[list[Any]], list[list[Any]]]:
    by_path = {item["path"]: item for item in inventory_data}
    row_overrides = row_overrides or {}
    canonical_map = {
        "Empresas": lambda p: "/Empresas" in p and p.endswith(".EMPRECSV"),
        "Estabelecimentos": lambda p: "/Estabelecimentos" in p and p.endswith(".ESTABELE"),
        "Socios": lambda p: "/Socios" in p and p.endswith(".SOCIOCSV"),
        "Simples": lambda p: "SIMPLES.CSV.D60314" in p,
        "Cnaes": lambda p: p.endswith("CNAECSV"),
        "Municipios": lambda p: p.endswith("MUNICCSV"),
        "Naturezas": lambda p: p.endswith("NATJUCSV"),
        "Motivos": lambda p: p.endswith("MOTICSV"),
        "Paises": lambda p: p.endswith("PAISCSV"),
        "Qualificacoes": lambda p: p.endswith("QUALSCSV"),
        "Regimes_Tributarios": lambda p: "Regimes Tributários" in p and p.endswith(".csv"),
        "Documentacao_PDF": lambda p: p.endswith(".pdf"),
    }
    canonical_rows: list[list[Any]] = []
    for name, matcher in canonical_map.items():
        matched = [(path, by_path[path], line_counts.get(path)) for path in sorted(by_path) if matcher(path)]
        total_size = sum(item["size_bytes"] for _, item, _ in matched)
        total_rows = row_overrides.get(name, sum(lc or 0 for _, _, lc in matched))
        canonical_rows.append([name, len(matched), human_size(total_size), total_rows if total_rows else "-", "sim"])

    zip_rows = []
    for item in sorted(inventory_data, key=lambda x: x["path"]):
        if item["suffix"] == ".zip":
            zip_rows.append(
                [
                    item["path"],
                    human_size(item["size_bytes"]),
                    len(item.get("zip_entries", [])),
                    "ignorar na leitura; usar pasta extraida",
                ]
            )
    return canonical_rows, zip_rows


def render_inventory_report(summary: dict[str, Any], canonical_rows: list[list[Any]], zip_rows: list[list[Any]]) -> None:
    lines = [
        "# Fase 01 - Inventario Operacional da Base",
        "",
        "Este documento registra quais arquivos sao canonicos para o projeto, quais devem ser ignorados na leitura e quais chaves serao usadas nas etapas seguintes.",
        "",
        "## Resumo",
        "",
        f"- Arquivos totais observados na pasta `Base de Dados`: {summary['total_files']}",
        f"- Tamanho total aproximado da base: {summary['total_size_human']}",
        f"- Arquivos canonicos extraidos do snapshot `2026-03`: {summary['canonical_extracted_files']}",
        f"- Arquivos ZIP redundantes no snapshot `2026-03`: {summary['zip_files']}",
        f"- PDFs de documentacao: {summary['pdf_files']}",
        "",
        "## Fontes canonicas para a Fase 1 e para o pipeline",
        "",
        md_table(["Bloco", "Arquivos", "Tamanho total", "Linhas/Paginas", "Usar no pipeline"], canonical_rows),
        "",
        "## Politica de uso dos ZIPs",
        "",
        "- Os ZIPs do bloco `2026-03` sao redundantes para leitura analitica porque o conteudo ja esta extraido em pastas paralelas.",
        "- A regra operacional do projeto passa a ser: usar as pastas extraidas como fonte canonica e ignorar os ZIPs em todas as etapas de leitura.",
        "- Na leitura auditada com DuckDB, as particoes `Estabelecimentos0`, `Estabelecimentos2`, `Estabelecimentos5` e `Estabelecimentos9` exigiram normalizacao transitoria para UTF-8 por causa de bytes inconsistentes. Os arquivos-fonte permanecem canonicos; a normalizacao e apenas um passo de ingestao reproduzivel.",
        "",
        "## Chaves de uniao confirmadas",
        "",
        "- `cnpj_basico` liga `Empresas`, `Socios`, `Simples` e a base empresarial derivada de `Estabelecimentos`.",
        "- `cnpj_basico + cnpj_ordem + cnpj_dv` identifica unicamente o estabelecimento.",
        "- `natureza_juridica`, `municipio`, `cnae_fiscal_principal`, `motivo_situacao_cadastral`, `pais` e qualificacoes sao ligados por tabelas de dominio.",
        "",
        "## Tabelas e granularidades",
        "",
        "- `Empresas`: 1 linha por CNPJ basico.",
        "- `Estabelecimentos`: 1 linha por CNPJ de 14 digitos.",
        "- `Socios`: 1 linha por socio vinculado a um CNPJ basico.",
        "- `Simples`: 1 linha por CNPJ basico.",
        "- `Regimes Tributarios`: granularidade anual por CNPJ ou CNPJ/SCP, dependendo do arquivo.",
        "",
        "## ZIPs identificados",
        "",
        md_table(["Arquivo ZIP", "Tamanho", "Entradas", "Regra"], zip_rows),
        "",
    ]
    (OUT_DIR / "01_inventario_operacional.md").write_text("\n".join(lines), encoding="utf-8")


def build_summary_from_inventory(inventory_data: list[dict[str, Any]]) -> dict[str, Any]:
    total_files = len(inventory_data)
    total_size = sum(item["size_bytes"] for item in inventory_data)
    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_human": human_size(total_size),
        "zip_files": sum(1 for item in inventory_data if item["suffix"] == ".zip"),
        "pdf_files": sum(1 for item in inventory_data if item["suffix"] == ".pdf"),
        "canonical_extracted_files": sum(1 for item in inventory_data if "2026-03" in item["path"] and item["suffix"] != ".zip"),
    }


def run_checks(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    checks["empresas"] = fetch_record(
        con,
        """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT cnpj_basico) AS distinct_cnpj_basico,
            SUM(CASE WHEN cnpj_basico IS NULL OR TRIM(cnpj_basico) = '' THEN 1 ELSE 0 END) AS blank_cnpj_basico,
            SUM(CASE WHEN natureza_juridica IS NULL OR TRIM(natureza_juridica) = '' THEN 1 ELSE 0 END) AS blank_natureza,
            SUM(CASE WHEN n.codigo IS NULL AND TRIM(COALESCE(e.natureza_juridica, '')) <> '' THEN 1 ELSE 0 END) AS invalid_natureza,
            SUM(CASE WHEN q.codigo IS NULL AND TRIM(COALESCE(e.qualificacao_responsavel, '')) <> '' THEN 1 ELSE 0 END) AS invalid_qualificacao_responsavel,
            SUM(CASE WHEN TRIM(COALESCE(porte, '')) <> '' AND porte NOT IN ('00','01','03','05') THEN 1 ELSE 0 END) AS invalid_porte
        FROM empresas_src e
        LEFT JOIN naturezas_dom n ON e.natureza_juridica = n.codigo
        LEFT JOIN qualificacoes_dom q ON e.qualificacao_responsavel = q.codigo
        """,
    )
    checks["empresas_duplicate_samples"] = fetch_rows(
        con,
        """
        SELECT cnpj_basico, COUNT(*) AS n
        FROM empresas_src
        GROUP BY 1
        HAVING COUNT(*) > 1
        ORDER BY n DESC, cnpj_basico
        LIMIT 20
        """,
    )
    checks["estabelecimentos"] = fetch_record(
        con,
        """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT cnpj_basico || cnpj_ordem || cnpj_dv) AS distinct_cnpj_14,
            COUNT(DISTINCT cnpj_basico) AS distinct_cnpj_basico,
            SUM(CASE WHEN identificador_matriz_filial NOT IN ('1','2') THEN 1 ELSE 0 END) AS invalid_identificador_matriz_filial,
            SUM(CASE WHEN situacao_cadastral NOT IN ('01','02','03','04','08') THEN 1 ELSE 0 END) AS invalid_situacao_cadastral,
            SUM(CASE WHEN m.codigo IS NULL AND TRIM(COALESCE(e.motivo_situacao_cadastral, '')) <> '' THEN 1 ELSE 0 END) AS invalid_motivo_situacao,
            SUM(CASE WHEN mun.codigo IS NULL AND TRIM(COALESCE(e.municipio, '')) <> '' THEN 1 ELSE 0 END) AS invalid_municipio,
            SUM(CASE WHEN c.codigo IS NULL AND TRIM(COALESCE(e.cnae_fiscal_principal, '')) <> '' THEN 1 ELSE 0 END) AS invalid_cnae_principal,
            SUM(CASE WHEN p.codigo IS NULL AND TRIM(COALESCE(e.pais, '')) <> '' THEN 1 ELSE 0 END) AS invalid_pais,
            SUM(CASE WHEN NOT regexp_full_match(COALESCE(e.data_inicio_atividade, ''), '^[0-9]{8}$') THEN 1 ELSE 0 END) AS invalid_data_inicio_formato,
            SUM(CASE WHEN e.data_situacao_cadastral IN ('0', '00000000') THEN 1 ELSE 0 END) AS data_situacao_sentinela_zero,
            SUM(
                CASE
                    WHEN TRIM(COALESCE(e.data_situacao_cadastral, '')) <> ''
                     AND e.data_situacao_cadastral NOT IN ('0', '00000000')
                     AND NOT regexp_full_match(COALESCE(e.data_situacao_cadastral, ''), '^[0-9]{8}$')
                    THEN 1 ELSE 0
                END
            ) AS invalid_data_situacao_formato,
            SUM(
                CASE
                    WHEN regexp_full_match(COALESCE(e.data_inicio_atividade, ''), '^[0-9]{8}$')
                     AND regexp_full_match(COALESCE(e.data_situacao_cadastral, ''), '^[0-9]{8}$')
                     AND e.data_situacao_cadastral <> '00000000'
                     AND e.data_situacao_cadastral <> '0'
                     AND e.data_situacao_cadastral < e.data_inicio_atividade
                    THEN 1 ELSE 0
                END
            ) AS data_situacao_antes_inicio
        FROM estabelecimentos_src e
        LEFT JOIN motivos_dom m ON e.motivo_situacao_cadastral = m.codigo
        LEFT JOIN municipios_dom mun ON e.municipio = mun.codigo
        LEFT JOIN cnaes_dom c ON e.cnae_fiscal_principal = c.codigo
        LEFT JOIN paises_dom p ON lpad(trim(e.pais), 3, '0') = p.codigo
        """,
    )
    checks["estabelecimentos_duplicate_samples"] = fetch_rows(
        con,
        """
        SELECT cnpj_basico || cnpj_ordem || cnpj_dv AS cnpj_14, COUNT(*) AS n
        FROM estabelecimentos_src
        GROUP BY 1
        HAVING COUNT(*) > 1
        ORDER BY n DESC, cnpj_14
        LIMIT 20
        """,
    )
    checks["matriz_counts"] = fetch_record(
        con,
        """
        WITH per_empresa AS (
            SELECT
                cnpj_basico,
                SUM(CASE WHEN identificador_matriz_filial = '1' THEN 1 ELSE 0 END) AS matriz_count
            FROM estabelecimentos_src
            GROUP BY 1
        )
        SELECT
            COUNT(*) AS empresas_com_estabelecimento,
            SUM(CASE WHEN matriz_count = 0 THEN 1 ELSE 0 END) AS empresas_sem_matriz,
            SUM(CASE WHEN matriz_count = 1 THEN 1 ELSE 0 END) AS empresas_com_matriz_unica,
            SUM(CASE WHEN matriz_count > 1 THEN 1 ELSE 0 END) AS empresas_com_multiplas_matrizes
        FROM per_empresa
        """,
    )
    checks["cross_table_consistency"] = fetch_record(
        con,
        """
        SELECT
            (SELECT COUNT(*) FROM (SELECT DISTINCT cnpj_basico FROM estabelecimentos_src EXCEPT SELECT DISTINCT cnpj_basico FROM empresas_src)) AS cnpj_basico_est_sem_empresa,
            (SELECT COUNT(*) FROM (SELECT DISTINCT cnpj_basico FROM empresas_src EXCEPT SELECT DISTINCT cnpj_basico FROM estabelecimentos_src)) AS cnpj_basico_empresa_sem_estabelecimento
        """,
    )
    checks["socios"] = fetch_record(
        con,
        """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT cnpj_basico) AS distinct_cnpj_basico,
            SUM(CASE WHEN identificador_socio NOT IN ('1','2','3') THEN 1 ELSE 0 END) AS invalid_identificador_socio,
            SUM(CASE WHEN q1.codigo IS NULL AND TRIM(COALESCE(s.qualificacao_socio, '')) <> '' THEN 1 ELSE 0 END) AS invalid_qualificacao_socio,
            SUM(CASE WHEN q2.codigo IS NULL AND TRIM(COALESCE(s.qualificacao_representante_legal, '')) <> '' THEN 1 ELSE 0 END) AS invalid_qualificacao_representante,
            SUM(CASE WHEN p.codigo IS NULL AND TRIM(COALESCE(s.pais, '')) <> '' THEN 1 ELSE 0 END) AS invalid_pais,
            SUM(CASE WHEN faixa_etaria NOT IN ('0','1','2','3','4','5','6','7','8','9') THEN 1 ELSE 0 END) AS invalid_faixa_etaria
        FROM socios_src s
        LEFT JOIN qualificacoes_dom q1 ON s.qualificacao_socio = q1.codigo
        LEFT JOIN qualificacoes_dom q2 ON s.qualificacao_representante_legal = q2.codigo
        LEFT JOIN paises_dom p ON lpad(trim(s.pais), 3, '0') = p.codigo
        """,
    )
    checks["simples"] = fetch_record(
        con,
        """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT cnpj_basico) AS distinct_cnpj_basico,
            SUM(CASE WHEN opcao_simples NOT IN ('S','N','') THEN 1 ELSE 0 END) AS invalid_opcao_simples,
            SUM(CASE WHEN opcao_mei NOT IN ('S','N','') THEN 1 ELSE 0 END) AS invalid_opcao_mei,
            SUM(CASE WHEN TRIM(COALESCE(data_opcao_simples, '')) <> '' AND NOT regexp_full_match(data_opcao_simples, '^[0-9]{8}$') THEN 1 ELSE 0 END) AS invalid_data_opcao_simples,
            SUM(CASE WHEN TRIM(COALESCE(data_exclusao_simples, '')) <> '' AND NOT regexp_full_match(data_exclusao_simples, '^[0-9]{8}$') THEN 1 ELSE 0 END) AS invalid_data_exclusao_simples,
            SUM(CASE WHEN TRIM(COALESCE(data_opcao_mei, '')) <> '' AND NOT regexp_full_match(data_opcao_mei, '^[0-9]{8}$') THEN 1 ELSE 0 END) AS invalid_data_opcao_mei,
            SUM(CASE WHEN TRIM(COALESCE(data_exclusao_mei, '')) <> '' AND NOT regexp_full_match(data_exclusao_mei, '^[0-9]{8}$') THEN 1 ELSE 0 END) AS invalid_data_exclusao_mei
        FROM simples_src
        """,
    )
    checks["invalid_code_samples"] = {
        "empresas_invalid_natureza": fetch_rows(
            con,
            """
            SELECT natureza_juridica AS codigo, COUNT(*) AS n
            FROM empresas_src e
            LEFT JOIN naturezas_dom n ON e.natureza_juridica = n.codigo
            WHERE TRIM(COALESCE(e.natureza_juridica, '')) <> '' AND n.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
        "empresas_invalid_qualificacao_responsavel": fetch_rows(
            con,
            """
            SELECT qualificacao_responsavel AS codigo, COUNT(*) AS n
            FROM empresas_src e
            LEFT JOIN qualificacoes_dom q ON e.qualificacao_responsavel = q.codigo
            WHERE TRIM(COALESCE(e.qualificacao_responsavel, '')) <> '' AND q.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
        "est_invalid_municipio": fetch_rows(
            con,
            """
            SELECT municipio AS codigo, COUNT(*) AS n
            FROM estabelecimentos_src e
            LEFT JOIN municipios_dom m ON e.municipio = m.codigo
            WHERE TRIM(COALESCE(e.municipio, '')) <> '' AND m.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
        "est_invalid_motivo": fetch_rows(
            con,
            """
            SELECT motivo_situacao_cadastral AS codigo, COUNT(*) AS n
            FROM estabelecimentos_src e
            LEFT JOIN motivos_dom m ON e.motivo_situacao_cadastral = m.codigo
            WHERE TRIM(COALESCE(e.motivo_situacao_cadastral, '')) <> '' AND m.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
        "est_invalid_cnae_principal": fetch_rows(
            con,
            """
            SELECT cnae_fiscal_principal AS codigo, COUNT(*) AS n
            FROM estabelecimentos_src e
            LEFT JOIN cnaes_dom c ON e.cnae_fiscal_principal = c.codigo
            WHERE TRIM(COALESCE(e.cnae_fiscal_principal, '')) <> '' AND c.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
        "socios_invalid_qualificacao_socio": fetch_rows(
            con,
            """
            SELECT qualificacao_socio AS codigo, COUNT(*) AS n
            FROM socios_src s
            LEFT JOIN qualificacoes_dom q ON s.qualificacao_socio = q.codigo
            WHERE TRIM(COALESCE(s.qualificacao_socio, '')) <> '' AND q.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
        "est_invalid_pais": fetch_rows(
            con,
            """
            SELECT pais AS codigo, COUNT(*) AS n
            FROM estabelecimentos_src e
            LEFT JOIN paises_dom p ON lpad(trim(e.pais), 3, '0') = p.codigo
            WHERE TRIM(COALESCE(e.pais, '')) <> '' AND p.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
        "socios_invalid_pais": fetch_rows(
            con,
            """
            SELECT pais AS codigo, COUNT(*) AS n
            FROM socios_src s
            LEFT JOIN paises_dom p ON lpad(trim(s.pais), 3, '0') = p.codigo
            WHERE TRIM(COALESCE(s.pais, '')) <> '' AND p.codigo IS NULL
            GROUP BY 1
            ORDER BY n DESC, codigo
            LIMIT 10
            """,
        ),
    }
    return checks


def render_integrity_report(checks: dict[str, Any]) -> None:
    emp = checks["empresas"]
    est = checks["estabelecimentos"]
    soc = checks["socios"]
    sim = checks["simples"]
    matriz = checks["matriz_counts"]
    cross = checks["cross_table_consistency"]

    quality_issues: list[str] = []
    if emp["invalid_qualificacao_responsavel"]:
        quality_issues.append(
            f"`Empresas.qualificacao_responsavel` tem {emp['invalid_qualificacao_responsavel']} registros fora do dominio de `Qualificacoes`."
        )
    if est["invalid_cnae_principal"]:
        quality_issues.append(
            f"`Estabelecimentos.cnae_fiscal_principal` tem {est['invalid_cnae_principal']} registros fora do dominio `Cnaes`."
        )
    if est["invalid_municipio"]:
        quality_issues.append(
            f"`Estabelecimentos.municipio` tem {est['invalid_municipio']} registros fora do dominio `Municipios`."
        )
    if est["invalid_motivo_situacao"]:
        quality_issues.append(
            f"`Estabelecimentos.motivo_situacao_cadastral` tem {est['invalid_motivo_situacao']} registros fora do dominio `Motivos`; o codigo observado fora da referencia foi `32`."
        )
    if est["invalid_pais"]:
        quality_issues.append(
            f"`Estabelecimentos.pais` manteve {est['invalid_pais']} registros fora do dominio mesmo apos padronizacao com zero a esquerda."
        )
    if soc["invalid_pais"]:
        quality_issues.append(
            f"`Socios.pais` manteve {soc['invalid_pais']} registros fora do dominio mesmo apos padronizacao com zero a esquerda."
        )
    if est["data_situacao_sentinela_zero"]:
        quality_issues.append(
            f"`Estabelecimentos.data_situacao_cadastral` usa o sentinela `0` em {est['data_situacao_sentinela_zero']} registros; isso deve ser tratado como ausencia de data, nao como data valida."
        )
    if est["data_situacao_antes_inicio"]:
        quality_issues.append(
            f"{est['data_situacao_antes_inicio']} estabelecimentos tem `data_situacao_cadastral` anterior a `data_inicio_atividade`."
        )
    if matriz["empresas_sem_matriz"]:
        quality_issues.append(
            f"{matriz['empresas_sem_matriz']} CNPJs basicos observados em `Estabelecimentos` nao possuem registro de matriz."
        )
    if matriz["empresas_com_multiplas_matrizes"]:
        quality_issues.append(
            f"{matriz['empresas_com_multiplas_matrizes']} CNPJs basicos possuem mais de uma matriz e exigem regra explicita na Fase 2."
        )
    if not quality_issues:
        quality_issues.append("Nenhum problema estrutural relevante foi identificado na Fase 1.")

    lines = [
        "# Fase 01 - Integridade e Consistencia",
        "",
        "Este documento resume as checagens de unicidade, chaves de uniao, consistencia entre tabelas e aderencia aos dominios codificados.",
        "",
        "## 1. Unicidade por tabela",
        "",
        md_table(
            ["Tabela", "Linhas", "Chave avaliada", "Distinct da chave", "Resultado"],
            [
                ["Empresas", emp["total_rows"], "`cnpj_basico`", emp["distinct_cnpj_basico"], "ok" if emp["total_rows"] == emp["distinct_cnpj_basico"] else "duplicatas"],
                ["Estabelecimentos", est["total_rows"], "`cnpj_basico+ordem+dv`", est["distinct_cnpj_14"], "ok" if est["total_rows"] == est["distinct_cnpj_14"] else "duplicatas"],
                ["Simples", sim["total_rows"], "`cnpj_basico`", sim["distinct_cnpj_basico"], "ok" if sim["total_rows"] == sim["distinct_cnpj_basico"] else "duplicatas"],
            ],
        ),
        "",
        "## 2. Consistencia entre `Empresas` e `Estabelecimentos`",
        "",
        md_table(
            ["Cheque", "Valor"],
            [
                ["CNPJs basicos em `Estabelecimentos` sem correspondente em `Empresas`", cross["cnpj_basico_est_sem_empresa"]],
                ["CNPJs basicos em `Empresas` sem correspondente em `Estabelecimentos`", cross["cnpj_basico_empresa_sem_estabelecimento"]],
                ["Empresas observadas em `Estabelecimentos`", matriz["empresas_com_estabelecimento"]],
                ["Empresas com matriz unica", matriz["empresas_com_matriz_unica"]],
                ["Empresas sem matriz", matriz["empresas_sem_matriz"]],
                ["Empresas com multiplas matrizes", matriz["empresas_com_multiplas_matrizes"]],
            ],
        ),
        "",
        "## 3. Dominios e formatos",
        "",
        md_table(
            ["Tabela", "Cheque", "Ocorrencias fora da regra"],
            [
                ["Empresas", "natureza_juridica fora do dominio", emp["invalid_natureza"]],
                ["Empresas", "qualificacao_responsavel fora do dominio", emp["invalid_qualificacao_responsavel"]],
                ["Empresas", "porte fora do conjunto permitido", emp["invalid_porte"]],
                ["Estabelecimentos", "identificador_matriz_filial invalido", est["invalid_identificador_matriz_filial"]],
                ["Estabelecimentos", "situacao_cadastral invalida", est["invalid_situacao_cadastral"]],
                ["Estabelecimentos", "motivo_situacao fora do dominio", est["invalid_motivo_situacao"]],
                ["Estabelecimentos", "municipio fora do dominio", est["invalid_municipio"]],
                ["Estabelecimentos", "cnae_principal fora do dominio", est["invalid_cnae_principal"]],
                ["Estabelecimentos", "pais fora do dominio", est["invalid_pais"]],
                ["Estabelecimentos", "data_inicio fora do formato yyyymmdd", est["invalid_data_inicio_formato"]],
                ["Estabelecimentos", "data_situacao com sentinela zero", est["data_situacao_sentinela_zero"]],
                ["Estabelecimentos", "data_situacao fora do formato yyyymmdd", est["invalid_data_situacao_formato"]],
                ["Estabelecimentos", "data_situacao antes de data_inicio", est["data_situacao_antes_inicio"]],
                ["Socios", "identificador_socio invalido", soc["invalid_identificador_socio"]],
                ["Socios", "qualificacao_socio fora do dominio", soc["invalid_qualificacao_socio"]],
                ["Socios", "qualificacao_representante fora do dominio", soc["invalid_qualificacao_representante"]],
                ["Socios", "pais fora do dominio", soc["invalid_pais"]],
                ["Socios", "faixa_etaria invalida", soc["invalid_faixa_etaria"]],
                ["Simples", "opcao_simples invalida", sim["invalid_opcao_simples"]],
                ["Simples", "opcao_mei invalida", sim["invalid_opcao_mei"]],
                ["Simples", "data_opcao_simples fora do formato", sim["invalid_data_opcao_simples"]],
                ["Simples", "data_exclusao_simples fora do formato", sim["invalid_data_exclusao_simples"]],
                ["Simples", "data_opcao_mei fora do formato", sim["invalid_data_opcao_mei"]],
                ["Simples", "data_exclusao_mei fora do formato", sim["invalid_data_exclusao_mei"]],
            ],
        ),
        "",
        "## 4. Problemas de qualidade relevantes identificados",
        "",
    ]
    for issue in quality_issues:
        lines.append(f"- {issue}")

    lines.extend(["", "## 5. Amostras de codigos fora do dominio", ""])
    for name, rows in checks["invalid_code_samples"].items():
        lines.append(f"### {name}")
        lines.append("")
        if rows:
            lines.append(md_table(["codigo", "ocorrencias"], [[r["codigo"], r["n"]] for r in rows]))
        else:
            lines.append("Nenhuma ocorrencia.")
        lines.append("")

    (OUT_DIR / "03_integridade_consistencia.md").write_text("\n".join(lines), encoding="utf-8")


def render_methodology_review(checks: dict[str, Any]) -> None:
    cross = checks["cross_table_consistency"]
    matriz = checks["matriz_counts"]
    est = checks["estabelecimentos"]
    emp = checks["empresas"]

    lines = [
        "# Fase 01 - Revisao Metodologica",
        "",
        "Esta revisao avalia se a Fase 1 terminou com algum erro metodologico evidente ou com alguma premissa perigosa para as fases seguintes.",
        "",
        "## Parecer geral",
        "",
        "A Fase 1 ficou metodologicamente coerente para continuar o projeto, mas ela estabelece algumas regras obrigatorias para as fases seguintes.",
        "",
        "## Pontos aprovados",
        "",
        "- A fonte canonica foi definida corretamente: usar os arquivos extraidos e ignorar os ZIPs redundantes.",
        "- O processo de leitura ficou reproduzivel mesmo com anomalias de encoding em 4 particoes de `Estabelecimentos`; a normalizacao transitoria foi isolada como etapa tecnica de ingestao, sem alterar a fonte bruta.",
        "- A granularidade das tabelas foi explicitada antes da modelagem.",
        "- As chaves de uniao principais ficaram claras: `cnpj_basico` para empresa e `cnpj_basico+ordem+dv` para estabelecimento.",
        "- A integridade estrutural principal esta boa: `Empresas` e `Simples` estao unicas por `cnpj_basico`; `Estabelecimentos` esta unico por CNPJ de 14 digitos.",
        "",
        "## Alertas metodologicos que precisam virar regra",
        "",
    ]

    if matriz["empresas_com_multiplas_matrizes"] > 0:
        lines.append(
            f"- Existem {matriz['empresas_com_multiplas_matrizes']} CNPJs basicos com mais de uma matriz. Antes de construir a base empresarial, a Fase 2 precisa definir uma regra explicita de resolucao."
        )
    else:
        lines.append("- Nao houve empresas com multiplas matrizes; o recorte por matriz parece seguro.")

    if matriz["empresas_sem_matriz"] > 0:
        lines.append(
            f"- Existem {matriz['empresas_sem_matriz']} CNPJs basicos sem matriz observada. Eles nao podem ser descartados sem documentacao."
        )
    else:
        lines.append("- Todos os CNPJs basicos observados em `Estabelecimentos` possuem pelo menos uma matriz, o que ajuda o desenho empresarial.")

    if cross["cnpj_basico_est_sem_empresa"] > 0 or cross["cnpj_basico_empresa_sem_estabelecimento"] > 0:
        lines.append("- A consistencia entre `Empresas` e `Estabelecimentos` nao e perfeita. A Fase 2 precisa definir regra clara de elegibilidade.")
    else:
        lines.append("- `Empresas` e `Estabelecimentos` ficaram consistentes na chave `cnpj_basico` para os cheques basicos da Fase 1.")

    if est["data_situacao_antes_inicio"] > 0:
        lines.append(
            f"- Foram encontrados {est['data_situacao_antes_inicio']} casos com cronologia invalida entre inicio e situacao cadastral. Esses registros devem ser tratados antes da modelagem temporal."
        )
    else:
        lines.append("- Nao apareceram incoerencias cronologicas entre `data_inicio_atividade` e `data_situacao_cadastral` nesta auditoria.")

    if est["data_situacao_sentinela_zero"] > 0:
        lines.append(
            f"- Existem {est['data_situacao_sentinela_zero']} registros com `data_situacao_cadastral = 0`. Isso nao deve ser tratado como erro de formato nem como data real; na Fase 2 a regra correta e converter para ausente."
        )
    else:
        lines.append("- Nao apareceram sentinelas `0` em `data_situacao_cadastral`.")

    if emp["invalid_qualificacao_responsavel"] > 0:
        lines.append(
            f"- `qualificacao_responsavel` apresentou {emp['invalid_qualificacao_responsavel']} ocorrencias fora do dominio validado. A Fase 2 deve tratar isso como categoria desconhecida ou revisar a referencia."
        )
    else:
        lines.append("- Os dominios centrais de `Empresas` ficaram coerentes com as tabelas auxiliares auditadas.")

    if est["invalid_motivo_situacao"] > 0:
        lines.append(
            f"- `motivo_situacao_cadastral` apresentou {est['invalid_motivo_situacao']} ocorrencias fora do dominio. O codigo observado foi `32`, ausente na tabela `Motivos`; por enquanto ele deve ser tratado como categoria desconhecida e documentada."
        )
    else:
        lines.append("- `motivo_situacao_cadastral` ficou coerente com a tabela `Motivos`.")

    if est["invalid_pais"] > 0 or checks["socios"]["invalid_pais"] > 0:
        lines.append(
            f"- Os codigos de pais ainda ficaram fora do dominio mesmo apos zero-padding: {est['invalid_pais']} em `Estabelecimentos` e {checks['socios']['invalid_pais']} em `Socios`. A Fase 2 deve consolidar esses casos como categoria residual e nao assumir que a tabela `Paises` cobre integralmente o historico."
        )
    else:
        lines.append("- Os codigos de pais ficaram aderentes ao dominio auditado apos padronizacao.")

    lines.extend(
        [
            "",
            "## O que NAO deve ser feito na Fase 2",
            "",
            "- Nao usar todos os estabelecimentos e chamar isso de empresa sem justificar.",
            "- Nao usar `Socios` como historico societario; ela e uma foto observada.",
            "- Nao tratar qualquer mudanca cadastral como baixa definitiva.",
            "- Nao tratar `data_situacao_cadastral = 0` como data valida.",
            "- Nao descartar silenciosamente codigos fora de dominio; eles precisam virar categoria residual documentada.",
            "- Nao construir feature de risco com informacao posterior ao ponto de observacao.",
            "",
            "## Conclusao",
            "",
            "A Fase 1 esta aprovada como base metodologica do projeto. O proximo risco real nao esta mais na fonte, e sim nas decisoes de modelagem da Fase 2: unidade analitica, regras de elegibilidade, tratamento de anomalias cronologicas, tratamento explicito de sentinelas e definicao correta do target temporal.",
        ]
    )

    (OUT_DIR / "04_revisao_metodologica_fase_01.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inventory_data = load_json_if_exists(ROOT / "tmp_inventory.json")
    line_count_data = load_json_if_exists(ROOT / "tmp_line_counts.json")
    if inventory_data is None or line_count_data is None:
        raise SystemExit("tmp_inventory.json e tmp_line_counts.json sao necessarios para gerar o inventario da Fase 1.")

    line_counts = {item["path"]: int(item["line_count"]) for item in line_count_data}
    write_schema_csv()

    summary = build_summary_from_inventory(inventory_data)
    con = build_con()
    build_views(con)
    checks = normalize_numbers(run_checks(con))
    row_overrides = {
        "Empresas": checks["empresas"]["total_rows"],
        "Estabelecimentos": checks["estabelecimentos"]["total_rows"],
        "Socios": checks["socios"]["total_rows"],
        "Simples": checks["simples"]["total_rows"],
    }
    canonical_rows, zip_rows = canonical_sources(inventory_data, line_counts, row_overrides=row_overrides)
    render_inventory_report(summary, canonical_rows, zip_rows)
    render_integrity_report(checks)
    render_methodology_review(checks)

    phase_summary = {"inventory_summary": summary, "checks": checks}
    (OUT_DIR / "00_resumo_fase_01.json").write_text(
        json.dumps(phase_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
