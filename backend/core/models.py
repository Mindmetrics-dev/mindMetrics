"""
core/models.py — MindMetrics
============================================================
Modelos ORM de dominio para el esquema 3NF de MindMetrics.

DECISIÓN ARQUITECTÓNICA: managed = False en TODAS las tablas.
  - Las tablas son creadas/gestionadas por 02_create_tables.sql
    (vía docker-entrypoint-initdb.d/ o el management command
    `create_domain_tables`), NO por las migraciones de Django.
  - Con managed=False Django usa los modelos para acceso ORM
    (SELECT / INSERT / UPDATE / DELETE / bulk_create) pero
    nunca ejecuta CREATE TABLE, ALTER TABLE ni DROP TABLE.
  - Índices declarados en Meta.indexes sirven como documentación
    y para introspección del admin; no son emitidos en migraciones.

IMPORTANTE: los campos TEXT que en el CSV contienen valores
  numéricos (cambio_emocional, apoyo_percibido, etc.) se
  almacenan como texto plano sin choices en el ORM para evitar
  conflictos con los datos reales del dataset (enteros 1-10).
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# ─────────────────────────────────────────────────────────────────────────────
# CHOICES — solo para campos cuyo dominio es realmente discreto/categórico
# ─────────────────────────────────────────────────────────────────────────────

class NivelRiesgoChoices(models.TextChoices):
    BAJO     = 'bajo',     'Bajo'
    MODERADO = 'moderado', 'Moderado'
    ALTO     = 'alto',     'Alto'
    CRITICO  = 'critico',  'Crítico'


# ─────────────────────────────────────────────────────────────────────────────
# 1. TABLAS MAESTRAS
# ─────────────────────────────────────────────────────────────────────────────

class Usuario(models.Model):
    """
    Tabla de dominio `usuario` — gestionada por SQL, NO por migraciones.
    DIFERENTE de usuarios.CustomUser (que es el modelo de autenticación web).
    Esta tabla almacena los usuarios cargados desde el CSV del dataset de ML.
    """
    id_usuario              = models.AutoField(primary_key=True)
    email                   = models.EmailField(max_length=100, unique=True)
    # Siempre almacenar hash Django (make_password). Nunca texto plano.
    password                = models.TextField()
    nickname                = models.CharField(max_length=50, null=True, blank=True)
    activo                  = models.BooleanField(default=True)
    consentimiento_aceptado = models.BooleanField(default=False)
    # Columna SQL: "2FA_habilitado" — nombre ilegal en Python, mapeado aquí.
    two_fa_habilitado = models.BooleanField(
        default=False,
        db_column='2FA_habilitado',
        verbose_name='2FA habilitado',
    )

    class Meta:
        managed             = False        # tablas creadas por SQL, no por Django
        db_table            = 'usuario'
        verbose_name        = 'Usuario (dominio)'
        verbose_name_plural = 'Usuarios (dominio)'

    def __str__(self):
        return f'[{self.id_usuario}] {self.email}'


class Emocion(models.Model):
    """Catálogo de emociones — tabla maestra."""
    id_emocion     = models.AutoField(primary_key=True)
    nombre_emocion = models.CharField(max_length=50)

    class Meta:
        managed             = False
        db_table            = 'emocion'
        verbose_name        = 'Emoción'
        verbose_name_plural = 'Emociones'

    def __str__(self):
        return self.nombre_emocion


class TipoRecurso(models.Model):
    """Catálogo de tipos de recurso."""
    id_tipo_recurso = models.AutoField(primary_key=True)
    nombre_recurso  = models.CharField(max_length=100)

    class Meta:
        managed             = False
        db_table            = 'tipo_recurso'
        verbose_name        = 'Tipo de recurso'
        verbose_name_plural = 'Tipos de recurso'

    def __str__(self):
        return self.nombre_recurso


# ─────────────────────────────────────────────────────────────────────────────
# 2. TABLAS DEPENDIENTES
# ─────────────────────────────────────────────────────────────────────────────

class EvaluacionInicial(models.Model):
    """
    Evaluación inicial del usuario: datos sociodemográficos, hábitos y
    antecedentes clínicos. Destino principal del ETL load_csv_normalized.

    Notas sobre tipos:
      - hr_trabajo: puede ser horas semanales (max 70 en el dataset).
        El validador acepta hasta 168 h (semana completa).
      - cambio_emocional, dificultad_concentra, apoyo_percibido:
        almacenados como TEXT según el DDL, contienen enteros 1-10
        como cadena ("1"–"10").
      - uso_sustancias, diagnostico_previo, tratamiento_previo:
        TEXT en DDL, contienen "0" o "1".
      - historial_panico, historial_familiar: BOOLEAN en DDL.
    """
    id_eval    = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuario',
        related_name='evaluaciones_iniciales',
    )

    # ── Datos sociodemográficos ──────────────────────────────────────────────
    edad = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(120)],
    )
    genero            = models.CharField(max_length=20,  null=True, blank=True)
    estado_relacion   = models.CharField(max_length=50,  null=True, blank=True)
    situacion_trabajo = models.CharField(max_length=100, null=True, blank=True)

    # ── Hábitos de vida ──────────────────────────────────────────────────────
    hr_sueno = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(24.0)],
        verbose_name='Horas de sueño (diarias)',
    )
    # hr_trabajo puede ser horas semanales → cap en 168 (7 × 24)
    hr_trabajo = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(168.0)],
        verbose_name='Horas de trabajo',
    )
    hr_pantalla = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(24.0)],
        verbose_name='Horas de pantalla',
    )
    hr_act_fis = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(24.0)],
        verbose_name='Horas de actividad física',
    )

    # ── Niveles de estrés y satisfacción (escala 1-10) ───────────────────────
    estres_laboral = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    estres_academico = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    estres_financ = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Estrés financiero',
    )
    satisfaccion_laboral = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    # ── Campos TEXT que contienen valores numéricos 0–10 ────────────────────
    # No se definen choices aquí porque los valores reales son cadenas numéricas
    # ("1" a "10") provenientes del dataset. Si en el futuro se codifican como
    # texto descriptivo, se pueden agregar choices sin cambiar la columna SQL.
    uso_sustancias       = models.TextField(null=True, blank=True)
    dificultad_concentra = models.TextField(
        null=True, blank=True,
        db_column='dificultad_concentra',   # CSV: dificultad_concentracion
        verbose_name='Dificultad de concentración',
    )
    cambio_emocional   = models.TextField(null=True, blank=True)
    diagnostico_previo = models.TextField(null=True, blank=True)
    tratamiento_previo = models.TextField(null=True, blank=True)
    apoyo_percibido    = models.TextField(null=True, blank=True)

    # ── Antecedentes booleanos ───────────────────────────────────────────────
    historial_panico   = models.BooleanField(null=True, blank=True)
    historial_familiar = models.BooleanField(null=True, blank=True)

    class Meta:
        managed             = False
        db_table            = 'evaluacion_inicial'
        verbose_name        = 'Evaluación inicial'
        verbose_name_plural = 'Evaluaciones iniciales'

    def __str__(self):
        return f'Eval #{self.id_eval} — Usuario {self.id_usuario_id}'


class RegistroEmocional(models.Model):
    """
    Registro diario conductual. nivel_riesgo es el output del pipeline KNN/SVM.
    """
    id_registro  = models.AutoField(primary_key=True)
    id_usuario   = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        db_column='id_usuario',
        related_name='registros_emocionales',
    )
    id_emocion   = models.ForeignKey(
        Emocion,
        on_delete=models.RESTRICT,
        db_column='id_emocion',
        related_name='registros',
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    nivel_riesgo   = models.CharField(
        max_length=50, null=True, blank=True,
        choices=NivelRiesgoChoices.choices,
        verbose_name='Nivel de riesgo (ML output)',
    )

    # ── Métricas del día ─────────────────────────────────────────────────────
    hr_sueno_dia    = models.FloatField(null=True, blank=True,
                          validators=[MinValueValidator(0.0), MaxValueValidator(24.0)])
    hr_trabajo_dia  = models.FloatField(null=True, blank=True,
                          validators=[MinValueValidator(0.0), MaxValueValidator(168.0)])
    hr_pantalla_dia = models.FloatField(null=True, blank=True,
                          validators=[MinValueValidator(0.0), MaxValueValidator(24.0)])
    hr_act_fis_dia  = models.FloatField(null=True, blank=True,
                          validators=[MinValueValidator(0.0), MaxValueValidator(24.0)])
    estres_laboral_dia   = models.IntegerField(null=True, blank=True,
                               validators=[MinValueValidator(1), MaxValueValidator(10)])
    estres_academico_dia = models.IntegerField(null=True, blank=True,
                               validators=[MinValueValidator(1), MaxValueValidator(10)])
    estres_financ_dia    = models.IntegerField(null=True, blank=True,
                               validators=[MinValueValidator(1), MaxValueValidator(10)])
    apoyo_percibido_dia  = models.TextField(null=True, blank=True)
    autocuidado          = models.TextField(null=True, blank=True)
    animo                = models.TextField(null=True, blank=True)

    class Meta:
        managed             = False
        db_table            = 'registro_emocional'
        verbose_name        = 'Registro emocional'
        verbose_name_plural = 'Registros emocionales'

    def __str__(self):
        return f'Reg #{self.id_registro} — {self.fecha_registro}'


class RecursoApoyo(models.Model):
    """Recurso de apoyo psicológico (artículo, video, ejercicio, etc.)."""
    id_recurso      = models.AutoField(primary_key=True)
    id_tipo_recurso = models.ForeignKey(
        TipoRecurso,
        on_delete=models.RESTRICT,
        db_column='id_tipo_recurso',
        related_name='recursos',
    )
    titulo      = models.CharField(max_length=200)
    informacion = models.TextField(null=True, blank=True)
    imagen      = models.TextField(null=True, blank=True,
                                   verbose_name='Ruta o URL de imagen')

    class Meta:
        managed             = False
        db_table            = 'recurso_apoyo'
        verbose_name        = 'Recurso de apoyo'
        verbose_name_plural = 'Recursos de apoyo'

    def __str__(self):
        return self.titulo


# ─────────────────────────────────────────────────────────────────────────────
# 3. TABLA DE RELACIÓN M2M
# ─────────────────────────────────────────────────────────────────────────────

class PresentacionRecurso(models.Model):
    """
    Registra qué recurso fue presentado a qué usuario y cuándo.

    La PK compuesta del DDL (id_usuario, id_recurso, fecha_presentacion)
    no puede representarse nativamente en Django. Se usa clave sustituta
    implícita + UniqueConstraint para reproducir la semántica. El ORM
    respeta la restricción vía IntegrityError en inserciones duplicadas.
    Con managed=False la PK real en Postgres sigue siendo la compuesta.
    """
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        db_column='id_usuario',
        related_name='presentaciones',
    )
    id_recurso = models.ForeignKey(
        RecursoApoyo,
        on_delete=models.RESTRICT,
        db_column='id_recurso',
        related_name='presentaciones',
    )
    fecha_presentacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed             = False
        db_table            = 'presentacion_recurso'
        verbose_name        = 'Presentación de recurso'
        verbose_name_plural = 'Presentaciones de recurso'

    def __str__(self):
        return (f'Usuario {self.id_usuario_id} → '
                f'Recurso {self.id_recurso_id}')
