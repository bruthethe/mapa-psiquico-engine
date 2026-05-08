"""Testes do Grupo B — Cap. 2, Cap. 3, Cap. 8 (5.5)."""

import pytest

from app.chapters.grupo_b import (
    Cap2Data, Cap3Data, Cap8Data,
    assemble_cap2, assemble_cap3, assemble_cap8,
)
from app.core.motor_types import AtmakarakaResult, NakshatraResult, PlanetResult, TropicalResult, VedicaResult
from app.motors.alquimia import AlquimiaResult
from app.motors.temperamentos import TemperamentosResult
from app.core.temporal import TemporalStatus


def _planet(name: str, sign: str, id_: int, status=TemporalStatus.EXACT) -> PlanetResult:
    return PlanetResult(planet=name, sign=sign, id_gatilho=id_, status=status)


def _planet_hybrid(name: str, sign_a: str, id_a: int, sign_b: str, id_b: int) -> PlanetResult:
    return PlanetResult(
        planet=name, sign=sign_a, id_gatilho=id_a,
        status=TemporalStatus.HYBRID, sign_b=sign_b, id_gatilho_b=id_b,
    )


def _tropical(sol_sign: str = "aries", hybrid: bool = False) -> TropicalResult:
    sol = (_planet_hybrid("sol", sol_sign, 9, "touro", 4) if hybrid
           else _planet("sol", sol_sign, 9))
    lua = _planet("lua", "cancer", 2)
    planets = [sol, lua,
               _planet("mercurio", "aries", 9),
               _planet("venus", "touro", 4),
               _planet("marte", "leao", 9),
               _planet("jupiter", "sagitario", 5),
               _planet("saturno", "capricornio", 4),
               _planet("urano", "aquario", 11),
               _planet("netuno", "peixes", 2),
               _planet("plutao", "escorpiao", 33)]
    return TropicalResult(
        sol=sol, lua=lua, ascendente=_planet("ascendente", "gemeos", 5),
        planets=planets,
        vote=sol.id_gatilho, vote_b=sol.id_gatilho_b,
        overall_status=TemporalStatus.HYBRID if hybrid else TemporalStatus.EXACT,
    )


def _temperamentos(elem: str = "Fogo", temp: str = "Colerico", id_: int = 9) -> TemperamentosResult:
    return TemperamentosResult(
        elemento_dominante=elem, temperamento_dominante=temp,
        elemento_secundario="Terra", temperamento_secundario="Melancolico",
        pontuacao={"Fogo": 9, "Terra": 5, "Ar": 0, "Agua": 0},
        id_gatilho=id_, vote=id_, overall_status=TemporalStatus.EXACT,
    )


def _nakshatra() -> NakshatraResult:
    return NakshatraResult(
        index=0, nome="Ashwini", id_gatilho=9, regente="ketu",
        pada=1, purushartha="Dharma", simbolo="Cabeça de Cavalo",
        deidade="Ashwini Kumaras", qualidade="Leve/Ágil",
        status=TemporalStatus.EXACT,
    )


def _vedica() -> VedicaResult:
    return VedicaResult(
        nakshatra=_nakshatra(),
        atmakaraka=AtmakarakaResult(graha="guru", id_gatilho=5, grau_no_signo=28.5),
        vote=9, vote_b=None, overall_status=TemporalStatus.EXACT,
    )


def _alquimia(signo: str = "Aries") -> AlquimiaResult:
    return AlquimiaResult(
        signo_solar=signo, elemento="Fogo", fase="Rubedo",
        operacao="Coagulação/Manifestação", vibe="Totalidade e Ação no Mundo",
        id_gatilho=9, vote=9, overall_status=TemporalStatus.EXACT,
    )


# ── Cap. 2 ────────────────────────────────────────────────────────────────────

class TestAssembleCap2:

    def test_campos_basicos(self):
        r = assemble_cap2(_tropical(), _temperamentos())
        assert r.sol.sign == "aries"
        assert r.lua.sign == "cancer"
        assert r.ascendente is not None
        assert r.ascendente.sign == "gemeos"

    def test_planetas_count(self):
        r = assemble_cap2(_tropical(), _temperamentos())
        assert len(r.planetas) == 10

    def test_temperamentos_propagados(self):
        r = assemble_cap2(_tropical(), _temperamentos())
        assert r.temperamentos.elemento_dominante == "Fogo"
        assert r.temperamentos.temperamento_dominante == "Colerico"

    def test_sem_ascendente(self):
        t = _tropical()
        t2 = TropicalResult(
            sol=t.sol, lua=t.lua, ascendente=None,
            planets=t.planets, vote=t.vote, vote_b=None,
            overall_status=TemporalStatus.EXACT,
        )
        r = assemble_cap2(t2, _temperamentos())
        assert r.ascendente is None

    def test_hybrid_sol(self):
        r = assemble_cap2(_tropical(hybrid=True), _temperamentos())
        assert r.sol.sign_b == "touro"
        assert r.sol.id_gatilho_b == 4

    def test_temperamentos_b_none_por_padrao(self):
        r = assemble_cap2(_tropical(), _temperamentos())
        assert r.temperamentos_b is None

    def test_temperamentos_b_preenchido(self):
        r = assemble_cap2(_tropical(), _temperamentos(), _temperamentos("Terra", "Melancolico", 4))
        assert r.temperamentos_b is not None
        assert r.temperamentos_b.elemento_dominante == "Terra"


# ── Cap. 3 ────────────────────────────────────────────────────────────────────

class TestAssembleCap3:

    def test_campos_basicos(self):
        r = assemble_cap3(_vedica())
        assert r.nakshatra.nome == "Ashwini"
        assert r.atmakaraka.graha == "guru"
        assert r.purushartha == "Dharma"

    def test_purushartha_do_nakshatra(self):
        # index=4 → 4 % 4 = 0 → Dharma
        nk = NakshatraResult(
            index=4, nome="Rohini", id_gatilho=2, regente="chandra",
            pada=2, purushartha="Dharma", simbolo="Carro",
            deidade="Brahma", qualidade="Fixa", status=TemporalStatus.EXACT,
        )
        v = VedicaResult(nakshatra=nk,
                         atmakaraka=AtmakarakaResult("shukra", 6, 25.0),
                         vote=2, vote_b=None, overall_status=TemporalStatus.EXACT)
        r = assemble_cap3(v)
        assert r.purushartha == "Dharma"
        assert r.atmakaraka.graha == "shukra"

    def test_hybrid_info_preservada(self):
        nk = NakshatraResult(
            index=0, nome="Ashwini", id_gatilho=9, regente="ketu",
            pada=1, purushartha="Dharma", simbolo="Cabeça de Cavalo",
            deidade="Ashwini Kumaras", qualidade="Leve/Ágil",
            status=TemporalStatus.HYBRID,
            nome_b="Bharani", id_gatilho_b=33, pada_b=4,
        )
        v = VedicaResult(nakshatra=nk,
                         atmakaraka=AtmakarakaResult("guru", 5, 28.5),
                         vote=9, vote_b=33, overall_status=TemporalStatus.HYBRID)
        r = assemble_cap3(v)
        assert r.nakshatra.nome_b == "Bharani"
        assert r.nakshatra.id_gatilho_b == 33


# ── Cap. 8 ────────────────────────────────────────────────────────────────────

class TestAssembleCap8:

    def test_campos_rubedo(self):
        r = assemble_cap8(_alquimia("Aries"))
        assert r.fase == "Rubedo"
        assert r.elemento == "Fogo"
        assert r.operacao == "Coagulação/Manifestação"
        assert r.vibe == "Totalidade e Ação no Mundo"
        assert r.id_gatilho == 9

    def test_campos_nigredo(self):
        a = AlquimiaResult(
            signo_solar="Escorpiao", elemento="Agua", fase="Nigredo",
            operacao="Putrefação/Calcinação", vibe="Morte do Ego e Sombra",
            id_gatilho=33, vote=33, overall_status=TemporalStatus.EXACT,
        )
        r = assemble_cap8(a)
        assert r.fase == "Nigredo"
        assert r.vibe == "Morte do Ego e Sombra"
        assert r.id_gatilho == 33

    def test_signo_preservado(self):
        r = assemble_cap8(_alquimia("Leao"))
        assert r.signo_solar == "Leao"
