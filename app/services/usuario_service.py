from geoalchemy2 import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario


class UserError(Exception):
    """Excepción para errores de usuario."""

    def __init__(self, detail: str, status_code: int = 404):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


async def get_usuario(db: AsyncSession, usuario_id: int) -> Usuario | None:
    return await db.get(Usuario, usuario_id)


async def update_ubicacion(
    db: AsyncSession,
    usuario_id: int,
    lat: float,
    lon: float,
) -> Usuario:
    usuario = await db.get(Usuario, usuario_id)
    if usuario is None:
        raise UserError("Usuario no encontrado", status_code=404)

    usuario.ubicacion = WKTElement(f"POINT({lon} {lat})", srid=4326)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def update_fcm_token(
    db: AsyncSession,
    usuario_id: int,
    fcm_token: str,
) -> Usuario:
    usuario = await db.get(Usuario, usuario_id)
    if usuario is None:
        raise UserError("Usuario no encontrado", status_code=404)

    usuario.fcm_token = fcm_token
    await db.commit()
    await db.refresh(usuario)
    return usuario
