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
| 11/05/2026 | Código / Revisión | Corrección de `frontend/templates/usuarios/register.html`: 5 defectos encontrados (form.full_name→username, brand faltante, IDs de Django no estándar, for/id desincronizados, SVG inline) | Terminado | — | — | — | ~60 | Defectos #006 y #007 registrados. Template entregado como drop-in replacement con contexto limpio. |
| 12/05/2026 | Debug / Código | Diagnóstico y fix de `enroll_2fa`: `TOTPDevice.get_or_create(confirmed=False)` generaba device duplicado al re-abrir `/2fa/enroll/`. Fix: guard para redirigir si `is_2fa_enabled=True`. | Terminado | — | — | — | ~90 | Defecto #008 registrado. Fix aplicado en `backend/usuarios/views.py`. Instrucciones de limpieza vía `manage.py shell` provistas. |
| 13/05/2026 | Diseño / Código | Script SQL idempotente `postgres/03_reorder_evaluacion_inicial.sql` para reordenar columnas de `evaluacion_inicial` via recreación + PL/pgSQL. FK y SERIAL sincronizados. | Terminado | — | — | — | ~60 | Script ejecutable con `psql -U postgres -d BD_MindMetrics -f ...`. Backup recomendado previo. |
| 14/05/2026 | Post-mortem | Unificación de `requirements.txt`: 3 archivos (raíz + backend + frontend) → 1 canónico en raíz. Resolución de conflictos: Django ≥5.0,<5.2 · psycopg3 sobre psycopg2. | Terminado | ~16:00 | ~16:38 | 0 | 38 | `python-decouple` + `python-dotenv` + `django-environ` coexisten pendiente limpieza. |
| 14/05/2026 | Documentación | Creación de `SETUP.md` (7 pasos Docker, comandos del día a día, 5 errores frecuentes) y `SETUP_LOCAL.md` (11 pasos entorno local, win/mac/linux, reset password postgres). | Terminado | ~16:38 | ~17:11 | 0 | 33 | Incluye nota crítica: `DB_HOST=db` (Docker) vs `DB_HOST=localhost` (local). |
| 14/05/2026 | Código | Refactoring mayor de estructura de proyecto: nuevas apps `agente`, `recursos`, `historial`, `calendario`, `perfil`. `core/models.py` expandido a 338 LOC. Migración `0002_alter_emocion`. | Terminado | ~16:21 | — | — | ~120 | Base para el motor experto y las vistas funcionales de la plataforma. |
| 15/05/2026 | Código | **Motor Experto `backend/agente/`**: `classifier.py` (167 LOC), `scorer.py` (194 LOC), `mapper.py` (449 LOC), `rules.py` (392 LOC, 21 reglas sinérgicas), `state_builder.py` (206 LOC), `variables.py` (164 LOC). Fórmula: `Score_final = (Score_bruto×0.65 + Score_sinérgico×0.25)×F_prot + Ajuste_clínico×0.10`. | Terminado | ~16:00 | ~17:00 | 0 | ~60 | 1 572 LOC. Nivel de riesgo 1–5 (`ceil(Score×5)`). Ajuste clínico por sustancias/diagnóstico. |
| 15/05/2026 | Código | **Módulo `formulario/actualizacion/`**: `forms.py` (283 LOC), `services.py` (210 LOC), `state_builder.py` (253 LOC), `views.py` (188 LOC), `urls.py`. Flujo: validar → resolver FK → crear RegistroEmocional → inferir riesgo → guardar, todo en `transaction.atomic`. | Terminado | ~16:17 | ~17:15 | 0 | ~58 | ~950 LOC. Idempotente: un registro por usuario por fecha. |
| 15/05/2026 | Código | Apps `recursos` (models + 243 LOC views + urls), `historial` (models + 101 LOC views + urls), `calendario` (models + 259 LOC views + urls), `perfil` (models + forms + 21 LOC views). | Terminado | ~17:12 | ~17:15 | 0 | ~60 | ~825 LOC netas. Cada app con su `apps.py` e `__init__.py`. |
| 15/05/2026 | Código | **Templates** nuevos (DTL): `dashboard.html`, `evaluacion_inicial.html`, `registro_diario.html`, `calendario.html`, `historial.html`, `recursos.html`, `perfil.html`, `resultado_registro.html`, `consentimiento.html`. Base `mindmetrics/base.html` y `auth_base.html` actualizados. | Terminado | ~19:00 | ~23:00 | 0 | ~240 | ~1 580 LOC de templates. Migración `0002_customuser_perfil_fields` en `usuarios`. |
| 15/05/2026 | Post-mortem | **Auditoría MVT + Docker** (`local_80dead29`): 14 issues (6 críticos, 4 graves, 4 moderados). Detectados: `DB_HOST=localhost`, path incorrecto de `requirements.txt` en Dockerfile, `working_dir` vs `manage.py`. App `etl_auditorias` marcada para eliminar. Defectos #009–#014 registrados. | En progreso | — | — | — | — | Docker NO listo para levantar (3 críticos bloquean boot). Fixes pendientes de aplicar. |
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

### Defecto #006

- **Fecha Encontrado:** 11/05
- **Tipo de Defecto:** 70 (Dat)
- **Fase Inyección:** Código (template `register.html`)
- **Fase Remoción:** Revisión
- **Severidad:** medio
- **Tiempo de Corrección:** 5 min
- **Descripción:** Template `register.html` referenciaba `form.full_name` (campo inexistente en `SignupForm`) en lugar de `form.username`. Valores y errores del campo nunca se renderizaban. POST fallido vaciaba el campo silenciosamente.
- **Estado:** corregido

### Defecto #007

- **Fecha Encontrado:** 11/05
- **Tipo de Defecto:** 60 (Chk)
- **Fase Inyección:** Código (template `register.html`)
- **Fase Remoción:** Revisión
- **Severidad:** bajo
- **Tiempo de Corrección:** 2 min
- **Descripción:** `<label for="id_password">` apuntaba a `id="id_password1"` y `<label for="id_password_confirm">` a `id="id_password2"`. Desincronización for/id rompía accesibilidad (WCAG 2.1 criterios 1.3.1 y 3.3.2). Click en label no enfocaba el input.
- **Estado:** corregido

### Defecto #008

- **Fecha Encontrado:** 12/05
- **Tipo de Defecto:** 80 (Log)
- **Fase Inyección:** Código (vista `enroll_2fa`)
- **Fase Remoción:** Debug
- **Severidad:** alto
- **Tiempo de Corrección:** 30 min
- **Descripción:** `TOTPDevice.objects.get_or_create(user=user, name="default", confirmed=False)` no matcheaba el device ya confirmado (id=1) y creaba uno nuevo (id=2) cada vez que el usuario re-abría `/2fa/enroll/`. La app autenticadora sincronizaba el secret del device nuevo; la BD validaba contra el viejo → login con 2FA fallaba siempre. Fix: guard en `enroll_2fa` que redirige al dashboard si `is_2fa_enabled=True`.
- **Estado:** corregido

### Defecto #009

- **Fecha Encontrado:** 15/05
- **Tipo de Defecto:** 100 (Env)
- **Fase Inyección:** Configuración (`.env` Docker)
- **Fase Remoción:** Auditoría
- **Severidad:** crítico
- **Tiempo de Corrección:** 1 min
- **Descripción:** `DB_HOST=localhost` en `backend/.env`. Dentro del contenedor `web_ia`, `localhost` apunta al propio contenedor, no al servicio PostgreSQL. Correcto: `DB_HOST=db` (nombre del servicio en docker-compose).
- **Estado:** abierto

### Defecto #010

- **Fecha Encontrado:** 15/05
- **Tipo de Defecto:** 100 (Env)
- **Fase Inyección:** Configuración (Dockerfile)
- **Fase Remoción:** Auditoría
- **Severidad:** crítico
- **Tiempo de Corrección:** 2 min
- **Descripción:** `docker/django/Dockerfile` ejecuta `COPY backend/requirements.txt /app/backend/requirements.txt` pero `requirements.txt` fue unificado a la raíz del proyecto. Build falla con `file not found in build context`. Fix: `COPY requirements.txt /app/requirements.txt`.
- **Estado:** abierto

### Defecto #011

- **Fecha Encontrado:** 15/05
- **Tipo de Defecto:** 100 (Env)
- **Fase Inyección:** Configuración (docker-compose.yml)
- **Fase Remoción:** Auditoría
- **Severidad:** crítico
- **Tiempo de Corrección:** 1 min
- **Descripción:** `working_dir: /app/backend` en el servicio `web_ia`, pero `manage.py` está en la raíz `/app/`. El comando `python manage.py migrate` falla porque no encuentra el archivo. Fix: cambiar `working_dir: /app` o llamar con path absoluto.
- **Estado:** abierto

### Defecto #012

- **Fecha Encontrado:** 15/05
- **Tipo de Defecto:** 70 (Dat)
- **Fase Inyección:** Diseño (migración `0002_delete_perfil`)
- **Fase Remoción:** Auditoría
- **Severidad:** crítico
- **Tiempo de Corrección:** 20 min
- **Descripción:** La migración `perfil/migrations/0002_delete_perfil.py` elimina la tabla `perfil_perfil` de la BD, pero `perfil/views.py` ejecuta `Perfil.objects.get_or_create(usuario=request.user)` en tiempo de ejecución. Runtime: `ProgrammingError: relation "perfil_perfil" does not exist`. Además, `perfil/model.py` (nombre incorrecto, debería ser `models.py`) importa `auth.User` en vez de `get_user_model()`.
- **Estado:** abierto

### Defecto #013

- **Fecha Encontrado:** 15/05
- **Tipo de Defecto:** 10 (Doc)
- **Fase Inyección:** Código (debug session 12/05)
- **Fase Remoción:** Auditoría
- **Severidad:** medio
- **Tiempo de Corrección:** 10 min
- **Descripción:** 13 sentencias `print("[2FA DEBUG] ...")` en `backend/usuarios/views.py` función `_verify_2fa_token` exponen datos de autenticación (user.pk, token, resultado) en stdout/logs del contenedor Docker. Viola mínima exposición de información. Fix: reemplazar por `logger.debug(...)`.
- **Estado:** abierto

### Defecto #014

- **Fecha Encontrado:** 15/05
- **Tipo de Defecto:** 10 (Doc)
- **Fase Inyección:** Código (`settings.py`)
- **Fase Remoción:** Auditoría
- **Severidad:** bajo
- **Tiempo de Corrección:** 1 min
- **Descripción:** `AXES_LOCKOUT_TEMPLATE = "usuarios/locked_out.html"` en `settings.py`, pero el template físico está en `frontend/templates/locked_out.html` (raíz, sin subdirectorio `usuarios/`). Al activarse Axes, la pantalla de bloqueo lanza `TemplateDoesNotExist`. Fix: `AXES_LOCKOUT_TEMPLATE = "locked_out.html"`.
- **Estado:** abierto

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

### Módulo: `agente` (Motor Experto de Riesgo Psicológico)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 1 500 LOC / 6 módulos
- **Real (LOC / Objetos):** 1 572 LOC / 6 archivos (`classifier.py`, `scorer.py`, `mapper.py`, `rules.py`, `state_builder.py`, `variables.py`)
- **Checklist de Aceptación:**
  - [x] Fórmula: `Score_final = (Score_bruto×0.65 + Score_sinérgico×0.25)×F_prot + Ajuste_clínico×0.10`.
  - [x] 21 reglas sinérgicas con activación total/parcial y deduplicación de pares solapados.
  - [x] Nivel de riesgo 1–5 (`ceil(Score×5)`).
  - [x] Ajuste clínico por sustancias (4A) y diagnóstico previo (4B).
  - [x] Integrado en `formulario/actualizacion/services.py` vía `transaction.atomic`.
  - [ ] Tests unitarios del motor (`pytest`) — pendiente.
  - [ ] Validación con dataset real y métricas de clasificación (KNN/SVM comparativo).

### Módulo: `formulario/actualizacion` (Flujo de Registro Diario)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 900 LOC / 5 archivos
- **Real (LOC / Objetos):** 934 LOC (`forms.py` 283, `services.py` 210, `state_builder.py` 253, `views.py` 188, `urls.py` ~15)
- **Checklist de Aceptación:**
  - [x] Flujo: validar → resolver FK Emocion → crear RegistroEmocional → inferir riesgo → guardar.
  - [x] Un registro por usuario por fecha (idempotencia).
  - [x] Rollback automático vía `transaction.atomic` si el motor falla.
  - [ ] Migración de la tabla `RegistroEmocional` aplicada en Docker.
  - [ ] Pruebas de integración (end-to-end: form submit → nivel_riesgo en BD).

### Módulo: `recursos` (App Recursos de Apoyo)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 280 LOC / 3 archivos
- **Real (LOC / Objetos):** ~290 LOC (`models.py` ~30, `views.py` 243, `urls.py` ~15) + `recursos.html` (66 LOC)
- **Checklist de Aceptación:**
  - [x] App registrada en `INSTALLED_APPS` con `apps.py`.
  - [ ] Migración aplicada.
  - [ ] Datos de recursos cargados (fixtures o admin).

### Módulo: `historial` (App Historial de Registros)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 150 LOC / 3 archivos
- **Real (LOC / Objetos):** ~150 LOC (`models.py` ~30, `views.py` 101, `urls.py` ~15) + `historial.html` (96 LOC)
- **Checklist de Aceptación:**
  - [x] App registrada con `apps.py` e `__init__.py`.
  - [ ] Migración aplicada.
  - [ ] Vista conectada al usuario autenticado.

### Módulo: `calendario` (App Calendario)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 300 LOC / 4 archivos
- **Real (LOC / Objetos):** ~305 LOC (`models.py` ~30, `views.py` 259, `urls.py` ~15) + `calendario.html` (145 LOC)
- **Checklist de Aceptación:**
  - [x] App registrada con `apps.py`.
  - [x] Funciones `_build_week_context` y `_get_dashboard_summary` creadas (acopladas aún desde `usuarios/views.py`).
  - [ ] Extraer a `calendario/services.py` (deuda técnica — Defecto arquitectónico audit).
  - [ ] Migración aplicada.

### Módulo: `perfil` (App Perfil de Usuario)

- **Tipo de Medida:** Nuevas
- **Estimado (LOC / Objetos):** 100 LOC / 4 archivos
- **Real (LOC / Objetos):** ~80 LOC (`models.py` ~30, `forms.py` ~30, `views.py` 21) + `perfil.html` (180 LOC)
- **Checklist de Aceptación:**
  - [x] `CustomUser` extendido con campos de perfil (migración `0002_customuser_perfil_fields`).
  - [ ] Defecto #012 corregido: `perfil/model.py` → renombrar a `models.py`, importar `get_user_model()`, restaurar tabla con migración `0003_restore_perfil`.
  - [ ] Vista conectada sin wrapper redundante en `usuarios/views.py`.

### Módulo: `templates` (Vistas Finales MVT — W20)

- **Tipo de Medida:** Nuevas + Modificadas
- **Estimado (LOC / Objetos):** 1 500 LOC / 9 templates
- **Real (LOC / Objetos):** ~1 580 LOC (`dashboard.html` 183, `evaluacion_inicial.html` 435, `registro_diario.html` 201, `calendario.html` 145, `historial.html` 96, `recursos.html` 66, `perfil.html` 180, `resultado_registro.html` 40, `consentimiento.html` 235) + `mindmetrics/base.html` y `auth_base.html` actualizados.
- **Checklist de Aceptación:**
  - [x] Todos heredan de `mindmetrics/base.html` o `mindmetrics/auth_base.html`.
  - [x] Assets servidos vía `{% static %}`.
  - [ ] Defecto #012 bloqueante: `perfil_inicial.html` inexistente (vista en `usuarios/views.py` línea 313).
  - [ ] Validación visual end-to-end con `docker compose up --build`.
  - [ ] Validación de accesibilidad (WCAG 2.1 AA).

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
| W19-2026 (04–10/05) | 4.5 | 5 | 5 | ~1 100 (2FA + ETL) | 4.5 def/KLOC |
| W20-2026 (11–17/05) | ~11 | 9 | 3 (abiertos: 6) | ~6 300 (agente + actualizacion + apps + templates + docs) | ~1.4 def/KLOC |
| **TOTAL acumulado** | **~15.5** | **14** | **8** | **~7 400** | **~1.9 def/KLOC** |
