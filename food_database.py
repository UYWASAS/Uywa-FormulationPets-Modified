# ======================== BASE DE DATOS DE ALIMENTOS ========================
# Alimentos balanceados comerciales ecuatorianos — valores extruidos típicos
# compatibles con estándares FEDIAF/NRC/AAFCO
# Unidades: % tal como está (as-fed basis)
#
# Los datos se cargan dinámicamente desde comercial_diets_ecuador.csv.
# Si el archivo no está disponible se usa el diccionario de respaldo definido abajo.

import csv
import os

# Columnas numéricas requeridas en el CSV (formato original)
_REQUIRED_NUMERIC_COLUMNS = {"PB(%)", "EE(%)", "Ash(%)", "Humedad(%)", "FC(%)"}

# Columnas mínimas que deben estar presentes en el CSV (formato original)
_REQUIRED_COLUMNS = {"ID", "Nombre", "Descripcion", "Categoria", "Emoji"} | _REQUIRED_NUMERIC_COLUMNS

# ---------------------------------------------------------------------------
# Constantes para el nuevo CSV con 21 columnas precalculadas (v2)
# ---------------------------------------------------------------------------

# Columnas numéricas requeridas en el nuevo CSV v2
_REQUIRED_NUMERIC_COLUMNS_V2 = {
    "PB(%)", "EE(%)", "Ash(%)", "Humedad(%)", "FC(%)",
    "ENA(%)", "FC_MS(%)", "GE(kcal)", "DE(kcal)", "ME(kcal)", "Precio_USD_kg",
}

# Columnas de texto requeridas en el nuevo CSV v2
_REQUIRED_TEXT_COLUMNS_V2 = {"ID", "Nombre", "Marca", "Especie", "Etapa_de_Vida"}

# Todas las columnas requeridas en el nuevo CSV v2
_REQUIRED_COLUMNS_V2 = (
    _REQUIRED_TEXT_COLUMNS_V2
    | _REQUIRED_NUMERIC_COLUMNS_V2
    | {"Ingredientes", "Fuente_PB", "Fuente_EE", "Fuente_FC", "Otros"}
)

# Ruta por defecto del CSV (mismo directorio que este módulo)
_DEFAULT_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comercial_diets_ecuador.csv")

# Caché en memoria: se llena al importar el módulo
_foods_cache: dict = {}


def validate_csv(csv_path: str) -> list[str]:
    """
    Valida la estructura del archivo CSV de dietas comerciales.

    Parámetros:
        csv_path (str): Ruta al archivo CSV.

    Retorna:
        list[str]: Lista de mensajes de error. Vacía si el CSV es válido.
    """
    errors: list[str] = []

    if not os.path.isfile(csv_path):
        errors.append(f"Archivo no encontrado: {csv_path}")
        return errors

    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                errors.append("El archivo CSV está vacío o no tiene encabezados.")
                return errors

            headers = set(reader.fieldnames)
            missing = _REQUIRED_COLUMNS - headers
            if missing:
                errors.append(f"Columnas faltantes en el CSV: {', '.join(sorted(missing))}")
                return errors

            for row_num, row in enumerate(reader, start=2):
                nombre = row.get("Nombre", "").strip()
                if not nombre:
                    errors.append(f"Fila {row_num}: columna 'Nombre' vacía.")
                    continue
                for col in _REQUIRED_NUMERIC_COLUMNS:
                    val = row.get(col, "").strip()
                    if val == "":
                        errors.append(f"Fila {row_num} ({nombre}): columna '{col}' vacía.")
                        continue
                    try:
                        float(val)
                    except ValueError:
                        errors.append(f"Fila {row_num} ({nombre}): '{col}' = '{val}' no es numérico.")
    except Exception as exc:
        errors.append(f"Error al leer el CSV: {exc}")

    return errors


def load_diets_from_csv(csv_path: str) -> dict:
    """
    Carga las dietas comerciales desde un archivo CSV y devuelve un diccionario
    compatible con el formato interno de FOODS.

    Cada clave es el nombre comercial del alimento (columna 'Nombre') y su valor
    es un diccionario con las claves: PB, EE, Ash, Humidity, FC, description,
    category, emoji, y campos adicionales de mercado (brand, species, life_stage,
    price_usd_kg, distributor, presentations, availability, benefits, id).

    Si el CSV contiene valores precalculados de ENA, GE, DE y ME estos son
    ignorados; los valores se recalculan en tiempo de ejecución mediante
    calculate_ena() y calculate_energy() para garantizar consistencia.

    Parámetros:
        csv_path (str): Ruta al archivo CSV.

    Retorna:
        dict: Diccionario de alimentos en formato FOODS, o {} si hubo errores.
    """
    errors = validate_csv(csv_path)
    if errors:
        return {}

    foods: dict = {}
    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                nombre = row.get("Nombre", "").strip()
                if not nombre:
                    continue
                try:
                    entry: dict = {
                        "PB": float(row["PB(%)"]),
                        "EE": float(row["EE(%)"]),
                        "Ash": float(row["Ash(%)"]),
                        "Humidity": float(row["Humedad(%)"]),
                        "FC": float(row["FC(%)"]),
                        "description": row.get("Descripcion", "").strip(),
                        "category": row.get("Categoria", "").strip(),
                        "emoji": row.get("Emoji", "").strip(),
                        # Campos adicionales de mercado
                        "id": row.get("ID", "").strip(),
                        "brand": row.get("Marca", "").strip(),
                        "species": row.get("Especie", "").strip(),
                        "life_stage": row.get("Etapa_de_Vida", "").strip(),
                        "price_usd_kg": (lambda v: float(v) if v else None)(row.get("Precio_USD_kg", "").strip()),
                        "distributor": row.get("Distribuidor", "").strip(),
                        "presentations": row.get("Presentaciones", "").strip(),
                        "availability": row.get("Disponibilidad", "").strip(),
                        "benefits": row.get("Beneficios", "").strip(),
                        # Fuentes principales de nutrientes
                        "source_pb": row.get("Fuente_PB", "").strip(),
                        "source_ee": row.get("Fuente_EE", "").strip(),
                        "source_fc": row.get("Fuente_FC", "").strip(),
                    }
                    foods[nombre] = entry
                except (ValueError, KeyError):
                    continue
    except Exception:
        return {}

    return foods


def validate_csv_v2(csv_path: str) -> list[str]:
    """
    Valida la estructura del CSV con 21 columnas precalculadas (v2).

    Comprueba únicamente las columnas críticas (13 de las 21) para permitir
    carga parcial cuando alguna de las columnas opcionales esté ausente.

    Parámetros:
        csv_path (str): Ruta al archivo CSV.

    Retorna:
        list[str]: Lista de errores. Vacía si el CSV es válido.
    """
    errors: list[str] = []

    if not os.path.isfile(csv_path):
        errors.append(f"Archivo no encontrado: {csv_path}")
        return errors

    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                errors.append("El archivo CSV está vacío o no tiene encabezados.")
                return errors

            headers = set(reader.fieldnames)

            # Validar columnas críticas (subconjunto de las 21)
            columnas_criticas = {
                "ID", "Nombre", "Marca", "Especie", "Etapa_de_Vida",
                "PB(%)", "EE(%)", "Ash(%)", "Humedad(%)", "FC(%)",
                "GE(kcal)", "DE(kcal)", "ME(kcal)",
            }
            missing = columnas_criticas - headers
            if missing:
                errors.append(f"Columnas faltantes: {', '.join(sorted(missing))}")
                return errors

            # Validar datos en cada fila
            columnas_numeric_validar = {
                "PB(%)", "EE(%)", "Ash(%)", "Humedad(%)", "FC(%)",
                "GE(kcal)", "DE(kcal)", "ME(kcal)",
            }
            for row_num, row in enumerate(reader, start=2):
                nombre = row.get("Nombre", "").strip()
                if not nombre:
                    errors.append(f"Fila {row_num}: columna 'Nombre' vacía.")
                    continue
                for col in columnas_numeric_validar:
                    val = row.get(col, "").strip()
                    if val == "":
                        errors.append(f"Fila {row_num} ({nombre}): '{col}' vacío.")
                    else:
                        try:
                            float(val)
                        except ValueError:
                            errors.append(
                                f"Fila {row_num} ({nombre}): '{col}' = '{val}' no es numérico."
                            )

    except Exception as exc:
        errors.append(f"Error al leer CSV: {exc}")

    return errors


def load_diets_from_csv_v2(csv_path: str) -> dict:
    """
    Carga dietas desde CSV con 21 columnas precalculadas (v2).

    A diferencia de ``load_diets_from_csv()``, esta función usa directamente los
    valores de energía ya calculados en el CSV (ENA, FC_MS, GE, DE, ME) en lugar
    de recalcularlos. Las funciones ``calculate_ena()`` y ``calculate_energy()``
    siguen disponibles por compatibilidad pero **no se invocan** durante la carga.

    Estructura esperada del CSV:
    - Composición (% as-fed): PB, EE, Ash, Humedad, FC
    - Precalculados: ENA(%), FC_MS(%), GE(kcal), DE(kcal), ME(kcal)
    - Metadata: Marca, Especie, Etapa_de_Vida, Precio_USD_kg
    - Info detallada: Ingredientes, Fuente_PB, Fuente_EE, Fuente_FC, Otros

    Parámetros:
        csv_path (str): Ruta al archivo CSV.

    Retorna:
        dict: Diccionario de alimentos compatible con FOODS, o {} si no se pudo
        leer el archivo.
    """
    import logging

    errors = validate_csv_v2(csv_path)
    if errors:
        for err in errors[:5]:
            logging.warning("CSV v2 validation: %s", err)
        # No se interrumpe la carga; se intentan procesar las filas válidas.

    foods: dict = {}
    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row_num, row in enumerate(reader, start=2):
                nombre = row.get("Nombre", "").strip()
                if not nombre:
                    continue
                try:
                    # --- Composición (% as-fed) ---
                    pb = float(row.get("PB(%)", "0").strip() or "0")
                    ee = float(row.get("EE(%)", "0").strip() or "0")
                    ash = float(row.get("Ash(%)", "0").strip() or "0")
                    humidity = float(row.get("Humedad(%)", "0").strip() or "0")
                    fc = float(row.get("FC(%)", "0").strip() or "0")

                    # --- Valores precalculados (del CSV, NO recalcular) ---
                    ena = float(row.get("ENA(%)", "0").strip() or "0")
                    fc_ms = float(row.get("FC_MS(%)", "0").strip() or "0")
                    ge = float(row.get("GE(kcal)", "0").strip() or "0")
                    de = float(row.get("DE(kcal)", "0").strip() or "0")
                    me = float(row.get("ME(kcal)", "0").strip() or "0")

                    # --- Precio (opcional) ---
                    precio_str = row.get("Precio_USD_kg", "").strip()
                    precio = float(precio_str) if precio_str else None

                    # --- Metadata texto ---
                    id_alimento = row.get("ID", "").strip()
                    marca = row.get("Marca", "").strip()
                    especie = row.get("Especie", "").strip()
                    etapa = row.get("Etapa_de_Vida", "").strip()
                    ingredientes = row.get("Ingredientes", "").strip()
                    fuente_pb = row.get("Fuente_PB", "").strip()
                    fuente_ee = row.get("Fuente_EE", "").strip()
                    fuente_fc = row.get("Fuente_FC", "").strip()
                    otros = row.get("Otros", "").strip()

                    # --- Emoji según especie ---
                    especie_lower = especie.lower()
                    if "perro" in especie_lower:
                        emoji = "🐶"
                    elif "gato" in especie_lower:
                        emoji = "🐱"
                    else:
                        emoji = "🍖"

                    # --- Descripción y categoría ---
                    descripcion = f"{marca} - {etapa}"
                    if ingredientes:
                        descripcion += f" | Ingredientes: {ingredientes}"

                    # --- Valores derivados ---
                    de_pct = (de / ge * 100.0) if ge > 0 else 0.0
                    ms = max(0.0, 100.0 - humidity)

                    entry: dict = {
                        # Valores base (as-fed) — disponibles para recálculo si se requiere
                        "PB": round(pb, 2),
                        "EE": round(ee, 2),
                        "Ash": round(ash, 2),
                        "Humidity": round(humidity, 2),
                        "FC": round(fc, 2),
                        # Valores precalculados del CSV
                        "ENA": round(ena, 2),
                        "GE": round(ge, 2),
                        "DE": round(de, 2),
                        "ME": round(me, 2),
                        "FC_MS": round(fc_ms, 2),
                        "DE_pct": round(de_pct, 2),
                        "MS": round(ms, 2),
                        # Metadata comercial
                        "id": id_alimento,
                        "brand": marca,
                        "species": especie,
                        "life_stage": etapa,
                        "price_usd_kg": precio,
                        # Info nutricional detallada
                        "ingredients": ingredientes,
                        "source_pb": fuente_pb,
                        "source_ee": fuente_ee,
                        "source_fc": fuente_fc,
                        "other_info": otros,
                        # Campos de compatibilidad con el resto del app
                        "description": descripcion,
                        "category": etapa,
                        "emoji": emoji,
                    }
                    foods[nombre] = entry

                except (ValueError, KeyError) as exc:
                    logging.warning("CSV v2 row %d (%s): error de parseo — %s", row_num, nombre, exc)
                    continue

    except Exception as exc:
        logging.error("Error al cargar CSV v2: %s", exc)
        return {}

    return foods


def food_data_is_precalculated(food_data: dict) -> bool:
    """
    Verifica si los datos de energía de un alimento provienen del CSV v2
    (precalculados) o si fueron calculados en tiempo de ejecución.

    Se considera precalculado cuando el diccionario incluye la clave ``DE_pct``
    con un valor no nulo, característica exclusiva de las entradas cargadas por
    ``load_diets_from_csv_v2()``.

    Parámetros:
        food_data (dict): Datos de composición de un alimento.

    Retorna:
        bool: ``True`` si los valores energéticos son precalculados.
    """
    return "DE_pct" in food_data and food_data.get("DE_pct") is not None


# ---------------------------------------------------------------------------
# Datos de respaldo (hardcoded) — usados cuando el CSV no está disponible
# ---------------------------------------------------------------------------
_FOODS_FALLBACK = {
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

# ---------------------------------------------------------------------------
# Inicialización: intentar cargar desde CSV v2 (21 columnas); si falla intentar
# CSV v1 (10 columnas) y, en último recurso, usar el diccionario de respaldo.
# ---------------------------------------------------------------------------
_foods_cache = load_diets_from_csv_v2(_DEFAULT_CSV_PATH)
if not _foods_cache:
    _foods_cache = load_diets_from_csv(_DEFAULT_CSV_PATH)
FOODS: dict = _foods_cache if _foods_cache else _FOODS_FALLBACK


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


def calculate_energy_breakdown(food_data):
    """
    Calcula el aporte energético de cada macronutriente según la fórmula NRC.

    Desglose basado en GE = (5.7 × PB) + (9.4 × EE) + [4.1 × (ENA + FC)]:
        - kcal_pb  : energía aportada por la Proteína Bruta
        - kcal_ee  : energía aportada por la Grasa (EE)
        - kcal_cho : energía aportada por Carbohidratos + Fibra (ENA + FC)

    Los porcentajes se calculan respecto a la GE total.
    Los valores de ME proporcionales escalan los % al valor real de ME.

    Parámetros:
        food_data (dict): Diccionario con las claves PB, EE, Ash, Humidity y FC
            (valores porcentuales en base tal como está / as-fed).

    Retorna:
        dict con kcal y porcentajes por nutriente, más GE, DE y ME totales.
    """
    PB = food_data["PB"]
    EE = food_data["EE"]
    FC = food_data["FC"]
    ENA = calculate_ena(food_data)

    kcal_pb = 5.7 * PB
    kcal_ee = 9.4 * EE
    kcal_cho = 4.1 * (ENA + FC)
    GE = kcal_pb + kcal_ee + kcal_cho

    if GE > 0:
        pct_pb = (kcal_pb / GE) * 100.0
        pct_ee = (kcal_ee / GE) * 100.0
        pct_cho = (kcal_cho / GE) * 100.0
    else:
        pct_pb = pct_ee = pct_cho = 0.0

    energy = calculate_energy(food_data)
    ME = energy["ME"]

    return {
        "kcal_pb": round(kcal_pb, 2),
        "kcal_ee": round(kcal_ee, 2),
        "kcal_cho": round(kcal_cho, 2),
        "pct_pb": round(pct_pb, 1),
        "pct_ee": round(pct_ee, 1),
        "pct_cho": round(pct_cho, 1),
        "me_pb": round(ME * pct_pb / 100.0, 2),
        "me_ee": round(ME * pct_ee / 100.0, 2),
        "me_cho": round(ME * pct_cho / 100.0, 2),
        "GE": energy["GE"],
        "DE": energy["DE"],
        "ME": ME,
    }


def get_food_names():
    """Devuelve la lista de nombres de alimentos disponibles."""
    return list(FOODS.keys())


def get_food_data(food_name):
    """Devuelve los datos de composición de un alimento por nombre."""
    return FOODS.get(food_name, None)
