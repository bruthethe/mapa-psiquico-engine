"""Consolidação — apura os votos dos 10 motores e elege o dominant archetype ID final."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.core.ids import MasterLabel, get_master_label
from app.core.temporal import TemporalStatus


@dataclass(frozen=True)
class ConsolidationResult:
    id_dominante: int                    # ID eleito (ponto A ou hora exata)
    id_dominante_b: int | None           # ID eleito do ponto B — apenas em Status HYBRID com A≠B
    status: TemporalStatus
    master_label: MasterLabel | None     # preenchido se id_dominante for 11 ou 33
    master_label_b: MasterLabel | None   # preenchido se id_dominante_b for 11 ou 33


def _elect(votes_fase1: list[int], votes_fase2: list[int]) -> int:
    """
    Elege o dominant archetype ID a partir dos votos das duas fases.

    Regras de desempate (em ordem):
    1. ID mais frequente no total de votos
    2. Em empate: preferência a IDs com ao menos um voto na Fase 1
    3. Em empate persistente: menor valor numérico
    """
    all_votes = votes_fase1 + votes_fase2
    if not all_votes:
        raise ValueError("Nenhum voto fornecido para consolidação.")

    freq = Counter(all_votes)
    max_freq = max(freq.values())
    candidates = [id_ for id_, count in freq.items() if count == max_freq]

    if len(candidates) == 1:
        return candidates[0]

    # Tiebreaker 1: preferência por IDs presentes na Fase 1 (temporal)
    fase1_set = set(votes_fase1)
    fase1_candidates = [id_ for id_ in candidates if id_ in fase1_set]
    if fase1_candidates:
        candidates = fase1_candidates

    # Tiebreaker 2: menor ID numérico
    return min(candidates)


def consolidate(
    votes_fase1: list[int],
    votes_fase2: list[int],
    votes_fase1_b: list[int] | None = None,
) -> ConsolidationResult:
    """
    Consolida os votos dos 10 motores e elege o dominant archetype ID.

    Args:
        votes_fase1:   5 votos dos motores temporais (ponto A ou hora exata)
        votes_fase2:   4 votos dos motores nominais
        votes_fase1_b: 5 votos do ponto B — fornecido apenas em dual-check (Status 1/2)

    Returns:
        ConsolidationResult com ID(s) eleito(s), status e label de mestre se aplicável.
    """
    id_a = _elect(votes_fase1, votes_fase2)

    if votes_fase1_b is None:
        return ConsolidationResult(
            id_dominante=id_a,
            id_dominante_b=None,
            status=TemporalStatus.EXACT,
            master_label=get_master_label(id_a),
            master_label_b=None,
        )

    id_b = _elect(votes_fase1_b, votes_fase2)

    if id_a == id_b:
        return ConsolidationResult(
            id_dominante=id_a,
            id_dominante_b=None,
            status=TemporalStatus.SAFE,
            master_label=get_master_label(id_a),
            master_label_b=None,
        )

    return ConsolidationResult(
        id_dominante=id_a,
        id_dominante_b=id_b,
        status=TemporalStatus.HYBRID,
        master_label=get_master_label(id_a),
        master_label_b=get_master_label(id_b),
    )
