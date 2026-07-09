"""Mapeamento de alarmes em familias funcionais (H009).

Operacionaliza a hipotese H009: agrupar os ~712 alarmes distintos em
familias funcionais (motor/transmissao/hidraulico/etc.) gera features de
contagem por familia que sao informativas isoladamente.

A taxonomia abaixo foi construida a partir da inspecao dos 712 nomes
distintos na telemetria (jan-jun 2025), priorizando:
1. **Determinismo**: um alarme cai em **exatamente uma** familia
   (regra de prioridade explicita).
2. **Cobertura**: 0 alarmes ficam sem familia ("Other" e fallback).
3. **Semantica fisica**: cada familia agrupa modos de falha que
   compartilham um sub-sistema (motor, hidraulico, freio, etc.) — essa
   e a base para o builder da Fase 3C.

Auditavel: rodar `python -m src.features.families` imprime a distribuicao
de alarmes por familia para inspecao visual.

Uso típico
----------
    from src.features.families import family_of, FAMILIES

    fam = family_of("Engine Coolant Level - Active")  # "Engine_Coolant"

    # Em SQL DuckDB:
    from src.features.families import FAMILIES_SQL_CASE
    sql = f"SELECT *, {FAMILIES_SQL_CASE} AS familia FROM tel"
"""
from __future__ import annotations

import re
from typing import Iterable

# Lista CANONICA de familias — ordem importa (a primeira que casar vence).
# `key` e o nome canonico; `patterns` e a lista de regex case-insensitive
# (alguns mais especificos vem antes para evitar match prematuro em outra
# familia). Comentarios indicam exemplos representativos e fontes
# encontradas na inspecao dos 712 alarmes.
FAMILIES: list[tuple[str, list[str]]] = [
    (
        # Sub-sistema de arrefecimento (motor) — top driver de Don't Go
        # Engine Coolant Level - Active e o alarme #1 (42% dos incidentes)
        "Engine_Coolant",
        [
            r"\bcoolant\b",
            r"\barref",  # "ARREF." (pt, com ou sem ponto)
            r"temp\.? arref",  # "MC - ALTA TEMP. ARREF. DO MOTOR"
        ],
    ),
    (
        # Lubrificacao do motor (oleo de motor especifico)
        # Engine Oil Level/Pressure (en + pt)
        "Engine_Oil",
        [
            r"engine oil",
            r"engine prelube",
            r"\bcrankcase\b",  # crankcase pressure
            r"low oil pressure",
            r"\bóleo motor\b|\boleo motor\b",  # pt
            r"pressão.*óleo|pressao.*oleo",  # "MC - QUEDA PRESSÃO DO ÓLEO MOTOR"
            r"filtro.*óleo|filtro.*oleo",  # "FILTRO ÓLEO MOTOR OBSTRUÍDO"
        ],
    ),
    (
        # Transmissao + diferencial + torque converter (mesmo trem de força)
        "Transmission",
        [
            r"\btransmission\b",
            r"\btransmiss",  # pt
            r"final drive",
            r"differential",
            r"torque converter",
        ],
    ),
    (
        # Hidraulico (caminhoes + pa LeTourneau — HPD, klenz, hoist)
        "Hydraulic",
        [
            r"\bhydraulic\b",
            r"\bhidraul",
            r"\bhpd\b",
            r"hoist",
            r"klenz",
            r"accessory pump",
        ],
    ),
    (
        # Freios (en + pt + variantes "Park Brake" sem -ing)
        "Brakes",
        [
            r"\bbrake\b",
            r"\bbrakes\b",
            r"\bpark\b.*brake",
            r"\bfreio",
            r"parking brake",
        ],
    ),
    (
        # Direção
        "Steering",
        [
            r"steering",
            r"steer\b",
            r"direção|direcao",
        ],
    ),
    (
        # Exaustão / turbinas / aftercooler (en + pt "Exaust")
        "Exhaust_Turbo",
        [
            r"exhaust",
            r"\bexaust\b",  # pt "Dif Temp Exaust"
            r"turbo",
            r"aftercooler",
            r"intake",
            r"injector",
        ],
    ),
    (
        # Operação de carga (corpo/cassamba/pá/lift) — relevante para
        # LeTourneau (escavadeira) mas tambem aparece em caminhoes
        # quando ha sobrecarga.
        "Body_Load",
        [
            r"\bbody\b",
            r"\blift arm",
            r"\bbucket\b",
            r"\bdipper\b",
            r"rollback",
            r"\bdump\b",
            r"\bpayload\b",
            r"\bload\b",
            r"truck load",
        ],
    ),
    (
        # Estado operacional / pedal / aceleracao
        "Operational_State",
        [
            r"vehicle speed",
            r"engine.*throttle",
            r"throttle",
            r"torque mode",
            r"\bcycle\b",
            r"\btire tag\b",
            r"engine .* high",
            r"low engine",
        ],
    ),
    (
        # Eletrica / comunicacao / sensor I/O / shutdown / start motor
        "Electrical_Comms",
        [
            r"rx channel",
            r"oem interface",
            r"voltagem|voltage",
            r"\bswitch\b",
            r"timeout",
            r"\bsensor\b",
            r"can bus|j1939",
            r"shutdown input",
            r"start motor",
            r"channel forced",
        ],
    ),
    (
        # Combustivel / DEF / DPF (en + pt)
        "Fuel_AfterTreatment",
        [
            r"\bfuel\b",
            r"\bdef\b",
            r"\bdpf\b",
            r"\bregeneration\b",
            r"combust",  # pt
        ],
    ),
    (
        # Fan drive
        "Fan_Drive",
        [
            r"\bfan\b",
        ],
    ),
    (
        # Pneus / suspensao (estado mecanico do chassi)
        "Tires_Suspension",
        [
            r"tire pressure",
            r"\btire\b",
            r"suspension",
        ],
    ),
    (
        # Filtros e ar (ar de admissao, ar do sistema, ambiente)
        "Air_Filters",
        [
            r"air filter",
            r"\bfiltro\b",
            r"ambient air",
            r"\bair leak\b",
        ],
    ),
]


# Compila uma vez na importacao — performance.
_COMPILED: list[tuple[str, list[re.Pattern[str]]]] = [
    (name, [re.compile(p, flags=re.IGNORECASE) for p in patterns])
    for name, patterns in FAMILIES
]

FAMILY_NAMES: tuple[str, ...] = tuple(name for name, _ in FAMILIES) + ("Other",)


def family_of(alarme: str | None) -> str:
    """Retorna a familia funcional do alarme.

    Determinismo: a primeira familia em `FAMILIES` que casar vence
    (ordem importa). Alarmes nao reconhecidos caem em `"Other"`.
    `None` ou string vazia caem em `"Other"` tambem.

    >>> family_of("Engine Coolant Level - Active")
    'Engine_Coolant'
    >>> family_of("Low Transmission Oil Level")
    'Transmission'
    >>> family_of("Left Rear Brake Temperature - Active")
    'Brakes'
    >>> family_of("Steering Oil Temperature - Active")
    'Steering'
    >>> family_of("Hydraulic Reservoir Oil Temperature Critically High (L-1850)")
    'Hydraulic'
    >>> family_of(None)
    'Other'
    >>> family_of("")
    'Other'
    >>> family_of("UNKNOWN_ALARM_FOO_BAR")
    'Other'
    """
    if not alarme:
        return "Other"
    for name, patterns in _COMPILED:
        for pat in patterns:
            if pat.search(alarme):
                return name
    return "Other"


def family_distribution(
    alarmes: Iterable[str | None],
) -> dict[str, int]:
    """Retorna a contagem de alarmes por familia.

    Util para auditoria — verificar se a taxonomia cobre o universo.
    """
    counts: dict[str, int] = {name: 0 for name in FAMILY_NAMES}
    for a in alarmes:
        counts[family_of(a)] += 1
    return counts


def _build_sql_case() -> str:
    """SQL fragment que classifica `Alarme` em familia, em ordem de
    prioridade. Usado pelo builder DuckDB.

    Replica a logica de `family_of` em SQL para evitar UDF (mais lento).
    """
    parts: list[str] = []
    for name, patterns in FAMILIES:
        # combine os patterns daquela familia em um unico regex via |
        combined = "|".join(p for p in patterns)
        # escapar aspas simples
        combined_sql = combined.replace("'", "''")
        parts.append(
            f"WHEN regexp_matches(LOWER(Alarme), '{combined_sql.lower()}', 'i') THEN '{name}'"
        )
    body = "\n    ".join(parts)
    return f"CASE\n    {body}\n    ELSE 'Other'\nEND"


# String pronta para usar em queries SQL.
FAMILIES_SQL_CASE: str = _build_sql_case()


__all__ = [
    "FAMILIES",
    "FAMILY_NAMES",
    "FAMILIES_SQL_CASE",
    "family_of",
    "family_distribution",
]


if __name__ == "__main__":  # pragma: no cover
    # Auditoria: imprime distribuicao na populacao da telemetria.
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

    from src.data.loaders import get_connection, load_telemetria_lazy  # noqa: E402

    con = get_connection()
    con.execute("PRAGMA disable_progress_bar")
    rel = load_telemetria_lazy(con)
    TEL = "(" + rel.sql_query() + ")"

    df = con.sql(
        f"SELECT Alarme, COUNT(*) AS n FROM {TEL} WHERE Alarme IS NOT NULL GROUP BY ALL"
    ).df()
    df["familia"] = df["Alarme"].map(family_of)
    print(f"# alarmes distintos: {len(df)}")
    print()
    by_fam = (
        df.groupby("familia")
        .agg(n_alarmes=("Alarme", "count"), n_eventos=("n", "sum"))
        .reset_index()
        .sort_values("n_eventos", ascending=False)
    )
    print(by_fam.to_string(index=False))
    print()
    other = df[df["familia"] == "Other"].sort_values("n", ascending=False)
    print(f"\nTop 30 alarmes em 'Other' (n_distinct={len(other)}, n_eventos={int(other['n'].sum()):,}):")
    print(other.head(30).to_string(index=False))
