"""Motor I Ching — lookup do hexagrama via Porta do Sol de Personalidade (Human Design)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus

_FALLBACK_HEXAGRAMA = 1


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
    hexagrama: int       # número do hexagrama consultado (Porta do Sol de Personalidade)
    nome: str            # nome do hexagrama
    sentenca: str        # sentença oracular
    id_gatilho: int      # ID arquetípico do hexagrama
    vote: int            # lookup_id(id_gatilho) — contribuição para consolidação
    fallback: bool       # True se hexagrama não estava na tabela e usou o fallback
    overall_status: TemporalStatus


def calculate_iching(porta_sol_personalidade: int) -> IChingResult:
    """
    Faz lookup do hexagrama correspondente à Porta do Sol de Personalidade do HD.

    A tabela cobre 12 hexagramas de referência. Para portais não mapeados,
    aplica fallback para o hexagrama 1 (Resiliência Total — sistema nunca retorna erro).

    Args:
        porta_sol_personalidade: inteiro 1–64 retornado pelo motor Human Design

    Returns:
        IChingResult com hexagrama, sentença, ID arquetípico e voto.
    """
    table = _hexagramas_table()
    key = str(porta_sol_personalidade)
    fallback = key not in table

    entry = table[key if not fallback else str(_FALLBACK_HEXAGRAMA)]
    id_gatilho = entry["id_gatilho"]

    return IChingResult(
        hexagrama=porta_sol_personalidade,
        nome=entry["nome"],
        sentenca=entry["sentenca"],
        id_gatilho=id_gatilho,
        vote=lookup_id(id_gatilho),
        fallback=fallback,
        overall_status=TemporalStatus.EXACT,
    )
