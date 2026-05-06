"""Tests de integración del agente LangGraph.

Criterio Fase 2: un caso simulado fluye de principio a fin en mock mode.
"""
import pytest

from app.agent.graph import construir_grafo
from app.agent.llm_client import LLMClient
from app.agent.nodes import set_llm_client
from app.agent.state import AuthorizationState
from app.integrations.hl7_mock import get_orden_ejemplo


@pytest.fixture(autouse=True)
def mock_llm():
    """Garantiza modo mock determinístico en todos los tests del agente."""
    set_llm_client(LLMClient(api_key=""))


@pytest.mark.asyncio
async def test_caso_001_flujo_completo_aprobado(monkeypatch):
    """Caso 1: Sanitas RM rodilla Más Salud Plus — flujo end-to-end aprobado."""
    # Forzar MockConnector determinístico (seed que cae en bucket "aprobado")
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )

    grafo = construir_grafo()
    initial: AuthorizationState = {
        "orden_raw": get_orden_ejemplo("ORD-001"),
        "modo": "mock",
    }

    final = await grafo.ainvoke(initial)

    # Datos extraídos correctamente
    datos = final["datos_estructurados"]
    assert datos["paciente_aseguradora"] == "Sanitas"
    assert datos["paciente_tipo_poliza"] == "mas_salud_plus"
    assert datos["procedimiento_cie10"] == "SIM_RM_RODILLA_DCHA"

    # Verificación de cobertura
    assert final["aseguradora"] == "sanitas"
    assert final["cobertura_verificada"] is True
    assert final["requiere_autorizacion"] is True
    assert final["confidence_score"] >= 0.80

    # Solicitud generada con código del calculador
    assert final["procedimiento_codigo"] == "SIM-001"
    assert final["solicitud_generada"]["aseguradora"] == "sanitas"

    # Aprobación de la aseguradora (mock determinístico)
    assert final["estado"] == "autorizado"
    assert final["numero_autorizacion"].startswith("AUTH-")
    assert final["solicitud_referencia"].startswith("MOCK-")

    # Audit log poblado
    assert len(final["audit_entries"]) == 1
    assert final["audit_entries"][0]["accion"] == "autorizacion_procesada"


@pytest.mark.asyncio
async def test_aseguradora_no_soportada_dispara_hitl(monkeypatch):
    """Una aseguradora desconocida debe terminar en pendiente_hitl, no enviarse."""
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )

    grafo = construir_grafo()
    final = await grafo.ainvoke(
        {
            "orden_raw": "Paciente: Test\nAseguradora: Mapfre\nProcedimiento: RM rodilla",
            "modo": "mock",
        }
    )

    assert final["estado"] == "pendiente_hitl"
    assert final["hitl_requerido"] is True
    # No debe haber numero_autorizacion porque no se envió
    assert not final.get("numero_autorizacion")


@pytest.mark.asyncio
async def test_orden_sin_aseguradora_dispara_hitl():
    """Orden sin aseguradora: el guardrail marca campo faltante → HITL."""
    grafo = construir_grafo()
    final = await grafo.ainvoke(
        {
            "orden_raw": "Paciente: Test sin aseguradora",
            "modo": "mock",
        }
    )

    assert final["hitl_requerido"] is True
    assert final["estado"] == "pendiente_hitl"
    assert final["confidence_score"] < 0.80


@pytest.mark.asyncio
async def test_audit_entry_contiene_modelo_y_confidence(monkeypatch):
    """El audit log debe registrar modelo usado y confidence (sec 10)."""
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )

    grafo = construir_grafo()
    final = await grafo.ainvoke(
        {"orden_raw": get_orden_ejemplo("ORD-001"), "modo": "mock"}
    )

    entrada = final["audit_entries"][0]
    assert entrada["modelo_usado"] == "mock"
    assert 0.0 <= entrada["confidence_score"] <= 1.0
    assert entrada["version_calculador"] == "1.0.0-simulado"
    assert entrada["actor"] == "agente_autorizaciones"


@pytest.mark.asyncio
async def test_mock_connector_determinista_con_seed():
    """Verifica que el MockConnector con seed da resultados reproducibles."""
    from app.conectores.mock_connector import MockConnector

    c1 = MockConnector(seed=42, latencia_segundos=0)
    c2 = MockConnector(seed=42, latencia_segundos=0)

    r1 = await c1.enviar({})
    r2 = await c2.enviar({})

    assert r1["estado"] == r2["estado"]
