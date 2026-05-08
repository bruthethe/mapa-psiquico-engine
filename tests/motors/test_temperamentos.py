"""
Testes do motor Temperamentos.

Input: dicionário {planet_key: signo_string} com signos do motor Tropical.
Pesos: Sol=3, Lua=3, Ascendente=3, planetas pessoais/sociais=1.
Tiebreaker: 1º elemento do Sol; 2º menor id_gatilho.

id_gatilho por elemento:
  Fogo (Colerico)   = 9
  Ar   (Sanguineo)  = 5
  Terra (Melancolico) = 4
  Agua (Fleumatico) = 2
"""

import pytest

from app.core.temporal import TemporalStatus
from app.motors.temperamentos import TemperamentosResult, calculate_temperamentos

_VALID_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})


@pytest.mark.integration
class TestCalculateTemperamentos:

    def test_fogo_dominante_claro(self):
        # Sol+Lua+Asc em Fogo (9 pts), resto em Terra (5 pts)
        r = calculate_temperamentos({
            "sol": "Aries", "lua": "Leao", "ascendente": "Sagitario",
            "mercurio": "Touro", "venus": "Touro", "marte": "Touro",
            "jupiter": "Touro", "saturno": "Touro",
        })
        assert r.elemento_dominante == "Fogo"
        assert r.temperamento_dominante == "Colerico"
        assert r.elemento_secundario == "Terra"
        assert r.temperamento_secundario == "Melancolico"
        assert r.pontuacao == {"Fogo": 9, "Terra": 5, "Ar": 0, "Agua": 0}
        assert r.id_gatilho == 9
        assert r.vote == 9

    def test_terra_dominante_claro(self):
        # Sol em Fogo(3); Lua+Asc em Terra(6); planetas em Terra(3)+Ar(2)
        r = calculate_temperamentos({
            "sol": "Leao", "lua": "Virgem", "ascendente": "Touro",
            "mercurio": "Touro", "venus": "Touro", "marte": "Touro",
            "jupiter": "Gemeos", "saturno": "Gemeos",
        })
        assert r.elemento_dominante == "Terra"
        assert r.temperamento_dominante == "Melancolico"
        assert r.id_gatilho == 4
        assert r.vote == 4

    def test_empate_dominante_sol_decide(self):
        # Fogo, Terra e Ar empatados a 4 pts cada; Sol em Fogo → Fogo vence
        r = calculate_temperamentos({
            "sol": "Aries",    "lua": "Touro",   "ascendente": "Gemeos",
            "mercurio": "Cancer", "venus": "Aries", "marte": "Touro",
            "jupiter": "Gemeos", "saturno": "Cancer",
        })
        # Fogo: sol(3)+venus(1)=4; Terra: lua(3)+marte(1)=4; Ar: asc(3)+jupiter(1)=4; Agua: merc(1)+sat(1)=2
        assert r.pontuacao == {"Fogo": 4, "Terra": 4, "Ar": 4, "Agua": 2}
        assert r.elemento_dominante == "Fogo"
        assert r.temperamento_dominante == "Colerico"

    def test_empate_secundario_menor_id_decide(self):
        # Fogo domina (9); Terra e Ar empatados a 2 — Sol não em nenhum → Terra(id=4) < Ar(id=5)
        r = calculate_temperamentos({
            "sol": "Aries", "lua": "Leao", "ascendente": "Sagitario",
            "mercurio": "Touro", "venus": "Gemeos", "marte": "Cancer",
            "jupiter": "Touro", "saturno": "Gemeos",
        })
        assert r.elemento_dominante == "Fogo"
        assert r.elemento_secundario == "Terra"   # Terra(id=4) < Ar(id=5)
        assert r.pontuacao == {"Fogo": 9, "Terra": 2, "Ar": 2, "Agua": 1}

    def test_sem_ascendente(self):
        # Ascendente None — ignorado no cálculo
        r = calculate_temperamentos({
            "sol": "Aries", "lua": "Leao", "ascendente": None,
            "mercurio": "Touro", "venus": "Touro", "marte": "Touro",
            "jupiter": "Touro", "saturno": "Touro",
        })
        # Fogo: sol(3)+lua(3)=6; Terra: 5 planetas x1=5
        assert r.pontuacao == {"Fogo": 6, "Terra": 5, "Ar": 0, "Agua": 0}
        assert r.elemento_dominante == "Fogo"

    def test_ascendente_ausente(self):
        # Chave "ascendente" ausente no dict — mesmo comportamento que None
        r = calculate_temperamentos({
            "sol": "Aries", "lua": "Leao",
            "mercurio": "Touro", "venus": "Touro", "marte": "Touro",
            "jupiter": "Touro", "saturno": "Touro",
        })
        assert r.pontuacao["Fogo"] == 6

    def test_agua_dominante(self):
        # Sol+Lua+Asc em Água; resto em Ar
        r = calculate_temperamentos({
            "sol": "Cancer", "lua": "Escorpiao", "ascendente": "Peixes",
            "mercurio": "Gemeos", "venus": "Libra", "marte": "Aquario",
            "jupiter": "Gemeos", "saturno": "Libra",
        })
        assert r.elemento_dominante == "Agua"
        assert r.temperamento_dominante == "Fleumatico"
        assert r.id_gatilho == 2
        assert r.vote == 2

    def test_status_sempre_exact(self):
        r = calculate_temperamentos({
            "sol": "Aries", "lua": "Leao", "ascendente": "Sagitario",
            "mercurio": "Touro", "venus": "Touro", "marte": "Touro",
            "jupiter": "Touro", "saturno": "Touro",
        })
        assert r.overall_status == TemporalStatus.EXACT

    def test_vote_em_valid_ids(self):
        casos = [
            {"sol": "Aries", "lua": "Leao", "ascendente": "Sagitario",
             "mercurio": "Cancer", "venus": "Cancer", "marte": "Cancer",
             "jupiter": "Cancer", "saturno": "Cancer"},
            {"sol": "Touro", "lua": "Virgem", "ascendente": "Capricornio",
             "mercurio": "Aries", "venus": "Aries", "marte": "Aries",
             "jupiter": "Aries", "saturno": "Aries"},
        ]
        for pos in casos:
            r = calculate_temperamentos(pos)
            assert r.vote in _VALID_IDS
