# Objetivo
Eres un asistente experto en organización de proyectos de software. Necesito que analices la estructura actual del proyecto **MindMetrics** (backend Django + scripts ETL) y realices las siguientes tareas:

1. **Revisar y limpiar la estructura de archivos**:
   - Identifica archivos y carpetas que no están siendo utilizados (por ejemplo, código comentado, versiones antiguas, archivos temporales, logs antiguos, backups, etc.).
   - Propón una estructura de directorios limpia y ordenada, manteniendo solo lo necesario para el funcionamiento del proyecto.
   - Genera una lista de archivos/carpetas a eliminar o archivar.
   - Si es posible, reorganiza los archivos en una estructura lógica (ej. `src/`, `scripts/`, `docs/`, `tests/`, `data/`, etc.) sin romper las rutas relativas existentes.

2. **Crear un archivo `PROJECT_LOGS.md`** en la raíz del proyecto que contenga tres secciones con el formato detallado abajo. Si ya existen algunos registros (por ejemplo, en archivos sueltos o en comentarios), intégralos; si no, crea una plantilla inicial.

### 📌 Formato para `PROJECT_LOGS.md`

#### 1. Registro de Tiempo - Time Log
Para cada sesión de trabajo se crea una entrada siguiendo este esquema:

| Fecha | Fase | Actividad | Estado | Inicio | Fin | Interrupciones (min) | Tiempo Neto (Delta) | Comentarios |
|-------|------|-----------|--------|--------|-----|----------------------|---------------------|-------------|
| DD/MM/AAAA | Planeación/Diseño/Código/Revisión/Pruebas/Post-mortem | Actividad específica | Terminado/pendiente/en progreso | HH:MM | HH:MM | minutos | (Fin - Inicio) - Interrupciones | Nota sobre distracciones o hallazgos |

#### 2. Registro de Defectos - Log Calidad
Lista numerada de defectos encontrados:

* **ID Defecto**: # (secuencial)
* **Fecha Encontrado**: DD/MM
* **Tipo de Defecto**: Código de la lista estándar (10,20,30,40,50,60,70,80,90,100)
* **Fase Inyección**: Donde se creó el error (ej. Diseño, Código)
* **Fase Remoción**: Donde se detectó (ej. Pruebas, Revisión)
* **Severidad**: Bajo / medio / alto / crítico
* **Tiempo de Corrección**: minutos dedicados a arreglarlo
* **Descripción**: ¿Qué era y cómo se solucionó?
* **Estado**: abierto / corregido

#### 3. Registro de Alcance - Scope Log
Para cada componente importante (ej. módulo de usuarios, módulo ETL, API, frontend si existe):

* **Módulo**: Nombre del componente
* **Tipo de Medida**: Nuevas / Reutilizadas / Modificadas
* **Estimado (LOC / Objetos)**: Cantidad planeada (ej. 500 LOC, 10 clases)
* **Real (LOC / Objetos)**: Cantidad final después de codificación
* **Checklist de Aceptación**:
  - ¿Cumple con el requerimiento X?
  - ¿Pasó las pruebas unitarias?
  - ¿Está documentado?

#### 📖 Códigos de Defecto (referencia rápida)
- 10 (Doc): Comentarios/Requisitos.
- 20 (Sin): Sintaxis/Tipografía.
- 30 (Bld): Compilación/Librerías.
- 40 (Asg): Inicialización/Valores.
- 50 (Int): Parámetros/Llamadas.
- 60 (Chk): Validaciones/Límites.
- 70 (Dat): Estructura de datos.
- 80 (Log): Algoritmos/Bucles.
- 90 (Sys): Memoria/Hardware.
- 100 (Env): Herramientas/IDE.

### 📁 Estructura que quiero de mi proyecto 
MindMetrics/
├── Backend/                 # (renombrar Backend a backend)
│   ├── core/               # app principal (models, commands, etc.)
│   ├── manage.py
│   ├── requirements.txt    # mover desde raíz
│   ├── etl_auditorias/     # carpeta de auditorías (creada por el ETL)
│   └── ...
├── frontend/ 
│   ├── static/               # app principal (models, commands, etc.)
│   ├── templates              # (
├── docker/                 # archivos dockerfile, scripts de entrada
├── postgres/          # (renombrar PostgreSQL a postgres, para volumen)
├── scripts/                # (nueva) scripts auxiliares, ej. Inicio.bat
├── docs/                   # (nueva) documentación, logs, reportes
├── venv/                   # entorno virtual (no mover, pero puede estar en .gitignore)
├── docker-compose.yml
└── PROJECT_LOGS.md         # (nuevo) archivo con los registros solicitados

### 🧹 Reglas de limpieza
- Conserva los archivos fuente `.py`, `.sql`, `.md`, `.txt` que sean usados por el proyecto.
- Elimina copias de seguridad (`*.bak`, `*~`, `*.old`), archivos de caché (`__pycache__`, `*.pyc`), logs antiguos si ya no son relevantes.
- Si hay archivos de configuración duplicados, mantén el más reciente y elimina los obsoletos.
- Genera un archivo `CLEANUP_REPORT.md` con la lista de archivos eliminados o movidos.

### ✅ Resultados esperados
1. Un reporte de limpieza (`CLEANUP_REPORT.md`).
2. El archivo `PROJECT_LOGS.md` actualizado con los registros existentes o plantillas iniciales.
3. Una nueva estructura de directorios organizada (si es necesario, con sugerencias de cambios).
