"""Testes do Grupo E — Cap. 10 (Panteões)."""

import pytest

from app.chapters.grupo_e import Cap10Data, assemble_cap10
from app.core.consolidation import ConsolidationResult
from app.core.ids import MasterLabel
from app.core.nivel2 import PanteoesData
from app.core.temporal import TemporalStatus


def _panteoes(master: MasterLabel | None = None) -> PanteoesData:
    return PanteoesData(
        divindades={"grego": "Zeus", "nordico": "Odin", "egipcio": "Ra"},
        master_label=master,
    )


def _consolidation(
    id_a: int = 3,
    id_b: int | None = None,
    status: TemporalStatus = TemporalStatus.EXACT,
) -> ConsolidationResult:
    return ConsolidationResult(
        id_dominante=id_a,
        id_dominante_b=id_b,
        status=status,
        master_label=None,
        master_label_b=None,
    )


class TestAssembleCap10:

    def test_retorna_cap10data(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()):
            r = assemble_cap10(_consolidation(id_a=3))
        assert isinstance(r, Cap10Data)

    def test_panteoes_b_none_em_exact(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()):
            r = assemble_cap10(_consolidation(id_a=3))
        assert r.panteoes_b is None

    def test_panteoes_b_preenchido_em_hybrid(self):
        import unittest.mock as mock
        panteoes_a = _panteoes()
        panteoes_b = PanteoesData(divindades={"grego": "Ares"}, master_label=None)
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", side_effect=[panteoes_a, panteoes_b]):
            r = assemble_cap10(_consolidation(id_a=3, id_b=1, status=TemporalStatus.HYBRID))
        assert r.panteoes.divindades["grego"] == "Zeus"
        assert r.panteoes_b is not None
        assert r.panteoes_b.divindades["grego"] == "Ares"

    def test_panteoes_divindades_dict(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()):
            r = assemble_cap10(_consolidation(id_a=3))
        assert isinstance(r.panteoes.divindades, dict)
        assert "grego" in r.panteoes.divindades

    def test_master_label_propagado(self):
        import unittest.mock as mock
        label = MasterLabel(id_dados=11, titulo="O Portal", texto="Frequência de Ruptura")
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes(master=label)):
            r = assemble_cap10(_consolidation(id_a=11))
        assert r.panteoes.master_label is not None
        assert r.panteoes.master_label.id_dados == 11

    def test_lookup_chamado_com_id_correto(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()) as mock_lookup:
            assemble_cap10(_consolidation(id_a=7))
        mock_lookup.assert_called_once_with(7)

    def test_lookup_chamado_duas_vezes_em_hybrid(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()) as mock_lookup:
            assemble_cap10(_consolidation(id_a=3, id_b=9, status=TemporalStatus.HYBRID))
        assert mock_lookup.call_count == 2
        mock_lookup.assert_any_call(3)
        mock_lookup.assert_any_call(9)
