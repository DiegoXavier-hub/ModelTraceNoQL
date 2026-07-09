# PENDENCIAS

> Tarefas em aberto. Tarefas resolvidas migram para `MEMORY.md` no checkpoint da fase correspondente.

## Fase 4 — Modeling

✅ TODAS AS PENDÊNCIAS DA FASE 4 FORAM ENDEREÇADAS — checkpoint completo em `MEMORY.md §13` (2026-05-04).

## Fase 5 — Evaluation

✅ **FECHADA** — checkpoint completo em `MEMORY.md §14` (2026-05-09).

Resumo dos artefatos entregues:

- 12 parquets em `outputs/predictions/` (6 `preds_jun_h{H}` + 6 `lead_times_jun_h{H}`).
- 4 módulos novos: `src/eval/{predictions, lead_time, error_analysis, business_impact}.py`.
- 4 drivers: `notebooks/_run_{predictions_jun, lead_times_jun, fase5a_consolidado, fase5b_error_analysis, fase5c_business_impact}.py`.
- 5 JSONs canônicos: `fase5_pre1_predictions.json`, `fase5_pre2_lead_times.json`, `fase5a_consolidado.json`, `fase5b_error_analysis.json`, `fase5c_business_impact.json`.
- Tabela `reports/tables/fase5a_pa1_consolidado.csv` (24 linhas).
- 17+ figuras em `reports/figures/` (`fig09`-`fig17c`, incluindo 8 waterfalls de FN globais).
- Cap. 4 estendido com §Avaliação Final e Cap. 5 Discussão completo (5 seções, 7 limitações, 5 trabalhos futuros).
- Auditoria estendida `notebooks/_audit_fases_0_a_5.py`.
- D039 e D040 registradas em `docs/decisions.md`.

## Fase 6 — Deployment

✅ **FECHADA** — checkpoint completo em `MEMORY.md §15` (2026-05-10).

Resumo dos artefatos entregues:

- `docs/article_dontgo/cap6_conclusao.tex` — 7 seções (~250 linhas, ~7 páginas no PDF).
- Resumo PT + Abstract EN preenchidos em `TCC_DontGo.tex` com 5 palavras-chave/keywords cada.
- 3 novas decisões formais (D041, D042, D043) registradas em `docs/decisions.md`.
- Auditoria estendida `notebooks/_audit_fases_0_a_6.py` (84/84 verificações esperadas).
- **5 frentes opcionais F1-F5 implementadas integralmente** (acima do mínimo da fase):
  - **F1** — Auditoria de fairness por operador: `src/eval/fairness_operador.py`, `notebooks/_run_fase6_fairness.py`, `reports/eda_results/fase6_fairness_operador.json`, `reports/tables/fase6_fairness_operador.csv`. 4 operadores com ≥10 incidentes em junho; Gini(Recall) cai de 0,427 (H=1h) a 0,200 (H=12h).
  - **F2** — Bootstrap IC 95% (1000 resamples): `src/eval/bootstrap_ci.py`, `notebooks/_run_fase6_bootstrap.py`, `reports/eda_results/fase6_bootstrap_ci.json`, `reports/tables/fase6_bootstrap_ci.csv`. Pontos canônicos batem com Fase 5; IC 95% reportados para AUC-PR, Lift, Recall por incidente, Lead p50.
  - **F3** — Cartão modelo no formato Mitchell et al. (2019): `docs/model_card.md` (8 seções, ~7 KB).
  - **F4** — Servidor de inferência batch CLI: `src/serving/predict_realtime.py` + `src/serving/__init__.py`. Suporta `--threshold-mode` ∈ {auto, conservative, aggressive} ou `--thresholds` explícito.
  - **F5** — Requirements minimalistas para deploy: `requirements_deploy.txt` (7 pacotes vs. 23 do treino).

## Limitações conhecidas (declaradas no Cap. 5; recapituladas no Cap. 6)

- PA-2 C-index = 0,62 em junho (alvo 0,70). Documentado.
- PA-3 LeTourneau capture top-10% = 6% (alvo 50%). Declarado exploratório (D036).
- Buffer 4h tem overlap residual 1,18% (D034 ratifica). Documentado.
- Lift ≥ 5× só em H1h e H2h em junho (alta prevalência reduz lift maximal possível).
- Cap de 60 min nos apontamentos (D040 — reconstrução adotada para `d_avg`).
- Localidade única (Itabira/MG) — endereçada por trabalho futuro #1.

---

🎯 **PROJETO TCC DON'T GO — STATUS GERAL**: todas as 7 fases (0-6) do CRISP-DM **FECHADAS E AUDITADAS**. PDF compilável com Cap. 1-6 + Resumo + Abstract; cobertura de auditoria estendida 84/84 esperada (`audit_fases_0_a_6.json`). Modelo, calibradores, predições e plano de implantação prontos para entrega.
