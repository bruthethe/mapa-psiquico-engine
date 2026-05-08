"""Motor Alquimia — deriva a fase alquímica do signo solar e retorna o ID arquetípico."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus

# Correspondência clássica Junguiana: elemento → fase alquímica.
# Fogo=Rubedo (manifestação), Agua=Nigredo (dissolução),
# Ar=Albedo (purificação), Terra=Citrinitas (sabedoria nascente).
_ELEMENTO_FASE: dict[str, str] = {
    "Fogo": "Rubedo",
    "Agua": "Nigredo",
    "Ar": "Albedo",
    "Terra": "Citrinitas",
}

_SIGNOS_ELEMENTOS: dict[str, str] = {
    "aries": "Fogo", "touro": "Terra", "gemeos": "Ar", "cancer": "Agua",
    "leao": "Fogo", "virgem": "Terra", "libra": "Ar", "escorpiao": "Agua",
    "sagitario": "Fogo", "capricornio": "Terra", "aquario": "Ar", "peixes": "Agua",
}


@lru_cache(maxsize=1)
def _fases_table() -> dict[str, dict]:
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-alquimia.json")
        .read_text(encoding="utf-8")
    )
    return raw["data_master_alquimia"]["estagios_processamento"]


@dataclass(frozen=True)
class AlquimiaResult:
    signo_solar: str     # signo solar de entrada
    elemento: str        # elemento do signo (Fogo/Ar/Terra/Agua)
    fase: str            # fase alquímica (Nigredo/Albedo/Citrinitas/Rubedo)
    operacao: str        # operação alquímica descritiva
    vibe: str            # princípio da fase (ex: "Morte do Ego e Sombra")
    id_gatilho: int      # ID arquetípico da fase
    vote: int            # lookup_id(id_gatilho) — não participa da consolidação de IDs
    overall_status: TemporalStatus


def calculate_alquimia(signo_solar: str) -> AlquimiaResult:
    """
    Deriva a fase alquímica a partir do signo solar.

    Args:
        signo_solar: signo solar em PT (ex: "Leao", "Escorpiao")

    Returns:
        AlquimiaResult com fase, operação e ID arquetípico.
    """
    elemento = _SIGNOS_ELEMENTOS[signo_solar]
    fase = _ELEMENTO_FASE[elemento]
    entry = _fases_table()[fase]
    id_gatilho = entry["id_gatilho"]

    return AlquimiaResult(
        signo_solar=signo_solar,
        elemento=elemento,
        fase=fase,
        operacao=entry["operacao"],
        vibe=entry["vibe"],
        id_gatilho=id_gatilho,
        vote=lookup_id(id_gatilho),
        overall_status=TemporalStatus.EXACT,
    )
