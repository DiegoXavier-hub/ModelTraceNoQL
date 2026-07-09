"use client";

import {
  AlertOctagon,
  ArrowRight,
  CheckCircle2,
  Circle,
  Clock,
  Layers,
  Pause,
  Play,
  TimerReset,
  UserCheck,
  XCircle
} from "lucide-react";
import { useMemo } from "react";
import { entityDisplayName, entityIdentifier } from "@/lib/entity";
import { Badge, type BadgeTone } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";

type AnyDoc = Record<string, any>;

export type CaseStatus = "open" | "assigned" | "in_progress" | "paused" | "resolved" | "dismissed";

interface SlaKanbanViewProps {
  cases: ReadonlyArray<AnyDoc>;
  loading: boolean;
  onUpdateStatus: (caseId: string, status: CaseStatus, note?: string) => void | Promise<void>;
  onOpenEntity: (entityId: string) => void;
  formatNumber: (value: unknown) => string;
}

interface ColumnConfig {
  id: "todo" | "doing" | "done";
  label: string;
  description: string;
  statuses: CaseStatus[];
  primaryAction: { label: string; status: CaseStatus; icon: typeof Play } | null;
  secondaryAction?: { label: string; status: CaseStatus; icon: typeof Play };
}

const COLUMNS: ReadonlyArray<ColumnConfig> = [
  {
    id: "todo",
    label: "A fazer",
    description: "Casos abertos e atribuídos, aguardando ação.",
    statuses: ["open", "assigned"],
    primaryAction: { label: "Iniciar", status: "in_progress", icon: Play }
  },
  {
    id: "doing",
    label: "Em andamento",
    description: "Casos em análise ou pausados.",
    statuses: ["in_progress", "paused"],
    primaryAction: { label: "Resolver", status: "resolved", icon: CheckCircle2 },
    secondaryAction: { label: "Pausar", status: "paused", icon: Pause }
  },
  {
    id: "done",
    label: "Resolvido",
    description: "Casos finalizados (resolvidos ou descartados).",
    statuses: ["resolved", "dismissed"],
    primaryAction: { label: "Reabrir", status: "open", icon: TimerReset }
  }
];

const PRIORITY_TONE: Record<string, BadgeTone> = {
  critical: "danger",
  high: "warn",
  medium: "info",
  low: "neutral"
};

interface SlaState {
  ratio: number;
  remainingMs: number;
  remainingLabel: string;
  status: "ontrack" | "atrisk" | "breached";
}

function parseDate(value: unknown): Date | null {
  if (!value) return null;
  const parsed = new Date(String(value));
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function priorityRank(rank: unknown): string {
  const value = Number(rank ?? 0);
  if (value <= 1) return "critical";
  if (value === 2) return "high";
  if (value === 3) return "medium";
  return "low";
}

function priorityLabel(label: unknown, rank: unknown): string {
  if (typeof label === "string" && label) return label;
  return priorityRank(rank);
}

function computeSla(caseDoc: AnyDoc): SlaState | null {
  const dueAt = parseDate(caseDoc.due_at ?? caseDoc.sla_due_at);
  const createdAt = parseDate(caseDoc.created_at) ?? new Date();
  if (!dueAt) {
    const slaHours = Number(caseDoc.sla_hours ?? caseDoc.sla?.hours ?? 0);
    if (!slaHours) return null;
    const projectedDue = new Date(createdAt.getTime() + slaHours * 3600_000);
    return computeSla({ ...caseDoc, due_at: projectedDue.toISOString() });
  }
  const totalMs = dueAt.getTime() - createdAt.getTime();
  const remainingMs = dueAt.getTime() - Date.now();
  const ratio = totalMs > 0 ? Math.max(0, Math.min(1, remainingMs / totalMs)) : 0;

  let status: SlaState["status"] = "ontrack";
  if (remainingMs <= 0) status = "breached";
  else if (ratio < 0.25) status = "atrisk";

  let remainingLabel: string;
  if (remainingMs <= 0) {
    const overdueHours = Math.abs(remainingMs) / 3600_000;
    remainingLabel = overdueHours < 24
      ? `vencido há ${Math.floor(overdueHours)}h`
      : `vencido há ${Math.floor(overdueHours / 24)}d`;
  } else if (remainingMs < 3600_000) {
    remainingLabel = `${Math.round(remainingMs / 60_000)} min`;
  } else if (remainingMs < 24 * 3600_000) {
    remainingLabel = `${Math.round(remainingMs / 3600_000)}h restantes`;
  } else {
    remainingLabel = `${Math.round(remainingMs / (24 * 3600_000))}d restantes`;
  }
  return { ratio, remainingMs, remainingLabel, status };
}

function statusTone(status: SlaState["status"]): { color: string; soft: string } {
  if (status === "breached") return { color: "var(--danger-strong)", soft: "var(--danger-soft)" };
  if (status === "atrisk") return { color: "var(--warning-strong)", soft: "var(--warning-soft)" };
  return { color: "var(--success-strong)", soft: "var(--success-soft)" };
}

function bucketCases(cases: ReadonlyArray<AnyDoc>): Record<ColumnConfig["id"], AnyDoc[]> {
  const result: Record<ColumnConfig["id"], AnyDoc[]> = { todo: [], doing: [], done: [] };
  for (const caseDoc of cases) {
    const status = String(caseDoc.status ?? "open") as CaseStatus;
    const column = COLUMNS.find((entry) => entry.statuses.includes(status));
    if (column) {
      result[column.id].push(caseDoc);
    } else {
      result.todo.push(caseDoc);
    }
  }
  for (const key of Object.keys(result) as Array<ColumnConfig["id"]>) {
    result[key].sort((a, b) => {
      const aRank = Number(a.priority_rank ?? 99);
      const bRank = Number(b.priority_rank ?? 99);
      if (aRank !== bRank) return aRank - bRank;
      return Number(b.risk_score ?? 0) - Number(a.risk_score ?? 0);
    });
  }
  return result;
}

export function SlaKanbanView({
  cases,
  loading,
  onUpdateStatus,
  onOpenEntity,
  formatNumber
}: SlaKanbanViewProps) {
  const buckets = useMemo(() => bucketCases(cases), [cases]);
  const summary = useMemo(() => {
    let total = 0;
    let breached = 0;
    let atRisk = 0;
    let resolvedCount = 0;
    for (const caseDoc of cases) {
      total++;
      const status = String(caseDoc.status ?? "open");
      if (status === "resolved" || status === "dismissed") resolvedCount++;
      const sla = computeSla(caseDoc);
      if (!sla) continue;
      if (sla.status === "breached") breached++;
      else if (sla.status === "atrisk") atRisk++;
    }
    return { total, breached, atRisk, resolvedCount };
  }, [cases]);

  if (!cases.length && !loading) {
    return (
      <section className="view-stack">
        <section className="surface">
          <EmptyState
            icon={<Layers size={18} />}
            title="Sem casos operacionais"
            text="Quando o sistema gerar casos a partir de predições acionáveis, eles aparecerão aqui agrupados por status e SLA."
          />
        </section>
      </section>
    );
  }

  return (
    <section className="view-stack">
      <section className="surface" style={{ display: "grid", gap: 16 }}>
        <div className="section-heading">
          <Layers size={16} />
          <h2>SLA Kanban — fila operacional</h2>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)", maxWidth: 760 }}>
          Casos abertos a partir de predições acionáveis, agrupados por status e ordenados por prioridade. A barra
          colorida mostra quanto resta do SLA configurado para o caso. Casos vencidos aparecem com destaque
          vermelho.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
          <KanbanStat label="Total" value={formatNumber(summary.total)} />
          <KanbanStat
            label="Vencidos"
            value={formatNumber(summary.breached)}
            tone={summary.breached > 0 ? "danger" : "neutral"}
          />
          <KanbanStat
            label="Em risco"
            value={formatNumber(summary.atRisk)}
            tone={summary.atRisk > 0 ? "warn" : "neutral"}
          />
          <KanbanStat
            label="Resolvidos"
            value={formatNumber(summary.resolvedCount)}
            tone={summary.resolvedCount > 0 ? "success" : "neutral"}
          />
        </div>
      </section>

      <div className="kanban">
        {COLUMNS.map((column) => {
          const items = buckets[column.id];
          return (
            <section className="kanban-column" key={column.id}>
              <h3>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                  {column.id === "todo" ? (
                    <Circle size={12} />
                  ) : column.id === "doing" ? (
                    <Play size={12} />
                  ) : (
                    <CheckCircle2 size={12} />
                  )}
                  {column.label}
                </span>
                <Badge tone="neutral">{items.length}</Badge>
              </h3>
              <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-xs)", margin: 0 }}>
                {column.description}
              </p>
              {items.length === 0 ? (
                <div
                  style={{
                    padding: "20px 12px",
                    color: "var(--text-subtle)",
                    fontSize: "var(--fs-sm)",
                    textAlign: "center"
                  }}
                >
                  Sem casos.
                </div>
              ) : (
                items.map((caseDoc) => (
                  <CaseCard
                    key={String(caseDoc._id ?? caseDoc.id)}
                    caseDoc={caseDoc}
                    column={column}
                    onUpdateStatus={onUpdateStatus}
                    onOpenEntity={onOpenEntity}
                  />
                ))
              )}
            </section>
          );
        })}
      </div>
    </section>
  );
}

interface KanbanStatProps {
  label: string;
  value: string;
  tone?: "neutral" | "danger" | "warn" | "success";
}

function KanbanStat({ label, value, tone = "neutral" }: KanbanStatProps) {
  const color =
    tone === "danger"
      ? "var(--danger-strong)"
      : tone === "warn"
        ? "var(--warning-strong)"
        : tone === "success"
          ? "var(--success-strong)"
          : "var(--text-strong)";
  return (
    <div
      style={{
        display: "grid",
        gap: 4,
        padding: "10px 12px",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-sm)",
        background: "var(--surface)"
      }}
    >
      <span className="stat-label">{label}</span>
      <strong className="num" style={{ color, fontSize: "var(--fs-lg)" }}>
        {value}
      </strong>
    </div>
  );
}

interface CaseCardProps {
  caseDoc: AnyDoc;
  column: ColumnConfig;
  onUpdateStatus: (caseId: string, status: CaseStatus, note?: string) => void | Promise<void>;
  onOpenEntity: (entityId: string) => void;
}

function CaseCard({ caseDoc, column, onUpdateStatus, onOpenEntity }: CaseCardProps) {
  const id = String(caseDoc._id ?? caseDoc.id ?? "");
  const priorityKey = priorityRank(caseDoc.priority_rank);
  const priorityTone = PRIORITY_TONE[priorityKey] ?? "neutral";
  const sla = computeSla(caseDoc);
  const slaTone = sla ? statusTone(sla.status) : null;
  const entityName = entityDisplayName(caseDoc.entity, "Entidade");
  const entityId = entityIdentifier(caseDoc.entity);
  const score = Number(caseDoc.risk_score ?? caseDoc.score ?? 0);
  const summary = String(caseDoc.summary ?? caseDoc.recommendation ?? caseDoc.note ?? "Caso operacional aberto.");
  const assignee = caseDoc.assignee?.name ?? caseDoc.assignee_name ?? null;

  const cardClass = ["case-card"];
  if (priorityKey === "critical") cardClass.push("critical");
  else if (priorityKey === "high") cardClass.push("high");

  return (
    <article
      className={cardClass.join(" ")}
      style={{
        display: "grid",
        gap: 10,
        padding: 12,
        gridTemplateColumns: "1fr"
      }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 8 }}>
        <div style={{ display: "grid", gap: 2, minWidth: 0 }}>
          <button
            type="button"
            onClick={() => entityId && onOpenEntity(entityId)}
            disabled={!entityId}
            style={{
              background: "transparent",
              color: "var(--text-strong)",
              border: 0,
              padding: 0,
              minHeight: "auto",
              fontWeight: 700,
              fontSize: "var(--fs-base)",
              textAlign: "left",
              cursor: entityId ? "pointer" : "default",
              boxShadow: "none",
              justifyContent: "flex-start"
            }}
          >
            {entityName}
          </button>
          {entityId ? (
            <span
              className="num"
              style={{ color: "var(--text-muted)", fontSize: "var(--fs-2xs)", overflowWrap: "anywhere" }}
            >
              {entityId}
            </span>
          ) : null}
        </div>
        <Badge tone={priorityTone}>{priorityLabel(caseDoc.priority_label, caseDoc.priority_rank)}</Badge>
      </header>

      {summary ? (
        <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "var(--fs-sm)", lineHeight: 1.5 }}>{summary}</p>
      ) : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr auto",
          alignItems: "center",
          gap: 8
        }}
      >
        <span className="stat-label" style={{ fontSize: "var(--fs-2xs)" }}>
          Score
        </span>
        <strong className="num" style={{ color: "var(--accent-strong)" }}>
          {score.toFixed(3)}
        </strong>
        {assignee ? (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 4, color: "var(--text-muted)", fontSize: "var(--fs-xs)" }}>
            <UserCheck size={11} />
            {assignee}
          </span>
        ) : null}
      </div>

      {sla && slaTone ? (
        <div style={{ display: "grid", gap: 4 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: "var(--fs-xs)"
            }}
          >
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: slaTone.color, fontWeight: 700 }}>
              {sla.status === "breached" ? <AlertOctagon size={11} /> : <Clock size={11} />}
              {sla.remainingLabel}
            </span>
            <span className="stat-label">{sla.status === "breached" ? "vencido" : sla.status === "atrisk" ? "em risco" : "no prazo"}</span>
          </div>
          <div
            style={{
              height: 4,
              borderRadius: 999,
              background: "var(--surface-3)",
              overflow: "hidden"
            }}
          >
            <div
              style={{
                width: `${Math.max(2, sla.ratio * 100).toFixed(1)}%`,
                height: "100%",
                background: sla.status === "breached" ? "var(--danger)" : sla.status === "atrisk" ? "var(--warning)" : "var(--success)",
                transition: "width 220ms ease"
              }}
            />
          </div>
        </div>
      ) : null}

      <footer style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
        {column.secondaryAction ? (
          <button
            type="button"
            className="ghost sm"
            onClick={() => onUpdateStatus(id, column.secondaryAction!.status)}
          >
            <column.secondaryAction.icon size={13} />
            {column.secondaryAction.label}
          </button>
        ) : null}
        {column.primaryAction ? (
          <button type="button" className="sm" onClick={() => onUpdateStatus(id, column.primaryAction!.status)}>
            <column.primaryAction.icon size={13} />
            {column.primaryAction.label}
            <ArrowRight size={11} />
          </button>
        ) : null}
        {column.id !== "done" ? (
          <button
            type="button"
            className="ghost sm"
            onClick={() => onUpdateStatus(id, "dismissed")}
            title="Descartar caso"
          >
            <XCircle size={13} />
          </button>
        ) : null}
      </footer>
    </article>
  );
}
