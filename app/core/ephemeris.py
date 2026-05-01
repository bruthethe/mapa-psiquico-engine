"""
Wrappers sobre o Swiss Ephemeris (pyswisseph).

Todas as funções esperam datetimes em UTC.
O path dos arquivos .se1 é resolvido via app.core.config.ephemeris_path().
"""

import threading
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

import swisseph as swe

from app.core.config import ephemeris_path

# Lock para operações que alteram estado global do Swiss Ephemeris (set_sid_mode)
_sid_lock = threading.Lock()


# ── Planetas ───────────────────────────────────────────────────────────────────


class Planet(IntEnum):
    SUN = swe.SUN
    MOON = swe.MOON
    MERCURY = swe.MERCURY
    VENUS = swe.VENUS
    MARS = swe.MARS
    JUPITER = swe.JUPITER
    SATURN = swe.SATURN
    URANUS = swe.URANUS
    NEPTUNE = swe.NEPTUNE
    PLUTO = swe.PLUTO


SIGN_NAMES: list[str] = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


@dataclass(frozen=True)
class PlanetPosition:
    planet: Planet
    longitude: float  # 0–360 graus eclípticos
    sign_index: int  # 0=Áries … 11=Peixes
    degree_in_sign: float  # 0–30


# ── Helpers internos ───────────────────────────────────────────────────────────


def _init() -> None:
    swe.set_ephe_path(str(ephemeris_path()))


def _julian_day(dt: datetime) -> float:
    """Converte datetime UTC em Julian Day Number."""
    hour_frac = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour_frac)


def _jd_to_datetime(jd: float) -> datetime:
    """Converte Julian Day Number em datetime UTC."""
    y, m, d, h = swe.jdut1_to_utc(jd, swe.GREG_CAL)
    hour = int(h)
    minute = int((h - hour) * 60)
    second = int(round(((h - hour) * 60 - minute) * 60))
    return datetime(y, m, d, hour, minute, min(second, 59))


def _make_position(planet: Planet, lon: float) -> PlanetPosition:
    return PlanetPosition(
        planet=planet,
        longitude=lon,
        sign_index=int(lon / 30),
        degree_in_sign=lon % 30,
    )


# ── API pública ────────────────────────────────────────────────────────────────


def tropical_longitude(planet: Planet, dt: datetime) -> PlanetPosition:
    """Longitude eclíptica de um planeta no zodíaco tropical."""
    _init()
    jd = _julian_day(dt)
    result, _ = swe.calc_ut(jd, int(planet))
    return _make_position(planet, result[0])


def sidereal_longitude(planet: Planet, dt: datetime) -> PlanetPosition:
    """
    Longitude eclíptica de um planeta no zodíaco sideral (ayanamsa Lahiri).

    Usa lock para proteger swe.set_sid_mode() — estado global do Swiss Ephemeris
    que causaria race condition em servidor com múltiplos workers.
    """
    _init()
    jd = _julian_day(dt)
    with _sid_lock:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        result, _ = swe.calc_ut(jd, int(planet), swe.FLG_SIDEREAL)
    return _make_position(planet, result[0])


def ascendant(dt: datetime, lat: float, lon: float) -> float:
    """
    Retorna o grau do Ascendente (0–360) para o datetime e localização dados.
    Sistema de casas: Placidus (padrão da astrologia ocidental).
    """
    _init()
    jd = _julian_day(dt)
    _, ascmc = swe.houses(jd, lat, lon, b"P")
    return ascmc[0]  # ascmc[0] = Ascendente, ascmc[1] = MC


def sunrise(dt: datetime, lat: float, lon: float) -> datetime:
    """
    Retorna o datetime UTC do nascer do Sol para a data e localização dadas.
    Busca a partir de 00:00 UTC do dia informado.
    """
    _init()
    jd = _julian_day(dt.replace(hour=0, minute=0, second=0, microsecond=0))
    _, tret = swe.rise_trans(
        jd,
        swe.SUN,
        b"",
        swe.FLG_SWIEPH,
        swe.CALC_RISE,
        (lon, lat, 0),
        1013.25,
        15.0,
    )
    return _jd_to_datetime(tret[0])


def sunset(dt: datetime, lat: float, lon: float) -> datetime:
    """
    Retorna o datetime UTC do pôr do Sol para a data e localização dadas.
    Busca a partir de 00:00 UTC do dia informado.
    """
    _init()
    jd = _julian_day(dt.replace(hour=0, minute=0, second=0, microsecond=0))
    _, tret = swe.rise_trans(
        jd,
        swe.SUN,
        b"",
        swe.FLG_SWIEPH,
        swe.CALC_SET,
        (lon, lat, 0),
        1013.25,
        15.0,
    )
    return _jd_to_datetime(tret[0])
