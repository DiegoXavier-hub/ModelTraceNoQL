"use client";

import { CheckCheck, Inbox, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "../ui/EmptyState";

interface NotificationDoc {
  _id?: string;
  id?: string;
  title?: string;
  message?: string;
  body?: string;
  status?: string;
  level?: string;
  category?: string;
  topic?: string;
  read?: boolean;
  read_at?: string;
  created_at?: string;
  link?: string;
  resource_id?: string;
  resource_type?: string;
  [key: string]: unknown;
}

interface NotificationsDrawerProps {
  open: boolean;
  notifications: ReadonlyArray<NotificationDoc>;
  unreadCount: number;
  onClose: () => void;
  onMarkAllRead: () => void;
  onSelect: (notification: NotificationDoc) => void;
}

type Filter = "all" | "unread" | "alerts" | "jobs" | "system";

interface TabConfig {
  id: Filter;
  label: string;
  match: (n: NotificationDoc) => boolean;
}

function isRead(notification: NotificationDoc): boolean {
  return Boolean(notification.read_at) || notification.read === true;
}

const TABS: ReadonlyArray<TabConfig> = [
  { id: "all", label: "Todas", match: () => true },
  { id: "unread", label: "Não lidas", match: (n) => !isRead(n) },
  {
    id: "alerts",
    label: "Alertas",
    match: (n) =>
      `${n.category ?? ""} ${n.topic ?? ""} ${n.resource_type ?? ""}`
        .toLowerCase()
        .includes("alert")
  },
  {
    id: "jobs",
    label: "Jobs",
    match: (n) =>
      `${n.category ?? ""} ${n.topic ?? ""} ${n.resource_type ?? ""}`
        .toLowerCase()
        .includes("job")
  },
  { id: "system", label: "Sistema", match: (n) => (n.category ?? "").toLowerCase() === "system" }
];

function notificationTone(notification: NotificationDoc): string {
  const level = String(notification.level ?? notification.status ?? "info").toLowerCase();
  if (level === "error" || level === "critical" || level === "high") return "error";
  if (level === "warn" || level === "warning" || level === "medium") return "warning";
  if (level === "success" || level === "ok" || level === "completed") return "success";
  return "info";
}

function formatTime(value?: string): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const now = Date.now();
  const diff = (now - date.getTime()) / 1000;
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)} min`;
  if (diff < 86_400) return `${Math.floor(diff / 3600)} h`;
  if (diff < 7 * 86_400) return `${Math.floor(diff / 86_400)} d`;
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

export function NotificationsDrawer({
  open,
  notifications,
  unreadCount,
  onClose,
  onMarkAllRead,
  onSelect
}: NotificationsDrawerProps) {
  const [filter, setFilter] = useState<Filter>("all");

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

  const filtered = useMemo(() => {
    const tab = TABS.find((entry) => entry.id === filter) ?? TABS[0];
    return notifications.filter((item) => tab.match(item));
  }, [notifications, filter]);

  const counts = useMemo(() => {
    return TABS.reduce<Record<Filter, number>>(
      (acc, tab) => {
        acc[tab.id] = notifications.filter(tab.match).length;
        return acc;
      },
      { all: 0, unread: 0, alerts: 0, jobs: 0, system: 0 }
    );
  }, [notifications]);

  if (!open) return null;

  return (
    <>
      <div className="notif-overlay" onClick={onClose} aria-hidden="true" />
      <aside
        className="notif-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Centro de notificações"
      >
        <header className="notif-header">
          <div style={{ display: "grid", gap: 2 }}>
            <h2>Notificações</h2>
            <span style={{ color: "var(--text-muted)", fontSize: "var(--fs-sm)" }}>
              {unreadCount > 0 ? `${unreadCount} não lidas` : "Tudo em dia"}
            </span>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="secondary sm"
              onClick={onMarkAllRead}
              disabled={unreadCount === 0}
              aria-label="Marcar todas como lidas"
            >
              <CheckCheck size={14} />
              Marcar lidas
            </button>
            <button
              type="button"
              className="ghost icon-only sm"
              onClick={onClose}
              aria-label="Fechar painel"
            >
              <X size={16} />
            </button>
          </div>
        </header>

        <nav className="notif-tabs" aria-label="Filtros de notificação">
          {TABS.map((tab) => {
            const count = counts[tab.id];
            return (
              <button
                key={tab.id}
                type="button"
                className={`notif-tab ${filter === tab.id ? "active" : ""}`}
                onClick={() => setFilter(tab.id)}
                aria-pressed={filter === tab.id}
              >
                {tab.label}
                {count > 0 ? <span className="count">{count}</span> : null}
              </button>
            );
          })}
        </nav>

        <div className="notif-body">
          {filtered.length === 0 ? (
            <EmptyState
              icon={<Inbox size={18} />}
              title="Sem novidades"
              text={
                filter === "unread"
                  ? "Você está com tudo lido neste filtro."
                  : "Nenhuma notificação para esse filtro ainda."
              }
            />
          ) : (
            filtered.map((notification) => {
              const tone = notificationTone(notification);
              const id = String(notification._id ?? notification.id ?? Math.random());
              const title = notification.title ?? "Notificação";
              const message =
                notification.message ?? notification.body ?? notification.topic ?? "";
              return (
                <button
                  key={id}
                  type="button"
                  className={`notif-item ${tone} ${isRead(notification) ? "" : "unread"}`}
                  onClick={() => onSelect(notification)}
                >
                  <span className="dot" aria-hidden="true" />
                  <div className="body">
                    <strong>{title}</strong>
                    {message ? <p>{String(message)}</p> : null}
                  </div>
                  <time>{formatTime(notification.created_at)}</time>
                </button>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
}
