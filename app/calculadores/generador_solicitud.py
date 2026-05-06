"""Genera el formulario de solicitud de autorización
en el formato específico de cada aseguradora.

Python puro — sin LLM, sin I/O externo.

DATA_STATUS = "SIMULADO"
Los campos del formulario son estimados de investigación pública.

En producción los formularios se obtienen de:
- Acceso directo a los portales de cada aseguradora (Fase 0)
- Isabella documenta cada campo real durante investigación
- HM valida los campos con su back-office operativo
- Si la aseguradora tiene API: usar spec oficial de la API

Riesgo: si un campo obligatorio falta o tiene formato incorrecto,
la aseguradora rechaza la solicitud. Por eso el mock_connector
simula rechazos para entrenar el flujo de corrección.
"""
from datetime import date
from typing import Callable

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"


def generar(
    aseguradora: str,
    datos_paciente: dict,
    datos_medico: dict,
    procedimiento_cie10: str,
    procedimiento_codigo_aseguradora: str,
    documentacion_adjunta: list[str],
    urgente: bool = False,
) -> dict:
    """Genera el payload de solicitud.

    En mock mode → formato simulado para demo.
    En modo real → formato exacto del portal de la aseguradora.
    """
    generadores: dict[str, Callable] = {
        "sanitas": _generar_sanitas,
        "adeslas": _generar_adeslas,
        "dkv": _generar_dkv,
    }

    generador = generadores.get(aseguradora.lower())
    if not generador:
        raise ValueError(f"Aseguradora no soportada: {aseguradora}")

    return generador(
        datos_paciente,
        datos_medico,
        procedimiento_cie10,
        procedimiento_codigo_aseguradora,
        documentacion_adjunta,
        urgente,
    )


def _generar_sanitas(
    datos_paciente: dict,
    datos_medico: dict,
    cie10: str,
    codigo_sanitas: str,
    documentacion: list[str],
    urgente: bool,
) -> dict:
    """FORMATO SIMULADO.

    Campos basados en investigación pública del portal Sanitas.
    Confirmar campos exactos, nombres y formatos en Fase 0.
    El mock_connector acepta este formato para la demo.
    """
    return {
        "_data_status": DATA_STATUS,  # eliminado en producción
        "tipo": "solicitud_autorizacion",
        "aseguradora": "sanitas",
        "version_formato": "simulado-1.0",  # actualizar en Fase 0
        "datos": {
            "paciente": {
                "nombre": datos_paciente.get("nombre"),
                "apellidos": datos_paciente.get("apellidos"),
                "numero_poliza": datos_paciente.get("poliza"),
                "fecha_nacimiento": datos_paciente.get("fecha_nacimiento"),
            },
            "medico_solicitante": {
                "nombre": datos_medico.get("nombre"),
                "numero_colegiado": datos_medico.get("numero_colegiado"),
                "especialidad": datos_medico.get("especialidad"),
            },
            "procedimiento": {
                "codigo_cie10": cie10,
                "codigo_sanitas": codigo_sanitas,  # SIMULADO hasta Fase 0
                "fecha_solicitud": date.today().isoformat(),
                "urgente": urgente,
            },
            "documentacion_adjunta": documentacion,
        },
    }


def _generar_adeslas(
    datos_paciente: dict,
    datos_medico: dict,
    cie10: str,
    codigo_adeslas: str,
    documentacion: list[str],
    urgente: bool,
) -> dict:
    """FORMATO SIMULADO — completar en Fase 0.

    Adeslas puede tener un formato de formulario diferente a Sanitas.
    Investigar durante Fase 0 si tiene API o solo portal web.
    """
    return {
        "_data_status": DATA_STATUS,
        "tipo": "solicitud_autorizacion",
        "aseguradora": "adeslas",
        "version_formato": "simulado-1.0",
        "datos": {
            "paciente": {
                "nombre": datos_paciente.get("nombre"),
                "apellidos": datos_paciente.get("apellidos"),
                "numero_poliza": datos_paciente.get("poliza"),
                "fecha_nacimiento": datos_paciente.get("fecha_nacimiento"),
            },
            "medico_solicitante": {
                "nombre": datos_medico.get("nombre"),
                "numero_colegiado": datos_medico.get("numero_colegiado"),
                "especialidad": datos_medico.get("especialidad"),
            },
            "procedimiento": {
                "codigo_cie10": cie10,
                "codigo_adeslas": codigo_adeslas,
                "fecha_solicitud": date.today().isoformat(),
                "urgente": urgente,
            },
            "documentacion_adjunta": documentacion,
        },
    }


def _generar_dkv(
    datos_paciente: dict,
    datos_medico: dict,
    cie10: str,
    codigo_dkv: str,
    documentacion: list[str],
    urgente: bool,
) -> dict:
    """FORMATO SIMULADO — completar en Fase 0.

    DKV tiene acuerdo activo con HM (confirmado 2026).
    Priorizar API si existe, RPA si no.
    """
    return {
        "_data_status": DATA_STATUS,
        "tipo": "solicitud_autorizacion",
        "aseguradora": "dkv",
        "version_formato": "simulado-1.0",
        "datos": {
            "paciente": {
                "nombre": datos_paciente.get("nombre"),
                "apellidos": datos_paciente.get("apellidos"),
                "numero_poliza": datos_paciente.get("poliza"),
                "fecha_nacimiento": datos_paciente.get("fecha_nacimiento"),
            },
            "medico_solicitante": {
                "nombre": datos_medico.get("nombre"),
                "numero_colegiado": datos_medico.get("numero_colegiado"),
                "especialidad": datos_medico.get("especialidad"),
            },
            "procedimiento": {
                "codigo_cie10": cie10,
                "codigo_dkv": codigo_dkv,
                "fecha_solicitud": date.today().isoformat(),
                "urgente": urgente,
            },
            "documentacion_adjunta": documentacion,
        },
    }


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
