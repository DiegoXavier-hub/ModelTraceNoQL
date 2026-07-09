from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]

CONFIGS = {
    "pt": {
        "out_dir": ROOT / "article" / "Images" / "plotly",
        "confusion_title": "Matriz de Confusao para Classificacao Binaria",
        "predicted_negative": "Previsto Negativo",
        "predicted_positive": "Previsto Positivo",
        "actual_negative": "Real Negativo",
        "actual_positive": "Real Positivo",
        "roc_model_title": "Exemplo de Curva ROC de um Modelo Preditivo",
        "roc_perfect_title": "Curva ROC de um Modelo Hipotetico Perfeito",
        "random": "Classificador aleatorio",
        "model_curve": "Curva ROC do modelo",
        "perfect_curve": "Curva ROC perfeita",
        "fpr": "Taxa de Falsos Positivos",
        "tpr": "Taxa de Verdadeiros Positivos",
    },
    "en": {
        "out_dir": ROOT / "article" / "Images" / "plotly_en",
        "confusion_title": "Confusion Matrix for Binary Classification",
        "predicted_negative": "Predicted Negative",
        "predicted_positive": "Predicted Positive",
        "actual_negative": "Actual Negative",
        "actual_positive": "Actual Positive",
        "roc_model_title": "Example ROC Curve from a Predictive Model",
        "roc_perfect_title": "ROC Curve of a Hypothetical Perfect Model",
        "random": "Random baseline",
        "model_curve": "Model ROC curve",
        "perfect_curve": "Perfect ROC curve",
        "fpr": "False Positive Rate",
        "tpr": "True Positive Rate",
    },
}


def save(fig: go.Figure, name: str, width: int, height: int, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(out_dir / f"{name}.png"), width=width, height=height, scale=2)
    fig.write_html(str(out_dir / f"{name}.html"), include_plotlyjs="cdn")
    print(f"Saved {out_dir.name}/{name}.png")


def confusion_matrix_example(labels: dict[str, str]) -> go.Figure:
    fig = go.Figure()
    cell_labels = [["TN", "FP"], ["FN", "TP"]]
    fills = [["#9474DC", "#D2B5FF"], ["#D2B5FF", "#9474DC"]]

    for row in range(2):
        for col in range(2):
            fig.add_shape(
                type="rect",
                x0=col - 0.5,
                x1=col + 0.5,
                y0=row - 0.5,
                y1=row + 0.5,
                fillcolor=fills[row][col],
                line=dict(color="white", width=2),
            )
            fig.add_annotation(
                x=col,
                y=row,
                text=f"<b>{cell_labels[row][col]}</b>",
                showarrow=False,
                font=dict(size=20, color="#1f2937"),
            )

    fig.update_layout(
        title=labels["confusion_title"],
        xaxis=dict(
            tickmode="array",
            tickvals=[0, 1],
            ticktext=[labels["predicted_negative"], labels["predicted_positive"]],
            range=[-0.7, 1.7],
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=[0, 1],
            ticktext=[labels["actual_negative"], labels["actual_positive"]],
            range=[1.7, -0.7],
            showgrid=False,
            zeroline=False,
        ),
        template="plotly_white",
        width=680,
        height=440,
        margin=dict(l=40, r=40, t=70, b=40),
    )
    return fig


def roc_example(labels: dict[str, str]) -> go.Figure:
    fig = go.Figure()
    fpr = [0.0, 0.05, 0.1, 0.18, 0.3, 0.5, 1.0]
    tpr = [0.0, 0.38, 0.56, 0.72, 0.83, 0.92, 1.0]

    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            line=dict(color="gray", dash="dash", width=1),
            name=labels["random"],
        )
    )
    fig.add_trace(
        go.Scatter(
            x=fpr,
            y=tpr,
            mode="lines+markers",
            line=dict(color="#9474DC", width=3),
            marker=dict(size=7),
            name=labels["model_curve"],
            fill="tozeroy",
            fillcolor="rgba(148, 116, 220, 0.15)",
        )
    )
    fig.update_layout(
        title=labels["roc_model_title"],
        xaxis_title=labels["fpr"],
        yaxis_title=labels["tpr"],
        template="plotly_white",
        width=900,
        height=500,
        legend=dict(x=0.58, y=0.1, bgcolor="rgba(255,255,255,0.85)"),
        margin=dict(l=60, r=40, t=70, b=60),
    )
    return fig


def roc_perfect(labels: dict[str, str]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            line=dict(color="gray", dash="dash", width=1),
            name=labels["random"],
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, 0, 1],
            y=[0, 1, 1],
            mode="lines+markers",
            line=dict(color="#9474DC", width=3),
            marker=dict(size=7),
            name=labels["perfect_curve"],
            fill="tozeroy",
            fillcolor="rgba(148, 116, 220, 0.15)",
        )
    )
    fig.update_layout(
        title=labels["roc_perfect_title"],
        xaxis_title=labels["fpr"],
        yaxis_title=labels["tpr"],
        template="plotly_white",
        width=900,
        height=500,
        legend=dict(x=0.55, y=0.1, bgcolor="rgba(255,255,255,0.85)"),
        margin=dict(l=60, r=40, t=70, b=60),
    )
    return fig


def generate_all() -> None:
    for labels in CONFIGS.values():
        out_dir = labels["out_dir"]
        save(confusion_matrix_example(labels), "plotly_matriz_confusao_explicacao", 680, 440, out_dir)
        save(roc_example(labels), "plotly_roc_explicacao_modelo", 900, 500, out_dir)
        save(roc_perfect(labels), "plotly_roc_explicacao_perfeita", 900, 500, out_dir)


if __name__ == "__main__":
    generate_all()
