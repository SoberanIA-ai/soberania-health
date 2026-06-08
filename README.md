# SoberanIA Health

Vertical salud de SoberanIA · MVP del **Agente 1 — Gestión automatizada
de autorizaciones previas** entre hospitales privados y aseguradoras
españolas.

**Cliente objetivo:** HM Hospitales (50 centros, 24 hospitales, 7.500
profesionales). Interlocutor técnico: Xavier Tarragó Bonfill, Director de
Transformación Digital.

**Stack:** FastAPI · LangGraph · Mistral API · PostgreSQL · Next.js 14 · Langfuse · Docker.

---

## Instalación en 3 comandos

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
```

Servicios:

| Servicio         | URL local                  |
|------------------|---------------------------|
| Dashboard        | http://localhost:3002      |
| API              | http://localhost:8002      |
| API docs         | http://localhost:8002/docs |
| Langfuse         | http://localhost:3000      |

---

## Usuarios de demo

| Rol           | Email                            | Contraseña     |
|---------------|----------------------------------|----------------|
| Admin         | isabella.cristancho@soberania.eu | soberania2026  |
| Recepcionista | recepcion@hmhospitales.es        | recepcion2026  |
| Supervisor    | supervisor@hmhospitales.es       | supervisor2026 |
| Auditor       | auditor@hmhospitales.es          | auditor2026    |

---

## Demo en 10 minutos

```bash
# Cargar ~50 casos de demo con todos los estados posibles
docker compose exec api python scripts/seed_dashboard.py --reset
```

Abre http://localhost:3002 y entra con cualquier usuario de demo.

Procesa un caso nuevo desde la pantalla Autorizaciones → **"+ Nueva autorización"**:

1. **Sanitas + procedimiento conocido** → autorizado automáticamente.
2. **Adeslas** → el agente usa "básica" como default y procesa con cobertura del catálogo.
3. **Aseguradora "Otra"** → HITL. El supervisor revisa, puede pedir más info,
   y la recepcionista reenvía con documentación adjunta → el agente reprocesa.

Cada caso tiene audit log con cadena SHA256 íntegra visible en el panel Auditoría AI Act.

---

## Principios no negociables

1. **Sin fechas en documentos externos** — fases secuenciales por
   dependencia, no por calendario.
2. **El LLM nunca decide códigos ni datos numéricos** — solo extrae
   texto a JSON estructurado y valida formato. Los códigos vienen
   exclusivamente de los calculadores Python.
3. **HITL obligatorio en modo real** hasta `confidence_score`
   acumulado > 0.95 en 100 autorizaciones consecutivas.
4. **Mock mode siempre disponible** — ninguna demo depende de
   credenciales externas.
5. **Test suite antes de cualquier deploy** de calculadores.
6. **Audit log es sagrado** — nunca se borra, nunca se modifica.
   Inmutabilidad criptográfica vía SHA256 encadenado.
7. **MVP primero, perfección después** — features fuera del alcance
   sec 2.2 del handoff no se construyen hasta que el piloto esté en
   marcha.

## Estado de los datos (CRÍTICO)

Todos los catálogos de aseguradoras están marcados con
`DATA_STATUS = "SIMULADO"` hasta validación con HM en Fase 0:

- **Sanitas**: 3 procedimientos en catálogo de ejemplo (RM rodilla,
  TAC abdominal, cirugía ambulatoria rodilla)
- **Adeslas**: catálogo vacío — todo dispara HITL
- **DKV**: catálogo vacío — todo dispara HITL

Cuando Isabella + HM rellenen los catálogos en Fase 0, los casos
Adeslas/DKV pasarán de HITL a happy path automáticamente. La
estructura del código no cambia — solo los dicts `CODIGOS`.

---

## Tests

```bash
docker compose exec api pytest                            # 107/107
docker compose exec api pytest --cov=app --cov-report=term # cobertura 94%
```

Suite por fase:

| Suite | Tests | Cobertura |
|-------|-------|-----------|
| `test_health.py`       | 2   | endpoint health |
| `test_calculadores.py` | 51  | unitario por función + AST check Python puro |
| `test_agent.py`        | 5   | flujo LangGraph end-to-end mock |
| `test_audit.py`        | 8   | SHA256 encadenado + detección de manipulación |
| `test_hitl.py`         | 9   | endpoint decisión humana |
| `test_e2e.py`          | 32  | 30 casos del handoff sec 13 + 2 estructura |

---

## Estado del MVP

Las 6 fases del handoff sec 16 están completadas:

| Fase | Descripción                          | Status |
|------|--------------------------------------|--------|
| 0    | Setup repo + docker + health         | ✓      |
| 1    | Calculadores Python puros            | ✓      |
| 2    | Agente LangGraph end-to-end mock     | ✓      |
| 3    | Audit log SHA256 encadenado          | ✓      |
| 4    | Frontend Next.js con RBAC completo   | ✓      |
| 5    | Test suite E2E (30 casos)            | ✓      |
| 6    | Demo ready — flujo más info completo | ✓      |

---

## Endpoints

```
GET  /api/v1/health                            health check
POST /api/v1/autorizaciones/procesar           procesar orden HL7 / texto  [auth]
GET  /api/v1/autorizaciones/                   lista todas las autorizaciones  [auth]
GET  /api/v1/autorizaciones/{id}               detalle de una autorización  [auth]
GET  /api/v1/autorizaciones/pendientes         cola HITL  [auth]
GET  /api/v1/autorizaciones/metricas           métricas para dashboard  [auth]
GET  /api/v1/autorizaciones/metricas-aiact     métricas AI Act compliance  [auth]
POST /api/v1/autorizaciones/{id}/hitl          decisión humana  [auth, supervisor/admin]
POST /api/v1/autorizaciones/{id}/reenviar      reenviar con documentación adjunta  [auth]
GET  /api/v1/audit/{autorizacion_id}           audit log + verificación integridad  [auth]
GET  /api/v1/audit/{autorizacion_id}/aiact-report  reporte AI Act estructurado  [auth]
POST /api/v1/auth/login                        autenticación → JWT
GET  /api/v1/auth/me                           datos del usuario autenticado  [auth]
GET  /api/v1/notificaciones/stream             SSE en tiempo real  [token en query]
```

## Arquitectura

```
ENTRADA (HL7 / texto libre)
        │
        ▼
┌─────────────────────────────────────────────────┐
│ CAPA LLM — solo lenguaje natural                │
│   parse_orden_medica  → Mistral Large           │
│   guardrail           → Mistral Nemo            │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│ CAPA PYTHON — fuente de verdad                  │
│   identificador_aseguradora                     │
│   verificador_cobertura                         │
│   codigos_{sanitas|adeslas|dkv}                 │
│   reglas_cobertura · plazos_respuesta           │
│   generador_solicitud                           │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│ ORQUESTACIÓN LangGraph                          │
│   parse → verify → [hitl_check] → generate →    │
│   send → monitor → process → notify             │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│ CAPA SALIDA                                     │
│   MockConnector (demo) / connectors reales      │
│   audit log SHA256 encadenado (DB)              │
│   notificación HIS (email + webhook)            │
│   Dashboard HITL Streamlit                      │
└─────────────────────────────────────────────────┘
```

## Roadmap post-MVP

Fuera del alcance del MVP (sec 2.2 del handoff), pendiente del piloto
con HM:

- Agentes 2-6 (Facturación, etc.)
- Otras aseguradoras (Mapfre, Asisa)
- Integración real con Doctoris HIS
- Frontend custom (Asaf entra después del MVP)
- Self-hosted Mistral
- Certificación AI Act formal

---

*SoberanIA — Arquitectura de Sistemas de IA SL · CIF B26912824 ·
Madrid · Documento confidencial · No distribuir sin autorización de
David Fernández.*
