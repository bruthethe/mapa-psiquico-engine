"""Nível 3 — Lookup da materialização sensorial completa por ID."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.ids import MasterLabel, get_master_label
from app.core.report_loader import lookup


@dataclass(frozen=True)
class AnimaisData:
    terra: str
    agua: str
    ar: str


@dataclass(frozen=True)
class MaterializacaoData:
    cores: str
    metais: str
    cristais: str
    ervas: str
    notas: str
    geometria: str
    animais: AnimaisData
    criaturas: str
    master_label: MasterLabel | None


def lookup_materializacao(id_: int) -> MaterializacaoData:
    """Retorna o objeto de materialização sensorial completo para o ID."""
    raw_animais = lookup("animais", id_)
    return MaterializacaoData(
        cores=lookup("cores", id_),
        metais=lookup("metais", id_),
        cristais=lookup("cristais", id_),
        ervas=lookup("ervas", id_),
        notas=lookup("notas", id_),
        geometria=lookup("geometria", id_),
        animais=AnimaisData(
            terra=raw_animais["terra"],
            agua=raw_animais["agua"],
            ar=raw_animais["ar"],
        ),
        criaturas=lookup("criaturas", id_),
        master_label=get_master_label(id_),
    )
