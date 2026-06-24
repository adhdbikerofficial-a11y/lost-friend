from pydantic import BaseModel


class RegistroRequest(BaseModel):
    correo: str
    contrasena: str
    nombre: str
    telefono: str | None = None


class LoginRequest(BaseModel):
    correo: str
    contrasena: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
