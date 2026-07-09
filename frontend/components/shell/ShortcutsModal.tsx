"use client";

import { Keyboard, X } from "lucide-react";
import { useEffect } from "react";
import { Shortcut } from "../ui/Kbd";
import { GLOBAL_SHORTCUTS, VIEW_SHORTCUTS } from "../nav";

interface ShortcutsModalProps {
  open: boolean;
  onClose: () => void;
}

export function ShortcutsModal({ open, onClose }: ShortcutsModalProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const navigationShortcuts = VIEW_SHORTCUTS.map((binding) => ({
    keys: binding.prefix
      ? [binding.prefix.toUpperCase(), binding.key.toUpperCase()]
      : [binding.key.toUpperCase()],
    label: binding.label
  }));

  const panelsAndActions = (group: "panels" | "actions") =>
    GLOBAL_SHORTCUTS.filter((entry) => entry.group === group).map((entry) => ({
      keys: entry.keys,
      label: entry.label,
      description: entry.description
    }));

  return (
    <div
      className="shortcuts-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Atalhos de teclado"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section className="shortcuts-modal">
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              style={{
                display: "inline-flex",
                width: 32,
                height: 32,
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "var(--radius-sm)",
                background: "var(--accent-soft)",
                color: "var(--accent-strong)"
              }}
              aria-hidden="true"
            >
              <Keyboard size={16} />
            </span>
            <h2>Atalhos de teclado</h2>
          </div>
          <button
            type="button"
            className="ghost icon-only sm"
            onClick={onClose}
            aria-label="Fechar"
          >
            <X size={16} />
          </button>
        </header>

        <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)" }}>
          Atalhos funcionam em qualquer tela, exceto quando você está digitando em um campo.
          Pressione <kbd className="kbd">?</kbd> a qualquer momento para reabrir esta lista.
        </p>

        <div className="shortcuts-grid">
          <div className="shortcuts-group">
            <h3>Painéis</h3>
            {panelsAndActions("panels").map((entry) => (
              <div className="shortcuts-row" key={entry.label}>
                <span>{entry.label}</span>
                <Shortcut keys={entry.keys} />
              </div>
            ))}
          </div>

          <div className="shortcuts-group">
            <h3>Ações rápidas</h3>
            {panelsAndActions("actions").map((entry) => (
              <div className="shortcuts-row" key={entry.label}>
                <span>{entry.label}</span>
                <Shortcut keys={entry.keys} />
              </div>
            ))}
          </div>

          <div className="shortcuts-group" style={{ gridColumn: "1 / -1" }}>
            <h3>Navegação (G + tecla)</h3>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                gap: "0 16px"
              }}
            >
              {navigationShortcuts.map((entry) => (
                <div className="shortcuts-row" key={entry.label}>
                  <span>{entry.label}</span>
                  <Shortcut keys={entry.keys} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
