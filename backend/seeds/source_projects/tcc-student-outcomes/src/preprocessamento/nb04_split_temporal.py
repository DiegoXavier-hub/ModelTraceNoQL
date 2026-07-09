from pathlib import Path
import pandas as pd
import numpy as np

PROJETO_ROOT = Path(__file__).resolve().parent.parent.parent
DADOS = PROJETO_ROOT / "data" / "preprocessamento"

ANO_CORTE_EXCLUSAO = 2020

SPLITS = {
    "treino": lambda ano: ano <= 2015,
    "val":    lambda ano: ano.between(2016, 2017),
    "teste":  lambda ano: ano.between(2018, 2019),
}

for janela in [1, 2, 4]:
    ml = pd.read_parquet(DADOS / f"ml_p{janela}.parquet")
    print(f"\n{'='*60}")
    print(f"SPLIT TEMPORAL — JANELA p{janela}")
    print(f"{'='*60}")
    print(f"Total ANTES da exclusao: {len(ml):,} alunos")

    excluidos = ml[ml["ano_ingresso"] >= ANO_CORTE_EXCLUSAO]
    ml_filtrado = ml[ml["ano_ingresso"] < ANO_CORTE_EXCLUSAO].copy()

    print(f"\nExcluidos (ano_ingresso >= {ANO_CORTE_EXCLUSAO}): {len(excluidos):,} alunos")
    print(f"  Distribuicao dos excluidos por ano:")
    for ano, sub in excluidos.groupby("ano_ingresso"):
        print(f"    {ano}: {len(sub)} alunos (evasao: {sub['y'].mean()*100:.1f}%)")
    print(f"\nTotal APOS exclusao: {len(ml_filtrado):,} alunos")

    resultados = {}
    for nome, condicao in SPLITS.items():
        mask = condicao(ml_filtrado["ano_ingresso"])
        df_split = ml_filtrado[mask].copy()
        resultados[nome] = df_split

    total_split = sum(len(v) for v in resultados.values())
    assert total_split == len(ml_filtrado), \
        f"ERRO: split nao cobre todos os alunos ({total_split} vs {len(ml_filtrado)})"

    print(f"\n{'—'*50}")
    print(f"{'Conjunto':<12} {'Alunos':>8} {'%':>7} {'y=0':>7} {'y=1':>7} {'Evasao%':>9}")
    print(f"{'—'*50}")
    for nome, df_split in resultados.items():
        n = len(df_split)
        y0 = (df_split["y"] == 0).sum()
        y1 = (df_split["y"] == 1).sum()
        pct = n / len(ml_filtrado) * 100
        ev = y1 / n * 100 if n > 0 else 0
        print(f"{nome:<12} {n:>8,} {pct:>6.1f}% {y0:>7,} {y1:>7,} {ev:>8.1f}%")

    total_n = len(ml_filtrado)
    total_y1 = ml_filtrado["y"].sum()
    print(f"{'—'*50}")
    print(f"{'TOTAL':<12} {total_n:>8,} {'100.0%':>7} {total_n - total_y1:>7,} {total_y1:>7,} {total_y1/total_n*100:>8.1f}%")

    print(f"\nDistribuicao por curso:")
    for nome, df_split in resultados.items():
        ct = df_split.groupby("curso_origem")["y"].agg(["size", "sum"])
        ct.columns = ["total", "evadidos"]
        ct["evasao_%"] = (ct["evadidos"] / ct["total"] * 100).round(1)
        print(f"\n  [{nome}]")
        for curso, row in ct.iterrows():
            print(f"    {curso}: {int(row['total'])} alunos ({row['evasao_%']}% evasao)")

    print(f"\nFaixa de anos por conjunto:")
    for nome, df_split in resultados.items():
        anos = df_split["ano_ingresso"]
        print(f"  {nome}: {anos.min()} a {anos.max()} ({len(df_split)} alunos)")

    for nome, df_split in resultados.items():
        path = DADOS / f"{nome}_p{janela}.parquet"
        df_split.to_parquet(path, index=False)
        print(f"\nSalvo: {path.name} ({len(df_split):,} x {df_split.shape[1]})")

print(f"\n{'='*60}")
print("ANALISE DE DRIFT TEMPORAL (taxa de evasao por faixa de ingresso)")
print(f"{'='*60}")

for janela in [1, 2, 4]:
    ml = pd.read_parquet(DADOS / f"ml_p{janela}.parquet")
    ml = ml[ml["ano_ingresso"] < ANO_CORTE_EXCLUSAO]

    print(f"\n--- p{janela} ---")

    faixas = pd.cut(ml["ano_ingresso"],
                    bins=[0, 1990, 1995, 2000, 2005, 2010, 2015, 2017, 2019],
                    labels=["<1990", "1990-95", "1996-00", "2001-05",
                            "2006-10", "2011-15", "2016-17", "2018-19"])
    drift = ml.groupby(faixas, observed=True)["y"].agg(["size", "mean"])
    drift.columns = ["alunos", "taxa_evasao"]
    drift["taxa_evasao_%"] = (drift["taxa_evasao"] * 100).round(1)
    print(drift[["alunos", "taxa_evasao_%"]].to_string())

    splits = {"treino": ml[ml["ano_ingresso"] <= 2015],
              "val": ml[ml["ano_ingresso"].between(2016, 2017)],
              "teste": ml[ml["ano_ingresso"].between(2018, 2019)]}
    print(f"\n  Resumo por split:")
    for nome, df_s in splits.items():
        print(f"    {nome}: evasao = {df_s['y'].mean()*100:.1f}%")

print("\nNotebook 04 concluido com sucesso.")
