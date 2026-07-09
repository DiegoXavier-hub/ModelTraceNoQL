# ModelTrace - Guia Completo Da API

Este guia explica como consumir a API do ModelTrace em um fluxo real. A documentacao anterior listava os endpoints de forma resumida; este documento descreve o uso de ponta a ponta, com exemplos de payload, `curl`, PowerShell, Python e TypeScript.

O ModelTrace expoe uma API REST sob o prefixo `/api/v1`. Em desenvolvimento local, considerando a configuracao atual deste projeto, a base usada pelo front-end e pela API e:

```txt
http://127.0.0.1:8001/api/v1
```

Se o projeto estiver rodando via Docker na porta padrao, a base normalmente sera:

```txt
http://localhost:8000/api/v1
```

Os exemplos abaixo usam `http://127.0.0.1:8001/api/v1`. Se voce estiver usando outra porta, troque apenas a variavel `BASE_URL`.

Documentacao relacionada:

- documentacao completa do software: [`documentacao-software.md`](documentacao-software.md);
- manual funcional da interface: [`manual-funcionalidades.md`](manual-funcionalidades.md);
- modelagem NoSQL: [`data-model.md`](data-model.md);
- evolucao para produto real: [`melhorias-produto-real.md`](melhorias-produto-real.md).

## 1. Conceito Geral

A API foi desenhada para registrar decisoes de modelos de Machine Learning em producao. Cada predicao recebida vira um documento na colecao `predictions`. Esse documento guarda a entidade avaliada, as features usadas pelo modelo, o score, o label, o threshold, a decisao operacional, explicacoes, metadata tecnica e, depois, feedback real quando o desfecho fica disponivel.

O fluxo mais comum em uma empresa e este: primeiro um usuario autentica no ModelTrace e cria o projeto, o modelo e a versao do modelo. Depois ele cria uma API key do projeto. A partir dai, um sistema externo, pipeline ou servico de scoring usa essa API key para enviar predicoes. Quando o desfecho real chega em outro sistema, a propria empresa pode enviar feedback para a predicao. O ModelTrace usa esses registros para dashboards, matriz de confusao, DS Lab, alertas, drift, auditoria e exportacoes.

A API aceita dois tipos de credencial. O token de usuario, retornado no login, serve para operacao administrativa e uso pela interface. A API key, criada por projeto, serve para integracoes externas. API keys nunca sao armazenadas em texto puro; o back-end guarda apenas hash HMAC, prefixo, escopos, expiracao e metadados.

## 2. Preparando Variaveis De Ambiente Para Os Exemplos

Em PowerShell, configure a URL base assim:

```powershell
$BASE_URL = "http://127.0.0.1:8001/api/v1"
```

Em Bash, Linux, macOS ou Git Bash:

```bash
BASE_URL="http://127.0.0.1:8001/api/v1"
```

Em Python:

```python
BASE_URL = "http://127.0.0.1:8001/api/v1"
```

Em TypeScript ou JavaScript:

```ts
const BASE_URL = "http://127.0.0.1:8001/api/v1";
```

## 3. Autenticacao

Para operar o ModelTrace como usuario, voce precisa criar conta ou fazer login. O cadastro cria um usuario e uma organizacao. O login retorna `access_token`, `refresh_token` e os dados do usuario. O `access_token` deve ser enviado no header `Authorization` como Bearer token.

### 3.1 Criar Conta

Use `POST /auth/register` quando ainda nao existir usuario local.

```bash
curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Diego Xavier",
    "email": "diegohenrique.mail@gmail.com",
    "password": "D1eg0X@vi3rHUB",
    "organization_name": "Projeto NoSQL"
  }'
```

Em PowerShell:

```powershell
$registerBody = @{
  name = "Diego Xavier"
  email = "diegohenrique.mail@gmail.com"
  password = "D1eg0X@vi3rHUB"
  organization_name = "Projeto NoSQL"
} | ConvertTo-Json

$session = Invoke-RestMethod "$BASE_URL/auth/register" `
  -Method Post `
  -ContentType "application/json" `
  -Body $registerBody

$TOKEN = $session.access_token
```

Se o usuario ja existir, use login.

### 3.2 Fazer Login

```bash
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "diegohenrique.mail@gmail.com",
    "password": "D1eg0X@vi3rHUB"
  }'
```

Em PowerShell:

```powershell
$loginBody = @{
  email = "diegohenrique.mail@gmail.com"
  password = "D1eg0X@vi3rHUB"
} | ConvertTo-Json

$session = Invoke-RestMethod "$BASE_URL/auth/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body $loginBody

$TOKEN = $session.access_token
$AUTH = @{ Authorization = "Bearer $TOKEN" }
```

O objeto retornado tem esta estrutura geral:

```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "user": {
    "_id": "usr_xxx",
    "org_id": "org_xxx",
    "name": "Diego Xavier",
    "email": "diegohenrique.mail@gmail.com",
    "role": "OWNER"
  }
}
```

### 3.3 Consultar Usuario Atual

Depois de obter o token, voce pode validar a sessao em `GET /auth/me`.

```bash
curl "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

Em PowerShell:

```powershell
Invoke-RestMethod "$BASE_URL/auth/me" -Headers $AUTH
```

### 3.4 Renovar Sessao E Sair

`POST /auth/refresh` usa o refresh token para gerar novo access token. Quando a aplicacao esta usando cookies `HttpOnly`, o refresh token pode vir do cookie `modeltrace_refresh`. Em clientes externos, voce tambem pode enviar `refresh_token` no corpo.

```bash
curl -X POST "$BASE_URL/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "jwt_refresh_token"
  }'
```

`POST /auth/logout` encerra a sessao no cliente e limpa cookies emitidos pela API.

```bash
curl -X POST "$BASE_URL/auth/logout" \
  -H "Authorization: Bearer $TOKEN"
```

## 4. Projetos

Um projeto representa o produto, area, caso de uso ou dominio que esta sendo monitorado. Exemplos: evasao academica, churn, fraude, manutencao industrial, risco de fechamento de empresas ou anomalias em transacoes.

### 4.1 Criar Projeto

Use `POST /projects` com token de usuario.

```bash
curl -X POST "$BASE_URL/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Industrial Predictive Maintenance",
    "description": "Monitoramento de risco de eventos em ativos industriais.",
    "problem_type": "binary_classification",
    "domain": "industrial",
    "tags": ["maintenance", "operations"],
    "default_threshold": 0.70,
    "bias_sensitive_features": ["shift", "site"]
  }'
```

Em PowerShell:

```powershell
$projectBody = @{
  name = "Industrial Predictive Maintenance"
  description = "Monitoramento de risco de eventos em ativos industriais."
  problem_type = "binary_classification"
  domain = "industrial"
  tags = @("maintenance", "operations")
  default_threshold = 0.70
  bias_sensitive_features = @("shift", "site")
} | ConvertTo-Json

$project = Invoke-RestMethod "$BASE_URL/projects" `
  -Method Post `
  -Headers $AUTH `
  -ContentType "application/json" `
  -Body $projectBody

$PROJECT_ID = $project._id
```

O retorno contem o `_id` do projeto. Esse ID sera usado nos proximos passos.

### 4.2 Listar Projetos

```bash
curl "$BASE_URL/projects" \
  -H "Authorization: Bearer $TOKEN"
```

O retorno vem no formato:

```json
{
  "items": [
    {
      "_id": "proj_xxx",
      "name": "Industrial Predictive Maintenance",
      "domain": "industrial",
      "status": "active"
    }
  ]
}
```

### 4.3 Recuperar, Atualizar E Arquivar Projeto

Para recuperar um projeto:

```bash
curl "$BASE_URL/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Para atualizar campos simples, use `PATCH /projects/{project_id}`:

```bash
curl -X PATCH "$BASE_URL/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Projeto industrial em operacao assistida.",
    "status": "active"
  }'
```

Para arquivar, tambem use `PATCH` com `status = "archived"`, ou `DELETE /projects/{project_id}` quando quiser remover o projeto no ambiente local.

## 5. Modelos

Um modelo representa uma familia de decisao. Ele guarda tipo de problema, nome do target, labels, threshold padrao, metrica primaria e contrato esperado de features. Esse contrato e importante porque a UI usa `expected_features` para montar formularios dinamicos, e o back-end usa essas features em alertas de qualidade e diagnosticos.

### 5.1 Criar Modelo

Use `POST /projects/{project_id}/models`.

```bash
curl -X POST "$BASE_URL/projects/$PROJECT_ID/models" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DontGo Event Risk",
    "description": "Classificador de risco operacional para eventos de manutencao.",
    "problem_type": "binary_classification",
    "target_name": "event_risk",
    "labels": {
      "positive": "event_risk",
      "negative": "normal_operation"
    },
    "default_threshold": 0.50,
    "primary_metric": "average_precision",
    "expected_features": [
      { "name": "n_evt_1h", "type": "numeric", "required": true },
      { "name": "n_crit_1h", "type": "numeric", "required": true },
      { "name": "shift", "type": "categorical", "required": false },
      { "name": "site", "type": "categorical", "required": false }
    ]
  }'
```

Em PowerShell:

```powershell
$modelBody = @{
  name = "DontGo Event Risk"
  description = "Classificador de risco operacional para eventos de manutencao."
  problem_type = "binary_classification"
  target_name = "event_risk"
  labels = @{
    positive = "event_risk"
    negative = "normal_operation"
  }
  default_threshold = 0.50
  primary_metric = "average_precision"
  expected_features = @(
    @{ name = "n_evt_1h"; type = "numeric"; required = $true },
    @{ name = "n_crit_1h"; type = "numeric"; required = $true },
    @{ name = "shift"; type = "categorical"; required = $false },
    @{ name = "site"; type = "categorical"; required = $false }
  )
} | ConvertTo-Json -Depth 8

$model = Invoke-RestMethod "$BASE_URL/projects/$PROJECT_ID/models" `
  -Method Post `
  -Headers $AUTH `
  -ContentType "application/json" `
  -Body $modelBody

$MODEL_ID = $model._id
```

### 5.2 Listar Modelos De Um Projeto

```bash
curl "$BASE_URL/projects/$PROJECT_ID/models" \
  -H "Authorization: Bearer $TOKEN"
```

### 5.3 Recuperar Um Modelo

```bash
curl "$BASE_URL/models/$MODEL_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## 6. Versoes De Modelo

Toda predicao precisa apontar para uma versao. A versao documenta algoritmo, status, features, hiperparametros, metadata de treino, metricas offline, changelog e notas. O status pode ser `draft`, `staging`, `production` ou `deprecated`.

### 6.1 Criar Versao

Use `POST /models/{model_id}/versions`.

```bash
curl -X POST "$BASE_URL/models/$MODEL_ID/versions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "h12",
    "algorithm": "LightGBM",
    "status": "production",
    "features": ["n_evt_1h", "n_crit_1h", "shift", "site"],
    "hyperparameters": {
      "num_leaves": 31,
      "learning_rate": 0.05
    },
    "training_metadata": {
      "dataset": "maintenance_2025",
      "train_period": "2025-01-01/2025-05-31"
    },
    "offline_metrics": {
      "average_precision": 0.81,
      "recall": 0.72,
      "precision": 0.44
    },
    "changelog": "Primeira versao em producao.",
    "notes": "Threshold inicial calibrado para capacidade operacional."
  }'
```

Quando uma nova versao e criada com `status = "production"`, a versao anterior em producao do mesmo modelo e marcada como `deprecated`.

### 6.2 Listar Versoes

```bash
curl "$BASE_URL/models/$MODEL_ID/versions" \
  -H "Authorization: Bearer $TOKEN"
```

### 6.3 Comparar Versoes

`GET /models/{model_id}/versions/compare` compara duas versoes usando as predicoes online registradas para cada versao.

```bash
curl "$BASE_URL/models/$MODEL_ID/versions/compare?a=h4&b=h12" \
  -H "Authorization: Bearer $TOKEN"
```

O retorno inclui resumo online de cada versao e deltas de volume, score medio e taxa acionavel.

### 6.4 Avaliacoes De Modelo

`GET /models/{model_id}/evaluations` retorna avaliacoes registradas para o modelo. Esses documentos sao usados pela aba Operacao para mostrar ranking champion/challenger, metricas offline e simulacao de producao.

```bash
curl "$BASE_URL/models/$MODEL_ID/evaluations" \
  -H "Authorization: Bearer $TOKEN"
```

## 7. API Keys

API keys sao usadas por pipelines e sistemas externos. Elas pertencem a um projeto. A chave completa aparece apenas no momento da criacao. Depois disso, a API mostra apenas prefixo, status, escopos, expiracao e ultimo uso.

### 7.1 Criar API Key

Use `POST /projects/{project_id}/api-keys` com token de usuario.

```bash
curl -X POST "$BASE_URL/projects/$PROJECT_ID/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pipeline de producao",
    "scopes": ["predictions:write", "predictions:batch", "feedback:write"],
    "expires_at": "2026-08-05T12:00:00.000Z"
  }'
```

Em PowerShell:

```powershell
$keyBody = @{
  name = "Pipeline de producao"
  scopes = @("predictions:write", "predictions:batch", "feedback:write")
  expires_at = "2026-08-05T12:00:00.000Z"
} | ConvertTo-Json

$keyResponse = Invoke-RestMethod "$BASE_URL/projects/$PROJECT_ID/api-keys" `
  -Method Post `
  -Headers $AUTH `
  -ContentType "application/json" `
  -Body $keyBody

$API_KEY = $keyResponse.api_key
```

O retorno tem o formato:

```json
{
  "api_key": "mt_live_valor_completo_exibido_uma_vez",
  "record": {
    "_id": "key_xxx",
    "project_id": "proj_xxx",
    "prefix": "mt_live_abcd",
    "hash_algorithm": "hmac_sha256",
    "scopes": ["predictions:write", "predictions:batch", "feedback:write"],
    "expires_at": "2026-08-05T12:00:00.000Z",
    "last_used_at": null,
    "status": "active"
  }
}
```

Os escopos aceitos sao:

```txt
predictions:write   permite POST /predictions
predictions:batch   permite POST /predictions/batch
feedback:write      permite POST /predictions/{id}/feedback
exports:read        reservado para leitura de exportacoes
admin               escopo amplo
```

### 7.2 Listar API Keys

```bash
curl "$BASE_URL/projects/$PROJECT_ID/api-keys" \
  -H "Authorization: Bearer $TOKEN"
```

### 7.3 Revogar API Key

```bash
curl -X DELETE "$BASE_URL/api-keys/$API_KEY_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Revogar uma chave nao apaga seu registro; altera o status para `revoked`, preservando auditoria e rastreabilidade.

## 8. Enviar Predicoes

`POST /predictions` e o endpoint central de ingestao. Ele pode ser usado com token de usuario ou com API key do projeto. Em integracoes reais, o normal e usar API key com escopo `predictions:write`.

O payload precisa conter `project_id`, `model_id`, `model_version`, `entity_id`, `features` e `prediction`. O campo `metadata.request_id` e recomendado para idempotencia. Se uma predicao com o mesmo `request_id` ja existir, a API retorna `409 Conflict`.

Antes de gravar a predicao, o backend valida o contrato de features configurado no modelo. Se o projeto estiver em modo `accept`, a violacao fica registrada em `metadata.contract` e a predicao entra normalmente. Em modo `warn`, a predicao tambem entra, mas o status do contrato fica visivel para diagnostico. Em modo `block`, features obrigatorias ausentes, tipos incompatíveis ou valores fora da faixa podem gerar `422 Unprocessable Entity` com o relatorio de contrato no campo `detail.contract`.

### 8.1 Predicao Unica Com API Key

```bash
curl -X POST "$BASE_URL/predictions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'"$PROJECT_ID"'",
    "model_id": "'"$MODEL_ID"'",
    "model_version": "h12",
    "entity_id": "asset_793D4S",
    "entity_type": "industrial_asset",
    "entity_display_name": "793-D 4S",
    "features": {
      "n_evt_1h": 89,
      "n_crit_1h": 41,
      "shift": "night",
      "site": "mine_a"
    },
    "prediction": {
      "label": "event_risk",
      "score": 0.82,
      "threshold": 0.50
    },
    "explanations": [
      {
        "feature": "n_evt_1h",
        "value": 89,
        "impact": 0.31,
        "direction": "risk_up",
        "rank": 1
      },
      {
        "feature": "n_crit_1h",
        "value": 41,
        "impact": 0.22,
        "direction": "risk_up",
        "rank": 2
      }
    ],
    "decision": {
      "action": "human_review",
      "status": "triggered",
      "reason": "score_above_threshold"
    },
    "metadata": {
      "request_id": "req_asset_793D4S_20260601T090000Z",
      "source_system": "scoring_service",
      "environment": "production"
    }
  }'
```

Em PowerShell:

```powershell
$predictionBody = @{
  project_id = $PROJECT_ID
  model_id = $MODEL_ID
  model_version = "h12"
  entity_id = "asset_793D4S"
  entity_type = "industrial_asset"
  entity_display_name = "793-D 4S"
  features = @{
    n_evt_1h = 89
    n_crit_1h = 41
    shift = "night"
    site = "mine_a"
  }
  prediction = @{
    label = "event_risk"
    score = 0.82
    threshold = 0.50
  }
  explanations = @(
    @{ feature = "n_evt_1h"; value = 89; impact = 0.31; direction = "risk_up"; rank = 1 },
    @{ feature = "n_crit_1h"; value = 41; impact = 0.22; direction = "risk_up"; rank = 2 }
  )
  decision = @{
    action = "human_review"
    status = "triggered"
    reason = "score_above_threshold"
  }
  metadata = @{
    request_id = "req_asset_793D4S_20260601T090000Z"
    source_system = "scoring_service"
    environment = "production"
  }
} | ConvertTo-Json -Depth 10

$predictionResult = Invoke-RestMethod "$BASE_URL/predictions" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $API_KEY" } `
  -ContentType "application/json" `
  -Body $predictionBody

$PREDICTION_ID = $predictionResult.prediction_id
```

O retorno inclui o ID da predicao:

```json
{
  "prediction_id": "pred_xxx",
  "status": "recorded",
  "prediction": {
    "_id": "pred_xxx",
    "project_id": "proj_xxx",
    "model_id": "model_xxx",
    "model_version": "h12"
  }
}
```

### 8.2 Enviar Lote De Predicoes

`POST /predictions/batch` aceita ate 500 itens por requisicao. Esse endpoint usa escopo `predictions:batch` quando a credencial e API key.

```bash
curl -X POST "$BASE_URL/predictions/batch" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "project_id": "'"$PROJECT_ID"'",
        "model_id": "'"$MODEL_ID"'",
        "model_version": "h12",
        "entity_id": "asset_001",
        "features": { "n_evt_1h": 10, "n_crit_1h": 1 },
        "prediction": { "label": "normal_operation", "score": 0.18, "threshold": 0.50 },
        "metadata": { "request_id": "req_asset_001" }
      },
      {
        "project_id": "'"$PROJECT_ID"'",
        "model_id": "'"$MODEL_ID"'",
        "model_version": "h12",
        "entity_id": "asset_002",
        "features": { "n_evt_1h": 95, "n_crit_1h": 30 },
        "prediction": { "label": "event_risk", "score": 0.91, "threshold": 0.50 },
        "metadata": { "request_id": "req_asset_002" }
      }
    ]
  }'
```

O endpoint retorna status por item. Se uma predicao falhar, as outras podem ser registradas.

```json
{
  "items": [
    { "status": "recorded", "prediction_id": "pred_001" },
    { "status": "failed", "status_code": 409, "detail": "Duplicated request_id" }
  ]
}
```

## 9. Recuperar Predicoes

`GET /predictions` lista predicoes usando filtros e paginacao no servidor. Isso e importante para bases grandes, porque evita carregar dezenas de milhares de documentos no navegador.

### 9.1 Listar Predicoes De Um Projeto

```bash
curl "$BASE_URL/predictions?project_id=$PROJECT_ID&limit=50&skip=0" \
  -H "Authorization: Bearer $TOKEN"
```

O retorno segue o formato:

```json
{
  "items": [
    {
      "_id": "pred_xxx",
      "project_id": "proj_xxx",
      "model_id": "model_xxx",
      "model_version": "h12",
      "prediction": {
        "label": "event_risk",
        "score": 0.82,
        "threshold": 0.5,
        "above_threshold": true,
        "score_band": "high"
      },
      "feedback": {
        "available": false
      }
    }
  ],
  "total": 18000,
  "limit": 50,
  "skip": 0
}
```

### 9.2 Filtros Disponiveis

Voce pode combinar filtros na query string:

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

Exemplos:

```bash
# Apenas predicoes acionaveis de um modelo
curl "$BASE_URL/predictions?project_id=$PROJECT_ID&model_id=$MODEL_ID&label=event_risk&limit=100" \
  -H "Authorization: Bearer $TOKEN"

# Apenas predicoes sem feedback
curl "$BASE_URL/predictions?project_id=$PROJECT_ID&feedback_available=false&limit=100" \
  -H "Authorization: Bearer $TOKEN"

# Buscar por texto, ID, request_id parcial, entidade protegida, versao ou label
curl "$BASE_URL/predictions?project_id=$PROJECT_ID&q=asset_793&limit=25" \
  -H "Authorization: Bearer $TOKEN"

# Segunda pagina, com tamanho de pagina 250
curl "$BASE_URL/predictions?project_id=$PROJECT_ID&limit=250&skip=250" \
  -H "Authorization: Bearer $TOKEN"
```

### 9.3 Recuperar Predicao Por ID

```bash
curl "$BASE_URL/predictions/$PREDICTION_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Esse endpoint retorna o documento completo, incluindo features, prediction, explanations, decision, feedback, metadata e flags.

## 10. Registrar Feedback

Feedback representa o desfecho real observado depois da predicao. Em classificacao binaria, o ModelTrace compara o que o modelo previu com o observado e calcula `tp`, `fp`, `tn`, `fn` ou `inconclusive`.

O endpoint `POST /predictions/{prediction_id}/feedback` aceita token de usuario ou API key com escopo `feedback:write`. Quando a credencial e API key, ela so pode escrever feedback em predicoes do mesmo projeto.

### 10.1 Feedback Por Valor Observado

Use `observed_value = 1` para positivo real e `observed_value = 0` para negativo real.

```bash
curl -X POST "$BASE_URL/predictions/$PREDICTION_ID/feedback" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "observed_value": 1,
    "feedback_date": "2026-06-15",
    "source": "maintenance_system",
    "notes": "Evento confirmado no sistema de manutencao."
  }'
```

### 10.2 Feedback Por Label Observado

Se voce preferir usar label de negocio:

```bash
curl -X POST "$BASE_URL/predictions/$PREDICTION_ID/feedback" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "observed_label": "event_risk",
    "source": "manual_review",
    "notes": "Revisao operacional confirmou o caso."
  }'
```

### 10.3 Feedback Inconclusivo

Use label `inconclusive` ou omita valor/label quando nao houver desfecho confiavel.

```bash
curl -X POST "$BASE_URL/predictions/$PREDICTION_ID/feedback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "observed_label": "inconclusive",
    "observed_value": null,
    "source": "manual_review",
    "notes": "Caso sem evidencia suficiente."
  }'
```

Depois do feedback, a API invalida caches de dashboard e DS Lab, grava evento de auditoria e recalcula metricas do modelo.

## 11. Anotacoes, What-if E Replay

Esses endpoints sao usados na investigacao de uma decisao. Eles exigem token de usuario, pois fazem parte da operacao analitica dentro da plataforma.

### 11.1 Criar Anotacao

```bash
curl -X POST "$BASE_URL/predictions/$PREDICTION_ID/annotations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "analyst_note",
    "content": "Caso revisado pela operacao.",
    "tags": ["reviewed", "priority"]
  }'
```

Tipos aceitos:

```txt
analyst_note
false_positive_flag
action_taken
escalated
```

Para listar anotacoes:

```bash
curl "$BASE_URL/predictions/$PREDICTION_ID/annotations" \
  -H "Authorization: Bearer $TOKEN"
```

### 11.2 Rodar What-if

What-if estima como o score mudaria se algumas features fossem alteradas. Nesta versao, quando nao ha endpoint real de scoring conectado, o resultado e estimativo.

```bash
curl -X POST "$BASE_URL/predictions/$PREDICTION_ID/whatif" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hypothetical_features": {
      "n_evt_1h": 40,
      "n_crit_1h": 5
    }
  }'
```

O retorno inclui score original, score estimado, delta e se a decisao mudaria.

### 11.3 Criar Replay

Replay registra uma nova leitura da mesma predicao. Voce pode informar um score simulado diretamente ou mandar features hipoteticas para estimativa.

```bash
curl -X POST "$BASE_URL/predictions/$PREDICTION_ID/replay" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_version": "h13",
    "replay_score": 0.42,
    "replay_label": "normal_operation"
  }'
```

Para listar replays:

```bash
curl "$BASE_URL/predictions/$PREDICTION_ID/replays" \
  -H "Authorization: Bearer $TOKEN"
```

### 11.4 Consultar Audit Trail De Uma Predicao

```bash
curl "$BASE_URL/predictions/$PREDICTION_ID/audit-trail" \
  -H "Authorization: Bearer $TOKEN"
```

Esse endpoint retorna eventos relacionados a predicao, como registro inicial, feedback, anotacoes e replay.

## 12. Dashboard, Metricas E DS Lab

O dashboard do projeto resume KPIs, volume temporal, distribuicao de score, matriz de confusao, alertas e metricas materializadas.

### 12.1 Dashboard Do Projeto

```bash
curl "$BASE_URL/projects/$PROJECT_ID/dashboard" \
  -H "Authorization: Bearer $TOKEN"
```

Esse endpoint e usado pelo Overview. Ele retorna `kpis`, `volume_series`, `score_histogram`, `confusion_matrix`, `version_summary` e alertas.

### 12.2 Metricas Do Modelo

```bash
curl "$BASE_URL/models/$MODEL_ID/metrics" \
  -H "Authorization: Bearer $TOKEN"
```

As metricas sao recalculadas a partir das predicoes e feedbacks disponiveis. Quando ha pouco feedback, metricas como recall, precision e F2 devem ser lidas como parciais.

### 12.3 Diagnosticos Do DS Lab

```bash
curl "$BASE_URL/models/$MODEL_ID/diagnostics" \
  -H "Authorization: Bearer $TOKEN"
```

Para diagnosticos por segmento, informe `slice_feature`:

```bash
curl "$BASE_URL/models/$MODEL_ID/diagnostics?slice_feature=shift" \
  -H "Authorization: Bearer $TOKEN"
```

O retorno alimenta a aba DS Lab, incluindo curva de threshold, calibracao, importancia de features, cobertura de contrato, falsos positivos, falsos negativos e recomendacoes.

### 12.4 Matriz De Confusao E Distribuicao De Score

```bash
curl "$BASE_URL/models/$MODEL_ID/confusion-matrix" \
  -H "Authorization: Bearer $TOKEN"

curl "$BASE_URL/models/$MODEL_ID/score-distribution" \
  -H "Authorization: Bearer $TOKEN"
```

### 12.5 Drift

`POST /models/{model_id}/drift/run` gera um novo relatorio de drift.

```bash
curl -X POST "$BASE_URL/models/$MODEL_ID/drift/run" \
  -H "Authorization: Bearer $TOKEN"
```

Para consultar relatorios anteriores:

```bash
curl "$BASE_URL/models/$MODEL_ID/drift" \
  -H "Authorization: Bearer $TOKEN"
```

### 12.6 Bias Analysis

```bash
curl "$BASE_URL/models/$MODEL_ID/bias-analysis?feature=shift" \
  -H "Authorization: Bearer $TOKEN"
```

Esse endpoint agrupa predicoes por valor da feature indicada e calcula metricas por grupo. Ele depende da feature existir no payload de predicoes.

## 13. Operacao

A area operacional agrega casos, incidentes, coortes, qualidade da fonte, alertas e avaliacoes. O endpoint principal e `GET /projects/{project_id}/operations`.

```bash
curl "$BASE_URL/projects/$PROJECT_ID/operations" \
  -H "Authorization: Bearer $TOKEN"
```

Para listar casos operacionais:

```bash
curl "$BASE_URL/projects/$PROJECT_ID/intervention-cases" \
  -H "Authorization: Bearer $TOKEN"
```

Para filtrar por status:

```bash
curl "$BASE_URL/projects/$PROJECT_ID/intervention-cases?status_filter=open" \
  -H "Authorization: Bearer $TOKEN"
```

Para alterar status de um caso:

```bash
curl -X POST "$BASE_URL/intervention-cases/$CASE_ID/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "note": "Caso atribuido para analise operacional."
  }'
```

Status aceitos:

```txt
open
assigned
in_progress
paused
resolved
dismissed
```

## 14. Alertas

Alertas sao criados a partir de regras. Uma regra define tipo, metrica, operador, threshold, severidade e modelo. A API tambem possui regras padrao que podem ser avaliadas com `include_defaults=true`.

### 14.1 Criar Regra De Alerta

```bash
curl -X POST "$BASE_URL/alert-rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'"$PROJECT_ID"'",
    "model_id": "'"$MODEL_ID"'",
    "name": "Cobertura de feedback baixa",
    "type": "feedback_rate_low",
    "metric": "feedback_rate",
    "operator": "less_than",
    "threshold": 0.25,
    "severity": "medium",
    "min_feedback_count": 1,
    "enabled": true
  }'
```

Tipos aceitos:

```txt
performance_threshold
volume_drop
data_drift
prediction_drift
missing_features
deprecated_version_active
feedback_rate_low
```

Operadores aceitos:

```txt
less_than
greater_than
```

### 14.2 Listar Regras

```bash
curl "$BASE_URL/alert-rules?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 14.3 Atualizar E Excluir Regras

```bash
curl -X PATCH "$BASE_URL/alert-rules/$RULE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 0.35,
    "severity": "high",
    "enabled": true
  }'

curl -X DELETE "$BASE_URL/alert-rules/$RULE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Atualizar regra preserva o identificador e altera apenas os campos enviados. Excluir remove a regra cadastrada; alertas ja criados continuam na trilha operacional e podem ser reconhecidos ou resolvidos normalmente.

### 14.4 Rodar Checagem De Alertas

```bash
curl -X POST "$BASE_URL/alerts/run-checks?project_id=$PROJECT_ID&include_defaults=true" \
  -H "Authorization: Bearer $TOKEN"
```

O retorno traz regras avaliadas e alertas criados. O motor deduplica alertas abertos por regra para evitar criar alertas repetidos enquanto o problema continua ativo.

### 14.5 Listar, Reconhecer E Resolver Alertas

```bash
curl "$BASE_URL/alerts?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST "$BASE_URL/alerts/$ALERT_ID/acknowledge" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST "$BASE_URL/alerts/$ALERT_ID/resolve" \
  -H "Authorization: Bearer $TOKEN"
```

Ao resolver um alerta, o contador de alertas ativos do projeto e atualizado. Quando uma checagem cria um alerta novo, o produto tambem registra uma notificacao interna para o responsavel do projeto.

## 15. Produto Operacional

Esses endpoints sustentam recursos de produto que ajudam o cientista de dados e a operacao a trabalhar diariamente sem depender de consultas manuais no banco.

### 15.1 Notificacoes

```bash
curl "$BASE_URL/notifications" \
  -H "Authorization: Bearer $TOKEN"

curl -X PATCH "$BASE_URL/notifications/$NOTIFICATION_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"read": true}'

curl -X POST "$BASE_URL/notifications/mark-all-read" \
  -H "Authorization: Bearer $TOKEN"
```

Notificacoes sao criadas por alertas, jobs e eventos de sistema. A interface usa essa API para mostrar o contador de nao lidas na topbar e a lista dentro da aba Automacao.

### 15.2 Jobs

```bash
curl -X POST "$BASE_URL/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'"$PROJECT_ID"'",
    "type": "drift",
    "params": { "window_days": 30 }
  }'

curl "$BASE_URL/jobs?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Tipos de job aceitos: `alerts`, `drift`, `metrics`, `diagnostics` e `dashboard`. No ambiente local, eles rodam com `BackgroundTasks`; em producao, a mesma modelagem permite migrar para uma fila distribuida.

### 15.3 Views Salvas

```bash
curl -X POST "$BASE_URL/saved-views" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alto risco sem feedback",
    "view": "predictions",
    "project_id": "'"$PROJECT_ID"'",
    "filters": { "score_min": 0.75, "feedback": "pending" },
    "columns": ["entity", "score", "label", "created_at"]
  }'

curl "$BASE_URL/saved-views?view=predictions" \
  -H "Authorization: Bearer $TOKEN"

curl -X DELETE "$BASE_URL/saved-views/$VIEW_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Views salvas guardam filtros e colunas por usuario. Elas nao duplicam predicoes; apenas persistem a forma como o usuario quer enxergar o conjunto de trabalho.

### 15.4 Timeline De Entidade E Notas

```bash
curl "$BASE_URL/projects/$PROJECT_ID/entity-timeline?q=student_001" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST "$BASE_URL/projects/$PROJECT_ID/entity-notes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "student_001",
    "body": "Contato revisado pela equipe operacional.",
    "tags": ["revisado", "prioritario"]
  }'
```

A timeline consulta predicoes, casos, replays e notas vinculados a uma entidade. O campo `q` pode ser ID real, matricula, nome exibido ou outro identificador autorizado.

### 15.5 Data Contracts

```bash
curl "$BASE_URL/projects/$PROJECT_ID/data-contract?model_id=$MODEL_ID" \
  -H "Authorization: Bearer $TOKEN"

curl -X PATCH "$BASE_URL/projects/$PROJECT_ID/data-contract" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode": "block"}'
```

O contrato de dados usa `expected_features` do modelo para validar as features recebidas. O modo `accept` registra problemas sem bloquear, `warn` destaca problemas operacionais e `block` recusa payloads que violam regras criticas.

## 16. Exportacoes

Exportacoes geram arquivos CSV ou JSON a partir da colecao `predictions`. Por padrao, `redact_pii` vem como `true`, o que protege identificadores sensiveis.

### 16.1 Criar Exportacao

```bash
curl -X POST "$BASE_URL/exports" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predictions",
    "filters": {
      "project_id": "'"$PROJECT_ID"'",
      "model_id": "'"$MODEL_ID"'"
    },
    "format": "csv",
    "include_features": true,
    "include_explanations": true,
    "redact_pii": true
  }'
```

O retorno inclui `_id`, `record_count`, `status`, `format` e metadados. Guarde o `_id` para download.

### 16.2 Listar E Consultar Exportacoes

```bash
curl "$BASE_URL/exports" \
  -H "Authorization: Bearer $TOKEN"

curl "$BASE_URL/exports/$EXPORT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 16.3 Baixar Arquivo

```bash
curl "$BASE_URL/exports/$EXPORT_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o predictions.csv
```

Em PowerShell:

```powershell
Invoke-WebRequest "$BASE_URL/exports/$EXPORT_ID/download" `
  -Headers $AUTH `
  -OutFile "predictions.csv"
```

## 17. Seguranca E Governanca

A API expoe endpoints para postura de seguranca e migracao de dados sensiveis existentes.

### 16.1 Postura De Seguranca

```bash
curl "$BASE_URL/security/posture" \
  -H "Authorization: Bearer $TOKEN"
```

Esse endpoint verifica criptografia de PII, indices cegos, hashing de senha, API keys em HMAC, SECRET_KEY, headers de seguranca e usuarios migrados.

### 16.2 Migrar Dados Sensiveis

```bash
curl -X POST "$BASE_URL/security/migrate-sensitive-data" \
  -H "Authorization: Bearer $TOKEN"
```

Execute essa migracao somente depois de configurar chaves definitivas em producao. Em ambiente local, ela serve para demonstrar criptografia, redaction e pseudonimizacao.

### 16.3 Audit Trail Do Projeto

`GET /projects/{project_id}/audit-events` retorna os eventos recentes do projeto. A aba Governanca usa esse endpoint para mostrar quem executou acoes, qual recurso foi afetado e quando o evento ocorreu.

```bash
curl "$BASE_URL/projects/$PROJECT_ID/audit-events" \
  -H "Authorization: Bearer $TOKEN"
```

O retorno segue o formato:

```json
{
  "items": [
    {
      "_id": "audit_xxx",
      "event_type": "prediction.recorded",
      "resource": {
        "type": "prediction",
        "id": "pred_xxx"
      },
      "actor": {
        "type": "api_key",
        "prefix": "mt_live_abcd"
      },
      "created_at": "2026-06-01T12:00:00Z"
    }
  ]
}
```

## 18. Cliente Python Completo

Este exemplo mostra um fluxo minimo usando `requests`: login, criacao de API key, envio de predicao, consulta e feedback.

```python
import requests

BASE_URL = "http://127.0.0.1:8001/api/v1"


def post(path, token=None, json=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.post(f"{BASE_URL}{path}", headers=headers, json=json, timeout=30)
    response.raise_for_status()
    return response.json()


def get(path, token):
    response = requests.get(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


session = post(
    "/auth/login",
    json={"email": "diegohenrique.mail@gmail.com", "password": "D1eg0X@vi3rHUB"},
)
token = session["access_token"]

projects = get("/projects", token)
project_id = projects["items"][0]["_id"]

models = get(f"/projects/{project_id}/models", token)
model_id = models["items"][0]["_id"]
model_version = "h12"

key_response = post(
    f"/projects/{project_id}/api-keys",
    token=token,
    json={
        "name": "Python pipeline",
        "scopes": ["predictions:write", "feedback:write"],
        "expires_at": "2026-08-05T12:00:00.000Z",
    },
)
api_key = key_response["api_key"]

prediction = post(
    "/predictions",
    token=api_key,
    json={
        "project_id": project_id,
        "model_id": model_id,
        "model_version": model_version,
        "entity_id": "asset_python_001",
        "features": {"n_evt_1h": 12, "n_crit_1h": 1},
        "prediction": {"label": "normal_operation", "score": 0.19, "threshold": 0.5},
        "metadata": {"request_id": "req_python_001"},
    },
)

prediction_id = prediction["prediction_id"]

feedback = post(
    f"/predictions/{prediction_id}/feedback",
    token=api_key,
    json={"observed_value": 0, "source": "python_example"},
)

print(prediction_id, feedback["feedback"]["classification_result"])
```

## 19. Cliente TypeScript Completo

Este exemplo usa `fetch`. Ele funciona em Node.js moderno ou no browser, ajustando CORS quando necessario.

```ts
const BASE_URL = "http://127.0.0.1:8001/api/v1";

async function api<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new Error(data?.detail || response.statusText);
  }

  return data as T;
}

type Session = {
  access_token: string;
  refresh_token: string;
};

type ListResponse<T> = {
  items: T[];
};

async function main() {
  const session = await api<Session>("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email: "diegohenrique.mail@gmail.com",
      password: "D1eg0X@vi3rHUB",
    }),
  });

  const token = session.access_token;

  const projects = await api<ListResponse<{ _id: string }>>("/projects", {}, token);
  const projectId = projects.items[0]._id;

  const models = await api<ListResponse<{ _id: string }>>(`/projects/${projectId}/models`, {}, token);
  const modelId = models.items[0]._id;

  const keyResponse = await api<{ api_key: string }>(
    `/projects/${projectId}/api-keys`,
    {
      method: "POST",
      body: JSON.stringify({
        name: "TypeScript pipeline",
        scopes: ["predictions:write", "feedback:write"],
        expires_at: "2026-08-05T12:00:00.000Z",
      }),
    },
    token,
  );

  const apiKey = keyResponse.api_key;

  const prediction = await api<{ prediction_id: string }>(
    "/predictions",
    {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        model_id: modelId,
        model_version: "h12",
        entity_id: "asset_ts_001",
        features: {
          n_evt_1h: 22,
          n_crit_1h: 4,
        },
        prediction: {
          label: "event_risk",
          score: 0.76,
          threshold: 0.5,
        },
        metadata: {
          request_id: "req_ts_001",
        },
      }),
    },
    apiKey,
  );

  await api(
    `/predictions/${prediction.prediction_id}/feedback`,
    {
      method: "POST",
      body: JSON.stringify({
        observed_value: 1,
        source: "typescript_example",
      }),
    },
    apiKey,
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

## 20. Tratamento De Erros

A API usa codigos HTTP convencionais. Em geral, `200` indica sucesso em consulta ou acao, `201` indica criacao, `400` indica payload invalido, `401` indica credencial ausente, invalida ou expirada, `403` indica falta de permissao ou API key tentando acessar projeto errado, `404` indica recurso inexistente ou fora da organizacao, e `409` indica conflito de idempotencia, como `request_id` duplicado.

Exemplo de erro:

```json
{
  "detail": "Duplicated request_id"
}
```

No cliente, trate qualquer resposta fora de `2xx` como falha. Em integracoes de predicao, use `metadata.request_id` para evitar duplicidade quando houver retry.

## 21. Boas Praticas De Integracao

Use API key apenas em backend, pipeline ou servico seguro. Nao coloque API key em codigo de front-end publico. Para interface web, use token de usuario.

Sempre envie `metadata.request_id`. Esse campo permite idempotencia e evita duplicar predicoes quando o seu sistema faz retry por timeout ou queda de rede.

Mantenha `model_version` consistente. O ModelTrace usa esse campo para comparar versoes, gerar metricas por janela e permitir replay.

Envie `features` com os nomes esperados pelo modelo. O schema e flexivel, mas features ausentes derrubam qualidade de fonte, alertas e diagnosticos.

Registre feedback assim que o desfecho real estiver disponivel. Sem feedback, a plataforma ainda monitora volume, score, drift e alertas, mas metricas como recall, precision e matriz de confusao ficam parciais.

Use `redact_pii: true` em exportacoes por padrao. Dados reais devem sair da plataforma apenas quando houver finalidade clara e autorizacao.

## 22. Fluxo Completo Resumido

Este e o caminho padrao para colocar um novo modelo sob monitoramento:

1. Fazer login com `POST /auth/login`.
2. Criar ou escolher projeto com `POST /projects` ou `GET /projects`.
3. Criar modelo com `POST /projects/{project_id}/models`.
4. Criar versao com `POST /models/{model_id}/versions`.
5. Criar API key com `POST /projects/{project_id}/api-keys`.
6. Enviar predicoes com `POST /predictions` ou `POST /predictions/batch`.
7. Consultar predicoes com `GET /predictions`.
8. Enviar feedback com `POST /predictions/{prediction_id}/feedback`.
9. Ver dashboard com `GET /projects/{project_id}/dashboard`.
10. Rodar diagnosticos com `GET /models/{model_id}/diagnostics`.
11. Rodar drift com `POST /models/{model_id}/drift/run`.
12. Checar alertas com `POST /alerts/run-checks`.
13. Exportar dados com `POST /exports`.

Com esse fluxo, o ModelTrace passa a ter dados suficientes para operar dashboards, DS Lab, monitoramento, auditoria, governanca e exportacoes.

## 23. Exemplo End-to-End Comentado: Do Modelo Ate A Operacao

Esta secao mostra um exemplo curto e completo, do treino do modelo ate a leitura do dashboard. O objetivo e deixar claro **onde acaba o codigo do modelo e onde comeca a API do ModelTrace**. Use os comentarios `# ===== SEU MODELO =====` e `# ===== MODELTRACE API =====` como marcadores visuais.

O caso de uso e classificacao binaria de risco operacional em equipamentos industriais. O modelo decide se um ativo tem risco elevado de evento `DontGo` na proxima janela horaria. Em producao real, esse modelo seria treinado com historico de meses; aqui ele e treinado com dados sinteticos para o exemplo rodar em qualquer maquina.

### 23.1 Pre-Requisitos

```bash
pip install scikit-learn requests joblib pandas numpy
```

Tenha o back-end do ModelTrace rodando em `http://127.0.0.1:8001` e uma conta criada (ou use o seed local).

### 23.2 Codigo Completo

Salve o arquivo abaixo como `exemplo_e2e.py` e execute com `python exemplo_e2e.py`. Cada bloco esta marcado para deixar claro o papel de cada parte.

```python
"""Exemplo end-to-end: treino do modelo + integracao com ModelTrace.

A linha divisoria entre o codigo do modelo (sklearn, sua logica de negocio)
e a API do ModelTrace (HTTP REST) esta marcada por comentarios em blocos.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split


# ============================================================================
# ===== SEU MODELO ===========================================================
# Tudo nesta secao e codigo de Machine Learning normal. O ModelTrace nao
# interfere aqui. Voce treina, valida e versiona seu modelo da forma habitual.
# ============================================================================

FEATURE_NAMES = ["n_evt_1h", "n_crit_1h", "vibration_rms", "oil_temp_c"]


def generate_synthetic_dataset(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Gera um dataset sintetico de manutencao industrial."""
    rng = np.random.default_rng(seed)
    n_evt = rng.poisson(lam=18, size=n).astype(float)
    n_crit = rng.poisson(lam=4, size=n).astype(float)
    vibration = rng.normal(loc=3.2, scale=1.1, size=n)
    oil_temp = rng.normal(loc=78.0, scale=8.0, size=n)
    risk_score = (
        0.04 * n_evt + 0.18 * n_crit + 0.22 * vibration + 0.012 * (oil_temp - 70)
    )
    prob = 1 / (1 + np.exp(-(risk_score - 2.4)))
    label = (rng.uniform(size=n) < prob).astype(int)
    return pd.DataFrame(
        {
            "n_evt_1h": n_evt,
            "n_crit_1h": n_crit,
            "vibration_rms": vibration,
            "oil_temp_c": oil_temp,
            "event_risk": label,
        }
    )


def train_model() -> tuple[LogisticRegression, dict]:
    """Treina LogisticRegression e devolve modelo + metricas offline."""
    df = generate_synthetic_dataset()
    X = df[FEATURE_NAMES].to_numpy()
    y = df["event_risk"].to_numpy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=7, stratify=y
    )

    clf = LogisticRegression(max_iter=500, class_weight="balanced")
    clf.fit(X_train, y_train)

    proba_test = clf.predict_proba(X_test)[:, 1]
    metrics = {
        "average_precision": float(average_precision_score(y_test, proba_test)),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
    }
    joblib.dump(clf, "model_v1.joblib")
    return clf, metrics


def score(model: LogisticRegression, features: dict) -> tuple[float, str]:
    """Calcula score 0-1 para um conjunto de features e devolve label."""
    row = np.array([[features[name] for name in FEATURE_NAMES]])
    proba = float(model.predict_proba(row)[0, 1])
    label = "event_risk" if proba >= 0.50 else "normal_operation"
    return proba, label


def top_explanations(model: LogisticRegression, features: dict, k: int = 2) -> list:
    """Aproximacao linear das contribuicoes por feature (didatica)."""
    coefs = dict(zip(FEATURE_NAMES, model.coef_[0]))
    contributions = sorted(
        (
            {
                "feature": name,
                "value": features[name],
                "impact": float(features[name] * coefs[name]),
                "direction": "risk_up" if features[name] * coefs[name] > 0 else "risk_down",
                "rank": rank,
            }
            for rank, name in enumerate(FEATURE_NAMES, start=1)
        ),
        key=lambda item: abs(item["impact"]),
        reverse=True,
    )
    return contributions[:k]


# ============================================================================
# ===== MODELTRACE API =======================================================
# Tudo abaixo sao chamadas REST para o backend do ModelTrace. Cada funcao
# corresponde a um endpoint documentado nas secoes anteriores.
# ============================================================================

BASE_URL = "http://127.0.0.1:8001/api/v1"


def mt_login(email: str, password: str) -> str:
    """POST /auth/login — devolve access_token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def mt_create_project(token: str, name: str) -> str:
    """POST /projects — devolve project_id."""
    response = requests.post(
        f"{BASE_URL}/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "description": "Risco de eventos DontGo em frota industrial.",
            "problem_type": "binary_classification",
            "domain": "industrial",
            "default_threshold": 0.50,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["_id"]


def mt_create_model(token: str, project_id: str) -> str:
    """POST /projects/{project_id}/models — devolve model_id."""
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/models",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Risco DontGo (LogReg)",
            "problem_type": "binary_classification",
            "target_name": "event_risk",
            "labels": {"positive": "event_risk", "negative": "normal_operation"},
            "default_threshold": 0.50,
            "primary_metric": "average_precision",
            "expected_features": [
                {"name": name, "type": "numeric", "required": True}
                for name in FEATURE_NAMES
            ],
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["_id"]


def mt_create_version(token: str, model_id: str, metrics: dict) -> str:
    """POST /models/{model_id}/versions — devolve version label."""
    response = requests.post(
        f"{BASE_URL}/models/{model_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "version": "v1",
            "algorithm": "LogisticRegression",
            "status": "production",
            "features": FEATURE_NAMES,
            "hyperparameters": {"class_weight": "balanced", "max_iter": 500},
            "offline_metrics": metrics,
            "changelog": "Versao inicial em producao.",
        },
        timeout=15,
    )
    response.raise_for_status()
    return "v1"


def mt_create_api_key(token: str, project_id: str) -> str:
    """POST /projects/{project_id}/api-keys — devolve api_key (mostrada uma unica vez)."""
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Pipeline scoring",
            "scopes": ["predictions:write", "feedback:write"],
            "expires_at": "2026-12-31T23:59:59.000Z",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["api_key"]


def mt_send_prediction(
    api_key: str,
    project_id: str,
    model_id: str,
    model_version: str,
    entity_id: str,
    features: dict,
    score_value: float,
    label: str,
    explanations: list,
    request_id: str,
) -> str:
    """POST /predictions — devolve prediction_id."""
    response = requests.post(
        f"{BASE_URL}/predictions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "project_id": project_id,
            "model_id": model_id,
            "model_version": model_version,
            "entity_id": entity_id,
            "entity_type": "industrial_asset",
            "features": features,
            "prediction": {
                "label": label,
                "score": score_value,
                "threshold": 0.50,
            },
            "explanations": explanations,
            "decision": {
                "action": "human_review" if score_value >= 0.70 else "auto_pass",
                "status": "triggered" if score_value >= 0.50 else "skipped",
                "reason": "score_above_threshold" if score_value >= 0.50 else "below_threshold",
            },
            "metadata": {
                "request_id": request_id,
                "source_system": "exemplo_e2e",
                "environment": "production",
            },
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["prediction_id"]


def mt_send_feedback(api_key: str, prediction_id: str, observed_value: int) -> None:
    """POST /predictions/{prediction_id}/feedback."""
    response = requests.post(
        f"{BASE_URL}/predictions/{prediction_id}/feedback",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "observed_value": observed_value,
            "feedback_date": datetime.now(tz=timezone.utc).date().isoformat(),
            "source": "maintenance_system",
        },
        timeout=15,
    )
    response.raise_for_status()


def mt_dashboard(token: str, project_id: str) -> dict:
    """GET /projects/{project_id}/dashboard."""
    response = requests.get(
        f"{BASE_URL}/projects/{project_id}/dashboard",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def mt_run_drift(token: str, model_id: str) -> dict:
    """POST /models/{model_id}/drift/run."""
    response = requests.post(
        f"{BASE_URL}/models/{model_id}/drift/run",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# ============================================================================
# ===== ORQUESTRACAO =========================================================
# main() costura as duas pecas: treina o modelo (codigo proprio) e usa a API
# do ModelTrace para registrar projeto/modelo/versao/predicoes/feedback.
# ============================================================================


def main() -> None:
    # ----- SEU MODELO: treino offline ---------------------------------------
    print("[modelo] Treinando LogisticRegression em dados sinteticos...")
    model, offline_metrics = train_model()
    print(f"[modelo] AP offline: {offline_metrics['average_precision']:.3f}")

    # ----- MODELTRACE API: autenticacao -------------------------------------
    print("[api] Login...")
    token = mt_login("diegohenrique.mail@gmail.com", "D1eg0X@vi3rHUB")

    # ----- MODELTRACE API: criar projeto/modelo/versao ----------------------
    print("[api] Criando projeto, modelo e versao...")
    project_id = mt_create_project(token, name="Manutencao Industrial (exemplo)")
    model_id = mt_create_model(token, project_id)
    model_version = mt_create_version(token, model_id, metrics=offline_metrics)

    # ----- MODELTRACE API: gerar API key para pipeline ----------------------
    print("[api] Gerando API key...")
    api_key = mt_create_api_key(token, project_id)

    # ----- LOOP DE SERVING: alterna SEU MODELO + MODELTRACE API -------------
    rng = np.random.default_rng(123)
    prediction_ids: list[tuple[str, int]] = []
    for i in range(20):
        # ===== SEU MODELO: gera/recebe features e calcula score =============
        features = {
            "n_evt_1h": float(rng.poisson(lam=20)),
            "n_crit_1h": float(rng.poisson(lam=5)),
            "vibration_rms": float(rng.normal(loc=3.4, scale=1.0)),
            "oil_temp_c": float(rng.normal(loc=80.0, scale=6.0)),
        }
        score_value, label = score(model, features)
        explanations = top_explanations(model, features, k=2)
        observed = 1 if score_value > 0.55 else 0  # simula desfecho real

        # ===== MODELTRACE API: registra a predicao ==========================
        prediction_id = mt_send_prediction(
            api_key=api_key,
            project_id=project_id,
            model_id=model_id,
            model_version=model_version,
            entity_id=f"asset_{i:03d}",
            features=features,
            score_value=score_value,
            label=label,
            explanations=explanations,
            request_id=f"req_exemplo_e2e_{i:03d}",
        )
        prediction_ids.append((prediction_id, observed))

    print(f"[api] {len(prediction_ids)} predicoes registradas.")

    # ----- MODELTRACE API: enviar feedback observado para cada predicao -----
    print("[api] Registrando feedback...")
    for prediction_id, observed_value in prediction_ids:
        mt_send_feedback(api_key, prediction_id, observed_value=observed_value)

    # ----- MODELTRACE API: ler dashboard e rodar drift ----------------------
    time.sleep(1)  # caches de dashboard sao invalidados; pequeno respiro
    print("[api] Lendo dashboard...")
    dash = mt_dashboard(token, project_id)
    kpis = dash.get("kpis", {})
    print(f"[api] KPIs: predictions={kpis.get('predictions_count')} "
          f"feedback_rate={kpis.get('feedback_rate')}")

    print("[api] Rodando drift...")
    drift = mt_run_drift(token, model_id)
    print(f"[api] Drift criado: id={drift.get('_id')}")

    print("[done] Fluxo completo concluido.")


if __name__ == "__main__":
    main()
```

### 23.3 O Que Acabou De Acontecer

Ao rodar `python exemplo_e2e.py` voce executou, em ordem:

1. **Seu modelo (offline):** treinou um `LogisticRegression` em 5 000 linhas sinteticas e mediu `average_precision` no conjunto de teste.
2. **`POST /auth/login`:** autenticou no ModelTrace e recebeu `access_token`.
3. **`POST /projects`, `POST /projects/{id}/models`, `POST /models/{id}/versions`:** registrou o projeto, o modelo, a versao em producao e as metricas offline.
4. **`POST /projects/{id}/api-keys`:** criou uma chave de API para o pipeline.
5. **`POST /predictions` (20x):** para cada exemplo, **seu codigo** calculou score com sklearn e a **API do ModelTrace** persistiu o documento da predicao com features, score, explanations, decision e metadata.
6. **`POST /predictions/{id}/feedback` (20x):** registrou o desfecho real, fazendo a plataforma calcular matriz de confusao, recall e precision.
7. **`GET /projects/{id}/dashboard`:** leu os KPIs consolidados (volume, feedback rate, score medio).
8. **`POST /models/{id}/drift/run`:** disparou o calculo de drift entre as janelas registradas.

Depois disso, a interface do ModelTrace mostra o projeto inteiro funcionando: Overview com KPIs, DS Lab com diagnostics, Operacao com casos, Auditoria com a trilha de eventos e Exportacao com CSV/JSON sob demanda.

### 23.4 Resumo Visual Da Divisao

```txt
SEU MODELO  (sklearn, joblib, sua logica)
  - generate_synthetic_dataset()
  - train_model()
  - score()
  - top_explanations()

MODELTRACE API  (HTTP REST sob /api/v1)
  - mt_login()              -> POST /auth/login
  - mt_create_project()     -> POST /projects
  - mt_create_model()       -> POST /projects/{id}/models
  - mt_create_version()     -> POST /models/{id}/versions
  - mt_create_api_key()     -> POST /projects/{id}/api-keys
  - mt_send_prediction()    -> POST /predictions
  - mt_send_feedback()      -> POST /predictions/{id}/feedback
  - mt_dashboard()          -> GET  /projects/{id}/dashboard
  - mt_run_drift()          -> POST /models/{id}/drift/run
```

Mantenha sempre essa fronteira clara no seu codigo: o modelo decide; o ModelTrace observa, audita e governa. Quando precisar trocar de algoritmo, apenas o bloco "SEU MODELO" muda; as funcoes da API ficam iguais.
