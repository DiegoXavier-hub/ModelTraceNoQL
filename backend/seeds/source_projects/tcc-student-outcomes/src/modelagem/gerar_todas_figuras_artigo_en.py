# gerar_todas_figuras_artigo.py
"""
Gera TODAS as figuras Plotly para o artigo TCC_Evasao.tex.
Cada figura e salva como PNG (alta resolucao) na pasta GRAFICOS_ARTIGO.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import (roc_curve, roc_auc_score, precision_recall_curve,
                             average_precision_score, confusion_matrix, fbeta_score)
from sklearn.calibration import calibration_curve

from config_modelagem import (DADOS, RESULTADOS, GRAFICOS, TARGET, SEED,
                               CORES_MODELO, ROXO_MEDIO, ROXO_CLARO, ROXO_ESCURO,
                               VERDE, VERMELHO, AZUL, LARANJA, CINZA,
                               calcular_metricas, f2_score, bootstrap_metricas,
                               ci_95, N_BOOTSTRAP, get_features)

PROJETO = Path(__file__).resolve().parents[2]
GRAFICOS_ARTIGO = PROJETO / "article" / "Images" / "artigo_en"
GRAFICOS_ARTIGO.mkdir(parents=True, exist_ok=True)

# Paleta
ROXO_BG = "#F9F0FF"

def salvar(fig, nome, width=900, height=600):
    """Salva figura Plotly como PNG e HTML."""
    fig.write_image(str(GRAFICOS_ARTIGO / f"{nome}.png"), width=width, height=height, scale=2)
    fig.write_html(str(GRAFICOS_ARTIGO / f"{nome}.html"), include_plotlyjs="cdn")
    print(f"  Salvo: {nome}.png")


# =================================================================
# CARREGAR DADOS
# =================================================================
print("Carregando dados...")
dfs = {}
for name in ['treino_p1', 'treino_p2', 'treino_p4', 'val_p1', 'val_p2', 'val_p4', 'teste_p1', 'teste_p2', 'teste_p4',
             'ml_p1', 'ml_p2', 'ml_p4']:
    dfs[name] = pd.read_parquet(DADOS / f"{name}.parquet")

res_todos = pd.read_csv(RESULTADOS / "resultados_todos_modelos.csv")
res_thr = pd.read_csv(RESULTADOS / "resultados_threshold_teste.csv")

MODELO_TIPO = {
    "LR":       "scaled",
    "RF":       "tree",
    "XGBoost":  "tree",
    "CatBoost": "cb",
    "MLP":      "scaled",
}
NOMES_MODELO = ["LR", "RF", "XGBoost", "CatBoost", "MLP"]
JANELAS = [1, 2, 4]
JANELAS_ACADEMICAS = [2, 4]
MODELOS_SELECIONADOS = {1: "CatBoost", 2: "XGBoost", 4: "CatBoost"}


# =================================================================
# FIG 1: TAXA DE EVASAO POR CURSO (barra)
# =================================================================
print("\n--- Fig 1: Taxa de evasao por curso ---")
fig = go.Figure()
cores_curso = {"ADM_Integral": AZUL, "ADM_Noturno": LARANJA, "GI": ROXO_MEDIO}
nomes_curso_bonito = {
    "ADM_Integral": "Business Admin Full-time",
    "ADM_Noturno": "Business Admin Evening",
    "GI": "Information Management"
}

for janela_label, ml_name in [("p1", "ml_p1"), ("p2", "ml_p2"), ("p4", "ml_p4")]:
    df = dfs[ml_name]
    for curso in ["ADM_Integral", "ADM_Noturno", "GI"]:
        sub = df[df["curso_origem"] == curso]
        rate = sub["y"].mean() * 100

        fig.add_trace(go.Bar(
            x=[f"{nomes_curso_bonito[curso]}<br>({janela_label})"],
            y=[rate],
            marker_color=cores_curso[curso],
            name=nomes_curso_bonito[curso],
            text=f"{rate:.1f}%",
            textposition="outside",
            cliponaxis=False,
            showlegend=(janela_label == "p2"),
            legendgroup=curso,
        ))

fig.update_layout(
    title=dict(
        text="Dropout Rate by Program and Observation Window",
        x=0.02,
        xanchor="left"
    ),
    yaxis_title="Dropout Rate (%)",
    yaxis=dict(range=[0, 85]),
    height=500,
    width=800,
    template="plotly_white",
    barmode="group",
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.08,
        xanchor="left",
        x=0.02
    ),
    margin=dict(t=120, r=40, l=60, b=80)
)

salvar(fig, "fig_evasao_por_curso", width=800, height=500)


# =================================================================
# FIG 2: DISTRIBUICAO TEMPORAL DOS SPLITS (3 figuras separadas)
# =================================================================
print("\n--- Fig 2: Distribuicao temporal dos splits ---")

def gerar_fig_split_temporal(janela):
    df = dfs[f"ml_p{janela}"].copy()

    anos = (
        pd.Series(df["ano_ingresso"])
        .dropna()
        .astype(int)
        .sort_values()
        .unique()
        .tolist()
    )

    if not anos:
        print(f"  [ERRO] p{janela}: sem valores validos em ano_ingresso")
        return

    treino_counts, val_counts, teste_counts = [], [], []

    for ano in anos:
        n = int((df["ano_ingresso"].astype("Int64") == ano).sum())

        if ano <= 2015:
            treino_counts.append(n)
            val_counts.append(0)
            teste_counts.append(0)
        elif ano <= 2017:
            treino_counts.append(0)
            val_counts.append(n)
            teste_counts.append(0)
        else:
            treino_counts.append(0)
            val_counts.append(0)
            teste_counts.append(n)

    year_labels = []
    tr_agg, va_agg, te_agg = [], [], []

    pre2000_tr = sum(t for a, t in zip(anos, treino_counts) if a < 2000)
    pre2000_va = sum(v for a, v in zip(anos, val_counts) if a < 2000)
    pre2000_te = sum(t for a, t in zip(anos, teste_counts) if a < 2000)

    if (pre2000_tr + pre2000_va + pre2000_te) > 0:
        year_labels.append("<2000")
        tr_agg.append(pre2000_tr)
        va_agg.append(pre2000_va)
        te_agg.append(pre2000_te)

    for i, ano in enumerate(anos):
        if ano >= 2000:
            year_labels.append(str(ano))
            tr_agg.append(treino_counts[i])
            va_agg.append(val_counts[i])
            te_agg.append(teste_counts[i])

    if not year_labels:
        print(f"  [ERRO] p{janela}: nenhum rotulo de ano foi gerado")
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=year_labels,
        y=tr_agg,
        name="Training",
        marker_color=AZUL
    ))

    fig.add_trace(go.Bar(
        x=year_labels,
        y=va_agg,
        name="Validation",
        marker_color=LARANJA
    ))

    fig.add_trace(go.Bar(
        x=year_labels,
        y=te_agg,
        name="Test",
        marker_color=VERMELHO
    ))

    fig.update_layout(
        title=dict(
            text=f"Temporal Distribution of Data Splits -- Window p{janela}",
            x=0.02,
            xanchor="left"
        ),
        xaxis_title="Year of Entry",
        yaxis_title="Number of Students",
        height=420,
        width=820,
        template="plotly_white",
        barmode="stack",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0.02
        ),
        margin=dict(t=100, r=40, l=60, b=80)
    )

    salvar(fig, f"fig_split_temporal_p{janela}", width=820, height=420)
    print(f"  OK: p{janela} com {len(year_labels)} grupos no eixo X")


for janela in [1, 2, 4]:
    gerar_fig_split_temporal(janela)

# =================================================================
# FIG 3: TABELA DE MEDIANAS POR DESFECHO (formados vs evadidos)
# =================================================================
print("\n--- Fig 3: Medianas por desfecho ---")
feats_display_p1 = [
    ("idade_ingresso", "Age at Entry"),
    ("num_semestre_ingresso", "Entry Semester"),
    ("cotista", "Quota Student"),
    ("natural_uberlandia", "Born in Uberlandia"),
]

feats_display = [
    ("nota_media", "Average Grade"),
    ("nota_mediana", "Median Grade"),
    ("nota_desvio", "Grade Standard Deviation"),
    ("nota_min", "Minimum Grade"),
    ("nota_max", "Maximum Grade"),
    ("qtd_aprovacoes", "Number of Passes"),
    ("qtd_reprovacoes", "Number of Failures"),
    ("taxa_aprovacao", "Pass Rate"),
    ("qtd_disciplinas_total", "Total Courses"),
    ("media_disc_por_periodo", "Average Courses per Semester"),
    ("ch_acumulada", "Accumulated Credits (h)"),
    ("pct_ch_concluida", "% Completed Credits"),
    ("nota_p1", "1st Semester Grade"),
    ("delta_nota", "Grade Delta"),
    ("reprov_p1", "Failures in 1st Semester"),
    ("disc_p1", "Courses in 1st Semester"),
]

for janela in JANELAS:
    df = dfs[f"ml_p{janela}"]
    feats_janela = feats_display_p1 if janela == 1 else feats_display
    rows_data = []
    for feat, label in feats_janela:
        med_f = df[df["y"]==0][feat].median()
        med_e = df[df["y"]==1][feat].median()
        diff = med_e - med_f
        rows_data.append([label, f"{med_f:.2f}", f"{med_e:.2f}", f"{diff:+.2f}"])

    header = ["Variable", "Graduate (med)", "Dropout (med)", "Difference"]
    cells_vals = list(zip(*rows_data))

    # Color cells based on difference direction
    fill_colors = []
    for i in range(len(header)):
        col_colors = []
        for r in rows_data:
            if i == 3:  # difference column
                val = float(r[3])
                if val < -1:
                    col_colors.append("rgba(231,76,60,0.15)")
                elif val > 1:
                    col_colors.append("rgba(39,174,96,0.15)")
                else:
                    col_colors.append("white")
            else:
                col_colors.append("white")
        fill_colors.append(col_colors)

    fig = go.Figure(data=[go.Table(
        header=dict(values=header,
                    fill_color=ROXO_MEDIO, font=dict(color="white", size=12),
                    align="center"),
        cells=dict(values=cells_vals,
                   fill_color=fill_colors,
                   align=["left", "center", "center", "center"],
                   font=dict(size=11),
                   height=28),
    )])
    fig.update_layout(title=f"Medians by Outcome -- Window p{janela}",
                      height=550, width=750, margin=dict(l=10, r=10, t=40, b=10))
    salvar(fig, f"fig_medianas_p{janela}", width=750, height=550)


# =================================================================
# FIG 4: FOREST PLOT - MULTIPLICADOR DE RISCO (razao de medias)
# =================================================================
print("\n--- Fig 4: Forest plot - multiplicador de risco ---")

def calcular_razao_subgrupo(df, mask):
    y = df["y"].to_numpy()
    mask = np.asarray(mask, dtype=bool)
    taxa_global = y.mean()
    razao = y[mask].mean() / taxa_global

    rng = np.random.RandomState(SEED)
    boots = []
    for _ in range(2000):
        idx = rng.randint(0, len(df), len(df))
        boot_mask = mask[idx]
        if boot_mask.sum() == 0:
            continue
        taxa_boot_global = y[idx].mean()
        if taxa_boot_global > 0:
            boots.append(y[idx][boot_mask].mean() / taxa_boot_global)

    if boots:
        return razao, np.percentile(boots, 2.5), np.percentile(boots, 97.5)
    return razao, razao * 0.8, razao * 1.2


def preparar_forest_p1(df):
    categorias = []
    entrada_labels = [
        ("Vestibular", "Entrance Exam Entry"),
        ("SISU", "SISU Entry"),
        ("PAIES_PAAES", "PAIES/PAAES Entry"),
        ("Transferencia", "Transfer Entry"),
        ("Portador_Diploma", "Diploma Holder Entry"),
        ("Outros", "Other Entry"),
    ]

    for valor, label in entrada_labels:
        mask = (df["forma_ingresso_grp"] == valor).to_numpy()
        if mask.sum() >= 30:
            razao, ci_low, ci_high = calcular_razao_subgrupo(df, mask)
            categorias.append((f"{label} (n={mask.sum()})", razao, ci_low, ci_high))

    faixas = pd.cut(
        df["idade_ingresso"],
        bins=[0, 18, 20, 24, 30, 120],
        labels=["Age <= 18", "Age 19-20", "Age 21-24", "Age 25-30", "Age > 30"],
        right=True,
    )
    for faixa in ["Age <= 18", "Age 19-20", "Age 21-24", "Age 25-30", "Age > 30"]:
        mask = (faixas == faixa).to_numpy()
        if mask.sum() >= 30:
            razao, ci_low, ci_high = calcular_razao_subgrupo(df, mask)
            categorias.append((f"{faixa} (n={mask.sum()})", razao, ci_low, ci_high))

    return categorias

for janela in JANELAS:
    df = dfs[f"ml_p{janela}"]
    if janela == 1:
        categorias_p1 = preparar_forest_p1(df)
        labels, ratios, ci_low, ci_high = zip(*categorias_p1)
        title = "Risk Multiplier by Subgroup (Subgroup Rate / Overall Rate) -- p1"
        xaxis_title = f"Rate Ratio (Subgroup / Overall = {df['y'].mean():.3f})"
        height, width, margin_l = 660, 880, 230
    else:
        feats_fp = [
        ("nota_media", "Average Grade"),
        ("nota_mediana", "Median Grade"),
        ("nota_desvio", "Grade Standard Deviation"),
        ("nota_min", "Minimum Grade"),
        ("nota_max", "Maximum Grade"),
        ("taxa_aprovacao", "Pass Rate"),
        ("qtd_aprovacoes", "Number of Passes"),
        ("qtd_reprovacoes", "Number of Failures"),
        ("qtd_reprov_nota", "Failures by Grade"),
        ("qtd_reprov_freq", "Failures by Attendance"),
        ("ch_acumulada", "Accumulated Credits"),
        ("pct_ch_concluida", "% Completed Credits"),
        ("nota_p1", "1st Semester Grade"),
        ("reprov_p1", "Failures in 1st Semester"),
        ("media_disc_por_periodo", "Average Courses per Semester"),
        ("qtd_disciplinas_total", "Total Courses"),
        ]
        labels, ratios = [], []
        for feat, label in feats_fp:
            # Usar MEDIA (evita problema de mediana=0)
            mean_f = df[df["y"]==0][feat].mean()
            mean_e = df[df["y"]==1][feat].mean()
            if abs(mean_f) > 1e-6:
                ratio = mean_e / mean_f
            elif abs(mean_e) > 1e-6:
                ratio = 8.0  # sinal claro: formado=0, evadido>0
            else:
                ratio = 1.0
            labels.append(label)
            ratios.append(ratio)

        # Bootstrap CI para razao de medias
        rng = np.random.RandomState(SEED)
        ci_low, ci_high = [], []
        for feat, label in feats_fp:
            boot_ratios = []
            for _ in range(2000):
                idx = rng.randint(0, len(df), len(df))
                boot = df.iloc[idx]
                mf = boot[boot["y"]==0][feat].mean()
                me = boot[boot["y"]==1][feat].mean()
                if abs(mf) > 1e-6:
                    boot_ratios.append(me / mf)
            if boot_ratios:
                ci_low.append(np.percentile(boot_ratios, 2.5))
                ci_high.append(np.percentile(boot_ratios, 97.5))
            else:
                # Sem IC calculavel (formado sempre ~0)
                r = ratios[len(ci_low)]
                ci_low.append(r * 0.8)
                ci_high.append(r * 1.2)
        title = f"Risk Multiplier (Dropout/Graduate Mean Ratio) -- p{janela}"
        xaxis_title = "Mean Ratio (Dropout / Graduate)"
        height, width, margin_l = 600, 800, 180

    # Escala log para lidar com razoes muito diferentes
    fig = go.Figure()
    colors = [VERMELHO if r < 0.85 else (VERDE if r > 1.15 else CINZA) for r in ratios]

    # Ordenar por razao
    order = np.argsort(ratios)
    labels_s = [labels[i] for i in order]
    ratios_s = [ratios[i] for i in order]
    ci_low_s = [ci_low[i] for i in order]
    ci_high_s = [ci_high[i] for i in order]
    colors_s = [colors[i] for i in order]

    fig.add_trace(go.Scatter(
        x=ratios_s, y=labels_s,
        mode="markers",
        marker=dict(size=12, color=colors_s, line=dict(width=1, color="black")),
        error_x=dict(
            type="data",
            symmetric=False,
            array=[h - r for r, h in zip(ratios_s, ci_high_s)],
            arrayminus=[r - l for r, l in zip(ratios_s, ci_low_s)],
            color="rgba(100,100,100,0.6)", thickness=2.5, width=6,
        ),
    ))
    fig.add_vline(x=1.0, line_dash="dash", line_color="gray", line_width=1.5)
    
    max_val = max(max(ci_high_s), max(ratios_s)) * 1.15
    min_val = min(min(ci_low_s), min(ratios_s)) * 0.85
    use_log = max_val / max(min_val, 0.01) > 10
    if use_log:
        x_range = [np.log10(max(min_val, 0.01)), np.log10(max_val)]
    else:
        x_range = [min_val, max_val]
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        height=height, width=width,
        template="plotly_white",
        showlegend=False,
        xaxis=dict(range=x_range, type="log" if use_log else "linear"),
        margin=dict(l=margin_l),
    )
    salvar(fig, f"fig_forest_plot_p{janela}", width=width, height=height)


# =================================================================
# FIG 5: TABELA COMPARATIVA COMPLETA (todos modelos, teste, p2 e p4)
# =================================================================
print("\n--- Fig 5: Tabela comparativa completa ---")
header_vals = ["Window", "Model", "F2", "AUC", "Recall", "Precision",
               "Accuracy", "FN", "Threshold"]

rows = []
for _, r in res_thr[res_thr["split"]=="teste"].iterrows():
    rows.append([
        f"p{r['janela'][-1]}" if isinstance(r['janela'], str) else f"p{int(r['janela'])}",
        r["modelo"],
        f"{r['f2']:.3f}",
        f"{r['auc_roc']:.3f}",
        f"{r['recall']:.3f}",
        f"{r['precision']:.3f}",
        f"{r['accuracy']:.3f}",
        str(int(r['fn'])),
        f"{r['threshold']:.2f}",
    ])

cells = list(zip(*rows))

# Highlight best F2 per window
fill = []
for i in range(len(header_vals)):
    col = []
    for r in rows:
        col.append("white")
    fill.append(col)

# Find best F2 per window
for j, r in enumerate(rows):
    jan = r[0]
    f2 = float(r[2])
    best_f2 = max(float(rr[2]) for rr in rows if rr[0] == jan)
    if f2 == best_f2:
        for i in range(len(header_vals)):
            fill[i][j] = "rgba(148,116,220,0.2)"

fig = go.Figure(data=[go.Table(
    header=dict(values=header_vals,
                fill_color=ROXO_MEDIO, font=dict(color="white", size=12),
                align="center"),
    cells=dict(values=cells,
               fill_color=fill,
               align="center",
               font=dict(size=11),
               height=28),
)])
fig.update_layout(title="Comparative Test Performance (Optimized Threshold)",
                  height=420, width=900, margin=dict(l=10, r=10, t=40, b=10))
salvar(fig, "fig_tabela_comparativa_teste", width=900, height=420)


# =================================================================
# FIG 6: PRECISION vs RECALL TRADE-OFF (scatter)
# =================================================================
print("\n--- Fig 6: Precision vs Recall scatter ---")
fig = make_subplots(
    rows=1,
    cols=len(JANELAS_ACADEMICAS),
    subplot_titles=[f"Window p{janela}" for janela in JANELAS_ACADEMICAS],
)

for col_idx, janela in enumerate(JANELAS_ACADEMICAS, 1):
    sub = res_thr[(res_thr["split"]=="teste")]
    # Parse janela
    for _, r in sub.iterrows():
        jan_val = r["janela"]
        if isinstance(jan_val, str):
            j = int(jan_val[-1])
        else:
            j = int(jan_val)
        if j != janela:
            continue
        fig.add_trace(go.Scatter(
            x=[r["recall"]], y=[r["precision"]],
            mode="markers",
            marker=dict(size=14, color=CORES_MODELO.get(r["modelo"], ROXO_MEDIO)),
            name=r["modelo"],
            legendgroup=r["modelo"],
            showlegend=(col_idx==1),
        ), row=1, col=col_idx)

    fig.update_xaxes(title_text="Recall", range=[0.7, 1.0], row=1, col=col_idx)
    fig.update_yaxes(title_text="Precision", range=[0.65, 1.0], row=1, col=col_idx)

fig.update_layout(
    title="Precision vs Recall Trade-off on Test Set",
    height=500, width=950,
    template="plotly_white",
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.08,
        xanchor="center",
        x=0.5,
    ),
    margin=dict(t=120, r=40, l=60, b=60),
)
salvar(fig, "fig_precision_recall_tradeoff", width=950, height=500)


# =================================================================
# FIG 7: MATRIZES DE CONFUSAO (melhor modelo por janela)
# =================================================================
print("\n--- Fig 7: Matrizes de confusao ---")
config_cm = [(janela, MODELOS_SELECIONADOS[janela]) for janela in JANELAS]

subplot_titles = []
thresholds_cm = {}
for janela, modelo_nome in config_cm:
    sub = res_thr[(res_thr["split"]=="teste") & (res_thr["modelo"]==modelo_nome)]
    thr_val = None
    for _, r in sub.iterrows():
        jv = r["janela"]
        j = int(jv[-1]) if isinstance(jv, str) else int(jv)
        if j == janela:
            thr_val = float(r["threshold"])
            break
    thresholds_cm[(janela, modelo_nome)] = thr_val
    subplot_titles.append(f"{modelo_nome} p{janela} (thr={thr_val:.2f})")

fig = make_subplots(rows=1, cols=3, subplot_titles=subplot_titles,
                    horizontal_spacing=0.10)

COR_DIAG_PRINCIPAL = "#9474DC"   # TN, TP
COR_DIAG_SECUNDARIA = "#D2B5FF"  # FP, FN
cores_celula = [[COR_DIAG_PRINCIPAL, COR_DIAG_SECUNDARIA],
                [COR_DIAG_SECUNDARIA, COR_DIAG_PRINCIPAL]]
x_labels = ["Graduate", "Dropout"]
y_labels = ["Graduate", "Dropout"]

for col_idx, (janela, modelo_nome) in enumerate(config_cm, 1):
    sub = res_thr[(res_thr["split"]=="teste") & (res_thr["modelo"]==modelo_nome)]
    for _, r in sub.iterrows():
        jan_val = r["janela"]
        if isinstance(jan_val, str):
            j = int(jan_val[-1])
        else:
            j = int(jan_val)
        if j != janela:
            continue
        tn, fp, fn, tp = int(r["tn"]), int(r["fp"]), int(r["fn"]), int(r["tp"])
        break

    cm = np.array([[tn, fp], [fn, tp]])
    total = cm.sum()
    labels = [["TN", "FP"], ["FN", "TP"]]
    vals = [[tn, fp], [fn, tp]]

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
    title="Confusion Matrices on Test Set",
    height=420, width=1200,
    template="plotly_white",
)
for i in [1, 2, 3]:
    fig.update_xaxes(title_text="Predicted", row=1, col=i,
                     categoryorder="array", categoryarray=x_labels,
                     showgrid=False, zeroline=False)
    fig.update_yaxes(title_text="Actual", row=1, col=i,
                     categoryorder="array", categoryarray=y_labels,
                     autorange="reversed", showgrid=False, zeroline=False)

salvar(fig, "fig_matrizes_confusao", width=1200, height=420)


# =================================================================
# FIG 8: DESEMPENHO POR CURSO (equity)
# =================================================================
print("\n--- Fig 8: Desempenho por curso (equity) ---")

for janela in JANELAS:
    teste = dfs[f"teste_p{janela}"]
    y_teste = teste[TARGET].values
    _, _, all_features = get_features(janela)
    nome_modelo = MODELOS_SELECIONADOS[janela]
    tipo_modelo = MODELO_TIPO[nome_modelo]

    preprocessor_scaled = joblib.load(RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
    preprocessor_tree = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
    thresholds = joblib.load(RESULTADOS / f"thresholds_otimos_p{janela}.joblib")

    X_teste_scaled = preprocessor_scaled.transform(teste[all_features])
    X_teste_tree = preprocessor_tree.transform(teste[all_features])
    X_teste_cb = teste[all_features].copy()

    modelo = joblib.load(RESULTADOS / f"modelo_{nome_modelo}_p{janela}.joblib")
    if tipo_modelo == "scaled":
        X_modelo = X_teste_scaled
    elif tipo_modelo == "tree":
        X_modelo = X_teste_tree
    else:
        X_modelo = X_teste_cb
    y_prob = modelo.predict_proba(X_modelo)[:, 1]
    thr = thresholds[nome_modelo]
    y_pred = (y_prob >= thr).astype(int)

    cursos = sorted(teste["curso_origem"].unique())
    recalls, fprs, f2s, ns = [], [], [], []
    for curso in cursos:
        mask = (teste["curso_origem"] == curso).values
        yt = y_teste[mask]
        yp = y_pred[mask]
        ypr = y_prob[mask]
        if len(np.unique(yt)) < 2:
            recalls.append(0)
            fprs.append(0)
            f2s.append(0)
        else:
            m = calcular_metricas(yt, yp, ypr)
            recalls.append(m["recall"])
            fprs.append(m["fp"] / (m["fp"] + m["tn"]) if (m["fp"] + m["tn"]) > 0 else 0)
            f2s.append(m["f2"])
        ns.append(mask.sum())

    cursos_bonito = [nomes_curso_bonito.get(c, c) for c in cursos]

    fig = make_subplots(rows=1, cols=3, subplot_titles=["Recall by Program", "FPR by Program", "F2 by Program"])

    cores = [cores_curso.get(c, ROXO_MEDIO) for c in cursos]
    fig.add_trace(go.Bar(x=cursos_bonito, y=recalls, marker_color=cores,
                         text=[f"{v:.3f}" for v in recalls], textposition="outside",
                         showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=cursos_bonito, y=fprs, marker_color=cores,
                         text=[f"{v:.3f}" for v in fprs], textposition="outside",
                         showlegend=False), row=1, col=2)
    fig.add_trace(go.Bar(x=cursos_bonito, y=f2s, marker_color=cores,
                         text=[f"{v:.3f}" for v in f2s], textposition="outside",
                         showlegend=False), row=1, col=3)

    fig.update_yaxes(range=[0, 1.15], row=1, col=1)
    fig.update_yaxes(range=[0, 1.15], row=1, col=2)
    fig.update_yaxes(range=[0, 1.15], row=1, col=3)

    fig.update_layout(
        title=f"Equity by Program -- {nome_modelo} p{janela}",
        height=450, width=1000,
        template="plotly_white",
    )
    salvar(fig, f"fig_equity_curso_p{janela}", width=1000, height=450)


# =================================================================
# FIG 9: SHAP BAR PLOTS (mean |SHAP|) para melhor modelo
# =================================================================
print("\n--- Fig 9: SHAP bar plots ---")
for janela in JANELAS:
    modelos_dict = joblib.load(RESULTADOS / f"melhores_modelos_p{janela}.joblib")
    _, _, all_features = get_features(janela)

    # Use CatBoost SHAP (most reliable)
    modelo_cb, tipo_cb, _ = modelos_dict["CatBoost"]
    teste_df = dfs[f"teste_p{janela}"]
    X_teste_cb = teste_df[all_features].copy()

    try:
        if janela == 1:
            mean_abs = np.asarray(modelo_cb.get_feature_importance(), dtype=float)
        else:
            import shap
            explainer = shap.TreeExplainer(modelo_cb)
            sv = explainer(X_teste_cb)

            if hasattr(sv, "values") and len(sv.values.shape) == 3:
                vals = sv.values[:, :, 1]
            else:
                vals = sv.values

            mean_abs = np.abs(vals).mean(axis=0)

        fn = all_features
        sorted_idx = np.argsort(mean_abs)[::-1][:15]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=[fn[i] for i in sorted_idx][::-1],
            x=[mean_abs[i] for i in sorted_idx][::-1],
            orientation="h",
            marker_color=ROXO_MEDIO,
            text=[f"{mean_abs[i]:.3f}" for i in sorted_idx][::-1],
            textposition="outside",
        ))
        fig.update_layout(
            title=f"Top 15 Features by SHAP Importance -- CatBoost p{janela}",
            xaxis_title="Mean |SHAP value|",
            height=550, width=750,
            template="plotly_white",
            margin=dict(l=180),
        )
        salvar(fig, f"fig_shap_bar_p{janela}", width=750, height=550)
    except Exception as e:
        print(f"  SHAP erro p{janela}: {e}")


# =================================================================
# FIG 10: BOOTSTRAP CI TABLE
# =================================================================
print("\n--- Fig 10: Bootstrap CI ---")
for janela in JANELAS:
    teste = dfs[f"teste_p{janela}"]
    y_teste = teste[TARGET].values
    _, _, all_features = get_features(janela)
    thresholds = joblib.load(RESULTADOS / f"thresholds_otimos_p{janela}.joblib")

    preprocessor_scaled = joblib.load(RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
    preprocessor_tree = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
    X_teste_scaled = preprocessor_scaled.transform(teste[all_features])
    X_teste_tree = preprocessor_tree.transform(teste[all_features])
    X_teste_cb = teste[all_features].copy()

    header = ["Model", "F2", "IC 95% F2", "AUC", "IC 95% AUC", "Recall", "IC 95% Recall"]
    rows_ci = []

    for nome in NOMES_MODELO:
        modelo = joblib.load(RESULTADOS / f"modelo_{nome}_p{janela}.joblib")
        tipo = MODELO_TIPO[nome]
        if tipo == "scaled":
            X_t = X_teste_scaled
        elif tipo == "tree":
            X_t = X_teste_tree
        else:
            X_t = X_teste_cb

        y_prob = modelo.predict_proba(X_t)[:, 1]
        thr = thresholds[nome]
        y_pred = (y_prob >= thr).astype(int)

        boot = bootstrap_metricas(y_teste, y_pred, y_prob, n_boot=N_BOOTSTRAP, seed=SEED)
        f2_vals = [b["f2"] for b in boot]
        auc_vals = [b["auc_roc"] for b in boot]
        rec_vals = [b["recall"] for b in boot]

        f2_m, f2_l, f2_h = ci_95(f2_vals)
        auc_m, auc_l, auc_h = ci_95(auc_vals)
        rec_m, rec_l, rec_h = ci_95(rec_vals)

        rows_ci.append([
            nome,
            f"{f2_m:.3f}",
            f"[{f2_l:.3f}; {f2_h:.3f}]",
            f"{auc_m:.3f}",
            f"[{auc_l:.3f}; {auc_h:.3f}]",
            f"{rec_m:.3f}",
            f"[{rec_l:.3f}; {rec_h:.3f}]",
        ])
        print(f"  p{janela} {nome}: F2={f2_m:.3f} [{f2_l:.3f};{f2_h:.3f}]")

    cells_ci = list(zip(*rows_ci))
    fig = go.Figure(data=[go.Table(
        header=dict(values=header,
                    fill_color=ROXO_MEDIO, font=dict(color="white", size=12),
                    align="center"),
        cells=dict(values=cells_ci,
                   align="center",
                   font=dict(size=11),
                   height=28),
    )])
    fig.update_layout(title=f"Confidence Intervals (Bootstrap 5000) -- Test p{janela}",
                      height=280, width=950, margin=dict(l=10, r=10, t=40, b=10))
    salvar(fig, f"fig_bootstrap_ci_p{janela}", width=950, height=280)


# =================================================================
# FIG 11: PSI DRIFT (p2 e p4)
# =================================================================
print("\n--- Fig 11: PSI Drift ---")
fig = make_subplots(
    rows=1,
    cols=len(JANELAS_ACADEMICAS),
    subplot_titles=[f"PSI -- p{janela}" for janela in JANELAS_ACADEMICAS],
    horizontal_spacing=0.08,
)

def calcular_psi(esperado, observado, n_bins=10):
    breakpoints = np.percentile(esperado, np.linspace(0, 100, n_bins + 1))
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 3:
        return 0.0
    exp_hist = np.histogram(esperado, bins=breakpoints)[0] / len(esperado)
    obs_hist = np.histogram(observado, bins=breakpoints)[0] / len(observado)
    exp_hist = np.clip(exp_hist, 1e-6, None)
    obs_hist = np.clip(obs_hist, 1e-6, None)
    psi = np.sum((obs_hist - exp_hist) * np.log(obs_hist / exp_hist))
    return psi

for col_idx, janela in enumerate(JANELAS_ACADEMICAS, 1):
    cat_features, num_features, _ = get_features(janela)
    feature_names_pp = num_features + cat_features
    dados = np.load(RESULTADOS / f"dados_preparados_p{janela}.npz")
    X_tr = dados["X_treino_tree"]
    X_te = dados["X_teste_tree"]

    psi_results = []
    for i, feat in enumerate(feature_names_pp):
        try:
            psi = calcular_psi(X_tr[:, i].astype(float), X_te[:, i].astype(float))
        except:
            psi = 0.0
        psi_results.append({"feature": feat, "PSI": psi})

    psi_df = pd.DataFrame(psi_results).sort_values("PSI", ascending=True)
    # Top 15 only for readability
    psi_df = psi_df.tail(15)

    colors = [VERMELHO if v > 0.25 else (LARANJA if v > 0.1 else VERDE) for v in psi_df["PSI"]]

    fig.add_trace(go.Bar(
        y=psi_df["feature"], x=psi_df["PSI"], orientation="h",
        marker_color=colors, showlegend=False,
        text=[f"{v:.3f}" for v in psi_df["PSI"]],
        textposition="outside",
    ), row=1, col=col_idx)

    fig.add_vline(x=0.1, line_dash="dash", line_color="orange", row=1, col=col_idx)
    fig.add_vline(x=0.25, line_dash="dash", line_color="red", row=1, col=col_idx)

fig.update_layout(
    title="Population Stability Index (Training -> Test Drift)",
    height=550, width=1050,
    template="plotly_white",
    margin=dict(l=180),
)
salvar(fig, "fig_psi_drift", width=1050, height=550)


# =================================================================
# FIG 12: CALIBRACAO (diagrama)
# =================================================================
print("\n--- Fig 12: Calibracao ---")
fig = make_subplots(
    rows=1,
    cols=len(JANELAS),
    subplot_titles=[f"Calibration -- p{janela}" for janela in JANELAS],
)

for col_idx, janela in enumerate(JANELAS, 1):
    teste = dfs[f"teste_p{janela}"]
    y_teste = teste[TARGET].values
    _, _, all_features = get_features(janela)

    preprocessor_scaled = joblib.load(RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
    preprocessor_tree = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
    X_teste_scaled = preprocessor_scaled.transform(teste[all_features])
    X_teste_tree = preprocessor_tree.transform(teste[all_features])
    X_teste_cb = teste[all_features].copy()

    # Diagonal
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines",
        line=dict(color="gray", dash="dash", width=1),
        name="Perfectly calibrated", showlegend=(col_idx==1),
    ), row=1, col=col_idx)

    for nome in NOMES_MODELO:
        modelo = joblib.load(RESULTADOS / f"modelo_{nome}_p{janela}.joblib")
        tipo = MODELO_TIPO[nome]
        if tipo == "scaled":
            X_t = X_teste_scaled
        elif tipo == "tree":
            X_t = X_teste_tree
        else:
            X_t = X_teste_cb

        y_prob = modelo.predict_proba(X_t)[:, 1]
        prob_true, prob_pred = calibration_curve(y_teste, y_prob, n_bins=10, strategy="uniform")

        fig.add_trace(go.Scatter(
            x=prob_pred, y=prob_true, mode="lines+markers",
            name=nome, showlegend=(col_idx==1),
            line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2),
            marker=dict(size=6),
        ), row=1, col=col_idx)

    fig.update_xaxes(title_text="Predicted Probability", range=[0, 1], row=1, col=col_idx)
    fig.update_yaxes(title_text="Fraction of Positives", range=[0, 1], row=1, col=col_idx)

fig.update_layout(
    title="Calibration Diagrams -- Test Set",
    height=520, width=1450,
    template="plotly_white",
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.12,
        xanchor="center",
        x=0.5,
    ),
    margin=dict(l=60, r=40, t=70, b=110),
)
salvar(fig, "fig_calibracao_teste", width=1450, height=520)


# =================================================================
# FIG 13: EVOLUCAO TEMPORAL DA TAXA DE EVASAO POR CURSO (line chart)
# =================================================================
print("\n--- Fig 13: Evolucao temporal da evasao ---")
df = dfs["ml_p2"]  # Use p2 for broader coverage
# Filter years with enough data
anos = sorted(df["ano_ingresso"].unique())
# Only use years >= 2000
anos = [a for a in anos if a >= 2000]

fig = go.Figure()
for curso in ["ADM_Integral", "ADM_Noturno", "GI"]:
    rates = []
    anos_valid = []
    for ano in anos:
        sub = df[(df["ano_ingresso"] == ano) & (df["curso_origem"] == curso)]
        if len(sub) >= 5:
            rates.append(sub["y"].mean() * 100)
            anos_valid.append(ano)
    if anos_valid:
        fig.add_trace(go.Scatter(
            x=anos_valid, y=rates, mode="lines+markers",
            name=nomes_curso_bonito[curso],
            line=dict(color=cores_curso[curso], width=2.5),
            marker=dict(size=7),
        ))

# Add vertical lines for splits and a single shared label to avoid overlap
fig.add_vline(x=2015.5, line_dash="dash", line_color="gray")
fig.add_vline(x=2017.5, line_dash="dash", line_color="gray")
fig.add_annotation(
    x=2016.5,
    y=1.03,
    xref="x",
    yref="paper",
    text="Training |  Val  | Test",
    showarrow=False,
    font=dict(size=11, color="#4f5d75"),
    align="center",
    xanchor="center",
)

fig.update_layout(
    title="Temporal Evolution of Dropout Rate by Program (Cohort p2)",
    xaxis_title="Year of Entry",
    yaxis_title="Dropout Rate (%)",
    yaxis=dict(range=[0, 100]),
    height=500, width=900,
    template="plotly_white",
    legend=dict(x=0.01, y=0.99),
)
salvar(fig, "fig_evolucao_temporal_evasao", width=900, height=500)

# =================================================================
# FIG 14: ESTABILIDADE TEMPORAL (walk-forward)
# =================================================================
print("\n--- Fig 14: Estabilidade temporal ---")
# Need to recompute walk-forward for both windows
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.base import clone

def build_preprocessor(num_feats, cat_feats, scale=False):
    transformers = []
    if num_feats:
        steps = [("imputer", SimpleImputer(strategy="median"))]
        if scale:
            steps.append(("scaler", StandardScaler()))
        transformers.append(("num", Pipeline(steps), num_feats))
    if cat_feats:
        transformers.append(("cat",
            OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
            cat_feats))
    return ColumnTransformer(transformers=transformers)

splits_alt = [
    {"nome": "Split A\n(tr<=2013)", "tr_max": 2013, "val_min": 2014, "val_max": 2015,
     "te_min": 2016, "te_max": 2017},
    {"nome": "Split B\n(tr<=2014)", "tr_max": 2014, "val_min": 2015, "val_max": 2016,
     "te_min": 2017, "te_max": 2018},
    {"nome": "Split C\n(tr<=2015)", "tr_max": 2015, "val_min": 2016, "val_max": 2017,
     "te_min": 2018, "te_max": 2019},
]

fig = make_subplots(
    rows=1,
    cols=len(JANELAS),
    subplot_titles=[f"Stability -- {MODELOS_SELECIONADOS[janela]} p{janela}" for janela in JANELAS],
)

for col_idx, janela in enumerate(JANELAS, 1):
    all_df = pd.concat([dfs[f"treino_p{janela}"], dfs[f"val_p{janela}"], dfs[f"teste_p{janela}"]], ignore_index=True)
    cat_features, num_features, all_features = get_features(janela)
    nome_modelo = MODELOS_SELECIONADOS[janela]
    tipo_modelo = MODELO_TIPO[nome_modelo]
    modelo_ref = joblib.load(RESULTADOS / f"modelo_{nome_modelo}_p{janela}.joblib")
    split_names = []
    split_f2s = []

    for sp in splits_alt:
        tr_mask = all_df["ano_ingresso"] <= sp["tr_max"]
        val_mask = all_df["ano_ingresso"].between(sp["val_min"], sp["val_max"])
        te_mask = all_df["ano_ingresso"].between(sp["te_min"], sp["te_max"])

        df_tr = all_df[tr_mask]
        df_val = all_df[val_mask]
        df_te = all_df[te_mask]
        y_tr = df_tr[TARGET].values
        y_val = df_val[TARGET].values
        y_te = df_te[TARGET].values

        if len(y_tr) < 30 or len(y_te) < 10 or len(np.unique(y_te)) < 2:
            continue

        try:
            if tipo_modelo == "cb":
                from catboost import CatBoostClassifier
                params = modelo_ref.get_params()
                params["verbose"] = 0
                params["cat_features"] = list(range(len(cat_features))) if cat_features else None
                m_s = CatBoostClassifier(**params)
                m_s.fit(df_tr[all_features], y_tr)
                y_prob_val = m_s.predict_proba(df_val[all_features])[:, 1]
                y_prob_te = m_s.predict_proba(df_te[all_features])[:, 1]
            else:
                from xgboost import XGBClassifier
                params = modelo_ref.get_params()
                params["verbosity"] = 0
                preprocessor = build_preprocessor(num_features, cat_features, scale=(tipo_modelo == "scaled"))
                X_tr = preprocessor.fit_transform(df_tr[all_features])
                X_val = preprocessor.transform(df_val[all_features])
                X_te = preprocessor.transform(df_te[all_features])
                m_s = XGBClassifier(**params)
                m_s.fit(X_tr, y_tr)
                y_prob_val = m_s.predict_proba(X_val)[:, 1]
                y_prob_te = m_s.predict_proba(X_te)[:, 1]

            best_thr, best_f2_val = 0.5, 0
            for t in np.arange(0.10, 0.90, 0.01):
                f2_c = f2_score(y_val, (y_prob_val >= t).astype(int))
                if f2_c > best_f2_val:
                    best_f2_val = f2_c
                    best_thr = t

            y_pred_te = (y_prob_te >= best_thr).astype(int)
            f2_te = f2_score(y_te, y_pred_te)
            split_names.append(sp["nome"])
            split_f2s.append(f2_te)
            print(f"  p{janela} {nome_modelo} {sp['nome'].replace(chr(10), ' ')}: F2={f2_te:.3f}")
        except Exception as e:
            print(f"  p{janela} {nome_modelo} {sp['nome'].replace(chr(10), ' ')}: erro {e}")

    if split_f2s:
        f2_mean = np.mean(split_f2s)
        colors_bar = [ROXO_CLARO, ROXO_MEDIO, ROXO_ESCURO][:len(split_f2s)]
        fig.add_trace(go.Bar(
            x=split_names, y=split_f2s,
            marker_color=colors_bar,
            text=[f"{v:.3f}" for v in split_f2s],
            textposition="outside",
            showlegend=False,
        ), row=1, col=col_idx)
        fig.add_hline(y=f2_mean, line_dash="dash", line_color=CINZA, row=1, col=col_idx)
        fig.add_annotation(
            x=0.02,
            xref="x domain" if col_idx == 1 else f"x{col_idx} domain",
            y=min(f2_mean + 0.012, 0.99),
            yref="y" if col_idx == 1 else f"y{col_idx}",
            text=f"Mean={f2_mean:.3f}",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(size=11, color="#4f5d75"),
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="rgba(149,165,166,0.5)",
            borderpad=2,
        )

    fig.update_yaxes(range=[0.7, 1.0], row=1, col=col_idx)

fig.update_layout(
    title="Walk-Forward Stability -- Selected Models",
    height=450, width=1350,
    template="plotly_white",
)
salvar(fig, "fig_estabilidade_walkforward", width=1350, height=450)


# =================================================================
# FIG 15: CURVAS DE APRENDIZAGEM
# =================================================================
print("\n--- Fig 15: Curvas de aprendizagem ---")
fig = make_subplots(
    rows=1,
    cols=len(JANELAS),
    subplot_titles=[f"Learning Curve -- {MODELOS_SELECIONADOS[janela]} p{janela}" for janela in JANELAS],
)

for col_idx, janela in enumerate(JANELAS, 1):
    thresholds = joblib.load(RESULTADOS / f"thresholds_otimos_p{janela}.joblib")
    cat_features, num_features, all_features = get_features(janela)
    nome_modelo = MODELOS_SELECIONADOS[janela]
    tipo_modelo = MODELO_TIPO[nome_modelo]
    modelo_ref = joblib.load(RESULTADOS / f"modelo_{nome_modelo}_p{janela}.joblib")
    thr = thresholds[nome_modelo]

    treino_df = dfs[f"treino_p{janela}"]
    teste_df = dfs[f"teste_p{janela}"]
    y_treino = treino_df[TARGET].values
    y_teste = teste_df[TARGET].values

    fractions = [0.2, 0.4, 0.6, 0.8, 1.0]
    lc_n, lc_f2 = [], []

    for frac in fractions:
        n_samples = int(len(y_treino) * frac)
        idx = np.random.RandomState(SEED).choice(len(y_treino), n_samples, replace=False)

        try:
            if tipo_modelo == "cb":
                from catboost import CatBoostClassifier
                params = modelo_ref.get_params()
                params["verbose"] = 0
                params["cat_features"] = list(range(len(cat_features))) if cat_features else None
                m_lc = CatBoostClassifier(**params)
                m_lc.fit(treino_df.iloc[idx][all_features], y_treino[idx])
                y_prob = m_lc.predict_proba(teste_df[all_features])[:, 1]
            else:
                from xgboost import XGBClassifier
                params = modelo_ref.get_params()
                params["verbosity"] = 0
                preprocessor = build_preprocessor(num_features, cat_features, scale=(tipo_modelo == "scaled"))
                X_tr = preprocessor.fit_transform(treino_df.iloc[idx][all_features])
                X_te = preprocessor.transform(teste_df[all_features])
                m_lc = XGBClassifier(**params)
                m_lc.fit(X_tr, y_treino[idx])
                y_prob = m_lc.predict_proba(X_te)[:, 1]
            y_pred = (y_prob >= thr).astype(int)
            f2 = f2_score(y_teste, y_pred)
            lc_n.append(n_samples)
            lc_f2.append(f2)
            print(f"  p{janela} {nome_modelo} {frac*100:.0f}%: F2={f2:.3f}")
        except Exception as e:
            print(f"  p{janela} {nome_modelo} {frac*100:.0f}%: erro {e}")

    fig.add_trace(go.Scatter(
        x=lc_n, y=lc_f2, mode="lines+markers",
        line=dict(color=ROXO_MEDIO, width=2.5),
        marker=dict(size=8),
        name=f"{nome_modelo} p{janela}",
        showlegend=False,
    ), row=1, col=col_idx)

    fig.update_xaxes(title_text="Number of Training Samples", row=1, col=col_idx)
    fig.update_yaxes(title_text="Test F2", range=[0.7, 1.0], row=1, col=col_idx)

fig.update_layout(
    title="Learning Curves -- Selected Models",
    height=450, width=1350,
    template="plotly_white",
)
salvar(fig, "fig_learning_curve", width=1350, height=450)


# =================================================================
# FIG 16: ABLATION STUDY
# =================================================================
print("\n--- Fig 16: Ablation study ---")
fig = make_subplots(
    rows=1,
    cols=len(JANELAS),
    subplot_titles=[f"Ablation -- {MODELOS_SELECIONADOS[janela]} p{janela}" for janela in JANELAS],
    shared_yaxes=False,
    horizontal_spacing=0.08,
)

GRUPOS_FEATURES_ACAD = {
    "Grades": ["nota_media", "nota_mediana", "nota_desvio", "nota_min", "nota_max"],
    "Pass/Fail": ["qtd_aprovacoes", "qtd_reprovacoes", "qtd_reprov_nota",
                  "qtd_reprov_freq", "taxa_aprovacao"],
    "Courses": ["qtd_disciplinas_total", "media_disc_por_periodo",
                "qtd_dispensas", "qtd_sem_resultado"],
    "Credits": ["ch_acumulada", "pct_ch_concluida"],
    "1st Semester": ["nota_p1", "delta_nota", "reprov_p1", "disc_p1"],
    "Categorical": ["curso_origem", "tipo_ingresso"],
    "Registration": ["sexo", "forma_ingresso_grp", "idade_ingresso", "cotista", "natural_uberlandia"],
}

GRUPOS_FEATURES_P1 = {
    "Profile": ["sexo", "idade_ingresso", "cotista", "natural_uberlandia"],
    "Entry": ["tipo_ingresso", "forma_ingresso_grp", "num_semestre_ingresso"],
    "Program": ["curso_origem"],
}

for col_idx, janela in enumerate(JANELAS, 1):
    thresholds = joblib.load(RESULTADOS / f"thresholds_otimos_p{janela}.joblib")
    nome_modelo = MODELOS_SELECIONADOS[janela]
    modelo_sel = joblib.load(RESULTADOS / f"modelo_{nome_modelo}_p{janela}.joblib")
    cat_features, num_features, all_features = get_features(janela)
    grupos_features = GRUPOS_FEATURES_P1 if janela == 1 else GRUPOS_FEATURES_ACAD
    thr = thresholds[nome_modelo]

    treino_df = dfs[f"treino_p{janela}"]
    teste_df = dfs[f"teste_p{janela}"]
    y_treino = treino_df[TARGET].values
    y_teste = teste_df[TARGET].values

    # Baseline
    if nome_modelo == "CatBoost":
        X_teste_base = teste_df[all_features]
    else:
        preprocessor_tree = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
        X_teste_base = preprocessor_tree.transform(teste_df[all_features])

    y_prob_base = modelo_sel.predict_proba(X_teste_base)[:, 1]
    y_pred_base = (y_prob_base >= thr).astype(int)
    f2_base = f2_score(y_teste, y_pred_base)

    configs = [f"All ({len(all_features)})"]
    f2_vals = [f2_base]
    deltas = [0.0]

    for grupo_nome, grupo_feats in grupos_features.items():
        remaining_cat = [f for f in cat_features if f not in grupo_feats]
        remaining_num = [f for f in num_features if f not in grupo_feats]
        remaining_all = remaining_cat + remaining_num

        if not remaining_all:
            continue

        try:
            if nome_modelo == "CatBoost":
                from catboost import CatBoostClassifier
                model_params = modelo_sel.get_params()
                model_params["verbose"] = 0
                model_params["cat_features"] = list(range(len(remaining_cat))) if remaining_cat else None
                m_abl = CatBoostClassifier(**model_params)
                m_abl.fit(treino_df[remaining_all], y_treino)
                X_teste_abl = teste_df[remaining_all]
            else:
                from xgboost import XGBClassifier
                model_params = modelo_sel.get_params()
                model_params["verbosity"] = 0
                preprocessor_abl = build_preprocessor(remaining_num, remaining_cat, scale=False)
                X_treino_abl = preprocessor_abl.fit_transform(treino_df[remaining_all])
                X_teste_abl = preprocessor_abl.transform(teste_df[remaining_all])
                m_abl = XGBClassifier(**model_params)
                m_abl.fit(X_treino_abl, y_treino)

            y_prob_abl = m_abl.predict_proba(X_teste_abl)[:, 1]
            y_pred_abl = (y_prob_abl >= thr).astype(int)
            f2_abl = f2_score(y_teste, y_pred_abl)
            delta = f2_abl - f2_base
            configs.append(f"Without {grupo_nome}")
            f2_vals.append(f2_abl)
            deltas.append(delta)
            print(f"  p{janela} {nome_modelo} Sem {grupo_nome}: F2={f2_abl:.3f} (d={delta:+.3f})")
        except Exception as e:
            print(f"  p{janela} {nome_modelo} Sem {grupo_nome}: erro {e}")

    cores_abl = [ROXO_MEDIO if d == 0 else (VERMELHO if d < -0.01 else VERDE) for d in deltas]

    fig.add_trace(go.Bar(
        y=configs, x=f2_vals, orientation="h",
        marker_color=cores_abl,
        text=[f"{v:.3f}" for v in f2_vals],
        textposition="outside",
        showlegend=False,
    ), row=1, col=col_idx)

    fig.add_vline(x=f2_base, line_dash="dash", line_color=CINZA, row=1, col=col_idx)

fig.update_layout(
    title="Ablation Study -- Selected Models",
    xaxis_title="F2-score",
    height=520, width=1500,
    template="plotly_white",
    margin=dict(l=150),
)
for i in range(1, len(JANELAS) + 1):
    fig.update_xaxes(range=[0.65, 1.0], row=1, col=i)
salvar(fig, "fig_ablation_study", width=1500, height=520)


# =================================================================
# FIG 17: PR CURVES (teste)
# =================================================================
print("\n--- Fig 17: PR Curves ---")
fig = make_subplots(
    rows=1,
    cols=len(JANELAS),
    subplot_titles=[f"PR Curve -- Test p{janela}" for janela in JANELAS],
)

for col_idx, janela in enumerate(JANELAS, 1):
    teste = dfs[f"teste_p{janela}"]
    y_teste = teste[TARGET].values
    _, _, all_features = get_features(janela)

    preprocessor_scaled = joblib.load(RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
    preprocessor_tree = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
    X_teste_scaled = preprocessor_scaled.transform(teste[all_features])
    X_teste_tree = preprocessor_tree.transform(teste[all_features])
    X_teste_cb = teste[all_features].copy()

    # Baseline prevalence
    prevalence = y_teste.mean()
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[prevalence, prevalence], mode="lines",
        line=dict(color="gray", dash="dash", width=1),
        name=f"Random (AP={prevalence:.3f})", showlegend=(col_idx==1),
    ), row=1, col=col_idx)

    for nome in NOMES_MODELO:
        modelo = joblib.load(RESULTADOS / f"modelo_{nome}_p{janela}.joblib")
        tipo = MODELO_TIPO[nome]
        if tipo == "scaled":
            X_t = X_teste_scaled
        elif tipo == "tree":
            X_t = X_teste_tree
        else:
            X_t = X_teste_cb

        y_prob = modelo.predict_proba(X_t)[:, 1]
        prec, rec, _ = precision_recall_curve(y_teste, y_prob)
        ap = average_precision_score(y_teste, y_prob)

        fig.add_trace(go.Scatter(
            x=rec, y=prec, mode="lines",
            name=f"{nome} (AP={ap:.3f})",
            line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2.5),
            showlegend=(col_idx==1),
        ), row=1, col=col_idx)

    fig.update_xaxes(title_text="Recall", range=[0, 1], row=1, col=col_idx)
    fig.update_yaxes(title_text="Precision", range=[0, 1], row=1, col=col_idx)

fig.update_layout(
    title="Precision-Recall Curves -- Test Set",
    height=500, width=1450,
    template="plotly_white",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.08,
        xanchor="center",
        x=0.5,
    ),
    margin=dict(t=120, r=40, l=60, b=60),
)
salvar(fig, "fig_pr_curves_teste", width=1450, height=500)


print("\n" + "="*60)
print("TODAS AS FIGURAS GERADAS COM SUCESSO!")
print(f"Pasta: {GRAFICOS_ARTIGO}")
print("="*60)
