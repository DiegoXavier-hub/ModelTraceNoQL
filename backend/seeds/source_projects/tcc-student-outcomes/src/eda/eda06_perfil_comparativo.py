import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from eda_config import (DADOS, GRAFICOS, META_COLS, CAT_COLS,
                         CORES_ALVO, LABELS_ALVO, CORES_CURSO,
                         ROXO_MEDIO, ROXO_CLARO, ROXO_ESCURO,
                         VERDE, VERMELHO, AZUL, LARANJA, CINZA,
                         salvar_fig)

treino_p2 = pd.read_parquet(DADOS / "treino_p2.parquet")
treino_p4 = pd.read_parquet(DADOS / "treino_p4.parquet")
NUM_COLS = [c for c in treino_p2.columns if c not in META_COLS + CAT_COLS]

RADAR_FEATURES = ["nota_media", "taxa_aprovacao", "qtd_reprovacoes",
                   "pct_ch_concluida", "nota_p1", "delta_nota",
                   "reprov_p1", "qtd_disciplinas_total"]

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    df_norm = df[RADAR_FEATURES].copy()
    for col in RADAR_FEATURES:
        vmin, vmax = df_norm[col].min(), df_norm[col].max()
        if vmax > vmin:
            df_norm[col] = (df_norm[col] - vmin) / (vmax - vmin)
        else:
            df_norm[col] = 0.5

    df_norm["y"] = df["y"].values

    fig = go.Figure()
    for y_val in [0, 1]:
        medias = df_norm[df_norm["y"] == y_val][RADAR_FEATURES].mean()
        fig.add_trace(go.Scatterpolar(
            r=medias.values.tolist() + [medias.values[0]],
            theta=RADAR_FEATURES + [RADAR_FEATURES[0]],
            fill="toself",
            name=LABELS_ALVO[y_val],
            line_color=CORES_ALVO[y_val],
            opacity=0.6,
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1]),
            bgcolor="rgba(210, 181, 255, 0.13)",
        ),
        title=f"Perfil Medio: Evadidos vs Nao-evadidos — Treino {janela_nome}",
        height=550, width=650,
    )
    salvar_fig(fig, f"radar_perfil_{janela_nome}", width=700, height=600)

print("\n" + "=" * 90)
print("PERFIL COMPARATIVO — MEDIAS POR GRUPO DO ALVO (TREINO)")
print("=" * 90)

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    print(f"\n--- {janela_nome.upper()} ---")
    print(f"{'Feature':<25} {'Nao-evadido':>12} {'Evadido':>12} {'Diff':>10} {'Diff%':>8}")
    print("-" * 70)

    for col in NUM_COLS:
        m0 = df.loc[df["y"] == 0, col].mean()
        m1 = df.loc[df["y"] == 1, col].mean()
        diff = m1 - m0
        diff_pct = (diff / m0 * 100) if m0 != 0 else 0
        print(f"{col:<25} {m0:>12.2f} {m1:>12.2f} {diff:>+10.2f} {diff_pct:>+7.1f}%")

print("\n" + "=" * 70)
print("ANALISE DE OUTLIERS (IQR) — TREINO P2")
print("=" * 70)

outlier_summary = []

for col in NUM_COLS:
    vals = treino_p2[col].dropna()
    q1 = vals.quantile(0.25)
    q3 = vals.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    n_low = (vals < lower).sum()
    n_high = (vals > upper).sum()
    n_total = n_low + n_high
    pct = n_total / len(vals) * 100

    if n_total > 0:
        mask_out = ((treino_p2[col] < lower) | (treino_p2[col] > upper)) & treino_p2[col].notna()
        mask_in = (~mask_out) & treino_p2[col].notna()
        ev_out = treino_p2.loc[mask_out, "y"].mean() * 100 if mask_out.sum() > 0 else 0
        ev_in = treino_p2.loc[mask_in, "y"].mean() * 100 if mask_in.sum() > 0 else 0

        outlier_summary.append({
            "feature": col, "n_outliers": n_total, "pct": pct,
            "n_low": n_low, "n_high": n_high,
            "evasao_outlier": ev_out, "evasao_normal": ev_in,
        })

        print(f"  {col:<25} {n_total:>5} outliers ({pct:>5.1f}%)  "
              f"[abaixo={n_low}, acima={n_high}]  "
              f"evasao: outliers={ev_out:.1f}% vs normais={ev_in:.1f}%")

print(f"\n  Total de features com outliers: {len(outlier_summary)}/{len(NUM_COLS)}")

if outlier_summary:
    out_df = pd.DataFrame(outlier_summary).sort_values("pct", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=out_df["feature"], x=out_df["pct"], orientation="h",
        marker_color=ROXO_MEDIO,
        marker_line_color=ROXO_ESCURO, marker_line_width=0.5,
        text=[f"{v:.1f}% ({n})" for v, n in zip(out_df["pct"], out_df["n_outliers"])],
        textposition="outside",
    ))
    fig.update_layout(
        title="Percentual de Outliers por Feature (IQR) — Treino p2",
        xaxis_title="% de outliers", height=500,
    )
    salvar_fig(fig, "outliers_pct_p2")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=out_df["feature"], x=out_df["evasao_normal"], orientation="h",
        name="Normais", marker_color=ROXO_CLARO,
        marker_line_color="black", marker_line_width=0.5,
    ))
    fig.add_trace(go.Bar(
        y=out_df["feature"], x=out_df["evasao_outlier"], orientation="h",
        name="Outliers", marker_color=VERMELHO,
        marker_line_color="black", marker_line_width=0.5,
    ))
    fig.update_layout(
        title="Taxa de Evasao: Outliers vs Normais — Treino p2",
        xaxis_title="Taxa de evasao (%)", height=500,
        barmode="group",
    )
    salvar_fig(fig, "evasao_outliers_vs_normais_p2")

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    ct = df.groupby(["curso_origem", "tipo_ingresso"])["y"].agg(["mean", "size"])
    ct.columns = ["taxa_evasao", "n_alunos"]
    ct["taxa_evasao_%"] = (ct["taxa_evasao"] * 100).round(1)

    pivot = ct["taxa_evasao_%"].unstack(fill_value=0)
    pivot_n = ct["n_alunos"].unstack(fill_value=0)

    text_matrix = []
    for i in range(len(pivot)):
        row_text = []
        for j in range(len(pivot.columns)):
            taxa = pivot.iloc[i, j]
            n = int(pivot_n.iloc[i, j])
            row_text.append(f"{taxa:.1f}%\n(n={n})")
        text_matrix.append(row_text)

    colorscale = [[0, VERDE], [0.5, "#FFFFFF"], [1.0, VERMELHO]]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=colorscale,
        zmin=0, zmax=100,
        text=text_matrix,
        texttemplate="%{text}",
        textfont=dict(size=10),
        colorbar_title="Evasao %",
    ))
    fig.update_layout(
        title=f"Taxa de Evasao por Curso x Tipo de Ingresso — Treino {janela_nome}",
        height=400, width=900,
        xaxis_tickangle=-30,
    )
    salvar_fig(fig, f"heatmap_curso_ingresso_{janela_nome}", width=1000, height=450)

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    fig = go.Figure()

    for y_val in [0, 1]:
        sub = df[df["y"] == y_val].sample(min(500, len(df[df["y"] == y_val])),
                                           random_state=42)
        fig.add_trace(go.Scatter(
            x=sub["nota_media"], y=sub["taxa_aprovacao"],
            mode="markers",
            name=LABELS_ALVO[y_val],
            marker=dict(color=CORES_ALVO[y_val], size=5, opacity=0.4),
        ))

    fig.update_layout(
        title=f"nota_media vs taxa_aprovacao — Treino {janela_nome}",
        xaxis_title="Nota media", yaxis_title="Taxa de aprovacao",
        height=500, width=700,
    )
    salvar_fig(fig, f"scatter_nota_taxa_{janela_nome}")

print("\n" + "=" * 80)
print("SINTESE DOS ACHADOS DA EDA")
print("=" * 80)

for janela_nome, df in [("p2", treino_p2), ("p4", treino_p4)]:
    print(f"\n{'='*60}")
    print(f"JANELA {janela_nome.upper()}")
    print(f"{'='*60}")

    n_total = len(df)
    taxa_ev = df["y"].mean() * 100
    print(f"\n1. AMOSTRA: {n_total:,} alunos, taxa de evasao = {taxa_ev:.1f}%")

    diffs = []
    for col in NUM_COLS:
        m0 = df.loc[df["y"] == 0, col].mean()
        m1 = df.loc[df["y"] == 1, col].mean()
        diff_pct = abs((m1 - m0) / m0 * 100) if m0 != 0 else 0
        diffs.append((col, m0, m1, diff_pct))

    diffs.sort(key=lambda x: x[3], reverse=True)
    print(f"\n2. FEATURES MAIS DISCRIMINATIVAS (maiores diferencas relativas):")
    for col, m0, m1, d in diffs[:7]:
        direcao = "maior nos evadidos" if m1 > m0 else "menor nos evadidos"
        print(f"   {col:<25} nao-ev={m0:.2f}, ev={m1:.2f} "
              f"(diff={d:.1f}%, {direcao})")

    print(f"\n3. EVASAO POR CURSO:")
    for curso in sorted(df["curso_origem"].unique()):
        sub = df[df["curso_origem"] == curso]
        print(f"   {curso}: {sub['y'].mean()*100:.1f}% ({len(sub)} alunos)")

    nulos = df[NUM_COLS].isnull().sum()
    nulos = nulos[nulos > 0]
    print(f"\n4. VALORES FALTANTES: {len(nulos)} features com nulos "
          f"(max = {nulos.max() if len(nulos) > 0 else 0})")

    n_features_out = 0
    for col in NUM_COLS:
        vals = df[col].dropna()
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        n_out = ((vals < q1 - 1.5 * iqr) | (vals > q3 + 1.5 * iqr)).sum()
        if n_out > 0:
            n_features_out += 1
    print(f"\n5. OUTLIERS: {n_features_out}/{len(NUM_COLS)} features com outliers (IQR)")

print("""
===============================================
CONCLUSOES GERAIS
===============================================

A. DESBALANCEAMENTO: moderado (~37% evadidos no treino p2, ~34% no treino p4).
   Estrategia: class_weight='balanced' + threshold tuning (sem SMOTE).

B. FEATURES DISCRIMINATIVAS: nota_media, taxa_aprovacao, qtd_reprovacoes e
   pct_ch_concluida apresentam as maiores diferencas entre grupos.
   Evadidos tem notas mais baixas, mais reprovacoes e menor progresso curricular.

C. MULTICOLINEARIDADE: esperada entre features de desempenho (nota_media,
   nota_mediana, nota_p1) e entre contagens (qtd_disciplinas_total,
   qtd_aprovacoes). Modelos baseados em arvore sao robustos a isso;
   Regressao Logistica pode precisar de regularizacao.

D. DRIFT TEMPORAL: taxa de evasao sobe de ~35% (treino) para ~55% (teste).
   Isso e concept drift real, nao um artefato. O modelo sera avaliado
   nesse cenario realista.

E. OUTLIERS: presentes em varias features, concentrados em alunos com
   muitas dispensas ou padroes atipicos. Nao serao removidos — sao
   informacao valida sobre perfis extremos.

F. NULOS: muito poucos (<1% na maioria). Concentrados em evadidos (alunos
   que so fizeram dispensas no periodo). Tratamento: imputacao simples
   (mediana) ou indicador de nulidade.
""")

print("EDA 06 concluida.")
