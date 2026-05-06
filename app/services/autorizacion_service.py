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
from app.utils.audit_log import AuditLogger, construir_entrada


class HitlDecisionError(Exception):
    """Errores al aplicar decisión HITL."""


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

    def metricas(self) -> dict:
        """Métricas agregadas para el dashboard.

        - total: autorizaciones procesadas
        - automatizadas: terminaron sin intervención humana
        - pendientes_hitl: en cola HITL ahora mismo
        - autorizadas / denegadas / con_hitl: desglose por estado
        - tasa_automatizacion: porcentaje 0-1
        """
        total = self.db.query(Autorizacion).count()
        pendientes = (
            self.db.query(Autorizacion)
            .filter(Autorizacion.hitl_requerido == True)  # noqa: E712
            .filter(Autorizacion.hitl_decision.is_(None))
            .count()
        )
        autorizadas = (
            self.db.query(Autorizacion)
            .filter(Autorizacion.estado == "autorizado")
            .count()
        )
        denegadas = (
            self.db.query(Autorizacion)
            .filter(Autorizacion.estado == "denegado")
            .count()
        )
        # Automatizadas = procesadas sin haber requerido HITL
        automatizadas = (
            self.db.query(Autorizacion)
            .filter(Autorizacion.hitl_requerido == False)  # noqa: E712
            .count()
        )
        con_hitl = total - automatizadas

        return {
            "total": total,
            "automatizadas": automatizadas,
            "con_hitl": con_hitl,
            "pendientes_hitl": pendientes,
            "autorizadas": autorizadas,
            "denegadas": denegadas,
            "tasa_automatizacion": (automatizadas / total) if total > 0 else 0.0,
        }

    def aplicar_decision_hitl(
        self,
        autorizacion_id: UUID | str,
        decision: str,
        revisor: str,
        notas: str | None = None,
    ) -> Autorizacion:
        """Aplica una decisión humana (aprobar/rechazar/mas_info) a una autorización
        que está en cola HITL.

        - aprobar: estado → aprobado_hitl (supervisor valida; reenvío manual)
        - rechazar: estado → rechazado_hitl
        - mas_info: estado → informacion_adicional_requerida

        Añade audit entry con hitl_intervencion=True.

        Levanta HitlDecisionError si la autorización no existe, ya tiene
        decisión, o no estaba en pendiente_hitl.
        """
        autorizacion = self.obtener(autorizacion_id)
        if autorizacion is None:
            raise HitlDecisionError("autorizacion_no_encontrada")
        if autorizacion.hitl_decision is not None:
            raise HitlDecisionError("ya_decidido")
        if not autorizacion.hitl_requerido:
            raise HitlDecisionError("no_requiere_hitl")

        estado_previo = autorizacion.estado
        nuevo_estado = {
            "aprobar": "aprobado_hitl",
            "rechazar": "rechazado_hitl",
            "mas_info": "informacion_adicional_requerida",
        }[decision]

        autorizacion.hitl_decision = decision
        autorizacion.hitl_revisor = revisor
        autorizacion.hitl_notas = notas
        autorizacion.hitl_revisado_at = datetime.now(timezone.utc)
        autorizacion.estado = nuevo_estado

        entry = construir_entrada(
            autorizacion_id=str(autorizacion.id),
            accion=f"hitl_{decision}",
            actor=f"hitl_supervisor:{revisor}",
            datos_entrada={"estado_previo": estado_previo},
            datos_salida={"estado": nuevo_estado, "notas": notas},
            confidence=1.0,  # decisión humana — confianza máxima
            modelo_usado="hitl_human",
            hitl_intervencion=True,
        )
        self.audit_logger.persistir_cadena(str(autorizacion.id), [entry])

        self.db.commit()
        self.db.refresh(autorizacion)
        return autorizacion

    @staticmethod
    def _aplicar_resultado(autorizacion: Autorizacion, final: dict) -> None:
        """Mapea el state final del grafo a la fila Autorizacion."""
        datos = final.get("datos_estructurados") or {}
        respuesta = final.get("respuesta_aseguradora") or {}

        autorizacion.estado = final.get("estado", "error")
        autorizacion.confidence_score = final.get("confidence_score")
        autorizacion.aseguradora = final.get("aseguradora")
        autorizacion.poliza_tipo = final.get("tipo_poliza")
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
