from geoalchemy2 import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alerta import Alerta
from app.schemas.alerta import AlertaRequest
from app.services.mascota_service import crear_mascota
from app.tasks.alertas import expandir_radio, notificar_radio_inicial


class AlertaError(Exception):
    """Excepción para errores de alerta."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


async def crear_alerta(
    db: AsyncSession,
    usuario_id: int,
    datos: AlertaRequest,
) -> dict:
    """Crea una alerta para una mascota perdida.

    Steps:
      1. Create or reuse mascota
      2. Build WKT geometry point
      3. Create Alerta with ubicacion
      4. Commit transaction
      5. Enqueue Celery task for cascade expansion
    """
    # 1. Create or reuse mascota
    mascota = await crear_mascota(db=db, usuario_id=usuario_id, datos=datos.mascota)

    # 2. Build geometry
    wkt_element = WKTElement(
        f"POINT({datos.ubicacion.lon} {datos.ubicacion.lat})",
        srid=4326,
    )

    # 3. Create alerta
    alerta = Alerta(
        mascota_id=mascota.id,
        usuario_id=usuario_id,
        ubicacion=wkt_element,
        descripcion=datos.descripcion,
    )
    db.add(alerta)

    # 4. Commit
    await db.commit()
    await db.refresh(alerta)

    # 5. Enqueue Celery task — AFTER commit, with initial countdown
    expandir_radio.apply_async(
        args=[alerta.id],
        countdown=settings.alert_expand_5km_minutes * 60,
    )

    # 6. Enqueue notification for 1km radius — inmediata, en Celery worker
    notificar_radio_inicial.apply_async(args=[alerta.id], countdown=0)

    return {
        "alerta_id": alerta.id,
        "estado": alerta.estado,
        "radio_actual_km": alerta.radio_actual_km,
        "mascota_id": mascota.id,
        "codigo_emergencia": mascota.codigo_emergencia,
        "created_at": alerta.created_at,
    }


async def listar_alertas_activas_service(
    db: AsyncSession,
) -> list[dict]:
    """Lista alertas activas (no resueltas) con coordenadas y datos de mascota.

    Extrae lat/lon de la geometría PostGIS usando ST_X/ST_Y a nivel SQL
    para evitar tener que decodificar WKBElement en Python.
    """
    from sqlalchemy import func, select

    from app.models.mascota import Mascota

    query = (
        select(
            Alerta,
            Mascota.nombre.label("mascota_nombre"),
            Mascota.especie.label("mascota_especie"),
            func.ST_X(Alerta.ubicacion).label("lon"),
            func.ST_Y(Alerta.ubicacion).label("lat"),
        )
        .join(Mascota, Alerta.mascota_id == Mascota.id)
        .where(Alerta.estado != "RESUELTA")
        .order_by(Alerta.created_at.desc())
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "alerta_id": row[0].id,
            "mascota_id": row[0].mascota_id,
            "estado": row[0].estado,
            "radio_actual_km": row[0].radio_actual_km,
            "lat": float(row.lat),
            "lon": float(row.lon),
            "descripcion": row[0].descripcion,
            "created_at": row[0].created_at,
            "mascota_nombre": row.mascota_nombre,
            "mascota_especie": row.mascota_especie,
        }
        for row in rows
    ]
