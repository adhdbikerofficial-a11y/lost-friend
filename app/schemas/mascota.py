from datetime import datetime

from pydantic import BaseModel


class MascotaRequest(BaseModel):
    nombre: str
    especie: str
    raza: str | None = None
    color: str | None = None


class MascotaResponse(BaseModel):
    id: int
    nombre: str
    especie: str
    raza: str | None = None
    color: str | None = None
    codigo_emergencia: str
    created_at: datetime

    model_config = {"from_attributes": True}
