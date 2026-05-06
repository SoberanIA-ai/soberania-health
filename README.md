# SoberanIA Health

Vertical salud de SoberanIA · MVP del **Agente 1 — Gestión automatizada
de autorizaciones previas** entre hospitales privados y aseguradoras
españolas.

**Cliente objetivo:** HM Hospitales (50 centros, 24 hospitales, 7.500
profesionales). Interlocutor técnico: Xavier Tarragó Bonfill, Director de
Transformación Digital.

**Stack:** FastAPI · LangGraph · Mistral API · PostgreSQL · Streamlit ·
Playwright · Langfuse · Docker.

---

## Instalación en 3 comandos

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
```

Servicios:

| Servicio       | URL local              |
|----------------|-----------------------|
| API            | http://localhost:8002 |
| API docs       | http://localhost:8002/docs |
| Dashboard HITL | http://localhost:8503 |
| Langfuse       | http://localhost:3001 |

Los puertos están desplazados (8002/8503/3001 en lugar de 8000/8501/3000)
para no chocar con otros servicios locales. En producción / demo a HM se
mapean a los nominales.

---

## Demo en 10 minutos

```bash
docker compose exec api python scripts/run_demo.py --reset --pause
```

Procesa 3 casos secuenciales:

1. **Sanitas — happy path**: RM rodilla derecha, póliza Más Salud Plus
   → autorizado. Muestra el flujo end-to-end con cálculo Python puro.
2. **Adeslas — HITL**: catálogo simulado vacío hasta Fase 0, el sistema
   escala a revisión humana (safe-default). Supervisor decide en
   `http://localhost:8503`.
3. **Datos faltantes — HITL**: el guardrail detecta médico ausente,
   confidence cae a 0.3, se dispara HITL.

Cada caso muestra el audit log con cadena SHA256 íntegra, distinguiendo
acciones del agente vs intervención humana (🧑).

Sin `--pause` corre los 3 casos seguidos. Con `--reset` limpia la DB
antes para empezar limpia.

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
| 4    | Dashboard HITL Streamlit             | ✓      |
| 5    | Test suite E2E (30 casos)            | ✓      |
| 6    | Demo ready                           | ✓      |

---

## Endpoints

```
GET  /api/v1/health                            health check
POST /api/v1/autorizaciones/procesar           procesar orden HL7 / texto
GET  /api/v1/autorizaciones/{id}               detalle de una autorización
GET  /api/v1/autorizaciones/pendientes         cola HITL
POST /api/v1/autorizaciones/{id}/hitl          decisión humana (aprobar/rechazar/mas_info)
GET  /api/v1/audit/{autorizacion_id}           audit log + verificación integridad
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
