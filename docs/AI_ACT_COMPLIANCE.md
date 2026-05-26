# SoberanIA Health — Compliance AI Act

> Documento normativo para auditores, equipo legal y directores técnicos de HM Hospitales.  
> Reglamento UE 2024/1689 sobre Inteligencia Artificial (AI Act).

---

## 1. Clasificación del sistema

**Clasificación:** Sistema de IA de Alto Riesgo  
**Base legal:** Artículo 6 y Anexo III, punto 5.a del Reglamento UE 2024/1689  
**Motivo:** Sistema de IA utilizado en el ámbito de la salud que asiste en decisiones clínico-administrativas (autorización previa de procedimientos médicos).

> "Los sistemas de IA destinados a ser utilizados por o en nombre de operadores en el sector de la salud […] se clasificarán como de alto riesgo" (Anexo III, punto 5).

---

## 2. Artículos aplicables y cumplimiento

### Artículo 9 — Sistema de gestión de riesgos

**Riesgos identificados:**

| Riesgo | Mitigación implementada |
|--------|------------------------|
| Autorización incorrecta de un procedimiento no cubierto | Calculador Python determinista (no LLM) para verificación de cobertura |
| LLM extrae datos incorrectos de la orden médica | Campo `confidence_score`. Si <0.80 → HITL obligatorio |
| Catálogos desactualizados | `DATA_STATUS=SIMULADO` hasta validación formal con HM |
| Decisión automatizada sin supervisión | `HITL_OBLIGATORIO_MODO_REAL=true`: 100% de casos revisados en producción hasta acumular 0.95 de confianza |
| Manipulación del audit log | SHA256 encadenado: cualquier modificación rompe la cadena |

**Variables de control:**
```
CONFIDENCE_THRESHOLD_HITL=0.80   # Umbral bajo el cual el sistema SIEMPRE escala a humano
HITL_OBLIGATORIO_MODO_REAL=true  # En producción: HITL al 100% hasta confidence acumulado >0.95
```

---

### Artículo 10 — Gobernanza de datos y datos de entrenamiento

- El modelo LLM (Mistral) se usa exclusivamente via API. No se fine-tunea con datos de HM.
- Los catálogos de procedimientos son datos de referencia administrativa, no datos de entrenamiento.
- `DATA_STATUS = "SIMULADO"` en todos los calculadores: los datos actuales son ficticios.
- Nunca hay datos reales de pacientes en el repositorio de código. Solo en servidores HM.
- El paso a `DATA_STATUS = "VALIDADO"` requiere validación formal del catálogo por parte de HM.

---

### Artículo 11 — Documentación técnica

La documentación técnica del sistema está distribuida en los siguientes archivos del repositorio:

| Archivo | Contenido |
|---------|-----------|
| `docs/SOBERANIA_HEALTH_HANDOFF.md` | Especificación completa del sistema (MVP) |
| `docs/ARQUITECTURA.md` | Arquitectura, flujo, stack técnico, principios |
| `docs/AI_ACT_COMPLIANCE.md` | Este documento (compliance normativo) |
| `docs/CONECTORES.md` | Especificación de integración con aseguradoras |
| `CHANGELOG.md` | Historial de versiones con justificación de cambios |

---

### Artículo 12 — Mantenimiento de registros

**Implementación técnica:**
- Tabla `audit_log` en PostgreSQL: cada acción del sistema (parse, verify, generate, send, process, hitl) genera una entrada.
- **SHA256 encadenado**: el campo `hash_sha256` de cada entrada incluye el hash del contenido anterior. El primer registro usa `hash_previo="GENESIS"`.
- **Verificación en tiempo real**: `GET /api/v1/audit/{id}` devuelve `integro: true/false`.
- **Exportable**: `GET /api/v1/audit/{id}/aiact-report` produce un JSON estructurado con toda la trazabilidad.
- El audit log **nunca se borra** y **nunca se modifica** (regla #6 del proyecto).

**Campos registrados por entrada:**
- `accion`: nombre del nodo del grafo que generó la entrada
- `actor`: tipo de actor (agente_parser_llm, calculador_python, hitl_supervisor)
- `tipo`: llm | python | human
- `razon_decision`: explicación en lenguaje natural de la decisión tomada
- `modelo_usado`: identificador del modelo o calculador usado
- `version_calculador`: versión del calculador (permite auditar cambios en el tiempo)
- `hitl_intervencion`: booleano — ¿fue una decisión humana?
- `confidence_score`: nivel de confianza en el momento de la decisión
- `hash_sha256`: hash del registro actual
- `hash_previo`: hash del registro anterior (o "GENESIS")

---

### Artículo 13 — Transparencia y provisión de información

- Cada decisión tiene `razon_decision` que explica en lenguaje natural por qué el sistema tomó esa decisión.
- El campo `tipo` distingue claramente entre decisión LLM, calculador Python y decisión humana.
- El dashboard muestra badges visuales con el tipo de decisión (`🤖 Automático`, `👤 HITL`).
- El `confidence_score` es visible en formato porcentaje con barra visual para cada caso.
- La trazabilidad completa (timeline de pasos) es accesible con un clic desde el dashboard.

---

### Artículo 14 — Supervisión humana (Human Oversight)

**Mecanismos implementados:**

1. **Cola HITL obligatoria en modo real**: todos los casos van a revisión humana hasta acumular historial de confianza.
2. **Umbral de confidence**: si el agente tiene confidence <0.80, el caso va automáticamente a HITL.
3. **Dashboard con cola de revisión**: los supervisores tienen una pantalla dedicada con los casos pendientes.
4. **Registro de intervención**: cada decisión HITL queda en el audit log con el nombre del revisor, la decisión, si coincide o contradice al agente, y el tiempo en cola.
5. **Poder de override**: el supervisor puede siempre contradecir al agente (aprobar lo que el agente rechazaría y viceversa).

**Métricas de supervisión (disponibles en el panel de Auditoría AI Act):**
- % de casos con supervisión humana
- % de casos donde el humano contradijo al agente
- Tiempo medio de revisión HITL

---

### Artículo 15 — Exactitud, solidez y ciberseguridad

**Exactitud:**
- Los calculadores Python son deterministas: el mismo input produce siempre el mismo output.
- Test suite: 107 tests, 94% de cobertura. Requerido antes de cualquier deploy de calculadores.
- Mock mode siempre disponible: ninguna demo depende de credenciales externas.

**Solidez:**
- El agente tiene safe-defaults: ante cualquier situación ambigua, escala a HITL en lugar de fallar.
- Los conectores reales se prueban en entorno PRE antes de activar en PRO.

**Ciberseguridad:**
- Autenticación JWT con expiración de 8 horas.
- Passwords hasheados con bcrypt (cost factor 12).
- Los conectores de aseguradoras usan HTTPS con certificados válidos.
- El audit log usa SHA256 para detectar cualquier manipulación.

---

## 3. Panel de Auditoría en el dashboard

El panel de Auditoría AI Act (pantalla visible para roles `supervisor`, `auditor`, `admin`) muestra:

- **KPIs de compliance**: supervisión humana, contradicciones, tiempo medio HITL, integridad del log.
- **Tabla de todas las autorizaciones**: con tipo de decisión (🤖 Automático / 👤 HITL), confidence, y acceso a trazabilidad.
- **Trazabilidad completa por caso**: timeline de todos los pasos del grafo con SHA256 de cada uno.
- **Estado del sistema**: versión de calculadores, DATA_STATUS, modo actual, estado Doctoris.

---

## 4. Proceso de verificación de integridad del audit log

```bash
# Via API (devuelve integro: true/false por caso)
GET /api/v1/audit/{autorizacion_id}

# Via panel de Auditoría AI Act en el dashboard
# → Click en 🔍 de cualquier caso → Ver trazabilidad
# → Badge final: "✓ Sistema compliant con AI Act · Cadena íntegra"
```

---

## 5. Umbral de activación del HITL

El umbral actual es `CONFIDENCE_THRESHOLD_HITL=0.80`. En producción:

- Todos los casos van a HITL (100%) hasta acumular 100 autorizaciones consecutivas con confidence >0.95.
- Después de alcanzar el umbral, el sistema puede tomar decisiones autónomas para casos con confidence ≥0.95.
- El supervisor siempre puede intervenir en cualquier caso, incluso tras alcanzar el umbral.

---

## 6. Instrucciones para el auditor externo

1. Acceder al dashboard: `http://[servidor]/dashboard` con credenciales de rol `auditor`.
2. Navegar a "Auditoría AI Act" en el sidebar.
3. Verificar los KPIs de compliance en la sección superior.
4. Para auditar un caso específico: hacer clic en 🔍 en la fila correspondiente.
5. Verificar el badge de integridad SHA256 en la trazabilidad del caso.
6. Exportar el reporte AI Act de cualquier caso como JSON: botón "⬇ Exportar JSON".
7. Para verificación programática: `GET /api/v1/audit/{id}/aiact-report`.

---

*Última actualización: Mayo 2026 — SoberanIA · Isabella Cristancho*