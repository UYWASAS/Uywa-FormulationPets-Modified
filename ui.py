import streamlit as st

def show_mascota_form(profile, on_update_callback=None):
    """
    Muestra el formulario de edición del perfil de la mascota.
    
    Args:
        profile (dict): Perfil actual de la mascota.
        on_update_callback (callable): Función a llamar después de guardar los cambios.
    """
    mascota = profile.get("mascota", {})

    col_img, col_form = st.columns([1, 4])
    with col_img:
        # Foto de la mascota (uploader o mostrar imagen cargada)
        if "foto_mascota_bytes" not in st.session_state:
            img = st.file_uploader("Foto de la mascota", type=["png", "jpg", "jpeg"], key="foto_mascota")
            if img:
                st.session_state["foto_mascota_bytes"] = img.getvalue()
                st.session_state["foto_mascota_name"] = mascota.get("nombre", "")
        if "foto_mascota_bytes" in st.session_state:
            st.image(st.session_state["foto_mascota_bytes"], width=140)
            nombre = mascota.get("nombre", st.session_state.get("foto_mascota_name", ""))
            st.markdown(f"<div style='text-align:center; font-weight:600; font-size:16px;'>{nombre}</div>", unsafe_allow_html=True)
            if st.button("Eliminar foto de la mascota", key=f"delete_photo_{nombre}"):
                del st.session_state["foto_mascota_bytes"]
                if "foto_mascota_name" in st.session_state:
                    del st.session_state["foto_mascota_name"]

    with col_form:
        col1, col2 = st.columns([2, 2])

        with col1:
            # Nombre, especie, edad
            nombre = st.text_input("Nombre de la mascota", value=mascota.get("nombre", ""))
            especie = st.selectbox("Especie", ["perro", "gato"], index=0 if mascota.get("especie") == "perro" else 1)
            edad = st.number_input("Edad (años)", min_value=0.0, max_value=30.0, value=float(mascota.get("edad", 1.0)))

        with col2:
            # Peso, etapa de vida
            peso = st.number_input("Peso (kg)", min_value=0.1, max_value=120.0, value=float(mascota.get("peso", 12.0)))
            etapa = st.selectbox(
                "Etapa", 
                ["adulto", "cachorro"], 
                index=["adulto", "cachorro"].index(mascota.get("etapa", "adulto"))
            )

        # Condición fisiológica/productiva (sin opciones eliminadas)
        opciones_condicion = ["Castrado", "Entero", "Gestación (Primera mitad)", "Gestación (Segunda mitad)", "Lactancia", "Destete a 4 meses", "5 meses hasta adulto"]
        condicion = st.selectbox(
            "Condición fisiológica/productiva",
            opciones_condicion,
            index=opciones_condicion.index(mascota.get("condicion", "Castrado"))
        )

        # Condición Corporal (BCS) con clave dinámica
        bcs = st.number_input(
            "Condición Corporal (BCS)",
            min_value=1,
            max_value=9,
            value=int(mascota.get("bcs", 5)),  # Valor predeterminado: 5 (ideal)
            key=f"input_bcs_{nombre}"  # Dynamic key based on the pet name
        )

        # Validación de todos los valores antes de realizar cambios
        errors = []
        if not nombre.strip():
            errors.append("El nombre de la mascota no puede estar vacío.")
        if peso <= 0:
            errors.append("El peso debe ser mayor a 0.")
        if edad < 0:
            errors.append("La edad no puede ser negativa.")
        if bcs < 1 or bcs > 9:
            errors.append("El BCS debe estar entre 1 y 9.")

        if errors:
            for error in errors:
                st.error(error)
        else:
            # Botón para guardar el perfil actualizado
            if st.button("Guardar perfil de mascota", key=f"save_profile_{nombre}"):
                profile["mascota"] = {
                    "nombre": nombre,
                    "especie": especie,
                    "edad": edad,
                    "peso": peso,
                    "etapa": etapa,
                    "bcs": bcs,
                    "condicion": condicion,
                }
                st.success("Perfil de mascota actualizado correctamente.")
                if on_update_callback:
                    on_update_callback(profile)

                # Actualizar el nombre vinculado a la foto
                if "foto_mascota_bytes" in st.session_state:
                    st.session_state["foto_mascota_name"] = nombre

    # Resumen visual en forma de tarjeta mejorada
    mascota = profile.get("mascota", {})
    etapa_val = mascota.get('etapa', 'adulto')
    badge_color = "#fef3c7" if etapa_val == "cachorro" else "#d1fae5"
    badge_text = "#92400e" if etapa_val == "cachorro" else "#065f46"
    badge_border = "#fcd34d" if etapa_val == "cachorro" else "#6ee7b7"
    especie_icon = "🐕" if mascota.get('especie', 'perro') == "perro" else "🐈"
    st.markdown(
        f"""
        <div style="border-radius:14px;background:linear-gradient(135deg,#eef4fc 0%,#f0f9ff 100%);
                    padding:20px;margin-top:16px;margin-bottom:8px;
                    box-shadow:0 3px 14px rgba(33,118,255,0.10);
                    border:1px solid #d4e4fc;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                <span style="font-size:36px;">{especie_icon}</span>
                <div>
                    <div style="font-size:20px;font-weight:700;color:#1a202c;">{mascota.get('nombre', '(Sin nombre)')}</div>
                    <span style="display:inline-block;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;
                                 background:{badge_color};color:{badge_text};border:1px solid {badge_border};">
                        {etapa_val.capitalize()}
                    </span>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:15px;color:#2d3748;">
                <div>🎂 <b>Edad:</b> {mascota.get('edad', '---')} años</div>
                <div>⚖️ <b>Peso:</b> {mascota.get('peso', '---')} kg</div>
                <div>📏 <b>BCS:</b> {mascota.get('bcs', '---')} / 9</div>
                <div>🛠️ <b>Condición:</b> {mascota.get('condicion', '---')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
