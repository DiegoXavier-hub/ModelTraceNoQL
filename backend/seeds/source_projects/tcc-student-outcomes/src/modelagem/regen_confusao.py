"""Regenera apenas a figura fig_matrizes_confusao com P1+P2+P4."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config_modelagem import RESULTADOS

PROJETO = Path(__file__).resolve().parent.parent.parent
GRAFICOS_ARTIGO = PROJETO / "article" / "Images" / "artigo"
GRAFICOS_ARTIGO.mkdir(parents=True, exist_ok=True)

res_thr = pd.read_csv(RESULTADOS / "resultados_threshold_teste.csv")

config_cm = [(1, "CatBoost"), (2, "XGBoost"), (4, "CatBoost")]

subplot_titles = []
for janela, modelo_nome in config_cm:
    sub = res_thr[(res_thr["split"] == "teste") & (res_thr["modelo"] == modelo_nome)]
    thr_val = None
    for _, r in sub.iterrows():
        jv = r["janela"]
        j = int(jv[-1]) if isinstance(jv, str) else int(jv)
        if j == janela:
            thr_val = float(r["threshold"])
            break
    subplot_titles.append(f"{modelo_nome} p{janela} (thr={thr_val:.2f})")

fig = make_subplots(rows=1, cols=3, subplot_titles=subplot_titles,
                    horizontal_spacing=0.10)

COR_P = "#9474DC"
COR_S = "#D2B5FF"
cores_celula = [[COR_P, COR_S], [COR_S, COR_P]]

for col_idx, (janela, modelo_nome) in enumerate(config_cm, 1):
    sub = res_thr[(res_thr["split"] == "teste") & (res_thr["modelo"] == modelo_nome)]
    for _, r in sub.iterrows():
        jv = r["janela"]
        j = int(jv[-1]) if isinstance(jv, str) else int(jv)
        if j != janela:
            continue
        tn, fp, fn, tp = int(r["tn"]), int(r["fp"]), int(r["fn"]), int(r["tp"])
        break

    total = tn + fp + fn + tp
    labels = [["TN", "FP"], ["FN", "TP"]]
    vals = [[tn, fp], [fn, tp]]
    y_labels = ["Formado", "Evadido"]
    x_labels = ["Formado", "Evadido"]

    for row_i in range(2):
        for col_j in range(2):
            v = vals[row_i][col_j]
            fig.add_trace(go.Scatter(
                x=[x_labels[col_j]], y=[y_labels[row_i]],
                mode="text",
                text=[f"{labels[row_i][col_j]}<br><b>{v}</b><br>({v/total*100:.1f}%)"],
                textfont=dict(size=13, color="black"),
                showlegend=False,
            ), row=1, col=col_idx)
            fig.add_shape(
                type="rect",
                x0=col_j - 0.5, x1=col_j + 0.5,
                y0=row_i - 0.5, y1=row_i + 0.5,
                fillcolor=cores_celula[row_i][col_j],
                line=dict(color="white", width=2),
                layer="below",
                xref=f"x{col_idx}" if col_idx > 1 else "x",
                yref=f"y{col_idx}" if col_idx > 1 else "y",
            )

fig.update_layout(
    title="Matrizes de Confusao no Teste",
    height=420, width=1200,
    template="plotly_white",
)
for i in [1, 2, 3]:
    fig.update_xaxes(title_text="Previsto", row=1, col=i,
                     categoryorder="array", categoryarray=["Formado", "Evadido"],
                     showgrid=False, zeroline=False)
    fig.update_yaxes(title_text="Real", row=1, col=i,
                     categoryorder="array", categoryarray=["Formado", "Evadido"],
                     autorange="reversed", showgrid=False, zeroline=False)

fig.write_image(str(GRAFICOS_ARTIGO / "fig_matrizes_confusao.png"),
                width=1200, height=420, scale=2)
fig.write_html(str(GRAFICOS_ARTIGO / "fig_matrizes_confusao.html"),
               include_plotlyjs="cdn")
print(f"Salvo: {GRAFICOS_ARTIGO / 'fig_matrizes_confusao.png'}")
