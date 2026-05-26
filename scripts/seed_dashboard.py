"""Seed de datos para verificación manual del dashboard.

Genera ~50 autorizaciones con TODOS los estados posibles:
  autorizado, denegado, informacion_adicional,
  pendiente_hitl, aprobado_hitl, rechazado_hitl, informacion_adicional_requerida

Uso:
    docker compose exec api python scripts/seed_dashboard.py
    docker compose exec api python scripts/seed_dashboard.py --reset
"""
import argparse
import sys
import time

import httpx

API = "http://localhost:8000"

# ─── Casos ────────────────────────────────────────────────────────────────────
# Sanitas con procedimientos del catálogo: irán a auto (autorizado/denegado/info_adicional)
# Adeslas/DKV/otras: catálogo vacío → pendiente_hitl

CASOS = [
    # ── SANITAS — 22 casos, mix automático ───────────────────────────────────
    {
        "paciente": "María García López",
        "aseguradora": "Sanitas", "poliza": "Más Salud Plus 987654",
        "procedimiento": "Resonancia magnética rodilla derecha",
        "medico": "Dr. Juan Pérez Traumatología", "urgente": False,
    },
    {
        "paciente": "Carlos López Hernández",
        "aseguradora": "Sanitas", "poliza": "Básica 4471201",
        "procedimiento": "TAC abdominal con contraste",
        "medico": "Dr. Sergio Ramírez Aparato Digestivo", "urgente": False,
    },
    {
        "paciente": "Roberto Vega Aznar",
        "aseguradora": "Sanitas", "poliza": "Óptima 7724118",
        "procedimiento": "Cirugía ambulatoria de rodilla",
        "medico": "Dra. Marta Soler Traumatología", "urgente": True,
    },
    {
        "paciente": "Ana Martínez Ruiz",
        "aseguradora": "Sanitas", "poliza": "Premium 9988123",
        "procedimiento": "Colonoscopia",
        "medico": "Dr. Carlos Vega Aparato Digestivo", "urgente": False,
    },
    {
        "paciente": "Fernando Gil Soto",
        "aseguradora": "Sanitas", "poliza": "Básica 4471892",
        "procedimiento": "Ecocardiograma",
        "medico": "Dra. Elena Ruiz Cardiología", "urgente": False,
    },
    {
        "paciente": "Carmen Iglesias Pardo",
        "aseguradora": "Sanitas", "poliza": "Más Salud 5523781",
        "procedimiento": "Artroscopia rodilla",
        "medico": "Dr. Miguel Torres Traumatología", "urgente": False,
    },
    {
        "paciente": "Diego Fuentes Mora",
        "aseguradora": "Sanitas", "poliza": "Óptima 3312456",
        "procedimiento": "Resonancia magnética cerebral",
        "medico": "Dra. Carmen Lahoz Neurología", "urgente": False,
    },
    {
        "paciente": "Inés Pascual Bou",
        "aseguradora": "Sanitas", "poliza": "Premium 7712300",
        "procedimiento": "TAC cerebral con contraste",
        "medico": "Dr. Ramón Esteve Neurología", "urgente": True,
    },
    {
        "paciente": "Héctor Ruiz Castro",
        "aseguradora": "Sanitas", "poliza": "Básica 8823401",
        "procedimiento": "Resonancia magnética columna lumbar",
        "medico": "Dr. Álvaro Pons Traumatología", "urgente": False,
    },
    {
        "paciente": "Natalia Vidal Expósito",
        "aseguradora": "Sanitas", "poliza": "Más Salud Plus 6645123",
        "procedimiento": "TAC tórax de alta resolución",
        "medico": "Dra. Silvia Garrido Neumología", "urgente": False,
    },
    {
        "paciente": "Álvaro Montoya Reyes",
        "aseguradora": "Sanitas", "poliza": "Óptima 5534712",
        "procedimiento": "Colonoscopia urgente",
        "medico": "Dr. Enrique Moya Digestivo", "urgente": True,
    },
    {
        "paciente": "Paula Sánchez Medina",
        "aseguradora": "Sanitas", "poliza": "Premium 4423567",
        "procedimiento": "Artroscopia hombro derecho",
        "medico": "Dra. Miriam Leal Traumatología", "urgente": False,
    },
    {
        "paciente": "Omar Jiménez Torres",
        "aseguradora": "Sanitas", "poliza": "Básica 3312890",
        "procedimiento": "Ecocardiograma de esfuerzo",
        "medico": "Dr. Javier Cano Cardiología", "urgente": False,
    },
    {
        "paciente": "Laura Blanco Ferrer",
        "aseguradora": "Sanitas", "poliza": "Más Salud 2201678",
        "procedimiento": "Resonancia magnética rodilla izquierda",
        "medico": "Dra. Rosa Esteve Traumatología", "urgente": False,
    },
    {
        "paciente": "Ignacio Herrero Pla",
        "aseguradora": "Sanitas", "poliza": "Óptima 9978345",
        "procedimiento": "TAC columna cervical",
        "medico": "Dr. Pedro Nadal Neurología", "urgente": False,
    },
    {
        "paciente": "Sara Morales Gimeno",
        "aseguradora": "Sanitas", "poliza": "Premium 8867234",
        "procedimiento": "Colonoscopia con sedación",
        "medico": "Dra. Verónica Camps Digestivo", "urgente": False,
    },
    {
        "paciente": "Óscar Prieto Font",
        "aseguradora": "Sanitas", "poliza": "Básica 7756123",
        "procedimiento": "Resonancia magnética hombro derecho",
        "medico": "Dr. Tomás Valls Traumatología", "urgente": False,
    },
    {
        "paciente": "Cristina Pons Martí",
        "aseguradora": "Sanitas", "poliza": "Más Salud Plus 6645012",
        "procedimiento": "TAC abdomino-pélvico con contraste",
        "medico": "Dra. Amparo Ros Oncología", "urgente": True,
    },
    {
        "paciente": "Eduardo Cortés Niño",
        "aseguradora": "Sanitas", "poliza": "Óptima 5534901",
        "procedimiento": "Artroscopia tobillo derecho",
        "medico": "Dr. Germán Soler Traumatología", "urgente": False,
    },
    {
        "paciente": "Verónica Llopis Palau",
        "aseguradora": "Sanitas", "poliza": "Premium 4423890",
        "procedimiento": "Ecocardiograma transesofágico",
        "medico": "Dra. Mónica Benet Cardiología", "urgente": False,
    },
    {
        "paciente": "Samuel Roca Ibáñez",
        "aseguradora": "Sanitas", "poliza": "Básica 3312789",
        "procedimiento": "Colonoscopia de control",
        "medico": "Dr. Clemente Mir Digestivo", "urgente": False,
    },
    {
        "paciente": "Beatriz Navarro Coll",
        "aseguradora": "Sanitas", "poliza": "Más Salud 2201567",
        "procedimiento": "Resonancia magnética cadera derecha",
        "medico": "Dra. Amparo Tortosa Traumatología", "urgente": False,
    },

    # ── ADESLAS — 10 casos → todos pendiente_hitl ────────────────────────────
    {
        "paciente": "Andrea Ruiz Villena",
        "aseguradora": "Adeslas", "poliza": "Completa 111222",
        "procedimiento": "Resonancia magnética cerebral",
        "medico": "Dra. Laura Serra Neurología", "urgente": False,
    },
    {
        "paciente": "Sofía Núñez Castillo",
        "aseguradora": "Adeslas", "poliza": "Básica 8893012",
        "procedimiento": "TAC tórax",
        "medico": "Dr. Andrés Gallego Neumología", "urgente": False,
    },
    {
        "paciente": "Manuel Díez Ramos",
        "aseguradora": "Adeslas", "poliza": "Premium 5566778",
        "procedimiento": "Cirugía de cadera",
        "medico": "Dr. Ramón Castellanos Traumatología", "urgente": True,
    },
    {
        "paciente": "Jorge Navarro Cid",
        "aseguradora": "Adeslas", "poliza": "Elite 2234567",
        "procedimiento": "Cirugía cataratas ojo derecho",
        "medico": "Dr. Ernesto Vila Oftalmología", "urgente": False,
    },
    {
        "paciente": "Marta Lozano Reyes",
        "aseguradora": "Adeslas", "poliza": "Completa 3345678",
        "procedimiento": "Endoscopia digestiva alta",
        "medico": "Dr. Javier Ríos Digestivo", "urgente": False,
    },
    {
        "paciente": "Alberto Fuentes Pons",
        "aseguradora": "Adeslas", "poliza": "Básica 4456789",
        "procedimiento": "Densitometría ósea lumbar",
        "medico": "Dra. Clara Méndez Reumatología", "urgente": False,
    },
    {
        "paciente": "Elena Guerrero Mas",
        "aseguradora": "Adeslas", "poliza": "Premium 5567890",
        "procedimiento": "Apendicectomía laparoscópica",
        "medico": "Dr. Raúl Castro Cirugía", "urgente": True,
    },
    {
        "paciente": "Patricia Soler Gimeno",
        "aseguradora": "Adeslas", "poliza": "Elite 6678901",
        "procedimiento": "Colecistectomía laparoscópica",
        "medico": "Dra. Isabel Valls Cirugía", "urgente": False,
    },
    {
        "paciente": "Marcos Ferrer Ibáñez",
        "aseguradora": "Adeslas", "poliza": "Completa 7789012",
        "procedimiento": "TAC craneal sin contraste",
        "medico": "Dr. Antoni Roca Neurología", "urgente": True,
    },
    {
        "paciente": "Susana Cano Torrent",
        "aseguradora": "Adeslas", "poliza": "Básica 8890123",
        "procedimiento": "Resonancia magnética rodilla derecha",
        "medico": "Dra. Neus Llopis Traumatología", "urgente": False,
    },

    # ── DKV — 8 casos → todos pendiente_hitl ─────────────────────────────────
    {
        "paciente": "Cristina Marín Ortega",
        "aseguradora": "DKV", "poliza": "Integral 9988776",
        "procedimiento": "Resonancia magnética columna lumbar",
        "medico": "Dra. Pilar Vázquez Neurología", "urgente": False,
    },
    {
        "paciente": "Patricia Roldán Esteve",
        "aseguradora": "DKV", "poliza": "Top 4433221",
        "procedimiento": "TAC cerebral",
        "medico": "Dr. Tomás Iglesias Neurología", "urgente": True,
    },
    {
        "paciente": "Pablo Herrera Font",
        "aseguradora": "DKV", "poliza": "Integral 6678901",
        "procedimiento": "Gammagrafía ósea",
        "medico": "Dra. Nuria Vidal Oncología", "urgente": False,
    },
    {
        "paciente": "Isabel Romero Llop",
        "aseguradora": "DKV", "poliza": "Top 7789012",
        "procedimiento": "Litotricia renal extracorpórea",
        "medico": "Dr. Sergio Mora Urología", "urgente": False,
    },
    {
        "paciente": "Antonio Jiménez Sanz",
        "aseguradora": "DKV", "poliza": "Básica 8890123",
        "procedimiento": "Ecocardiograma transtorácico",
        "medico": "Dra. Pilar León Cardiología", "urgente": False,
    },
    {
        "paciente": "Claudia Serrano Bou",
        "aseguradora": "DKV", "poliza": "Top 9901234",
        "procedimiento": "Prótesis total de cadera",
        "medico": "Dr. Marcos Gil Traumatología", "urgente": True,
    },
    {
        "paciente": "Rodrigo Espinosa Mas",
        "aseguradora": "DKV", "poliza": "Integral 1012345",
        "procedimiento": "Artroscopia de hombro izquierdo",
        "medico": "Dra. Laia Puig Traumatología", "urgente": False,
    },
    {
        "paciente": "Adriana Costa Giner",
        "aseguradora": "DKV", "poliza": "Top 2123456",
        "procedimiento": "Biopsia de ganglio linfático",
        "medico": "Dr. Víctor Molés Oncología", "urgente": False,
    },

    # ── Aseguradoras no soportadas — 6 casos → pendiente_hitl ────────────────
    {
        "paciente": "Lucía Mateo Cabrera",
        "aseguradora": "Mapfre", "poliza": "Salud 1122334",
        "procedimiento": "Resonancia magnética rodilla derecha",
        "medico": "Dra. Beatriz Sanchís Traumatología", "urgente": False,
    },
    {
        "paciente": "Víctor Molina Roca",
        "aseguradora": "Asisa", "poliza": "Completa 1123456",
        "procedimiento": "Resonancia magnética columna cervical",
        "medico": "Dr. Tomás Pla Neurología", "urgente": False,
    },
    {
        "paciente": "Beatriz Pascual Mir",
        "aseguradora": "Cigna", "poliza": "International 2234561",
        "procedimiento": "TAC abdominal con contraste",
        "medico": "Dra. Laura Sans Digestivo", "urgente": False,
    },
    {
        "paciente": "Rafael Orozco Boix",
        "aseguradora": "Allianz", "poliza": "Care 3345672",
        "procedimiento": "Cirugía columna lumbar",
        "medico": "Dr. Jaume Esteve Neurocirugia", "urgente": True,
    },
    {
        "paciente": "Mónica Gallardo Peris",
        "aseguradora": "Axa", "poliza": "Health 4456783",
        "procedimiento": "Resonancia magnética cerebral con contraste",
        "medico": "Dra. Carmen Blay Neurología", "urgente": False,
    },
    {
        "paciente": "Pedro Anónimo Datos",
        "aseguradora": "Sanitas",
        "procedimiento": "Cirugía ambulatoria",
        "medico": "", "urgente": False,
    },
]

# Decisiones HITL a aplicar a los primeros casos que queden pendiente_hitl
HITL_DECISIONS = [
    {"decision": "aprobar", "revisor": "supervisor@hmhospitales.es",
     "notas": "Caso revisado: cobertura confirmada manualmente con Adeslas."},
    {"decision": "rechazar", "revisor": "supervisor@hmhospitales.es",
     "notas": "Procedimiento no cubierto según póliza básica vigente."},
    {"decision": "mas_info", "revisor": "supervisor@hmhospitales.es",
     "notas": "Se necesita informe previo del médico de cabecera y historia clínica."},
    {"decision": "aprobar", "revisor": "isabella@hmhospitales.es",
     "notas": "Autorizado tras verificación directa con DKV."},
    {"decision": "rechazar", "revisor": "supervisor@hmhospitales.es",
     "notas": "DKV no cubre este procedimiento en la modalidad de póliza aportada."},
    {"decision": "mas_info", "revisor": "auditor@hmhospitales.es",
     "notas": "Pendiente de confirmar número de póliza con el paciente."},
    {"decision": "aprobar", "revisor": "isabella@hmhospitales.es",
     "notas": "Caso urgente: aprobado manualmente. Aseguradora notificada por teléfono."},
    {"decision": "rechazar", "revisor": "supervisor@hmhospitales.es",
     "notas": "Aseguradora no reconoce el número de póliza aportado."},
]


def banner(txt: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {txt}")
    print(f"{'─' * 60}")


def post(path: str, payload: dict) -> dict:
    r = httpx.post(f"{API}{path}", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def get(path: str) -> dict | list:
    r = httpx.get(f"{API}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def reset_db() -> None:
    from sqlalchemy import text
    from app.models.database import SessionLocal
    session = SessionLocal()
    try:
        session.execute(text("TRUNCATE TABLE audit_log, autorizaciones CASCADE"))
        session.commit()
        print("  ✓ DB limpia")
    finally:
        session.close()


def _orden_texto(c: dict) -> str:
    lines = [f"Paciente: {c['paciente']}"]
    lines.append(f"Aseguradora: {c['aseguradora']}")
    if c.get("poliza"):
        lines.append(f"Póliza: {c['poliza']}")
    lines.append(f"Procedimiento: {c['procedimiento']}")
    if c.get("medico"):
        lines.append(f"Médico: {c['medico']}")
    if c.get("urgente"):
        lines.append("Urgente: sí")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    banner("SoberanIA Health — Seed Dashboard")

    # Verificar API
    try:
        h = get("/api/v1/health")
        print(f"  API: {h['status']} · versión {h.get('version', '?')}")
    except Exception as e:
        print(f"  ✗ API no responde: {e}")
        sys.exit(1)

    if args.reset:
        reset_db()

    # ── 1. Enviar todos los casos ─────────────────────────────────────────────
    banner(f"Enviando {len(CASOS)} casos al agente…")
    resultados = []
    hitl_ids = []

    for i, caso in enumerate(CASOS, 1):
        orden = _orden_texto(caso)
        try:
            resp = post("/api/v1/autorizaciones/procesar", {"orden_h17": orden, "modo": "mock"})
            estado = resp["estado"]
            aid = resp["autorizacion_id"]
            urgente_badge = " 🔴" if caso.get("urgente") else ""
            print(f"  [{i:02d}] {caso['paciente'][:28]:<28}  {caso['aseguradora']:<8}  {estado}{urgente_badge}")
            resultados.append({"id": aid, "estado": estado, "caso": caso})
            if estado == "pendiente_hitl":
                hitl_ids.append(aid)
        except Exception as e:
            print(f"  [{i:02d}] ERROR {caso['paciente']}: {e}")
        time.sleep(0.05)

    # ── 2. Aplicar decisiones HITL ────────────────────────────────────────────
    banner(f"Aplicando decisiones HITL ({min(len(HITL_DECISIONS), len(hitl_ids))} casos)…")

    for idx, decision in enumerate(HITL_DECISIONS):
        if idx >= len(hitl_ids):
            print(f"  ⚠ Solo hay {len(hitl_ids)} casos HITL, saltando el resto")
            break
        aid = hitl_ids[idx]
        try:
            r = post(f"/api/v1/autorizaciones/{aid}/hitl", decision)
            print(
                f"  {decision['decision']:<10}  {r['estado']:<35}  "
                f"revisor: {decision['revisor']}"
            )
        except Exception as e:
            print(f"  ✗ HITL {aid}: {e}")

    # ── 3. Resumen final ──────────────────────────────────────────────────────
    banner("Resumen")
    try:
        metricas = get("/api/v1/autorizaciones/metricas")
        total = metricas.get("total", len(resultados))
        print(f"  Total autorizaciones  {total}")
        print(f"  Automáticas           {metricas.get('automatizadas', '?')}")
        print(f"  Con HITL              {metricas.get('con_hitl', '?')}")
        print(f"  Pendientes HITL       {metricas.get('pendientes_hitl', '?')}")
        print(f"  Rechazadas            {metricas.get('rechazadas', '?')}")
    except Exception:
        pass

    # Contar estados
    conteo: dict[str, int] = {}
    for r in resultados:
        conteo[r["estado"]] = conteo.get(r["estado"], 0) + 1
    print("\n  Estados después de procesar:")
    for estado, n in sorted(conteo.items()):
        print(f"    {estado:<40} {n}")

    print("\n  Estados tras decisiones HITL: ver /api/v1/autorizaciones/")
    print(f"\n  Dashboard → http://localhost:8002/dashboard")
    print(f"  Login    → isabella@hmhospitales.es / soberania2026\n")


if __name__ == "__main__":
    main()
