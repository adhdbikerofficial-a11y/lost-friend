from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import FCMTokenUpdate, UbicacionUpdate, UsuarioResponse
from app.services.usuario_service import (
    UserError,
    update_fcm_token,
    update_ubicacion,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/yo", response_model=UsuarioResponse)
async def obtener_perfil(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    return usuario


@router.put("/yo/ubicacion", response_model=UsuarioResponse)
async def actualizar_ubicacion(
    data: UbicacionUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    try:
        return await update_ubicacion(
            db=db,
            usuario_id=usuario.id,
            lat=data.lat,
            lon=data.lon,
        )
    except UserError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/yo/fcm-token", response_model=UsuarioResponse)
async def actualizar_fcm_token(
    data: FCMTokenUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    try:
        return await update_fcm_token(
            db=db,
            usuario_id=usuario.id,
            fcm_token=data.fcm_token,
        )
    except UserError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
