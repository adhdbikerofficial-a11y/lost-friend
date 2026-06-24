import logging

from firebase_admin import messaging

from app.core.firebase import init_firebase

logger = logging.getLogger(__name__)


def enviar_push(
    tokens: list[str],
    titulo: str,
    cuerpo: str,
    data: dict | None = None,
) -> dict:
    """Envía una notificación push multicast vía FCM.

    Todos los tokens se envían en una sola llamada multicast.
    Se ejecuta en Celery worker (sync).
    """
    if not tokens:
        logger.warning("enviar_push llamada sin tokens — no se envía nada")
        return {"success": 0, "failure": 0}

    # Asegura que Firebase esté inicializado (singleton)
    init_firebase()

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=titulo,
            body=cuerpo,
        ),
        data=data or {},
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)
    logger.info(
        "Push enviado: %d success, %d failure de %d tokens",
        response.success_count,
        response.failure_count,
        len(tokens),
    )

    return {
        "success": response.success_count,
        "failure": response.failure_count,
    }
