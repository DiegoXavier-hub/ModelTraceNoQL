import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from eda_config import (DADOS, GRAFICOS, META_COLS, CAT_COLS,
                         CORES_ALVO, LABELS_ALVO, CORES_CURSO,
                         ROXO_MEDIO, ROXO_CLARO, ROXO_ESCURO, ROXO_BG,
                         VERDE, VERMELHO, AZUL, LARANJA,
                         salvar_fig)

dfs = {}
for split in ["treino", "val", "teste"]:
    for janela in [2, 4]:
        dfs[f"{split}_p{janela}"] = pd.read_parquet(DADOS / f"{split}_p{janela}.parquet")

NUM_COLS = [c for c in dfs["treino_p2"].columns if c not in META_COLS + CAT_COLS]

for janela in [2, 4]:
    df = dfs[f"treino_p{janela}"]
    by_year = df.groupby("ano_ingresso")["y"].agg(["size", "mean"])
    by_year.columns = ["alunos", "taxa_evasao"]
    by_year["taxa_evasao_%"] = (by_year["taxa_evasao"] * 100).round(1)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=by_year.index, y=by_year["alunos"],
        name="Alunos", marker_color=ROXO_CLARO,
        marker_line_color=ROXO_ESCURO, marker_line_width=0.5,
        opacity=0.7,
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=by_year.index, y=by_year["taxa_evasao_%"],
        name="Taxa de Evasao (%)", mode="lines+markers",
        line=dict(color=VERMELHO, width=2.5),
        marker=dict(size=7, color=VERMELHO),
    ), secondary_y=True)

    fig.update_layout(
        title=f"Alunos e Taxa de Evasao por Ano de Ingresso — Treino p{janela}",
        height=500, barmode="overlay",
    )
    fig.update_yaxes(title_text="Quantidade de alunos", secondary_y=False)
    fig.update_yaxes(title_text="Taxa de evasao (%)", secondary_y=True,
                     range=[0, 100])
    fig.update_xaxes(title_text="Ano de ingresso", dtick=1)
    salvar_fig(fig, f"evasao_por_ano_treino_p{janela}")

for janela in [2, 4]:
    df = dfs[f"treino_p{janela}"]
    cursos = sorted(df["curso_origem"].unique())
    fig = go.Figure()

    for curso in cursos:
        sub = df[df["curso_origem"] == curso]
        by_year = sub.groupby("ano_ingresso")["y"].mean() * 100
        by_year_smooth = by_year.rolling(3, min_periods=1, center=True).mean()

        fig.add_trace(go.Scatter(
            x=by_year_smooth.index, y=by_year_smooth.values,
            name=curso, mode="lines+markers",
            line=dict(color=CORES_CURSO[curso], width=2),
            marker=dict(size=5),
        ))

    fig.update_layout(
        title=f"Evolucao da Taxa de Evasao por Curso — Treino p{janela} (media movel 3 anos)",
        xaxis_title="Ano de ingresso", yaxis_title="Taxa de evasao (%)",
        height=500, yaxis_range=[0, 100],
    )
    fig.update_xaxes(dtick=2)
    salvar_fig(fig, f"evasao_por_curso_ano_p{janela}")

SPLIT_CORES = {"treino": ROXO_MEDIO, "val": ROXO_CLARO, "teste": LARANJA}

for janela in [2, 4]:
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["Tamanho dos conjuntos",
                                        "Taxa de evasao por conjunto"])

    nomes = ["treino", "val", "teste"]
    tamanhos = [len(dfs[f"{s}_p{janela}"]) for s in nomes]
    taxas = [dfs[f"{s}_p{janela}"]["y"].mean() * 100 for s in nomes]

    fig.add_trace(go.Bar(
        x=nomes, y=tamanhos,
        marker_color=[SPLIT_CORES[s] for s in nomes],
        marker_line_color="black", marker_line_width=1,
        text=[f"{v:,}" for v in tamanhos], textposition="outside",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=nomes, y=taxas,
        marker_color=[SPLIT_CORES[s] for s in nomes],
        marker_line_color="black", marker_line_width=1,
        text=[f"{v:.1f}%" for v in taxas], textposition="outside",
        showlegend=False,
    ), row=1, col=2)

    fig.update_yaxes(title_text="Quantidade", row=1, col=1)
    fig.update_yaxes(title_text="Taxa de evasao (%)", range=[0, 70], row=1, col=2)
    fig.update_layout(
        title=f"Composicao dos Conjuntos — p{janela}",
        height=450,
    )
    salvar_fig(fig, f"composicao_splits_p{janela}")

print("\n" + "=" * 80)
print("DRIFT DE FEATURES ENTRE CONJUNTOS (media)")
print("=" * 80)

FEATURES_DRIFT = ["nota_media", "taxa_aprovacao", "qtd_reprovacoes",
                   "pct_ch_concluida", "nota_p1", "reprov_p1"]

for janela in [2, 4]:
    print(f"\n--- p{janela} ---")
    print(f"{'Feature':<25} {'Treino':>10} {'Val':>10} {'Teste':>10} {'Drift T->Te':>12}")
    print("-" * 70)

    drift_data = []
    for col in FEATURES_DRIFT:
        medias = {}
        for split in ["treino", "val", "teste"]:
            medias[split] = dfs[f"{split}_p{janela}"][col].mean()

        drift = ((medias["teste"] - medias["treino"]) / medias["treino"] * 100
                 if medias["treino"] != 0 else 0)
        print(f"{col:<25} {medias['treino']:>10.2f} {medias['val']:>10.2f} "
              f"{medias['teste']:>10.2f} {drift:>+11.1f}%")
        drift_data.append({"feature": col, **medias, "drift_%": drift})

    drift_df = pd.DataFrame(drift_data)

    fig = go.Figure()
    for split, cor in SPLIT_CORES.items():
        fig.add_trace(go.Bar(
            x=drift_df["feature"], y=drift_df[split],
            name=split.capitalize(), marker_color=cor,
            marker_line_color="black", marker_line_width=0.5,
        ))

    fig.update_layout(
        title=f"Comparacao de Medias entre Conjuntos — p{janela}",
        yaxis_title="Media da feature", height=500,
        barmode="group",
    )
    salvar_fig(fig, f"drift_features_p{janela}")

for janela in [2, 4]:
    df = dfs[f"treino_p{janela}"]

    bins = [0, 1995, 2000, 2005, 2010, 2015]
    labels = ["<1996", "1996-00", "2001-05", "2006-10", "2011-15"]
    df = df.copy()
    df["faixa"] = pd.cut(df["ano_ingresso"], bins=bins, labels=labels)

    ct = pd.crosstab(df["faixa"], df["y"])
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    faixas = ct_pct.index.tolist()
    totais = ct.sum(axis=1)

    fig = go.Figure()
    for y_val in [0, 1]:
        fig.add_trace(go.Bar(
            x=[str(f) for f in faixas], y=ct_pct[y_val].values,
            name=LABELS_ALVO[y_val], marker_color=CORES_ALVO[y_val],
            marker_line_color="black", marker_line_width=1,
            text=[f"{v:.1f}%" for v in ct_pct[y_val].values],
            textposition="inside",
        ))

    for j, (faixa, total) in enumerate(zip(faixas, totais)):
        fig.add_annotation(x=str(faixa), y=105, text=f"n={total}",
                           showarrow=False, font=dict(size=11))

    fig.update_layout(
        barmode="stack",
        title=f"Distribuicao do Alvo por Faixa de Ingresso — Treino p{janela}",
        yaxis_title="Percentual (%)", yaxis_range=[0, 115],
        height=500,
    )
    salvar_fig(fig, f"alvo_por_faixa_treino_p{janela}")

print("\nEDA 05 concluida.")
