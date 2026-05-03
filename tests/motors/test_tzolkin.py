"""
Testes do motor Tzolkin Maya (Dreamspell).

Unitários: dreamspell_days, kin, tom, selo, oráculo (sem pyswisseph).
Integração: 10 datas conhecidas da tradição Dreamspell.
"""

import pytest
from datetime import date

from app.core.temporal import TemporalStatus
from app.motors.tzolkin import (
    TzolkinResult,
    TzolkinSelo,
    TzolkinTom,
    TzolkinOraculo,
    analogo,
    antipoda,
    calculate_tzolkin,
    dreamspell_days,
    guia,
    kin_from_days,
    oculto,
    selo_pos_from_kin,
    tom_from_kin,
)

_VALID_IDS = {1, 2, 3, 4, 5, 6, 7, 9, 11, 33}
_REF = date(1987, 7, 26)  # Kin 1


# ── Testes unitários — contagem de dias Dreamspell ────────────────────────────


class TestDreamspellDays:
    def test_referencia_e_zero(self):
        assert dreamspell_days(_REF) == 0

    def test_dia_seguinte(self):
        assert dreamspell_days(date(1987, 7, 27)) == 1

    def test_dia_anterior(self):
        assert dreamspell_days(date(1987, 7, 25)) == -1

    def test_pula_29_fevereiro_para_frente(self):
        """29/02 não é contado: 28/02 e 01/03 são consecutivos no ciclo."""
        d28 = dreamspell_days(date(1988, 2, 28))
        d01 = dreamspell_days(date(1988, 3, 1))
        assert d01 == d28 + 1  # sem lacuna de 2 dias no ciclo

    def test_nascido_em_29_fev_usa_28_fev(self):
        """Nascido em 29/02 tem o mesmo Kin que 28/02."""
        assert dreamspell_days(date(1988, 2, 29)) == dreamspell_days(date(1988, 2, 28))

    def test_multiplos_bissextos_acumulam(self):
        """Cada 29/02 entre ref e data desconta 1 dia do ciclo."""
        # 1988, 1992, 1996: 3 bissextos antes de 2000-01-01
        calendar_delta = (date(2000, 1, 1) - _REF).days
        assert dreamspell_days(date(2000, 1, 1)) == calendar_delta - 3


# ── Testes unitários — fórmulas Kin / Tom / Selo ──────────────────────────────


class TestKinFormula:
    @pytest.mark.parametrize("dias,expected_kin", [
        (0,    1),    # referência
        (1,    2),
        (259,  260),  # último Kin do ciclo
        (260,  1),    # reinício do ciclo
        (-1,   260),  # dia anterior à referência
        (-260, 1),    # 260 dias antes = mesmo Kin
    ])
    def test_kin(self, dias, expected_kin):
        assert kin_from_days(dias) == expected_kin

    def test_kin_range(self):
        for dias in range(-520, 521):
            kin = kin_from_days(dias)
            assert 1 <= kin <= 260, f"Kin fora de [1,260]: dias={dias}, kin={kin}"


class TestTomFormula:
    def test_tom_range(self):
        for kin in range(1, 261):
            assert 1 <= tom_from_kin(kin) <= 13

    @pytest.mark.parametrize("kin,expected_tom", [
        (1,   1),
        (13,  13),
        (14,  1),    # reinício do ciclo de 13
        (260, 13),   # último Kin = Tom 13
    ])
    def test_tom_conhecido(self, kin, expected_tom):
        assert tom_from_kin(kin) == expected_tom


class TestSeloFormula:
    def test_selo_range(self):
        for kin in range(1, 261):
            assert 1 <= selo_pos_from_kin(kin) <= 20

    @pytest.mark.parametrize("kin,expected_pos", [
        (1,   1),
        (20,  20),
        (21,  1),    # reinício do ciclo de 20
        (260, 20),   # último Kin = Selo 20
    ])
    def test_selo_conhecido(self, kin, expected_pos):
        assert selo_pos_from_kin(kin) == expected_pos


# ── Testes unitários — Oráculo da Quinta Força ────────────────────────────────


class TestOraculo:
    @pytest.mark.parametrize("seal,expected_analogo", [
        (1,  2),   # Dragão ↔ Vento (Vermelho ↔ Branco, ímpar+1)
        (2,  1),   # Vento ↔ Dragão (par-1)
        (3,  4),
        (19, 20),
        (20, 19),
    ])
    def test_analogo(self, seal, expected_analogo):
        assert analogo(seal) == expected_analogo

    @pytest.mark.parametrize("seal,expected_antipoda", [
        (1,  11),  # Dragão ↔ Macaco
        (11, 1),   # Macaco ↔ Dragão
        (10, 20),
        (20, 10),
    ])
    def test_antipoda(self, seal, expected_antipoda):
        assert antipoda(seal) == expected_antipoda

    @pytest.mark.parametrize("seal,expected_oculto", [
        (1,  20),   # Dragão ↔ Sol
        (20, 1),    # Sol ↔ Dragão
        (10, 11),   # Cachorro ↔ Macaco
        (11, 10),
    ])
    def test_oculto(self, seal, expected_oculto):
        assert oculto(seal) == expected_oculto

    def test_oculto_soma_21(self):
        """Para todo Selo, Selo + Oculto = 21."""
        for s in range(1, 21):
            assert s + oculto(s) == 21

    def test_guia_tom1_e_proprio_selo(self):
        """Tom Magnético (1) → Guia sempre é o próprio Selo."""
        for s in range(1, 21):
            assert guia(s, 1) == s

    @pytest.mark.parametrize("seal,tom,expected_guia", [
        (1,  2, 5),   # Dragão + Tom 2 → Serpente (fam. Vermelho pos 1)
        (2,  2, 6),   # Vento + Tom 2 → Enlaçador (fam. Branco pos 1)
        (1,  5, 17),  # Dragão + Tom 5 → Terra (fam. Vermelho pos 4)
        (20, 1, 20),  # Sol + Tom 1 → Sol (próprio)
    ])
    def test_guia_conhecido(self, seal, tom, expected_guia):
        assert guia(seal, tom) == expected_guia

    def test_guia_range(self):
        for s in range(1, 21):
            for t in range(1, 14):
                g = guia(s, t)
                assert 1 <= g <= 20, f"Guia fora de range: seal={s}, tom={t}, guia={g}"

    def test_guia_mesma_familia_de_cor(self):
        """Guia sempre pertence à mesma família de cor do Selo."""
        for s in range(1, 21):
            for t in range(1, 14):
                color_self = (s - 1) % 4
                color_guia = (guia(s, t) - 1) % 4
                assert color_self == color_guia, f"Guia cor diferente: seal={s}, tom={t}"


# ── Testes de integração — 10 datas conhecidas ────────────────────────────────


@pytest.mark.integration
class TestDatasConhecidas:
    """
    10 datas com Kin, Tom e Selo verificáveis pela fórmula Dreamspell.
    Calculados a partir da referência 1987-07-26 = Kin 1 (Dragão Magnético).
    """

    @pytest.mark.parametrize("birth_date,expected_kin,expected_tom,expected_seal,nota", [
        # ── Referência e dias consecutivos ──
        (date(1987, 7, 26), 1,   1,  1,  "Referência: Dragão Magnético"),
        (date(1987, 7, 27), 2,   2,  2,  "Kin 2: Vento Lunar"),
        # ── Virada de Selo (Seal wraps at 20) ──
        (date(1987, 8, 14), 20,  7,  20, "Kin 20: Sol Ressonante (último Kin da sequência de selos)"),
        (date(1987, 8, 15), 21,  8,  1,  "Kin 21: Dragão Galáctico (reinício do Selo)"),
        # ── Dia antes da referência ──
        (date(1987, 7, 25), 260, 13, 20, "Kin 260: Sol Cósmico (dia anterior à ref)"),
        # ── Meio do primeiro ciclo ──
        (date(1987, 9,  7), 44,  5,  4,  "Kin 44: Semente Harmônica"),
        # ── Regra do ano bissexto ──
        (date(1988, 2, 29), 218, 10, 18, "29/02 usa Kin do 28/02: Espelho Planetário"),
        (date(1988, 3,  1), 219, 11, 19, "01/03 é Kin seguinte ao 28/02: Tormenta Espectral"),
        # ── Datas distantes ──
        (date(1987, 7, 25), 260, 13, 20, "1 dia antes da ref"),
        (date(2000, 1,  1), 120, 3,  20, "2000-01-01: Sol Elétrico (3 bissextos excluídos)"),
    ])
    def test_kin_tom_selo(self, birth_date, expected_kin, expected_tom, expected_seal, nota):
        result = calculate_tzolkin(birth_date)
        assert result.kin == expected_kin, nota
        assert result.tom.tom == expected_tom, nota
        assert result.selo.posicao == expected_seal, nota

    def test_oraculo_kin1(self):
        """Kin 1 (Dragão Magnético, Seal=1, Tom=1): verificação completa do Oráculo."""
        result = calculate_tzolkin(_REF)
        assert result.oraculo.guia.posicao == 1     # Tom 1 → Guia = próprio Selo
        assert result.oraculo.analogo.posicao == 2  # Dragão ↔ Vento
        assert result.oraculo.antipoda.posicao == 11  # Macaco
        assert result.oraculo.oculto.posicao == 20  # Sol

    def test_oraculo_kin2(self):
        """Kin 2 (Vento Lunar, Seal=2, Tom=2): Guia = Enlaçador (pos 6)."""
        result = calculate_tzolkin(date(1987, 7, 27))
        assert result.oraculo.guia.posicao == 6
        assert result.oraculo.analogo.posicao == 1   # Vento ↔ Dragão
        assert result.oraculo.antipoda.posicao == 12  # Humano
        assert result.oraculo.oculto.posicao == 19   # Tormenta


@pytest.mark.integration
class TestEstrutura:
    def test_estrutura_completa(self):
        result = calculate_tzolkin(date(2000, 6, 15))

        assert isinstance(result, TzolkinResult)
        assert isinstance(result.selo, TzolkinSelo)
        assert isinstance(result.tom, TzolkinTom)
        assert isinstance(result.oraculo, TzolkinOraculo)
        assert 1 <= result.kin <= 260
        assert 1 <= result.selo.posicao <= 20
        assert 1 <= result.tom.tom <= 13
        assert result.vote in _VALID_IDS
        assert result.overall_status == TemporalStatus.EXACT

    def test_ids_validos_em_todos_os_campos(self):
        result = calculate_tzolkin(date(1987, 7, 26))
        for obj in [result.selo, result.oraculo.guia, result.oraculo.analogo,
                    result.oraculo.antipoda, result.oraculo.oculto]:
            assert obj.id_gatilho in _VALID_IDS, f"id inválido em {obj.nome}"
        assert result.tom.id_gatilho in _VALID_IDS

    def test_todos_os_20_selos_alcancaveis(self):
        """Iterando 260 Kins a partir da referência cobre todos os 20 Selos."""
        selos_vistos = set()
        for i in range(260):
            result = calculate_tzolkin(date(1987 + i // 365, 7, 26) if False else _REF)
            _ = result  # satisfaz linter; usamos a abordagem direta abaixo
        for kin in range(1, 261):
            selos_vistos.add(selo_pos_from_kin(kin))
        assert selos_vistos == set(range(1, 21))

    def test_todos_os_13_tons_alcancaveis(self):
        tons_vistos = {tom_from_kin(k) for k in range(1, 261)}
        assert tons_vistos == set(range(1, 14))

    def test_vote_igual_a_id_do_selo(self):
        result = calculate_tzolkin(date(2010, 3, 22))
        assert result.vote == result.selo.id_gatilho
