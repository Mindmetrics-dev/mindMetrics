"""
core/management/commands/create_domain_tables.py
================================================
Ejecuta 02_create_tables.sql sobre la base de datos activa.

USO
────
    python manage.py create_domain_tables
    python manage.py create_domain_tables --sql-path /ruta/alternativa.sql
    python manage.py create_domain_tables --check   # solo verifica existencia

CUÁNDO USARLO
──────────────
    1. Primera puesta en marcha SIN Docker (desarrollo local).
    2. En pipelines CI/CD donde el volumen de Postgres ya existe
       pero el init.sql no se ejecutó (Docker no re-ejecuta init
       si el volumen existe).
    3. Para verificar que todas las tablas están creadas.

IDEMPOTENCIA
─────────────
    El SQL usa CREATE TABLE IF NOT EXISTS → siempre es seguro re-ejecutar.
"""

import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

# Ruta por defecto relativa a la raíz del proyecto (MindMetrics/)
DEFAULT_SQL = Path(__file__).resolve().parents[4] / 'postgreSQL' / '02_create_tables.sql'

DOMAIN_TABLES = [
    'usuario',
    'emocion',
    'tipo_recurso',
    'evaluacion_inicial',
    'registro_emocional',
    'recurso_apoyo',
    'presentacion_recurso',
]


class Command(BaseCommand):
    help = 'Crea las tablas de dominio 3NF ejecutando 02_create_tables.sql.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sql-path', type=str, default=str(DEFAULT_SQL), dest='sql_path',
            help=f'Ruta al archivo SQL (default: {DEFAULT_SQL})',
        )
        parser.add_argument(
            '--check', action='store_true', default=False,
            help='Solo verifica existencia de tablas sin ejecutar SQL.',
        )

    def handle(self, *args, **options):
        sql_path = options['sql_path']
        check_only = options['check']

        if check_only:
            self._check_tables()
            return

        # ── Verificar que el SQL existe ───────────────────────────────────────
        if not os.path.isfile(sql_path):
            raise CommandError(
                f'Archivo SQL no encontrado: {sql_path}\n'
                f'Usa --sql-path para especificar la ruta correcta.'
            )

        # ── Leer el SQL ───────────────────────────────────────────────────────
        with open(sql_path, encoding='utf-8') as fh:
            sql_content = fh.read()

        self.stdout.write(f'Ejecutando: {sql_path}')

        # ── Ejecutar dentro de una transacción ────────────────────────────────
        # execute() acepta scripts multi-statement en psycopg2 cuando se
        # pasan como un solo string.
        try:
            with connection.cursor() as cur:
                cur.execute(sql_content)
            self.stdout.write(self.style.SUCCESS('✔ SQL ejecutado correctamente.'))
        except Exception as exc:
            raise CommandError(f'Error ejecutando SQL: {exc}')

        # ── Verificar resultado ───────────────────────────────────────────────
        self._check_tables()

    def _check_tables(self):
        """Verifica que todas las tablas de dominio existen en el schema public."""
        self.stdout.write('\nVerificando tablas de dominio:')
        all_ok = True
        with connection.cursor() as cur:
            for table in DOMAIN_TABLES:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name   = %s
                    )
                    """,
                    [table],
                )
                exists = cur.fetchone()[0]
                status = self.style.SUCCESS('✔') if exists else self.style.ERROR('✘')
                self.stdout.write(f'  {status}  {table}')
                if not exists:
                    all_ok = False

        if all_ok:
            self.stdout.write(self.style.SUCCESS(
                '\n✔ Todas las tablas de dominio están presentes.'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                '\n✘ Faltan tablas. Ejecuta: python manage.py create_domain_tables'
            ))
