"""Calculador de códigos Sanitas.

Fuente de verdad para procedimientos Sanitas.

DATA_STATUS = "SIMULADO"
Los códigos son ejemplos de estructura, no valores reales.
Ver sección 7.1b del handoff antes de usar en producción.

Proceso de actualización a datos reales (Fase 0):
1. HM proporciona catálogo operativo Sanitas
2. Revisar y validar cada código con back-office HM
3. Ejecutar test_calculadores.py completo
4. Deploy con HITL al 100% en Sanitas hasta estabilización
5. Cambiar DATA_STATUS a "VALIDADO_YYYY-MM-DD" tras Fase 0

NUNCA modificar sin pasar el test suite completo.

Python puro: sin LLM, sin I/O, sin red.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"  # Cambiar a "VALIDADO_YYYY-MM-DD" tras Fase 0


class TipoPolizaSanitas(Enum):
    BASICA = "basica"
    MAS_SALUD = "mas_salud"
    MAS_SALUD_PLUS = "mas_salud_plus"
    OPTIMA = "optima"
    PREMIUM = "premium"


@dataclass
class CodigoSanitas:
    codigo: str  # Código interno Sanitas — PENDIENTE validación
    descripcion: str
    requiere_autorizacion: bool
    documentacion_requerida: list[str] = field(default_factory=list)
    copago_euros: float = 0.0  # PENDIENTE: confirmar con HM
    plazo_respuesta_horas: int = 48  # PENDIENTE: confirmar con Sanitas
    notas: Optional[str] = None


# CATÁLOGO SIMULADO — solo para desarrollo y demo del MVP
# Fuente real: HM back-office + validación directa con Sanitas en Fase 0
CODIGOS: dict[str, dict[str, CodigoSanitas]] = {
    "SIM_RM_RODILLA_DCHA": {
        TipoPolizaSanitas.BASICA.value: CodigoSanitas(
            codigo="SIM-001",
            descripcion="Resonancia magnética rodilla derecha",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico", "justificacion_medica"],
            copago_euros=0.0,
            plazo_respuesta_horas=48,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
        TipoPolizaSanitas.MAS_SALUD.value: CodigoSanitas(
            codigo="SIM-001",
            descripcion="Resonancia magnética rodilla derecha",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico"],
            copago_euros=0.0,
            plazo_respuesta_horas=24,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
        TipoPolizaSanitas.MAS_SALUD_PLUS.value: CodigoSanitas(
            codigo="SIM-001",
            descripcion="Resonancia magnética rodilla derecha",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico"],
            copago_euros=0.0,
            plazo_respuesta_horas=24,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
    },
    "SIM_TAC_ABDOMINAL": {
        TipoPolizaSanitas.BASICA.value: CodigoSanitas(
            codigo="SIM-002",
            descripcion="TAC abdominal con contraste",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico", "justificacion_medica"],
            copago_euros=0.0,
            plazo_respuesta_horas=48,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
    },
    "SIM_CIRUGIA_RODILLA_AMB": {
        TipoPolizaSanitas.OPTIMA.value: CodigoSanitas(
            codigo="SIM-003",
            descripcion="Cirugía ambulatoria de rodilla",
            requiere_autorizacion=True,
            documentacion_requerida=[
                "informe_clinico",
                "consentimiento_informado",
                "pruebas_complementarias",
            ],
            copago_euros=0.0,
            plazo_respuesta_horas=72,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
    },
    "SIM_COLONOSCOPIA": {
        TipoPolizaSanitas.PREMIUM.value: CodigoSanitas(
            codigo="SIM-004",
            descripcion="Colonoscopia",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico", "historia_clinica_previa"],
            copago_euros=0.0,
            plazo_respuesta_horas=72,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
    },
    "SIM_ECOCARDIOGRAMA": {
        TipoPolizaSanitas.BASICA.value: CodigoSanitas(
            codigo="SIM-005",
            descripcion="Ecocardiograma",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico"],
            copago_euros=0.0,
            plazo_respuesta_horas=48,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
    },
    "SIM_ARTROSCOPIA_RODILLA": {
        TipoPolizaSanitas.MAS_SALUD.value: CodigoSanitas(
            codigo="SIM-006",
            descripcion="Artroscopia rodilla",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico", "consentimiento_informado"],
            copago_euros=0.0,
            plazo_respuesta_horas=72,
            notas="DATO SIMULADO — validar con Sanitas en Fase 0",
        ),
    },
    # Resto de los 20-30 procedimientos top — rellenar en Fase 0
    # con el Google Sheet de Isabella validado por HM.
}


def get_codigo(
    procedimiento_sim_id: str,
    tipo_poliza: str,
) -> Optional[CodigoSanitas]:
    """Devuelve el código Sanitas para un procedimiento y póliza.

    Devuelve None si el procedimiento no está en el catálogo.
    None → HITL obligatorio (el agente nunca falla silenciosamente).
    """
    procedimiento = CODIGOS.get(procedimiento_sim_id)
    if not procedimiento:
        return None
    return procedimiento.get(tipo_poliza)


def requiere_autorizacion(
    procedimiento_sim_id: str,
    tipo_poliza: str,
) -> bool:
    """True si requiere autorización previa.

    Safe default: True si el procedimiento no está en el catálogo.
    Mejor pedir una autorización innecesaria que no pedirla.
    """
    codigo = get_codigo(procedimiento_sim_id, tipo_poliza)
    if codigo is None:
        return True
    return codigo.requiere_autorizacion


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
