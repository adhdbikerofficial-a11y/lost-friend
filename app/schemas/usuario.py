from datetime import datetime

from pydantic import BaseModel


class UsuarioResponse(BaseModel):
    id: int
    correo: str
    nombre: str
    telefono: str | None = None
    fcm_token: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UbicacionUpdate(BaseModel):
    lat: float
    lon: float


class FCMTokenUpdate(BaseModel):
    fcm_token: str
