import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
from sklearn.metrics import (roc_curve, precision_recall_curve, roc_auc_score,
                              average_precision_score, brier_score_loss)

from config_modelagem import (DADOS, RESULTADOS, GRAFICOS, TARGET, SEED,
                               JANELAS, CORES_MODELO, ROXO_MEDIO, ROXO_CLARO,
                               VERDE, VERMELHO, AZUL, LARANJA, CINZA,
                               calcular_metricas, f2_score, bootstrap_metricas,
                               ci_95, salvar_fig, get_features)

resultados_finais = []

for janela in JANELAS:
    print(f"\n{'='*70}")
    print(f"JANELA p{janela}")
    print(f"{'='*70}")

    CAT_FEATURES, NUM_FEATURES, ALL_FEATURES = get_features(janela)

    dados = np.load(RESULTADOS / f"dados_preparados_p{janela}.npz")
    X_val_scaled = dados["X_val_scaled"]
    X_teste_scaled = dados["X_teste_scaled"]
    X_val_tree = dados["X_val_tree"]
    X_teste_tree = dados["X_teste_tree"]
    y_val = dados["y_val"]
    y_teste = dados["y_teste"]

    val_df = pd.read_parquet(DADOS / f"val_p{janela}.parquet")
    teste_df = pd.read_parquet(DADOS / f"teste_p{janela}.parquet")
    X_val_cb = val_df[ALL_FEATURES].copy()
    X_teste_cb = teste_df[ALL_FEATURES].copy()

    modelos_dict = joblib.load(RESULTADOS / f"melhores_modelos_p{janela}.joblib")

    print(f"\n--- THRESHOLD TUNING (validacao) ---")
    print(f"{'Modelo':<12} {'Thr_opt':>8} {'F2_0.5':>7} {'F2_opt':>7} {'Gain':>7}")
    print("-" * 50)

    thresholds_otimos = {}

    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_v = X_val_scaled
        elif tipo == "tree":
            X_v = X_val_tree
        else:
            X_v = X_val_cb

        y_prob = modelo.predict_proba(X_v)[:, 1]

        melhor_f2, melhor_thr = 0, 0.5
        for thr in np.arange(0.10, 0.90, 0.01):
            y_pred = (y_prob >= thr).astype(int)
            f2 = f2_score(y_val, y_pred)
            if f2 > melhor_f2:
                melhor_f2 = f2
                melhor_thr = thr

        y_pred_05 = (y_prob >= 0.5).astype(int)
        f2_05 = f2_score(y_val, y_pred_05)

        thresholds_otimos[nome] = melhor_thr
        gain = melhor_f2 - f2_05

        print(f"{nome:<12} {melhor_thr:>8.2f} {f2_05:>7.3f} {melhor_f2:>7.3f} "
              f"{gain:>+6.3f}")

    print(f"\n--- CURVAS ROC e PR ---")

    fig_roc = go.Figure()
    fig_roc.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                       line=dict(dash="dash", color="gray"))

    fig_pr = go.Figure()
    prevalencia = y_val.mean()
    fig_pr.add_shape(type="line", x0=0, y0=prevalencia, x1=1, y1=prevalencia,
                      line=dict(dash="dash", color="gray"))

    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_v = X_val_scaled
        elif tipo == "tree":
            X_v = X_val_tree
        else:
            X_v = X_val_cb

        y_prob = modelo.predict_proba(X_v)[:, 1]

        fpr, tpr, _ = roc_curve(y_val, y_prob)
        auc = roc_auc_score(y_val, y_prob)
        fig_roc.add_trace(go.Scatter(
            x=fpr, y=tpr, mode="lines",
            name=f"{nome} (AUC={auc:.3f})",
            line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2),
        ))

        prec, rec, _ = precision_recall_curve(y_val, y_prob)
        ap = average_precision_score(y_val, y_prob)
        fig_pr.add_trace(go.Scatter(
            x=rec, y=prec, mode="lines",
            name=f"{nome} (AP={ap:.3f})",
            line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2),
        ))

    fig_roc.update_layout(title=f"Curva ROC -- Validacao p{janela}",
                           xaxis_title="FPR", yaxis_title="TPR",
                           height=500, width=650)
    salvar_fig(fig_roc, f"roc_validacao_p{janela}")

    fig_pr.update_layout(title=f"Curva Precision-Recall -- Validacao p{janela}",
                          xaxis_title="Recall", yaxis_title="Precision",
                          height=500, width=650)
    salvar_fig(fig_pr, f"pr_validacao_p{janela}")

    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_v = X_val_scaled
        elif tipo == "tree":
            X_v = X_val_tree
        else:
            X_v = X_val_cb

        y_prob = modelo.predict_proba(X_v)[:, 1]

        thresholds = np.arange(0.10, 0.90, 0.01)
        f2s, f1s, recalls, precs = [], [], [], []
        for thr in thresholds:
            yp = (y_prob >= thr).astype(int)
            from sklearn.metrics import precision_score, recall_score, f1_score, fbeta_score
            f2s.append(fbeta_score(y_val, yp, beta=2, zero_division=0))
            f1s.append(f1_score(y_val, yp, zero_division=0))
            recalls.append(recall_score(y_val, yp, zero_division=0))
            precs.append(precision_score(y_val, yp, zero_division=0))

        fig_thr = go.Figure()
        fig_thr.add_trace(go.Scatter(x=thresholds, y=f2s, name="F2",
                                      line=dict(color=VERMELHO, width=2.5)))
        fig_thr.add_trace(go.Scatter(x=thresholds, y=f1s, name="F1",
                                      line=dict(color=AZUL, width=1.5)))
        fig_thr.add_trace(go.Scatter(x=thresholds, y=recalls, name="Recall",
                                      line=dict(color=VERDE, width=1.5, dash="dash")))
        fig_thr.add_trace(go.Scatter(x=thresholds, y=precs, name="Precision",
                                      line=dict(color=LARANJA, width=1.5, dash="dash")))
        thr_opt = thresholds_otimos[nome]
        fig_thr.add_vline(x=thr_opt, line_dash="dot", line_color="black",
                           annotation_text=f"thr={thr_opt:.2f}")
        fig_thr.update_layout(
            title=f"Metricas vs Threshold -- {nome} (Val p{janela})",
            xaxis_title="Threshold", yaxis_title="Score",
            height=400, width=700,
        )
        salvar_fig(fig_thr, f"threshold_{nome}_p{janela}", width=750, height=450)

    print(f"\n--- CALIBRACAO ---")
    print(f"{'Modelo':<12} {'Brier':>7} {'Brier_cal':>10}")
    print("-" * 35)

    fig_cal = go.Figure()
    fig_cal.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                       line=dict(dash="dash", color="gray"))

    modelos_calibrados = {}

    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_v = X_val_scaled
        elif tipo == "tree":
            X_v = X_val_tree
        else:
            X_v = X_val_cb

        y_prob = modelo.predict_proba(X_v)[:, 1]
        brier_orig = brier_score_loss(y_val, y_prob)

        prob_true, prob_pred = calibration_curve(y_val, y_prob, n_bins=10,
                                                  strategy="uniform")
        fig_cal.add_trace(go.Scatter(
            x=prob_pred, y=prob_true, mode="lines+markers",
            name=f"{nome} (Brier={brier_orig:.3f})",
            line=dict(color=CORES_MODELO.get(nome, ROXO_MEDIO), width=2),
        ))

        from sklearn.base import clone
        if tipo == "scaled":
            X_t_cal = X_val_scaled
        elif tipo == "tree":
            X_t_cal = X_val_tree
        else:
            X_t_cal = X_val_cb

        try:
            cal_modelo = CalibratedClassifierCV(modelo, method="sigmoid", cv="prefit")
            cal_modelo.fit(X_t_cal, y_val)
            y_prob_cal = cal_modelo.predict_proba(X_v)[:, 1]
            brier_cal = brier_score_loss(y_val, y_prob_cal)
            modelos_calibrados[nome] = cal_modelo
        except Exception as e:
            brier_cal = brier_orig
            modelos_calibrados[nome] = modelo

        print(f"{nome:<12} {brier_orig:>7.4f} {brier_cal:>10.4f}")

    fig_cal.update_layout(
        title=f"Curva de Calibracao -- Validacao p{janela}",
        xaxis_title="Probabilidade predita (media do bin)",
        yaxis_title="Fracao de positivos observada",
        height=500, width=600,
    )
    salvar_fig(fig_cal, f"calibracao_validacao_p{janela}")

    print(f"\n--- SELECAO DE MODELO (validacao, threshold otimo) ---")
    print(f"{'Modelo':<12} {'Thr':>5} {'F2':>6} {'AUC':>6} {'Recall':>7} "
          f"{'Prec':>6} {'F1':>6} {'Brier':>6}")
    print("-" * 60)

    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_v = X_val_scaled
        elif tipo == "tree":
            X_v = X_val_tree
        else:
            X_v = X_val_cb

        y_prob = modelo.predict_proba(X_v)[:, 1]
        thr = thresholds_otimos[nome]
        y_pred = (y_prob >= thr).astype(int)
        m = calcular_metricas(y_val, y_pred, y_prob)
        m.update({"modelo": nome, "janela": f"p{janela}", "split": "val_thr_opt",
                  "threshold": thr})
        resultados_finais.append(m)

        print(f"{nome:<12} {thr:>5.2f} {m['f2']:>6.3f} {m['auc_roc']:>6.3f} "
              f"{m['recall']:>7.3f} {m['precision']:>6.3f} "
              f"{m['f1']:>6.3f} {m['brier']:>6.3f}")

    joblib.dump(thresholds_otimos, RESULTADOS / f"thresholds_otimos_p{janela}.joblib")
    joblib.dump(modelos_calibrados, RESULTADOS / f"modelos_calibrados_p{janela}.joblib")

    print(f"\n{'='*70}")
    print(f"AVALIACAO FINAL NO TESTE p{janela} (threshold otimo, UMA VEZ)")
    print(f"{'='*70}")
    print(f"{'Modelo':<12} {'Thr':>5} {'F2':>6} {'AUC':>6} {'Recall':>7} "
          f"{'Prec':>6} {'F1':>6} {'Brier':>6}")
    print("-" * 60)

    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_t = X_teste_scaled
        elif tipo == "tree":
            X_t = X_teste_tree
        else:
            X_t = X_teste_cb

        y_prob = modelo.predict_proba(X_t)[:, 1]
        thr = thresholds_otimos[nome]
        y_pred = (y_prob >= thr).astype(int)
        m = calcular_metricas(y_teste, y_pred, y_prob)
        m.update({"modelo": nome, "janela": f"p{janela}", "split": "teste",
                  "threshold": thr})
        resultados_finais.append(m)

        print(f"{nome:<12} {thr:>5.2f} {m['f2']:>6.3f} {m['auc_roc']:>6.3f} "
              f"{m['recall']:>7.3f} {m['precision']:>6.3f} "
              f"{m['f1']:>6.3f} {m['brier']:>6.3f}")

    val_results = [r for r in resultados_finais
                   if r["janela"] == f"p{janela}" and r["split"] == "val_thr_opt"]
    melhor_val = max(val_results, key=lambda x: x["f2"])
    melhor_nome = melhor_val["modelo"]
    teste_res = [r for r in resultados_finais
                 if r["janela"] == f"p{janela}" and r["split"] == "teste"
                 and r["modelo"] == melhor_nome][0]
    print(f"\n  Melhor modelo p{janela} (selecao por val): {melhor_nome} "
          f"(F2_val={melhor_val['f2']:.3f}, F2_teste={teste_res['f2']:.3f})")

    modelo_sel, tipo_sel, _ = modelos_dict[melhor_nome]
    if tipo_sel == "scaled":
        X_t = X_teste_scaled
    elif tipo_sel == "tree":
        X_t = X_teste_tree
    else:
        X_t = X_teste_cb

    y_prob_sel = modelo_sel.predict_proba(X_t)[:, 1]
    thr_sel = thresholds_otimos[melhor_nome]
    y_pred_sel = (y_prob_sel >= thr_sel).astype(int)

    print(f"  Calculando bootstrap IC 95% (n=5000)...")
    boot_results = bootstrap_metricas(y_teste, y_pred_sel, y_prob_sel)

    print(f"\n  {'Metrica':<12} {'Ponto':>8} {'IC 2.5%':>8} {'IC 97.5%':>8}")
    print("  " + "-" * 40)
    for metrica in ["f2", "auc_roc", "recall", "precision", "f1", "pr_auc", "brier"]:
        valores = [r[metrica] for r in boot_results]
        media, lower, upper = ci_95(valores)
        print(f"  {metrica:<12} {media:>8.3f} {lower:>8.3f} {upper:>8.3f}")

df_final = pd.DataFrame(resultados_finais)
df_final.to_csv(RESULTADOS / "resultados_threshold_teste.csv", index=False)

print("\n" + "=" * 80)
print("RESUMO GERAL -- TESTE COM THRESHOLD OTIMO")
print("=" * 80)

for jan in [f"p{j}" for j in JANELAS]:
    print(f"\n--- {jan.upper()} ---")
    sub = df_final[(df_final["janela"] == jan) & (df_final["split"] == "teste")]
    sub = sub.sort_values("f2", ascending=False)
    print(f"{'Modelo':<12} {'Thr':>5} {'F2':>6} {'AUC':>6} {'Recall':>7} "
          f"{'Prec':>6} {'F1':>6} {'Brier':>6}")
    print("-" * 60)
    for _, row in sub.iterrows():
        print(f"{row['modelo']:<12} {row['threshold']:>5.2f} {row['f2']:>6.3f} "
              f"{row['auc_roc']:>6.3f} {row['recall']:>7.3f} "
              f"{row['precision']:>6.3f} {row['f1']:>6.3f} {row['brier']:>6.3f}")

print("\nNotebook 08 concluido.")
