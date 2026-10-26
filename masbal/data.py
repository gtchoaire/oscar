"""Leitura de arquivos MASBAL e metadados de simulação."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import LABELS

UNKNOWN = "Não identificado"


@dataclass(frozen=True)
class SimulationMetadata:
    """Facetas extraídas do nome, sem abrir o arquivo de dados."""

    oil: str
    treatment_group: str
    treatment_detail: str
    semester: str
    criterion: str
    title: str


def _treatment_name(token: str) -> tuple[str, str]:
    """Classifica tratamentos conhecidos; novas convenções ficam aqui."""
    normalized = re.sub(r"[\s_-]+", "", token).casefold()
    ssmd = re.fullmatch(r"(?:ssmd)?(45|50|55)(?:wj)?", normalized)
    if ssmd:
        return "SSMD", f"SSMD {ssmd.group(1)}WJ"
    if normalized.startswith("ssmd"):
        return "SSMD", token.replace("_", " ").upper()
    if normalized in {"untreated", "untrated", "semtratamento", "none"}:
        return "Sem tratamento", "Sem tratamento"
    # Convenção observada no conjunto atual: Corexit e Finasol são produtos
    # de dispersão química e entram no grupo SSDI. Edite este mapa se a
    # classificação científica do seu conjunto de dados for diferente.
    if normalized in {"corexit", "finasol"}:
        return "SSDI", token[:1].upper() + token[1:]
    if normalized.startswith("ssdi"):
        return "SSDI", token.replace("_", " ").upper()
    return "Outro tratamento", token.replace("_", " ")[:1].upper() + token.replace("_", " ")[1:]


def simulation_metadata(path: Path) -> SimulationMetadata:
    """Lê óleo, tratamento, semestre e critério do nome MASBAL."""
    stem = re.sub(r"(?i)(?:\.masbal)?\.(?:log|txt)$", "", path.name)
    match = re.fullmatch(r"(.+)_([12])_(AS|MM)_(.+)", stem, flags=re.IGNORECASE)
    if match is None:
        readable = stem.replace("_", " ")
        return SimulationMetadata(readable, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, readable)

    oil, semester, criterion, treatment = match.groups()
    oil_name = " ".join(part[:1].upper() + part[1:] for part in oil.split("_"))
    group, detail = _treatment_name(treatment)
    criterion_code = criterion.upper()
    criterion_name = "ASHORE" if criterion_code == "AS" else "More Mass"
    title = f"{oil_name} · {detail} · {semester}º sem. · {criterion_name}"
    return SimulationMetadata(oil_name, group, detail, semester, criterion_code, title)


def simulation_title(path: Path) -> str:
    """Título da simulação, partilhado por seleção, filtros e gráficos."""
    return simulation_metadata(path).title


def split_column(column: str) -> tuple[str, str]:
    """Separa ``nome(unidade)`` sem depender de nomes fixos."""
    column = column.strip()
    if column.endswith(")") and "(" in column:
        name, unit = column.rsplit("(", 1)
        return name.strip(), unit[:-1].strip()
    return column, ""


def load_table(path: Path) -> tuple[np.ndarray, list[str], str, str, str]:
    """Lê um MASBAL, valida sua estrutura e preserva a ordem original."""
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with path.open("r", encoding="utf-8-sig") as stream:
        header = stream.readline().strip()
    columns = [split_column(item) for item in header.split(",")]
    if len(columns) < 2:
        raise ValueError("O arquivo precisa ter ao menos duas colunas separadas por vírgula.")

    names = [name for name, _unit in columns]
    if any(not name for name in names):
        raise ValueError(f"Cabeçalho contém nomes de colunas vazios: {path.name}")
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError(f"Cabeçalho contém nomes de colunas duplicados: {path.name}")

    time_name, time_unit = columns[0]
    mass_units = [unit for _name, unit in columns[1:]]
    if not time_unit or any(not unit for unit in mass_units):
        raise ValueError(f"Todas as colunas precisam declarar unidades: {path.name}")
    if len(set(mass_units)) != 1:
        raise ValueError(f"Unidades de massa incompatíveis no arquivo: {path.name}")

    data = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    if data.size == 0:
        raise ValueError(f"O arquivo não contém registros numéricos: {path.name}")
    if data.shape[1] != len(columns):
        raise ValueError(
            f"Cabeçalho com {len(columns)} colunas, mas os dados possuem {data.shape[1]}."
        )
    if not np.all(np.isfinite(data)):
        raise ValueError(f"O arquivo contém valores não finitos: {path.name}")
    if np.any(np.diff(data[:, 0]) < 0):
        raise ValueError(f"Tempo decrescente no arquivo: {path.name}")
    if np.any(data[:, 1:] < 0):
        raise ValueError(f"Massas negativas no arquivo: {path.name}")

    # Tempos repetidos são preservados: a precisão textual pode causar empates.
    return data, names[1:], time_name, time_unit, mass_units[0]


def format_br(value: float, decimals: int = 4) -> str:
    """Formata decimal com vírgula e remove zeros decimais desnecessários."""
    text = f"{value:,.{decimals}f}"
    text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    return text.rstrip("0").rstrip(",") if "," in text else text


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
