"""Motor Temperamentos — calcula os temperamentos dominante e secundário pelos signos planetários."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus

_PESOS: dict[str, int] = {
    "sol": 3,
    "lua": 3,
    "ascendente": 3,
    "mercurio": 1,
    "venus": 1,
    "marte": 1,
    "jupiter": 1,
    "saturno": 1,
}


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(
        (data_path() / "chapters-sources" / "data-temperamentos.json")
        .read_text(encoding="utf-8")
    )


@lru_cache(maxsize=1)
def _signo_elemento_map() -> dict[str, str]:
    return {k.lower(): v for k, v in _data()["signos_elementos"].items()}


@lru_cache(maxsize=1)
def _elemento_id_map() -> dict[str, int]:
    """Mapa elemento → id_gatilho construído a partir do JSON."""
    d = _data()
    result: dict[str, int] = {}
    for elemento, meta in d["elementos_temperamento"].items():
        temp_name = meta["temperamento"]
        result[elemento] = d["data_master_temperamentos"]["os_quatro_tipos"][temp_name]["id_gatilho"]
    return result


@lru_cache(maxsize=1)
def _elemento_temperamento_map() -> dict[str, str]:
    return {e: v["temperamento"] for e, v in _data()["elementos_temperamento"].items()}


def _tiebreak(candidatos: list[str], sol_elemento: str | None) -> str:
    """
    Desempate entre elementos empatados:
    1. Preferência ao elemento que contém o Sol
    2. Menor id_gatilho
    """
    if sol_elemento in candidatos:
        return sol_elemento
    return min(candidatos, key=lambda e: _elemento_id_map()[e])


@dataclass(frozen=True)
class TemperamentosResult:
    elemento_dominante: str       # "Fogo", "Ar", "Terra", "Agua"
    elemento_secundario: str
    temperamento_dominante: str   # "Colerico", "Sanguineo", "Melancolico", "Fleumatico"
    temperamento_secundario: str
    pontuacao: dict[str, int]     # pontos acumulados por elemento
    id_gatilho: int               # ID do temperamento dominante
    vote: int                     # lookup_id(id_gatilho) — contribuição para consolidação
    overall_status: TemporalStatus


def calculate_temperamentos(
    posicoes: dict[str, str | None],
) -> TemperamentosResult:
    """
    Calcula os temperamentos dominante e secundário.

    Args:
        posicoes: dicionário {planet_key: signo_string}.
                  Chaves esperadas: "sol", "lua", "ascendente", "mercurio",
                  "venus", "marte", "jupiter", "saturno".
                  Valores None ou chaves ausentes são ignorados (ex: ascendente
                  desconhecido quando hora não é informada).

    Returns:
        TemperamentosResult com temperamentos, pontuação e voto.
    """
    signo_elem = _signo_elemento_map()
    scores: dict[str, int] = {"Fogo": 0, "Ar": 0, "Terra": 0, "Agua": 0}
    sol_elemento: str | None = None

    for planeta, peso in _PESOS.items():
        signo = posicoes.get(planeta)
        if not signo:
            continue
        elemento = signo_elem[signo]
        scores[elemento] += peso
        if planeta == "sol":
            sol_elemento = elemento

    # Eleger dominante
    max_score = max(scores.values())
    tied_dom = [e for e, s in scores.items() if s == max_score]
    dominante = tied_dom[0] if len(tied_dom) == 1 else _tiebreak(tied_dom, sol_elemento)

    # Eleger secundário (excluindo dominante)
    remaining = {e: s for e, s in scores.items() if e != dominante}
    sec_score = max(remaining.values())
    tied_sec = [e for e, s in remaining.items() if s == sec_score]
    secundario = tied_sec[0] if len(tied_sec) == 1 else _tiebreak(tied_sec, sol_elemento)

    id_gatilho = _elemento_id_map()[dominante]

    return TemperamentosResult(
        elemento_dominante=dominante,
        elemento_secundario=secundario,
        temperamento_dominante=_elemento_temperamento_map()[dominante],
        temperamento_secundario=_elemento_temperamento_map()[secundario],
        pontuacao=scores,
        id_gatilho=id_gatilho,
        vote=lookup_id(id_gatilho),
        overall_status=TemporalStatus.EXACT,
    )
