# SoberanIA Health — Guía del Dashboard

> Guía para recepcionistas, supervisores y formadores de HM Hospitales.

---

## 1. Cómo acceder

**URL:** `http://[servidor_hm]/dashboard`

**Credenciales de demo (cambiar antes del piloto con HM):**

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Administrador | `isabella@hmhospitales.es` | `soberania2026` |
| Supervisor | `supervisor@hmhospitales.es` | `supervisor2026` |
| Auditor AI Act | `auditor@hmhospitales.es` | `auditor2026` |

La sesión dura **8 horas** (una jornada laboral completa). Al terminar el turno, hacer clic en "Cerrar sesión".

---

## 2. Pantallas del dashboard

### Resumen (pantalla de inicio)

Muestra el estado general de todas las autorizaciones:
- **5 KPIs**: Total, Pendiente revisión, Autorizadas, Rechazadas, Urgentes.
- **Gráfico de estado**: distribución de autorizaciones por estado.
- **Gráfico por aseguradora**: volumen Sanitas / Adeslas / DKV.
- **Panel de urgentes**: los casos más urgentes con badge rojo.

### Autorizaciones

Tabla completa de todas las autorizaciones con:
- **Filtros rápidos** (pestañas): Todas, En proceso, Pendiente HITL, Urgentes, Autorizadas, Rechazadas.
- **Búsqueda**: por nombre de paciente, aseguradora o número de autorización.
- **Acciones por fila**: Ver detalle (👁), Aprobar (✓), Rechazar (✕).

### Cola HITL

Solo muestra los casos en estado **"Pendiente HITL"** que requieren revisión humana.

### Urgentes

Solo muestra los casos marcados como **urgentes**.

### Auditoría AI Act *(solo supervisores, auditores y admins)*

Panel técnico de compliance. Ver `docs/AI_ACT_COMPLIANCE.md` para detalles.

---

## 3. Cómo introducir una nueva autorización

1. Ir a la pantalla **Autorizaciones**.
2. Hacer clic en **"+ Nueva autorización"** (botón azul, esquina superior derecha).
3. Rellenar el formulario:
   - **Nombre del paciente**: nombre completo.
   - **Aseguradora**: seleccionar Sanitas, Adeslas, DKV, u Otra.
   - **Número de póliza**: el número que aparece en la tarjeta del seguro.
   - **Procedimiento solicitado**: descripción del procedimiento (ej: "Resonancia magnética rodilla derecha").
   - **Médico solicitante**: nombre y especialidad del médico.
   - **Urgente**: marcar si el caso es urgente.
   - **Notas adicionales**: información clínica relevante (opcional).
4. Hacer clic en **"Enviar al agente"**.
5. El sistema procesará la solicitud en segundos:
   - Si aparece **"Autorizada"** (verde): la aseguradora ha dado luz verde.
   - Si aparece **"Pendiente HITL"** (amarillo): el caso requiere revisión de un supervisor antes de continuar.
   - Si aparece otro estado: consultar con el supervisor.

> **Nota:** Si la aseguradora es "Otra" (Mapfre, Asisa, Cigna, etc.), el caso irá automáticamente a HITL porque el sistema solo tiene catálogos para Sanitas, Adeslas y DKV.

---

## 4. Estados de una autorización

| Estado | Color | Significado |
|--------|-------|-------------|
| **Pendiente HITL** | Amarillo | El agente no puede decidir solo. Un supervisor debe revisarlo. |
| **Autorizada** | Verde | La aseguradora ha dado autorización. |
| **Aprobado HITL** | Verde | Un supervisor ha aprobado el caso manualmente. |
| **Rechazada** | Rojo | La aseguradora ha denegado la autorización. |
| **Rechazado HITL** | Rojo | Un supervisor ha rechazado el caso manualmente. |
| **Más info solicitada** | Naranja | Un supervisor ha pedido información adicional. |
| **En proceso** | Naranja | El sistema está procesando la solicitud. |
| **Error** | Rojo oscuro | Error técnico. Contactar con soporte. |

---

## 5. Cómo revisar una autorización en cola HITL *(supervisores)*

1. Ir a la pantalla **Cola HITL** (o hacer clic en el icono ⏳ del sidebar).
2. Ver los casos pendientes. Cada uno muestra el nombre del paciente, aseguradora, procedimiento y el nivel de confianza del agente.
3. Hacer clic en **👁 Ver detalle** para abrir el panel de detalles.
4. Revisar:
   - Los datos del caso.
   - El motivo por el que el agente no pudo decidir solo.
   - El historial de pasos del proceso.
5. Tomar una decisión:
   - **✓ Aprobar**: la autorización puede seguir adelante.
   - **✕ Rechazar**: se deniega la autorización.
   - **ℹ Más info**: se necesita información adicional antes de decidir.
6. Opcionalmente añadir notas en el campo de texto antes de confirmar.

También se puede aprobar o rechazar directamente desde la tabla haciendo clic en ✓ o ✕ sin abrir el detalle.

---

## 6. Notificaciones en tiempo real

El dashboard muestra notificaciones (toasts) en la esquina superior derecha cuando:
- Se procesa una nueva autorización.
- Un supervisor toma una decisión HITL.

Las notificaciones se cierran automáticamente en 5 segundos, o se pueden cerrar manualmente con el botón ✕.

---

## 7. Qué hacer si un caso lleva mucho tiempo pendiente

1. Verificar que el caso esté en estado "Pendiente HITL" (no simplemente "En proceso").
2. Si está en HITL y no hay supervisores disponibles, escalar por los canales habituales del centro.
3. Si el caso lleva más de 24 horas en "En proceso" (no HITL), puede ser un error técnico. Contactar con soporte.

---

## 8. FAQ

**¿Puedo usar el dashboard desde una tablet?**  
Sí. El dashboard está optimizado para tablets. Se recomienda orientación horizontal.

**¿Qué pasa si cierro el navegador sin cerrar sesión?**  
La sesión expira automáticamente a las 8 horas. Al volver a abrir el navegador se pedirá el login de nuevo.

**¿El sistema guarda mis decisiones HITL?**  
Sí. Cada decisión queda registrada en el audit log con tu nombre y la fecha y hora exacta.

**¿Puedo cancelar una autorización ya enviada?**  
No directamente desde el dashboard. Si el caso está en "Pendiente HITL", puedes rechazarlo. Si ya está "Autorizada", contactar con el departamento correspondiente.

**¿Qué significa "Confidence"?**  
Es el nivel de certeza del agente (0-100%). Por encima del 80% el sistema puede decidir solo. Por debajo, el caso va a revisión humana.

**¿Puedo buscar autorizaciones antiguas?**  
Sí. Usa la barra de búsqueda en la pantalla Autorizaciones. Busca por nombre de paciente, aseguradora o número de autorización.

---

*Guía creada por SoberanIA · Mayo 2026*