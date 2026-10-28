"""Tela individual, menu lateral, player e ações do painel."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QSize, Qt, QTimer, Signal, QEvent
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMenu, QMessageBox
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QFileDialog, QFrame,
    QDialog, QGroupBox, QHBoxLayout, QLabel, QMainWindow, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QSlider, QSplitter, QStyle, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from .charts import MassBalanceCanvas, SeriesLabel
from .config import (EXPORT_DPI, EXPORT_FIGURE_SIZE, EXPORT_RENDER_DPI, FONT_PERCENT_STEP, LABELS, PAGE_MARGINS, PAGE_MINIMUM_SIZE,
    SIDEBAR_WIDTH_RANGE, SPLITTER_INITIAL_SIZES, WINDOW_MINIMUM_SIZE, WINDOW_SIZE)
from .data import format_br, load_table, simulation_title
from .export import save_report_figure
from .series_info import series_help_html
from .theme import scaled_app_style

class MassBalanceWindow(QMainWindow):
    """Janela principal responsiva do painel."""

    closed = Signal()

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.interface_zoom = 5
        data, names, time_name, time_unit, mass_unit = load_table(path)
        self.path = path
        self.time = data[:, 0]
        # Reordena as colunas pela ordem definida em LABELS. Chaves que não
        # estiverem no dicionário permanecem no fim, na ordem original do arquivo.
        configured_order = {name: index for index, name in enumerate(LABELS)}
        column_order = sorted(
            range(len(names)),
            key=lambda index: (
                configured_order.get(names[index].lower(), len(configured_order)),
                index,
            ),
        )
        ordered_names = [names[index] for index in column_order]
        self.values = data[:, 1:][:, column_order]
        self.labels = [LABELS.get(name.lower(), name) for name in ordered_names]
        self.time_name = "Tempo" if time_name.lower() == "time" else time_name.capitalize()
        self.time_unit = "dias" if time_unit.lower() in {"day", "days"} else time_unit
        self.mass_unit = mass_unit

        self.setWindowTitle("CANNES — Balanço de Massa")
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*WINDOW_MINIMUM_SIZE)
        self.timer = QTimer(self)
        self.timer.setInterval(90)
        self.timer.timeout.connect(self._animation_tick)

        self.canvas = MassBalanceCanvas(
            self.time, self.values, self.labels, self.time_name, self.time_unit, self.mass_unit
        )
        self._build_interface()
        self._create_shortcuts()
        self._update_time_display(len(self.time) - 1)
        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)

        self._apply_interface_font_size(0)

    def _build_interface(self) -> None:
        shell = QWidget()
        shell.setObjectName("appShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        root = QWidget()
        root.setObjectName("appRoot")
        # Mantém uma área segura para os quatro gráficos. Em janelas menores,
        # aparecem barras de rolagem em vez de um painel invadir o outro.
        root.setMinimumSize(*PAGE_MINIMUM_SIZE)
        page_scroll = QScrollArea()
        page_scroll.setObjectName("pageScroll")
        page_scroll.setWidgetResizable(True)
        page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        page_scroll.setWidget(root)
        shell_layout.addWidget(page_scroll, stretch=1)
        self.setCentralWidget(shell)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(*PAGE_MARGINS)
        root_layout.setSpacing(14)

        root_layout.addWidget(self._build_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_graph_area())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes(list(SPLITTER_INITIAL_SIZES))
        root_layout.addWidget(splitter, stretch=1)

        root_layout.addWidget(self._build_player())

    def _create_shortcuts(self) -> None:
        """Atalhos de apresentação e navegação do painel."""
        shortcut_specs = (
            ("Space", self._toggle_playback),
            ("Left", self._step_back),
            ("Right", self._step_forward),
            ("Home", self._go_start),
            ("End", self._go_end),
            ("Ctrl+S", self._save_dialog),
            ("Escape", self.canvas.restore_grid),
        )
        self.shortcuts: list[QShortcut] = []
        for key, callback in shortcut_specs:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.Type.Wheel
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and isinstance(watched, QWidget)
            and (watched is self or self.isAncestorOf(watched))
        ):
            delta = event.angleDelta().y()

            if delta:
                self._change_interface_zoom(1 if delta > 0 else -1)

            event.accept()
            return True

        return super().eventFilter(watched, event)


    def _change_interface_zoom(self, step: int) -> None:
        self.interface_zoom = int(
            np.clip(self.interface_zoom + step, -5, 5)
        )

        self._apply_interface_font_size(
            self.canvas._font_adjustment
        )

    # -------------------------------------------------------------------------
    # SETOR A — CABEÇALHO: título, tempo atual e retorno do gráfico ampliado
    # -------------------------------------------------------------------------
    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("headerCard")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 4, 0, 12)
        layout.setSpacing(16)

        identity = QVBoxLayout()
        identity.setSpacing(2)
        eyebrow = QLabel("ANÁLISE  /  BALANÇO DE MASSA")
        eyebrow.setObjectName("eyebrow")
        identity.addWidget(eyebrow)

        title = QLabel("Balanço de massa")
        title.setObjectName("mainTitle")
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        identity.addWidget(title)

        description = QLabel("Explore a evolução, a distribuição e a composição das massas modeladas.")
        description.setObjectName("subtitle")
        identity.addWidget(description)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        file_chip = QLabel(simulation_title(self.path))
        file_chip.setObjectName("fileChip")
        file_chip.setToolTip(str(self.path))
        file_row.addWidget(file_chip)
        summary = QLabel(f"{len(self.labels)} séries  •  {len(self.time)} passos")
        summary.setObjectName("subtitle")
        file_row.addWidget(summary)
        file_row.addStretch()
        identity.addLayout(file_row)
        layout.addLayout(identity, stretch=1)

        time_card = QFrame()
        time_card.setObjectName("timeCard")
        time_box = QVBoxLayout(time_card)
        time_box.setContentsMargins(16, 8, 16, 8)
        time_box.setSpacing(0)
        time_caption = QLabel("TEMPO VISUALIZADO")
        time_caption.setObjectName("timeCaption")
        time_caption.setAlignment(Qt.AlignmentFlag.AlignRight)
        time_box.addWidget(time_caption)
        self.time_label = QLabel()
        self.time_label.setObjectName("timeDisplay")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.step_label = QLabel()
        self.step_label.setObjectName("stepDisplay")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        time_box.addWidget(self.time_label)
        time_box.addWidget(self.step_label)
        layout.addWidget(time_card)

        self.back_button = QPushButton("Voltar ao mosaico")
        self.back_button.setProperty("role", "ghost")
        self.back_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        )
        self.back_button.setVisible(False)
        self.back_button.clicked.connect(self.canvas.restore_grid)
        layout.addWidget(self.back_button)
        self.canvas.expanded_changed.connect(self.back_button.setVisible)
        self.canvas.expanded_changed.connect(self._update_canvas_size)
        return header

    # -------------------------------------------------------------------------
    # SETOR B — MENU LATERAL CANNES: contexto, séries, escala, fontes e ações
    # -------------------------------------------------------------------------
    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        self.sidebar = sidebar
        sidebar.setObjectName("cannesSidebar")
        sidebar.setMinimumWidth(SIDEBAR_WIDTH_RANGE[0])
        sidebar.setMaximumWidth(SIDEBAR_WIDTH_RANGE[1])
        sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 16)
        layout.setSpacing(10)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        mark = QLabel("C")
        mark.setObjectName("brandMark")
        mark.setFixedSize(34, 34)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.addWidget(mark)
        brand_name = QLabel("CANNES")
        brand_name.setObjectName("brandName")
        brand.addWidget(brand_name)
        brand.addStretch()
        layout.addLayout(brand)
        brand_subtitle = QLabel("PÓS-PROCESSAMENTO")
        brand_subtitle.setObjectName("sideMuted")
        layout.addWidget(brand_subtitle)
        layout.addSpacing(12)

        section = QLabel("RESULTADOS DA SIMULAÇÃO")
        section.setObjectName("sideSection")
        layout.addWidget(section)
        current = QLabel("▥   Balanço de massa")
        current.setObjectName("sideCurrent")
        current.setMinimumHeight(42)
        current.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(current)
        layout.addSpacing(8)

        sidebar_tabs = QTabWidget()
        sidebar_tabs.setObjectName("sidebarTabs")
        series_page = QWidget()
        series_page.setObjectName("sidebarTabPage")
        series_layout = QVBoxLayout(series_page)
        series_layout.setContentsMargins(4, 12, 4, 2)
        series_layout.setSpacing(10)
        self._add_series_selector(series_layout)
        sidebar_tabs.addTab(series_page, "Séries")

        settings_page = QWidget()
        settings_page.setObjectName("sidebarTabPage")
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(4, 12, 4, 2)
        settings_layout.setSpacing(10)
        settings_layout.addWidget(self._build_scale_controls())
        settings_layout.addWidget(self._build_font_controls())

        self.reset_button = QPushButton("Redefinir painel")
        self.reset_button.setProperty("role", "ghost")
        self.reset_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.reset_button.setToolTip(
            "Volta ao tempo zero, reativa todas as séries e retorna à escala linear."
        )
        self.reset_button.clicked.connect(self._reset_panel)
        settings_layout.addWidget(self.reset_button)
        settings_layout.addStretch()
        sidebar_tabs.addTab(settings_page, "Ajustes")
        layout.addWidget(sidebar_tabs, stretch=1)

        self.new_file_button = QPushButton("Escolher outro arquivo")
        self.new_file_button.setProperty("role", "ghost")
        self.new_file_button.setVisible(False)
        layout.addWidget(self.new_file_button)

        save_button = QPushButton("Salvar imagem")
        save_button.setProperty("role", "primary")
        save_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        )
        save_menu = QMenu(save_button)
        save_menu.addAction(
            "Painel para relatório (PNG 300 dpi / EPS)", lambda: self._save_dialog(professional=True)
        )
        save_menu.addAction(
            "Visualização atual (como na tela)", lambda: self._save_dialog(professional=False)
        )
        save_button.setMenu(save_menu)
        layout.addWidget(save_button)
        footer = QLabel("MASBAL  ·  VISUALIZADOR INDEPENDENTE")
        footer.setObjectName("sideFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return sidebar

    def _add_series_selector(self, parent_layout: QVBoxLayout) -> None:
        """Adiciona a lista rolável de séries ao setor lateral."""
        title_row = QHBoxLayout()
        series_title = QLabel("Séries visíveis")
        series_title.setObjectName("sideTitle")
        title_row.addWidget(series_title)
        series_count = QLabel(str(len(self.labels)))
        series_count.setObjectName("sideCount")
        title_row.addWidget(series_count)
        title_row.addStretch()
        help_button = QPushButton("?")
        help_button.setProperty("role", "compact")
        help_button.setFixedWidth(34)
        help_button.setToolTip("Significado e interpretação das 11 categorias MASBAL")
        help_button.setAccessibleName("Consultar categorias MASBAL")
        help_button.clicked.connect(self._show_series_info)
        title_row.addWidget(help_button)
        parent_layout.addLayout(title_row)

        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(8)
        select_all = QPushButton("Todas")
        select_all.setProperty("role", "compact")
        select_all.clicked.connect(lambda: self._set_all_series(True))
        clear_all = QPushButton("Nenhuma")
        clear_all.setProperty("role", "compact")
        clear_all.clicked.connect(lambda: self._set_all_series(False))
        quick_actions.addWidget(select_all)
        quick_actions.addWidget(clear_all)
        quick_actions.addStretch()
        parent_layout.addLayout(quick_actions)

        series_content = QWidget()
        series_content.setObjectName("seriesList")
        series_layout = QVBoxLayout(series_content)
        series_layout.setContentsMargins(0, 4, 0, 4)
        series_layout.setSpacing(2)
        self.series_checks: list[QCheckBox] = []
        for index, label in enumerate(self.labels):
            row = QFrame()
            row.setObjectName("seriesRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(6, 1, 4, 1)
            row_layout.setSpacing(8)
            swatch = QLabel()
            swatch.setFixedSize(10, 10)
            swatch.setStyleSheet(
                f"background: {self.canvas.colors[index]}; border-radius: 5px;"
            )
            checkbox = QCheckBox()
            checkbox.setToolTip(label)
            checkbox.setChecked(True)
            checkbox.toggled.connect(
                lambda checked, column=index: self.canvas.set_selected(column, checked)
            )
            series_label = SeriesLabel(label)
            series_label.setObjectName("seriesLabel")
            series_label.setWordWrap(True)
            series_label.setToolTip(label)
            series_label.setCursor(Qt.CursorShape.PointingHandCursor)
            series_label.clicked.connect(checkbox.toggle)
            row_layout.addWidget(swatch)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(series_label, stretch=1)
            series_layout.addWidget(row)
            self.series_checks.append(checkbox)
        series_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(series_content)
        parent_layout.addWidget(scroll, stretch=1)

    def _show_series_info(self) -> None:
        """Abre documentação interpretativa sem modificar os resultados."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Categorias MASBAL — OSCAR")
        dialog.resize(750, 600)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser(dialog)
        text.setOpenExternalLinks(False)
        text.setHtml(series_help_html())
        layout.addWidget(text)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def _set_all_series(self, checked: bool) -> None:
        """Marca ou desmarca todas as séries com apenas uma redesenha."""
        for checkbox in self.series_checks:
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        self.canvas.selected[:] = checked
        self.canvas.redraw()

    def _build_scale_controls(self) -> QGroupBox:
        """Cria exclusivamente os controles de escala dos gráficos."""
        scale_group = QGroupBox("ESCALA DOS VALORES")
        scale_layout = QHBoxLayout(scale_group)
        scale_layout.setContentsMargins(10, 10, 10, 8)
        scale_layout.setSpacing(12)
        self.linear_radio = QRadioButton("Linear")
        self.log_radio = QRadioButton("Logarítmica")
        self.linear_radio.setChecked(True)
        scale_buttons = QButtonGroup(self)
        scale_buttons.addButton(self.linear_radio)
        scale_buttons.addButton(self.log_radio)
        self.linear_radio.toggled.connect(lambda checked: checked and self.canvas.set_log_scale(False))
        self.log_radio.toggled.connect(lambda checked: checked and self.canvas.set_log_scale(True))
        scale_layout.addWidget(self.linear_radio)
        scale_layout.addWidget(self.log_radio)
        return scale_group

    def _build_font_controls(self) -> QGroupBox:
        """Cria exclusivamente os botões A− e A+ da tipografia."""
        font_group = QGroupBox("TIPOGRAFIA DA INTERFACE")
        font_layout = QHBoxLayout(font_group)
        font_layout.setContentsMargins(10, 10, 10, 8)
        font_layout.setSpacing(8)
        decrease_font = QPushButton("A−")
        decrease_font.setProperty("role", "compact")
        decrease_font.setToolTip("Diminuir todas as fontes da interface")
        decrease_font.clicked.connect(self._decrease_graph_fonts)
        self.font_size_label = QLabel("100%")
        self.font_size_label.setObjectName("timePill")
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        increase_font = QPushButton("A+")
        increase_font.setProperty("role", "compact")
        increase_font.setToolTip("Aumentar todas as fontes da interface")
        increase_font.clicked.connect(self._increase_graph_fonts)
        font_layout.addWidget(decrease_font)
        font_layout.addWidget(self.font_size_label, stretch=1)
        font_layout.addWidget(increase_font)
        return font_group

    # -------------------------------------------------------------------------
    # SETOR C — ÁREA CENTRAL DOS QUATRO GRÁFICOS
    # -------------------------------------------------------------------------
    def _build_graph_area(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("chartCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(4)

        toolbar = QHBoxLayout()
        panel_title = QLabel("PAINEL ANALÍTICO")
        panel_title.setObjectName("sectionEyebrow")
        toolbar.addWidget(panel_title)
        toolbar.addStretch()
        hint = QLabel("Clique em um gráfico para ampliar")
        hint.setObjectName("subtitle")
        toolbar.addWidget(hint)
        layout.addLayout(toolbar)
        chart_scroll = QScrollArea()
        chart_scroll.setObjectName("chartScroll")
        chart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        chart_scroll.setWidgetResizable(True)
        chart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chart_scroll.setWidget(self.canvas)
        layout.addWidget(chart_scroll, stretch=1)
        return frame

    # -------------------------------------------------------------------------
    # SETOR D — REPRODUTOR TEMPORAL E BARRA DE PROGRESSO
    # -------------------------------------------------------------------------
    def _build_player(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("playerCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        self.playback_status = QLabel("●  Pausado")
        self.playback_status.setObjectName("playbackStatus")
        self.playback_status.setProperty("active", False)
        button_layout.addWidget(self.playback_status)
        button_layout.addStretch()
        button_specs = (
            (
                "Início",
                QStyle.StandardPixmap.SP_MediaSkipBackward,
                self._go_start,
                "Ir diretamente ao primeiro passo (Home)",
                "ghost",
            ),
            (
                "Recuar",
                QStyle.StandardPixmap.SP_MediaSeekBackward,
                self._step_back,
                "Recuar um passo (←)",
                "ghost",
            ),
            (
                "Reproduzir",
                QStyle.StandardPixmap.SP_MediaPlay,
                self._play,
                "Iniciar a reprodução (Espaço)",
                "primary",
            ),
            (
                "Pausar",
                QStyle.StandardPixmap.SP_MediaPause,
                self._pause,
                "Pausar a reprodução (Espaço)",
                "ghost",
            ),
            (
                "Avançar",
                QStyle.StandardPixmap.SP_MediaSeekForward,
                self._step_forward,
                "Avançar um passo (→)",
                "ghost",
            ),
            (
                "Fim",
                QStyle.StandardPixmap.SP_MediaSkipForward,
                self._go_end,
                "Ir diretamente ao último passo (End)",
                "ghost",
            ),
        )
        for text, icon, callback, tooltip, role in button_specs:
            button = QPushButton(text)
            button.setProperty("role", role)
            button.setProperty("kind", "transport")
            button.setIcon(self.style().standardIcon(icon))
            button.setIconSize(QSize(18, 18))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            button_layout.addWidget(button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(12)
        progress_label = QLabel("PROGRESSO TEMPORAL")
        progress_label.setObjectName("sectionEyebrow")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, len(self.time) - 1)
        self.slider.setValue(len(self.time) - 1)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(max(1, len(self.time) // 20))
        self.slider.valueChanged.connect(self._update_time_display)
        self.progress_value = QLabel()
        self.progress_value.setObjectName("timePill")
        self.progress_value.setMinimumWidth(130)
        self.progress_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.slider, stretch=1)
        progress_layout.addWidget(self.progress_value)
        layout.addLayout(progress_layout)
        return frame

    def _update_time_display(self, index: int) -> None:
        self.canvas.set_current_index(index)
        time_text = format_br(float(self.time[index]))
        self.time_label.setText(f"{time_text} {self.time_unit}")
        self.step_label.setText(f"PASSO {index + 1} / {len(self.time)}")
        self.progress_value.setText(f"{time_text} {self.time_unit}")

    def _reset_panel(self) -> None:
        self._pause()
        if self.canvas.expanded_index is not None:
            self.canvas.restore_grid()
        for checkbox in self.series_checks:
            checkbox.blockSignals(True)
            checkbox.setChecked(True)
            checkbox.blockSignals(False)
        self.canvas.selected[:] = True
        self.canvas.reset_font_size()
        self._apply_interface_font_size(0)
        self.linear_radio.setChecked(True)
        self.slider.setValue(0)
        self.canvas.redraw()

    def _decrease_graph_fonts(self) -> None:
        adjustment = self.canvas.change_font_size(-1)
        self._apply_interface_font_size(adjustment)

    def _increase_graph_fonts(self) -> None:
        adjustment = self.canvas.change_font_size(1)
        self._apply_interface_font_size(adjustment)

    def _apply_interface_font_size(self, adjustment: int) -> None:
        """Sincroniza menus, navegação e gráficos no mesmo nível de zoom."""
        application = QApplication.instance()
        if application is not None:
            effective_zoom = int(np.clip(self.interface_zoom + adjustment, -5, 5))
            application.setStyleSheet(scaled_app_style(effective_zoom))
        # A+ altera fontes, não as larguras dos setores nem a posição dos gráficos.
        self.sidebar.setMinimumWidth(SIDEBAR_WIDTH_RANGE[0])
        self.sidebar.setMaximumWidth(SIDEBAR_WIDTH_RANGE[1])
        self.font_size_label.setText(f"{100 + adjustment * FONT_PERCENT_STEP}%")
        self._update_canvas_size(self.canvas.expanded_index is not None)

    def _update_canvas_size(self, expanded: bool) -> None:
        """Preserva o mosaico 2×2 com espaço suficiente para fontes ampliadas."""
        if expanded or self.canvas._font_adjustment <= 0:
            minimum_height = 500
        else:
            minimum_height = 750 if self.canvas._font_adjustment == 1 else 860
        self.canvas.setMinimumSize(680, minimum_height)

    def _go_start(self) -> None:
        self._pause()
        self.slider.setValue(0)

    def _go_end(self) -> None:
        self._pause()
        self.slider.setValue(len(self.time) - 1)

    def _step_back(self) -> None:
        self._pause()
        self.slider.setValue(max(0, self.slider.value() - 1))

    def _step_forward(self) -> None:
        self._pause()
        self.slider.setValue(min(len(self.time) - 1, self.slider.value() + 1))

    def _play(self) -> None:
        if self.slider.value() >= len(self.time) - 1:
            self.slider.setValue(0)
        self.timer.start()
        self._set_playback_status(True)

    def _toggle_playback(self) -> None:
        if self.timer.isActive():
            self._pause()
        else:
            self._play()

    def _pause(self) -> None:
        self.timer.stop()
        self._set_playback_status(False)

    def _set_playback_status(self, active: bool) -> None:
        """Atualiza o estado visual do reprodutor temporal."""
        if not hasattr(self, "playback_status"):
            return
        self.playback_status.setText("●  Em reprodução" if active else "●  Pausado")
        self.playback_status.setProperty("active", active)
        self.playback_status.style().unpolish(self.playback_status)
        self.playback_status.style().polish(self.playback_status)

    def _animation_tick(self) -> None:
        next_index = self.slider.value() + 1
        if next_index >= len(self.time):
            self._pause()
            return
        self.slider.setValue(next_index)

    def _save_dialog(self, professional: bool = True) -> None:
        """Escolhe o destino, com relatório padronizado como opção principal."""
        suffix = "_relatorio" if professional else "_painel"
        default = self.path.with_name(f"{self.path.stem}{suffix}.png")
        output, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar painel para relatório" if professional else "Salvar visualização atual",
            str(default),
            "Imagem PNG (*.png);;Documento PDF (*.pdf);;Imagem SVG (*.svg);;Imagem EPS (*.eps)",
        )
        if not output:
            return
        target = Path(output)
        if not target.suffix:
            extension = {
                "Imagem PNG (*.png)": ".png",
                "Documento PDF (*.pdf)": ".pdf",
                "Imagem SVG (*.svg)": ".svg",
                "Imagem EPS (*.eps)": ".eps",
            }.get(selected_filter, ".png")
            target = target.with_suffix(extension)
        try:
            self.save_figure(target, professional=professional)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Falha ao exportar figura", str(error))

    def save_figure(self, output: Path, *, professional: bool = True) -> None:
        """Exporta relatório padronizado ou preserva a exportação antiga da tela."""
        if not professional:
            self.canvas.figure.savefig(
                output, dpi=EXPORT_DPI, bbox_inches="tight", facecolor="white"
            )
            return

        # Um canvas independente impede que o tamanho da janela, zoom de fonte
        # ou ampliação temporária de gráfico afetem a figura para relatório.
        report = MassBalanceCanvas(
            self.canvas.time, self.canvas.values, self.canvas.labels,
            self.canvas.time_name, self.canvas.time_unit, self.canvas.mass_unit,
        )
        try:
            width, height = (
                round(size * EXPORT_RENDER_DPI) for size in EXPORT_FIGURE_SIZE
            )
            report.resize(width, height)
            report._font_scale = 1.0
            report._font_adjustment = 0
            report.selected = self.canvas.selected.copy()
            report.current_index = self.canvas.current_index
            report.log_scale = self.canvas.log_scale
            report.redraw()

            # Identifica a simulação sem depender do cabeçalho da janela Qt.
            report.figure.suptitle(
                simulation_title(self.path), x=0.10, y=0.955,
                ha="left", fontsize=16, fontweight="bold",
            )
            report.figure.text(
                0.50, 0.015,
                f"Tempo visualizado: {format_br(float(self.time[report.current_index]))} "
                f"{self.time_unit}  |  Fonte: OSCAR (MASBAL)",
                ha="center", va="bottom", fontsize=11, color="#526169",
            )
            save_report_figure(report.figure, output)
        finally:
            report.close()

    def closeEvent(self, event) -> None:  # noqa: N802 - nome definido pelo Qt
        self._pause()
        self.closed.emit()
        super().closeEvent(event)
