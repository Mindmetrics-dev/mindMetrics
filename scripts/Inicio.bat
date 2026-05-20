@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM ═══════════════════════════════════════════════════════════════════════════
REM MindMetrics — Bootstrap local sin Docker
REM Estructura esperada (relativa a la raíz del repo, NO a este script):
REM   backend/manage.py
REM   backend/requirements.txt
REM   backend/.env
REM   docker/postgres/init.sql
REM   venv/
REM Ubicación de este script: scripts/Inicio.bat
REM Se posiciona en la raíz del repo automáticamente (cd ..\).
REM ═══════════════════════════════════════════════════════════════════════════

REM ---- 0. Posicionar en la raíz del repo ----
cd /d "%~dp0\.."

echo ==========================================
echo   MINDMETRICS - Setup y arranque
echo ==========================================

REM ---- 1. Validar Python ----
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta en el PATH.
    pause
    exit /b 1
)
echo [OK] Python detectado

REM ---- 2. Crear entorno virtual si no existe (en la raiz) ----
if not exist venv (
    echo [INFO] Creando entorno virtual en .\venv ...
    python -m venv venv
) else (
    echo [OK] Entorno virtual ya existe
)

REM ---- 3. Activar entorno ----
call venv\Scripts\activate.bat

REM ---- 4. Instalar dependencias (backend\requirements.txt) ----
if exist backend\requirements.txt (
    echo [INFO] Instalando dependencias desde backend\requirements.txt ...
    python -m pip install --upgrade pip >nul
    pip install -r backend\requirements.txt
) else (
    echo [ERROR] No se encontro backend\requirements.txt
    pause
    exit /b 1
)

REM ---- 5. Variables de entorno Django ----
set DJANGO_SETTINGS_MODULE=mi_plataforma.settings

REM ---- 6. Migraciones ----
cd backend
echo.
echo [INFO] Generando migraciones...
python manage.py makemigrations
echo [INFO] Aplicando migraciones a PostgreSQL...
python manage.py migrate
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo la conexion a PostgreSQL.
    echo         Verifica que el servicio postgres este corriendo
    echo         y que las credenciales en backend\.env sean correctas.
    echo         La BD "mi_plataforma" debe existir (ejecuta docker\postgres\init.sql).
    pause
    exit /b 1
)

REM ---- 7. Levantar servidor ----
echo.
echo ==========================================
echo   Servidor disponible en:
echo   http://127.0.0.1:8000/
echo ==========================================
echo.
python manage.py runserver

pause
