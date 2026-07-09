"use client";

import {
  CalendarRange,
  CircleDollarSign,
  Coins,
  Database,
  HardDrive,
  KeyRound,
  Receipt,
  RefreshCcw,
  TrendingUp,
  Users
} from "lucide-react";
import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { cleanProtectedValue } from "@/lib/entity";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Sparkline } from "../ui/Sparkline";

type AnyDoc = Record<string, any>;

interface CostUsageData {
  period_days?: number;
  generated_at?: string;
  totals?: {
    predictions_total?: number;
    predictions_recent?: number;
    audit_events_total?: number;
    audit_events_recent?: number;
    feedback_recent?: number;
    api_keys_total?: number;
    api_keys_active?: number;
    projects?: number;
    models?: number;
    storage_bytes?: number;
    storage_gb?: number;
  };
  series?: ReadonlyArray<{ date: string; predictions: number; with_feedback: number }>;
  top_entities?: ReadonlyArray<{ entity: string; predictions: number }>;
  cost_estimate_brl?: {
    predictions?: number;
    audit_events?: number;
    storage?: number;
    total?: number;
  };
  pricing?: {
    currency?: string;
    per_prediction?: number;
    per_api_call?: number;
    per_gb_storage?: number;
  };
  methodological_warning?: string;
}

interface CostUsageViewProps {
  data: CostUsageData | null;
  loading: boolean;
  periodDays: number;
  onPeriodChange: (days: number) => void;
  onRefresh: () => void;
  formatNumber: (value: unknown) => string;
}

function formatBytes(bytes?: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index++;
  }
  return `${value.toFixed(value >= 100 || index === 0 ? 0 : 2)} ${units[index]}`;
}

function formatBRL(value?: number): string {
  if (value === undefined || value === null || Number.isNaN(value)) return "R$ 0,00";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2
  });
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      style={{
        background: "var(--surface-elev)",
        border: "1px solid var(--border-strong)",
        borderRadius: "var(--radius-sm)",
        boxShadow: "var(--shadow-md)",
        padding: "8px 10px",
        fontSize: "var(--fs-sm)"
      }}
    >
      <div style={{ color: "var(--text-muted)", fontSize: "var(--fs-xs)", marginBottom: 4 }}>
        {label}
      </div>
      {payload.map((entry: any) => (
        <div
          key={entry.dataKey}
          style={{ display: "flex", justifyContent: "space-between", gap: 12 }}
        >
          <span style={{ color: entry.color }}>{entry.name ?? entry.dataKey}</span>
          <strong className="num" style={{ color: "var(--text-strong)" }}>
            {typeof entry.value === "number" ? entry.value.toLocaleString("pt-BR") : entry.value}
          </strong>
        </div>
      ))}
    </div>
  );
}

const PERIOD_OPTIONS: ReadonlyArray<number> = [7, 14, 30, 60, 90];

export function CostUsageView({
  data,
  loading,
  periodDays,
  onPeriodChange,
  onRefresh,
  formatNumber
}: CostUsageViewProps) {
  const totals = data?.totals ?? {};
  const series = data?.series ?? [];
  const topEntities = data?.top_entities ?? [];
  const cost = data?.cost_estimate_brl ?? {};
  const pricing = data?.pricing ?? {};

  const sparkPredictions = useMemo<ReadonlyArray<number>>(
    () => series.map((row) => Number(row.predictions ?? 0)),
    [series]
  );

  const feedbackRate = useMemo<number>(() => {
    const recent = Number(totals.predictions_recent ?? 0);
    if (!recent) return 0;
    return Number(totals.feedback_recent ?? 0) / recent;
  }, [totals]);

  const dailyAverage = useMemo<number>(() => {
    if (!series.length) return 0;
    const sum = series.reduce((acc, row) => acc + Number(row.predictions ?? 0), 0);
    return sum / series.length;
  }, [series]);

  const monthlyProjection = useMemo<number>(() => {
    return dailyAverage * 30 * (Number(pricing.per_prediction ?? 0));
  }, [dailyAverage, pricing.per_prediction]);

  const generatedAt = data?.generated_at
    ? new Date(data.generated_at).toLocaleString("pt-BR", {
        dateStyle: "short",
        timeStyle: "short"
      })
    : "—";

  return (
    <section className="view-stack">
      <section className="surface" style={{ display: "grid", gap: 16 }}>
        <div className="section-heading split">
          <div className="section-title-row">
            <CircleDollarSign size={16} />
            <h2>Custo e consumo</h2>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span className="stat-label">Período</span>
            <div style={{ display: "flex", gap: 4 }}>
              {PERIOD_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`sm ${option === periodDays ? "" : "secondary"}`}
                  onClick={() => onPeriodChange(option)}
                >
                  {option}d
                </button>
              ))}
            </div>
            <button type="button" className="secondary sm" onClick={onRefresh} disabled={loading}>
              <RefreshCcw size={14} />
              Atualizar
            </button>
          </div>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)", maxWidth: 800 }}>
          Estimativas de uso e custo agregadas ao nível da organização. Custos são calculados via tabela
          ilustrativa de pricing (R$ {pricing.per_prediction ?? "—"} por predição). Em produção real,
          substitua o pricing pela tabela do provedor da sua infra.
        </p>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            color: "var(--text-muted)",
            fontSize: "var(--fs-xs)"
          }}
        >
          <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
            <CalendarRange size={11} />
            últimos {data?.period_days ?? periodDays} dias
          </span>
          <span>gerado em {generatedAt}</span>
        </div>
      </section>

      {!data ? (
        <section className="surface">
          <EmptyState
            icon={<Coins size={18} />}
            title={loading ? "Calculando consumo…" : "Sem dados de consumo"}
            text={
              loading
                ? "Aguarde a agregação dos endpoints de uso."
                : "Conecte-se ao backend e registre predições para popular este painel."
            }
          />
        </section>
      ) : (
        <>
          <div className="metric-grid">
            <CostMetric
              label="Custo estimado"
              value={formatBRL(cost.total)}
              icon={<Receipt size={16} />}
              tone="warn"
              subtitle={`projeção 30d: ${formatBRL(monthlyProjection)}`}
            />
            <CostMetric
              label="Predições no período"
              value={formatNumber(totals.predictions_recent ?? 0)}
              icon={<Database size={16} />}
              spark={sparkPredictions}
              subtitle={`${formatNumber(totals.predictions_total ?? 0)} no total · ${formatNumber(Math.round(dailyAverage))} / dia`}
            />
            <CostMetric
              label="Audit events"
              value={formatNumber(totals.audit_events_recent ?? 0)}
              icon={<TrendingUp size={16} />}
              subtitle={`${formatNumber(totals.audit_events_total ?? 0)} no total`}
            />
            <CostMetric
              label="API keys ativas"
              value={`${formatNumber(totals.api_keys_active ?? 0)} / ${formatNumber(totals.api_keys_total ?? 0)}`}
              icon={<KeyRound size={16} />}
              tone="good"
            />
            <CostMetric
              label="Armazenamento estimado"
              value={formatBytes(totals.storage_bytes)}
              icon={<HardDrive size={16} />}
              subtitle={`${formatNumber(totals.predictions_total ?? 0)} docs × ~1.8 KB`}
            />
          </div>

          <div className="chart-grid">
            <section className="surface chart-surface">
              <div className="section-heading split">
                <div className="section-title-row">
                  <TrendingUp size={16} />
                  <h2>Volume diário de predições</h2>
                </div>
                <Badge tone="accent">média {formatNumber(Math.round(dailyAverage))} / dia</Badge>
              </div>
              {series.length === 0 ? (
                <EmptyState
                  icon={<TrendingUp size={18} />}
                  title="Sem volume registrado"
                  text="Aguarde o primeiro lote de predições para popular a série."
                />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={series as any[]}>
                    <defs>
                      <linearGradient id="cuVolume" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--accent-strong)" stopOpacity={0.6} />
                        <stop offset="95%" stopColor="var(--accent-strong)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 4" />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} />
                    <YAxis stroke="var(--text-muted)" fontSize={11} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area
                      type="monotone"
                      dataKey="predictions"
                      stroke="var(--accent-strong)"
                      strokeWidth={2}
                      fill="url(#cuVolume)"
                      name="Predições"
                    />
                    <Area
                      type="monotone"
                      dataKey="with_feedback"
                      stroke="var(--success-strong)"
                      strokeWidth={2}
                      fill="transparent"
                      name="Com feedback"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </section>

            <section className="surface" style={{ display: "grid", gap: 16, alignContent: "start" }}>
              <div className="section-heading">
                <Coins size={16} />
                <h2>Composição do custo estimado</h2>
              </div>
              <CostBar
                label="Predições"
                value={cost.predictions ?? 0}
                total={cost.total ?? 0}
                color="var(--accent)"
              />
              <CostBar
                label="Audit events"
                value={cost.audit_events ?? 0}
                total={cost.total ?? 0}
                color="var(--info)"
              />
              <CostBar
                label="Armazenamento"
                value={cost.storage ?? 0}
                total={cost.total ?? 0}
                color="var(--warning)"
              />
              <div
                style={{
                  borderTop: "1px solid var(--border)",
                  paddingTop: 12,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}
              >
                <span className="stat-label">Total no período</span>
                <strong
                  className="num"
                  style={{ fontSize: "var(--fs-2xl)", color: "var(--text-strong)" }}
                >
                  {formatBRL(cost.total)}
                </strong>
              </div>
              <p
                style={{
                  margin: 0,
                  color: "var(--text-muted)",
                  fontSize: "var(--fs-xs)",
                  lineHeight: 1.6,
                  borderLeft: "3px solid var(--warning)",
                  paddingLeft: 10
                }}
              >
                {data.methodological_warning ?? "Estimativa ilustrativa."}
              </p>
            </section>
          </div>

          <section className="surface" style={{ display: "grid", gap: 12 }}>
            <div className="section-heading split">
              <div className="section-title-row">
                <Users size={16} />
                <h2>Top entidades por volume</h2>
              </div>
              <span className="stat-label">topo 10 do período</span>
            </div>
            {topEntities.length === 0 ? (
              <EmptyState
                icon={<Users size={18} />}
                title="Sem entidades registradas"
                text="Quando seu modelo começar a tomar decisões, as mais frequentes aparecem aqui."
              />
            ) : (
              <div style={{ display: "grid", gap: 6 }}>
                {topEntities.map((entry, index) => {
                  const ratio =
                    Number(totals.predictions_recent ?? 0) > 0
                      ? Number(entry.predictions) / Number(totals.predictions_recent)
                      : 0;
                  return (
                    <div
                      key={`${entry.entity}-${index}`}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "32px minmax(0, 1fr) 100px 80px",
                        gap: 12,
                        alignItems: "center",
                        padding: "8px 12px",
                        borderRadius: "var(--radius-sm)",
                        background:
                          index === 0
                            ? "linear-gradient(180deg, var(--accent-soft), var(--surface))"
                            : "var(--surface)",
                        border: "1px solid var(--border)"
                      }}
                    >
                      <span
                        className="num"
                        style={{
                          color: "var(--text-muted)",
                          fontSize: "var(--fs-sm)",
                          fontWeight: 600
                        }}
                      >
                        #{index + 1}
                      </span>
                      <strong
                        className="truncate"
                        style={{ color: "var(--text-strong)", fontSize: "var(--fs-sm)" }}
                        title={cleanProtectedValue(entry.entity) || "Entidade não nomeada"}
                      >
                        {cleanProtectedValue(entry.entity) || (
                          <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
                            Entidade não nomeada
                          </span>
                        )}
                      </strong>
                      <div
                        style={{
                          height: 6,
                          borderRadius: 999,
                          background: "var(--surface-3)",
                          overflow: "hidden"
                        }}
                      >
                        <div
                          style={{
                            width: `${(ratio * 100).toFixed(2)}%`,
                            height: "100%",
                            background: "var(--accent)"
                          }}
                        />
                      </div>
                      <span
                        className="num"
                        style={{ color: "var(--text-strong)", textAlign: "right" }}
                      >
                        {formatNumber(entry.predictions)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          <section className="surface" style={{ display: "grid", gap: 12 }}>
            <div className="section-heading">
              <Coins size={16} />
              <h2>Tabela de pricing usada</h2>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                gap: 12
              }}
            >
              <PricingCell label="Por predição" value={`R$ ${pricing.per_prediction?.toFixed(4) ?? "—"}`} />
              <PricingCell label="Por API call" value={`R$ ${pricing.per_api_call?.toFixed(4) ?? "—"}`} />
              <PricingCell label="Por GB armazenado" value={`R$ ${pricing.per_gb_storage?.toFixed(2) ?? "—"}`} />
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-xs)", margin: 0 }}>
              Para personalizar, edite as constantes em <code>backend/app/api/routes/usage.py</code> ou
              integre com sua tabela real de billing.
            </p>
            {feedbackRate > 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)", margin: 0 }}>
                Cobertura de feedback no período:{" "}
                <strong className="text-success">{(feedbackRate * 100).toFixed(1)}%</strong>
              </p>
            ) : null}
          </section>
        </>
      )}
    </section>
  );
}

interface CostMetricProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  tone?: "default" | "good" | "warn" | "bad";
  spark?: ReadonlyArray<number>;
  subtitle?: string;
}

function CostMetric({ label, value, icon, tone = "default", spark, subtitle }: CostMetricProps) {
  const className = ["metric", tone === "default" ? "" : tone].filter(Boolean).join(" ");
  const accent =
    tone === "good"
      ? "var(--success-strong)"
      : tone === "warn"
        ? "var(--warning-strong)"
        : tone === "bad"
          ? "var(--danger-strong)"
          : "var(--accent-strong)";
  return (
    <div className={className}>
      <span aria-hidden="true">{icon}</span>
      <small>{label}</small>
      <strong>{value}</strong>
      <div
        style={{
          gridColumn: "2",
          display: "grid",
          gap: 4,
          color: accent
        }}
      >
        {spark && spark.length > 1 ? <Sparkline values={spark} ariaLabel={`Tendência de ${label}`} /> : null}
        {subtitle ? (
          <small
            style={{
              color: "var(--text-muted)",
              fontSize: "var(--fs-2xs)",
              fontFamily: "var(--font-mono)",
              textTransform: "none",
              letterSpacing: 0
            }}
          >
            {subtitle}
          </small>
        ) : null}
      </div>
    </div>
  );
}

interface CostBarProps {
  label: string;
  value: number;
  total: number;
  color: string;
}

function CostBar({ label, value, total, color }: CostBarProps) {
  const ratio = total > 0 ? value / total : 0;
  return (
    <div style={{ display: "grid", gap: 6 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}
      >
        <span style={{ color: "var(--text)", fontSize: "var(--fs-sm)" }}>{label}</span>
        <strong className="num" style={{ color: "var(--text-strong)" }}>
          {formatBRL(value)}{" "}
          <span style={{ color: "var(--text-muted)", fontSize: "var(--fs-xs)" }}>
            ({(ratio * 100).toFixed(0)}%)
          </span>
        </strong>
      </div>
      <div
        style={{
          height: 8,
          borderRadius: 999,
          background: "var(--surface-3)",
          overflow: "hidden"
        }}
      >
        <div
          style={{
            width: `${(ratio * 100).toFixed(2)}%`,
            height: "100%",
            background: color,
            transition: "width 240ms var(--ease)"
          }}
        />
      </div>
    </div>
  );
}

function PricingCell({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        padding: "10px 12px",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-sm)",
        background: "var(--surface-2)"
      }}
    >
      <span className="stat-label">{label}</span>
      <strong className="num" style={{ display: "block", color: "var(--text-strong)", fontSize: "var(--fs-md)" }}>
        {value}
      </strong>
    </div>
  );
}
