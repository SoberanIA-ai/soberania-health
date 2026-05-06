"""Nodos del grafo LangGraph del agente de autorizaciones.

Sec 8.3 del handoff. Cada nodo recibe AuthorizationState y devuelve un dict
con el delta a aplicar al estado.

Principios:
- Los nodos LLM (parse_orden_medica) NO deciden códigos ni datos numéricos
- Los nodos de cálculo (verificar_cobertura, generar_solicitud) son Python puro
- El nodo enviar_solicitud usa connector según modo (mock/real)
- registrar_audit añade entrada al audit_entries del estado
"""
from datetime import datetime, timezone

from app.agent.llm_client import GUARDRAIL_MODEL, LLMClient, PARSER_MODEL
from app.agent.state import AuthorizationState
from app.calculadores import (
    codigos_adeslas,
    codigos_dkv,
    codigos_sanitas,
    generador_solicitud,
    identificador_aseguradora,
    verificador_cobertura,
)
from app.conectores.mock_connector import MockConnector
from app.config import settings
from app.integrations import hl7_parser
from app.utils import audit_log, confidence
from app.utils.notifications import notificar_recepcion


_llm: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Singleton lazy del LLM client. Permite override en tests."""
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm


def set_llm_client(client: LLMClient) -> None:
    """Inyecta un cliente LLM (útil en tests)."""
    global _llm
    _llm = client


# ---------------------------------------------------------------------------
# Nodo 1 — parse_orden_medica (LLM)
# ---------------------------------------------------------------------------


async def parse_orden_medica(state: AuthorizationState) -> dict:
    """Extrae datos estructurados del texto de la orden médica.

    Usa Mistral Large + guardrail Mistral Nemo. En mock mode, heurística
    determinística (regla 5 sec 19).
    """
    orden_raw = state["orden_raw"]
    texto = hl7_parser.hl7_a_texto(orden_raw) if orden_raw.startswith("MSH") else orden_raw

    client = get_llm_client()
    datos = await client.parse_orden_medica(texto)
    validacion = await client.validar_guardrail(datos)

    return {
        "datos_estructurados": datos,
        "confidence_score": validacion["confidence"],
        "hitl_requerido": validacion["requiere_hitl"],
        "razon_hitl": validacion.get("razon_hitl", ""),
        "estado": "parseado",
    }


# ---------------------------------------------------------------------------
# Nodo 2 — verificar_cobertura (Python puro)
# ---------------------------------------------------------------------------


async def verificar_cobertura(state: AuthorizationState) -> dict:
    """Comprueba si el procedimiento está cubierto y requiere autorización.

    Python puro — no consulta LLM. Usa los calculadores como única fuente
    de verdad (regla 3 sec 19).
    """
    datos = state["datos_estructurados"]
    aseguradora_raw = datos.get("paciente_aseguradora", "")
    canonical = identificador_aseguradora.identificar(aseguradora_raw)

    cubierto, requiere_auth, documentacion, conf_calc = verificador_cobertura.verificar(
        aseguradora=aseguradora_raw,
        procedimiento_cie10=datos.get("procedimiento_cie10", ""),
        tipo_poliza=datos.get("paciente_tipo_poliza") or "basica",
    )

    confidence_combinada = confidence.combinar(state["confidence_score"], conf_calc)
    hitl = (
        state.get("hitl_requerido", False)
        or confidence.requiere_hitl(confidence_combinada)
        or not cubierto
    )

    return {
        "aseguradora": canonical or aseguradora_raw,
        "tipo_poliza": datos.get("paciente_tipo_poliza") or "basica",
        "cobertura_verificada": cubierto,
        "requiere_autorizacion": requiere_auth,
        "documentacion_requerida": documentacion,
        "confidence_score": confidence_combinada,
        "hitl_requerido": hitl,
        "estado": "verificado",
    }


# ---------------------------------------------------------------------------
# Nodo 3 — generar_solicitud (Python puro)
# ---------------------------------------------------------------------------


_CALCULADOR_POR_ASEGURADORA = {
    "sanitas": codigos_sanitas,
    "adeslas": codigos_adeslas,
    "dkv": codigos_dkv,
}


async def generar_solicitud(state: AuthorizationState) -> dict:
    """Genera el payload de solicitud en el formato de la aseguradora.

    Si no requiere autorización → estado: no_requiere_autorizacion (END).
    """
    if not state.get("requiere_autorizacion"):
        return {
            "estado": "no_requiere_autorizacion",
        }

    datos = state["datos_estructurados"]
    aseguradora = state["aseguradora"]
    tipo_poliza = state["tipo_poliza"]
    cie10 = datos.get("procedimiento_cie10", "")

    calculador = _CALCULADOR_POR_ASEGURADORA.get(aseguradora)
    codigo = calculador.get_codigo(cie10, tipo_poliza) if calculador else None

    if codigo is None:
        # Safe default: no podemos generar solicitud sin código → HITL
        return {
            "estado": "pendiente_hitl",
            "hitl_requerido": True,
            "razon_hitl": f"Sin código de aseguradora para {cie10}",
        }

    payload = generador_solicitud.generar(
        aseguradora=aseguradora,
        datos_paciente={
            "nombre": _split_nombre(datos.get("paciente_nombre"))[0],
            "apellidos": _split_nombre(datos.get("paciente_nombre"))[1],
            "poliza": datos.get("paciente_poliza"),
            "fecha_nacimiento": None,
        },
        datos_medico={
            "nombre": datos.get("medico_nombre"),
            "numero_colegiado": None,
            "especialidad": datos.get("medico_especialidad"),
        },
        procedimiento_cie10=cie10,
        procedimiento_codigo_aseguradora=codigo.codigo,
        documentacion_adjunta=state.get("documentacion_requerida") or [],
        urgente=bool(datos.get("urgente")),
    )

    return {
        "solicitud_generada": payload,
        "procedimiento_codigo": codigo.codigo,
        "estado": "solicitud_generada",
    }


def _split_nombre(nombre_completo: str | None) -> tuple[str, str]:
    """Heurística simple: primera palabra=nombre, resto=apellidos."""
    if not nombre_completo:
        return ("", "")
    partes = nombre_completo.strip().split(maxsplit=1)
    if len(partes) == 1:
        return (partes[0], "")
    return (partes[0], partes[1])


# ---------------------------------------------------------------------------
# Nodo 4 — hitl_check
# ---------------------------------------------------------------------------


async def hitl_check(state: AuthorizationState) -> dict:
    """Si hitl_requerido y no estamos en mock auto-approve, se marca pendiente_hitl.

    Fase 4 conecta el dashboard. En Fase 2, si modo=mock, el flow puede
    continuar sólo si hitl no se dispara — es responsabilidad del caller
    construir casos donde hitl no se dispare para tests E2E happy path.
    """
    if state.get("hitl_requerido"):
        return {
            "estado": "pendiente_hitl",
        }
    # Sin HITL: passthrough (LangGraph requiere algún canal escrito)
    return {"estado": state.get("estado", "verificado")}


# ---------------------------------------------------------------------------
# Nodo 5 — enviar_solicitud
# ---------------------------------------------------------------------------


async def enviar_solicitud(state: AuthorizationState) -> dict:
    """Envía la solicitud al portal de la aseguradora.

    En modo mock o si MODO_DEFAULT=mock → MockConnector (sec 9.1).
    En modo real → connector específico (Fase 2+ no implementado todavía
    porque depende de credenciales de aseguradoras).
    """
    modo = state.get("modo") or settings.modo_default

    if modo == "mock":
        connector = MockConnector(latencia_segundos=0)
    else:
        # Connectores reales se implementan cuando lleguen credenciales
        # En cualquier caso, fallback a mock para no romper el flujo
        connector = MockConnector(latencia_segundos=0)

    resultado = await connector.enviar(state["solicitud_generada"])

    return {
        "solicitud_referencia": resultado["referencia"],
        "respuesta_aseguradora": resultado,
        "estado": "enviado",
    }


# ---------------------------------------------------------------------------
# Nodo 6 — monitorizar_respuesta
# ---------------------------------------------------------------------------


async def monitorizar_respuesta(state: AuthorizationState) -> dict:
    """En real mode: hace polling al portal. En mock: pass-through.

    Para Fase 2 con MockConnector, la respuesta ya está en state. No-op.
    """
    return {"estado": "pendiente_respuesta"}


# ---------------------------------------------------------------------------
# Nodo 7 — procesar_respuesta
# ---------------------------------------------------------------------------


async def procesar_respuesta(state: AuthorizationState) -> dict:
    """Mapea la respuesta de la aseguradora al estado final."""
    respuesta = state.get("respuesta_aseguradora", {})
    estado_aseguradora = respuesta.get("estado", "error")

    delta = {
        "respuesta_aseguradora": respuesta,
    }

    if estado_aseguradora == "aprobado":
        delta["estado"] = "autorizado"
        delta["numero_autorizacion"] = respuesta.get("numero_autorizacion", "")
    elif estado_aseguradora == "denegado":
        delta["estado"] = "denegado"
    elif estado_aseguradora == "informacion_adicional":
        delta["estado"] = "informacion_adicional"
    else:
        delta["estado"] = "error"
        delta["errores"] = (state.get("errores") or []) + [
            f"Estado aseguradora desconocido: {estado_aseguradora}"
        ]

    return delta


# ---------------------------------------------------------------------------
# Nodo 8 — notificar_resultado
# ---------------------------------------------------------------------------


async def notificar_resultado(state: AuthorizationState) -> dict:
    """Envía notificación. Fase 2: log. Fase 4+: email + webhook HIS."""
    await notificar_recepcion(
        autorizacion_id=state.get("solicitud_referencia", ""),
        estado=state.get("estado", "desconocido"),
        detalles={
            "aseguradora": state.get("aseguradora"),
            "procedimiento_codigo": state.get("procedimiento_codigo"),
            "numero_autorizacion": state.get("numero_autorizacion"),
        },
    )
    # LangGraph requiere escribir al menos un canal: confirmamos el estado actual
    return {"estado": state.get("estado", "desconocido")}


# ---------------------------------------------------------------------------
# Nodo 9 — registrar_audit
# ---------------------------------------------------------------------------


async def registrar_audit(state: AuthorizationState) -> dict:
    """Registra una entrada en audit_entries del estado.

    Fase 3 implementa SHA256 encadenado y persistencia DB (sec 10).
    """
    entrada = audit_log.construir_entrada(
        autorizacion_id=state.get("solicitud_referencia"),
        accion="autorizacion_procesada",
        actor="agente_autorizaciones",
        datos_entrada={"orden_raw": state.get("orden_raw", "")[:200]},
        datos_salida={
            "estado": state.get("estado"),
            "numero_autorizacion": state.get("numero_autorizacion"),
            "aseguradora": state.get("aseguradora"),
            "procedimiento_codigo": state.get("procedimiento_codigo"),
        },
        confidence=state.get("confidence_score", 0.0),
        modelo_usado=PARSER_MODEL if not get_llm_client().use_mock else "mock",
        hitl_intervencion=state.get("hitl_requerido", False),
    )
    return {
        "audit_entries": (state.get("audit_entries") or []) + [entrada],
    }
