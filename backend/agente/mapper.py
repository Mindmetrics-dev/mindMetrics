'''
Convierte un registro base de evaluacion_inicial al formato
que el motor de inferencia necesita: 

{codigo_variable: valor_numerico} donde valor_numerico ∈ {0.2, 0.6, 1.0}.

CONVENCIÓN de valores:
    0.2 = Bajo    (sin riesgo / protector)
    0.6 = Medio   (riesgo moderado)
    1.0 = Alto    (mayor riesgo)

Cada variable se mapea según criterios clínicos basados en la literatura
'''

from __future__ import annotations
from typing import Union


def _get(data: Union[dict, object], field: str):
    '''Extrae un campo de un dict o de un objeto Django model.'''
    if isinstance(data, dict):
        return data.get(field)
    return getattr(data, field, None)


def _map_texto_tristate(valor: str | None,
                        bajo: tuple,
                        medio: tuple,
                        alto: tuple,
                        default: float = 0.2) -> float:
    '''
    Mapea un valor de texto a {0.2, 0.6, 1.0} usando grupos de strings.
    La comparación es case-insensitive y strip() automático.
    '''
    if valor is None:
        return default
    v = str(valor).strip().lower()
    if v in bajo:
        return 0.2
    if v in medio:
        return 0.6
    if v in alto:
        return 1.0
    return default


def _map_escala(valor: int | float | None,
                umbral_medio: float,
                umbral_alto: float,
                default: float = 0.2) -> float:
    '''
    Mapea un valor numérico de escala a {0.2, 0.6, 1.0}.
    valor < umbral_medio  → 0.2
    valor < umbral_alto   → 0.6
    valor >= umbral_alto  → 1.0
    '''
    if valor is None:
        return default
    if valor >= umbral_alto:
        return 1.0
    if valor >= umbral_medio:
        return 0.6
    return 0.2


# ---------------------------------------------------------------------------
# Mapeo de cada variable
# ---------------------------------------------------------------------------

def _map_edad(data) -> float:
    '''
    Bajo  (0.2): 33+ años  - franja de menor riesgo relativo
    Medio (0.6): rangos intermedios no especificados
    Alto  (1.0): 18-21  - franja de mayor riesgo
    '''
    edad = _get(data, "edad")
    if edad is None:
        return 0.2
    if 33 <= edad :
        return 0.2
    if (18 <= edad <= 21) :
        return 1.0
    return 0.6  # 22-32 es el rango intermedio


def _map_genero(data) -> float:
    '''
    Bajo  (0.2): Ambos / no binario / otro
    Medio (0.6): Masculino
    Alto  (1.0): Femenino  (mayor prevalencia de riesgo psicosocial)
    '''
    genero = _get(data, "genero")
    if genero is None:
        return 0.2
    g = str(genero).strip().lower()
    if g in ("femenino", "mujer", "f"):
        return 1.0
    if g in ("masculino", "hombre", "m"):
        return 0.6
    return 0.2  # no binario, otro, prefiero no decir


def _map_estado_relacion(data) -> float:
    '''
    Bajo  (0.2): Noviazgo activo
    Medio (0.6): Matrimonio / Poliamor / En pareja
    Alto  (1.0): Soltero/a / Divorciado / Viudo
    '''
    return _map_texto_tristate(
        _get(data, "estado_relacion"),
        bajo=("noviazgo", "noviazgo activo"),
        medio=("matrimonio", "casado", "casada", "poliamor", "en pareja", "union libre"),
        alto=("soltero", "soltera", "soltero/a", "divorciado", "divorciada",
              "viudo", "viuda", "separado", "separada"),
        default=0.6,
    )


def _map_historial_familiar(data) -> float:
    '''
    Campo BOOLEAN en la BD.
    False / None → 0.2 (Ausente)
    True         → 1.0 (Existente)

    Si en el futuro se cambia a TEXT, se puede extender a 0.6 (resuelto).
    '''
    val = _get(data, "historial_familiar")
    if val is None or val is False:
        return 0.2
    return 1.0


def _map_diagnostico_previo(data) -> float:
    '''
    ⚠ Ancla clínica — peso 2.5
    BOOLEAN en la BD:
        False / None → 0.2 (sin diagnóstico)
        True         → 1.0 (con diagnóstico)
    '''
    val = _get(data, "diagnostico_previo")
    if val is None or val is False:
        return 0.2
    return 1.0


def _map_situacion_trabajo(data) -> float:
    '''
    Bajo  (0.2): Pensionado / Empleo estable / Estudiante con beca
    Medio (0.6): Empleado informal / Freelance / Trabajo parcial
    Alto  (1.0): Desempleado / Buscando trabajo
    '''
    return _map_texto_tristate(
        _get(data, "situacion_trabajo"),
        bajo=("pensionado", "pensionada", "empleo estable", "empleado estable",
              "empleada estable", "empleado formal", "empleada formal",
              "estudiante", "jubilado", "jubilada", "empleado tiempo completo"),
        medio=("informal", "empleado informal", "freelance", "independiente",
               "tiempo parcial", "part time", "contrato temporal", "empleado medio tiempo"),
        alto=("desempleado", "desempleada", "sin trabajo", "sin empleo",
              "buscando trabajo", "cesante"),
        default=0.6,
    )


def _map_hr_sueno(data) -> float:
    '''
    Bajo  (0.2): 7–9 h — rango óptimo
    Medio (0.6): 5–6 h o 10+ h — fuera del óptimo
    Alto  (1.0): < 4 h — privación severa
    '''
    hr = _get(data, "hr_sueno")
    if hr is None:
        return 0.6
    if hr < 4:
        return 1.0
    if hr < 5 or hr >= 10:
        return 0.6  # privación moderada o exceso
    if 5 <= hr < 7:
        return 0.6
    if 7 <= hr <= 9:
        return 0.2
    return 0.6  # 9–10h: rango limítrofe


def _map_hr_trabajo(data) -> float:
    '''
    Bajo  (0.2): ≤ 40 h/semana
    Medio (0.6): 41–48 h/semana
    Alto  (1.0): > 48 h/semana
    '''
    hr = _get(data, "hr_trabajo")
    if hr is None:
        return 0.2
    if hr > 48:
        return 1.0
    if hr > 40:
        return 0.6
    return 0.2


def _map_hr_pantalla(data) -> float:
    '''
    Bajo  (0.2): < 2 h recreativas/día
    Medio (0.6): 2–5 h/día
    Alto  (1.0): > 6 h/día
    '''
    hr = _get(data, "hr_pantalla")
    if hr is None:
        return 0.2
    if hr > 6:
        return 1.0
    if hr >= 2:
        return 0.6
    return 0.2


def _map_hr_act_fis(data) -> float:
    '''
    La BD guarda horas/semana — convertimos a minutos para comparar.
    Bajo  (0.2): ≥ 150 min/semana (≥ 2.5 h) — activo
    Medio (0.6): 60–149 min/semana (1–2.5 h) — moderado
    Alto  (1.0): < 30 min/semana (< 0.5 h)  — sedentario

    NOTA: actividad física BAJA = mayor riesgo (lógica directa).
    El efecto protector de actividad alta se aplica en protectors.py.
    '''
    hr = _get(data, "hr_act_fis")
    if hr is None:
        return 1.0  # sin dato → asumir sedentario
    minutos = hr * 60
    if minutos >= 150:
        return 0.2
    if minutos >= 60:
        return 0.6
    return 1.0


def _map_estres_escala(campo: str, data) -> float:
    '''
    Escala INTEGER 1–10.
    Bajo  (0.2): 1–3   — estrés bajo o ausente
    Medio (0.6): 4–6   — estrés moderado / ocasional
    Alto  (1.0): 7–10  — estrés constante / elevado
    '''
    val = _get(data, campo)
    if val is None:
        return 0.2
    return _map_escala(val, umbral_medio=4, umbral_alto=7, default=0.2)


def _map_uso_sustancias(data) -> float:
    '''
    ⚠ Escalador crítico — peso 3.0
    BOOLEAN en la BD:
        False / None → 0.2 (no consume)
        True         → 1.0 (consume)

    NOTA: booleano elimina el nivel Medio (0.6 = consumo ocasional).
    Si en el futuro se cambia a escala, extender a tristate.
    '''
    val = _get(data, "uso_sustancias")
    if val is None or val is False:
        return 0.2
    return 1.0


def _map_dificultad_concentra(data) -> float:
    '''
    ninguno / sin alteraciones → 0.2
    ocasional / leve           → 0.6
    severo / frecuente         → 1.0
    '''
    return _map_texto_tristate(
        _get(data, "dificultad_concentra"),
        bajo=("ninguno", "no", "sin alteraciones", "none", ""),
        medio=("ocasional", "leve", "a veces", "moderado"),
        alto=("severo", "frecuente", "constante", "grave", "significativo"),
        default=0.2,
    )


def _map_satisfaccion_laboral(data) -> float:
    '''
    INTEGER — escala INVERTIDA 1–10: alta satisfacción = bajo riesgo.
    Bajo  (0.2): 7–10 — alta satisfacción
    Medio (0.6): 4–6  — insatisfacción ocasional
    Alto  (1.0): 1–3  — nula o muy poca satisfacción
    '''
    val = _get(data, "satisfaccion_laboral")
    if val is None:
        return 0.2
    if val >= 7:
        return 0.2
    if val >= 4:
        return 0.6
    return 1.0


def _map_cambio_emocional(data) -> float:
    '''
    Escala INTEGER 1–10 (igual que estrés).
    Bajo  (0.2): 1–3  — respuestas estables / esperadas
    Medio (0.6): 4–6  — desregulación ocasional
    Alto  (1.0): 7–10 — labilidad afectiva / cambio marcado
    '''
    return _map_estres_escala("cambio_emocional", data)


def _map_historial_panico(data) -> float:
    '''
    Campo BOOLEAN en la BD.
    False / None → 0.2
    True         → 1.0

    Si se cambia a TEXT en el futuro: resuelto → 0.6, activo → 1.0
    '''
    val = _get(data, "historial_panico")
    if val is None or val is False:
        return 0.2
    return 1.0


def _map_tratamiento_previo(data) -> float:
    '''
    ⚠ Variable con lógica ESPECIAL:
        Sin intervención        → 0.2  (sin antecedentes)
        Tratamiento ADHERENTE   → 0.6  (actúa como protector en reglas)
        No adherente / abandono → 1.0  (escalador de riesgo)

    La lógica de inversión (adherente = protector) se aplica en
    protectors.py al calcular el Factor_Protector.
    '''
    return _map_texto_tristate(
        _get(data, "tratamiento_previo"),
        bajo=("ninguno", "no", "sin intervencion", "sin intervención",
              "nunca", "none", ""),
        medio=("adherente", "en tratamiento", "tratamiento actual",
               "con seguimiento", "cumple tratamiento"),
        alto=("no adherente", "abandono", "abandono terapeutico",
              "abandonó", "abandono tratamiento", "sin seguimiento"),
        default=0.2,
    )


def _map_apoyo_percibido(data) -> float:
    '''
    ⚠ LÓGICA INVERTIDA respecto a otras variables:
        Alto apoyo  → 0.2 (protector — REDUCE el score)
        Apoyo medio → 0.6
        Poco apoyo  → 1.0 (factor de riesgo)

    El efecto reductor se aplica en protectors.py.
    Aquí solo mapeamos el nivel como variable de riesgo.
    '''
    return _map_texto_tristate(
        _get(data, "apoyo_percibido"),
        bajo=("alto", "alta cohesion", "alta cohesión", "mucho apoyo",
              "red de apoyo fuerte", "excelente"),
        medio=("moderado", "intermitente", "moderado apoyo", "regular",
               "a veces"),
        alto=("nulo", "poco", "sin apoyo", "aislado", "aislada",
              "conflictos", "muy poco"),
        default=0.6,
    )


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

# Tabla de despacho: código de variable → función de mapeo
_MAPPERS = {
    "1A": _map_edad,
    "1B": _map_genero,
    "1C": _map_estado_relacion,
    "3F": _map_historial_familiar,
    "4B": _map_diagnostico_previo,
    "2A": _map_situacion_trabajo,
    "3A": _map_hr_sueno,
    "2B": _map_hr_trabajo,
    "2C": _map_hr_pantalla,
    "2D": _map_hr_act_fis,
    "2E": _map_dificultad_concentra,
    "3D": _map_satisfaccion_laboral,
    "3E": _map_cambio_emocional,
    "3B": lambda d: _map_estres_escala("estres_laboral", d),
    "3C": lambda d: _map_estres_escala("estres_academico", d),
    "4A": _map_uso_sustancias,
    "4C": _map_historial_panico,
    "4D": _map_tratamiento_previo,
    "4E": _map_apoyo_percibido,
}


def mapear_evaluacion(eval_data: Union[dict, object]) -> dict[str, float]:
    '''
    Convierte un registro de evaluacion_inicial al formato del motor.

    Args:
        eval_data: dict con los campos de evaluacion_inicial,
                   o un objeto Django model instance.

    Returns:
        dict con 19 entradas: {"1A": 0.2, "1B": 1.0, ..., "4E": 0.6}

    Ejemplo:
        from expert_system.engine.mapper import mapear_evaluacion
        from expert_system.engine.classifier import evaluar

        eval_obj = EvaluacionInicial.objects.get(id_usuario=usuario_id)
        respuestas = mapear_evaluacion(eval_obj)
        resultado = evaluar(respuestas)
        print(resultado["nivel_riesgo"])  # 1, 2, 3, 4 o 5
    '''
    return {codigo: mapper(eval_data) for codigo, mapper in _MAPPERS.items()}


def mapear_con_detalle(eval_data: Union[dict, object]) -> dict:
    '''
    Igual que mapear_evaluacion pero retorna detalle de cada variable
    útil para debugging y para mostrar al usuario qué factores activó.

    Returns:
        {
            "respuestas": {"1A": 1.0, ...},
            "detalle": {
                "1A": {"nombre": "Edad", "valor": 1.0, "nivel": "Alto"},
                ...
            }
        }
    '''
    from .variables import VARIABLES

    NIVELES = {0.2: "Bajo", 0.6: "Medio", 1.0: "Alto"}
    respuestas = {}
    detalle = {}

    for codigo, mapper in _MAPPERS.items():
        valor = mapper(eval_data)
        respuestas[codigo] = valor
        detalle[codigo] = {
            "nombre": VARIABLES[codigo]["name"],
            "capa": VARIABLES[codigo]["layer"],
            "peso": VARIABLES[codigo]["weight"],
            "valor": valor,
            "nivel": NIVELES.get(valor, "?"),
        }

    return {"respuestas": respuestas, "detalle": detalle}
