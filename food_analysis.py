# ======================== ANÁLISIS NUTRICIONAL DE ALIMENTOS ========================
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st

from food_database import FOODS, calculate_energy, calculate_ena, calculate_energy_breakdown, get_food_names, get_food_data

# ---- Paleta de colores corporativa ----
COLORS = {
    "PB": "#2176FF",
    "EE": "#FFB703",
    "Ash": "#8E9AAF",
    "Humidity": "#8ECAE6",
    "FC": "#52B788",
    "ENA": "#F4845F",
}

LABELS = {
    "PB": "Proteína Bruta",
    "EE": "Grasa (EE)",
    "Ash": "Cenizas",
    "Humidity": "Humedad",
    "FC": "Fibra Cruda",
    "ENA": "Carbohidratos (ENA)",
}

# Umbral de cobertura energética para alertas visuales (%)
ENERGY_COVERAGE_THRESHOLD = 110

# Íconos por clase de decisión nutricional
DECISION_COLORS = {
    "low": "🔵",       # < 90%
    "adequate": "🟢",  # 90-110%
    "moderate": "🟠",  # 110-130%
    "high": "🔴",      # > 130%
}


def get_clase_decision(cobertura_pct):
    """Devuelve la clase CSS según el porcentaje de cobertura energética."""
    if cobertura_pct < 90:
        return "low"
    elif cobertura_pct <= 110:
        return "adequate"
    elif cobertura_pct <= 130:
        return "moderate"
    else:
        return "high"


def get_resultado_cobertura(cobertura_pct):
    """Texto interpretativo de cobertura energética."""
    if cobertura_pct < 90:
        return "No cubre el requerimiento energético"
    elif cobertura_pct <= 110:
        return "Cubre adecuadamente el requerimiento energético"
    else:
        return "Excede el requerimiento energético"


def generar_interpretacion_alimento(nombre, cobertura, aporte, mer,
                                    gramos_act, gramos_rec, cob_pb, cob_ee):
    """
    Genera un párrafo interpretativo con el análisis nutricional completo del alimento.

    Parámetros:
        nombre (str)       : Nombre del alimento.
        cobertura (float)  : Cobertura energética en % (aporte/MER×100).
        aporte (float)     : Energía aportada (kcal/día).
        mer (float)        : Requerimiento energético del animal (kcal/día).
        gramos_act (float) : Gramos diarios actuales.
        gramos_rec (float) : Gramos diarios recomendados para cubrir MER.
        cob_pb (float|None): Cobertura de proteína en % (puede ser None).
        cob_ee (float|None): Cobertura de grasa en % (puede ser None).

    Retorna:
        str: Párrafo interpretativo.
    """
    template = f"{nombre} aporta {aporte:.0f} kcal/día con {gramos_act:.0f} g/día. "

    if cobertura < 90:
        template += f"Cubre solo el {cobertura:.0f}% del requerimiento energético. "
        template += f"Se recomienda aumentar a {gramos_rec:.0f} g/día. "
    elif cobertura <= 110:
        template += f"Cubre adecuadamente el {cobertura:.0f}% del requerimiento energético. "
    else:
        template += f"Excede al {cobertura:.0f}% el requerimiento energético. "
        template += f"Se recomienda reducir a {gramos_rec:.0f} g/día. "

    if cob_pb is not None:
        if cob_pb < 90:
            template += f"Proteína insuficiente ({cob_pb:.0f}% del requerimiento). "
        elif cob_pb <= 110:
            template += f"Proteína adecuada ({cob_pb:.0f}% del requerimiento). "
        else:
            template += f"Proteína elevada ({cob_pb:.0f}% del requerimiento). "

    if cob_ee is not None:
        if cob_ee < 90:
            template += f"Grasa insuficiente ({cob_ee:.0f}% del requerimiento). "
        elif cob_ee <= 110:
            template += f"Grasa adecuada ({cob_ee:.0f}% del requerimiento). "
        else:
            template += f"Grasa elevada ({cob_ee:.0f}% del requerimiento). "

    template += "Se recomienda monitoreo de peso y condición corporal regularmente."
    return template


def plot_macronutrients(food_name, food_data):
    """
    Crea un gráfico de barras apiladas con la composición proximal del alimento.

    Parámetros:
        food_name (str): Nombre del alimento.
        food_data (dict): Diccionario con PB, EE, Ash, Humidity, FC.

    Retorna:
        plotly.graph_objects.Figure
    """
    ENA = calculate_ena(food_data)
    components = {
        "PB": food_data["PB"],
        "EE": food_data["EE"],
        "Ash": food_data["Ash"],
        "Humidity": food_data["Humidity"],
        "FC": food_data["FC"],
        "ENA": ENA,
    }

    fig = go.Figure()
    for key, value in components.items():
        fig.add_trace(
            go.Bar(
                name=LABELS[key],
                x=[food_name],
                y=[value],
                marker_color=COLORS[key],
                text=[f"{value:.1f}%"],
                textposition="inside",
                hovertemplate=f"<b>{LABELS[key]}</b>: {value:.2f}%<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=f"Composición Proximal — {food_name}",
            font=dict(size=15, family="Montserrat, sans-serif"),
        ),
        yaxis_title="% (Base tal como está)",
        xaxis_title="",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
            font=dict(size=11),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=500,
        margin=dict(t=60, b=150, l=40, r=190),
    )
    return fig


def plot_macronutrients_pie(food_name, food_data):
    """
    Crea un gráfico de torta mostrando la distribución de macronutrientes (sin humedad).

    Parámetros:
        food_name (str): Nombre del alimento.
        food_data (dict): Diccionario con PB, EE, Ash, Humidity, FC.

    Retorna:
        plotly.graph_objects.Figure
    """
    ENA = calculate_ena(food_data)
    labels = []
    values = []
    colors = []

    for key, label in LABELS.items():
        val = food_data[key] if key != "ENA" else ENA
        if val > 0:
            labels.append(label)
            values.append(val)
            colors.append(COLORS[key])

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo="label+percent",
            textfont=dict(size=14),
            hovertemplate="<b>%{label}</b>: %{value:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(
            text=f"Distribución Composicional — {food_name}",
            font=dict(size=20, family="Montserrat, sans-serif"),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=550,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=13),
        ),
        margin=dict(t=70, b=110, l=20, r=20),
    )
    return fig


def plot_energy_funnel(food_name, energy):
    """
    Visualiza el flujo de cálculo de energía: GE → DE → ME.

    Parámetros:
        food_name (str): Nombre del alimento.
        energy (dict): Resultado de calculate_energy().

    Retorna:
        plotly.graph_objects.Figure
    """
    steps = ["Energía Bruta (GE)", "Energía Digestible (DE)", "Energía Metabolizable (ME)"]
    values = [energy["GE"], energy["DE"], energy["ME"]]

    fig = go.Figure(
        go.Funnel(
            y=steps,
            x=values,
            textinfo="value+percent initial",
            marker=dict(color=["#2176FF", "#52B788", "#FFB703"]),
            connector=dict(line=dict(color="rgb(63, 63, 63)", dash="dot", width=1)),
            hovertemplate="<b>%{y}</b><br>%{x:.2f} kcal/100g<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(
            text=f"Flujo de Energía NRC — {food_name}",
            font=dict(size=16, family="Montserrat, sans-serif"),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(t=60, b=40, l=140, r=40),
    )
    return fig


def plot_comparison_bar(selected_foods):
    """
    Compara la energía metabolizable de múltiples alimentos en un gráfico de barras.

    Parámetros:
        selected_foods (list[str]): Lista de nombres de alimentos a comparar.

    Retorna:
        plotly.graph_objects.Figure
    """
    names = []
    me_values = []
    ge_values = []
    de_values = []
    emoji_names = []

    for fname in selected_foods:
        fdata = get_food_data(fname)
        if fdata:
            energy = calculate_energy(fdata)
            names.append(fname)
            emoji_names.append(f"{fdata.get('emoji', '')} {fname}")
            me_values.append(energy["ME"])
            de_values.append(energy["DE"])
            ge_values.append(energy["GE"])

    fig = go.Figure()
    fig.add_trace(go.Bar(name="GE (kcal/100g)", x=emoji_names, y=ge_values, marker_color="#8E9AAF"))
    fig.add_trace(go.Bar(name="DE (kcal/100g)", x=emoji_names, y=de_values, marker_color="#52B788"))
    fig.add_trace(go.Bar(name="ME (kcal/100g)", x=emoji_names, y=me_values, marker_color="#2176FF"))

    fig.update_layout(
        barmode="group",
        title=dict(
            text="Comparación de Energía entre Alimentos",
            font=dict(size=16, family="Montserrat, sans-serif"),
        ),
        yaxis_title="kcal / 100 g",
        xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=-0.45, xanchor="center", x=0.5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(t=60, b=130, l=60, r=40),
    )
    return fig


def plot_energy_breakdown_stacked(selected_foods):
    """
    Gráfico de barras apiladas mostrando ME de cada alimento desglosada
    por contribución porcentual de Proteína, Grasa y Carbohidratos.

    Parámetros:
        selected_foods (list[str]): Lista de nombres de alimentos a comparar.

    Retorna:
        plotly.graph_objects.Figure
    """
    emoji_names = []
    me_pb_vals = []
    me_ee_vals = []
    me_cho_vals = []

    for fname in selected_foods:
        fdata = get_food_data(fname)
        if fdata:
            bd = calculate_energy_breakdown(fdata)
            emoji_names.append(f"{fdata.get('emoji', '')} {fname}")
            me_pb_vals.append(bd["me_pb"])
            me_ee_vals.append(bd["me_ee"])
            me_cho_vals.append(bd["me_cho"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Proteína (PB)",
        x=emoji_names,
        y=me_pb_vals,
        marker_color="#2176FF",
        hovertemplate="<b>Proteína</b><br>%{y:.1f} kcal/100g<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Grasa (EE)",
        x=emoji_names,
        y=me_ee_vals,
        marker_color="#FFB703",
        hovertemplate="<b>Grasa</b><br>%{y:.1f} kcal/100g<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Carbohidratos + Fibra",
        x=emoji_names,
        y=me_cho_vals,
        marker_color="#52B788",
        hovertemplate="<b>Carbohidratos + Fibra</b><br>%{y:.1f} kcal/100g<extra></extra>",
    ))

    fig.update_layout(
        barmode="stack",
        title=dict(
            text="Origen de la Energía Metabolizable por Alimento",
            font=dict(size=16, family="Montserrat, sans-serif"),
        ),
        yaxis_title="Energía Metabolizable (kcal / 100 g)",
        xaxis_tickangle=-25,
        legend=dict(orientation="h", yanchor="bottom", y=-0.45, xanchor="center", x=0.5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=480,
        margin=dict(t=60, b=140, l=60, r=40),
    )
    return fig


def show_energy_breakdown_cards(selected_foods):
    """
    Renderiza cards individuales por alimento con el desglose energético porcentual
    e información de las fuentes principales de cada nutriente.

    Parámetros:
        selected_foods (list[str]): Lista de nombres de alimentos a mostrar.
    """
    cols = st.columns(min(len(selected_foods), 3))
    for idx, fname in enumerate(selected_foods):
        fdata = get_food_data(fname)
        if not fdata:
            continue
        bd = calculate_energy_breakdown(fdata)
        col = cols[idx % 3]

        source_pb = fdata.get("source_pb", "")
        source_ee = fdata.get("source_ee", "")
        source_fc = fdata.get("source_fc", "")

        source_pb_html = (
            f'<div style="font-size:0.75rem;color:#4a5568;margin-top:2px;margin-bottom:6px;">'
            f'Proviene de: {source_pb}</div>'
            if source_pb else ""
        )
        source_ee_html = (
            f'<div style="font-size:0.75rem;color:#4a5568;margin-top:2px;margin-bottom:6px;">'
            f'Proviene de: {source_ee}</div>'
            if source_ee else ""
        )
        source_fc_html = (
            f'<div style="font-size:0.75rem;color:#4a5568;margin-top:2px;margin-bottom:6px;">'
            f'Proviene de: {source_fc}</div>'
            if source_fc else ""
        )

        with col:
            st.markdown(
                f"""
                <div style="background:#fff;border:1px solid #e0e7ef;border-radius:12px;
                            padding:16px;margin-bottom:12px;box-shadow:0 2px 8px #0001;">
                    <div style="font-size:1.6rem;text-align:center;">{fdata.get('emoji','')}</div>
                    <div style="font-weight:700;font-size:0.95rem;text-align:center;
                                color:#2C3E50;margin:6px 0 10px 0;line-height:1.3;">{fname}</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                margin-bottom:5px;">
                        <span style="color:#2176FF;font-weight:600;font-size:0.85rem;">🥩 Proteína</span>
                        <span style="background:#2176FF22;color:#2176FF;border-radius:8px;
                                     padding:2px 8px;font-size:0.88rem;font-weight:700;">
                            {bd['pct_pb']:.1f}%
                        </span>
                    </div>
                    <div style="background:#2176FF;height:6px;border-radius:4px;
                                width:{bd['pct_pb']:.1f}%;margin-bottom:2px;"></div>
                    {source_pb_html}
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                margin-bottom:5px;">
                        <span style="color:#FFB703;font-weight:600;font-size:0.85rem;">🧈 Grasa</span>
                        <span style="background:#FFB70322;color:#b57d00;border-radius:8px;
                                     padding:2px 8px;font-size:0.88rem;font-weight:700;">
                            {bd['pct_ee']:.1f}%
                        </span>
                    </div>
                    <div style="background:#FFB703;height:6px;border-radius:4px;
                                width:{bd['pct_ee']:.1f}%;margin-bottom:2px;"></div>
                    {source_ee_html}
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                margin-bottom:5px;">
                        <span style="color:#52B788;font-weight:600;font-size:0.85rem;">🌾 Carbohidratos</span>
                        <span style="background:#52B78822;color:#1b7a53;border-radius:8px;
                                     padding:2px 8px;font-size:0.88rem;font-weight:700;">
                            {bd['pct_cho']:.1f}%
                        </span>
                    </div>
                    <div style="background:#52B788;height:6px;border-radius:4px;
                                width:{bd['pct_cho']:.1f}%;margin-bottom:2px;"></div>
                    {source_fc_html}
                    <div style="font-size:0.8rem;color:#5a6e8c;text-align:center;margin-top:6px;">
                        ME: <b>{bd['ME']:.1f} kcal/100g</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def build_energy_breakdown_table(selected_foods):
    """
    Construye un DataFrame con el desglose energético de cada alimento seleccionado.

    Columnas: Alimento | Proteína (kcal) | Grasa (kcal) | Carbohidratos (kcal) | GE | DE | ME

    Parámetros:
        selected_foods (list[str]): Lista de nombres de alimentos.

    Retorna:
        pandas.DataFrame
    """
    rows = []
    for fname in selected_foods:
        fdata = get_food_data(fname)
        if not fdata:
            continue
        bd = calculate_energy_breakdown(fdata)
        rows.append({
            "Alimento": f"{fdata.get('emoji','')} {fname}",
            "Proteína (kcal/100g)": bd["kcal_pb"],
            "Grasa (kcal/100g)": bd["kcal_ee"],
            "Carbohidratos (kcal/100g)": bd["kcal_cho"],
            "GE Total (kcal/100g)": bd["GE"],
            "DE Total (kcal/100g)": bd["DE"],
            "ME Total (kcal/100g)": bd["ME"],
        })
    return pd.DataFrame(rows)


def plot_nutrient_comparison(mer_animal, me_total_kcal, req_pb_g, gramos_pb, req_ee_g, gramos_ee):
    """
    Crea un gráfico de subplots (3 paneles) comparando Requerimiento vs Aporte
    para Energía, Proteína y Grasa, con colores que indican el estado de cobertura.

    Colores:
        - 🔵 Azul  (#2176FF) : Aporte < 90% del requerimiento (bajo)
        - 🟢 Verde (#52B788) : Aporte entre 90-110% (en rango)
        - 🟠 Naranja (#FF6B35): Aporte > 110% (excedido)

    Parámetros:
        mer_animal (float)   : Requerimiento energético diario (kcal/día).
        me_total_kcal (float): Energía aportada por la ración (kcal/día).
        req_pb_g (float|None): Requerimiento mínimo de proteína (g/día).
        gramos_pb (float)    : Proteína aportada por la ración (g/día).
        req_ee_g (float|None): Requerimiento mínimo de grasa (g/día).
        gramos_ee (float)    : Grasa aportada por la ración (g/día).

    Retorna:
        plotly.graph_objects.Figure
    """
    def _coverage_color(aporte, req):
        if req is None or req <= 0:
            return "#2176FF"
        pct = (aporte / req) * 100.0
        if pct < 90.0:
            return "#2176FF"   # Azul — bajo
        elif pct <= 110.0:
            return "#52B788"   # Verde — en rango
        else:
            return "#FF6B35"   # Naranja — excedido

    def _coverage_label(aporte, req):
        if req is None or req <= 0:
            return "Sin referencia"
        pct = (aporte / req) * 100.0
        if pct < 90.0:
            return f"🔵 Bajo ({pct:.0f}%)"
        elif pct <= 110.0:
            return f"🟢 En rango ({pct:.0f}%)"
        else:
            return f"🟠 Excedido ({pct:.0f}%)"

    panels = [
        {
            "title": "⚡ Energía",
            "unit": "kcal/día",
            "req": mer_animal,
            "aporte": me_total_kcal,
        },
        {
            "title": "🥩 Proteína (PB)",
            "unit": "g/día",
            "req": req_pb_g if req_pb_g else 0.0,
            "aporte": gramos_pb,
        },
        {
            "title": "🧈 Grasa (EE)",
            "unit": "g/día",
            "req": req_ee_g if req_ee_g else 0.0,
            "aporte": gramos_ee,
        },
    ]

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=[p["title"] for p in panels],
        horizontal_spacing=0.12,
    )

    for i, panel in enumerate(panels, start=1):
        aporte_color = _coverage_color(panel["aporte"], panel["req"])
        show_legend = (i == 1)

        fig.add_trace(
            go.Bar(
                name="🎯 Requerimiento",
                x=["Requerimiento"],
                y=[panel["req"]],
                marker_color="#8E9AAF",
                text=[f"{panel['req']:.1f}"],
                textposition="outside",
                hovertemplate=f"<b>Requerimiento</b><br>%{{y:.2f}} {panel['unit']}<extra></extra>",
                showlegend=show_legend,
                legendgroup="req",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Bar(
                name="📦 Aporte del Alimento",
                x=["Aporte"],
                y=[panel["aporte"]],
                marker_color=aporte_color,
                text=[f"{panel['aporte']:.1f}"],
                textposition="outside",
                hovertemplate=(
                    f"<b>Aporte</b><br>%{{y:.2f}} {panel['unit']}<br>"
                    f"{_coverage_label(panel['aporte'], panel['req'])}<extra></extra>"
                ),
                showlegend=show_legend,
                legendgroup="aporte",
            ),
            row=1,
            col=i,
        )
        fig.update_yaxes(title_text=panel["unit"], row=1, col=i)

    fig.update_layout(
        barmode="group",
        title=dict(
            text="Requerimiento vs Aporte por Nutriente",
            font=dict(size=15, family="Montserrat, sans-serif"),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=430,
        margin=dict(t=80, b=80, l=50, r=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        font=dict(family="Montserrat, sans-serif"),
    )
    return fig


def get_foods_by_species(species: str) -> list[str]:
    """
    Filtra alimentos por especie del diccionario FOODS.

    Parámetros:
        species (str): "perro", "gato" o vacío (todos)

    Retorna:
        list[str]: Nombres de alimentos disponibles ordenados alfabéticamente
    """
    if not species or species.strip() == "":
        return sorted(list(FOODS.keys()))

    species_lower = species.lower().strip()
    alimentos_filtrados = []

    # "perro" in session_state maps to "canino" in the XLSX species field
    # "gato" in session_state maps to "felino" or "gato" in the XLSX species field
    _PERRO_TERMS = {"perro", "canino", "canine"}
    _GATO_TERMS = {"gato", "felino", "feline"}

    for nombre, datos in FOODS.items():
        food_species = datos.get("species", "").lower()
        food_category = datos.get("category", "").lower()

        if "perro" in species_lower:
            if any(t in food_species for t in _PERRO_TERMS) or any(t in food_category for t in _PERRO_TERMS):
                alimentos_filtrados.append(nombre)
        elif "gato" in species_lower:
            if any(t in food_species for t in _GATO_TERMS) or any(t in food_category for t in _GATO_TERMS):
                alimentos_filtrados.append(nombre)

    # Si no hay resultados filtrados, devolver todos (fallback)
    if not alimentos_filtrados:
        return sorted(list(FOODS.keys()))

    return sorted(alimentos_filtrados)


def filtrar_alimentos_por_busqueda(query: str, alimentos: list) -> list[str]:
    """
    Filtra alimentos por búsqueda de texto en nombre/marca (case-insensitive).

    Parámetros:
        query (str): Texto de búsqueda (puede estar vacío)
        alimentos (list): Lista de nombres de alimentos

    Retorna:
        list[str]: Alimentos que coinciden con la búsqueda
    """
    if not query or query.strip() == "":
        return alimentos

    query_lower = query.lower().strip()
    resultados = [alim for alim in alimentos if query_lower in alim.lower()]
    return sorted(resultados)


def show_food_analysis():
    """
    Renderiza la interfaz de análisis nutricional en el Tab de Análisis de Streamlit.
    """
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
            background-color: #4A5568;
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
        .decision-card {
            border-radius: 12px;
            padding: 20px 24px;
            margin: 20px 0;
            border-left: 6px solid;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            text-align: center;
        }
        .decision-card.low {
            background: rgba(33, 118, 255, 0.08);
            border-left-color: #2176FF;
            color: #1254d1;
        }
        .decision-card.adequate {
            background: rgba(82, 183, 136, 0.08);
            border-left-color: #52B788;
            color: #1b7a53;
        }
        .decision-card.moderate {
            background: rgba(255, 183, 3, 0.08);
            border-left-color: #FFB703;
            color: #92400e;
        }
        .decision-card.high {
            background: rgba(244, 132, 95, 0.08);
            border-left-color: #F4845F;
            color: #933b1a;
        }
        .decision-icon { font-size: 32px; margin-bottom: 8px; }
        .decision-status { font-size: 18px; font-weight: 700; margin-bottom: 6px; }
        .decision-percentage { font-size: 28px; font-weight: 700; margin: 8px 0; }
        .decision-details { font-size: 13px; opacity: 0.85; margin: 8px 0; }
        .decision-diff { font-size: 14px; font-weight: 600; margin-top: 8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.header("Análisis Nutricional de Alimentos")
    st.markdown(
        "Selecciona un alimento para ver su composición proximal y el cálculo de "
        "energía metabolizable según el modelo **NRC**."
    )

    # Full list kept for the comparison multiselect later in this function
    food_names = get_food_names()

    # ── Especie desde Pestaña 1 ───────────────────────────────────────────────
    especie = st.session_state.get("especie_mascota", "")
    if especie:
        st.markdown(f"**🐾 Especie:** {especie.capitalize()}")
        st.markdown("---")

    # ── Filtrar alimentos por especie ─────────────────────────────────────────
    alimentos_disponibles = get_foods_by_species(especie)

    col_search, col_info = st.columns([3, 1])
    with col_search:
        query_busqueda = st.text_input(
            "🔍 Busca un alimento (nombre o marca):",
            placeholder="Ej: Pro Plan, Purina, Royal Canin...",
            key="food_search_input",
            help="Escribe para filtrar alimentos disponibles",
        )
    with col_info:
        _plural_especie = {"perro": "perros", "gato": "gatos"}.get(especie.lower(), "")
        st.metric(
            "Disponibles",
            len(alimentos_disponibles),
            f"para {_plural_especie}" if _plural_especie else None,
        )

    # ── Filtrar dinámicamente por búsqueda ────────────────────────────────────
    alimentos_filtrados = filtrar_alimentos_por_busqueda(query_busqueda, alimentos_disponibles)

    if query_busqueda:
        st.caption(f"📌 {len(alimentos_filtrados)} resultado(s) encontrado(s)")

    if not alimentos_filtrados:
        st.warning(f"❌ No se encontraron alimentos con '{query_busqueda}'")
        especie_info = f" para {_plural_especie}" if _plural_especie else ""
        st.info(f"💡 **Alimentos disponibles{especie_info}:**")
        cols = st.columns(2)
        for idx, alim in enumerate(alimentos_disponibles[:10]):
            with cols[idx % 2]:
                st.write(f"• {alim}")
        if len(alimentos_disponibles) > 10:
            st.caption(f"...y {len(alimentos_disponibles) - 10} más")
        return

    food_name = st.selectbox(
        "Selecciona un alimento balanceado:",
        alimentos_filtrados,
        key="analysis_food_selector",
        help="Elige el alimento que consume tu mascota",
    )

    # Guardar en session_state para otras pestañas
    st.session_state["alimento_seleccionado"] = food_name
    st.session_state["food_name"] = food_name

    food_data = get_food_data(food_name)
    if food_data is None:
        st.error("No se encontraron datos para el alimento seleccionado.")
        return

    # ---- Encabezado del alimento ----
    st.markdown(
        f"""
        <div style="background:linear-gradient(90deg,#2176ff11,#eef4fc);
                    border-left:5px solid #2176FF;border-radius:10px;padding:16px 20px;margin-bottom:16px;">
            <span style="font-size:2rem;">{food_data.get('emoji','')}</span>
            <span style="font-size:1.4rem;font-weight:700;color:#2C3E50;margin-left:10px;">{food_name}</span>
            <br>
            <span style="color:#5a6e8c;font-size:0.95rem;">{food_data.get('description','')}</span>
            &nbsp;&nbsp;<span style="background:#2176FF22;color:#2176FF;border-radius:6px;
                                     padding:2px 10px;font-size:0.85rem;font-weight:600;">
                {food_data.get('category','')}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Tabla de composición proximal (editable) ----
    st.subheader("📊 Composición Proximal")
    st.markdown(
        "<small style='color:#5a6e8c;'>Edita los valores para recalcular automáticamente la energía y los gráficos.</small>",
        unsafe_allow_html=True,
    )

    # Column mapping: display name → food_data key
    EDIT_COLS = {
        "PB (%)": "PB",
        "EE (%)": "EE",
        "Cenizas (%)": "Ash",
        "Humedad (%)": "Humidity",
        "FC (%)": "FC",
    }

    # Sanitize food_name for use as a widget key
    safe_key = "".join(c if c.isalnum() else "_" for c in food_name)

    # Initialise session_state with original food values (only on first load for this food)
    session_key = f"comp_data_{safe_key}"
    if session_key not in st.session_state:
        st.session_state[session_key] = {col: food_data[key] for col, key in EDIT_COLS.items()}

    with st.expander("✏️ Editar Valores", expanded=False):
        edit_df = pd.DataFrame([st.session_state[session_key]])
        edited = st.data_editor(
            edit_df,
            use_container_width=True,
            hide_index=True,
            key=f"comp_editor_{safe_key}",
            column_config={
                "PB (%)": st.column_config.NumberColumn("PB (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f"),
                "EE (%)": st.column_config.NumberColumn("EE (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f"),
                "Cenizas (%)": st.column_config.NumberColumn("Cenizas (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f"),
                "Humedad (%)": st.column_config.NumberColumn("Humedad (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f"),
                "FC (%)": st.column_config.NumberColumn("FC (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f"),
            },
        )
        # Persist edits into session_state so they survive re-runs
        for col in EDIT_COLS:
            st.session_state[session_key][col] = float(edited[col].iloc[0])

    # Build updated food_data from session_state (always up-to-date)
    edited_food_data = dict(food_data)
    for col, key in EDIT_COLS.items():
        edited_food_data[key] = st.session_state[session_key][col]

    # Recalculate derived values from edited data
    ENA = calculate_ena(edited_food_data)
    energy = calculate_energy(edited_food_data)

    # ---- Métricas de nutrientes proximales ----
    st.markdown("#### 📊 Composición Proximal")

    prox_col1, prox_col2 = st.columns(2)
    with prox_col1:
        st.metric("🥩 Proteína Bruta (PB)", f"{edited_food_data['PB']:.2f} %",
                  help="PB: Proteína Bruta (base tal como está)")
        st.metric("⚫ Cenizas", f"{edited_food_data['Ash']:.2f} %",
                  help="Contenido de cenizas (minerales totales)")
        st.metric("🌾 Fibra Cruda (FC)", f"{edited_food_data['FC']:.2f} %",
                  help="Fibra Cruda (base tal como está)")
    with prox_col2:
        st.metric("🧈 Extracto Etéreo (EE)", f"{edited_food_data['EE']:.2f} %",
                  help="EE: Grasa o Extracto Etéreo (base tal como está)")
        st.metric("💧 Humedad", f"{edited_food_data['Humidity']:.2f} %",
                  help="Contenido de humedad del alimento")
        st.metric("🌽 Extracto No Nitrogenado (ENA)", f"{ENA:.2f} %",
                  help="ENA calculado por diferencia: 100 − PB − EE − Ash − Humedad − FC")

    st.markdown("#### 📈 Valores Derivados")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔬 Materia Seca (MS)", f"{energy['MS']:.1f} %",
                  help="MS = 100 − Humedad")
    with col2:
        st.metric("📐 FC en base MS", f"{energy['FC_MS']:.2f} %",
                  help="FC_MS = (FC / MS) × 100")

    # ---- Cálculo de Aporte Energético ----
    st.subheader("🧮 Cálculo de Aporte Energético")
    st.markdown(
        "Ingresa los **gramos diarios** del alimento seleccionado para calcular el aporte energético "
        "y compararlo con el requerimiento diario de la mascota (MER)."
    )

    gramos_key = f"gramos_alimento_{food_name}"
    gramos_input = st.number_input(
        f"Gramos diarios de **{food_name}**",
        min_value=0.0,
        max_value=5000.0,
        value=float(st.session_state.get(gramos_key, 100.0)),
        step=10.0,
        key=gramos_key,
    )

    # Energía metabolizable aportada
    me_por_100g = energy["ME"]
    me_total_kcal = (me_por_100g / 100.0) * gramos_input

    # MER del animal desde sesión (calculado en Tab 1)
    mer_animal = st.session_state.get("energia_actual", None)

    # Gramos de nutrientes aportados (siempre calculados)
    gramos_pb = (edited_food_data["PB"] / 100.0) * gramos_input
    gramos_ee = (edited_food_data["EE"] / 100.0) * gramos_input

    # Requerimientos de proteína y grasa del perfil de la mascota (Tab 1)
    req_pb_g = st.session_state.get("req_pb_g", None)
    req_ee_g = st.session_state.get("req_ee_g", None)

    # ── 🩺 DECISIÓN NUTRICIONAL DEL ALIMENTO ──────────────────────────────────
    st.markdown("---")
    st.subheader("🩺 Decisión Nutricional del Alimento")

    if mer_animal and mer_animal > 0:
        cobertura_energetica_pct = (me_total_kcal / mer_animal) * 100.0
        diferencia_kcal = me_total_kcal - mer_animal
        gramos_recomendados = (mer_animal / (me_por_100g / 100.0)) if me_por_100g > 0 else 0.0
        diferencia_g = gramos_recomendados - gramos_input

        clase = get_clase_decision(cobertura_energetica_pct)
        resultado = get_resultado_cobertura(cobertura_energetica_pct)
        icono = DECISION_COLORS[clase]
        signo = "+" if diferencia_kcal > 0 else ""

        st.markdown(
            f"""
            <div class="decision-card {clase}">
                <div class="decision-icon">{icono}</div>
                <div class="decision-status">{resultado.upper()}</div>
                <div class="decision-percentage">{cobertura_energetica_pct:.1f}%</div>
                <div class="decision-details">
                    Aporte: {me_total_kcal:.0f} kcal/día &nbsp;·&nbsp; Requerimiento: {mer_animal:.0f} kcal/día
                </div>
                <div class="decision-diff">{signo}{diferencia_kcal:.0f} kcal/día</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric(
                "📌 Recomendado",
                f"{gramos_recomendados:.0f} g/día",
                help="Gramos necesarios para cubrir exactamente el MER del animal.",
            )
        with col_r2:
            st.metric(
                "📊 Actual",
                f"{gramos_input:.0f} g/día",
                help="Gramos diarios que actualmente ingresa el animal.",
            )
        with col_r3:
            if abs(diferencia_g) < 5:
                estado_g = "✓ En rango aceptable"
            elif diferencia_g > 0:
                estado_g = f"↑ Faltan {diferencia_g:.0f} g"
            else:
                estado_g = f"↓ Exceso {abs(diferencia_g):.0f} g"
            st.metric(
                "📏 Diferencia",
                estado_g,
                help="Diferencia entre la cantidad recomendada y la actual.",
            )

        # Diagnóstico proteína y grasa
        cob_pb = (gramos_pb / req_pb_g * 100.0) if req_pb_g and req_pb_g > 0 else None
        cob_ee = (gramos_ee / req_ee_g * 100.0) if req_ee_g and req_ee_g > 0 else None

        if cob_pb is not None or cob_ee is not None:
            col_p, col_e_diag = st.columns(2)
            if cob_pb is not None:
                pb_estado = (
                    "✓ Adecuada" if 90 <= cob_pb <= 110
                    else ("⚠ Insuficiente" if cob_pb < 90 else "⚠ Excedida")
                )
                with col_p:
                    st.metric(
                        "🥩 Proteína",
                        f"{cob_pb:.0f}%",
                        pb_estado,
                        help=f"Proteína aportada: {gramos_pb:.1f} g vs requerimiento: {req_pb_g:.1f} g",
                    )
            if cob_ee is not None:
                ee_estado = (
                    "✓ Adecuada" if 90 <= cob_ee <= 110
                    else ("⚠ Insuficiente" if cob_ee < 90 else "⚠ Excedida")
                )
                with col_e_diag:
                    st.metric(
                        "🧈 Grasa",
                        f"{cob_ee:.0f}%",
                        ee_estado,
                        help=f"Grasa aportada: {gramos_ee:.1f} g vs requerimiento: {req_ee_g:.1f} g",
                    )
        else:
            cob_pb = None
            cob_ee = None

        # Párrafo interpretativo
        interpretacion = generar_interpretacion_alimento(
            food_name, cobertura_energetica_pct, me_total_kcal, mer_animal,
            gramos_input, gramos_recomendados, cob_pb, cob_ee,
        )
        st.info(interpretacion)
    else:
        st.info(
            "💡 Completa el perfil de la mascota en la pestaña **Perfil de Mascota** "
            "para obtener el MER y ver la decisión nutricional."
        )

    st.markdown("---")

    # ── Cards de energía ─────────────────────────────────────────────────────
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        st.metric(
            label="⚡ Energía Aportada",
            value=f"{me_total_kcal:.1f} kcal",
            help="Energía Metabolizable total aportada por los gramos ingresados.",
        )
    with col_e2:
        mer_display = f"{mer_animal:.1f} kcal/día" if mer_animal else "No calculado"
        st.metric(
            label="🎯 MER del Animal",
            value=mer_display,
            help="Requerimiento Energético Metabolizable diario del animal (calculado en Tab 1).",
        )
    with col_e3:
        if mer_animal and mer_animal > 0:
            cobertura_pct = (me_total_kcal / mer_animal) * 100.0
            delta_color = "normal" if cobertura_pct <= ENERGY_COVERAGE_THRESHOLD else "inverse"
            st.metric(
                label="📊 Cobertura Energética",
                value=f"{cobertura_pct:.1f}%",
                delta=f"{cobertura_pct - 100:.1f}% vs requerimiento",
                delta_color=delta_color,
                help="Porcentaje del requerimiento energético diario cubierto.",
            )
        else:
            st.metric(label="📊 Cobertura Energética", value="—", help="Completa el perfil en Tab 1 para obtener el MER.")

    # ── Expander: Cálculo energético detallado (NRC) ──────────────────────────
    with st.expander("📋 Ver cálculo energético detallado", expanded=False):
        st.markdown(
            """
            <div style="background:#fffbe6;border-left:4px solid #FFB703;border-radius:8px;
                        padding:12px 18px;margin-bottom:16px;font-size:0.93rem;">
                <b>Ecuaciones utilizadas (NRC):</b><br>
                1. <code>GE = (5.7×PB) + (9.4×EE) + [4.1×(ENA+FC)]</code><br>
                2. <code>%DE = 91.2 - (1.43×FC_MS)</code><br>
                3. <code>DE = GE × (%DE/100)</code><br>
                4. <code>ME = DE - (1.04×PB)</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 📋 Cálculo Paso a Paso (NRC)")
        energy_calc_rows = [
            ("Materia Seca (MS)", energy["MS"], "%"),
            ("FC en base MS (FC_MS)", energy["FC_MS"], "%"),
            ("Energía Bruta (GE)", energy["GE"], "kcal/100g"),
            ("Digestibilidad Energética (DE%)", energy["DE_pct"], "%"),
            ("Energía Digestible (DE)", energy["DE"], "kcal/100g"),
            ("Energía Metabolizable (ME)", energy["ME"], "kcal/100g"),
        ]
        html_energy_calc = "<table class='energy-table'><thead><tr><th>Parámetro</th><th>Valor</th><th>Unidad</th></tr></thead><tbody>"
        for param, val, unit in energy_calc_rows:
            html_energy_calc += f"<tr><td>{param}</td><td>{val:.2f}</td><td>{unit}</td></tr>"
        html_energy_calc += "</tbody></table>"
        st.markdown(html_energy_calc, unsafe_allow_html=True)

        me_por_kg = energy["ME"] * 10.0
        st.markdown(
            f"""
            <div style="background:linear-gradient(90deg,#2176ff,#52B788);
                        border-radius:10px;padding:16px;text-align:center;margin:10px 0 20px 0;">
                <span style="color:#fff;font-size:1.1rem;">Energía Metabolizable</span><br>
                <span style="color:#fff;font-size:2.5rem;font-weight:700;">{energy['ME']:.1f}</span>
                <span style="color:#ffffffcc;font-size:1.2rem;"> kcal / 100 g</span>
                &nbsp;&nbsp;
                <span style="color:#ffffffcc;font-size:1rem;">({me_por_kg:.0f} kcal / kg)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 📊 Desglose del Aporte Energético")
        base_rows = [
            {"Concepto": "ME del alimento (kcal/100g)", "Valor": f"{me_por_100g:.2f} kcal/100g"},
            {"Concepto": f"Gramos diarios de {food_name}", "Valor": f"{gramos_input:.1f} g/día"},
            {"Concepto": "Gramos de Proteína Bruta (PB)", "Valor": f"{gramos_pb:.2f} g/día"},
            {"Concepto": "Gramos de Grasa (EE)", "Valor": f"{gramos_ee:.2f} g/día"},
            {"Concepto": "Energía Metabolizable aportada", "Valor": f"{me_total_kcal:.2f} kcal/día"},
        ]
        if mer_animal and mer_animal > 0:
            _cob = (me_total_kcal / mer_animal) * 100.0
            base_rows += [
                {"Concepto": "MER del animal", "Valor": f"{mer_animal:.2f} kcal/día"},
                {"Concepto": "Cobertura energética", "Valor": f"{_cob:.1f}%"},
            ]
        aporte_df = pd.DataFrame(base_rows)
        html_aporte = "<table class='energy-table'><thead><tr><th>Concepto</th><th>Valor</th></tr></thead><tbody>"
        for _, row in aporte_df.iterrows():
            html_aporte += f"<tr><td>{row['Concepto']}</td><td>{row['Valor']}</td></tr>"
        html_aporte += "</tbody></table>"
        st.markdown(html_aporte, unsafe_allow_html=True)

    # ── Gráfico de composición (torta/donut) ──────────────────────────────────
    st.markdown("#### 📈 Composición del Alimento")
    st.plotly_chart(plot_macronutrients_pie(food_name, edited_food_data), use_container_width=True)

    # Gráfico comparativo mejorado (solo cuando MER disponible)
    if mer_animal and mer_animal > 0:
        st.plotly_chart(
            plot_nutrient_comparison(
                mer_animal, me_total_kcal,
                req_pb_g, gramos_pb,
                req_ee_g, gramos_ee,
            ),
            use_container_width=True,
        )

    # ── Comparación de Origen Energético entre Alimentos ─────────────────────
    st.subheader("📊 Comparación del Origen de la Energía entre Alimentos")
    st.markdown(
        "Este gráfico muestra **de qué nutriente proviene la energía** del alimento "
        "(Proteína, Grasa y Carbohidratos) según el modelo NRC. "
        "Selecciona varios alimentos para comparar su perfil energético."
    )
    selected_for_comparison = st.multiselect(
        "Selecciona alimentos para comparar (hasta 6)",
        food_names,
        default=[food_name] if food_name else [],
        key="analysis_comparison_selector",
        max_selections=6,
    )
    if selected_for_comparison:
        # Gráfico de barras apiladas
        st.plotly_chart(plot_energy_breakdown_stacked(selected_for_comparison), use_container_width=True)

        # Cards individuales
        st.markdown("#### 🃏 Desglose por Alimento")
        show_energy_breakdown_cards(selected_for_comparison)

        # Tabla de desglose energético
        st.markdown("#### 📋 Tabla de Desglose Energético")
        breakdown_df = build_energy_breakdown_table(selected_for_comparison)
        if not breakdown_df.empty:
            html_breakdown = "<table class='energy-table'><thead><tr>"
            for col in breakdown_df.columns:
                html_breakdown += f"<th>{col}</th>"
            html_breakdown += "</tr></thead><tbody>"
            for _, row in breakdown_df.iterrows():
                html_breakdown += "<tr>"
                for val in row:
                    if isinstance(val, float):
                        html_breakdown += f"<td>{val:.2f}</td>"
                    else:
                        html_breakdown += f"<td>{val}</td>"
                html_breakdown += "</tr>"
            html_breakdown += "</tbody></table>"
            st.markdown(html_breakdown, unsafe_allow_html=True)
    else:
        st.info("Selecciona al menos un alimento para ver la comparación energética.")
