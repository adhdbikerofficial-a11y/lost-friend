from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.mascota import MascotaResponse
from app.services.mascota_service import listar_mascotas_por_usuario

router = APIRouter(prefix="/mascotas", tags=["mascotas"])


@router.get("", response_model=list[MascotaResponse])
async def obtener_mascotas(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[MascotaResponse]:
    """Lista todas las mascotas registradas del usuario autenticado."""
    return await listar_mascotas_por_usuario(db, usuario.id)
