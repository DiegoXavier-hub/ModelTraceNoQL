"""
Gera 2 graficos:
  - roc_teste_p2.png: Curvas ROC dos 5 modelos no teste p2
  - roc_teste_p4.png: Curvas ROC dos 5 modelos no teste p4
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from sklearn.metrics import roc_curve, roc_auc_score

from config_modelagem import (DADOS, RESULTADOS, GRAFICOS, ALL_FEATURES,
                               CAT_FEATURES, NUM_FEATURES, TARGET,
                               CORES_MODELO, ROXO_MEDIO, salvar_fig)

MODELO_TIPO = {
    "LR":       "scaled",
    "RF":       "tree",
    "XGBoost":  "tree",
    "CatBoost": "cb",
    "MLP":      "scaled",
}

for janela in [2, 4]:
    print(f"\n{'='*50}")
    print(f"  Gerando ROC Teste -- p{janela}")
    print(f"{'='*50}")

    teste = pd.read_parquet(DADOS / f"teste_p{janela}.parquet")
    y_teste = teste[TARGET].values

    preprocessor_scaled = joblib.load(RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
    preprocessor_tree = joblib.load(RESULTADOS / f"preprocessor_tree_p{janela}.joblib")

    X_teste_scaled = preprocessor_scaled.transform(teste[ALL_FEATURES])
    X_teste_tree = preprocessor_tree.transform(teste[ALL_FEATURES])
    X_teste_cb = teste[ALL_FEATURES].copy()

    fig_roc = go.Figure()

    fig_roc.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines",
        line=dict(color="gray", dash="dash", width=1),
        name="Aleatorio (AUC=0.500)",
        showlegend=True,
    ))

    for nome, tipo in MODELO_TIPO.items():
        modelo = joblib.load(RESULTADOS / f"modelo_{nome}_p{janela}.joblib")

        if tipo == "scaled":
            X_t = X_teste_scaled
        elif tipo == "tree":
            X_t = X_teste_tree
        else:
            X_t = X_teste_cb

        y_prob = modelo.predict_proba(X_t)[:, 1]
        fpr, tpr, _ = roc_curve(y_teste, y_prob)
        auc = roc_auc_score(y_teste, y_prob)

        fig_roc.add_trace(go.Scatter(
            x=fpr, y=tpr, mode="lines",
            name=f"{nome} (AUC={auc:.3f})",
            line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2.5),
        ))

        print(f"  {nome}: AUC = {auc:.3f}")

    fig_roc.update_layout(
        title=f"Curva ROC -- Teste p{janela}",
        xaxis_title="FPR (Taxa de Falsos Positivos)",
        yaxis_title="TPR (Taxa de Verdadeiros Positivos / Recall)",
        height=550,
        width=700,
        legend=dict(x=0.55, y=0.05, bgcolor="rgba(255,255,255,0.8)"),
        template="plotly_white",
    )

    salvar_fig(fig_roc, f"roc_teste_p{janela}", width=700, height=550)
    print(f"  Salvo: roc_teste_p{janela}.png")

print("\nConcluido!")
