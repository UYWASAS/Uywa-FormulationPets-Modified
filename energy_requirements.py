import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)

def descripcion_condiciones(especie):
    """
    Devuelve las descripciones seleccionables en la interfaz según la especie.
    """
    if especie == "perro":
        return {
            "Castrado (Adulto)": "adulto_castrado",
            "Entero (Adulto)": "adulto_entero",
            "Cachorro (<4 meses)": "cachorro_menor4m",
            "Cachorro (5 meses - Adulto)": "cachorro_5m_adulto",
            "Gestación (Primera mitad)": "gestacion_primera_mitad",
            "Gestación (Segunda mitad)": "gestacion_segunda_mitad",
            "Lactancia": "lactancia",
        }
    elif especie == "gato":
        return {
            "Castrado (Adulto)": "adulto_castrado",
            "Entero (Adulto)": "adulto_entero",
            "Gatito (<4 meses)": "cachorro_menor4m",
            "Gatito (5 meses - Adulto)": "cachorro_5m_adulto",
            "Gestación (Inicio)": "gestacion_inicio",
            "Gestación (Final)": "gestacion_final",
            "Lactancia": "lactancia",
        }
    else:
        logging.error(f"[CONDICIONES] Especie desconocida: {especie}")
        return {}

def calcular_rer(peso):
    """
    Calcula el Requerimiento Energético en Reposo (RER) de un animal.

    Fórmula: RER = 70 * peso^0.75

    Args:
        peso (float): Peso del animal en kilogramos.

    Returns:
        float: Requerimiento Energético en Reposo en kcal/día.
    """
    try:
        rer = 70 * (peso ** 0.75)
        logging.info(f"[RER] Calculado: {rer:.2f} kcal para peso: {peso:.2f} kg")
        return rer
    except Exception as e:
        logging.error(f"[RER] Error al calcular el RER: {e}")
        return None

def calcular_mer(especie, condicion, peso, bcs=None):
    """
    Calcula el Requerimiento Energético Diario de Mantenimiento (MER), ajustado por BCS si corresponde.

    Fórmula: MER = Factor específico * RER con peso ajustado (si aplica BCS)

    Args:
        especie (str): Especie del animal (e.g., "perro", "gato").
        condicion (str): Condición específica del animal.
        peso (float): Peso del animal en kilogramos.
        bcs (int, optional): Condición Corporal (BCS) en escala 1/9.

    Returns:
        dict: Diccionario con valores de MER, RER, y peso ajustado (si aplica).
    """
    # Factores metabólicos predefinidos
    factores_perro = {
        "adulto_castrado": 1.6,
        "adulto_entero": 1.8,
        "cachorro_menor4m": 3.0,
        "cachorro_5m_adulto": 2.0,
        "gestacion_primera_mitad": 1.2,
        "gestacion_segunda_mitad": 1.6,
        "lactancia": 4.0,
    }

    factores_gato = {
        "adulto_castrado": 1.2,
        "adulto_entero": 1.4,
        "cachorro_menor4m": 2.5,
        "cachorro_5m_adulto": 2.0,
        "gestacion_inicio": 1.6,
        "gestacion_final": 2.0,
        "lactancia": 2.5,
    }

    # Factores BCS para peso ajustado
    factores_bcs = {6: 0.9, 7: 0.8, 8: 0.7, 9: 0.6, 4: 1.1, 3: 1.2, 2: 1.3, 1: 1.4}

    # Seleccionar factores por especie
    factores_especie = {"perro": factores_perro, "gato": factores_gato}

    if especie not in factores_especie:
        logging.error(f"[MER] Especie desconocida: {especie}")
        return None
    
    if condicion not in factores_especie[especie]:
        logging.error(f"[MER] Condición desconocida: {condicion} para especie: {especie}")
        return None

    try:
        # Calcular el RER con peso actual
        rer_actual = calcular_rer(peso)
        factor_fisiologico = factores_especie[especie][condicion]
        mer_actual = rer_actual * factor_fisiologico

        resultado = {
            "RER_actual": rer_actual,
            "MER_actual": mer_actual,
            "Peso_objetivo": None,
            "RER_objetivo": None,
            "MER_final": mer_actual,  # Por defecto, igual a MER_actual
        }
        
        # Ajustar cálculos si el BCS no es ideal
        if bcs and bcs != 5:
            factor_bcs = factores_bcs.get(bcs, 1.0)
            peso_objetivo = peso * factor_bcs
            rer_objetivo = calcular_rer(peso_objetivo)
            mer_final = rer_objetivo * factor_fisiologico

            resultado.update({
                "Peso_objetivo": peso_objetivo,
                "RER_objetivo": rer_objetivo,
                "MER_final": mer_final
            })
        
        logging.info(f"[MER] Resultado: {resultado}")
        return resultado
    except Exception as e:
        logging.error(f"[MER] Error al calcular el MER: {e}")
        return None

if __name__ == "__main__":
    # Pruebas rápidas
    print(descripcion_condiciones("perro"))
    print(calcular_rer(20))  # Ejemplo para 20 kg
    print(calcular_mer("perro", "adulto_castrado", 20))  # Adulto castrado de 20 kg
    print(calcular_mer("perro", "adulto_castrado", 20, bcs=4))  # Adulto castrado con BCS bajo (4/9)
    print(calcular_mer("gato", "lactancia", 5))  # Gato en lactancia con peso de 5 kg
    print(calcular_mer("gato", "adulto_castrado", 5, bcs=8))  # Gato castrado con sobrepeso (8/9)
