from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import LoginRequest, RegistroRequest, TokenResponse
from app.services.auth_service import AuthError, login, login_autoridad, register

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registro", response_model=TokenResponse)
async def registro_endpoint(
    data: RegistroRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await register(
            db=db,
            correo=data.correo,
            contrasena=data.contrasena,
            nombre=data.nombre,
            telefono=data.telefono,
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await login(db=db, correo=data.correo, contrasena=data.contrasena)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/login-autoridad", response_model=TokenResponse)
async def login_autoridad_endpoint(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await login_autoridad(
            db=db, email=data.correo, contrasena=data.contrasena
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
