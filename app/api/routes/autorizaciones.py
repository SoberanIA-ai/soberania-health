"""Endpoints de autorizaciones — sec 12 del handoff."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.autorizacion import (
    AutorizacionDetalleResponse,
    AutorizacionResumenResponse,
    HitlDecisionRequest,
    ProcesarAutorizacionRequest,
    ReenviarRequest,
)
from app.api.routes.auth import get_usuario_actual
from app.models.database import get_db
from app.models.usuario import Usuario
from app.services.autorizacion_service import AutorizacionService, HitlDecisionError

router = APIRouter(prefix="/autorizaciones", tags=["autorizaciones"])

_ROLES_HITL = {"supervisor", "admin"}


@router.post(
    "/procesar",
    response_model=AutorizacionResumenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def procesar_autorizacion(
    payload: ProcesarAutorizacionRequest,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
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
async def listar_pendientes_hitl(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
):
    service = AutorizacionService(db)
    return service.listar_pendientes_hitl()


@router.get("/", response_model=list[AutorizacionDetalleResponse])
async def listar_todas(
    limit: int = 200,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
):
    """Lista TODAS las autorizaciones (para vista Auditoría AI Act)."""
    service = AutorizacionService(db)
    return service.listar_todas(limit=limit)


@router.get("/metricas")
async def obtener_metricas(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
) -> dict:
    """Métricas agregadas para el dashboard."""
    service = AutorizacionService(db)
    return service.metricas()


@router.get("/metricas-aiact")
async def obtener_metricas_aiact(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
) -> dict:
    """Métricas de compliance AI Act para la pestaña de auditoría.

    - porcentaje_supervision_humana: % autorizaciones que pasaron por HITL
    - porcentaje_contradicciones: % donde el humano contradijo al agente
    - tiempo_medio_revision_segundos: media del tiempo en cola HITL
    """
    from sqlalchemy import text as sql_text

    service = AutorizacionService(db)
    base = service.metricas()
    total = base["total"]

    # Buscamos en audit_log las entradas hitl_intervencion=True que persisten
    # los campos coincide_con_agente y tiempo_en_cola_segundos en datos_salida.
    rows = db.execute(
        sql_text(
            "SELECT datos_salida FROM audit_log "
            "WHERE hitl_intervencion = TRUE AND actor LIKE 'hitl_supervisor:%'"
        )
    ).fetchall()

    decisiones_humanas = [r[0] for r in rows if r[0]]
    contradicciones = sum(
        1 for d in decisiones_humanas if d.get("coincide_con_agente") is False
    )
    tiempos = [
        d.get("tiempo_en_cola_segundos")
        for d in decisiones_humanas
        if d.get("tiempo_en_cola_segundos") is not None
    ]
    tiempo_medio = sum(tiempos) / len(tiempos) if tiempos else None

    return {
        "total_autorizaciones": total,
        "con_supervision_humana": base["con_hitl"],
        "porcentaje_supervision": (base["con_hitl"] / total) if total else 0.0,
        "decisiones_humanas_registradas": len(decisiones_humanas),
        "humano_contradijo_agente": contradicciones,
        "porcentaje_contradicciones": (
            contradicciones / len(decisiones_humanas) if decisiones_humanas else 0.0
        ),
        "tiempo_medio_revision_segundos": tiempo_medio,
    }


@router.get("/{autorizacion_id}", response_model=AutorizacionDetalleResponse)
async def obtener_autorizacion(
    autorizacion_id: UUID,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
):
    service = AutorizacionService(db)
    autorizacion = service.obtener(autorizacion_id)
    if not autorizacion:
        raise HTTPException(status_code=404, detail="Autorización no encontrada")
    return autorizacion


@router.post("/{autorizacion_id}/hitl", response_model=AutorizacionDetalleResponse)
async def aplicar_decision_hitl(
    autorizacion_id: UUID,
    payload: HitlDecisionRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Registra la decisión humana (aprobar / rechazar / mas_info) de una
    autorización en cola HITL.

    Audit log registra la intervención humana con hash encadenado.
    """
    if usuario.rol not in _ROLES_HITL:
        raise HTTPException(status_code=403, detail="Solo supervisores y administradores pueden resolver casos HITL")
    service = AutorizacionService(db)
    try:
        return service.aplicar_decision_hitl(
            autorizacion_id=autorizacion_id,
            decision=payload.decision,
            revisor=payload.revisor,
            notas=payload.notas,
        )
    except HitlDecisionError as exc:
        codigo = str(exc)
        if codigo == "autorizacion_no_encontrada":
            raise HTTPException(status_code=404, detail=codigo)
        if codigo == "ya_decidido":
            raise HTTPException(status_code=409, detail=codigo)
        raise HTTPException(status_code=400, detail=codigo)


@router.post("/{autorizacion_id}/reenviar", response_model=AutorizacionDetalleResponse)
async def reenviar_con_documentacion(
    autorizacion_id: UUID,
    payload: ReenviarRequest,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
):
    """Reenvía al agente una autorización en estado informacion_adicional_requerida.

    La recepcionista o el médico aportan la documentación solicitada por el
    supervisor; el agente reprocesa el caso sobre el mismo registro.
    """
    service = AutorizacionService(db)
    try:
        return await service.reenviar_con_documentacion(
            autorizacion_id=autorizacion_id,
            notas_adicionales=payload.notas_adicionales,
            archivos_adjuntos=payload.archivos_adjuntos,
        )
    except HitlDecisionError as exc:
        codigo = str(exc)
        if codigo == "autorizacion_no_encontrada":
            raise HTTPException(status_code=404, detail=codigo)
        raise HTTPException(status_code=400, detail=codigo)
