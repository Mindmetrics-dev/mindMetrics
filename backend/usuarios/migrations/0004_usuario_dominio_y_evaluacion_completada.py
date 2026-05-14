"""
Migracion: enlace CustomUser <-> core.Usuario y flag de onboarding.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0003_remove_first_last_name"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="usuario_dominio",
            field=models.OneToOneField(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="auth_user",
                to="core.usuario",
                db_column="id_usuario_dominio",
                db_constraint=False,
                help_text="FK 1-a-1 a la tabla de dominio usuario.",
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="evaluacion_completada",
            field=models.BooleanField(
                default=False,
                help_text="True cuando el usuario completo su evaluacion_inicial.",
            ),
        ),
    ]
