"""Canvases Matplotlib do resultado individual e da comparação."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QScrollArea, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .config import (CHART_ACCUMULATED, CHART_COMPOSITION, CHART_HEATMAP, CHART_TEMPORAL,
    COLORBAR_GAP, COLORBAR_WIDTH, COMPARISON_GRID_PLOT_HEIGHT, EXPANDED_COMPOSITION_POSITION,
    EXPANDED_HEATMAP_POSITION, EXPANDED_UPPER_POSITION, FONT_ADJUSTMENT_MAX,
    FONT_ADJUSTMENT_MIN, FONT_BASE, FONT_PERCENT_STEP, FONT_SECTION, FONT_SMALL, FONT_STEP,
    LEGEND_LABELS, LOWER_AXIS_LABELS, NORMAL_CHART_POSITIONS, NORMAL_LEGEND_ANCHOR,
    NORMAL_LEGEND_COLUMNS, SERIES_COLORS, SIDE_LEGEND_ANCHOR, SIDE_LEGEND_MIN_HEIGHT,
    SIDE_LEGEND_MIN_WIDTH, TOTAL_COLOR)
from .data import ComparisonResult
from .typography import configure_matplotlib_typography
from .plot_style import COMPARISON_CANVAS_MARGINS, SERIES_LINE_WIDTH, TOTAL_LINE_WIDTH, apply_axes_style
from .comparison_plot import draw_comparison_axis
from .theme import PLOT_BACKGROUND, PLOT_GRID, PLOT_MUTED, PLOT_SPINE, PLOT_TEXT

class SeriesLabel(QLabel):
    """Rótulo que quebra linhas e também alterna a seleção da série."""

    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MassBalanceCanvas(FigureCanvas):
    """Canvas Matplotlib incorporado à interface Qt."""

    expanded_changed = Signal(bool)

    def __init__(
        self,
        time: np.ndarray,
        values: np.ndarray,
        labels: list[str],
        time_name: str,
        time_unit: str,
        mass_unit: str,
    ) -> None:
        configure_matplotlib_typography()
        self.figure = Figure(figsize=(12, 8), dpi=100, facecolor="white")
        super().__init__(self.figure)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(680, 500)

        self.time = time
        self.values = values
        self.labels = labels
        self.lower_axis_labels = [LOWER_AXIS_LABELS.get(label, label) for label in labels]
        self.time_name = time_name
        self.time_unit = time_unit
        self.mass_unit = mass_unit
        self.colors = np.asarray([SERIES_COLORS.get(label, "#6c757d") for label in labels])
        self.selected = np.ones(len(labels), dtype=bool)
        self.current_index = len(time) - 1
        self.log_scale = False
        self.expanded_index: int | None = None
        self.colorbar = None
        self.shared_legend = None
        self._side_legend_enabled = False
        self._font_scale = 1.0
        self._font_adjustment = 0

        self.axes = [
            self.figure.add_subplot(2, 2, 1),
            self.figure.add_subplot(2, 2, 2),
            self.figure.add_subplot(2, 2, 3),
            self.figure.add_subplot(2, 2, 4),
        ]
        self.redraw()
        self.mpl_connect("button_press_event", self._on_click)

    # -------------------------------------------------------------------------
    # TIPOGRAFIA RESPONSIVA DO MATPLOTLIB
    # -------------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802 - nome definido pelo Qt
        """Reduz a tipografia dos gráficos junto com a largura disponível."""
        super().resizeEvent(event)
        if not hasattr(self, "axes"):
            return
        new_scale = float(np.clip(event.size().width() / 1100.0, 0.62, 1.0))
        font_changed = abs(new_scale - self._font_scale) >= 0.04
        self._font_scale = new_scale
        legend_mode_changed = self._can_show_side_legend(int(np.count_nonzero(self.selected))) != self._side_legend_enabled
        if font_changed or legend_mode_changed:
            self.redraw()

    def _font(self, base_size: int) -> int:
        """Ajusta a fonte ao canvas e aplica o zoom em passos discretos."""
        responsive_size = int(round(base_size * self._font_scale / FONT_STEP)) * FONT_STEP
        return int(np.clip(responsive_size + FONT_STEP * self._font_adjustment, 8, 40))

    def _tick_font(self) -> int:
        """Escala legendas e marcações com o controle tipográfico global."""
        return self._font(FONT_SMALL)

    def _axis_font(self) -> int:
        """Escala também os títulos dos eixos."""
        return self._font(FONT_BASE)

    def _chart_title_font(self) -> int:
        """Escala os títulos dos quatro gráficos."""
        return self._font(FONT_SECTION)

    def change_font_size(self, step: int) -> int:
        """Aumenta ou reduz a tipografia dos gráficos junto com a interface."""
        self._font_adjustment = int(
            np.clip(
                self._font_adjustment + step,
                FONT_ADJUSTMENT_MIN,
                FONT_ADJUSTMENT_MAX,
            )
        )
        self.redraw()
        return self._font_adjustment

    def reset_font_size(self) -> None:
        self._font_adjustment = 0

    # -------------------------------------------------------------------------
    # ESTADO INTERATIVO: tempo, séries e escala
    # -------------------------------------------------------------------------
    def set_current_index(self, index: int) -> None:
        self.current_index = int(np.clip(index, 0, len(self.time) - 1))
        self.redraw()

    def set_selected(self, index: int, checked: bool) -> None:
        self.selected[index] = checked
        self.redraw()

    def set_log_scale(self, enabled: bool) -> None:
        self.log_scale = enabled
        self.redraw()

    # -------------------------------------------------------------------------
    # FLUXO PRINCIPAL DE DESENHO
    # -------------------------------------------------------------------------
    def redraw(self) -> None:
        visible_columns = np.flatnonzero(self.selected)
        shown_time = self.time[: self.current_index + 1]
        shown_values = self.values[: self.current_index + 1]

        for axis in self.axes:
            axis.clear()
            axis.set_axis_on()
            axis.set_visible(True)
        if self.shared_legend is not None:
            self.shared_legend.remove()
            self.shared_legend = None

        line_axis, stack_axis, bar_axis, heat_axis = self.axes
        if visible_columns.size == 0:
            self._draw_empty_state(line_axis)
            for axis in self.axes[1:]:
                axis.set_visible(False)
            if self.colorbar is not None:
                self.colorbar.ax.set_visible(False)
            self.draw_idle()
            return

        self._draw_lines(line_axis, shown_time, shown_values, visible_columns)
        self._draw_stack(stack_axis, shown_time, shown_values, visible_columns)
        self._draw_composition(bar_axis, shown_values, visible_columns)
        self._draw_heatmap(heat_axis, shown_time, shown_values, visible_columns)
        self._draw_shared_legend(line_axis, visible_columns)

        for axis in self.axes:
            self._style_axis(axis)
        category_font = self._tick_font()
        bar_axis.tick_params(axis="y", labelsize=category_font, pad=12)
        heat_axis.tick_params(axis="y", labelsize=category_font, pad=12)
        if self.expanded_index is not None:
            self._apply_expanded_layout()
        self.draw_idle()

    def _draw_empty_state(self, axis) -> None:
        """Mostra uma orientação clara quando nenhuma série está ativa."""
        axis.set_position((0.12, 0.20, 0.76, 0.56))
        axis.set_axis_off()
        axis.text(
            0.5,
            0.56,
            "Nenhuma série selecionada",
            ha="center",
            va="center",
            fontsize=self._font(FONT_SECTION),
            fontweight="bold",
            color=PLOT_TEXT,
            transform=axis.transAxes,
        )
        axis.text(
            0.5,
            0.44,
            "Use “Todas” ou marque uma variável na barra lateral para continuar.",
            ha="center",
            va="center",
            fontsize=self._tick_font(),
            color=PLOT_MUTED,
            transform=axis.transAxes,
        )

    def _style_axis(self, axis) -> None:
        """Uniformiza os eixos sem alterar escalas ou valores."""
        if axis is self.axes[CHART_HEATMAP]:
            grid_axis = None
        elif axis is self.axes[CHART_COMPOSITION]:
            grid_axis = "x"
        else:
            grid_axis = "y"
        apply_axes_style(axis, tick_size=self._tick_font(), grid_axis=grid_axis)

    @staticmethod
    def _set_time_limits(axis, time: np.ndarray) -> None:
        """Mantém o eixo X evolutivo e evita limites idênticos no primeiro passo."""
        start = float(time[0])
        end = float(time[-1])
        if start == end:
            half_step = max(abs(start) * 0.01, 1e-6)
            start, end = start - half_step, end + half_step
        axis.set_xlim(start, end)

    # -------------------------------------------------------------------------
    # GRÁFICO 1 — EVOLUÇÃO TEMPORAL
    # -------------------------------------------------------------------------
    def _draw_lines(self, axis, time, values, columns) -> None:
        for index in columns:
            axis.plot(
                time,
                values[:, index],
                color=self.colors[index],
                lw=SERIES_LINE_WIDTH,
                solid_capstyle="round",
                label=self.labels[index],
            )
        total = np.clip(self.values, 0, None).sum(axis=1)[: len(time)]
        axis.plot(time, total, color=TOTAL_COLOR, lw=TOTAL_LINE_WIDTH, label="Massa total")
        axis.set_title(
            "Evolução temporal",
            fontsize=self._chart_title_font(),
            fontweight="bold",
        )
        axis.set_xlabel(
            f"{self.time_name} ({self.time_unit})", fontsize=self._axis_font()
        )
        axis.set_ylabel(f"Massa ({self.mass_unit})", fontsize=self._axis_font())
        complete = np.column_stack(
            (
                np.clip(self.values[:, columns], 0, None),
                np.clip(self.values, 0, None).sum(axis=1),
            )
        )
        maximum = max(float(np.max(complete)), 1e-12)
        if self.log_scale and np.any(complete > 0):
            positive = complete[complete > 0]
            axis.set_yscale("log")
            axis.set_ylim(max(float(np.min(positive)) * 0.7, 1e-12), maximum * 1.2)
        else:
            axis.set_ylim(0, maximum * 1.08)
        self._set_time_limits(axis, time)


    # -------------------------------------------------------------------------
    # GRÁFICO 2 — DISTRIBUIÇÃO ACUMULADA
    # -------------------------------------------------------------------------
    def _draw_stack(self, axis, time, values, columns) -> None:
        stack_values = np.clip(values[:, columns], 0, None).T
        axis.stackplot(
            time, stack_values, colors=self.colors[columns], alpha=0.86,
            labels=[self.labels[index] for index in columns],
        )
        total = np.clip(self.values, 0, None).sum(axis=1)[: len(time)]
        axis.plot(time, total, color=TOTAL_COLOR, lw=2.2, label="Massa total")
        axis.set_title(
            "Distribuição acumulada",
            fontsize=self._chart_title_font(),
            fontweight="bold",
        )
        axis.set_xlabel(
            f"{self.time_name} ({self.time_unit})", fontsize=self._axis_font()
        )
        axis.set_ylabel(f"Massa ({self.mass_unit})", fontsize=self._axis_font())
        complete_totals = np.clip(self.values, 0, None).sum(axis=1)
        maximum = max(float(np.max(complete_totals)), 1e-12)
        if self.log_scale and np.any(complete_totals > 0):
            positive = complete_totals[complete_totals > 0]
            axis.set_yscale("log")
            axis.set_ylim(max(float(np.min(positive)) * 0.7, 1e-12), maximum * 1.2)
        else:
            axis.set_ylim(0, maximum * 1.08)
        self._set_time_limits(axis, time)

    # -------------------------------------------------------------------------
    # GRÁFICO 3 — COMPOSIÇÃO NO TEMPO ATUAL
    # -------------------------------------------------------------------------
    def _draw_composition(self, axis, values, columns) -> None:
        # A ordem segue permanentemente a ordem das colunas. Ela não é
        # reordenada pelos valores, portanto as categorias não saltam no eixo Y.
        current_values = values[-1, columns]
        positions = np.arange(columns.size)
        axis.barh(
            positions,
            current_values,
            height=0.68,
            color=self.colors[columns],
            edgecolor="#ffffff",
            linewidth=0.6,
            alpha=0.94,
        )
        axis.set_yticks(positions, [self._category_label(index) for index in columns])
        axis.invert_yaxis()
        axis.set_title(
            "Composição atual",
            fontsize=self._chart_title_font(),
            fontweight="bold",
        )
        axis.set_xlabel(f"Massa ({self.mass_unit})", fontsize=self._axis_font())
        complete = np.clip(self.values[:, columns], 0, None)
        maximum = max(float(np.max(complete)), 1e-12)
        if self.log_scale and np.any(complete > 0):
            positive = complete[complete > 0]
            axis.set_xscale("log")
            axis.set_xlim(max(float(np.min(positive)) * 0.7, 1e-12), maximum * 1.2)
        else:
            axis.set_xlim(0, maximum * 1.08)

    # -------------------------------------------------------------------------
    # GRÁFICO 4 — MAPA DE PARTICIPAÇÃO E SUA BARRA DE CORES
    # -------------------------------------------------------------------------
    def _draw_heatmap(self, axis, time, values, columns) -> None:
        selected_values = np.clip(values[:, columns], 0, None)
        totals = selected_values.sum(axis=1, keepdims=True)
        shares = np.divide(
            selected_values, totals, out=np.zeros_like(selected_values), where=totals != 0
        ).T * 100
        start, end = float(time[0]), float(time[-1])
        if start == end:
            half_step = max(abs(start) * 0.01, 1e-6)
            start, end = start - half_step, end + half_step
        image = axis.imshow(
            shares,
            aspect="auto",
            origin="upper",
            interpolation="nearest",
            extent=(start, end, columns.size - 0.5, -0.5),
            cmap="viridis",
            vmin=0,
            vmax=100,
        )
        axis.set_yticks(
            np.arange(columns.size), [self._category_label(index) for index in columns]
        )
        axis.yaxis.tick_left()
        axis.tick_params(axis="y", labelleft=True, labelright=False, pad=6)
        axis.set_title(
            "Participação (%)" if self._font_adjustment > 0 else "Participação no total (%)",
            fontsize=self._chart_title_font(),
            fontweight="bold",
        )
        axis.set_xlabel(
            f"{self.time_name} ({self.time_unit})", fontsize=self._axis_font()
        )
        if self.colorbar is None:
            self.colorbar = self.figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
        else:
            self.colorbar.update_normal(image)
            self.colorbar.ax.set_visible(True)
        # A unidade já consta no título; repetir "%" à direita cortava o rótulo.
        self.colorbar.set_label("")
        self.colorbar.ax.tick_params(
            labelsize=self._tick_font(), colors=PLOT_MUTED, width=0.8
        )
        self.colorbar.ax.yaxis.label.set_color(PLOT_TEXT)
        self.colorbar.outline.set_edgecolor(PLOT_SPINE)
        self.colorbar.outline.set_linewidth(0.8)
        self.colorbar.ax.yaxis.set_ticks_position("right")
        self.colorbar.ax.yaxis.set_label_position("right")
        self._apply_normal_layout()

    def _apply_normal_layout(self) -> None:
        """Mantém a geometria escolhida pelo usuário em qualquer zoom de fonte."""
        for chart_axis, position in zip(self.axes, NORMAL_CHART_POSITIONS):
            chart_axis.set_position(position)
        self._place_colorbar_next_to_heatmap()

    def _place_colorbar_next_to_heatmap(self) -> None:
        """Ancora a barra de cores ao mapa, mesmo após editar sua posição."""
        if self.colorbar is None:
            return
        heatmap_position = self.axes[CHART_HEATMAP].get_position()
        left = min(heatmap_position.x1 + COLORBAR_GAP, 0.96)
        self.colorbar.ax.set_position(
            (left, heatmap_position.y0, COLORBAR_WIDTH, heatmap_position.height)
        )

    def _category_label(self, index: int) -> str:
        """Lê o nome configurável do eixo Y, comum aos dois gráficos inferiores."""
        return self.lower_axis_labels[index]

    def _can_show_side_legend(self, visible_count: int) -> bool:
        """Exige largura e altura suficientes sem mudar o tamanho dos eixos."""
        return (
            self.expanded_index is None
            and self.width() >= SIDE_LEGEND_MIN_WIDTH
            and self.height() >= SIDE_LEGEND_MIN_HEIGHT
            and (visible_count + 1) * self._tick_font() * 1.45
            <= self.height() * 0.44
        )

    def _draw_shared_legend(self, source_axis, visible_columns: np.ndarray) -> None:
        """Mantém a legenda lateral ao acumulado quando houver espaço livre."""
        side_legend = self._can_show_side_legend(len(visible_columns))
        self._side_legend_enabled = side_legend
        if side_legend:
            handles = [Patch(facecolor=self.colors[index], edgecolor="none") for index in visible_columns]
            labels = [LEGEND_LABELS.get(self.labels[index], self.labels[index]) for index in visible_columns]
            handles.append(Line2D([0], [0], color=TOTAL_COLOR, linewidth=TOTAL_LINE_WIDTH))
            labels.append("Massa total")
            anchor = SIDE_LEGEND_ANCHOR
            location = "upper left"
            columns = 1
            legend_size = self._tick_font()
        else:
            handles, labels = source_axis.get_legend_handles_labels()
            labels = [LEGEND_LABELS.get(label, label) for label in labels]
            anchor = NORMAL_LEGEND_ANCHOR
            location = "upper center"
            columns = 3 if self._font_adjustment > 0 else NORMAL_LEGEND_COLUMNS
            legend_size = self._tick_font()
        self.shared_legend = self.figure.legend(
            handles,
            labels,
            fontsize=legend_size,
            ncol=columns,
            loc=location,
            bbox_to_anchor=anchor,
            borderaxespad=0,
            labelspacing=0.08 if side_legend else 0.15,
            columnspacing=1.2,
            handlelength=1.3 if side_legend else 1.8,
            handletextpad=0.5 if side_legend else 0.6,
            frameon=True,
            fancybox=True,
            framealpha=1.0,
            facecolor="#e0e2db" if side_legend else "#ffffff",
            edgecolor="#5f7470" if side_legend else "#c3c3c3",
        )

    # -------------------------------------------------------------------------
    # AMPLIAÇÃO E RETORNO AO MOSAICO
    # -------------------------------------------------------------------------
    def _on_click(self, event) -> None:
        if self.expanded_index is not None or event.inaxes not in self.axes:
            return
        self.expanded_index = self.axes.index(event.inaxes)
        self.redraw()
        self.expanded_changed.emit(True)

    def _apply_expanded_layout(self) -> None:
        if self.expanded_index is None:
            return
        selected_axis = self.axes[self.expanded_index]
        for axis in self.axes:
            axis.set_visible(axis is selected_axis)
        if self.expanded_index == CHART_HEATMAP:
            selected_axis.set_position(EXPANDED_HEATMAP_POSITION)
            self._place_colorbar_next_to_heatmap()
            self.colorbar.ax.set_visible(True)
            self.shared_legend.set_visible(False)
        elif self.expanded_index == CHART_COMPOSITION:
            selected_axis.set_position(EXPANDED_COMPOSITION_POSITION)
            self.colorbar.ax.set_visible(False)
            self.shared_legend.set_visible(False)
        else:
            # Reserva o lado direito para a legenda externa.
            selected_axis.set_position(EXPANDED_UPPER_POSITION)
            self.colorbar.ax.set_visible(False)
            self.shared_legend.set_visible(True)

    def restore_grid(self) -> None:
        if self.expanded_index is None:
            return
        self.expanded_index = None
        self.expanded_changed.emit(False)
        self.redraw()

class ComparisonCanvas(FigureCanvas):
    """Um gráfico do mosaico, com escalas comuns a todos os resultados."""

    zoom_requested = Signal()

    def __init__(
        self,
        result: ComparisonResult,
        time_limits: tuple[float, float],
        mass_maximum: float,
    ) -> None:
        self.figure = Figure(figsize=(5.2, 3.2), dpi=100, facecolor="white")
        super().__init__(self.figure)
        self.result = result
        self.time_limits = time_limits
        self.mass_maximum = mass_maximum
        self.font_adjustment = 0
        self.setMinimumWidth(330)
        self.setFixedHeight(COMPARISON_GRID_PLOT_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.redraw()
        self.mpl_connect("button_press_event", self._on_click)

    def _on_click(self, event) -> None:
        if event.inaxes is not None and event.button == 1:
            self.zoom_requested.emit()

    def set_font_adjustment(self, adjustment: int) -> None:
        if adjustment != self.font_adjustment:
            self.font_adjustment = adjustment
            self.redraw()

    def set_limits(self, time_limits: tuple[float, float], mass_maximum: float) -> None:
        """Mantém a mesma escala em todos os gráficos ainda visíveis."""
        if self.time_limits != time_limits or self.mass_maximum != mass_maximum:
            self.time_limits = time_limits
            self.mass_maximum = mass_maximum
            self.redraw()

    def _font(self, size: int) -> int:
        return max(8, round(size * (1 + self.font_adjustment * FONT_PERCENT_STEP / 100)))

    def wheelEvent(self, event) -> None:  # noqa: N802 - nome definido pelo Qt
        """Faz a roda do mouse percorrer a página mesmo sobre o gráfico."""
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        if parent is None or not event.angleDelta().y():
            super().wheelEvent(event)
            return
        bar = parent.verticalScrollBar()
        bar.setValue(bar.value() - round(event.angleDelta().y() / 120 * 72))
        event.accept()

    def redraw(self) -> None:
        self.figure.clear()
        axis = self.figure.add_subplot(111)
        draw_comparison_axis(
            axis, self.result, self.time_limits, self.mass_maximum,
            font_adjustment=self.font_adjustment,
        )
        self.figure.subplots_adjust(**COMPARISON_CANVAS_MARGINS)
        self.draw_idle()
