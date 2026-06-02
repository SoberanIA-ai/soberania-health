import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Autorizacion(Base):
    __tablename__ = "autorizaciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Orden médica
    orden_id: Mapped[str | None] = mapped_column(String(100))
    paciente_id: Mapped[str | None] = mapped_column(String(100))
    paciente_nombre: Mapped[str | None] = mapped_column(String(200))
    medico_id: Mapped[str | None] = mapped_column(String(100))
    medico_nombre: Mapped[str | None] = mapped_column(String(200))
    procedimiento_descripcion: Mapped[str | None] = mapped_column(Text)
    procedimiento_cie10: Mapped[str | None] = mapped_column(String(50))
    fecha_solicitud: Mapped[date | None] = mapped_column(Date)
    urgencia: Mapped[str] = mapped_column(String(20), default="normal")

    # Aseguradora
    aseguradora: Mapped[str | None] = mapped_column(String(50))
    poliza_numero: Mapped[str | None] = mapped_column(String(100))
    poliza_tipo: Mapped[str | None] = mapped_column(String(50))

    # Procesamiento
    procedimiento_codigo: Mapped[str | None] = mapped_column(String(50))
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    requiere_autorizacion: Mapped[bool | None] = mapped_column(Boolean)
    cobertura_verificada: Mapped[bool | None] = mapped_column(Boolean)

    # Estado
    estado: Mapped[str] = mapped_column(String(50), default="recibido")
    modo: Mapped[str] = mapped_column(String(10), default="real")

    # Solicitud enviada
    solicitud_enviada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    solicitud_referencia: Mapped[str | None] = mapped_column(String(100))

    # Respuesta aseguradora
    respuesta_recibida_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    numero_autorizacion: Mapped[str | None] = mapped_column(String(100))
    autorizado: Mapped[bool | None] = mapped_column(Boolean)
    motivo_denegacion: Mapped[str | None] = mapped_column(Text)

    # HITL
    hitl_requerido: Mapped[bool] = mapped_column(Boolean, default=False)
    razon_hitl: Mapped[str | None] = mapped_column(Text)
    hitl_revisado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hitl_revisor: Mapped[str | None] = mapped_column(String(100))
    hitl_decision: Mapped[str | None] = mapped_column(String(20))
    hitl_notas: Mapped[str | None] = mapped_column(Text)

    # Metadata
    raw_orden: Mapped[str | None] = mapped_column(Text)
    raw_respuesta: Mapped[str | None] = mapped_column(Text)


class CodigoAseguradora(Base):
    __tablename__ = "codigos_aseguradora"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    aseguradora: Mapped[str] = mapped_column(String(50), nullable=False)
    procedimiento_descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    cie10_codigo: Mapped[str | None] = mapped_column(String(50))
    aseguradora_codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=True)
    documentacion_requerida: Mapped[dict | None] = mapped_column(JSON)
    copago_euros: Mapped[float | None] = mapped_column(Numeric(8, 2))
    notas: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "idx_codigo_aseguradora",
            "aseguradora",
            "cie10_codigo",
            "version",
            unique=True,
            postgresql_where=(activo == True),  # noqa: E712
        ),
    )
