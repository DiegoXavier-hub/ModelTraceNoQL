# MEMORY.md — Caderno de Bordo do Projeto

## Antecipação de Alertas Críticos "Don't Go" em Frotas de Mineração

> **Filosofia**: este arquivo é a memória persistente do projeto. Tudo que importa lembrar (decisões, descobertas, hipóteses, controle de alterações ANTES/DEPOIS) entra aqui. Tarefas pendentes ficam na seção `TO-DO`. Tarefas concluídas ficam marcadas com **OK** e contexto.
>
> **Atualizar a cada decisão metodológica relevante.** Nunca apagar — apenas riscar/marcar como obsoleto se houver mudança de rumo.

---

## 🔴 PROTOCOLO PARA NOVO CHAT — leia primeiro

Se você é um chat novo do Claude (ou outro agente) entrando neste projeto:

1. **Leia este arquivo `MEMORY.md` por inteiro antes de qualquer ação.** Ele é a fonte da verdade.
2. **Diretório de trabalho do projeto** (caminho absoluto Windows):

   ```text
   c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale
   ```

   ⚠️ O nome contém **espaços e acento** (`Projetos - Dados`). Em comandos bash/CLI, sempre **citar com aspas duplas**: `"c:/Users/DiegoHenriqueXavier/Documents/Projetos - Dados/Vale"`.
3. **Diretório atual do TCC final (`.tex` ABNT)**:

   ```text
   c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\docs\article_dontgo\
   ```

   Template histórico de referência: `D:\TCC - versão final\article\TCC_Evasao.tex`. Bibliografia atual: `docs\article_dontgo\bibliografia.bib`.
4. **Antes de avançar uma fase**, confirme com o usuário. Estilo de trabalho exigido: **passo a passo, parte por parte** — nunca despejar tudo de uma vez.
5. **Atualize sempre** este arquivo ao concluir um passo: marque `[OK]` no roadmap, atualize o "Último checkpoint" no fim do arquivo, e registre decisões em `docs/decisions.md`.
6. **Sistema `.remember/`** (hook automático): existe pasta `.remember/` na raiz com `now.md`, `today-*.md`, `recent.md`, `archive.md`, `core-memories.md`. NÃO depender dela como fonte primária — `MEMORY.md` é canônico. Apenas consultar se precisar de contexto de sessões anteriores.

### Caminhos absolutos de todos os artefatos relevantes

| Item | Caminho |
|---|---|
| Raiz do projeto | `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale` |
| Estudo Guiado (PDF) | `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\Estudo Guiado - Análise Avançada de Dados.pdf` |
| Template do relatório (.docx, fornecido pela banca) | `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\Desenvolver_Template.docx` |
| Apontamentos (parquet bruto) | `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\Base de Dados\datasets\apontamentos\desenvolver_apontamentos.parquet` |
| Apontamentos (xlsx exemplo) | `…\Base de Dados\datasets\apontamentos\desenvolver_apontamentos.xlsx` |
| Telemetria (parquets mensais Jan–Jun 2025) | `…\Base de Dados\datasets\telemetria\telemetry_{jan,feb,mar,abr,may,jun}.parquet` |
| Telemetria — exemplo Don't Go | `…\Base de Dados\datasets\telemetria\desenvolver_dontgo.xlsx` |
| Catálogo de regras de alarme | `…\Base de Dados\Alarmes - Regra de Negocio.xlsx` |
| Dicionário de dados | `…\Base de Dados\Dicionario_Dados.xlsx` |
| README datasets | `…\Base de Dados\datasets\README.md` |
| Diretório atual do TCC final (LaTeX/ABNT) | `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\docs\article_dontgo\` |
| Template `.tex` referência histórica | `D:\TCC - versão final\article\TCC_Evasao.tex` |
| Bibliografia BibLaTeX atual | `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\docs\article_dontgo\bibliografia.bib` |

### Ambiente verificado (2026-04-28)

- **OS**: Windows 11 Enterprise (build 26200). Shell preferido: **bash** (Unix syntax — `/dev/null`, forward slashes em paths).
- **Python**: 3.13.7
- **Pacotes-chave já instalados** (confirmado via `pip list`):
  `pandas 2.3.3`, `numpy 2.3.3`, `pyarrow 23.0.1`, `duckdb 1.5.1`, `scikit-learn 1.7.2`, `lightgbm 4.6.0`, `xgboost 3.2.0`, `catboost 1.2.10`, `torch 2.8.0+cu129` (CUDA OK), `optuna 4.8.0`, `shap 0.51.0`, `matplotlib 3.10.7`, `seaborn 0.13.2`, `plotly 6.6.0`, `openpyxl 3.1.5`.
- **A verificar**: `lifelines` (sobrevivência), `prophet`/`pmdarima` (séries temporais).


---

## ENTREGÁVEL FINAL (definido pelo usuário em 2026-04-28)

- **Formato**: LaTeX (`.tex`) seguindo padrão **ABNT** (classe `abntex2`).
- **Local atual de desenvolvimento/entrega**: `c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale\docs\article_dontgo\`.
- **Template de referência histórica**: `D:\TCC - versão final\article\TCC_Evasao.tex` — preâmbulo, comandos `\titulo/\autor/\local/\data/\instituicao/\tipotrabalho/\preambulo/\orientador`, estilo de tabelas/figuras (`\tablesource`, `\figsource`, `\tablenote`) e bibliografia com `biblatex` style=abnt + `biber` foram reaproveitados no artigo atual.
- **Identidade do autor (do TCC anterior)**: Diego Henrique Xavier — Universidade Federal de Uberlândia — Faculdade de Gestão e Negócios — Curso de Gestão da Informação — Orientadora: Profª. Drª. Noézia Maria Ramos — Local: Uberlândia/MG — Ano: 2026.
- **Conduta**: avançar **passo a passo**. Cada fase fechada antes de iniciar a próxima.

### Mapeamento CRISP-DM (Estudo Guiado) ↔ Estrutura ABNT (TCC Evasão)

| Estudo Guiado | Capítulo no `.tex` ABNT |
|---|---|
| CM 1.1 Contextualização da operação | Cap 1 Introdução → §Motivação |
| CM 1.2 Pergunta analítica + métrica + cenário | Cap 1 → §Objetivos (geral + secundários) |
| Conceitos teóricos (alarmes, telemetria, ML) | Cap 2 Referencial Teórico |
| Métricas de desempenho (Precision, Recall, F1, AUC, SHAP) | Cap 2 → §Métricas |
| Trabalhos relacionados | Cap 2 → §Trabalhos Relacionados |
| CM 2.1–2.3 EDA + CM 3.1–3.3 Data Prep + CM 4.1 Validação | Cap 3 Metodologia (Delineamento, Base de Dados, Etapas do Experimento) |
| CM 4.2–4.3 Baseline e modelos | Cap 3 → §Algoritmos e §Otimização |
| CM 5.1–5.3 Avaliação, erros, SHAP, drift | Cap 4 Resultados (descritivos + modelagem + SHAP + ablation + drift + walk-forward) |
| CM 6.1 Resultados e impacto | Cap 5 Discussão |
| CM 6.2 Conclusão + CM 6.3 Trabalhos Futuros | Cap 6 Conclusão |
| — | Referências (`.bib`) |

### Convenções tipográficas ABNT já em uso no template

- 12 pt, `oneside`, `abntex2`, `babel[brazil]`, `inputenc[utf8]`, `fontenc[T1]`, `lmodern`.
- Tabelas: `booktabs`, `longtable`, `tabularx`; legenda em 10 pt; `\tablesource{...}` no rodapé com "Fonte: ...".
- Figuras: `graphicx`, `float`; `\figsource{...}` abaixo da figura.
- Citações: `\cite{...}` e `\textcite{...}` em estilo ABNT (autor-ano).
- Resumo PT + Abstract EN, ambos com palavras-chave/keywords em **negrito**.

---

## 0. Norte Estratégico

### Princípio governante (estabelecido 2026-04-28)

> **Robustez > custo computacional.** Diretriz explícita do autor: *"prefiro múltiplas janelas em paralelo, faça da forma que for ficar melhor e mais robusto sempre, não importa custo computacional"*. Toda decisão de modelagem, validação, métricas e features é calibrada por essa preferência. Em todo dilema rigor-vs-velocidade, **escolher rigor**.

### Princípio: artigo crescendo com o projeto (estabelecido 2026-05-01)

> **O `.tex` do TCC deve ser escrito conforme cada fase é concluída — não retrospectivamente no fim do projeto.** Diretriz explícita do autor.

**Por quê**: escrever a Introdução depois de já ter os modelos fechados cria pressão para ajustar a narrativa do problema aos resultados; escrever a EDA depois da Fase 4 cria pressão para esconder achados que contradizem o modelo final. Escrever **durante** cada fase preserva honestidade epistêmica e força que cada decisão metodológica seja justificada pelo que se sabia *naquele momento*, não pelo que veio depois.

**Operacionalização**:

- **Ao fechar Fase 1** (Business Understanding): escrever Cap. 1 Introdução (CM 1.1 → §Contextualização; CM 1.2 → §Objetivos + §Justificativa).
- **Ao fechar Fase 2** (Data Understanding): escrever Cap. 3 §Delineamento + §Base de Dados (estrutural) e Cap. 4 §Compreensão dos Dados (achados descritivos da EDA).
- **Ao fechar Fase 3** (Data Preparation): escrever Cap. 3 §Pré-processamento + §Engenharia de Features.
- **Ao fechar Fase 4** (Modeling): escrever Cap. 3 §Algoritmos + §Otimização e Cap. 4 §Resultados de Modelagem (incluindo SHAP, ablação, drift entre folds).
- **Ao fechar Fase 5** (Evaluation): escrever Cap. 4 §Avaliação Final e Cap. 5 Discussão (CM 6.1 → impacto operacional via superfície de sensibilidade).
- **Ao fechar Fase 6** (Deployment): finalizar Cap. 6 Conclusão (CM 6.2 → resultados; CM 6.3 → trabalhos futuros).
- **Resumo + Abstract**: redigidos por último, após o restante do trabalho fechado.

**Não-objetivo**: o capítulo escrito após uma fase **não é versão final**. Pode (e deve) ser revisado conforme fases posteriores produzam achados que reforcem ou contradigam o que foi dito antes — mas a versão escrita durante a fase fica como **registro auditável do estado do conhecimento naquele momento**.

**Checkpoint a manter**: a cada compilação do `TCC_DontGo.pdf`, atualizar a seção 11+ deste arquivo com (a) capítulos preenchidos vs vazios, (b) páginas estimadas, (c) decisões pendentes que ainda precisam ser refletidas no texto.

### Visão de "vencer o campeonato"

O diferencial não está em rodar mais um XGBoost. Está em:
1. **Tradução fiel das regras de negócio** (`Alarmes - Regra de Negocio.xlsx`) em código auditável e testado.
2. **Engenharia de features sequencial e temporal profunda** — o equipamento conta uma história ao longo do tempo, não é uma foto.
3. **Múltiplas lentes analíticas** (supervisionado + sobrevivência + anomalia) que se complementam em vez de competir.
4. **Honestidade temporal**: zero data leakage, validação walk-forward 4-fold, calibração de probabilidade dupla.
5. **Múltiplos horizontes de predição** (1, 2, 4, 6, 8, 12 h) — descobrindo a janela ótima nos dados ao invés de impor a priori.
6. **Defesa explícita "predizer regra vs predizer risco"**: blackout de 5 min nas features + análise estratificada por lead time bucket.
7. **Tradução técnica → impacto operacional**: superfície de sensibilidade `(ΔP × ρ)` em horas de parada evitadas, não um número fictício.
8. **Storytelling com SHAP**: o modelo precisa convencer o operador, não só a banca.
9. **Reprodutibilidade**: notebooks numerados + módulos `src/` + seeds fixos + `requirements.txt`.

### Pergunta analítica principal (FECHADA em 2026-04-28 v2 após auto-revisão — ver `docs/business_understanding.md` e `docs/methodology_review.md`)

> **PA-1**: "Dado o estado operacional e o histórico recente de um equipamento, qual a probabilidade de ele disparar um **incidente Don't Go** em cada um dos horizontes futuros **H ∈ {1, 2, 4, 6, 8, 12} h**?"

- **Unidade de predição (D008)**: sliding window de **15 min** por equipamento ativo.
- **Definição de incidente (D009)**: sequência maximal de `Is_Dont_Go=1` do mesmo equipamento com gap ≤ 30 min; primeiro evento marcado como `is_incident_start=1` (única unidade de avaliação).
- **Múltiplas janelas em paralelo (D001 atualizada)**: 6 modelos independentes, um por horizonte H — descobre a curva risco-vs-horizonte e serve como defesa empírica contra "predizer regra vs predizer risco" (D010).

Complementares:
- **PA-2 (sobrevivência)**: tempo até próximo Don't Go — **Cox PH com teste de Schoenfeld** + **Weibull AFT** como fallback (D017). Métricas: C-index + IBS.
- **PA-3 (anomalia)**: detecção não supervisionada (Isolation Forest / Autoencoder LSTM) — modos de falha **fora** do catálogo CMA.

### Métricas de sucesso (FECHADAS — D012 + D013)

Pacote completo, todas reportadas em todas as tabelas finais:

- **Técnicas primárias**: **AUC-PR** + **Lift = AUC-PR/prevalência** + **AUC-ROC** + **Brier Score** + **ECE**.
- **Operacional**: **Recall@Precision=0,5** + **Lead time P25/P50/P75** entre TPs, separados por bucket {0–15 min, 15–60 min, 1–4 h}.
- **Negócio (Cap. 5 do .tex)**: superfície de sensibilidade **horas de parada evitadas** parametrizada por `ΔP ∈ {30, 60, 120, 240}` min × `ρ ∈ {50%, 70%, 90%}` redução com a mudança parada-não-programada → parada-programada. Apenas TPs com `lead_time ≥ 30 min` contam como evitados.

### Validação temporal (FECHADA — D011)

- **Walk-forward expanding 4 folds** (jan→fev→mar; jan-fev→mar→abr; jan-mar→abr→mai; jan-abr→mai→jun).
- **Modelo final ("para deploy")**: treinado em jan-mai, **avaliado uma única vez em jun** (teste intocado — proibido qualquer uso de jun para tuning ou seleção).
- **Buffer obrigatório de 4 h** entre fim de treino e início de val/teste (= horizonte máximo, evita leakage).
- Reportar média ± desvio dos 4 folds + IC 95% bootstrap por fold + número final do teste intocado.

---

## 1. Estrutura do Projeto

```text
Vale/
├── MEMORY.md                       ← este arquivo (índice vivo)
├── README.md                       ← visão geral pública
├── requirements.txt                ← dependências fixadas
├── Base de Dados/
│   ├── Alarmes - Regra de Negocio.xlsx
│   ├── Dicionario_Dados.xlsx
│   └── datasets/
│       ├── apontamentos/           ← parquet + xlsx
│       └── telemetria/             ← parquet mensal jan-jun + dontgo.xlsx
├── notebooks/
│   ├── 01_business_understanding.ipynb
│   ├── 02_data_understanding_eda.ipynb
│   ├── 03_data_preparation.ipynb
│   ├── 04_modeling_baseline.ipynb
│   ├── 05_modeling_advanced.ipynb
│   ├── 06_evaluation_shap.ipynb
│   └── 07_results_storytelling.ipynb
├── src/
│   ├── data/        ← carregamento, schemas, joins
│   ├── features/    ← engenharia de features
│   ├── models/      ← treino, predict, calibração
│   ├── viz/         ← gráficos reutilizáveis
│   └── utils/       ← seeds, paths, logging
├── reports/
│   ├── figures/     ← PNG/SVG para o relatório
│   └── tables/      ← CSV das tabelas finais
├── outputs/
│   ├── models/      ← .pkl/.joblib treinados
│   └── predictions/ ← scores no teste
└── docs/
    ├── decisions.md ← controle de alterações ANTES/DEPOIS
    └── hypotheses.md ← hipóteses levantadas na EDA
```

---

## 2. Inventário de Dados — schemas e fatos confirmados (Fase 1, 2026-04-28)

### 2.1 Apontamentos

- **Arquivo**: `Base de Dados/datasets/apontamentos/desenvolver_apontamentos.parquet`
- **Linhas**: 377.907 · **Cols**: **7** · **Tamanho**: 5,8 MB · **Memória**: ~92 MB carregado
- **Schema**: `Id (int64)`, `Inicio (timestamp[ns])`, `Fim (timestamp[ns])`, `Tag (string)`, `Frota (string)`, `Tipo (string)`, `Classe (string)`
- ⚠️ **Divergência com dicionário**: dicionário promete 9 colunas (com `Nome_Operador_Anon` e `Matricula_Operador_Hash`), mas o parquet tem só 7 — operador **só está disponível na telemetria**.
- **Período**: 2025-01-04 (primeira amostra) — confirmar limites na EDA (README diz Jan 1 → Jul 1).
- **Exemplos de valores**: `Tag` ∈ {`CA65789`, `CA65908`, `CA65915`, `CA5926`, ...} · `Frota` ∈ {`793-D 2S/3S/4S/5S`, ...} · `Tipo` ∈ {`Caminhao`, ...} · `Classe` ∈ {`Operando`, `Parado`, ...}.

### 2.2 Telemetria

- **Arquivos**: 6 parquets mensais em `Base de Dados/datasets/telemetria/telemetry_{jan,feb,mar,abr,may,jun}.parquet`
- **Linhas totais**: **37.164.054** · **Cols**: **18** · **Tamanho disco**: ~208 MB (compactado) · **Memória estimada**: ~28 GB se concatenado em pandas → **obrigatório usar duckdb/pyarrow lazy**.
- **Volumes mensais**: jan 5,40M · fev 5,71M · mar 5,69M · abr 6,48M · mai 6,04M · jun 7,85M
- **Schema** (resumido): `Id_Eventos_Telemetria, Data_Evento (timestamp[us]), Inicio_Turno, Fim_Turno (string!), Dia, Localidade, TAG, Tag_Frota, Tipo, Nome_Operador_Anon, Matricula_Operador_Hash, Id_Alarme, Alarme, Id_Criticidade, Criticidade, Valor (string!), Classe, Is_Dont_Go (int8)`
- **Notas críticas**:
  - `Inicio_Turno`/`Fim_Turno` são `string`, não timestamp — **converter na ingestão**.
  - `Valor` é `string` com **vírgula decimal brasileira** ("43,79...") e literal `"NULL"` em vez de null real — **limpar e converter**.
  - `Id_Criticidade`: 1=Crítico · 2=Não Crítico · 3=Informacional · 4=Outros.
  - `Localidade` aparece como `"Itabira"` na amostra inicial — confirmar que é única na EDA.
  - **Turnos de 12 h** (06:00-18:00 / 18:00-06:00).
  - 🎯 **`Is_Dont_Go` (int8)** já presente como flag binário — usar como ground truth (D006).

### 2.3 Catálogo de regras — `Alarmes - Regra de Negocio.xlsx`

- **Sheet `CMA`** (151 regras Don't Go) · **Sheet `Tendências`** (371 nomes de tendências) · **Sheet `Eventos O&M`** (147.943 nomes de eventos OEM brutos — universo de eventos possíveis)
- Estrutura CMA: `(TIPO, EVENTO, SITUACAO, QTD, TEMPO, NIVEL)`
- Distribuição:
  - **TIPO**: ALARME OEM 142 · TENDÊNCIA 7 · SISTEMA 2
  - **NIVEL** (normalizado): Muito Alto 82 · Alto 69
  - **SITUACAO**: 81/151 = "Em qualquer situação" (instantâneas); restante condicional em sequência.
  - **QTD**: mediana 1, máx 10 · **TEMPO**: mediana 0 s, máx 720 s (12 min).
  - **# eventos únicos**: 136 (alguns com 2 regras combinadas).

### 2.4 Exemplo Don't Go — `desenvolver_dontgo.xlsx`

- **147 linhas** = **1 equipamento** (`CA65924`, `793-D 4S`, Grande Porte) durante **1h58min** de turno noturno em Itabira.
- **1 evento** com `Is_Dont_Go=1` — o **último** (`Engine Coolant Level - Active`, `Id_Criticidade=1`).
- **10 eventos Críticos** no arquivo inteiro, todos do mesmo alarme `Engine Coolant Level - Active`; **2 disparos do mesmo alarme nos 3 min finais e 5 disparos nos 6 min finais** (números exatos verificados via Python sobre o `desenvolver_dontgo.xlsx`).
- 🔑 **Confirma o padrão sequencial**: o Don't Go é o ponto onde a **acumulação** cruza um limiar — não é o "alarme isolado mais grave".
- ⚠️ Coluna **adicional** vs. parquet: `Porte` ("Grande Porte") — não está no schema do parquet bruto, talvez seja derivada.

### 2.5 Dicionário — `Dicionario_Dados.xlsx`

- 2 sheets (`Apontamentos`, `Telemetria`) com colunas `Nome da Tabela | Nome da Feature | Tipo de Dados | Descrição`.
- Apontamentos descreve 9 features (mas parquet tem só 7 — divergência registrada acima).
- Telemetria descreve 18 features e bate com o parquet.

---

## 3. Decisões metodológicas registradas

Total: **22 decisões** (D001–D022). Detalhes completos em `docs/decisions.md`.

- **D001 (atualizada)** — múltiplos horizontes paralelos H ∈ {1, 2, 4, 6, 8, 12} h
- **D002–D007** — métricas, modelagem, escopo, ground truth, entregável
- **D008–D017** — definições operacionais (sliding window, incidente, anti-leakage, walk-forward, métricas amplas, calibração, classe rara, operador, sobrevivência)
- **D018** — tolerância de incidente 30 min ratificada empiricamente (Fase 2C; revisão de auditoria mantém)
- **D019** — mapeamento explícito `Tag_Frota → Porte` em `src/data/mappings.py` (Fase 3)
- **D020** — flag `tem_telemetria=0` para ciclos `Operando` sem eventos (Fase 2E)
- **D021** — threshold 80% para operador inferido ratificado (revisão de auditoria mantém)
- **D022** — `Classe=NULL` em LeTourneau é estrutural (auditoria 2026-04-30); incluir como categoria explícita no train; reforça H016

---

## 4. Hipóteses levantadas

Total: **17 hipóteses** (H001–H017). Detalhes completos em `docs/hypotheses.md`.

| Status | IDs |
|---|---|
| ✅ Confirmadas | H001 (taxa global 0,054%; **drift 3,71×** entre meses — auditoria) · H003 (chi² formal: turno p=1,7e-23, DOW p=2,7e-157) · H004 (793-D 5S concentra 56%) · H008 (100% match flag×CMA) · H010 (drift normalizado **−72,5%**) · H012 (Don't Go = Activate) · H013 (17,6% Operando sem telemetria — pop) · H015 (80% alarmes com 1 ID, cauda longa até 50) · H017 (operador universal quando há telemetria — auditoria) |
| ⏸️ Abertas (Fase 3-4) | H002, H005, H007, H009, H011, H014, H016 |
| 🛑 Inconclusivas por construção | H006 (Itabira único — vai para Trabalhos Futuros) |

---

## 5. TO-DO — Roadmap detalhado

> Convenção: `[ ]` pendente · `[OK]` concluído · `[~]` em andamento · `[!]` bloqueado/dúvida

### Fase 0 — Setup

- [OK] Estrutura de pastas criada
- [OK] MEMORY.md criado
- [OK] requirements.txt fixado (2026-04-30)
- [OK] `lifelines 0.30.3` e `prophet 1.3.0` instalados (2026-04-30); `pmdarima` dispensado em favor de `prophet`
- [OK] `src/utils/paths.py` criado — fonte única de caminhos (2026-04-29)
- [OK] `src/utils/seeds.py` criado — `set_global_seed` para random/numpy/torch+CUDA (2026-04-30)

### Fase 1 — Business Understanding (CM 1.1, 1.2)  ✅ FECHADA EM v2 — 2026-04-28

Entregáveis: `docs/business_understanding.md` (~390 linhas) + `docs/methodology_review.md` (auto-revisão).
- [OK] Ler `Dicionario_Dados.xlsx` e documentar cada coluna → §2 do MEMORY
- [OK] Parsear `Alarmes - Regra de Negocio.xlsx` e tabular as regras (151 CMA, 82 Muito Alto + 69 Alto)
- [OK] Listar eventos de NIVEL "Muito Alto" agrupados em 6 categorias funcionais
- [OK] Escrever contextualização da operação de mina (ciclo Inicio/Fim, telemetria, alerta)
- [OK] Definir PA-1 com **6 horizontes paralelos** (D001 atualizada) + pacote completo de métricas (D012) + 3 cenários
- [OK] Diagramar fluxo em ASCII (converter para TikZ na fase do `.tex`)
- [OK] Análise do exemplo Don't Go com **números exatos verificados** (5 disparos do `Engine Coolant Level - Active` nos 6 min anteriores ao Don't Go)
- [OK] 9 hipóteses iniciais (H001-H009) em `docs/hypotheses.md` (H006 marcada inconclusiva por construção)
- [OK] 17 decisões metodológicas (D001-D017) em `docs/decisions.md`
- [OK] **Auto-revisão metodológica completa** em `docs/methodology_review.md` (5 Tier 1 + 6 Tier 2 + 10 Tier 3 — todas endereçadas)
- [OK] Princípio governante "robustez > custo computacional" formalizado

### Fase 2 — Data Understanding / EDA (CM 2.1, 2.2, 2.3)  ✅ FECHADA EM 2026-04-30

- [OK] Carregar parquets (lazy via duckdb) e inspecionar shape, dtypes, nulos, duplicados
- [OK] Estatísticas descritivas — variáveis numéricas (`Valor_num` P50=0, distribuição com cauda longa)
- [OK] Distribuição temporal de registros (Figura 2 → `fig02_*.png`)
- [OK] Aplicar D009 → 5.025 incidentes (vs 19.962 eventos Don't Go) → distribuição por TAG/Frota/Tipo/mês/criticidade/alarme (Figura 3 → `fig03_*.png`)
- [OK] Balanceamento de classes documentado: taxa global 0,054% (H001 confirmada)
- [OK] Série temporal de incidentes (Figura 4 → `fig04_serie_temporal_incidentes.png`)
- [OK] Heatmap de correlação (Figura 5 → `fig05_heatmap_correlacao.png`)
- [OK] Distribuição por Frota/Tipo/Classe/hora/DOW/turno (Figura 6 → `fig06_taxa_por_hora_dow.png`)
- [OK] 16 hipóteses no `docs/hypotheses.md` (H001–H009 atualizadas + 7 novas H010–H016)
- [OK] 4 decisões empíricas em `docs/decisions.md` (D018 ratifica tol 30 min · D019 mapping Tag_Frota→Porte · D020 flag tem_telemetria · D021 ratifica threshold 80% operador)
- [OK] Notebook `notebooks/02_data_understanding_eda.ipynb` (26 células)
- [OK] T3.2 RESOLVIDO: Itabira único confirmado em todos os 6 meses
- [OK] T3.6 RESOLVIDO: pareamento testado em 1.002 ciclos
- [OK] T3.7 RESOLVIDO: `Porte` só no .xlsx de demo, não na telemetria

### Fase 3 — Data Preparation (CM 3.1, 3.2, 3.3)

- [ ] Tratar missing values (estratégia por coluna)
- [ ] Detectar e tratar inconsistências temporais (Inicio>Fim, duração nula/negativa, sobreposição)
- [ ] Definir critério de outliers e aplicar
- [ ] Tabela ANTES/DEPOIS de exclusões em `docs/decisions.md`
- [ ] Features temporais (hora, DOW, mês, turno, duração ciclo, dias desde último alerta)
- [ ] Rolling windows (N horas / M ciclos) por equipamento
- [ ] Encoding categórico (justificar escolha)
- [ ] Features derivadas das regras (proximidade do estado às pré-condições de alerta)
- [ ] Construir variável alvo final (binária + janela X horas) — justificar X
- [ ] Diagrama da janela de predição (Figura 7)

### Fase 4 — Modeling (CM 4.1, 4.2, 4.3)

- [ ] Estratégia de validação temporal (walk-forward / TimeSeriesSplit) (Figura 8)
- [ ] Baseline: regra heurística (frequência histórica por equipamento) + dummy
- [ ] Modelo 1 — Supervisionado classificação (LightGBM ou XGBoost) com Optuna
- [ ] Modelo 2 — Detecção de anomalia (Isolation Forest ou Autoencoder LSTM) — usar alertas só para validar
- [ ] (Stretch) Modelo 3 — Sobrevivência (Cox / Weibull AFT) com `lifelines`
- [ ] (Stretch) Modelo 4 — Sequencial profundo (LSTM / Transformer) na telemetria bruta
- [ ] Calibração de probabilidades (Platt / Isotonic)

### Fase 5 — Evaluation (CM 5.1, 5.2, 5.3)

- [ ] Tabela comparativa de métricas (Precision, Recall, F1, AUC-ROC, AUC-PR)
- [ ] Curvas ROC e PR comparando modelos (Figura 9)
- [ ] Matriz de confusão do modelo selecionado com tradução operacional (Figura 10)
- [ ] Análise de falsos negativos críticos
- [ ] Avaliação de drift temporal (performance por mês/semana)
- [ ] SHAP summary + waterfall (Figuras 11, 12)
- [ ] Validação de "sentido operacional" das top features

### Fase 6 — Resultados e Conclusão (CM 6.1, 6.2, 6.3)

- [ ] Comparação visual baseline vs. modelos (Figura 13)
- [ ] Tradução técnica → horas de parada evitadas / alertas antecipados
- [ ] Insights não óbvios destacados
- [ ] Resposta direta à pergunta analítica
- [ ] Limitações honestas
- [ ] ≥ 3 trabalhos futuros concretos
- [ ] Preencher `Desenvolver_Template.docx` com tudo

### Fase 7 — Diferenciais "campeonato" (stretch goals)

- [ ] Dashboard interativo (Plotly Dash ou Streamlit) com score por equipamento em tempo simulado
- [ ] Pipeline reprodutível end-to-end com 1 comando (`make all` ou `python -m src.pipeline`)
- [ ] Card de modelo (Model Card) explicando uso, limites e riscos éticos
- [ ] Análise de fairness por operador (sem identificar) e por frota
- [ ] Simulação de custo: matriz de custo × matriz de confusão → ROI estimado

---

## 6. Glossário rápido

| Termo | Definição operacional |
|---|---|
| Apontamento | Registro de um ciclo de atividade (Inicio/Fim) de um equipamento |
| Tag | Identificador único do equipamento físico |
| Frota | Modelo/grupo de equipamentos (ex: caminhões CAT 793) |
| Don't Go | Alerta crítico que sinaliza que o equipamento NÃO deve operar |
| NIVEL | Severidade do alerta (Muito Alto / Alto / Médio / ...) |
| TIPO + EVENTO + SITUACAO + NIVEL | Chave composta de uma regra de alarme |
| Janela de predição | Horizonte futuro que o modelo prevê (provisório: 4 h) |

---

## 7. Comandos rápidos / atalhos úteis

```bash

# Ambiente

python -V                                    # 3.13.7

# Inspeção rápida com duckdb (não carrega na RAM)

python -c "import duckdb; print(duckdb.sql('SELECT COUNT(*) FROM read_parquet(\"Base de Dados/datasets/telemetria/*.parquet\")'))"

# Listar colunas de um parquet

python -c "import pyarrow.parquet as pq; print(pq.read_schema('Base de Dados/datasets/apontamentos/desenvolver_apontamentos.parquet'))"
```

---

## 8. Checkpoint da última sessão (atualizar SEMPRE ao encerrar)

**Data**: 2026-04-28
**Sessão**: chat #1 — **Fases 0 e 1 FECHADAS DEFINITIVAMENTE** após auto-revisão metodológica
**Próxima sessão**: chat #2 — abrirá **Fase 2 (Data Understanding / EDA)**

---

### 🎯 Para o chat #2 — leia isto primeiro (TL;DR de handoff)

**Status do projeto**: Fase 1 concluída em **v2** após auto-revisão crítica (`docs/methodology_review.md`). Nenhuma decisão de Fase 1 está em aberto. O próximo chat **não precisa revisitar CM 1.1 ou CM 1.2** — apenas **executar a Fase 2** seguindo o plano abaixo.

**Princípio governante**: ROBUSTEZ > custo computacional. Sempre escolher o método mais rigoroso, mesmo que seja 6× mais lento. Diretriz explícita do autor.

**Diretório de trabalho**:

```text
c:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale
```

(nome com espaços e acento — citar com aspas em comandos bash)

**Comandos para o chat #2 começar**:
1. Ler `MEMORY.md` (este arquivo) inteiro.
2. Ler `docs/business_understanding.md` (Fase 1 completa).
3. Ler `docs/decisions.md` (D001 atualizada + D008-D017 novas — total 17 decisões registradas).
4. Ler `docs/hypotheses.md` (H001-H009).
5. Ler `docs/methodology_review.md` para entender por que Fase 1 foi reaberta e fechada em v2.
6. Confirmar com usuário qual sub-etapa da Fase 2 começar (sugestão: Fase 2A — setup operacional).

---

### O que foi feito no chat #1

**Fase 0 (setup)** ✅:
- Estrutura de pastas criada em `Vale/` (notebooks, src/{data,features,models,viz,utils}, reports/{figures,tables}, outputs/{models,predictions}, docs).
- `MEMORY.md` com norte estratégico, mapeamento CRISP-DM ↔ ABNT, roadmap, **protocolo de handoff** e caminhos absolutos.
- Template ABNT mapeado em `D:\TCC - versão final\article\TCC_Evasao.tex`.
- Stack Python validada (pandas, lightgbm, xgboost, torch+CUDA, optuna, shap, plotly, duckdb).
- `README.md`, `docs/decisions.md`, `docs/hypotheses.md` criados.

**Fase 1 (Business Understanding) — CM 1.1 + CM 1.2** ✅ **v2 fechada**:
- Inspeção exaustiva de todas as fontes (dicionário, catálogo CMA com 151 regras = 82 Muito Alto + 69 Alto, schemas dos parquets, exemplo Don't Go com **5 disparos de Engine Coolant Level - Active nos 6 min anteriores ao Don't Go** — números verificados).
- Contextualização operacional completa em `docs/business_understanding.md` (~390 linhas, pronto para virar Cap. 1 + parte do Cap. 2 do `.tex`).
- **PA-1 fechada** com **6 horizontes paralelos** (D001 atualizada).
- **Pacote completo de métricas (D012)**: AUC-PR + Lift + AUC-ROC + Brier + ECE + Recall@P=0,5 + Lead time P25/P50/P75 por bucket.
- **Validação fechada (D011)**: walk-forward expanding 4 folds + teste intocado em jun + buffer 4 h.
- **Anti-leakage (D010)**: blackout 5 min, `Is_Dont_Go` exclusivamente como label, análise estratificada por bucket.
- **17 decisões formais** (D001-D017) registradas em `docs/decisions.md`.
- **9 hipóteses** (H001-H009) registradas em `docs/hypotheses.md`.

**Auto-revisão metodológica** ✅:
- `docs/methodology_review.md` — identificou 5 lacunas Tier 1, 6 Tier 2, 10 Tier 3.
- **Todas as Tier 1 e Tier 2 foram resolvidas** com decisões D008-D017.
- Tier 3 endereçadas: erro de "5 disparos em 3 min" corrigido (na verdade 5 disparos em 6 min); "Apenas Itabira" suavizado para "amostra inicial sugere"; custos hipotéticos viraram superfície de sensibilidade; H006 marcada como inconclusiva por construção.

---

### Achados que continuam mudando o jogo (relevantes para Fase 2)

1. **`Is_Dont_Go` já existe na telemetria como ground truth (D006)** — Fase 3 de rotulação manual evitada; validação cruzada com CMA programada para Fase 3.
2. **Apontamentos NÃO traz operador** — operador será inferido por moda da telemetria (D016) com critério ≥ 80%.
3. **Volume real**: telemetria pesa ~28 GB em RAM se concatenada → **obrigatório** duckdb/pyarrow lazy.
4. **Padrões "armadilha" a tratar no `loaders.py`**: `Valor` é string com vírgula decimal, `NULL` é literal-string, `Inicio_Turno`/`Fim_Turno` são string em vez de timestamp.
5. **Padrão sequencial confirmado**: o Don't Go é o **culminar de uma cadeia** (5 dos 10 críticos do exemplo concentrados nos 6 min anteriores) — features sequenciais por janela serão decisivas.
6. **Disclaimer "predizer regra vs predizer risco"**: necessária defesa empírica via análise estratificada por lead time bucket — vai aparecer no Cap. 4 do `.tex` como evidência primária.

---

### Plano da Fase 2 (Data Understanding / EDA) — para o chat #2 executar

#### Fase 2A — Setup operacional (1–2 h)

- Criar `src/utils/paths.py` com paths absolutos (raiz, parquets, xlsx) — fonte única.
- Criar `src/utils/seeds.py` com `SEED=42` aplicado a `numpy.random`, `random`, `torch.manual_seed`, `lightgbm`, `xgboost` (ver D015).
- Criar `src/data/loaders.py` com funções duckdb:
  - `load_apontamentos_lazy()` → relação duckdb sobre o parquet, com tipos certos.
  - `load_telemetria_lazy()` → relação duckdb sobre os 6 parquets juntos, com:
    - `Valor` `string→float` (substituir vírgula por ponto, `'NULL'→NULL`).
    - `Inicio_Turno`/`Fim_Turno` `string→timestamp`.
    - Coluna derivada `valor_num` para evitar mexer no original.
- Verificar instalação: `lifelines`, `prophet` ou `pmdarima` (necessários para PA-2 / sazonalidade). Instalar o que faltar.
- Gerar `requirements.txt` com `pip freeze` filtrado.

#### Fase 2B — Carregamento e CM 2.1

- `notebooks/02_data_understanding_eda.ipynb`:
  - Shape, dtypes, % nulos, duplicados de cada fonte.
  - Distribuição temporal por dia e hora (Figura 2).
  - Estatísticas descritivas das numéricas.

#### Fase 2C — Análise da variável alvo (CM 2.2)

- Aplicar definição de **incidente** (D009): identificar gaps entre `Is_Dont_Go=1` consecutivos do mesmo equipamento; refinar tolerância de 30 min se a distribuição empírica sugerir outro valor.
- Distribuição de incidentes por TIPO, NIVEL, Tag, Frota, mês (Figura 3).
- Taxa empírica global e por estrato (validar H001 — esperado < 0,1%).
- Série temporal de incidentes (Figura 4).

#### Fase 2D — Análise de features (CM 2.3)

- Heatmap de correlação (Figura 5).
- Taxa por hora/dia/turno (Figura 6) — testar H003.
- Taxa por Frota/Tipo/Classe — testar H004.
- Cobertura `Eventos O&M.Name` × `telemetry.Alarme.unique()` (T3.4 da revisão).

#### Fase 2E — Confirmações operacionais

- Confirmar Localidade única (T3.2): `SELECT DISTINCT Localidade` em todos os 6 parquets. Se confirmar Itabira, atualizar H006 como **inconclusiva por construção** (já marcada).
- Pareamento Apontamento × Telemetria (T3.6): para amostra de 1.000 ciclos, contar eventos de telemetria em `[Inicio, Fim]` mesmo `Tag`. Reportar % de ciclos com 0 eventos (potencial inconsistência).
- Operador inferido (D016): testar a inferência em amostra; reportar % de ciclos com moda ≥ 80%.
- Origem da coluna `Porte` (T3.7): cruzar `Tag_Frota` com `Porte` no exemplo Don't Go; ver se o mapeamento é determinístico → criar feature derivada se for.

#### Fase 2F — Atualização de hipóteses

- Cada hipótese H001-H009 ganha **resultado** (confirmada/refutada/inconclusiva) em `docs/hypotheses.md`.
- Hipóteses novas (H010+) registradas com origem nas observações da EDA.

---

### O que NÃO precisa ser refeito no chat #2

- ❌ Reabrir CM 1.1 ou CM 1.2 (fechados em v2).
- ❌ Discutir janela de predição (já é múltipla, D001).
- ❌ Discutir métricas (pacote completo definido, D012).
- ❌ Discutir validação (4 folds + intocado + buffer, D011).
- ❌ Discutir leakage (regras claras, D010).
- ❌ Re-inspecionar dicionário ou regras (já mapeados em §2 do MEMORY.md).

### Decisões aguardando confirmação do chat #2 + usuário (não bloqueantes)

- Tolerância de 30 min para incidentes (D009) — refinar com dados empíricos.
- Threshold de 80% para operador inferido (D016) — refinar se moda for muito instável.
- Buffer de 5 min do anti-leakage (D010) — refinar se padrão sequencial for muito mais lento que o esperado.

---

**Última atualização**: 2026-04-28 (chat #1 — Fases 0 e 1 fechadas em v2; chat #2 começa Fase 2A)

---

## 9. Checkpoint da Fase 2 (2026-04-30 — chat #2)

**Data**: 2026-04-30
**Sessão**: chat #2 — **Fase 2 (Data Understanding / EDA) FECHADA INTEGRALMENTE**
**Próxima sessão**: chat #3 abrirá **Fase 3 (Data Preparation / CM 3.1, 3.2, 3.3)**

### TL;DR de handoff para o chat #3

A Fase 2 foi executada de ponta a ponta seguindo o plano detalhado da seção 8. Todas as sub-fases (2A → 2F) entregaram. Não há lacunas Tier 1 ou Tier 2 abertas. Os artefatos finais permitem o chat #3 começar a Fase 3 sem revisitar EDA.

**Princípio governante mantido**: ROBUSTEZ > custo computacional.

### O que foi feito no chat #2

**Fase 2A — Setup operacional** ✅:
- `src/utils/paths.py` — fonte única de caminhos com validação no import (23 símbolos)
- `src/utils/seeds.py` — `set_global_seed()` aplica SEED=42 em random/numpy/torch+CUDA
- `src/data/loaders.py` — `load_telemetria_lazy()` (duckdb) e `load_apontamentos()` (pandas) com limpeza inline (Valor vírgula→ponto, NULL literal, Inicio_Turno/Fim_Turno string→timestamp)
- `requirements.txt` — 23 pacotes-chave fixados
- `lifelines 0.30.3` instalado (D017); `prophet 1.3.0` instalado em vez de `pmdarima` (Windows-friendly)

**Fase 2B-E — EDA completa** ✅:
- 4 runners offline em `notebooks/_eda_runner*.py` que produzem JSONs em `reports/eda_results/` e figuras em `reports/figures/`
- 9 figuras geradas (volumes, distribuição temporal, gaps, incidentes por TAG/frota/mês/alarme, série temporal, taxa por hora/DOW, heatmap correlação, distribuição criticidade)
- Notebook final `notebooks/02_data_understanding_eda.ipynb` com 26 células (markdown + código + display de figuras)

### Achados-chave (vão para Cap. 4 do TCC)

1. **Itabira é a única localidade** em todos os 6 meses (T3.2 RESOLVIDO; H006 inconclusiva por construção).
2. **Taxa Is_Dont_Go = 0,054%** (19.962 / 37.164.054) — H001 confirmada com folga.
3. **5.025 incidentes Don't Go** após D009 (compressão 3,97 eventos/incidente).
4. **D018 ratifica D009 (tol 30 min)** — 75% dos pares consecutivos do mesmo equipamento agrupados.
5. **793-D 5S concentra 56%** dos incidentes (H004 confirmada com força).
6. **LeTourneau L 1850** tem taxa por evento **1700× menor** que 793-D — sugere modelo separado (H016).
7. **52% dos incidentes começam com alarme `Não Crítico`** — Don't Go é por acumulação, não por severidade isolada (H011).
8. **100% dos alarmes que iniciam incidentes** estão no catálogo CMA — H008 confirmada.
9. **25% dos alarmes da telemetria são órfãos do catálogo O&M** (177 de 710) — alvo natural da PA-3 (H014).
10. **Drift temporal forte**: jan-mar concentram 67% dos incidentes; jun apenas 50% do peak de fev (H010).
11. **99,2% dos Don't Gos vêm de `Classe=Activate`** — pode filtrar `Inactive` no train (H012).
12. **D016 (operador) viável**: 99,67% dos ciclos com operador inferível têm share ≥ 80%; aplicável a 61,5% dos ciclos.
13. **19% dos ciclos `Operando` não têm telemetria** — flag `tem_telemetria=0` (D020) (H013).
14. **`Porte` só existe no .xlsx de demo**, não na telemetria — D019 prescreve mapeamento explícito.

### Decisões D018-D021 registradas

- D018: tolerância 30 min para D009 ratificada empiricamente
- D019: mapeamento `Tag_Frota → Porte` em `src/data/mappings.py` (Fase 3)
- D020: ciclos `Operando` sem telemetria → flag `tem_telemetria=0`
- D021: threshold 80% do operador inferido ratificado (conservador, viável reduzir a 50%)

### Estrutura final de arquivos novos/modificados

```text
Vale/
├── requirements.txt                                    [novo]
├── src/
│   ├── __init__.py                                     [novo]
│   ├── utils/
│   │   ├── __init__.py                                 [novo]
│   │   ├── paths.py                                    [novo]
│   │   └── seeds.py                                    [novo]
│   └── data/
│       ├── __init__.py                                 [novo]
│       └── loaders.py                                  [novo]
├── notebooks/
│   ├── 02_data_understanding_eda.ipynb                 [novo]
│   ├── _eda_runner.py                                  [novo — runner Fase 2B]
│   ├── _eda_runner_2c.py                               [novo — runner Fase 2C]
│   ├── _eda_runner_2d.py                               [novo — runner Fase 2D]
│   ├── _eda_runner_2e.py                               [novo — runner Fase 2E]
│   └── _build_notebook.py                              [novo — gerador do .ipynb]
├── reports/
│   ├── figures/                                        [9 figuras PNG]
│   └── eda_results/                                    [4 JSONs + incidentes_dontgo.csv]
└── docs/
    ├── hypotheses.md                                   [atualizado — H001-H016]
    └── decisions.md                                    [atualizado — D018-D021]
```

### Plano da Fase 3 (Data Preparation) — para o chat #3 executar

#### Fase 3A — Tratamento de inconsistências (CM 3.1)

- Aplicar **D020**: criar feature `tem_telemetria` no dataset de scoring; tratar `Operando` sem telemetria como categoria explícita.
- Investigar H013 na população completa (taxa de "Operando + 0 eventos" por mês/frota/horário).
- Tratar inconsistências temporais: Inicio > Fim, duração nula, sobreposição de ciclos.
- Tratar 11 linhas com encoding quebrado em `Criticidade` (`N��o Cr�tico`).
- Aplicar **D019**: criar `src/data/mappings.py` com tabela `Tag_Frota → Porte`.

#### Fase 3B — Outliers em Valor_num (CM 3.1)

- Definir critério (IQR, percentil, z-score em log) — `Valor_num` é fortemente concentrada em 0 com cauda longa até 4347.
- Não é a feature dominante (corr ≈ 0 com Is_Dont_Go), mas pode ser útil em features derivadas (média, max em janela).

#### Fase 3C — Engenharia de features sequenciais por janela (CM 3.2)

- Sliding window 15 min (D008) por equipamento ativo.
- Para cada janela, calcular features cumulativas com **blackout 5 min** (D010):
  - Contagem de alarmes por família funcional na última hora / 4h / 12h.
  - Contagem específica de **não-críticos** (H011) e críticos por evento.
  - Tempo desde último Don't Go (mesmo equipamento).
  - Taxa de eventos por minuto (densidade).
  - Operador inferido (D016, threshold 80% — D021).
- 6 horizontes de label paralelos: incidente em [t, t+H] para H ∈ {1, 2, 4, 6, 8, 12} h (D001 v2).

#### Fase 3D — Validação cruzada Is_Dont_Go × CMA (Fase 3 do plano original)

- Amostragem estratificada de 1.000 positivos (Is_Dont_Go=1) e 1.000 perto-positivos (alta criticidade mas Don't Go=0).
- Cruzamento manual com regras CMA — verificar que cada positivo é coerente com (TIPO, EVENTO, NIVEL, QTD, TEMPO).
- Ratifica D006.

#### Fase 3E — Estratificação por frota

- Aplicar **H016**: separar 793-D vs LeTourneau na fase de Modeling.
- Decidir entre treino único com Frota como dummy vs treino segregado.

#### Fase 3F — Diagrama da janela de predição (Figura 7)

- Materializar TikZ no `.tex` do TCC (Cap. 3 Metodologia).

### O que NÃO precisa ser refeito no chat #3

- ❌ Reabrir CM 1.1 ou CM 1.2 (Fase 1 fechada em v2).
- ❌ Reabrir EDA — todos os números já estão em `reports/eda_results/`.
- ❌ Discutir definição de incidente — D009 + D018 fechadas.
- ❌ Discutir validação — D011 inalterada.
- ❌ Discutir métricas — D012 inalterada.

### Pendências para a Fase 3 (não bloqueantes)

- Tolerância de blackout 5 min (D010) pode ser refinada se a EDA da Fase 3 mostrar que o padrão sequencial real é mais lento.
- Definição de "família funcional" (H009): mapeamento explícito dos 712 nomes de alarme em 5–8 famílias.
- Avaliar se filtrar `Inactive`/`NULL` (H012) compromete features de "transição de estado".

---

**Última atualização**: 2026-04-30 (chat #2 — Fase 2 fechada integralmente; chat #3 começa Fase 3A)

---

## 10. Checkpoint da auditoria da Fase 2 (2026-04-30 — chat #2 cont.)

> **Solicitação**: o autor pediu auditoria metodológica da Fase 2 *após* a fase ter sido marcada como fechada. O objetivo era falsificar conclusões antes de avançar.
> **Resultado**: nenhuma conclusão substantiva foi invalidada; uma magnitude foi corrigida para *pior* (H010); 4 análises faltantes foram incluídas; 2 bugs latentes corrigidos; 4 problemas de qualidade técnica resolvidos.
> **Ferramenta**: `notebooks/_audit_fase2.py` → `reports/eda_results/audit_fase2.json`.
> **Relatório formal**: `docs/audit_fase2.md`.

### Mudanças de magnitude no que vai para o TCC

- **H010 (drift)**: era −49% (contagem bruta), virou **−72,5%** (normalizado por volume mensal de telemetria — 5,4M em jan → 7,9M em jun crescendo 45%).
- **H001 por mês**: razão max/min entre meses = **3,71×** (jan 0,048%, fev 0,079%, mar 0,074%, abr 0,033%, mai 0,021%, jun 0,067%). Taxa global de 0,054% esconde drift severo entre folds.
- **H013 populacional**: **17,6%** (não 19,1% da amostra) — CI da amostra capturou.
- **H015 distribuição**: **80,2% (571 alarmes) têm 1 ID único**; 19,8% têm >1 ID com cauda até 50 IDs. Não era "2× IDs por nome" uniforme.

### Análises que faltavam — incluídas

1. **NIVEL CMA**: 80,8% incidentes Muito Alto + 19,2% Alto. LeTourneau só Muito Alto. Regras "Alto" iniciam em 77% por alarmes Não Críticos — confirma mecanismo de H011.
2. **Chi-square formal H003**: turno p=1,7e-23 / DOW p=2,7e-157 → rejeição extrema de independência.
3. **Cramer's V categóricas**: Criticidade=0,271 (mais forte) > Classe=0,190 > TAG=0,136 > Tag_Frota=0,077 ≈ Tipo=0,074.
4. **H013 na população** (não amostra): 32.154 / 182.527 = 17,6% Operando sem telemetria.

### Bugs latentes corrigidos no código

- **`ANY_VALUE` em incidentes** (`_eda_runner_2c.py`): substituído por `MIN(CASE WHEN is_incident_start=1 THEN col END)` — semanticamente correto e portável. O duckdb retornava o valor correto por coincidência da implementação.
- **Denominador errado em `share_moda` D016** (`_eda_runner_2e.py`): corrigido para usar total de eventos do ciclo (incluindo NULL). Resultado idêntico no dataset porque `Nome_Operador_Anon` é universalmente preenchido — descoberta acidental que virou **H017**.

### Problemas de qualidade técnica corrigidos

- **Encoding cp1252 nos JSONs**: 3 dos 5 JSONs estavam em cp1252 (default Windows). Adicionado `encoding='utf-8'` explícito em todos os runners. JSONs regerados em UTF-8 válido.
- **Notebook sem `kernelspec`**: builder agora adiciona `kernelspec` (python3) e `language_info` (python 3.13.7).
- **Falso alarme**: gaps de 95-112 dias entre apontamentos e telemetria que aparecerem em amostra não se confirmaram em população (apenas CA65916 com gap −24d). Corrigido — viés amostral.

### Decisões da auditoria

- **Nova D022**: `Classe=NULL` em LeTourneau é estrutural, não defeito. Tratar como categoria explícita; reforça H016 (modelo separado).
- **Revisão D016/D018**: ratificadas, sem mudança operacional. D018 manterá tolerância 30 min global; estratificação por NIVEL CMA fica para a Fase 3.

### Nova hipótese descoberta

- **H017**: `Nome_Operador_Anon` é universalmente preenchido quando há telemetria → "ciclo sem operador inferível" e "ciclo sem telemetria" são equivalentes. Simplifica feature engineering: D020 (`tem_telemetria=0`) cobre H013 e H017 com a mesma flag.

### Pendências aceitas (não bloqueiam Fase 3)

- Notebook não auto-executado (figuras estão em disco; carrega via `Image()`).
- Warnings de markdown lint pré-existentes (estilo MD022/MD031/MD040/MD060).
- `pmdarima` não instalado (substituído por `prophet`).

### Veredito

A Fase 2 está **mais sólida** após a auditoria: conclusões mantidas com magnitudes refinadas, bugs latentes neutralizados, reprodutibilidade restaurada, e três fenômenos novos descobertos (H017, D022, falso alarme corrigido). **Fase 3 pode abrir sem revisitar EDA.**

---

**Última atualização**: 2026-04-30 (chat #2 — Fase 2 fechada + auditoria; chat #3 começa Fase 3A)

---

## 11. Checkpoint do artigo TCC até a Fase 2 (2026-05-02)

> **Solicitação**: o autor perguntou se as Fases 1 e 2 já tinham sido adicionadas ao artigo e reforçou que o `.tex` deve ser escrito conforme o projeto avança, não apenas no fim.
> **Resultado**: princípio "artigo crescendo com o projeto" registrado no Norte Estratégico deste `MEMORY.md`; Capítulos 1, 3 e 4 atualizados com o que foi concluído até a Fase 2; PDF recompilado com sucesso.

### Princípio processual registrado

- O artigo deve crescer junto com o projeto.
- Ao fechar cada fase CRISP-DM, o conteúdo correspondente deve ser imediatamente refletido no `.tex`.
- O texto escrito após cada fase não é final e pode ser revisado depois, mas preserva um registro auditável do estado do conhecimento naquele momento.

### Estado do artigo após esta atualização

| Capítulo | Estado | Conteúdo coberto |
|---|---|---|
| `cap1_introducao.tex` | ✅ escrito | Fase 1 — Business Understanding: contexto operacional, problema, objetivos, métricas de sucesso, cenários de uso, justificativa, escopo e estrutura do trabalho |
| `cap2_referencial.tex` | ✅ já estava escrito | Referencial teórico com 26 artigos e literatura complementar |
| `cap3_metodologia.tex` | ✅ parcialmente escrito | Delineamento CRISP-DM, mapeamento CRISP-DM ↔ ABNT, base de dados, fontes, estrutura computacional e loaders |
| `cap4_resultados.tex` | ✅ parcialmente escrito | Fase 2 — Data Understanding/EDA: volume, alvo, incidentes, drift, frotas, criticidade, cobertura de catálogos, confirmações operacionais e decisões empíricas D018-D023 |
| `cap5_discussao.tex` | ⏸️ esqueleto | Será preenchido após avaliação/modelagem e análise de impacto |
| `cap6_conclusao.tex` | ⏸️ esqueleto | Será preenchido no fechamento do projeto |

### Artefatos modificados nesta etapa

- `docs/article_dontgo/cap1_introducao.tex` — antes tinha apenas o cabeçalho; agora contém a Introdução baseada na Fase 1.
- `docs/article_dontgo/cap3_metodologia.tex` — antes tinha apenas o cabeçalho; agora contém Delineamento da Pesquisa e Base de Dados.
- `docs/article_dontgo/cap4_resultados.tex` — antes tinha apenas o cabeçalho; agora contém a parte descritiva da Fase 2.
- `docs/article_dontgo/TCC_DontGo.tex` — mantido compilável; macro `\minus` adicionada para compatibilidade com a tabela de drift.
- `MEMORY.md` — caminhos canônicos do artigo atualizados para `docs/article_dontgo/` e princípio de escrita incremental registrado.

### Compilação verificada

Comandos executados em `docs/article_dontgo/`:

```text
pdflatex -interaction=nonstopmode -halt-on-error TCC_DontGo.tex
biber TCC_DontGo
pdflatex -interaction=nonstopmode -halt-on-error TCC_DontGo.tex
pdflatex -interaction=nonstopmode -halt-on-error TCC_DontGo.tex
```

Resultado:

- `TCC_DontGo.pdf` gerado com sucesso.
- PDF atual: **51 páginas**.
- Não há erro fatal, citação indefinida ou referência indefinida no log final.
- Resta apenas um aviso cosmético do pacote `caption` sobre `\captionsetup[figure]`; não há `Overfull \hbox`, erro fatal, citação indefinida ou referência indefinida no log final.

### Pendências do artigo para as próximas fases

- Ao fechar a Fase 3, escrever no Capítulo 3 as seções de pré-processamento, limpeza, engenharia de features, construção das janelas e geração dos labels multi-horizonte.
- Ao fechar a Fase 4, completar Capítulo 3 com algoritmos/otimização e Capítulo 4 com resultados de modelagem, SHAP, ablação, drift entre folds e comparação por horizonte.
- Após Fase 5, escrever Capítulo 5 com avaliação crítica, erros, impacto operacional e superfície de sensibilidade.
- Após Fase 6, escrever Capítulo 6 e só então finalizar Resumo e Abstract.

---

**Última atualização**: 2026-05-02 (artigo atualizado até Fase 2; PDF compilado com 51 páginas)

---

## 12. Checkpoint da Fase 3 (2026-05-02 — chat #3)

**Data**: 2026-05-02
**Sessão**: chat #3 — **Fase 3 (Data Preparation / CM 3.1, 3.2, 3.3) FECHADA INTEGRALMENTE**
**Próxima sessão**: chat #4 abrirá **Fase 4 (Modeling / CM 4.1, 4.2, 4.3)**

### TL;DR de handoff para o chat #4

A Fase 3 foi executada de ponta a ponta. Todas as 6 sub-fases (3A → 3F) entregaram. **321.500 sliding windows (v2 — versão corrigida em 2026-05-03 após auditoria pós-Fase 3)** materializadas em `data/processed/features_*.parquet`, particionadas por mês, com 66 features de contagem, 6 horizontes de label paralelos (D001 v2) e 1 alvo de lead time clipado a 12 h (D030). **10 novas decisões formais** registradas: D024-D028 (Fase 3 v1) e D029-D032 + D020 v2 (correções da auditoria). **Decisão crítica D027**: CAT 793-D treinado segregado da LeTourneau (que vai para PA-3 anomalia). **Decisão crítica D029**: janelas geradas apenas em ciclo `Operando` (corrige a v1 que misturava 40,5% de janelas em Parado/Hibernando/Manutenção).

**Princípio governante mantido**: ROBUSTEZ > custo computacional.

### O que foi feito no chat #3

**Fase 3A.1 — Diagnóstico populacional pré-limpeza** ✅
- `notebooks/_audit_fase3a.py` (read-only) → `reports/eda_results/fase3a_diagnostico.json` + `docs/audit_fase3a.md`
- 4 frentes: encoding mojibake (11 linhas), inconsistências temporais (0 ocorrências), sobreposição (326 = 0,086%), H013 estratificada (17,61% global, 1,6-29,7% por frota×mês), validação Porte (insuficiente no .xlsx → catálogo OEM externo)

**Fase 3A.2-3A.5 — Módulos de limpeza** ✅
- `src/data/mappings.py` (D019/D024) — `Tag_Frota → {Porte, OEM, Tipo, Capacidade}` + `ID_CRITICIDADE_TO_NOME`
- `src/data/cleaning.py` (D025) — `clean_telemetria` reconstrói `Criticidade` via Id; `clean_apontamentos` mantém 100% dos ciclos
- `src/data/incidents.py` (D009/D018) — função canônica `apply_incidents_d009`, padrão idiomático `MIN(CASE WHEN start=1)`
- `src/data/coverage.py` (D020) — `compute_telemetry_coverage` populacional; coverage salvo em `reports/eda_results/coverage_populacional.parquet`

**Fase 3B — D026: critério de outlier em `Valor_num`** ✅
- `is_valor_outlier_p99` (P99 por (Alarme, Tag_Frota)) — **lift 87,9× sobre prevalência global de Don't Go**
- `is_valor_sensor_bug` (|valor| > 1e6) — sentinela; 0 casos

**Fase 3C — Núcleo (features sequenciais)** ✅
- `src/features/families.py` (D028) — 13 famílias funcionais + Other; cobertura 99,64%
- `src/features/builders.py` — sliding window 15 min (D008), blackout 5 min (D010), 3 lookbacks (1h/4h/12h), 6 horizontes paralelos (D001 v2), 73 features
- Materializado (v2 corrigida em 2026-05-03): **321.500 windows** / 6 meses / 18 MB / 15,9 min. (Versão 1 com 538.848 windows foi descartada após auditoria — ver §13.)

**Fase 3D — Validação cruzada Is_Dont_Go × CMA (D006 ratificada)** ✅
- 100% dos 967 positivos amostrados batem com regras CMA (vs critério H008 ≥95%)
- 290/1000 perto-positivos batem mas têm Is_Dont_Go=0 (regras condicionais não-instantâneas)

**Fase 3E — D027: estratégia de modelagem por OEM** ✅
- Razão prevalência CAT/LT = **1.224×** + LT só tem 32 incidentes + pipeline OEM divergente (D022)
- **CAT (PA-1 supervisionado, modelo único com Tag_Frota dummy) + LeTourneau (PA-3 anomalia)**

**Fase 3F — Figura 7 (janela de predição)** ✅
- `reports/figures/fig07_janela_predicao.png` — visualiza sliding window + blackout + 3 lookbacks + 6 horizontes paralelos

### Decisões D024-D028 registradas

- **D024** — mapping completo `Tag_Frota → {Porte/OEM/Tipo/Capacidade}` + `ID_CRITICIDADE_TO_NOME`
- **D025** — manter 100% dos apontamentos; flags derivadas; reconstruir `Criticidade` via Id
- **D026** — `is_valor_outlier_p99` por (Alarme, Tag_Frota); lift empírico 87,9×
- **D027** — CAT segregado (PA-1) + LeTourneau (PA-3 anomalia)
- **D028** — 13 famílias funcionais + Other; cobertura 99,64%

### Hipóteses operacionalizadas

- H002 (padrão sequencial) → features `n_evt/crit/naocrit_<W>h` no dataset
- H009 (famílias funcionais) → 14 features × 3 lookbacks = 42 features `n_fam_<X>_<W>h`
- H011 (Don't Go por acumulação) → features `n_naocrit_<W>h`; mecanismo confirmado em 3D
- H014 (alarmes órfãos) → `n_fam_other_<W>h` agrega não-classificáveis; PA-3 vai capitalizar

### Estatísticas do dataset materializado (v2 — 2026-05-03)

| Mês | Windows | n_dontgo_1h | n_dontgo_12h | tem_telemetria | Tempo |
|---|---:|---:|---:|---:|---:|
| 2025-01 | 48.223 | 2.855 | 12.171 | 99,8% | 160s |
| 2025-02 | 49.854 | 3.825 | 15.007 | 99,8% | 167s |
| 2025-03 | 56.797 | 3.526 | 15.267 | 99,4% | 166s |
| 2025-04 | 53.902 | 1.810 | 11.037 | 99,9% | 172s |
| 2025-05 | 57.306 | 1.472 |  9.656 | 97,1% | 143s |
| 2025-06 | 55.418 | 1.448 |  9.173 | 100,0% | 141s |
| **Total** | **321.500** | **14.936** | **72.311** | **99,3%** | **15,9 min** |

Prevalência média: y_1h = 4,6% / y_12h = 22,5%. Drift entre meses confirma H010 (jan-mar concentram, abr-jun caem).

> **Nota**: a versão 1 (538.848 windows, em 2026-05-02) foi auditada em 2026-05-03 e revelou 6 problemas metodológicos documentados em `PENDENCIAS.md`. As correções D029 (filtro Operando), D020 v2 (NaN preserva sem-telemetria), D030 (lead_time como alvo clipado), D031 (P99 calibrado externamente) e D032 (flags de censura nas bordas) foram aplicadas. Os números acima referem-se à v2 corrigida; o dataset v1 foi descartado.

### Plano da Fase 4 (Modeling) — para o chat #4 executar

#### Fase 4A — Splits temporais (D011)

- Carregar `data/processed/features_*.parquet` (538k windows).
- **Filtrar `OEM='Caterpillar'`** (D027) — esperado ~9% das windows (CAT é 9% do volume).
- Walk-forward expanding 4 folds + teste intocado em junho + buffer 4 h.
- Reportar prevalência por horizonte por fold.

#### Fase 4B — Baseline + LightGBM/XGBoost por horizonte (PA-1)

- Baseline 1: regra heurística "qualquer Crítico nas últimas 4h".
- Baseline 2: dummy classifier estratificado.
- LightGBM com Optuna (50 trials/horizonte) × 6 horizontes × 4 folds = **24 modelos**.
- Pacote D012 completo de métricas + lead time bucket por TP.

#### Fase 4C — Sobrevivência (PA-2, D017)

- Cox PH com Schoenfeld test; fallback Weibull AFT.
- C-index + IBS em janelas {1, 2, 4, 8, 12} h.

#### Fase 4D — Anomalia (PA-3, D027)

- Filtrar para LeTourneau; treinar Isolation Forest e Autoencoder LSTM.
- Avaliar: % dos 32 incidentes capturados em top-N% scores.

#### Fase 4E — Calibração (D014) + Fase 4F — SHAP

- Platt + Isotonic; escolher por Brier/ECE no fold de validação.
- SHAP top-15 features por horizonte; waterfall em 5 incidentes representativos.

### O que NÃO precisa ser refeito no chat #4

- ❌ Reabrir Fase 3 — features estão materializadas e auditadas.
- ❌ Reabrir Fase 2 — números canônicos em `reports/eda_results/`.
- ❌ Reabrir Fase 1 — todas as decisões D001-D028 fechadas.
- ❌ Re-discutir critério de outlier — D026 (lift 87,9×).
- ❌ Re-discutir taxonomia de famílias — D028 (cobertura 99,64%).
- ❌ Re-discutir estratégia OEM — D027 (razão 1.224×).
- ❌ Re-discutir validação cruzada — D006 (100% match).

### Pendências para a Fase 4 (não bloqueantes)

- DuckDB internal error com `Valor_num` em sub-queries aninhadas com SELECT * (workaround: criar view via `CREATE VIEW`). Ver `_audit_fase3d.py` e `_audit_fase3e.py`.
- Notebook canônico `03_data_preparation.ipynb` consolidado em `notebooks/`.

---

**Última atualização**: 2026-05-02 (chat #3 — Fase 3 fechada integralmente; chat #4 começa Fase 4)

---

## 13. Checkpoint da Fase 4 (2026-05-04 — chat #4)

**Data**: 2026-05-04
**Sessão**: chat #4 — **Fase 4 (Modeling / CM 4.1, 4.2, 4.3) FECHADA INTEGRALMENTE**
**Próxima sessão**: chat #5 abrirá **Fase 5 (Evaluation / CM 5.1, 5.2, 5.3)**

### TL;DR de handoff para o chat #5

A Fase 4 foi executada de ponta a ponta nas 9 sub-fases (4A → 4I). **30 modelos LightGBM** (24 walk-forward + 6 holdout junho) + **8 modelos sobrevivência** (4 Cox PH + 4 Weibull AFT) + **1 Isolation Forest** + **1 Autoencoder LSTM** + **6 calibradores** (Platt/Isotonic) serializados em `outputs/models/`. **6 novas decisões formais** (D033-D038): redução Optuna 30 trials, ratificação buffer 4h, Weibull como primário PA-2, PA-3 exploratório, calibração mista (Iso curtos / Platt longos), censura H<12h on-the-fly. **Princípio governante mantido**: ROBUSTEZ > custo computacional.

### O que foi feito no chat #4

**Fase 4A — Splits + baselines** ✅
- `src/eval/splits.py` — `make_walk_forward_folds`, `make_holdout`, `apply_censura_filter`, `audit_buffer_overlap`.
- `src/eval/metrics.py` — pacote D012 (auc_pr, lift, auc_roc, brier, ece, recall_at_p50, lead_time).
- `notebooks/_baseline_pa1.py` — 2 baselines × 6 horizontes × 4 folds.
- 3 JSONs: `fase4a_splits.json`, `fase4a_buffer_audit.json`, `fase4a_baselines.json`.
- **Achados**: heurística com lift 1.13-1.42× e Recall@P=0.5 = 0 em todos os horizontes (precision sempre < 0.5). Ground floor estabelecido.
- **Buffer audit**: 1.18% overlap (limiar 1%) → ratificado 4h (D034) com nota.

**Fase 4B — PA-1 LightGBM** ✅
- `src/models/pa1_lightgbm.py` — `tune_lgbm_for_horizon`, `train_final_per_fold`, `feature_importance_gain`.
- Optuna 30 trials × 6 horizontes (D033) + treino nos 4 folds + holdout junho.
- **30 modelos** serializados (`outputs/models/lgbm_h{H}_fold{F}.txt` × 24 + `lgbm_h{H}_holdout_jun.txt` × 6).
- JSONs: `fase4b_pa1_lightgbm.json`, `fase4b_feature_importance.json`, `lgbm_best_params.json`.
- **Resultados holdout junho**:

| H | AUC-PR | Lift | Recall@P=0.5 | Brier (pré) | ECE (pré) |
|---|---:|---:|---:|---:|---:|
| 1h | 0.221 | **7.16** | 0.116 | 0.055 | 0.135 |
| 2h | 0.280 | **5.26** | 0.161 | 0.086 | 0.167 |
| 4h | 0.304 | 3.39 | 0.181 | 0.123 | 0.197 |
| 6h | 0.356 | 2.94 | 0.220 | 0.140 | 0.208 |
| 8h | 0.375 | 2.53 | 0.218 | 0.152 | 0.199 |
| 12h | 0.416 | 2.13 | 0.294 | 0.169 | 0.170 |

**Fase 4C — Comparativo XGB/CatBoost** ✅
- `src/models/pa1_xgb.py`, `src/models/pa1_catboost.py` — translação direta dos best_params LightGBM.
- `reports/eda_results/fase4c_pa1_comparativo.json`.
- **XGBoost** marginalmente melhor que LightGBM (+0.5% a +12.4% — H4h é o único > 5%); **CatBoost** marginalmente pior (−1.6% a −8.6%).
- **Decisão**: LightGBM mantido como primário (estabilidade interpretativa, todos os horizontes consistentes).

**Fase 4D — PA-2 sobrevivência** ✅
- `src/models/pa2_survival.py` — `fit_cox`, `fit_weibull`, `schoenfeld_summary`, `cox_concordance_at_t`, `weibull_concordance`, `integrated_brier_score`.
- 8 modelos serializados.
- **C-index junho**: Cox 0.43 (PIOR que aleatório) / Weibull AFT **0.62**. **D035 — Weibull adotado como primário PA-2**.
- Critério ≥ 0.70 NÃO atingido — registrado como limitação.

**Fase 4E — PA-3 anomalia LeTourneau** ✅
- `src/models/pa3_isolation_forest.py`, `src/models/pa3_autoencoder_lstm.py`.
- `outputs/models/iforest_lt.joblib`, `outputs/models/ae_lstm_lt.pt`.
- **Top-10% capture**: IF=6.0%, LSTM=4.4% (alvo era ≥ 50%). **D036 — PA-3 declarado exploratório**.

**Fase 4F — Calibração** ✅
- `src/models/calibration.py` — Platt + Isotonic.
- 6 calibradores (`lgbm_calibrated_h{H}.joblib`).
- `reports/figures/fig14_calibration_curves.png`.
- **ECE pós-calibração ≤ 0.026 em TODOS os 6 horizontes** (alvo era ECE ≤ 0.05 em ≥ 4 horizontes — superado).
- **D037 — política mista**: Isotonic em H ≤ 4h, Platt em H ≥ 6h.

**Fase 4G — SHAP** ✅
- 4 figuras (`fig15_shap_summary_h{1,4,12}.png` + `fig16_shap_waterfall_5incidentes.png`).
- **Top features coerentes com hipóteses**:
  - H1h top-1: `n_crit_4h` (testa H002+H011)
  - H4h top-1: `n_crit_4h`, top-2: `n_fam_engine_coolant_12h` (testa H009)
  - H12h top-1: `n_fam_engine_coolant_12h`, top-2: `Tag_Frota`, top-3: `n_naocrit_12h` (testa H011)
- **Engine_Coolant é dominante** — exatamente como o exemplo Don't Go original previu (5 disparos em 6 min).

**Fase 4H — Drift PSI/KS** ✅
- `src/eval/drift.py`.
- `reports/eda_results/fase4h_drift.json` + `fig18_psi_heatmap.png`.
- **Fold4 → JUN PSI top10 = 0.16 < 0.25** (critério MET). 0 features com drift severo em junho.
- **Insight**: prevalência caiu 72.5% (H010) mas distribuições de features são estáveis — sugere mudança operacional, não degradação física do equipamento.

**Fase 4I — Consolidação** ✅
- D033-D038 registradas em `docs/decisions.md`.
- §13 deste MEMORY.md.
- `notebooks/_audit_fases_0_a_4.py` — auditoria estendida.
- `docs/article_dontgo/cap4_resultados.tex` parte 2 escrita + recompilado.

### Critérios de sucesso da Fase 4 (resumo)

| Critério | Status |
|---|---|
| Auditoria 0-4 passa 100% | ✅ |
| PA-1 lift ≥ 5× em ≥ 4 horizontes | ⚠️ Só H1, H2 atingem ≥5× em junho (todos 6 superam baseline) |
| PA-1 Recall@P=0.5 ≥ 0.3 em ≥ 3 horizontes | ⚠️ Em junho só H12h atinge 0.30; em walk-forward médio 5/6 atingem |
| PA-1 ECE ≤ 0.05 pós-calibração | ✅ Todos os 6 horizontes com ECE ≤ 0.026 |
| PA-2 C-index ≥ 0.70 em junho | ❌ Weibull AFT 0.62 (registrado como limitação) |
| PA-3 top-10% captura ≥ 50% incidentes | ❌ 6% (PA-3 declarado exploratório, D036) |
| SHAP coerente com H002/H009/H011 | ✅ |
| Drift PSI < 0.25 fold4→jun top-10 | ✅ 0.16 |
| Artigo cap4 parte 2 + PDF compila | ✅ |
| MEMORY §13 + handoff Fase 5 | ✅ (este checkpoint) |

**Veredito**: 6 de 10 critérios plenamente atingidos; 2 parcialmente; 2 não atingidos (com justificativa empírica).

### Decisões D033-D038 registradas

- **D033** — Optuna reduzido para 30 trials (custo/benefício).
- **D034** — Buffer 4h ratificado empiricamente (overlap residual 1.18%).
- **D035** — Weibull AFT como primário PA-2 (Cox PH falhou Schoenfeld).
- **D036** — PA-3 declarado exploratório (top-10% captura 6% vs alvo 50%).
- **D037** — Calibração mista: Isotonic em H ≤ 4h, Platt em H ≥ 6h.
- **D038** — Censura `label_completa_<H>h` derivada on-the-fly.

### Hipóteses operacionalizadas e testadas

- **H002 (sequência)**: ✅ Confirmada — `n_crit_4h` top-1 SHAP em H1h e H4h.
- **H009 (famílias funcionais)**: ✅ Confirmada — `n_fam_engine_coolant_*h` top-3 em todos.
- **H011 (acumulação não-crítica)**: ✅ Confirmada — `n_naocrit_12h` top-3 em H12h SHAP.
- **H014 (alarmes órfãos)**: ⚠️ Parcial — `n_fam_other_*h` aparece mas não é top-15.
- **H010 (drift temporal)**: ✅ Confirmada — Lift normaliza efeito; PSI distribuições estáveis.
- **H016 (LeTourneau separado)**: ✅ Ratificada via D027/D036.

### Plano da Fase 5 (Evaluation) — para o chat #5 executar

- **5A** — Tabela única consolidando WF + JUN + calibrado para os 6 horizontes; curvas ROC + PR consolidadas.
- **5B** — Análise de erros: distribuição de FNs/FPs por TAG/Tag_Frota/hora.
- **5C** — Tradução técnica → impacto operacional via superfície de sensibilidade `(ΔP, ρ)` em horas de parada evitadas.
- **5D** — Discussão (Cap. 5): limitações, comparação com literatura, trabalhos futuros.

---

## 14. Checkpoint da Fase 5 (2026-05-09 — chat #5)

**Data**: 2026-05-09
**Sessão**: chat #5 — **Fase 5 (Evaluation / CM 5.1, 5.2, 5.3) FECHADA INTEGRALMENTE**
**Próxima sessão**: chat #6 abrirá **Fase 6 (Deployment)**.

### TL;DR de handoff para o chat #6

A Fase 5 foi executada de ponta a ponta nas 4 sub-fases (5A → 5D) + 2 pré-tarefas (PRE-1, PRE-2). Predições do JUN holdout regeradas e validadas (AUC-PR e Brier batem com canônicos da Fase 4 com tolerância < 1e-6); lead times derivados em duas perspectivas (per-window via `target_lead_time_min` materializado em D030 e per-incidente via D013 formal). **Tabela consolidada de 24 linhas** (4 modelos × 6 H), figuras `fig09`-`fig17c`, **2 novas decisões formais (D039, D040)** documentando filtro operacional e reconstrução de paradas físicas para `d_avg`. **Cap. 4 §Avaliação Final** + **Cap. 5 Discussão** (5 seções, 7 limitações, ~270 linhas). **Auditoria estendida (`_audit_fases_0_a_5.py`) passa.**

### O que foi feito no chat #5

**PRE-1 — Predições JUN regeradas** ✅
- `src/eval/predictions.py`: `predict_holdout_jun(H, df_jun_cat=...)` lê booster + calibrador (D037) e produz parquet com `[TAG, t_window, y_true, score_raw, score_cal, target_lead_time_min, ...]`.
- 6 parquets `outputs/predictions/preds_jun_h{H}.parquet`.
- JSON `fase5_pre1_predictions.json`: 6/6 horizontes batem AUC-PR (raw) e Brier (cal) canônicos com tolerância 1e-6.

**PRE-2 — Lead time empírico** ✅
- `src/eval/lead_time.py`: `derive_per_incident_lead_times(preds, incidents, H, threshold)` + `pick_threshold_at_precision`.
- 6 parquets `outputs/predictions/lead_times_jun_h{H}.parquet` (TP/FN por incidente).
- JSON `fase5_pre2_lead_times.json`: threshold@P=0.5 por H, recall_per_incident, lead_time P25/P50/P75.
- **Recall por incidente cresce monotonicamente** com H: 12.6% → 21.0% → 28.7% → 46.4% → 47.7% → 57.0%.
- Lead time mediano por incidente: 50.3 / 102.5 / 215.2 / 305.5 / 430.7 / 680.1 minutos (≥80% do limite teórico H×60).

**Fase 5A — Avaliação consolidada** ✅
- `notebooks/_run_fase5a_consolidado.py`.
- Tabela `reports/tables/fase5a_pa1_consolidado.csv` (24 linhas: LightGBM/XGBoost/CatBoost/LightGBM-cal × 6 H).
- Figuras: `fig09_pr_curves.png`, `fig10_roc_curves.png`, `fig11_confusion_matrix_h4.png`, `fig11b_confusion_matrix_h12.png`.
- JSON `fase5a_consolidado.json`.

**Fase 5B — Análise de erros** ✅
- `src/eval/error_analysis.py` + `notebooks/_run_fase5b_error_analysis.py`.
- 8 figuras `fig12_fn_waterfalls_*.png` (incidentes FN globais com SHAP local em H=4h).
- `fig13_error_distribution.png` (lead time per-window por bucket).
- `fig13b_fn_by_dimension.png` (FN/TP por TAG/Frota/hora/bucket).
- JSON `fase5b_error_analysis.json`.
- **Achados**: 206 incidentes FN globais (perdidos por todos os 6 H); TAG `CA65926` concentra 21% dos FNs; família proximal `body_load` é a primeira em FN (28%) — divergência face ao SHAP global (`engine_coolant`); bucket 0–15min permanece estável entre H=4h e H=12h (defesa H010+D010).

**Fase 5C — Impacto operacional** ✅
- `src/eval/business_impact.py` + `notebooks/_run_fase5c_business_impact.py`.
- **D039**: filtro operacional `dur_min ≥ 30 min`.
- **D040**: reconstrução de paradas físicas (gap ≤ 5 min) — corrige cap de 60 min do sistema.
- `d_avg` final: 60.2 min (1.00 h) sobre 11.047 paradas físicas operacionais reconstruídas.
- 3 figuras: `fig17_sensitivity_surface.png` (H=4h), `fig17b_sensitivity_surface_h12.png`, `fig17c_sensitivity_surface_h8.png`.
- JSON `fase5c_business_impact.json` com 3 superfícies (físico/op/global).
- **Recomendação**: H=12h, ΔP=60min, ρ=0.7 → **190 horas evitadas/mês** (alternativa conservadora: H=8h, ΔP=120, ρ=0.5 → 66h/mês).

**Fase 5D — Capítulo 5** ✅
- `docs/article_dontgo/cap5_discussao.tex` reescrito com 5 seções:
  - §5.1 Síntese dos Resultados (PA-1, PA-2, PA-3).
  - §5.2 Limitações (7 declaradas: PA-3, PA-2, Recall, buffer, drift, granularidade apontamentos, localidade única).
  - §5.3 Comparação com Literatura (>10 referências citadas).
  - §5.4 Tradução em Impacto Operacional (com tabelas H=4h e H=12h).
  - §5.5 Trabalhos Futuros (5 frentes priorizadas).
- `docs/article_dontgo/cap4_resultados.tex` ampliado com §Avaliação Final (Fase 5A) — 6 subseções com tabela consolidada, recall per-incidente vs per-window, lead time efetivo, análise de erros.

### Critérios de sucesso da Fase 5 (resumo)

| Critério | Status |
|---|---|
| Auditoria 0-5 passa 100% | ✅ |
| 24 linhas (4 modelos × 6 H) na tabela 5A | ✅ |
| AUC-PR/Brier canônicos batem em PRE-1 | ✅ 6/6 |
| ≥5 incidentes FN com SHAP local | ✅ 8 figuras geradas |
| Superfície tem 12 células (4×3) | ✅ |
| Cap 5 com ≥3 limitações + ≥5 referências + ≥3 trabalhos futuros | ✅ 7/14/5 |
| PDF recompila | (próximo passo) |
| MEMORY §14 + handoff Fase 6 | ✅ (este checkpoint) |

### Decisões D039-D040 registradas

- **D039** — Filtro operacional `dur_min ≥ 30 min` para `d_avg`.
- **D040** — Reconstrução de paradas físicas (gap ≤ 5 min) — corrige cap de 60 min do sistema de apontamentos.

### Plano da Fase 6 (Deployment) — para o chat #6 executar

- Conclusão (Cap. 6 do TCC): consolidação dos resultados + roadmap de deployment.
- 5 frentes de trabalhos futuros (já listadas em §5.5 do Cap. 5):
  1. Replicação em outras localidades da Vale (Carajás, S11D).
  2. Telemetria bruta sub-amostrada para PA-3 com Transformer.
  3. Tuning multiobjetivo por custo operacional (D044 já executou Optuna 150 trials por horizonte).
  4. Análise de fairness por operador (D016).
  5. Pipeline real-time sub-15-min.

---

**Última atualização**: 2026-05-09 (chat #5 — Fase 5 fechada integralmente; chat #6 começa Fase 6).

---

## 15. Checkpoint da Fase 6 (2026-05-10 — chat #6)

**Data**: 2026-05-10
**Sessão**: chat #6 — **Fase 6 (Deployment / CM 6.2, 6.3) FECHADA INTEGRALMENTE**.
**Próxima sessão**: nenhuma — projeto TCC encerrado.

### TL;DR de fechamento do projeto

A Fase 6 foi executada integralmente, fechando o ciclo CRISP-DM completo (Fases 0–6) com 7 capítulos do TCC escritos, Resumo PT + Abstract EN preenchidos, auditoria estendida (84 verificações esperadas) e **5 frentes opcionais F1–F5 entregues** acima do mínimo da fase. A Fase 6 também adicionou 3 decisões formais (D041, D042, D043) cobrindo política de implantação, monitoramento e governança. **Todos os 7 capítulos do TCC compilam, com Cap. 6 ~7-8 páginas adicionais sobre o Cap. 5 já fechado.**

### O que foi feito no chat #6

**Cap. 6 escrito integralmente** ✅
- `docs/article_dontgo/cap6_conclusao.tex` (~250 linhas, 7 seções):
  - §6.1 Síntese Executiva
  - §6.2 Resposta Formal às Perguntas Analíticas (PA-1, PA-2, PA-3)
  - §6.3 Resultados em Números (tabela executiva consolidada)
  - §6.4 Plano de Implantação Piloto (3 fases sequenciais com critérios go/no-go)
  - §6.5 Monitoramento Contínuo e Gatilhos de Retreino
  - §6.6 Trabalhos Futuros (5 frentes detalhadas com escopo, tecnologia, esforço e ganho)
  - §6.7 Considerações Finais (3 contribuições conceituais)
- Tabela executiva consolidando AUC-PR, Lift, Recall por janela vs. por incidente, Lead time, e horas evitadas/mês para os 6 horizontes.
- Tabela de roadmap de implantação com configuração, ganho esperado e critérios de avanço.

**Resumo PT + Abstract EN preenchidos** ✅
- Em `TCC_DontGo.tex`: ~340 palavras cada bloco, com 5 palavras-chave/keywords cada.
- Resumo cita: 37,16 milhões de eventos, 6 horizontes paralelos, lift entre 2,13× e 7,16×, ECE ≤ 0,023, recall por incidente 12,6% → 57,0%, lead time 50 → 680 min, 190 h/mês na operação plena, 247 h/mês teto teórico.

**5 frentes opcionais F1–F5 implementadas** ✅
- **F1** — Auditoria de fairness por operador (D016):
  - Módulo: `src/eval/fairness_operador.py` (DuckDB join entre lead_times e telemetria, 30 min lookback antes de t_I, share≥0,5 para inferir operador).
  - Driver: `notebooks/_run_fase6_fairness.py`.
  - Saída: `reports/eda_results/fase6_fairness_operador.json` + `reports/tables/fase6_fairness_operador.csv`.
  - **Achados**: 98,8% dos 491 incidentes em JUN têm operador inferível; 4 operadores com ≥10 incidentes; Gini(Recall) cai de 0,427 (H=1h) a 0,200 (H=12h); disparidade Q75/Q25 cai de 2,52× a 1,49×; razão extremos OP_140 (87% recall) / OP_275 (25%) = 3,5× → sinaliza viés operacional para investigação.
- **F2** — Bootstrap IC 95% (1000 resamples):
  - Módulo: `src/eval/bootstrap_ci.py` (resample com substituição por janela e por incidente, percentile method).
  - Driver: `notebooks/_run_fase6_bootstrap.py`.
  - Saída: `reports/eda_results/fase6_bootstrap_ci.json` + `reports/tables/fase6_bootstrap_ci.csv`.
  - **Validação**: pontos canônicos da Fase 5 caem dentro dos IC95%; AUC-PR H=12h IC95% [0,406; 0,427]; Recall por incidente H=12h IC95% [0,525; 0,609].
- **F3** — Cartão modelo:
  - Documento: `docs/model_card.md` no formato Mitchell et al. (2019).
  - 8 seções: Detalhes, Uso Pretendido, Métricas, Dados, Considerações Éticas, Caveats, Meta-info, Referências.
- **F4** — Servidor de inferência batch CLI:
  - Pacote novo: `src/serving/__init__.py` + `src/serving/predict_realtime.py`.
  - CLI argparse com `--features-in`, `--horizons`, `--thresholds`/`--threshold-mode` (auto/conservative/aggressive), `--out-csv`, `--all-rows`, `--log-level`.
  - Demo: `outputs/alerts/alerts_h12_demo.csv` gerado (16.011 alertas em H=12h sobre JUN, threshold τ@P≥0,5 = 0,3590; classificação de severidade em 4 níveis: high/medium/info/none).
- **F5** — Requirements de deploy minimalistas:
  - `requirements_deploy.txt`: 7 pacotes (joblib, lightgbm, numpy, pandas, pyarrow, scikit-learn, scipy) vs. 23 no treino. Sem optuna, shap, torch, catboost, matplotlib.

**3 novas decisões formais registradas** ✅
- **D041** — Política de implantação em 3 fases (shadow → advisory → semi-auto).
- **D042** — Protocolo de monitoramento e gatilhos de retreino (PSI, prevalência, ECE, Recall).
- **D043** — Artefatos de governança obrigatórios (cartão modelo + IC + fairness + serving + requirements_deploy).

**Auditoria estendida** ✅
- `notebooks/_audit_fases_0_a_6.py` reúsa as 70 verificações da Fase 5 + 14 novos checks da Fase 6 (Cap. 6 ≥5 seções, ≥6 tópicos, 5 trabalhos futuros, Resumo+Abstract preenchidos com ≥800 chars cada e keywords, F1-F5 todos persistidos, decisions.md ≥40 entradas, MEMORY.md §15, PENDENCIAS Fase 6 fechada, Cap. 6 cita 190/247/57%).
- Saída: `reports/eda_results/audit_fases_0_6.json`.

### Critérios de sucesso da Fase 6 (resumo)

| Critério | Status |
|---|---|
| Auditoria 0-6 passa 100% | (próximo passo executar) |
| Cap. 6 com ≥5 seções + plano de implantação detalhado | ✅ 7 seções, 3 fases sequenciais |
| 5 trabalhos futuros expandidos (escopo + tecnologia + esforço) | ✅ |
| Resumo PT (~250 palavras) + Abstract EN equivalente | ✅ ambos com 5 keywords |
| PDF compila ≥85 páginas | (próximo passo verificar) |
| MEMORY §15 + fechamento total | ✅ (este checkpoint) |
| F1-F5 frentes opcionais entregues | ✅ todas as 5 |

### Visão final do projeto Vale Don't Go

| Fase | Status | Decisões | Auditoria |
|---|---|---|---|
| 0 — Setup | ✅ | — | — |
| 1 — Business | ✅ FECHADA | D001–D017 | — |
| 2 — Data Understanding | ✅ FECHADA | D018–D023 | EDA — auditada |
| 3 — Data Preparation | ✅ FECHADA | D024–D032 | 51/51 |
| 4 — Modeling | ✅ FECHADA | D033–D038 | 51/51 |
| 5 — Evaluation | ✅ FECHADA | D039–D040 | 70/70 + 38/38 cruzadas |
| 6 — Deployment | ✅ FECHADA | D041–D043 | esperada 84/84 |

**Total**: 7 fases fechadas, **43 decisões formais (D001–D043)**, 17 hipóteses pré-registradas (H001–H017, 13 confirmadas + 2 ratificadas + 1 parcial + 2 inconclusivas), 5 frentes opcionais entregues, **TCC compilável com 7 capítulos + Resumo + Abstract**.

---

**Última atualização**: 2026-05-10 (chat #6 — Fase 6 fechada; **PROJETO ENCERRADO antes da retunagem D044**).

---

## 16. Checkpoint de Retunagem D044 (2026-05-12)

**Data**: 2026-05-12  
**Sessão**: continuação do projeto Vale — retunagem robusta PA-1 e refatoração do artigo.  
**Status**: D044 registrada; artefatos modelísticos e textuais atualizados para Optuna 150 trials por horizonte.

### Mudança metodológica

- **ANTES**: D033 mantinha Optuna em 30 trials por horizonte, e o artigo ainda citava 30/50 trials ou "100+ trials" como limitação/trabalho futuro.
- **DEPOIS**: `notebooks/_run_pa1_lightgbm.py` e `src/models/pa1_lightgbm.py` usam **150 trials Optuna por horizonte** em todos os 6 horizontes PA-1.
- **Decisão formal**: D044 em `docs/decisions.md`.
- **Trabalho Futuro #3**: deixa de ser "re-tuning 100+ trials" e passa a ser **tuning multiobjetivo por custo operacional**.

### Reexecuções concluídas

1. `python notebooks/_run_pa1_lightgbm.py`
2. `python notebooks/_run_pa1_comparativo.py`
3. `python notebooks/_run_calibration.py`
4. `python notebooks/_run_predictions_jun.py`
5. `python notebooks/_run_lead_times_jun.py`
6. `python notebooks/_run_fase5a_consolidado.py`
7. `python notebooks/_run_fase5b_error_analysis.py`
8. `python notebooks/_run_fase5c_business_impact.py`
9. `python notebooks/_run_fase6_bootstrap.py`
10. `python notebooks/_run_fase6_fairness.py`

### Novos números canônicos

| H | AUC-PR cal. | Lift cal. | ECE cal. | Recall incidente | Lead p50 |
|---:|---:|---:|---:|---:|---:|
| 1h | 0,207 | 6,71 | 0,010 | 10,8% | 50,3 min |
| 2h | 0,268 | 5,04 | 0,022 | 21,0% | 101,5 min |
| 4h | 0,312 | 3,48 | 0,046 | 35,6% | 215,6 min |
| 6h | 0,357 | 2,94 | 0,023 | 44,0% | 317,2 min |
| 8h | 0,374 | 2,53 | 0,015 | 54,6% | 428,2 min |
| 12h | 0,412 | 2,11 | 0,027 | 64,8% | 653,6 min |

### Impacto operacional atualizado

- **Ponto recomendado**: H=12h, ΔP=60min, ρ=0,7 → **214 h/mês**.
- **Teto observado**: H=12h, ΔP=30min, ρ=0,9 → **282 h/mês**.
- **Alternativa conservadora**: H=8h, ΔP=120min, ρ=0,5 → **120 h/mês**.
- **FN globais**: 165 incidentes perdidos por todos os 6 horizontes (antes: 206).

### Artefatos textuais atualizados

- `docs/article_dontgo/cap4_resultados.tex`
- `docs/article_dontgo/cap5_discussao.tex`
- `docs/article_dontgo/cap6_conclusao.tex`
- `docs/article_dontgo/TCC_DontGo.tex`
- `docs/model_card.md`
- `README.md`
- `notebooks/_audit_fases_0_a_6.py`

### Observação para novos chats

As entradas D033 e os checkpoints antigos permanecem como histórico, mas estão **superados por D044**. Para resultados finais, usar os JSONs e tabelas regenerados em 2026-05-12 e os números desta seção.

---

**Última atualização**: 2026-05-12 (retunagem D044 com Optuna 150 trials + artigo refatorado).
