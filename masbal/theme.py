"""Tema Qt e cores neutras dos gráficos."""

import re

from .config import FONT_PERCENT_STEP
from .typography import FONT_FAMILY

# 5. APARÊNCIA DOS COMPONENTES PYSIDE6
# =============================================================================
PLOT_BACKGROUND = "#fcfdfb"
PLOT_TEXT = "#2c423f"
PLOT_MUTED = "#5f7470"
PLOT_GRID = "#dfe7e1"
PLOT_SPINE = "#a7b9b0"

APP_STYLE = """
QWidget {
    color: #172b36;
    
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
QWidget { color: #1c293b;  }
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
QFrame#comparisonLegend {
    background: #ffffff; border: 1px solid #dce4eb; border-radius: 8px;
}
QLabel#comparisonLegendTitle {
    color: #526075; font-size: 13px; font-weight: 700;
}
QLabel#comparisonLegendName { color: #26354b; font-size: 16px; }
QLabel#comparisonChartTitle {
    color: #172238; font-size: 19px; font-weight: 700;
}
QLabel#comparisonChartMetadata { color: #526075; font-size: 14px; }
QPushButton#comparisonZoomButton, QPushButton#comparisonZoomReset {
    min-width: 42px; min-height: 32px; font-size: 14px;
}
QPushButton#comparisonChartZoom {
    color: #315569; background: #edf5f8; border: 1px solid #d1e2e9;
    border-radius: 6px; min-height: 27px; padding: 2px 10px; font-size: 13px;
}
QPushButton#comparisonChartZoom:hover {
    color: #086788; background: #e2f1f6; border-color: #a8cedc;
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

# Identidade visual do CANNES: verde profundo na navegação, laranja nas ações
# e superfícies claras para os dados. Mantida separada da paleta das séries,
# cuja escolha atende também à leitura por pessoas com daltonismo.
APP_STYLE += """
QWidget { color: #2c423f; }
QWidget#appShell, QWidget#appRoot, QWidget#startRoot, QWidget#comparisonRoot,
QScrollArea#pageScroll, QScrollArea#pageScroll > QWidget > QWidget,
QWidget#comparisonContent, QScrollArea#comparisonScroll,
QScrollArea#comparisonScroll > QWidget > QWidget { background: #f2f5f2; }
QFrame#navigationRail { background: #21332f; }
QLabel#brandMark { background: #f98600; color: #21332f; }
QLabel#brandName { color: #ffffff; }
QLabel#navSection, QLabel#navMuted { color: #bbcbc3; }
QLabel#navFooter { color: #a5b9ad; }
QLabel#navCurrent {
    color: #ffffff; background: #3d5b50;
    border-left: 3px solid #f98600;
}
QFrame#sidebarCard, QFrame#chartCard, QFrame#playerCard,
QFrame#startCard, QFrame#comparisonCard, QFrame#comparisonLegend,
QFrame#timeCard {
    background: #ffffff; border: 1px solid #d9e3dc; border-radius: 9px;
}
QLabel#mainTitle, QLabel#sidebarTitle, QLabel#panelTitle,
QLabel#startTitle, QLabel#startCardTitle, QLabel#comparisonTitle,
QLabel#comparisonChartTitle, QLabel#timeDisplay { color: #213b33; }
QLabel#eyebrow, QLabel#sectionEyebrow, QLabel#startEyebrow,
QLabel#comparisonLegendTitle { color: #9c4a00; }
QLabel#subtitle, QLabel#startDescription, QLabel#startHelp,
QLabel#comparisonInstruction, QLabel#comparisonChartMetadata,
QLabel#stepDisplay, QLabel#timeCaption { color: #5f7470; }
QLabel#fileChip, QLabel#timePill, QLabel#comparisonCount {
    color: #2c423f; background: #edf3ed; border: 1px solid #d9e3dc;
}
QGroupBox { color: #3d5b50; background: #f9fbf8; border-color: #d9e3dc; }
QPushButton {
    color: #2c423f; background: #f9fbf8;
    border: 1px solid #bdcec3; border-radius: 8px;
}
QPushButton:hover {
    color: #744000; background: #fff3e5; border-color: #f3ae5c;
}
QPushButton:pressed { background: #ffe5c2; }
QPushButton[role="primary"] {
    color: #21332f; background: #f98600; border-color: #da7600;
}
QPushButton[role="primary"]:hover {
    color: #21332f; background: #ffad3e; border-color: #d97800;
}
QPushButton[role="ghost"] { color: #2c423f; background: #ffffff; }
QPushButton#comparisonChartZoom {
    color: #2c423f; background: #edf3ed; border-color: #d9e3dc;
}
QPushButton#comparisonChartZoom:hover {
    color: #744000; background: #fff3e5; border-color: #f3ae5c;
}
QCheckBox, QRadioButton, QLabel#seriesLabel,
QLabel#comparisonLegendName { color: #2c423f; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: #2c423f; border: 4px solid #dcece1;
}
QFrame#seriesRow:hover { background: #eef5ee; }
QSlider::groove:horizontal, QSlider::add-page:horizontal { background: #dae4dc; }
QSlider::sub-page:horizontal, QSlider::handle:horizontal { background: #f98600; }
QLabel#playbackStatus[active="true"] { color: #995000; }
QSplitter::handle { background: #f2f5f2; }
QListWidget#comparisonList { color: #2c423f; border-color: #d9e3dc; }
QListWidget#comparisonList::item:selected { color: #21332f; background: #e4f0e7; }
QTabWidget#startTabs::pane { border-color: #d9e3dc; }
QTabWidget#startTabs QTabBar::tab {
    color: #486456; background: #e7eee8; border-color: #d9e3dc;
}
QTabWidget#startTabs QTabBar::tab:selected {
    color: #213b33; background: #ffffff; border-top: 3px solid #f98600;
}
QToolTip { color: #ffffff; background: #21332f; border-color: #21332f; }
"""

# Menu lateral do resultado individual. O CANNES concentra navegação e
# ferramentas numa única superfície escura, com a página ativa em laranja.
APP_STYLE += """
QFrame#cannesSidebar {
    background: #2c423f; border: 1px solid #223a35; border-radius: 10px;
}
QFrame#cannesSidebar QLabel#brandName { color: #ffffff; font-size: 19px; }
QFrame#cannesSidebar QLabel#sideMuted {
    color: #bdcec5; font-size: 12px; font-weight: 600;
}
QFrame#cannesSidebar QLabel#sideSection {
    color: #e0e2db; font-size: 12px; font-weight: 700;
}
QFrame#cannesSidebar QLabel#sideCurrent {
    color: #ffffff; background: #3d505f;
    border-left: 4px solid #f98600; border-radius: 5px;
    padding: 6px 10px; font-size: 15px; font-weight: 700;
}
QFrame#cannesSidebar QLabel#sideTitle {
    color: #ffffff; font-size: 19px; font-weight: 700;
}
QFrame#cannesSidebar QLabel#sideCount {
    color: #ffffff; background: #506b61; border: 1px solid #789184;
    border-radius: 7px; padding: 2px 8px; font-size: 13px;
}
QFrame#cannesSidebar QLabel#sideFooter {
    color: #bdcec5; font-size: 11px; font-weight: 600;
}
QFrame#cannesSidebar QTabWidget#sidebarTabs::pane {
    background: #2c423f; border: none;
}
QFrame#cannesSidebar QTabWidget#sidebarTabs QTabBar::tab {
    color: #c8d6cd; background: #344d47;
    border: 1px solid #5f7470; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    padding: 8px 18px; margin-right: 3px; font-size: 14px;
}
QFrame#cannesSidebar QTabWidget#sidebarTabs QTabBar::tab:selected {
    color: #21332f; background: #f98600;
    border-color: #f98600;
}
QFrame#cannesSidebar QWidget#sidebarTabPage { background: #2c423f; }
QFrame#cannesSidebar QWidget#seriesList,
QFrame#cannesSidebar QScrollArea,
QFrame#cannesSidebar QScrollArea > QWidget > QWidget {
    background: #2c423f;
}
QFrame#cannesSidebar QFrame#seriesRow { background: transparent; }
QFrame#cannesSidebar QFrame#seriesRow:hover { background: #3d5a52; }
QFrame#cannesSidebar QLabel#seriesLabel { color: #f4f7f4; font-size: 14px; }
QFrame#cannesSidebar QCheckBox::indicator,
QFrame#cannesSidebar QRadioButton::indicator {
    background: #ffffff; border-color: #c4d3ca;
}
QFrame#cannesSidebar QCheckBox::indicator:checked,
QFrame#cannesSidebar QRadioButton::indicator:checked {
    background: #f98600; border: 4px solid #fce3c2;
}
QFrame#cannesSidebar QRadioButton { color: #ffffff; }
QFrame#cannesSidebar QGroupBox {
    color: #e0e2db; background: #3d505f;
    border: 1px solid #5f7470; border-radius: 8px;
}
QFrame#cannesSidebar QGroupBox::title { color: #ffffff; background: #3d505f; }
QFrame#cannesSidebar QPushButton {
    color: #ffffff; background: #3d505f;
    border: 1px solid #71877a; border-radius: 7px;
}
QFrame#cannesSidebar QPushButton:hover {
    color: #ffffff; background: #496658; border-color: #f98600;
}
QFrame#cannesSidebar QPushButton:pressed { background: #506e5f; }
QFrame#cannesSidebar QPushButton[role="primary"] {
    color: #20322e; background: #f98600; border-color: #f98600;
}
QFrame#cannesSidebar QPushButton[role="primary"]:hover {
    color: #20322e; background: #ffad3e; border-color: #ffad3e;
}
QFrame#cannesSidebar QLabel#timePill {
    color: #ffffff; background: #506b61; border-color: #789184;
}
"""

# Acabamento visual CANNES (main.py e ViewPagesUI/index.ui do projeto-base):
# grafite #212B33, verde #2C423F, azul-acinzentado #3D505F, cinzas
# #C3C3C3/#E0E2DB e destaque #F98600. Não altera SERIES_CONFIG.
APP_STYLE += """
QWidget#appShell, QWidget#appRoot, QWidget#startRoot,
QWidget#comparisonRoot, QWidget#comparisonContent,
QScrollArea#pageScroll, QScrollArea#pageScroll > QWidget > QWidget,
QScrollArea#comparisonScroll, QScrollArea#comparisonScroll > QWidget > QWidget {
    background: #212b33;
}
QFrame#headerCard { background: transparent; border: none; }
QLabel#mainTitle, QLabel#startTitle, QLabel#comparisonTitle { color: #ffffff; }
QLabel#eyebrow, QLabel#sectionEyebrow, QLabel#startEyebrow,
QLabel#comparisonLegendTitle { color: #f98600; }
QLabel#subtitle, QLabel#startDescription, QLabel#comparisonInstruction {
    color: #d9e1da;
}
QFrame#chartCard QLabel#subtitle { color: #4c5b61; }
QLabel#fileChip, QLabel#timePill, QLabel#comparisonCount {
    color: #ffffff; background: #3d505f;
    border: 1px solid #829191; border-radius: 6px;
}
QFrame#timeCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #3d505f, stop:1 #2c423f);
    border: 1px solid #f98600; border-radius: 10px;
}
QLabel#timeCaption { color: #e0e2db; }
QLabel#timeDisplay { color: #ffffff; }
QLabel#stepDisplay { color: #d9e1da; }
QFrame#chartCard, QFrame#startCard, QFrame#comparisonCard {
    background: #e0e2db; border: 1px solid #829191; border-radius: 10px;
}
QFrame#chartCard QLabel#sectionEyebrow { color: #6f1a07; }
QLabel#startCardTitle, QLabel#comparisonChartTitle { color: #2c423f; }
QLabel#startHelp, QLabel#comparisonChartMetadata { color: #4c5b61; }
QWidget#comparisonRoot QLabel#startHelp { color: #d9e1da; }
QFrame#playerCard, QFrame#comparisonLegend {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #3d505f, stop:1 #2c423f);
    border: 1px solid #829191; border-radius: 10px;
}
QFrame#comparisonLegend QLabel#comparisonLegendName { color: #ffffff; }
QFrame#playerCard QLabel#playbackStatus { color: #e0e2db; }
QFrame#playerCard QLabel#playbackStatus[active="true"] { color: #ffb251; }
QFrame#playerCard QLabel#sectionEyebrow { color: #ffb251; }
QPushButton {
    color: #2c423f;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #e0e2db, stop:1 #c3c3c3);
    border: 1px solid #829191; border-radius: 8px;
}
QPushButton:hover {
    color: #2c423f;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffffff, stop:1 #e0e2db);
    border-color: #f98600;
}
QPushButton:pressed { background: #c3c3c3; }
QPushButton[role="primary"] {
    color: #212b33;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffb251, stop:1 #f98600);
    border: 1px solid #d97700;
}
QPushButton[role="primary"]:hover {
    color: #212b33;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffd091, stop:1 #f98600);
    border-color: #f98600;
}
QPushButton[role="ghost"] { color: #2c423f; background: #e0e2db; }
QFrame#cannesSidebar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #3d505f, stop:1 #2c423f);
    border: 1px solid #829191;
}
QFrame#cannesSidebar QLabel#sideCurrent {
    background: #2c423f; border-left-color: #f98600;
}
QFrame#cannesSidebar QTabWidget#sidebarTabs QTabBar::tab:selected {
    color: #212b33;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffb251, stop:1 #f98600);
}
QFrame#cannesSidebar QPushButton[role="primary"] {
    color: #212b33;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffb251, stop:1 #f98600);
}
QFrame#cannesSidebar QPushButton[role="primary"]:hover {
    color: #212b33;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffd091, stop:1 #f98600);
}
QSlider::groove:horizontal, QSlider::add-page:horizontal { background: #829191; }
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #e48100, stop:1 #f98600);
}
QSlider::handle:horizontal { background: #f98600; }
QScrollBar::handle:vertical { background: #829191; }
QScrollBar::handle:vertical:hover { background: #5f7470; }
QTabWidget#startTabs::pane { background: #e0e2db; border-color: #829191; }
QTabWidget#startTabs QTabBar::tab {
    color: #ffffff; background: #3d505f; border-color: #829191;
}
QTabWidget#startTabs QTabBar::tab:selected {
    color: #2c423f; background: #e0e2db; border-top: 3px solid #f98600;
}
QListWidget#comparisonList {
    color: #2c423f; background: #ffffff; border-color: #829191;
}
QListWidget#comparisonList::item:selected { color: #212b33; background: #e0e2db; }
QToolTip { color: #ffffff; background: #2c423f; border-color: #f98600; }
"""

APP_STYLE += """
QFrame#simulationFilterBar {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #3d505f, stop:1 #2c423f);
    border: 1px solid #829191; border-radius: 9px;
}
QFrame#simulationFilterBar QLabel#filterTitle {
    color: #f98600; font-size: 13px; font-weight: 700;
}
QFrame#simulationFilterBar QPushButton#filterFacet {
    color: #ffffff; background: #2c423f;
    border: 1px solid #829191; border-radius: 6px;
    min-height: 34px; text-align: left; padding: 3px 10px;
}
QFrame#simulationFilterBar QPushButton#filterFacet:hover {
    background: #496658; border-color: #f98600;
}
QFrame#simulationFilterBar QPushButton#filterReset {
    color: #2c423f; background: #e0e2db;
    border: 1px solid #829191; min-height: 26px;
}
QFrame#simulationFilterBar QLineEdit#filterSearch {
    color: #2c423f; background: #ffffff;
    border: 1px solid #829191; border-radius: 6px;
    min-height: 34px; padding: 2px 10px; font-size: 14px;
}
QFrame#simulationFilterBar QLineEdit#filterSearch:focus { border-color: #f98600; }
QMenu {
    color: #ffffff; background: #2c423f;
    border: 1px solid #829191; padding: 4px;
    font-size: 14px;
}
QMenu::item { padding: 7px 18px 7px 28px; }
QMenu::item:selected { background: #3d505f; color: #ffffff; }
QMenu::indicator:checked { background: #f98600; border: 1px solid #ffb251; }
QScrollArea#selectionScroll,
QScrollArea#selectionScroll > QWidget > QWidget,
QWidget#selectionContent {
    background: #e0e2db; border: none;
}
"""



# Tipografia global — incremento 4.3B. Fonte única em typography.py.
APP_STYLE += f"""
QWidget, QMenu, QToolTip {{ font-family: "{FONT_FAMILY}"; }}
"""


def scaled_app_style(adjustment: int) -> str:
    """Aplica o mesmo nível A−/A+ a todas as fontes dos menus Qt."""
    scale = 1.0 + adjustment * FONT_PERCENT_STEP / 100.0
    return re.sub(
        r"(font-size:\s*)(\d+)px",
        lambda match: f"{match.group(1)}{max(8, round(int(match.group(2)) * scale))}px",
        APP_STYLE,
    )
