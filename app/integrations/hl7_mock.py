"""Mock de Doctoris HIS (sec 9.2 del handoff).

Genera mensajes HL7 v2 simulados para los casos de demo. La integración real
con Doctoris se hace en Fase 0 con HM (assumption sec 20.2: usa HL7).
"""

ORDENES_EJEMPLO: list[dict] = [
    {
        "id": "ORD-001",
        "descripcion": "Caso Sanitas Resonancia Magnética Rodilla",
        "hl7": (
            "MSH|^~\\&|DOCTORIS|HM_MONTEPRINCIPE|SOBERANIA|HEALTH|20260506||"
            "ORM^O01|MSG-001|P|2.5\r"
            "PID|1||12345^^^HM||GARCIA^MARIA^ANA||19810315|F|||"
            "CALLE MAYOR 1^MADRID^28001\r"
            "IN1|1|SANITAS|SANITAS||||||MAS_SALUD_PLUS|987654\r"
            "ORC|NW|ORD-001|||||^^^20260506|^DR_TRAUMATOLOGIA^JUAN\r"
            "OBR|1|ORD-001||RM_RODILLA_DCHA^Resonancia Magnetica Rodilla Derecha"
            "|||20260506"
        ),
    },
    {
        "id": "ORD-002",
        "descripcion": "Caso Sanitas TAC Abdominal",
        "hl7": (
            "MSH|^~\\&|DOCTORIS|HM_MONTEPRINCIPE|SOBERANIA|HEALTH|20260506||"
            "ORM^O01|MSG-002|P|2.5\r"
            "PID|1||23456^^^HM||LOPEZ^CARLOS^|||19720811|M\r"
            "IN1|1|SANITAS|SANITAS||||||BASICA|123456\r"
            "ORC|NW|ORD-002|||||^^^20260506|^DR_DIGESTIVO^ANA\r"
            "OBR|1|ORD-002||TAC_ABDOMINAL^TAC abdominal con contraste|||20260506"
        ),
    },
    {
        "id": "ORD-003",
        "descripcion": "Caso Adeslas RM Cerebral (urgente)",
        "hl7": (
            "MSH|^~\\&|DOCTORIS|HM_MONTEPRINCIPE|SOBERANIA|HEALTH|20260506||"
            "ORM^O01|MSG-003|P|2.5\r"
            "PID|1||34567^^^HM||MARTIN^LAURA^|||19850622|F\r"
            "IN1|1|ADESLAS|ADESLAS||||||COMPLETA|765432\r"
            "ORC|NW|ORD-003|||||^^^20260506|^DR_NEUROLOGIA^MIGUEL\r"
            "OBR|1|ORD-003||RM_CEREBRAL^Resonancia Magnetica Cerebral URGENTE"
            "|||20260506"
        ),
    },
]


def get_orden_ejemplo(caso_id: str) -> str:
    """Devuelve la orden HL7 simulada para un caso_id dado.

    Si no encuentra el caso, devuelve la primera orden por defecto
    (comportamiento de fallback explícito para evitar errores en demo).
    """
    for orden in ORDENES_EJEMPLO:
        if orden["id"] == caso_id:
            return orden["hl7"]
    return ORDENES_EJEMPLO[0]["hl7"]


def listar_casos() -> list[dict]:
    """Lista los casos de demo disponibles (sin el HL7 raw)."""
    return [{"id": o["id"], "descripcion": o["descripcion"]} for o in ORDENES_EJEMPLO]
