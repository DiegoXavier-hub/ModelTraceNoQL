# ModelTrace - Manual Funcional E Tecnico Da Interface

Este documento descreve a interface do ModelTrace no nivel de produto: cada tela, bloco, indicador, filtro e botao principal. Para cada item, a documentacao explica o que o usuario faz, qual valor de negocio existe por tras da funcao e como a plataforma executa tecnicamente a acao.

Arquivo principal da interface: `frontend/app/page.tsx`.

Helper HTTP usado pela interface: `frontend/lib/api.ts`.

Prefixo padrao da API: `/api/v1`.

Guia completo de consumo da API, com exemplos de `curl`, PowerShell, Python e TypeScript: [`api.md`](api.md).

## Sumario

* [1. Modelo mental do produto](#1-modelo-mental-do-produto)

* [2. Como a interface funciona](#2-como-a-interface-funciona)

* [3. Autenticacao](#3-autenticacao)

* [4. Navegacao global](#4-navegacao-global)

* [5. Overview](#5-overview)

* [6. Monitor](#6-monitor)

* [7. DS Lab](#7-ds-lab)

* [8. Predicoes](#8-predicoes)

* [9. Decision inspector](#9-decision-inspector)

* [10. Entidades](#10-entidades)

* [11. Workbench](#11-workbench)

* [12. Operacao](#12-operacao)

* [13. Automacao](#13-automacao)

* [14. Governanca](#14-governanca)

* [15. Docs](#15-docs)

* [16. Bloco de resultados das acoes](#16-bloco-de-resultados-das-acoes)

* [17. Mapa rapido de botoes e endpoints](#17-mapa-rapido-de-botoes-e-endpoints)

* [18. Observacoes tecnicas e limites](#18-observacoes-tecnicas-e-limites)

## 1. Modelo Mental Do Produto

O ModelTrace organiza a operacao de modelos de Machine Learning nestes objetos:

| Conceito         | O que representa                                                                         | Onde aparece                                                 |
| ---------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Organizacao      | Tenant logico do usuario autenticado.                                                    | Autenticacao, auditoria, isolamento dos dados.               |
| Projeto          | Produto, area de negocio ou dominio monitorado.                                          | Seletor lateral, Overview, Monitor, Operacao.                |
| Modelo           | Modelo de ML associado a um projeto.                                                     | Seletor lateral, DS Lab, Monitor, Workbench.                 |
| Versao           | Artefato ou janela de uso do modelo.                                                     | Versoes do modelo, comparacao, replay, registro de predicao. |
| Predicao         | Documento central com entidade, features, score, label, decisao, explicacoes e feedback. | Predicoes, Decision inspector, dashboards.                   |
| Feedback         | Desfecho real observado depois da predicao.                                              | Matriz de confusao, DS Lab, Decision inspector.              |
| Alerta           | Sinal operacional ativo sobre risco, qualidade, drift ou incidente.                      | Overview, Operacao.                                          |
| Caso operacional | Item acionavel para acompanhamento humano.                                               | Operacao, fila operacional.                                  |
| Notificacao      | Mensagem interna gerada por alerta, job ou evento de sistema.                            | Topbar, Automacao.                                           |
| Job              | Execucao operacional de alerta, drift, metricas, diagnostico ou dashboard.               | Automacao, `jobs`.                                           |
| View salva       | Filtros e colunas persistidos para acelerar investigacoes recorrentes.                   | Predicoes, Automacao.                                        |
| Data contract    | Regras esperadas para features, tipos, ranges e nulidade.                                | DS Lab, Automacao, ingestao.                                 |
| Nota de entidade | Anotacao operacional ligada a aluno, cliente, ativo ou qualquer entidade.                | Entidades, `entity_notes`.                                   |
| Auditoria        | Evento append-only de uso da plataforma.                                                 | Governanca, `audit_events`.                                  |

O produto nao depende de um tipo especifico de problema. O mesmo fluxo aceita risco academico, churn, manutencao, fraude, ranking, anomalia ou qualquer modelo que gere uma decisao rastreavel.

## 2. Como A Interface Funciona

A interface e uma aplicacao single-page em Next.js. O usuario navega entre abas internas sem trocar de rota. A tela principal mantem em estado local:

* sessao autenticada;

* projeto selecionado;

* modelo selecionado;

* versoes do modelo;

* dashboard do projeto;

* diagnosticos do modelo;

* predicoes paginadas;

* operacao corporativa;

* postura de seguranca;

* eventos de auditoria;

* ultimo resultado de acao executada.

Todas as chamadas HTTP passam por `apiRequest` em `frontend/lib/api.ts`. Esse helper:

* monta a URL com `NEXT_PUBLIC_API_URL`;

* envia `Content-Type: application/json`;

* adiciona `Authorization: Bearer <token>` quando existe token;

* usa `credentials: "include"` para permitir cookies `HttpOnly`;

* retorna `{ data, error, status }`;

* evita cache de browser com `cache: "no-store"`.

### Atualizacao De Dados

O fluxo principal de atualizacao chama `refreshAll`. Ele carrega:

* projetos: `GET /projects`;

* modelos do projeto: `GET /projects/{project_id}/models`;

* dashboard do projeto: `GET /projects/{project_id}/dashboard`;

* operacao do projeto: `GET /projects/{project_id}/operations`;

* postura de seguranca: `GET /security/posture`;

* auditoria: `GET /projects/{project_id}/audit-events`;

* versoes do modelo: `GET /models/{model_id}/versions`;

* diagnosticos do modelo: `GET /models/{model_id}/diagnostics`;

* predicoes filtradas quando a aba de predicoes esta ativa: `GET /predictions`.

* notificacoes: `GET /notifications`;

* jobs: `GET /jobs`;

* views salvas: `GET /saved-views`;

* contrato de dados do projeto/modelo: `GET /projects/{project_id}/data-contract`.

As predicoes usam paginacao no servidor com tamanho de pagina `250`. Isso evita renderizar dezenas de milhares de linhas no browser.

### Notificacoes

Acoes de botao chamam `notify`. A funcao atualiza:

* `status`, exibido na faixa de status;

* `notice`, exibido como toast de sucesso, erro ou informacao.

Assim o usuario recebe retorno imediato quando clica em Atualizar, Sair, Drift, Equidade, Exportar, What-if, Replay, Feedback, API key ou Aplicar controles.

## 3. Autenticacao

Tela exibida quando nao ha sessao em `sessionStorage`.

| Elemento              | Funcao para o usuario              | Como e feito tecnicamente                                                                                             |
| --------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Campo e-mail          | Identifica o usuario.              | Usado no payload de login/cadastro. No back-end o e-mail e protegido por criptografia e indice cego.                  |
| Campo senha           | Autentica a sessao.                | Senhas sao validadas contra hash PBKDF2-SHA256 versionado.                                                            |
| Campo nome            | Usado no cadastro inicial.         | Enviado no cadastro para criar o usuario.                                                                             |
| Botao `Entrar`        | Inicia sessao existente.           | Chama `POST /auth/login`; salva access token, refresh token e usuario em `sessionStorage`; depois chama `refreshAll`. |
| Botao `Registrar`     | Cria usuario e organizacao local.  | Chama `POST /auth/register`; depois aplica o mesmo fluxo de sessao do login.                                          |
| Toast de erro/sucesso | Confirma login, cadastro ou falha. | Usa `notify` com `tone` `success`, `error` ou `info`.                                                                 |

Endpoints principais:

```txt
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
```

## 4. Navegacao Global

### Sidebar

| Elemento                         | Funcao para o usuario                            | Como e feito tecnicamente                                                                                |
| -------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Logo `ModelTrace / Decision Ops` | Identifica o workspace.                          | Elemento visual local.                                                                                   |
| Aba `Overview`                   | Visao executiva do projeto.                      | Define `activeView = "overview"`.                                                                        |
| Aba `Monitor`                    | Ferramentas de monitoramento e integracao.       | Define `activeView = "monitor"`.                                                                         |
| Aba `DS Lab`                     | Diagnosticos para cientista de dados.            | Define `activeView = "lab"` e usa diagnosticos do modelo.                                                |
| Aba `Predicoes`                  | Lista operacional das predicoes.                 | Define `activeView = "predictions"` e aciona carregamento paginado.                                      |
| Aba `Entidades`                  | Linha do tempo de uma entidade especifica.       | Define `activeView = "entities"` e usa `GET /projects/{project_id}/entity-timeline`.                     |
| Aba `Operacao`                   | Alertas, casos, incidentes, coortes e qualidade. | Define `activeView = "operations"`.                                                                      |
| Aba `Automacao`                  | Jobs, notificacoes, contracts e views salvas.    | Define `activeView = "control"` e carrega recursos operacionais auxiliares.                              |
| Aba `Workbench`                  | Entrada guiada para novas predicoes.             | Define `activeView = "workbench"`.                                                                       |
| Aba `Governanca`                 | Seguranca, auditoria e modelo documental.        | Define `activeView = "governance"`.                                                                      |
| Aba `Docs`                       | Manual de uso dentro do produto.                 | Define `activeView = "docs"` e usa `docSections` para trocar os topicos.                                 |
| Seletor `Projeto`                | Troca o projeto monitorado.                      | Atualiza `selectedProjectId`; a interface recarrega modelos, dashboard, operacao, auditoria e seguranca. |
| Seletor `Modelo`                 | Troca o modelo analisado.                        | Atualiza `selectedModelId`; a interface recarrega versoes e diagnosticos.                                |
| Rodape `API online`              | Mostra a API configurada.                        | Le `API_URL` em `frontend/lib/api.ts`.                                                                   |

### Topbar

| Elemento          | Funcao para o usuario               | Como e feito tecnicamente                                                                                     |
| ----------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Titulo do projeto | Mostra projeto, dominio e ambiente. | Usa `selectedProject` e `domain`; quando nao ha projeto, mostra estado vazio.                                 |
| Botao `Comandos`  | Abre busca de acoes, telas e documentacao. | Abre a command palette (`components/shell/CommandPalette.tsx`); tambem responde a `Cmd+K` / `Ctrl+K`. O botao mostra o atalho visivel ao lado do label. |
| Botao `Notificacoes` | Abre o painel lateral de notificacoes; mostra badge numerico com nao lidas. | Renderiza `NotificationsDrawer` (`components/shell/NotificationsDrawer.tsx`); responde a `Cmd+/` / `Ctrl+/`. |
| Botao `Atualizar` | Recarrega o workspace inteiro.      | Executa `refreshWorkspace`, que chama `refreshAll(token)` e exibe toast. Atalho `R`.                          |
| Botao `Sair`      | Encerra a sessao.                   | Chama `POST /auth/logout`, remove `modeltrace_session` do `sessionStorage`, limpa estado local. Atalho `Shift+Q`. |
| Faixa de status   | Mostra o ultimo evento importante.  | Exibe a string `status`, atualizada por `notify`.                                                             |

### Atalhos De Teclado

A partir da versao 2 o produto tem atalhos completos. Apertar `?` em qualquer tela abre o modal `ShortcutsModal` com a lista completa.

**Globais (independentes de aba):**

| Atalho             | Acao                             |
| ------------------ | -------------------------------- |
| `Cmd+K` / `Ctrl+K` | Abrir command palette            |
| `Cmd+/` / `Ctrl+/` | Abrir painel de notificacoes     |
| `?`                | Abrir lista de atalhos           |
| `R`                | Atualizar workspace              |
| `T`                | Alternar tema (claro/escuro)     |
| `Shift+Q`          | Sair (logout)                    |
| `Esc`              | Fechar modais e overlays abertos |

**Navegacao por aba (prefixo `G`):**

| Atalho | Aba             |
| ------ | --------------- |
| `G O`  | Overview        |
| `G M`  | Monitor         |
| `G C`  | Compare         |
| `G X`  | Drift           |
| `G S`  | Casos (SLA)     |
| `G U`  | Custo & Consumo |
| `G L`  | DS Lab          |
| `G P`  | Predicoes       |
| `G Q`  | Operacao        |
| `G E`  | Entidades       |
| `G A`  | Automacao       |
| `G W`  | Workbench       |
| `G V`  | Governanca      |
| `G D`  | Docs            |

Comportamento:

* atalhos sem modificador sao ignorados quando o foco esta em campo de texto;
* prefixo `G` aguarda a segunda tecla por 1.2 segundos;
* `Cmd+K` e `Cmd+/` funcionam dentro de inputs;
* na sidebar, cada item da nav mostra seu atalho ao lado.

### Painel De Notificacoes

Abre como drawer lateral de 440px no canto direito.

| Elemento                  | Funcao para o usuario                                              | Como e feito tecnicamente                                              |
| ------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| Cabecalho com contador    | Mostra "Tudo em dia" ou "X nao lidas".                             | Usa `unreadCount` calculado de `notifications.filter(!read)`.           |
| Botao `Marcar lidas`      | Marca todas como lidas em massa.                                   | Faz `POST /notifications/{id}/read` para cada nao lida e refresca.      |
| Botao `Fechar` (`X`)      | Fecha o drawer.                                                    | Define `notificationsOpen = false`. Tambem responde a `Esc`.            |
| Aba `Todas`               | Lista todas as notificacoes.                                       | Filtro `() => true`.                                                    |
| Aba `Nao lidas`           | Filtra apenas itens com `read=false`.                              | Filtro `(n) => !n.read`.                                                |
| Aba `Alertas`             | Filtra alertas e incidentes.                                       | Filtro por `category/topic/resource_type` contendo `alert`.             |
| Aba `Jobs`                | Filtra notificacoes de jobs.                                       | Filtro por `category/topic/resource_type` contendo `job`.               |
| Aba `Sistema`             | Filtra eventos de sistema.                                         | Filtro por `category === "system"`.                                     |
| Item nao lido             | Aparece com gradient suave de destaque.                            | Classe `.notif-item.unread`.                                            |
| Clique em item            | Faz deep-link para o objeto relacionado e fecha o drawer.          | `handleNotificationSelect`: `alert/incident → operations`, `prediction → predictions`, `job → control`. |

## 5. Overview

A aba Overview entrega a leitura executiva do projeto selecionado.

### Saude Operacional Do Modelo

| Elemento               | Funcao para o usuario                              | Como e feito tecnicamente                                                             |
| ---------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Anel `health`          | Resume a prontidao operacional do modelo.          | Calculado no front-end com KPIs do dashboard.                                         |
| Tags de versao/metrica | Mostram contexto do modelo.                        | Usam `versions.length`, `selectedModel.primary_metric` e `productionVersion.version`. |
| Breakdown `Base`       | Pontuacao inicial do indice.                       | Valor fixo `28`.                                                                      |
| Breakdown `Feedback`   | Premia cobertura de feedback.                      | `min(feedback_rate / 0.45, 1) * 34`.                                                  |
| Breakdown `Recall`     | Premia desempenho observado.                       | `dashboard.performance.recall * 38`; se nao houver recall, usa `22`.                  |
| Breakdown `Alertas`    | Penaliza alertas ativos.                           | `min(active_alerts, 4) * 8`.                                                          |
| Breakdown `Acionaveis` | Penaliza volume acionavel acima da faixa esperada. | `max(actionable_rate - 0.22, 0) * 80`.                                                |

Formula resumida:

```txt
health = clamp(
  28 + feedback_score + performance_score - alert_penalty - actionable_penalty,
  8,
  100
)
```

O valor nao e acuracia. Ele mede se a operacao esta em condicao de acompanhamento: volume, feedback, alertas e desempenho observado.

### Proximas Melhores Acoes

| Elemento                 | Funcao para o usuario                                 | Como e feito tecnicamente                              |
| ------------------------ | ----------------------------------------------------- | ------------------------------------------------------ |
| Card de feedback baixo   | Indica necessidade de ampliar desfechos.              | Aparece quando `feedback_rate < 0.35`.                 |
| Card de volume acionavel | Indica pressao operacional.                           | Aparece quando `actionableRate > 0.2`.                 |
| Card de operacao estavel | Confirma que indicadores estao dentro da faixa atual. | Aparece quando nao existem alertas de feedback/volume. |
| Card de governanca       | Lembra que auditoria e colecoes estao disponiveis.    | Sempre adicionado ao bloco.                            |

### Cards De KPI

| Card          | Ao clicar                                               | Como e feito tecnicamente                           |
| ------------- | ------------------------------------------------------- | --------------------------------------------------- |
| `Predicoes`   | Abre a aba Predicoes sem filtro adicional.              | Chama `openPredictions()`.                          |
| `Acionaveis`  | Abre Predicoes filtrando pelo label positivo do modelo. | Chama `openPredictions(positiveLabel, "all")`.      |
| `Feedback`    | Abre Predicoes mostrando itens com feedback.            | Chama `openPredictions("all", "with")`.             |
| `Score medio` | Abre Predicoes no filtro geral.                         | Chama `openPredictions("all", "all")`.              |
| `Alertas`     | Abre Operacao e rola ate Alertas ativos.                | Chama `goToSection("operations", "active-alerts")`. |

### Graficos

| Bloco                   | O que mostra                           | Como e feito tecnicamente                                                             |
| ----------------------- | -------------------------------------- | ------------------------------------------------------------------------------------- |
| `Volume temporal`       | Quantidade de predicoes por dia.       | Usa `dashboard.volume_series`, produzido por `build_project_dashboard`.               |
| `Distribuicao de score` | Histograma em faixas de 0.1.           | Usa `dashboard.score_histogram`, calculado em `backend/app/services/metrics.py`.      |
| `Matriz de confusao`    | Total de TP, FP, TN e FN com feedback. | Usa `dashboard.confusion_matrix`; so conta predicoes com `feedback.available = true`. |

## 6. Monitor

A aba Monitor concentra acoes operacionais do modelo selecionado.

### Botoes Do Monitor

| Botao               | Funcao para o usuario                                               | Como e feito tecnicamente                                                                                               |
| ------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `Atualizar monitor` | Recarrega dashboard, operacao, auditoria, seguranca e diagnosticos. | Executa `refreshMonitor`, que chama `refreshAll(token)`.                                                                |
| `Gerar API key`     | Cria chave para integrar sistemas externos.                         | Chama `POST /projects/{project_id}/api-keys` com nome padrao. A chave completa aparece uma unica vez.                   |
| `Comparar versoes`  | Compara uma versao challenger com a versao em producao.             | Chama `GET /models/{model_id}/versions/compare?a={challenger}&b={production}`.                                          |
| `Rodar drift`       | Calcula drift de score e features numericas.                        | Chama `POST /models/{model_id}/drift/run`.                                                                              |
| `Equidade`          | Analisa diferencas por grupo de uma feature.                        | Chama `GET /models/{model_id}/bias-analysis?feature={biasFeature}`.                                                     |
| `Exportar CSV`      | Cria exportacao das predicoes filtradas.                            | Chama `POST /exports` com `format: "csv"`, `include_features: true`, `include_explanations: true` e `redact_pii: true`. |

### Versoes Do Modelo

| Elemento                       | Funcao para o usuario                       | Como e feito tecnicamente                                                   |
| ------------------------------ | ------------------------------------------- | --------------------------------------------------------------------------- |
| Lista de versoes               | Mostra versao, status e algoritmo.          | Usa `GET /models/{model_id}/versions`.                                      |
| Destaque de producao           | Identifica a versao ativa.                  | Aplica classe visual quando `version.status === "production"`.              |
| Metrica da versao              | Mostra a melhor metrica offline disponivel. | Prioriza `f2`, `pr_auc`, `average_precision`, `threshold_top10` e `recall`. |
| Seletor de feature de equidade | Define a feature usada no botao Equidade.   | Usa `selectedModel.expected_features`; fallback `signal_value`.             |

### Resumo Do Produto

| Elemento       | Funcao para o usuario                        | Como e feito tecnicamente                                                  |
| -------------- | -------------------------------------------- | -------------------------------------------------------------------------- |
| Projeto        | Nome do projeto selecionado.                 | Usa `selectedProject.name`.                                                |
| Dominio        | Dominio de negocio.                          | Usa `selectedProject.domain`.                                              |
| Modelos ativos | Quantidade de modelos carregados no projeto. | Usa `models.length`.                                                       |
| Predicoes      | Volume total no dashboard.                   | Usa `kpis.total_predictions` ou `selectedProject.stats.total_predictions`. |
| Descricao      | Contexto do projeto.                         | Usa `selectedProject.description`.                                         |

## 7. DS Lab

A aba DS Lab e voltada ao cientista de dados. Ela transforma predicoes online e feedback real em diagnosticos de melhoria.

Endpoint principal:

```txt
GET /models/{model_id}/diagnostics
GET /models/{model_id}/diagnostics?slice_feature={feature}
```

Servico principal:

```txt
backend/app/services/diagnostics.py
```

### Botoes Do DS Lab

| Botao              | Funcao para o usuario                                        | Como e feito tecnicamente                                                                   |
| ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `Atualizar DS Lab` | Recalcula ou recarrega diagnosticos.                         | Chama `refreshDiagnosticsWithToast`; internamente usa `GET /models/{model_id}/diagnostics`. |
| `Drift`            | Executa o mesmo relatorio de drift do Monitor.               | Chama `POST /models/{model_id}/drift/run`.                                                  |
| `Equidade`         | Executa analise por grupo da feature selecionada no Monitor. | Chama `GET /models/{model_id}/bias-analysis`.                                               |
| `Exportar pacote`  | Baixa um JSON local com diagnosticos atuais.                 | Cria um `Blob` no browser a partir de `diagnostics`; nao chama endpoint de exportacao.      |

### Cards Principais

| Card             | O que mostra                             | Como e feito tecnicamente                                             |
| ---------------- | ---------------------------------------- | --------------------------------------------------------------------- |
| `Amostra online` | Total de predicoes do modelo.            | `diagnostics.summary.prediction_count`.                               |
| `Feedback real`  | Proporcao com desfecho real.             | `feedback_count / prediction_count`.                                  |
| `Threshold F2`   | Threshold recomendado para maximizar F2. | Varre thresholds de `0.05` a `0.95` em passos de `0.05`.              |
| `ECE`            | Expected Calibration Error.              | Media ponderada do gap entre score medio e taxa observada por bucket. |
| `Brier`          | Erro quadratico medio de probabilidade.  | Media de `(score - resultado_real)^2`.                                |

### Threshold Optimizer

| Elemento        | Funcao para o usuario                                | Como e feito tecnicamente                                              |
| --------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| Linha F2        | Mostra qualidade do threshold para recall ponderado. | Calcula TP/FP/TN/FN para cada threshold usando predicoes com feedback. |
| Linha Recall    | Mostra cobertura dos positivos reais.                | `tp / (tp + fn)`.                                                      |
| Linha Precision | Mostra qualidade dos acionaveis.                     | `tp / (tp + fp)`.                                                      |
| Workload rate   | Mede volume de casos acima do threshold.             | Usa todos os scores, inclusive sem feedback.                           |

O F2 foi escolhido porque em operacoes de risco normalmente perder um positivo real pode custar mais que revisar um falso positivo.

### Simulador De Threshold

| Elemento                     | Funcao para o usuario                              | Como e feito tecnicamente                                            |
| ---------------------------- | -------------------------------------------------- | -------------------------------------------------------------------- |
| Slider                       | Permite testar threshold visualmente.              | Atualiza `selectedThreshold`.                                        |
| Precision/Recall/F2/Workload | Mostra as metricas da linha mais proxima da curva. | Seleciona o item de `threshold_curve` com menor distancia do slider. |

O simulador nao altera o modelo nem a producao. Ele apenas ajuda a avaliar uma proposta de threshold.

### Calibracao Online

| Elemento              | Funcao para o usuario                | Como e feito tecnicamente                                                   |
| --------------------- | ------------------------------------ | --------------------------------------------------------------------------- |
| Linha `avg_score`     | Score medio por bucket.              | Buckets de 0.1 em `diagnostics.calibration.bins`.                           |
| Linha `observed_rate` | Taxa real observada no mesmo bucket. | Usa feedback real (`tp/fn` como positivo real, `fp/tn` como negativo real). |
| ECE                   | Desalinhamento agregado.             | Soma ponderada dos gaps por bucket.                                         |
| Brier                 | Qualidade probabilistica geral.      | Media dos erros quadraticos.                                                |

### Melhores Proximas Analises

| Elemento                   | Funcao para o usuario                   | Como e feito tecnicamente                                        |
| -------------------------- | --------------------------------------- | ---------------------------------------------------------------- |
| Recomendacao de feedback   | Prioriza coleta de desfecho.            | Gerada quando `feedback_count < 50`.                             |
| Recomendacao de threshold  | Sugere revisao operacional.             | Gerada quando threshold F2 difere do padrao em pelo menos `0.1`. |
| Recomendacao de calibracao | Indica desalinhamento de score.         | Gerada quando `ECE >= 0.08`.                                     |
| Recomendacao de contrato   | Indica feature obrigatoria com missing. | Gerada quando feature obrigatoria tem missing rate acima de 5%.  |

### Feature Intelligence

| Elemento            | Funcao para o usuario                                       | Como e feito tecnicamente                                    |
| ------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| Ranking de features | Mostra drivers mais relevantes nas explicacoes registradas. | Agrega `prediction.explanations[].impact` por feature.       |
| Barra de impacto    | Mostra impacto medio absoluto.                              | Usa `avg_abs_impact`.                                        |
| Direcao dominante   | Indica se a feature costuma elevar ou reduzir score.        | Calculada no back-end como `raises_score` ou `lowers_score`. |

Essa analise depende das explicacoes enviadas junto com cada predicao. Ela nao substitui interpretabilidade offline do modelo.

### Contrato De Features

| Elemento        | Funcao para o usuario                             | Como e feito tecnicamente                                  |
| --------------- | ------------------------------------------------- | ---------------------------------------------------------- |
| Feature         | Nome esperado pelo modelo.                        | Vem de `models.expected_features`.                         |
| Tipo            | Tipo declarado da feature.                        | `numeric`, `boolean`, `categorical`, `text` ou `datetime`. |
| Obrigatoriedade | Indica se a feature e requerida.                  | Usa `feature.required`.                                    |
| Cobertura       | Percentual de predicoes com valor presente.       | `present / total_predictions`.                             |
| Type mismatch   | Divergencia entre tipo esperado e valor recebido. | Validado em `_type_ok`.                                    |

### Slice Diagnostics

| Elemento           | Funcao para o usuario           | Como e feito tecnicamente                                   |
| ------------------ | ------------------------------- | ----------------------------------------------------------- |
| Seletor de feature | Escolhe segmento para analisar. | Atualiza `selectedSliceFeature` e recarrega diagnostico.    |
| Grupo              | Valor ou faixa da feature.      | Numericas sao agrupadas por quartis; categoricas por valor. |
| Total              | Volume do grupo.                | Contagem de predicoes no slice.                             |
| Score medio        | Media do score no grupo.        | Media de `prediction.score`.                                |
| Acionavel          | Taxa de label positivo.         | Positivos / total do grupo.                                 |
| Feedback           | Quantidade com desfecho real.   | `feedback.available`.                                       |
| Precision/Recall   | Desempenho observado no grupo.  | Calculado a partir de TP/FP/FN.                             |

Slices indicam diferencas operacionais por segmento. Eles nao provam causalidade sozinhos.

### Falsos Positivos E Falsos Negativos Prioritarios

| Bloco                           | Funcao para o usuario                               | Como e feito tecnicamente                                                               |
| ------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `Falsos positivos prioritarios` | Mostra casos acionados que deram negativo real.     | Lista predicoes com `feedback.classification_result = "fp"`, ordenadas por maior score. |
| `Falsos negativos prioritarios` | Mostra casos nao acionados que deram positivo real. | Lista predicoes com `feedback.classification_result = "fn"`, ordenadas por menor score. |
| Botao de cada caso              | Mostra o caso como item clicavel.                   | Hoje e visual; pode evoluir para abrir a predicao diretamente.                          |

## 8. Predicoes

A aba Predicoes e a tela operacional para investigar documentos individuais.

Endpoint principal:

```txt
GET /predictions
```

Filtros aceitos:

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

### Cabecalho E Fatos

| Elemento                        | Funcao para o usuario                                     | Como e feito tecnicamente                                                                               |
| ------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Titulo `Historico de predicoes` | Mostra volume carregado e total filtrado.                 | Usa `predictions.length` e `predictionTotal`.                                                           |
| Botao `Registrar predicao`      | Cria uma predicao de exemplo com o modelo atual.          | Chama `sendDemoPrediction`, que monta payload com `buildPredictionPayload` e envia `POST /predictions`. |
| Fatos por janela                | Resume entidades, predicoes e feedback por versao/janela. | Usa `dashboard.version_summary`.                                                                        |
| Filtro atual                    | Mostra total filtrado e estado de carregamento.           | Usa `totalVisiblePredictions` e `predictionsLoading`.                                                   |

### Filtros

| Filtro   | Funcao para o usuario                          | Como e feito tecnicamente                                                    |
| -------- | ---------------------------------------------- | ---------------------------------------------------------------------------- |
| Busca    | Pesquisa por ID, entidade, label ou resultado. | Atualiza `q`; o back-end filtra campos relevantes em memoria no store atual. |
| Label    | Filtra positivo, negativo ou todos.            | Envia `label` para `GET /predictions`.                                       |
| Janela   | Filtra por versao do modelo.                   | Envia `model_version`.                                                       |
| Feedback | Filtra todos, com desfecho ou pendente.        | Envia `feedback_available=true/false`.                                       |

### Tabela

| Coluna   | O que mostra                               | Fonte                                                             |
| -------- | ------------------------------------------ | ----------------------------------------------------------------- |
| ID       | ID da predicao.                            | `prediction._id`.                                                 |
| Entidade | ID pseudonimizado ou exibivel da entidade. | `prediction.entity.id`.                                           |
| Versao   | Versao/janela do modelo.                   | `prediction.model_version`.                                       |
| Label    | Label gerado pelo modelo.                  | `prediction.prediction.label`.                                    |
| Score    | Score numerico.                            | `prediction.prediction.score`.                                    |
| Feedback | Resultado real quando existe.              | `prediction.feedback.classification_result`; fallback `pendente`. |
| Data     | Data de registro.                          | `prediction.created_at`.                                          |

Clicar em uma linha atualiza `selectedPredictionId` e abre os detalhes no Decision inspector.

### Paginacao

| Botao      | Funcao para o usuario | Como e feito tecnicamente                                    |
| ---------- | --------------------- | ------------------------------------------------------------ |
| `Anterior` | Volta uma pagina.     | Reduz `predictionPage`, respeitando minimo `1`.              |
| `Proxima`  | Avanca uma pagina.    | Aumenta `predictionPage`, respeitando `predictionPageCount`. |

Cada pagina solicita no maximo `250` itens do servidor.

## 9. Decision Inspector

O Decision inspector mostra uma predicao selecionada e suas acoes de investigacao.

### Blocos Do Inspector

| Bloco             | Funcao para o usuario                                               | Como e feito tecnicamente                                                                         |
| ----------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Cabecalho         | Mostra ID, entidade e versao.                                       | Usa `selectedPrediction`.                                                                         |
| Barra de score    | Mostra intensidade do score.                                        | Largura proporcional a `prediction.score * 100`.                                                  |
| Feature list      | Mostra principais explicacoes.                                      | Lista ate 5 itens de `prediction.explanations`.                                                   |
| Auditoria tecnica | Exibe detalhes da decisao.                                          | Componente `PredictionTechnicalDetails`; mostra predicao, modelo, versao, request, acao e status. |
| Resultado da acao | Mostra ultimo resultado de Feedback, What-if, Replay ou Exportacao. | Usa `AnalysisBlock` quando existe `analysisResult`.                                               |

### Botao Feedback

| Item                | Descricao                                                                                              |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| Funcao              | Registra feedback completo para a predicao selecionada.                                                |
| Quando usar         | Quando o usuario conhece o desfecho real ou precisa marcar o caso como inconclusivo.                   |
| Endpoint            | `POST /predictions/{prediction_id}/feedback`.                                                          |
| Payload atual da UI | Envia `observed_label`, `observed_value`, `source` e `notes`.                                          |
| Back-end            | `add_feedback` em `backend/app/services/predictions.py`.                                               |
| API key             | Tambem aceita API key do mesmo projeto com escopo `feedback:write`.                                    |
| Resultado           | O back-end compara label/threshold da predicao com o valor observado e grava `tp`, `fp`, `tn`, `fn` ou `inconclusive`. |
| Efeitos secundarios | Atualiza documentos de predicao, metricas futuras, auditoria e dashboards depois do refresh.           |

### Botao What-if

| Item        | Descricao                                                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Funcao      | Simula como o score poderia mudar se algumas features fossem diferentes.                                                               |
| Quando usar | Para investigar sensibilidade da decisao antes de propor ajustes no modelo, nas features ou no processo.                               |
| Endpoint    | `POST /predictions/{prediction_id}/whatif`.                                                                                            |
| Payload     | `{ "hypothetical_features": { ... } }`.                                                                                                |
| Back-end    | `estimate_what_if` em `backend/app/services/whatif.py`.                                                                                |
| Saida       | `original_score`, `estimated_score`, `estimated_delta`, `threshold`, `would_change_decision`, `changed_features` e aviso metodologico. |

Como a UI monta o cenario:

1. Seleciona a predicao atual.
2. Carrega ate 10 features existentes no documento.
3. Permite edicao manual por input numerico/textual ou select booleano.
4. Oferece presets `Otimista`, `Conservador` e `Reset`.
5. Converte valores numericos e booleanos antes de enviar.
6. Se a predicao nao tiver features, cria `signal_value` a partir do score atual.
7. Envia o cenario para o back-end.

Como o back-end estima:

1. Le as features originais da predicao.
2. Le o score original e o threshold.
3. Monta um mapa de impactos a partir de `prediction.explanations`.
4. Para features academicas conhecidas, calcula mudanca de risco com regras especificas:

   * `attendance_rate`: risco = `1 - attendance_rate`;

   * `avg_grade`: risco = `1 - avg_grade / 100`;

   * `failed_subjects`: risco = `min(value / 5, 1)`;

   * `credits_completed`: risco = `1 - min(value / 120, 1)`;

   * `night_shift`: risco = `1` quando verdadeiro;

   * `scholarship`: risco = `0` quando verdadeiro.
5. Para features genericas, usa uma aproximacao baseada no impacto registrado.
6. Soma os deltas ao score original.
7. Limita o score final entre `0` e `1`.
8. Informa se a decisao passaria ou nao do threshold.

Ponto importante: o What-if atual e uma estimativa baseada em impactos salvos, nao uma nova inferencia do modelo real. Para virar inferencia real em producao, a plataforma precisaria receber um endpoint de scoring por modelo ou integrar o artefato de modelo ao back-end.

### Botao Replay

| Item                | Descricao                                                                                              |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| Funcao              | Registra uma simulacao de decisao contra uma versao alvo.                                              |
| Quando usar         | Para comparar se uma decisao historica mudaria em outro contexto de versao.                            |
| Endpoint            | `POST /predictions/{prediction_id}/replay`.                                                            |
| Payload atual da UI | `target_version` e `replay_score`.                                                                     |
| Back-end            | Rota `prediction_replay` em `backend/app/api/routes/predictions.py`.                                   |
| Resultado           | Documento em `prediction_replays` com score original, score replay, label replay e `decision_changed`. |
| Auditoria           | Cria evento `prediction.replay_created`.                                                               |

A UI atual gera um replay simples reduzindo o score em `0.12`, limitado entre `0` e `1`, e usa a versao de producao como alvo quando disponivel.

### Botao Exportar

| Item            | Descricao                                                                      |
| --------------- | ------------------------------------------------------------------------------ |
| Funcao          | Cria exportacao de predicoes para auditoria ou analise externa.                |
| Endpoint        | `POST /exports`.                                                               |
| Formato atual   | CSV.                                                                           |
| Protecao padrao | `redact_pii: true`.                                                            |
| Inclui          | Features e explicacoes.                                                        |
| Back-end        | `backend/app/api/routes/exports.py`.                                           |
| Resultado       | Documento em `exports`, arquivo local em `backend/.data/exports` no modo JSON. |

## 10. Entidades

A tela Entidades existe para investigar uma pessoa, aluno, cliente, ativo, maquina, empresa ou qualquer outro objeto monitorado pelo projeto. Ela consolida eventos que normalmente ficariam espalhados: predicoes, casos operacionais, replays e notas.

### Pesquisa De Entidade

| Elemento | Funcao para o usuario | Como e feito tecnicamente |
| -------- | --------------------- | ------------------------- |
| Campo de busca | Recebe ID, matricula, nome exibido ou identificador equivalente. | Atualiza `entityQuery` no front-end. |
| Botao `Pesquisar` | Carrega a linha do tempo da entidade. | Chama `GET /projects/{project_id}/entity-timeline?q={valor}`. |
| Botao `Usar entidade selecionada` | Copia a entidade da predicao aberta no inspector. | Usa `selectedPrediction.entity.id` ou `display_name` e preenche a busca. |

O back-end primeiro tenta encontrar a entidade pelo indice cego, usando a mesma estrategia de pseudonimizacao aplicada nas predicoes. Quando nao encontra correspondencia direta, ele faz fallback seguro em campos exibiveis ja autorizados para a interface, como ID revelado ou nome exibido.

### Linha Do Tempo

A resposta da API retorna listas separadas e uma lista consolidada em `events`. O front-end mostra contadores para predicoes, casos, replays, notas e eventos totais. Cada item da linha do tempo exibe tipo, titulo, data e contexto tecnico suficiente para auditoria.

Na pratica, essa tela ajuda um cientista de dados a responder perguntas como: quantas vezes esta entidade foi avaliada, se houve mudanca de score entre versoes, se algum replay mudou a decisao, se existe caso operacional aberto e quais anotacoes humanas foram registradas.

### Notas De Entidade

| Elemento | Funcao para o usuario | Como e feito tecnicamente |
| -------- | --------------------- | ------------------------- |
| Campo `Adicionar nota` | Registra observacao operacional sobre a entidade. | Atualiza `entityNote`. |
| Botao `Salvar nota` | Persiste a anotacao sem alterar predicoes antigas. | Chama `POST /projects/{project_id}/entity-notes`. |
| Lista de notas | Mostra historico manual da entidade. | Vem da colecao `entity_notes`. |

Notas sao documentos separados para nao poluir a predicao original. A predicao continua sendo evidencia tecnica do modelo, enquanto a nota registra contexto humano posterior.

## 11. Workbench

O Workbench permite registrar predicoes sem exigir que o usuario escreva JSON.

### Registro Assistido

| Campo/Botao                | Funcao para o usuario                    | Como e feito tecnicamente                                                             |
| -------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------- |
| `ID da entidade`           | Identifica a entidade avaliada.          | Entra em `payload.entity.id`; o back-end protege com criptografia/indice cego.        |
| `Nome exibido`             | Nome amigavel para operacao.             | Entra em `payload.entity.display_name`; pode ser protegido na migracao de seguranca.  |
| `Janela do modelo`         | Escolhe versao/janela usada.             | Usa lista de `versions`.                                                              |
| `Score do modelo`          | Informa o score produzido externamente.  | Normalizado entre `0` e `1`.                                                          |
| Campos de features         | Capturam features esperadas pelo modelo. | Gerados dinamicamente a partir de `selectedModel.expected_features`.                  |
| Botao `Registrar predicao` | Envia predicao completa.                 | Chama `sendGuidedPrediction`, que usa `buildPredictionPayload` e `POST /predictions`. |

Antes do envio, `validatePredictionPayload` verifica projeto, modelo, versao, entidade, score e features obrigatorias. Quando existe erro, o Workbench mostra a lista no proprio bloco e nao envia a predicao.

### Como O Payload E Montado

`buildPredictionPayload` cria:

* `project_id`, `model_id` e `model_version`;

* `entity` com ID, tipo e nome exibido;

* `features` a partir dos campos do formulario;

* `prediction.score`, `prediction.label`, `threshold`, `score_band` e `above_threshold`;

* `explanations` com as duas principais features preenchidas;

* `decision.action`, como `human_review` para label positivo e `monitor` para label negativo;

* `metadata.source_system = "guided_simulator"`;

* `metadata.environment = "product_simulation"`;

* `metadata.request_id = "ui_<timestamp>"`.

### Integracao Segura

| Elemento                        | Funcao para o usuario                           | Como e feito tecnicamente                                                     |
| ------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------- |
| `API key ativa`                 | Mostra prefixo da chave ativa criada na sessao. | Usa estado local `apiKey`; a chave completa so aparece no momento da criacao. |
| `Decisao simulada`              | Mostra o label previsto pelo threshold atual.   | Compara `simScore` com `selectedModel.default_threshold`.                     |
| `Exemplo de integracao`         | Mostra comando `curl` para sistemas externos.   | Usa `API_URL` e a API key atual ou placeholder.                               |
| Resultado `Predicao registrada` | Confirma retorno da API.                        | Exibe `prediction_id` e `status` em `AnalysisBlock`.                          |

## 12. Operacao

A aba Operacao representa o uso corporativo do produto: alertas, fila, qualidade, incidentes e coortes.

Endpoint principal:

```txt
GET /projects/{project_id}/operations
```

Servico/rota:

```txt
backend/app/api/routes/operations.py
```

### Botoes E KPIs

| Elemento            | Funcao para o usuario                                      | Como e feito tecnicamente                                                                      |
| ------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Botao `Atualizar`   | Recarrega dados operacionais.                              | Chama `refreshOperationsWithToast`; internamente usa `GET /projects/{project_id}/operations`.  |
| `Casos abertos`     | Quantidade de casos em aberto, atribuidos ou em andamento. | Calculado no back-end a partir de `intervention_cases.status`.                                 |
| `Criticos`          | Casos abertos com prioridade critica.                      | Filtro `priority == "critical"`.                                                               |
| `Feedback pendente` | Casos que ainda aguardam desfecho.                         | Filtro `outcome_status == "pending"`.                                                          |
| `Alertas ativos`    | Alertas nao resolvidos.                                    | Conta documentos em `alerts` com `status != "resolved"`. Ao clicar, rola para `active-alerts`. |
| `Modelos avaliados` | Quantidade de avaliacoes de modelo.                        | Tamanho de `model_evaluations`.                                                                |
| Botao `Checar alertas` | Executa regras cadastradas e checks padrao do projeto. | Chama `POST /alerts/run-checks?project_id={id}&include_defaults=true`. |

### Alertas Ativos

| Elemento         | Funcao para o usuario                          | Como e feito tecnicamente                        |
| ---------------- | ---------------------------------------------- | ------------------------------------------------ |
| Card de alerta   | Mostra severidade, titulo, mensagem e destino. | Usa documentos de `alerts`.                      |
| Clique no alerta | Leva o usuario ao bloco mais relacionado.      | Chama `alertDestination(alert)` e `goToSection`. |
| Estado vazio     | Informa ausencia de alertas.                   | Exibe `EmptyState` quando `alerts.length === 0`. |

### Fila Operacional

| Elemento         | Funcao para o usuario                 | Como e feito tecnicamente                                                   |
| ---------------- | ------------------------------------- | --------------------------------------------------------------------------- |
| Nome/entidade    | Identifica o caso.                    | Usa `entity_display_name`, `student_display_name`, `entity_id` ou fallback. |
| Prioridade       | Mostra criticidade do acompanhamento. | Usa `case.priority`.                                                        |
| Risco            | Mostra risco em percentual.           | `risk_score * 100`.                                                         |
| Acao recomendada | Orienta o proximo passo.              | Usa `recommended_action`.                                                   |

### Qualidade Da Fonte

| Elemento      | Funcao para o usuario                            | Como e feito tecnicamente          |
| ------------- | ------------------------------------------------ | ---------------------------------- |
| Linhas        | Total de linhas da fonte importada.              | `dataQuality.source.row_count`.    |
| Entidades     | Total de entidades/alunos/objetos.               | `student_count` ou `entity_count`. |
| Colunas       | Total de colunas.                                | `column_count`.                    |
| Paginas PDF   | Quantidade de paginas quando a fonte inclui PDF. | `pdf_pages`.                       |
| Elegibilidade | Contagens por janela ou criterio.                | `dataQuality.eligibility`.         |
| Warnings      | Problemas de qualidade detectados.               | `dataQuality.warnings`.            |

### Registry Champion/Challenger

| Elemento        | Funcao para o usuario               | Como e feito tecnicamente                                         |
| --------------- | ----------------------------------- | ----------------------------------------------------------------- |
| Modelo/janela   | Mostra algoritmo e janela avaliada. | Usa `model_evaluations`.                                          |
| Rank            | Posicao do modelo na avaliacao.     | `item.rank`.                                                      |
| Metrica offline | Resultado de teste offline.         | Prioriza `f2`, `pr_auc`, `average_precision` e `threshold_top10`. |
| Recall online   | Desempenho em simulacao/operacao.   | `production_simulation.performance.recall`.                       |
| Predicoes       | Volume avaliado.                    | `production_simulation.prediction_count`.                         |

### Incidentes E Coortes

| Bloco                     | Funcao para o usuario                               | Como e feito tecnicamente                                    |
| ------------------------- | --------------------------------------------------- | ------------------------------------------------------------ |
| `Incidentes operacionais` | Lista problemas em aberto ou historicos do projeto. | Usa colecao `incidents`.                                     |
| `Coortes monitoradas`     | Lista grupos acompanhados pela operacao.            | Usa colecao `cohorts`; mostra nome, tamanho e casos abertos. |

## 12.1 Casos (SLA Kanban)

A aba Casos (`activeView = "cases"`, atalho `G S`) apresenta a fila operacional como um Kanban com SLA visual. Foi pensada para times que precisam priorizar atendimento rapido aos casos abertos pelo modelo.

### Cabecalho

| Bloco                | Funcao para o usuario                          | Como e feito tecnicamente                                                     |
| -------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------- |
| KPI `Total`          | Numero total de casos no projeto.              | Conta `intervention_cases` carregados via `refreshOperations`.                |
| KPI `Vencidos`       | Casos com SLA estourado.                       | Calcula com base em `due_at` (ou `created_at + sla_hours`).                   |
| KPI `Em risco`       | Casos com menos de 25% do SLA restante.        | Mesma logica, ratio < 0.25.                                                   |
| KPI `Resolvidos`     | Casos com `status` resolvido ou descartado.    | Filtra `status in {resolved, dismissed}`.                                     |

### Colunas

| Coluna           | Statuses incluidos             | Acao primaria          | Acao secundaria  |
| ---------------- | ------------------------------ | ---------------------- | ---------------- |
| `A fazer`        | `open`, `assigned`             | Iniciar (in\_progress) | —                |
| `Em andamento`   | `in_progress`, `paused`        | Resolver               | Pausar           |
| `Resolvido`      | `resolved`, `dismissed`        | Reabrir                | —                |

Ordem dentro de cada coluna: prioridade ascendente (`priority_rank` 1 = critica) e depois `risk_score` decrescente.

### Cartao de caso

Cada cartao contem:

* **Entidade** (clique abre Timeline em `Entidades`);
* `id` da entidade em fonte mono pequena;
* badge de prioridade (`critical` vermelho, `high` ambar, `medium` info, `low` neutro);
* score do modelo;
* nome do responsavel quando ha `assignee`;
* descricao curta (`summary` ou `recommendation`);
* barra de SLA com cor dinamica (verde / ambar / vermelho) e tempo restante humanizado;
* botao primario para mover para a proxima coluna;
* botao discreto `X` para descartar.

### Endpoints usados

* `GET /projects/{project_id}/intervention-cases?status_filter=...` (lista — via `refreshOperations`);
* `POST /intervention-cases/{case_id}/status` (atualiza status, recebe `{status, note}`).

Cada mudanca de status:

* atualiza o registro em `intervention_cases`;
* anexa entrada ao `timeline` do caso;
* gera `audit_event` `intervention_case.status_changed`;
* exibe toast de sucesso ou erro;
* recarrega `operationsData` automaticamente.

## 13. Automacao

A aba Automacao concentra recursos que sustentam o uso diario do produto: jobs, notificacoes, contratos de dados, views salvas e regras de alerta. Ela existe para reduzir a necessidade de acionar endpoints manualmente e para dar visibilidade sobre tarefas executadas em segundo plano.

### Jobs Operacionais

| Elemento | Funcao para o usuario | Como e feito tecnicamente |
| -------- | --------------------- | ------------------------- |
| Botao `Dashboard` | Reprocessa a leitura agregada do projeto. | Cria `POST /jobs` com `type = "dashboard"`. |
| Botao `Drift` | Executa avaliacao de drift para o projeto/modelo. | Cria job `drift` e atualiza a lista de jobs. |
| Botao `DS Lab` | Recalcula diagnosticos de ciencia de dados. | Cria job `diagnostics`. |
| Botao `Metricas` | Atualiza snapshots e indicadores. | Cria job `metrics`. |
| Botao `Checar alertas` | Roda o motor de alertas pelo fluxo de jobs. | Cria job `alerts`. |
| Lista de jobs | Mostra status, tipo, data, resultado e erro. | Usa `GET /jobs?project_id={project_id}`. |

No ambiente atual, os jobs rodam por `BackgroundTasks` do FastAPI. A colecao `jobs` ja separa status, parametros, resultado, erro, usuario criador e timestamps, o que permite migrar para Redis, Celery, RQ ou outro worker sem mudar o contrato da interface.

### Notificacoes

| Elemento | Funcao para o usuario | Como e feito tecnicamente |
| -------- | --------------------- | ------------------------- |
| Contador na topbar | Mostra quantas notificacoes ainda nao foram lidas. | Calculado a partir de `GET /notifications`. |
| Lista de notificacoes | Exibe mensagem, severidade, tipo e data. | Usa documentos da colecao `notifications`. |
| Botao `Marcar lidas` | Limpa o contador de nao lidas. | Chama `POST /notifications/mark-all-read`. |

Alertas e jobs criam notificacoes automaticamente. O front-end tambem oferece feedback imediato com toasts, mas notificacao persistida e diferente de toast: o toast e temporario; a notificacao fica no banco ate ser marcada como lida.

### Data Contracts

| Elemento | Funcao para o usuario | Como e feito tecnicamente |
| -------- | --------------------- | ------------------------- |
| Segmento `accept` | Permite ingestao mesmo com divergencias. | Atualiza `settings.data_contract_mode = "accept"`. |
| Segmento `warn` | Aceita a predicao e destaca problemas. | Atualiza `settings.data_contract_mode = "warn"`. |
| Segmento `block` | Recusa payloads com violacoes bloqueantes. | Atualiza `settings.data_contract_mode = "block"`. |
| Resumo do contrato | Mostra features esperadas, modo e status. | Usa `GET /projects/{project_id}/data-contract`. |

O contrato parte de `selectedModel.expected_features`. Na ingestao, `validate_prediction_contract` verifica feature obrigatoria, nulidade, tipo, faixa numerica e valores permitidos quando essas regras existem no schema do modelo.

### Views Salvas E Regras De Alerta

| Elemento | Funcao para o usuario | Como e feito tecnicamente |
| -------- | --------------------- | ------------------------- |
| Botao `Salvar view` em Predicoes | Persiste filtros e colunas da tela atual. | Chama `POST /saved-views`. |
| Lista de views | Permite aplicar uma configuracao salva. | Usa `GET /saved-views` e `applySavedView`. |
| Regras de alerta | Mostra regras cadastradas do projeto. | Usa `GET /alert-rules?project_id={project_id}`. |

Views salvas sao pessoais no estado atual. Elas tornam mais rapido voltar a conjuntos recorrentes, como predicoes sem feedback, alto risco, determinada versao do modelo ou janela de investigacao.

## 14. Governanca

A aba Governanca concentra seguranca, auditoria e documentacao estrutural do banco.

### Postura De Seguranca

Endpoint:

```txt
GET /security/posture
```

| Elemento                   | Funcao para o usuario                             | Como e feito tecnicamente                             |
| -------------------------- | ------------------------------------------------- | ----------------------------------------------------- |
| Check de criptografia      | Mostra se a criptografia de PII esta configurada. | Verifica `FIELD_ENCRYPTION_KEY` ou chave derivada.    |
| Check de indice cego       | Mostra se buscas seguras usam chave dedicada.     | Verifica `PII_HASH_KEY`.                              |
| Check de senha             | Mostra estrategia de hash.                        | PBKDF2-SHA256 versionado com iteracoes configuraveis. |
| Check de API key           | Mostra se chaves usam HMAC.                       | Conta `api_keys.key_hash` com prefixo `hmac_sha256:`. |
| Check de SECRET\_KEY       | Mostra se a chave principal ainda e padrao.       | Usa configuracao do back-end.                         |
| Check de headers           | Mostra se headers de seguranca estao ativos.      | Verifica `ENABLE_SECURITY_HEADERS`.                   |
| Check de usuarios migrados | Mostra e-mails criptografados/hasheados.          | Conta usuarios com `email_encrypted`.                 |
| Recomendacoes              | Lista acoes para producao.                        | Retornadas pela rota de postura.                      |

### Botao Aplicar Controles

| Item               | Descricao                                                        |
| ------------------ | ---------------------------------------------------------------- |
| Funcao             | Executa migracao de protecao para dados sensiveis ja existentes. |
| Endpoint           | `POST /security/migrate-sensitive-data`.                         |
| Permissao          | Apenas `OWNER` ou `ADMIN`.                                       |
| Usuarios           | Criptografa e-mail e cria indice cego.                           |
| Projetos           | Mascara e-mail de alerta e cria hash.                            |
| Predicoes          | Protege `entity.id` e `entity.display_name`.                     |
| Auditoria          | Redige dados sensiveis em actor, diff e context.                 |
| Casos operacionais | Redige dados sensiveis em timeline.                              |
| API keys legadas   | Conta chaves que precisam de rotacao.                            |

### API Keys

| Elemento | Funcao para o usuario | Como e feito tecnicamente |
| --- | --- | --- |
| Lista de chaves | Mostra chaves do projeto atual. | Chama `GET /projects/{project_id}/api-keys`. |
| Escopos | Mostra permissoes da chave. | Usa `api_keys.scopes`; a interface cria chave com `predictions:write`, `predictions:batch` e `feedback:write`. |
| Expiracao | Mostra validade da chave. | Usa `api_keys.expires_at`; chaves expiradas passam para `expired` no primeiro uso. |
| Ultimo uso | Mostra atividade recente da chave. | `get_optional_user_or_api_key` atualiza `last_used_at`. |
| Botao `Nova chave` | Cria uma API key para o projeto atual. | Reusa `POST /projects/{project_id}/api-keys` com escopos e expiracao. |
| Botao `Revogar` | Revoga a chave selecionada. | Chama `DELETE /api-keys/{api_key_id}` e atualiza seguranca/auditoria. |
| Status `revoked` | Indica chave desativada. | O back-end preserva o registro e altera `status`. |

### Audit Trail

| Elemento               | Funcao para o usuario                              | Como e feito tecnicamente                                      |
| ---------------------- | -------------------------------------------------- | -------------------------------------------------------------- |
| Lista de eventos       | Mostra eventos recentes do projeto.                | Usa `GET /projects/{project_id}/audit-events`.                 |
| Campo de filtro        | Busca eventos por tipo, ator, recurso ou data.     | Filtra `auditEvents` em memoria com `auditQuery`.              |
| Botao `Exportar evidencias` | Gera pacote auditavel do filtro atual.        | Cria JSON local com eventos filtrados, projeto, data e consulta. |
| Ator                   | Mostra e-mail mascarado, ID ou prefixo de API key. | Usa `event.actor`.                                             |
| Data                   | Momento do evento.                                 | Usa `event.created_at`.                                        |
| Indicador de historico | Informa eventos alem dos 28 exibidos.              | A UI limita exibicao e aponta para historico completo via API. |

### Modelo Documental

| Colecao              | Papel na arquitetura                               |
| -------------------- | -------------------------------------------------- |
| `predictions`        | Documento central da decisao de ML.                |
| `metrics_snapshots`  | Metricas materializadas por periodo/modelo/versao. |
| `diagnostic_cache`   | Cache dos diagnosticos do DS Lab.                  |
| `audit_events`       | Trilha append-only de eventos.                     |
| `prediction_replays` | Historico de replays de decisao.                   |
| `alerts`             | Alertas ativos ou historicos.                      |
| `exports`            | Metadados de exportacoes geradas.                  |

## 15. Docs

A aba `Docs` e a documentacao de uso dentro do produto. Ela foi estruturada como um manual navegavel, com texto em formato de artigo, paragrafos explicativos e exemplos de codigo apenas quando existe uma integracao tecnica envolvida. O objetivo e que um usuario consiga aprender a usar a plataforma pela propria interface, sem precisar abrir o repositorio ou ler diretamente os arquivos Markdown.

O topo da aba apresenta o escopo da documentacao e botoes rapidos para tarefas frequentes. `Registrar predicao` abre a documentacao do Workbench, `Entender What-if` abre uma secao dedicada ao simulador de cenarios e `Seguranca` abre a documentacao de governanca. Esses botoes apenas atualizam `selectedDocId`; eles nao executam nenhuma acao operacional.

A navegacao lateral e gerada a partir do array `docSections` em `frontend/app/page.tsx`. Cada item possui identificador, label, titulo, introducao, topicos narrativos, exemplos opcionais e referencias relacionadas. O conteudo principal renderiza `selectedDocSection`, exibindo primeiro o contexto da secao, depois os topicos em sequencia e por fim uma linha de continuidade com assuntos relacionados.

Os topicos atuais cobrem Comece aqui, Conceitos, Acesso e sessao, Navegacao, Overview, Monitor, DS Lab, Predicoes, Decision inspector, Feedback, What-if, Replay e exportacoes, Operacao, Alertas, Workbench, Governanca, API, Resultados e Limites atuais. As secoes Feedback, What-if e Replay foram separadas porque sao fluxos importantes dentro do inspector e precisam de explicacao propria: quando usar, como a UI monta o payload, qual endpoint e chamado, quais efeitos aparecem no produto e quais limites metodologicos existem.

Na secao What-if, a documentacao explica que a simulacao parte da predicao selecionada, carrega ate dez features, converte valores numericos, booleanos e textuais, permite presets `Otimista`, `Conservador` e `Reset`, e envia `hypothetical_features` para `POST /predictions/{prediction_id}/whatif`. A documentacao tambem deixa claro que o resultado atual e estimativo quando nao ha endpoint real de scoring conectado.

## 16. Bloco De Resultados Das Acoes

O componente `AnalysisBlock` renderiza o retorno da ultima acao executada.

| Tipo                 | Quando aparece                        | Campos exibidos                                             |
| -------------------- | ------------------------------------- | ----------------------------------------------------------- |
| `drift`              | Apos `Rodar drift` ou `Drift`.        | Status, PSI, score medio atual e features avaliadas.        |
| `version-compare`    | Apos `Comparar versoes`.              | Versao A, Versao B, delta de score medio e delta acionavel. |
| `bias`               | Apos `Equidade`.                      | Feature, grupos, casos analisados e mini-tabela por grupo.  |
| `export`             | Apos `Exportar CSV` ou `Exportar`.    | ID do arquivo, formato, registros e status.                 |
| `what-if`            | Apos `What-if`.                       | Score original, score estimado, delta e se muda decisao.    |
| `replay`             | Apos `Replay`.                        | Versao alvo, score replay, label replay e se muda decisao.  |
| `api-response`       | Apos registrar predicao no Workbench. | ID da predicao e status.                                    |
| `api-key`            | Apos gerar API key.                   | Chave completa uma unica vez, prefixo e escopo.             |
| `security-migration` | Apos aplicar controles.               | Usuarios, predicoes, auditoria e API keys legadas.          |

## 17. Mapa Rapido De Botoes E Endpoints

| Tela       | Botao/acao           | Endpoint ou execucao                                                                               |
| ---------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| Login      | `Entrar`             | `POST /auth/login`                                                                                 |
| Login      | `Registrar`          | `POST /auth/register`                                                                              |
| Global     | `Atualizar`          | `refreshAll`: projetos, modelos, dashboard, operacao, seguranca, auditoria, versoes e diagnosticos |
| Global     | `Comandos`           | Abre command palette para telas, acoes e documentacao                                              |
| Global     | `Notificacoes`       | Abre Automacao e atualiza `GET /notifications`                                                     |
| Global     | `Sair`               | `POST /auth/logout` + limpeza de sessao local                                                      |
| Overview   | KPI `Predicoes`      | Abre aba Predicoes                                                                                 |
| Overview   | KPI `Acionaveis`     | Abre Predicoes com filtro de label positivo                                                        |
| Overview   | KPI `Feedback`       | Abre Predicoes com filtro de feedback                                                              |
| Overview   | KPI `Alertas`        | Abre Operacao em `active-alerts`                                                                   |
| Monitor    | `Atualizar monitor`  | `refreshAll`                                                                                       |
| Monitor    | `Gerar API key`      | `POST /projects/{project_id}/api-keys`                                                             |
| Monitor    | `Comparar versoes`   | `GET /models/{model_id}/versions/compare`                                                          |
| Monitor    | `Rodar drift`        | `POST /models/{model_id}/drift/run`                                                                |
| Monitor    | `Equidade`           | `GET /models/{model_id}/bias-analysis`                                                             |
| Monitor    | `Exportar CSV`       | `POST /exports`                                                                                    |
| DS Lab     | `Atualizar DS Lab`   | `GET /models/{model_id}/diagnostics`                                                               |
| DS Lab     | `Drift`              | `POST /models/{model_id}/drift/run`                                                                |
| DS Lab     | `Equidade`           | `GET /models/{model_id}/bias-analysis`                                                             |
| DS Lab     | `Exportar pacote`    | Download local de JSON no browser                                                                  |
| Predicoes  | `Registrar predicao` | `POST /predictions`                                                                                |
| Predicoes  | `Salvar view`        | `POST /saved-views`                                                                                |
| Predicoes  | `Anterior`           | Atualiza pagina local e recarrega `GET /predictions` com `skip`                                    |
| Predicoes  | `Proxima`            | Atualiza pagina local e recarrega `GET /predictions` com `skip`                                    |
| Inspector  | `Feedback`           | `POST /predictions/{prediction_id}/feedback`                                                       |
| Inspector  | `What-if`            | `POST /predictions/{prediction_id}/whatif`                                                         |
| Inspector  | `Replay`             | `POST /predictions/{prediction_id}/replay`                                                         |
| Inspector  | `Exportar`           | `POST /exports`                                                                                    |
| Entidades  | `Pesquisar`          | `GET /projects/{project_id}/entity-timeline?q={valor}`                                             |
| Entidades  | `Usar entidade selecionada` | Copia ID da predicao selecionada para o campo de busca                                      |
| Entidades  | `Salvar nota`        | `POST /projects/{project_id}/entity-notes`                                                         |
| Operacao   | `Atualizar`          | `GET /projects/{project_id}/operations`                                                            |
| Operacao   | `Checar alertas`     | `POST /alerts/run-checks?project_id={id}&include_defaults=true`                                     |
| Operacao   | Alerta ativo         | Scroll para bloco operacional relacionado                                                          |
| Operacao   | `Assumir` / `Resolver` | `POST /intervention-cases/{case_id}/status`                                                      |
| Automacao  | Jobs de painel       | `POST /jobs` com tipos `dashboard`, `drift`, `diagnostics`, `metrics` ou `alerts`                  |
| Automacao  | `Marcar lidas`       | `POST /notifications/mark-all-read`                                                                |
| Automacao  | Modo do contrato     | `PATCH /projects/{project_id}/data-contract`                                                       |
| Automacao  | Aplicar view         | Atualiza filtros locais e recarrega `GET /predictions`                                             |
| Workbench  | `Registrar predicao` | `POST /predictions`                                                                                |
| Governanca | `Nova chave`         | `POST /projects/{project_id}/api-keys`                                                             |
| Governanca | `Revogar`            | `DELETE /api-keys/{api_key_id}`                                                                    |
| Governanca | `Exportar evidencias` | Download local de JSON com eventos de auditoria filtrados                                         |
| Governanca | `Aplicar controles`  | `POST /security/migrate-sensitive-data`                                                            |
| Docs       | Topico de navegacao  | Atualiza `selectedDocId`                                                                           |

## 18. Observacoes Tecnicas E Limites

* O What-if atual e estimativo. Ele usa explicacoes e heuristicas, nao executa o artefato real do modelo.

* Replay registra uma simulacao historica. A UI atual usa uma variacao simples de score; o back-end tambem suporta `hypothetical_features`.

* Exportacoes sao gravadas em disco local quando o store JSON esta ativo.

* DS Lab usa predicoes online e feedback disponivel; quando ha pouco feedback, threshold e calibracao devem ser tratados como indicativos.

* Drift divide o historico do modelo em metade de referencia e metade atual. Para producao, uma janela temporal configuravel seria uma evolucao natural.

* Jobs rodam localmente com `BackgroundTasks`. A modelagem separada em `jobs` permite evoluir para fila distribuida sem trocar a interface.

* Data contracts usam o schema de `expected_features`. Quanto mais completo for esse schema, mais precisa sera a validacao de tipos, nulidade, ranges e valores permitidos.

* Timeline de entidade depende de identificadores consistentes. Quando dados antigos nao possuem indice cego, a API usa fallback em campos exibiveis autorizados.

* A tabela de predicoes usa pagina de 250 itens para manter a interface responsiva.

* Filtros de busca textual em `q` sao adequados para demo/store JSON. Em MongoDB, o ideal e criar indices textuais ou estrategia de busca dedicada.

* API keys sao exibidas completas apenas no momento da criacao. Depois disso, a plataforma mostra somente metadados e prefixo.

* A documentacao da modelagem completa fica em [`modelagem-banco-json.md`](modelagem-banco-json.md).

* A documentacao de arquitetura e seguranca fica em [`documentacao-software.md`](documentacao-software.md).
