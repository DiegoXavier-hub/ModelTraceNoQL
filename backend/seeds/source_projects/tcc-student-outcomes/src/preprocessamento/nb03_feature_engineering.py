from pathlib import Path
import pandas as pd
import numpy as np

PROJETO_ROOT = Path(__file__).resolve().parent.parent.parent
DADOS = PROJETO_ROOT / "data" / "preprocessamento"

def engenharia_features(df_disc, df_alunos, janela):
    """Cria features agregadas por aluno a partir dos registros de disciplina."""

    print(f"\n{'='*60}")
    print(f"FEATURE ENGINEERING — JANELA p{janela}")
    print(f"{'='*60}")
    print(f"Registros de disciplina: {len(df_disc):,}")
    print(f"Alunos: {df_disc['id_aluno'].nunique():,}")

    df_com_nota = df_disc[df_disc["nota"].notna()].copy()

    notas = df_com_nota.groupby("id_aluno")["nota"].agg(
        nota_media="mean",
        nota_mediana="median",
        nota_desvio="std",
        nota_min="min",
        nota_max="max",
    ).reset_index()
    notas["nota_desvio"] = notas["nota_desvio"].fillna(0)

    print(f"\n1. Notas: {len(notas):,} alunos com pelo menos 1 nota")

    contagens_grupo = (
        df_disc.groupby(["id_aluno", "grupo_situacao_disc"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["aprovado", "reprovado", "dispensa", "sem_resultado"]:
        if col not in contagens_grupo.columns:
            contagens_grupo[col] = 0

    contagens_grupo = contagens_grupo.rename(columns={
        "aprovado": "qtd_aprovacoes",
        "reprovado": "qtd_reprovacoes",
        "dispensa": "qtd_dispensas",
        "sem_resultado": "qtd_sem_resultado",
    })
    contagens_grupo = contagens_grupo[["id_aluno", "qtd_aprovacoes", "qtd_reprovacoes",
                                        "qtd_dispensas", "qtd_sem_resultado"]]

    df_reprov = df_disc[df_disc["grupo_situacao_disc"] == "reprovado"].copy()
    reprov_tipo = (
        df_reprov.assign(
            reprov_nota=df_reprov["situacao_disciplina"].str.contains("Nota", na=False).astype(int),
            reprov_freq=df_reprov["situacao_disciplina"].str.contains("Frequ", na=False).astype(int),
        )
        .groupby("id_aluno")[["reprov_nota", "reprov_freq"]]
        .sum()
        .reset_index()
        .rename(columns={"reprov_nota": "qtd_reprov_nota", "reprov_freq": "qtd_reprov_freq"})
    )

    apr = contagens_grupo[["id_aluno", "qtd_aprovacoes", "qtd_reprovacoes"]].copy()
    apr["tentativas"] = apr["qtd_aprovacoes"] + apr["qtd_reprovacoes"]
    apr["taxa_aprovacao"] = np.where(
        apr["tentativas"] > 0,
        apr["qtd_aprovacoes"] / apr["tentativas"],
        np.nan
    )
    taxa_aprov = apr[["id_aluno", "taxa_aprovacao"]]

    print(f"2. Aprovacao/Reprovacao: {len(contagens_grupo):,} alunos")

    qtd_disc_total = df_disc.groupby("id_aluno").size().reset_index(name="qtd_disciplinas_total")

    disc_por_periodo = (
        df_disc.groupby(["id_aluno", "periodo_sequencial"])
        .size()
        .reset_index(name="n_disc")
        .groupby("id_aluno")["n_disc"]
        .mean()
        .reset_index()
        .rename(columns={"n_disc": "media_disc_por_periodo"})
    )

    df_ch = df_disc[
        (df_disc["grupo_situacao_disc"].isin(["aprovado", "dispensa"])) &
        (df_disc["carga_horaria"].notna())
    ].copy()
    ch_acum = (
        df_ch.groupby("id_aluno")["carga_horaria"]
        .sum()
        .reset_index()
        .rename(columns={"carga_horaria": "ch_acumulada"})
    )

    print(f"3. Carga de trabalho: {len(qtd_disc_total):,} alunos")

    nota_por_periodo = (
        df_com_nota.groupby(["id_aluno", "periodo_sequencial"])["nota"]
        .mean()
        .reset_index()
        .rename(columns={"nota": "nota_media_periodo"})
        .sort_values(["id_aluno", "periodo_sequencial"])
    )

    primeiro_periodo = nota_por_periodo.drop_duplicates("id_aluno", keep="first")[
        ["id_aluno", "nota_media_periodo"]
    ].rename(columns={"nota_media_periodo": "nota_p1"})
    ultimo_periodo = nota_por_periodo.drop_duplicates("id_aluno", keep="last")[
        ["id_aluno", "nota_media_periodo"]
    ].rename(columns={"nota_media_periodo": "nota_ultimo"})

    tendencia = primeiro_periodo.merge(ultimo_periodo, on="id_aluno")
    tendencia["delta_nota"] = tendencia["nota_ultimo"] - tendencia["nota_p1"]
    tendencia = tendencia[["id_aluno", "nota_p1", "delta_nota"]]

    df_p1 = df_disc[df_disc["periodo_sequencial"] == 1]
    reprov_p1 = (
        df_p1[df_p1["grupo_situacao_disc"] == "reprovado"]
        .groupby("id_aluno")
        .size()
        .reset_index(name="reprov_p1")
    )

    disc_p1 = (
        df_p1.groupby("id_aluno")
        .size()
        .reset_index(name="disc_p1")
    )

    print(f"4. Padroes temporais: {len(tendencia):,} alunos com tendencia de nota")

    cols_aluno = ["id_aluno", "y", "curso_origem", "situacao_aluno",
                  "tipo_ingresso", "ano_ingresso", "num_semestre_ingresso",
                  "versao", "ch_total_exigida", "max_periodo",
                  "sexo", "idade_ingresso", "forma_ingresso_grp",
                  "cotista", "natural_uberlandia"]
    base = df_alunos[cols_aluno].copy()

    for df_feat in [notas, contagens_grupo, reprov_tipo, taxa_aprov,
                     qtd_disc_total, disc_por_periodo, ch_acum,
                     tendencia, reprov_p1, disc_p1]:
        base = base.merge(df_feat, on="id_aluno", how="left")

    base["pct_ch_concluida"] = np.where(
        base["ch_total_exigida"] > 0,
        base["ch_acumulada"] / base["ch_total_exigida"],
        np.nan
    )

    colunas_contagem = ["qtd_aprovacoes", "qtd_reprovacoes", "qtd_dispensas",
                        "qtd_sem_resultado", "qtd_reprov_nota", "qtd_reprov_freq",
                        "qtd_disciplinas_total", "reprov_p1", "disc_p1",
                        "ch_acumulada"]
    for col in colunas_contagem:
        if col in base.columns:
            base[col] = base[col].fillna(0).astype(int)

    n_alunos = len(base)
    n_features = len([c for c in base.columns if c not in
                      ["id_aluno", "y", "situacao_aluno"]])

    print(f"\n{'='*40}")
    print(f"DATASET FINAL p{janela}")
    print(f"{'='*40}")
    print(f"Alunos: {n_alunos:,}")
    print(f"Features (incluindo metadados): {n_features}")
    print(f"Colunas: {list(base.columns)}")

    assert base["id_aluno"].is_unique, "ERRO: alunos duplicados na base final!"

    assert base["y"].notna().all(), "ERRO: alunos sem y!"

    print(f"\nDistribuicao de y:")
    for val, cnt in base["y"].value_counts().sort_index().items():
        label = "nao-evadido" if val == 0 else "evadido"
        print(f"  y={val} ({label}): {cnt} ({cnt/n_alunos*100:.1f}%)")

    nulls = base.isnull().sum()
    nulls_pct = (nulls / n_alunos * 100).round(1)
    cols_com_null = nulls[nulls > 0]
    if len(cols_com_null) > 0:
        print(f"\nColunas com valores nulos:")
        for col in cols_com_null.index:
            print(f"  {col}: {cols_com_null[col]} ({nulls_pct[col]}%)")
    else:
        print("\nNenhuma coluna com nulos.")

    features_num = ["nota_media", "nota_mediana", "nota_desvio", "nota_min", "nota_max",
                    "qtd_aprovacoes", "qtd_reprovacoes", "qtd_dispensas",
                    "qtd_reprov_nota", "qtd_reprov_freq", "taxa_aprovacao",
                    "qtd_disciplinas_total", "media_disc_por_periodo",
                    "ch_acumulada", "pct_ch_concluida",
                    "nota_p1", "delta_nota", "reprov_p1", "disc_p1"]
    features_presentes = [f for f in features_num if f in base.columns]
    print(f"\nEstatisticas das features:")
    print(base[features_presentes].describe().round(2).to_string())

    return base


print(f"\n{'='*60}")
print(f"FEATURE ENGINEERING — JANELA p1 (INGRESSO)")
print(f"{'='*60}")

alunos_p1 = pd.read_parquet(DADOS / "alunos_p1.parquet")
print(f"Alunos: {len(alunos_p1):,}")

cols_p1 = ["id_aluno", "y", "curso_origem", "situacao_aluno",
           "tipo_ingresso", "ano_ingresso", "num_semestre_ingresso",
           "versao", "ch_total_exigida", "max_periodo",
           "sexo", "idade_ingresso", "forma_ingresso_grp",
           "cotista", "natural_uberlandia"]
ml_p1 = alunos_p1[cols_p1].copy()

assert ml_p1["id_aluno"].is_unique, "ERRO: alunos duplicados na base p1!"
assert ml_p1["y"].notna().all(), "ERRO: alunos sem y!"

print(f"\nDistribuicao de y (p1):")
for val, cnt in ml_p1["y"].value_counts().sort_index().items():
    label = "nao-evadido" if val == 0 else "evadido"
    print(f"  y={val} ({label}): {cnt} ({cnt/len(ml_p1)*100:.1f}%)")

nulls = ml_p1.isnull().sum()
cols_null = nulls[nulls > 0]
if len(cols_null) > 0:
    print(f"\nColunas com nulos (p1):")
    for col in cols_null.index:
        print(f"  {col}: {cols_null[col]} ({cols_null[col]/len(ml_p1)*100:.1f}%)")

path_p1 = DADOS / "ml_p1.parquet"
ml_p1.to_parquet(path_p1, index=False)
print(f"\nSalvo: {path_p1.name} ({ml_p1.shape[0]:,} linhas x {ml_p1.shape[1]} colunas)")

for janela in [2, 4]:
    df_disc = pd.read_parquet(DADOS / f"coorte_p{janela}.parquet")
    df_alunos = pd.read_parquet(DADOS / f"alunos_p{janela}.parquet")

    ml_base = engenharia_features(df_disc, df_alunos, janela)

    path = DADOS / f"ml_p{janela}.parquet"
    ml_base.to_parquet(path, index=False)
    print(f"\nSalvo: {path.name} ({ml_base.shape[0]:,} linhas x {ml_base.shape[1]} colunas)")

print("\nNotebook 03 concluido com sucesso.")
