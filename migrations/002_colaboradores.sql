-- ===========================================================================
-- EstimaIA — Migracion 002: catalogo de colaboradores (rol + costo por hora)
-- OPCIONAL: el backend crea la tabla y carga los datos semilla solo al arrancar.
-- Usar este script solo si se prefiere crearla a mano en Supabase (SQL Editor).
-- Idempotente.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS colaboradores (
    id                 SERIAL PRIMARY KEY,
    nombre             VARCHAR(120) NOT NULL,
    email              VARCHAR(150),
    rol                VARCHAR(20)  NOT NULL DEFAULT 'dev',   -- dev | qa | devops | seguridad
    seniority          VARCHAR(20)  NOT NULL DEFAULT 'mid',   -- junior | mid | senior
    tecnologias        JSON         NOT NULL DEFAULT '[]',
    disponibilidad_pct DOUBLE PRECISION NOT NULL DEFAULT 100,
    experiencia_anos   INTEGER      NOT NULL DEFAULT 0,
    costo_hora         DOUBLE PRECISION NOT NULL DEFAULT 0,   -- S/. por hora
    proyectos          JSON         NOT NULL DEFAULT '[]',
    activo             BOOLEAN      NOT NULL DEFAULT TRUE,
    updated_at         TIMESTAMP    DEFAULT NOW()
);
