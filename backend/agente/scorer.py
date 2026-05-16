'''
scorer.py
=========
Calcula el score bruto del sistema experto por capa y entre capas.

PASOS que implementa este módulo:
    PASO 1: Score bruto por capa      S_k = Σ(valor_i × peso_i)
    PASO 2: Score normalizado por capa S_k_norm = S_k / Max_teórico_capa_k
    PASO 3: Score ponderado inter-capas
            Score_bruto = (0.15 × S1_norm) + (0.30 × S2_norm)
                        + (0.35 × S3_norm) + (0.20 × S4_norm)

Los PASOS 4, 5 y 6 (sinergias, protectores, clasificación final)
están en sus propios módulos: synergies.py, protectors.py, classifier.py.

PESOS INTER-CAPAS (del Excel):
    Capa 1 — Vulnerabilidad Basal   : 0.15
    Capa 2 — Estado Funcional       : 0.30
    Capa 3 — Escalada Clínica       : 0.35  ← mayor peso
    Capa 4 — Factores Protectores   : 0.20
'''

from __future__ import annotations
from .variables import VARIABLES, MAX_TEORICO_CAPA

# Peso de cada capa en el score inter-capas final
PESO_CAPA = {
    1: 0.15,
    2: 0.30,
    3: 0.35,
    4: 0.20,
}


def calcular_score_por_capa(respuestas: dict[str, float]) -> dict[int, float]:
    '''
    PASO 1: Score bruto por capa.
    S_k = Σ(valor_i × peso_i) para cada variable i en la capa k.

    Args:
        respuestas: {"1A": 0.2, "1B": 1.0, ...}  — salida de mapper.py

    Returns:
        {1: 1.84, 2: 6.20, 3: 4.10, 4: 0.40}
    '''
    scores = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}

    for codigo, valor in respuestas.items():
        var = VARIABLES.get(codigo)
        if var is None:
            continue
        scores[var["layer"]] += valor * var["weight"]

    return scores


def normalizar_scores(scores_brutos: dict[int, float]) -> dict[int, float]:
    '''
    PASO 2: Score normalizado por capa → rango [0.0, 1.0].
    S_k_norm = S_k / Max_teórico_capa_k

    El máximo teórico es cuando todas las variables de la capa = 1.0.

    Args:
        scores_brutos: {1: 1.84, 2: 6.20, 3: 4.10, 4: 0.40}

    Returns:
        {1: 0.279, 2: 0.459, 3: 0.373, 4: 0.200}
    '''
    return {
        capa: min(1.0, score / MAX_TEORICO_CAPA[capa])
        for capa, score in scores_brutos.items()
    }


def calcular_score_bruto(respuestas: dict[str, float]) -> dict:
    '''
    PASOS 1, 2 y 3 combinados.
    Función principal del módulo — la llama classifier.py.

    Args:
        respuestas: {"1A": 0.2, "1B": 1.0, ...}  — salida de mapper.py

    Returns:
        {
            "por_capa_bruto":     {1: 1.84, 2: 6.20, 3: 4.10, 4: 0.40},
            "por_capa_norm":      {1: 0.279, 2: 0.459, 3: 0.373, 4: 0.200},
            "score_bruto":        0.412,   # score inter-capas [0.0, 1.0]
            "contribucion_capa":  {1: 0.042, 2: 0.138, 3: 0.131, 4: 0.040},
        }
    '''
    scores_brutos = calcular_score_por_capa(respuestas)
    scores_norm   = normalizar_scores(scores_brutos)

    # PASO 3: ponderación inter-capas
    contribucion = {
        capa: PESO_CAPA[capa] * scores_norm[capa]
        for capa in scores_norm
    }
    score_bruto = sum(contribucion.values())

    return {
        "por_capa_bruto":    scores_brutos,
        "por_capa_norm":     scores_norm,
        "score_bruto":       round(score_bruto, 6),
        "contribucion_capa": {c: round(v, 6) for c, v in contribucion.items()},
    }


def aplicar_bonus(score_bruto: float, respuestas: dict[str, float]) -> tuple[float, list[str]]:
    '''
    Bonus de las Reglas Anti-Falso Positivo del Excel (Tabla de Riesgos).

    Regla 3: ≥ 4 variables Capa 2 en valor ≥ 0.6  → +0.15
    Regla 4: ≥ 2 variables Capa 3 en valor = 1.0   → +0.20

    Estos bonus se suman ANTES de aplicar el Factor_Protector.

    Args:
        score_bruto: resultado del PASO 3
        respuestas:  dict completo de variable → valor

    Returns:
        (score_con_bonus, lista de bonus aplicados)
    '''
    bonus_aplicados = []
    score = score_bruto

    # Regla 3: múltiples moderados en Capa 2
    capa2_en_medio_o_alto = sum(
        1 for cod, val in respuestas.items()
        if VARIABLES.get(cod, {}).get("layer") == 2 and val >= 0.6
    )
    if capa2_en_medio_o_alto >= 4:
        score += 0.15
        bonus_aplicados.append(
            f"Regla 3: {capa2_en_medio_o_alto} variables Capa 2 ≥ 0.6 → +0.15"
        )

    # Regla 4: múltiples altos en Capa 3
    capa3_en_alto = sum(
        1 for cod, val in respuestas.items()
        if VARIABLES.get(cod, {}).get("layer") == 3 and val == 1.0
    )
    if capa3_en_alto >= 2:
        score += 0.20
        bonus_aplicados.append(
            f"Regla 4: {capa3_en_alto} variables Capa 3 = 1.0 → +0.20"
        )

    return min(1.0, score), bonus_aplicados


def techo_anti_falso_positivo(nivel: int, respuestas: dict[str, float],
                               reglas_activas: int) -> tuple[int, str | None]:
    '''
    Reglas Anti-Falso Positivo que LIMITAN el nivel máximo (Tabla de Riesgos).

    Regla 1: Solo 1 variable Capa 3 en Alto y sin sinergias activas
             → nivel máximo = 4

    Regla 2: 4A (Sustancias) o 4B (Diagnóstico) en Alto
             + ≥ 2 variables Capa 2 en Medio+
             → excepción: puede llegar a 5

    Args:
        nivel:          nivel calculado (1–5)
        respuestas:     dict completo de variable → valor
        reglas_activas: número de reglas sinérgicas que se activaron

    Returns:
        (nivel_final, razon_del_techo_si_aplica)
    '''
    capa3_en_alto = [
        cod for cod, val in respuestas.items()
        if VARIABLES.get(cod, {}).get("layer") == 3 and val == 1.0
    ]

    # Regla 1: un solo factor Capa 3 alto sin sinergia → techo en 4
    if nivel == 5 and len(capa3_en_alto) == 1 and reglas_activas == 0:
        # Verificar si aplica la excepción de Regla 2
        es_escalador = capa3_en_alto[0] in ("4A", "4B")
        capa2_medio_plus = sum(
            1 for cod, val in respuestas.items()
            if VARIABLES.get(cod, {}).get("layer") == 2 and val >= 0.6
        )
        if es_escalador and capa2_medio_plus >= 2:
            return nivel, None  # excepción Regla 2: se permite nivel 5
        return 4, (
            f"Anti-FP Regla 1: solo '{capa3_en_alto[0]}' en Alto "
            f"y 0 sinergias activas → techo Riesgo 4"
        )

    return nivel, None
