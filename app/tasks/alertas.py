import logging

from geoalchemy2 import Geography
from sqlalchemy import cast, create_engine, func
from sqlalchemy.orm import Session

from app.core.celery import celery_app
from app.core.config import settings
from app.models.alerta import Alerta
from app.models.usuario import Usuario
from app.services.notificacion_service import enviar_push

logger = logging.getLogger(__name__)


def _sync_database_url() -> str:
    """Deriva la URL de BD síncrona desde la URL (con o sin driver async)."""
    url = settings.database_url
    if "+asyncpg" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


# Engine compartido a nivel módulo — se crea una vez por worker
_sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True)


def _notificar_usuarios_en_radio(
    session: Session,
    alerta: Alerta,
    radio_km: int,
) -> None:
    """Consulta usuarios con ST_DWithin dentro del radio y les envía push.

    Todos los tokens se obtienen en UNA SOLA consulta (no loops).
    Usa ST_DWithin con cast a geography para distancia en metros.
    """
    tokens_rows = session.query(Usuario.fcm_token).filter(
        Usuario.fcm_token.isnot(None),
        Usuario.ubicacion.isnot(None),
        func.ST_DWithin(
            cast(Usuario.ubicacion, Geography),
            func.ST_GeogFromWKB(alerta.ubicacion),
            radio_km * 1000,  # km → metros
        ),
    ).all()

    tokens = [row[0] for row in tokens_rows if row[0]]
    if not tokens:
        logger.info(
            "Alerta %s: sin usuarios con FCM token en %dkm",
            alerta.id,
            radio_km,
        )
        return

    enviar_push(
        tokens=tokens,
        titulo="🐾 Mascota perdida cerca de ti",
        cuerpo=(
            f"Se reportó una mascota perdida a menos de {radio_km}km "
            f"de tu ubicación. Ayuda a encontrarla."
        ),
        data={
            "alerta_id": str(alerta.id),
            "radio_km": str(radio_km),
            "tipo": "expansion",
        },
    )


@celery_app.task(
    acks_late=True,
    max_retries=3,
    default_retry_delay=60,
)
def expandir_radio(alerta_id: int) -> None:
    """Expande el radio de una alerta según su estado actual.

    State machine:
      ACTIVA_1KM  → ACTIVA_5KM  (+ notifica a usuarios en 5km)
      ACTIVA_5KM  → ACTIVA_10KM (+ notifica a usuarios en 10km)
      ACTIVA_10KM / RESUELTA / CANCELADA → no-op
    """
    try:
        with Session(_sync_engine) as session:
            alerta = session.get(Alerta, alerta_id)
            if alerta is None:
                logger.warning("Alerta %s no encontrada", alerta_id)
                return

            if alerta.estado == "ACTIVA_1KM":
                alerta.estado = "ACTIVA_5KM"
                alerta.radio_actual_km = 5
                alerta.expandida_5km_en = func.now()
                session.commit()

                # Notificar a usuarios en el nuevo radio (5km)
                _notificar_usuarios_en_radio(session, alerta, 5)

                # Schedule next expansion (5KM → 10KM)
                countdown = (
                    settings.alert_expand_10km_minutes
                    - settings.alert_expand_5km_minutes
                ) * 60
                expandir_radio.apply_async(
                    args=[alerta_id], countdown=countdown
                )

            elif alerta.estado == "ACTIVA_5KM":
                alerta.estado = "ACTIVA_10KM"
                alerta.radio_actual_km = 10
                alerta.expandida_10km_en = func.now()
                session.commit()

                # Notificar a usuarios en el nuevo radio (10km)
                _notificar_usuarios_en_radio(session, alerta, 10)
                # Terminal state — no further expansion

            # ACTIVA_10KM, RESUELTA, CANCELADA → no-op

    except Exception as exc:
        logger.error(
            "Error expandiendo alerta %s: %s", alerta_id, exc, exc_info=True
        )
        raise expandir_radio.retry(exc=exc)


@celery_app.task(acks_late=True, max_retries=3, default_retry_delay=60)
def notificar_radio_inicial(alerta_id: int) -> None:
    """Envía notificación push inicial a usuarios dentro de 1km.

    Se encola inmediatamente al crear una alerta.
    Corre en Celery worker (no bloquea el event loop de FastAPI).
    """
    try:
        with Session(_sync_engine) as session:
            alerta = session.get(Alerta, alerta_id)
            if alerta is None:
                logger.warning(
                    "notificar_radio_inicial: alerta %s no encontrada",
                    alerta_id,
                )
                return

            _notificar_usuarios_en_radio(session, alerta, 1)

    except Exception as exc:
        logger.error(
            "Error en notificación inicial alerta %s: %s",
            alerta_id,
            exc,
            exc_info=True,
        )
        raise notificar_radio_inicial.retry(exc=exc)
