"""Painel comparativo dos indicadores de chegada derivados do MASBAL."""

from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .config import FONT_BASE, LABELS, SERIES_COLORS
from .data import ComparisonResult, format_br, simulation_title
from .plot_style import apply_axes_style
from .typography import configure_matplotlib_typography


def _arrival_hours(value: float | None, unit: str) -> float | None:
    """Converte um tempo de chegada do MASBAL para horas."""
    if value is None:
        return None

    normalized = unit.casefold().strip()
    if normalized in {"dia", "dias", "day", "days", "d"}:
        return float(value) * 24.0
    if normalized in {"hora", "horas", "hour", "hours", "h"}:
        return float(value)

    raise ValueError(f"Unidade de tempo não suportada na comparação: {unit!r}")


class ArrivalComparisonPanel(QWidget):
    """Mostra tempos de chegada e uma tabela para os cenários filtrados."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        configure_matplotlib_typography()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(12)

        description = QLabel(
            "Tempos correspondentes ao primeiro registro de massa positiva no MASBAL. "
            "A massa acumulada de chegada à costa ainda não pode ser determinada "
            "com segurança a partir dos estoques disponíveis."
        )
        description.setObjectName("comparisonInstruction")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor="white")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.canvas)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("arrivalComparisonTable")
        self.table.setHorizontalHeaderLabels([
            "Nº", "Cenário", "Superfície (h)", "Costa (h)",
            "Massa acumulada na costa",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)


    def set_results(self, results: list[ComparisonResult]) -> None:
        """Atualiza gráfico e tabela usando apenas os cenários visíveis."""

        self.table.clearContents()
        self.table.setRowCount(len(results))

        surface_hours: list[float] = []
        coast_hours: list[float] = []

        # ---------------------------------------------------------
        # 1. Preenchimento dos indicadores e da tabela
        # ---------------------------------------------------------
        for row, result in enumerate(results):
            metrics = result.arrival_times

            if metrics is None:
                surface = coast = None
                surface_text = coast_text = "Não calculado"
            else:
                surface = _arrival_hours(metrics.surface_time, result.time_unit
                )
                coast = _arrival_hours(metrics.coast_time, result.time_unit
                )

                surface_text = ("Não registrado"if surface is None else format_br(surface, 2)
                )
                coast_text = ("Não registrado" if coast is None else format_br(coast, 2)
                )

            surface_hours.append(np.nan if surface is None else surface
            )
            coast_hours.append(np.nan if coast is None else coast
            )

            columns = (f"{row + 1:02d}",simulation_title(result.path),surface_text,coast_text,"Não determinada",
            )

            for column, value in enumerate(columns):
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value)),
                )

        # ---------------------------------------------------------
        # 2. Dimensionamento dos componentes
        # ---------------------------------------------------------
        self.table.setFixedHeight(
            min(800, 65 + 31 * len(results))
        )

        self.canvas.setFixedHeight(
            max(340, 110 + 35 * len(results))
        )

        # ---------------------------------------------------------
        # 3. Construção do gráfico comparativo
        # ---------------------------------------------------------
        self.figure.clear()
        axis = self.figure.add_subplot(111)

        if not results:
            axis.set_axis_off()
            axis.text(
                0.5,
                0.5,
                "Nenhum cenário corresponde aos filtros.",
                ha="center",
                va="center",
                transform=axis.transAxes,
            )
        else:
            positions = np.arange(len(results))

            # Tempo de chegada à superfície
            axis.barh(
                positions - 0.19,
                surface_hours,
                height=0.36,
                color=SERIES_COLORS[LABELS["surface"]],
                label="Chegada à superfície",
            )

            # Tempo de chegada à costa
            axis.barh(
                positions + 0.19,
                coast_hours,
                height=0.36,
                color=SERIES_COLORS[LABELS["stranded"]],
                label="Chegada à costa",
            )

            axis.set_yticks(
                positions,
                [f"{i + 1:02d}" for i in positions],
            )

            axis.invert_yaxis()

            axis.set_xlabel(
                "Tempo desde o início da simulação (h)"
            )
            axis.set_ylabel(
                "Cenário (número na tabela)"
            )
            axis.set_title(
                "Primeira chegada registrada",
                loc="left",
                pad=16,
            )

            axis.set_xlim(left=0)
            axis.legend(loc="lower right")

            apply_axes_style(
                axis,
                tick_size=FONT_BASE,
                grid_axis="x",
            )

        # ---------------------------------------------------------
        # 4. Layout e atualização do canvas
        # ---------------------------------------------------------
        self.figure.subplots_adjust(
            left=0.10,
            right=0.97,
            top=0.89,
            bottom=0.13,
        )

        self.canvas.draw_idle()
