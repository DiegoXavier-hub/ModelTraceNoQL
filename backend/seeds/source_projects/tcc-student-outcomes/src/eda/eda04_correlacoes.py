import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from eda_config import (DADOS, GRAFICOS, META_COLS, CAT_COLS,
                         ROXO_MEDIO, ROXO_CLARO, ROXO_ESCURO, ROXO_BG,
                         VERMELHO, VERDE,
                         salvar_fig)

treino_p2 = pd.read_parquet(DADOS / "treino_p2.parquet")
treino_p4 = pd.read_parquet(DADOS / "treino_p4.parquet")
NUM_COLS = [c for c in treino_p2.columns if c not in META_COLS + CAT_COLS]

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    corr = df[NUM_COLS].corr()

    colorscale = [
        [0.0, VERDE],
        [0.5, "#FFFFFF"],
        [1.0, ROXO_MEDIO],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale=colorscale,
        zmin=-1, zmax=1,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=8),
        colorbar_title="r",
    ))
    fig.update_layout(
        title=f"Matriz de Correlacao (Pearson) — Treino {janela_nome}",
        height=700, width=800,
        xaxis_tickangle=-45,
    )
    salvar_fig(fig, f"corr_heatmap_{janela_nome}", width=900, height=800)

THRESHOLD = 0.7

print("\n" + "=" * 70)
print(f"PARES COM |r| > {THRESHOLD}")
print("=" * 70)

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    corr = df[NUM_COLS].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    pares = []
    for i in range(len(corr)):
        for j in range(i + 1, len(corr)):
            r = corr.iloc[i, j]
            if abs(r) > THRESHOLD:
                pares.append((corr.index[i], corr.columns[j], r))

    pares.sort(key=lambda x: abs(x[2]), reverse=True)

    print(f"\n--- {janela_nome.upper()} ({len(pares)} pares) ---")
    for f1, f2, r in pares:
        print(f"  {f1:<25} x {f2:<25} r = {r:+.3f}")

    if pares:
        labels = [f"{f1} x {f2}" for f1, f2, r in pares]
        values = [r for _, _, r in pares]
        colors = [ROXO_MEDIO if r > 0 else VERDE for r in values]

        fig = go.Figure(go.Bar(
            y=labels, x=values, orientation="h",
            marker_color=colors,
            marker_line_color="black", marker_line_width=0.5,
            text=[f"{v:+.3f}" for v in values], textposition="outside",
        ))
        fig.update_layout(
            title=f"Pares com |r| > {THRESHOLD} — Treino {janela_nome}",
            xaxis_title="Correlacao (r)",
            height=max(350, 40 * len(pares)),
            xaxis_range=[-1.1, 1.1],
        )
        salvar_fig(fig, f"pares_alta_corr_{janela_nome}")

from numpy.linalg import LinAlgError

def calcular_vif(df, cols):
    """Calcula VIF para cada feature. Usa pseudoinversa se singular."""
    X = df[cols].dropna()
    X_std = (X - X.mean()) / X.std()
    X_std = X_std.fillna(0)

    vifs = {}
    for i, col in enumerate(cols):
        y_col = X_std[col].values
        X_rest = X_std.drop(columns=[col]).values

        try:
            beta = np.linalg.lstsq(X_rest, y_col, rcond=None)[0]
            y_pred = X_rest @ beta
            ss_res = np.sum((y_col - y_pred) ** 2)
            ss_tot = np.sum((y_col - y_col.mean()) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            vif = 1 / (1 - r2) if r2 < 1 else float("inf")
        except Exception:
            vif = float("inf")

        vifs[col] = round(vif, 1)

    return pd.Series(vifs).sort_values(ascending=False)

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    print(f"\n--- VIF — Treino {janela_nome} ---")
    vif = calcular_vif(df, NUM_COLS)
    for col, v in vif.items():
        flag = " *** SEVERA" if v > 10 else " ** MODERADA" if v > 5 else ""
        print(f"  {col:<25} VIF = {v:>8.1f}{flag}")

    vif_sorted = vif.sort_values()
    colors = []
    for v in vif_sorted.values:
        if v > 10:
            colors.append(VERMELHO)
        elif v > 5:
            colors.append("#E67E22")
        else:
            colors.append(ROXO_MEDIO)

    fig = go.Figure(go.Bar(
        y=vif_sorted.index.tolist(), x=vif_sorted.values, orientation="h",
        marker_color=colors,
        marker_line_color="black", marker_line_width=0.5,
        text=[f"{v:.1f}" for v in vif_sorted.values], textposition="outside",
    ))
    fig.add_vline(x=5, line_dash="dash", line_color="#E67E22", line_width=1.5,
                  annotation_text="VIF=5", annotation_position="top right")
    fig.add_vline(x=10, line_dash="dash", line_color=VERMELHO, line_width=1.5,
                  annotation_text="VIF=10", annotation_position="top right")
    fig.update_layout(
        title=f"Variance Inflation Factor (VIF) — Treino {janela_nome}",
        xaxis_title="VIF", height=550,
    )
    salvar_fig(fig, f"vif_{janela_nome}")

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    corr_with_y = df[NUM_COLS + ["y"]].corr()["y"].drop("y").sort_values()

    fig = go.Figure(go.Bar(
        y=corr_with_y.index.tolist(), x=corr_with_y.values, orientation="h",
        marker_color=[VERMELHO if v > 0 else VERDE for v in corr_with_y.values],
        marker_line_color="black", marker_line_width=0.5,
        text=[f"{v:+.3f}" for v in corr_with_y.values], textposition="outside",
    ))
    fig.update_layout(
        title=f"Correlacao Pearson com Alvo (y) — Treino {janela_nome}",
        xaxis_title="r (positivo = associado a evasao)",
        height=550, xaxis_range=[-0.6, 0.6],
    )
    salvar_fig(fig, f"corr_com_alvo_{janela_nome}")

print("\nEDA 04 concluida.")
