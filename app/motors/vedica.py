"""
Motor Védico (Jyotish).

Calcula Nakshatra lunar, Pada, Atmakaraka e Purushartha a partir da posição
sidereal da Lua (ayanamsa Lahiri) e dos 7 grahas principais.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache

from app.core.config import data_path
from app.core.ephemeris import Planet, sidereal_longitude
from app.core.ids import lookup_id
from app.core.motor_types import AtmakarakaResult, NakshatraResult, VedicaResult
from app.core.temporal import TemporalStatus, TimeInput, local_to_utc, resolve_status

# 360° ÷ 27 Nakshatras = 13°20' por Nakshatra
_NK_SPAN: float = 360.0 / 27
# 13°20' ÷ 4 Padas = 3°20' por Pada
_PADA_SPAN: float = _NK_SPAN / 4

# Purusharthas derivados pelo ciclo sequencial padrão do Jyotish (index % 4)
_PURUSHARTHAS = ("Dharma", "Artha", "Kama", "Moksha")

# 7 grahas usados no Atmakaraka (Rahu e Ketu são excluídos)
_AK_PLANETS: list[tuple[Planet, str]] = [
    (Planet.SUN,     "surya"),
    (Planet.MOON,    "chandra"),
    (Planet.MARS,    "mangala"),
    (Planet.MERCURY, "budha"),
    (Planet.JUPITER, "guru"),
    (Planet.VENUS,   "shukra"),
    (Planet.SATURN,  "shani"),
]


@lru_cache(maxsize=1)
def _load_data() -> dict:
    path = data_path() / "chapters-sources" / "data-vedica.json"
    return json.loads(path.read_text(encoding="utf-8"))["data_master_vedica"]


def _nakshatra_index(sidereal_lon: float) -> int:
    """Converte longitude sidereal (0–360°) em índice de Nakshatra (0–26)."""
    return int(sidereal_lon / _NK_SPAN) % 27


def _pada(sidereal_lon: float) -> int:
    """Retorna o Pada (1–4) dentro do Nakshatra."""
    pos_in_nk = sidereal_lon % _NK_SPAN
    return int(pos_in_nk / _PADA_SPAN) + 1


def _purushartha(nakshatra_idx: int) -> str:
    """Deriva o Purushartha pelo ciclo sequencial Dharma/Artha/Kama/Moksha."""
    return _PURUSHARTHAS[nakshatra_idx % 4]



def _calc_nakshatra(sidereal_lon: float) -> tuple[int, int, dict]:
    """Retorna (nakshatra_index, pada, nakshatra_dict) para uma longitude."""
    idx = _nakshatra_index(sidereal_lon)
    pada = _pada(sidereal_lon)
    nk = _load_data()["nakshatras"][idx]
    return idx, pada, nk


def _calc_atmakaraka(dt_utc: datetime) -> AtmakarakaResult:
    """Planeta com maior grau dentro do signo entre os 7 grahas (exclui Rahu/Ketu)."""
    best_graha = ""
    best_degree = -1.0

    for planet, name in _AK_PLANETS:
        pos = sidereal_longitude(planet, dt_utc)
        degree_in_sign = pos.longitude % 30
        if degree_in_sign > best_degree:
            best_degree = degree_in_sign
            best_graha = name

    id_bruto = _load_data()["grahas_principais"][best_graha]["id_gatilho"]
    return AtmakarakaResult(
        graha=best_graha,
        id_gatilho=lookup_id(id_bruto),
        grau_no_signo=best_degree,
    )


def calculate_vedica(
    birth_date: date,
    time_input: TimeInput,
    tz_name: str,
) -> VedicaResult:
    """
    Calcula Nakshatra lunar, Pada, Atmakaraka e Purushartha.

    Args:
        birth_date: data de nascimento (horário local)
        time_input: modo temporal — hora de nascimento
        tz_name:    fuso IANA do local de nascimento

    Returns:
        VedicaResult com Nakshatra (+ Status) e Atmakaraka.
    """
    dt_a = local_to_utc(datetime.combine(birth_date, time_input.point_a), tz_name)
    dt_b = local_to_utc(datetime.combine(birth_date, time_input.point_b), tz_name)

    moon_a = sidereal_longitude(Planet.MOON, dt_a)
    moon_b = sidereal_longitude(Planet.MOON, dt_b)

    idx_a, pada_a, nk_a = _calc_nakshatra(moon_a.longitude)
    idx_b, pada_b, nk_b = _calc_nakshatra(moon_b.longitude)

    id_a = lookup_id(nk_a["id_gatilho"])
    id_b = lookup_id(nk_b["id_gatilho"])

    status = resolve_status(time_input, id_a, id_b)
    hybrid = status == TemporalStatus.HYBRID

    nakshatra = NakshatraResult(
        index=idx_a,
        nome=nk_a["nome"],
        id_gatilho=id_a,
        regente=nk_a["regente"],
        pada=pada_a,
        purushartha=_purushartha(idx_a),
        simbolo=nk_a["simbolo"],
        deidade=nk_a["deidade"],
        qualidade=nk_a["qualidade"],
        status=status,
        nome_b=nk_b["nome"] if hybrid else None,
        id_gatilho_b=id_b if hybrid else None,
        pada_b=pada_b if hybrid else None,
    )

    # Atmakaraka calculado em point_a (posição primária)
    atmakaraka = _calc_atmakaraka(dt_a)

    return VedicaResult(
        nakshatra=nakshatra,
        atmakaraka=atmakaraka,
        vote=id_a,
        vote_b=id_b if hybrid else None,
        overall_status=status,
    )
