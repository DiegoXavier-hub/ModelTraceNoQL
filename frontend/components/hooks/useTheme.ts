"use client";

import { useCallback, useEffect, useState } from "react";

export type Theme = "dark" | "light";

const STORAGE_KEY = "modeltrace_theme";

function readInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // ignore quota / privacy mode errors
  }
  if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
    return "light";
  }
  return "dark";
}

/**
 * Hook que gerencia o tema do app (dark/light) sincronizando com:
 *   - data-theme no <html>
 *   - localStorage para persistência entre sessões
 *   - meta theme-color para a barra de status do navegador
 *
 * Inclui pequena pausa de animação ao trocar para evitar transições
 * piscando de 200ms em todos os elementos quando o usuário clica no toggle.
 */
export function useTheme(): { theme: Theme; toggle: () => void; setTheme: (next: Theme) => void } {
  const [theme, setThemeState] = useState<Theme>(readInitialTheme);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    const previous = root.dataset.theme;
    if (previous === theme) return;

    root.classList.add("theme-transition-disable");
    root.dataset.theme = theme;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", theme === "light" ? "#f6f7fb" : "#0a0c10");
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // ignore
    }
    const timer = window.setTimeout(() => {
      root.classList.remove("theme-transition-disable");
    }, 60);
    return () => window.clearTimeout(timer);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
  }, []);

  const toggle = useCallback(() => {
    setThemeState((current) => (current === "dark" ? "light" : "dark"));
  }, []);

  return { theme, toggle, setTheme };
}
