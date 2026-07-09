"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Database,
  Gauge,
  GitCompare,
  LineChart as LineChartIcon,
  Sparkles,
  TrendingUp,
  Zap
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { Kpi } from "../ui/Kpi";
import { Trend } from "../ui/Trend";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";

type AnyDoc = Record<string, any>;

interface HealthPart {
  label: string;
  value: number;
  detail: string;
  tone: "positive" | "negative";
}

interface InsightRow {
  tone: "good" | "warn" | "bad" | "info";
  title: string;
  detail: string;
}

interface OverviewViewProps {
  healthScore: number;
  healthParts: ReadonlyArray<HealthPart>;
  insightRows: ReadonlyArray<InsightRow>;
  kpis: AnyDoc;
  actionableRate: number;
  dashboard: AnyDoc | null;
  confusion: AnyDoc;
  versions: ReadonlyArray<AnyDoc>;
  productionVersion?: AnyDoc;
  selectedModelPrimaryMetric?: string;
  positiveLabel: string;
  formatNumber: (value: unknown) => string;
  formatPercent: (value: number | undefined) => string;
  onOpenPredictions: (label?: string, feedback?: string, message?: string) => void;
  onGoToSection: (view: string, section: string, message: string) => void;
}

function statusClass(score: number): string {
  if (score >= 82) return "good";
  if (score >= 62) return "warn";
  return "bad";
}

function deltaFromSeries(series: ReadonlyArray<AnyDoc> | undefined, key: string): number | null {
  if (!series || series.length < 2) return null;
  const numeric = series
    .map((row) => Number(row[key] ?? 0))
    .filter((value) => Number.isFinite(value));
  if (numeric.length < 2) return null;
  const head = numeric.slice(0, Math.max(1, Math.floor(numeric.length / 2)));
  const tail = numeric.slice(-Math.max(1, Math.floor(numeric.length / 2)));
  const headAvg = head.reduce((acc, value) => acc + value, 0) / head.length;
  const tailAvg = tail.reduce((acc, value) => acc + value, 0) / tail.length;
  if (headAvg === 0) return null;
  return (tailAvg - headAvg) / headAvg;
}

function sparkValues(series: ReadonlyArray<AnyDoc> | undefined, key: string): ReadonlyArray<number> {
  if (!series) return [];
  return series.map((row) => Number(row[key] ?? 0)).filter((value) => Number.isFinite(value));
}

const CHART_THEME = {
  grid: "var(--border)",
  axis: "var(--text-muted)",
  accent: "var(--accent-strong)",
  success: "var(--success-strong)",
  info: "var(--info-strong)"
};

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
        fontSize: "var(--fs-sm)",
        minWidth: 120
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

export function OverviewView({
  healthScore,
  healthParts,
  insightRows,
  kpis,
  actionableRate,
  dashboard,
  confusion,
  versions,
  productionVersion,
  selectedModelPrimaryMetric,
  positiveLabel,
  formatNumber,
  formatPercent,
  onOpenPredictions,
  onGoToSection
}: OverviewViewProps) {
  const ringClass = statusClass(healthScore);
  const volumeSeries = (dashboard?.volume_series as ReadonlyArray<AnyDoc>) ?? [];
  const histogram = (dashboard?.score_histogram as ReadonlyArray<AnyDoc>) ?? [];
  const totalPredictionsSpark = sparkValues(volumeSeries, "count");
  const totalPredictionsTrend = deltaFromSeries(volumeSeries, "count");
  const feedbackSpark = sparkValues(volumeSeries, "feedback");
  const feedbackTrend = deltaFromSeries(volumeSeries, "feedback");

  const totalConfusion =
    (Number(confusion.tp ?? 0) || 0) +
    (Number(confusion.fp ?? 0) || 0) +
    (Number(confusion.tn ?? 0) || 0) +
    (Number(confusion.fn ?? 0) || 0);

  const feedbackRate = Number(kpis.feedback_rate ?? 0);

  return (
    <section className="view-stack">
      <div className="overview-grid">
        <div className="health-panel">
          <div
            className={`health-ring ${ringClass}`}
            style={{ ["--score" as any]: `${healthScore}%` }}
            role="img"
            aria-label={`Health score ${healthScore} de 100`}
          >
            <strong>{healthScore}</strong>
            <span>health</span>
          </div>
          <div className="health-copy">
            <h2>Saúde operacional do modelo</h2>
            <p>
              Sinal executivo combinando feedback, performance, alertas e capacidade.
              Clique nos KPIs abaixo para investigar.
            </p>
            <div className="health-tags">
              <span>
                <Activity size={11} style={{ marginRight: 4 }} />
                {versions.length} {versions.length === 1 ? "versão" : "versões"}
              </span>
              <span>
                <Gauge size={11} style={{ marginRight: 4 }} />
                {selectedModelPrimaryMetric || "recall"}
              </span>
              <span>
                <Sparkles size={11} style={{ marginRight: 4 }} />
                {productionVersion?.version || "sem produção"}
              </span>
            </div>
            <div className="health-breakdown" aria-label="Composição da saúde operacional">
              {healthParts.map((part) => (
                <div className={part.tone} key={part.label}>
                  <span>{part.label}</span>
                  <strong>
                    {part.value >= 0 ? "+" : ""}
                    {Math.round(part.value)}
                  </strong>
                  <small>{part.detail}</small>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="insight-panel">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2>Prioridades</h2>
            <Badge tone="accent">
              <TrendingUp size={11} />
              auto-detectadas
            </Badge>
          </div>
          {insightRows.map((row) => (
            <div className={`insight ${row.tone}`} key={row.title}>
              <span aria-hidden="true" />
              <div>
                <strong>{row.title}</strong>
                <p>{row.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="metric-grid">
        <Kpi
          label="Predições"
          value={formatNumber(kpis.total_predictions ?? 0)}
          icon={<Database size={16} />}
          trend={totalPredictionsTrend}
          spark={totalPredictionsSpark}
          onClick={() => onOpenPredictions()}
        />
        <Kpi
          label="Acionáveis"
          value={formatPercent(actionableRate)}
          icon={<AlertTriangle size={16} />}
          tone="bad"
          trendInvert
          trend={deltaFromSeries(volumeSeries, "actionable")}
          spark={sparkValues(volumeSeries, "actionable")}
          onClick={() => onOpenPredictions(positiveLabel, "all", "Filtro: acionáveis.")}
        />
        <Kpi
          label="Feedback"
          value={formatPercent(feedbackRate)}
          icon={<CheckCircle2 size={16} />}
          tone="good"
          trend={feedbackTrend}
          spark={feedbackSpark}
          onClick={() => onOpenPredictions("all", "with", "Filtro: com feedback.")}
        />
        <Kpi
          label="Score médio"
          value={formatNumber(kpis.avg_score ?? 0)}
          icon={<Gauge size={16} />}
          spark={sparkValues(volumeSeries, "avg_score")}
          onClick={() => onOpenPredictions("all", "all", "Predições abertas.")}
        />
        <Kpi
          label="Alertas"
          value={formatNumber(kpis.active_alerts ?? 0)}
          icon={<Zap size={16} />}
          tone={Number(kpis.active_alerts ?? 0) > 0 ? "warn" : "default"}
          onClick={() => onGoToSection("operations", "active-alerts", "Alertas ativos.")}
        />
      </div>

      <div className="chart-grid">
        <section className="surface chart-surface">
          <div className="section-heading">
            <LineChartIcon size={16} />
            <h2>Volume temporal</h2>
            {totalPredictionsTrend !== null ? (
              <div style={{ marginLeft: "auto" }}>
                <Trend delta={totalPredictionsTrend} format="percent" />
              </div>
            ) : null}
          </div>
          {volumeSeries.length === 0 ? (
            <EmptyState
              icon={<LineChartIcon size={18} />}
              title="Sem dados"
              text="Aguardando primeiras predições para construir a série temporal."
            />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={volumeSeries as any[]}>
                <defs>
                  <linearGradient id="ovVolume" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_THEME.accent} stopOpacity={0.6} />
                    <stop offset="95%" stopColor={CHART_THEME.accent} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 4" stroke={CHART_THEME.grid} />
                <XAxis dataKey="date" stroke={CHART_THEME.axis} fontSize={11} />
                <YAxis stroke={CHART_THEME.axis} fontSize={11} />
                <Tooltip content={<ChartTooltip />} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke={CHART_THEME.accent}
                  strokeWidth={2}
                  dot={false}
                  fill="url(#ovVolume)"
                  name="Predições"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </section>

        <section className="surface chart-surface">
          <div className="section-heading">
            <BarChart3 size={16} />
            <h2>Distribuição de score</h2>
          </div>
          {histogram.length === 0 ? (
            <EmptyState
              icon={<BarChart3 size={18} />}
              title="Sem distribuição"
              text="Ainda não há histograma calculado para esse modelo."
            />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={histogram as any[]}>
                <CartesianGrid strokeDasharray="3 4" stroke={CHART_THEME.grid} />
                <XAxis dataKey="bucket" stroke={CHART_THEME.axis} fontSize={11} />
                <YAxis stroke={CHART_THEME.axis} fontSize={11} />
                <Tooltip content={<ChartTooltip />} />
                <Bar
                  dataKey="count"
                  fill={CHART_THEME.success}
                  radius={[6, 6, 0, 0]}
                  name="Predições"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      <section className="surface">
        <div className="section-heading split">
          <div className="section-title-row">
            <GitCompare size={16} />
            <h2>Matriz de confusão</h2>
          </div>
          <span className="stat-label">{formatNumber(totalConfusion)} eventos com feedback</span>
        </div>
        <div className="matrix-grid">
          {(["tp", "fp", "tn", "fn"] as const).map((key) => {
            const value = Number(confusion[key] ?? 0);
            const tone =
              key === "tp"
                ? "var(--success-strong)"
                : key === "fp"
                  ? "var(--warning-strong)"
                  : key === "fn"
                    ? "var(--danger-strong)"
                    : "var(--info-strong)";
            const ratio = totalConfusion > 0 ? value / totalConfusion : 0;
            return (
              <div key={key}>
                <span style={{ color: tone }}>{key.toUpperCase()}</span>
                <strong>{formatNumber(value)}</strong>
                <small style={{ color: "var(--text-muted)", fontSize: "var(--fs-xs)" }}>
                  {(ratio * 100).toFixed(1)}% do total
                </small>
              </div>
            );
          })}
        </div>
      </section>
    </section>
  );
}
