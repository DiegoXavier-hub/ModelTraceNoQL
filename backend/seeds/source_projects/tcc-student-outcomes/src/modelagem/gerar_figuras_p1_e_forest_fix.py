"""Gera figuras faltantes da janela p1 e corrige o forest plot (eixo X distorcido).

Figuras produzidas:
- fig_forest_plot_p2.png / fig_forest_plot_p4.png (corrigidas: ratios clipados a 20x,
  features com mean_formado~0 descartadas, escala log dentro de [0.1, 20]).
- fig_forest_plot_p1.png (nova: razao evadido/formado para variaveis cadastrais
  numericas e razao de taxas por categoria para variaveis categoricas).
- fig_medianas_p1.png (nova: tabela comparativa cadastral por desfecho).
- roc_teste_p1.png (nova: curvas ROC dos 5 modelos no teste p1).
- fig_bootstrap_ci_p1.png (nova: tabela IC 95% p1).
- fig_equity_curso_p1.png (nova: recall, FPR, F2 por curso na p1).
- fig_shap_bar_p1.png (nova: top-8 importancia por ganho CatBoost p1).
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import joblib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import roc_curve, roc_auc_score

from config_modelagem import (
    DADOS, RESULTADOS, SEED, TARGET,
    ROXO_MEDIO, VERDE, VERMELHO, AZUL, LARANJA, CINZA,
    CORES_MODELO, calcular_metricas, bootstrap_metricas, ci_95, N_BOOTSTRAP,
    get_features,
)

PROJETO = Path(__file__).resolve().parent.parent.parent
GRAFICOS_ARTIGO = PROJETO / "article" / "Images" / "artigo"
GRAFICOS_ARTIGO.mkdir(parents=True, exist_ok=True)

MODELO_TIPO = {"LR": "scaled", "RF": "tree", "XGBoost": "tree",
               "CatBoost": "cb", "MLP": "scaled"}
NOMES_MODELO = ["LR", "RF", "XGBoost", "CatBoost", "MLP"]

nomes_curso_bonito = {
    "ADM_Integral": "ADM Integral",
    "ADM_Noturno": "ADM Noturno",
    "GI": "Gestao da Informacao",
}
cores_curso = {"ADM_Integral": AZUL, "ADM_Noturno": LARANJA, "GI": ROXO_MEDIO}


def salvar(fig: go.Figure, nome: str, width: int = 900, height: int = 600) -> None:
    fig.write_image(str(GRAFICOS_ARTIGO / f"{nome}.png"), width=width, height=height, scale=2)
    fig.write_html(str(GRAFICOS_ARTIGO / f"{nome}.html"), include_plotlyjs="cdn")
    print(f"  salvo: {nome}.png")


def carregar_x_teste(teste: pd.DataFrame, janela: int, tipo: str):
    cat_f, num_f, all_f = get_features(janela)
    if tipo == "scaled":
        pre = joblib.load(RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
        return pre.transform(teste[all_f])
    if tipo == "tree":
        pre = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
        return pre.transform(teste[all_f])
    return teste[all_f].copy()


print("\n--- Forest plot corrigido (p2, p4) ---")
RATIO_CAP = 20.0
MEAN_F_MIN_REL = 0.05

feats_fp = [
    ("nota_media", "Nota Media"),
    ("nota_mediana", "Nota Mediana"),
    ("nota_desvio", "Desvio Padrao Nota"),
    ("nota_min", "Nota Minima"),
    ("nota_max", "Nota Maxima"),
    ("taxa_aprovacao", "Taxa Aprovacao"),
    ("qtd_aprovacoes", "Qtd Aprovacoes"),
    ("qtd_reprovacoes", "Qtd Reprovacoes"),
    ("qtd_reprov_nota", "Reprov. por Nota"),
    ("qtd_reprov_freq", "Reprov. por Frequencia"),
    ("ch_acumulada", "CH Acumulada"),
    ("pct_ch_concluida", "% CH Concluida"),
    ("nota_p1", "Nota 1o Periodo"),
    ("reprov_p1", "Reprov. 1o Periodo"),
    ("media_disc_por_periodo", "Media Disc/Periodo"),
    ("qtd_disciplinas_total", "Total Disciplinas"),
]

for janela in (2, 4):
    df = pd.read_parquet(DADOS / f"ml_p{janela}.parquet")
    labels, ratios, ci_low, ci_high = [], [], [], []
    rng = np.random.RandomState(SEED)

    for feat, label in feats_fp:
        col = df[feat].astype(float)
        scale = max(col.std(), 1e-6)
        mean_f = df.loc[df["y"] == 0, feat].mean()
        mean_e = df.loc[df["y"] == 1, feat].mean()

        if abs(mean_f) < MEAN_F_MIN_REL * scale:
            continue

        ratio = float(np.clip(mean_e / mean_f, 1.0 / RATIO_CAP, RATIO_CAP))
        labels.append(label)
        ratios.append(ratio)

        boot = []
        for _ in range(2000):
            idx = rng.randint(0, len(df), len(df))
            b = df.iloc[idx]
            mf = b.loc[b["y"] == 0, feat].mean()
            me = b.loc[b["y"] == 1, feat].mean()
            if abs(mf) < MEAN_F_MIN_REL * scale:
                continue
            boot.append(float(np.clip(me / mf, 1.0 / RATIO_CAP, RATIO_CAP)))
        if len(boot) > 100:
            ci_low.append(float(np.percentile(boot, 2.5)))
            ci_high.append(float(np.percentile(boot, 97.5)))
        else:
            ci_low.append(ratio * 0.9)
            ci_high.append(ratio * 1.1)

    order = np.argsort(ratios)
    labels_s = [labels[i] for i in order]
    ratios_s = [ratios[i] for i in order]
    ci_low_s = [ci_low[i] for i in order]
    ci_high_s = [ci_high[i] for i in order]
    colors_s = [VERMELHO if r < 0.85 else (VERDE if r > 1.15 else CINZA) for r in ratios_s]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ratios_s, y=labels_s,
        mode="markers",
        marker=dict(size=12, color=colors_s, line=dict(width=1, color="black")),
        error_x=dict(
            type="data", symmetric=False,
            array=[h - r for r, h in zip(ratios_s, ci_high_s)],
            arrayminus=[r - l for r, l in zip(ratios_s, ci_low_s)],
            color="rgba(100,100,100,0.6)", thickness=2.5, width=6,
        ),
        showlegend=False,
    ))
    fig.add_vline(x=1.0, line_dash="dash", line_color="gray", line_width=1.5)
    fig.add_annotation(x=np.log10(0.3), y=1.03, text="< Protecao",
                       showarrow=False, xref="x", yref="paper",
                       font=dict(size=11, color=VERMELHO))
    fig.add_annotation(x=np.log10(5.0), y=1.03, text="Risco >",
                       showarrow=False, xref="x", yref="paper",
                       font=dict(size=11, color=VERDE))

    fig.update_layout(
        title=f"Multiplicador de Risco (Razao Media Evadido/Formado) -- p{janela}",
        xaxis_title="Razao de Medias (Evadido / Formado) -- escala log",
        height=600, width=800,
        template="plotly_white",
        xaxis=dict(type="log", range=[np.log10(1.0 / RATIO_CAP), np.log10(RATIO_CAP)],
                   tickvals=[0.1, 0.25, 0.5, 1, 2, 5, 10, 20]),
        margin=dict(l=180),
    )
    salvar(fig, f"fig_forest_plot_p{janela}", width=800, height=600)


print("\n--- Forest plot p1: taxas por categoria ---")
df1 = pd.read_parquet(DADOS / "ml_p1.parquet")
taxa_global = df1["y"].mean()

categorias_p1 = []
for var, label_prefix in [
    ("sexo", "Sexo"),
    ("cotista", "Cotista"),
    ("natural_uberlandia", "Natural UDI"),
    ("forma_ingresso_grp", "Ingresso"),
    ("curso_origem", "Curso"),
]:
    for val in sorted(df1[var].dropna().unique()):
        sub = df1[df1[var] == val]
        if len(sub) < 30:
            continue
        taxa_cat = sub["y"].mean()
        razao = taxa_cat / taxa_global
        label = f"{label_prefix}: {val}"
        rng = np.random.RandomState(SEED)
        boots = []
        for _ in range(2000):
            idx = rng.randint(0, len(sub), len(sub))
            boots.append(sub.iloc[idx]["y"].mean() / taxa_global)
        ci_low_v = float(np.percentile(boots, 2.5))
        ci_high_v = float(np.percentile(boots, 97.5))
        categorias_p1.append((label, razao, ci_low_v, ci_high_v, int(len(sub))))

df1["faixa_idade"] = pd.cut(df1["idade_ingresso"],
                             bins=[0, 18, 20, 25, 30, 100],
                             labels=["<=18", "19-20", "21-25", "26-30", ">30"])
for val in ["<=18", "19-20", "21-25", "26-30", ">30"]:
    sub = df1[df1["faixa_idade"] == val]
    if len(sub) < 30:
        continue
    razao = sub["y"].mean() / taxa_global
    rng = np.random.RandomState(SEED)
    boots = [sub.iloc[rng.randint(0, len(sub), len(sub))]["y"].mean() / taxa_global
             for _ in range(2000)]
    categorias_p1.append((f"Idade: {val}", razao,
                          float(np.percentile(boots, 2.5)),
                          float(np.percentile(boots, 97.5)),
                          int(len(sub))))

categorias_p1.sort(key=lambda r: r[1])
labels_p1 = [f"{c[0]} (n={c[4]})" for c in categorias_p1]
ratios_p1 = [c[1] for c in categorias_p1]
lo_p1 = [c[2] for c in categorias_p1]
hi_p1 = [c[3] for c in categorias_p1]
cores_p1 = [VERMELHO if r < 0.85 else (VERDE if r > 1.15 else CINZA) for r in ratios_p1]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=ratios_p1, y=labels_p1,
    mode="markers",
    marker=dict(size=11, color=cores_p1, line=dict(width=1, color="black")),
    error_x=dict(
        type="data", symmetric=False,
        array=[h - r for r, h in zip(ratios_p1, hi_p1)],
        arrayminus=[r - l for r, l in zip(ratios_p1, lo_p1)],
        color="rgba(100,100,100,0.6)", thickness=2.2, width=5,
    ),
    showlegend=False,
))
fig.add_vline(x=1.0, line_dash="dash", line_color="gray", line_width=1.5)
fig.update_layout(
    title="Razao de Taxas por Subgrupo Cadastral -- p1 (ingresso)",
    xaxis_title=f"Taxa subgrupo / Taxa global (= {taxa_global:.3f})",
    height=720, width=880,
    template="plotly_white",
    xaxis=dict(range=[0, max(2.5, max(hi_p1) * 1.1)]),
    margin=dict(l=220),
)
salvar(fig, "fig_forest_plot_p1", width=880, height=720)


print("\n--- Medianas p1 (tabela cadastral) ---")
rows = []
for feat, label in [("idade_ingresso", "Idade ingresso"),
                     ("cotista", "Cotista (0=nao, 1=sim)"),
                     ("natural_uberlandia", "Natural UDI (0=nao,1=sim)"),
                     ("num_semestre_ingresso", "Semestre ingresso")]:
    med_f = df1.loc[df1["y"] == 0, feat].median()
    med_e = df1.loc[df1["y"] == 1, feat].median()
    rows.append([label, f"{med_f:.2f}", f"{med_e:.2f}", f"{med_e - med_f:+.2f}"])

for feat, label in [("sexo", "Sexo (%M)"),
                     ("curso_origem", "Curso majoritario"),
                     ("forma_ingresso_grp", "Forma majoritaria"),
                     ("tipo_ingresso", "Tipo majoritario")]:
    form_g = df1.loc[df1["y"] == 0, feat]
    evad_g = df1.loc[df1["y"] == 1, feat]
    if feat == "sexo":
        f_val = f"{(form_g == 'M').mean() * 100:.1f}%"
        e_val = f"{(evad_g == 'M').mean() * 100:.1f}%"
        diff = ""
    else:
        f_val = str(form_g.mode().iloc[0]) if len(form_g) else "-"
        e_val = str(evad_g.mode().iloc[0]) if len(evad_g) else "-"
        diff = ""
    rows.append([label, f_val, e_val, diff])

header = ["Variavel", "Formado", "Evadido", "Diferenca"]
cells = list(zip(*rows))
fig = go.Figure(data=[go.Table(
    header=dict(values=header, fill_color=ROXO_MEDIO,
                font=dict(color="white", size=12), align="center"),
    cells=dict(values=cells, align=["left", "center", "center", "center"],
               font=dict(size=11), height=28),
)])
fig.update_layout(title="Perfil Cadastral por Desfecho -- Janela p1",
                  height=400, width=780, margin=dict(l=10, r=10, t=40, b=10))
salvar(fig, "fig_medianas_p1", width=780, height=400)


print("\n--- ROC teste p1 ---")
teste1 = pd.read_parquet(DADOS / "teste_p1.parquet")
y1 = teste1[TARGET].values

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[0, 1], y=[0, 1], mode="lines",
    line=dict(color="gray", dash="dash", width=1),
    name="Aleatorio (AUC=0.500)",
))
for nome in NOMES_MODELO:
    modelo = joblib.load(RESULTADOS / f"modelo_{nome}_p1.joblib")
    X_t = carregar_x_teste(teste1, 1, MODELO_TIPO[nome])
    y_prob = modelo.predict_proba(X_t)[:, 1]
    fpr, tpr, _ = roc_curve(y1, y_prob)
    auc = roc_auc_score(y1, y_prob)
    fig.add_trace(go.Scatter(
        x=fpr, y=tpr, mode="lines",
        name=f"{nome} (AUC={auc:.3f})",
        line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2.5),
    ))

fig.update_layout(
    title="Curva ROC -- Teste p1 (8 variaveis cadastrais)",
    xaxis_title="FPR (Taxa de Falsos Positivos)",
    yaxis_title="TPR (Recall)",
    height=550, width=700,
    legend=dict(x=0.55, y=0.05, bgcolor="rgba(255,255,255,0.85)"),
    template="plotly_white",
)
salvar(fig, "roc_teste_p1", width=700, height=550)
import shutil
shutil.copy(str(GRAFICOS_ARTIGO / "roc_teste_p1.png"),
            str(PROJETO / "article" / "Images" / "roc_teste_p1.png"))


print("\n--- Bootstrap CI p1 ---")
thresholds1 = joblib.load(RESULTADOS / "thresholds_otimos_p1.joblib")
rows_ci = []
for nome in NOMES_MODELO:
    modelo = joblib.load(RESULTADOS / f"modelo_{nome}_p1.joblib")
    X_t = carregar_x_teste(teste1, 1, MODELO_TIPO[nome])
    y_prob = modelo.predict_proba(X_t)[:, 1]
    thr = thresholds1[nome]
    y_pred = (y_prob >= thr).astype(int)
    boot = bootstrap_metricas(y1, y_pred, y_prob, n_boot=N_BOOTSTRAP, seed=SEED)
    f2_m, f2_l, f2_h = ci_95([b["f2"] for b in boot])
    auc_m, auc_l, auc_h = ci_95([b["auc_roc"] for b in boot])
    rec_m, rec_l, rec_h = ci_95([b["recall"] for b in boot])
    rows_ci.append([nome, f"{f2_m:.3f}", f"[{f2_l:.3f}; {f2_h:.3f}]",
                    f"{auc_m:.3f}", f"[{auc_l:.3f}; {auc_h:.3f}]",
                    f"{rec_m:.3f}", f"[{rec_l:.3f}; {rec_h:.3f}]"])
    print(f"  p1 {nome}: F2={f2_m:.3f} [{f2_l:.3f};{f2_h:.3f}]")

header = ["Modelo", "F2", "IC 95% F2", "AUC", "IC 95% AUC", "Recall", "IC 95% Recall"]
cells = list(zip(*rows_ci))
fig = go.Figure(data=[go.Table(
    header=dict(values=header, fill_color=ROXO_MEDIO,
                font=dict(color="white", size=12), align="center"),
    cells=dict(values=cells, align="center", font=dict(size=11), height=28),
)])
fig.update_layout(title="Intervalos de Confianca (Bootstrap 5000) -- Teste p1",
                  height=280, width=950, margin=dict(l=10, r=10, t=40, b=10))
salvar(fig, "fig_bootstrap_ci_p1", width=950, height=280)


print("\n--- Equidade por curso p1 (CatBoost) ---")
modelo_cb = joblib.load(RESULTADOS / "modelo_CatBoost_p1.joblib")
X_cb = carregar_x_teste(teste1, 1, "cb")
y_prob = modelo_cb.predict_proba(X_cb)[:, 1]
thr = thresholds1["CatBoost"]
y_pred = (y_prob >= thr).astype(int)

cursos = sorted(teste1["curso_origem"].unique())
recalls, fprs, f2s = [], [], []
for c in cursos:
    mask = (teste1["curso_origem"] == c).values
    yt, yp, ypr = y1[mask], y_pred[mask], y_prob[mask]
    if len(np.unique(yt)) < 2:
        recalls.append(0); fprs.append(0); f2s.append(0)
        continue
    m = calcular_metricas(yt, yp, ypr)
    recalls.append(m["recall"])
    fprs.append(m["fp"] / max(1, m["fp"] + m["tn"]))
    f2s.append(m["f2"])

cursos_b = [nomes_curso_bonito.get(c, c) for c in cursos]
cores_c = [cores_curso.get(c, ROXO_MEDIO) for c in cursos]

fig = make_subplots(rows=1, cols=3,
                    subplot_titles=["Recall por Curso", "FPR por Curso", "F2 por Curso"])
fig.add_trace(go.Bar(x=cursos_b, y=recalls, marker_color=cores_c,
                     text=[f"{v:.3f}" for v in recalls], textposition="outside",
                     showlegend=False), row=1, col=1)
fig.add_trace(go.Bar(x=cursos_b, y=fprs, marker_color=cores_c,
                     text=[f"{v:.3f}" for v in fprs], textposition="outside",
                     showlegend=False), row=1, col=2)
fig.add_trace(go.Bar(x=cursos_b, y=f2s, marker_color=cores_c,
                     text=[f"{v:.3f}" for v in f2s], textposition="outside",
                     showlegend=False), row=1, col=3)
for c in (1, 2, 3):
    fig.update_yaxes(range=[0, 1.15], row=1, col=c)
fig.update_layout(title="Equidade por Curso -- CatBoost p1",
                  height=450, width=1000, template="plotly_white")
salvar(fig, "fig_equity_curso_p1", width=1000, height=450)


print("\n--- SHAP bar p1 (CatBoost feature_importance) ---")
cat_f1, num_f1, all_f1 = get_features(1)
try:
    importances = modelo_cb.get_feature_importance()
    ranking = sorted(zip(all_f1, importances), key=lambda x: -x[1])
    feats_plot = [f for f, _ in ranking]
    vals_plot = [v for _, v in ranking]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=feats_plot[::-1], x=vals_plot[::-1],
        orientation="h", marker_color=ROXO_MEDIO,
        text=[f"{v:.2f}" for v in vals_plot[::-1]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Importancia de Features -- CatBoost p1 (8 cadastrais)",
        xaxis_title="Importancia relativa (ganho)",
        height=450, width=780, template="plotly_white",
        margin=dict(l=180),
    )
    salvar(fig, "fig_shap_bar_p1", width=780, height=450)
except Exception as e:
    print(f"  ERRO SHAP p1: {e}")

print("\nConcluido!")
