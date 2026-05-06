"""Parser básico de mensajes HL7 v2.

Convierte un mensaje HL7 a texto plano legible para que el parser LLM
pueda extraer los datos clínicos. El LLM se queda con esto último —
nosotros sólo limpiamos el formato pipe-delimited.

Para Fase 2: parser mínimo. La integración HL7 completa con Doctoris
viene en Fase 0 con HM.
"""

SEPARADOR_SEGMENTOS = "\r"


def hl7_a_texto(mensaje_hl7: str) -> str:
    """Convierte un mensaje HL7 v2 a texto descriptivo.

    Mantiene los segmentos relevantes (PID, IN1, OBR, ORC) y los presenta
    de forma que el LLM o el mock heurístico los pueda parsear.
    """
    # Normalizar separadores (algunos sistemas usan \n en lugar de \r)
    mensaje = mensaje_hl7.replace("\r\n", SEPARADOR_SEGMENTOS).replace(
        "\n", SEPARADOR_SEGMENTOS
    )
    segmentos = [s.strip() for s in mensaje.split(SEPARADOR_SEGMENTOS) if s.strip()]

    lineas: list[str] = []
    for segmento in segmentos:
        tipo = segmento[:3]
        if tipo == "PID":
            lineas.append(f"Paciente: {segmento}")
        elif tipo == "IN1":
            lineas.append(f"Aseguradora: {segmento}")
        elif tipo == "OBR":
            lineas.append(f"Procedimiento: {segmento}")
        elif tipo == "ORC":
            lineas.append(f"Orden: {segmento}")
    return "\n".join(lineas) if lineas else mensaje
