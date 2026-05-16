"""
recursos/views.py — MindMetrics
============================================================
Vistas funcionales del módulo `recursos` (patrón MVT).

Responsabilidades:
  1. `lista_recursos`    — Render del catálogo de recursos de apoyo.
                           Fuente primaria: tabla `recurso_apoyo` (ORM).
                           Fallback: catálogo estático de PDFs locales
                           cuando la tabla aún no está poblada.
  2. `descargar_recurso` — Sirve el PDF físico de backend/recursos/ vía
                           FileResponse y registra la traza en
                           `presentacion_recurso` (auditoría de uso).

Los nombres de URL (`recursos`, `descargar_recurso`) se conservan para
no romper los `{% url %}` de las plantillas existentes.
"""
from __future__ import annotations

import logging
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from .models import PresentacionRecurso, RecursoApoyo

logger = logging.getLogger(__name__)

# Directorio físico donde viven los PDF (backend/recursos/).
RECURSOS_DIR = Path(__file__).resolve().parent

# ─────────────────────────────────────────────────────────────────────────────
# Catálogo estático — fallback cuando la tabla `recurso_apoyo` está vacía.
# `archivo` debe coincidir con un PDF real de backend/recursos/.
# ─────────────────────────────────────────────────────────────────────────────
CATALOGO_ESTATICO: list[dict] = [
    {
        "titulo": "Termómetro de la Rabia",
        "descripcion": "Identifica la intensidad de tu enojo en una escala visual para aprender a regularlo.",
        "beneficio": "Autoconciencia emocional.",
        "archivo": "ejercicio1_termometro_rabia.pdf",
        "imagen": "img/Termometrorabia.png",
    },
    {
        "titulo": "Disparadores de la Rabia",
        "descripcion": "Reconoce las situaciones o pensamientos que activan tu enojo.",
        "beneficio": "Prevención de crisis.",
        "archivo": "ejercicio2_disparadores_rabia.pdf",
        "imagen": "img/Disparadoresderabia.png",
    },
    {
        "titulo": "Cera de Conflictos",
        "descripcion": "Técnica guiada para desescalar conflictos interpersonales.",
        "beneficio": "Resolución pacífica.",
        "archivo": "ejercicio3_cera_conflictos.pdf",
        "imagen": "img/Ceraconflictos.png",
    },
    {
        "titulo": "Hoja de Fortalezas",
        "descripcion": "Descubre y registra tus fortalezas personales para momentos difíciles.",
        "beneficio": "Refuerzo de autoestima.",
        "archivo": "ejercicio4_hoja_fortalezas.pdf",
        "imagen": "img/Hojafortaleza.png",
    },
    {
        "titulo": "Partes de Mí",
        "descripcion": "Explora las diferentes facetas de tu personalidad y cómo se relacionan.",
        "beneficio": "Autoconocimiento integral.",
        "archivo": "ejercicio5_partes_de_mi.pdf",
        "imagen": "img/Partesdemi.png",
    },
    {
        "titulo": "Autorretrato",
        "descripcion": "Ejercicio creativo para representar cómo te ves y cómo te sientes.",
        "beneficio": "Expresión emocional.",
        "archivo": "ejercicio6_autorretrato.pdf",
        "imagen": "img/Autoretrato.png",
    },
]

# Líneas de atención — dato de referencia institucional, no proviene de BD.
LINEAS_ATENCION: list[dict] = [
    {
        "nombre": "Línea 106",
        "telefono": "106",
        "descripcion": "Atención en salud mental en Cali",
        "horario": "24/7, gratuita desde fijos y celulares",
    },
    {
        "nombre": "Psicóloga Daniela Soto",
        "telefono": "+57 301 4646247",
        "descripcion": "Psicoterapia presencial y remota",
        "horario": "",
    },
    {
        "nombre": "Casa Matria",
        "telefono": "350 803 2031 (Diurno) / 311 612 0000 (24/7)",
        "descripcion": "Atención a mujeres — Violencia de género",
        "horario": "",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _catalogo_desde_bd() -> list[dict]:
    """
    Construye el catálogo a partir de la tabla `recurso_apoyo` (ORM).

    Devuelve [] si la tabla está vacía o si hay un error de acceso a BD,
    de modo que la vista pueda decidir el fallback estático.
    """
    try:
        recursos = (
            RecursoApoyo.objects
            .select_related("id_tipo_recurso")
            .order_by("titulo")
        )
        catalogo = []
        for r in recursos:
            catalogo.append({
                "id": r.id_recurso,
                "titulo": r.titulo,
                "descripcion": r.informacion or "",
                "beneficio": getattr(r.id_tipo_recurso, "nombre_recurso", ""),
                "url": f"/recursos/descargar/{r.id_recurso}/",
                "externo": False,
                "imagen": r.imagen or "",
            })
        return catalogo
    except Exception:  # tabla inexistente, BD caída, etc.
        logger.exception("No se pudo leer el catálogo desde `recurso_apoyo`.")
        return []


def _catalogo_estatico() -> list[dict]:
    """Adapta CATALOGO_ESTATICO al shape que consume la plantilla."""
    return [
        {
            "id": None,
            "titulo": item["titulo"],
            "descripcion": item["descripcion"],
            "beneficio": item["beneficio"],
            "url": f"/recursos/descargar/archivo/{item['archivo']}/",
            "externo": False,
            "imagen": item["imagen"],
        }
        for item in CATALOGO_ESTATICO
    ]


def _registrar_presentacion(request: HttpRequest, recurso: RecursoApoyo) -> None:
    """
    Inserta una fila en `presentacion_recurso` (traza usuario ↔ recurso).

    Defensivo: solo registra si el usuario web tiene `usuario_dominio`
    asociado. Un IntegrityError por PK compuesta duplicada se ignora
    (el recurso ya fue presentado hoy a ese usuario).
    """
    dominio = getattr(request.user, "usuario_dominio", None)
    if dominio is None:
        return
    try:
        PresentacionRecurso.objects.create(id_usuario=dominio, id_recurso=recurso)
    except IntegrityError:
        pass
    except Exception:
        logger.exception("Fallo al registrar presentación de recurso %s", recurso.pk)


# ─────────────────────────────────────────────────────────────────────────────
# Vistas
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url="login_step1")
def lista_recursos(request: HttpRequest) -> HttpResponse:
    """
    Catálogo de recursos de apoyo.

    Estrategia Database-First: intenta servir desde `recurso_apoyo`;
    si la tabla aún no tiene datos, cae al catálogo estático de PDFs.
    """
    catalogo = _catalogo_desde_bd()
    origen = "bd"
    if not catalogo:
        catalogo = _catalogo_estatico()
        origen = "estatico"

    contexto = {
        "active_section": "recursos",
        "recursos": catalogo,
        "lineas_atencion": LINEAS_ATENCION,
        "origen_catalogo": origen,
    }
    return render(request, "recursos.html", contexto)


@login_required(login_url="login_step1")
def descargar_recurso(request: HttpRequest, id_recurso: int) -> FileResponse:
    """
    Sirve el PDF asociado a un `RecursoApoyo` y registra la presentación.

    El campo `imagen`/`informacion` de RecursoApoyo no guarda la ruta del
    PDF de forma estandarizada en el preview actual, por lo que se asume
    la convención backend/recursos/<imagen|titulo>. Si no se halla el
    archivo, responde 404.
    """
    try:
        recurso = RecursoApoyo.objects.get(pk=id_recurso)
    except RecursoApoyo.DoesNotExist:
        raise Http404("Recurso no encontrado.")

    nombre_archivo = (recurso.imagen or "").strip()
    ruta = (RECURSOS_DIR / nombre_archivo).resolve()
    # Anti path-traversal: el archivo debe quedar dentro de RECURSOS_DIR.
    if RECURSOS_DIR not in ruta.parents or not ruta.is_file():
        raise Http404("Archivo del recurso no disponible.")

    _registrar_presentacion(request, recurso)
    return FileResponse(open(ruta, "rb"), content_type="application/pdf")


@login_required(login_url="login_step1")
def descargar_recurso_estatico(request: HttpRequest, nombre: str) -> FileResponse:
    """
    Sirve un PDF del catálogo estático por nombre de archivo.

    Usado mientras la tabla `recurso_apoyo` no esté poblada. Valida que
    `nombre` pertenezca al catálogo conocido (whitelist) para evitar
    lectura arbitraria de archivos.
    """
    permitidos = {item["archivo"] for item in CATALOGO_ESTATICO}
    if nombre not in permitidos:
        raise Http404("Recurso no reconocido.")

    ruta = (RECURSOS_DIR / nombre).resolve()
    if RECURSOS_DIR not in ruta.parents or not ruta.is_file():
        raise Http404("Archivo no disponible.")

    return FileResponse(open(ruta, "rb"), content_type="application/pdf")
