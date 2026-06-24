import logging

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app = None


def init_firebase() -> None:
    """Inicializa Firebase Admin SDK como singleton.

    Se llama una sola vez desde el lifespan de FastAPI.
    También se inicializa automáticamente al importarse en Celery workers.
    """
    global _firebase_app

    if _firebase_app is not None:
        return

    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK inicializado correctamente")
        except Exception as exc:
            logger.error(
                "Error al inicializar Firebase Admin SDK: %s", exc, exc_info=True
            )
            raise
    else:
        _firebase_app = list(firebase_admin._apps.values())[0]
