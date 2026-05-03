"""Motor Pitagórica (Numerologia) — calcula IDs do nome e data via tabela pitagórica."""

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


@lru_cache(maxsize=1)
def _conversion_table() -> dict[str, int]:
    """Tabela pitagórica invertida: letra maiúscula → valor (1–9)."""
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-pitagoras.json")
        .read_text(encoding="utf-8")
    )
    table: dict[str, int] = {}
    for val_str, letters in raw["configuracao_sistema"]["tabela_conversao_pitagorica"].items():
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
    Converte nome em lista de (letra_base_normalizada, valor_pitagórico).
    Espaços, hífens e caracteres sem mapeamento são ignorados.
    """
    table = _conversion_table()
    result: list[tuple[str, int]] = []
    for c in name:
        base = normalize_letter(c)
        if base in table:
            result.append((base, table[base]))
    return result


def caminho_vida(data_nascimento: date) -> int:
    """
    Reduz cada componente da data separadamente antes de somar,
    preservando mestres (11, 22, 33) que possam aparecer em cada componente.
    """
    dia = theosophic_reduce(data_nascimento.day)
    mes = theosophic_reduce(data_nascimento.month)
    ano = theosophic_reduce(sum(int(d) for d in str(data_nascimento.year)))
    return theosophic_reduce(dia + mes + ano)


@dataclass(frozen=True)
class PitagoricaResult:
    id_alma: int             # soma vogais nome batismo
    id_persona: int          # soma consoantes nome batismo
    id_expressao: int        # soma total nome batismo
    id_vibe_atual: int       # soma total nome social
    ajuste_frequencia: int   # id_expressao − id_vibe_atual (signed, não reduzido)
    caminho_vida: int        # soma reduzida da data de nascimento
    vote: int                # caminho_vida com redirecionamentos de ID aplicados
    overall_status: TemporalStatus


def calculate_pitagorica(
    nome_batismo: str,
    data_nascimento: date,
    nome_social: str | None = None,
) -> PitagoricaResult:
    """
    Calcula os IDs pitagóricos de nome e data.

    Args:
        nome_batismo:    nome completo da certidão (acentos aceitos)
        data_nascimento: data de nascimento
        nome_social:     nome de uso atual; se None, usa nome_batismo

    Returns:
        PitagoricaResult com todos os IDs calculados.
    """
    lv = name_to_values(nome_batismo)

    id_alma = theosophic_reduce(sum(v for letra, v in lv if letra in _VOWELS))
    id_persona = theosophic_reduce(sum(v for letra, v in lv if letra not in _VOWELS))
    id_expressao = theosophic_reduce(sum(v for _, v in lv))

    social = nome_social if nome_social else nome_batismo
    id_vibe_atual = theosophic_reduce(sum(v for _, v in name_to_values(social)))

    cv = caminho_vida(data_nascimento)

    return PitagoricaResult(
        id_alma=id_alma,
        id_persona=id_persona,
        id_expressao=id_expressao,
        id_vibe_atual=id_vibe_atual,
        ajuste_frequencia=id_expressao - id_vibe_atual,
        caminho_vida=cv,
        vote=lookup_id(cv),
        overall_status=TemporalStatus.EXACT,
    )
