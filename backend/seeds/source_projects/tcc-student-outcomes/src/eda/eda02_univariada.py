import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats as sp_stats
from eda_config import (DADOS, GRAFICOS, META_COLS, CAT_COLS,
                         ROXO_MEDIO, ROXO_CLARO, ROXO_ESCURO, ROXO_BG,
                         VERDE, VERMELHO, LARANJA, CINZA,
                         salvar_fig)

treino_p2 = pd.read_parquet(DADOS / "treino_p2.parquet")
treino_p4 = pd.read_parquet(DADOS / "treino_p4.parquet")
NUM_COLS = [c for c in treino_p2.columns if c not in META_COLS + CAT_COLS]

print(f"Features numericas ({len(NUM_COLS)}): {NUM_COLS}")

GRUPOS = {
    "Desempenho Academico": ["nota_media", "nota_mediana", "nota_desvio",
                              "nota_min", "nota_max"],
    "Aprovacoes e Reprovacoes": ["qtd_aprovacoes", "qtd_reprovacoes", "qtd_dispensas",
                                  "qtd_sem_resultado", "qtd_reprov_nota",
                                  "qtd_reprov_freq", "taxa_aprovacao"],
    "Carga de Trabalho": ["qtd_disciplinas_total", "media_disc_por_periodo",
                           "ch_acumulada", "pct_ch_concluida"],
    "Temporais (1o periodo)": ["nota_p1", "delta_nota", "reprov_p1", "disc_p1"],
}

for grupo_nome, cols in GRUPOS.items():
    n = len(cols)
    fig = make_subplots(rows=n, cols=2,
                        subplot_titles=[f"{c} (p2)" if j == 0 else f"{c} (p4)"
                                        for c in cols for j in range(2)],
                        vertical_spacing=0.04,
                        horizontal_spacing=0.08)

    for i, col in enumerate(cols, 1):
        for j, (nome, df) in enumerate([("p2", treino_p2), ("p4", treino_p4)], 1):
            vals = df[col].dropna()
            fig.add_trace(go.Histogram(
                x=vals, nbinsx=40,
                marker_color=ROXO_MEDIO if j == 1 else ROXO_CLARO,
                marker_line_color=ROXO_ESCURO, marker_line_width=0.5,
                opacity=0.85, showlegend=False,
            ), row=i, col=j)

            med = vals.median()
            fig.add_vline(x=med, line_dash="dash", line_color=VERMELHO,
                          line_width=1.5, row=i, col=j,
                          annotation_text=f"med={med:.1f}",
                          annotation_font_size=9,
                          annotation_position="top right")

    fig.update_layout(
        title=f"Distribuicoes — {grupo_nome}",
        height=280 * n, showlegend=False,
    )
    slug = grupo_nome.lower().replace(" ", "_").replace("(", "").replace(")", "")
    slug = slug.replace("á", "a").replace("ã", "a").replace("ç", "c").replace("õ", "o")
    salvar_fig(fig, f"hist_{slug}")

for grupo_nome, cols in GRUPOS.items():
    n = len(cols)
    fig = make_subplots(rows=1, cols=n,
                        subplot_titles=cols,
                        horizontal_spacing=0.05)

    for i, col in enumerate(cols, 1):
        for nome, df, cor in [("p2", treino_p2, ROXO_MEDIO),
                               ("p4", treino_p4, ROXO_CLARO)]:
            vals = df[col].dropna()
            fig.add_trace(go.Box(
                y=vals, name=nome,
                marker_color=cor, line_color=ROXO_ESCURO,
                boxmean="sd",
                legendgroup=nome, showlegend=(i == 1),
            ), row=1, col=i)

    fig.update_layout(
        title=f"Boxplots — {grupo_nome}",
        height=500, boxmode="group",
    )
    slug = grupo_nome.lower().replace(" ", "_").replace("(", "").replace(")", "")
    slug = slug.replace("á", "a").replace("ã", "a").replace("ç", "c").replace("õ", "o")
    salvar_fig(fig, f"box_{slug}")

print("\n" + "=" * 70)
print("ESTATISTICAS DE FORMA — TREINO P2")
print("=" * 70)
print(f"{'Feature':<25} {'Skewness':>10} {'Kurtosis':>10} {'Interpretacao'}")
print("-" * 70)

for col in NUM_COLS:
    vals = treino_p2[col].dropna()
    skew = vals.skew()
    kurt = vals.kurtosis()
    interp = []
    if abs(skew) > 1:
        interp.append("muito assimetrica")
    elif abs(skew) > 0.5:
        interp.append("assimetria moderada")
    if kurt > 3:
        interp.append("leptocurtica (caudas pesadas)")
    elif kurt < -1:
        interp.append("platicurtica")
    print(f"{col:<25} {skew:>10.2f} {kurt:>10.2f}  {', '.join(interp) if interp else 'aprox. normal'}")

for cat_col in CAT_COLS:
    fig = make_subplots(rows=1, cols=2, subplot_titles=["Treino p2", "Treino p4"])

    for i, (nome, df) in enumerate([("p2", treino_p2), ("p4", treino_p4)], 1):
        counts = df[cat_col].value_counts().sort_index()
        pcts = (counts / counts.sum() * 100).round(1)
        text = [f"{v:,} ({p}%)" for v, p in zip(counts.values, pcts.values)]

        cores = [ROXO_MEDIO, ROXO_CLARO, ROXO_ESCURO][:len(counts)]
        fig.add_trace(go.Bar(
            x=counts.index.tolist(), y=counts.values,
            text=text, textposition="outside",
            marker_color=cores,
            marker_line_color="black", marker_line_width=1,
            showlegend=False,
        ), row=1, col=i)
        fig.update_yaxes(range=[0, counts.max() * 1.3], row=1, col=i)

    fig.update_layout(title=f"Distribuicao de {cat_col} — Treino",
                      height=450, yaxis_title="Quantidade")
    salvar_fig(fig, f"cat_{cat_col}")

print("\nEDA 02 concluida.")
