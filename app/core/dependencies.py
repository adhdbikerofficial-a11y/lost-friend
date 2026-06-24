from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.autoridad import Autoridad
from app.models.usuario import Usuario

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: no contiene identificador de usuario",
        )

    usuario = await db.get(Usuario, int(usuario_id))
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    return usuario


async def get_current_authority(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Autoridad:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    if payload.get("tipo") != "autoridad":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere token de autoridad",
        )

    autoridad_id = payload.get("sub")
    if autoridad_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    autoridad = await db.get(Autoridad, int(autoridad_id))
    if autoridad is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autoridad no encontrada",
        )

    return autoridad


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple[int, bool]:
    """Return (actor_id, is_authority) para endpoints accesibles por usuario o autoridad.

    Decodifica el token y verifica que el sujeto exista en la tabla correspondiente
    según el campo ``tipo`` del JWT.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    actor_id = int(payload["sub"])
    is_authority = payload.get("tipo") == "autoridad"

    if is_authority:
        autoridad = await db.get(Autoridad, actor_id)
        if not autoridad:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autoridad no encontrada",
            )
    else:
        usuario = await db.get(Usuario, actor_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
            )

    return (actor_id, is_authority)
