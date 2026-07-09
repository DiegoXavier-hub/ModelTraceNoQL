export type Locale = "pt-BR" | "en";

export const DEFAULT_LOCALE: Locale = "pt-BR";
export const LOCALE_STORAGE_KEY = "modeltrace_locale";

type Dictionary = Record<string, string>;

const ptExact: Dictionary = {
  "Append-only": "Registro imutável",
  "Decision Ops": "Operação de decisões",
  "Docs": "Documentação",
  "Overview": "Visão geral",
  "Predicoes": "Predições",
  "Operacao": "Operação",
  "Automacao": "Automação",
  "Governanca": "Governança",
  "Documentacao": "Documentação",
  "Seguranca": "Segurança",
  "Configuracoes": "Configurações",
  "Notificacoes": "Notificações",
  "Acoes": "Ações",
  "Versoes": "Versões",
  "Metricas": "Métricas",
  "Diagnosticos": "Diagnósticos",
  "Saude": "Saúde",
  "Avaliacao": "Avaliação",
  "Comparacao": "Comparação",
  "Predicao": "Predição",
  "Exportacao": "Exportação",
  "Integracao": "Integração",
  "Evidencia": "Evidência",
  "Evidencias": "Evidências",
  "Descricao": "Descrição",
  "Calibracao": "Calibração",
  "Acionaveis": "Acionáveis",
  "Producao": "Produção",
  "Sessao": "Sessão",
  "Autenticacao": "Autenticação",
  "Navegacao": "Navegação",
  "Informacao": "Informação",
  "Conclusao": "Conclusão",
  "Revisao": "Revisão",
  "Usuario": "Usuário",
  "Usuarios": "Usuários",
  "Formulario": "Formulário",
  "Schema flexivel": "Esquema flexível",
  "Schema flexível": "Esquema flexível",
  "health": "saúde"
};

const enExact: Dictionary = {
  "Acesso ao workspace": "Workspace access",
  "Acesso e sessão": "Access and session",
  "Acesso, sessão e notificações": "Access, session, and notifications",
  "Abrir Docs": "Open Docs",
  "Abrir DS Lab": "Open DS Lab",
  "Abrir Automação": "Open Automation",
  "Abrir Automacao": "Open Automation",
  "Abrir Entidades": "Open Entities",
  "Abrir Governança": "Open Governance",
  "Abrir Monitor": "Open Monitor",
  "Abrir Operação": "Open Operations",
  "Abrir Predições": "Open Predictions",
  "Abrir Perfil": "Open Profile",
  "Abrir Workbench": "Open Workbench",
  "Abrir Overview": "Open Overview",
  "Abaixo da meta operacional.": "Below the operational target.",
  "Acionáveis": "Actionable",
  "Alerta:": "Alert:",
  "Alertas": "Alerts",
  "Alertas ativos": "Active alerts",
  "Alertas e regras operacionais": "Alerts and operational rules",
  "Automação": "Automation",
  "Automacao": "Automation",
  "Automação operacional": "Operational automation",
  "Automacao operacional": "Operational automation",
  "Análise avançada": "Advanced analysis",
  "Análise da decisão": "Decision analysis",
  "Analisar segmentos por": "Analyze segments by",
  "Anterior": "Previous",
  "API e integrações": "API and integrations",
  "API key ativa": "Active API key",
  "API key criada": "API key created",
  "API key criada.": "API key created.",
  "API key revogada.": "API key revoked.",
  "API keys": "API keys",
  "API online": "API online",
  "Aplicar controles": "Apply controls",
  "Atualizar": "Refresh",
  "Atualizar DS Lab": "Refresh DS Lab",
  "Atualizar monitor": "Refresh monitor",
  "Atualizar perfil": "Refresh profile",
  "Atualizando centro de operação...": "Refreshing operations center...",
  "Atualizando DS Lab...": "Refreshing DS Lab...",
  "Atualizando monitor...": "Refreshing monitor...",
  "Atualizando workspace...": "Refreshing workspace...",
  "Auditoria": "Audit",
  "Auditoria, replays, what-if e exportacoes seguras.": "Audit, replays, what-if, and secure exports.",
  ["Auditoria, replays, what-if e exporta\u00e7\u00f5es seguras."]: "Audit, replays, what-if, and secure exports.",
  "Audit trail": "Audit trail",
  "Baixo risco": "Low risk",
  "Bio": "Bio",
  "Bio profissional": "Professional bio",
  "Buscar ação, tela ou documento": "Search action, screen, or document",
  "Buscar ID, entidade ou label": "Search ID, entity, or label",
  "Calibração": "Calibration",
  "Cancelar": "Cancel",
  "Capacidade operacional": "Operational capacity",
  "Cargo": "Job title",
  "Casos abertos": "Open cases",
  "Cenário atualizado.": "Scenario updated.",
  "Cenário what-if": "What-if scenario",
  "Centro operacional": "Operations center",
  "Checar alertas": "Check alerts",
  "Confira os requisitos de senha para criar a conta.": "Check the password requirements to create the account.",
  "Classificação binária": "Binary classification",
  "Cobertura de feedback": "Feedback coverage",
  "Comece aqui": "Start here",
  "Comandos": "Commands",
  "Comparação pronta": "Comparison ready",
  "Comparar versões": "Compare versions",
  "Conceitos": "Concepts",
  "Conceitos principais": "Core concepts",
  "Conservador": "Conservative",
  "Continue lendo": "Continue reading",
  "Conta criada.": "Account created.",
  "Conta criada. Verifique seu email para confirmar o acesso.": "Account created. Check your email to confirm access.",
  "Criar conta": "Create account",
  "Criar conta no ModelTrace": "Create your ModelTrace account",
  "Já tenho conta": "I already have an account",
  "Dados profissionais (opcional)": "Professional details (optional)",
  "Modo de acesso": "Access mode",
  "Formulário de login": "Sign-in form",
  "Formulário de cadastro": "Sign-up form",
  "Conta, foto, segurança e preferências.": "Account, photo, security, and preferences.",
  "Contratos por modelo e versão.": "Contracts by model and version.",
  "Criando chave de API...": "Creating API key...",
  "Criar uma chave com escopos": "Create a scoped key",
  "Criticos": "Critical",
  "Críticos": "Critical",
  "Dados pessoais e profissionais": "Personal and professional information",
  "Dados profissionais para cadastro": "Professional registration details",
  "Dados técnicos": "Technical data",
  "Data": "Date",
  "Data contracts": "Data contracts",
  "Decisão": "Decision",
  "Decision inspector": "Decision inspector",
  "Demanda acima da faixa planejada.": "Demand above the planned range.",
  "Detalhes técnicos da predição": "Prediction technical details",
  "Diagnóstico por segmento": "Segment diagnostics",
  "Diagnósticos": "Diagnostics",
  "Distribuição de score": "Score distribution",
  "Distribuicao de score": "Score distribution",
  "Docs /": "Docs /",
  "Documentação": "Docs",
  "Documentação do usuário": "User documentation",
  "DS Lab atualizado.": "DS Lab refreshed.",
  "Email": "Email",
  "Email confirmado": "Email confirmed",
  "Email confirmado.": "Email confirmed.",
  "Email de confirmação enviado.": "Confirmation email sent.",
  "Email da conta": "Account email",
  "Email já confirmado.": "Email already confirmed.",
  "Email pendente": "Email pending",
  "Enviar email": "Send email",
  "Enviar reset de senha": "Send password reset",
  "Enviando...": "Uploading...",
  "Entrar": "Sign in",
  "Entrar no ModelTrace": "Sign in to ModelTrace",
  "Entender What-if": "Understand What-if",
  "Esqueci minha senha": "Forgot my password",
  "Entidade": "Entity",
  "Entidades": "Entities",
  "Entidades e timeline": "Entities and timeline",
  "Empresa": "Company",
  "Erro ao carregar predições.": "Failed to load predictions.",
  "Erro ao checar alertas.": "Failed to check alerts.",
  "Erro ao criar API key.": "Failed to create API key.",
  "Erro ao enviar predição.": "Failed to submit prediction.",
  "Erro ao registrar feedback.": "Failed to save feedback.",
  "Erro ao revogar chave.": "Failed to revoke key.",
  "Erro no drift.": "Drift failed.",
  "Erro no DS Lab.": "DS Lab failed.",
  "Foto atualizada.": "Photo updated.",
  "Erro no replay.": "Replay failed.",
  "Erro no what-if.": "What-if failed.",
  "Erro na análise de equidade.": "Fairness analysis failed.",
  "Erro na comparação.": "Comparison failed.",
  "Erro na exportação.": "Export failed.",
  "Erro na migração de segurança.": "Security migration failed.",
  "Falha no cadastro.": "Registration failed.",
  "Falha no login.": "Login failed.",
  "Fuso horário": "Time zone",
  "Escolha projeto e modelo para registrar a predição.": "Select a project and model to register the prediction.",
  "Escolha um modelo para calcular drift.": "Select a model to calculate drift.",
  "Escolha um modelo e uma feature para equidade.": "Select a model and a feature for fairness.",
  "Escolha um projeto para checar alertas.": "Select a project to check alerts.",
  "Escolha um projeto para exportar.": "Select a project to export.",
  "Escolha um projeto para gerar a chave.": "Select a project to create the key.",
  "Escolha um projeto para iniciar o monitoramento.": "Choose a project to start monitoring.",
  "Escopos": "Scopes",
  "Estado": "Status",
  "Exemplo": "Example",
  "Exportação criada": "Export created",
  "Exportar": "Export",
  "Exportar auditoria": "Export audit",
  "Exportar CSV": "Export CSV",
  "Exportar evidências": "Export evidence",
  "Exportar pacote": "Export package",
  "Feature de equidade": "Fairness feature",
  "Feature intelligence": "Feature intelligence",
  "Feedback": "Feedback",
  "Feedback e desfecho real": "Feedback and observed outcome",
  "Feedback pendente": "Pending feedback",
  "Feedback positivo por API": "Positive feedback via API",
  "Feedback salvo": "Feedback saved",
  "Fechar": "Close",
  "Fechar notificação": "Close notification",
  "Fila operacional": "Operations queue",
  "Filtro: acionáveis.": "Filter: actionable.",
  "Filtro: com feedback.": "Filter: with feedback.",
  "Formato atual": "Current format",
  "Gerar API key": "Generate API key",
  "Jobs": "Jobs",
  "Jobs, notificações e contratos.": "Jobs, notifications, and contracts.",
  "Jobs, notificacoes e contratos.": "Jobs, notifications, and contracts.",
  "Jobs, notificações, contratos de dados, views salvas e regras de alerta em um painel operacional.": "Jobs, notifications, data contracts, saved views, and alert rules in one operations panel.",
  "Jobs, notificacoes, contratos de dados, views salvas e regras de alerta em um painel operacional.": "Jobs, notifications, data contracts, saved views, and alert rules in one operations panel.",
  "Governança": "Governance",
  "Governança ativa": "Governance active",
  "Governança e segurança": "Governance and security",
  "Guia de uso do ModelTrace para operação, ciência de dados, governança e integrações.": "ModelTrace user guide for operations, data science, governance, and integrations.",
  "Health": "Health",
  "Historico imutavel de decisoes.": "Immutable decision history.",
  ["Hist\u00f3rico imut\u00e1vel de decis\u00f5es."]: "Immutable decision history.",
  "Histórico de predições": "Prediction history",
  "ID da entidade": "Entity ID",
  "Inconclusivo": "Inconclusive",
  "Incidentes operacionais": "Operational incidents",
  "Indicadores sem desvio relevante.": "Indicators without relevant deviation.",
  "Integração": "Integration",
  "Label": "Label",
  "Linhas": "Rows",
  "Login pela API": "API login",
  "Letra maiuscula": "Uppercase letter",
  "Letra minuscula": "Lowercase letter",
  "Matriz de confusão": "Confusion matrix",
  "Matriz de confusao": "Confusion matrix",
  "Métrica": "Metric",
  "Métrica primária": "Primary metric",
  "Métricas": "Metrics",
  "Modelo": "Model",
  "Modelo documental": "Document model",
  "Modelos ativos": "Active models",
  "Modelos avaliados": "Evaluated models",
  "Monitore predicoes, feedback, drift e auditoria em um workspace unico.": "Monitor predictions, feedback, drift, and audit in one workspace.",
  ["Monitore predi\u00e7\u00f5es, feedback, drift e auditoria em um workspace \u00fanico."]: "Monitor predictions, feedback, drift, and audit in one workspace.",
  "Monitor atualizado.": "Monitor refreshed.",
  "Navegação": "Navigation",
  "Navegação, contexto e comandos": "Navigation, context, and commands",
  "Nenhum comando encontrado.": "No command found.",
  "Nenhum envio nesta sessão.": "No submission in this session.",
  "Notificações": "Notifications",
  "Notificacoes": "Notifications",
  "Notificações marcadas como lidas.": "Notifications marked as read.",
  "Notificacoes marcadas como lidas.": "Notifications marked as read.",
  "Nome": "Name",
  "Nome completo": "Full name",
  "Nome público": "Public name",
  "Nova senha": "New password",
  "Nova senha pronta.": "New password ready.",
  "Nova chave": "New key",
  "Nova predição": "New prediction",
  "O que é o ModelTrace": "What ModelTrace is",
  "O que faz e o que não faz": "What it does and does not do",
  "Operação": "Operations",
  "Operação de decisões": "Decision Ops",
  "Operação em faixa": "Operations in range",
  "Operação e governança para modelos em produção.": "Operations and governance for production models.",
  "Operação com coortes, qualidade, incidentes e auditoria.": "Operations with cohorts, quality, incidents, and audit.",
  "Auditoria, indices e exportacoes operacionais.": "Audit, indexes, and operational exports.",
  ["Auditoria, \u00edndices e exporta\u00e7\u00f5es operacionais."]: "Audit, indexes, and operational exports.",
  "Origem": "Source",
  "Organização": "Organization",
  "Otimista": "Optimistic",
  "Página": "Page",
  "Paginas PDF": "PDF pages",
  "Páginas PDF": "PDF pages",
  "Painel lateral para investigar a decisão selecionada: score, feedback, what-if, replay, explicabilidade e detalhes técnicos.": "Side panel for investigating the selected decision: score, feedback, what-if, replay, explainability, and technical details.",
  "Pacote exportado.": "Package exported.",
  "Pendente": "Pending",
  "Pendentes": "Pending",
  "Perfil": "Profile",
  "Perfil atualizado.": "Profile updated.",
  "Perfil profissional": "Professional profile",
  "Preferências": "Preferences",
  "Preferências salvas no perfil acompanham o usuário e podem ser usadas por fluxos de notificação, auditoria e operação.": "Profile preferences follow the user and can be used by notification, audit, and operations flows.",
  "Postura de segurança": "Security posture",
  "Predição registrada": "Prediction registered",
  "Predição salva": "Prediction saved",
  "Predições": "Predictions",
  "Predições abertas.": "Predictions opened.",
  "Pelo menos 12 caracteres": "At least 12 characters",
  "Pelo menos um caractere especial": "At least one special character",
  "Pelo menos um numero": "At least one number",
  "Para novas contas, use uma senha forte:": "For new accounts, use a strong password:",
  "Preparando CSV...": "Preparing CSV...",
  "Primeiro uso": "First use",
  "Prioridades": "Priorities",
  "Prioridades de análise": "Analysis priorities",
  "Produção": "Production",
  "Projeto": "Project",
  "Próxima": "Next",
  "Visão geral": "Overview",
  "Qualidade da fonte": "Source quality",
  "Recall": "Recall",
  "Receber alertas por email": "Receive alerts by email",
  "Registrar": "Register",
  "Registrar feedback": "Register feedback",
  "Registrar feedback por API": "Register feedback through API",
  "Registrar predição": "Register prediction",
  "Redefinir senha": "Reset password",
  "Reenviar confirmação": "Resend confirmation",
  "Replay e exportações": "Replay and exports",
  "Replay salvo.": "Replay saved.",
  "Registro imutável": "Append-only",
  "Reset": "Reset",
  "Resultados": "Results",
  "Resultados das ações e detalhes técnicos": "Action results and technical details",
  "Revogar": "Revoke",
  "Rodar drift": "Run drift",
  "Salvar feedback": "Save feedback",
  "Salvar nova senha": "Save new password",
  "Salvar perfil": "Save profile",
  "Score médio": "Average score",
  "Segurança": "Security",
  "Schema flexivel": "Flexible schema",
  ["Schema flex\u00edvel"]: "Flexible schema",
  "Esquema flexível": "Flexible schema",
  "Saúde": "Health",
  "Saúde operacional do modelo": "Operational model health",
  "Segurança da conta": "Account security",
  "Selecione uma predição.": "Select a prediction.",
  "Selecionar": "Select",
  "Telefone": "Phone",
  "Token": "Token",
  "Alterar foto": "Change photo",
  "Área": "Area",
  "Modo compacto para tabelas operacionais": "Compact mode for operational tables",
  "Sem alertas ativos.": "No active alerts.",
  "Sem casos nesta classe.": "No cases in this class.",
  "Sem chaves para este projeto.": "No keys for this project.",
  "Sem coortes monitoradas.": "No monitored cohorts.",
  "Sem dados de explicabilidade.": "No explainability data.",
  "Sem eventos para este filtro.": "No events for this filter.",
  "Sem incidentes ativos.": "No active incidents.",
  "Sem produção": "No production",
  "Sem versões.": "No versions.",
  "Senha": "Password",
  "Senha atualizada. Entre com a nova senha.": "Password updated. Sign in with the new password.",
  "Senha fora da politica de seguranca.": "Password does not meet the security policy.",
  "Email ou senha incorretos.": "Email or password incorrect.",
  "Formato de email invalido.": "Invalid email format.",
  "Conta bloqueada ou inativa.": "Account is blocked or inactive.",
  "Muitas tentativas. Aguarde alguns minutos.": "Too many attempts. Wait a few minutes.",
  "Erro interno. Tente novamente em instantes.": "Internal error. Try again shortly.",
  "Erro interno.": "Internal error.",
  "Este email ja esta cadastrado.": "This email is already registered.",
  "Verifique os dados do formulario.": "Check the form data.",
  "Email nao encontrado.": "Email not found.",
  "Token invalido ou expirado. Solicite um novo email.": "Token invalid or expired. Request a new email.",
  "A nova senha nao atende aos requisitos.": "The new password does not meet the requirements.",
  "Nao foi possivel contactar o servidor. Verifique sua conexao.": "Could not reach the server. Check your connection.",
  "Senha pronta para cadastro.": "Password is ready for registration.",
  "Nao usar nome, email ou organizacao": "Do not use name, email, or organization",
  "Nao usar senhas comuns": "Do not use common passwords",
  "Sessão encerrada.": "Session ended.",
  "Sessão expirada. Entre novamente.": "Session expired. Sign in again.",
  "Sessão iniciada.": "Session started.",
  "Simular alteração de feature": "Simulate feature change",
  "Simular cenário": "Simulate scenario",
  "Sinal executivo de operação, feedback, alertas e desempenho.": "Executive signal for operations, feedback, alerts, and performance.",
  "Sair": "Sign out",
  "Todos": "All",
  "Todos os labels": "All labels",
  "Todas janelas": "All windows",
  "Último uso": "Last used",
  "Valor": "Value",
  "Versão": "Version",
  "Versão/janela": "Version/window",
  "Versões": "Versions",
  "Views": "Views",
  "Views salvas": "Saved views",
  "Versões do modelo": "Model versions",
  "Volume temporal": "Volume over time",
  "Workspace atualizado.": "Workspace refreshed.",
  "Workspace online.": "Workspace online.",
  "Workspace sem projeto": "Workspace without project"
};

const dynamicExact: Record<string, { "pt-BR": string; en: string }> = {
  "Industrial Predictive Maintenance": {
    "pt-BR": "Manutenção preditiva industrial",
    en: "Industrial Predictive Maintenance"
  },
  "Modelos industriais para antecipar eventos DontGo em equipamentos de mina.": {
    "pt-BR": "Modelos industriais para antecipar eventos DontGo em equipamentos de mina.",
    en: "Industrial models for anticipating DontGo events in mine equipment."
  },
  "CNPJ Closure Risk Radar": {
    "pt-BR": "Radar de risco de encerramento de CNPJ",
    en: "CNPJ Closure Risk Radar"
  },
  "TCC Student Outcomes Full Replay": {
    "pt-BR": "Replay completo de desfechos estudantis do TCC",
    en: "TCC Student Outcomes Full Replay"
  },
  "Replay completo dos modelos do TCC com treino, validacao e teste para demonstrar rastreabilidade de decisoes.": {
    "pt-BR": "Replay completo dos modelos do TCC com treino, validação e teste para demonstrar rastreabilidade de decisões.",
    en: "Full replay of the TCC models with training, validation, and test data to demonstrate decision traceability."
  },
  "Modelo de risco de baixa de empresas brasileiras em horizonte de 12 meses.": {
    "pt-BR": "Modelo de risco de baixa de empresas brasileiras em horizonte de 12 meses.",
    en: "Risk model for Brazilian company closure within a 12-month horizon."
  },
  "DontGo Event Risk": {
    "pt-BR": "Risco de evento DontGo",
    en: "DontGo Event Risk"
  },
  "Modelo LR treinado no TCC para risco de evasao em janelas P1/P2/P4.": {
    "pt-BR": "Modelo LR treinado no TCC para risco de evasão em janelas P1/P2/P4.",
    en: "LR model trained in the TCC for dropout risk across P1/P2/P4 windows."
  },
  "Modelo RF treinado no TCC para risco de evasao em janelas P1/P2/P4.": {
    "pt-BR": "Modelo RF treinado no TCC para risco de evasão em janelas P1/P2/P4.",
    en: "RF model trained in the TCC for dropout risk across P1/P2/P4 windows."
  },
  "Modelo XGBoost treinado no TCC para risco de evasao em janelas P1/P2/P4.": {
    "pt-BR": "Modelo XGBoost treinado no TCC para risco de evasão em janelas P1/P2/P4.",
    en: "XGBoost model trained in the TCC for dropout risk across P1/P2/P4 windows."
  },
  "Modelo CatBoost treinado no TCC para risco de evasao em janelas P1/P2/P4.": {
    "pt-BR": "Modelo CatBoost treinado no TCC para risco de evasão em janelas P1/P2/P4.",
    en: "CatBoost model trained in the TCC for dropout risk across P1/P2/P4 windows."
  },
  "Modelo MLP treinado no TCC para risco de evasao em janelas P1/P2/P4.": {
    "pt-BR": "Modelo MLP treinado no TCC para risco de evasão em janelas P1/P2/P4.",
    en: "MLP model trained in the TCC for dropout risk across P1/P2/P4 windows."
  },
  "Entidade em acompanhamento": {
    "pt-BR": "Entidade em acompanhamento",
    en: "Entity under monitoring"
  },
  "Ingestao operacional": {
    "pt-BR": "Ingestão operacional",
    en: "Operational ingestion"
  }
};

const ptWordReplacements: Array<[RegExp, string]> = [
  [/\bPredicoes\b/g, "Predições"],
  [/\bpredicoes\b/g, "predições"],
  [/\bPredicao\b/g, "Predição"],
  [/\bpredicao\b/g, "predição"],
  [/\bDecisao\b/g, "Decisão"],
  [/\bdecisao\b/g, "decisão"],
  [/\bDecisoes\b/g, "Decisões"],
  [/\bdecisoes\b/g, "decisões"],
  [/\bOperacao\b/g, "Operação"],
  [/\boperacao\b/g, "operação"],
  [/\bGovernanca\b/g, "Governança"],
  [/\bgovernanca\b/g, "governança"],
  [/\bDocumentacao\b/g, "Documentação"],
  [/\bdocumentacao\b/g, "documentação"],
  [/\bSeguranca\b/g, "Segurança"],
  [/\bseguranca\b/g, "segurança"],
  [/\bSaude\b/g, "Saúde"],
  [/\bsaude\b/g, "saúde"],
  [/\bAcoes\b/g, "Ações"],
  [/\bacoes\b/g, "ações"],
  [/\bAcao\b/g, "Ação"],
  [/\bacao\b/g, "ação"],
  [/\bVersoes\b/g, "Versões"],
  [/\bversoes\b/g, "versões"],
  [/\bVersao\b/g, "Versão"],
  [/\bversao\b/g, "versão"],
  [/\bMetrica\b/g, "Métrica"],
  [/\bmetrica\b/g, "métrica"],
  [/\bMetricas\b/g, "Métricas"],
  [/\bmetricas\b/g, "métricas"],
  [/\bDiagnostico\b/g, "Diagnóstico"],
  [/\bdiagnostico\b/g, "diagnóstico"],
  [/\bDiagnosticos\b/g, "Diagnósticos"],
  [/\bdiagnosticos\b/g, "diagnósticos"],
  [/\bClassificacao\b/g, "Classificação"],
  [/\bclassificacao\b/g, "classificação"],
  [/\bCalibracao\b/g, "Calibração"],
  [/\bcalibracao\b/g, "calibração"],
  [/\bComparacao\b/g, "Comparação"],
  [/\bcomparacao\b/g, "comparação"],
  [/\bComposicao\b/g, "Composição"],
  [/\bcomposicao\b/g, "composição"],
  [/\bExportacao\b/g, "Exportação"],
  [/\bexportacao\b/g, "exportação"],
  [/\bExportacoes\b/g, "Exportações"],
  [/\bexportacoes\b/g, "exportações"],
  [/\bIntegracao\b/g, "Integração"],
  [/\bintegracao\b/g, "integração"],
  [/\bIntegracoes\b/g, "Integrações"],
  [/\bintegracoes\b/g, "integrações"],
  [/\bDistribuicao\b/g, "Distribuição"],
  [/\bdistribuicao\b/g, "distribuição"],
  [/\bConfusao\b/g, "Confusão"],
  [/\bconfusao\b/g, "confusão"],
  [/\bIndice\b/g, "Índice"],
  [/\bindice\b/g, "índice"],
  [/\bIndices\b/g, "Índices"],
  [/\bindices\b/g, "índices"],
  [/\bPrimaria\b/g, "Primária"],
  [/\bprimaria\b/g, "primária"],
  [/\bConfiguracao\b/g, "Configuração"],
  [/\bconfiguracao\b/g, "configuração"],
  [/\bConfiguracoes\b/g, "Configurações"],
  [/\bconfiguracoes\b/g, "configurações"],
  [/\bInformacao\b/g, "Informação"],
  [/\binformacao\b/g, "informação"],
  [/\bInformacoes\b/g, "Informações"],
  [/\binformacoes\b/g, "informações"],
  [/\bNotificacao\b/g, "Notificação"],
  [/\bnotificacao\b/g, "notificação"],
  [/\bNotificacoes\b/g, "Notificações"],
  [/\bnotificacoes\b/g, "notificações"],
  [/\bUsuario\b/g, "Usuário"],
  [/\busuario\b/g, "usuário"],
  [/\bUsuarios\b/g, "Usuários"],
  [/\busuarios\b/g, "usuários"],
  [/\bEvidencia\b/g, "Evidência"],
  [/\bevidencia\b/g, "evidência"],
  [/\bEvidencias\b/g, "Evidências"],
  [/\bevidencias\b/g, "evidências"],
  [/\bTecnico\b/g, "Técnico"],
  [/\btecnico\b/g, "técnico"],
  [/\bTecnicos\b/g, "Técnicos"],
  [/\btecnicos\b/g, "técnicos"],
  [/\bAnalise\b/g, "Análise"],
  [/\banalise\b/g, "análise"],
  [/\bArea\b/g, "Área"],
  [/\barea\b/g, "área"],
  [/\bAreas\b/g, "Áreas"],
  [/\bareas\b/g, "áreas"],
  [/\bCiencia\b/g, "Ciência"],
  [/\bciencia\b/g, "ciência"],
  [/\bNegocio\b/g, "Negócio"],
  [/\bnegocio\b/g, "negócio"],
  [/\bHistorico\b/g, "Histórico"],
  [/\bhistorico\b/g, "histórico"],
  [/\bRepositorio\b/g, "Repositório"],
  [/\brepositorio\b/g, "repositório"],
  [/\bUnico\b/g, "Único"],
  [/\bunico\b/g, "único"],
  [/\bImutavel\b/g, "Imutável"],
  [/\bimutavel\b/g, "imutável"],
  [/\bFlexivel\b/g, "Flexível"],
  [/\bflexivel\b/g, "flexível"],
  [/\bVisivel\b/g, "Visível"],
  [/\bvisivel\b/g, "visível"],
  [/\bDisponivel\b/g, "Disponível"],
  [/\bdisponivel\b/g, "disponível"],
  [/\bDisponiveis\b/g, "Disponíveis"],
  [/\bdisponiveis\b/g, "disponíveis"],
  [/\bPossivel\b/g, "Possível"],
  [/\bpossivel\b/g, "possível"],
  [/\bPossiveis\b/g, "Possíveis"],
  [/\bpossiveis\b/g, "possíveis"],
  [/\bPaginacao\b/g, "Paginação"],
  [/\bpaginacao\b/g, "paginação"],
  [/\bPagina\b/g, "Página"],
  [/\bpagina\b/g, "página"],
  [/\bProxima\b/g, "Próxima"],
  [/\bproxima\b/g, "próxima"],
  [/\bMedia\b/g, "Média"],
  [/\bmedia\b/g, "média"],
  [/\bMedio\b/g, "Médio"],
  [/\bmedio\b/g, "médio"],
  [/\bMinimo\b/g, "Mínimo"],
  [/\bminimo\b/g, "mínimo"],
  [/\bMaximo\b/g, "Máximo"],
  [/\bmaximo\b/g, "máximo"],
  [/\bNumerico\b/g, "Numérico"],
  [/\bnumerico\b/g, "numérico"],
  [/\bInvalido\b/g, "Inválido"],
  [/\binvalido\b/g, "inválido"],
  [/\bPeriodo\b/g, "Período"],
  [/\bperiodo\b/g, "período"],
  [/\bCriticos\b/g, "Críticos"],
  [/\bcriticos\b/g, "críticos"],
  [/\bAcionaveis\b/g, "Acionáveis"],
  [/\bacionaveis\b/g, "acionáveis"],
  [/\bProducao\b/g, "Produção"],
  [/\bproducao\b/g, "produção"],
  [/\bSessao\b/g, "Sessão"],
  [/\bsessao\b/g, "sessão"],
  [/\bEsta\b/g, "Está"],
  [/\besta\b/g, "está"],
  [/\bEstao\b/g, "Estão"],
  [/\bestao\b/g, "estão"],
  [/\bTambem\b/g, "Também"],
  [/\btambem\b/g, "também"],
  [/\bVoce\b/g, "Você"],
  [/\bvoce\b/g, "você"],
  [/\bJa\b/g, "Já"],
  [/\bja\b/g, "já"],
  [/\bAte\b/g, "Até"],
  [/\bate\b/g, "até"],
  [/\bHa\b/g, "Há"],
  [/\bha\b/g, "há"],
  [/\bArea\b/g, "Área"],
  [/\barea\b/g, "área"],
  [/\bAreas\b/g, "Áreas"],
  [/\bareas\b/g, "áreas"],
  [/\bObrigatorio\b/g, "Obrigatório"],
  [/\bobrigatorio\b/g, "obrigatório"],
  [/\bObrigatoria\b/g, "Obrigatória"],
  [/\bobrigatoria\b/g, "obrigatória"],
  [/\bObrigatorios\b/g, "Obrigatórios"],
  [/\bobrigatorios\b/g, "obrigatórios"],
  [/\bObrigatorias\b/g, "Obrigatórias"],
  [/\bobrigatorias\b/g, "obrigatórias"],
  [/\bSenha\b/g, "Senha"],
  [/\bsenha\b/g, "senha"],
  [/\bAutenticacao\b/g, "Autenticação"],
  [/\bautenticacao\b/g, "autenticação"],
  [/\bNavegacao\b/g, "Navegação"],
  [/\bnavegacao\b/g, "navegação"],
  [/\bConclusao\b/g, "Conclusão"],
  [/\bconclusao\b/g, "conclusão"],
  [/\bRevisao\b/g, "Revisão"],
  [/\brevisao\b/g, "revisão"],
  [/\bFormulario\b/g, "Formulário"],
  [/\bformulario\b/g, "formulário"],
  [/\bDescricao\b/g, "Descrição"],
  [/\bdescricao\b/g, "descrição"],
  [/\bAuditavel\b/g, "Auditável"],
  [/\bauditavel\b/g, "auditável"],
  [/\bCenario\b/g, "Cenário"],
  [/\bcenario\b/g, "cenário"],
  [/\bCenarios\b/g, "Cenários"],
  [/\bcenarios\b/g, "cenários"],
  [/\bComeca\b/g, "Começa"],
  [/\bcomeca\b/g, "começa"],
  [/\bCritico\b/g, "Crítico"],
  [/\bcritico\b/g, "crítico"],
  [/\bCritica\b/g, "Crítica"],
  [/\bcritica\b/g, "crítica"],
  [/\bDominio\b/g, "Domínio"],
  [/\bdominio\b/g, "domínio"],
  [/\bInvestigacao\b/g, "Investigação"],
  [/\binvestigacao\b/g, "investigação"],
  [/\bJa\b/g, "Já"],
  [/\bja\b/g, "já"],
  [/\bManutencao\b/g, "Manutenção"],
  [/\bmanutencao\b/g, "manutenção"],
  [/\bMaiuscula\b/g, "Maiúscula"],
  [/\bmaiuscula\b/g, "maiúscula"],
  [/\bMinuscula\b/g, "Minúscula"],
  [/\bminuscula\b/g, "minúscula"],
  [/\bNecessario\b/g, "Necessário"],
  [/\bnecessario\b/g, "necessário"],
  [/\bNecessaria\b/g, "Necessária"],
  [/\bnecessaria\b/g, "necessária"],
  [/\bObrigatorio\b/g, "Obrigatório"],
  [/\bobrigatorio\b/g, "obrigatório"],
  [/\bObrigatoria\b/g, "Obrigatória"],
  [/\bobrigatoria\b/g, "obrigatória"],
  [/\bOrganizacao\b/g, "Organização"],
  [/\borganizacao\b/g, "organização"],
  [/\bPadrao\b/g, "Padrão"],
  [/\bpadrao\b/g, "padrão"],
  [/\bPolitica\b/g, "Política"],
  [/\bpolitica\b/g, "política"],
  [/\bPadroes\b/g, "Padrões"],
  [/\bpadroes\b/g, "padrões"],
  [/\bProprio\b/g, "Próprio"],
  [/\bproprio\b/g, "próprio"],
  [/\bPropria\b/g, "Própria"],
  [/\bpropria\b/g, "própria"],
  [/\bSao\b/g, "São"],
  [/\bsao\b/g, "são"],
  [/\bSeparacao\b/g, "Separação"],
  [/\bseparacao\b/g, "separação"],
  [/\bServico\b/g, "Serviço"],
  [/\bservico\b/g, "serviço"],
  [/\bSimulacao\b/g, "Simulação"],
  [/\bsimulacao\b/g, "simulação"],
  [/\bSituacao\b/g, "Situação"],
  [/\bsituacao\b/g, "situação"],
  [/\bTambem\b/g, "Também"],
  [/\btambem\b/g, "também"],
  [/\bTecnica\b/g, "Técnica"],
  [/\btecnica\b/g, "técnica"],
  [/\bTecnicas\b/g, "Técnicas"],
  [/\btecnicas\b/g, "técnicas"],
  [/\bValidacao\b/g, "Validação"],
  [/\bvalidacao\b/g, "validação"],
  [/\bNumero\b/g, "Número"],
  [/\bnumero\b/g, "número"],
  [/\bO que e\b/g, "O que é"],
  [/\bo que e\b/g, "o que é"],
  [/\bModelTrace e\b/g, "ModelTrace é"],
  [/\bO papel dele e\b/g, "O papel dele é"],
  [/\bO primeiro passo e\b/g, "O primeiro passo é"],
  [/\bA predição e\b/g, "A predição é"],
  [/\bA predicao e\b/g, "A predição é"],
  [/\bA decisão e\b/g, "A decisão é"],
  [/\bA decisao e\b/g, "A decisão é"],
  [/\bO projeto e\b/g, "O projeto é"],
  [/\bO Monitor e\b/g, "O Monitor é"],
  [/\bO Workbench e\b/g, "O Workbench é"],
  [/\bA API e\b/g, "A API é"],
  [/\bEsse documento e\b/g, "Esse documento é"],
  [/\bEssa tela e\b/g, "Essa tela é"],
  [/\bEsse desenho e\b/g, "Esse desenho é"],
  [/\bA Visão geral\b/g, "A Visão geral"],
  [/\bO Visão geral\b/g, "A Visão geral"],
  [/\bno Visão geral\b/g, "na Visão geral"],
  [/\bdo Visão geral\b/g, "da Visão geral"],
  [/\bEntao\b/g, "Então"],
  [/\bentao\b/g, "então"],
  [/\bNao\b/g, "Não"],
  [/\bnao\b/g, "não"]
];

const enWordReplacements: Array<[RegExp, string]> = [
  [/\bSaúde operacional do modelo\b/g, "Operational model health"],
  [/\bComposição da saúde operacional\b/g, "Operational health composition"],
  [/\bDistribuição de score\b/g, "Score distribution"],
  [/\bMatriz de confusão\b/g, "Confusion matrix"],
  [/\bAuditoria\b/g, "Audit"],
  [/\bGovernança\b/g, "Governance"],
  [/\bPredições\b/g, "Predictions"],
  [/\bOperação\b/g, "Operations"],
  [/\bSegurança\b/g, "Security"],
  [/\bDocumentação\b/g, "Documentation"],
  [/\bVisão geral\b/g, "Overview"],
  [/\bSaúde\b/g, "Health"],
  [/\bsaúde\b/g, "health"],
  [/\bversões\b/g, "versions"],
  [/\bversão\b/g, "version"],
  [/\bsem produção\b/g, "no production"],
  [/\bprodução\b/g, "production"],
  [/\bmétrica primária\b/g, "primary metric"],
  [/\bmétrica\b/g, "metric"],
  [/\bíndices\b/g, "indexes"],
  [/\bíndice\b/g, "index"],
  [/\bexportações operacionais\b/g, "operational exports"],
  [/\bexportações\b/g, "exports"],
  [/\bativos\b/g, "active"],
  [/\bativo\b/g, "active"],
  [/\bacionáveis\b/g, "actionable"],
  [/\bcasos\b/g, "cases"],
  [/\balunos\b/g, "students"]
];

const ptFromEnglishWordReplacements: Array<[RegExp, string]> = [
  [/\bOperational model health\b/g, "Saúde operacional do modelo"],
  [/\bOperational health composition\b/g, "Composição da saúde operacional"],
  [/\bScore distribution\b/g, "Distribuição de score"],
  [/\bConfusion matrix\b/g, "Matriz de confusão"],
  [/\bVolume over time\b/g, "Volume temporal"],
  [/\bAverage score\b/g, "Score médio"],
  [/\bFeedback coverage\b/g, "Cobertura de feedback"],
  [/\bGovernance active\b/g, "Governança ativa"],
  [/\bPredictions\b/g, "Predições"],
  [/\bOperations\b/g, "Operação"],
  [/\bOverview\b/g, "Visão geral"],
  [/\bGovernance\b/g, "Governança"],
  [/\bSecurity\b/g, "Segurança"],
  [/\bDocumentation\b/g, "Documentação"],
  [/\bDecision Ops\b/g, "Operação de decisões"],
  [/\bCommands\b/g, "Comandos"],
  [/\bRefresh\b/g, "Atualizar"],
  [/\bSign out\b/g, "Sair"],
  [/\bProject\b/g, "Projeto"],
  [/\bModel\b/g, "Modelo"],
  [/\bSelect\b/g, "Selecionar"],
  [/\bAccount created\./g, "Conta criada."],
  [/\bContinue reading\b/g, "Continue lendo"],
  [/\bWorkspace without project\b/g, "Workspace sem projeto"],
  [/\bChoose a project to start monitoring\./g, "Escolha um projeto para iniciar o monitoramento."],
  [/\bExecutive signal for operations, feedback, alerts, and performance\./g, "Sinal executivo de operação, feedback, alertas e desempenho."],
  [/\bAudit, indexes, and operational exports\./g, "Auditoria, índices e exportações operacionais."],
  [/\bBelow the operational target\./g, "Abaixo da meta operacional."],
  [/\bversions\b/g, "versões"],
  [/\bversion\b/g, "versão"],
  [/\bno production\b/g, "sem produção"],
  [/\bproduction\b/g, "produção"],
  [/\bprimary metric\b/g, "métrica primária"],
  [/\bmetric\b/g, "métrica"],
  [/\bindexes\b/g, "índices"],
  [/\bindex\b/g, "índice"],
  [/\boperational exports\b/g, "exportações operacionais"],
  [/\bexports\b/g, "exportações"],
  [/\b([0-9]+) active\b/g, "$1 ativos"],
  [/\bactive\b/g, "ativo"],
  [/\bActionable\b/g, "Acionáveis"],
  [/\bAlerts\b/g, "Alertas"],
  [/\bHealth\b/g, "Saúde"],
  [/\bhealth\b/g, "saúde"]
];

let reverseEnglishExactCache: Dictionary | null = null;

function englishToPortugueseExact() {
  if (reverseEnglishExactCache) return reverseEnglishExactCache;
  reverseEnglishExactCache = {};
  for (const [pt, en] of Object.entries(enExact)) {
    if (!reverseEnglishExactCache[en]) {
      reverseEnglishExactCache[en] = accentPortuguese(pt);
    }
  }
  reverseEnglishExactCache["Flexible schema"] = "Esquema flexível";
  return reverseEnglishExactCache;
}

function preserveWhitespace(original: string, translated: string) {
  const leading = original.match(/^\s*/)?.[0] ?? "";
  const trailing = original.match(/\s*$/)?.[0] ?? "";
  return `${leading}${translated}${trailing}`;
}

export function accentPortuguese(value: string) {
  let next = value;
  for (const [pattern, replacement] of ptWordReplacements) {
    next = next.replace(pattern, replacement);
  }
  return next;
}

export function translateText(value: unknown, locale: Locale) {
  if (typeof value !== "string" || !value.trim()) return value as string;
  const trimmed = value.trim();
  const dynamic = dynamicExact[trimmed]?.[locale];
  if (dynamic) return preserveWhitespace(value, dynamic);
  if (locale === "pt-BR") {
    const reverseExact = englishToPortugueseExact()[trimmed];
    if (reverseExact) return preserveWhitespace(value, reverseExact);
    let fallback = trimmed;
    for (const [pattern, replacement] of ptFromEnglishWordReplacements) {
      fallback = fallback.replace(pattern, replacement);
    }
    if (fallback !== trimmed) return preserveWhitespace(value, accentPortuguese(fallback));
    const exact = ptExact[trimmed] || dynamicExact[accentPortuguese(trimmed)]?.["pt-BR"];
    return preserveWhitespace(value, accentPortuguese(exact || trimmed));
  }
  const accented = accentPortuguese(trimmed);
  const exact = enExact[trimmed] || enExact[accented] || dynamicExact[trimmed]?.en || dynamicExact[accented]?.en;
  if (exact) return preserveWhitespace(value, exact);
  let fallback = accented;
  for (const [pattern, replacement] of enWordReplacements) {
    fallback = fallback.replace(pattern, replacement);
  }
  if (fallback !== accented) return preserveWhitespace(value, fallback);
  return value;
}

export function localizedField(item: any, field: string, locale: Locale, fallback = ""): string {
  if (!item) return fallback;
  const localized = item.i18n?.[field]?.[locale] || item.i18n?.[field]?.[DEFAULT_LOCALE];
  const value = localized ?? item[field] ?? fallback;
  return translateText(String(value ?? fallback), locale);
}

const docOverridesEn: Record<string, any> = {
  start: {
    label: "Start here",
    title: "First use",
    intro: "ModelTrace organizes production model operations: predictions, feedback, alerts, diagnostics, security, and audit in one workspace.",
    topics: [
      {
        heading: "What ModelTrace is",
        paragraphs: [
          "ModelTrace is an operations layer for machine learning models. It does not replace training, notebooks, experiment tracking, or the MLOps pipeline. Its role starts after a model begins making decisions: it records the inputs, score, version, decision, review, and observed outcome.",
          "The product is designed for monitoring and governance. Data scientists use the technical areas to inspect thresholds, calibration, slices, errors, and drift. Operations teams use predictions, cases, and alerts to prioritize follow-up. Audit teams use history, evidence, and API keys to understand every event."
        ]
      },
      {
        heading: "Recommended flow",
        paragraphs: [
          "Start by choosing a project and a model in the sidebar. The whole interface then uses that context. Overview shows the operational picture, Predictions opens the decision list, DS Lab shows diagnostics, Operations concentrates cases and alerts, Workbench registers a prediction without JSON, and Governance covers security, audit, and credentials.",
          "In real usage, a model service sends predictions to the API. When the true outcome becomes available, another system or an analyst sends feedback. With those two flows, ModelTrace recalculates online metrics, raises alerts, and preserves an auditable trail by entity, model, version, and request_id."
        ]
      },
      {
        heading: "Who uses each area",
        paragraphs: [
          "Data science teams usually work in DS Lab, Monitor, and Decision inspector. Business teams usually track Overview, Operations, and Predictions. Technology teams use API, Workbench, and Governance to integrate systems, manage keys, validate contracts, and recover evidence.",
          "This separation keeps the operational user away from raw JSON while still giving engineers and data scientists the technical detail they need."
        ]
      }
    ],
    related: ["Overview", "Predictions", "DS Lab", "Governance"]
  },
  concepts: {
    label: "Concepts",
    title: "Core concepts",
    intro: "The platform uses a flexible document structure that supports binary classification, multiclass classification, regression, ranking, anomaly detection, and other decision problems.",
    topics: [
      {
        heading: "Project",
        paragraphs: [
          "A project represents a real use case: a product, department, customer journey, risk process, operational queue, or any context where a model makes decisions.",
          "The same installation can monitor different domains because each project groups its own models, predictions, alerts, audit events, and security settings."
        ]
      },
      {
        heading: "Model and version",
        paragraphs: [
          "A model represents a decision family. A version represents a specific delivery of that model, with algorithm metadata, feature contract, reference metrics, status, and creation date.",
          "Versioning is essential for audit because the same entity can be evaluated by different model versions over time."
        ]
      },
      {
        heading: "Prediction",
        paragraphs: [
          "A prediction is the central document in ModelTrace. It stores the evaluated entity, project, model, version, features, score, label, decision, explanations, technical context, and audit metadata.",
          "The document format is flexible. Classification can store score and label, regression can store an estimated value, ranking can store position, and anomaly detection can store anomaly score and severity."
        ]
      },
      {
        heading: "Feedback, alert, and audit",
        paragraphs: [
          "Feedback is the observed outcome after a decision. It turns predictions into evidence for precision, recall, confusion matrix, calibration, slices, and error analysis.",
          "Alerts evaluate project and model signals such as low feedback, high actionable volume, drift, feature quality, SLA, or custom rules. Audit records the relevant events."
        ]
      }
    ],
    related: ["Document model", "API", "Governance"]
  },
  "access-session": {
    label: "Access and session",
    title: "Access, session, and notifications",
    intro: "This section explains login, registration, local session storage, refresh, sign out, and action feedback.",
    topics: [
      {
        heading: "Entry screen",
        paragraphs: [
          "When there is no active session, ModelTrace shows the access screen. Email identifies the user, password authenticates the account, and name is used during initial registration.",
          "After a successful login, the interface stores the session in the browser and loads projects, security posture, and the first workspace data."
        ]
      },
      {
        heading: "Refresh and sign out",
        paragraphs: [
          "Refresh reloads the whole workspace: projects, models, dashboard, operations, audit, security posture, API keys, versions, and screen-specific data.",
          "Sign out ends the backend session, clears local state, removes the browser session, and shows a confirmation notification."
        ]
      },
      {
        heading: "Toasts and status ribbon",
        paragraphs: [
          "Every important action updates the status ribbon and shows a temporary toast. Information toasts indicate processing, success toasts confirm completion, and error toasts show a localized failure message.",
          "When an action returns data, the interface also shows a result block so the user can inspect what the backend returned."
        ]
      }
    ],
    related: ["Navigation", "Governance", "API"]
  },
  navigation: {
    label: "Navigation",
    title: "Navigation, context, and commands",
    intro: "ModelTrace is a single-page application with internal views. Navigation changes the active work area while preserving project and model context.",
    topics: [
      {
        heading: "Sidebar",
        paragraphs: [
          "The sidebar is the starting point. Overview, Monitor, DS Lab, Predictions, Operations, Workbench, Governance, and Docs select the area shown in the main panel.",
          "Changing the project resets dependent data and reloads models, dashboard, operations, audit, security, and API keys. Changing the model reloads versions and diagnostics."
        ]
      },
      {
        heading: "Topbar",
        paragraphs: [
          "The topbar shows domain, environment, project name, and description. It also contains Commands, Refresh, Sign out, and the language toggle.",
          "The status ribbon below the topbar shows the last important event and the signed-in user."
        ]
      },
      {
        heading: "Command palette",
        paragraphs: [
          "Commands opens a searchable action palette. It can also be opened with Ctrl+K or Cmd+K.",
          "The palette can open screens, refresh the workspace, run drift, check alerts, export predictions, export audit evidence, and open documentation topics."
        ]
      },
      {
        heading: "Context-dependent actions",
        paragraphs: [
          "Some actions require a project, such as alert checks, exports, and API keys. Others require a model, such as drift, fairness, version comparison, and DS Lab.",
          "When context is missing, the interface shows a localized error instead of creating inconsistent records."
        ]
      }
    ],
    related: ["Access and session", "Overview", "Docs"]
  },
  overview: {
    label: "Overview",
    title: "Overview",
    intro: "Executive summary for the selected project: volume, operational health, feedback, average score, confusion matrix, and priorities.",
    topics: [
      {
        heading: "Reading indicators",
        paragraphs: [
          "Overview quickly answers whether the model is operating in the expected range. KPI cards show prediction volume, actionable rate, feedback coverage, average score, and active alerts.",
          "Clickable KPIs open the right investigation path, such as filtered Predictions or active alerts in Operations."
        ]
      },
      {
        heading: "Operational health",
        paragraphs: [
          "Operational health is not pure accuracy. It combines feedback coverage, observed performance, alerts, and actionable volume to indicate whether the model is operationally reliable.",
          "Improving the score means increasing feedback, resolving alerts, tuning thresholds when workload is high, fixing data issues, and reducing version inconsistencies."
        ]
      },
      {
        heading: "Charts and matrix",
        paragraphs: [
          "Score distribution shows concentration across score ranges. Unusual concentration can indicate data changes, feature bugs, rule changes, or a real domain shift.",
          "The confusion matrix appears when enough feedback exists to classify true positives, false positives, true negatives, and false negatives."
        ]
      }
    ],
    related: ["Predictions", "Operations", "DS Lab"]
  },
  monitor: {
    label: "Monitor",
    title: "Monitor",
    intro: "Technical-operational screen for model versions, drift, version comparison, fairness, and exports.",
    topics: [
      {
        heading: "Screen usage",
        paragraphs: [
          "Monitor lists model versions and runs checks on demand. Refresh synchronizes the current project and model context.",
          "Action buttons show success or error toasts, and long-running analyses expose a result block when the backend returns data."
        ]
      },
      {
        heading: "Drift",
        paragraphs: [
          "Drift compares recent distributions against a reference. It can evaluate score, numeric features, categorical features, and volume stability.",
          "A drift alert does not automatically mean the model is wrong. It means the environment changed enough to justify investigation."
        ]
      },
      {
        heading: "Comparison and fairness",
        paragraphs: [
          "Version comparison groups online predictions by model_version to show behavioral differences between versions.",
          "Fairness analysis compares performance by a selected feature and should be interpreted carefully, especially when the feature is sensitive or a proxy."
        ]
      }
    ],
    related: ["DS Lab", "Governance", "API"]
  },
  lab: {
    label: "DS Lab",
    title: "DS Lab",
    intro: "Workspace for data scientists to inspect threshold, calibration, feature coverage, errors, slices, and analysis priorities.",
    topics: [
      {
        heading: "What to analyze",
        paragraphs: [
          "DS Lab turns production predictions and real feedback into diagnostics. It shows threshold curves, calibration, source quality, feature contract, feature importance, monitored slices, and error classes.",
          "It complements notebooks and experiment tracking with online behavior and operational traceability."
        ]
      },
      {
        heading: "Threshold",
        paragraphs: [
          "Threshold defines the point where a score becomes actionable. Lower thresholds usually increase recall and workload; higher thresholds usually increase precision and reduce workload.",
          "The simulator moves a vertical line over the chart and updates precision, recall, F2, and workload for the selected cut."
        ]
      },
      {
        heading: "Calibration, slices, and contract",
        paragraphs: [
          "Calibration checks whether predicted scores behave like reliable probabilities. Slices group entities by relevant attributes for segmented analysis.",
          "The feature contract compares what the model expects with what predictions actually receive."
        ]
      }
    ],
    related: ["Predictions", "Feedback", "What-if"]
  },
  predictions: {
    label: "Predictions",
    title: "Predictions",
    intro: "Operational list of registered decisions. Server-side pagination keeps the screen responsive on large datasets.",
    topics: [
      {
        heading: "Operational table",
        paragraphs: [
          "Each row represents an evaluation made by a model version for an entity. The table shows ID, entity, version, label, score, feedback status, and date.",
          "Clicking a row opens the Decision inspector with the full decision context."
        ]
      },
      {
        heading: "Filters and pagination",
        paragraphs: [
          "Search, label, window, and feedback filters reduce the result set. Pagination happens on the server, so the browser only receives the current page.",
          "The backend keeps the full filtered base while the UI renders a manageable slice."
        ]
      },
      {
        heading: "Export",
        paragraphs: [
          "Exports support offline investigation, audit, and controlled sharing with other teams.",
          "Sensitive data should be minimized or redacted according to company policy."
        ]
      }
    ],
    related: ["Decision inspector", "Workbench", "Governance"]
  },
  inspector: {
    label: "Decision inspector",
    title: "Decision inspector",
    intro: "Side panel for investigating the selected decision: score, feedback, what-if, replay, explainability, and technical details.",
    topics: [
      {
        heading: "Decision analysis",
        paragraphs: [
          "The inspector opens after a prediction is selected. It shows entity, score, class, window, model version, top explanations, and technical details.",
          "The panel scrolls independently so predictions remain usable even when the selected decision has many features."
        ]
      },
      {
        heading: "Feedback",
        paragraphs: [
          "Feedback records the observed outcome after the decision. It can be manual, imported, or sent by another system.",
          "Once saved, feedback updates metrics, confusion matrix, slices, alerts, and entity history."
        ]
      },
      {
        heading: "What-if",
        paragraphs: [
          "What-if simulates how the score could change if selected features changed. In the current implementation, the result is local and estimated unless a real scoring endpoint is connected.",
          "The user chooses the fields and values. The platform does not decide the final values automatically."
        ]
      },
      {
        heading: "Replay and export",
        paragraphs: [
          "Replay creates a new reading of the same decision without overwriting the original prediction.",
          "Export generates auditable data for the selected project and keeps an evidence trail."
        ]
      }
    ],
    related: ["Predictions", "Feedback", "DS Lab"]
  },
  feedback: {
    label: "Feedback",
    title: "Feedback and observed outcome",
    intro: "Feedback turns a registered prediction into evidence of real-world performance.",
    topics: [
      {
        heading: "When to use",
        paragraphs: [
          "Use Feedback when the true outcome is known. It can represent an event that happened, a class confirmed by review, or a real numeric value.",
          "Positive, Negative, and Inconclusive map to the model labels and determine whether the case contributes to supervised metrics."
        ]
      },
      {
        heading: "Source and note",
        paragraphs: [
          "Source identifies where the feedback came from, such as manual_review, batch load, CRM, ERP, or another operational system.",
          "Notes are optional and should remain concise because they can appear in audit evidence."
        ]
      },
      {
        heading: "Automatic classification",
        paragraphs: [
          "The backend compares the original prediction with the observed result and classifies the case as TP, FP, TN, FN, or inconclusive.",
          "That classification feeds health, confusion matrix, threshold curves, calibration, error analysis, and alerts."
        ]
      },
      {
        heading: "Product impact",
        paragraphs: [
          "Saving feedback updates prediction status and can change Overview, DS Lab, and operational alerts.",
          "Incorrect feedback damages the product, so uncertain outcomes should be marked inconclusive or delayed until a reliable source is available."
        ]
      }
    ],
    related: ["Decision inspector", "Predictions", "DS Lab"]
  },
  whatif: {
    label: "What-if",
    title: "What-if",
    intro: "What-if is a local simulation for a selected decision. It changes features and estimates how the score could move before a real scoring run.",
    topics: [
      {
        heading: "What happens when it opens",
        paragraphs: [
          "The user selects a prediction and clicks What-if. The interface loads up to ten features from that prediction and converts them into editable fields.",
          "Numeric features become numeric inputs, boolean features become true/false selectors, and other values become text inputs."
        ]
      },
      {
        heading: "Optimistic, Conservative, and Reset",
        paragraphs: [
          "Reset restores the current prediction values. Optimistic reduces signals interpreted as risk and increases signals interpreted as quality. Conservative does the opposite.",
          "The presets infer meaning from feature names. When a feature does not match known patterns, the value changes little or remains unchanged."
        ]
      },
      {
        heading: "How the simulation is sent",
        paragraphs: [
          "When the user clicks Simulate scenario, the UI coerces values back to numbers, booleans, or strings and sends hypothetical_features to the backend.",
          "The backend compares the hypothetical features with the original prediction and returns original score, estimated score, delta, and whether the decision would change."
        ]
      },
      {
        heading: "What What-if does not promise",
        paragraphs: [
          "Current What-if is an estimate when no real scoring endpoint is connected. It is useful for investigation and explanation, but it is not an official new decision.",
          "In a corporate implementation, What-if should clearly show whether the result was estimated by ModelTrace or executed by the real model service."
        ]
      },
      {
        heading: "When to use it",
        paragraphs: [
          "Use What-if to inspect sensitivity of an individual decision, especially cases close to the threshold.",
          "What-if does not save a new prediction automatically. Use Replay or saved scenarios when the company needs evidence."
        ]
      }
    ],
    related: ["Decision inspector", "Replay and exports", "DS Lab"]
  },
  "replay-export": {
    label: "Replay and exports",
    title: "Replay, exports, and evidence",
    intro: "Replay and exports are evidence features for comparing decision readings and extracting auditable data.",
    topics: [
      {
        heading: "Replay",
        paragraphs: [
          "Replay creates a document related to an existing prediction. It does not overwrite the original score, label, or feedback.",
          "The current UI creates a simple replay using a target version and adjusted score. The backend stores whether the decision changed."
        ]
      },
      {
        heading: "Export predictions",
        paragraphs: [
          "Export creates a CSV for the current project with features and explanations when enabled.",
          "Exports are useful for audit, offline analysis, controlled sharing, and reporting."
        ]
      },
      {
        heading: "Export audit",
        paragraphs: [
          "Governance can export audit evidence as JSON with timestamp, project, filter, event count, and events.",
          "The file supports reviews, incident analysis, academic work, and internal audit."
        ]
      },
      {
        heading: "DS Lab package",
        paragraphs: [
          "The DS Lab package exports model diagnostics as JSON.",
          "It can be used in notebooks, reports, or offline investigation."
        ]
      }
    ],
    related: ["Decision inspector", "Governance", "API"]
  },
  operations: {
    label: "Operations",
    title: "Operations",
    intro: "Center for cases, alerts, incidents, cohorts, source quality, and model evaluations.",
    topics: [
      {
        heading: "Operational queue",
        paragraphs: [
          "Operations organizes daily follow-up. It shows open cases, critical cases, active alerts, monitored cohorts, source quality, incidents, and model evaluations.",
          "A case can represent a high-risk prediction, missing feedback, a priority entity, or any operational rule."
        ]
      },
      {
        heading: "Alerts",
        paragraphs: [
          "Alerts can be automatic or configured by rules. They may point to low feedback, high actionable volume, drift, source quality problems, or feature contract issues.",
          "Clicking an alert navigates to the area where investigation should happen."
        ]
      },
      {
        heading: "Cohorts, incidents, and quality",
        paragraphs: [
          "Cohorts group entities that need separate monitoring by period, region, product, channel, or segment.",
          "Incidents formalize problems that require treatment. Source quality helps distinguish model errors, data errors, and process errors."
        ]
      }
    ],
    related: ["Alerts", "Governance", "Overview"]
  },
  alerts: {
    label: "Alerts",
    title: "Alerts and operational rules",
    intro: "Alerts turn metrics, data quality, and operational risk into actionable signals.",
    topics: [
      {
        heading: "Check alerts",
        paragraphs: [
          "Check alerts evaluates configured rules and default rules for the current project.",
          "After the check, the interface reloads Operations and Dashboard and shows how many alerts were created."
        ]
      },
      {
        heading: "Alert types",
        paragraphs: [
          "The engine supports performance_threshold, feedback_rate_low, volume_drop, prediction_drift, data_drift, missing_features, and deprecated_version_active.",
          "Default rules help every project, while custom rules adapt thresholds to the domain."
        ]
      },
      {
        heading: "Click an alert",
        paragraphs: [
          "Clicking an alert does not resolve it. It opens the operational area where the user can investigate the related data.",
          "Missing features points to Source quality, backlog points to the operational queue, and other alerts remain in Active alerts."
        ]
      },
      {
        heading: "Severity and lifecycle",
        paragraphs: [
          "Severity indicates operational priority, not definitive proof that the model failed.",
          "The backend supports acknowledge and resolve flows; a corporate UI can add owner, SLA, comments, snooze, incidents, and timelines."
        ]
      }
    ],
    related: ["Operations", "DS Lab", "Governance"]
  },
  workbench: {
    label: "Workbench",
    title: "Workbench",
    intro: "Guided entry for registering test predictions or operational simulations without requiring JSON from the final user.",
    topics: [
      {
        heading: "Using the interface",
        paragraphs: [
          "Workbench registers a prediction through a form. The user enters entity, display name, version, score, and feature values.",
          "It is useful for validation, demonstration, small controlled loads, and integration testing."
        ]
      },
      {
        heading: "Contract validation",
        paragraphs: [
          "The feature contract defines expected fields, required fields, types, and common values.",
          "If a required feature is missing, Workbench shows an error before sending the prediction."
        ]
      }
    ],
    related: ["API", "Predictions", "Governance"]
  },
  governance: {
    label: "Governance",
    title: "Governance and security",
    intro: "Area for security posture, API keys, audit, evidence, and the document model.",
    topics: [
      {
        heading: "Purpose",
        paragraphs: [
          "Governance contains the controls a company needs to operate real data: security posture, API keys, audit trail, exports, document map, and evidence.",
          "Sensitive data requires strong password hashing, hashed API keys, token expiration, and audit records for relevant actions."
        ]
      },
      {
        heading: "API keys",
        paragraphs: [
          "API keys are used by external systems. Each key belongs to an organization, can be restricted to a project, has scopes, and can expire.",
          "The platform stores only the key hash. The full key is shown only once at creation time."
        ]
      },
      {
        heading: "Audit and evidence",
        paragraphs: [
          "Audit trail lists relevant events such as login, key creation, prediction ingestion, feedback, replay, export, and security checks.",
          "Evidence exports should preserve enough context to explain a decision while exposing only the data needed."
        ]
      }
    ],
    related: ["API", "Document model", "Operations"]
  },
  api: {
    label: "API",
    title: "API and integrations",
    intro: "The API registers predictions, feedback, replay, what-if, exports, alerts, models, and audit data.",
    topics: [
      {
        heading: "Authentication",
        paragraphs: [
          "The API accepts session tokens for authenticated users and API keys for external systems.",
          "Every mutating call must use a credential with the required scope."
        ]
      },
      {
        heading: "Prediction ingestion",
        paragraphs: [
          "External systems send project, model, version, entity, features, prediction, and request_id.",
          "Features vary by model, but they should follow the version contract."
        ]
      },
      {
        heading: "Query and retrieval",
        paragraphs: [
          "Internal systems can retrieve predictions by project, model, entity, feedback status, label, version, and pagination.",
          "Feedback should be sent when the observed outcome becomes reliable."
        ]
      }
    ],
    related: ["Workbench", "Governance", "Predictions"]
  },
  "api-example": {
    label: "End-to-end example",
    title: "Complete example: from model to operations",
    intro: "A short annotated example that draws a clear line between your model code and the ModelTrace API. The use case is binary classification of operational risk, but the pattern applies to any domain.",
    topics: [
      {
        heading: "Flow overview",
        paragraphs: [
          "The flow combines two clearly separated parts. The first is your Machine Learning code: training, scoring, and explanations. The second is the ModelTrace REST API: registering project, model, version, predictions, feedback, and triggering dashboards, drift, and exports.",
          "Keeping this boundary clear lets you swap algorithms without touching the integration. The 'YOUR MODEL' block changes; the API calls stay the same. The full runnable example lives in docs/api.md, section 23."
        ]
      },
      {
        heading: "Block 1 - YOUR MODEL (sklearn, joblib, your logic)",
        paragraphs: [
          "Train your model the usual way. Here we use LogisticRegression over synthetic industrial maintenance features. In production you replace it with your real pipeline (LightGBM, XGBoost, neural nets, rules) without changing the integration."
        ]
      },
      {
        heading: "Block 2 - MODELTRACE API (HTTP REST under /api/v1)",
        paragraphs: [
          "Once the model is trained, register its context in ModelTrace. Four calls run only once per model: login, create project, create model, create version. Then create a dedicated API key for the pipeline."
        ]
      },
      {
        heading: "Block 3 - Serving loop (model + API alternating)",
        paragraphs: [
          "Each decision in production runs two things in sequence. First, your model computes the score (your code). Then you push the prediction document to ModelTrace (API call). Use request_id for idempotency, which protects against duplicate retries."
        ]
      },
      {
        heading: "Block 4 - Feedback, dashboard, and drift (API only)",
        paragraphs: [
          "When the real outcome arrives, send feedback. The platform updates confusion matrix, recall, precision, and the Operations tab. Then read the dashboard, run drift, or export CSV for audit. All of these are API calls; the model is no longer needed at this stage."
        ]
      },
      {
        heading: "Summary of the split",
        paragraphs: [
          "Your model decides. ModelTrace observes, audits, and governs. The 9 API functions (login, project, model, version, api_key, prediction, feedback, dashboard, drift) cover the complete post-deploy cycle. The full runnable example, including model training with synthetic data, is in docs/api.md section 23."
        ]
      }
    ],
    related: ["API", "Workbench", "Predictions"]
  },
  "action-results": {
    label: "Results",
    title: "Action results and technical details",
    intro: "The platform gives immediate feedback for each action and preserves technical details when investigation is needed.",
    topics: [
      {
        heading: "Result block",
        paragraphs: [
          "Actions such as Drift, Fairness, Version comparison, API key creation, Prediction registration, What-if, Replay, Export, and Security controls show a result block.",
          "The block summarizes backend output so the user is not dependent only on the toast."
        ]
      },
      {
        heading: "Prediction technical details",
        paragraphs: [
          "The Decision inspector includes a technical details section with the structured prediction document.",
          "It is meant for data science, engineering, and audit users who need to inspect payloads, feature types, metadata, or evidence."
        ]
      },
      {
        heading: "Empty states and errors",
        paragraphs: [
          "When a list has no data, the interface shows an empty state instead of a broken table.",
          "When an action fails, the user sees a localized error message while technical details stay in logs or technical blocks."
        ]
      },
      {
        heading: "Why code still appears in docs",
        paragraphs: [
          "Operational users do not need JSON to use the product.",
          "Code examples exist for integrators, data scientists, and engineers who need to consume the API directly."
        ]
      }
    ],
    related: ["Decision inspector", "API", "Workbench"]
  }
};

export function localizeDocSections<T extends Array<any>>(sections: T, locale: Locale): T {
  return sections.map((section) => ({
    ...section,
    ...(locale === "en" && docOverridesEn[section.id] ? docOverridesEn[section.id] : {}),
  })).map((section, sectionIndex) => ({
    ...section,
    label: translateText(section.label, locale),
    title: translateText(section.title, locale),
    intro: translateText(section.intro, locale),
    related: (section.related || []).map((item: string) => translateText(item, locale)),
    topics: (section.topics || []).map((topic: any, topicIndex: number) => {
      const originalTopic = sections[sectionIndex]?.topics?.[topicIndex];
      const example = topic.example || originalTopic?.example;
      return {
        ...topic,
        heading: translateText(topic.heading, locale),
        paragraphs: (topic.paragraphs || []).map((paragraph: string) => translateText(paragraph, locale)),
        example: example ? {
          ...example,
          title: translateText(example.title, locale),
          caption: translateText(example.caption, locale)
        } : undefined
      };
    })
  })) as T;
}

const SKIP_NODE_NAMES = new Set(["SCRIPT", "STYLE", "CODE", "PRE", "TEXTAREA", "INPUT", "SELECT"]);
const TRANSLATABLE_ATTRIBUTES = ["placeholder", "aria-label", "title"];

export function translateDocument(root: ParentNode, locale: Locale) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent || SKIP_NODE_NAMES.has(parent.nodeName)) return NodeFilter.FILTER_REJECT;
      if (!node.nodeValue?.trim()) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  const textNodes: Text[] = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode as Text);
  textNodes.forEach((node) => {
    const translated = translateText(node.nodeValue || "", locale);
    if (translated !== node.nodeValue) node.nodeValue = translated;
  });

  root.querySelectorAll?.("*").forEach((element) => {
    if (SKIP_NODE_NAMES.has(element.nodeName)) return;
    TRANSLATABLE_ATTRIBUTES.forEach((attribute) => {
      const value = element.getAttribute(attribute);
      if (!value) return;
      const translated = translateText(value, locale);
      if (translated !== value) element.setAttribute(attribute, translated);
    });
  });
}
