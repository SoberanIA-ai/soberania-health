"""AutorizacionService — orquesta el flujo completo end-to-end.

Responsabilidades:
1. Crear fila Autorizacion en DB con UUID nuevo
2. Invocar el grafo LangGraph pasando autorizacion_id en el state
3. Persistir audit_entries con SHA256 encadenado (sec 10)
4. Actualizar la fila con el resultado final

Esta es la única forma "production" de procesar una autorización —
el grafo en sí es una caja de cómputo, este servicio es el que toca DB.
"""
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent.graph import get_grafo
from app.models.autorizacion import Autorizacion
from app.utils.audit_log import AuditLogger


class AutorizacionService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_logger = AuditLogger(db)

    async def procesar(self, orden_raw: str, modo: str = "mock") -> Autorizacion:
        # 1. Crear fila Autorizacion en estado "recibido"
        autorizacion = Autorizacion(
            modo=modo,
            estado="recibido",
            raw_orden=orden_raw,
        )
        self.db.add(autorizacion)
        self.db.flush()  # asigna id sin commit

        autorizacion_id_str = str(autorizacion.id)

        # 2. Invocar el grafo
        grafo = get_grafo()
        final = await grafo.ainvoke(
            {
                "orden_raw": orden_raw,
                "modo": modo,
                "autorizacion_id": autorizacion_id_str,
            }
        )

        # 3. Persistir audit con SHA256 encadenado
        entries = final.get("audit_entries") or []
        self.audit_logger.persistir_cadena(autorizacion_id_str, entries)

        # 4. Actualizar fila con resultado
        self._aplicar_resultado(autorizacion, final)
        self.db.commit()
        self.db.refresh(autorizacion)
        return autorizacion

    def obtener(self, autorizacion_id: UUID | str) -> Autorizacion | None:
        return self.db.query(Autorizacion).filter(Autorizacion.id == autorizacion_id).first()

    def listar_pendientes_hitl(self) -> list[Autorizacion]:
        return (
            self.db.query(Autorizacion)
            .filter(Autorizacion.hitl_requerido == True)  # noqa: E712
            .filter(Autorizacion.hitl_decision.is_(None))
            .order_by(Autorizacion.created_at.desc())
            .all()
        )

    @staticmethod
    def _aplicar_resultado(autorizacion: Autorizacion, final: dict) -> None:
        """Mapea el state final del grafo a la fila Autorizacion."""
        datos = final.get("datos_estructurados") or {}
        respuesta = final.get("respuesta_aseguradora") or {}

        autorizacion.estado = final.get("estado", "error")
        autorizacion.confidence_score = final.get("confidence_score")
        autorizacion.aseguradora = final.get("aseguradora")
        autorizacion.tipo_poliza = final.get("tipo_poliza")
        autorizacion.procedimiento_codigo = final.get("procedimiento_codigo")
        autorizacion.requiere_autorizacion = final.get("requiere_autorizacion")
        autorizacion.cobertura_verificada = final.get("cobertura_verificada")
        autorizacion.numero_autorizacion = final.get("numero_autorizacion")
        autorizacion.solicitud_referencia = final.get("solicitud_referencia")
        autorizacion.hitl_requerido = final.get("hitl_requerido", False)

        autorizacion.paciente_nombre = datos.get("paciente_nombre")
        autorizacion.medico_nombre = datos.get("medico_nombre")
        autorizacion.procedimiento_descripcion = datos.get("procedimiento_descripcion")
        autorizacion.procedimiento_cie10 = datos.get("procedimiento_cie10")
        autorizacion.poliza_numero = datos.get("paciente_poliza")
        autorizacion.urgencia = "urgente" if datos.get("urgente") else "normal"

        if final.get("solicitud_referencia"):
            autorizacion.solicitud_enviada_at = datetime.now(timezone.utc)

        if respuesta:
            autorizacion.respuesta_recibida_at = datetime.now(timezone.utc)
            autorizacion.raw_respuesta = json.dumps(respuesta, ensure_ascii=False)
            estado_final = final.get("estado")
            if estado_final == "autorizado":
                autorizacion.autorizado = True
            elif estado_final == "denegado":
                autorizacion.autorizado = False
                autorizacion.motivo_denegacion = respuesta.get("motivo")
