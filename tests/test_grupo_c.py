"""Testes do Grupo C — Cap. 4, Cap. 5, Cap. 9 (5.6)."""

import pytest

from app.chapters.grupo_c import (
    Cap4Data, Cap5Data, Cap9Data,
    assemble_cap4, assemble_cap5, assemble_cap9,
)
from app.core.motor_types import (
    BaZiPillar, BaZiPilarHora, BaZiResult,
    DaimonHoraMotorResult, DaimonHoraResult,
)
from app.core.temporal import TemporalStatus
from app.motors.tzolkin import TzolkinOraculo, TzolkinResult, TzolkinSelo, TzolkinTom


def _pillar(animal: str, elemento: str, id_: int) -> BaZiPillar:
    return BaZiPillar(animal=animal, elemento=elemento, id_gatilho=id_)


def _hora_exact(animal: str, elemento: str, id_: int) -> BaZiPilarHora:
    return BaZiPilarHora(animal=animal, elemento=elemento, id_gatilho=id_,
                         status=TemporalStatus.EXACT)


def _hora_hybrid(animal_a: str, el_a: str, id_a: int,
                 animal_b: str, el_b: str, id_b: int) -> BaZiPilarHora:
    return BaZiPilarHora(
        animal=animal_a, elemento=el_a, id_gatilho=id_a,
        status=TemporalStatus.HYBRID,
        animal_b=animal_b, elemento_b=el_b, id_gatilho_b=id_b,
    )


def _bazi(hybrid: bool = False) -> BaZiResult:
    hora = (_hora_hybrid("rato", "agua", 2, "boi", "terra", 4)
            if hybrid else _hora_exact("rato", "agua", 2))
    return BaZiResult(
        ano=_pillar("dragao", "madeira", 3),
        mes=_pillar("tigre", "fogo", 9),
        dia=_pillar("cavalo", "fogo", 9),
        hora=hora,
        vote=2 if not hybrid else 2,
        overall_status=TemporalStatus.HYBRID if hybrid else TemporalStatus.EXACT,
    )


def _selo(pos: int = 1, nome: str = "Imix") -> TzolkinSelo:
    return TzolkinSelo(posicao=pos, nome=nome, cor="Vermelho",
                       essencia="Criação", id_gatilho=1)


def _tzolkin() -> TzolkinResult:
    oraculo = TzolkinOraculo(
        guia=_selo(1, "Imix"),
        analogo=_selo(6, "Mundo das Pontes"),
        antipoda=_selo(11, "Chuen"),
        oculto=_selo(20, "Ahau"),
    )
    return TzolkinResult(
        kin=1,
        selo=_selo(1, "Imix"),
        tom=TzolkinTom(tom=1, nome="Magnético", poder="Unificar",
                       acao="Atrair", essencia="Propósito", id_gatilho=1),
        oraculo=oraculo,
        vote=1,
        overall_status=TemporalStatus.EXACT,
    )


def _daimon(planeta: str = "Sol", id_: int = 1, periodo: str = "diurno",
            status: TemporalStatus = TemporalStatus.EXACT) -> DaimonHoraMotorResult:
    d = DaimonHoraResult(planeta=planeta, id_gatilho=id_,
                         numero_hora=6, periodo=periodo, status=status)
    return DaimonHoraMotorResult(daimon=d, vote=id_, vote_b=None,
                                 overall_status=status)


def _daimon_hybrid() -> DaimonHoraMotorResult:
    d = DaimonHoraResult(
        planeta="Sol", id_gatilho=1, numero_hora=6, periodo="diurno",
        status=TemporalStatus.HYBRID,
        planeta_b="Lua", id_gatilho_b=2, numero_hora_b=13, periodo_b="noturno",
    )
    return DaimonHoraMotorResult(daimon=d, vote=1, vote_b=2,
                                 overall_status=TemporalStatus.HYBRID)


# ── Cap. 4 ────────────────────────────────────────────────────────────────────

class TestAssembleCap4:

    def test_quatro_pilares_presentes(self):
        r = assemble_cap4(_bazi())
        assert r.ano.animal == "dragao"
        assert r.mes.animal == "tigre"
        assert r.dia.animal == "cavalo"
        assert r.hora.animal == "rato"

    def test_elementos_propagados(self):
        r = assemble_cap4(_bazi())
        assert r.ano.elemento == "madeira"
        assert r.hora.elemento == "agua"

    def test_ids_propagados(self):
        r = assemble_cap4(_bazi())
        assert r.ano.id_gatilho == 3
        assert r.hora.id_gatilho == 2

    def test_hora_hybrid_preserva_b(self):
        r = assemble_cap4(_bazi(hybrid=True))
        assert r.hora.animal_b == "boi"
        assert r.hora.elemento_b == "terra"
        assert r.hora.id_gatilho_b == 4


# ── Cap. 5 ────────────────────────────────────────────────────────────────────

class TestAssembleCap5:

    def test_kin_e_selo(self):
        r = assemble_cap5(_tzolkin())
        assert r.kin == 1
        assert r.selo.nome == "Imix"

    def test_tom_propagado(self):
        r = assemble_cap5(_tzolkin())
        assert r.tom.nome == "Magnético"
        assert r.tom.poder == "Unificar"

    def test_oraculo_quatro_campos(self):
        r = assemble_cap5(_tzolkin())
        assert r.oraculo.guia.nome == "Imix"
        assert r.oraculo.antipoda.nome == "Chuen"
        assert r.oraculo.oculto.nome == "Ahau"


# ── Cap. 9 ────────────────────────────────────────────────────────────────────

class TestAssembleCap9:

    def test_diurno_genio(self):
        r = assemble_cap9(_daimon("Sol", 1, "diurno"))
        assert r.tipo == "Gênio"
        assert r.planeta == "Sol"
        assert r.periodo == "diurno"

    def test_noturno_guardiao(self):
        r = assemble_cap9(_daimon("Lua", 2, "noturno"))
        assert r.tipo == "Guardião"

    def test_hybrid_tipo_hibrid(self):
        r = assemble_cap9(_daimon_hybrid())
        assert r.tipo == "Híbrido"
        assert r.tipo_b == "Híbrido"

    def test_exact_sem_b(self):
        r = assemble_cap9(_daimon())
        assert r.planeta_b is None
        assert r.id_gatilho_b is None
        assert r.tipo_b is None

    def test_hybrid_com_b(self):
        r = assemble_cap9(_daimon_hybrid())
        assert r.planeta_b == "Lua"
        assert r.id_gatilho_b == 2
        assert r.numero_hora == 6
