from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    correo: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ubicacion: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    mascotas: Mapped[list["Mascota"]] = relationship(
        "Mascota", back_populates="usuario"
    )
