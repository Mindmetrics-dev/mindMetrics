# ADR-001: Implementación de 2FA TOTP en MindMetrics

**Status:** Accepted
**Fecha:** 2026-05-10
**Aceptado:** 2026-05-10
**Decisores:** Julian Andres Gomez Cabrera (owner técnico)
**Stack afectado:** Django 4.2 → 5.x · PostgreSQL 15 · `backend/usuarios/` app · `backend/core/` (sin cambios)

---

## 1. Contexto

El proyecto **MindMetrics** debe implementar autenticación de dos factores (TOTP RFC 6238) para proteger el acceso a datos sensibles de evaluación psicológica. Estado actual relevante:

| Componente | Estado |
|------------|--------|
| `backend/usuarios/CustomUser` | Hereda `AbstractUser`, ya tiene `totp_secret`, `is_2fa_enabled`, método `verify_totp` casero usando `pyotp`. `USERNAME_FIELD='email'`. |
| `backend/core/Usuario` | Tabla de dominio (`managed=False`), almacena usuarios del **dataset ML**, NO se usa para autenticación. **NO se toca en este ADR.** |
| `backend/core/EvaluacionInicial` y otros | Referencian `core.Usuario` vía FK. **NO se tocan.** |
| Migraciones existentes | `usuarios/migrations/0001_initial.py` (crea tabla `usuarios_customuser`). Asumimos BD vacía. |
| Dependencias actuales | `pyotp==2.9.0`, `qrcode[pil]==7.4.2`, `djangorestframework==3.14.0`. |

**Fuerzas en juego:**
- Cumplir con NIST SP 800-63B AAL2 (factor de posesión + factor de conocimiento).
- Mantener compatibilidad con el ETL (no romper `core.Usuario` ni FKs existentes).
- Minimizar deuda técnica: usar librerías mantenidas (`django-otp` ≥ 1.5.4) en lugar de TOTP casero.
- Requisitos del usuario: extender `backend/usuarios/` sin crear `apps/accounts/`.

---

## 2. Decisión

Se adopta **`django-otp` + `django-axes` extendiendo el módulo `backend/usuarios/`** existente, con drop & rebuild del modelo `CustomUser` (asumiendo BD vacía).

**Resumen ejecutivo:**

1. Eliminar `totp_secret` y los métodos caseros de `CustomUser`; reemplazarlos por `TOTPDevice` y `StaticDevice` (django-otp).
2. Añadir a `CustomUser` los campos `email_verified_at: datetime|None` y mantener `is_2fa_enabled: bool`.
3. Configurar `AUTH_USER_MODEL = 'usuarios.CustomUser'` (ya está; no cambia).
4. Registrar `django_otp`, `django_otp.plugins.otp_totp`, `django_otp.plugins.otp_static`, `axes` en `INSTALLED_APPS`.
5. Pipeline de auth: `ModelBackend` + `AxesStandaloneBackend` + Argon2 password hasher.
6. Vistas, forms y templates **dentro de `backend/usuarios/`** (no nuevo módulo `apps/accounts/`).

---

## 3. Opciones Consideradas

### Opción A: `django-otp` extendiendo `backend/usuarios/` (Recomendada — adoptada)

| Dimensión | Evaluación |
|-----------|-----------|
| Complejidad | Media — requiere migraciones nuevas + actualizar settings |
| Costo dev | ~2 sesiones (8–10 h) |
| Mantenibilidad | Alta — django-otp es estándar de facto, mantenido |
| Seguridad | Alta — soporte para anti-replay, dispositivo confirmado, throttling |
| Familiaridad equipo | Media (Julian conoce Django pero no django-otp) |

**Pros:**
- Reutiliza la app `usuarios` existente; no duplica responsabilidades.
- `django-otp` aporta `OTPMiddleware`, decorador `@otp_required`, soporte multi-device.
- `django-axes` añade rate limiting a nivel de IP+username con bloqueo configurable.
- Argon2 es el password hasher recomendado por OWASP 2024.
- Cumple PSP/ISO 29148 (trazabilidad RF → diseño).

**Cons:**
- `CustomUser.totp_secret` y `verify_totp()` deben eliminarse — código existente queda obsoleto.
- Requiere migración `0002` (alter) + ejecución de migraciones de `django_otp` y `axes`.

### Opción B: TOTP casero con `pyotp` (status quo extendido)

| Dimensión | Evaluación |
|-----------|-----------|
| Complejidad | Baja inicialmente, alta a largo plazo |
| Mantenibilidad | Baja — hay que implementar a mano: anti-replay, rate limiting, backup codes |
| Seguridad | Media — fácil olvidar mitigaciones (window de tolerancia, etc.) |

**Pros:** Cero dependencias nuevas; menor superficie de ataque por menos código de terceros.
**Cons:** Reinventa la rueda. Sin backup codes nativos. Sin rate limiting. Sin staticdevice.
**Decisión:** Rechazada — viola el principio "no reinventes la rueda" de la spec.

### Opción C: Crear nuevo módulo `apps/accounts/` (per spec literal)

| Dimensión | Evaluación |
|-----------|-----------|
| Complejidad | Alta — añade un directorio raíz `apps/` no presente |
| Limpieza | Alta — separación clara entre auth web y dominio ML |

**Pros:** Coincide con la spec literal del prompt; deja `usuarios/` para deprecación.
**Cons:** Duplica funcionalidad (CustomUser vs apps.accounts.User); aumenta superficie de migración; rompe convención actual.
**Decisión:** Rechazada — el usuario eligió explícitamente "Extender backend/usuarios/".

---

## 4. Trade-off Analysis

| Eje | A (adoptada) | B | C |
|-----|--------------|---|---|
| Time-to-ship | ~10 h | ~20 h (reinventar) | ~14 h (más migración estructural) |
| Riesgo regresión | Bajo (BD vacía) | Bajo | Medio (renombre/duplicación apps) |
| Cumplimiento NIST AAL2 | ✓ | ⚠️ requiere trabajo extra | ✓ |
| Tests automatizables | ✓ (django-otp tiene fixtures) | Hay que escribir todo | ✓ |
| Deuda técnica futura | Baja | Alta | Media |

**Conclusión:** Opción A maximiza calidad/tiempo y respeta la restricción del usuario.

---

## 5. Consecuencias

**Más fácil:**
- Añadir nuevos métodos 2FA en el futuro (WebAuthn, FIDO2) — django-otp tiene plugins.
- Auditoría de seguridad (anti-replay, lockout) gestionada por la librería.
- Tests de integración usando `pytest-django` + `django-otp` fixtures.

**Más difícil:**
- Hay que reentrenar al equipo en django-otp (model `Device` polimórfico, `confirmed=False/True`).
- Las migraciones de `django_otp` añaden 4 tablas (`otp_totp_totpdevice`, `otp_static_staticdevice`, `otp_static_statictoken`, internal indexes).
- Debug en producción es más complejo (multiple devices por usuario).

**Por revisitar (futuro):**
- Decidir si `core.Usuario` y `usuarios.CustomUser` deben fusionarse cuando el ETL madure.
- Implementar verificación de email (`email_verified_at` se llenará vía signal o vista de confirmación).
- Decidir si el segundo factor debe estar disponible vía push notification además de TOTP.

---

## 6. Plan de Implementación (archivo-por-archivo)

> **Convención de notación:** [N] = archivo nuevo, [M] = modificación, [D] = delete, [-] = sin cambios.

### Fase 1 — Modelado y migraciones

| Acción | Ruta | Cambios |
|--------|------|---------|
| [M] | `backend/usuarios/models.py` | Eliminar `totp_secret`, `generate_totp_secret`, `verify_totp`. Mantener `is_2fa_enabled`. Añadir `email_verified_at: DateTimeField(null=True, blank=True)`. Eliminar `import pyotp`. |
| [N] | `backend/usuarios/migrations/0002_remove_totp_add_verified.py` | `RemoveField` (totp_secret) + `AddField` (email_verified_at). |
| [-] | `backend/usuarios/migrations/0001_initial.py` | Sin cambios (BD vacía; se aplica desde cero). |
| [-] | `backend/core/models.py` | Sin cambios — `core.Usuario` permanece intocado (managed=False, dataset ML). |

### Fase 2 — Configuración

| Acción | Ruta | Cambios |
|--------|------|---------|
| [M] | `backend/requirements.txt` | Subir `Django>=5.0,<5.2`, `psycopg[binary]>=3.1`. Añadir `django-otp>=1.5.4`, `django-axes>=6.4`, `argon2-cffi>=23.1`. Quitar `pyotp` y `djangorestframework` si no se usan. |
| [M] | `backend/mi_plataforma/settings.py` | Bloques nuevos: `INSTALLED_APPS` (django_otp + plugins, axes), `MIDDLEWARE` (OTPMiddleware tras Auth, AxesMiddleware al final), `AUTHENTICATION_BACKENDS` ([AxesStandaloneBackend, ModelBackend]), `PASSWORD_HASHERS` (Argon2 primero), `OTP_TOTP_ISSUER = "MindMetrics"`, `AXES_FAILURE_LIMIT = 5`, `AXES_COOLOFF_TIME = timedelta(minutes=15)`, `AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]`. |
| [M] | `docker-compose.yml` | Añadir variables de entorno: `DJANGO_SECRET_KEY`, `OTP_TOTP_ISSUER`, `AXES_FAILURE_LIMIT`, `AXES_COOLOFF_MINUTES`. |
| [M] | `backend/.env` (no versionado) | Añadir `DJANGO_SECRET_KEY=...`, `OTP_TOTP_ISSUER=MindMetrics`, `AXES_FAILURE_LIMIT=5`, `AXES_COOLOFF_MINUTES=15`. |

### Fase 3 — Forms

| Acción | Ruta | Cambios |
|--------|------|---------|
| [M] | `backend/usuarios/forms.py` | Reemplazar contenido con `SignupForm(forms.ModelForm)` (campos email, username, first_name, last_name, password1, password2 + clean_password2 + validate_password). Añadir `LoginStep1Form(forms.Form)` y `LoginStep2Form(forms.Form)` (campo `token` length 6-8). Añadir `Enroll2FAForm(forms.Form)` con campo `token`. |

### Fase 4 — Vistas

| Acción | Ruta | Cambios |
|--------|------|---------|
| [M] | `backend/usuarios/views.py` | Reemplazar las views *preview* por implementaciones funcionales: `signup(request)`, `enroll_2fa(request)` (GET genera QR base64, POST confirma device), `backup_codes(request)` (crea StaticDevice + 8 StaticToken con `secrets.token_hex(5)`), `login_step1(request)`, `login_step2(request)`, `logout_view(request)`, `dashboard(request)` con `@otp_required`. Usar type hints + docstrings. |
| [-] | `backend/core/management/commands/*.py` | Sin cambios. |

### Fase 5 — URLs

| Acción | Ruta | Cambios |
|--------|------|---------|
| [M] | `backend/usuarios/urls.py` | Rutas: `signup/`, `login/`, `login/2fa/`, `2fa/enroll/`, `2fa/backup/`, `logout/`. |
| [M] | `backend/mi_plataforma/urls.py` | Incluir `path('', include('usuarios.urls'))`. Asegurar `path('admin/', admin.site.urls)`. |

### Fase 6 — Templates

| Acción | Ruta | Cambios |
|--------|------|---------|
| [N] | `frontend/templates/usuarios/signup.html` | Form con CSRF, campos email/username/passwords. Hereda de `mindmetrics/auth_base.html`. |
| [N] | `frontend/templates/usuarios/enroll_2fa.html` | Muestra imagen QR (base64) y secreto en texto. Form de token (6 dígitos). |
| [N] | `frontend/templates/usuarios/backup_codes.html` | Lista de 8 códigos + botón "He guardado los códigos" (redirige a dashboard). |
| [M] | `frontend/templates/login.html` | Form email + password (sin 2FA aquí). |
| [N] | `frontend/templates/usuarios/login_step2.html` | Form de token TOTP o backup. |

### Fase 7 — Tests

| Acción | Ruta | Cambios |
|--------|------|---------|
| [N] | `backend/usuarios/tests/__init__.py` | Vacío. |
| [N] | `backend/usuarios/tests/conftest.py` | Fixtures `pytest-django`: `user_factory`, `confirmed_totp_device`, `client_logged_in`. |
| [N] | `backend/usuarios/tests/test_signup.py` | Casos: éxito, email duplicado, contraseña débil (Argon2 + validators). |
| [N] | `backend/usuarios/tests/test_enroll_2fa.py` | Casos: token correcto confirma device, token incorrecto rechaza, anti-replay. |
| [N] | `backend/usuarios/tests/test_login_2fa.py` | Casos: login sin 2FA directo, login con 2FA dos pasos, backup code consume token, rate limiting `django-axes` (simular 6 fallos → 403). |
| [N] | `backend/usuarios/tests/factories.py` | `UserFactory` con `factory_boy`. |
| [N] | `backend/pytest.ini` | `[pytest]` con `DJANGO_SETTINGS_MODULE = mi_plataforma.settings`, `python_files = test_*.py`. |

### Fase 8 — Documentación

| Acción | Ruta | Cambios |
|--------|------|---------|
| [N] | `docs/2FA_API.md` | Documentación de vistas internas (no REST). |
| [M] | `PROJECT_LOGS.md` | Añadir Time Log, Defect Log, Scope Log para el módulo 2FA. |

---

## 7. Migración desde el modelo `CustomUser` actual

**Supuesto:** BD vacía (`docker compose down -v` ejecutado o primera instalación).

### 7.1 Si BD está vacía (caso adoptado)

```powershell
# 1. Bajar volúmenes
docker compose down -v

# 2. Aplicar migraciones limpias
docker compose up --build
# El startup ejecuta: migrate → create_domain_tables → load_csv_normalized
```

Resultado: tablas `usuarios_customuser`, `otp_totp_totpdevice`, `otp_static_staticdevice`, `otp_static_statictoken`, `axes_accessattempt`, `axes_accessfailurelog` creadas vacías.

### 7.2 Si hubiera datos (advertencia futura)

Si en el futuro el `CustomUser` ya tiene filas:

1. **Antes** de aplicar la migración `0002_remove_totp_add_verified`, exportar `totp_secret` de cada fila:
   ```python
   # En un script auxiliar (backend/scripts/migrate_totp.py)
   from django_otp.plugins.otp_totp.models import TOTPDevice
   from usuarios.models import CustomUser
   for user in CustomUser.objects.filter(is_2fa_enabled=True):
       TOTPDevice.objects.create(
           user=user, name='legacy', key=user.totp_secret, confirmed=True
       )
   ```
2. Luego ejecutar la migración `0002` que elimina `totp_secret`.
3. Los usuarios mantienen su 2FA sin re-enrolar.

---

## 8. Checklist de Despliegue

- [ ] **Sincronización de relojes:** Servidor con NTP activo (`timedatectl status` en Linux). TOTP tolera ±30 s; un drift > 60 s rompe verificación.
- [ ] **HTTPS obligatorio:** `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` en `settings.py` cuando `DEBUG=False`.
- [ ] **`DJANGO_SECRET_KEY`** rotada y única por entorno (generar con `python -c "import secrets; print(secrets.token_urlsafe(64))"`).
- [ ] **Variables de entorno en producción:** `DJANGO_SECRET_KEY`, `OTP_TOTP_ISSUER`, `DB_PASSWORD`, `AXES_FAILURE_LIMIT`, `AXES_COOLOFF_MINUTES`.
- [ ] **`SECURE_HSTS_SECONDS = 31536000`** y `SECURE_HSTS_INCLUDE_SUBDOMAINS=True` tras validar HTTPS.
- [ ] **CSRF** activo en todas las vistas POST (django lo trae por default; no desactivar).
- [ ] **Rate limiting** validado: simular 6 fallos en login_step2 desde la misma IP y comprobar bloqueo HTTP 403.
- [ ] **Backup codes**: confirmar que se muestran solo una vez y que cada token se invalida tras un uso (`StaticToken.objects.filter(...).delete()` o uso de `verify_token` de StaticDevice que lo elimina).
- [ ] **Migraciones aplicadas en orden**: `migrate auth`, `migrate usuarios`, `migrate otp_totp`, `migrate otp_static`, `migrate axes`.
- [ ] **Argon2 disponible**: `pip show argon2-cffi` — sin esto, `PASSWORD_HASHERS` falla en runtime.
- [ ] **Logs ETL no contienen secretos**: revisar `backend/etl_auditorias/*.csv` y `logs/`.
- [ ] **Tests pasan con cobertura ≥ 70%**: `pytest backend/usuarios/tests/ --cov=usuarios --cov-fail-under=70`.

---

## 9. Action Items

1. [ ] **Resolver bloqueo de `Frontend/`** (rename pendiente) — no bloquea código pero sí la convención lowercase. Ver `CLEANUP_REPORT.md §9.2`.
2. [ ] **Aprobar este ADR** (cambiar `Status: Proposed` → `Status: Accepted`).
3. [ ] **Ejecutar Fase 1** (modelado + migración) — entregable mínimo: `python manage.py migrate` sin errores.
4. [ ] **Ejecutar Fase 2** (settings.py + requirements.txt) — entregable: contenedor Docker construye sin errores.
5. [ ] **Ejecutar Fases 3-7** en orden, con commit por fase para facilitar rollback.
6. [ ] **Ejecutar Fase 8** (docs + PROJECT_LOGS.md update) — cierre.
7. [ ] **Revisión final**: ejecutar `pytest`, `flake8`, `django-admin check --deploy`.

---

## 10. Advertencias Clave

> **W-01 — `core.Usuario` ≠ `usuarios.CustomUser`.** No fusionar. La primera es la tabla del **dataset ML** (managed=False, gestionada por SQL); la segunda es el modelo de **autenticación web**. Compartir el nombre `usuario` es coincidencia semántica, no técnica.

> **W-02 — Eliminar `totp_secret` rompe el método `verify_totp()` actual.** Asegúrate de que ningún view, signal o test referencie `user.totp_secret` o `user.verify_totp(...)` antes de aplicar la migración 0002.

> **W-03 — Orden de middlewares es crítico.** `OTPMiddleware` debe ir **después** de `AuthenticationMiddleware`; `AxesMiddleware` debe ir **al final**. Invertir el orden causa que `request.user.is_verified()` no funcione o que `axes` no registre intentos.

> **W-04 — `django-axes` requiere migración propia.** `python manage.py migrate axes` debe ejecutarse antes del primer login en producción.

> **W-05 — Templates Frontend.** Las nuevas plantillas deben ubicarse bajo `frontend/templates/usuarios/` (subcarpeta) para coincidir con la convención Django de namespacing por app. Actualizar `TEMPLATES.DIRS` en `settings.py` ya está hecho (`PROJECT_DIR / 'frontend' / 'templates'`); el lookup `usuarios/signup.html` funciona automáticamente.

> **W-06 — pyotp queda obsoleto.** Una vez aplicada esta refactorización, `pyotp` puede removerse de `requirements.txt`. `django-otp` lo trae como dependencia transitiva si lo necesita.
