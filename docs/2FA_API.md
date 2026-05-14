# 2FA API (interna) — MindMetrics

> Documentación de las vistas de autenticación y 2FA expuestas por `usuarios/urls.py`.
> No es una API REST; son vistas Django renderizadas por servidor.

**Versión:** 1.0
**Fecha:** 2026-05-10
**Referencia:** `docs/ADR-001-2FA-TOTP.md`

---

## 1. Tabla de endpoints

| Método | URL | Vista | Auth requerida | 2FA requerida | Descripción |
|--------|-----|-------|----------------|---------------|-------------|
| GET/POST | `/signup/` | `signup` | No | No | Alta de usuario. Tras éxito → `enroll_2fa`. |
| GET/POST | `/login/` | `login_step1` | No | No | Email + password. Si 2FA activo → `login_step2`; si no → `dashboard`. |
| GET/POST | `/login/2fa/` | `login_step2` | Sesión pendiente | No | Verificación TOTP o backup code. |
| GET/POST | `/2fa/enroll/` | `enroll_2fa` | Sí | No | Genera QR + secreto, confirma `TOTPDevice` con primer token. |
| GET/POST | `/2fa/backup/` | `backup_codes` | Sí | No | Muestra 8 códigos de respaldo (UNA sola vez). |
| POST | `/logout/` | `logout_view` | Sí | No | Cierra sesión. |
| GET | `/dashboard/`, `/` | `dashboard` | Sí | **Sí** (`@otp_required`) | Página principal. Si no hay device confirmado → redirige a `login_step1`. |

---

## 2. Contratos por vista

### 2.1 `signup` (`/signup/`)

**Form:** `SignupForm`
**Campos POST:** `email`, `username`, `first_name`, `last_name`, `password1`, `password2`, `csrfmiddlewaretoken`.
**Respuestas:**
- `200` con form re-renderizado y errores si hay validación fallida.
- `302` → `/2fa/enroll/` si éxito (login automático + mensaje informativo).

**Validaciones aplicadas:**
- `email` único (case-insensitive).
- `password1 == password2`.
- `AUTH_PASSWORD_VALIDATORS` de `settings.py`: longitud ≥ 10, no común, no numérica, no similar al usuario.

---

### 2.2 `login_step1` (`/login/`)

**Form:** `LoginStep1Form`
**Campos POST:** `email`, `password`.
**Comportamiento:**
1. `authenticate(...)` con `AxesStandaloneBackend` + `ModelBackend`.
2. Si `user.is_2fa_enabled` y existe `TOTPDevice(confirmed=True)`:
   - `request.session[PENDING_2FA_KEY] = user.pk`
   - `302` → `/login/2fa/`
3. Si no: `login(request, user)` + `302` → `/dashboard/`.

**Rate limiting:** controlado por `django-axes` (`AXES_FAILURE_LIMIT=5`, `AXES_COOLOFF_TIME=15min`). Tras superar el límite, se renderiza `usuarios/locked_out.html`.

---

### 2.3 `login_step2` (`/login/2fa/`)

**Form:** `LoginStep2Form` (campo `token`).
**Pre-condición:** `request.session["pending_2fa_user_id"]` debe existir; si no, `302` → `/login/`.
**Comportamiento:**
1. Recupera `User` por PK guardado en sesión.
2. `_verify_2fa_token(user, token)` itera sobre:
   - `TOTPDevice(user=user, confirmed=True)` → `verify_token`.
   - `StaticDevice(user=user, confirmed=True)` → `verify_token` (consume el `StaticToken`).
3. Si válido: `login(request, user)` + limpieza de sesión + `302` → `/dashboard/`.
4. Si no: form se re-renderiza con error.

---

### 2.4 `enroll_2fa` (`/2fa/enroll/`)

**Form:** `Enroll2FAForm` (campo `token`).
**Comportamiento:**
- **GET:** `get_or_create(user=request.user, name="default", confirmed=False)`, genera QR PNG codificado en base64 desde `device.config_url`, renderiza template con `secret = device.key`.
- **POST:** verifica `token` con `device.verify_token(...)`. Si válido:
  - `device.confirmed = True`
  - `user.is_2fa_enabled = True`
  - `user.email_verified_at = timezone.now()`
  - `302` → `/2fa/backup/`.

**Context del template:** `{ form, qr_image (base64 sin prefijo), secret, user }`.

---

### 2.5 `backup_codes` (`/2fa/backup/`)

**Comportamiento:**
- **GET:** elimina tokens previos del `StaticDevice` del usuario, crea 8 nuevos con `secrets.token_hex(5)`, los muestra UNA vez.
- **POST:** confirmación del usuario, redirige a `/dashboard/`.

**Context del template:** `{ codes: list[str] }` (cada code = 10 chars hex).

**Advertencia operativa:** Si el usuario abandona esta página sin hacer POST, los códigos quedan almacenados en BD pero no fueron mostrados — `StaticToken.objects.filter(...).delete()` al regenerar previene fuga, pero el usuario perdió la única oportunidad de verlos.

---

### 2.6 `dashboard` (`/dashboard/`)

**Decorator:** `@otp_required(login_url="login_step1", redirect_field_name="next")`.

**Comportamiento:** Si el usuario no tiene OTP verificado activo en la sesión actual, `302` → `/login/?next=/dashboard/`.

---

## 3. Modelo de sesión

| Clave | Tipo | Cuándo se setea | Cuándo se limpia |
|-------|------|-----------------|------------------|
| `pending_2fa_user_id` | int | `login_step1` tras password OK | `login_step2` tras TOTP OK, o expiración natural de la sesión |
| `_auth_user_id` | int | `login()` después de TOTP OK (o sin 2FA) | `logout()` |
| `_otp_device_id` | str | Automático por `OTPMiddleware` tras verificación | `logout()` |

---

## 4. Códigos de error y mensajes

| Situación | Detección | Mensaje al usuario |
|-----------|-----------|--------------------|
| Email ya registrado | `SignupForm.clean_email` | "Ya existe un usuario con este correo." |
| Password débil | `validate_password` | Mensaje propio del validator de Django. |
| Contraseñas no coinciden | `SignupForm.clean_password2` | "Las contraseñas no coinciden." |
| Credenciales login inválidas | `authenticate() is None` | "Credenciales inválidas." |
| Cuenta inactiva | `not user.is_active` | "Cuenta inactiva." |
| TOTP inválido en enrolamiento | `device.verify_token == False` | "El código no es válido o ya expiró." |
| TOTP/backup inválido en login | `_verify_2fa_token == False` | "Código incorrecto." |
| Rate limit superado | Middleware de `django-axes` | Template `usuarios/locked_out.html` |

---

## 5. Seguridad

- **CSRF:** todas las vistas POST usan `@csrf_protect`. Templates incluyen `{% csrf_token %}`.
- **Password hashing:** Argon2 (primero en `PASSWORD_HASHERS`).
- **Anti-replay TOTP:** `TOTPDevice.verify_token` actualiza `last_t` para impedir reuso del mismo código.
- **Backup codes single-use:** `StaticDevice.verify_token` elimina el `StaticToken` consumido.
- **HSTS / SSL:** activado automáticamente cuando `DEBUG=False`.
- **Rate limiting:** `django-axes` con `LOCKOUT_PARAMETERS=["ip_address", "username"]` mitiga brute-force tanto por IP como por cuenta.
