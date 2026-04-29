# ======================== BLOQUE 1: IMPORTS Y UTILIDADES ========================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random
import base64

# Función para generar colores únicos
def get_color_map(items):
    """
    Devuelve un diccionario con una asignación de colores para cada elemento único en la lista.
    
    Parámetros:
    - items: Lista de elementos (por ejemplo, ingredientes).

    Retorno:
    - Diccionario {'elemento': 'color'}.
    """
    palette = [
        "#FF5733", "#33FF57", "#3357FF", "#FFF333", "#8E44AD", "#3498DB",
        "#1ABC9C", "#E67E22", "#E74C3C", "#9B59B6", "#2ECC71", "#F1C40F",
        "#16A085", "#2980B9", "#D35400", "#C0392B", "#27AE60", "#7F8C8D"
    ]
    random.shuffle(palette)
    return {item: palette[i % len(palette)] for i, item in enumerate(items)}

from utils.nutrient_reference import NUTRIENTES_REFERENCIA_PERRO, NUTRIENTES_REFERENCIA_GATO
from utils.fmt_tools import fmt2, fmt2_df
from data import load_ingredients, get_nutrient_list
from optimization import DietFormulator
from profile import load_profile, save_profile, update_mascota_en_perfil
from ui import show_mascota_form
from energy_requirements import calcular_mer, calcular_rer
from energy_requirements import descripcion_condiciones
from auth import USERS_DB
from food_analysis import show_food_analysis
from food_database import FOODS, calculate_energy as calc_energy_food, calculate_ena as calc_ena_food, get_food_names as get_food_names_db
from food_database import calculate_energy_breakdown
from PIL import Image
import io
import datetime
from export_tools import (
    generar_diagnostico_resumen,
    generar_recomendaciones,
    generar_decision_resumen,
    exportar_a_excel,
    exportar_a_html,
    exportar_ficha_maestra_excel,
    crear_visita_dict,
    generar_id_visita,
    generar_uuid_paciente,
)

# Umbral de cobertura energética para alertas visuales (%)
ENERGY_COVERAGE_THRESHOLD = 110

# Factor de ajuste energético para mascotas adultas senior
SENIOR_FACTOR = 0.85

# Paleta de colores para gráficos radar
RADAR_CHART_COLORS = ["#2176FF", "#FFB703", "#52B788", "#F4845F", "#8E9AAF", "#E74C3C"]

# ======================== CONSTANTES DE DIAGNÓSTICO NUTRICIONAL ========================
RIESGO_COLORES = {
    "Bajo": "#52B788",
    "Moderado": "#FFB703",
    "Alto": "#F4845F",
}

RIESGO_ICONS = {
    "Bajo": "🟢",
    "Moderado": "🟠",
    "Alto": "🔴",
}


def get_estado_corporal(bcs):
    """Devuelve el estado corporal textual según el BCS (escala 1–9)."""
    if 1 <= bcs <= 3:
        return "Bajo peso"
    if bcs == 4:
        return "Ligeramente bajo"
    if bcs == 5:
        return "Condición ideal"
    if bcs == 6:
        return "Ligeramente sobrepeso"
    if bcs == 7:
        return "Sobrepeso"
    if 8 <= bcs <= 9:
        return "Obesidad"
    return "Desconocido"


def calcular_riesgo_nutricional(bcs, edad, condicion, etapa, aplicar_senior):
    """Calcula el nivel de riesgo nutricional según los parámetros del perfil."""
    if bcs == 5:
        riesgo = "Bajo"
    elif bcs in [4, 6]:
        riesgo = "Moderado"
    else:
        riesgo = "Alto"

    if aplicar_senior and bcs >= 6:
        riesgo = "Alto"

    if condicion == "Castrado" and bcs >= 6:
        riesgo = "Alto"

    if etapa == "cachorro" and condicion == "Destete a 4 meses":
        riesgo = "Moderado"

    if condicion in ["Gestación (Segunda mitad)", "Lactancia"]:
        riesgo = "Alto"

    return riesgo


def calcular_prioridad_nutricional(bcs, etapa, condicion, edad):
    """Devuelve (prioridad, recomendación) según el perfil de la mascota."""
    if etapa == "cachorro":
        return "Sostener crecimiento", "Maximizar aporte nutricional balanceado"

    if condicion in ["Gestación (Segunda mitad)", "Lactancia"]:
        return "Cubrir alta demanda energética", "Aumentar frecuencia de alimentación y calidad"

    if bcs < 5:
        return "Recuperar condición corporal", "Aumentar gradualmente el aporte energético"

    if bcs > 5:
        return "Controlar peso y energía", "Reducir calorías y aumentar monitoreo"

    # BCS == 5
    if edad >= 7:
        return "Mantener masa magra y prevenir sobrepeso", "Monitoreo frecuente cada 4–8 semanas"

    return "Mantener condición corporal", "Monitoreo regular cada 2–4 semanas"


def generar_interpretacion_diagnostico(nombre, bcs, estado, mer_final,
                                       prioridad, condicion, edad, aplicar_senior):
    """Genera un párrafo con el diagnóstico nutricional automático."""
    texto = f"{nombre} presenta condición corporal {estado.lower()} (BCS {bcs}/9). "
    texto += f"Su requerimiento energético final estimado es {mer_final:.0f} kcal/día. "

    if bcs < 5:
        texto += ("La prioridad nutricional es recuperar condición corporal. "
                  "Se recomienda aumentar gradualmente el aporte energético y monitorear peso cada 2–3 semanas.")
    elif bcs > 5:
        texto += ("La prioridad nutricional es controlar peso y energía. "
                  "Se recomienda reducir calorías gradualmente y monitorear peso cada 1–2 semanas.")
    else:
        if edad >= 7 and aplicar_senior:
            texto += ("Como animal senior, la prioridad es mantener masa magra y prevenir sobrepeso. "
                      "Se recomienda monitoreo frecuente cada 4–8 semanas.")
        elif condicion in ["Gestación (Segunda mitad)", "Lactancia"]:
            texto += ("La prioridad nutricional es cubrir la alta demanda energética. "
                      "Se recomienda aumentar frecuencia de alimentación y monitoreo semanal.")
        else:
            texto += ("La prioridad es mantener la condición corporal actual. "
                      "Se recomienda monitoreo regular cada 2–4 semanas.")

    return texto

# ======================== DEFINICIÓN GLOBAL DE FACTORES ========================
FACTORES_CONDICION = {
    "perro": {
        "adulto": {
            "Castrado": 1.6,
            "Entero": 1.8,
            "Tendencia obesidad o inactivo": [1.2, 1.4],
            "Obeso": 1.0,
            "Bajo peso": [1.4, 1.6],
            "Gestación (Primera mitad)": 1.2,
            "Gestación (Segunda mitad)": 1.6,
            "Lactancia": [3.0, 6.0],
        },
        "cachorro": {
            "Destete a 4 meses": 3.0,
            "5 meses hasta adulto": 2.0,
        },
    },
    "gato": {
        "adulto": {
            "Castrado": 1.2,
            "Entero": 1.4,
            "Tendencia obesidad": 1.0,
            "Obeso": 0.8,
            "Bajo peso": [1.2, 1.4],
            "Gestación (Inicio)": 1.6,
            "Gestación (Final)": 2.0,
            "Lactancia": [2.0, 6.0],
        },
        "cachorro": {
            "Destete a 4 meses": 3.0,
            "5 meses hasta adulto": 2.0,
        },
    },
}

# Set of all gestación condition labels (used for BCS logic and descriptions)
CONDICIONES_GESTACION = {
    "Gestación (Primera mitad)",
    "Gestación (Segunda mitad)",
    "Gestación (Inicio)",
    "Gestación (Final)",
}

# Gestación conditions corresponding to early phase (first half / inicio)
CONDICIONES_GESTACION_INICIAL = {
    "Gestación (Primera mitad)",
    "Gestación (Inicio)",
}

# Gestación conditions corresponding to late phase (second half / final)
CONDICIONES_GESTACION_FINAL = {
    "Gestación (Segunda mitad)",
    "Gestación (Final)",
}

# ======================== BLOQUE 2: ESTILO Y LOGO CON BARRA LATERAL ========================
st.set_page_config(page_title="Formulador UYWA Premium", layout="wide")

# Estilo global para la aplicación
st.markdown("""
    <style>
    html, body, .stApp, .block-container {
        background: linear-gradient(120deg, #ffffff 0%, #eef4fc 100%) !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #2C3E50 !important;
        color: #fff !important;
    }
    section[data-testid="stSidebar"] * {
        color: #fff !important;
    }
    .stButton > button {
        background-color: #2176ff;
        color: #fff !important;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem !important;
    }
    .stButton > button:hover {
        background-color: #1254d1;
        color: #fff !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2) !important;
    }
    .block-container {
        padding: 2rem 4rem;
    }
    .stNumberInput, .stSelectbox, .stTextInput {
        background-color: #eef4fc !important;
        border-radius: 4px;
        border: 1px solid #d4e4fc !important;
        padding: 0.5rem;
    }
    footer {visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

# Validar que la variable `user` esté definida
user = st.session_state.get("user", None)

# Configuración de la barra lateral
with st.sidebar:
    st.image("asstes/logo.png", use_container_width=True)
    st.markdown(
        """
        <div style="text-align:center;margin-bottom:20px;">
            <h1 style="font-family:Montserrat,sans-serif;margin:0;color:#fff;">UYWA Nutrition</h1>
            <p style="font-size:14px;margin:0;color:#fff;">Nutrición de Precisión Basada en Evidencia</p>
            <br>
            <hr style="border:1px solid #fff;">
            <p style="font-size:13px;color:#fff;margin:0;">📧 uywasas@gmail.com</p>
            <p style="font-size:11px;color:#fff;margin:0;">Derechos reservados © 2026</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Verificar el estado del usuario
    if user:
        if user.get("premium", False):
            st.success("Acceso premium activado")
        else:
            st.info("Acceso estándar activado")
    else:
        st.warning("Por favor, inicia sesión.")
        
# ======================== BLOQUE 3: LOGIN ========================
from auth import USERS_DB

def login():
    """
    Maneja la autenticación de usuario y actualiza el estado de sesión.
    """
    st.title("Iniciar sesión")

    # Campos para ingreso de credenciales
    username = st.text_input("Usuario", key="login_usuario")
    password = st.text_input("Contraseña", type="password", key="login_password")

    if st.button("Entrar"):
        user = USERS_DB.get(username.strip().lower())
        if user and user["password"] == password:
            # Establecer la información del usuario en el estado de sesión
            st.session_state["logged_in"] = True
            st.session_state["user"] = user

            # Mensaje de éxito al iniciar sesión
            st.success(f"Bienvenido, {user['name']}!")
        else:
            st.error("Usuario o contraseña incorrectos.")
    else:
        if not st.session_state.get("logged_in", False):
            st.warning("Por favor, inicia sesión para acceder al contenido.")

# Comprobar si el usuario está autenticado
if not st.session_state.get("logged_in", False):
    login()
    st.stop()

# Recuperar la información del usuario autenticado
user = st.session_state.get("user", None)
if not user:
    st.error("El usuario no está autenticado.")
    st.stop()
    
# ======================== BLOQUE 3.1: CARGA DEL PERFIL ========================
from profile import load_profile, save_profile

# Carga el perfil asociado al usuario autenticado
profile = load_profile(user) or {}

# Validar que el perfil tenga valores predeterminados si está vacío
profile.setdefault("mascota", {
    "nombre": "",
    "especie": "perro",
    "edad": 1.0,
    "peso": 12.0,
    "etapa": "adulto",
    "bcs": 5
})

def update_and_save_profile(updated_profile):
    """
    Actualiza el perfil del usuario y guarda los datos.
    """
    save_profile(user, updated_profile)
    st.session_state["profile"] = updated_profile
    st.success("Perfil actualizado exitosamente.")

# ======================== BLOQUE 4: UTILIDADES DE SESIÓN ========================
def safe_float(val, default=0.0):
    try:
        if isinstance(val, str):
            val = val.replace(",", ".")
        return float(val)
    except Exception:
        return default

def clean_state(keys_prefix, valid_names):
    for key in list(st.session_state.keys()):
        for prefix in keys_prefix:
            if key.startswith(prefix):
                found = False
                for n in valid_names:
                    if key.endswith(f"{n}_incl_input") or key.endswith(f"{n}_input"):
                        found = True
                        break
                if not found:
                    del st.session_state[key]

# ======================== BLOQUE 5: TITULO Y TABS PRINCIPALES ========================
st.title("Gestión y Análisis de Dietas")

tabs = st.tabs([
    "Perfil de Mascota",
    "Análisis",
    "Resumen y Exportar"
])

from nutrient_tools import transformar_referencia_a_porcentaje

# ======================== BLOQUE 5.1: TAB PERFIL EDITABLE + CÁLCULOS COMPLETO ========================
with tabs[0]:
    st.subheader("Perfil y Requerimientos Energéticos de la Mascota")

    # --- CSS personalizado para el perfil de mascota ---
    st.markdown(
        """
        <style>
        /* Contenedor principal del perfil en 2 columnas */
        .profile-left {
            text-align: center;
            padding: 20px 10px;
        }
        /* Foto circular de la mascota */
        .pet-photo-circle {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid #2176ff;
            box-shadow: 0 4px 16px rgba(33,118,255,0.25);
            margin: 0 auto 12px auto;
            display: block;
        }
        /* Placeholder circular cuando no hay foto */
        .pet-photo-placeholder {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2176ff 0%, #52b788 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 56px;
            margin: 0 auto 12px auto;
            box-shadow: 0 4px 16px rgba(33,118,255,0.25);
        }
        /* Nombre de la mascota */
        .pet-name {
            font-size: 24px;
            font-weight: 700;
            color: #1a202c;
            margin: 6px 0 2px 0;
        }
        /* Badge de etapa de vida */
        .stage-badge {
            display: inline-block;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin: 6px 0;
        }
        .stage-badge.cachorro {
            background-color: #fef3c7;
            color: #92400e;
            border: 1px solid #fcd34d;
        }
        .stage-badge.adulto {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #6ee7b7;
        }
        /* Tarjetas de datos vitales */
        .vital-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
            border-left: 4px solid #2176ff;
        }
        .vital-card .card-label {
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
        }
        .vital-card .card-value {
            font-size: 20px;
            font-weight: 700;
            color: #1a202c;
        }
        .vital-card .card-icon {
            font-size: 22px;
            float: right;
            margin-top: -2px;
        }
        /* BCS indicator */
        .bcs-bar-container {
            background: #e2e8f0;
            border-radius: 6px;
            height: 8px;
            margin-top: 6px;
            overflow: hidden;
        }
        .bcs-bar-fill {
            height: 8px;
            border-radius: 6px;
            background: linear-gradient(90deg, #52b788, #2176ff);
        }
        /* Tarjetas de energía */
        .energy-card {
            background: linear-gradient(135deg, #2176ff 0%, #1254d1 100%);
            border-radius: 12px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0 4px 14px rgba(33,118,255,0.3);
            color: #fff;
        }
        .energy-card .card-label {
            font-size: 12px;
            color: rgba(255,255,255,0.8);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
        }
        .energy-card .card-value {
            font-size: 22px;
            font-weight: 700;
            color: #fff;
        }
        .energy-card.green {
            background: linear-gradient(135deg, #52b788 0%, #2d9e72 100%);
            box-shadow: 0 4px 14px rgba(82,183,136,0.3);
        }
        .energy-card.orange {
            background: linear-gradient(135deg, #f4845f 0%, #d4603a 100%);
            box-shadow: 0 4px 14px rgba(244,132,95,0.3);
        }
        .energy-card.purple {
            background: linear-gradient(135deg, #8e44ad 0%, #6c3483 100%);
            box-shadow: 0 4px 14px rgba(142,68,173,0.3);
        }
        .energy-card.purple-inactive {
            background: linear-gradient(135deg, #aab0c0 0%, #8e9aaf 100%);
            box-shadow: 0 4px 14px rgba(142,154,175,0.25);
        }
        /* Sección separadora */
        .section-divider {
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 20px 0 16px 0;
        }
        /* Tablas de energía y nutrientes */
        .energy-table, .nutrients-table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
            font-size: 15px;
            text-align: center;
            border-radius: 8px;
            overflow: hidden;
        }
        .energy-table th, .nutrients-table th {
            background-color: #4A5568;
            color: #fff;
            padding: 10px;
            font-weight: bold;
        }
        .energy-table td, .nutrients-table td {
            padding: 10px;
        }
        .energy-table tr:nth-child(even), .nutrients-table tr:nth-child(even) {
            background-color: #edf2f7;
        }
        .energy-table tr:nth-child(odd), .nutrients-table tr:nth-child(odd) {
            background-color: #ffffff;
        }
        /* Card de diagnóstico nutricional */
        .diagnostic-card {
            border-radius: 12px;
            padding: 20px 24px;
            margin: 20px 0;
            border-left: 6px solid;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .diagnostic-card.low-risk {
            background: rgba(82, 183, 136, 0.08);
            border-left-color: #52B788;
            color: #1b7a53;
        }
        .diagnostic-card.moderate-risk {
            background: rgba(255, 183, 3, 0.08);
            border-left-color: #FFB703;
            color: #92400e;
        }
        .diagnostic-card.high-risk {
            background: rgba(244, 132, 95, 0.08);
            border-left-color: #F4845F;
            color: #933b1a;
        }
        .diagnostic-title {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .diagnostic-state {
            font-size: 14px;
            margin-bottom: 6px;
            opacity: 0.9;
        }
        .diagnostic-priority {
            font-size: 14px;
            font-weight: 600;
            margin-top: 8px;
        }
        .diagnostic-text {
            font-size: 15px;
            line-height: 1.5;
            margin-top: 16px;
            font-style: italic;
            opacity: 0.95;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Formulario de edición en expander ---
    mascota = profile.get("mascota", {})
    with st.expander("✏️ Editar Perfil de la Mascota", expanded=False):
        ef_col1, ef_col2 = st.columns(2)
        with ef_col1:
            nombre_mascota = st.text_input("Nombre de la mascota", value=mascota.get("nombre", "Mascota"), key="nombre_mascota")
            especie = st.selectbox("Especie", ["perro", "gato"], index=["perro", "gato"].index(mascota.get("especie", "perro").lower()), key="especie_mascota")
            edad = st.number_input("Edad en años", min_value=0.1, max_value=20.0, value=max(0.1, safe_float(mascota.get("edad", 1.0), 1.0)), step=0.1, key="edad_mascota")
        with ef_col2:
            peso = st.number_input("Peso en kg", min_value=0.1, max_value=200.0, value=max(0.1, safe_float(mascota.get("peso", 12.0), 12.0)), step=0.1, key="peso_mascota")
            etapa = st.selectbox("Etapa de vida", ["adulto", "cachorro"], index=["adulto", "cachorro"].index(mascota.get("etapa", "adulto").lower()), key="etapa_mascota")

        # Condición fisiológica/productiva dependiente de la etapa
        _especie_form_cond = st.session_state.get("especie_mascota", mascota.get("especie", "perro"))
        if st.session_state.get("etapa_mascota", mascota.get("etapa", "adulto")) == "adulto":
            if _especie_form_cond == "perro":
                opciones_condicion = ["Castrado", "Entero", "Gestación (Primera mitad)", "Gestación (Segunda mitad)", "Lactancia"]
            else:
                opciones_condicion = ["Castrado", "Entero", "Gestación (Inicio)", "Gestación (Final)", "Lactancia"]
        else:
            opciones_condicion = ["Destete a 4 meses", "5 meses hasta adulto"]

        condicion_predeterminada = mascota.get("condicion", "Castrado")
        if condicion_predeterminada not in opciones_condicion:
            condicion_predeterminada = opciones_condicion[0]
        condicion = st.selectbox(
            "Condición fisiológica/productiva",
            opciones_condicion,
            index=opciones_condicion.index(condicion_predeterminada),
            key="condicion_mascota",
        )

        # Condición Corporal (BCS)
        bcs_disabled = st.session_state.get("etapa_mascota", mascota.get("etapa", "adulto")) == "cachorro" and condicion == "Destete a 4 meses"
        bcs_val = max(1, min(9, int(safe_float(mascota.get("bcs", 5), 5))))
        bcs = st.slider("Condición Corporal (BCS 1–9)", min_value=1, max_value=9, value=bcs_val, key="bcs_mascota", disabled=bcs_disabled)

        # Ajuste Senior: visible solo para perro/gato adulto
        _etapa_form = st.session_state.get("etapa_mascota", mascota.get("etapa", "adulto"))
        _especie_form = st.session_state.get("especie_mascota", mascota.get("especie", "perro"))
        _edad_form = safe_float(st.session_state.get("edad_mascota", mascota.get("edad", 1.0)), 1.0)
        if _etapa_form == "adulto" and _especie_form in ("perro", "gato"):
            _stored_senior = mascota.get("aplicar_ajuste_senior")
            _senior_default = bool(_stored_senior) if _stored_senior is not None else (_edad_form >= 7)
            aplicar_ajuste_senior_form = st.checkbox(
                "👴 Aplicar ajuste energético Senior (-15%)",
                value=_senior_default,
                key="aplicar_ajuste_senior_mascota",
                help="Reduce el MER en un 15% para mascotas adultas senior. Se aplica solo cuando la condición corporal es ideal (BCS = 5).",
            )
            if _edad_form >= 7:
                st.info("ℹ️ Recomendado para mascota mayor de 7 años")
        else:
            aplicar_ajuste_senior_form = False
            if "aplicar_ajuste_senior_mascota" in st.session_state:
                del st.session_state["aplicar_ajuste_senior_mascota"]

        # Foto de la mascota en el formulario
        foto_upload = st.file_uploader("Foto de la mascota (opcional)", type=["png", "jpg", "jpeg"], key="foto_mascota_upload")
        if foto_upload is not None:
            st.session_state["mascota_foto_bytes"] = foto_upload.getvalue()
        if st.session_state.get("mascota_foto_bytes"):
            col_prev, _ = st.columns([1, 3])
            with col_prev:
                st.image(st.session_state["mascota_foto_bytes"], width=100, caption="Vista previa")
            if st.button("🗑️ Eliminar foto", key="del_foto_perfil"):
                del st.session_state["mascota_foto_bytes"]
                st.rerun()

        if st.button("💾 Guardar perfil de mascota", key="guardar_perfil_btn"):
            mascota_actualizada = {
                "nombre": st.session_state["nombre_mascota"],
                "especie": st.session_state["especie_mascota"].lower(),
                "edad": st.session_state["edad_mascota"],
                "peso": st.session_state["peso_mascota"],
                "etapa": st.session_state["etapa_mascota"].lower(),
                "condicion": condicion,
                "bcs": st.session_state.get("bcs_mascota", 5),
                "aplicar_ajuste_senior": st.session_state.get("aplicar_ajuste_senior_mascota", False),
            }
            profile["mascota"] = mascota_actualizada
            update_and_save_profile(profile)
            st.success("✅ Perfil actualizado correctamente.")

    # Refrescar datos del perfil tras posible guardado
    mascota = profile.get("mascota", {})

    # Leer valores actuales (del estado de sesión si fueron modificados, o del perfil guardado)
    especie = st.session_state.get("especie_mascota", mascota.get("especie", "perro"))
    etapa = st.session_state.get("etapa_mascota", mascota.get("etapa", "adulto"))
    condicion = st.session_state.get("condicion_mascota", mascota.get("condicion", "Castrado"))
    bcs = max(1, min(9, int(safe_float(st.session_state.get("bcs_mascota", mascota.get("bcs", 5)), 5))))
    peso = max(0.1, safe_float(st.session_state.get("peso_mascota", mascota.get("peso", 12.0)), 12.0))
    edad = safe_float(st.session_state.get("edad_mascota", mascota.get("edad", 1.0)), 1.0)
    bcs_disabled = etapa == "cachorro" and condicion == "Destete a 4 meses"

    # Leer ajuste senior: desde session_state (widget) o desde perfil guardado
    if etapa == "adulto" and especie in ("perro", "gato"):
        _stored_senior = mascota.get("aplicar_ajuste_senior")
        _senior_profile_default = bool(_stored_senior) if _stored_senior is not None else (edad >= 7)
        aplicar_ajuste_senior = bool(st.session_state.get("aplicar_ajuste_senior_mascota", _senior_profile_default))
    else:
        aplicar_ajuste_senior = False

    # --- Cálculo del RER y MER (necesario antes del layout) ---
    try:
        energia_basal_actual = calcular_rer(peso)
        factores_etapa = FACTORES_CONDICION.get(especie, {}).get(etapa, {}).get(condicion, None)
        if factores_etapa is None:
            raise ValueError(f"Condición desconocida para '{especie}'.")
        factor_fisiologico = factores_etapa if isinstance(factores_etapa, (int, float)) else factores_etapa[0]
        mer_actual = energia_basal_actual * factor_fisiologico

        factores_bcs = {6: 0.9, 7: 0.8, 8: 0.7, 9: 0.6, 4: 1.1, 3: 1.2, 2: 1.3, 1: 1.4}

        # Determine if condition is gestación
        es_gestacion = condicion in CONDICIONES_GESTACION

        if es_gestacion and not bcs_disabled:
            # For gestating animals, BCS adjustment is only applied at extreme values (≤3 or ≥7).
            # BCS 4–6 is considered an acceptable range for a gestante; no adjustment is needed
            # because moderate variation in body condition is normal during pregnancy.
            bcs_gestacion_extremo = bcs <= 3 or bcs >= 7
            if bcs_gestacion_extremo:
                # BCS extreme: apply adjustment
                peso_objetivo = peso * factores_bcs.get(bcs, 1.0)
                energia_basal_objetivo = calcular_rer(peso_objetivo)
                mer_final = energia_basal_objetivo * factor_fisiologico
            else:
                # BCS 4–6: acceptable range for gestante, no BCS adjustment
                peso_objetivo = "-"
                energia_basal_objetivo = "-"
                mer_final = mer_actual
        elif not es_gestacion and bcs != 5 and not bcs_disabled:
            peso_objetivo = peso * factores_bcs.get(bcs, 1.0)
            energia_basal_objetivo = calcular_rer(peso_objetivo)
            mer_final = energia_basal_objetivo * factor_fisiologico
            bcs_gestacion_extremo = False
        else:
            peso_objetivo = "-"
            energia_basal_objetivo = "-"
            mer_final = mer_actual
            bcs_gestacion_extremo = False
        factor_condicion_val = round(mer_final / energia_basal_actual, 2) if energia_basal_actual > 1e-6 else "-"

        # --- Ajuste senior (paso final, después de todos los cálculos de BCS) ---
        senior_aplicado = False
        if (etapa == "adulto"
                and aplicar_ajuste_senior
                and bcs == 5
                and not bcs_disabled):
            mer_final = mer_final * SENIOR_FACTOR
            senior_aplicado = True

        st.session_state["energia_actual"] = mer_final
        # Almacenar valores intermedios para Pestaña 3
        st.session_state["rer_actual"] = energia_basal_actual
        st.session_state["mer_base_actual"] = mer_actual
        st.session_state["factor_fisiologico_actual"] = factor_fisiologico
        st.session_state["senior_aplicado_actual"] = senior_aplicado

    except Exception as e:
        st.error(f"Error en cálculos energéticos: {str(e)}")
        st.stop()

    # ===================== LAYOUT DE 2 COLUMNAS =====================
    col_left, col_right = st.columns([3, 7])

    with col_left:
        # Icono de especie
        especie_icon = "🐕" if especie == "perro" else "🐈"
        nombre_display = mascota.get("nombre", "Mascota")

        # Foto circular o placeholder
        foto_bytes = st.session_state.get("mascota_foto_bytes")
        if foto_bytes:
            foto_b64 = base64.b64encode(foto_bytes).decode("utf-8")
            st.markdown(
                f"""
                <div class="profile-left">
                    <img src="data:image/png;base64,{foto_b64}" class="pet-photo-circle" alt="foto mascota"/>
                    <div class="pet-name">{nombre_display}</div>
                    <div style="font-size:32px; margin:4px 0;">{especie_icon}</div>
                    <span class="stage-badge {etapa}">{etapa.capitalize()}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="profile-left">
                    <div class="pet-photo-placeholder">{especie_icon}</div>
                    <div class="pet-name">{nombre_display}</div>
                    <div style="font-size:13px; color:#718096; margin:2px 0;">{especie.capitalize()}</div>
                    <span class="stage-badge {etapa}">{etapa.capitalize()}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_right:
        # --- Datos Vitales en cards (2 por fila) ---
        edad_display = max(0.0, safe_float(st.session_state.get("edad_mascota", mascota.get("edad", 1.0)), 1.0))
        bcs_pct = int((bcs / 9) * 100)
        bcs_color = "#52b788" if 4 <= bcs <= 6 else ("#f4845f" if bcs > 6 else "#fbbf24")

        vc1, vc2 = st.columns(2)
        with vc1:
            st.markdown(
                f"""
                <div class="vital-card">
                    <span class="card-icon">🎂</span>
                    <div class="card-label">Edad</div>
                    <div class="card-value">{fmt2(edad_display)} años</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with vc2:
            st.markdown(
                f"""
                <div class="vital-card" style="border-left-color:#52b788;">
                    <span class="card-icon">⚖️</span>
                    <div class="card-label">Peso</div>
                    <div class="card-value">{fmt2(peso)} kg</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        vc3, vc4 = st.columns(2)
        with vc3:
            st.markdown(
                f"""
                <div class="vital-card" style="border-left-color:{bcs_color};">
                    <span class="card-icon">📏</span>
                    <div class="card-label">Condición Corporal (BCS)</div>
                    <div class="card-value">{bcs} / 9</div>
                    <div class="bcs-bar-container">
                        <div class="bcs-bar-fill" style="width:{bcs_pct}%; background:{bcs_color};"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with vc4:
            st.markdown(
                f"""
                <div class="vital-card" style="border-left-color:#8e9aaf;">
                    <span class="card-icon">🛠️</span>
                    <div class="card-label">Condición Fisiológica</div>
                    <div class="card-value" style="font-size:15px;">{condicion}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ===================== DIAGNÓSTICO NUTRICIONAL INICIAL (ANCHO COMPLETO) =====================
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("### 🩺 Diagnóstico Nutricional Inicial")

    _estado_corporal = get_estado_corporal(bcs)
    _riesgo = calcular_riesgo_nutricional(bcs, edad, condicion, etapa, aplicar_ajuste_senior)
    _prioridad, _recomendacion = calcular_prioridad_nutricional(bcs, etapa, condicion, edad)
    _interpretacion = generar_interpretacion_diagnostico(
        nombre_display, bcs, _estado_corporal, mer_final,
        _prioridad, condicion, edad, aplicar_ajuste_senior
    )

    _riesgo_class = {"Bajo": "low-risk", "Moderado": "moderate-risk", "Alto": "high-risk"}.get(_riesgo, "low-risk")
    _riesgo_icon = RIESGO_ICONS.get(_riesgo, "🟢")

    # Almacenar diagnóstico para Pestaña 3
    st.session_state["estado_corporal_tab1"] = _estado_corporal
    st.session_state["riesgo_nutricional_tab1"] = _riesgo
    st.session_state["prioridad_nutricional_tab1"] = _prioridad
    st.session_state["interpretacion_diagnostico_tab1"] = _interpretacion

    st.markdown(
        f"""
        <div class="diagnostic-card {_riesgo_class}">
            <div class="diagnostic-title">{_riesgo_icon} RIESGO {_riesgo.upper()}</div>
            <div class="diagnostic-state">Estado corporal: {_estado_corporal} (BCS {bcs}/9)</div>
            <div class="diagnostic-priority">🎯 Prioridad: {_prioridad}</div>
            <div class="diagnostic-priority" style="font-weight:400;">💡 {_recomendacion}</div>
            <div class="diagnostic-text">"{_interpretacion}"</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===================== SECCIÓN ENERGÍA (ANCHO COMPLETO) =====================
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("**🔋 Requerimientos Energéticos**")

    ec1, ec2, ec3, ec4 = st.columns(4)
    with ec1:
        st.markdown(
            f"""
            <div class="energy-card">
                <div class="card-label">RER Actual</div>
                <div class="card-value">{fmt2(energia_basal_actual)}</div>
                <div style="font-size:11px; opacity:0.85;">kcal/día</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ec2:
        st.markdown(
            f"""
            <div class="energy-card green">
                <div class="card-label">MER Adulto/Fisiológico</div>
                <div class="card-value">{fmt2(mer_actual)}</div>
                <div style="font-size:11px; opacity:0.85;">kcal/día</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ec3:
        st.markdown(
            f"""
            <div class="energy-card orange">
                <div class="card-label">MER Ajustado Final</div>
                <div class="card-value">{fmt2(mer_final)}</div>
                <div style="font-size:11px; opacity:0.85;">kcal/día</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ec4:
        _senior_card_class = "purple" if senior_aplicado else "purple-inactive"
        _senior_label = "×0.85 aplicado" if senior_aplicado else "No aplicado"
        st.markdown(
            f"""
            <div class="energy-card {_senior_card_class}">
                <div class="card-label">Factor Condición Final</div>
                <div class="card-value">{factor_condicion_val}</div>
                <div style="font-size:11px; opacity:0.85;">Senior: {_senior_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Aviso cuando ajuste senior no se aplica por BCS ≠ 5
    if aplicar_ajuste_senior and not senior_aplicado and etapa == "adulto" and especie in ("perro", "gato"):
        st.warning("⚠️ Ajuste senior no aplicado porque el requerimiento fue priorizado por corrección de condición corporal.")

    # Mensajes informativos para gestación
    if es_gestacion and not bcs_disabled:
        if not bcs_gestacion_extremo:
            st.info("ℹ️ Ajuste BCS no aplicado: La gestante se encuentra en condición corporal aceptable. "
                    "El requerimiento se basa únicamente en el factor de gestación.")
        else:
            st.warning("⚠️ Condición corporal fuera de rango ideal. Se aplicará corrección adicional por BCS.")

    # Botón de edición
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    if st.button("✏️ Editar perfil", key="btn_editar_perfil_shortcut"):
        st.info("Usa el panel **✏️ Editar Perfil de la Mascota** en la parte superior para modificar los datos.")

    # ===================== TABLAS DETALLADAS (ANCHO COMPLETO) =====================
    try:
        # Descripción condicional para MER Actual según gestación
        if condicion in CONDICIONES_GESTACION_INICIAL:
            _desc_mer_actual = "Incremento energético asociado al desarrollo embrionario inicial y adaptación metabólica materna."
        elif condicion in CONDICIONES_GESTACION_FINAL:
            _desc_mer_actual = "Incremento energético elevado por crecimiento fetal acelerado y preparación para la lactancia."
        else:
            _desc_mer_actual = "Energía diaria necesaria según la condición productiva y fisiológica."

        # Tabla de energías calculadas
        _senior_valor = "Aplicado: ×0.85" if senior_aplicado else "No aplicado"
        energia_data = [
            {"Tipo": "RER Actual", "Valor": f"{fmt2(energia_basal_actual)} kcal/día", "Descripción": "Energía necesaria en reposo para mantener funciones básicas como respirar y digerir."},
            {"Tipo": "MER Actual (RER × Factor Fisiológico)", "Valor": f"{fmt2(mer_actual)} kcal/día", "Descripción": _desc_mer_actual},
            {"Tipo": "Peso Objetivo", "Valor": f"{fmt2(peso_objetivo)} kg" if peso_objetivo != "-" else "-", "Descripción": "Peso estimado para ajustar según la condición corporal (BCS)."},
            {"Tipo": "RER Objetivo", "Valor": f"{fmt2(energia_basal_objetivo)} kcal/día" if energia_basal_objetivo != "-" else "-", "Descripción": "Energía en reposo recalculada con el peso objetivo."},
            {"Tipo": "Ajuste senior", "Valor": _senior_valor, "Descripción": "Corrección energética opcional (-15%, ×0.85) para animales adultos senior (7+ años), usada solo cuando la condición corporal es ideal."},
            {"Tipo": "MER Ajustada Final", "Valor": f"{fmt2(mer_final)} kcal/día", "Descripción": "Energía total diaria necesaria tras ajustes por BCS y condición."},
        ]

        st.markdown("<br>", unsafe_allow_html=True)
        html_table = "<table class='energy-table'><thead><tr><th>Tipo de Energía</th><th>Valor</th><th>Descripción</th></tr></thead><tbody>"
        for entry in energia_data:
            html_table += f"<tr><td>{entry['Tipo']}</td><td>{entry['Valor']}</td><td>{entry['Descripción']}</td></tr>"
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)

        # Tabla de nutrientes ajustados
        nutrientes_ref = NUTRIENTES_REFERENCIA_PERRO if especie == "perro" else NUTRIENTES_REFERENCIA_GATO
        nutrientes_especie_etapa = nutrientes_ref.get(etapa, {})
        kg_dieta_necesaria = mer_final / 4000.0

        requerimientos_ajustados = []
        _req_pb_g = None
        _req_ee_g = None
        for nutriente, valores in nutrientes_especie_etapa.items():
            unidad = valores.get("unit", "")
            min_valor = valores.get("min", None)
            max_valor = valores.get("max", None)

            if unidad == "%":
                min_ajustado = (min_valor / 100.0) * kg_dieta_necesaria * 1000 if min_valor is not None else None
                max_ajustado = (max_valor / 100.0) * kg_dieta_necesaria * 1000 if max_valor is not None else None
                nueva_unidad = "g"
                if nutriente == "Proteína" and min_ajustado is not None:
                    _req_pb_g = min_ajustado
                elif nutriente == "Grasa" and min_ajustado is not None:
                    _req_ee_g = min_ajustado
            elif unidad in ["mg/kg", "UI/kg", "IU/kg", "µg/kg"]:
                unidad_base = unidad.replace("/kg", "")
                min_ajustado = min_valor * kg_dieta_necesaria if min_valor is not None else None
                max_ajustado = max_valor * kg_dieta_necesaria if max_valor is not None else None
                nueva_unidad = unidad_base
            else:
                min_ajustado = min_valor
                max_ajustado = max_valor
                nueva_unidad = unidad if unidad else "-"

            requerimientos_ajustados.append({
                "Nutriente": nutriente,
                "Min Ajustado": fmt2(min_ajustado) if min_ajustado is not None else "-",
                "Max Ajustado": fmt2(max_ajustado) if max_ajustado is not None else "-",
                "Unidad": nueva_unidad,
            })

        st.session_state["req_pb_g"] = _req_pb_g
        st.session_state["req_ee_g"] = _req_ee_g

        df_nutrientes_ajustados = pd.DataFrame(requerimientos_ajustados)
        st.session_state["tabla_requerimientos_base"] = df_nutrientes_ajustados.copy()

        with st.expander("📋 Ver requerimientos nutricionales detallados del paciente", expanded=False):
            st.markdown("<br>", unsafe_allow_html=True)
            html_nutrientes = "<table class='nutrients-table'><thead><tr><th>Nutriente</th><th>Min Ajustado</th><th>Max Ajustado</th><th>Unidad</th></tr></thead><tbody>"
            for req in requerimientos_ajustados:
                html_nutrientes += f"<tr><td>{req['Nutriente']}</td><td>{req['Min Ajustado']}</td><td>{req['Max Ajustado']}</td><td>{req['Unidad']}</td></tr>"
            html_nutrientes += "</tbody></table>"
            st.markdown(html_nutrientes, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error en cálculos y ajustes: {str(e)}")
        st.stop()
        
# ======================== DEFINICIÓN DE FUNCIONES AUXILIARES ========================
def get_unidades_dict(nutrientes_seleccionados):
    """
    Devuelve un diccionario de nutrientes seleccionados con sus unidades correspondientes.
    Si el nutriente no tiene una unidad definida, se asigna por defecto 'unidad'.
    """
    unidades_base = {
        "Proteína": "g",
        "Grasa": "g",
        "Energía metabolizable (EM)": "kcal",
        "Calcio": "mg",
        "Fósforo": "mg",
        "Hierro": "mg",
        "Zinc": "mg",
        "Vitamina A": "UI",
        "Vitamina D": "UI",
        "Vitamina E": "mg",
    }
    return {nutriente: unidades_base.get(nutriente, "unidad") for nutriente in nutrientes_seleccionados}

# ======================== BLOQUE 6: ANÁLISIS NUTRICIONAL ========================
with tabs[1]:
    show_food_analysis()

# ======================== FUNCIONES AUXILIARES ========================
def mf_a_ms(gramos_mf, humedad_pct):
    """Convierte gramos en Materia Fresca a Materia Seca usando el % de humedad."""
    return gramos_mf * (100.0 - humedad_pct) / 100.0


def fmt2(x):
    try:
        f = float(x)
        return f"{f:,.2f}"
    except Exception:
        return x

def fmt2_df(df):
    df_fmt = df.copy()
    for c in df_fmt.columns:
        if c.startswith('%') or c.lower().startswith('costo') or c.lower().startswith('precio') or c.lower().startswith('aporte'):
            df_fmt[c] = df_fmt[c].apply(fmt2)
    return df_fmt

# --- Mapeo color ingredientes (simple pero efectivo) ---
def get_color_map(ingredientes):
    palette = [
        "#19345c", "#7a9fc8", "#e2b659", "#7fc47f",
        "#ed7a7a", "#c07ad7", "#7ad7d2", "#ffb347",
        "#b7e28a", "#d1a3a4", "#f0837c", "#b2b2b2",
    ]
    return {ing: palette[i % len(palette)] for i, ing in enumerate(ingredientes)}

# --- Selector de unidad robusto ---
def unit_selector(label, options, default, key):
    idx = options.index(default) if default in options else 0
    return st.selectbox(label, options, index=idx, key=key)

# --- Factor de conversión y etiqueta según unidad ---
def get_unit_factor(base_unit, manual_unit):
    # Ejemplo: base_unit = "kg", manual_unit = "ton" ⇒ factor = 0.001
    conversion = {
        ("kg", "kg"): (1, "kg"),
        ("kg", "ton"): (0.001, "ton"),
        ("g", "g"): (1, "g"),
        ("g", "100g"): (0.01, "100g"),
        ("g", "kg"): (0.001, "kg"),
        ("g", "ton"): (0.000001, "ton"),
        ("kcal", "kcal"): (1, "kcal"),
        ("kcal", "1000kcal"): (0.001, "1000kcal"),
        ("%", "%"): (1, "%"),  # ← CORREGIDO: Agregué la comilla faltante aquí
        ("%", "100 unidades"): (100, "100 unidades"),
        ("unidad", "unidad"): (1, "unidad"),
        ("unidad", "100 unidades"): (100, "100 unidades"),
        ("unidad", "1000 unidades"): (1000, "1000 unidades"),
        ("unidad", "kg"): (1, "kg"),
        ("unidad", "ton"): (0.001, "ton"),
    }
    return conversion.get((base_unit, manual_unit), (1, manual_unit))

# --- Unidades base por nutriente (puedes ajustar según tus columnas) ---
def get_unidades_dict(nutrientes):
    default = "unidad"
    ref = {
        "PB": "kg",
        "EE": "kg",
        "FB": "kg",
        "EMA_POLLIT": "kcal",
        "LYS_DR": "g",
        "MET_DR": "g",
        "M+C_DR": "g",
        # Agrega los que correspondan...
    }
    return {nut: ref.get(nut, default) for nut in nutrientes}

# ======================== BLOQUE 9: RESUMEN Y EXPORTAR ========================
with tabs[2]:
    st.header("📋 Resumen y Exportación")

    # ── Leer datos del perfil ──────────────────────────────────────────────────
    _perfil3 = st.session_state.get("profile", {})
    _mascota3 = _perfil3.get("mascota", {})

    _nombre3 = st.session_state.get("nombre_mascota", _mascota3.get("nombre", "—")) or "—"
    _especie3 = st.session_state.get("especie_mascota", _mascota3.get("especie", "perro"))
    _edad3 = safe_float(st.session_state.get("edad_mascota", _mascota3.get("edad", 1.0)), 1.0)
    _peso3 = safe_float(st.session_state.get("peso_mascota", _mascota3.get("peso", 12.0)), 12.0)
    _etapa3 = st.session_state.get("etapa_mascota", _mascota3.get("etapa", "adulto"))
    _condicion3 = st.session_state.get("condicion_mascota", _mascota3.get("condicion", "Castrado"))
    _bcs3 = max(1, min(9, int(safe_float(st.session_state.get("bcs_mascota", _mascota3.get("bcs", 5)), 5))))

    # ── Leer datos energéticos calculados en Pestaña 1 ────────────────────────
    _mer_final3 = st.session_state.get("energia_actual", None)
    _rer3 = st.session_state.get("rer_actual", None)
    _mer_base3 = st.session_state.get("mer_base_actual", None)
    _factor_fis3 = st.session_state.get("factor_fisiologico_actual", None)
    _senior3 = st.session_state.get("senior_aplicado_actual", False)
    _estado_corp3 = st.session_state.get("estado_corporal_tab1", get_estado_corporal(_bcs3))
    _riesgo3 = st.session_state.get("riesgo_nutricional_tab1", "—")
    _prioridad3 = st.session_state.get("prioridad_nutricional_tab1", "—")
    _aplicar_senior3 = bool(st.session_state.get("aplicar_ajuste_senior_mascota", False))

    # ── Leer datos del alimento evaluado en Pestaña 2 ─────────────────────────
    _food_name3 = st.session_state.get("analysis_food_selector", None)
    _food_data3 = FOODS.get(_food_name3, {}) if _food_name3 else {}
    _food_energy3 = calc_energy_food(_food_data3) if _food_data3 else {}
    _food_ena3 = calc_ena_food(_food_data3) if _food_data3 else 0.0
    _gramos3 = safe_float(
        st.session_state.get(f"gramos_alimento_{_food_name3}", 100.0), 100.0
    ) if _food_name3 else 0.0

    # Calcular valores derivados de alimento
    _me3 = _food_energy3.get("ME", 0.0) if _food_energy3 else 0.0
    _aporte3 = (_me3 / 100.0) * _gramos3
    _req_pb3 = st.session_state.get("req_pb_g", None)
    _req_ee3 = st.session_state.get("req_ee_g", None)
    _gramos_pb3 = (_food_data3.get("PB", 0) / 100.0) * _gramos3 if _food_data3 else 0.0
    _gramos_ee3 = (_food_data3.get("EE", 0) / 100.0) * _gramos3 if _food_data3 else 0.0

    _datos_completos = (_mer_final3 is not None and _mer_final3 > 0 and _food_name3 is not None)

    if _datos_completos:
        _cobertura3 = (_aporte3 / _mer_final3) * 100.0
        _gramos_rec3 = (_mer_final3 / (_me3 / 100.0)) if _me3 > 0 else 0.0
        _dif_g3 = _gramos_rec3 - _gramos3
        _cob_pb3 = (_gramos_pb3 / _req_pb3 * 100.0) if (_req_pb3 and _req_pb3 > 0) else None
        _cob_ee3 = (_gramos_ee3 / _req_ee3 * 100.0) if (_req_ee3 and _req_ee3 > 0) else None
    else:
        _cobertura3 = 0.0
        _gramos_rec3 = 0.0
        _dif_g3 = 0.0
        _cob_pb3 = None
        _cob_ee3 = None

    # ── Generar textos del informe ─────────────────────────────────────────────
    _diagnostico3 = generar_diagnostico_resumen(
        _nombre3, _bcs3, _estado_corp3, _mer_final3 or 0.0,
        _prioridad3, _condicion3, _edad3, _aplicar_senior3
    )

    _resultado3, _dif_kcal3, _interpretacion3 = generar_decision_resumen(
        _cobertura3, _aporte3, _mer_final3 or 0.0,
        _gramos3, _gramos_rec3, _cob_pb3, _cob_ee3
    ) if _datos_completos else ("—", 0.0, "Complete el perfil y el análisis de alimento.")

    _recomendaciones3 = generar_recomendaciones(
        _estado_corp3, _bcs3, _edad3, _condicion3,
        _cobertura3 if _datos_completos else None,
        _cob_pb3, _cob_ee3
    )

    # ── SECCIÓN 1: RESUMEN DEL PACIENTE ───────────────────────────────────────
    st.subheader("👤 Resumen del Paciente")
    _rc1, _rc2 = st.columns(2)
    _resumen_items_izq = [
        ("Nombre", _nombre3),
        ("Especie", _especie3.capitalize()),
        ("Edad", f"{_edad3:.1f} años"),
        ("Peso actual", f"{_peso3:.1f} kg"),
    ]
    _resumen_items_der = [
        ("Etapa de vida", _etapa3.capitalize()),
        ("Condición fisiológica", _condicion3),
        ("BCS", f"{_bcs3}/9"),
        ("Estado corporal", _estado_corp3),
        ("Riesgo nutricional", _riesgo3),
    ]
    with _rc1:
        for _lbl, _val in _resumen_items_izq:
            st.markdown(
                f"<div style='padding:6px 0;border-bottom:1px solid #eef0f4;'>"
                f"<b>{_lbl}:</b> {_val}</div>",
                unsafe_allow_html=True,
            )
    with _rc2:
        for _lbl, _val in _resumen_items_der:
            st.markdown(
                f"<div style='padding:6px 0;border-bottom:1px solid #eef0f4;'>"
                f"<b>{_lbl}:</b> {_val}</div>",
                unsafe_allow_html=True,
            )

    # ── SECCIÓN 2: DIAGNÓSTICO NUTRICIONAL ────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🩺 Diagnóstico Nutricional")
    st.markdown(
        f"<div style='background:#f0f8ff;border-left:4px solid #52B788;"
        f"padding:14px 18px;border-radius:6px;font-size:0.97rem;'>"
        f"{_diagnostico3}</div>",
        unsafe_allow_html=True,
    )

    # ── SECCIÓN 3: REQUERIMIENTO ENERGÉTICO ───────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⚡ Requerimiento Energético")

    if _mer_final3 is not None:
        _ec1, _ec2, _ec3, _ec4 = st.columns(4)
        with _ec1:
            st.metric("🔋 RER (kcal/día)", f"{_rer3:.1f}" if _rer3 else "—")
        with _ec2:
            st.metric("📊 MER base (kcal/día)", f"{_mer_base3:.1f}" if _mer_base3 else "—")
        with _ec3:
            st.metric("🎯 MER final (kcal/día)", f"{_mer_final3:.1f}")
        with _ec4:
            _bcs_adj = "Sí" if _bcs3 != 5 else "No"
            _sen_adj = "Sí" if _senior3 else "No"
            st.metric("⚙️ Ajuste BCS / Senior", f"{_bcs_adj} / {_sen_adj}")

        _en_rows = [
            ("RER (kcal/día)", f"{_rer3:.1f}" if _rer3 else "—"),
            ("MER base (kcal/día)", f"{_mer_base3:.1f}" if _mer_base3 else "—"),
            ("Factor fisiológico", f"{_factor_fis3:.2f}" if _factor_fis3 else "—"),
            ("Ajuste por BCS", "Sí" if _bcs3 != 5 else "No"),
            ("Ajuste senior (×0.85)", "Sí" if _senior3 else "No"),
            ("MER final ajustado (kcal/día)", f"{_mer_final3:.1f}"),
        ]
        with st.expander("Ver detalle de requerimientos energéticos", expanded=False):
            for _k, _v in _en_rows:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:6px 0;border-bottom:1px solid #eef0f4;'>"
                    f"<span style='font-weight:600'>{_k}</span><span>{_v}</span></div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("Completa el perfil de la mascota en la pestaña **Perfil de Mascota** para ver los requerimientos energéticos.")

    # ── SECCIÓN 4: ANÁLISIS DEL ALIMENTO ──────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🍽️ Análisis del Alimento")

    if _food_name3 and _food_data3:
        _fa1, _fa2 = st.columns(2)
        with _fa1:
            st.markdown(f"**Alimento seleccionado:** {_food_name3}")
            st.metric("⚡ ME (kcal/100g)", f"{_me3:.2f}")
            st.metric("🥣 Gramos evaluados (g/día)", f"{_gramos3:.0f}")
            st.metric("🔥 Energía aportada (kcal/día)", f"{_aporte3:.1f}")
        with _fa2:
            _comp_rows = [
                ("Proteína Bruta (PB %)", _food_data3.get("PB", 0)),
                ("Grasa (EE %)", _food_data3.get("EE", 0)),
                ("Cenizas (%)", _food_data3.get("Ash", 0)),
                ("Humedad (%)", _food_data3.get("Humidity", 0)),
                ("Fibra Cruda (FC %)", _food_data3.get("FC", 0)),
                ("ENA (%)", round(_food_ena3, 2)),
            ]
            for _n, _v in _comp_rows:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:5px 0;border-bottom:1px solid #eef0f4;font-size:0.93rem;'>"
                    f"<span>{_n}</span><span><b>{_v:.2f}</b></span></div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("Selecciona un alimento en la pestaña **Análisis** para ver el análisis nutricional.")

    # ── SECCIÓN 5: DECISIÓN NUTRICIONAL ───────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("✅ Decisión Nutricional")

    if _datos_completos:
        _clase_dec = (
            "low" if _cobertura3 < 90
            else "adequate" if _cobertura3 <= 110
            else "moderate" if _cobertura3 <= 130
            else "high"
        )
        _colores_dec = {
            "low": ("#2176FF", "#e8f0fe"),
            "adequate": ("#52B788", "#e9f7f0"),
            "moderate": ("#FFB703", "#fff8e1"),
            "high": ("#F4845F", "#fdeee8"),
        }
        _color_border, _color_bg = _colores_dec[_clase_dec]
        st.markdown(
            f"<div style='background:{_color_bg};border-left:5px solid {_color_border};"
            f"padding:14px 18px;border-radius:6px;margin-bottom:10px;'>"
            f"<div style='font-size:1.1rem;font-weight:700;color:{_color_border};'>{_resultado3}</div>"
            f"<div style='font-size:0.95rem;margin-top:6px;'>{_interpretacion3}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Complete el perfil de la mascota y el análisis del alimento para ver la decisión nutricional.")

    # ── SECCIÓN 6: CANTIDAD RECOMENDADA ───────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Cantidad Recomendada")

    if _datos_completos and _me3 > 0:
        _rng_min3 = _gramos_rec3 * 0.9
        _rng_max3 = _gramos_rec3 * 1.1
        _cq1, _cq2, _cq3 = st.columns(3)
        with _cq1:
            st.metric("📌 Gramos recomendados (g/día)", f"{_gramos_rec3:.0f}")
        with _cq2:
            _signo_g = "+" if _dif_g3 > 0 else ""
            st.metric("📏 Diferencia vs evaluado (g)", f"{_signo_g}{_dif_g3:.0f}")
        with _cq3:
            st.metric("↔️ Rango aceptable (±10%)", f"{_rng_min3:.0f} – {_rng_max3:.0f} g")
    else:
        st.info("Completa el análisis de alimento para obtener la cantidad recomendada.")

    # ── SECCIÓN 7: RECOMENDACIONES ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 Recomendaciones")

    if _recomendaciones3:
        for _i, _rec in enumerate(_recomendaciones3, 1):
            st.markdown(
                f"<div style='padding:8px 12px 8px 32px;border-bottom:1px solid #eef0f4;"
                f"position:relative;font-size:0.95rem;'>"
                f"<span style='position:absolute;left:8px;color:#52B788;font-weight:bold;'>✓</span>"
                f"{_rec}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Las recomendaciones se generan automáticamente al completar el perfil.")

    # ── SECCIÓN 8 & 9: EXPORTACIÓN ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📥 Descargar Informes")

    _fecha3 = datetime.date.today()
    _nombre_archivo3 = _nombre3.replace(" ", "_") if _nombre3 != "—" else "Mascota"

    # Preparar datos para exportadores
    _datos_energeticos3 = {
        "edad": _edad3,
        "peso": _peso3,
        "bcs": _bcs3,
        "etapa": _etapa3,
        "estado_corporal": _estado_corp3,
        "riesgo_nutricional": _riesgo3,
        "condicion": _condicion3,
        "rer": _rer3 or 0.0,
        "mer_base": _mer_base3 or 0.0,
        "diagnostico": _diagnostico3,
        "recomendaciones": _recomendaciones3,
    }
    _rng_min_exp = _gramos_rec3 * 0.9 if _datos_completos else 0.0
    _rng_max_exp = _gramos_rec3 * 1.1 if _datos_completos else 0.0

    # Obtener energía desglosada del alimento para exportar
    _food_eb3 = calculate_energy_breakdown(_food_data3) if _food_data3 else {}

    _datos_alimento3 = {
        "alimento": _food_name3 or "—",
        "me": _me3,
        "gramos": _gramos3,
        "aporte": _aporte3,
        "cobertura": _cobertura3,
        "recomendados": _gramos_rec3,
        "rango_min": _rng_min_exp,
        "rango_max": _rng_max_exp,
        "decision": _resultado3,
        "interpretacion": _interpretacion3,
        "pb": _food_data3.get("PB", 0) if _food_data3 else 0,
        "ee": _food_data3.get("EE", 0) if _food_data3 else 0,
        "ash": _food_data3.get("Ash", 0) if _food_data3 else 0,
        "humidity": _food_data3.get("Humidity", 0) if _food_data3 else 0,
        "fc": _food_data3.get("FC", 0) if _food_data3 else 0,
        "ena": _food_ena3,
        "ms": _food_energy3.get("MS", 0) if _food_energy3 else 0,
        "ge": _food_eb3.get("GE", 0) if _food_eb3 else 0,
        "de_pct": _food_energy3.get("DE_pct", 0) if _food_energy3 else 0,
        "de": _food_energy3.get("DE", 0) if _food_energy3 else 0,
    }

    # Construir dict mascota completo con valores de session_state
    _mascota_export3 = {
        "nombre": _nombre3,
        "especie": _especie3,
    }

    # Texto explicativo antes de los botones
    st.info(
        "**📌 IMPORTANTE - Dos formatos disponibles:**\n\n"
        "1️⃣ **Excel (.xlsx) - Ficha Maestra de Seguimiento**\n"
        "- Archivo base que funciona como historial del paciente\n"
        "- Consérvelo para llevar un registro entre visitas\n"
        "- Permite comparar evolución: peso, BCS, requerimientos energéticos, alimento evaluado, cobertura nutricional\n"
        "- Se acumula histórico de visitas para tomar decisiones clínicas\n\n"
        "2️⃣ **HTML (.html) - Informe Visual de Hoy**\n"
        "- Resumen formal y profesional de la visita actual\n"
        "- Apto para imprimir o enviar al cliente\n"
        "- Información visual clara"
    )

    _col_xlsx, _col_html = st.columns(2)

    with _col_xlsx:
        try:
            _nutrientes_ref3 = (
                NUTRIENTES_REFERENCIA_PERRO if _especie3 == "perro" else NUTRIENTES_REFERENCIA_GATO
            )
            _xlsx_bytes = exportar_ficha_maestra_excel(
                mascota=_mascota_export3,
                datos_energeticos=_datos_energeticos3,
                datos_alimento=_datos_alimento3,
                mer_final=_mer_final3 or 0.0,
                senior_applied=_senior3,
                recomendaciones=_recomendaciones3,
                nutrientes_ref=_nutrientes_ref3,
                cob_pb=_cob_pb3,
                cob_ee=_cob_ee3,
            )
            st.download_button(
                label="📥 Descargar ficha maestra de seguimiento (.xlsx)",
                data=_xlsx_bytes,
                file_name=f"UYWA_Ficha_Nutricional_{_nombre_archivo3}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_ficha_maestra",
            )
        except Exception as _e:
            st.error(f"Error al generar ficha maestra: {_e}")

    with _col_html:
        try:
            _html_str = exportar_a_html(
                _mascota_export3, _datos_energeticos3, _datos_alimento3,
                _mer_final3 or 0.0, _diagnostico3, _recomendaciones3
            )
            st.download_button(
                label="📄 Descargar informe visual de hoy (HTML)",
                data=_html_str,
                file_name=f"UYWA_Informe_{_nombre_archivo3}_{_fecha3.strftime('%d%m%Y')}.html",
                mime="text/html",
                use_container_width=True,
                key="download_html_informe",
            )
        except Exception as _e:
            st.error(f"Error al generar informe HTML: {_e}")

