import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.alertas import router as alertas_router
from app.api.auth import router as auth_router
from app.api.mascotas import router as mascotas_router
from app.api.usuarios import router as usuarios_router
from app.api.ws import router as ws_router
from app.core.database import async_session_factory, create_tables
from app.core.firebase import init_firebase

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Inicializa servicios al arrancar, limpia al cerrar."""
    await create_tables()
    init_firebase()
    yield

app = FastAPI(
    title="Lost Friend API",
    description="Sistema de alerta geoespacial en cascada para mascotas perdidas",
    version="1.0.0",
    lifespan=lifespan,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all para errores no manejados — loggea y devuelve JSON."""
    logger.exception(
        "Unhandled error processing %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(mascotas_router)
app.include_router(alertas_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    """Health check que verifica conectividad con la base de datos."""
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "healthy", "checks": {"database": "ok"}}
    except Exception as exc:
        logger.error("Health check — DB not reachable: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "checks": {"database": "failed"}},
        )
