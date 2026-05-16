"""
formulario/forms.py — MindMetrics

Dos ModelForm distintos:
  - DatasetForm: captura manual de entradas al dataset (formulario_datasetregistro).
  - EvaluacionInicialForm: formulario obligatorio al primer login.
    Persiste en `evaluacion_inicial` (managed=False, esquema dominio 3NF).

Todos los campos opcionales del modelo se exponen con required=False
para permitir un onboarding gradual; las validaciones de rango ya estan
declaradas en core/models.py (MinValueValidator/MaxValueValidator).

COMPATIBILIDAD CON agente/mapper.py
------------------------------------
Los widgets y choices de cada campo producen exactamente el tipo Python
que el mapper espera al hacer getattr(evaluacion, campo):

  Campo              Tipo en BD   Widget               Valor que llega al mapper
  -----------------  -----------  -------------------  --------------------------
  uso_sustancias     BOOLEAN      NullBooleanSelect    True | False | None
  diagnostico_previo BOOLEAN      NullBooleanSelect    True | False | None
  cambio_emocional   INTEGER      NumberInput(1-10)    int
  tratamiento_previo TEXT         Select descriptivo   'ninguno'|'adherente'|'abandono'
  dificultad_concentra TEXT       Select descriptivo   'ninguno'|'ocasional'|'frecuente'
  apoyo_percibido    TEXT         Select descriptivo   'excelente'|'alto'|...|'nulo'
"""
from __future__ import annotations

from django import forms

from core.models import EvaluacionInicial
from formulario.models import DatasetRegistro


# ─────────────────────────────────────────────────────────────────────────────
# 1. DatasetRegistro (captura manual)
# ─────────────────────────────────────────────────────────────────────────────
class DatasetForm(forms.ModelForm):
    class Meta:
        model = DatasetRegistro
        fields = ["nombre", "email", "edad", "profesion"]
        widgets = {
            "nombre":    forms.TextInput(attrs={"class": "form-control"}),
            "email":     forms.EmailInput(attrs={"class": "form-control"}),
            "edad":      forms.NumberInput(attrs={"class": "form-control"}),
            "profesion": forms.TextInput(attrs={"class": "form-control"}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Evaluacion inicial (gate de primer login)
# ─────────────────────────────────────────────────────────────────────────────

GENERO_CHOICES = [
    ("", "— Selecciona —"),
    ("femenino",   "Femenino"),
    ("masculino",  "Masculino"),
    ("no_binario", "No binario"),
    ("otro",       "Otro"),
]

ESTADO_RELACION_CHOICES = [
    ("", "— Selecciona —"),
    ("soltero",     "Soltero/a"),
    ("noviazgo",    "Noviazgo"),
    ("union libre", "Union libre"),
    ("casado",      "Casado/a"),
    ("poliamor",    "Poliamor"),
    ("divorciado",  "Divorciado/a"),
    ("viudo",       "Viudo/a"),
]

SITUACION_TRABAJO_CHOICES = [
    ("", "— Selecciona —"),
    ("estudiante",             "Estudiante"),
    ("empleado tiempo completo", "Empleado tiempo completo"),
    ("empleado medio tiempo",  "Empleado medio tiempo"),
    ("independiente",          "Independiente"),
    ("contrato temporal",      "Contrato temporal"),
    ("desempleado",            "Desempleado/a"),
    ("pensionado",             "Pensionado/a"),
]

# mapper._map_dificultad_concentra:
#   bajo=("ninguno",...) | medio=("ocasional","leve",...) | alto=("frecuente","severo",...)
DIFICULTAD_CONCENTRA_CHOICES = [
    ("", "— Selecciona —"),
    ("ninguno",   "Ninguna"),
    ("ocasional", "Ocasional"),
    ("frecuente", "Frecuente / severa"),
]

# mapper._map_apoyo_percibido:
#   bajo=("excelente","alto",...) | medio=("moderado","intermitente",...) | alto=("poco","nulo",...)
APOYO_PERCIBIDO_CHOICES = [
    ("", "— Selecciona —"),
    ("excelente",   "Excelente"),
    ("alto",        "Alto"),
    ("moderado",    "Moderado"),
    ("intermitente","Intermitente"),
    ("poco",        "Poco"),
    ("nulo",        "Nulo / sin apoyo"),
]

# mapper._map_tratamiento_previo:
#   bajo=("ninguno","no",...) | medio=("adherente","en tratamiento",...) | alto=("abandono",...)
TRATAMIENTO_PREVIO_CHOICES = [
    ("", "— Selecciona —"),
    ("ninguno",  "No, nunca he tenido tratamiento"),
    ("adherente", "Sí, actualmente en tratamiento (con seguimiento)"),
    ("abandono",  "Tuve tratamiento pero lo abandoné"),
]


def _input(cls="form-group__input", **extra):
    attrs = {"class": cls}
    attrs.update(extra)
    return attrs


class EvaluacionInicialForm(forms.ModelForm):
    """
    Formulario completo de evaluacion inicial.
    Se muestra UNA SOLA VEZ tras el signup (o en el primer login si quedo pendiente).
    Persiste 1 fila en `evaluacion_inicial` con FK a `usuario.id_usuario`.

    Los widgets producen exactamente los tipos que agente/mapper.py espera:
      - BooleanField  → NullBooleanSelect  → True/False/None
      - IntegerField  → NumberInput        → int
      - TextField     → Select descriptivo → string reconocido por _map_texto_tristate
    """

    class Meta:
        model = EvaluacionInicial
        # Se excluye id_eval (PK auto) e id_usuario (lo inyecta la vista).
        exclude = ["id_eval", "id_usuario"]
        widgets = {
            # ── Sociodemográfico ─────────────────────────────────────────────
            "edad": forms.NumberInput(attrs=_input(min=0, max=120)),
            "genero":            forms.Select(choices=GENERO_CHOICES,
                                              attrs=_input("form-group__select")),
            "estado_relacion":   forms.Select(choices=ESTADO_RELACION_CHOICES,
                                              attrs=_input("form-group__select")),
            "situacion_trabajo": forms.Select(choices=SITUACION_TRABAJO_CHOICES,
                                              attrs=_input("form-group__select")),

            # ── Hábitos (horas) ──────────────────────────────────────────────
            "hr_sueno":    forms.NumberInput(attrs=_input(min=0, max=24,  step="0.5")),
            "hr_trabajo":  forms.NumberInput(attrs=_input(min=0, max=168, step="0.5")),
            "hr_pantalla": forms.NumberInput(attrs=_input(min=0, max=24,  step="0.5")),
            "hr_act_fis":  forms.NumberInput(attrs=_input(min=0, max=24,  step="0.5")),

            # ── Escalas 1-10 (IntegerField → mapper recibe int) ───────────────
            "estres_laboral":       forms.NumberInput(attrs=_input(min=1, max=10)),
            "estres_academico":     forms.NumberInput(attrs=_input(min=1, max=10)),
            "estres_financ":        forms.NumberInput(attrs=_input(min=1, max=10)),
            "satisfaccion_laboral": forms.NumberInput(attrs=_input(min=1, max=10)),
            # cambio_emocional: IntegerField en modelo → mapper._map_escala espera int
            "cambio_emocional":     forms.NumberInput(attrs=_input(min=1, max=10)),

            # ── Booleanos (BooleanField → mapper recibe True/False/None) ─────
            # NullBooleanSelect entrega Python bool o None, nunca strings.
            "uso_sustancias":      forms.NullBooleanSelect(attrs={"class": "form-group__select"}),
            "diagnostico_previo":  forms.NullBooleanSelect(attrs={"class": "form-group__select"}),
            "historial_panico":    forms.NullBooleanSelect(attrs={"class": "form-group__select"}),
            "historial_familiar":  forms.NullBooleanSelect(attrs={"class": "form-group__select"}),

            # ── Campos TEXT descriptivos (mapper usa _map_texto_tristate) ─────
            "dificultad_concentra": forms.Select(choices=DIFICULTAD_CONCENTRA_CHOICES,
                                                 attrs=_input("form-group__select")),
            "apoyo_percibido":      forms.Select(choices=APOYO_PERCIBIDO_CHOICES,
                                                 attrs=_input("form-group__select")),
            "tratamiento_previo":   forms.Select(choices=TRATAMIENTO_PREVIO_CHOICES,
                                                 attrs=_input("form-group__select")),
        }
        labels = {
            "edad":                 "Edad",
            "genero":               "Género",
            "estado_relacion":      "Estado civil / pareja",
            "situacion_trabajo":    "Situación laboral",
            "hr_sueno":             "Horas de sueño (diarias)",
            "hr_trabajo":           "Horas de trabajo (semanales)",
            "hr_pantalla":          "Horas frente a pantalla (diarias)",
            "hr_act_fis":           "Horas de actividad física (semanales)",
            "estres_laboral":       "Estrés laboral (1-10)",
            "estres_academico":     "Estrés académico (1-10)",
            "estres_financ":        "Estrés financiero (1-10)",
            "satisfaccion_laboral": "Satisfacción laboral (1-10)",
            "cambio_emocional":     "Cambios emocionales bruscos (1-10)",
            "uso_sustancias":       "¿Consumes sustancias psicoactivas?",
            "dificultad_concentra": "Dificultad para concentrarse",
            "diagnostico_previo":   "¿Tienes diagnóstico psicológico previo?",
            "tratamiento_previo":   "Tratamiento psicológico previo",
            "apoyo_percibido":      "Apoyo social percibido",
            "historial_panico":     "¿Has tenido crisis de pánico?",
            "historial_familiar":   "¿Antecedentes familiares de salud mental?",
        }

    # Campos que el agente necesita para calcular riesgo — todos obligatorios.
    CAMPOS_REQUERIDOS = {
        "edad", "genero", "estado_relacion", "situacion_trabajo",
        "hr_sueno", "hr_trabajo", "hr_pantalla", "hr_act_fis",
        "estres_laboral", "estres_academico", "estres_financ",
        "satisfaccion_laboral", "cambio_emocional",
        "uso_sustancias", "diagnostico_previo",
        "dificultad_concentra", "tratamiento_previo", "apoyo_percibido",
        "historial_panico", "historial_familiar",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.required = name in self.CAMPOS_REQUERIDOS


# ─────────────────────────────────────────────────────────────────────────────
# 3. Registro diario (formulario que el usuario llena cada día)
# ─────────────────────────────────────────────────────────────────────────────

# Las 6 emociones que el template ofrece. Coinciden con lo pre-poblado en la
# tabla `emocion`. Los valores van sin tildes y en minúscula para que la
# búsqueda en BD sea estable.
EMOCION_CHOICES = [
    ("miedo",    "Miedo"),
    ("tristeza", "Tristeza"),
    ("ira",      "Ira"),
    ("alegria",  "Alegría"),
    ("sorpresa", "Sorpresa"),
    ("asco",     "Asco"),
]


class RegistroDiarioForm(forms.Form):
    """
    Formulario del registro diario.

    NO es un ModelForm porque:
      - RegistroEmocional necesita la FK id_emocion (no un texto).
      - El service hace la resolución texto → Emocion y otros mapeos.
      - Algunos nombres de campo del formulario difieren del modelo
        (ej: horas_sueno en el form vs hr_sueno_dia en el modelo).

    Los names de los inputs coinciden con los del template registro_diario.html.
    """
    # ── Bloque 1: Hábitos (horas) ────────────────────────────────────────────
    horas_sueno = forms.FloatField(
        min_value=0, max_value=24, required=True,
        label="¿Cuántas horas dormiste hoy?",
    )
    horas_trabajo_estudio = forms.FloatField(
        min_value=0, max_value=24, required=True,
        label="¿Cuántas horas trabajaste o estudiaste hoy?",
    )
    horas_pantallas = forms.FloatField(
        min_value=0, max_value=24, required=True,
        label="¿Cuántas horas pasaste frente a pantallas hoy?",
    )
    horas_actividad_fisica = forms.FloatField(
        min_value=0, max_value=24, required=True,
        label="¿Cuántas horas realizaste actividad física hoy?",
    )

    # ── Bloque 2: Estrés (escalas 1-10) ──────────────────────────────────────
    estres_laboral = forms.IntegerField(
        min_value=1, max_value=10, required=True,
        label="Nivel de estrés laboral hoy",
    )
    estres_academico = forms.IntegerField(
        min_value=1, max_value=10, required=True,
        label="Nivel de estrés académico hoy",
    )
    estres_financiero = forms.IntegerField(
        min_value=1, max_value=10, required=True,
        label="Nivel de estrés financiero hoy",
    )

    # ── Bloque 3: Interacción y ánimo (escalas 1-10) ─────────────────────────
    interaccion_social = forms.IntegerField(
        min_value=1, max_value=10, required=True,
        label="Interacción con tu círculo cercano hoy",
    )
    animo = forms.IntegerField(
        min_value=1, max_value=10, required=True,
        label="Estado de ánimo hoy",
    )

    # ── Bloque 4: Cualitativos ───────────────────────────────────────────────
    autocuidado = forms.CharField(
        max_length=255, required=False,
        label="¿Realizaste alguna actividad de autocuidado hoy?",
    )
    emocion_predominante = forms.ChoiceField(
        choices=EMOCION_CHOICES, required=True,
        label="¿Qué emoción predominó durante el día?",
    )
