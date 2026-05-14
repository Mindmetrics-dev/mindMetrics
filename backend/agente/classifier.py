'''
classifier.py
=============
Integra todos los módulos y produce el nivel de riesgo final 1–5 (PASO 6).

FÓRMULA FINAL (del Excel):
    Score_final = (Score_bruto × 0.65 + Score_sinérgico × 0.25) × F_prot
                  + Ajuste_clínico × 0.10

    Nivel = ceil(Score_final × 5)  →  acotado en [1, 5]

AJUSTE CLÍNICO (0.10):
    Modificador adicional basado en escaladores críticos presentes.
    4A (Sustancias) = 1.0  → ajuste_clinico += 0.15
    4B (Diagnóstico) = 1.0 → ajuste_clinico += 0.10
    El ajuste_clinico se normaliza a [0, 1] antes de aplicar el ×0.10.

USO PRINCIPAL:
    from expert_system.engine.mapper import mapear_evaluacion
    from expert_system.engine.classifier import evaluar

    respuestas = mapear_evaluacion(evaluacion_obj)
    resultado  = evaluar(respuestas)

    nivel = resultado["nivel_riesgo"]   # 1, 2, 3, 4 o 5
'''

from __future__ import annotations
import math

from .mapper      import mapear_evaluacion
from .scorer      import calcular_score_bruto, aplicar_bonus, techo_anti_falso_positivo
from .rules   import calcular_score_sinergico
from .protectors  import calcular_factor_protector

# Pesos de la fórmula final
_W_BRUTO     = 0.65
_W_SINERGICO = 0.25
_W_CLINICO   = 0.10

# Etiquetas de nivel
ETIQUETAS_NIVEL = {
    1: "Muy Bajo",
    2: "Bajo",
    3: "Moderado",
    4: "Alto",
    5: "Crítico",
}

DESCRIPCIONES_NIVEL = {
    1: "Sin indicadores relevantes de riesgo psicosocial.",
    2: "Factores de riesgo presentes pero compensados por protectores.",
    3: "Múltiples factores activos. Requiere seguimiento y psicoeducación.",
    4: "Combinaciones sinérgicas activas. Intervención recomendada.",
    5: "Riesgo severo multifactorial. Atención clínica urgente.",
}


# ---------------------------------------------------------------------------
# Ajuste clínico
# ---------------------------------------------------------------------------

def _calcular_ajuste_clinico(respuestas: dict[str, float]) -> float:
    '''
    Ajuste basado en escaladores críticos de Capa 3.
    Retorna valor normalizado [0, 1].
    '''
    ajuste = 0.0
    if respuestas.get("4A", 0.2) == 1.0:   # Uso de Sustancias — peso 3.0
        ajuste += 0.15
    if respuestas.get("4B", 0.2) == 1.0:   # Diagnóstico Previo — peso 2.5
        ajuste += 0.10
    return min(1.0, ajuste)


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def evaluar(respuestas: dict[str, float]) -> dict:
    '''
    Ejecuta el pipeline completo y retorna el nivel de riesgo 1–5.

    Args:
        respuestas: {"1A": 0.2, "4A": 1.0, ...}
                    Salida de mapear_evaluacion() — valores en {0.2, 0.6, 1.0}

    Returns:
        {
            "nivel_riesgo":      3,
            "etiqueta":          "Moderado",
            "descripcion":       "Múltiples factores activos...",
            "score_final":       0.512,
            "score_bruto":       0.487,
            "score_bruto_bonus": 0.502,
            "score_sinergico":   0.341,
            "ajuste_clinico":    0.100,
            "factor_protector":  0.830,
            "techo_aplicado":    None,
            "detalle_scorer":    {...},    # salida completa de scorer.py
            "detalle_sinergias": {...},    # salida completa de synergies.py
            "detalle_protector": {...},    # salida completa de protectors.py
        }
    '''
    # PASOS 1–3: score por capas
    detalle_scorer   = calcular_score_bruto(respuestas)
    score_bruto      = detalle_scorer["score_bruto"]

    # Bonus anti-falso positivo (reglas 3 y 4 del Excel)
    score_con_bonus, _ = aplicar_bonus(score_bruto, respuestas)

    # PASO 4: score sinérgico
    detalle_sinergias = calcular_score_sinergico(respuestas)
    score_sinergico   = detalle_sinergias["score_sinergico"]
    n_reglas_activas  = detalle_sinergias["n_reglas_activas"]

    # PASO 5: factor protector
    detalle_protector = calcular_factor_protector(respuestas)
    factor_protector  = detalle_protector["factor_protector"]

    # Ajuste clínico
    ajuste_clinico = _calcular_ajuste_clinico(respuestas)

    # PASO 6: score final
    score_base  = score_con_bonus * _W_BRUTO + score_sinergico * _W_SINERGICO
    score_final = score_base * factor_protector + ajuste_clinico * _W_CLINICO
    score_final = min(1.0, max(0.0, score_final))

    # Nivel preliminar
    nivel = min(5, max(1, math.ceil(score_final * 5)))

    # Techo anti-falso positivo (Regla 1 del Excel)
    nivel, techo_aplicado = techo_anti_falso_positivo(
        nivel, respuestas, n_reglas_activas
    )

    return {
        "nivel_riesgo":      nivel,
        "etiqueta":          ETIQUETAS_NIVEL[nivel],
        "descripcion":       DESCRIPCIONES_NIVEL[nivel],
        "score_final":       round(score_final, 4),
        "score_bruto":       round(score_bruto, 4),
        "score_bruto_bonus": round(score_con_bonus, 4),
        "score_sinergico":   round(score_sinergico, 4),
        "ajuste_clinico":    round(ajuste_clinico * _W_CLINICO, 4),
        "factor_protector":  round(factor_protector, 4),
        "techo_aplicado":    techo_aplicado,
        "detalle_scorer":    detalle_scorer,
        "detalle_sinergias": detalle_sinergias,
        "detalle_protector": detalle_protector,
    }


def evaluar_desde_evaluacion(eval_data) -> dict:
    '''
    Shortcut que acepta directamente un objeto Django model o dict
    con los campos de evaluacion_inicial.

    Ejemplo en una view de Django:
        from expert_system.engine.classifier import evaluar_desde_evaluacion

        eval_obj = EvaluacionInicial.objects.get(id_usuario=request.user.id)
        resultado = evaluar_desde_evaluacion(eval_obj)
        return JsonResponse({"nivel_riesgo": resultado["nivel_riesgo"]})
    '''
    respuestas = mapear_evaluacion(eval_data)
    return evaluar(respuestas)
