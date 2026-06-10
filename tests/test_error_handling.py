"""Tests de manejo de errores — fallos en LLM/conector → error_procesamiento.

Sec "Robustez" del audit: las llamadas a servicios externos (LLM, conector
de aseguradora) pueden fallar (timeout, 5xx, credenciales caducadas...).
Verificamos que un fallo NO produce un 500 sin rastro: el grafo transiciona
a `error_procesamiento`, queda registrado en el audit log con su propia
entrada (sec 10 AI Act) y la autorización se marca para revisión humana.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.agent.llm_client import LLMClient
from app.agent.nodes import set_llm_client
from app.integrations.hl7_mock import get_orden_ejemplo
from app.main import app
from app.models.database import SessionLocal


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


@pytest.fixture(autouse=True)
def restaurar_llm_client():
    """Asegura que un LLM roto en un test no contamina los siguientes."""
    yield
    set_llm_client(LLMClient(api_key=""))


@pytest.fixture
def client(auth_admin):
    return TestClient(app)


class _LLMClientRoto(LLMClient):
    """Simula una caída del proveedor LLM (timeout, 5xx, etc.)."""

    async def parse_orden_medica(self, orden_raw: str) -> dict:
        raise RuntimeError("Mistral API no disponible (simulado)")


def test_fallo_llm_transiciona_a_error_procesamiento(client):
    set_llm_client(_LLMClientRoto(api_key=""))

    resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["estado"] == "error_procesamiento"
    assert data["hitl_requerido"] is True

    aut = client.get(f"/api/v1/autorizaciones/{data['autorizacion_id']}").json()
    assert aut["estado"] == "error_procesamiento"
    assert aut["razon_hitl"]

    audit = client.get(f"/api/v1/audit/{data['autorizacion_id']}").json()
    assert audit["integro"] is True
    entry = next(e for e in audit["entries"] if e["accion"] == "parse_orden_medica")
    assert entry["datos_salida"]["estado"] == "error_procesamiento"
    assert entry["datos_salida"]["modo_inferencia"] == "error"


def test_fallo_conector_transiciona_a_error_procesamiento(client, monkeypatch):
    import app.agent.nodes as nodes_mod

    class _ConnectorRoto:
        def __init__(self, **kwargs):
            pass

        async def enviar(self, payload):
            raise RuntimeError("Portal aseguradora no disponible (simulado)")

    monkeypatch.setattr(nodes_mod, "MockConnector", _ConnectorRoto)
    set_llm_client(LLMClient(api_key=""))

    resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["estado"] == "error_procesamiento"
    assert data["hitl_requerido"] is True

    audit = client.get(f"/api/v1/audit/{data['autorizacion_id']}").json()
    entry = next(e for e in audit["entries"] if e["accion"] == "enviar_solicitud")
    assert entry["datos_salida"]["estado"] == "error_procesamiento"
    assert entry["datos_salida"]["modo_inferencia"] == "error"


def test_error_procesamiento_aparece_en_pendientes_hitl(client):
    set_llm_client(_LLMClientRoto(api_key=""))

    resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    aid = resp.json()["autorizacion_id"]

    pendientes = client.get("/api/v1/autorizaciones/pendientes").json()
    assert any(p["id"] == aid for p in pendientes)
