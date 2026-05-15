# SOBERANIA_HEALTH_HANDOFF.md
## Documento Master de Construcción — Agente de Autorizaciones MVP
### SoberanIA · Vertical Salud

---

| Campo | Valor |
|-------|-------|
| **Versión** | 1.3 |
| **Estado** | MVP completado — Listo para clonar y probar en local |
| **Fecha** | Mayo 2026 |
| **Autor** | David Fernández — SoberanIA |
| **Revisado por** | Análisis independiente (Grok) |
| **Repo** | github.com/SoberanIA-ai/soberania-health |
| **Confidencialidad** | Interno — No distribuir sin autorización |

**Historial de cambios:**

| Versión | Cambio |
|---------|--------|
| 1.0 | Versión inicial del handoff |
| 1.1 | Sección de riesgos · Diagrama Mermaid · Success criteria explícitos · Glosario · Humanización de prompts y tabla de decisiones |
| 1.2 | MVP completado · Estado real de las 6 fases · Tareas Isabella actualizadas · Comandos de demo |
| 1.3 | Instrucciones de instalación local para Isabella · 11 casos de demo · Dashboard Claude Design integrado |

---

## ÍNDICE

1. [Contexto y decisiones tomadas](#1-contexto-y-decisiones-tomadas)
2. [Alcance del MVP y success criteria](#2-alcance-del-mvp-y-success-criteria)
3. [Arquitectura técnica](#3-arquitectura-técnica)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Stack y dependencias](#5-stack-y-dependencias)
6. [Modelos de datos](#6-modelos-de-datos)
7. [Spec de los calculadores Python](#7-spec-de-los-calculadores-python)
8. [Spec del Agente 1 — Autorizaciones](#8-spec-del-agente-1--autorizaciones)
9. [Spec de integraciones](#9-spec-de-integraciones)
10. [Spec del audit log y compliance](#10-spec-del-audit-log-y-compliance)
11. [Spec del dashboard HITL](#11-spec-del-dashboard-hitl)
12. [Spec del API REST](#12-spec-del-api-rest)
13. [Test suite E2E](#13-test-suite-e2e)
14. [Configuración Docker y deploy](#14-configuración-docker-y-deploy)
15. [Variables de entorno](#15-variables-de-entorno)
16. [Plan de construcción por fases](#16-plan-de-construcción-por-fases)
17. [Checklist pre-demo](#17-checklist-pre-demo)
18. [Tareas de Isabella — Domain expert](#18-tareas-de-isabella--domain-expert)
19. [Reglas del proyecto](#19-reglas-del-proyecto)
20. [Glosario y assumptions](#20-glosario-y-assumptions)

---


---

## ESTADO ACTUAL DEL MVP — Mayo 2026

> Esta sección resume el estado real del código. Las secciones siguientes describen el spec completo.

### MVP completado — 6 fases en GitHub

| Fase | Descripción | Status | Tests | Commit |
|------|-------------|--------|-------|--------|
| 0 | Setup repo + Docker + PostgreSQL + health | ✅ | 2 | c68a922 |
| 1 | Calculadores Python puros (8 módulos) | ✅ | 53 | 4c45b10 |
| 2 | Agente LangGraph end-to-end mock | ✅ | 58 | 1884258 |
| 3 | Audit log SHA256 encadenado + endpoints REST | ✅ | 66 | ecb97df |
| 4 | Dashboard HITL Streamlit | ✅ | 75 | fa6833c |
| 5 | Test suite E2E 30 casos | ✅ | 107 | dad03c0 |
| 6 | Demo ready — script automatizado + README | ✅ | 107 | c4296f3 |

**Resultado: 107/107 tests · 94% cobertura · Demo funcional en mock mode**

### Cómo instalar y probar en local (para Isabella y el equipo)

```bash
# 1. Clonar el repositorio
git clone https://github.com/SoberanIA-ai/soberania-health.git
cd soberania-health

# 2. Configurar variables de entorno
cp .env.example .env
# El .env por defecto usa mock mode — no necesitas API key de Mistral

# 3. Levantar el sistema
docker compose up -d --build
docker compose exec api alembic upgrade head

# 4. Cargar casos de demo
docker compose exec api python scripts/run_demo.py --reset
```

**URLs una vez levantado:**

| Servicio | URL |
|----------|-----|
| Dashboard HITL (principal) | http://localhost:8002/dashboard |
| API REST + documentación | http://localhost:8002/docs |
| Health check | http://localhost:8002/api/v1/health |
| Langfuse (observabilidad) | http://localhost:3001 |

**Para correr los tests:**
```bash
docker compose exec api pytest tests/ -v
# Resultado esperado: 107/107 pasando, cobertura 94%
```

**Los 11 casos de demo cubren:**

| Caso | Paciente | Aseguradora | Resultado |
|------|---------|-------------|-----------|
| 1 | María García López | Sanitas Más Salud Plus | ✅ Autorizado automático |
| 2 | Andrea Ruiz | Adeslas Completa | 🔄 HITL (catálogo vacío) |
| 3 | Pedro Anónimo | Sanitas (sin médico) | 🔄 HITL (datos faltantes) |
| 4 | Carlos López | Sanitas Básica | ✅ Autorizado automático |
| 5 | Roberto Vega | Sanitas Óptima (urgente) | ✅ Autorizado automático |
| 6 | Sofía Núñez | Adeslas Básica | 🔄 HITL (catálogo vacío) |
| 7 | Manuel Diez | Adeslas Premium (urgente) | 🔄 HITL (catálogo vacío) |
| 8 | Cristina Marín | DKV Integral | 🔄 HITL (catálogo vacío) |
| 9 | Patricia Roldán | DKV Top (urgente) | 🔄 HITL (catálogo vacío) |
| 10 | Javier Soto | Sanitas (sin póliza) | 🔄 HITL (confidence 75%) |
| 11 | Lucía Mateo | Mapfre | 🔄 HITL (no soportada en MVP) |

**Nota importante:** Los casos de Adeslas y DKV van a HITL porque sus catálogos están vacíos (`DATA_STATUS = "SIMULADO"`). Cuando Isabella rellene el Google Sheet con los códigos reales de HM, estos casos pasarán a aprobación automática sin tocar el código.

Abrir `http://localhost:8503` para el dashboard HITL en vivo.

### Estado de los datos (CRÍTICO para Isabella)

Todos los catálogos están marcados `DATA_STATUS = "SIMULADO"`:

| Aseguradora | Estado catálogo | Comportamiento actual |
|-------------|----------------|----------------------|
| Sanitas | 3 procedimientos de ejemplo | Happy path en demo |
| Adeslas | Vacío | Todo va a HITL (correcto) |
| DKV | Vacío | Todo va a HITL (correcto) |

**Cuando Isabella rellene los catálogos con datos reales de HM, los casos Adeslas/DKV pasarán automáticamente a happy path. La estructura del código no cambia — solo los dicts `CODIGOS`.**

### Versiones reales de dependencias (ajustadas durante construcción)

El handoff original tenía versiones que estaban yanked en PyPI. Las versiones reales en producción:

| Paquete | Handoff v1.1 | Real |
|---------|-------------|------|
| langgraph | 0.1.0 | 0.1.19 |
| langfuse | 2.0.0 | 2.46.0 |
| pydantic | 2.7.0 | 2.8.2 |
| hl7 | python-hl7==0.3.5 | hl7==0.3.5 |
| pytest-asyncio | 0.23.0 | 0.23.8 |

---

## 1. CONTEXTO Y DECISIONES TOMADAS

### 1.1 Qué es este proyecto

SoberanIA Health es el primer vertical de salud de SoberanIA. El objetivo es automatizar la gestión de autorizaciones previas entre hospitales privados y aseguradoras españolas — el cuello de botella administrativo más costoso del back-office sanitario privado en España.

El cliente objetivo inicial es **HM Hospitales** (50 centros asistenciales, 24 hospitales, 7.500 profesionales). El interlocutor técnico es **Xavier Tarragó Bonfill**, Director de Transformación Digital.

El documento técnico completo está en `SoberanIA_HM_Hospitales_v9.docx` (versión 3.1).

### 1.2 Decisiones tomadas — no reabrir

Estas decisiones están tomadas. No requieren debate en cada sesión de trabajo.

| Decisión | Elegido | Razón |
|----------|---------|-------|
| Repositorio | Nuevo: `soberania-health` | Separado de producción Asintex. Sin riesgo de contaminación |
| Asaf | Entra después del MVP | Se enfoca en producción Asintex. Isabella lidera salud |
| Datos iniciales | Simulados (investigación pública) | Construimos ahora. HM valida y ajusta en Fase 0 |
| Domain expert | Isabella + HM en Fase 0 | Sin contratar externos hasta validar el modelo |
| LLM | API Mistral — sin self-hosted | Self-hosted es coste y tiempo que el MVP no necesita |
| Alcance | Solo Agente 1 (Autorizaciones) | Entramos rápido, escalamos con datos reales |
| Aseguradoras | Sanitas, Adeslas, DKV | Las de mayor volumen en hospitales privados españoles |
| Frontend | Streamlit para HITL | Suficiente para la demo. UI real viene después |

### 1.3 Principio fundamental — no negociable

**Los calculadores Python son la única fuente de verdad para códigos, tarifas y reglas. El LLM nunca decide datos numéricos ni códigos. El LLM solo convierte lenguaje natural en datos estructurados y genera comunicaciones.**

Si en algún momento del desarrollo se propone que el LLM elija un código de procedimiento o una tarifa — es un error de diseño que se rechaza en PR.

### 1.4 Riesgos del MVP y mitigaciones

Somos honestos sobre los riesgos desde el inicio. Un sistema de alto riesgo (salud + AI Act) exige que los riesgos estén documentados y gestionados explícitamente.

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Precisión de los calculadores Python — los catálogos iniciales se construyen con datos públicos no validados por HM | Media | Alto | Test suite exhaustivo + HITL al 100% en modo real hasta validación + monitor de rechazos automático |
| Cambios en portales de aseguradoras rompen el RPA | Alta | Medio | Mock mode siempre disponible · Priorizar APIs donde existan · Monitor de rechazos como señal temprana · Rollback automático de calculadores |
| Integración HL7 con Doctoris más compleja de lo esperado | Baja-Media | Alto | Mock HL7 primero · Integración real solo después de Fase 0 con equipo técnico de HM |
| Latencia o coste de API Mistral en producción | Media | Bajo | Mistral Nemo como guardrail (modelo ligero) · Cache de resultados frecuentes · Límites de uso configurables |
| Adopción baja por el personal administrativo de HM | Baja | Medio | Dashboard HITL intuitivo · HITL al 100% al inicio (sin presión) · Formación breve antes del piloto · Champion interno identificado en Fase 0 |
| Datos de pacientes: incidente de privacidad en fase de desarrollo | Baja | Muy alto | Solo datos simulados en desarrollo · Datos reales solo en servidor de HM · Nunca datos reales en repositorio de código |



## 2. ALCANCE DEL MVP Y SUCCESS CRITERIA

### 2.1 Lo que construimos

```
Agente 1 — Gestión automatizada de autorizaciones previas
├── 3 aseguradoras: Sanitas, Adeslas, DKV
├── 20-30 procedimientos de mayor volumen
├── Flujo completo: orden médica → autorización → notificación
├── Mock mode: demo sin credenciales reales de aseguradoras
├── HITL dashboard: supervisión humana de cada decisión
└── Audit log: registro inmutable de cada acción
```

### 2.2 Fuera del alcance del MVP

```
❌ Agente 2 (Facturación) — después del piloto con HM
❌ Mapfre, Asisa y otras aseguradoras — después del piloto
❌ Integración real con Doctoris HIS — después de Fase 0 con HM
❌ Frontend custom — Streamlit es suficiente para la demo
❌ Self-hosted Mistral — la API es suficiente para el MVP
❌ Certificación AI Act formal — diseño compliant, certificación después
❌ Agentes 3-6 de la plataforma RCM — roadmap post-piloto
```

### 2.3 Success criteria — cuándo el MVP está listo para HM

El MVP está listo para mostrar a Xavier Tarragó cuando cumple **todos** estos criterios. No cuando cumple la mayoría.

**Criterios técnicos:**

| Criterio | Medición | Umbral |
|----------|----------|--------|
| Flujo end-to-end en mock mode | Demo sin errores | 3 casos de demo sin fallo |
| Test suite E2E | `pytest tests/test_e2e.py` | 30/30 pasan |
| Cobertura de tests | `pytest --cov` | > 80% |
| Tiempo de respuesta | Desde orden hasta solicitud enviada | < 30 segundos |
| Confidence scoring | Visible en dashboard | Presente en cada autorización |
| Audit log | SHA256 encadenado sin huecos | 100% de acciones |
| HITL | Aprobar/rechazar desde dashboard | Sin errores en 10 pruebas |
| Instalación | README instrucciones | David instala solo sin ayuda técnica |

**Criterio de calidad:**
> David hace la demo de 10 minutos sin interrupciones y puede responder preguntas técnicas básicas sobre cómo funciona el sistema.

### 2.4 Diagrama de arquitectura

```mermaid
flowchart TD
    A[Orden médica\nHL7 / Mock] --> B[Parser LLM\nMistral Large]
    B --> C[Guardrail\nMistral Nemo]
    C --> D{Confidence\n≥ 0.80?}

    D -- Sí --> E[Verificador cobertura\nPython puro]
    D -- No --> F[Cola HITL\nRevisión humana]
    F --> E

    E --> G{¿Requiere\nautorización?}
    G -- No --> H[Notificar:\nNo requiere auth]
    G -- Sí --> I[Generador solicitud\nPython puro]

    I --> J{Modo}
    J -- Mock --> K[Mock Connector]
    J -- Real --> L{Aseguradora}
    L -- Sanitas --> M[Sanitas Connector]
    L -- Adeslas --> N[Adeslas Connector]
    L -- DKV --> O[DKV Connector]

    K --> P[Procesar respuesta]
    M --> P
    N --> P
    O --> P

    P --> Q[Notificar resultado]
    Q --> R[Audit Log SHA256]

    style B fill:#dbeafe,stroke:#3b82f6
    style C fill:#dbeafe,stroke:#3b82f6
    style E fill:#dcfce7,stroke:#16a34a
    style I fill:#dcfce7,stroke:#16a34a
    style F fill:#fef9c3,stroke:#ca8a04
    style R fill:#fee2e2,stroke:#dc2626
```

**Leyenda:** 🔵 LLM (solo lenguaje natural) · 🟢 Python puro (fuente de verdad) · 🟡 HITL (humano) · 🔴 Audit log (inmutable)

### 2.5 Roadmap de fases (secuencial, sin fechas)

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ FASE 0  │ →  │ FASE 1  │ →  │ FASE 2  │ →  │ FASE 3  │
│  Setup  │    │  Calc.  │    │ Agente  │    │  Tests  │
│  repo   │    │ Python  │    │ + Integ │    │   E2E   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     ↓              ↓              ↓              ↓
 Repo listo    30 tests       Flujo mock     30/30 OK
 DB migrada    unitarios      end-to-end
 Health OK     pasando        funciona
                                   ↓
                         ┌─────────┐    ┌─────────┐
                         │ FASE 4  │ →  │ FASE 5  │
                         │  Audit  │    │  Demo   │
                         │  +HITL  │    │  ready  │
                         └─────────┘    └─────────┘
                                             ↓
                                      David hace demo
                                      sin ayuda técnica
                                      → Contacto HM
```

---

## 3. ARQUITECTURA TÉCNICA

### 3.1 Diagrama de flujo

```
ENTRADA
────────────────────────────────────────────────────
Orden médica (HL7 simulado o real)
  → Datos: paciente, procedimiento, médico, fecha

CAPA LLM — SOLO LENGUAJE NATURAL
────────────────────────────────────────────────────
Parser Mistral Large
  → Extrae datos estructurados de la orden médica
  → Identifica aseguradora, procedimiento, diagnóstico CIE-10
  → Output: JSON limpio y estructurado

Guardrail Mistral Nemo
  → Valida que el output del parser es coherente
  → Detecta campos faltantes o inconsistentes
  → Si confidence < umbral → HITL obligatorio

CAPA PYTHON — FUENTE DE VERDAD
────────────────────────────────────────────────────
calculadores/
  ├── identificador_aseguradora.py
  │     → Determina aseguradora y tipo de póliza
  ├── verificador_cobertura.py
  │     → ¿Este procedimiento requiere autorización?
  │     → ¿Está cubierto por esta póliza?
  ├── codigos_sanitas.py
  │     → Código correcto para este procedimiento en Sanitas
  ├── codigos_adeslas.py
  │     → Código correcto para este procedimiento en Adeslas
  ├── codigos_dkv.py
  │     → Código correcto para este procedimiento en DKV
  ├── reglas_cobertura.py
  │     → Reglas de qué procedimientos requieren auth previa
  ├── plazos_respuesta.py
  │     → SLA de respuesta por aseguradora y urgencia
  └── generador_solicitud.py
        → Construye el formulario de solicitud correcto
        → Formato específico por aseguradora

ORQUESTACIÓN — LANGGRAPH
────────────────────────────────────────────────────
Estado del grafo:
  → orden_medica_raw
  → datos_estructurados (output parser)
  → aseguradora_identificada
  → cobertura_verificada
  → codigo_procedimiento
  → solicitud_generada
  → estado_envio
  → respuesta_aseguradora
  → audit_entries

Nodos del grafo:
  1. parse_orden_medica
  2. verificar_cobertura
  3. generar_solicitud
  4. hitl_check (si confidence < umbral)
  5. enviar_solicitud (API o RPA o mock)
  6. monitorizar_respuesta
  7. procesar_respuesta
  8. notificar_resultado
  9. registrar_audit

CAPA DE CONECTIVIDAD — ASEGURADORAS
────────────────────────────────────────────────────
conectores/
  ├── sanitas_connector.py (API si existe, RPA Playwright si no)
  ├── adeslas_connector.py
  ├── dkv_connector.py
  └── mock_connector.py (para demo sin credenciales)

CAPA DE SALIDA
────────────────────────────────────────────────────
  → Notificación a recepción (email + webhook HIS)
  → Actualización de estado en base de datos
  → Entrada en audit log con SHA256
  → Dashboard HITL actualizado
```

### 3.2 Flujo de estados LangGraph

```python
# Estados posibles del grafo
class AuthorizationState(TypedDict):
    # Input
    orden_raw: str
    modo: Literal["real", "mock"]

    # Procesamiento
    datos_estructurados: dict
    confidence_score: float
    aseguradora: str
    tipo_poliza: str
    procedimiento_codigo: str
    requiere_autorizacion: bool
    cobertura_verificada: bool

    # Solicitud
    solicitud_generada: dict
    documentos_adjuntos: list

    # Estado
    estado: Literal[
        "recibido", "parseado", "verificado",
        "pendiente_hitl", "aprobado_hitl",
        "enviado", "pendiente_respuesta",
        "autorizado", "denegado", "error"
    ]

    # Resultado
    respuesta_aseguradora: dict
    numero_autorizacion: str

    # Audit
    audit_entries: list
    errores: list

# Transiciones del grafo
START → parse_orden_medica
parse_orden_medica → verificar_cobertura
verificar_cobertura → [hitl_check | generar_solicitud]
hitl_check → [generar_solicitud | END(requiere_info_adicional)]
generar_solicitud → enviar_solicitud
enviar_solicitud → monitorizar_respuesta
monitorizar_respuesta → [procesar_respuesta | reenviar_recordatorio]
procesar_respuesta → notificar_resultado
notificar_resultado → registrar_audit → END
```

---

## 4. ESTRUCTURA DEL REPOSITORIO

```
soberania-health/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.prod.yml
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entrypoint
│   ├── config.py                  # Settings desde .env
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py               # Definición del grafo LangGraph
│   │   ├── nodes.py               # Implementación de cada nodo
│   │   ├── state.py               # AuthorizationState TypedDict
│   │   └── prompts.py             # System prompts del agente
│   │
│   ├── calculadores/
│   │   ├── __init__.py
│   │   ├── identificador_aseguradora.py
│   │   ├── verificador_cobertura.py
│   │   ├── codigos_sanitas.py
│   │   ├── codigos_adeslas.py
│   │   ├── codigos_dkv.py
│   │   ├── reglas_cobertura.py
│   │   ├── plazos_respuesta.py
│   │   └── generador_solicitud.py
│   │
│   ├── conectores/
│   │   ├── __init__.py
│   │   ├── base_connector.py      # Clase abstracta
│   │   ├── sanitas_connector.py
│   │   ├── adeslas_connector.py
│   │   ├── dkv_connector.py
│   │   └── mock_connector.py      # Para demo
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── autorizacion.py        # SQLAlchemy models
│   │   ├── audit.py
│   │   └── database.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── autorizaciones.py
│   │   │   ├── health.py
│   │   │   └── audit.py
│   │   └── schemas/
│   │       ├── autorizacion.py    # Pydantic schemas
│   │       └── audit.py
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── hl7_parser.py          # Parser de mensajes HL7
│   │   └── hl7_mock.py            # Mock de Doctoris HIS
│   │
│   └── utils/
│       ├── __init__.py
│       ├── audit_log.py           # SHA256 + inmutabilidad
│       ├── confidence.py          # Scoring
│       └── notifications.py      # Email + webhook
│
├── dashboard/
│   └── hitl_dashboard.py          # Streamlit HITL supervisor
│
├── data/
│   ├── codigos/
│   │   ├── sanitas_codigos.json   # Generado desde Google Sheet Isabella
│   │   ├── adeslas_codigos.json
│   │   └── dkv_codigos.json
│   ├── procedimientos_top20.json  # 20 procedimientos más frecuentes
│   └── casos_test/                # 30 casos E2E
│       ├── caso_001_sanitas_rm.json
│       ├── caso_002_adeslas_tac.json
│       └── ...
│
├── tests/
│   ├── __init__.py
│   ├── test_calculadores.py       # Unit tests Python puro
│   ├── test_agent.py              # Integration tests agente
│   ├── test_conectores.py         # Tests mock connectors
│   └── test_e2e.py                # 30 casos end-to-end
│
├── scripts/
│   ├── seed_database.py           # Inicializa DB con datos base
│   ├── import_codigos.py          # Importa JSON de Isabella
│   └── run_demo.py                # Script demo para HM
│
└── docs/
    ├── SOBERANIA_HEALTH_HANDOFF.md  # Este documento
    ├── arquitectura.md
    └── casos_de_uso.md
```

---

## 5. STACK Y DEPENDENCIAS

### 5.1 Dependencias Python (requirements.txt)

```txt
# Framework
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
pydantic-settings==2.3.0

# Agente IA
langchain==0.2.0
langgraph==0.1.0
langfuse==2.0.0

# LLM
mistralai==1.0.0

# Base de datos
sqlalchemy==2.0.0
alembic==1.13.0
psycopg2-binary==2.9.9

# HL7
python-hl7==0.3.5

# RPA
playwright==1.44.0

# Dashboard HITL
streamlit==1.35.0

# Utils
python-dotenv==1.0.0
httpx==0.27.0
tenacity==8.3.0

# Observabilidad
structlog==24.1.0

# Testing
pytest==8.2.0
pytest-asyncio==0.23.0
pytest-cov==5.0.0
```

### 5.2 Versiones de servicios (Docker)

```yaml
postgres: 16-alpine
redis: 7-alpine
langfuse: latest
```

---

## 6. MODELOS DE DATOS

### 6.1 Tabla: autorizaciones

```sql
CREATE TABLE autorizaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Orden médica
    orden_id VARCHAR(100),
    paciente_id VARCHAR(100),
    paciente_nombre VARCHAR(200),
    medico_id VARCHAR(100),
    medico_nombre VARCHAR(200),
    procedimiento_descripcion TEXT,
    procedimiento_cie10 VARCHAR(20),
    fecha_solicitud DATE,
    urgencia VARCHAR(20) DEFAULT 'normal',

    -- Aseguradora
    aseguradora VARCHAR(50),
    poliza_numero VARCHAR(100),
    poliza_tipo VARCHAR(50),

    -- Procesamiento
    procedimiento_codigo VARCHAR(50),
    confidence_score DECIMAL(5,4),
    requiere_autorizacion BOOLEAN,
    cobertura_verificada BOOLEAN,

    -- Estado
    estado VARCHAR(50) DEFAULT 'recibido',
    modo VARCHAR(10) DEFAULT 'real',

    -- Solicitud enviada
    solicitud_enviada_at TIMESTAMP,
    solicitud_referencia VARCHAR(100),

    -- Respuesta aseguradora
    respuesta_recibida_at TIMESTAMP,
    numero_autorizacion VARCHAR(100),
    autorizado BOOLEAN,
    motivo_denegacion TEXT,

    -- HITL
    hitl_requerido BOOLEAN DEFAULT FALSE,
    hitl_revisado_at TIMESTAMP,
    hitl_revisor VARCHAR(100),
    hitl_decision VARCHAR(20),
    hitl_notas TEXT,

    -- Metadata
    raw_orden TEXT,
    raw_respuesta TEXT
);
```

### 6.2 Tabla: audit_log

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    autorizacion_id UUID REFERENCES autorizaciones(id),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Acción
    accion VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    resultado VARCHAR(50),

    -- Datos
    datos_entrada JSONB,
    datos_salida JSONB,
    confidence_score DECIMAL(5,4),

    -- Integridad
    hash_sha256 VARCHAR(64) NOT NULL,
    hash_previo VARCHAR(64),

    -- AI Act
    modelo_usado VARCHAR(100),
    version_calculador VARCHAR(20),
    hitl_intervencion BOOLEAN DEFAULT FALSE
);
```

### 6.3 Tabla: codigos_aseguradora

```sql
CREATE TABLE codigos_aseguradora (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aseguradora VARCHAR(50) NOT NULL,
    procedimiento_descripcion TEXT NOT NULL,
    cie10_codigo VARCHAR(20),
    aseguradora_codigo VARCHAR(50) NOT NULL,
    requiere_autorizacion BOOLEAN DEFAULT TRUE,
    documentacion_requerida JSONB,
    copago_euros DECIMAL(8,2),
    notas TEXT,
    version VARCHAR(20) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_codigo_aseguradora
ON codigos_aseguradora(aseguradora, cie10_codigo, version)
WHERE activo = TRUE;
```

---

## 7. SPEC DE LOS CALCULADORES PYTHON

### 7.1 Principio de diseño — CRÍTICO

```
REGLA DE ORO:
Los calculadores son módulos Python puros.
No importan langchain. No importan mistral.
No hacen llamadas HTTP. No hacen I/O.
Son funciones puras: input → output determinista.

Si un calculador necesita acceder a internet
o a un modelo de lenguaje → es un error de diseño.

Los calculadores se actualizan SOLO mediante:
1. Detección de rechazo anómalo (monitor automático)
2. Comunicación oficial de la aseguradora
3. Proceso de validación + test suite completo
4. Deploy con HITL al 100% en esa aseguradora
```

### 7.1b Estado de los datos — LEER ANTES DE CONSTRUIR

```
⚠️  IMPORTANTE: DATOS SIMULADOS EN EL MVP

Los catálogos de códigos de Sanitas, Adeslas y DKV
NO son públicos en su totalidad. Los códigos que
aparecen en este documento son SIMULADOS para
ilustrar la estructura correcta.

PARA EL MVP:
- Usar datos simulados marcados explícitamente
- La estructura del código es correcta y production-ready
- Los valores son placeholder hasta Fase 0 con HM

PARA PRODUCCIÓN (Fase 0 con HM):
Los catálogos reales se obtienen de:
1. HM aporta sus catálogos operativos por aseguradora
2. Cada aseguradora valida sus códigos directamente
3. El back-office de HM valida procedimiento por procedimiento
4. Los tests E2E se ejecutan con datos reales antes de activar

NUNCA usar los datos simulados en producción real.
Cada módulo tiene un flag DATA_STATUS que lo indica.
```

### 7.2 codigos_sanitas.py

```python
"""
Calculador de códigos Sanitas.
Fuente de verdad para procedimientos Sanitas.

⚠️  DATA_STATUS = "SIMULADO"
    Los códigos son ejemplos de estructura, no valores reales.
    Ver sección 7.1b del handoff antes de usar en producción.

Proceso de actualización a datos reales (Fase 0):
1. HM proporciona catálogo operativo Sanitas
2. Revisar y validar cada código con back-office HM
3. Ejecutar test_calculadores.py completo
4. Deploy con HITL al 100% en Sanitas hasta estabilización
5. Cambiar DATA_STATUS a "VALIDADO" + fecha de validación

NUNCA modificar sin pasar el test suite completo.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"  # Cambiar a "VALIDADO_YYYY-MM-DD" tras Fase 0

class TipoPolizaSanitas(Enum):
    BASICA = "basica"
    MAS_SALUD = "mas_salud"
    MAS_SALUD_PLUS = "mas_salud_plus"
    OPTIMA = "optima"
    PREMIUM = "premium"

@dataclass
class CodigoSanitas:
    codigo: str               # Código interno Sanitas — PENDIENTE validación
    descripcion: str
    requiere_autorizacion: bool
    documentacion_requerida: list[str]
    copago_euros: float       # PENDIENTE: confirmar con HM
    plazo_respuesta_horas: int  # PENDIENTE: confirmar con Sanitas
    notas: Optional[str] = None

# ─────────────────────────────────────────────────────────────
# CATÁLOGO SIMULADO — solo para desarrollo y demo del MVP
# Fuente real: HM back-office + validación directa con Sanitas
# ─────────────────────────────────────────────────────────────
CODIGOS: dict[str, dict[str, CodigoSanitas]] = {

    # RADIOLOGÍA
    # ⚠️ Códigos simulados — confirmar con Sanitas en Fase 0
    "SIM_RM_SIN_CONTRASTE": {
        TipoPolizaSanitas.BASICA.value: CodigoSanitas(
            codigo="SIM-001",  # ← SIMULADO
            descripcion="Resonancia magnética sin contraste",
            requiere_autorizacion=True,
            documentacion_requerida=[
                "informe_clinico",
                "justificacion_medica"
            ],
            copago_euros=0.0,
            plazo_respuesta_horas=48,  # ← SIMULADO
            notas="DATO SIMULADO — validar con Sanitas en Fase 0"
        ),
        TipoPolizaSanitas.MAS_SALUD.value: CodigoSanitas(
            codigo="SIM-001",  # ← SIMULADO
            descripcion="Resonancia magnética sin contraste",
            requiere_autorizacion=True,
            documentacion_requerida=["informe_clinico"],
            copago_euros=0.0,
            plazo_respuesta_horas=24,  # ← SIMULADO
            notas="DATO SIMULADO — validar con Sanitas en Fase 0"
        ),
    },

    "SIM_RM_CON_CONTRASTE": {
        # ← PENDIENTE: rellenar en Fase 0 con datos reales
    },

    "SIM_TAC_ABDOMINAL": {
        # ← PENDIENTE: rellenar en Fase 0 con datos reales
    },

    # Añadir aquí los 20-30 procedimientos top
    # usando el Google Sheet de Isabella como base
    # y validando con HM en Fase 0
}


def get_codigo(
    procedimiento_sim_id: str,
    tipo_poliza: str
) -> Optional[CodigoSanitas]:
    """
    Devuelve el código Sanitas para un procedimiento y póliza.
    Devuelve None si el procedimiento no está en el catálogo.

    None → HITL obligatorio (el agente nunca falla silenciosamente).
    """
    if DATA_STATUS == "SIMULADO":
        # En modo simulado, cualquier procedimiento no mapeado
        # va a HITL — comportamiento correcto y seguro
        pass

    procedimiento = CODIGOS.get(procedimiento_sim_id)
    if not procedimiento:
        return None
    return procedimiento.get(tipo_poliza)


def requiere_autorizacion(
    procedimiento_sim_id: str,
    tipo_poliza: str
) -> bool:
    """
    True si requiere autorización previa.
    Safe default: True si el procedimiento no está en el catálogo.
    Mejor pedir una autorización innecesaria que no pedirla.
    """
    codigo = get_codigo(procedimiento_sim_id, tipo_poliza)
    if codigo is None:
        return True
    return codigo.requiere_autorizacion


def get_version() -> str:
    return f"{VERSION} ({DATA_STATUS})"
```

### 7.3 codigos_adeslas.py y codigos_dkv.py

Misma estructura que `codigos_sanitas.py`. Mismas advertencias. Mismo `DATA_STATUS = "SIMULADO"`.

```python
"""
Calculador de códigos Adeslas.

⚠️  DATA_STATUS = "SIMULADO"
    Los códigos son ejemplos de estructura, no valores reales.

Proceso de actualización a datos reales (Fase 0):
1. HM proporciona catálogo operativo Adeslas
2. Revisar y validar cada código con back-office HM
3. Ejecutar test_calculadores.py completo
4. Deploy con HITL al 100% en Adeslas hasta estabilización
5. Cambiar DATA_STATUS a "VALIDADO_YYYY-MM-DD"

Diferencias relevantes de Adeslas vs Sanitas (a investigar en Fase 0):
- ¿Tiene API o solo portal web?
- ¿Usa nomenclatura propia o adaptación de CIE-10?
- ¿Los copagos son fijos o variables por póliza?
- ¿Los plazos de respuesta son distintos por tipo de procedimiento?
"""

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"

# Estructura idéntica a codigos_sanitas.py
# Rellenar con datos reales en Fase 0
CODIGOS: dict = {}  # ← vacío hasta Fase 0


# ─────────────────────────────────────────────────────────────
# DKV — misma estructura, mismas advertencias
# ─────────────────────────────────────────────────────────────

"""
Calculador de códigos DKV.

⚠️  DATA_STATUS = "SIMULADO"

Diferencias relevantes de DKV vs Sanitas/Adeslas (a investigar):
- DKV tiene acuerdo con HM confirmado (fuente: Galiciapress 2026)
- ¿Tiene API de autorizaciones o solo portal web?
- ¿Usa códigos propios o estándar SENAME?
- Verificar si los copagos siguen el convenio DKV-HM actual
"""

VERSION = "1.0.0-simulado"
DATA_STATUS = "SIMULADO"
CODIGOS: dict = {}  # ← vacío hasta Fase 0
```

### 7.4 reglas_cobertura.py

```python
"""
Reglas de cobertura por aseguradora y tipo de póliza.
Define qué procedimientos requieren autorización previa.

⚠️  DATA_STATUS = "SIMULADO"
    Las reglas son estructura de ejemplo, no reglas reales.

En producción estas reglas se obtienen de:
- Contratos HM-aseguradora (confidenciales, aporta HM)
- Documentación oficial de cada aseguradora
- Validación con back-office HM procedimiento a procedimiento

Principio safe-default:
Si un procedimiento no está en las reglas → requiere_auth = True
Nunca asumimos que no requiere autorización si no lo sabemos.
"""

DATA_STATUS = "SIMULADO"

# Estructura: {aseguradora: {tipo_poliza: {cie10: requiere_auth}}}
# ← VACÍO hasta Fase 0. El safe-default en verificador_cobertura.py
#   garantiza que todo va a HITL si no está mapeado.
REGLAS: dict = {}


def requiere_autorizacion_previa(
    aseguradora: str,
    tipo_poliza: str,
    procedimiento_id: str
) -> bool:
    """
    Safe default: True si no tenemos la regla.
    En producción, estas reglas vendrán de Fase 0 con HM.
    """
    aseg = REGLAS.get(aseguradora.lower(), {})
    poliza = aseg.get(tipo_poliza, {})
    return poliza.get(procedimiento_id, True)  # True = safe default
```

### 7.5 plazos_respuesta.py

```python
"""
SLAs de respuesta por aseguradora y urgencia.

⚠️  DATA_STATUS = "SIMULADO"
    Los plazos son estimaciones del sector, no contractuales.

En producción estos plazos se obtienen de:
- Contratos HM-aseguradora (SLAs comprometidos)
- Regulación: AI Act no impone SLAs, pero el contrato con HM sí
- Validar con HM cuándo se dispara un recordatorio real

Nota: los SLAs de respuesta de aseguradoras en España
no están regulados uniformemente. Varían por contrato.
"""

DATA_STATUS = "SIMULADO"

# Estimaciones del sector — NO contractuales
# Confirmar con HM los SLAs reales de cada aseguradora
PLAZOS_HORAS: dict = {
    "sanitas": {
        "normal": 48,    # ← estimación, no contractual
        "urgente": 4,    # ← estimación, no contractual
    },
    "adeslas": {
        "normal": 48,
        "urgente": 4,
    },
    "dkv": {
        "normal": 72,
        "urgente": 6,
    },
}

DEFAULT_PLAZO_HORAS = 72  # Si no tenemos el dato, 72h es conservador


def get_plazo_horas(aseguradora: str, urgente: bool = False) -> int:
    tipo = "urgente" if urgente else "normal"
    plazos = PLAZOS_HORAS.get(aseguradora.lower(), {})
    return plazos.get(tipo, DEFAULT_PLAZO_HORAS)
```

### 7.6 generador_solicitud.py

```python
"""
Genera el formulario de solicitud de autorización
en el formato específico de cada aseguradora.
Python puro — sin LLM, sin I/O externo.

⚠️  DATA_STATUS = "SIMULADO"
    Los campos del formulario son estimados de investigación pública.

En producción los formularios se obtienen de:
- Acceso directo a los portales de cada aseguradora (Fase 0)
- Isabella documenta cada campo real durante investigación
- HM valida los campos con su back-office operativo
- Si la aseguradora tiene API: usar spec oficial de la API

Riesgo: si un campo obligatorio falta o tiene formato incorrecto,
la aseguradora rechaza la solicitud. Por eso el mock_connector
simula rechazos para entrenar el flujo de corrección.
"""

from datetime import date

DATA_STATUS = "SIMULADO"


def generar(
    aseguradora: str,
    datos_paciente: dict,
    datos_medico: dict,
    procedimiento_cie10: str,
    procedimiento_codigo_aseguradora: str,
    documentacion_adjunta: list[str],
    urgente: bool = False
) -> dict:
    """
    Genera el payload de solicitud.
    En mock mode → formato simulado para demo.
    En modo real → formato exacto del portal de la aseguradora.
    """
    generadores = {
        "sanitas": _generar_sanitas,
        "adeslas": _generar_adeslas,
        "dkv": _generar_dkv,
    }

    generador = generadores.get(aseguradora.lower())
    if not generador:
        raise ValueError(f"Aseguradora no soportada: {aseguradora}")

    return generador(
        datos_paciente, datos_medico,
        procedimiento_cie10, procedimiento_codigo_aseguradora,
        documentacion_adjunta, urgente
    )


def _generar_sanitas(
    datos_paciente, datos_medico,
    cie10, codigo_sanitas,
    documentacion, urgente
) -> dict:
    """
    ⚠️  FORMATO SIMULADO
    Campos basados en investigación pública del portal Sanitas.
    Confirmar campos exactos, nombres y formatos en Fase 0.
    El mock_connector acepta este formato para la demo.
    """
    return {
        "_data_status": DATA_STATUS,  # ← eliminado en producción
        "tipo": "solicitud_autorizacion",
        "aseguradora": "sanitas",
        "version_formato": "simulado-1.0",  # ← actualizar en Fase 0
        "datos": {
            "paciente": {
                "nombre": datos_paciente.get("nombre"),
                "apellidos": datos_paciente.get("apellidos"),
                "numero_poliza": datos_paciente.get("poliza"),
                "fecha_nacimiento": datos_paciente.get("fecha_nacimiento"),
                # ← confirmar campos adicionales requeridos por Sanitas
            },
            "medico_solicitante": {
                "nombre": datos_medico.get("nombre"),
                "numero_colegiado": datos_medico.get("numero_colegiado"),
                "especialidad": datos_medico.get("especialidad"),
                # ← confirmar campos adicionales requeridos
            },
            "procedimiento": {
                "codigo_cie10": cie10,
                "codigo_sanitas": codigo_sanitas,  # ← SIMULADO hasta Fase 0
                "fecha_solicitud": date.today().isoformat(),
                "urgente": urgente,
                # ← confirmar campos de diagnóstico y justificación
            },
            "documentacion_adjunta": documentacion,
        }
    }


def _generar_adeslas(
    datos_paciente, datos_medico,
    cie10, codigo_adeslas,
    documentacion, urgente
) -> dict:
    """
    ⚠️  FORMATO SIMULADO — completar en Fase 0
    Adeslas puede tener un formato de formulario diferente a Sanitas.
    Investigar durante Fase 0 si tiene API o solo portal web.
    """
    return {
        "_data_status": DATA_STATUS,
        "tipo": "solicitud_autorizacion",
        "aseguradora": "adeslas",
        "version_formato": "simulado-1.0",
        # ← rellenar estructura real en Fase 0
    }


def _generar_dkv(
    datos_paciente, datos_medico,
    cie10, codigo_dkv,
    documentacion, urgente
) -> dict:
    """
    ⚠️  FORMATO SIMULADO — completar en Fase 0
    DKV tiene acuerdo activo con HM (confirmado 2026).
    Priorizar API si existe, RPA si no.
    """
    return {
        "_data_status": DATA_STATUS,
        "tipo": "solicitud_autorizacion",
        "aseguradora": "dkv",
        "version_formato": "simulado-1.0",
        # ← rellenar estructura real en Fase 0
    }
```

### 7.7 Checklist de transición MVP → Producción

Cuando llegue Fase 0 con HM, este es el proceso para cada módulo:

```
Para cada aseguradora (Sanitas, Adeslas, DKV):

□ HM proporciona catálogo operativo de procedimientos
□ Isabella mapea cada procedimiento al CIE-10 correspondiente
□ Ingeniero IA/CTO rellena CODIGOS dict con datos reales
□ Cambiar DATA_STATUS de "SIMULADO" a "VALIDADO_YYYY-MM-DD"
□ Cambiar VERSION de "1.0.0-simulado" a "1.0.0"
□ Ejecutar pytest tests/test_calculadores.py completo
□ Deploy en staging con HITL al 100%
□ Back-office HM valida 50 casos reales
□ Solo entonces: activar en producción con HITL progresivo
□ Documentar en CHANGELOG.md con la fuente de los datos
```



---

## 8. SPEC DEL AGENTE 1 — AUTORIZACIONES

### 8.1 System prompt del parser

```python
PARSER_SYSTEM_PROMPT = """
Eres un parser especializado en órdenes médicas hospitalarias españolas.
Tu única función es extraer información estructurada de texto clínico.

Extrae exactamente lo que está escrito. Si un dato no aparece, devuelve null.
No interpretes, no asumas, no rellenes con lógica clínica.

CAMPOS A EXTRAER:
- paciente_nombre: nombre completo
- paciente_id: identificador si aparece (null si no)
- paciente_aseguradora: nombre de la aseguradora (null si no)
- paciente_poliza: número de póliza (null si no)
- procedimiento_descripcion: descripción textual del procedimiento
- procedimiento_cie10: código CIE-10 solo si aparece explícito (null si no)
- medico_nombre: médico solicitante
- medico_especialidad: especialidad si aparece (null si no)
- fecha_solicitud: fecha en formato ISO YYYY-MM-DD (null si no)
- urgente: true solo si hay indicación explícita, false si no
- diagnostico_principal: diagnóstico si aparece (null si no)
- notas_clinicas: cualquier nota adicional relevante (null si no)

Devuelve únicamente JSON válido. Sin texto adicional, sin explicaciones.
"""
```

### 8.2 System prompt del guardrail

```python
GUARDRAIL_SYSTEM_PROMPT = """
Eres un validador de outputs de un sistema de autorizaciones médicas.

Recibes un JSON extraído de una orden médica. Tu trabajo es comprobar
que está completo y coherente antes de que el sistema actúe sobre él.

Comprueba:
1. ¿Están presentes los campos obligatorios? (paciente_nombre, paciente_aseguradora, procedimiento_descripcion)
2. ¿Los formatos son correctos? (fechas ISO, booleanos)
3. ¿Hay inconsistencias evidentes?

Devuelve JSON con esta estructura:
{
  "valido": true/false,
  "campos_faltantes": [],
  "inconsistencias": [],
  "confidence": 0.0-1.0,
  "requiere_hitl": true/false,
  "razon_hitl": "descripción breve si requiere_hitl es true"
}

No tomes decisiones clínicas. No asignes códigos.
Solo valida que el JSON está bien formado y completo.
"""
```

### 8.3 Nodos del grafo LangGraph

```python
# app/agent/nodes.py

async def parse_orden_medica(state: AuthorizationState) -> dict:
    """
    Usa Mistral Large para extraer datos estructurados
    de la orden médica en texto libre.
    """
    client = MistralClient()
    response = await client.chat(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": state["orden_raw"]}
        ]
    )
    datos = json.loads(response.content)

    # Guardrail con Mistral Nemo
    validation = await client.chat(
        model="open-mistral-nemo",
        messages=[
            {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(datos)}
        ]
    )
    validation_result = json.loads(validation.content)

    return {
        "datos_estructurados": datos,
        "confidence_score": validation_result["confidence"],
        "hitl_requerido": validation_result["requiere_hitl"],
        "estado": "parseado"
    }


async def verificar_cobertura(state: AuthorizationState) -> dict:
    """
    Python puro. No usa LLM.
    Llama al calculador verificador_cobertura.
    """
    datos = state["datos_estructurados"]

    cubierto, requiere_auth, documentacion, confidence = (
        verificador_cobertura.verificar(
            aseguradora=datos["paciente_aseguradora"],
            procedimiento_cie10=datos.get("procedimiento_cie10", ""),
            tipo_poliza=datos.get("paciente_tipo_poliza", "basica")
        )
    )

    # Confidence combinada: min del parser y del calculador
    confidence_combinada = min(
        state["confidence_score"],
        confidence
    )

    hitl = (
        state["hitl_requerido"] or
        confidence_combinada < 0.8 or
        not cubierto
    )

    return {
        "cobertura_verificada": cubierto,
        "requiere_autorizacion": requiere_auth,
        "documentacion_requerida": documentacion,
        "confidence_score": confidence_combinada,
        "hitl_requerido": hitl,
        "estado": "verificado"
    }


async def generar_solicitud(state: AuthorizationState) -> dict:
    """
    Python puro. No usa LLM.
    Genera el formulario de solicitud.
    """
    if not state["requiere_autorizacion"]:
        return {
            "estado": "no_requiere_autorizacion",
            "notas": "Procedimiento no requiere autorización previa"
        }

    datos = state["datos_estructurados"]
    aseguradora = datos["paciente_aseguradora"].lower()

    # Obtener código correcto — PYTHON PURO
    if aseguradora == "sanitas":
        codigo = codigos_sanitas.get_codigo(
            datos.get("procedimiento_cie10", ""),
            datos.get("paciente_tipo_poliza", "basica")
        )
    # ... otras aseguradoras

    solicitud = generador_solicitud.generar(
        aseguradora=aseguradora,
        datos_paciente=datos,
        datos_medico=datos,
        procedimiento_cie10=datos.get("procedimiento_cie10", ""),
        procedimiento_codigo_aseguradora=codigo.codigo if codigo else "",
        documentacion_adjunta=state["documentacion_requerida"],
        urgente=datos.get("urgente", False)
    )

    return {
        "solicitud_generada": solicitud,
        "procedimiento_codigo": codigo.codigo if codigo else "",
        "estado": "solicitud_generada"
    }


async def enviar_solicitud(state: AuthorizationState) -> dict:
    """
    Envía la solicitud al portal de la aseguradora.
    En mock_mode → usa mock_connector.
    En modo real → usa connector específico.
    """
    if state["modo"] == "mock":
        connector = MockConnector()
    elif state["datos_estructurados"]["paciente_aseguradora"].lower() == "sanitas":
        connector = SanitasConnector()
    # ... otros conectores

    resultado = await connector.enviar(state["solicitud_generada"])

    return {
        "solicitud_enviada_at": datetime.now().isoformat(),
        "solicitud_referencia": resultado["referencia"],
        "estado": "enviado"
    }
```

---

## 9. SPEC DE INTEGRACIONES

### 9.1 Mock connector (para demo)

```python
# app/conectores/mock_connector.py

class MockConnector:
    """
    Simula el comportamiento de un portal de aseguradora.
    Usa para demos sin credenciales reales.

    Comportamiento:
    - 80% de las solicitudes se aprueban automáticamente
    - 15% piden información adicional
    - 5% se deniegan (para mostrar el flujo completo)
    """

    async def enviar(self, solicitud: dict) -> dict:
        import random
        roll = random.random()

        await asyncio.sleep(2)  # Simula latencia de red

        if roll < 0.80:
            return {
                "estado": "aprobado",
                "referencia": f"MOCK-{uuid4().hex[:8].upper()}",
                "numero_autorizacion": f"AUTH-{uuid4().hex[:8].upper()}",
                "mensaje": "Autorización aprobada automáticamente"
            }
        elif roll < 0.95:
            return {
                "estado": "informacion_adicional",
                "referencia": f"MOCK-{uuid4().hex[:8].upper()}",
                "informacion_requerida": ["historia_clinica_previa"],
                "mensaje": "Se requiere documentación adicional"
            }
        else:
            return {
                "estado": "denegado",
                "referencia": f"MOCK-{uuid4().hex[:8].upper()}",
                "motivo": "Procedimiento no cubierto por la póliza actual",
                "mensaje": "Solicitud denegada"
            }
```

### 9.2 HL7 Mock (simula Doctoris HIS)

```python
# app/integrations/hl7_mock.py

ORDENES_EJEMPLO = [
    {
        "id": "ORD-001",
        "descripcion": "Caso Sanitas Resonancia Magnética Rodilla",
        "hl7": """MSH|^~\&|DOCTORIS|HM_MONTEPRÍNCIPE|SOBERANIA|HEALTH|20260506||ORM^O01|001|P|2.5
PID|1||12345^^^HM||GARCIA^MARIA^ANA||19810315|F|||CALLE MAYOR 1^MADRID^28001||||||
IN1|1|SANITAS|SANITAS|||||||MAS_SALUD_PLUS|987654|||||||
ORC|NW|ORD-001|||||^^^20260506||20260506|^DR_TRAUMATOLOGIA^JUAN
OBR|1|ORD-001||RM_RODILLA_DCHA^Resonancia Magnética Rodilla Derecha|||20260506||||||||^Posible rotura de menisco medial derecho"""
    },
    {
        "id": "ORD-002",
        "descripcion": "Caso Adeslas TAC Abdominal",
        "hl7": "..."
    }
]

def get_orden_ejemplo(caso_id: str) -> str:
    for orden in ORDENES_EJEMPLO:
        if orden["id"] == caso_id:
            return orden["hl7"]
    return ORDENES_EJEMPLO[0]["hl7"]
```

---

## 10. SPEC DEL AUDIT LOG Y COMPLIANCE

### 10.1 Estructura del audit log

```python
# app/utils/audit_log.py

import hashlib
import json
from datetime import datetime
from uuid import uuid4

class AuditLogger:
    """
    Registro inmutable de cada acción del sistema.
    Cada entrada tiene hash SHA256 encadenado al anterior.
    Cumple AI Act: trazabilidad completa, inmutabilidad,
    identificación del modelo usado.
    """

    def __init__(self, db_session):
        self.db = db_session

    async def log(
        self,
        autorizacion_id: str,
        accion: str,
        actor: str,
        datos_entrada: dict,
        datos_salida: dict,
        confidence_score: float,
        modelo_usado: str = None,
        hitl_intervencion: bool = False
    ) -> str:
        """
        Registra una acción en el audit log.
        Retorna el hash SHA256 de la entrada.
        """
        # Obtener el hash de la entrada anterior
        ultima_entrada = await self.db.get_ultima_entrada(autorizacion_id)
        hash_previo = ultima_entrada.hash_sha256 if ultima_entrada else "GENESIS"

        # Construir la entrada
        entrada = {
            "id": str(uuid4()),
            "autorizacion_id": autorizacion_id,
            "timestamp": datetime.utcnow().isoformat(),
            "accion": accion,
            "actor": actor,
            "resultado": datos_salida.get("estado", "desconocido"),
            "datos_entrada": datos_entrada,
            "datos_salida": datos_salida,
            "confidence_score": confidence_score,
            "modelo_usado": modelo_usado,
            "version_calculador": "1.0.0",
            "hitl_intervencion": hitl_intervencion,
            "hash_previo": hash_previo,
        }

        # Calcular hash SHA256
        entrada_str = json.dumps(entrada, sort_keys=True, ensure_ascii=False)
        hash_actual = hashlib.sha256(entrada_str.encode()).hexdigest()
        entrada["hash_sha256"] = hash_actual

        # Persistir en DB
        await self.db.insert_audit(entrada)

        return hash_actual
```

---

## 11. SPEC DEL DASHBOARD HITL

### 11.1 Funcionalidades del dashboard Streamlit

```python
# dashboard/hitl_dashboard.py

"""
Dashboard de supervisión humana (HITL).
Construido en Streamlit para velocidad de desarrollo.
Asaf construirá la versión React después del MVP.

Funcionalidades:
1. Cola de autorizaciones pendientes de revisión
2. Detalle de cada autorización (datos + decisión del agente)
3. Botones: Aprobar / Rechazar / Pedir más info
4. Vista del audit log en tiempo real
5. Métricas: % automatizado, tiempo medio, rechazos
"""

import streamlit as st
import httpx

API_BASE = "http://localhost:8000"

def main():
    st.set_page_config(
        page_title="SoberanIA Health — HITL Supervisor",
        layout="wide"
    )

    st.title("SoberanIA Health — Supervisor de Autorizaciones")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pendientes revisión", obtener_pendientes())
    with col2:
        st.metric("Automatizadas hoy", obtener_automatizadas())
    with col3:
        st.metric("Tasa automatización", "87%")

    st.divider()

    # Cola de revisión
    pendientes = obtener_lista_pendientes()

    for auth in pendientes:
        with st.expander(
            f"🔴 {auth['paciente_nombre']} — {auth['procedimiento_descripcion']}"
        ):
            col_datos, col_decision = st.columns([2, 1])

            with col_datos:
                st.write(f"**Aseguradora:** {auth['aseguradora']}")
                st.write(f"**Póliza:** {auth['poliza_tipo']}")
                st.write(f"**Código generado:** {auth['procedimiento_codigo']}")
                st.write(f"**Confidence:** {auth['confidence_score']:.0%}")
                st.write(f"**Razón HITL:** {auth['hitl_razon']}")

            with col_decision:
                if st.button("✅ Aprobar", key=f"aprobar_{auth['id']}"):
                    aprobar(auth["id"])
                    st.rerun()
                if st.button("❌ Rechazar", key=f"rechazar_{auth['id']}"):
                    rechazar(auth["id"])
                    st.rerun()
                if st.button("📋 Más info", key=f"info_{auth['id']}"):
                    pedir_info(auth["id"])
                    st.rerun()
```

---

## 12. SPEC DEL API REST

### 12.1 Endpoints principales

```
POST   /api/v1/autorizaciones/procesar
       Body: { orden_hl7: string, modo: "real"|"mock" }
       Returns: { autorizacion_id, estado, confidence_score }

GET    /api/v1/autorizaciones/{id}
       Returns: autorización completa con audit log

GET    /api/v1/autorizaciones/pendientes
       Returns: lista de autorizaciones pendientes de HITL

POST   /api/v1/autorizaciones/{id}/hitl
       Body: { decision: "aprobar"|"rechazar"|"mas_info", notas: string }
       Returns: autorización actualizada

GET    /api/v1/audit/{autorizacion_id}
       Returns: audit log completo con hashes

GET    /api/v1/health
       Returns: { status: "ok", version, calculadores_version }

POST   /api/v1/demo/run
       Body: { caso_id: string }
       Returns: flujo completo simulado paso a paso
```

---

## 13. TEST SUITE E2E

### 13.1 Los 30 casos de test obligatorios

```
SANITAS (10 casos)
├── caso_001: RM rodilla derecha, póliza Más Salud Plus → Aprobado
├── caso_002: TAC abdominal con contraste, póliza Básica → Aprobado
├── caso_003: Cirugía ambulatoria rodilla, póliza Óptima → Aprobado
├── caso_004: Procedimiento NO cubierto por póliza → Denegado
├── caso_005: Orden con campo aseguradora ambiguo → HITL
├── caso_006: Orden sin código CIE-10 explícito → HITL
├── caso_007: Procedimiento urgente → Plazo reducido
├── caso_008: Información adicional requerida → Ciclo de ida/vuelta
├── caso_009: Autorización caducada → Re-solicitud
└── caso_010: Orden malformada → Error controlado

ADESLAS (10 casos)
├── caso_011: RM cerebral, póliza Completa → Aprobado
├── caso_012: TAC tórax, póliza Básica → Aprobado
├── caso_013: ...
└── ...

DKV (10 casos)
├── caso_021: ...
└── ...
```

### 13.2 Estructura de cada caso de test

```json
{
  "id": "caso_001",
  "descripcion": "RM rodilla derecha Sanitas Más Salud Plus",
  "input": {
    "orden_hl7": "MSH|...",
    "modo": "mock"
  },
  "expected": {
    "aseguradora": "sanitas",
    "poliza_tipo": "mas_salud_plus",
    "procedimiento_codigo": "SIM-001",  // ← código simulado hasta Fase 0
    "requiere_autorizacion": true,
    "confidence_min": 0.85,
    "hitl_requerido": false,
    "estado_final": "enviado"
  }
}
```

---

## 14. CONFIGURACIÓN DOCKER Y DEPLOY

### 14.1 docker-compose.yml (desarrollo)

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://soberania:soberania@db:5432/health
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - MODO_DEFAULT=mock
    volumes:
      - ./app:/app
      - ./data:/data
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --reload --host 0.0.0.0

  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - API_BASE=http://api:8000
    command: streamlit run dashboard/hitl_dashboard.py

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: soberania
      POSTGRES_PASSWORD: soberania
      POSTGRES_DB: health
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U soberania"]
      interval: 5s
      timeout: 5s
      retries: 5

  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://soberania:soberania@db:5432/langfuse

volumes:
  postgres_data:
```

### 14.2 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000 8501
```

---

## 15. VARIABLES DE ENTORNO

```bash
# .env.example

# LLM — API Mistral (NO self-hosted en MVP)
MISTRAL_API_KEY=your_key_here

# Base de datos
DATABASE_URL=postgresql://soberania:soberania@localhost:5432/health

# Observabilidad
LANGFUSE_PUBLIC_KEY=your_key_here
LANGFUSE_SECRET_KEY=your_key_here
LANGFUSE_HOST=http://localhost:3000

# Agente
CONFIDENCE_THRESHOLD_HITL=0.80
MODO_DEFAULT=mock   # "mock" para demo, "real" para producción

# Notificaciones
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_EMAIL_FROM=health@soberania.eu

# Compliance
AUDIT_LOG_ENABLED=true
HITL_OBLIGATORIO_MODO_REAL=true

# Conectores aseguradoras (solo para modo real)
SANITAS_PORTAL_URL=
SANITAS_USER=
SANITAS_PASSWORD=
ADESLAS_PORTAL_URL=
ADESLAS_USER=
ADESLAS_PASSWORD=
DKV_PORTAL_URL=
DKV_USER=
DKV_PASSWORD=
```

---

## 16. PLAN DE CONSTRUCCIÓN POR FASES

> **Regla: sin fechas. Las fases son secuenciales por dependencia técnica, no por calendario.**

### Fase 0 — Setup del repositorio

**Quién:** Ingeniero IA/CTO

**Criterio de done:** `docker-compose up` levanta sin errores y `/api/v1/health` responde 200

```
□ Crear repositorio soberania-health en GitHub SoberanIA-ai
□ Setup inicial: estructura de directorios según sección 4
□ Configurar .gitignore, .env.example, README.md
□ docker-compose.yml funcionando con PostgreSQL
□ FastAPI básico respondiendo en /api/v1/health
□ Alembic configurado con primera migración (tablas sección 6)
□ Langfuse corriendo y conectado
□ pytest configurado y pasando test vacío
```

### Fase 1 — Calculadores Python

**Quién:** Ingeniero IA/CTO construye estructura + Isabella aporta datos del Google Sheet

**Criterio de done:** `pytest tests/test_calculadores.py` pasa al 100%

```
□ Implementar codigos_sanitas.py con datos de Isabella
□ Implementar codigos_adeslas.py con datos de Isabella
□ Implementar codigos_dkv.py con datos de Isabella
□ Implementar reglas_cobertura.py
□ Implementar plazos_respuesta.py
□ Implementar verificador_cobertura.py
□ Implementar generador_solicitud.py (formato Sanitas primero)
□ Test unitario por cada función de cada calculador
□ Confirmar: ningún calculador hace I/O externo
```

### Fase 2 — Agente LangGraph

**Quién:** Ingeniero IA/CTO

**Criterio de done:** un caso simulado fluye de principio a fin en mock mode

```
□ Implementar AuthorizationState TypedDict
□ Implementar nodo parse_orden_medica (Mistral Large)
□ Implementar nodo guardrail (Mistral Nemo)
□ Implementar nodo verificar_cobertura (Python puro)
□ Implementar nodo generar_solicitud (Python puro)
□ Implementar MockConnector
□ Implementar nodo enviar_solicitud con MockConnector
□ Implementar nodo registrar_audit
□ Conectar todos los nodos en graph.py
□ Probar con caso_001 manualmente
```

### Fase 3 — Audit log y compliance

**Quién:** Ingeniero IA/CTO

**Criterio de done:** cada acción del agente aparece en audit log con hash SHA256 correcto

```
□ Implementar AuditLogger con SHA256 encadenado
□ Integrar AuditLogger en cada nodo del grafo
□ Verificar inmutabilidad (hash encadenado correcto)
□ Implementar endpoint GET /api/v1/audit/{id}
□ Test: modificar entrada en DB → hash inválido detectado
```

### Fase 4 — Dashboard HITL

**Quién:** Ingeniero IA/CTO (Streamlit) / Isabella (UX de los casos)

**Criterio de done:** supervisor puede ver cola y aprobar/rechazar desde el navegador

```
□ Implementar hitl_dashboard.py en Streamlit
□ Cola de autorizaciones pendientes
□ Detalle de cada autorización
□ Botones aprobar/rechazar/más info
□ Endpoint POST /api/v1/autorizaciones/{id}/hitl
□ Integrar HITL en el grafo LangGraph (nodo hitl_check)
□ Test: autorización con confidence < 0.8 va a HITL
```

### Fase 5 — Test suite E2E

**Quién:** Ingeniero IA/CTO + Isabella (define los 30 casos)

**Criterio de done:** 30/30 casos pasan en modo mock

```
□ Isabella define los 30 casos en data/casos_test/
□ Implementar test_e2e.py
□ Todos los casos pasan
□ Informe de cobertura > 80%
```

### Fase 6 — Demo ready

**Quién:** David revisa + Ingeniero IA/CTO pulimento final

**Criterio de done:** demo de 10 minutos sin errores ni interrupciones

```
□ Script de demo automatizado (scripts/run_demo.py)
□ Mock mode activado por defecto
□ 3 casos de demo preparados (Sanitas, Adeslas, DKV)
□ Dashboard HITL limpio y sin datos de test
□ README con instrucciones de instalación en 3 comandos
□ David hace la demo en su máquina sin ayuda técnica
```

---

## 17. CHECKLIST PRE-DEMO

```
TÉCNICO
□ docker-compose up levanta sin errores
□ /api/v1/health responde 200
□ Mock mode activado
□ 3 casos de demo cargados en DB
□ Dashboard HITL abre en http://localhost:8501
□ Audit log funcionando con hashes correctos
□ Langfuse mostrando trazas

DEMO FLOW (10 minutos)
□ Caso 1: Sanitas RM rodilla → aprobación automática
□ Caso 2: Adeslas TAC → HITL (supervisor aprueba desde dashboard)
□ Caso 3: DKV procedimiento ambiguo → información adicional
□ Mostrar audit log con hashes
□ Mostrar confidence scores en tiempo real

NARRATIVA
□ "El mismo sistema que funciona en Asintex con Hacienda"
□ "Python puro para los códigos — el LLM nunca inventa"
□ "Audit log inmutable — AI Act compliant desde día 1"
□ "Mock mode: demo sin credenciales reales de aseguradoras"
```

---

## 18. TAREAS DE ISABELLA — DOMAIN EXPERT

Isabella lidera el vertical salud. El MVP técnico está construido y funcionando. Lo que bloquea el piloto con HM ahora son los datos reales de aseguradoras y el acceso a HM — ambos dependen de Isabella.

### Estado actual (Mayo 2026)

| Tarea | Estado |
|-------|--------|
| MVP técnico construido | ✅ Completado por el equipo de ingeniería |
| Google Sheet catálogos Sanitas/Adeslas/DKV | ⏳ PENDIENTE Isabella |
| 30 casos test E2E con datos reales | ⏳ PENDIENTE Isabella |
| Investigación APIs aseguradoras | ⏳ PENDIENTE Isabella |
| Respuesta CEO HM | ⏳ Pendiente de seguimiento |
| Contacto Xavier Tarragó (Dir. Transformación Digital) | ⏳ Siguiente paso |

### Prioridad MÁXIMA — Desbloquea los datos reales

**Google Sheet: Catálogo de códigos inicial**

Crear un Google Sheet compartido con el Ingeniero IA/CTO con estas pestañas:

```
Pestaña 1: SANITAS_CODIGOS
Columnas: procedimiento_descripcion | cie10 | codigo_sanitas |
          tipo_poliza | requiere_auth | docs_requeridos |
          copago_euros | notas | fuente | confianza

Pestaña 2: ADESLAS_CODIGOS
[mismas columnas]

Pestaña 3: DKV_CODIGOS
[mismas columnas]

Pestaña 4: PROCEDIMIENTOS_TOP20
Columnas: ranking | descripcion | cie10 | volumen_estimado |
          presente_en_sanitas | presente_en_adeslas | presente_en_dkv
```

**Fuentes para investigar:**

```
- Portales públicos de Sanitas, Adeslas y DKV
- Documentación pública de cuadros médicos
- Guías de autorización publicadas por las aseguradoras
- Catálogos de procedimientos SENAME / Ministerio de Sanidad
- CIE-10-ES: Clasificación Internacional de Enfermedades
```

**Confianza a marcar en cada fila:**

```
ALTA: dato verificado en fuente oficial de la aseguradora
MEDIA: dato inferido de documentación pública
BAJA: estimación basada en práctica del sector
PENDIENTE: dato que necesitamos confirmar con HM en Fase 0
```

### Prioridad ALTA — Desbloquea la Fase 5

**Definir los 30 casos de test E2E**

Para cada caso, rellenar el JSON de la sección 13.2:

```
10 casos Sanitas:
- 3 aprobaciones automáticas normales
- 2 casos con HITL (confidence baja o campo faltante)
- 2 casos de información adicional requerida
- 1 caso urgente
- 1 caso de procedimiento no cubierto
- 1 caso de orden malformada

10 casos Adeslas (mismo patrón)
10 casos DKV (mismo patrón)
```

### Prioridad MEDIA — Desbloquea la reunión con HM

**Investigación de APIs de aseguradoras**

```
Para Sanitas, Adeslas y DKV investigar:
1. ¿Tienen API documentada para solicitar autorizaciones?
2. ¿Tienen portal web con formulario? (→ RPA con Playwright)
3. ¿Tienen integración HL7 directa con hospitales?
4. ¿Existe documentación técnica pública?

Entregable: documento de 1 página con estado por aseguradora
```

**Investigación de contactos en HM**

```
Objetivo: identificar al champion interno en back-office
- ¿Quién gestiona las autorizaciones en HM Montepríncipe hoy?
- ¿Hay un responsable de operaciones back-office identificado?
- ¿Podemos llegar a Xavier Tarragó antes de tener la demo lista?
```

---

## 19. REGLAS DEL PROYECTO

```
1. SIN FECHAS EN DOCUMENTOS EXTERNOS
   Las fases son secuenciales por dependencia, no por calendario.
   En documentos para HM, nunca aparecen fechas de entrega.

2. SIN AFIRMACIONES SIN VERIFICAR
   Cada dato en el Google Sheet de Isabella tiene su columna
   de confianza. Si es BAJA o PENDIENTE, no lo ponemos como
   hecho en ningún documento.

3. EL LLM NUNCA DECIDE CÓDIGOS NI DATOS NUMÉRICOS
   Si en alguna PR aparece un LLM eligiendo un código de
   procedimiento o una tarifa → se rechaza.

4. HITL OBLIGATORIO EN MODO REAL
   Hasta que confidence_score acumulado sea > 0.95 en 100
   autorizaciones consecutivas, toda autorización pasa por
   revisión humana en modo real.

5. MOCK MODE SIEMPRE DISPONIBLE
   El sistema siempre debe poder correr en mock mode.
   Ninguna demo depende de credenciales externas.

6. TEST SUITE ANTES DE CUALQUIER DEPLOY
   Ningún calculador se actualiza sin pasar el test suite
   completo. Nunca.

7. AUDIT LOG ES SAGRADO
   El audit log nunca se borra. Nunca se modifica.
   Cualquier intento de hacerlo es un bug crítico.

8. MVP PRIMERO, PERFECCIÓN DESPUÉS
   Si algo no está en el alcance del MVP (sección 2.2),
   no se construye hasta que el piloto esté en marcha.
   Resistir la tentación de añadir features.
```

---

## 20. GLOSARIO Y ASSUMPTIONS

### 20.1 Glosario

| Término | Definición en este proyecto |
|---------|----------------------------|
| **Autorización previa** | Permiso que la aseguradora debe conceder antes de que el hospital realice un procedimiento cubierto por la póliza |
| **Calculador Python** | Módulo Python puro (sin LLM, sin I/O externo) que implementa las reglas exactas de una aseguradora. Fuente de verdad del sistema |
| **CIE-10** | Clasificación Internacional de Enfermedades, décima revisión. Sistema estándar de codificación de diagnósticos y procedimientos |
| **Confidence score** | Puntuación de 0 a 1 que el sistema asigna a cada decisión. Valores < 0.80 disparan revisión humana obligatoria |
| **HITL** | Human-in-the-Loop. Supervisión humana de las decisiones del agente. Al 100% en las primeras fases del piloto |
| **HL7** | Health Level 7. Estándar de intercambio de información sanitaria. El HIS Doctoris de HM usa HL7 |
| **HIS** | Hospital Information System. Sistema de gestión hospitalaria. En HM: Doctoris, de TRC |
| **Mock mode** | Modo de demostración sin credenciales reales de aseguradoras. Respuestas simuladas por `mock_connector.py` |
| **RCM** | Revenue Cycle Management. Gestión del ciclo completo de ingresos hospitalarios |
| **RPA** | Robotic Process Automation. Automatización de interfaces web mediante navegador controlado (Playwright) cuando no hay API disponible |
| **SHA256** | Algoritmo de hash criptográfico usado para garantizar la inmutabilidad del audit log |
| **Soberanía EU** | Todos los datos procesados en servidores dentro de la Unión Europea (Hetzner Frankfurt). Obligatorio para datos clínicos bajo GDPR Art. 9 |

### 20.2 Assumptions — lo que asumimos sin haber verificado con HM

Estos datos están basados en investigación pública. **Deben validarse con HM en Fase 0** antes de usar en producción.

| Assumption | Fuente | Confianza | Validar en Fase 0 |
|-----------|--------|-----------|-------------------|
| HM usa Doctoris HIS con HL7 | Investigación pública | Media | Confirmar versión y acceso |
| Sanitas, Adeslas y DKV son las 3 aseguradoras de mayor volumen en HM | Benchmark sector | Media | Confirmar con back-office HM |
| Los portales de aseguradoras requieren RPA (sin API pública) | Investigación pública | Baja | Investigación Isabella |
| 50-100 autorizaciones/día por hospital medio | Benchmark sector (Isabella) | Media | Confirmar con HM Montepríncipe |
| Los catálogos de códigos en `codigos_X.py` son correctos | Portales públicos | Baja | Validar con HM y aseguradoras |
| El personal administrativo de HM estará disponible para Fase 0 | Asumido | Baja | Confirmar con Xavier Tarragó |

---

*SoberanIA — Arquitectura de Sistemas de IA SL · CIF B26912824 · Madrid · Mayo 2026*
*Documento confidencial v1.1 — No distribuir sin autorización de David Fernández.*
