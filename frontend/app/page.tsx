"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Archive,
  BarChart3,
  BookOpen,
  Camera,
  CheckCircle2,
  Command,
  CircleDollarSign,
  Database,
  Download,
  Flame,
  Gauge,
  GitCompare,
  KeyRound,
  Layers3,
  LineChart as LineChartIcon,
  Lock,
  LogOut,
  MailCheck,
  Play,
  RefreshCcw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  Upload,
  UserCircle,
  UserPlus,
  Zap
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { API_URL, apiRequest } from "@/lib/api";
import {
  DEFAULT_LOCALE,
  LOCALE_STORAGE_KEY,
  Locale,
  localizedField,
  localizeDocSections,
  translateDocument,
  translateText
} from "@/lib/i18n";
import { AuthScreen } from "@/components/auth/AuthScreen";
import { Sidebar } from "@/components/shell/Sidebar";
import { Topbar } from "@/components/shell/Topbar";
import { CommandPalette, type CommandItem as PaletteItem } from "@/components/shell/CommandPalette";
import { NotificationsDrawer } from "@/components/shell/NotificationsDrawer";
import { ShortcutsModal } from "@/components/shell/ShortcutsModal";
import { SlaAlertBar } from "@/components/shell/SlaAlertBar";
import {
  OnboardingTour,
  dismissOnboarding,
  shouldShowOnboarding
} from "@/components/shell/OnboardingTour";
import { OverviewView } from "@/components/views/OverviewView";
import { ChampionChallengerView } from "@/components/views/ChampionChallengerView";
import { DriftHeatmapView } from "@/components/views/DriftHeatmapView";
import { SlaKanbanView, type CaseStatus } from "@/components/views/SlaKanbanView";
import { CostUsageView } from "@/components/views/CostUsageView";
import { useKeyboardShortcuts } from "@/components/hooks/useKeyboardShortcuts";
import { useTheme } from "@/components/hooks/useTheme";
import { Toast } from "@/components/ui/Toast";

type AnyDoc = Record<string, any>;
const PREDICTION_PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const;
const PREDICTION_PAGE_SIZE_DEFAULT = 50;
const PASSWORD_MIN_LENGTH = 12;
const PASSWORD_SPECIAL_PATTERN = /[^A-Za-z0-9]/;
const DEMO_ORGANIZATION_NAME = "Projeto NoSQL";
const COMMON_WEAK_PASSWORDS = new Set([
  "password",
  "password1",
  "password123",
  "senha",
  "senha123",
  "admin",
  "admin123",
  "qwerty",
  "qwerty123",
  "secret",
  "secret123",
  "modeltrace"
]);

type Notice = {
  id: number;
  tone: "success" | "error" | "info";
  message: string;
};

type DocExample = {
  title: string;
  caption?: string;
  language?: string;
  code: string;
};

type DocTopic = {
  heading: string;
  paragraphs: string[];
  example?: DocExample;
};

type DocSection = {
  id: string;
  label: string;
  title: string;
  intro: string;
  topics: DocTopic[];
  related: string[];
};

type CommandItem = {
  id: string;
  label: string;
  detail: string;
  run: () => void | Promise<void>;
};

type Session = {
  access_token: string;
  refresh_token: string;
  user: AnyDoc;
};

function profileTerms(...values: Array<string | undefined>) {
  return values
    .flatMap((value) => String(value || "").toLowerCase().split(/[^a-z0-9]+/i))
    .filter((term) => term.length >= 4);
}

function apiAssetUrl(path?: string | null) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  const base = API_URL.replace(/\/api\/v1\/?$/, "");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

function cleanProtectedValue(value?: unknown) {
  const text = String(value || "").trim();
  return text && text !== "[protected]" ? text : "";
}

function predictionEntityName(prediction?: AnyDoc) {
  return (
    cleanProtectedValue(prediction?.entity?.display_name) ||
    cleanProtectedValue(prediction?.entity?.id) ||
    cleanProtectedValue(prediction?.entity?.id_masked) ||
    "Entidade"
  );
}

function predictionEntityId(prediction?: AnyDoc) {
  return cleanProtectedValue(prediction?.entity?.id) || cleanProtectedValue(prediction?.entity?.id_masked);
}

function passwordPolicyChecks(password: string, email: string, name: string, organizationName = DEMO_ORGANIZATION_NAME) {
  const normalized = password.toLowerCase();
  const terms = profileTerms(email.split("@")[0], name, organizationName);
  return [
    { id: "length", label: "Pelo menos 12 caracteres", passed: password.length >= PASSWORD_MIN_LENGTH },
    { id: "lower", label: "Letra minuscula", passed: /[a-z]/.test(password) },
    { id: "upper", label: "Letra maiuscula", passed: /[A-Z]/.test(password) },
    { id: "number", label: "Pelo menos um numero", passed: /\d/.test(password) },
    { id: "special", label: "Pelo menos um caractere especial", passed: PASSWORD_SPECIAL_PATTERN.test(password) },
    { id: "profile", label: "Nao usar nome, email ou organizacao", passed: !terms.some((term) => normalized.includes(term)) },
    { id: "common", label: "Nao usar senhas comuns", passed: !COMMON_WEAK_PASSWORDS.has(normalized) && new Set(normalized).size > 3 }
  ];
}

const navItems = [
  { id: "overview", label: "Overview", icon: Gauge },
  { id: "monitor", label: "Monitor", icon: Activity },
  { id: "compare", label: "Compare", icon: GitCompare },
  { id: "drift", label: "Drift", icon: Flame },
  { id: "lab", label: "DS Lab", icon: BarChart3 },
  { id: "predictions", label: "Predicoes", icon: Database },
  { id: "entities", label: "Entidades", icon: Search },
  { id: "operations", label: "Operacao", icon: AlertTriangle },
  { id: "cases", label: "Casos (SLA)", icon: Layers3 },
  { id: "usage", label: "Custo & Consumo", icon: CircleDollarSign },
  { id: "control", label: "Automacao", icon: Zap },
  { id: "workbench", label: "Workbench", icon: TerminalSquare },
  { id: "governance", label: "Governanca", icon: ShieldCheck },
  { id: "profile", label: "Perfil", icon: UserCircle },
  { id: "docs", label: "Docs", icon: BookOpen }
];

const docSections: DocSection[] = [
  {
    id: "start",
    label: "Comece aqui",
    title: "Primeiro uso",
    intro: "O ModelTrace organiza a operacao de modelos em producao: predicoes, feedback, alertas, diagnosticos, seguranca e auditoria no mesmo workspace.",
    topics: [
      {
        heading: "O que e o ModelTrace",
        paragraphs: [
          "O ModelTrace e uma camada de operacao para modelos de machine learning. Ele nao tenta substituir o treino, o notebook, o experimento ou a esteira de MLOps que a empresa ja usa. O papel dele e acompanhar o que acontece depois que um modelo comeca a tomar decisoes: quais entradas chegaram, qual score foi gerado, qual versao respondeu, qual decisao foi registrada, quem revisou e qual foi o resultado real observado depois.",
          "A plataforma foi pensada para funcionar como um produto de monitoramento e governanca. Um cientista de dados usa a area tecnica para analisar threshold, calibracao, slices, erros e drift. Uma equipe operacional usa a lista de predicoes, os casos e os alertas para priorizar acompanhamento. Uma area de auditoria usa o historico, as evidencias e as chaves de API para entender a origem de cada evento."
        ]
      },
      {
        heading: "Fluxo recomendado",
        paragraphs: [
          "O primeiro passo e escolher o projeto e o modelo na barra lateral. A partir disso, todas as telas passam a usar o mesmo contexto. O Overview mostra a situacao geral, Predicoes abre a lista operacional, DS Lab apresenta diagnosticos tecnicos, Operacao concentra casos e alertas, Workbench permite registrar uma predicao sem escrever JSON e Governanca mostra seguranca, auditoria e credenciais.",
          "Em um uso real, o servico do modelo envia predicoes para a API. Quando o desfecho real fica disponivel, outro sistema ou um analista registra feedback. Com esses dois movimentos, o ModelTrace consegue recalcular metricas online, indicar pontos de investigacao, criar alertas e manter uma trilha auditavel por entidade, modelo, versao e request_id."
        ]
      },
      {
        heading: "Quem usa cada area",
        paragraphs: [
          "Times de ciencia de dados tendem a trabalhar mais em DS Lab, Monitor e Decision inspector. Essas telas ajudam a entender comportamento do score, impacto de threshold, qualidade dos dados recebidos e segmentos em que o modelo erra mais. A equipe de negocio normalmente acompanha Overview, Operacao e Predicoes, porque ali estao os casos, volumes e prioridades de acompanhamento.",
          "A area de tecnologia usa API, Workbench e Governanca para integrar sistemas, controlar chaves, validar contratos e recuperar evidencias. Essa separacao evita que o usuario final precise manipular payloads tecnicos, sem impedir que integradores tenham exemplos claros de como consumir a API quando isso for necessario."
        ]
      }
    ],
    related: ["Overview", "Predicoes", "DS Lab", "Governanca"]
  },
  {
    id: "concepts",
    label: "Conceitos",
    title: "Conceitos principais",
    intro: "A plataforma usa uma estrutura documental flexivel para funcionar com classificacao binaria, multiclasse, regressao, ranking, anomalia e outros tipos de problema.",
    topics: [
      {
        heading: "Projeto",
        paragraphs: [
          "Um projeto representa um caso de uso real. Pode ser uma area da empresa, um produto, uma jornada do cliente, um processo de risco, uma fila operacional ou qualquer contexto em que um modelo gere decisoes. O projeto agrupa modelos, predicoes, alertas, auditoria e configuracoes de seguranca.",
          "Essa separacao permite que a mesma instalacao acompanhe modelos muito diferentes. Um projeto pode monitorar evasao de alunos, outro pode monitorar manutencao preditiva, outro pode acompanhar propensao de compra e outro pode registrar anomalias operacionais. O desenho documental evita amarrar a plataforma a um unico dominio."
        ]
      },
      {
        heading: "Modelo e versao",
        paragraphs: [
          "O modelo representa a familia de decisao. A versao representa uma entrega especifica dessa familia, com algoritmo, metadados, contrato de features, metricas de referencia, status operacional e data de criacao. Uma versao pode estar em draft, staging, production ou deprecated, permitindo comparar o que esta em uso com candidatos ou historicos.",
          "A versao e importante porque uma mesma entidade pode receber decisoes em momentos diferentes por modelos diferentes. Sem versionamento, a auditoria perde a capacidade de explicar exatamente qual logica estava ativa no momento da decisao."
        ]
      },
      {
        heading: "Predicao",
        paragraphs: [
          "A predicao e o documento central do ModelTrace. Ela guarda a entidade avaliada, o projeto, o modelo, a versao, as features recebidas, o score, o label, a decisao, a explicabilidade, o contexto tecnico e os metadados de auditoria. Esse documento e criado pela API, pelo Workbench ou por rotinas de carga.",
          "O formato e flexivel para aceitar diferentes problemas. Em classificacao binaria, prediction pode conter score e label. Em regressao, pode conter valor estimado, intervalo e erro esperado. Em ranking, pode conter posicao, conjunto candidato e criterios de ordenacao. Em anomalia, pode conter score de anomalia, severidade e regra de corte."
        ]
      },
      {
        heading: "Feedback, alerta e auditoria",
        paragraphs: [
          "Feedback e o resultado observado depois da decisao. Ele pode vir de um sistema externo, de uma revisao humana ou de uma carga posterior. Com feedback, a plataforma calcula acertos, erros, precision, recall, matriz de confusao, slices e outras metricas supervisionadas. Sem feedback, o sistema ainda monitora volume, score, dados e operacao, mas nao consegue afirmar performance real.",
          "Alertas combinam regras automaticas e configuracoes do projeto. Eles podem apontar baixo feedback, volume acionavel alto, deterioracao de score, drift, problema de qualidade da fonte, SLA ou qualquer regra generica cadastrada. Auditoria registra os eventos relevantes, incluindo criacao de credenciais, ingestao, feedback, replay, exportacoes e acoes de seguranca."
        ]
      }
    ],
    related: ["Modelo documental", "API", "Governanca"]
  },
  {
    id: "access-session",
    label: "Acesso e sessao",
    title: "Acesso, sessao e notificacoes",
    intro: "Esta secao explica tudo que acontece antes e depois do login: cadastro, entrada, sessao local, atualizacao, saida e retorno visual das acoes.",
    topics: [
      {
        heading: "Tela de entrada",
        paragraphs: [
          "Quando nao existe sessao ativa, o ModelTrace mostra a tela de acesso. O campo de email identifica o usuario, o campo de senha autentica a conta e o campo de nome e usado no cadastro inicial. O botao Entrar chama o endpoint de login e o botao Registrar cria o usuario e a organizacao local quando o ambiente ainda nao tem conta.",
          "Depois de um login bem-sucedido, a interface salva a sessao no navegador e carrega os projetos, a postura de seguranca e os primeiros dados do workspace. Se o backend responder que a credencial expirou, a sessao local e removida e o usuario volta para a tela de entrada."
        ],
        example: {
          title: "Login pela API",
          language: "bash",
          caption: "A interface faz esta chamada internamente quando o usuario clica em Entrar.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "diegohenrique.mail@gmail.com",
    "password": "D1eg0X@vi3rHUB"
  }'`
        }
      },
      {
        heading: "Atualizar e sair",
        paragraphs: [
          "O botao Atualizar da barra superior recarrega o workspace inteiro. Ele busca novamente projetos, modelos, dashboard, operacao, auditoria, postura de seguranca, API keys, versoes e, quando a tela exige, predicoes ou diagnosticos. Isso e util quando outro processo acabou de inserir dados ou quando uma acao terminou no backend.",
          "O botao Sair encerra a sessao no backend, remove a sessao armazenada no navegador e limpa o estado visual da aplicacao. A acao tambem mostra uma notificacao de sucesso para confirmar que o clique foi processado."
        ]
      },
      {
        heading: "Toasts e faixa de status",
        paragraphs: [
          "Toda acao importante atualiza a faixa de status e mostra um toast temporario. Toasts de informacao indicam processamento em andamento, toasts de sucesso confirmam conclusao e toasts de erro mostram a causa retornada pela API. Esse padrao aparece em Atualizar, Sair, Drift, Equidade, Feedback, What-if, Replay, exportacoes, chaves de API e migracao de seguranca.",
          "O toast nao substitui o resultado detalhado da acao. Quando uma analise retorna dados, a interface tambem mostra um bloco de resultado com o payload resumido. Assim o usuario sabe que a acao terminou e ainda consegue inspecionar o que o backend respondeu."
        ]
      }
    ],
    related: ["Navegacao", "Governanca", "API"]
  },
  {
    id: "navigation",
    label: "Navegacao",
    title: "Navegacao, contexto e comandos",
    intro: "O ModelTrace usa uma unica aplicacao com abas internas. A navegacao troca a area de trabalho sem mudar a URL e preserva o contexto de projeto e modelo selecionados.",
    topics: [
      {
        heading: "Sidebar",
        paragraphs: [
          "A barra lateral e o ponto de partida da operacao. As abas Overview, Monitor, DS Lab, Predicoes, Operacao, Workbench, Governanca e Docs definem qual area sera exibida no painel principal. Elas nao sao paginas separadas; cada clique muda o estado ativo da aplicacao e reaproveita os dados ja carregados quando possivel.",
          "O seletor Projeto muda todo o contexto operacional. Quando o projeto muda, a interface limpa predicoes antigas, reseta filtros dependentes, busca os modelos do projeto, carrega dashboard, operacao, auditoria, postura de seguranca e chaves de API. O seletor Modelo muda o contexto tecnico, recarregando versoes e diagnosticos."
        ]
      },
      {
        heading: "Topbar",
        paragraphs: [
          "A barra superior mostra dominio, ambiente, nome do projeto e descricao. Quando nao ha projeto selecionado, ela informa que o workspace esta sem contexto. A direita ficam Comandos, Atualizar e Sair. Esses botoes sao globais e funcionam independentemente da aba aberta.",
          "A faixa de status logo abaixo da topbar mostra o ultimo evento relevante, como sessao iniciada, workspace atualizado, CSV pronto ou erro de validacao. O email do usuario aparece no mesmo bloco para deixar claro qual conta esta operando o workspace."
        ]
      },
      {
        heading: "Command palette",
        paragraphs: [
          "O botao Comandos abre uma busca de acoes. Tambem e possivel abrir pelo atalho Ctrl+K ou Cmd+K. A palette permite abrir abas, atualizar o workspace, rodar drift, checar alertas, exportar predicoes, exportar auditoria e abrir pontos especificos da documentacao.",
          "Cada item da palette tem nome e descricao. Quando o usuario executa um comando, a janela fecha, a consulta e limpa e a acao correspondente roda exatamente como se o botao da tela tivesse sido clicado. Isso torna o produto mais rapido para usuarios frequentes."
        ]
      },
      {
        heading: "Dependencia de contexto",
        paragraphs: [
          "Algumas acoes dependem de projeto selecionado, como Checar alertas, Exportar predicoes e Criar API key. Outras dependem de modelo, como Drift, Equidade, Comparar versoes e DS Lab. Quando falta contexto, a interface nao tenta adivinhar; ela mostra uma mensagem de erro e pede que o usuario escolha projeto ou modelo.",
          "Esse comportamento evita registros inconsistentes. Uma predicao sem projeto, um drift sem modelo ou uma chave sem projeto gerariam dados impossiveis de auditar corretamente."
        ]
      }
    ],
    related: ["Acesso e sessao", "Overview", "Docs"]
  },
  {
    id: "overview",
    label: "Overview",
    title: "Overview",
    intro: "Resumo executivo do projeto selecionado. Ele mostra volume, saude operacional, feedback, score medio, matriz de confusao e prioridades.",
    topics: [
      {
        heading: "Leitura dos indicadores",
        paragraphs: [
          "O Overview foi desenhado para responder rapidamente se o modelo esta operando bem. Os indicadores mostram volume de predicoes, percentual de decisoes de alto risco, cobertura de feedback, score medio, alertas ativos e saude operacional. Cada indicador tem relacao com uma area da plataforma, entao a leitura executiva pode virar investigacao com poucos cliques.",
          "Quando um card e clicavel, ele leva para a lista mais adequada. Um volume de alto risco pode abrir Predicoes filtradas, um alerta pode levar para Operacao, e um problema de feedback pode direcionar a investigacao para Decision inspector ou DS Lab."
        ]
      },
      {
        heading: "Saude operacional",
        paragraphs: [
          "A saude operacional nao e uma medida pura de acuracia. Ela combina sinais que indicam se o modelo esta pronto para ser usado com confianca no processo. Feedback baixo reduz a nota porque existe pouca evidencia real. Alertas ativos reduzem a nota porque existe algum ponto pendente. Volume acionavel muito alto tambem pesa, porque pode gerar fila maior do que a equipe consegue acompanhar.",
          "Para melhorar esse score, a empresa precisa aumentar a cobertura de feedback, resolver alertas, ajustar threshold quando o workload estiver alto, corrigir problemas de dados e reduzir inconsistencias entre versoes. O objetivo nao e maquiar o numero, e aproximar operacao, dados e governanca de uma rotina confiavel."
        ]
      },
      {
        heading: "Graficos e matriz",
        paragraphs: [
          "A distribuicao de score mostra como as decisoes estao concentradas. Uma concentracao estranha em faixas muito baixas, muito altas ou em um unico ponto pode indicar mudanca na fonte de dados, bug de feature, mudanca de regra ou comportamento natural do dominio. A matriz de confusao aparece quando existe feedback suficiente para classificar acertos e erros.",
          "Esses graficos devem ser lidos junto com a janela temporal. Uma queda em um dia isolado pode ser apenas variacao de volume. Uma queda sustentada, principalmente acompanhada de drift ou reducao de feedback, merece investigacao tecnica."
        ]
      }
    ],
    related: ["Predicoes", "Operacao", "DS Lab"]
  },
  {
    id: "monitor",
    label: "Monitor",
    title: "Monitor",
    intro: "Tela de acompanhamento tecnico-operacional para versoes do modelo, drift, comparacao de versoes, equidade e exportacao.",
    topics: [
      {
        heading: "Uso da tela",
        paragraphs: [
          "O Monitor mostra as versoes cadastradas para o modelo selecionado e permite executar checagens sob demanda. O botao Atualizar recarrega o contexto do projeto, sincronizando versoes, metricas e indicadores recentes. Essa tela e mais tecnica do que o Overview, porque ajuda a entender diferencas entre versoes e riscos antes de promover uma nova entrega.",
          "Os botoes de acao retornam mensagens de sucesso ou erro para evitar a sensacao de que a interface nao respondeu. Quando uma analise demora, o estado de carregamento deixa claro que o backend esta processando dados."
        ]
      },
      {
        heading: "Drift",
        paragraphs: [
          "A analise de drift compara distribuicoes recentes com uma referencia. O ModelTrace pode avaliar score, features numericas, features categoricas e estabilidade de volume. Em producao, a regra de drift deve considerar o dominio do modelo, porque algumas variacoes sao esperadas e outras indicam quebra da fonte de dados.",
          "Um alerta de drift nao significa automaticamente que o modelo esta errado. Ele significa que o ambiente mudou o suficiente para justificar investigacao. A conclusao deve combinar drift, feedback, impacto operacional e conhecimento do processo."
        ]
      },
      {
        heading: "Comparacao e equidade",
        paragraphs: [
          "A comparacao de versoes agrupa predicoes por model_version e mostra diferencas de comportamento. Isso ajuda a avaliar se uma versao candidata mudou o volume acionavel, alterou a media de score ou concentrou decisoes em determinados segmentos.",
          "A analise de equidade usa uma feature escolhida para comparar desempenho entre grupos. Ela e generica, entao pode ser aplicada a idade, regiao, produto, turma, unidade, canal, tipo de cliente ou qualquer atributo presente nas features. A interpretacao exige cuidado, principalmente quando a feature e sensivel ou pode representar proxy de atributo protegido."
        ]
      }
    ],
    related: ["DS Lab", "Governanca", "API"]
  },
  {
    id: "lab",
    label: "DS Lab",
    title: "DS Lab",
    intro: "Ambiente para cientistas de dados acompanharem threshold, calibracao, cobertura de features, erros, slices e prioridades de analise.",
    topics: [
      {
        heading: "O que analisar",
        paragraphs: [
          "O DS Lab concentra as analises que um cientista de dados precisa depois que o modelo esta em uso. A tela mostra curva de threshold, simulador, calibracao, ECE, qualidade da fonte, contrato de features, inteligencia de features, slices monitorados e classes de erro. A ideia e transformar predicoes de producao em material de diagnostico.",
          "Essa area nao treina o modelo e nao substitui ferramentas como MLflow, DVC ou notebooks de experimentacao. Ela complementa essas ferramentas com sinais online, feedback real e rastreabilidade operacional."
        ]
      },
      {
        heading: "Threshold",
        paragraphs: [
          "O threshold define o ponto em que um score passa a ser tratado como decisao acionavel. Em classificacao binaria, reduzir o threshold costuma aumentar recall e workload, enquanto elevar o threshold costuma aumentar precision e reduzir volume. O grafico mostra como F2, recall e precision mudam em diferentes pontos.",
          "O simulador move uma linha vertical sobre a curva para mostrar o ponto selecionado. Quando o valor muda, os indicadores abaixo do slider acompanham o novo corte. Isso permite discutir trade-offs sem alterar a configuracao oficial do modelo."
        ]
      },
      {
        heading: "Calibracao, slices e contrato",
        paragraphs: [
          "Calibracao mostra se scores previstos se comportam como probabilidades confiaveis. Um score 0.80 deveria representar aproximadamente 80% de ocorrencia no grupo correspondente. Quando isso nao acontece, o modelo pode continuar ordenando bem, mas a interpretacao probabilistica fica fraca.",
          "Slices monitorados agrupam entidades por atributos importantes, como periodo, produto, unidade ou segmento. O contrato de features compara o que a versao espera com o que chega nas predicoes. Essa parte e essencial para encontrar colunas ausentes, tipos incorretos e valores fora do padrao."
        ]
      }
    ],
    related: ["Predicoes", "Feedback", "What-if"]
  },
  {
    id: "predictions",
    label: "Predicoes",
    title: "Predicoes",
    intro: "Lista operacional das decisoes registradas. A tela usa paginacao no servidor para manter a interface responsiva em bases grandes.",
    topics: [
      {
        heading: "Tabela operacional",
        paragraphs: [
          "Predicoes e a tela usada para consultar decisoes registradas. Cada linha representa uma avaliacao feita por uma versao de modelo para uma entidade. A tabela mostra identificador, score, label, versao, janela, data e status de feedback, permitindo encontrar rapidamente casos que precisam de revisao.",
          "Ao clicar em uma linha, o Decision inspector abre a decisao completa. O usuario final nao precisa copiar JSON nem abrir banco de dados para entender o caso; a interface mostra os principais campos de forma navegavel e deixa o payload tecnico em uma area separada."
        ]
      },
      {
        heading: "Filtros e paginacao",
        paragraphs: [
          "A busca permite localizar entidades, labels, versoes e valores relevantes. Os filtros de label, janela temporal e feedback reduzem a tabela para o conjunto de interesse. A paginacao acontece no servidor, entao a tela continua rapida mesmo quando o projeto tem milhares de predicoes.",
          "Quando a interface informa que uma pagina carregou parte das predicoes filtradas, isso significa que a base completa ficou no backend e apenas o recorte necessario veio para o navegador. Esse comportamento evita travamentos em computadores comuns e melhora a experiencia em datasets grandes."
        ],
        example: {
          title: "Recuperar predicoes pela API",
          language: "bash",
          caption: "Use este formato quando um sistema externo precisar consultar predicoes filtradas sem abrir a interface.",
          code: `curl "http://127.0.0.1:8001/api/v1/predictions?project_id=proj_123&limit=250&offset=0&feedback=missing" \\
  -H "Authorization: Bearer mt_live_xxx"`
        }
      },
      {
        heading: "Exportacao",
        paragraphs: [
          "A exportacao serve para investigacoes offline, auditoria ou compartilhamento controlado com outras areas. Em uma instalacao corporativa, exportacoes grandes devem ser tratadas por jobs assincronos, com controle de acesso, tempo de expiracao e registro de auditoria.",
          "Dados sensiveis devem ser mascarados ou minimizados de acordo com a politica da empresa. A plataforma ja separa campos tecnicos, payload e evidencias para facilitar essa governanca."
        ]
      }
    ],
    related: ["Decision inspector", "Workbench", "Governanca"]
  },
  {
    id: "inspector",
    label: "Decision inspector",
    title: "Decision inspector",
    intro: "Painel lateral para investigar a decisao selecionada: score, feedback, what-if, replay, explicabilidade e detalhes tecnicos.",
    topics: [
      {
        heading: "Analise da decisao",
        paragraphs: [
          "O Decision inspector e aberto quando uma predicao e selecionada. Ele mostra a entidade, o score, a classe, a janela, a versao do modelo, os principais fatores de explicabilidade e os detalhes tecnicos. O objetivo e permitir que alguem investigue uma decisao sem sair da tela de trabalho.",
          "O painel tambem mostra uma barra visual de score e campos de contexto. Em bases com muitas features, a area interna do inspector precisa rolar independentemente da tabela principal, porque a predicao pode ter dezenas de atributos e ainda assim a lista de predicoes deve continuar acessivel."
        ]
      },
      {
        heading: "Feedback",
        paragraphs: [
          "Feedback registra o resultado observado depois da decisao. Em um modelo de risco, por exemplo, o feedback informa se o evento de risco realmente aconteceu. Em um modelo de regressao, pode registrar o valor real. Em um problema de classificacao multiclasse, pode registrar a classe correta. Esse dado transforma uma predicao em evidencia de performance.",
          "O feedback pode ser manual, vindo de revisao humana, ou automatico, vindo de outro sistema. Depois de salvo, ele passa a alimentar metricas, matriz de confusao, slices, alertas e historico da entidade."
        ],
        example: {
          title: "Registrar feedback por API",
          language: "bash",
          caption: "API keys precisam do escopo feedback:write para gravar feedback sem usar a sessao do front-end.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/predictions/pred_123/feedback" \\
  -H "Authorization: Bearer mt_live_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "observed_value": 1,
    "source": "manual_review",
    "notes": "Desfecho confirmado pelo sistema operacional."
  }'`
        }
      },
      {
        heading: "What-if",
        paragraphs: [
          "What-if simula como o score poderia mudar se algumas features fossem alteradas. A simulacao e local quando nao existe um endpoint real de scoring conectado. Nesse modo, o sistema estima o impacto usando os sinais disponiveis na propria predicao, como features numericas, explicabilidade e score original.",
          "A escolha dos valores nao e feita sozinha pela plataforma. O usuario informa os campos que deseja testar, ou usa cenarios rapidos como otimista e conservador quando eles estiverem disponiveis. Em uma integracao completa, o What-if pode chamar o servico real do modelo e retornar a nova predicao calculada pelo mesmo pipeline de producao."
        ],
        example: {
          title: "Simular alteracao de feature",
          language: "bash",
          caption: "Este exemplo altera duas features e pede uma estimativa para a predicao selecionada.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/predictions/pred_123/whatif" \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "hypothetical_features": {
      "feature_a": 0.82,
      "feature_b": "segmento_alvo"
    }
  }'`
        }
      },
      {
        heading: "Replay e exportacao",
        paragraphs: [
          "Replay cria uma nova leitura da mesma decisao sem apagar a predicao original. Ele serve para comparar versoes, registrar uma revisao posterior ou guardar evidencia de que uma decisao foi reprocessada com outro contexto. A predicao original continua preservada para auditoria.",
          "Exportar gera um arquivo com os dados auditaveis da predicao. Esse recurso e util quando uma area precisa anexar evidencia a um chamado, explicar uma decisao para auditoria ou transferir um caso para investigacao tecnica."
        ]
      }
    ],
    related: ["Predicoes", "Feedback", "DS Lab"]
  },
  {
    id: "feedback",
    label: "Feedback",
    title: "Feedback e desfecho real",
    intro: "Feedback e o mecanismo que transforma uma predicao registrada em evidencia de performance real. Sem feedback, a plataforma monitora operacao; com feedback, ela mede acerto, erro e qualidade supervisionada.",
    topics: [
      {
        heading: "Quando usar",
        paragraphs: [
          "Use Feedback quando a empresa ja sabe o resultado observado da decisao. Em risco, o resultado pode ser evento ocorrido ou nao ocorrido. Em churn, pode ser cliente saiu ou permaneceu. Em manutencao, pode ser falha confirmada ou ausencia de falha. Em regressao, pode ser o valor real medido. O importante e que o feedback represente uma fonte confiavel, nao uma opiniao sem evidencia.",
          "No Decision inspector, o botao Feedback abre um painel com tres escolhas: Positivo, Negativo e Inconclusivo. Positivo grava observed_label igual ao label positivo do modelo e observed_value igual a 1. Negativo grava o label negativo e observed_value igual a 0. Inconclusivo registra que ainda nao existe desfecho confiavel e evita contaminar as metricas supervisionadas."
        ]
      },
      {
        heading: "Origem e nota",
        paragraphs: [
          "O campo Origem identifica de onde veio o feedback. Pode ser manual_review, sistema_operacional, carga_batch, planilha_validada, CRM, ERP ou qualquer nome que faca sentido para a empresa. Esse valor aparece na auditoria e ajuda a separar feedback humano, feedback automatico e feedback importado.",
          "O campo Nota e opcional. Ele serve para registrar contexto curto, como motivo da revisao, regra usada, evidencia externa ou observacao do analista. A nota deve ser objetiva, porque pode aparecer em trilhas de auditoria e exportacoes."
        ]
      },
      {
        heading: "Classificacao automatica",
        paragraphs: [
          "Depois que o feedback e salvo, o backend compara a predicao original com o resultado observado. Se o modelo acionou e o evento ocorreu, o caso vira TP. Se acionou e o evento nao ocorreu, vira FP. Se nao acionou e o evento nao ocorreu, vira TN. Se nao acionou e o evento ocorreu, vira FN. Se o resultado e inconclusivo, a classificacao fica inconclusive.",
          "Essa classificacao alimenta matriz de confusao, precision, recall, F2, calibracao, diagnosticos por segmento, falsos positivos, falsos negativos e saude operacional. A interface atualiza predicoes, dashboard e DS Lab depois de salvar o feedback."
        ],
        example: {
          title: "Feedback positivo por API",
          language: "bash",
          caption: "Sistemas externos podem enviar feedback usando API key com escopo feedback:write.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/predictions/pred_123/feedback" \\
  -H "Authorization: Bearer mt_live_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "observed_label": "alto_risco",
    "observed_value": 1,
    "source": "sistema_operacional",
    "notes": "Evento confirmado na base de desfechos."
  }'`
        }
      },
      {
        heading: "Efeito no produto",
        paragraphs: [
          "Ao salvar feedback, a predicao deixa de aparecer como pendente quando o filtro de feedback esta ativo. O KPI de Feedback no Overview pode subir, a matriz de confusao pode mudar e o DS Lab ganha mais dados para threshold e calibracao. Se o feedback indicar erro critico em volume relevante, regras de alerta podem apontar degradacao.",
          "Feedback incorreto prejudica o produto. Se a fonte de desfecho estiver atrasada, duplicada ou inconsistente, e melhor marcar como inconclusivo ou aguardar uma carga confiavel. A plataforma foi desenhada para aceitar feedback tardio sem quebrar o historico."
        ]
      }
    ],
    related: ["Decision inspector", "Predicoes", "DS Lab"]
  },
  {
    id: "whatif",
    label: "What-if",
    title: "What-if",
    intro: "What-if e a simulacao local de uma decisao. Ele permite alterar features de uma predicao selecionada e estimar como o score poderia mudar antes de executar um novo scoring real.",
    topics: [
      {
        heading: "O que acontece quando abre",
        paragraphs: [
          "O What-if fica dentro do Decision inspector. Primeiro o usuario seleciona uma predicao na tabela. Depois clica em What-if. A interface pega ate dez features da predicao selecionada, converte os valores para campos editaveis e monta o cenario atual. Features numericas viram inputs numericos, features booleanas viram selects true/false e outros valores viram campos de texto.",
          "O sistema nao escolhe os valores finais sozinho. Ele apenas preenche o estado inicial com os valores atuais da predicao. A partir dai, o usuario altera manualmente o que deseja testar ou usa um dos presets para criar uma variacao rapida."
        ]
      },
      {
        heading: "Presets Otimista, Conservador e Reset",
        paragraphs: [
          "O preset Reset volta os campos para os valores atuais da predicao. Ele deve ser usado quando o usuario quer descartar uma simulacao e recomecar. O preset Otimista reduz sinais interpretados como risco e aumenta sinais interpretados como qualidade quando os nomes das features permitem essa inferencia. O preset Conservador faz o oposto, aumentando sinais de risco e reduzindo sinais de qualidade.",
          "Essa inferencia e baseada em nomes comuns de features. Termos como attendance, frequencia, grade, nota, credit, income, score, rate e coverage sao tratados como sinais positivos ou de qualidade. Termos como failed, reprov, debt, delay, risk, absent, missing, error, cost e backlog sao tratados como sinais de risco. Quando a feature nao se encaixa nesses padroes, o valor muda pouco ou permanece igual."
        ]
      },
      {
        heading: "Como a simulacao e enviada",
        paragraphs: [
          "Quando o usuario clica em Simular cenario, a interface converte cada campo editado para o tipo mais adequado. Se a feature original era numero, o valor digitado vira numero. Se era booleana, true e false viram booleanos reais. Se o texto parece numero, ele tambem pode ser convertido para numero. Depois o payload e enviado para o endpoint de what-if.",
          "O backend recebe hypothetical_features e chama o estimador local. Esse estimador compara o cenario hipotetico com a predicao original e retorna score original, score estimado, delta, possivel troca de decisao e detalhes usados na estimativa. O resultado aparece no bloco de resultado abaixo das acoes do inspector."
        ],
        example: {
          title: "Simular um cenario",
          language: "bash",
          caption: "O endpoint correto e /whatif. A chave hypothetical_features contem apenas os campos que serao simulados.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/predictions/pred_123/whatif" \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "hypothetical_features": {
      "frequencia": 0.92,
      "reprovacoes": 0,
      "segmento": "regular"
    }
  }'`
        }
      },
      {
        heading: "O que o What-if nao promete",
        paragraphs: [
          "O What-if atual e uma estimativa local quando nao existe endpoint real de scoring conectado. Ele e util para investigacao, explicacao e conversa com negocio, mas nao deve ser tratado como decisao oficial se a empresa exige reprocessamento pelo pipeline original do modelo.",
          "Em um produto corporativo completo, o What-if pode ser conectado ao servico real do modelo. Nesse caso, a tela deveria mostrar claramente se o resultado foi estimado pelo ModelTrace ou executado pelo modelo real. Essa distincao e importante para auditoria e para evitar que uma simulacao seja confundida com uma nova predicao oficial."
        ]
      },
      {
        heading: "Quando usar na pratica",
        paragraphs: [
          "Use What-if para investigar sensibilidade de uma decisao individual. Um cientista de dados pode testar se pequenas mudancas em features relevantes alteram o score. Um analista pode entender por que um caso esta perto do threshold. Um gestor pode visualizar o impacto de regras de negocio sem alterar a predicao original.",
          "O What-if nao grava uma nova predicao automaticamente. Ele mostra uma estimativa. Se a empresa quiser guardar o experimento como evidencia, o caminho correto e usar Replay ou uma futura funcionalidade de cenarios salvos."
        ]
      }
    ],
    related: ["Decision inspector", "Replay e exportacoes", "DS Lab"]
  },
  {
    id: "replay-export",
    label: "Replay e exportacoes",
    title: "Replay, exportacoes e evidencias",
    intro: "Replay e exportacao sao recursos de evidencia. Eles ajudam a comparar leituras da mesma decisao e a retirar dados auditaveis da plataforma com controle.",
    topics: [
      {
        heading: "Replay",
        paragraphs: [
          "Replay cria um novo documento relacionado a uma predicao existente. Ele nao apaga a predicao original, nao substitui o score original e nao altera o feedback ja registrado. O objetivo e preservar uma leitura alternativa: outra versao, outro score, outro label ou uma reexecucao controlada.",
          "Na interface atual, o botao Replay usa a versao de producao como alvo quando ela existe e gera um replay_score reduzindo o score atual em 0.12, limitado entre 0 e 1. O backend calcula replay_label com base no threshold e registra se a decisao mudou. O resultado fica no bloco de acao como evidencia da comparacao."
        ],
        example: {
          title: "Criar replay por API",
          language: "bash",
          caption: "Este payload cria uma leitura alternativa sem editar a predicao original.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/predictions/pred_123/replay" \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "target_version": "v2.0.0",
    "replay_score": 0.42,
    "replay_label": "baixo_risco"
  }'`
        }
      },
      {
        heading: "Exportar predicoes",
        paragraphs: [
          "O botao Exportar aparece no Monitor e no Decision inspector. Ele chama o endpoint de exportacoes com filtros do projeto atual, formato CSV e inclusao de features e explicacoes. O backend cria um registro em exports, gera o arquivo e retorna metadados como quantidade de registros.",
          "Exportacoes sao uteis para auditoria, analise offline, envio controlado para outra area ou montagem de relatorio. Em dados sensiveis, a empresa deve aplicar minimizacao, redacao e expiracao do arquivo. O produto ja registra o evento para trilha de auditoria."
        ]
      },
      {
        heading: "Exportar auditoria",
        paragraphs: [
          "Na aba Governanca, o botao Exportar evidencias gera um JSON local com os eventos filtrados do audit trail. O arquivo inclui data da exportacao, projeto, consulta usada, quantidade de eventos e a lista de eventos. Ele serve para anexar evidencias em revisoes, trabalhos academicos, incidentes ou auditorias internas.",
          "A exportacao de auditoria acontece no navegador a partir dos eventos ja carregados. Quando o filtro tem mais eventos do que a tela mostra, a interface indica que existem eventos adicionais no filtro e orienta o uso da exportacao para recuperar o conjunto completo carregado."
        ]
      },
      {
        heading: "Pacote do DS Lab",
        paragraphs: [
          "O botao Exportar pacote do DS Lab baixa um JSON com os diagnosticos do modelo selecionado. Esse pacote contem resumo, curva de threshold, calibracao, cobertura de features, importancia, diagnosticos por segmento, analise de erro e recomendacoes quando disponiveis.",
          "Esse arquivo e voltado ao cientista de dados. Ele permite levar os diagnosticos para notebook, anexo de relatorio ou investigacao offline sem precisar extrair manualmente cada grafico."
        ]
      }
    ],
    related: ["Decision inspector", "Governanca", "API"]
  },
  {
    id: "entities",
    label: "Entidades",
    title: "Entidades e timeline",
    intro: "A tela Entidades consolida o historico de uma pessoa, aluno, cliente, ativo, maquina ou empresa em uma linha do tempo operacional.",
    topics: [
      {
        heading: "Para que serve",
        paragraphs: [
          "A tela Entidades evita que a investigacao fique espalhada entre tabela, alerta, caso e replay. O usuario pesquisa uma entidade e ve predicoes, casos operacionais, replays e notas relacionadas ao mesmo identificador.",
          "Isso ajuda a responder perguntas frequentes de produto: quantas vezes essa entidade foi avaliada, se o score mudou ao longo do tempo, se existe caso aberto, se houve replay e qual contexto humano foi anotado pela equipe."
        ]
      },
      {
        heading: "Como pesquisar",
        paragraphs: [
          "Digite ID, matricula, nome exibido ou outro identificador autorizado no campo de busca e clique em Pesquisar. Se uma predicao estiver aberta no Decision inspector, o botao Usar entidade selecionada copia o identificador dela para a busca.",
          "O backend tenta localizar a entidade pelo indice cego e, quando necessario, faz fallback em campos exibiveis autorizados. A resposta traz listas separadas e uma lista consolidada em events para alimentar a timeline."
        ],
        example: {
          title: "Buscar timeline",
          language: "bash",
          caption: "A mesma rota serve para qualquer dominio porque o parametro q representa o identificador da entidade.",
          code: `curl "http://127.0.0.1:8001/api/v1/projects/proj_123/entity-timeline?q=student_001" \\
  -H "Authorization: Bearer eyJ..."`
        }
      },
      {
        heading: "Notas de entidade",
        paragraphs: [
          "Notas sao observacoes manuais vinculadas a entidade, nao a uma predicao especifica. Elas servem para registrar contexto operacional posterior, como contato realizado, evidencia revisada, decisao humana ou motivo de prioridade.",
          "A nota fica em entity_notes e nao altera documentos antigos. Isso preserva a predicao como evidencia tecnica original e separa comentario humano do payload gerado pelo modelo."
        ],
        example: {
          title: "Salvar nota",
          language: "bash",
          caption: "Tags sao opcionais e podem ser usadas para organizar investigacoes.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/projects/proj_123/entity-notes" \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "entity_id": "student_001",
    "body": "Contato validado pela equipe operacional.",
    "tags": ["revisado", "prioritario"]
  }'`
        }
      }
    ],
    related: ["Predicoes", "Decision inspector", "Operacao"]
  },
  {
    id: "automation",
    label: "Automacao",
    title: "Automacao operacional",
    intro: "A aba Automacao concentra jobs, notificacoes, data contracts, views salvas e regras de alerta para o uso diario do produto.",
    topics: [
      {
        heading: "Jobs",
        paragraphs: [
          "Jobs executam tarefas operacionais sem prender a navegacao do usuario. A interface permite criar jobs para dashboard, drift, diagnosticos, metricas e alertas. A lista mostra status, tipo, projeto, resultado, erro e datas.",
          "No ambiente local, os jobs usam BackgroundTasks do FastAPI. O contrato ja separa params, result, status e timestamps, entao uma implantacao corporativa pode migrar para fila distribuida com workers sem mudar a experiencia da interface."
        ],
        example: {
          title: "Criar job de drift",
          language: "bash",
          caption: "Tipos aceitos: alerts, drift, metrics, diagnostics e dashboard.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/jobs" \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "project_id": "proj_123",
    "type": "drift",
    "params": { "window_days": 30 }
  }'`
        }
      },
      {
        heading: "Notificacoes",
        paragraphs: [
          "Notificacoes persistidas sao diferentes de toasts. Toast e uma resposta visual temporaria. Notificacao fica no banco, aparece no contador da topbar e pode ser marcada como lida depois.",
          "Alertas e jobs criam notificacoes automaticamente. A aba Automacao lista as mensagens e permite marcar tudo como lido para limpar o contador."
        ]
      },
      {
        heading: "Data contracts",
        paragraphs: [
          "Data contracts validam se as features recebidas por uma predicao respeitam o esperado pelo modelo. O modo accept registra divergencias sem bloquear. O modo warn aceita e destaca o problema. O modo block recusa payloads com violacoes bloqueantes.",
          "O contrato usa expected_features do modelo. Quanto mais completo estiver o schema, melhor a validacao de obrigatoriedade, tipo, nulidade, ranges numericos e valores permitidos."
        ],
        example: {
          title: "Ativar modo bloqueante",
          language: "bash",
          caption: "Depois disso, predicoes com violacoes criticas retornam 422.",
          code: `curl -X PATCH "http://127.0.0.1:8001/api/v1/projects/proj_123/data-contract" \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{"mode": "block"}'`
        }
      },
      {
        heading: "Views salvas",
        paragraphs: [
          "Views salvas guardam filtros e colunas para consultas recorrentes. O usuario pode salvar, por exemplo, alto risco sem feedback, predicoes de uma versao, casos de uma janela ou qualquer recorte operacional usado com frequencia.",
          "A view nao copia dados. Ela guarda a configuracao de leitura e reaplica filtros no front-end, recarregando predicoes quando necessario."
        ]
      }
    ],
    related: ["Operacao", "Alertas", "API"]
  },
  {
    id: "operations",
    label: "Operacao",
    title: "Operacao",
    intro: "Centro para acompanhar casos, alertas, incidentes, coortes, qualidade da fonte e avaliacoes de modelos.",
    topics: [
      {
        heading: "Fila operacional",
        paragraphs: [
          "A aba Operacao organiza o trabalho diario de acompanhamento. Ela mostra casos abertos, casos criticos, alertas ativos, coortes monitoradas, qualidade da fonte, incidentes e avaliacoes entre modelos. A tela existe para transformar sinais tecnicos em trabalho acionavel.",
          "Um caso pode representar uma predicao de alto risco, uma decisao sem feedback, uma entidade prioritaria ou qualquer regra operacional cadastrada. Em uma empresa, essa fila pode se conectar a ferramentas como Jira, ServiceNow, Slack, Teams ou sistemas internos."
        ]
      },
      {
        heading: "Alertas",
        paragraphs: [
          "Alertas podem ser automaticos ou cadastrados por regra. Regras automaticas verificam sinais genericos, como feedback baixo, volume acionavel elevado, drift, baixa qualidade da fonte e problemas de contrato de features. Regras cadastradas podem refletir limites especificos do projeto, como SLA, volume por coorte, queda de recall ou instabilidade em uma versao.",
          "Clicar em um alerta deve levar para a area onde a investigacao acontece. Um alerta de feedback aponta para predicoes sem desfecho. Um alerta de drift aponta para diagnosticos. Um alerta de seguranca aponta para Governanca. Esse comportamento reduz o tempo entre perceber o problema e abrir a tela correta."
        ]
      },
      {
        heading: "Coortes, incidentes e qualidade",
        paragraphs: [
          "Coortes monitoradas agrupam entidades que precisam de acompanhamento separado. Isso ajuda a entender se o modelo funciona de forma diferente em turmas, regioes, produtos, canais, periodos ou qualquer outro segmento relevante.",
          "Incidentes registram problemas que exigem tratamento formal. Qualidade da fonte mostra linhas, entidades, colunas e sinais de integridade dos dados recebidos. Juntas, essas informacoes ajudam a separar erro do modelo, erro de dado e erro de processo."
        ]
      }
    ],
    related: ["Alertas", "Governanca", "Overview"]
  },
  {
    id: "alerts",
    label: "Alertas",
    title: "Alertas e regras operacionais",
    intro: "Alertas transformam metricas, qualidade de dados e risco operacional em sinais acionaveis. Eles podem vir de regras cadastradas ou de regras padrao avaliadas pelo backend.",
    topics: [
      {
        heading: "Checar alertas",
        paragraphs: [
          "O botao Checar alertas fica na aba Operacao e tambem aparece na command palette. Quando acionado, ele chama o backend com o projeto atual e include_defaults=true. Isso faz o motor avaliar regras cadastradas e regras padrao geradas para o projeto e seus modelos.",
          "Depois da checagem, a interface recarrega Operacao e Dashboard. Se novos alertas foram criados, o contador de alertas ativos muda no Overview e na Operacao. O toast informa quantos alertas novos surgiram."
        ],
        example: {
          title: "Executar regras de alerta",
          language: "bash",
          caption: "A interface envia esta chamada quando o usuario clica em Checar alertas.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/alerts/run-checks?project_id=proj_123&include_defaults=true" \\
  -H "Authorization: Bearer eyJ..."`
        }
      },
      {
        heading: "Tipos de alerta",
        paragraphs: [
          "O motor suporta regras como performance_threshold, feedback_rate_low, volume_drop, prediction_drift, data_drift, missing_features e deprecated_version_active. Essas regras cobrem desempenho observado, cobertura de feedback, queda de volume, instabilidade de score, mudanca nos dados, quebra de contrato de features e uso indevido de versao antiga.",
          "Regras padrao ajudam qualquer projeto, mesmo quando ninguem cadastrou uma regra especifica. Regras customizadas permitem adaptar limites ao dominio. Um projeto de credito pode ter limites diferentes de um projeto de manutencao ou educacao."
        ]
      },
      {
        heading: "Clique em um alerta",
        paragraphs: [
          "Cada alerta ativo aparece como um item clicavel. O clique nao resolve o alerta; ele leva o usuario para o ponto onde a investigacao deve acontecer. Alertas de missing_features apontam para Qualidade da fonte. Alertas de backlog operacional apontam para Fila operacional. Os demais ficam na area de Alertas ativos.",
          "Esse comportamento cria um caminho de investigacao. O alerta mostra o problema, o destino mostra os dados relacionados e as outras abas ajudam a aprofundar: Predicoes para casos individuais, DS Lab para diagnostico tecnico e Governanca para auditoria."
        ]
      },
      {
        heading: "Severidade e ciclo de vida",
        paragraphs: [
          "A severidade indica prioridade visual. Medium, high e critical devem ser lidos como urgencia operacional, nao como prova isolada de falha do modelo. Um alerta critico merece investigacao mais rapida, mas a conclusao depende de dados, feedback e contexto.",
          "O backend ja possui estrutura para acknowledge e resolucao de alertas, mas a tela atual prioriza listagem, checagem e navegação para investigacao. Em uma versao corporativa, o fluxo natural seria incluir responsavel, SLA, comentario, snooze, incidente vinculado e timeline de transicoes."
        ]
      }
    ],
    related: ["Operacao", "DS Lab", "Governanca"]
  },
  {
    id: "workbench",
    label: "Workbench",
    title: "Workbench",
    intro: "Entrada guiada para registrar predicoes de teste ou simulacoes operacionais sem obrigar o usuario final a escrever JSON.",
    topics: [
      {
        heading: "Uso pela interface",
        paragraphs: [
          "O Workbench permite registrar uma predicao de teste sem escrever JSON. O usuario informa entidade, nome de exibicao, versao, janela, score e features. O formulario usa o contrato do modelo selecionado para sugerir campos e reduzir erros de preenchimento.",
          "Esse recurso e util para validacao, demonstracao, carga pequena e simulacao controlada. Em producao, a maior parte das predicoes deve chegar pela API ou por pipeline de dados, porque o volume operacional normalmente e maior do que uma entrada manual."
        ]
      },
      {
        heading: "Validacao de contrato",
        paragraphs: [
          "O contrato de features define quais campos o modelo espera, quais sao obrigatorios, quais tipos sao aceitos e quais valores costumam aparecer. Quando uma feature obrigatoria falta, o Workbench mostra erro antes de enviar. Isso evita criar predicoes quebradas e ajuda integradores a corrigir payloads.",
          "O usuario final nao precisa ver o JSON para trabalhar, mas o exemplo tecnico continua disponivel para quem integra sistemas. Assim a mesma tela atende operacao e engenharia sem misturar responsabilidades."
        ],
        example: {
          title: "Payload equivalente ao formulario",
          language: "json",
          caption: "Este e o formato que o Workbench envia para a API depois da validacao.",
          code: `{
  "project_id": "proj_123",
  "model_id": "model_123",
  "model_version": "v1.0.0",
  "entity_id": "cliente_001",
  "entity_display": "Cliente 001",
  "features": {
    "idade": 42,
    "segmento": "premium",
    "valor_medio": 318.5
  },
  "prediction": {
    "score": 0.78,
    "label": "alto_risco"
  },
  "request_id": "req_2026_0001"
}`
        }
      }
    ],
    related: ["API", "Predicoes", "Governanca"]
  },
  {
    id: "governance",
    label: "Governanca",
    title: "Governanca e seguranca",
    intro: "Area para seguranca, auditoria, chaves de API, evidencias e mapa documental.",
    topics: [
      {
        heading: "Para que serve",
        paragraphs: [
          "Governanca reune os controles que uma empresa precisa para operar dados reais. A tela mostra postura de seguranca, chaves de API, auditoria, exportacoes, mapa documental e evidencias. Ela nao e apenas uma pagina administrativa; e a area que permite responder quem acessou, quem gravou, qual credencial foi usada e qual dado foi alterado.",
          "Quando o projeto usa dados sensiveis, como emails, identificadores pessoais, historico academico ou dados de clientes, a governanca precisa ser tratada como parte do produto. Senhas devem ser armazenadas com hash forte, chaves devem ser gravadas como digest, tokens devem expirar e toda acao relevante precisa deixar rastro."
        ]
      },
      {
        heading: "Chaves de API",
        paragraphs: [
          "Chaves de API sao usadas por sistemas externos. Cada chave pertence a uma organizacao, pode ser restrita a um projeto, possui escopos e pode ter expiracao. A plataforma armazena apenas o hash da chave. Depois da criacao, o valor completo nao deve ser mostrado novamente.",
          "Escopos reduzem o impacto de vazamento. Uma chave de ingestao pode ter apenas predictions:write. Outra chave pode ter feedback:write. Uma chave de consulta pode ter predictions:read. Em producao, tambem e recomendado usar rotacao periodica, limite por ambiente e registro de last_used_at."
        ],
        example: {
          title: "Criar uma chave com escopos",
          language: "json",
          caption: "A interface faz isso sem exigir JSON. Este exemplo e para integracao ou teste via API.",
          code: `{
  "name": "servico-scoring-producao",
  "project_id": "proj_123",
  "scopes": ["predictions:write", "feedback:write"],
  "expires_at": "2026-12-31T23:59:59Z"
}`
        }
      },
      {
        heading: "Auditoria e evidencias",
        paragraphs: [
          "Audit trail lista eventos relevantes da plataforma. Ele registra login, criacao de credenciais, ingestao de predicoes, feedback, replay, exportacao, checks de seguranca e outras acoes de impacto. O filtro ajuda a localizar eventos por tipo, ator, projeto ou periodo.",
          "Evidencias exportadas devem preservar contexto suficiente para explicar uma decisao sem expor mais dados do que o necessario. Em um ambiente corporativo, esse fluxo deve se integrar a retencao, classificacao de dados e politica interna de LGPD."
        ]
      }
    ],
    related: ["API", "Modelo documental", "Operacao"]
  },
  {
    id: "api",
    label: "API",
    title: "API e integracoes",
    intro: "A API permite registrar predicoes, feedback, replay, what-if, exportacoes, alertas, modelos e auditoria.",
    topics: [
      {
        heading: "Autenticacao",
        paragraphs: [
          "A API aceita tokens de sessao para usuarios autenticados e API keys para sistemas externos. Tokens de sessao sao usados pelo front-end. API keys sao usadas por pipelines, servicos de scoring, cargas automatizadas e integracoes corporativas.",
          "Toda chamada que altera dados deve usar credencial com escopo compativel. Isso impede que uma chave criada apenas para ingestao consiga exportar dados ou mexer em governanca. A documentacao tecnica completa fica no arquivo docs/api.md."
        ]
      },
      {
        heading: "Ingestao de predicoes",
        paragraphs: [
          "Para registrar uma predicao, o sistema externo envia projeto, modelo, versao, entidade, features, prediction e request_id. O request_id e importante para idempotencia e rastreabilidade. Se a empresa tiver um servico de scoring, ele deve calcular o score e chamar o ModelTrace logo apos a decisao.",
          "Features podem variar por modelo, mas devem seguir o contrato da versao. Campos adicionais podem ser mantidos em metadata quando forem relevantes para auditoria, observabilidade ou reconciliacao com sistemas externos."
        ],
        example: {
          title: "Registrar uma predicao",
          language: "bash",
          caption: "Exemplo minimo usando API key com escopo predictions:write.",
          code: `curl -X POST "http://127.0.0.1:8001/api/v1/predictions" \\
  -H "Authorization: Bearer mt_live_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "project_id": "proj_123",
    "model_id": "model_123",
    "model_version": "v1.0.0",
    "entity_id": "entity_001",
    "features": {"feature_a": 10, "feature_b": "A"},
    "prediction": {"score": 0.81, "label": "alto_risco"},
    "request_id": "req_001"
  }'`
        }
      },
      {
        heading: "Consulta e recuperacao",
        paragraphs: [
          "Sistemas internos podem recuperar predicoes por projeto, modelo, entidade, feedback, label, janela e paginacao. Isso permite construir relatorios, reconciliar decisoes ou alimentar ferramentas de atendimento sem consultar diretamente o banco.",
          "Feedback deve ser enviado quando o desfecho confiavel estiver disponivel. Em alguns dominios isso acontece no mesmo dia. Em outros, pode levar semanas ou meses. A plataforma aceita esse atraso e atualiza as metricas quando o feedback chega."
        ]
      }
    ],
    related: ["Workbench", "Governanca", "Predicoes"]
  },
  {
    id: "api-example",
    label: "Exemplo end-to-end",
    title: "Exemplo completo: do modelo ate a operacao",
    intro: "Exemplo curto e comentado que mostra a fronteira entre o codigo do modelo e a API do ModelTrace. O caso de uso e classificacao binaria de risco operacional, mas o padrao se aplica a qualquer dominio.",
    topics: [
      {
        heading: "Visao geral do fluxo",
        paragraphs: [
          "O fluxo combina duas pecas claramente separadas. A primeira e seu codigo de Machine Learning: treina o modelo, calcula score, gera explicacoes. A segunda e a API REST do ModelTrace: registra projeto, modelo, versao, predicoes, feedback e dispara dashboards, drift e exportacoes.",
          "Mantendo essa fronteira clara, voce pode trocar de algoritmo sem mexer na integracao. O bloco 'SEU MODELO' muda; as chamadas para a API ficam iguais. A documentacao tecnica completa do exemplo, com codigo executavel, fica em docs/api.md, secao 23."
        ]
      },
      {
        heading: "Bloco 1 - SEU MODELO (sklearn, joblib, sua logica)",
        paragraphs: [
          "Treine o modelo da forma habitual. Aqui usamos LogisticRegression sobre features sinteticas de manutencao industrial. Em producao, voce substitui pelo seu pipeline real (LightGBM, XGBoost, redes, regras) sem mudar a integracao."
        ],
        example: {
          title: "Treinar e pontuar (codigo do modelo)",
          language: "python",
          caption: "Tudo neste bloco e codigo seu. O ModelTrace nao interfere.",
          code: `from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

FEATURE_NAMES = ["n_evt_1h", "n_crit_1h", "vibration_rms", "oil_temp_c"]

def train_model(X_train, y_train, X_test, y_test):
    clf = LogisticRegression(max_iter=500, class_weight="balanced")
    clf.fit(X_train, y_train)
    ap = average_precision_score(y_test, clf.predict_proba(X_test)[:, 1])
    return clf, {"average_precision": float(ap)}

def score(model, features):
    row = [[features[name] for name in FEATURE_NAMES]]
    proba = float(model.predict_proba(row)[0, 1])
    label = "event_risk" if proba >= 0.50 else "normal_operation"
    return proba, label`
        }
      },
      {
        heading: "Bloco 2 - MODELTRACE API (HTTP REST sob /api/v1)",
        paragraphs: [
          "Depois de treinado, registre o contexto do modelo no ModelTrace. Sao quatro chamadas que rodam apenas uma vez por modelo: login, criar projeto, criar modelo, criar versao. Em seguida crie uma API key dedicada para o pipeline."
        ],
        example: {
          title: "Registrar projeto, modelo e versao",
          language: "python",
          caption: "Cada funcao corresponde a um endpoint da API.",
          code: `import requests
BASE_URL = "http://127.0.0.1:8001/api/v1"

# POST /auth/login
token = requests.post(f"{BASE_URL}/auth/login",
    json={"email": EMAIL, "password": PASSWORD}).json()["access_token"]

# POST /projects
project_id = requests.post(f"{BASE_URL}/projects",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "Manutencao Industrial", "problem_type": "binary_classification"}
).json()["_id"]

# POST /projects/{id}/models
model_id = requests.post(f"{BASE_URL}/projects/{project_id}/models",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "Risco DontGo (LogReg)", "target_name": "event_risk",
          "expected_features": [{"name": n, "type": "numeric"} for n in FEATURE_NAMES]}
).json()["_id"]

# POST /models/{id}/versions
requests.post(f"{BASE_URL}/models/{model_id}/versions",
    headers={"Authorization": f"Bearer {token}"},
    json={"version": "v1", "algorithm": "LogisticRegression",
          "status": "production", "offline_metrics": metrics})

# POST /projects/{id}/api-keys
api_key = requests.post(f"{BASE_URL}/projects/{project_id}/api-keys",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "Pipeline", "scopes": ["predictions:write", "feedback:write"]}
).json()["api_key"]`
        }
      },
      {
        heading: "Bloco 3 - Loop de serving (modelo + API alternando)",
        paragraphs: [
          "Cada decisao em producao executa duas coisas em sequencia. Primeiro, seu modelo calcula o score (codigo seu). Depois, voce envia o documento da predicao para o ModelTrace (chamada de API). Use request_id para idempotencia, o que protege contra retries duplicados."
        ],
        example: {
          title: "Cada predicao mistura SEU MODELO + MODELTRACE API",
          language: "python",
          caption: "A fronteira entre as duas pecas fica explicita nos comentarios.",
          code: `for i, raw in enumerate(stream):
    # ===== SEU MODELO =====
    features = extract_features(raw)
    score_value, label = score(model, features)

    # ===== MODELTRACE API =====
    # POST /predictions
    prediction_id = requests.post(f"{BASE_URL}/predictions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "project_id": project_id,
            "model_id": model_id,
            "model_version": "v1",
            "entity_id": raw["asset_id"],
            "features": features,
            "prediction": {"label": label, "score": score_value, "threshold": 0.5},
            "metadata": {"request_id": f"req_{raw['asset_id']}_{i}"}
        }
    ).json()["prediction_id"]`
        }
      },
      {
        heading: "Bloco 4 - Feedback, dashboard e drift (apenas API)",
        paragraphs: [
          "Quando o desfecho real chega, envie feedback. A plataforma atualiza matriz de confusao, recall, precision e a aba Operacao. Depois leia o dashboard, dispare drift ou exporte CSV para auditoria. Tudo isso e chamada de API; o modelo nao e mais necessario nesta fase."
        ],
        example: {
          title: "Encerrar o ciclo: feedback + dashboard + drift",
          language: "python",
          caption: "Estas chamadas alimentam o Overview, o DS Lab e a Governanca.",
          code: `# POST /predictions/{id}/feedback
requests.post(f"{BASE_URL}/predictions/{prediction_id}/feedback",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"observed_value": 1, "source": "maintenance_system"})

# GET /projects/{id}/dashboard
dash = requests.get(f"{BASE_URL}/projects/{project_id}/dashboard",
    headers={"Authorization": f"Bearer {token}"}).json()

# POST /models/{id}/drift/run
requests.post(f"{BASE_URL}/models/{model_id}/drift/run",
    headers={"Authorization": f"Bearer {token}"})

# POST /exports (auditoria/regulatorio)
requests.post(f"{BASE_URL}/exports",
    headers={"Authorization": f"Bearer {token}"},
    json={"type": "predictions", "format": "csv", "redact_pii": True,
          "filters": {"project_id": project_id}})`
        }
      },
      {
        heading: "Resumo da divisao",
        paragraphs: [
          "Seu modelo decide. O ModelTrace observa, audita e governa. As 9 funcoes da API (login, projeto, modelo, versao, api_key, prediction, feedback, dashboard, drift) cobrem o ciclo completo de pos-deploy. O codigo executavel completo do exemplo, incluindo treino do modelo com dados sinteticos, esta em docs/api.md secao 23."
        ]
      }
    ],
    related: ["API", "Workbench", "Predicoes"]
  },
  {
    id: "action-results",
    label: "Resultados",
    title: "Resultados das acoes e detalhes tecnicos",
    intro: "A plataforma mostra retorno imediato para cada acao e preserva detalhes tecnicos quando o usuario precisa auditar, copiar ou investigar uma resposta.",
    topics: [
      {
        heading: "Bloco de resultado",
        paragraphs: [
          "Apos acoes como Drift, Equidade, Comparar versoes, Criar API key, Registrar predicao, What-if, Replay, Exportar CSV e Aplicar controles, a interface exibe um bloco de resultado. Esse bloco resume a resposta do backend e evita que o usuario dependa apenas do toast.",
          "O titulo do bloco muda conforme a acao. Drift mostra relatorio de estabilidade. Comparacao de versoes mostra as versoes comparadas e metricas. API key mostra o valor recem-criado e o prefixo. What-if mostra score original, score estimado, delta e possivel mudanca de decisao. Replay mostra a nova leitura registrada."
        ]
      },
      {
        heading: "Detalhes tecnicos da predicao",
        paragraphs: [
          "No Decision inspector existe uma area de detalhes tecnicos. Ela mostra o documento da predicao em formato estruturado, incluindo features, prediction, explanations, decision, metadata, feedback e outros campos disponiveis. Essa area e voltada a cientistas de dados, engenharia e auditoria.",
          "O usuario final nao precisa abrir essa area para trabalhar. Ela existe para quando alguem precisa verificar o payload real, confirmar tipos de dados, entender feature ausente, conferir metadata de origem ou copiar informacao para investigacao."
        ]
      },
      {
        heading: "Estados vazios e erros",
        paragraphs: [
          "Quando uma lista nao tem dados, a interface mostra um estado vazio em vez de uma tabela quebrada. Exemplos: sem versoes, sem diagnosticos, fila vazia, sem alertas ativos, sem chaves de API e sem eventos de auditoria para o filtro.",
          "Quando uma acao falha, a mensagem de erro vem da API e aparece no toast. Em fluxos com formulario, como Workbench, a interface tambem mostra uma lista de erros de validacao dentro da propria tela para indicar exatamente quais campos precisam ser corrigidos."
        ]
      },
      {
        heading: "Por que ainda existe codigo na documentacao",
        paragraphs: [
          "O usuario operacional nao precisa escrever JSON para usar o produto. Predicoes, feedback, what-if, replay, exportacoes e seguranca podem ser usados pela interface. Os exemplos de codigo aparecem apenas nas areas em que um integrador, cientista de dados ou engenheiro precisa consumir a API diretamente.",
          "Essa separacao e intencional. A interface explica o fluxo humano. Os blocos de codigo documentam contratos tecnicos para automacao, pipelines, servicos de scoring e testes."
        ]
      }
    ],
    related: ["Decision inspector", "API", "Workbench"]
  }
];

function percent(value: number | undefined) {
  return `${(((value ?? 0) as number) * 100).toFixed(1)}%`;
}

function fmt(value: unknown): string {
  if (typeof value === "number") return value.toLocaleString("pt-BR");
  if (typeof value === "string") return value;
  return "-";
}

function LanguageToggle({
  locale,
  onChange
}: {
  locale: Locale;
  onChange: (locale: Locale) => void;
}) {
  const nextLocale: Locale = locale === "pt-BR" ? "en" : "pt-BR";
  const label = locale === "pt-BR"
    ? "Idioma: Português. Alternar para inglês"
    : "Language: English. Switch to Portuguese";
  return (
    <button
      type="button"
      className="language-toggle"
      aria-label={label}
      aria-pressed={locale === "en"}
      title={label}
      onClick={() => onChange(nextLocale)}
    >
      <span className={locale === "pt-BR" ? "active" : ""} aria-hidden="true">
        PT
      </span>
      <span className={locale === "en" ? "active" : ""} aria-hidden="true">
        EN
      </span>
    </button>
  );
}

function statusClass(score: number) {
  if (score >= 82) return "good";
  if (score >= 62) return "warn";
  return "bad";
}

type AuthScenario = "login" | "register" | "reset-request" | "reset-confirm";

function authErrorMessage(
  scenario: AuthScenario,
  response: { status: number; error?: string; detail?: unknown }
): string {
  const detail = (response.error || "").toLowerCase();

  if (response.status === 0) {
    return "Nao foi possivel contactar o servidor. Verifique sua conexao.";
  }

  if (scenario === "login") {
    if (response.status === 401) return "Email ou senha incorretos.";
    if (response.status === 422) return "Formato de email invalido.";
    if (response.status === 403) return "Conta bloqueada ou inativa.";
    if (response.status === 429) return "Muitas tentativas. Aguarde alguns minutos.";
    return "Erro interno. Tente novamente em instantes.";
  }

  if (scenario === "register") {
    if (response.status === 409 || detail.includes("already registered")) {
      return "Este email ja esta cadastrado.";
    }
    if (response.status === 422) {
      if (detail.includes("password") || detail.includes("senha")) {
        return "Senha fora da politica de seguranca.";
      }
      if (detail.includes("email")) {
        return "Formato de email invalido.";
      }
      return "Verifique os dados do formulario.";
    }
    return "Erro interno. Tente novamente em instantes.";
  }

  if (scenario === "reset-request") {
    if (response.status === 404) return "Email nao encontrado.";
    if (response.status === 429) return "Muitas tentativas. Aguarde alguns minutos.";
    return "Erro interno. Tente novamente em instantes.";
  }

  if (scenario === "reset-confirm") {
    if (
      response.status === 400 &&
      (detail.includes("token") || detail.includes("expired") || detail.includes("invalid"))
    ) {
      return "Token invalido ou expirado. Solicite um novo email.";
    }
    if (response.status === 422) return "A nova senha nao atende aos requisitos.";
    return "Erro interno. Tente novamente em instantes.";
  }

  return "Erro interno.";
}

export default function Home() {
  const [locale, setLocale] = useState<Locale>(DEFAULT_LOCALE);
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("diegohenrique.mail@gmail.com");
  const [password, setPassword] = useState("D1eg0X@vi3rHUB");
  const [name, setName] = useState("Diego Henrique Xavier");
  const [organizationName, setOrganizationName] = useState(DEMO_ORGANIZATION_NAME);
  const [jobTitle, setJobTitle] = useState("Cientista de Dados");
  const [department, setDepartment] = useState("Governança de Modelos");
  const [company, setCompany] = useState("ModelTrace");
  const [phone, setPhone] = useState("");
  const [timezone, setTimezone] = useState("America/Sao_Paulo");
  const [bio, setBio] = useState("");
  const [resetOpen, setResetOpen] = useState(false);
  const [resetEmail, setResetEmail] = useState("diegohenrique.mail@gmail.com");
  const [resetToken, setResetToken] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [profileDraft, setProfileDraft] = useState<AnyDoc>({});
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [activeView, setActiveView] = useState("overview");
  const [selectedDocId, setSelectedDocId] = useState(docSections[0].id);
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<AnyDoc | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const { theme, toggle: toggleTheme } = useTheme();
  const [driftHeatmap, setDriftHeatmap] = useState<AnyDoc | null>(null);
  const [driftHeatmapLoading, setDriftHeatmapLoading] = useState(false);
  const [usageData, setUsageData] = useState<AnyDoc | null>(null);
  const [usageLoading, setUsageLoading] = useState(false);
  const [usagePeriodDays, setUsagePeriodDays] = useState(30);
  const [projects, setProjects] = useState<AnyDoc[]>([]);
  const [models, setModels] = useState<AnyDoc[]>([]);
  const [versions, setVersions] = useState<AnyDoc[]>([]);
  const [predictions, setPredictions] = useState<AnyDoc[]>([]);
  const [predictionTotal, setPredictionTotal] = useState(0);
  const [predictionsLoading, setPredictionsLoading] = useState(false);
  const [predictionPage, setPredictionPage] = useState(1);
  const [predictionPageSize, setPredictionPageSize] = useState<number>(PREDICTION_PAGE_SIZE_DEFAULT);
  const [dashboard, setDashboard] = useState<AnyDoc | null>(null);
  const [diagnostics, setDiagnostics] = useState<AnyDoc | null>(null);
  const [diagnosticsLoading, setDiagnosticsLoading] = useState(false);
  const [operationsData, setOperationsData] = useState<AnyDoc | null>(null);
  const [securityPosture, setSecurityPosture] = useState<AnyDoc | null>(null);
  const [auditEvents, setAuditEvents] = useState<AnyDoc[]>([]);
  const [apiKeys, setApiKeys] = useState<AnyDoc[]>([]);
  const [notifications, setNotifications] = useState<AnyDoc[]>([]);
  const [notificationUnread, setNotificationUnread] = useState(0);
  const [jobs, setJobs] = useState<AnyDoc[]>([]);
  const [savedViews, setSavedViews] = useState<AnyDoc[]>([]);
  const [alertRules, setAlertRules] = useState<AnyDoc[]>([]);
  const [contractSummary, setContractSummary] = useState<AnyDoc | null>(null);
  const [entityQuery, setEntityQuery] = useState("");
  const [entityTimeline, setEntityTimeline] = useState<AnyDoc | null>(null);
  const [entityNote, setEntityNote] = useState("");
  const [analysisResult, setAnalysisResult] = useState<AnyDoc | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedModelId, setSelectedModelId] = useState("");
  const [selectedPredictionId, setSelectedPredictionId] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState("Workspace online.");
  const [notice, setNotice] = useState<Notice | null>(null);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [labelFilter, setLabelFilter] = useState("all");
  const [windowFilter, setWindowFilter] = useState("all");
  const [feedbackFilter, setFeedbackFilter] = useState("all");
  const [auditQuery, setAuditQuery] = useState("");
  const [workbenchErrors, setWorkbenchErrors] = useState<string[]>([]);
  const [inspectorPanel, setInspectorPanel] = useState<"feedback" | "what-if" | null>(null);
  const [feedbackOutcome, setFeedbackOutcome] = useState("positive");
  const [feedbackSource, setFeedbackSource] = useState("manual_review");
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [whatIfValues, setWhatIfValues] = useState<Record<string, string>>({});
  const [biasFeature, setBiasFeature] = useState("");
  const [selectedSliceFeature, setSelectedSliceFeature] = useState("");
  const [selectedThreshold, setSelectedThreshold] = useState(0.7);
  const [simStudentId, setSimStudentId] = useState("entity_live_001");
  const [simStudentName, setSimStudentName] = useState("Entidade em acompanhamento");
  const [simWindow, setSimWindow] = useState("p4");
  const [simScore, setSimScore] = useState(0.82);
  const [simFeatureValues, setSimFeatureValues] = useState<Record<string, string>>({});

  const token = session?.access_token;
  const t = (value: unknown) => translateText(value, locale);
  const passwordChecks = useMemo(
    () => passwordPolicyChecks(password, email, name, organizationName),
    [password, email, name, organizationName]
  );
  const passwordReadyForRegister = passwordChecks.every((item) => item.passed);
  const resetPasswordChecks = useMemo(
    () => passwordPolicyChecks(resetPassword, resetEmail || email, name, organizationName),
    [resetPassword, resetEmail, email, name, organizationName]
  );
  const resetPasswordReady = resetPasswordChecks.every((item) => item.passed);

  const selectedProject = useMemo(
    () => projects.find((project) => project._id === selectedProjectId),
    [projects, selectedProjectId]
  );

  const selectedModel = useMemo(
    () => models.find((model) => model._id === selectedModelId),
    [models, selectedModelId]
  );

  const projectName = localizedField(selectedProject, "name", locale, "Workspace sem projeto");
  const projectDescription = localizedField(selectedProject, "description", locale, "Escolha um projeto para iniciar o monitoramento.");
  const modelName = localizedField(selectedModel, "name", locale, "Modelo selecionado");
  const localizedNavItems = useMemo(
    () => navItems.map((item) => ({ ...item, label: t(item.label) })),
    [locale]
  );
  const localizedDocSections = useMemo(() => localizeDocSections(docSections, locale), [locale]);

  const productionVersion = useMemo(
    () => versions.find((version) => version.status === "production") || versions[0],
    [versions]
  );

  const entityLabel = t(selectedProject?.entity_label || selectedProject?.settings?.entity_label || "entidades");
  const positiveLabel = selectedModel?.labels?.positive || selectedProject?.settings?.positive_label || "positive";
  const negativeLabel = selectedModel?.labels?.negative || selectedProject?.settings?.negative_label || "negative";

  const availableBiasFeatures = useMemo<string[]>(() => {
    const modelFeatures = ((selectedModel?.expected_features || []) as AnyDoc[])
      .map((feature: AnyDoc) => feature.name)
      .filter((name: unknown): name is string => typeof name === "string" && Boolean(name));
    return modelFeatures.length ? Array.from(new Set(modelFeatures)) : ["signal_value"];
  }, [selectedModel]);

  const filteredPredictions = useMemo(() => predictions, [predictions]);
  const totalVisiblePredictions = predictionTotal || predictions.length;
  const predictionPageCount = Math.max(1, Math.ceil(Math.max(totalVisiblePredictions, 1) / predictionPageSize));
  const pagedPredictions = useMemo(() => predictions, [predictions]);

  const predictionWindowStats = useMemo(() => {
    const summary = Array.isArray(dashboard?.version_summary) ? dashboard.version_summary : [];
    if (summary.length) {
      return summary.slice(0, 6).map((item: AnyDoc) => ({
        window: String(item.window || item.value || "sem_versao").toUpperCase(),
        value: String(item.value || item.window || "sem_versao"),
        predictions: Number(item.predictions || 0),
        entities: Number(item.entities || 0),
        feedback: Number(item.feedback || 0)
      }));
    }
    return versions.slice(0, 6).map((version) => ({
      window: String(version.version || "sem_versao").toUpperCase(),
      value: String(version.version || "sem_versao"),
      predictions: 0,
      entities: 0,
      feedback: 0
    }));
  }, [dashboard, versions]);

  const predictionVersionOptions = useMemo(() => {
    const summary = Array.isArray(dashboard?.version_summary) ? dashboard.version_summary : [];
    const values = summary.length
      ? summary.map((item: AnyDoc) => item.value || item.window)
      : versions.map((version) => version.version);
    return Array.from(new Set(values.filter(Boolean)))
      .sort()
      .map((version) => ({ value: String(version), label: String(version).toUpperCase() }));
  }, [dashboard, versions]);

  const securityChecks = useMemo(() => {
    return Array.isArray(securityPosture?.checks) ? securityPosture.checks : [];
  }, [securityPosture]);

  const filteredAuditEvents = useMemo(() => {
    const normalized = auditQuery.trim().toLowerCase();
    if (!normalized) return auditEvents;
    return auditEvents.filter((event) => {
      const haystack = [
        event.event_type,
        event.resource_type,
        event.resource_id,
        event.actor?.email_masked,
        event.actor?.id,
        event.actor?.prefix,
        event.created_at
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [auditEvents, auditQuery]);

  const selectedDocSection = useMemo(() => {
    return localizedDocSections.find((section) => section.id === selectedDocId) || localizedDocSections[0];
  }, [localizedDocSections, selectedDocId]);

  const selectedPrediction = useMemo(() => {
    return (
      filteredPredictions.find((prediction) => prediction._id === selectedPredictionId) ||
      filteredPredictions[0] ||
      predictions[0]
    );
  }, [filteredPredictions, predictions, selectedPredictionId]);

  const kpis = dashboard?.kpis || {};
  const confusion = dashboard?.confusion_matrix || {};
  const operationSummary = operationsData?.summary || {};
  const interventionCases = operationsData?.intervention_cases || [];
  const modelEvaluations = operationsData?.model_evaluations || [];
  const dataQuality = operationsData?.data_quality;
  const incidents = operationsData?.incidents || [];
  const alerts = operationsData?.alerts || [];
  const cohorts = operationsData?.cohorts || [];
  const contractMode = contractSummary?.mode || selectedProject?.settings?.data_contract_mode || "warn";
  const diagnosticSummary = diagnostics?.summary || {};
  const thresholdCurve = diagnostics?.threshold_curve || [];
  const selectedThresholdRow = useMemo(() => {
    if (!thresholdCurve.length) return null;
    return thresholdCurve.reduce((nearest: AnyDoc, row: AnyDoc) => (
      Math.abs(Number(row.threshold) - selectedThreshold) < Math.abs(Number(nearest.threshold) - selectedThreshold)
        ? row
        : nearest
    ), thresholdCurve[0]);
  }, [thresholdCurve, selectedThreshold]);
  const actionableRate = kpis.actionable_rate ?? kpis.high_risk_rate ?? 0;
  const healthBreakdown = useMemo(() => {
    const baseScore = 28;
    const feedbackScore = Math.min((kpis.feedback_rate ?? 0) / 0.45, 1) * 34;
    const alertPenalty = Math.min(kpis.active_alerts ?? 0, 4) * 8;
    const riskPenalty = Math.max(actionableRate - 0.22, 0) * 80;
    const performanceScore = dashboard?.performance?.recall ? dashboard.performance.recall * 38 : 22;
    const score = Math.max(8, Math.min(100, Math.round(baseScore + feedbackScore + performanceScore - alertPenalty - riskPenalty)));
    return {
      score,
      parts: [
        { label: "Base", value: baseScore, detail: "baseline", tone: "positive" },
        { label: "Feedback", value: feedbackScore, detail: percent(kpis.feedback_rate), tone: "positive" },
        { label: "Recall", value: performanceScore, detail: percent(dashboard?.performance?.recall), tone: "positive" },
        { label: "Alertas", value: -alertPenalty, detail: `${fmt(kpis.active_alerts ?? 0)} ativos`, tone: alertPenalty ? "negative" : "positive" },
        { label: "Acionaveis", value: -riskPenalty, detail: percent(actionableRate), tone: riskPenalty ? "negative" : "positive" }
      ]
    };
  }, [dashboard, kpis, actionableRate]);
  const healthScore = healthBreakdown.score;

  const insightRows = useMemo(() => {
    const rows = [];
    if ((kpis.feedback_rate ?? 0) < 0.35) {
      rows.push({
        tone: "warn",
        title: "Cobertura de feedback",
        detail: "Abaixo da meta operacional."
      });
    }
    if (actionableRate > 0.2) {
      rows.push({
        tone: "bad",
        title: "Capacidade operacional",
        detail: "Demanda acima da faixa planejada."
      });
    }
    if (!rows.length) {
      rows.push({
        tone: "good",
        title: "Operacao em faixa",
        detail: "Indicadores sem desvio relevante."
      });
    }
    rows.push({
      tone: "info",
      title: "Governanca ativa",
      detail: "Auditoria, indices e exportacoes operacionais."
    });
    return rows;
  }, [kpis, actionableRate]);

  const apiSnippet = useMemo(() => {
    return `curl -X POST ${API_URL}/predictions \\
  -H "Authorization: Bearer ${apiKey || "mt_live_xxx"}" \\
  -H "Content-Type: application/json" \\
  -d @prediction.json`;
  }, [apiKey]);

  function notify(message: string, tone: Notice["tone"] = "info") {
    setStatus(message);
    setNotice({ id: Date.now(), tone, message });
  }

  function commitSession(next: Session | null) {
    setSession(next);
    if (next) {
      sessionStorage.setItem("modeltrace_session", JSON.stringify(next));
      if (shouldShowOnboarding()) {
        setOnboardingOpen(true);
      }
    } else {
      sessionStorage.removeItem("modeltrace_session");
    }
  }

  function profileFromUser(user: AnyDoc) {
    return {
      name: user.name || "",
      email: user.email || "",
      job_title: user.job_title || "",
      department: user.department || "",
      company: user.company || "",
      phone: user.phone || "",
      timezone: user.timezone || "America/Sao_Paulo",
      bio: user.bio || "",
      email_alerts: user.preferences?.email_alerts !== false,
      compact_mode: Boolean(user.preferences?.compact_mode)
    };
  }

  function mergeSessionUser(user: AnyDoc) {
    if (!session) return;
    const next = { ...session, user };
    commitSession(next);
    setProfileDraft(profileFromUser(user));
  }

  async function refreshMe(accessToken = token) {
    if (!accessToken || !session) return;
    const response = await apiRequest<{ user: AnyDoc }>("/auth/me", {}, accessToken);
    if (response.data) mergeSessionUser(response.data.user);
  }

  async function refreshProjects(accessToken = token) {
    if (!accessToken) return;
    const response = await apiRequest<{ items: AnyDoc[] }>("/projects", {}, accessToken);
    if (response.data) {
      setProjects(response.data.items);
      if (!selectedProjectId && response.data.items[0]) setSelectedProjectId(response.data.items[0]._id);
    } else if (response.status === 401) {
      sessionStorage.removeItem("modeltrace_session");
      setSession(null);
      notify("Sessao expirada. Entre novamente.", "error");
    }
  }

  async function refreshModels(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken || !projectId) return;
    const response = await apiRequest<{ items: AnyDoc[] }>(`/projects/${projectId}/models`, {}, accessToken);
    if (response.data) {
      setModels(response.data.items);
      if (!response.data.items.length) {
        setSelectedModelId("");
      } else if (!response.data.items.some((model) => model._id === selectedModelId)) {
        setSelectedModelId(response.data.items[0]._id);
      }
    }
  }

  async function refreshVersions(modelId = selectedModelId, accessToken = token) {
    if (!accessToken || !modelId) return;
    const response = await apiRequest<{ items: AnyDoc[] }>(`/models/${modelId}/versions`, {}, accessToken);
    if (response.data) setVersions(response.data.items);
  }

  async function refreshPredictions(accessToken = token, page = predictionPage) {
    if (!accessToken) return;
    const safePage = Math.max(1, page);
    const params = new URLSearchParams({
      limit: String(predictionPageSize),
      skip: String((safePage - 1) * predictionPageSize)
    });
    if (selectedProjectId) params.set("project_id", selectedProjectId);
    if (selectedModelId) params.set("model_id", selectedModelId);
    if (labelFilter !== "all") params.set("label", labelFilter);
    if (windowFilter !== "all") params.set("model_version", windowFilter);
    if (feedbackFilter === "with") params.set("feedback_available", "true");
    if (feedbackFilter === "pending") params.set("feedback_available", "false");
    if (debouncedQuery) params.set("q", debouncedQuery);

    setPredictionsLoading(true);
    try {
      const response = await apiRequest<{ items: AnyDoc[]; total: number }>(`/predictions?${params.toString()}`, {}, accessToken);
      if (!response.data) {
        console.warn("Prediction load failed", response.error);
        notify(t("Erro ao carregar predições."), "error");
        return;
      }
      const items = response.data.items;
      const total = response.data.total ?? items.length;
      setPredictions(items);
      setPredictionTotal(total);
      const pageCount = Math.max(1, Math.ceil(Math.max(total, 1) / predictionPageSize));
      if (safePage > pageCount) {
        setPredictionPage(pageCount);
      } else {
        setSelectedPredictionId((current) => (
          current && items.some((item) => item._id === current)
            ? current
            : items[0]?._id || ""
        ));
      }
    } finally {
      setPredictionsLoading(false);
    }
  }

  async function refreshDashboard(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken || !projectId) return;
    const response = await apiRequest<AnyDoc>(`/projects/${projectId}/dashboard`, {}, accessToken);
    if (response.data) setDashboard(response.data);
  }

  async function refreshDiagnostics(
    modelId = selectedModelId,
    accessToken = token,
    sliceFeature = selectedSliceFeature,
    showToast = false
  ) {
    if (!accessToken || !modelId) return false;
    const params = new URLSearchParams();
    if (sliceFeature) params.set("slice_feature", sliceFeature);
    setDiagnosticsLoading(true);
    try {
      const suffix = params.toString() ? `?${params.toString()}` : "";
      const response = await apiRequest<AnyDoc>(`/models/${modelId}/diagnostics${suffix}`, {}, accessToken);
      if (response.data) {
        setDiagnostics(response.data);
        if (response.data.slice_feature && response.data.slice_feature !== selectedSliceFeature) {
          setSelectedSliceFeature(response.data.slice_feature);
        }
        const recommended = Number(response.data.summary?.recommended_threshold ?? selectedModel?.default_threshold ?? 0.7);
        setSelectedThreshold(Number.isFinite(recommended) ? recommended : 0.7);
        if (showToast) notify("DS Lab atualizado.", "success");
        return true;
      }
      if (showToast) {
        console.warn("DS Lab refresh failed", response.error);
        notify(t("Erro no DS Lab."), "error");
      }
      return false;
    } finally {
      setDiagnosticsLoading(false);
    }
  }

  async function refreshAudit(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken || !projectId) return;
    const response = await apiRequest<{ items: AnyDoc[] }>(`/projects/${projectId}/audit-events`, {}, accessToken);
    if (response.data) setAuditEvents(response.data.items);
  }

  async function refreshOperations(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken || !projectId) return false;
    const response = await apiRequest<AnyDoc>(`/projects/${projectId}/operations`, {}, accessToken);
    if (response.data) {
      setOperationsData(response.data);
      return true;
    }
    return false;
  }

  async function refreshApiKeys(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken || !projectId) {
      setApiKeys([]);
      return false;
    }
    const response = await apiRequest<{ items: AnyDoc[] }>(`/projects/${projectId}/api-keys`, {}, accessToken);
    if (response.data) {
      setApiKeys(response.data.items);
      return true;
    }
    return false;
  }

  async function refreshNotifications(accessToken = token) {
    if (!accessToken) return false;
    const response = await apiRequest<{ items: AnyDoc[]; unread: number }>("/notifications", {}, accessToken);
    if (response.data) {
      setNotifications(response.data.items);
      setNotificationUnread(response.data.unread || 0);
      return true;
    }
    return false;
  }

  async function refreshJobs(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken) return false;
    const suffix = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
    const response = await apiRequest<{ items: AnyDoc[] }>(`/jobs${suffix}`, {}, accessToken);
    if (response.data) {
      setJobs(response.data.items);
      return true;
    }
    return false;
  }

  async function refreshSavedViews(accessToken = token) {
    if (!accessToken) return false;
    const response = await apiRequest<{ items: AnyDoc[] }>("/saved-views", {}, accessToken);
    if (response.data) {
      setSavedViews(response.data.items);
      return true;
    }
    return false;
  }

  async function refreshAlertRules(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken || !projectId) return false;
    const response = await apiRequest<{ items: AnyDoc[] }>(`/alert-rules?project_id=${projectId}`, {}, accessToken);
    if (response.data) {
      setAlertRules(response.data.items);
      return true;
    }
    return false;
  }

  async function refreshDataContract(projectId = selectedProjectId, accessToken = token) {
    if (!accessToken || !projectId) return false;
    const response = await apiRequest<AnyDoc>(`/projects/${projectId}/data-contract`, {}, accessToken);
    if (response.data) {
      setContractSummary(response.data);
      return true;
    }
    return false;
  }

  async function refreshSecurityPosture(accessToken = token) {
    if (!accessToken) return false;
    const response = await apiRequest<AnyDoc>("/security/posture", {}, accessToken);
    if (response.data) {
      setSecurityPosture(response.data);
      return true;
    }
    return false;
  }

  async function refreshAll(accessToken = token) {
    await refreshProjects(accessToken);
    await refreshSecurityPosture(accessToken);
    await refreshNotifications(accessToken);
    await refreshJobs(selectedProjectId, accessToken);
    await refreshSavedViews(accessToken);
    if (selectedProjectId) {
      await refreshModels(selectedProjectId, accessToken);
      await refreshDashboard(selectedProjectId, accessToken);
      await refreshAudit(selectedProjectId, accessToken);
      await refreshOperations(selectedProjectId, accessToken);
      await refreshApiKeys(selectedProjectId, accessToken);
      await refreshAlertRules(selectedProjectId, accessToken);
      await refreshDataContract(selectedProjectId, accessToken);
      if (activeView === "predictions") await refreshPredictions(accessToken, predictionPage);
      if (activeView === "lab") await refreshDiagnostics(selectedModelId, accessToken, selectedSliceFeature);
    }
    if (selectedModelId) await refreshVersions(selectedModelId, accessToken);
  }

  async function refreshWorkspace() {
    if (!token) return;
    notify("Atualizando workspace...", "info");
    await refreshAll(token);
    notify("Workspace atualizado.", "success");
  }

  async function refreshOperationsWithToast() {
    notify("Atualizando centro de operacao...", "info");
    const ok = await refreshOperations();
    notify(ok ? "Centro de operacao atualizado." : "Erro ao atualizar centro de operacao.", ok ? "success" : "error");
  }

  async function refreshDiagnosticsWithToast() {
    notify("Atualizando DS Lab...", "info");
    await refreshDiagnostics(selectedModelId, token, selectedSliceFeature, true);
  }

  async function runSecurityMigration() {
    if (!token) {
      notify("Entre novamente para executar a migracao de seguranca.", "error");
      return;
    }
    notify("Aplicando controles de seguranca...", "info");
    const response = await apiRequest<AnyDoc>("/security/migrate-sensitive-data", { method: "POST" }, token);
    if (response.data) {
      setAnalysisResult({ type: "security-migration", result: response.data });
      await refreshSecurityPosture(token);
      await refreshAudit(selectedProjectId, token);
      await refreshPredictions(token, predictionPage);
      notify("Controles aplicados.", "success");
    } else {
      console.warn("Security migration failed", response.error);
      notify(t("Erro na migração de segurança."), "error");
    }
  }

  function exportDiagnosticsPack() {
    if (!diagnostics) {
      notify("Atualize o DS Lab antes de exportar.", "error");
      return;
    }
    const blob = new Blob([JSON.stringify(diagnostics, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `modeltrace-ds-lab-${selectedModel?.slug || selectedModelId || "model"}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    notify("Pacote exportado.", "success");
  }

  async function register() {
    if (!passwordReadyForRegister) {
      notify("Confira os requisitos de senha para criar a conta.", "error");
      return;
    }
    const response = await apiRequest<Session>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        name,
        email,
        password,
        organization_name: organizationName || DEMO_ORGANIZATION_NAME,
        job_title: jobTitle || null,
        department: department || null,
        company: company || null,
        phone: phone || null,
        timezone,
        bio: bio || null
      })
    });
    if (response.data) {
      commitSession(response.data);
      setProfileDraft(profileFromUser(response.data.user));
      notify("Conta criada. Verifique seu email para confirmar o acesso.", "success");
      await refreshProjects(response.data.access_token);
    } else {
      console.error("[auth] register failed", {
        status: response.status,
        error: response.error,
        detail: response.detail
      });
      notify(t(authErrorMessage("register", response)), "error");
    }
  }

  async function login() {
    const response = await apiRequest<Session>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    if (response.data) {
      commitSession(response.data);
      setProfileDraft(profileFromUser(response.data.user));
      notify("Sessao iniciada.", "success");
      await refreshProjects(response.data.access_token);
    } else {
      console.error("[auth] login failed", {
        status: response.status,
        error: response.error,
        detail: response.detail,
        email
      });
      notify(t(authErrorMessage("login", response)), "error");
    }
  }

  async function logout() {
    if (token) {
      await apiRequest("/auth/logout", { method: "POST" }, token);
    }
    commitSession(null);
    notify("Sessao encerrada.", "success");
  }

  async function requestPasswordReset(targetOverride?: string) {
    const targetEmail = targetOverride || resetEmail || email;
    if (!targetEmail) {
      notify("Informe o email da conta.", "error");
      return;
    }
    notify("Enviando instrucoes de redefinicao...", "info");
    const response = await apiRequest<AnyDoc>("/auth/password-reset/request", {
      method: "POST",
      body: JSON.stringify({ email: targetEmail })
    });
    if (response.data) {
      notify("Instrucoes enviadas. Verifique seu email.", "success");
    } else {
      console.error("[auth] password-reset request failed", {
        status: response.status,
        error: response.error,
        detail: response.detail
      });
      notify(t(authErrorMessage("reset-request", response)), "error");
    }
  }

  async function confirmPasswordReset() {
    if (!resetToken.trim()) {
      notify("Informe o token recebido por email.", "error");
      return;
    }
    if (!resetPasswordReady) {
      notify("A nova senha nao atende aos requisitos.", "error");
      return;
    }
    const response = await apiRequest<AnyDoc>("/auth/password-reset/confirm", {
      method: "POST",
      body: JSON.stringify({ token: resetToken.trim(), new_password: resetPassword })
    });
    if (response.data) {
      setPassword(resetPassword);
      setResetPassword("");
      setResetToken("");
      setResetOpen(false);
      notify("Senha atualizada. Entre com a nova senha.", "success");
    } else {
      console.error("[auth] password-reset confirm failed", {
        status: response.status,
        error: response.error,
        detail: response.detail
      });
      notify(t(authErrorMessage("reset-confirm", response)), "error");
    }
  }

  async function verifyEmailToken(tokenValue: string) {
    const response = await apiRequest<{ user: AnyDoc }>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token: tokenValue })
    });
    if (response.data) {
      if (session) {
        mergeSessionUser(response.data.user);
      } else {
        const raw = sessionStorage.getItem("modeltrace_session");
        if (raw) {
          const parsed = JSON.parse(raw);
          commitSession({ ...parsed, user: response.data.user });
        }
      }
      notify("Email confirmado.", "success");
    } else {
      console.warn("Email verification failed", response.error);
      notify("Link de confirmacao invalido ou expirado.", "error");
    }
  }

  async function resendVerificationEmail() {
    if (!token) return;
    const response = await apiRequest<AnyDoc>("/auth/resend-verification", { method: "POST" }, token);
    if (response.data) {
      notify(response.data.email_verified ? "Email ja confirmado." : "Email de confirmacao enviado.", "success");
    } else {
      console.warn("Resend verification failed", response.error);
      notify("Nao foi possivel enviar a confirmacao.", "error");
    }
  }

  async function saveProfile() {
    if (!token || !session) return;
    notify("Salvando perfil...", "info");
    const response = await apiRequest<{ user: AnyDoc; updated: boolean }>("/auth/me", {
      method: "PATCH",
      body: JSON.stringify({
        name: profileDraft.name,
        email: profileDraft.email,
        job_title: profileDraft.job_title || null,
        department: profileDraft.department || null,
        company: profileDraft.company || null,
        phone: profileDraft.phone || null,
        timezone: profileDraft.timezone || "America/Sao_Paulo",
        bio: profileDraft.bio || null,
        preferences: {
          email_alerts: Boolean(profileDraft.email_alerts),
          compact_mode: Boolean(profileDraft.compact_mode),
          locale
        }
      })
    }, token);
    if (response.data) {
      mergeSessionUser(response.data.user);
      notify("Perfil atualizado.", "success");
    } else {
      console.warn("Profile update failed", response.error);
      notify(response.status === 409 ? "Este email ja esta em uso." : "Nao foi possivel salvar o perfil.", "error");
    }
  }

  async function uploadAvatar(file?: File | null) {
    if (!file || !token) return;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
      notify("Use uma imagem PNG, JPG ou WebP.", "error");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      notify("A imagem deve ter ate 2 MB.", "error");
      return;
    }
    setAvatarUploading(true);
    try {
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
      const response = await apiRequest<{ user: AnyDoc }>("/auth/me/avatar", {
        method: "POST",
        body: JSON.stringify({
          file_name: file.name,
          content_type: file.type,
          data_base64: dataUrl
        })
      }, token);
      if (response.data) {
        mergeSessionUser(response.data.user);
        notify("Foto atualizada.", "success");
      } else {
        console.warn("Avatar upload failed", response.error);
        notify("Nao foi possivel atualizar a foto.", "error");
      }
    } finally {
      setAvatarUploading(false);
    }
  }

  async function refreshMonitor() {
    if (!token) return;
    notify("Atualizando monitor...", "info");
    await refreshAll();
    notify("Monitor atualizado.", "success");
  }

  async function createApiKey() {
    if (!token || !selectedProjectId) {
      notify("Escolha um projeto para gerar a chave.", "error");
      return;
    }
    notify("Criando chave de API...", "info");
    const expiresAt = new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString();
    const response = await apiRequest<{ api_key: string; record: AnyDoc }>(
      `/projects/${selectedProjectId}/api-keys`,
      {
        method: "POST",
        body: JSON.stringify({
          name: "Ingestao operacional",
          scopes: ["predictions:write", "predictions:batch", "feedback:write"],
          expires_at: expiresAt
        })
      },
      token
    );
    if (response.data) {
      setApiKey(response.data.api_key);
      setAnalysisResult({ type: "api-key", result: { api_key: response.data.api_key, prefix: response.data.record.prefix } });
      await refreshApiKeys(selectedProjectId, token);
      await refreshAudit(selectedProjectId, token);
      notify(`API key criada. Prefixo: ${response.data.record.prefix}.`, "success");
    } else {
      console.warn("API key creation failed", response.error);
      notify(t("Erro ao criar API key."), "error");
    }
  }

  async function revokeApiKey(keyId: string) {
    if (!token) return;
    const response = await apiRequest<AnyDoc>(`/api-keys/${keyId}`, { method: "DELETE" }, token);
    if (response.data) {
      await refreshApiKeys(selectedProjectId, token);
      await refreshAudit(selectedProjectId, token);
      await refreshSecurityPosture(token);
      notify("API key revogada.", "success");
    } else {
      console.warn("API key revoke failed", response.error);
      notify(t("Erro ao revogar chave."), "error");
    }
  }

  function buildPredictionPayload() {
    const threshold = Number(selectedModel?.default_threshold ?? 0.7);
    const score = Math.max(0, Math.min(1, Number(simScore) || 0));
    const label = score >= threshold ? positiveLabel : negativeLabel;
    const expected = selectedModel?.expected_features || [];
    const dynamicFeatures = expected.reduce((acc: AnyDoc, feature: AnyDoc, index: number) => {
      const raw = simFeatureValues[feature.name];
      if (feature.type === "numeric") {
        acc[feature.name] = raw === undefined ? index + 1 : raw === "" ? "" : Number(raw);
      } else {
        acc[feature.name] = raw === undefined ? "valor_padrao" : raw;
      }
      return acc;
    }, {});
    return {
      project_id: selectedProjectId,
      model_id: selectedModelId,
      model_version: simWindow || productionVersion?.version || "p4",
      entity_id: simStudentId || `entity_${Math.floor(Math.random() * 9000 + 1000)}`,
      entity_type: selectedProject?.domain || "entity",
      entity_display_name: simStudentName || "Entidade em acompanhamento",
      features: Object.keys(dynamicFeatures).length ? dynamicFeatures : { signal_value: score, source: "guided_simulator" },
      prediction: { label, score, threshold },
      explanations: [
        { feature: expected[0]?.name || "score", value: Object.values(dynamicFeatures)[0] ?? score, impact: 0.31, direction: "main_signal", rank: 1 },
        { feature: expected[1]?.name || "threshold", value: Object.values(dynamicFeatures)[1] ?? threshold, impact: 0.18, direction: "supporting_signal", rank: 2 }
      ],
      decision: {
        action: label === positiveLabel ? "human_review" : "monitor",
        status: label === positiveLabel ? "triggered" : "not_triggered"
      },
      metadata: {
        source_system: "guided_simulator",
        environment: "product_simulation",
        request_id: `ui_${Date.now()}`
      }
    };
  }

  async function submitPrediction(payload: AnyDoc) {
    const credential = apiKey || token;
    if (!credential) {
      notify("Sessao necessaria para registrar predicoes.", "error");
      return null;
    }
    const response = await apiRequest<{ prediction_id: string }>(
      "/predictions",
      { method: "POST", body: JSON.stringify(payload) },
      credential
    );
    if (response.data) {
      notify(`Predicao salva: ${response.data.prediction_id}`, "success");
      if (activeView === "predictions") await refreshPredictions(token, predictionPage);
      await refreshDashboard();
      await refreshAudit();
      return response.data;
    } else {
      console.warn("Prediction submission failed", response.error);
      notify(t("Erro ao enviar predição."), "error");
      return null;
    }
  }

  async function sendDemoPrediction() {
    if (!selectedProjectId || !selectedModelId) {
      notify("Escolha projeto e modelo para registrar a predicao.", "error");
      return;
    }
    await submitPrediction(buildPredictionPayload());
  }

  async function sendGuidedPrediction() {
    const payload = buildPredictionPayload();
    const errors = validatePredictionPayload(payload);
    setWorkbenchErrors(errors);
    if (errors.length) {
      notify("Revise os campos destacados antes de registrar a predicao.", "error");
      return;
    }
    const result = await submitPrediction(payload);
    if (result) setAnalysisResult({ type: "api-response", result });
  }

  function validatePredictionPayload(payload: AnyDoc) {
    const errors: string[] = [];
    if (!payload.project_id) errors.push("Projeto obrigatorio.");
    if (!payload.model_id) errors.push("Modelo obrigatorio.");
    if (!payload.model_version) errors.push("Versao obrigatoria.");
    if (!payload.entity_id) errors.push("ID da entidade obrigatorio.");
    if (!Number.isFinite(Number(payload.prediction?.score))) errors.push("Score deve ser numerico.");
    const expected = selectedModel?.expected_features || [];
    expected.forEach((feature: AnyDoc) => {
      const name = feature.name;
      if (!name || feature.required === false) return;
      const value = payload.features?.[name];
      if (value === undefined || value === null || value === "") {
        errors.push(`${name}: campo obrigatorio.`);
        return;
      }
      if (feature.type === "numeric" && !Number.isFinite(Number(value))) {
        errors.push(`${name}: valor numerico invalido.`);
      }
    });
    return errors.slice(0, 12);
  }

  function openFeedbackPanel() {
    setInspectorPanel((current) => current === "feedback" ? null : "feedback");
  }

  function featureEntriesForWhatIf(prediction = selectedPrediction) {
    return Object.entries(prediction?.features || {}).slice(0, 10);
  }

  function formatFeatureValue(value: unknown) {
    if (typeof value === "boolean") return String(value);
    if (typeof value === "number") return Number(value.toFixed(4)).toString();
    if (value === null || value === undefined) return "";
    return String(value);
  }

  function boundedFeatureValue(original: number, next: number) {
    if (original >= 0 && original <= 1) return Math.max(0, Math.min(1, next));
    return next;
  }

  function buildWhatIfPreset(mode: "current" | "optimistic" | "conservative", prediction = selectedPrediction) {
    const entries = featureEntriesForWhatIf(prediction);
    if (!entries.length && prediction?.prediction?.score !== undefined) {
      const score = Number(prediction.prediction.score || 0);
      const value = mode === "conservative" ? score + 0.05 : mode === "optimistic" ? score - 0.05 : score;
      return { signal_value: formatFeatureValue(Math.max(0, Math.min(1, value))) };
    }
    return Object.fromEntries(entries.map(([feature, value]) => {
      const name = feature.toLowerCase();
      if (typeof value === "number") {
        let next = value;
        const raisesQuality = /(attendance|frequencia|grade|nota|credit|income|score|rate|coverage)/i.test(name);
        const raisesRisk = /(failed|reprov|debt|delay|risk|absen|missing|error|cost|backlog)/i.test(name);
        if (mode === "optimistic") {
          next = raisesRisk ? value * 0.8 : raisesQuality ? value * 1.1 : value * 0.95;
        } else if (mode === "conservative") {
          next = raisesRisk ? value * 1.2 : raisesQuality ? value * 0.9 : value * 1.05;
        }
        return [feature, formatFeatureValue(boundedFeatureValue(value, next))];
      }
      if (typeof value === "boolean") {
        if (mode === "current") return [feature, String(value)];
        if (/scholarship|active|valid|approved|healthy|ok/i.test(name)) {
          return [feature, String(mode === "optimistic")];
        }
        if (/night|failed|error|missing|late|risk/i.test(name)) {
          return [feature, String(mode === "conservative")];
        }
        return [feature, String(value)];
      }
      return [feature, formatFeatureValue(value)];
    }));
  }

  function openWhatIfPanel() {
    setInspectorPanel((current) => {
      const next = current === "what-if" ? null : "what-if";
      if (next === "what-if") setWhatIfValues(buildWhatIfPreset("current"));
      return next;
    });
  }

  function coerceWhatIfValue(feature: string, raw: string) {
    const original = selectedPrediction?.features?.[feature];
    if (typeof original === "number") {
      const value = Number(raw);
      return Number.isFinite(value) ? value : original;
    }
    if (typeof original === "boolean") return raw === "true";
    const numeric = Number(raw);
    if (raw.trim() !== "" && Number.isFinite(numeric) && /^-?\d+(\.\d+)?$/.test(raw.trim())) return numeric;
    return raw;
  }

  async function submitFeedbackToSelectedPrediction() {
    if (!token || !selectedPrediction) return;
    const payload: AnyDoc = {
      source: feedbackSource || "manual_review",
      notes: feedbackNotes
    };
    if (feedbackOutcome === "positive") {
      payload.observed_label = positiveLabel;
      payload.observed_value = 1;
    } else if (feedbackOutcome === "negative") {
      payload.observed_label = negativeLabel;
      payload.observed_value = 0;
    } else {
      payload.observed_label = "inconclusive";
      payload.observed_value = null;
    }
    const response = await apiRequest<AnyDoc>(
      `/predictions/${selectedPrediction._id}/feedback`,
      { method: "POST", body: JSON.stringify(payload) },
      token
    );
    if (response.data) {
      notify(`Feedback salvo: ${response.data.feedback.classification_result}.`, "success");
      setFeedbackNotes("");
      setInspectorPanel(null);
      await refreshPredictions(token, predictionPage);
      await refreshDashboard();
      if (selectedModelId) await refreshDiagnostics(selectedModelId, token, selectedSliceFeature);
    } else {
      console.warn("Feedback failed", response.error);
      notify(t("Erro ao registrar feedback."), "error");
    }
  }

  async function runDrift() {
    if (!token || !selectedModelId) {
      notify("Escolha um modelo para calcular drift.", "error");
      return;
    }
    notify("Calculando drift...", "info");
    const response = await apiRequest<AnyDoc>(`/models/${selectedModelId}/drift/run`, { method: "POST" }, token);
    if (response.data) {
      notify(`Drift atualizado: ${response.data.prediction_drift?.status || response.data.status}`, "success");
      setAnalysisResult({ type: "drift", result: response.data });
      void refreshDriftHeatmap();
    } else {
      notify(t("Erro no drift."), "error");
    }
  }

  async function refreshDriftHeatmap(modelId: string = selectedModelId, accessToken: string | undefined = token) {
    if (!modelId || !accessToken) return;
    setDriftHeatmapLoading(true);
    const response = await apiRequest<AnyDoc>(
      `/models/${modelId}/drift/heatmap?limit=12`,
      { method: "GET" },
      accessToken
    );
    setDriftHeatmapLoading(false);
    if (response.error) {
      notify(`Falha ao carregar drift heatmap: ${response.error}`, "error");
      return;
    }
    setDriftHeatmap(response.data ?? null);
  }

  async function refreshUsage(days: number = usagePeriodDays, accessToken: string | undefined = token) {
    if (!accessToken) return;
    setUsageLoading(true);
    const response = await apiRequest<AnyDoc>(
      `/usage/summary?days=${encodeURIComponent(String(days))}`,
      { method: "GET" },
      accessToken
    );
    setUsageLoading(false);
    if (response.error) {
      notify(`Falha ao carregar consumo: ${response.error}`, "error");
      return;
    }
    setUsageData(response.data ?? null);
  }

  function changeUsagePeriod(days: number) {
    setUsagePeriodDays(days);
    void refreshUsage(days, token);
  }

  async function runBiasAnalysis() {
    if (!token || !selectedModelId || !biasFeature) {
      notify("Escolha um modelo e uma feature para equidade.", "error");
      return;
    }
    notify(`Analisando segmentos por ${biasFeature}...`, "info");
    const response = await apiRequest<AnyDoc>(
      `/models/${selectedModelId}/bias-analysis?feature=${encodeURIComponent(biasFeature)}`,
      {},
      token
    );
    if (response.data) {
      setAnalysisResult({ type: "bias", result: response.data });
      notify(`Equidade atualizada para ${biasFeature}.`, "success");
    } else {
      console.warn("Bias analysis failed", response.error);
      notify(t("Erro na análise de equidade."), "error");
    }
  }

  async function runAlertChecks() {
    if (!token || !selectedProjectId) {
      notify("Escolha um projeto para checar alertas.", "error");
      return;
    }
    notify("Checando regras de alerta...", "info");
    const response = await apiRequest<AnyDoc>(
      `/alerts/run-checks?project_id=${encodeURIComponent(selectedProjectId)}&include_defaults=true`,
      { method: "POST" },
      token
    );
    if (response.data) {
      await refreshOperations(selectedProjectId, token);
      await refreshDashboard(selectedProjectId, token);
      await refreshNotifications(token);
      await refreshJobs(selectedProjectId, token);
      notify(`Alertas checados: ${response.data.created?.length || 0} novos.`, "success");
    } else {
      console.warn("Alert checks failed", response.error);
      notify(t("Erro ao checar alertas."), "error");
    }
  }

  async function runProductJob(type: "alerts" | "drift" | "metrics" | "diagnostics" | "dashboard") {
    if (!token) return;
    const needsModel = ["drift", "metrics", "diagnostics"].includes(type);
    if (!selectedProjectId || (needsModel && !selectedModelId)) {
      notify(needsModel ? "Escolha projeto e modelo para executar o job." : "Escolha um projeto para executar o job.", "error");
      return;
    }
    notify("Job enviado para execucao.", "info");
    const response = await apiRequest<AnyDoc>("/jobs", {
      method: "POST",
      body: JSON.stringify({
        type,
        project_id: selectedProjectId,
        model_id: needsModel ? selectedModelId : null,
        params: { include_defaults: true, slice_feature: selectedSliceFeature }
      })
    }, token);
    if (response.data) {
      await refreshJobs(selectedProjectId, token);
      notify("Job criado.", "success");
    } else {
      console.warn("Job creation failed", response.error);
      notify("Erro ao criar job.", "error");
    }
  }

  async function markNotificationsRead() {
    if (!token) return;
    await apiRequest("/notifications/mark-all-read", { method: "POST" }, token);
    await refreshNotifications(token);
    notify("Notificacoes marcadas como lidas.", "success");
  }

  async function saveCurrentPredictionView() {
    if (!token) return;
    const response = await apiRequest<AnyDoc>("/saved-views", {
      method: "POST",
      body: JSON.stringify({
        view: "predictions",
        name: `Predicoes ${new Date().toLocaleString("pt-BR")}`,
        filters: { project_id: selectedProjectId, model_id: selectedModelId, q: query, labelFilter, windowFilter, feedbackFilter },
        columns: ["id", "entity", "version", "label", "score", "feedback", "created_at"],
        sort: { created_at: "desc" },
        shared: false
      })
    }, token);
    if (response.data) {
      await refreshSavedViews(token);
      notify("View salva.", "success");
    } else {
      notify("Erro ao salvar view.", "error");
    }
  }

  function applySavedView(view: AnyDoc) {
    const filters = view.filters || {};
    if (filters.project_id) setSelectedProjectId(filters.project_id);
    if (filters.model_id) setSelectedModelId(filters.model_id);
    setQuery(filters.q || "");
    setLabelFilter(filters.labelFilter || "all");
    setWindowFilter(filters.windowFilter || "all");
    setFeedbackFilter(filters.feedbackFilter || "all");
    setActiveView(view.view || "predictions");
    notify("View aplicada.", "success");
  }

  async function searchEntityTimeline() {
    if (!token || !selectedProjectId || !entityQuery.trim()) {
      notify("Informe uma entidade para pesquisar.", "error");
      return;
    }
    const response = await apiRequest<AnyDoc>(
      `/projects/${selectedProjectId}/entity-timeline?q=${encodeURIComponent(entityQuery.trim())}`,
      {},
      token
    );
    if (response.data) {
      setEntityTimeline(response.data);
      notify(`${response.data.events?.length || 0} eventos encontrados.`, "success");
    } else {
      notify("Erro ao buscar entidade.", "error");
    }
  }

  async function saveEntityNote() {
    if (!token || !selectedProjectId || !entityQuery.trim() || !entityNote.trim()) return;
    const response = await apiRequest<AnyDoc>(`/projects/${selectedProjectId}/entity-notes`, {
      method: "POST",
      body: JSON.stringify({ entity_id: entityQuery.trim(), content: entityNote.trim(), tags: ["manual"] })
    }, token);
    if (response.data) {
      setEntityNote("");
      await searchEntityTimeline();
      notify("Nota registrada.", "success");
    } else {
      notify("Erro ao registrar nota.", "error");
    }
  }

  async function updateDataContractMode(mode: "accept" | "warn" | "block") {
    if (!token || !selectedProjectId) return;
    const response = await apiRequest<AnyDoc>(`/projects/${selectedProjectId}/data-contract`, {
      method: "PATCH",
      body: JSON.stringify({ mode })
    }, token);
    if (response.data) {
      setContractSummary(response.data);
      notify("Contrato atualizado.", "success");
    } else {
      notify("Erro ao atualizar contrato.", "error");
    }
  }

  async function updateCaseStatus(caseId: string, nextStatus: string) {
    if (!token) return;
    const response = await apiRequest<AnyDoc>(`/intervention-cases/${caseId}/status`, {
      method: "POST",
      body: JSON.stringify({ status: nextStatus, note: "Atualizado pela interface operacional." })
    }, token);
    if (response.data) {
      await refreshOperations();
      notify("Caso atualizado.", "success");
    } else {
      notify("Erro ao atualizar caso.", "error");
    }
  }

  async function submitWhatIfScenario() {
    if (!token || !selectedPrediction) return;
    const hypothetical = Object.fromEntries(
      Object.entries(whatIfValues).map(([feature, value]) => [feature, coerceWhatIfValue(feature, value)])
    );
    const response = await apiRequest<AnyDoc>(
      `/predictions/${selectedPrediction._id}/whatif`,
      {
        method: "POST",
        body: JSON.stringify({
          hypothetical_features: Object.keys(hypothetical).length
            ? hypothetical
            : { signal_value: Math.min(1, Number(selectedPrediction.prediction?.score || 0) + 0.05) }
        })
      },
      token
    );
    if (response.data) {
      setAnalysisResult({ type: "what-if", result: response.data });
      notify("Cenario atualizado.", "success");
    } else {
      console.warn("What-if failed", response.error);
      notify(t("Erro no what-if."), "error");
    }
  }

  async function runReplay() {
    if (!token || !selectedPrediction) return;
    const currentScore = Number(selectedPrediction.prediction?.score || 0);
    const replayScore = Math.max(0, Math.min(1, Number((currentScore - 0.12).toFixed(4))));
    const targetVersion = productionVersion?.version || selectedPrediction.model_version || "current";
    const response = await apiRequest<AnyDoc>(
      `/predictions/${selectedPrediction._id}/replay`,
      { method: "POST", body: JSON.stringify({ target_version: targetVersion, replay_score: replayScore }) },
      token
    );
    if (response.data) {
      setAnalysisResult({ type: "replay", result: response.data });
      notify("Replay salvo.", "success");
    } else {
      console.warn("Replay failed", response.error);
      notify(t("Erro no replay."), "error");
    }
  }

  async function exportPredictions() {
    if (!token || !selectedProjectId) {
      notify("Escolha um projeto para exportar.", "error");
      return;
    }
    notify("Preparando CSV...", "info");
    const response = await apiRequest<AnyDoc>(
      "/exports",
      {
        method: "POST",
        body: JSON.stringify({
          filters: { project_id: selectedProjectId },
          format: "csv",
          include_features: true,
          include_explanations: true
        })
      },
      token
    );
    if (response.data) {
      setAnalysisResult({ type: "export", result: response.data });
      notify(`CSV pronto: ${response.data.record_count} registros.`, "success");
    } else {
      console.warn("Export failed", response.error);
      notify(t("Erro na exportação."), "error");
    }
  }

  function exportAuditEvidence() {
    if (!filteredAuditEvents.length) {
      notify("Nao ha eventos de auditoria para exportar.", "error");
      return;
    }
    const payload = {
      exported_at: new Date().toISOString(),
      project_id: selectedProjectId,
      project_name: selectedProject?.name,
      query: auditQuery.trim() || null,
      event_count: filteredAuditEvents.length,
      events: filteredAuditEvents
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `modeltrace-audit-${selectedProject?.slug || selectedProjectId || "workspace"}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    notify(`${filteredAuditEvents.length} eventos exportados.`, "success");
  }

  async function compareVersions() {
    if (!token || !selectedModelId || versions.length < 2) {
      notify("Sao necessarias duas versoes para comparar.", "error");
      return;
    }
    const production = productionVersion || versions[0];
    const challenger = versions.find((version) => version._id !== production?._id) || versions[1];
    if (!production || !challenger) {
      notify("Nao ha versoes comparaveis.", "error");
      return;
    }
    const response = await apiRequest<AnyDoc>(
      `/models/${selectedModelId}/versions/compare?a=${challenger.version}&b=${production.version}`,
      {},
      token
    );
    if (response.data) {
      setAnalysisResult({ type: "version-compare", result: response.data });
      notify(`Comparacao pronta: ${challenger.version} vs ${production.version}.`, "success");
    } else {
      console.warn("Version comparison failed", response.error);
      notify(t("Erro na comparação."), "error");
    }
  }

  function openPredictions(label = "all", feedback = "all", message = "Predicoes abertas.") {
    setQuery("");
    setLabelFilter(label);
    setWindowFilter("all");
    setFeedbackFilter(feedback);
    setPredictionPage(1);
    setActiveView("predictions");
    notify(message, "info");
  }

  function goToSection(view: string, sectionId: string, message: string) {
    setActiveView(view);
    notify(message, "info");
    if (view === "operations") void refreshOperations();
    window.setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  }

  function alertDestination(alert: AnyDoc) {
    if (alert.type === "missing_features") {
      return { id: "source-quality", label: "qualidade da fonte" };
    }
    if (alert.type === "operations_backlog") {
      return { id: "intervention-queue", label: "fila operacional" };
    }
    return { id: "active-alerts", label: "alertas ativos" };
  }

  function openDocs(sectionId = "start") {
    setSelectedDocId(sectionId);
    setActiveView("docs");
  }

  function runCommandItem(item: CommandItem) {
    setCommandOpen(false);
    setCommandQuery("");
    void item.run();
  }

  const commandItems: CommandItem[] = [
    { id: "view-overview", label: t("Abrir Overview"), detail: t("KPIs, health, volume e matriz."), run: () => setActiveView("overview") },
    { id: "view-monitor", label: t("Abrir Monitor"), detail: t("Versoes, drift, equidade e comparacao."), run: () => setActiveView("monitor") },
    { id: "view-lab", label: t("Abrir DS Lab"), detail: t("Threshold, calibracao e diagnosticos."), run: () => setActiveView("lab") },
    { id: "view-predictions", label: t("Abrir Predicoes"), detail: t("Tabela operacional e Decision inspector."), run: () => openPredictions() },
    { id: "view-entities", label: t("Abrir Entidades"), detail: t("Timeline por entidade e historico completo."), run: () => setActiveView("entities") },
    { id: "view-operations", label: t("Abrir Operacao"), detail: t("Casos, alertas, qualidade e incidentes."), run: () => setActiveView("operations") },
    { id: "view-control", label: t("Abrir Automacao"), detail: t("Jobs, notificacoes e contratos."), run: () => setActiveView("control") },
    { id: "view-workbench", label: t("Abrir Workbench"), detail: t("Entrada guiada de novas predicoes."), run: () => setActiveView("workbench") },
    { id: "view-governance", label: t("Abrir Governanca"), detail: t("Seguranca, API keys e auditoria."), run: () => setActiveView("governance") },
    { id: "view-profile", label: t("Abrir Perfil"), detail: t("Conta, foto, seguranca e preferencias."), run: () => setActiveView("profile") },
    { id: "view-docs", label: t("Abrir Docs"), detail: t("Manual de uso do produto."), run: () => openDocs() },
    { id: "refresh", label: t("Atualizar workspace"), detail: t("Sincroniza os dados do projeto atual."), run: refreshWorkspace },
    { id: "drift", label: t("Rodar drift"), detail: t("Gera relatorio para o modelo selecionado."), run: runDrift },
    { id: "alerts", label: t("Checar alertas"), detail: t("Avalia regras cadastradas e regras padrao."), run: runAlertChecks },
    { id: "export-predictions", label: t("Exportar predicoes"), detail: t("Cria exportacao CSV do projeto atual."), run: exportPredictions },
    { id: "audit-export", label: t("Exportar auditoria"), detail: t("Gera evidencia JSON dos eventos filtrados."), run: exportAuditEvidence },
    { id: "docs-whatif", label: "Docs: What-if", detail: t("Como simular cenarios no inspector."), run: () => openDocs("whatif") },
    { id: "docs-entities", label: t("Docs: Entidades"), detail: t("Timeline, notas e historico por entidade."), run: () => openDocs("entities") },
    { id: "docs-automation", label: t("Docs: Automacao"), detail: t("Jobs, notificacoes, contratos e views salvas."), run: () => openDocs("automation") },
    { id: "docs-api", label: "Docs: API", detail: t("Como integrar sistemas externos."), run: () => openDocs("api") },
    { id: "docs-governance", label: t("Docs: Governanca"), detail: t("Seguranca, chaves e trilha de auditoria."), run: () => openDocs("governance") },
    { id: "open-tour", label: t("Reabrir tour de boas-vindas"), detail: t("Mostra o tour multi-step novamente."), run: () => setOnboardingOpen(true) },
    { id: "toggle-theme", label: t("Alternar tema"), detail: t("Troca entre claro e escuro (atalho T)."), run: () => toggleTheme() },
    { id: "open-shortcuts", label: t("Ver atalhos de teclado"), detail: t("Modal com todos os atalhos disponiveis."), run: () => setShortcutsOpen(true) }
  ];

  const normalizedCommandQuery = commandQuery.trim().toLowerCase();
  const filteredCommandItems = commandItems
    .filter((item) => {
      if (!normalizedCommandQuery) return true;
      return `${item.label} ${item.detail}`.toLowerCase().includes(normalizedCommandQuery);
    })
    .slice(0, 12);

  useEffect(() => {
    const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (savedLocale === "pt-BR" || savedLocale === "en") setLocale(savedLocale);
    const raw = sessionStorage.getItem("modeltrace_session");
    if (raw) {
      const parsed = JSON.parse(raw);
      setSession(parsed);
      setProfileDraft(profileFromUser(parsed.user || {}));
      refreshProjects(parsed.access_token);
      refreshSecurityPosture(parsed.access_token);
      refreshNotifications(parsed.access_token);
      refreshSavedViews(parsed.access_token);
      if (shouldShowOnboarding()) {
        setOnboardingOpen(true);
      }
    }
    const params = new URLSearchParams(window.location.search);
    const verifyToken = params.get("verify_email_token");
    const resetTokenFromUrl = params.get("reset_token");
    if (verifyToken) {
      void verifyEmailToken(verifyToken);
      params.delete("verify_email_token");
    }
    if (resetTokenFromUrl) {
      setResetOpen(true);
      setResetToken(resetTokenFromUrl);
      params.delete("reset_token");
    }
    if (verifyToken || resetTokenFromUrl) {
      const nextQuery = params.toString();
      window.history.replaceState({}, "", `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}`);
    }
  }, []);

  useEffect(() => {
    setResetEmail(email);
  }, [email]);

  useEffect(() => {
    if (session?.user) setProfileDraft(profileFromUser(session.user));
  }, [session?.user?._id]);

  useEffect(() => {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
    document.documentElement.lang = locale === "pt-BR" ? "pt-BR" : "en";
  }, [locale]);

  useEffect(() => {
    const timer = window.setTimeout(() => translateDocument(document.body, locale), 0);
    return () => window.clearTimeout(timer);
  }, [
    locale,
    session?.user?._id,
    activeView,
    selectedDocId,
    selectedProjectId,
    selectedModelId,
    selectedPredictionId,
    predictionPage,
    predictions.length,
    versions.length,
    projects.length,
    models.length,
    commandOpen,
    notice?.message,
    analysisResult?.type,
    inspectorPanel
  ]);

  useEffect(() => {
    if (selectedProjectId && token) {
      setPredictions([]);
      setPredictionTotal(0);
      setSelectedPredictionId("");
      setPredictionPage(1);
      setDiagnostics(null);
      setSelectedSliceFeature("");
      setWorkbenchErrors([]);
      refreshModels();
      refreshDashboard();
      refreshAudit();
      refreshOperations();
      refreshSecurityPosture();
      refreshApiKeys();
      refreshNotifications();
      refreshJobs();
      refreshSavedViews();
      refreshAlertRules();
      refreshDataContract();
    }
  }, [selectedProjectId, token]);

  useEffect(() => {
    if (selectedModelId && token) {
      setDiagnostics(null);
      setSelectedSliceFeature("");
      setSelectedThreshold(Number(selectedModel?.default_threshold ?? 0.7));
      setWorkbenchErrors([]);
      refreshVersions();
    }
  }, [selectedModelId, token]);

  useEffect(() => {
    if (!availableBiasFeatures.includes(biasFeature)) {
      setBiasFeature(availableBiasFeatures[0] || "signal_value");
    }
  }, [availableBiasFeatures, biasFeature]);

  useEffect(() => {
    if (!versions.length) return;
    if (!versions.some((version) => version.version === simWindow)) {
      setSimWindow((productionVersion || versions[0])?.version || "");
    }
  }, [versions, simWindow, productionVersion]);

  useEffect(() => {
    setPredictionPage(1);
  }, [debouncedQuery, labelFilter, windowFilter, feedbackFilter, selectedModelId]);

  useEffect(() => {
    setInspectorPanel(null);
    setFeedbackOutcome("positive");
    setFeedbackSource("manual_review");
    setFeedbackNotes("");
    setWhatIfValues(buildWhatIfPreset("current"));
  }, [selectedPrediction?._id]);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (notice) {
      const timer = window.setTimeout(() => setNotice(null), 15000);
      return () => window.clearTimeout(timer);
    }
  }, [notice]);

  useKeyboardShortcuts({
    enabled: Boolean(session) && !commandOpen,
    onCommandPalette: () => {
      setNotificationsOpen(false);
      setShortcutsOpen(false);
      setCommandOpen(true);
    },
    onNotifications: () => {
      setCommandOpen(false);
      setShortcutsOpen(false);
      setNotificationsOpen(true);
      void refreshNotifications(token);
    },
    onShortcutsHelp: () => {
      setCommandOpen(false);
      setNotificationsOpen(false);
      setShortcutsOpen(true);
    },
    onRefresh: () => {
      void refreshWorkspace();
    },
    onLogout: () => {
      void logout();
    },
    onNavigate: (viewId) => {
      setCommandOpen(false);
      setNotificationsOpen(false);
      setShortcutsOpen(false);
      setActiveView(viewId);
    },
    onToggleTheme: () => {
      toggleTheme();
    }
  });

  async function markNotificationRead(notificationId: string) {
    if (!token || !notificationId) return false;
    const response = await apiRequest<AnyDoc>(
      `/notifications/${notificationId}`,
      {
        method: "PATCH",
        body: JSON.stringify({ read: true })
      },
      token
    );
    if (response.error) return false;
    setNotifications((current) =>
      current.map((item) => {
        const id = item._id ?? item.id;
        if (id !== notificationId) return item;
        return { ...item, read: true, read_at: response.data?.read_at ?? new Date().toISOString() };
      })
    );
    setNotificationUnread((value) => Math.max(0, value - 1));
    return true;
  }

  async function markAllNotificationsRead() {
    if (!token) return;
    const response = await apiRequest<{ updated: number }>(
      "/notifications/mark-all-read",
      { method: "POST" },
      token
    );
    if (response.error) {
      notify("Falha ao marcar notificacoes.", "error");
      return;
    }
    const now = new Date().toISOString();
    setNotifications((current) =>
      current.map((item) => ({ ...item, read: true, read_at: item.read_at ?? now }))
    );
    setNotificationUnread(0);
    notify(
      response.data?.updated
        ? `${response.data.updated} notificacoes marcadas como lidas.`
        : "Tudo em dia.",
      "success"
    );
    void refreshNotifications(token);
  }

  async function runChampionChallenger(championVersion: string, challengerVersion: string) {
    if (!selectedModelId || !token) {
      notify("Selecione um modelo antes de comparar.", "error");
      return;
    }
    if (!championVersion || !challengerVersion) {
      notify("Escolha as duas versoes para comparar.", "error");
      return;
    }
    if (championVersion === challengerVersion) {
      notify("Champion e challenger precisam ser versoes diferentes.", "error");
      return;
    }
    setComparisonLoading(true);
    const params = new URLSearchParams({ a: championVersion, b: challengerVersion }).toString();
    const result = await apiRequest<AnyDoc>(
      `/models/${selectedModelId}/versions/compare?${params}`,
      { method: "GET" },
      token
    );
    setComparisonLoading(false);
    if (result.error) {
      notify(`Falha ao comparar versoes: ${result.error}`, "error");
      return;
    }
    setComparisonResult(result.data ?? null);
    notify(`Comparacao ${championVersion} vs ${challengerVersion} pronta.`, "success");
  }

  async function promoteChallenger(challengerVersion: string) {
    if (!selectedModelId || !token || !challengerVersion) return;
    const previousChampion =
      (comparisonResult?.version_a as AnyDoc | undefined)?.metadata?.version ?? "";
    if (typeof window !== "undefined") {
      const confirmed = window.confirm(
        `Promover ${challengerVersion} para production? A versao atualmente em production sera marcada como deprecated.`
      );
      if (!confirmed) return;
    }
    const result = await apiRequest<AnyDoc>(
      `/models/${selectedModelId}/versions/${encodeURIComponent(challengerVersion)}/promote`,
      { method: "POST" },
      token
    );
    if (result.error) {
      notify(`Falha ao promover: ${result.error}`, "error");
      return;
    }
    if (result.data?.noop) {
      notify("Esta versao ja esta em production.", "info");
    } else {
      notify(`${challengerVersion} promovida. Anterior: ${result.data?.previous_version ?? "—"}.`, "success");
    }
    await refreshWorkspace();
    if (previousChampion) {
      await runChampionChallenger(challengerVersion, previousChampion);
    }
  }

  function handleNotificationSelect(notification: AnyDoc) {
    const id = String(notification?._id ?? notification?.id ?? "");
    const wasUnread = !notification?.read && !notification?.read_at;
    if (id && wasUnread) {
      void markNotificationRead(id);
    }
    const resourceType = String(notification?.resource_type || "").toLowerCase();
    if (resourceType === "alert" || resourceType === "incident") {
      goToSection("operations", "active-alerts", "Notificacao aberta na fila operacional.");
    } else if (resourceType === "prediction") {
      openPredictions();
    } else if (resourceType === "job") {
      goToSection("control", "jobs", "Job aberto na automacao.");
    } else if (resourceType === "intervention_case" || resourceType === "case") {
      setActiveView("cases");
    } else {
      setActiveView("control");
    }
    setNotificationsOpen(false);
  }

  useEffect(() => {
    if (activeView === "predictions" && selectedProjectId && token) {
      refreshPredictions(token, predictionPage);
    }
  }, [
    activeView,
    selectedProjectId,
    selectedModelId,
    labelFilter,
    windowFilter,
    feedbackFilter,
    debouncedQuery,
    predictionPage,
    predictionPageSize,
    token
  ]);

  useEffect(() => {
    if (activeView === "lab" && selectedModelId && token) {
      refreshDiagnostics(selectedModelId, token, selectedSliceFeature);
    }
  }, [activeView, selectedModelId, selectedSliceFeature, token]);

  useEffect(() => {
    if (activeView === "drift" && selectedModelId && token) {
      void refreshDriftHeatmap(selectedModelId, token);
    }
  }, [activeView, selectedModelId, token]);

  useEffect(() => {
    if (activeView === "cases" && selectedProjectId && token) {
      void refreshOperations(selectedProjectId, token);
    }
  }, [activeView, selectedProjectId, token]);

  useEffect(() => {
    if (activeView === "usage" && token) {
      void refreshUsage(usagePeriodDays, token);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeView, token]);

  if (!session) {
    return (
      <AuthScreen
        locale={locale}
        onLocaleChange={setLocale}
        email={email}
        password={password}
        name={name}
        organizationName={organizationName}
        jobTitle={jobTitle}
        department={department}
        company={company}
        phone={phone}
        timezone={timezone}
        bio={bio}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onNameChange={setName}
        onOrganizationChange={setOrganizationName}
        onJobTitleChange={setJobTitle}
        onDepartmentChange={setDepartment}
        onCompanyChange={setCompany}
        onPhoneChange={setPhone}
        onTimezoneChange={setTimezone}
        onBioChange={setBio}
        passwordChecks={passwordChecks}
        passwordReadyForRegister={passwordReadyForRegister}
        resetOpen={resetOpen}
        onToggleReset={() => setResetOpen((value) => !value)}
        resetEmail={resetEmail}
        resetToken={resetToken}
        resetPassword={resetPassword}
        onResetEmailChange={setResetEmail}
        onResetTokenChange={setResetToken}
        onResetPasswordChange={setResetPassword}
        resetPasswordChecks={resetPasswordChecks}
        resetPasswordReady={resetPasswordReady}
        status={status}
        notice={notice}
        onCloseNotice={() => setNotice(null)}
        onLogin={login}
        onRegister={register}
        onRequestPasswordReset={() => requestPasswordReset()}
        onConfirmPasswordReset={confirmPasswordReset}
      />
    );
  }

  return (
    <main className="app-shell">
      <Sidebar
        navItems={localizedNavItems}
        activeView={activeView}
        onSelect={setActiveView}
        projects={projects}
        models={models}
        selectedProjectId={selectedProjectId}
        selectedModelId={selectedModelId}
        onProjectChange={setSelectedProjectId}
        onModelChange={setSelectedModelId}
        apiUrl={API_URL}
        locale={locale}
      />

      <section className="workspace">
        <Topbar
          domain={selectedProject?.domain}
          title={projectName}
          description={projectDescription}
          notificationsUnread={notificationUnread}
          locale={locale}
          onLocaleChange={setLocale}
          onCommandPalette={() => setCommandOpen(true)}
          onNotifications={() => {
            setNotificationsOpen(true);
            void refreshNotifications(token);
          }}
          onRefresh={refreshWorkspace}
          onLogout={logout}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        <div className="status-ribbon">
          <span>{status}</span>
          <strong>{session.user.email}</strong>
        </div>

        <SlaAlertBar
          cases={interventionCases as AnyDoc[]}
          currentView={activeView}
          onGoToCases={() => setActiveView("cases")}
        />

        {notice && (
          <Toast
            tone={notice.tone}
            message={notice.message}
            onClose={() => setNotice(null)}
          />
        )}

        <CommandPalette
          open={commandOpen}
          items={filteredCommandItems as PaletteItem[]}
          query={commandQuery}
          onQueryChange={setCommandQuery}
          onClose={() => {
            setCommandOpen(false);
            setCommandQuery("");
          }}
        />

        <NotificationsDrawer
          open={notificationsOpen}
          notifications={notifications}
          unreadCount={notificationUnread}
          onClose={() => setNotificationsOpen(false)}
          onMarkAllRead={markAllNotificationsRead}
          onSelect={handleNotificationSelect}
        />

        <ShortcutsModal open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />

        <OnboardingTour
          open={onboardingOpen}
          onDismiss={() => {
            dismissOnboarding();
            setOnboardingOpen(false);
          }}
          onNavigate={(viewId) => {
            setActiveView(viewId);
          }}
        />

        {activeView === "overview" && (
          <OverviewView
            healthScore={healthScore}
            healthParts={healthBreakdown.parts as any}
            insightRows={insightRows as any}
            kpis={kpis}
            actionableRate={actionableRate}
            dashboard={dashboard}
            confusion={confusion}
            versions={versions}
            productionVersion={productionVersion}
            selectedModelPrimaryMetric={selectedModel?.primary_metric}
            positiveLabel={positiveLabel}
            formatNumber={fmt}
            formatPercent={percent}
            onOpenPredictions={openPredictions}
            onGoToSection={goToSection}
          />
        )}

        {activeView === "compare" && (
          <ChampionChallengerView
            versions={versions}
            selectedModelId={selectedModelId}
            result={comparisonResult as any}
            loading={comparisonLoading}
            onRunComparison={runChampionChallenger}
            onPromote={promoteChallenger}
            formatNumber={fmt}
            formatPercent={percent}
          />
        )}

        {activeView === "drift" && (
          <DriftHeatmapView
            data={driftHeatmap as any}
            loading={driftHeatmapLoading}
            selectedModelId={selectedModelId}
            onRefresh={() => refreshDriftHeatmap()}
            onRunDrift={runDrift}
          />
        )}

        {activeView === "cases" && (
          <SlaKanbanView
            cases={interventionCases as AnyDoc[]}
            loading={!operationsData}
            onUpdateStatus={(caseId: string, nextStatus: CaseStatus) =>
              updateCaseStatus(caseId, nextStatus)
            }
            onOpenEntity={(entityId: string) => {
              setEntityQuery(entityId);
              setActiveView("entities");
            }}
            formatNumber={fmt}
          />
        )}

        {activeView === "usage" && (
          <CostUsageView
            data={usageData}
            loading={usageLoading}
            periodDays={usagePeriodDays}
            onPeriodChange={changeUsagePeriod}
            onRefresh={() => refreshUsage()}
            formatNumber={fmt}
          />
        )}

        {activeView === "monitor" && (
          <section className="view-stack">
            <div className="action-strip">
              <button onClick={refreshMonitor}><RefreshCcw size={17} />Atualizar monitor</button>
              <button className="secondary" onClick={createApiKey}><KeyRound size={17} />Gerar API key</button>
              <button className="secondary" onClick={compareVersions}><GitCompare size={17} />Comparar versoes</button>
              <button className="secondary" onClick={runDrift}><Activity size={17} />Rodar drift</button>
              <button className="secondary" onClick={runBiasAnalysis}><ShieldCheck size={17} />Equidade</button>
              <button className="secondary" onClick={exportPredictions}><Download size={17} />Exportar CSV</button>
            </div>

            <div className="monitor-grid">
              <section className="surface">
                <div className="section-heading split">
                  <div className="section-title-row">
                    <Layers3 size={18} />
                    <h2>Versoes do modelo</h2>
                  </div>
                  <select value={biasFeature} onChange={(event) => setBiasFeature(event.target.value)} aria-label="Feature de equidade">
                    {availableBiasFeatures.map((feature) => (
                      <option key={feature} value={feature}>{feature}</option>
                    ))}
                  </select>
                </div>
                <div className="version-list">
                  {versions.map((version) => (
                    <div key={version._id} className={version.status === "production" ? "production" : ""}>
                      <strong>{version.version}</strong>
                      <span>{version.status} / {version.algorithm}</span>
                      <small>Metrica {fmt(version.offline_metrics?.f2 ?? version.offline_metrics?.pr_auc ?? version.offline_metrics?.average_precision ?? version.offline_metrics?.threshold_top10 ?? version.offline_metrics?.recall)}</small>
                    </div>
                  ))}
                  {!versions.length && <EmptyState text="Sem versoes." />}
                </div>
              </section>

              <section className="surface">
                <div className="section-heading">
                  <Archive size={18} />
                  <h2>Workspace</h2>
                </div>
                {selectedProject ? (
                  <div className="project-summary">
                    <div>
                      <span>Projeto</span>
                      <strong>{localizedField(selectedProject, "name", locale)}</strong>
                    </div>
                    <div>
                      <span>Dominio</span>
                      <strong>{selectedProject.domain}</strong>
                    </div>
                    <div>
                      <span>Modelos ativos</span>
                      <strong>{fmt(models.length)}</strong>
                    </div>
                    <div>
                      <span>Predicoes</span>
                      <strong>{fmt(kpis.total_predictions ?? selectedProject.stats?.total_predictions ?? 0)}</strong>
                    </div>
                    <p>{localizedField(selectedProject, "description", locale)}</p>
                    <p>Operacao com coortes, qualidade, incidentes e auditoria.</p>
                  </div>
                ) : (
                  <EmptyState text="Escolha um projeto." />
                )}
              </section>
            </div>

            {analysisResult && <AnalysisBlock data={analysisResult} />}
          </section>
        )}

        {activeView === "lab" && (
          <section className="view-stack">
            <div className="action-strip">
              <button onClick={refreshDiagnosticsWithToast}><RefreshCcw size={17} />Atualizar DS Lab</button>
              <button className="secondary" onClick={runDrift}><Activity size={17} />Drift</button>
              <button className="secondary" onClick={runBiasAnalysis}><ShieldCheck size={17} />Equidade</button>
              <button className="secondary" onClick={exportDiagnosticsPack}><Download size={17} />Exportar pacote</button>
            </div>

            <section className="surface lab-command">
              <div className="section-heading split">
                <div>
                  <div className="section-title-row">
                    <BarChart3 size={18} />
                    <h2>DS Lab</h2>
                  </div>
                  <p>{modelName} / {projectName || t("projeto atual")}</p>
                </div>
                <span className={`lab-status ${diagnosticsLoading ? "loading" : "ready"}`}>
                  {diagnosticsLoading ? "processando" : "pronto"}
                </span>
              </div>
              <div className="metric-grid">
                <Metric label="Amostra" value={fmt(diagnosticSummary.prediction_count ?? 0)} icon={<Database size={18} />} />
                <Metric label="Feedback" value={percent(diagnosticSummary.feedback_rate)} icon={<CheckCircle2 size={18} />} tone="good" />
                <Metric label="Threshold F2" value={fmt(diagnosticSummary.recommended_threshold ?? selectedModel?.default_threshold ?? 0.7)} icon={<Gauge size={18} />} />
                <Metric label="ECE" value={fmt(diagnosticSummary.ece ?? 0)} icon={<Activity size={18} />} tone={(diagnosticSummary.ece ?? 0) >= 0.08 ? "warn" : "good"} />
                <Metric label="Brier" value={fmt(diagnosticSummary.brier_score ?? 0)} icon={<LineChartIcon size={18} />} />
              </div>
            </section>

            <div className="lab-grid">
              <section className="surface chart-surface">
                <div className="section-heading split">
                  <div className="section-title-row">
                    <LineChartIcon size={18} />
                    <h2>Otimizacao de threshold</h2>
                  </div>
                  <div className="chart-legend">
                    <span className="cyan">F2</span>
                    <span className="green">recall</span>
                    <span className="amber">precision</span>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={thresholdCurve}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#253244" />
                    <XAxis dataKey="threshold" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" domain={[0, 1]} />
                    <Tooltip
                      cursor={{ stroke: "#00d4ff", strokeOpacity: 0.22 }}
                      contentStyle={{ background: "#121822", border: "1px solid #253244", color: "#eef4f8" }}
                      labelStyle={{ color: "#eef4f8" }}
                    />
                    <Line type="monotone" dataKey="f2" stroke="#00d4ff" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="recall" stroke="#00c88c" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="precision" stroke="#f5b642" strokeWidth={2} dot={false} />
                    {selectedThresholdRow ? (
                      <>
                        <ReferenceLine
                          x={selectedThresholdRow.threshold}
                          stroke="#eef4f8"
                          strokeDasharray="4 4"
                          strokeOpacity={0.55}
                        />
                        {selectedThresholdRow.f2 !== null && selectedThresholdRow.f2 !== undefined ? (
                          <ReferenceDot x={selectedThresholdRow.threshold} y={selectedThresholdRow.f2} r={4} fill="#00d4ff" stroke="#081018" strokeWidth={2} />
                        ) : null}
                        {selectedThresholdRow.recall !== null && selectedThresholdRow.recall !== undefined ? (
                          <ReferenceDot x={selectedThresholdRow.threshold} y={selectedThresholdRow.recall} r={4} fill="#00c88c" stroke="#081018" strokeWidth={2} />
                        ) : null}
                        {selectedThresholdRow.precision !== null && selectedThresholdRow.precision !== undefined ? (
                          <ReferenceDot x={selectedThresholdRow.threshold} y={selectedThresholdRow.precision} r={4} fill="#f5b642" stroke="#081018" strokeWidth={2} />
                        ) : null}
                      </>
                    ) : null}
                  </LineChart>
                </ResponsiveContainer>
              </section>

              <section className="surface threshold-panel">
                <div className="section-heading">
                  <Gauge size={18} />
                  <h2>Simulador de threshold</h2>
                </div>
                <div className="threshold-readout">
                  <strong>{selectedThreshold.toFixed(2)}</strong>
                  <span>threshold</span>
                </div>
                <input
                  className="threshold-slider"
                  type="range"
                  min="0.05"
                  max="0.95"
                  step="0.05"
                  value={selectedThreshold}
                  onChange={(event) => setSelectedThreshold(Number(event.target.value))}
                />
                <div className="threshold-metrics">
                  <div><span>Precision</span><strong>{percent(selectedThresholdRow?.precision)}</strong></div>
                  <div><span>Recall</span><strong>{percent(selectedThresholdRow?.recall)}</strong></div>
                  <div><span>F2</span><strong>{percent(selectedThresholdRow?.f2)}</strong></div>
                  <div><span>Workload</span><strong>{percent(selectedThresholdRow?.workload_rate)}</strong></div>
                </div>
              </section>
            </div>

            <div className="lab-grid">
              <section className="surface chart-surface">
                <div className="section-heading">
                  <Activity size={18} />
                  <h2>Calibracao</h2>
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={diagnostics?.calibration?.bins || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#253244" />
                    <XAxis dataKey="bucket" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" domain={[0, 1]} />
                    <Tooltip
                      cursor={{ stroke: "#00d4ff", strokeOpacity: 0.22 }}
                      contentStyle={{ background: "#121822", border: "1px solid #253244", color: "#eef4f8" }}
                      labelStyle={{ color: "#eef4f8" }}
                    />
                    <Line type="monotone" dataKey="avg_score" stroke="#00d4ff" strokeWidth={2} />
                    <Line type="monotone" dataKey="observed_rate" stroke="#00c88c" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </section>

              <section className="surface">
                <div className="section-heading">
                  <Sparkles size={18} />
                  <h2>Prioridades de analise</h2>
                </div>
                <div className="action-list">
                  {(diagnostics?.recommendations?.actions || []).map((item: AnyDoc) => (
                    <div key={item.title} className={item.severity}>
                      <span>{item.severity}</span>
                      <strong>{localizedField(item, "title", locale)}</strong>
                      <small>{localizedField(item, "detail", locale)}</small>
                    </div>
                  ))}
                  {!diagnostics && <EmptyState text="Escolha um modelo para ver diagnosticos." />}
                </div>
              </section>
            </div>

            <div className="lab-grid">
              <section className="surface">
                <div className="section-heading">
                  <BarChart3 size={18} />
                  <h2>Feature intelligence</h2>
                </div>
                <div className="feature-impact-list">
                  {(diagnostics?.feature_importance || []).slice(0, 10).map((item: AnyDoc) => (
                    <div key={item.feature}>
                      <span>{item.feature}</span>
                      <strong>{fmt(item.avg_abs_impact)}</strong>
                      <em style={{ width: `${Math.min(100, Number(item.avg_abs_impact || 0) * 100)}%` }} />
                    </div>
                  ))}
                  {!diagnostics?.feature_importance?.length && <EmptyState text="Sem dados de explicabilidade." />}
                </div>
              </section>

              <section className="surface">
                <div className="section-heading">
                  <Database size={18} />
                  <h2>Contrato de features</h2>
                </div>
                <div className="coverage-list">
                  {(diagnostics?.feature_coverage || []).slice(0, 12).map((item: AnyDoc) => (
                    <div key={item.feature}>
                      <strong>{item.feature}</strong>
                      <span>{item.type} / {item.required ? "obrigatoria" : "opcional"}</span>
                      <em>{percent(item.coverage)}</em>
                    </div>
                  ))}
                  {!diagnostics?.feature_coverage?.length && <EmptyState text="Contrato nao definido." />}
                </div>
              </section>
            </div>

            <section className="surface">
              <div className="section-heading split">
                <div className="section-title-row">
                  <ShieldCheck size={18} />
                  <h2>Diagnostico por segmento</h2>
                </div>
                <select value={selectedSliceFeature} onChange={(event) => setSelectedSliceFeature(event.target.value)} aria-label="Feature para slice diagnostics">
                  {(diagnostics?.slice_candidates || []).map((item: AnyDoc) => (
                    <option key={item.feature} value={item.feature}>{item.feature}</option>
                  ))}
                </select>
              </div>
              <div className="table-wrap compact-table">
                <table>
                  <thead>
                    <tr>
                      <th>Grupo</th>
                      <th>Total</th>
                      <th>Score medio</th>
                      <th>Acionavel</th>
                      <th>Feedback</th>
                      <th>Precision</th>
                      <th>Recall</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(diagnostics?.slice_diagnostics || []).map((row: AnyDoc) => (
                      <tr key={row.group}>
                        <td>{row.group}</td>
                        <td>{fmt(row.total)}</td>
                        <td>{fmt(row.avg_score)}</td>
                        <td>{percent(row.positive_rate)}</td>
                        <td>{fmt(row.feedback)}</td>
                        <td>{percent(row.precision)}</td>
                        <td>{percent(row.recall)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <div className="lab-grid">
              <ErrorList title="Falsos positivos prioritarios" rows={diagnostics?.error_analysis?.false_positives || []} />
              <ErrorList title="Falsos negativos prioritarios" rows={diagnostics?.error_analysis?.false_negatives || []} />
            </div>
          </section>
        )}

        {activeView === "predictions" && (
          <section className="prediction-layout">
            <section className="surface prediction-table-surface">
              <div className="section-heading split">
                <div>
                  <div className="section-title-row">
                    <Database size={18} />
                    <h2>Historico de predicoes</h2>
                  </div>
                  <p>
                    {fmt(predictions.length)} de {fmt(totalVisiblePredictions)} resultados.
                  </p>
                </div>
                <button onClick={sendDemoPrediction}><Send size={17} />Registrar predicao</button>
                <button className="secondary" onClick={saveCurrentPredictionView}><Archive size={17} />Salvar view</button>
              </div>

              <div className="prediction-facts">
                {predictionWindowStats.map((item) => (
                  <div key={item.window}>
                    <span>{item.window}</span>
                    <strong>{fmt(item.entities)} {entityLabel}</strong>
                    <small>{fmt(item.predictions)} predicoes / {fmt(item.feedback)} com desfecho</small>
                  </div>
                ))}
                <div>
                  <span>Resultado</span>
                  <strong>{fmt(totalVisiblePredictions)} predicoes</strong>
                  <small>{predictionsLoading ? "carregando" : "paginado"}</small>
                </div>
              </div>

              <div className="filter-bar">
                <label className="search-field">
                  <Search size={16} />
                  <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar ID, entidade ou label" />
                </label>
                <select value={labelFilter} onChange={(event) => setLabelFilter(event.target.value)}>
                  <option value="all">Todos os labels</option>
                  <option value={positiveLabel}>{positiveLabel}</option>
                  <option value={negativeLabel}>{negativeLabel}</option>
                </select>
                <select value={windowFilter} onChange={(event) => setWindowFilter(event.target.value)}>
                  <option value="all">Todas janelas</option>
                  {predictionVersionOptions.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
                <select value={feedbackFilter} onChange={(event) => setFeedbackFilter(event.target.value)} aria-label="Filtro de feedback">
                  <option value="all">Todos</option>
                  <option value="with">Com desfecho</option>
                  <option value="pending">Pendentes</option>
                </select>
                <select
                  value={predictionPageSize}
                  onChange={(event) => {
                    setPredictionPageSize(Number(event.target.value));
                    setPredictionPage(1);
                  }}
                  aria-label="Predicoes por pagina"
                  title="Predicoes por pagina"
                >
                  {PREDICTION_PAGE_SIZE_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>{opt} por pagina</option>
                  ))}
                </select>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Entidade</th>
                      <th>Versao</th>
                      <th>Label</th>
                      <th>Score</th>
                      <th>Feedback</th>
                      <th>Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pagedPredictions.map((prediction) => (
                      <tr
                        key={prediction._id}
                        className={selectedPrediction?._id === prediction._id ? "selected" : ""}
                        onClick={() => setSelectedPredictionId(prediction._id)}
                      >
                        <td>{prediction._id}</td>
                        <td>
                          <div className="entity-cell">
                            <strong>{predictionEntityName(prediction)}</strong>
                            {predictionEntityId(prediction) && <small>{predictionEntityId(prediction)}</small>}
                          </div>
                        </td>
                        <td>{prediction.model_version}</td>
                        <td><span className={`badge ${prediction.prediction?.label}`}>{prediction.prediction?.label}</span></td>
                        <td>{prediction.prediction?.score}</td>
                        <td>{prediction.feedback?.classification_result || "Pendente"}</td>
                        <td>{prediction.created_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="pagination-bar">
                <span>
                  Pagina {fmt(Math.min(predictionPage, predictionPageCount))} / {fmt(predictionPageCount)}
                  {" - "}{fmt(pagedPredictions.length)} de {fmt(totalVisiblePredictions)} resultados
                </span>
                <div>
                  <button
                    className="secondary"
                    disabled={predictionPage <= 1}
                    onClick={() => setPredictionPage((page) => Math.max(1, page - 1))}
                  >
                    Anterior
                  </button>
                  <button
                    className="secondary"
                    disabled={predictionPage >= predictionPageCount}
                    onClick={() => setPredictionPage((page) => Math.min(predictionPageCount, page + 1))}
                  >
                    Proxima
                  </button>
                </div>
              </div>
            </section>

            <aside className="surface inspector">
              <div className="section-heading">
                <ShieldCheck size={18} />
                <h2>Decision inspector</h2>
              </div>
              {selectedPrediction ? (
                <>
                  <div className="decision-head">
                    <span>{selectedPrediction._id}</span>
                    <strong>{predictionEntityName(selectedPrediction)}</strong>
                    {predictionEntityId(selectedPrediction) && <small>{predictionEntityId(selectedPrediction)}</small>}
                    <em>{selectedPrediction.model_version}</em>
                  </div>
                  <div className="score-bar">
                    <div style={{ width: `${Math.min(100, (selectedPrediction.prediction?.score || 0) * 100)}%` }} />
                  </div>
                  <div className="inspector-actions">
                    <button onClick={openFeedbackPanel}><CheckCircle2 size={16} />Feedback</button>
                    <button className="secondary" onClick={openWhatIfPanel}><Sparkles size={16} />What-if</button>
                    <button className="secondary" onClick={runReplay}><GitCompare size={16} />Replay</button>
                    <button className="secondary" onClick={exportPredictions}><Download size={16} />Exportar</button>
                  </div>
                  {inspectorPanel === "feedback" ? (
                    <div className="inspector-panel">
                      <div className="section-heading compact">
                        <h2>Registrar feedback</h2>
                      </div>
                      <div className="segmented-control">
                        <button type="button" className={feedbackOutcome === "positive" ? "active" : "secondary"} onClick={() => setFeedbackOutcome("positive")}>
                          Positivo
                        </button>
                        <button type="button" className={feedbackOutcome === "negative" ? "active" : "secondary"} onClick={() => setFeedbackOutcome("negative")}>
                          Negativo
                        </button>
                        <button type="button" className={feedbackOutcome === "inconclusive" ? "active" : "secondary"} onClick={() => setFeedbackOutcome("inconclusive")}>
                          Inconclusivo
                        </button>
                      </div>
                      <div className="inspector-form">
                        <label>
                          Origem
                          <input value={feedbackSource} onChange={(event) => setFeedbackSource(event.target.value)} />
                        </label>
                        <label>
                          Nota
                          <textarea rows={3} value={feedbackNotes} onChange={(event) => setFeedbackNotes(event.target.value)} placeholder="Opcional" />
                        </label>
                      </div>
                      <div className="inline-actions">
                        <button type="button" onClick={submitFeedbackToSelectedPrediction}>Salvar feedback</button>
                        <button type="button" className="secondary" onClick={() => setInspectorPanel(null)}>Cancelar</button>
                      </div>
                    </div>
                  ) : null}
                  {inspectorPanel === "what-if" ? (
                    <div className="inspector-panel">
                      <div className="section-heading compact">
                        <h2>Cenario what-if</h2>
                      </div>
                      <div className="inline-actions preset-actions">
                        <button type="button" className="secondary" onClick={() => setWhatIfValues(buildWhatIfPreset("optimistic"))}>Otimista</button>
                        <button type="button" className="secondary" onClick={() => setWhatIfValues(buildWhatIfPreset("conservative"))}>Conservador</button>
                        <button type="button" className="secondary" onClick={() => setWhatIfValues(buildWhatIfPreset("current"))}>Reset</button>
                      </div>
                      <div className="whatif-grid">
                        {Object.entries(whatIfValues).map(([feature, value]) => {
                          const original = selectedPrediction.features?.[feature];
                          return (
                            <label key={feature}>
                              {feature}
                              {typeof original === "boolean" ? (
                                <select value={value} onChange={(event) => setWhatIfValues((current) => ({ ...current, [feature]: event.target.value }))}>
                                  <option value="true">true</option>
                                  <option value="false">false</option>
                                </select>
                              ) : (
                                <input
                                  type={typeof original === "number" ? "number" : "text"}
                                  step={typeof original === "number" ? "0.01" : undefined}
                                  value={value}
                                  onChange={(event) => setWhatIfValues((current) => ({ ...current, [feature]: event.target.value }))}
                                />
                              )}
                            </label>
                          );
                        })}
                      </div>
                      <div className="inline-actions">
                        <button type="button" onClick={submitWhatIfScenario}>Simular cenario</button>
                        <button type="button" className="secondary" onClick={() => setInspectorPanel(null)}>Fechar</button>
                      </div>
                    </div>
                  ) : null}
                  <div className="feature-list">
                    {(selectedPrediction.explanations || []).slice(0, 5).map((row: AnyDoc) => (
                      <div key={row.feature}>
                        <span>{row.feature}</span>
                        <strong>{row.impact}</strong>
                      </div>
                    ))}
                  </div>
                  {analysisResult && <AnalysisBlock data={analysisResult} compact />}
                  <PredictionTechnicalDetails prediction={selectedPrediction} />
                </>
              ) : (
                <EmptyState text="Selecione uma predicao." />
              )}
            </aside>
          </section>
        )}

        {activeView === "entities" && (
          <section className="view-stack">
            <section className="surface">
              <div className="section-heading split">
                <div>
                  <div className="section-title-row">
                    <Search size={18} />
                    <h2>Entidades</h2>
                  </div>
                  <p>Pesquise aluno, cliente, ativo, empresa ou qualquer entidade monitorada e veja a linha do tempo operacional.</p>
                </div>
                <button onClick={searchEntityTimeline}><Search size={17} />Pesquisar</button>
              </div>
              <div className="filter-bar">
                <label className="search-field">
                  <Search size={16} />
                  <input value={entityQuery} onChange={(event) => setEntityQuery(event.target.value)} placeholder="Nome, matricula, ID ou entidade" />
                </label>
                <button type="button" className="secondary" onClick={() => {
                  const id = predictionEntityId(selectedPrediction);
                  if (id) {
                    setEntityQuery(id);
                    setActiveView("entities");
                  }
                }}>
                  Usar entidade selecionada
                </button>
              </div>
            </section>

            {entityTimeline && (
              <section className="entity-grid">
                <section className="surface">
                  <div className="section-heading">
                    <Database size={18} />
                    <h2>Resumo da entidade</h2>
                  </div>
                  <div className="metric-grid">
                    <Metric label="Predicoes" value={fmt(entityTimeline.predictions?.length || 0)} icon={<Database size={18} />} />
                    <Metric label="Casos" value={fmt(entityTimeline.cases?.length || 0)} icon={<Archive size={18} />} tone="warn" />
                    <Metric label="Replays" value={fmt(entityTimeline.replays?.length || 0)} icon={<GitCompare size={18} />} />
                    <Metric label="Notas" value={fmt(entityTimeline.notes?.length || 0)} icon={<BookOpen size={18} />} />
                    <Metric label="Eventos" value={fmt(entityTimeline.events?.length || 0)} icon={<Activity size={18} />} tone="good" />
                  </div>
                  <div className="timeline entity-timeline">
                    {(entityTimeline.events || []).map((event: AnyDoc, index: number) => (
                      <div key={`${event.type}-${event.item?._id || index}`}>
                        <strong>{event.type} / {event.title || "evento"}</strong>
                        <span>{event.item?.prediction?.label || event.item?.status || event.item?.content || event.item?._id}</span>
                        <small>{event.created_at}</small>
                      </div>
                    ))}
                    {!entityTimeline.events?.length && <EmptyState text="Nenhum evento para esta entidade." />}
                  </div>
                </section>
                <section className="surface">
                  <div className="section-heading">
                    <BookOpen size={18} />
                    <h2>Notas da entidade</h2>
                  </div>
                  <label>
                    Nova nota
                    <textarea rows={5} value={entityNote} onChange={(event) => setEntityNote(event.target.value)} />
                  </label>
                  <button type="button" onClick={saveEntityNote}><CheckCircle2 size={17} />Salvar nota</button>
                  <div className="action-list">
                    {(entityTimeline.notes || []).map((note: AnyDoc) => (
                      <div key={note._id}>
                        <strong>{note.content}</strong>
                        <small>{note.created_at}</small>
                      </div>
                    ))}
                  </div>
                </section>
              </section>
            )}
          </section>
        )}

        {activeView === "operations" && (
          <section className="view-stack">
            <section className="surface ops-command">
              <div className="section-heading split">
                <div>
                  <div className="section-title-row">
                    <AlertTriangle size={18} />
                  <h2>Centro operacional</h2>
                  </div>
                  <p>Casos, alertas, qualidade e incidentes.</p>
                </div>
                <div className="inline-actions section-actions">
                  <button className="secondary" onClick={refreshOperationsWithToast}><RefreshCcw size={17} />Atualizar</button>
                  <button className="secondary" onClick={runAlertChecks}><Zap size={17} />Checar alertas</button>
                </div>
              </div>
              <div className="metric-grid">
                <Metric label="Casos abertos" value={fmt(operationSummary.open_cases ?? 0)} icon={<Archive size={18} />} tone="warn" />
                <Metric label="Criticos" value={fmt(operationSummary.critical_cases ?? 0)} icon={<AlertTriangle size={18} />} tone="bad" />
                <Metric label="Feedback pendente" value={fmt(operationSummary.pending_feedback ?? 0)} icon={<Database size={18} />} />
                <Metric label="Alertas ativos" value={fmt(operationSummary.active_alerts ?? alerts.length)} icon={<Zap size={18} />} tone="warn" onClick={() => goToSection("operations", "active-alerts", "Alertas ativos.")} />
                <Metric label="Modelos avaliados" value={fmt(operationSummary.models_evaluated ?? 0)} icon={<Layers3 size={18} />} tone="good" />
              </div>
            </section>

            <section className="ops-grid">
              <section className="surface alert-surface" id="active-alerts">
                <div className="section-heading">
                  <Zap size={18} />
                  <h2>Alertas ativos</h2>
                </div>
                <div className="alert-list">
                  {alerts.map((alert: AnyDoc) => {
                    const destination = alertDestination(alert);
                    return (
                      <button
                        type="button"
                        key={alert._id}
                        className={`alert-card ${alert.severity || "medium"}`}
                        onClick={() => goToSection("operations", destination.id, `${t("Alerta:")} ${localizedField(alert, "title", locale)}. ${t(destination.label)}.`)}
                      >
                        <span>{alert.severity || "medium"}</span>
                        <div>
                          <strong>{localizedField(alert, "title", locale)}</strong>
                          <small>{localizedField(alert, "message", locale)}</small>
                        </div>
                        <em>{destination.label}</em>
                      </button>
                    );
                  })}
                  {!alerts.length && <EmptyState text="Sem alertas ativos." />}
                </div>
              </section>

              <section className="surface" id="intervention-queue">
                <div className="section-heading">
                  <CheckCircle2 size={18} />
                  <h2>Fila operacional</h2>
                </div>
                <div className="case-list">
                  {interventionCases.slice(0, 10).map((item: AnyDoc) => {
                    const displayName = cleanProtectedValue(item.entity_display_name) || cleanProtectedValue(item.student_display_name) || item.entity_id || item.student_id || item._id;
                    const entityId = item.entity_id || item.student_id || "entidade";
                    return (
                      <div key={item._id} className={`case-card ${item.priority}`}>
                        <div>
                          <strong>{t(displayName)}</strong>
                          <span>{entityId} / {item.window_used || item.model_version || "janela atual"}</span>
                        </div>
                        <em>{item.priority}</em>
                        <strong>{Math.round((item.risk_score || 0) * 100)}%</strong>
                        <small>{item.recommended_action}</small>
                        <div className="inline-actions compact-actions">
                          <button type="button" className="secondary" onClick={() => updateCaseStatus(item._id, "in_progress")}>Assumir</button>
                          <button type="button" className="secondary" onClick={() => updateCaseStatus(item._id, "resolved")}>Resolver</button>
                        </div>
                      </div>
                    );
                  })}
                  {!interventionCases.length && <EmptyState text="Fila vazia." />}
                </div>
              </section>

              <section className="surface" id="source-quality">
                <div className="section-heading">
                  <Database size={18} />
                  <h2>Qualidade da fonte</h2>
                </div>
                {dataQuality ? (
                  <div className="quality-grid">
                    <div><span>Linhas</span><strong>{fmt(dataQuality.source?.row_count)}</strong></div>
                    <div><span>Entidades</span><strong>{fmt(dataQuality.source?.student_count ?? dataQuality.source?.entity_count)}</strong></div>
                    <div><span>Colunas</span><strong>{fmt(dataQuality.source?.column_count)}</strong></div>
                    {dataQuality.source?.pdf_pages ? <div><span>Paginas PDF</span><strong>{fmt(dataQuality.source?.pdf_pages)}</strong></div> : null}
                    {dataQuality.eligibility ? Object.entries(dataQuality.eligibility).map(([key, value]) => (
                      <div key={key}><span>{key.toUpperCase()}</span><strong>{fmt(value)}</strong></div>
                    )) : null}
                    {(dataQuality.warnings || []).slice(0, 3).map((warning: string) => (
                      <p key={warning}>{warning}</p>
                    ))}
                  </div>
                ) : (
                  <EmptyState text="Qualidade indisponivel." />
                )}
              </section>
            </section>

            <section className="surface">
              <div className="section-heading">
                <BarChart3 size={18} />
                <h2>Champion/challenger</h2>
              </div>
              <div className="evaluation-grid">
                {modelEvaluations.slice(0, 15).map((item: AnyDoc) => (
                  <div key={item._id}>
                    <strong>{item.algorithm} {item.window}</strong>
                    <span>rank #{item.rank}</span>
                    <small>Offline: {fmt(item.offline_test_metrics?.f2 ?? item.offline_test_metrics?.pr_auc ?? item.offline_test_metrics?.average_precision ?? item.offline_test_metrics?.threshold_top10 ?? "n/a")}</small>
                    <small>Recall: {item.production_simulation?.performance?.recall ?? "n/a"}</small>
                    <small>Predicoes: {fmt(item.production_simulation?.prediction_count)}</small>
                  </div>
                ))}
              </div>
            </section>

            <section className="ops-grid">
              <section className="surface">
                <div className="section-heading">
                  <AlertTriangle size={18} />
                  <h2>Incidentes operacionais</h2>
                </div>
                <div className="incident-list">
                  {incidents.map((incident: AnyDoc) => (
                    <div key={incident._id}>
                      <strong>{incident.title}</strong>
                      <span>{incident.severity} / {incident.status}</span>
                      <small>{incident.impact}</small>
                    </div>
                  ))}
                  {!incidents.length && <EmptyState text="Sem incidentes ativos." />}
                </div>
              </section>
              <section className="surface">
                <div className="section-heading">
                  <GitCompare size={18} />
                  <h2>Coortes monitoradas</h2>
                </div>
                <div className="cohort-list">
                  {cohorts.slice(0, 8).map((cohort: AnyDoc) => (
                    <div key={cohort._id}>
                      <strong>{localizedField(cohort, "name", locale)}</strong>
                      <span>{fmt(cohort.size)} {entityLabel}</span>
                      <small>{fmt(cohort.open_cases)} casos</small>
                    </div>
                  ))}
                  {!cohorts.length && <EmptyState text="Sem coortes monitoradas." />}
                </div>
              </section>
            </section>
          </section>
        )}

        {activeView === "control" && (
          <section className="view-stack">
            <section className="surface">
              <div className="section-heading split">
                <div>
                  <div className="section-title-row">
                    <Zap size={18} />
                    <h2>Automacao e operacao corporativa</h2>
                  </div>
                  <p>Jobs, notificacoes, contratos de dados, views salvas e regras de alerta em um painel operacional.</p>
                </div>
                <div className="inline-actions section-actions">
                  <button className="secondary" onClick={() => { refreshJobs(); refreshNotifications(); refreshSavedViews(); refreshDataContract(); refreshAlertRules(); }}>
                    <RefreshCcw size={17} />Atualizar
                  </button>
                  <button onClick={() => runProductJob("alerts")}><Zap size={17} />Rodar alertas</button>
                </div>
              </div>
              <div className="metric-grid">
                <Metric label="Notificacoes" value={fmt(notificationUnread)} icon={<Activity size={18} />} tone={notificationUnread ? "warn" : "good"} />
                <Metric label="Jobs" value={fmt(jobs.length)} icon={<Play size={18} />} />
                <Metric label="Views" value={fmt(savedViews.length)} icon={<Archive size={18} />} />
                <Metric label="Regras" value={fmt(alertRules.length)} icon={<Zap size={18} />} />
                <Metric label="Contrato" value={String(contractMode).toUpperCase()} icon={<ShieldCheck size={18} />} tone={contractMode === "block" ? "good" : "warn"} />
              </div>
            </section>

            <section className="control-grid">
              <section className="surface">
                <div className="section-heading split">
                  <div className="section-title-row">
                    <Play size={18} />
                    <h2>Jobs assicronos</h2>
                  </div>
                  <div className="inline-actions">
                    <button className="secondary" onClick={() => runProductJob("dashboard")}>Dashboard</button>
                    <button className="secondary" onClick={() => runProductJob("drift")}>Drift</button>
                    <button className="secondary" onClick={() => runProductJob("diagnostics")}>DS Lab</button>
                    <button className="secondary" onClick={() => runProductJob("metrics")}>Metricas</button>
                  </div>
                </div>
                <div className="job-list">
                  {jobs.slice(0, 10).map((job) => (
                    <div key={job._id} className={job.status}>
                      <strong>{job.type}</strong>
                      <span>{job.status}</span>
                      <small>{job.created_at}</small>
                    </div>
                  ))}
                  {!jobs.length && <EmptyState text="Nenhum job executado." />}
                </div>
              </section>

              <section className="surface">
                <div className="section-heading split">
                  <div className="section-title-row">
                    <Activity size={18} />
                    <h2>Notificacoes</h2>
                  </div>
                  <button className="secondary" onClick={markNotificationsRead}>Marcar lidas</button>
                </div>
                <div className="notification-list">
                  {notifications.slice(0, 12).map((item) => (
                    <div key={item._id} className={item.read_at ? "read" : item.severity || "info"}>
                      <strong>{item.title}</strong>
                      <span>{item.message}</span>
                      <small>{item.created_at}</small>
                    </div>
                  ))}
                  {!notifications.length && <EmptyState text="Sem notificacoes." />}
                </div>
              </section>
            </section>

            <section className="control-grid">
              <section className="surface">
                <div className="section-heading">
                  <ShieldCheck size={18} />
                  <h2>Data contracts</h2>
                </div>
                <div className="segmented-control">
                  {(["accept", "warn", "block"] as const).map((mode) => (
                    <button key={mode} type="button" className={contractMode === mode ? "active" : "secondary"} onClick={() => updateDataContractMode(mode)}>
                      {mode}
                    </button>
                  ))}
                </div>
                <div className="coverage-list">
                  {(contractSummary?.models || []).map((model: AnyDoc) => (
                    <div key={model.model_id}>
                      <strong>{model.name}</strong>
                      <span>{fmt(model.expected_features?.length || 0)} features no contrato</span>
                      <em>{contractMode}</em>
                    </div>
                  ))}
                  {!contractSummary && <EmptyState text="Contrato indisponivel." />}
                </div>
              </section>

              <section className="surface">
                <div className="section-heading">
                  <Archive size={18} />
                  <h2>Views salvas</h2>
                </div>
                <div className="saved-view-list">
                  {savedViews.slice(0, 12).map((view) => (
                    <button key={view._id} type="button" className="secondary" onClick={() => applySavedView(view)}>
                      <strong>{view.name}</strong>
                      <span>{view.view}</span>
                    </button>
                  ))}
                  {!savedViews.length && <EmptyState text="Nenhuma view salva." />}
                </div>
              </section>
            </section>

            <section className="surface">
              <div className="section-heading">
                <Zap size={18} />
                <h2>Regras de alerta</h2>
              </div>
              <div className="alert-rule-list">
                {alertRules.map((rule) => (
                  <div key={rule._id}>
                    <strong>{localizedField(rule, "name", locale, rule.name)}</strong>
                    <span>{rule.type} / {rule.metric} / {rule.operator} {rule.threshold}</span>
                    <small>{rule.enabled ? "ativa" : "pausada"} / {rule.severity}</small>
                  </div>
                ))}
                {!alertRules.length && <EmptyState text="Sem regras customizadas." />}
              </div>
            </section>
          </section>
        )}

        {activeView === "workbench" && (
          <section className="workbench-grid">
            <section className="surface">
              <div className="section-heading split">
                <div>
                  <div className="section-title-row">
                    <TerminalSquare size={18} />
                    <h2>Nova predicao</h2>
                  </div>
                  <p>Entrada guiada para novas decisoes.</p>
                </div>
                <button onClick={sendGuidedPrediction}><Play size={17} />Registrar predicao</button>
              </div>
              <div className="simulator-form">
                <label>
                  ID da entidade
                  <input value={simStudentId} onChange={(event) => setSimStudentId(event.target.value)} />
                </label>
                <label>
                  Nome publico
                  <input value={simStudentName} onChange={(event) => setSimStudentName(event.target.value)} />
                </label>
                <label>
                  Versao/janela
                  <select value={simWindow} onChange={(event) => setSimWindow(event.target.value)}>
                    {versions.map((version) => (
                      <option key={version._id} value={version.version}>{version.version}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Score
                  <input type="number" min="0" max="1" step="0.01" value={simScore} onChange={(event) => setSimScore(event.target.valueAsNumber)} />
                </label>
                {(selectedModel?.expected_features || []).slice(0, 12).map((feature: AnyDoc, index: number) => (
                  <label key={feature.name}>
                    {feature.name}
                    <input
                      type={feature.type === "numeric" ? "number" : "text"}
                      step={feature.type === "numeric" ? "0.01" : undefined}
                      value={simFeatureValues[feature.name] ?? (feature.type === "numeric" ? String(index + 1) : "valor_padrao")}
                      onChange={(event) => setSimFeatureValues((current) => ({ ...current, [feature.name]: event.target.value }))}
                    />
                  </label>
                ))}
              </div>
              {workbenchErrors.length ? (
                <div className="form-errors" role="alert">
                  {workbenchErrors.map((error) => (
                    <span key={error}>{error}</span>
                  ))}
                </div>
              ) : null}
            </section>
            <section className="surface">
              <div className="section-heading">
                <KeyRound size={18} />
                <h2>Integracao</h2>
              </div>
              <div className="key-box">
                <span>API key ativa</span>
                <code>{apiKey ? `${apiKey.slice(0, 18)}...` : "Sem API key ativa"}</code>
              </div>
              <div className="simulation-preview">
                <span>Preview da decisao</span>
                <strong>{simScore >= Number(selectedModel?.default_threshold ?? 0.7) ? positiveLabel : negativeLabel}</strong>
                <small>Threshold: {fmt(selectedModel?.default_threshold ?? 0.7)}</small>
              </div>
              <details className="technical-details">
                <summary>cURL</summary>
                <pre>{apiSnippet}</pre>
              </details>
              {analysisResult?.type === "api-response" ? (
                <AnalysisBlock data={analysisResult} compact />
              ) : (
                <EmptyState text="Nenhum envio nesta sessao." />
              )}
            </section>
          </section>
        )}

        {activeView === "governance" && (
          <section className="governance-grid">
            <section className="surface">
              <div className="section-heading split">
                <div>
                  <div className="section-title-row">
                    <Lock size={18} />
                    <h2>Postura de seguranca</h2>
                  </div>
                  <p>PII, chaves, headers e hardening.</p>
                </div>
                <button className="secondary" onClick={runSecurityMigration}>
                  <ShieldCheck size={17} />
                  Aplicar controles
                </button>
              </div>
              <div className="security-check-list">
                {securityChecks.map((check: AnyDoc) => (
                  <div key={check.id} className={check.severity || "info"}>
                    <span>{check.status}</span>
                    <strong>{check.label}</strong>
                    <small>{check.detail}</small>
                  </div>
                ))}
                {!securityChecks.length && <EmptyState text="Postura nao disponivel." />}
              </div>
              {securityPosture?.recommendations?.length ? (
                <div className="security-notes">
                  {securityPosture.recommendations.slice(0, 4).map((item: string) => (
                    <span key={item}>{item}</span>
                  ))}
                </div>
              ) : null}
            </section>
            <section className="surface">
              <div className="section-heading split">
                <div className="section-title-row">
                  <KeyRound size={18} />
                  <h2>API keys</h2>
                </div>
                <button className="secondary" onClick={createApiKey}>
                  <KeyRound size={17} />
                  Nova chave
                </button>
              </div>
              <div className="key-list">
                {apiKeys.map((item) => (
                  <div key={item._id} className={item.status === "revoked" ? "revoked" : ""}>
                    <div>
                      <strong>{item.name}</strong>
                      <span>{item.prefix} / {item.status}</span>
                      <small>Escopos: {(item.scopes || ["predictions:write"]).join(", ")}</small>
                      <small>Expira em {item.expires_at || "sem expiracao definida"}</small>
                      <small>Ultimo uso {item.last_used_at || "ainda nao usada"}</small>
                    </div>
                    <button
                      type="button"
                      className="secondary"
                      disabled={item.status === "revoked"}
                      onClick={() => revokeApiKey(item._id)}
                    >
                      Revogar
                    </button>
                  </div>
                ))}
                {!apiKeys.length && <EmptyState text="Sem chaves para este projeto." />}
              </div>
            </section>
            <section className="surface">
              <div className="section-heading split">
                <div className="section-title-row">
                  <ShieldCheck size={18} />
                  <h2>Audit trail</h2>
                </div>
                <div className="audit-actions">
                  <label className="search-field audit-search">
                    <Search size={15} />
                    <input
                      value={auditQuery}
                      onChange={(event) => setAuditQuery(event.target.value)}
                      placeholder="Filtrar auditoria"
                    />
                  </label>
                  <button type="button" className="secondary" onClick={exportAuditEvidence}>
                    <Download size={17} />
                    Exportar evidencias
                  </button>
                </div>
              </div>
              <div className="timeline">
                {filteredAuditEvents.slice(0, 28).map((event) => (
                  <div key={event._id}>
                    <strong>{event.event_type}</strong>
                    <span>{event.actor?.email_masked || event.actor?.id || event.actor?.prefix}</span>
                    <small>{event.created_at}</small>
                  </div>
                ))}
                {filteredAuditEvents.length > 28 && (
                  <div className="timeline-more">
                    <strong>+{filteredAuditEvents.length - 28} eventos no filtro</strong>
                    <span>Use a exportacao para o conjunto completo</span>
                    <small>audit_events</small>
                  </div>
                )}
                {!filteredAuditEvents.length && <EmptyState text="Sem eventos para este filtro." />}
              </div>
            </section>
            <section className="surface">
              <div className="section-heading">
                <Database size={18} />
                <h2>Modelo documental</h2>
              </div>
              <div className="collection-map">
                {[
                  "users",
                  "email_tokens",
                  "api_keys",
                  "notifications",
                  "jobs",
                  "saved_views",
                  "predictions",
                  "entity_notes",
                  "prediction_scenarios",
                  "metrics_snapshots",
                  "diagnostic_cache",
                  "audit_events",
                  "prediction_replays",
                  "alerts",
                  "exports"
                ].map((collection) => (
                  <div key={collection}>
                    <strong>{collection}</strong>
                    <span>{collection === "predictions" ? "principal" : "suporte"}</span>
                  </div>
                ))}
              </div>
            </section>
          </section>
        )}

        {activeView === "profile" && (
          <section className="profile-view">
            <section className="surface profile-hero">
              <div className="profile-avatar">
                {session.user.avatar_url ? (
                  <img src={apiAssetUrl(session.user.avatar_url)} alt="" />
                ) : (
                  <UserCircle size={56} />
                )}
              </div>
              <div className="profile-summary">
                <span className="eyebrow">Conta</span>
                <h2>{session.user.name}</h2>
                <p>{session.user.job_title || "Perfil profissional"} {session.user.department ? `/ ${session.user.department}` : ""}</p>
                <div className="health-tags">
                  <span>{session.user.email}</span>
                  <span className={session.user.email_verified ? "badge-success" : "badge-warn"}>
                    {session.user.email_verified ? "Email confirmado" : "Email pendente"}
                  </span>
                  <span>{session.user.role || "USER"}</span>
                </div>
              </div>
              <div className="profile-actions">
                <label className="avatar-upload-button">
                  <Upload size={17} />
                  {avatarUploading ? "Enviando..." : "Alterar foto"}
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    disabled={avatarUploading}
                    onChange={(event) => uploadAvatar(event.target.files?.[0])}
                  />
                </label>
                <button type="button" className="secondary" onClick={() => refreshMe()}>
                  <RefreshCcw size={17} />
                  Atualizar perfil
                </button>
              </div>
            </section>

            <section className="profile-grid">
              <section className="surface">
                <div className="section-heading split">
                  <div>
                    <div className="section-title-row">
                      <UserCircle size={18} />
                      <h2>Dados pessoais e profissionais</h2>
                    </div>
                    <p>Essas informações identificam o usuário em auditorias, aprovações e fluxos operacionais.</p>
                  </div>
                  <button type="button" onClick={saveProfile}>
                    <CheckCircle2 size={17} />
                    Salvar perfil
                  </button>
                </div>
                <div className="profile-form">
                  <label>
                    Nome completo
                    <input value={profileDraft.name || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, name: event.target.value }))} />
                  </label>
                  <label>
                    Email
                    <input value={profileDraft.email || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, email: event.target.value }))} />
                  </label>
                  <label>
                    Cargo
                    <input value={profileDraft.job_title || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, job_title: event.target.value }))} />
                  </label>
                  <label>
                    Área
                    <input value={profileDraft.department || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, department: event.target.value }))} />
                  </label>
                  <label>
                    Empresa
                    <input value={profileDraft.company || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, company: event.target.value }))} />
                  </label>
                  <label>
                    Telefone
                    <input value={profileDraft.phone || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, phone: event.target.value }))} />
                  </label>
                  <label>
                    Fuso horário
                    <input value={profileDraft.timezone || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, timezone: event.target.value }))} />
                  </label>
                  <label className="span-2">
                    Bio
                    <textarea rows={5} value={profileDraft.bio || ""} onChange={(event) => setProfileDraft((current) => ({ ...current, bio: event.target.value }))} />
                  </label>
                </div>
              </section>

              <section className="surface profile-security">
                <div className="section-heading">
                  <ShieldCheck size={18} />
                  <h2>Segurança da conta</h2>
                </div>
                <div className="security-check-list compact-list">
                  <div className={session.user.email_verified ? "good" : "warn"}>
                    <span>{session.user.email_verified ? "ok" : "pendente"}</span>
                    <strong>Confirmação de email</strong>
                    <small>{session.user.email_verified ? "Endereço confirmado." : "Confirme o email para concluir a validação da conta."}</small>
                  </div>
                  <div className="info">
                    <span>ativo</span>
                    <strong>Senha forte</strong>
                    <small>Novas senhas exigem tamanho mínimo, número, letra maiúscula, letra minúscula e caractere especial.</small>
                  </div>
                  <div className="info">
                    <span>http-only</span>
                    <strong>Sessão protegida</strong>
                    <small>Tokens ficam em cookies HTTP-only e também alimentam chamadas autenticadas no cliente.</small>
                  </div>
                </div>
                <div className="profile-action-stack">
                  <button type="button" className="secondary" onClick={resendVerificationEmail}>
                    <MailCheck size={17} />
                    Reenviar confirmação
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => {
                      setResetEmail(profileDraft.email || session.user.email || email);
                      setResetOpen(true);
                      setActiveView("profile");
                      requestPasswordReset(profileDraft.email || session.user.email || email);
                    }}
                  >
                    <KeyRound size={17} />
                    Enviar reset de senha
                  </button>
                </div>
              </section>

              <section className="surface profile-security">
                <div className="section-heading">
                  <Camera size={18} />
                  <h2>Preferências</h2>
                </div>
                <div className="preference-list">
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={Boolean(profileDraft.email_alerts)}
                      onChange={(event) => setProfileDraft((current) => ({ ...current, email_alerts: event.target.checked }))}
                    />
                    <span>Receber alertas por email</span>
                  </label>
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={Boolean(profileDraft.compact_mode)}
                      onChange={(event) => setProfileDraft((current) => ({ ...current, compact_mode: event.target.checked }))}
                    />
                    <span>Modo compacto para tabelas operacionais</span>
                  </label>
                </div>
                <p>
                  Preferências salvas no perfil acompanham o usuário e podem ser usadas por fluxos de notificação, auditoria e operação.
                </p>
              </section>
            </section>
          </section>
        )}

        {activeView === "docs" && (
          <section className="docs-view">
            <section className="surface docs-hero">
              <div>
                <div className="section-title-row">
                  <BookOpen size={19} />
                  <h2>Documentacao do usuario</h2>
                </div>
                <p>
                  Guia de uso do ModelTrace para operacao, ciencia de dados, governanca e integracoes.
                </p>
              </div>
              <div className="docs-quickstart">
                <button type="button" className="secondary" onClick={() => setSelectedDocId("workbench")}>Registrar predicao</button>
                <button type="button" className="secondary" onClick={() => setSelectedDocId("whatif")}>Entender What-if</button>
                <button type="button" className="secondary" onClick={() => setSelectedDocId("governance")}>Seguranca</button>
              </div>
            </section>

            <div className="docs-layout">
              <aside className="surface docs-sidebar">
                <strong>Navegacao</strong>
                <div className="docs-nav-list">
                  {localizedDocSections.map((section) => (
                    <button
                      type="button"
                      key={section.id}
                      className={selectedDocSection.id === section.id ? "active" : "secondary"}
                      onClick={() => setSelectedDocId(section.id)}
                    >
                      {section.label}
                    </button>
                  ))}
                </div>
              </aside>

              <section className="surface docs-content">
                <span className="eyebrow">Docs / {selectedDocSection.label}</span>
                <h2>{selectedDocSection.title}</h2>
                <p className="doc-lead">{selectedDocSection.intro}</p>

                <article className="doc-article">
                  {selectedDocSection.topics.map((topic) => (
                    <section className="doc-topic" key={topic.heading}>
                      <h3>{topic.heading}</h3>
                      {topic.paragraphs.map((paragraph, paragraphIndex) => (
                        <p key={`${topic.heading}-${paragraphIndex}`}>{paragraph}</p>
                      ))}
                      {topic.example && (
                        <div className="doc-example">
                          <span className="doc-example-label">Exemplo</span>
                          <strong>{topic.example.title}</strong>
                          {topic.example.caption && <p>{topic.example.caption}</p>}
                          <pre>
                            <code>{topic.example.code}</code>
                          </pre>
                        </div>
                      )}
                    </section>
                  ))}
                </article>

                <div className="doc-related">
                  <strong>Continue lendo</strong>
                  <p>{selectedDocSection.related.join(" / ")}</p>
                </div>
              </section>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

function Metric({
  label,
  value,
  icon,
  tone = "neutral",
  onClick
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  tone?: string;
  onClick?: () => void;
}) {
  const content = (
    <>
      <span>{icon}</span>
      <small>{label}</small>
      <strong>{value}</strong>
    </>
  );
  if (onClick) {
    return (
      <button type="button" className={`metric ${tone} clickable`} onClick={onClick}>
        {content}
      </button>
    );
  }
  return (
    <div className={`metric ${tone}`}>
      {content}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty-state">{text}</div>;
}

function ErrorList({ title, rows }: { title: string; rows: AnyDoc[] }) {
  return (
    <section className="surface error-panel">
      <div className="section-heading">
        <AlertTriangle size={18} />
        <h2>{title}</h2>
      </div>
      <div className="error-list">
        {rows.map((row) => (
          <button type="button" key={row.id}>
            <span>{row.result}</span>
            <strong>{row.entity || row.id}</strong>
            <small>{row.model_version} / score {fmt(row.score)} / {row.top_driver || "driver nao identificado"}</small>
          </button>
        ))}
        {!rows.length && <EmptyState text="Sem casos nesta classe." />}
      </div>
    </section>
  );
}

function ResultMetric({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{fmt(value)}</strong>
    </div>
  );
}

function AnalysisBlock({ data, compact = false }: { data: AnyDoc; compact?: boolean }) {
  const result = data.result || {};
  const titleMap: Record<string, string> = {
    drift: "Drift",
    "version-compare": "Comparacao de versoes",
    bias: "Equidade",
    export: "Exportacao criada",
    "what-if": "What-if",
    replay: "Replay",
    "api-response": "Predicao registrada",
    "api-key": "API key criada",
    "security-migration": "Controles de seguranca"
  };

  return (
    <section className={compact ? "analysis-block compact" : "analysis-block"}>
      <strong>{titleMap[data.type] || "Resultado"}</strong>

      {data.type === "drift" && (
        <>
          <div className="result-grid">
            <ResultMetric label="Status" value={result.prediction_drift?.status || result.status} />
            <ResultMetric label="PSI" value={result.prediction_drift?.psi} />
            <ResultMetric label="Score medio atual" value={result.prediction_drift?.mean_score_cur} />
            <ResultMetric label="Features avaliadas" value={(result.data_drift?.features || []).length} />
          </div>
          <p>{result.message || "Drift atualizado. Features em atencao listadas acima."}</p>
        </>
      )}

      {data.type === "version-compare" && (
        <>
          <div className="result-grid">
            <ResultMetric label="Versao A" value={result.version_a?.metadata?.version} />
            <ResultMetric label="Versao B" value={result.version_b?.metadata?.version} />
            <ResultMetric label="Delta score medio" value={result.delta?.avg_score} />
            <ResultMetric label="Delta acionavel" value={result.delta?.positive_rate} />
          </div>
          <p>Deltas comparados na populacao observada.</p>
        </>
      )}

      {data.type === "bias" && (
        <>
          <div className="result-grid">
            <ResultMetric label="Feature" value={result.feature} />
            <ResultMetric label="Grupos" value={(result.rows || []).length} />
            <ResultMetric label="Casos analisados" value={(result.rows || []).reduce((sum: number, row: AnyDoc) => sum + (row.total || 0), 0)} />
          </div>
          <div className="mini-table">
            {(result.rows || []).slice(0, 6).map((row: AnyDoc) => (
              <div key={row.group}>
                <strong>{row.group}</strong>
                <span>{fmt(row.total)} casos</span>
                <span>{percent(row.positive_rate)} acionaveis</span>
                <span>recall {fmt(row.recall)}</span>
              </div>
            ))}
          </div>
          <p>Segmentos com diferenca operacional para revisao.</p>
        </>
      )}

      {data.type === "export" && (
        <div className="result-grid">
          <ResultMetric label="Arquivo" value={result._id} />
          <ResultMetric label="Formato" value={result.format} />
          <ResultMetric label="Registros" value={result.record_count} />
          <ResultMetric label="Status" value={result.status} />
        </div>
      )}

      {data.type === "what-if" && (
        <div className="result-grid">
          <ResultMetric label="Score original" value={result.original_score} />
          <ResultMetric label="Score estimado" value={result.estimated_score} />
          <ResultMetric label="Delta" value={result.estimated_delta ?? result.delta} />
          <ResultMetric label="Decisao muda" value={(result.would_change_decision ?? result.decision_changed) ? "sim" : "nao"} />
        </div>
      )}

      {data.type === "replay" && (
        <div className="result-grid">
          <ResultMetric label="Versao alvo" value={result.replay?.target_version} />
          <ResultMetric label="Score replay" value={result.replay?.score} />
          <ResultMetric label="Label replay" value={result.replay?.label} />
          <ResultMetric label="Decisao muda" value={result.decision_changed ? "sim" : "nao"} />
        </div>
      )}

      {data.type === "api-response" && (
        <div className="result-grid">
          <ResultMetric label="ID da predicao" value={result.prediction_id} />
          <ResultMetric label="Status" value={result.status} />
        </div>
      )}

      {data.type === "api-key" && (
        <>
          <div className="key-box reveal">
            <span>Exibida uma vez.</span>
            <code>{result.api_key}</code>
          </div>
          <div className="result-grid">
            <ResultMetric label="Prefixo" value={result.prefix} />
            <ResultMetric label="Escopo" value="Projeto atual" />
          </div>
        </>
      )}

      {data.type === "security-migration" && (
        <div className="result-grid">
          <ResultMetric label="Usuarios" value={result.counts?.users} />
          <ResultMetric label="Predicoes" value={result.counts?.predictions} />
          <ResultMetric label="Auditoria" value={result.counts?.audit_events} />
          <ResultMetric label="API keys legadas" value={result.counts?.legacy_api_keys_requiring_rotation} />
        </div>
      )}
    </section>
  );
}

function PredictionTechnicalDetails({ prediction }: { prediction: AnyDoc }) {
  return (
    <details className="technical-details">
      <summary>Auditoria tecnica</summary>
      <div className="audit-detail-grid">
        <ResultMetric label="Predicao" value={prediction._id} />
        <ResultMetric label="Modelo" value={prediction.model_id} />
        <ResultMetric label="Versao" value={prediction.model_version} />
        <ResultMetric label="Request" value={prediction.metadata?.request_id} />
        <ResultMetric label="Acao" value={prediction.decision?.action} />
        <ResultMetric label="Status" value={prediction.decision?.status} />
      </div>
    </details>
  );
}
