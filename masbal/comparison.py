"""Tela de comparação da distribuição acumulada."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget, QFileDialog, QMessageBox)
from numpy.strings import index

from .charts import ComparisonCanvas
from .comparison_export import save_comparison_report
from .config import (COMPARISON_EXPANDED_PLOT_HEIGHT, COMPARISON_EXPANDED_PLOT_WIDTH, COMPARISON_GRID_COLUMNS, COMPARISON_GRID_PLOT_HEIGHT, COMPARISON_GRID_PLOT_WIDTH,
    FONT_ADJUSTMENT_MAX, FONT_ADJUSTMENT_MIN, FONT_PERCENT_STEP, SERIES_COLORS,
    SERIES_CONFIG, TOTAL_COLOR)
from .data import ComparisonResult, simulation_title
from .filters import SimulationFilterBar
from .theme import scaled_app_style

class ComparisonView(QWidget):
    """Exibe a comparação na mesma janela da tela inicial."""

    back_requested = Signal()

    def __init__(self, results: list[ComparisonResult]) -> None:
        super().__init__()
        self.results = results
        self.setObjectName("comparisonRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._legend_columns = 0
        self.font_adjustment = 0
        self.expanded_index: int | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        header = QVBoxLayout()
        header.setSpacing(4)
        header_top = QHBoxLayout()
        title = QLabel("Distribuição acumulada")
        title.setObjectName("comparisonTitle")
        header_top.addWidget(title, stretch=1)

        count = QLabel(f"{len(results)} resultados")
        count.setObjectName("comparisonCount")
        self.count_label = count
        header_top.addWidget(count)
        header.addLayout(header_top)

        subtitle = QLabel(
            "Compare os cenários carregados com a mesma escala de tempo e massa. "
            "Para incluir outros, volte aos arquivos."
        )
        subtitle.setObjectName("startHelp")
        subtitle.setWordWrap(True)
        header.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.addStretch()
        export_button = QPushButton("Exportar comparação")
        export_button.setToolTip("Exportar os cenários filtrados em PNG 300 dpi, PDF, SVG ou EPS")
        export_button.clicked.connect(self._export_comparison)
        actions.addWidget(export_button)
        font_down = QPushButton("A−")
        font_down.setObjectName("comparisonZoomButton")
        font_down.setToolTip("Diminuir os textos da comparação")
        font_down.clicked.connect(lambda: self._change_font(-1))
        self.font_down = font_down
        actions.addWidget(font_down)
        font_reset = QPushButton("100%")
        font_reset.setObjectName("comparisonZoomReset")
        font_reset.setToolTip("Restaurar o tamanho padrão dos textos")
        font_reset.clicked.connect(lambda: self._set_font_adjustment(0))
        self.font_reset = font_reset
        actions.addWidget(font_reset)
        font_up = QPushButton("A+")
        font_up.setObjectName("comparisonZoomButton")
        font_up.setToolTip("Ampliar os textos da comparação")
        font_up.clicked.connect(lambda: self._change_font(1))
        self.font_up = font_up
        actions.addWidget(font_up)
        self.grid_button = QPushButton("Voltar à grade")
        self.grid_button.setToolTip("Restaurar os gráficos lado a lado")
        self.grid_button.clicked.connect(self._restore_grid)
        self.grid_button.hide()
        actions.addWidget(self.grid_button)
        top_button = QPushButton("↑  Voltar ao topo")
        top_button.setObjectName("comparisonTopButton")
        actions.addWidget(top_button)
        back_button = QPushButton("Voltar aos arquivos")
        back_button.clicked.connect(self.back_requested.emit)
        actions.addWidget(back_button)
        header.addLayout(actions)
        layout.addLayout(header)

        self.filters = SimulationFilterBar()
        layout.addWidget(self.filters)

        # A legenda pertence à tela, não ao canvas: permanece visível ao rolar.
        legend = QFrame()
        legend.setObjectName("comparisonLegend")
        legend_layout = QVBoxLayout(legend)
        legend_layout.setContentsMargins(16, 10, 16, 10)
        legend_layout.setSpacing(8)
        legend_title = QLabel("BALANÇO DE MASSA  ·  SÉRIES")
        legend_title.setObjectName("comparisonLegendTitle")
        legend_layout.addWidget(legend_title)
        self.legend_grid = QGridLayout()
        self.legend_grid.setHorizontalSpacing(14)
        self.legend_grid.setVerticalSpacing(5)
        legend_layout.addLayout(self.legend_grid)
        self.legend_entries = self._make_legend_entries(results)
        self._layout_legend(3)
        layout.addWidget(legend)

        scroll = QScrollArea()
        scroll.setObjectName("comparisonScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.verticalScrollBar().setSingleStep(72)
        top_button.clicked.connect(lambda: scroll.verticalScrollBar().setValue(0))
        scroll.verticalScrollBar().valueChanged.connect(
            lambda value: top_button.setEnabled(value > 0)
        )
        top_button.setEnabled(False)

        content = QWidget()
        content.setObjectName("comparisonContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(10)
        instruction = QLabel("Simulações lado a lado  ·  mesmas escalas em todos os gráficos")
        instruction.setObjectName("comparisonInstruction")
        content_layout.addWidget(instruction)

        time_min = min(float(result.time[0]) for result in results)
        time_max = max(float(result.time[-1]) for result in results)
        if time_min == time_max:
            time_min -= 0.5
            time_max += 0.5
        mass_maximum = max(
            1e-12,
            *(float(np.max(np.clip(result.values, 0, None).sum(axis=1))) for result in results),
        )
        chart_grid = QGridLayout()
        chart_grid.setContentsMargins(0, 0, 0, 0)
        chart_grid.setHorizontalSpacing(16)
        chart_grid.setVerticalSpacing(14)
        # chart_grid.setColumnStretch(0, 1)
        # chart_grid.setColumnStretch(1, 1)
        self.chart_grid = chart_grid
        self.chart_cards: list[QFrame] = []
        self.chart_buttons: list[QPushButton] = []
        self.canvases: list[ComparisonCanvas] = []
        for index, result in enumerate(results):
            card = self._make_chart_card(index, result, (time_min, time_max), mass_maximum)
            self.chart_cards.append(card)
            # chart_grid.addWidget(card, index // 2, index % 2)
            chart_grid.addWidget(card, index // COMPARISON_GRID_COLUMNS, index % COMPARISON_GRID_COLUMNS)
        self.empty_filter_label = QLabel("Nenhuma simulação corresponde aos filtros atuais.")
        self.empty_filter_label.setObjectName("comparisonInstruction")
        self.empty_filter_label.hide()
        content_layout.addWidget(self.empty_filter_label)

        #alteração importante
        chart_row = QHBoxLayout()
        chart_row.setContentsMargins(0, 0, 0, 0)
        chart_row.setSpacing(0)

        chart_row.addStretch(1)
        chart_row.addLayout(chart_grid)
        chart_row.addStretch(1)

        content_layout.addLayout(chart_row)

        # content_layout.addLayout(chart_grid)
        content_layout.addStretch()
        scroll.setWidget(content)
        self.scroll = scroll
        layout.addWidget(scroll, stretch=1)
        self.filters.changed.connect(self._apply_filters)
        self.filters.set_paths([result.path for result in results])

    def _export_comparison(self) -> None:
        """Exporta apenas os cenários ativos no filtro; zoom não altera a saída."""
        visible_results = [
            result for result in self.results if self.filters.matches(result.path)
        ]
        if not visible_results:
            QMessageBox.information(self, "Exportação MASBAL", "Nenhum cenário visível para exportar.")
            return
        default = visible_results[0].path.parent / "comparacao_masbal.png"
        output, selected_filter = QFileDialog.getSaveFileName(
            self, "Exportar comparação MASBAL", str(default),
            "Imagem PNG (*.png);;Documento PDF (*.pdf);;Imagem SVG (*.svg);;Imagem EPS (*.eps)",
        )
        if not output:
            return
        target = Path(output)
        if not target.suffix:
            extension = {
                "Imagem PNG (*.png)": ".png", "Documento PDF (*.pdf)": ".pdf",
                "Imagem SVG (*.svg)": ".svg", "Imagem EPS (*.eps)": ".eps",
            }.get(selected_filter, ".png")
            target = target.with_suffix(extension)
        try:
            written = save_comparison_report(visible_results, target)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Falha ao exportar comparação", str(error))
            return
        message = (f"{len(written)} arquivo(s) exportado(s) em:\n"
                   f"{written[0].parent}\n\n"
                   f"Primeiro arquivo: {written[0].name}")
        QMessageBox.information(self, "Exportação concluída", message)

    def _apply_filters(self) -> None:
        """Reorganiza apenas os cartões visíveis e recalcula a escala comum."""
        self.expanded_index = None
        self.grid_button.hide()
        visible = [
            index for index, result in enumerate(self.results)
            if self.filters.matches(result.path)
        ]
        for index, card in enumerate(self.chart_cards):
            self.chart_grid.removeWidget(card)
            card.hide()
            card.setFixedWidth(COMPARISON_GRID_PLOT_WIDTH + 32)
            self.canvases[index].setFixedWidth(COMPARISON_GRID_PLOT_WIDTH)
            self.canvases[index].setFixedHeight(COMPARISON_GRID_PLOT_HEIGHT)
            self.chart_buttons[index].setText("Ampliar")
        for position, index in enumerate(visible):
            card = self.chart_cards[index]
            self.chart_grid.addWidget(card, position // COMPARISON_GRID_COLUMNS, position % COMPARISON_GRID_COLUMNS)
            card.show()
        if visible:
            active = [self.results[index] for index in visible]
            time_min = min(float(result.time[0]) for result in active)
            time_max = max(float(result.time[-1]) for result in active)
            if time_min == time_max:
                time_min -= 0.5
                time_max += 0.5
            maximum = max(
                1e-12,
                *(float(np.max(np.clip(result.values, 0, None).sum(axis=1))) for result in active),
            )
            for index in visible:
                self.canvases[index].set_limits((time_min, time_max), maximum)
        self.empty_filter_label.setVisible(not visible)
        self.count_label.setText(f"{len(visible)} de {len(self.results)} resultados")

    def _make_legend_entries(self, results: list[ComparisonResult]) -> list[QWidget]:
        present = {label for result in results for label in result.labels}
        labels = [item["label"] for item in SERIES_CONFIG if item["label"] in present]
        labels += sorted(present.difference(labels))
        entries: list[QWidget] = []
        for label in [*labels, "Massa total"]:
            item = QWidget()
            row = QHBoxLayout(item)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)
            swatch = QFrame()
            swatch.setFixedSize(18, 12 if label != "Massa total" else 3)
            color = TOTAL_COLOR if label == "Massa total" else SERIES_COLORS.get(label, "#6c757d")
            border = "border: 1px solid #b8c5cc;" if label != "Massa total" else ""
            swatch.setStyleSheet(f"background: {color}; border-radius: 2px; {border}")
            row.addWidget(swatch)
            name = QLabel(label)
            name.setObjectName("comparisonLegendName")
            row.addWidget(name)
            row.addStretch()
            entries.append(item)
        return entries

    def _layout_legend(self, columns: int) -> None:
        if columns == self._legend_columns:
            return
        while self.legend_grid.count():
            self.legend_grid.takeAt(0)
        for index, entry in enumerate(self.legend_entries):
            self.legend_grid.addWidget(entry, index // columns, index % columns)
        for column in range(max(columns, self._legend_columns)):
            self.legend_grid.setColumnStretch(column, 1 if column < columns else 0)
        self._legend_columns = columns

    def resizeEvent(self, event) -> None:  # noqa: N802 - nome definido pelo Qt
        super().resizeEvent(event)
        self._update_legend_columns()

    def _update_legend_columns(self) -> None:
        effective_width = self.width() / (1 + self.font_adjustment * FONT_PERCENT_STEP / 100)
        self._layout_legend(4 if effective_width >= 1500 else 3 if effective_width >= 1100 else 2)

    def _change_font(self, step: int) -> None:
        self._set_font_adjustment(self.font_adjustment + step)

    def _set_font_adjustment(self, adjustment: int) -> None:
        adjustment = int(np.clip(adjustment, FONT_ADJUSTMENT_MIN, FONT_ADJUSTMENT_MAX))
        self.font_adjustment = adjustment
        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(scaled_app_style(adjustment))
        for canvas in self.canvases:
            canvas.set_font_adjustment(adjustment)
        self.font_down.setEnabled(adjustment > FONT_ADJUSTMENT_MIN)
        self.font_up.setEnabled(adjustment < FONT_ADJUSTMENT_MAX)
        self.font_reset.setText(f"{100 + adjustment * FONT_PERCENT_STEP}%")
        self._update_legend_columns()

    def _toggle_chart_zoom(self, index: int) -> None:
        if self.expanded_index == index:
            self._restore_grid()
            return
        if self.expanded_index is not None:
            self._restore_grid()
        self.expanded_index = index
        for card in self.chart_cards:
            card.hide()
        selected = self.chart_cards[index]
        self.chart_grid.removeWidget(selected)
        self.chart_grid.addWidget(selected, 0, 0, 1, COMPARISON_GRID_COLUMNS)
        selected.show()
        selected.setFixedWidth(COMPARISON_EXPANDED_PLOT_WIDTH + 32)
        self.canvases[index].setFixedWidth(COMPARISON_EXPANDED_PLOT_WIDTH)
        self.canvases[index].setFixedHeight(COMPARISON_EXPANDED_PLOT_HEIGHT)
        self.chart_buttons[index].setText("Reduzir")
        self.grid_button.show()
        self.scroll.verticalScrollBar().setValue(0)

    def _restore_grid(self) -> None:
        if self.expanded_index is None:
            return
        self._apply_filters()

    def _make_chart_card(
        self,
        index: int,
        result: ComparisonResult,
        time_limits: tuple[float, float],
        mass_maximum: float,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("comparisonCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 12)
        card_layout.setSpacing(5)
        full_title = simulation_title(result.path)
        oil_name, separator, details = full_title.partition(" · ")
        title = QLabel(oil_name)
        title.setObjectName("comparisonChartTitle")
        title.setToolTip(full_title)
        card_layout.addWidget(title)
        if separator:
            metadata = QLabel(details)
            metadata.setObjectName("comparisonChartMetadata")
            metadata.setToolTip(full_title)
            metadata.setWordWrap(True)
            card_layout.addWidget(metadata)
        chart_actions = QHBoxLayout()
        chart_actions.addStretch()
        zoom_button = QPushButton("Ampliar")
        zoom_button.setObjectName("comparisonChartZoom")
        zoom_button.setToolTip("Ampliar este gráfico ou voltar à grade")
        zoom_button.clicked.connect(lambda _checked=False: self._toggle_chart_zoom(index))
        chart_actions.addWidget(zoom_button)
        self.chart_buttons.append(zoom_button)
        card_layout.addLayout(chart_actions)
        canvas = ComparisonCanvas(result, time_limits, mass_maximum)
        canvas.setMinimumWidth(COMPARISON_GRID_PLOT_WIDTH)
        canvas.setFixedHeight(COMPARISON_GRID_PLOT_HEIGHT)
        canvas.setMaximumWidth(COMPARISON_GRID_PLOT_WIDTH)
        card.setMinimumWidth(COMPARISON_GRID_PLOT_WIDTH + 24)
        card.setMaximumWidth(COMPARISON_GRID_PLOT_WIDTH + 24)
        canvas.zoom_requested.connect(lambda: self._toggle_chart_zoom(index))
        self.canvases.append(canvas)
        card_layout.addWidget(canvas, stretch=1)
        return card
