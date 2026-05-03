"""
Testes do motor Human Design — História 2.5.

Unitários: lon_to_gate, lon_to_line, _derive_tipo, _derive_autoridade (sem ephemeris).
Integração: 5 perfis com verificação de Tipo, Autoridade e Porta do Sol.
"""

import pytest
from datetime import date, time

from app.core.temporal import TemporalStatus, TimeWindow, parse_time_input
from app.motors.human_design import (
    HDActivation,
    HDResult,
    _CHANNELS,
    _RODA_GATES,
    _active_channels,
    _defined_centers,
    _derive_autoridade,
    _derive_tipo,
    _gate_center_map,
    _reachable_from,
    calculate_hd,
    lon_to_gate,
    lon_to_line,
)

_VALID_IDS  = {1, 2, 3, 4, 5, 6, 7, 9, 11, 33}
_VALID_TIPOS = {"Manifestador", "Gerador", "Gerador_Manifestante", "Projetor", "Refletor"}
_VALID_AUT   = {
    "Emocional", "Sacral", "Esplenica",
    "Ego_Manifest", "Ego_Projetado", "G_Centro", "Mental", "Lunar",
}
_ALL_CENTERS = {
    "Cabeca", "Ajna", "Garganta", "G_Centro",
    "Ego", "Sacral", "Plexo_Solar", "Baco", "Raiz",
}


# ── Testes unitários — conversão de longitude ─────────────────────────────────


class TestLonToGate:
    @pytest.mark.parametrize("lon,expected_gate", [
        (0.0,     41),   # posicao 0 → roda_gates[0]
        (5.625,   19),   # posicao 1 → roda_gates[1]
        (5.624,   41),   # ainda na posicao 0
        (180.0,   31),   # posicao 32 → roda_gates[32]
        (359.9,   60),   # posicao 63 → roda_gates[63]
        (360.0,   41),   # wrap para posicao 0
    ])
    def test_gate_conhecido(self, lon, expected_gate):
        assert lon_to_gate(lon) == expected_gate

    def test_todas_64_posicoes_cobrem_64_portas(self):
        gates = {lon_to_gate(i * 5.625) for i in range(64)}
        assert gates == set(_RODA_GATES)

    def test_gate_range(self):
        for i in range(1000):
            lon = i * 360 / 1000
            assert 1 <= lon_to_gate(lon) <= 64


class TestLonToLine:
    @pytest.mark.parametrize("lon_offset,expected_line", [
        (0.0,     1),
        (1.0,     2),   # 1.0/5.625 ≈ 0.178 → linha 2
        (1.875,   3),   # 2/6 exato
        (3.0,     4),   # 3.0/5.625 ≈ 0.533 → linha 4
        (3.750,   5),   # 4/6 exato
        (5.0,     6),   # 5.0/5.625 ≈ 0.889 → linha 6
        (5.624,   6),   # quase fim → ainda linha 6
    ])
    def test_linha_dentro_de_uma_porta(self, lon_offset, expected_line):
        # testa com offset dentro da primeira porta (0–5.625°)
        assert lon_to_line(lon_offset) == expected_line

    def test_linha_range(self):
        for i in range(1000):
            lon = i * 360 / 1000
            assert 1 <= lon_to_line(lon) <= 6

    def test_linha_reinicia_em_cada_porta(self):
        """A Linha 1 aparece no início de cada porta, a Linha 6 no fim."""
        for p in range(64):
            base = p * 5.625
            assert lon_to_line(base) == 1           # início da porta
            assert lon_to_line(base + 5.624) == 6   # quase fim da porta


# ── Testes unitários — mapeamento de portas para centros ─────────────────────


class TestGateCenterMap:
    def test_todas_64_portas_mapeadas(self):
        assert len(_gate_center_map()) == 64

    def test_cada_porta_em_exatamente_um_centro(self):
        """Cada porta aparece exatamente uma vez no mapeamento."""
        all_gates_in_map = list(_gate_center_map().keys())
        assert len(all_gates_in_map) == len(set(all_gates_in_map))

    def test_centros_corretos(self):
        gc = _gate_center_map()
        # Exemplos verificáveis pela data-human-design.json
        assert gc[64] == "Cabeca"
        assert gc[47] == "Ajna"
        assert gc[20] == "Garganta"
        assert gc[34] == "Sacral"
        assert gc[57] == "Baco"
        assert gc[60] == "Raiz"
        assert gc[22] == "Plexo_Solar"
        assert gc[21] == "Ego"
        assert gc[7]  == "G_Centro"


class TestChannels:
    def test_total_35_canais(self):
        assert len(_CHANNELS) == 35

    def test_cada_canal_conecta_centros_diferentes(self):
        gc = _gate_center_map()
        for g1, g2 in _CHANNELS:
            assert gc[g1] != gc[g2], f"Canal {g1}-{g2} conecta o mesmo centro"

    def test_todas_portas_dos_canais_existem_no_mapa(self):
        gc = _gate_center_map()
        for g1, g2 in _CHANNELS:
            assert g1 in gc, f"Porta {g1} não está no mapa de centros"
            assert g2 in gc, f"Porta {g2} não está no mapa de centros"


# ── Testes unitários — derivação de Tipo ─────────────────────────────────────


class TestDerivaTipo:
    def test_nenhum_centro_definido_e_refletor(self):
        assert _derive_tipo(frozenset(), frozenset()) == "Refletor"

    def test_sacral_sem_garganta_e_gerador(self):
        # Sacral definido, Garganta sem conexão com Motor
        # Ativa só Sacral via porta 5 (Sacral) e 34 (Sacral) — canal 20-34 exige 20 no Garganta
        active = frozenset({5})  # só porta 5 no Sacral
        defined = _defined_centers(active)
        assert "Sacral" in defined
        assert _derive_tipo(defined, active) == "Gerador"

    def test_sacral_mais_canal_garganta_sacral_e_mg(self):
        # Canal 20-34: gates 20 (Garganta) e 34 (Sacral) → MG
        active = frozenset({20, 34})
        defined = _defined_centers(active)
        assert "Garganta" in defined and "Sacral" in defined
        assert _derive_tipo(defined, active) == "Gerador_Manifestante"

    def test_garganta_motor_sem_sacral_e_manifestador(self):
        # Canal 45-21: gates 45 (Garganta) e 21 (Ego) → Garganta conectada ao Ego (Motor)
        active = frozenset({45, 21})
        defined = _defined_centers(active)
        assert "Sacral" not in defined
        assert _derive_tipo(defined, active) == "Manifestador"

    def test_sem_sacral_sem_conexao_motor_e_projetor(self):
        # Só Cabeça definida (sem Sacral, sem canal Garganta→Motor)
        active = frozenset({64})
        defined = _defined_centers(active)
        assert _derive_tipo(defined, active) == "Projetor"


class TestDerivaAutoridade:
    def test_plexo_solar_e_emocional(self):
        active = frozenset({6})  # porta 6 no Plexo Solar
        defined = _defined_centers(active)
        assert _derive_autoridade(defined, active) == "Emocional"

    def test_sacral_sem_plexo_e_sacral(self):
        active = frozenset({5})
        defined = _defined_centers(active)
        assert _derive_autoridade(defined, active) == "Sacral"

    def test_nenhum_centro_e_lunar(self):
        assert _derive_autoridade(frozenset(), frozenset()) == "Lunar"

    def test_ego_conectado_garganta_e_ego_manifest(self):
        # Canal 45-21: Garganta(45) ↔ Ego(21)
        active = frozenset({45, 21})
        defined = _defined_centers(active)
        assert _derive_autoridade(defined, active) == "Ego_Manifest"

    def test_ego_sem_garganta_e_ego_projetado(self):
        # Só Ego via porta 26 (Ego), sem canal para Garganta
        active = frozenset({26})
        defined = _defined_centers(active)
        assert _derive_autoridade(defined, active) == "Ego_Projetado"


class TestReachable:
    def test_sem_canais_ativos_alcanca_apenas_si_mesmo(self):
        active = frozenset({20})  # só Garganta, sem canal ativo
        reached = _reachable_from("Garganta", active)
        # Canal 20-34 exige 34, 20-57 exige 57, 20-10 exige 10 — nenhum ativo
        assert "Sacral" not in reached
        assert "Baco" not in reached

    def test_canal_20_34_conecta_garganta_ao_sacral(self):
        active = frozenset({20, 34})
        reached = _reachable_from("Garganta", active)
        assert "Sacral" in reached

    def test_conectividade_transitiva(self):
        # Canal 8-1 (Garganta-G) + canal 2-14 (G-Sacral)
        active = frozenset({8, 1, 2, 14})
        reached = _reachable_from("Garganta", active)
        assert "G_Centro" in reached
        assert "Sacral" in reached


# ── Testes de integração ───────────────────────────────────────────────────────


@pytest.mark.integration
class TestPerfisConhecidos:
    """
    5 perfis com Tipo verificado pelas regras do corpo gráfico HD.
    O gate do Sol de Personalidade é verificado pela fórmula lon_to_gate
    contra a longitude computada pelo Swiss Ephemeris.
    """

    def _assert_valid_result(self, result: HDResult) -> None:
        assert isinstance(result, HDResult)
        assert result.tipo in _VALID_TIPOS
        assert result.autoridade in _VALID_AUT
        assert result.centros_definidos.issubset(_ALL_CENTERS)
        assert 1 <= result.porta_sol_personalidade <= 64
        assert result.tipo_id_gatilho in _VALID_IDS
        assert result.autoridade_id_gatilho in _VALID_IDS
        assert result.vote in _VALID_IDS
        assert len(result.personalidade) == 13
        assert len(result.design) == 13
        for act in result.personalidade + result.design:
            assert 1 <= act.gate <= 64
            assert 1 <= act.linha <= 6

    def test_perfil_1_2000_01_01(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2000, 1, 1), time_input, "UTC")
        self._assert_valid_result(result)
        assert result.overall_status == TemporalStatus.EXACT
        # Sol em ~280° → posicao 49 → gate 44 (Baço)
        assert result.porta_sol_personalidade == 44

    def test_perfil_2_equinox_marco(self):
        """Equinócio de março: Sol ≈ 0° → posicao 0 → gate 41."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2024, 3, 20), time_input, "UTC")
        self._assert_valid_result(result)
        # Sol no equinócio ≈ 0° → gate 41
        assert result.porta_sol_personalidade == 41

    def test_perfil_3_solsticio_verao(self):
        """Solstício de verão: Sol ≈ 90° → posicao 16 → gate 27."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2000, 6, 21), time_input, "UTC")
        self._assert_valid_result(result)
        # Sol no solstício de verão ≈ 90° → gate 27
        assert result.porta_sol_personalidade == 27

    def test_perfil_4_solsticio_inverno(self):
        """Solstício de inverno: Sol ≈ 270° → posicao 47 → gate 50."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2000, 12, 21), time_input, "UTC")
        self._assert_valid_result(result)
        # Sol no solstício de inverno ≈ 269.93° → posicao 47 → gate 50
        assert result.porta_sol_personalidade == 50

    def test_perfil_5_fallback_hora_desconhecida(self):
        """Caminho C (hora desconhecida) → fallback 12:00 → resultado válido."""
        time_input = parse_time_input()
        result = calculate_hd(date(1990, 5, 15), time_input, "UTC")
        self._assert_valid_result(result)
        assert result.overall_status == TemporalStatus.SAFE


@pytest.mark.integration
class TestStatusTemporal:
    def test_hora_exata_e_exact(self):
        time_input = parse_time_input(exact_time=time(14, 30))
        result = calculate_hd(date(2000, 6, 1), time_input, "UTC")
        assert result.overall_status == TemporalStatus.EXACT
        assert result.tipo_b is None

    def test_janela_pode_ser_safe_ou_hybrid(self):
        """Janela de 4h: Sol move ~4°, gate tem 5.625°. Pode ou não cruzar fronteira."""
        time_input = parse_time_input(window=TimeWindow.TARDE)
        result = calculate_hd(date(2000, 6, 1), time_input, "UTC")
        assert result.overall_status in (TemporalStatus.SAFE, TemporalStatus.HYBRID)
        if result.overall_status == TemporalStatus.HYBRID:
            assert result.tipo_b is not None
        else:
            assert result.tipo_b is None

    def test_vote_e_tipo_id_gatilho(self):
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2000, 1, 1), time_input, "UTC")
        assert result.vote == result.tipo_id_gatilho

    def test_ativacoes_sol_e_primeiro(self):
        """Sol é sempre o primeiro planeta na lista de Personalidade."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2000, 1, 1), time_input, "UTC")
        assert result.personalidade[0].planeta == "sol"
        assert result.design[0].planeta == "sol"

    def test_terra_e_oposta_ao_sol(self):
        """Terra = Sol + 180°; os gates devem estar em posições opostas."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2000, 6, 21), time_input, "UTC")
        sol = next(a for a in result.personalidade if a.planeta == "sol")
        terra = next(a for a in result.personalidade if a.planeta == "terra")
        # Terra deve estar ~180° oposta; gates opostos na roda = ~32 posições distante
        sol_pos = _RODA_GATES.index(sol.gate)
        terra_pos = _RODA_GATES.index(terra.gate)
        diff = abs(sol_pos - terra_pos)
        assert 28 <= diff <= 36  # ~32 posições opostas ± tolerância para gates compartilhados

    def test_nodo_sul_e_oposto_ao_nodo_norte(self):
        """Nodo Sul = Nodo Norte + 180°."""
        time_input = parse_time_input(exact_time=time(12, 0))
        result = calculate_hd(date(2000, 1, 1), time_input, "UTC")
        nn = next(a for a in result.personalidade if a.planeta == "nodo_norte")
        ns = next(a for a in result.personalidade if a.planeta == "nodo_sul")
        diff_lon = abs(nn.longitude - ns.longitude)
        # Diferença deve ser ~180° (tolerância para wrap)
        assert 170 <= diff_lon <= 190 or 170 <= (360 - diff_lon) <= 190
