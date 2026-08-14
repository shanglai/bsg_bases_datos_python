-- =====================================================================
-- c1_s2_b2_ddl_modelo.sql
-- Sesion 1.2: definicion del modelo normalizado
--
-- Motor:  SQLite
-- Salida: base pagos_normalizado.db con seis tablas
-- Uso:    lo ejecuta el script c1_s2_b3_migracion.py
--         o bien se corre a mano contra una base vacia
--
-- Corresponde al diagrama c1_s2_d2_modelo_logico.png
-- =====================================================================

-- SQLite no aplica las llaves foraneas de forma predeterminada.
-- Esta instruccion debe emitirse en cada conexion.
PRAGMA foreign_keys = ON;


-- ---------------------------------------------------------------------
-- Catalogo de comercios
--
-- La restriccion UNIQUE sobre el nombre es el mecanismo que impide
-- que un mismo comercio vuelva a registrarse bajo varias escrituras.
-- En el archivo plano existian diecisiete valores para siete comercios.
-- ---------------------------------------------------------------------
CREATE TABLE comercios (
    id_comercio INTEGER PRIMARY KEY,
    nombre      TEXT NOT NULL UNIQUE,
    categoria   TEXT NOT NULL,
    ciudad      TEXT NOT NULL
);


-- ---------------------------------------------------------------------
-- Terminales
--
-- Una terminal pertenece a un solo comercio. La llave foranea traslada
-- esa regla de negocio al motor: no es posible registrar una terminal
-- de un comercio que no existe.
--
-- El codigo de terminal NO es unico por si solo. En el archivo plano,
-- dos comercios de la misma ciudad comparten codigos como 'TPV01-CIU'.
-- La llave natural es compuesta: el codigo es unico dentro del comercio.
-- Declarar UNIQUE sobre el codigo solo habria fusionado terminales de
-- comercios distintos y trasladado transacciones al comercio equivocado.
-- ---------------------------------------------------------------------
CREATE TABLE terminales (
    id_terminal INTEGER PRIMARY KEY,
    id_comercio INTEGER NOT NULL,
    codigo      TEXT NOT NULL,
    UNIQUE (id_comercio, codigo),
    FOREIGN KEY (id_comercio) REFERENCES comercios (id_comercio)
);


-- ---------------------------------------------------------------------
-- Clientes
--
-- El correo se declara unico. En el archivo plano el mismo dato de
-- contacto se repetia en cada fila del cliente, de modo que corregir
-- un correo implicaba modificar cientos de filas.
-- ---------------------------------------------------------------------
CREATE TABLE clientes (
    id_cliente INTEGER PRIMARY KEY,
    nombre     TEXT NOT NULL,
    correo     TEXT NOT NULL UNIQUE
);


-- ---------------------------------------------------------------------
-- Tarjetas
--
-- Un cliente puede tener varias tarjetas. La restriccion CHECK limita
-- el dominio de la marca a los valores admitidos.
-- ---------------------------------------------------------------------
CREATE TABLE tarjetas (
    id_tarjeta INTEGER PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    ultimos4   TEXT NOT NULL,
    marca      TEXT NOT NULL CHECK (marca IN ('VISA', 'MASTERCARD', 'AMEX')),
    FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
);


-- ---------------------------------------------------------------------
-- Transacciones
--
-- Entidad central del modelo. Conserva el identificador original del
-- sistema operativo, de modo que la trazabilidad hacia el archivo de
-- origen se mantiene.
-- ---------------------------------------------------------------------
CREATE TABLE transacciones (
    id_transaccion TEXT PRIMARY KEY,
    fecha_hora     TEXT NOT NULL,
    id_terminal    INTEGER NOT NULL,
    id_tarjeta     INTEGER NOT NULL,
    monto          REAL NOT NULL CHECK (monto > 0),
    moneda         TEXT NOT NULL DEFAULT 'MXN',
    estatus        TEXT NOT NULL
                   CHECK (estatus IN ('APROBADA', 'RECHAZADA', 'REVERSADA')),
    metodo_captura TEXT NOT NULL
                   CHECK (metodo_captura IN ('CHIP', 'CONTACTLESS', 'BANDA',
                                             'QR', 'MANUAL')),
    FOREIGN KEY (id_terminal) REFERENCES terminales (id_terminal),
    FOREIGN KEY (id_tarjeta)  REFERENCES tarjetas (id_tarjeta)
);


-- ---------------------------------------------------------------------
-- Contracargos
--
-- Un contracargo existe solo si existe la transaccion que lo motiva.
-- La restriccion UNIQUE sobre la llave foranea establece la relacion
-- de cero o uno: una transaccion no puede tener dos contracargos.
--
-- La columna fecha_contracargo admite nulo porque el archivo plano de
-- origen no conserva ese dato. La perdida de informacion es un hallazgo
-- del ejercicio de modelado.
-- ---------------------------------------------------------------------
CREATE TABLE contracargos (
    id_contracargo    INTEGER PRIMARY KEY,
    id_transaccion    TEXT NOT NULL UNIQUE,
    fecha_contracargo TEXT,
    FOREIGN KEY (id_transaccion) REFERENCES transacciones (id_transaccion)
);


-- ---------------------------------------------------------------------
-- Indices de apoyo
--
-- Los indices sobre llaves foraneas aceleran las combinaciones que se
-- usaran a partir de la sesion 2.2. El estudio del plan de ejecucion
-- y la medicion de su efecto corresponden a la sesion 2.5.
-- ---------------------------------------------------------------------
CREATE INDEX idx_transacciones_terminal ON transacciones (id_terminal);
CREATE INDEX idx_transacciones_tarjeta  ON transacciones (id_tarjeta);
CREATE INDEX idx_transacciones_fecha    ON transacciones (fecha_hora);
CREATE INDEX idx_terminales_comercio    ON terminales (id_comercio);
CREATE INDEX idx_tarjetas_cliente       ON tarjetas (id_cliente);
