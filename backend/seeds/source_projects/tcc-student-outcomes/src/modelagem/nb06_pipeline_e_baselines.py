import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

from config_modelagem import (DADOS, RESULTADOS, TARGET, META_COLS, SEED, JANELAS,
                               calcular_metricas, f2_score, get_features)

resultados_todos = []

for janela in JANELAS:
    print(f"\n{'='*70}")
    print(f"JANELA p{janela}")
    print(f"{'='*70}")

    CAT_FEATURES, NUM_FEATURES, ALL_FEATURES = get_features(janela)

    treino = pd.read_parquet(DADOS / f"treino_p{janela}.parquet")
    val = pd.read_parquet(DADOS / f"val_p{janela}.parquet")
    teste = pd.read_parquet(DADOS / f"teste_p{janela}.parquet")

    print(f"Treino: {len(treino)} | Val: {len(val)} | Teste: {len(teste)}")
    print(f"Taxa evasao treino: {treino[TARGET].mean()*100:.1f}%")
    print(f"Taxa evasao val: {val[TARGET].mean()*100:.1f}%")
    print(f"Taxa evasao teste: {teste[TARGET].mean()*100:.1f}%")
    print(f"Features: {len(ALL_FEATURES)} ({len(CAT_FEATURES)} cat + {len(NUM_FEATURES)} num)")

    X_treino = treino[ALL_FEATURES].copy()
    y_treino = treino[TARGET].values
    X_val = val[ALL_FEATURES].copy()
    y_val = val[TARGET].values
    X_teste = teste[ALL_FEATURES].copy()
    y_teste = teste[TARGET].values

    preprocessor_scaled = ColumnTransformer(
        transformers=[
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]), NUM_FEATURES),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value",
                                    unknown_value=-1), CAT_FEATURES),
        ],
        remainder="drop",
    )

    preprocessor_tree = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), NUM_FEATURES),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value",
                                    unknown_value=-1), CAT_FEATURES),
        ],
        remainder="drop",
    )

    preprocessor_scaled.fit(X_treino)
    preprocessor_tree.fit(X_treino)

    X_treino_scaled = preprocessor_scaled.transform(X_treino)
    X_val_scaled = preprocessor_scaled.transform(X_val)
    X_teste_scaled = preprocessor_scaled.transform(X_teste)

    X_treino_tree = preprocessor_tree.transform(X_treino)
    X_val_tree = preprocessor_tree.transform(X_val)
    X_teste_tree = preprocessor_tree.transform(X_teste)

    print(f"\nX_treino_scaled shape: {X_treino_scaled.shape}")
    print(f"X_treino_tree shape: {X_treino_tree.shape}")
    print(f"Nulos apos imputacao (scaled): {np.isnan(X_treino_scaled).sum()}")
    print(f"Nulos apos imputacao (tree): {np.isnan(X_treino_tree).sum()}")

    joblib.dump(preprocessor_scaled, RESULTADOS / f"preprocessor_scaled_p{janela}.joblib")
    joblib.dump(preprocessor_tree, RESULTADOS / f"preprocessor_tree_p{janela}.joblib")
    print(f"Preprocessadores salvos para p{janela}")

    dummy = DummyClassifier(strategy="most_frequent", random_state=SEED)
    dummy.fit(X_treino_scaled, y_treino)

    for nome_split, X_sp, y_sp in [("val", X_val_scaled, y_val),
                                     ("teste", X_teste_scaled, y_teste)]:
        y_pred = dummy.predict(X_sp)
        y_prob = np.full(len(y_sp), y_treino.mean())
        m = calcular_metricas(y_sp, y_pred, y_prob)
        m.update({"modelo": "Dummy", "janela": f"p{janela}", "split": nome_split,
                  "threshold": 0.5})
        resultados_todos.append(m)
        print(f"\n  Dummy ({nome_split} p{janela}): F2={m['f2']:.3f} | "
              f"AUC={m['auc_roc']:.3f} | Recall={m['recall']:.3f}")

    lr_base = LogisticRegression(random_state=SEED, max_iter=1000,
                                  class_weight="balanced")
    lr_base.fit(X_treino_scaled, y_treino)

    for nome_split, X_sp, y_sp in [("val", X_val_scaled, y_val),
                                     ("teste", X_teste_scaled, y_teste)]:
        y_prob = lr_base.predict_proba(X_sp)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)
        m = calcular_metricas(y_sp, y_pred, y_prob)
        m.update({"modelo": "LR_base", "janela": f"p{janela}", "split": nome_split,
                  "threshold": 0.5})
        resultados_todos.append(m)
        print(f"\n  LR_base ({nome_split} p{janela}): F2={m['f2']:.3f} | "
              f"AUC={m['auc_roc']:.3f} | Recall={m['recall']:.3f} | "
              f"Precision={m['precision']:.3f}")

    feature_names = NUM_FEATURES + CAT_FEATURES
    coefs = pd.DataFrame({
        "feature": feature_names,
        "coef": lr_base.coef_[0],
        "abs_coef": np.abs(lr_base.coef_[0]),
    }).sort_values("abs_coef", ascending=False)
    print(f"\n  Top-10 coeficientes LR_base (p{janela}):")
    for _, row in coefs.head(10).iterrows():
        sinal = "+" if row["coef"] > 0 else "-"
        print(f"    {sinal} {row['feature']:<25} {row['coef']:>+.4f}")

    np.savez(RESULTADOS / f"dados_preparados_p{janela}.npz",
             X_treino_scaled=X_treino_scaled, X_val_scaled=X_val_scaled,
             X_teste_scaled=X_teste_scaled,
             X_treino_tree=X_treino_tree, X_val_tree=X_val_tree,
             X_teste_tree=X_teste_tree,
             y_treino=y_treino, y_val=y_val, y_teste=y_teste)

df_res = pd.DataFrame(resultados_todos)
df_res.to_csv(RESULTADOS / "resultados_baselines.csv", index=False)

print("\n" + "=" * 80)
print("RESUMO DOS BASELINES")
print("=" * 80)

for janela in [f"p{j}" for j in JANELAS]:
    print(f"\n--- {janela.upper()} ---")
    sub = df_res[df_res["janela"] == janela]
    print(f"{'Modelo':<12} {'Split':<8} {'F2':>6} {'AUC':>6} {'Recall':>7} "
          f"{'Prec':>6} {'F1':>6} {'Brier':>6}")
    print("-" * 65)
    for _, row in sub.iterrows():
        print(f"{row['modelo']:<12} {row['split']:<8} {row['f2']:>6.3f} "
              f"{row['auc_roc']:>6.3f} {row['recall']:>7.3f} "
              f"{row['precision']:>6.3f} {row['f1']:>6.3f} {row['brier']:>6.3f}")

print("\nNotebook 06 concluido.")
