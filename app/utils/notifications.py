"""Notificaciones — placeholder Fase 2.

Fase 4+ implementa email + webhook al HIS. Fase 2 sólo registra en log.
"""
import logging

logger = logging.getLogger(__name__)


async def notificar_recepcion(
    autorizacion_id: str,
    estado: str,
    detalles: dict,
) -> None:
    """Notifica el resultado de una autorización.

    Fase 2: log estructurado. Fase 4+: email + webhook al HIS.
    """
    logger.info(
        "notificacion",
        extra={
            "autorizacion_id": autorizacion_id,
            "estado": estado,
            "detalles": detalles,
        },
    )
