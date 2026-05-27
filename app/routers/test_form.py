"""GET /test e POST /test — formulário HTML de testes dos motores."""

from __future__ import annotations

from datetime import date, time
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.chapters.grupo_a import assemble_cap1, assemble_cap11, assemble_prefacio
from app.chapters.grupo_b import assemble_cap2, assemble_cap3, assemble_cap8
from app.chapters.grupo_c import assemble_cap4, assemble_cap5, assemble_cap9
from app.chapters.grupo_d import assemble_cap6, assemble_cap7
from app.chapters.grupo_e import assemble_cap10
from app.core.consolidation import consolidate
from app.core.geocoding import GeocodingError, geocode
from app.core.narrator import generate_narrative
from app.core.temporal import TimeInputType, TimeWindow, parse_time_input
from app.motors.alquimia import calculate_alquimia
from app.motors.bazi import calculate_bazi
from app.motors.cabalistica import calculate_cabalistica
from app.motors.caldeia import calculate_caldeia
from app.motors.daimon_hora import calculate_daimon_hora
from app.motors.gematria import calculate_gematria
from app.motors.iching import calculate_iching
from app.motors.pitagorica import calculate_pitagorica
from app.motors.taro import calculate_taro
from app.motors.temperamentos import calculate_temperamentos
from app.motors.tropical import calculate_tropical
from app.motors.tzolkin import calculate_tzolkin
from app.motors.vedica import calculate_vedica
from app.routers.reports import _to_json

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter(tags=["test"])

_PANTEAO_NAMES: dict[str, str] = {
    "arcanjo":         "Arcanjo",
    "dogon":           "Dogon",
    "egipcio":         "Egípcio",
    "grego":           "Grego",
    "inca":            "Inca",
    "inuit":           "Inuit",
    "ioruba":          "Iorubá",
    "maia":            "Maia",
    "maori":           "Maori",
    "nordico":         "Nórdico",
    "norte-americano": "Norte-Americano",
    "tao":             "Tao",
    "tupi-guarani":    "Tupi-Guarani",
    "xinto":           "Xinto",
}

SIGNO_GLYPHS: dict[str, str] = {
    "aries": "♈", "touro": "♉", "gemeos": "♊", "cancer": "♋",
    "leao": "♌", "virgem": "♍", "libra": "♎", "escorpiao": "♏",
    "sagitario": "♐", "capricornio": "♑", "aquario": "♒", "peixes": "♓",
}

SIGNO_REGENTES: dict[str, str] = {
    "aries": "Marte", "touro": "Vênus", "gemeos": "Mercúrio", "cancer": "Lua",
    "leao": "Sol", "virgem": "Mercúrio", "libra": "Vênus", "escorpiao": "Marte",
    "sagitario": "Júpiter", "capricornio": "Saturno", "aquario": "Urano", "peixes": "Netuno",
}


@router.get("/test", response_class=HTMLResponse)
async def test_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "test_form.html")


@router.post("/test", response_class=HTMLResponse)
async def test_submit(
    request: Request,
    nome_batismo: str = Form(...),
    nome_social: str = Form(""),
    genero: str = Form("masculino"),
    data_nascimento: str = Form(...),
    tipo_hora: str = Form(...),
    hora_exata: str = Form(""),
    janela_inicio: str = Form(""),
    janela_fim: str = Form(""),
    cidade: str = Form(...),
    estado: str = Form(""),
    pais: str = Form(""),
) -> HTMLResponse:
    capitulos: dict | None = None
    prefacio_data: dict | None = None
    narrative: dict | None = None
    debug_info: dict | None = None
    error: str | None = None

    try:
        day, month, year = data_nascimento.strip().split("/")
        birth_date = date(int(year), int(month), int(day))

        hora_obj: time | None = None
        janela_obj: TimeWindow | None = None
        if tipo_hora == "exata" and hora_exata:
            h, m = hora_exata.strip().split(":")
            hora_obj = time(int(h), int(m))
        elif tipo_hora == "janela" and janela_inicio and janela_fim:
            hi, mi = janela_inicio.strip().split(":")
            hf, mf = janela_fim.strip().split(":")
            janela_obj = TimeWindow(start=time(int(hi), int(mi)), end=time(int(hf), int(mf)))

        time_input = parse_time_input(exact_time=hora_obj, window=janela_obj)

        try:
            geo = geocode(cidade, estado, pais)
        except GeocodingError as exc:
            raise ValueError(f"Geocoding falhou: {exc}") from exc
        lat, lon, tz_name = geo.latitude, geo.longitude, geo.timezone

        nome_social_eff = nome_social.strip() or None

        tropical    = calculate_tropical(birth_date, time_input, tz_name, lat, lon)
        vedica      = calculate_vedica(birth_date, time_input, tz_name)
        bazi        = calculate_bazi(birth_date, time_input, tz_name)
        daimon_hora = calculate_daimon_hora(birth_date, time_input, tz_name, lat, lon)
        tzolkin     = calculate_tzolkin(birth_date)

        pitagorica  = calculate_pitagorica(nome_batismo, birth_date, nome_social_eff)
        cabalistica = calculate_cabalistica(nome_batismo, birth_date)
        caldeia     = calculate_caldeia(nome_batismo, birth_date)
        gematria    = calculate_gematria(nome_batismo)

        votes_fase1 = [tropical.vote, vedica.vote, bazi.vote, daimon_hora.vote, tzolkin.vote]
        votes_fase2 = [pitagorica.vote, cabalistica.vote, caldeia.vote, gematria.vote]

        votes_fase1_b: list[int] | None = None
        if time_input.type != TimeInputType.EXACT:
            votes_fase1_b = [
                tropical.vote_b   if tropical.vote_b   is not None else tropical.vote,
                vedica.vote_b     if vedica.vote_b     is not None else vedica.vote,
                bazi.vote,
                daimon_hora.vote_b if daimon_hora.vote_b is not None else daimon_hora.vote,
                tzolkin.vote,
            ]

        consolidation = consolidate(votes_fase1, votes_fase2, votes_fase1_b)

        alquimia = calculate_alquimia(tropical.sol.sign)
        taro     = calculate_taro(birth_date)
        iching   = calculate_iching(tropical.sol.longitude or 0.0)

        posicoes_a: dict[str, str | None] = {}
        for p in [tropical.sol, tropical.lua, tropical.ascendente, *tropical.planets]:
            if p is not None:
                posicoes_a[p.planet] = p.sign
        temperamentos_a = calculate_temperamentos(posicoes_a)

        temperamentos_b = None
        if consolidation.id_dominante_b is not None:
            posicoes_b: dict[str, str | None] = {}
            for p in [tropical.sol, tropical.lua, tropical.ascendente, *tropical.planets]:
                if p is not None:
                    posicoes_b[p.planet] = p.sign_b if p.sign_b is not None else p.sign
            temperamentos_b = calculate_temperamentos(posicoes_b)

        prefacio_raw = assemble_prefacio(consolidation)
        cap1  = assemble_cap1(consolidation)
        cap2  = assemble_cap2(tropical, temperamentos_a, temperamentos_b)
        cap3  = assemble_cap3(vedica)
        cap4  = assemble_cap4(bazi)
        cap5  = assemble_cap5(tzolkin)
        cap6  = assemble_cap6(pitagorica, cabalistica, caldeia, gematria)
        cap7  = assemble_cap7(taro, iching)
        cap8  = assemble_cap8(alquimia)
        cap9  = assemble_cap9(daimon_hora)
        cap10 = assemble_cap10(consolidation)
        cap11 = assemble_cap11(consolidation)

        report_dict = {
            "consolidation": _to_json(consolidation),
            "prefacio": _to_json(prefacio_raw),
            "capitulos": {
                "cap1":  _to_json(cap1),
                "cap2":  _to_json(cap2),
                "cap3":  _to_json(cap3),
                "cap4":  _to_json(cap4),
                "cap5":  _to_json(cap5),
                "cap6":  _to_json(cap6),
                "cap7":  _to_json(cap7),
                "cap8":  _to_json(cap8),
                "cap9":  _to_json(cap9),
                "cap10": _to_json(cap10),
                "cap11": _to_json(cap11),
            },
            "debug": {
                "votes_fase1":   votes_fase1,
                "votes_fase2":   votes_fase2,
                "votes_fase1_b": votes_fase1_b,
                "tz_name": tz_name,
                "lat": lat,
                "lon": lon,
            },
        }

        capitulos    = report_dict["capitulos"]
        prefacio_data = report_dict["prefacio"]
        narrative    = generate_narrative(report_dict, genero=genero)
        debug_info   = report_dict["debug"] | {
            "id_dominante": consolidation.id_dominante,
            "status": consolidation.status.value,
        }

    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"

    return templates.TemplateResponse(
        request,
        "test_form.html",
        {
            "capitulos":     capitulos,
            "prefacio_data": prefacio_data,
            "narrative":     narrative,
            "panteao_names": _PANTEAO_NAMES,
            "signo_glyphs":  SIGNO_GLYPHS,
            "signo_regentes": SIGNO_REGENTES,
            "debug_info":    debug_info,
            "error":         error,
            "form": {
                "nome_batismo":    nome_batismo,
                "nome_social":     nome_social,
                "genero":          genero,
                "data_nascimento": data_nascimento,
                "tipo_hora":       tipo_hora,
                "hora_exata":      hora_exata,
                "janela_inicio":   janela_inicio,
                "janela_fim":      janela_fim,
                "cidade":          cidade,
                "estado":          estado,
                "pais":            pais,
            },
        },
    )
