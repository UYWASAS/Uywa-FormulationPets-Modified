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
    st.image("asstes/logo.png", use_column_width=True)
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
    "Formulación",
    "Resultados",
    "Comparativo",
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

# ======================== BLOQUE 6: AJUSTE DE REQUERIMIENTOS ========================
with tabs[1]:
    with st.expander("Ajuste de requerimientos nutricionales según dosis diaria", expanded=True):
        # Obtener especie y etapa: primero desde widgets de Tab 1 (session state),
        # con fallback al perfil guardado
        especie_tab2 = (
            st.session_state.get("especie_mascota")
            or profile.get("mascota", {}).get("especie", None)
        )
        etapa_tab2 = (
            st.session_state.get("etapa_mascota")
            or profile.get("mascota", {}).get("etapa", None)
        )
        if not especie_tab2 or not etapa_tab2:
            st.warning("⚠️ Por favor completa el Perfil (Tab 1) con especie y etapa.")
            st.stop()

        # Cargar directamente los datos FEDIAF base a 1000 kcal (independiente del MER)
        nutrientes_ref_tab2 = NUTRIENTES_REFERENCIA_PERRO if especie_tab2 == "perro" else NUTRIENTES_REFERENCIA_GATO
        nutrientes_especie_etapa_tab2 = nutrientes_ref_tab2.get(etapa_tab2, {})

        requerimientos_base_tab2 = []
        for nutriente, valores in nutrientes_especie_etapa_tab2.items():
            requerimientos_base_tab2.append({
                "Nutriente": nutriente,
                "Min": valores.get("min", None),
                "Max": valores.get("max", None),
                "Unidad": valores.get("unit", "")
            })
        df_base = pd.DataFrame(requerimientos_base_tab2)

        # Entrada para dosis diaria de dieta
        dosis_g = st.number_input(
            "Dosis diaria de dieta (g/día)", min_value=10, max_value=3000, value=1000, step=10, key="dosis_dieta_g_formulacion"
        )

        # Ajustar valores base (a 1000 kcal) a la dosis de dieta seleccionada
        def escalar_por_dosis(val, dosis):
            return round((val / 1000) * dosis, 2) if pd.notna(val) and val is not None else None

        df_base["Min por kg dieta"] = df_base["Min"].apply(lambda x: escalar_por_dosis(x, dosis_g))
        df_base["Max por kg dieta"] = df_base["Max"].apply(lambda x: escalar_por_dosis(x, dosis_g))

        # Agregar fila de Energía Metabolizable con el estándar FEDIAF (1000 kcal/kg)
        if not any(df_base["Nutriente"].str.contains("Energía metabolizable", na=False)):
            em_row = pd.DataFrame({
                "Nutriente": ["Energía metabolizable (EM)"],
                "Min": [4000.0],
                "Max": [None],
                "Min por kg dieta": [4000.0],
                "Max por kg dieta": [None],
                "Unidad": ["kcal/kg"]
            })
            df_base = pd.concat([em_row, df_base], ignore_index=True)

        # Guardar datos base FEDIAF y dosis para uso en Tab 3
        st.session_state["fediaf_requirements_used"] = df_base[["Nutriente", "Min", "Max", "Unidad"]].copy()
        st.session_state["dosis_dieta_formulacion"] = dosis_g

        df_base = df_base.round(2)

        # Visualización con tabla editable
        editable_cols = {
            "Min por kg dieta": st.column_config.NumberColumn("Min por kg dieta", min_value=0.0, step=0.01),
            "Max por kg dieta": st.column_config.NumberColumn("Max por kg dieta", min_value=0.0, step=0.01),
        }
        df_req_kg_edit = st.data_editor(
            df_base[["Nutriente", "Min por kg dieta", "Max por kg dieta", "Unidad"]],
            column_config=editable_cols,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="tabla_req_kg_editable_formulacion"
        )

        # Extraer los ajustes realizados
        user_requirements = {}
        for _, row in df_req_kg_edit.iterrows():
            nut = row["Nutriente"]
            try:
                min_val = float(row["Min por kg dieta"]) if row["Min por kg dieta"] not in ["", None, "None"] else 0.0
            except Exception:
                min_val = 0.0
            try:
                max_val = float(row["Max por kg dieta"]) if row["Max por kg dieta"] not in ["", None, "None"] else 0.0
            except Exception:
                max_val = 0.0
            unidad = row["Unidad"]
            user_requirements[nut] = {
                "min": min_val,
                "max": max_val,
                "unit": unidad
            }
        st.session_state["nutrientes_requeridos"] = user_requirements
        
        # INGREDIENTES Y LÍMITES (Selección y ajuste de ingredientes)
        ingredientes_file = st.file_uploader(
            "Matriz de ingredientes (.csv o .xlsx)", 
            type=["csv", "xlsx"], 
            key="uploader_ingredientes"
        )
        ingredientes_df = load_ingredients(ingredientes_file)
        formulable = False

        ingredientes_sel = []
        ingredientes_df_filtrado = pd.DataFrame()
        limites_min = {}
        limites_max = {}

        if ingredientes_df is not None and not ingredientes_df.empty:
            for col in ingredientes_df.columns:
                if col not in ["Ingrediente", "Categoría"]:
                    ingredientes_df[col] = pd.to_numeric(ingredientes_df[col], errors='coerce').fillna(0)

            ingredientes_df = ingredientes_df.round(2)
            st.subheader("Selecciona las materias primas para formular la dieta por categoría")
            categorias = ["Proteinas", "Carbohidratos", "Grasas", "Vegetales", "Frutas", "Otros"]
            ingredientes_seleccionados = []
            for cat in categorias:
                df_cat = ingredientes_df[
                    ingredientes_df["Categoría"].astype(str).str.strip().str.capitalize() == cat
                ]
                if not df_cat.empty:
                    st.markdown(f"**{cat}**")
                    ing_cat = df_cat["Ingrediente"].tolist()
                    sel_cat = st.multiselect(
                        f"Selecciona ingredientes de {cat}",
                        ing_cat,
                        default=[],
                        key=f"multiselect_{cat}_formulacion"
                    )
                    ingredientes_seleccionados.extend(sel_cat)
            ingredientes_sel = list(dict.fromkeys(ingredientes_seleccionados))
            ingredientes_df_filtrado = ingredientes_df[ingredientes_df["Ingrediente"].isin(ingredientes_sel)].copy()

            if not ingredientes_df_filtrado.empty:
                with st.expander("Límites de inclusión de materias primas (%)", expanded=True):
                    if "min_inclusion" not in st.session_state or "max_inclusion" not in st.session_state:
                        st.session_state["min_inclusion"] = {ing: 0.0 for ing in ingredientes_sel}
                        st.session_state["max_inclusion"] = {ing: 100.0 for ing in ingredientes_sel}

                    limites_df = pd.DataFrame({
                        "Ingrediente": ingredientes_sel,
                        "Mínimo (%)": [st.session_state["min_inclusion"].get(ing, 0.0) for ing in ingredientes_sel],
                        "Máximo (%)": [st.session_state["max_inclusion"].get(ing, 100.0) for ing in ingredientes_sel],
                    })

                    limites_editados = st.data_editor(
                        limites_df,
                        column_config={
                            "Mínimo (%)": st.column_config.NumberColumn("Mínimo (%)", min_value=0.0, max_value=100.0, step=0.01),
                            "Máximo (%)": st.column_config.NumberColumn("Máximo (%)", min_value=0.0, max_value=100.0, step=0.01),
                        },
                        use_container_width=True,
                        hide_index=True,
                        key="tabla_limites_inclusion_formulacion"
                    )
                    for _, row in limites_editados.iterrows():
                        ing = row["Ingrediente"]
                        st.session_state["min_inclusion"][ing] = float(row["Mínimo (%)"])
                        st.session_state["max_inclusion"][ing] = float(row["Máximo (%)"])

                    limites_min = {ing: st.session_state["min_inclusion"].get(ing, 0.0) / 100.0 for ing in ingredientes_sel}
                    limites_max = {ing: st.session_state["max_inclusion"].get(ing, 100.0) / 100.0 for ing in ingredientes_sel}

            formulable = not ingredientes_df_filtrado.empty

        # ---------- FORMULAR DIETA ----------
        if formulable:
            if st.button("Formular dieta automática", key="btn_formular_dieta_auto"):
                user_requirements = st.session_state.get("nutrientes_requeridos", {})
                nutrientes_seleccionados = ["EM"] + list(user_requirements.keys())  # Incluye EM en la fórmula
                formulator = DietFormulator(
                    ingredientes_df_filtrado,
                    nutrientes_seleccionados,
                    user_requirements,
                    limits={"min": limites_min, "max": limites_max},
                    ratios=[],
                    min_selected_ingredients={},
                    diet_type=None
                )
                try:
                    result = formulator.solve()
                except Exception as e:
                    result = {"success": False, "message": f"Error al ejecutar el solver: {str(e)}"}
                st.session_state["last_result"] = result
                if result.get("success", False):
                    st.session_state["last_diet"] = result.get("diet", {})
                    st.session_state["last_cost"] = result.get("cost", 0)
                    st.session_state["last_nutritional_values"] = result.get("nutritional_values", {})
                    st.session_state["ingredients_df"] = ingredientes_df_filtrado
                    st.session_state["nutrientes_seleccionados"] = nutrientes_seleccionados
                    st.success("¡Formulación realizada!")
                else:
                    st.error(result.get("message", "No se pudo formular la dieta."))

        else:
            st.info("Selecciona al menos un ingrediente para formular la mezcla.")

# ===================== BLOQUE 7: RESULTADOS DE LA FORMULACIÓN AUTOMÁTICA =====================
with tabs[2]:
    st.header("Resultados de la formulación automática")
    result = st.session_state.get("last_result", None)
    ingredientes_df_filtrado = st.session_state.get("ingredients_df", None)

    ingredientes_sel = []
    if ingredientes_df_filtrado is not None and "Ingrediente" in ingredientes_df_filtrado.columns:
        ingredientes_sel = list(ingredientes_df_filtrado["Ingrediente"])
    
    diet = result.get("diet", {}) if result else {}
    comp_data = []

    # Obtener la dosis diaria usada para formulación
    dosis_g = (
        st.session_state.get("dosis_dieta_g_formulacion")
        or st.session_state.get("dosis_dieta_g")
        or 1000  # Valor por defecto si no existe
    )

    for ing in ingredientes_sel:
        porcentaje = diet.get(ing, 0.0)
        gramos = (porcentaje / 100.0) * dosis_g
        comp_data.append({
            "Ingrediente": ing,
            "% Inclusión": fmt2(porcentaje),
            "Gramos en dosis": fmt2(gramos)
        })
    res_df = pd.DataFrame(comp_data)

    st.subheader("Composición óptima de la dieta (por dosis seleccionada)")
    if "Ingrediente" in res_df.columns and not res_df.empty:
        st.dataframe(res_df.set_index("Ingrediente"), use_container_width=True)
    else:
        st.info("Carga la matriz de ingredientes y selecciona al menos un ingrediente para ver la composición de la dieta.")

    # ----------- Costo de la dieta formulada -----------
    if result and "Ingrediente" in res_df.columns and not res_df.empty:
        total_cost = result.get("cost", 0)
        st.markdown(f"<b>Costo total (por 100 kg):</b> ${fmt2(total_cost)}", unsafe_allow_html=True)
        precio_kg = total_cost / 100 if total_cost else 0
        precio_ton = precio_kg * 1000
        st.metric(label="Precio por kg de dieta", value=f"${fmt2(precio_kg)}")
        st.metric(label="Precio por tonelada de dieta", value=f"${fmt2(precio_ton)}")
    else:
        st.info("No hay resultados de costo para mostrar.")

    # ----------- COMPOSICIÓN NUTRICIONAL Y CUMPLIMIENTO -----------
    st.subheader("Composición nutricional y cumplimiento (por kg de dieta)")

    # Consolidar datos ajustados desde BLOQUE 6 y resultados calculados
    user_requirements = st.session_state.get("nutrientes_requeridos", {})  # Valores ajustados
    nutritional_values = result.get("nutritional_values", {}) if result else {}

    # Incluir datos calculados y ajustados sin duplicar
    comp_list = []
    for nut, req in user_requirements.items():
        obtenido = nutritional_values.get(nut, None)
        min_v = fmt2(req.get("min", ""))
        max_v = fmt2(req.get("max", ""))
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
            if max_f > 0 and obt_f > max_f:
                cumple = "❌"
        except Exception:
            pass

        # Asegurarse de no duplicar "Energía metabolizable (EM)"
        if nut == "Energía metabolizable (EM)":
            comp_list = [item for item in comp_list if item["Nutriente"] != "Energía metabolizable (EM)"]

        comp_list.append({
            "Nutriente": nut,
            "Min": fmt2(min_v),
            "Max": fmt2(max_v),
            "Obtenido": fmt2(obtenido) if obtenido is not None and obtenido != "" else "",
            "Unidad por kg de dieta": unidad,
            "Cumple": cumple
        })

    # Generar DataFrame y mostrar resultados
    comp_df = pd.DataFrame(comp_list)
    if not comp_df.empty and "Nutriente" in comp_df.columns:
        st.dataframe(comp_df.set_index("Nutriente"), use_container_width=True)
    else:
        st.info("No hay composición nutricional disponible para mostrar.")

    # ----------- Humedad de la Dieta Formulada -----------
    if diet and ingredientes_df_filtrado is not None and "Humedad" in ingredientes_df_filtrado.columns:
        humedad_ponderada = 0.0
        for ing, porcentaje in diet.items():
            row = ingredientes_df_filtrado[ingredientes_df_filtrado["Ingrediente"] == ing]
            if not row.empty:
                humedad_ing = float(row["Humedad"].values[0])
                humedad_ponderada += (porcentaje / 100.0) * humedad_ing
        st.markdown(f"**Humedad de la Dieta:** {fmt2(humedad_ponderada)}%")

# ======================== BLOQUE AUXILIARES PARA BLOQUE 8 (GRÁFICOS) ========================
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

# --- Cargar escenarios (stub, deberías implementar persistencia real según tu flujo) ---
def cargar_escenarios():
    return []

def guardar_escenarios(escenarios):
    pass

# ======================== BLOQUE 8: TAB GRÁFICOS DINÁMICOS (DISTRIBUCIÓN SOLO EN PASTEL EN SUBTAB) ========================
with tabs[2]:
    st.header("Gráficos de la formulación")

    actualizar_graficos = st.button("Actualizar gráficos", key="actualizar_graficos_tab2")
    if actualizar_graficos:
        st.experimental_rerun()

    diet = st.session_state.get("last_diet", None)
    nutritional_values = st.session_state.get("last_nutritional_values", {})
    ingredientes_seleccionados = list(st.session_state.get("last_diet", {}).keys())
    nutrientes_seleccionados = st.session_state.get("nutrientes_seleccionados", [])
    ingredients_df = st.session_state.get("ingredients_df", None)
    total_cost = st.session_state.get("last_cost", 0)
    unidades_dict = get_unidades_dict(nutrientes_seleccionados)
    dosis_g = st.session_state.get("dosis_dieta_g_formulacion", 1000)

    # ============= SUBTABS DE GRÁFICOS ==============
    subtab_dist, subtab1, subtab2, subtab3 = st.tabs([
        "Distribución de la dieta",
        "Costo Total por Ingrediente",
        "Aporte por Ingrediente a Nutrientes",
        "Precio Sombra por Nutriente (Shadow Price)"
    ])

    # ---------- SUBTAB: Distribución de la dieta (solo pastel) ----------
    with subtab_dist:
        st.subheader("Distribución de la dieta por ingrediente")
        if diet and ingredients_df is not None and not ingredients_df.empty:
            ingredientes_sel = list(diet.keys())
            distribucion_data = []
            for ing in ingredientes_sel:
                porcentaje = diet.get(ing, 0.0)
                gramos = (porcentaje / 100.0) * dosis_g
                distribucion_data.append({
                    "Ingrediente": ing,
                    "% Inclusión": porcentaje,
                    "Gramos en dosis": gramos
                })
            df_dist = pd.DataFrame(distribucion_data)

            # --- Gráfico de pastel (% inclusión) ---
            import plotly.graph_objects as go
            fig_pie = go.Figure(go.Pie(
                labels=df_dist["Ingrediente"],
                values=df_dist["% Inclusión"],
                textinfo="label+percent",
                hole=0.35
            ))
            fig_pie.update_layout(title="Proporción % de cada ingrediente en la dieta")
            st.plotly_chart(fig_pie, use_container_width=True)

            # --- Tabla resumen ---
            st.markdown("#### Tabla de distribución")
            st.dataframe(df_dist.set_index("Ingrediente"), use_container_width=True)
        else:
            st.info("Formula una dieta y selecciona ingredientes para ver la distribución.")

    # ---------- SUBTAB 1: Costo Total por Ingrediente ----------
    with subtab1:
        if diet and ingredients_df is not None and not ingredients_df.empty:
            df_formula = ingredients_df.copy()
            df_formula["% Inclusión"] = df_formula["Ingrediente"].map(diet).fillna(0)
            df_formula["precio"] = df_formula["precio"].fillna(0)
            df_formula = df_formula[df_formula["Ingrediente"].isin(diet.keys())].reset_index(drop=True)
            ingredientes_seleccionados = list(df_formula["Ingrediente"])
            color_map = get_color_map(ingredientes_seleccionados)

            manual_unit = unit_selector(
                "Unidad para mostrar el costo total por ingrediente",
                ['USD/kg', 'USD/ton'],
                'USD/ton',
                key="unit_selector_costototal_tab1"
            )
            factor = 1 if manual_unit == 'USD/kg' else 10
            label = manual_unit
            costos = [
                float(row["precio"]) * float(row["% Inclusión"]) / 100 * factor
                if pd.notnull(row["precio"]) and pd.notnull(row["% Inclusión"]) else 0
                for _, row in df_formula.iterrows()
            ]
            suma_costos = sum(costos)
            suma_inclusion = sum(df_formula["% Inclusión"])
            proporciones = [
                float(row["% Inclusión"]) * 100 / suma_inclusion if suma_inclusion > 0 else 0
                for _, row in df_formula.iterrows()
            ]

            # --------- SOLO GRÁFICO DE PASTEL ---------
            fig_pie = go.Figure(go.Pie(
                labels=ingredientes_seleccionados,
                values=costos,
                marker_colors=[color_map[ing] for ing in ingredientes_seleccionados],
                hoverinfo="label+percent+value",
                textinfo="label+percent",
                hole=0.3
            ))
            fig_pie.update_layout(title="Participación de cada ingrediente en el costo total")
            st.plotly_chart(fig_pie, use_container_width=True)

            df_costos = pd.DataFrame({
                "Ingrediente": ingredientes_seleccionados,
                f"Costo aportado ({label})": [fmt2(c) for c in costos],
                "% Inclusión": [fmt2(row["% Inclusión"]) for _, row in df_formula.iterrows()],
                "Proporción dieta (%)": [fmt2(p) for p in proporciones],
                "Precio ingrediente (USD/kg)": [fmt2(row["precio"]) for _, row in df_formula.iterrows()],
            })
            st.dataframe(fmt2_df(df_costos), use_container_width=True)
            st.markdown(f"**Costo total de la fórmula:** {fmt2(suma_costos)} {label} (suma de los ingredientes). Puedes cambiar la unidad.")
        else:
            st.info("No hay ingredientes o dieta formulada para mostrar el costo total.")

    # ---------- SUBTAB 2: Aporte por Ingrediente a Nutrientes ----------
    with subtab2:
        unit_options = {
            'kg': ['kg', 'ton'],
            'g': ['g', '100g', 'kg', 'ton'],
            'kcal': ['kcal', '1000kcal'],
            '%': ['%', '100 unidades'],
            'unidad': ['unidad', '100 unidades', '1000 unidades', 'kg', 'ton'],
        }
        if diet and ingredients_df is not None and not ingredients_df.empty and nutrientes_seleccionados:
            df_formula = ingredients_df.copy()
            df_formula["% Inclusión"] = df_formula["Ingrediente"].map(diet).fillna(0)
            df_formula = df_formula[df_formula["Ingrediente"].isin(diet.keys())].reset_index(drop=True)
            ingredientes_seleccionados = list(df_formula["Ingrediente"])
            color_map = get_color_map(ingredientes_seleccionados)

            nut_tabs = st.tabs([nut for nut in nutrientes_seleccionados])
            for i, nut in enumerate(nutrientes_seleccionados):
                with nut_tabs[i]:
                    unit = unidades_dict.get(nut, "unidad")
                    manual_unit = unit_selector(
                        f"Unidad para {nut}",
                        unit_options.get(unit, ["unidad", "100 unidades", "1000 unidades", "kg", "ton"]),
                        unit_options.get(unit, ["unidad"])[0],
                        key=f"unit_selector_{nut}_aporte_tab1"
                    )
                    factor, label = get_unit_factor(unit, manual_unit)
                    valores = []
                    porc_aporte = []
                    total_nut = sum([
                        (float(df_formula.loc[df_formula["Ingrediente"] == ing, nut].values[0]) *
                         float(df_formula[df_formula["Ingrediente"] == ing]["% Inclusión"].values[0]) / 100 * factor)
                        if nut in df_formula.columns and
                           pd.notnull(df_formula.loc[df_formula["Ingrediente"] == ing, nut].values[0]) else 0
                        for ing in ingredientes_seleccionados
                    ])
                    for ing in ingredientes_seleccionados:
                        valor = float(df_formula.loc[df_formula["Ingrediente"] == ing, nut].values[0]) \
                            if nut in df_formula.columns and pd.notnull(df_formula.loc[df_formula["Ingrediente"] == ing, nut].values[0]) else 0
                        porc = float(df_formula[df_formula["Ingrediente"] == ing]["% Inclusión"].values[0])
                        aporte = valor * porc / 100 * factor
                        valores.append(aporte)
                        porc_aporte.append(100 * aporte / total_nut if total_nut > 0 else 0)
                    df_aporte = pd.DataFrame({
                        "Ingrediente": ingredientes_seleccionados,
                        f"Aporte de {nut} ({label})": [fmt2(v) for v in valores],
                        "% Inclusión": [fmt2(df_formula[df_formula["Ingrediente"] == ing]["% Inclusión"].values[0]) for ing in ingredientes_seleccionados],
                        "Contenido por kg": [fmt2(df_formula[df_formula["Ingrediente"] == ing][nut].values[0]) if nut in df_formula.columns else "" for ing in ingredientes_seleccionados],
                        f"Proporción aporte {nut} (%)": [fmt2(p) for p in porc_aporte],
                    })
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=ingredientes_seleccionados,
                        y=valores,
                        marker_color=[color_map[ing] for ing in ingredientes_seleccionados],
                        text=[fmt2(v) for v in valores],
                        textposition='auto',
                        customdata=porc_aporte,
                        hovertemplate='%{x}<br>Aporte: %{y:.2f} ' + label + '<br>Proporción aporte: %{customdata:.2f}%<extra></extra>',
                    ))
                    fig.update_layout(
                        xaxis_title="Ingrediente",
                        yaxis_title=f"Aporte de {nut} ({label})",
                        title=f"Aporte de cada ingrediente a {nut} ({label})",
                        template="simple_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(fmt2_df(df_aporte), use_container_width=True)
                    st.markdown(
                        f"Puedes ajustar la unidad para visualizar el aporte en la escala más útil para tu análisis."
                    )
        else:
            st.info("Selecciona al menos un nutriente para visualizar los aportes por ingrediente.")

    # ---------- SUBTAB 3: Precio sombra por nutriente ----------
    with subtab3:
        unit_options = {
            'kg': ['kg', 'ton'],
            'g': ['g', '100g', 'kg', 'ton'],
            'kcal': ['kcal', '1000kcal'],
            '%': ['%', '100 unidades'],
            'unidad': ['unidad', '100 unidades', '1000 unidades', 'kg', 'ton'],
        }
        if diet and ingredients_df is not None and not ingredients_df.empty and nutrientes_seleccionados:
            df_formula = ingredients_df.copy()
            df_formula["% Inclusión"] = df_formula["Ingrediente"].map(diet).fillna(0)
            df_formula = df_formula[df_formula["Ingrediente"].isin(diet.keys())].reset_index(drop=True)
            ingredientes_seleccionados = list(df_formula["Ingrediente"])
            color_map = get_color_map(ingredientes_seleccionados)

            shadow_tab = st.tabs([nut for nut in nutrientes_seleccionados])
            for idx, nut in enumerate(nutrientes_seleccionados):
                with shadow_tab[idx]:
                    unit = unidades_dict.get(nut, "unidad")
                    manual_unit = unit_selector(
                        f"Unidad para {nut}",
                        unit_options.get(unit, ["unidad", "100 unidades", "1000 unidades", "kg", "ton"]),
                        unit_options.get(unit, ["unidad"])[0],
                        key=f"unit_selector_{nut}_shadow_tab1"
                    )
                    factor, label = get_unit_factor(unit, manual_unit)
                    precios_unit = []
                    contenidos = []
                    precios_ing = []
                    for i, ing in enumerate(ingredientes_seleccionados):
                        row = df_formula[df_formula["Ingrediente"] == ing].iloc[0]
                        contenido = float(row.get(nut, 0))
                        precio = float(row.get("precio", np.nan))
                        if pd.notnull(contenido) and contenido > 0 and pd.notnull(precio):
                            precios_unit.append(precio / contenido * factor)
                        else:
                            precios_unit.append(np.nan)
                        contenidos.append(contenido)
                        precios_ing.append(precio)
                    df_shadow = pd.DataFrame({
                        "Ingrediente": ingredientes_seleccionados,
                        f"Precio por {manual_unit}": [fmt2(v) if pd.notnull(v) else "" for v in precios_unit],
                        f"Contenido de {nut} por kg": [fmt2(c) for c in contenidos],
                        "Precio ingrediente (USD/kg)": [fmt2(p) for p in precios_ing],
                    })
                    precios_unit_np = np.array([v if pd.notnull(v) else np.inf for v in precios_unit])
                    if len(precios_unit_np) > 0 and np.isfinite(precios_unit_np).any():
                        min_idx = int(np.nanargmin(precios_unit_np))
                        df_shadow["Es el más barato"] = ["✅" if i == min_idx else "" for i in range(len(df_shadow))]
                        bar_colors = ['green' if i == min_idx else 'royalblue' for i in range(len(df_shadow))]
                    else:
                        min_idx = None
                        df_shadow["Es el más barato"] = ["" for _ in range(len(df_shadow))]
                        bar_colors = ['royalblue' for _ in range(len(df_shadow))]
                    fig_shadow = go.Figure()
                    fig_shadow.add_trace(go.Bar(
                        x=df_shadow["Ingrediente"],
                        y=[v if pd.notnull(v) else 0 for v in precios_unit],
                        marker_color=bar_colors,
                        text=[fmt2(v) if pd.notnull(v) else "" for v in precios_unit],
                        textposition='auto',
                        customdata=df_shadow["Es el más barato"],
                        hovertemplate=f'%{{x}}<br>Precio sombra: %{{y:.2f}} {label}<br>%{{customdata}}<extra></extra>',
                    ))
                    fig_shadow.update_layout(
                        xaxis_title="Ingrediente",
                        yaxis_title=label,
                        title=f"Precio sombra y costo por ingrediente para {nut}",
                        template="simple_white"
                    )
                    st.plotly_chart(fig_shadow, use_container_width=True)
                    st.dataframe(fmt2_df(df_shadow), use_container_width=True)
                    st.markdown(
                        f"**El precio sombra de {nut} es el menor costo posible para obtener una unidad de este nutriente usando el ingrediente más barato en la fórmula.**\n\n"
                        f"- Puedes ajustar la unidad para mejorar la visualización.\n"
                        f"- El ingrediente marcado con ✅ aporta el precio sombra."
                    )
        else:
            st.info("Selecciona al menos un nutriente para visualizar el precio sombra por ingrediente.")

# ======================== BLOQUE 10: TAB COMPARATIVO DINÁMICO ========================
def calcular_nutrientes_en_dosis(dieta, ingredientes_df, gramos_totales):
    """
    Calcula nutrientes obtenidos en gramos_totales de dieta.
    Para nutrientes en %/mg/UI por 100 kg: aporte = (% inclusión / 100) × val × gramos_totales / 100
    Para energía (kcal/kg):               aporte = (% inclusión / 100) × val × gramos_totales / 1000
    """
    resultado = {}
    if ingredientes_df is None or ingredientes_df.empty:
        return resultado
    exclude_cols = {"Ingrediente", "precio", "Materia seca (%)", "Categoría"}
    nut_cols = [c for c in ingredientes_df.columns if c not in exclude_cols]
    for nut_col in nut_cols:
        total = 0.0
        for ing, porcentaje in dieta.items():
            row = ingredientes_df[ingredientes_df["Ingrediente"] == ing]
            if row.empty:
                continue
            val = row[nut_col].values[0]
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue
            if pd.isna(val):
                continue
            if "EM" in nut_col or "Energía" in nut_col:
                # Energía metabolizable (EM) está en kcal/kg de ingrediente.
                # Se pondera por % de inclusión y se escala por la dosis.
                # (% / 100) × kcal/kg × (gramos / 1000) → kcal aportadas por este ingrediente.
                total += (porcentaje / 100.0) * val * gramos_totales / 1000.0
            else:
                # Otros nutrientes (%, mg/kg, UI/kg): aporte proporcional al % de inclusión.
                # val está expresado por 100 kg de ingrediente; gramos_totales en gramos.
                total += (porcentaje / 100.0) * val * gramos_totales / 100.0
        resultado[nut_col] = total
    return resultado


def generar_comparativo(requerimientos_perro, nutrientes_obtenidos, mer_final=None):
    """
    Genera DataFrame comparativo entre requerimientos del perro y lo que aporta la dieta.
    requerimientos_perro: DataFrame con columnas Nutriente, Min Ajustado, Max Ajustado, Unidad
    nutrientes_obtenidos: dict {nutriente: valor_obtenido}
    mer_final: requerimiento energético diario del animal (kcal/día), usado para comparar energía
    """
    rows = []
    for _, row in requerimientos_perro.iterrows():
        nut = row.get("Nutriente", "")
        min_str = row.get("Min Ajustado", "-")
        max_str = row.get("Max Ajustado", "-")
        unidad = row.get("Unidad", "")

        try:
            min_req = float(min_str) if min_str not in ["-", "", None, "None"] else None
        except (ValueError, TypeError):
            min_req = None
        try:
            max_req = float(max_str) if max_str not in ["-", "", None, "None"] else None
        except (ValueError, TypeError):
            max_req = None

        obtenido = nutrientes_obtenidos.get(nut, None)

        if obtenido is None:
            cumple = "-"
            obtenido_str = "-"
        else:
            obtenido_str = fmt2(obtenido)
            try:
                obt_f = float(obtenido)
                if min_req is not None and max_req is not None:
                    if min_req <= obt_f <= max_req:
                        cumple = "✅"
                    elif obt_f < min_req:
                        cumple = "⚠️ BAJO"
                    else:
                        cumple = "⚠️ ALTO"
                elif min_req is not None:
                    cumple = "✅" if obt_f >= min_req else "⚠️ BAJO"
                else:
                    cumple = "-"
            except (ValueError, TypeError):
                cumple = "-"

        rows.append({
            "Nutriente": nut,
            "Necesita (Min)": fmt2(min_req) if min_req is not None else "-",
            "Necesita (Max)": fmt2(max_req) if max_req is not None else "-",
            "Obtiene": obtenido_str,
            "Unidad": unidad,
            "Cumple": cumple,
        })

    comparativo_df = pd.DataFrame(rows)

    # Agregar fila de Energía metabolizable si no está en los requerimientos
    if "Energía metabolizable (EM)" not in comparativo_df["Nutriente"].values:
        # El optimizer almacena la energía con la clave "EM"; también buscar la clave larga
        em_obtenido = nutrientes_obtenidos.get("Energía metabolizable (EM)") or nutrientes_obtenidos.get("EM")
        # Usar mer_final como requerimiento mínimo de energía (kcal/día del animal)
        em_min_req = mer_final if mer_final is not None else None
        if em_obtenido is not None:
            em_obt_f = float(em_obtenido)
            if em_min_req is not None:
                em_cumple = "✅" if em_obt_f >= em_min_req else "⚠️ BAJO"
            else:
                em_cumple = "-"
            em_obtenido_str = fmt2(em_obt_f)
        else:
            em_cumple = "-"
            em_obtenido_str = "-"
        em_row = pd.DataFrame([{
            "Nutriente": "Energía metabolizable (EM)",
            "Necesita (Min)": fmt2(em_min_req) if em_min_req is not None else "-",
            "Necesita (Max)": "-",
            "Obtiene": em_obtenido_str,
            "Unidad": "kcal",
            "Cumple": em_cumple,
        }])
        comparativo_df = pd.concat([em_row, comparativo_df], ignore_index=True)

    return comparativo_df


with tabs[3]:
    st.header("Comparativo Nutricional: Necesita vs Obtiene")

    # Validaciones previas
    requerimientos_perro = st.session_state.get("tabla_requerimientos_base")
    dieta_formulada = st.session_state.get("last_diet")
    ingredientes_df_comp = st.session_state.get("ingredients_df")
    nutritional_values_per_kg = st.session_state.get("last_nutritional_values", {})

    if requerimientos_perro is None or requerimientos_perro.empty or not dieta_formulada:
        st.warning("⚠️ Completa primero el Perfil (Tab 1) y la Formulación (Tab 2)")
        st.stop()

    # ── Sección 1: Selector de dosis ─────────────────────────────────────────
    st.subheader("1. Dosis Diaria")
    col_inp, col_btn = st.columns([4, 1])
    with col_inp:
        gramos_a_dar = st.number_input(
            "¿Cuántos gramos de dieta dará al día?",
            min_value=50,
            max_value=5000,
            value=int(st.session_state.get("gramos_a_dar", 500)),
            step=50,
            key="gramos_comparativo_input",
        )
    with col_btn:
        st.write("")
        st.write("")
        calcular_btn = st.button("🔄 Calcular", key="btn_calcular_comparativo")

    if calcular_btn:
        st.session_state["gramos_a_dar"] = gramos_a_dar

    gramos_a_dar = st.session_state.get("gramos_a_dar", gramos_a_dar)

    # ── Calcular humedad de la dieta y convertir MF → MS ─────────────────────
    humedad_dieta = 0.0
    tiene_humedad = (
        dieta_formulada
        and ingredientes_df_comp is not None
        and "Humedad" in ingredientes_df_comp.columns
    )
    if tiene_humedad:
        for ing, porcentaje in dieta_formulada.items():
            row = ingredientes_df_comp[ingredientes_df_comp["Ingrediente"] == ing]
            if not row.empty:
                humedad_ing = float(row["Humedad"].values[0])
                humedad_dieta += (porcentaje / 100.0) * humedad_ing
    else:
        st.warning(
            "⚠️ La columna 'Humedad' no está disponible en la matriz de ingredientes. "
            "Los cálculos de nutrientes se realizarán sobre la dosis en Materia Fresca sin conversión."
        )

    gramos_ms = mf_a_ms(gramos_a_dar, humedad_dieta)

    st.info(
        f"**Dosis ingresada:** {gramos_a_dar}g Materia Fresca | "
        f"**Equivalente MS:** {fmt2(gramos_ms)}g | "
        f"**Humedad dieta:** {fmt2(humedad_dieta)}%"
    )

    # ── Calcular "Obtiene" ────────────────────────────────────────────────────
    # Usar gramos en Materia Seca para calcular nutrientes correctamente.
    nutrientes_obtenidos = calcular_nutrientes_en_dosis(
        dieta_formulada, ingredientes_df_comp, gramos_ms
    )

    st.session_state["nutrientes_obtenidos_final"] = nutrientes_obtenidos

    # ── Sección 2: Tabla Comparativa ─────────────────────────────────────────
    st.subheader("2. Tabla Comparativa")
    mer_final_tab3 = st.session_state.get("energia_actual")
    comparativo_df = generar_comparativo(requerimientos_perro, nutrientes_obtenidos, mer_final=mer_final_tab3)
    st.session_state["comparativo_final"] = comparativo_df

    if not comparativo_df.empty:
        st.dataframe(
            comparativo_df.set_index("Nutriente"),
            use_container_width=True,
            height=420,
        )
    else:
        st.info("No hay datos para mostrar el comparativo.")

    # ── Sección 3: Métricas de cumplimiento ──────────────────────────────────
    with st.expander("📊 3. Métricas de Cumplimiento", expanded=False):
        if not comparativo_df.empty:
            evaluados = comparativo_df[comparativo_df["Cumple"] != "-"]
            total_evaluados = len(evaluados)
            cumplen = int((evaluados["Cumple"] == "✅").sum())
            fuera_rango = int(evaluados["Cumple"].isin(["⚠️ BAJO", "⚠️ ALTO"]).sum())
            porc = (cumplen / total_evaluados * 100) if total_evaluados > 0 else 0.0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cumplimiento", f"{porc:.1f}%")
            with col2:
                st.metric("✅ Nutrientes que cumplen", cumplen)
            with col3:
                st.metric("⚠️ Fuera de rango", fuera_rango)

            bajos = evaluados[evaluados["Cumple"] == "⚠️ BAJO"]["Nutriente"].tolist()
            altos = evaluados[evaluados["Cumple"] == "⚠️ ALTO"]["Nutriente"].tolist()

            if bajos:
                st.warning(
                    f"⚠️ **Nutrientes BAJOS** ({len(bajos)}): {', '.join(bajos)}\n\n"
                    f"💡 Sugerencia: Aumenta los gramos de dieta diaria o reformula con ingredientes "
                    f"más ricos en estos nutrientes."
                )
            if altos:
                st.warning(
                    f"⚠️ **Nutrientes ALTOS** ({len(altos)}): {', '.join(altos)}\n\n"
                    f"💡 Sugerencia: Reduce los gramos de dieta diaria o ajusta la formulación "
                    f"para disminuir estos nutrientes."
                )

    # ── Sección 4: Desglose expandible ───────────────────────────────────────
    with st.expander("4. Desglose de ingredientes en la dosis (Materia Fresca vs Materia Seca)"):
        desglose_rows = []
        for ing, porcentaje in dieta_formulada.items():
            gramos_mf = (porcentaje / 100.0) * gramos_a_dar
            row = ingredientes_df_comp[ingredientes_df_comp["Ingrediente"] == ing] if ingredientes_df_comp is not None else pd.DataFrame()
            if not row.empty and "Humedad" in row.columns:
                humedad_ing = float(row["Humedad"].values[0])
                gramos_ms_ing = mf_a_ms(gramos_mf, humedad_ing)
                humedad_display = fmt2(humedad_ing)
                gramos_ms_display = fmt2(gramos_ms_ing)
            else:
                humedad_display = "N/A"
                gramos_ms_display = "N/A"
            desglose_rows.append({
                "Ingrediente": ing,
                "% Inclusión": fmt2(porcentaje),
                "Gramos MF": fmt2(gramos_mf),
                "Humedad %": humedad_display,
                "Gramos MS": gramos_ms_display,
            })
        desglose_df = pd.DataFrame(desglose_rows)
        if not desglose_df.empty:
            st.dataframe(desglose_df.set_index("Ingrediente"), use_container_width=True)
            st.info("**MF:** Materia Fresca | **MS:** Materia Seca")
        else:
            st.info("No hay ingredientes en la dieta formulada.")

# ======================== BLOQUE 9: RESUMEN Y EXPORTAR (FOTO, GUARDAR, ELIMINAR, SIN DRAG SI YA HAY FOTO) ========================
with tabs[4]:
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
        from PIL import Image
        import io

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
                st.experimental_rerun()

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
                st.experimental_rerun()

    with cols[1]:
        st.markdown(f"""
        - <b>Nombre:</b> {mascota.get('nombre', 'No definido')}
        - <b>Especie:</b> {mascota.get('especie', 'No definido')}
        - <b>Edad:</b> {mascota.get('edad', 'No definido')} años
        - <b>Peso:</b> {mascota.get('peso', 'No definido')} kg
        - <b>Condición:</b> {mascota.get('condicion', 'No definido')}
        """, unsafe_allow_html=True)

    # === 2. Dieta (proporciones y gramos) ===
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

    # === 3. Precio de la dieta ===
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

    # === 4. Tabla Unificada de Requerimientos y Composición Obtenida ===
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

    # === 5. Exportar a Excel ===
    st.subheader("Exportar resumen a Excel")

    import io
    import pandas as pd

    perfil_df = pd.DataFrame([mascota])
    dieta_df = res_df
    precio_df = pd.DataFrame([{
        "Costo total (100kg)": fmt2(total_cost),
        "Precio por kg": fmt2(precio_kg),
        "Precio por dosis": fmt2(precio_dosis)
    }])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        perfil_df.to_excel(writer, sheet_name='Perfil Mascota', index=False)
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

