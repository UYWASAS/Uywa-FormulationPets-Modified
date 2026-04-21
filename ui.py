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

    # Resumen visual en forma de tarjeta
    mascota = profile.get("mascota", {})
    st.markdown(
        f"""
        <div style="border-radius:12px;background:#e3ecf7;padding:18px;margin-bottom:15px;box-shadow:0 2px 10px #adbadb33;">
            <h3 style="margin-top:0;">{mascota.get('nombre', '(Sin nombre)')}</h3>
            <p><b>🐾 Especie:</b> {mascota.get('especie', '---')}</p>
            <p><b>🎂 Edad:</b> {mascota.get('edad', '---')} años</p>
            <p><b>⚖️ Peso:</b> {mascota.get('peso', '---')} kg</p>
            <p><b>🍼 Etapa:</b> {mascota.get('etapa', '---')}</p>
            <p><b>📏 Condición Corporal (BCS):</b> {mascota.get('bcs', '---')}</p>
            <p><b>🛠️ Condición Fisiológica/Productiva:</b> {mascota.get('condicion', '---')}</p>
        </div>
        """, unsafe_allow_html=True
    )
