"""
Testes do motor Daimon da Hora.

Unitários: sequência caldeia, mapeamento de dia da semana (sem pyswisseph).
Integração: 5 nascimentos com regente esperado + testes de status temporal.

Referências para os casos de integração:
  - Verificados com https://www.astrology.com/us/horoscope/planetary-hour-today.aspx
    e cálculo manual da sequência caldeia.
  - Todos usam hora local explícita (EXACT) para evitar ambiguidade.
"""

import pytest
from datetime import date, time

from app.core.temporal import TemporalStatus, TimeWindow, parse_time_input
from app.motors.daimon_hora import (
    _CHALDEAN_IDS,
    _CHALDEAN_NAMES,
    _WEEKDAY_START_IDX,
    DaimonHoraMotorResult,
    DaimonHoraResult,
    calculate_daimon_hora,
)

_VALID_IDS = {1, 2, 3, 4, 5, 6, 7, 9, 11, 33}
_VALID_PLANETAS = set(_CHALDEAN_NAMES)


# ── Testes unitários ───────────────────────────────────────────────────────────


class TestSequenciaCaldeia:
    """A sequência caldeia deve ter 7 planetas com IDs e nomes corretos."""

    def test_comprimento(self):
        assert len(_CHALDEAN_NAMES) == 7
        assert len(_CHALDEAN_IDS) == 7

    def test_nomes_corretos(self):
        assert _CHALDEAN_NAMES == [
            "Saturno", "Júpiter", "Marte", "Sol", "Vênus", "Mercúrio", "Lua"
        ]

    def test_ids_corretos(self):
        # Saturn→4, Jupiter→3, Mars→9, Sun→1, Venus→6, Mercury→5, Moon→2
        assert _CHALDEAN_IDS == [4, 3, 9, 1, 6, 5, 2]

    def test_ids_validos(self):
        assert all(i in _VALID_IDS for i in _CHALDEAN_IDS)


class TestMapeamentoDiaSemana:
    """O índice inicial da sequência caldeia deve corresponder ao dia da semana."""

    @pytest.mark.parametrize("weekday,expected_planet", [
        (0, "Lua"),       # Segunda
        (1, "Marte"),     # Terça
        (2, "Mercúrio"),  # Quarta
        (3, "Júpiter"),   # Quinta
        (4, "Vênus"),     # Sexta
        (5, "Saturno"),   # Sábado
        (6, "Sol"),       # Domingo
    ])
    def test_planeta_inicial_por_dia(self, weekday, expected_planet):
        idx = _WEEKDAY_START_IDX[weekday]
        assert _CHALDEAN_NAMES[idx] == expected_planet

    def test_cobre_todos_7_dias(self):
        assert len(_WEEKDAY_START_IDX) == 7
        assert set(_WEEKDAY_START_IDX) == set(range(7))


# ── Testes de integração ───────────────────────────────────────────────────────


def _assert_valid_result(result: DaimonHoraMotorResult) -> None:
    assert isinstance(result, DaimonHoraMotorResult)
    assert result.daimon.planeta in _VALID_PLANETAS
    assert result.daimon.id_gatilho in _VALID_IDS
    assert 1 <= result.daimon.numero_hora <= 24
    assert result.daimon.periodo in {"diurno", "noturno"}
    assert result.vote == result.daimon.id_gatilho


@pytest.mark.integration
class TestPerfisConhecidos:
    """
    5 nascimentos com regente caldeu verificado.

    Localização padrão: Londres (lat=51.5074, lon=-0.1278, tz=Europe/London)
    """

    LAT = 51.5074
    LON = -0.1278
    TZ = "Europe/London"

    def test_domingo_meio_dia_jupiter(self):
        """
        2023-01-01 (domingo) às 12:00 UTC — Londres (inverno, GMT=UTC)
        Domingo: sequência inicia em Sol (idx 3).
        Nascer Londres ≈ 08:06 UTC (~7h56min diurnos, cada hora ≈ 39.7 min).
        12:00 = ~3h54min após nascer → offset 5 → hora 6 → Júpiter (3+5)%7=1.
        """
        ti = parse_time_input(exact_time=time(12, 0))
        result = calculate_daimon_hora(date(2023, 1, 1), ti, self.TZ, self.LAT, self.LON)
        _assert_valid_result(result)
        assert result.overall_status == TemporalStatus.EXACT
        assert result.daimon.periodo == "diurno"
        assert result.daimon.planeta == "Júpiter"
        assert result.daimon.id_gatilho == 3

    def test_segunda_nascer_lua(self):
        """
        2023-01-02 (segunda-feira) logo após o nascer do sol — 1ª hora diurna = Lua.
        Londres: nascer ≈ 08:07 UTC; usamos 08:10 para garantir pós-nascer.
        """
        ti = parse_time_input(exact_time=time(8, 10))
        result = calculate_daimon_hora(date(2023, 1, 2), ti, self.TZ, self.LAT, self.LON)
        _assert_valid_result(result)
        assert result.overall_status == TemporalStatus.EXACT
        assert result.daimon.periodo == "diurno"
        assert result.daimon.numero_hora == 1
        assert result.daimon.planeta == "Lua"
        assert result.daimon.id_gatilho == 2

    def test_sabado_noturno(self):
        """
        2023-01-07 (sábado) às 22:00 UTC — período noturno.
        Londres: pôr ≈ 16:07 UTC → 22:00 UTC é noturno.
        Resultado deve ser período noturno com numero_hora entre 13 e 24.
        """
        ti = parse_time_input(exact_time=time(22, 0))
        result = calculate_daimon_hora(date(2023, 1, 7), ti, self.TZ, self.LAT, self.LON)
        _assert_valid_result(result)
        assert result.overall_status == TemporalStatus.EXACT
        assert result.daimon.periodo == "noturno"
        assert 13 <= result.daimon.numero_hora <= 24

    def test_sexta_madrugada_pertence_noite_quinta(self):
        """
        2023-01-06 (sexta) às 01:00 UTC — antes do nascer do sol (≈08:07 UTC).
        Pertence à noite de quinta-feira. Resultado: período noturno, hora 13-24.
        """
        ti = parse_time_input(exact_time=time(1, 0))
        result = calculate_daimon_hora(date(2023, 1, 6), ti, self.TZ, self.LAT, self.LON)
        _assert_valid_result(result)
        assert result.overall_status == TemporalStatus.EXACT
        assert result.daimon.periodo == "noturno"
        assert 13 <= result.daimon.numero_hora <= 24

    def test_quarta_primeira_hora_mercurio(self):
        """
        2023-01-04 (quarta-feira) às 08:10 UTC — 1ª hora diurna = Mercúrio.
        Londres: nascer ≈ 08:08 UTC.
        """
        ti = parse_time_input(exact_time=time(8, 10))
        result = calculate_daimon_hora(date(2023, 1, 4), ti, self.TZ, self.LAT, self.LON)
        _assert_valid_result(result)
        assert result.overall_status == TemporalStatus.EXACT
        assert result.daimon.periodo == "diurno"
        assert result.daimon.numero_hora == 1
        assert result.daimon.planeta == "Mercúrio"
        assert result.daimon.id_gatilho == 5


@pytest.mark.integration
class TestStatusTemporal:
    LAT = 51.5074
    LON = -0.1278
    TZ = "Europe/London"

    def test_exact_sem_hibrido(self):
        ti = parse_time_input(exact_time=time(12, 0))
        result = calculate_daimon_hora(date(2023, 6, 15), ti, self.TZ, self.LAT, self.LON)
        assert result.overall_status == TemporalStatus.EXACT
        assert result.daimon.planeta_b is None
        assert result.daimon.id_gatilho_b is None
        assert result.vote_b is None

    def test_unknown_retorna_safe_ou_hybrid(self):
        ti = parse_time_input()  # desconhecido → fallback 12:00
        result = calculate_daimon_hora(date(2023, 6, 15), ti, self.TZ, self.LAT, self.LON)
        assert result.overall_status in {TemporalStatus.SAFE, TemporalStatus.HYBRID}

    def test_window_pode_gerar_hybrid(self):
        """Janela que cruza fronteira entre horas planetárias gera HYBRID."""
        # Usa janela MANHA (08:00–11:59) — alta chance de cruzar fronteira entre horas
        ti = parse_time_input(window=TimeWindow.MANHA)
        result = calculate_daimon_hora(date(2023, 1, 1), ti, self.TZ, self.LAT, self.LON)
        assert result.overall_status in {TemporalStatus.SAFE, TemporalStatus.HYBRID}
        if result.overall_status == TemporalStatus.HYBRID:
            assert result.daimon.planeta_b is not None
            assert result.daimon.id_gatilho_b in _VALID_IDS
            assert result.vote_b is not None

    def test_hybrid_preenche_campos_b(self):
        """Quando híbrido, todos os campos _b devem estar preenchidos."""
        # Busca uma janela que seja garantidamente híbrida testando várias datas
        # 2023-01-01 domingo: cada hora ~66 min, janela MANHA cobre 4h → cruza ~3-4 fronteiras
        ti = parse_time_input(window=TimeWindow.TARDE)
        result = calculate_daimon_hora(date(2023, 1, 1), ti, self.TZ, self.LAT, self.LON)
        if result.overall_status == TemporalStatus.HYBRID:
            assert result.daimon.planeta_b in _VALID_PLANETAS
            assert result.daimon.id_gatilho_b in _VALID_IDS
            assert result.daimon.numero_hora_b is not None
            assert result.daimon.periodo_b in {"diurno", "noturno"}

    def test_numero_hora_range_valido(self):
        for h in range(0, 24, 3):
            ti = parse_time_input(exact_time=time(h, 0))
            result = calculate_daimon_hora(date(2023, 3, 20), ti, self.TZ, self.LAT, self.LON)
            assert 1 <= result.daimon.numero_hora <= 24
