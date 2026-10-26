"""Tipografia comum à interface e às figuras MASBAL.

A aplicação solicita Times New Roman. Quando ausente, Matplotlib usa uma
alternativa serifada explicitamente identificada por aviso (sem baixar fontes).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

from matplotlib import rcParams
from matplotlib.font_manager import FontProperties, findfont

FONT_FAMILY = "Times New Roman"
FONT_FALLBACKS = ("Tinos", "Liberation Serif", "DejaVu Serif")


@dataclass(frozen=True)
class ComparisonTypography:
    """Tamanhos em pontos para o relatório comparativo de 16 × 10 pol."""

    title: int = 20
    subtitle: int = 12
    scenario: int = 15
    metadata: int = 11
    axis_label: int = 12
    axis_ticks: int = 11
    legend: int = 11
    footer: int = 9


COMPARISON_TYPOGRAPHY = ComparisonTypography()
_warned = False


def installed_plot_font() -> str:
    """Retorna a primeira família disponível, respeitando a preferência."""
    for family in (FONT_FAMILY, *FONT_FALLBACKS):
        try:
            findfont(FontProperties(family=[family]), fallback_to_default=False)
        except ValueError:
            continue
        return family
    raise RuntimeError("Nenhuma fonte serifada disponível para os gráficos MASBAL.")


def configure_matplotlib_typography() -> str:
    """Aplica a mesma fonte a todas as figuras, incluindo matemática e vetores."""
    global _warned
    effective = installed_plot_font()
    if effective != FONT_FAMILY and not _warned:
        warnings.warn(
            f"Times New Roman não está instalada; Matplotlib usará {effective}. "
            "Instale Times New Roman para padronização tipográfica exata.",
            RuntimeWarning,
            stacklevel=2,
        )
        _warned = True
    rcParams.update({
        "font.family": [effective],
        "font.serif": [FONT_FAMILY, *FONT_FALLBACKS],
        "mathtext.fontset": "stix",  # glifos matemáticos compatíveis com serifadas
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    return effective
