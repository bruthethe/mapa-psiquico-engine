"""
Motor Tropical.

Converte data/hora/local de nascimento em IDs via posições
planetárias no zodíaco tropical.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache

from app.core.config import data_path
from app.core.ephemeris import Planet, ascendant, tropical_longitude
from app.core.ids import lookup_id
from app.core.motor_types import PlanetResult, TropicalResult
from app.core.temporal import TemporalStatus, TimeInput, local_to_utc, resolve_status

# Chaves PT dos signos indexadas por sign_index (0=Áries … 11=Peixes)
_SIGN_KEYS: list[str] = [
    "aries", "touro", "gemeos", "cancer", "leao", "virgem",
    "libra", "escorpiao", "sagitario", "capricornio", "aquario", "peixes",
]

# 10 planetas na ordem canônica do Swiss Ephemeris
_ALL_PLANETS: list[tuple[Planet, str]] = [
    (Planet.SUN,     "sol"),
    (Planet.MOON,    "lua"),
    (Planet.MERCURY, "mercurio"),
    (Planet.VENUS,   "venus"),
    (Planet.MARS,    "marte"),
    (Planet.JUPITER, "jupiter"),
    (Planet.SATURN,  "saturno"),
    (Planet.URANUS,  "urano"),
    (Planet.NEPTUNE, "netuno"),
    (Planet.PLUTO,   "plutao"),
]


@lru_cache(maxsize=1)
def _load_data() -> dict:
    path = data_path() / "chapters-sources" / "data-tropical.json"
    return json.loads(path.read_text(encoding="utf-8"))["data_master_tropical"]


def _sign_to_id(sign_key: str) -> int:
    """signo → regente_principal → id_gatilho, com lookup_id() aplicado."""
    data = _load_data()
    regente = data["zodiaco"][sign_key]["regente_principal"]
    id_bruto = data["regentes_principais"][regente]["id_gatilho"]
    return lookup_id(id_bruto)




def _planet_result(
    planet: Planet,
    name: str,
    time_input: TimeInput,
    dt_a: datetime,
    dt_b: datetime,
) -> PlanetResult:
    pos_a = tropical_longitude(planet, dt_a)
    sign_a = _SIGN_KEYS[pos_a.sign_index]
    id_a = _sign_to_id(sign_a)

    pos_b = tropical_longitude(planet, dt_b)
    sign_b = _SIGN_KEYS[pos_b.sign_index]
    id_b = _sign_to_id(sign_b)

    status = resolve_status(time_input, id_a, id_b)

    return PlanetResult(
        planet=name,
        sign=sign_a,
        id_gatilho=id_a,
        status=status,
        sign_b=sign_b if status == TemporalStatus.HYBRID else None,
        id_gatilho_b=id_b if status == TemporalStatus.HYBRID else None,
        longitude=pos_a.longitude,
    )


def _ascendant_result(
    time_input: TimeInput,
    dt_a: datetime,
    dt_b: datetime,
    lat: float,
    lon: float,
) -> PlanetResult:
    lon_a = ascendant(dt_a, lat, lon)
    sign_a = _SIGN_KEYS[int(lon_a / 30) % 12]
    id_a = _sign_to_id(sign_a)

    lon_b = ascendant(dt_b, lat, lon)
    sign_b = _SIGN_KEYS[int(lon_b / 30) % 12]
    id_b = _sign_to_id(sign_b)

    status = resolve_status(time_input, id_a, id_b)

    return PlanetResult(
        planet="ascendente",
        sign=sign_a,
        id_gatilho=id_a,
        status=status,
        sign_b=sign_b if status == TemporalStatus.HYBRID else None,
        id_gatilho_b=id_b if status == TemporalStatus.HYBRID else None,
        longitude=lon_a,
    )


def calculate_tropical(
    birth_date: date,
    time_input: TimeInput,
    tz_name: str,
    lat: float | None = None,
    lon: float | None = None,
) -> TropicalResult:
    """
    Calcula posições planetárias tropicais e converte em IDs.

    Args:
        birth_date: data de nascimento (horário local)
        time_input: modo temporal — hora de nascimento
        tz_name:    fuso IANA do local de nascimento (ex: "Europe/London")
        lat:        latitude — necessária para calcular Ascendente
        lon:        longitude — necessária para calcular Ascendente

    Returns:
        TropicalResult com todos os planetas e Ascendente opcional.
    """
    dt_a = local_to_utc(datetime.combine(birth_date, time_input.point_a), tz_name)
    dt_b = local_to_utc(datetime.combine(birth_date, time_input.point_b), tz_name)

    planets: list[PlanetResult] = [
        _planet_result(planet, name, time_input, dt_a, dt_b)
        for planet, name in _ALL_PLANETS
    ]

    sol = next(p for p in planets if p.planet == "sol")
    lua = next(p for p in planets if p.planet == "lua")

    asc: PlanetResult | None = None
    if lat is not None and lon is not None:
        asc = _ascendant_result(time_input, dt_a, dt_b, lat, lon)

    overall_status = min(sol.status, lua.status)

    return TropicalResult(
        sol=sol,
        lua=lua,
        ascendente=asc,
        planets=planets,
        vote=sol.id_gatilho,
        vote_b=sol.id_gatilho_b,
        overall_status=overall_status,
    )
