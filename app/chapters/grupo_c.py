"""
Grupo C — Sistemas Orientais: Cap. 4 (Ba Zi), Cap. 5 (Tzolkin), Cap. 9 (Daimon da Hora).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.motor_types import BaZiPillar, BaZiPilarHora, BaZiResult, DaimonHoraMotorResult
from app.core.temporal import TemporalStatus
from app.motors.tzolkin import TzolkinOraculo, TzolkinResult, TzolkinSelo, TzolkinTom

_TIPO_MAP = {
    ("diurno",  False): "Gênio",
    ("noturno", False): "Guardião",
}


@dataclass(frozen=True)
class Cap4Data:
    ano: BaZiPillar
    mes: BaZiPillar
    dia: BaZiPillar
    hora: BaZiPilarHora


@dataclass(frozen=True)
class Cap5Data:
    kin: int
    selo: TzolkinSelo
    tom: TzolkinTom
    oraculo: TzolkinOraculo


@dataclass(frozen=True)
class Cap9Data:
    planeta: str
    id_gatilho: int
    numero_hora: int
    periodo: str
    tipo: str                  # "Gênio" | "Guardião" | "Híbrido"
    planeta_b: str | None
    id_gatilho_b: int | None
    tipo_b: str | None         # preenchido em HYBRID


def assemble_cap4(bazi: BaZiResult) -> Cap4Data:
    return Cap4Data(ano=bazi.ano, mes=bazi.mes, dia=bazi.dia, hora=bazi.hora)


def assemble_cap5(tzolkin: TzolkinResult) -> Cap5Data:
    return Cap5Data(
        kin=tzolkin.kin,
        selo=tzolkin.selo,
        tom=tzolkin.tom,
        oraculo=tzolkin.oraculo,
    )


def _tipo(periodo: str, status: TemporalStatus) -> str:
    if status == TemporalStatus.HYBRID:
        return "Híbrido"
    return "Gênio" if periodo == "diurno" else "Guardião"


def assemble_cap9(motor: DaimonHoraMotorResult) -> Cap9Data:
    d = motor.daimon
    tipo_b = None
    if d.planeta_b is not None and d.periodo_b is not None:
        tipo_b = _tipo(d.periodo_b, d.status)
    return Cap9Data(
        planeta=d.planeta,
        id_gatilho=d.id_gatilho,
        numero_hora=d.numero_hora,
        periodo=d.periodo,
        tipo=_tipo(d.periodo, d.status),
        planeta_b=d.planeta_b,
        id_gatilho_b=d.id_gatilho_b,
        tipo_b=tipo_b,
    )
