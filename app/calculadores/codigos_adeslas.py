"""Calculador de códigos Adeslas.

DATA_STATUS = "SIMULADO"
Los códigos son ejemplos de estructura, no valores reales.

Proceso de actualización a datos reales (Fase 0):
1. HM proporciona catálogo operativo Adeslas
2. Revisar y validar cada código con back-office HM
3. Ejecutar test_calculadores.py completo
4. Deploy con HITL al 100% en Adeslas hasta estabilización
5. Cambiar DATA_STATUS a "VALIDADO_YYYY-MM-DD"

Diferencias relevantes de Adeslas vs Sanitas (a investigar en Fase 0):
- ¿Tiene API o solo portal web?
- ¿Usa nomenclatura propia o adaptación de CIE-10?
- ¿Los copagos son fijos o variables por póliza?
- ¿Los plazos de respuesta son distintos por tipo de procedimiento?

Python puro: sin LLM, sin I/O, sin red.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"


class TipoPolizaAdeslas(Enum):
    BASICA = "basica"
    PLENA = "plena"
    COMPLETA = "completa"
    PREMIUM = "premium"


@dataclass
class CodigoAdeslas:
    codigo: str
    descripcion: str
    requiere_autorizacion: bool
    documentacion_requerida: list[str] = field(default_factory=list)
    copago_euros: float = 0.0
    plazo_respuesta_horas: int = 48
    notas: Optional[str] = None


# Estructura idéntica a codigos_sanitas.py
# Rellenar con datos reales en Fase 0 con el Google Sheet de Isabella
CODIGOS: dict[str, dict[str, CodigoAdeslas]] = {}


def get_codigo(
    procedimiento_sim_id: str,
    tipo_poliza: str,
) -> Optional[CodigoAdeslas]:
    """Devuelve el código Adeslas. None si no está en catálogo (→ HITL)."""
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
