import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mascota import Mascota
from app.schemas.mascota import MascotaRequest


class MascotaError(Exception):
    """Excepción para errores de mascota."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


async def crear_mascota(
    db: AsyncSession,
    usuario_id: int,
    datos: MascotaRequest,
) -> Mascota:
    """Crea una nueva mascota o reusa una existente con mismo nombre+especie."""
    existing = await db.execute(
        select(Mascota).where(
            Mascota.usuario_id == usuario_id,
            Mascota.nombre == datos.nombre,
            Mascota.especie == datos.especie,
        )
    )
    mascota = existing.scalar_one_or_none()
    if mascota is not None:
        return mascota

    # Generate unique codigo_emergencia (6-char hex, uppercase)
    while True:
        codigo = secrets.token_hex(3).upper()
        exists = await db.execute(
            select(Mascota).where(Mascota.codigo_emergencia == codigo)
        )
        if exists.scalar_one_or_none() is None:
            break

    mascota = Mascota(
        usuario_id=usuario_id,
        nombre=datos.nombre,
        especie=datos.especie,
        raza=datos.raza,
        color=datos.color,
        codigo_emergencia=codigo,
    )
    db.add(mascota)
    await db.flush()
    return mascota


async def obtener_mascota(
    db: AsyncSession,
    mascota_id: int,
) -> Mascota | None:
    return await db.get(Mascota, mascota_id)


async def listar_mascotas_por_usuario(
    db: AsyncSession,
    usuario_id: int,
) -> list[Mascota]:
    result = await db.execute(
        select(Mascota)
        .where(Mascota.usuario_id == usuario_id)
        .order_by(Mascota.created_at.desc())
    )
    return list(result.scalars().all())
