"""
Hook de integración con Doctoris HIS — STUB.

Estado: PENDIENTE de acceso a APIs privadas de HM.
Las APIs de Doctoris solo son accesibles desde IPs autorizadas
de los entornos PRE y PRO de HM Hospitales.

Cuando HM proporcione acceso:
1. Implementar la lógica en _procesar_orden_hl7()
2. Validar firma del webhook con el secret de HM
3. Cambiar DOCTORIS_WEBHOOK_STATUS a "ACTIVO" en .env
4. Añadir tests en tests/test_doctoris_webhook.py
5. Documentar el formato exacto del mensaje HL7 en docs/CONECTORES.md
"""
import logging

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integraciones", tags=["integraciones"])

DOCTORIS_WEBHOOK_STATUS = "STUB"  # Cambiar a "ACTIVO" cuando HM dé acceso


@router.post("/doctoris/orden")
async def recibir_orden_doctoris(request: Request):
    """
    Recibe órdenes médicas desde Doctoris HIS.
    ESTADO ACTUAL: STUB — registra la orden y responde 200 sin procesarla.
    """
    body = await request.body()
    logger.info(
        "Orden Doctoris recibida [STUB — no procesada]. "
        f"Bytes: {len(body)}. "
        "Implementar cuando HM proporcione acceso a APIs PRE."
    )
    # TODO: cuando HM dé acceso:
    # 1. Validar X-Doctoris-Signature
    # 2. Parsear HL7: hl7_parser.parse(body)
    # 3. Llamar a autorizacion_service.procesar(orden_texto)
    # 4. Responder con el ID de autorización generado
    return Response(status_code=200, content="OK — recibido [STUB]")


@router.get("/doctoris/status")
async def estado_integracion_doctoris():
    """Estado de la integración con Doctoris para el panel de auditoría."""
    return {
        "status": DOCTORIS_WEBHOOK_STATUS,
        "descripcion": "Integración pendiente de acceso a APIs privadas de HM Hospitales",
        "endpoint": "POST /api/v1/integraciones/doctoris/orden",
        "documentacion": "docs/CONECTORES.md",
    }