# PROJECT_LOGS — MindMetrics

> Registro disciplinado siguiendo lineamientos PSP (Personal Software Process) y alineado con ISO/IEC/IEEE 29119 (Testing) y ISO/IEC/IEEE 29148 (Requirements). Actualizar al cierre de cada sesión de trabajo.

**Proyecto:** MindMetrics — Plataforma de monitoreo conductual y riesgo psicológico (ML).
**Stack:** Python 3.13 · Django 4.2 · PostgreSQL 15 · Docker · scikit-learn (KNN/SVM).
**Owner:** Julian Andres Gomez Cabrera.
**Fecha de inicio del log:** 2026-05-10.

---

## 1. Registro de Tiempo — Time Log

> Cada sesión de trabajo se documenta con una entrada nueva. **Tiempo Neto = (Fin − Inicio) − Interrupciones**.

| Fecha | Fase | Actividad | Estado | Inicio | Fin | Interrupciones (min) | Tiempo Neto (min) | Comentarios |
|-------|------|-----------|--------|--------|-----|----------------------|-------------------|-------------|
| 10/05/2026 | Post-mortem | Auditoría estructural del repositorio + reorganización + creación de `CLEANUP_REPORT.md` y `PROJECT_LOGS.md` | Terminado | 22:00 | 23:30 | 0 | 90 | Renombrados `Backend→backend`, `Frontend→frontend`, `PostgreSQL→postgres`, `.docker→docker`. Eliminados artefactos obsoletos. Sin defectos inyectados. |
| 09/05/2026 | Código | Implementación de comandos ETL `create_domain_tables` y `load_csv_normalized` | Terminado | — | — | — | — | (Histórico inferido por timestamps de archivos. Completar con datos reales.) |
| 09/05/2026 | Diseño | `02_create_tables.sql` — DDL del esquema normalizado 3NF | Terminado | — | — | — | — | (Histórico inferido.) |
| DD/MM/AAAA | Planeación / Diseño / Código / Revisión / Pruebas / Post-mortem | _Descripción_ | Terminado / En progreso / Pendiente | HH:MM | HH:MM | 0 | 0 | _Hallazgos, distracciones, decisiones._ |

**Convenciones de fase:**

- **Planeación:** Estimación, descomposición de tareas, definición de Definition of Done.
- **Diseño:** UML, DDL, ER, arquitectura.
- **Código:** Implementación efectiva (`.py`, `.sql`, `.html`).
- **Revisión:** Code review (auto o pares).
- **Pruebas:** Unit, integration, system (ISO/IEC/IEEE 29119-2).
- **Post-mortem:** Análisis retrospectivo, refactorización, limpieza.

---

## 2. Registro de Defectos — Log de Calidad

> Cada defecto se numera secuencialmente. **Tipo** según códigos PSP (ver §4). Severidad: bajo / medio / alto / crítico.

### Defecto #001

- **Fecha Encontrado:** 10/05
- **Tipo de Defecto:** 100 (Env)
- **Fase Inyección:** Diseño (configuración Docker)
- **Fase Remoción:** Revisión
- **Severidad:** medio
- **Tiempo de Corrección:** 5 min
- **Descripción:** `docker-compose.yml` referenciaba `.docker/django/Dockerfile`, pero el archivo nunca fue creado. Se creó el Dockerfile correspondiente en `docker/django/Dockerfile`.
- **Estado:** corregido

### Defecto #002

- **Fecha Encontrado:** 10/05
- **Tipo de Defecto:** 20 (Sin)
- **Fase Inyección:** Código
- **Fase Remoción:** Revisión
- **Severidad:** bajo
- **Tiempo de Corrección:** 1 min
- **Descripción:** Archivo `Backend/DokerFile` (typo de "Dockerfile"), vacío. Eliminado.
- **Estado:** corregido

### Defecto #003

- **Fecha Encontrado:** 10/05
- **Tipo de Defecto:** 10 (Doc)
- **Fase Inyección:** Diseño
- **Fase Remoción:** Revisión
- **Severidad:** bajo
- **Tiempo de Corrección:** 2 min
- **Descripción:** Templates duplicados (`Frontend/Templates/base.html` y `Frontend/Templates/mindmetrics/base.html`). El primero no era referenciado por ningún view ni por `{% extends %}`. Eliminado.
- **Estado:** corregido

### Plantilla — Defecto #NNN

- **ID Defecto:** #
- **Fecha Encontrado:** DD/MM
- **Tipo de Defecto:** 10 / 20 / 30 / 40 / 50 / 60 / 70 / 80 / 90 / 100
- **Fase Inyección:** Planeación / Diseño / Código
- **Fase Remoción:** Revisión / Pruebas / Producción
- **Severidad:** bajo / medio / alto / crítico
- **Tiempo de Corrección:** N min
- **Descripción:** _¿Qué era y cómo se solucionó?_
- **Estado:** abierto / corregido

---

## 3. Registro de Alcance — Scope Log

> Una entrada por módulo significativo. LOC = Lines of Code netas (sin blanks ni comentarios). Objetos = clases o funciones públicas.

### Módulo: `core` (ETL + dominio)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 400 LOC / 8 funciones (commands + models)
- **Real (LOC / Objetos):** 321 LOC en `core/models.py` + commands (pendiente medir)
- **Checklist de Aceptación:**
  - [x] `create_domain_tables` ejecuta DDL idempotente.
  - [x] `load_csv_normalized` carga `Dataset.csv` con `--batch-size`.
  - [ ] Cobertura de pruebas unitarias ≥ 70% (pendiente — fase Pruebas).
  - [x] Documentado en docstrings.

### Módulo: `usuarios` (CustomUser + Auth)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 150 LOC / 4 vistas + 1 modelo
- **Real (LOC / Objetos):** 22 LOC en `models.py` (modelo mínimo); vistas en modo *preview* sin lógica funcional.
- **Checklist de Aceptación:**
  - [x] `AUTH_USER_MODEL = 'usuarios.CustomUser'` registrado en settings.
  - [ ] 2FA implementado (TOTP via `pyotp`).
  - [ ] Login con CSRF + sesión persistente.
  - [ ] Pruebas unitarias del flujo de registro.

### Módulo: `formulario` (Registro diario)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 200 LOC / 1 modelo + 1 form
- **Real (LOC / Objetos):** 9 LOC en `models.py` (esqueleto)
- **Checklist de Aceptación:**
  - [ ] Modelo `RegistroDiario` con campos validados.
  - [ ] Form con validación de rango (`MinValueValidator`, `MaxValueValidator`).
  - [ ] Migración aplicada.

### Módulo: `frontend/templates`

- **Tipo de Medida:** Reutilizadas + Modificadas
- **Estimado (LOC / Objetos):** 12 templates
- **Real (LOC / Objetos):** 12 templates activos (post-limpieza) + 2 layouts base (`mindmetrics/base.html`, `mindmetrics/auth_base.html`)
- **Checklist de Aceptación:**
  - [x] Todos los templates heredan de `mindmetrics/base.html` o `mindmetrics/auth_base.html`.
  - [x] Assets servidos vía `{% static %}`.
  - [ ] Validación de accesibilidad (WCAG 2.1 AA).

### Módulo: `docker` (Infraestructura)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 1 `docker-compose.yml` + 2 Dockerfiles + 1 `init.sql`
- **Real (LOC / Objetos):** `docker-compose.yml` (95 LOC) + `docker/postgres/init.sql` (~160 LOC) + `docker/django/Dockerfile` (pendiente contenido real)
- **Checklist de Aceptación:**
  - [x] `db` con healthcheck `pg_isready`.
  - [x] `web_ia` `depends_on: db.service_healthy`.
  - [ ] Volumen `postgres_data` persistente verificado tras reinicio.
  - [ ] Healthcheck para `web_ia`.

### Plantilla — Módulo: _NombreDelComponente_

- **Tipo de Medida:** Nuevas / Reutilizadas / Modificadas
- **Estimado (LOC / Objetos):** _N_ LOC / _N_ objetos
- **Real (LOC / Objetos):** _N_ LOC / _N_ objetos
- **Checklist de Aceptación:**
  - [ ] ¿Cumple con el requerimiento RF-XX?
  - [ ] ¿Pasó pruebas unitarias?
  - [ ] ¿Está documentado en `docs/`?

---

## 4. Códigos de Defecto — Referencia rápida (PSP)

| Código | Categoría | Descripción |
|--------|-----------|-------------|
| 10 | Doc | Comentarios, requisitos, especificaciones incompletas. |
| 20 | Sin | Sintaxis, tipografía, errores de formato. |
| 30 | Bld | Compilación, librerías ausentes, build system. |
| 40 | Asg | Inicialización, asignación, valores por defecto. |
| 50 | Int | Parámetros, llamadas, contratos de interfaz. |
| 60 | Chk | Validaciones, límites, condiciones de borde. |
| 70 | Dat | Estructura de datos, esquema, integridad referencial. |
| 80 | Log | Algoritmos, bucles, control de flujo. |
| 90 | Sys | Memoria, hardware, recursos del SO. |
| 100 | Env | Herramientas, IDE, configuración de entorno, Docker, CI/CD. |

---

## 5. Métricas Acumuladas (Auto-resumen)

> Actualizar manualmente al final de cada semana.

| Semana | Tiempo neto total (h) | Defectos inyectados | Defectos removidos | LOC netas añadidas | Densidad defectos (def/KLOC) |
|--------|----------------------|--------------------|--------------------|---------------------|------------------------------|
| W19-2026 | 1.5 | 3 | 3 | 0 (limpieza) | n/a |
