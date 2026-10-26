"""Entrada compatível: use ``python3 post.py`` ou ``python3 main.py``.

A implementação está organizada no pacote ``masbal``. Este arquivo conserva
os nomes públicos usados durante o desenvolvimento inicial.
"""

from masbal.charts import ComparisonCanvas, MassBalanceCanvas, SeriesLabel
from masbal.comparison import ComparisonView
from masbal.config import *  # noqa: F401,F403 - compatibilidade com configuração antiga
from masbal.data import (ComparisonResult, SimulationMetadata, format_br,
                         load_comparison_result, load_table, simulation_metadata,
                         simulation_title, split_column)
from masbal.filters import SimulationFilterBar
from masbal.individual import MassBalanceWindow
from masbal.launcher import StartWindow
from masbal.theme import APP_STYLE, PLOT_BACKGROUND, PLOT_GRID, PLOT_MUTED, PLOT_SPINE, PLOT_TEXT, scaled_app_style
from main import main, parse_args


if __name__ == "__main__":
    main()
