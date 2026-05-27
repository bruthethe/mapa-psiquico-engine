"""
Grupo E — Panteões: Cap. 10 (14 panteões + sombra Goétia).

Recebe ConsolidationResult e faz lookup_panteoes pelo id_dominante;
em status HYBRID, preenche panteoes_b com o segundo ID.

14 panteões: Arcanjo, Dogon, Egípcio, Grego, Inca, Inuit, Iorubá, Maia,
Maori, Nórdico, Norte-Americano, Tao, Tupi-Guarani, Xinto.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.consolidation import ConsolidationResult
from app.core.nivel2 import PanteoesData, lookup_panteoes


@dataclass(frozen=True)
class Cap10Data:
    panteoes: PanteoesData
    panteoes_b: PanteoesData | None   # preenchido apenas em HYBRID


def assemble_cap10(consolidation: ConsolidationResult) -> Cap10Data:
    panteoes = lookup_panteoes(consolidation.id_dominante)
    panteoes_b = None
    if consolidation.id_dominante_b is not None:
        panteoes_b = lookup_panteoes(consolidation.id_dominante_b)
    return Cap10Data(panteoes=panteoes, panteoes_b=panteoes_b)
