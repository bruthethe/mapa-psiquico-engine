"""Engine asyncpg + session factory + dependency FastAPI."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://astro:astro@localhost:5432/astro")
    # asyncpg exige o scheme postgresql+asyncpg://
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


DATABASE_URL = _database_url()

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_tables() -> None:
    """Cria todas as tabelas se não existirem (idempotente).

    Uso: startup da aplicação em dev. Em produção, usar `alembic upgrade head`.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency FastAPI: entrega AsyncSession e fecha ao final da request."""
    async with AsyncSessionLocal() as session:
        yield session
