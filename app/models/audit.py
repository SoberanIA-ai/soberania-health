import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    autorizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("autorizaciones.id")
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Acción
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    resultado: Mapped[str | None] = mapped_column(String(50))

    # Datos
    datos_entrada: Mapped[dict | None] = mapped_column(JSON)
    datos_salida: Mapped[dict | None] = mapped_column(JSON)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 4))

    # Integridad — encadenado SHA256
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    hash_previo: Mapped[str | None] = mapped_column(String(64))

    # AI Act
    modelo_usado: Mapped[str | None] = mapped_column(String(100))
    version_calculador: Mapped[str | None] = mapped_column(String(20))
    hitl_intervencion: Mapped[bool] = mapped_column(Boolean, default=False)
