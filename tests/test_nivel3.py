"""Testes do Nível 3 — materialização sensorial (5.3)."""

import pytest

from app.core.ids import MasterLabel
from app.core.nivel3 import AnimaisData, MaterializacaoData, lookup_materializacao

_DATA_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 9, 11, 33})


class TestLookupMaterializacao:

    def test_id_4_valores(self):
        r = lookup_materializacao(4)
        assert r.cores == "Preto"
        assert r.metais == "Chumbo"
        assert r.cristais == "Ônix"
        assert r.ervas == "Arruda e Mirra"
        assert r.notas == "Lá"
        assert r.geometria == "Quadrado"
        assert r.criaturas == "Golem"

    def test_id_4_animais(self):
        r = lookup_materializacao(4)
        assert r.animais.terra == "Urso"
        assert r.animais.agua == "Tartaruga"
        assert r.animais.ar == "Condor"

    def test_id_1_valores(self):
        r = lookup_materializacao(1)
        assert r.cores == "Amarelo"
        assert r.metais == "Ouro"
        assert r.animais.terra == "Leão"

    def test_todos_ids_retornam_dados_completos(self):
        for id_ in _DATA_IDS:
            r = lookup_materializacao(id_)
            assert r.cores
            assert r.metais
            assert r.cristais
            assert r.ervas
            assert r.notas
            assert r.geometria
            assert r.criaturas
            assert isinstance(r.animais, AnimaisData)
            assert r.animais.terra
            assert r.animais.agua
            assert r.animais.ar

    def test_id_8_herda_id_4(self):
        r8 = lookup_materializacao(8)
        r4 = lookup_materializacao(4)
        assert r8.cores == r4.cores
        assert r8.metais == r4.metais
        assert r8.animais == r4.animais

    def test_id_22_herda_id_4(self):
        r22 = lookup_materializacao(22)
        r4 = lookup_materializacao(4)
        assert r22.cores == r4.cores
        assert r22.criaturas == r4.criaturas

    def test_master_label_11(self):
        r = lookup_materializacao(11)
        assert isinstance(r.master_label, MasterLabel)

    def test_master_label_22(self):
        r = lookup_materializacao(22)
        assert isinstance(r.master_label, MasterLabel)

    def test_master_label_33(self):
        r = lookup_materializacao(33)
        assert isinstance(r.master_label, MasterLabel)

    def test_sem_master_label_id_7(self):
        r = lookup_materializacao(7)
        assert r.master_label is None

    def test_sem_master_label_id_8(self):
        r = lookup_materializacao(8)
        assert r.master_label is None

    def test_id_9_animais(self):
        r = lookup_materializacao(9)
        assert r.animais.terra == "Tigre"
        assert r.animais.agua == "Tubarão"
        assert r.animais.ar == "Gavião"

    def test_retorna_frozen_dataclass(self):
        r = lookup_materializacao(1)
        assert isinstance(r, MaterializacaoData)
        with pytest.raises((AttributeError, TypeError)):
            r.cores = "outra cor"  # type: ignore
