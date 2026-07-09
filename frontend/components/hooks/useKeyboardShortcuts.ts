"use client";

import { useEffect, useRef } from "react";
import { VIEW_SHORTCUTS } from "../nav";

interface ShortcutHandlers {
  onCommandPalette: () => void;
  onNotifications: () => void;
  onShortcutsHelp: () => void;
  onRefresh: () => void;
  onLogout: () => void;
  onNavigate: (viewId: string) => void;
  onToggleTheme?: () => void;
  enabled?: boolean;
}

const TYPING_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"]);

function isTyping(event: KeyboardEvent): boolean {
  const target = event.target as HTMLElement | null;
  if (!target) return false;
  if (TYPING_TAGS.has(target.tagName)) return true;
  if (target.isContentEditable) return true;
  return false;
}

/**
 * Atalhos de teclado estilo Gmail / GitHub:
 *   - Cmd+K / Ctrl+K  → command palette
 *   - Cmd+/ / Ctrl+/  → notificações
 *   - ?               → modal de atalhos
 *   - R               → refresh workspace
 *   - Shift+Q         → logout
 *   - G + (o,m,l,p,q,e,a,w,v,d) → navegação por aba
 *
 * Atalhos com modificador (Cmd/Ctrl/Shift) ignoram inputs/textareas naturalmente.
 * Atalhos de tecla única ("?", "R", G+X) também ignoram quando o foco está em campo de texto.
 */
export function useKeyboardShortcuts({
  onCommandPalette,
  onNotifications,
  onShortcutsHelp,
  onRefresh,
  onLogout,
  onNavigate,
  onToggleTheme,
  enabled = true
}: ShortcutHandlers): void {
  const prefixRef = useRef<string | null>(null);
  const prefixTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const clearPrefix = () => {
      prefixRef.current = null;
      if (prefixTimerRef.current) {
        clearTimeout(prefixTimerRef.current);
        prefixTimerRef.current = null;
      }
    };

    const handler = (event: KeyboardEvent) => {
      const meta = event.metaKey || event.ctrlKey;
      const shift = event.shiftKey;
      const alt = event.altKey;
      const lowKey = event.key.toLowerCase();

      // Cmd/Ctrl + K → command palette
      if (meta && lowKey === "k" && !shift && !alt) {
        event.preventDefault();
        clearPrefix();
        onCommandPalette();
        return;
      }

      // Cmd/Ctrl + / → notifications drawer
      if (meta && event.key === "/" && !shift && !alt) {
        event.preventDefault();
        clearPrefix();
        onNotifications();
        return;
      }

      // Atalhos sem modificador → só funcionam fora de inputs
      if (meta || alt) {
        return;
      }
      if (isTyping(event)) {
        return;
      }

      // Shift + Q → logout
      if (shift && lowKey === "q") {
        event.preventDefault();
        clearPrefix();
        onLogout();
        return;
      }

      if (shift) {
        return;
      }

      // ? → ajuda
      if (event.key === "?") {
        event.preventDefault();
        clearPrefix();
        onShortcutsHelp();
        return;
      }

      // R → refresh
      if (lowKey === "r") {
        event.preventDefault();
        clearPrefix();
        onRefresh();
        return;
      }

      // T → toggle theme
      if (lowKey === "t" && onToggleTheme && prefixRef.current !== "g") {
        event.preventDefault();
        clearPrefix();
        onToggleTheme();
        return;
      }

      // Esperando segunda tecla do prefixo G+X
      if (prefixRef.current === "g") {
        const binding = VIEW_SHORTCUTS.find((item) => item.prefix === "g" && item.key === lowKey);
        if (binding) {
          event.preventDefault();
          clearPrefix();
          onNavigate(binding.viewId);
          return;
        }
        clearPrefix();
        return;
      }

      // Prefixo G
      if (lowKey === "g") {
        prefixRef.current = "g";
        if (prefixTimerRef.current) clearTimeout(prefixTimerRef.current);
        prefixTimerRef.current = setTimeout(clearPrefix, 1200);
        return;
      }
    };

    window.addEventListener("keydown", handler);
    return () => {
      window.removeEventListener("keydown", handler);
      if (prefixTimerRef.current) clearTimeout(prefixTimerRef.current);
    };
  }, [
    enabled,
    onCommandPalette,
    onNotifications,
    onShortcutsHelp,
    onRefresh,
    onLogout,
    onNavigate,
    onToggleTheme
  ]);
}
