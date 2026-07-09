/**
 * Mapeamento de atalhos de teclado para as visualizações do app.
 * O array de NAV_ITEMS continua em app/page.tsx (fonte única de verdade).
 * Aqui ficam apenas os bindings de teclado padrão estilo Gmail/GitHub: prefixo "G" + tecla.
 */
export interface ShortcutBinding {
  viewId: string;
  prefix?: string;
  key: string;
  label: string;
}

export const VIEW_SHORTCUTS: ReadonlyArray<ShortcutBinding> = [
  { viewId: "overview", prefix: "g", key: "o", label: "Overview" },
  { viewId: "monitor", prefix: "g", key: "m", label: "Monitor" },
  { viewId: "lab", prefix: "g", key: "l", label: "DS Lab" },
  { viewId: "predictions", prefix: "g", key: "p", label: "Predições" },
  { viewId: "operations", prefix: "g", key: "q", label: "Operação" },
  { viewId: "entities", prefix: "g", key: "e", label: "Entidades" },
  { viewId: "control", prefix: "g", key: "a", label: "Automação" },
  { viewId: "workbench", prefix: "g", key: "w", label: "Workbench" },
  { viewId: "governance", prefix: "g", key: "v", label: "Governança" },
  { viewId: "compare", prefix: "g", key: "c", label: "Compare" },
  { viewId: "drift", prefix: "g", key: "x", label: "Drift" },
  { viewId: "cases", prefix: "g", key: "s", label: "Casos (SLA)" },
  { viewId: "usage", prefix: "g", key: "u", label: "Custo & Consumo" },
  { viewId: "docs", prefix: "g", key: "d", label: "Docs" }
];

export interface GlobalShortcut {
  id: string;
  keys: ReadonlyArray<string>;
  label: string;
  description: string;
  group: "navigation" | "actions" | "panels";
}

export const GLOBAL_SHORTCUTS: ReadonlyArray<GlobalShortcut> = [
  {
    id: "command",
    keys: ["⌘", "K"],
    label: "Abrir Comandos",
    description: "Busca telas, ações e tópicos da documentação.",
    group: "panels"
  },
  {
    id: "notifications",
    keys: ["⌘", "/"],
    label: "Notificações",
    description: "Abre o painel lateral de notificações.",
    group: "panels"
  },
  {
    id: "shortcuts",
    keys: ["?"],
    label: "Atalhos de teclado",
    description: "Mostra todos os atalhos disponíveis.",
    group: "panels"
  },
  {
    id: "refresh",
    keys: ["R"],
    label: "Atualizar workspace",
    description: "Recarrega projetos, modelos e métricas.",
    group: "actions"
  },
  {
    id: "logout",
    keys: ["⇧", "Q"],
    label: "Sair",
    description: "Encerra a sessão atual.",
    group: "actions"
  },
  {
    id: "theme",
    keys: ["T"],
    label: "Alternar tema",
    description: "Troca entre tema escuro e claro.",
    group: "actions"
  }
];

export function shortcutsForView(viewId: string): ReadonlyArray<string> | undefined {
  const binding = VIEW_SHORTCUTS.find((item) => item.viewId === viewId);
  if (!binding) return undefined;
  return binding.prefix ? [binding.prefix.toUpperCase(), binding.key.toUpperCase()] : [binding.key.toUpperCase()];
}
