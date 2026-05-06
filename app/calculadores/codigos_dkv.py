"""Calculador de códigos DKV.

DATA_STATUS = "SIMULADO"

Diferencias relevantes de DKV vs Sanitas/Adeslas (a investigar en Fase 0):
- DKV tiene acuerdo con HM confirmado (fuente: Galiciapress)
- ¿Tiene API de autorizaciones o solo portal web?
- ¿Usa códigos propios o estándar SENAME?
- Verificar si los copagos siguen el convenio DKV-HM actual

Python puro: sin LLM, sin I/O, sin red.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"


class TipoPolizaDKV(Enum):
    INTEGRAL = "integral"
    MUNDISALUD = "mundisalud"
    CLASSICA = "classica"
    TOP = "top"


@dataclass
class CodigoDKV:
    codigo: str
    descripcion: str
    requiere_autorizacion: bool
    documentacion_requerida: list[str] = field(default_factory=list)
    copago_euros: float = 0.0
    plazo_respuesta_horas: int = 72
    notas: Optional[str] = None


# Vacío hasta Fase 0 con HM
CODIGOS: dict[str, dict[str, CodigoDKV]] = {}


def get_codigo(
    procedimiento_sim_id: str,
    tipo_poliza: str,
) -> Optional[CodigoDKV]:
    """Devuelve el código DKV. None si no está en catálogo (→ HITL)."""
    procedimiento = CODIGOS.get(procedimiento_sim_id)
    if not procedimiento:
        return None
    return procedimiento.get(tipo_poliza)


def requiere_autorizacion(
    procedimiento_sim_id: str,
    tipo_poliza: str,
) -> bool:
    """Safe default: True si no está en catálogo."""
    codigo = get_codigo(procedimiento_sim_id, tipo_poliza)
    if codigo is None:
        return True
    return codigo.requiere_autorizacion


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
