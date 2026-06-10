# SoberanIA Health — Arquitectura del Sistema

> Documento maestro del repositorio. Si eres un desarrollador nuevo o una IA trabajando en este repo, lee esto primero. Contiene todo lo necesario para entender y trabajar en el sistema sin preguntar nada.

---

## 1. Qué es este sistema

**SoberanIA Health** es un agente de IA que automatiza las **autorizaciones previas** entre HM Hospitales y las aseguradoras (Sanitas, Adeslas, DKV). Cuando un médico prescribe un procedimiento cubierto por un seguro, una recepcionista solicita autorización a la aseguradora antes de realizarlo. Este proceso es hoy manual, lento y propenso a errores. El agente lo automatiza.

**Cliente:** HM Hospitales (50 centros, mayor grupo hospitalario privado de España).  
**Empresa:** SoberanIA — Arquitectura de Sistemas de IA SL (CIF B26912824, Madrid).  
**Diferenciador:** Cumplimiento AI Act (Reglamento UE 2024/1689) desde el diseño, no como añadido posterior. El sistema de autorizaciones médicas es un **sistema de alto riesgo** según el Anexo III punto 5.a del Reglamento.

---

## 2. Cómo levantar el sistema en local (3 comandos)

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
```

URLs de cada servicio:

| URL | Servicio |
|-----|----------|
| `http://localhost:3002` | Dashboard principal (Next.js) |
| `http://localhost:8002/docs` | Swagger API (FastAPI) |
| `http://localhost:8002/api/v1/health` | Health check |
| `http://localhost:3001` | Langfuse (trazas LLM) |

---

## 3. Credenciales de demo

| Email | Contraseña | Rol |
|-------|-----------|-----|
| `isabella.cristancho@soberania.eu` | `soberania2026` | admin |
| `recepcion@hmhospitales.es` | `recepcion2026` | recepcionista |
| `supervisor@hmhospitales.es` | `supervisor2026` | supervisor |
| `auditor@hmhospitales.es` | `auditor2026` | auditor |

**Roles y permisos (RBAC backend, `app/api/routes/auth.py::require_roles`):**
- `recepcionista`: `POST /procesar`, `POST /{id}/reenviar` (pantallas operativas, nueva autorización)
- `supervisor`: recepcionista + `GET /pendientes`, `POST /{id}/hitl` (cola HITL)
- `auditor`: solo lectura + `GET /metricas-aiact` (panel Auditoría AI Act)
- `admin`: acceso completo a todos los endpoints anteriores

`GET /` (listado), `GET /{id}`, `GET /metricas` y los endpoints de `audit` solo
exigen JWT válido (`Depends(get_usuario_actual)`), sin restricción de rol —
los usan las cuatro pantallas del dashboard.

---

## 4. Árbol del repositorio

```
soberania-health/
├── README.md                          # Guía de inicio rápido
├── CHANGELOG.md                       # Historial de versiones
├── .env.example                       # Variables de entorno de ejemplo
├── .gitignore
├── docker-compose.yml                 # Orquestación de servicios (api, frontend, db, langfuse)
├── Dockerfile                         # Imagen Python 3.12-slim para el servicio api
├── requirements.txt                   # Dependencias Python
├── alembic.ini                        # Configuración de Alembic
├── pytest.ini                         # Configuración de pytest
│
├── app/
│   ├── main.py                        # Punto de entrada FastAPI — registra todos los routers
│   ├── config.py                      # Settings Pydantic (lee .env)
│   │
│   ├── agent/                         # Grafo LangGraph 8 nodos — NO TOCAR
│   │   ├── graph.py                   # Grafo principal con get_grafo() + aristas condicionales
│   │   ├── nodes.py                   # Los 8 nodos (parse, verify, hitl_check, generate, send, monitor, process, notify)
│   │   ├── llm_client.py              # Cliente LLM con fallback mock determinístico
│   │   ├── prompts.py                 # System prompts del parser y guardrail
│   │   └── state.py                   # Schema del estado del grafo (AuthorizationState)
│   │
│   ├── calculadores/                  # Lógica de negocio Python puro — NO TOCAR
│   │   ├── identificador_aseguradora.py # Normaliza el nombre de aseguradora detectado
│   │   ├── verificador_cobertura.py   # Decide cobertura + requiere_autorizacion
│   │   ├── codigos_sanitas.py         # Catálogo de códigos Sanitas (CIE-10 → código aseguradora)
│   │   ├── codigos_adeslas.py         # Catálogo de códigos Adeslas
│   │   ├── codigos_dkv.py             # Catálogo de códigos DKV
│   │   ├── generador_solicitud.py     # Genera el payload de solicitud para el conector
│   │   ├── reglas_cobertura.py        # Reglas generales de cobertura
│   │   └── plazos_respuesta.py        # Plazos de respuesta por aseguradora
│   │
│   ├── conectores/                    # Adaptadores para aseguradoras
│   │   ├── base_connector.py          # Contrato abstracto BaseConnector — NO TOCAR
│   │   ├── mock_connector.py          # Mock para demos — NO TOCAR
│   │   ├── sanitas_connector.py       # [FUTURO Fase C]
│   │   ├── adeslas_connector.py       # [FUTURO Fase C]
│   │   └── dkv_connector.py           # [FUTURO Fase C]
│   │
│   ├── models/
│   │   ├── __init__.py                # Exporta Base, Autorizacion, AuditLog, Usuario
│   │   ├── database.py                # Engine SQLAlchemy + get_db()
│   │   ├── autorizacion.py            # Tabla autorizaciones + codigos_aseguradora — NO TOCAR
│   │   ├── audit.py                   # Tabla audit_log — NO TOCAR
│   │   └── usuario.py                 # Tabla usuarios (Fase A)
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py              # GET /api/v1/health
│   │   │   ├── autorizaciones.py      # CRUD autorizaciones + métricas + RBAC por endpoint — NO TOCAR
│   │   │   ├── audit.py               # GET /api/v1/audit/{id} + aiact-report — NO TOCAR
│   │   │   ├── auth.py                # POST /api/v1/auth/login, GET /api/v1/auth/me, require_roles()
│   │   │   └── notificaciones.py      # GET /api/v1/notificaciones/stream (SSE)
│   │   └── schemas/
│   │       ├── autorizacion.py        # Schemas Pydantic de autorización — NO TOCAR
│   │       ├── audit.py               # Schemas Pydantic de audit — NO TOCAR
│   │       └── usuario.py             # LoginRequest, TokenResponse, UsuarioResponse
│   │
│   ├── integrations/
│   │   ├── hl7_parser.py              # Parser HL7 v2.x — NO TOCAR
│   │   ├── hl7_mock.py                # Órdenes HL7 de ejemplo — NO TOCAR
│   │   └── doctoris_webhook.py        # Stub para integración HIS Doctoris [PENDIENTE HM]
│   │
│   ├── services/
│   │   └── autorizacion_service.py    # Orquesta procesar() y aplicar_decision_hitl()
│   │
│   └── utils/
│       ├── audit_log.py               # AuditLogger + SHA256 encadenado — NO TOCAR
│       ├── confidence.py              # Cálculo de confidence score — NO TOCAR
│       └── notifications.py           # Notificaciones email — NO TOCAR
│
├── frontend/                          # Dashboard principal (Next.js + Tailwind)
│   ├── src/                           # Código fuente React
│   ├── public/                        # Assets estáticos
│   ├── Dockerfile                     # Imagen Node para el servicio frontend
│   └── package.json                   # Dependencias Node.js
│
├── alembic/
│   └── versions/
│       ├── 0001_initial.py            # Schema inicial
│       ├── 0002_widen_cie10.py        # Amplía VARCHAR para códigos simulados
│       ├── 0003_add_usuarios.py       # Tabla usuarios + seed de demo
│       └── e08d6087a1f6_add_razon_hitl.py # Columna razon_hitl en autorizaciones
│
├── docs/
│   ├── SOBERANIA_HEALTH_HANDOFF.md    # Spec MVP original David Fernández — NUNCA TOCAR
│   ├── ARQUITECTURA.md                # Este documento
│   ├── AI_ACT_COMPLIANCE.md           # Compliance normativo AI Act
│   ├── CONECTORES.md                  # Spec de conectores de aseguradoras
│   └── DASHBOARD.md                   # Guía del dashboard para recepcionistas
│
├── scripts/
│   └── run_demo.py                    # Script demo original — NO TOCAR
│
└── tests/
    ├── conftest.py                    # Fixtures auth_admin / client_as (override JWT)
    ├── test_health.py                 # Health check
    ├── test_calculadores.py           # Calculadores Python puro
    ├── test_agent.py                  # Grafo LangGraph
    ├── test_audit.py                  # Audit log SHA256
    ├── test_hitl.py                   # Flujo HITL
    ├── test_e2e.py                    # 30 casos E2E (10×aseguradora)
    ├── test_aiact.py                  # Compliance AI Act
    ├── test_demo_extraction.py        # Extracción de aseguradora
    ├── test_auth.py                   # Autenticación JWT (Fase A)
    ├── test_rbac.py                   # RBAC por rol (403/200 en endpoints reforzados)
    └── test_error_handling.py         # Fallos LLM/conector → error_procesamiento
```

---

## 5. Flujo de una autorización de principio a fin

```
1. Recepcionista abre el dashboard y rellena el formulario de nueva autorización.

2. POST /api/v1/autorizaciones/procesar
   { "orden_h17": "<texto libre>", "modo": "mock" }

3. AutorizacionService.procesar():
   a. Crea fila Autorizacion en PostgreSQL (estado="recibido")
   b. Invoca el grafo LangGraph

4. Grafo LangGraph (8 nodos):
   ┌─ parse_orden_medica ──── LLM Mistral (mock en demo): extrae paciente, aseguradora, procedimiento
   ├─ verify_guardrail ────── Python puro: valida campos, calcula confidence
   ├─ [hitl_review] ───────── Si confidence < 0.80 → estado=pendiente_hitl, espera supervisor
   ├─ generate_solicitud ──── Python puro: genera XML/JSON para la aseguradora
   ├─ send_to_aseguradora ─── Conector (mock/real): envía solicitud
   ├─ monitor_respuesta ───── Espera respuesta (mock: inmediata)
   ├─ process_respuesta ───── Calculador Python: interpreta respuesta y decide
   └─ notify ──────────────── Registra resultado final

   Aristas condicionales (`graph.py`): si `parse_orden_medica` o
   `send_to_aseguradora` lanzan una excepción (LLM caído, conector caído),
   el nodo captura el error, escribe `estado="error_procesamiento"` y el
   grafo termina en `END` en vez de continuar con datos a medias.
   `AutorizacionService` tiene además una red de seguridad: si el grafo
   entero lanza una excepción no controlada, igualmente se persiste un
   audit entry `error_procesamiento` y la autorización se marca para HITL.

5. AuditLogger.persistir_cadena():
   - Cada paso genera un AuditLog con hash SHA256 encadenado al anterior
   - El primero tiene hash_previo="GENESIS"
   - Cualquier manipulación posterior rompe la cadena → detectable

6. Resultado almacenado en tabla autorizaciones:
   - estado: "autorizado" | "denegado" | "pendiente_hitl" | "informacion_adicional_requerida" | "error_procesamiento"
   - confidence_score: 0.0–1.0
   - numero_autorizacion: si fue autorizado (ej: "AUTH-035BB1C7")
   - razon_hitl: motivo exacto que escribió el agente (visible para el supervisor en el drawer)

7. SSE: emitir_evento("autorizacion_procesada", {...}) notifica al dashboard en tiempo real

8. Si estado=pendiente_hitl o error_procesamiento:
   - El caso aparece en "Cola HITL" (GET /pendientes)
   - El supervisor hace POST /api/v1/autorizaciones/{id}/hitl { decision, revisor, notas }
   - Estado → "aprobado_hitl" | "rechazado_hitl" | "informacion_adicional_requerida"
   - Queda registrado en audit log con hitl_intervencion=True

9. Si estado=informacion_adicional_requerida:
   - La recepcionista ve en el drawer el mensaje del supervisor (razon_hitl)
   - Sube documentación adicional y hace POST /api/v1/autorizaciones/{id}/reenviar
     { notas_adicionales, archivos_adjuntos }
   - AutorizacionService.reenviar_con_documentacion() vuelve a correr el
     agente sobre el MISMO registro, encadenando el audit log existente
     (no crea una autorización nueva)
```

---

## 6. Principios de diseño no negociables

1. **Sin fechas en documentos externos** — las fases son por dependencia, no por calendario.
2. **El LLM nunca decide códigos ni datos numéricos** — solo los calculadores Python son fuente de verdad.
3. **HITL obligatorio en modo real** — hasta confidence acumulado >0.95 en 100 autorizaciones consecutivas.
4. **Mock mode siempre disponible** — ninguna demo depende de credenciales externas.
5. **Test suite antes de cualquier deploy de calculadores** — nunca actualizar calculadores sin pasar 229/229.
6. **Audit log es sagrado** — nunca se borra, nunca se modifica. Inmutabilidad criptográfica SHA256.
7. **MVP primero, perfección después** — nada fuera del alcance hasta tener el piloto en marcha.
8. **Cada decisión técnica relevante se documenta en /docs** — un markdown por componente nuevo.
9. **Los conectores reales se prueban en PRE antes de PRO** — nunca activar directamente en producción.
10. **El dashboard tiene siempre una versión que funciona** — no romper la demo por añadir features.
11. **Datos reales nunca en el repositorio** — solo datos simulados en desarrollo.
12. **Cumplimiento AI Act no es opcional** — cada nuevo componente evalúa su impacto en los artículos 9-15.

---

## 7. Stack tecnológico

| Tecnología | Por qué |
|-----------|---------|
| **FastAPI** | API REST async, tipado fuerte, Swagger automático |
| **LangGraph** | Grafo de agente con control de flujo explícito (vs chains implícitas) |
| **Mistral (API)** | LLM para parser; sin self-hosting, sin datos de pacientes en el modelo |
| **PostgreSQL 16** | Transacciones ACID para audit log inmutable |
| **Alembic** | Migraciones versionadas, trazables en git |
| **Docker Compose** | Entorno reproducible: servicios `api` + `frontend` + `db` + `langfuse` |
| **Next.js 14 (App Router) + TypeScript** | Dashboard `frontend/`: SSR, rutas protegidas por rol, tipado end-to-end |
| **Tailwind CSS** | Estilos del dashboard, sin CSS a medida |
| **Recharts** | Gráficos del dashboard (donut, barras) |
| **python-jose + passlib** | JWT para autenticación de la API |
| **Langfuse** | Observabilidad de trazas LLM (opcional en local) |

---

## 8. Mapa completo de endpoints

| Método | Endpoint | Descripción | Acceso |
|--------|----------|-------------|--------|
| GET | `/api/v1/health` | Health check: `{status, version, calculadores_version}` | público |
| POST | `/api/v1/autorizaciones/procesar` | Procesar nueva orden: `{orden_h17, modo}` → `{autorizacion_id, estado, confidence_score}`. `estado` puede salir como `error_procesamiento` si falla el LLM o el conector | recepcionista, supervisor, admin |
| GET | `/api/v1/autorizaciones/` | Listar todas (limit=200) | auth |
| GET | `/api/v1/autorizaciones/pendientes` | Listar pendientes HITL (incluye `pendiente_hitl` y `error_procesamiento`) | supervisor, admin |
| GET | `/api/v1/autorizaciones/metricas` | KPIs: total, autorizadas, pendientes, tasa_automatizacion | auth |
| GET | `/api/v1/autorizaciones/metricas-aiact` | Métricas AI Act: supervisión, contradicciones, tiempo | auditor, admin |
| GET | `/api/v1/autorizaciones/{id}` | Detalle de una autorización | auth |
| POST | `/api/v1/autorizaciones/{id}/hitl` | Decisión HITL: `{decision, revisor, notas}` | supervisor, admin |
| POST | `/api/v1/autorizaciones/{id}/reenviar` | Reenviar con documentación adjunta: `{notas_adicionales, archivos_adjuntos}`. Reprocesa el grafo sobre el mismo registro (solo si `estado=informacion_adicional_requerida`) | recepcionista, supervisor, admin |
| GET | `/api/v1/audit/{id}` | Audit log + verificación SHA256 | auth |
| GET | `/api/v1/audit/{id}/aiact-report` | Reporte AI Act estructurado (JSON exportable) | auth |
| POST | `/api/v1/auth/login` | Login: `{email, password}` → `{access_token, usuario}` | público |
| GET | `/api/v1/auth/me` | Datos del usuario autenticado | auth |
| GET | `/api/v1/notificaciones/stream` | SSE stream de notificaciones (token en query param) | auth |
| POST | `/api/v1/integraciones/doctoris/orden` | Hook Doctoris (STUB) | — |
| GET | `/api/v1/integraciones/doctoris/status` | Estado integración Doctoris | — |

`auth` = requiere JWT válido (`Depends(get_usuario_actual)`), cualquier rol.
Los roles concretos se imponen vía `require_roles(...)` —
ver `app/api/routes/auth.py` y sección 3.

---

## 9. Configuración / Seguridad

Variables relevantes en `.env` (ver `.env.example`):

| Variable | Descripción |
|----------|-------------|
| `ENVIRONMENT` | `development` (default) o `production`. En `production`, la app **no arranca** (`RuntimeError`) si `JWT_SECRET_KEY` o `DATABASE_URL` siguen con sus valores de demo (ver `app/config.py::_validar_secretos_produccion`). |
| `CORS_ORIGINS` | Orígenes permitidos para el frontend, separados por coma. Se expone vía `settings.cors_origins_list` y reemplaza el antiguo `allow_origins=["*"]` en `app/main.py`. |
| `JWT_SECRET_KEY` / `JWT_EXPIRE_MINUTES` | Firma y expiración del token de sesión (8h por defecto). |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | Tamaño del pool de conexiones SQLAlchemy (`app/models/database.py`, `create_engine(..., pool_pre_ping=True)`). |

**Manejo de errores externos:** si una llamada al LLM (parser/guardrail) o
al conector de la aseguradora falla (timeout, 5xx, credenciales caducadas),
el agente **no devuelve un 500 sin más**. El nodo correspondiente captura
la excepción, transiciona a `estado="error_procesamiento"`, escribe su
propia entrada en el audit log (`modo_inferencia: "error"`) y marca
`hitl_requerido=True` para que el caso aparezca en la cola de revisión
humana (`GET /pendientes`). Ver sección 5, paso 4.

---

## 10. Cómo añadir una nueva aseguradora

1. Crear `app/calculadores/{aseg}_calculador.py` con `CalculadorCobertura{Aseg}`.
2. Crear `app/conectores/{aseg}_connector.py` que extiende `BaseConnector`.
3. Añadir catálogo en `data/catalogos/{aseg}_procedimientos.json`.
4. Añadir tests en `tests/test_calculadores.py` y `tests/test_e2e.py`.
5. Actualizar `MOCK_CONNECTOR` en `app/conectores/mock_connector.py` para incluir la nueva aseguradora.
6. Cambiar `DATA_STATUS` a `VALIDADO` tras validación con HM.
7. Documentar en `docs/CONECTORES.md`.

---

## 11. Cómo actualizar un catálogo de procedimientos

1. HM proporciona Google Sheet con los procedimientos validados.
2. Exportar como CSV y convertir a JSON en `data/catalogos/`.
3. Cambiar `DATA_STATUS = "VALIDADO"` en el calculador correspondiente.
4. Correr el test suite completo: `docker compose exec api pytest tests/ -v`.
5. Hacer commit con `[data] actualizar catálogo {aseg} v{N}`.

---

## 12. Datos simulados (DATA_STATUS)

Todos los calculadores tienen `DATA_STATUS` que indica el estado de los datos:

| Valor | Significado |
|-------|-------------|
| `SIMULADO` | Catálogo ficticio para demos y tests. No usar en producción. |
| `PENDIENTE_VALIDACION` | Datos reales recibidos de HM, pendientes de validación técnica. |
| `VALIDADO` | Datos validados con HM. Listo para piloto. |

Actualmente todas las aseguradoras están en `SIMULADO`. El cambio a `VALIDADO` requiere validación formal con HM Hospitales.

---

## 13. Compliance AI Act

El sistema es de **alto riesgo** según el Artículo 6 y Anexo III punto 5.a del Reglamento UE 2024/1689.

| Artículo | Descripción | Implementación |
|----------|-------------|----------------|
| Art. 9 | Gestión de riesgos | HITL obligatorio, `CONFIDENCE_THRESHOLD_HITL=0.80` |
| Art. 10 | Gobernanza de datos | `DATA_STATUS=SIMULADO`, nunca datos reales en repo |
| Art. 11 | Documentación técnica | Este documento + `docs/SOBERANIA_HEALTH_HANDOFF.md` |
| Art. 12 | Mantenimiento de registros | Audit log SHA256 encadenado, inmutable |
| Art. 13 | Transparencia | `razon_decision` en cada entrada del audit log |
| Art. 14 | Supervisión humana | Cola HITL, revisor registrado en audit log |
| Art. 15 | Exactitud y ciberseguridad | Test suite 229/229, JWT, bcrypt, RBAC por rol, CORS restringido |

Ver detalles completos en `docs/AI_ACT_COMPLIANCE.md`.

---

## 14. Glosario

| Término | Definición |
|---------|-----------|
| **HITL** | Human-in-the-Loop. Intervención humana obligatoria para casos con baja confianza. |
| **Confidence score** | Valor 0.0–1.0 que representa la certeza del agente. <0.80 → HITL. |
| **CIE-10** | Clasificación Internacional de Enfermedades, 10ª edición. Código estándar de procedimientos. |
| **HL7** | Health Level 7. Estándar de mensajería para sistemas de salud. El HIS Doctoris usa HL7 v2.x. |
| **HIS** | Hospital Information System. Sistema de gestión hospitalaria. En HM: Doctoris. |
| **Mock mode** | Modo de funcionamiento sin APIs externas reales. Respuestas simuladas reproducibles. |
| **Calculador Python** | Módulo determinista que implementa las reglas de negocio de una aseguradora. Nunca usa LLM. |
| **SHA256 encadenado** | Cada entrada del audit log incluye el hash SHA256 de la anterior. Garantiza inmutabilidad. |
| **DATA_STATUS** | Estado del catálogo de datos de una aseguradora (SIMULADO / PENDIENTE_VALIDACION / VALIDADO). |
| **SSE** | Server-Sent Events. Protocolo HTTP unidireccional (servidor → cliente) para notificaciones en tiempo real. |
| **Doctoris** | HIS de HM Hospitales. Fuente de las órdenes médicas en producción. |

---

## 15. Historial de fases

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fases 0–6 (MVP) | Agente completo, 107 tests, 3 aseguradoras mock. David Fernández. | ✅ Completado |
| **Fase A** | Dashboard v2, auth JWT, SSE, panel AI Act. Isabella Cristancho. | ✅ Completado |
| **0.3.0** | Frontend Next.js 14 (reemplaza dashboard estático), RBAC frontend completo, flujo "Más información" (`/reenviar`), `razon_hitl` en BD. | ✅ Completado |
| **Hardening (este repo, post-audit)** | RBAC backend granular por endpoint (`require_roles`), CORS vía `CORS_ORIGINS`, fail-fast de secretos en producción, estado `error_procesamiento` con aristas condicionales en el grafo, pool de conexiones DB configurable, suite ampliada a 229/229. | ✅ Completado |
| Fase B | Catálogos reales Sanitas/Adeslas/DKV validados con HM. | 🔲 Pendiente |
| Fase C | Conectores reales (APIs privadas). Requiere acceso a entornos PRE de HM. | 🔲 Pendiente |
| Fase D | Multi-hospital, escalado. | 🔲 Pendiente |