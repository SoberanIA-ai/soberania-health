"""AuditLogger — placeholder Fase 2.

Fase 3 implementa SHA256 encadenado + persistencia en DB (sec 10 del handoff).
Fase 2 sólo registra entradas en memoria — suficiente para que el grafo
tenga su nodo registrar_audit y el flujo end-to-end funcione.

Regla 7 sec 19: el audit log es sagrado. Esta versión Fase 2 no es
inmutable — Fase 3 corrige eso.
"""
from datetime import datetime, timezone
from typing import Optional


def construir_entrada(
    autorizacion_id: Optional[str],
    accion: str,
    actor: str,
    datos_entrada: dict,
    datos_salida: dict,
    confidence: float = 1.0,
    modelo_usado: Optional[str] = None,
    hitl_intervencion: bool = False,
) -> dict:
    """Construye una entrada de audit log básica (sin hash todavía).

    Fase 3 añade hash_sha256 + hash_previo encadenado.
    """
    return {
        "autorizacion_id": autorizacion_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "accion": accion,
        "actor": actor,
        "resultado": datos_salida.get("estado", "desconocido"),
        "datos_entrada": datos_entrada,
        "datos_salida": datos_salida,
        "confidence_score": confidence,
        "modelo_usado": modelo_usado,
        "version_calculador": "1.0.0-simulado",
        "hitl_intervencion": hitl_intervencion,
    }
