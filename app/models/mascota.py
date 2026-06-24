from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Mascota(Base):
    __tablename__ = "mascotas"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    especie: Mapped[str] = mapped_column(String(100), nullable=False)
    raza: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    senas_particulares: Mapped[str | None] = mapped_column(Text, nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    codigo_emergencia: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    usuario = relationship("Usuario", back_populates="mascotas")
