"""Abstracción del cliente LLM con fallback mock.

Sec 19 regla 5: mock mode siempre disponible. Sin MISTRAL_API_KEY el agente
debe seguir funcionando para demos sin credenciales.

Sec 19 regla 3: el LLM nunca decide códigos ni datos numéricos. Solo extrae
texto a JSON estructurado y valida formato.
"""
import json
import re
from typing import Optional

from app.agent.prompts import GUARDRAIL_SYSTEM_PROMPT, PARSER_SYSTEM_PROMPT
from app.config import settings

PARSER_MODEL = "mistral-large-latest"
GUARDRAIL_MODEL = "open-mistral-nemo"

# Strings que indican que la "key" es un placeholder, no una key real.
# Si la key cae en este set → mock mode (regla 5 sec 19).
_PLACEHOLDERS = {
    "", "your_key_here", "your-key-here", "changeme", "change-me",
    "todo", "xxx", "none", "null",
}


def _es_placeholder(key: Optional[str]) -> bool:
    if not key:
        return True
    return key.strip().lower() in _PLACEHOLDERS


class LLMClient:
    """Cliente LLM unificado con fallback determinístico.

    Si settings.mistral_api_key está vacío → usa heurísticas deterministas.
    Si está set → usa Mistral API real.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.mistral_api_key
        self.use_mock = _es_placeholder(self.api_key)
        self._real_client = None

    @property
    def real_client(self):
        if self._real_client is None and not self.use_mock:
            from mistralai import Mistral

            self._real_client = Mistral(api_key=self.api_key)
        return self._real_client

    async def parse_orden_medica(self, orden_raw: str) -> dict:
        """Extrae JSON estructurado de la orden médica."""
        if self.use_mock:
            return _mock_parse(orden_raw)
        return await _real_parse(self.real_client, orden_raw)

    async def validar_guardrail(self, datos: dict) -> dict:
        """Valida coherencia del JSON extraído."""
        if self.use_mock:
            return _mock_guardrail(datos)
        return await _real_guardrail(self.real_client, datos)


# ---------------------------------------------------------------------------
# Mock heurístico — sin red, sin credenciales, determinístico
# ---------------------------------------------------------------------------

# Reglas heurísticas para extraer datos de órdenes médicas en formato HL7
# o texto libre en mock mode. NO sustituyen al LLM real — solo simulan
# para demos y tests E2E. Determinísticas para que los tests sean reproducibles.

_ASEGURADORAS_KEYWORDS = {
    "sanitas": "Sanitas",
    "adeslas": "Adeslas",
    "dkv": "DKV",
}

_POLIZAS_KEYWORDS = {
    "mas_salud_plus": "mas_salud_plus",
    "más salud plus": "mas_salud_plus",
    "mas_salud": "mas_salud",
    "más salud": "mas_salud",
    "mundisalud": "mundisalud",
    "premium": "premium",
    "optima": "optima",
    "óptima": "optima",
    "completa": "completa",
    "classica": "classica",
    "integral": "integral",
    "plena": "plena",
    "basica": "basica",
    "básica": "basica",
    "elite": "elite",
    "top": "top",
}

_PROCEDIMIENTOS_KEYWORDS = [
    # (regex, sim_id, descripcion)
    # Orden importa: las patterns más específicas van primero.
    (r"rm[\s_-]+rodilla|resonancia.{0,30}rodilla", "SIM_RM_RODILLA_DCHA", "Resonancia magnética rodilla derecha"),
    (r"tac[\s_-]+abdomin|tomograf[ií]a.{0,30}abdomin", "SIM_TAC_ABDOMINAL", "TAC abdominal con contraste"),
    (r"artroscop", "SIM_ARTROSCOPIA_RODILLA", "Artroscopia rodilla"),
    (r"cirug[ií]a.{0,30}rodilla", "SIM_CIRUGIA_RODILLA_AMB", "Cirugía ambulatoria de rodilla"),
    (r"cirug[ií]a.{0,30}cadera|fractura.{0,30}cadera", "SIM_CIRUGIA_CADERA", "Cirugía de cadera"),
    (r"cirug[ií]a.{0,30}catarat", "SIM_CIRUGIA_CATARATAS", "Cirugía cataratas"),
    (r"rm[\s_-]+cerebr|resonancia.{0,30}cerebr", "SIM_RM_CEREBRAL", "Resonancia magnética cerebral"),
    (r"rm[\s_-]+columna[\s_-]*cervical|resonancia.{0,30}columna[\s_-]*cervical", "SIM_RM_COLUMNA_CERVICAL", "Resonancia magnética columna cervical"),
    (r"rm[\s_-]+(?:columna|lumbar)|resonancia.{0,30}(?:columna|lumbar)", "SIM_RM_COLUMNA_LUMBAR", "Resonancia magnética columna lumbar"),
    (r"tac[\s_-]+t[oó]rax|tomograf[ií]a.{0,30}t[oó]rax", "SIM_TAC_TORAX", "TAC tórax"),
    (r"tac[\s_-]+(?:cerebr|cranea?l)|tomograf[ií]a.{0,30}(?:cerebr|cranea?l)", "SIM_TAC_CEREBRAL", "TAC cerebral"),
    (r"colonoscop", "SIM_COLONOSCOPIA", "Colonoscopia"),
    (r"ecocardiogram", "SIM_ECOCARDIOGRAMA", "Ecocardiograma"),
    (r"radiograf[ií]a.{0,30}t[oó]rax", "SIM_RADIOGRAFIA_TORAX", "Radiografía tórax"),
    (r"fisioterapi", "SIM_FISIOTERAPIA", "Fisioterapia"),
    (r"endoscop", "SIM_ENDOSCOPIA_DIGESTIVA", "Endoscopia digestiva"),
    (r"densitometr[ií]a", "SIM_DENSITOMETRIA_OSEA", "Densitometría ósea"),
    (r"apendicectom[ií]a|apendic", "SIM_APENDICECTOMIA", "Apendicectomía"),
    (r"gammagraf[ií]a", "SIM_GAMMAGRAFIA_OSEA", "Gammagrafía ósea"),
    (r"litotric", "SIM_LITOTRICIA_RENAL", "Litotricia renal"),
]


def _mock_parse(orden_raw: str) -> dict:
    """Heurística simple: detecta aseguradora, póliza y procedimiento por keywords.

    Devuelve null en campos no detectados — el guardrail los marcará como
    faltantes y el flujo dispará HITL.
    """
    texto_lower = orden_raw.lower()

    aseguradora = None
    for kw, valor in _ASEGURADORAS_KEYWORDS.items():
        if kw in texto_lower:
            aseguradora = valor
            break
    # Fallback: si no es ninguna de las 3 soportadas (sanitas/adeslas/dkv),
    # extraer el nombre literal de la línea "Aseguradora: ...". El verificador
    # se encargará de marcarla como no soportada y disparar HITL — pero el
    # campo se persiste con su nombre real (Mapfre, Asisa, etc.) para el
    # audit log y el dashboard.
    if aseguradora is None:
        aseguradora = _extraer_aseguradora_libre(orden_raw)

    tipo_poliza = None
    # Buscar la mas larga primero para no confundir "mas_salud" con "mas_salud_plus"
    for kw in sorted(_POLIZAS_KEYWORDS, key=len, reverse=True):
        if kw in texto_lower:
            tipo_poliza = _POLIZAS_KEYWORDS[kw]
            break

    cie10 = None
    descripcion = None
    for patron, sim_id, desc in _PROCEDIMIENTOS_KEYWORDS:
        if re.search(patron, texto_lower):
            cie10 = sim_id
            descripcion = desc
            break
    # Fallback: si ninguna keyword matchea, extraer la línea "Procedimiento: ..."
    # tal cual del texto libre. cie10 queda en None — eso es correcto porque
    # sin código no podemos enviar a la aseguradora (irá a HITL por safe-default).
    if descripcion is None:
        descripcion = _extraer_procedimiento_libre(orden_raw)

    paciente_nombre = _extraer_paciente_hl7(orden_raw) or _extraer_paciente_libre(orden_raw)
    medico_nombre = _extraer_medico_hl7(orden_raw) or _extraer_medico_libre(orden_raw)
    poliza_numero = _extraer_poliza_hl7(orden_raw) or _extraer_poliza_libre(orden_raw)
    urgente = "urgente" in texto_lower or "urgent" in texto_lower
    es_reenvio = "reenvio_solicitud_info: true" in texto_lower

    return {
        "paciente_nombre": paciente_nombre,
        "paciente_id": None,
        "paciente_aseguradora": aseguradora,
        "paciente_poliza": poliza_numero,
        "paciente_tipo_poliza": tipo_poliza,
        "procedimiento_descripcion": descripcion,
        "procedimiento_cie10": cie10,
        "medico_nombre": medico_nombre,
        "medico_especialidad": None,
        "fecha_solicitud": None,
        "urgente": urgente,
        "diagnostico_principal": None,
        "notas_clinicas": None,
        "es_reenvio": es_reenvio,
    }


def _mock_guardrail(datos: dict) -> dict:
    """Valida que campos obligatorios estén presentes.

    Confidence alta (>0.85) si todos los obligatorios están.
    Confidence media (0.7) si falta cie10.
    Confidence baja (<0.5) si faltan obligatorios → HITL.

    Nota: tipo_poliza NO es obligatorio aquí — en producción lo provee la
    aseguradora al consultar el número de póliza. El agente usa "basica"
    como default seguro cuando no viene explícito en la orden.
    """
    # Reenvíos con documentación aportada: el guardrail da paso libre —
    # la documentación adjunta resuelve la incertidumbre del primer intento.
    if datos.get("es_reenvio"):
        return {
            "valido": True,
            "campos_faltantes": [],
            "inconsistencias": [],
            "confidence": 0.87,
            "requiere_hitl": False,
            "razon_hitl": "",
        }

    obligatorios = [
        "paciente_nombre",
        "paciente_aseguradora",
        "procedimiento_descripcion",
        "medico_nombre",
    ]
    faltantes = [c for c in obligatorios if not datos.get(c)]

    inconsistencias = []
    if datos.get("urgente") not in (True, False):
        inconsistencias.append("campo 'urgente' debe ser boolean")

    if faltantes:
        confidence = 0.3
        requiere_hitl = True
        razon = f"Campos obligatorios faltantes: {', '.join(faltantes)}"
    elif not datos.get("procedimiento_cie10"):
        confidence = 0.7
        requiere_hitl = True
        razon = "Falta procedimiento_cie10 — no podemos elegir código sin HITL"
    else:
        confidence = 0.92
        requiere_hitl = False
        razon = ""

    return {
        "valido": not faltantes and not inconsistencias,
        "campos_faltantes": faltantes,
        "inconsistencias": inconsistencias,
        "confidence": confidence,
        "requiere_hitl": requiere_hitl,
        "razon_hitl": razon,
    }


# Heurísticas de extracción para HL7 v2 pipe format y texto libre
# HL7 PID segment: PID|1||12345^^^HM||GARCIA^MARIA^ANA||...
_HL7_PID_RE = re.compile(r"PID\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|([^|]+)")
_HL7_OBR_RE = re.compile(r"OBR\|[^|]*\|[^|]*\|[^|]*\|[^|]+\|+\d+\|+\^([^|]+)")
_HL7_IN1_POLIZA_RE = re.compile(r"IN1\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|([A-Z0-9]+)\|")


def _extraer_paciente_hl7(texto: str) -> Optional[str]:
    match = _HL7_PID_RE.search(texto)
    if not match:
        return None
    nombre_raw = match.group(1)
    # Formato HL7: APELLIDOS^NOMBRE^SEGUNDO_NOMBRE
    partes = [p for p in nombre_raw.split("^") if p]
    if len(partes) >= 2:
        return f"{' '.join(partes[1:])} {partes[0]}".strip()
    return nombre_raw.strip()


def _extraer_paciente_libre(texto: str) -> Optional[str]:
    # Heurística mínima para texto libre
    match = re.search(r"paciente[:\s]+([^,\n]+)", texto, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extraer_medico_hl7(texto: str) -> Optional[str]:
    match = re.search(r"\^DR_([A-Z]+)\^([A-Z]+)", texto)
    if match:
        return f"Dr. {match.group(2).title()} {match.group(1).title()}"
    match = re.search(r"\^([A-Z]+)\^([A-Z]+)\b.*OBR", texto, re.DOTALL)
    return None


def _extraer_medico_libre(texto: str) -> Optional[str]:
    # Detecta "Dr.", "Dra.", "Dr ", "Dra " seguido del nombre
    match = re.search(r"(Dra?\.?\s+[A-ZÁÉÍÓÚÑ][\w\sÁÉÍÓÚÑáéíóúñ]+)", texto)
    return match.group(1).strip() if match else None


def _extraer_poliza_hl7(texto: str) -> Optional[str]:
    match = _HL7_IN1_POLIZA_RE.search(texto)
    return match.group(1) if match else None


# Texto libre: "Póliza: Más Salud Plus 987654" → captura "987654".
# Acepta cualquier prefijo (tipo de póliza) seguido de un número de ≥4 dígitos
# o un código alfanumérico tipo SAN-4471892.
_POLIZA_LIBRE_RE = re.compile(
    r"p[oó]liza[:\s]+[^\n]*?([A-Z]{2,4}-\d{4,}|\d{4,})",
    re.IGNORECASE,
)


def _extraer_poliza_libre(texto: str) -> Optional[str]:
    match = _POLIZA_LIBRE_RE.search(texto)
    return match.group(1) if match else None


# Texto libre: "Aseguradora: Mapfre" → captura "Mapfre". Para nombres
# compuestos como "DKV Seguros" captura todo hasta el salto de línea.
_ASEGURADORA_LIBRE_RE = re.compile(
    r"aseguradora[:\s]+([^\n]+)",
    re.IGNORECASE,
)


def _extraer_aseguradora_libre(texto: str) -> Optional[str]:
    match = _ASEGURADORA_LIBRE_RE.search(texto)
    if not match:
        return None
    return match.group(1).strip() or None


# Texto libre: "Procedimiento: TAC cerebral URGENTE" → captura el resto de
# la línea sin "URGENTE" final (que ya se detecta por separado en `urgente`).
_PROCEDIMIENTO_LIBRE_RE = re.compile(
    r"procedimiento[:\s]+([^\n]+)",
    re.IGNORECASE,
)


def _extraer_procedimiento_libre(texto: str) -> Optional[str]:
    match = _PROCEDIMIENTO_LIBRE_RE.search(texto)
    if not match:
        return None
    desc = match.group(1).strip()
    # Quitar marca "URGENTE" final — ya viaja en el campo urgente
    desc = re.sub(r"\s+URGENTE\s*$", "", desc, flags=re.IGNORECASE)
    return desc.strip() or None


# ---------------------------------------------------------------------------
# Real Mistral API
# ---------------------------------------------------------------------------


async def _real_parse(client, orden_raw: str) -> dict:
    response = await client.chat.complete_async(
        model=PARSER_MODEL,
        messages=[
            {"role": "system", "content": PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": orden_raw},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


async def _real_guardrail(client, datos: dict) -> dict:
    response = await client.chat.complete_async(
        model=GUARDRAIL_MODEL,
        messages=[
            {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(datos, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
