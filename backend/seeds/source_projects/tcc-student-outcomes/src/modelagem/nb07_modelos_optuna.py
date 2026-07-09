import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import joblib
import optuna
import warnings
warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

from config_modelagem import (DADOS, RESULTADOS, TARGET, SEED, OPTUNA_TRIALS,
                               JANELAS, calcular_metricas, f2_score, get_features)

resultados_todos = []

baselines = pd.read_csv(RESULTADOS / "resultados_baselines.csv")
resultados_todos.extend(baselines.to_dict("records"))

for janela in JANELAS:
    print(f"\n{'='*70}")
    print(f"JANELA p{janela}")
    print(f"{'='*70}")

    CAT_FEATURES, NUM_FEATURES, ALL_FEATURES = get_features(janela)
    print(f"Features: {len(ALL_FEATURES)} ({len(CAT_FEATURES)} cat + {len(NUM_FEATURES)} num)")

    dados = np.load(RESULTADOS / f"dados_preparados_p{janela}.npz")
    X_treino_scaled = dados["X_treino_scaled"]
    X_val_scaled = dados["X_val_scaled"]
    X_teste_scaled = dados["X_teste_scaled"]
    X_treino_tree = dados["X_treino_tree"]
    X_val_tree = dados["X_val_tree"]
    X_teste_tree = dados["X_teste_tree"]
    y_treino = dados["y_treino"]
    y_val = dados["y_val"]
    y_teste = dados["y_teste"]

    treino_df = pd.read_parquet(DADOS / f"treino_p{janela}.parquet")
    val_df = pd.read_parquet(DADOS / f"val_p{janela}.parquet")
    teste_df = pd.read_parquet(DADOS / f"teste_p{janela}.parquet")

    X_treino_cb = treino_df[ALL_FEATURES].copy()
    X_val_cb = val_df[ALL_FEATURES].copy()
    X_teste_cb = teste_df[ALL_FEATURES].copy()
    cat_indices = [ALL_FEATURES.index(c) for c in CAT_FEATURES]

    n_neg = (y_treino == 0).sum()
    n_pos = (y_treino == 1).sum()
    scale_pos = n_neg / n_pos

    melhores_modelos = {}

    print("\n--- LR (Optuna) ---")

    def objective_lr(trial):
        C = trial.suggest_float("C", 1e-2, 100, log=True)
        penalty = trial.suggest_categorical("penalty", ["l1", "l2"])
        solver = "saga" if penalty == "l1" else "lbfgs"
        modelo = LogisticRegression(C=C, penalty=penalty, solver=solver,
                                     class_weight="balanced", max_iter=2000,
                                     random_state=SEED)
        modelo.fit(X_treino_scaled, y_treino)
        y_prob = modelo.predict_proba(X_val_scaled)[:, 1]
        from sklearn.metrics import roc_auc_score
        if len(np.unique(y_prob.round(4))) < 3:
            return 0.0
        y_pred = (y_prob >= 0.5).astype(int)
        return f2_score(y_val, y_pred)

    study_lr = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=SEED))
    study_lr.optimize(objective_lr, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    print(f"  Melhor F2 val: {study_lr.best_value:.4f}")
    print(f"  Params: {study_lr.best_params}")

    bp = study_lr.best_params
    solver = "saga" if bp["penalty"] == "l1" else "lbfgs"
    lr_best = LogisticRegression(C=bp["C"], penalty=bp["penalty"], solver=solver,
                                  class_weight="balanced", max_iter=2000,
                                  random_state=SEED)
    lr_best.fit(X_treino_scaled, y_treino)
    melhores_modelos["LR"] = (lr_best, "scaled", study_lr.best_params)

    print("\n--- RF (Optuna) ---")

    def objective_rf(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 800, step=50),
            "max_depth": trial.suggest_int("max_depth", 3, 20),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 30),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 20),
            "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", 0.3, 0.5, 0.7]),
            "class_weight": "balanced",
            "random_state": SEED,
            "n_jobs": -1,
        }
        modelo = RandomForestClassifier(**params)
        modelo.fit(X_treino_tree, y_treino)
        y_pred = modelo.predict(X_val_tree)
        return f2_score(y_val, y_pred)

    study_rf = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=SEED))
    study_rf.optimize(objective_rf, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    print(f"  Melhor F2 val: {study_rf.best_value:.4f}")
    print(f"  Params: {study_rf.best_params}")

    bp = study_rf.best_params
    rf_best = RandomForestClassifier(**bp, class_weight="balanced",
                                      random_state=SEED, n_jobs=-1)
    rf_best.fit(X_treino_tree, y_treino)
    melhores_modelos["RF"] = (rf_best, "tree", study_rf.best_params)

    print("\n--- XGBoost (Optuna) ---")

    def objective_xgb(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 800, step=50),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.3, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10, log=True),
            "gamma": trial.suggest_float("gamma", 1e-8, 5, log=True),
            "scale_pos_weight": scale_pos,
            "random_state": SEED,
            "eval_metric": "logloss",
            "n_jobs": -1,
        }
        modelo = XGBClassifier(**params)
        modelo.fit(X_treino_tree, y_treino, verbose=False)
        y_pred = modelo.predict(X_val_tree)
        return f2_score(y_val, y_pred)

    study_xgb = optuna.create_study(direction="maximize",
                                     sampler=optuna.samplers.TPESampler(seed=SEED))
    study_xgb.optimize(objective_xgb, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    print(f"  Melhor F2 val: {study_xgb.best_value:.4f}")
    print(f"  Params: {study_xgb.best_params}")

    bp = study_xgb.best_params
    xgb_best = XGBClassifier(**bp, scale_pos_weight=scale_pos,
                              random_state=SEED, eval_metric="logloss", n_jobs=-1)
    xgb_best.fit(X_treino_tree, y_treino, verbose=False)
    melhores_modelos["XGBoost"] = (xgb_best, "tree", study_xgb.best_params)

    print("\n--- CatBoost (Optuna) ---")

    def objective_cb(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 100, 800, step=50),
            "depth": trial.suggest_int("depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1e-2, 10, log=True),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0, 5),
            "random_strength": trial.suggest_float("random_strength", 0.1, 10, log=True),
            "auto_class_weights": "Balanced",
            "random_seed": SEED,
            "verbose": 0,
            "cat_features": cat_indices,
        }
        modelo = CatBoostClassifier(**params)
        modelo.fit(X_treino_cb, y_treino)
        y_pred = modelo.predict(X_val_cb)
        return f2_score(y_val, y_pred)

    study_cb = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=SEED))
    study_cb.optimize(objective_cb, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    print(f"  Melhor F2 val: {study_cb.best_value:.4f}")
    print(f"  Params: {study_cb.best_params}")

    bp = study_cb.best_params
    cb_best = CatBoostClassifier(**bp, auto_class_weights="Balanced",
                                  random_seed=SEED, verbose=0,
                                  cat_features=cat_indices)
    cb_best.fit(X_treino_cb, y_treino)
    melhores_modelos["CatBoost"] = (cb_best, "catboost", study_cb.best_params)

    print("\n--- MLP (Optuna) ---")

    from sklearn.utils import compute_sample_weight
    rng_mlp = np.random.RandomState(SEED)
    sample_w = compute_sample_weight("balanced", y_treino)
    idx_resampled = rng_mlp.choice(len(y_treino), size=len(y_treino),
                                    replace=True, p=sample_w / sample_w.sum())
    X_treino_mlp = X_treino_scaled[idx_resampled]
    y_treino_mlp = y_treino[idx_resampled]

    def objective_mlp(trial):
        n_layers = trial.suggest_int("n_layers", 1, 3)
        layers = []
        for i in range(n_layers):
            layers.append(trial.suggest_int(f"n_units_{i}", 16, 128, step=16))
        hidden = tuple(layers)

        params = {
            "hidden_layer_sizes": hidden,
            "activation": trial.suggest_categorical("activation", ["relu", "tanh"]),
            "alpha": trial.suggest_float("alpha", 1e-5, 1e-1, log=True),
            "learning_rate_init": trial.suggest_float("learning_rate_init", 1e-4, 1e-2, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128]),
            "max_iter": 500,
            "early_stopping": True,
            "validation_fraction": 0.15,
            "random_state": SEED,
        }
        modelo = MLPClassifier(**params)
        modelo.fit(X_treino_mlp, y_treino_mlp)
        y_pred = modelo.predict(X_val_scaled)
        return f2_score(y_val, y_pred)

    study_mlp = optuna.create_study(direction="maximize",
                                     sampler=optuna.samplers.TPESampler(seed=SEED))
    study_mlp.optimize(objective_mlp, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    print(f"  Melhor F2 val: {study_mlp.best_value:.4f}")
    print(f"  Params: {study_mlp.best_params}")

    bp = study_mlp.best_params
    n_layers = bp["n_layers"]
    hidden = tuple(bp[f"n_units_{i}"] for i in range(n_layers))
    mlp_best = MLPClassifier(
        hidden_layer_sizes=hidden,
        activation=bp["activation"],
        alpha=bp["alpha"],
        learning_rate_init=bp["learning_rate_init"],
        batch_size=bp["batch_size"],
        max_iter=500, early_stopping=True, validation_fraction=0.15,
        random_state=SEED,
    )
    mlp_best.fit(X_treino_mlp, y_treino_mlp)
    melhores_modelos["MLP"] = (mlp_best, "scaled", study_mlp.best_params)

    print(f"\n{'='*70}")
    print(f"AVALIACAO NA VALIDACAO p{janela} (threshold=0.5)")
    print(f"{'='*70}")
    print(f"{'Modelo':<12} {'F2':>6} {'AUC':>6} {'Recall':>7} "
          f"{'Prec':>6} {'F1':>6} {'Brier':>6}")
    print("-" * 55)

    for nome, (modelo, tipo, params) in melhores_modelos.items():
        if tipo == "scaled":
            X_v, X_t = X_val_scaled, X_teste_scaled
        elif tipo == "tree":
            X_v, X_t = X_val_tree, X_teste_tree
        else:
            X_v, X_t = X_val_cb, X_teste_cb

        y_prob_v = modelo.predict_proba(X_v)[:, 1]
        y_pred_v = (y_prob_v >= 0.5).astype(int)
        m = calcular_metricas(y_val, y_pred_v, y_prob_v)
        m.update({"modelo": nome, "janela": f"p{janela}", "split": "val",
                  "threshold": 0.5})
        resultados_todos.append(m)

        print(f"{nome:<12} {m['f2']:>6.3f} {m['auc_roc']:>6.3f} "
              f"{m['recall']:>7.3f} {m['precision']:>6.3f} "
              f"{m['f1']:>6.3f} {m['brier']:>6.3f}")

    for nome, (modelo, tipo, params) in melhores_modelos.items():
        joblib.dump(modelo, RESULTADOS / f"modelo_{nome}_p{janela}.joblib")
    joblib.dump(melhores_modelos, RESULTADOS / f"melhores_modelos_p{janela}.joblib")

    estudos = {
        "LR": study_lr, "RF": study_rf, "XGBoost": study_xgb,
        "CatBoost": study_cb, "MLP": study_mlp,
    }
    joblib.dump(estudos, RESULTADOS / f"estudos_optuna_p{janela}.joblib")
    print(f"\nModelos e estudos salvos para p{janela}")

df_res = pd.DataFrame(resultados_todos)
df_res.to_csv(RESULTADOS / "resultados_todos_modelos.csv", index=False)

print("\n" + "=" * 80)
print("RESUMO GERAL -- TODOS OS MODELOS NA VALIDACAO")
print("=" * 80)

for jan in [f"p{j}" for j in JANELAS]:
    print(f"\n--- {jan.upper()} ---")
    sub = df_res[(df_res["janela"] == jan) & (df_res["split"] == "val")]
    sub = sub.sort_values("f2", ascending=False)
    print(f"{'Modelo':<12} {'F2':>6} {'AUC':>6} {'Recall':>7} "
          f"{'Prec':>6} {'F1':>6} {'Brier':>6}")
    print("-" * 55)
    for _, row in sub.iterrows():
        print(f"{row['modelo']:<12} {row['f2']:>6.3f} {row['auc_roc']:>6.3f} "
              f"{row['recall']:>7.3f} {row['precision']:>6.3f} "
              f"{row['f1']:>6.3f} {row['brier']:>6.3f}")

print("\nNotebook 07 concluido.")
