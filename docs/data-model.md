# ModelTrace - Modelagem NoSQL

Guia completo de consumo da API: [`api.md`](api.md)

Documentacao completa do software: [`documentacao-software.md`](documentacao-software.md)

Manual funcional da interface: [`manual-funcionalidades.md`](manual-funcionalidades.md)

Versoes atualizadas da modelagem:

- ER simplificado e completo: [`modelagem-banco-er.md`](modelagem-banco-er.md)
- JSON simplificado: [`modelagem-json-simplificada.json`](modelagem-json-simplificada.json)
- JSON completo: [`modelagem-json-completa.json`](modelagem-json-completa.json)
- Guia JSON comentado: [`modelagem-banco-json.md`](modelagem-banco-json.md)

## Colecoes principais

- `users`
- `organizations`
- `projects`
- `models`
- `model_versions`
- `api_keys`
- `email_tokens`
- `notifications`
- `jobs`
- `saved_views`
- `entity_notes`
- `prediction_scenarios`
- `predictions`
- `prediction_annotations`
- `prediction_replays`
- `metrics_snapshots`
- `dashboard_cache`
- `diagnostic_cache`
- `drift_reports`
- `alert_rules`
- `alerts`
- `webhooks`
- `webhook_deliveries`
- `datasets`
- `cohorts`
- `model_evaluations`
- `model_cards`
- `intervention_cases`
- `incidents`
- `data_quality_reports`
- `approvals`
- `audit_events`
- `exports`

## Colecao central

`predictions` e a colecao central. Ela usa documentos aninhados para representar uma decisao completa do modelo:

- dados da entidade;
- features recebidas;
- score, label e threshold;
- explicacoes;
- decisao tomada;
- feedback real posterior;
- metadata tecnica.

## Justificativa NoSQL

MongoDB e adequado porque o payload de `features` varia por modelo. Em um banco relacional, cada novo modelo poderia exigir alteracao de schema ou tabelas auxiliares excessivas. Em MongoDB, cada predicao armazena seu proprio conjunto de features como documento.

## Embed vs referencia

Dados embutidos em `predictions`:

- `entity`
- `features`
- `prediction`
- `explanations`
- `decision`
- `feedback`
- `flags`
- `metadata`

Dados separados:

- `prediction_annotations`, pois pode crescer independentemente.
- `prediction_replays`, pois replay e uma analise posterior e pode haver varias simulacoes para uma mesma predicao.
- `prediction_scenarios`, pois cenarios de what-if precisam de historico e comparacao sem alterar a predicao original.
- `metrics_snapshots`, pois representa agregados materializados.
- `dashboard_cache`, pois evita recalculo completo de paineis em bases grandes.
- `diagnostic_cache`, pois materializa threshold tuning, calibracao, slices e contrato de features para o DS Lab.
- `drift_reports`, pois os relatorios de drift sao materializacoes temporais por modelo.
- `audit_events`, pois e historico imutavel.
- `alerts`, pois possui ciclo de vida proprio.
- `entity_notes`, pois anotacoes sobre uma entidade podem crescer ao longo do tempo e nao pertencem a uma predicao especifica.
- `saved_views`, pois filtros, colunas e preferencias de tela pertencem ao usuario e mudam independentemente dos dados transacionais.
- `jobs`, pois execucoes assincronas possuem status, parametro, resultado e ciclo de vida proprio.
- `notifications`, pois comunicacoes internas precisam de leitura, agrupamento e marcacao independente.
- `api_keys`, pois credenciais precisam de hash, escopos, expiracao e ciclo de revogacao separados dos projetos.
- `email_tokens`, pois confirmacao de email e reset de senha precisam de token com hash, finalidade, expiracao e uso unico separados do documento do usuario.
- `alert_rules`, pois regras mudam independentemente das ocorrencias geradas em `alerts`.
- `datasets` e `data_quality_reports`, pois fontes e qualidade possuem ciclo proprio de ingestao e validacao.
- `cohorts`, pois segmentos operacionais sao reaproveitados em dashboards e filas.
- `model_evaluations`, `model_cards` e `approvals`, pois governanca de modelos nao pertence ao payload transacional da predicao.
- `intervention_cases` e `incidents`, pois operacao possui status, prioridade, SLA e timeline proprios.
- `webhooks` e `webhook_deliveries`, pois configuracao e tentativas de entrega precisam de historico separado.
- `exports`, pois arquivos e evidencias possuem status e metadados proprios.

## Indices

```js
db.predictions.createIndex({ org_id: 1, project_id: 1, created_at: -1 })
db.predictions.createIndex({ model_id: 1, model_version: 1, created_at: -1 })
db.predictions.createIndex({ "entity.id": 1, project_id: 1, created_at: -1 })
db.predictions.createIndex({ "entity.id_hash": 1, project_id: 1, created_at: -1 })
db.predictions.createIndex({ "prediction.score": -1, project_id: 1 })
db.predictions.createIndex({ "prediction.label": 1, model_id: 1 })
db.predictions.createIndex({ "prediction.score_band": 1, project_id: 1 })
db.predictions.createIndex({ "feedback.available": 1, model_id: 1 })
db.predictions.createIndex({ "feedback.classification_result": 1, model_id: 1 })
db.predictions.createIndex({ "metadata.request_id": 1 }, { unique: true, sparse: true })
db.metrics_snapshots.createIndex({ model_id: 1, "period.granularity": 1, "period.start": -1 })
db.diagnostic_cache.createIndex({ model_id: 1, slice_feature: 1 }, { unique: true })
db.audit_events.createIndex({ project_id: 1, created_at: -1 })
db.api_keys.createIndex({ key_hash: 1 }, { unique: true, sparse: true })
db.api_keys.createIndex({ project_id: 1, status: 1 })
db.email_tokens.createIndex({ token_hash: 1, purpose: 1 }, { unique: true })
db.email_tokens.createIndex({ user_id: 1, purpose: 1, created_at: -1 })
db.notifications.createIndex({ org_id: 1, user_id: 1, read_at: 1, created_at: -1 })
db.jobs.createIndex({ org_id: 1, project_id: 1, created_at: -1 })
db.saved_views.createIndex({ org_id: 1, user_id: 1, view: 1, created_at: -1 })
db.entity_notes.createIndex({ org_id: 1, project_id: 1, entity_hash: 1, created_at: -1 })
db.prediction_scenarios.createIndex({ org_id: 1, prediction_id: 1, created_at: -1 })
db.dashboard_cache.createIndex({ project_id: 1 }, { unique: true })
db.prediction_replays.createIndex({ prediction_id: 1, created_at: -1 })
db.audit_events.createIndex({ "actor.id": 1, created_at: -1 })
db.audit_events.createIndex({ event_type: 1, created_at: -1 })
db.alerts.createIndex({ project_id: 1, status: 1, severity: 1, created_at: -1 })
db.intervention_cases.createIndex({ project_id: 1, status: 1, priority: 1 })
db.model_evaluations.createIndex({ project_id: 1, model_id: 1, window: 1 })
db.model_cards.createIndex({ project_id: 1, model_id: 1 })
db.data_quality_reports.createIndex({ project_id: 1, created_at: -1 })
db.cohorts.createIndex({ project_id: 1, created_at: -1 })
```
