# ======================== ANÁLISIS NUTRICIONAL DE ALIMENTOS ========================
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from food_database import FOODS, calculate_energy, calculate_ena, get_food_names, get_food_data

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
            hovertemplate="<b>%{label}</b>: %{value:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(
            text=f"Distribución Composicional — {food_name}",
            font=dict(size=16, family="Montserrat, sans-serif"),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(t=60, b=100, l=20, r=20),
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


def show_food_analysis():
    """
    Renderiza la interfaz de análisis nutricional en el Tab de Análisis de Streamlit.
    """
    st.header("Análisis Nutricional de Alimentos")
    st.markdown(
        "Selecciona un alimento para ver su composición proximal y el cálculo de "
        "energía metabolizable según el modelo **NRC**."
    )

    food_names = get_food_names()
    food_name = st.selectbox(
        "🔍 Selecciona un alimento balanceado",
        food_names,
        key="analysis_food_selector",
    )

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

    edit_df = pd.DataFrame(
        [{col: food_data[key] for col, key in EDIT_COLS.items()}]
    )

    # Sanitize food_name for use as a widget key
    safe_key = "".join(c if c.isalnum() else "_" for c in food_name)

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

    # Build updated food_data from edited values using the same mapping
    edited_food_data = dict(food_data)
    edited_food_data.update({key: float(edited[col].iloc[0]) for col, key in EDIT_COLS.items()})

    # Recalculate derived values from edited data
    ENA = calculate_ena(edited_food_data)
    energy = calculate_energy(edited_food_data)

    # Show calculated (read-only) values
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric("🌾 ENA / Carbohidratos (%)", f"{ENA:.1f} %", help="Calculado por diferencia: 100 - PB - EE - Ash - Humidity - FC")
    with col_c2:
        st.metric("🔬 Materia Seca (MS) (%)", f"{energy['MS']:.1f} %", help="MS = 100 - Humedad")
    with col_c3:
        st.metric("📐 FC en base MS (%)", f"{energy['FC_MS']:.2f} %", help="FC_MS = (FC / MS) × 100")

    # ---- Gráficos de composición ----
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_macronutrients(food_name, edited_food_data), use_container_width=True)
    with col2:
        st.plotly_chart(plot_macronutrients_pie(food_name, edited_food_data), use_container_width=True)

    # ---- Sección de energía metabolizable ----
    st.subheader("⚡ Cálculo de Energía Metabolizable (Modelo NRC)")

    st.markdown(
        """
        <div style="background:#fffbe6;border-left:4px solid #FFB703;border-radius:8px;
                    padding:12px 18px;margin-bottom:16px;font-size:0.93rem;">
            <b>Ecuaciones utilizadas (NRC):</b><br>
            1. <code>GE = (5.7×PB) + (9.4×EE) + [4.1×(ENA+FC)]</code><br>
            2. <code>%DE = 91.2 - (1.43*FC_MS)</code><br>
            3. <code>DE = GE * (%DE/100)</code><br>
            4. <code>ME = DE - (1.04*PB)</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ME destacada
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

    # Tabla de desglose
    if mer_animal and mer_animal > 0:
        cobertura_pct = (me_total_kcal / mer_animal) * 100.0
        aporte_df = pd.DataFrame([
            {"Concepto": "ME del alimento (kcal/100g)", "Valor": f"{me_por_100g:.2f} kcal/100g"},
            {"Concepto": f"Gramos diarios de {food_name}", "Valor": f"{gramos_input:.1f} g/día"},
            {"Concepto": "Energía Metabolizable aportada", "Valor": f"{me_total_kcal:.2f} kcal/día"},
            {"Concepto": "MER del animal", "Valor": f"{mer_animal:.2f} kcal/día"},
            {"Concepto": "Cobertura energética", "Valor": f"{cobertura_pct:.1f}%"},
        ])
        st.dataframe(aporte_df.set_index("Concepto"), use_container_width=True)

        # Gráfico de barras Requerimiento vs Aporte
        fig_aporte = go.Figure()
        fig_aporte.add_trace(go.Bar(
            name="MER Requerida",
            x=["Energía (kcal/día)"],
            y=[mer_animal],
            marker_color="#8E9AAF",
            text=[f"{mer_animal:.1f} kcal"],
            textposition="outside",
        ))
        fig_aporte.add_trace(go.Bar(
            name="Aporte del Alimento",
            x=["Energía (kcal/día)"],
            y=[me_total_kcal],
            marker_color="#2176FF" if cobertura_pct <= ENERGY_COVERAGE_THRESHOLD else "#FFB703",
            text=[f"{me_total_kcal:.1f} kcal"],
            textposition="outside",
        ))
        fig_aporte.update_layout(
            barmode="group",
            title=dict(
                text="Requerimiento Energético vs Aporte del Alimento",
                font=dict(size=15, family="Montserrat, sans-serif"),
            ),
            yaxis_title="kcal / día",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=360,
            margin=dict(t=60, b=40, l=60, r=40),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_aporte, use_container_width=True)
    else:
        st.info("💡 Completa el perfil de la mascota en la pestaña **Perfil de Mascota** para obtener el MER y calcular la cobertura energética.")

    # ---- Comparación con todos los alimentos ----
    st.subheader("📈 Comparación entre Alimentos")
    st.markdown("Compara la energía bruta, digestible y metabolizable entre los alimentos disponibles.")
    selected_for_comparison = st.multiselect(
        "Selecciona alimentos para comparar",
        food_names,
        default=food_names,
        key="analysis_comparison_selector",
    )
    if selected_for_comparison:
        st.plotly_chart(plot_comparison_bar(selected_for_comparison), use_container_width=True)
    else:
        st.info("Selecciona al menos un alimento para ver la comparación.")
