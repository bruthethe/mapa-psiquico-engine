"""
Grupo D — Nome e Oráculos: Cap. 6 (Numerologias), Cap. 7 (Tarô + I Ching).

Todos os motores deste grupo produzem status EXACT (dados nominais e de data
são determinísticos, sem ambiguidade temporal). Não há campos `_b`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.motors.cabalistica import CabalisticaResult
from app.motors.caldeia import CaldeiaResult
from app.motors.gematria import GematriaResult
from app.motors.iching import IChingResult
from app.motors.pitagorica import PitagoricaResult
from app.motors.taro import TaroResult


@dataclass(frozen=True)
class Cap6Data:
    pitagorica: PitagoricaResult
    cabalistica: CabalisticaResult
    caldeia: CaldeiaResult
    gematria: GematriaResult


@dataclass(frozen=True)
class Cap7Data:
    taro: TaroResult
    iching: IChingResult


def assemble_cap6(
    pitagorica: PitagoricaResult,
    cabalistica: CabalisticaResult,
    caldeia: CaldeiaResult,
    gematria: GematriaResult,
) -> Cap6Data:
    return Cap6Data(
        pitagorica=pitagorica,
        cabalistica=cabalistica,
        caldeia=caldeia,
        gematria=gematria,
    )


def assemble_cap7(taro: TaroResult, iching: IChingResult) -> Cap7Data:
    return Cap7Data(taro=taro, iching=iching)
