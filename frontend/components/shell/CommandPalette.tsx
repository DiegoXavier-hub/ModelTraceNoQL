"use client";

import { Search } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Kbd } from "../ui/Kbd";
import { EmptyState } from "../ui/EmptyState";

export interface CommandItem {
  id: string;
  label: string;
  detail: string;
  group?: string;
  run: () => void | Promise<void>;
}

interface CommandPaletteProps {
  open: boolean;
  items: ReadonlyArray<CommandItem>;
  query: string;
  onQueryChange: (value: string) => void;
  onClose: () => void;
}

function matches(item: CommandItem, query: string): boolean {
  if (!query) return true;
  const haystack = `${item.label} ${item.detail} ${item.group ?? ""}`.toLowerCase();
  return haystack.includes(query.toLowerCase());
}

export function CommandPalette({ open, items, query, onQueryChange, onClose }: CommandPaletteProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const filtered = useMemo(
    () => items.filter((item) => matches(item, query.trim())),
    [items, query]
  );

  useEffect(() => {
    setActiveIndex(0);
  }, [query, open]);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    inputRef.current?.select();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveIndex((index) => (filtered.length === 0 ? 0 : (index + 1) % filtered.length));
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveIndex((index) =>
          filtered.length === 0 ? 0 : (index - 1 + filtered.length) % filtered.length
        );
        return;
      }
      if (event.key === "Enter") {
        const candidate = filtered[activeIndex];
        if (candidate) {
          event.preventDefault();
          void Promise.resolve(candidate.run()).finally(() => onClose());
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, filtered, activeIndex, onClose]);

  if (!open) return null;

  return (
    <div
      className="command-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Comandos"
      ref={overlayRef}
      onClick={(event) => {
        if (event.target === overlayRef.current) onClose();
      }}
    >
      <section className="command-palette">
        <label className="search-field command-search">
          <span style={{ position: "absolute", left: 12, bottom: 11 }}>
            <Search size={16} />
          </span>
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Buscar tela, ação ou tópico…"
            aria-label="Buscar comando"
          />
        </label>
        <div className="command-list" role="listbox" aria-label="Resultados">
          {filtered.length === 0 ? (
            <EmptyState text="Nenhum comando encontrado." />
          ) : (
            filtered.map((item, index) => (
              <button
                type="button"
                key={item.id}
                className={index === activeIndex ? "is-active" : ""}
                onClick={() => {
                  void Promise.resolve(item.run()).finally(() => onClose());
                }}
                onMouseEnter={() => setActiveIndex(index)}
                role="option"
                aria-selected={index === activeIndex}
              >
                <strong>{item.label}</strong>
                <span>{item.detail}</span>
              </button>
            ))
          )}
        </div>
        <div className="command-footer">
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <Kbd>↑</Kbd>
            <Kbd>↓</Kbd>
            navegar
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <Kbd>↵</Kbd>
            executar
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <Kbd>Esc</Kbd>
            fechar
          </span>
        </div>
      </section>
    </div>
  );
}
