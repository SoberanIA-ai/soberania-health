# Changelog — SoberanIA Health

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [Unreleased]

## [0.2.0] — Dashboard v2 (Fase A — Isabella Cristancho)

### Added
- **Autenticación JWT**: login por usuario con roles (recepcionista, supervisor, auditor, admin). Sesión de 8 horas.
- **Tabla `usuarios`** con seed de cuentas de demo para HM Hospitales.
- **Notificaciones SSE** (`GET /api/v1/notificaciones/stream`): el dashboard recibe eventos en tiempo real cuando cambia el estado de una autorización.
- **Dashboard HTML/CSS/JS** (`dashboard/hitl_dashboard.html`): reemplaza el Streamlit. Incluye login, sidebar con navegación por rol, 5 KPIs, gráfico donut y barras con Chart.js, tabla con filtros y búsqueda, modal de nueva autorización, panel HITL con aprobar/rechazar/más info, panel de detalle con timeline del audit log SHA256, y panel de Auditoría AI Act.
- **Panel Auditoría AI Act**: métricas de compliance, tabla de decisiones con tipo automático/HITL, trazabilidad completa por caso, exportación del aiact-report como JSON.
- **Hook Doctoris** (`POST /api/v1/integraciones/doctoris/orden`): stub vacío para la futura integración con el HIS de HM Hospitales.
- **Documentación completa**: `docs/ARQUITECTURA.md`, `docs/AI_ACT_COMPLIANCE.md`, `docs/CONECTORES.md`, `docs/DASHBOARD.md`.
- **`tests/test_auth.py`**: tests de autenticación JWT.

### Changed
- `requirements.txt`: añadidas dependencias `python-jose[cryptography]`, `passlib[bcrypt]`, `bcrypt==3.2.2`.
- `app/config.py`: añadidos campos `jwt_secret_key`, `jwt_algorithm`, `jwt_expire_minutes`.
- `app/main.py`: registrados routers `auth`, `notificaciones`, `doctoris_webhook`.
- `app/services/autorizacion_service.py`: añadidas llamadas a `emitir_evento` SSE en `procesar()` y `aplicar_decision_hitl()`.

### Technical
- Migración Alembic `0003_add_usuarios`: tabla `usuarios` con seed de demo.
- bcrypt pinado a `3.2.2` por incompatibilidad de `passlib==1.7.4` con `bcrypt>=4.0`.

---

## [0.1.0] — MVP inicial (Fases 0–6, David Fernández)

### Added
- Grafo LangGraph de 8 nodos: parse → verify_guardrail → [hitl_review] → generate_solicitud → send_to_aseguradora → monitor_respuesta → process_respuesta → notify.
- Calculadores Python deterministas para Sanitas, Adeslas y DKV.
- Conectores con patrón adaptador (MockConnector funcional).
- API REST FastAPI completa (12 endpoints).
- Audit log SHA256 encadenado (inmutable, cumple AI Act Art. 12).
- Endpoint `GET /api/v1/audit/{id}/aiact-report`.
- Dashboard Streamlit básico (puerto 8503).
- 107 tests automatizados, 94% de cobertura.
- Integración HL7 mock para simulación de órdenes Doctoris.
- 26 casos de demo con 3 aseguradoras (Sanitas, Adeslas, DKV).