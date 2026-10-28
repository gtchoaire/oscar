"""Tela de comparação da distribuição acumulada."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget, QFileDialog, QMessageBox,
    QTabBar, QToolButton, QComboBox, QMenu)
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
        self.interface_zoom = 0
        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)
        self.expanded_index: int | None = None
        self.plot_mode = "accumulated"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        header = QVBoxLayout()
        header.setSpacing(4)
        header_top = QHBoxLayout()
        title = QLabel("Comparação de cenários")
        title.setObjectName("comparisonTitle")
        self.title_label = title
        header_top.addWidget(title, stretch=1)

        count = QLabel(f"{len(results)} resultados")
        count.setObjectName("comparisonCount")
        self.count_label = count
        header_top.addWidget(count)
        header.addLayout(header_top)

        subtitle = QLabel(
            "Compare os resultados entre diferentes cenários."
        )
        subtitle.setObjectName("startHelp")
        subtitle.setWordWrap(True)
        self.subtitle_label = subtitle
        header.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.addStretch()
        export_button = QPushButton("Exportar comparação")
        export_button.setToolTip("Exportar os cenários filtrados em PNG 300 dpi, PDF, SVG ou EPS")
        export_button.clicked.connect(self._export_comparison)
        self.export_button = export_button
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

        # As abas alternam somente os desenhos; controles e cartões são os mesmos.
        self.plot_tabs = QTabBar()
        self.plot_tabs.setObjectName("comparisonTabs")
        self.plot_tabs.addTab("Distribuição acumulada")
        self.plot_tabs.addTab("Evolução temporal")
        self.plot_tabs.setExpanding(False)
        layout.addWidget(self.plot_tabs)

        temporal_controls = QFrame()
        temporal_controls.setObjectName("comparisonTemporalControls")
        temporal_row = QHBoxLayout(temporal_controls)
        temporal_row.setContentsMargins(0, 0, 0, 0)
        temporal_row.setSpacing(10)
        series_button = QToolButton()
        series_button.setProperty("role", "compact")
        series_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.temporal_series_button = series_button
        series_menu = QMenu(series_button)
        all_action = series_menu.addAction("Todas")
        all_action.triggered.connect(lambda: self._set_all_temporal_series(True))
        none_action = series_menu.addAction("Nenhuma")
        none_action.triggered.connect(lambda: self._set_all_temporal_series(False))
        series_menu.addSeparator()
        self.temporal_series_actions = {}
        present = {label for result in results for label in result.labels}
        ordered = [item["label"] for item in SERIES_CONFIG if item["label"] in present]
        ordered += sorted(present.difference(ordered))
        for label in ordered:
            action = series_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(self._refresh_temporal_plots)
            self.temporal_series_actions[label] = action
        series_button.setMenu(series_menu)
        temporal_row.addWidget(series_button)
        temporal_row.addWidget(QLabel("Escala:"))
        scale_combo = QComboBox()
        scale_combo.addItems(["Linear", "Logarítmica"])
        scale_combo.currentIndexChanged.connect(self._refresh_temporal_plots)
        self.temporal_scale_combo = scale_combo
        temporal_row.addWidget(scale_combo)
        temporal_row.addStretch()
        temporal_controls.hide()
        self.temporal_controls = temporal_controls
        layout.addWidget(temporal_controls)
        self._update_temporal_series_label()

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
        self.legend_panel = legend
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
        self.instruction_label = instruction

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
        self.chart_grid = chart_grid
        self.chart_cards: list[QFrame] = []
        self.chart_buttons: list[QPushButton] = []
        self.canvases: list[ComparisonCanvas] = []
        for index, result in enumerate(results):
            card = self._make_chart_card(index, result, (time_min, time_max), mass_maximum)
            self.chart_cards.append(card)

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
        content_layout.addStretch()
        scroll.setWidget(content)
        self.scroll = scroll
        layout.addWidget(scroll, stretch=1)
        self.filters.changed.connect(self._apply_filters)
        self.filters.set_paths([result.path for result in results])
        self.plot_tabs.currentChanged.connect(self._switch_plot_mode)
        QTimer.singleShot(0, lambda: self._change_interface_zoom(5)
)

    def _fit_expanded_chart(self) -> None:
        """Expande o cartão selecionado até os limites da área disponível."""

        if self.expanded_index is None:
            return

        index = self.expanded_index
        viewport = self.scroll.viewport()

        card_width = max(240, viewport.width() - 52)
        canvas_width = card_width - 32
        canvas_height = max(220, viewport.height() - 115)

        card = self.chart_cards[index]
        canvas = self.canvases[index]

        card.setFixedWidth(card_width)
        canvas.setFixedSize(canvas_width, canvas_height)

    def _fit_chart_grid(self) -> None:
        """Ajusta os cartões à largura disponível, preservando o mosaico."""

        if self.expanded_index is not None:
            return

        visible = [i for i, result in enumerate(self.results) if self.filters.matches(result.path)]

        if not visible:
            return

        # Largura efetivamente disponível dentro da área rolável.
        available = max(220, self.scroll.viewport().width() - 24)
        spacing = self.chart_grid.horizontalSpacing()

        # Acompanha o Ctrl + Scroll já implementado.
        zoom = float(np.clip(1.0 + 0.07 * self.interface_zoom, 0.70, 1.30))

        preferred_width = round(COMPARISON_GRID_PLOT_WIDTH * zoom)
        minimum_width = max(250, round(320 * zoom))

        # Até quatro colunas, desde que haja espaço suficiente.
        columns = min(COMPARISON_GRID_COLUMNS, len(visible), max(1, (available + spacing) // (minimum_width + 32 + spacing)),)

        # Limita os cartões à largura real da janela.
        plot_width = max(180,min(preferred_width, (available - spacing * (columns - 1)) // columns - 32,),)

        # Mantém a proporção original do canvas.
        plot_height = round(COMPARISON_GRID_PLOT_HEIGHT * plot_width / COMPARISON_GRID_PLOT_WIDTH)

        for index in visible:
            canvas = self.canvases[index]
            card = self.chart_cards[index]

            canvas.setFixedSize(plot_width, plot_height)
            card.setFixedWidth(plot_width + 32)

        # Reorganiza os cartões apenas se suas posições mudaram.
        needs_layout = False

        for position, index in enumerate(visible):
            layout_index = self.chart_grid.indexOf(self.chart_cards[index])
            expected = (position // columns, position % columns)

            if (layout_index < 0 or self.chart_grid.getItemPosition(layout_index)[:2] != expected):
                needs_layout = True
                break

        if needs_layout:
            for index in visible:
                self.chart_grid.removeWidget(self.chart_cards[index])

            for position, index in enumerate(visible):
                self.chart_grid.addWidget(self.chart_cards[index], position // columns, position % columns,)

    def eventFilter(self, watched, event):
        if (event.type() == QEvent.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and isinstance(watched, QWidget) and (watched is self or self.isAncestorOf(watched))):
            delta = event.angleDelta().y()

            if delta:
                self._change_interface_zoom(1 if delta > 0 else -1)

            event.accept()
            return True

        return super().eventFilter(watched, event)


    def _change_interface_zoom(self, step: int) -> None:
        new_zoom = int(np.clip(self.interface_zoom + step, -5, 5))

        if new_zoom == self.interface_zoom:
            return

        self.interface_zoom = new_zoom

        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(scaled_app_style(self.interface_zoom)) 
        QTimer.singleShot(0, self._fit_expanded_chart if self.expanded_index is not None else self._fit_chart_grid) 

    def _switch_plot_mode(self, index: int) -> None:
        """Mantém a grade existente e troca apenas o conteúdo dos eixos."""
        if self.expanded_index is not None:
            self._restore_grid()
        self.plot_mode = "temporal" if index == 1 else "accumulated"
        self.title_label.setText(
            "Evolução temporal" if index == 1 else "Distribuição acumulada"
        )
        self.subtitle_label.setText(
            "Compare a evolução temporal completa até o último passo de cada cenário."
            if index == 1 else
            "Compare os cenários carregados com a mesma escala de tempo e massa. "
            "Para incluir outros, volte aos arquivos."
        )
        self.temporal_controls.setVisible(index == 1)
        # Evita exportar a distribuição acumulada com o nome de evolução temporal.
        self.export_button.setEnabled(True)
        self.export_button.setToolTip(
            "Exportar os cenários filtrados em PNG 300 dpi, PDF, SVG ou EPS"
        )
        self._refresh_temporal_plots()

    def _set_all_temporal_series(self, checked: bool) -> None:
        for action in self.temporal_series_actions.values():
            action.blockSignals(True)
            action.setChecked(checked)
            action.blockSignals(False)
        self._refresh_temporal_plots()

    def _update_temporal_series_label(self) -> None:
        count = sum(action.isChecked() for action in self.temporal_series_actions.values())
        self.temporal_series_button.setText(f"Séries ({count})")

    def _refresh_temporal_plots(self, *_args) -> None:
        """Aplica seleção de categorias e a mesma escala logarítmica aos cartões."""
        self._update_temporal_series_label()
        selected = frozenset(label for label, action in self.temporal_series_actions.items()
                             if action.isChecked())
        log_scale = self.temporal_scale_combo.currentIndex() == 1
        positive_minimum = None
        if self.plot_mode == "temporal" and log_scale and selected:
            for result in self.results:
                if not self.filters.matches(result.path):
                    continue
                columns = [i for i, label in enumerate(result.labels) if label in selected]
                if not columns:
                    continue
                values = np.asarray(result.values)
                chosen = np.clip(values[:, columns], 0, None)
                total = np.clip(values, 0, None).sum(axis=1)
                positive = np.concatenate((chosen[chosen > 0], total[total > 0]))
                if positive.size:
                    minimum = float(np.min(positive))
                    positive_minimum = (minimum if positive_minimum is None
                                        else min(positive_minimum, minimum))
        for canvas in self.canvases:
            canvas.set_presentation(self.plot_mode, selected, log_scale, positive_minimum)

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
            self, "Exportar comparação", str(default),
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
            written = save_comparison_report(visible_results, target, plot_mode = self.plot_mode, 
            selected_labels = (frozenset(label for label, action in self.temporal_series_actions.items() if action.isChecked()) if self.plot_mode == "temporal" else None) 
            if self.plot_mode == "temporal" else None, log_scale = (self.temporal_scale_combo.currentIndex() == 1 if self.plot_mode == "temporal" else False))
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
        self._refresh_temporal_plots()
        QTimer.singleShot(0, self._fit_chart_grid)

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
        if hasattr(self, "scroll"):
            QTimer.singleShot(0, self._fit_expanded_chart if self.expanded_index is not None else self._fit_chart_grid)

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
            effective_zoom = int(np.clip(self.interface_zoom + adjustment, -5, +5))
            application.setStyleSheet(scaled_app_style(effective_zoom))
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
        self.chart_grid.addWidget(
            selected, 0, 0, 1, COMPARISON_GRID_COLUMNS
        )

        selected.show()

        # Libera espaço para a visualização ampliada.
        self.filters.hide()
        self.legend_panel.hide()
        self.instruction_label.hide()
        self.plot_tabs.hide()
        self.temporal_controls.hide()

        self.chart_buttons[index].setText("Reduzir")
        self.grid_button.show()

        self.scroll.verticalScrollBar().setValue(0)

        QTimer.singleShot(0, self._fit_expanded_chart)

    def _restore_grid(self) -> None:
        if self.expanded_index is None:
            return

        self.expanded_index = None

        self.filters.show()
        self.legend_panel.show()
        self.instruction_label.show()
        self.plot_tabs.show()

        self.temporal_controls.setVisible(
            self.plot_mode == "temporal"
        )

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
