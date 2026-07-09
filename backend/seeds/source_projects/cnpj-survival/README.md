# Analise de Sobrevivencia de Empresas Brasileiras

Este projeto investiga dois problemas complementares com os Dados Abertos do CNPJ: quanto tempo empresas brasileiras permanecem ativas e quais sinais ajudam a antecipar baixa no horizonte de 12 meses. O trabalho foi estruturado como um case completo de Data Science, com auditoria da base, desenho temporal explicito, analise de sobrevivencia e modelagem preditiva calibrada.

## O que o projeto responde

- Qual e a duracao observada das empresas brasileiras
- Como a sobrevivencia varia por coorte, porte, UF e atividade economica
- Quais sinais cadastrais conseguem antecipar risco de baixa sem leakage temporal

## Principais resultados

- 67.175.202 empresas analisadas e 31.342.895 eventos de baixa observados
- Mediana Kaplan-Meier de 14,17 anos
- Sobrevivencia estimada: 85,4% em 1 ano, 75,7% em 3 anos, 68,6% em 5 anos, 57,2% em 10 anos
- Modelo final `logistic_full` com isotonic calibration: ROC-AUC 0,6975, PR-AUC 0,1327, lift 2,53x no top 10%
- Sinais mais fortes: idade da empresa, enquadramento Simples/MEI e coorte de abertura

## Estrutura do repositorio

```
analise-sobrevivencia-cnpj/
├── src/                    # Pipeline de analise (rodar em ordem)
│   ├── 01_diagnostico.py   # Diagnostico e integridade da base
│   ├── 02_consolidacao.py  # Consolidacao das tabelas CNPJ
│   ├── 03_bases_analiticas.py  # Bases survival e radar 12M
│   ├── 04_auditoria.py     # Auditoria de leakage e estabilidade
│   ├── 05_eda.py           # Analise exploratoria descritiva
│   ├── 06_sobrevivencia.py # Kaplan-Meier, Cox e riscos competitivos
│   └── 07_modelagem_radar.py  # Classificacao e calibracao do radar 12M
├── figures/                # Graficos gerados pelo pipeline
├── tables/                 # Tabelas de resultados (CSV)
├── artigo/                 # Artigo cientifico em LaTeX (ABNT)
│   ├── references.bib      # Referencias bibliograficas
│   ├── pt/artigo.tex       # Versao em portugues (abntex2 + biblatex-abnt)
│   └── en/artigo.tex       # Versao em ingles (abntex2 + biblatex-abnt)
├── data/
│   ├── raw/                # Dados brutos (nao versionados — ver instrucoes)
│   └── processed/          # Parquets intermediarios (nao versionados)
├── portfolio/              # Materiais de portfolio
│   ├── README.md
│   └── images/             # 6 melhores visualizacoes do projeto
└── requirements.txt
```

## Dados

Os dados brutos nao estao no repositorio por restricao de tamanho (snapshot CNPJ 2026-03, ~50 GB).

**Para reproduzir:**
1. Baixe os arquivos de [dados.rfb.gov.br/CNPJ](https://dados.rfb.gov.br/CNPJ/) (snapshot 2026-03)
2. Coloque em `data/raw/cnpj/`
3. Baixe os arquivos de Regimes Tributarios da RFB
4. Coloque em `data/raw/regimes_tributarios/`
5. Execute os scripts de `src/` em ordem

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python src/01_diagnostico.py
python src/02_consolidacao.py
python src/03_bases_analiticas.py
python src/04_auditoria.py
python src/05_eda.py
python src/06_sobrevivencia.py
python src/07_modelagem_radar.py
```

## Tecnologias

Python, DuckDB, pandas, statsmodels, scikit-learn, XGBoost, LightGBM, SHAP, Plotly, Seaborn

## Licenca

MIT
