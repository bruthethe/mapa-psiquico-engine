"""Testes do narrator: preparação de dados (5.5.2) e fallback (5.5.4).

Valida filtragem de campos internos, remoção de _b nulos, tradução de valores
e resiliência a falhas de API — sem chamar a API Anthropic.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.core.narrator import _clean, _prepare_for_narrator, generate_narrative


# ── Fixtures de relatório sintético ───────────────────────────────────────────

def _report_exact() -> dict:
    """Perfil EXACT (Status 3): sem campos _b, nakshatra sem nome_b."""
    return {
        "consolidation": {"id_dominante": 7, "id_dominante_b": None, "votes": [7, 7, 7]},
        "prefacio": {
            "id_dominante": 7,
            "id_dominante_b": None,
            "status": "EXACT",
            "master_label": {"titulo": "O Sábio", "texto": "Busca a verdade interior."},
            "master_label_b": None,
        },
        "capitulos": {
            "cap1": {
                "arquetipos": {
                    "essencia_solar": "Contemplação",
                    "mascara": "Reservado",
                    "refugio_lunar": "Silêncio",
                    "necessidade": "Isolamento criativo",
                    "demonio": "Paranoia",
                },
                "goetia": {"nome": "Valac", "id_gatilho": 7},
            },
            "cap3": {
                "nakshatra": {
                    "index": 14,
                    "nome": "Chitra",
                    "id_gatilho": 7,
                    "regente": "Marte",
                    "pada": 2,
                    "purushartha": "Kama",
                    "simbolo": "Pérola brilhante",
                    "deidade": "Vishwakarma",
                    "qualidade": "Rajásica",
                    "status": "EXACT",
                    "nome_b": None,
                    "id_gatilho_b": None,
                    "pada_b": None,
                },
                "atmakaraka": {
                    "graha": "shani",
                    "id_gatilho": 4,
                    "grau_no_signo": 22.47,
                },
                "purushartha": "Kama",
            },
        },
        "debug": {"votes_fase1": [7, 7, 7], "tz_name": "Europe/London"},
    }


def _report_hybrid() -> dict:
    """Perfil HYBRID (Status 1): dois arquétipos simultâneos."""
    return {
        "consolidation": {"id_dominante": 3, "id_dominante_b": 9},
        "prefacio": {
            "id_dominante": 3,
            "id_dominante_b": 9,
            "status": "HYBRID",
            "master_label": {"titulo": "O Criador", "texto": "Expressa o mundo em formas."},
            "master_label_b": {"titulo": "O Ermitão", "texto": "Retira-se para encontrar."},
        },
        "capitulos": {
            "cap9": {
                "planeta": "Mercúrio",
                "id_gatilho": 3,
                "numero_hora": 5,
                "periodo": "diurno",
                "tipo": "Gênio",
                "planeta_b": "Lua",
                "id_gatilho_b": 9,
                "tipo_b": "Guardião",
            },
        },
        "debug": {},
    }


def _report_hd() -> dict:
    """Perfil com ativações Human Design — deve remover longitude."""
    return {
        "consolidation": {"id_dominante": 1},
        "prefacio": {"id_dominante": 1, "id_dominante_b": None, "status": "EXACT",
                     "master_label": None, "master_label_b": None},
        "capitulos": {
            "cap10": {
                "tipo": "Manifestador",
                "estrategia": "Informar antes de agir",
                "tipo_id_gatilho": 1,
                "autoridade": "Emocional",
                "autoridade_id_gatilho": 1,
                "centros_definidos": ["Plexo Solar", "Garganta"],
                "canais_ativos": [[20, 34]],
                "porta_sol_personalidade": 20,
                "personalidade": [
                    {"planeta": "Sol", "longitude": 123.456, "gate": 20, "linha": 3},
                    {"planeta": "Lua", "longitude": 87.1, "gate": 34, "linha": 1},
                ],
                "design": [
                    {"planeta": "Sol", "longitude": 290.0, "gate": 51, "linha": 6},
                ],
                "chakra": "Plexo Solar",
                "sistema": "Sistema Digestivo",
                "frequencia": "528 Hz",
                "tipo_b": None,
                "estrategia_b": None,
                "tipo_b_id_gatilho": None,
                "porta_sol_personalidade_b": None,
            },
        },
        "debug": {},
    }


# ── Testes de _clean ───────────────────────────────────────────────────────────

class TestClean:

    def test_strip_id_gatilho(self):
        data = {"nome": "Chitra", "id_gatilho": 7, "regente": "Marte"}
        result = _clean(data)
        assert "id_gatilho" not in result
        assert result["nome"] == "Chitra"

    def test_strip_vote_and_status(self):
        data = {"tipo": "Manifestador", "vote": 1, "overall_status": "EXACT", "status": "EXACT"}
        result = _clean(data)
        assert "vote" not in result
        assert "overall_status" not in result
        assert "status" not in result
        assert result["tipo"] == "Manifestador"

    def test_strip_longitude_from_hd_activation(self):
        activation = {"planeta": "Sol", "longitude": 123.456, "gate": 20, "linha": 3}
        result = _clean(activation)
        assert "longitude" not in result
        assert result["gate"] == 20
        assert result["linha"] == 3
        assert result["planeta"] == "Sol"

    def test_remove_null_b_fields(self):
        data = {"nome": "Chitra", "nome_b": None, "pada": 2, "pada_b": None}
        result = _clean(data)
        assert "nome_b" not in result
        assert "pada_b" not in result
        assert result["nome"] == "Chitra"

    def test_keep_non_null_b_fields(self):
        data = {"tipo": "Manifestador", "tipo_b": "Projetor", "estrategia_b": None}
        result = _clean(data)
        assert result["tipo_b"] == "Projetor"
        assert "estrategia_b" not in result

    def test_translate_graha_shani(self):
        data = {"graha": "shani", "grau_no_signo": 22.47}
        result = _clean(data)
        assert result["graha"] == "Saturno"

    def test_translate_graha_surya(self):
        data = {"graha": "surya"}
        result = _clean(data)
        assert result["graha"] == "Sol"

    def test_translate_all_grahas(self):
        grahas = {
            "surya": "Sol", "chandra": "Lua", "mangala": "Marte",
            "budha": "Mercúrio", "guru": "Júpiter", "shukra": "Vênus",
            "shani": "Saturno", "rahu": "Rahu (Nó Norte)", "ketu": "Ketu (Nó Sul)",
        }
        for sanskrit, pt in grahas.items():
            assert _clean({"graha": sanskrit})["graha"] == pt

    def test_translate_periodo_diurno(self):
        data = {"periodo": "diurno"}
        result = _clean(data)
        assert result["periodo"] == "nascido durante o dia"

    def test_translate_periodo_noturno(self):
        data = {"periodo": "noturno"}
        result = _clean(data)
        assert result["periodo"] == "nascido durante a noite"

    def test_strip_index(self):
        data = {"index": 14, "nome": "Chitra"}
        result = _clean(data)
        assert "index" not in result

    def test_nested_recursion(self):
        data = {
            "nakshatra": {"id_gatilho": 7, "nome": "Chitra", "graha": "surya"},
            "vote": 7,
        }
        result = _clean(data)
        assert "vote" not in result
        assert "id_gatilho" not in result["nakshatra"]
        assert result["nakshatra"]["graha"] == "Sol"

    def test_list_of_dicts(self):
        data = [
            {"planeta": "Sol", "longitude": 100.0, "gate": 20},
            {"planeta": "Lua", "longitude": 200.0, "gate": 34},
        ]
        result = _clean(data)
        assert isinstance(result, list)
        assert len(result) == 2
        assert "longitude" not in result[0]
        assert result[0]["gate"] == 20


# ── Testes de _prepare_for_narrator ───────────────────────────────────────────

class TestPrepareForNarrator:

    def test_excludes_debug(self):
        report = _report_exact()
        result = _prepare_for_narrator(report)
        assert "debug" not in result

    def test_excludes_consolidation(self):
        report = _report_exact()
        result = _prepare_for_narrator(report)
        assert "consolidation" not in result

    def test_includes_prefacio_and_capitulos(self):
        report = _report_exact()
        result = _prepare_for_narrator(report)
        assert "prefacio" in result
        assert "capitulos" in result

    def test_exact_profile_prefacio(self):
        result = _prepare_for_narrator(_report_exact())
        pref = result["prefacio"]
        assert pref["id_dominante"] == 7
        assert "id_dominante_b" not in pref   # None _b stripped
        assert "status" not in pref            # stripped
        assert pref["master_label"]["titulo"] == "O Sábio"
        assert "master_label_b" not in pref    # None _b stripped

    def test_exact_profile_goetia_internal_stripped(self):
        result = _prepare_for_narrator(_report_exact())
        goetia = result["capitulos"]["cap1"]["goetia"]
        assert "id_gatilho" not in goetia
        assert goetia["nome"] == "Valac"

    def test_exact_profile_nakshatra_cleaned(self):
        result = _prepare_for_narrator(_report_exact())
        nk = result["capitulos"]["cap3"]["nakshatra"]
        assert "index" not in nk
        assert "id_gatilho" not in nk
        assert "status" not in nk
        assert "nome_b" not in nk
        assert "id_gatilho_b" not in nk
        assert "pada_b" not in nk
        assert nk["nome"] == "Chitra"

    def test_exact_profile_atmakaraka_graha_translated(self):
        result = _prepare_for_narrator(_report_exact())
        atm = result["capitulos"]["cap3"]["atmakaraka"]
        assert "id_gatilho" not in atm
        assert atm["graha"] == "Saturno"
        assert atm["grau_no_signo"] == 22.47

    def test_hybrid_profile_b_fields_kept(self):
        result = _prepare_for_narrator(_report_hybrid())
        pref = result["prefacio"]
        assert pref["id_dominante_b"] == 9
        assert pref["master_label_b"]["titulo"] == "O Ermitão"

    def test_hybrid_profile_cap9_cleaned(self):
        result = _prepare_for_narrator(_report_hybrid())
        cap9 = result["capitulos"]["cap9"]
        assert "id_gatilho" not in cap9
        assert "id_gatilho_b" not in cap9
        assert cap9["periodo"] == "nascido durante o dia"
        assert cap9["tipo"] == "Gênio"
        assert cap9["tipo_b"] == "Guardião"
        assert cap9["planeta_b"] == "Lua"

    def test_hd_profile_activations_stripped(self):
        result = _prepare_for_narrator(_report_hd())
        cap10 = result["capitulos"]["cap10"]
        # Arrays brutos de ativações removidos — resumidos por canais_ativos e porta_sol
        assert "personalidade" not in cap10
        assert "design" not in cap10
        # IDs internos removidos
        assert "tipo_id_gatilho" not in cap10
        assert "autoridade_id_gatilho" not in cap10
        # Campos _b nulos removidos
        assert "tipo_b" not in cap10
        assert "estrategia_b" not in cap10
        assert "tipo_b_id_gatilho" not in cap10
        assert "porta_sol_personalidade_b" not in cap10
        # Dados válidos presentes
        assert cap10["tipo"] == "Manifestador"
        assert cap10["chakra"] == "Plexo Solar"
        assert cap10["porta_sol_personalidade"] == 20


# ── Testes de fallback (5.5.4) ────────────────────────────────────────────────

class TestGenerateNarrativeFallback:

    def test_returns_empty_dict_when_api_key_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            # sem ANTHROPIC_API_KEY — RuntimeError interno deve ser absorvido
            import app.core.narrator as mod
            original = mod._client
            mod._client = None  # força re-init
            try:
                result = generate_narrative({"prefacio": {}, "capitulos": {}})
                assert result == {}
            finally:
                mod._client = original

    def test_returns_empty_dict_on_api_exception(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API indisponível")
        with patch("app.core.narrator._get_client", return_value=mock_client):
            result = generate_narrative({"prefacio": {}, "capitulos": {}})
        assert result == {}

    def test_returns_empty_dict_on_timeout(self):
        import httpx
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = httpx.TimeoutException("timeout")
        with patch("app.core.narrator._get_client", return_value=mock_client):
            result = generate_narrative({"prefacio": {}, "capitulos": {}})
        assert result == {}

    def test_returns_empty_dict_on_json_parse_error(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="não é json válido")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        with patch("app.core.narrator._get_client", return_value=mock_client):
            result = generate_narrative({"prefacio": {}, "capitulos": {}})
        assert result == {}

    def test_success_path_returns_narrative(self):
        resp_lote1 = MagicMock()
        resp_lote1.content = [MagicMock(type="text", text='{"capitulos": {"cap1": {"essencia_solar": {"nome": "O Sábio", "tipo": "essencia_solar", "texto": "Essência."}}}}')]
        resp_lote2 = MagicMock()
        resp_lote2.content = [MagicMock(type="text", text='{"capitulos": {"cap7": {"taro": {"arcano": 5, "nome_arcano": "O Hierofante", "texto": "Tarô."}}}}')]
        resp_lote3 = MagicMock()
        resp_lote3.content = [MagicMock(type="text", text='{"prefacio": "Você é...", "conclusao": "Integração fecunda."}')]
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [resp_lote1, resp_lote2, resp_lote3]
        with patch("app.core.narrator._get_client", return_value=mock_client):
            result = generate_narrative({"prefacio": {}, "capitulos": {}})
        assert result["prefacio"] == "Você é..."
        assert result["conclusao"] == "Integração fecunda."
        assert result["capitulos"]["cap1"]["essencia_solar"]["texto"] == "Essência."
        assert result["capitulos"]["cap7"]["taro"]["texto"] == "Tarô."
