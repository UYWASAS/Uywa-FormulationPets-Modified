"""Herramientas de seguimiento nutricional histórico - Pestaña 4 UYWA."""

import io
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime


# ---------------------------------------------------------------------------
# Carga y validación del archivo Excel
# ---------------------------------------------------------------------------

def leer_ficha_maestra(archivo_xlsx):
    """
    Lee archivo Excel y valida estructura.

    Parámetros:
        archivo_xlsx: archivo subido por usuario

    Retorna:
        tuple: (df_visitas, metadatos, es_valido, mensaje_error)
    """
    try:
        df_visitas = pd.read_excel(archivo_xlsx, sheet_name="VISITAS_SEGUIMIENTO")

        columnas_requeridas = [
            "id_visita", "fecha_visita", "nombre_paciente", "especie",
            "edad", "peso_kg", "bcs", "rer_kcal_dia", "mer_final_kcal_dia",
            "alimento_evaluado", "energia_aportada_kcal_dia", "cobertura_energia_pct"
        ]

        columnas_faltantes = [col for col in columnas_requeridas if col not in df_visitas.columns]
        if columnas_faltantes:
            return None, None, False, f"Columnas faltantes: {columnas_faltantes}"

        df_metadatos = pd.read_excel(archivo_xlsx, sheet_name="METADATOS")
        metadatos = dict(zip(df_metadatos["Clave"], df_metadatos["Valor"]))

        df_visitas = df_visitas.sort_values("fecha_visita", ascending=False).reset_index(drop=True)

        return df_visitas, metadatos, True, "Archivo válido"

    except KeyError as e:
        return None, None, False, f"Hoja no encontrada: {str(e)}"
    except Exception as e:
        return None, None, False, f"Error al leer archivo: {str(e)}"


def validar_estructura_excel(df_visitas):
    """
    Valida que el DataFrame tenga estructura correcta.

    Retorna:
        bool: True si estructura válida
    """
    if df_visitas is None or len(df_visitas) == 0:
        return False

    tipos_esperados = {
        "fecha_visita": ["datetime64", "object"],
        "peso_kg": ["float64", "int64"],
        "bcs": ["int64", "float64"],
        "cobertura_energia_pct": ["float64", "int64"]
    }

    for col, tipos in tipos_esperados.items():
        if col not in df_visitas.columns:
            return False
        if str(df_visitas[col].dtype) not in tipos:
            return False

    return True


def migrar_visita_actual_legacy(archivo_xlsx):
    """
    Si existe hoja "VISITA ACTUAL" (legacy), migra a VISITAS_SEGUIMIENTO.
    """
    try:
        df_visita_actual = pd.read_excel(archivo_xlsx, sheet_name="VISITA ACTUAL")
        return df_visita_actual
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Cálculo de deltas
# ---------------------------------------------------------------------------

def calcular_deltas(df_visitas):
    """
    Compara última vs penúltima visita.

    Retorna:
        dict: deltas y tendencias
    """
    if len(df_visitas) < 2:
        return {
            "peso_delta": 0,
            "peso_delta_pct": 0,
            "bcs_delta": 0,
            "mer_delta": 0,
            "mer_delta_pct": 0,
            "cobertura_delta": 0,
            "tendencia": "sin_datos"
        }

    ultima = df_visitas.iloc[0]
    penultima = df_visitas.iloc[1]

    peso_delta = float(ultima["peso_kg"]) - float(penultima["peso_kg"])
    peso_delta_pct = (peso_delta / float(penultima["peso_kg"]) * 100) if float(penultima["peso_kg"]) > 0 else 0

    bcs_delta = int(ultima["bcs"]) - int(penultima["bcs"])

    mer_delta = float(ultima["mer_final_kcal_dia"]) - float(penultima["mer_final_kcal_dia"])
    mer_delta_pct = (mer_delta / float(penultima["mer_final_kcal_dia"]) * 100) if float(penultima["mer_final_kcal_dia"]) > 0 else 0

    cobertura_delta = float(ultima["cobertura_energia_pct"]) - float(penultima["cobertura_energia_pct"])

    mejoras = 0
    empeoras = 0

    if -0.5 <= peso_delta <= 0.5:
        mejoras += 1
    elif peso_delta < 0 and float(penultima["bcs"]) > 5:
        mejoras += 1
    elif peso_delta > 0 and float(penultima["bcs"]) < 5:
        mejoras += 1
    else:
        empeoras += 1

    if bcs_delta == 0:
        mejoras += 1
    elif (bcs_delta > 0 and float(penultima["bcs"]) < 5) or (bcs_delta < 0 and float(penultima["bcs"]) > 5):
        mejoras += 1
    else:
        empeoras += 1

    if 90 <= float(ultima["cobertura_energia_pct"]) <= 110:
        if 90 <= float(penultima["cobertura_energia_pct"]) <= 110:
            mejoras += 1
        else:
            mejoras += 1
    else:
        if 90 <= float(penultima["cobertura_energia_pct"]) <= 110:
            empeoras += 1
        else:
            mejoras += 1

    if mejoras > empeoras:
        tendencia = "mejora"
    elif empeoras > mejoras:
        tendencia = "empeora"
    else:
        tendencia = "estable"

    return {
        "peso_delta": round(peso_delta, 1),
        "peso_delta_pct": round(peso_delta_pct, 1),
        "bcs_delta": bcs_delta,
        "mer_delta": round(mer_delta, 1),
        "mer_delta_pct": round(mer_delta_pct, 1),
        "cobertura_delta": round(cobertura_delta, 1),
        "tendencia": tendencia
    }


def render_resumen_rapido(deltas):
    """
    Renderiza cards con deltas.
    """
    col1, col2, col3, col4 = st.columns(4)

    tendencia_icon = {
        "mejora": "🟢",
        "estable": "🟡",
        "empeora": "🔴",
        "sin_datos": "⚪"
    }

    icon = tendencia_icon.get(deltas["tendencia"], "⚪")

    with col1:
        st.metric(
            "Peso (kg)",
            f"{deltas['peso_delta']:+.1f}",
            f"{deltas['peso_delta_pct']:+.1f}%"
        )

    with col2:
        st.metric(
            "BCS",
            f"{deltas['bcs_delta']:+d}",
            "Cambio"
        )

    with col3:
        st.metric(
            "MER (kcal/día)",
            f"{deltas['mer_delta']:+.0f}",
            f"{deltas['mer_delta_pct']:+.1f}%"
        )

    with col4:
        st.metric(
            "Cobertura (%)",
            f"{deltas['cobertura_delta']:+.1f}%",
            f"{icon} {deltas['tendencia'].capitalize()}"
        )


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def crear_graficos_seguimiento(df_visitas):
    """
    Crea 4 gráficos interactivos del histórico.
    """
    df_plot = df_visitas.sort_values("fecha_visita", ascending=True).reset_index(drop=True)

    # 1. PESO VS TIEMPO
    fig_peso = go.Figure()
    fig_peso.add_trace(go.Scatter(
        x=df_plot["fecha_visita"],
        y=df_plot["peso_kg"],
        mode="lines+markers",
        name="Peso (kg)",
        line=dict(color="#2176FF", width=3),
        marker=dict(size=8)
    ))
    fig_peso.update_layout(
        title="📊 Evolución de Peso",
        xaxis_title="Fecha",
        yaxis_title="Peso (kg)",
        hovermode="x unified",
        height=400
    )

    # 2. BCS VS TIEMPO
    fig_bcs = go.Figure()
    fig_bcs.add_trace(go.Scatter(
        x=df_plot["fecha_visita"],
        y=df_plot["bcs"],
        mode="lines+markers",
        name="BCS",
        line=dict(color="#52B788", width=3),
        marker=dict(size=8)
    ))
    fig_bcs.add_hline(y=5, line_dash="dash", line_color="gray", annotation_text="Ideal (5/9)")
    fig_bcs.update_layout(
        title="📈 Evolución de BCS",
        xaxis_title="Fecha",
        yaxis_title="BCS (1-9)",
        yaxis=dict(range=[1, 9]),
        hovermode="x unified",
        height=400
    )

    # 3. MER VS ENERGÍA APORTADA
    fig_energia = go.Figure()
    fig_energia.add_trace(go.Scatter(
        x=df_plot["fecha_visita"],
        y=df_plot["mer_final_kcal_dia"],
        mode="lines+markers",
        name="MER requerido",
        line=dict(color="#FF6B6B", width=3),
        marker=dict(size=8)
    ))
    fig_energia.add_trace(go.Scatter(
        x=df_plot["fecha_visita"],
        y=df_plot["energia_aportada_kcal_dia"],
        mode="lines+markers",
        name="Energía aportada",
        line=dict(color="#FFB703", width=3),
        marker=dict(size=8)
    ))
    fig_energia.update_layout(
        title="⚡ MER vs Energía Aportada",
        xaxis_title="Fecha",
        yaxis_title="kcal/día",
        hovermode="x unified",
        height=400
    )

    # 4. COBERTURA ENERGÉTICA
    fig_cobertura = go.Figure()

    colores = []
    for cob in df_plot["cobertura_energia_pct"]:
        if cob < 90:
            colores.append("#2176FF")
        elif cob <= 110:
            colores.append("#52B788")
        elif cob <= 130:
            colores.append("#FFB703")
        else:
            colores.append("#F4845F")

    fig_cobertura.add_trace(go.Bar(
        x=df_plot["fecha_visita"],
        y=df_plot["cobertura_energia_pct"],
        marker=dict(color=colores),
        name="Cobertura (%)",
        text=df_plot["cobertura_energia_pct"].round(1),
        textposition="auto"
    ))
    fig_cobertura.add_hline(y=90, line_dash="dash", line_color="blue", annotation_text="Min (90%)")
    fig_cobertura.add_hline(y=110, line_dash="dash", line_color="green", annotation_text="Max (110%)")
    fig_cobertura.update_layout(
        title="🎯 Cobertura Energética",
        xaxis_title="Fecha",
        yaxis_title="Cobertura (%)",
        hovermode="x unified",
        height=400,
        showlegend=False
    )

    return fig_peso, fig_bcs, fig_energia, fig_cobertura


# ---------------------------------------------------------------------------
# Interpretación automática
# ---------------------------------------------------------------------------

def generar_interpretacion_evolucion(df_visitas, deltas):
    """
    Genera texto interpretativo de la evolución.
    """
    if len(df_visitas) < 2:
        return "Sin histórico disponible para análisis de evolución."

    ultima = df_visitas.iloc[0]
    penultima = df_visitas.iloc[1]

    texto = f"**Análisis desde {penultima['fecha_visita']} a {ultima['fecha_visita']}:**\n\n"

    if deltas["peso_delta"] < -0.5:
        texto += f"✅ Pérdida de peso: {abs(deltas['peso_delta']):.1f} kg ({abs(deltas['peso_delta_pct']):.1f}%). "
        if ultima["bcs"] > 5:
            texto += "Positivo para reducir sobrepeso.\n"
        else:
            texto += "Revisar si es intencional.\n"
    elif deltas["peso_delta"] > 0.5:
        texto += f"📈 Ganancia de peso: {deltas['peso_delta']:.1f} kg ({deltas['peso_delta_pct']:.1f}%). "
        if ultima["bcs"] < 5:
            texto += "Positivo para recuperar peso.\n"
        else:
            texto += "Revisar si es excesiva.\n"
    else:
        texto += "➡️ Peso estable.\n"

    if deltas["bcs_delta"] > 0:
        texto += f"📈 BCS aumentó {deltas['bcs_delta']} punto(s). "
        if ultima["bcs"] <= 5:
            texto += "En rango ideal.\n"
        else:
            texto += "Considerar reducción.\n"
    elif deltas["bcs_delta"] < 0:
        texto += f"📉 BCS disminuyó {abs(deltas['bcs_delta'])} punto(s). "
        if ultima["bcs"] >= 5:
            texto += "En rango ideal.\n"
        else:
            texto += "Considerar aumento.\n"
    else:
        texto += "➡️ BCS sin cambios.\n"

    cobertura_ultima = float(ultima["cobertura_energia_pct"])
    if 90 <= cobertura_ultima <= 110:
        texto += f"✅ Cobertura energética adecuada ({cobertura_ultima:.1f}%).\n"
    elif cobertura_ultima < 90:
        texto += f"⚠️ Cobertura baja ({cobertura_ultima:.1f}%). Aumentar ración.\n"
    else:
        texto += f"⚠️ Cobertura alta ({cobertura_ultima:.1f}%). Reducir ración.\n"

    texto += f"\n**Tendencia general:** {deltas['tendencia'].upper()}"

    return texto


# ---------------------------------------------------------------------------
# Decisión clínica
# ---------------------------------------------------------------------------

def generar_decision_clinica(df_visitas, deltas):
    """
    Genera recomendación clínica automática.
    """
    if len(df_visitas) == 0:
        return "—", "Sin datos"

    ultima = df_visitas.iloc[0]
    cobertura = float(ultima["cobertura_energia_pct"])
    peso_delta = deltas["peso_delta"]
    bcs = int(ultima["bcs"])

    decision = ""
    justificacion = ""

    if 90 <= cobertura <= 110 and bcs == 5 and len(df_visitas) > 1:
        if abs(peso_delta) < 0.5:
            decision = "✅ MANTENER RACIÓN"
            justificacion = "Cobertura adecuada, peso estable, BCS ideal."
        else:
            decision = "✅ MANTENER RACIÓN"
            justificacion = "Cobertura adecuada. Monitorear peso."

    elif cobertura < 90:
        if bcs < 5 or peso_delta < 0:
            decision = "📈 AUMENTAR RACIÓN"
            justificacion = f"Cobertura baja ({cobertura:.1f}%). Aumentar gradualmente."
        else:
            decision = "⚠️ REVISAR ALIMENTO"
            justificacion = "Cobertura baja pero peso/BCS adecuados. Considerar alternativa."

    elif cobertura > 110:
        if bcs > 5 or peso_delta > 1:
            decision = "📉 REDUCIR RACIÓN"
            justificacion = f"Cobertura excesiva ({cobertura:.1f}%). Reducir gradualmente."
        else:
            decision = "⚠️ REVISAR ALIMENTO"
            justificacion = "Cobertura alta pero peso/BCS adecuados. Considerar alternativa."

    if bcs < 5 and len(df_visitas) > 1:
        if deltas["bcs_delta"] <= 0:
            decision = "📈 AUMENTAR RACIÓN"
            justificacion = "BCS bajo sin mejora. Aumentar aporte energético."

    elif bcs > 5 and len(df_visitas) > 1:
        if deltas["bcs_delta"] >= 0:
            decision = "📉 REDUCIR RACIÓN"
            justificacion = "BCS alto sin mejoría. Reducir aporte energético."

    if not decision:
        decision = "⚠️ REVISAR DATOS"
        justificacion = "Datos insuficientes para emitir recomendación."

    return decision, justificacion


# ---------------------------------------------------------------------------
# Tabla histórica
# ---------------------------------------------------------------------------

def render_tabla_historica(df_visitas):
    """
    Renderiza tabla limpia con columnas clave.
    """
    columnas_mostrar = [
        "fecha_visita",
        "peso_kg",
        "bcs",
        "estado_corporal",
        "rer_kcal_dia",
        "mer_final_kcal_dia",
        "alimento_evaluado",
        "gramos_dia_evaluados",
        "energia_aportada_kcal_dia",
        "cobertura_energia_pct"
    ]

    columnas_disponibles = [c for c in columnas_mostrar if c in df_visitas.columns]
    df_display = df_visitas[columnas_disponibles].copy()

    rename_map = {
        "fecha_visita": "Fecha",
        "peso_kg": "Peso (kg)",
        "bcs": "BCS",
        "estado_corporal": "Estado",
        "rer_kcal_dia": "RER (kcal)",
        "mer_final_kcal_dia": "MER (kcal)",
        "alimento_evaluado": "Alimento",
        "gramos_dia_evaluados": "Gramos/día",
        "energia_aportada_kcal_dia": "Energía (kcal)",
        "cobertura_energia_pct": "Cobertura (%)"
    }
    df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns}, inplace=True)

    st.dataframe(df_display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Agregar visita
# ---------------------------------------------------------------------------

def agregar_visita_a_historico(df_visitas, nueva_visita):
    """
    Agrega nueva visita validando duplicados.
    """
    fecha_nueva = nueva_visita["fecha_visita"]

    existe_duplicado = any(
        (df_visitas["fecha_visita"].astype(str) == str(fecha_nueva)) &
        (df_visitas["nombre_paciente"] == nueva_visita["nombre_paciente"])
    )

    if existe_duplicado:
        return False, "Ya existe visita registrada para esta fecha."

    df_actualizado = pd.concat([df_visitas, pd.DataFrame([nueva_visita])], ignore_index=True)
    df_actualizado = df_actualizado.sort_values("fecha_visita", ascending=False).reset_index(drop=True)

    return True, df_actualizado


# ---------------------------------------------------------------------------
# Exportación actualizada
# ---------------------------------------------------------------------------

def exportar_ficha_actualizada(df_visitas, df_analisis, df_requisitos, metadatos):
    """
    Exporta Excel actualizado manteniendo estructura.
    """
    output = io.BytesIO()

    metadatos = dict(metadatos)
    metadatos["fecha_ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadatos["numero_visitas"] = len(df_visitas)
    metadatos["ultima_visita_registrada"] = str(df_visitas.iloc[0]["fecha_visita"]) if len(df_visitas) > 0 else ""

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        header_fmt = workbook.add_format({
            "bg_color": "#2176FF",
            "font_color": "white",
            "bold": True,
            "border": 1
        })

        df_visitas.to_excel(writer, sheet_name="VISITAS_SEGUIMIENTO", index=False)
        ws_visitas = writer.sheets["VISITAS_SEGUIMIENTO"]
        for col_idx in range(len(df_visitas.columns)):
            ws_visitas.set_column(col_idx, col_idx, 18)
            ws_visitas.write(0, col_idx, df_visitas.columns[col_idx], header_fmt)

        df_analisis.to_excel(writer, sheet_name="ANALISIS_ALIMENTO", index=False)
        ws_analisis = writer.sheets["ANALISIS_ALIMENTO"]
        for col_idx in range(len(df_analisis.columns)):
            ws_analisis.set_column(col_idx, col_idx, 18)
            ws_analisis.write(0, col_idx, df_analisis.columns[col_idx], header_fmt)

        df_requisitos.to_excel(writer, sheet_name="REQUERIMIENTOS_TECNICOS", index=False)
        ws_req = writer.sheets["REQUERIMIENTOS_TECNICOS"]
        for col_idx in range(len(df_requisitos.columns)):
            ws_req.set_column(col_idx, col_idx, 20)
            ws_req.write(0, col_idx, df_requisitos.columns[col_idx], header_fmt)

        df_meta = pd.DataFrame(list(metadatos.items()), columns=["Clave", "Valor"])
        df_meta.to_excel(writer, sheet_name="METADATOS", index=False)
        ws_meta = writer.sheets["METADATOS"]
        ws_meta.set_column(0, 0, 35)
        ws_meta.set_column(1, 1, 50)
        for col_idx in range(len(df_meta.columns)):
            ws_meta.write(0, col_idx, df_meta.columns[col_idx], header_fmt)

    return output.getvalue()
