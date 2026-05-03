"""Motor Gematria — transliteração PT→Hebraico/Grego e cálculo de IDs nominais."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id, theosophic_reduce
from app.core.temporal import TemporalStatus

_DIGRAPHS: frozenset[str] = frozenset({"lh", "nh", "ch", "rr", "ss"})


@lru_cache(maxsize=1)
def _tables() -> tuple[dict[str, int], dict[str, int]]:
    """Retorna (tabela_hebraica, tabela_grega): token → valor numérico."""
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-gematria.json")
        .read_text(encoding="utf-8")
    )
    heb = {k: v["valor"] for k, v in raw["transliteracao_hebraica"]["tabela"].items()}
    gre = {k: v["valor"] for k, v in raw["transliteracao_grega"]["tabela"].items()}
    return heb, gre


def tokenize(name: str) -> list[str]:
    """
    Segmenta o nome em tokens prontos para transliteração.

    Ordem de prioridade:
    1. Dígrafos: lh, nh, ch, rr, ss
    2. qu antes de e/i → token "k" (u mudo)
    3. c antes de e/i → token "ce" ou "ci" (som sibilante)
    4. ç → token "ç" (Samekh/Sigma, não Kaph/Kappa)
    5. Demais: strip de diacríticos NFD, emite letra base
    """
    tokens: list[str] = []
    s = name.lower()
    i = 0
    while i < len(s):
        two = s[i : i + 2]
        # Dígrafos (maior prioridade)
        if two in _DIGRAPHS:
            tokens.append(two)
            i += 2
            continue
        # "qu" antes de e/i → K simples (u mudo)
        if two == "qu" and i + 2 < len(s) and s[i + 2] in "ei":
            tokens.append("k")
            i += 2
            continue
        c = s[i]
        # "c" antes de e/i → som sibilante (Samekh/Sigma)
        if c == "c" and i + 1 < len(s) and s[i + 1] in "ei":
            tokens.append("c" + s[i + 1])
            i += 2
            continue
        # ç → token próprio (não normalizar para 'c' que mapearia para Kaph)
        if c == "ç":
            tokens.append("ç")
            i += 1
            continue
        # Demais: remover diacríticos e emitir letra base
        base = "".join(
            ch for ch in unicodedata.normalize("NFD", c)
            if unicodedata.category(ch) != "Mn"
        )
        if base and base.isalpha():
            tokens.append(base)
        i += 1
    return tokens


def _sum_tokens(tokens: list[str], table: dict[str, int]) -> int:
    """Soma os valores numéricos de uma lista de tokens segundo a tabela dada."""
    return sum(table.get(t, 0) for t in tokens)


@dataclass(frozen=True)
class GematriaResult:
    id_hebraico: int     # soma hebraica reduzida teosoficamente
    id_grego: int        # soma grega reduzida teosoficamente
    vote: int            # lookup_id do ID do alfabeto com maior soma bruta
    overall_status: TemporalStatus


def calculate_gematria(nome_batismo: str) -> GematriaResult:
    """
    Transliterar nome PT→Hebraico e PT→Grego, somar valores, reduzir.

    O voto é determinado pelo alfabeto cuja soma bruta (pré-redução) for maior.
    Em empate, Grego é usado como desempate.

    Args:
        nome_batismo: nome completo da certidão (acentos aceitos)

    Returns:
        GematriaResult com IDs hebraico, grego e voto.
    """
    heb_table, gre_table = _tables()
    tokens = tokenize(nome_batismo)

    raw_heb = _sum_tokens(tokens, heb_table)
    raw_gre = _sum_tokens(tokens, gre_table)

    id_heb = theosophic_reduce(raw_heb)
    id_gre = theosophic_reduce(raw_gre)

    dominant_id = id_gre if raw_gre >= raw_heb else id_heb

    return GematriaResult(
        id_hebraico=id_heb,
        id_grego=id_gre,
        vote=lookup_id(dominant_id),
        overall_status=TemporalStatus.EXACT,
    )
