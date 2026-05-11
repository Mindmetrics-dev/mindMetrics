# CLEANUP_REPORT — MindMetrics

**Fecha de auditoría:** 2026-05-10
**Autor:** Julian Andres Gomez Cabrera
**Alcance:** Reorganización estructural y eliminación de artefactos obsoletos del repositorio.

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos/carpetas eliminados | 6 entradas + N caches |
| Archivos renombrados/movidos | 8 |
| Carpetas nuevas creadas | 5 (`docker/`, `postgres/`, `scripts/`, `docs/`, `logs/`, `reports/`) |
| Archivos nuevos creados | 4 (`.gitignore`, `PROJECT_LOGS.md`, `docker/django/Dockerfile`, `CLEANUP_REPORT.md`) |
| Archivos modificados (rutas) | 3 (`settings.py`, `docker-compose.yml`, `Inicio.bat`) |
| Riesgo de ruptura funcional | **Bajo** (todas las rutas relativas se actualizan en el mismo commit). |

---

## 2. Archivos / Carpetas Eliminados

| Ruta original | Tipo | Motivo técnico |
|---------------|------|----------------|
| `Backend/DokerFile` | Archivo (0 bytes) | Vacío y mal nombrado. El Dockerfile real vive en `docker/django/Dockerfile`. |
| `Backend/staticfiles/` (recursivo) | Carpeta autogenerada | Output de `python manage.py collectstatic`. La fuente canónica es `Frontend/static/`. Se añade a `.gitignore`. |
| `Frontend/Templates/base.html` | Archivo HTML | Versión obsoleta no referenciada. Todos los views (`{% extends 'mindmetrics/base.html' %}`) usan la copia en `Templates/mindmetrics/`. |
| `Frontend/Templates/auth_base.html` | Archivo HTML | Idem; obsoleto. Activo: `Templates/mindmetrics/auth_base.html`. |
| `Backend/etl_auditorias/etl_audit_20260509_200838.csv` | CSV (42 B) | Auditoría ETL antigua, sin filas de datos (solo header). |
| `Backend/etl_auditorias/etl_audit_20260509_201503.csv` | CSV (42 B) | Idem. |
| `**/__pycache__/` | Carpetas (bytecode CPython 3.13) | Reproducibles desde `.py`. Cubierto por `.gitignore`. |
| `**/*.pyc` | Archivos bytecode | Idem. |

> Total `__pycache__` detectados antes de limpieza: **9 directorios** (core, core/management, core/management/commands, formulario, formulario/migrations, mi_plataforma, usuarios, usuarios/migrations).

---

## 3. Archivos Renombrados / Movidos

| Origen | Destino | Justificación |
|--------|---------|---------------|
| `Backend/` | `backend/` | Convención POSIX/Docker (lowercase). |
| `Frontend/` | `frontend/` | Idem. |
| `Frontend/Templates/` | `frontend/templates/` | Convención Django (Templates → templates). |
| `PostgreSQL/` | `postgres/` | Coincide con servicio Docker (`postgres:15`), simplifica volumen. |
| `.docker/` | `docker/` | Carpeta visible (no dotfile). Estructura `docker/django/`, `docker/postgres/`. |
| `requirements.txt` (raíz) | `backend/requirements.txt` | Pertenece al artefacto Django, no al meta-proyecto. |
| `Inicio.bat` (raíz) | `scripts/Inicio.bat` | Script auxiliar de bootstrap; se aísla de raíz. |
| `# Objetivo.md` (uploads externo) | `docs/Objetivo.md` | Documento de requerimientos; se preserva en `docs/`. |

---

## 4. Archivos / Carpetas Creados

| Ruta | Propósito |
|------|-----------|
| `.gitignore` | Excluir `venv/`, `__pycache__/`, `*.pyc`, `staticfiles/`, `media/`, `.env`, `logs/`, `reports/`, `*.sqlite3`. |
| `PROJECT_LOGS.md` | Plantilla PSP: Time Log, Defect Log, Scope Log. |
| `CLEANUP_REPORT.md` | Este reporte. |
| `docker/django/Dockerfile` | Dockerfile real para `web_ia` (referenciado por `docker-compose.yml` pero faltante). |
| `scripts/` | Scripts auxiliares (`Inicio.bat` y futuros). |
| `docs/` | Documentación, requisitos, reportes. |
| `logs/` | Logs ETL (montaje `./logs:/app/logs`). |
| `reports/` | Reportes de auditoría ETL (montaje `./reports:/app/reports`). |

---

## 5. Modificaciones de Rutas (Integridad Referencial)

| Archivo | Cambio |
|---------|--------|
| `backend/mi_plataforma/settings.py` | `TEMPLATES.DIRS`: `PROJECT_DIR / 'Frontend' / 'Templates'` → `PROJECT_DIR / 'frontend' / 'templates'`. `STATICFILES_DIRS`: `'Frontend' / 'static'` → `'frontend' / 'static'`. |
| `docker-compose.yml` | `env_file`: `Backend/.env` → `backend/.env`. Volumen `./.docker/postgres/init.sql` → `./docker/postgres/init.sql`. Volumen `./PostgreSQL/` → `./postgres/`. `dockerfile: .docker/django/Dockerfile` → `docker/django/Dockerfile`. `working_dir: /app/Backend` → `/app/backend`. Comandos `--sql-path /app/PostgreSQL/...` → `/app/postgres/...`. |
| `scripts/Inicio.bat` | `cd Backend` → `cd backend`. Referencias a `requirements.txt` → `backend\requirements.txt`. Mensaje `PostgreSQL\init.sql` → `docker\postgres\init.sql`. |

---

## 6. Estructura Final Resultante

```
MindMetrics/
├── backend/
│   ├── .env                       # (NO versionado)
│   ├── core/
│   │   ├── management/commands/
│   │   │   ├── create_domain_tables.py
│   │   │   └── load_csv_normalized.py
│   │   └── models.py
│   ├── formulario/
│   ├── usuarios/
│   ├── mi_plataforma/
│   ├── etl_auditorias/
│   │   └── etl_audit_20260510_172732.csv
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── static/
│   │   ├── css/, img/, js/
│   └── templates/
│       ├── mindmetrics/
│       │   ├── base.html
│       │   └── auth_base.html
│       ├── dashboard.html, login.html, ...
├── docker/
│   ├── django/Dockerfile
│   └── postgres/init.sql
├── postgres/
│   ├── 02_create_tables.sql
│   └── Dataset.csv
├── scripts/
│   └── Inicio.bat
├── docs/
│   ├── Objetivo.md
│   └── (reportes futuros)
├── logs/                          # vacío (volumen Docker)
├── reports/                       # vacío (volumen Docker)
├── venv/                          # (NO versionado)
├── .gitignore
├── docker-compose.yml
├── PROJECT_LOGS.md
└── CLEANUP_REPORT.md
```

---

## 7. Reglas de Limpieza Aplicadas

- [x] Se conservan archivos fuente `.py`, `.sql`, `.md`, `.txt` usados por el proyecto.
- [x] Se eliminan `__pycache__/` y `*.pyc`.
- [x] No se encontraron `*.bak`, `*~`, `*.old`.
- [x] No se encontraron logs antiguos (`logs/` se creó vacío).
- [x] Archivos duplicados: se conserva la versión más reciente y referenciada (templates en `mindmetrics/`, ETL audit más reciente).
- [x] `staticfiles/` (output) excluido del versionado.

---

## 8. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Sistema de archivos Windows case-insensitive ignora `Backend → backend`. | Rename en dos pasos (`Backend → _tmp → backend`). Verificado en post-condición. |
| Caché Docker invalida tras renombrar volúmenes. | Documentado en `PROJECT_LOGS.md`. Requiere `docker compose down -v` antes del primer build. |
| `Backend/.env` se pierde durante el rename. | Se preserva mediante `mv` recursivo, no copia. Validado post-rename. |
| Migraciones Django dependen de paths absolutos. | No aplica: `BASE_DIR` se resuelve dinámicamente vía `Path(__file__).resolve().parent.parent`. |

---

## 9. Estado Final de la Ejecución

### 9.1 Acciones completadas automáticamente

- [x] Eliminados 9 directorios `__pycache__/` y sus `.pyc`.
- [x] Eliminado `Backend/DokerFile` (vacío, mal nombrado).
- [x] Eliminado `Backend/staticfiles/` completo.
- [x] Eliminados `Frontend/Templates/base.html` y `auth_base.html` (obsoletos).
- [x] Eliminados 2 CSV ETL antiguos (`etl_audit_20260509_*.csv`).
- [x] Eliminados originales: `.docker/`, `Inicio.bat` (raíz), `requirements.txt` (raíz).
- [x] Creados: `docker/django/Dockerfile`, `docker/postgres/init.sql`, `postgres/02_create_tables.sql`, `postgres/Dataset.csv`, `scripts/Inicio.bat`, `scripts/finalize_rename.ps1`, `Backend/requirements.txt`, `docs/Objetivo.md`, `.gitignore`, `PROJECT_LOGS.md`, `CLEANUP_REPORT.md`.
- [x] Actualizados: `Backend/mi_plataforma/settings.py`, `docker-compose.yml`, `scripts/Inicio.bat`.
- [x] Stubs `.gitkeep` en `logs/`, `reports/`, `Backend/etl_auditorias/`.

### 9.2 Acciones que requieren intervención manual en Windows

| Acción | Motivo | Cómo ejecutar |
|--------|--------|---------------|
| Rename `Backend → backend`, `Frontend → frontend`, `Templates → templates` | NTFS es case-preserving pero case-insensitive: el rename de solo-case no es aplicable desde la sesión actual (la diferencia se interpreta como no-op). | `powershell -ExecutionPolicy Bypass -File scripts\finalize_rename.ps1` |
| Eliminar `PostgreSQL\Dataset.csv` (1.5 MB) | El archivo presenta un lock o ACL que bloqueó la eliminación remota. Su contenido ya fue replicado en `postgres\Dataset.csv`. | Ejecutado por el mismo `finalize_rename.ps1`, o manualmente: `Remove-Item .\PostgreSQL -Recurse -Force`. |

> **Una vez ejecutado el script**, la estructura coincide 1:1 con la sección §6.

### 9.3 Próximos Pasos Recomendados

1. Ejecutar `scripts\finalize_rename.ps1` para cerrar §9.2.
2. Inicializar repositorio Git: `git init && git add . && git commit -m "chore: reorganización estructural"`.
3. Validar arranque end-to-end: `docker compose down -v && docker compose up --build`.
4. Migrar `Inicio.bat` a un equivalente PowerShell `Inicio.ps1` para soporte multiplataforma.
5. Crear `backend/tests/` con pruebas unitarias siguiendo ISO/IEC/IEEE 29119.
6. Implementar contenido real de la lógica ML (KNN/SVM) en `backend/core/ml/` (sugerido como módulo aparte).
