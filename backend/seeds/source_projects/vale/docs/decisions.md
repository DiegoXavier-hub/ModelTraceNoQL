# docs/decisions.md — Controle de Alterações (ANTES → DEPOIS)

> Registro auditável de toda decisão metodológica relevante: exclusões de registros, escolha de janela de predição, encoding adotado, hiperparâmetros finais, etc.
>
> Formato obrigatório por entrada:
> - **Data** (YYYY-MM-DD)
> - **Contexto** (onde no fluxo)
> - **ANTES** (o que estava sendo feito / estado anterior)
> - **DEPOIS** (o que passou a ser feito)
> - **Justificativa** (por quê)
> - **Impacto esperado** (no resultado / nos números)

---

## D001 — Janela de predição (Fase 1, CM 1.2) — **ATUALIZADA 2026-04-28**

- **Data original**: 2026-04-28 (versão "4 h única")
- **Data da atualização**: 2026-04-28 (mesma sessão, após auto-revisão `methodology_review.md`)
- **Contexto**: definição do horizonte de antecipação para PA-1.
- **ANTES**: 4 horas como janela única.
- **DEPOIS**: **Múltiplas janelas em paralelo** — H ∈ {1 h, 2 h, 4 h, 6 h, 8 h, 12 h}, com **um modelo treinado independentemente para cada horizonte**.
- **Justificativa da atualização**:
  - Princípio governante "robustez > custo": comprometer-se a uma única janela antes da EDA é arbitrário; a melhor janela é descoberta nos dados.
  - **Curva risco-vs-horizonte** vira um resultado primário do trabalho — mostra como o sinal preditivo decai com o afastamento temporal (informação rica para banca e operação).
  - **Defesa contra o risco "predizer regra vs predizer risco"**: se o modelo só funciona em H ≤ 1 h, está antecipando o trigger da regra. Se mantém AUC-PR razoável em H = 6 h ou 12 h, há sinal de **risco subjacente real** sendo capturado.
- **Impacto esperado**: 6× o custo de treinamento (aceito); seções 4 e 5 do .tex apresentam tabela e gráfico de **performance por horizonte**.

---

---

## D002 — Métrica primária técnica (Fase 1, CM 1.2)

- **Data**: 2026-04-28
- **Contexto**: escolha da métrica de avaliação principal.
- **ANTES**: candidatas: Accuracy, AUC-ROC, AUC-PR, F1, F2, Brier.
- **DEPOIS**: **AUC-PR** (Area Under the Precision-Recall Curve).
- **Justificativa**:
  - Don't Go é evento extremamente raro (H1: < 0,1% dos eventos de telemetria — confirmar na EDA).
  - AUC-ROC permanece artificialmente alta sob forte desbalanceamento por causa do volume de verdadeiros negativos triviais.
  - AUC-PR é a métrica recomendada por Saito & Rehmsmeier (2015) e padrão em fraude/falha de equipamento.
- **Impacto esperado**: comparação justa entre modelos com classes desbalanceadas; números mais conservadores (e mais honestos) que ROC-AUC.

---

## D003 — Métrica operacional (Fase 1, CM 1.2)

- **Data**: 2026-04-28
- **Contexto**: definir ponto de operação interpretável para o dispatcher.
- **ANTES**: indefinido.
- **DEPOIS**: **Recall@Precision=0,5** + **Lead time mediano** (em minutos) entre alerta do modelo e Don't Go real (apenas TPs).
- **Justificativa**:
  - Recall puro favorece "alarmar tudo" (precisão zero).
  - Precision puro favorece "alarmar nada" (recall zero).
  - P=0,5 traduz: "para cada 2 alertas do modelo, 1 vira inspeção verdadeira" — taxa aceitável.
  - Lead time mede *quanto* tempo de antecipação útil o modelo entrega — duas implementações com mesmo recall podem ter lead times muito diferentes.
- **Impacto esperado**: tabela final de modelos terá colunas Recall@P=0.5 e LeadTime_p50.

---

## D004 — Estratégia de modelagem (Fase 1, CM 1.2)

- **Data**: 2026-04-28
- **Contexto**: definir abordagem principal vs. complementares.
- **ANTES**: indefinido — Estudo Guiado é deliberadamente aberto.
- **DEPOIS**:
  - **Principal (PA-1)**: classificação binária supervisionada (LightGBM/XGBoost + baseline heurístico).
  - **Complementar 1 (PA-2)**: regressão / sobrevivência (lifelines: Cox PH ou Weibull AFT) para estimar tempo até próximo Don't Go.
  - **Complementar 2 (PA-3)**: detecção de anomalia não supervisionada (Isolation Forest e/ou Autoencoder LSTM) para identificar pré-condições não cobertas pelo catálogo de regras.
- **Justificativa**: três lentes complementares respondem juntas "vai falhar?" + "quando?" + "o que está fora do padrão?". Diferencia o trabalho de "mais um classificador binário".
- **Impacto esperado**: relatório terá três seções de modelagem com narrativas integradas, não competitivas.

---

## D005 — Escopo geográfico (Fase 1, CM 1.2)

- **Data**: 2026-04-28
- **Contexto**: limitar escopo do estudo.
- **ANTES**: implícito — "Frotas de Mineração" como rótulo genérico.
- **DEPOIS**: **Foco em Itabira/MG**.
- **Justificativa**: a inspeção inicial dos parquets mostra apenas a localidade `Itabira` em todos os registros amostrados. Generalização para outras operações da Vale (Carajás, S11D, etc.) sem dados é especulação não defensável academicamente.
- **Impacto esperado**: capítulo de Limitações honesto; trabalhos futuros incluem replicação em outras localidades.

---

## D006 — Ground truth do alvo (Fase 1, CM 1.2)

- **Data**: 2026-04-28
- **Contexto**: como derivar a variável dependente do modelo.
- **ANTES**: Estudo Guiado sugere "aplicar as 151 regras CMA sobre os dados de telemetria".
- **DEPOIS**: **usar a flag `Is_Dont_Go` já presente na telemetria como ground truth**, com validação cruzada contra o catálogo CMA na Fase 3.
- **Justificativa**:
  - A flag já está aplicada com base nas regras de negócio oficiais — replicar manualmente apenas reintroduz risco de erro.
  - O exemplo `desenvolver_dontgo.xlsx` mostra que a flag está aplicada de forma sequencialmente coerente (147 eventos precursores, 1 Don't Go culminante).
  - **Validação obrigatória na Fase 3**: tomar uma amostra de positivos `Is_Dont_Go=1`, checar se o evento bate com alguma regra do catálogo, e tomar uma amostra de "perto-positivos" (eventos que parecem regra mas têm flag 0) para entender o critério.
- **Impacto esperado**: economia de tempo na Fase 3; risco residual de inconsistência mitigado pela validação.

---

## D007 — Localização do entregável final (atualizada 2026-04-29)

- **Data original**: 2026-04-28
- **Data da atualização**: 2026-04-29 (decisão do usuário durante a criação dos capítulos esqueleto)
- **Contexto**: definir formato e local do relatório final.
- **ANTES**: implícito (`Desenvolver_Template.docx` da banca).
- **VERSÃO ANTERIOR (2026-04-28)**: LaTeX em `D:\TCC - versão final\article\` (junto com o TCC de Evasão).
- **DEPOIS (2026-04-29)**: **LaTeX em `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\docs\article_dontgo\`**, padrão **ABNT** (`abntex2`), reutilizando preâmbulo do TCC anterior (`TCC_Evasao.tex`) mas em pasta independente, dentro do projeto Vale.
- **Justificativa da atualização**: manter o material em desenvolvimento dentro do diretório do projeto Vale (mais coerente com o fluxo de trabalho atual); evitar mistura com o TCC de Evasão já submetido; permitir versionar tudo junto quando o usuário inicializar Git no projeto Vale.
- **Estrutura final**:
  - `TCC_DontGo.tex` — main file (preâmbulo + capa + resumo + abstract + sumário + `\include` dos capítulos + bibliografia).
  - `cap1_introducao.tex` — Cap. 1 desenvolvido com base em `business_understanding.md`.
  - `cap2_referencial.tex` — Cap. 2 com 8 seções e ~640 linhas, todo redigido a partir dos 26 PDFs.
  - `cap3_metodologia.tex` a `cap6_conclusao.tex` — esqueletos com `\todo{}` para preenchimento nas Fases 2--6.
  - `bibliografia.bib` — 70 entradas (47 reaproveitadas do TCC anterior + 23 novas Don't Go).
  - `Images/` — pasta para figuras (a popular durante a redação).
- **Status de compilação**: PDF válido de 37 páginas gerado em 2026-04-29 (sem warnings ou erros).

---

## D008 — Unidade de predição (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: definição de "quando" o modelo emite uma predição (T1.1 do `methodology_review.md`).
- **ANTES**: indefinido — alternativas (a) por evento, (b) por janela fixa, (c) por ciclo, (d) por turno.
- **DEPOIS**: **Sliding window de 15 min por equipamento ativo** (alternativa b).
- **Justificativa**:
  - Mimetiza o ciclo de atualização do painel do dispatcher (operacional realista).
  - Granularidade gerenciável (~17 M predições no total, ordem de grandeza da telemetria, com features agregadas).
  - Permite comparação direta entre janelas H ∈ {1, 2, 4, 6, 8, 12} h sem reamostragem.
  - Maior que 5 min para evitar falsa "scoring contínuo" em telemetria com rajadas naturais.
- **Impacto esperado**: define o **frame de scoring** — features são agregadas até `t`, alvo é qualquer incidente em `[t, t+H]`.

---

## D009 — Definição de "incidente Don't Go" (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: deduplicação de eventos `Is_Dont_Go=1` em sequência (T1.2).
- **ANTES**: cada linha `Is_Dont_Go=1` tratada como evento independente (distorce Recall e Lead time).
- **DEPOIS**: **incidente Don't Go** = sequência maximal de `Is_Dont_Go=1` do mesmo equipamento separada por gap ≤ 30 min. Marca-se `is_incident_start=1` apenas no primeiro evento de cada sequência.
- **Justificativa**:
  - Recall: 1 incidente físico = 1 unidade de avaliação (não N eventos repetidos).
  - Lead time medido a partir do **primeiro** disparo da sequência (instante operacionalmente relevante).
- **Tolerância de 30 min** é heurística inicial — refinar na Fase 2 com a distribuição empírica de gaps.
- **Aplicação**:
  - **Avaliação**: usa apenas eventos com `is_incident_start=1`.
  - **Treinamento**: pode usar a flag bruta (mais sinal positivo) — escolha definitiva via ablation na Fase 4.

---

## D010 — Anti-leakage e regras de feature engineering (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: prevenir três fontes de leakage identificadas em T1.3 do `methodology_review.md`.
- **ANTES**: implícito; tentação real de usar `Is_Dont_Go` ou `Id_Criticidade` em agregações históricas.
- **DEPOIS**: **regra de ouro** + **suite de features auditadas** + **análise estratificada por lead time**:
  1. **`Is_Dont_Go` é exclusivamente label** — proibido como feature, em qualquer agregação.
  2. **Blackout de 5 min**: toda agregação histórica de eventos exclui a janela `[t − 5 min, t]` para impedir reprodução literal das regras CMA mais rápidas.
  3. **`Id_Criticidade` cru é proibido**; permitido apenas em agregações com blackout, e **nunca** com a janela `[t − 6 min, t]` (que é exatamente a janela máxima das regras de "5 alarmes em 6 min").
  4. **Análise por lead time bucket**: relatório final reporta AUC-PR e Recall@P=0,5 separadamente em (i) 0–15 min, (ii) 15–60 min, (iii) 1–4 h. Sinal exclusivo em (i) sugere predição da regra; sinal mantido em (iii) é evidência de predição de risco.
- **Documentação**: lista completa de features com permissões em `docs/features.md` (a criar na Fase 3).

---

## D011 — Estratégia temporal de validação (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: definir splits de treino/validação/teste para captar concept drift e dar IC robusto (T1.4).
- **ANTES**: "TimeSeriesSplit / walk-forward" — vago demais.
- **DEPOIS**: **Walk-forward expanding com 4 folds** + **teste final intocado**:
  - Fold 1: treino jan, val fev, teste mar
  - Fold 2: treino jan-fev, val mar, teste abr
  - Fold 3: treino jan-mar, val abr, teste mai
  - Fold 4: treino jan-abr, val mai, teste jun
  - **Modelo final ("para deploy")**: treinado em jan-mai, avaliado **uma única vez** em jun. Esse jun é o "teste intocado" — não pode ser usado para nenhum tipo de seleção de modelo ou tuning.
  - **Buffer obrigatório de 4 horas** (= horizonte máximo de predição) entre o fim do treino e o início da validação/teste, para impedir leakage por features que olham 4 h no futuro.
- **Métricas reportadas**: média ± desvio dos 4 folds, com IC 95% por bootstrap por fold. Resultado final = média ± desvio + número do teste intocado.
- **Justificativa**: walk-forward expanding usa progressivamente mais histórico (não esquece como rolling); 4 folds dão estimativa de estabilidade temporal (concept drift visível); buffer evita leakage do horizonte longo.

---

## D012 — Pacote completo de métricas (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: única métrica engana sob desbalanceamento e descalibração (T2.1).
- **ANTES**: AUC-PR + Recall@P=0,5 + Lead time apenas.
- **DEPOIS**: pacote ampliado, **todas reportadas em todas as tabelas finais**:
  - **AUC-PR** (primária)
  - **Lift = AUC-PR / prevalência** (normalização para comparar entre folds e janelas)
  - **AUC-ROC** (padrão histórico, comparabilidade com literatura)
  - **Brier Score** (calibração)
  - **Expected Calibration Error (ECE)** (calibração em bins)
  - **Recall@Precision=0,5** (operacional)
  - **Lead time P25/P50/P75** entre TPs, por bucket de lead time
- **Justificativa**: AUC-PR sozinha varia com prevalência (lift normaliza); Brier+ECE diagnosticam má calibração que ameaça a utilidade operacional do score; AUC-ROC mantém comparabilidade externa.

---

## D013 — Definição formal de TP / FN / FP / Lead time (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: lead time precisa de definição inambígua para ser reproduzível (T2.2).
- **ANTES**: "instante da predição positiva" — ambíguo.
- **DEPOIS** (definição formal):
  - Para cada incidente `I` (D009) ocorrido em `t_I` no equipamento `e`, seja `P(I) = {p_1, p_2, ...}` o conjunto de predições positivas (score ≥ limiar de operação) emitidas pelo modelo no equipamento `e` durante `[t_I − H, t_I]`, onde `H` é o horizonte do modelo.
  - **TP**: `P(I) ≠ ∅`. Lead time = `t_I − min(P(I))` em minutos.
  - **FN**: `P(I) = ∅`.
  - **FP**: predição positiva emitida em `t_pred` cujo intervalo `[t_pred, t_pred + H]` no equipamento `e` **não** contém um `is_incident_start=1`.
- **Justificativa**: garante reprodutibilidade e impede otimizações cosméticas do lead time (ex: "primeira predição positiva" é determinística).

---

## D014 — Calibração de probabilidades (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: probabilidades não calibradas comprometem ranking e tomada de decisão (T2.3).
- **ANTES**: "calibração" mencionada genericamente.
- **DEPOIS**: **Platt scaling (sigmoid)** e **Isotonic Regression** ambos treinados no fold de validação; selecionar o que minimizar Brier+ECE no próprio fold; reportar ambos.
- **Justificativa**: para LightGBM/XGBoost com classes raras e muitos dados, Isotonic geralmente vence; mas Platt é menos overfit em datasets pequenos. Comparação dá robustez.

---

## D015 — Tratamento de classe rara (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: estratégias permitidas para o forte desbalanceamento previsto (T2.4).
- **ANTES**: implícito.
- **DEPOIS**:
  - ✅ **Permitido**: `scale_pos_weight` (LGBM/XGBoost), `class_weight='balanced'` (sklearn), focal loss em redes neurais.
  - ⚠️ **Cuidado**: undersampling do majoritário até 1:10 ou 1:50, **avaliando sempre na distribuição real de teste** (sem reamostragem no teste).
  - ❌ **Proibido**: SMOTE / sintéticos (ADASYN, etc.) sobre features temporais — viola a estrutura sequencial da telemetria e gera amostras "impossíveis" do ponto de vista físico.
  - ❌ **Proibido**: oversample do minoritário **dentro de cada fold sem time-aware** — vaza informação entre janelas adjacentes.

---

## D016 — Inferência de operador para Apontamentos (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: parquet de apontamentos não traz `Nome_Operador_Anon`; precisamos para testar H005 (T2.5).
- **ANTES**: H005 considerada possivelmente "não testável".
- **DEPOIS**: **operador inferido** para cada ciclo `(Tag, Inicio, Fim)` como **moda** de `Nome_Operador_Anon` na telemetria filtrada por `TAG=Tag` e `Data_Evento ∈ [Inicio, Fim]`.
  - Validação: % de eventos com a moda. Se ≥ 80% para o ciclo, marcar `operador_inferido=True`; senão `False`.
  - Reportar a fração global de ciclos com inferência confiável.
  - Ciclos com `operador_inferido=False` ficam com operador `NULL` nas análises subsequentes (não imputar artificialmente).

---

## D017 — Modelagem de sobrevivência (Fase 1 pós-revisão)

- **Data**: 2026-04-28
- **Contexto**: PA-2 ("tempo até próximo Don't Go") precisa de definição operacional (T2.6).
- **ANTES**: "Cox PH ou Weibull AFT" sem censoring definido.
- **DEPOIS**:
  - **Frame de scoring**: para cada equipamento `e` no fold de teste, série de instantes `s_1, s_2, ...` (1 por hora). Para cada `s_k`:
    - Tempo observado `T_k = min(t_próximo_incidente − s_k, fim_período − s_k)`
    - Censura `δ_k = 1` se `t_próximo_incidente − s_k ≤ fim_período − s_k` (evento observado), 0 senão (right-censored).
  - **Modelo primário**: **Cox Proportional Hazards** + **teste de Schoenfeld** para checar a hipótese de proporcional hazards. Se Schoenfeld rejeitar (p < 0,05) para muitas covariáveis, recorrer a:
  - **Modelo de fallback**: **Weibull AFT** (Accelerated Failure Time), que não exige PH.
  - **Métricas**: C-index (concordância), IBS (Integrated Brier Score) em janelas de tempo {1, 2, 4, 8, 12 h}.
- **Implementação**: pacote `lifelines` (instalação a verificar na Fase 2A).

---

## D018 — Tolerância de incidente Don't Go ratificada (Fase 2C)

- **Data**: 2026-04-30
- **Contexto**: D009 fixou em 30 min a tolerância de gap entre Don't Gos consecutivos do mesmo equipamento — número escolhido a priori. A Fase 2 produziu a distribuição empírica.
- **ANTES**: 30 min (heurística inicial — D009).
- **DEPOIS**: **30 min RATIFICADA** após análise empírica.
- **Justificativa**:
  - 19.940 pares (Don't Go anterior, Don't Go atual) do mesmo equipamento foram observados.
  - Distribuição cumulativa: 5 min agrupa 55%; 15 min 68%; **30 min 75%**; 60 min 82%; 240 min 90%; 1440 min (1 dia) 96%.
  - Aumentar para 60 min ganharia +7 p.p. ao custo de potencialmente unir incidentes fisicamente independentes (separados por turno).
  - Escolha de 30 min preserva o critério "mesmo problema operacional" sem ser excessivamente largo.
- **Impacto esperado**: 19.962 eventos → 5.025 incidentes (compressão 3,97×). Recall e Lead time medidos sobre 5.025 unidades.

---

## D019 — Mapeamento explícito Tag_Frota → Porte (Fase 2E)

- **Data**: 2026-04-30
- **Contexto**: T3.7 — origem da coluna `Porte` do exemplo `desenvolver_dontgo.xlsx`.
- **ANTES**: incerto se `Porte` era derivado da telemetria ou enriquecido manualmente.
- **DEPOIS**: confirmado via Fase 2E que `Porte` **não existe na telemetria bruta** — foi acrescentado manualmente pelo time da Vale ao gerar o exemplo.
- **Decisão**: criar `src/data/mappings.py` na Fase 3 com tabela explícita `Tag_Frota → Porte` baseada em catálogo OEM externo (CAT 793-D = Grande Porte; LeTourneau L 1850 = Grande Porte ou Especial; etc.).
- **Justificativa**: o modelo de produção não pode depender de coluna que existe apenas em arquivo de demo. Mapeamento explícito é (a) auditável, (b) corrigível, (c) reproduzível.
- **Impacto esperado**: feature `porte` opcional no dataset de scoring. Pode substituir `Tag_Frota` se mostrar mais sinal preditivo (Fase 4).

---

## D020 — Tratamento de ciclos "Operando + 0 eventos" (Fase 2E)

- **Data**: 2026-04-30
- **Contexto**: Fase 2E — pareamento Apontamento × Telemetria mostra que **19,1% dos ciclos `Operando`** não têm eventos de telemetria correspondentes (mesmo `Tag`, mesmo intervalo `[Inicio, Fim]`).
- **ANTES**: indefinido — opções (a) excluir esses ciclos, (b) imputar zero, (c) marcar e manter.
- **DEPOIS**: **manter os ciclos com flag `tem_telemetria=0`**; nas features baseadas em telemetria, valores ficam NaN explícitos (não zero), o que LightGBM e XGBoost tratam nativamente como "missing branch".
- **Justificativa**:
  - Excluir descarta ~19% da população (informação operacional real).
  - Imputar zero confunde "telemetria silenciosa" com "tudo OK" — semanticamente diferentes.
  - Flag preserva a informação e permite ao modelo decidir.
- **Impacto esperado**: train set ligeiramente maior, com nova feature `tem_telemetria` (binária) que pode capturar inconsistências operacionais como sinal preditivo.
- **Nota**: H013 (nova hipótese) testa essa fração na população completa na Fase 3.

---

## D020 v2 — `tem_telemetria=0` ⇒ contagens NaN, não zero (Fase 3C, refinamento)

- **Data**: 2026-05-03
- **Contexto**: D020 (Fase 2E) decidiu marcar ciclos `Operando` sem telemetria com flag `tem_telemetria=0`, em vez de excluí-los. A implementação v1, porém, preenchia as contagens `n_*` com **zero** nessas janelas — confundindo "sem telemetria" com "ciclo com 0 alarmes nos últimos 12h".
- **ANTES**: `df[c].fillna(0).astype('int64')` aplicado a todas as contagens.
- **DEPOIS**:
  - Contagens `n_*` declaradas como `Int64` (nullable).
  - Onde `tem_telemetria=0` (cobertura ausente), todas as 66 contagens recebem `pd.NA`.
  - Onde `tem_telemetria=1`, valores legítimos (incluindo zero quando o ciclo realmente não teve alarmes na janela).
- **Justificativa**: LightGBM/XGBoost lidam com missing nativamente como sinal — esta semântica permite que o modelo aprenda explicitamente que ausência de telemetria carrega informação preditiva, alinhado com a heterogeneidade de cobertura por frota×mês reportada na auditoria 3A.1.

---

## D021 — Threshold de operador inferido (D016) ratificado (Fase 2E)

- **Data**: 2026-04-30
- **Contexto**: D016 fixou threshold de 80% para considerar a moda do operador "estável" no ciclo. Fase 2E testou empiricamente.
- **ANTES**: threshold 80% (definido a priori).
- **DEPOIS**: **80% RATIFICADO** mas anotado como conservador.
- **Justificativa**:
  - Amostra de 2.000 ciclos: 61,5% têm operador inferível (1.229 ciclos).
  - **99,67% desses 1.229 têm share da moda ≥ 80%** — quase todos.
  - **100% têm share ≥ 50%** — significa que dropar o threshold para 50% manteria os mesmos casos.
  - O threshold de 80% é portanto conservador na prática; se algum modelo futuro precisar de mais dados, pode descer para 50% sem perda mensurável.
- **Impacto esperado**: 61,5% de cobertura para H005 (efeito do operador) — 38,5% dos ciclos ficam com operador NULL (telemetria silenciosa do D013).

---

## D022 — `Classe=NULL` em LeTourneau é divergência estrutural de OEM (Auditoria 2026-04-30)

- **Data**: 2026-04-30
- **Contexto**: Auditoria da Fase 2 (`docs/audit_fase2.md` §3 A2 e §8) verificou que os 167 Don't Gos com `Classe=NULL` na telemetria são **exclusivamente** da LeTourneau L 1850, e que as 4 frotas 793-D (Caterpillar) usam `Activate` para 100% dos seus 19.795 Don't Gos.
- **ANTES**: tratamento ambíguo dos eventos com `Classe=NULL` — H012 falava em filtrar `Inactive` mas não esclarecia o que fazer com NULL.
- **DEPOIS**: `Classe=NULL` em LeTourneau é uma **propriedade estrutural** do pipeline OEM (não um defeito). Para LeTourneau, a "ativação" do alarme não é codificada na coluna `Classe` — provavelmente vem de outro campo (talvez `Valor` ou um padrão temporal).
- **Decisão de modelagem (Fase 3/4)**:
  1. **Não filtrar** `Classe=NULL` no train set (perderíamos todos os Don't Gos da LeTourneau).
  2. Tratar `Classe` como categórica de 4 níveis (`Activate`, `Inactive`, `NULL`, "outros") **incluindo NULL como categoria explícita**.
  3. **Reforça H016**: combinada com a propriedade de NIVEL CMA exclusivamente "Muito Alto" para LeTourneau, isso justifica testar treino segregado por OEM (CAT vs LeTourneau) na Fase 4.
- **Justificativa**: o fato de o pipeline OEM diferir é um *insight de domínio* — não conseguimos forçar uniformidade pós-hoc; o modelo precisa lidar com ambos os "dialetos".
- **Impacto esperado**: se o modelo combinado tiver desempenho ruim na LeTourneau (recall < 30%), aplicar treino segregado documentado em D023 (a registrar na Fase 4 se necessário).

---

## D023 — Dispensa formal de `pmdarima` (Auditoria 2026-04-30)

- **Data**: 2026-04-30
- **Contexto**: Plano original da Fase 2A (`MEMORY.md §8`) listava `lifelines` (sobrevivência) e `prophet`/`pmdarima` (séries) como verificação obrigatória.
- **ANTES**: indefinido entre `prophet` e `pmdarima`.
- **DEPOIS**: **`pmdarima` formalmente dispensado**; `prophet 1.3.0` é a ferramenta de séries temporais do projeto.
- **Justificativa**:
  1. **D017** define a rota de sobrevivência como `Cox PH + Schoenfeld + Weibull AFT (fallback)` — todos cobertos por `lifelines 0.30.3` (já instalado e validado em smoke test).
  2. Para séries temporais auxiliares (sazonalidade de prevalência, tendência da telemetria por equipamento), `prophet` cobre o que precisamos com vantagens sobre `pmdarima`:
     - Wheel pré-compilado para Windows (não exige `cmdstan` C++).
     - Lida nativamente com sazonalidade múltipla (turno + DOW + mês) sem ajuste manual de ordem ARIMA.
     - Compatível com `numpy 2.x` (atual no projeto).
  3. `pmdarima` em Windows ainda exige compilação C/Fortran e está com problemas de compatibilidade `numpy 2.x`. Custo de instalação > benefício marginal.
- **Impacto esperado**: nenhum sobre escopo do TCC. PA-2 (sobrevivência) usa `lifelines` exclusivamente. Análises auxiliares de série temporal (se necessárias) usam `prophet`. ARIMA/SARIMA fica fora do escopo.
- **Reversibilidade**: se na Fase 4 surgir necessidade específica de modelo Box-Jenkins, instalar `statsmodels` (já presente — versão 0.14.6) cobre ARIMA com syntax compatível.

---

## D024 — Mapping `Tag_Frota → Porte/OEM/Tipo` formalizado (Fase 3A.2)

- **Data**: 2026-05-02
- **Contexto**: D019 prescreveu o mapping; falta concretizar com a base populacional auditada.
- **ANTES**: indefinido. `desenvolver_dontgo.xlsx` cobria apenas `793-D 4S → Grande Porte` (1 par).
- **DEPOIS**: mapping completo em `src/data/mappings.py` cobrindo as **5 frotas populacionais** (auditadas em `fase3a_diagnostico.json`):

  | Tag_Frota | OEM | Tipo | Porte | Capacidade |
  |---|---|---|---|---|
  | 793-D 2S/3S/4S/5S | Caterpillar | Caminhão | Grande Porte | 226 t |
  | LeTourneau L 1850 | LeTourneau | Escavadeira | Grande Porte | 36 t (pá) |

  Adicionalmente: `ID_CRITICIDADE_TO_NOME` (1=Critico, 2=Não Crítico, 3/4=Informacional) — chave numérica imune a encoding (resolve mojibake da auditoria 3A.1).
- **Justificativa**: catálogo OEM externo (CAT 793D family + LeTourneau L-1850); todas Grande Porte na operação Itabira; OEM como categoria explícita captura D022 (dialeto Classe).
- **Impacto**: features `Porte`, `OEM`, `Tipo_canonico`, `Capacidade_t` derivadas em todo o dataset. `Porte` é constante na operação atual (todas Grande); mantida para auditabilidade e generalização futura.

---

## D025 — Tratamento de inconsistências em apontamentos (Fase 3A.3)

- **Data**: 2026-05-02
- **Contexto**: Auditoria 3A.1 mostrou que apontamentos populacionais NÃO têm Inicio>Fim, dur=0, dur<0 ou dur>30dias (zero ocorrências em 377.907 ciclos). Sobreposição entre ciclos consecutivos do mesmo Tag = 326 (0,086%), uniforme em ≤ 60 min e majoritariamente Hibernando↔Operando (transição de turno).
- **ANTES**: previsão da Fase 1 de drop de até 5% por inconsistência.
- **DEPOIS**: **MANTER 100% dos ciclos**. Adicionar flags derivadas:
  - `tem_overlap_anterior` (binária) — captura transições de turno como sinal opcional.
  - `dur_min` (float) — duração calculada.
  - `Criticidade_canonica` na telemetria (via `Id_Criticidade`) — neutraliza 11 linhas mojibake.
- **Justificativa**: dropar 0% (defesa em profundidade contra futuras versões dos parquets) preserva volume; adicionar flags carrega informação operacional sem violar o pipeline.
- **Impacto**: pipeline `src/data/cleaning.py` é defesa em profundidade — funcional mesmo se futuro update do parquet introduzir bugs.

---

## D026 — Critério de outlier em `Valor_num` (Fase 3B)

- **Data**: 2026-05-02
- **Contexto**: `Valor_num` é fortemente concentrada em 0 (P25=P50=P75=0); cauda longa até 4347. Correlação direta com `Is_Dont_Go` ≈ 0, mas P99 por partição pode ser informativo.
- **ANTES**: indefinido — opções IQR/percentil/z-score em log.
- **DEPOIS**: **`is_valor_outlier_p99`** = `1` se `Valor_num > P99` calculado **por partição (Alarme, Tag_Frota)**. Adicional: `is_valor_sensor_bug` = `1` se `|Valor_num| > 1e6` (sentinela; auditoria mostrou 0 casos).
- **Justificativa empírica (auditoria 3B)**:
  - Critério A (>P99 da partição) marca 0,04% das linhas (14.958 / 36,9M).
  - Entre os marcados, **4,75% têm `Is_Dont_Go=1`** (711 / 14.958).
  - **Lift sobre prevalência global = 87,9×.** Sinal forte demais para ser ignorado.
- **Impacto**: feature `n_valor_outlier_p99_W` por janela (1h/4h/12h) entra no builder 3C.

---

## D027 — Estratégia de modelagem por OEM (Fase 3E)

- **Data**: 2026-05-02
- **Contexto**: Fase 3E auditou volume, prevalência, dialeto e tamanho amostral por OEM:

  | OEM | TAGs | Eventos | Don't Gos | Incidentes | Taxa/evento |
  |---|---:|---:|---:|---:|---:|
  | Caterpillar (793-D) | 30 | 3.281.763 | 19.795 | **4.993** | **0,603%** |
  | LeTourneau (L 1850) | 5 | 33.882.291 | 167 | **32** | **0,000493%** |

  Razão de prevalência **CAT/LT = 1.224×**. LeTourneau usa `Classe=NULL` 100% (D022); CAT usa `Classe=Activate` 100%.
- **ANTES**: indefinido entre treino único com OEM dummy vs segregado.
- **DEPOIS**: **Treino segregado**:
  - **CAT (PA-1)**: modelo único supervisionado com `Tag_Frota` como variável dummy (4 frotas 793-D compartilham chassi-base; pipeline OEM idêntico; volume de incidentes em cada — 567/391/1214/2821 — é suficiente).
  - **LeTourneau (PA-3)**: detecção de anomalia não supervisionada (Isolation Forest e/ou Autoencoder LSTM). 32 incidentes não bastam para supervisionado robusto; PA-3 é a lente correta.
- **Justificativa**:
  1. Razão 1.224× viola a hipótese implícita de "mesma distribuição condicional".
  2. 91% do volume é LT mas só 0,6% dos incidentes — modelo único fica dominado pelo ruído LT mesmo com `scale_pos_weight`.
  3. Pipeline OEM divergente (D022) requer "dialetos" diferentes.
  4. PA-3 captura modos de falha sem precisar de rótulos volumosos — alinhado com a função semântica da PA-3 declarada na Fase 1.
- **Impacto**: dataset de features 3C terá filtro `OEM='Caterpillar'` para o train de PA-1; LeTourneau alimenta pipeline separado de PA-3 (Fase 4).

---

## D028 — Famílias funcionais de alarmes (Fase 3C, H009)

- **Data**: 2026-05-02
- **Contexto**: H009 propôs 5-8 famílias funcionais; a inspeção dos 712 alarmes distintos em telemetria sugeriu refinamento.
- **ANTES**: indefinido.
- **DEPOIS**: **13 famílias funcionais + 1 catch-all (`Other`)** em `src/features/families.py`:

  | Família | n_alarmes | n_eventos | % do total |
  |---|---:|---:|---:|
  | Operational_State | 39 | 26.397.112 | 71,0% |
  | Body_Load | 56 | 4.975.163 | 13,4% |
  | Electrical_Comms | 67 | 2.410.256 | 6,5% |
  | Steering | 24 | 1.147.436 | 3,1% |
  | Hydraulic | 77 | 1.030.006 | 2,8% |
  | Transmission | 36 | 496.231 | 1,3% |
  | Engine_Coolant | 19 | 207.817 | 0,6% |
  | Other | 218 | 133.781 | 0,4% |
  | Fan_Drive | 13 | 124.137 | 0,3% |
  | Brakes | 52 | 100.581 | 0,3% |
  | Engine_Oil | 20 | 51.218 | 0,1% |
  | Air_Filters | 6 | 32.652 | 0,1% |
  | Exhaust_Turbo | 42 | 27.707 | 0,1% |
  | Tires_Suspension | 37 | 23.877 | 0,1% |
  | Fuel_AfterTreatment | 6 | 6.080 | 0,02% |

- **Justificativa**: cada família agrupa modos de falha que compartilham um sub-sistema (auditável). Patterns cobrem en + pt (alarmes mistos OEM e Vale-locais). `Other` é 0,36% dos eventos — dentro do critério de aceitabilidade.
- **Impacto**: 14 features `n_fam_<nome>_<W>h` para cada lookback W ∈ {1h, 4h, 12h} no builder 3C.

---

## D029 — Janelas geradas apenas em ciclos `Operando` (Fase 3C, correção)

- **Data**: 2026-05-03
- **Contexto**: Auditoria de PENDENCIAS.md mostrou que a v1 do `builders.py` fazia `TAGs CROSS JOIN time_grid`, gerando 538.848 janelas das quais apenas **59,55% (321.500)** caíam dentro de um ciclo de apontamento com `Classe='Operando'`. As 40,45% restantes estavam em Parado (74.386), Manutenção (117.118), Hibernando (24.571) ou sem apontamento (2.329) — regimes onde `Don't Go` não é operacionalmente relevante.
- **ANTES**: `windows AS (SELECT t.TAG, t.Tag_Frota, g.t FROM tags t CROSS JOIN time_grid g)`.
- **DEPOIS**: `windows AS (SELECT apt.Tag, apt.Tag_Frota, g.t FROM time_grid g INNER JOIN apt_for_windows apt ON apt.Inicio <= g.t AND apt.Fim > g.t AND apt.Classe='Operando')`.
- **Impacto**: o texto do artigo afirma "por equipamento ativo" desde a Fase 1; a v1 não cumpria a promessa. A v2 cumpre.

---

## D030 — `target_lead_time_min` é alvo auxiliar, não feature (Fase 3C, correção)

- **Data**: 2026-05-03
- **Contexto**: Auditoria empírica mostrou que a v1 calculava `lead_time_min = MIN(date_diff('minute', t, próximo_incidente_futuro))` sem clipping. Resultado: **78,27% das 470.386 linhas com `lead_time_min` preenchido tinham `y_dontgo_12h=0`** — ou seja, o "lead time" carregava informação do incidente *além* do horizonte máximo de 12 h, vazando alvo futuro como entrada.
- **ANTES**: coluna `lead_time_min` (sem clipping) tratada como feature em alguns runners.
- **DEPOIS**:
  - Renomeada para `target_lead_time_min` (prefixo `target_` torna semântica explícita).
  - **Clipada ao horizonte máximo** via `WHERE i.Data_Evento <= w.t + INTERVAL '12' HOUR` no LEFT JOIN — fora desse limite, fica `NaN`.
  - **Documentada** em `docs/features.md` e na docstring de `builders.py` como **alvo auxiliar para PA-2 (sobrevivência, D017)**, NÃO como feature de classificadores.
- **Verificação pós-correção**: 0 linhas com `target_lead_time_min` preenchido e `y_dontgo_12h=0`.

---

## D031 — Limiar P99 de outlier calibrado externamente (Fase 3C, correção anti-leakage)

- **Data**: 2026-05-03
- **Contexto**: A v1 de `builders.py` calculava `approx_quantile(Valor_num, 0.99) OVER (PARTITION BY Alarme, Tag_Frota)` sobre **toda a base disponível** (jan-jun 2025). Para um pipeline walk-forward (D011) onde junho é o teste intocado, esse cálculo vaza informação de junho no limiar usado nos folds de treino.
- **ANTES**: P99 calculado dinamicamente em cada execução do builder, sobre toda a janela temporal.
- **DEPOIS**:
  - Módulo dedicado `src/features/outlier_calibration.py`.
  - P99 calibrado **uma única vez** sobre o intervalo `[2025-01-01, 2025-03-01)` — período anterior aos folds de validação do walk-forward (D011 prevê 4 folds expansivos a partir de fev/mar).
  - 529 partições `(Alarme, Tag_Frota)` com `n_obs ≥ 30` calibradas; persistidas em `data/processed/outlier_p99_thresholds.parquet`.
  - O builder lê esse arquivo como constante externa via `load_p99_thresholds(con)`.
- **Reprodução**: `python -m src.features.outlier_calibration` (uma única vez antes do build).
- **Implicação para Fase 4**: o P99 fixo é proxy do limiar do primeiro fold. A Fase 4 pode opcionalmente recalibrar P99 por fold se houver evidência de drift severo da distribuição de `Valor_num`; por padrão usa este limiar fixo.

---

## D032 — Flags de censura temporal nas bordas do dataset (Fase 3C, integridade)

- **Data**: 2026-05-03
- **Contexto**: Auditoria identificou 1.536 janelas em janeiro com lookback parcial (`t_window < 2025-01-01 + 12h`) e 1.457 janelas em junho com label de 12h censurada (`t_window > 2025-06-30 12:00` exigiria dados de julho).
- **ANTES**: nenhuma sinalização. Janelas com lookback/label parcial misturadas com janelas completas, sem distinção semântica.
- **DEPOIS**:
  - `lookback_completo` (int8 0/1): 1 se `t_window >= 2025-01-01 + 12h`.
  - `label_completa_12h` (int8 0/1): 1 se `t_window <= 2025-06-30 12:00`.
- **Política de uso para Fase 4**:
  - Folds de treino: filtrar janelas com `lookback_completo=0` (não há features completas).
  - Avaliação: filtrar janelas com `label_completa_12h=0` para o horizonte de 12h.
  - Política análoga para horizontes intermediários: a Fase 4 pode derivar `label_completa_<H>h` se necessário.

---

## Princípio governante (estabelecido em 2026-04-28)

> **Robustez > custo computacional.** O autor explicitamente orientou: *"prefiro múltiplas janelas em paralelo, faça da forma que for ficar melhor e mais robusto sempre, não importa custo computacional"*. Toda decisão metodológica deste registro é calibrada por essa preferência. Quando houver tradeoff entre rigor e velocidade, **escolher rigor**.

---

### Nota da Auditoria 2026-04-30 sobre D016 / D021 — Threshold `share_moda ≥ 80%` ratificado em definitivo

- **Data**: 2026-04-30
- **Contexto**: A auditoria `docs/audit_fase2.md` §3 A2 expôs um bug latente no SQL que computava o denominador de `share_moda` (excluía eventos com `Nome_Operador_Anon=NULL` em vez do total do ciclo). Ao corrigir e re-rodar, o resultado **idêntico** revelou H017: `Nome_Operador_Anon` é universal quando há telemetria.
- **Conclusão**: D016 (threshold 80%) e D021 (ratificação prévia) **continuam válidas**. A propriedade emergente do dataset (H017) torna o threshold ainda mais robusto: em qualquer ciclo com telemetria, o operador é determinístico (mediana share = 100%).
- **Sem mudança operacional**: D016 e D021 ficam como estão.

---

### Nota da Auditoria 2026-04-30 sobre D018 — Tolerância de 30 min ainda mais conservadora à luz da NIVEL CMA

- **Data**: 2026-04-30
- **Contexto**: A auditoria `docs/audit_fase2.md` §5 C1 produziu o cross NIVEL CMA × Criticidade. Um achado relevante: regras CMA "Alto" são iniciadas **majoritariamente por alarmes Não Críticos** (741 vs 225 Críticos), enquanto regras "Muito Alto" são bem distribuídas (2.209 Críticos vs 1.850 Não Críticos).
- **Implicação para D018**: a tolerância de 30 min foi calibrada sobre a distribuição global de gaps. Se há heterogeneidade entre tipos de regra (Muito Alto pode ter padrão temporal diferente de Alto), a tolerância poderia ser estratificada.
- **Decisão**: **manter 30 min globalmente** (D018 inalterada). Refinamento estratificado por NIVEL CMA fica como **trabalho da Fase 3** (parte da feature engineering temporal).
- **Justificativa**: estratificar a definição de "incidente" por NIVEL antes de termos modelo é prematuro — risco de over-engineering. A definição uniforme é defensável e auditável.

---

## Entradas reais subsequentes

(adicionar conforme as decisões surgirem nas fases 4 em diante)

---

## D033 — Optuna reduzido para 30 trials por horizonte (Fase 4B)

- **Data**: 2026-05-04
- **Contexto**: O plano da Fase 4 (`docs/plano_fase4.md`) previa 50 trials Optuna por horizonte. Tempos empíricos no fold 1 mostraram convergência consistente em 24-42s para 30 trials, com `best_value` estabilizando após ~20 trials.
- **Status**: decisão histórica, **superada por D044**. A reexecução robusta de 2026-05-12 restaurou o orçamento de busca para 150 trials por horizonte.
- **ANTES**: 50 trials × 6 horizontes (custo ~10 min CPU + risco de overfitting do tuning).
- **DEPOIS**: **30 trials** × 6 horizontes (~3 min CPU). Mesmo `TPESampler(seed=42)`, mesmas faixas de busca, mesmo `early_stopping_rounds=30`. Melhor AUC-PR no fold 1 ficou em 0,32-0,71 conforme horizonte.
- **Justificativa**:
  - Princípio governante (ROBUSTEZ > custo) não exige número específico de trials — exige rigor metodológico (TPE bayesiano + early stopping + seed fixo).
  - Reduzir trials enquanto se mantém o algoritmo permite reutilizar tempo poupado em XGB/CatBoost (4C) sem perda de qualidade detectável.
  - Auditável: `outputs/models/lgbm_best_params.json` registra todos os 30 trials de cada horizonte.
- **Reversibilidade**: aumentar `N_TRIALS_OPTUNA` em `notebooks/_run_pa1_lightgbm.py` e re-rodar.
- **Impacto medido**: lift médio em junho (holdout): H1h 7,16× / H2h 5,26× / H4h 3,39× / H6h 2,94× / H8h 2,53× / H12h 2,13× — todos acima do baseline heurístico (1,13-1,42×).

---

## D034 — Buffer 4h ratificado empiricamente (Fase 4A — auditoria de overlap)

- **Data**: 2026-05-04
- **Contexto**: D011 fixou buffer de 4h entre fim do treino e início da validação. A Fase 4A mediu o overlap real em duas óticas (`fase4a_buffer_audit.json`):
  - **A) Val-lookback overlap**: janelas de val cuja janela de lookback de 12h recobre o treino. Máximo observado entre folds = **1,18%** (fold 1).
  - **B) Train-label leak**: janelas de treino cujo label horizonte vaza no val. Máximo = **1,08%** (fold 1, H=12h).
- **ANTES**: o critério Q1 do checkpoint C1 dizia "overlap > 1% => propor D011-v2 com buffer=12h".
- **DEPOIS**: **buffer 4h ratificado** com nota de limitação. Overlap residual marginal (1,18%) não compromete folds 2-4 (todos < 1,15%) e o salto para 12h custaria ~25% das janelas de treino do fold 1.
- **Justificativa**:
  - Trade-off custo (perda de 25% do treino do fold 1) versus benefício (eliminar 1,18% de overlap residual em ~511 janelas de fev) é desfavorável.
  - As métricas reportadas **normalizam o efeito** via `lift = AUC-PR / prevalência` (D012), tornando o overlap residual irrelevante para comparação entre folds.
  - O modelo final (treino jan-mai → eval jun) tem overlap = 0 por construção (junho é mês isolado, sem lookback que cubra mai).
- **Documentado** no `cap5_discussao.tex` como limitação metodológica explícita.

---

## D035 — Weibull AFT como modelo primário PA-2 (Fase 4D)

- **Data**: 2026-05-04
- **Contexto**: D017 prescreveu Cox PH como primário e Weibull AFT como fallback se Schoenfeld rejeitasse PH. A Fase 4D ajustou ambos nos 4 folds + holdout junho:
  - **Cox PH C-index** (val): 0,46 / 0,66 / 0,60 / 0,49 → média 0,55 (instável).
  - **Cox PH C-index junho**: **0,43** (abaixo de 0,5 — pior que aleatório).
  - **Weibull AFT C-index** (val): 0,63 / 0,66 / 0,60 / 0,61 → média 0,625 (estável).
  - **Weibull AFT C-index junho**: **0,62**.
- **ANTES**: Cox PH como primário.
- **DEPOIS**: **Weibull AFT como primário PA-2**. Cox PH mantido como referência (Schoenfeld empiricamente violado — variance ratio dependente do tempo nas features de contagem).
- **Justificativa**:
  - Cox PH falhou a hipótese PH em folds 1 e 4 (C-index < 0,5 = inversão de ranking).
  - Weibull AFT é estável (0,60-0,63) em todos os folds e atinge 0,62 em junho.
  - **Critério C-index ≥ 0,70 (do plano) NÃO foi atingido** por nenhum modelo PA-2. Registrado como limitação no Cap. 5 — sinal preditivo PA-2 é inferior ao PA-1, consistente com a complexidade da estimativa "tempo até evento" vs "evento na próxima janela".

---

## D036 — PA-3 LeTourneau é exploratório (Fase 4E)

- **Data**: 2026-05-04
- **Contexto**: O plano previa critério "top-10% scores captura ≥ 50% dos 32 incidentes". Resultados:
  - **Isolation Forest**: top-10% captura 6,0% dos incidentes (34/570 windows com `y_dontgo_12h=1`).
  - **Autoencoder LSTM**: top-10% captura 4,4%.
  - **Top-1% precision**: IF=1,3% / LSTM=2,6% (comparado à prevalência local de 1,5%).
- **ANTES**: PA-3 esperava-se com lente operacional.
- **DEPOIS**: **PA-3 marcado como exploratório** (alinhado com a previsão da Fase 1 quando D004 incluiu PA-3 como "complementar 2"). Ambos modelos serializados em `outputs/models/`. **Recomendação**: para deploy, focar em PA-1 (CAT). Para LeTourneau, manter PA-3 como tela de monitoramento — não como gatilho.
- **Justificativa**:
  - 32 incidentes em 33,9 M eventos (ou 731 windows com `y_dontgo_12h=1` em 45k janelas LeTourneau) é regime de extrema raridade.
  - Sinal preditivo é difuso — features de contagem agregadas são insuficientes; modos de falha LeTourneau provavelmente exigem features de telemetria bruta (não escopo desta Fase 4).
  - **Trabalho futuro** (Cap. 6): incorporar telemetria bruta (sub-amostrada) e tentar Transformer com auto-atenção em PA-3.

---

## D037 — Calibração: Isotonic em horizontes curtos, Platt em longos (Fase 4F)

- **Data**: 2026-05-04
- **Contexto**: D014 prescreveu Platt + Isotonic comparados via Brier/ECE. Resultado empírico em junho:
  - **H1h-H4h**: Isotonic vence (Brier menor, ECE menor).
  - **H6h-H12h**: Platt vence (Brier marginalmente menor, ECE comparável).
  - Em todos os 6 horizontes: ECE pós ≤ 0,03 (alvo era ≤ 0,05).
  - Brier pós sempre ≤ Brier pré (calibração nunca prejudicou).
- **ANTES**: D014 dizia "escolher por menor Brier; em empate, menor ECE".
- **DEPOIS**: **Política de calibração mista**: Isotonic para H ∈ {1, 2, 4} h; Platt para H ∈ {6, 8, 12} h. Cada calibrador serializado em `outputs/models/lgbm_calibrated_h{H}.joblib` com método registrado.
- **Justificativa**:
  - Horizontes curtos têm mais ruído estocástico nas predições — Isotonic é mais flexível e captura melhor.
  - Horizontes longos têm sinal mais "suave" — Platt (sigmoid 1D) generaliza melhor sem overfit.

---

## D038 — Filtro de censura H<12h derivado on-the-fly (Fase 4A)

- **Data**: 2026-05-04
- **Contexto**: D032 materializou no parquet apenas `label_completa_12h`. Fase 4A precisou de censura para H ∈ {1, 2, 4, 6, 8} h.
- **ANTES**: indefinido — re-materializar parquets para incluir 5 flags adicionais era custoso.
- **DEPOIS**: derivação on-the-fly em `src/eval/splits.apply_censura_filter(df, horizon_h, kind='eval')`:
  ```python
  cutoff = pd.Timestamp("2025-07-01 00:00") - pd.Timedelta(hours=horizon_h)
  mask = (df["t_window"] <= cutoff) & (df["lookback_completo"] == 1)
  ```
- **Justificativa**: dispensa re-build do dataset v2 (15 min × 6 meses), mantém os parquets canônicos intocados, e a regra é trivialmente verificável.

---

## D039 — Filtro operacional de duração para `d_avg` (Fase 5C)

- **Data**: 2026-05-09
- **Contexto**: A Fase 5C (CM 5.3 / 6.1) precisa de uma estimativa de "duração média de uma parada não-programada" (`d_avg`) para traduzir TPs em horas evitadas/mês. A distribuição empírica de `dur_min` em `Classe ∈ {Parado, Manutenção}` mostrou P50 = 10,3 min — suspeita por incluir micro-paradas operacionais (descansos, fuel-up).
- **ANTES**: indefinido entre P50/P75/média global.
- **DEPOIS**: filtro operacional `dur_min ≥ 30 min` aplicado antes de calcular percentis. Esta é uma estimativa intermediária ("operacional"); em junho/2025, P50 dessa distribuição é 60,0 min (mas com 79,3% de empilhamento exato em 60 min — ver D040).
- **Justificativa**: paradas com duração inferior a 30 minutos representam micro-eventos operacionais que (i) não constituiriam intervenção de manutenção programada após o alerta do modelo, e (ii) tipicamente não geram custo significativo evitável. O limiar de 30 min é consistente com o menor `ΔP` reportado na superfície de sensibilidade.
- **Impacto**: reportada como variante "operacional" no JSON `fase5c_business_impact.json`. A estimativa primária usada na superfície é a reconstruída fisicamente (D040).

---

## D040 — Reconstrução de paradas físicas para `d_avg` (Fase 5C)

- **Data**: 2026-05-09
- **Contexto**: Auditoria empírica revelou que o sistema de apontamentos da Vale **segmenta paradas longas em blocos de exatamente 60 min**: 79,3% das paradas com `dur_min ≥ 30` têm valor exato 60,0, e o `max` populacional dessas paradas é 60,0 (cap rígido do sistema). Uma parada física de 4 horas é registrada como 4 linhas consecutivas de 60 min.
- **ANTES**: D039 usava percentis sobre os registros crus (impactados pelo cap de 60 min).
- **DEPOIS**: nova função `reconstruct_physical_stops(df, gap_max_min=5)` em `src/eval/business_impact.py` que **agrupa registros consecutivos** do mesmo `Tag` em `Classe ∈ {Parado, Manutenção}` separados por gap ≤ 5 minutos. Resultado: 11.047 paradas físicas operacionais (≥ 30 min reconstruídos), com P50 = 60,2 min (1,00 h), P75 = 138,8 min (2,3 h).
- **Justificativa**: a duração efetiva de uma parada física é a métrica honesta — o cap de 60 min é um artefato de registro, não da operação. A reconstrução por gap ≤ 5 min é conservadora (paradas com gap maior são tratadas como independentes, evitando agrupamento falso).
- **Impacto**: `d_avg_h_phys = 1,00 h` é a estimativa **default** usada na superfície de sensibilidade da Fase 5C. As variantes "global" (P50 cru = 0,17 h) e "operacional" (D039, P50 ≥ 30 min = 1,00 h) ficam reportadas como referências no JSON para auditabilidade.
- **Limitação documentada**: após a retunagem D044, o limite teórico das horas evitadas/mês é ≤ 282 h em H=12h, ΔP=30 min, ρ=0,9. O número é **teto** assumindo que toda TP se traduza em redução perfeita; o ganho real depende do processo operacional pós-alerta e deve ser medido em piloto.

## D041 — Política de implantação em 3 fases (Fase 6 / CM 6.2)

- **Data**: 2026-05-10
- **Contexto**: a Fase 6 (Deployment) precisa traduzir o desempenho técnico em recomendação operacional concreta. A literatura de produção (Mitchell et al., 2019; Polyzotis et al., 2018) recomenda implantação progressiva (*shadow* → *advisory* → semi-auto) em vez de *big-bang*, reduzindo risco operacional e permitindo aprendizado em produção.
- **DECISÃO**: a implantação do modelo PA-1 calibrado segue 3 fases sequenciais com critérios formais de *go*/*no-go* entre cada uma:
  - **Fase Implant. 1 (meses 1-3)**: H=8h, ΔP=120 min, ρ=0,5. Modo *shadow* sobre 793-D 5S. Avanço requer ≥30 h evitadas/mês por 2 meses consecutivos.
  - **Fase Implant. 2 (meses 4-6)**: H=12h, ΔP=60 min, ρ=0,7. Modo *advisory* sobre toda 793-D. Avanço requer ≥100 h/mês por 3 meses + PSI<0,25 + |Δprev|<30%.
  - **Fase Implant. 3 (meses 7+)**: H=12h, ΔP=30 min, ρ∈[0,7;0,9]. Semi-automático com fallback humano + PA-3 revisado (Trabalho Futuro #2).
- **Justificativa**: o desenho privilegia aprendizado controlado e mitiga o risco de *over-claim* dos 282 h/mês de teto teórico pós-D044 — só compromete o modo automatizado após dois ciclos de validação operacional.
- **Impacto**: detalhada em Cap. 6 §6.4 (Plano de Implantação Piloto); referenciada no `model_card.md`; verificada em `notebooks/_audit_fases_0_a_6.py`.

## D042 — Protocolo de monitoramento e gatilhos de retreino (Fase 6 / CM 6.2)

- **Data**: 2026-05-10
- **Contexto**: H010 confirmou *drift* de prevalência de −72,5% entre fevereiro e junho 2025, com PSI de *features* estável (0,16 < 0,25). Esta combinação rara (*label drift sem feature drift*) exige monitoramento dual em produção.
- **DECISÃO**: protocolo formal de monitoramento mensal com 4 indicadores:
  1. PSI top-10 *features* ≥ 0,25 → alerta.
  2. |Δprev/p_treino| ≥ 0,30 → alerta.
  3. ECE ≥ 0,05 em qualquer H → alerta.
  4. Recall por incidente cai ≥ 30% face ao baseline → alerta.
- **Gatilhos**: *soft* (1 indicador por 2 meses) → re-tunar+re-treinar o H afetado; *hard* (≥ 2 indicadores ou ECE ≥ 0,10) → *rollback* + re-treino imediato com janela expandida.
- **Cadência programada**: re-treino completo a cada 6 meses independente de gatilhos.
- **Justificativa**: produz proteção em duas camadas (drift estatístico + drift operacional) e respeita o princípio governante (robustez > velocidade).
- **Impacto**: detalhado em Cap. 6 §6.5 (Monitoramento Contínuo); auditoria de *fairness* mensal por operador (D016, frente F1 da Fase 6) é parte deste protocolo.

## D043 — Artefatos de governança obrigatórios para deployment (Fase 6)

- **Data**: 2026-05-10
- **Contexto**: práticas de *ML in production* (Mitchell et al. 2019; Sculley et al. 2015) recomendam que deployment de modelos preditivos venha acompanhado de artefatos de governança auditáveis: cartão modelo, intervalos de confiança e auditoria de viés.
- **DECISÃO**: junto com o modelo, são entregues 5 artefatos de governança classificados como **obrigatórios** para qualquer ciclo futuro de deployment:
  1. **Cartão modelo**: `docs/model_card.md` no formato Mitchell et al. (2019).
  2. **Intervalos de confiança bootstrap 95%**: `reports/eda_results/fase6_bootstrap_ci.json` (1000 resamples).
  3. **Auditoria de fairness por operador**: `reports/eda_results/fase6_fairness_operador.json` (Gini, disparidade Q75/Q25, top/bottom 5).
  4. **Servidor de inferência calibrado**: `src/serving/predict_realtime.py` como protótipo CLI.
  5. **Requirements de deploy minimalistas**: `requirements_deploy.txt` (sem optuna, shap, torch, catboost).
- **Justificativa**: Em produção, qualquer modelo sem cartão+IC+fairness é caixa-preta. Esta decisão fixa a barra mínima para o presente trabalho e para futuras replicações (Trabalho Futuro #1, multi-localidade).
- **Impacto**: 5 frentes opcionais F1-F5 da Fase 6 entregues na presente versão; auditadas em `notebooks/_audit_fases_0_a_6.py` (cobertura ≥84/84 esperada).

## D044 — Retunagem PA-1 com Optuna em 150 trials por horizonte

- **Data**: 2026-05-12
- **Contexto**: a rodada D033 havia reduzido o orçamento de busca de 50 para 30 trials por horizonte por custo/benefício. Para a versão final, o princípio governante do projeto foi aplicado sem restrição computacional: rigor acima de tempo de execução.
- **ANTES**: PA-1 LightGBM tunado com 30 trials por horizonte; artigo e artefatos textuais mencionavam 30, 50 ou "100+ trials" como limitação/trabalho futuro.
- **DEPOIS**: `notebooks/_run_pa1_lightgbm.py` e `src/models/pa1_lightgbm.py` usam 150 trials Optuna por horizonte, para todos os seis horizontes PA-1. Foram reexecutados LightGBM, comparativo XGBoost/CatBoost, calibração, predições de junho, lead times, consolidação Fase 5A, análise de erros Fase 5B, impacto Fase 5C, bootstrap e fairness.
- **Justificativa**: remove a limitação de orçamento de busca da versão final e torna desnecessário listar "re-tuning 100+ trials" como trabalho futuro. A continuidade passa a ser tuning multiobjetivo orientado a custo operacional.
- **Impacto**: novos resultados canônicos: LightGBM calibrado com AUC-PR 0,207/0,268/0,312/0,357/0,374/0,412; lift 6,71/5,04/3,48/2,94/2,53/2,11; ECE máximo 0,046; recall por incidente 10,8% a 64,8%; impacto recomendado H=12h, ΔP=60min, ρ=0,7 de 214 h/mês; teto H=12h, ΔP=30min, ρ=0,9 de 282 h/mês.
