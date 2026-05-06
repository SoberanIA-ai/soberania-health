"""Identificador de aseguradora.

Normaliza el nombre de aseguradora extraído del parser LLM a un canonical name
soportado por el sistema. Si no reconoce, devuelve None → HITL obligatorio.

DATA_STATUS = "SIMULADO" para variantes/sinónimos. Se completa en Fase 0
revisando con HM cómo aparecen las aseguradoras en sus órdenes médicas reales.

Python puro: sin LLM, sin I/O, sin red.
"""
from typing import Optional

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"

ASEGURADORAS_SOPORTADAS = {"sanitas", "adeslas", "dkv"}

# Variantes y sinónimos detectados en órdenes simuladas.
# Ampliar en Fase 0 con muestras reales de HM.
ALIAS: dict[str, str] = {
    "sanitas": "sanitas",
    "sanitas s.a.": "sanitas",
    "sanitas sa": "sanitas",
    "bupa sanitas": "sanitas",
    "adeslas": "adeslas",
    "segurcaixa adeslas": "adeslas",
    "segurcaixa": "adeslas",
    "dkv": "dkv",
    "dkv seguros": "dkv",
    "dkv salud": "dkv",
}


def identificar(nombre_raw: Optional[str]) -> Optional[str]:
    """Normaliza el nombre de aseguradora a su canonical name.

    Devuelve None si no es una aseguradora soportada → HITL obligatorio.
    Nunca asume — mejor escalar a humano que adivinar.
    """
    if not nombre_raw:
        return None
    clave = nombre_raw.strip().lower()
    canonical = ALIAS.get(clave)
    if canonical in ASEGURADORAS_SOPORTADAS:
        return canonical
    return None


def es_soportada(nombre_raw: Optional[str]) -> bool:
    """True si la aseguradora es una de las 3 del MVP."""
    return identificar(nombre_raw) is not None


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
