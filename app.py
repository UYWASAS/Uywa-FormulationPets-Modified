# ======================== APLICACIÓN PRINCIPAL: PET FORMULATION COMPANION ========================

import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
from io import BytesIO

# Importar módulos personalizados
from pet_profile_tools import (
    calcular_mer, 
    calcular_requerimientos_nutrientes,
    generar_perfil_mascota,
    validar_datos_basicos,
)
from food_database import get_food_names, get_food_data
from food_analysis import show_food_analysis
from export_tools import exportar_ficha_maestra, generar_informe_pdf
from tracking_tools import (
    leer_ficha_maestra,
    calcular_deltas,
    render_resumen_rapido,
    crear_graficos_seguimiento,
    generar_interpretacion_evolucion,
    generar_decision_clinica,
    render_tabla_historica,
    agregar_visita_a_historico,
    exportar_ficha_actualizada,
)

# ======================== CONFIGURACIÓN DE STREAMLIT ========================

st.set_page_config(
    page_title="Pet Formulation Companion",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session_state
if "especie_mascota" not in st.session_state:
    st.session_state["especie_mascota"] = ""
if "energia_actual" not in st.session_state:
    st.session_state["energia_actual"] = None
if "req_pb_g" not in st.session_state:
    st.session_state["req_pb_g"] = None
if "req_ee_g" not in st.session_state:
    st.session_state["req_ee_g"] = None
if "alimento_seleccionado" not in st.session_state:
    st.session_state["alimento_seleccionado"] = None
if "df_tracking" not in st.session_state:
    st.session_state["df_tracking"] = None
if "metadatos_tracking" not in st.session_state:
    st.session_state["metadatos_tracking"] = {}

# ======================== ESTILOS GLOBALES ========================

st.markdown("""
    <style>
    /* Fuentes y estilos generales */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    
    body {
        font-family: 'Montserrat', sans-serif;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #7a8998;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] button {
        font-weight: 600;
        font-size: 1.05rem;
    }
    
    /* Cards y containers */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ======================== ENCABEZADO PRINCIPAL ========================

st.markdown(
    """
    <div class="main-title">🐾 Pet Formulation Companion</div>
    <div class="subtitle">Análisis Nutricional Personalizado para Mascotas</div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ======================== CREAR TABS ========================

tabs = st.tabs([
    "🐾 Perfil de Mascota",
    "📊 Análisis de Alimentos",
    "📤 Resumen y Exportar",
    "📈 Seguimiento del Paciente"
])

# ======================== TAB 1: PERFIL DE MASCOTA ========================

with tabs[0]:
    st.header("🐾 Perfil de la Mascota")
    st.markdown(
        "Ingresa información básica sobre tu mascota para calcular sus requerimientos nutricionales."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        especie = st.selectbox(
            "Especie",
            ["Selecciona...", "Perro", "Gato"],
            key="especie_input"
        )
        
        if especie != "Selecciona...":
            st.session_state["especie_mascota"] = especie.lower()
        else:
            st.session_state["especie_mascota"] = ""
        
        nombre_mascota = st.text_input("Nombre de la mascota", key="nombre_input")
        edad_anos = st.number_input("Edad (años)", min_value=0.1, max_value=30.0, value=3.0, step=0.1, key="edad_input")
        
    with col2:
        peso_actual_kg = st.number_input("Peso actual (kg)", min_value=0.5, max_value=100.0, value=15.0, step=0.1, key="peso_input")
        actividad = st.selectbox(
            "Nivel de actividad",
            ["Sedentario", "Moderado", "Activo", "Muy activo"],
            key="actividad_input"
        )
        estado_reproductivo = st.selectbox(
            "Estado reproductivo",
            ["Intacto", "Castrado/Esterilizado"],
            key="reproductor_input"
        )
    
    st.markdown("---")
    
    # Botón para calcular
    if st.button("🧮 Calcular Requerimientos", key="calc_button"):
        # Validar datos
        if not nombre_mascota:
            st.error("Por favor ingresa el nombre de la mascota.")
        elif especie == "Selecciona...":
            st.error("Por favor selecciona una especie.")
        else:
            # Mapeo de factor de actividad
            activity_map = {
                "Sedentario": 1.2,
                "Moderado": 1.5,
                "Activo": 1.8,
                "Muy activo": 2.0
            }
            
            factor_actividad = activity_map[actividad]
            factor_reproductivo = 1.0 if estado_reproductivo == "Intacto" else 1.1
            
            # Calcular MER
            mer = calcular_mer(
                peso_kg=peso_actual_kg,
                edad_anos=edad_anos,
                factor_actividad=factor_actividad,
                factor_reproductivo=factor_reproductivo,
                especie=especie.lower()
            )
            
            # Guardar en session_state
            st.session_state["energia_actual"] = mer
            
            # Calcular requerimientos de nutrientes
            reqs = calcular_requerimientos_nutrientes(
                especie=especie.lower(),
                peso_kg=peso_actual_kg,
                edad_anos=edad_anos,
                actividad=actividad
            )
            
            st.session_state["req_pb_g"] = reqs.get("pb_g", None)
            st.session_state["req_ee_g"] = reqs.get("ee_g", None)
            
            # Mostrar resultados
            st.success("✅ Cálculo completado")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 MER", f"{mer:.0f} kcal/día")
            with col2:
                st.metric("🥩 Proteína", f"{reqs.get('pb_g', 0):.1f} g/día")
            with col3:
                st.metric("🧈 Grasa", f"{reqs.get('ee_g', 0):.1f} g/día")
            
            # Generar perfil
            perfil = generar_perfil_mascota(
                nombre=nombre_mascota,
                especie=especie.lower(),
                edad=edad_anos,
                peso=peso_actual_kg,
                actividad=actividad,
                estado_reproductivo=estado_reproductivo,
                mer=mer,
                requerimientos=reqs
            )
            
            st.session_state["perfil_actual"] = perfil
            
            st.info(f"📝 Perfil guardado: {nombre_mascota} ({especie}, {peso_actual_kg} kg)")

# ======================== TAB 2: ANÁLISIS DE ALIMENTOS ========================

with tabs[1]:
    show_food_analysis()

# ======================== TAB 3: RESUMEN Y EXPORTAR ========================

with tabs[2]:
    st.header("📤 Resumen y Exportar")
    st.markdown(
        "Descarga un resumen completo del análisis nutricional en formato Excel."
    )
    
    if st.session_state.get("perfil_actual") and st.session_state.get("alimento_seleccionado"):
        st.success("✅ Datos listos para exportar")
        
        perfil = st.session_state["perfil_actual"]
        alimento = st.session_state["alimento_seleccionado"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Descargar Ficha Maestra (Excel)", key="export_excel_btn"):
                try:
                    excel_bytes = exportar_ficha_maestra(perfil, alimento)
                    st.download_button(
                        label="⬇️ Descargar Excel",
                        data=excel_bytes,
                        file_name=f"ficha_{perfil['nombre']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    st.success("✅ Excel generado correctamente")
                except Exception as e:
                    st.error(f"Error al generar Excel: {str(e)}")
        
        with col2:
            if st.button("📄 Generar PDF", key="export_pdf_btn"):
                try:
                    pdf_bytes = generar_informe_pdf(perfil, alimento)
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"informe_{perfil['nombre']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                    )
                    st.success("✅ PDF generado correctamente")
                except Exception as e:
                    st.error(f"Error al generar PDF: {str(e)}")
    else:
        st.warning("⚠️ Completa el perfil de mascota y selecciona un alimento en las pestañas anteriores.")

# ======================== TAB 4: SEGUIMIENTO DEL PACIENTE ========================

with tabs[3]:
    st.header("📈 Seguimiento del Paciente")
    st.markdown(
        "Carga la **ficha maestra Excel** de un paciente anterior para analizar su evolución nutricional."
    )
    
    # ─── UPLOADER ───
    st.subheader("📁 Cargar Ficha Maestra de Seguimiento")
    archivo_excel = st.file_uploader(
        "Selecciona archivo Excel (.xlsx) con histórico de visitas",
        type=["xlsx"],
        key="tracking_file_upload"
    )
    
    if archivo_excel is not None:
        # Leer y validar
        try:
            df_visitas, metadatos, es_valido, msg_validacion = leer_ficha_maestra(archivo_excel)
            
            if es_valido:
                st.success(f"✅ {msg_validacion}")
                st.session_state["df_tracking"] = df_visitas
                st.session_state["metadatos_tracking"] = metadatos
            else:
                st.error(f"❌ {msg_validacion}")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error al leer archivo: {str(e)}")
            st.stop()
    
    # ─── CONTENIDO PRINCIPAL ───
    if st.session_state.get("df_tracking") is not None:
        df_visitas = st.session_state["df_tracking"]
        metadatos = st.session_state.get("metadatos_tracking", {})
        
        # Calcular deltas
        deltas = calcular_deltas(df_visitas)
        
        # ─── SECCIÓN 1: RESUMEN RÁPIDO ───
        st.markdown("### 📊 Resumen de Cambios (Última vs Penúltima Visita)")
        render_resumen_rapido(deltas)
        
        st.markdown("---")
        
        # ─── SECCIÓN 2: INTERPRETACIÓN NARRATIVA ───
        st.markdown("### 📝 Análisis de Evolución")
        interpretacion = generar_interpretacion_evolucion(df_visitas, deltas)
        st.markdown(
            f"<div style='background:#f0f8ff;border-left:4px solid #2176ff;padding:14px 18px;border-radius:6px;'>{interpretacion}</div>",
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # ─── SECCIÓN 3: 4 GRÁFICOS PLOTLY (2x2 GRID) ───
        st.markdown("### 📈 Gráficos de Evolución")
        try:
            fig_peso, fig_bcs, fig_energia, fig_cobertura = crear_graficos_seguimiento(df_visitas)
            
            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(fig_peso, use_container_width=True)
            with g2:
                st.plotly_chart(fig_bcs, use_container_width=True)
            
            g3, g4 = st.columns(2)
            with g3:
                st.plotly_chart(fig_energia, use_container_width=True)
            with g4:
                st.plotly_chart(fig_cobertura, use_container_width=True)
        except Exception as e:
            st.error(f"Error al crear gráficos: {str(e)}")
        
        st.markdown("---")
        
        # ─── SECCIÓN 4: TABLA HISTÓRICA ───
        st.markdown("### 📋 Tabla de Seguimiento Histórico")
        render_tabla_historica(df_visitas)
        
        st.markdown("---")
        
        # ─── SECCIÓN 5: DECISIÓN CLÍNICA ───
        st.markdown("### 🎯 Recomendación Clínica")
        decision, justificacion = generar_decision_clinica(df_visitas, deltas)
        
        # Determinar color según decision
        color_mapa = {
            "MANTENER": "#52B788",
            "AUMENTAR": "#FFB703",
            "REDUCIR": "#F4845F",
        }
        
        color_decision = "#2176FF"
        for palabra, color in color_mapa.items():
            if palabra in decision:
                color_decision = color
                break
        
        st.markdown(
            f"<div style='background:rgba(255,255,255,1);border-left:5px solid {color_decision};padding:16px 20px;border-radius:8px;margin:12px 0;'>"
            f"<div style='font-size:1.2rem;font-weight:700;color:{color_decision};margin-bottom:8px;'>{decision}</div>"
            f"<div style='font-size:0.95rem;color:#333;'>{justificacion}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # ─── SECCIÓN 6: BOTONES DE ACCIÓN ───
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("➕ Agregar Nueva Visita", key="add_visit_btn"):
                st.info("📝 Funcionalidad de agregar visita disponible en próximas versiones.")
        
        with col_btn2:
            if st.button("💾 Descargar Ficha Actualizada", key="download_updated_btn"):
                try:
                    excel_bytes = exportar_ficha_actualizada(df_visitas, metadatos)
                    st.download_button(
                        label="⬇️ Descargar Excel",
                        data=excel_bytes,
                        file_name=f"seguimiento_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    st.success("✅ Archivo descargado correctamente")
                except Exception as e:
                    st.error(f"Error al descargar: {str(e)}")
    else:
        st.info("👆 Carga un archivo Excel para comenzar el seguimiento del paciente.")

# ======================== PIE DE PÁGINA ========================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #7a8998; font-size: 0.9rem;'>
    🐾 <b>Pet Formulation Companion</b> v1.0 | 
    Análisis Nutricional Integral para Mascotas | 
    2025
    </div>
    """,
    unsafe_allow_html=True
)
