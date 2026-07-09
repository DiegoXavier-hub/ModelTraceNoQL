"use client";

import { AlertOctagon, ArrowRight, Clock, X } from "lucide-react";
import { useMemo, useState } from "react";
import { entityDisplayName } from "@/lib/entity";

type AnyDoc = Record<string, any>;

interface SlaAlertBarProps {
  cases: ReadonlyArray<AnyDoc>;
  currentView: string;
  onGoToCases: () => void;
}

interface SlaSummary {
  breached: number;
  atRisk: number;
  next: AnyDoc | null;
}

function summarize(cases: ReadonlyArray<AnyDoc>): SlaSummary {
  let breached = 0;
  let atRisk = 0;
  let next: AnyDoc | null = null;
  let minRemaining = Number.POSITIVE_INFINITY;
  const now = Date.now();

  for (const caseDoc of cases) {
    const status = String(caseDoc.status ?? "open");
    if (status === "resolved" || status === "dismissed") continue;

    const dueRaw = caseDoc.due_at ?? caseDoc.sla_due_at;
    let dueMs: number | null = null;
    if (dueRaw) {
      const parsed = new Date(String(dueRaw)).getTime();
      if (!Number.isNaN(parsed)) dueMs = parsed;
    } else if (caseDoc.sla_hours && caseDoc.created_at) {
      const created = new Date(String(caseDoc.created_at)).getTime();
      if (!Number.isNaN(created)) dueMs = created + Number(caseDoc.sla_hours) * 3600_000;
    }
    if (dueMs === null) continue;

    const remaining = dueMs - now;
    if (remaining <= 0) {
      breached++;
      continue;
    }
    if (remaining < 6 * 3600_000) atRisk++;
    if (remaining < minRemaining) {
      minRemaining = remaining;
      next = caseDoc;
    }
  }

  return { breached, atRisk, next };
}

function formatRemaining(ms: number): string {
  if (ms < 60_000) return "< 1 min";
  if (ms < 3600_000) return `${Math.round(ms / 60_000)} min`;
  if (ms < 24 * 3600_000) return `${Math.round(ms / 3600_000)} h`;
  return `${Math.round(ms / (24 * 3600_000))} d`;
}

export function SlaAlertBar({ cases, currentView, onGoToCases }: SlaAlertBarProps) {
  const [dismissed, setDismissed] = useState(false);
  const summary = useMemo(() => summarize(cases), [cases]);

  if (currentView === "cases") return null;
  if (dismissed) return null;
  if (!summary.breached && !summary.atRisk) return null;

  const tone = summary.breached > 0 ? "danger" : "warning";
  const Icon = summary.breached > 0 ? AlertOctagon : Clock;

  const headline =
    summary.breached > 0
      ? `${summary.breached} ${summary.breached === 1 ? "caso vencido" : "casos vencidos"} de SLA`
      : `${summary.atRisk} ${summary.atRisk === 1 ? "caso" : "casos"} com SLA em risco`;

  const detail = (() => {
    const parts: string[] = [];
    if (summary.breached > 0 && summary.atRisk > 0) {
      parts.push(`+ ${summary.atRisk} em risco`);
    }
    if (summary.next?.entity) {
      const name = entityDisplayName(summary.next.entity, "");
      if (name) parts.push(`proximo: ${name}`);
    }
    return parts.join(" · ");
  })();

  const colors =
    tone === "danger"
      ? {
          background:
            "linear-gradient(180deg, color-mix(in srgb, var(--danger) 22%, var(--surface)), color-mix(in srgb, var(--danger) 12%, var(--surface)))",
          border: "rgba(239, 68, 68, 0.45)",
          icon: "var(--danger-strong)"
        }
      : {
          background:
            "linear-gradient(180deg, color-mix(in srgb, var(--warning) 22%, var(--surface)), color-mix(in srgb, var(--warning) 12%, var(--surface)))",
          border: "rgba(245, 158, 11, 0.45)",
          icon: "var(--warning-strong)"
        };

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: "grid",
        gridTemplateColumns: "auto 1fr auto auto",
        gap: 12,
        alignItems: "center",
        padding: "10px 14px",
        marginBottom: 16,
        background: colors.background,
        border: `1px solid ${colors.border}`,
        borderRadius: "var(--radius)",
        boxShadow: "var(--shadow-sm)"
      }}
    >
      <span
        aria-hidden="true"
        style={{
          display: "inline-grid",
          placeItems: "center",
          width: 32,
          height: 32,
          borderRadius: "var(--radius-sm)",
          background: "color-mix(in srgb, currentColor 18%, transparent)",
          color: colors.icon
        }}
      >
        <Icon size={16} />
      </span>
      <div style={{ display: "grid", gap: 2, minWidth: 0 }}>
        <strong style={{ color: "var(--text-strong)", fontSize: "var(--fs-base)" }}>
          {headline}
        </strong>
        {detail ? (
          <span style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)" }}>
            {detail}
            {summary.next && summary.next.due_at ? (
              <>
                {" · "}
                <span className="num">
                  proxima expira em{" "}
                  {formatRemaining(
                    Math.max(0, new Date(String(summary.next.due_at)).getTime() - Date.now())
                  )}
                </span>
              </>
            ) : null}
          </span>
        ) : null}
      </div>
      <button type="button" className="sm" onClick={onGoToCases}>
        Ir para fila
        <ArrowRight size={13} />
      </button>
      <button
        type="button"
        className="ghost icon-only sm"
        onClick={() => setDismissed(true)}
        aria-label="Dispensar alerta de SLA"
      >
        <X size={14} />
      </button>
    </div>
  );
}
