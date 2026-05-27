"""
Grupo D — Nome e Oráculos: Cap. 6 (Numerologias), Cap. 7 (Tarô + I Ching).

Todos os motores deste grupo produzem status EXACT (dados nominais e de data
são determinísticos, sem ambiguidade temporal). Não há campos `_b`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.nivel2 import lookup_arquetipos
from app.motors.cabalistica import CabalisticaResult
from app.motors.caldeia import CaldeiaResult
from app.motors.gematria import GematriaResult
from app.motors.iching import IChingResult
from app.motors.pitagorica import PitagoricaResult
from app.motors.taro import TaroResult


@dataclass(frozen=True)
class Cap6Nomes:
    """Nome do arquétipo (essência solar) para cada sub-ID do Cap. 6."""
    alma: str
    persona: str
    expressao: str
    caminho: str
    missao: str
    motivacao: str
    impressao: str
    destino: str
    psiquico: str
    grego: str
    hebraico: str


@dataclass(frozen=True)
class Cap6Data:
    pitagorica: PitagoricaResult
    cabalistica: CabalisticaResult
    caldeia: CaldeiaResult
    gematria: GematriaResult
    nomes: Cap6Nomes


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
    def _nome(id_: int) -> str:
        return lookup_arquetipos(id_).essencia_solar

    nomes = Cap6Nomes(
        alma=_nome(pitagorica.id_alma),
        persona=_nome(pitagorica.id_persona),
        expressao=_nome(pitagorica.id_expressao),
        caminho=_nome(pitagorica.caminho_vida),
        missao=_nome(cabalistica.missao_vida),
        motivacao=_nome(cabalistica.id_motivacao),
        impressao=_nome(cabalistica.id_impressao),
        destino=_nome(caldeia.numero_destino),
        psiquico=_nome(caldeia.vibracao_psiquica),
        grego=_nome(gematria.id_grego),
        hebraico=_nome(gematria.id_hebraico),
    )

    return Cap6Data(
        pitagorica=pitagorica,
        cabalistica=cabalistica,
        caldeia=caldeia,
        gematria=gematria,
        nomes=nomes,
    )


def assemble_cap7(taro: TaroResult, iching: IChingResult) -> Cap7Data:
    return Cap7Data(taro=taro, iching=iching)
