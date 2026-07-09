# ModelTrace — Design System v2

Este documento descreve o design system implementado no frontend do ModelTrace a partir da versao 2 do produto. A intencao e dar a um novo membro do time o suficiente para construir telas novas com a mesma linguagem visual.

## 1. Filosofia

Estilo de referencia: **Stripe / Datadog**.

Um console de operacao de modelos tem operadores que passam horas olhando numeros, graficos e tabelas. O design otimiza para:

- densidade informacional alta sem virar bagunca visual;
- hierarquia tipografica forte (numeros grandes monoespacados, labels pequenas em uppercase);
- cor com significado (sucesso, atencao, perigo) e nao como decoracao;
- gradientes funcionais somente onde reforcam estado (ex: KPI com tendencia negativa);
- glow controlado, nunca decorativo, e sempre amarrado a foco/acao.

## 2. Tipografia

Configurada em `frontend/app/layout.tsx` via `next/font/google`:

```ts
import { Inter, IBM_Plex_Mono } from "next/font/google";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", weight: [...] });
const ibmPlexMono = IBM_Plex_Mono({ subsets: ["latin"], variable: "--font-mono", weight: [...] });
```

- `Inter` para texto de UI, headings, labels e botoes.
- `IBM Plex Mono` para numeros grandes (KPIs), codigo, tokens, status e timestamps.

Boas praticas:

- toda metrica e KPI usa `font-family: var(--font-mono)` com `font-feature-settings: "tnum"` para alinhar colunas;
- titulos usam `letter-spacing: -0.011em` ou `-0.02em` (tighter em fontes grandes);
- labels semanticas (`SUCCESS`, `RISK`, `LATENCY`) usam `font-size: var(--fs-xs)` + `text-transform: uppercase` + `letter-spacing: 0.04em..0.06em`;
- ligaduras estilisticas Inter ativadas via `font-feature-settings: "cv11" 1, "ss03" 1, "cv02" 1`.

Escala (em `globals.css`):

```text
--fs-2xs: 10px
--fs-xs:  11px
--fs-sm:  12px
--fs-base:13px   (default body)
--fs-md:  14px
--fs-lg:  16px
--fs-xl:  20px
--fs-2xl: 24px
--fs-3xl: 32px
--fs-4xl: 40px
```

## 3. Paleta De Cores

Definida em camada `@layer tokens` no seletor `:root, [data-theme="dark"]`.

### 3.1 Surfaces (escala de profundidade)

| Token | Valor | Uso |
| --- | --- | --- |
| `--bg` | `#07090d` | fundo da pagina |
| `--bg-grid` | `#0a0d12` | gradiente sutil sobre o fundo |
| `--surface` | `#0e1218` | cartoes primarios |
| `--surface-2` | `#131922` | cartoes em segundo nivel, hover |
| `--surface-3` | `#181f2a` | inputs em foco, terciario |
| `--surface-elev` | `#1d2532` | toast, drawer, paleta de comandos |
| `--surface-glass` | `rgba(20,26,36,.72)` | overlay translucido |

### 3.2 Borders

| Token | Uso |
| --- | --- |
| `--border` | borda padrao em superficies |
| `--border-strong` | divisores e cabecalhos de tabela |
| `--border-accent` | borda accent (foco, KPIs ativos) |

### 3.3 Texto

| Token | Uso |
| --- | --- |
| `--text` | texto padrao |
| `--text-strong` | titulos, valores |
| `--text-muted` | labels, captions |
| `--text-subtle` | hints, placeholders |
| `--text-inverse` | texto sobre cor solida |

### 3.4 Marca + status

| Token | Hex | Significado |
| --- | --- | --- |
| `--accent` | `#7c5cff` | brand indigo (botoes primarios, focos) |
| `--accent-strong` | `#9b82ff` | hover do accent |
| `--success` | `#10b981` | tudo OK |
| `--warning` | `#f59e0b` | atencao |
| `--danger` | `#ef4444` | erro, risco |
| `--info` | `#38bdf8` | neutro informativo |

Para cada cor de status existe `<color>-soft` (translucido para fundo de badges) e `<color>-strong` (variacao mais clara para texto sobre soft).

### 3.5 Gradientes funcionais

```css
--grad-accent:  linear-gradient(135deg, rgba(124,92,255,.20), rgba(124,92,255,.02) 65%);
--grad-success: linear-gradient(135deg, rgba(16,185,129,.18), rgba(16,185,129,.02) 65%);
--grad-warning: linear-gradient(135deg, rgba(245,158,11,.18), rgba(245,158,11,.02) 65%);
--grad-danger:  linear-gradient(135deg, rgba(239,68,68,.18), rgba(239,68,68,.02) 65%);
--grad-aurora:  radial-gradient(...) /* hero auth */
```

Use em painel critico (KPI ruim, hero de auth, banner de incident). Nunca em area de conteudo continuo.

## 4. Espacamento

Grid de 4 pontos:

```text
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

Convencao:

- `padding` interno de surface = `--space-4` (16px) por padrao, `--space-5` em superficies hero/health-panel;
- `gap` entre cartoes em grids = `--space-3` (12px) ou `--space-4` (16px);
- `gap` interno em listas densas (jobs, alertas) = `--space-2` (8px).

## 5. Sombras E Foco

```text
--shadow-xs   0 1px 2px rgba(0,0,0,0.18)
--shadow-sm   0 2px 6px ...
--shadow-md   ... cartoes ativos
--shadow-lg   ... toast, drawer
--shadow-xl   ... modais
--shadow-glow 0 0 0 1px var(--accent-soft), 0 12px 40px var(--accent-glow)
--shadow-focus 0 0 0 3px color-mix(in srgb, var(--accent) 26%, transparent)
```

Acessibilidade: todo elemento focavel (`button`, `input`, `select`) usa `--shadow-focus` em `:focus-visible`. Nunca remover outline sem fornecer alternativa.

## 6. Layers De CSS

`globals.css` usa `@layer reset, tokens, base, components, utilities;`. Essa ordem garante que:

- estilos componentes (`.health-panel`, `.metric`) sobrescrevem `base` e `tokens`;
- `utilities` (helpers como `.row`, `.stack`, `.text-muted`) sobrescrevem componentes quando necessarios;
- estilos legados (sem layer) participam normalmente da cascata.

Quando criar uma classe nova, escolher a camada correta:

- token de tema (cor, espacamento) → `tokens`;
- estilo base de tag HTML → `base`;
- componente reusavel (KPI, badge) → `components`;
- helper utilitario sem semantica → `utilities`.

## 7. Componentes UI Disponiveis

Em `frontend/components/ui/`:

| Componente | Proposito |
| --- | --- |
| `Badge` | pill com tom (`accent`, `success`, `warn`, `danger`, `info`) |
| `EmptyState` | placeholder com icone + texto + acao opcional |
| `Kbd` / `Shortcut` | tecla individual e combinacao com separador |
| `Kpi` | KPI card com label, valor, icone, sparkline opcional, trend opcional, click handler |
| `Skeleton` | loader animado (`text` / `box` / `circle`) |
| `Sparkline` | mini-chart SVG inline (sem dependencia externa) |
| `Toast` | notificacao com tom (success/error/info) |
| `Trend` | seta + percentual (com inversao semantica via `invert`) |

Importacao:

```ts
import { Kpi, Trend, Sparkline, Badge } from "@/components/ui";
```

## 8. Componentes De Shell

Em `frontend/components/shell/`:

| Componente | Proposito |
| --- | --- |
| `Sidebar` | navegacao primaria com atalhos visiveis ao lado de cada item |
| `Topbar` | titulo da view + acoes globais (idioma, comandos, notificacoes, refresh, logout) |
| `LanguageToggle` | toggle PT/EN com `aria-pressed` |
| `CommandPalette` | overlay com busca, navegacao por seta, footer de atalhos |
| `NotificationsDrawer` | painel lateral 440px com tabs e mark-all-read |
| `ShortcutsModal` | modal com lista de atalhos agrupados (Paineis / Acoes / Navegacao) |

## 9. Hooks

- `useKeyboardShortcuts` (em `components/hooks/`): registra atalhos globais com prefixo `G + tecla`, ignora foco em campos de texto, suporta modificadores `Cmd`, `Ctrl`, `Shift`.

## 10. Padroes De Estado Visual

| Estado | Mecanismo |
| --- | --- |
| Loading | `Skeleton` (`shimmer` 1.4s) ou `lab-status.loading` em pill |
| Empty | `EmptyState` com `icon`, `title`, `text`, `action` |
| Error | `Toast` tone `error` ou `.form-errors` block |
| Success | `Toast` tone `success` ou pill `.success` |
| Live | `pulse-dot` animado em sidebar/footer |
| Disabled | `opacity: 0.45` + `cursor: not-allowed` + `filter: grayscale(0.2)` |

## 11. Responsividade

Breakpoints definidos em `globals.css`:

- `1180px` → sidebar reduzida para 220px, grids de duas colunas viram uma;
- `860px` → app shell single-column, sidebar acima do conteudo, auth shell empilhado;
- `520px` → workspace compacto, action strips em coluna, paleta full-width.

Boas praticas:

- nunca usar `width` fixo em pixels para conteudo (so para KPIs/avatar);
- `min-width: 0` em filhos de grid para permitir text overflow correto;
- `overflow-wrap: anywhere` em codigo, IDs, emails truncaveis.

## 12. Light Theme

Implementado integralmente na v2.1.

Hook: `components/hooks/useTheme.ts`

- expoe `{ theme, toggle, setTheme }`;
- estado interno tipado `Theme = "dark" | "light"`;
- ao trocar, aplica `document.documentElement.dataset.theme = next`, salva em `localStorage` (`modeltrace_theme`) e atualiza `<meta name="theme-color">`;
- aplica classe transitoria `theme-transition-disable` por 60ms para evitar flicker generalizado de transicoes ao alternar.

Anti-FOUC: `app/layout.tsx` injeta um `<Script id="modeltrace-theme-boot" strategy="beforeInteractive">` que le `localStorage` antes do paint inicial e seta `data-theme` no `<html>`. Quando nao ha preferencia salva, respeita `prefers-color-scheme: light`.

Toggle UI:

- botao Sol/Lua (`Sun` / `Moon` da `lucide-react`) no `Topbar`, com `aria-pressed` refletindo estado;
- atalho `T` global (registrado em `useKeyboardShortcuts`).

Tokens light theme:

- bloco `[data-theme="light"]` no inicio do `globals.css` redefine superficies (`#f6f7fb`, `#ffffff`, `#f3f5f9`, `#eaeef5`), bordas (`#e2e6ee`, `#c8d0dc`) e texto (`#0f1521`, `#5a6478`, `#828ea1`).
- camada `6.5 THEME TRANSITION + LIGHT REFINEMENTS` no fim do arquivo adiciona overrides para: `body`, `pre`, `auth-product`, `toast`, `command-palette`, `notif-drawer`, `key-box`, `health-ring`, `recharts-default-tooltip`, `kbd` e `tbody tr.selected`.

Antipadroes evitados:

- nenhum hex literal hardcoded em componente — tudo via `var(--...)` ou `color-mix(in srgb, ...)`;
- transicoes globais sao desligadas durante toggle, evitando o "wave" de fade-in piscando;
- focus rings usam `--shadow-focus` (que depende do `--accent`) em vez de cor fixa, mantendo contraste no light theme.

## 12.1 Padroes Visuais Especificos Do ModelTrace

A v2 introduziu tres padroes visuais novos com classes CSS dedicadas em `globals.css`. Use-os como referencia quando criar variantes.

### `.compare-card` (Champion vs Challenger)

- base: `border-radius: var(--radius-md)`, padding `--space-5`, gradient lateral em `::after`;
- `.champion` ganha borda verde + gradient `success-soft → surface`;
- `.challenger` ganha borda accent + gradient `accent-soft → surface`;
- hover: `translateY(-2px)` + `shadow-md` para dar afeto;
- uso correto: cartao de comparacao 2-up, **nao** usar para listas longas.

### `.kanban-column`

- 3 colunas usando `grid-template-columns: repeat(3, minmax(0, 1fr))`;
- cada coluna ganha barra de cor no topo via `::before`:
  - coluna 1 → `info → info-strong` (a fazer);
  - coluna 2 → `warning → accent-strong` (em andamento);
  - coluna 3 → `success → success-strong` (resolvido);
- `.kanban-column .case-card:hover` aplica `translateY(-1px)` + sombra suave;
- `.case-card.critical:hover` ativa borda vermelha viva — sinalizacao operacional;
- layout interno do `.case-card` no Kanban e diferente do operations: linha unica `1fr` (definido inline).

### `.drift-cell`

- gridded com gap 1px sobre `var(--border)` (efeito visual de tabela com bordas finas);
- `button.drift-cell` (celula clicavel) ganha `transform: scale(1.04)` + outline accent ao hover/focus;
- z-index temporario evita que celulas vizinhas tampem;
- `.drift-cell.legend` para cabecalhos: cor mais clara, uppercase, `--fs-2xs`;
- a coloracao **nao** vem do CSS — vem inline do componente via `color-mix(in srgb, var(--danger) 32%, var(--surface))` baseado em PSI vs threshold.

## 13. Como Criar Uma View Nova

1. Criar arquivo em `frontend/components/views/<NomeView>.tsx` marcado com `"use client"` se usar hooks ou eventos.
2. Definir interface explicita de props com formatadores e handlers (nunca importar de `app/`).
3. Reusar `Kpi`, `Sparkline`, `Trend`, `Badge`, `EmptyState` em vez de reimplementar.
4. Para charts, usar `recharts` + `ChartTooltip` customizado (ver `OverviewView.tsx`).
5. Usar tokens (`var(--accent-strong)`, `var(--space-3)`, etc.) em vez de hex literals.
6. Em `app/page.tsx`, adicionar o renderiazador condicional `{activeView === "<id>" && <NomeView ... />}`.

## 13.1 Renderizando Nomes De Entidade

O backend grava ``display_name = "[protected]"`` literal junto de ``display_name_encrypted`` quando o campo passa pela camada de privacidade. Para usuario autenticado, o backend chama ``reveal_entity`` antes de devolver — mas se o endpoint for novo e esquecer essa etapa, o frontend recebe ``[protected]`` direto.

**Sempre use os helpers em `frontend/lib/entity.ts`** ao renderizar entidades:

```typescript
import { entityDisplayName, entityIdentifier, cleanProtectedValue } from "@/lib/entity";

// Em um cartao de caso, predicao ou notificacao:
const name = entityDisplayName(caseDoc.entity, "Entidade");
const id = entityIdentifier(caseDoc.entity);

// Em campo solto (ex: ranking textual):
const label = cleanProtectedValue(entry.entity) || "Entidade não nomeada";
```

Os helpers tratam tres sentinels (``[protected]``, ``[redacted]``, ``[masked]``) e retornam string vazia para qualquer um. ``entityDisplayName`` faz fallback ``display_name → id → id_masked → fallback``, sempre filtrando sentinels antes de cada candidato. **Não** acesse ``entity.display_name`` direto.

## 14. Antipadroes A Evitar

- nao usar `style={{ background: "#xxxxxx" }}` direto. Use tokens.
- nao usar classes do Tailwind ou CSS-in-JS — o projeto e CSS puro com layered.
- nao remover `:focus-visible` outline sem substituir por `--shadow-focus`.
- nao misturar `Arial` ou `Helvetica` no codigo — todas as fontes vem via `next/font`.
- nao criar gradient decorativo. Cada gradient deve significar algo (status, hierarquia, foco).
- nao colocar mais de 3 cores semanticas no mesmo componente.
- nao acessar `entity.display_name` direto — use `entityDisplayName` de `lib/entity.ts` para nao mostrar o sentinel `[protected]`.

## 15. Referencia Cruzada

- Implementacao: `frontend/app/globals.css`, `frontend/components/`.
- Documentacao geral: [`documentacao-software.md`](documentacao-software.md), secoes 9 e 17.
- Manual de uso para usuario final: [`manual-funcionalidades.md`](manual-funcionalidades.md).
