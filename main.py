from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.alertas import router as alertas_router
from app.api.auth import router as auth_router
from app.api.mascotas import router as mascotas_router
from app.api.usuarios import router as usuarios_router
from app.api.ws import router as ws_router
from app.core.database import create_tables
from app.core.firebase import init_firebase


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

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(mascotas_router)
app.include_router(alertas_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
