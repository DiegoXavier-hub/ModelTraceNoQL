import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import mannwhitneyu, chi2_contingency, pointbiserialr
from eda_config import (DADOS, GRAFICOS, META_COLS, CAT_COLS,
                         CORES_ALVO, LABELS_ALVO,
                         ROXO_MEDIO, ROXO_CLARO, ROXO_ESCURO,
                         VERDE, VERMELHO, AZUL, LARANJA,
                         salvar_fig)

treino_p2 = pd.read_parquet(DADOS / "treino_p2.parquet")
treino_p4 = pd.read_parquet(DADOS / "treino_p4.parquet")
NUM_COLS = [c for c in treino_p2.columns if c not in META_COLS + CAT_COLS]

GRUPOS = {
    "Desempenho Academico": ["nota_media", "nota_mediana", "nota_desvio",
                              "nota_min", "nota_max"],
    "Aprovacoes e Reprovacoes": ["qtd_aprovacoes", "qtd_reprovacoes",
                                  "qtd_reprov_nota", "qtd_reprov_freq",
                                  "taxa_aprovacao"],
    "Carga de Trabalho": ["qtd_disciplinas_total", "media_disc_por_periodo",
                           "ch_acumulada", "pct_ch_concluida"],
    "Temporais": ["nota_p1", "delta_nota", "reprov_p1", "disc_p1"],
}

for grupo_nome, cols in GRUPOS.items():
    n = len(cols)
    fig = make_subplots(rows=1, cols=n, subplot_titles=cols,
                        horizontal_spacing=0.05)

    for i, col in enumerate(cols, 1):
        for y_val in [0, 1]:
            vals = treino_p2.loc[treino_p2["y"] == y_val, col].dropna()
            fig.add_trace(go.Violin(
                y=vals, name=LABELS_ALVO[y_val],
                marker_color=CORES_ALVO[y_val],
                box_visible=True, meanline_visible=True,
                legendgroup=str(y_val), showlegend=(i == 1),
                side="positive" if y_val == 0 else "negative",
                scalemode="width",
            ), row=1, col=i)

    fig.update_layout(
        title=f"Distribuicao por Alvo (p2) — {grupo_nome}",
        height=500, violinmode="overlay",
    )
    slug = grupo_nome.lower().replace(" ", "_").replace("(", "").replace(")", "")
    slug = slug.replace("á", "a").replace("ã", "a").replace("ç", "c").replace("õ", "o")
    salvar_fig(fig, f"violin_{slug}_p2")

for grupo_nome, cols in GRUPOS.items():
    n = len(cols)
    fig = make_subplots(rows=1, cols=n, subplot_titles=cols,
                        horizontal_spacing=0.05)

    for i, col in enumerate(cols, 1):
        for y_val in [0, 1]:
            vals = treino_p4.loc[treino_p4["y"] == y_val, col].dropna()
            fig.add_trace(go.Violin(
                y=vals, name=LABELS_ALVO[y_val],
                marker_color=CORES_ALVO[y_val],
                box_visible=True, meanline_visible=True,
                legendgroup=str(y_val), showlegend=(i == 1),
                side="positive" if y_val == 0 else "negative",
                scalemode="width",
            ), row=1, col=i)

    fig.update_layout(
        title=f"Distribuicao por Alvo (p4) — {grupo_nome}",
        height=500, violinmode="overlay",
    )
    slug = grupo_nome.lower().replace(" ", "_").replace("(", "").replace(")", "")
    slug = slug.replace("á", "a").replace("ã", "a").replace("ç", "c").replace("õ", "o")
    salvar_fig(fig, f"violin_{slug}_p4")

FEATURES_DESTAQUE = ["nota_media", "taxa_aprovacao", "qtd_reprovacoes",
                      "pct_ch_concluida", "nota_p1", "delta_nota"]

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    n = len(FEATURES_DESTAQUE)
    ncols = 3
    nrows = (n + ncols - 1) // ncols
    fig = make_subplots(rows=nrows, cols=ncols,
                        subplot_titles=FEATURES_DESTAQUE,
                        vertical_spacing=0.1,
                        horizontal_spacing=0.08)

    for idx, col in enumerate(FEATURES_DESTAQUE):
        r = idx // ncols + 1
        c = idx % ncols + 1
        for y_val in [0, 1]:
            vals = df.loc[df["y"] == y_val, col].dropna()
            fig.add_trace(go.Histogram(
                x=vals, nbinsx=50, histnorm="probability density",
                name=LABELS_ALVO[y_val], marker_color=CORES_ALVO[y_val],
                opacity=0.55,
                legendgroup=str(y_val), showlegend=(idx == 0),
            ), row=r, col=c)

    fig.update_layout(
        title=f"KDE Aproximado — Evadidos vs Nao-evadidos ({janela_nome})",
        height=350 * nrows, barmode="overlay",
    )
    salvar_fig(fig, f"kde_alvo_{janela_nome}")

print("\n" + "=" * 90)
print("TESTES ESTATISTICOS — FEATURES NUMERICAS vs ALVO (TREINO)")
print("=" * 90)

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    print(f"\n--- {janela_nome.upper()} ---")
    print(f"{'Feature':<25} {'Media y=0':>10} {'Media y=1':>10} {'Diff%':>8} "
          f"{'MW U-stat':>12} {'p-value':>12} {'r_pb':>8} {'Signif':>8}")
    print("-" * 90)

    resultados = []
    for col in NUM_COLS:
        g0 = df.loc[df["y"] == 0, col].dropna()
        g1 = df.loc[df["y"] == 1, col].dropna()

        if len(g0) < 2 or len(g1) < 2:
            continue

        m0, m1 = g0.mean(), g1.mean()
        diff_pct = ((m1 - m0) / m0 * 100) if m0 != 0 else float("inf")

        u_stat, p_val = mannwhitneyu(g0, g1, alternative="two-sided")

        mask = df[col].notna()
        if mask.sum() > 2:
            r_pb, _ = pointbiserialr(df.loc[mask, "y"], df.loc[mask, col])
        else:
            r_pb = np.nan

        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"

        print(f"{col:<25} {m0:>10.2f} {m1:>10.2f} {diff_pct:>+7.1f}% "
              f"{u_stat:>12,.0f} {p_val:>12.2e} {r_pb:>+8.3f} {sig:>8}")

        resultados.append({"feature": col, "r_pb": r_pb, "p_value": p_val,
                           "media_y0": m0, "media_y1": m1})

    resultados_df = pd.DataFrame(resultados).sort_values("r_pb", key=abs, ascending=False)
    print(f"\nRanking por |r_pb| ({janela_nome}):")
    for _, row in resultados_df.head(10).iterrows():
        print(f"  {row['feature']:<25} r_pb = {row['r_pb']:+.3f}")

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    resultados = []
    for col in NUM_COLS:
        mask = df[col].notna()
        if mask.sum() > 2:
            r_pb, p_val = pointbiserialr(df.loc[mask, "y"], df.loc[mask, col])
            resultados.append({"feature": col, "r_pb": r_pb, "p_value": p_val})

    res = pd.DataFrame(resultados).sort_values("r_pb")

    fig = go.Figure()
    colors = [VERMELHO if v > 0 else VERDE for v in res["r_pb"]]
    fig.add_trace(go.Bar(
        y=res["feature"], x=res["r_pb"], orientation="h",
        marker_color=colors, marker_line_color="black", marker_line_width=0.5,
        text=[f"{v:+.3f}" for v in res["r_pb"]], textposition="outside",
    ))
    fig.update_layout(
        title=f"Correlacao Ponto-Bisserial com Alvo — Treino {janela_nome}",
        xaxis_title="r_pb (positivo = associado a evasao)",
        height=500, xaxis_range=[-0.6, 0.6],
    )
    salvar_fig(fig, f"rpb_ranking_{janela_nome}")

print("\n" + "=" * 60)
print("TESTES CHI-QUADRADO — FEATURES CATEGORICAS vs ALVO")
print("=" * 60)

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    print(f"\n--- {janela_nome.upper()} ---")
    for cat_col in CAT_COLS:
        ct = pd.crosstab(df[cat_col], df["y"])
        chi2, p_val, dof, expected = chi2_contingency(ct)
        cramers_v = np.sqrt(chi2 / (ct.sum().sum() * (min(ct.shape) - 1)))
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        print(f"  {cat_col}: chi2={chi2:.1f}, p={p_val:.2e}, "
              f"Cramer's V={cramers_v:.3f} {sig}")

print("\nEDA 03 concluida.")
