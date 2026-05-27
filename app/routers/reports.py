"""POST /reports/generate — orquestra todos os motores e retorna o relatório completo."""

from __future__ import annotations

import dataclasses
import io
import uuid
from dataclasses import is_dataclass
from datetime import date, time
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chapters.grupo_a import assemble_cap1, assemble_cap11, assemble_prefacio
from app.core.config import frontend_url
from app.chapters.grupo_b import assemble_cap2, assemble_cap3, assemble_cap8
from app.chapters.grupo_c import assemble_cap4, assemble_cap5, assemble_cap9
from app.chapters.grupo_d import assemble_cap6, assemble_cap7
from app.chapters.grupo_e import assemble_cap10
from app.core.consolidation import consolidate
from app.core.geocoding import GeocodingError, geocode
from app.core.narrator import generate_narrative
from app.core.temporal import TimeInputType, TimeWindow, parse_time_input
from app.db.models import Report
from app.db.session import get_db
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

router = APIRouter(prefix="/reports", tags=["reports"])


# ── Response schemas ───────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    ok: bool
    id: str
    created_at: str
    prefacio: dict[str, Any] | None
    capitulos: dict[str, Any] | None
    narrative: dict[str, Any] | None
    debug: dict[str, Any] | None


class GenerateResponse(BaseModel):
    ok: bool
    id: str
    narrative: dict[str, Any] | None
    debug: dict[str, Any] | None


class ReportRequest(BaseModel):
    nome_batismo: str
    nome_social: str | None = None
    genero: str = "masculino"   # "masculino" | "feminino" | "neutro"
    data_nascimento: date
    hora_exata: time | None = None
    janela: TimeWindow | None = None
    # Localização: fornecer lat/lon/tz_name diretamente OU cidade para geocoding
    cidade: str | None = None
    estado: str = ""
    pais: str = ""
    lat: float | None = None
    lon: float | None = None
    tz_name: str | None = None


def _to_json(obj: Any) -> Any:
    """Serializa dataclasses, Enums, frozensets e date/time para tipos JSON-safe."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _to_json(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, frozenset | set):
        return sorted(_to_json(i) for i in obj)
    if isinstance(obj, tuple | list):
        return [_to_json(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _to_json(v) for k, v in obj.items()}
    if isinstance(obj, date | time):
        return obj.isoformat()
    return obj


def _error(msg: str, status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": msg})


@router.post("/generate", response_model=GenerateResponse)
async def generate_report(
    req: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        # 1. Protocolo temporal
        time_input = parse_time_input(
            exact_time=req.hora_exata,
            window=req.janela,
        )

        # 2. Localização
        if req.lat is not None and req.lon is not None and req.tz_name is not None:
            lat, lon, tz_name = req.lat, req.lon, req.tz_name
        elif req.cidade:
            try:
                geo = geocode(req.cidade, req.estado, req.pais)
            except GeocodingError as exc:
                return _error(f"Geocoding falhou: {exc}")
            lat, lon, tz_name = geo.latitude, geo.longitude, geo.timezone
        else:
            return _error("Informe lat/lon/tz_name ou cidade para localização.")

        # 3. Motores temporais — Fase 1
        tropical = calculate_tropical(req.data_nascimento, time_input, tz_name, lat, lon)
        vedica = calculate_vedica(req.data_nascimento, time_input, tz_name)
        bazi = calculate_bazi(req.data_nascimento, time_input, tz_name)
        daimon_hora = calculate_daimon_hora(req.data_nascimento, time_input, tz_name, lat, lon)
        tzolkin = calculate_tzolkin(req.data_nascimento)

        # 4. Motores nominais — Fase 2
        pitagorica = calculate_pitagorica(req.nome_batismo, req.data_nascimento, req.nome_social)
        cabalistica = calculate_cabalistica(req.nome_batismo, req.data_nascimento)
        caldeia = calculate_caldeia(req.nome_batismo, req.data_nascimento)
        gematria = calculate_gematria(req.nome_batismo)

        # 5. Votos para consolidação
        votes_fase1 = [
            tropical.vote,
            vedica.vote,
            bazi.vote,
            daimon_hora.vote,
            tzolkin.vote,
        ]
        votes_fase2 = [pitagorica.vote, cabalistica.vote, caldeia.vote, gematria.vote]

        votes_fase1_b: list[int] | None = None
        if time_input.type != TimeInputType.EXACT:
            votes_fase1_b = [
                tropical.vote_b if tropical.vote_b is not None else tropical.vote,
                vedica.vote_b if vedica.vote_b is not None else vedica.vote,
                bazi.vote,  # pilar do dia — independente da hora
                daimon_hora.vote_b if daimon_hora.vote_b is not None else daimon_hora.vote,
                tzolkin.vote,  # data apenas — sem variação temporal
            ]

        # 6. Consolidação
        consolidation = consolidate(votes_fase1, votes_fase2, votes_fase1_b)

        # 7. Motores derivados (dependem da consolidação ou de outros motores)
        alquimia = calculate_alquimia(tropical.sol.sign)
        taro = calculate_taro(req.data_nascimento)
        iching = calculate_iching(tropical.sol.longitude or 0.0)

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

        # 8. Montagem dos capítulos
        prefacio = assemble_prefacio(consolidation)
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

        report = {
            "consolidation": _to_json(consolidation),
            "prefacio": _to_json(prefacio),
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

        # 9. Narrativa — gerada uma única vez e persistida
        narrative = generate_narrative(report, genero=req.genero)

        # 10. Persistência
        record = Report(report_json=report, narrative_json=narrative or None)
        db.add(record)
        await db.commit()
        await db.refresh(record)

        return JSONResponse(content={
            "ok": True,
            "id": str(record.id),
            "narrative": narrative,
            "debug": report["debug"],
        })

    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"{type(exc).__name__}: {exc}"},
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Retorna relatório salvo + narrativa. Nunca chama a IA novamente."""
    try:
        uid = uuid.UUID(report_id)
    except ValueError:
        return _error("ID inválido.", 400)

    result = await db.execute(select(Report).where(Report.id == uid))
    record = result.scalar_one_or_none()

    if record is None:
        return _error("Relatório não encontrado.", 404)

    return JSONResponse(content={
        "ok": True,
        "id": str(record.id),
        "created_at": record.created_at.isoformat(),
        "prefacio": record.report_json.get("prefacio"),
        "capitulos": record.report_json.get("capitulos"),
        "narrative": record.narrative_json,
        "debug": record.report_json.get("debug"),
    })


@router.get("/{report_id}/pdf")
async def get_report_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Gera PDF do relatório via Playwright (headless Chromium) e retorna como stream."""
    try:
        uid = uuid.UUID(report_id)
    except ValueError:
        return _error("ID inválido.", 400)

    result = await db.execute(select(Report).where(Report.id == uid))
    if result.scalar_one_or_none() is None:
        return _error("Relatório não encontrado.", 404)

    url = f"{frontend_url()}/report/{report_id}/print"

    try:
        from playwright.async_api import async_playwright  # noqa: PLC0415
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            # Landscape desktop: 1280×800px ativa layout de desktop (sem breakpoints mobile)
            await page.set_viewport_size({"width": 1280, "height": 800})
            # networkidle garante que imagens e fontes carregaram
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            # aguarda o zoom por seção ser aplicado (sinalizado pelo print/page.tsx)
            await page.wait_for_selector(".print-ready", timeout=15_000)
            pdf_bytes = await page.pdf(
                width="297mm",
                height="210mm",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
            )
            await browser.close()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"ok": False, "error": f"PDF generation failed: {exc}"})

    filename = f"mapa-psiquico-{report_id[:8]}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
