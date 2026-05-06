"""Reglas de cobertura por aseguradora y tipo de póliza.

Define qué procedimientos requieren autorización previa.

DATA_STATUS = "SIMULADO"
Las reglas son estructura de ejemplo, no reglas reales.

En producción estas reglas se obtienen de:
- Contratos HM-aseguradora (confidenciales, aporta HM)
- Documentación oficial de cada aseguradora
- Validación con back-office HM procedimiento a procedimiento

Principio safe-default:
Si un procedimiento no está en las reglas → requiere_auth = True
Nunca asumimos que no requiere autorización si no lo sabemos.

Python puro: sin LLM, sin I/O, sin red.
"""

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"

# Estructura: {aseguradora: {tipo_poliza: {procedimiento_id: requiere_auth}}}
# VACÍO hasta Fase 0. El safe-default en verificador_cobertura.py
# garantiza que todo va a HITL si no está mapeado.
REGLAS: dict[str, dict[str, dict[str, bool]]] = {}


def requiere_autorizacion_previa(
    aseguradora: str,
    tipo_poliza: str,
    procedimiento_id: str,
) -> bool:
    """Safe default: True si no tenemos la regla.

    En producción, estas reglas vendrán de Fase 0 con HM.
    """
    aseg = REGLAS.get(aseguradora.lower(), {})
    poliza = aseg.get(tipo_poliza, {})
    return poliza.get(procedimiento_id, True)  # True = safe default


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
