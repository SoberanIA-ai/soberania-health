"""
Modelo de usuario para autenticación del dashboard.

Roles:
  recepcionista → acceso a pantallas operativas (autorizaciones, nueva auth)
  supervisor    → recepcionista + puede revisar HITL
  auditor       → solo lectura + acceso al panel AI Act
  admin         → acceso completo
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    rol: Mapped[str] = mapped_column(String(50), default="recepcionista")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)