"""Interface PySide6 para visualizar balanços de massa MASBAL.

Uso:
    python3 post.py
    python3 post.py include/outro_arquivo.txt
    python3 post.py arquivo.log --save painel.png --no-show
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    from PySide6.QtCore import QSize, Qt, QTimer, Signal
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
        QCheckBox,
        QFileDialog,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSizePolicy,
        QSlider,
        QSplitter,
        QStyle,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
except ModuleNotFoundError as error:
    if error.name and error.name.startswith("PySide6"):
        raise SystemExit(
            "PySide6 não está instalado. Execute: python3 -m pip install PySide6"
        ) from error
    raise


# =============================================================================
# 1. ARQUIVO PADRÃO
# =============================================================================
DEFAULT_FILE = Path(__file__).resolve().parent / "include" / "Tutorial.masbal.log"


def simulation_title(path: Path) -> str:
    """Transforma o nome do arquivo em um título legível para a simulação.

    Padrão: <óleo>_<semestre 1|2>_<AS|MM>_<45|50|55|tratamento>.
    Arquivos fora desse padrão continuam legíveis, sem a extensão MASBAL.
    """
    stem = re.sub(r"(?i)(?:\.masbal)?\.(?:log|txt)$", "", path.name)
    match = re.fullmatch(r"(.+)_([12])_(AS|MM)_([^_]+)", stem, flags=re.IGNORECASE)
    if match is None:
        return stem.replace("_", " ")

    oil, semester, criterion, treatment = match.groups()
    oil_name = " ".join(part[:1].upper() + part[1:] for part in oil.split("_"))
    criterion_name = "ASHORE" if criterion.upper() == "AS" else "Maximum Mass"
    if treatment in {"45", "50", "55"}:
        treatment_name = f"SSMD {treatment}WJ"
    elif treatment.lower() == "untreated":
        treatment_name = "Sem tratamento"
    else:
        treatment_name = treatment[:1].upper() + treatment[1:]
    return f"{oil_name} · {treatment_name} · {semester}º sem. · {criterion_name}"


# =============================================================================
# 2. SÉRIES — EDITE A ORDEM, OS NOMES E AS CORES SOMENTE NESTA LISTA
# =============================================================================
# A ordem dos itens abaixo controla, ao mesmo tempo:
#   • a lista lateral;
#   • as curvas e áreas dos gráficos superiores;
#   • o eixo Y dos dois gráficos inferiores;
#   • a legenda.
#
# ``axis`` é o texto compacto dos eixos inferiores.
# ``legend`` é o texto compacto da legenda externa.
SERIES_CONFIG = [
    {
        "column": "surface",
        "label": "Óleo na superfície",
        "axis": "Superfície",
        "legend": "Superfície",
        "color": "#0072b2",
    },
    {
        "column": "stranded",
        "label": "Encalhado na costa",
        "axis": "Costa",
        "legend": "Costa",
        "color": "#f0e442",
    },
    {
        "column": "droplet",
        "label": "Gotículas na coluna d'água",
        "axis": "Gotículas",
        "legend": "Gotículas",
        "color": "#009e73",
    },
    {
        "column": "atmos-evap",
        "label": "Evaporado para a atmosfera",
        "axis": "Evaporado",
        "legend": "Evaporado",
        "color": "#e69f00",
    },
    {
        "column": "decayed",
        "label": "Biodegradado",
        "axis": "Biodegradado",
        "legend": "Biodegradado",
        "color": "#d55e00",
    },
    {
        "column": "dissolved",
        "label": "Dissolvido na coluna d'água",
        "axis": "Dissolvido",
        "legend": "Dissolvido",
        "color": "#56b4e9",
    },
    {
        "column": "atmos-gas",
        "label": "Gás na atmosfera",
        "axis": "Gás atmosférico",
        "legend": "Gás atmosférico",
        "color": "#8c564b",
    },
    {
        "column": "gasbubbles",
        "label": "Bolhas de gás na coluna d'água",
        "axis": "Bolhas de gás",
        "legend": "Bolhas de gás",
        "color": "#17becf",
    },
    {
        "column": "sediment",
        "label": "Sedimentado no fundo",
        "axis": "Sedimentado",
        "legend": "Sedimentado",
        "color": "#cc79a7",
    },
    {
        "column": "cleaned",
        "label": "Removido/limpo",
        "axis": "Removido/limpo",
        "legend": "Removido/limpo",
        "color": "#9467bd",
    },
    {
        "column": "outside",
        "label": "Fora do domínio modelado",
        "axis": "Fora do domínio",
        "legend": "Fora do domínio",
        "color": "#999999",
    },
]

# Mapas derivados automaticamente. Não é necessário editar estes três blocos.
LABELS = {item["column"]: item["label"] for item in SERIES_CONFIG}
SERIES_COLORS = {item["label"]: item["color"] for item in SERIES_CONFIG}
LOWER_AXIS_LABELS = {item["label"]: item["axis"] for item in SERIES_CONFIG}
LEGEND_LABELS = {item["label"]: item["legend"] for item in SERIES_CONFIG}
TOTAL_COLOR = "#202124"


# =============================================================================
# 3. FONTES — ESCALA GLOBAL E AJUSTE FINO DO MATPLOTLIB
# =============================================================================
FONT_SMALL = 12
FONT_BASE = 16
FONT_SECTION = 20
FONT_TIME = 28
FONT_TITLE = 36
FONT_STEP = 2
FONT_ADJUSTMENT_MIN = -2  # dois cliques em A−: 80%
FONT_ADJUSTMENT_MAX = 2   # dois cliques em A+: 120%
FONT_PERCENT_STEP = 10


# =============================================================================
# 4. GEOMETRIA DOS SETORES DA TELA
# =============================================================================
# Coordenadas Matplotlib: (esquerda, base, largura, altura), de 0.0 a 1.0.
# As duas linhas compartilham exatamente o início e a largura de cada coluna.
NORMAL_CHART_POSITIONS = (
    (0.1, 0.51, 0.30, 0.29),  # superior esquerdo: evolução temporal
    (0.5, 0.51, 0.30, 0.29),  # superior direito: distribuição acumulada
    (0.1, 0.08, 0.30, 0.29),  # inferior esquerdo: composição atual
    (0.5, 0.08, 0.30, 0.29),  # inferior direito: participação no total
)
COLORBAR_GAP = 0.015
COLORBAR_WIDTH = 0.012
NORMAL_LEGEND_ANCHOR = (0.58, 0.99)
NORMAL_LEGEND_COLUMNS = 4

# Posições usadas ao clicar em um gráfico para ampliá-lo.
EXPANDED_UPPER_POSITION = (0.10, 0.08, 0.80, 0.67)
EXPANDED_COMPOSITION_POSITION = (0.25, 0.10, 0.70, 0.82)
EXPANDED_HEATMAP_POSITION = (0.27, 0.10, 0.57, 0.82)

# Dimensões dos setores Qt da janela.
WINDOW_SIZE = (1600, 980)
WINDOW_MINIMUM_SIZE = (1100, 700)
PAGE_MINIMUM_SIZE = (1080, 720)
PAGE_MARGINS = (22, 16, 22, 18)
NAVIGATION_WIDTH = 146
SIDEBAR_WIDTH_RANGE = (300, 390)
SPLITTER_INITIAL_SIZES = (320, 1080)

# Índices dos gráficos dentro de ``MassBalanceCanvas.axes``.
CHART_TEMPORAL = 0
CHART_ACCUMULATED = 1
CHART_COMPOSITION = 2
CHART_HEATMAP = 3


# =============================================================================
# 5. APARÊNCIA DOS COMPONENTES PYSIDE6
# =============================================================================
PLOT_BACKGROUND = "#fbfdfe"
PLOT_TEXT = "#243843"
PLOT_MUTED = "#617984"
PLOT_GRID = "#dce7eb"
PLOT_SPINE = "#9eb2bc"

APP_STYLE = """
QWidget {
    color: #172b36;
    font-family: "Inter", "Segoe UI", "DejaVu Sans", sans-serif;
    font-size: 16px;
}
QWidget#appRoot, QScrollArea#pageScroll, QScrollArea#pageScroll > QWidget > QWidget {
    background: #edf3f6;
}
QFrame#headerCard, QFrame#sidebarCard, QFrame#chartCard, QFrame#playerCard {
    background: #ffffff;
    border: 1px solid #d5e1e7;
    border-radius: 16px;
}
QLabel#mainTitle {
    color: #102a37;
    font-size: 32px;
    font-weight: 700;
}
QLabel#eyebrow, QLabel#sectionEyebrow {
    color: #527080;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#subtitle {
    color: #667f8c;
    font-size: 14px;
}
QLabel#fileChip, QLabel#timePill {
    color: #315569;
    background: #edf5f8;
    border: 1px solid #d1e2e9;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 13px;
    font-weight: 600;
}
QFrame#timeCard {
    background: #f2f8fa;
    border: 1px solid #cfe1e8;
    border-radius: 12px;
}
QLabel#timeCaption {
    color: #537180;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#timeDisplay {
    font-size: 26px;
    font-weight: 700;
    color: #086788;
}
QLabel#stepDisplay {
    font-size: 13px;
    color: #58717e;
}
QLabel#sidebarTitle, QLabel#panelTitle {
    color: #173744;
    font-size: 20px;
    font-weight: 700;
}
QGroupBox {
    background: #f8fbfc;
    border: 1px solid #dce7ec;
    border-radius: 10px;
    margin-top: 16px;
    padding: 15px 10px 10px 10px;
    color: #365563;
    font-size: 13px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    background: #ffffff;
}
QPushButton {
    min-height: 38px;
    padding: 3px 14px;
    color: #244653;
    background: #f7fafb;
    border: 1px solid #c5d6de;
    border-radius: 9px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover {
    color: #075f7d;
    background: #edf6f9;
    border-color: #72aabd;
}
QPushButton:pressed { background: #dbeef4; }
QPushButton:disabled { color: #94a5ad; background: #f0f3f4; }
QPushButton[role="primary"] {
    color: #ffffff;
    background: #087b9d;
    border-color: #087b9d;
}
QPushButton[role="primary"]:hover {
    background: #066a89;
    border-color: #066a89;
}
QPushButton[role="ghost"] {
    color: #46616e;
    background: transparent;
    border-color: #d2dee4;
}
QPushButton[role="compact"] {
    min-height: 30px;
    padding: 1px 10px;
    border-radius: 7px;
    font-size: 12px;
}
QPushButton[kind="transport"] {
    min-height: 40px;
    min-width: 78px;
}
QCheckBox, QRadioButton {
    spacing: 10px;
    min-height: 30px;
    font-size: 14px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #8ba4b0;
    border-radius: 10px;
    background: #ffffff;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: #0a86a8;
    border: 4px solid #d9f0f5;
}
QFrame#seriesRow {
    background: transparent;
    border: none;
    border-radius: 7px;
}
QFrame#seriesRow:hover { background: #f1f7f9; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    width: 9px;
    background: transparent;
    margin: 2px;
}
QScrollBar::handle:vertical {
    min-height: 30px;
    background: #b7cad3;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #88a8b6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSlider::groove:horizontal {
    height: 8px;
    border-radius: 4px;
    background: #d9e5ea;
}
QSlider::sub-page:horizontal {
    border-radius: 4px;
    background: #0b8daf;
}
QSlider::add-page:horizontal {
    border-radius: 4px;
    background: #d9e5ea;
}
QSlider::handle:horizontal {
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    background: #087b9d;
    border: 3px solid #ffffff;
}
QLabel#playbackStatus {
    color: #687f8a;
    font-size: 13px;
    font-weight: 700;
}
QLabel#playbackStatus[active="true"] { color: #087b68; }
QSplitter::handle { background: transparent; width: 10px; }
QToolTip {
    color: #ffffff;
    background: #243d49;
    border: 1px solid #243d49;
    padding: 6px;
}
"""

# Tema do espaço de trabalho. Mantido em um bloco próprio para facilitar
# ajustes de cor, contraste e densidade sem alterar a lógica dos gráficos.
APP_STYLE += """
QWidget { color: #1c293b; font-family: "Inter", "Segoe UI", "DejaVu Sans", sans-serif; }
QWidget#appShell, QWidget#appRoot, QScrollArea#pageScroll,
QScrollArea#pageScroll > QWidget > QWidget { background: #f2f4f8; }
QFrame#navigationRail { background: #111a2a; border: none; }
QLabel#brandMark {
    color: #ffffff; background: #ef6c1b; border-radius: 6px;
    font-size: 17px; font-weight: 800;
}
QLabel#brandName { color: #ffffff; font-size: 16px; font-weight: 800; }
QLabel#navSection { color: #9eabba; font-size: 12px; font-weight: 700; }
QLabel#navMuted { color: #aab5c3; font-size: 12px; }
QLabel#navFooter { color: #7d8c9e; font-size: 11px; }
QLabel#seriesLabel { color: #26354b; font-size: 14px; }
QLabel#navCurrent {
    color: #ffffff; background: #25334c;
    border-left: 3px solid #ef6c1b; border-radius: 3px;
    padding-left: 12px; font-size: 14px; font-weight: 700;
}
QFrame#headerCard { background: transparent; border: none; border-radius: 0; }
QFrame#sidebarCard, QFrame#chartCard, QFrame#playerCard {
    background: #ffffff; border: 1px solid #e0e5ec; border-radius: 8px;
}
QLabel#mainTitle { color: #172238; font-size: 30px; font-weight: 750; }
QLabel#eyebrow, QLabel#sectionEyebrow {
    color: #536073; font-size: 12px; font-weight: 700;
}
QLabel#subtitle { color: #667386; font-size: 14px; }
QLabel#sidebarTitle, QLabel#panelTitle {
    color: #182338; font-size: 20px; font-weight: 700;
}
QFrame#timeCard {
    background: #ffffff; border: 1px solid #e0e5ec; border-radius: 8px;
}
QLabel#timeCaption { color: #667386; font-size: 12px; }
QLabel#timeDisplay { color: #172238; font-size: 26px; }
QLabel#stepDisplay { color: #68758a; font-size: 13px; }
QLabel#fileChip, QLabel#timePill {
    color: #3b485f; background: #f4f6f9; border: 1px solid #e4e8ee;
    border-radius: 4px; padding: 4px 9px; font-size: 13px;
}
QGroupBox {
    color: #415066; background: #f8f9fb; border: 1px solid #e4e8ee;
    border-radius: 6px; font-size: 13px; font-weight: 700;
}
QGroupBox::title { background: #ffffff; }
QPushButton {
    color: #26354b; background: #f7f8fa; border: 1px solid #dce2e9;
    border-radius: 5px; font-size: 14px; min-height: 34px;
}
QPushButton:hover {
    color: #9b450f; background: #fff3e9; border-color: #edbb99;
}
QPushButton:pressed { background: #fce6d6; }
QPushButton[role="primary"] {
    color: #a34b13; background: #fff0e5; border: 1px solid #efc3a4;
}
QPushButton[role="primary"]:hover {
    color: #8d3c08; background: #ffe4d1; border-color: #e7a36f;
}
QPushButton[role="ghost"] { color: #40506a; background: #ffffff; }
QPushButton[kind="transport"] { min-height: 36px; min-width: 72px; }
QCheckBox, QRadioButton { color: #26354b; font-size: 14px; min-height: 27px; }
QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid #aeb8c6; border-radius: 9px; background: #ffffff;
    width: 17px; height: 17px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: #263b56; border: 4px solid #e1e8f0;
}
QFrame#seriesRow:hover { background: #faf3ee; }
QSplitter::handle { background: #f2f4f8; width: 12px; }
QSlider::groove:horizontal, QSlider::add-page:horizontal { background: #e5e9ee; }
QSlider::sub-page:horizontal, QSlider::handle:horizontal { background: #e76318; }
QLabel#playbackStatus[active="true"] { color: #be5719; }
QToolTip { color: #ffffff; background: #1b2639; border-color: #1b2639; }
QWidget#startRoot { background: #f2f4f8; }
QLabel#startEyebrow { color: #a75019; font-size: 15px; font-weight: 700; }
QLabel#startTitle { color: #172238; font-size: 38px; font-weight: 750; }
QLabel#startDescription { color: #667386; font-size: 18px; }
QFrame#startCard {
    background: #ffffff; border: 1px solid #e0e5ec; border-radius: 8px;
}
QLabel#startCardTitle { color: #172238; font-size: 27px; font-weight: 700; }
QLabel#startHelp { color: #667386; font-size: 17px; }
QWidget#startRoot QPushButton { font-size: 17px; min-height: 43px; }
QWidget#comparisonRoot { background: #f2f4f8; }
QLabel#comparisonTitle { color: #172238; font-size: 30px; font-weight: 700; }
QLabel#comparisonCount {
    color: #315569; background: #e7f2f6; border: 1px solid #cfe3eb;
    border-radius: 8px; padding: 8px 12px; font-size: 16px; font-weight: 700;
}
QLabel#comparisonInstruction {
    color: #667386; font-size: 15px; padding: 3px 2px;
}
QWidget#comparisonContent, QScrollArea#comparisonScroll,
QScrollArea#comparisonScroll > QWidget > QWidget { background: #f2f4f8; }
QFrame#comparisonCard {
    background: #ffffff; border: 1px solid #e0e5ec; border-radius: 8px;
}
QPushButton#comparisonTopButton:disabled { color: #a1aab8; background: #f2f4f7; }
QScrollArea#comparisonScroll QScrollBar:vertical {
    background: #e8edf3; width: 12px; margin: 4px 0 4px 0; border-radius: 6px;
}
QScrollArea#comparisonScroll QScrollBar::handle:vertical {
    background: #aab8c8; border-radius: 6px; min-height: 36px;
}
QScrollArea#comparisonScroll QScrollBar::handle:vertical:hover { background: #788ca4; }
QScrollArea#comparisonScroll QScrollBar::add-line:vertical,
QScrollArea#comparisonScroll QScrollBar::sub-line:vertical { height: 0; }
QScrollArea#comparisonScroll QScrollBar::add-page:vertical,
QScrollArea#comparisonScroll QScrollBar::sub-page:vertical { background: transparent; }
QListWidget#comparisonList {
    color: #26354b; background: #ffffff; border: 1px solid #dce2e9;
    border-radius: 7px; padding: 5px; font-size: 16px;
}
QListWidget#comparisonList::item { padding: 8px 10px; }
QListWidget#comparisonList::item:selected { background: #dcecf4; color: #172238; }
QTabWidget#startTabs::pane {
    background: #ffffff; border: 1px solid #e0e5ec; border-radius: 8px;
}
QTabWidget#startTabs QTabBar::tab {
    color: #526075; background: #e9edf2; border: 1px solid #dce2e9;
    border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px;
    padding: 11px 22px; margin-right: 4px; font-size: 17px;
}
QTabWidget#startTabs QTabBar::tab:selected {
    color: #172238; background: #ffffff; border-top: 3px solid #e76318;
}
"""


def scaled_app_style(adjustment: int) -> str:
    """Aplica o mesmo nível A−/A+ a todas as fontes dos menus Qt."""
    scale = 1.0 + adjustment * FONT_PERCENT_STEP / 100.0
    return re.sub(
        r"(font-size:\s*)(\d+)px",
        lambda match: f"{match.group(1)}{max(8, round(int(match.group(2)) * scale))}px",
        APP_STYLE,
    )


def split_column(column: str) -> tuple[str, str]:
    """Separa ``nome(unidade)`` sem depender de nomes fixos."""
    column = column.strip()
    if column.endswith(")") and "(" in column:
        name, unit = column.rsplit("(", 1)
        return name.strip(), unit[:-1].strip()
    return column, ""


def load_table(path: Path) -> tuple[np.ndarray, list[str], str, str, str]:
    """Lê e valida uma tabela CSV numérica com cabeçalho."""
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with path.open("r", encoding="utf-8-sig") as stream:
        header = stream.readline().strip()
    columns = [item.strip() for item in header.split(",")]
    if len(columns) < 2:
        raise ValueError("O arquivo precisa ter ao menos duas colunas separadas por vírgula.")

    data = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    if data.shape[1] != len(columns):
        raise ValueError(
            f"Cabeçalho com {len(columns)} colunas, mas os dados possuem {data.shape[1]}."
        )
    if data.size == 0 or not np.all(np.isfinite(data)):
        raise ValueError("A tabela está vazia ou contém valores não numéricos/infinitos.")

    time_name, time_unit = split_column(columns[0])
    parsed_series = [split_column(column) for column in columns[1:]]
    series_names = [name for name, _unit in parsed_series]
    mass_units = {unit for _name, unit in parsed_series if unit}
    mass_unit = mass_units.pop() if len(mass_units) == 1 else "valor"
    order = np.argsort(data[:, 0], kind="stable")
    return data[order], series_names, time_name, time_unit or "unidade", mass_unit


def format_br(value: float, decimals: int = 4) -> str:
    """Formata decimal com vírgula e remove zeros decimais desnecessários."""
    text = f"{value:,.{decimals}f}"
    text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    return text.rstrip("0").rstrip(",") if "," in text else text


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
        new_scale = float(np.clip(event.size().width() / 1100.0, 0.62, 1.0))
        if abs(new_scale - self._font_scale) >= 0.04 and hasattr(self, "axes"):
            self._font_scale = new_scale
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
        self._draw_shared_legend(line_axis)

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
        """Aplica acabamento científico consistente a qualquer gráfico."""
        axis.set_facecolor(PLOT_BACKGROUND)
        axis.set_axisbelow(True)
        axis.grid(True, color=PLOT_GRID, linewidth=0.8, linestyle="--", alpha=0.85)
        axis.tick_params(
            axis="both",
            labelsize=self._tick_font(),
            colors=PLOT_MUTED,
            width=0.8,
            length=4,
        )
        axis.title.set_color(PLOT_TEXT)
        axis.xaxis.label.set_color(PLOT_TEXT)
        axis.yaxis.label.set_color(PLOT_TEXT)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color(PLOT_SPINE)
        axis.spines["bottom"].set_color(PLOT_SPINE)
        axis.spines["left"].set_linewidth(0.8)
        axis.spines["bottom"].set_linewidth(0.8)

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
                lw=2.2,
                solid_capstyle="round",
                label=self.labels[index],
            )
        total = np.clip(self.values, 0, None).sum(axis=1)[: len(time)]
        axis.plot(time, total, color=TOTAL_COLOR, lw=2.6, label="Massa total")
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

    def _draw_shared_legend(self, source_axis) -> None:
        """Cria uma legenda externa comum aos dois gráficos superiores."""
        handles, labels = source_axis.get_legend_handles_labels()
        compact_labels = [LEGEND_LABELS.get(label, label) for label in labels]
        legend_size = self._tick_font()
        self.shared_legend = self.figure.legend(
            handles,
            compact_labels,
            fontsize=legend_size,
            ncol=3 if self._font_adjustment > 0 else NORMAL_LEGEND_COLUMNS,
            loc="upper center",
            bbox_to_anchor=NORMAL_LEGEND_ANCHOR,
            borderaxespad=0,
            labelspacing=0.15,
            columnspacing=1.2,
            handlelength=1.8,
            handletextpad=0.6,
            frameon=True,
            fancybox=True,
            framealpha=1.0,
            facecolor="#ffffff",
            edgecolor="#dce7eb",
        )

    # -------------------------------------------------------------------------
    # AMPLIAÇÃO E RETORNO AO MOSAICO
    # -------------------------------------------------------------------------
    def _on_click(self, event) -> None:
        if self.expanded_index is not None or event.inaxes not in self.axes:
            return
        self.expanded_index = self.axes.index(event.inaxes)
        self._apply_expanded_layout()
        self.expanded_changed.emit(True)
        self.draw_idle()

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


class MassBalanceWindow(QMainWindow):
    """Janela principal responsiva do painel."""

    closed = Signal()

    def __init__(self, path: Path) -> None:
        super().__init__()
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

        self.setWindowTitle("OSCAR — Balanço de Massa")
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

    def _build_interface(self) -> None:
        shell = QWidget()
        shell.setObjectName("appShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._build_navigation())

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

    def _build_navigation(self) -> QWidget:
        """Barra escura fixa de contexto, inspirada na referência enviada."""
        navigation = QFrame()
        self.navigation = navigation
        navigation.setObjectName("navigationRail")
        navigation.setFixedWidth(NAVIGATION_WIDTH)
        layout = QVBoxLayout(navigation)
        layout.setContentsMargins(14, 22, 14, 18)
        layout.setSpacing(0)

        brand = QHBoxLayout()
        brand.setSpacing(8)
        mark = QLabel("O")
        mark.setObjectName("brandMark")
        mark.setFixedSize(30, 30)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.addWidget(mark)
        brand_name = QLabel("OSCAR")
        brand_name.setObjectName("brandName")
        brand.addWidget(brand_name)
        brand.addStretch()
        layout.addLayout(brand)

        brand_subtitle = QLabel("ANÁLISE DE MASSA")
        brand_subtitle.setObjectName("navMuted")
        brand_subtitle.setWordWrap(True)
        layout.addWidget(brand_subtitle)
        layout.addSpacing(46)

        section = QLabel("ANÁLISE")
        section.setObjectName("navSection")
        layout.addWidget(section)
        layout.addSpacing(9)

        current = QLabel("Balanço\nde massa")
        current.setObjectName("navCurrent")
        current.setMinimumHeight(62)
        current.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(current)
        layout.addSpacing(14)

        nav_note = QLabel("Séries temporais\nComposição\nParticipação")
        nav_note.setObjectName("navMuted")
        layout.addWidget(nav_note)
        layout.addStretch()

        footer = QLabel("OSCAR · Visualização\nDados MASBAL")
        footer.setObjectName("navFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return navigation

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
    # SETOR B — BARRA LATERAL: séries, escala, fontes e ações
    # -------------------------------------------------------------------------
    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        self.sidebar = sidebar
        sidebar.setObjectName("sidebarCard")
        sidebar.setMinimumWidth(SIDEBAR_WIDTH_RANGE[0])
        sidebar.setMaximumWidth(SIDEBAR_WIDTH_RANGE[1])
        sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 14)
        layout.setSpacing(10)

        eyebrow = QLabel("CONTROLES")
        eyebrow.setObjectName("sectionEyebrow")
        layout.addWidget(eyebrow)
        sidebar_title = QLabel("Explorar resultados")
        sidebar_title.setObjectName("sidebarTitle")
        layout.addWidget(sidebar_title)

        self._add_series_selector(layout)
        layout.addWidget(self._build_scale_controls())
        layout.addWidget(self._build_font_controls())

        self.reset_button = QPushButton("Redefinir painel")
        self.reset_button.setProperty("role", "ghost")
        self.reset_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.reset_button.setToolTip(
            "Volta ao tempo zero, reativa todas as séries e retorna à escala linear."
        )
        self.reset_button.clicked.connect(self._reset_panel)
        layout.addWidget(self.reset_button)

        self.new_file_button = QPushButton("Escolher outro arquivo")
        self.new_file_button.setProperty("role", "ghost")
        self.new_file_button.setVisible(False)
        layout.addWidget(self.new_file_button)

        save_button = QPushButton("Salvar imagem")
        save_button.setProperty("role", "primary")
        save_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        )
        save_button.clicked.connect(self._save_dialog)
        layout.addWidget(save_button)
        return sidebar

    def _add_series_selector(self, parent_layout: QVBoxLayout) -> None:
        """Adiciona a lista rolável de séries ao setor lateral."""
        title_row = QHBoxLayout()
        series_title = QLabel("Séries visíveis")
        series_title.setObjectName("panelTitle")
        title_row.addWidget(series_title)
        series_count = QLabel(str(len(self.labels)))
        series_count.setObjectName("fileChip")
        title_row.addWidget(series_count)
        title_row.addStretch()
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
            application.setStyleSheet(scaled_app_style(adjustment))
        # A+ altera fontes, não as larguras dos setores nem a posição dos gráficos.
        self.navigation.setFixedWidth(NAVIGATION_WIDTH)
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

    def _save_dialog(self) -> None:
        default = self.path.with_name(f"{self.path.stem}_painel.png")
        output, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Salvar painel",
            str(default),
            "Imagem PNG (*.png);;Documento PDF (*.pdf);;Imagem SVG (*.svg)",
        )
        if output:
            self.save_figure(Path(output))

    def save_figure(self, output: Path) -> None:
        self.canvas.figure.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")

    def closeEvent(self, event) -> None:  # noqa: N802 - nome definido pelo Qt
        self._pause()
        self.closed.emit()
        super().closeEvent(event)


@dataclass
class ComparisonResult:
    """Um MASBAL normalizado para comparação entre cenários."""

    path: Path
    time: np.ndarray
    values: np.ndarray
    labels: list[str]
    time_unit: str
    mass_unit: str


def load_comparison_result(path: Path) -> ComparisonResult:
    data, names, _time_name, time_unit, mass_unit = load_table(path)
    configured_order = {name: index for index, name in enumerate(LABELS)}
    order = sorted(
        range(len(names)),
        key=lambda index: (configured_order.get(names[index].lower(), len(configured_order)), index),
    )
    return ComparisonResult(
        path=path,
        time=data[:, 0],
        values=data[:, 1:][:, order],
        labels=[LABELS.get(names[index].lower(), names[index]) for index in order],
        time_unit="dias" if time_unit.lower() in {"day", "days"} else time_unit,
        mass_unit=mass_unit,
    )


class ComparisonCanvas(FigureCanvas):
    """Distribuição acumulada de cada resultado, com escalas compartilhadas."""

    def __init__(self, results: list[ComparisonResult]) -> None:
        canvas_height = max(720, 350 * len(results) + 170)
        self.figure = Figure(figsize=(12, canvas_height / 100), dpi=100)
        super().__init__(self.figure)
        self.setMinimumSize(780, canvas_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._draw_results(results)

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

    def _draw_results(self, results: list[ComparisonResult]) -> None:
        axes = self.figure.subplots(len(results), 1, sharex=True, sharey=True, squeeze=False).ravel()
        all_labels = {label for result in results for label in result.labels}
        ordered_labels = [item["label"] for item in SERIES_CONFIG if item["label"] in all_labels]
        ordered_labels += sorted(all_labels.difference(ordered_labels))
        legend_handles = [
            Patch(
                facecolor=SERIES_COLORS.get(label, "#6c757d"),
                label=LEGEND_LABELS.get(label, label),
            )
            for label in ordered_labels
        ]
        legend_handles.append(Line2D([], [], color=TOTAL_COLOR, lw=2.3, label="Massa total"))
        self.figure.legend(
            handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 0.99),
            ncol=4, fontsize=11, frameon=False, columnspacing=1.3,
        )

        time_min = min(float(result.time[0]) for result in results)
        time_max = max(float(result.time[-1]) for result in results)
        if time_min == time_max:
            time_min -= 0.5
            time_max += 0.5
        mass_max = max(
            float(np.max(np.clip(result.values, 0, None).sum(axis=1)))
            for result in results
        )
        mass_max = max(mass_max, 1e-12)

        for axis, result in zip(axes, results):
            colors = [SERIES_COLORS.get(label, "#6c757d") for label in result.labels]
            values = np.clip(result.values, 0, None)
            axis.stackplot(result.time, values.T, colors=colors, alpha=0.88)
            axis.plot(result.time, values.sum(axis=1), color=TOTAL_COLOR, lw=2.2)
            axis.set_title(
                simulation_title(result.path), loc="left",
                fontsize=14, fontweight="bold", color=PLOT_TEXT, pad=12,
            )
            axis.set_xlim(time_min, time_max)
            axis.set_ylim(0, mass_max * 1.08)
            axis.set_ylabel(f"Massa ({result.mass_unit})", fontsize=12, color=PLOT_TEXT)
            axis.set_facecolor(PLOT_BACKGROUND)
            axis.set_axisbelow(True)
            axis.grid(True, color=PLOT_GRID, linewidth=0.8, linestyle="--")
            axis.tick_params(colors=PLOT_MUTED, labelsize=11)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            axis.spines["left"].set_color(PLOT_SPINE)
            axis.spines["bottom"].set_color(PLOT_SPINE)
        axes[-1].set_xlabel(f"Tempo ({results[0].time_unit})", fontsize=12, color=PLOT_TEXT)
        figure_height = self.figure.get_figheight() * self.figure.dpi
        self.figure.subplots_adjust(
            left=0.11, right=0.97,
            top=1 - 155 / figure_height, bottom=70 / figure_height,
            hspace=0.42,
        )
        self.draw_idle()


class ComparisonView(QWidget):
    """Exibe a comparação na mesma janela da tela inicial."""

    back_requested = Signal()

    def __init__(self, results: list[ComparisonResult]) -> None:
        super().__init__()
        self.setObjectName("comparisonRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(14)

        header = QVBoxLayout()
        header.setSpacing(4)
        header_top = QHBoxLayout()
        title = QLabel("Distribuição acumulada")
        title.setObjectName("comparisonTitle")
        header_top.addWidget(title, stretch=1)

        count = QLabel(f"{len(results)} resultados")
        count.setObjectName("comparisonCount")
        header_top.addWidget(count)
        header.addLayout(header_top)

        subtitle = QLabel(
            "Compare os cenários abaixo usando a mesma escala de tempo e massa."
        )
        subtitle.setObjectName("startHelp")
        header.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.addStretch()
        top_button = QPushButton("↑  Voltar ao topo")
        top_button.setObjectName("comparisonTopButton")
        actions.addWidget(top_button)
        back_button = QPushButton("Voltar aos arquivos")
        back_button.clicked.connect(self.back_requested.emit)
        actions.addWidget(back_button)
        header.addLayout(actions)
        layout.addLayout(header)

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
        content_layout.setSpacing(12)
        instruction = QLabel("Role para visualizar todas as simulações  ·  A legenda vale para todos os gráficos")
        instruction.setObjectName("comparisonInstruction")
        content_layout.addWidget(instruction)
        chart_card = QFrame()
        chart_card.setObjectName("comparisonCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(14, 14, 14, 14)
        self.canvas = ComparisonCanvas(results)
        chart_layout.addWidget(self.canvas)
        content_layout.addWidget(chart_card)
        scroll.setWidget(content)
        self.scroll = scroll
        layout.addWidget(scroll, stretch=1)


class StartWindow(QMainWindow):
    """Tela inicial para escolher um resultado antes de criar o painel."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("OSCAR — Início")
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

        eyebrow = QLabel("OSCAR  /  ANÁLISE DE RESULTADOS")
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
        tabs.addTab(self._multiple_results_tab(), "Múltiplos resultados")
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

    def _multiple_results_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
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

        self.comparison_list = QListWidget()
        self.comparison_list.setObjectName("comparisonList")
        self.comparison_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.comparison_list.setAlternatingRowColors(True)
        layout.addWidget(self.comparison_list, stretch=1)
        self.comparison_count = QLabel("Nenhum arquivo selecionado")
        self.comparison_count.setObjectName("startHelp")
        layout.addWidget(self.comparison_count)
        compare_button = QPushButton("Comparar distribuição acumulada")
        compare_button.setProperty("role", "primary")
        compare_button.clicked.connect(self._open_comparison)
        layout.addWidget(compare_button)
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
                item = QListWidgetItem(simulation_title(path))
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                item.setToolTip(str(path))
                self.comparison_list.addItem(item)
                self.last_directory = path.parent
        self._update_comparison_count()

    def _remove_comparison_files(self) -> None:
        for item in self.comparison_list.selectedItems():
            self.comparison_paths.remove(Path(item.data(Qt.ItemDataRole.UserRole)))
            self.comparison_list.takeItem(self.comparison_list.row(item))
        self._update_comparison_count()

    def _clear_comparison_files(self) -> None:
        self.comparison_paths.clear()
        self.comparison_list.clear()
        self._update_comparison_count()

    def _update_comparison_count(self) -> None:
        count = len(self.comparison_paths)
        self.comparison_count.setText(
            f"{count} arquivo{'s' if count != 1 else ''} selecionado{'s' if count != 1 else ''}"
            if count else "Nenhum arquivo selecionado"
        )

    def _open_comparison(self) -> None:
        if len(self.comparison_paths) < 2:
            QMessageBox.information(
                self, "Selecione mais arquivos", "Escolha ao menos dois balanços de massa."
            )
            return
        try:
            results = [load_comparison_result(path) for path in self.comparison_paths]
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
        self.setWindowTitle("OSCAR — Comparação de resultados")
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
        self.setWindowTitle("OSCAR — Balanço de Massa")
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
        self.setWindowTitle("OSCAR — Início")
        self.setMinimumSize(780, 620)
        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(APP_STYLE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualiza tabelas de balanço de massa MASBAL.")
    parser.add_argument("arquivo", nargs="?", type=Path, help="arquivo .txt ou .log")
    parser.add_argument("--save", type=Path, metavar="IMAGEM", help="salva os gráficos ao iniciar")
    parser.add_argument("--no-show", action="store_true", help="não abre a janela")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    application = QApplication.instance() or QApplication(sys.argv)
    application.setStyle("Fusion")
    application.setStyleSheet(APP_STYLE)

    if args.arquivo is None and not args.save and not args.no_show:
        launcher = StartWindow()
        launcher.show()
        raise SystemExit(application.exec())

    path = args.arquivo or DEFAULT_FILE

    try:
        window = MassBalanceWindow(path.expanduser().resolve())
    except (FileNotFoundError, ValueError) as error:
        if args.no_show:
            raise SystemExit(str(error)) from error
        QMessageBox.critical(None, "Não foi possível abrir o arquivo", str(error))
        raise SystemExit(1) from error

    if args.save:
        window.save_figure(args.save.expanduser().resolve())
        print(f"Imagem salva em: {args.save.expanduser().resolve()}")
    if args.no_show:
        window.close()
        return

    window.show()
    raise SystemExit(application.exec())


if __name__ == "__main__":
    main()
