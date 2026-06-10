"""Estado del grafo LangGraph del agente de autorizaciones.

Sec 3.2 del handoff. Cada nodo recibe el estado completo y devuelve
el delta a aplicar.

audit_entries y errores usan Annotated[list, add] para que se acumulen
automáticamente entre nodos (cada nodo añade su entrada, LangGraph las
concatena). Sec 10 del handoff: trazabilidad completa por paso.
"""
from operator import add
from typing import Annotated, Literal, TypedDict


class AuthorizationState(TypedDict, total=False):
    # Input
    orden_raw: str
    modo: Literal["real", "mock"]
    autorizacion_id: str  # UUID de la fila Autorizacion en DB (lo asigna el service)

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
        "error_procesamiento",
    ]

    # Resultado
    respuesta_aseguradora: dict
    numero_autorizacion: str
    solicitud_referencia: str

    # Audit & errores — se acumulan entre nodos
    audit_entries: Annotated[list[dict], add]
    errores: Annotated[list[str], add]
