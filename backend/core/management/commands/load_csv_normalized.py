"""
ETL Command: load_csv_normalized.py
Proyecto:    MindMetrics
Version:     1.2.0 - campos reales del modelo aplicados

Tablas que puebla (orden FK-safe):
    1. usuario
    2. evaluacion_inicial (FK -> usuario.id_usuario)

Campos reales de EvaluacionInicial (extraidos del FieldError de Django):
    id_eval, id_usuario(FK), edad, genero, estado_relacion,
    situacion_trabajo, hr_sueno, hr_trabajo, hr_act_fis, hr_pantalla,
    estres_laboral, estres_financ, estres_academico, apoyo_percibido,
    satisfaccion_laboral, dificultad_concentra, cambio_emocional,
    historial_familiar, diagnostico_previo, tratamiento_previo,
    historial_panico, uso_sustancias

AJUSTE REQUERIDO antes de ejecutar:
    1. Import: cambia 'core.models' por el modulo real de tus modelos.
    2. CSV_COL_USUARIO: verifica que las claves coincidan con cabeceras del CSV.
    3. CSV_COL_EVAL: idem para evaluacion_inicial.
    4. CAMPOS_BOOLEANOS_EVAL: lista los campos que son BOOLEAN en tu BD.
       Si son VARCHAR (ej: "Si"/"No"), vacialo: set()
    5. SEQUENCE_TABLES: ajusta con los nombres reales de tus tablas PostgreSQL.

Uso:
    python manage.py load_csv_normalized Dataset.csv
    python manage.py load_csv_normalized Dataset.csv --dry-run
    python manage.py load_csv_normalized Dataset.csv --batch-size 500
    python manage.py load_csv_normalized Dataset.csv --audit-dir ./auditorias
"""

import csv
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

# ---------------------------------------------------------------------------
# AJUSTA 'core' al nombre real de tu app Django donde viven los modelos.
# ---------------------------------------------------------------------------
from core.models import EvaluacionInicial, Usuario


logger = logging.getLogger("mindmetrics.etl")


# =============================================================================
# SECCION 1 - MAPEO COLUMNAS CSV -> CAMPOS DEL MODELO
# Clave  = nombre exacto de la columna en Dataset.csv
# Valor  = nombre del campo en el modelo Django
# Si tu CSV usa nombres identicos al modelo, clave == valor.
# =============================================================================

CSV_COL_USUARIO: Dict[str, str] = {
    "id_usuario": "id_usuario",   # PK INT
    "nombre":     "nickname",       # VARCHAR NOT NULL
    "password": "password",     # VARCHAR -- elimina si no existe en tu modelo
    "email":      "email",        # VARCHAR UNIQUE -- elimina si no existe
}

CSV_COL_EVAL: Dict[str, str] = {
    "id_eval":              "id_eval",
    "id_usuario":           "id_usuario_id",       # FK raw int
    "edad":                 "edad",
    "genero":               "genero",
    "estado_relacion":      "estado_relacion",
    "situacion_trabajo":    "situacion_trabajo",
    "hr_sueno":             "hr_sueno",
    "hr_trabajo":           "hr_trabajo",
    "hr_act_fis":           "hr_act_fis",
    "hr_pantalla":          "hr_pantalla",
    "estres_laboral":       "estres_laboral",
    "estres_financ":        "estres_financ",
    "estres_academico":     "estres_academico",
    "apoyo_percibido":      "apoyo_percibido",
    "satisfaccion_laboral": "satisfaccion_laboral",
    "dificultad_concentra": "dificultad_concentra",
    "cambio_emocional":     "cambio_emocional",
    "historial_familiar":   "historial_familiar",
    "diagnostico_previo":   "diagnostico_previo",
    "tratamiento_previo":   "tratamiento_previo",
    "historial_panico":     "historial_panico",
    "uso_sustancias":       "uso_sustancias",
}


# =============================================================================
# SECCION 2 - CONSTANTES DE VALIDACION
# =============================================================================

ESCALA_MIN, ESCALA_MAX = 0, 10      # escalas psicologicas
HORAS_MIN,  HORAS_MAX  = 0, 168      # horas diarias
EDAD_MIN,   EDAD_MAX   = 0, 120

# Campos de EvaluacionInicial que son BOOLEAN en PostgreSQL.
# Si alguno es VARCHAR (ej: guarda "Si"/"No"), retiralo de este set.
CAMPOS_BOOLEANOS_EVAL: Set[str] = {
    "historial_familiar",
    "diagnostico_previo",
    "tratamiento_previo",
    "historial_panico",
    "uso_sustancias",
}

BOOL_TRUE:  Set[str] = {"1", "true", "si", "yes", "t", "verdadero"}
BOOL_FALSE: Set[str] = {"0", "false", "no",  "f",  "falso"}

DATE_FORMATS: List[str] = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

# Tablas PostgreSQL para reset de secuencias SERIAL.
# Django genera el nombre como: <app>_<modeloenminusculas>
# Verifica con: \dt en psql, o python manage.py inspectdb
SEQUENCE_TABLES: List[Tuple[str, str]] = [
    ("usuario",           "id_usuario"),
    ("evaluacion_inicial", "id_eval"),
]


# =============================================================================
# SECCION 3 - HELPERS DE PARSEO Y VALIDACION
# =============================================================================

class ValidationError(Exception):
    """Error de validacion con contexto completo de fila y columna."""
    def __init__(self, row_num: int, column: str, value: Any, reason: str):
        self.row_num = row_num
        self.column  = column
        self.value   = value
        self.reason  = reason
        super().__init__(
            "Fila {} | col='{}' | val='{}' -> {}".format(row_num, column, value, reason)
        )


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def parse_int(row_num, column, raw, *, nullable=False, min_val=None, max_val=None):
    cleaned = _clean(raw)
    if not cleaned:
        if nullable:
            return None
        raise ValidationError(row_num, column, raw, "entero requerido (no nulo)")
    try:
        result = int(float(cleaned))   # tolera "3.0"
    except ValueError:
        raise ValidationError(row_num, column, raw, "no es un entero valido")
    if min_val is not None and result < min_val:
        raise ValidationError(row_num, column, raw,
                               "valor {} < minimo {}".format(result, min_val))
    if max_val is not None and result > max_val:
        raise ValidationError(row_num, column, raw,
                               "valor {} > maximo {}".format(result, max_val))
    return result


def parse_decimal(row_num, column, raw, *, nullable=False, min_val=None, max_val=None):
    cleaned = _clean(raw)
    if not cleaned:
        if nullable:
            return None
        raise ValidationError(row_num, column, raw, "decimal requerido (no nulo)")
    try:
        result = Decimal(cleaned)
    except InvalidOperation:
        raise ValidationError(row_num, column, raw, "no es un decimal valido")
    if min_val is not None and result < Decimal(str(min_val)):
        raise ValidationError(row_num, column, raw,
                               "valor {} < minimo {}".format(result, min_val))
    if max_val is not None and result > Decimal(str(max_val)):
        raise ValidationError(row_num, column, raw,
                               "valor {} > maximo {}".format(result, max_val))
    return result


def parse_bool(row_num, column, raw, *, nullable=False):
    cleaned = _clean(raw).lower()
    if not cleaned:
        if nullable:
            return None
        raise ValidationError(row_num, column, raw, "booleano requerido")
    if cleaned in BOOL_TRUE:
        return True
    if cleaned in BOOL_FALSE:
        return False
    raise ValidationError(
        row_num, column, raw,
        "valor no reconocido. Acepta: {}".format(BOOL_TRUE | BOOL_FALSE)
    )


def parse_str(row_num, column, raw, *, nullable=False, max_length=None, choices=None):
    cleaned = _clean(raw)
    if not cleaned:
        if nullable:
            return None
        raise ValidationError(row_num, column, raw, "texto requerido (no nulo)")
    if max_length is not None and len(cleaned) > max_length:
        raise ValidationError(row_num, column, raw,
                               "longitud {} > maximo {}".format(len(cleaned), max_length))
    if choices is not None and cleaned not in choices:
        raise ValidationError(row_num, column, raw,
                               "'{}' no esta en {}".format(cleaned, sorted(choices)))
    return cleaned


# =============================================================================
# SECCION 4 - AUDITORIA CSV
# =============================================================================

@dataclass
class AuditRecord:
    fila:    int
    entidad: str
    columna: str
    valor:   Any
    motivo:  str
    accion:  str


class AuditReporter:
    """Acumula errores del ETL y escribe un CSV de auditoria al finalizar."""

    FIELDNAMES = ["fila", "entidad", "columna", "valor", "motivo", "accion"]

    def __init__(self, audit_dir: str):
        self._records: List[AuditRecord] = []
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def add_validation_error(self, err: ValidationError, entidad: str) -> None:
        self._add(AuditRecord(fila=err.row_num, entidad=entidad,
                              columna=err.column, valor=err.value,
                              motivo=err.reason, accion="OMITIDA"))

    def add_duplicate(self, row_num, entidad, key_col, key_val) -> None:
        self._add(AuditRecord(fila=row_num, entidad=entidad,
                              columna=key_col, valor=key_val,
                              motivo="Duplicado (existe en DB o en el CSV)",
                              accion="DUPLICADA"))

    def add_fk_missing(self, row_num, entidad, fk_col, fk_val, ref_table) -> None:
        self._add(AuditRecord(fila=row_num, entidad=entidad,
                              columna=fk_col, valor=fk_val,
                              motivo="FK inexistente en '{}'".format(ref_table),
                              accion="OMITIDA"))

    def _add(self, r: AuditRecord) -> None:
        self._records.append(r)
        logger.warning("[AUDIT] fila=%d | %s.%s=%r | %s -> %s",
                       r.fila, r.entidad, r.columna, r.valor, r.motivo, r.accion)

    def write_report(self, timestamp: str) -> Path:
        path = self.audit_dir / "etl_audit_{}.csv".format(timestamp)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            w.writeheader()
            for r in self._records:
                w.writerow({"fila": r.fila, "entidad": r.entidad,
                             "columna": r.columna, "valor": r.valor,
                             "motivo": r.motivo, "accion": r.accion})
        return path

    @property
    def total_errors(self) -> int:
        return len(self._records)


# =============================================================================
# SECCION 5 - CONTEXTO ETL (precarga FK en memoria, elimina N+1 queries)
# =============================================================================

@dataclass
class ETLContext:
    existing_usuario_ids: Set[int] = field(default_factory=set)
    existing_eval_ids:    Set[int] = field(default_factory=set)
    existing_emails:      Set[str] = field(default_factory=set)
    inserted_usuario_ids: Set[int] = field(default_factory=set)
    reporter: Optional[AuditReporter] = None

    def all_valid_usuario_ids(self) -> Set[int]:
        """PKs de usuario validos como FK: DB + insertados en esta corrida."""
        return self.existing_usuario_ids | self.inserted_usuario_ids


def build_context(reporter: AuditReporter) -> ETLContext:
    """
    Precarga TODOS los PKs relevantes en 3 queries fijas.
    Usa los campos reales del modelo: 'id_usuario' y 'id_eval'.
    """
    logger.info("Precargando contexto FK desde la base de datos...")
    ctx = ETLContext(reporter=reporter)

    ctx.existing_usuario_ids = set(
        Usuario.objects.values_list("id_usuario", flat=True)
    )
    # CORREGIDO: PK real del modelo es 'id_eval', no 'id_evaluacion'
    ctx.existing_eval_ids = set(
        EvaluacionInicial.objects.values_list("id_eval", flat=True)
    )
    try:
        ctx.existing_emails = set(
            Usuario.objects.values_list("email", flat=True)
        )
    except Exception:
        logger.warning("Usuario no tiene campo 'email'. "
                       "Deduplicacion por email desactivada.")
        ctx.existing_emails = set()

    logger.info("Contexto: %d usuarios, %d evaluaciones en DB.",
                len(ctx.existing_usuario_ids), len(ctx.existing_eval_ids))
    return ctx


# =============================================================================
# SECCION 6 - EXTRACTORES POR ENTIDAD
# =============================================================================

def extract_usuarios(rows: List[Dict[str, str]], ctx: ETLContext):
    """
    Extrae y valida registros de Usuario desde el CSV.
    Deduplicacion por: id_usuario (PK) y email (UNIQUE si existe).
    """
    instances:   List[Usuario] = []
    seen_pks:    Set[int]      = set()
    seen_emails: Set[str]      = set()
    errors = 0

    for i, row in enumerate(rows, start=2):   # fila 1 = cabecera
        rn = i
        try:
            pk = parse_int(rn, "id_usuario", row.get("id_usuario", ""))

            nombre   = parse_str(rn, "nombre",   row.get("nombre",   ""),
                                 nullable=False, max_length=150)
            
            email    = parse_str(rn, "email",    row.get("email", ""),
                                 nullable=True, max_length=255)

        except ValidationError as exc:
            ctx.reporter.add_validation_error(exc, "usuario")
            errors += 1
            continue

        if pk in ctx.existing_usuario_ids or pk in seen_pks:
            ctx.reporter.add_duplicate(rn, "usuario", "id_usuario", pk)
            errors += 1
            continue

        if email and (email in ctx.existing_emails or email in seen_emails):
            ctx.reporter.add_duplicate(rn, "usuario", "email", email)
            errors += 1
            continue

        seen_pks.add(pk)
        if email:
            seen_emails.add(email)
        ctx.inserted_usuario_ids.add(pk)

        # Construye kwargs dinamicamente para no fallar si el modelo
        # no tiene 'apellido' o 'email'
        kwargs: Dict[str, Any] = {"id_usuario": pk, "nickname": nombre}
        
        if email is None or email == "":
            email = f"user_{pk}@placeholder.local"
        kwargs = {"id_usuario": pk, "nickname": nombre, "email": email}

        instances.append(Usuario(**kwargs))

    return instances, errors


def extract_evaluaciones(rows: List[Dict[str, str]], ctx: ETLContext):
    """
    Extrae y valida registros de EvaluacionInicial.

    Usa los 22 campos reales detectados del modelo Django.
    PK correcto: id_eval (no id_evaluacion).
    FK: id_usuario_id (sintaxis Django para asignar FK por valor entero).

    Validaciones:
      - Escalas [ESCALA_MIN, ESCALA_MAX]
      - Horas [HORAS_MIN, HORAS_MAX]
      - Campos en CAMPOS_BOOLEANOS_EVAL -> parse_bool
      - Campos fuera de ese set -> parse_str (nullable)
    """
    instances: List[EvaluacionInicial] = []
    seen_pks:  Set[int]                = set()
    errors = 0

    valid_usuario_ids = ctx.all_valid_usuario_ids()

    for i, row in enumerate(rows, start=2):
        rn = i
        try:
            pk         = parse_int(rn, "id_eval",    row.get("id_eval",    ""))
            usuario_id = parse_int(rn, "id_usuario", row.get("id_usuario", ""))
            edad       = parse_int(rn, "edad",        row.get("edad",       ""),
                                   nullable=True,
                                   min_val=EDAD_MIN, max_val=EDAD_MAX)
            genero          = parse_str(rn, "genero",
                                        row.get("genero", ""), nullable=True, max_length=50)
            estado_relacion = parse_str(rn, "estado_relacion",
                                        row.get("estado_relacion", ""), nullable=True, max_length=100)
            situacion_trabajo = parse_str(rn, "situacion_trabajo",
                                          row.get("situacion_trabajo", ""), nullable=True, max_length=100)

            hr_sueno    = parse_decimal(rn, "hr_sueno",   row.get("hr_sueno",   ""),
                                        nullable=True, min_val=HORAS_MIN, max_val=HORAS_MAX)
            hr_trabajo  = parse_decimal(rn, "hr_trabajo", row.get("hr_trabajo", ""),
                                        nullable=True, min_val=HORAS_MIN, max_val=HORAS_MAX)
            hr_act_fis  = parse_decimal(rn, "hr_act_fis", row.get("hr_act_fis", ""),
                                        nullable=True, min_val=HORAS_MIN, max_val=HORAS_MAX)
            hr_pantalla = parse_decimal(rn, "hr_pantalla", row.get("hr_pantalla", ""),
                                        nullable=True, min_val=HORAS_MIN, max_val=HORAS_MAX)

            estres_laboral       = parse_int(rn, "estres_laboral",
                                             row.get("estres_laboral", ""), nullable=True,
                                             min_val=ESCALA_MIN, max_val=ESCALA_MAX)
            estres_financ        = parse_int(rn, "estres_financ",
                                             row.get("estres_financ", ""), nullable=True,
                                             min_val=ESCALA_MIN, max_val=ESCALA_MAX)
            estres_academico     = parse_int(rn, "estres_academico",
                                             row.get("estres_academico", ""), nullable=True,
                                             min_val=ESCALA_MIN, max_val=ESCALA_MAX)
            apoyo_percibido      = parse_int(rn, "apoyo_percibido",
                                             row.get("apoyo_percibido", ""), nullable=True,
                                             min_val=ESCALA_MIN, max_val=ESCALA_MAX)
            satisfaccion_laboral = parse_int(rn, "satisfaccion_laboral",
                                             row.get("satisfaccion_laboral", ""), nullable=True,
                                             min_val=ESCALA_MIN, max_val=ESCALA_MAX)
            dificultad_concentra = parse_int(rn, "dificultad_concentra",
                                             row.get("dificultad_concentra", ""), nullable=True,
                                             min_val=ESCALA_MIN, max_val=ESCALA_MAX)
            cambio_emocional     = parse_int(rn, "cambio_emocional",
                                             row.get("cambio_emocional", ""), nullable=True,
                                             min_val=ESCALA_MIN, max_val=ESCALA_MAX)

            # Antecedentes: BOOLEAN o VARCHAR segun CAMPOS_BOOLEANOS_EVAL
            def _ant(col):
                raw = row.get(col, "")
                if col in CAMPOS_BOOLEANOS_EVAL:
                    return parse_bool(rn, col, raw, nullable=True)
                return parse_str(rn, col, raw, nullable=True, max_length=50)

            historial_familiar = _ant("historial_familiar")
            diagnostico_previo = _ant("diagnostico_previo")
            tratamiento_previo = _ant("tratamiento_previo")
            historial_panico   = _ant("historial_panico")
            uso_sustancias     = _ant("uso_sustancias")

        except ValidationError as exc:
            ctx.reporter.add_validation_error(exc, "evaluacion_inicial")
            errors += 1
            continue

        # Validacion FK
        if usuario_id not in valid_usuario_ids:
            ctx.reporter.add_fk_missing(
                rn, "evaluacion_inicial", "id_usuario", usuario_id, "usuario"
            )
            errors += 1
            continue

        # Duplicado PK
        if pk in ctx.existing_eval_ids or pk in seen_pks:
            ctx.reporter.add_duplicate(rn, "evaluacion_inicial", "id_eval", pk)
            errors += 1
            continue

        seen_pks.add(pk)

        instances.append(EvaluacionInicial(
            id_eval=pk,
            id_usuario_id=usuario_id,
            edad=edad,
            genero=genero,
            estado_relacion=estado_relacion,
            situacion_trabajo=situacion_trabajo,
            hr_sueno=hr_sueno,
            hr_trabajo=hr_trabajo,
            hr_act_fis=hr_act_fis,
            hr_pantalla=hr_pantalla,
            estres_laboral=estres_laboral,
            estres_financ=estres_financ,
            estres_academico=estres_academico,
            apoyo_percibido=apoyo_percibido,
            satisfaccion_laboral=satisfaccion_laboral,
            dificultad_concentra=dificultad_concentra,
            cambio_emocional=cambio_emocional,
            historial_familiar=historial_familiar,
            diagnostico_previo=diagnostico_previo,
            tratamiento_previo=tratamiento_previo,
            historial_panico=historial_panico,
            uso_sustancias=uso_sustancias,
        ))

    return instances, errors


# =============================================================================
# SECCION 7 - LOADER GENERICO
# =============================================================================

def bulk_insert(model_class, instances, batch_size, entity_name, dry_run):
    if not instances:
        logger.info("[%s] Sin registros nuevos.", entity_name)
        return 0
    if dry_run:
        logger.info("[DRY-RUN][%s] Se insertarian %d registros.",
                    entity_name, len(instances))
        return len(instances)
    total = 0
    for start in range(0, len(instances), batch_size):
        batch = instances[start: start + batch_size]
        model_class.objects.bulk_create(batch, batch_size=batch_size)
        total += len(batch)
        logger.info("[%s] Lote %d-%d insertado (%d/%d).",
                    entity_name, start + 1, start + len(batch),
                    total, len(instances))
    return total


# =============================================================================
# SECCION 8 - RESET SECUENCIAS POSTGRESQL
# =============================================================================

def reset_postgres_sequences(dry_run: bool) -> None:
    """
    Sincroniza secuencias SERIAL/IDENTITY tras insertar PKs explicitos.
    setval(seq, MAX(pk)+1, false) -> el proximo nextval() retorna MAX+1.
    Idempotente y seguro de ejecutar en cualquier momento.
    """
    if dry_run:
        logger.info("[DRY-RUN] Omitiendo reset de secuencias.")
        return
    logger.info("Sincronizando secuencias SERIAL/IDENTITY en PostgreSQL...")
    with connection.cursor() as cursor:
        for table_name, pk_col in SEQUENCE_TABLES:
            sql = (
                "SELECT setval("
                "    pg_get_serial_sequence('{table}', '{col}'),"
                "    COALESCE(MAX(\"{col}\"), 0) + 1,"
                "    false"
                ") FROM \"{table}\";".format(table=table_name, col=pk_col)
            )
            try:
                cursor.execute(sql)
                new_val = cursor.fetchone()[0]
                logger.info("Secuencia OK: %s.%s -> next=%s",
                            table_name, pk_col, new_val)
            except Exception as exc:
                logger.warning("No se pudo sincronizar %s.%s: %s",
                               table_name, pk_col, exc)


# =============================================================================
# SECCION 9 - COMANDO DJANGO
# =============================================================================

class Command(BaseCommand):
    """
    ETL MindMetrics v1.2: puebla usuario + evaluacion_inicial desde Dataset.csv.

    python manage.py load_csv_normalized <ruta_csv>
                     [--dry-run] [--batch-size N]
                     [--audit-dir DIR] [--encoding utf-8] [--delimiter ,]
    """

    help = ("ETL MindMetrics v1.2: puebla 'usuario' y 'evaluacion_inicial' "
            "desde Dataset.csv con validacion robusta y auditoria CSV.")

    def add_arguments(self, parser):
        parser.add_argument("csv_path",    type=str)
        parser.add_argument("--dry-run",   action="store_true", default=False)
        parser.add_argument("--batch-size", type=int, default=1000)
        parser.add_argument("--audit-dir", type=str, default="./etl_auditorias")
        parser.add_argument("--encoding",  type=str, default="utf-8")
        parser.add_argument("--delimiter", type=str, default=",")

    def handle(self, *args, **options):
        csv_path   = options["csv_path"]
        dry_run    = options["dry_run"]
        batch_size = options["batch_size"]
        audit_dir  = options["audit_dir"]
        encoding   = options["encoding"]
        delimiter  = options["delimiter"]
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")

        self._configure_logging()
        logger.info("=" * 65)
        logger.info("ETL MindMetrics - load_csv_normalized v1.2.0")
        logger.info("CSV:        %s", csv_path)
        logger.info("Dry-run:    %s", dry_run)
        logger.info("Batch size: %d", batch_size)
        logger.info("=" * 65)

        if not os.path.isfile(csv_path):
            raise CommandError("Archivo CSV no encontrado: '{}'".format(csv_path))

        logger.info("Leyendo CSV...")
        rows = self._read_csv(csv_path, encoding=encoding, delimiter=delimiter)
        logger.info("Filas leidas: %d", len(rows))

        reporter = AuditReporter(audit_dir=audit_dir)
        ctx      = build_context(reporter=reporter)

        logger.info("Extrayendo y validando datos...")
        usuarios,     err_u = extract_usuarios(rows, ctx)
        evaluaciones, err_e = extract_evaluaciones(rows, ctx)
        total_errors = err_u + err_e

        logger.info("-" * 50)
        logger.info("EXTRACCION: usuario=%d validos/%d err | eval=%d validos/%d err",
                    len(usuarios), err_u, len(evaluaciones), err_e)
        logger.info("-" * 50)

        try:
            with transaction.atomic():
                n_u = bulk_insert(Usuario, usuarios,
                                  batch_size, "usuario", dry_run)
                n_e = bulk_insert(EvaluacionInicial, evaluaciones,
                                  batch_size, "evaluacion_inicial", dry_run)
        except Exception as exc:
            logger.critical("Error en carga. Rollback ejecutado: %s", exc)
            raise CommandError("ETL abortado: {}".format(exc)) from exc

        reset_postgres_sequences(dry_run=dry_run)

        report_path = reporter.write_report(timestamp)

        mode = "DRY-RUN" if dry_run else "PRODUCCION"
        logger.info("=" * 65)
        logger.info("ETL COMPLETADO [%s]", mode)
        logger.info("  Filas CSV leidas:        %d", len(rows))
        logger.info("  usuario insertados:      %d", n_u)
        logger.info("  evaluaciones insertadas: %d", n_e)
        logger.info("  Total insertados:        %d", n_u + n_e)
        logger.info("  Errores/omitidos:        %d", total_errors)
        logger.info("  Reporte auditoria:       %s", report_path)
        if total_errors > 0:
            logger.warning("  %d filas rechazadas. Revisa el reporte CSV.",
                           total_errors)
        logger.info("=" * 65)

    @staticmethod
    def _configure_logging():
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s][%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            logger.addHandler(handler)

    @staticmethod
    def _read_csv(csv_path, encoding="utf-8", delimiter=","):
        rows = []
        try:
            with open(csv_path, newline="", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                if reader.fieldnames is None:
                    raise CommandError("CSV vacio o sin cabeceras.")
                for row in reader:
                    rows.append({k.strip(): v for k, v in row.items()})
        except (OSError, UnicodeDecodeError) as exc:
            raise CommandError("Error leyendo CSV: {}".format(exc)) from exc
        return rows