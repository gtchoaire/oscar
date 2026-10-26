"""Acabamento comum dos eixos Matplotlib do MASBAL, sem alterar paletas.

Funcoes exclusivamente visuais: nao modificam valores nem escalas dos dados.
"""

from __future__ import annotations

from typing import Literal

from matplotlib.axes import Axes

from .theme import PLOT_BACKGROUND, PLOT_GRID, PLOT_MUTED, PLOT_SPINE, PLOT_TEXT

# Espessuras em pontos, usadas nos graficos individuais e comparativos.
SERIES_LINE_WIDTH = 2.2
TOTAL_LINE_WIDTH = 2.6
GRID_LINE_WIDTH = 0.7
SPINE_LINE_WIDTH = 0.8
TICK_LINE_WIDTH = 0.8
TICK_LENGTH = 4

GridAxis = Literal["x", "y", "both"] | None


def apply_axes_style(axis: Axes, *, tick_size: int, grid_axis: GridAxis = "y") -> None:
    """Aplica grade, bordas e marcas; preserva cores de dados, limites e escalas.

    ``grid_axis=None`` desliga a grade (adequado para mapas de cores).
    """
    if tick_size <= 0:
        raise ValueError("tick_size deve ser positivo")
    if grid_axis not in (None, "x", "y", "both"):
        raise ValueError("grid_axis deve ser 'x', 'y', 'both' ou None")

    axis.set_facecolor(PLOT_BACKGROUND)
    axis.set_axisbelow(True)
    axis.grid(False)
    if grid_axis is not None:
        axis.grid(
            True,
            axis=grid_axis,
            color=PLOT_GRID,
            linewidth=GRID_LINE_WIDTH,
            linestyle="--",
            alpha=0.8,
        )

    axis.tick_params(
        axis="both", labelsize=tick_size, colors=PLOT_MUTED,
        direction="out", width=TICK_LINE_WIDTH, length=TICK_LENGTH, pad=5,
    )
    axis.title.set_color(PLOT_TEXT)
    axis.xaxis.label.set_color(PLOT_TEXT)
    axis.yaxis.label.set_color(PLOT_TEXT)

    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(PLOT_SPINE)
        axis.spines[side].set_linewidth(SPINE_LINE_WIDTH)


# Geometria comparativa centralizada — incremento 4.4
# A proporção é altura/largura da ÁREA DOS EIXOS, não do cartão Qt.
COMPARISON_AXIS_BOX_ASPECT = 0.46

# Frações da figura Matplotlib, exclusivas da visualização Qt.
COMPARISON_CANVAS_MARGINS: dict[str, float] = {
    "left": 0.09,
    "right": 0.94,
    "top": 0.94,
    "bottom": 0.16,
}
