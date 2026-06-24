from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.mascota import MascotaRequest


class UbicacionSchema(BaseModel):
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


class AlertaRequest(BaseModel):
    mascota: MascotaRequest
    ubicacion: UbicacionSchema
    descripcion: str | None = None


class AlertaResponse(BaseModel):
    alerta_id: int
    estado: str
    radio_actual_km: int
    mascota_id: int
    codigo_emergencia: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertaActivaResponse(BaseModel):
    """Alerta activa (no resuelta) con coordenadas y datos de mascota."""

    alerta_id: int
    mascota_id: int
    estado: str
    radio_actual_km: int
    lat: float
    lon: float
    descripcion: str | None = None
    created_at: datetime
    mascota_nombre: str
    mascota_especie: str

    model_config = {"from_attributes": True}


class ResolveAlertResponse(BaseModel):
    """Respuesta de resolver o cancelar una alerta."""

    alerta_id: int
    estado: str
    resuelta_en: str
