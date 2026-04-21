# Referencias de nutrientes para perros y gatos expresadas a 4000 kcal/kg MS
# Macronutrientes y macrominerales en %MS; vitaminas y microminerales en mg/kg, UI/kg o µg/kg
NUTRIENTES_REFERENCIA = {
    "perro": {
        "cachorro": {
            # =========================
            # 1) MACRONUTRIENTES (%MS a 4000 kcal/kg MS)
            # =========================
            "Proteína": {"min": 25.0, "max": None, "unit": "%"},
            "Grasa": {"min": 8.5, "max": None, "unit": "%"},

            # (Ácidos grasos esenciales / lípidos)
            "Ácido linoleico (ω-6)": {"min": 1.3, "max": None, "unit": "%"},
            "Ácido araquidónico (ω-6)": {"min": 300.0, "max": None, "unit": "mg/kg"},
            "Ácido alfa-linolénico (ω-3)": {"min": 0.08, "max": None, "unit": "%"},
            "EPA + DHA (ω-3)": {"min": 0.05, "max": None, "unit": "%"},

            # =========================
            # 2) AMINOÁCIDOS (%MS a 4000 kcal/kg MS)
            # =========================
            "Arginina": {"min": 0.82, "max": None, "unit": "%"},
            "Histidina": {"min": 0.39, "max": None, "unit": "%"},
            "Isoleucina": {"min": 0.65, "max": None, "unit": "%"},
            "Leucina": {"min": 1.29, "max": None, "unit": "%"},
            "Lisina": {"min": 0.88, "max": None, "unit": "%"},
            "Metionina": {"min": 0.35, "max": None, "unit": "%"},
            "Metionina + Cistina": {"min": 0.70, "max": None, "unit": "%"},
            "Fenilalanina": {"min": 0.65, "max": None, "unit": "%"},
            "Fenilalanina + Tirosina": {"min": 1.30, "max": None, "unit": "%"},
            "Treonina": {"min": 0.81, "max": None, "unit": "%"},
            "Triptófano": {"min": 0.23, "max": None, "unit": "%"},
            "Valina": {"min": 0.68, "max": None, "unit": "%"},

            # =========================
            # 3) MACROMINERALES (%MS a 4000 kcal/kg MS)
            # =========================
            "Calcio (Ca)": {"min": 1.0, "max": 1.0, "unit": "%"},
            "Fósforo (P)": {"min": 0.9, "max": None, "unit": "%"},
            "Relación Ca:P": {"min": 1.0, "max": 1.5, "unit": None},
            "Potasio (K)": {"min": 0.44, "max": None, "unit": "%"},
            "Sodio (Na)": {"min": 0.22, "max": None, "unit": "%"},
            "Cloruro (Cl)": {"min": 0.33, "max": None, "unit": "%"},
            "Magnesio (Mg)": {"min": 0.04, "max": None, "unit": "%"},

            # =========================
            # 4) VITAMINAS (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Vitamina A": {"min": 5000.0, "max": None, "unit": "UI/kg"},
            "Vitamina D": {"min": 552.0, "max": None, "unit": "IU/kg"},
            "Vitamina E": {"min": 50.0, "max": None, "unit": "IU/kg"},
            "Vitamina B1 (Tiamina)": {"min": 1.8, "max": None, "unit": "mg/kg"},
            "Vitamina B2 (Riboflavina)": {"min": 4.2, "max": None, "unit": "mg/kg"},
            "Vitamina B3 (Niacina)": {"min": 13.6, "max": None, "unit": "mg/kg"},
            "Vitamina B5 (Ácido pantoténico)": {"min": 12.0, "max": None, "unit": "mg/kg"},
            "Vitamina B6 (Piridoxina)": {"min": 1.2, "max": None, "unit": "mg/kg"},
            "Vitamina B9 (Ácido fólico)": {"min": 216.0, "max": None, "unit": "µg/kg"},
            "Vitamina B12 (Cobalamina)": {"min": 28.0, "max": None, "unit": "µg/kg"},
            "Colina": {"min": 1700.0, "max": None, "unit": "mg/kg"},

            # =========================
            # 5) MICROMINERALES (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Hierro (Fe)": {"min": 88.0, "max": None, "unit": "mg/kg"},
            "Cobre (Cu)": {"min": 11.0, "max": None, "unit": "mg/kg"},
            "Yodo (I)": {"min": 1.52, "max": None, "unit": "mg/kg"},
            "Manganeso (Mn)": {"min": 5.6, "max": None, "unit": "mg/kg"},
            "Zinc (Zn)": {"min": 100.0, "max": None, "unit": "mg/kg"},
            "Selenio (Se)": {"min": 400.0, "max": None, "unit": "µg/kg"},
        },

        "adulto": {
            # =========================
            # 1) MACRONUTRIENTES (%MS a 4000 kcal/kg MS)
            # =========================
            "Proteína": {"min": 20.0, "max": None, "unit": "%"},
            "Grasa": {"min": 8.5, "max": None, "unit": "%"},

            # (Ácidos grasos esenciales / lípidos)
            "Ácido linoleico (ω-6)": {"min": 1.3, "max": None, "unit": "%"},
            "Ácido araquidónico (ω-6)": {"min": 300.0, "max": None, "unit": "mg/kg"},
            "Ácido alfa-linolénico (ω-3)": {"min": 0.08, "max": None, "unit": "%"},
            "EPA + DHA (ω-3)": {"min": 0.05, "max": None, "unit": "%"},

            # =========================
            # 2) AMINOÁCIDOS (%MS a 4000 kcal/kg MS)
            # =========================
            "Arginina": {"min": 0.74, "max": None, "unit": "%"},
            "Histidina": {"min": 0.25, "max": None, "unit": "%"},
            "Isoleucina": {"min": 0.50, "max": None, "unit": "%"},
            "Leucina": {"min": 0.80, "max": None, "unit": "%"},
            "Lisina": {"min": 0.70, "max": None, "unit": "%"},
            "Metionina": {"min": 0.26, "max": None, "unit": "%"},
            "Metionina + Cistina": {"min": 0.53, "max": None, "unit": "%"},
            "Fenilalanina": {"min": 0.50, "max": None, "unit": "%"},
            "Fenilalanina + Tirosina": {"min": 1.00, "max": None, "unit": "%"},
            "Treonina": {"min": 0.64, "max": None, "unit": "%"},
            "Triptófano": {"min": 0.21, "max": None, "unit": "%"},
            "Valina": {"min": 0.56, "max": None, "unit": "%"},

            # =========================
            # 3) MACROMINERALES (%MS a 4000 kcal/kg MS)
            # =========================
            "Calcio (Ca)": {"min": 0.8, "max": 1.0, "unit": "%"},
            "Fósforo (P)": {"min": 0.70, "max": None, "unit": "%"},
            "Relación Ca:P": {"min": 1.0, "max": 1.5, "unit": None},
            "Potasio (K)": {"min": 0.44, "max": None, "unit": "%"},
            "Sodio (Na)": {"min": 0.22, "max": None, "unit": "%"},
            "Cloruro (Cl)": {"min": 0.33, "max": None, "unit": "%"},
            "Magnesio (Mg)": {"min": 0.04, "max": None, "unit": "%"},

            # =========================
            # 4) VITAMINAS (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Vitamina A": {"min": 5000.0, "max": None, "unit": "UI/kg"},
            "Vitamina D": {"min": 552.0, "max": None, "unit": "IU/kg"},
            "Vitamina E": {"min": 50.0, "max": None, "unit": "IU/kg"},
            "Vitamina B1 (Tiamina)": {"min": 1.8, "max": None, "unit": "mg/kg"},
            "Vitamina B2 (Riboflavina)": {"min": 4.2, "max": None, "unit": "mg/kg"},
            "Vitamina B3 (Niacina)": {"min": 13.6, "max": None, "unit": "mg/kg"},
            "Vitamina B5 (Ácido pantoténico)": {"min": 12.0, "max": None, "unit": "mg/kg"},
            "Vitamina B6 (Piridoxina)": {"min": 1.2, "max": None, "unit": "mg/kg"},
            "Vitamina B9 (Ácido fólico)": {"min": 216.0, "max": None, "unit": "µg/kg"},
            "Vitamina B12 (Cobalamina)": {"min": 28.0, "max": None, "unit": "µg/kg"},
            "Colina": {"min": 1700.0, "max": None, "unit": "mg/kg"},

            # =========================
            # 5) MICROMINERALES (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Hierro (Fe)": {"min": 88.0, "max": None, "unit": "mg/kg"},
            "Cobre (Cu)": {"min": 11.0, "max": None, "unit": "mg/kg"},
            "Yodo (I)": {"min": 1.52, "max": None, "unit": "mg/kg"},
            "Manganeso (Mn)": {"min": 5.6, "max": None, "unit": "mg/kg"},
            "Zinc (Zn)": {"min": 100.0, "max": None, "unit": "mg/kg"},
            "Selenio (Se)": {"min": 400.0, "max": None, "unit": "µg/kg"},
        },
    },

    "gato": {
        "cachorro": {
            # =========================
            # 1) MACRONUTRIENTES (%MS a 4000 kcal/kg MS)
            # =========================
            "Proteína": {"min": 28.0, "max": None, "unit": "%"},
            "Grasa": {"min": 9.0, "max": None, "unit": "%"},

            # (Ácidos grasos esenciales / lípidos)
            "Ácido linoleico (ω-6)": {"min": 0.55, "max": None, "unit": "%"},
            "Ácido araquidónico (ω-6)": {"min": 200.0, "max": None, "unit": "mg/kg"},
            "Ácido alfa-linolénico (ω-3)": {"min": 0.02, "max": None, "unit": "%"},
            "EPA + DHA (ω-3)": {"min": 0.01, "max": None, "unit": "%"},

            # =========================
            # 2) AMINOÁCIDOS (%MS a 4000 kcal/kg MS)
            # =========================
            "Taurina (húmedo)": {"min": 0.20, "max": None, "unit": "%"},
            
            # =========================
            # 3) MACROMINERALES (%MS a 4000 kcal/kg MS)
            # =========================
            "Calcio (Ca)": {"min": 1.0, "max": None, "unit": "%"},
            "Fósforo (P)": {"min": 0.84, "max": None, "unit": "%"},
            "Relación Ca:P": {"min": 1.0, "max": 1.5, "unit": None},
            "Potasio (K)": {"min": 0.60, "max": None, "unit": "%"},
            "Sodio (Na)": {"min": 0.16, "max": None, "unit": "%"},
            "Cloruro (Cl)": {"min": 0.24, "max": None, "unit": "%"},
            "Magnesio (Mg)": {"min": 0.05, "max": None, "unit": "%"},

            # =========================
            # 4) VITAMINAS (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Vitamina A": {"min": 3600.0, "max": None, "unit": "UI/kg"},
            "Vitamina D": {"min": 280.0, "max": None, "unit": "IU/kg"},
            "Vitamina E": {"min": 15.2, "max": None, "unit": "IU/kg"},
            "Vitamina B1 (Tiamina)": {"min": 5.6, "max": None, "unit": "mg/kg"},
            "Vitamina B2 (Riboflavina)": {"min": 3.2, "max": None, "unit": "mg/kg"},
            "Vitamina B3 (Niacina)": {"min": 32.0, "max": None, "unit": "mg/kg"},
            "Vitamina B5 (Ácido pantoténico)": {"min": 5.72, "max": None, "unit": "mg/kg"},
            "Vitamina B6 (Piridoxina)": {"min": 2.52, "max": None, "unit": "mg/kg"},
            "Vitamina B7 (Biotina)": {"min": 70.0, "max": None, "unit": "µg/kg"},
            "Vitamina B9 (Ácido fólico)": {"min": 752.0, "max": None, "unit": "µg/kg"},
            "Vitamina B12 (Cobalamina)": {"min": 18.0, "max": None, "unit": "µg/kg"},
            "Colina": {"min": 2400.0, "max": None, "unit": "mg/kg"},

            # =========================
            # 5) MICROMINERALES (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Hierro (Fe)": {"min": 80.0, "max": None, "unit": "mg/kg"},
            "Cobre (Cu)": {"min": 10.0, "max": None, "unit": "mg/kg"},
            "Yodo (I)": {"min": 1.8, "max": None, "unit": "mg/kg"},
            "Manganeso (Mn)": {"min": 10.0, "max": None, "unit": "mg/kg"},
            "Zinc (Zn)": {"min": 75.2, "max": None, "unit": "mg/kg"},
            "Selenio (Se)": {"min": 300.0, "max": None, "unit": "µg/kg"},
        },

        "adulto": {
            # =========================
            # 1) MACRONUTRIENTES (%MS a 4000 kcal/kg MS)
            # =========================
            "Proteína": {"min": 25.0, "max": None, "unit": "%"},
            "Grasa": {"min": 9.0, "max": None, "unit": "%"},

            # (Ácidos grasos esenciales / lípidos)
            "Ácido linoleico (ω-6)": {"min": 0.50, "max": None, "unit": "%"},
            "Ácido araquidónico (ω-6)": {"min": 60.0, "max": None, "unit": "mg/kg"},

            # =========================
            # 2) AMINOÁCIDOS (%MS a 4000 kcal/kg MS)
            # =========================
            "Arginina": {"min": 1.00, "max": None, "unit": "%"},
            "Histidina": {"min": 0.26, "max": None, "unit": "%"},
            "Isoleucina": {"min": 0.43, "max": None, "unit": "%"},
            "Leucina": {"min": 1.02, "max": None, "unit": "%"},
            "Lisina": {"min": 0.34, "max": None, "unit": "%"},
            "Metionina": {"min": 0.17, "max": None, "unit": "%"},
            "Metionina + Cistina": {"min": 0.34, "max": None, "unit": "%"},
            "Fenilalanina": {"min": 0.40, "max": None, "unit": "%"},
            "Fenilalanina + Tirosina": {"min": 1.53, "max": None, "unit": "%"},
            "Treonina": {"min": 0.52, "max": None, "unit": "%"},
            "Triptófano": {"min": 0.13, "max": None, "unit": "%"},
            "Valina": {"min": 0.51, "max": None, "unit": "%"},
            "Taurina (húmedo)": {"min": 0.20, "max": None, "unit": "%"},
            
            # =========================
            # 3) MACROMINERALES (%MS a 4000 kcal/kg MS)
            # =========================
            "Calcio (Ca)": {"min": 0.40, "max": None, "unit": "%"},
            "Fósforo (P)": {"min": 0.26, "max": None, "unit": "%"},
            "Relación Ca:P": {"min": 1.0, "max": 1.5, "unit": None},
            "Potasio (K)": {"min": 0.60, "max": None, "unit": "%"},
            "Sodio (Na)": {"min": 0.08, "max": None, "unit": "%"},
            "Cloruro (Cl)": {"min": 0.12, "max": None, "unit": "%"},
            "Magnesio (Mg)": {"min": 0.04, "max": None, "unit": "%"},

            # =========================
            # 4) VITAMINAS (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Vitamina A": {"min": 1332.0, "max": None, "unit": "UI/kg"},
            "Vitamina D": {"min": 250.0, "max": None, "unit": "IU/kg"},
            "Vitamina E": {"min": 15.2, "max": None, "unit": "IU/kg"},
            "Vitamina B1 (Tiamina)": {"min": 4.4, "max": None, "unit": "mg/kg"},
            "Vitamina B2 (Riboflavina)": {"min": 3.2, "max": None, "unit": "mg/kg"},
            "Vitamina B3 (Niacina)": {"min": 32.0, "max": None, "unit": "mg/kg"},
            "Vitamina B5 (Ácido pantoténico)": {"min": 5.76, "max": None, "unit": "mg/kg"},
            "Vitamina B6 (Piridoxina)": {"min": 2.52, "max": None, "unit": "mg/kg"},
            "Vitamina B7 (Biotina)": {"min": 60.0, "max": None, "unit": "µg/kg"},
            "Vitamina B9 (Ácido fólico)": {"min": 752.0, "max": None, "unit": "µg/kg"},
            "Vitamina B12 (Cobalamina)": {"min": 17.6, "max": None, "unit": "µg/kg"},
            "Colina": {"min": 2400.0, "max": None, "unit": "mg/kg"},

            # =========================
            # 5) MICROMINERALES (por kg MS a 4000 kcal/kg MS)
            # =========================
            "Hierro (Fe)": {"min": 80.0, "max": None, "unit": "mg/kg"},
            "Cobre (Cu)": {"min": 5.0, "max": None, "unit": "mg/kg"},
            "Yodo (I)": {"min": 1.32, "max": None, "unit": "mg/kg"},
            "Manganeso (Mn)": {"min": 5.0, "max": None, "unit": "mg/kg"},
            "Zinc (Zn)": {"min": 75.2, "max": None, "unit": "mg/kg"},
            "Selenio (Se)": {"min": 260.0, "max": None, "unit": "µg/kg"},
        },
    },
}

# Variables específicas para facilitar su uso
NUTRIENTES_REFERENCIA_PERRO = NUTRIENTES_REFERENCIA["perro"]
NUTRIENTES_REFERENCIA_GATO = NUTRIENTES_REFERENCIA["gato"]
