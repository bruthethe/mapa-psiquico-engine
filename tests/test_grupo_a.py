"""Testes do Grupo A — Prefácio, Cap. 1, Cap. 12 (5.4)."""

import pytest

from app.chapters.grupo_a import (
    Cap1Data, Cap12Data, PrefacioData,
    assemble_cap1, assemble_cap12, assemble_prefacio,
)
from app.core.consolidation import ConsolidationResult
from app.core.ids import MasterLabel, get_master_label
from app.core.nivel2 import ArquetipoData, GoetiaData
from app.core.nivel3 import MaterializacaoData
from app.core.temporal import TemporalStatus


def _exact(id_: int) -> ConsolidationResult:
    return ConsolidationResult(
        id_dominante=id_,
        id_dominante_b=None,
        status=TemporalStatus.EXACT,
        master_label=get_master_label(id_),
        master_label_b=None,
    )


def _hybrid(id_a: int, id_b: int) -> ConsolidationResult:
    return ConsolidationResult(
        id_dominante=id_a,
        id_dominante_b=id_b,
        status=TemporalStatus.HYBRID,
        master_label=get_master_label(id_a),
        master_label_b=get_master_label(id_b),
    )


# ── Prefácio ──────────────────────────────────────────────────────────────────

class TestAssemblePrefacio:

    def test_exact_sem_b(self):
        r = assemble_prefacio(_exact(1))
        assert r.id_dominante == 1
        assert r.id_dominante_b is None
        assert r.status == TemporalStatus.EXACT
        assert r.master_label is None

    def test_hybrid_com_b(self):
        r = assemble_prefacio(_hybrid(1, 9))
        assert r.id_dominante == 1
        assert r.id_dominante_b == 9
        assert r.status == TemporalStatus.HYBRID

    def test_master_label_propagado(self):
        r = assemble_prefacio(_exact(11))
        assert isinstance(r.master_label, MasterLabel)

    def test_master_label_b_propagado(self):
        r = assemble_prefacio(_hybrid(1, 33))
        assert r.master_label is None
        assert isinstance(r.master_label_b, MasterLabel)


# ── Cap. 1 ────────────────────────────────────────────────────────────────────

class TestAssembleCap1:

    def test_exact_campos_preenchidos(self):
        r = assemble_cap1(_exact(1))
        assert isinstance(r.arquetipos, ArquetipoData)
        assert isinstance(r.goetia, GoetiaData)
        assert r.arquetipos_b is None
        assert r.goetia_b is None

    def test_exact_valores_id_1(self):
        r = assemble_cap1(_exact(1))
        assert r.arquetipos.essencia_solar == "O Rei"
        assert r.arquetipos.mascara == "O Herói"
        assert r.goetia.demonio == "O Tirano (Paimon)"

    def test_hybrid_b_preenchido(self):
        r = assemble_cap1(_hybrid(1, 9))
        assert isinstance(r.arquetipos_b, ArquetipoData)
        assert isinstance(r.goetia_b, GoetiaData)
        assert r.arquetipos_b.essencia_solar == "O Guerreiro"

    def test_id_8_herda_4(self):
        r8 = assemble_cap1(_exact(8))
        r4 = assemble_cap1(_exact(4))
        assert r8.arquetipos.essencia_solar == r4.arquetipos.essencia_solar
        assert r8.goetia.demonio == r4.goetia.demonio

    def test_master_label_no_arquetipos(self):
        r = assemble_cap1(_exact(11))
        assert isinstance(r.arquetipos.master_label, MasterLabel)

    def test_sem_master_label_id_3(self):
        r = assemble_cap1(_exact(3))
        assert r.arquetipos.master_label is None
        assert r.goetia.master_label is None


# ── Cap. 12 ───────────────────────────────────────────────────────────────────

class TestAssembleCap12:

    def test_exact_campos_preenchidos(self):
        r = assemble_cap12(_exact(4))
        assert isinstance(r.materializacao, MaterializacaoData)
        assert r.materializacao_b is None

    def test_exact_valores_id_4(self):
        r = assemble_cap12(_exact(4))
        m = r.materializacao
        assert m.cores == "Preto"
        assert m.metais == "Chumbo"
        assert m.animais.terra == "Urso"

    def test_hybrid_b_preenchido(self):
        r = assemble_cap12(_hybrid(4, 9))
        assert isinstance(r.materializacao_b, MaterializacaoData)
        assert r.materializacao_b.cores == "Vermelho"

    def test_id_22_herda_4(self):
        r22 = assemble_cap12(_exact(22))
        r4 = assemble_cap12(_exact(4))
        assert r22.materializacao.cores == r4.materializacao.cores

    def test_master_label_em_materializacao(self):
        r = assemble_cap12(_exact(33))
        assert isinstance(r.materializacao.master_label, MasterLabel)
