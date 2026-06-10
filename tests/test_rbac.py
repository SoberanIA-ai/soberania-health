"""Tests RBAC — sec "RBAC" del audit.

Antes de esta corrección, solo /hitl comprobaba el rol: cualquier usuario
autenticado (incluido `auditor`, pensado para solo-lectura) podía llamar a
/procesar, /pendientes, /reenviar o /metricas-aiact. Verificamos que cada
endpoint exige ahora el rol correcto (require_roles) y devuelve 403 para
roles no permitidos.
"""
import pytest
from sqlalchemy import text

from app.agent.llm_client import LLMClient
from app.agent.nodes import set_llm_client
from app.integrations.hl7_mock import get_orden_ejemplo
from app.models.database import SessionLocal

DUMMY_ID = "00000000-0000-0000-0000-000000000000"


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


# ---------------------------------------------------------------------------
# POST /procesar — recepcionista, supervisor, admin (NO auditor)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["recepcionista", "supervisor", "admin"])
def test_procesar_permitido_para_roles_operativos(client_as, rol):
    client = client_as(rol)
    resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    assert resp.status_code == 201, resp.text


def test_procesar_denegado_para_auditor(client_as):
    client = client_as("auditor")
    resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /pendientes — supervisor, admin (NO recepcionista, NO auditor)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["supervisor", "admin"])
def test_pendientes_permitido_para_supervision(client_as, rol):
    client = client_as(rol)
    resp = client.get("/api/v1/autorizaciones/pendientes")
    assert resp.status_code == 200


@pytest.mark.parametrize("rol", ["recepcionista", "auditor"])
def test_pendientes_denegado(client_as, rol):
    client = client_as(rol)
    resp = client.get("/api/v1/autorizaciones/pendientes")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /metricas-aiact — auditor, admin (NO recepcionista, NO supervisor)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["auditor", "admin"])
def test_metricas_aiact_permitido_para_auditoria(client_as, rol):
    client = client_as(rol)
    resp = client.get("/api/v1/autorizaciones/metricas-aiact")
    assert resp.status_code == 200


@pytest.mark.parametrize("rol", ["recepcionista", "supervisor"])
def test_metricas_aiact_denegado(client_as, rol):
    client = client_as(rol)
    resp = client.get("/api/v1/autorizaciones/metricas-aiact")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /{id}/hitl — supervisor, admin (NO recepcionista, NO auditor)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["recepcionista", "auditor"])
def test_hitl_denegado(client_as, rol):
    client = client_as(rol)
    resp = client.post(
        f"/api/v1/autorizaciones/{DUMMY_ID}/hitl",
        json={"decision": "aprobar", "revisor": "test"},
    )
    assert resp.status_code == 403


@pytest.mark.parametrize("rol", ["supervisor", "admin"])
def test_hitl_permitido_pero_404_si_no_existe(client_as, rol):
    client = client_as(rol)
    resp = client.post(
        f"/api/v1/autorizaciones/{DUMMY_ID}/hitl",
        json={"decision": "aprobar", "revisor": "test"},
    )
    # Pasa el check de rol; 404 porque la autorización no existe
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /{id}/reenviar — recepcionista, supervisor, admin (NO auditor)
# ---------------------------------------------------------------------------


def test_reenviar_denegado_para_auditor(client_as):
    client = client_as("auditor")
    resp = client.post(
        f"/api/v1/autorizaciones/{DUMMY_ID}/reenviar",
        json={"notas_adicionales": "", "archivos_adjuntos": []},
    )
    assert resp.status_code == 403


@pytest.mark.parametrize("rol", ["recepcionista", "supervisor", "admin"])
def test_reenviar_permitido_pero_404_si_no_existe(client_as, rol):
    client = client_as(rol)
    resp = client.post(
        f"/api/v1/autorizaciones/{DUMMY_ID}/reenviar",
        json={"notas_adicionales": "", "archivos_adjuntos": []},
    )
    # Pasa el check de rol; 404 porque la autorización no existe
    assert resp.status_code == 404
