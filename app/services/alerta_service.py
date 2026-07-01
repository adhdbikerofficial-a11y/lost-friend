from datetime import datetime, timezone

from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.core.config import settings
from app.models.alerta import Alerta
from app.schemas.alerta import AlertaRequest
from app.services.mascota_service import crear_mascota
from app.tasks.alertas import expandir_radio, notificar_radio_inicial

logger = logging.getLogger(__name__)


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
    try:
        expandir_radio.apply_async(
            args=[alerta.id],
            countdown=settings.alert_expand_5km_minutes * 60,
        )
    except Exception as exc:
        logger.error(
            "Failed to schedule expandir_radio for alerta %s: %s",
            alerta.id,
            exc,
        )
        # TODO: background job should retry scheduling for pending alerts

    # 6. Enqueue notification for 1km radius — inmediata, en Celery worker
    try:
        notificar_radio_inicial.apply_async(args=[alerta.id], countdown=0)
    except Exception as exc:
        logger.error(
            "Failed to schedule notificar_radio_inicial for alerta %s: %s",
            alerta.id,
            exc,
        )
        # TODO: background job should retry scheduling for pending alerts

    # 7. Broadcast alerta en tiempo real a autoridades conectadas vía WebSocket
    from app.services.websocket_manager import manager

    await manager.broadcast(
        {
            "type": "nueva_alerta",
            "alerta_id": alerta.id,
            "mascota_id": mascota.id,
            "estado": alerta.estado,
            "radio_actual_km": alerta.radio_actual_km,
            "lat": datos.ubicacion.lat,
            "lon": datos.ubicacion.lon,
            "descripcion": alerta.descripcion,
            "created_at": str(alerta.created_at),
            "mascota_nombre": mascota.nombre,
            "mascota_especie": mascota.especie,
        }
    )

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
        .where(Alerta.estado.notin_(["RESUELTA", "CANCELADA"]))
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


async def resolver_alerta(
    db: AsyncSession,
    alerta_id: int,
    usuario_id: int,
    es_autoridad: bool = False,
) -> dict:
    """Marca una alerta como resuelta.

    Solo el dueño de la alerta o una autoridad puede resolverla.
    """
    result = await db.execute(select(Alerta).where(Alerta.id == alerta_id))
    alerta = result.scalar_one_or_none()

    if alerta is None:
        raise AlertaError("Alerta no encontrada", status_code=404)

    if alerta.usuario_id != usuario_id and not es_autoridad:
        raise AlertaError(
            "No tenés permiso para resolver esta alerta", status_code=403
        )

    if alerta.estado == "RESUELTA":
        raise AlertaError("La alerta ya está resuelta", status_code=400)

    ahora = datetime.now(timezone.utc)
    alerta.estado = "RESUELTA"
    alerta.resuelta_en = ahora
    await db.commit()
    await db.refresh(alerta)

    from app.services.websocket_manager import manager

    await manager.broadcast(
        {
            "type": "alerta_resuelta",
            "alerta_id": alerta.id,
        }
    )

    return {
        "alerta_id": alerta.id,
        "estado": alerta.estado,
        "resuelta_en": str(alerta.resuelta_en),
    }


async def cancelar_alerta(
    db: AsyncSession,
    alerta_id: int,
    usuario_id: int,
) -> dict:
    """Cancela una alerta (solo el dueño).

    A diferencia de resolver, cancelar implica que la mascota
    nunca estuvo perdida o se encontró antes de activar la alerta.
    """
    result = await db.execute(select(Alerta).where(Alerta.id == alerta_id))
    alerta = result.scalar_one_or_none()

    if alerta is None:
        raise AlertaError("Alerta no encontrada", status_code=404)

    if alerta.usuario_id != usuario_id:
        raise AlertaError(
            "Solo el dueño de la alerta puede cancelarla", status_code=403
        )

    if alerta.estado in ("RESUELTA", "CANCELADA"):
        raise AlertaError(
            f"La alerta ya está {alerta.estado.lower()}", status_code=400
        )

    ahora = datetime.now(timezone.utc)
    alerta.estado = "CANCELADA"
    alerta.resuelta_en = ahora
    await db.commit()
    await db.refresh(alerta)

    from app.services.websocket_manager import manager

    await manager.broadcast(
        {
            "type": "alerta_cancelada",
            "alerta_id": alerta.id,
        }
    )

    return {
        "alerta_id": alerta.id,
        "estado": alerta.estado,
        "resuelta_en": str(alerta.resuelta_en),
    }
