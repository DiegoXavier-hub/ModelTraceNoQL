# ModelTrace - Documentacao Completa De Software

Guia completo de consumo da API, com exemplos de `curl`, PowerShell, Python e TypeScript: [`api.md`](api.md).

## Sumario

- [1. Visao geral](#1-visao-geral)
- [2. Objetivos do produto](#2-objetivos-do-produto)
- [3. Publico-alvo](#3-publico-alvo)
- [4. Escopo funcional](#4-escopo-funcional)
- [5. Arquitetura geral](#5-arquitetura-geral)
- [6. Stack tecnica](#6-stack-tecnica)
- [7. Estrutura do repositorio](#7-estrutura-do-repositorio)
- [8. Backend](#8-backend)
- [9. Frontend](#9-frontend)
- [10. Banco de dados NoSQL](#10-banco-de-dados-nosql)
- [11. Modelo de seguranca e criptografia](#11-modelo-de-seguranca-e-criptografia)
- [12. API REST](#12-api-rest)
- [13. Fluxos de negocio](#13-fluxos-de-negocio)
- [14. Observabilidade de modelos](#14-observabilidade-de-modelos)
- [15. Operacao corporativa](#15-operacao-corporativa)
- [16. Importacao de dados reais e simulacao de uso](#16-importacao-de-dados-reais-e-simulacao-de-uso)
- [17. Frontend e experiencia de usuario](#17-frontend-e-experiencia-de-usuario)
- [18. Configuracao e execucao](#18-configuracao-e-execucao)
- [19. Testes e validacao](#19-testes-e-validacao)
- [20. Deploy](#20-deploy)
- [21. Operacao, manutencao e governanca](#21-operacao-manutencao-e-governanca)
- [22. Decisoes de arquitetura](#22-decisoes-de-arquitetura)
- [23. Limitacoes conhecidas](#23-limitacoes-conhecidas)
- [24. Roadmap recomendado](#24-roadmap-recomendado)

## 1. Visao Geral

O ModelTrace e uma plataforma web para observabilidade, auditoria, governanca e operacao de decisoes de Machine Learning. O sistema registra cada predicao feita por modelos de ML, armazena as features utilizadas, a saida do modelo, a decisao tomada, explicacoes, feedback posterior e eventos de auditoria.

O projeto nasceu como trabalho para a disciplina de Banco de Dados NoSQL, mas foi evoluido para simular um produto real usado por empresas. A plataforma nao e limitada ao caso de evasao academica. Ela foi desenhada para aceitar modelos de qualquer dominio e problema, como:

- risco de evasao de alunos;
- risco de fechamento de empresas;
- manutencao preditiva industrial;
- risco de churn de clientes;
- fraude;
- ranking;
- regressao;
- anomalias;
- forecasting;
- qualquer outro problema que produza uma decisao rastreavel.

O conceito central e: toda predicao relevante para o negocio vira um documento auditavel, enriquecido com contexto operacional e governanca.

## 2. Objetivos Do Produto

O ModelTrace busca resolver um problema comum em projetos reais de Ciencia de Dados: modelos sao treinados, avaliados e colocados em uso, mas as decisoes em producao ficam pouco rastreaveis. Sem uma plataforma de registro e monitoramento, torna-se dificil responder perguntas como:

- qual versao do modelo tomou determinada decisao;
- quais features foram usadas;
- qual era o score e o threshold naquele momento;
- se houve feedback real depois;
- se a decisao foi correta;
- se o modelo esta piorando ao longo do tempo;
- quais segmentos apresentam desempenho diferente;
- se existem alertas de drift, qualidade ou sobrecarga operacional;
- se dados pessoais estao armazenados com seguranca.

Objetivos praticos:

- demonstrar modelagem documental NoSQL aplicada a ML;
- suportar features flexiveis por modelo sem schema rigido;
- registrar trilha de auditoria;
- materializar metricas para dashboards rapidos;
- oferecer ferramentas uteis para cientistas de dados;
- oferecer ferramentas uteis para operacao de negocio;
- proteger dados reais com criptografia, redaction e indices cegos;
- simular um produto SaaS multi-projeto e multi-dominio.

## 3. Publico-Alvo

Usuarios principais:

- cientistas de dados que precisam acompanhar modelos em producao;
- engenheiros de ML que precisam integrar pipelines e modelos;
- analistas de negocio que precisam acompanhar decisoes acionaveis;
- gestores que precisam de KPIs e saude operacional;
- times de governanca, compliance e auditoria;
- professores e avaliadores da disciplina de Banco de Dados NoSQL.

Papeis previstos:

- `OWNER`: dono da organizacao, com permissao de administracao;
- `ADMIN`: administrador operacional;
- `ANALYST`: usuario de analise, monitoramento e feedback;
- `VIEWER`: usuario somente leitura.

No estado atual, o backend ja registra `role`, `org_id` e permissoes por projeto, mas nem todas as regras finas de RBAC foram implementadas. O controle principal e por autenticacao e isolamento por organizacao.

## 4. Escopo Funcional

### 4.1 Autenticacao

- Cadastro de usuario e organizacao.
- Login com e-mail e senha.
- Emissao de access token e refresh token.
- Cookies `HttpOnly` para sessao.
- Suporte a bearer token para API.
- Logout com limpeza de cookies.
- Endpoint `/auth/me` para dados do usuario autenticado.

### 4.2 Projetos

Projetos representam unidades de negocio ou produtos de ML. Cada projeto possui:

- nome;
- dominio;
- tipo de problema;
- labels de negocio;
- threshold padrao;
- tags;
- configuracoes de drift;
- estatisticas agregadas;
- status ativo ou arquivado.

Exemplos de projetos importados:

- `TCC Student Outcomes Full Replay`;
- `CNPJ Closure Risk Radar`;
- `Industrial Predictive Maintenance`.

### 4.3 Modelos E Versoes

Cada projeto pode ter varios modelos. Cada modelo pode ter varias versoes. Uma versao representa um artefato ou janela de predicao.

Campos importantes:

- algoritmo;
- status: `draft`, `staging`, `production`, `deprecated`;
- features esperadas;
- hiperparametros;
- metadata de treino;
- metricas offline;
- changelog;
- notas.

Quando uma nova versao e criada como `production`, a versao anterior em producao pode ser marcada como `deprecated`.

### 4.4 Predicoes

Predicoes sao o nucleo transacional do produto. Cada predicao registra:

- projeto;
- modelo;
- versao;
- entidade avaliada;
- features;
- score;
- label;
- threshold;
- score band;
- explicacoes;
- decisao operacional;
- feedback;
- flags;
- metadata.

O produto aceita ingestao individual e em lote.

### 4.5 Feedback

Feedback representa o resultado real observado depois da predicao. Ele permite calcular:

- verdadeiro positivo (`tp`);
- falso positivo (`fp`);
- verdadeiro negativo (`tn`);
- falso negativo (`fn`);
- precision;
- recall;
- accuracy;
- F1;
- matriz de confusao.

### 4.6 Auditoria

Eventos importantes geram documentos em `audit_events`. A auditoria cobre:

- cadastro;
- login;
- criacao de projeto;
- criacao de modelo;
- criacao de versao;
- criacao/revogacao de API key;
- registro de predicao;
- feedback;
- anotacoes;
- replay;
- exportacao;
- mudancas de status operacional.

Antes de persistir auditoria, campos sensiveis passam por redaction.

### 4.7 DS Lab

Area voltada para cientistas de dados:

- threshold optimizer;
- curva de thresholds;
- F2;
- precision;
- recall;
- workload rate;
- calibracao;
- ECE;
- Brier score;
- feature coverage;
- feature importance a partir de explicacoes;
- slices;
- diagnostico de erros;
- recomendacoes automaticas.

### 4.8 Monitor

Area de monitoramento:

- API key do projeto;
- comparacao de versoes;
- drift;
- equidade por feature;
- exportacao;
- acompanhamento de metricas.

### 4.9 Operacao

Area de operacao corporativa:

- intervention cases;
- incidentes;
- alertas ativos;
- coortes;
- qualidade de dados;
- avaliacoes de modelos;
- model cards;
- aprovacoes.

### 4.10 Workbench

Tela guiada para registrar predicoes sem escrever JSON. O formulario e montado dinamicamente a partir de `expected_features` do modelo selecionado.

### 4.11 Governanca

Area de governanca:

- audit trail;
- mapa das colecoes NoSQL;
- postura de seguranca;
- migracao de dados sensiveis;
- recomendacoes de hardening.

## 5. Arquitetura Geral

O sistema e dividido em:

- frontend Next.js;
- backend FastAPI;
- camada de persistencia documental;
- adaptador MongoDB;
- adaptador JSON local;
- scripts de importacao;
- documentos de engenharia.

Fluxo de alto nivel:

```mermaid
flowchart LR
  U[Usuario] --> F[Frontend Next.js]
  F --> A[API FastAPI]
  S[Sistema externo / pipeline ML] --> A
  A --> Auth[Autenticacao e API keys]
  A --> Store[DocumentStore]
  Store --> J[JSON local]
  Store --> M[MongoDB]
  A --> Metrics[Metricas, drift e diagnosticos]
  A --> Audit[Audit events]
  F --> Dash[Dashboards, DS Lab, Operacao, Governanca]
```

Fluxo principal de uma predicao:

```mermaid
sequenceDiagram
  participant Client as Pipeline ou Workbench
  participant API as FastAPI
  participant Store as DocumentStore
  participant Audit as Audit
  participant UI as Frontend

  Client->>API: POST /predictions
  API->>API: Valida auth, projeto, modelo e versao
  API->>API: Protege entidade e metadata sensivel
  API->>Store: Insere documento em predictions
  API->>Store: Invalida dashboard_cache e diagnostic_cache
  API->>Audit: Cria evento prediction.recorded
  API-->>Client: prediction_id
  UI->>API: GET /projects/{id}/dashboard
  API->>Store: Calcula ou le cache materializado
  API-->>UI: KPIs e graficos
```

## 6. Stack Tecnica

### 6.1 Backend

- Python 3.13 no ambiente atual.
- FastAPI para API REST.
- Pydantic para validacao de payload.
- Uvicorn como servidor ASGI.
- Motor para MongoDB async.
- Cryptography/Fernet para criptografia de campos.
- Pytest e TestClient para testes.

Dependencias principais:

```txt
fastapi
uvicorn[standard]
pydantic[email]
motor
cryptography
pytest
httpx
```

### 6.2 Frontend

- Next.js 16 (Turbopack) para build e dev server.
- React 18 com Server Components opt-in via `"use client"`.
- TypeScript estrito (`strict: true`, `noEmit`).
- Recharts para graficos com tooltip customizado.
- Lucide React para icones (tree-shaken).
- `next/font/google` para Inter (UI) + IBM Plex Mono (numeros).
- Design system v2 em CSS puro (`globals.css`, ~1.700 linhas, layered com `@layer`).
- Path alias `@/*` para imports a partir da raiz do frontend.

Scripts:

```txt
npm run dev      # next dev (Turbopack)
npm run build    # next build
npm run start    # next start
npm run lint     # tsc --noEmit
```

### 6.3 Persistencia

Dois modos:

- `JsonDocumentStore`: arquivo JSON local em `backend/.data/modeltrace.json`;
- `MongoDocumentStore`: MongoDB real quando `MONGODB_URL` esta configurado.

O contrato da aplicacao depende de `DocumentStore`, permitindo trocar o backend de armazenamento sem alterar as rotas.

## 7. Estrutura Do Repositorio

```txt
Projeto NoSQL/
  backend/
    app/
      api/
        dependencies.py
        routes/
      core/
      db/
      services/
      main.py
      schemas.py
    tests/
    requirements.txt
    Dockerfile
  frontend/
    app/
      page.tsx
      globals.css
      layout.tsx
    lib/
      api.ts
    package.json
    Dockerfile
  docs/
    api.md
    architecture.md
    data-model.md
    manual-funcionalidades.md
    modelagem-banco-json.md
    modelagem-banco-er.md
    modelagem-json-simplificada.json
    modelagem-json-completa.json
    modeltrace-er.svg
    documentacao-software.md
  scripts/
    import_tcc_gi_real_data.py
    seed_data.py
    load_test.py
    requirements-import.txt
  data/
    imported/
  backups/
  tmp/
  docker-compose.yml
  README.md
```

### 7.1 Backend

- `app/main.py`: cria app FastAPI, middlewares, health check e registra routers.
- `app/schemas.py`: modelos Pydantic de entrada.
- `app/api/dependencies.py`: autenticacao, API key e acesso ao store.
- `app/api/routes/auth.py`: cadastro, login, refresh, logout e usuario atual.
- `app/api/routes/projects.py`: CRUD de projetos e dashboard.
- `app/api/routes/models.py`: modelos, versoes, metricas, drift, bias e comparacao.
- `app/api/routes/predictions.py`: ingestao, listagem, feedback, anotacoes, what-if e replay.
- `app/api/routes/api_keys.py`: criacao, listagem e revogacao de chaves.
- `app/api/routes/alerts.py`: regras e alertas.
- `app/api/routes/exports.py`: exportacoes CSV/JSON.
- `app/api/routes/operations.py`: operacao corporativa.
- `app/api/routes/product.py`: notificacoes, jobs, views salvas, timeline de entidades e data contracts.
- `app/api/routes/security.py`: postura e migracao de seguranca.
- `app/core/config.py`: configuracoes por variaveis de ambiente.
- `app/core/security.py`: senhas, tokens e API keys.
- `app/core/privacy.py`: criptografia, indices cegos, mascaramento e redaction.
- `app/core/utils.py`: funcoes utilitarias.
- `app/db/document_store.py`: abstracao e implementacoes de persistencia.
- `app/services/audit.py`: criacao de audit events.
- `app/services/predictions.py`: regra de registro de predicoes e feedback.
- `app/services/metrics.py`: dashboard, snapshots e drift.
- `app/services/diagnostics.py`: DS Lab e diagnosticos.
- `app/services/whatif.py`: simulacao aproximada.
- `app/services/data_contracts.py`: validacao de contratos de features na ingestao.
- `app/services/notifications.py`: criacao de notificacoes internas.

### 7.2 Frontend

- `frontend/app/page.tsx`: aplicacao principal, estados, chamadas API e views.
- `frontend/app/globals.css`: layout, responsividade, superficies, graficos e componentes.
- `frontend/app/layout.tsx`: layout raiz do Next.
- `frontend/app/icon.svg`: icone.
- `frontend/lib/api.ts`: helper de chamadas HTTP.

### 7.3 Scripts

- `scripts/import_tcc_gi_real_data.py`: importacao limpa com dados reais, artefatos de modelo e projetos externos.
- `scripts/seed_data.py`: carga demo simples.
- `scripts/load_test.py`: apoio para carga/testes.
- `scripts/requirements-import.txt`: dependencias extras para importacao de dados e modelos.

## 8. Backend

### 8.1 Inicializacao

`app/main.py` cria o FastAPI com:

- titulo vindo de `APP_NAME`;
- versao `0.1.0`;
- lifespan para abrir e fechar o store;
- documentacao Swagger desativavel em producao;
- `TrustedHostMiddleware`;
- CORS configuravel;
- headers de seguranca;
- rota `/health`;
- routers com prefixo `API_PREFIX`, por padrao `/api/v1`.

### 8.2 Configuracoes

Configuracoes em `app/core/config.py`:

```txt
APP_NAME
API_PREFIX
ENVIRONMENT
SECRET_KEY
FIELD_ENCRYPTION_KEY
PII_HASH_KEY
PASSWORD_PEPPER
API_KEY_HASH_SECRET
PASSWORD_ITERATIONS
ACCESS_TOKEN_MINUTES
REFRESH_TOKEN_DAYS
COOKIE_SECURE
COOKIE_SAMESITE
MONGODB_URL
MONGODB_DB_NAME
LOCAL_STORE_PATH
REDIS_URL
ENABLE_SECURITY_HEADERS
CORS_ORIGINS
ALLOWED_HOSTS
```

Propriedades derivadas:

- `is_production`: verdadeiro para `prod` ou `production`;
- `uses_default_secret`: detecta `SECRET_KEY` padrao de desenvolvimento.

### 8.3 Middlewares

Middlewares aplicados:

- `TrustedHostMiddleware`: restringe hosts aceitos.
- `CORSMiddleware`: libera origens configuradas.
- middleware customizado de headers:
  - `X-Content-Type-Options: nosniff`;
  - `X-Frame-Options: DENY`;
  - `Referrer-Policy: no-referrer`;
  - `Permissions-Policy`;
  - `Cache-Control: no-store` nas rotas da API;
  - `Content-Security-Policy` nas rotas da API.

### 8.4 Camada DocumentStore

Interface `DocumentStore`:

- `connect`;
- `close`;
- `ensure_indexes`;
- `insert_one`;
- `find_one`;
- `find_many`;
- `count`;
- `update_one`;
- `upsert_one`;
- `delete_one`;
- `delete_many`;
- `transform_many`.

`JsonDocumentStore`:

- carrega todas as colecoes do JSON em memoria;
- salva em disco apos modificacoes;
- suporta filtros simples e operadores como `$gte`, `$lte`, `$gt`, `$lt`, `$ne`, `$in`, `$exists`;
- permite desenvolvimento sem MongoDB.

`MongoDocumentStore`:

- usa Motor;
- cria indices;
- executa consultas e updates diretamente no MongoDB;
- `transform_many` usa `bulk_write`.

### 8.5 Servicos De Dominio

`services/predictions.py`:

- valida projeto, modelo e versao;
- aplica controle de organizacao;
- valida idempotencia por `metadata.request_id`;
- protege entidade;
- grava documento em `predictions`;
- invalida caches;
- atualiza contador do projeto;
- registra auditoria;
- adiciona feedback e recalcula metricas.

`services/metrics.py`:

- calcula histograma;
- calcula matriz de confusao;
- calcula precision, recall, accuracy e F1;
- cria `metrics_snapshots`;
- monta dashboard do projeto;
- usa `dashboard_cache`;
- calcula drift de score com PSI;
- calcula drift simples de features numericas.

`services/diagnostics.py`:

- calcula curva de thresholds;
- calcula precision, recall, F1, F2 e workload por threshold;
- calcula calibracao por buckets;
- calcula ECE;
- calcula Brier score;
- calcula feature importance por explicacoes registradas;
- calcula feature coverage;
- gera slices por feature;
- prioriza falsos positivos e falsos negativos;
- gera recomendacoes;
- usa `diagnostic_cache`.

`services/whatif.py`:

- estima efeito de mudancas em features sobre o score;
- usa explicacoes armazenadas;
- retorna alerta metodologico informando que nao e inferencia real do modelo.

`services/audit.py`:

- cria eventos de auditoria;
- aplica redaction antes de persistir.

## 9. Frontend

O frontend e uma aplicacao Next.js 16 (Turbopack) com React 18 e TypeScript estrito. A partir da versao 2 do produto, o monolito original em `app/page.tsx` foi parcialmente refatorado em uma arvore de componentes presentational, mantendo o estado e os efeitos no container principal.

### 9.1 Arquitetura De Componentes

Estrutura atual:

```text
frontend/
  app/
    layout.tsx            (next/font: Inter + IBM Plex Mono, theme=dark)
    page.tsx              (container com state e handlers)
    globals.css           (design system v2: Stripe/Datadog dense)
  components/
    ui/                   (primitives sem dependencia de dominio)
      Badge.tsx
      EmptyState.tsx
      Kbd.tsx             (kbd visual + Shortcut helper)
      Kpi.tsx             (KPI card com sparkline + trend)
      Skeleton.tsx
      Sparkline.tsx       (SVG inline, sem dependencia externa)
      Toast.tsx
      Trend.tsx           (seta + percentual com inversao semantica)
      index.ts
    shell/                (chrome do app)
      AppShell layout
      Sidebar.tsx         (atalhos G+X visiveis em cada item)
      Topbar.tsx          (badge numerico de notificacoes)
      LanguageToggle.tsx
      CommandPalette.tsx  (Cmd+K real, navegacao por seta + Enter)
      NotificationsDrawer.tsx (painel lateral 440px com tabs e contadores)
      ShortcutsModal.tsx  (lista completa em 3 grupos)
    auth/
      AuthScreen.tsx      (hero com gradient aurora, stats, proof grid)
    views/
      OverviewView.tsx    (presentational, recebe ~15 props)
    hooks/
      useKeyboardShortcuts.ts (prefix G+X estilo Gmail/GitHub)
    nav.ts                (VIEW_SHORTCUTS + GLOBAL_SHORTCUTS)
  lib/
    api.ts
    i18n.ts
```

Padroes:

- componentes de `ui/` nao importam nada de `app/`;
- componentes de `views/` recebem dados e formatadores via props;
- estado global continua em `app/page.tsx` (autenticacao, dados, filtros, sessao);
- hooks customizados ficam em `components/hooks/`.

### 9.2 Estado Principal

Estados controlados em `page.tsx`:

- sessao;
- usuario;
- projeto e modelo selecionados;
- versoes, predicoes e paginacao;
- dashboard, diagnosticos e operacao;
- auditoria e chaves de API;
- postura de seguranca;
- command palette aberto e query;
- notifications drawer aberto;
- shortcuts modal aberto;
- filtros de label, versao, feedback e auditoria;
- simulador do Workbench;
- notificacoes toast.

### 9.3 Views

Navegacao:

- `Overview` (refatorado para `components/views/OverviewView.tsx`);
- `Monitor`;
- `Compare` (refatorado para `components/views/ChampionChallengerView.tsx`);
- `Drift` (novo, em `components/views/DriftHeatmapView.tsx`);
- `DS Lab`;
- `Predicoes`;
- `Entidades`;
- `Operacao`;
- `Casos (SLA)` (novo, em `components/views/SlaKanbanView.tsx`);
- `Automacao`;
- `Workbench`;
- `Governanca`;
- `Profile`;
- `Docs`.

A migracao das demais views para `components/views/` esta no roadmap, seguindo o mesmo padrao do `OverviewView`, `ChampionChallengerView`, `DriftHeatmapView` e `SlaKanbanView`.

### 9.4 Componentes Internos Restantes

Componentes ainda definidos dentro de `page.tsx` (alvos para extracao futura):

- `Metric`;
- `EmptyState`;
- `ErrorList`;
- `ResultMetric`;
- `AnalysisBlock`;
- `PredictionTechnicalDetails`.

Os equivalentes mais novos vivem em `components/ui/` (`Kpi` substitui `Metric`, `EmptyState` foi reimplementado, etc.).

### 9.5 Chamadas API

`frontend/lib/api.ts`:

- define `API_URL`;
- monta headers;
- adiciona bearer token quando existe (terceiro argumento);
- usa `credentials: include` para cookies HttpOnly;
- usa `cache: no-store`;
- padroniza retorno em `{ data, error, status }`.

### 9.6 UX E Responsividade

O CSS foi reescrito como design system v2 (`globals.css`, `~1.700` linhas), com camadas `@layer reset, tokens, base, components, utilities`.

Caracteristicas:

- tipografia premium (Inter + IBM Plex Mono via `next/font/google`);
- numeros tabulares (`font-feature-settings: 'tnum'`);
- paleta semantica (accent indigo `#7c5cff`, success `#10b981`, warning `#f59e0b`, danger `#ef4444`, info `#38bdf8`);
- gradientes funcionais nos KPIs criticos e na hero de auth;
- glow funcional (`--shadow-glow`) em elementos com foco;
- light theme preparado via `[data-theme="light"]` (rotina de toggle e o proximo passo);
- skeleton loaders animados via `@keyframes shimmer`;
- pulse-dot animado para indicadores live;
- breakpoints: 1180px (sidebar reduzida), 860px (single column), 520px (mobile).

Para detalhes do design system, ver [`design-system.md`](design-system.md).

## 10. Banco De Dados NoSQL

### 10.1 Justificativa NoSQL

O banco documental e adequado porque cada modelo pode usar features diferentes. Em um modelo relacional tradicional, seria necessario criar:

- colunas demais;
- muitas tabelas auxiliares;
- schemas especificos por modelo;
- joins frequentes para reconstruir uma decisao.

No ModelTrace, cada predicao armazena seu payload completo:

- features;
- predicao;
- explicacoes;
- decisao;
- feedback;
- metadata.

Isso reduz atrito para ingestao e facilita auditoria.

### 10.2 Colecoes

Colecoes suportadas:

```txt
users
organizations
projects
models
model_versions
api_keys
email_tokens
notifications
jobs
saved_views
entity_notes
prediction_scenarios
predictions
prediction_annotations
prediction_replays
metrics_snapshots
dashboard_cache
diagnostic_cache
drift_reports
alert_rules
alerts
webhooks
webhook_deliveries
datasets
cohorts
model_evaluations
model_cards
intervention_cases
incidents
data_quality_reports
approvals
audit_events
exports
```

### 10.3 Documento Central: predictions

Estrutura conceitual:

```json
{
  "_id": "pred_xxx",
  "org_id": "org_xxx",
  "project_id": "proj_xxx",
  "model_id": "model_xxx",
  "model_version_id": "version_xxx",
  "model_version": "v1",
  "entity": {
    "id": "entity_hash_curto",
    "id_hash": "hmac_sha256:...",
    "id_encrypted": "enc:v1:...",
    "type": "student",
    "display_name": "[protected]",
    "display_name_encrypted": "enc:v1:..."
  },
  "features": {
    "feature_name": "valor"
  },
  "prediction": {
    "label": "high_risk",
    "score": 0.82,
    "threshold": 0.7,
    "above_threshold": true,
    "score_band": "0.8-0.9"
  },
  "explanations": [],
  "decision": {},
  "feedback": {},
  "annotations": [],
  "flags": {},
  "metadata": {}
}
```

### 10.4 Embed Vs Referencia

Dados embutidos em `predictions`:

- `entity`;
- `features`;
- `prediction`;
- `explanations`;
- `decision`;
- `feedback`;
- `flags`;
- `metadata`.

Dados separados:

- `prediction_annotations`: anotacoes podem crescer independentemente;
- `prediction_replays`: varios replays para uma mesma predicao;
- `audit_events`: trilha append-only;
- `metrics_snapshots`: agregados por periodo;
- `dashboard_cache`: resposta materializada;
- `diagnostic_cache`: diagnosticos caros;
- `alerts`: ciclo de vida proprio;
- `exports`: arquivos gerados.

### 10.5 Indices MongoDB

Indices implementados:

```js
db.users.createIndex({ org_id: 1, email_hash: 1 }, { unique: true, sparse: true })
db.api_keys.createIndex({ key_hash: 1 }, { unique: true, sparse: true })
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
db.dashboard_cache.createIndex({ project_id: 1 }, { unique: true })
db.diagnostic_cache.createIndex({ model_id: 1, slice_feature: 1 }, { unique: true })
db.metrics_snapshots.createIndex({ model_id: 1, "period.granularity": 1, "period.start": -1 })
db.audit_events.createIndex({ project_id: 1, created_at: -1 })
db.audit_events.createIndex({ "actor.id": 1, created_at: -1 })
db.audit_events.createIndex({ event_type: 1, created_at: -1 })
db.alerts.createIndex({ project_id: 1, status: 1, severity: 1, created_at: -1 })
db.intervention_cases.createIndex({ project_id: 1, status: 1, priority: 1 })
db.model_evaluations.createIndex({ project_id: 1, model_id: 1, window: 1 })
db.model_cards.createIndex({ project_id: 1, model_id: 1 })
db.data_quality_reports.createIndex({ project_id: 1, created_at: -1 })
db.cohorts.createIndex({ project_id: 1, created_at: -1 })
db.notifications.createIndex({ org_id: 1, user_id: 1, read_at: 1, created_at: -1 })
db.jobs.createIndex({ org_id: 1, project_id: 1, created_at: -1 })
db.saved_views.createIndex({ org_id: 1, user_id: 1, view: 1, created_at: -1 })
db.entity_notes.createIndex({ org_id: 1, project_id: 1, entity_hash: 1, created_at: -1 })
db.prediction_scenarios.createIndex({ org_id: 1, prediction_id: 1, created_at: -1 })
```

## 11. Modelo De Seguranca E Criptografia

### 11.1 Principios

O sistema adota:

- minimo armazenamento de dados sensiveis em texto claro;
- criptografia em repouso para PII;
- indices cegos para busca;
- redaction antes de auditoria/exportacao;
- hashing forte de senhas;
- HMAC para API keys;
- cookies `HttpOnly`;
- headers de seguranca.

### 11.2 Senhas

Senhas sao armazenadas como:

```txt
pbkdf2_sha256_v2$390000$salt$digest
```

Caracteristicas:

- salt aleatorio;
- iteracoes configuraveis por `PASSWORD_ITERATIONS`;
- pepper opcional por `PASSWORD_PEPPER`;
- compatibilidade com hashes legados;
- rehash automatico no login quando necessario.

### 11.3 Tokens

Tokens sao JWT-like assinados com HMAC-SHA256:

- access token;
- refresh token;
- expiracao configuravel;
- campo `sub` com user id;
- campo `type` com tipo do token.

### 11.4 Cookies

No login e cadastro, a API emite:

- `modeltrace_access`;
- `modeltrace_refresh`.

Ambos sao:

- `HttpOnly`;
- `SameSite` configuravel;
- `Secure` configuravel.

O frontend tambem mantem sessao em `sessionStorage` para compatibilidade com bearer token, evitando persistencia longa em `localStorage`.

### 11.5 E-mails

Cada e-mail e armazenado como:

```json
{
  "email": "d***@example.com",
  "email_masked": "d***@example.com",
  "email_hash": "hmac_sha256:...",
  "email_encrypted": "enc:v1:..."
}
```

Uso:

- `email_encrypted`: recuperacao autorizada;
- `email_hash`: busca sem expor e-mail;
- `email_masked`: exibicao segura.

### 11.6 Entidades

IDs reais de entidades sao protegidos:

```json
{
  "id": "entity_ab12cd34",
  "id_hash": "hmac_sha256:...",
  "id_encrypted": "enc:v1:...",
  "display_name": "[protected]",
  "display_name_encrypted": "enc:v1:..."
}
```

### 11.7 API Keys

API keys:

- sao geradas com prefixo `mt_live_`;
- a chave completa aparece uma unica vez;
- apenas `prefix` e `key_hash` ficam armazenados;
- `key_hash` usa HMAC-SHA256 com `API_KEY_HASH_SECRET` ou `SECRET_KEY`;
- `scopes` controla quais endpoints a chave pode usar;
- `expires_at` permite vencimento configuravel;
- `last_used_at` e atualizado no uso da chave;
- chaves expiradas recebem status `expired` no primeiro uso apos o vencimento;
- hashes legados SHA-256 sao aceitos e migrados ao serem usados.

Escopos aceitos:

- `predictions:write` para `POST /predictions`;
- `predictions:batch` para `POST /predictions/batch`;
- `feedback:write` para `POST /predictions/{prediction_id}/feedback`;
- `exports:read` para uso futuro em exportacoes;
- `admin` para escopo amplo.

### 11.8 Auditoria E Redaction

Antes de persistir auditoria, a funcao `redact_sensitive` remove ou mascara:

- access token;
- refresh token;
- senha;
- hash de senha;
- segredos;
- API keys;
- key hash;
- autorizacao;
- cookie;
- e-mails;
- display names;
- campos criptografados.

### 11.9 Exportacoes Seguras

`ExportPayload` possui `redact_pii`, padrao `true`.

Quando ativo:

- IDs de entidade viram indices cegos;
- request IDs podem ser hasheados;
- features passam por redaction;
- explanations passam por redaction;
- JSON exportado remove identificadores sensiveis.

### 11.10 Postura De Seguranca

Endpoint:

```txt
GET /api/v1/security/posture
```

Verifica:

- chave dedicada de criptografia;
- chave dedicada de indice cego;
- hashing de senhas;
- API keys em HMAC;
- `SECRET_KEY` padrao;
- headers de seguranca;
- usuarios migrados.

### 11.11 Migracao De Dados Sensiveis

Endpoint:

```txt
POST /api/v1/security/migrate-sensitive-data
```

Executa:

- migracao de e-mails legados;
- migracao de alert e-mail em projetos;
- pseudonimizacao de entidades antigas;
- redaction de auditoria antiga;
- redaction de timeline de casos;
- contagem de API keys legadas que exigem rotacao.

Importante: configure chaves definitivas antes de migrar dados reais.

## 12. API REST

Base local em desenvolvimento:

```txt
http://127.0.0.1:8001/api/v1
```

Base Docker padrao:

```txt
http://localhost:8000/api/v1
```

### 12.1 Autenticacao

```txt
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
PATCH /auth/me
POST /auth/me/avatar
GET  /auth/me/avatar
POST /auth/resend-verification
POST /auth/verify-email
POST /auth/password-reset/request
POST /auth/password-reset/confirm
```

### 12.2 Projetos

```txt
GET    /projects
POST   /projects
GET    /projects/{project_id}
PATCH  /projects/{project_id}
DELETE /projects/{project_id}
GET    /projects/{project_id}/dashboard
GET    /projects/{project_id}/audit-events
```

### 12.3 Modelos

```txt
GET  /projects/{project_id}/models
POST /projects/{project_id}/models
GET  /models/{model_id}
GET  /models/{model_id}/versions
POST /models/{model_id}/versions
GET  /models/{model_id}/metrics
GET  /models/{model_id}/diagnostics
GET  /models/{model_id}/versions/compare?a=v1&b=v2
GET  /models/{model_id}/confusion-matrix
GET  /models/{model_id}/score-distribution
POST /models/{model_id}/drift/run
GET  /models/{model_id}/drift
GET  /models/{model_id}/bias-analysis?feature=feature_name
GET  /models/{model_id}/evaluations
```

### 12.4 Predicoes

```txt
POST /predictions
POST /predictions/batch
GET  /predictions
GET  /predictions/{prediction_id}
POST /predictions/{prediction_id}/feedback
POST /predictions/{prediction_id}/annotations
GET  /predictions/{prediction_id}/annotations
GET  /predictions/{prediction_id}/audit-trail
POST /predictions/{prediction_id}/whatif
POST /predictions/{prediction_id}/replay
GET  /predictions/{prediction_id}/replays
```

Filtros de `GET /predictions`:

```txt
project_id
model_id
model_version
label
score_band
entity_id
q
feedback_available
limit
skip
```

Autenticacao por API key:

- `POST /predictions` exige `predictions:write`;
- `POST /predictions/batch` exige `predictions:batch`;
- `POST /predictions/{prediction_id}/feedback` exige `feedback:write`;
- a API key so pode atuar no projeto ao qual pertence.

### 12.5 API Keys

```txt
GET    /projects/{project_id}/api-keys
POST   /projects/{project_id}/api-keys
DELETE /api-keys/{api_key_id}
```

Payload de criacao:

```json
{
  "name": "Ingestao operacional",
  "scopes": ["predictions:write", "predictions:batch", "feedback:write"],
  "expires_at": "2026-08-05T12:00:00.000Z"
}
```

### 12.6 Alertas

```txt
GET  /alert-rules
POST /alert-rules
PATCH /alert-rules/{rule_id}
DELETE /alert-rules/{rule_id}
GET  /alerts
POST /alerts/{alert_id}/acknowledge
POST /alerts/{alert_id}/resolve
POST /alerts/run-checks?project_id={project_id}
```

### 12.7 Produto Operacional

```txt
GET  /notifications
PATCH /notifications/{notification_id}
POST /notifications/mark-all-read
GET  /jobs
POST /jobs
GET  /saved-views
POST /saved-views
DELETE /saved-views/{view_id}
GET  /projects/{project_id}/entity-timeline
POST /projects/{project_id}/entity-notes
GET  /projects/{project_id}/data-contract
PATCH /projects/{project_id}/data-contract
```

Esses endpoints sustentam as telas `Automacao` e `Entidades`. Eles permitem acompanhar execucoes assincronas, receber notificacoes internas, salvar filtros de trabalho, consultar a linha do tempo de uma entidade e aplicar contratos de dados na ingestao.

### 12.8 Exportacoes

```txt
POST /exports
GET  /exports
GET  /exports/{export_id}
GET  /exports/{export_id}/download
```

### 12.9 Operacao

```txt
GET  /projects/{project_id}/operations
GET  /projects/{project_id}/intervention-cases
POST /intervention-cases/{case_id}/status
```

### 12.10 Seguranca

```txt
GET  /security/posture
POST /security/migrate-sensitive-data
```

## 13. Fluxos De Negocio

### 13.1 Fluxo De Onboarding

1. Usuario registra conta.
2. Organizacao e criada automaticamente.
3. Usuario recebe role `OWNER`.
4. Tokens sao emitidos.
5. Cookies `HttpOnly` sao configurados.
6. Usuario acessa workspace.

### 13.2 Fluxo De Configuracao De Modelo

1. Usuario cria projeto.
2. Usuario cria modelo.
3. Usuario informa features esperadas.
4. Usuario cria versao.
5. Versao pode ser `draft`, `staging`, `production` ou `deprecated`.
6. Usuario gera API key para ingestao.

### 13.3 Fluxo De Ingestao

1. Cliente envia `POST /predictions`.
2. API valida bearer token ou API key.
3. API valida projeto e organizacao.
4. API valida modelo e versao.
5. API verifica `request_id` para idempotencia.
6. API valida contrato de features do modelo e aplica o modo `accept`, `warn` ou `block`.
7. API protege PII.
8. API grava documento com o resultado do contrato em `metadata.contract`.
9. API invalida caches.
10. API atualiza contador do projeto.
11. API registra auditoria.

### 13.4 Fluxo De Feedback

1. Usuario seleciona predicao.
2. Usuario informa resultado real.
3. API calcula `tp`, `fp`, `tn` ou `fn`.
4. API atualiza `feedback`.
5. API invalida caches.
6. API recalcula metricas do modelo.
7. API registra auditoria.

### 13.5 Fluxo De DS Lab

1. Usuario seleciona modelo.
2. Frontend chama `/models/{id}/diagnostics`.
3. Backend verifica cache.
4. Se nao houver cache valido, calcula diagnosticos.
5. Resultado alimenta threshold tuning, calibracao, coverage, slices e erros.

### 13.6 Fluxo De Exportacao

1. Usuario solicita exportacao.
2. Backend normaliza filtros permitidos.
3. Backend busca predicoes.
4. Backend aplica redaction se `redact_pii=true`.
5. Arquivo CSV ou JSON e salvo em `backend/.data/exports`.
6. Documento `exports` e criado.
7. Evento de auditoria e criado.
8. Usuario baixa arquivo por endpoint autenticado.

## 14. Observabilidade De Modelos

### 14.1 Health Score

O health score mostrado na tela nao e acuracia pura. Ele resume prontidao operacional, considerando:

- base operacional pronta;
- taxa de feedback;
- recall quando existe feedback;
- alertas ativos;
- volume acionavel em relacao a capacidade operacional esperada.

Um modelo pode ter boa performance estatistica e health baixo se gerar excesso de casos acionaveis ou possuir alertas abertos.

### 14.2 Dashboard

Dashboard por projeto:

- total de predicoes;
- taxa acionavel;
- label positivo;
- taxa de feedback;
- score medio;
- alertas ativos;
- metricas de performance;
- matriz de confusao;
- histograma de score;
- serie temporal de volume;
- resumo por versao;
- predicoes criticas recentes;
- alertas.

### 14.3 Metric Snapshots

`metrics_snapshots` sao agregados por dia e versao:

- contagens;
- positivos/negativos;
- com feedback/sem feedback;
- matriz de confusao;
- performance;
- distribuicao de score.

### 14.4 Drift

Drift usa:

- PSI para distribuicao de score;
- comparacao simples de medias para features numericas.

Status:

- `stable`;
- `attention`;
- `drift_detected`;
- `insufficient_data`.

### 14.5 Bias Analysis

Analise por feature:

- agrupa predicoes por valor da feature;
- calcula total;
- positive rate;
- precision;
- recall.

Observacao: diferencas entre grupos nao provam causalidade nem vies por si so.

### 14.6 Comparacao De Versoes

Compara duas versoes do mesmo modelo:

- quantidade de predicoes;
- positive rate;
- score medio;
- feedback;
- matriz de confusao;
- deltas.

### 14.7 What-If

What-if estima mudancas no score a partir de alteracoes hipoteticas em features. Nao executa o modelo real. E uma simulacao aproximada baseada em impactos armazenados.

### 14.8 Replay

Replay registra uma simulacao de decisao com outra versao ou outro score. Ele guarda:

- decisao original;
- decisao simulada;
- features hipoteticas;
- se a decisao mudou;
- usuario criador.

## 15. Operacao Corporativa

### 15.1 Intervention Cases

Casos operacionais representam entidades que precisam de acompanhamento. Campos comuns:

- prioridade;
- score de risco;
- acao recomendada;
- status;
- timeline;
- outcome.

### 15.2 Incidents

Incidentes representam problemas operacionais:

- severidade;
- status;
- titulo;
- impacto;
- causa raiz.

### 15.3 Cohorts

Coortes agrupam entidades por criterio:

- janela;
- banda de risco;
- tipo de ativo;
- status;
- grupo operacional.

### 15.4 Data Quality Reports

Relatorios de qualidade registram:

- origem;
- total de linhas;
- total de entidades;
- colunas;
- missingness;
- checks;
- warnings;
- campos PII detectados;
- controles.

### 15.5 Model Cards

Model cards documentam:

- uso pretendido;
- uso proibido;
- contexto de treino;
- limitacoes;
- governanca;
- ciclo de revisao.

### 15.6 Approvals

Aprovacoes representam governanca formal de modelos, versoes ou cards.

## 16. Importacao De Dados Reais E Simulacao De Uso

### 16.1 Script Principal

Script:

```txt
scripts/import_tcc_gi_real_data.py
```

Comando:

```powershell
python scripts/import_tcc_gi_real_data.py --source tcc-full
```

O script:

- faz backup do store atual;
- recria `backend/.data/modeltrace.json`;
- copia artefatos do TCC;
- copia bases preprocessadas;
- executa modelos do TCC;
- gera predicoes;
- gera feedback quando existe desfecho;
- cria metricas;
- cria coortes;
- cria casos operacionais;
- cria model cards;
- cria relatorios de qualidade;
- importa projetos externos compativeis.

### 16.2 Fontes Usadas

Fontes esperadas:

```txt
D:\TCC - versao final
D:\alunos-vinculo-GI.pdf
D:\alunos-vinculo-GI.xlsx
C:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados
```

O script copia arquivos para `data/imported`, sem alterar os arquivos originais.

### 16.3 Projetos Importados

`TCC Student Outcomes Full Replay`:

- dominio: education;
- entidades: alunos;
- modelos: LR, RF, XGBoost, CatBoost, MLP;
- janelas: P1, P2, P4;
- usa registros completos para replay funcional.

`CNPJ Closure Risk Radar`:

- dominio: business;
- entidades: empresas;
- modelo: logistic_full calibrado;
- label positivo: `closure_risk`.

`Industrial Predictive Maintenance`:

- dominio: industrial;
- entidades: ativos;
- modelo: LightGBM;
- horizontes: 1h, 4h, 12h;
- label positivo: `event_risk`.

### 16.4 Caveat Metodologico

A carga `tcc-full` usa todos os registros completos disponiveis para demonstrar produto, incluindo treino, validacao e teste. Portanto, nao deve ser apresentada como estimativa imparcial de performance em producao. Ela serve para:

- testar plataforma;
- demonstrar NoSQL;
- simular monitoramento;
- validar UX;
- mostrar auditoria;
- exercitar dashboards.

## 17. Frontend E Experiencia De Usuario

### 17.1 Overview

Mostra:

- saude operacional;
- KPIs;
- grafico de score;
- serie temporal;
- matriz;
- detalhes clicaveis.

### 17.2 Monitor

Mostra:

- API key;
- acoes de refresh;
- drift;
- bias;
- comparacao rapida de versoes (lista textual);
- exportacoes.

### 17.2.0 Drift Heatmap

Aba dedicada (`activeView === "drift"`, atalho `G X`) que materializa o historico de drift como matriz feature x tempo.

Componentes:

- `frontend/components/views/DriftHeatmapView.tsx` (presentational);
- estado em `page.tsx`: `driftHeatmap`, `driftHeatmapLoading`;
- handler `refreshDriftHeatmap` chama `GET /models/{model_id}/drift/heatmap?limit=12`;
- `runDrift` (existente) recarrega o heatmap automaticamente apos novo relatorio.

Backend:

- `app/services/metrics.py` ganhou helper `_psi_continuous` (PSI em quantis igualitarios, funciona para qualquer feature continua) e `drift_status_from_psi`;
- `generate_drift_report` agora persiste PSI por feature em `data_drift.features[].psi`;
- novo endpoint `GET /models/{model_id}/drift/heatmap?limit=N` em `app/api/routes/models.py` pivota os ultimos N relatorios em formato `{ buckets, features, thresholds }`;
- `limit` aceita 1..36, default 12;
- relatorios com `status="insufficient_data"` sao excluidos.

Conteudo da tela:

- header com botoes `Atualizar` (apenas releitura) e `Rodar drift` (POST + atualizacao);
- 4 cartoes de sumario: Buckets, Features, Drift detectado, Atencao;
- legenda colorida com thresholds (`>= 0.10` atencao, `>= 0.25` drift);
- matriz principal com features em linhas (ordenadas por PSI maximo decrescente), buckets em colunas (mais antigos a esquerda);
- linha extra do `prediction.score` mostrando PSI top-level;
- celulas clicaveis com hover detalhado (CellDetail) mostrando feature, data, versao, PSI numerico e badge de tom.

A coloracao usa `color-mix(in srgb, ...)` para gerar tons translucidos sobre a superficie, evitando gradientes hardcoded.

### 17.2.1 Compare (Champion vs Challenger)

Aba dedicada (`activeView === "compare"`, atalho `G C`) que materializa um duelo visual entre duas versoes do mesmo modelo.

Componentes:

- `frontend/components/views/ChampionChallengerView.tsx` (presentational);
- estado em `page.tsx`: `comparisonResult`, `comparisonLoading`;
- handler `runChampionChallenger(a, b)` chama `GET /models/{model_id}/versions/compare?a=...&b=...`;
- handler `promoteChallenger(version)` chama `POST /models/{model_id}/versions/{version}/promote` apos confirmacao manual.

Conteudo da tela:

- seletor lado a lado para Champion e Challenger;
- aviso metodologico devolvido pelo backend;
- dois cartoes (`compare-card.champion` em verde, `compare-card.challenger` em accent) com algoritmo, status, predicoes, score medio, taxa positiva, com feedback, precision, recall, F1 e mini matriz de confusao;
- Trend (`Δ`) em cada metrica do challenger relativa ao champion (com `invert` quando "menor e melhor", como taxa positiva);
- destaque automatico de "vencendo" baseado em precision/recall/F1;
- bar chart `recharts` comparando todas as metricas em escala absoluta;
- botao `Promover challenger` que dispara o endpoint de promote, marca o champion atual como `deprecated`, atualiza `production_version_id` no modelo e registra `model_version.promoted` na auditoria.

A operacao de promote eh idempotente: se a versao alvo ja esta em production, o endpoint retorna `noop=true` e a UI exibe toast informativo.

### 17.3 DS Lab

Mostra:

- recomendacao de threshold;
- curva de metricas;
- calibracao;
- feature coverage;
- feature importance;
- slice diagnostics;
- falsos positivos;
- falsos negativos;
- exportacao de pacote tecnico.

### 17.4 Predicoes

Mostra:

- tabela paginada;
- filtros por label, versao, feedback e busca;
- inspector lateral;
- detalhes auditaveis;
- what-if;
- replay;
- feedback.

### 17.5 Operacao

Mostra:

- casos;
- alertas;
- incidentes;
- coortes;
- qualidade;
- avaliacoes.

### 17.5.2 Custo e Consumo

Aba dedicada (`activeView === "usage"`, atalho `G U`) com painel de FinOps por organizacao.

> **Patch v2.1.1 (PII):** Endpoint passa cada predicao por ``reveal_entity`` (de ``app.core.privacy``) antes de extrair o nome da entidade para o ranking de top entidades. Isso garante que usuario autenticado veja o ``id`` real (decifrado) em vez do sentinel literal ``[protected]`` que o storage retorna por padrao. Fallback final substitui ``[protected]`` residual por ``—`` caso a entidade nao tenha ``id`` decifravel.

Componentes:

- `frontend/components/views/CostUsageView.tsx` (presentational);
- estado em `page.tsx`: `usageData`, `usageLoading`, `usagePeriodDays`;
- handler `refreshUsage(days, accessToken)` chama `GET /usage/summary?days=N`;
- handler `changeUsagePeriod(days)` atualiza periodo e refresca em uma operacao;
- toggle de periodo: 7 / 14 / 30 / 60 / 90 dias.

Backend (novo arquivo `app/api/routes/usage.py`):

- endpoint `GET /usage/summary?days=N` com `days` em [7..90], default 30;
- agrega contagens de `predictions`, `audit_events`, `api_keys`, `projects`, `models` da org;
- monta serie diaria de predicoes e cobertura de feedback;
- calcula top 10 entidades por volume no periodo;
- estima custo via constantes `COST_PER_PREDICTION_BRL`, `COST_PER_API_CALL_BRL`, `COST_PER_GB_STORAGE_BRL`;
- estimativa de armazenamento via `predictions_total * AVG_PREDICTION_BYTES (1800)`;
- registrado em `backend/app/main.py` no array de routers.

Conteudo da tela:

- 5 KPIs no topo: Custo estimado (com projecao 30d), Predicoes no periodo (com sparkline), Audit events, API keys ativas, Armazenamento estimado;
- Area chart com volume diario de predicoes + linha de cobertura de feedback;
- Card de composicao do custo: barras horizontais para Predicoes, Audit events, Armazenamento + total destacado;
- Tabela top entidades com barra de proporcao;
- Card de pricing usado, com link para customizar via `usage.py`.

Em produto real, substituir as constantes pricing por consulta a tabela do provedor da infra (Mongo Atlas, S3, etc.) ou plano da org.

### 17.5.1 Casos (SLA Kanban)

Aba dedicada (`activeView === "cases"`, atalho `G S`) que materializa a fila de `intervention_cases` como um Kanban com SLA visual.

Componentes:

- `frontend/components/views/SlaKanbanView.tsx` (presentational);
- estado em `page.tsx`: reusa `operationsData.intervention_cases` (carregado por `refreshOperations`);
- handler `updateCaseStatus(caseId, nextStatus)` chama `POST /intervention-cases/{id}/status` (existente);
- handler de navegacao para entidade clicada faz `setEntityQuery(id) + setActiveView("entities")`.

Estrutura visual:

- 3 colunas: `A fazer` (statuses `open`, `assigned`), `Em andamento` (`in_progress`, `paused`), `Resolvido` (`resolved`, `dismissed`);
- cada coluna tem cor de topo dedicada (info / accent / success);
- 4 cartoes de sumario no topo: Total, Vencidos, Em risco, Resolvidos;
- ordem dentro da coluna: prioridade ascendente (`priority_rank`), depois `risk_score` decrescente;
- cada cartao mostra: entidade clicavel (link para timeline), id da entidade, badge de prioridade tonalizado (`critical`, `high`, `medium`, `low`), score, assignee se houver, summary, e barra de progresso de SLA;
- SLA computado via `due_at` ou `created_at + sla_hours` quando `due_at` falta;
- estados de SLA: `ontrack` (>= 25% do tempo), `atrisk` (< 25%), `breached` (vencido);
- acoes do cartao: botao primario (Iniciar / Resolver / Reabrir conforme coluna), botao secundario (Pausar) quando aplicavel, e botao discreto de Descartar.

Backend: nenhuma alteracao necessaria, todos os endpoints ja existem.

### 17.6 Workbench

Permite registrar predicao com formulario dinamico. O usuario nao precisa escrever JSON.

O Workbench valida projeto, modelo, versao, entidade, score e features obrigatorias antes de enviar. Quando existe falha, a tela mostra os erros e nao chama a API.

### 17.7 Governanca

Mostra:

- audit trail;
- filtro e exportacao de evidencias de auditoria;
- API keys com escopos, expiracao, ultimo uso e revogacao;
- mapa NoSQL;
- postura de seguranca;
- botao de migracao de dados sensiveis.

### 17.8 Docs

A aba `Docs` e a documentacao de usuario dentro do produto. Ela organiza cada topico em:

- para que serve;
- como usar;
- o que entrega;
- o que nao faz;
- topicos relacionados.

Topicos cobertos:

- Comece aqui;
- Conceitos;
- Overview;
- Monitor;
- DS Lab;
- Predicoes;
- Decision inspector;
- Operacao;
- Workbench;
- Governanca;
- API;
- Limites atuais.

### 17.9 Command Palette

O botao `Comandos` abre uma busca de acoes, telas e documentos. A nova versao implementada em `components/shell/CommandPalette.tsx` e um componente dedicado com:

- atalho de teclado real `Cmd+K` / `Ctrl+K`;
- navegacao por setas `↑` / `↓`;
- selecao com `Enter`;
- fechamento com `Esc` ou clique fora;
- busca incremental com filtro por label, detalhe e grupo;
- footer com legenda de atalhos visiveis.

A command palette pode:

- abrir views (mesmo efeito de `G + tecla`);
- executar refresh, drift, alertas e exportacoes;
- abrir topicos especificos de documentacao;
- exportar evidencias de auditoria.

### 17.9.1 SLA Alert Bar (cross-view)

Barra horizontal renderizada em qualquer view (exceto a aba `Casos`) entre o `status-ribbon` e o conteudo, sempre que existem casos com SLA estourado ou em risco.

Componente: `frontend/components/shell/SlaAlertBar.tsx`.

Comportamento:

- usa o mesmo `interventionCases` ja carregado pelo `refreshOperations`, sem chamada adicional;
- diferencia dois tons: `danger` quando ha pelo menos um caso vencido, `warning` quando so ha casos em risco;
- `em risco` = SLA com menos de 6h restantes;
- mostra titulo, contagem agregada e o nome do proximo caso a vencer com tempo humanizado;
- botao `Ir para fila` chama `setActiveView("cases")`;
- botao `X` dispensa a barra ate o proximo refresh do componente (state local).

Esta barra existe para que operadores trabalhando em DS Lab, Predicoes ou outras telas nao percam casos criticos.

### 17.10 Notifications Hub

O painel de notificacoes (`components/shell/NotificationsDrawer.tsx`) e um drawer lateral de 440px.

Funcionalidades:

- abertura via botao `Notificacoes` no topbar (com badge numerico) ou atalho `Cmd+/` / `Ctrl+/`;
- tabs com contadores: Todas, Nao lidas, Alertas, Jobs, Sistema;
- marca todas como lidas em massa (`Mark All Read`);
- deep-link automatico ao clicar em uma notificacao:
  - `resource_type=alert` ou `incident` → leva a Operacao com filtro ativo;
  - `resource_type=prediction` → abre Predicoes;
  - `resource_type=job` → abre Automacao;
  - `resource_type=intervention_case` → abre Kanban de Casos;
  - demais → abre Automacao com listagem geral.
- estilo visual com tom semantico (success/warn/error/info);
- itens nao lidos recebem gradient suave de destaque.

Contrato com o backend (corrigido na v2.1):

- a flag de leitura no banco e `read_at` (timestamp), nao `read` (boolean);
- helper `isRead(notification) = Boolean(notification.read_at) || notification.read === true` no frontend;
- endpoints usados:
  - `PATCH /notifications/{id}` com body `{ read: true }` para marcar individual;
  - `POST /notifications/mark-all-read` para batch atomico (uma round-trip, retorna `{updated: N}`);
- ao clicar em uma notificacao nao lida, `markNotificationRead` e disparado em paralelo com a navegacao para deep-link, com optimistic update local.

### 17.11 Light Theme E Tema Persistido

Hook `useTheme` (`components/hooks/useTheme.ts`) gerencia o tema atual.

- valores: `dark` (default) ou `light`;
- persistencia em `localStorage` chave `modeltrace_theme`;
- respeita `prefers-color-scheme: light` no primeiro carregamento se nao houver preferencia salva;
- aplica `data-theme="..."` no `<html>` durante o `useEffect` (evita flash em re-render);
- aplica classe transitoria `theme-transition-disable` por 60ms para suprimir transicoes globais e evitar flicker generalizado ao trocar.

Anti-FOUC: `app/layout.tsx` injeta um `<Script id="modeltrace-theme-boot" strategy="beforeInteractive">` que le `localStorage` e seta `data-theme` antes do paint inicial.

Botao de toggle: icone Sol/Lua no `Topbar`, com `aria-pressed` refletindo o estado. Atalho global `T` tambem alterna.

Os tokens de light theme ficam em `[data-theme="light"]` no `globals.css` (escala de superficies, bordas, texto). Ajustes adicionais em `body`, `pre`, `auth-product`, `toast`, `command-palette`, `notif-drawer`, `key-box`, `health-ring`, `recharts-default-tooltip` e `kbd` foram adicionados em camada `6.5 THEME TRANSITION + LIGHT REFINEMENTS` no fim do arquivo.

### 17.12 Onboarding Tour

`components/shell/OnboardingTour.tsx` e um modal multi-step com 7 passos cobrindo as features-chave do produto.

Comportamento:

- aparece automaticamente apos login bem-sucedido ou ao restaurar sessao da `sessionStorage`, somente quando `localStorage.modeltrace_onboarding_v2 !== "completed"`;
- versionamento via `_v2` no nome da chave: bump para `_v3` reabre o tour para todos quando features importantes chegarem;
- helpers exportados: `shouldShowOnboarding()`, `dismissOnboarding()`, `resetOnboarding()`;
- navegacao: `←` `→` setas, dots clicaveis, botoes `Voltar` / `Proximo` / `Pular`;
- alguns passos tem CTA `Abrir <view>` que navega direto para a aba relacionada e fecha o tour;
- pode ser reaberto via comando `Reabrir tour de boas-vindas` na command palette.

Os 7 passos:

1. Welcome (visao geral + 30+ colecoes);
2. Overview (health + KPIs);
3. Compare (Champion vs Challenger);
4. Drift (heatmap por feature);
5. Casos (SLA Kanban);
6. Atalhos de teclado;
7. Governanca (segurança e auditoria).

### 17.11 Atalhos De Teclado

A partir da versao 2 o produto tem atalhos completos estilo Gmail/GitHub. O hook responsavel e `components/hooks/useKeyboardShortcuts.ts`.

Atalhos globais:

- `Cmd+K` / `Ctrl+K` → command palette;
- `Cmd+/` / `Ctrl+/` → notifications drawer;
- `?` → modal com lista completa de atalhos;
- `R` → atualizar workspace;
- `T` → alternar tema (claro/escuro);
- `Shift+Q` → sair.

Navegacao por aba (prefixo `G`):

- `G O` → Overview;
- `G M` → Monitor;
- `G C` → Compare (Champion vs Challenger);
- `G X` → Drift Heatmap;
- `G L` → DS Lab;
- `G P` → Predicoes;
- `G Q` → Operacao;
- `G S` → Casos (SLA Kanban);
- `G U` → Custo & Consumo;
- `G E` → Entidades;
- `G A` → Automacao;
- `G W` → Workbench;
- `G V` → Governanca;
- `G D` → Docs.

Comportamento:

- atalhos sem modificador sao ignorados quando o foco esta em `<input>`, `<textarea>`, `<select>` ou `contenteditable`;
- prefixo `G` aguarda a segunda tecla por 1.2 segundos e expira sozinho;
- `Cmd+K` e `Cmd+/` funcionam mesmo dentro de inputs;
- modais e drawers abertos respondem a `Esc`.

A interface mostra os atalhos diretamente:

- na sidebar, ao lado de cada item de navegacao;
- no botao `Comandos` do topbar (`⌘ K` visivel);
- no modal de ajuda (`?`), agrupado por: Paineis, Acoes rapidas, Navegacao.

## 18. Configuracao E Execucao

### 18.1 Backend Local

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### 18.2 Frontend Local

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\frontend"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Ou build de producao:

```powershell
npm run build
npm run start -- --hostname 127.0.0.1 --port 3000
```

### 18.3 Login Demo

```txt
Email: diegohenrique.mail@gmail.com
Senha: D1eg0X@vi3rHUB
```

### 18.4 MongoDB Local

```powershell
$env:MONGODB_URL="mongodb://localhost:27017"
$env:MONGODB_DB_NAME="modeltrace"
```

### 18.5 MongoDB Atlas

```powershell
$env:MONGODB_URL="mongodb+srv://usuario:senha@cluster.mongodb.net"
$env:MONGODB_DB_NAME="modeltrace"
```

### 18.6 Variaveis De Producao Recomendadas

```powershell
$env:ENVIRONMENT="production"
$env:SECRET_KEY="gere-um-segredo-longo"
$env:FIELD_ENCRYPTION_KEY="gere-outro-segredo-longo"
$env:PII_HASH_KEY="gere-outro-segredo-longo"
$env:PASSWORD_PEPPER="gere-outro-segredo-longo"
$env:API_KEY_HASH_SECRET="gere-outro-segredo-longo"
$env:COOKIE_SECURE="true"
$env:CORS_ORIGINS="https://seu-front-end.com"
$env:ALLOWED_HOSTS="sua-api.com"
```

## 19. Testes E Validacao

### 19.1 Backend

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\backend"
python -m pytest
```

O teste principal cobre:

- health check;
- cadastro;
- cookie auth;
- projeto;
- modelo;
- versoes;
- API key;
- predicao via API key;
- idempotencia;
- feedback;
- dashboard;
- postura de seguranca;
- anotacao;
- what-if;
- replay;
- comparacao de versoes;
- bias;
- drift;
- alertas;
- exportacao segura;
- migracao de seguranca.

### 19.2 Frontend

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\frontend"
npm run lint
npm run build
```

### 19.3 Importador

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL"
python -m py_compile scripts/import_tcc_gi_real_data.py
```

### 19.4 Health Check

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8001/health
```

Resposta esperada:

```json
{
  "status": "ok",
  "app": "ModelTrace",
  "store": "json"
}
```

## 20. Deploy

### 20.1 Docker Compose

```powershell
docker compose up --build
```

Servicos:

- frontend: `http://localhost:3000`;
- backend: `http://localhost:8000`;
- MongoDB: `localhost:27017`;
- Redis: `localhost:6379`.

### 20.2 Observacoes Sobre Docker

O `docker-compose.yml` usa:

- `mongo:7`;
- `redis:7-alpine`;
- build local do backend;
- build local do frontend;
- `MONGODB_URL=mongodb://mongodb:27017`;
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`.

### 20.3 Deploy Real

Para ambiente real:

- usar HTTPS no proxy;
- usar MongoDB gerenciado;
- configurar segredos fora do codigo;
- configurar backups;
- configurar logs centralizados;
- configurar CORS restrito;
- configurar ALLOWED_HOSTS;
- usar `COOKIE_SECURE=true`;
- desativar docs em producao com `ENVIRONMENT=production`;
- rotacionar API keys;
- executar migracao de seguranca apos definir chaves finais.

## 21. Operacao, Manutencao E Governanca

### 21.1 Rotina Recomendada

Diaria:

- verificar alertas;
- verificar volume de predicoes;
- verificar falhas de feedback;
- verificar casos operacionais.

Semanal:

- executar drift;
- revisar slices;
- revisar feature coverage;
- revisar falsos positivos e falsos negativos;
- verificar postura de seguranca.

Mensal:

- revisar model cards;
- comparar versoes;
- revisar thresholds;
- avaliar necessidade de retreino;
- rotacionar chaves quando necessario.

### 21.2 Backup

Modo JSON:

- arquivo principal: `backend/.data/modeltrace.json`;
- backups do importador: `backups/`.

Modo MongoDB:

- usar backup nativo do provedor;
- manter indices;
- considerar TTL/retencao conforme LGPD e politica interna.

### 21.3 Retencao

Organizacoes e projetos possuem configuracoes como:

- `retention_days`;
- limites de predicoes;
- maximo de projetos;
- habilitacao de drift;
- habilitacao de webhooks.

Retencao automatica ainda nao esta implementada como job, mas o modelo ja possui campo para isso.

## 22. Decisoes De Arquitetura

### 22.1 Por Que FastAPI

- rapido para APIs;
- tipagem clara com Pydantic;
- boa documentacao Swagger;
- facil para testes;
- adequado para servicos de ML.

### 22.2 Por Que Next.js

- bom ecossistema React;
- build otimizado;
- facil componentizacao;
- boa experiencia para dashboard.

### 22.3 Por Que DocumentStore

A abstracao permite:

- rodar sem MongoDB em ambiente de faculdade;
- migrar para MongoDB real;
- testar com JSON local;
- preservar contrato das rotas.

### 22.4 Por Que Cache Materializado

Dashboards e diagnosticos podem exigir leitura de milhares de predicoes. `dashboard_cache` e `diagnostic_cache` reduzem latencia em telas interativas.

### 22.5 Por Que Redaction Por Padrao

Como o sistema manipula dados reais, auditoria e exportacoes nao devem vazar PII ou segredos. O produto escolhe seguranca por padrao.

## 23. Limitacoes Conhecidas

- RBAC fino por endpoint ainda pode ser expandido.
- Nao ha fila real para jobs longos.
- Redis esta no compose, mas nao e usado extensivamente no codigo atual.
- What-if e aproximado, nao executa modelo real.
- Drift e estatistico simples, nao substitui monitoramento avancado.
- Store JSON e util para demo, mas MongoDB e recomendado para producao.
- Retencao automatica ainda nao possui job agendado.
- Exportacoes ficam em disco local no modo JSON.
- Webhooks estao previstos na modelagem, mas nao implementados como fluxo completo.

## 24. Roadmap Recomendado

Evolucoes de produto:

- RBAC completo por role e permissao de projeto;
- organizacoes multiusuario no front;
- convite de usuarios;
- jobs assicronos para drift, diagnosticos e exportacoes grandes;
- integracao real com storage de artefatos de modelo;
- webhooks configuraveis;
- notificacoes por e-mail;
- retencao automatica;
- logs estruturados;
- observabilidade com OpenTelemetry;
- dashboards customizaveis;
- suporte formal a regressao, ranking e forecasting na UI;
- gestao de experimentos;
- model registry com approvals obrigatorios;
- data contracts versionados;
- comparacao entre treino, validacao, teste e producao;
- monitoramento de custo/latencia por modelo;
- trilha LGPD com finalidade, base legal e prazo de retencao;
- secrets manager externo;
- rotacao automatica de API keys.

## Referencias Internas

- README principal: [`../README.md`](../README.md)
- API resumida: [`api.md`](api.md)
- Arquitetura resumida: [`architecture.md`](architecture.md)
- Manual funcional da interface: [`manual-funcionalidades.md`](manual-funcionalidades.md)
- Melhorias para produto real: [`melhorias-produto-real.md`](melhorias-produto-real.md)
- Modelagem NoSQL resumida: [`data-model.md`](data-model.md)
- Modelagem documental em JSON: [`modelagem-banco-json.md`](modelagem-banco-json.md)
- JSON simplificado: [`modelagem-json-simplificada.json`](modelagem-json-simplificada.json)
- JSON completo: [`modelagem-json-completa.json`](modelagem-json-completa.json)
- Diagramas ER simplificado e completo: [`modelagem-banco-er.md`](modelagem-banco-er.md)
- Diagrama ER SVG legado: [`modeltrace-er.svg`](modeltrace-er.svg)
