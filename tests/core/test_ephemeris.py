"""
Testes de integração do wrapper Swiss Ephemeris.

Usam equinócios e solstícios do ano 2000 como dataset de referência —
eventos astronômicos com horários UTC publicados pela USNO e verificáveis
em Astro.com. Os testes são pulados automaticamente se pyswisseph não
estiver instalado (ex: Windows sem Build Tools; rode via Docker).

Critério de aceite: zero divergências de signo solar nos 5 casos.
"""

from datetime import datetime

import pytest

# Pula toda a suite se pyswisseph não estiver disponível
swe = pytest.importorskip("swisseph", reason="pyswisseph não instalado — rode via Docker")

from app.core.ephemeris import (
    Planet,
    PlanetPosition,
    ascendant,
    sidereal_longitude,
    sunrise,
    sunset,
    tropical_longitude,
)

pytestmark = pytest.mark.integration


# ── Dataset: equinócios e solstícios 2000 (UTC verificado pela USNO) ──────────
#
#   Evento               | Data/Hora UTC       | Sol entra em
#   ---------------------|---------------------|-------------
#   Equinócio de Março   | 2000-03-20 07:35    | Áries  (sign_index=0)
#   Solstício de Junho   | 2000-06-21 01:48    | Câncer (sign_index=3)
#   Equinócio de Setembro| 2000-09-22 17:28    | Libra  (sign_index=6)
#   Solstício de Dezembro| 2000-12-21 13:38    | Capricórnio (sign_index=9)


class TestTropicalLongitude:
    def test_sun_at_vernal_equinox_is_aries(self) -> None:
        dt = datetime(2000, 3, 20, 7, 35)
        pos = tropical_longitude(Planet.SUN, dt)
        assert pos.sign_index == 0, f"Esperado Áries (0), obtido {pos.sign_index} ({pos.longitude:.2f}°)"

    def test_sun_at_summer_solstice_is_cancer(self) -> None:
        dt = datetime(2000, 6, 21, 1, 48)
        pos = tropical_longitude(Planet.SUN, dt)
        assert pos.sign_index == 3, f"Esperado Câncer (3), obtido {pos.sign_index} ({pos.longitude:.2f}°)"

    def test_sun_at_autumn_equinox_is_libra(self) -> None:
        dt = datetime(2000, 9, 22, 17, 28)
        pos = tropical_longitude(Planet.SUN, dt)
        assert pos.sign_index == 6, f"Esperado Libra (6), obtido {pos.sign_index} ({pos.longitude:.2f}°)"

    def test_sun_at_winter_solstice_is_capricorn(self) -> None:
        dt = datetime(2000, 12, 21, 13, 38)
        pos = tropical_longitude(Planet.SUN, dt)
        assert pos.sign_index == 9, f"Esperado Capricórnio (9), obtido {pos.sign_index} ({pos.longitude:.2f}°)"

    def test_longitude_range_is_valid(self) -> None:
        dt = datetime(2000, 1, 1, 12, 0)
        pos = tropical_longitude(Planet.SUN, dt)
        assert 0 <= pos.longitude < 360
        assert 0 <= pos.sign_index <= 11
        assert 0 <= pos.degree_in_sign < 30

    def test_returns_planet_position_dataclass(self) -> None:
        dt = datetime(2000, 6, 21, 1, 48)
        pos = tropical_longitude(Planet.SUN, dt)
        assert isinstance(pos, PlanetPosition)
        assert pos.planet == Planet.SUN


class TestSiderealLongitude:
    def test_sidereal_differs_from_tropical(self) -> None:
        # Lahiri ayanamsa em 2000 é ~23.85° — Lua sideral ≠ tropical
        dt = datetime(2000, 6, 21, 1, 48)
        tropical = tropical_longitude(Planet.MOON, dt)
        sidereal = sidereal_longitude(Planet.MOON, dt)
        assert abs(tropical.longitude - sidereal.longitude) > 20

    def test_sidereal_longitude_range_valid(self) -> None:
        dt = datetime(2000, 3, 20, 7, 35)
        pos = sidereal_longitude(Planet.MOON, dt)
        assert 0 <= pos.longitude < 360
        assert 0 <= pos.sign_index <= 11


class TestAscendant:
    def test_ascendant_range_valid(self) -> None:
        # São Paulo: -23.55°S, -46.63°W
        dt = datetime(2000, 6, 21, 12, 0)
        asc = ascendant(dt, lat=-23.55, lon=-46.63)
        assert 0 <= asc < 360

    def test_ascendant_changes_with_time(self) -> None:
        # O Ascendente muda ~1° a cada 4 minutos
        dt1 = datetime(2000, 6, 21, 12, 0)
        dt2 = datetime(2000, 6, 21, 14, 0)
        asc1 = ascendant(dt1, lat=-23.55, lon=-46.63)
        asc2 = ascendant(dt2, lat=-23.55, lon=-46.63)
        assert asc1 != asc2


class TestSunriseSunset:
    def test_sunrise_before_sunset(self) -> None:
        dt = datetime(2000, 6, 21)
        lat, lon = -23.55, -46.63  # São Paulo
        sr = sunrise(dt, lat, lon)
        ss = sunset(dt, lat, lon)
        assert sr < ss

    def test_sunrise_is_datetime(self) -> None:
        dt = datetime(2000, 6, 21)
        sr = sunrise(dt, lat=-23.55, lon=-46.63)
        assert isinstance(sr, datetime)

    def test_sunset_is_datetime(self) -> None:
        dt = datetime(2000, 6, 21)
        ss = sunset(dt, lat=-23.55, lon=-46.63)
        assert isinstance(ss, datetime)

    def test_sunrise_sao_paulo_summer_solstice_approx(self) -> None:
        # Nascer do sol em São Paulo no solstício de junho ≈ 10:00 UTC (07:00 BRT)
        dt = datetime(2000, 6, 21)
        sr = sunrise(dt, lat=-23.55, lon=-46.63)
        assert 9 <= sr.hour <= 11, f"Nascer do sol inesperado: {sr}"
