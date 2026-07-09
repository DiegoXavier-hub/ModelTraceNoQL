"""Configuracao compartilhada para todos os notebooks de EDA.

Paleta de cores baseada no artigo (roxo/purple theme).
Helpers para salvar graficos Plotly em HTML + PNG.
"""
from pathlib import Path
import plotly.io as pio

PROJETO = Path(__file__).resolve().parent.parent.parent
DADOS = PROJETO / "data" / "preprocessamento"
EDA_ROOT = Path(__file__).resolve().parent
GRAFICOS = EDA_ROOT / "graficos"
GRAFICOS.mkdir(parents=True, exist_ok=True)

ROXO_ESCURO  = "#7B68AE"
ROXO_MEDIO   = "#9474DC"
ROXO_CLARO   = "#D2B5FF"
ROXO_BG      = "#F9F0FF"
ROXO_HOVER   = "#B898EF"
VERDE        = "#27AE60"
VERMELHO     = "#C0392B"
AZUL         = "#2980B9"
LARANJA      = "#E67E22"
CINZA        = "#BDC3C7"

CORES_ALVO = {0: VERDE, 1: VERMELHO}
LABELS_ALVO = {0: "Nao-evadido (Formado)", 1: "Evadido"}

CORES_CURSO = {
    "ADM_Integral": "#2980B9",
    "ADM_Noturno":  "#E67E22",
    "GI":           "#9474DC",
}

pio.templates["tcc"] = pio.templates["plotly_white"]
pio.templates["tcc"].layout.update(
    font=dict(family="Arial, sans-serif", size=13),
    title_font=dict(size=16),
    plot_bgcolor=ROXO_BG,
    paper_bgcolor="white",
    colorway=[ROXO_MEDIO, VERDE, VERMELHO, AZUL, LARANJA, ROXO_CLARO],
)
pio.templates.default = "tcc"

META_COLS = ["id_aluno", "y", "situacao_aluno", "max_periodo", "ano_ingresso",
             "num_semestre_ingresso", "versao", "ch_total_exigida"]
CAT_COLS = ["curso_origem", "tipo_ingresso", "sexo", "forma_ingresso_grp"]

_counter = [0]

def salvar_fig(fig, nome, width=1200, height=600):
    """Salva figura Plotly como HTML interativo e PNG estatico."""
    _counter[0] += 1
    prefixo = f"{_counter[0]:02d}_{nome}"

    path_html = GRAFICOS / f"{prefixo}.html"
    path_png = GRAFICOS / f"{prefixo}.png"

    fig.write_html(str(path_html), include_plotlyjs="cdn")
    fig.write_image(str(path_png), width=width, height=height, scale=2)
    print(f"  [{_counter[0]:02d}] {nome} -> HTML + PNG")
    return path_png
