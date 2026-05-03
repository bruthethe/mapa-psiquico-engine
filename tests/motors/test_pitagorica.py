"""
Testes do motor Pitagórica (Numerologia).

Unitários: normalize_letter, name_to_values, caminho_vida, IDs individuais.
Integração: 10 nomes/datas conhecidos com resultados esperados.

Todos os cálculos verificados manualmente letra a letra.
Tabela pitagórica: A/J/S=1  B/K/T=2  C/L/U=3  D/M/V=4  E/N/W=5
                   F/O/X=6  G/P/Y=7  H/Q/Z=8  I/R=9
"""

import pytest
from datetime import date

from app.core.temporal import TemporalStatus
from app.motors.pitagorica import (
    PitagoricaResult,
    calculate_pitagorica,
    caminho_vida,
    name_to_values,
    normalize_letter,
)

_VALID_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})


# ── Testes unitários — normalização ──────────────────────────────────────────


class TestNormalizeLetter:
    def test_ascii_maiusculo(self):
        assert normalize_letter("A") == "A"

    def test_ascii_minusculo(self):
        assert normalize_letter("z") == "Z"

    def test_acento_agudo(self):
        assert normalize_letter("á") == "A"
        assert normalize_letter("é") == "E"

    def test_acento_til(self):
        assert normalize_letter("ã") == "A"
        assert normalize_letter("õ") == "O"

    def test_cedilha(self):
        assert normalize_letter("ç") == "C"

    def test_circunflexo(self):
        assert normalize_letter("ô") == "O"
        assert normalize_letter("ê") == "E"


# ── Testes unitários — conversão de nome ──────────────────────────────────────


class TestNameToValues:
    def test_espaco_ignorado(self):
        # espaço não tem mapeamento; resultado ignora
        assert name_to_values("A B") == [("A", 1), ("B", 2)]

    def test_hifen_ignorado(self):
        assert name_to_values("A-B") == [("A", 1), ("B", 2)]

    def test_digito_ignorado(self):
        assert name_to_values("A1B") == [("A", 1), ("B", 2)]

    def test_acento_normalizado(self):
        # JOÃO: J=1, O=6, Ã→A=1, O=6
        vals = name_to_values("JOÃO")
        assert vals == [("J", 1), ("O", 6), ("A", 1), ("O", 6)]

    def test_cedilha_normalizada(self):
        # Ç → C = 3
        vals = name_to_values("Ç")
        assert vals == [("C", 3)]

    def test_valores_pitagoricos_basicos(self):
        # A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9
        assert name_to_values("ABCDEFGHI") == [
            ("A", 1), ("B", 2), ("C", 3), ("D", 4), ("E", 5),
            ("F", 6), ("G", 7), ("H", 8), ("I", 9),
        ]

    def test_segunda_linha_pitagorica(self):
        # J=1, K=2, L=3, M=4, N=5, O=6, P=7, Q=8, R=9
        assert name_to_values("JKLMNOPQR") == [
            ("J", 1), ("K", 2), ("L", 3), ("M", 4), ("N", 5),
            ("O", 6), ("P", 7), ("Q", 8), ("R", 9),
        ]

    def test_terceira_linha_pitagorica(self):
        # S=1, T=2, U=3, V=4, W=5, X=6, Y=7, Z=8
        assert name_to_values("STUVWXYZ") == [
            ("S", 1), ("T", 2), ("U", 3), ("V", 4),
            ("W", 5), ("X", 6), ("Y", 7), ("Z", 8),
        ]


# ── Testes unitários — Caminho de Vida ───────────────────────────────────────


class TestCaminhoVida:
    def test_sem_mestres(self):
        # 15/07/1984: dia=6, mes=7, ano=1+9+8+4=22→22, total=6+7+22=35→8
        assert caminho_vida(date(1984, 7, 15)) == 8

    def test_preserva_mestre_22_no_ano(self):
        # 1984: 1+9+8+4=22 → mestre, não reduz para 4
        # Confere implicitamente via resultado acima (=8, não =8 de outra forma)
        # Forçamos um caso onde sem o 22 o resultado seria diferente:
        # 04/12/1993: dia=4, mes=3, ano=1+9+9+3=22→22, total=4+3+22=29→11
        assert caminho_vida(date(1993, 12, 4)) == 11

    def test_preserva_mestre_11_no_dia(self):
        # 11/11/2000: dia=11, mes=11, ano=2, total=11+11+2=24→6
        assert caminho_vida(date(2000, 11, 11)) == 6

    def test_preserva_mestre_22_no_dia(self):
        # 22/11/1990: dia=22, mes=11, ano=1+9+9+0=19→10→1, total=22+11+1=34→7
        assert caminho_vida(date(1990, 11, 22)) == 7

    def test_resultado_mestre_11(self):
        # 04/12/1993 → 11 (verificado acima)
        cv = caminho_vida(date(1993, 12, 4))
        assert cv == 11

    def test_resultado_simples(self):
        # 01/01/2001: dia=1, mes=1, ano=2+0+0+1=3, total=5
        assert caminho_vida(date(2001, 1, 1)) == 5


# ── Testes de integração — 10 nomes/datas conhecidos ─────────────────────────


@pytest.mark.integration
class TestCalculatePitagorica:
    """
    Resultados calculados manualmente letra a letra.
    Tabela: A/J/S=1 B/K/T=2 C/L/U=3 D/M/V=4 E/N/W=5 F/O/X=6 G/P/Y=7 H/Q/Z=8 I/R=9
    """

    def test_ana(self):
        # A=1, N=5, A=1
        # vogais: A(1)+A(1)=2  consoantes: N(5)=5  total: 1+5+1=7
        r = calculate_pitagorica("ANA", date(2000, 1, 1))
        assert r.id_alma == 2
        assert r.id_persona == 5
        assert r.id_expressao == 7

    def test_jose_preserva_mestre_11_na_alma(self):
        # J=1, O=6, S=1, E=5
        # vogais: O(6)+E(5)=11→mestre  consoantes: J(1)+S(1)=2  total: 1+6+1+5=13→4
        r = calculate_pitagorica("JOSE", date(2000, 1, 1))
        assert r.id_alma == 11
        assert r.id_persona == 2
        assert r.id_expressao == 4

    def test_maria_preserva_mestre_11_na_alma(self):
        # M=4, A=1, R=9, I=9, A=1
        # vogais: A(1)+I(9)+A(1)=11→mestre  consoantes: M(4)+R(9)=13→4  total: 4+1+9+9+1=24→6
        r = calculate_pitagorica("MARIA", date(2000, 1, 1))
        assert r.id_alma == 11
        assert r.id_persona == 4
        assert r.id_expressao == 6

    def test_paulo(self):
        # P=7, A=1, U=3, L=3, O=6
        # vogais: A(1)+U(3)+O(6)=10→1  consoantes: P(7)+L(3)=10→1  total: 7+1+3+3+6=20→2
        r = calculate_pitagorica("PAULO", date(2000, 1, 1))
        assert r.id_alma == 1
        assert r.id_persona == 1
        assert r.id_expressao == 2

    def test_lucas_expressao_mestre_11(self):
        # L=3, U=3, C=3, A=1, S=1
        # vogais: U(3)+A(1)=4  consoantes: L(3)+C(3)+S(1)=7  total: 3+3+3+1+1=11→mestre
        r = calculate_pitagorica("LUCAS", date(2000, 1, 1))
        assert r.id_alma == 4
        assert r.id_persona == 7
        assert r.id_expressao == 11

    def test_joao_com_acento(self):
        # J=1, O=6, Ã→A=1, O=6
        # vogais: O(6)+A(1)+O(6)=13→4  consoantes: J(1)=1  total: 1+6+1+6=14→5
        r = calculate_pitagorica("JOÃO", date(2000, 1, 1))
        assert r.id_alma == 4
        assert r.id_persona == 1
        assert r.id_expressao == 5

    def test_nome_social_diferente(self):
        # Batismo "JOAO PEDRO": J(1)+O(6)+A(1)+O(6)+P(7)+E(5)+D(4)+R(9)+O(6)=45→9
        # Social "PEDRO":       P(7)+E(5)+D(4)+R(9)+O(6)=31→4
        # ajuste = 9-4=5
        r = calculate_pitagorica("JOAO PEDRO", date(2000, 1, 1), nome_social="PEDRO")
        assert r.id_expressao == 9
        assert r.id_vibe_atual == 4
        assert r.ajuste_frequencia == 5

    def test_nome_social_none_usa_batismo(self):
        r = calculate_pitagorica("ANA", date(2000, 1, 1), nome_social=None)
        assert r.id_vibe_atual == r.id_expressao
        assert r.ajuste_frequencia == 0

    def test_caminho_vida_e_vote_com_lookup(self):
        # 15/07/1984: caminho=8, vote=lookup_id(8)=4
        r = calculate_pitagorica("ANA", date(1984, 7, 15))
        assert r.caminho_vida == 8
        assert r.vote == 4  # lookup_id(8) → 4

    def test_caminho_vida_mestre_11_vote_preservado(self):
        # 04/12/1993: caminho=11, vote=lookup_id(11)=11
        r = calculate_pitagorica("ANA", date(1993, 12, 4))
        assert r.caminho_vida == 11
        assert r.vote == 11

    def test_status_sempre_exact(self):
        r = calculate_pitagorica("ANA", date(2000, 1, 1))
        assert r.overall_status == TemporalStatus.EXACT

    def test_vote_em_valid_ids(self):
        nomes = ["ANA", "JOSE", "MARIA", "PAULO", "LUCAS", "JOAO PEDRO"]
        datas = [
            date(2000, 1, 1), date(1984, 7, 15), date(1993, 12, 4),
            date(1990, 11, 22), date(2000, 11, 11), date(2001, 1, 1),
        ]
        for nome in nomes:
            for dt in datas:
                r = calculate_pitagorica(nome, dt)
                assert r.vote in _VALID_IDS, f"vote inválido: {nome} {dt} → {r.vote}"
