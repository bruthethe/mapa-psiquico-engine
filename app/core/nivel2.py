"""Nível 2 — Lookups de arquétipos, panteões e sombra Goética por ID."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.ids import MasterLabel, get_master_label
from app.core.report_loader import lookup

_PANTEAO_SOURCES: tuple[str, ...] = (
    "panteao-arcanjo",
    "panteao-dogon",
    "panteao-egipcio",
    "panteao-grego",
    "panteao-inca",
    "panteao-inuit",
    "panteao-ioruba",
    "panteao-maia",
    "panteao-maori",
    "panteao-nordico",
    "panteao-norte-americano",
    "panteao-tao",
    "panteao-tupi-guarani",
    "panteao-xinto",
)

_ARQUETIPOS_SOURCE = "data-mapa-arquetipos"
_GOETIA_SOURCE = "sombra-goetia"


@dataclass(frozen=True)
class ArquetipoData:
    essencia_solar: str    # "O Rei"
    mascara: str           # "O Herói"
    refugio_lunar: str     # "O Soberano"
    necessidade: str       # "Precisa de Validação"
    master_label: MasterLabel | None


@dataclass(frozen=True)
class PanteoesData:
    divindades: dict[str, str]   # panteao_name → divindade (ex: "grego" → "Apolo")
    master_label: MasterLabel | None


@dataclass(frozen=True)
class GoetiaData:
    demonio: str
    master_label: MasterLabel | None


def lookup_arquetipos(id_: int) -> ArquetipoData:
    """Retorna Essência Solar, Máscara, Refúgio Lunar e Necessidade para o ID."""
    entry = lookup(_ARQUETIPOS_SOURCE, id_)
    return ArquetipoData(
        essencia_solar=entry["sol"]["essencia"],
        mascara=entry["sol"]["mascara"],
        refugio_lunar=entry["lua"]["refugio"],
        necessidade=entry["lua"]["necessidade"],
        master_label=get_master_label(id_),
    )


def lookup_panteoes(id_: int) -> PanteoesData:
    """Retorna a divindade correspondente ao ID em cada um dos 14 panteões."""
    divindades = {
        src.removeprefix("panteao-"): lookup(src, id_)
        for src in _PANTEAO_SOURCES
    }
    return PanteoesData(divindades=divindades, master_label=get_master_label(id_))


def lookup_goetia(id_: int) -> GoetiaData:
    """Retorna o demônio arquetípico (sombra Goética) correspondente ao ID."""
    return GoetiaData(
        demonio=lookup(_GOETIA_SOURCE, id_),
        master_label=get_master_label(id_),
    )
