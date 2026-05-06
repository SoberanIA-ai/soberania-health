"""Dashboard HITL — sec 11 del handoff.

Construido en Streamlit para velocidad de desarrollo. Asaf construirá
la versión React después del MVP.

Funcionalidades:
1. Cola de autorizaciones pendientes de revisión
2. Detalle de cada autorización (datos + decisión del agente)
3. Botones: Aprobar / Rechazar / Pedir más info
4. Vista del audit log en tiempo real
5. Métricas: % automatizado, tiempo medio, rechazos
"""
import os
from datetime import datetime, timezone

import httpx
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
DEFAULT_REVISOR = os.environ.get("DASHBOARD_REVISOR", "supervisor")


# ---------------------------------------------------------------------------
# Cliente API
# ---------------------------------------------------------------------------


def api_get(path: str) -> dict | list:
    response = httpx.get(f"{API_BASE}{path}", timeout=10.0)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict) -> dict:
    response = httpx.post(f"{API_BASE}{path}", json=payload, timeout=10.0)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------


def calcular_metricas() -> dict:
    """Métricas básicas para el header del dashboard."""
    pendientes = api_get("/api/v1/autorizaciones/pendientes")
    return {
        "pendientes": len(pendientes),
    }


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


def main():
    st.set_page_config(
        page_title="SoberanIA Health — HITL Supervisor",
        layout="wide",
    )

    st.title("SoberanIA Health — Supervisor de Autorizaciones")
    st.caption("Mock mode · Datos simulados hasta validación con HM en Fase 0")

    try:
        health = api_get("/api/v1/health")
        st.sidebar.success(f"API conectada · v{health.get('version')}")
        st.sidebar.caption(f"Calculadores: {health.get('calculadores_version')}")
    except Exception as e:
        st.sidebar.error(f"API no responde: {e}")
        st.stop()

    st.sidebar.divider()
    revisor = st.sidebar.text_input("Revisor", value=DEFAULT_REVISOR)

    if st.sidebar.button("🔄 Refrescar"):
        st.rerun()

    # ----- Métricas -----
    pendientes = api_get("/api/v1/autorizaciones/pendientes")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pendientes revisión", len(pendientes))
    with col2:
        urgentes = sum(1 for p in pendientes if p.get("urgencia") == "urgente")
        st.metric("Urgentes", urgentes)
    with col3:
        st.metric(
            "Mock mode", "Activo",
            help="Datos simulados — ningún portal real es contactado"
        )

    st.divider()

    # ----- Cola de pendientes -----
    if not pendientes:
        st.info("No hay autorizaciones pendientes de revisión.")
        st.markdown(
            "Para crear una autorización de prueba, usa "
            "`POST /api/v1/autorizaciones/procesar`."
        )
        return

    st.subheader(f"Cola HITL ({len(pendientes)})")

    for auth in pendientes:
        _render_autorizacion(auth, revisor)


def _render_autorizacion(auth: dict, revisor: str):
    """Renderiza una autorización pendiente como expander con acciones."""
    nombre_paciente = auth.get("paciente_nombre") or "(paciente sin extraer)"
    procedimiento = auth.get("procedimiento_descripcion") or "(procedimiento sin extraer)"
    confidence = auth.get("confidence_score") or 0.0
    badge = "🔴" if confidence < 0.5 else "🟡"

    with st.expander(f"{badge} {nombre_paciente} — {procedimiento}"):
        col_datos, col_decision = st.columns([2, 1])

        with col_datos:
            st.markdown(f"**ID:** `{auth['id']}`")
            st.markdown(f"**Aseguradora:** {auth.get('aseguradora') or '—'}")
            st.markdown(f"**Tipo póliza:** {auth.get('poliza_tipo') or '—'}")
            st.markdown(f"**Código generado:** {auth.get('procedimiento_codigo') or '—'}")
            st.markdown(f"**CIE-10:** {auth.get('procedimiento_cie10') or '—'}")
            st.markdown(f"**Médico:** {auth.get('medico_nombre') or '—'}")
            st.markdown(f"**Confidence:** `{confidence:.0%}`")
            st.markdown(f"**Estado:** `{auth['estado']}`")
            st.markdown(f"**Recibido:** {auth.get('created_at')}")

            with st.popover("Ver audit log"):
                _render_audit_log(auth["id"])

        with col_decision:
            notas = st.text_area(
                "Notas del revisor",
                key=f"notas_{auth['id']}",
                placeholder="Razón de la decisión",
            )

            if st.button("✅ Aprobar", key=f"aprobar_{auth['id']}", type="primary"):
                _aplicar_decision(auth["id"], "aprobar", revisor, notas)

            if st.button("❌ Rechazar", key=f"rechazar_{auth['id']}"):
                _aplicar_decision(auth["id"], "rechazar", revisor, notas)

            if st.button("ℹ️ Pedir más info", key=f"info_{auth['id']}"):
                _aplicar_decision(auth["id"], "mas_info", revisor, notas)


def _aplicar_decision(autorizacion_id: str, decision: str, revisor: str, notas: str):
    try:
        api_post(
            f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
            {"decision": decision, "revisor": revisor, "notas": notas or None},
        )
        st.success(f"Decisión '{decision}' registrada")
        st.rerun()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"Error: {detail}")


def _render_audit_log(autorizacion_id: str):
    audit = api_get(f"/api/v1/audit/{autorizacion_id}")
    integridad_icon = "🔒" if audit["integro"] else "⚠️"
    st.markdown(
        f"{integridad_icon} **Integridad:** "
        f"{'OK' if audit['integro'] else 'COMPROMETIDA'} · "
        f"{audit['total_entries']} entries"
    )
    if not audit["integro"]:
        st.error(f"Entries inválidas: {audit['entries_invalidas']}")

    for entry in audit["entries"]:
        st.markdown(
            f"`{entry['timestamp']}` · **{entry['accion']}** "
            f"({entry['actor']}) — confidence {entry.get('confidence_score', 0):.2f}"
        )
        st.caption(f"sha256: `{entry['hash_sha256'][:16]}...`")


if __name__ == "__main__":
    main()
