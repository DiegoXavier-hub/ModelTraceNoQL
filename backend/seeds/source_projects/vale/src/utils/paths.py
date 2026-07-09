"""Caminhos absolutos do projeto Vale — fonte unica de verdade.

Toda referencia a arquivos do projeto deve passar por este modulo.
NAO faca hard-code de caminhos em notebooks ou em outros modulos de src/.

Uso tipico:
    from src.utils.paths import APONTAMENTOS_PARQUET, TELEMETRIA_GLOB
    import duckdb
    rel = duckdb.sql(f"SELECT * FROM read_parquet('{TELEMETRIA_GLOB}') LIMIT 5")
"""
from __future__ import annotations

from pathlib import Path

# parents[2]: src/utils/paths.py -> src/utils -> src -> PROJECT_ROOT
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = PROJECT_ROOT / "Base de Dados"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
NOTEBOOKS_DIR: Path = PROJECT_ROOT / "notebooks"
SRC_DIR: Path = PROJECT_ROOT / "src"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"
OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
PAPERS_DIR: Path = PROJECT_ROOT / "papers"

APONTAMENTOS_DIR: Path = DATA_DIR / "datasets" / "apontamentos"
TELEMETRIA_DIR: Path = DATA_DIR / "datasets" / "telemetria"

APONTAMENTOS_PARQUET: Path = APONTAMENTOS_DIR / "desenvolver_apontamentos.parquet"
APONTAMENTOS_XLSX: Path = APONTAMENTOS_DIR / "desenvolver_apontamentos.xlsx"
DONTGO_EXAMPLE_XLSX: Path = TELEMETRIA_DIR / "desenvolver_dontgo.xlsx"
ALARMES_XLSX: Path = DATA_DIR / "Alarmes - Regra de Negocio.xlsx"
DICIONARIO_XLSX: Path = DATA_DIR / "Dicionario_Dados.xlsx"
DATASETS_README: Path = DATA_DIR / "datasets" / "README.md"

# Os parquets misturam pt/en (feb/abr/may) — preservar a grafia do disco.
TELEMETRIA_MESES: tuple[str, ...] = ("jan", "feb", "mar", "abr", "may", "jun")

TELEMETRIA_PARQUETS: dict[str, Path] = {
    mes: TELEMETRIA_DIR / f"telemetry_{mes}.parquet" for mes in TELEMETRIA_MESES
}

# String, nao Path: duckdb.read_parquet() espera glob literal (*) preservado.
TELEMETRIA_GLOB: str = str(TELEMETRIA_DIR / "telemetry_*.parquet")

FIGURES_DIR: Path = REPORTS_DIR / "figures"
TABLES_DIR: Path = REPORTS_DIR / "tables"
MODELS_DIR: Path = OUTPUTS_DIR / "models"
PREDICTIONS_DIR: Path = OUTPUTS_DIR / "predictions"


def _check_required_inputs() -> None:
    """Falha cedo se uma fonte critica de leitura sumir.

    Saidas (reports/, outputs/) nao sao validadas — sao criadas sob demanda.
    """
    required: list[tuple[Path, str]] = [
        (DATA_DIR, "DATA_DIR"),
        (APONTAMENTOS_PARQUET, "APONTAMENTOS_PARQUET"),
        (TELEMETRIA_DIR, "TELEMETRIA_DIR"),
        (ALARMES_XLSX, "ALARMES_XLSX"),
        (DICIONARIO_XLSX, "DICIONARIO_XLSX"),
    ]
    for mes in TELEMETRIA_MESES:
        required.append((TELEMETRIA_PARQUETS[mes], f"TELEMETRIA_PARQUETS[{mes!r}]"))

    missing = [(p, label) for p, label in required if not p.exists()]
    if missing:
        details = "\n".join(f"  - {label}: {p}" for p, label in missing)
        raise FileNotFoundError(
            "Caminhos obrigatorios nao encontrados "
            f"(PROJECT_ROOT={PROJECT_ROOT}):\n{details}"
        )


_check_required_inputs()


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "DOCS_DIR",
    "NOTEBOOKS_DIR",
    "SRC_DIR",
    "REPORTS_DIR",
    "OUTPUTS_DIR",
    "PAPERS_DIR",
    "APONTAMENTOS_DIR",
    "TELEMETRIA_DIR",
    "APONTAMENTOS_PARQUET",
    "APONTAMENTOS_XLSX",
    "DONTGO_EXAMPLE_XLSX",
    "ALARMES_XLSX",
    "DICIONARIO_XLSX",
    "DATASETS_README",
    "TELEMETRIA_MESES",
    "TELEMETRIA_PARQUETS",
    "TELEMETRIA_GLOB",
    "FIGURES_DIR",
    "TABLES_DIR",
    "MODELS_DIR",
    "PREDICTIONS_DIR",
]
