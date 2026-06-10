"""Tests Fase 4 — flujo HITL.

Criterio: supervisor puede ver cola y aprobar/rechazar desde el navegador.
Verificamos contrato del endpoint que el dashboard consume.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.agent.llm_client import LLMClient
from app.agent.nodes import set_llm_client
from app.main import app
from app.models.database import SessionLocal


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
def client(auth_admin):
    return TestClient(app)


@pytest.fixture
def autorizacion_pendiente_hitl(client) -> str:
    """Crea una autorización que cae en cola HITL (orden incompleta)."""
    resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": "Paciente sin aseguradora", "modo": "mock"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["hitl_requerido"] is True
    return data["autorizacion_id"]


# ---------------------------------------------------------------------------
# Aprobar
# ---------------------------------------------------------------------------


def test_hitl_aprobar_actualiza_estado(client, autorizacion_pendiente_hitl):
    autorizacion_id = autorizacion_pendiente_hitl
    resp = client.post(
        f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
        json={
            "decision": "aprobar",
            "revisor": "isabella@soberania.eu",
            "notas": "Aseguradora aclarada por teléfono",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["estado"] == "aprobado_hitl"
    assert data["hitl_decision"] == "aprobar"
    assert data["hitl_revisor"] == "isabella@soberania.eu"
    assert data["hitl_notas"] == "Aseguradora aclarada por teléfono"
    assert data["hitl_revisado_at"] is not None


def test_hitl_rechazar_actualiza_estado(client, autorizacion_pendiente_hitl):
    resp = client.post(
        f"/api/v1/autorizaciones/{autorizacion_pendiente_hitl}/hitl",
        json={"decision": "rechazar", "revisor": "isabella", "notas": "Datos insuficientes"},
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "rechazado_hitl"


def test_hitl_mas_info_actualiza_estado(client, autorizacion_pendiente_hitl):
    resp = client.post(
        f"/api/v1/autorizaciones/{autorizacion_pendiente_hitl}/hitl",
        json={"decision": "mas_info", "revisor": "isabella"},
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "informacion_adicional_requerida"


# ---------------------------------------------------------------------------
# Audit registra intervención humana
# ---------------------------------------------------------------------------


def test_hitl_aprobar_anade_audit_entry_con_intervencion_humana(
    client, autorizacion_pendiente_hitl
):
    autorizacion_id = autorizacion_pendiente_hitl

    audit_antes = client.get(f"/api/v1/audit/{autorizacion_id}").json()
    entries_antes = audit_antes["total_entries"]

    client.post(
        f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
        json={"decision": "aprobar", "revisor": "isabella"},
    )

    audit_despues = client.get(f"/api/v1/audit/{autorizacion_id}").json()
    assert audit_despues["total_entries"] == entries_antes + 1
    assert audit_despues["integro"] is True

    # La nueva entrada es la del HITL, marcada como intervención humana
    nueva = audit_despues["entries"][-1]
    assert nueva["accion"] == "hitl_aprobar"
    assert nueva["actor"] == "hitl_supervisor:isabella"
    assert nueva["hitl_intervencion"] is True
    assert nueva["modelo_usado"] == "hitl_human"


def test_hitl_audit_mantiene_cadena_sha256(client, autorizacion_pendiente_hitl):
    autorizacion_id = autorizacion_pendiente_hitl
    client.post(
        f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
        json={"decision": "rechazar", "revisor": "isabella"},
    )
    audit = client.get(f"/api/v1/audit/{autorizacion_id}").json()
    assert audit["integro"] is True

    entries = audit["entries"]
    # La nueva entrada extiende la cadena: su hash_previo es el último
    # hash antes de su inserción
    assert entries[-1]["hash_previo"] == entries[-2]["hash_sha256"]


# ---------------------------------------------------------------------------
# Reglas de error
# ---------------------------------------------------------------------------


def test_hitl_no_se_puede_decidir_dos_veces(client, autorizacion_pendiente_hitl):
    autorizacion_id = autorizacion_pendiente_hitl
    primera = client.post(
        f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
        json={"decision": "aprobar", "revisor": "isabella"},
    )
    assert primera.status_code == 200

    segunda = client.post(
        f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
        json={"decision": "rechazar", "revisor": "isabella"},
    )
    assert segunda.status_code == 409
    assert segunda.json()["detail"] == "ya_decidido"


def test_hitl_autorizacion_inexistente_404(client):
    resp = client.post(
        "/api/v1/autorizaciones/00000000-0000-0000-0000-000000000000/hitl",
        json={"decision": "aprobar", "revisor": "isabella"},
    )
    assert resp.status_code == 404


def test_hitl_decision_invalida_422(client, autorizacion_pendiente_hitl):
    resp = client.post(
        f"/api/v1/autorizaciones/{autorizacion_pendiente_hitl}/hitl",
        json={"decision": "tal_vez", "revisor": "isabella"},
    )
    assert resp.status_code == 422  # validación pydantic


# ---------------------------------------------------------------------------
# Cola
# ---------------------------------------------------------------------------


def test_pendientes_excluye_decididas(client, autorizacion_pendiente_hitl):
    autorizacion_id = autorizacion_pendiente_hitl
    pendientes_antes = client.get("/api/v1/autorizaciones/pendientes").json()
    assert any(p["id"] == autorizacion_id for p in pendientes_antes)

    client.post(
        f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
        json={"decision": "aprobar", "revisor": "isabella"},
    )

    pendientes_despues = client.get("/api/v1/autorizaciones/pendientes").json()
    assert not any(p["id"] == autorizacion_id for p in pendientes_despues)
