"""MockConnector — sec 9.1 del handoff.

Simula el comportamiento de un portal de aseguradora.
Usa para demos sin credenciales reales.

Comportamiento:
- 80% de las solicitudes se aprueban automáticamente
- 15% piden información adicional
- 5% se deniegan (para mostrar el flujo completo)

Determinístico por seed cuando se necesita reproducibilidad en tests.
"""
import asyncio
import random
from uuid import uuid4

from app.conectores.base_connector import BaseConnector


class MockConnector(BaseConnector):
    """Implementa BaseConnector con respuestas simuladas.

    Args:
        seed: Si se pasa, hace el output determinístico (para tests).
        latencia_segundos: Simula latencia de red (0 en tests).
    """

    def __init__(self, seed: int | None = None, latencia_segundos: float = 2.0):
        self._random = random.Random(seed) if seed is not None else random
        self.latencia_segundos = latencia_segundos

    async def enviar(self, solicitud: dict) -> dict:
        if self.latencia_segundos > 0:
            await asyncio.sleep(self.latencia_segundos)

        roll = self._random.random()
        referencia = f"MOCK-{uuid4().hex[:8].upper()}"

        if roll < 0.80:
            return {
                "estado": "aprobado",
                "referencia": referencia,
                "numero_autorizacion": f"AUTH-{uuid4().hex[:8].upper()}",
                "mensaje": "Autorización aprobada automáticamente",
            }
        if roll < 0.95:
            return {
                "estado": "informacion_adicional",
                "referencia": referencia,
                "informacion_requerida": ["historia_clinica_previa"],
                "mensaje": "Se requiere documentación adicional",
            }
        return {
            "estado": "denegado",
            "referencia": referencia,
            "motivo": "Procedimiento no cubierto por la póliza actual",
            "mensaje": "Solicitud denegada",
        }
