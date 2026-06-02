"""Endpoint del audit log — sec 12 del handoff.

GET /api/v1/audit/{autorizacion_id}              audit log + verificación
GET /api/v1/audit/{autorizacion_id}/aiact-report reporte AI Act estructurado
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.autorizacion import AuditEntryResponse, AuditLogResponse
from app.api.routes.auth import get_usuario_actual
from app.models.autorizacion import Autorizacion
from app.models.database import get_db
from app.models.usuario import Usuario
from app.utils.audit_log import AuditLogger

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{autorizacion_id}", response_model=AuditLogResponse)
async def obtener_audit_log(
    autorizacion_id: UUID,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
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


def _tipo_actor(entry) -> str:
    """LLM, Python puro o humano — para distinción visual del reporte."""
    if entry.hitl_intervencion:
        return "hitl"
    modelo = (entry.modelo_usado or "").lower()
    if "mistral" in modelo or "nemo" in modelo or modelo.startswith("mock"):
        return "llm"
    return "python"


@router.get("/{autorizacion_id}/aiact-report")
async def aiact_report(
    autorizacion_id: UUID,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
) -> dict:
    """Reporte estructurado de trazabilidad AI Act listo para auditoría.

    Combina datos de la autorización + audit log + intervención humana
    en un único JSON con todos los campos requeridos por la regulación:
    explicabilidad (razon_decision), trazabilidad del modelo, integridad
    SHA256, intervención humana.
    """
    autorizacion = (
        db.query(Autorizacion).filter(Autorizacion.id == autorizacion_id).first()
    )
    if not autorizacion:
        raise HTTPException(status_code=404, detail="Autorización no encontrada")

    logger = AuditLogger(db)
    entries = logger.listar(str(autorizacion_id))
    integridad = logger.verificar_integridad(str(autorizacion_id))

    pasos = []
    for entry in entries:
        ds = entry.datos_salida or {}
        de = entry.datos_entrada or {}
        pasos.append(
            {
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "accion": entry.accion,
                "actor": entry.actor,
                "tipo": _tipo_actor(entry),
                "razon_decision": ds.get("razon_decision"),
                "modelo_version": ds.get("modelo_version") or entry.modelo_usado,
                "modo_inferencia": ds.get("modo_inferencia"),
                "confidence_score": (
                    float(entry.confidence_score)
                    if entry.confidence_score is not None
                    else None
                ),
                "datos_entrada": de,
                "datos_salida": ds,
                "hash_sha256": entry.hash_sha256,
                "hash_previo": entry.hash_previo,
                "hitl_intervencion": entry.hitl_intervencion,
            }
        )

    intervencion_humana = None
    hitl_entry = next(
        (e for e in entries if e.hitl_intervencion and e.actor.startswith("hitl_supervisor:")),
        None,
    )
    if hitl_entry and hitl_entry.datos_salida:
        ds = hitl_entry.datos_salida
        intervencion_humana = {
            "revisor": ds.get("revisor_nombre"),
            "decision": ds.get("decision_humana"),
            "coincide_con_agente": ds.get("coincide_con_agente"),
            "notas": ds.get("notas_revisor"),
            "tiempo_en_cola_segundos": ds.get("tiempo_en_cola_segundos"),
            "timestamp": hitl_entry.timestamp.isoformat() if hitl_entry.timestamp else None,
        }

    # Tiempo total: desde primera a última entry del audit
    tiempo_total = None
    if len(entries) >= 2:
        primer = entries[0].timestamp
        ultimo = entries[-1].timestamp
        if primer and ultimo:
            tiempo_total = round((ultimo - primer).total_seconds(), 2)

    return {
        "autorizacion": {
            "id": str(autorizacion.id),
            "created_at": autorizacion.created_at.isoformat() if autorizacion.created_at else None,
            "estado_final": autorizacion.estado,
            "modo": autorizacion.modo,
            "paciente_nombre": autorizacion.paciente_nombre,
            "medico_nombre": autorizacion.medico_nombre,
            "aseguradora": autorizacion.aseguradora,
            "poliza_tipo": autorizacion.poliza_tipo,
            "poliza_numero": autorizacion.poliza_numero,
            "procedimiento_descripcion": autorizacion.procedimiento_descripcion,
            "procedimiento_cie10": autorizacion.procedimiento_cie10,
            "procedimiento_codigo": autorizacion.procedimiento_codigo,
            "confidence_score": (
                float(autorizacion.confidence_score)
                if autorizacion.confidence_score is not None
                else None
            ),
            "numero_autorizacion": autorizacion.numero_autorizacion,
            "tiempo_total_segundos": tiempo_total,
        },
        "audit": {
            "integro": integridad["integro"],
            "total_pasos": integridad["total_entries"],
            "entries_invalidas": integridad["entries_invalidas"],
            "pasos": pasos,
        },
        "intervencion_humana": intervencion_humana,
        "compliance": {
            "ai_act": "compliant" if integridad["integro"] else "comprometida",
            "calculadores_version": "1.0.0-simulado",
            "data_status": "SIMULADO",
        },
    }
