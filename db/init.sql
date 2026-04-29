-- ─────────────────────────────────────────────────────────────
--  db/init.sql  —  Esquema inicial  (Inmobiliaria)
--  Se ejecuta automáticamente la primera vez que arranca el
--  contenedor postgres (docker-entrypoint-initdb.d).
-- ─────────────────────────────────────────────────────────────

-- ── Usuario ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Usuario" (
    id         SERIAL PRIMARY KEY,
    nombre     VARCHAR(100)  NOT NULL,
    correo     VARCHAR(100)  NOT NULL UNIQUE,
    telefono   VARCHAR(20),
    password   VARCHAR(255)  NOT NULL,
    rol        VARCHAR(50)   NOT NULL,
    estado     VARCHAR(20)   NOT NULL DEFAULT 'activo'
);

-- ── Ubicación ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Ubicacion" (
    id                 SERIAL PRIMARY KEY,
    direccion_completa TEXT          NOT NULL,
    latitud            DECIMAL(10,6),
    longitud           DECIMAL(10,6),
    estado             VARCHAR(100),
    ciudad             VARCHAR(100),
    colonia            VARCHAR(100),
    calle              VARCHAR(100),
    numero_exterior    VARCHAR(20),
    numero_interior    VARCHAR(20),
    codigo_postal      VARCHAR(20)
);

-- ── Inmueble ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Inmueble" (
    id                   SERIAL PRIMARY KEY,
    titulo               VARCHAR(150)   NOT NULL,
    descripcion          TEXT,
    precio               DECIMAL(12,2)  NOT NULL,
    tipo                 VARCHAR(50)    NOT NULL,
    estado               VARCHAR(50)    NOT NULL DEFAULT 'disponible',
    propietario_id       INTEGER        NOT NULL REFERENCES "Usuario"(id),
    ubicacion_id         INTEGER        REFERENCES "Ubicacion"(id),
    area_construccion    DECIMAL(10,2),
    area_terreno         DECIMAL(10,2),
    num_recamaras        INTEGER,
    num_banos            INTEGER,
    num_estacionamientos INTEGER,
    niveles              INTEGER,
    amueblado            BOOLEAN        DEFAULT FALSE
);

-- ── Contrato ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Contrato" (
    id           SERIAL PRIMARY KEY,
    fecha_inicio DATE           NOT NULL,
    fecha_fin    DATE,
    tipo         VARCHAR(50)    NOT NULL,
    monto        DECIMAL(12,2)  NOT NULL,
    estado       VARCHAR(50)    NOT NULL DEFAULT 'activo',
    url_archivo  TEXT,
    usuario_id   INTEGER        NOT NULL REFERENCES "Usuario"(id),
    inmueble_id  INTEGER        NOT NULL REFERENCES "Inmueble"(id)
);

-- ── Pago ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Pago" (
    id           SERIAL PRIMARY KEY,
    monto        DECIMAL(12,2)  NOT NULL,
    fecha        TIMESTAMP      NOT NULL DEFAULT NOW(),
    metodo       VARCHAR(50)    NOT NULL,
    estado       VARCHAR(50)    NOT NULL DEFAULT 'pendiente',
    contrato_id  INTEGER        NOT NULL REFERENCES "Contrato"(id)
);

-- ── Clausula ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Clausula" (
    id           SERIAL PRIMARY KEY,
    descripcion  TEXT    NOT NULL,
    id_contrato  INTEGER NOT NULL REFERENCES "Contrato"(id)
);

-- ── Imagen ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Imagen" (
    id           SERIAL PRIMARY KEY,
    url_archivo  TEXT    NOT NULL,
    inmueble_id  INTEGER NOT NULL REFERENCES "Inmueble"(id)
);

-- ── Visita ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Visita" (
    id           SERIAL PRIMARY KEY,
    fecha        TIMESTAMP    NOT NULL,
    estado       VARCHAR(50)  NOT NULL DEFAULT 'programada',
    usuario_id   INTEGER      NOT NULL REFERENCES "Usuario"(id),
    inmueble_id  INTEGER      NOT NULL REFERENCES "Inmueble"(id)
);

-- ── HistorialEstado ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "HistorialEstado" (
    id           SERIAL PRIMARY KEY,
    fecha_inicio TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado       VARCHAR(50)  NOT NULL,
    fecha_fin    TIMESTAMP,
    id_inmueble  INTEGER      NOT NULL REFERENCES "Inmueble"(id)
);

-- ── Contacto ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Contacto" (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100)  NOT NULL,
    correo      VARCHAR(100)  NOT NULL,
    mensaje     TEXT,
    fecha       TIMESTAMP     NOT NULL DEFAULT NOW(),
    id_inmueble INTEGER       NOT NULL REFERENCES "Inmueble"(id)
);
