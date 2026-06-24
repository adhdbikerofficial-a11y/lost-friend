from datetime import datetime

from pydantic import BaseModel, field_validator


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

    @field_validator("lat")
    @classmethod
    def lat_en_rango(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError(f"lat debe estar entre -90 y 90, got {v}")
        return v

    @field_validator("lon")
    @classmethod
    def lon_en_rango(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError(f"lon debe estar entre -180 y 180, got {v}")
        return v


class FCMTokenUpdate(BaseModel):
    fcm_token: str
