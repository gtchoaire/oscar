"""Seleção de resultados e troca de páginas na janela principal."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QTabWidget,
    QScrollArea, QVBoxLayout, QWidget)

from .comparison import ComparisonView
from .config import DEFAULT_FILE, WINDOW_MINIMUM_SIZE
from .data import load_comparison_result, simulation_title
from .filters import SimulationFilterBar
from .individual import MassBalanceWindow
from .theme import APP_STYLE

class StartWindow(QMainWindow):
    """Tela inicial para escolher um resultado antes de criar o painel."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CANNES — Visualizador MASBAL")
        self.resize(1020, 720)
        self.setMinimumSize(780, 620)
        self.dashboard: MassBalanceWindow | None = None
        self.comparison: ComparisonView | None = None
        self.comparison_paths: list[Path] = []
        self.last_directory = DEFAULT_FILE.parent if DEFAULT_FILE.parent.is_dir() else Path.cwd()

        root = QWidget()
        root.setObjectName("startRoot")
        self.start_page = root
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(36, 30, 36, 36)
        layout.setSpacing(10)

        eyebrow = QLabel("CANNES  /  PÓS-PROCESSAMENTO  /  MASBAL")
        eyebrow.setObjectName("startEyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("Balanço de massa")
        title.setObjectName("startTitle")
        layout.addWidget(title)
        description = QLabel("Abra um resultado individual ou compare vários balanços de massa.")
        description.setObjectName("startDescription")
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addSpacing(18)

        tabs = QTabWidget()
        tabs.setObjectName("startTabs")
        tabs.addTab(self._single_result_tab(), "Resultado individual")
        tabs.addTab(self._cumulative_distribution_tab(), "Distribuição acumulada")
        layout.addWidget(tabs, stretch=1)

    def _single_result_tab(self) -> QWidget:
        page = QWidget()
        outer = QHBoxLayout(page)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addStretch()
        card = QFrame()
        card.setObjectName("startCard")
        card.setMaximumWidth(700)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(34, 30, 34, 30)
        card_layout.setSpacing(13)
        card_layout.addStretch()

        title = QLabel("Visualizar um resultado")
        title.setObjectName("startCardTitle")
        card_layout.addWidget(title)
        help_text = QLabel(
            "Abra um arquivo .masbal.log, .log ou .txt. "
            "Os gráficos serão gerados assim que você selecionar o arquivo."
        )
        help_text.setObjectName("startHelp")
        help_text.setWordWrap(True)
        card_layout.addWidget(help_text)
        card_layout.addSpacing(12)

        choose_button = QPushButton("Selecionar arquivo MASBAL")
        choose_button.setProperty("role", "primary")
        choose_button.clicked.connect(self._choose_file)
        card_layout.addWidget(choose_button)
        card_layout.addStretch()
        outer.addWidget(card, stretch=1)
        outer.addStretch()
        return page

    def _cumulative_distribution_tab(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(14)
        scroll = QScrollArea()
        scroll.setObjectName("selectionScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        content.setObjectName("selectionContent")
        content.setMinimumHeight(530)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)
        title = QLabel("Comparação de múltiplos resultados")
        title.setObjectName("startCardTitle")
        layout.addWidget(title)
        note = QLabel(
            "Selecione dois ou mais arquivos MASBAL. A distribuição acumulada de cada "
            "resultado será mostrada com as mesmas cores e escalas."
        )
        note.setObjectName("startHelp")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        add_button = QPushButton("Adicionar arquivos")
        add_button.setProperty("role", "primary")
        add_button.clicked.connect(self._add_comparison_files)
        buttons.addWidget(add_button)
        remove_button = QPushButton("Remover selecionados")
        remove_button.clicked.connect(self._remove_comparison_files)
        buttons.addWidget(remove_button)
        clear_button = QPushButton("Limpar lista")
        clear_button.clicked.connect(self._clear_comparison_files)
        buttons.addWidget(clear_button)
        layout.addLayout(buttons)

        self.comparison_filters = SimulationFilterBar()
        self.comparison_filters.setMinimumHeight(154)
        layout.addWidget(self.comparison_filters)

        self.comparison_list = QListWidget()
        self.comparison_list.setObjectName("comparisonList")
        self.comparison_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.comparison_list.setAlternatingRowColors(True)
        self.comparison_list.setMinimumHeight(130)
        layout.addWidget(self.comparison_list, stretch=1)
        self.comparison_count = QLabel("Nenhum arquivo selecionado")
        self.comparison_count.setObjectName("startHelp")
        layout.addWidget(self.comparison_count)
        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)
        compare_button = QPushButton("Comparar distribuição acumulada")
        compare_button.setProperty("role", "primary")
        compare_button.clicked.connect(self._open_comparison)
        self.compare_button = compare_button
        outer.addWidget(compare_button)
        self.comparison_filters.changed.connect(self._refresh_comparison_list)
        self.comparison_filters.set_paths([])
        return page

    def _choose_file(self) -> None:
        selected = self._select_files(multiple=False)
        if selected:
            self.open_file(selected[0])

    def _select_files(self, multiple: bool) -> list[Path]:
        # O diálogo Qt mostra /mnt/c mesmo quando o seletor nativo do sistema
        # não oferece uma forma simples de navegar até as unidades Windows.
        dialog = QFileDialog(self, "Selecionar resultado MASBAL")
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setFileMode(
            QFileDialog.FileMode.ExistingFiles if multiple else QFileDialog.FileMode.ExistingFile
        )
        dialog.setNameFilters(
            ["Resultados MASBAL (*.masbal.log *.log *.txt)", "Todos os arquivos (*)"]
        )
        dialog.setDirectory(str(self.last_directory))
        if dialog.exec():
            return [Path(selected).expanduser().resolve() for selected in dialog.selectedFiles()]
        return []

    def _add_comparison_files(self) -> None:
        for path in self._select_files(multiple=True):
            if path not in self.comparison_paths:
                self.comparison_paths.append(path)
                self.last_directory = path.parent
        self.comparison_filters.set_paths(self.comparison_paths)

    def _remove_comparison_files(self) -> None:
        selected = {
            Path(item.data(Qt.ItemDataRole.UserRole))
            for item in self.comparison_list.selectedItems()
        }
        self.comparison_paths = [path for path in self.comparison_paths if path not in selected]
        self.comparison_filters.set_paths(self.comparison_paths)

    def _clear_comparison_files(self) -> None:
        self.comparison_paths.clear()
        self.comparison_filters.clear_filters()
        self.comparison_filters.set_paths([])

    def _filtered_comparison_paths(self) -> list[Path]:
        return self.comparison_filters.filter_paths(self.comparison_paths)

    def _refresh_comparison_list(self) -> None:
        visible = self._filtered_comparison_paths()
        self.comparison_list.setUpdatesEnabled(False)
        self.comparison_list.clear()
        for path in visible:
            item = QListWidgetItem(simulation_title(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.comparison_list.addItem(item)
        self.comparison_list.setUpdatesEnabled(True)
        count = len(visible)
        total = len(self.comparison_paths)
        self.comparison_count.setText(
            f"{count} de {total} arquivo{'s' if total != 1 else ''} no filtro atual"
            if total else "Nenhum arquivo selecionado"
        )
        self.compare_button.setEnabled(count >= 2)

    def _open_comparison(self) -> None:
        paths = self._filtered_comparison_paths()
        if len(paths) < 2:
            QMessageBox.information(
                self, "Selecione mais arquivos", "O filtro atual precisa conter ao menos dois balanços de massa."
            )
            return
        try:
            results = [load_comparison_result(path) for path in paths]
            time_unit = results[0].time_unit
            mass_unit = results[0].mass_unit
            if any(result.time_unit != time_unit or result.mass_unit != mass_unit for result in results[1:]):
                raise ValueError(
                    "Os arquivos precisam usar as mesmas unidades de tempo e massa "
                    "para compartilhar as escalas dos gráficos."
                )
            comparison = ComparisonView(results)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível comparar", str(error))
            return
        comparison.back_requested.connect(self._show_start_page)
        self.comparison = comparison
        self.start_page = self.takeCentralWidget()
        self.setCentralWidget(comparison)
        self.setWindowTitle("CANNES — Comparação de resultados")
        self.setMinimumSize(900, 650)

    def open_file(self, path: Path) -> None:
        """Substitui o conteúdo da janela atual pelo painel de gráficos."""
        path = path.expanduser().resolve()
        try:
            dashboard = MassBalanceWindow(path)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível abrir o resultado", str(error))
            return
        self.last_directory = path.parent
        self.dashboard = dashboard
        dashboard.new_file_button.setVisible(True)
        dashboard.new_file_button.clicked.connect(self._show_start_page)
        self.start_page = self.takeCentralWidget()
        self.setCentralWidget(dashboard)
        self.setWindowTitle("CANNES — Balanço de Massa")
        self.setMinimumSize(*WINDOW_MINIMUM_SIZE)

    def _show_start_page(self) -> None:
        """Retorna à seleção de arquivo sem criar ou trocar de janela."""
        if self.dashboard is None and self.comparison is None:
            return
        if self.dashboard is not None:
            self.dashboard._pause()
        old_page = self.dashboard or self.comparison
        self.takeCentralWidget()
        self.dashboard = None
        self.comparison = None
        old_page.deleteLater()
        self.setCentralWidget(self.start_page)
        self.setWindowTitle("CANNES — Visualizador MASBAL")
        self.setMinimumSize(780, 620)
        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(APP_STYLE)
