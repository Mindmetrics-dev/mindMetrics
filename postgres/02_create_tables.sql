-- =====================================================================================
-- MindMetrics — 02_create_tables.sql
-- DDL idempotente (IF NOT EXISTS) para el esquema de dominio 3NF.
-- Ejecutar DESPUÉS de que Django aplique sus propias migraciones.
-- Tablas gestionadas con managed=False en core/models.py.
-- =====================================================================================

-- ────────────────────────────────────────────────────────────────────────────────────
-- 1. TABLAS MAESTRAS (sin llaves foráneas)
-- ────────────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario            SERIAL PRIMARY KEY,
    email                 VARCHAR(100) UNIQUE NOT NULL,
    password              TEXT        NOT NULL,
    nickname              VARCHAR(50),
    activo                BOOLEAN     DEFAULT TRUE,
    consentimiento_aceptado BOOLEAN   DEFAULT FALSE,
    "2FA_habilitado"      BOOLEAN     DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS emocion (
    id_emocion      SERIAL PRIMARY KEY,
    nombre_emocion  VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS tipo_recurso (
    id_tipo_recurso SERIAL PRIMARY KEY,
    nombre_recurso  VARCHAR(100) NOT NULL
);

-- ────────────────────────────────────────────────────────────────────────────────────
-- 2. TABLAS DEPENDIENTES
-- ────────────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS evaluacion_inicial (
    id_eval              SERIAL PRIMARY KEY,
        id_usuario           INTEGER NOT NULL,

        -- Datos sociodemograficos
        edad                 INTEGER,
        genero               VARCHAR(20),
        estado_relacion      VARCHAR(50),
        situacion_trabajo    VARCHAR(100),

        -- Habitos de vida (horas)
        hr_sueno             FLOAT,
        hr_trabajo           FLOAT,
        hr_pantalla          FLOAT,
        hr_act_fis           FLOAT,

        -- Niveles de estres y satisfaccion (escala 1-10)
        estres_laboral       INTEGER,
        estres_academico     INTEGER,
        estres_financ        INTEGER,
        satisfaccion_laboral INTEGER,

        -- Campos compatibles con agente/mapper.py
        -- uso_sustancias: BOOLEAN (True=consume, False/NULL=no consume)
        -- cambio_emocional: INTEGER 1-10 (mapper._map_escala espera int)
        -- diagnostico_previo: BOOLEAN (True=con diagnóstico, False/NULL=sin)
        -- tratamiento_previo: TEXT con valores 'ninguno'|'adherente'|'abandono'
        -- dificultad_concentra: TEXT con valores 'ninguno'|'ocasional'|'frecuente'
        -- apoyo_percibido: TEXT con valores del SITUACION_APOYO_RECIBIDO
        uso_sustancias       BOOLEAN,
        dificultad_concentra TEXT,
        cambio_emocional     INTEGER,
        diagnostico_previo   BOOLEAN,
        tratamiento_previo   TEXT,
        apoyo_percibido      TEXT,

        -- Antecedentes booleanos
        historial_panico     BOOLEAN,
        historial_familiar   BOOLEAN
);

CREATE TABLE IF NOT EXISTS registro_emocional (
    id_registro          SERIAL PRIMARY KEY,
    id_usuario           INTEGER NOT NULL REFERENCES usuario(id_usuario),
    id_emocion           INTEGER NOT NULL REFERENCES emocion(id_emocion),
    fecha_registro       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nivel_riesgo         VARCHAR(50),
    hr_sueno_dia         FLOAT,
    hr_trabajo_dia       FLOAT,
    hr_pantalla_dia      FLOAT,
    hr_act_fis_dia       FLOAT,
    estres_laboral_dia   INTEGER,
    estres_academico_dia INTEGER,
    estres_financ_dia    INTEGER,
    apoyo_percibido_dia  TEXT,
    autocuidado          TEXT,
    animo                TEXT
);

CREATE TABLE IF NOT EXISTS recurso_apoyo (
    id_recurso      SERIAL PRIMARY KEY,
    id_tipo_recurso INTEGER NOT NULL REFERENCES tipo_recurso(id_tipo_recurso),
    titulo          VARCHAR(200) NOT NULL,
    informacion     TEXT,
    imagen          TEXT
);

-- ────────────────────────────────────────────────────────────────────────────────────
-- 3. TABLA DE RELACIÓN M2M
-- ────────────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS presentacion_recurso (
    id_usuario         INTEGER NOT NULL REFERENCES usuario(id_usuario),
    id_recurso         INTEGER NOT NULL REFERENCES recurso_apoyo(id_recurso),
    fecha_presentacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario, id_recurso, fecha_presentacion)
);

-- ────────────────────────────────────────────────────────────────────────────────────
-- 4. ÍNDICES DE RENDIMIENTO
-- ────────────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_usuario_email        ON usuario(email);
CREATE INDEX IF NOT EXISTS idx_eval_usuario         ON evaluacion_inicial(id_usuario);
CREATE INDEX IF NOT EXISTS idx_reg_usuario_fecha    ON registro_emocional(id_usuario, fecha_registro);
CREATE INDEX IF NOT EXISTS idx_reg_nivel_riesgo     ON registro_emocional(nivel_riesgo);
CREATE INDEX IF NOT EXISTS idx_recurso_tipo         ON recurso_apoyo(id_tipo_recurso);
CREATE INDEX IF NOT EXISTS idx_pres_usuario         ON presentacion_recurso(id_usuario);
CREATE INDEX IF NOT EXISTS idx_pres_recurso         ON presentacion_recurso(id_recurso);
