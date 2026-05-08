"""
Grupo B — Astrologia: Cap. 2 (Tropical + Temperamentos), Cap. 3 (Védica), Cap. 8 (Alquimia).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.motor_types import AtmakarakaResult, NakshatraResult, PlanetResult, TropicalResult, VedicaResult
from app.motors.alquimia import AlquimiaResult
from app.motors.temperamentos import TemperamentosResult


@dataclass(frozen=True)
class Cap2Data:
    sol: PlanetResult
    lua: PlanetResult
    ascendente: PlanetResult | None
    planetas: tuple[PlanetResult, ...]
    temperamentos: TemperamentosResult
    temperamentos_b: TemperamentosResult | None   # preenchido em HYBRID


@dataclass(frozen=True)
class Cap3Data:
    nakshatra: NakshatraResult
    atmakaraka: AtmakarakaResult
    purushartha: str


@dataclass(frozen=True)
class Cap8Data:
    signo_solar: str
    elemento: str
    fase: str
    operacao: str
    vibe: str
    id_gatilho: int


def assemble_cap2(
    tropical: TropicalResult,
    temperamentos: TemperamentosResult,
    temperamentos_b: TemperamentosResult | None = None,
) -> Cap2Data:
    return Cap2Data(
        sol=tropical.sol,
        lua=tropical.lua,
        ascendente=tropical.ascendente,
        planetas=tuple(tropical.planets),
        temperamentos=temperamentos,
        temperamentos_b=temperamentos_b,
    )


def assemble_cap3(vedica: VedicaResult) -> Cap3Data:
    return Cap3Data(
        nakshatra=vedica.nakshatra,
        atmakaraka=vedica.atmakaraka,
        purushartha=vedica.nakshatra.purushartha,
    )


def assemble_cap8(alquimia: AlquimiaResult) -> Cap8Data:
    return Cap8Data(
        signo_solar=alquimia.signo_solar,
        elemento=alquimia.elemento,
        fase=alquimia.fase,
        operacao=alquimia.operacao,
        vibe=alquimia.vibe,
        id_gatilho=alquimia.id_gatilho,
    )
