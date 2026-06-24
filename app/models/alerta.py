from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    mascota_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mascotas.id"), nullable=False, index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVA_1KM"
    )
    radio_actual_km: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    ubicacion: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326), nullable=False
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    expandida_5km_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expandida_10km_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resuelta_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
