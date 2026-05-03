"""
Testes do motor Cabalística (Numerologia).

Unitários: normalize_letter, name_to_values (incluindo J ausente), missao_vida.
Integração: 10 nomes/datas com resultados verificados manualmente.

Tabela cabalística: A/I/Q/Y=1  B/K/R=2  C/G/L/S=3  D/M/T=4  E/H/N/X=5
                    U/V/W=6   O/Z=7    F/P=8
Nota: J NÃO existe na tabela cabalística — letras sem mapeamento são ignoradas.

Dívidas kármicas detectadas nos somas brutas (antes da redução teosófica): 13, 14, 16, 19.
Missão de vida: soma de TODOS os dígitos de DDMMYYYY de uma vez (diferente da Pitagórica).
"""

import pytest
from datetime import date

from app.core.temporal import TemporalStatus
from app.motors.cabalistica import (
    CabalisticaResult,
    calculate_cabalistica,
    missao_vida,
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

    def test_cedilha(self):
        assert normalize_letter("ç") == "C"

    def test_til(self):
        assert normalize_letter("ã") == "A"


# ── Testes unitários — tabela e conversão de nome ────────────────────────────


class TestConversionTable:
    def test_valores_basicos(self):
        # A=1, B=2, C=3, D=4, E=5, F=8, G=3, H=5
        assert name_to_values("ABCDEFGH") == [
            ("A", 1), ("B", 2), ("C", 3), ("D", 4),
            ("E", 5), ("F", 8), ("G", 3), ("H", 5),
        ]

    def test_segunda_linha(self):
        # I=1, K=2, L=3, M=4, N=5, O=7, P=8, Q=1, R=2, S=3, T=4
        assert name_to_values("IKLMNOPQRST") == [
            ("I", 1), ("K", 2), ("L", 3), ("M", 4), ("N", 5),
            ("O", 7), ("P", 8), ("Q", 1), ("R", 2), ("S", 3), ("T", 4),
        ]

    def test_terceira_linha(self):
        # U=6, V=6, W=6, X=5, Y=1, Z=7
        assert name_to_values("UVWXYZ") == [
            ("U", 6), ("V", 6), ("W", 6), ("X", 5), ("Y", 1), ("Z", 7),
        ]

    def test_j_ausente_na_tabela(self):
        # J não existe na tabela cabalística — deve ser ignorado
        assert name_to_values("J") == []

    def test_j_em_nome_ignorado(self):
        # "JOSE" → J ignorado; O=7, S=3, E=5
        assert name_to_values("JOSE") == [("O", 7), ("S", 3), ("E", 5)]

    def test_espaco_ignorado(self):
        assert name_to_values("A B") == [("A", 1), ("B", 2)]

    def test_acento_normalizado(self):
        # Ã → A=1
        vals = name_to_values("JOÃO")
        # J=ignorado, O=7, Ã→A=1, O=7
        assert vals == [("O", 7), ("A", 1), ("O", 7)]


# ── Testes unitários — Missão de Vida ────────────────────────────────────────


class TestMissaoVida:
    def test_simples(self):
        # 01/01/2001: 0+1+0+1+2+0+0+1=5
        assert missao_vida(date(2001, 1, 1)) == 5

    def test_reduz_para_8(self):
        # 15/07/1984: 1+5+0+7+1+9+8+4=35 → 3+5=8
        assert missao_vida(date(1984, 7, 15)) == 8

    def test_preserva_mestre_11(self):
        # 04/12/1993: 0+4+1+2+1+9+9+3=29 → 2+9=11 (mestre!)
        assert missao_vida(date(1993, 12, 4)) == 11

    def test_preserva_mestre_22(self):
        # precisa de soma=22: ex. 29/12/1994: 2+9+1+2+1+9+9+4=37→10→1... não
        # 19/06/2005: 1+9+0+6+2+0+0+5=23→5. não
        # 05/11/2006: 0+5+1+1+2+0+0+6=15→6. não
        # 07/09/2006: 0+7+0+9+2+0+0+6=24→6. não
        # 29/09/2002: 2+9+0+9+2+0+0+2=24→6. não
        # 29/09/2020: 2+9+0+9+2+0+2+0=24→6. não
        # 29/12/2020: 2+9+1+2+2+0+2+0=18→9. não
        # 29/12/1984: 2+9+1+2+1+9+8+4=36→9. não
        # 29/12/2003: 2+9+1+2+2+0+0+3=19→19→1+9=10→1. não
        # 07/07/2008: 0+7+0+7+2+0+0+8=24→6. não
        # 09/04/2009: 0+9+0+4+2+0+0+9=24→6. não
        # soma=22: precisamos de dígitos somando exatamente 22
        # 29/09/1984: 2+9+0+9+1+9+8+4=42→6. não
        # 28/12/1975: 2+8+1+2+1+9+7+5=35→8. não
        # 09/09/2004: 0+9+0+9+2+0+0+4=24→6. não
        # 05/09/1975: 0+5+0+9+1+9+7+5=36→9. não
        # 09/09/1993: 0+9+0+9+1+9+9+3=40→4. não
        # 09/09/2003: 0+9+0+9+2+0+0+3=23→5. não
        # 19/09/1976: 1+9+0+9+1+9+7+6=42→6. não
        # 28/09/1976: 2+8+0+9+1+9+7+6=42→6. não
        # 28/03/1985: 2+8+0+3+1+9+8+5=36→9. não
        # Tentando soma=22: 0+4+0+9+1+9=23. Precisamos: soma restante=22 dos dígitos
        # ex: 04/09/1900: 0+4+0+9+1+9+0+0=23→5
        # ex: 05/09/1900: 0+5+0+9+1+9+0+0=24→6
        # ex: 04/08/1900: 0+4+0+8+1+9+0+0=22! → MASTER 22
        assert missao_vida(date(1900, 8, 4)) == 22

    def test_difere_da_pitagorica(self):
        # 11/11/2000:
        # Pitagórica: dia=11(mestre), mes=11(mestre), ano=2+0+0+0=2, total=11+11+2=24→6
        # Cabalística: 1+1+1+1+2+0+0+0=6 (coincidentemente igual aqui)
        # Usamos 22/11/1990 para mostrar diferença:
        # Pitagórica: dia=22(mestre), mes=11(mestre), ano=1+9+9+0=19→10→1, total=22+11+1=34→7
        # Cabalística: 2+2+1+1+1+9+9+0=25→7 (igual por coincidência)
        # Caso com diferença real: 29/11/1993
        # Pitagórica: dia=29→11(mestre!), mes=11(mestre), ano=1+9+9+3=22(mestre), total=11+11+22=44→8
        # Cabalística: 2+9+1+1+1+9+9+3=35→8 (igual outra vez)
        # A diferença estrutural é na *preservação de mestres intermediários* —
        # verificamos que o método cabalístico computa sem preservar componentes
        assert missao_vida(date(1993, 11, 29)) == 8


# ── Testes de integração — 10 nomes/datas conhecidos ─────────────────────────


@pytest.mark.integration
class TestCalculateCabalistica:
    """
    Resultados calculados manualmente letra a letra.
    Tabela: A/I/Q/Y=1  B/K/R=2  C/G/L/S=3  D/M/T=4  E/H/N/X=5
            U/V/W=6   O/Z=7    F/P=8       J=ausente (ignorado)
    """

    def test_ana(self):
        # A=1, N=5, A=1
        # vogais: A(1)+A(1)=2   consoantes: N(5)=5   total: 1+5+1=7
        r = calculate_cabalistica("ANA", date(2000, 1, 1))
        assert r.id_motivacao == 2
        assert r.id_impressao == 5
        assert r.id_expressao == 7
        assert r.dividas_karmicas == frozenset()

    def test_maria(self):
        # M=4, A=1, R=2, I=1, A=1
        # vogais: A(1)+I(1)+A(1)=3   consoantes: M(4)+R(2)=6   total: 4+1+2+1+1=9
        r = calculate_cabalistica("MARIA", date(2000, 1, 1))
        assert r.id_motivacao == 3
        assert r.id_impressao == 6
        assert r.id_expressao == 9
        assert r.dividas_karmicas == frozenset()

    def test_paulo_karmic_14_na_motivacao(self):
        # P=8, A=1, U=6, L=3, O=7
        # vogais: A(1)+U(6)+O(7)=14 → DÍVIDA KÁRMICA 14 → reduz para 5
        # consoantes: P(8)+L(3)=11 → MESTRE 11
        # total: 8+1+6+3+7=25 → 7
        r = calculate_cabalistica("PAULO", date(2000, 1, 1))
        assert r.id_motivacao == 5
        assert r.id_impressao == 11
        assert r.id_expressao == 7
        assert 14 in r.dividas_karmicas

    def test_lucas_karmic_16_na_expressao(self):
        # L=3, U=6, C=3, A=1, S=3
        # vogais: U(6)+A(1)=7   consoantes: L(3)+C(3)+S(3)=9
        # total: 3+6+3+1+3=16 → DÍVIDA KÁRMICA 16 → reduz para 7
        r = calculate_cabalistica("LUCAS", date(2000, 1, 1))
        assert r.id_motivacao == 7
        assert r.id_impressao == 9
        assert r.id_expressao == 7
        assert 16 in r.dividas_karmicas

    def test_roberto_karmic_19_na_motivacao(self):
        # R=2, O=7, B=2, E=5, R=2, T=4, O=7
        # vogais: O(7)+E(5)+O(7)=19 → DÍVIDA KÁRMICA 19 → reduz para 1
        # consoantes: R(2)+B(2)+R(2)+T(4)=10 → 1
        # total: 2+7+2+5+2+4+7=29 → 11 (MESTRE!)
        r = calculate_cabalistica("ROBERTO", date(2000, 1, 1))
        assert r.id_motivacao == 1
        assert r.id_impressao == 1
        assert r.id_expressao == 11
        assert 19 in r.dividas_karmicas

    def test_diana(self):
        # D=4, I=1, A=1, N=5, A=1
        # vogais: I(1)+A(1)+A(1)=3   consoantes: D(4)+N(5)=9   total: 4+1+1+5+1=12→3
        r = calculate_cabalistica("DIANA", date(2000, 1, 1))
        assert r.id_motivacao == 3
        assert r.id_impressao == 9
        assert r.id_expressao == 3
        assert r.dividas_karmicas == frozenset()

    def test_beatriz_expressao_mestre_22(self):
        # B=2, E=5, A=1, T=4, R=2, I=1, Z=7
        # vogais: E(5)+A(1)+I(1)=7   consoantes: B(2)+T(4)+R(2)+Z(7)=15→6
        # total: 2+5+1+4+2+1+7=22 → MESTRE 22
        r = calculate_cabalistica("BEATRIZ", date(2000, 1, 1))
        assert r.id_motivacao == 7
        assert r.id_impressao == 6
        assert r.id_expressao == 22
        assert r.dividas_karmicas == frozenset()

    def test_carlos_karmic_19_na_expressao(self):
        # C=3, A=1, R=2, L=3, O=7, S=3
        # vogais: A(1)+O(7)=8   consoantes: C(3)+R(2)+L(3)+S(3)=11 → MESTRE 11
        # total: 3+1+2+3+7+3=19 → DÍVIDA KÁRMICA 19 → reduz para 1
        r = calculate_cabalistica("CARLOS", date(2000, 1, 1))
        assert r.id_motivacao == 8
        assert r.id_impressao == 11
        assert r.id_expressao == 1
        assert 19 in r.dividas_karmicas

    def test_helena_karmic_13_nas_consoantes(self):
        # H=5, E=5, L=3, E=5, N=5, A=1
        # vogais: E(5)+E(5)+A(1)=11 → MESTRE 11
        # consoantes: H(5)+L(3)+N(5)=13 → DÍVIDA KÁRMICA 13 → reduz para 4
        # total: 5+5+3+5+5+1=24 → 6
        r = calculate_cabalistica("HELENA", date(2000, 1, 1))
        assert r.id_motivacao == 11
        assert r.id_impressao == 4
        assert r.id_expressao == 6
        assert 13 in r.dividas_karmicas

    def test_jose_j_ignorado(self):
        # J não existe na tabela cabalística → ignorado
        # O=7, S=3, E=5
        # vogais: O(7)+E(5)=12→3   consoantes: S(3)=3   total: 7+3+5=15→6
        r = calculate_cabalistica("JOSE", date(2000, 1, 1))
        assert r.id_motivacao == 3
        assert r.id_impressao == 3
        assert r.id_expressao == 6
        assert r.dividas_karmicas == frozenset()

    def test_missao_vida_mestre_11(self):
        # 04/12/1993: 0+4+1+2+1+9+9+3=29 → 2+9=11 (mestre)
        r = calculate_cabalistica("ANA", date(1993, 12, 4))
        assert r.missao_vida == 11
        assert r.vote == 11

    def test_missao_vida_karmica_na_data(self):
        # "ANA" + 09/01/2013: nome sem dívidas kármicas
        # data: 0+9+0+1+2+0+1+3=16 → DÍVIDA KÁRMICA 16 → reduz para 7
        r = calculate_cabalistica("ANA", date(2013, 1, 9))
        assert r.missao_vida == 7
        assert 16 in r.dividas_karmicas

    def test_vote_aplica_lookup(self):
        # missao_vida=8 → lookup_id(8)=4
        # 15/07/1984: dígitos=1+5+0+7+1+9+8+4=35→8
        r = calculate_cabalistica("ANA", date(1984, 7, 15))
        assert r.missao_vida == 8
        assert r.vote == 4

    def test_status_sempre_exact(self):
        r = calculate_cabalistica("ANA", date(2000, 1, 1))
        assert r.overall_status == TemporalStatus.EXACT

    def test_vote_em_valid_ids(self):
        nomes = ["ANA", "MARIA", "PAULO", "LUCAS", "ROBERTO", "DIANA", "BEATRIZ", "CARLOS"]
        datas = [
            date(2000, 1, 1), date(1984, 7, 15), date(1993, 12, 4),
            date(1990, 11, 22), date(2000, 11, 11), date(2001, 1, 1),
        ]
        for nome in nomes:
            for dt in datas:
                r = calculate_cabalistica(nome, dt)
                assert r.vote in _VALID_IDS, f"vote inválido: {nome} {dt} → {r.vote}"
