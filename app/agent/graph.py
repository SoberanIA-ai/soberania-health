"""Grafo LangGraph del agente de autorizaciones.

Sec 3.1 del handoff. Construye el StateGraph con los 9 nodos y las
transiciones condicionales (HITL, no requiere autorización, etc.).
"""
from langgraph.graph import END, StateGraph

from app.agent import nodes
from app.agent.state import AuthorizationState


def _despues_de_verificar(state: AuthorizationState) -> str:
    """Si hitl_requerido o no cubierto → revisión humana."""
    if state.get("hitl_requerido"):
        return "hitl_check"
    return "generar_solicitud"


def _despues_de_hitl(state: AuthorizationState) -> str:
    """Si sigue pendiente_hitl, terminamos (dashboard de Fase 4 retoma).

    Si no, seguimos al siguiente paso.
    """
    if state.get("estado") == "pendiente_hitl":
        return "registrar_audit"
    return "generar_solicitud"


def _despues_de_generar(state: AuthorizationState) -> str:
    """Saltarse enviar_solicitud cuando no hay solicitud que enviar."""
    estado = state.get("estado")
    if estado == "no_requiere_autorizacion":
        return "registrar_audit"
    if estado == "pendiente_hitl":
        return "registrar_audit"
    return "enviar_solicitud"


def construir_grafo():
    """Construye y compila el grafo LangGraph del agente.

    Retorna el grafo compilado, listo para ainvoke().
    """
    graph = StateGraph(AuthorizationState)

    graph.add_node("parse_orden_medica", nodes.parse_orden_medica)
    graph.add_node("verificar_cobertura", nodes.verificar_cobertura)
    graph.add_node("hitl_check", nodes.hitl_check)
    graph.add_node("generar_solicitud", nodes.generar_solicitud)
    graph.add_node("enviar_solicitud", nodes.enviar_solicitud)
    graph.add_node("monitorizar_respuesta", nodes.monitorizar_respuesta)
    graph.add_node("procesar_respuesta", nodes.procesar_respuesta)
    graph.add_node("notificar_resultado", nodes.notificar_resultado)
    graph.add_node("registrar_audit", nodes.registrar_audit)

    graph.set_entry_point("parse_orden_medica")
    graph.add_edge("parse_orden_medica", "verificar_cobertura")
    graph.add_conditional_edges(
        "verificar_cobertura",
        _despues_de_verificar,
        {"hitl_check": "hitl_check", "generar_solicitud": "generar_solicitud"},
    )
    graph.add_conditional_edges(
        "hitl_check",
        _despues_de_hitl,
        {"registrar_audit": "registrar_audit", "generar_solicitud": "generar_solicitud"},
    )
    graph.add_conditional_edges(
        "generar_solicitud",
        _despues_de_generar,
        {"registrar_audit": "registrar_audit", "enviar_solicitud": "enviar_solicitud"},
    )
    graph.add_edge("enviar_solicitud", "monitorizar_respuesta")
    graph.add_edge("monitorizar_respuesta", "procesar_respuesta")
    graph.add_edge("procesar_respuesta", "notificar_resultado")
    graph.add_edge("notificar_resultado", "registrar_audit")
    graph.add_edge("registrar_audit", END)

    return graph.compile()


# Singleton compilado para reutilizar entre invocaciones
_compiled_graph = None


def get_grafo():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = construir_grafo()
    return _compiled_graph
