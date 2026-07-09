"""Compute equity-by-curso, Top-K precision, and SHAP top-features for p1 (CatBoost)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import fbeta_score, recall_score, precision_score

from config_modelagem import DADOS, RESULTADOS, get_features

JANELA = 1
MODELO = "CatBoost"

teste = pd.read_parquet(DADOS / f"teste_p{JANELA}.parquet")
cat_feats, num_feats, feats_all = get_features(JANELA)
y = teste["y"].astype(int).values

modelo = joblib.load(RESULTADOS / f"modelo_{MODELO}_p{JANELA}.joblib")
thresholds = joblib.load(RESULTADOS / f"thresholds_otimos_p{JANELA}.joblib")
thr = float(thresholds[MODELO])

X = teste[feats_all]
proba = modelo.predict_proba(X)[:, 1]
pred = (proba >= thr).astype(int)

print(f"\n=== p{JANELA} {MODELO} (thr={thr:.3f}) ===")
print(f"n_teste={len(y)}  evadidos={int(y.sum())}  taxa={y.mean():.3f}")
print(f"F2={fbeta_score(y, pred, beta=2):.4f}  recall={recall_score(y, pred):.4f}  precision={precision_score(y, pred):.4f}")

print("\n--- Equidade por curso (p1) ---")
if "curso_origem" in teste.columns:
    for curso, sub in teste.groupby("curso_origem"):
        idx = sub.index
        ys = y[teste.index.isin(idx)]
        ps = pred[teste.index.isin(idx)]
        if len(ys) == 0 or ys.sum() == 0:
            continue
        f2 = fbeta_score(ys, ps, beta=2, zero_division=0)
        rec = recall_score(ys, ps, zero_division=0)
        prec = precision_score(ys, ps, zero_division=0)
        fpr = ((ps == 1) & (ys == 0)).sum() / max(1, (ys == 0).sum())
        print(f"  {curso}: n={len(ys)} pos={int(ys.sum())} F2={f2:.4f} recall={rec:.4f} prec={prec:.4f} FPR={fpr:.4f}")

print("\n--- Top-K precision (p1) ---")
order = np.argsort(-proba)
for k in [50, 100, 150, 200]:
    if k > len(order):
        continue
    top = order[:k]
    prec_k = y[top].mean()
    print(f"  Top-{k}: precision={prec_k:.4f}  ({int(y[top].sum())}/{k} verdadeiros evadidos)")

print("\n--- SHAP top features (p1, CatBoost) ---")
try:
    shap_vals = modelo.get_feature_importance(type="ShapValues", data=X)
    shap_vals = shap_vals[:, :-1]
    mean_abs = np.abs(shap_vals).mean(axis=0)
    ranking = sorted(zip(feats_all, mean_abs), key=lambda x: -x[1])
    for f, v in ranking:
        print(f"  {f}: {v:.4f}")
except Exception as e:
    print(f"  ERRO SHAP: {e}")
    importances = modelo.get_feature_importance()
    ranking = sorted(zip(feats_all, importances), key=lambda x: -x[1])
    print("  Fallback - feature_importance padrao:")
    for f, v in ranking:
        print(f"  {f}: {v:.4f}")
