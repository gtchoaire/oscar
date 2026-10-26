"""Exportação de figuras Matplotlib para relatórios, sem dependência de Qt."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from pathlib import Path

import numpy as np
from matplotlib import rc_context
from matplotlib.collections import Collection
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .config import EXPORT_DPI, EXPORT_FIGURE_SIZE

SUPPORTED_EXTENSIONS = frozenset({".png", ".pdf", ".svg", ".eps"})


def _blend_over_white(colors):
    """Converte cores RGBA em equivalentes opacos sobre fundo branco."""
    rgba = np.array(colors, dtype=float, copy=True)
    if not rgba.size:
        return rgba
    alpha = rgba[..., 3:4]
    rgba[..., :3] = rgba[..., :3] * alpha + (1.0 - alpha)
    rgba[..., 3:4] = np.where(alpha == 0, 0.0, 1.0)
    return rgba


@contextmanager
def _opaque_eps_artists(figure: Figure):
    """Aproxima transparências em EPS mantendo vetores e restaurando a figura."""
    restore = []
    try:
        for artist in figure.findobj():
            alpha = artist.get_alpha()
            if alpha is None or not np.isscalar(alpha) or alpha == 0 or alpha == 1:
                continue
            if isinstance(artist, Line2D):
                color = artist.get_color()
                restore.append((artist, "line", alpha, color, None))
                artist.set_alpha(None)
                artist.set_color(_blend_over_white(to_rgba(color, alpha=alpha)))
            elif isinstance(artist, Patch):
                face, edge = artist.get_facecolor(), artist.get_edgecolor()
                restore.append((artist, "patch", alpha, face, edge))
                artist.set_alpha(None)
                artist.set_facecolor(_blend_over_white(face))
                artist.set_edgecolor(_blend_over_white(edge))
            elif isinstance(artist, Collection):
                face = artist.get_facecolors().copy()
                edge = artist.get_edgecolors().copy()
                restore.append((artist, "collection", alpha, face, edge))
                artist.set_alpha(None)
                artist.set_facecolors(_blend_over_white(face))
                artist.set_edgecolors(_blend_over_white(edge))
        yield
    finally:
        for artist, kind, alpha, face, edge in reversed(restore):
            artist.set_alpha(None)
            if kind == "line":
                artist.set_color(face)
            elif kind == "patch":
                artist.set_facecolor(face)
                artist.set_edgecolor(edge)
            else:
                artist.set_facecolors(face)
                artist.set_edgecolors(edge)
            artist.set_alpha(alpha)


def save_report_figure(figure: Figure, output: Path) -> None:
    """Exporta painel com dimensões fixas, PNG a 300 dpi e vetores em PDF/SVG/EPS.

    No EPS, as transparências são mescladas ao fundo branco, pois PostScript
    não suporta canal alfa. Imagens (como o mapa de calor) seguem rasterizadas
    na resolução EXPORT_DPI, inclusive dentro dos formatos vetoriais.
    """
    output = Path(output)
    extension = output.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Formato inválido. Utilize PNG, PDF, SVG ou EPS.")

    original_size = tuple(figure.get_size_inches())
    eps = extension == ".eps"
    try:
        figure.set_size_inches(*EXPORT_FIGURE_SIZE, forward=False)
        with rc_context({"ps.fonttype": 42, "pdf.fonttype": 42}):
            with _opaque_eps_artists(figure) if eps else nullcontext():
                figure.savefig(
                    output,
                    dpi=EXPORT_DPI,
                    facecolor="white",
                    bbox_inches=None,
                    metadata={"Creator": "CANNES - OSCAR/MASBAL post-processing"},
                )
    finally:
        figure.set_size_inches(*original_size, forward=False)
