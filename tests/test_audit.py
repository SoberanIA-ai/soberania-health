"""Tests Fase 3 — audit log SHA256 encadenado e integridad.

Criterio de done: cada acción del agente aparece en audit log con hash
SHA256 correcto.

Estos tests requieren DB postgres levantada (docker-compose up db).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.agent.llm_client import LLMClient
from app.agent.nodes import set_llm_client
from app.integrations.hl7_mock import get_orden_ejemplo
from app.main import app
from app.models.audit import AuditLog
from app.models.database import SessionLocal


@pytest.fixture(autouse=True)
def mock_llm():
    set_llm_client(LLMClient(api_key=""))


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def limpiar_db():
    """Limpia tablas antes y después de cada test."""
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
def client(monkeypatch):
    """TestClient con MockConnector determinístico."""
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST procesar → audit completo encadenado
# ---------------------------------------------------------------------------


def test_procesar_devuelve_resumen_y_persiste_audit(client, db):
    response = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["estado"] == "autorizado"
    assert data["numero_autorizacion"].startswith("AUTH-")

    autorizacion_id = data["autorizacion_id"]

    # Audit entries persistidas
    entries = (
        db.query(AuditLog)
        .filter(AuditLog.autorizacion_id == autorizacion_id)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )
    assert len(entries) >= 6  # parse, verify, generate, send, monitor, process, notify
    acciones = [e.accion for e in entries]
    assert "parse_orden_medica" in acciones
    assert "verificar_cobertura" in acciones
    assert "generar_solicitud" in acciones
    assert "enviar_solicitud" in acciones
    assert "procesar_respuesta" in acciones


def test_audit_log_hashes_encadenados_correctamente(client, db):
    response = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    autorizacion_id = response.json()["autorizacion_id"]

    entries = (
        db.query(AuditLog)
        .filter(AuditLog.autorizacion_id == autorizacion_id)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )
    # Primera entrada usa GENESIS
    assert entries[0].hash_previo == "GENESIS"
    # Cada entrada siguiente usa el hash de la previa
    for i in range(1, len(entries)):
        assert entries[i].hash_previo == entries[i - 1].hash_sha256
    # Todos los hashes son SHA256 hex (64 chars)
    for entry in entries:
        assert len(entry.hash_sha256) == 64
        assert all(c in "0123456789abcdef" for c in entry.hash_sha256)


def test_audit_log_endpoint_devuelve_integro_true(client):
    create_resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    autorizacion_id = create_resp.json()["autorizacion_id"]

    audit_resp = client.get(f"/api/v1/audit/{autorizacion_id}")
    assert audit_resp.status_code == 200
    data = audit_resp.json()
    assert data["integro"] is True
    assert data["total_entries"] >= 6
    assert data["entries_invalidas"] == []


# ---------------------------------------------------------------------------
# Detección de manipulación
# ---------------------------------------------------------------------------


def test_modificar_entry_se_detecta_como_manipulacion(client, db):
    """Modificar una entry en DB debe romper la verificación de integridad."""
    create_resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    autorizacion_id = create_resp.json()["autorizacion_id"]

    # Atacante manipula directamente la fila en DB
    db.execute(
        text(
            "UPDATE audit_log SET resultado = 'manipulado' "
            "WHERE autorizacion_id = :aid AND accion = 'parse_orden_medica'"
        ),
        {"aid": autorizacion_id},
    )
    db.commit()

    audit_resp = client.get(f"/api/v1/audit/{autorizacion_id}")
    data = audit_resp.json()
    assert data["integro"] is False
    assert len(data["entries_invalidas"]) >= 1
    # La entrada manipulada o las posteriores aparecen como inválidas
    acciones_invalidas = {
        next(
            (e["accion"] for e in data["entries"] if e["id"] == inv["id"]),
            None,
        )
        for inv in data["entries_invalidas"]
    }
    assert "parse_orden_medica" in acciones_invalidas


def test_aseguradora_no_soportada_genera_audit_pendiente_hitl(client, db):
    response = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": "Paciente: X. Aseguradora: Mapfre. RM rodilla", "modo": "mock"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["hitl_requerido"] is True
    assert data["estado"] == "pendiente_hitl"
    # No debe haberse enviado solicitud
    assert data["numero_autorizacion"] is None

    # Audit log se persiste también para casos HITL
    autorizacion_id = data["autorizacion_id"]
    audit = client.get(f"/api/v1/audit/{autorizacion_id}").json()
    assert audit["integro"] is True
    assert audit["total_entries"] >= 3  # parse, verify, hitl_check


def test_get_autorizacion_devuelve_detalle_completo(client):
    create_resp = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )
    autorizacion_id = create_resp.json()["autorizacion_id"]

    detail_resp = client.get(f"/api/v1/autorizaciones/{autorizacion_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["aseguradora"] == "sanitas"
    assert detail["procedimiento_codigo"] == "SIM-001"
    assert detail["estado"] == "autorizado"
    assert detail["numero_autorizacion"].startswith("AUTH-")
    assert detail["paciente_nombre"] is not None


def test_listar_pendientes_hitl(client):
    # Una orden que dispara HITL
    client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": "Paciente sin aseguradora", "modo": "mock"},
    )
    # Y una aprobada
    client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    )

    pendientes = client.get("/api/v1/autorizaciones/pendientes").json()
    assert len(pendientes) == 1
    assert pendientes[0]["hitl_requerido"] is True


def test_autorizacion_inexistente_devuelve_404(client):
    response = client.get("/api/v1/autorizaciones/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
