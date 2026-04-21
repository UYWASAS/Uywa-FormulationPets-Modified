def ajustar_nutrientes_referencia_y_generar_tabla(nutrientes_ref, especie, etapa, energia_kcal_kg_actual):
    """
    Ajusta los valores de referencia de nutrientes y genera la tabla para mostrar en Streamlit.

    Argumentos:
    nutrientes_ref: dict con los datos de referencia reorganizados.
    especie: especie de la mascota ("perro", "gato").
    etapa: etapa de la vida ("cachorro", "adulto").
    energia_kcal_kg_actual: energía actual calculada (MER en kcal/kg).

    Retorna:
    DataFrame con los nutrientes ajustados.
    """
    import pandas as pd

    # Selección de nutrientes según especie y etapa
    try:
        nutrientes_especie_etapa = nutrientes_ref[especie][etapa]
    except KeyError:
        raise ValueError("Especie o etapa inválida. Verifica la entrada del perfil.")

    # Proceso de ajuste proporcional en base a la energía calculada
    energia_kcal_kg_ref = 1000  # Energía de referencia estándar en kcal/kg
    nutrientes_ajustados = []
    for nutriente, valores in nutrientes_especie_etapa.items():
        min_ref = valores["min"]
        max_ref = valores.get("max", None)
        unidad_ref = valores["unit"]

        if min_ref is None and max_ref is None:
            continue  # Si no hay valores de referencia, saltar el nutriente

        # Ajuste proporcional basado en la energía actual
        if unidad_ref in ["g/100g", "g/kg"]:
            min_aj = (min_ref * energia_kcal_kg_actual / energia_kcal_kg_ref) if min_ref is not None else None
            max_aj = (max_ref * energia_kcal_kg_actual / energia_kcal_kg_ref) if max_ref is not None else None
        else:
            min_aj = min_ref
            max_aj = max_ref

        nutrientes_ajustados.append({
            "Nutriente": nutriente,
            "Min Ajustado": min_aj if min_aj is not None else "",
            "Max Ajustado": max_aj if max_aj is not None else "",
            "Unidad": unidad_ref
        })

    # Generar DataFrame para visualización
    return pd.DataFrame(nutrientes_ajustados)
