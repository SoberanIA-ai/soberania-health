"""SLAs de respuesta por aseguradora y urgencia.

DATA_STATUS = "SIMULADO"
Los plazos son estimaciones del sector, no contractuales.

En producción estos plazos se obtienen de:
- Contratos HM-aseguradora (SLAs comprometidos)
- Regulación: AI Act no impone SLAs, pero el contrato con HM sí
- Validar con HM cuándo se dispara un recordatorio real

Nota: los SLAs de respuesta de aseguradoras en España
no están regulados uniformemente. Varían por contrato.

Python puro: sin LLM, sin I/O, sin red.
"""

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"

# Estimaciones del sector — NO contractuales
# Confirmar con HM los SLAs reales de cada aseguradora
PLAZOS_HORAS: dict[str, dict[str, int]] = {
    "sanitas": {
        "normal": 48,
        "urgente": 4,
    },
    "adeslas": {
        "normal": 48,
        "urgente": 4,
    },
    "dkv": {
        "normal": 72,
        "urgente": 6,
    },
}

DEFAULT_PLAZO_HORAS = 72  # Si no tenemos el dato, 72h es conservador


def get_plazo_horas(aseguradora: str, urgente: bool = False) -> int:
    """Devuelve el SLA en horas para una aseguradora dada.

    Si la aseguradora no está mapeada → DEFAULT_PLAZO_HORAS (72h, conservador).
    """
    tipo = "urgente" if urgente else "normal"
    plazos = PLAZOS_HORAS.get(aseguradora.lower(), {})
    return plazos.get(tipo, DEFAULT_PLAZO_HORAS)


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
