-- =====================================================================
-- c1_s2_b4_verificacion.sql
-- Sesion 1.2: comprobacion del modelo normalizado
--
-- Motor: SQLite
-- Base:  pagos_normalizado.db, seis tablas
-- Uso:   despues de ejecutar c1_s2_b3_migracion.py
-- =====================================================================

PRAGMA foreign_keys = ON;

.headers on
.mode column


-- ---------------------------------------------------------------------
-- Bloque A. Estructura resultante
-- ---------------------------------------------------------------------

-- A1. Tablas creadas.
SELECT name
FROM sqlite_master
WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
ORDER BY name;

-- A2. Volumen de cada tabla.
SELECT 'comercios'     AS tabla, COUNT(*) AS filas FROM comercios
UNION ALL SELECT 'terminales',    COUNT(*) FROM terminales
UNION ALL SELECT 'clientes',      COUNT(*) FROM clientes
UNION ALL SELECT 'tarjetas',      COUNT(*) FROM tarjetas
UNION ALL SELECT 'transacciones', COUNT(*) FROM transacciones
UNION ALL SELECT 'contracargos',  COUNT(*) FROM contracargos;

-- A3. Llaves foraneas declaradas en la tabla de hechos.
PRAGMA foreign_key_list(transacciones);


-- ---------------------------------------------------------------------
-- Bloque B. El problema de la sesion 1.1, ya resuelto
-- ---------------------------------------------------------------------

-- B1. El catalogo contiene un registro por comercio real.
SELECT id_comercio, nombre, categoria, ciudad
FROM comercios
ORDER BY id_comercio;

-- B2. El volumen por comercio ya no se reparte entre variantes.
--     Compara este resultado con el bloque D2 de la sesion 1.1.
SELECT c.nombre,
       COUNT(*)              AS operaciones,
       ROUND(SUM(t.monto),2) AS importe_total
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
GROUP BY c.nombre
ORDER BY operaciones DESC;

-- B3. El correo de un cliente reside en un solo lugar.
SELECT id_cliente, nombre, correo
FROM clientes
ORDER BY id_cliente
LIMIT 5;


-- ---------------------------------------------------------------------
-- Bloque C. El motor rechaza lo que antes era posible
--
-- Las cuatro sentencias siguientes deben fallar. Ejecutalas una por una
-- y registra el mensaje de error que devuelve el motor.
-- ---------------------------------------------------------------------

-- C1. Nombre de comercio duplicado. Falla por la restriccion UNIQUE.
-- INSERT INTO comercios (nombre, categoria, ciudad)
-- VALUES ('Super Norteno', 'Supermercado', 'Monterrey');

-- C2. Terminal de un comercio inexistente. Falla por la llave foranea.
-- INSERT INTO terminales (id_comercio, codigo)
-- VALUES (999, 'TPV99-XXX');

-- C3. Monto negativo. Falla por la restriccion CHECK.
-- INSERT INTO transacciones
--   (id_transaccion, fecha_hora, id_terminal, id_tarjeta, monto, moneda,
--    estatus, metodo_captura)
-- VALUES ('TRX9999999', '2026-07-01 10:00:00', 1, 1, -500, 'MXN',
--         'APROBADA', 'CHIP');

-- C4. Estatus fuera del dominio permitido. Falla por la restriccion CHECK.
-- INSERT INTO transacciones
--   (id_transaccion, fecha_hora, id_terminal, id_tarjeta, monto, moneda,
--    estatus, metodo_captura)
-- VALUES ('TRX9999998', '2026-07-01 10:00:00', 1, 1, 500, 'MXN',
--         'PENDIENTE', 'CHIP');


-- ---------------------------------------------------------------------
-- Bloque D. Comprobaciones de integridad
-- ---------------------------------------------------------------------

-- D1. Verificacion global de llaves foraneas. Debe devolver cero filas.
PRAGMA foreign_key_check;

-- D2. Ninguna transaccion debe quedar sin terminal o sin tarjeta.
SELECT COUNT(*) AS transacciones_huerfanas
FROM transacciones t
LEFT JOIN terminales te ON te.id_terminal = t.id_terminal
LEFT JOIN tarjetas   ta ON ta.id_tarjeta  = t.id_tarjeta
WHERE te.id_terminal IS NULL OR ta.id_tarjeta IS NULL;

-- D3. Todo contracargo debe apuntar a una transaccion aprobada.
SELECT COUNT(*) AS contracargos_inconsistentes
FROM contracargos cc
JOIN transacciones t ON t.id_transaccion = cc.id_transaccion
WHERE t.estatus <> 'APROBADA';

-- D4. Ninguna terminal debe quedar sin comercio.
SELECT COUNT(*) AS terminales_huerfanas
FROM terminales te
LEFT JOIN comercios c ON c.id_comercio = te.id_comercio
WHERE c.id_comercio IS NULL;


-- ---------------------------------------------------------------------
-- Bloque E. Lo que el modelo dejo al descubierto
-- ---------------------------------------------------------------------

-- E1. El codigo de terminal se repite entre comercios distintos.
--     Por eso la llave natural de terminal es compuesta.
SELECT codigo, COUNT(DISTINCT id_comercio) AS comercios_que_lo_usan
FROM terminales
GROUP BY codigo
HAVING COUNT(DISTINCT id_comercio) > 1
ORDER BY comercios_que_lo_usan DESC;

-- E2. La fecha del contracargo no existe en el origen.
--     El archivo plano solo registraba una marca de si o no.
SELECT COUNT(*)                                          AS total_contracargos,
       SUM(CASE WHEN fecha_contracargo IS NULL THEN 1
                ELSE 0 END)                               AS sin_fecha
FROM contracargos;

-- E3. Un mismo nombre de cliente puede corresponder a personas distintas.
--     Por eso el correo, y no el nombre, sirve como llave natural.
SELECT nombre, COUNT(*) AS clientes_con_ese_nombre
FROM clientes
GROUP BY nombre
HAVING COUNT(*) > 1
ORDER BY clientes_con_ese_nombre DESC
LIMIT 10;


-- Pregunta de cierre de la sesion:
-- este modelo resuelve la integridad, pero el motor sigue siendo de un
-- solo archivo y un solo escritor. Que ocurre cuando varias terminales
-- escriben al mismo tiempo.
