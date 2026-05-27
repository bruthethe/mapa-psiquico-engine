"""Motor I Ching — lookup do hexagrama pelo hexagrama do Sol natal (64 portas)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus

_FALLBACK_HEXAGRAMA = 1

# Roda das 64 portas (I Ching / HD): índice 0–63, cada posição = 5,625° a partir de 0° Áries
_RODA_GATES: list[int] = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42,  3,
    27, 24,  2, 23,  8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33,  7,  4, 29, 59, 40, 64, 47,  6, 46, 18, 48, 57, 32, 50,
    28, 44,  1, 43, 14, 34,  9,  5, 26, 11, 10, 58, 38, 54, 61, 60,
]


@lru_cache(maxsize=1)
def _hexagramas_table() -> dict[str, dict]:
    """Tabela de hexagramas: string '1'–'64' → {nome, id_gatilho, sentenca}."""
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-iching.json")
        .read_text(encoding="utf-8")
    )
    return raw["biblioteca_hexagramas"]


@dataclass(frozen=True)
class IChingResult:
    hexagrama: int       # número do hexagrama (1–64)
    nome: str
    sentenca: str
    id_gatilho: int
    vote: int
    fallback: bool
    overall_status: TemporalStatus


def calculate_iching(lon_sol: float) -> IChingResult:
    """
    Deriva o hexagrama I Ching a partir da longitude eclíptica do Sol natal.

    Converte a longitude para uma das 64 portas usando a roda de portões,
    depois faz lookup na tabela de hexagramas. Para hexagramas não mapeados,
    aplica fallback para o hexagrama 1 (sistema nunca retorna erro).

    Args:
        lon_sol: longitude eclíptica tropical do Sol (0–360°)
    """
    hexagrama = _RODA_GATES[int(lon_sol / 5.625) % 64]
    table = _hexagramas_table()
    key = str(hexagrama)
    fallback = key not in table

    entry = table[key if not fallback else str(_FALLBACK_HEXAGRAMA)]
    id_gatilho = entry["id_gatilho"]

    return IChingResult(
        hexagrama=hexagrama,
        nome=entry["nome"],
        sentenca=entry["sentenca"],
        id_gatilho=id_gatilho,
        vote=lookup_id(id_gatilho),
        fallback=fallback,
        overall_status=TemporalStatus.EXACT,
    )
