# ModelTrace

Plataforma de observabilidade, auditoria e governanca de decisoes de Machine Learning, com arquitetura documental NoSQL e experiencia orientada a operacao.

O ModelTrace nao e preso ao problema de evasao. Ele registra decisoes de qualquer modelo, para qualquer entidade e qualquer dominio: alunos, empresas, ativos industriais, clientes, pedidos, transacoes ou outros objetos de negocio.

## Capacidades Principais

- Modelagem documental para predicoes de ML.
- `features` flexiveis por modelo, sem schema rigido.
- Auditoria append-only por decisao.
- Snapshots de metricas materializadas.
- Projetos, modelos, versoes, datasets, model cards e governanca.
- Feedback posterior com matriz de confusao.
- Drift, what-if, replay, bias analysis e comparacao de versoes.
- Operacao com coortes, qualidade de dados, incidentes, alertas e fila.
- Front-end responsivo com simulador guiado, sem exigir JSON do usuario final.
- Tabela de predicoes com paginacao/filtros no servidor para bases grandes.
- Notificacoes visuais de sucesso, erro e carregamento em acoes operacionais.
- Confirmacao de email, reset de senha, perfil editavel e upload de foto.
- Exportacao CSV/JSON para auditoria e relatorios.
- Criptografia de PII, indices cegos, hashes versionados, cookies HttpOnly e painel de postura de seguranca.

### Novidades v2 (2026-05)

Foundation:

- Design system Stripe/Datadog (`docs/design-system.md`): tipografia premium (Inter + IBM Plex Mono), tokens semanticos, paleta accent indigo, gradientes funcionais, light theme preparado.
- Refatoracao do monolito `page.tsx` em `components/ui/`, `components/shell/`, `components/views/` e `components/hooks/`.
- KPIs com sparklines + indicador de tendencia integrados.

Atalhos e comandos:

- Command palette real (`Cmd+K` / `Ctrl+K`) com navegacao por seta, footer de atalhos e busca incremental.
- Painel lateral de notificacoes (`Cmd+/`) com tabs (Todas / Nao lidas / Alertas / Jobs / Sistema), mark-all-read e deep-link por tipo de recurso.
- Atalhos de teclado completos estilo Gmail/GitHub (`G + tecla` para navegacao, `?` para ajuda, `R` refresh, `Shift+Q` logout).
- Modal de ajuda com lista completa de atalhos agrupados.

Novas views:

- **Compare (Champion vs Challenger)** [`G C`]: comparador visual lado a lado de duas versoes do mesmo modelo com metricas, matriz de confusao por feedback, lift de F1 e botao de promote (`POST /models/{id}/versions/{v}/promote`).
- **Drift Heatmap** [`G X`]: matriz feature x tempo com PSI por feature, cores semanticas (estavel / atencao / drift detectado), hover detalhado e linha extra de PSI top-level do `prediction.score`. Backend: helper `_psi_continuous` (PSI por quantis igualitarios) e endpoint `GET /models/{id}/drift/heatmap`.
- **Casos (SLA Kanban)** [`G S`]: Kanban com 3 colunas (A fazer / Em andamento / Resolvido), prioridade visual, barra de SLA dinamica (no prazo / em risco / vencido), deep-link para Timeline da entidade e acoes rapidas para mover entre colunas.
- **Custo & Consumo** [`G U`]: painel FinOps com 5 KPIs (custo estimado + projecao 30d, predicoes, audit events, API keys ativas, armazenamento), area chart de volume diario, composicao do custo, top entidades e tabela de pricing customizavel. Backend: novo endpoint `GET /usage/summary?days=N` agregando contagens da org.

### Patches v2.1 (2026-05-09)

- **Bug fix critico**: notificacoes nao eram marcadas como lidas (campo `read` vs `read_at` divergente entre frontend e backend, e endpoint `/notifications/{id}/read` nao existia). Frontend agora usa `PATCH /notifications/{id}` com body `{read: true}` para individual e `POST /notifications/mark-all-read` para batch atomico.
- **Light theme** real: hook `useTheme` com persistencia `localStorage`, anti-FOUC via `next/script` `beforeInteractive`, atalho `T`, botao Sol/Lua no Topbar e overrides cuidadosos de surfaces, tooltips, charts e `kbd` em camada `[data-theme="light"]`.
- **Onboarding tour**: modal multi-step (7 passos) que aparece no primeiro login e pode ser reaberto via command palette. Versionamento `modeltrace_onboarding_v2` permite reabrir o tour para todos quando features importantes forem adicionadas.
- **Atalho `T`**: alterna entre temas claro e escuro de qualquer tela.

### Patches v2.1.1 (2026-05-09 noite)

- **PII unmask em Cost & Usage**: o ranking de top entidades exibia `[protected]` (sentinel literal do storage) em vez do `id` real. Endpoint `/usage/summary` agora chama `reveal_entity` em cada predicao antes de extrair o nome — mesmo padrao que `/predictions` e `/dashboard` ja usavam.
- **Helpers compartilhados em `lib/entity.ts`**: `entityDisplayName`, `entityIdentifier` e `cleanProtectedValue` unificam o tratamento do sentinel em todos os componentes (`SlaKanbanView`, `SlaAlertBar`, `CostUsageView`). Antipadrao "acessar `entity.display_name` direto" agora esta documentado em `docs/design-system.md` secao 13.1.

## Documentacao

Para aprender a consumir a API, enviar predicoes, registrar feedback, consultar dados, exportar arquivos e integrar pipelines, use o guia completo: [`docs/api.md`](docs/api.md).

A documentacao de software fica em [`docs/documentacao-software.md`](docs/documentacao-software.md), o manual de funcionalidades da interface fica em [`docs/manual-funcionalidades.md`](docs/manual-funcionalidades.md), a modelagem NoSQL fica em [`docs/data-model.md`](docs/data-model.md) e o design system do front-end fica em [`docs/design-system.md`](docs/design-system.md).

## Como Rodar

Nesta maquina, a porta `8000` ficou ocupada por uma API antiga. Por isso o front-end foi configurado em `frontend/.env.local` para usar a API atual em `8001`.

URLs atuais:

- Front-end: `http://127.0.0.1:3000`
- Back-end/Swagger: `http://127.0.0.1:8001/docs`
- Health check: `http://127.0.0.1:8001/health`

Credenciais locais:

```txt
Email: diegohenrique.mail@gmail.com
Senha: D1eg0X@vi3rHUB
```

### Back-end

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### Front-end

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\frontend"
npm run build
npm run start -- --hostname 127.0.0.1 --port 3000
```

Para desenvolvimento:

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\frontend"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

### Dependencias

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\backend"
pip install -r requirements.txt
pip install -r ..\scripts\requirements-import.txt

cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\frontend"
npm install
```

### Parar Servidores

```powershell
$ports = 3000,8001
foreach ($port in $ports) {
  $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($processId in $processes) {
    if ($processId -and $processId -ne 0) {
      Stop-Process -Id $processId -Force
    }
  }
}
```

## Banco De Dados

Por padrao, o projeto roda sem MongoDB instalado usando um store documental JSON local:

```txt
backend/.data/modeltrace.json
```

Para usar MongoDB real:

```powershell
$env:MONGODB_URL="mongodb://localhost:27017"
$env:MONGODB_DB_NAME="modeltrace"
```

## Seguranca E Criptografia

O produto agora protege dados reais no nivel da aplicacao, mesmo quando roda no store JSON local:

- e-mails ficam criptografados em `email_encrypted`, pesquisaveis por `email_hash` e exibidos como `email_masked`;
- entidades reais ficam pseudonimizadas em `entity.id`, com `entity.id_encrypted` e `entity.id_hash`;
- usuarios autenticados recebem os nomes, matriculas e identificadores reais na interface; a mascaracao fica restrita ao armazenamento, auditoria tecnica e exportacoes com `redact_pii=true`;
- senhas usam hash versionado PBKDF2-SHA256 com iteracoes configuraveis e pepper opcional;
- API keys usam HMAC-SHA256, escopos, expiracao, ultimo uso e a chave completa aparece apenas no momento da criacao;
- auditoria e exportacoes redigem tokens, senhas, API keys, e-mails e nomes exibidos;
- o front-end usa `sessionStorage` em vez de `localStorage` e a API tambem emite cookies `HttpOnly`;
- a aba **Governanca** mostra postura de seguranca, API keys, auditoria filtravel e exportacao de evidencias.

Variaveis recomendadas para producao:

```powershell
$env:SECRET_KEY="gere-um-segredo-longo"
$env:FIELD_ENCRYPTION_KEY="gere-outro-segredo-longo"
$env:PII_HASH_KEY="gere-outro-segredo-longo"
$env:PASSWORD_PEPPER="gere-outro-segredo-longo"
$env:API_KEY_HASH_SECRET="gere-outro-segredo-longo"
$env:COOKIE_SECURE="true"
$env:CORS_ORIGINS="https://seu-front-end.com"
$env:ALLOWED_HOSTS="sua-api.com"
```

Rotas uteis:

```txt
GET  /api/v1/security/posture
POST /api/v1/security/migrate-sensitive-data
```

Configure as chaves definitivas antes de executar a migracao completa de dados sensiveis, para evitar criptografar dados reais com segredos temporarios de desenvolvimento.

## Email, Perfil E Recuperacao De Senha

O back-end envia emails transacionais para confirmacao de conta e redefinicao de senha. Em desenvolvimento, quando `SMTP_HOST` nao esta configurado, os emails sao gravados em:

```txt
backend/.data/email_outbox.jsonl
```

Esse outbox local permite testar o fluxo completo sem servidor de email. Para producao, configure SMTP:

```powershell
$env:PUBLIC_APP_URL="https://seu-front-end.com"
$env:SMTP_HOST="smtp.seu-provedor.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="usuario-smtp"
$env:SMTP_PASSWORD="senha-smtp"
$env:SMTP_FROM="ModelTrace <no-reply@seu-dominio.com>"
$env:SMTP_STARTTLS="true"
$env:EMAIL_VERIFICATION_MINUTES="1440"
$env:PASSWORD_RESET_MINUTES="45"
```

Rotas de autenticacao e perfil:

```txt
POST  /api/v1/auth/resend-verification
POST  /api/v1/auth/verify-email
POST  /api/v1/auth/password-reset/request
POST  /api/v1/auth/password-reset/confirm
PATCH /api/v1/auth/me
POST  /api/v1/auth/me/avatar
GET   /api/v1/auth/me/avatar
```

A aba **Perfil** permite atualizar nome, email, cargo, area, empresa, telefone, fuso horario, bio, preferencias e foto. Se o email for alterado, a conta volta para estado pendente e recebe novo email de confirmacao. Avatares aceitos: PNG, JPG e WebP ate 2 MB.

Tambem e possivel usar MongoDB Atlas:

```powershell
$env:MONGODB_URL="mongodb+srv://usuario:senha@cluster.mongodb.net"
$env:MONGODB_DB_NAME="modeltrace"
```

## Modelagem Do Banco

A documentacao detalhada esta organizada por objetivo:

- Documentacao completa de software: [`docs/documentacao-software.md`](docs/documentacao-software.md)
- Manual de telas, blocos, botoes e funcionalidades: [`docs/manual-funcionalidades.md`](docs/manual-funcionalidades.md)
- Melhorias para evoluir como produto real: [`docs/melhorias-produto-real.md`](docs/melhorias-produto-real.md)
- Estrutura documental em JSON: [`docs/modelagem-banco-json.md`](docs/modelagem-banco-json.md)
- JSON simplificado: [`docs/modelagem-json-simplificada.json`](docs/modelagem-json-simplificada.json)
- JSON completo: [`docs/modelagem-json-completa.json`](docs/modelagem-json-completa.json)
- Modelos entidade-relacionamento simplificado e completo: [`docs/modelagem-banco-er.md`](docs/modelagem-banco-er.md)
- Diagrama SVG legado: [`docs/modeltrace-er.svg`](docs/modeltrace-er.svg)

O ER em Mermaid e os arquivos JSON acima sao a referencia atualizada. Eles mostram as colecoes centrais, os relacionamentos logicos e onde o modelo documental embute dados como `features`, `prediction`, `decision`, `feedback`, `flags` e `metadata`.

## Importacao Limpa Com Dados Reais

Pare o back-end antes de importar. O store JSON salva dados em memoria ao encerrar, entao importar com a API antiga aberta pode sobrescrever a carga nova.

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL"
python scripts/import_tcc_gi_real_data.py --source tcc-full
```

O importador:

- faz backup do store atual em `backups/`;
- limpa e recria `backend/.data/modeltrace.json`;
- copia artefatos do TCC de `D:\TCC - versao final` para `data/imported/tcc_models`;
- copia os parquets completos do TCC para `data/imported/tcc_preprocessamento`;
- roda LR, RF, XGBoost, CatBoost e MLP nas janelas P1, P2 e P4;
- usa o conjunto completo do TCC, incluindo treino, validacao e teste, como replay funcional completo;
- importa projetos reutilizaveis de `C:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados`;
- copia artefatos externos para `data/imported/external_projects`;
- popula projetos, modelos, versoes, predicoes, metricas, datasets, coortes, model cards, qualidade de dados e auditoria;
- nao altera os arquivos originais do TCC nem dos projetos externos.

Estado final da carga limpa:

```txt
Projetos: 3
Modelos: 7
Versoes: 19
Predicoes: 102.230
Alertas ativos: 0
```

Projetos importados:

```txt
TCC Student Outcomes Full Replay
- Dominio: education
- Entidades: 5.330 alunos anonimizados
- Predicoes: 76.230
- Modelos: LR, RF, XGBoost, CatBoost e MLP
- Janelas: P1, P2 e P4

CNPJ Closure Risk Radar
- Dominio: business
- Entidades: empresas
- Predicoes: 8.000
- Modelo: logistic_full calibrado
- Label acionavel: closure_risk

Industrial Predictive Maintenance
- Dominio: industrial
- Entidades: ativos
- Predicoes: 18.000
- Modelo: LightGBM
- Horizontes: 1h, 4h e 12h
- Label acionavel: event_risk
```

O resumo da ultima importacao fica em:

```txt
tmp/modeltrace_real_import_summary.json
```

Observacao metodologica: no projeto TCC, a carga `tcc-full` usa todos os registros completos disponiveis para validar funcionamento, auditoria e monitoramento. Como inclui registros de treino, validacao e teste, nao deve ser apresentada como estimativa imparcial de performance em producao.

## Projetos Externos Avaliados

Em `C:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados`, foram aproveitados os projetos com artefatos reutilizaveis de modelo e dados:

- CNPJ: importado com predicoes, metricas, SHAP e modelos `.joblib`.
- Vale: importado com features parquet, boosters LightGBM e calibradores por horizonte.

Projetos que tinham apenas notebooks ou tabelas analiticas, sem artefato de modelo reaproveitavel para replay de produto, foram deixados fora da carga automatica.

## Como Funciona

Fluxo principal:

1. Usuario entra no workspace.
2. Seleciona um projeto de qualquer dominio.
3. Seleciona o modelo e a versao.
4. Um sistema externo envia predicoes via API ou o usuario usa o Workbench guiado.
5. A API salva cada decisao como documento NoSQL.
6. O sistema anexa feedback real quando disponivel.
7. Dashboards e metricas usam as colecoes materializadas.
8. O usuario investiga drift, what-if, replay, equidade, alertas, exportacoes e auditoria.

A tela **Workbench** apresenta campos dinamicos a partir de `expected_features` do modelo selecionado e monta a requisicao internamente. Detalhes de integracao ficam disponiveis em uma area tecnica separada.

## Por Que NoSQL

A colecao central e `predictions`. Cada documento guarda uma decisao completa:

- `entity`: entidade avaliada, como aluno, empresa ou ativo.
- `features`: variaveis usadas pelo modelo, variando por projeto.
- `prediction`: label, score, threshold e score band.
- `explanations`: impactos por feature.
- `decision`: acao recomendada.
- `feedback`: resultado real posterior.
- `metadata`: sistema de origem, request ID, janela e contexto.

MongoDB/documentos fazem sentido porque cada modelo tem um conjunto diferente de features. Um modelo academico pode usar notas e carga horaria, um modelo de empresas pode usar CNAE/UF/score bruto, e um modelo industrial pode usar sinais de telemetria. Em tabelas rigidas isso geraria muitas colunas nulas ou schemas por modelo; no documento, cada decisao guarda o payload real.

Colecoes usadas:

- `organizations`
- `users`
- `projects`
- `models`
- `model_versions`
- `api_keys`
- `alert_rules`
- `predictions`
- `email_tokens`
- `notifications`
- `jobs`
- `saved_views`
- `entity_notes`
- `prediction_scenarios`
- `metrics_snapshots`
- `dashboard_cache`
- `diagnostic_cache`
- `audit_events`
- `prediction_annotations`
- `prediction_replays`
- `alerts`
- `exports`
- `datasets`
- `cohorts`
- `model_evaluations`
- `model_cards`
- `intervention_cases`
- `incidents`
- `data_quality_reports`
- `approvals`

## Health Score

O health score e um indicador composto de prontidao operacional. Ele consolida:

- disponibilidade de dados operacionais;
- cobertura de feedback;
- desempenho observado com feedback;
- alertas ativos;
- carga acionavel em relacao a capacidade prevista.

Um modelo pode manter boa performance estatistica e ainda exigir atencao quando gera alto volume de casos ou possui alertas ativos.

## Principais Funcionalidades

- Autenticacao com token.
- Cadastro de projetos genericos.
- Cadastro de modelos e versoes.
- Labels positivos/negativos configuraveis por modelo.
- API key por projeto.
- Ingestao individual e em lote.
- Idempotencia por `request_id`.
- Feedback posterior.
- Matriz `tp`, `fp`, `tn`, `fn`.
- Dashboard com KPIs, histograma, serie temporal e matriz.
- DS Lab com threshold optimizer, calibracao, slices, feature coverage e erros prioritarios.
- Auditoria de eventos importantes.
- Drift simplificado.
- Alertas configuraveis.
- Notificacoes internas com contador de nao lidas.
- Jobs operacionais para alertas, drift, metricas, diagnosticos e dashboard.
- Views salvas para filtros de predicoes.
- Timeline de entidade com predicoes, casos, replays e anotacoes.
- Data contracts com modos `accept`, `warn` e `block` na ingestao.
- Bias analysis por feature selecionada.
- What-if analysis.
- Replay de decisoes.
- Comparacao de versoes.
- Exportacao CSV/JSON.
- Model registry champion/challenger.
- Casos operacionais com prioridade e SLA.
- Incidentes operacionais.
- Model cards e aprovacoes.
- Qualidade de fonte por dataset.
- Workbench guiado com payload montado automaticamente.
- Postura de seguranca com criptografia, migracao de PII e rotacao de chaves legadas.

## Experiencia De Produto

Areas da aplicacao:

- **Overview:** painel executivo com health score, KPIs clicaveis, graficos e matriz de confusao.
- **Monitor:** API key, comparacao de versoes, drift, equidade e exportacao.
- **DS Lab:** diagnosticos para cientista de dados, threshold tuning, calibracao e contrato de features.
- **Predicoes:** tabela filtravel, busca por ID/entidade/label, paginacao e inspector lateral.
- **Decision Inspector:** score, drivers, feedback, what-if, replay, exportacao e detalhes auditaveis.
- **Operacao:** fila, alertas, qualidade de dados, incidentes, coortes e avaliacoes.
- **Entidades:** busca por aluno, cliente, ativo ou entidade, com linha do tempo operacional e notas.
- **Automacao:** jobs, notificacoes, data contracts, views salvas e regras de alerta.
- **Workbench:** simulador guiado com campos dinamicos por modelo.
- **Governanca:** trilha de auditoria, evidencias, API keys, mapa NoSQL e postura de seguranca.
- **Docs:** manual de uso dentro do produto com fluxos, limites, API e topicos por tela.

O botao **Comandos** abre uma command palette para navegar por telas, executar acoes e abrir topicos da documentacao.

O design e responsivo: sidebar em desktop, paineis empilhados em telas menores, tabelas com rolagem horizontal e botoes com icones para acoes operacionais.

## Testes E Validacao

Back-end:

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\backend"
python -m pytest
```

Front-end:

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL\frontend"
npm run lint
npm run build
```

Importador:

```powershell
cd "C:\Users\DiegoHenriqueXavier\Downloads\Projeto NoSQL"
python -m py_compile scripts/import_tcc_gi_real_data.py
```

Validacoes feitas nesta versao:

- importacao limpa `tcc-full`;
- API listando 3 projetos;
- dashboards por projeto com contagens corretas;
- alertas ativos zerados;
- botao de metrica abrindo predicoes;
- troca de projeto atualizando modelos, labels e features;
- aba Operacao mostrando alertas vazios e qualidade correta;
- DS Lab carregando diagnosticos online do modelo e pacote exportavel;
- Workbench registrando predicao com a versao correta apos trocar de projeto;
- backend `pytest` aprovado;
- front-end `tsc --noEmit` aprovado;
- build Next.js aprovado.

## Fluxo De Demonstracao

1. Entrar com `diegohenrique.mail@gmail.com` / `D1eg0X@vi3rHUB`.
2. Mostrar que existem tres projetos de dominios diferentes.
3. Abrir **Industrial Predictive Maintenance** para mostrar horizontes 1h/4h/12h.
4. Abrir **CNPJ Closure Risk Radar** para mostrar labels `closure_risk` e `active_business`.
5. Abrir **TCC Student Outcomes Full Replay** para mostrar o replay completo do TCC.
6. Na **Overview**, clicar em Predicoes, Acionaveis, Feedback e Alertas.
7. Na **Predicoes**, filtrar por label, versao e feedback.
8. Na **Operacao**, mostrar que alertas ativos ficam explicitos e navegaveis.
9. No **Workbench**, registrar uma predicao pelo formulario assistido.
10. Na **Governanca**, mostrar auditoria e colecoes NoSQL.

## Docker Compose

Em uma maquina com Docker instalado:

```powershell
docker compose up --build
```

Servicos padrao:

- Front-end: `http://localhost:3000`
- Back-end: `http://localhost:8000`
- MongoDB: `localhost:27017`
- Redis: `localhost:6379`

Se usar Docker e porta `8000` estiver livre, ajuste/remova `frontend/.env.local` para apontar para `http://localhost:8000/api/v1`.
