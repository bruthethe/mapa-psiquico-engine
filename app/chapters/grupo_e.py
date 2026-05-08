"""
Grupo E — HD e Panteões: Cap. 10 (Human Design), Cap. 11 (15 panteões).

Cap. 10 recebe HDResult + MedicinaResult — o chakra/Hz vem da Medicina
aplicada ao id_dominante consolidado.

Cap. 11 recebe ConsolidationResult e faz lookup_panteoes pelo id_dominante;
em status HYBRID, preenche panteoes_b com o segundo ID.

14 panteões: Arcanjo, Dogon, Egípcio, Grego, Inca, Inuit, Iorubá, Maia,
Maori, Nórdico, Norte-Americano, Tao, Tupi-Guarani, Xinto.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.consolidation import ConsolidationResult
from app.core.motor_types import HDActivation, HDResult
from app.core.nivel2 import PanteoesData, lookup_panteoes
from app.motors.medicina import MedicinaResult


@dataclass(frozen=True)
class Cap10Data:
    tipo: str
    estrategia: str
    tipo_id_gatilho: int
    autoridade: str
    autoridade_id_gatilho: int
    centros_definidos: frozenset[str]
    canais_ativos: tuple[tuple[int, int], ...]
    porta_sol_personalidade: int
    personalidade: tuple[HDActivation, ...]
    design: tuple[HDActivation, ...]
    chakra: str
    sistema: str
    frequencia: str
    tipo_b: str | None
    estrategia_b: str | None
    tipo_b_id_gatilho: int | None
    porta_sol_personalidade_b: int | None


@dataclass(frozen=True)
class Cap11Data:
    panteoes: PanteoesData
    panteoes_b: PanteoesData | None   # preenchido apenas em HYBRID


def assemble_cap10(hd: HDResult, medicina: MedicinaResult) -> Cap10Data:
    return Cap10Data(
        tipo=hd.tipo,
        estrategia=hd.estrategia,
        tipo_id_gatilho=hd.tipo_id_gatilho,
        autoridade=hd.autoridade,
        autoridade_id_gatilho=hd.autoridade_id_gatilho,
        centros_definidos=hd.centros_definidos,
        canais_ativos=tuple(hd.canais_ativos),
        porta_sol_personalidade=hd.porta_sol_personalidade,
        personalidade=tuple(hd.personalidade),
        design=tuple(hd.design),
        chakra=medicina.chakra,
        sistema=medicina.sistema,
        frequencia=medicina.frequencia,
        tipo_b=hd.tipo_b,
        estrategia_b=hd.estrategia_b,
        tipo_b_id_gatilho=hd.tipo_b_id_gatilho,
        porta_sol_personalidade_b=hd.porta_sol_personalidade_b,
    )


def assemble_cap11(consolidation: ConsolidationResult) -> Cap11Data:
    panteoes = lookup_panteoes(consolidation.id_dominante)
    panteoes_b = None
    if consolidation.id_dominante_b is not None:
        panteoes_b = lookup_panteoes(consolidation.id_dominante_b)
    return Cap11Data(panteoes=panteoes, panteoes_b=panteoes_b)
