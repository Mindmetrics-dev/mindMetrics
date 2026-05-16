'''
variables.py
============
Definición de las 19 variables del sistema experto de Riesgo Psicosocial.

Estructura de cada variable:
    code    : código del Excel (ej: "1A")
    name    : nombre legible
    layer   : capa (1=Vulnerabilidad Basal, 2=Estado Funcional,
                     3=Escalada Clínica, 4=Factores Protectores)
    weight  : peso clínico según Tabla de Ponderación
    db_field: nombre exacto del campo en evaluacion_inicial

Valores posibles después del mapeo: 0.2 (Bajo) | 0.6 (Medio) | 1.0 (Alto)

Nota sobre Capa 4 (4E - Apoyo Social):
    En esta capa el valor ALTO (1.0) significa PEOR apoyo (más riesgo).
    El valor BAJO (0.2) actúa como protector y reduce el score final.
    Esto se maneja en protectors.py, no aquí.
'''

VARIABLES = {
    # =========================================================
    # CAPA 1 — Vulnerabilidad Basal
    # =========================================================
    "1A": {
        "name": "Edad",
        "layer": 1,
        "weight": 0.8,
        "db_field": "edad",
    },
    "1B": {
        "name": "Género",
        "layer": 1,
        "weight": 0.8,
        "db_field": "genero",
    },
    "1C": {
        "name": "Estado Relacional",
        "layer": 1,
        "weight": 1.0,
        "db_field": "estado_relacion",
    },
    "3F": {
        "name": "Historial Familiar",
        "layer": 1,
        "weight": 1.5,
        "db_field": "historial_familiar",
    },
    "4B": {
        "name": "Diagnóstico Previo",
        "layer": 1,
        "weight": 2.5,
        "db_field": "diagnostico_previo",
    },

    # =========================================================
    # CAPA 2 — Estado Funcional
    # =========================================================
    "2A": {
        "name": "Situación Laboral",
        "layer": 2,
        "weight": 1.5,
        "db_field": "situacion_trabajo",
    },
    "3A": {
        "name": "Horas de Sueño",
        "layer": 2,
        "weight": 2.0,
        "db_field": "hr_sueno",
    },
    "2B": {
        "name": "Horas de Trabajo",
        "layer": 2,
        "weight": 1.5,
        "db_field": "hr_trabajo",
    },
    "2C": {
        "name": "Horas de Pantalla",
        "layer": 2,
        "weight": 1.0,
        "db_field": "hr_pantalla",
    },
    "2D": {
        "name": "Actividad Física",
        "layer": 2,
        "weight": 1.5,
        "db_field": "hr_act_fis",
    },
    "2E": {
        "name": "Dificultad de Concentración",
        "layer": 2,
        "weight": 1.5,
        "db_field": "dificultad_concentra",
    },
    "3D": {
        "name": "Satisfacción Laboral",
        "layer": 2,
        "weight": 2.0,
        "db_field": "satisfaccion_laboral",
    },
    "3E": {
        "name": "Cambio Emocional",
        "layer": 2,
        "weight": 2.5,
        "db_field": "cambio_emocional",
    },

    # =========================================================
    # CAPA 3 — Escalada Clínica
    # =========================================================
    "3B": {
        "name": "Estrés Laboral",
        "layer": 3,
        "weight": 2.0,
        "db_field": "estres_laboral",
    },
    "3C": {
        "name": "Estrés Académico",
        "layer": 3,
        "weight": 1.5,
        "db_field": "estres_academico",
    },
    "4A": {
        "name": "Uso de Sustancias",
        "layer": 3,
        "weight": 3.0,   # ⚠ escalador crítico — peso más alto del sistema
        "db_field": "uso_sustancias",
    },
    "4C": {
        "name": "Historial de Pánico",
        "layer": 3,
        "weight": 2.0,
        "db_field": "historial_panico",
    },
    "4D": {
        "name": "Tratamiento Previo",
        "layer": 3,
        "weight": 2.5,
        "db_field": "tratamiento_previo",
    },

    # =========================================================
    # CAPA 4 — Factores Protectores
    # =========================================================
    "4E": {
        "name": "Apoyo Social Percibido",
        "layer": 4,
        "weight": 2.0,
        # INVERTIDO: Alto (1.0) = poco apoyo = más riesgo
        #            Bajo (0.2) = mucho apoyo = factor protector
        "db_field": "apoyo_percibido",
    },
}

# Máximo teórico por capa si todas las variables de esa capa = 1.0
# Fórmula: sum(weight) para cada variable de la capa
# Estos valores vienen del Excel — usarlos para normalizar
MAX_TEORICO_CAPA = {
    1: 6.6,   # (0.8+0.8+1.0+1.5+2.5) × 1.0
    2: 13.5,  # (1.5+2.0+1.5+1.0+1.5+1.5+2.0+2.5) × 1.0
    3: 11.0,  # (2.0+1.5+3.0+2.0+2.5) × 1.0
    4: 2.0,   # (2.0) × 1.0
}
