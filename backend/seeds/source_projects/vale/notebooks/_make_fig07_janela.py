"""Fase 3F - Diagrama da janela de predicao (Figura 7).

Materializa em PNG (matplotlib) o diagrama que ilustra:
  - timeline do equipamento (eventos de telemetria)
  - sliding window 15 min (D008)
  - blackout 5 min anti-leakage (D010)
  - features cumulativas em janelas de lookback (1h/4h/12h)
  - alvo: incidente Don't Go em [t, t+H], H ∈ {1, 2, 4, 6, 8, 12} h (D001 v2)

Saida: `reports/figures/fig07_janela_predicao.png`.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from src.utils.paths import FIGURES_DIR

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(13, 6.5))

# Eixo: minutos relativos a t=0 (instante de scoring).
ax.set_xlim(-12 * 60 - 60, 12 * 60 + 60)
ax.set_ylim(-1, 9)
ax.axhline(0, color="black", lw=0.8)

# Linha do tempo (mostra t=0 como agora)
ax.axvline(0, color="black", lw=2, zorder=5)
ax.text(0, 8.4, "t (instante de scoring)", ha="center", fontsize=11, fontweight="bold")

# Blackout 5 min: [t-5, t]
black = mpatches.Rectangle(
    (-5, -0.3), 5, 1.0, facecolor="#d62728", alpha=0.5, edgecolor="black", lw=1
)
ax.add_patch(black)
ax.text(-2.5, 0.9, "blackout 5 min\n(anti-leakage, D010)",
        ha="center", va="bottom", fontsize=9, color="#660000")

# Lookback windows (1h, 4h, 12h)
# Cada uma vai de [t-W, t-5min]
colors = ["#9ecae1", "#6baed6", "#3182bd"]
labels = ["1h", "4h", "12h"]
ys = [1.5, 2.7, 3.9]
widths = [60, 240, 720]

for c, lab, y, w in zip(colors, labels, ys, widths):
    rect = mpatches.Rectangle(
        (-w, y), w - 5, 0.9, facecolor=c, alpha=0.6, edgecolor="black", lw=1
    )
    ax.add_patch(rect)
    ax.text(-w / 2, y + 0.45, f"lookback {lab}: features cumulativas",
            ha="center", va="center", fontsize=10, fontweight="bold")
    ax.annotate(
        "",
        xy=(-w, y + 0.45),
        xytext=(-w - 30, y + 0.45),
        arrowprops=dict(arrowstyle="->", color="black"),
    )
    ax.text(-w - 35, y + 0.45, f"-{lab}", ha="right", va="center", fontsize=9)

# Sliding window 15 min stride (D008) — pequenas marcacoes
for tau in range(-720, 1, 15):
    ax.plot([tau], [-0.7], marker="|", color="gray", markersize=6)
ax.text(-720, -0.85, "stride 15 min (D008)", ha="left", va="top", fontsize=9, color="gray")

# Lookahead windows (labels, 6 horizontes paralelos)
horizons = [(60, "1h"), (120, "2h"), (240, "4h"), (360, "6h"), (480, "8h"), (720, "12h")]
ys_h = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5]
hcolors = plt.cm.Greens(np.linspace(0.4, 0.9, len(horizons)))

for (h_min, h_lab), y, c in zip(horizons, ys_h, hcolors):
    rect = mpatches.Rectangle(
        (0, y), h_min, 0.42, facecolor=c, alpha=0.7, edgecolor="black", lw=0.7
    )
    ax.add_patch(rect)
    ax.text(h_min + 10, y + 0.21, f"y_dontgo_{h_lab}",
            ha="left", va="center", fontsize=9, fontweight="bold")

ax.text(360, 8.0,
        "6 horizontes de label paralelos (D001 v2)\n"
        "label = 1 se ha incidente em [t, t+H]",
        ha="center", fontsize=10, color="#1a5e1a")

# Eventos de telemetria simulados
np.random.seed(42)
event_times = np.random.uniform(-720, -5, 80).tolist()
event_times += np.random.uniform(-30, -5, 30).tolist()
for t_evt in event_times:
    ax.plot([t_evt], [0], marker="o", color="#377eb8", markersize=3, alpha=0.6)
# Don't Go simulado em t+200 min
ax.plot([200], [0], marker="*", color="red", markersize=20, zorder=10)
ax.text(200, -0.6, "incidente\nDon't Go", ha="center", va="top",
        fontsize=10, color="darkred", fontweight="bold")

# Eixos / grid / titulo
ax.set_xticks([-720, -480, -240, -60, 0, 60, 240, 480, 720])
ax.set_xticklabels(["-12h", "-8h", "-4h", "-1h", "0", "+1h", "+4h", "+8h", "+12h"])
ax.set_xlabel("Tempo relativo ao instante de scoring t (min)")
ax.set_yticks([])
ax.set_title(
    "Janela de predicao Don't Go — features (esq) + label (dir) + blackout anti-leakage\n"
    "(D008 sliding 15 min · D010 blackout 5 min · D001 v2 horizontes paralelos)",
    fontsize=12,
)
ax.grid(alpha=0.2, axis="x")
ax.set_aspect("auto")

# Legenda
patches = [
    mpatches.Patch(facecolor="#3182bd", alpha=0.6, label="lookback (features cumulativas)"),
    mpatches.Patch(facecolor="#d62728", alpha=0.5, label="blackout (proibido)"),
    mpatches.Patch(facecolor=hcolors[3], alpha=0.7, label="lookahead (label binaria)"),
]
ax.legend(handles=patches, loc="lower right", fontsize=10)

out = FIGURES_DIR / "fig07_janela_predicao.png"
fig.tight_layout()
fig.savefig(out, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"Figura 7 salva em {out}")
