"use client";

import type { ReactNode } from "react";

interface KbdProps {
  children: ReactNode;
}

export function Kbd({ children }: KbdProps) {
  return <kbd className="kbd">{children}</kbd>;
}

interface ShortcutProps {
  keys: ReadonlyArray<string>;
  separator?: string;
}

export function Shortcut({ keys, separator = "+" }: ShortcutProps) {
  return (
    <span className="keys" aria-label={`Atalho: ${keys.join(" + ")}`}>
      {keys.map((key, index) => (
        <span key={`${key}-${index}`} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          {index > 0 ? <span style={{ color: "var(--text-subtle)" }}>{separator}</span> : null}
          <Kbd>{key}</Kbd>
        </span>
      ))}
    </span>
  );
}
