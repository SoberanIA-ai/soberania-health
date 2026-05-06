"""Clase abstracta para conectores de aseguradoras.

Cada aseguradora soportada tiene su connector concreto (sanitas, adeslas, dkv).
El MockConnector simula el comportamiento para demos sin credenciales.
"""
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """Contrato común para todos los conectores."""

    @abstractmethod
    async def enviar(self, solicitud: dict) -> dict:
        """Envía una solicitud de autorización a la aseguradora.

        Returns:
            dict con keys:
            - estado: "aprobado" | "informacion_adicional" | "denegado"
            - referencia: identificador de la solicitud
            - numero_autorizacion: solo si estado == "aprobado"
            - informacion_requerida: list, solo si estado == "informacion_adicional"
            - motivo: str, solo si estado == "denegado"
            - mensaje: descripción human-readable
        """
        ...
