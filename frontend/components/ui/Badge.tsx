"use client";

import type { ReactNode } from "react";

export type BadgeTone = "neutral" | "accent" | "success" | "warn" | "danger" | "info";

interface BadgeProps {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
}

const TONE_CLASS: Record<BadgeTone, string> = {
  neutral: "",
  accent: "accent",
  success: "success",
  warn: "warn",
  danger: "danger",
  info: "info"
};

export function Badge({ tone = "neutral", children, className }: BadgeProps) {
  const classes = ["badge", TONE_CLASS[tone], className].filter(Boolean).join(" ");
  return <span className={classes}>{children}</span>;
}
