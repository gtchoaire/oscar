"""Exportação de comparação MASBAL para relatórios (sem dependência de Qt)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib import rc_context
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .comparison_plot import draw_comparison_axis
from .config import (
    EXPORT_FIGURE_SIZE, EXPORT_RENDER_DPI, SERIES_COLORS, SERIES_CONFIG, TOTAL_COLOR,
)
from .data import ComparisonResult, simulation_title
from .export import SUPPORTED_EXTENSIONS, save_report_figure
from .plot_style import TOTAL_LINE_WIDTH
from .typography import COMPARISON_TYPOGRAPHY as TYPE, configure_matplotlib_typography
from .theme import PLOT_MUTED, PLOT_TEXT


SCENARIOS_PER_PAGE = 4


def _shared_limits(results: list[ComparisonResult]) -> tuple[tuple[float, float], float]:
    """Reproduz a escala comum adotada pela janela de comparação."""
    if not results:
        raise ValueError("Não há cenários visíveis para exportação.")
    if len({result.time_unit for result in results}) != 1 or len(
        {result.mass_unit for result in results}
    ) != 1:
        raise ValueError("Os cenários precisam ter unidades de tempo e massa iguais.")
    time_min = min(float(result.time[0]) for result in results)
    time_max = max(float(result.time[-1]) for result in results)
    if time_min == time_max:
        time_min -= 0.5
        time_max += 0.5
    mass_maximum = max(
        1e-12,
        *(float(np.max(np.clip(result.values, 0, None).sum(axis=1))) for result in results),
    )
    return (time_min, time_max), mass_maximum


# Incremento 4.3B — hierarquia de impressão, sem alterar as séries.
def _legend(figure: Figure, results: list[ComparisonResult]) -> None:
    present = {label for result in results for label in result.labels}
    ordered = [item["label"] for item in SERIES_CONFIG if item["label"] in present]
    ordered += sorted(present.difference(ordered))
    handles = [Patch(facecolor=SERIES_COLORS.get(label, "#6c757d")) for label in ordered]
    handles.append(Line2D([0], [0], color=TOTAL_COLOR, lw=TOTAL_LINE_WIDTH))
    figure.legend(
        handles, [*ordered, "Massa total"],
        loc="lower center", bbox_to_anchor=(0.5, 0.085),
        ncol=4, fontsize=TYPE.legend, frameon=False,
        handlelength=1.6, columnspacing=1.5, labelspacing=0.8,
    )


def build_comparison_page(
    page_results: list[ComparisonResult],
    time_limits: tuple[float, float],
    mass_maximum: float,
    *,
    page_number: int = 1,
    page_count: int = 1,
    legend_results: list[ComparisonResult] | None = None,
) -> Figure:
    """Página 2×2 com tipografia hierárquica e legenda comum."""
    if not 1 <= len(page_results) <= SCENARIOS_PER_PAGE:
        raise ValueError("Uma página precisa conter de um a quatro cenários.")
    configure_matplotlib_typography()
    figure = Figure(figsize=EXPORT_FIGURE_SIZE, dpi=EXPORT_RENDER_DPI, facecolor="white")
    grid = figure.add_gridspec(
        2, 2, left=0.085, right=0.975, top=0.785, bottom=0.285,
        wspace=0.25, hspace=0.75,
    )
    figure.text(0.085, 0.946, "Comparação MASBAL — distribuição acumulada",
                fontsize=TYPE.title, color=PLOT_TEXT, weight="bold", va="top")
    figure.text(0.085, 0.903, "Mesmas escalas de tempo e massa em todos os cenários",
                fontsize=TYPE.subtitle, color=PLOT_MUTED, va="top")
    for index, result in enumerate(page_results):
        axis = (figure.add_subplot(grid[0, :]) if len(page_results) == 1
                else figure.add_subplot(grid[index // 2, index % 2]))
        draw_comparison_axis(
            axis, result, time_limits, mass_maximum,
            axis_label_size=TYPE.axis_label, axis_tick_size=TYPE.axis_ticks,
        )
        main, separator, metadata = simulation_title(result.path).partition(" · ")
        position = axis.get_position()
        figure.text(position.x0, position.y1 + 0.073, main,
                    fontsize=TYPE.scenario, color=PLOT_TEXT,
                    weight="bold", va="top")
        if separator:
            figure.text(position.x0, position.y1 + 0.044, metadata,
                        fontsize=TYPE.metadata, color=PLOT_MUTED, va="top")
    _legend(figure, page_results if legend_results is None else legend_results)
    figure.text(0.085, 0.025, "Fonte: OSCAR · arquivos MASBAL",
                fontsize=TYPE.footer, color=PLOT_MUTED, va="bottom")
    figure.text(0.975, 0.025, f"Página {page_number}/{page_count}",
                fontsize=TYPE.footer, color=PLOT_MUTED, va="bottom", ha="right")
    return figure


def save_comparison_report(results: list[ComparisonResult], output: Path) -> list[Path]:
    """Exporta até quatro cenários por página com escalas comuns.

    PDF: arquivo com várias páginas. PNG/SVG/EPS: um arquivo por página;
    quando houver mais de quatro cenários, acrescenta _p01, _p02 etc.
    Retorna os caminhos efetivamente produzidos.
    """
    output = Path(output)
    extension = output.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Formato inválido. Utilize PNG, PDF, SVG ou EPS.")
    time_limits, mass_maximum = _shared_limits(results)
    pages = [results[start:start + SCENARIOS_PER_PAGE]
             for start in range(0, len(results), SCENARIOS_PER_PAGE)]
    if extension == ".pdf":
        with rc_context({"pdf.fonttype": 42}):
            with PdfPages(output, metadata={"Creator": "CANNES - OSCAR/MASBAL post-processing"}) as document:
                for index, page in enumerate(pages, 1):
                    figure = build_comparison_page(
                        page, time_limits, mass_maximum,
                        page_number=index, page_count=len(pages), legend_results=results,
                    )
                    try:
                        document.savefig(figure, dpi=300, facecolor="white")
                    finally:
                        figure.clear()
        return [output]

    filenames = ([output] if len(pages) == 1 else [
        output.with_name(f"{output.stem}_p{index:02d}{output.suffix}")
        for index in range(1, len(pages) + 1)
    ])
    existing = [path.name for path in filenames if path.exists()]
    if existing:
        raise FileExistsError("Arquivos já existentes: " + ", ".join(existing))
    written = []
    try:
        for index, (page, filename) in enumerate(zip(pages, filenames), 1):
            figure = build_comparison_page(
                page, time_limits, mass_maximum,
                page_number=index, page_count=len(pages), legend_results=results,
            )
            try:
                save_report_figure(figure, filename)
                written.append(filename)
            finally:
                figure.clear()
    except Exception:
        # Evita deixar um pacote incompleto de páginas no diretório.
        for path in written:
            path.unlink(missing_ok=True)
        raise
    return written
