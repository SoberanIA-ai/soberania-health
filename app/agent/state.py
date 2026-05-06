"""Estado del grafo LangGraph del agente de autorizaciones.

Sec 3.2 del handoff. Cada nodo recibe el estado completo y devuelve
el delta a aplicar.
"""
from typing import Literal, TypedDict


class AuthorizationState(TypedDict, total=False):
    # Input
    orden_raw: str
    modo: Literal["real", "mock"]

    # Procesamiento (parser LLM + guardrail)
    datos_estructurados: dict
    confidence_score: float
    hitl_requerido: bool
    razon_hitl: str

    # Identificación / verificación
    aseguradora: str
    tipo_poliza: str
    procedimiento_codigo: str
    requiere_autorizacion: bool
    cobertura_verificada: bool
    documentacion_requerida: list[str]

    # Solicitud
    solicitud_generada: dict
    documentos_adjuntos: list[str]

    # Estado
    estado: Literal[
        "recibido",
        "parseado",
        "verificado",
        "pendiente_hitl",
        "aprobado_hitl",
        "no_requiere_autorizacion",
        "solicitud_generada",
        "enviado",
        "pendiente_respuesta",
        "autorizado",
        "denegado",
        "informacion_adicional",
        "error",
    ]

    # Resultado
    respuesta_aseguradora: dict
    numero_autorizacion: str
    solicitud_referencia: str

    # Audit & errores
    audit_entries: list[dict]
    errores: list[str]
