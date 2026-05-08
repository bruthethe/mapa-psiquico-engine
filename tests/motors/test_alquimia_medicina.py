"""
Testes dos motores Alquimia e Medicina.

Alquimia: signo solar → elemento → fase alquímica → id_gatilho
  Fogo → Rubedo  (id=9)
  Agua → Nigredo (id=33)
  Ar   → Albedo  (id=2)
  Terra → Citrinitas (id=1)

Medicina: dominant archetype ID → chakra → sistema + frequência Hz
  Tabela direta: 1→Coronario, 2→Sacro, 3→Plexo_Solar, 4→Raiz,
                 5→Laringeo, 6→Cardiaco, 11→Frontal
  Fallback: IDs 7, 9, 33 → Coronario

Ambos os motores são de síntese — não participam da votação do dominant archetype ID.
"""

import pytest

from app.core.temporal import TemporalStatus
from app.motors.alquimia import AlquimiaResult, calculate_alquimia
from app.motors.medicina import MedicinaResult, calculate_medicina


# ── Alquimia ──────────────────────────────────────────────────────────────────


class TestCalculateAlquimia:

    def test_fogo_rubedo(self):
        # Aries, Leao, Sagitario → Rubedo (id=9)
        for signo in ["Aries", "Leao", "Sagitario"]:
            r = calculate_alquimia(signo)
            assert r.elemento == "Fogo", signo
            assert r.fase == "Rubedo", signo
            assert r.id_gatilho == 9, signo

    def test_agua_nigredo(self):
        # Cancer, Escorpiao, Peixes → Nigredo (id=33)
        for signo in ["Cancer", "Escorpiao", "Peixes"]:
            r = calculate_alquimia(signo)
            assert r.elemento == "Agua", signo
            assert r.fase == "Nigredo", signo
            assert r.id_gatilho == 33, signo

    def test_ar_albedo(self):
        # Gemeos, Libra, Aquario → Albedo (id=2)
        for signo in ["Gemeos", "Libra", "Aquario"]:
            r = calculate_alquimia(signo)
            assert r.elemento == "Ar", signo
            assert r.fase == "Albedo", signo
            assert r.id_gatilho == 2, signo

    def test_terra_citrinitas(self):
        # Touro, Virgem, Capricornio → Citrinitas (id=1)
        for signo in ["Touro", "Virgem", "Capricornio"]:
            r = calculate_alquimia(signo)
            assert r.elemento == "Terra", signo
            assert r.fase == "Citrinitas", signo
            assert r.id_gatilho == 1, signo

    def test_signo_solar_preservado(self):
        r = calculate_alquimia("Escorpiao")
        assert r.signo_solar == "Escorpiao"

    def test_operacao_preenchida(self):
        r = calculate_alquimia("Aries")
        assert r.operacao  # não vazio

    def test_status_sempre_exact(self):
        r = calculate_alquimia("Leao")
        assert r.overall_status == TemporalStatus.EXACT

    def test_todos_signos_mapeados(self):
        signos = [
            "Aries", "Touro", "Gemeos", "Cancer", "Leao", "Virgem",
            "Libra", "Escorpiao", "Sagitario", "Capricornio", "Aquario", "Peixes",
        ]
        for s in signos:
            r = calculate_alquimia(s)
            assert r.fase in {"Nigredo", "Albedo", "Citrinitas", "Rubedo"}


# ── Medicina ─────────────────────────────────────────────────────────────────


class TestCalculateMedicina:

    def test_id_1_coronario(self):
        r = calculate_medicina(1)
        assert r.chakra == "Coronario"
        assert r.frequencia == "963Hz"
        assert r.fallback is False

    def test_id_2_sacro(self):
        r = calculate_medicina(2)
        assert r.chakra == "Sacro"
        assert r.frequencia == "417Hz"
        assert r.fallback is False

    def test_id_4_raiz(self):
        r = calculate_medicina(4)
        assert r.chakra == "Raiz"
        assert r.frequencia == "396Hz"
        assert r.fallback is False

    def test_id_11_frontal(self):
        r = calculate_medicina(11)
        assert r.chakra == "Frontal"
        assert r.frequencia == "852Hz"
        assert r.fallback is False

    def test_id_6_cardiaco(self):
        r = calculate_medicina(6)
        assert r.chakra == "Cardiaco"
        assert r.fallback is False

    def test_fallback_id_7(self):
        # ID 7 não tem chakra direto → Coronario
        r = calculate_medicina(7)
        assert r.chakra == "Coronario"
        assert r.fallback is True

    def test_fallback_id_9(self):
        r = calculate_medicina(9)
        assert r.chakra == "Coronario"
        assert r.fallback is True

    def test_fallback_id_33(self):
        r = calculate_medicina(33)
        assert r.chakra == "Coronario"
        assert r.fallback is True

    def test_todos_ids_diretos_sem_fallback(self):
        ids_diretos = {1, 2, 3, 4, 5, 6, 11}
        for id_ in ids_diretos:
            r = calculate_medicina(id_)
            assert r.fallback is False, f"ID {id_} deveria ter chakra direto"

    def test_sistema_e_frequencia_preenchidos(self):
        for id_ in [1, 2, 3, 4, 5, 6, 11]:
            r = calculate_medicina(id_)
            assert r.sistema
            assert r.frequencia

    def test_status_sempre_exact(self):
        r = calculate_medicina(1)
        assert r.overall_status == TemporalStatus.EXACT
