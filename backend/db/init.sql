
-- ── Usuario 
CREATE TABLE IF NOT EXISTS "Usuario" (
    id         SERIAL PRIMARY KEY,
    nombre     VARCHAR(100)  NOT NULL,
    correo     VARCHAR(100)  NOT NULL UNIQUE,
    telefono   VARCHAR(20)   UNIQUE,
    password   VARCHAR(255)  NOT NULL,
    is_admin   BOOLEAN   NOT NULL DEFAULT FALSE,
    is_active  BOOLEAN   NOT NULL DEFAULT TRUE
);

-- ── Administrador inicial (seed) ──────────────────────────────────────
-- Credenciales por defecto: admin@propify.com / Admin1234
-- El hash es bcrypt de 'Admin1234'.
INSERT INTO "Usuario" (nombre, correo, telefono, password, is_admin, is_active)
VALUES (
    'Administrador',
    'admin@propify.com',
    NULL,
    '$2b$12$lgryabEiKCZ6JILnwLg/mOqmjQar3JRmrWfJJqyGs2msckUQFiMvW',
    TRUE,
    TRUE
)
ON CONFLICT (correo) DO NOTHING;

-- ── EstadoRepublica ──────────────────────────────────────────────────
-- Catálogo de estados de México para poblar el selector del frontend.
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


-- ── Catálogos de inmueble ────────────────────────
CREATE TABLE IF NOT EXISTS "EstadoInmueble" (
    id    SERIAL PRIMARY KEY,
    valor VARCHAR(50) UNIQUE NOT NULL DEFAULT 'en venta'
);
INSERT INTO "EstadoInmueble" (valor) VALUES
    ('en venta'), ('vendido'), ('en renta'), ('rentado'), ('reservado'), ('no disponible')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS "TipoInmueble" (
    id    SERIAL PRIMARY KEY,
    valor VARCHAR(50) UNIQUE NOT NULL DEFAULT 'departamento'
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
    ubicacion_id         INTEGER        NOT NULL REFERENCES "Ubicacion"(id),
    area_construccion    DECIMAL(12,2),
    area_terreno         DECIMAL(12,2),
    num_recamaras        INTEGER,
    num_banos            INTEGER,
    num_estacionamientos INTEGER,
    niveles              INTEGER,
    amueblado            BOOLEAN        DEFAULT FALSE
);

-- ── Contrato ──────────────────────────────────────────────────
-- tipo = operación (Venta | Renta).
-- url_archivo  = documento ORIGINAL generado por el sistema.
-- url_firmado  = documento FIRMADO subido por cliente/administrador.
-- Trazabilidad: fecha_generacion, fecha_descarga, fecha_firma_subida.
CREATE TABLE IF NOT EXISTS "Contrato" (
    id                 SERIAL PRIMARY KEY,
    fecha_inicio       DATE           NOT NULL,
    fecha_fin          DATE,
    tipo               VARCHAR(50)    NOT NULL
                       CHECK (tipo IN ('Venta','Renta')),
    monto              DECIMAL(12,2)  NOT NULL CHECK (monto > 0),
    estado             VARCHAR(50)    NOT NULL DEFAULT 'activo'
                       CHECK (estado IN ('borrador','pendiente_de_firma','firmado',
                                         'activo','finalizado','cancelado','liquidado')),
    folio              VARCHAR(30)    UNIQUE,
    -- Validación de la documentación firmada por parte del administrador.
    estado_documento   VARCHAR(20)    NOT NULL DEFAULT 'pendiente'
                       CHECK (estado_documento IN ('pendiente','aprobado','rechazado')),
    motivo_rechazo     TEXT,
    condiciones        TEXT,          -- condiciones especiales / observaciones
    contrato_padre_id  INTEGER        REFERENCES "Contrato"(id),  -- renovaciones
    url_archivo        TEXT,
    url_firmado        TEXT,
    fecha_generacion   TIMESTAMP      NOT NULL DEFAULT NOW(),
    fecha_descarga     TIMESTAMP,
    fecha_firma_subida TIMESTAMP,
    usuario_id         INTEGER        NOT NULL REFERENCES "Usuario"(id),
    inmueble_id        INTEGER        NOT NULL REFERENCES "Inmueble"(id)
);

--  Pago
-- fecha_vencimiento + numero_cuota: para el calendario mensual de renta.
CREATE TABLE IF NOT EXISTS "Pago" (
    id                 SERIAL PRIMARY KEY,
    monto              DECIMAL(12,2)  NOT NULL,
    fecha              TIMESTAMP,
    fecha_vencimiento  DATE,
    numero_cuota       INTEGER,
    metodo             VARCHAR(50),
    estado             VARCHAR(50)    NOT NULL DEFAULT 'pendiente'
                       CHECK (estado IN ('pendiente','pagado','vencido','cancelado','reembolsado')),
    contrato_id        INTEGER        NOT NULL REFERENCES "Contrato"(id),
    usuario_id         INTEGER,                 -- quién realizó/registró el pago
    ip                 VARCHAR(45),             -- IP de origen cuando esté disponible
    stripe_session_id  VARCHAR(255),
    stripe_payment_intent VARCHAR(255)          -- id de transacción de la pasarela
);

--  Clausula
CREATE TABLE IF NOT EXISTS "Clausula" (
    id           SERIAL PRIMARY KEY,
    descripcion  TEXT    NOT NULL,
    id_contrato  INTEGER NOT NULL REFERENCES "Contrato"(id)
);

-- Imagen (descripcion = texto alternativo accesible, WCAG 1.1.1)
CREATE TABLE IF NOT EXISTS "Imagen" (
    id           SERIAL PRIMARY KEY,
    url_archivo  TEXT    NOT NULL,
    descripcion  TEXT    NOT NULL,
    inmueble_id  INTEGER NOT NULL REFERENCES "Inmueble"(id)
);

-- ── Estado Visita ────────────────────────────────────────────────────
-- Ids fijos (orden de inserción): 1 programada, 2 confirmada, 3 realizada,
-- 4 cancelada, 5 no asistio. Los ids 1 y 2 son los estados "activos" que
-- ocupan un horario (ver índice de solapamiento más abajo).
CREATE TABLE IF NOT EXISTS "EstadoVisita" (
    id           SERIAL PRIMARY KEY,
    valor        VARCHAR(50) UNIQUE NOT NULL DEFAULT 'programada'
);

INSERT INTO "EstadoVisita" (valor) VALUES
    ('programada'), ('confirmada'), ('realizada'), ('cancelada'), ('no asistio')
ON CONFLICT DO NOTHING;


-- ── Visita ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Visita" (
    id           SERIAL PRIMARY KEY,
    fecha        TIMESTAMP    NOT NULL,
    estado_id    INTEGER      NOT NULL REFERENCES "EstadoVisita"(id),
    usuario_id   INTEGER      NOT NULL REFERENCES "Usuario"(id),
    inmueble_id  INTEGER      NOT NULL REFERENCES "Inmueble"(id)
);

-- Integridad a nivel BD: un inmueble no puede tener dos visitas ACTIVAS
-- (programada=1, confirmada=2) en la misma fecha y hora. Índice parcial:
-- permite reutilizar el horario si la visita previa fue cancelada/realizada.
CREATE UNIQUE INDEX IF NOT EXISTS uq_visita_inmueble_fecha_activa
    ON "Visita" (inmueble_id, fecha)
    WHERE estado_id IN (1, 2);

-- ── HistorialEstado ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "HistorialEstado" (
    id           SERIAL PRIMARY KEY,
    fecha_inicio TIMESTAMP    DEFAULT NOW(),
    fecha_fin    TIMESTAMP,
    estado_id    INTEGER      NOT NULL REFERENCES "EstadoInmueble"(id),
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

--Contacto
CREATE TABLE IF NOT EXISTS "Contacto" (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100)  NOT NULL,
    correo      VARCHAR(100)  NOT NULL,
    mensaje     TEXT,
    fecha       TIMESTAMP     DEFAULT NOW(),
    inmueble_id INTEGER       NOT NULL REFERENCES "Inmueble"(id)
);

-- ── SolicitudRenta ────────────────────────────────────────────
-- Flujo de renta en línea iniciado por el cliente.
CREATE TABLE IF NOT EXISTS "SolicitudRenta" (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER     NOT NULL REFERENCES "Usuario"(id),
    inmueble_id     INTEGER     NOT NULL REFERENCES "Inmueble"(id),
    fecha_solicitud TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente','en revision','aprobada','rechazada','cancelada')),
    tipo_operacion  VARCHAR(10) NOT NULL DEFAULT 'renta'
                    CHECK (tipo_operacion IN ('renta','venta')),
    fecha_inicio    DATE,
    fecha_fin       DATE,
    duracion_meses  INTEGER,
    mensaje         TEXT,
    contrato_id     INTEGER     REFERENCES "Contrato"(id)
);

-- ── Comprobante de pago ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Comprobante" (
    id           SERIAL PRIMARY KEY,
    contrato_id  INTEGER   NOT NULL REFERENCES "Contrato"(id),
    pago_id      INTEGER   REFERENCES "Pago"(id),
    url_archivo  TEXT      NOT NULL,
    usuario_id   INTEGER   NOT NULL REFERENCES "Usuario"(id),
    fecha_carga  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── Auditoría (bitácora de acciones relevantes) ───────────────
CREATE TABLE IF NOT EXISTS "Auditoria" (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER,
    accion          VARCHAR(100) NOT NULL,
    entidad         VARCHAR(50),
    entidad_id      INTEGER,
    valor_anterior  TEXT,
    valor_nuevo     TEXT,
    detalle         TEXT,
    fecha           TIMESTAMP    NOT NULL DEFAULT NOW()
);
