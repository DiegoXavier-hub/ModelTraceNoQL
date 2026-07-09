"use client";

import { Activity, Flame, Info, RefreshCcw, TrendingDown, TrendingUp } from "lucide-react";
import { useMemo, useState } from "react";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";

type AnyDoc = Record<string, any>;

interface DriftBucket {
  id: string;
  created_at?: string;
  model_version?: string;
  score_psi: number;
  score_status: string;
  values: Record<string, number>;
}

interface DriftFeature {
  name: string;
  type: string;
  max_psi: number;
  samples: number;
}

interface DriftHeatmapData {
  model_id?: string;
  buckets: ReadonlyArray<DriftBucket>;
  features: ReadonlyArray<DriftFeature>;
  thresholds?: { attention: number; drift: number };
}

interface DriftHeatmapViewProps {
  data: DriftHeatmapData | null;
  loading: boolean;
  selectedModelId: string;
  onRefresh: () => void | Promise<void>;
  onRunDrift: () => void | Promise<void>;
}

function colorForPsi(value: number, attention: number, drift: number): {
  background: string;
  border: string;
  text: string;
  level: "stable" | "attention" | "drift";
} {
  if (value >= drift) {
    return {
      background: "color-mix(in srgb, var(--danger) 32%, var(--surface))",
      border: "rgba(239, 68, 68, 0.5)",
      text: "var(--danger-strong)",
      level: "drift"
    };
  }
  if (value >= attention) {
    return {
      background: "color-mix(in srgb, var(--warning) 32%, var(--surface))",
      border: "rgba(245, 158, 11, 0.5)",
      text: "var(--warning-strong)",
      level: "attention"
    };
  }
  if (value >= attention * 0.5) {
    return {
      background: "color-mix(in srgb, var(--success) 18%, var(--surface))",
      border: "rgba(16, 185, 129, 0.36)",
      text: "var(--success-strong)",
      level: "stable"
    };
  }
  return {
    background: "var(--surface-2)",
    border: "var(--border)",
    text: "var(--text-muted)",
    level: "stable"
  };
}

function formatBucketDate(value?: string): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

function formatBucketTime(value?: string): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export function DriftHeatmapView({
  data,
  loading,
  selectedModelId,
  onRefresh,
  onRunDrift
}: DriftHeatmapViewProps) {
  const [hovered, setHovered] = useState<{ feature: string; bucketId: string } | null>(null);

  const features = data?.features ?? [];
  const buckets = data?.buckets ?? [];
  const thresholds = data?.thresholds ?? { attention: 0.1, drift: 0.25 };

  const summary = useMemo(() => {
    if (!buckets.length || !features.length) {
      return { driftCount: 0, attentionCount: 0, totalCells: 0, latestPsi: 0 };
    }
    let driftCount = 0;
    let attentionCount = 0;
    let totalCells = 0;
    for (const bucket of buckets) {
      for (const feature of features) {
        const value = bucket.values[feature.name];
        if (value === undefined) continue;
        totalCells++;
        if (value >= thresholds.drift) driftCount++;
        else if (value >= thresholds.attention) attentionCount++;
      }
    }
    const latestBucket = buckets[buckets.length - 1];
    return {
      driftCount,
      attentionCount,
      totalCells,
      latestPsi: latestBucket?.score_psi ?? 0
    };
  }, [buckets, features, thresholds]);

  const hoveredCell = useMemo(() => {
    if (!hovered) return null;
    const bucket = buckets.find((entry) => entry.id === hovered.bucketId);
    if (!bucket) return null;
    const value = bucket.values[hovered.feature];
    if (value === undefined) return null;
    return {
      feature: hovered.feature,
      bucket,
      value,
      tone: colorForPsi(value, thresholds.attention, thresholds.drift)
    };
  }, [hovered, buckets, thresholds]);

  return (
    <section className="view-stack">
      <section className="surface" style={{ display: "grid", gap: 16 }}>
        <div className="section-heading split">
          <div className="section-title-row">
            <Flame size={16} />
            <h2>Drift Heatmap por feature</h2>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" className="secondary sm" onClick={() => onRefresh()} disabled={loading}>
              <RefreshCcw size={14} />
              Atualizar
            </button>
            <button type="button" className="sm" onClick={() => onRunDrift()} disabled={!selectedModelId || loading}>
              <Activity size={14} />
              Rodar drift
            </button>
          </div>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)", maxWidth: 760 }}>
          Cada celula mostra o PSI (Population Stability Index) da feature naquele relatorio de drift. Quanto mais
          intenso, maior o desvio entre periodo de referencia e periodo atual. PSI {`>=`} {thresholds.drift.toFixed(2)}{" "}
          indica drift detectado, PSI {`>=`} {thresholds.attention.toFixed(2)} pede atencao.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
          <SummaryStat label="Buckets" value={String(buckets.length)} />
          <SummaryStat label="Features" value={String(features.length)} />
          <SummaryStat
            label="Drift detectado"
            value={String(summary.driftCount)}
            tone={summary.driftCount > 0 ? "danger" : "neutral"}
          />
          <SummaryStat
            label="Atenção"
            value={String(summary.attentionCount)}
            tone={summary.attentionCount > 0 ? "warn" : "neutral"}
          />
        </div>

        <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
          <span className="stat-label">Legenda</span>
          <LegendChip label="Estavel" tone="stable" />
          <LegendChip label={`PSI >= ${thresholds.attention.toFixed(2)}`} tone="attention" />
          <LegendChip label={`PSI >= ${thresholds.drift.toFixed(2)}`} tone="drift" />
        </div>
      </section>

      {!buckets.length || !features.length ? (
        <section className="surface">
          <EmptyState
            icon={<Flame size={18} />}
            title="Sem historico de drift ainda"
            text={
              !selectedModelId
                ? "Selecione um modelo no sidebar para visualizar drift."
                : "Rode pelo menos um relatorio de drift para popular o heatmap."
            }
            action={
              selectedModelId ? (
                <button type="button" onClick={() => onRunDrift()} disabled={loading}>
                  <Activity size={15} />
                  Rodar drift agora
                </button>
              ) : null
            }
          />
        </section>
      ) : (
        <section className="surface" style={{ display: "grid", gap: 16, overflowX: "auto" }}>
          <DriftMatrix
            features={features}
            buckets={buckets}
            thresholds={thresholds}
            onHover={setHovered}
          />
          <div style={{ display: "grid", gap: 8 }}>
            <span className="stat-label">Score do modelo (top-level PSI)</span>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: `220px repeat(${buckets.length}, minmax(64px, 1fr))`,
                gap: 1,
                background: "var(--border)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                overflow: "hidden"
              }}
            >
              <div className="drift-cell legend">prediction.score</div>
              {buckets.map((bucket) => {
                const tone = colorForPsi(bucket.score_psi, thresholds.attention, thresholds.drift);
                return (
                  <div
                    key={`score-${bucket.id}`}
                    title={`${formatBucketDate(bucket.created_at)} — PSI ${bucket.score_psi.toFixed(3)}`}
                    style={{
                      background: tone.background,
                      color: tone.text,
                      padding: "10px 8px",
                      textAlign: "center",
                      fontFamily: "var(--font-mono)",
                      fontSize: "var(--fs-xs)",
                      fontWeight: 600
                    }}
                  >
                    {bucket.score_psi.toFixed(3)}
                  </div>
                );
              })}
            </div>
          </div>

          {hoveredCell ? <CellDetail cell={hoveredCell} thresholds={thresholds} /> : <CellHint />}
        </section>
      )}
    </section>
  );
}

interface SummaryStatProps {
  label: string;
  value: string;
  tone?: "neutral" | "danger" | "warn";
}

function SummaryStat({ label, value, tone = "neutral" }: SummaryStatProps) {
  const accent =
    tone === "danger" ? "var(--danger-strong)" : tone === "warn" ? "var(--warning-strong)" : "var(--text-strong)";
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
      <strong className="num" style={{ color: accent, fontSize: "var(--fs-lg)" }}>
        {value}
      </strong>
    </div>
  );
}

interface LegendChipProps {
  label: string;
  tone: "stable" | "attention" | "drift";
}

function LegendChip({ label, tone }: LegendChipProps) {
  const styles =
    tone === "drift"
      ? { background: "color-mix(in srgb, var(--danger) 32%, var(--surface))", color: "var(--danger-strong)" }
      : tone === "attention"
        ? { background: "color-mix(in srgb, var(--warning) 32%, var(--surface))", color: "var(--warning-strong)" }
        : { background: "var(--surface-2)", color: "var(--text-muted)" };
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "3px 9px",
        borderRadius: "var(--radius-pill)",
        fontSize: "var(--fs-xs)",
        fontWeight: 700,
        ...styles
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: 2,
          background: "currentColor",
          opacity: 0.55
        }}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}

interface DriftMatrixProps {
  features: ReadonlyArray<DriftFeature>;
  buckets: ReadonlyArray<DriftBucket>;
  thresholds: { attention: number; drift: number };
  onHover: (entry: { feature: string; bucketId: string } | null) => void;
}

function DriftMatrix({ features, buckets, thresholds, onHover }: DriftMatrixProps) {
  const columns = `220px repeat(${buckets.length}, minmax(64px, 1fr))`;

  return (
    <div className="drift-heatmap" style={{ gridTemplateColumns: columns }}>
      <div className="drift-cell legend">feature \\ bucket</div>
      {buckets.map((bucket) => (
        <div
          key={`head-${bucket.id}`}
          className="drift-cell legend"
          style={{ flexDirection: "column", display: "grid", gap: 2 }}
        >
          <span>{formatBucketDate(bucket.created_at)}</span>
          <small style={{ color: "var(--text-subtle)", fontSize: 9 }}>
            {formatBucketTime(bucket.created_at)}
          </small>
        </div>
      ))}

      {features.map((feature) => (
        <FeatureRow
          key={feature.name}
          feature={feature}
          buckets={buckets}
          thresholds={thresholds}
          onHover={onHover}
        />
      ))}
    </div>
  );
}

interface FeatureRowProps {
  feature: DriftFeature;
  buckets: ReadonlyArray<DriftBucket>;
  thresholds: { attention: number; drift: number };
  onHover: (entry: { feature: string; bucketId: string } | null) => void;
}

function FeatureRow({ feature, buckets, thresholds, onHover }: FeatureRowProps) {
  const tone = colorForPsi(feature.max_psi, thresholds.attention, thresholds.drift);
  return (
    <>
      <div
        className="drift-cell legend"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr auto",
          alignItems: "center",
          gap: 6,
          textAlign: "left",
          padding: "6px 10px"
        }}
      >
        <strong style={{ color: "var(--text)", fontSize: "var(--fs-sm)", fontWeight: 600 }}>
          {feature.name}
        </strong>
        <span
          style={{
            fontSize: "var(--fs-2xs)",
            color: tone.text,
            fontFamily: "var(--font-mono)",
            fontWeight: 700
          }}
          title={`PSI maximo observado: ${feature.max_psi.toFixed(3)}`}
        >
          max {feature.max_psi.toFixed(2)}
        </span>
      </div>
      {buckets.map((bucket) => {
        const value = bucket.values[feature.name];
        if (value === undefined) {
          return (
            <div
              key={`${feature.name}-${bucket.id}`}
              className="drift-cell"
              style={{
                background: "var(--surface-2)",
                color: "var(--text-subtle)",
                fontSize: "var(--fs-2xs)"
              }}
            >
              —
            </div>
          );
        }
        const cellTone = colorForPsi(value, thresholds.attention, thresholds.drift);
        return (
          <button
            key={`${feature.name}-${bucket.id}`}
            type="button"
            className="drift-cell"
            onMouseEnter={() => onHover({ feature: feature.name, bucketId: bucket.id })}
            onMouseLeave={() => onHover(null)}
            onFocus={() => onHover({ feature: feature.name, bucketId: bucket.id })}
            onBlur={() => onHover(null)}
            style={{
              background: cellTone.background,
              color: cellTone.text,
              fontWeight: cellTone.level === "stable" ? 500 : 700,
              border: "none"
            }}
            aria-label={`${feature.name}, ${formatBucketDate(bucket.created_at)}, PSI ${value.toFixed(3)}`}
          >
            {value.toFixed(2)}
          </button>
        );
      })}
    </>
  );
}

interface CellDetailProps {
  cell: {
    feature: string;
    bucket: DriftBucket;
    value: number;
    tone: { level: "stable" | "attention" | "drift"; text: string };
  };
  thresholds: { attention: number; drift: number };
}

function CellDetail({ cell, thresholds }: CellDetailProps) {
  const labelTone = cell.tone.level === "drift" ? "danger" : cell.tone.level === "attention" ? "warn" : "success";
  const TrendIcon = cell.value > thresholds.drift ? TrendingUp : cell.value < thresholds.attention ? TrendingDown : Activity;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "auto 1fr auto",
        alignItems: "center",
        gap: 16,
        padding: "10px 14px",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        background: "var(--surface)"
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
          color: cell.tone.text
        }}
      >
        <TrendIcon size={16} />
      </span>
      <div style={{ display: "grid", gap: 2 }}>
        <strong style={{ color: "var(--text-strong)" }}>{cell.feature}</strong>
        <span style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)" }}>
          {formatBucketDate(cell.bucket.created_at)} {formatBucketTime(cell.bucket.created_at)} · versao{" "}
          {cell.bucket.model_version ?? "—"}
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
        <strong className="num" style={{ fontSize: "var(--fs-lg)", color: cell.tone.text }}>
          PSI {cell.value.toFixed(3)}
        </strong>
        <Badge tone={labelTone}>{cell.tone.level}</Badge>
      </div>
    </div>
  );
}

function CellHint() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 12px",
        color: "var(--text-muted)",
        fontSize: "var(--fs-sm)",
        border: "1px dashed var(--border)",
        borderRadius: "var(--radius-sm)"
      }}
    >
      <Info size={14} />
      Passe o mouse sobre uma celula para ver detalhes.
    </div>
  );
}
