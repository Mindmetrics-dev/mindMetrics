'''
protectors.py
=============
Calcula el Factor_Protector que modula el score final (PASO 5).

FÓRMULA (del Excel):
    F_prot = 1.0 − Σ(reducción_j)
    Techo mínimo: 0.50  (nunca reduce más del 50% del score)

REDUCCIONES base definidas en el Excel:
    4E = Bajo (apoyo social ALTO)   → −0.12
    2D = Bajo (activo físicamente)  → −0.08
    3A = Bajo (sueño óptimo)        → −0.07
    4D = Medio (tratamiento adherente) → −0.10
    3F = Bajo (sin historial fam.)  → −0.05

CONDICIÓN ESPECIAL Regla 5 invertida:
    Si 4D = 0.6 (adherente) → ya está cubierto por la reducción −0.10.
    Si 4D = 0.2 (sin tratamiento previo) → no aplica reducción.
    Si 4D = 1.0 (no adherente) → no aplica reducción (es factor de riesgo).

DOBLE PROTECCIÓN (Regla AFP-6 del Excel):
    4E = Bajo + 2D = Bajo → −0.12 + −0.08 = −0.20 combinados.
    Ya cubierto por sumar ambas reducciones individualmente.

NOTA sobre 4E (Apoyo Social Percibido):
    En el mapper, 4E=Bajo (0.2) significa apoyo ALTO (protector).
    En el scorer, 4E=Alto (1.0) significa apoyo NULO (riesgo).
    Aquí operamos sobre el valor mapeado: si 4E=0.2 → aplicar reducción.
'''

from __future__ import annotations

# Techo mínimo del factor protector (nunca puede ser menor a esto)
FACTOR_PROTECTOR_MINIMO = 0.50

# Reducciones individuales: (código_variable, valor_que_activa, reducción)
_REDUCCIONES = [
    ("4E", 0.2, 0.12),   # Apoyo social ALTO (4E=Bajo en escala de riesgo)
    ("2D", 0.2, 0.08),   # Actividad física alta (2D=Bajo = activo)
    ("3A", 0.2, 0.07),   # Sueño óptimo (3A=Bajo = 7–9h)
    ("4D", 0.6, 0.10),   # Tratamiento adherente (4D=Medio)
    ("3F", 0.2, 0.05),   # Sin historial familiar (3F=Bajo)
]


def calcular_factor_protector(respuestas: dict[str, float]) -> dict:
    '''
    PASO 5: Calcula el Factor_Protector y detalla qué reducciones se aplicaron.

    Args:
        respuestas: {"1A": 0.2, "4E": 0.2, ...}  — salida de mapper.py

    Returns:
        {
            "factor_protector":   0.83,
            "reduccion_total":    0.17,
            "reducciones":  [
                {"variable": "4E", "nombre": "Apoyo Social Percibido",
                 "reduccion": 0.12, "motivo": "Apoyo social alto"},
                ...
            ]
        }
    '''
    from .variables import VARIABLES

    reducciones_aplicadas = []
    reduccion_total = 0.0

    for codigo, valor_activador, reduccion in _REDUCCIONES:
        valor_actual = respuestas.get(codigo, 0.2)

        if valor_actual == valor_activador:
            var_nombre = VARIABLES.get(codigo, {}).get("name", codigo)
            motivo = _motivo(codigo, valor_activador)

            reducciones_aplicadas.append({
                "variable":  codigo,
                "nombre":    var_nombre,
                "reduccion": reduccion,
                "motivo":    motivo,
            })
            reduccion_total += reduccion

    factor = max(FACTOR_PROTECTOR_MINIMO, 1.0 - reduccion_total)

    return {
        "factor_protector":  round(factor, 4),
        "reduccion_total":   round(reduccion_total, 4),
        "reducciones":       reducciones_aplicadas,
    }


def _motivo(codigo: str, valor: float) -> str:
    '''Descripción legible del motivo de cada reducción.'''
    motivos = {
        "4E": "Apoyo social alto → factor protector",
        "2D": "Actividad física activa → factor protector",
        "3A": "Sueño óptimo (7–9h) → factor protector",
        "4D": "Tratamiento psicológico adherente → factor protector",
        "3F": "Sin historial familiar de salud mental → factor protector",
    }
    return motivos.get(codigo, f"{codigo}={valor} actúa como protector")
