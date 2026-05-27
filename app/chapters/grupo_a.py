"""
Grupo A — MVP Core: Prefácio, Cap. 1 (Arquétipo Central), Cap. 11 (Materialização).

Todos os capítulos aceitam ConsolidationResult e produzem um dataclass pronto
para serialização. No status HYBRID (A ≠ B), os campos `_b` são preenchidos
com os dados do segundo ID; nos demais status ficam None.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.consolidation import ConsolidationResult
from app.core.ids import MasterLabel
from app.core.nivel2 import ArquetipoData, GoetiaData, lookup_arquetipos, lookup_goetia
from app.core.nivel3 import MaterializacaoData, lookup_materializacao
from app.core.temporal import TemporalStatus


@dataclass(frozen=True)
class PrefacioData:
    id_dominante: int
    id_dominante_b: int | None       # preenchido apenas em HYBRID
    status: TemporalStatus
    master_label: MasterLabel | None
    master_label_b: MasterLabel | None


@dataclass(frozen=True)
class Cap1Data:
    arquetipos: ArquetipoData
    goetia: GoetiaData
    arquetipos_b: ArquetipoData | None   # preenchido apenas em HYBRID
    goetia_b: GoetiaData | None          # preenchido apenas em HYBRID


@dataclass(frozen=True)
class Cap11Data:
    materializacao: MaterializacaoData
    materializacao_b: MaterializacaoData | None   # preenchido apenas em HYBRID


def assemble_prefacio(consolidation: ConsolidationResult) -> PrefacioData:
    return PrefacioData(
        id_dominante=consolidation.id_dominante,
        id_dominante_b=consolidation.id_dominante_b,
        status=consolidation.status,
        master_label=consolidation.master_label,
        master_label_b=consolidation.master_label_b,
    )


def assemble_cap1(consolidation: ConsolidationResult) -> Cap1Data:
    arquetipos_b = None
    goetia_b = None
    if consolidation.id_dominante_b is not None:
        arquetipos_b = lookup_arquetipos(consolidation.id_dominante_b)
        goetia_b = lookup_goetia(consolidation.id_dominante_b)
    return Cap1Data(
        arquetipos=lookup_arquetipos(consolidation.id_dominante),
        goetia=lookup_goetia(consolidation.id_dominante),
        arquetipos_b=arquetipos_b,
        goetia_b=goetia_b,
    )


def assemble_cap11(consolidation: ConsolidationResult) -> Cap11Data:
    materializacao_b = None
    if consolidation.id_dominante_b is not None:
        materializacao_b = lookup_materializacao(consolidation.id_dominante_b)
    return Cap11Data(
        materializacao=lookup_materializacao(consolidation.id_dominante),
        materializacao_b=materializacao_b,
    )
