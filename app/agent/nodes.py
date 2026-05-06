"""Nodos del grafo LangGraph del agente de autorizaciones.

Sec 8.3 del handoff. Cada nodo recibe AuthorizationState y devuelve un dict
con el delta a aplicar al estado.

Cada nodo añade su entrada al audit_entries (acumulación automática vía
Annotated[list, add] en state.py). Sec 10: trazabilidad por paso.
"""
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


def _modelo_actor(es_llm: bool, nombre_actor: str) -> tuple[str, str]:
    """Devuelve (modelo_usado, actor) según si el nodo invocó LLM o no."""
    if not es_llm:
        return ("", nombre_actor)
    if get_llm_client().use_mock:
        return ("mock", nombre_actor)
    return (PARSER_MODEL, nombre_actor)


def _entry(
    state: AuthorizationState,
    accion: str,
    actor: str,
    datos_entrada: dict,
    datos_salida: dict,
    confidence_score: float = 1.0,
    modelo_usado: str | None = None,
    hitl_intervencion: bool = False,
) -> dict:
    """Construye un audit entry para el nodo actual."""
    return audit_log.construir_entrada(
        autorizacion_id=state.get("autorizacion_id"),
        accion=accion,
        actor=actor,
        datos_entrada=datos_entrada,
        datos_salida=datos_salida,
        confidence=confidence_score,
        modelo_usado=modelo_usado,
        hitl_intervencion=hitl_intervencion,
    )


# ---------------------------------------------------------------------------
# Nodo 1 — parse_orden_medica (LLM)
# ---------------------------------------------------------------------------


async def parse_orden_medica(state: AuthorizationState) -> dict:
    """Extrae datos estructurados del texto de la orden médica."""
    orden_raw = state["orden_raw"]
    texto = hl7_parser.hl7_a_texto(orden_raw) if orden_raw.startswith("MSH") else orden_raw

    client = get_llm_client()
    datos = await client.parse_orden_medica(texto)
    validacion = await client.validar_guardrail(datos)

    delta = {
        "datos_estructurados": datos,
        "confidence_score": validacion["confidence"],
        "hitl_requerido": validacion["requiere_hitl"],
        "razon_hitl": validacion.get("razon_hitl", ""),
        "estado": "parseado",
    }
    modelo = "mock" if client.use_mock else f"{PARSER_MODEL}+{GUARDRAIL_MODEL}"
    delta["audit_entries"] = [
        _entry(
            state,
            accion="parse_orden_medica",
            actor="agente_parser_llm",
            datos_entrada={"orden_raw": orden_raw[:500]},
            datos_salida={
                "estado": "parseado",
                "datos_estructurados": datos,
                "validacion": validacion,
            },
            confidence_score=validacion["confidence"],
            modelo_usado=modelo,
        )
    ]
    return delta


# ---------------------------------------------------------------------------
# Nodo 2 — verificar_cobertura (Python puro)
# ---------------------------------------------------------------------------


async def verificar_cobertura(state: AuthorizationState) -> dict:
    """Comprueba cobertura. Python puro — usa los calculadores."""
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

    delta = {
        "aseguradora": canonical or aseguradora_raw,
        "tipo_poliza": datos.get("paciente_tipo_poliza") or "basica",
        "cobertura_verificada": cubierto,
        "requiere_autorizacion": requiere_auth,
        "documentacion_requerida": documentacion,
        "confidence_score": confidence_combinada,
        "hitl_requerido": hitl,
        "estado": "verificado",
    }
    delta["audit_entries"] = [
        _entry(
            state,
            accion="verificar_cobertura",
            actor="calculador_verificador_cobertura",
            datos_entrada={
                "aseguradora": aseguradora_raw,
                "procedimiento_cie10": datos.get("procedimiento_cie10"),
                "tipo_poliza": datos.get("paciente_tipo_poliza"),
            },
            datos_salida={
                "estado": "verificado",
                "cobertura_verificada": cubierto,
                "requiere_autorizacion": requiere_auth,
                "documentacion_requerida": documentacion,
            },
            confidence_score=confidence_combinada,
        )
    ]
    return delta


# ---------------------------------------------------------------------------
# Nodo 3 — generar_solicitud (Python puro)
# ---------------------------------------------------------------------------


_CALCULADOR_POR_ASEGURADORA = {
    "sanitas": codigos_sanitas,
    "adeslas": codigos_adeslas,
    "dkv": codigos_dkv,
}


async def generar_solicitud(state: AuthorizationState) -> dict:
    """Genera el payload de solicitud."""
    if not state.get("requiere_autorizacion"):
        return {
            "estado": "no_requiere_autorizacion",
            "audit_entries": [
                _entry(
                    state,
                    accion="generar_solicitud",
                    actor="calculador_generador_solicitud",
                    datos_entrada={"requiere_autorizacion": False},
                    datos_salida={"estado": "no_requiere_autorizacion"},
                )
            ],
        }

    datos = state["datos_estructurados"]
    aseguradora = state["aseguradora"]
    tipo_poliza = state["tipo_poliza"]
    cie10 = datos.get("procedimiento_cie10", "")

    calculador = _CALCULADOR_POR_ASEGURADORA.get(aseguradora)
    codigo = calculador.get_codigo(cie10, tipo_poliza) if calculador else None

    if codigo is None:
        return {
            "estado": "pendiente_hitl",
            "hitl_requerido": True,
            "razon_hitl": f"Sin código de aseguradora para {cie10}",
            "audit_entries": [
                _entry(
                    state,
                    accion="generar_solicitud",
                    actor="calculador_generador_solicitud",
                    datos_entrada={"aseguradora": aseguradora, "cie10": cie10},
                    datos_salida={"estado": "pendiente_hitl", "razon": "sin_codigo"},
                    hitl_intervencion=True,
                )
            ],
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
        "audit_entries": [
            _entry(
                state,
                accion="generar_solicitud",
                actor="calculador_generador_solicitud",
                datos_entrada={
                    "aseguradora": aseguradora,
                    "cie10": cie10,
                    "tipo_poliza": tipo_poliza,
                },
                datos_salida={
                    "estado": "solicitud_generada",
                    "procedimiento_codigo": codigo.codigo,
                },
            )
        ],
    }


def _split_nombre(nombre_completo: str | None) -> tuple[str, str]:
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
    """Si hitl_requerido, marca pendiente_hitl. Sino, passthrough."""
    if state.get("hitl_requerido"):
        return {
            "estado": "pendiente_hitl",
            "audit_entries": [
                _entry(
                    state,
                    accion="hitl_check",
                    actor="agente_autorizaciones",
                    datos_entrada={
                        "confidence_score": state.get("confidence_score"),
                        "razon_hitl": state.get("razon_hitl", ""),
                    },
                    datos_salida={"estado": "pendiente_hitl"},
                    hitl_intervencion=True,
                )
            ],
        }
    return {"estado": state.get("estado", "verificado")}


# ---------------------------------------------------------------------------
# Nodo 5 — enviar_solicitud
# ---------------------------------------------------------------------------


async def enviar_solicitud(state: AuthorizationState) -> dict:
    """Envía la solicitud al portal de la aseguradora."""
    modo = state.get("modo") or settings.modo_default
    connector = MockConnector(latencia_segundos=0)  # real connectors: Fase 2+
    resultado = await connector.enviar(state["solicitud_generada"])

    return {
        "solicitud_referencia": resultado["referencia"],
        "respuesta_aseguradora": resultado,
        "estado": "enviado",
        "audit_entries": [
            _entry(
                state,
                accion="enviar_solicitud",
                actor=f"connector_{modo}",
                datos_entrada={"aseguradora": state.get("aseguradora")},
                datos_salida={
                    "estado": "enviado",
                    "referencia": resultado["referencia"],
                    "estado_aseguradora": resultado.get("estado"),
                },
            )
        ],
    }


# ---------------------------------------------------------------------------
# Nodo 6 — monitorizar_respuesta
# ---------------------------------------------------------------------------


async def monitorizar_respuesta(state: AuthorizationState) -> dict:
    """En real mode hace polling. En mock: pass-through."""
    return {
        "estado": "pendiente_respuesta",
        "audit_entries": [
            _entry(
                state,
                accion="monitorizar_respuesta",
                actor="agente_autorizaciones",
                datos_entrada={"referencia": state.get("solicitud_referencia")},
                datos_salida={"estado": "pendiente_respuesta"},
            )
        ],
    }


# ---------------------------------------------------------------------------
# Nodo 7 — procesar_respuesta
# ---------------------------------------------------------------------------


async def procesar_respuesta(state: AuthorizationState) -> dict:
    """Mapea la respuesta de la aseguradora al estado final."""
    respuesta = state.get("respuesta_aseguradora", {})
    estado_aseguradora = respuesta.get("estado", "error")

    delta: dict = {"respuesta_aseguradora": respuesta}

    if estado_aseguradora == "aprobado":
        delta["estado"] = "autorizado"
        delta["numero_autorizacion"] = respuesta.get("numero_autorizacion", "")
    elif estado_aseguradora == "denegado":
        delta["estado"] = "denegado"
    elif estado_aseguradora == "informacion_adicional":
        delta["estado"] = "informacion_adicional"
    else:
        delta["estado"] = "error"
        delta["errores"] = [f"Estado aseguradora desconocido: {estado_aseguradora}"]

    delta["audit_entries"] = [
        _entry(
            state,
            accion="procesar_respuesta",
            actor="agente_autorizaciones",
            datos_entrada={"respuesta_aseguradora": respuesta},
            datos_salida={
                "estado": delta["estado"],
                "numero_autorizacion": delta.get("numero_autorizacion"),
            },
        )
    ]
    return delta


# ---------------------------------------------------------------------------
# Nodo 8 — notificar_resultado
# ---------------------------------------------------------------------------


async def notificar_resultado(state: AuthorizationState) -> dict:
    """Notifica resultado al HIS / recepción. Fase 2: log."""
    await notificar_recepcion(
        autorizacion_id=state.get("solicitud_referencia", ""),
        estado=state.get("estado", "desconocido"),
        detalles={
            "aseguradora": state.get("aseguradora"),
            "procedimiento_codigo": state.get("procedimiento_codigo"),
            "numero_autorizacion": state.get("numero_autorizacion"),
        },
    )
    return {
        "estado": state.get("estado", "desconocido"),
        "audit_entries": [
            _entry(
                state,
                accion="notificar_resultado",
                actor="agente_autorizaciones",
                datos_entrada={"estado": state.get("estado")},
                datos_salida={
                    "estado": state.get("estado"),
                    "numero_autorizacion": state.get("numero_autorizacion"),
                },
            )
        ],
    }
