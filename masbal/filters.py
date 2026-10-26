"""Filtros reutilizáveis de simulação para qualquer aba de resultados."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
)

from .data import SimulationMetadata, UNKNOWN, simulation_metadata


class MultiSelectFacet(QPushButton):
    """Botão-menu que aceita várias opções da mesma categoria."""

    changed = Signal()

    def __init__(self, title: str) -> None:
        super().__init__()
        self.title = title
        self.selected_values: set[str] = set()
        self.option_labels: dict[str, str] = {}
        self._actions = {}
        self.setObjectName("filterFacet")
        self.setMinimumHeight(36)
        self.setMenu(QMenu(self))
        self._update_caption()

    def set_options(self, options: dict[str, str]) -> None:
        """Atualiza opções, preservando escolhas que ainda existem."""
        self.option_labels = options
        self.selected_values.intersection_update(options)
        menu = self.menu()
        menu.clear()
        reset_action = menu.addAction("Todas as opções")
        reset_action.triggered.connect(self.clear_selection)
        menu.addSeparator()
        self._actions = {}
        for value, label in sorted(options.items(), key=lambda pair: pair[1].casefold()):
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(value in self.selected_values)
            action.triggered.connect(
                lambda checked, selected=value: self._toggle(selected, checked)
            )
            self._actions[value] = action
        self._update_caption()

    def _toggle(self, value: str, checked: bool) -> None:
        if checked:
            self.selected_values.add(value)
        else:
            self.selected_values.discard(value)
        self._update_caption()
        self.changed.emit()

    def clear_selection(self) -> None:
        if not self.selected_values:
            return
        self.selected_values.clear()
        for action in self._actions.values():
            action.blockSignals(True)
            action.setChecked(False)
            action.blockSignals(False)
        self._update_caption()
        self.changed.emit()

    def accepts(self, value: str) -> bool:
        return not self.selected_values or value in self.selected_values

    def _update_caption(self) -> None:
        if not self.selected_values:
            selected = "Todos"
        elif len(self.selected_values) == 1:
            value = next(iter(self.selected_values))
            selected = self.option_labels.get(value, value)
        else:
            selected = f"{len(self.selected_values)} opções"
        self.setText(f"{self.title}: {selected}")
        self.setToolTip(
            f"{self.title}: "
            + (", ".join(self.option_labels.get(v, v) for v in sorted(self.selected_values))
               if self.selected_values else "todas as opções")
        )


class SimulationFilterBar(QFrame):
    """Template de filtros por óleo, tratamento, semestre e critério.

    Sem opções marcadas em uma categoria, todas passam. Dentro de uma
    categoria as escolhas são combinadas com OU; entre categorias, com E.
    """

    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("simulationFilterBar")
        self._metadata: dict[Path, SimulationMetadata] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        heading = QHBoxLayout()
        title = QLabel("FILTRAR SIMULAÇÕES")
        title.setObjectName("filterTitle")
        heading.addWidget(title)
        heading.addStretch()
        reset = QPushButton("Limpar filtros")
        reset.setObjectName("filterReset")
        reset.clicked.connect(self.clear_filters)
        heading.addWidget(reset)
        layout.addLayout(heading)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        self.oil = MultiSelectFacet("Óleo")
        self.group = MultiSelectFacet("Tipo")
        self.detail = MultiSelectFacet("Tratamento")
        self.semester = MultiSelectFacet("Semestre")
        self.criterion = MultiSelectFacet("Critério")
        facets = (self.oil, self.group, self.detail, self.semester, self.criterion)
        for index, facet in enumerate(facets):
            row, column = divmod(index, 3)
            grid.addWidget(facet, row, column)
            facet.changed.connect(self.changed.emit)
        self.search = QLineEdit()
        self.search.setObjectName("filterSearch")
        self.search.setPlaceholderText("Buscar pelo nome ou arquivo…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self.changed.emit())
        grid.addWidget(self.search, 1, 2)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        layout.addLayout(grid)

    def set_paths(self, paths: list[Path]) -> None:
        """Lê apenas nomes de arquivo, sem carregar as tabelas MASBAL."""
        self._metadata = {path: simulation_metadata(path) for path in paths}
        values = tuple(self._metadata.values())
        self.oil.set_options({item.oil: item.oil for item in values})
        self.group.set_options({item.treatment_group: item.treatment_group for item in values})
        self.detail.set_options({item.treatment_detail: item.treatment_detail for item in values})
        self.semester.set_options({
            item.semester: f"{item.semester}º semestre" if item.semester in {"1", "2"} else UNKNOWN
            for item in values
        })
        self.criterion.set_options({
            item.criterion: "ASHORE (AS)" if item.criterion == "AS" else "MM" if item.criterion == "MM" else UNKNOWN
            for item in values
        })
        self.changed.emit()

    def clear_filters(self) -> None:
        self.blockSignals(True)
        for facet in (self.oil, self.group, self.detail, self.semester, self.criterion):
            facet.clear_selection()
        self.search.clear()
        self.blockSignals(False)
        self.changed.emit()

    def matches(self, path: Path) -> bool:
        item = self._metadata.get(path)
        if item is None:
            item = simulation_metadata(path)
            self._metadata[path] = item
        criteria = (
            (self.oil, item.oil),
            (self.group, item.treatment_group),
            (self.detail, item.treatment_detail),
            (self.semester, item.semester),
            (self.criterion, item.criterion),
        )
        if not all(facet.accepts(value) for facet, value in criteria):
            return False
        query = self.search.text().strip().casefold()
        return not query or query in item.title.casefold() or query in str(path).casefold()

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        return [path for path in paths if self.matches(path)]
