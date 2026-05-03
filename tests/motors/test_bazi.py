"""
Testes do motor Ba Zi.

Unitários: _hour_branch, _calc_hour_stem (sem pyswisseph).
Integração: 5 nascimentos com Pilares conhecidos + testes de status temporal.
"""

import pytest
from datetime import date, time

from app.core.temporal import TemporalStatus, TimeWindow, parse_time_input
from app.motors.bazi import (
    BaZiPillar,
    BaZiPilarHora,
    BaZiResult,
    _ANIMALS,
    _STEM_ELEMENTS,
    _calc_hour_stem,
    _hour_branch,
    calculate_bazi,
)

_VALID_IDS = {1, 2, 3, 4, 5, 6, 7, 9, 11, 33}
_VALID_ANIMALS = set(_ANIMALS)
_VALID_ELEMENTOS = {"madeira", "fogo", "terra", "metal", "agua"}


# ── Testes unitários ───────────────────────────────────────────────────────────


class TestHourBranch:
    @pytest.mark.parametrize("hour,expected_animal", [
        (0,  "rato"),      # 00:00 — segunda metade do Rato (23h–01h)
        (1,  "boi"),       # 01:00 — início do Boi
        (2,  "boi"),       # 02:00 — meio do Boi
        (3,  "tigre"),     # 03:00 — início do Tigre
        (5,  "coelho"),    # 05:00 — início do Coelho
        (7,  "dragao"),    # 07:00 — início do Dragão
        (9,  "serpente"),  # 09:00 — início da Serpente
        (11, "cavalo"),    # 11:00 — início do Cavalo
        (12, "cavalo"),    # 12:00 — meio do Cavalo (noon)
        (13, "cabra"),     # 13:00 — início da Cabra
        (15, "macaco"),    # 15:00 — início do Macaco
        (17, "galo"),      # 17:00 — início do Galo
        (19, "cao"),       # 19:00 — início do Cão
        (21, "porco"),     # 21:00 — início do Porco
        (23, "rato"),      # 23:00 — início do Rato (próximo dia Ba Zi)
    ])
    def test_hour_to_animal(self, hour, expected_animal):
        branch_idx = _hour_branch(hour)
        assert _ANIMALS[branch_idx] == expected_animal

    def test_covers_all_12_animals(self):
        seen = {_ANIMALS[_hour_branch(h)] for h in range(24)}
        assert seen == _VALID_ANIMALS


class TestHourStem:
    @pytest.mark.parametrize("day_stem,hour_branch,expected_element", [
        # day 甲(0) ou 己(5): Rato começa em 甲(0=madeira)
        (0, 0, "madeira"),   # 甲日 + Rato → 甲子(madeira)
        (0, 6, "metal"),     # 甲日 + Cavalo → 庚午(metal)  — (0+6)%10=6
        (5, 0, "madeira"),   # 己日 + Rato → 甲子(madeira)   — mesmo grupo que 甲
        # day 乙(1) ou 庚(6): Rato começa em 丙(2=fogo)
        (1, 0, "fogo"),      # 乙日 + Rato → 丙子(fogo)
        (6, 0, "fogo"),      # 庚日 + Rato → 丙子(fogo)
        # day 丙(2) ou 辛(7): Rato começa em 戊(4=terra)
        (2, 0, "terra"),     # 丙日 + Rato → 戊子(terra)
        # day 丁(3) ou 壬(8): Rato começa em 庚(6=metal)
        (3, 0, "metal"),     # 丁日 + Rato → 庚子(metal)
        # day 戊(4) ou 癸(9): Rato começa em 壬(8=agua)
        (4, 0, "agua"),      # 戊日 + Rato → 壬子(agua)
        (9, 0, "agua"),      # 癸日 + Rato → 壬子(agua)
    ])
    def test_hour_stem_element(self, day_stem, hour_branch, expected_element):
        stem_idx = _calc_hour_stem(day_stem, hour_branch)
        assert _STEM_ELEMENTS[stem_idx] == expected_element


# ── Testes de integração ───────────────────────────────────────────────────────


@pytest.mark.integration
class TestPilaresConhecidos:
    """
    5 nascimentos com Pilares verificáveis:
      1. 2000-01-01 — Dia 甲戌 (calibração JDN); Ano 己卯 (Coelho da Terra, Ba Zi 1999)
      2. 1990-05-01 — Ano 庚午 (Cavalo do Metal — fato público)
      3. 2024-01-01 — Ano 癸卯 (Coelho da Água, Ba Zi 2023, antes de Li Chun 2024)
      4. 1984-02-02 — Ano 癸亥 (Porco da Água, Ba Zi 1983, antes de Li Chun 1984)
      5. 1984-02-10 — Ano 甲子 (Rato da Madeira, Ba Zi 1984, após Li Chun 1984)
    """

    def test_2000_01_01_dia_jia_xu(self):
        """Dia 甲戌: stem=甲(madeira), branch=戌(cão) → id_gatilho=4."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(2000, 1, 1), time_input, "UTC")

        assert isinstance(result, BaZiResult)
        assert result.dia.animal == "cao"
        assert result.dia.elemento == "madeira"
        assert result.dia.id_gatilho == 4
        assert result.vote == 4

    def test_2000_01_01_ano_ji_mao(self):
        """Ano 己卯: animal=coelho (Ba Zi 1999, antes de Li Chun 2000), elemento=terra."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(2000, 1, 1), time_input, "UTC")

        assert result.ano.animal == "coelho"
        assert result.ano.elemento == "terra"

    def test_1990_05_01_ano_geng_wu(self):
        """Ano 庚午: 1990 = Ano do Cavalo de Metal (fato público do horóscopo chinês)."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(1990, 5, 1), time_input, "UTC")

        assert result.ano.animal == "cavalo"
        assert result.ano.elemento == "metal"

    def test_2024_01_01_ano_gui_mao_antes_li_chun(self):
        """Ano 癸卯: jan/2024 é ainda o ano Ba Zi 2023 (Coelho da Água), antes de Li Chun."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(2024, 1, 1), time_input, "UTC")

        assert result.ano.animal == "coelho"
        assert result.ano.elemento == "agua"

    def test_1984_02_02_antes_li_chun_porco(self):
        """1984-02-02: antes de Li Chun 1984 → Ba Zi ano 1983 = Porco da Água (癸亥)."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(1984, 2, 2), time_input, "UTC")

        assert result.ano.animal == "porco"
        assert result.ano.elemento == "agua"

    def test_1984_02_10_apos_li_chun_rato(self):
        """1984-02-10: após Li Chun 1984 → Ba Zi ano 1984 = Rato da Madeira (甲子)."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(1984, 2, 10), time_input, "UTC")

        assert result.ano.animal == "rato"
        assert result.ano.elemento == "madeira"


@pytest.mark.integration
class TestStructura:
    def test_todos_campos_validos(self):
        """Verifica que todos os pilares produzem valores dentro dos conjuntos válidos."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(2000, 7, 15), time_input, "UTC")

        for pillar in [result.ano, result.mes, result.dia]:
            assert isinstance(pillar, BaZiPillar)
            assert pillar.animal in _VALID_ANIMALS
            assert pillar.elemento in _VALID_ELEMENTOS
            assert pillar.id_gatilho in _VALID_IDS

        assert isinstance(result.hora, BaZiPilarHora)
        assert result.hora.animal in _VALID_ANIMALS
        assert result.hora.elemento in _VALID_ELEMENTOS
        assert result.hora.id_gatilho in _VALID_IDS
        assert result.vote in _VALID_IDS

    def test_vote_e_dia_id_gatilho(self):
        """O voto deve sempre ser igual ao id_gatilho do Pilar do Dia."""
        time_input = parse_time_input(exact_time=time(9, 0))
        result = calculate_bazi(date(2010, 6, 21), time_input, "UTC")
        assert result.vote == result.dia.id_gatilho

    def test_cao_redireciona_para_4(self):
        """Se o Pilar do Dia for Cão (branch=戌), id_gatilho deve ser 4."""
        # 2000-01-01 = 甲戌 (Cão)
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_bazi(date(2000, 1, 1), time_input, "UTC")
        if result.dia.animal == "cao":
            assert result.dia.id_gatilho == 4


@pytest.mark.integration
class TestStatusTemporal:
    def test_exact_time(self):
        """Hora exata → hora Status EXACT, hora_b None."""
        time_input = parse_time_input(exact_time=time(14, 30))
        result = calculate_bazi(date(2000, 6, 1), time_input, "UTC")

        assert result.hora.status == TemporalStatus.EXACT
        assert result.hora.animal_b is None
        assert result.hora.id_gatilho_b is None
        assert result.overall_status == TemporalStatus.EXACT

    def test_window_always_hybrid(self):
        """Janela de tempo sempre cobre 2 shi_chen → Pilar da Hora sempre HYBRID."""
        for window in TimeWindow:
            time_input = parse_time_input(window=window)
            result = calculate_bazi(date(2000, 6, 1), time_input, "UTC")

            assert result.hora.status == TemporalStatus.HYBRID, f"Janela {window} deveria ser HYBRID"
            assert result.hora.animal_b is not None
            assert result.hora.id_gatilho_b is not None
            assert result.overall_status == TemporalStatus.HYBRID

    def test_unknown_fallback(self):
        """Hora desconhecida → fallback 12:00 → shi_chen do Cavalo (11h–13h) → Status SAFE."""
        time_input = parse_time_input()  # hora desconhecida — fallback 12:00
        result = calculate_bazi(date(2000, 6, 1), time_input, "UTC")

        assert result.hora.animal == "cavalo"
        assert result.hora.status == TemporalStatus.SAFE
        assert result.hora.animal_b is None
        assert result.overall_status == TemporalStatus.SAFE

    def test_mes_cobre_todos_12_animais(self):
        """O mês Ba Zi cobre todos os 12 animais ao longo do ano."""
        time_input = parse_time_input(exact_time=time(12, 0))
        meses_vistos = set()
        # Datas espaçadas para cobrir os 12 meses solares Ba Zi
        datas = [
            date(2000, 2, 10),   # Tigre
            date(2000, 3, 15),   # Coelho
            date(2000, 4, 15),   # Dragão
            date(2000, 5, 15),   # Serpente
            date(2000, 6, 15),   # Cavalo
            date(2000, 7, 15),   # Cabra
            date(2000, 8, 15),   # Macaco
            date(2000, 9, 15),   # Galo
            date(2000, 10, 15),  # Cão
            date(2000, 11, 15),  # Porco
            date(2000, 12, 15),  # Rato
            date(2001, 1, 15),   # Boi
        ]
        for d in datas:
            result = calculate_bazi(d, time_input, "UTC")
            meses_vistos.add(result.mes.animal)

        assert meses_vistos == _VALID_ANIMALS
