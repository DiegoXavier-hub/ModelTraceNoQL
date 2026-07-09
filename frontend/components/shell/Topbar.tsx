"use client";

import { Bell, Command, LogOut, Moon, RefreshCcw, Sun } from "lucide-react";
import type { Locale } from "@/lib/i18n";
import { LanguageToggle } from "./LanguageToggle";

import type { Theme } from "../hooks/useTheme";

interface TopbarProps {
  domain?: string;
  title: string;
  description: string;
  notificationsUnread: number;
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  onCommandPalette: () => void;
  onNotifications: () => void;
  onRefresh: () => void;
  onLogout: () => void;
  theme: Theme;
  onToggleTheme: () => void;
}

export function Topbar({
  domain,
  title,
  description,
  notificationsUnread,
  locale,
  onLocaleChange,
  onCommandPalette,
  onNotifications,
  onRefresh,
  onLogout,
  theme,
  onToggleTheme
}: TopbarProps) {
  const isDark = theme === "dark";
  const labelTheme = isDark ? "Mudar para tema claro" : "Mudar para tema escuro";
  const labelCommands = "Comandos (Ctrl+K)";
  const labelNotifications = notificationsUnread
    ? `Notificações: ${notificationsUnread} não lidas`
    : "Notificações (Ctrl+/)";
  const labelRefresh = "Atualizar workspace (R)";
  const labelLogout = "Sair (Shift+Q)";

  return (
    <header className="app-topbar">
      <div>
        <span className="eyebrow">{(domain || "workspace")} · production</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="topbar-actions">
        <LanguageToggle locale={locale} onChange={onLocaleChange} />
        <button
          type="button"
          className="ghost icon-only"
          onClick={onToggleTheme}
          aria-label={labelTheme}
          title={labelTheme}
          aria-pressed={!isDark}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        <button
          type="button"
          className="secondary icon-only"
          onClick={onCommandPalette}
          aria-label={labelCommands}
          title={labelCommands}
        >
          <Command size={16} />
        </button>
        <button
          type="button"
          className="secondary icon-only"
          onClick={onNotifications}
          aria-label={labelNotifications}
          title={labelNotifications}
          style={{ position: "relative" }}
        >
          <Bell size={16} />
          {notificationsUnread > 0 ? (
            <span
              aria-hidden="true"
              style={{
                position: "absolute",
                top: -4,
                right: -4,
                minWidth: 16,
                height: 16,
                padding: "0 4px",
                borderRadius: "var(--radius-pill)",
                background: "var(--danger)",
                color: "#fff",
                fontFamily: "var(--font-mono)",
                fontSize: "var(--fs-2xs)",
                fontWeight: 700,
                lineHeight: "16px",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 0 2px var(--surface)"
              }}
            >
              {notificationsUnread > 99 ? "99+" : notificationsUnread}
            </span>
          ) : null}
        </button>
        <button
          type="button"
          className="secondary icon-only"
          onClick={onRefresh}
          aria-label={labelRefresh}
          title={labelRefresh}
        >
          <RefreshCcw size={16} />
        </button>
        <button
          type="button"
          className="secondary icon-only"
          onClick={onLogout}
          aria-label={labelLogout}
          title={labelLogout}
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}
