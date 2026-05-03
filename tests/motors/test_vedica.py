"""
Testes do motor Védico — História 2.2.

Unitários: nakshatra_index, pada, purushartha (sem pyswisseph).
Integração: 5 mapas verificados via ephemeris + validação de Atmakaraka.
"""

import pytest
from datetime import date, datetime, time

from app.core.ephemeris import Planet, sidereal_longitude
from app.core.temporal import TemporalStatus, TimeWindow, parse_time_input
from app.motors.vedica import (
    AtmakarakaResult,
    NakshatraResult,
    VedicaResult,
    _NK_SPAN,
    _nakshatra_index,
    _pada,
    _purushartha,
    calculate_vedica,
)

_VALID_IDS = {1, 2, 3, 4, 5, 6, 7, 9, 11, 33}
_VALID_PURUSHARTHAS = {"Dharma", "Artha", "Kama", "Moksha"}

_NAKSHATRAS_27 = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


# ── Testes unitários ───────────────────────────────────────────────────────────


class TestNakshatraIndex:
    @pytest.mark.parametrize("lon,expected_idx", [
        (0.0,    0),   # Ashwini — início exato
        (6.0,    0),   # Ashwini — meio
        (13.333, 0),   # ainda Ashwini — 13.333 < 13.333... (float trunca para 0)
        (20.0,   1),   # Bharani — meio
        (26.666, 1),   # Bharani — fim
        (26.667, 2),   # Krittika — início exato
        (346.667, 26), # Revati — início exato
        (359.999, 26), # Revati — fim
    ])
    def test_index_from_longitude(self, lon, expected_idx):
        assert _nakshatra_index(lon) == expected_idx

    def test_all_27_covered(self):
        seen = set()
        for i in range(27):
            lon = i * _NK_SPAN + 0.5
            seen.add(_nakshatra_index(lon))
        assert len(seen) == 27


class TestPada:
    @pytest.mark.parametrize("lon_in_nk,expected_pada", [
        (0.0,   1),
        (1.0,   1),
        (3.333, 1),   # fim do pada 1
        (3.334, 2),   # início do pada 2
        (6.666, 2),
        (6.667, 3),
        (10.0,  4),   # 10.0 / 3.333... = 3.0 exato → int(3.0)+1 = 4 (início do pada 4)
        (10.001, 4),
        (13.0,  4),
    ])
    def test_pada_from_offset(self, lon_in_nk, expected_pada):
        # usa Ashwini (começa em 0°) para testar com longitude absoluta igual ao offset
        assert _pada(lon_in_nk) == expected_pada

    def test_pada_range_is_1_to_4(self):
        for i in range(27):
            for sub in [0.1, 3.5, 7.0, 10.5]:
                lon = i * _NK_SPAN + sub
                assert 1 <= _pada(lon) <= 4


class TestPurushartha:
    def test_cycle_4(self):
        expected = ["Dharma", "Artha", "Kama", "Moksha"]
        for i in range(27):
            assert _purushartha(i) == expected[i % 4]

    def test_always_valid(self):
        for i in range(27):
            assert _purushartha(i) in _VALID_PURUSHARTHAS


# ── Testes de integração ───────────────────────────────────────────────────────


@pytest.mark.integration
class TestNakshatraFromEphemeris:
    """
    5 mapas verificados via Swiss Ephemeris (mesma referência usada por
    Shri Jyoti Star e Jagannatha Hora). O índice esperado é calculado
    diretamente da longitude sidereal retornada pelo ephemeris.
    """

    @pytest.mark.parametrize("birth_date,notes", [
        (date(2000,  1,  1), "Lua na área Capricórnio/Sagitário sideral"),
        (date(2000,  4,  1), "Lua na área Áries/Peixes sideral"),
        (date(2000,  7,  1), "Lua na área Câncer/Gêmeos sideral"),
        (date(2000, 10,  1), "Lua na área Libra/Virgem sideral"),
        (date(2000, 12, 15), "Lua na área Sagitário/Escorpião sideral"),
    ])
    def test_nakshatra_matches_ephemeris(self, birth_date, notes):
        dt_utc = datetime.combine(birth_date, time(12, 0))
        moon_pos = sidereal_longitude(Planet.MOON, dt_utc)
        expected_idx = _nakshatra_index(moon_pos.longitude)
        expected_pada = _pada(moon_pos.longitude)

        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_vedica(birth_date, time_input, "UTC")

        assert isinstance(result, VedicaResult), notes
        assert result.nakshatra.index == expected_idx, notes
        assert result.nakshatra.nome == _NAKSHATRAS_27[expected_idx], notes
        assert result.nakshatra.pada == expected_pada, notes
        assert result.nakshatra.id_gatilho in _VALID_IDS, notes
        assert result.nakshatra.purushartha in _VALID_PURUSHARTHAS, notes
        assert result.nakshatra.status == TemporalStatus.EXACT, notes
        assert result.vote == result.nakshatra.id_gatilho, notes
        assert result.vote_b is None, notes
        assert result.overall_status == TemporalStatus.EXACT, notes


@pytest.mark.integration
class TestAtmakaraka:
    def test_atmakaraka_is_valid_graha(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_vedica(date(2000, 1, 1), time_input, "UTC")
        ak = result.atmakaraka
        assert isinstance(ak, AtmakarakaResult)
        assert ak.graha in {"surya", "chandra", "mangala", "budha", "guru", "shukra", "shani"}
        assert ak.id_gatilho in _VALID_IDS
        assert 0.0 <= ak.grau_no_signo < 30.0

    def test_atmakaraka_excludes_rahu_ketu(self):
        # Rahu (id=11) e Ketu (id=7) podem aparecer via Nakshatra mas não como Atmakaraka
        # O Atmakaraka deve ser apenas um dos 7 grahas
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_vedica(date(2000, 7, 1), time_input, "UTC")
        assert result.atmakaraka.graha not in {"rahu", "ketu"}

    def test_atmakaraka_has_highest_degree_in_sign(self):
        """Verifica que o Atmakaraka retornado tem o maior grau dentro do signo."""
        time_input = parse_time_input(exact_time=time(12, 0))
        dt_utc = datetime.combine(date(2000, 1, 1), time(12, 0))

        from app.motors.vedica import _AK_PLANETS
        degrees = {}
        for planet, name in _AK_PLANETS:
            pos = sidereal_longitude(planet, dt_utc)
            degrees[name] = pos.longitude % 30

        result = calculate_vedica(date(2000, 1, 1), time_input, "UTC")
        ak_name = result.atmakaraka.graha
        assert degrees[ak_name] == max(degrees.values())


@pytest.mark.integration
class TestStatusTemporal:
    def test_exact_time_gives_exact_status(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_vedica(date(2000, 4, 1), time_input, "UTC")
        assert result.overall_status == TemporalStatus.EXACT
        assert result.nakshatra.nome_b is None
        assert result.nakshatra.id_gatilho_b is None
        assert result.nakshatra.pada_b is None

    def test_window_mid_nakshatra_gives_safe_status(self):
        # Usa data mid-Nakshatra + janela TARDE (4h) — Lua deve permanecer no mesmo Nakshatra
        # (Lua move ~2.2° em 4h; metade de um Nakshatra = 6.7°)
        time_input = parse_time_input(window=TimeWindow.TARDE)
        result = calculate_vedica(date(2000, 4, 1), time_input, "UTC")
        # Lua mid-Nakshatra → provavelmente Safe; se HYBRID, nakshatra_b deve estar preenchido
        if result.overall_status == TemporalStatus.HYBRID:
            assert result.nakshatra.nome_b is not None
            assert result.nakshatra.id_gatilho_b is not None
        else:
            assert result.overall_status == TemporalStatus.SAFE

    def test_unknown_fallback_gives_valid_result(self):
        time_input = parse_time_input()  # Caminho C — fallback 12:00
        result = calculate_vedica(date(2000, 1, 1), time_input, "UTC")
        assert result.nakshatra.id_gatilho in _VALID_IDS
        assert result.nakshatra.pada in {1, 2, 3, 4}
