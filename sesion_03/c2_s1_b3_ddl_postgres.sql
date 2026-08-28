-- =====================================================================
-- c2_s1_b3_ddl_postgres.sql
-- Sesion 2.1: el modelo de la sesion 1.2, ahora en PostgreSQL
--
-- Motor:  PostgreSQL 16 o superior
-- Base:   pagos
-- Uso:    se ejecuta desde DBeaver, o bien lo aplica el script
--         c2_s1_b4_carga.py
--
-- Este archivo es la traduccion de c1_s2_b2_ddl_modelo.sql. Las
-- diferencias respecto de la version de SQLite estan comentadas y son
-- el material de la primera parte de la sesion.
-- =====================================================================

-- El esquema agrupa los objetos del caso y evita mezclarlos con los
-- objetos del sistema. SQLite no tiene esquemas: su unidad de
-- agrupacion es el archivo.
DROP SCHEMA IF EXISTS pagos CASCADE;
CREATE SCHEMA pagos;
SET search_path TO pagos;


-- ---------------------------------------------------------------------
-- Comercios
--
-- Diferencia 1: identidad generada por el motor.
-- SQLite acepta INTEGER PRIMARY KEY y asigna el valor solo.
-- PostgreSQL lo declara de forma explicita con GENERATED AS IDENTITY,
-- que es la sintaxis del estandar. La forma antigua era SERIAL.
--
-- Diferencia 2: longitud declarada.
-- VARCHAR(n) documenta la expectativa sobre el dato. SQLite admite el
-- tipo pero no aplica el limite, porque su tipado es dinamico.
-- ---------------------------------------------------------------------
CREATE TABLE comercios (
    id_comercio INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre      VARCHAR(120) NOT NULL UNIQUE,
    categoria   VARCHAR(60)  NOT NULL,
    ciudad      VARCHAR(80)  NOT NULL
);


-- ---------------------------------------------------------------------
-- Terminales
--
-- El codigo NO es unico por si solo: se repite entre comercios de la
-- misma ciudad. La llave natural es compuesta. Este hallazgo proviene
-- de la sesion 1.2 y se conserva sin cambios.
-- ---------------------------------------------------------------------
CREATE TABLE terminales (
    id_terminal INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_comercio INTEGER      NOT NULL REFERENCES comercios (id_comercio),
    codigo      VARCHAR(30)  NOT NULL,
    UNIQUE (id_comercio, codigo)
);


-- ---------------------------------------------------------------------
-- Clientes
--
-- Diferencia 3: CITEXT no esta disponible sin extension, de modo que
-- la unicidad del correo se apoya en un indice sobre el valor en
-- minusculas. La normalizacion del valor ocurre en la carga.
-- ---------------------------------------------------------------------
CREATE TABLE clientes (
    id_cliente INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre     VARCHAR(120) NOT NULL,
    correo     VARCHAR(160) NOT NULL UNIQUE
);


-- ---------------------------------------------------------------------
-- Tarjetas
-- ---------------------------------------------------------------------
CREATE TABLE tarjetas (
    id_tarjeta INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente INTEGER     NOT NULL REFERENCES clientes (id_cliente),
    ultimos4   CHAR(4)     NOT NULL CHECK (ultimos4 ~ '^[0-9]{4}$'),
    marca      VARCHAR(20) NOT NULL
               CHECK (marca IN ('VISA', 'MASTERCARD', 'AMEX')),
    UNIQUE (id_cliente, ultimos4, marca)
);


-- ---------------------------------------------------------------------
-- Transacciones
--
-- Diferencia 4: tipos reales para fecha y para dinero.
--
-- En SQLite la fecha se guardo como TEXT y el monto como REAL, porque
-- ese motor carece de un tipo de fecha nativo y su REAL es de punto
-- flotante.
--
-- TIMESTAMP permite aritmetica de fechas y comparaciones correctas sin
-- convertir cadenas.
--
-- NUMERIC(12,2) es aritmetica decimal exacta. El punto flotante no
-- representa de forma exacta valores como 0.10, de modo que no debe
-- usarse para importes monetarios. Es la diferencia con mayor impacto
-- practico de esta sesion.
-- ---------------------------------------------------------------------
CREATE TABLE transacciones (
    id_transaccion VARCHAR(20)   PRIMARY KEY,
    fecha_hora     TIMESTAMP     NOT NULL,
    id_terminal    INTEGER       NOT NULL REFERENCES terminales (id_terminal),
    id_tarjeta     INTEGER       NOT NULL REFERENCES tarjetas (id_tarjeta),
    monto          NUMERIC(12,2) NOT NULL CHECK (monto > 0),
    moneda         CHAR(3)       NOT NULL DEFAULT 'MXN',
    estatus        VARCHAR(20)   NOT NULL
                   CHECK (estatus IN ('APROBADA', 'RECHAZADA', 'REVERSADA')),
    metodo_captura VARCHAR(20)   NOT NULL
                   CHECK (metodo_captura IN ('CHIP', 'CONTACTLESS', 'BANDA',
                                             'QR', 'MANUAL'))
);


-- ---------------------------------------------------------------------
-- Contracargos
--
-- La restriccion UNIQUE sobre la llave foranea establece la relacion de
-- cero o uno. La fecha admite nulo porque el origen no la conserva.
--
-- Diferencia 5: ON DELETE CASCADE se declara de forma explicita. Al
-- eliminar una transaccion, su contracargo se elimina con ella. En
-- SQLite el comportamiento predeterminado es rechazar el borrado.
-- ---------------------------------------------------------------------
CREATE TABLE contracargos (
    id_contracargo    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_transaccion    VARCHAR(20) NOT NULL UNIQUE
                      REFERENCES transacciones (id_transaccion)
                      ON DELETE CASCADE,
    fecha_contracargo TIMESTAMP
);


-- ---------------------------------------------------------------------
-- Indices de apoyo
--
-- PostgreSQL crea el indice de la llave primaria y el de cada
-- restriccion UNIQUE de forma automatica. Los indices sobre llaves
-- foraneas no se crean solos y hay que declararlos.
--
-- Su efecto sobre el plan de ejecucion se estudia en la sesion 2.5.
-- ---------------------------------------------------------------------
CREATE INDEX idx_transacciones_terminal ON transacciones (id_terminal);
CREATE INDEX idx_transacciones_tarjeta  ON transacciones (id_tarjeta);
CREATE INDEX idx_transacciones_fecha    ON transacciones (fecha_hora);
CREATE INDEX idx_terminales_comercio    ON terminales (id_comercio);
CREATE INDEX idx_tarjetas_cliente       ON tarjetas (id_cliente);


-- ---------------------------------------------------------------------
-- Comentarios sobre los objetos
--
-- PostgreSQL permite documentar tablas y columnas dentro de la propia
-- base. DBeaver muestra estos comentarios en el navegador de objetos.
-- La documentacion viaja con el modelo, no en un archivo aparte.
-- ---------------------------------------------------------------------
COMMENT ON TABLE  transacciones IS
    'Operaciones de pago capturadas en terminal. Tabla de hechos del caso.';
COMMENT ON COLUMN transacciones.monto IS
    'Importe en la moneda de la operacion. NUMERIC para aritmetica exacta.';
COMMENT ON COLUMN contracargos.fecha_contracargo IS
    'Nulo cuando el origen no conserva la fecha de la disputa.';
