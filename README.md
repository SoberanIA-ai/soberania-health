# SoberanIA Health

Vertical salud de SoberanIA. Agente 1 — Gestión automatizada de autorizaciones previas
entre hospitales privados y aseguradoras españolas.

Cliente objetivo: HM Hospitales.

## Principio fundamental

Los calculadores Python son la única fuente de verdad para códigos, tarifas y reglas.
El LLM nunca decide datos numéricos ni códigos. El LLM solo convierte lenguaje natural
en datos estructurados y genera comunicaciones.

## Stack

- FastAPI + LangGraph + Mistral API
- PostgreSQL + Alembic
- Streamlit (dashboard HITL)
- Playwright (RPA)
- Langfuse (observabilidad)

## Instalación

```bash
cp .env.example .env
docker-compose up --build
```

Servicios:

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Dashboard HITL: http://localhost:8501
- Langfuse: http://localhost:3000

## Tests

```bash
pytest
```

## Reglas no negociables

1. Sin fechas en documentos externos
2. El LLM nunca decide códigos ni cifras — solo calculadores Python
3. Mock mode siempre disponible
4. Datos aseguradoras: SIMULADOS hasta validación con HM
5. MVP primero, complejidad después

## Estado de los datos

Todos los catálogos de códigos (Sanitas, Adeslas, DKV) están marcados con
`DATA_STATUS = "SIMULADO"` hasta validación con HM en Fase 0. Cada calculador
expone su estado vía `get_version()`.

## Modos

- `MODO_DEFAULT=mock`: demo sin credenciales reales (default)
- `MODO_DEFAULT=real`: usa conectores de aseguradoras (requiere credenciales)
