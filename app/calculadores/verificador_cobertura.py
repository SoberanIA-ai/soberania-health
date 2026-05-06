"""Verificador de cobertura.

¿Este procedimiento requiere autorización? ¿Está cubierto por esta póliza?

Orquesta los calculadores codigos_X según la aseguradora. Python puro.

Contrato:
    verificar(aseguradora, procedimiento_cie10, tipo_poliza) -> tuple
        return (cubierto, requiere_auth, documentacion, confidence)

Confidence < 0.80 dispara HITL obligatorio (sec 19 del handoff, regla 4).

Python puro: sin LLM, sin I/O, sin red.
"""
from typing import Tuple

from app.calculadores import (
    codigos_adeslas,
    codigos_dkv,
    codigos_sanitas,
    identificador_aseguradora,
)

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"

CONFIDENCE_CATALOGO_HIT = 1.0  # Procedimiento encontrado en catálogo
CONFIDENCE_NO_CATALOGADO = 0.5  # No catalogado → safe default + HITL
CONFIDENCE_ASEGURADORA_DESCONOCIDA = 0.0  # Aseguradora no soportada → HITL


def verificar(
    aseguradora: str,
    procedimiento_cie10: str,
    tipo_poliza: str = "basica",
) -> Tuple[bool, bool, list[str], float]:
    """Verifica cobertura de un procedimiento.

    Returns:
        (cubierto, requiere_autorizacion, documentacion_requerida, confidence)

    Reglas:
    - Aseguradora no soportada → (False, True, [], 0.0) → HITL
    - Procedimiento no en catálogo → (False, True, [], 0.5) → HITL (safe default)
    - Procedimiento en catálogo → (True, codigo.requiere_auth, docs, 1.0)
    """
    canonical = identificador_aseguradora.identificar(aseguradora)
    if canonical is None:
        return (False, True, [], CONFIDENCE_ASEGURADORA_DESCONOCIDA)

    if canonical == "sanitas":
        codigo = codigos_sanitas.get_codigo(procedimiento_cie10, tipo_poliza)
    elif canonical == "adeslas":
        codigo = codigos_adeslas.get_codigo(procedimiento_cie10, tipo_poliza)
    elif canonical == "dkv":
        codigo = codigos_dkv.get_codigo(procedimiento_cie10, tipo_poliza)
    else:
        return (False, True, [], CONFIDENCE_ASEGURADORA_DESCONOCIDA)

    if codigo is None:
        return (False, True, [], CONFIDENCE_NO_CATALOGADO)

    return (
        True,
        codigo.requiere_autorizacion,
        list(codigo.documentacion_requerida),
        CONFIDENCE_CATALOGO_HIT,
    )


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
