"""Tests unitarios de los calculadores Python.

Cubre cada función pública de cada calculador. Verifica el principio
fundamental (sec 7.1): los calculadores son Python puro, sin LLM, sin I/O.
"""
import ast
import pathlib

import pytest

from app.calculadores import (
    codigos_adeslas,
    codigos_dkv,
    codigos_sanitas,
    generador_solicitud,
    identificador_aseguradora,
    plazos_respuesta,
    reglas_cobertura,
    verificador_cobertura,
)


# ---------------------------------------------------------------------------
# codigos_sanitas
# ---------------------------------------------------------------------------


def test_sanitas_data_status_simulado():
    assert codigos_sanitas.DATA_STATUS == "SIMULADO"


def test_sanitas_get_codigo_existente():
    codigo = codigos_sanitas.get_codigo("SIM_RM_RODILLA_DCHA", "basica")
    assert codigo is not None
    assert codigo.codigo == "SIM-001"
    assert codigo.requiere_autorizacion is True
    assert "informe_clinico" in codigo.documentacion_requerida


def test_sanitas_get_codigo_procedimiento_desconocido():
    assert codigos_sanitas.get_codigo("NO_EXISTE", "basica") is None


def test_sanitas_get_codigo_poliza_no_mapeada():
    # SIM_TAC_ABDOMINAL solo está mapeado en BASICA en el catálogo simulado
    assert codigos_sanitas.get_codigo("SIM_TAC_ABDOMINAL", "premium") is None


def test_sanitas_requiere_autorizacion_safe_default():
    """Procedimiento no catalogado debe devolver True (safe default)."""
    assert codigos_sanitas.requiere_autorizacion("NO_EXISTE", "basica") is True


def test_sanitas_requiere_autorizacion_existente():
    assert codigos_sanitas.requiere_autorizacion("SIM_RM_RODILLA_DCHA", "basica") is True


def test_sanitas_get_version_marca_simulado():
    assert "SIMULADO" in codigos_sanitas.get_version()


def test_sanitas_tipos_poliza_completos():
    """El enum cubre las 5 pólizas Sanitas conocidas."""
    valores = {p.value for p in codigos_sanitas.TipoPolizaSanitas}
    assert valores == {"basica", "mas_salud", "mas_salud_plus", "optima", "premium"}


# ---------------------------------------------------------------------------
# codigos_adeslas (catálogo vacío hasta Fase 0)
# ---------------------------------------------------------------------------


def test_adeslas_catalogo_vacio_hasta_fase_0():
    assert codigos_adeslas.CODIGOS == {}


def test_adeslas_get_codigo_devuelve_none():
    assert codigos_adeslas.get_codigo("CUALQUIER_COSA", "basica") is None


def test_adeslas_requiere_autorizacion_safe_default():
    assert codigos_adeslas.requiere_autorizacion("CUALQUIER_COSA", "basica") is True


def test_adeslas_get_version_marca_simulado():
    assert "SIMULADO" in codigos_adeslas.get_version()


# ---------------------------------------------------------------------------
# codigos_dkv (catálogo vacío hasta Fase 0)
# ---------------------------------------------------------------------------


def test_dkv_catalogo_vacio_hasta_fase_0():
    assert codigos_dkv.CODIGOS == {}


def test_dkv_get_codigo_devuelve_none():
    assert codigos_dkv.get_codigo("CUALQUIER_COSA", "integral") is None


def test_dkv_requiere_autorizacion_safe_default():
    assert codigos_dkv.requiere_autorizacion("CUALQUIER_COSA", "integral") is True


def test_dkv_get_version_marca_simulado():
    assert "SIMULADO" in codigos_dkv.get_version()


# ---------------------------------------------------------------------------
# identificador_aseguradora
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Sanitas", "sanitas"),
        ("SANITAS", "sanitas"),
        ("sanitas s.a.", "sanitas"),
        ("Bupa Sanitas", "sanitas"),
        ("Adeslas", "adeslas"),
        ("SegurCaixa Adeslas", "adeslas"),
        ("DKV", "dkv"),
        ("DKV Seguros", "dkv"),
    ],
)
def test_identificar_canonical_names(entrada, esperado):
    assert identificador_aseguradora.identificar(entrada) == esperado


@pytest.mark.parametrize("entrada", ["Mapfre", "Asisa", "", "   ", None])
def test_identificar_no_soportadas_devuelve_none(entrada):
    assert identificador_aseguradora.identificar(entrada) is None


def test_es_soportada_true_para_las_3_del_mvp():
    assert identificador_aseguradora.es_soportada("Sanitas") is True
    assert identificador_aseguradora.es_soportada("Adeslas") is True
    assert identificador_aseguradora.es_soportada("DKV") is True


def test_es_soportada_false_para_otras():
    assert identificador_aseguradora.es_soportada("Mapfre") is False


# ---------------------------------------------------------------------------
# reglas_cobertura
# ---------------------------------------------------------------------------


def test_reglas_vacias_hasta_fase_0():
    assert reglas_cobertura.REGLAS == {}


def test_requiere_autorizacion_previa_safe_default():
    """Sin reglas mapeadas, todo va a HITL → True."""
    assert (
        reglas_cobertura.requiere_autorizacion_previa("sanitas", "basica", "X") is True
    )


def test_reglas_get_version_marca_simulado():
    assert "SIMULADO" in reglas_cobertura.get_version()


# ---------------------------------------------------------------------------
# plazos_respuesta
# ---------------------------------------------------------------------------


def test_plazos_sanitas_normal():
    assert plazos_respuesta.get_plazo_horas("sanitas") == 48


def test_plazos_sanitas_urgente():
    assert plazos_respuesta.get_plazo_horas("sanitas", urgente=True) == 4


def test_plazos_adeslas_normal():
    assert plazos_respuesta.get_plazo_horas("adeslas") == 48


def test_plazos_dkv_normal():
    assert plazos_respuesta.get_plazo_horas("dkv") == 72


def test_plazos_dkv_urgente():
    assert plazos_respuesta.get_plazo_horas("dkv", urgente=True) == 6


def test_plazos_aseguradora_desconocida_default():
    """Aseguradora no mapeada → DEFAULT_PLAZO_HORAS (72h, conservador)."""
    assert plazos_respuesta.get_plazo_horas("desconocida") == 72


def test_plazos_case_insensitive():
    assert plazos_respuesta.get_plazo_horas("SANITAS") == 48


# ---------------------------------------------------------------------------
# verificador_cobertura
# ---------------------------------------------------------------------------


def test_verificar_aseguradora_desconocida():
    cubierto, requiere, docs, conf = verificador_cobertura.verificar(
        aseguradora="Mapfre",
        procedimiento_cie10="SIM_RM_RODILLA_DCHA",
        tipo_poliza="basica",
    )
    assert cubierto is False
    assert requiere is True  # safe default → HITL
    assert docs == []
    assert conf == 0.0


def test_verificar_sanitas_procedimiento_conocido():
    cubierto, requiere, docs, conf = verificador_cobertura.verificar(
        aseguradora="Sanitas",
        procedimiento_cie10="SIM_RM_RODILLA_DCHA",
        tipo_poliza="basica",
    )
    assert cubierto is True
    assert requiere is True
    assert "informe_clinico" in docs
    assert conf == 1.0


def test_verificar_sanitas_procedimiento_desconocido_dispara_hitl():
    cubierto, requiere, docs, conf = verificador_cobertura.verificar(
        aseguradora="Sanitas",
        procedimiento_cie10="PROCEDIMIENTO_QUE_NO_EXISTE",
        tipo_poliza="basica",
    )
    assert cubierto is False
    assert requiere is True  # safe default
    assert docs == []
    assert conf == 0.5
    assert conf < 0.80  # debe disparar HITL (regla 4 sec 19)


def test_verificar_adeslas_catalogo_vacio_va_a_hitl():
    """Adeslas tiene CODIGOS={} hasta Fase 0 → todo a HITL."""
    cubierto, requiere, docs, conf = verificador_cobertura.verificar(
        aseguradora="Adeslas",
        procedimiento_cie10="CUALQUIER",
        tipo_poliza="basica",
    )
    assert cubierto is False
    assert requiere is True
    assert conf < 0.80


def test_verificar_dkv_catalogo_vacio_va_a_hitl():
    cubierto, _, _, conf = verificador_cobertura.verificar(
        aseguradora="DKV",
        procedimiento_cie10="CUALQUIER",
        tipo_poliza="integral",
    )
    assert cubierto is False
    assert conf < 0.80


# ---------------------------------------------------------------------------
# generador_solicitud
# ---------------------------------------------------------------------------


def _datos_paciente_demo():
    return {
        "nombre": "María",
        "apellidos": "García López",
        "poliza": "SAN-987654",
        "fecha_nacimiento": "1981-03-15",
    }


def _datos_medico_demo():
    return {
        "nombre": "Dr. Juan Traumatología",
        "numero_colegiado": "28-12345",
        "especialidad": "Traumatología",
    }


def test_generador_sanitas_payload_completo():
    payload = generador_solicitud.generar(
        aseguradora="sanitas",
        datos_paciente=_datos_paciente_demo(),
        datos_medico=_datos_medico_demo(),
        procedimiento_cie10="SIM_RM_RODILLA_DCHA",
        procedimiento_codigo_aseguradora="SIM-001",
        documentacion_adjunta=["informe_clinico"],
        urgente=False,
    )
    assert payload["aseguradora"] == "sanitas"
    assert payload["tipo"] == "solicitud_autorizacion"
    assert payload["_data_status"] == "SIMULADO"
    assert payload["datos"]["paciente"]["nombre"] == "María"
    assert payload["datos"]["procedimiento"]["codigo_sanitas"] == "SIM-001"
    assert payload["datos"]["procedimiento"]["urgente"] is False


def test_generador_adeslas_payload_completo():
    payload = generador_solicitud.generar(
        aseguradora="Adeslas",
        datos_paciente=_datos_paciente_demo(),
        datos_medico=_datos_medico_demo(),
        procedimiento_cie10="SIM_RM_CEREBRAL",
        procedimiento_codigo_aseguradora="ADE-X",
        documentacion_adjunta=[],
        urgente=True,
    )
    assert payload["aseguradora"] == "adeslas"
    assert payload["datos"]["procedimiento"]["urgente"] is True


def test_generador_dkv_payload_completo():
    payload = generador_solicitud.generar(
        aseguradora="DKV",
        datos_paciente=_datos_paciente_demo(),
        datos_medico=_datos_medico_demo(),
        procedimiento_cie10="SIM_X",
        procedimiento_codigo_aseguradora="DKV-Y",
        documentacion_adjunta=[],
        urgente=False,
    )
    assert payload["aseguradora"] == "dkv"


def test_generador_aseguradora_no_soportada_levanta():
    with pytest.raises(ValueError, match="no soportada"):
        generador_solicitud.generar(
            aseguradora="Mapfre",
            datos_paciente={},
            datos_medico={},
            procedimiento_cie10="X",
            procedimiento_codigo_aseguradora="Y",
            documentacion_adjunta=[],
        )


# ---------------------------------------------------------------------------
# Principio fundamental: calculadores son Python puro
# Sec 7.1 del handoff: sin LLM, sin I/O, sin red.
# ---------------------------------------------------------------------------


PROHIBIDOS_EN_CALCULADORES = {
    # LLM
    "langchain", "langgraph", "langfuse", "mistralai", "openai", "anthropic",
    # HTTP / red
    "requests", "httpx", "urllib", "urllib3", "aiohttp",
    # DB / I/O
    "sqlalchemy", "psycopg2", "alembic", "redis",
    # Web framework
    "fastapi", "starlette", "uvicorn",
}


def _top_level_imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def test_calculadores_son_python_puro():
    """Ningún calculador puede importar LLM, HTTP, DB ni framework web."""
    calc_dir = pathlib.Path(__file__).parent.parent / "app" / "calculadores"
    archivos_revisados = []
    for archivo in calc_dir.glob("*.py"):
        if archivo.name == "__init__.py":
            continue
        archivos_revisados.append(archivo.name)
        imports = _top_level_imports(archivo)
        violaciones = imports & PROHIBIDOS_EN_CALCULADORES
        assert not violaciones, (
            f"{archivo.name} importa módulos prohibidos: {violaciones}. "
            "Los calculadores deben ser Python puro (sec 7.1 del handoff)."
        )
    assert len(archivos_revisados) >= 7, (
        f"Esperaba ≥7 calculadores, encontré: {archivos_revisados}"
    )
