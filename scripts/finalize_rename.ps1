# ════════════════════════════════════════════════════════════════════════════════
# MindMetrics — Finalize Rename (PowerShell)
#
# Objetivo:
#   1. Forzar el cambio de case en NTFS para los directorios que solo difieren
#      en mayúsculas (Backend→backend, Frontend→frontend, Templates→templates).
#   2. Limpiar el remanente PostgreSQL/Dataset.csv que no fue eliminable desde
#      la sesión de Cowork (file lock o permisos).
#
# Requisitos:
#   - Ejecutar DESDE la raíz del repositorio MindMetrics.
#   - PowerShell 5.1+ (Windows nativo).
#   - Ningún proceso bloqueando archivos (cierre VS Code, Django dev server, etc.).
#
# Uso:
#   cd C:\MindMetrics
#   powershell -ExecutionPolicy Bypass -File scripts\finalize_rename.ps1
# ════════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

function Rename-DirCase {
    param([string]$Path, [string]$NewName)

    if (-not (Test-Path $Path)) {
        Write-Host "[SKIP] $Path no existe."
        return
    }

    $parent  = Split-Path -Parent $Path
    $current = Split-Path -Leaf   $Path
    $temp    = "_tmp_$([guid]::NewGuid().ToString('N'))"

    if ($current -ceq $NewName) {
        Write-Host "[OK]   $Path ya está en case $NewName."
        return
    }

    Write-Host "[INFO] Renombrando $Path -> $NewName (vía $temp)"
    Rename-Item -Path (Join-Path $parent $current) -NewName $temp
    Rename-Item -Path (Join-Path $parent $temp)    -NewName $NewName
    Write-Host "[OK]   Renombrado."
}

# 1. Case-renames de directorios de primer y segundo nivel
Rename-DirCase -Path ".\Backend"  -NewName "backend"
Rename-DirCase -Path ".\Frontend" -NewName "frontend"
Rename-DirCase -Path ".\frontend\Templates" -NewName "templates"

# 2. Eliminar remanente PostgreSQL/Dataset.csv si existe
if (Test-Path ".\PostgreSQL\Dataset.csv") {
    Write-Host "[INFO] Eliminando .\PostgreSQL\Dataset.csv (copia ya replicada en .\postgres\)..."
    Remove-Item -Path ".\PostgreSQL\Dataset.csv" -Force
}
if (Test-Path ".\PostgreSQL") {
    Write-Host "[INFO] Eliminando carpeta .\PostgreSQL\ (replicada en .\postgres\)..."
    Remove-Item -Path ".\PostgreSQL" -Recurse -Force
}

Write-Host ""
Write-Host "[DONE] Estructura finalizada. Ejecute 'docker compose down -v' antes del primer 'docker compose up --build'."
