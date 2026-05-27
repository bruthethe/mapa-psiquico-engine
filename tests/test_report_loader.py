"""
Testes do report data loader (5.1).

Verifica que todos os 25 arquivos ID-indexados são carregados ao startup,
que todos os 10 DATA_IDs retornam dados de cada fonte, e que herança (8→4,
22→4) e master labels (11, 22, 33) funcionam automaticamente.
"""

import pytest

from app.core.ids import MasterLabel
from app.core.report_loader import DATA_IDS, lookup, lookup_with_label, sources

_TRANSLATION_SOURCES = frozenset({
    "panteao-arcanjo", "panteao-dogon", "panteao-egipcio", "panteao-grego",
    "panteao-inca", "panteao-inuit", "panteao-ioruba", "panteao-maia",
    "panteao-maori", "panteao-nordico", "panteao-norte-americano", "panteao-tao",
    "panteao-tupi-guarani", "panteao-xinto", "sombra-goetia",
})
_MATERIALIZATION_SOURCES = frozenset({
    "animais", "cores", "criaturas", "cristais", "ervas", "geometria", "metais", "notas",
})
_ARCHETIPOS = "data-mapa-arquetipos"
_ALL_SOURCES = _TRANSLATION_SOURCES | _MATERIALIZATION_SOURCES | {_ARCHETIPOS}


class TestReportLoader:

    def test_all_expected_sources_loaded(self):
        assert _ALL_SOURCES.issubset(sources())

    def test_source_count(self):
        assert len(sources()) >= 24

    def test_all_data_ids_in_translation_sources(self):
        for src in _TRANSLATION_SOURCES:
            for id_ in DATA_IDS:
                result = lookup(src, id_)
                assert result is not None, f"id={id_} missing in {src}"

    def test_all_data_ids_in_materialization_sources(self):
        for src in _MATERIALIZATION_SOURCES:
            for id_ in DATA_IDS:
                result = lookup(src, id_)
                assert result is not None, f"id={id_} missing in {src}"

    def test_all_data_ids_in_mapa_arquetipos(self):
        for id_ in DATA_IDS:
            result = lookup(_ARCHETIPOS, id_)
            assert result is not None, f"id={id_} missing in {_ARCHETIPOS}"

    def test_id_8_resolves_to_id_4(self):
        for src in _ALL_SOURCES:
            assert lookup(src, 8) == lookup(src, 4), f"id=8 != id=4 in {src}"

    def test_id_22_resolves_to_id_4(self):
        for src in _ALL_SOURCES:
            assert lookup(src, 22) == lookup(src, 4), f"id=22 != id=4 in {src}"

    def test_master_label_11(self):
        _, label = lookup_with_label("panteao-grego", 11)
        assert isinstance(label, MasterLabel)
        assert label.id_dados == 11

    def test_master_label_22(self):
        data, label = lookup_with_label("panteao-grego", 22)
        assert isinstance(label, MasterLabel)
        assert data == lookup("panteao-grego", 4)

    def test_master_label_33(self):
        _, label = lookup_with_label("panteao-grego", 33)
        assert isinstance(label, MasterLabel)
        assert label.id_dados == 33

    def test_no_master_label_for_regular_id(self):
        _, label = lookup_with_label("panteao-grego", 1)
        assert label is None

    def test_no_master_label_for_id_8(self):
        # ID 8 é Oitava Superior — herda dados silenciosamente, sem label
        _, label = lookup_with_label("panteao-grego", 8)
        assert label is None

    def test_panteao_returns_string(self):
        assert lookup("panteao-grego", 1) == "Apolo"

    def test_materializacao_returns_string(self):
        assert lookup("cores", 1) == "Amarelo"
        assert lookup("metais", 4) == "Chumbo"

    def test_mapa_arquetipos_structure(self):
        data = lookup(_ARCHETIPOS, 1)
        assert "sol" in data
        assert "lua" in data
        assert "essencia" in data["sol"]
        assert "refugio" in data["lua"]

    def test_goetia_returns_string(self):
        assert lookup("sombra-goetia", 1) == "Tirano (Paimon)"
