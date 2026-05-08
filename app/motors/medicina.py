"""Motor Medicina — lookup do chakra e sistema biológico a partir do dominant archetype ID."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus

_FALLBACK_CHAKRA = "Coronario"


@lru_cache(maxsize=1)
def _chakras_table() -> dict[str, dict]:
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-medicina.json")
        .read_text(encoding="utf-8")
    )
    return raw["data_master_medicina"]["centros_de_forca"]


@lru_cache(maxsize=1)
def _id_to_chakra_map() -> dict[int, str]:
    """Índice inverso: id_gatilho → nome do chakra."""
    return {v["id_gatilho"]: k for k, v in _chakras_table().items()}


@dataclass(frozen=True)
class MedicinaResult:
    chakra: str          # nome do centro de força (ex: "Frontal")
    sistema: str         # sistema biológico associado
    frequencia: str      # frequência Hz do chakra
    id_gatilho: int      # id_gatilho do chakra encontrado
    fallback: bool       # True se dominant archetype ID não tinha chakra direto
    overall_status: TemporalStatus


def calculate_medicina(id_dominante: int) -> MedicinaResult:
    """
    Faz lookup do chakra correspondente ao dominant archetype ID.

    A tabela cobre IDs: 1, 2, 3, 4, 5, 6, 11.
    Para IDs sem chakra direto (ex: 7, 9, 33), aplica fallback para Coronario
    (sistema nunca retorna erro).

    Args:
        id_dominante: dominant archetype ID eleito pela consolidação (já pós-lookup_id)

    Returns:
        MedicinaResult com chakra, sistema biológico e frequência.
    """
    id_map = _id_to_chakra_map()
    fallback = id_dominante not in id_map
    chakra_nome = id_map.get(id_dominante, _FALLBACK_CHAKRA)
    entry = _chakras_table()[chakra_nome]

    return MedicinaResult(
        chakra=chakra_nome,
        sistema=entry["sistema"],
        frequencia=entry["frequencia"],
        id_gatilho=entry["id_gatilho"],
        fallback=fallback,
        overall_status=TemporalStatus.EXACT,
    )
