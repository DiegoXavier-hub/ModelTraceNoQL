# ModelTrace - Evolucao Para Produto Real

Este documento separa o que ja foi entregue do que ainda pode evoluir para tornar o ModelTrace uma plataforma corporativa mais madura. As sugestoes pendentes foram revisadas para remover itens que ja estao implementados.

## 1. Capacidades Ja Implementadas

### 1.1 Interface E Usabilidade

- Ajuste visual em `Qualidade da fonte`, separando label e valor numerico.
- Scroll interno no `Decision inspector` quando o conteudo ultrapassa a altura da tela.
- Correcao de overflow nos filtros de predicoes.
- Indicador sincronizado no grafico de otimizacao de threshold.
- Linha vertical e pontos nas curvas de F2, recall e precision conforme o simulador de threshold muda.
- Toasts de sucesso, erro e informacao para acoes operacionais.
- Tabela de predicoes com paginacao pelo servidor.
- Command palette para abrir telas, executar acoes e navegar pela documentacao.
- Pagina `Docs` no front-end com manual de uso por tela, fluxo e limite operacional.

### 1.2 Feedback E Analise De Decisao

- Feedback completo no `Decision inspector`.
- Registro de desfecho positivo, negativo ou inconclusivo.
- Origem e nota de feedback.
- Calculo automatico de `tp`, `fp`, `tn`, `fn` ou `inconclusive`.
- Recalculo de metricas apos feedback.
- Endpoint de feedback aceitando API key com escopo `feedback:write`.
- What-if editavel por feature.
- Presets de What-if: otimista, conservador e reset.
- Replay de decisao.
- Exportacao CSV de predicoes.

### 1.3 Alertas E Operacao

- Motor de alertas para:
  - `performance_threshold`;
  - `feedback_rate_low`;
  - `volume_drop`;
  - `prediction_drift`;
  - `data_drift`;
  - `missing_features`;
  - `deprecated_version_active`.
- Checagem de alertas por regras cadastradas.
- Checagem de alertas por regras padrao geradas por projeto/modelo.
- Deduplicacao de alertas abertos por regra.
- Acknowledge e resolucao de alertas.
- Atualizacao do contador de alertas ativos ao resolver alerta.
- Botao `Checar alertas` na aba Operacao.

### 1.4 Governanca E Seguranca

- Postura de seguranca.
- Criptografia de PII e indices cegos.
- Exibicao autorizada de PII no front-end para usuarios autenticados, mantendo criptografia em repouso e redaction em auditoria/exportacao.
- Hashing de senhas.
- Politica de senha forte no cadastro e no reset.
- Confirmacao de email por token seguro.
- Reset de senha por token seguro.
- Envio transacional por SMTP configuravel.
- Outbox local de desenvolvimento para testar emails sem provedor externo.
- Perfil editavel com dados profissionais, preferencias e foto.
- Upload de avatar com validacao de tipo e tamanho.
- API keys com HMAC.
- API keys com escopos operacionais e expiracao.
- Listagem de API keys na aba Governanca.
- Criacao de nova API key pela interface.
- Revogacao de API key pela interface.
- Atualizacao de ultimo uso de API key.
- Bloqueio de API key expirada.
- Audit trail recente.
- Filtro e exportacao de evidencias no audit trail.
- Migracao de dados sensiveis existentes.
- Redaction em auditoria e exportacoes.

### 1.5 Workbench E Fluxo Operacional

- Entrada guiada para novas predicoes sem exigir JSON do usuario final.
- Validacao de projeto, modelo, versao, entidade, score e features obrigatorias antes do envio.
- Mensagens de erro no proprio fluxo do Workbench.

### 1.6 Validacao

- `npm run lint`.
- `npm run build`.
- `python -m compileall app`.
- `python -m pytest`.

### 1.7 Matriz De Cobertura Atual

| Area | Status | Observacao |
| --- | --- | --- |
| Interface operacional | Completo local | Overview, Monitor, DS Lab, Predicoes, Operacao, Workbench, Governanca e Docs estao funcionais. |
| Documentacao de usuario | Completo local | Aba `Docs` cobre fluxos, limites, entradas e saidas para uso no produto. |
| Feedback operacional | Completo local | UI, API por sessao e API key com escopo `feedback:write`. |
| Alertas padrao | Completo local | Regras padrao e regras cadastradas podem ser avaliadas sob demanda. |
| Conta e perfil | Completo local | Cadastro com dados profissionais, confirmacao de email, reset de senha, perfil editavel e avatar. |
| API keys | Completo local | HMAC, escopos, expiracao, ultimo uso, criacao, listagem e revogacao. |
| Auditoria | Completo local | Eventos, redaction, filtro e exportacao de evidencias. |
| What-if | Parcial | Simulacao local funciona; execucao contra endpoint real de scoring ainda depende de integracao externa. |
| Jobs e automacao local | Completo local | Jobs persistidos e executados via `BackgroundTasks`; fila distribuida e agendamento recorrente seguem como backlog de producao. |
| Notificacoes internas | Completo local | Notificacoes persistidas, contador de nao lidas e marcacao como lida. |
| Entidades e timeline | Completo local | Pesquisa por entidade com predicoes, casos, replays e notas em linha do tempo. |
| Data contracts | Completo local | Modos `accept`, `warn` e `block`, validacao na ingestao e registro em metadata. |
| Views salvas | Completo local | Filtros e colunas salvos por usuario e aplicaveis pela interface. |
| Webhooks externos | Pendente | Requer endpoints de destino, assinatura, retry e credenciais de Slack/Teams/e-mail. |
| RBAC corporativo | Pendente | Roles existem conceitualmente, mas faltam permissoes finas por acao/projeto. |
| Model registry corporativo | Parcial | Versoes e avaliacoes existem; aprovacao formal, rollback e checklist bloqueante ainda sao backlog. |
| Suporte avancado por tipo de problema | Parcial | O documento e o schema sao flexiveis; metricas especializadas para regressao/ranking/forecasting ainda sao backlog. |

### 1.8 Produto Corporativo Implementado Nesta Etapa

- Colecao `jobs` para execucoes assicronas de alertas, drift, metricas, diagnosticos e dashboard.
- Painel **Automacao** no front-end para criar jobs e acompanhar status.
- Colecao `notifications` com notificacoes de alertas e jobs.
- Botao de notificacoes na topbar com contador de nao lidas.
- Colecao `saved_views` para salvar filtros e colunas de trabalho.
- Botao `Salvar view` em Predicoes e aplicacao de views pela area Automacao.
- Tela **Entidades** com pesquisa por ID, matricula, nome ou entidade.
- Timeline unificada de predicoes, casos, replays e notas por entidade.
- Colecao `entity_notes` para anotacoes manuais por entidade.
- Data contracts com modo `accept`, `warn` e `block`.
- Validacao de contrato de features na ingestao de predicoes.
- Bloqueio de predicao com feature obrigatoria ausente quando o contrato esta em `block`.
- Registro do resultado do contrato em `metadata.contract` e `flags.contract_status`.
- Painel para alterar modo do contrato no front-end.
- Atualizacao de status de casos operacionais pela interface.
- Endpoints para editar e excluir regras de alerta.
- Notificacao automatica quando alerta e criado.

## 2. Melhorias Globais Pendentes

### 2.1 Jobs, Filas E Automacao Continua

- Executar checks de alerta automaticamente por agenda, sem clique manual.
- Levar jobs locais para uma fila distribuida com workers independentes.
- Adicionar retry configuravel, timeout, cancelamento e logs por etapa.
- Usar Redis, RQ, Celery, Dramatiq ou equivalente em producao.
- Permitir agendamento por projeto: horario, frequencia, janela e tipo de check.
- Criar jobs longos para exportacoes grandes com progresso incremental e download posterior.

### 2.2 Alertas Avancados

- Criar regra visual pela interface, sem depender da API.
- Pausar, duplicar e versionar regras de alerta.
- Configurar janela temporal por regra.
- Configurar severidade dinamica por faixas.
- Criar escalonamento: warning -> high -> critical.
- Criar snooze de alerta.
- Associar alerta a caso operacional.
- Gerar incidente automaticamente a partir de alertas criticos recorrentes.
- Criar runbooks por tipo de alerta.
- Mostrar timeline completa de transicoes do alerta.
- Medir tempo medio de acknowledge e resolucao.

### 2.3 Feedback E Desfechos Em Escala

- Importacao de feedback em lote por CSV/XLSX.
- Webhook de feedback recebido.
- Mapeamento de labels externos para labels do modelo.
- Diferenciar feedback operacional, desfecho parcial e desfecho final.
- Suportar desfecho censurado com motivo.
- SLA de feedback por projeto, modelo, segmento e fonte.
- Fila de predicoes sem feedback por prioridade.
- Amostragem ativa: sugerir quais predicoes devem receber feedback primeiro.

### 2.4 What-if E Simulacao Avancada

- Sliders para features numericas com min/max inferido do historico.
- Selects para features categoricas com valores frequentes.
- Comparar varios cenarios lado a lado.
- Persistir cenarios pela interface usando a colecao `prediction_scenarios`.
- Nomear, versionar e comparar cenarios salvos.
- Gerar cenario automaticamente para reduzir score abaixo do threshold.
- Calcular sensibilidade local por feature.
- Conectar What-if a endpoint real de scoring.
- Exibir selo claro: `estimado` vs `modelo executado`.
- Permitir replay usando os mesmos cenarios salvos.

### 2.5 Model Registry Corporativo

- Workflow formal de versao: `draft -> staging -> production -> deprecated`.
- Promocao de versao com aprovacao obrigatoria.
- Rollback de versao pela interface.
- Registro de artefato, hash, URI, dataset, responsavel e data.
- Comparacao entre treino, validacao, teste, shadow e producao.
- Checklist de release por modelo.
- Model card obrigatorio por versao.
- Evidencias anexadas ao release.
- Historico de alteracoes com diffs entre versoes.
- Bloqueio de promocao quando metricas minimas nao forem atingidas.

### 2.6 Multiusuario, RBAC E Organizacoes

- Convite de usuarios por organizacao.
- Times e grupos.
- RBAC por role, projeto e acao.
- Permissoes finas para exportar, migrar seguranca, criar chave, revogar chave, promover modelo e resolver alerta.
- Auditoria de acesso negado.
- Sessao administrativa para revisar usuarios ativos.
- MFA com aplicativo autenticador, WebAuthn ou chave de seguranca.
- Login corporativo com OIDC/SAML.
- Separacao entre ambiente dev, staging e prod por organizacao.

### 2.7 Integracoes Reais

- Webhooks configuraveis para:
  - predicao registrada;
  - feedback recebido;
  - alerta criado;
  - alerta resolvido;
  - exportacao pronta;
  - versao promovida.
- SDK Python.
- SDK TypeScript.
- CLI para ingestao e exportacao.
- Conector para MLflow.
- Conector para DVC.
- Conector para S3, Azure Blob, GCS ou MinIO.
- Integracao com Slack, Teams e e-mail.
- OpenAPI versionada com exemplos por linguagem.
- Portal de desenvolvedores com chaves, limites e exemplos.

### 2.8 Escala E Performance

- Materializacao incremental de metricas.
- Cache com invalidacao por evento.
- Busca textual indexada.
- Indices MongoDB revisados por cardinalidade real.
- Exportacao assicrona para bases grandes.
- Streaming de download.
- Particionamento logico por projeto e periodo.
- Retencao automatica por projeto.
- Armazenamento quente/frio para predicoes antigas.
- Compactacao de payloads tecnicos grandes.
- Teste de carga com cenarios de 1M+ predicoes.

### 2.9 Observabilidade Da Plataforma

- Logs estruturados com correlation ID.
- Request ID propagado no front-end, back-end e auditoria.
- Metricas de latencia, erro, throughput e tamanho de payload.
- Tracing com OpenTelemetry.
- Painel de saude da propria plataforma.
- Alertas de indisponibilidade.
- Monitoramento de jobs.
- Auditoria de downloads de exportacao.
- Relatorio de uso por projeto/modelo.

### 2.10 Seguranca, Compliance E Privacidade

- Rotacao assistida de chaves.
- Secrets manager externo.
- Rotacao de chaves de criptografia.
- Politica de retencao por projeto.
- Base legal, finalidade e origem dos dados por dataset.
- Aprovacao para exportacao sensivel.
- Watermark em exportacoes.
- Data subject request: localizar, exportar e apagar dados por entidade.
- Relatorio LGPD/auditoria em PDF.

### 2.11 Suporte A Mais Tipos De Problema

- Multiclasse com matriz expandida.
- Regressao com MAE, RMSE, erro percentual e analise de residuos.
- Ranking com NDCG, MAP, MRR e top-k.
- Forecasting com MAPE, sMAPE, backtesting e janelas temporais.
- Anomalia com taxa de alerta, investigacao e falso positivo.
- Recomendacao com coverage, diversity e fairness.
- UI adaptativa por `problem_type`.
- Contratos de metricas por tipo de problema.

### 2.12 Produto SaaS E Administracao

- Onboarding guiado para primeiro projeto.
- Templates por dominio: churn, fraude, manutencao, educacao, credito, anomalia.
- Setup wizard para projeto, modelo, features e primeira API key.
- Ambientes separados: sandbox e production.
- Limites de uso por plano.
- Billing interno ou simulacao de plano.
- Painel de uso: predicoes, usuarios, armazenamento, exportacoes e chamadas de API.
- Pagina de status do workspace.
- Checklist de producao antes de ativar um projeto.

### 2.13 Qualidade De Dados E Contratos

- Editor visual de contrato de features.
- Validacao de tipo, faixa, cardinalidade e nulos na ingestao.
- Data quality score por dataset e por modelo.
- Historico de schema drift.
- Bloqueio ou quarentena de predicoes com contrato quebrado.
- Amostragem de exemplos invalidos.
- Comparacao entre contrato esperado e contrato observado.
- Alertas por degradacao de cobertura de feature.

### 2.14 MLOps E Ciclo De Vida

- Shadow deployment.
- Champion/challenger com roteamento de percentual de trafego.
- A/B testing de versoes.
- Canary release.
- Registro de experimentos.
- Comparacao de custo, latencia e qualidade por modelo.
- Politica de rollback automatica.
- Promocao baseada em evidencias.
- Relatorio executivo de release.

### 2.15 Experiencia Profissional De Front-End

- Atalhos de teclado.
- Views salvas por usuario.
- Filtros compartilhaveis por URL.
- Layout configuravel por persona: cientista de dados, operacao, gestor e auditor.
- Tabelas com colunas configuraveis.
- Exportacao visual de graficos.
- Tooltips tecnicos sob demanda.
- Estados de loading por bloco, nao so por pagina.
- Skeletons para telas grandes.
- Acessibilidade revisada: foco, contraste, ARIA e navegacao por teclado.
- Tema claro/escuro com preferencia por usuario.

## 3. Melhorias Locais Por Tela

### 3.1 Overview

- Seletor de periodo global.
- Comparacao contra periodo anterior.
- Meta configuravel por KPI.
- Health score configuravel por projeto.
- Drill-down a partir dos graficos.
- Tooltip executivo para explicar cada penalidade do health score.
- Alertas executivos de variacao abrupta.
- Snapshot PDF do Overview.

### 3.2 Monitor

- Historico de drift em grafico dedicado.
- Ranking das features com maior drift.
- Configuracao de limites de drift pela interface.
- Comparacao de versoes com intervalo de confianca.
- Comparacao por periodo e por segmento.
- Botao de promover, despromover e rollback de versao.
- Status de integracao por API key.

### 3.3 DS Lab

- Curva precision-recall.
- Curva ROC quando aplicavel.
- Calibracao por segmento.
- Estabilidade de feature por janela.
- Escolha da metrica-alvo do threshold.
- Notebook real exportavel com celulas preenchidas.
- Relatorio de erro com clusters de falsos positivos/negativos.
- Recomendacoes com dono, prazo e status.

### 3.4 Predicoes

- Colunas configuraveis.
- Ordenacao por coluna.
- Filtros por data, score band, decisao, fonte, request ID e feature.
- Selecionar linhas e executar acoes em lote.
- Copiar ID, request ID e payload auditavel.
- Abrir detalhe completo em rota dedicada.
- Criar anotacoes na propria predicao.
- Salvar filtros como views.

### 3.5 Decision Inspector

- Abas internas: resumo, feedback, What-if, replay, auditoria, payload e explicabilidade.
- Timeline da decisao.
- Comparacao visual entre predicao original e replay.
- Historico de feedbacks quando houver reprocessamento.
- Salvar What-if como cenario.
- Vincular predicao a caso operacional.
- Botao para abrir auditoria completa da predicao.

### 3.6 Workbench

- Preview do documento antes do envio.
- Templates de payload.
- Upload em lote por CSV/XLSX.
- Modo tecnico para colar JSON, separado do fluxo principal.
- Simulacao com API key selecionada.
- Historico dos ultimos envios da sessao.

### 3.7 Operacao

- Atribuir casos a usuarios.
- Alterar status do caso pela interface.
- SLA por caso.
- Comentarios e historico por caso.
- Conectar alerta a caso operacional.
- Criar incidente a partir de alerta.
- Painel de backlog.
- Capacidade operacional estimada.
- Kanban de casos por status.
- Filtros por severidade, responsavel e prazo.

### 3.8 Governanca

- Painel de usuarios e permissoes.
- Rotacao assistida de API keys.
- Aprovacao de exportacao sensivel.
- Retencao e base legal por projeto.
- Linhagem: dataset -> modelo -> versao -> predicao -> feedback.
- Checklist de producao com status bloqueante.

## 4. Prioridade Recomendada Atualizada

1. Agendamento recorrente de jobs com calendario, horario e frequencia.
2. Editor visual completo de regras de alerta com criacao e edicao pela interface.
3. Gerenciamento completo de casos human-in-the-loop com responsavel, SLA, comentarios e kanban.
4. Data contracts avancados com editor visual de ranges, cardinalidade e exemplos invalidos.
5. Tela de entidades com graficos historicos e comparacao entre modelos.
6. Importacao de feedback em lote, mapeamento de labels externos e webhooks de feedback.
7. RBAC completo por projeto e acao.
8. Model Release Center com aprovacao, rollback e evidencias.
9. Trust Center com controles de compliance e exportacao sensivel.
10. Busca global, filtros compartilhaveis por URL e acoes em lote.
11. Suporte formal a regressao, multiclasse, ranking e forecasting.
12. Webhooks, SDK Python, SDK TypeScript e conectores de storage/MLflow.
13. Observabilidade da plataforma com logs, metricas, tracing e health check profundo.

## 5. Novas Melhorias De Alto Valor Para Virar Produto Corporativo

As proximas ideias elevam o ModelTrace de uma plataforma local robusta para um produto mais proximo do uso diario em empresas com muitos modelos, equipes e responsabilidades.

### 5.1 Trust Center E Controles De Compliance

- Criar uma pagina `Trust Center` dentro de Governanca com status de criptografia, retencao, exportacoes, SMTP, chaves, cookies, CORS, backups e integracoes.
- Mostrar evidencias baixaveis por controle: configuracao de seguranca, trilha de auditoria, ultima rotacao de chave, politicas ativas e exportacoes sensiveis.
- Criar checklist LGPD por projeto: finalidade, base legal, origem dos dados, responsavel, tempo de retencao e processo de exclusao.
- Adicionar aprovacao obrigatoria para exportacoes sem redaction.
- Registrar motivo, aprovador e validade quando um usuario exportar dados sensiveis.

### 5.2 Entidades E Linha Do Tempo Unificada

- Adicionar graficos historicos de score, feedback e status operacional na tela `Entidades`.
- Exibir alertas, incidentes e exportacoes relacionados a uma entidade, alem de predicoes, casos, replays e notas.
- Permitir tags por entidade e filtros por tipo de evento.
- Mostrar evolucao temporal do score por modelo e por versao.
- Abrir a entidade a partir da tabela de predicoes, fila operacional ou alerta.

### 5.3 Gerenciamento De Casos Human-In-The-Loop

- Transformar a fila operacional em um fluxo completo de casos.
- Atribuir responsavel, prazo, status, prioridade, comentario, checklist e resultado.
- Criar SLA por tipo de caso e por severidade.
- Exibir kanban por status e ranking de casos vencidos.
- Conectar caso a alerta, predicao, entidade e feedback final.

### 5.4 Data Contracts Bloqueantes

- Quarentenar predicoes com features ausentes, tipos incorretos ou valores fora da faixa.
- Exibir amostras dos erros de contrato e recomendacoes de correcao.
- Gerar versao de contrato a partir de dados historicos e permitir aprovacao manual.
- Criar editor visual para tipos, ranges, valores permitidos, nulidade e exemplos invalidos.
- Medir taxa de violacao por origem, modelo, versao e janela temporal.

### 5.5 Model Release Center

- Criar uma area de release para promover versoes de modelo com evidencias.
- Exigir metricas minimas, model card aprovado, dataset identificado, contrato de features valido e teste de drift antes da promocao.
- Comparar versao candidata contra champion em producao, shadow e backtest.
- Registrar aprovadores, comentarios e diffs de configuracao.
- Permitir rollback com motivo e auditoria.

### 5.6 Notificacoes Inteligentes

- Permitir notificacoes por email, Slack, Teams e webhook.
- Agrupar alertas repetidos para reduzir ruido.
- Enviar resumo diario ou semanal por projeto.
- Adicionar regras de roteamento por severidade, modelo, dominio e equipe responsavel.
- Permitir preferencia por canal no perfil do usuario.

### 5.7 Portal De Desenvolvedores

- Criar uma pagina dedicada para integradores com API keys, exemplos, SDKs, payload builder e status da API.
- Gerar snippets em Python, TypeScript, cURL e PowerShell a partir do projeto/modelo selecionado.
- Validar payload antes do envio.
- Mostrar ultimas chamadas, erros, latencia e limites de uso por API key.
- Versionar exemplos conforme o contrato do modelo.

### 5.8 Busca Global E Views Salvas

- Adicionar busca global por predicao, entidade, request ID, modelo, alerta, caso, exportacao e auditoria.
- Permitir filtros compartilhaveis por URL.
- Criar views salvas por equipe, alem das views por usuario.
- Salvar ordenacao, periodo, projeto e permissoes de compartilhamento.
- Oferecer templates de view para cientista de dados, operador, auditor e gestor.

### 5.9 Explicabilidade Mais Acionavel

- Criar comparacao entre principais drivers do score e principais drivers de erro.
- Mostrar explicabilidade agregada por segmento.
- Adicionar analise de contrafactual: quais features teriam maior chance de mudar a decisao.
- Salvar cenarios de What-if e comparar lado a lado.
- Diferenciar claramente explicacao do modelo, regra operacional e inferencia estimada.

### 5.10 Robustez Operacional

- Mover jobs assicronos para workers dedicados com fila distribuida.
- Criar progresso por etapa, logs detalhados, retry e cancelamento.
- Adicionar OpenTelemetry para tracing.
- Registrar correlation ID entre front-end, API, jobs e auditoria.
- Criar health check profundo: banco, storage, SMTP, fila, cache e integracoes.

## 6. Papel Da Aba Governanca

A aba Governanca existe para responder perguntas que empresas fazem antes de confiar em uma plataforma com dados reais:

- Quem acessou ou alterou algo?
- Quais API keys existem?
- Os dados sensiveis estao protegidos?
- Existe trilha de auditoria?
- O sistema esta pronto para ambiente de producao?
- Como o banco documental esta organizado?
- Quais controles ainda precisam de hardening?

No estado atual, ela mostra:

- postura de seguranca;
- criptografia e indices cegos;
- hashing de senhas;
- API keys com listagem, criacao e revogacao;
- status de API keys em HMAC;
- headers de seguranca;
- usuarios com e-mail protegido;
- recomendacoes de hardening;
- botao para aplicar controles de seguranca;
- audit trail recente;
- mapa das principais colecoes documentais.

Em um produto real, essa aba deve evoluir para o centro de compliance, seguranca, auditoria, permissoes, retencao, evidencias e governanca de modelos.
