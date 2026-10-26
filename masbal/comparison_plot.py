"""Desenho científico comum aos gráficos comparativos e à exportação."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes

from .config import FONT_PERCENT_STEP, SERIES_COLORS, TOTAL_COLOR
from .data import ComparisonResult
from .typography import configure_matplotlib_typography
from .plot_style import COMPARISON_AXIS_BOX_ASPECT, TOTAL_LINE_WIDTH, apply_axes_style
from .theme import PLOT_BACKGROUND, PLOT_GRID, PLOT_MUTED, PLOT_SPINE, PLOT_TEXT


def draw_comparison_axis(
    axis: Axes,
    result: ComparisonResult,
    time_limits: tuple[float, float],
    mass_maximum: float,
    *,
    font_adjustment: int = 0,
    axis_label_size: int | None = None,
    axis_tick_size: int | None = None,
) -> None:
    """Desenha as séries MASBAL com escalas fornecidas, sem alterar os dados.

    A mesma função é utilizada na janela Qt e nos arquivos exportados.
    """
    configure_matplotlib_typography()
    font = lambda size: max(8, round(size * (1 + font_adjustment * FONT_PERCENT_STEP / 100)))
    label_size = font(13) if axis_label_size is None else axis_label_size
    tick_size = font(12) if axis_tick_size is None else axis_tick_size
    values = np.clip(result.values, 0, None)
    colors = [SERIES_COLORS.get(label, "#6c757d") for label in result.labels]
    axis.stackplot(
        result.time, values.T, colors=colors, alpha=0.92,
        edgecolor="white", linewidth=0.35,
    )
    axis.plot(result.time, values.sum(axis=1), color=TOTAL_COLOR, lw=TOTAL_LINE_WIDTH)
    axis.set_xlim(*time_limits)
    axis.set_ylim(0, mass_maximum * 1.08)
    axis.set_box_aspect(COMPARISON_AXIS_BOX_ASPECT)
    axis.set_xlabel(f"Tempo ({result.time_unit})", fontsize=label_size, color=PLOT_TEXT)
    axis.set_ylabel(f"Massa ({result.mass_unit})", fontsize=label_size, color=PLOT_TEXT)
    apply_axes_style(axis, tick_size=tick_size, grid_axis="y")
    axis.ticklabel_format(axis="y", style="sci", scilimits=(4, 4), useMathText=True)
    axis.yaxis.get_offset_text().set_fontsize(tick_size)
