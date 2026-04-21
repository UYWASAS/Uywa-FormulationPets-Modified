# ======================== BASE DE DATOS DE ALIMENTOS ========================
# Alimentos balanceados comerciales ecuatorianos — valores extruidos típicos
# compatibles con estándares FEDIAF/NRC/AAFCO
# Unidades: % tal como está (as-fed basis)

FOODS = {
    "Pro Plan Puppy (Cachorro Perro)": {
        "PB": 30.0,
        "EE": 13.0,
        "Ash": 7.0,
        "Humidity": 12.0,
        "FC": 3.0,
        "description": "Alimento balanceado extruido para cachorros con alto contenido proteico y DHA para desarrollo cerebral.",
        "category": "Cachorro Perro",
        "emoji": "🐶",
    },
    "Procan Premium (Adulto Perro)": {
        "PB": 22.0,
        "EE": 10.0,
        "Ash": 6.5,
        "Humidity": 10.0,
        "FC": 4.0,
        "description": "Alimento balanceado extruido para perros adultos de formulación ecuatoriana con cereales y proteína animal.",
        "category": "Adulto Perro",
        "emoji": "🐕",
    },
    "Whiskas Gatos (Adulto Gato)": {
        "PB": 26.0,
        "EE": 11.0,
        "Ash": 6.0,
        "Humidity": 10.0,
        "FC": 2.5,
        "description": "Alimento balanceado extruido para gatos adultos, con taurina y nutrientes esenciales para felinos.",
        "category": "Adulto Gato",
        "emoji": "🐱",
    },
    "Hill's Science Diet Sensitive": {
        "PB": 20.0,
        "EE": 12.0,
        "Ash": 5.5,
        "Humidity": 10.0,
        "FC": 2.0,
        "description": "Alimento balanceado para mascotas con digestión sensible, bajo en fibra y fácil digestibilidad.",
        "category": "Sensitive",
        "emoji": "🌿",
    },
    "Orijen Performance": {
        "PB": 38.0,
        "EE": 18.0,
        "Ash": 8.0,
        "Humidity": 12.0,
        "FC": 3.5,
        "description": "Alimento balanceado premium de alto rendimiento, rico en proteína biológicamente apropiada para perros activos.",
        "category": "Performance",
        "emoji": "🏆",
    },
    "Royal Canin Senior": {
        "PB": 25.0,
        "EE": 11.0,
        "Ash": 6.0,
        "Humidity": 10.0,
        "FC": 4.5,
        "description": "Alimento balanceado para mascotas mayores de 7 años con soporte articular, renal y antioxidantes.",
        "category": "Senior",
        "emoji": "👴",
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
        3. %DE  = 91.2 - (1.43 x FC_MS)
        4. DE   (kcal/100g) = GE x (%DE / 100)
        5. ME   (kcal/100g) = DE - (1.04 x PB)

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
