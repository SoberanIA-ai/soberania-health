# SoberanIA Health — Guía del Dashboard

> Guía para recepcionistas, supervisores y formadores de HM Hospitales.

---

## 1. Cómo acceder

**URL:** `http://localhost:3002` (demo local) · `http://[servidor_hm]` (producción)

**Usuarios de demo:**

| Rol           | Email                            | Contraseña     | Acceso                                      |
|---------------|----------------------------------|----------------|---------------------------------------------|
| Admin         | isabella.cristancho@soberania.eu | soberania2026  | Todo                                        |
| Recepcionista | recepcion@hmhospitales.es        | recepcion2026  | Autorizaciones + Urgentes                   |
| Supervisor    | supervisor@hmhospitales.es       | supervisor2026 | Autorizaciones + Cola HITL + Urgentes       |
| Auditor       | auditor@hmhospitales.es          | auditor2026    | Solo lectura + panel Auditoría AI Act       |

La sesión dura **8 horas** (una jornada laboral). Al terminar, hacer clic en "Cerrar sesión".

---

## 2. Pantallas del dashboard

El sidebar muestra solo las secciones a las que tiene acceso cada rol.

### Resumen *(admin, supervisor)*
- **5 KPIs**: Total, Pendiente revisión, Autorizadas, Rechazadas, Urgentes.
- Gráfico de distribución por estado y por aseguradora.

### Autorizaciones *(recepcionista, supervisor, admin)*
- Tabla completa con filtros rápidos: Todas, En proceso, Pendiente HITL, Urgentes, Autorizadas, Rechazadas.
- Búsqueda por nombre de paciente, aseguradora o número de autorización.
- Botón **"+ Nueva autorización"** para crear una solicitud manual.

### Cola HITL *(supervisor, admin)*
- Solo los casos en estado **"Pendiente HITL"** que requieren revisión humana.

### Urgentes *(recepcionista, supervisor, admin)*
- Solo los casos marcados como urgentes.

### Auditoría AI Act *(auditor, admin)*
- Métricas de compliance, tabla de decisiones, trazabilidad completa por caso.
- Ver `docs/AI_ACT_COMPLIANCE.md` para detalles.

---

## 3. Cómo introducir una nueva autorización *(recepcionista, admin)*

1. Ir a **Autorizaciones** → **"+ Nueva autorización"**.
2. Rellenar el formulario:
   - **Nombre del paciente**: nombre completo.
   - **Aseguradora**: Sanitas, Adeslas, DKV, u Otra.
   - **Número de póliza**: el número de la tarjeta del seguro.
   - **Procedimiento solicitado**: descripción del procedimiento (ej: "Resonancia magnética rodilla derecha").
   - **Médico solicitante**: nombre y especialidad.
   - **Urgente**: marcar si el caso es urgente.
   - **Notas adicionales**: información clínica relevante (opcional).
3. Hacer clic en **"Enviar al agente"**.
4. Resultado en segundos:
   - **Autorizada** (verde): la aseguradora ha dado luz verde.
   - **Pendiente HITL** (amarillo): requiere revisión de un supervisor.
   - **Denegada** (rojo): la aseguradora ha rechazado la solicitud.

> **Nota:** Si la aseguradora es "Otra" (Mapfre, Asisa, etc.), el caso irá automáticamente a HITL porque el sistema solo tiene catálogos para Sanitas, Adeslas y DKV.

---

## 4. Estados de una autorización

| Estado | Color | Significado |
|--------|-------|-------------|
| **Pendiente HITL** | Amarillo | El agente no puede decidir solo. Un supervisor debe revisarlo. |
| **Información adicional** | Azul | El supervisor ha pedido documentación al médico/recepción. |
| **Autorizada** | Verde | La aseguradora ha dado autorización. |
| **Aprobado HITL** | Verde | Un supervisor ha aprobado el caso manualmente. |
| **Rechazada** | Rojo | La aseguradora ha denegado la autorización. |
| **Rechazado HITL** | Rojo | Un supervisor ha rechazado el caso manualmente. |
| **En proceso** | Gris | El sistema está procesando la solicitud. |
| **Error de procesamiento** | Rojo oscuro | Ha fallado un servicio externo (el asistente de IA o el portal de la aseguradora) al procesar el caso. No se ha perdido información: el caso pasa automáticamente a Cola HITL para que un supervisor lo revise y, si hace falta, lo reenvíe. |

---

## 5. Cómo revisar una autorización en cola HITL *(supervisor)*

1. Ir a **Cola HITL** (icono ⏳ en el sidebar).
2. Hacer clic en un caso para abrir el panel de detalles.
3. Revisar:
   - Los datos del caso (paciente, aseguradora, procedimiento).
   - El **motivo por el que el agente envió a HITL** (mensaje del Agente IA).
   - La confianza del agente (confidence).
   - El historial SHA256 en el audit log.
4. Tomar una decisión:
   - **✓ Aprobar**: la autorización puede seguir adelante.
   - **✕ Rechazar**: se deniega la autorización. Añadir notas con el motivo.
   - **ℹ Más info**: se necesita documentación adicional. Escribir en el campo de notas qué hay que aportar (ej: "Adjuntar informe del traumatólogo").

---

## 6. Flujo "Más información" *(recepcionista / médico → supervisor)*

Cuando un supervisor marca un caso como "Más info":

1. El caso pasa a estado **"Información adicional requerida"**.
2. La recepcionista o el médico ve el caso en Autorizaciones con un panel azul que muestra:
   - Quién lo pidió y **qué documentación necesita**.
   - Un área para **subir archivos** (PDF, Word, imágenes, XML).
   - Un campo para añadir notas adicionales.
3. Tras adjuntar los documentos, hacer clic en **"Reenviar al agente"**.
4. El agente reprocesa el caso con la nueva documentación:
   - Sanitas/Adeslas/DKV con procedimiento conocido → **Autorizado**.
   - Aseguradora no soportada → **vuelve a cola HITL** con los docs ya adjuntos para que el supervisor tome la decisión final.

---

## 7. Notificaciones en tiempo real

El dashboard muestra notificaciones en la esquina superior derecha cuando:
- Se procesa una nueva autorización.
- Un supervisor toma una decisión HITL.

Las notificaciones se cierran automáticamente en 5 segundos.

---

## 8. FAQ

**¿Puedo usar el dashboard desde una tablet?**
Sí. El dashboard está optimizado para pantallas de al menos 1024px de ancho.

**¿Qué pasa si cierro el navegador sin cerrar sesión?**
La sesión expira automáticamente a las 8 horas. Al volver se pedirá el login de nuevo.

**¿El sistema guarda mis decisiones HITL?**
Sí. Cada decisión queda en el audit log con tu nombre, la fecha y hora exacta, y un hash SHA256 que garantiza que no ha sido modificada.

**¿Puedo cancelar una autorización ya enviada?**
No directamente. Si está en "Pendiente HITL" puedes rechazarla. Si ya está "Autorizada", contactar con el departamento correspondiente.

**¿Qué significa "Confidence"?**
El nivel de certeza del agente (0–100%). Por encima del 80% el sistema puede decidir solo. Por debajo, el caso va a revisión humana.

**¿La recepcionista puede aprobar/rechazar casos HITL?**
No. Solo los roles supervisor y admin pueden tomar decisiones HITL. La recepcionista puede ver los casos y reenviar documentación adicional.

---

*Guía actualizada por SoberanIA · Junio 2026*
