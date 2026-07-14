-- ===========================================================================
-- EstimaIA — Migracion 001: tabla projects para el modulo de reentrenamiento
-- Ejecutar UNA VEZ en Supabase (SQL Editor).
-- Idempotente: se puede correr varias veces sin romper nada.
-- ===========================================================================

-- 1) Crear la tabla si no existe
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR NOT NULL
);

-- 2) Agregar/asegurar todas las columnas del modelo
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS empresa                 VARCHAR,
    ADD COLUMN IF NOT EXISTS tipo_sistema            VARCHAR,
    ADD COLUMN IF NOT EXISTS tecnologia_principal    VARCHAR,
    ADD COLUMN IF NOT EXISTS num_modulos             INTEGER,
    ADD COLUMN IF NOT EXISTS complejidad             INTEGER,
    ADD COLUMN IF NOT EXISTS tamano_equipo           INTEGER,
    ADD COLUMN IF NOT EXISTS num_tareas_asana        INTEGER,
    ADD COLUMN IF NOT EXISTS duracion_estimada_dias  INTEGER,
    ADD COLUMN IF NOT EXISTS duracion_real_dias      INTEGER,
    ADD COLUMN IF NOT EXISTS start_on                DATE,
    ADD COLUMN IF NOT EXISTS completed_at            DATE,
    ADD COLUMN IF NOT EXISTS esfuerzo_estimado_horas DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS esfuerzo_real_horas     DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS estado                  VARCHAR DEFAULT 'estimado' NOT NULL,
    ADD COLUMN IF NOT EXISTS sincerado               BOOLEAN DEFAULT FALSE NOT NULL,
    ADD COLUMN IF NOT EXISTS incluir_en_training     BOOLEAN DEFAULT TRUE  NOT NULL,
    ADD COLUMN IF NOT EXISTS fecha_sincerado         TIMESTAMP,
    ADD COLUMN IF NOT EXISTS sincerado_por           VARCHAR;

-- 3) IMPORTANTE: si la tabla ya existia con NOT NULL en estas columnas,
--    liberarlas. El modelo las llena al estimar, pero deben permitir NULL
--    para no romper filas antiguas.
ALTER TABLE projects ALTER COLUMN tecnologia_principal DROP NOT NULL;
ALTER TABLE projects ALTER COLUMN num_modulos          DROP NOT NULL;

-- 4) Indices para las consultas del modulo de sinceracion/reentrenamiento
CREATE INDEX IF NOT EXISTS ix_projects_sincerado
    ON projects (sincerado);
CREATE INDEX IF NOT EXISTS ix_projects_training
    ON projects (sincerado, incluir_en_training);

-- 5) Verificacion
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'projects'
ORDER BY ordinal_position;
