# ======================== BASE DE DATOS DE ALIMENTOS ========================
# Valores de composición nutricional según estándares comerciales NRC/AAFCO
# Unidades: % tal como está (as-fed basis)

FOODS = {
    "Pollo (pechuga, crudo)": {
        "PB": 23.0,
        "EE": 5.0,
        "Ash": 1.1,
        "Humidity": 70.0,
        "FC": 0.0,
        "description": "Fuente de proteína animal de alta digestibilidad.",
        "category": "Proteína",
        "emoji": "🍗",
    },
    "Arroz (cocido, blanco)": {
        "PB": 2.5,
        "EE": 0.3,
        "Ash": 0.2,
        "Humidity": 68.0,
        "FC": 0.3,
        "description": "Carbohidrato altamente digestible, bajo en fibra.",
        "category": "Carbohidrato",
        "emoji": "🍚",
    },
    "Aceite de pescado": {
        "PB": 0.0,
        "EE": 99.9,
        "Ash": 0.0,
        "Humidity": 0.1,
        "FC": 0.0,
        "description": "Fuente concentrada de energía y ácidos grasos omega-3.",
        "category": "Grasa",
        "emoji": "🐟",
    },
    "Harina de hueso": {
        "PB": 11.0,
        "EE": 3.0,
        "Ash": 68.0,
        "Humidity": 5.0,
        "FC": 0.0,
        "description": "Fuente de calcio y fósforo, suplemento mineral.",
        "category": "Mineral",
        "emoji": "🦴",
    },
    "Maíz (harina, seco)": {
        "PB": 8.5,
        "EE": 3.5,
        "Ash": 1.3,
        "Humidity": 14.0,
        "FC": 2.5,
        "description": "Carbohidrato con aporte energético moderado y algo de fibra.",
        "category": "Carbohidrato",
        "emoji": "🌽",
    },
    "Carne molida (res, 80/20)": {
        "PB": 17.0,
        "EE": 20.0,
        "Ash": 1.0,
        "Humidity": 60.0,
        "FC": 0.0,
        "description": "Proteína animal con contenido moderado-alto en grasa.",
        "category": "Proteína",
        "emoji": "🥩",
    },
}


def calculate_ena(food_data):
    """Calcula el Extracto No Nitrogenado (carbohidratos disponibles) por diferencia."""
    ENA = (
        100
        - food_data["PB"]
        - food_data["EE"]
        - food_data["Ash"]
        - food_data["Humidity"]
        - food_data["FC"]
    )
    return max(0.0, round(ENA, 2))


def calculate_energy(food_data):
    """
    Calcula la energía metabolizable según el modelo NRC para perros y gatos.

    Ecuaciones:
        1. GE  (kcal/100g) = (5.7 × PB) + (9.4 × EE) + [4.1 × (ENA + FC)]
        2. FC_MS (% en materia seca) = FC / MS × 100
        3. %DE  = 91.2 − (1.43 × FC_MS)
        4. DE   (kcal/100g) = GE × (%DE / 100)
        5. ME   (kcal/100g) = DE − (1.04 × PB)

    Retorna:
        dict con GE, ENA, MS, FC_MS, DE_pct, DE y ME.
    """
    PB = food_data["PB"]
    EE = food_data["EE"]
    Ash = food_data["Ash"]
    Humidity = food_data["Humidity"]
    FC = food_data["FC"]

    ENA = calculate_ena(food_data)

    # 1. Energía Bruta
    GE = (5.7 * PB) + (9.4 * EE) + (4.1 * (ENA + FC))

    # 2. Materia Seca y FC en base MS
    MS = max(0.0, 100.0 - Humidity)
    FC_MS = (FC / MS * 100.0) if MS > 0 else 0.0

    # 3. Digestibilidad Energética
    DE_pct = 91.2 - (1.43 * FC_MS)
    DE_pct = min(100.0, max(0.0, DE_pct))

    # 4. Energía Digestible
    DE = GE * (DE_pct / 100.0)

    # 5. Energía Metabolizable
    ME = DE - (1.04 * PB)

    return {
        "ENA": round(ENA, 2),
        "GE": round(GE, 2),
        "MS": round(MS, 2),
        "FC_MS": round(FC_MS, 2),
        "DE_pct": round(DE_pct, 2),
        "DE": round(DE, 2),
        "ME": round(ME, 2),
    }


def get_food_names():
    """Devuelve la lista de nombres de alimentos disponibles."""
    return list(FOODS.keys())


def get_food_data(food_name):
    """Devuelve los datos de composición de un alimento por nombre."""
    return FOODS.get(food_name, None)
