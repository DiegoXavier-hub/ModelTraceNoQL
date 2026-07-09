"""Fase 2E — confirmacoes operacionais.

T3.2 — Localidade unica nos 6 parquets.
T3.6 — Pareamento Apontamento x Telemetria.
D016 — Inferencia de operador por moda no intervalo do ciclo.
T3.7 — Origem da coluna 'Porte' do exemplo Don't Go.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.data.loaders import (
    get_connection,
    load_apontamentos,
    load_telemetria_lazy,
)
from src.utils.paths import DONTGO_EXAMPLE_XLSX, REPORTS_DIR
from src.utils.seeds import set_global_seed

set_global_seed()
RESULTS: dict = {}
RESULTS_DIR = REPORTS_DIR / "eda_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

con = get_connection()
rel = load_telemetria_lazy(con)
TEL = "(" + rel.sql_query() + ")"


def section(t: str) -> None:
    print()
    print("-" * 72)
    print(t)
    print("-" * 72)


print("=" * 72)
print("Fase 2E — Confirmacoes operacionais")
print("=" * 72)

# -------------------------------------------------------------------------
# T3.2 — Localidade unica nos 6 parquets
# -------------------------------------------------------------------------
section("[2E.1] T3.2 — Localidade unica?")
loc = con.sql(f"SELECT DISTINCT Localidade FROM {TEL} ORDER BY Localidade").df()
print(loc)
RESULTS["localidades_distintas"] = loc["Localidade"].astype(str).tolist()
print(f"# localidades distintas: {len(loc)}")
print(
    "T3.2: "
    + (
        "Itabira UNICO confirmado em todos os 6 parquets"
        if len(loc) == 1 and "Itabira" in str(loc.iloc[0, 0])
        else f"Multiplas localidades: {loc['Localidade'].tolist()}"
    )
)

# Tambem por mes (caso o pipeline mude de localidade ao longo do tempo)
loc_mes = con.sql(
    f"""
    SELECT date_trunc('month', Data_Evento) AS mes, Localidade, COUNT(*) AS n
    FROM {TEL}
    GROUP BY ALL
    ORDER BY mes, Localidade
    """
).df()
RESULTS["localidades_por_mes"] = loc_mes.to_dict("records")
print(f"\nlinhas (mes, localidade): {len(loc_mes)}")
print(loc_mes)

# -------------------------------------------------------------------------
# T3.6 — Pareamento Apontamento x Telemetria
# -------------------------------------------------------------------------
section("[2E.2] T3.6 — Pareamento Apontamento x Telemetria (amostra de 1000 ciclos)")
apt = load_apontamentos(con)
print(f"apontamentos total: {len(apt):,}")

# amostra estratificada por mes
apt_sample = apt.assign(mes=apt["Inicio"].dt.to_period("M").astype(str))
sampled_per_mes = (
    apt_sample.groupby("mes", group_keys=False)
    .apply(lambda g: g.sample(min(167, len(g)), random_state=42))
)
sampled = sampled_per_mes.reset_index(drop=True)
print(f"amostra: {len(sampled)} ciclos (estratificada por mes)")

# Para cada ciclo, contar eventos de telemetria com mesmo TAG e Data_Evento em [Inicio, Fim]
sampled_tmp = sampled[["Id", "Tag", "Inicio", "Fim", "Classe"]].copy()
con.register("apt_sample", sampled_tmp)

pareamento = con.sql(
    f"""
    SELECT a.Id, a.Tag, a.Classe AS apt_classe,
           a.Inicio, a.Fim,
           date_diff('second', a.Inicio, a.Fim)/60.0 AS dur_min,
           (
               SELECT COUNT(*)
               FROM {TEL} t
               WHERE t.TAG = a.Tag
                 AND t.Data_Evento >= a.Inicio
                 AND t.Data_Evento <  a.Fim
           ) AS n_eventos_tel
    FROM apt_sample a
    """
).df()
print(f"\nestatisticas do pareamento:")
print(pareamento["n_eventos_tel"].describe())
RESULTS["pareamento_n_eventos_describe"] = (
    pareamento["n_eventos_tel"].describe().to_dict()
)
RESULTS["pareamento_pct_zero"] = float(
    (pareamento["n_eventos_tel"] == 0).mean() * 100
)
RESULTS["pareamento_pct_zero_operando"] = float(
    (
        (pareamento["n_eventos_tel"] == 0)
        & (pareamento["apt_classe"] == "Operando")
    ).mean() * 100
)
print(f"\n% ciclos com 0 eventos de telemetria: {RESULTS['pareamento_pct_zero']:.2f}%")
print(
    f"% ciclos 'Operando' com 0 eventos: {RESULTS['pareamento_pct_zero_operando']:.2f}%"
)

por_classe = (
    pareamento.groupby("apt_classe")["n_eventos_tel"]
    .agg(["count", "mean", "median", lambda x: (x == 0).mean() * 100])
    .rename(columns={"<lambda_0>": "pct_zero"})
    .reset_index()
)
print()
print("pareamento por classe de apontamento:")
print(por_classe)
RESULTS["pareamento_por_classe"] = por_classe.to_dict("records")

# -------------------------------------------------------------------------
# D016 — Inferencia de operador por moda
# -------------------------------------------------------------------------
section("[2E.3] D016 — Operador inferido por moda (amostra)")

# Pegar mais ciclos para um teste robusto
sample2 = apt.sample(min(2000, len(apt)), random_state=42)[
    ["Id", "Tag", "Inicio", "Fim", "Classe"]
].copy()
con.unregister("apt_sample")
con.register("apt_sample", sample2)

# Para cada ciclo, pegar moda do operador.
# CORRECAO: o denominador correto e o total de eventos do ciclo (incluindo
# os com Nome_Operador_Anon=NULL), nao apenas os eventos com operador.
# A versao bug coincide com a correta neste dataset porque operador e
# universal nos eventos que existem (propriedade descoberta na auditoria),
# mas o SQL deve ser semanticamente correto.
oper = con.sql(
    f"""
    WITH ciclo_total AS (
        SELECT a.Id,
               COUNT(t.Data_Evento) AS n_total_ciclo
        FROM apt_sample a
        LEFT JOIN {TEL} t
          ON t.TAG = a.Tag AND t.Data_Evento >= a.Inicio AND t.Data_Evento < a.Fim
        GROUP BY a.Id
    ),
    ciclo_moda AS (
        SELECT a.Id, a.Tag, a.Classe AS apt_classe, op.operador, op.n_op
        FROM apt_sample a
        LEFT JOIN LATERAL (
            SELECT t.Nome_Operador_Anon AS operador, COUNT(*) AS n_op
            FROM {TEL} t
            WHERE t.TAG = a.Tag
              AND t.Data_Evento >= a.Inicio
              AND t.Data_Evento <  a.Fim
              AND t.Nome_Operador_Anon IS NOT NULL
            GROUP BY t.Nome_Operador_Anon
            ORDER BY n_op DESC
            LIMIT 1
        ) op ON TRUE
    )
    SELECT m.Id, m.Tag, m.apt_classe, m.operador, m.n_op,
           c.n_total_ciclo AS n_total,
           1.0 * m.n_op / NULLIF(c.n_total_ciclo, 0) AS share_moda
    FROM ciclo_moda m
    LEFT JOIN ciclo_total c ON c.Id = m.Id
    """
).df()

print(f"amostra: {len(oper)} ciclos")
print(f"  ciclos com operador inferivel (>=1 evento com operador): {oper['operador'].notna().sum()}")
print(f"  ciclos sem operador: {oper['operador'].isna().sum()}")

oper_ok = oper.dropna(subset=["operador"])
if len(oper_ok) > 0:
    desc_share = oper_ok["share_moda"].describe(percentiles=[0.5, 0.75, 0.9, 0.95])
    print()
    print("share da moda (entre os ciclos com operador inferivel):")
    print(desc_share)
    pct_80 = float((oper_ok["share_moda"] >= 0.80).mean() * 100)
    pct_50 = float((oper_ok["share_moda"] >= 0.50).mean() * 100)
    print(f"\n% ciclos com share >= 80%: {pct_80:.2f}%")
    print(f"% ciclos com share >= 50%: {pct_50:.2f}%")
    RESULTS["operador_inferido"] = {
        "n_amostra": int(len(oper)),
        "n_inferivel": int(oper["operador"].notna().sum()),
        "share_moda_describe": {k: float(v) for k, v in desc_share.items()},
        "pct_share_ge_80": pct_80,
        "pct_share_ge_50": pct_50,
    }

# -------------------------------------------------------------------------
# T3.7 — Origem da coluna 'Porte' do exemplo Don't Go
# -------------------------------------------------------------------------
section("[2E.4] T3.7 — Origem da coluna 'Porte'")
ex = pd.read_excel(DONTGO_EXAMPLE_XLSX)
print(f"exemplo dontgo: shape={ex.shape}, cols={list(ex.columns)}")
if "Porte" in ex.columns:
    porte_uniq = ex["Porte"].unique().tolist()
    print(f"valores de Porte no exemplo: {porte_uniq}")
    RESULTS["exemplo_porte"] = {
        "presente": True,
        "valores_unicos": [str(v) for v in porte_uniq],
        "tag_frota_no_exemplo": list(ex["Tag_Frota"].unique()),
    }
    # mapeamento
    if "Tag_Frota" in ex.columns:
        m = ex.groupby("Tag_Frota")["Porte"].nunique().to_dict()
        print(f"# valores de Porte por Tag_Frota: {m}")
        RESULTS["exemplo_porte"]["mapeamento_unico_por_frota"] = (
            all(v == 1 for v in m.values())
        )
else:
    RESULTS["exemplo_porte"] = {"presente": False}

# Verificar se Porte aparece em algum lugar dos parquets de telemetria
cols_tel = con.sql(f"SELECT * FROM {TEL} LIMIT 0").df().columns.tolist()
RESULTS["porte_em_telemetria"] = "Porte" in cols_tel
print(f"\n'Porte' existe em telemetria? {'Porte' in cols_tel}")

# -------------------------------------------------------------------------
# Persistir
# -------------------------------------------------------------------------
out = RESULTS_DIR / "fase2e_results.json"
out.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
print(f"\n>>> Fase 2E salva em {out}")
print("=" * 72)
