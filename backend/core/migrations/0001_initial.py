"""
core/migrations/0001_initial.py — MindMetrics

Declara los modelos de dominio para que Django los conozca en su grafo
de migraciones, PERO con managed=False: las tablas SQL las gestiona
postgres/02_create_tables.sql (DDL idempotente).

Esta migracion NO emite CREATE TABLE / ALTER TABLE en BD. Solo registra
los modelos para que otras apps puedan declarar FKs hacia core.usuario
(p.ej. usuarios.CustomUser.usuario_dominio).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                ("id_usuario", models.AutoField(primary_key=True, serialize=False)),
                ("email",      models.EmailField(max_length=100, unique=True)),
                ("password",   models.TextField()),
                ("nickname",   models.CharField(max_length=50, null=True, blank=True)),
                ("activo",     models.BooleanField(default=True)),
                ("consentimiento_aceptado", models.BooleanField(default=False)),
                ("two_fa_habilitado", models.BooleanField(
                    default=False, db_column="2FA_habilitado")),
            ],
            options={
                "db_table": "usuario",
                "managed": False,
                "verbose_name": "Usuario (dominio)",
                "verbose_name_plural": "Usuarios (dominio)",
            },
        ),
        migrations.CreateModel(
            name="Emocion",
            fields=[
                ("id_emocion",     models.AutoField(primary_key=True, serialize=False)),
                ("nombre_emocion", models.CharField(max_length=50)),
            ],
            options={
                "db_table": "emocion",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="TipoRecurso",
            fields=[
                ("id_tipo_recurso", models.AutoField(primary_key=True, serialize=False)),
                ("nombre_recurso",  models.CharField(max_length=100)),
            ],
            options={
                "db_table": "tipo_recurso",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="EvaluacionInicial",
            fields=[
                ("id_eval", models.AutoField(primary_key=True, serialize=False)),
                ("edad",              models.IntegerField(null=True, blank=True)),
                ("genero",            models.CharField(max_length=20,  null=True, blank=True)),
                ("estado_relacion",   models.CharField(max_length=50,  null=True, blank=True)),
                ("situacion_trabajo", models.CharField(max_length=100, null=True, blank=True)),
                ("hr_sueno",         models.FloatField(null=True, blank=True)),
                ("hr_trabajo",       models.FloatField(null=True, blank=True)),
                ("hr_pantalla",      models.FloatField(null=True, blank=True)),
                ("hr_act_fis",       models.FloatField(null=True, blank=True)),
                ("estres_laboral",       models.IntegerField(null=True, blank=True)),
                ("estres_academico",     models.IntegerField(null=True, blank=True)),
                ("estres_financ",        models.IntegerField(null=True, blank=True)),
                ("satisfaccion_laboral", models.IntegerField(null=True, blank=True)),
                ("uso_sustancias",       models.TextField(null=True, blank=True)),
                ("dificultad_concentra", models.TextField(null=True, blank=True,
                    db_column="dificultad_concentra")),
                ("cambio_emocional",   models.TextField(null=True, blank=True)),
                ("diagnostico_previo", models.TextField(null=True, blank=True)),
                ("tratamiento_previo", models.TextField(null=True, blank=True)),
                ("apoyo_percibido",    models.TextField(null=True, blank=True)),
                ("historial_panico",   models.BooleanField(null=True, blank=True)),
                ("historial_familiar", models.BooleanField(null=True, blank=True)),
                ("id_usuario", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    db_column="id_usuario",
                    to="core.usuario",
                    related_name="evaluaciones_iniciales",
                    db_constraint=False)),
            ],
            options={
                "db_table": "evaluacion_inicial",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="RecursoApoyo",
            fields=[
                ("id_recurso", models.AutoField(primary_key=True, serialize=False)),
                ("titulo",      models.CharField(max_length=200)),
                ("informacion", models.TextField(null=True, blank=True)),
                ("imagen",      models.TextField(null=True, blank=True)),
                ("id_tipo_recurso", models.ForeignKey(
                    on_delete=models.deletion.RESTRICT,
                    db_column="id_tipo_recurso",
                    to="core.tiporecurso",
                    related_name="recursos",
                    db_constraint=False)),
            ],
            options={
                "db_table": "recurso_apoyo",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="RegistroEmocional",
            fields=[
                ("id_registro", models.AutoField(primary_key=True, serialize=False)),
                ("fecha_registro", models.DateTimeField(auto_now_add=True)),
                ("nivel_riesgo",   models.CharField(max_length=50, null=True, blank=True)),
                ("hr_sueno_dia",   models.FloatField(null=True, blank=True)),
                ("hr_trabajo_dia", models.FloatField(null=True, blank=True)),
                ("hr_pantalla_dia",models.FloatField(null=True, blank=True)),
                ("hr_act_fis_dia", models.FloatField(null=True, blank=True)),
                ("estres_laboral_dia",   models.IntegerField(null=True, blank=True)),
                ("estres_academico_dia", models.IntegerField(null=True, blank=True)),
                ("estres_financ_dia",    models.IntegerField(null=True, blank=True)),
                ("apoyo_percibido_dia",  models.TextField(null=True, blank=True)),
                ("autocuidado",          models.TextField(null=True, blank=True)),
                ("animo",                models.TextField(null=True, blank=True)),
                ("id_usuario", models.ForeignKey(
                    on_delete=models.deletion.RESTRICT,
                    db_column="id_usuario",
                    to="core.usuario",
                    related_name="registros_emocionales",
                    db_constraint=False)),
                ("id_emocion", models.ForeignKey(
                    on_delete=models.deletion.RESTRICT,
                    db_column="id_emocion",
                    to="core.emocion",
                    related_name="registros",
                    db_constraint=False)),
            ],
            options={
                "db_table": "registro_emocional",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="PresentacionRecurso",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("fecha_presentacion", models.DateTimeField(auto_now_add=True)),
                ("id_usuario", models.ForeignKey(
                    on_delete=models.deletion.RESTRICT,
                    db_column="id_usuario",
                    to="core.usuario",
                    related_name="presentaciones",
                    db_constraint=False)),
                ("id_recurso", models.ForeignKey(
                    on_delete=models.deletion.RESTRICT,
                    db_column="id_recurso",
                    to="core.recursoapoyo",
                    related_name="presentaciones",
                    db_constraint=False)),
            ],
            options={
                "db_table": "presentacion_recurso",
                "managed": False,
            },
        ),
    ]
