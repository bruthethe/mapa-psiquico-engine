"""Motor Caldeia (Numerologia) — calcula IDs do nome e data via tabela caldeia."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from app.core.config import data_path
from app.core.ids import lookup_id, theosophic_reduce
from app.core.temporal import TemporalStatus


@lru_cache(maxsize=1)
def _conversion_table() -> dict[str, int]:
    """Tabela caldeia invertida: letra maiúscula → valor (1–8; 9 não é atribuído)."""
    raw = json.loads(
        (data_path() / "chapters-sources" / "data-caldeia.json")
        .read_text(encoding="utf-8")
    )
    table: dict[str, int] = {}
    for val_str, letters in raw["configuracao_sistema"]["tabela_conversao_caldeia"].items():
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
    Converte nome em lista de (letra_base_normalizada, valor_caldeu).
    Espaços, hífens e caracteres sem mapeamento são ignorados.
    Diferença da Cabalística: J=1 existe na tabela caldeia.
    """
    table = _conversion_table()
    result: list[tuple[str, int]] = []
    for c in name:
        base = normalize_letter(c)
        if base in table:
            result.append((base, table[base]))
    return result


def vibracao_psiquica(dia_nascimento: int) -> int:
    """Reduz teosoficamente apenas o dia de nascimento."""
    return theosophic_reduce(dia_nascimento)


@dataclass(frozen=True)
class CaldeiaResult:
    id_nome: int             # soma total das letras do nome batismo, reduzida
    vibracao_psiquica: int   # dia de nascimento reduzido teosoficamente
    numero_destino: int      # soma bruta do nome + soma bruta dos dígitos da data, reduzida
    vote: int                # numero_destino com redirecionamentos de ID aplicados
    overall_status: TemporalStatus


def calculate_caldeia(
    nome_batismo: str,
    data_nascimento: date,
) -> CaldeiaResult:
    """
    Calcula os IDs caldeus de nome e data.

    Args:
        nome_batismo:    nome completo da certidão (acentos aceitos)
        data_nascimento: data de nascimento

    Returns:
        CaldeiaResult com todos os IDs calculados.
    """
    lv = name_to_values(nome_batismo)
    raw_nome = sum(v for _, v in lv)

    digits_str = (
        f"{data_nascimento.day:02d}"
        f"{data_nascimento.month:02d}"
        f"{data_nascimento.year:04d}"
    )
    raw_data = sum(int(d) for d in digits_str)

    nd = theosophic_reduce(raw_nome + raw_data)

    return CaldeiaResult(
        id_nome=theosophic_reduce(raw_nome),
        vibracao_psiquica=vibracao_psiquica(data_nascimento.day),
        numero_destino=nd,
        vote=lookup_id(nd),
        overall_status=TemporalStatus.EXACT,
    )
