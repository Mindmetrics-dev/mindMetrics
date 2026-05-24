<div align="center">
  <img src="frontend/static/img/logo-mindmetrics.png" alt="Logo MindMetrics" width="150">
  <h1>Psicoingenieros | MindMetrics</h1>
  <p><strong>Plataforma web predictiva y preventiva para la gestión de la salud mental.</strong></p>

  [![Python](https://img.shields.io/badge/Backend-Python%203.x-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Framework-Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
  [![Docker](https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
  [![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
</div>

---

## 🚀 Sobre el Proyecto

**MindMetrics** es una plataforma de salud mental predictiva y preventiva orientada al monitoreo y análisis automatizado de variables comportamentales en la población adulta de la ciudad de Santiago de Cali. El sistema combina el desarrollo web robusto con un módulo analítico experto para mitigar brechas de acceso en el bienestar emocional.

### ✨ Características Principales
* **Seguridad Multi-Factor:** Autenticación de doble factor (2FA) integrada nativamente mediante algoritmos TOTP y códigos de respaldo.
* **Infraestructura Contenerizada:** Orquestación e independencia de servicios mediante capas de aislamiento en Docker.
* **Gestión Estática Eficiente:** Despliegue optimizado para producción.
* **Persistencia Segura y Coherente:** Replicación e integridad transaccional unificada entre el CustomUser y los modelos de dominio.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Backend / Core** | Python & Django | Lógica de negocio, controladores MVT y seguridad |
| **Módulo Analítico** | Algoritmos de IA | Para la estimación de riesgo emocional |
| **Base de Datos** | PostgreSQL 15 | Almacenamiento relacional persistente en tercera forma normal |
| **Servidor Estáticos** | WhiteNoise | Gestión y distribución síncrona de assets en producción |
| **Orquestación** | Docker & Docker Compose | Contenerización y aislamiento de entornos lógicos |

---

## 📦 Arquitectura de Contenedores

De acuerdo con las decisiones de optimización del sistema e ingeniería de red, el stack productivo se compone de una infraestructura de dos contenedores principales interconectados bajo una red interna tipo *bridge*:

* **`web_ia`:** Contenedor de la capa de aplicación. Aloja el núcleo de Django, los layouts MVT, las validaciones criptográficas de Argon2 y el motor experto de Inteligencia Artificial.
* **`db`:** Motor transaccional PostgreSQL. Cuenta con volúmenes de datos persistentes mapeados al disco y se encuentra aislado del tráfico directo de internet por seguridad.

---

## 🔧 Configuración y Despliegue Local

### Requisitos Previos
Disponer de **Docker** y **Docker Compose** instalados en la máquina local.

### Pasos para iniciar el entorno:

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/Mindmetrics-dev/mindMetrics.git](https://github.com/Mindmetrics-dev/mindMetrics.git)
   cd mindMetrics
   docker compose up --build -d
