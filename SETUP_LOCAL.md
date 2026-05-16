# MindMetrics — Guía de Instalación Local (sin Docker)

> Esta guía es para correr el proyecto directamente en tu máquina,  
> sin contenedores. Útil para desarrollo activo y depuración rápida.  
> Tiempo estimado: 20–30 minutos.

---

## Requisitos previos

Instala estas herramientas antes de empezar:

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| Git | cualquiera | https://git-scm.com |
| Python | 3.11 o superior | https://www.python.org/downloads |
| PostgreSQL | 14 o superior | https://www.postgresql.org/download |

> **Verifica que todo esté instalado** antes de continuar:
> ```bash
> git --version
> python --version
> psql --version
> ```

---

## Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/<usuario>/MindMetrics.git
cd MindMetrics
```

> Reemplaza `<usuario>` con el nombre de usuario u organización de GitHub.

---

## Paso 2 — Crear el entorno virtual de Python

Un entorno virtual aísla las dependencias del proyecto de tu Python global.

```bash
# Crear el entorno virtual (se crea una carpeta llamada venv)
python -m venv venv
```

### Activar el entorno virtual

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

> Sabes que está activo cuando ves `(venv)` al inicio de tu terminal:
> ```
> (venv) C:\MindMetrics>
> ```

---

## Paso 3 — Instalar las dependencias de Python

Con el entorno virtual activo, instala todas las librerías del proyecto:

```bash
pip install -r requirements.txt
```

> Esto instala Django, psycopg3, django-otp, scikit-learn y todo lo demás.  
> Puede tardar 1–3 minutos la primera vez.

---

## Paso 4 — Crear la base de datos en PostgreSQL

Necesitas crear una base de datos vacía antes de que Django pueda usarla.

### Paso 4.1 — Abrir la consola de PostgreSQL

**Windows:** Busca **pgAdmin** en el menú de inicio, o abre la terminal y escribe:
```bash
psql -U postgres
```

**Mac / Linux:**
```bash
psql -U postgres
```

> Si te pide contraseña, usa la que pusiste cuando instalaste PostgreSQL.  
> Si no recuerdas la contraseña, mira la sección de problemas frecuentes al final.

### Paso 4.2 — Crear la base de datos

Dentro de la consola de PostgreSQL (`postgres=#`), ejecuta:

```sql
CREATE DATABASE "BD_MindMetrics";
```

Verifica que se creó:
```sql
\l
```

Deberías ver `BD_MindMetrics` en la lista. Luego sal:
```sql
\q
```

---

## Paso 5 — Crear el archivo de variables de entorno

El archivo `backend/.env` no está en el repositorio. Tienes que crearlo manualmente.

### Paso 5.1 — Crear el archivo

**Windows (PowerShell):**
```powershell
New-Item -Path backend\.env -ItemType File
```

**Mac / Linux:**
```bash
touch backend/.env
```

### Paso 5.2 — Pegar el contenido

Abre `backend/.env` con tu editor y escribe exactamente esto:

```env
# ── Django ──────────────────────────────────────────────────────────────────
DJANGO_SECRET_KEY=django-insecure-preview-key-cambiar-en-produccion
DEBUG=True
DJANGO_ALLOWED_HOSTS=*

# ── PostgreSQL ───────────────────────────────────────────────────────────────
DB_NAME=BD_MindMetrics
DB_USER=postgres
DB_PASSWORD=clave123
DB_HOST=localhost
DB_PORT=5432

# ── 2FA ──────────────────────────────────────────────────────────────────────
OTP_TOTP_ISSUER=MindMetrics
```

> **Importante:** Cambia `DB_PASSWORD` por la contraseña real de tu PostgreSQL local.  
> A diferencia del setup con Docker, aquí `DB_HOST=localhost` (no `db`).

---

## Paso 6 — Aplicar las migraciones de Django

Las migraciones crean las tablas que Django necesita para autenticación y 2FA.

Desde la **raíz del proyecto** (`MindMetrics/`), ejecuta:

```bash
python manage.py migrate
```

Deberías ver una lista de migraciones aplicadas:
```
Applying contenttypes.0001_initial... OK
Applying usuarios.0001_initial... OK
Applying otp_totp.0001_initial... OK
...
```

---

## Paso 7 — Crear las tablas de dominio

Estas tablas (`evaluacion_inicial`, `registro_emocional`, etc.) no las crea Django sino un script SQL propio del proyecto.

```bash
python manage.py create_domain_tables --sql-path postgres/02_create_tables.sql
```

Deberías ver:
```
Ejecutando: postgres/02_create_tables.sql
✔ SQL ejecutado correctamente.

Verificando tablas de dominio:
  ✔  usuario
  ✔  emocion
  ✔  tipo_recurso
  ✔  evaluacion_inicial
  ✔  registro_emocional
  ✔  recurso_apoyo
  ✔  presentacion_recurso

✔ Todas las tablas de dominio están presentes.
```

---

## Paso 8 — Cargar el dataset (opcional pero recomendado)

El proyecto incluye un dataset de ~10.900 registros de ejemplo para alimentar el modelo de Machine Learning.

```bash
python manage.py load_csv_normalized postgres/Dataset.csv
```

> Este paso puede tardar **2–4 minutos**. Verás el progreso en la terminal:
> ```
> [ETL] Lote 1-500 insertado (500/10920).
> [ETL] Lote 501-1000 insertado (1000/10920).
> ...
> ETL COMPLETADO [PRODUCCION]
> ```

Si no lo necesitas ahora, puedes saltarlo y ejecutarlo después.

---

## Paso 9 — Crear un superusuario para el admin

```bash
python manage.py createsuperuser
```

Te pedirá:
- **Username:** pon cualquier nombre (ej: `admin`)
- **Email:** tu correo
- **Password:** una contraseña (mínimo 10 caracteres)

---

## Paso 10 — Correr el servidor

```bash
python manage.py runserver
```

Deberías ver:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
Django version 5.x, using settings 'mi_plataforma.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Abre tu navegador y ve a:
```
http://127.0.0.1:8000/
```

---

## Paso 11 — Crear tu usuario de prueba en la app

Sigue el flujo completo en el navegador:

**11.1** — Ve a `http://127.0.0.1:8000/consentimiento/` y acepta.

**11.2** — Regístrate con tu correo y una contraseña de mínimo 10 caracteres.

**11.3** — Configura el 2FA: escanea el código QR con Google Authenticator o Authy, ingresa el código de 6 dígitos para confirmar, y guarda los 8 códigos de respaldo.

**11.4** — Llena la evaluación inicial. Al enviarla, el sistema experto calcula tu nivel de riesgo psicosocial automáticamente.

**11.5** — Llegas al Dashboard con tu resultado.

---

## Cómo trabajar en el día a día

Una vez instalado, para retomar el trabajo en una nueva sesión:

```bash
# 1. Entrar a la carpeta del proyecto
cd MindMetrics

# 2. Activar el entorno virtual
# Windows:
venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# 3. Correr el servidor
python manage.py runserver
```

### Otros comandos útiles

```bash
# Correr las pruebas
pytest backend/

# Crear migraciones después de modificar un modelo
python manage.py makemigrations

# Aplicar migraciones nuevas
python manage.py migrate

# Abrir la shell de Django (para probar consultas ORM)
python manage.py shell

# Entrar a la consola de PostgreSQL del proyecto
psql -U postgres -d BD_MindMetrics

# Recargar el dataset desde cero
python manage.py load_csv_normalized postgres/Dataset.csv
```

---

## Estructura de carpetas (referencia rápida)

```
MindMetrics/
├── backend/
│   ├── .env                ← ⚠ Tú lo creas (no está en el repo)
│   ├── agente/             ← Sistema experto de clasificación de riesgo
│   ├── calendario/         ← Vistas del calendario y resumen del dashboard
│   ├── core/               ← Modelos de dominio (tablas creadas por SQL)
│   ├── formulario/         ← Formulario de evaluación + llamada al agente
│   ├── mi_plataforma/      ← Settings, URLs, WSGI
│   └── usuarios/           ← Auth, 2FA, dashboard, middleware
├── frontend/
│   ├── static/             ← CSS, JS, imágenes
│   └── templates/          ← HTML de todas las pantallas
├── postgres/
│   ├── 02_create_tables.sql ← DDL de las tablas de dominio
│   └── Dataset.csv          ← Dataset de ~10.900 registros
├── manage.py               ← Entry point de Django
└── requirements.txt        ← Dependencias Python
```

---

## Solución de problemas frecuentes

### ❌ `ModuleNotFoundError: No module named 'decouple'` (u otro módulo)

El entorno virtual no está activo o no instalaste las dependencias.

```bash
# Activar el venv
venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate     # Mac/Linux

# Reinstalar dependencias
pip install -r requirements.txt
```

---

### ❌ `django.db.utils.OperationalError: connection refused`

PostgreSQL no está corriendo o las credenciales en `.env` son incorrectas.

**Verifica que PostgreSQL esté activo:**

```bash
# Windows (en PowerShell como administrador)
Get-Service -Name postgresql*

# Mac
brew services list | grep postgresql

# Linux
sudo systemctl status postgresql
```

**Si está apagado, enciéndelo:**
```bash
# Mac
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

Luego revisa que `DB_PASSWORD` en `backend/.env` coincida con tu contraseña real de PostgreSQL.

---

### ❌ `FATAL: password authentication failed for user "postgres"`

La contraseña en `backend/.env` no coincide con la de tu PostgreSQL local.

Edita `backend/.env` y cambia `DB_PASSWORD=clave123` por tu contraseña real.

Si no recuerdas la contraseña, puedes resetearla:
```bash
# Entrar como superusuario del sistema
sudo -u postgres psql                    # Linux/Mac
# En Windows: abre psql desde pgAdmin

# Dentro de psql, cambiar contraseña
ALTER USER postgres WITH PASSWORD 'nueva_contraseña';
\q
```

Luego actualiza `backend/.env` con la nueva contraseña.

---

### ❌ `relation "evaluacion_inicial" does not exist`

No ejecutaste el Paso 7. Las tablas de dominio no se crean con `migrate`.

```bash
python manage.py create_domain_tables --sql-path postgres/02_create_tables.sql
```

---

### ❌ `python manage.py` da error de settings o de import

Asegúrate de estar ejecutando el comando **desde la raíz del proyecto**  
(la carpeta `MindMetrics/`, donde está el `manage.py`), no desde dentro de `backend/`.

```bash
# Correcto ✅
cd MindMetrics
python manage.py runserver

# Incorrecto ❌
cd MindMetrics/backend
python manage.py runserver
```

---

### ❌ El código QR del 2FA no se muestra

Asegúrate de que Pillow esté instalado correctamente:

```bash
pip install qrcode[pil]
```

---

## Contacto del equipo

| Nombre | Rol | Contacto |
|---|---|---|
| Julian Andres Gomez | Desarrollador principal | julianandresgomezcabrera02@gmail.com |
