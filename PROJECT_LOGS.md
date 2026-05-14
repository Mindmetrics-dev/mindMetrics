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
| 10/05/2026 | Diseño | ADR-001-2FA-TOTP (django-otp + django-axes + Argon2 extendiendo `backend/usuarios/`) | Terminado | 23:30 | 00:15 | 0 | 45 | Aceptado. Decisión: drop & rebuild, BD vacía. 3 opciones evaluadas. |
| 10/05/2026 | Código | Fase 1: modelo `CustomUser` refactorizado + migración `0002_remove_totp_add_verified` | Terminado | 00:15 | 00:30 | 0 | 15 | Removido `totp_secret`, `generate_totp_secret`, `verify_totp`. Añadido `email_verified_at`. Defecto #004 detectado y corregido (AlterModelTable inválido). |
| 10/05/2026 | Código | Fase 2: `requirements.txt` (Django 5, django-otp, django-axes, argon2-cffi) + `settings.py` (middlewares, backends, hashers, OTP_TOTP_ISSUER, AXES_*) + variables OTP en `docker-compose.yml` | Terminado | 00:30 | 00:50 | 0 | 20 | Orden de middlewares verificado: OTPMiddleware después de Auth, AxesMiddleware al final. |
| 10/05/2026 | Código | Fase 3: `forms.py` con SignupForm, LoginStep1Form, LoginStep2Form, Enroll2FAForm | Terminado | 00:50 | 01:05 | 0 | 15 | Validación Argon2 + AUTH_PASSWORD_VALIDATORS. Tokens normalizados (sin espacios ni guiones). |
| 10/05/2026 | Código | Fase 4: `views.py` (signup, enroll_2fa, backup_codes, login_step1, login_step2, logout_view, dashboard) | Terminado | 01:05 | 01:35 | 0 | 30 | Helpers `_verify_2fa_token` (TOTP + Static), `_build_qr_base64`. @otp_required en dashboard. |
| 10/05/2026 | Código | Fase 5: `urls.py` (usuarios + raíz) | Terminado | 01:35 | 01:42 | 0 | 7 | Rutas: /signup/, /login/, /login/2fa/, /2fa/enroll/, /2fa/backup/, /logout/, /dashboard/. |
| 10/05/2026 | Código | Fase 6: 6 templates HTML bajo `frontend/templates/usuarios/` | Terminado | 01:42 | 02:05 | 0 | 23 | signup, enroll_2fa, backup_codes, login, login_step2, locked_out. Heredan de `mindmetrics/auth_base.html`. |
| 10/05/2026 | Pruebas | Fase 7: Suite pytest (`tests/` con factories, conftest, 3 archivos de tests) | Terminado | 02:05 | 02:35 | 0 | 30 | 14 casos cubriendo signup, enroll TOTP (incl. anti-replay), login con/sin 2FA, backup codes one-shot, rate limiting axes. |
| 10/05/2026 | Documentación | Fase 8: `docs/2FA_API.md` + actualización de PROJECT_LOGS.md | Terminado | 02:35 | 02:50 | 0 | 15 | Tabla de endpoints, contratos por vista, modelo de sesión, códigos de error. |
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

### Defecto #004

- **Fecha Encontrado:** 10/05
- **Tipo de Defecto:** 30 (Bld)
- **Fase Inyección:** Código (Fase 1)
- **Fase Remoción:** Revisión (inmediata)
- **Severidad:** medio
- **Tiempo de Corrección:** 1 min
- **Descripción:** Migración `0002_remove_totp_add_verified` incluía `migrations.AlterModelTable(...)`, operación inexistente en Django. Se eliminó (el `db_table` por defecto ya coincidía con `usuarios_customuser`).
- **Estado:** corregido

### Defecto #005

- **Fecha Encontrado:** 10/05
- **Tipo de Defecto:** 50 (Int)
- **Fase Inyección:** Diseño (CustomUser original con `totp_secret`)
- **Fase Remoción:** Diseño (ADR-001)
- **Severidad:** medio
- **Tiempo de Corrección:** N/A (decisión arquitectónica)
- **Descripción:** El `CustomUser` original implementaba TOTP a mano con `pyotp`, sin anti-replay, sin rate limiting, sin backup codes. Reemplazado por `django-otp` (TOTPDevice + StaticDevice).
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

### Módulo: `usuarios` (CustomUser + Auth + 2FA)

- **Tipo de Medida:** Modificadas + Nuevas
- **Estimado (LOC / Objetos):** ~700 LOC / 7 vistas + 4 forms + 1 modelo + 6 templates + 14 tests
- **Real (LOC / Objetos):**
  - `models.py`: 40 LOC (refactor)
  - `forms.py`: 130 LOC (4 forms)
  - `views.py`: 230 LOC (7 vistas + 3 helpers)
  - `urls.py`: 25 LOC
  - `migrations/0002_*.py`: 35 LOC
  - Templates: 6 archivos (≈ 220 LOC totales)
  - Tests: 4 archivos (`test_signup.py`, `test_enroll_2fa.py`, `test_login_2fa.py`, `factories.py`, `conftest.py`) ≈ 350 LOC
- **Checklist de Aceptación:**
  - [x] `AUTH_USER_MODEL = 'usuarios.CustomUser'` registrado en settings.
  - [x] 2FA implementado con `django-otp` (TOTPDevice + StaticDevice).
  - [x] Login con CSRF + sesión persistente + flujo en dos pasos.
  - [x] Rate limiting con `django-axes` (5 intentos / 15 min).
  - [x] Backup codes (8, single-use).
  - [x] Pruebas unitarias del flujo de registro, enrolamiento, login, backup, rate limiting.
  - [ ] Validación end-to-end con `docker compose up --build` (pendiente: requiere finalize_rename.ps1 + arranque).
  - [x] Documentación en `docs/2FA_API.md` y `docs/ADR-001-2FA-TOTP.md`.

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
