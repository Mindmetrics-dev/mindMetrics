# MindMetrics — Guía de Instalación para Desarrolladores

> Sigue esta guía **en orden**. Cada paso depende del anterior.  
> Tiempo estimado: 15–20 minutos en una máquina limpia.

---

## Requisitos previos

Antes de empezar, asegúrate de tener instalado en tu computador:

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Git | cualquiera | `git --version` |
| Python | 3.11 o superior | `python --version` |
| Docker Desktop | cualquiera | `docker --version` |
| Docker Compose | v2 (incluido en Docker Desktop) | `docker compose version` |

> **Windows:** usa PowerShell o la terminal de VS Code. Todos los comandos funcionan igual.  
> **Mac / Linux:** usa la terminal normal.

---

## Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/<usuario>/MindMetrics.git
cd MindMetrics
```

> Reemplaza `<usuario>` con el nombre de usuario o la organización de GitHub donde está el repo.

---

## Paso 2 — Crear el archivo de variables de entorno

El archivo `.env` **no está en el repositorio** (está en `.gitignore` por seguridad).  
Tienes que crearlo manualmente dentro de la carpeta `backend/`.

### Paso 2.1 — Crear el archivo

```bash
# En Windows (PowerShell)
New-Item -Path backend\.env -ItemType File

# En Mac / Linux
touch backend/.env
```

### Paso 2.2 — Pegar el contenido

Abre `backend/.env` con cualquier editor de texto y escribe esto:

```env
# ── Django ──────────────────────────────────────────────────────────────────
DJANGO_SECRET_KEY=django-insecure-preview-key-cambiar-en-produccion
DEBUG=True
DJANGO_ALLOWED_HOSTS=*

# ── PostgreSQL ───────────────────────────────────────────────────────────────
DB_NAME=BD_MindMetrics
DB_USER=postgres
DB_PASSWORD=clave123
DB_HOST=db
DB_PORT=5432

# ── 2FA ──────────────────────────────────────────────────────────────────────
OTP_TOTP_ISSUER=MindMetrics
```

> **Importante:** `DB_HOST=db` (no `localhost`). Dentro de Docker los servicios se comunican por nombre, y el servicio de PostgreSQL se llama `db` en el `docker-compose.yml`.

---

## Paso 3 — Levantar los contenedores con Docker

Desde la raíz del proyecto (donde está el archivo `docker-compose.yml`), ejecuta:

```bash
docker compose up --build
```

Este comando hace **4 cosas automáticamente** en orden:

1. Construye la imagen de Django con Python 3.13 y todas las dependencias del `requirements.txt`
2. Levanta PostgreSQL 15 y espera a que esté listo (`healthcheck`)
3. Aplica las migraciones de Django (`python manage.py migrate`)
4. Crea las tablas del dominio 3NF (`python manage.py create_domain_tables`)
5. Carga el dataset CSV con ~10.900 registros (`python manage.py load_csv_normalized`)
6. Inicia el servidor Django en el puerto `8000`

### ¿Cómo sé que funcionó?

Espera hasta ver este mensaje en la terminal:

```
[startup] ── 4/4 Iniciando servidor Django...
Watching for file changes with StatReloader
Performing system checks...
System check identified no issues (0 silenced).
Django version 5.x, using settings 'mi_plataforma.settings'
Starting development server at http://0.0.0.0:8000/
```

> La primera vez puede tardar **3–5 minutos** mientras descarga las imágenes de Docker y carga el CSV.

---

## Paso 4 — Abrir la aplicación

Una vez que el servidor esté corriendo, abre tu navegador y ve a:

```
http://localhost:8000/
```

Deberías ver el dashboard o ser redirigido al formulario de consentimiento.

---

## Paso 5 — Crear tu usuario de prueba

La aplicación tiene un flujo de registro completo. Sigue estos pasos en el navegador:

**Paso 5.1** — Ve a `http://localhost:8000/consentimiento/` y acepta el consentimiento informado.

**Paso 5.2** — Llena el formulario de registro con tu correo y contraseña (mínimo 10 caracteres).

**Paso 5.3** — Configura el 2FA:
- Escanea el código QR con Google Authenticator, Authy o cualquier app TOTP.
- Ingresa el código de 6 dígitos para confirmar.
- Guarda los 8 códigos de respaldo que te muestra (son de un solo uso).

**Paso 5.4** — Llena la evaluación inicial (formulario de onboarding). Al enviarlo, el sistema experto calcula tu nivel de riesgo psicosocial (1 al 5) y lo guarda automáticamente.

**Paso 5.5** — Llegas al Dashboard con tu resultado.

---

## Paso 6 — Acceder al panel de administración de Django (opcional)

Para ver la base de datos directamente desde el navegador:

### Paso 6.1 — Crear un superusuario

Abre otra terminal (mientras Docker sigue corriendo) y ejecuta:

```bash
docker compose exec web_ia python manage.py createsuperuser
```

Te pedirá:
- **Username:** pon cualquier nombre (ej: `admin`)
- **Email:** tu correo
- **Password:** una contraseña segura

### Paso 6.2 — Entrar al admin

Ve a `http://localhost:8000/admin/` e inicia sesión con las credenciales que acabas de crear.

---

## Paso 7 — Apagar los contenedores

Cuando termines de trabajar, detén los contenedores con:

```bash
# Detener sin borrar datos
docker compose down

# Detener Y borrar la base de datos (vuelve a cero)
docker compose down -v
```

> Usa `down -v` solo si quieres reiniciar desde cero. Borra todos los datos de PostgreSQL.

---

## Comandos útiles del día a día

```bash
# Ver los logs en tiempo real
docker compose logs -f web_ia

# Ver solo los logs de PostgreSQL
docker compose logs -f db

# Abrir una terminal dentro del contenedor de Django
docker compose exec web_ia bash

# Correr las pruebas
docker compose exec web_ia pytest

# Aplicar migraciones después de cambiar un modelo
docker compose exec web_ia python manage.py migrate

# Crear nuevas migraciones
docker compose exec web_ia python manage.py makemigrations

# Recargar el dataset manualmente
docker compose exec web_ia python manage.py load_csv_normalized /app/postgres/Dataset.csv
```

---

## Estructura del proyecto (referencia rápida)

```
MindMetrics/
├── backend/
│   ├── agente/            ← Sistema experto de clasificación de riesgo (6 módulos)
│   ├── calendario/        ← Vistas de calendario y resumen del dashboard
│   ├── core/              ← Modelos de dominio (tablas gestionadas por SQL)
│   ├── formulario/        ← Formulario de evaluación inicial + integración con agente
│   ├── mi_plataforma/     ← Settings, URLs raíz, WSGI/ASGI
│   └── usuarios/          ← Autenticación, 2FA, dashboard, middleware
├── docker/
│   ├── django/Dockerfile  ← Imagen Python 3.13 para el servicio web
│   └── postgres/init.sql  ← DDL de primera creación de la BD
├── frontend/
│   ├── static/            ← CSS, JS, imágenes
│   └── templates/         ← Templates HTML de todas las vistas
├── postgres/
│   ├── 02_create_tables.sql ← DDL idempotente (se ejecuta en cada startup)
│   └── Dataset.csv          ← Dataset de ~10.900 registros para el modelo ML
├── docker-compose.yml     ← Orquestación de servicios
├── manage.py              ← Entry point de Django
└── requirements.txt       ← Dependencias Python
```

---

## Solución de problemas frecuentes

### ❌ Error: `db_host: db` — no puede conectar a la base de datos

**Causa:** El archivo `backend/.env` tiene `DB_HOST=localhost` en lugar de `DB_HOST=db`.  
**Solución:** Cambia `DB_HOST=db` y reinicia con `docker compose down && docker compose up`.

---

### ❌ Error: `relation "evaluacion_inicial" does not exist`

**Causa:** Las tablas de dominio no se crearon porque el volumen de Docker ya existía con una BD vacía o incompleta.  
**Solución:**
```bash
docker compose down -v        # borra el volumen
docker compose up --build     # vuelve a crear todo desde cero
```

---

### ❌ Error: `ModuleNotFoundError: No module named 'agente'`

**Causa:** Estás corriendo `python manage.py` desde una ruta incorrecta.  
**Solución:** Siempre ejecuta los comandos desde la raíz del proyecto (donde está el `docker-compose.yml`), usando `docker compose exec web_ia python manage.py ...`.

---

### ❌ El código QR del 2FA no aparece o da error

**Causa:** La librería `qrcode[pil]` necesita Pillow instalado.  
**Solución:** Verifica que el contenedor se construyó correctamente con `docker compose up --build` (no reutilices una imagen vieja).

---

### ❌ El CSV tarda mucho en cargar

Es normal. Son ~10.900 filas con validación completa. En el primer arranque puede tomar **2–4 minutos extra**. El log muestra el progreso:
```
[startup] ── 3/4 Cargando Dataset.csv...
[ETL] Lote 1-500 insertado (500/10920).
[ETL] Lote 501-1000 insertado (1000/10920).
...
```

---

## Contacto del equipo

| Nombre | Rol | Contacto |
|---|---|---|
| Julian Andres Gomez | Desarrollador principal | julianandresgomezcabrera02@gmail.com |
