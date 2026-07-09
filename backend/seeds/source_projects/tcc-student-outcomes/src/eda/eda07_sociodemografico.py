"""
EDA sociodemográfica complementar.

Analisa associação entre variáveis sociodemográficas (sexo, idade, cotista,
naturalidade, forma de ingresso) e o desfecho de evasão. Gera figuras Plotly
e tabelas (CSV) para inclusão no artigo.

Base: ml_p1.parquet (5.330 alunos com desfecho terminal — máximo de cobertura
sociodemográfica antes de qualquer filtro de coorte acadêmica).

Output:
- 04_analise_exploratoria_descritiva_completa/graficos/13_*.png/.html
- 04_analise_exploratoria_descritiva_completa/graficos/sociodemografico_resumo.csv
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

DADOS = Path(__file__).resolve().parent.parent.parent / "data" / "preprocessamento"
GRAFICOS = Path(__file__).resolve().parent / "graficos"
GRAFICOS.mkdir(parents=True, exist_ok=True)

ROXO_ESCURO = "#7B68AE"
ROXO_MEDIO = "#9474DC"
ROXO_CLARO = "#D2B5FF"
AZUL = "#3498DB"
LARANJA = "#F39C12"
VERDE = "#27AE60"
VERMELHO = "#E74C3C"
CINZA = "#95A5A6"


def salvar(fig: go.Figure, nome: str, w: int = 900, h: int = 520) -> None:
    fig.write_image(str(GRAFICOS / f"{nome}.png"), width=w, height=h, scale=2)
    fig.write_html(str(GRAFICOS / f"{nome}.html"), include_plotlyjs="cdn")
    print(f"  salvo: {nome}.png")


def chi2_str(tab: pd.DataFrame) -> str:
    chi2, p, dof, _ = stats.chi2_contingency(tab.values)
    n = tab.values.sum()
    cramer = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    return f"chi2={chi2:.2f}, p={p:.4f}, V_Cramer={cramer:.3f}"


def taxa_por_grupo(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = df.groupby(col)["y"].agg(["count", "sum", "mean"]).reset_index()
    g.columns = [col, "n", "evadidos", "taxa_evasao"]
    g["taxa_evasao_pct"] = g["taxa_evasao"] * 100
    return g


def main() -> None:
    df = pd.read_parquet(DADOS / "ml_p1.parquet")
    print(f"Base: ml_p1 -- {df.shape[0]} alunos")

    resumo: list[dict] = []

    print("\n--- SEXO ---")
    g = taxa_por_grupo(df, "sexo")
    print(g.to_string(index=False))
    tab = pd.crosstab(df["sexo"], df["y"])
    print(chi2_str(tab))
    for _, r in g.iterrows():
        resumo.append({"variavel": "sexo", "categoria": r["sexo"], "n": int(r["n"]),
                       "evadidos": int(r["evadidos"]), "taxa_evasao_pct": round(r["taxa_evasao_pct"], 2)})

    fig = go.Figure()
    cores_sexo = {"M": AZUL, "F": ROXO_MEDIO}
    for _, r in g.iterrows():
        fig.add_trace(go.Bar(
            x=[f"{r['sexo']}<br>n={int(r['n'])}"],
            y=[r["taxa_evasao_pct"]],
            marker_color=cores_sexo[r["sexo"]],
            text=f"{r['taxa_evasao_pct']:.1f}%",
            textposition="outside",
            showlegend=False,
        ))
    fig.update_layout(
        title=f"Taxa de Evasão por Sexo ({chi2_str(tab)})",
        yaxis_title="Taxa de Evasão (%)",
        yaxis=dict(range=[0, max(g['taxa_evasao_pct']) * 1.2]),
        template="plotly_white", height=450, width=700,
    )
    salvar(fig, "13_evasao_por_sexo", w=700, h=450)

    print("\n--- SEXO x CURSO ---")
    cross = df.groupby(["curso_origem", "sexo"])["y"].agg(["count", "mean"]).reset_index()
    cross["taxa_pct"] = cross["mean"] * 100
    print(cross.to_string(index=False))
    fig = go.Figure()
    for sx, cor in cores_sexo.items():
        sub = cross[cross["sexo"] == sx]
        fig.add_trace(go.Bar(
            name=f"Sexo {sx}",
            x=sub["curso_origem"],
            y=sub["taxa_pct"],
            marker_color=cor,
            text=[f"{v:.1f}%" for v in sub["taxa_pct"]],
            textposition="outside",
        ))
    fig.update_layout(
        title="Taxa de Evasão por Curso e Sexo",
        yaxis_title="Taxa de Evasão (%)",
        yaxis=dict(range=[0, 100]),
        barmode="group",
        template="plotly_white", height=480, width=820,
    )
    salvar(fig, "14_evasao_por_curso_sexo", w=820, h=480)

    print("\n--- IDADE ---")
    df_id = df.dropna(subset=["idade_ingresso"]).copy()
    df_id["faixa_idade"] = pd.cut(
        df_id["idade_ingresso"],
        bins=[0, 18, 20, 25, 30, 100],
        labels=["<=18", "19-20", "21-25", "26-30", ">30"],
    )
    g_id = taxa_por_grupo(df_id, "faixa_idade")
    print(g_id.to_string(index=False))
    tab = pd.crosstab(df_id["faixa_idade"], df_id["y"])
    print(chi2_str(tab))
    for _, r in g_id.iterrows():
        resumo.append({"variavel": "faixa_idade", "categoria": str(r["faixa_idade"]),
                       "n": int(r["n"]), "evadidos": int(r["evadidos"]),
                       "taxa_evasao_pct": round(r["taxa_evasao_pct"], 2)})

    idade_evad = df_id[df_id["y"] == 1]["idade_ingresso"]
    idade_form = df_id[df_id["y"] == 0]["idade_ingresso"]
    t_stat, p_t = stats.ttest_ind(idade_evad, idade_form, equal_var=False)
    print(f"Idade media -- evadidos: {idade_evad.mean():.2f} ({idade_evad.std():.2f})")
    print(f"Idade media -- formados: {idade_form.mean():.2f} ({idade_form.std():.2f})")
    print(f"Welch t-test: t={t_stat:.3f}, p={p_t:.4f}")

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["Distribuição da idade no ingresso",
                                        "Taxa de evasão por faixa etária"])
    fig.add_trace(go.Histogram(
        x=idade_form, name="Formados", marker_color=VERDE, opacity=0.65, nbinsx=40,
    ), row=1, col=1)
    fig.add_trace(go.Histogram(
        x=idade_evad, name="Evadidos", marker_color=VERMELHO, opacity=0.65, nbinsx=40,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=g_id["faixa_idade"].astype(str),
        y=g_id["taxa_evasao_pct"],
        marker_color=ROXO_MEDIO,
        text=[f"{v:.1f}%<br>(n={int(n)})" for v, n in zip(g_id['taxa_evasao_pct'], g_id['n'])],
        textposition="outside",
        showlegend=False,
    ), row=1, col=2)
    fig.update_layout(
        title=f"Idade no ingresso vs evasão (t={t_stat:.2f}, p={p_t:.4f})",
        barmode="overlay",
        template="plotly_white", height=460, width=1000,
    )
    fig.update_yaxes(title_text="Frequência", row=1, col=1)
    fig.update_xaxes(title_text="Idade (anos)", row=1, col=1)
    fig.update_yaxes(title_text="Taxa evasão (%)", row=1, col=2, range=[0, 100])
    salvar(fig, "15_idade_vs_evasao", w=1000, h=460)

    print("\n--- COTISTA ---")
    g = taxa_por_grupo(df, "cotista")
    print(g.to_string(index=False))
    tab = pd.crosstab(df["cotista"], df["y"])
    print(chi2_str(tab))
    for _, r in g.iterrows():
        resumo.append({"variavel": "cotista", "categoria": "sim" if r["cotista"] else "nao",
                       "n": int(r["n"]), "evadidos": int(r["evadidos"]),
                       "taxa_evasao_pct": round(r["taxa_evasao_pct"], 2)})

    print("\n--- NATURAL DE UBERLANDIA ---")
    df_nu = df.dropna(subset=["natural_uberlandia"])
    g = taxa_por_grupo(df_nu, "natural_uberlandia")
    print(g.to_string(index=False))
    tab = pd.crosstab(df_nu["natural_uberlandia"], df_nu["y"])
    print(chi2_str(tab))
    for _, r in g.iterrows():
        resumo.append({"variavel": "natural_uberlandia",
                       "categoria": "sim" if r["natural_uberlandia"] else "nao",
                       "n": int(r["n"]), "evadidos": int(r["evadidos"]),
                       "taxa_evasao_pct": round(r["taxa_evasao_pct"], 2)})

    g_cot = taxa_por_grupo(df, "cotista")
    g_nat = taxa_por_grupo(df_nu, "natural_uberlandia")
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["Cotista", "Natural de Uberlândia"])
    fig.add_trace(go.Bar(
        x=["Não cotista", "Cotista"],
        y=g_cot.sort_values("cotista")["taxa_evasao_pct"],
        marker_color=[CINZA, LARANJA],
        text=[f"{v:.1f}%" for v in g_cot.sort_values("cotista")["taxa_evasao_pct"]],
        textposition="outside",
        showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=["Não Uberlândia", "Uberlândia"],
        y=g_nat.sort_values("natural_uberlandia")["taxa_evasao_pct"],
        marker_color=[CINZA, ROXO_MEDIO],
        text=[f"{v:.1f}%" for v in g_nat.sort_values("natural_uberlandia")["taxa_evasao_pct"]],
        textposition="outside",
        showlegend=False,
    ), row=1, col=2)
    fig.update_layout(
        title="Evasão por situação de cota e naturalidade",
        template="plotly_white", height=440, width=820,
    )
    fig.update_yaxes(range=[0, 80], title_text="Taxa de evasão (%)")
    salvar(fig, "16_cotista_naturalidade", w=820, h=440)

    print("\n--- FORMA DE INGRESSO AGRUPADA ---")
    g = taxa_por_grupo(df, "forma_ingresso_grp")
    g = g.sort_values("taxa_evasao_pct", ascending=False)
    print(g.to_string(index=False))
    tab = pd.crosstab(df["forma_ingresso_grp"], df["y"])
    print(chi2_str(tab))
    for _, r in g.iterrows():
        resumo.append({"variavel": "forma_ingresso_grp", "categoria": str(r["forma_ingresso_grp"]),
                       "n": int(r["n"]), "evadidos": int(r["evadidos"]),
                       "taxa_evasao_pct": round(r["taxa_evasao_pct"], 2)})

    fig = go.Figure(go.Bar(
        x=g["forma_ingresso_grp"],
        y=g["taxa_evasao_pct"],
        marker_color=ROXO_MEDIO,
        text=[f"{v:.1f}%<br>(n={int(n)})" for v, n in zip(g['taxa_evasao_pct'], g['n'])],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Taxa de Evasão por Forma de Ingresso ({chi2_str(tab)})",
        yaxis_title="Taxa de Evasão (%)",
        yaxis=dict(range=[0, 100]),
        template="plotly_white", height=480, width=900,
    )
    salvar(fig, "17_forma_ingresso", w=900, h=480)

    resumo_df = pd.DataFrame(resumo)
    out = GRAFICOS / "sociodemografico_resumo.csv"
    resumo_df.to_csv(out, index=False, encoding="utf-8")
    print(f"\nResumo salvo: {out}")
    print(resumo_df.to_string(index=False))


if __name__ == "__main__":
    main()
