from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import create_tables
from app.routers.reports import router as reports_router
from app.routers.test_form import router as test_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_tables()
        logger.info("Tabelas verificadas/criadas com sucesso.")
    except Exception as exc:
        logger.warning("Banco indisponível no startup: %s", exc)
    yield


app = FastAPI(
    title="Esoteric Calculation Engine API",
    version="0.1.0",
    description="Astronomical and esoteric calculation engine.",
    lifespan=lifespan,
)

app.include_router(reports_router)
app.include_router(test_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
