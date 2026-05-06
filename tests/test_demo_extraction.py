"""Test explícito: el mock heuristic extrae bien los datos de cada caso
de scripts/run_demo.py.

Bug histórico: el _extraer_poliza_hl7 sólo capturaba póliza desde HL7 IN1
y dejaba paciente_poliza=None para órdenes en texto libre. El mock se
arregló (commit 47f6fc7) añadiendo _extraer_poliza_libre y fallbacks de
procedimiento. Este test impide regresiones cuando se añadan casos nuevos.
"""
import re

import pytest
from sqlalchemy import text

from app.agent.llm_client import LLMClient
from app.agent.nodes import set_llm_client
from app.models.database import SessionLocal
from app.services.autorizacion_service import AutorizacionService
from scripts.run_demo import CASOS_DEMO

# Casos donde la orden NO incluye número de póliza por diseño:
# son escenarios HITL por datos faltantes y deben mantenerse sin extraer
# (no es un fallo del heurístico).
PACIENTES_SIN_POLIZA_INTENCIONAL = {"Pedro Anónimo", "Javier Soto Ferreira"}


@pytest.fixture(autouse=True)
def mock_llm():
    set_llm_client(LLMClient(api_key=""))


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        session.execute(text("TRUNCATE TABLE audit_log, autorizaciones CASCADE"))
        session.commit()
        yield session
    finally:
        session.execute(text("TRUNCATE TABLE audit_log, autorizaciones CASCADE"))
        session.commit()
        session.close()


def _poliza_esperada_de_la_orden(orden: str) -> str | None:
    """Extrae la póliza tal y como aparece en la orden del demo (ground truth)."""
    match = re.search(
        r"p[oó]liza[:\s]+[^\n]*?([A-Z]{2,4}-\d{4,}|\d{4,})",
        orden,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


@pytest.mark.parametrize("caso", CASOS_DEMO, ids=lambda c: c["id"])
@pytest.mark.asyncio
async def test_demo_extrae_poliza_correctamente(caso, db, monkeypatch):
    # MockConnector determinístico para casos que se aprueban
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )

    service = AutorizacionService(db)
    autorizacion = await service.procesar(caso["orden"], modo=caso["input"]["modo"]
                                          if "input" in caso else "mock")

    paciente = autorizacion.paciente_nombre or ""
    poliza_extraida = autorizacion.poliza_numero
    poliza_orden = _poliza_esperada_de_la_orden(caso["orden"])

    if paciente in PACIENTES_SIN_POLIZA_INTENCIONAL:
        assert poliza_extraida is None, (
            f"{caso['id']} ({paciente}): la orden NO tiene póliza, "
            f"pero se extrajo {poliza_extraida!r}"
        )
        return

    # Para el resto, debe haber póliza extraída y coincidir con la orden
    assert poliza_extraida, (
        f"{caso['id']} ({paciente}): orden contiene póliza '{poliza_orden}' "
        f"pero el mock no la extrajo"
    )
    if poliza_orden:
        assert poliza_extraida == poliza_orden, (
            f"{caso['id']} ({paciente}): póliza orden={poliza_orden} "
            f"vs extraída={poliza_extraida}"
        )


@pytest.mark.parametrize("caso", CASOS_DEMO, ids=lambda c: c["id"])
@pytest.mark.asyncio
async def test_demo_extrae_procedimiento_descripcion(caso, db, monkeypatch):
    """procedimiento_descripcion nunca puede quedar vacío si la orden lo incluye."""
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )

    service = AutorizacionService(db)
    autorizacion = await service.procesar(caso["orden"], modo="mock")

    # Si la orden contiene "Procedimiento:", la descripción debe extraerse
    if "Procedimiento:" in caso["orden"] or "procedimiento:" in caso["orden"]:
        assert autorizacion.procedimiento_descripcion, (
            f"{caso['id']}: orden tiene Procedimiento: pero "
            f"procedimiento_descripcion quedó vacío"
        )


@pytest.mark.parametrize("caso", CASOS_DEMO, ids=lambda c: c["id"])
@pytest.mark.asyncio
async def test_demo_extrae_aseguradora(caso, db, monkeypatch):
    """aseguradora nunca puede quedar vacía si la orden incluye 'Aseguradora: ...'.

    Aseguradoras soportadas (Sanitas/Adeslas/DKV) se persisten como canonical
    lowercase ("sanitas", "dkv"). Aseguradoras no soportadas (Mapfre, Asisa)
    se persisten con su nombre literal — el verificador las marca como no
    soportadas y dispara HITL pero el campo no queda vacío.
    """
    import app.agent.nodes as nodes_mod
    from app.conectores.mock_connector import MockConnector

    monkeypatch.setattr(
        nodes_mod, "MockConnector",
        lambda **kwargs: MockConnector(seed=42, latencia_segundos=0),
    )

    service = AutorizacionService(db)
    autorizacion = await service.procesar(caso["orden"], modo="mock")

    if "Aseguradora:" not in caso["orden"]:
        return  # casos como demo_3 / demo_10 sin aseguradora explícita

    assert autorizacion.aseguradora, (
        f"{caso['id']} ({autorizacion.paciente_nombre}): orden tiene Aseguradora "
        f"pero el campo se persistió vacío"
    )
