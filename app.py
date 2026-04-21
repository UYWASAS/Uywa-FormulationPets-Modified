# ======================== BLOQUE 1: IMPORTS Y UTILIDADES ========================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random

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
from PIL import Image
import io

# Umbral de cobertura energética para alertas visuales (%)
ENERGY_COVERAGE_THRESHOLD = 110

# Paleta de colores para gráficos radar
RADAR_CHART_COLORS = ["#2176FF", "#FFB703", "#52B788", "#F4845F", "#8E9AAF", "#E74C3C"]

# ======================== DEFINICIÓN GLOBAL DE FACTORES ========================
FACTORES_CONDICION = {
    "perro": {
        "adulto": {
            "Castrado": 1.6,
            "Entero": 1.8,
            "Tendencia obesidad o inactivo": [1.2, 1.4],
            "Obeso": 1.0,
            "Bajo peso": [1.4, 1.6],
            "Gestación (primera mitad)": 1.8,
            "Gestación (segunda mitad)": [2.5, 3.0],
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
            "Gestación (inicio)": 1.6,
            "Gestación (incremento hasta parto)": 2.0,
            "Lactancia": [2.0, 6.0],
        },
        "cachorro": {
            "Destete a 4 meses": 3.0,
            "5 meses hasta adulto": 2.0,
        },
    },
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

    # Mostrar formulario para editar el perfil de la mascota
    mascota = profile.get("mascota", {})
    nombre_mascota = st.text_input("Nombre de la mascota", value=mascota.get("nombre", "Mascota"), key="nombre_mascota")
    especie = st.selectbox("Especie", ["perro", "gato"], index=["perro", "gato"].index(mascota.get("especie", "perro").lower()), key="especie_mascota")
    edad = st.number_input("Edad en años", min_value=0.1, max_value=20.0, value=mascota.get("edad", 1.0), step=0.1, key="edad_mascota")
    peso = st.number_input("Peso en kg", min_value=0.1, max_value=200.0, value=mascota.get("peso", 12.0), step=0.1, key="peso_mascota")
    etapa = st.selectbox("Etapa de vida", ["adulto", "cachorro"], index=["adulto", "cachorro"].index(mascota.get("etapa", "adulto").lower()), key="etapa_mascota")

    # Condición fisiológica/productiva dependiente de la etapa
    if etapa == "adulto":
        opciones_condicion = ["Castrado", "Entero", "Gestación (Primera mitad)", "Gestación (Segunda mitad)", "Lactancia"]
    elif etapa == "cachorro":
        opciones_condicion = ["Destete a 4 meses", "5 meses hasta adulto"]

    condicion_predeterminada = mascota.get("condicion", "Castrado")
    if condicion_predeterminada not in opciones_condicion:
        condicion_predeterminada = opciones_condicion[0]
    condicion = st.selectbox(
        "Condición fisiológica/productiva",
        opciones_condicion,
        index=opciones_condicion.index(condicion_predeterminada),
        key="condicion_mascota"
    )

    # Condición Corporal (BCS) con bloqueo según condición seleccionada
    bcs_disabled = etapa == "cachorro" and condicion == "Destete a 4 meses"
    bcs = st.slider(
        "Condición Corporal (BCS)",
        min_value=1,
        max_value=9,
        value=mascota.get("bcs", 5),
        key="bcs_mascota",
        disabled=bcs_disabled
    )

    # Botón para guardar perfil
    if st.button("Guardar perfil de mascota"):
        mascota_actualizada = {
            "nombre": st.session_state["nombre_mascota"],
            "especie": st.session_state["especie_mascota"].lower(),
            "edad": st.session_state["edad_mascota"],
            "peso": st.session_state["peso_mascota"],
            "etapa": st.session_state["etapa_mascota"].lower(),
            "condicion": condicion,
            "bcs": st.session_state.get("bcs_mascota", 5),
        }
        profile["mascota"] = mascota_actualizada
        update_and_save_profile(profile)
        st.success("Perfil actualizado correctamente.")

    # Visualización del perfil actualizado
    st.markdown(
        f"""
        <div style="background-color: #eef4fc; padding: 20px; border-radius: 12px; box-shadow: 0px 2px 8px #d6e0f0;">
            <p style="font-size: 20px; margin: 0; text-align: center;"><b>{mascota.get('nombre', 'Mascota')}</b></p>
            <ul style="margin: 0; padding: 0; list-style: none; font-size: 16px; color: #2c3e50;">
                <li>🐾 <b>Especie:</b> {mascota.get('especie', 'No definido')}</li>
                <li>⏳ <b>Edad:</b> {fmt2(mascota.get('edad', 0.0))} años</li>
                <li>⚖️ <b>Peso:</b> {fmt2(mascota.get('peso', 12.0))} kg</li>
                <li>🌟 <b>Etapa:</b> {mascota.get('etapa', 'adulto')}</li>
                <li>📏 <b>Condición Corporal (BCS):</b> {mascota.get('bcs', 5)}</li>
                <li>🛠️ <b>Condición Fisiológica/Productiva:</b> {mascota.get('condicion', 'No definida')}</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Cálculo del RER y MER
    try:
        energia_basal_actual = calcular_rer(peso)
        factores_etapa = FACTORES_CONDICION.get(especie, {}).get(etapa, {}).get(condicion, None)
        if factores_etapa is None:
            raise ValueError(f"Condición desconocida para '{especie}'.")
        factor_fisiologico = factores_etapa if isinstance(factores_etapa, (int, float)) else factores_etapa[0]
        mer_actual = energia_basal_actual * factor_fisiologico

        # Ajuste por BCS
        factores_bcs = {6: 0.9, 7: 0.8, 8: 0.7, 9: 0.6, 4: 1.1, 3: 1.2, 2: 1.3, 1: 1.4}
        peso_objetivo = peso * factores_bcs.get(bcs, 1.0) if bcs != 5 and not bcs_disabled else "-"
        energia_basal_objetivo = calcular_rer(peso_objetivo) if bcs != 5 and not bcs_disabled else "-"
        mer_final = energia_basal_objetivo * factor_fisiologico if bcs != 5 and not bcs_disabled else mer_actual

        # Guardar MER ajustada en el estado de sesión
        st.session_state["energia_actual"] = mer_final

        # Tabla de energías calculadas
        energia_data = [
            {"Tipo": "RER Actual", "Valor": f"{fmt2(energia_basal_actual)} kcal/día", "Descripción": "Energía necesaria en reposo para mantener funciones básicas como respirar y digerir."},
            {"Tipo": "MER Actual (RER × Factor Fisiológico)", "Valor": f"{fmt2(mer_actual)} kcal/día", "Descripción": "Energía diaria necesaria según la condición productiva y fisiológica."},
            {"Tipo": "Peso Objetivo", "Valor": f"{fmt2(peso_objetivo)} kg" if peso_objetivo != "-" else "-", "Descripción": "Peso estimado para ajustar según la condición corporal (BCS)."},
            {"Tipo": "RER Objetivo", "Valor": f"{fmt2(energia_basal_objetivo)} kcal/día" if energia_basal_objetivo != "-" else "-", "Descripción": "Energía en reposo recalculada con el peso objetivo."},
            {"Tipo": "MER Ajustada Final", "Valor": f"{fmt2(mer_final)} kcal/día", "Descripción": "Energía total diaria necesaria tras ajustes por BCS y condición."},
        ]

        # Estilo de la tabla HTML de energías
        st.markdown(
            """
            <style>
            .energy-table {
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
                font-size: 15px;
                text-align: center;
                border-radius: 8px;
                overflow: hidden;
            }
            .energy-table th {
                background-color: #4A5568; /* Tono ajustado */
                color: #fff;
                padding: 10px;
                font-weight: bold;
            }
            .energy-table td {
                padding: 10px;
            }
            .energy-table tr:nth-child(even) {
                background-color: #edf2f7;
            }
            .energy-table tr:nth-child(odd) {
                background-color: #ffffff;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Generar la tabla HTML para energías
        html_table = "<table class='energy-table'><thead><tr><th>Tipo de Energía</th><th>Valor</th><th>Descripción</th></tr></thead><tbody>"
        for entry in energia_data:
            html_table += f"<tr><td>{entry['Tipo']}</td><td>{entry['Valor']}</td><td>{entry['Descripción']}</td></tr>"
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)

        # Cálculo y tabla de nutrientes ajustados
        nutrientes_ref = NUTRIENTES_REFERENCIA_PERRO if especie == "perro" else NUTRIENTES_REFERENCIA_GATO
        nutrientes_especie_etapa = nutrientes_ref.get(etapa, {})

        # Cantidad de dieta (kg) necesaria para cubrir el MER del animal.
        # 4000 kcal/kg MS es la densidad energética de referencia usada en nutrient_reference.py
        kg_dieta_necesaria = mer_final / 4000.0

        requerimientos_ajustados = []
        for nutriente, valores in nutrientes_especie_etapa.items():
            unidad = valores.get("unit", "")
            min_valor = valores.get("min", None)
            max_valor = valores.get("max", None)

            # Convertir según el tipo de unidad al valor diario absoluto
            if unidad == "%":
                # % MS → gramos por día: (% / 100) × kg_dieta × 1000
                min_ajustado = (min_valor / 100.0) * kg_dieta_necesaria * 1000 if min_valor is not None else None
                max_ajustado = (max_valor / 100.0) * kg_dieta_necesaria * 1000 if max_valor is not None else None
                nueva_unidad = "g"
            elif unidad in ["mg/kg", "UI/kg", "IU/kg", "µg/kg"]:
                # valor/kg MS → valor por día: valor × kg_dieta
                unidad_base = unidad.replace("/kg", "")
                min_ajustado = min_valor * kg_dieta_necesaria if min_valor is not None else None
                max_ajustado = max_valor * kg_dieta_necesaria if max_valor is not None else None
                nueva_unidad = unidad_base
            else:
                # Mantener tal cual (ratios u otras unidades sin conversión)
                min_ajustado = min_valor
                max_ajustado = max_valor
                nueva_unidad = unidad if unidad else "-"

            requerimientos_ajustados.append({
                "Nutriente": nutriente,
                "Min Ajustado": fmt2(min_ajustado) if min_ajustado is not None else "-",
                "Max Ajustado": fmt2(max_ajustado) if max_ajustado is not None else "-",
                "Unidad": nueva_unidad
            })

        # Persistencia de la tabla en el estado de sesión
        df_nutrientes_ajustados = pd.DataFrame(requerimientos_ajustados)
        st.session_state["tabla_requerimientos_base"] = df_nutrientes_ajustados.copy()

        # Estilo para la tabla de nutrientes ajustados
        st.markdown(
            """
            <style>
            .nutrients-table {
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
                font-size: 15px;
                text-align: center;
                border-radius: 8px;
                overflow: hidden;
            }
            .nutrients-table th {
                background-color: #4A5568; /* Tono ajustado */
                color: #fff;
                padding: 10px;
                font-weight: bold;
            }
            .nutrients-table td {
                padding: 10px;
            }
            .nutrients-table tr:nth-child(even) {
                background-color: #edf2f7;
            }
            .nutrients-table tr:nth-child(odd) {
                background-color: #ffffff;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Generar la tabla HTML para nutrientes ajustados
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
    st.header("Resumen general y exportación")

    # --- CSS de tabla bonita (igual que requerimientos) ---
    st.markdown("""
        <style>
        .styled-table {
            border-collapse: collapse;
            margin: 10px 0 20px 0;
            font-size: 16px;
            min-width: 390px;
            width: 90%;
            border-radius: 14px 14px 0 0;
            overflow: hidden;
            box-shadow: 0 2px 10px #e3ecf7;
        }
        .styled-table th {
            background-color: #19345c !important;
            color: #fff;
            text-align: center;
            font-weight: bold;
            padding: 10px 7px;
            font-size: 17px;
            border-right: 1px solid #e3ecf7;
        }
        .styled-table td {
            padding: 7px 7px;
            text-align: center;
            border-bottom: 1px solid #e3ecf7;
            font-size: 16px;
        }
        .styled-table tr:nth-child(even) {
            background-color: #f3f6fa;
        }
        .styled-table tr:nth-child(odd) {
            background-color: #eaf3fc;
        }
        .styled-table td.min-cell, .styled-table td.obt-cell {
            font-weight: bold;
            color: #23783d;
            background: #e0f7e9;
            border-radius: 6px;
        }
        .styled-table td.fail-cell {
            color: #c0392b;
            background: #ffeaea;
        }
        .photo-box {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 140px;
            background: #eaf3fc;
            border-radius: 12px;
            color: #19345c;
            font-size: 18px;
            font-weight: 600;
            border: 1px solid #e3ecf7;
            margin-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    # === 1. Perfil de la mascota ===
    perfil = st.session_state.get("profile", {})
    mascota = perfil.get("mascota", {})
    st.subheader("Perfil de la mascota")
    cols = st.columns([1, 3])

    with cols[0]:
        # --- FOTO UX MEJORADO ---
        foto_guardada = st.session_state.get("mascota_foto", None)
        nueva_foto = None
        show_preview = False
        img_preview = None

        # 1. Si NO hay foto guardada, mostrar uploader
        if foto_guardada is None:
            nueva_foto = st.file_uploader(
                "Cargar o reemplazar foto",
                type=["png", "jpg", "jpeg"],
                key="foto_resumen",
                label_visibility="visible"
            )
            if nueva_foto is not None:
                try:
                    img_preview = Image.open(nueva_foto)
                    st.image(img_preview, width=130)
                    show_preview = True
                except Exception:
                    st.warning("No se pudo cargar la imagen seleccionada.")
            else:
                st.markdown("<div class='photo-box'>No hay foto disponible.</div>", unsafe_allow_html=True)

            # Solo mostrar botón de guardar si hay preview
            if show_preview and st.button("Guardar foto de la mascota", key="guardar_foto_resumen"):
                st.session_state["mascota_foto"] = nueva_foto.getvalue()
                st.success("Foto guardada correctamente.")
                st.rerun()

        # 2. Si HAY foto guardada, mostrar solo imagen y botón eliminar
        else:
            try:
                if isinstance(foto_guardada, Image.Image):
                    st.image(foto_guardada, width=130)
                elif isinstance(foto_guardada, bytes):
                    st.image(Image.open(io.BytesIO(foto_guardada)), width=130)
            except Exception:
                st.markdown("<div class='photo-box'>No hay foto disponible.</div>", unsafe_allow_html=True)
            if st.button("Eliminar foto de la mascota", key="eliminar_foto_resumen"):
                del st.session_state["mascota_foto"]
                st.rerun()

    with cols[1]:
        st.markdown(f"""
        - <b>Nombre:</b> {mascota.get('nombre', 'No definido')}
        - <b>Especie:</b> {mascota.get('especie', 'No definido')}
        - <b>Edad:</b> {mascota.get('edad', 'No definido')} años
        - <b>Peso:</b> {mascota.get('peso', 'No definido')} kg
        - <b>Condición:</b> {mascota.get('condicion', 'No definido')}
        """, unsafe_allow_html=True)

    # === 2. Requerimiento Energético del Animal ===
    st.subheader("⚡ Requerimiento Energético del Animal")
    mer_animal = st.session_state.get("energia_actual", None)
    energia_basal = calcular_rer(mascota.get("peso", 0)) if mascota.get("peso") else None

    if mer_animal is not None and energia_basal is not None:
        factor_cond = round(mer_animal / energia_basal, 2) if energia_basal and energia_basal > 1e-6 else "-"
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("🔋 RER (Energía en Reposo)", f"{energia_basal:.1f} kcal/día")
        with col_r2:
            st.metric("🎯 MER (Requerimiento Diario)", f"{mer_animal:.1f} kcal/día")
        with col_r3:
            st.metric("⚙️ Factor de Condición", str(factor_cond))
    else:
        st.info("Completa el perfil de la mascota en la pestaña **Perfil de Mascota** para ver los requerimientos energéticos.")

    # === 3. Composición de Alimentos Seleccionados (food_database) ===
    st.subheader("🥗 Composición Nutricional de Alimentos Balanceados")

    food_names_all = get_food_names_db()
    selected_alimentos = st.multiselect(
        "Selecciona alimentos para ver su composición",
        food_names_all,
        default=food_names_all[:2] if len(food_names_all) >= 2 else food_names_all,
        key="resumen_alimentos_selector",
    )

    if selected_alimentos:
        comp_alimentos_rows = []
        for fname in selected_alimentos:
            fdata = FOODS.get(fname, {})
            if fdata:
                ena = calc_ena_food(fdata)
                energy_f = calc_energy_food(fdata)
                comp_alimentos_rows.append({
                    "Alimento": fname,
                    "Categoría": fdata.get("category", ""),
                    "PB (%)": fdata["PB"],
                    "EE (%)": fdata["EE"],
                    "Cenizas (%)": fdata["Ash"],
                    "Humedad (%)": fdata["Humidity"],
                    "FC (%)": fdata["FC"],
                    "ENA (%)": round(ena, 2),
                    "ME (kcal/100g)": round(energy_f["ME"], 2),
                })
        comp_alimentos_df = pd.DataFrame(comp_alimentos_rows)
        st.dataframe(comp_alimentos_df.set_index("Alimento"), use_container_width=True)

        # Gráfico radar de macronutrientes por alimento
        st.markdown("**Gráfico Radar: Macronutrientes por Alimento**")
        radar_fig = go.Figure()
        radar_cats = ["PB (%)", "EE (%)", "Cenizas (%)", "FC (%)", "ENA (%)"]
        colors_radar = RADAR_CHART_COLORS
        for idx, fname in enumerate(selected_alimentos):
            fdata = FOODS.get(fname, {})
            if fdata:
                ena = calc_ena_food(fdata)
                vals = [fdata["PB"], fdata["EE"], fdata["Ash"], fdata["FC"], round(ena, 2)]
                vals_closed = vals + [vals[0]]
                cats_closed = radar_cats + [radar_cats[0]]
                radar_fig.add_trace(go.Scatterpolar(
                    r=vals_closed,
                    theta=cats_closed,
                    fill="toself",
                    name=fname,
                    line_color=colors_radar[idx % len(colors_radar)],
                    opacity=0.6,
                ))
        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
            height=420,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
            margin=dict(t=40, b=100, l=40, r=40),
        )
        st.plotly_chart(radar_fig, use_container_width=True)

        # Aporte Energético Total si hay MER
        if mer_animal and mer_animal > 0:
            st.markdown("**Aporte Energético Total de los Alimentos Seleccionados**")
            aporte_total_kcal = 0.0
            aporte_por_alimento = []
            for fname in selected_alimentos:
                fdata = FOODS.get(fname, {})
                if fdata:
                    gramos_key = f"gramos_alimento_{fname}"
                    gramos_sel = st.session_state.get(gramos_key, 0.0)
                    energy_f = calc_energy_food(fdata)
                    aporte_kcal = (energy_f["ME"] / 100.0) * gramos_sel
                    aporte_total_kcal += aporte_kcal
                    aporte_por_alimento.append({
                        "Alimento": fname,
                        "Gramos/día": gramos_sel,
                        "ME (kcal/100g)": round(energy_f["ME"], 2),
                        "Aporte (kcal/día)": round(aporte_kcal, 2),
                    })
            aporte_df = pd.DataFrame(aporte_por_alimento)
            st.dataframe(aporte_df.set_index("Alimento"), use_container_width=True)

            cobertura_total = (aporte_total_kcal / mer_animal) * 100.0
            st.metric(
                "📊 Cobertura Energética Total",
                f"{cobertura_total:.1f}%",
                delta=f"{aporte_total_kcal:.1f} kcal de {mer_animal:.1f} kcal requeridas",
            )

            # Gráfico de barras: Requerimiento vs Aporte Total
            fig_comp_bar = go.Figure()
            fig_comp_bar.add_trace(go.Bar(
                name="MER Requerida",
                x=["Energía (kcal/día)"],
                y=[mer_animal],
                marker_color="#8E9AAF",
                text=[f"{mer_animal:.1f} kcal"],
                textposition="outside",
            ))
            fig_comp_bar.add_trace(go.Bar(
                name="Aporte Total Alimentos",
                x=["Energía (kcal/día)"],
                y=[aporte_total_kcal],
                marker_color="#2176FF" if cobertura_total <= ENERGY_COVERAGE_THRESHOLD else "#FFB703",
                text=[f"{aporte_total_kcal:.1f} kcal ({cobertura_total:.0f}%)"],
                textposition="outside",
            ))
            fig_comp_bar.update_layout(
                barmode="group",
                title=dict(
                    text="Requerimiento Energético vs Aporte Total",
                    font=dict(size=15, family="Montserrat, sans-serif"),
                ),
                yaxis_title="kcal / día",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=360,
                margin=dict(t=60, b=40, l=60, r=40),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_comp_bar, use_container_width=True)
    else:
        st.info("Selecciona al menos un alimento para ver su composición nutricional.")

    # === 4. Dieta (proporciones y gramos) ===
    st.subheader("Composición de la dieta formulada")
    result = st.session_state.get("last_result", None)
    diet = result.get("diet", {}) if result is not None else {}
    dosis_g = st.session_state.get("dosis_dieta_g_formulacion", 1000)
    ingredientes_df_filtrado = st.session_state.get("ingredients_df", None)
    ingredientes_sel = list(ingredientes_df_filtrado["Ingrediente"]) if ingredientes_df_filtrado is not None and "Ingrediente" in ingredientes_df_filtrado.columns else []

    comp_data = []
    for ing in ingredientes_sel:
        porcentaje = diet.get(ing, 0.0)
        gramos = (porcentaje / 100.0) * dosis_g
        comp_data.append({
            "Ingrediente": ing,
            "% Inclusión": fmt2(porcentaje),
            "Gramos en dosis": fmt2(gramos)
        })
    res_df = pd.DataFrame(comp_data)

    if not res_df.empty and "Ingrediente" in res_df.columns:
        html_table = "<table class='styled-table'><tr><th>Ingrediente</th><th>% Inclusión</th><th>Gramos en dosis</th></tr>"
        for _, row in res_df.iterrows():
            html_table += (
                f"<tr>"
                f"<td>{row['Ingrediente']}</td>"
                f"<td>{row['% Inclusión']}</td>"
                f"<td>{row['Gramos en dosis']}</td>"
                f"</tr>"
            )
        html_table += "</table>"
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("No hay ingredientes para mostrar la dieta. Por favor, formula primero la dieta y selecciona ingredientes.")

    # === 5. Precio de la dieta ===
    st.subheader("Precio de la dieta")
    if result is not None:
        total_cost = result.get("cost", 0)
        precio_kg = total_cost / 100 if total_cost else 0
        precio_dosis = (precio_kg * dosis_g) / 1000
    else:
        total_cost = 0
        precio_kg = 0
        precio_dosis = 0
    st.markdown(f"- <b>Costo total (por 100 kg):</b> ${fmt2(total_cost)}", unsafe_allow_html=True)
    st.markdown(f"- <b>Precio por kg:</b> ${fmt2(precio_kg)}", unsafe_allow_html=True)
    st.markdown(f"- <b>Precio por dosis diaria:</b> ${fmt2(precio_dosis)}", unsafe_allow_html=True)

    # === 6. Tabla Unificada de Requerimientos y Composición Obtenida ===
    st.subheader("Requerimientos y composición obtenida (por kg dieta)")
    user_requirements = st.session_state.get("nutrientes_requeridos", {})
    nutritional_values = result.get("nutritional_values", {}) if result is not None else {}

    unified_list = []
    for nut, req in user_requirements.items():
        min_v = fmt2(req.get("min", ""))
        max_v = fmt2(req.get("max", ""))
        obtenido = nutritional_values.get(nut, None)
        unidad = req.get("unit", "")
        cumple = "✔️"
        try:
            min_f = float(req.get("min", 0))
            obt_f = float(obtenido) if obtenido not in [None, "", "None"] else 0
            if obt_f < min_f:
                cumple = "❌"
        except Exception:
            cumple = "❌"
        try:
            max_f = float(req.get("max", 0))
            obt_f = float(obtenido) if obtenido not in [None, "", "None"] else 0
            if max_f > 0 and obt_f > max_f:
                cumple = "❌"
        except Exception:
            pass
        unified_list.append({
            "Nutriente": nut,
            "Mín": min_v,
            "Máx": max_v,
            "Obtenido": fmt2(obtenido) if obtenido is not None and obtenido != "" else "",
            "Unidad por kg de dieta": unidad,
            "Cumple": cumple
        })
    unified_df = pd.DataFrame(unified_list)

    if not unified_df.empty and "Nutriente" in unified_df.columns:
        html_table = "<table class='styled-table'><tr><th>Nutriente</th><th>Mín</th><th>Máx</th><th>Obtenido</th><th>Unidad por kg de dieta</th><th>Cumple</th></tr>"
        for _, row in unified_df.iterrows():
            min_cell = f"<td class='min-cell'>{row['Mín']}</td>"
            max_cell = f"<td>{row['Máx']}</td>"
            obt_cell = f"<td class='obt-cell'>{row['Obtenido']}</td>"
            cumple_cell = f"<td>{row['Cumple']}</td>"
            html_table += (
                f"<tr>"
                f"<td>{row['Nutriente']}</td>"
                f"{min_cell}"
                f"{max_cell}"
                f"{obt_cell}"
                f"<td>{row['Unidad por kg de dieta']}</td>"
                f"{cumple_cell}"
                f"</tr>"
            )
        html_table += "</table>"
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("No hay requerimientos ni composición nutricional para mostrar.")

    # === 7. Exportar a Excel ===
    st.subheader("Exportar resumen a Excel")

    perfil_df = pd.DataFrame([mascota])
    dieta_df = res_df
    precio_df = pd.DataFrame([{
        "Costo total (100kg)": fmt2(total_cost),
        "Precio por kg": fmt2(precio_kg),
        "Precio por dosis": fmt2(precio_dosis)
    }])
    energia_df_export = pd.DataFrame([{
        "RER (kcal/día)": round(energia_basal, 2) if energia_basal else "-",
        "MER (kcal/día)": round(mer_animal, 2) if mer_animal else "-",
        "Factor de condición": factor_cond if mer_animal and energia_basal else "-",
    }])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        perfil_df.to_excel(writer, sheet_name='Perfil Mascota', index=False)
        energia_df_export.to_excel(writer, sheet_name='Requerimiento Energético', index=False)
        if selected_alimentos and not comp_alimentos_df.empty:
            comp_alimentos_df.reset_index().to_excel(writer, sheet_name='Alimentos Balanceados', index=False)
        dieta_df.to_excel(writer, sheet_name='Dieta', index=False)
        precio_df.to_excel(writer, sheet_name='Precio', index=False)
        unified_df.to_excel(writer, sheet_name='Requerimientos y Composición', index=False)
    excel_data = output.getvalue()

    st.download_button(
        label="Descargar resumen en Excel",
        data=excel_data,
        file_name="Resumen_dieta_uywa.xlsx",
        mime="application/vnd/openxmlformats-officedocument/spreadsheetml.sheet"
    )

