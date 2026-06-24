from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.usuario import Usuario


class AuthError(Exception):
    """Excepción para errores de autenticación."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


async def register(
    db: AsyncSession,
    correo: str,
    contrasena: str,
    nombre: str,
    telefono: str | None = None,
) -> dict:
    result = await db.execute(select(Usuario).where(Usuario.correo == correo))
    if result.scalar_one_or_none():
        raise AuthError("El correo ya está registrado", status_code=400)

    usuario = Usuario(
        correo=correo,
        contrasena_hash=hash_password(contrasena),
        nombre=nombre,
        telefono=telefono,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    token = create_access_token({"sub": str(usuario.id)})
    return {"access_token": token, "token_type": "bearer"}


async def login(
    db: AsyncSession,
    correo: str,
    contrasena: str,
) -> dict:
    result = await db.execute(select(Usuario).where(Usuario.correo == correo))
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(contrasena, usuario.contrasena_hash):
        raise AuthError("Credenciales inválidas", status_code=401)

    token = create_access_token({"sub": str(usuario.id)})
    return {"access_token": token, "token_type": "bearer"}
