"""Endpoint del audit log — sec 12 del handoff.

GET /api/v1/audit/{autorizacion_id} devuelve el audit log completo
con verificación de integridad (hashes SHA256 encadenados).
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.autorizacion import AuditEntryResponse, AuditLogResponse
from app.models.database import get_db
from app.utils.audit_log import AuditLogger

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{autorizacion_id}", response_model=AuditLogResponse)
async def obtener_audit_log(
    autorizacion_id: UUID,
    db: Session = Depends(get_db),
):
    """Devuelve el audit log de una autorización con verificación de integridad.

    Si algún hash no coincide → integro=False y entries_invalidas detalla
    cuáles fueron manipuladas.
    """
    logger = AuditLogger(db)
    entries = logger.listar(str(autorizacion_id))
    integridad = logger.verificar_integridad(str(autorizacion_id))

    return AuditLogResponse(
        autorizacion_id=autorizacion_id,
        total_entries=integridad["total_entries"],
        integro=integridad["integro"],
        entries=[AuditEntryResponse.model_validate(e) for e in entries],
        entries_invalidas=integridad["entries_invalidas"],
    )
