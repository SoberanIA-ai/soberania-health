"""Test suite E2E — sec 13 del handoff. Fase 5.

Criterio de done: 30/30 casos pasan en modo mock.

Carga los casos de data/casos_test/casos_e2e.json y los ejecuta via
AutorizacionService. Cada caso define sus expectations (aseguradora,
código, hitl_requerido, estado_final, etc.).

Casos están alineados con DATA_STATUS=SIMULADO:
- Sanitas: 4 happy paths (procedimientos en catálogo) + 6 HITL
- Adeslas / DKV: todos HITL hasta Fase 0 con HM (catálogo vacío)
"""
import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.agent.llm_client import LLMClient
from app.agent.nodes import set_llm_client
from app.models.database import SessionLocal
from app.services.autorizacion_service import AutorizacionService

CASOS_PATH = Path(__file__).parent.parent / "data" / "casos_test" / "casos_e2e.json"


def _load_casos() -> list[dict]:
    with CASOS_PATH.open() as f:
        return json.load(f)["casos"]


CASOS = _load_casos()


@pytest.fixture(autouse=True)
def mock_llm():
    set_llm_client(LLMClient(api_key=""))


@pytest.fixture(autouse=True)
def limpiar_db():
    session = SessionLocal()
    try:
        session.execute(text("TRUNCATE TABLE audit_log, autorizaciones CASCADE"))
        session.commit()
        yield
        session.execute(text("TRUNCATE TABLE audit_log, autorizaciones CASCADE"))
        session.commit()
    finally:
        session.close()


@pytest.fixture
def mock_connector_determinista(monkeypatch):
    """MockConnector con seed=42 → cae en bucket aprobado para casos happy path."""
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )


def test_archivo_casos_tiene_30_entradas():
    assert len(CASOS) == 30, f"El handoff (sec 13.1) define 30 casos; encontré {len(CASOS)}"


def test_distribucion_10_por_aseguradora():
    """10 Sanitas (caso_001-010) + 10 Adeslas (011-020) + 10 DKV (021-030) — sec 13.1."""
    def numero(caso): return int(caso["id"].replace("caso_", ""))
    sanitas = [c for c in CASOS if 1 <= numero(c) <= 10]
    adeslas = [c for c in CASOS if 11 <= numero(c) <= 20]
    dkv = [c for c in CASOS if 21 <= numero(c) <= 30]
    assert len(sanitas) == 10
    assert len(adeslas) == 10
    assert len(dkv) == 10


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
@pytest.mark.asyncio
async def test_caso_e2e(caso, mock_connector_determinista):
    """Ejecuta un caso end-to-end y verifica todas sus expectations."""
    db = SessionLocal()
    try:
        service = AutorizacionService(db)
        autorizacion = await service.procesar(
            orden_raw=caso["input"]["orden_h17"],
            modo=caso["input"]["modo"],
        )

        expected = caso["expected"]

        # Estado final
        if "estado_final" in expected:
            assert autorizacion.estado == expected["estado_final"], (
                f"{caso['id']}: estado esperado {expected['estado_final']}, "
                f"got {autorizacion.estado}"
            )

        # HITL
        if "hitl_requerido" in expected:
            assert autorizacion.hitl_requerido is expected["hitl_requerido"], (
                f"{caso['id']}: hitl_requerido esperado {expected['hitl_requerido']}, "
                f"got {autorizacion.hitl_requerido}"
            )

        # Aseguradora
        if "aseguradora" in expected:
            assert autorizacion.aseguradora == expected["aseguradora"], (
                f"{caso['id']}: aseguradora esperada {expected['aseguradora']}, "
                f"got {autorizacion.aseguradora}"
            )

        # Tipo de póliza
        if "tipo_poliza" in expected:
            assert autorizacion.poliza_tipo == expected["tipo_poliza"], (
                f"{caso['id']}: tipo_poliza esperado {expected['tipo_poliza']}, "
                f"got {autorizacion.poliza_tipo}"
            )

        # Código de procedimiento
        if "procedimiento_codigo" in expected:
            assert autorizacion.procedimiento_codigo == expected["procedimiento_codigo"], (
                f"{caso['id']}: código esperado {expected['procedimiento_codigo']}, "
                f"got {autorizacion.procedimiento_codigo}"
            )

        # Cobertura
        if "cobertura_verificada" in expected:
            assert autorizacion.cobertura_verificada is expected["cobertura_verificada"]

        # Requiere autorización
        if "requiere_autorizacion" in expected:
            assert autorizacion.requiere_autorizacion is expected["requiere_autorizacion"]

        # Confidence mínima
        if "confidence_min" in expected:
            assert float(autorizacion.confidence_score or 0) >= expected["confidence_min"], (
                f"{caso['id']}: confidence_score "
                f"{autorizacion.confidence_score} < {expected['confidence_min']}"
            )

        # Urgente
        if "urgente" in expected:
            assert (autorizacion.urgencia == "urgente") is expected["urgente"]

        # Audit log siempre debe quedar registrado e íntegro
        from app.utils.audit_log import AuditLogger
        integridad = AuditLogger(db).verificar_integridad(str(autorizacion.id))
        assert integridad["integro"] is True, (
            f"{caso['id']}: audit log no íntegro: {integridad['entries_invalidas']}"
        )
        assert integridad["total_entries"] >= 1
    finally:
        db.close()
