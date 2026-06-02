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
    is_admin   BOOLEAN   NOT NULL DEFAULT FALSE,
    is_active  BOOLEAN   NOT NULL DEFAULT TRUE
);

-- ── EstadoRepublica ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "EstadoRepublica" (
    id           SERIAL PRIMARY KEY,
    valor        VARCHAR(50) UNIQUE NOT NULL
);
INSERT INTO "EstadoRepublica" (valor) VALUES ('Aguascalientes'), ('Baja California'), ('Baja California Sur'), ('Campeche'), ('Chiapas'),
('Chihuahua'), ('Ciudad de Mexico'), ('Coahuila'), ('Colima'),('Durango'),('Estado de Mexico'), ('Guanajuato'), ('Guerrero'),('Hidalgo'),
('Jalisco'),('Michoacan'),('Morelos'),('Nayarit'),('Nuevo Leon'),('Oaxaca'), ('Puebla'),('Queretaro'),('Quintana Roo'),('San Luis Potosi'),
('Sinaloa'),('Sonora'),('Tabasco'),('Tamaulipas'),('Tlaxcala'),('Veracruz'),('Yucatan'),('Zacatecas')
ON CONFLICT DO NOTHING;


-- ── Ubicación ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Ubicacion" (
    id                 SERIAL PRIMARY KEY,
    latitud            DECIMAL(10,6),
    longitud           DECIMAL(10,6),
    estado_id          INTEGER NOT NULL REFERENCES "EstadoRepublica"(id),
    ciudad             VARCHAR(100),
    colonia            VARCHAR(100),
    calle              VARCHAR(100),
    numero_exterior    VARCHAR(20),
    numero_interior    VARCHAR(20),
    codigo_postal      VARCHAR(20)
);

CREATE VIEW "VistaUbicacionCompleta" AS
SELECT
    u.id,
    CONCAT(
        u.calle, ' ',
        u.numero_exterior,
        ', ',
        u.colonia,
        ', ',
        u.ciudad,
        ', ',
        e.valor,
        ', CP ',
        u.codigo_postal
    ) AS direccion_completa
FROM "Ubicacion" u
JOIN "EstadoRepublica" e
ON u.estado_id = e.id;


-- ── EstadoInmueble ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "EstadoInmueble" (
    id           SERIAL PRIMARY KEY,
    valor        VARCHAR(50) UNIQUE NOT NULL DEFAULT 'en venta'
);
INSERT INTO "EstadoInmueble" (valor) VALUES ('en venta'), ('vendido'), ('en renta'), ('rentado'), ('reservado'), ('no disponible')
ON CONFLICT DO NOTHING;

-- ── TipoInmueble ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "TipoInmueble" (
    id           SERIAL PRIMARY KEY,
    valor        VARCHAR(50) UNIQUE NOT NULL DEFAULT 'departamento'
);
INSERT INTO "TipoInmueble" (valor) VALUES ('departamento'), ('casa'), ('edificio'), ('mansion'), ('cabaña'), ('local comercial'), ('terreno'), ('casa en condiminio'), ('bodega comercial'), ('departamento compartido'), ('duplex'), ('huerta'), ('local de centro comercial'),('oficina'), ('quinta'), ('rancho'), ('terreno comercial'), ('terreno industrial'), ('villa')
ON CONFLICT DO NOTHING;


-- ── Inmueble ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Inmueble" (
    id                   SERIAL PRIMARY KEY,
    titulo               VARCHAR(150)   NOT NULL,
    descripcion          TEXT,
    precio               DECIMAL(12,2)  NOT NULL,
    tipo_id              INTEGER        NOT NULL REFERENCES "TipoInmueble"(id),
    estado_id            INTEGER        NOT NULL REFERENCES "EstadoInmueble"(id),
    propietario_id       INTEGER        REFERENCES "Usuario"(id),
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
    descripcion  TEXT   NOT NULL,
    inmueble_id  INTEGER NOT NULL REFERENCES "Inmueble"(id)
);


-- ── Estado Visita ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "EstadoVisita" (
    id           SERIAL PRIMARY KEY,
    valor        VARCHAR(50) UNIQUE NOT NULL DEFAULT 'programada'
);

INSERT INTO "EstadoVisita" (valor) VALUES ('programada'), ('cancelada'), ('completada')
ON CONFLICT DO NOTHING;


-- ── Visita ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Visita" (
    id           SERIAL PRIMARY KEY,
    fecha        TIMESTAMP    NOT NULL,
    estado_id    INTEGER      NOT NULL REFERENCES "EstadoVisita"(id),
    usuario_id   INTEGER      NOT NULL REFERENCES "Usuario"(id),
    inmueble_id  INTEGER      NOT NULL REFERENCES "Inmueble"(id)
);


-- ── HistorialEstado ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "HistorialEstado" (
    id           SERIAL PRIMARY KEY,
    fecha_inicio TIMESTAMP    DEFAULT NOW(),
    estado_id    INTEGER  NOT NULL REFERENCES "EstadoInmueble"(id),
    fecha_fin    TIMESTAMP,
    inmueble_id  INTEGER      NOT NULL REFERENCES "Inmueble"(id)
);

-- ── HistorialPropietario ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "HistorialPropietario" (
    id               SERIAL PRIMARY KEY,
    inmueble_id      INTEGER NOT NULL REFERENCES "Inmueble"(id),
    propietario_id   INTEGER NOT NULL REFERENCES "Usuario"(id),
    fecha_inicio     TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_fin        TIMESTAMP
);

-- ── Contacto ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Contacto" (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100)  NOT NULL,
    correo      VARCHAR(100)  NOT NULL,
    mensaje     TEXT,
    fecha       TIMESTAMP     DEFAULT NOW(),
    inmueble_id INTEGER       NOT NULL REFERENCES "Inmueble"(id)
);
