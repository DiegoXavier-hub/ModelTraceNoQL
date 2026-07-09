"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

interface TrendProps {
  delta?: number | null;
  format?: "absolute" | "percent";
  invert?: boolean;
  ariaLabel?: string;
}

export function Trend({ delta, format = "percent", invert = false, ariaLabel }: TrendProps) {
  if (delta === null || delta === undefined || Number.isNaN(delta)) {
    return null;
  }

  const direction = delta > 0 ? "up" : delta < 0 ? "down" : "flat";
  const positive = invert ? direction === "down" : direction === "up";
  const negative = invert ? direction === "up" : direction === "down";
  const tone = positive ? "up" : negative ? "down" : "flat";

  const formatted =
    format === "percent"
      ? `${delta > 0 ? "+" : ""}${(delta * 100).toFixed(1)}%`
      : `${delta > 0 ? "+" : ""}${delta.toLocaleString("pt-BR")}`;

  const Icon = direction === "up" ? ArrowUpRight : direction === "down" ? ArrowDownRight : Minus;

  return (
    <span className={`trend ${tone}`} aria-label={ariaLabel ?? `Variação ${formatted}`}>
      <Icon size={12} />
      {formatted}
    </span>
  );
}
