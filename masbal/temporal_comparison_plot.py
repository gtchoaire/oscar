"""Adapta o gráfico temporal individual aos cartões de comparação MASBAL."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from matplotlib.axes import Axes

from .config import (FONT_BASE, FONT_PERCENT_STEP, FONT_SECTION, SERIES_COLORS,
                     TOTAL_COLOR)
from .data import ComparisonResult, load_table
from .plot_style import SERIES_LINE_WIDTH, TOTAL_LINE_WIDTH, apply_axes_style
from .temporal_plot import draw_temporal_lines
from . import plot_style


@lru_cache(maxsize=64)
def _source_units(path: Path) -> tuple[str, str, str]:
    """Recupera unidades do cabeçalho MASBAL uma única vez por arquivo."""
    _, _, time_name, time_unit, mass_unit = load_table(path)
    return time_name, time_unit, mass_unit


def draw_temporal_comparison_axis(
    axis: Axes,
    result: ComparisonResult,
    time_limits: tuple[float, float],
    mass_maximum: float,
    *,
    selected_labels: frozenset[str] | None = None,
    log_scale: bool = False,
    positive_minimum: float | None = None,
    font_adjustment: int = 0,
) -> None:
    """Desenha uma curva por categoria até o último registro do cenário."""
    labels = list(result.labels)
    columns = np.asarray(
        [i for i, label in enumerate(labels)
         if selected_labels is None or label in selected_labels],
        dtype=int,
    )
    if columns.size == 0:
        axis.set_axis_off()
        axis.text(0.5, 0.5, "Nenhuma série selecionada", ha="center", va="center",
                  transform=axis.transAxes)
        return

    time_name = getattr(result, "time_name", None)
    time_unit = getattr(result, "time_unit", None)
    mass_unit = getattr(result, "mass_unit", None)
    if not all((time_name, time_unit, mass_unit)):
        time_name, time_unit, mass_unit = _source_units(Path(result.path))
    time_name = "Tempo" if str(time_name).lower() == "time" else str(time_name).capitalize()
    time_unit = "dias" if str(time_unit).lower() in {"day", "days"} else str(time_unit)

    font_factor = 1 + font_adjustment * FONT_PERCENT_STEP / 100
    def font(size: int) -> int:
        return max(8, round(size * font_factor))
    colors = [SERIES_COLORS.get(label, "#6c757d") for label in labels]
    draw_temporal_lines(
        axis, time=np.asarray(result.time), values=np.asarray(result.values),
        columns=columns, labels=labels, colors=colors,
        time_name=time_name, time_unit=time_unit, mass_unit=str(mass_unit),
        log_scale=log_scale, title_font=font(FONT_SECTION), axis_font=font(FONT_BASE),
        line_width=SERIES_LINE_WIDTH, total_width=TOTAL_LINE_WIDTH,
        total_color=TOTAL_COLOR, reference_values=np.asarray(result.values),
        time_limits=time_limits, mass_maximum=mass_maximum,
    )
    # O nome do cenário já está no cabeçalho externo do cartão.
    axis.set_title("")
    if log_scale and positive_minimum is not None:
        axis.set_yscale("log")
        axis.set_ylim(max(positive_minimum * 0.7, 1e-12), mass_maximum * 1.2)
        axis.ticklabel_format(axis="y", style="sci", scilimits=(4, 4), useMathText=True)

    axis.ticklabel_format(axis="y", style="sci", scilimits=(4, 4), useMathText=True)
    aspect = getattr(plot_style, "COMPARISON_AXIS_BOX_ASPECT", 0.46)
    axis.set_box_aspect(aspect)
    apply_axes_style(axis, tick_size=font(FONT_BASE), grid_axis="y")
