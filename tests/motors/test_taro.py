"""
Testes do motor Tarô.

Redução: DD + MM + AAAA (inteiros), soma de dígitos repetida até atingir 1–22.
Arcano 22 (O Louco) é preservado — id_gatilho=33.

Casos notáveis:
- 01/03/1980: 1+3+1980=1984 → 22 (O Louco) — arcano especial
- 06/05/1988: 6+5+1988=1999 → 28 → 10 (duas reduções)
- 04/12/1993: 4+12+1993=2009 → 11 (A Força)
"""

import pytest
from datetime import date

from app.core.temporal import TemporalStatus
from app.motors.taro import TaroResult, _sum_to_arcano, calculate_taro

_VALID_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})


# ── Testes unitários — _sum_to_arcano ────────────────────────────────────────


class TestSumToArcano:
    def test_reducao_simples(self):
        # 15+7+1984=2006 → 2+0+0+6=8
        assert _sum_to_arcano(15, 7, 1984) == 8

    def test_arcano_11_preservado(self):
        # 4+12+1993=2009 → 2+0+0+9=11 ≤ 22, para
        assert _sum_to_arcano(4, 12, 1993) == 11

    def test_arcano_22_o_louco(self):
        # 1+3+1980=1984 → 1+9+8+4=22 ≤ 22, para (O Louco)
        assert _sum_to_arcano(1, 3, 1980) == 22

    def test_reducao_dois_passos(self):
        # 6+5+1988=1999 → 1+9+9+9=28 > 22 → 2+8=10
        assert _sum_to_arcano(6, 5, 1988) == 10

    def test_arcano_minimo(self):
        # 1+1+2001=2003 → 2+0+0+3=5
        assert _sum_to_arcano(1, 1, 2001) == 5

    def test_resultado_em_range_valido(self):
        for day in [1, 15, 28, 31]:
            for month in [1, 6, 12]:
                for year in [1900, 1984, 2000, 2024]:
                    result = _sum_to_arcano(day, month, year)
                    assert 1 <= result <= 22, f"Arcano fora do range: {day}/{month}/{year} → {result}"


# ── Testes de integração ──────────────────────────────────────────────────────


@pytest.mark.integration
class TestCalculateTaro:

    def test_justica(self):
        # 15+7+1984=2006 → 8 → A Justiça, id_gatilho=4
        r = calculate_taro(date(1984, 7, 15))
        assert r.arcano == 8
        assert r.nome_arcano == "A Justiça"
        assert r.id_gatilho == 4
        assert r.vote == 4

    def test_hierofante(self):
        # 1+1+2001=2003 → 5 → O Hierofante, id_gatilho=3
        r = calculate_taro(date(2001, 1, 1))
        assert r.arcano == 5
        assert r.nome_arcano == "O Hierofante"
        assert r.id_gatilho == 3
        assert r.vote == 3

    def test_forca_arcano_11(self):
        # 4+12+1993=2009 → 11 → A Força, id_gatilho=1
        r = calculate_taro(date(1993, 12, 4))
        assert r.arcano == 11
        assert r.nome_arcano == "A Força"
        assert r.id_gatilho == 1
        assert r.vote == 1

    def test_louco_arcano_22(self):
        # 1+3+1980=1984 → 22 → O Louco, id_gatilho=33
        r = calculate_taro(date(1980, 3, 1))
        assert r.arcano == 22
        assert r.nome_arcano == "O Louco"
        assert r.id_gatilho == 33
        assert r.vote == 33

    def test_roda_da_fortuna_dois_passos(self):
        # 6+5+1988=1999 → 28 → 10 → A Roda da Fortuna, id_gatilho=3
        r = calculate_taro(date(1988, 5, 6))
        assert r.arcano == 10
        assert r.nome_arcano == "A Roda da Fortuna"
        assert r.id_gatilho == 3
        assert r.vote == 3

    def test_carro_arcano_7(self):
        # 22+11+1990=2023 → 2+0+2+3=7 → O Carro, id_gatilho=9
        r = calculate_taro(date(1990, 11, 22))
        assert r.arcano == 7
        assert r.nome_arcano == "O Carro"
        assert r.id_gatilho == 9
        assert r.vote == 9

    def test_status_sempre_exact(self):
        r = calculate_taro(date(1984, 7, 15))
        assert r.overall_status == TemporalStatus.EXACT

    def test_vote_em_valid_ids(self):
        datas = [
            date(1984, 7, 15), date(2001, 1, 1), date(1993, 12, 4),
            date(1980, 3, 1), date(1988, 5, 6), date(1990, 11, 22),
            date(2000, 11, 11), date(1975, 3, 28), date(1999, 9, 9),
        ]
        for dt in datas:
            r = calculate_taro(dt)
            assert r.vote in _VALID_IDS, f"vote inválido: {dt} → arcano={r.arcano}, vote={r.vote}"
