"""Testes do Grupo D — Cap. 6, Cap. 7 (5.7)."""

from app.chapters.grupo_d import (
    Cap6Data, Cap7Data,
    assemble_cap6, assemble_cap7,
)
from app.core.temporal import TemporalStatus
from app.motors.cabalistica import CabalisticaResult
from app.motors.caldeia import CaldeiaResult
from app.motors.gematria import GematriaResult
from app.motors.iching import IChingResult
from app.motors.pitagorica import PitagoricaResult
from app.motors.taro import TaroResult


# ── Stubs ─────────────────────────────────────────────────────────────────────

def _pitagorica(
    alma: int = 1, persona: int = 3, expressao: int = 4,
    vibe: int = 4, caminho: int = 7,
) -> PitagoricaResult:
    return PitagoricaResult(
        id_alma=alma,
        id_persona=persona,
        id_expressao=expressao,
        id_vibe_atual=vibe,
        ajuste_frequencia=expressao - vibe,
        caminho_vida=caminho,
        vote=caminho,
        overall_status=TemporalStatus.EXACT,
    )


def _cabalistica(
    motivacao: int = 2, impressao: int = 5, expressao: int = 7,
    missao: int = 9,
) -> CabalisticaResult:
    return CabalisticaResult(
        id_motivacao=motivacao,
        id_impressao=impressao,
        id_expressao=expressao,
        missao_vida=missao,
        dividas_karmicas=frozenset(),
        vote=missao,
        overall_status=TemporalStatus.EXACT,
    )


def _caldeia(nome: int = 6, psiquica: int = 3, destino: int = 9) -> CaldeiaResult:
    return CaldeiaResult(
        id_nome=nome,
        vibracao_psiquica=psiquica,
        numero_destino=destino,
        vote=destino,
        overall_status=TemporalStatus.EXACT,
    )


def _gematria(hebraico: int = 5, grego: int = 8) -> GematriaResult:
    return GematriaResult(
        id_hebraico=hebraico,
        id_grego=grego,
        vote=grego,
        overall_status=TemporalStatus.EXACT,
    )


def _taro(arcano: int = 8, nome: str = "A Justiça", id_gatilho: int = 4) -> TaroResult:
    return TaroResult(
        arcano=arcano,
        nome_arcano=nome,
        id_gatilho=id_gatilho,
        vote=id_gatilho,
        overall_status=TemporalStatus.EXACT,
    )


def _iching(
    hexagrama: int = 1, nome: str = "O Criativo",
    sentenca: str = "Ação persistente", id_gatilho: int = 1,
    fallback: bool = False,
) -> IChingResult:
    return IChingResult(
        hexagrama=hexagrama,
        nome=nome,
        sentenca=sentenca,
        id_gatilho=id_gatilho,
        vote=id_gatilho,
        fallback=fallback,
        overall_status=TemporalStatus.EXACT,
    )


# ── Cap. 6 ────────────────────────────────────────────────────────────────────

class TestAssembleCap6:

    def test_retorna_cap6data(self):
        r = assemble_cap6(_pitagorica(), _cabalistica(), _caldeia(), _gematria())
        assert isinstance(r, Cap6Data)

    def test_pitagorica_propagada(self):
        r = assemble_cap6(_pitagorica(alma=2, caminho=11), _cabalistica(), _caldeia(), _gematria())
        assert r.pitagorica.id_alma == 2
        assert r.pitagorica.caminho_vida == 11

    def test_cabalistica_propagada(self):
        r = assemble_cap6(_pitagorica(), _cabalistica(motivacao=3, missao=22), _caldeia(), _gematria())
        assert r.cabalistica.id_motivacao == 3
        assert r.cabalistica.missao_vida == 22

    def test_caldeia_propagada(self):
        r = assemble_cap6(_pitagorica(), _cabalistica(), _caldeia(destino=6), _gematria())
        assert r.caldeia.numero_destino == 6

    def test_gematria_propagada(self):
        r = assemble_cap6(_pitagorica(), _cabalistica(), _caldeia(), _gematria(hebraico=5, grego=8))
        assert r.gematria.id_hebraico == 5
        assert r.gematria.id_grego == 8

    def test_dividas_karmicas_vazias(self):
        r = assemble_cap6(_pitagorica(), _cabalistica(), _caldeia(), _gematria())
        assert r.cabalistica.dividas_karmicas == frozenset()

    def test_dividas_karmicas_preenchidas(self):
        cab = _cabalistica()
        cab_com_divida = CabalisticaResult(
            id_motivacao=cab.id_motivacao,
            id_impressao=cab.id_impressao,
            id_expressao=cab.id_expressao,
            missao_vida=cab.missao_vida,
            dividas_karmicas=frozenset({13, 16}),
            vote=cab.vote,
            overall_status=cab.overall_status,
        )
        r = assemble_cap6(_pitagorica(), cab_com_divida, _caldeia(), _gematria())
        assert 13 in r.cabalistica.dividas_karmicas
        assert 16 in r.cabalistica.dividas_karmicas

    def test_ajuste_frequencia_calculado(self):
        pit = _pitagorica(expressao=7, vibe=4)
        r = assemble_cap6(pit, _cabalistica(), _caldeia(), _gematria())
        assert r.pitagorica.ajuste_frequencia == 3

    def test_todos_status_exact(self):
        r = assemble_cap6(_pitagorica(), _cabalistica(), _caldeia(), _gematria())
        assert r.pitagorica.overall_status == TemporalStatus.EXACT
        assert r.cabalistica.overall_status == TemporalStatus.EXACT
        assert r.caldeia.overall_status == TemporalStatus.EXACT
        assert r.gematria.overall_status == TemporalStatus.EXACT


# ── Cap. 7 ────────────────────────────────────────────────────────────────────

class TestAssembleCap7:

    def test_retorna_cap7data(self):
        r = assemble_cap7(_taro(), _iching())
        assert isinstance(r, Cap7Data)

    def test_taro_propagado(self):
        r = assemble_cap7(_taro(arcano=11, nome="A Força", id_gatilho=1), _iching())
        assert r.taro.arcano == 11
        assert r.taro.nome_arcano == "A Força"
        assert r.taro.id_gatilho == 1

    def test_taro_louco_id33(self):
        r = assemble_cap7(_taro(arcano=22, nome="O Louco", id_gatilho=33), _iching())
        assert r.taro.arcano == 22
        assert r.taro.id_gatilho == 33

    def test_iching_propagado(self):
        r = assemble_cap7(_taro(), _iching(hexagrama=29, nome="O Abismal", id_gatilho=7))
        assert r.iching.hexagrama == 29
        assert r.iching.nome == "O Abismal"
        assert r.iching.id_gatilho == 7

    def test_iching_fallback_preserva_hexagrama_original(self):
        r = assemble_cap7(_taro(), _iching(hexagrama=33, nome="O Criativo", id_gatilho=1, fallback=True))
        assert r.iching.hexagrama == 33
        assert r.iching.fallback is True
        assert r.iching.nome == "O Criativo"

    def test_iching_sem_fallback(self):
        r = assemble_cap7(_taro(), _iching(hexagrama=64, fallback=False))
        assert r.iching.fallback is False

    def test_sentenca_oracular_presente(self):
        r = assemble_cap7(_taro(), _iching(sentenca="Força divina persistente"))
        assert r.iching.sentenca == "Força divina persistente"

    def test_taro_status_exact(self):
        r = assemble_cap7(_taro(), _iching())
        assert r.taro.overall_status == TemporalStatus.EXACT

    def test_iching_status_exact(self):
        r = assemble_cap7(_taro(), _iching())
        assert r.iching.overall_status == TemporalStatus.EXACT
