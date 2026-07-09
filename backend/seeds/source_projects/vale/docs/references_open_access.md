# Referências Bibliográficas Open Access — TCC Don't Go

> **Curadoria de 26 artigos open-access** para fundamentar o Capítulo 2 (Referencial Teórico)
> do TCC sobre antecipação de alertas Don't Go em frotas de mineração.
>
> Todos os artigos foram **verificados via busca web em 2026-04-28** quanto ao status open-access.
>
> **Como usar**: copie a entrada BibTeX da seção "BibTeX consolidado" no fim do documento e cole
> em `docs/article_dontgo/bibliografia.bib`. Cite no `.tex` com `\cite{chave}` ou
> `\textcite{chave}`.

## Status dos PDFs (atualizado 2026-04-29)

✅ **26 PDFs baixados localmente** em `papers/` (numerados 01–26). Os 14 primeiros foram baixados via `curl` (arXiv, NeurIPS, PLoS, Berkeley, NJU, Nature SR, Springer Open, Frontiers, PMC mirror para 3 MDPI Sensors); os 12 restantes (MDPI bloqueia curl com 403) foram baixados manualmente pelo usuário a partir das URLs abertas no navegador.

A seção "Lista de download manual" no fim deste documento é mantida apenas como **registro histórico**, com as URLs originais para conferência futura.

---

## Bloco 1 — Métodos seminais de Machine Learning (5 papers)

> Referências obrigatórias para fundamentar a escolha dos algoritmos LightGBM, XGBoost,
> CatBoost, Random Forest e Isolation Forest declarados em D004 e D015.

### [B1-01] Breiman, 2001 — Random Forests

- **Título**: Random Forests
- **Autores**: Leo Breiman
- **Ano / Venue**: 2001 / Machine Learning, vol. 45, pp. 5–32
- **DOI**: 10.1023/A:1010933404324
- **PDF (OA, manuscrito do autor)**: https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf
- **Local**: `papers/01_breiman_2001_random_forests.pdf`
- **Por que cito**: paper fundador de árvores de decisão em ensemble. Base teórica para entender bagging e gradient boosting (LightGBM/XGBoost são extensões diretas desse trabalho). Citação obrigatória em qualquer seção de modelagem com árvores.
- **Chave BibTeX**: `breiman2001randomforests`

### [B1-02] Chen & Guestrin, 2016 — XGBoost

- **Título**: XGBoost: A Scalable Tree Boosting System
- **Autores**: Tianqi Chen, Carlos Guestrin
- **Ano / Venue**: 2016 / Proceedings of the 22nd ACM SIGKDD (KDD '16)
- **DOI**: 10.1145/2939672.2939785
- **PDF (OA, arXiv)**: https://arxiv.org/pdf/1603.02754
- **Local**: `papers/02_chen_guestrin_2016_xgboost.pdf`
- **Por que cito**: justifica a escolha do XGBoost como um dos modelos avaliados. Fundamenta as inovações de boosting esparso, weighted quantile sketch e tratamento eficiente de missing values.
- **Chave BibTeX**: `chen2016xgboost`

### [B1-03] Ke et al., 2017 — LightGBM

- **Título**: LightGBM: A Highly Efficient Gradient Boosting Decision Tree
- **Autores**: Guolin Ke, Qi Meng, Thomas Finley, Taifeng Wang, Wei Chen, Weidong Ma, Qiwei Ye, Tie-Yan Liu
- **Ano / Venue**: 2017 / NeurIPS 2017
- **PDF (OA, NeurIPS proceedings)**: https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree
- **Local**: `papers/03_ke_2017_lightgbm.pdf`
- **Por que cito**: LightGBM é o modelo principal candidato para PA-1 (D004). Paper introduz GOSS e EFB, que tornam o algoritmo viável em datasets de 17M+ predições (escala do nosso problema).
- **Chave BibTeX**: `ke2017lightgbm`

### [B1-04] Prokhorenkova et al., 2018 — CatBoost

- **Título**: CatBoost: Unbiased Boosting with Categorical Features
- **Autores**: Liudmila Prokhorenkova, Gleb Gusev, Aleksandr Vorobev, Anna Veronika Dorogush, Andrey Gulin
- **Ano / Venue**: 2018 / NeurIPS 2018
- **arXiv**: 1706.09516
- **PDF (OA)**: https://arxiv.org/pdf/1706.09516
- **Local**: `papers/04_prokhorenkova_2018_catboost.pdf`
- **Por que cito**: CatBoost é alternativa para terceiro modelo de boosting, especialmente útil pelo tratamento nativo de categóricas (relevante para `Tag`, `Frota`, `Tipo`, `Operador`). Paper introduz "ordered boosting" para combater target leakage — alinhado ao princípio anti-leakage do projeto (D010).
- **Chave BibTeX**: `prokhorenkova2018catboost`

### [B1-05] Liu, Ting & Zhou, 2008 — Isolation Forest

- **Título**: Isolation Forest
- **Autores**: Fei Tony Liu, Kai Ming Ting, Zhi-Hua Zhou
- **Ano / Venue**: 2008 / IEEE ICDM 2008
- **DOI**: 10.1109/ICDM.2008.17
- **PDF (OA, cópia dos autores)**: https://www.lamda.nju.edu.cn/publication/icdm08b.pdf
- **Local**: `papers/05_liu_2008_isolation_forest.pdf`
- **Por que cito**: fundamenta PA-3 (detecção de anomalia não supervisionada). Algoritmo escolhido como linha não supervisionada para identificar modos de falha **fora** do catálogo CMA — uma das defesas do projeto.
- **Chave BibTeX**: `liu2008isolationforest`

---

## Bloco 2 — Interpretabilidade e Métricas (2 papers)

> Fundamentos para D012 (pacote de métricas) e seção SHAP do Cap. 4.

### [B2-06] Lundberg & Lee, 2017 — SHAP

- **Título**: A Unified Approach to Interpreting Model Predictions
- **Autores**: Scott M. Lundberg, Su-In Lee
- **Ano / Venue**: 2017 / NeurIPS 2017
- **arXiv**: 1705.07874
- **PDF (OA)**: https://arxiv.org/pdf/1705.07874
- **Local**: `papers/06_lundberg_lee_2017_shap.pdf`
- **Por que cito**: paper original do SHAP. Justifica o uso de Shapley values (CM 5.3 do Estudo Guiado) para validação de "sentido operacional" das features — defesa-chave contra "predizer regra vs predizer risco" (D010).
- **Chave BibTeX**: `lundberg2017shap`

### [B2-07] Saito & Rehmsmeier, 2015 — Plot Precision-Recall

- **Título**: The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets
- **Autores**: Takaya Saito, Marc Rehmsmeier
- **Ano / Venue**: 2015 / PLoS ONE 10(3): e0118432
- **DOI**: 10.1371/journal.pone.0118432
- **PDF (OA)**: https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0118432&type=printable
- **Local**: `papers/07_saito_rehmsmeier_2015_pr_plot.pdf`
- **Por que cito**: **referência absolutamente obrigatória** — fundamenta D002 (escolha de AUC-PR como métrica primária) e D012 (pacote ampliado de métricas). Mostra empiricamente por que ROC-AUC ilude em desbalanceamento extremo.
- **Chave BibTeX**: `saito2015precisionrecall`

---

## Bloco 3 — Manutenção Preditiva em Mineração (3 papers)

> Aplicações específicas ao domínio do TCC.

### [B3-08] Predictive Maintenance Underground Mining (MDPI Engineering 2025)

- **Título**: Predictive Maintenance in Underground Mining Equipment Using Artificial Intelligence
- **Venue / Ano**: MDPI Engineering / 2025
- **DOI**: 10.3390/eng6100261
- **URL**: https://www.mdpi.com/2673-4117/6/10/261
- **Local**: `papers/08_mdpi_2025_pdm_underground_mining.pdf`
- **Por que cito**: caso de uso direto de manutenção preditiva em equipamentos de mineração com IoT + ML. Reporta redução de 8% em custo de manutenção e +10% em disponibilidade — métricas comparáveis ao impacto previsto pelo nosso modelo. Referência primária para Cap. 2 §1 e Cap. 5 (Discussão).
- **Chave BibTeX**: `mdpi2025undergroundmining`

### [B3-09] AI-Driven PdM in Mining: Systematic Review (MDPI Applied Sciences 2025)

- **Título**: AI-Driven Predictive Maintenance in Mining: A Systematic Literature Review on Fault Detection, Digital Twins, and Intelligent Asset Management
- **Venue / Ano**: MDPI Applied Sciences / 2025
- **DOI**: 10.3390/app15063337
- **URL**: https://www.mdpi.com/2076-3417/15/6/3337
- **Local**: `papers/09_mdpi_2025_ai_pdm_mining_review.pdf`
- **Por que cito**: revisão sistemática de 166 estudos em mineração — fonte ideal para a seção "Trabalhos Relacionados" do Cap. 2. Identifica tendências em fault detection, hybrid AI e digital twins.
- **Chave BibTeX**: `mdpi2025aiminingreview`

### [B3-10] TinyML Hierarchical Inference for Mining Mobile Machinery (arXiv 2024)

- **Título**: Enhancing Predictive Maintenance in Mining Mobile Machinery through a TinyML-enabled Hierarchical Inference Network
- **Ano / Venue**: 2024 / arXiv preprint
- **arXiv**: 2411.07168
- **URL**: https://arxiv.org/abs/2411.07168
- **Local**: `papers/10_arxiv_2024_tinyml_mining.pdf`
- **Por que cito**: aborda haul trucks, front-loaders e equipamentos auxiliares — exatamente o nosso escopo (Caminhão, Carregadeira, Escavadeira). Discute reinforcement learning para gestão de paradas. Referência para Cap. 2 §3 e Cap. 6 (Trabalhos Futuros).
- **Chave BibTeX**: `tinyml2024mining`

---

## Bloco 4 — Surveys de Manutenção Preditiva (3 papers)

> Fundamentação ampla para a seção de manutenção preditiva no Cap. 2.

### [B3-11] Deep Learning Fault Diagnosis Industrial Systems Review (MDPI Sensors 2023)

- **Título**: Deep Learning Techniques in Intelligent Fault Diagnosis and Prognosis for Industrial Systems: A Review
- **Venue / Ano**: MDPI Sensors / 2023
- **DOI**: 10.3390/s23031305
- **URL**: https://www.mdpi.com/1424-8220/23/3/1305
- **Local**: `papers/11_mdpi_2023_dl_fault_diagnosis_review.pdf`
- **Por que cito**: revisão recente sobre DL aplicado a diagnóstico de falhas industriais. Cobre LSTM, CNN, autoencoders — três arquiteturas relevantes ao nosso PA-3.
- **Chave BibTeX**: `mdpi2023dlfaultdiagnosis`

### [B3-12] Application-Wise ML Predictive Maintenance Review (MDPI Applied Sciences 2025)

- **Título**: Application-Wise Review of Machine Learning-Based Predictive Maintenance: Trends, Challenges, and Future Directions
- **Venue / Ano**: MDPI Applied Sciences / 2025
- **DOI**: 10.3390/app15094898
- **URL**: https://www.mdpi.com/2076-3417/15/9/4898
- **Local**: `papers/12_mdpi_2025_app_wise_ml_pdm_review.pdf`
- **Por que cito**: organiza a literatura de PdM por **aplicação** — ideal para posicionar o nosso problema (mineração de carga pesada) no panorama mais amplo (manufatura, energia, transporte, aviação).
- **Chave BibTeX**: `mdpi2025appwisepdm`

### [B3-13] Predictive Maintenance in Industry 4.0 — Overview, Models, Challenges (MDPI Applied Sciences 2022)

- **Título**: On Predictive Maintenance in Industry 4.0: Overview, Models, and Challenges
- **Venue / Ano**: MDPI Applied Sciences / 2022
- **DOI**: 10.3390/app12168081
- **URL**: https://www.mdpi.com/2076-3417/12/16/8081
- **Local**: `papers/13_mdpi_2022_pdm_industry40_overview.pdf`
- **Por que cito**: framework conceitual de PdM em Indústria 4.0. Distingue corrective/preventive/predictive — necessário para enquadrar o trabalho na taxonomia clássica de manutenção.
- **Chave BibTeX**: `mdpi2022pdmindustry40`

---

## Bloco 5 — Modelos Sequenciais (LSTM, Autoencoders) (4 papers)

> Fundamentação para PA-3 (anomalia via Autoencoder LSTM) e features sequenciais.

### [B5-14] LSTM Autoencoders Cyber-Physical (MDPI Sensors 2021)

- **Título**: A Deep Learning Model for Predictive Maintenance in Cyber-Physical Production Systems Using LSTM Autoencoders
- **Venue / Ano**: MDPI Sensors / 2021
- **DOI**: 10.3390/s21030972
- **URL**: https://www.mdpi.com/1424-8220/21/3/972
- **Local**: `papers/14_mdpi_2021_lstm_autoencoder_cps.pdf`
- **Por que cito**: caso de uso de LSTM-autoencoder para RUL em sistemas ciber-físicos. Padrão arquitetural quase idêntico ao que propomos como abordagem PA-3 (anomalia em sequência de telemetria).
- **Chave BibTeX**: `mdpi2021lstmautoencoder`

### [B5-15] Hybrid DL Transformer Failure (MDPI Energies 2025)

- **Título**: Hybrid Deep Learning for Predictive Maintenance: LSTM, GRU, CNN, and Dense Models Applied to Transformer Failure Forecasting
- **Venue / Ano**: MDPI Energies / 2025
- **DOI**: 10.3390/en18215634
- **URL**: https://www.mdpi.com/1996-1073/18/21/5634
- **Local**: `papers/15_mdpi_2025_hybrid_dl_transformer_failure.pdf`
- **Por que cito**: comparação cabeça-a-cabeça de LSTM vs GRU vs CNN vs MLP para previsão de falha — exemplo bem documentado de protocolo experimental que podemos espelhar.
- **Chave BibTeX**: `mdpi2025hybriddl`

### [B5-16] CNN-LSTM para Predição de Falha em Indústria 4.0 (Wahid, Breslin & Intizar 2022)

- **Título**: Prediction of Machine Failure in Industry 4.0: A Hybrid CNN-LSTM Framework
- **Autores**: Abdul Wahid, John G. Breslin, Muhammad Ali Intizar
- **Venue / Ano**: MDPI Applied Sciences, vol. 12, n. 9, art. 4221 / 2022
- **DOI**: 10.3390/app12094221
- **URL**: https://www.mdpi.com/2076-3417/12/9/4221
- **Local**: `papers/16_mdpi_2022_cnn_lstm_industry40.pdf`
- **Por que cito**: arquitetura híbrida CNN-LSTM (com skip connection) para previsão multivariada de séries temporais aplicada a predictive maintenance, usando o dataset público da Microsoft Azure ML. **Trata-se de regressão (forecasting de degradação), não classificação** — métricas reportadas: **MAE = 30,125; RMSE ≈ 35; R² ≈ 1**. Útil como referência de protocolo experimental para comparação CNN vs LSTM vs CNN-LSTM, e como ponte entre nossa PA-1 (binária) e PA-2 (regressão de RUL).
- **Chave BibTeX**: `wahid2022cnnlstm`

### [B5-17] LSTM-AE + Transformer Encoders Manufacturing (MDPI Sensors 2024)

- **Título**: Condition Monitoring and Predictive Maintenance of Assets in Manufacturing Using LSTM-Autoencoders and Transformer Encoders
- **Venue / Ano**: MDPI Sensors / 2024
- **DOI**: 10.3390/s24103215
- **URL**: https://www.mdpi.com/1424-8220/24/10/3215
- **Local**: `papers/17_mdpi_2024_lstm_ae_transformer_manuf.pdf`
- **Por que cito**: combinação LSTM-AE + Transformer encoder — referência atual (2024) que justifica a opção por arquiteturas sequenciais profundas. Discute imputation com LSTM em dados multivariados de 5 anos.
- **Chave BibTeX**: `mdpi2024lstmaetransformer`

---

## Bloco 6 — Sobrevivência e RUL (4 papers)

> Fundamentação para PA-2 (sobrevivência), D017.

### [B6-18] Survival Analysis Mobile Equipment (Nature SR 2022)

- **Título**: Prognostic modeling of predictive maintenance with survival analysis for mobile work equipment
- **Venue / Ano**: Scientific Reports (Nature) / 2022
- **DOI**: 10.1038/s41598-022-12572-z
- **URL**: https://www.nature.com/articles/s41598-022-12572-z
- **Local**: `papers/18_nature_sr_2022_survival_mobile_eq.pdf`
- **Por que cito**: aplicação direta de análise de sobrevivência em **equipamentos móveis de trabalho** — domínio quase idêntico ao nosso (caminhões fora-de-estrada). Referência primária para PA-2.
- **Chave BibTeX**: `naturesurvivalmobile2022`

### [B6-19] Machine Failure Prediction Using Survival Analysis (MDPI Future Internet 2023)

- **Título**: Machine Failure Prediction Using Survival Analysis
- **Venue / Ano**: MDPI Future Internet / 2023
- **DOI**: 10.3390/fi15050153
- **URL**: https://www.mdpi.com/1999-5903/15/5/153
- **Local**: `papers/19_mdpi_2023_machine_failure_survival.pdf`
- **Por que cito**: compara Cox PH, Random Survival Forests, Gradient Boosting Survival e Survival SVM. Resposta direta à decisão D017 (Cox + Schoenfeld + Weibull AFT como fallback).
- **Chave BibTeX**: `mdpi2023machinefailuresurvival`

### [B6-20] RUL Deep Learning Survey (MDPI Sensors 2024)

- **Título**: Remaining Useful Life Prediction Based on Deep Learning: A Survey
- **Venue / Ano**: MDPI Sensors / 2024
- **DOI**: 10.3390/s24113454
- **URL**: https://www.mdpi.com/1424-8220/24/11/3454
- **Local**: `papers/20_mdpi_2024_rul_dl_survey.pdf`
- **Por que cito**: survey recente de DL para RUL — fornece taxonomia que conecta PA-1 (classificação binária) e PA-2 (regressão / sobrevivência) num mesmo framework conceitual.
- **Chave BibTeX**: `mdpi2024rulsurvey`

### [B6-21] Cox PH for Cutting Tool Lifespan (MDPI JMMP 2020)

- **Título**: An Analytic Approach to the Cox Proportional Hazards Model for Estimating the Lifespan of Cutting Tools
- **Venue / Ano**: MDPI Journal of Manufacturing and Materials Processing / 2020
- **DOI**: 10.3390/jmmp4010027
- **URL**: https://www.mdpi.com/2504-4494/4/1/27
- **Local**: `papers/21_mdpi_2020_cox_ph_cutting_tools.pdf`
- **Por que cito**: aplicação concreta de Cox PH em equipamento industrial. Discute teste de Schoenfeld e violações de PH — operacionaliza exatamente o que D017 prescreve.
- **Chave BibTeX**: `mdpi2020coxph`

---

## Bloco 7 — Classes Desbalanceadas (2 papers)

> Fundamentação para D015.

### [B7-22] Survey Deep Learning Class Imbalance (Springer Big Data 2019)

- **Título**: Survey on Deep Learning with Class Imbalance
- **Autores**: Justin Johnson, Taghi Khoshgoftaar
- **Venue / Ano**: Journal of Big Data (Springer Open) / 2019
- **DOI**: 10.1186/s40537-019-0192-5
- **URL**: https://link.springer.com/article/10.1186/s40537-019-0192-5
- **Local**: `papers/22_springer_2019_dl_class_imbalance.pdf`
- **Por que cito**: review obrigatório sobre classes desbalanceadas em DL. Cobre cost-sensitive learning, resampling, ensemble — discussão direta para D015 (proibição de SMOTE em séries temporais).
- **Chave BibTeX**: `johnson2019dlimbalance`

### [B7-23] Tomek Link + SMOTE Machine Fault (MDPI Sensors 2022)

- **Título**: Tomek Link and SMOTE Approaches for Machine Fault Classification with an Imbalanced Dataset
- **Venue / Ano**: MDPI Sensors / 2022
- **DOI**: 10.3390/s22093246
- **URL**: https://www.mdpi.com/1424-8220/22/9/3246
- **Local**: `papers/23_mdpi_2022_tomek_smote_machine_fault.pdf`
- **Por que cito**: compara variantes de SMOTE em diagnóstico de falha de máquina. Referência para a discussão sobre por que SMOTE puro não é adequado em telemetria sequencial (D015).
- **Chave BibTeX**: `mdpi2022tomeksmote`

---

## Bloco 8 — Concept Drift e Validação Temporal (2 papers)

> Fundamentação para D011 (walk-forward) e seção de drift do Cap. 4.

### [B8-24] Concept Drift Survey Part A (Hinder, Vaquet & Hammer 2024)

- **Título**: One or two things we know about concept drift — a survey on monitoring in evolving environments. Part A: detecting concept drift
- **Autores**: Fabian Hinder, Valerie Vaquet, Barbara Hammer (Bielefeld University)
- **Venue / Ano**: Frontiers in Artificial Intelligence / 2024
- **DOI**: 10.3389/frai.2024.1330257
- **URL**: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1330257/full
- **Local**: `papers/24_frontiers_2024_concept_drift_partA.pdf`
- **Por que cito**: survey moderno (2024) de detecção de concept drift, com foco em data streams **não supervisionados** — alinhado ao nosso cenário de monitoramento contínuo de telemetria. Fundamenta a análise de drift temporal entre folds do walk-forward (D011) e oferece definições matemáticas precisas de drift virtual, real e covariate shift.
- **Chave BibTeX**: `hinder2024conceptdriftA`

### [B8-25] Systematic Review Concept Drift Detection (MDPI Information 2024)

- **Título**: Evolving Strategies in Machine Learning: A Systematic Review of Concept Drift Detection
- **Venue / Ano**: MDPI Information / 2024
- **DOI**: 10.3390/info15120786
- **URL**: https://www.mdpi.com/2078-2489/15/12/786
- **Local**: `papers/25_mdpi_2024_concept_drift_systematic.pdf`
- **Por que cito**: complemento metodológico ao Frontiers — categoriza métodos de detecção de drift (DDM, ADWIN, PSI). Referência para a análise de drift entre folds.
- **Chave BibTeX**: `mdpi2024driftsystematic`

---

## Bloco 9 — Aplicação adicional (1 paper)

### [B9-26] Data-Driven Predictive Maintenance for Railway (MDPI Sensors 2021)

- **Título**: A Survey on Data-Driven Predictive Maintenance for the Railway Industry
- **Venue / Ano**: MDPI Sensors / 2021
- **DOI**: 10.3390/s21175739
- **URL**: https://www.mdpi.com/1424-8220/21/17/5739
- **Local**: `papers/26_mdpi_2021_data_driven_pdm_railway.pdf`
- **Por que cito**: domínio análogo (transporte pesado, rotas fixas, telemetria abundante). Útil para argumentar transferência de aprendizados para o domínio de mineração na seção "Trabalhos Relacionados".
- **Chave BibTeX**: `mdpi2021railwaypdm`

---

## Mapa de uso por seção do `.tex`

| Seção do Cap. 2 / 4 | Referências sugeridas |
|---|---|
| 2.1 Operação de mina e PdM (introdução) | B3-08, B3-09, B3-13 |
| 2.2 Aprendizado de máquina supervisionado | B1-01, B1-02, B1-03, B1-04 |
| 2.3 Detecção de anomalia não supervisionada | B1-05, B5-14, B5-17 |
| 2.4 Sobrevivência e RUL | B6-18, B6-19, B6-20, B6-21 |
| 2.5 Métricas e calibração | B2-07, B7-22 |
| 2.6 Interpretabilidade SHAP | B2-06 |
| 2.7 Validação temporal e drift | B8-24, B8-25 |
| 2.8 Trabalhos relacionados | B3-09, B3-10, B5-15, B5-16, B6-18, B9-26 |
| 5 Discussão (impacto operacional) | B3-08, B3-12 |

---

## BibTeX consolidado (copiar e colar em `bibliografia.bib`)

```bibtex
@article{breiman2001randomforests,
  author  = {Breiman, Leo},
  title   = {Random Forests},
  journal = {Machine Learning},
  volume  = {45},
  number  = {1},
  pages   = {5--32},
  year    = {2001},
  doi     = {10.1023/A:1010933404324}
}

@inproceedings{chen2016xgboost,
  author    = {Chen, Tianqi and Guestrin, Carlos},
  title     = {{XGBoost}: A Scalable Tree Boosting System},
  booktitle = {Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining},
  series    = {KDD '16},
  pages     = {785--794},
  year      = {2016},
  publisher = {ACM},
  doi       = {10.1145/2939672.2939785}
}

@inproceedings{ke2017lightgbm,
  author    = {Ke, Guolin and Meng, Qi and Finley, Thomas and Wang, Taifeng and Chen, Wei and Ma, Weidong and Ye, Qiwei and Liu, Tie-Yan},
  title     = {{LightGBM}: A Highly Efficient Gradient Boosting Decision Tree},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {30},
  pages     = {3146--3154},
  year      = {2017}
}

@inproceedings{prokhorenkova2018catboost,
  author    = {Prokhorenkova, Liudmila and Gusev, Gleb and Vorobev, Aleksandr and Dorogush, Anna Veronika and Gulin, Andrey},
  title     = {{CatBoost}: Unbiased Boosting with Categorical Features},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {31},
  pages     = {6638--6648},
  year      = {2018},
  eprint    = {1706.09516},
  archivePrefix = {arXiv}
}

@inproceedings{liu2008isolationforest,
  author    = {Liu, Fei Tony and Ting, Kai Ming and Zhou, Zhi-Hua},
  title     = {Isolation Forest},
  booktitle = {2008 Eighth IEEE International Conference on Data Mining},
  pages     = {413--422},
  year      = {2008},
  publisher = {IEEE},
  doi       = {10.1109/ICDM.2008.17}
}

@inproceedings{lundberg2017shap,
  author    = {Lundberg, Scott M. and Lee, Su-In},
  title     = {A Unified Approach to Interpreting Model Predictions},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {30},
  pages     = {4765--4774},
  year      = {2017},
  eprint    = {1705.07874},
  archivePrefix = {arXiv}
}

@article{saito2015precisionrecall,
  author  = {Saito, Takaya and Rehmsmeier, Marc},
  title   = {The Precision-Recall Plot Is More Informative than the {ROC} Plot When Evaluating Binary Classifiers on Imbalanced Datasets},
  journal = {PLoS ONE},
  volume  = {10},
  number  = {3},
  pages   = {e0118432},
  year    = {2015},
  doi     = {10.1371/journal.pone.0118432}
}

@article{mdpi2025undergroundmining,
  title   = {Predictive Maintenance in Underground Mining Equipment Using Artificial Intelligence},
  journal = {Eng (MDPI)},
  volume  = {6},
  number  = {10},
  pages   = {261},
  year    = {2025},
  doi     = {10.3390/eng6100261},
  url     = {https://www.mdpi.com/2673-4117/6/10/261}
}

@article{mdpi2025aiminingreview,
  title   = {{AI}-Driven Predictive Maintenance in Mining: A Systematic Literature Review on Fault Detection, Digital Twins, and Intelligent Asset Management},
  journal = {Applied Sciences},
  volume  = {15},
  number  = {6},
  pages   = {3337},
  year    = {2025},
  doi     = {10.3390/app15063337},
  url     = {https://www.mdpi.com/2076-3417/15/6/3337}
}

@misc{tinyml2024mining,
  title         = {Enhancing Predictive Maintenance in Mining Mobile Machinery through a {TinyML}-enabled Hierarchical Inference Network},
  year          = {2024},
  eprint        = {2411.07168},
  archivePrefix = {arXiv},
  url           = {https://arxiv.org/abs/2411.07168}
}

@article{mdpi2023dlfaultdiagnosis,
  title   = {Deep Learning Techniques in Intelligent Fault Diagnosis and Prognosis for Industrial Systems: A Review},
  journal = {Sensors},
  volume  = {23},
  number  = {3},
  pages   = {1305},
  year    = {2023},
  doi     = {10.3390/s23031305},
  url     = {https://www.mdpi.com/1424-8220/23/3/1305}
}

@article{mdpi2025appwisepdm,
  title   = {Application-Wise Review of Machine Learning-Based Predictive Maintenance: Trends, Challenges, and Future Directions},
  journal = {Applied Sciences},
  volume  = {15},
  number  = {9},
  pages   = {4898},
  year    = {2025},
  doi     = {10.3390/app15094898},
  url     = {https://www.mdpi.com/2076-3417/15/9/4898}
}

@article{mdpi2022pdmindustry40,
  title   = {On Predictive Maintenance in Industry 4.0: Overview, Models, and Challenges},
  journal = {Applied Sciences},
  volume  = {12},
  number  = {16},
  pages   = {8081},
  year    = {2022},
  doi     = {10.3390/app12168081},
  url     = {https://www.mdpi.com/2076-3417/12/16/8081}
}

@article{mdpi2021lstmautoencoder,
  title   = {A Deep Learning Model for Predictive Maintenance in Cyber-Physical Production Systems Using {LSTM} Autoencoders},
  journal = {Sensors},
  volume  = {21},
  number  = {3},
  pages   = {972},
  year    = {2021},
  doi     = {10.3390/s21030972},
  url     = {https://www.mdpi.com/1424-8220/21/3/972}
}

@article{mdpi2025hybriddl,
  title   = {Hybrid Deep Learning for Predictive Maintenance: {LSTM}, {GRU}, {CNN}, and Dense Models Applied to Transformer Failure Forecasting},
  journal = {Energies},
  volume  = {18},
  number  = {21},
  pages   = {5634},
  year    = {2025},
  doi     = {10.3390/en18215634},
  url     = {https://www.mdpi.com/1996-1073/18/21/5634}
}

@article{wahid2022cnnlstm,
  author  = {Wahid, Abdul and Breslin, John G. and Intizar, Muhammad Ali},
  title   = {Prediction of Machine Failure in Industry 4.0: A Hybrid {CNN}-{LSTM} Framework},
  journal = {Applied Sciences},
  volume  = {12},
  number  = {9},
  pages   = {4221},
  year    = {2022},
  doi     = {10.3390/app12094221},
  url     = {https://www.mdpi.com/2076-3417/12/9/4221}
}

@article{mdpi2024lstmaetransformer,
  title   = {Condition Monitoring and Predictive Maintenance of Assets in Manufacturing Using {LSTM}-Autoencoders and Transformer Encoders},
  journal = {Sensors},
  volume  = {24},
  number  = {10},
  pages   = {3215},
  year    = {2024},
  doi     = {10.3390/s24103215},
  url     = {https://www.mdpi.com/1424-8220/24/10/3215}
}

@article{naturesurvivalmobile2022,
  title   = {Prognostic modeling of predictive maintenance with survival analysis for mobile work equipment},
  journal = {Scientific Reports},
  volume  = {12},
  pages   = {8529},
  year    = {2022},
  doi     = {10.1038/s41598-022-12572-z},
  url     = {https://www.nature.com/articles/s41598-022-12572-z}
}

@article{mdpi2023machinefailuresurvival,
  title   = {Machine Failure Prediction Using Survival Analysis},
  journal = {Future Internet},
  volume  = {15},
  number  = {5},
  pages   = {153},
  year    = {2023},
  doi     = {10.3390/fi15050153},
  url     = {https://www.mdpi.com/1999-5903/15/5/153}
}

@article{mdpi2024rulsurvey,
  title   = {Remaining Useful Life Prediction Based on Deep Learning: A Survey},
  journal = {Sensors},
  volume  = {24},
  number  = {11},
  pages   = {3454},
  year    = {2024},
  doi     = {10.3390/s24113454},
  url     = {https://www.mdpi.com/1424-8220/24/11/3454}
}

@article{mdpi2020coxph,
  title   = {An Analytic Approach to the {Cox} Proportional Hazards Model for Estimating the Lifespan of Cutting Tools},
  journal = {Journal of Manufacturing and Materials Processing},
  volume  = {4},
  number  = {1},
  pages   = {27},
  year    = {2020},
  doi     = {10.3390/jmmp4010027},
  url     = {https://www.mdpi.com/2504-4494/4/1/27}
}

@article{johnson2019dlimbalance,
  author  = {Johnson, Justin M. and Khoshgoftaar, Taghi M.},
  title   = {Survey on deep learning with class imbalance},
  journal = {Journal of Big Data},
  volume  = {6},
  number  = {1},
  pages   = {27},
  year    = {2019},
  doi     = {10.1186/s40537-019-0192-5},
  url     = {https://link.springer.com/article/10.1186/s40537-019-0192-5}
}

@article{mdpi2022tomeksmote,
  title   = {{Tomek} Link and {SMOTE} Approaches for Machine Fault Classification with an Imbalanced Dataset},
  journal = {Sensors},
  volume  = {22},
  number  = {9},
  pages   = {3246},
  year    = {2022},
  doi     = {10.3390/s22093246},
  url     = {https://www.mdpi.com/1424-8220/22/9/3246}
}

@article{hinder2024conceptdriftA,
  author  = {Hinder, Fabian and Vaquet, Valerie and Hammer, Barbara},
  title   = {One or two things we know about concept drift -- a survey on monitoring in evolving environments. {Part A}: detecting concept drift},
  journal = {Frontiers in Artificial Intelligence},
  volume  = {7},
  pages   = {1330257},
  year    = {2024},
  doi     = {10.3389/frai.2024.1330257},
  url     = {https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1330257/full}
}

@article{mdpi2024driftsystematic,
  title   = {Evolving Strategies in Machine Learning: A Systematic Review of Concept Drift Detection},
  journal = {Information},
  volume  = {15},
  number  = {12},
  pages   = {786},
  year    = {2024},
  doi     = {10.3390/info15120786},
  url     = {https://www.mdpi.com/2078-2489/15/12/786}
}

@article{mdpi2021railwaypdm,
  title   = {A Survey on Data-Driven Predictive Maintenance for the Railway Industry},
  journal = {Sensors},
  volume  = {21},
  number  = {17},
  pages   = {5739},
  year    = {2021},
  doi     = {10.3390/s21175739},
  url     = {https://www.mdpi.com/1424-8220/21/17/5739}
}
```

---

## Lista de download manual (12 referências MDPI)

> Abra cada URL no navegador e clique em **"Download PDF"** no canto superior direito da página.
> Salve com o nome sugerido (mesma convenção dos PDFs já baixados em `papers/`).

| # | Salvar como | URL HTML |
|---|---|---|
| B3-08 | `papers/08_mdpi_2025_pdm_underground_mining.pdf` | <https://www.mdpi.com/2673-4117/6/10/261> |
| B3-09 | `papers/09_mdpi_2025_ai_pdm_mining_review.pdf` | <https://www.mdpi.com/2076-3417/15/6/3337> |
| B3-11 | `papers/11_mdpi_2023_dl_fault_diagnosis_review.pdf` | <https://www.mdpi.com/1424-8220/23/3/1305> |
| B3-12 | `papers/12_mdpi_2025_app_wise_ml_pdm_review.pdf` | <https://www.mdpi.com/2076-3417/15/9/4898> |
| B3-13 | `papers/13_mdpi_2022_pdm_industry40_overview.pdf` | <https://www.mdpi.com/2076-3417/12/16/8081> |
| B5-15 | `papers/15_mdpi_2025_hybrid_dl_transformer_failure.pdf` | <https://www.mdpi.com/1996-1073/18/21/5634> |
| B5-16 | `papers/16_mdpi_2022_cnn_lstm_industry40.pdf` | <https://www.mdpi.com/2076-3417/12/9/4221> |
| B6-19 | `papers/19_mdpi_2023_machine_failure_survival.pdf` | <https://www.mdpi.com/1999-5903/15/5/153> |
| B6-21 | `papers/21_mdpi_2020_cox_ph_cutting_tools.pdf` | <https://www.mdpi.com/2504-4494/4/1/27> |
| B7-23 | `papers/23_mdpi_2022_tomek_smote_machine_fault.pdf` | <https://www.mdpi.com/1424-8220/22/9/3246> |
| B8-25 | `papers/25_mdpi_2024_concept_drift_systematic.pdf` | <https://www.mdpi.com/2078-2489/15/12/786> |
| B9-26 | `papers/26_mdpi_2021_data_driven_pdm_railway.pdf` | <https://www.mdpi.com/1424-8220/21/17/5739> |

**Tempo estimado**: ~5 min para baixar os 12 manualmente. Todos são CC-BY 4.0 (uso livre com atribuição).

---

## Notas

- **Verificação de licença**: todos os papers MDPI são CC-BY 4.0 (livre uso com atribuição). PLoS ONE é CC-BY. Frontiers é CC-BY. Springer Open Big Data é CC-BY. arXiv é OA mas com licença variável (geralmente uso permitido para pesquisa). Berkeley/lamda.nju.edu.cn são cópias dos autores (Bronze OA — uso pessoal/acadêmico).
- **MDPI bloqueio anti-bot**: a editora retorna HTTP 403 para `curl/wget` mesmo com User-Agent de browser. Os PDFs são totalmente OA, mas devem ser baixados via clique no navegador. PMC/PubMed serve mirror para alguns Sensors (3 conseguidos via PMC).
- **Volume final no `.bib`**: 26 entradas. Adicionar +14–24 referências durante a redação para chegar ao alvo de 40–50 que é típico para um TCC ABNT desta extensão.
- **Versão / atualização**: 2026-04-29 (v2, **26 PDFs locais** em `papers/`; download manual dos 12 MDPI restantes concluído; histórico das URLs preservado para auditoria).
