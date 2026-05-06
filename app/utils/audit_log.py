"""AuditLogger — sec 10 del handoff.

Cada acción del sistema queda registrada con hash SHA256 encadenado
al anterior. Permite detectar manipulación posterior (regla 7 sec 19:
"el audit log es sagrado").

Compliance AI Act:
- Trazabilidad completa por paso
- Inmutabilidad criptográfica (manipulación detectable)
- Identificación del modelo usado (modelo_usado)
- Versión del calculador (version_calculador)
- Marca explícita de intervención humana (hitl_intervencion)

Estrategia:
- Durante la ejecución del grafo, los nodos añaden entries SIN hash
  (sólo metadata). Esto es seguro porque el state no se persiste.
- Al final, AuditLogger.persistir_cadena() computa los hashes en orden
  y los guarda en DB. La cadena es inmutable a partir de ese momento.
- AuditLogger.verificar_integridad() recompute los hashes y compara
  con los persistidos — cualquier modificación posterior se detecta.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def _parse_iso(timestamp_str: str) -> datetime:
    """Parsea un timestamp ISO con timezone."""
    return datetime.fromisoformat(timestamp_str)

GENESIS_HASH = "GENESIS"
HASH_VERSION_CALCULADOR_DEFAULT = "1.0.0-simulado"


def construir_entrada(
    autorizacion_id: Optional[str],
    accion: str,
    actor: str,
    datos_entrada: dict,
    datos_salida: dict,
    confidence: float = 1.0,
    modelo_usado: Optional[str] = None,
    hitl_intervencion: bool = False,
    version_calculador: str = HASH_VERSION_CALCULADOR_DEFAULT,
) -> dict:
    """Construye una entrada de audit log (sin hash todavía).

    Los hashes se computan al persistir la cadena completa para garantizar
    el orden correcto del encadenamiento.
    """
    return {
        "autorizacion_id": autorizacion_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "accion": accion,
        "actor": actor,
        "resultado": datos_salida.get("estado", "desconocido"),
        "datos_entrada": datos_entrada,
        "datos_salida": datos_salida,
        "confidence_score": confidence,
        "modelo_usado": modelo_usado,
        "version_calculador": version_calculador,
        "hitl_intervencion": hitl_intervencion,
    }


def _calcular_hash(entrada_para_hash: dict) -> str:
    """SHA256 de la entrada serializada con sort_keys para reproducibilidad."""
    serializado = json.dumps(entrada_para_hash, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def _hashable(entrada: dict, hash_previo: str) -> dict:
    """Versión de la entrada que se incluye en el hash.

    Excluye hash_sha256 (que es el resultado) e incluye hash_previo.
    """
    return {
        "autorizacion_id": str(entrada.get("autorizacion_id") or ""),
        "timestamp": entrada["timestamp"],
        "accion": entrada["accion"],
        "actor": entrada["actor"],
        "resultado": entrada.get("resultado"),
        "datos_entrada": entrada.get("datos_entrada"),
        "datos_salida": entrada.get("datos_salida"),
        "confidence_score": entrada.get("confidence_score"),
        "modelo_usado": entrada.get("modelo_usado"),
        "version_calculador": entrada.get("version_calculador"),
        "hitl_intervencion": entrada.get("hitl_intervencion", False),
        "hash_previo": hash_previo,
    }


class AuditLogger:
    """Persiste cadenas de audit entries con SHA256 encadenado."""

    def __init__(self, db: Session):
        self.db = db

    def persistir_cadena(
        self,
        autorizacion_id: str,
        entries: list[dict],
    ) -> list[str]:
        """Persiste las entries en orden encadenando SHA256.

        Cada entry usa el hash_sha256 de la previa como hash_previo.
        La primera usa GENESIS (o el hash del último audit existente
        para esa autorizacion_id, si hay).

        Returns: lista de hashes en orden.
        """
        hash_previo = self._ultimo_hash(autorizacion_id)
        hashes: list[str] = []

        for entry in entries:
            entrada_para_hash = _hashable(entry, hash_previo)
            hash_actual = _calcular_hash(entrada_para_hash)

            audit_row = AuditLog(
                autorizacion_id=autorizacion_id if autorizacion_id else None,
                # Pasar timestamp explícito para que coincida con el hashado
                timestamp=_parse_iso(entry["timestamp"]),
                accion=entry["accion"],
                actor=entry["actor"],
                resultado=entry.get("resultado"),
                datos_entrada=entry.get("datos_entrada"),
                datos_salida=entry.get("datos_salida"),
                confidence_score=entry.get("confidence_score"),
                hash_sha256=hash_actual,
                hash_previo=hash_previo,
                modelo_usado=entry.get("modelo_usado"),
                version_calculador=entry.get("version_calculador"),
                hitl_intervencion=entry.get("hitl_intervencion", False),
            )
            self.db.add(audit_row)

            hashes.append(hash_actual)
            hash_previo = hash_actual

        self.db.flush()
        return hashes

    def _ultimo_hash(self, autorizacion_id: str) -> str:
        """Devuelve el hash de la última entrada para extender la cadena.

        Si no hay entradas previas → GENESIS.
        """
        ultimo = (
            self.db.query(AuditLog)
            .filter(AuditLog.autorizacion_id == autorizacion_id)
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        return ultimo.hash_sha256 if ultimo else GENESIS_HASH

    def listar(self, autorizacion_id: str) -> list[AuditLog]:
        """Lista las entries de una autorización en orden cronológico."""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.autorizacion_id == autorizacion_id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )

    def verificar_integridad(self, autorizacion_id: str) -> dict:
        """Recompute los hashes y detecta manipulación.

        Returns dict con:
        - integro: bool
        - total_entries: int
        - entries_invalidas: list[dict] con id, accion, hash_esperado, hash_real
        """
        entries = self.listar(autorizacion_id)
        invalidas: list[dict] = []
        hash_previo = GENESIS_HASH

        for entry in entries:
            entrada_para_hash = {
                "autorizacion_id": str(entry.autorizacion_id or ""),
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "accion": entry.accion,
                "actor": entry.actor,
                "resultado": entry.resultado,
                "datos_entrada": entry.datos_entrada,
                "datos_salida": entry.datos_salida,
                "confidence_score": float(entry.confidence_score) if entry.confidence_score is not None else None,
                "modelo_usado": entry.modelo_usado,
                "version_calculador": entry.version_calculador,
                "hitl_intervencion": entry.hitl_intervencion,
                "hash_previo": entry.hash_previo,
            }
            hash_esperado = _calcular_hash(entrada_para_hash)

            if hash_esperado != entry.hash_sha256 or entry.hash_previo != hash_previo:
                invalidas.append(
                    {
                        "id": str(entry.id),
                        "accion": entry.accion,
                        "hash_esperado": hash_esperado,
                        "hash_real": entry.hash_sha256,
                        "hash_previo_esperado": hash_previo,
                        "hash_previo_real": entry.hash_previo,
                    }
                )

            hash_previo = entry.hash_sha256

        return {
            "integro": not invalidas,
            "total_entries": len(entries),
            "entries_invalidas": invalidas,
        }
