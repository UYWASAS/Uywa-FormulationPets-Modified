"""
Pet Profile Tools - Funciones consolidadas para gestión de perfiles de mascotas
Reúne funcionalidad de cálculo de MER, requerimientos de nutrientes, y generación de perfiles.
"""

import pandas as pd
from datetime import datetime


def calcular_mer(peso_kg, edad_anos, factor_actividad=1.0, factor_reproductivo=1.0, especie="perro"):
    """
    Calcula el Metabolizable Energy Requirement (MER) basado en:
    - Peso corporal
    - Edad
    - Factor de actividad
    - Factor reproductivo
    - Especie
    
    Usa la ecuación: MER = 70 * (peso_kg)^0.75 * factor_actividad * factor_reproductivo
    """
    try:
        # Ecuación base para MER (kcal/día)
        base_energy = 70 * (peso_kg ** 0.75)
        
        # Ajustes según edad
        if edad_anos < 1:
            base_energy *= 2.0  # Cachorro: 2x energía
        elif edad_anos > 7:
            base_energy *= 0.95  # Adulto mayor: reducción 5%
        
        # Aplicar factores
        mer = base_energy * factor_actividad * factor_reproductivo
        
        return round(mer, 0)
    except Exception as e:
        print(f"Error calculando MER: {str(e)}")
        return None


def calcular_requerimientos_nutrientes(especie="perro", peso_kg=15.0, edad_anos=3.0, actividad="Moderado"):
    """
    Calcula requerimientos de macro y micronutrientes basado en:
    - Especie (perro/gato)
    - Peso
    - Edad
    - Nivel de actividad
    
    Retorna un diccionario con requerimientos en g/día
    """
    try:
        # Calcular MER primero
        activity_map = {
            "Sedentario": 1.2,
            "Moderado": 1.5,
            "Activo": 1.8,
            "Muy activo": 2.0
        }
        
        factor_actividad = activity_map.get(actividad, 1.5)
        mer = calcular_mer(peso_kg, edad_anos, factor_actividad)
        
        if mer is None:
            return {}
        
        # Requerimientos según especie
        if especie.lower() == "perro":
            # Proteína: 12-18% de kcal = 4.8 kcal/g
            pb_g = (mer * 0.15) / 4.8
            
            # Grasa: 12-15% de kcal = 8.8 kcal/g
            ee_g = (mer * 0.125) / 8.8
            
            # Carbohidratos: calculados
            cho_g = (mer * 0.40) / 3.5
            
            # Micronutrientes (valores típicos)
            calcio_mg = peso_kg * 100
            fosforo_mg = peso_kg * 70
            
        elif especie.lower() == "gato":
            # Gatos requieren más proteína
            pb_g = (mer * 0.25) / 4.8  # 25% de kcal
            ee_g = (mer * 0.15) / 8.8  # 15% de kcal
            cho_g = (mer * 0.30) / 3.5  # 30% de kcal (gatos son carnívoros)
            
            calcio_mg = peso_kg * 80
            fosforo_mg = peso_kg * 60
        else:
            # Default a perro
            pb_g = (mer * 0.15) / 4.8
            ee_g = (mer * 0.125) / 8.8
            cho_g = (mer * 0.40) / 3.5
            calcio_mg = peso_kg * 100
            fosforo_mg = peso_kg * 70
        
        return {
            "mer_kcal": round(mer, 0),
            "pb_g": round(pb_g, 1),
            "ee_g": round(ee_g, 1),
            "cho_g": round(cho_g, 1),
            "calcio_mg": round(calcio_mg, 0),
            "fosforo_mg": round(fosforo_mg, 0),
            "especie": especie,
            "edad_anos": edad_anos,
            "peso_kg": peso_kg,
        }
    except Exception as e:
        print(f"Error calculando requerimientos: {str(e)}")
        return {}


def generar_perfil_mascota(nombre, especie, edad, peso, actividad, estado_reproductivo, mer, requerimientos):
    """
    Genera un perfil consolidado de la mascota con toda la información relevante.
    
    Retorna un diccionario con:
    - Datos básicos: nombre, especie, edad, peso, actividad, estado reproductivo
    - Requerimientos nutricionales calculados
    - Metadata: fecha de creación
    """
    try:
        perfil = {
            "nombre": nombre,
            "especie": especie,
            "edad_anos": edad,
            "peso_kg": peso,
            "actividad": actividad,
            "estado_reproductivo": estado_reproductivo,
            "mer_kcal": mer,
            "requerimientos": requerimientos,
            "fecha_creacion": datetime.now().isoformat(),
            "version": "1.0"
        }
        return perfil
    except Exception as e:
        print(f"Error generando perfil: {str(e)}")
        return None


def validar_datos_basicos(nombre, especie, edad, peso):
    """
    Valida que los datos básicos sean correctos antes de procesarlos.
    
    Retorna (es_válido: bool, mensaje: str)
    """
    errores = []
    
    if not nombre or nombre.strip() == "":
        errores.append("El nombre de la mascota es requerido")
    
    if especie.lower() not in ["perro", "gato"]:
        errores.append("La especie debe ser 'perro' o 'gato'")
    
    try:
        edad_float = float(edad)
        if edad_float <= 0 or edad_float > 30:
            errores.append("La edad debe estar entre 0.1 y 30 años")
    except:
        errores.append("La edad debe ser un número válido")
    
    try:
        peso_float = float(peso)
        if peso_float <= 0.5 or peso_float > 100:
            errores.append("El peso debe estar entre 0.5 y 100 kg")
    except:
        errores.append("El peso debe ser un número válido")
    
    if errores:
        return False, " | ".join(errores)
    else:
        return True, "Datos válidos"
