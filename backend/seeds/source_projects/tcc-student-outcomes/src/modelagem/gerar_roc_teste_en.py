from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import roc_auc_score, roc_curve

from config_modelagem import DADOS, RESULTADOS, TARGET, CORES_MODELO, ROXO_MEDIO, get_features


PROJETO = Path(__file__).resolve().parents[2]
OUT_DIR = PROJETO / "article" / "Images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELO_TIPO = {
    "LR": "scaled",
    "RF": "tree",
    "XGBoost": "tree",
    "CatBoost": "cb",
    "MLP": "scaled",
}


def salvar(fig: go.Figure, nome: str) -> None:
    fig.write_image(str(OUT_DIR / f"{nome}.png"), width=700, height=550, scale=2)
    fig.write_html(str(OUT_DIR / f"{nome}.html"), include_plotlyjs="cdn")
    print(f"  Saved: {nome}.png")


def carregar_x_teste(teste: pd.DataFrame, janela: int, tipo: str):
    _, _, all_features = get_features(janela)
    if tipo == "scaled":
        pre = joblib.load(RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
        return pre.transform(teste[all_features])
    if tipo == "tree":
        pre = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
        return pre.transform(teste[all_features])
    return teste[all_features].copy()


for janela in [1, 2, 4]:
    print(f"\nGenerating test ROC curves -- p{janela}")
    teste = pd.read_parquet(DADOS / f"teste_p{janela}.parquet")
    y_teste = teste[TARGET].values

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            line=dict(color="gray", dash="dash", width=1),
            name="Random (AUC=0.500)",
            showlegend=True,
        )
    )

    for nome, tipo in MODELO_TIPO.items():
        modelo = joblib.load(RESULTADOS / f"modelo_{nome}_p{janela}.joblib")
        X_t = carregar_x_teste(teste, janela, tipo)
        y_prob = modelo.predict_proba(X_t)[:, 1]
        fpr, tpr, _ = roc_curve(y_teste, y_prob)
        auc = roc_auc_score(y_teste, y_prob)

        fig.add_trace(
            go.Scatter(
                x=fpr,
                y=tpr,
                mode="lines",
                name=f"{nome} (AUC={auc:.3f})",
                line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2.5),
            )
        )
        print(f"  {nome}: AUC = {auc:.3f}")

    subtitle = "registration features only" if janela == 1 else f"window p{janela}"
    fig.update_layout(
        title=f"ROC Curve -- Test Set p{janela} ({subtitle})",
        xaxis_title="FPR (False Positive Rate)",
        yaxis_title="TPR (True Positive Rate / Recall)",
        height=550,
        width=700,
        legend=dict(x=0.52, y=0.05, bgcolor="rgba(255,255,255,0.85)"),
        template="plotly_white",
    )
    salvar(fig, f"roc_teste_p{janela}_en")


print("\nDone.")
