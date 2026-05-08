"""Motor Tarô — calcula o Arcano Maior de nascimento e o ID arquetípico correspondente."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus


@lru_cache(maxsize=1)
def _arcanos_table() -> dict[str, dict]:
    """Tabela de arcanos: string '1'–'22' → {nome, id_gatilho, arquetipo}."""
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-taro.json")
        .read_text(encoding="utf-8")
    )
    return raw["data_master_taro"]["arcanos_maiores"]


def _sum_to_arcano(day: int, month: int, year: int) -> int:
    """
    Soma DD + MM + AAAA como inteiros e reduz por soma de dígitos até atingir 1–22.
    Arcano 22 (O Louco) é preservado — não reduzido para 4.
    """
    n = day + month + year
    while n > 22:
        n = sum(int(d) for d in str(n))
    return n


@dataclass(frozen=True)
class TaroResult:
    arcano: int          # número do Arcano Maior (1–22)
    nome_arcano: str     # nome do arcano (ex: "A Justiça")
    id_gatilho: int      # ID arquetípico do arcano conforme tabela
    vote: int            # lookup_id(id_gatilho) — contribuição para consolidação
    overall_status: TemporalStatus


def calculate_taro(data_nascimento: date) -> TaroResult:
    """
    Calcula o Arcano Maior de nascimento.

    Args:
        data_nascimento: data de nascimento

    Returns:
        TaroResult com arcano, nome, ID arquetípico e voto para consolidação.
    """
    arcano = _sum_to_arcano(
        data_nascimento.day,
        data_nascimento.month,
        data_nascimento.year,
    )
    entry = _arcanos_table()[str(arcano)]
    id_gatilho = entry["id_gatilho"]

    return TaroResult(
        arcano=arcano,
        nome_arcano=entry["nome"],
        id_gatilho=id_gatilho,
        vote=lookup_id(id_gatilho),
        overall_status=TemporalStatus.EXACT,
    )
