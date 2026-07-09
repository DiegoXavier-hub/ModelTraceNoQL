import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from eda_config import (DADOS, GRAFICOS, META_COLS, CAT_COLS,
                         CORES_ALVO, LABELS_ALVO, CORES_CURSO,
                         ROXO_MEDIO, ROXO_CLARO, VERDE, VERMELHO, CINZA,
                         salvar_fig)

treino_p2 = pd.read_parquet(DADOS / "treino_p2.parquet")
treino_p4 = pd.read_parquet(DADOS / "treino_p4.parquet")
NUM_COLS = [c for c in treino_p2.columns if c not in META_COLS + CAT_COLS]

print(f"Treino p2: {len(treino_p2):,} alunos, {len(treino_p2.columns)} colunas")
print(f"Treino p4: {len(treino_p4):,} alunos, {len(treino_p4.columns)} colunas")
print(f"\nFeatures numericas ({len(NUM_COLS)}): {NUM_COLS}")
print(f"Features categoricas ({len(CAT_COLS)}): {CAT_COLS}")

for nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    print(f"\n{'='*60}")
    print(f"ESTATISTICAS DESCRITIVAS — TREINO {nome.upper()} ({len(df):,} alunos)")
    print(f"{'='*60}")
    desc = df[NUM_COLS].describe().T
    desc["nulos"] = df[NUM_COLS].isnull().sum()
    desc["nulos_%"] = (desc["nulos"] / len(df) * 100).round(1)
    print(desc.round(2).to_string())

fig = make_subplots(rows=1, cols=2, subplot_titles=["Treino p2", "Treino p4"])

for i, (nome, df) in enumerate([("p2", treino_p2), ("p4", treino_p4)], 1):
    counts = df["y"].value_counts().sort_index()
    labels = [LABELS_ALVO[k] for k in counts.index]
    colors = [CORES_ALVO[k] for k in counts.index]
    pcts = (counts / counts.sum() * 100).round(1)
    text = [f"{v:,}<br>({p}%)" for v, p in zip(counts.values, pcts.values)]

    fig.add_trace(go.Bar(
        x=labels, y=counts.values, text=text, textposition="outside",
        marker_color=colors, marker_line_color="black", marker_line_width=1,
        showlegend=False,
    ), row=1, col=i)
    fig.update_yaxes(range=[0, counts.max() * 1.25], row=1, col=i)

fig.update_layout(title="Distribuicao da Variavel Alvo (y) — Conjunto de Treino",
                  height=500, yaxis_title="Quantidade de alunos")
salvar_fig(fig, "alvo_distribuicao_geral")

fig = make_subplots(rows=1, cols=2, subplot_titles=["Treino p2", "Treino p4"])

for i, (nome, df) in enumerate([("p2", treino_p2), ("p4", treino_p4)], 1):
    ct = pd.crosstab(df["curso_origem"], df["y"])
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    cursos = ct.index.tolist()
    totais = ct.sum(axis=1)

    for y_val in [0, 1]:
        fig.add_trace(go.Bar(
            x=cursos, y=ct_pct[y_val].values,
            name=LABELS_ALVO[y_val], marker_color=CORES_ALVO[y_val],
            marker_line_color="black", marker_line_width=1,
            text=[f"{v:.1f}%" for v in ct_pct[y_val].values],
            textposition="inside",
            legendgroup=str(y_val), showlegend=(i == 1),
        ), row=1, col=i)

    for j, (curso, total) in enumerate(zip(cursos, totais)):
        fig.add_annotation(
            x=curso, y=105, text=f"n={total}", showarrow=False,
            font=dict(size=11, color="black"), row=1, col=i)

fig.update_layout(barmode="stack", title="Taxa de Evasao por Curso — Treino",
                  height=500, yaxis_title="Percentual (%)")
fig.update_yaxes(range=[0, 115])
salvar_fig(fig, "alvo_por_curso")

fig = make_subplots(rows=1, cols=2, subplot_titles=["Treino p2", "Treino p4"])

for i, (nome, df) in enumerate([("p2", treino_p2), ("p4", treino_p4)], 1):
    ct = pd.crosstab(df["tipo_ingresso"], df["y"])
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    ct_pct = ct_pct.sort_values(1, ascending=True)
    tipos = ct_pct.index.tolist()
    totais = ct.loc[tipos].sum(axis=1)

    for y_val in [0, 1]:
        fig.add_trace(go.Bar(
            y=tipos, x=ct_pct[y_val].values, orientation="h",
            name=LABELS_ALVO[y_val], marker_color=CORES_ALVO[y_val],
            marker_line_color="black", marker_line_width=1,
            text=[f"{v:.1f}%" for v in ct_pct[y_val].values],
            textposition="inside",
            legendgroup=str(y_val), showlegend=(i == 1),
        ), row=1, col=i)

    for j, (tipo, total) in enumerate(zip(tipos, totais)):
        fig.add_annotation(
            y=tipo, x=105, text=f"n={total}", showarrow=False,
            font=dict(size=10), row=1, col=i)

fig.update_layout(barmode="stack", title="Taxa de Evasao por Tipo de Ingresso — Treino",
                  height=450, xaxis_title="Percentual (%)")
fig.update_xaxes(range=[0, 115])
salvar_fig(fig, "alvo_por_tipo_ingresso")

print("\n" + "=" * 60)
print("VALORES FALTANTES")
print("=" * 60)

for nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    print(f"\n--- Treino {nome} ---")
    nulos = df[NUM_COLS].isnull().sum()
    nulos = nulos[nulos > 0]
    if len(nulos) > 0:
        for col, n in nulos.items():
            null_mask = df[col].isnull()
            taxa_ev = null_mask[df["y"] == 1].mean() * 100
            taxa_nev = null_mask[df["y"] == 0].mean() * 100
            print(f"  {col}: {n} nulos ({n/len(df)*100:.1f}%)"
                  f" | evadidos={taxa_ev:.1f}% vs nao-evadidos={taxa_nev:.1f}%")
    else:
        print("  Nenhum")

nulos_p2 = treino_p2[NUM_COLS].isnull().sum()
nulos_p2 = nulos_p2[nulos_p2 > 0].sort_values(ascending=True)

if len(nulos_p2) > 0:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=nulos_p2.index, x=nulos_p2.values, orientation="h",
        marker_color=ROXO_MEDIO, marker_line_color="black", marker_line_width=1,
        text=[f"{v} ({v/len(treino_p2)*100:.1f}%)" for v in nulos_p2.values],
        textposition="outside",
    ))
    fig.update_layout(title="Valores Faltantes por Feature — Treino p2",
                      xaxis_title="Quantidade de nulos", height=400)
    salvar_fig(fig, "nulos_por_feature_p2")

print("\nEDA 01 concluida.")
