from app.core.celery import celery_app

# Importar tareas para que Celery las registre
from app.tasks import alertas  # noqa: F401

if __name__ == "__main__":
    celery_app.start()
