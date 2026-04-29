"""Herramientas de exportación y generación de informes clínico-nutricionales UYWA."""

import io
import uuid
import logging
import pandas as pd
from datetime import datetime


# ---------------------------------------------------------------------------
# Funciones de generación de texto
# ---------------------------------------------------------------------------

def generar_diagnostico_resumen(nombre, bcs, estado, mer_final,
                                 prioridad, condicion, edad, aplicar_senior):
    """
    Genera el párrafo de diagnóstico nutricional para el informe de resumen.

    Parámetros:
        nombre (str)        : Nombre de la mascota.
        bcs (int)           : Body Condition Score (1-9).
        estado (str)        : Estado corporal textual.
        mer_final (float)   : MER final ajustado (kcal/día).
        prioridad (str)     : Prioridad nutricional.
        condicion (str)     : Condición fisiológica.
        edad (float)        : Edad en años.
        aplicar_senior (bool): Si se aplica el factor senior.

    Retorna:
        str: Párrafo de diagnóstico.
    """
    texto = f"{nombre} presenta condición corporal {estado.lower()} (BCS {bcs}/9). "
    texto += f"Su requerimiento energético final estimado es de {mer_final:.1f} kcal/día. "
    texto += f"La prioridad nutricional es {prioridad.lower()}."

    if aplicar_senior and edad >= 7:
        texto += " Se ha aplicado factor de ajuste senior (0.85×)."

    condicion_lower = condicion.lower()
    if any(g in condicion_lower for g in ["gestaci", "lactancia"]):
        texto += " Animal en gestación/lactancia: requerimiento elevado por condición reproductiva."

    texto += " Se recomienda monitoreo periódico."
    return texto


def generar_recomendaciones(estado, bcs, edad, condicion, cobertura,
                             cob_pb=None, cob_ee=None):
    """
    Genera la lista de recomendaciones clínico-nutricionales.

    Parámetros:
        estado (str)          : Estado corporal textual.
        bcs (int)             : Body Condition Score (1-9).
        edad (float)          : Edad en años.
        condicion (str)       : Condición fisiológica.
        cobertura (float|None): Cobertura energética en %.
        cob_pb (float|None)   : Cobertura de proteína en %.
        cob_ee (float|None)   : Cobertura de grasa en %.

    Retorna:
        list[str]: Lista de recomendaciones.
    """
    recomendaciones = []

    # Monitoreo según BCS
    if bcs == 5:
        recomendaciones.append(
            "Monitoreo de peso cada 2–4 semanas para mantener la condición corporal actual."
        )
    elif bcs < 5:
        recomendaciones.append(
            "Monitoreo semanal de peso durante la recuperación de condición corporal."
        )
    else:
        recomendaciones.append(
            "Monitoreo bisemanal de peso durante el proceso de reducción de peso."
        )

    # Ajuste de ración según cobertura energética
    if cobertura is not None:
        if cobertura < 90:
            recomendaciones.append(
                "Aumentar la cantidad de alimento gradualmente hasta cubrir el requerimiento energético."
            )
        elif cobertura > 110:
            recomendaciones.append(
                "Reducir la cantidad de alimento o evaluar una alternativa con menor densidad energética."
            )

    # Pacientes senior
    if edad >= 7:
        recomendaciones.append(
            "Realizar evaluación nutricional cada 6–8 semanas dada la edad avanzada del paciente."
        )

    # Cobertura de proteína
    if cob_pb is not None and cob_pb < 90:
        recomendaciones.append(
            "Considerar complementación proteica para cubrir el requerimiento mínimo."
        )

    # Cobertura de grasa
    if cob_ee is not None and cob_ee < 90:
        recomendaciones.append(
            "Evaluar el aporte de ácidos grasos esenciales en la dieta."
        )

    # Gestación / lactancia
    condicion_lower = condicion.lower()
    if "gestaci" in condicion_lower:
        recomendaciones.append("Realizar valoración nutricional pre-parto.")
        recomendaciones.append("Preparar plan nutricional para la fase de lactancia.")
    if "lactancia" in condicion_lower:
        recomendaciones.append(
            "Aumentar la frecuencia de alimentación para sostener la producción de leche."
        )

    return recomendaciones


def generar_decision_resumen(cobertura, energia_aportada, mer_final,
                              gramos_input, gramos_recomendados,
                              cob_pb=None, cob_ee=None):
    """
    Genera la decisión ejecutiva de la evaluación nutricional.

    Retorna:
        tuple: (resultado: str, diferencia_kcal: float, interpretacion: str)
    """
    if cobertura < 90:
        resultado = "No cubre el requerimiento energético"
    elif cobertura <= 110:
        resultado = "Cubre adecuadamente el requerimiento energético"
    else:
        resultado = "Excede el requerimiento energético"

    diferencia = energia_aportada - mer_final

    interpretacion = (
        f"Con la ración actual de {gramos_input:.0f} g/día, "
        f"el alimento aporta {energia_aportada:.0f} kcal "
        f"vs {mer_final:.0f} kcal requeridas, "
        f"lo que representa una cobertura del {cobertura:.1f}%. "
    )

    if abs(diferencia) < 50:
        interpretacion += "La ración está adecuadamente ajustada."
    elif diferencia < 0:
        interpretacion += f"Se recomienda aumentar a {gramos_recomendados:.0f} g/día."
    else:
        interpretacion += f"Se recomienda reducir a {gramos_recomendados:.0f} g/día."

    return resultado, diferencia, interpretacion


# ---------------------------------------------------------------------------
# Exportación a Excel
# ---------------------------------------------------------------------------

def exportar_a_excel(mascota, datos_energeticos, datos_alimento,
                     fecha, mer_final, recomendaciones):
    """
    Genera un archivo Excel con 4 hojas: RESUMEN, VISITA ACTUAL, ANÁLISIS DEL ALIMENTO, RECOMENDACIONES.

    Parámetros:
        mascota (dict)            : Datos de la mascota (nombre, especie, etc.).
        datos_energeticos (dict)  : Valores energéticos y diagnóstico.
        datos_alimento (dict)     : Datos del alimento evaluado.
        fecha (datetime.date)     : Fecha del informe.
        mer_final (float)         : MER final ajustado (kcal/día).
        recomendaciones (list)    : Lista de recomendaciones de texto.

    Retorna:
        bytes: Contenido del archivo Excel.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Formatos
        header_fmt = workbook.add_format({
            "bg_color": "#2176FF",
            "font_color": "white",
            "bold": True,
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        })

        # ── HOJA 1: RESUMEN ────────────────────────────────────────────────
        resumen_data = {
            "Parámetro": [
                "Nombre del paciente",
                "Especie",
                "Edad",
                "Peso actual",
                "BCS",
                "Estado corporal",
                "Riesgo nutricional",
                "MER final",
                "Fecha del informe",
            ],
            "Valor": [
                mascota.get("nombre", "—"),
                mascota.get("especie", "—").capitalize(),
                f"{datos_energeticos.get('edad', 0):.1f} años",
                f"{datos_energeticos.get('peso', 0):.1f} kg",
                f"{datos_energeticos.get('bcs', 0)}/9",
                datos_energeticos.get("estado_corporal", "—"),
                datos_energeticos.get("riesgo_nutricional", "—"),
                f"{mer_final:.1f} kcal/día",
                fecha.strftime("%d/%m/%Y"),
            ],
        }
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name="RESUMEN", index=False)
        ws_resumen = writer.sheets["RESUMEN"]
        ws_resumen.set_column(0, 0, 30)
        ws_resumen.set_column(1, 1, 30)
        for col_idx, col_name in enumerate(df_resumen.columns):
            ws_resumen.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 2: VISITA ACTUAL ──────────────────────────────────────────
        visita_data = {
            "Fecha": [fecha.strftime("%d/%m/%Y")],
            "Nombre": [mascota.get("nombre", "—")],
            "Especie": [mascota.get("especie", "—").capitalize()],
            "Edad (años)": [f"{datos_energeticos.get('edad', 0):.1f}"],
            "Peso (kg)": [f"{datos_energeticos.get('peso', 0):.1f}"],
            "BCS": [f"{datos_energeticos.get('bcs', 0)}/9"],
            "Estado corporal": [datos_energeticos.get("estado_corporal", "—")],
            "Condición fisiológica": [datos_energeticos.get("condicion", "—")],
            "RER (kcal/día)": [f"{datos_energeticos.get('rer', 0):.1f}"],
            "MER base (kcal/día)": [f"{datos_energeticos.get('mer_base', 0):.1f}"],
            "MER final (kcal/día)": [f"{mer_final:.1f}"],
            "Alimento": [datos_alimento.get("alimento", "—")],
            "Gramos/día": [f"{datos_alimento.get('gramos', 0):.1f}"],
            "ME (kcal/100g)": [f"{datos_alimento.get('me', 0):.2f}"],
            "Energía aportada (kcal/día)": [f"{datos_alimento.get('aporte', 0):.1f}"],
            "Cobertura (%)": [f"{datos_alimento.get('cobertura', 0):.1f}"],
            "Gramos recomendados": [f"{datos_alimento.get('recomendados', 0):.0f}"],
            "Diagnóstico": [datos_energeticos.get("diagnostico", "—")],
            "Observaciones": [""],
        }
        df_visita = pd.DataFrame(visita_data)
        df_visita.to_excel(writer, sheet_name="VISITA ACTUAL", index=False)
        ws_visita = writer.sheets["VISITA ACTUAL"]
        for col_idx in range(len(df_visita.columns)):
            ws_visita.set_column(col_idx, col_idx, 22)
        for col_idx, col_name in enumerate(df_visita.columns):
            ws_visita.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 3: ANÁLISIS DEL ALIMENTO ─────────────────────────────────
        alimento_data = {
            "Parámetro": [
                "Alimento",
                "Proteína Bruta (%)",
                "Grasa (EE) (%)",
                "Cenizas (%)",
                "Humedad (%)",
                "Fibra Cruda (%)",
                "ENA (%)",
                "Materia Seca (%)",
                "Energía Bruta (kcal/100g)",
                "Digestibilidad (%)",
                "Energía Digestible (kcal/100g)",
                "Energía Metabolizable (kcal/100g)",
            ],
            "Valor": [
                datos_alimento.get("alimento", "—"),
                f"{datos_alimento.get('pb', 0):.2f}",
                f"{datos_alimento.get('ee', 0):.2f}",
                f"{datos_alimento.get('ash', 0):.2f}",
                f"{datos_alimento.get('humidity', 0):.2f}",
                f"{datos_alimento.get('fc', 0):.2f}",
                f"{datos_alimento.get('ena', 0):.2f}",
                f"{datos_alimento.get('ms', 0):.2f}",
                f"{datos_alimento.get('ge', 0):.2f}",
                f"{datos_alimento.get('de_pct', 0):.2f}",
                f"{datos_alimento.get('de', 0):.2f}",
                f"{datos_alimento.get('me', 0):.2f}",
            ],
        }
        df_alimento = pd.DataFrame(alimento_data)
        df_alimento.to_excel(writer, sheet_name="ANÁLISIS DEL ALIMENTO", index=False)
        ws_alimento = writer.sheets["ANÁLISIS DEL ALIMENTO"]
        ws_alimento.set_column(0, 0, 35)
        ws_alimento.set_column(1, 1, 20)
        for col_idx, col_name in enumerate(df_alimento.columns):
            ws_alimento.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 4: RECOMENDACIONES ────────────────────────────────────────
        if recomendaciones:
            rec_data = {
                "N°": list(range(1, len(recomendaciones) + 1)),
                "Recomendación": recomendaciones,
            }
            df_rec = pd.DataFrame(rec_data)
            df_rec.to_excel(writer, sheet_name="RECOMENDACIONES", index=False)
            ws_rec = writer.sheets["RECOMENDACIONES"]
            ws_rec.set_column(0, 0, 6)
            ws_rec.set_column(1, 1, 80)
            for col_idx, col_name in enumerate(df_rec.columns):
                ws_rec.write(0, col_idx, col_name, header_fmt)

    return output.getvalue()


# ---------------------------------------------------------------------------
# Ficha Maestra de Seguimiento Nutricional (5 hojas)
# ---------------------------------------------------------------------------

def _safe_float(value, default=0.0):
    """Convierte un valor a float de forma segura."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def generar_id_visita():
    """Genera UUID único para cada visita."""
    return str(uuid.uuid4())


def generar_uuid_paciente(nombre_especie):
    """Genera UUID determinístico para el paciente (mismo para todas sus visitas)."""
    key = str(nombre_especie).lower()
    # NAMESPACE_OID is appropriate for application-specific non-DNS identifiers
    return str(uuid.uuid5(uuid.NAMESPACE_OID, key))


def crear_visita_dict(mascota, datos_energeticos, datos_alimento,
                      mer_final, senior_applied, cob_pb, cob_ee,
                      recomendaciones=None, objetivo_nutricional=""):
    """
    Crea diccionario con 35 campos para 1 visita.
    Estructura: 1 diccionario = 1 fila en VISITAS_SEGUIMIENTO.

    Parámetros:
        mascota (dict)              : Datos de la mascota (nombre, especie).
        datos_energeticos (dict)    : Valores energéticos y diagnóstico.
        datos_alimento (dict)       : Datos del alimento evaluado.
        mer_final (float)           : MER final ajustado (kcal/día).
        senior_applied (bool)       : Si se aplicó ajuste senior.
        cob_pb (float|None)         : Cobertura proteína (%).
        cob_ee (float|None)         : Cobertura grasa (%).
        recomendaciones (list|None) : Lista de recomendaciones. Si None, lee de datos_energeticos.
        objetivo_nutricional (str)  : Objetivo nutricional; se infiere del BCS si está vacío.

    Retorna:
        dict: 35 campos para la fila de VISITAS_SEGUIMIENTO.
    """
    if recomendaciones is None:
        recomendaciones = datos_energeticos.get("recomendaciones", [])

    ahora = datetime.now()
    timestamp_iso = ahora.isoformat()
    fecha_iso = ahora.strftime("%Y-%m-%d")

    bcs = datos_energeticos.get("bcs", 5)
    if objetivo_nutricional == "":
        if bcs < 5:
            objetivo_nutricional = "Recuperar"
        elif bcs > 5:
            objetivo_nutricional = "Reducir"
        else:
            objetivo_nutricional = "Mantener"

    recomendaciones_str = (
        " | ".join(recomendaciones)
        if isinstance(recomendaciones, list)
        else str(recomendaciones)
    )

    cobertura = _safe_float(datos_alimento.get("cobertura", 0))
    decision = datos_alimento.get("decision", "Revisar")

    visita = {
        "id_visita": generar_id_visita(),
        "timestamp_registro": timestamp_iso,
        "fecha_visita": fecha_iso,
        "nombre_paciente": mascota.get("nombre", "—"),
        "especie": mascota.get("especie", "—").lower(),
        "edad": round(_safe_float(datos_energeticos.get("edad", 0)), 1),
        "peso_kg": round(_safe_float(datos_energeticos.get("peso", 0)), 1),
        "bcs": int(bcs),
        "estado_corporal": datos_energeticos.get("estado_corporal", "—"),
        "riesgo_nutricional": datos_energeticos.get("riesgo_nutricional", "—"),
        "etapa_vida": datos_energeticos.get("etapa", "adulto").lower(),
        "condicion_fisiologica": datos_energeticos.get("condicion", "—"),
        "ajuste_senior": bool(senior_applied),
        "objetivo_nutricional": objetivo_nutricional,
        "rer_kcal_dia": round(_safe_float(datos_energeticos.get("rer", 0)), 1),
        "mer_base_kcal_dia": round(_safe_float(datos_energeticos.get("mer_base", 0)), 1),
        "mer_final_kcal_dia": round(_safe_float(mer_final), 1),
        "alimento_evaluado": datos_alimento.get("alimento", "—"),
        "gramos_dia_evaluados": round(_safe_float(datos_alimento.get("gramos", 0)), 1),
        "me_kcal_100g": round(_safe_float(datos_alimento.get("me", 0)), 2),
        "energia_aportada_kcal_dia": round(_safe_float(datos_alimento.get("aporte", 0)), 1),
        "cobertura_energia_pct": round(cobertura, 1),
        "gramos_recomendados_dia": round(_safe_float(datos_alimento.get("recomendados", 0)), 0),
        "diferencia_gramos_dia": round(
            _safe_float(datos_alimento.get("recomendados", 0)) - _safe_float(datos_alimento.get("gramos", 0)), 1
        ),
        "cobertura_proteina_pct": round(_safe_float(cob_pb), 1) if cob_pb is not None else "",
        "cobertura_grasa_pct": round(_safe_float(cob_ee), 1) if cob_ee is not None else "",
        "resultado_nutricional": decision,
        "decision_clinica": f"Cobertura {cobertura:.1f}% - {decision}",
        "diagnostico_nutricional": datos_energeticos.get("diagnostico", "—"),
        "recomendaciones": recomendaciones_str,
        "observaciones": "",
        "profesional_responsable": "",
        "version_modelo": "v1.0",
        "fuente_dato": "app",
        "permitir_edicion": True,
    }
    return visita


def exportar_ficha_maestra_excel(mascota, datos_energeticos, datos_alimento,
                                  mer_final, senior_applied, recomendaciones,
                                  nutrientes_ref, cob_pb, cob_ee):
    """
    Genera archivo Excel con 6 hojas para seguimiento nutricional del paciente.

    Hojas:
        1. RESUMEN_ACTUAL          - Visualización humana (NO para lectura automática).
        2. VISITAS_SEGUIMIENTO     - Base histórica (1 fila = 1 visita, 35 columnas).
        3. ANALISIS_ALIMENTO       - Composición proximal (14 columnas).
        4. REQUERIMIENTOS_TECNICOS - Tabla referencia nutrientes (7 columnas).
        5. METADATOS               - Trazabilidad y versioning (12 pares clave-valor).
        6. CONFIG_APP              - Configuración de la app (4 pares clave-valor).

    Parámetros:
        mascota (dict)          : Datos de la mascota (nombre, especie).
        datos_energeticos (dict): Valores energéticos y diagnóstico.
        datos_alimento (dict)   : Datos del alimento evaluado.
        mer_final (float)       : MER final ajustado (kcal/día).
        senior_applied (bool)   : Si se aplicó ajuste senior.
        recomendaciones (list)  : Lista de recomendaciones.
        nutrientes_ref (dict)   : Referencia nutricional filtrada por especie
                                  (e.g. NUTRIENTES_REFERENCIA_PERRO).
        cob_pb (float|None)     : Cobertura proteína (%).
        cob_ee (float|None)     : Cobertura grasa (%).

    Retorna:
        bytes: Contenido del archivo Excel.
    """
    output = io.BytesIO()
    especie = mascota.get("especie", "perro").lower()
    etapa = datos_energeticos.get("etapa", "adulto").lower()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        header_fmt = workbook.add_format({
            "bg_color": "#2176FF",
            "font_color": "white",
            "bold": True,
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        })

        label_fmt = workbook.add_format({
            "bg_color": "#ECF0F3",
            "bold": True,
            "border": 1,
        })

        # ── HOJA 1: RESUMEN_ACTUAL ─────────────────────────────────────────
        recs_str = (
            " | ".join(recomendaciones)
            if isinstance(recomendaciones, list)
            else str(recomendaciones)
        )

        resumen_labels = [
            "DATOS DEL PACIENTE",
            "Nombre",
            "Especie",
            "Edad",
            "Peso actual",
            "BCS",
            "Estado corporal",
            "",
            "REQUERIMIENTOS ENERGÉTICOS",
            "RER",
            "MER base",
            "MER final ajustado",
            "",
            "ALIMENTO EVALUADO",
            "Nombre alimento",
            "Gramos/día",
            "ME (kcal/100g)",
            "Energía aportada",
            "Cobertura energética",
            "Gramos recomendados",
            "",
            "DIAGNÓSTICO",
            "Diagnóstico nutricional",
            "Recomendaciones",
        ]

        resumen_values = [
            "",
            mascota.get("nombre", "—"),
            mascota.get("especie", "—").capitalize(),
            f"{_safe_float(datos_energeticos.get('edad', 0)):.1f} años",
            f"{_safe_float(datos_energeticos.get('peso', 0)):.1f} kg",
            f"{datos_energeticos.get('bcs', 5)}/9",
            datos_energeticos.get("estado_corporal", "—"),
            "",
            "",
            f"{_safe_float(datos_energeticos.get('rer', 0)):.1f} kcal/día",
            f"{_safe_float(datos_energeticos.get('mer_base', 0)):.1f} kcal/día",
            f"{_safe_float(mer_final):.1f} kcal/día",
            "",
            "",
            datos_alimento.get("alimento", "—"),
            f"{_safe_float(datos_alimento.get('gramos', 0)):.1f} g",
            f"{_safe_float(datos_alimento.get('me', 0)):.2f}",
            f"{_safe_float(datos_alimento.get('aporte', 0)):.1f} kcal/día",
            f"{_safe_float(datos_alimento.get('cobertura', 0)):.1f}%",
            f"{_safe_float(datos_alimento.get('recomendados', 0)):.0f} g/día",
            "",
            "",
            datos_energeticos.get("diagnostico", "—"),
            recs_str,
        ]

        df_resumen = pd.DataFrame({"Parámetro": resumen_labels, "Valor": resumen_values})
        df_resumen.to_excel(writer, sheet_name="RESUMEN_ACTUAL", index=False)
        ws_resumen = writer.sheets["RESUMEN_ACTUAL"]
        ws_resumen.set_column(0, 0, 35)
        ws_resumen.set_column(1, 1, 50)
        for col_idx, col_name in enumerate(df_resumen.columns):
            ws_resumen.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 2: VISITAS_SEGUIMIENTO (35 columnas) ─────────────────────
        visita_actual = crear_visita_dict(
            mascota, datos_energeticos, datos_alimento,
            mer_final, senior_applied, cob_pb, cob_ee,
            recomendaciones=recomendaciones,
        )
        df_visitas = pd.DataFrame([visita_actual])
        df_visitas.to_excel(writer, sheet_name="VISITAS_SEGUIMIENTO", index=False)
        ws_visitas = writer.sheets["VISITAS_SEGUIMIENTO"]
        for col_idx in range(len(df_visitas.columns)):
            ws_visitas.set_column(col_idx, col_idx, 22)
        for col_idx, col_name in enumerate(df_visitas.columns):
            ws_visitas.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 3: ANALISIS_ALIMENTO (14 columnas + id_visita) ───────────
        def _or_empty(val):
            return val if val not in (None, 0, 0.0, "") else ""

        id_visita_actual = visita_actual["id_visita"]

        alimento_data = {
            "id_visita": [id_visita_actual],
            "alimento": [datos_alimento.get("alimento", "—")],
            "proteina_bruta_pct": [_or_empty(datos_alimento.get("pb"))],
            "grasa_ee_pct": [_or_empty(datos_alimento.get("ee"))],
            "cenizas_pct": [_or_empty(datos_alimento.get("ash"))],
            "humedad_pct": [_or_empty(datos_alimento.get("humidity"))],
            "fibra_cruda_pct": [_or_empty(datos_alimento.get("fc"))],
            "ena_pct": [_or_empty(datos_alimento.get("ena"))],
            "materia_seca_pct": [_or_empty(datos_alimento.get("ms"))],
            "energia_bruta_kcal_100g": [_or_empty(datos_alimento.get("ge"))],
            "energia_digestible_kcal_100g": [_or_empty(datos_alimento.get("de"))],
            "energia_metabolizable_kcal_100g": [_or_empty(datos_alimento.get("me"))],
            "precio_unitario": [datos_alimento.get("precio", "")],
            "distribuidor": [datos_alimento.get("distribuidor", "")],
        }
        df_alimento = pd.DataFrame(alimento_data)
        df_alimento.to_excel(writer, sheet_name="ANALISIS_ALIMENTO", index=False)
        ws_alimento = writer.sheets["ANALISIS_ALIMENTO"]
        ws_alimento.set_column(0, 0, 40)
        for col_idx in range(1, len(df_alimento.columns)):
            ws_alimento.set_column(col_idx, col_idx, 22)
        for col_idx, col_name in enumerate(df_alimento.columns):
            ws_alimento.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 4: REQUERIMIENTOS_TECNICOS (7 columnas) ──────────────────
        requisitos_rows = []
        try:
            nutrientes_dict = nutrientes_ref.get(etapa, {})
            for nutriente, valores in nutrientes_dict.items():
                requisitos_rows.append({
                    "nutriente": nutriente,
                    "unidad": valores.get("unit", ""),
                    "valor_minimo": valores.get("min", ""),
                    "valor_maximo": valores.get("max", ""),
                    "especie": especie,
                    "etapa_vida": etapa,
                    "fuente_modelo": "NRC 2006",
                })
        except Exception as exc:
            logging.warning(f"Error al extraer requerimientos técnicos para {especie}/{etapa}: {exc}")

        df_requisitos = pd.DataFrame(
            requisitos_rows,
            columns=["nutriente", "unidad", "valor_minimo", "valor_maximo",
                     "especie", "etapa_vida", "fuente_modelo"],
        )
        df_requisitos.to_excel(writer, sheet_name="REQUERIMIENTOS_TECNICOS", index=False)
        ws_req = writer.sheets["REQUERIMIENTOS_TECNICOS"]
        for col_idx in range(len(df_requisitos.columns)):
            ws_req.set_column(col_idx, col_idx, 20)
        for col_idx, col_name in enumerate(df_requisitos.columns):
            ws_req.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 5: METADATOS (12 pares clave-valor) ──────────────────────
        uuid_paciente = generar_uuid_paciente(
            f"{mascota.get('nombre', 'paciente')}_{especie}"
        )
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_hoy_date = datetime.now().strftime("%Y-%m-%d")

        metadatos_labels = [
            "METADATOS DEL ARCHIVO",
            "id_paciente",
            "nombre_paciente",
            "especie",
            "fecha_creacion_archivo",
            "fecha_ultima_actualizacion",
            "ultima_visita_registrada",
            "numero_visitas",
            "version_app",
            "version_modelo_energia",
            "fuente_modelo_energia",
            "ultima_modificacion_por",
            "observacion_general",
        ]
        metadatos_values = [
            "",
            uuid_paciente,
            mascota.get("nombre", "—"),
            especie,
            fecha_hoy,
            fecha_hoy,
            fecha_hoy_date,
            1,
            "1.0.0",
            "NRC v1",
            "National Research Council",
            "Sistema UYWA",
            "",
        ]

        df_metadatos = pd.DataFrame({"Clave": metadatos_labels, "Valor": metadatos_values})
        df_metadatos.to_excel(writer, sheet_name="METADATOS", index=False)
        ws_meta = writer.sheets["METADATOS"]
        ws_meta.set_column(0, 0, 35)
        ws_meta.set_column(1, 1, 50)
        for col_idx, col_name in enumerate(df_metadatos.columns):
            ws_meta.write(0, col_idx, col_name, header_fmt)

        # ── HOJA 6: CONFIG_APP ─────────────────────────────────────────────
        config_labels = [
            "CONFIGURACIÓN DE LA APP",
            "usar_ajuste_senior",
            "usar_ajuste_bcs",
            "umbral_cobertura_minima",
            "umbral_cobertura_maxima",
        ]
        config_values = [
            "",
            True,
            True,
            90,
            110,
        ]

        df_config = pd.DataFrame({"Clave": config_labels, "Valor": config_values})
        df_config.to_excel(writer, sheet_name="CONFIG_APP", index=False)
        ws_config = writer.sheets["CONFIG_APP"]
        ws_config.set_column(0, 0, 35)
        ws_config.set_column(1, 1, 20)
        for col_idx, col_name in enumerate(df_config.columns):
            ws_config.write(0, col_idx, col_name, header_fmt)

    return output.getvalue()


# ---------------------------------------------------------------------------
# Exportación a HTML
# ---------------------------------------------------------------------------

def exportar_a_html(mascota, datos_energeticos, datos_alimento,
                    mer_final, diagnostico, recomendaciones):
    """
    Genera un HTML descargable profesional con el informe nutricional completo.

    Parámetros:
        mascota (dict)            : Datos de la mascota.
        datos_energeticos (dict)  : Valores energéticos y diagnóstico.
        datos_alimento (dict)     : Datos del alimento evaluado.
        mer_final (float)         : MER final ajustado (kcal/día).
        diagnostico (str)         : Párrafo de diagnóstico nutricional.
        recomendaciones (list)    : Lista de recomendaciones de texto.

    Retorna:
        str: Contenido HTML del informe.
    """
    nombre = mascota.get("nombre", "—")
    especie = mascota.get("especie", "—").capitalize()
    edad = datos_energeticos.get("edad", 0)
    peso = datos_energeticos.get("peso", 0)
    bcs = datos_energeticos.get("bcs", 5)
    estado_corporal = datos_energeticos.get("estado_corporal", "—")
    condicion = datos_energeticos.get("condicion", "—")
    rer = datos_energeticos.get("rer", 0)
    mer_base = datos_energeticos.get("mer_base", 0)
    riesgo = datos_energeticos.get("riesgo_nutricional", "—")

    alimento = datos_alimento.get("alimento", "—")
    me = datos_alimento.get("me", 0)
    gramos = datos_alimento.get("gramos", 0)
    aporte = datos_alimento.get("aporte", 0)
    cobertura = datos_alimento.get("cobertura", 0)
    recomendados = datos_alimento.get("recomendados", 0)
    rango_min = datos_alimento.get("rango_min", 0)
    rango_max = datos_alimento.get("rango_max", 0)
    decision = datos_alimento.get("decision", "—")
    interpretacion = datos_alimento.get("interpretacion", "—")

    recs_html = "\n".join(f"            <li>{rec}</li>" for rec in recomendaciones)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>UYWA - Informe Nutricional</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #2176FF;
            padding-bottom: 20px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{ color: #2176FF; font-size: 28px; margin-bottom: 5px; }}
        .header p {{ color: #7f8c8d; font-size: 12px; }}
        .section {{ margin-bottom: 30px; page-break-inside: avoid; }}
        .section-title {{
            background: #ecf0f3;
            color: #2176FF;
            padding: 12px 16px;
            font-size: 16px;
            font-weight: 700;
            border-left: 4px solid #2176FF;
            margin-bottom: 15px;
        }}
        .data-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #ecf0f3;
        }}
        .data-row:last-child {{ border-bottom: none; }}
        .data-label {{ font-weight: 600; color: #2c3e50; }}
        .data-value {{ color: #34495e; }}
        .highlight {{
            background: #ecf0f3;
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .diagnostic-box {{
            background: #f0f8ff;
            border-left: 4px solid #52B788;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .recommendations {{ list-style: none; margin: 15px 0; }}
        .recommendations li {{
            padding: 8px 0 8px 25px;
            position: relative;
            border-bottom: 1px solid #f0f0f0;
        }}
        .recommendations li:last-child {{ border-bottom: none; }}
        .recommendations li:before {{
            content: "\\2713";
            position: absolute;
            left: 0;
            color: #52B788;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f3;
            font-size: 11px;
            color: #7f8c8d;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>UYWA Nutrition</h1>
        <p>Informe Nutricional Personalizado</p>
    </div>

    <div class="section">
        <div class="section-title">&#128203; RESUMEN DEL PACIENTE</div>
        <div class="data-row">
            <span class="data-label">Nombre:</span>
            <span class="data-value">{nombre}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Especie:</span>
            <span class="data-value">{especie}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Edad:</span>
            <span class="data-value">{edad:.1f} a&#241;os</span>
        </div>
        <div class="data-row">
            <span class="data-label">Peso actual:</span>
            <span class="data-value">{peso:.1f} kg</span>
        </div>
        <div class="data-row">
            <span class="data-label">BCS:</span>
            <span class="data-value">{bcs}/9</span>
        </div>
        <div class="data-row">
            <span class="data-label">Estado corporal:</span>
            <span class="data-value">{estado_corporal}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Condici&#243;n fisiol&#243;gica:</span>
            <span class="data-value">{condicion}</span>
        </div>
        <div class="data-row">
            <span class="data-label">Riesgo nutricional:</span>
            <span class="data-value">{riesgo}</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">&#129514; DIAGN&#211;STICO NUTRICIONAL</div>
        <div class="diagnostic-box">{diagnostico}</div>
    </div>

    <div class="section">
        <div class="section-title">&#9889; REQUERIMIENTOS ENERG&#201;TICOS</div>
        <div class="data-row">
            <span class="data-label">RER:</span>
            <span class="data-value">{rer:.1f} kcal/d&#237;a</span>
        </div>
        <div class="data-row">
            <span class="data-label">MER base:</span>
            <span class="data-value">{mer_base:.1f} kcal/d&#237;a</span>
        </div>
        <div class="data-row" style="background:#f0f8ff;font-weight:bold;">
            <span class="data-label">MER final ajustado:</span>
            <span class="data-value">{mer_final:.1f} kcal/d&#237;a</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">&#127869;&#65039; AN&#193;LISIS DEL ALIMENTO</div>
        <div class="data-row">
            <span class="data-label">Alimento:</span>
            <span class="data-value">{alimento}</span>
        </div>
        <div class="data-row">
            <span class="data-label">ME:</span>
            <span class="data-value">{me:.2f} kcal/100g</span>
        </div>
        <div class="data-row">
            <span class="data-label">Gramos diarios:</span>
            <span class="data-value">{gramos:.0f} g/d&#237;a</span>
        </div>
        <div class="data-row">
            <span class="data-label">Energ&#237;a aportada:</span>
            <span class="data-value">{aporte:.1f} kcal/d&#237;a</span>
        </div>
        <div class="data-row">
            <span class="data-label">Cobertura energ&#233;tica:</span>
            <span class="data-value">{cobertura:.1f}%</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">&#9989; DECISI&#211;N NUTRICIONAL</div>
        <div class="highlight">
            <strong>{decision}</strong>
            <p style="margin-top:8px;font-size:14px;">{interpretacion}</p>
        </div>
    </div>

    <div class="section">
        <div class="section-title">&#128202; CANTIDAD RECOMENDADA</div>
        <div class="data-row">
            <span class="data-label">Gramos recomendados:</span>
            <span class="data-value">{recomendados:.0f} g/d&#237;a</span>
        </div>
        <div class="data-row">
            <span class="data-label">Rango aceptable (&#177;10%):</span>
            <span class="data-value">{rango_min:.0f} &#8211; {rango_max:.0f} g/d&#237;a</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">&#128161; RECOMENDACIONES</div>
        <ul class="recommendations">
{recs_html}
        </ul>
    </div>

    <div class="footer">
        <p>Este informe ha sido generado por UYWA Nutrition.</p>
        <p>Para m&#225;s informaci&#243;n: uywasas@gmail.com | &copy; 2026 Derechos reservados</p>
    </div>
</div>
</body>
</html>"""
    return html
