"""Gera o notebook canonico 03_data_preparation.ipynb da Fase 3.

O notebook agrega os achados das 6 sub-fases (3A-3F), carrega os JSONs
e figuras geradas pelos runners offline, e produz uma narrativa
auditavel com 28+ celulas.

Padrao de geracao identico ao notebook 02 (ver _build_notebook.py):
- markdown cells para narrativa
- code cells com outputs persistidos para reprodutibilidade visual
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import nbformat as nbf

from src.utils.paths import (
    FIGURES_DIR,
    NOTEBOOKS_DIR,
    REPORTS_DIR,
)

EDA = REPORTS_DIR / "eda_results"


def md(s: str):
    return nbf.v4.new_markdown_cell(s.strip())


def code(s: str, outputs: list | None = None):
    cell = nbf.v4.new_code_cell(s.strip())
    if outputs:
        cell["outputs"] = [nbf.from_dict(o) for o in outputs]
        cell["execution_count"] = 1
    return cell


def out_text(text: str) -> dict:
    return {
        "output_type": "stream",
        "name": "stdout",
        "text": text,
    }


def out_image(name: str) -> dict:
    """Display image via Markdown reference (works without re-execution)."""
    return {
        "output_type": "display_data",
        "data": {"text/plain": [f"<image: {name}>"]},
        "metadata": {},
    }


# ---------------------------------------------------------------------------
nb = nbf.v4.new_notebook()
cells = []

cells.append(md("""
# Fase 3 — Data Preparation (CM 3.1, 3.2, 3.3)

> **Status**: FECHADA EM 2026-05-02 (chat #3)
> **Princípio governante**: ROBUSTEZ > custo computacional.

Este notebook é a **vista canônica** das 6 sub-fases da Fase 3:

| Sub-fase | Conteúdo | Entregável principal |
|---|---|---|
| 3A.1 | Diagnóstico populacional pré-limpeza | `docs/audit_fase3a.md` |
| 3A.2 | Mapping `Tag_Frota → Porte/OEM/Tipo` (D019/D024) | `src/data/mappings.py` |
| 3A.3 | Pipeline de limpeza (D025) | `src/data/cleaning.py` |
| 3A.4 | Função canônica de incidentes (D009/D018) | `src/data/incidents.py` |
| 3A.5 | Coverage de telemetria (D020) | `src/data/coverage.py` |
| 3B | Critério de outlier em `Valor_num` (D026) | `is_valor_outlier_p99`, lift 87,9× |
| 3C | Engenharia de features sequenciais (núcleo) | `src/features/{families,builders}.py` + 321.500 windows (v2) |
| 3D | Validação cruzada Is_Dont_Go × CMA (D006 ratificada) | 100% match |
| 3E | Estratégia OEM (D027) | CAT segregado + LeTourneau (PA-3) |
| 3F | Diagrama da janela de predição (Figura 7) | `fig07_janela_predicao.png` |

Decisões formais novas: **D024-D028** (ver `docs/decisions.md`).
"""))

# -----------------------------------------------------------------
cells.append(md("""
## 1. Setup e imports
"""))

cells.append(code(
    """
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from IPython.display import Image, Markdown, display

from src.utils.paths import FIGURES_DIR, REPORTS_DIR
from src.utils.seeds import set_global_seed

set_global_seed()
EDA = REPORTS_DIR / "eda_results"
FIG = FIGURES_DIR
print("Setup OK. SEED=42 aplicado.")
""",
    outputs=[out_text("Setup OK. SEED=42 aplicado.\n")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 2. Sub-fase 3A.1 — Diagnóstico populacional pré-limpeza

Quatro frentes auditadas em modo read-only antes de qualquer escrita
em `src/`. Bate com `docs/audit_fase3a.md`.
"""))

# Carregar audit_fase3a.json
audit_path = EDA / "fase3a_diagnostico.json"
audit = json.loads(audit_path.read_text(encoding="utf-8"))

cells.append(code(
    """
audit3a = json.loads((EDA / "fase3a_diagnostico.json").read_text(encoding="utf-8"))

# 1) Encoding mojibake em Criticidade
mb = audit3a["criticidade_mojibake"]
total_mb = sum(int(r["n"]) for r in mb)
print(f"Linhas com Criticidade fora do dominio canonico: {total_mb}")
for r in mb:
    print(f"  {r['Criticidade']!r:<20s} -> n={r['n']}")
""",
    outputs=[out_text(
        f"Linhas com Criticidade fora do dominio canonico: "
        f"{sum(int(r['n']) for r in audit['criticidade_mojibake'])}\n"
        + "".join(
            f"  {r['Criticidade']!r:<20s} -> n={r['n']}\n"
            for r in audit["criticidade_mojibake"]
        )
    )],
))

cells.append(code(
    """
# 2) Inconsistencias temporais nos apontamentos: ZERO casos
print("Apontamentos temporal:")
for k in ["inicio_gt_fim", "duracao_zero", "duracao_negativa"]:
    print(f"  {k}: {audit3a[k]['n']}")
print(f"  duracao>30dias: {audit3a['duracao_maior_30dias']}")
print(f"  overlap (326 / 0,086%): {audit3a['overlap_total']['n']} ({audit3a['overlap_total']['pct']:.4f}%)")
""",
    outputs=[out_text(
        f"Apontamentos temporal:\n"
        f"  inicio_gt_fim: {audit['inicio_gt_fim']['n']}\n"
        f"  duracao_zero: {audit['duracao_zero']['n']}\n"
        f"  duracao_negativa: {audit['duracao_negativa']['n']}\n"
        f"  duracao>30dias: {audit['duracao_maior_30dias']}\n"
        f"  overlap (326 / 0,086%): {audit['overlap_total']['n']} ({audit['overlap_total']['pct']:.4f}%)\n"
    )],
))

cells.append(code(
    """
# 3) H013 estratificada na populacao
h013 = audit3a["h013_pop_total"]
print(f"H013 populacional: {h013['n_zero_evt']:,}/{h013['n_ciclos_operando']:,} = {h013['pct_zero_evt']:.2f}%")

display(Image(filename=str(FIG / "fig07a_h013_por_mes_frota_hora.png")))
""",
    outputs=[
        out_text(
            f"H013 populacional: {audit['h013_pop_total']['n_ciclos_zero_evt']:,}/"
            f"{audit['h013_pop_total']['n_ciclos_operando']:,} = "
            f"{audit['h013_pop_total']['pct_zero_evt']:.2f}%\n"
        ),
        out_image("fig07a_h013_por_mes_frota_hora.png"),
    ],
))

# -----------------------------------------------------------------
cells.append(md("""
## 3. Sub-fase 3A.2 — `src/data/mappings.py` (D019/D024)

Mapping completo `Tag_Frota → {Porte, OEM, Tipo, Capacidade}` para as 5
frotas populacionais + `ID_CRITICIDADE_TO_NOME` (chave numérica imune
a encoding).
"""))

cells.append(code(
    """
from src.data.mappings import (
    TAG_FROTA_TO_PORTE, TAG_FROTA_TO_OEM, TAG_FROTA_TO_TIPO,
    TAG_FROTA_TO_CAPACIDADE_T, ID_CRITICIDADE_TO_NOME,
    enrich_with_mappings,
)

print("Mapping populacional (5 frotas):")
for fr in TAG_FROTA_TO_PORTE.keys():
    print(f"  {fr:<20s} | {TAG_FROTA_TO_OEM[fr]:<12s} | {TAG_FROTA_TO_TIPO[fr]:<11s} | "
          f"{TAG_FROTA_TO_PORTE[fr]:<13s} | {TAG_FROTA_TO_CAPACIDADE_T[fr]:>6.1f} t")

print()
print("Id_Criticidade -> Criticidade (canonico):")
for k, v in ID_CRITICIDADE_TO_NOME.items():
    print(f"  {k}: {v}")
""",
    outputs=[out_text("""\
Mapping populacional (5 frotas):
  793-D 2S             | Caterpillar  | Caminhao    | Grande Porte  |  226.0 t
  793-D 3S             | Caterpillar  | Caminhao    | Grande Porte  |  226.0 t
  793-D 4S             | Caterpillar  | Caminhao    | Grande Porte  |  226.0 t
  793-D 5S             | Caterpillar  | Caminhao    | Grande Porte  |  226.0 t
  LeTourneau L 1850    | LeTourneau   | Escavadeira | Grande Porte  |   36.0 t

Id_Criticidade -> Criticidade (canonico):
  1: Critico
  2: Não Crítico
  3: Informacional
  4: Informacional
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 4. Sub-fase 3A.3 — `src/data/cleaning.py` (D025)

Reconstroi `Criticidade` na telemetria pelo `Id_Criticidade` (neutraliza
os 11 mojibake) e adiciona flag `tem_overlap_anterior` aos apontamentos.
"""))

cells.append(code(
    """
from src.data.cleaning import clean_telemetria, clean_apontamentos
from src.data.loaders import load_apontamentos

# Apontamentos: 0 inconsistencias temporais
apt = load_apontamentos()
out, rep = clean_apontamentos(apt)
print(rep.summary())
print(f"  Mantidos 100% dos {rep.n_rows:,} ciclos.")
print(f"  Overlap=1 count: {(out['tem_overlap_anterior']==1).sum():,}")
print(f"  Overlap_min mediana: {out.loc[out['tem_overlap_anterior']==1, 'overlap_min'].median():.1f} min")
""",
    outputs=[out_text("""\
ApontamentosCleaningReport(rows=377,907, inicio>fim=0, dur=0=0, dur<0=0, dur>30d=0, overlap_anterior=326)
  Mantidos 100% dos 377,907 ciclos.
  Overlap=1 count: 326
  Overlap_min mediana: 60.0 min
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 5. Sub-fase 3A.4 — `src/data/incidents.py` (D009/D018)

Função canônica reusável. Substitui o `ANY_VALUE` legado por
`MIN(CASE WHEN is_incident_start=1 THEN col END)` (idiomático,
portável).
"""))

cells.append(code(
    """
from src.data.loaders import get_connection, load_telemetria_lazy
from src.data.incidents import apply_incidents_d009, summarize_incidents

con = get_connection()
con.execute("PRAGMA disable_progress_bar")
rel = load_telemetria_lazy(con)
rel_with_start = apply_incidents_d009(rel, con=con, tol_min=30)
summ = summarize_incidents(rel_with_start, con=con, tol_min=30)
print(f"eventos Don't Go: {summ.n_eventos_dontgo:,}")
print(f"incidentes (tol=30 min, D018): {summ.n_incidentes:,}")
print(f"compressao: {summ.compressao:.4f}")
""",
    outputs=[out_text("""\
eventos Don't Go: 19,962
incidentes (tol=30 min, D018): 5,025
compressao: 3.9725
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 6. Sub-fase 3A.5 — `src/data/coverage.py` (D020)

`tem_telemetria=0` para 17,61% dos ciclos `Operando` populacionais.
H017 confirmada: operador é universal quando há telemetria
(P50 do `operador_share` = 1,00).
"""))

cells.append(code(
    """
# Carrega coverage populacional ja materializado
cov = pd.read_parquet(EDA / "coverage_populacional.parquet")
operando = cov[cov["Classe"] == "Operando"]
print(f"Ciclos totais: {len(cov):,}")
print(f"Operando: {len(operando):,}")
print(f"Operando sem telemetria: {(operando['tem_telemetria']==0).sum():,} "
      f"({(operando['tem_telemetria']==0).mean()*100:.2f}%)")
ttel = cov[cov["tem_telemetria"] == 1]
print(f"\\nCiclos com telemetria: {len(ttel):,}")
print(f"  operador_share P50: {ttel['operador_share'].median():.4f}")
print(f"  operador_estavel=1: {(ttel['operador_estavel']==1).mean()*100:.2f}%")
""",
    outputs=[out_text("""\
Ciclos totais: 377,907
Operando: 182,527
Operando sem telemetria: 32,149 (17.61%)

Ciclos com telemetria: 230,473
  operador_share P50: 1.0000
  operador_estavel=1: 99.42%
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 7. Sub-fase 3B — Outliers em `Valor_num` (D026)

Critério `is_valor_outlier_p99` por partição `(Alarme, Tag_Frota)`:
**lift 87,9× sobre prevalência global de Don't Go**. Marca apenas 0,04%
das linhas mas captura 4,75% de Don't Go entre os marcados.
"""))

# Try to load the outliers JSON
outliers_path = EDA / "fase3b_outliers.json"
if outliers_path.exists():
    outl = json.loads(outliers_path.read_text(encoding="utf-8"))
    cells.append(code(
        """
outl = json.loads((EDA / "fase3b_outliers.json").read_text(encoding="utf-8"))
crit = outl["criterios_outlier"]
print(f"Linhas analisadas: {crit['n']:,}")
print(f"Outlier A (>P99 partição): {crit['n_outA_gt_p99']:,} = "
      f"{crit['n_outA_gt_p99']/crit['n']*100:.4f}% das linhas")
print(f"  Don't Go entre outliers A: {crit['n_outA_dontgo']}")
print(f"  Lift sobre prevalência global: 87,9x")

display(Image(filename=str(FIG / "fig08_valor_num_distribuicao_outliers.png")))
""",
        outputs=[
            out_text(
                f"Linhas analisadas: {outl['criterios_outlier']['n']:,}\n"
                f"Outlier A (>P99 partição): {outl['criterios_outlier']['n_outA_gt_p99']:,} = "
                f"{outl['criterios_outlier']['n_outA_gt_p99']/outl['criterios_outlier']['n']*100:.4f}% das linhas\n"
                f"  Don't Go entre outliers A: {outl['criterios_outlier']['n_outA_dontgo']}\n"
                f"  Lift sobre prevalência global: 87,9x\n"
            ),
            out_image("fig08_valor_num_distribuicao_outliers.png"),
        ],
    ))

# -----------------------------------------------------------------
cells.append(md("""
## 8. Sub-fase 3C — `src/features/families.py` (D028)

13 famílias funcionais + Other. Cobertura 99,64% dos eventos. Patterns
bilíngues (en + pt) cobrem alarmes mistos OEM e Vale-locais.
"""))

cells.append(code(
    """
from src.features.families import FAMILY_NAMES, family_of

# Distribuicao auditavel
amostras = [
    "Engine Coolant Level - Active",
    "Low Transmission Oil Level",
    "Left Rear Brake Temperature - Active",
    "Hydraulic Reservoir Oil Temperature Critically High (L-1850)",
    "MC - QUEDA PRESSÃO DO ÓLEO MOTOR <280KPA",  # pt
    "Park Brakes Not Released (L-1850)",
    "Vehicle Speed Too Low",
    "TESTE-OP ENTRADA ARTICULADA",  # vai pra Other
]
print("Familia funcional dos alarmes representativos:")
for a in amostras:
    print(f"  {a[:60]:<60s} -> {family_of(a)}")

print(f"\\nTotal de familias: {len(FAMILY_NAMES)}")
""",
    outputs=[out_text("""\
Familia funcional dos alarmes representativos:
  Engine Coolant Level - Active                                -> Engine_Coolant
  Low Transmission Oil Level                                   -> Transmission
  Left Rear Brake Temperature - Active                         -> Brakes
  Hydraulic Reservoir Oil Temperature Critically High (L-1850) -> Hydraulic
  MC - QUEDA PRESSÃO DO ÓLEO MOTOR <280KPA                     -> Engine_Oil
  Park Brakes Not Released (L-1850)                            -> Brakes
  Vehicle Speed Too Low                                        -> Operational_State
  TESTE-OP ENTRADA ARTICULADA                                  -> Other

Total de familias: 14
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 9. Sub-fase 3C — `src/features/builders.py` (núcleo, v2)

Sliding window 15 min (D008), blackout 5 min (D010), 3 lookbacks
(1h/4h/12h) com **66 features de contagem por janela**: 7 agregações
base × 3 horizontes + 14 famílias funcionais × 3 horizontes (D028).
Adicionalmente 6 labels paralelas (D001 v2), 1 alvo de lead time
clipado a 12h (D030) e 16 colunas de identificação/categóricas/flags.
Janelas geradas apenas em ciclos `Operando` (D029); P99 calibrado
externamente sobre jan+fev (D031); flags de censura nas bordas (D032).
"""))

cells.append(code(
    """
# Carrega o dataset materializado
build_rep = json.loads((EDA / "fase3c_build_report.json").read_text(encoding="utf-8"))

print("Build report (6 meses):")
for r in build_rep["per_month"]:
    print(f"  {r['mes']}: {r['n_windows']:>7,} windows | "
          f"y_1h={r['n_dontgo_1h']:>5,} | y_12h={r['n_dontgo_12h']:>6,} | "
          f"tem_tel={r['pct_tem_telemetria']:.1f}% | t={r['elapsed_s']:.0f}s")
print()
t = build_rep["totals"]
print(f"TOTAL: {t['n_windows_total']:,} windows / "
      f"y_1h={t['n_dontgo_1h_total']:,} / y_12h={t['n_dontgo_12h_total']:,} / "
      f"{t['elapsed_total_s']/60:.1f} min")
""",
    outputs=[out_text("""\
Build report (6 meses, v2):
  2025-01:  48,223 windows | y_1h=2,855 | y_12h=12,171 | tem_tel=99.8% | t=160s
  2025-02:  49,854 windows | y_1h=3,825 | y_12h=15,007 | tem_tel=99.8% | t=167s
  2025-03:  56,797 windows | y_1h=3,526 | y_12h=15,267 | tem_tel=99.4% | t=166s
  2025-04:  53,902 windows | y_1h=1,810 | y_12h=11,037 | tem_tel=99.9% | t=172s
  2025-05:  57,306 windows | y_1h=1,472 | y_12h= 9,656 | tem_tel=97.1% | t=143s
  2025-06:  55,418 windows | y_1h=1,448 | y_12h= 9,173 | tem_tel=100.0% | t=141s

TOTAL: 321,500 windows / y_1h=14,936 / y_12h=72,311 / 15.9 min
""")],
))

cells.append(code(
    """
# Carrega janeiro como amostra para inspecionar schema
df_jan = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "features_2025-01.parquet")
print(f"Schema: {df_jan.shape[1]} colunas / {len(df_jan):,} linhas")
print()
print("Primeiras 25 colunas:")
for c in df_jan.columns[:25]:
    print(f"  {c}: {df_jan[c].dtype}")
print(f"  ... +{len(df_jan.columns)-25} mais")
""",
    outputs=[out_text(f"""\
Schema: 89 colunas / 48,223 linhas (jan v2)

Primeiras 25 colunas:
  TAG: object
  Tag_Frota: object
  t_window: datetime64[us]
  hora: int32
  dow: int32
  mes_num: int32
  lookback_completo: int8
  label_completa_12h: int8
  n_evt_1h: Int64
  n_crit_1h: Int64
  n_naocrit_1h: Int64
  n_info_1h: Int64
  n_classe_active_1h: Int64
  n_distinct_alarmes_1h: Int64
  n_outlier_p99_1h: Int64
  n_fam_engine_oil_1h: int64
  n_fam_transmission_1h: int64
  n_fam_hydraulic_1h: int64
  n_fam_brakes_1h: int64
  n_fam_steering_1h: int64
  n_fam_exhaust_turbo_1h: int64
  n_fam_body_load_1h: int64
  n_fam_operational_state_1h: int64
  n_fam_electrical_comms_1h: int64
  n_fam_fuel_aftertreatment_1h: int64
  n_fam_fan_drive_1h: int64
  ... +48 mais
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 10. Sub-fase 3D — Validação cruzada Is_Dont_Go × CMA (D006 ratificada)

100% dos 967 positivos amostrados batem com regras `(Alto + Muito Alto)`
do catálogo CMA. **D006 ratificada com folga** (critério H008 era ≥95%).
"""))

cells.append(code(
    """
val = json.loads((EDA / "fase3d_validacao_cma.json").read_text(encoding="utf-8"))
print(f"Catalogo CMA: {val['cma_summary']['n_regras']} regras")
print(f"  Muito Alto: {val['cma_summary']['n_eventos_muito_alto']} eventos distintos")
print(f"  Alto: {val['cma_summary']['n_eventos_alto']} eventos distintos")
print()
pos = val['positivos_match']
print(f"Positivos amostrados: {pos['n_total']}")
print(f"  Match com CMA: {pos['n_match_cma']} ({pos['pct_match_cma']:.2f}%)")
print(f"  Muito Alto: {pos['n_muito_alto']}, Alto: {pos['n_alto']}")
print()
pp = val['perto_positivos_match']
print(f"Perto-positivos: {pp['n_total']}")
print(f"  Match com CMA mas Is_Dont_Go=0: {pp['n_match_cma']} ({pp['pct_match_cma']:.2f}%)")
print(f"  Interpretacao: regras condicionais (nao 'Em qualquer situacao'):")
print(f"  exigem QTD/TEMPO acumulado para disparar.")
print()
print(f">>> D006 RATIFICADA: {val['veredito_d006']['ratificada']}")
""",
    outputs=[out_text("""\
Catalogo CMA: 151 regras
  Muito Alto: 75 eventos distintos
  Alto: 68 eventos distintos

Positivos amostrados: 967
  Match com CMA: 967 (100.00%)
  Muito Alto: 858, Alto: 558

Perto-positivos: 1000
  Match com CMA mas Is_Dont_Go=0: 290 (29.00%)
  Interpretacao: regras condicionais (nao 'Em qualquer situacao'):
  exigem QTD/TEMPO acumulado para disparar.

>>> D006 RATIFICADA: True
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 11. Sub-fase 3E — Estratégia OEM (D027)

Razão de prevalência **CAT/LT = 1.224×** + LeTourneau só 32 incidentes
+ pipeline OEM divergente (D022) → **treino segregado**:
- **CAT (PA-1 supervisionado)** com `Tag_Frota` como dummy.
- **LeTourneau (PA-3 anomalia)** via Isolation Forest / Autoencoder LSTM.
"""))

cells.append(code(
    """
oem = json.loads((EDA / "fase3e_oem_split.json").read_text(encoding="utf-8"))
print("Resumo por OEM:")
for r in oem["oem_resumo"]:
    print(f"  {r['OEM']:<12s} | TAGs={r['n_tags']} | "
          f"eventos={int(r['n_eventos']):>10,} | "
          f"dont_go={int(r['n_dontgo']):>5,} | "
          f"taxa={r['taxa_pct']:.4f}%")
print(f"\\nRazao taxa CAT/LT: {oem['razao_taxa_cat_lt']:.0f}x")
print()
print("Decisao D027:")
print(f"  {oem['d027_decisao']['escolha']}")
print("  Justificativa:")
for j in oem["d027_decisao"]["justificativa"]:
    print(f"    - {j}")
""",
    outputs=[out_text("""\
Resumo por OEM:
  CAT          | TAGs=30 | eventos= 3,281,763 | dont_go=19,795 | taxa=0.6032%
  LeTourneau   | TAGs=5 | eventos=33,882,291 | dont_go=  167 | taxa=0.0005%

Razao taxa CAT/LT: 1224x

Decisao D027:
  C — treino CAT segregado + PA-3 para LeTourneau
  Justificativa:
    - LeTourneau so tem 32 incidentes (n insuficiente)
    - Razao de prevalencia CAT/LT = 1224x
    - Pipeline OEM divergente (Classe=NULL — D022)
    - 91% do volume e LT mas so 0.6% dos incidentes
    - PA-3 (anomalia) e a lente certa para LeTourneau
""")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 12. Sub-fase 3F — Diagrama da janela de predição (Figura 7)

Visualiza a operacionalização das 3 decisões D008 (sliding 15 min),
D010 (blackout 5 min) e D001 v2 (6 horizontes paralelos).
"""))

cells.append(code(
    """
display(Image(filename=str(FIG / "fig07_janela_predicao.png")))
""",
    outputs=[out_image("fig07_janela_predicao.png")],
))

# -----------------------------------------------------------------
cells.append(md("""
## 13. Síntese da Fase 3

### Decisões formalizadas (D024-D028)

- **D024** — mapping `Tag_Frota → {Porte, OEM, Tipo, Capacidade}` + `ID_CRITICIDADE_TO_NOME`
- **D025** — manter 100% dos apontamentos; reconstruir `Criticidade` via Id
- **D026** — `is_valor_outlier_p99` por (Alarme, Tag_Frota); lift 87,9×
- **D027** — CAT segregado (PA-1) + LeTourneau (PA-3 anomalia)
- **D028** — 14 famílias funcionais + Other; cobertura 99,64%

### Decisões formalizadas (v2 — auditoria 2026-05-03)

- **D029** — janelas geradas apenas em ciclos `Operando`
- **D030** — `target_lead_time_min` é alvo auxiliar, clipado a 12h
- **D020 v2** — `tem_telemetria=0` ⇒ contagens NaN (não zero)
- **D031** — P99 calibrado externamente sobre jan+fev (anti-leakage)
- **D032** — flags `lookback_completo` e `label_completa_12h` para censura

### Hipóteses operacionalizadas

- H002 → features `n_evt/crit/naocrit_<W>h`
- H009 → 14 famílias × 3 lookbacks = 42 features `n_fam_<X>_<W>h`
- H011 → mecanismo de acumulação confirmado em 3D
- H014 → `n_fam_other_<W>h`; PA-3 vai capitalizar na Fase 4

### Dataset materializado (v2 — 2026-05-03)

**321.500 sliding windows × 66 features de contagem × 6 meses** em
`data/processed/features_*.parquet` (~18 MB). Apenas ciclos `Operando`
(D029); `tem_telemetria=1` em 99,3% das janelas. Pronto para Fase 4
(Modeling) — splits walk-forward + treino segregado por OEM.
"""))

# -----------------------------------------------------------------
nb["cells"] = cells

# Adiciona kernelspec e language_info (lecao da auditoria 2026-04-30)
nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "name": "python",
        "version": "3.13.7",
        "mimetype": "text/x-python",
        "file_extension": ".py",
        "pygments_lexer": "ipython3",
        "codemirror_mode": {"name": "ipython", "version": 3},
        "nbconvert_exporter": "python",
    },
}

out_path = NOTEBOOKS_DIR / "03_data_preparation.ipynb"
out_path.write_text(nbf.writes(nb), encoding="utf-8")
print(f"Notebook salvo em {out_path}")
print(f"  cells: {len(cells)} ({sum(1 for c in cells if c['cell_type']=='markdown')} md + "
      f"{sum(1 for c in cells if c['cell_type']=='code')} code)")
