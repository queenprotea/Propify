
-- ------------------------------------------------------------
-- USUARIO
-- ------------------------------------------------------------
CREATE TABLE usuario (
                         id          SERIAL PRIMARY KEY,
                         correo      VARCHAR(255) NOT NULL UNIQUE,
                         nombre      VARCHAR(255) NOT NULL,
                         password    VARCHAR(255) NOT NULL,
                         rol         VARCHAR(50)  NOT NULL,
                         telefono    VARCHAR(20)
);

-- ------------------------------------------------------------
-- UBICACION
-- ------------------------------------------------------------
CREATE TABLE ubicacion (
                           id                   SERIAL PRIMARY KEY,
                           calle                VARCHAR(255),
                           ciudad               VARCHAR(100),
                           codigo_postal        VARCHAR(10),
                           colonia              VARCHAR(100),
                           direccion_completa   TEXT,
                           estado               VARCHAR(100),
                           latitud              DOUBLE PRECISION,
                           longitud             DOUBLE PRECISION,
                           numero_exterior      VARCHAR(20),
                           numero_interior      VARCHAR(20)
);

-- ------------------------------------------------------------
-- INMUEBLE
-- ------------------------------------------------------------
CREATE TABLE inmueble (
                          id                      SERIAL PRIMARY KEY,
                          amueblado               BOOLEAN          DEFAULT FALSE,
                          area_construccion       DOUBLE PRECISION,
                          area_terreno            DOUBLE PRECISION,
                          descripcion             TEXT,
                          estado                  VARCHAR(50),
                          niveles                 INTEGER,
                          num_banos               INTEGER,
                          num_estacionamientos    INTEGER,
                          num_recamaras           INTEGER,
                          precio                  DOUBLE PRECISION,
                          tipo                    VARCHAR(50),
                          titulo                  VARCHAR(255),

                          ubicacion_id            INTEGER UNIQUE REFERENCES ubicacion(id) ON DELETE SET NULL,

                          propietario_id          INTEGER        REFERENCES usuario(id)   ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- CONTRATO
-- ------------------------------------------------------------
CREATE TABLE contrato (
                          id            SERIAL PRIMARY KEY,
                          estado        VARCHAR(50),
                          fecha_fin     TIMESTAMP,
                          fecha_inicio  TIMESTAMP,
                          monto         DOUBLE PRECISION,
                          tipo          VARCHAR(50),
                          url_archivo   VARCHAR(500),

                          inmueble_id   INTEGER REFERENCES inmueble(id) ON DELETE RESTRICT,

                          usuario_id    INTEGER REFERENCES usuario(id)  ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- PAGO
-- ------------------------------------------------------------
CREATE TABLE pago (
                      id           SERIAL PRIMARY KEY,
                      estado       VARCHAR(50),
                      fecha        TIMESTAMP,
                      metodo       VARCHAR(50),
                      monto        DOUBLE PRECISION,

                      contrato_id  INTEGER NOT NULL REFERENCES contrato(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- CLAUSULA
-- ------------------------------------------------------------
CREATE TABLE clausula (
                          id           SERIAL PRIMARY KEY,
                          descripcion  TEXT
);

-- ------------------------------------------------------------
-- CONTRATO_CLAUSULA
-- ------------------------------------------------------------
CREATE TABLE contrato_clausula (
                                   contrato_id  INTEGER NOT NULL REFERENCES contrato(id) ON DELETE CASCADE,
                                   clausula_id  INTEGER NOT NULL REFERENCES clausula(id) ON DELETE CASCADE,
                                   PRIMARY KEY (contrato_id, clausula_id)
);

-- ------------------------------------------------------------
-- IMAGEN
-- ------------------------------------------------------------
CREATE TABLE imagen (
                        id           SERIAL PRIMARY KEY,
                        url          VARCHAR(500),

                        inmueble_id  INTEGER NOT NULL REFERENCES inmueble(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- VISITA
-- ------------------------------------------------------------
CREATE TABLE visita (
                        id           SERIAL PRIMARY KEY,
                        estado       VARCHAR(50),
                        fecha        TIMESTAMP,

                        usuario_id   INTEGER REFERENCES usuario(id)  ON DELETE SET NULL,

                        inmueble_id  INTEGER REFERENCES inmueble(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- HISTORIAL_ESTADO
-- ------------------------------------------------------------
CREATE TABLE historial_estado (
                                  id            SERIAL PRIMARY KEY,
                                  estado        VARCHAR(50),
                                  fecha_fin     TIMESTAMP,
                                  fecha_inicio  TIMESTAMP,

                                  inmueble_id   INTEGER NOT NULL REFERENCES inmueble(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- CONTACTO
-- ------------------------------------------------------------
CREATE TABLE contacto (
                          id           SERIAL PRIMARY KEY,
                          correo       VARCHAR(255),
                          fecha        TIMESTAMP,
                          mensaje      TEXT,
                          nombre       VARCHAR(255),

                          inmueble_id  INTEGER NOT NULL REFERENCES inmueble(id) ON DELETE CASCADE
);
