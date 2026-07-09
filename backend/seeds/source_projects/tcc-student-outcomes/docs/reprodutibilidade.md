# Reprodutibilidade do projeto

Levantamento feito em 2026-05-11 no workspace `D:\TCC - versão final`.

## Versao do codigo

- Git HEAD: `5af00e52082c1b2c68c16b51e0a8d6d02651d573`
- Commit curto: `5af00e5`
- Data do commit: `2026-05-10 17:29:45 -0300`
- Mensagem: `files upload`
- `git status --short` estava limpo durante este levantamento.

## Ambiente de execucao observado

- Sistema: `Windows-11-10.0.26200-SP0`
- Processador reportado: `Intel64 Family 6 Model 183 Stepping 1, GenuineIntel`
- Python: `3.13.7` 64-bit, MSC v.1944
- Executavel Python: `C:\Users\DiegoHenriqueXavier\AppData\Local\Programs\Python\Python313\python.exe`
- pip: `26.0.1`
- Nao foi encontrado `requirements.txt`, `pyproject.toml` ou ambiente virtual versionado. Para reproducao estrita, congele este ambiente.

Versoes das bibliotecas no ambiente atual:

```text
pandas==2.3.3
numpy==2.3.3
scikit-learn==1.7.2
optuna==4.8.0
xgboost==3.2.0
catboost==1.2.10
plotly==6.6.0
kaleido==1.2.0
shap==0.51.0
scipy==1.16.3
matplotlib==3.10.7
seaborn==0.13.2
joblib==1.5.2
pyarrow==23.0.1
openpyxl==3.1.5
statsmodels==0.14.6
```

## Ordem de execucao dos scripts

Ordem inferida pelos artefatos consumidos e produzidos:

```powershell
python src\preprocessamento\nb01_consolidacao_padronizacao.py
python src\preprocessamento\nb02_alvo_e_coorte.py
python src\preprocessamento\nb03_feature_engineering.py
python src\preprocessamento\nb04_split_temporal.py
python src\modelagem\nb06_pipeline_e_baselines.py
python src\modelagem\nb07_modelos_optuna.py
python src\modelagem\nb08_threshold_calibracao.py
python src\modelagem\nb09_shap_erro_robustez.py
python src\modelagem\gerar_roc_teste.py
python src\modelagem\gerar_todas_figuras_artigo.py
python scripts\generate_plotly_theory_figures.py
```

Para os artefatos em ingles:

```powershell
python src\modelagem\gerar_todas_figuras_artigo_en.py
python scripts\generate_missing_english_assets.py
python scripts\translate_article_to_en.py
```

## Seeds e aleatoriedade

Constantes em `src/modelagem/config_modelagem.py`:

- `SEED = 42`
- `OPTUNA_TRIALS = 150`
- `N_BOOTSTRAP = 5000`
- `JANELAS = [1, 2, 4]`

Usos relevantes:

- Optuna: `TPESampler(seed=SEED)` em todos os estudos.
- Logistic Regression: `random_state=SEED`.
- Random Forest: `random_state=SEED`, `n_jobs=-1`.
- XGBoost: `random_state=SEED`, `n_jobs=-1`.
- CatBoost: `random_seed=SEED`.
- MLP: `random_state=SEED`, com reamostragem ponderada usando `np.random.RandomState(SEED)`.
- Bootstrap: `np.random.RandomState(SEED)`, `N_BOOTSTRAP=5000`.
- SHAP/curvas auxiliares: subamostras com `np.random.RandomState(SEED)`.
- O script de consolidacao tambem define `SEED = 42`, mas nao usa sorteio relevante nessa etapa.

Pontos de nao determinismo residual:

- `PYTHONHASHSEED` nao estava definido no ambiente.
- RF/XGBoost usam paralelismo (`n_jobs=-1`), podendo gerar pequenas diferencas entre plataformas/versoes.
- CatBoost tambem pode variar levemente com versao, CPU e threads.

## Fontes de dados e criterios de preprocessamento

Arquivos brutos consumidos:

- `data/raw/ADM_Integral/Registros_ADM_Integral.xlsx`
- `data/raw/ADM_Noturno/Registros_ADM_Noturno.xlsx`
- `data/raw/GI/Registros_GI.xlsx`
- `data/raw/11.02.02.80.04_Alunos-Evadidos_Curso-Ano_(ADM-Int-Not_GI)_1965-2025.xlsx`, aba `relatorio`

Consolidacao e padronizacao (`nb01_consolidacao_padronizacao.py`):

- Adiciona `curso_origem` por arquivo.
- Remove colunas tratadas como leakage quando presentes:
  `data_diploma`, `formado`, `tem_data_diploma`, `nota_valida`, `ch_total_integralizada`, `dilacao_semestres`, `enade_status`.
- Anonimiza matricula com SHA-256: `sha256(f"{salt}_{matricula}")[:16]`.
  O salt fixo esta no codigo (`SALT_ANONIMIZACAO = "tcc_ufu_2026_dxavier"`). Nao publicar esse salt junto de dados brutos identificaveis.
- Remove `matricula` e `nome`.
- Corrige encoding das colunas cadastrais `SEXO`, `FORMA_INGRESSO`, `MODALIDADE_INGRESSO`, `NATURALIDADE`.
- `sexo`: `Masculino -> M`, `Feminino -> F`.
- `idade_ingresso`: `(INGRESSO_DATA - ALUNO_NASCIMENTO).days / 365.25`, arredondada para 1 casa; valores `<15` ou `>70` viram nulos.
- `forma_ingresso_grp`: grupos `Vestibular`, `SISU`, `PAIES_PAAES`, `Transferencia`, `Portador_Diploma`, `Outros`.
- `cotista`: ampla concorrencia/AC -> 0; modalidades/codigos `LI`/`LB` -> 1; demais -> nulo.
- `natural_uberlandia`: 1 se naturalidade contem `uberlândia`/`uberlandia`, senao 0.
- Dados cadastrais sao deduplicados por `id_aluno`, `keep="last"`.
- Situacoes de aluno mantidas e alvo posterior:
  `Formado`, `Abandono`, `Desistente`, `Jubilamento`, `Desligamento`.
- Situacoes excluidas:
  transferencia interna/migracao/transferido, falecimento, cancelamentos de convenio/matricula/renda, ingressante nao compareceu.
- Situacoes de disciplina sao padronizadas e agrupadas em:
  `aprovado`, `reprovado`, `dispensa`, `sem_resultado`.
- Texto normalizado com `strip`, Unicode NFC e espacos colapsados.
- Duplicatas removidas pelo subconjunto:
  `id_aluno`, `semestre_disciplina`, `codigo_disciplina`, `nome_disciplina`, `carga_horaria`, `nota`, `situacao_disciplina`.
- `ano_disciplina` e `num_semestre_disc` sao extraidos por regex do texto de semestre.
- `periodo_sequencial` e calculado por aluno a partir dos semestres validos ordenados por ano/semestre.
- `num_semestre_ingresso` e extraido por regex de `semestre_ingresso`.
- Saida: `data/preprocessamento/base_consolidada_granular.parquet`.

Alvo e coortes (`nb02_alvo_e_coorte.py`):

- `Formado -> y=0`.
- `Abandono`, `Desistente`, `Jubilamento`, `Desligamento -> y=1`.
- `max_periodo`: maximo `periodo_sequencial` por aluno; nulos viram 0.
- p1: todos os alunos no ingresso.
- p2: alunos com `max_periodo >= 2`; disciplinas com `periodo_sequencial <= 2`.
- p4: alunos com `max_periodo >= 4`; disciplinas com `periodo_sequencial <= 4`.
- Saidas principais: `alunos_p1/p2/p4.parquet`, `coorte_p2.parquet`, `coorte_p4.parquet`.

Feature engineering (`nb03_feature_engineering.py`):

- p1 usa apenas variaveis cadastrais/ingresso.
- p2/p4 agregam registros de disciplinas ate a janela:
  `nota_media`, `nota_mediana`, `nota_desvio`, `nota_min`, `nota_max`;
  contagens de aprovacao/reprovacao/dispensa/sem resultado;
  reprovacao por nota/frequencia;
  `taxa_aprovacao`;
  `qtd_disciplinas_total`;
  `media_disc_por_periodo`;
  `ch_acumulada`;
  `nota_p1`;
  `delta_nota`;
  `reprov_p1`;
  `disc_p1`;
  `pct_ch_concluida = ch_acumulada / ch_total_exigida`.
- Contagens sem ocorrencia viram 0.
- Variaveis numericas continuas com ausencia permanecem nulas ate a imputacao no pipeline de modelagem.
- Saidas: `ml_p1.parquet`, `ml_p2.parquet`, `ml_p4.parquet`.

Split temporal (`nb04_split_temporal.py`):

- Exclui `ano_ingresso >= 2020`.
- Treino: `ano_ingresso <= 2015`.
- Validacao: `2016 <= ano_ingresso <= 2017`.
- Teste: `2018 <= ano_ingresso <= 2019`.
- Saidas: `treino_p*.parquet`, `val_p*.parquet`, `teste_p*.parquet`.

Tamanhos finais dos splits:

| Janela | Split | n | y=0 | y=1 | Evasao | Ano min-max |
|---|---:|---:|---:|---:|---:|---|
| p1 | treino | 4160 | 2551 | 1609 | 38.68% | 1968-2015 |
| p1 | val | 450 | 212 | 238 | 52.89% | 2016-2017 |
| p1 | teste | 381 | 161 | 220 | 57.74% | 2018-2019 |
| p2 | treino | 4033 | 2551 | 1482 | 36.75% | 1968-2015 |
| p2 | val | 436 | 212 | 224 | 51.38% | 2016-2017 |
| p2 | teste | 364 | 161 | 203 | 55.77% | 2018-2019 |
| p4 | treino | 3880 | 2551 | 1329 | 34.25% | 1968-2015 |
| p4 | val | 420 | 212 | 208 | 49.52% | 2016-2017 |
| p4 | teste | 340 | 160 | 180 | 52.94% | 2018-2019 |

## Features usadas na modelagem

p1:

- Categoricas: `curso_origem`, `tipo_ingresso`, `sexo`, `forma_ingresso_grp`.
- Numericas: `idade_ingresso`, `cotista`, `natural_uberlandia`, `num_semestre_ingresso`.

p2 e p4:

- Categoricas: `curso_origem`, `tipo_ingresso`, `sexo`, `forma_ingresso_grp`.
- Numericas: `nota_media`, `nota_mediana`, `nota_desvio`, `nota_min`, `nota_max`,
  `qtd_aprovacoes`, `qtd_reprovacoes`, `qtd_dispensas`, `qtd_sem_resultado`,
  `qtd_reprov_nota`, `qtd_reprov_freq`, `taxa_aprovacao`,
  `qtd_disciplinas_total`, `media_disc_por_periodo`, `ch_acumulada`,
  `nota_p1`, `delta_nota`, `reprov_p1`, `disc_p1`, `pct_ch_concluida`,
  `idade_ingresso`, `cotista`, `natural_uberlandia`.

## Pipelines de modelagem

Preprocessamento salvo por janela em `src/modelagem/resultados/preprocessor_*_p*.joblib`.

Pipeline `scaled`, usado por LR e MLP:

- Numericas: `SimpleImputer(strategy="median")` + `StandardScaler()`.
- Categoricas: `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)`.
- `remainder="drop"`.

Pipeline `tree`, usado por RF e XGBoost:

- Numericas: `SimpleImputer(strategy="median")`.
- Categoricas: `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)`.
- `remainder="drop"`.

CatBoost:

- Recebe o `DataFrame` bruto das features selecionadas, com `cat_features` por indice.

Desbalanceamento:

- LR: `class_weight="balanced"`.
- RF: `class_weight="balanced"`.
- XGBoost: `scale_pos_weight = n_neg / n_pos`.
- CatBoost: `auto_class_weights="Balanced"`.
- MLP: `compute_sample_weight("balanced", y_treino)` e reamostragem com reposicao usando `RandomState(42)`.
- Nao ha SMOTE nos scripts de modelagem finais.

`scale_pos_weight` final:

- p1: `1.5854568054692355`
- p2: `1.7213225371120109`
- p4: `1.9194883370955607`

## Optuna: funcao objetivo e search spaces

Todos os estudos:

- `direction="maximize"`
- `sampler=optuna.samplers.TPESampler(seed=42)`
- `n_trials=150`
- Funcao objetivo: `F2` na validacao com threshold padrao `0.5`.

LR:

- `C`: `suggest_float("C", 1e-2, 100, log=True)`
- `penalty`: `suggest_categorical("penalty", ["l1", "l2"])`
- `solver`: `saga` se `l1`, senao `lbfgs`
- fixos: `class_weight="balanced"`, `max_iter=2000`, `random_state=42`

RF:

- `n_estimators`: `100..800`, passo `50`
- `max_depth`: `3..20`
- `min_samples_split`: `2..30`
- `min_samples_leaf`: `1..20`
- `max_features`: `["sqrt", "log2", 0.3, 0.5, 0.7]`
- fixos: `class_weight="balanced"`, `random_state=42`, `n_jobs=-1`

XGBoost:

- `n_estimators`: `100..800`, passo `50`
- `max_depth`: `3..12`
- `learning_rate`: `0.01..0.3`, log
- `subsample`: `0.5..1.0`
- `colsample_bytree`: `0.3..1.0`
- `min_child_weight`: `1..20`
- `reg_alpha`: `1e-8..10`, log
- `reg_lambda`: `1e-8..10`, log
- `gamma`: `1e-8..5`, log
- fixos: `scale_pos_weight`, `random_state=42`, `eval_metric="logloss"`, `n_jobs=-1`

CatBoost:

- `iterations`: `100..800`, passo `50`
- `depth`: `3..10`
- `learning_rate`: `0.01..0.3`, log
- `l2_leaf_reg`: `1e-2..10`, log
- `bagging_temperature`: `0..5`
- `random_strength`: `0.1..10`, log
- fixos: `auto_class_weights="Balanced"`, `random_seed=42`, `verbose=0`, `cat_features`

MLP:

- `n_layers`: `1..3`
- `n_units_i`: `16..128`, passo `16`, para cada camada
- `activation`: `["relu", "tanh"]`
- `alpha`: `1e-5..1e-1`, log
- `learning_rate_init`: `1e-4..1e-2`, log
- `batch_size`: `[32, 64, 128]`
- fixos: `max_iter=500`, `early_stopping=True`, `validation_fraction=0.15`, `random_state=42`

## Hiperparametros finais

Parametros otimos salvos em `melhores_modelos_p*.joblib` e estudos em `estudos_optuna_p*.joblib`.

### p1

- LR: `C=2.481040974867813`, `penalty="l1"`, `solver="saga"`.
- RF: `n_estimators=450`, `max_depth=7`, `min_samples_split=14`, `min_samples_leaf=20`, `max_features=0.3`.
- XGBoost: `n_estimators=150`, `max_depth=4`, `learning_rate=0.01059428998750912`, `subsample=0.9781650724308198`, `colsample_bytree=0.3151578862007609`, `min_child_weight=20`, `reg_alpha=2.867613794497486`, `reg_lambda=0.002094674743907601`, `gamma=1.186471440474477e-05`, `scale_pos_weight=1.5854568054692355`.
- CatBoost: `iterations=200`, `depth=3`, `learning_rate=0.013161227807190765`, `l2_leaf_reg=0.22365806333500168`, `bagging_temperature=3.5682999069611356`, `random_strength=8.61316599158533`.
- MLP: `hidden_layer_sizes=(112,)`, `activation="relu"`, `alpha=0.05319275804742567`, `learning_rate_init=0.0001411892817578801`, `batch_size=128`.

### p2

- LR: `C=0.17594678649531834`, `penalty="l1"`, `solver="saga"`.
- RF: `n_estimators=400`, `max_depth=20`, `min_samples_split=28`, `min_samples_leaf=17`, `max_features="sqrt"`.
- XGBoost: `n_estimators=100`, `max_depth=4`, `learning_rate=0.05720690315035899`, `subsample=0.5989628195058954`, `colsample_bytree=0.6386883125842427`, `min_child_weight=17`, `reg_alpha=3.759774054433333e-07`, `reg_lambda=1.3827423920130038`, `gamma=4.248497284400524e-06`, `scale_pos_weight=1.7213225371120109`.
- CatBoost: `iterations=500`, `depth=7`, `learning_rate=0.06426749552471313`, `l2_leaf_reg=5.5988708872472`, `bagging_temperature=1.178380211208532`, `random_strength=1.2295852135862932`.
- MLP: `hidden_layer_sizes=(96,)`, `activation="tanh"`, `alpha=0.013741702501490285`, `learning_rate_init=0.0007535066874479521`, `batch_size=32`.

### p4

- LR: `C=0.012133085742908773`, `penalty="l2"`, `solver="lbfgs"`.
- RF: `n_estimators=550`, `max_depth=12`, `min_samples_split=25`, `min_samples_leaf=8`, `max_features=0.3`.
- XGBoost: `n_estimators=400`, `max_depth=3`, `learning_rate=0.04073240253788198`, `subsample=0.9700035098229814`, `colsample_bytree=0.7900250011312688`, `min_child_weight=17`, `reg_alpha=1.2254117483236326`, `reg_lambda=0.004704966269446811`, `gamma=0.002421001468049282`, `scale_pos_weight=1.9194883370955607`.
- CatBoost: `iterations=450`, `depth=4`, `learning_rate=0.016260805723060594`, `l2_leaf_reg=0.7786576242665619`, `bagging_temperature=0.3951140860607368`, `random_strength=8.62874877188591`.
- MLP: `hidden_layer_sizes=(128,)`, `activation="tanh"`, `alpha=0.0003544699834410658`, `learning_rate_init=0.0007842688695583152`, `batch_size=32`.

Fixos aplicados alem dos parametros acima:

- LR: `class_weight="balanced"`, `max_iter=2000`, `random_state=42`.
- RF: `class_weight="balanced"`, `random_state=42`, `n_jobs=-1`.
- XGBoost: `random_state=42`, `eval_metric="logloss"`, `n_jobs=-1`.
- CatBoost: `auto_class_weights="Balanced"`, `random_seed=42`, `verbose=0`, `cat_features`.
- MLP: `max_iter=500`, `early_stopping=True`, `validation_fraction=0.15`, `random_state=42`.

## Thresholds finais

Busca exaustiva em validacao:

- `np.arange(0.10, 0.90, 0.01)`
- criterio: maximizar `F2`.
- threshold encontrado na validacao e aplicado diretamente ao teste.

| Janela | LR | RF | XGBoost | CatBoost | MLP |
|---|---:|---:|---:|---:|---:|
| p1 | 0.24 | 0.10 | 0.46 | 0.50 | 0.10 |
| p2 | 0.33 | 0.40 | 0.35 | 0.30 | 0.41 |
| p4 | 0.33 | 0.29 | 0.25 | 0.30 | 0.44 |

Modelos selecionados por maior `F2` na validacao com threshold otimizado:

- p1: `CatBoost`, `F2_val=0.854978354978355`, `threshold=0.50`
- p2: `XGBoost`, `F2_val=0.8899398108340498`, `threshold=0.35`
- p4: `CatBoost`, `F2_val=0.9132841328413284`, `threshold=0.30`

## Resultados finais de teste

Metricas em `src/modelagem/resultados/resultados_threshold_teste.csv`.

Melhor `F2` observado no teste por janela:

- p1: LR, `F2=0.8757961783439491`, `AUC=0.7058865047995482`, `recall=1.0`, `precision=0.5851063829787234`.
- p2: LR, `F2=0.9001865671641791`, `AUC=0.916133769849769`, `recall=0.9507389162561576`, `precision=0.7423076923076923`.
- p4: LR, `F2=0.9200841219768664`, `AUC=0.9498958333333334`, `recall=0.9722222222222222`, `precision=0.7575757575757576`.

Observacao: a selecao metodologica do artigo foi feita pelo desempenho na validacao, resultando em CatBoost p1, XGBoost p2 e CatBoost p4. A ordenacao acima e apenas o ranking observado no teste.

## Artefatos salvos

Modelos e preprocessadores:

- `src/modelagem/resultados/preprocessor_scaled_p*.joblib`
- `src/modelagem/resultados/preprocessor_tree_p*.joblib`
- `src/modelagem/resultados/modelo_{LR,RF,XGBoost,CatBoost,MLP}_p*.joblib`
- `src/modelagem/resultados/melhores_modelos_p*.joblib`
- `src/modelagem/resultados/estudos_optuna_p*.joblib`
- `src/modelagem/resultados/thresholds_otimos_p*.joblib`
- `src/modelagem/resultados/modelos_calibrados_p*.joblib`
- `src/modelagem/resultados/dados_preparados_p*.npz`

Resultados tabulares:

- `src/modelagem/resultados/resultados_baselines.csv`
- `src/modelagem/resultados/resultados_todos_modelos.csv`
- `src/modelagem/resultados/resultados_threshold_teste.csv`
- `src/auditoria/auditoria_vazamento.csv`
- `src/eda/graficos/sociodemografico_resumo.csv`

## Figuras e tabelas do artigo

Script principal em portugues:

- `src/modelagem/gerar_todas_figuras_artigo.py`
- Saida: `article/Images/artigo/*.png` e `*.html`
- Modelos destacados no script: `{1: "CatBoost", 2: "XGBoost", 4: "CatBoost"}`

Figuras geradas pelo script principal:

- `fig_evasao_por_curso`
- `fig_split_temporal_p1`, `fig_split_temporal_p2`, `fig_split_temporal_p4`
- `fig_medianas_p1`, `fig_medianas_p2`, `fig_medianas_p4`
- `fig_forest_plot_p1`, `fig_forest_plot_p2`, `fig_forest_plot_p4`
- `fig_tabela_comparativa_teste`
- `fig_precision_recall_tradeoff`
- `fig_matrizes_confusao`
- `fig_equity_curso_p1`, `fig_equity_curso_p2`, `fig_equity_curso_p4`
- `fig_shap_bar_p1`, `fig_shap_bar_p2`, `fig_shap_bar_p4`
- `fig_bootstrap_ci_p1`, `fig_bootstrap_ci_p2`, `fig_bootstrap_ci_p4`
- `fig_psi_drift`
- `fig_calibracao_teste`
- `fig_evolucao_temporal_evasao`
- `fig_estabilidade_walkforward`
- `fig_learning_curve`
- `fig_ablation_study`
- `fig_pr_curves_teste`

Scripts auxiliares:

- `src/modelagem/gerar_roc_teste.py`: curvas ROC de teste `roc_teste_p*.png/html`.
- `src/modelagem/regen_confusao.py`: regenera apenas `fig_matrizes_confusao`.
- `src/modelagem/gerar_figuras_p1_e_forest_fix.py`: ajustes especificos de p1/forest plot.
- `scripts/generate_plotly_theory_figures.py`: figuras teoricas de matriz de confusao e ROC.
- `scripts/generate_missing_english_assets.py`: ativos ausentes em ingles e copias/adaptacoes.
- `src/modelagem/gerar_todas_figuras_artigo_en.py`: versao em ingles das figuras do artigo.

Tabelas LaTeX:

- As tabelas principais em `article/TCC_Evasao.tex` estao embutidas manualmente no arquivo `.tex`.
- As bases tabulares mais importantes para regeneracao sao:
  `resultados_todos_modelos.csv` para validacao com threshold 0.5 e
  `resultados_threshold_teste.csv` para validacao/teste com threshold otimizado.
- Nao foi encontrado um script unico que regenere automaticamente todas as tabelas LaTeX do artigo a partir dos CSVs.

## Informacoes importantes para reprodutibilidade

- A validacao (2016-2017) e usada para tres etapas: Optuna, ajuste de threshold e calibracao sigmoid (`CalibratedClassifierCV(..., cv="prefit")`). O teste (2018-2019) e usado apenas para avaliacao final.
- Dados de 2020 em diante sao excluidos por regra fixa antes do split.
- O estudo armazena os objetos Optuna em `.joblib`, permitindo auditar trials e parametros sem rerodar a busca.
- O projeto depende de `kaleido` para exportar Plotly para PNG.
- Para reproducao externa, recomenda-se adicionar um `requirements.txt`/`environment.yml` e registrar threads (`OMP_NUM_THREADS`, `MKL_NUM_THREADS`) caso seja necessario reduzir variacao numerica.
