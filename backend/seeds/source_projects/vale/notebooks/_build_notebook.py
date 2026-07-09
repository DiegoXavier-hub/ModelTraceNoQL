"""Constroi notebooks/02_data_understanding_eda.ipynb a partir dos
runners _eda_runner*.py + os JSONs de resultados ja produzidos.

O notebook gerado:
- Tem celulas de markdown explicando cada etapa.
- Tem celulas de codigo executaveis que reproduzem os mesmos resultados.
- Tem celulas com saidas pre-computadas (a partir dos JSONs) para que abrir
  o notebook ja mostre os achados sem precisar re-executar.
"""
from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "reports" / "eda_results"

def _read(p):
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))


R2B = _read(RESULTS_DIR / "fase2b_results.json")
R2C = _read(RESULTS_DIR / "fase2c_results.json")
R2D = _read(RESULTS_DIR / "fase2d_results.json")
R2E = _read(RESULTS_DIR / "fase2e_results.json")
RAUD = _read(RESULTS_DIR / "audit_fase2.json")

nb = new_notebook()
cells = []

cells.append(
    new_markdown_cell(
        """# Fase 2 — Data Understanding / EDA
## Projeto Vale — Antecipacao de alertas Don't Go

**Status**: Fase 2 concluida em 2026-04-30.

Este notebook documenta a Fase 2 do CRISP-DM (Conteudos Minimos 2.1, 2.2, 2.3
do Estudo Guiado). Ele:

1. Carrega os parquets de telemetria (37M linhas) via duckdb lazy e os
   apontamentos (377k linhas) em pandas.
2. Roda estatisticas basicas (shape, dtypes, % nulos, duplicados,
   distribuicao temporal).
3. Analisa a variavel alvo `Is_Dont_Go` aplicando a definicao de **incidente**
   da decisao D009 (sequencia maximal com gap <= 30 min).
4. Calcula taxas por hora/dia/turno/frota/tipo/classe/criticidade.
5. Avalia cobertura entre alarmes da telemetria e os catalogos `Eventos O&M`
   e `CMA` (regras Don't Go).
6. Confirma premissas operacionais: Localidade unica (T3.2), pareamento
   apontamento x telemetria (T3.6), operador inferivel (D016) e origem da
   coluna `Porte` (T3.7).
7. Resultados das hipoteses H001-H009 e novas hipoteses H010+ derivadas.

> **Pre-requisito**: Rodar primeiro `python notebooks/_eda_runner.py`,
> `_eda_runner_2c.py`, `_eda_runner_2d.py` e `_eda_runner_2e.py` para gerar
> as figuras em `reports/figures/` e os dumps em `reports/eda_results/`.

> **Robustez > custo computacional** (princípio governante D000): preferir
> sempre a opcao mais robusta, mesmo que mais lenta.
"""
    )
)

cells.append(
    new_code_cell(
        """import sys, json
from pathlib import Path

ROOT = Path.cwd().parents[0] if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from src.utils.seeds import SEED, set_global_seed
from src.utils.paths import (
    APONTAMENTOS_PARQUET, TELEMETRIA_GLOB, TELEMETRIA_PARQUETS,
    ALARMES_XLSX, DICIONARIO_XLSX, DONTGO_EXAMPLE_XLSX,
    FIGURES_DIR, REPORTS_DIR,
)
from src.data.loaders import (
    get_connection, load_telemetria_lazy,
    load_apontamentos_lazy, load_apontamentos,
)

info = set_global_seed()
print(f"SEED={SEED} aplicado em random/numpy/torch (CUDA: {info.get('torch_cuda')})")
print(f"PROJECT_ROOT = {ROOT}")
print(f"FIGURES_DIR  = {FIGURES_DIR}")
"""
    )
)

cells.append(new_markdown_cell("## 2A — Setup e schema"))

cells.append(
    new_markdown_cell(
        f"""### Apontamentos
- Linhas: **{R2B['apontamentos_shape'][0]:,}**, colunas: **{R2B['apontamentos_shape'][1]}**
- Memoria carregado em pandas: **{R2B['apontamentos_mem_mb']:.1f} MB** (OK)
- Periodo: `{R2B['apontamentos_periodo']['min_inicio']}` -> `{R2B['apontamentos_periodo']['max_inicio']}` (Inicio)
- Sem nulos. Sem duplicados (Id e linha completa).

### Telemetria (limpa)
- Linhas totais: **{R2B['telemetria_total_rows']:,}** (lazy via duckdb)
- Periodo: `{R2B['telemetria_periodo']['min']}` -> `{R2B['telemetria_periodo']['max']}`
- Volume mensal (eventos): {{
{', '.join([f'"{r["mes_str"]}":{r["n"]:,}' for r in R2B['telemetria_volume_mes']])}
}}
- Sem nulos significativos. `Valor_num` (limpo): apenas {R2B['telemetria_pct_null']['Valor_num']:.4f}% nulos.
- Sem duplicados em `Id_Eventos_Telemetria`.

### Cardinalidades
- Equipamentos (TAG): **{R2B['telemetria_cardinalidades']['n_tag']}**
- Frotas (Tag_Frota): **{R2B['telemetria_cardinalidades']['n_frota']}**
- Tipos: **{R2B['telemetria_cardinalidades']['n_tipo']}**
- Localidades: **{R2B['telemetria_cardinalidades']['n_localidade']}** (Itabira unico — confirmado)
- Alarmes distintos (texto): **{R2B['telemetria_cardinalidades']['n_alarme']}**
- Id_Alarme distintos: **{R2B['telemetria_cardinalidades']['n_alarme_id']}** (~2x os nomes — multiplos IDs por alarme entre OEMs)
- Operadores anonimizados: **{R2B['telemetria_cardinalidades']['n_operador']}**
"""
    )
)

cells.append(
    new_code_cell(
        """con = get_connection()
rel_tel = load_telemetria_lazy(con)
TEL = '(' + rel_tel.sql_query() + ')'

apt = load_apontamentos(con)
print(f"apontamentos: {apt.shape}, mem={apt.memory_usage(deep=True).sum()/1e6:.1f} MB")
print()
print(apt.dtypes)
print()
n_tel = con.sql(f'SELECT COUNT(*) n FROM {TEL}').df().iloc[0,0]
print(f"telemetria total (lazy): {n_tel:,} linhas")
"""
    )
)

cells.append(new_markdown_cell("### Volumes mensais"))
cells.append(
    new_code_cell(
        """from IPython.display import Image, display
display(Image(filename=str(FIGURES_DIR / 'fig02_volume_telemetria_mensal.png')))
display(Image(filename=str(FIGURES_DIR / 'fig02_volume_apontamentos_mensal.png')))
"""
    )
)

cells.append(new_markdown_cell("### Distribuicao temporal de telemetria"))
cells.append(
    new_code_cell(
        """display(Image(filename=str(FIGURES_DIR / 'fig02_dist_temporal_telemetria.png')))
"""
    )
)

cells.append(new_markdown_cell("## 2B — Estatisticas descritivas"))
cells.append(
    new_markdown_cell(
        f"""**Valor_num** — variavel numerica unica do parquet (sensor):
| metrica | valor |
|---|---|
| n total | {R2B['telemetria_valor_stats']['n_total']:,.0f} |
| n nao-null | {R2B['telemetria_valor_stats']['n_nao_null']:,.0f} |
| media | {R2B['telemetria_valor_stats']['media']:.3f} |
| stddev | {R2B['telemetria_valor_stats']['stddev']:.3f} |
| min | {R2B['telemetria_valor_stats']['minv']:.3f} |
| P25 | {R2B['telemetria_valor_stats']['p25']:.3f} |
| P50 | {R2B['telemetria_valor_stats']['p50']:.3f} |
| P75 | {R2B['telemetria_valor_stats']['p75']:.3f} |
| max | {R2B['telemetria_valor_stats']['maxv']:.3f} |

Distribuicao **fortemente concentrada em zero**: P25=P50=P75=0. Cauda longa
ate 4347. Valor_num nao e a feature dominante para predizer Don't Go por si
so (correlacao ~ 0 com Is_Dont_Go, ver 2D).
"""
    )
)

cells.append(
    new_markdown_cell(
        """## 2C — Analise da variavel alvo

A flag `Is_Dont_Go` na telemetria e o ground truth (D006). Para evitar
distorcao de Recall e Lead time por Don't Gos repetidos do mesmo problema
fisico, aplicamos D009: **incidente = sequencia maximal de Is_Dont_Go=1 do
mesmo equipamento separada por gap <= 30 min**, e marcamos apenas o primeiro
evento como `is_incident_start=1`.
"""
    )
)

cells.append(
    new_markdown_cell(
        f"""### Taxa empirica global (testa H001)
- Eventos totais: **{R2C['taxa_is_dont_go']['n_total']:,}**
- Eventos com Is_Dont_Go=1: **{R2C['taxa_is_dont_go']['n_dontgo']:,}**
- Taxa global: **{R2C['taxa_is_dont_go']['taxa_pct']:.4f}%**

> **H001 (taxa < 0,1%)**: ✅ **CONFIRMADA**
> A taxa empirica de {R2C['taxa_is_dont_go']['taxa_pct']:.4f}% esta bem abaixo do limiar e configura **forte desbalanceamento**, justificando D002 (AUC-PR primaria) e D015 (sem SMOTE em series temporais).

### Distribuicao de gaps entre Don't Gos consecutivos do mesmo equipamento

| Tolerancia (min) | % de pares agrupados |
|---|---|
{chr(10).join([f"| {k} | {v:.2f}% |" for k, v in R2C['frac_pares_dentro_tol'].items()])}

> **D009 ratificada empiricamente**: tolerancia de 30 min agrupa 75% dos pares; 60 min ganharia +7 p.p. e 240 min (4h) +15 p.p. a custo de potencialmente unir incidentes fisicamente distintos.
> A nova **D018** ratifica 30 min como tolerancia oficial.

### Compressao eventos -> incidentes (tol = 30 min)
- Eventos Is_Dont_Go=1: {R2C['incidentes']['n_eventos_dontgo']:,}
- Incidentes Don't Go: **{R2C['incidentes']['n_incidentes_30min']:,}**
- Compressao media: **{R2C['incidentes']['compressao']:.2f} eventos/incidente**
"""
    )
)

cells.append(
    new_code_cell(
        """display(Image(filename=str(FIGURES_DIR / 'fig02_gaps_dontgo_consec.png')))
"""
    )
)

cells.append(
    new_markdown_cell(
        f"""### Distribuicao de incidentes por dimensao

**Por modelo de frota** (testa H004 — heterogeneidade entre frotas):
| Frota | # incidentes |
|---|---:|
{chr(10).join([f"| {r['Tag_Frota']} | {r['n_incidentes']:,} |" for r in R2C['incidentes_por_frota']])}

**793-D 5S concentra 56% dos incidentes** (2.821 de 5.025) — fortissima
heterogeneidade. **H004 ✅ CONFIRMADA com folga**.

**Por mes** (drift temporal):
| Mes | # incidentes |
|---|---:|
{chr(10).join([f"| {r['mes']} | {r['n_incidentes']:,} |" for r in R2C['incidentes_por_mes']])}

**Drift forte: jan-mar concentram 67% dos incidentes; abr-jun apenas 33%**.
Esta queda (-49% entre o pico de fev e o vale de mai) sera tratada como
**H010** (nova hipotese empirica).

**Por criticidade do alarme inicial**:
| Criticidade | # incidentes |
|---|---:|
{chr(10).join([f"| {r['crit_inicio']} | {r['n']:,} |" for r in R2C['incidentes_por_criticidade']])}

**52% dos incidentes comecam com alarme `Nao Critico`**. Confirma a tese de
acumulacao: Don't Go nao e disparado isoladamente por gravidade, mas por
**padrao de repeticao**. Sera **H011**.

**Top 10 alarmes que iniciam incidentes**:
| Alarme | # incidentes |
|---|---:|
{chr(10).join([f"| {r['alarme_inicio']} | {r['n']:,} |" for r in R2C['incidentes_por_alarme_top'][:10]])}
"""
    )
)

cells.append(
    new_code_cell(
        """display(Image(filename=str(FIGURES_DIR / 'fig03_incidentes_por_tag.png')))
display(Image(filename=str(FIGURES_DIR / 'fig03_incidentes_por_frota.png')))
display(Image(filename=str(FIGURES_DIR / 'fig03_incidentes_por_mes.png')))
display(Image(filename=str(FIGURES_DIR / 'fig03_incidentes_por_alarme.png')))
display(Image(filename=str(FIGURES_DIR / 'fig04_serie_temporal_incidentes.png')))
"""
    )
)

cells.append(
    new_markdown_cell(
        f"""## 2D — Analise de features

### Taxa de Is_Dont_Go por hora do dia, DOW e turno (H003)

**Por turno (06-18 / 18-06):**
| Turno | # eventos | # Don't Go | Taxa |
|---|---:|---:|---:|
{chr(10).join([f"| {r['turno']} | {r['n_eventos']:,} | {int(r['n_dontgo']):,} | {r['taxa_pct']:.4f}% |" for r in R2D['taxa_dontgo_por_turno']])}

> Razao noturno/diurno = **{R2D['taxa_dontgo_por_turno'][1]['taxa']/R2D['taxa_dontgo_por_turno'][0]['taxa']:.2f}x**.
> Diferenca real porem **modesta**.

**Por dia da semana**:
| DOW | Taxa |
|---|---:|
{chr(10).join([f"| {r.get('dow_nome', r['dow'])} | {r['taxa_pct']:.4f}% |" for r in R2D['taxa_dontgo_por_dow']])}

> Segunda-feira tem **1,77x** a taxa de domingo (0,072% vs 0,041%).
> **H003 ✅ CONFIRMADA parcialmente**: turno tem efeito modesto; dia da semana tem efeito maior, com peak na segunda.
"""
    )
)

cells.append(
    new_code_cell(
        """display(Image(filename=str(FIGURES_DIR / 'fig06_taxa_por_hora_dow.png')))
"""
    )
)

cells.append(
    new_markdown_cell(
        f"""### Taxa por frota e tipo (testa H004 sob outra lente)

**Por modelo de frota (taxa por evento):**
| Frota | n_eventos | n_dontgo | n_equip | Taxa |
|---|---:|---:|---:|---:|
{chr(10).join([f"| {r['Tag_Frota']} | {r['n_eventos']:,} | {int(r['n_dontgo']):,} | {r['n_equip']} | {r['taxa_pct']:.4f}% |" for r in R2D['taxa_dontgo_por_frota']])}

> A LeTourneau tem **1700x menos** Don't Go por evento que as Caterpillar 793-D.
> Isso pode refletir (a) menos estresse termico em escavadeira vs caminhao,
> (b) catalogo CMA majoritariamente OEM CAT — alarmes da LeTourneau podem
> estar nos 177 orfaos do O&M (ver 2D.4 abaixo).
> **Implicacao para Fase 3**: avaliar treino separado por frota.

**Por tipo de equipamento:**
| Tipo | Taxa |
|---|---:|
{chr(10).join([f"| {r['Tipo']} | {r['taxa_pct']:.4f}% |" for r in R2D['taxa_dontgo_por_tipo']])}

**Por classe (Activate/Inactive):**
| Classe | n_eventos | n_dontgo | Taxa |
|---|---:|---:|---:|
{chr(10).join([f"| {r['Classe']} | {r['n_eventos']:,} | {int(r['n_dontgo']):,} | {r['taxa_pct']:.4f}% |" for r in R2D['taxa_dontgo_por_classe']])}

> **Insight estrutural**: 19.795 dos 19.962 Don't Gos (99,2%) vem de
> eventos `Activate`. **Zero** vem de `Inactive`. **H012** (nova).

**Por criticidade:**
| Id | Criticidade | n_eventos | n_dontgo | Taxa |
|---|---|---:|---:|---:|
{chr(10).join([f"| {r['Id_Criticidade']} | {r['Criticidade']} | {r['n_eventos']:,} | {int(r['n_dontgo']):,} | {r['taxa_pct']:.4f}% |" for r in R2D['taxa_dontgo_por_criticidade']])}

> Don't Go ocorre **exclusivamente** em alarmes Critico (12,4% dos eventos
> crit) ou Nao Critico (2,1%). **Zero** em Informacional — pipeline da Vale
> aplica CMA so a alarmes severos.
"""
    )
)

cells.append(
    new_markdown_cell(
        f"""### Heatmap de correlacao (amostra 500k linhas)

Variaveis numericas: `Id_Criticidade`, `Valor_num`, `Is_Dont_Go`, `hora`,
`dow`, `mes`.

**Correlacoes notaveis:**
- `Id_Criticidade <-> Is_Dont_Go = -0,24`: negativa moderada (Id=1=Critico
  tem mais Don't Go; Id=3=Informacional tem zero). Nao e suficiente sozinha.
- `Valor_num <-> Is_Dont_Go = ~0`: o sensor cru nao prediz por si. Vai
  aparecer apenas em features agregadas.
- `hora/dow/mes <-> Is_Dont_Go = ~0`: temporal **linear** e fraco. Pode ser
  forte em features nao-lineares (ex: dia da semana cruzado com turno).
"""
    )
)

cells.append(
    new_code_cell(
        """display(Image(filename=str(FIGURES_DIR / 'fig05_heatmap_correlacao.png')))
display(Image(filename=str(FIGURES_DIR / 'fig05b_distribuicao_criticidade.png')))
"""
    )
)

cells.append(
    new_markdown_cell(
        f"""### Cobertura entre catalogos e telemetria (T3.4)

**O&M (Eventos O&M) — universo de eventos OEM possiveis**:
- # nomes unicos no catalogo O&M: **{R2D['cobertura_alarmes_om']['n_om_total']:,}**
- # alarmes distintos na telemetria: **{R2D['cobertura_alarmes_om']['n_telemetria_distintos']}**
- Match: **{R2D['cobertura_alarmes_om']['n_match']}** ({R2D['cobertura_alarmes_om']['pct_cobertura_telemetria']:.1f}%)
- Orfaos (telemetria sem match em O&M): **{R2D['cobertura_alarmes_om']['n_orfaos_telemetria']}**

> **H014 (nova)**: 25% dos alarmes da telemetria sao orfaos do catalogo O&M.
> Provavelmente alarmes OEM da LeTourneau ou eventos de sistema interno —
> nicho potencial de modos de falha nao cobertos pela CMA, alvo natural da
> PA-3 (anomalia nao supervisionada).

**CMA — alarmes que disparam Don't Go**:
- Eventos no CMA: **{R2D['cobertura_inicios_cma']['n_cma_total']}**
- Alarmes distintos no inicio dos incidentes: **{R2D['cobertura_inicios_cma']['n_inicios_distintos']}**
- Match: **{R2D['cobertura_inicios_cma']['n_match']}** ({R2D['cobertura_inicios_cma']['pct_match']:.1f}%)

> **H008 ✅ CONFIRMADA com folga**: **100% dos alarmes que iniciaram
> incidentes Don't Go** estao no catalogo CMA. A flag `Is_Dont_Go` da
> telemetria e plenamente coerente com o motor de regras CMA.
"""
    )
)

cells.append(new_markdown_cell("## 2E — Confirmacoes operacionais"))

cells.append(
    new_markdown_cell(
        f"""### T3.2 — Localidade unica
- # localidades distintas em todos os 6 parquets: **{len(R2E['localidades_distintas'])}** (`{R2E['localidades_distintas']}`)
- Por mes: 100% Itabira em todos os 6 meses

> **T3.2 RESOLVIDO**: Itabira e a localidade UNICA. Confirmacao formal feita
> sobre os 37M de eventos. **H006 (dependencia de localidade) e
> oficialmente inconclusiva por construcao** — sera incluida em Trabalhos
> Futuros (replicar em outras minas Vale).

### T3.6 — Pareamento Apontamento x Telemetria
Amostra de 1.002 ciclos estratificada por mes:

| Estatistica | Valor |
|---|---:|
| % ciclos com 0 eventos de telemetria (geral) | **{R2E['pareamento_pct_zero']:.2f}%** |
| % ciclos `Operando` com 0 eventos | **{R2E['pareamento_pct_zero_operando']:.2f}%** |

| Classe | n | media eventos/ciclo | mediana | % com 0 eventos |
|---|---:|---:|---:|---:|
{chr(10).join([f"| {r['apt_classe']} | {int(r['count'])} | {r['mean']:.2f} | {r['median']:.0f} | {r['pct_zero']:.2f}% |" for r in R2E['pareamento_por_classe']])}

> **T3.6 RESOLVIDO**: Hibernando/Manutencao/Parado tem alto % de ciclos sem
> telemetria — esperado. **Mas 19% dos ciclos `Operando` tambem tem 0
> eventos** — inconsistencia operacional real. **H013 (nova)**: ciclos
> "Operando com 0 eventos" provavelmente refletem telemetria offline ou
> dessincronia de relogio. Decisao **D020 (nova)**: marcar essa categoria
> com flag `tem_telemetria=0` no dataset de scoring, nao excluir.

### D016 — Operador inferido por moda
Amostra: 2.000 ciclos.

| Estatistica | Valor |
|---|---:|
| ciclos com >=1 evento com operador | **{R2E['operador_inferido']['n_inferivel']}** ({R2E['operador_inferido']['n_inferivel']/R2E['operador_inferido']['n_amostra']*100:.1f}%) |
| ciclos sem operador inferivel | **{R2E['operador_inferido']['n_amostra']-R2E['operador_inferido']['n_inferivel']}** ({(1-R2E['operador_inferido']['n_inferivel']/R2E['operador_inferido']['n_amostra'])*100:.1f}%) |
| share da moda — mediana | **{R2E['operador_inferido']['share_moda_describe']['50%']*100:.1f}%** |
| share da moda — P95 | **{R2E['operador_inferido']['share_moda_describe']['95%']*100:.1f}%** |
| % ciclos com share >= 80% | **{R2E['operador_inferido']['pct_share_ge_80']:.2f}%** |

> **D016 VALIDADA com folga**: o threshold de 80% (definido a priori) e na
> pratica conservador — 99,67% dos ciclos com operador inferivel batem isso.
> Decisao **D018 (nova)**: ratificar 80% mas anotar que poderia descer ate
> 50% sem perda. 38,5% dos ciclos nao tem operador inferivel (telemetria
> silenciosa). **H005 e testavel** sobre os 61,5%.

### T3.7 — Origem da coluna `Porte`
- `Porte` aparece SO no exemplo `desenvolver_dontgo.xlsx`, **nao na
  telemetria bruta** ({len(R2E['exemplo_porte']['valores_unicos'])} valor: `{R2E['exemplo_porte']['valores_unicos']}`).
- Tag_Frota no exemplo: `{R2E['exemplo_porte']['tag_frota_no_exemplo']}` (so um modelo).

> **T3.7 RESOLVIDO**: `Porte` foi acrescentada manualmente pelo time da Vale
> ao gerar o exemplo. **Nao depender dela** no modelo de producao. Decisao
> **D019 (nova)**: criar mapeamento explicito `Tag_Frota -> Porte` em
> `src/data/mappings.py` na Fase 3, com base em catalogo OEM externo.
"""
    )
)

cells.append(
    new_markdown_cell(
        """## 2F — Sintese das hipoteses

| Hipotese | Status | Evidencia resumida |
|---|---|---|
| **H001** taxa Don't Go < 0,1% | ✅ CONFIRMADA | 0,054% global em 37M eventos |
| **H002** padrao sequencial precursor | ⏸️ aberta | precisa janela temporal por incidente — Fase 3 |
| **H003** concentracao temporal (turno/dia) | ✅ PARCIAL | DOW=Seg tem 1,77x DOW=Dom; turno noturno 1,15x diurno |
| **H004** heterogeneidade entre frotas | ✅ CONFIRMADA | 793-D 4S/3S taxa 1,7x maior que 5S/2S por evento; 793-D 5S concentra 56% dos incidentes absolutos |
| **H005** efeito do operador | ⏸️ TESTAVEL | D016 viavel em 61,5% dos ciclos |
| **H006** dependencia de localidade | 🛑 INCONCLUSIVA POR CONSTRUCAO | Itabira unico — vai para Trabalhos Futuros |
| **H007** janela otima 4h | ⏸️ aberta | testar na Fase 4 com 6 horizontes paralelos (D001) |
| **H008** coerencia flag x CMA | ✅ CONFIRMADA com folga | 100% dos alarmes que iniciam incidentes estao no CMA |
| **H009** familias funcionais como features | ⏸️ aberta | testar como baseline na Fase 4 |

### Hipoteses novas derivadas da EDA (H010+)

| Hipotese | Resumo | Como testar |
|---|---|---|
| **H010** | Drift temporal de prevalencia: jan-mar concentram 67% dos incidentes; jun apenas 50% do pico de fev (-49%) | Comparar prevalencia entre folds do walk-forward (D011) |
| **H011** | Don't Go nasce de **acumulacao de nao-criticos**, nao de severidade isolada — 52% dos incidentes comecam com alarme `Nao Critico` | Feature: contagem de nao-criticos do mesmo evento na janela |
| **H012** | Don't Go ocorre exclusivamente em `Classe=Activate` (99,2%); zero em `Inactive` | Filtrar `Inactive`/`NULL` no train set |
| **H013** | 19% dos ciclos `Operando` tem zero eventos de telemetria — inconsistencia operacional | Cruzar com horario do incidente, frota |
| **H014** | 25% dos alarmes da telemetria sao orfaos do catalogo O&M (177 de 710) | Cruzar orfaos com Tag_Frota — provavel concentracao em LeTourneau |
| **H015** | n_alarme_id = 2x n_alarme: mesmo nome textual com IDs distintos por OEM | `SELECT Alarme, COUNT(DISTINCT Id_Alarme) FROM tel GROUP BY Alarme HAVING COUNT > 1` |
| **H016** | LeTourneau (escavadeira) precisa de modelo separado: 1700x menos Don't Go por evento que 793-D | Treinar modelo separado e comparar |
"""
    )
)

cells.append(
    new_markdown_cell(
        """## 2G — Decisoes empiricas registradas (D018+)

| Id | Decisao | Origem |
|---|---|---|
| **D018** | Ratificar tolerancia de 30 min para incidente Don't Go (D009) — agrupa 75% dos pares consecutivos do mesmo equipamento; aumentar para 60 min ganharia +7 p.p. mas une eventos potencialmente independentes | 2C.2 |
| **D019** | Criar mapeamento explicito `Tag_Frota -> Porte` em `src/data/mappings.py` (Fase 3) — coluna `Porte` so aparece no .xlsx de demo, nao na telemetria | 2E.4 |
| **D020** | Marcar ciclos `Operando` com 0 eventos como `tem_telemetria=0` (flag); nao excluir do dataset, mas tratar features como NaN | 2E.2 |
| **D021** | Threshold de 80% para operador inferido (D016) e na pratica conservador — manter 80% para 2026 mas registrar que 50% seria viavel | 2E.3 |
| **D022** | `Classe=NULL` em LeTourneau e estrutural (auditoria 2026-04-30) — incluir como categoria explicita; reforca H016 | Auditoria §3 A2 |
| **D023** | Dispensa formal de `pmdarima` (auditoria) — `lifelines` cobre D017 (Cox+Weibull) e `prophet 1.3.0` cobre serie temporal | Auditoria §10 |
"""
    )
)

cells.append(
    new_markdown_cell(
        """## 2I — Auditoria pos-EDA (rodada apos a Fase 2 fechar)

> Auditoria executada por `notebooks/_audit_fase2.py` em 2026-04-30 — apos a
> Fase 2 fechar formalmente — para verificar omissoes, bugs latentes e
> validar conclusoes na populacao total.

### Achados que refinam ou corrigem conclusoes anteriores

#### Refinamento de H010 — drift normalizado

A queda de incidentes de fev a jun foi reportada como −49% usando contagens
brutas. Normalizando por **incidentes por milhao de eventos de telemetria**
(que cresce 45% no periodo), a queda real e:

| Mes | n_evt | n_inc | inc/M evt |
|---|---:|---:|---:|
""" + chr(10).join([f"| {r['mes_str']} | {r['n_evt']:,} | {r['n_inc']:,} | {r['inc_per_milhao_evt']:.1f} |" for r in RAUD['h010_normalizado']]) + f"""

**Reducao real peak (fev) -> vale (jun): −72,5%** (nao −49%). A diferenca
vem de a telemetria crescer enquanto incidentes caem.

#### H001 reportada por mes (nao apenas global)

A taxa global de 0,054% esconde drift severo entre meses:

| Mes | Taxa |
|---|---:|
""" + chr(10).join([f"| {r['mes_str']} | {r['pct']:.4f}% |" for r in RAUD['taxa_dontgo_por_mes']]) + f"""

**Razao max/min = 3,71x**. Implicacao: ao aplicar walk-forward (D011), os
folds terao prevalencias muito diferentes. Metricas absolutas (AUC-PR) nao
sao diretamente comparaveis entre folds — Lift = AUC-PR / prevalencia
permite comparacao normalizada (justificativa adicional para D012).

#### NIVEL CMA — analise que faltava

| NIVEL | n incidentes |
|---|---:|
""" + chr(10).join([f"| {k} | {v:,} |" for k, v in RAUD['nivel_cma_incidentes'].items()]) + f"""

**80,8% Muito Alto + 19,2% Alto.** LeTourneau **so** tem incidentes Muito
Alto (32 de 32). Cross com Criticidade do alarme inicial revela: regras CMA
"Alto" sao iniciadas majoritariamente por alarmes **Nao Criticos** (741 vs
225) — confirma o mecanismo de H011 (acumulacao de nao-criticos).

#### Refinamento de H015 — distribuicao de # IDs por nome de Alarme

Reportei "n_alarme_id ~ 2x n_alarme" como se fosse uniforme. Real:

- **80,2% (571 alarmes) com 1 unico Id_Alarme**
- 19,8% (141 alarmes) com >1 Id_Alarme
- **Cauda longa**: alguns alarmes tem 25, 27, 30, 49, 50 IDs distintos

Os 141 alarmes "compartilhados entre OEMs" sao exatamente os bons
candidatos a "familias funcionais" (H009).

#### Validacao formal de H003 — chi-square

| Teste | chi2 | p-value | dof |
|---|---:|---:|---:|
| Turno x Is_Dont_Go | {RAUD['h003_turno_chi2']['chi2']:.1f} | {RAUD['h003_turno_chi2']['p']:.2e} | {RAUD['h003_turno_chi2']['dof']} |
| DOW x Is_Dont_Go | {RAUD['h003_dow_chi2']['chi2']:.1f} | {RAUD['h003_dow_chi2']['p']:.2e} | {RAUD['h003_dow_chi2']['dof']} |

Ambos rejeitam H0 (independencia) com p << 0,001 — **H003 confirmada
formalmente**.

#### Cramer V para forca da associacao categorica

| Variavel | V | Categorias |
|---|---:|---:|
""" + chr(10).join([f"| {k} | {v['cramers_v']:.4f} | {v['n_categorias']} |" for k, v in RAUD['cramers_v'].items()]) + f"""

**Criticidade (V=0,27)** e o categorico mais informativo, seguido de Classe
(0,19) e TAG (0,14). Frota e Tipo tem associacao fraca (~0,07). Nenhuma
variavel sozinha resolve — sinal preditivo virá de combinacoes temporais.

#### H013 confirmada na populacao total

A amostra de 471 ciclos `Operando` deu 19,1% (CI 95%: [15,6%, 22,6%]).
Sobre **182.527 ciclos `Operando` totais**: **17,6%** tem 0 eventos de
telemetria. CI da amostra capturou a verdade populacional.

#### Falso alarme corrigido — gap apontamentos vs telemetria

A amostra de 2.000 ciclos sugeriu que CA65916 e CA65793 tinham gaps de
95-112 dias entre primeiro apontamento e primeira telemetria. Em populacao
total, **so CA65916 tem gap > 7 dias** (gap = -24 d, telemetria comeca antes
dos apontamentos). Lição: validacoes de pareamento populacional devem usar
populacao total, nao amostra.

#### 167 Don't Gos com Classe NULL = 167 LeTourneau (verificado)

Cross Classe x Tag_Frota dos 19.962 Don't Gos confirmou: **todos os 167
NULL sao da LeTourneau L 1850**, e todas as 4 frotas 793-D usam Activate
exclusivamente. Reforca H016 (LeTourneau requer modelo separado).

### Bugs latentes corrigidos no codigo (sem mudanca em conclusoes)

1. **`ANY_VALUE` em incidentes**: substituido por
   `MIN(CASE WHEN is_incident_start=1 THEN col END)` — semanticamente
   correto e portavel. Verificacao mostrou que ANY_VALUE retornava
   coincidentemente o evento de inicio neste dataset.
2. **Denominador de share_moda em D016**: substituido pelo total de
   eventos do ciclo (incluindo NULL). Verificacao mostrou que neste
   dataset a versao bug coincide com a correta porque `Nome_Operador_Anon`
   e universalmente preenchido nos eventos que existem.
3. **Encoding cp1252 dos JSONs**: agora todos os runners escrevem com
   `encoding='utf-8'` explicito.
4. **Notebook sem kernelspec**: agora tem `kernelspec` e `language_info`
   na metadata.

### Propriedade emergente do dataset descoberta na auditoria

`Nome_Operador_Anon IS NOT NULL` para 100% dos eventos quando ha telemetria.
Isso significa que "ciclo sem operador inferivel" e "ciclo sem telemetria"
sao conceitos **equivalentes** neste dataset, nao independentes.
"""
    )
)

cells.append(
    new_markdown_cell(
        """## 2H — Proximos passos (Fase 3 — Data Preparation)

1. Tratar a inconsistencia "Operando + 0 eventos" (D020).
2. Construir features sequenciais por janela respeitando D010 (anti-leakage,
   blackout 5 min).
3. Criar mapeamento `Tag_Frota -> Porte` (D019).
4. Definir critério de outliers em `Valor_num`.
5. Avaliar treino segregado por frota (LeTourneau vs 793-D — H016).
6. Construir matriz de features para os 6 horizontes paralelos H ∈ {1,2,4,6,8,12} h.

> **Volume final do training set**: ~17M sliding windows de 15 min × 35
> equipamentos × 6 meses (D008). Operacional em duckdb + pyarrow lazy.
"""
    )
)

nb["cells"] = cells
# Kernelspec explicito — sem isso, Jupyter pede ao usuario para escolher
# kernel toda vez que abrir. Tambem permite que `nbconvert --execute` rode.
nb["metadata"]["kernelspec"] = {
    "name": "python3",
    "display_name": "Python 3",
    "language": "python",
}
nb["metadata"]["language_info"] = {
    "name": "python",
    "version": "3.13.7",
    "mimetype": "text/x-python",
    "file_extension": ".py",
    "pygments_lexer": "ipython3",
}
out_path = ROOT / "notebooks" / "02_data_understanding_eda.ipynb"
nbf.write(nb, str(out_path))
print(f"notebook salvo em {out_path}")
print(f"# cells: {len(cells)}")
print(f"kernelspec: {nb.metadata['kernelspec']}")
