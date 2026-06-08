# Changelog — SoberanIA Health

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [Unreleased]

## [0.3.0] — Next.js Frontend + RBAC + Flujo Más Info (Junio 2026)

### Added
- **Frontend Next.js 14** (`frontend/`): reemplaza el dashboard HTML estático. App Router, TypeScript, Tailwind CSS, Recharts. Cinco secciones: Resumen, Autorizaciones, Cola HITL, Urgentes, Auditoría AI Act.
- **RBAC completo frontend**: la barra lateral oculta las secciones según el rol; el layout protege rutas con redirect automático; login redirige a la página de inicio por rol.
- **RBAC backend**: todos los endpoints de autorizaciones y audit requieren JWT válido (`Depends(get_usuario_actual)`). El endpoint HITL restringe acceso a roles `supervisor` y `admin`.
- **Flujo "Más información" completo**: endpoint `POST /autorizaciones/{id}/reenviar`. La recepcionista ve qué documentación pidió el supervisor, sube archivos y reenvía al agente. El agente reprocesa sobre el mismo registro encadenando el audit log.
- **Panel `informacion_adicional_requerida`** en el DrawerDetalle: muestra el mensaje del supervisor, upload de archivos y botón "Reenviar al agente".
- **`razon_hitl`** en la tabla `autorizaciones`: el agente escribe el motivo exacto de HITL; el drawer lo muestra al supervisor.
- **Toast de error** cuando `aplicarHITL` falla por red.
- Campo `roleDefaultRoute()` compartido en `page.tsx` para eliminar la duplicación de la lógica de redirección por rol.

### Changed
- `app/agent/llm_client.py`: eliminado el bloqueo a HITL por `paciente_tipo_poliza` faltante (lo provee la aseguradora, no la recepcionista). El agente usa `"basica"` como default.
- `app/agent/llm_client.py`: guardrail detecta `REENVIO_SOLICITUD_INFO: true` y da paso libre (confidence 0.87) para reenvíos con documentación adjunta.
- `app/agent/nodes.py`: `generar_solicitud` preserva `razon_hitl` existente en lugar de sobreescribirla; `verificar_cobertura` escribe la razón exacta con guard `if not razon_hitl`.
- `frontend/src/components/layout/Sidebar.tsx`: guard de roles cambiado a deny-by-default (`!item.roles || ...`).
- `frontend/src/app/(app)/layout.tsx`: `refreshCounts` separado en su propio `useEffect([user])` para evitar 2 llamadas API extra en cada navegación.
- `docker-compose.yml`: servicio `dashboard` (Streamlit) reemplazado por `frontend` (Next.js, puerto 3002).

### Fixed
- `app/main.py`: añadido `CORSMiddleware` para permitir llamadas directas del browser al backend.
- Rutas RBAC usan `startsWith('/auditoria')` para que funcionen correctamente con sub-rutas futuras.
- `frontend/src/lib/types.ts`: añadidos `razon_hitl` y `motivo_denegacion` al tipo `Autorizacion`.

### Technical
- Migración Alembic `e08d6087a1f6_add_razon_hitl`: añade columna `razon_hitl TEXT` a tabla `autorizaciones`.
- `frontend/.dockerignore`: excluye `node_modules` y `.next` del contexto de build.

---

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