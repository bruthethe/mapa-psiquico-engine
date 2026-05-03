"""
Motor Tzolkin Maya (Dreamspell) — Épica 2, História 2.4.

Calcula Kin, Selo Solar, Tom Lunar e Oráculo da Quinta Força segundo a
correlação Dreamspell (José Argüelles). Referência: 1987-07-26 = Kin 1.

Tzolkin é puramente baseado na data — sem protocolo temporal.
"""

from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus

# Referência Dreamspell: 1987-07-26 = Kin 1 (Dragão Magnético)
_REF = date(1987, 7, 26)


@lru_cache(maxsize=1)
def _load_data() -> dict:
    path = data_path() / "chapters-sources" / "data-maia.json"
    return json.loads(path.read_text(encoding="utf-8"))["data_master_maia"]


def _selo_by_pos(pos: int) -> dict:
    """Retorna o dict do Selo pela posição (1–20)."""
    return _load_data()["os_20_selos"][pos - 1]


def _tom_by_num(tom: int) -> dict:
    """Retorna o dict do Tom Lunar pelo número (1–13)."""
    return _load_data()["os_13_tons_lunares"][tom - 1]


# ── Contagem de dias Dreamspell ────────────────────────────────────────────────


def _count_feb29(start: date, end: date) -> int:
    """Número de ocorrências de 29/02 no intervalo semi-aberto [start, end)."""
    count = 0
    for year in range(start.year, end.year + 1):
        if calendar.isleap(year):
            feb29 = date(year, 2, 29)
            if start <= feb29 < end:
                count += 1
    return count


def dreamspell_days(birth_date: date) -> int:
    """
    Offset em dias Dreamspell de _REF até birth_date.
    Nascidos em 29/02 usam 28/02; dias 29/02 são excluídos da contagem.
    Retorna negativo para datas anteriores a _REF.
    """
    d = birth_date.replace(day=28) if (birth_date.month == 2 and birth_date.day == 29) else birth_date
    delta = (d - _REF).days
    if d >= _REF:
        return delta - _count_feb29(_REF, d)
    else:
        return delta + _count_feb29(d, _REF)


# ── Fórmulas Tzolkin ───────────────────────────────────────────────────────────


def kin_from_days(dias: int) -> int:
    """Kin (1–260) a partir do offset em dias Dreamspell."""
    return ((dias % 260) + 260) % 260 + 1


def tom_from_kin(kin: int) -> int:
    """Tom Lunar (1–13) a partir do Kin."""
    return (kin - 1) % 13 + 1


def selo_pos_from_kin(kin: int) -> int:
    """Posição do Selo Solar (1–20) a partir do Kin."""
    return (kin - 1) % 20 + 1


# ── Oráculo da Quinta Força ───────────────────────────────────────────────────


def analogo(seal: int) -> int:
    """Selo Análogo — par de cor complementar (Vermelho↔Branco, Azul↔Amarelo)."""
    return seal + 1 if seal % 2 == 1 else seal - 1


def antipoda(seal: int) -> int:
    """Selo Antípoda — oposto, 10 posições adiante no ciclo de 20."""
    return ((seal - 1 + 10) % 20) + 1


def oculto(seal: int) -> int:
    """Selo Oculto — parceiro complementar (posição + oculto = 21)."""
    return 21 - seal


def guia(seal: int, tom: int) -> int:
    """
    Selo Guia — mesmo família de cor, posição determinada pelo Tom.
    Tom 1 (Magnético) sempre retorna o próprio Selo como Guia.
    """
    self_pos = (seal - 1) // 4
    guide_pos = (self_pos + tom - 1) % 5
    color = (seal - 1) % 4
    return guide_pos * 4 + color + 1


# ── Dataclasses de resultado ───────────────────────────────────────────────────


@dataclass(frozen=True)
class TzolkinSelo:
    posicao: int     # 1–20
    nome: str
    cor: str
    essencia: str
    id_gatilho: int  # após lookup_id()


@dataclass(frozen=True)
class TzolkinTom:
    tom: int         # 1–13
    nome: str
    poder: str
    acao: str
    essencia: str
    id_gatilho: int  # após lookup_id()


@dataclass(frozen=True)
class TzolkinOraculo:
    guia: TzolkinSelo
    analogo: TzolkinSelo
    antipoda: TzolkinSelo
    oculto: TzolkinSelo


@dataclass
class TzolkinResult:
    kin: int                  # 1–260
    selo: TzolkinSelo
    tom: TzolkinTom
    oraculo: TzolkinOraculo
    vote: int                 # selo.id_gatilho → vota no ID Dominante
    overall_status: TemporalStatus  # sempre EXACT — Tzolkin é baseado apenas na data


# ── Helpers de construção ──────────────────────────────────────────────────────


def _build_selo(pos: int) -> TzolkinSelo:
    d = _selo_by_pos(pos)
    return TzolkinSelo(
        posicao=pos,
        nome=d["nome"],
        cor=d["cor"],
        essencia=d["essencia"],
        id_gatilho=lookup_id(d["id_gatilho"]),
    )


def _build_tom(tom_num: int) -> TzolkinTom:
    d = _tom_by_num(tom_num)
    return TzolkinTom(
        tom=tom_num,
        nome=d["nome"],
        poder=d["poder"],
        acao=d["acao"],
        essencia=d["essencia"],
        id_gatilho=lookup_id(d["id_gatilho"]),
    )


# ── Função principal ───────────────────────────────────────────────────────────


def calculate_tzolkin(birth_date: date) -> TzolkinResult:
    """
    Calcula a assinatura galáctica Dreamspell de um nascimento.

    Args:
        birth_date: data de nascimento local (tempo não afeta o resultado).

    Returns:
        TzolkinResult com Kin, Selo, Tom e Oráculo da Quinta Força.
    """
    dias = dreamspell_days(birth_date)
    kin = kin_from_days(dias)
    tom_num = tom_from_kin(kin)
    seal_pos = selo_pos_from_kin(kin)

    selo = _build_selo(seal_pos)
    tom = _build_tom(tom_num)

    oraculo = TzolkinOraculo(
        guia=_build_selo(guia(seal_pos, tom_num)),
        analogo=_build_selo(analogo(seal_pos)),
        antipoda=_build_selo(antipoda(seal_pos)),
        oculto=_build_selo(oculto(seal_pos)),
    )

    return TzolkinResult(
        kin=kin,
        selo=selo,
        tom=tom,
        oraculo=oraculo,
        vote=selo.id_gatilho,
        overall_status=TemporalStatus.EXACT,
    )
