from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_actor, get_current_user
from app.models.usuario import Usuario
from app.schemas.alerta import AlertaActivaResponse, AlertaRequest, AlertaResponse
from app.services.alerta_service import (
    AlertaError,
    cancelar_alerta,
    crear_alerta,
    listar_alertas_activas_service,
    resolver_alerta,
)

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.post("", response_model=AlertaResponse, status_code=201)
async def crear_alerta_endpoint(
    data: AlertaRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        return await crear_alerta(db=db, usuario_id=usuario.id, datos=data)
    except AlertaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/activas", response_model=list[AlertaActivaResponse])
async def listar_alertas_activas_endpoint(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Lista todas las alertas activas (no resueltas) con coordenadas y datos de mascota."""
    return await listar_alertas_activas_service(db=db)


@router.put("/{alerta_id}/resolver")
async def resolver_alerta_endpoint(
    alerta_id: int,
    db: AsyncSession = Depends(get_db),
    actor: tuple[int, bool] = Depends(get_current_actor),
):
    """Marca una alerta como resuelta.

    Accesible por el dueño de la alerta (JWT ciudadano) o por una autoridad (JWT autoridad).
    """
    actor_id, es_autoridad = actor
    try:
        return await resolver_alerta(
            db=db,
            alerta_id=alerta_id,
            usuario_id=actor_id,
            es_autoridad=es_autoridad,
        )
    except AlertaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{alerta_id}/cancelar")
async def cancelar_alerta_endpoint(
    alerta_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Cancela una alerta propia (solo el dueño).

    Usa JWT de ciudadano — las autoridades no pueden cancelar alertas ajenas.
    """
    try:
        return await cancelar_alerta(
            db=db,
            alerta_id=alerta_id,
            usuario_id=usuario.id,
        )
    except AlertaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
