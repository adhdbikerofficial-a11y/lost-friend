import re

from pydantic import BaseModel, field_validator

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegistroRequest(BaseModel):
    correo: str
    contrasena: str
    nombre: str
    telefono: str | None = None

    @field_validator("correo")
    @classmethod
    def email_valido(cls, v: str) -> str:
        if not EMAIL_RE.match(v):
            raise ValueError("El formato del email no es válido")
        return v.lower().strip()

    @field_validator("contrasena")
    @classmethod
    def contrasena_segura(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class LoginRequest(BaseModel):
    correo: str
    contrasena: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
