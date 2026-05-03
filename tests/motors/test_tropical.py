"""
Testes do motor Tropical — História 2.1.

Unitários: sign_keys, sign_to_id (sem pyswisseph).
Integração: 10 mapas solares verificados + status temporal + Ascendente.
"""

import pytest
from datetime import date, time

from app.core.temporal import TemporalStatus, TimeWindow, parse_time_input
from app.motors.tropical import (
    TropicalResult,
    _SIGN_KEYS,
    _sign_to_id,
    calculate_tropical,
)


# ── Testes unitários ───────────────────────────────────────────────────────────


class TestSignKeys:
    def test_twelve_signs(self):
        assert len(_SIGN_KEYS) == 12

    def test_first_is_aries(self):
        assert _SIGN_KEYS[0] == "aries"

    def test_last_is_peixes(self):
        assert _SIGN_KEYS[11] == "peixes"

    def test_order(self):
        expected = [
            "aries", "touro", "gemeos", "cancer", "leao", "virgem",
            "libra", "escorpiao", "sagitario", "capricornio", "aquario", "peixes",
        ]
        assert _SIGN_KEYS == expected


class TestSignToId:
    @pytest.mark.parametrize("sign,expected_id", [
        ("aries",       9),   # Marte
        ("touro",       6),   # Vênus
        ("gemeos",      5),   # Mercúrio
        ("cancer",      2),   # Lua
        ("leao",        1),   # Sol
        ("virgem",      5),   # Mercúrio
        ("libra",       6),   # Vênus
        ("escorpiao",  33),   # Plutão — nunca reduz
        ("sagitario",   3),   # Júpiter
        ("capricornio", 4),   # Saturno
        ("aquario",    11),   # Urano — nunca reduz
        ("peixes",      7),   # Netuno
    ])
    def test_all_signs(self, sign, expected_id):
        assert _sign_to_id(sign) == expected_id

    def test_escorpiao_never_reduces(self):
        # Plutão → 33; garantir que lookup_id não altera mestres
        assert _sign_to_id("escorpiao") == 33

    def test_aquario_never_reduces(self):
        # Urano → 11; garantir que lookup_id não altera mestres
        assert _sign_to_id("aquario") == 11


# ── Testes de integração ───────────────────────────────────────────────────────

pytestmark_integration = pytest.mark.integration


@pytest.mark.integration
class TestSolarPosition:
    """
    10 mapas verificados contra ephemeris astronômico.
    Datas escolhidas no meio de cada signo para eliminar ambiguidade de cúspide.
    Cobre todos os 10 IDs válidos: 1, 2, 3, 4, 5, 6, 7, 9, 11, 33.
    """

    @pytest.mark.parametrize("birth_date,expected_sign,expected_id", [
        # ── Áries (Marte → 9) ──────────────────────────────────────
        (date(2000,  4,  1), "aries",       9),
        # ── Câncer (Lua → 2) ───────────────────────────────────────
        (date(2000,  7,  1), "cancer",      2),
        # ── Libra (Vênus → 6) ──────────────────────────────────────
        (date(2000, 10,  1), "libra",       6),
        # ── Capricórnio (Saturno → 4) ──────────────────────────────
        (date(2000,  1,  1), "capricornio", 4),
        # ── Leão (Sol → 1) ─────────────────────────────────────────
        (date(1990,  8,  1), "leao",        1),
        # ── Virgem (Mercúrio → 5) ──────────────────────────────────
        (date(1990,  9,  1), "virgem",      5),
        # ── Escorpião (Plutão → 33) ────────────────────────────────
        (date(1990, 11,  1), "escorpiao",  33),
        # ── Sagitário (Júpiter → 3) ────────────────────────────────
        (date(1990, 12,  1), "sagitario",   3),
        # ── Aquário (Urano → 11) ───────────────────────────────────
        (date(1990,  2,  1), "aquario",    11),
        # ── Peixes (Netuno → 7) ────────────────────────────────────
        (date(1990,  3,  1), "peixes",      7),
    ])
    def test_solar_sign_and_id(self, birth_date, expected_sign, expected_id):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_tropical(birth_date, time_input, "UTC")

        assert isinstance(result, TropicalResult)
        assert result.sol.sign == expected_sign, (
            f"{birth_date}: esperado signo '{expected_sign}', obtido '{result.sol.sign}'"
        )
        assert result.sol.id_gatilho == expected_id
        assert result.sol.status == TemporalStatus.EXACT
        assert result.overall_status == TemporalStatus.EXACT

    def test_vote_equals_solar_id(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_tropical(date(1990, 8, 1), time_input, "UTC")
        assert result.vote == result.sol.id_gatilho

    def test_vote_b_is_none_on_exact(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_tropical(date(1990, 8, 1), time_input, "UTC")
        assert result.vote_b is None

    def test_ten_planets_returned(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_tropical(date(2000, 4, 1), time_input, "UTC")
        assert len(result.planets) == 10
        planet_names = {p.planet for p in result.planets}
        assert planet_names == {
            "sol", "lua", "mercurio", "venus", "marte",
            "jupiter", "saturno", "urano", "netuno", "plutao",
        }


@pytest.mark.integration
class TestAscendente:
    def test_ascendente_none_without_coords(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_tropical(date(2000, 1, 1), time_input, "UTC")
        assert result.ascendente is None

    def test_ascendente_present_with_coords(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        # Londres: lat=51.50, lon=-0.12
        result = calculate_tropical(
            date(2000, 1, 1), time_input, "Europe/London",
            lat=51.50, lon=-0.12,
        )
        assert result.ascendente is not None
        assert result.ascendente.sign in _SIGN_KEYS
        assert result.ascendente.id_gatilho in {1, 2, 3, 4, 5, 6, 7, 9, 11, 33}

    def test_ascendente_window_is_hybrid(self):
        # Ascendente muda ~15°/hora → qualquer janela de 4h cruza pelo menos 1 signo
        time_input = parse_time_input(window=TimeWindow.TARDE)
        result = calculate_tropical(
            date(2000, 1, 1), time_input, "Europe/London",
            lat=51.50, lon=-0.12,
        )
        assert result.ascendente is not None
        assert result.ascendente.status == TemporalStatus.HYBRID
        assert result.ascendente.sign_b is not None
        assert result.ascendente.id_gatilho_b is not None


@pytest.mark.integration
class TestStatusTemporal:
    def test_exact_time_gives_exact_status(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_tropical(date(2000, 4, 1), time_input, "UTC")
        assert result.overall_status == TemporalStatus.EXACT

    def test_window_same_sign_gives_safe_status(self):
        # Sol não muda de signo em 4h → Sol e Lua provavelmente Safe para data de meio-signo
        # Usa MANHA (08:00-11:59) em data solidamente em Áries (01/04)
        time_input = parse_time_input(window=TimeWindow.MANHA)
        result = calculate_tropical(date(2000, 4, 1), time_input, "UTC")
        # Sol certamente Safe; overall pode variar por Lua — verificar apenas Sol
        assert result.sol.status == TemporalStatus.SAFE
        assert result.sol.sign_b is None

    def test_unknown_time_uses_fallback(self):
        time_input = parse_time_input()  # Caminho C — fallback 12:00
        result = calculate_tropical(date(2000, 4, 1), time_input, "UTC")
        # point_a == point_b == 12:00 → Sol Safe (ou Exact se UNKNOWN tratado como SAFE)
        assert result.sol.sign == "aries"
        assert result.sol.id_gatilho == 9
