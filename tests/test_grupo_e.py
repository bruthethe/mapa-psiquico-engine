"""Testes do Grupo E — Cap. 10, Cap. 11 (5.8)."""

from app.chapters.grupo_e import (
    Cap10Data, Cap11Data,
    assemble_cap10, assemble_cap11,
)
from app.core.consolidation import ConsolidationResult
from app.core.ids import MasterLabel
from app.core.motor_types import HDActivation, HDResult
from app.core.nivel2 import PanteoesData
from app.core.temporal import TemporalStatus
from app.motors.medicina import MedicinaResult


# ── Stubs ─────────────────────────────────────────────────────────────────────

def _activation(planeta: str = "sol", gate: int = 1, linha: int = 1) -> HDActivation:
    return HDActivation(planeta=planeta, longitude=0.0, gate=gate, linha=linha)


def _hd(
    tipo: str = "Gerador",
    estrategia: str = "Esperar para responder",
    tipo_id: int = 3,
    autoridade: str = "Sacral",
    aut_id: int = 3,
    porta: int = 1,
    status: TemporalStatus = TemporalStatus.EXACT,
    tipo_b: str | None = None,
    estrategia_b: str | None = None,
    tipo_b_id: int | None = None,
    porta_b: int | None = None,
) -> HDResult:
    act = [_activation()]
    return HDResult(
        personalidade=act,
        design=act,
        centros_definidos=frozenset({"Sacral", "G_Centro"}),
        canais_ativos=[(2, 14)],
        tipo=tipo,
        estrategia=estrategia,
        tipo_id_gatilho=tipo_id,
        autoridade=autoridade,
        autoridade_id_gatilho=aut_id,
        porta_sol_personalidade=porta,
        vote=tipo_id,
        overall_status=status,
        tipo_b=tipo_b,
        estrategia_b=estrategia_b,
        tipo_b_id_gatilho=tipo_b_id,
        porta_sol_personalidade_b=porta_b,
    )


def _medicina(chakra: str = "Sacro", sistema: str = "Sistema Reprodutor", frequencia: str = "417 Hz") -> MedicinaResult:
    return MedicinaResult(
        chakra=chakra,
        sistema=sistema,
        frequencia=frequencia,
        id_gatilho=3,
        fallback=False,
        overall_status=TemporalStatus.EXACT,
    )


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


# ── Cap. 10 ───────────────────────────────────────────────────────────────────

class TestAssembleCap10:

    def test_retorna_cap10data(self):
        r = assemble_cap10(_hd(), _medicina())
        assert isinstance(r, Cap10Data)

    def test_tipo_propagado(self):
        r = assemble_cap10(_hd(tipo="Manifestador", tipo_id=1), _medicina())
        assert r.tipo == "Manifestador"
        assert r.tipo_id_gatilho == 1

    def test_estrategia_propagada(self):
        r = assemble_cap10(_hd(estrategia="Informar antes de agir"), _medicina())
        assert r.estrategia == "Informar antes de agir"

    def test_autoridade_propagada(self):
        r = assemble_cap10(_hd(autoridade="Emocional", aut_id=2), _medicina())
        assert r.autoridade == "Emocional"
        assert r.autoridade_id_gatilho == 2

    def test_centros_definidos_propagados(self):
        r = assemble_cap10(_hd(), _medicina())
        assert "Sacral" in r.centros_definidos
        assert "G_Centro" in r.centros_definidos

    def test_canais_convertidos_para_tuple(self):
        r = assemble_cap10(_hd(), _medicina())
        assert isinstance(r.canais_ativos, tuple)
        assert r.canais_ativos == ((2, 14),)

    def test_porta_sol_propagada(self):
        r = assemble_cap10(_hd(porta=29), _medicina())
        assert r.porta_sol_personalidade == 29

    def test_activations_convertidas_para_tuple(self):
        r = assemble_cap10(_hd(), _medicina())
        assert isinstance(r.personalidade, tuple)
        assert isinstance(r.design, tuple)
        assert r.personalidade[0].planeta == "sol"

    def test_chakra_hz_da_medicina(self):
        r = assemble_cap10(_hd(), _medicina(chakra="Frontal", sistema="Pineal", frequencia="852 Hz"))
        assert r.chakra == "Frontal"
        assert r.sistema == "Pineal"
        assert r.frequencia == "852 Hz"

    def test_exact_sem_b(self):
        r = assemble_cap10(_hd(), _medicina())
        assert r.tipo_b is None
        assert r.estrategia_b is None
        assert r.tipo_b_id_gatilho is None
        assert r.porta_sol_personalidade_b is None

    def test_hybrid_com_b(self):
        hd = _hd(
            status=TemporalStatus.HYBRID,
            tipo_b="Projetor",
            estrategia_b="Esperar pelo convite",
            tipo_b_id=5,
            porta_b=12,
        )
        r = assemble_cap10(hd, _medicina())
        assert r.tipo_b == "Projetor"
        assert r.estrategia_b == "Esperar pelo convite"
        assert r.tipo_b_id_gatilho == 5
        assert r.porta_sol_personalidade_b == 12

    def test_hybrid_porta_b_none_quando_igual(self):
        hd = _hd(
            porta=1,
            status=TemporalStatus.HYBRID,
            tipo_b="Projetor",
            estrategia_b="Esperar pelo convite",
            tipo_b_id=5,
            porta_b=None,   # mesmo portal
        )
        r = assemble_cap10(hd, _medicina())
        assert r.porta_sol_personalidade_b is None

    def test_refletor_lunar(self):
        hd = _hd(tipo="Refletor", estrategia="Aguardar um ciclo lunar completo (28,5 dias)", tipo_id=2)
        r = assemble_cap10(hd, _medicina())
        assert r.tipo == "Refletor"
        assert "lunar" in r.estrategia.lower()


# ── Cap. 11 ───────────────────────────────────────────────────────────────────

class TestAssembleCap11:

    def test_retorna_cap11data(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()):
            r = assemble_cap11(_consolidation(id_a=3))
        assert isinstance(r, Cap11Data)

    def test_panteoes_b_none_em_exact(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()):
            r = assemble_cap11(_consolidation(id_a=3))
        assert r.panteoes_b is None

    def test_panteoes_b_preenchido_em_hybrid(self):
        import unittest.mock as mock
        panteoes_a = _panteoes()
        panteoes_b = PanteoesData(divindades={"grego": "Ares"}, master_label=None)
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", side_effect=[panteoes_a, panteoes_b]):
            r = assemble_cap11(_consolidation(id_a=3, id_b=1, status=TemporalStatus.HYBRID))
        assert r.panteoes.divindades["grego"] == "Zeus"
        assert r.panteoes_b is not None
        assert r.panteoes_b.divindades["grego"] == "Ares"

    def test_panteoes_divindades_dict(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()):
            r = assemble_cap11(_consolidation(id_a=3))
        assert isinstance(r.panteoes.divindades, dict)
        assert "grego" in r.panteoes.divindades

    def test_master_label_propagado(self):
        import unittest.mock as mock
        label = MasterLabel(id_dados=11, titulo="O Portal", texto="Frequência de Ruptura")
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes(master=label)):
            r = assemble_cap11(_consolidation(id_a=11))
        assert r.panteoes.master_label is not None
        assert r.panteoes.master_label.id_dados == 11

    def test_lookup_chamado_com_id_correto(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()) as mock_lookup:
            assemble_cap11(_consolidation(id_a=7))
        mock_lookup.assert_called_once_with(7)

    def test_lookup_chamado_duas_vezes_em_hybrid(self):
        import unittest.mock as mock
        with mock.patch("app.chapters.grupo_e.lookup_panteoes", return_value=_panteoes()) as mock_lookup:
            assemble_cap11(_consolidation(id_a=3, id_b=9, status=TemporalStatus.HYBRID))
        assert mock_lookup.call_count == 2
        mock_lookup.assert_any_call(3)
        mock_lookup.assert_any_call(9)
