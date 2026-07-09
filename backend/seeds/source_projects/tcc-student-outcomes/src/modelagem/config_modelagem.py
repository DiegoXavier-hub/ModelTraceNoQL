"""
Constantes, listas de features e funcoes utilitarias compartilhadas
por todos os notebooks de modelagem.
"""
from pathlib import Path
import numpy as np

PROJETO = Path(__file__).resolve().parent.parent.parent
DADOS = PROJETO / "data" / "preprocessamento"
RESULTADOS = Path(__file__).resolve().parent / "resultados"
GRAFICOS = Path(__file__).resolve().parent / "graficos"

RESULTADOS.mkdir(parents=True, exist_ok=True)
GRAFICOS.mkdir(parents=True, exist_ok=True)

JANELAS = [1, 2, 4]

META_COLS = ["id_aluno", "y", "situacao_aluno", "max_periodo",
             "ano_ingresso", "num_semestre_ingresso", "versao", "ch_total_exigida"]

CAT_FEATURES_P1 = ["curso_origem", "tipo_ingresso", "sexo", "forma_ingresso_grp"]
NUM_FEATURES_P1 = ["idade_ingresso", "cotista", "natural_uberlandia",
                    "num_semestre_ingresso"]
ALL_FEATURES_P1 = CAT_FEATURES_P1 + NUM_FEATURES_P1

CAT_FEATURES = ["curso_origem", "tipo_ingresso", "sexo", "forma_ingresso_grp"]

NUM_FEATURES = ["nota_media", "nota_mediana", "nota_desvio", "nota_min", "nota_max",
                "qtd_aprovacoes", "qtd_reprovacoes", "qtd_dispensas", "qtd_sem_resultado",
                "qtd_reprov_nota", "qtd_reprov_freq", "taxa_aprovacao",
                "qtd_disciplinas_total", "media_disc_por_periodo", "ch_acumulada",
                "nota_p1", "delta_nota", "reprov_p1", "disc_p1", "pct_ch_concluida",
                "idade_ingresso", "cotista", "natural_uberlandia"]

ALL_FEATURES = CAT_FEATURES + NUM_FEATURES
TARGET = "y"

FEATURES_POR_JANELA = {
    1: {"cat": CAT_FEATURES_P1, "num": NUM_FEATURES_P1, "all": ALL_FEATURES_P1},
    2: {"cat": CAT_FEATURES, "num": NUM_FEATURES, "all": ALL_FEATURES},
    4: {"cat": CAT_FEATURES, "num": NUM_FEATURES, "all": ALL_FEATURES},
}


def get_features(janela):
    """Retorna (cat_features, num_features, all_features) para a janela."""
    f = FEATURES_POR_JANELA[janela]
    return f["cat"], f["num"], f["all"]

ROXO_ESCURO = "#7B68AE"
ROXO_MEDIO = "#9474DC"
ROXO_CLARO = "#D2B5FF"
ROXO_BG = "#F9F0FF"
VERDE = "#27AE60"
VERMELHO = "#E74C3C"
AZUL = "#3498DB"
LARANJA = "#F39C12"
CINZA = "#95A5A6"

CORES_MODELO = {
    "Dummy": CINZA,
    "LR_base": "#B0B0B0",
    "LR": AZUL,
    "RF": VERDE,
    "XGBoost": LARANJA,
    "CatBoost": VERMELHO,
    "MLP": ROXO_MEDIO,
}

SEED = 42
N_BOOTSTRAP = 5000
OPTUNA_TRIALS = 150

def f2_score(y_true, y_pred):
    """F2-score: pondera recall 4x mais que precision."""
    from sklearn.metrics import fbeta_score
    return fbeta_score(y_true, y_pred, beta=2, zero_division=0)


def calcular_metricas(y_true, y_pred, y_prob):
    """Calcula todas as metricas de avaliacao."""
    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                 f1_score, fbeta_score, roc_auc_score,
                                 average_precision_score, brier_score_loss,
                                 confusion_matrix)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "f2": fbeta_score(y_true, y_pred, beta=2, zero_division=0),
        "auc_roc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
        "brier": brier_score_loss(y_true, y_prob),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def bootstrap_metricas(y_true, y_pred, y_prob, n_boot=N_BOOTSTRAP, seed=SEED):
    """Bootstrap de metricas com n_boot reamostras."""
    rng = np.random.RandomState(seed)
    resultados = []
    n = len(y_true)
    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        yt, yp, ypr = y_true[idx], y_pred[idx], y_prob[idx]
        if len(np.unique(yt)) < 2:
            continue
        resultados.append(calcular_metricas(yt, yp, ypr))
    return resultados


def ci_95(valores):
    """Retorna (media, lower, upper) para IC 95%."""
    arr = np.array(valores)
    return float(np.mean(arr)), float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


def salvar_fig(fig, nome, width=900, height=600):
    """Salva figura Plotly como PNG e HTML."""
    fig.write_image(str(GRAFICOS / f"{nome}.png"), width=width, height=height, scale=2)
    fig.write_html(str(GRAFICOS / f"{nome}.html"), include_plotlyjs="cdn")
    print(f"  Salvo: {nome}.png + .html")
