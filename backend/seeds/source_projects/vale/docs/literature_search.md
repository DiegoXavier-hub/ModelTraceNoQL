# Estratégia de Busca Bibliográfica — Referencial Teórico (Cap. 2 do TCC)

> **Objetivo**: orientar a busca por artigos científicos para o referencial teórico do TCC sobre
> *Antecipação de Alertas Críticos "Don't Go" em Frotas de Mineração*. Cada bloco abaixo cobre
> uma seção previsível do Capítulo 2 do `.tex` ABNT.
>
> **Princípio de construção**: `(sinônimos_conceito_A com OR) AND (sinônimos_conceito_B com OR) ...`
> Cada conceito **deve** aparecer (interseção via `AND`); a forma de expressá-lo pode variar
> (alternativas via `OR`). Aspas duplas em torno de termos compostos forçam busca pela frase exata.

---

## 1. Bases de dados recomendadas

| Base | URL | Quando usar |
|---|---|---|
| **Scopus** | scopus.com | Cobertura ampla de engenharia + métricas de citação |
| **Web of Science** | webofknowledge.com | Alta qualidade; permite "citing/cited" navegação |
| **IEEE Xplore** | ieeexplore.ieee.org | Específico para engenharia, IoT, sensores, ML em sistemas |
| **ScienceDirect** | sciencedirect.com | Journals Elsevier (Mechanical Systems and Signal Processing, Reliability Engineering) |
| **Google Scholar** | scholar.google.com | "Pesca" inicial, citation chains, teses |
| **SciELO** | scielo.br | Artigos brasileiros (importante para ABNT) |
| **CAPES Periódicos** | periodicos.capes.gov.br | Acesso institucional UFU a quase tudo acima |
| **arXiv** | arxiv.org | Preprints de ML recentes (LightGBM, SHAP, etc.) |

### Filtros recomendados em todas as buscas

- **Período**: 2018–2026 (últimos 5–8 anos para state-of-the-art); abrir para 2010+ apenas em fundamentos clássicos.
- **Tipo de documento**: `Article OR Conference Paper OR Review`.
- **Idioma**: `English OR Portuguese`.
- **Áreas de conhecimento** (Scopus/WoS): Engineering, Computer Science, Decision Sciences.

---

## 2. Blocos conceituais (vocabulário controlado)

Use estes blocos como **componentes** que você combina com `AND` para formar strings específicas.
Cada bloco lista termos em **inglês** (priorizado nas bases internacionais) e **português** (priorizado em SciELO/teses brasileiras).

### Bloco D — Domínio: Mineração e equipamentos móveis

**EN**: `("open pit mining" OR "open-pit mining" OR "surface mining" OR "iron ore mining" OR "mining operation*" OR "haul truck*" OR "off-road truck*" OR "off-highway truck*" OR "mining fleet*" OR "mobile mining equipment" OR "load-haul-dump" OR "earth-moving equipment")`

**PT**: `("mineração a céu aberto" OR "mineração de minério de ferro" OR "frota de mineração" OR "caminhão fora de estrada" OR "caminhões fora-de-estrada" OR "equipamentos móveis de mineração" OR "operação de mina")`

### Bloco M — Manutenção preditiva e prognóstico

**EN**: `("predictive maintenance" OR "prognostic*" OR "condition monitoring" OR "condition-based maintenance" OR "PHM" OR "prognostics and health management" OR "RUL prediction" OR "remaining useful life" OR "fault prognosis" OR "early warning system*")`

**PT**: `("manutenção preditiva" OR "monitoramento de condição" OR "prognóstico de falhas" OR "diagnóstico de falhas" OR "vida útil residual" OR "alerta precoce")`

### Bloco F — Predição/Detecção de falha

**EN**: `("failure prediction" OR "fault detection" OR "fault prediction" OR "anomaly detection" OR "alarm prediction" OR "incident prediction" OR "breakdown prediction" OR "machine failure")`

**PT**: `("predição de falhas" OR "detecção de falhas" OR "detecção de anomalias" OR "predição de alarme*" OR "falha de máquina")`

### Bloco T — Telemetria e dados industriais

**EN**: `(telemetry OR "industrial IoT" OR IIoT OR SCADA OR "sensor data" OR "operational data" OR "machine data" OR "OEM alarm*" OR "vehicle telematics")`

**PT**: `(telemetria OR "internet das coisas industrial" OR "dados de sensores" OR "dados operacionais" OR "alarmes OEM")`

### Bloco ML — Machine learning (genérico)

**EN**: `("machine learning" OR "deep learning" OR "supervised learning" OR "data-driven model*" OR "data mining" OR "artificial intelligence")`

**PT**: `("aprendizado de máquina" OR "aprendizagem de máquina" OR "aprendizado profundo" OR "inteligência artificial" OR "mineração de dados")`

### Bloco GB — Gradient boosting (algoritmos específicos do projeto)

**EN**: `("gradient boosting" OR XGBoost OR LightGBM OR CatBoost OR "boosted trees" OR "tree-based ensemble")`

**PT**: `("gradient boosting" OR XGBoost OR LightGBM OR CatBoost OR "árvores impulsionadas")`

### Bloco SEQ — Modelos sequenciais / temporais

**EN**: `(LSTM OR "long short-term memory" OR GRU OR transformer OR "recurrent neural network" OR RNN OR "temporal convolutional" OR TCN OR "sequence model*")`

**PT**: `(LSTM OR "redes neurais recorrentes" OR transformer OR "modelos sequenciais")`

### Bloco AD — Detecção de anomalia (não supervisionado)

**EN**: `("isolation forest" OR "one-class SVM" OR autoencoder OR "variational autoencoder" OR "unsupervised anomaly detection" OR "novelty detection" OR "outlier detection")`

**PT**: `("floresta de isolamento" OR autoencoder OR "detecção de anomalia* não supervisionada" OR "detecção de novidade")`

### Bloco SUR — Análise de sobrevivência / Time-to-event

**EN**: `("survival analysis" OR "Cox proportional hazards" OR "Cox regression" OR "Weibull AFT" OR "accelerated failure time" OR "time-to-event" OR "hazard model*" OR "Kaplan-Meier")`

**PT**: `("análise de sobrevivência" OR "regressão de Cox" OR "riscos proporcionais" OR "tempo até evento" OR "modelos de risco")`

### Bloco IMB — Classes desbalanceadas / Eventos raros

**EN**: `("class imbalance" OR "imbalanced data*" OR "rare event*" OR "minority class" OR "skewed distribution" OR SMOTE OR "focal loss" OR "cost-sensitive learning")`

**PT**: `("classes desbalanceadas" OR "dados desbalanceados" OR "eventos raros" OR "aprendizado sensível a custo")`

### Bloco MET — Métricas de avaliação

**EN**: `("AUC-PR" OR "AUC-ROC" OR "precision-recall curve" OR "F1-score" OR "F-beta" OR "Brier score" OR "expected calibration error" OR "calibration" OR "lift curve")`

**PT**: `("AUC-PR" OR "curva ROC" OR "curva precisão-recall" OR "F1-score" OR "Brier" OR "calibração de probabilidade*")`

### Bloco INT — Interpretabilidade / XAI

**EN**: `(SHAP OR "Shapley value*" OR "explainable AI" OR XAI OR "interpretable machine learning" OR "feature importance" OR "permutation importance" OR LIME)`

**PT**: `(SHAP OR "valores de Shapley" OR "IA explicável" OR "aprendizado de máquina interpretável" OR "importância de variáveis" OR LIME)`

### Bloco VAL — Validação temporal e concept drift

**EN**: `("walk-forward validation" OR "time series cross-validation" OR "temporal validation" OR "concept drift" OR "data drift" OR "model degradation" OR "online learning")`

**PT**: `("validação temporal" OR "validação cruzada para séries temporais" OR "deriva de conceito" OR "degradação de modelo")`

---

## 3. Strings de busca prontas (copie e cole)

> Cada string abaixo é desenhada para uma seção específica do Capítulo 2 do TCC.
> Esperado: 30–200 resultados por string. Se vier > 500, restringir período. Se vier < 10, relaxar com OR adicional ou trocar `AND` por `OR` em um bloco menos central.

### S1 — Manutenção preditiva em mineração (domínio + manutenção)

> Cobre seção 2.1 do referencial: "Manutenção preditiva em frotas de mineração".

**Scopus/WoS (TITLE-ABS-KEY)**:

```
("predictive maintenance" OR "condition monitoring" OR "prognostics and health management" OR "early warning system*" OR "fault prediction")
AND
("haul truck*" OR "open-pit mining" OR "open pit mining" OR "mining fleet*" OR "off-road truck*" OR "mining operation*" OR "earth-moving equipment")
```

**Google Scholar** (sintaxe simplificada):

```
"predictive maintenance" OR "condition monitoring" "haul truck" OR "open pit mining"
```

**SciELO/CAPES (português)**:

```
("manutenção preditiva" OR "monitoramento de condição")
AND
("mineração" OR "frota" OR "caminhão fora de estrada" OR "haul truck")
```

### S2 — ML para predição de falha em equipamentos industriais

> Cobre seção 2.2 do referencial: "Aprendizado de máquina para predição de falhas".

```
("machine learning" OR "deep learning" OR "data-driven model*" OR XGBoost OR LightGBM OR "gradient boosting" OR LSTM)
AND
("failure prediction" OR "fault detection" OR "predictive maintenance" OR "anomaly detection" OR "early warning")
AND
(equipment OR machinery OR "industrial system*" OR vehicle* OR truck* OR "rotating machinery" OR engine*)
```

### S3 — Detecção de anomalia em telemetria/IoT industrial

> Cobre seção 2.2 (alternativa não supervisionada): "Detecção de anomalia para alarme precoce".

```
("anomaly detection" OR "outlier detection" OR "novelty detection")
AND
("isolation forest" OR autoencoder OR LSTM OR "one-class SVM" OR "deep learning")
AND
(telemetry OR "industrial IoT" OR IIoT OR "sensor data" OR "time series" OR SCADA)
```

### S4 — Análise de sobrevivência em manutenção/confiabilidade

> Cobre seção 2.3 do referencial: "Modelos de sobrevivência aplicados à confiabilidade".

```
("survival analysis" OR "Cox proportional hazards" OR "Weibull AFT" OR "time-to-event" OR "accelerated failure time")
AND
(equipment OR machinery OR maintenance OR reliability OR "remaining useful life" OR "industrial asset*")
```

### S5 — Classes desbalanceadas em problemas industriais

> Cobre seção 2.4 do referencial: "Tratamento de classes desbalanceadas em eventos raros".

```
("class imbalance" OR "imbalanced data*" OR "rare event*" OR SMOTE OR "focal loss" OR "cost-sensitive")
AND
("fault detection" OR "anomaly detection" OR "predictive maintenance" OR "machine failure" OR "equipment failure")
```

### S6 — Métricas para classificadores em desbalanceamento

> Cobre seção 2.5 do referencial: "Métricas de desempenho sob desbalanceamento extremo".
> Precisa do clássico Saito & Rehmsmeier (2015), que é referência obrigatória.

```
("AUC-PR" OR "precision-recall curve" OR "area under" )
AND
("class imbalance" OR "imbalanced" OR "rare event*" OR "skewed")
AND
(evaluation OR metric* OR comparison OR ROC)
```

Adicionar busca direta pelo paper-chave:

```
"Saito" "Rehmsmeier" "precision-recall"
```

### S7 — Calibração de probabilidades

> Cobre seção 2.5 (continuação): "Calibração de probabilidades em modelos de classificação".

```
(calibration OR "calibrated probabilit*" OR "Brier score" OR "expected calibration error" OR ECE OR "Platt scaling" OR "isotonic regression")
AND
("machine learning" OR classifier* OR "neural network*" OR "gradient boosting")
```

### S8 — SHAP e interpretabilidade

> Cobre seção 2.6 do referencial: "Interpretabilidade de modelos via SHAP".

```
(SHAP OR "Shapley value*" OR "explainable AI" OR XAI OR "interpretable machine learning")
AND
("feature importance" OR "model interpretation" OR "explanation method*" OR "tree-based" OR "ensemble model*")
```

Para o paper original obrigatório (Lundberg & Lee, NeurIPS 2017):

```
"Lundberg" "Lee" SHAP "unified approach"
```

### S9 — Validação temporal e concept drift

> Cobre seção 2.7 do referencial: "Validação temporal e robustez ao longo do tempo".

```
("walk-forward" OR "time series cross-validation" OR "temporal validation" OR "rolling window evaluation")
AND
("machine learning" OR forecasting OR "predictive model*" OR classifier*)
```

```
("concept drift" OR "data drift" OR "covariate shift" OR "distribution shift" OR "model degradation")
AND
("machine learning" OR "predictive maintenance" OR monitoring OR detection)
```

### S10 — Trabalhos relacionados (busca exaustiva — interseção exata do projeto)

> Esta é a string mais valiosa: encontra trabalhos quase idênticos ao seu, que servirão como referências centrais e base de comparação. Esperado: poucos resultados (5–30), todos altamente relevantes.

```
("predictive maintenance" OR "fault prediction" OR "failure prediction" OR "anomaly detection")
AND
("machine learning" OR "deep learning" OR "gradient boosting" OR LSTM)
AND
(mining OR "haul truck*" OR "off-road truck*" OR "heavy equipment" OR "earth-moving")
```

### S11 — Específico Brasil/Vale/UFU (referências locais)

> Para SciELO, CAPES, repositórios institucionais. Boas para argumentar relevância local.

```
("manutenção preditiva" OR "predição de falha*" OR "monitoramento de equipamento*")
AND
(mineração OR "frota de mineração" OR "minério de ferro" OR Vale OR Itabira OR Carajás)
```

### S12 — Operação de mina e gerenciamento de alarmes

> Para o disclaimer "predizer regra vs predizer risco" e fundamentação operacional.

```
("alarm management" OR "alarm flooding" OR "alarm rationalization" OR "smart alarm*" OR "operational alert*")
AND
(industrial OR mining OR equipment OR fleet)
```

---

## 4. Tabela-resumo: que string para que seção do `.tex`

| Seção do Cap. 2 (planejada) | Strings principais | Strings de apoio |
|---|---|---|
| 2.1 Operações de mineração e manutenção preditiva | S1, S11 | S12 |
| 2.2 Aprendizado de máquina para predição de falhas | S2, S10 | S3, S4 |
| 2.3 Modelos sequenciais e detecção de anomalia | S3 | S2 |
| 2.4 Análise de sobrevivência em confiabilidade | S4 | S2 |
| 2.5 Classes desbalanceadas e métricas | S5, S6, S7 | — |
| 2.6 Interpretabilidade via SHAP | S8 | — |
| 2.7 Validação temporal e drift | S9 | — |
| 2.8 Trabalhos relacionados | S10, S11 | S1 |

---

## 5. Estratégia de leitura e curadoria

Depois de rodar as strings, **não tente ler tudo**. Aplique este funil:

1. **Triagem por título** (1 segundo cada): descarta ~70%. Ficam ~30%.
2. **Triagem por abstract** (30 segundos cada): descarta ~70% restantes. Ficam ~10%.
3. **Triagem por intro + conclusão** (2 min cada): descarta mais ~50%. Ficam ~5% para leitura completa.
4. **Leitura completa** dos 5–10 mais relevantes por seção. Total alvo: **40–60 referências** no `.bib`.

### Critérios de inclusão prioritária

- ⭐ **Papers seminais** (sempre incluir, mesmo se antigos): SHAP (Lundberg & Lee 2017), AUC-PR (Saito & Rehmsmeier 2015), XGBoost (Chen & Guestrin 2016), LightGBM (Ke et al. 2017), Cox 1972, Random Forest (Breiman 2001).
- ⭐ **Reviews recentes** (≥ 2022): "machine learning for predictive maintenance: a review" — ótimo para fundamentação ampla.
- ⭐ **Trabalhos em mineração específica**: raros e valiosos para defesa.
- ⭐ **Aplicações brasileiras**: relevância local fortalece a Discussão.

### Critérios de exclusão

- Não é peer-reviewed (preprints em arXiv só se forem do método citado, ex: SHAP).
- Aplicação totalmente diferente (saúde, finanças, agro) **a menos que** seja o paper metodológico fundamental (ex: AUC-PR original é de bioinformática).
- Anteriores a 2010 e que **não** sejam seminais.

---

## 6. Workflow operacional sugerido (passo a passo)

1. **Abrir CAPES Periódicos** logado pela UFU (acesso institucional gera muitos PDFs gratuitos).
2. Rodar **S1 e S10 primeiro** — identificam o "tronco" da literatura.
3. Para cada artigo central, usar a função **"Citing this paper"** (Scopus/WoS) e **"Cited by"** para navegar para frente no tempo, e **referências do próprio artigo** para trás. Esse "snowball" é frequentemente mais produtivo que novas strings.
4. Manter um **CSV vivo** em `docs/literatura.csv` com colunas: `id_bibtex, autor, ano, título, fonte, relevância (1–5), seção_TCC, lido (S/N), notas`.
5. Conforme aceita um artigo, exportar BibTeX direto para `D:\TCC - versão final\article\bibliografia.bib`.
6. **Meta inicial**: 40 referências em 2 semanas; **meta final**: 50–80 no `.bib` ao terminar o TCC.

---

## 7. Anotações específicas para o TCC do projeto Vale

- Como o projeto adota **6 horizontes paralelos de predição** (D001) e usa o flag `Is_Dont_Go` como ground truth derivada de regras de negócio, vale buscar literatura específica sobre:
  - "**rule-based labels**" + "machine learning" — meta-tema sobre quando rótulos são derivados de regras determinísticas.
  - "**knowledge-driven**" + "data-driven" + maintenance — fusão entre regras de domínio e ML.
- Para a defesa "**predizer regra vs predizer risco**" (D010), a literatura de **alarm management** (ANSI/ISA-18.2, EEMUA 191) e **alarm flooding** é essencial — vide S12.
- Para **walk-forward + 4 folds** (D011), buscar especificamente em literatura financeira e de previsão de demanda — domínios que historicamente formalizaram o protocolo.

---

**Última atualização**: 2026-04-28 (criado durante chat de planejamento do referencial teórico).
