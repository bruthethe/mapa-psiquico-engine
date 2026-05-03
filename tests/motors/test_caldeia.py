"""
Testes do motor Caldeia (Numerologia).

Unitários: normalize_letter, name_to_values (J=1 presente), vibracao_psiquica.
Integração: 5 nomes/datas com resultados verificados manualmente.

Tabela caldeia: A/I/J/Q/Y=1  B/K/R=2  C/G/L/S=3  D/M/T=4  E/H/N/X=5
                U/V/W=6     O/Z=7    F/P=8
Nota: 9 não é atribuído a nenhuma letra (considerado sagrado).
Diferença da Cabalística: J=1 EXISTE na tabela caldeia.

Número do Destino = theosophic_reduce(raw_nome + raw_dígitos_DDMMYYYY).
O nome contribui com sua soma bruta (sem redução prévia) para o destino.
"""

import pytest
from datetime import date

from app.core.temporal import TemporalStatus
from app.motors.caldeia import (
    CaldeiaResult,
    calculate_caldeia,
    name_to_values,
    normalize_letter,
    vibracao_psiquica,
)

_VALID_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})


# ── Testes unitários — normalização ──────────────────────────────────────────


class TestNormalizeLetter:
    def test_ascii_maiusculo(self):
        assert normalize_letter("A") == "A"

    def test_ascii_minusculo(self):
        assert normalize_letter("z") == "Z"

    def test_acento(self):
        assert normalize_letter("á") == "A"

    def test_cedilha(self):
        assert normalize_letter("ç") == "C"


# ── Testes unitários — tabela e conversão de nome ────────────────────────────


class TestConversionTable:
    def test_j_presente_com_valor_1(self):
        # J=1 existe na Caldeia — diferença fundamental da Cabalística
        assert name_to_values("J") == [("J", 1)]

    def test_j_em_nome_mapeado(self):
        # "JOSE" → J=1, O=7, S=3, E=5 (J não é ignorado aqui)
        assert name_to_values("JOSE") == [("J", 1), ("O", 7), ("S", 3), ("E", 5)]

    def test_nove_nao_aparece_em_letras(self):
        # Nenhuma letra deve ter valor 9
        all_values = {v for _, v in name_to_values("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
        assert 9 not in all_values

    def test_valores_basicos(self):
        # A=1, B=2, C=3, D=4, E=5, F=8, G=3, H=5
        assert name_to_values("ABCDEFGH") == [
            ("A", 1), ("B", 2), ("C", 3), ("D", 4),
            ("E", 5), ("F", 8), ("G", 3), ("H", 5),
        ]

    def test_espaco_ignorado(self):
        assert name_to_values("A B") == [("A", 1), ("B", 2)]

    def test_acento_normalizado(self):
        # JOÃO: J=1, O=7, Ã→A=1, O=7 (J mapeado!)
        assert name_to_values("JOÃO") == [("J", 1), ("O", 7), ("A", 1), ("O", 7)]


# ── Testes unitários — Vibração Psíquica ─────────────────────────────────────


class TestVibracaoPsiquica:
    def test_dia_simples(self):
        assert vibracao_psiquica(7) == 7

    def test_dia_reduzido(self):
        # 15 → 1+5 = 6
        assert vibracao_psiquica(15) == 6

    def test_dia_mestre_11(self):
        assert vibracao_psiquica(11) == 11

    def test_dia_mestre_22(self):
        assert vibracao_psiquica(22) == 22

    def test_dia_29(self):
        # 29 → 2+9 = 11 (mestre!)
        assert vibracao_psiquica(29) == 11


# ── Testes de integração — 5 nomes/datas conhecidos ──────────────────────────


@pytest.mark.integration
class TestCalculateCaldeia:
    """
    Resultados calculados manualmente.
    Tabela: A/I/J/Q/Y=1  B/K/R=2  C/G/L/S=3  D/M/T=4  E/H/N/X=5
            U/V/W=6     O/Z=7    F/P=8       (9=sagrado, não atribuído)

    Número do Destino = theosophic_reduce(raw_nome + raw_dígitos_data).
    """

    def test_ana(self):
        # A=1, N=5, A=1 → raw_nome=7, id_nome=7
        # VP: dia=1 → 1
        # raw_data(01/01/2001): 0+1+0+1+2+0+0+1=5
        # destino: theosophic_reduce(7+5)=theosophic_reduce(12)=3
        r = calculate_caldeia("ANA", date(2001, 1, 1))
        assert r.id_nome == 7
        assert r.vibracao_psiquica == 1
        assert r.numero_destino == 3
        assert r.vote == 3

    def test_jose_j_presente(self):
        # J=1, O=7, S=3, E=5 → raw_nome=16, id_nome=7
        # VP: dia=15 → 6
        # raw_data(15/07/1984): 1+5+0+7+1+9+8+4=35
        # destino: theosophic_reduce(16+35)=theosophic_reduce(51)=6
        r = calculate_caldeia("JOSE", date(1984, 7, 15))
        assert r.id_nome == 7
        assert r.vibracao_psiquica == 6
        assert r.numero_destino == 6
        assert r.vote == 6

    def test_maria_destino_mestre_11(self):
        # M=4, A=1, R=2, I=1, A=1 → raw_nome=9, id_nome=9
        # VP: dia=4 → 4
        # raw_data(04/12/1993): 0+4+1+2+1+9+9+3=29
        # destino: theosophic_reduce(9+29)=theosophic_reduce(38)=11 (MESTRE!)
        r = calculate_caldeia("MARIA", date(1993, 12, 4))
        assert r.id_nome == 9
        assert r.vibracao_psiquica == 4
        assert r.numero_destino == 11
        assert r.vote == 11

    def test_paulo_vp_mestre_22(self):
        # P=8, A=1, U=6, L=3, O=7 → raw_nome=25, id_nome=7
        # VP: dia=22 → 22 (MESTRE!)
        # raw_data(22/11/1990): 2+2+1+1+1+9+9+0=25
        # destino: theosophic_reduce(25+25)=theosophic_reduce(50)=5
        r = calculate_caldeia("PAULO", date(1990, 11, 22))
        assert r.id_nome == 7
        assert r.vibracao_psiquica == 22
        assert r.numero_destino == 5
        assert r.vote == 5

    def test_lucas_destino_mestre_22(self):
        # L=3, U=6, C=3, A=1, S=3 → raw_nome=16, id_nome=7
        # VP: dia=11 → 11 (MESTRE!)
        # raw_data(11/11/2000): 1+1+1+1+2+0+0+0=6
        # destino: theosophic_reduce(16+6)=theosophic_reduce(22)=22 (MESTRE!)
        # vote: lookup_id(22)=4
        r = calculate_caldeia("LUCAS", date(2000, 11, 11))
        assert r.id_nome == 7
        assert r.vibracao_psiquica == 11
        assert r.numero_destino == 22
        assert r.vote == 4

    def test_status_sempre_exact(self):
        r = calculate_caldeia("ANA", date(2001, 1, 1))
        assert r.overall_status == TemporalStatus.EXACT

    def test_vote_em_valid_ids(self):
        nomes = ["ANA", "JOSE", "MARIA", "PAULO", "LUCAS"]
        datas = [
            date(2001, 1, 1), date(1984, 7, 15), date(1993, 12, 4),
            date(1990, 11, 22), date(2000, 11, 11),
        ]
        for nome in nomes:
            for dt in datas:
                r = calculate_caldeia(nome, dt)
                assert r.vote in _VALID_IDS, f"vote inválido: {nome} {dt} → {r.vote}"
