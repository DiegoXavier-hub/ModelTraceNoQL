"use client";

import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title?: string;
  text: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, text, action }: EmptyStateProps) {
  return (
    <div className="empty-state" role="status">
      {icon ? (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 36,
            height: 36,
            borderRadius: "var(--radius-pill)",
            background: "var(--accent-soft)",
            color: "var(--accent-strong)",
            marginBottom: 8
          }}
        >
          {icon}
        </div>
      ) : null}
      {title ? (
        <strong style={{ display: "block", color: "var(--text-strong)", marginBottom: 4 }}>{title}</strong>
      ) : null}
      <span style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)" }}>{text}</span>
      {action ? <div style={{ marginTop: 12 }}>{action}</div> : null}
    </div>
  );
}
