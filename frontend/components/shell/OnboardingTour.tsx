"use client";

import {
  ArrowLeft,
  ArrowRight,
  Database,
  Flame,
  Gauge,
  GitCompare,
  Keyboard,
  Layers3,
  ShieldCheck,
  Sparkles,
  X
} from "lucide-react";
import type { ComponentType, ReactNode, SVGProps } from "react";
import { useEffect, useState } from "react";
import { Kbd } from "../ui/Kbd";

interface OnboardingTourProps {
  open: boolean;
  onDismiss: () => void;
  onNavigate: (viewId: string) => void;
}

interface TourStep {
  id: string;
  title: string;
  body: string;
  highlights: ReadonlyArray<string>;
  icon: ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>;
  preview: ReactNode;
  cta?: { label: string; viewId: string };
}

const STEPS: ReadonlyArray<TourStep> = [
  {
    id: "welcome",
    title: "Bem-vindo ao ModelTrace",
    body:
      "Plataforma de observabilidade e governança para decisões de Machine Learning. Toda predição vira documento auditável com features, score, decisão e feedback.",
    highlights: [
      "30+ coleções NoSQL prontas para uso",
      "Auditoria append-only de cada decisão",
      "Criptografia de PII e índices cegos no nível da aplicação"
    ],
    icon: Database,
    preview: (
      <div style={{ display: "grid", gap: 8 }}>
        <strong style={{ color: "var(--accent-strong)", fontSize: "var(--fs-xs)", letterSpacing: "0.16em" }}>
          O QUE VOCÊ VERÁ
        </strong>
        <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)", margin: 0 }}>
          Workspace dividido em 14 abas, cada uma com função específica. Use a sidebar à esquerda para navegar.
        </p>
      </div>
    )
  },
  {
    id: "overview",
    title: "Overview — Saúde executiva",
    body:
      "Comece pelo Overview para ver o health score do modelo, KPIs clicáveis, série temporal, distribuição de score e matriz de confusão.",
    highlights: [
      "Health score combina feedback, alertas, recall e capacidade",
      "KPIs com sparkline e variação automática",
      "Clicar em KPI leva direto para Predições filtradas"
    ],
    icon: Gauge,
    preview: (
      <pre style={{ margin: 0, fontSize: "var(--fs-xs)", lineHeight: 1.6 }}>
{`╭──────────╮  Predicões  Acionáveis  Feedback
│   92     │  102.230    18,4%       62,1%
│   ●●●●●○ │   ▁▂▄▆█▆▄▂  ▁▃▆▆▄▂      ▆█▇▆▅
│  health  │
╰──────────╯`}
      </pre>
    ),
    cta: { label: "Abrir Overview", viewId: "overview" }
  },
  {
    id: "compare",
    title: "Compare — Champion vs Challenger",
    body:
      "Compare duas versões do mesmo modelo lado a lado: predição, distribuição, matriz de confusão e métricas. Promova o challenger com um clique.",
    highlights: [
      "Endpoint /models/{id}/versions/compare?a=…&b=…",
      "Promote idempotente com auditoria automática",
      "Indicação visual de quem está vencendo"
    ],
    icon: GitCompare,
    preview: (
      <pre style={{ margin: 0, fontSize: "var(--fs-xs)", lineHeight: 1.6 }}>
{`┌─ Champion v1 ─┐  ┌─ Challenger v2 ─┐
│ F1   72.4%   │  │ F1    78.1% ↑5.7│
│ AUC  0.834   │  │ AUC   0.851 ↑   │
│ ●●●●○○○○     │  │ ●●●●●●○○        │
└──────────────┘  └─────────────────┘`}
      </pre>
    ),
    cta: { label: "Ver Compare", viewId: "compare" }
  },
  {
    id: "drift",
    title: "Drift — Heatmap por feature",
    body:
      "Quando a entrada do modelo muda, o score muda. O heatmap mostra PSI por feature × tempo, destacando drift detectado e atenção.",
    highlights: [
      "PSI por feature contínua via quantis igualitários",
      "Threshold padrão: 0.10 atenção, 0.25 drift",
      "Linha extra com PSI top-level do score"
    ],
    icon: Flame,
    preview: (
      <pre style={{ margin: 0, fontSize: "var(--fs-xs)", lineHeight: 1.6 }}>
{`feature \\ bucket   01/05  03/05  05/05  07/05
score              0.04   0.09   0.18   0.31  ⚠
nota_p1            0.02   0.03   0.05   0.07
freq_aulas         0.11   0.16   0.24   0.42  🔥
faltas             0.08   0.12   0.14   0.21`}
      </pre>
    ),
    cta: { label: "Ver Drift Heatmap", viewId: "drift" }
  },
  {
    id: "cases",
    title: "Casos (SLA Kanban) — fila operacional",
    body:
      "Casos abertos a partir de predições acionáveis aparecem em colunas (A fazer / Em andamento / Resolvido) com SLA visual em cor.",
    highlights: [
      "Prioridade visual: critical, high, medium, low",
      "Barra de SLA com tempo restante humanizado",
      "Alerta global cross-view quando há vencidos"
    ],
    icon: Layers3,
    preview: (
      <pre style={{ margin: 0, fontSize: "var(--fs-xs)", lineHeight: 1.6 }}>
{`┌── A fazer (8) ──┐ ┌── Em andamento (3) ──┐
│ #312 critical    │ │ #309 high            │
│ ████░░░░ 4h      │ │ ░░░░░░░░ -2h vencido │
│ entidade_a4f7    │ │ entidade_b81e        │
└──────────────────┘ └──────────────────────┘`}
      </pre>
    ),
    cta: { label: "Ver Kanban de SLA", viewId: "cases" }
  },
  {
    id: "shortcuts",
    title: "Atalhos de teclado",
    body:
      "Tudo o que importa tem atalho. Modal de ajuda completo abre com '?', e a navegação principal usa prefixo G estilo Gmail/GitHub.",
    highlights: [
      "Cmd+K → Comandos · Cmd+/ → Notificações",
      "G + tecla → navegação por aba",
      "T → tema · R → refresh · Shift+Q → sair"
    ],
    icon: Keyboard,
    preview: (
      <div style={{ display: "grid", gap: 6, fontSize: "var(--fs-sm)" }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Comandos</span>
          <span style={{ display: "inline-flex", gap: 3 }}>
            <Kbd>⌘</Kbd>
            <Kbd>K</Kbd>
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Notificações</span>
          <span style={{ display: "inline-flex", gap: 3 }}>
            <Kbd>⌘</Kbd>
            <Kbd>/</Kbd>
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Ajuda completa</span>
          <Kbd>?</Kbd>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Alternar tema</span>
          <Kbd>T</Kbd>
        </div>
      </div>
    )
  },
  {
    id: "governance",
    title: "Governança e segurança",
    body:
      "API keys com escopo, postura de segurança auditável, criptografia de PII e exportação de evidências para auditoria regulatória.",
    highlights: [
      "PBKDF2-SHA256 para senhas, HMAC-SHA256 para API keys",
      "Migração de PII com chaves rotacionáveis",
      "Audit trail filtrável e exportável"
    ],
    icon: ShieldCheck,
    preview: (
      <div style={{ display: "grid", gap: 8 }}>
        <strong style={{ color: "var(--success-strong)", fontSize: "var(--fs-sm)" }}>
          ● 5 / 5 checks de postura passando
        </strong>
        <span style={{ color: "var(--text-muted)", fontSize: "var(--fs-xs)" }}>
          PII criptografado · API keys hashadas · Cookies HttpOnly · CORS restrito
        </span>
      </div>
    ),
    cta: { label: "Abrir Governança", viewId: "governance" }
  }
];

export function OnboardingTour({ open, onDismiss, onNavigate }: OnboardingTourProps) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!open) return;
    setStep(0);
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onDismiss();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        setStep((current) => Math.min(STEPS.length - 1, current + 1));
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        setStep((current) => Math.max(0, current - 1));
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onDismiss]);

  if (!open) return null;

  const current = STEPS[step];
  const Icon = current.icon;
  const isLast = step === STEPS.length - 1;

  return (
    <div
      className="shortcuts-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Tour de boas-vindas"
      onClick={(event) => {
        if (event.target === event.currentTarget) onDismiss();
      }}
    >
      <section
        className="shortcuts-modal"
        style={{ width: "min(820px, 100%)", padding: "var(--space-6)" }}
      >
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span
              aria-hidden="true"
              style={{
                display: "inline-grid",
                placeItems: "center",
                width: 40,
                height: 40,
                borderRadius: "var(--radius)",
                background: "linear-gradient(135deg, var(--accent), var(--info))",
                color: "#fff",
                boxShadow: "0 6px 18px var(--accent-glow)"
              }}
            >
              <Sparkles size={18} />
            </span>
            <div>
              <strong style={{ display: "block", color: "var(--text-strong)", fontSize: "var(--fs-lg)" }}>
                Tour rápido
              </strong>
              <span className="stat-label" style={{ fontSize: "var(--fs-2xs)" }}>
                Passo {step + 1} de {STEPS.length}
              </span>
            </div>
          </div>
          <button
            type="button"
            className="ghost icon-only sm"
            onClick={onDismiss}
            aria-label="Fechar tour"
          >
            <X size={16} />
          </button>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1.1fr) minmax(0, 0.9fr)",
            gap: 24,
            alignItems: "start"
          }}
        >
          <div style={{ display: "grid", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span
                aria-hidden="true"
                style={{
                  display: "inline-grid",
                  placeItems: "center",
                  width: 32,
                  height: 32,
                  borderRadius: "var(--radius-sm)",
                  background: "var(--accent-soft)",
                  color: "var(--accent-strong)"
                }}
              >
                <Icon size={16} />
              </span>
              <h2 style={{ fontSize: "var(--fs-xl)" }}>{current.title}</h2>
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-md)", lineHeight: 1.6 }}>
              {current.body}
            </p>
            <ul
              style={{
                margin: 0,
                paddingLeft: 0,
                listStyle: "none",
                display: "grid",
                gap: 8
              }}
            >
              {current.highlights.map((highlight) => (
                <li
                  key={highlight}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "auto 1fr",
                    gap: 10,
                    alignItems: "start",
                    color: "var(--text)",
                    fontSize: "var(--fs-sm)"
                  }}
                >
                  <span
                    aria-hidden="true"
                    style={{
                      display: "inline-block",
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: "var(--accent-strong)",
                      marginTop: 7
                    }}
                  />
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </div>

          <div
            style={{
              padding: 16,
              borderRadius: "var(--radius)",
              background: "var(--surface-2)",
              border: "1px solid var(--border)",
              minHeight: 180,
              display: "flex",
              alignItems: "center",
              fontFamily: "var(--font-mono)",
              fontSize: "var(--fs-xs)",
              color: "var(--text-muted)",
              overflow: "auto"
            }}
          >
            {current.preview}
          </div>
        </div>

        <footer
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingTop: 16,
            borderTop: "1px solid var(--border)"
          }}
        >
          <div style={{ display: "flex", gap: 6 }}>
            {STEPS.map((entry, index) => (
              <button
                key={entry.id}
                type="button"
                onClick={() => setStep(index)}
                aria-label={`Ir para passo ${index + 1}`}
                style={{
                  width: 24,
                  height: 6,
                  borderRadius: 999,
                  background: index === step ? "var(--accent)" : "var(--surface-3)",
                  border: 0,
                  padding: 0,
                  minHeight: 6,
                  cursor: "pointer",
                  boxShadow: "none",
                  transition: "background var(--dur)"
                }}
              />
            ))}
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              type="button"
              className="ghost sm"
              onClick={onDismiss}
              aria-label="Pular tour"
            >
              Pular
            </button>
            <button
              type="button"
              className="secondary sm"
              onClick={() => setStep((current) => Math.max(0, current - 1))}
              disabled={step === 0}
              aria-label="Passo anterior"
            >
              <ArrowLeft size={13} />
              Voltar
            </button>
            {current.cta ? (
              <button
                type="button"
                className="sm"
                onClick={() => {
                  onNavigate(current.cta!.viewId);
                  onDismiss();
                }}
              >
                {current.cta.label}
                <ArrowRight size={13} />
              </button>
            ) : null}
            <button
              type="button"
              className="sm"
              onClick={() => {
                if (isLast) {
                  onDismiss();
                } else {
                  setStep((c) => Math.min(STEPS.length - 1, c + 1));
                }
              }}
            >
              {isLast ? "Concluir" : "Próximo"}
              {!isLast ? <ArrowRight size={13} /> : null}
            </button>
          </div>
        </footer>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 18,
            color: "var(--text-subtle)",
            fontSize: "var(--fs-xs)",
            paddingTop: 4
          }}
        >
          <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
            <Kbd>←</Kbd>
            <Kbd>→</Kbd>
            navegar
          </span>
          <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
            <Kbd>Esc</Kbd>
            fechar
          </span>
        </div>
      </section>
    </div>
  );
}

const ONBOARDING_KEY = "modeltrace_onboarding_v2";

export function shouldShowOnboarding(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(ONBOARDING_KEY) !== "completed";
  } catch {
    return false;
  }
}

export function dismissOnboarding(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(ONBOARDING_KEY, "completed");
  } catch {
    // ignore
  }
}

export function resetOnboarding(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(ONBOARDING_KEY);
  } catch {
    // ignore
  }
}
