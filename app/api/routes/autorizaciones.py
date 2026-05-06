"""Endpoints de autorizaciones — sec 12 del handoff."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.autorizacion import (
    AutorizacionDetalleResponse,
    AutorizacionResumenResponse,
    ProcesarAutorizacionRequest,
)
from app.models.database import get_db
from app.services.autorizacion_service import AutorizacionService

router = APIRouter(prefix="/autorizaciones", tags=["autorizaciones"])


@router.post(
    "/procesar",
    response_model=AutorizacionResumenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def procesar_autorizacion(
    payload: ProcesarAutorizacionRequest,
    db: Session = Depends(get_db),
):
    service = AutorizacionService(db)
    autorizacion = await service.procesar(payload.orden_h17, modo=payload.modo)

    return AutorizacionResumenResponse(
        autorizacion_id=autorizacion.id,
        estado=autorizacion.estado,
        confidence_score=float(autorizacion.confidence_score) if autorizacion.confidence_score is not None else None,
        numero_autorizacion=autorizacion.numero_autorizacion,
        solicitud_referencia=autorizacion.solicitud_referencia,
        hitl_requerido=autorizacion.hitl_requerido,
    )


@router.get("/pendientes", response_model=list[AutorizacionDetalleResponse])
async def listar_pendientes_hitl(db: Session = Depends(get_db)):
    service = AutorizacionService(db)
    return service.listar_pendientes_hitl()


@router.get("/{autorizacion_id}", response_model=AutorizacionDetalleResponse)
async def obtener_autorizacion(
    autorizacion_id: UUID,
    db: Session = Depends(get_db),
):
    service = AutorizacionService(db)
    autorizacion = service.obtener(autorizacion_id)
    if not autorizacion:
        raise HTTPException(status_code=404, detail="Autorización no encontrada")
    return autorizacion
