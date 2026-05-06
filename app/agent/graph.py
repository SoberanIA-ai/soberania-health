"""Grafo LangGraph del agente de autorizaciones.

Sec 3.1 del handoff. 8 nodos + transiciones condicionales.

Cada nodo añade su propio audit entry al state (Annotated[list, add]).
La persistencia con SHA256 encadenado se hace en AutorizacionService
después de invocar el grafo (sec 10).
"""
from langgraph.graph import END, StateGraph

from app.agent import nodes
from app.agent.state import AuthorizationState


def _despues_de_verificar(state: AuthorizationState) -> str:
    if state.get("hitl_requerido"):
        return "hitl_check"
    return "generar_solicitud"


def _despues_de_hitl(state: AuthorizationState) -> str:
    """Si pendiente_hitl, terminamos. Fase 4 retoma desde el dashboard."""
    if state.get("estado") == "pendiente_hitl":
        return "fin"
    return "generar_solicitud"


def _despues_de_generar(state: AuthorizationState) -> str:
    estado = state.get("estado")
    if estado in {"no_requiere_autorizacion", "pendiente_hitl"}:
        return "fin"
    return "enviar_solicitud"


def construir_grafo():
    graph = StateGraph(AuthorizationState)

    graph.add_node("parse_orden_medica", nodes.parse_orden_medica)
    graph.add_node("verificar_cobertura", nodes.verificar_cobertura)
    graph.add_node("hitl_check", nodes.hitl_check)
    graph.add_node("generar_solicitud", nodes.generar_solicitud)
    graph.add_node("enviar_solicitud", nodes.enviar_solicitud)
    graph.add_node("monitorizar_respuesta", nodes.monitorizar_respuesta)
    graph.add_node("procesar_respuesta", nodes.procesar_respuesta)
    graph.add_node("notificar_resultado", nodes.notificar_resultado)

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
        {"fin": END, "generar_solicitud": "generar_solicitud"},
    )
    graph.add_conditional_edges(
        "generar_solicitud",
        _despues_de_generar,
        {"fin": END, "enviar_solicitud": "enviar_solicitud"},
    )
    graph.add_edge("enviar_solicitud", "monitorizar_respuesta")
    graph.add_edge("monitorizar_respuesta", "procesar_respuesta")
    graph.add_edge("procesar_respuesta", "notificar_resultado")
    graph.add_edge("notificar_resultado", END)

    return graph.compile()


_compiled_graph = None


def get_grafo():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = construir_grafo()
    return _compiled_graph
