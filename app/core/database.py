from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_tables() -> None:
    """Crea todas las tablas definidas en los modelos ORM si no existen."""
    # Import all models so they register in Base.metadata
    import app.models.alerta  # noqa: F401
    import app.models.autoridad  # noqa: F401
    import app.models.mascota  # noqa: F401
    import app.models.usuario  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession]:  # type: ignore[return-type]
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
