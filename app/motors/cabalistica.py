"""Motor Cabalística (Numerologia) — calcula IDs do nome e data via tabela cabalística."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id, theosophic_reduce
from app.core.temporal import TemporalStatus

_VOWELS: frozenset[str] = frozenset("AEIOU")
_KARMIC_DEBT_NUMBERS: frozenset[int] = frozenset({13, 14, 16, 19})


@lru_cache(maxsize=1)
def _conversion_table() -> dict[str, int]:
    """Tabela cabalística invertida: letra maiúscula → valor (1–8)."""
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-cabala.json")
        .read_text(encoding="utf-8")
    )
    table: dict[str, int] = {}
    for val_str, letters in raw["configuracao_sistema"]["tabela_conversao_cabalistica"].items():
        for letter in letters:
            table[letter] = int(val_str)
    return table


def normalize_letter(c: str) -> str:
    """Converte um caractere PT para letra base ASCII maiúscula (remove acentos)."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", c.upper())
        if unicodedata.category(ch) != "Mn"
    )


def name_to_values(name: str) -> list[tuple[str, int]]:
    """
    Converte nome em lista de (letra_base_normalizada, valor_cabalístico).
    Espaços, hífens e caracteres sem mapeamento cabalístico (ex: J) são ignorados.
    """
    table = _conversion_table()
    result: list[tuple[str, int]] = []
    for c in name:
        base = normalize_letter(c)
        if base in table:
            result.append((base, table[base]))
    return result


def missao_vida(data_nascimento: date) -> int:
    """
    Soma todos os dígitos de DDMMYYYY de uma vez e reduz teosoficamente.
    Difere da Pitagórica que reduz cada componente separadamente antes de somar.
    """
    digits_str = (
        f"{data_nascimento.day:02d}"
        f"{data_nascimento.month:02d}"
        f"{data_nascimento.year:04d}"
    )
    return theosophic_reduce(sum(int(d) for d in digits_str))


@dataclass(frozen=True)
class CabalisticaResult:
    id_motivacao: int               # vogais — o que a alma busca
    id_impressao: int               # consoantes — ego social
    id_expressao: int               # nome completo — talento manifestado
    missao_vida: int                # soma de todos os dígitos da data
    dividas_karmicas: frozenset[int]  # subcálculos que tocaram 13, 14, 16 ou 19
    vote: int                       # missao_vida com redirecionamentos de ID aplicados
    overall_status: TemporalStatus


def calculate_cabalistica(
    nome_batismo: str,
    data_nascimento: date,
) -> CabalisticaResult:
    """
    Calcula os IDs cabalísticos de nome e data.

    Args:
        nome_batismo:    nome completo da certidão (acentos aceitos)
        data_nascimento: data de nascimento

    Returns:
        CabalisticaResult com todos os IDs calculados.
    """
    lv = name_to_values(nome_batismo)

    raw_motivacao = sum(v for letra, v in lv if letra in _VOWELS)
    raw_impressao = sum(v for letra, v in lv if letra not in _VOWELS)
    raw_expressao = sum(v for _, v in lv)

    digits_str = (
        f"{data_nascimento.day:02d}"
        f"{data_nascimento.month:02d}"
        f"{data_nascimento.year:04d}"
    )
    raw_missao = sum(int(d) for d in digits_str)

    karmics = frozenset(
        n for n in (raw_motivacao, raw_impressao, raw_expressao, raw_missao)
        if n in _KARMIC_DEBT_NUMBERS
    )

    mv = theosophic_reduce(raw_missao)

    return CabalisticaResult(
        id_motivacao=theosophic_reduce(raw_motivacao),
        id_impressao=theosophic_reduce(raw_impressao),
        id_expressao=theosophic_reduce(raw_expressao),
        missao_vida=mv,
        dividas_karmicas=karmics,
        vote=lookup_id(mv),
        overall_status=TemporalStatus.EXACT,
    )
