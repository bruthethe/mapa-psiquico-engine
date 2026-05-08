"""
Testes do Nível 2 — arquétipos, panteões e sombra Goética (5.2).

Cobre herança 8→4, 22→4 e master labels para 11, 22, 33.
"""

import pytest

from app.core.ids import MasterLabel
from app.core.nivel2 import (
    ArquetipoData, GoetiaData, PanteoesData,
    lookup_arquetipos, lookup_goetia, lookup_panteoes,
)

_DATA_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 9, 11, 33})
_ALL_PANTEOES = {
    "arcanjo", "dogon", "egipcio", "grego", "inca", "inuit",
    "ioruba", "maia", "maori", "nordico", "norte-americano",
    "tao", "tupi-guarani", "xinto",
}


class TestLookupArquetipos:

    def test_id_1_valores(self):
        r = lookup_arquetipos(1)
        assert r.essencia_solar == "O Rei"
        assert r.mascara == "O Herói"
        assert r.refugio_lunar == "O Soberano"
        assert r.necessidade == "Precisa de Validação"

    def test_todos_ids_retornam_dados(self):
        for id_ in _DATA_IDS:
            r = lookup_arquetipos(id_)
            assert r.essencia_solar
            assert r.mascara
            assert r.refugio_lunar
            assert r.necessidade

    def test_id_8_herda_id_4(self):
        assert lookup_arquetipos(8) == lookup_arquetipos(4)

    def test_id_22_herda_dados_id_4(self):
        r22 = lookup_arquetipos(22)
        r4 = lookup_arquetipos(4)
        assert r22.essencia_solar == r4.essencia_solar
        assert r22.mascara == r4.mascara

    def test_master_label_11(self):
        r = lookup_arquetipos(11)
        assert isinstance(r.master_label, MasterLabel)

    def test_master_label_22_com_label(self):
        r = lookup_arquetipos(22)
        assert isinstance(r.master_label, MasterLabel)

    def test_master_label_33(self):
        r = lookup_arquetipos(33)
        assert isinstance(r.master_label, MasterLabel)

    def test_sem_master_label_id_1(self):
        r = lookup_arquetipos(1)
        assert r.master_label is None

    def test_sem_master_label_id_8(self):
        r = lookup_arquetipos(8)
        assert r.master_label is None


class TestLookupPanteoes:

    def test_todos_14_panteoes_presentes(self):
        r = lookup_panteoes(1)
        assert r.divindades.keys() == _ALL_PANTEOES

    def test_grego_id_1(self):
        r = lookup_panteoes(1)
        assert r.divindades["grego"] == "Apolo"

    def test_nordico_id_9(self):
        r = lookup_panteoes(9)
        assert r.divindades["nordico"] == "Thor"

    def test_arcanjo_id_4(self):
        r = lookup_panteoes(4)
        assert r.divindades["arcanjo"] == "Zaphkiel"

    def test_todos_ids_retornam_dados(self):
        for id_ in _DATA_IDS:
            r = lookup_panteoes(id_)
            assert len(r.divindades) == 14
            for panteao, div in r.divindades.items():
                assert div, f"Divindade vazia para id={id_} panteao={panteao}"

    def test_id_8_herda_id_4(self):
        assert lookup_panteoes(8).divindades == lookup_panteoes(4).divindades

    def test_id_22_herda_id_4(self):
        assert lookup_panteoes(22).divindades == lookup_panteoes(4).divindades

    def test_master_label_33(self):
        r = lookup_panteoes(33)
        assert isinstance(r.master_label, MasterLabel)

    def test_sem_master_label_id_3(self):
        r = lookup_panteoes(3)
        assert r.master_label is None


class TestLookupGoetia:

    def test_id_1_tirano(self):
        r = lookup_goetia(1)
        assert r.demonio == "O Tirano (Paimon)"

    def test_id_9_destruidor(self):
        r = lookup_goetia(9)
        assert r.demonio == "O Destruidor (Eligos)"

    def test_todos_ids_retornam_dados(self):
        for id_ in _DATA_IDS:
            r = lookup_goetia(id_)
            assert r.demonio

    def test_id_8_herda_id_4(self):
        assert lookup_goetia(8).demonio == lookup_goetia(4).demonio

    def test_id_22_herda_id_4(self):
        assert lookup_goetia(22).demonio == lookup_goetia(4).demonio

    def test_master_label_11(self):
        r = lookup_goetia(11)
        assert isinstance(r.master_label, MasterLabel)

    def test_sem_master_label_id_5(self):
        r = lookup_goetia(5)
        assert r.master_label is None
