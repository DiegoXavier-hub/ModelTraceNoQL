from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "data" / "preprocessamento"
OUT = ROOT / "article" / "Images" / "artigo_en"
SRC_ARTIGO = ROOT / "article" / "Images" / "artigo"
OUT.mkdir(parents=True, exist_ok=True)

ROXO_MEDIO = "#9474DC"
AZUL = "#3498DB"
LARANJA = "#F39C12"
VERDE = "#27AE60"
VERMELHO = "#E74C3C"
CINZA = "#95A5A6"

PROGRAM_LABELS = {
    "ADM_Integral": "Full-time Administration",
    "ADM_Noturno": "Evening Administration",
    "GI": "Information Management",
}

ENTRY_LABELS = {
    "Portador_Diploma": "Diploma Holder",
    "Outros": "Other",
    "SISU": "SISU",
    "Vestibular": "Entrance Exam",
    "Transferencia": "Transfer",
    "PAIES_PAAES": "PAIES/PAAES",
}


def save(fig: go.Figure, name: str, width: int, height: int) -> None:
    fig.write_image(str(OUT / f"{name}.png"), width=width, height=height, scale=2)
    fig.write_html(str(OUT / f"{name}.html"), include_plotlyjs="cdn")
    print(f"saved {name}.png")


def chi2_text(tab: pd.DataFrame) -> str:
    chi2, p, _, _ = stats.chi2_contingency(tab.values)
    n = tab.values.sum()
    cramer = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    return f"chi2={chi2:.2f}, p={p:.4f}, V_Cramer={cramer:.3f}"


def rate_by_group(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = df.groupby(col)["y"].agg(["count", "sum", "mean"]).reset_index()
    g.columns = [col, "n", "dropouts", "dropout_rate"]
    g["dropout_rate_pct"] = g["dropout_rate"] * 100
    return g


def generate_sociodemographic_figures() -> None:
    df = pd.read_parquet(DADOS / "ml_p1.parquet")

    cross = df.groupby(["curso_origem", "sexo"])["y"].agg(["count", "mean"]).reset_index()
    cross["rate_pct"] = cross["mean"] * 100
    cross["program_label"] = cross["curso_origem"].map(PROGRAM_LABELS)

    fig = go.Figure()
    for sex, color, label in [("M", AZUL, "Male"), ("F", ROXO_MEDIO, "Female")]:
        sub = cross[cross["sexo"] == sex]
        fig.add_trace(go.Bar(
            name=label,
            x=sub["program_label"],
            y=sub["rate_pct"],
            marker_color=color,
            text=[f"{v:.1f}%" for v in sub["rate_pct"]],
            textposition="outside",
        ))
    fig.update_layout(
        title="Dropout Rate by Program and Gender",
        yaxis_title="Dropout Rate (%)",
        yaxis=dict(range=[0, 100]),
        barmode="group",
        template="plotly_white",
        height=480,
        width=820,
    )
    save(fig, "fig_evasao_por_curso_sexo", 820, 480)

    df_id = df.dropna(subset=["idade_ingresso"]).copy()
    df_id["age_group"] = pd.cut(
        df_id["idade_ingresso"],
        bins=[0, 18, 20, 25, 30, 100],
        labels=["<=18", "19-20", "21-25", "26-30", ">30"],
    )
    g_id = rate_by_group(df_id, "age_group")
    age_dropout = df_id[df_id["y"] == 1]["idade_ingresso"]
    age_grad = df_id[df_id["y"] == 0]["idade_ingresso"]
    t_stat, p_t = stats.ttest_ind(age_dropout, age_grad, equal_var=False)

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Age at Enrollment Distribution", "Dropout Rate by Age Group"],
    )
    fig.add_trace(go.Histogram(
        x=age_grad,
        name="Graduates",
        marker_color=VERDE,
        opacity=0.65,
        nbinsx=40,
    ), row=1, col=1)
    fig.add_trace(go.Histogram(
        x=age_dropout,
        name="Dropouts",
        marker_color=VERMELHO,
        opacity=0.65,
        nbinsx=40,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=g_id["age_group"].astype(str),
        y=g_id["dropout_rate_pct"],
        marker_color=ROXO_MEDIO,
        text=[f"{v:.1f}%<br>(n={int(n)})" for v, n in zip(g_id["dropout_rate_pct"], g_id["n"])],
        textposition="outside",
        showlegend=False,
    ), row=1, col=2)
    fig.update_layout(
        title=f"Age at Enrollment vs Dropout (t={t_stat:.2f}, p={p_t:.4f})",
        barmode="overlay",
        template="plotly_white",
        height=460,
        width=1000,
    )
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    fig.update_xaxes(title_text="Age (years)", row=1, col=1)
    fig.update_yaxes(title_text="Dropout Rate (%)", row=1, col=2, range=[0, 100])
    save(fig, "fig_idade_vs_evasao", 1000, 460)

    df_birth = df.dropna(subset=["natural_uberlandia"]).copy()
    g_quota = rate_by_group(df, "cotista").sort_values("cotista")
    g_birth = rate_by_group(df_birth, "natural_uberlandia").sort_values("natural_uberlandia")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Quota Status", "Born in Uberlandia"],
    )
    fig.add_trace(go.Bar(
        x=["Non-quota", "Quota"],
        y=g_quota["dropout_rate_pct"],
        marker_color=[CINZA, LARANJA],
        text=[f"{v:.1f}%" for v in g_quota["dropout_rate_pct"]],
        textposition="outside",
        showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=["Not Uberlandia", "Uberlandia"],
        y=g_birth["dropout_rate_pct"],
        marker_color=[CINZA, ROXO_MEDIO],
        text=[f"{v:.1f}%" for v in g_birth["dropout_rate_pct"]],
        textposition="outside",
        showlegend=False,
    ), row=1, col=2)
    fig.update_layout(
        title="Dropout by Quota Status and Place of Birth",
        template="plotly_white",
        height=440,
        width=820,
    )
    fig.update_yaxes(range=[0, 80], title_text="Dropout Rate (%)")
    save(fig, "fig_cotista_naturalidade", 820, 440)

    g_entry = rate_by_group(df, "forma_ingresso_grp").sort_values("dropout_rate_pct", ascending=False)
    g_entry["entry_label"] = g_entry["forma_ingresso_grp"].map(ENTRY_LABELS).fillna(g_entry["forma_ingresso_grp"])
    tab = pd.crosstab(df["forma_ingresso_grp"], df["y"])

    fig = go.Figure(go.Bar(
        x=g_entry["entry_label"],
        y=g_entry["dropout_rate_pct"],
        marker_color=ROXO_MEDIO,
        text=[f"{v:.1f}%<br>(n={int(n)})" for v, n in zip(g_entry["dropout_rate_pct"], g_entry["n"])],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Dropout Rate by Entry Route ({chi2_text(tab)})",
        yaxis_title="Dropout Rate (%)",
        yaxis=dict(range=[0, 100]),
        template="plotly_white",
        height=480,
        width=900,
    )
    save(fig, "fig_forma_ingresso", 900, 480)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def patch_beeswarm_titles() -> None:
    title_font = _font(30)
    for window in [1, 2, 4]:
        src = SRC_ARTIGO / f"fig_shap_beeswarm_p{window}.png"
        dst = OUT / f"fig_shap_beeswarm_p{window}.png"

        image = Image.open(src).convert("RGBA")
        draw = ImageDraw.Draw(image)
        rect_height = 115
        draw.rectangle([(350, 0), (image.width - 240, rect_height)], fill="white")
        title = f"SHAP Beeswarm -- CatBoost (Test p{window})"
        draw.text((image.width // 2, 28), title, fill="black", font=title_font, anchor="ma")
        image.save(dst)
        print(f"saved {dst.name}")


def main() -> None:
    generate_sociodemographic_figures()
    patch_beeswarm_titles()


if __name__ == "__main__":
    main()
