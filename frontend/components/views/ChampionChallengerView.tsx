"use client";

import { ArrowRight, Crown, Sparkles, Swords, Trophy } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Trend } from "../ui/Trend";

type AnyDoc = Record<string, any>;

interface VersionLike {
  _id?: string;
  version?: string;
  status?: string;
  algorithm?: string;
  primary_metric?: string;
  offline_metrics?: AnyDoc;
  [key: string]: unknown;
}

interface ComparisonResult {
  model_id?: string;
  version_a?: { metadata?: AnyDoc; online_summary?: AnyDoc };
  version_b?: { metadata?: AnyDoc; online_summary?: AnyDoc };
  delta?: AnyDoc;
  methodological_warning?: string;
}

interface ChampionChallengerViewProps {
  versions: ReadonlyArray<VersionLike>;
  selectedModelId: string;
  result: ComparisonResult | null;
  loading: boolean;
  onRunComparison: (championVersion: string, challengerVersion: string) => void | Promise<void>;
  onPromote: (challengerVersion: string) => void | Promise<void>;
  formatNumber: (value: unknown) => string;
  formatPercent: (value: number | undefined) => string;
}

interface SideStats {
  predictionCount: number;
  positiveRate: number;
  avgScore: number;
  withFeedback: number;
  confusion: { tp: number; fp: number; tn: number; fn: number };
  precision: number | null;
  recall: number | null;
  f1: number | null;
}

function deriveStats(summary: AnyDoc | undefined): SideStats {
  const predictionCount = Number(summary?.prediction_count ?? 0);
  const positiveRate = Number(summary?.positive_rate ?? 0);
  const avgScore = Number(summary?.avg_score ?? 0);
  const withFeedback = Number(summary?.with_feedback ?? 0);
  const cm = (summary?.confusion_matrix ?? {}) as AnyDoc;
  const tp = Number(cm.tp ?? 0);
  const fp = Number(cm.fp ?? 0);
  const tn = Number(cm.tn ?? 0);
  const fn = Number(cm.fn ?? 0);
  const denomP = tp + fp;
  const denomR = tp + fn;
  const precision = denomP > 0 ? tp / denomP : null;
  const recall = denomR > 0 ? tp / denomR : null;
  const f1 =
    precision !== null && recall !== null && precision + recall > 0
      ? (2 * precision * recall) / (precision + recall)
      : null;
  return { predictionCount, positiveRate, avgScore, withFeedback, confusion: { tp, fp, tn, fn }, precision, recall, f1 };
}

function pickDefaultPair(versions: ReadonlyArray<VersionLike>): {
  champion: string;
  challenger: string;
} {
  if (!versions.length) return { champion: "", challenger: "" };
  const production = versions.find((v) => v.status === "production");
  const champion = production?.version ?? versions[0].version ?? "";
  const candidate = versions.find((v) => v.version !== champion && v.status !== "deprecated");
  const challenger = candidate?.version ?? versions[Math.min(1, versions.length - 1)]?.version ?? "";
  return { champion: String(champion || ""), challenger: String(challenger || "") };
}

export function ChampionChallengerView({
  versions,
  selectedModelId,
  result,
  loading,
  onRunComparison,
  onPromote,
  formatNumber,
  formatPercent
}: ChampionChallengerViewProps) {
  const defaults = useMemo(() => pickDefaultPair(versions), [versions]);
  const [championVersion, setChampionVersion] = useState(defaults.champion);
  const [challengerVersion, setChallengerVersion] = useState(defaults.challenger);

  useEffect(() => {
    if (!championVersion && defaults.champion) setChampionVersion(defaults.champion);
    if (!challengerVersion && defaults.challenger) setChallengerVersion(defaults.challenger);
  }, [defaults.champion, defaults.challenger]);

  const championMeta = result?.version_a?.metadata as AnyDoc | undefined;
  const challengerMeta = result?.version_b?.metadata as AnyDoc | undefined;
  const championStats = useMemo(() => deriveStats(result?.version_a?.online_summary), [result]);
  const challengerStats = useMemo(() => deriveStats(result?.version_b?.online_summary), [result]);

  const hasResult = Boolean(result?.version_a && result?.version_b);

  const compareRows = useMemo(() => {
    if (!hasResult) return [];
    return [
      {
        key: "predictionCount",
        label: "Predições",
        value: formatNumber(challengerStats.predictionCount) + " vs " + formatNumber(championStats.predictionCount),
        chart: { Champion: championStats.predictionCount, Challenger: challengerStats.predictionCount }
      },
      {
        key: "avgScore",
        label: "Score médio",
        value: `${challengerStats.avgScore.toFixed(3)} vs ${championStats.avgScore.toFixed(3)}`,
        chart: { Champion: championStats.avgScore, Challenger: challengerStats.avgScore }
      },
      {
        key: "positiveRate",
        label: "Taxa positiva",
        value: `${formatPercent(challengerStats.positiveRate)} vs ${formatPercent(championStats.positiveRate)}`,
        chart: { Champion: championStats.positiveRate, Challenger: challengerStats.positiveRate }
      },
      {
        key: "precision",
        label: "Precision",
        value:
          challengerStats.precision !== null && championStats.precision !== null
            ? `${formatPercent(challengerStats.precision)} vs ${formatPercent(championStats.precision)}`
            : "—",
        chart: { Champion: championStats.precision ?? 0, Challenger: challengerStats.precision ?? 0 }
      },
      {
        key: "recall",
        label: "Recall",
        value:
          challengerStats.recall !== null && championStats.recall !== null
            ? `${formatPercent(challengerStats.recall)} vs ${formatPercent(championStats.recall)}`
            : "—",
        chart: { Champion: championStats.recall ?? 0, Challenger: challengerStats.recall ?? 0 }
      },
      {
        key: "f1",
        label: "F1",
        value:
          challengerStats.f1 !== null && championStats.f1 !== null
            ? `${(challengerStats.f1 * 100).toFixed(1)}% vs ${(championStats.f1 * 100).toFixed(1)}%`
            : "—",
        chart: { Champion: championStats.f1 ?? 0, Challenger: challengerStats.f1 ?? 0 }
      }
    ];
  }, [hasResult, championStats, challengerStats, formatNumber, formatPercent]);

  const winnerHint = useMemo(() => {
    if (!hasResult) return null;
    let challengerWins = 0;
    let championWins = 0;
    if (challengerStats.f1 !== null && championStats.f1 !== null) {
      if (challengerStats.f1 > championStats.f1) challengerWins++;
      else if (challengerStats.f1 < championStats.f1) championWins++;
    }
    if (challengerStats.recall !== null && championStats.recall !== null) {
      if (challengerStats.recall > championStats.recall) challengerWins++;
      else if (challengerStats.recall < championStats.recall) championWins++;
    }
    if (challengerStats.precision !== null && championStats.precision !== null) {
      if (challengerStats.precision > championStats.precision) challengerWins++;
      else if (challengerStats.precision < championStats.precision) championWins++;
    }
    if (challengerWins === 0 && championWins === 0) return null;
    return challengerWins > championWins ? "challenger" : "champion";
  }, [hasResult, championStats, challengerStats]);

  const versionOptions = useMemo(
    () =>
      versions
        .map((version) => String(version.version || ""))
        .filter((value, index, array) => Boolean(value) && array.indexOf(value) === index),
    [versions]
  );

  const canRun =
    !loading &&
    Boolean(selectedModelId) &&
    Boolean(championVersion) &&
    Boolean(challengerVersion) &&
    championVersion !== challengerVersion;

  return (
    <section className="view-stack">
      <section className="surface" style={{ display: "grid", gap: 16 }}>
        <div className="section-heading split">
          <div className="section-title-row">
            <Swords size={16} />
            <h2>Champion vs Challenger</h2>
          </div>
          <Badge tone="accent">
            <Sparkles size={11} />
            comparação online
          </Badge>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)", maxWidth: 720 }}>
          Selecione duas versões do modelo para comparar lado a lado: volume de decisões, distribuição de score, matriz
          de confusão derivada do feedback e métricas de precisão. O backend agrega os dados online sob demanda.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) auto minmax(0, 1fr) auto",
            gap: 12,
            alignItems: "end"
          }}
        >
          <label>
            Champion (atual)
            <select
              value={championVersion}
              onChange={(event) => setChampionVersion(event.target.value)}
              disabled={!versions.length || loading}
            >
              <option value="">Selecionar</option>
              {versionOptions.map((value) => (
                <option key={`champ-${value}`} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <ArrowRight size={20} style={{ color: "var(--text-muted)", marginBottom: 10 }} />
          <label>
            Challenger
            <select
              value={challengerVersion}
              onChange={(event) => setChallengerVersion(event.target.value)}
              disabled={!versions.length || loading}
            >
              <option value="">Selecionar</option>
              {versionOptions.map((value) => (
                <option key={`chal-${value}`} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => onRunComparison(championVersion, challengerVersion)}
            disabled={!canRun}
          >
            <Swords size={15} />
            {loading ? "Comparando…" : "Comparar"}
          </button>
        </div>
        {result?.methodological_warning ? (
          <div
            style={{
              padding: "8px 12px",
              borderRadius: "var(--radius-sm)",
              background: "var(--warning-soft)",
              color: "var(--warning-strong)",
              border: "1px solid rgba(245, 158, 11, 0.36)",
              fontSize: "var(--fs-sm)"
            }}
          >
            {result.methodological_warning}
          </div>
        ) : null}
      </section>

      {!hasResult ? (
        <section className="surface">
          <EmptyState
            icon={<Swords size={18} />}
            title="Sem comparação ainda"
            text={
              versions.length < 2
                ? "É preciso ter pelo menos duas versões cadastradas para comparar."
                : "Escolha duas versões e clique em Comparar para ver o duelo."
            }
          />
        </section>
      ) : (
        <>
          <div className="compare-grid">
            <article className="compare-card champion">
              <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span
                    aria-hidden="true"
                    style={{
                      display: "inline-grid",
                      placeItems: "center",
                      width: 32,
                      height: 32,
                      borderRadius: "var(--radius-sm)",
                      background: "var(--success-soft)",
                      color: "var(--success-strong)"
                    }}
                  >
                    <Crown size={16} />
                  </span>
                  <div style={{ display: "grid", gap: 2 }}>
                    <strong style={{ color: "var(--text-strong)" }}>Champion</strong>
                    <span className="num" style={{ fontSize: "var(--fs-md)" }}>
                      {championMeta?.version}
                    </span>
                  </div>
                </div>
                {winnerHint === "champion" ? (
                  <Badge tone="success">
                    <Trophy size={11} />
                    vencendo
                  </Badge>
                ) : null}
              </header>
              <dl
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  gap: 12,
                  margin: 0
                }}
              >
                <StatCell label="Algoritmo" value={String(championMeta?.algorithm ?? "—")} />
                <StatCell label="Status" value={String(championMeta?.status ?? "—")} />
                <StatCell label="Predições" value={formatNumber(championStats.predictionCount)} />
                <StatCell label="Score médio" value={championStats.avgScore.toFixed(3)} />
                <StatCell label="Taxa positiva" value={formatPercent(championStats.positiveRate)} />
                <StatCell label="Com feedback" value={formatNumber(championStats.withFeedback)} />
                <StatCell label="Precision" value={formatPercent(championStats.precision ?? undefined)} />
                <StatCell label="Recall" value={formatPercent(championStats.recall ?? undefined)} />
                <StatCell
                  label="F1"
                  value={championStats.f1 !== null ? `${(championStats.f1 * 100).toFixed(1)}%` : "—"}
                />
              </dl>
              <ConfusionMini stats={championStats.confusion} formatNumber={formatNumber} />
            </article>

            <article className="compare-card challenger">
              <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
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
                    <Sparkles size={16} />
                  </span>
                  <div style={{ display: "grid", gap: 2 }}>
                    <strong style={{ color: "var(--text-strong)" }}>Challenger</strong>
                    <span className="num" style={{ fontSize: "var(--fs-md)" }}>
                      {challengerMeta?.version}
                    </span>
                  </div>
                </div>
                {winnerHint === "challenger" ? (
                  <Badge tone="accent">
                    <Trophy size={11} />
                    vencendo
                  </Badge>
                ) : null}
              </header>
              <dl
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  gap: 12,
                  margin: 0
                }}
              >
                <StatCell label="Algoritmo" value={String(challengerMeta?.algorithm ?? "—")} />
                <StatCell label="Status" value={String(challengerMeta?.status ?? "—")} />
                <StatCell
                  label="Predições"
                  value={formatNumber(challengerStats.predictionCount)}
                  delta={challengerStats.predictionCount - championStats.predictionCount}
                />
                <StatCell
                  label="Score médio"
                  value={challengerStats.avgScore.toFixed(3)}
                  delta={challengerStats.avgScore - championStats.avgScore}
                  format="absolute"
                />
                <StatCell
                  label="Taxa positiva"
                  value={formatPercent(challengerStats.positiveRate)}
                  delta={challengerStats.positiveRate - championStats.positiveRate}
                  invert
                />
                <StatCell label="Com feedback" value={formatNumber(challengerStats.withFeedback)} />
                <StatCell
                  label="Precision"
                  value={formatPercent(challengerStats.precision ?? undefined)}
                  delta={
                    challengerStats.precision !== null && championStats.precision !== null
                      ? challengerStats.precision - championStats.precision
                      : null
                  }
                />
                <StatCell
                  label="Recall"
                  value={formatPercent(challengerStats.recall ?? undefined)}
                  delta={
                    challengerStats.recall !== null && championStats.recall !== null
                      ? challengerStats.recall - championStats.recall
                      : null
                  }
                />
                <StatCell
                  label="F1"
                  value={challengerStats.f1 !== null ? `${(challengerStats.f1 * 100).toFixed(1)}%` : "—"}
                  delta={
                    challengerStats.f1 !== null && championStats.f1 !== null
                      ? challengerStats.f1 - championStats.f1
                      : null
                  }
                />
              </dl>
              <ConfusionMini stats={challengerStats.confusion} formatNumber={formatNumber} />
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
                <button
                  type="button"
                  className="success"
                  onClick={() => onPromote(String(challengerMeta?.version || ""))}
                  disabled={!challengerMeta?.version}
                  title="Marca o challenger como production e move o champion para deprecated."
                >
                  <Crown size={15} />
                  Promover challenger
                </button>
              </div>
            </article>
          </div>

          <section className="surface">
            <div className="section-heading">
              <Trophy size={16} />
              <h2>Métricas comparadas</h2>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={compareRows.map((row) => ({
                  metric: row.label,
                  Champion: row.chart.Champion,
                  Challenger: row.chart.Challenger
                }))}
              >
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 4" />
                <XAxis dataKey="metric" stroke="var(--text-muted)" fontSize={11} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface-elev)",
                    border: "1px solid var(--border-strong)",
                    borderRadius: 8
                  }}
                />
                <Bar dataKey="Champion" fill="var(--success)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Challenger" fill="var(--accent)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>
        </>
      )}
    </section>
  );
}

interface StatCellProps {
  label: string;
  value: string;
  delta?: number | null;
  invert?: boolean;
  format?: "percent" | "absolute";
}

function StatCell({ label, value, delta, invert, format = "percent" }: StatCellProps) {
  return (
    <div style={{ display: "grid", gap: 4 }}>
      <span className="stat-label">{label}</span>
      <strong className="num" style={{ fontSize: "var(--fs-md)", color: "var(--text-strong)" }}>
        {value}
      </strong>
      {delta !== undefined && delta !== null ? <Trend delta={delta} format={format} invert={invert} /> : null}
    </div>
  );
}

function ConfusionMini({
  stats,
  formatNumber
}: {
  stats: { tp: number; fp: number; tn: number; fn: number };
  formatNumber: (value: unknown) => string;
}) {
  const total = stats.tp + stats.fp + stats.tn + stats.fn;
  const cells: Array<{ key: keyof typeof stats; label: string; tone: string }> = [
    { key: "tp", label: "TP", tone: "var(--success-strong)" },
    { key: "fp", label: "FP", tone: "var(--warning-strong)" },
    { key: "tn", label: "TN", tone: "var(--info-strong)" },
    { key: "fn", label: "FN", tone: "var(--danger-strong)" }
  ];
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
        gap: 6,
        borderTop: "1px solid var(--border)",
        paddingTop: 12
      }}
    >
      {cells.map((cell) => {
        const value = stats[cell.key];
        const ratio = total > 0 ? value / total : 0;
        return (
          <div
            key={cell.key}
            style={{
              padding: "8px 10px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border)",
              background: "var(--surface-2)"
            }}
          >
            <span style={{ color: cell.tone, fontSize: "var(--fs-2xs)", fontWeight: 700, letterSpacing: "0.06em" }}>
              {cell.label}
            </span>
            <strong className="num" style={{ display: "block", fontSize: "var(--fs-md)", color: "var(--text-strong)" }}>
              {formatNumber(value)}
            </strong>
            <small style={{ color: "var(--text-muted)", fontSize: "var(--fs-2xs)" }}>
              {(ratio * 100).toFixed(1)}%
            </small>
          </div>
        );
      })}
    </div>
  );
}
