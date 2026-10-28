
"""Indicadores de chegada derivados dos resultados MASBAL."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ArrivalTimes:
    surface_time: float | None
    coast_time: float | None


def calculate_arrival_times(
    time: np.ndarray,
    surface_mass: np.ndarray,
    stranded_mass: np.ndarray,
) -> ArrivalTimes:
    """Determina os primeiros registros com massa positiva."""

    time = np.asarray(time, dtype=float)
    surface_mass = np.asarray(surface_mass, dtype=float)
    stranded_mass = np.asarray(stranded_mass, dtype=float)

    arrays = (time, surface_mass, stranded_mass)

    if any(array.ndim != 1 for array in arrays):
        raise ValueError("As séries MASBAL devem ser unidimensionais.")

    if time.size == 0 or any(
        array.size != time.size for array in arrays
    ):
        raise ValueError("Séries MASBAL vazias ou incompatíveis.")

    if any(not np.isfinite(array).all() for array in arrays):
        raise ValueError("As séries MASBAL contêm valores não finitos.")

    if np.any(np.diff(time) < 0):
        raise ValueError("O tempo MASBAL deve estar ordenado.")

    def first_arrival(mass: np.ndarray) -> float | None:
        indices = np.flatnonzero(mass > 0.0)

        if indices.size == 0:
            return None

        return float(time[indices[0]])

    return ArrivalTimes(
        surface_time=first_arrival(surface_mass),
        coast_time=first_arrival(stranded_mass),
    )

