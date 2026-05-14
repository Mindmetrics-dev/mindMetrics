'''
synergies.py
============
Implementa las 21 reglas sinérgicas del sistema experto (PASO 4).

LÓGICA DE ACTIVACIÓN (del Excel):
    - Activación TOTAL  (×1.0): TODOS los factores de la regla = 1.0 (Alto)
    - Activación PARCIAL (×0.6): algún factor = 0.6 (Medio), ninguno = 0.2
    - NO se activa: cualquier factor = 0.2 (Bajo)

FÓRMULA DEL SCORE SINÉRGICO (PASO 4):
    S_sinérgico = min(1.0,
        max(valor_regla_activada_i) + 0.05 × (n_reglas_activas − 1)
    )

DEDUPLICACIÓN (reglas solapadas):
    Si dos reglas comparten los mismos factores, contar la mayor + 50% menor.
    Pares solapados definidos explícitamente según notas del Excel:
        (14, 21): "Deterioro Cognitivo Digital" vs "Riesgo Cognitivo-Compulsivo Digital"
        (15, 21): "Fatiga Tecnológica" vs "Riesgo Cognitivo-Compulsivo Digital"
        (13, 19): "Deterioro Ocupacional" vs "Aislamiento Funcional" (factor ×0.7)

CONDICIÓN ESPECIAL Regla 5 (Riesgo por Abandono Terapéutico):
    Solo activa si 4D = 1.0 (no adherente).
    Si 4D = 0.6 (adherente) → actúa como PROTECTOR: no suma, resta en protectors.py.

CONDICIÓN ESPECIAL Regla 6 (Riesgo Emocional Acumulado):
    Tiene dos versiones equivalentes. Si ambas se activarían, contar solo una vez.

SCORE SINÉRGICO NORMALIZADO:
    El máximo teórico de una sola regla es 22 pts (Regla 3 y Regla 20).
    Para normalizar a [0,1] usamos MAX_SINERGICO = 22.
    El score final del PASO 4 queda en [0, 1] antes de entrar al classifier.
'''

from __future__ import annotations
from dataclasses import dataclass, field

# Máximo valor de activación total en una sola regla (Regla 3 y 20 = 22)
MAX_SINERGICO = 22.0


# ---------------------------------------------------------------------------
# Estructura de una regla
# ---------------------------------------------------------------------------

@dataclass
class ReglaS:
    '''Define una regla sinérgica.'''
    id: int
    nombre: str
    factores: list[str]          # códigos de variables requeridos
    valor_total: float           # puntos si activación total (×1.0)
    valor_parcial: float         # puntos si activación parcial (×0.6)
    condicion_especial: str = "" # descripción de condición si aplica


# ---------------------------------------------------------------------------
# Las 21 reglas (valores según Excel revisado)
# ---------------------------------------------------------------------------

REGLAS: list[ReglaS] = [
    # ── CLÍNICAS ─────────────────────────────────────────────────────────
    ReglaS(
        id=1, nombre="Vulnerabilidad Clínica",
        factores=["4B", "4E"],
        valor_total=12, valor_parcial=7.2,
    ),
    ReglaS(
        id=2, nombre="Riesgo Ansioso Persistente",
        factores=["4C", "3E", "3A"],
        valor_total=18, valor_parcial=10.8,
    ),
    ReglaS(
        id=3, nombre="Vulnerabilidad Psiquiátrica Acumulada",
        factores=["4B", "4C", "4D"],
        valor_total=22, valor_parcial=13.2,
        condicion_especial="Si 4D=0.6 (adherente): 4D actúa como protector, no suma.",
    ),
    ReglaS(
        id=4, nombre="Riesgo Familiar-Clínico",
        factores=["3F", "4B", "4E"],
        valor_total=16, valor_parcial=9.6,
    ),
    ReglaS(
        id=5, nombre="Riesgo por Abandono Terapéutico",
        factores=["4D", "4B", "3E"],
        valor_total=20, valor_parcial=12.0,
        condicion_especial="Solo activa si 4D=1.0 (no adherente). 4D=0.6 → protector.",
    ),
    ReglaS(
        id=6, nombre="Riesgo Emocional Acumulado",
        factores=["4B", "3B", "3E"],   # versión laboral (principal)
        valor_total=16, valor_parcial=9.6,
        condicion_especial="Anti-doble-conteo con versión académica (4B+3C+3E).",
    ),

    # ── SOCIODEMOGRÁFICAS ────────────────────────────────────────────────
    ReglaS(
        id=7, nombre="Prevalencia Sociodemográfica",
        factores=["1A", "1B", "1C"],
        valor_total=8, valor_parcial=4.8,
    ),
    ReglaS(
        id=8, nombre="Vulnerabilidad Etaria",
        factores=["1A", "2A", "1C"],
        valor_total=10, valor_parcial=6.0,
    ),
    ReglaS(
        id=9, nombre="Vulnerabilidad de Género Contextual",
        factores=["1B", "3E", "4E"],
        valor_total=10, valor_parcial=6.0,
    ),

    # ── FUNCIONALES ──────────────────────────────────────────────────────
    ReglaS(
        id=10, nombre="Riesgo de Agotamiento",
        factores=["2B", "3A", "3B", "2E"],
        valor_total=18, valor_parcial=10.8,
    ),
    ReglaS(
        id=11, nombre="Sobrecarga Laboral Funcional",
        factores=["2B", "3B", "3D", "3E"],
        valor_total=20, valor_parcial=12.0,
    ),
    ReglaS(
        id=12, nombre="Aislamiento Funcional",
        factores=["1C", "2A", "4E"],
        valor_total=14, valor_parcial=8.4,
    ),
    ReglaS(
        id=13, nombre="Deterioro Ocupacional",
        factores=["2A", "3D", "4E"],
        valor_total=16, valor_parcial=9.6,
        condicion_especial="Si Regla 12 también activa → aplicar ×0.7 a la segunda.",
    ),
    ReglaS(
        id=14, nombre="Deterioro Cognitivo Digital",
        factores=["2C", "2E"],
        valor_total=10, valor_parcial=6.0,
        condicion_especial="Solapada con Regla 21. Activar solo si 3A NO está en Alto.",
    ),
    ReglaS(
        id=15, nombre="Fatiga Tecnológica",
        factores=["2C", "3A", "2E"],
        valor_total=14, valor_parcial=8.4,
        condicion_especial="Solapada con Regla 21. Deduplicar: mayor + 50% menor.",
    ),
    ReglaS(
        id=16, nombre="Sedentarismo Crítico",
        factores=["2D", "3A", "3E"],
        valor_total=14, valor_parcial=8.4,
    ),

    # ── EMOCIONAL / CONDUCTUAL ───────────────────────────────────────────
    ReglaS(
        id=17, nombre="Desregulación Emocional Funcional",
        factores=["3E", "2E", "3B"],
        valor_total=16, valor_parcial=9.6,
    ),
    ReglaS(
        id=18, nombre="Agotamiento Emocional-Académico",
        factores=["3C", "3A", "3E"],
        valor_total=14, valor_parcial=8.4,
    ),
    ReglaS(
        id=19, nombre="Riesgo Depresivo Contextual",
        factores=["4E", "1C", "3E"],
        valor_total=18, valor_parcial=10.8,
        condicion_especial="Si 4B también = 1.0 → bonus adicional +5 pts.",
    ),
    ReglaS(
        id=20, nombre="Riesgo por Sustancias y Desregulación",
        factores=["4A", "3E", "4E"],
        valor_total=22, valor_parcial=13.2,
    ),
    ReglaS(
        id=21, nombre="Riesgo Cognitivo-Compulsivo Digital",
        factores=["2C", "2E", "3A"],
        valor_total=14, valor_parcial=8.4,
        condicion_especial="Solapada con Reglas 14 y 15. Deduplicar con la de mayor valor.",
    ),
]

# Índice rápido por id
_REGLA_POR_ID: dict[int, ReglaS] = {r.id: r for r in REGLAS}

# Pares solapados que requieren deduplicación especial
# formato: (id_a, id_b, factor_dedup)
#   factor_dedup=0.5  → mayor + 50% menor
#   factor_dedup=0.7  → la segunda que se active se multiplica ×0.7
_PARES_SOLAPADOS = [
    (14, 21, 0.5),   # Cog. Digital vs Cog. Compulsivo
    (15, 21, 0.5),   # Fatiga Tecnológica vs Cog. Compulsivo
    (12, 13, 0.7),   # Aislamiento Funcional vs Deterioro Ocupacional
]


# ---------------------------------------------------------------------------
# Evaluación de una regla individual
# ---------------------------------------------------------------------------

@dataclass
class ResultadoRegla:
    '''Resultado de evaluar una regla.'''
    regla: ReglaS
    activada: bool
    tipo_activacion: str    # "total", "parcial", "no_activada"
    valor_obtenido: float
    nota: str = ""


def _evaluar_regla(regla: ReglaS, respuestas: dict[str, float]) -> ResultadoRegla:
    '''
    Evalúa si una regla se activa y con qué valor.

    Lógica base:
        - Si cualquier factor = 0.2 → no se activa
        - Si todos los factores = 1.0 → activación total
        - Si algún factor = 0.6 (y ninguno = 0.2) → activación parcial
    '''
    valores = {f: respuestas.get(f, 0.2) for f in regla.factores}
    minimo  = min(valores.values())
    todos_alto = all(v == 1.0 for v in valores.values())

    # Condición especial Regla 5: solo activa si 4D = 1.0
    if regla.id == 5:
        if respuestas.get("4D", 0.2) != 1.0:
            return ResultadoRegla(
                regla=regla, activada=False,
                tipo_activacion="no_activada", valor_obtenido=0.0,
                nota="Regla 5: 4D no es Alto (no adherente) → no se activa",
            )

    # Condición especial Regla 14: solo si 3A NO está en Alto
    if regla.id == 14:
        if respuestas.get("3A", 0.2) == 1.0:
            return ResultadoRegla(
                regla=regla, activada=False,
                tipo_activacion="no_activada", valor_obtenido=0.0,
                nota="Regla 14: 3A=Alto → usar Regla 21 en su lugar",
            )

    # No activada: algún factor es Bajo
    if minimo == 0.2:
        return ResultadoRegla(
            regla=regla, activada=False,
            tipo_activacion="no_activada", valor_obtenido=0.0,
        )

    # Activación total
    if todos_alto:
        valor = regla.valor_total

        # Bonus Regla 19: si 4B también está en Alto
        if regla.id == 19 and respuestas.get("4B", 0.2) == 1.0:
            valor += 5
            nota = "Bonus +5: 4B=Alto simultáneo"
        else:
            nota = ""

        return ResultadoRegla(
            regla=regla, activada=True,
            tipo_activacion="total", valor_obtenido=valor, nota=nota,
        )

    # Activación parcial (algún factor = 0.6, ninguno = 0.2)
    return ResultadoRegla(
        regla=regla, activada=True,
        tipo_activacion="parcial", valor_obtenido=regla.valor_parcial,
    )


# ---------------------------------------------------------------------------
# Deduplicación
# ---------------------------------------------------------------------------

def _deduplicar(activas: list[ResultadoRegla]) -> tuple[list[ResultadoRegla], list[str]]:
    '''
    Aplica lógica de deduplicación a reglas solapadas.
    Retorna la lista corregida y las notas de deduplicación aplicadas.
    '''
    ids_activos = {r.regla.id for r in activas}
    notas = []

    # Construir dict mutable de valores para poder ajustar
    valores = {r.regla.id: r.valor_obtenido for r in activas}

    for id_a, id_b, factor in _PARES_SOLAPADOS:
        if id_a in ids_activos and id_b in ids_activos:
            v_a = valores[id_a]
            v_b = valores[id_b]

            if factor == 0.5:
                # Mayor se queda igual, menor se multiplica por 0.5
                if v_a >= v_b:
                    valores[id_b] = round(v_b * 0.5, 4)
                    notas.append(
                        f"Dedup ({id_a},{id_b}): Regla {id_b} "
                        f"{v_b:.1f} → {valores[id_b]:.1f} (×0.5)"
                    )
                else:
                    valores[id_a] = round(v_a * 0.5, 4)
                    notas.append(
                        f"Dedup ({id_a},{id_b}): Regla {id_a} "
                        f"{v_a:.1f} → {valores[id_a]:.1f} (×0.5)"
                    )
            elif factor == 0.7:
                # La segunda que se evalúa se reduce ×0.7
                # Convención: id_b es la "segunda"
                valores[id_b] = round(v_b * 0.7, 4)
                notas.append(
                    f"Dedup ({id_a},{id_b}): Regla {id_b} "
                    f"{v_b:.1f} → {valores[id_b]:.1f} (×0.7)"
                )

    # Anti-doble-conteo Regla 6:
    # versión académica (4B+3C+3E) solapada con versión laboral (4B+3B+3E)
    # La versión académica no tiene regla propia en el Excel, ambas son Regla 6.
    # Se garantiza contando solo una vez (la regla ya tiene un solo id=6).

    # Aplicar valores deduplicados de vuelta a los objetos
    for resultado in activas:
        resultado.valor_obtenido = valores[resultado.regla.id]

    return activas, notas


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def calcular_score_sinergico(respuestas: dict[str, float]) -> dict:
    '''
    PASO 4: Calcula el score sinérgico normalizado [0, 1].

    Args:
        respuestas: {"1A": 0.2, "4A": 1.0, ...}  — salida de mapper.py

    Returns:
        {
            "score_sinergico":      0.614,   # normalizado [0, 1]
            "n_reglas_activas":     3,
            "reglas_activadas":     [ResultadoRegla, ...],
            "notas_deduplicacion":  ["Dedup (14,21): ..."],
            "detalle": [
                {
                    "id": 1, "nombre": "Vulnerabilidad Clínica",
                    "activada": True, "tipo": "total", "valor": 12.0,
                },
                ...
            ]
        }
    '''
    # Evaluar todas las reglas
    todos_resultados = [_evaluar_regla(r, respuestas) for r in REGLAS]
    activas = [r for r in todos_resultados if r.activada]

    # Deduplicar reglas solapadas
    if len(activas) > 1:
        activas, notas_dedup = _deduplicar(activas, )
    else:
        notas_dedup = []

    n_activas = len(activas)

    # FÓRMULA PASO 4:
    # S_sinérgico = min(1.0, max(valor_i) + 0.05 × (n − 1)) / MAX_SINERGICO
    if n_activas == 0:
        score_sinergico = 0.0
    else:
        valor_max = max(r.valor_obtenido for r in activas)
        score_raw = valor_max + 0.05 * (n_activas - 1)
        score_sinergico = min(1.0, score_raw / MAX_SINERGICO)

    return {
        "score_sinergico":     round(score_sinergico, 6),
        "n_reglas_activas":    n_activas,
        "reglas_activadas":    activas,
        "notas_deduplicacion": notas_dedup,
        "detalle": [
            {
                "id":       r.regla.id,
                "nombre":   r.regla.nombre,
                "activada": r.activada,
                "tipo":     r.tipo_activacion,
                "valor":    r.valor_obtenido,
                "nota":     r.nota,
            }
            for r in todos_resultados
        ],
    }
