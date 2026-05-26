# SoberanIA Health — Conectores de Aseguradoras

> Spec de integración con aseguradoras. Documento para el ingeniero que implemente los conectores reales en Fase C.

---

## 1. Contrato BaseConnector

Todo conector debe implementar `app/conectores/base_connector.py`:

```python
class BaseConnector(ABC):
    @abstractmethod
    async def enviar_solicitud(self, solicitud: dict) -> dict:
        """
        Envía una solicitud de autorización a la aseguradora.
        Retorna: { referencia, estado_inicial }
        """

    @abstractmethod
    async def consultar_estado(self, referencia: str) -> dict:
        """
        Consulta el estado de una solicitud en curso.
        Retorna: { estado, numero_autorizacion, motivo_denegacion }
        """

    @property
    @abstractmethod
    def data_status(self) -> str:
        """SIMULADO | PENDIENTE_VALIDACION | VALIDADO"""
```

Para añadir un nuevo conector:
1. Crear `app/conectores/{aseg}_connector.py` que extienda `BaseConnector`.
2. Añadir tests en `tests/test_e2e.py` con 10 casos para esa aseguradora.
3. Cambiar `DATA_STATUS` cuando el catálogo esté validado con HM.
4. Actualizar este documento con los detalles de la API.

---

## 2. Estado actual de conectores

| Aseguradora | Conector | Estado | Portal / API | Notas |
|-------------|----------|--------|-------------|-------|
| Sanitas | `mock_connector.py` | **SIMULADO** | Portal web desconocido | API privada. Requiere credenciales HM. |
| Adeslas / SegurCaixa | `mock_connector.py` | **SIMULADO** | Portal web desconocido | API privada. Requiere credenciales HM. |
| DKV Seguros | `mock_connector.py` | **SIMULADO** | Portal web desconocido | API privada. Requiere credenciales HM. |

El `MockConnector` simula respuestas aleatorias con seed configurable (`MOCK_CONNECTOR_SEED=42` en `.env` para reproducibilidad en demos).

---

## 3. Investigación de APIs por aseguradora

### Sanitas
- **Tipo de integración conocida:** Desconocido (pendiente de información de HM).
- **Portal de autorizaciones:** Posiblemente `portal.sanitas.es` o similar (requiere validación).
- **Posibles enfoques:** REST API con OAuth2, o scraping RPA del portal web.
- **Contacto técnico HM:** Xavier Tarragó Bonfill, Director de Transformación Digital.
- **Estado:** Pendiente de reunión técnica con Sanitas via HM.

### Adeslas / SegurCaixa Adeslas
- **Tipo de integración conocida:** Desconocido (pendiente de información de HM).
- **Estado:** Pendiente de reunión técnica con Adeslas via HM.

### DKV Seguros
- **Tipo de integración conocida:** Desconocido (pendiente de información de HM).
- **Estado:** Pendiente de reunión técnica con DKV via HM.

> **Nota:** Las APIs de las aseguradoras son privadas y solo accesibles con credenciales de HM Hospitales. No hay documentación pública disponible. El acceso se coordinará en Fase C con Xavier Tarragó.

---

## 4. Variables de entorno necesarias por conector

Añadir a `.env` cuando se active cada conector:

```bash
# Sanitas (cuando esté disponible)
SANITAS_PORTAL_URL=https://...
SANITAS_USER=usuario_hm
SANITAS_PASSWORD=password_hm

# Adeslas (cuando esté disponible)
ADESLAS_PORTAL_URL=https://...
ADESLAS_USER=usuario_hm
ADESLAS_PASSWORD=password_hm

# DKV (cuando esté disponible)
DKV_PORTAL_URL=https://...
DKV_USER=usuario_hm
DKV_PASSWORD=password_hm
```

---

## 5. Cómo activar un conector real

1. Implementar `app/conectores/{aseg}_connector.py` siguiendo el contrato `BaseConnector`.
2. Escribir tests de integración que usen el conector real (en entorno PRE, nunca en local).
3. Validar el catálogo de procedimientos con HM → `DATA_STATUS = "PENDIENTE_VALIDACION"`.
4. Ejecutar los 10 casos E2E de esa aseguradora en entorno PRE.
5. Si pasan, cambiar `DATA_STATUS = "VALIDADO"`.
6. Activar en PRO solo si el PR tiene aprobación de Isabella.
7. Actualizar este documento con los detalles de la API activada.

---

## 6. Integración Doctoris HIS

El endpoint `POST /api/v1/integraciones/doctoris/orden` es actualmente un stub (estado: `STUB`).

Cuando HM proporcione acceso a las APIs PRE de Doctoris:
1. Implementar `app/integrations/doctoris_webhook.py` (actualmente stub vacío).
2. Validar la firma del webhook con `X-Doctoris-Signature: <hmac-sha256>`.
3. Parsear el mensaje HL7 v2.x con `app/integrations/hl7_parser.py`.
4. Llamar a `autorizacion_service.procesar(orden_texto)`.
5. Responder con el ID de autorización generado.
6. Cambiar `DOCTORIS_WEBHOOK_STATUS = "ACTIVO"` en el módulo.

El formato de mensaje HL7 v2.x que Doctoris envía está documentado en `app/integrations/hl7_mock.py` (mensajes ORM^O01 de ejemplo).

**Estado actual:** `GET /api/v1/integraciones/doctoris/status` → `{"status": "STUB"}`.

---

*Última actualización: Mayo 2026 — SoberanIA · Isabella Cristancho*