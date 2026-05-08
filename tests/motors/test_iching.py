"""
Testes do motor I Ching.

Motor de lookup puro — input é a Porta do Sol de Personalidade do Human Design (1–64).
Tabela cobre 12 hexagramas: 1, 2, 3, 4, 11, 12, 29, 30, 51, 52, 63, 64.
Portais fora da tabela → fallback para hexagrama 1 (Resiliência Total).
"""

import pytest

from app.core.temporal import TemporalStatus
from app.motors.iching import IChingResult, calculate_iching

_VALID_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})
_TABELA_HEXAGRAMAS = frozenset({1, 2, 3, 4, 11, 12, 29, 30, 51, 52, 63, 64})


@pytest.mark.integration
class TestCalculateIching:

    def test_hex1_o_criativo(self):
        r = calculate_iching(1)
        assert r.hexagrama == 1
        assert r.nome == "O Criativo"
        assert r.id_gatilho == 1
        assert r.vote == 1
        assert r.fallback is False

    def test_hex29_o_abismal(self):
        r = calculate_iching(29)
        assert r.hexagrama == 29
        assert r.nome == "O Abismal"
        assert r.id_gatilho == 7
        assert r.vote == 7
        assert r.fallback is False

    def test_hex64_antes_conclusao_id_11(self):
        # hexagrama 64 → id_gatilho=11 (mestre preservado)
        r = calculate_iching(64)
        assert r.hexagrama == 64
        assert r.id_gatilho == 11
        assert r.vote == 11
        assert r.fallback is False

    def test_hex51_o_trovao(self):
        r = calculate_iching(51)
        assert r.hexagrama == 51
        assert r.nome == "O Trovão"
        assert r.id_gatilho == 9
        assert r.vote == 9
        assert r.fallback is False

    def test_hex63_apos_conclusao(self):
        r = calculate_iching(63)
        assert r.hexagrama == 63
        assert r.id_gatilho == 6
        assert r.vote == 6
        assert r.fallback is False

    def test_fallback_para_hex_nao_mapeado(self):
        # Porta 5 não está na tabela → fallback para hexagrama 1
        r = calculate_iching(5)
        assert r.hexagrama == 5        # preserva o portal original
        assert r.nome == "O Criativo"  # dados do fallback (hex 1)
        assert r.fallback is True

    def test_fallback_preserva_hexagrama_original(self):
        # O campo hexagrama registra o portal real mesmo em fallback
        r = calculate_iching(33)
        assert r.hexagrama == 33
        assert r.fallback is True

    def test_todos_hexagramas_da_tabela_sem_fallback(self):
        for h in _TABELA_HEXAGRAMAS:
            r = calculate_iching(h)
            assert r.fallback is False, f"hex {h} deveria estar na tabela"

    def test_status_sempre_exact(self):
        r = calculate_iching(1)
        assert r.overall_status == TemporalStatus.EXACT

    def test_vote_em_valid_ids(self):
        for h in _TABELA_HEXAGRAMAS:
            r = calculate_iching(h)
            assert r.vote in _VALID_IDS, f"vote inválido: hex {h} → {r.vote}"
