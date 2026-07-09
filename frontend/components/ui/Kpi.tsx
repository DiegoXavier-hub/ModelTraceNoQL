"use client";

import type { ReactNode } from "react";
import { Sparkline } from "./Sparkline";
import { Trend } from "./Trend";

export type KpiTone = "default" | "good" | "warn" | "bad";

interface KpiProps {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  tone?: KpiTone;
  trend?: number | null;
  trendInvert?: boolean;
  trendFormat?: "absolute" | "percent";
  spark?: ReadonlyArray<number>;
  onClick?: () => void;
  ariaLabel?: string;
}

export function Kpi({
  label,
  value,
  icon,
  tone = "default",
  trend,
  trendInvert = false,
  trendFormat = "percent",
  spark,
  onClick,
  ariaLabel
}: KpiProps) {
  const className = ["metric", tone === "default" ? "" : tone, onClick ? "clickable" : ""]
    .filter(Boolean)
    .join(" ");

  const sparkColor =
    tone === "good"
      ? "var(--success-strong)"
      : tone === "warn"
        ? "var(--warning-strong)"
        : tone === "bad"
          ? "var(--danger-strong)"
          : "var(--accent-strong)";

  const content = (
    <>
      {icon ? <span aria-hidden="true">{icon}</span> : null}
      <small>{label}</small>
      <strong>{value}</strong>
      {(trend !== undefined && trend !== null) || (spark && spark.length > 1) ? (
        <div
          style={{
            gridColumn: icon ? "2" : "1 / -1",
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: sparkColor
          }}
        >
          {trend !== undefined && trend !== null ? (
            <Trend delta={trend} format={trendFormat} invert={trendInvert} />
          ) : null}
          {spark && spark.length > 1 ? (
            <Sparkline values={spark} ariaLabel={`Tendência de ${label}`} />
          ) : null}
        </div>
      ) : null}
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        className={className}
        onClick={onClick}
        aria-label={ariaLabel ?? `${label}: ${value}`}
      >
        {content}
      </button>
    );
  }

  return (
    <div className={className} role="group" aria-label={ariaLabel ?? `${label}: ${value}`}>
      {content}
    </div>
  );
}
