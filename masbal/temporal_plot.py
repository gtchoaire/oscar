"""Desenho reutilizável da evolução temporal MASBAL."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from matplotlib.axes import Axes


def draw_temporal_lines(
    axis: Axes,
    *,
    time: np.ndarray,
    values: np.ndarray,
    columns: np.ndarray,
    labels: Sequence[str],
    colors: Sequence[str],
    time_name: str,
    time_unit: str,
    mass_unit: str,
    log_scale: bool,
    title_font: int,
    axis_font: int,
    line_width: float,
    total_width: float,
    total_color: str,
    reference_values: np.ndarray | None = None,
    time_limits: tuple[float, float] | None = None,
    mass_maximum: float | None = None,
) -> None:
    """Desenha as curvas MASBAL, incluindo a massa total de todas as categorias."""
    reference = values if reference_values is None else reference_values

    for index in columns:
        axis.plot(
            time,
            values[:, index],
            color=colors[index],
            lw=line_width,
            solid_capstyle="round",
            label=labels[index],
        )

    total = np.clip(values, 0, None).sum(axis=1)
    axis.plot(time, total, color=total_color, lw=total_width, label="Massa total")
    axis.set_title("Evolução temporal", fontsize=title_font, fontweight="bold")
    axis.set_xlabel(f"{time_name} ({time_unit})", fontsize=axis_font)
    axis.set_ylabel(f"Massa ({mass_unit})", fontsize=axis_font)

    complete = np.column_stack(
        (np.clip(reference[:, columns], 0, None), np.clip(reference, 0, None).sum(axis=1))
    )
    maximum = max(float(np.max(complete)), 1e-12) if mass_maximum is None else max(mass_maximum, 1e-12)
    if log_scale and np.any(complete > 0):
        positive = complete[complete > 0]
        axis.set_yscale("log")
        axis.set_ylim(max(float(np.min(positive)) * 0.7, 1e-12), maximum * 1.2)
    else:
        axis.set_ylim(0, maximum * 1.08)

    if time_limits is not None:
        axis.set_xlim(*time_limits)
