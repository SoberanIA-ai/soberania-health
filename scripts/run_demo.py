"""Script de demo automatizada — sec 17 del handoff.

Ejecuta los 3 casos del MVP contra el API en mock mode.
Pensado para la demo de 10 min con Xavier Tarragó (HM Hospitales).

Uso:
    docker compose exec api python scripts/run_demo.py
    docker compose exec api python scripts/run_demo.py --reset
    docker compose exec api python scripts/run_demo.py --reset --pause

Flags:
    --reset: limpia DB antes de empezar (útil para demos limpias)
    --pause: pausa entre casos para la narrativa del demoer
"""
import argparse
import json
import os
import sys
import time

import httpx

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
DASHBOARD_BASE = os.environ.get(
    "DASHBOARD_BASE", "http://localhost:8501"
)


CASOS_DEMO = [
    {
        "id": "demo_1",
        "titulo": "Caso 1 — Happy path completo",
        "narrativa": (
            "Una orden de RM rodilla derecha entra al sistema. "
            "El parser LLM extrae los datos. Los calculadores Python deciden "
            "el código (SIM-001), confirman cobertura, generan la solicitud "
            "y el conector mock simula el envío a Sanitas. Aprobación automática."
        ),
        "orden": (
            "Paciente: María García López\n"
            "Aseguradora: Sanitas\n"
            "Póliza: Más Salud Plus 987654\n"
            "Procedimiento: Resonancia magnética rodilla derecha\n"
            "Médico: Dr. Juan Pérez Traumatología"
        ),
        "esperado": "autorizado",
    },
    {
        "id": "demo_2",
        "titulo": "Caso 2 — HITL (catálogo Adeslas pendiente de validar con HM)",
        "narrativa": (
            "Una orden Adeslas entra al sistema. Como su catálogo está marcado "
            "DATA_STATUS=SIMULADO hasta validación con HM en Fase 0, el sistema "
            "no envía a ciegas — escala a revisión humana (safe-default). "
            "El supervisor decide en el dashboard. Audit log registra "
            "la intervención humana con SHA256 encadenado."
        ),
        "orden": (
            "Paciente: Andrea Ruiz\n"
            "Aseguradora: Adeslas\n"
            "Póliza: Completa 111222\n"
            "Procedimiento: Resonancia magnética cerebral\n"
            "Médico: Dra. Laura Neurología"
        ),
        "esperado": "pendiente_hitl",
    },
    {
        "id": "demo_3",
        "titulo": "Caso 3 — Datos faltantes detectados por el guardrail",
        "narrativa": (
            "Una orden incompleta (sin médico) entra al sistema. "
            "El guardrail Mistral Nemo detecta el campo obligatorio faltante "
            "y baja la confidence a 0.3. Por la regla 4 (sec 19), confidence < 0.80 "
            "dispara HITL. El supervisor decide pedir más información."
        ),
        "orden": (
            "Paciente: Pedro Anónimo\n"
            "Aseguradora: Sanitas\n"
            "Procedimiento: Cirugía ambulatoria de rodilla"
        ),
        "esperado": "pendiente_hitl",
    },
]


def banner(texto: str, char: str = "=") -> None:
    print(f"\n{char * 70}")
    print(f"  {texto}")
    print(f"{char * 70}")


def kv(label: str, value, width: int = 28) -> None:
    print(f"  {label:<{width}} {value}")


def fetch(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    if method == "GET":
        r = httpx.get(url, timeout=30)
    else:
        r = httpx.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def reset_db() -> None:
    """Trunca audit_log y autorizaciones para empezar la demo limpia."""
    print("Limpiando DB...")
    from sqlalchemy import text

    from app.models.database import SessionLocal

    session = SessionLocal()
    try:
        session.execute(text("TRUNCATE TABLE audit_log, autorizaciones CASCADE"))
        session.commit()
        print("  ✓ DB limpia\n")
    finally:
        session.close()


def correr_caso(caso: dict, pausa: bool) -> None:
    banner(caso["titulo"])
    print(f"\n  Narrativa:\n  {caso['narrativa']}\n")

    print("  Orden de entrada:")
    for linea in caso["orden"].splitlines():
        print(f"    {linea}")

    if pausa:
        input("\n  [Enter para procesar]")

    print("\n  → Enviando a /api/v1/autorizaciones/procesar...")
    resp = fetch(
        "/api/v1/autorizaciones/procesar",
        method="POST",
        payload={"orden_h17": caso["orden"], "modo": "mock"},
    )

    print("\n  Respuesta del agente:")
    kv("autorizacion_id", resp["autorizacion_id"])
    kv("estado", resp["estado"])
    kv("confidence_score", f"{resp['confidence_score']:.2%}" if resp.get("confidence_score") else "—")
    kv("hitl_requerido", resp["hitl_requerido"])
    kv("numero_autorizacion", resp.get("numero_autorizacion") or "—")

    detalle = fetch(f"/api/v1/autorizaciones/{resp['autorizacion_id']}")
    print("\n  Datos extraídos:")
    kv("paciente_nombre", detalle.get("paciente_nombre") or "—")
    kv("aseguradora", detalle.get("aseguradora") or "—")
    kv("tipo_poliza", detalle.get("poliza_tipo") or "—")
    kv("procedimiento_codigo", detalle.get("procedimiento_codigo") or "—")
    kv("procedimiento_cie10", detalle.get("procedimiento_cie10") or "—")

    audit = fetch(f"/api/v1/audit/{resp['autorizacion_id']}")
    print("\n  Audit log:")
    kv("total_entries", audit["total_entries"])
    kv("integro (SHA256)", "✓ OK" if audit["integro"] else "✗ COMPROMETIDO")
    print("  Acciones registradas:")
    for entry in audit["entries"]:
        marca_humana = " 🧑" if entry["hitl_intervencion"] else ""
        print(
            f"    {entry['timestamp'][:19]} · {entry['accion']:<24} "
            f"({entry['actor']}) — {entry.get('confidence_score', 0):.0%}{marca_humana}"
        )

    if resp["estado"] != caso["esperado"]:
        print(
            f"\n  ⚠️  Estado inesperado: esperaba {caso['esperado']}, "
            f"obtuvimos {resp['estado']}"
        )
    else:
        print(f"\n  ✓ Estado coincide con lo esperado: {caso['esperado']}")

    if pausa:
        input("\n  [Enter para siguiente caso]")


def resumen_final() -> None:
    pendientes = fetch("/api/v1/autorizaciones/pendientes")
    banner("RESUMEN DE LA DEMO", "─")
    kv("Autorizaciones procesadas", len(CASOS_DEMO))
    kv("Pendientes en cola HITL", len(pendientes))
    kv("Dashboard HITL", DASHBOARD_BASE)
    kv("Modo", "mock — sin credenciales reales de aseguradoras")
    kv("DATA_STATUS", "SIMULADO — validar con HM en Fase 0")

    if pendientes:
        print("\n  Para revisar HITL: abrir el dashboard, identificarse")
        print("  como revisor, y aprobar/rechazar cada autorización.")
        print(f"\n  → {DASHBOARD_BASE}\n")


def main():
    parser = argparse.ArgumentParser(description="SoberanIA Health — demo MVP")
    parser.add_argument("--reset", action="store_true", help="Limpia DB antes")
    parser.add_argument("--pause", action="store_true", help="Pausa entre casos")
    args = parser.parse_args()

    banner("SoberanIA Health — Demo MVP", "█")
    print("\n  Vertical salud · Agente 1: Autorizaciones previas")
    print("  Cliente objetivo: HM Hospitales")
    print("  Stack: FastAPI + LangGraph + Mistral API + Postgres + Streamlit")
    print(f"  API: {API_BASE}\n")

    try:
        health = fetch("/api/v1/health")
        kv("API status", health["status"])
        kv("Calculadores", health["calculadores_version"])
    except Exception as exc:
        print(f"\n  ✗ API no responde: {exc}")
        print("  ¿Levantaste el stack con  docker compose up -d ?")
        sys.exit(1)

    if args.reset:
        reset_db()

    for caso in CASOS_DEMO:
        correr_caso(caso, pausa=args.pause)
        if not args.pause:
            time.sleep(0.3)

    resumen_final()


if __name__ == "__main__":
    main()
