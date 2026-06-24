from datetime import datetime

from pydantic import BaseModel, field_validator

ESPECIES_VALIDAS = {"perro", "gato", "conejo", "ave", "otro"}


class MascotaRequest(BaseModel):
    nombre: str
    especie: str
    raza: str | None = None
    color: str | None = None

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre de la mascota no puede estar vacío")
        return v.strip()

    @field_validator("especie")
    @classmethod
    def especie_valida(cls, v: str) -> str:
        if v.lower() not in ESPECIES_VALIDAS:
            raise ValueError(
                f"Especie no válida: {v}. Válidas: {', '.join(sorted(ESPECIES_VALIDAS))}"
            )
        return v.lower()


class MascotaResponse(BaseModel):
    id: int
    nombre: str
    especie: str
    raza: str | None = None
    color: str | None = None
    codigo_emergencia: str
    created_at: datetime

    model_config = {"from_attributes": True}
