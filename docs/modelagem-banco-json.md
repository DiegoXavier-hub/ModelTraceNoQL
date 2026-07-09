# ModelTrace - Modelagem JSON Do Banco

Esta pagina consolida a modelagem documental em JSON depois da revisao do projeto.

Artefatos principais:

- Versao JSON simplificada: [`modelagem-json-simplificada.json`](modelagem-json-simplificada.json)
- Versao JSON completa: [`modelagem-json-completa.json`](modelagem-json-completa.json)
- Versoes ER simplificada e completa: [`modelagem-banco-er.md`](modelagem-banco-er.md)

## Resultado Da Analise

A modelagem anterior estava correta no ponto central: `predictions` deve ser a colecao principal e deve embutir `entity`, `features`, `prediction`, `explanations`, `decision`, `feedback` e `metadata`. Isso faz sentido para MongoDB/NoSQL porque cada modelo possui features diferentes e o documento precisa preservar o payload real da decisao.

As atualizacoes necessarias eram:

- incluir todas as colecoes declaradas no `DocumentStore`;
- documentar `model_version_id`, `flags`, `annotations` e `metadata.contract` em `predictions`;
- separar corretamente `prediction_annotations`, `prediction_replays` e `prediction_scenarios`;
- adicionar `drift_reports`, `webhooks`, `webhook_deliveries`, `cohorts` e `approvals`;
- alinhar `notifications` ao campo real `read_at`;
- alinhar `alerts` aos campos reais `rule_id`, `metric`, `observed_value` e `threshold`;
- expandir os relacionamentos logicos de operacao, governanca, jobs, notificacoes, exports e caches.

Validacao feita em 2026-05-12 contra:

- [`backend/app/db/document_store.py`](../backend/app/db/document_store.py)
- [`backend/app/schemas.py`](../backend/app/schemas.py)
- rotas em [`backend/app/api/routes`](../backend/app/api/routes)
- servicos em [`backend/app/services`](../backend/app/services)
- store local `backend/.data/modeltrace.json`

## Versao Simplificada

Use a versao simplificada para apresentacao, trabalho academico ou explicacao rapida do desenho NoSQL. Ela mantem somente o fluxo essencial:

```text
organizations -> users
organizations -> projects -> models -> model_versions
projects/models/model_versions -> predictions
predictions -> metrics_snapshots / alerts / audit_events
projects -> api_keys
```

Arquivo fonte: [`modelagem-json-simplificada.json`](modelagem-json-simplificada.json)

Colecoes na versao simplificada:

- `organizations`
- `users`
- `projects`
- `models`
- `model_versions`
- `predictions`
- `metrics_snapshots`
- `alerts`
- `api_keys`
- `audit_events`

## Versao Completa

Use a versao completa como referencia tecnica do sistema. Ela cobre todas as colecoes atuais do backend:

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

Arquivo fonte: [`modelagem-json-completa.json`](modelagem-json-completa.json)

## Leitura Operacional

- `predictions` e o documento transacional central. Ele guarda a decisao completa, features variaveis, explicacao, decisao operacional e feedback posterior.
- `models` e `model_versions` separam contrato do modelo, versoes treinadas e promocao para producao.
- `metrics_snapshots`, `dashboard_cache`, `diagnostic_cache` e `drift_reports` sao materializacoes para leitura rapida.
- `alerts`, `alert_rules`, `intervention_cases`, `incidents`, `jobs` e `notifications` compoem a camada operacional.
- `datasets`, `data_quality_reports`, `cohorts`, `model_evaluations`, `model_cards` e `approvals` compoem a camada de governanca de dados/modelos.
- `api_keys`, `email_tokens`, `audit_events` e `exports` compoem seguranca, acesso, evidencias e rastreabilidade.

## Privacidade E Seguranca

- E-mails usam `email_encrypted`, `email_hash` e `email_masked`.
- Entidades usam `entity.id_encrypted`, `entity.id_hash`, `entity.id_masked`, `entity.display_name_encrypted` e `entity.display_name_masked`.
- API keys persistem apenas `key_hash`; a chave completa aparece somente na criacao.
- Exportacoes devem usar `redact_pii=true` por padrao.
- Auditoria deve redigir tokens, senhas, API keys, e-mails e nomes exibidos antes de persistir.
