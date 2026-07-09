"use client";

import { Database } from "lucide-react";
import type { ComponentType, SVGProps } from "react";
import { localizedField, type Locale } from "@/lib/i18n";
import { Kbd } from "../ui/Kbd";
import { shortcutsForView } from "../nav";

interface NavItem {
  id: string;
  label: string;
  icon: ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>;
}

type AnyDoc = Record<string, any>;

interface SidebarProps {
  navItems: ReadonlyArray<NavItem>;
  activeView: string;
  onSelect: (id: string) => void;
  projects: ReadonlyArray<AnyDoc>;
  models: ReadonlyArray<AnyDoc>;
  selectedProjectId: string;
  selectedModelId: string;
  onProjectChange: (id: string) => void;
  onModelChange: (id: string) => void;
  apiUrl: string;
  locale: Locale;
}

export function Sidebar({
  navItems,
  activeView,
  onSelect,
  projects,
  models,
  selectedProjectId,
  selectedModelId,
  onProjectChange,
  onModelChange,
  apiUrl,
  locale
}: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Navegação principal">
      <div className="brand-block">
        <div className="brand-icon" aria-hidden="true">
          <Database size={20} />
        </div>
        <div>
          <strong>ModelTrace</strong>
          <span>Decision Operations</span>
        </div>
      </div>

      <nav className="side-nav" aria-label="Telas">
        {navItems.map((item) => {
          const Icon = item.icon;
          const shortcut = shortcutsForView(item.id);
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={isActive ? "active" : ""}
              onClick={() => onSelect(item.id)}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon size={16} />
              <span style={{ flex: 1, textAlign: "left" }}>{item.label}</span>
              {shortcut ? (
                <span
                  style={{ display: "inline-flex", gap: 2, opacity: 0.66 }}
                  aria-hidden="true"
                >
                  {shortcut.map((key) => (
                    <Kbd key={key}>{key}</Kbd>
                  ))}
                </span>
              ) : null}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-controls">
        <label>
          Projeto
          <select value={selectedProjectId} onChange={(event) => onProjectChange(event.target.value)}>
            <option value="">Selecionar</option>
            {projects.map((project) => (
              <option key={project._id} value={project._id}>
                {localizedField(project, "name", locale)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Modelo
          <select value={selectedModelId} onChange={(event) => onModelChange(event.target.value)}>
            <option value="">Selecionar</option>
            {models.map((model) => (
              <option key={model._id} value={model._id}>
                {localizedField(model, "name", locale)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div />

      <div className="sidebar-foot" role="status" aria-label="Status da API">
        <span className="pulse-dot" aria-hidden="true" />
        <div>
          <strong>API online</strong>
          <span>{apiUrl}</span>
        </div>
      </div>
    </aside>
  );
}
