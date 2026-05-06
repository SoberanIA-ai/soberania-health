"""Helpers para confidence scoring.

Regla 4 sec 19: HITL obligatorio en modo real hasta confidence acumulado > 0.95
en 100 autorizaciones consecutivas.
"""
from app.config import settings


def combinar(parser: float, calculador: float) -> float:
    """Confidence combinada de varios pasos.

    Tomamos el mínimo: si cualquier paso tiene baja confianza,
    el sistema completo no debe confiar.
    """
    return min(parser, calculador)


def requiere_hitl(confidence: float) -> bool:
    """True si la confidence está por debajo del umbral configurado."""
    return confidence < settings.confidence_threshold_hitl
