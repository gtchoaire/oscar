"""Dados configuráveis, fontes e geometria do visualizador."""

from pathlib import Path

# 1. ARQUIVO PADRÃO
# =============================================================================
DEFAULT_FILE = Path(__file__).resolve().parent.parent / "include" / "Tutorial.masbal.log"
# 2. SÉRIES — EDITE A ORDEM, OS NOMES E AS CORES SOMENTE NESTA LISTA
# =============================================================================
# A ordem dos itens abaixo controla, ao mesmo tempo:
#   • a lista lateral;
#   • as curvas e áreas dos gráficos superiores;
#   • o eixo Y dos dois gráficos inferiores;
#   • a legenda.
#
# ``axis`` é o texto compacto dos eixos inferiores.
# ``legend`` é o texto compacto da legenda externa no painel individual.
# As oito cores da figura de referência seguem a paleta Okabe–Ito.
# Séries que não aparecem nela usam três tons adicionais da CARTOColors Safe
# (CARTO, CC BY 4.0): https://github.com/CartoDB/CartoColor
# A legenda do comparativo usa os ``label`` completos e fica fixa ao rolar.
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
        "color": "#332288",
    },
    {
        "column": "gasbubbles",
        "label": "Bolhas de gás na coluna d'água",
        "axis": "Bolhas de gás",
        "legend": "Bolhas de gás",
        "color": "#882255",
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
        "color": "#117733",
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
SIDE_LEGEND_MIN_WIDTH = 1120
SIDE_LEGEND_MIN_HEIGHT = 600
SIDE_LEGEND_ANCHOR = (0.825, 0.85)

# Posições usadas ao clicar em um gráfico para ampliá-lo.
EXPANDED_UPPER_POSITION = (0.10, 0.08, 0.80, 0.67)
EXPANDED_COMPOSITION_POSITION = (0.25, 0.10, 0.70, 0.82)
EXPANDED_HEATMAP_POSITION = (0.27, 0.10, 0.57, 0.82)

# Dimensões dos setores Qt da janela.
WINDOW_SIZE = (1600, 980)
WINDOW_MINIMUM_SIZE = (1100, 700)
PAGE_MINIMUM_SIZE = (1080, 720)
PAGE_MARGINS = (22, 16, 22, 18)
SIDEBAR_WIDTH_RANGE = (300, 390)
SPLITTER_INITIAL_SIZES = (320, 1080)
# Geometria dos gráficos comparativos
COMPARISON_GRID_COLUMNS = 4

COMPARISON_GRID_PLOT_WIDTH = 760
COMPARISON_GRID_PLOT_HEIGHT = 430

COMPARISON_EXPANDED_PLOT_WIDTH = 1120
COMPARISON_EXPANDED_PLOT_HEIGHT = 720


# Índices dos gráficos dentro de ``MassBalanceCanvas.axes``.
CHART_TEMPORAL = 0
CHART_ACCUMULATED = 1
CHART_COMPOSITION = 2
CHART_HEATMAP = 3


# =============================================================================

# =============================================================================
# 5. EXPORTAÇÃO DE FIGURAS PARA RELATÓRIOS
# =============================================================================
# Dimensões físicas fixas (polegadas) e resolução raster (pixels/polegada).
# PNG: 4800 x 3000 pixels. PDF e SVG preservam vetores quando disponíveis.
EXPORT_FIGURE_SIZE = (16.0, 10.0)
EXPORT_DPI = 300
EXPORT_RENDER_DPI = 100  # dimensão lógica usada para compor legendas e fontes
