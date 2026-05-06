"""Dashboard HITL — sec 11 del handoff.

Construido en Streamlit puro para velocidad de desarrollo.
Asaf construirá la versión React después del MVP.

Funcionalidades:
1. Métricas en tiempo real: total, % automatización, pendientes HITL
2. Cola de autorizaciones pendientes con detalle expandible
3. Datos extraídos por el agente (paciente, aseguradora, código...)
4. Confidence score visualizado con barra de progreso
5. Botones aprobar / rechazar / pedir más info → POST hitl
6. Audit log inline distinguiendo 🤖 agente vs 🧑 humano
7. Indicador 🔒 de integridad SHA256
8. Auto-refresh cada 15s (toggleable)

Diseñado para que alguien no técnico (back-office HM) entienda lo que
está pasando sin explicación.
"""
import os
import time

import httpx
import streamlit as st
import streamlit.components.v1 as components

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
DEFAULT_REVISOR = os.environ.get("DASHBOARD_REVISOR", "supervisor@hm.es")
AUTO_REFRESH_SEGUNDOS = 15


# ---------------------------------------------------------------------------
# Cliente API
# ---------------------------------------------------------------------------


def api_get(path: str) -> dict | list:
    r = httpx.get(f"{API_BASE}{path}", timeout=10.0)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict) -> dict:
    r = httpx.post(f"{API_BASE}{path}", json=payload, timeout=10.0)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Config visual
# ---------------------------------------------------------------------------


def _badge_confidence(confidence: float) -> str:
    if confidence < 0.3:
        return "🔴"
    if confidence < 0.6:
        return "🟠"
    if confidence < 0.8:
        return "🟡"
    return "🟢"


def _emoji_actor(hitl_intervencion: bool) -> str:
    return "🧑" if hitl_intervencion else "🤖"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


def _sidebar() -> tuple[str, bool]:
    with st.sidebar:
        st.title("⚙️ Configuración")

        try:
            health = api_get("/api/v1/health")
            st.success(f"API conectada · v{health['version']}")
            st.caption(f"Calculadores: `{health['calculadores_version']}`")
        except Exception as exc:
            st.error(f"API no responde: {exc}")
            st.stop()

        st.divider()

        revisor = st.text_input(
            "Revisor",
            value=st.session_state.get("revisor", DEFAULT_REVISOR),
            help="Identificador que queda en el audit log",
        )
        st.session_state["revisor"] = revisor
        if not revisor.strip():
            st.warning("Identifícate para poder decidir")

        st.divider()

        auto_refresh = st.toggle(
            f"🔄 Auto-refresh ({AUTO_REFRESH_SEGUNDOS}s)",
            value=st.session_state.get("auto_refresh", True),
            help="Recarga la cola automáticamente. Desactívalo si estás escribiendo notas.",
        )
        st.session_state["auto_refresh"] = auto_refresh

        if st.button("Refrescar ahora", use_container_width=True):
            st.rerun()

        st.divider()
        st.caption(
            "**Mock mode** · Datos SIMULADOS hasta validación "
            "con HM en Fase 0. Ningún portal real es contactado."
        )
        return revisor, auto_refresh


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------


def _render_metricas() -> None:
    try:
        m = api_get("/api/v1/autorizaciones/metricas")
    except Exception:
        m = {
            "total": 0,
            "automatizadas": 0,
            "pendientes_hitl": 0,
            "autorizadas": 0,
            "denegadas": 0,
            "tasa_automatizacion": 0.0,
        }

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📦 Total procesadas", m["total"])
    with c2:
        tasa = m["tasa_automatizacion"]
        delta = None
        if m["total"] > 0:
            delta = f"{m['automatizadas']} de {m['total']}"
        st.metric(
            "🤖 Automatización",
            f"{tasa:.0%}",
            delta=delta,
            help="Porcentaje sin intervención humana",
        )
    with c3:
        st.metric(
            "🧑 Pendientes HITL",
            m["pendientes_hitl"],
            help="En cola de revisión humana",
        )
    with c4:
        st.metric("✅ Autorizadas", m["autorizadas"])

    if m["total"] > 0:
        st.progress(
            m["tasa_automatizacion"],
            text=(
                f"Automatización: {m['automatizadas']} sin HITL · "
                f"{m['con_hitl']} con HITL · {m['denegadas']} denegadas"
            ),
        )


# ---------------------------------------------------------------------------
# Detalle de autorización
# ---------------------------------------------------------------------------


def _render_caso(auth: dict, revisor: str) -> None:
    confidence = float(auth.get("confidence_score") or 0)
    nombre = auth.get("paciente_nombre") or "(paciente sin extraer)"
    proc = auth.get("procedimiento_descripcion") or "(procedimiento sin extraer)"
    badge = _badge_confidence(confidence)
    urgente = (auth.get("urgencia") or "").lower() == "urgente"
    titulo_urg = " 🚨 URGENTE" if urgente else ""

    titulo = f"{badge} **{nombre}** — {proc}{titulo_urg}"

    with st.expander(titulo, expanded=False):
        col_datos, col_decision = st.columns([3, 2])

        # ----- Columna izquierda: datos + audit -----
        with col_datos:
            st.markdown("##### 📋 Datos extraídos por el agente")
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"**Paciente:** {nombre}")
                st.markdown(f"**Aseguradora:** {auth.get('aseguradora') or '—'}")
                st.markdown(f"**Tipo de póliza:** {auth.get('poliza_tipo') or '—'}")
                st.markdown(f"**Nº póliza:** {auth.get('poliza_numero') or '—'}")
            with d2:
                st.markdown(f"**Médico:** {auth.get('medico_nombre') or '—'}")
                st.markdown(f"**CIE-10:** `{auth.get('procedimiento_cie10') or '—'}`")
                st.markdown(
                    f"**Código aseguradora:** `{auth.get('procedimiento_codigo') or '—'}`"
                )
                st.markdown(f"**Urgencia:** `{auth.get('urgencia') or 'normal'}`")

            st.markdown("##### 🎯 Confidence del agente")
            st.progress(confidence, text=f"{confidence:.0%}")
            if confidence < 0.5:
                st.error("⚠️ Confidence baja — campos faltantes o ambiguos")
            elif confidence < 0.8:
                st.warning("⚠️ Confidence media — requiere revisión humana")

            st.caption(
                f"ID: `{auth['id']}` · "
                f"Estado: `{auth['estado']}` · "
                f"Recibido: {auth.get('created_at', '—')[:19].replace('T', ' ')}"
            )

            st.markdown("##### 📜 Audit log")
            try:
                audit = api_get(f"/api/v1/audit/{auth['id']}")
                _render_audit(audit)
            except Exception as exc:
                st.error(f"Error cargando audit log: {exc}")

        # ----- Columna derecha: decisión -----
        with col_decision:
            st.markdown("##### 👤 Decisión humana")

            if not revisor.strip():
                st.info("Identifícate como revisor en el sidebar para decidir")
                return

            notas = st.text_area(
                "Notas del revisor",
                key=f"notas_{auth['id']}",
                placeholder=(
                    "Razón de la decisión (opcional). Se guarda en audit log."
                ),
                height=140,
            )

            bt1, bt2 = st.columns(2)
            with bt1:
                if st.button(
                    "✅ Aprobar",
                    key=f"a_{auth['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    _decidir(auth["id"], "aprobar", revisor, notas)
            with bt2:
                if st.button(
                    "❌ Rechazar",
                    key=f"r_{auth['id']}",
                    use_container_width=True,
                ):
                    _decidir(auth["id"], "rechazar", revisor, notas)
            if st.button(
                "ℹ️ Pedir más info",
                key=f"i_{auth['id']}",
                use_container_width=True,
            ):
                _decidir(auth["id"], "mas_info", revisor, notas)

            with st.popover("Razón sugerida según confidence"):
                if confidence < 0.5:
                    st.markdown(
                        "Hay **campos críticos faltantes**. Sugerencia: "
                        "**Pedir más info** y confirmar con el médico."
                    )
                elif confidence < 0.8:
                    st.markdown(
                        "Confidence media. Verifica los datos extraídos contra "
                        "el HIS y decide."
                    )
                else:
                    st.markdown(
                        "Confidence alta pero el sistema escaló a HITL "
                        "(probablemente catálogo simulado pendiente)."
                    )


def _decidir(autorizacion_id: str, decision: str, revisor: str, notas: str) -> None:
    try:
        api_post(
            f"/api/v1/autorizaciones/{autorizacion_id}/hitl",
            {
                "decision": decision,
                "revisor": revisor,
                "notas": notas.strip() or None,
            },
        )
        emoji = {"aprobar": "✅", "rechazar": "❌", "mas_info": "ℹ️"}[decision]
        st.success(f"{emoji} Decisión registrada: **{decision}** por `{revisor}`")
        time.sleep(0.6)  # breve para que el usuario vea el feedback
        st.rerun()
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        st.error(f"Error: {detail}")


def _render_audit(audit: dict) -> None:
    if audit["integro"]:
        st.success(
            f"🔒 SHA256 íntegro · {audit['total_entries']} entries encadenadas"
        )
    else:
        invalidas = len(audit["entries_invalidas"])
        st.error(
            f"⚠️ Integridad COMPROMETIDA · "
            f"{invalidas} de {audit['total_entries']} entries alteradas"
        )

    for entry in audit["entries"]:
        emoji = _emoji_actor(entry["hitl_intervencion"])
        ts = entry["timestamp"][11:19]  # HH:MM:SS
        accion = entry["accion"]
        actor = entry["actor"]
        conf = float(entry.get("confidence_score") or 0)

        col_actor, col_accion, col_conf = st.columns([1, 4, 1])
        with col_actor:
            st.markdown(f"{emoji} `{ts}`")
        with col_accion:
            modelo_caption = ""
            if entry.get("modelo_usado"):
                modelo_caption = f" · modelo: `{entry['modelo_usado']}`"
            st.markdown(f"**{accion}** · `{actor}`{modelo_caption}")
        with col_conf:
            st.markdown(f"`{conf:.0%}`")
        st.caption(f"sha256: `{entry['hash_sha256'][:24]}…`")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    st.set_page_config(
        page_title="SoberanIA Health — Supervisor",
        page_icon="🏥",
        layout="wide",
    )

    revisor, auto_refresh = _sidebar()

    st.title("🏥 SoberanIA Health — Supervisor de Autorizaciones")
    st.caption(
        "Cliente objetivo: **HM Hospitales** · Vertical salud · "
        "Modo demo con datos simulados"
    )

    _render_metricas()
    st.divider()

    pendientes = api_get("/api/v1/autorizaciones/pendientes")

    if not pendientes:
        st.success("✅ Cola HITL vacía — no hay autorizaciones pendientes de revisión.")
        with st.expander("¿Cómo añadir un caso de prueba?"):
            st.code(
                "curl -X POST http://localhost:8002/api/v1/autorizaciones/procesar \\\n"
                "  -H 'Content-Type: application/json' \\\n"
                "  -d '{\"orden_h17\":\"Paciente: Test\\nAseguradora: Adeslas\\n"
                "Procedimiento: RM cerebral\\nMédico: Dr. X\",\"modo\":\"mock\"}'",
                language="bash",
            )
            st.caption(
                "O ejecuta `docker compose exec api python scripts/run_demo.py --reset`"
            )
    else:
        st.subheader(f"📋 Cola HITL ({len(pendientes)})")
        st.caption(
            "Cada caso muestra qué extrajo el agente, su confidence y el "
            "audit log completo. Decide aprobar, rechazar o pedir más info."
        )
        for auth in pendientes:
            _render_caso(auth, revisor)

    # Auto-refresh vía iframe JS — no bloquea Streamlit (a diferencia de time.sleep)
    if auto_refresh:
        components.html(
            f"""
            <script>
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {AUTO_REFRESH_SEGUNDOS * 1000});
            </script>
            """,
            height=0,
        )
        st.caption(
            f"🔄 Auto-refresh activo · próxima actualización en "
            f"{AUTO_REFRESH_SEGUNDOS}s · desactiva el toggle en el sidebar "
            "si estás escribiendo notas"
        )


if __name__ == "__main__":
    main()
