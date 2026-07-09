# Model Card — `dontgo-lightgbm-multihorizon-v1.0`

> Cartão modelo nos moldes de Mitchell et al. (2019), *Model Cards for Model Reporting*. Documenta o modelo PA-1 (LightGBM calibrado, multi-horizonte) treinado no projeto Vale Don't Go.

---

## 1. Detalhes do Modelo

| Atributo | Valor |
|---|---|
| **Nome do modelo** | `dontgo-lightgbm-multihorizon-v1.0` |
| **Família** | LightGBM (Gradient Boosting on Trees) |
| **Versão** | 1.0 (treinado em 2026-05-04) |
| **Calibração** | Isotonic em H ∈ {1, 2, 4} h, Platt em H ∈ {6, 8, 12} h (D037) |
| **Horizontes** | 6 modelos paralelos: 1, 2, 4, 6, 8, 12 h |
| **Tipo de problema** | Classificação binária multi-horizonte por janela deslizante 15 min |
| **Autores** | Diego Henrique Xavier (UFU/FAGEN/GI) — Orientadora: Profª. Drª. Noézia Maria Ramos |
| **Contato** | diegohenrique.mail@gmail.com |
| **Licença** | Acadêmica (TCC). Uso em produção requer acordo formal com Vale S.A. |
| **Repositório** | `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale` |

### 1.1. Arquivos canônicos

- Boosters serializados: `outputs/models/lgbm_h{H}_holdout_jun.txt` (6 arquivos)
- Calibradores: `outputs/models/lgbm_calibrated_h{H}.joblib` (6 arquivos)
- Hyperparams: `outputs/models/lgbm_best_params.json`
- Schema de features: 89 colunas — ver `data/processed/features_2025-{01..06}.parquet`

---

## 2. Uso Pretendido

### 2.1. Casos de uso primários

- **Antecipação operacional** de incidentes Don't Go em frotas Caterpillar 793-D (todas variantes 2S/3S/4S/5S) operando em Itabira/MG.
- **Suporte à programação de manutenção**: dispatcher recebe probabilidades em horizontes 1h–12h e prioriza intervenções.
- **Pesquisa metodológica em manutenção preditiva**: o framework multi-horizonte + multi-PA é genérico e replicável.

### 2.2. Usuários-alvo

- **Primário**: dispatchers de operação Vale Itabira.
- **Secundário**: engenheiros de confiabilidade, analistas de dados de manutenção.
- **Terciário**: pesquisadores em manutenção preditiva industrial.

### 2.3. Casos de uso fora do escopo (NÃO usar para)

- ❌ Frotas LeTourneau L 1850 — PA-3 declarado exploratório (D036), captura ~6%.
- ❌ Outras localidades Vale (Carajás, S11D, Mariana) sem replicação prévia (D005, H006 inconclusiva).
- ❌ Decisões automáticas críticas sem revisão humana — modelo é *advisory*.
- ❌ Outros equipamentos fora da família 793-D — schema de features é específico.
- ❌ Janelas com `tem_telemetria=0` (17,6% dos ciclos Operando — H013) — modelo retorna predição, mas a confiança é baixa.

---

## 3. Métricas de Desempenho

### 3.1. Tabela canônica (holdout JUN 2025)

| H | AUC-PR | Lift | AUC-ROC | ECE | Recall@P=0.5 (janela) | Recall por incidente | Lead p50 (min) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1h | 0,207 | 6,71 | 0,817 | 0,010 | 0,090 | 0,108 | 50,3 |
| 2h | 0,268 | 5,04 | 0,793 | 0,022 | 0,119 | 0,210 | 101,5 |
| 4h | 0,312 | 3,48 | 0,762 | 0,046 | 0,189 | 0,356 | 215,6 |
| 6h | 0,357 | 2,94 | 0,748 | 0,023 | 0,210 | 0,440 | 317,2 |
| 8h | 0,374 | 2,53 | 0,732 | 0,015 | 0,258 | 0,546 | 428,2 |
| 12h | 0,412 | 2,11 | 0,712 | 0,027 | 0,288 | 0,648 | 653,6 |

Fonte: `reports/eda_results/fase5a_consolidado.json` (auditado em `notebooks/_audit_fases_0_a_5.py`, 70/70 PASSA).

### 3.2. Intervalos de confiança bootstrap 95% (Frente F2 da Fase 6, 1000 resamples)

| H | AUC-PR (média) | AUC-PR IC 95% | Lift IC 95% | Recall por incidente IC 95% |
|---:|---:|---|---|---|
| 1h | 0,208 | [0,188; 0,228] | [6,13; 7,38] | [0,081; 0,134] |
| 2h | 0,268 | [0,250; 0,286] | [4,72; 5,35] | [0,177; 0,246] |
| 4h | 0,312 | [0,298; 0,326] | [3,33; 3,64] | [0,314; 0,399] |
| 6h | 0,357 | [0,344; 0,370] | [2,84; 3,05] | [0,395; 0,483] |
| 8h | 0,374 | [0,362; 0,385] | [2,45; 2,60] | [0,503; 0,589] |
| 12h | 0,412 | [0,402; 0,422] | [2,06; 2,16] | [0,603; 0,686] |

Fonte: `reports/eda_results/fase6_bootstrap_ci.json`.

### 3.3. Análise de fairness por operador (Frente F1 da Fase 6)

98,8% dos 491 incidentes em JUN têm operador inferível na janela de 30 min pré-incidente. Após filtro `n ≥ 10 incidentes/operador`, 4 operadores qualificam.

| H | Gini(Recall) | Disparidade Q75/Q25 | Razão Top/Bottom (extremos) |
|---:|---:|---:|---:|
| 1h | 0,427 | 2,52 | OP_140 (0,87) / OP_275 (0,25) = 3,5× |
| 4h | 0,230 | 1,40 | OP_140 (0,87) / OP_275 (0,19) = 4,6× |
| 12h | 0,156 | 1,24 | OP_140 (0,87) / OP_275 (0,31) = 2,8× |

**Interpretação**: o operador OP_275 apresenta `Recall por incidente` consistentemente inferior aos demais (n=16 incidentes, 5 detectados em H=12h). Possíveis causas:

- Padrão operacional do operador difere da população média (ex.: estilo mais conservador que mascara sinais precursores).
- Equipamentos sob OP_275 em maior fração de tempo apresentam telemetria com ruído distinto.
- Amostra ainda pequena (n=16) — o intervalo bootstrap pode atravessar zero.

**Recomendação operacional**: monitorar mensalmente a estatística de Recall/operador na operação plena (Fase de Implantação 2 do Cap. 6). Se OP_275 mantiver disparidade após 3 meses com `n ≥ 30`, escalar para análise técnica direcionada (revisão de features, pode ser viés sistemático).

Fonte: `reports/eda_results/fase6_fairness_operador.json` + `reports/tables/fase6_fairness_operador.csv`.

---

## 4. Dados de Treino e Avaliação

### 4.1. Dados de treino

- **Origem**: telemetria mensal Itabira/MG, jan–mai 2025 (5 meses).
- **Volume**: ~30,9 milhões de eventos brutos → ~282 mil janelas após preparação (Fase 3).
- **Buffer**: 4h entre fim de treino e início de teste (D034).
- **Calibração**: split holdout interno (último 20% temporal de cada fold).

### 4.2. Dados de avaliação

- **Holdout intocado**: junho 2025 (~7,85 milhões de eventos brutos → ~46 mil janelas).
- **Walk-forward 4 folds**: jan→fev, jan-fev→mar, jan-mar→abr, jan-abr→mai (D011).
- **Auditoria buffer**: 1,18% overlap residual no fold 1 (D034 ratifica).

### 4.3. Características demográficas e operacionais relevantes

- **Localidade**: 100% Itabira/MG (D005, H006).
- **Frota**: 35 equipamentos físicos, 5 modelos (793-D 2S/3S/4S/5S, LeTourneau L 1850).
- **Distribuição de incidentes**: 56% concentrados na frota 793-D 5S (H004 confirmada).
- **Operadores**: 395 anonimizados na telemetria; 61,5% dos ciclos com operador inferível confiável (D016).
- **Turnos**: 12h (06h-18h / 18h-06h); chi² formal p<10⁻²² para turno e p<10⁻¹⁵⁷ para dia da semana (H003).

### 4.4. Drift documentado

- **Prevalência Don't Go**: queda de 72,5% entre fevereiro (pico) e junho (H010 confirmada).
- **PSI top-10 features**: 0,16 < 0,25 (estável).
- **Interpretação**: drift de label sem drift de feature → mudança operacional (intervenção da Vale em resposta aos sinais), não degradação física.

---

## 5. Considerações Éticas

### 5.1. Riscos identificados

1. **Viés por operador** (ver Seção 3.3). Disparidade fator ~3,5× entre top e bottom operador. Mitigação: monitoramento mensal (Cap. 6 §6.4).
2. **Dependência de dados anonimizados**. Modelo não usa identidade direta do operador, mas pode inferir padrões correlacionados — atenção a deploy regulatório.
3. **Falsos negativos** custam parada não-programada (downtime estimado 60 min médio). Falsos positivos custam manutenção desnecessária. Não há simetria de custo.
4. **Drift de prevalência alto** (H010): se a Vale alterar o regime operacional após deploy, modelo degrada rapidamente. Gatilho de retreino: `|Δprev/p_treino| ≥ 0,30`.

### 5.2. Limitações conhecidas

- PA-2 (sobrevivência) C-index = 0,62 (alvo 0,70). Modelo complementar, não primário.
- PA-3 (anomalia LeTourneau) captura 6% top-10 (alvo 50%). Declarado exploratório.
- Cap de 60 min em apontamentos do sistema da Vale. Reconstrução de paradas físicas (D040) mitiga via gap-merge ≤5 min.
- Localidade única Itabira: generalização para Carajás/S11D/Mariana **não validada** (Trabalho Futuro #1).

### 5.3. Recomendações de uso responsável

1. **Sempre operar em modo `advisory`** nas Fases 1 e 2 do roadmap (Cap. 6 §6.3). Decisão final = humana.
2. **Auditar fairness por operador** mensalmente. Disparidade ≥2× sustentada deve disparar revisão técnica.
3. **Monitorar drift** com gatilhos formais (Cap. 6 §6.4): PSI ≥ 0,25 ou prevalência divergente ≥30% disparam retreino.
4. **Não substituir manutenção preventiva regular** pelo modelo. Este é uma camada *adicional*, não substituta.
5. **Re-treinar a cada 6 meses** mesmo sem gatilhos — sazonalidade operacional é real.

---

## 6. Caveats e Recomendações Adicionais

### 6.1. O que o modelo NÃO faz

- ❌ Não prediz o tipo específico do alarme que disparará.
- ❌ Não recomenda ação de manutenção (qual peça trocar).
- ❌ Não estima custo financeiro do incidente.
- ❌ Não estima probabilidade conjunta de múltiplos equipamentos simultaneamente (cada modelo é independente por TAG-janela).

### 6.2. O que o modelo faz bem

- ✅ Probabilidade calibrada de incidente em 6 horizontes paralelos.
- ✅ Lead time mediano confiável: 50 min (H=1h) a 654 min (H=12h).
- ✅ Recall por incidente alto: 10,8% (H=1h) → 64,8% (H=12h).
- ✅ Interpretabilidade via SHAP (features dominantes: `n_fam_engine_coolant_*h`, `n_crit_*h`, `Tag_Frota`).

### 6.3. Comportamento observado em casos extremos

- **Equipamento sem telemetria** (`tem_telemetria=0`, 17,6% dos ciclos): modelo retorna baseline de prevalência, não confiar.
- **Início de turno** (primeiros 30 min): janela de lookback incompleta; flag `lookback_completo=0` no dataset; predição é ainda emitida mas com confiança reduzida.
- **Equipamento novo na frota** (sem histórico em jan-mai): modelo trata como genérico do `Tag_Frota`; sem personalização TAG-específica.

---

## 7. Meta-informação

| Atributo | Valor |
|---|---|
| **Versão deste cartão** | 1.0 |
| **Data de emissão** | 2026-05-10 |
| **Próxima revisão programada** | 2026-11-10 (6 meses) ou na primeira atualização do modelo |
| **Auditoria associada** | `notebooks/_audit_fases_0_a_6.py` (estende `_audit_fases_0_a_5.py`) |
| **Decisões registradas** | D001–D040 em `docs/decisions.md` |
| **Hipóteses pré-registradas** | H001–H017 em `docs/hypotheses.md` |

---

## 8. Referências

- Mitchell, M. et al. (2019). *Model Cards for Model Reporting*. FAT* '19.
- Saito, T. & Rehmsmeier, M. (2015). *The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets*. PLoS ONE.
- Lundberg, S. & Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions*. NIPS.
- Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NIPS.

Para a lista completa de referências, consultar `docs/article_dontgo/bibliografia.bib`.
