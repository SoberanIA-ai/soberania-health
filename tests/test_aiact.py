"""Tests del compliance AI Act — endpoints de auditoría enriquecida.

Verifica:
- razon_decision en cada entry del audit log
- modelo_version y modo_inferencia en datos_salida
- Endpoint /aiact-report con estructura completa
- HITL registra revisor, coincide_con_agente, tiempo_en_cola
- Endpoint /metricas-aiact con porcentajes y tiempos
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
def client(monkeypatch):
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Explicabilidad: razon_decision
# ---------------------------------------------------------------------------


def test_cada_entry_tiene_razon_decision(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    ).json()
    audit = client.get(f"/api/v1/audit/{aut['autorizacion_id']}").json()

    for entry in audit["entries"]:
        ds = entry["datos_salida"]
        assert ds.get("razon_decision"), (
            f"Falta razon_decision en {entry['accion']}"
        )


def test_parser_razon_menciona_campos_extraidos(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    ).json()
    audit = client.get(f"/api/v1/audit/{aut['autorizacion_id']}").json()

    parse = next(e for e in audit["entries"] if e["accion"] == "parse_orden_medica")
    razon = parse["datos_salida"]["razon_decision"]
    assert "campos" in razon.lower()
    assert "confidence" in razon.lower()


def test_parser_datos_entrada_tiene_orden_original_y_campos(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    ).json()
    audit = client.get(f"/api/v1/audit/{aut['autorizacion_id']}").json()

    parse = next(e for e in audit["entries"] if e["accion"] == "parse_orden_medica")
    de = parse["datos_entrada"]
    assert "orden_original" in de
    assert get_orden_ejemplo("ORD-001") in de["orden_original"]
    assert isinstance(de.get("campos_extraidos"), dict)
    assert isinstance(de.get("campos_faltantes"), list)


# ---------------------------------------------------------------------------
# 2. Trazabilidad del modelo
# ---------------------------------------------------------------------------


def test_parser_registra_modelo_version_y_modo(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    ).json()
    audit = client.get(f"/api/v1/audit/{aut['autorizacion_id']}").json()

    parse = next(e for e in audit["entries"] if e["accion"] == "parse_orden_medica")
    ds = parse["datos_salida"]
    assert ds["modelo_version"] == "mock-heuristic-v1"
    assert ds["modo_inferencia"] == "mock"


def test_calculador_registra_modelo_deterministic(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    ).json()
    audit = client.get(f"/api/v1/audit/{aut['autorizacion_id']}").json()

    verify = next(e for e in audit["entries"] if e["accion"] == "verificar_cobertura")
    ds = verify["datos_salida"]
    assert ds["modo_inferencia"] == "deterministic"
    assert "calculador" in ds["modelo_version"]


# ---------------------------------------------------------------------------
# 3. Intervención humana
# ---------------------------------------------------------------------------


def test_hitl_registra_metadata_aiact(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": "Paciente sin aseguradora", "modo": "mock"},
    ).json()
    aid = aut["autorizacion_id"]

    client.post(
        f"/api/v1/autorizaciones/{aid}/hitl",
        json={"decision": "aprobar", "revisor": "isabella@soberania.eu", "notas": "OK"},
    )

    audit = client.get(f"/api/v1/audit/{aid}").json()
    # Distinguir hitl_check (agente) de hitl_aprobar/rechazar/mas_info (humano)
    hitl = next(
        e for e in audit["entries"]
        if e["accion"] in ("hitl_aprobar", "hitl_rechazar", "hitl_mas_info")
    )
    ds = hitl["datos_salida"]

    assert ds["revisor_nombre"] == "isabella@soberania.eu"
    assert ds["decision_humana"] == "aprobar"
    assert "coincide_con_agente" in ds
    assert isinstance(ds["coincide_con_agente"], bool)
    assert ds["notas_revisor"] == "OK"
    assert isinstance(ds["tiempo_en_cola_segundos"], (int, float))
    assert ds["tiempo_en_cola_segundos"] >= 0


# ---------------------------------------------------------------------------
# 4. Endpoint /aiact-report
# ---------------------------------------------------------------------------


def test_aiact_report_estructura_completa(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"},
    ).json()
    report = client.get(
        f"/api/v1/audit/{aut['autorizacion_id']}/aiact-report"
    ).json()

    # Top-level keys
    assert set(report.keys()) >= {"autorizacion", "audit", "intervencion_humana", "compliance"}

    # Autorización
    a = report["autorizacion"]
    assert a["id"] == aut["autorizacion_id"]
    assert a["estado_final"] == "autorizado"
    assert a["procedimiento_codigo"] == "SIM-001"
    assert isinstance(a["tiempo_total_segundos"], (int, float))

    # Audit
    aud = report["audit"]
    assert aud["integro"] is True
    assert aud["total_pasos"] >= 6
    for paso in aud["pasos"]:
        assert paso["razon_decision"]
        assert paso["modelo_version"]
        assert paso["tipo"] in ("llm", "python", "hitl")
        assert paso["hash_sha256"]

    # Sin HITL en este caso
    assert report["intervencion_humana"] is None

    # Compliance
    assert report["compliance"]["ai_act"] == "compliant"


def test_aiact_report_con_intervencion_humana(client):
    aut = client.post(
        "/api/v1/autorizaciones/procesar",
        json={"orden_h17": "Paciente sin aseguradora", "modo": "mock"},
    ).json()
    aid = aut["autorizacion_id"]
    client.post(
        f"/api/v1/autorizaciones/{aid}/hitl",
        json={"decision": "rechazar", "revisor": "supervisor", "notas": "Datos incompletos"},
    )

    report = client.get(f"/api/v1/audit/{aid}/aiact-report").json()

    intervencion = report["intervencion_humana"]
    assert intervencion is not None
    assert intervencion["revisor"] == "supervisor"
    assert intervencion["decision"] == "rechazar"
    assert "coincide_con_agente" in intervencion
    assert intervencion["notas"] == "Datos incompletos"


def test_aiact_report_404_si_no_existe(client):
    r = client.get(
        "/api/v1/audit/00000000-0000-0000-0000-000000000000/aiact-report"
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# 5. Endpoint /metricas-aiact
# ---------------------------------------------------------------------------


def test_metricas_aiact_estructura(client):
    # Crear varias autorizaciones
    client.post("/api/v1/autorizaciones/procesar",
                json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"})
    aut2 = client.post("/api/v1/autorizaciones/procesar",
                       json={"orden_h17": "Paciente sin aseguradora", "modo": "mock"}).json()
    client.post(f"/api/v1/autorizaciones/{aut2['autorizacion_id']}/hitl",
                json={"decision": "rechazar", "revisor": "isa", "notas": ""})

    m = client.get("/api/v1/autorizaciones/metricas-aiact").json()

    assert m["total_autorizaciones"] >= 2
    assert m["con_supervision_humana"] >= 1
    assert 0.0 <= m["porcentaje_supervision"] <= 1.0
    assert m["decisiones_humanas_registradas"] >= 1
    assert "porcentaje_contradicciones" in m
    assert "tiempo_medio_revision_segundos" in m


# ---------------------------------------------------------------------------
# 6. Endpoint listar todas
# ---------------------------------------------------------------------------


def test_listar_todas_devuelve_autorizadas_y_pendientes(client):
    client.post("/api/v1/autorizaciones/procesar",
                json={"orden_h17": get_orden_ejemplo("ORD-001"), "modo": "mock"})  # → autorizada
    client.post("/api/v1/autorizaciones/procesar",
                json={"orden_h17": "Paciente sin aseguradora", "modo": "mock"})  # → HITL

    todas = client.get("/api/v1/autorizaciones/").json()
    estados = {a["estado"] for a in todas}
    assert "autorizado" in estados
    assert "pendiente_hitl" in estados
    assert len(todas) == 2
