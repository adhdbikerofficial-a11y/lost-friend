import json
import logging

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app = None


def _load_firebase_credential() -> credentials.Certificate:
    """Carga credenciales de Firebase desde env var JSON o archivo."""
    if settings.firebase_credentials_json:
        logger.info("Cargando credenciales Firebase desde FIREBASE_CREDENTIALS_JSON")
        cred_dict = json.loads(settings.firebase_credentials_json)
        return credentials.Certificate(cred_dict)

    logger.info(
        "Cargando credenciales Firebase desde archivo: %s",
        settings.firebase_credentials_path,
    )
    return credentials.Certificate(settings.firebase_credentials_path)


def init_firebase() -> None:
    """Inicializa Firebase Admin SDK como singleton.

    Se llama una sola vez desde el lifespan de FastAPI.
    También se inicializa automáticamente al importarse en Celery workers.

    Las credenciales se toman de:
    1. ``FIREBASE_CREDENTIALS_JSON`` (env var) — ideal para Railway
    2. ``firebase_credentials_path`` (archivo) — para desarrollo local
    """
    global _firebase_app

    if _firebase_app is not None:
        return

    if not firebase_admin._apps:
        try:
            cred = _load_firebase_credential()
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK inicializado correctamente")
        except Exception as exc:
            logger.error(
                "Error al inicializar Firebase Admin SDK: %s", exc, exc_info=True
            )
            raise
    else:
        _firebase_app = list(firebase_admin._apps.values())[0]
