import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import joblib
import shap
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import fbeta_score, roc_auc_score

from config_modelagem import (DADOS, RESULTADOS, GRAFICOS, TARGET, SEED,
                               JANELAS, CORES_MODELO, ROXO_MEDIO, ROXO_CLARO,
                               ROXO_ESCURO, VERDE, VERMELHO, AZUL, LARANJA, CINZA,
                               calcular_metricas, f2_score, bootstrap_metricas,
                               ci_95, salvar_fig, N_BOOTSTRAP, get_features)

from scipy.stats import norm, chi2
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.base import clone
from sklearn.utils import compute_sample_weight


def delong_test(y_true, y_score1, y_score2):
    """Teste de DeLong para comparar duas AUC-ROCs sobre os mesmos dados.

    Retorna: (auc1, auc2, z_stat, p_value)
    Ref: DeLong, DeLong & Clarke-Pearson (1988), Biometrics 44(3):837-845.
    """
    pos_mask = y_true == 1
    neg_mask = y_true == 0
    m, n = pos_mask.sum(), neg_mask.sum()

    pos1, neg1 = y_score1[pos_mask], y_score1[neg_mask]
    pos2, neg2 = y_score2[pos_mask], y_score2[neg_mask]

    V10_1 = np.array([(neg1 < p).mean() + 0.5 * (neg1 == p).mean() for p in pos1])
    V10_2 = np.array([(neg2 < p).mean() + 0.5 * (neg2 == p).mean() for p in pos2])
    V01_1 = np.array([(pos1 > nv).mean() + 0.5 * (pos1 == nv).mean() for nv in neg1])
    V01_2 = np.array([(pos2 > nv).mean() + 0.5 * (pos2 == nv).mean() for nv in neg2])

    auc1, auc2 = V10_1.mean(), V10_2.mean()

    S10 = np.cov(V10_1, V10_2)
    S01 = np.cov(V01_1, V01_2)

    var_diff = (S10[0, 0] + S10[1, 1] - 2 * S10[0, 1]) / m + \
               (S01[0, 0] + S01[1, 1] - 2 * S01[0, 1]) / n

    z = (auc1 - auc2) / np.sqrt(max(var_diff, 1e-10))
    p_value = 2 * norm.sf(abs(z))
    return auc1, auc2, z, p_value


def build_preprocessor(num_feats, cat_feats, scale=False):
    """Constroi ColumnTransformer para subconjuntos de features."""
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


def treinar_modelo_subset(melhor_nome, modelo_ref, tipo_ref, df_tr, y_tr,
                          df_te, y_te, num_feats, cat_feats, thr):
    """Retrain a model on a feature subset and evaluate on test."""
    remaining_all = cat_feats + num_feats

    if tipo_ref == "catboost":
        from catboost import CatBoostClassifier as CBC
        cb_params = modelo_ref.get_params()
        cb_params["verbose"] = 0
        cat_idx = list(range(len(cat_feats))) if cat_feats else None
        cb_params["cat_features"] = cat_idx
        m = CBC(**cb_params)
        m.fit(df_tr[remaining_all], y_tr)
        y_prob = m.predict_proba(df_te[remaining_all])[:, 1]
    else:
        scale = (tipo_ref == "scaled")
        pp = build_preprocessor(num_feats, cat_feats, scale=scale)
        X_tr = pp.fit_transform(df_tr)
        X_te = pp.transform(df_te)
        m = clone(modelo_ref)
        if melhor_nome == "MLP":
            sw = compute_sample_weight("balanced", y_tr)
            rng = np.random.RandomState(SEED)
            idx_os = rng.choice(len(y_tr), size=len(y_tr), replace=True,
                                p=sw / sw.sum())
            m.fit(X_tr[idx_os], y_tr[idx_os])
        else:
            m.fit(X_tr, y_tr)
        y_prob = m.predict_proba(X_te)[:, 1]

    y_pred = (y_prob >= thr).astype(int)
    f2 = f2_score(y_te, y_pred)
    auc = roc_auc_score(y_te, y_prob) if len(np.unique(y_te)) == 2 else np.nan
    return f2, auc, y_prob


GRUPOS_FEATURES_ACAD = {
    "Notas": ["nota_media", "nota_mediana", "nota_desvio", "nota_min", "nota_max"],
    "Aprov/Reprov": ["qtd_aprovacoes", "qtd_reprovacoes", "qtd_reprov_nota",
                     "qtd_reprov_freq", "taxa_aprovacao"],
    "Disciplinas": ["qtd_disciplinas_total", "media_disc_por_periodo",
                    "qtd_dispensas", "qtd_sem_resultado"],
    "Carga Horaria": ["ch_acumulada", "pct_ch_concluida"],
    "1o Periodo": ["nota_p1", "delta_nota", "reprov_p1", "disc_p1"],
    "Categoricas": ["curso_origem", "tipo_ingresso"],
    "Cadastrais": ["sexo", "forma_ingresso_grp", "idade_ingresso",
                   "cotista", "natural_uberlandia"],
}

GRUPOS_FEATURES_P1 = {
    "Perfil": ["sexo", "idade_ingresso", "cotista", "natural_uberlandia"],
    "Ingresso": ["tipo_ingresso", "forma_ingresso_grp", "num_semestre_ingresso"],
    "Curso": ["curso_origem"],
}


def get_grupos_features(janela):
    return GRUPOS_FEATURES_P1 if janela == 1 else GRUPOS_FEATURES_ACAD


for janela in JANELAS:
    print(f"\n{'='*70}")
    print(f"JANELA p{janela}")
    print(f"{'='*70}")

    CAT_FEATURES, NUM_FEATURES, ALL_FEATURES = get_features(janela)

    dados = np.load(RESULTADOS / f"dados_preparados_p{janela}.npz")
    X_treino_scaled = dados["X_treino_scaled"]
    X_treino_tree = dados["X_treino_tree"]
    X_teste_scaled = dados["X_teste_scaled"]
    X_teste_tree = dados["X_teste_tree"]
    y_treino = dados["y_treino"]
    y_teste = dados["y_teste"]

    treino_df = pd.read_parquet(DADOS / f"treino_p{janela}.parquet")
    teste_df = pd.read_parquet(DADOS / f"teste_p{janela}.parquet")
    X_treino_cb = treino_df[ALL_FEATURES].copy()
    X_teste_cb = teste_df[ALL_FEATURES].copy()
    for _df in [X_treino_cb, X_teste_cb]:
        for c in _df.select_dtypes(include=["Int8", "Int16", "Int32", "Int64",
                                             "UInt8", "UInt16", "UInt32", "UInt64"]).columns:
            _df[c] = _df[c].astype("float64")

    modelos_dict = joblib.load(RESULTADOS / f"melhores_modelos_p{janela}.joblib")
    thresholds = joblib.load(RESULTADOS / f"thresholds_otimos_p{janela}.joblib")

    feature_names_preprocessed = NUM_FEATURES + CAT_FEATURES
    feature_names_catboost = ALL_FEATURES

    print("\n--- SHAP VALUES ---")

    shap_valores = {}

    for nome, (modelo, tipo, params) in modelos_dict.items():
        print(f"\n  Calculando SHAP para {nome}...")

        fn = feature_names_catboost if tipo == "catboost" else feature_names_preprocessed

        if tipo == "scaled":
            X_bg = X_treino_scaled[:200]
            X_exp = X_teste_scaled
        elif tipo == "tree":
            X_bg = X_treino_tree[:200]
            X_exp = X_teste_tree
        else:
            X_bg = X_treino_cb.iloc[:200]
            X_exp = X_teste_cb

        try:
            if nome in ["RF", "XGBoost", "CatBoost"]:
                explainer = shap.TreeExplainer(modelo)
                sv = explainer(X_exp)
            else:
                explainer = shap.KernelExplainer(
                    lambda x: modelo.predict_proba(x)[:, 1], X_bg)
                sv_raw = explainer.shap_values(X_exp, nsamples=100)
                sv = shap.Explanation(values=sv_raw, data=X_exp,
                                       feature_names=fn)

            shap_valores[nome] = sv

            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig_shap, ax = plt.subplots(figsize=(10, 8))
            if hasattr(sv, "values") and len(sv.values.shape) == 3:
                sv_plot = shap.Explanation(
                    values=sv.values[:, :, 1],
                    base_values=sv.base_values[:, 1] if len(sv.base_values.shape) > 1 else sv.base_values,
                    data=sv.data,
                    feature_names=fn,
                )
            else:
                sv_plot = sv
                if not hasattr(sv_plot, "feature_names") or sv_plot.feature_names is None:
                    sv_plot.feature_names = fn

            if hasattr(sv_plot, "data") and sv_plot.data.dtype == object:
                cat_idx = [fn.index(c) for c in CAT_FEATURES if c in fn]
                data_float = sv_plot.data.copy()
                for idx in cat_idx:
                    cats = sorted(set(data_float[:, idx]))
                    cat_map = {c: float(i) for i, c in enumerate(cats)}
                    data_float[:, idx] = [cat_map[v] for v in data_float[:, idx]]
                sv_plot = shap.Explanation(
                    values=sv_plot.values,
                    base_values=sv_plot.base_values,
                    data=data_float.astype(float),
                    feature_names=sv_plot.feature_names,
                )
            shap.plots.beeswarm(sv_plot, max_display=20, show=False)
            plt.title(f"SHAP Beeswarm -- {nome} (Teste p{janela})")
            plt.tight_layout()
            plt.savefig(str(GRAFICOS / f"shap_beeswarm_{nome}_p{janela}.png"),
                        dpi=200, bbox_inches="tight")
            plt.close()
            print(f"    Salvo: shap_beeswarm_{nome}_p{janela}.png")

            if hasattr(sv_plot, "values"):
                mean_abs = np.abs(sv_plot.values).mean(axis=0)
                top_idx = np.argsort(mean_abs)[::-1][:5]
                print(f"    Top-5 SHAP: {[fn[i] for i in top_idx]}")

        except Exception as e:
            print(f"    [!] Erro no SHAP para {nome}: {e}")

    print(f"\n--- ANALISE DE ERRO ---")

    dados_val = np.load(RESULTADOS / f"dados_preparados_p{janela}.npz")
    X_val_scaled = dados_val["X_val_scaled"]
    X_val_tree = dados_val["X_val_tree"]
    y_val = dados_val["y_val"]
    val_df = pd.read_parquet(DADOS / f"val_p{janela}.parquet")
    X_val_cb = val_df[ALL_FEATURES].copy()
    for c in X_val_cb.select_dtypes(include=["Int8", "Int16", "Int32", "Int64",
                                              "UInt8", "UInt16", "UInt32", "UInt64"]).columns:
        X_val_cb[c] = X_val_cb[c].astype("float64")

    melhor_nome = None
    melhor_f2 = 0
    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_v = X_val_scaled
        elif tipo == "tree":
            X_v = X_val_tree
        else:
            X_v = X_val_cb
        y_prob = modelo.predict_proba(X_v)[:, 1]
        thr = thresholds[nome]
        y_pred = (y_prob >= thr).astype(int)
        f2 = f2_score(y_val, y_pred)
        if f2 > melhor_f2:
            melhor_f2 = f2
            melhor_nome = nome

    modelo_sel, tipo_sel, _ = modelos_dict[melhor_nome]
    if tipo_sel == "scaled":
        X_t = X_teste_scaled
    elif tipo_sel == "tree":
        X_t = X_teste_tree
    else:
        X_t = X_teste_cb

    y_prob = modelo_sel.predict_proba(X_t)[:, 1]
    thr = thresholds[melhor_nome]
    y_pred = (y_prob >= thr).astype(int)

    teste_erro = teste_df.copy()
    teste_erro["y_pred"] = y_pred
    teste_erro["y_prob"] = y_prob
    teste_erro["tipo_erro"] = "Correto"
    teste_erro.loc[(y_teste == 1) & (y_pred == 0), "tipo_erro"] = "FN (evadido nao detectado)"
    teste_erro.loc[(y_teste == 0) & (y_pred == 1), "tipo_erro"] = "FP (formado classificado risco)"

    print(f"\n  Modelo: {melhor_nome} | Threshold: {thr:.2f}")
    print(f"\n  Distribuicao dos erros:")
    for tipo_e in ["Correto", "FN (evadido nao detectado)", "FP (formado classificado risco)"]:
        n = (teste_erro["tipo_erro"] == tipo_e).sum()
        print(f"    {tipo_e}: {n} ({n/len(teste_erro)*100:.1f}%)")

    if janela == 1:
        perfil_cols = ["idade_ingresso", "cotista"]
    else:
        perfil_cols = ["nota_media", "taxa_aprovacao", "qtd_reprovacoes", "pct_ch_concluida"]

    fn = teste_erro[teste_erro["tipo_erro"] == "FN (evadido nao detectado)"]
    if len(fn) > 0:
        print(f"\n  Perfil dos FALSOS NEGATIVOS ({len(fn)} alunos):")
        for col in perfil_cols:
            if col in fn.columns:
                media_fn = fn[col].mean()
                media_ev = teste_erro[teste_erro[TARGET] == 1][col].mean()
                print(f"    {col}: FN={media_fn:.2f} vs todos_evadidos={media_ev:.2f}")
        print(f"    Cursos: {fn['curso_origem'].value_counts().to_dict()}")

    fp = teste_erro[teste_erro["tipo_erro"] == "FP (formado classificado risco)"]
    if len(fp) > 0:
        print(f"\n  Perfil dos FALSOS POSITIVOS ({len(fp)} alunos):")
        for col in perfil_cols:
            if col in fp.columns:
                media_fp = fp[col].mean()
                media_form = teste_erro[teste_erro[TARGET] == 0][col].mean()
                print(f"    {col}: FP={media_fp:.2f} vs todos_formados={media_form:.2f}")
        print(f"    Cursos: {fp['curso_origem'].value_counts().to_dict()}")

    print(f"\n--- FAIRNESS POR SUBGRUPO ---")

    for grupo_col in ["curso_origem", "tipo_ingresso", "sexo"]:
        print(f"\n  Por {grupo_col}:")
        print(f"  {'Grupo':<25} {'N':>5} {'F2':>6} {'AUC':>6} {'Recall':>7} {'Prec':>6}")
        print("  " + "-" * 60)

        for grupo in sorted(teste_erro[grupo_col].unique()):
            mask = teste_erro[grupo_col] == grupo
            n = mask.sum()
            if n < 5:
                continue
            yt = y_teste[mask.values]
            yp = y_pred[mask.values]
            ypr = y_prob[mask.values]
            if len(np.unique(yt)) < 2:
                print(f"  {grupo:<25} {n:>5} -- classes insuficientes --")
                continue
            m = calcular_metricas(yt, yp, ypr)
            print(f"  {grupo:<25} {n:>5} {m['f2']:>6.3f} {m['auc_roc']:>6.3f} "
                  f"{m['recall']:>7.3f} {m['precision']:>6.3f}")

    print(f"\n--- TESTES ESTATISTICOS ---")


    nomes = list(modelos_dict.keys())
    predicoes = {}
    probs = {}
    for nome, (modelo, tipo, params) in modelos_dict.items():
        if tipo == "scaled":
            X_t = X_teste_scaled
        elif tipo == "tree":
            X_t = X_teste_tree
        else:
            X_t = X_teste_cb
        probs[nome] = modelo.predict_proba(X_t)[:, 1]
        predicoes[nome] = (probs[nome] >= thresholds[nome]).astype(int)

    print(f"\n  McNemar Test (pareado, teste p{janela}):")
    print(f"  {'Par':<25} {'b (A=1,B=0)':>12} {'c (A=0,B=1)':>12} {'chi2':>8} {'p-valor':>10}")
    print("  " + "-" * 70)

    for i, nome_a in enumerate(nomes):
        for nome_b in nomes[i+1:]:
            pred_a = predicoes[nome_a]
            pred_b = predicoes[nome_b]
            b = ((pred_a == 1) & (pred_b == 0)).sum()
            c = ((pred_a == 0) & (pred_b == 1)).sum()
            if b + c > 0:
                chi2_stat = (abs(b - c) - 1)**2 / (b + c)
                p_value = 1 - chi2.cdf(chi2_stat, df=1)
            else:
                chi2_stat, p_value = 0, 1.0
            sig = "*" if p_value < 0.05 else ""
            print(f"  {nome_a} vs {nome_b:<14} {b:>12} {c:>12} {chi2_stat:>8.2f} {p_value:>10.4f} {sig}")

    print(f"\n  AUC por modelo (teste p{janela}):")
    for nome in nomes:
        auc = roc_auc_score(y_teste, probs[nome])
        print(f"    {nome:<12} AUC={auc:.4f}")

    print(f"\n  DeLong Test (comparacao pareada de AUC, teste p{janela}):")
    print(f"  {'Par':<25} {'AUC_A':>7} {'AUC_B':>7} {'dAUC':>7} {'Z':>8} {'p-valor':>10}")
    print("  " + "-" * 70)

    delong_results = []
    for i, nome_a in enumerate(nomes):
        for nome_b in nomes[i+1:]:
            try:
                auc_a, auc_b, z_stat, p_val = delong_test(
                    y_teste, probs[nome_a], probs[nome_b])
                sig = "*" if p_val < 0.05 else ""
                print(f"  {nome_a} vs {nome_b:<14} {auc_a:>7.4f} {auc_b:>7.4f} "
                      f"{auc_a - auc_b:>+7.4f} {z_stat:>8.2f} {p_val:>10.4f} {sig}")
                delong_results.append({
                    "par": f"{nome_a} vs {nome_b}",
                    "delta_auc": abs(auc_a - auc_b),
                    "p_valor": p_val,
                    "significativo": p_val < 0.05,
                })
            except Exception as e:
                print(f"  {nome_a} vs {nome_b:<14} -- erro: {e}")

    n_sig = sum(1 for r in delong_results if r["significativo"])
    print(f"\n  Resumo DeLong: {n_sig}/{len(delong_results)} pares com diferenca "
          f"significativa (p < 0.05)")

    print(f"\n--- CURVAS DE APRENDIZAGEM ---")

    modelo_sel, tipo_sel, params_sel = modelos_dict[melhor_nome]
    fractions = [0.2, 0.4, 0.6, 0.8, 1.0]
    learning_f2 = []

    for frac in fractions:
        n_samples = int(len(y_treino) * frac)
        idx = np.random.RandomState(SEED).choice(len(y_treino), n_samples, replace=False)

        if tipo_sel == "scaled":
            X_sub = X_treino_scaled[idx]
            X_v = X_teste_scaled
        elif tipo_sel == "tree":
            X_sub = X_treino_tree[idx]
            X_v = X_teste_tree
        else:
            X_sub = X_treino_cb.iloc[idx]
            X_v = X_teste_cb

        from sklearn.base import clone
        if tipo_sel == "catboost":
            from catboost import CatBoostClassifier as CBC
            cb_params = modelo_sel.get_params()
            cb_params["verbose"] = 0
            m_clone = CBC(**cb_params)
        else:
            m_clone = clone(modelo_sel)
        m_clone.fit(X_sub, y_treino[idx])
        y_prob_lc = m_clone.predict_proba(X_v)[:, 1]
        y_pred_lc = (y_prob_lc >= thr).astype(int)
        f2_lc = f2_score(y_teste, y_pred_lc)
        learning_f2.append({"frac": frac, "n": n_samples, "f2": f2_lc})
        print(f"  {frac*100:.0f}% treino ({n_samples} alunos): F2={f2_lc:.3f}")

    lc_df = pd.DataFrame(learning_f2)
    fig_lc = go.Figure()
    fig_lc.add_trace(go.Scatter(
        x=lc_df["n"], y=lc_df["f2"], mode="lines+markers",
        line=dict(color=ROXO_MEDIO, width=2),
        marker=dict(size=8),
    ))
    fig_lc.update_layout(
        title=f"Curva de Aprendizagem -- {melhor_nome} (Teste p{janela})",
        xaxis_title="N amostras de treino", yaxis_title="F2 no teste",
        height=400, width=600,
    )
    salvar_fig(fig_lc, f"learning_curve_p{janela}")

    print(f"\n--- PSI (DRIFT FORMAL) ---")

    def calcular_psi(esperado, observado, n_bins=10):
        """PSI entre duas distribuicoes."""
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

    X_tr = X_treino_tree
    X_te = X_teste_tree

    psi_results = []
    for i, feat in enumerate(feature_names_preprocessed):
        try:
            psi = calcular_psi(X_tr[:, i].astype(float), X_te[:, i].astype(float))
        except (TypeError, ValueError):
            psi = np.nan
        psi_results.append({"feature": feat, "PSI": psi})

    psi_df = pd.DataFrame(psi_results).sort_values("PSI", ascending=False)
    print(f"\n  {'Feature':<28} {'PSI':>8} {'Status':>15}")
    print("  " + "-" * 55)
    for _, row in psi_df.iterrows():
        if row["PSI"] > 0.25:
            status = "SIGNIFICATIVA"
        elif row["PSI"] > 0.1:
            status = "MODERADA"
        else:
            status = "ESTAVEL"
        print(f"  {row['feature']:<28} {row['PSI']:>8.4f} {status:>15}")

    fig_psi = go.Figure()
    fig_psi.add_trace(go.Bar(
        y=psi_df["feature"], x=psi_df["PSI"], orientation="h",
        marker_color=[VERMELHO if v > 0.25 else (LARANJA if v > 0.1 else VERDE)
                       for v in psi_df["PSI"]],
    ))
    fig_psi.add_vline(x=0.1, line_dash="dash", line_color="orange",
                       annotation_text="Moderada")
    fig_psi.add_vline(x=0.25, line_dash="dash", line_color="red",
                       annotation_text="Significativa")
    fig_psi.update_layout(
        title=f"PSI (Drift Treino -> Teste) -- p{janela}",
        xaxis_title="PSI", height=600, width=700,
    )
    salvar_fig(fig_psi, f"psi_drift_p{janela}")

    print(f"\n--- PRECISION@K ---")

    y_prob_sel = probs[melhor_nome]
    sorted_idx = np.argsort(y_prob_sel)[::-1]

    for k in [50, 100, 200]:
        if k > len(y_teste):
            continue
        top_k = sorted_idx[:k]
        prec_k = y_teste[top_k].mean()
        print(f"  Precision@{k}: {prec_k:.3f} "
              f"({int(y_teste[top_k].sum())}/{k} evadidos reais)")

    print(f"\n--- ABLATION STUDY ---")
    print(f"  Modelo base: {melhor_nome} | Threshold: {thr:.2f}")

    modelo_abl, tipo_abl, _ = modelos_dict[melhor_nome]
    thr_abl = thresholds[melhor_nome]

    n_total_feat = len(ALL_FEATURES)
    y_prob_base = probs[melhor_nome]
    y_pred_base = (y_prob_base >= thr_abl).astype(int)
    f2_base = f2_score(y_teste, y_pred_base)
    auc_base = roc_auc_score(y_teste, y_prob_base)

    ablation_results = [{"config": f"Todas ({n_total_feat} features)", "n_features": n_total_feat,
                         "f2": f2_base, "auc": auc_base, "delta_f2": 0.0}]
    print(f"\n  {'Config':<30} {'N_feat':>6} {'F2':>7} {'AUC':>7} {'dF2':>7}")
    print("  " + "-" * 62)
    print(f"  {f'Todas ({n_total_feat} features)':<30} {n_total_feat:>6} {f2_base:>7.3f} {auc_base:>7.3f} {0.0:>+7.3f}")

    grupos_abl = get_grupos_features(janela)
    for grupo_nome, grupo_feats in grupos_abl.items():
        remaining_cat = [f for f in CAT_FEATURES if f not in grupo_feats]
        remaining_num = [f for f in NUM_FEATURES if f not in grupo_feats]
        n_remaining = len(remaining_cat) + len(remaining_num)

        if n_remaining == 0:
            continue

        try:
            f2_abl, auc_abl, _ = treinar_modelo_subset(
                melhor_nome, modelo_abl, tipo_abl,
                treino_df, y_treino, teste_df, y_teste,
                remaining_num, remaining_cat, thr_abl)
            delta = f2_abl - f2_base
            ablation_results.append({
                "config": f"Sem {grupo_nome} (-{len(grupo_feats)})",
                "n_features": n_remaining,
                "f2": f2_abl, "auc": auc_abl, "delta_f2": delta})
            print(f"  {'Sem ' + grupo_nome + ' (-' + str(len(grupo_feats)) + ')':<30} "
                  f"{n_remaining:>6} {f2_abl:>7.3f} {auc_abl:>7.3f} {delta:>+7.3f}")
        except Exception as e:
            print(f"  Sem {grupo_nome}: ERRO -- {e}")

    abl_df = pd.DataFrame(ablation_results)
    fig_abl = go.Figure()
    cores_abl = [ROXO_MEDIO if d == 0 else (VERMELHO if d < -0.02 else VERDE)
                 for d in abl_df["delta_f2"]]
    fig_abl.add_trace(go.Bar(
        y=abl_df["config"], x=abl_df["f2"], orientation="h",
        marker_color=cores_abl,
        text=[f"{v:.3f}" for v in abl_df["f2"]],
        textposition="outside",
    ))
    fig_abl.add_vline(x=f2_base, line_dash="dash", line_color=CINZA,
                       annotation_text=f"Baseline F2={f2_base:.3f}")
    fig_abl.update_layout(
        title=f"Ablation Study -- {melhor_nome} (Teste p{janela})",
        xaxis_title="F2-score", height=400, width=700,
        xaxis=dict(range=[max(0, abl_df["f2"].min() - 0.05), 1.0]),
    )
    salvar_fig(fig_abl, f"ablation_study_p{janela}")

    if len(ablation_results) > 1:
        mais_critico = min(ablation_results[1:], key=lambda x: x["f2"])
        print(f"\n  Grupo mais critico: {mais_critico['config']} "
              f"(F2={mais_critico['f2']:.3f}, dF2={mais_critico['delta_f2']:+.3f})")

    print(f"\n--- ESTABILIDADE EM SPLITS ALTERNATIVOS ---")

    all_df = pd.concat([treino_df, val_df, teste_df], ignore_index=True)
    y_all = all_df[TARGET].values

    splits_alt = [
        {"nome": "Split A (tr<=2013 / val 14-15 / te 16-17)",
         "tr_max": 2013, "val_min": 2014, "val_max": 2015,
         "te_min": 2016, "te_max": 2017},
        {"nome": "Split B (tr<=2014 / val 15-16 / te 17-18)",
         "tr_max": 2014, "val_min": 2015, "val_max": 2016,
         "te_min": 2017, "te_max": 2018},
        {"nome": "Split C (tr<=2015 / val 16-17 / te 18-19) [original]",
         "tr_max": 2015, "val_min": 2016, "val_max": 2017,
         "te_min": 2018, "te_max": 2019},
    ]

    print(f"\n  Modelo: {melhor_nome} (mesmos hiperparametros)")
    print(f"  {'Split':<55} {'N_tr':>5} {'N_te':>5} {'F2_te':>7} {'AUC_te':>7}")
    print("  " + "-" * 85)

    split_f2_list = []
    for sp in splits_alt:
        tr_mask = all_df["ano_ingresso"] <= sp["tr_max"]
        val_mask = all_df["ano_ingresso"].between(sp["val_min"], sp["val_max"])
        te_mask = all_df["ano_ingresso"].between(sp["te_min"], sp["te_max"])

        df_tr_s = all_df[tr_mask]
        df_val_s = all_df[val_mask]
        df_te_s = all_df[te_mask]

        y_tr_s = df_tr_s[TARGET].values
        y_val_s = df_val_s[TARGET].values
        y_te_s = df_te_s[TARGET].values

        if len(y_tr_s) < 30 or len(y_te_s) < 10 or len(np.unique(y_te_s)) < 2:
            print(f"  {sp['nome']:<55} -- dados insuficientes "
                  f"(tr={len(y_tr_s)}, te={len(y_te_s)})")
            continue

        try:
            if tipo_sel == "catboost":
                from catboost import CatBoostClassifier as CBC
                cb_p = modelo_sel.get_params()
                cb_p["verbose"] = 0
                m_s = CBC(**cb_p)
                m_s.fit(df_tr_s[ALL_FEATURES], y_tr_s)
                y_prob_val_s = m_s.predict_proba(df_val_s[ALL_FEATURES])[:, 1]
                y_prob_te_s = m_s.predict_proba(df_te_s[ALL_FEATURES])[:, 1]
            else:
                scale = (tipo_sel == "scaled")
                pp_s = build_preprocessor(list(NUM_FEATURES), list(CAT_FEATURES), scale=scale)
                X_tr_s = pp_s.fit_transform(df_tr_s[ALL_FEATURES])
                X_val_s = pp_s.transform(df_val_s[ALL_FEATURES])
                X_te_s = pp_s.transform(df_te_s[ALL_FEATURES])
                m_s = clone(modelo_sel)
                if melhor_nome == "MLP":
                    sw = compute_sample_weight("balanced", y_tr_s)
                    rng = np.random.RandomState(SEED)
                    idx_os = rng.choice(len(y_tr_s), size=len(y_tr_s),
                                        replace=True, p=sw / sw.sum())
                    m_s.fit(X_tr_s[idx_os], y_tr_s[idx_os])
                else:
                    m_s.fit(X_tr_s, y_tr_s)
                y_prob_val_s = m_s.predict_proba(X_val_s)[:, 1]
                y_prob_te_s = m_s.predict_proba(X_te_s)[:, 1]

            melhor_thr_s, melhor_f2_val_s = 0.5, 0
            for t_cand in np.arange(0.10, 0.90, 0.01):
                f2_cand = f2_score(y_val_s, (y_prob_val_s >= t_cand).astype(int))
                if f2_cand > melhor_f2_val_s:
                    melhor_f2_val_s = f2_cand
                    melhor_thr_s = t_cand

            y_pred_te_s = (y_prob_te_s >= melhor_thr_s).astype(int)
            f2_te_s = f2_score(y_te_s, y_pred_te_s)
            auc_te_s = roc_auc_score(y_te_s, y_prob_te_s)
            split_f2_list.append(f2_te_s)

            print(f"  {sp['nome']:<55} {len(y_tr_s):>5} {len(y_te_s):>5} "
                  f"{f2_te_s:>7.3f} {auc_te_s:>7.3f}")
        except Exception as e:
            print(f"  {sp['nome']:<55} -- ERRO: {e}")

    if len(split_f2_list) >= 2:
        f2_mean = np.mean(split_f2_list)
        f2_std = np.std(split_f2_list)
        print(f"\n  Resumo: F2 medio={f2_mean:.3f} +/- {f2_std:.3f} "
              f"(range [{min(split_f2_list):.3f}, {max(split_f2_list):.3f}])")

        fig_stab = go.Figure()
        nomes_split = [f"Split {chr(65+i)}" for i in range(len(split_f2_list))]
        fig_stab.add_trace(go.Bar(
            x=nomes_split, y=split_f2_list,
            marker_color=[ROXO_CLARO, ROXO_MEDIO, ROXO_ESCURO][:len(split_f2_list)],
            text=[f"{v:.3f}" for v in split_f2_list],
            textposition="outside",
        ))
        fig_stab.add_hline(y=f2_mean, line_dash="dash", line_color=CINZA,
                            annotation_text=f"Media={f2_mean:.3f}")
        fig_stab.update_layout(
            title=f"Estabilidade Temporal -- {melhor_nome} (p{janela})",
            yaxis_title="F2 no teste",
            yaxis=dict(range=[max(0, min(split_f2_list) - 0.1), 1.0]),
            height=400, width=500,
        )
        salvar_fig(fig_stab, f"estabilidade_splits_p{janela}")

print("\nNotebook 09 concluido.")
