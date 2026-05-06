"""Schemas Pydantic para los endpoints de autorizaciones."""
from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcesarAutorizacionRequest(BaseModel):
    orden_h17: str = Field(..., description="Mensaje HL7 v2 o texto libre de la orden médica")
    modo: Literal["real", "mock"] = "mock"


class AutorizacionResumenResponse(BaseModel):
    """Respuesta inmediata al POST procesar — devuelve los identificadores."""

    autorizacion_id: UUID
    estado: str
    confidence_score: Optional[float] = None
    numero_autorizacion: Optional[str] = None
    solicitud_referencia: Optional[str] = None
    hitl_requerido: bool = False

    model_config = ConfigDict(from_attributes=True)


class AutorizacionDetalleResponse(BaseModel):
    """Detalle completo de una autorización."""

    id: UUID
    created_at: datetime
    estado: str
    modo: str

    paciente_nombre: Optional[str] = None
    medico_nombre: Optional[str] = None
    procedimiento_descripcion: Optional[str] = None
    procedimiento_cie10: Optional[str] = None
    procedimiento_codigo: Optional[str] = None
    fecha_solicitud: Optional[date] = None
    urgencia: Optional[str] = None

    aseguradora: Optional[str] = None
    poliza_numero: Optional[str] = None
    poliza_tipo: Optional[str] = None

    confidence_score: Optional[float] = None
    requiere_autorizacion: Optional[bool] = None
    cobertura_verificada: Optional[bool] = None

    solicitud_enviada_at: Optional[datetime] = None
    solicitud_referencia: Optional[str] = None
    respuesta_recibida_at: Optional[datetime] = None
    numero_autorizacion: Optional[str] = None
    autorizado: Optional[bool] = None
    motivo_denegacion: Optional[str] = None

    hitl_requerido: bool = False
    hitl_revisado_at: Optional[datetime] = None
    hitl_revisor: Optional[str] = None
    hitl_decision: Optional[str] = None
    hitl_notas: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditEntryResponse(BaseModel):
    id: UUID
    timestamp: datetime
    accion: str
    actor: str
    resultado: Optional[str] = None
    confidence_score: Optional[float] = None
    modelo_usado: Optional[str] = None
    version_calculador: Optional[str] = None
    hitl_intervencion: bool = False
    hash_sha256: str
    hash_previo: Optional[str] = None
    datos_entrada: Optional[dict] = None
    datos_salida: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    autorizacion_id: UUID
    total_entries: int
    integro: bool
    entries: list[AuditEntryResponse]
    entries_invalidas: list[dict] = []
