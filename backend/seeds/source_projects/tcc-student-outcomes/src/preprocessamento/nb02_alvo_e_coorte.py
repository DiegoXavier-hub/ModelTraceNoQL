from pathlib import Path
import pandas as pd

PROJETO_ROOT = Path(__file__).resolve().parent.parent.parent
DADOS = PROJETO_ROOT / "data" / "preprocessamento"

df = pd.read_parquet(DADOS / "base_consolidada_granular.parquet")
print(f"Base carregada: {df.shape[0]:,} linhas, {df['id_aluno'].nunique():,} alunos")

MAPA_ALVO = {
    "Formado":      0,
    "Abandono":     1,
    "Desistente":   1,
    "Jubilamento":  1,
    "Desligamento": 1,
}

assert set(df["situacao_aluno"].unique()) == set(MAPA_ALVO.keys()), \
    f"Valores nao mapeados: {set(df['situacao_aluno'].unique()) - set(MAPA_ALVO.keys())}"

alunos = df.drop_duplicates("id_aluno")[
    ["id_aluno", "curso_origem", "situacao_aluno", "ano_ingresso",
     "num_semestre_ingresso", "tipo_ingresso", "versao", "ch_total_exigida",
     "sexo", "idade_ingresso", "forma_ingresso_grp",
     "cotista", "natural_uberlandia"]
].copy()
alunos["y"] = alunos["situacao_aluno"].map(MAPA_ALVO)

print(f"Total de alunos: {len(alunos):,}")
print(f"\nDistribuicao do alvo:")
for val, cnt in alunos["y"].value_counts().sort_index().items():
    label = "nao-evadido" if val == 0 else "evadido"
    print(f"  y={val} ({label}): {cnt} ({cnt/len(alunos)*100:.1f}%)")

print(f"\nPor curso e alvo:")
ct = pd.crosstab(alunos["curso_origem"], alunos["y"], margins=True)
ct.columns = ["nao_evadido", "evadido", "total"]
ct["taxa_evasao_%"] = (ct["evadido"] / ct["total"] * 100).round(1)
print(ct.to_string())

periodos_por_aluno = (
    df[df["periodo_sequencial"].notna()]
    .groupby("id_aluno")["periodo_sequencial"]
    .max()
    .astype(int)
    .reset_index()
    .rename(columns={"periodo_sequencial": "max_periodo"})
)

alunos = alunos.merge(periodos_por_aluno, on="id_aluno", how="left")
alunos["max_periodo"] = alunos["max_periodo"].fillna(0).astype(int)

print("Distribuicao de max_periodo (quantos periodos cada aluno cursou):")
dist = alunos["max_periodo"].value_counts().sort_index()
for per, cnt in dist.items():
    print(f"  {per} periodos: {cnt} alunos")
    if per > 15:
        print("  ...")
        break

print(f"\nAlunos com 0 periodos (sem disciplinas com semestre): {(alunos['max_periodo'] == 0).sum()}")

def selecionar_coorte(df_disciplinas, df_alunos, janela):
    """Seleciona coorte elegivel para uma janela e filtra disciplinas ate a janela."""
    elegiveis = df_alunos[df_alunos["max_periodo"] >= janela].copy()

    n_total = len(df_alunos)
    n_elegiveis = len(elegiveis)
    n_excluidos = n_total - n_elegiveis

    print(f"\n{'='*50}")
    print(f"JANELA p{janela}")
    print(f"{'='*50}")
    print(f"Total de alunos: {n_total:,}")
    print(f"Elegiveis (>= {janela} periodos): {n_elegiveis:,}")
    print(f"Excluidos (< {janela} periodos): {n_excluidos:,} ({n_excluidos/n_total*100:.1f}%)")

    excluidos = df_alunos[df_alunos["max_periodo"] < janela]
    print(f"\nDistribuicao dos excluidos por situacao:")
    for sit, cnt in excluidos["situacao_aluno"].value_counts().items():
        print(f"  {sit}: {cnt}")

    print(f"\nDistribuicao da coorte elegivel:")
    for val, cnt in elegiveis["y"].value_counts().sort_index().items():
        label = "nao-evadido" if val == 0 else "evadido"
        pct = cnt / len(elegiveis) * 100
        print(f"  y={val} ({label}): {cnt} ({pct:.1f}%)")

    print(f"\nPor curso:")
    ct = pd.crosstab(elegiveis["curso_origem"], elegiveis["y"], margins=True)
    ct.columns = ["nao_evadido", "evadido", "total"]
    ct["taxa_evasao_%"] = (ct["evadido"] / ct["total"] * 100).round(1)
    print(ct.to_string())

    ids_elegiveis = set(elegiveis["id_aluno"])
    df_filtrado = df_disciplinas[
        (df_disciplinas["id_aluno"].isin(ids_elegiveis)) &
        (df_disciplinas["periodo_sequencial"].notna()) &
        (df_disciplinas["periodo_sequencial"] <= janela)
    ].copy()

    print(f"\nLinhas de disciplina na coorte (ate p{janela}): {len(df_filtrado):,}")
    print(f"Alunos com disciplinas: {df_filtrado['id_aluno'].nunique():,}")

    return elegiveis, df_filtrado

print(f"\n{'='*50}")
print(f"JANELA p1 (INGRESSO)")
print(f"{'='*50}")
print(f"Todos os alunos sao elegiveis (momento da matricula)")
print(f"Total: {len(alunos):,} alunos")
print(f"\nDistribuicao da coorte p1:")
for val, cnt in alunos["y"].value_counts().sort_index().items():
    label = "nao-evadido" if val == 0 else "evadido"
    pct = cnt / len(alunos) * 100
    print(f"  y={val} ({label}): {cnt} ({pct:.1f}%)")
coorte_p1_alunos = alunos.copy()

coorte_p2_alunos, coorte_p2_disc = selecionar_coorte(df, alunos, janela=2)
coorte_p4_alunos, coorte_p4_disc = selecionar_coorte(df, alunos, janela=4)

for nome, df_disc, df_al in [
    ("coorte_p2", coorte_p2_disc, coorte_p2_alunos),
    ("coorte_p4", coorte_p4_disc, coorte_p4_alunos),
]:
    cols_aluno = ["id_aluno", "y", "curso_origem", "situacao_aluno",
                  "ano_ingresso", "num_semestre_ingresso", "tipo_ingresso",
                  "versao", "ch_total_exigida", "max_periodo",
                  "sexo", "idade_ingresso", "forma_ingresso_grp",
                  "cotista", "natural_uberlandia"]
    df_saida = df_disc.merge(
        df_al[cols_aluno],
        on="id_aluno",
        how="left",
        suffixes=("", "_aluno")
    )

    for col in ["curso_origem", "situacao_aluno", "ano_ingresso",
                "num_semestre_ingresso", "tipo_ingresso", "versao", "ch_total_exigida",
                "sexo", "idade_ingresso", "forma_ingresso_grp",
                "cotista", "natural_uberlandia"]:
        if f"{col}_aluno" in df_saida.columns:
            df_saida = df_saida.drop(columns=[f"{col}_aluno"])

    path = DADOS / f"{nome}.parquet"
    df_saida.to_parquet(path, index=False)
    print(f"\n{nome}: {df_saida.shape[0]:,} linhas, {df_saida['id_aluno'].nunique():,} alunos -> {path.name}")

for nome, df_al in [("alunos_p1", coorte_p1_alunos),
                     ("alunos_p2", coorte_p2_alunos),
                     ("alunos_p4", coorte_p4_alunos)]:
    path = DADOS / f"{nome}.parquet"
    df_al.to_parquet(path, index=False)
    print(f"{nome}: {len(df_al):,} alunos -> {path.name}")

print("\nNotebook 02 concluido com sucesso.")
